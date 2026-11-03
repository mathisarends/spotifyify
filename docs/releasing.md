# Releasing spotifyify

The prepared release is **0.9.0**, dated **2026-11-03** in the changelog.
Its version is already set in `pyproject.toml`
and the root `spotifyify` entry in `uv.lock`. Release preparation does not publish
the package or create a tag. The CI workflow validates changes and builds
distributions; there is no automated PyPI publishing workflow.

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

1. Choose the exact commit to release and confirm it has passed CI. Confirm that
   the changelog date matches the publication date; update it if publication is
   delayed. Build artifacts from that exact commit using the checks above.
2. Check PyPI for an existing `0.9.0`; published versions cannot be replaced.
   Configure PyPI credentials or a trusted publishing workflow before uploading.
3. Validate metadata with `uvx --from twine twine check` followed by the two exact
   distribution paths. Upload those same files with `uv publish`, passing both
   paths explicitly rather than uploading all of `dist/`.
4. Tag the validated commit as `v0.9.0`, push the tag and create a GitHub release
   from the matching changelog entry. Confirm the installed version and imports
   from PyPI in a fresh environment.

Package upload, tag creation and GitHub release publication are separate steps
from opening or merging the release PR.
