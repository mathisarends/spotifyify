# Releasing spotifyify

The prepared release is **0.9.0**, dated **2026-11-03** in the changelog.
Its version is already set in `pyproject.toml`
and the root `spotifyify` entry in `uv.lock`. Release preparation does not publish
the package or create a tag. The `release.yml` workflow publishes stable version
tags after the full CI matrix, package build, metadata checks and an installed
wheel smoke test succeed.

## Validate the release PR

Start from the latest `main` and use the canonical repository,
[`mathisarends/spotifyify`](https://github.com/mathisarends/spotifyify).
Review changes since the previous tag, currently `v0.8.0`, together with
[CHANGELOG.md](../CHANGELOG.md) and the [migration guide](migration-0.9.md).
For a future version, update `pyproject.toml` and run `uv lock` before validation.

```bash
uv sync --frozen --group dev --group schema --group examples
uv run --no-sync ruff check spotifyify tests examples tools
uv run --no-sync ruff format --check spotifyify tests examples tools
uv run --no-sync pyright
uv run --no-sync python tools/generate_models.py --verify-only
uv run --no-sync pytest -q
uv build --out-dir dist/release-0.9.0
```

Use an empty output directory for each build so older packages cannot be
uploaded accidentally. Check the artifacts themselves:

- Both the wheel and source distribution report version `0.9.0` and Python
  `>=3.13`, with HTTPX2 as a runtime dependency.
- The wheel includes `spotifyify/py.typed`, has no `spotifyify/cli/` package or
  console entry point, and does not expose a `cli` extra.
- The source distribution includes the changelog, migration/release/model docs,
  pinned schema, generator and examples.
- Install the wheel into a fresh environment outside the source tree and check
  public imports, compatibility aliases and an HTTPX2 mock request. Also build
  a wheel from the source distribution.

Before merging, require the PR's four CI combinations (Windows/Linux, Python
3.13/3.14) to pass and resolve any review blockers. Offline tests and mock
requests do not verify a real Spotify grant, app quota eligibility or playback.
Check those with a dedicated Spotify account if release changes require them.

## Publish after merge

The PyPI Trusted Publisher must match these exact values:

- Owner: `mathisarends`
- Repository: `spotifyify`
- Workflow: `release.yml`
- GitHub environment: `pypi`

The GitHub repository must have an environment named `pypi`. No PyPI API token
is required: only the publish job receives `id-token: write`, and it downloads
the distributions from the separate build job without executing project code.

1. Choose the exact commit on `main` to release and confirm it has passed CI.
   Confirm that the changelog date matches the publication date; update it if
   publication is delayed. The package version, lockfile version and tag must
   agree, and the changelog must contain a dated entry.
2. Check PyPI for an existing version; published files cannot be replaced.
3. Tag that commit and push the tag:

   ```bash
   git tag -a v0.9.0 <validated-main-commit> -m "Release 0.9.0"
   git push origin v0.9.0
   ```

4. Watch the **Release** workflow. It repeats all four CI combinations, builds
   fresh distributions, validates them with Twine, smoke-tests an installed wheel,
   and uploads them to PyPI with OIDC and attestations. Only after PyPI succeeds
   does it create the GitHub release with changelog notes, the same distributions
   and SHA-256 checksums.
5. Confirm the installed version and imports from PyPI in a fresh environment.

To retry an interrupted release, rerun its workflow or manually dispatch
`release.yml` with the existing version tag as the ref. Branch refs are rejected
before publication. Already published files are skipped; GitHub release assets
can be uploaded again. Never move a published version tag or change its source.

Package upload, tag creation and GitHub release publication are separate steps
from opening or merging the release PR.
