"""Generate an upstream comparison baseline from the pinned Spotify schema.

Public models contain compatibility fixes and are maintained in spotifyify/models.
This tool intentionally generates a separate baseline for reviewing upstream drift.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from importlib.metadata import version

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build" / "spotify-schema-baseline.py"
    )
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    metadata = json.loads(
        (ROOT / "schemas" / "source.json").read_text(encoding="utf-8")
    )
    raw = gzip.decompress((ROOT / "schemas" / "spotify.openapi.yaml.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest() != metadata["sha256"]:
        raise SystemExit("Pinned schema checksum mismatch")
    if args.verify_only:
        print("Pinned Spotify schema checksum verified")
        return
    if version("datamodel-code-generator") != metadata["generator_version"]:
        raise SystemExit(
            "Use the pinned schema tool group: uv run --group schema python tools/generate_models.py"
        )
    output = args.output.resolve()
    if output.is_relative_to(ROOT / "spotifyify"):
        raise SystemExit(
            "Generate a comparison baseline outside the maintained spotifyify package"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "spotify.openapi.yaml"
        source.write_bytes(raw)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "datamodel_code_generator",
                "--input",
                str(source),
                "--output",
                str(output),
                *metadata["generator_args"],
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
