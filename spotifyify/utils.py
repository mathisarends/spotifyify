from collections.abc import Iterable


def coalesce_items(ids_or_uris: Iterable[str]) -> list[str]:
    return [str(v).strip() for v in ids_or_uris if str(v).strip()]


def coalesce_csv(ids_or_uris: Iterable[str]) -> str:
    return ",".join(coalesce_items(ids_or_uris))


def ensure_episode_uri(episode_uri_or_id: str) -> str:
    if episode_uri_or_id.startswith("spotify:episode:"):
        return episode_uri_or_id
    return f"spotify:episode:{episode_uri_or_id}"
