# Plan: User-Playlist-Modifikation in spotifyify integrieren

## Die eigentliche Neuerung: Bring Your Own Token (BYOT)

Der gepostete `SpotifyPlaylistCreator` reicht in **jeder** Methode ein
`access_token=...` herein. Das ist der wesentliche Unterschied zu spotifyify:

- Heute löst spotifyify das Token **immer intern** auf – über
  `SpotifyClient._request_json` → `self._token_provider.get_access_token(...)`
  → `SpotifyifyOAuth` → `SpotifyCredentials` + Cache-Handler. Das ist ein
  **Single-Tenant**-Modell: ein Client = ein Nutzer/eine Credential-Quelle.
- Der gepostete Code ist **Multi-Tenant**: der Aufrufer (z. B. ein Web-Backend)
  bringt pro Request das Token des jeweiligen Endnutzers mit – unabhängig von
  `credentials.py`, OAuth-Flow und Cache.

Das ist die Kernfähigkeit, die spotifyify fehlt. „Replace tracks" ist dagegen nur
eine fehlende Methode (siehe unten, Sekundär-Scope).

### Architektonischer Hebelpunkt

`AccessTokenProvider` (`spotifyify/auth.py`) ist nur ein Protocol:

```python
class AccessTokenProvider(Protocol):
    async def get_access_token(self, require_user, scope=None) -> str: ...
```

`SpotifyClient` hängt nur an diesem Protocol – nicht an `SpotifyifyOAuth`. Damit
ist BYOT sauber integrierbar, ohne Namespaces oder die OAuth-Maschinerie
anzufassen.

## Gewählter Ansatz: Scoped Override via `ContextVar` (Option B)

> **Entscheidung:** Umgesetzt wird ausschließlich Option B. Die Alternativen A
> (`StaticTokenProvider` pro Instanz) und C (`access_token=` an jeder Methode)
> sind am Ende kurz als verworfen dokumentiert.

### Option B – Scoped Override via `ContextVar` (pro Aufruf/Block)

Spiegelt das bereits vorhandene `retry_hook`-Muster
(`spotifyify/http/retry_context.py` + `Spotifyify.retry_hook`):

1. Neuer `ContextVar`, z. B. `spotifyify/http/auth_context.py`:
   ```python
   current_access_token: ContextVar[str | None] = ContextVar(
       "current_access_token", default=None
   )
   ```
2. Gemeinsamer Async-Context-Manager auf `Spotifyify` für Request-Scope-Konfiguration:
   ```python
   @asynccontextmanager
   async def session(
     self,
     *,
     access_token: str | None = None,
     on_retry: OnRetryHook | None = None,
   ) -> AsyncIterator[None]: ...
   ```
3. Expliziter Convenience-Context für reine BYOT-Aufrufe:
   ```python
   @asynccontextmanager
   async def user_token(self, access_token: str) -> AsyncIterator[None]:
     async with self.session(access_token=access_token):
           yield
   ```
4. In `SpotifyClient._request_json`: zuerst den ContextVar prüfen; ist er gesetzt,
   diesen Token verwenden und den `token_provider` **überspringen** (kein OAuth,
   kein Refresh, kein Scope-Check):
   ```python
   override = current_access_token.get()
   if override is not None:
       token = override
   else:
       token = await self._token_provider.get_access_token(
           require_user=require_user, scope=self._scopes
       )
   ```

- **Passt zu:** „ein langlebiger, geteilter Client für viele Nutzer". Jeder
  async-Request setzt in seinem Kontext sein eigenes Token – nebenläufigkeitssicher
  über `ContextVar` (gleicher Mechanismus wie `retry_hook`).
- **Vorteil:** geteilter Connection-Pool, kein Instanz-pro-Nutzer, idiomatisch zum
  bestehenden Code; Signaturen der Namespaces bleiben unverändert.
- **Nutzung:**
  ```python
  async with Spotifyify() as spotify:
    async with spotify.session(access_token=end_user_token):
          await spotify.playlists.create("Mix", public=False)
  ```

### Verworfene Alternativen

- **Option A – `StaticTokenProvider` (pro Instanz):** triviale Implementierung des
  `AccessTokenProvider`-Protocols, verdrahtet via `Spotifyify.with_access_token(...)`.
  Modell „ein Client pro Nutzer", kein geteilter Connection-Pool. Verworfen
  zugunsten des nebenläufig geteilten Clients aus B. (Kann bei Bedarf später
  ergänzt werden – koexistiert mit B.)
- **Option C – `access_token=` an jeder Methode (wörtlicher Port):** würde
  `_request_json` und **jede** Namespace-Methode um einen Parameter erweitern.
  Invasiv, bricht die schlanken Signaturen, kein Mehrwert gegenüber B.

## Semantik-Entscheidungen (BYOT)

- **`require_user` / `scope`:** bei gesetztem Override irrelevant – das Token ist
  bereits gemintet. Provider und Scope-Logik werden komplett umgangen.
- **Fehlerfälle:** ungültige/abgelaufene Fremd-Tokens → Spotify liefert 401/403;
  läuft durch den bestehenden `parse_response`-Fehlerpfad. Kein Auto-Refresh
  (der Aufrufer besitzt den Token-Lebenszyklus).
- **Retry:** 429/503-Retry greift unverändert über `HttpTransport`/`RetryPolicy` –
  kein eigener Retry-Pfad nötig (der gepostete `_send_with_retry` wird **nicht**
  portiert).

## Sekundär-Scope: `Playlists.replace()`

Unabhängig von BYOT fehlt die „kompletten Tracklisten-Inhalt ersetzen"-Operation
(`PUT …/tracks` mit voller URI-Liste). Vorhanden sind nur `add`/`remove`/`reorder`.

- Neue Methode `Playlists.replace(playlist_id, uris) -> str | None`, Stil wie
  `add`/`remove` (`coalesce_items`, Rückgabe `snapshot_id`, `/items`-Pfad).
- **100-URI-Limit:** erster `PUT …/items` mit den ersten 100 URIs (ersetzt +
  verwirft Rest), restliche URIs in 100er-Blöcken per `POST …/items` anhängen.
  Konstante `_MAX_ITEMS_PER_REQUEST = 100`. Leere Liste → ein `PUT {"uris": []}`.

## Schritte

1. **BYOT-Kern (Option B):**
   - `spotifyify/http/auth_context.py` mit `current_access_token`-ContextVar.
   - Export über `spotifyify/http/__init__.py` (analog `current_retry_hook`).
   - `SpotifyClient._request_json`: Override-Prüfung vor dem Provider-Call.

- `Spotifyify.session(...)` als gemeinsamer async Scope für `access_token` und `on_retry`.
- `Spotifyify.user_token(...)`-Context-Manager.

2. **Sekundär:** `Playlists.replace()` inkl. Chunking.
3. **Tests:**
   - `tests/test_client.py`: Override schlägt den Provider, `require_user`/`scope`
     werden umgangen; ohne Override unveränderter Pfad.
   - Ein Test für `Spotifyify.user_token(...)` (Set/Reset, Nebenläufigkeit analog
     der vorhandenen retry-hook-Tests).
   - `tests/namespaces/test_playlists.py`: `test_replace`, `test_replace_empty`,
     `test_replace_chunks`.
4. **Doku:** kurzes BYOT-Beispiel (Multi-User-Backend) in README; `replace` in der
   Operationsliste ergänzen.

## Bewusst NICHT im Scope

- Portierung der Klasse `SpotifyPlaylistCreator` oder ihrer Retry-/HTTP-/`/me`-
  Hilfsfunktionen (alles bereits zentral vorhanden).
- Auto-Refresh für fremde Tokens (Lebenszyklus liegt beim Aufrufer).
- Dediziertes Snapshot-Antwortmodell – Rückgabe bleibt `snapshot_id: str | None`.

## Definition of Done

- [ ] BYOT via ContextVar implementiert; Override umgeht Provider, Scope und
      `require_user` korrekt.
- [ ] `Spotifyify.user_token(...)` als Context-Manager (Set/Reset sauber).
- [ ] `Playlists.replace()` inkl. Chunking >100 URIs.
- [ ] Keine neue HTTP-/Retry-/Auth-Maschinerie dupliziert.
- [ ] Tests grün; `pytest` und Linter sauber.
