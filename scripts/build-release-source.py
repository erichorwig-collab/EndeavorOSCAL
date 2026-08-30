#!/usr/bin/env python3
"""Build a byte-reproducible, source-only Endeavor release bundle from Git."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_git(*args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise ValueError(completed.stderr.strip() or "Git command failed")
    return completed.stdout.strip()


def archive(commit: str, prefix: str, output: Path) -> None:
    completed = subprocess.run(
        ["git", "archive", "--format=tar.gz", f"--prefix={prefix}/", "--output", str(output), commit],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise ValueError(completed.stderr.strip() or "Could not create source archive")


def build(version: str, ref: str, output_dir: Path) -> dict[str, object]:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("version must be a semantic version without a leading 'v'")
    if output_dir.exists():
        raise ValueError("output directory must not already exist")
    commit = run_git("rev-parse", "--verify", f"{ref}^{{commit}}")
    prefix = f"EndeavorOSCAL-{version}"
    output_dir.mkdir(parents=True)
    archive_path = output_dir / f"{prefix}-source.tar.gz"
    with tempfile.TemporaryDirectory(prefix="endeavor-release-") as temporary:
        comparison = Path(temporary) / archive_path.name
        archive(commit, prefix, archive_path)
        archive(commit, prefix, comparison)
        if archive_path.read_bytes() != comparison.read_bytes():
            shutil.rmtree(output_dir)
            raise ValueError("source archive was not byte-reproducible for the selected commit")
    sbom = output_dir / "sbom.cdx.json"
    shutil.copyfile(ROOT / "sbom.cdx.json", sbom)
    manifest = {
        "format": "endeavor-release-manifest",
        "version": "1.0.0",
        "release-version": version,
        "source-commit": commit,
        "artifacts": {
            archive_path.name: {"sha256": sha256(archive_path)},
            sbom.name: {"sha256": sha256(sbom)},
        },
    }
    manifest_path = output_dir / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in (archive_path, sbom, manifest_path)),
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = build(args.version, args.ref, args.output_dir)
    except ValueError as error:
        print(f"release source build failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
