#!/usr/bin/env python3
"""Build byte-reproducible Endeavor source and standard Python distributions."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import os
import tarfile
import tomllib


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


def package_version(release_version: str) -> str:
    """Translate the accepted SemVer prerelease spelling to PEP 440."""

    for semver, pep440 in (("-alpha.", "a"), ("-beta.", "b"), ("-rc.", "rc")):
        if semver in release_version:
            return release_version.replace(semver, pep440)
    return release_version


def source_date_epoch(commit: str) -> str:
    epoch = run_git("show", "-s", "--format=%ct", commit)
    if not epoch.isdecimal():
        raise ValueError("could not determine source commit timestamp")
    return epoch


def extract_source(archive_path: Path, destination: Path, prefix: str) -> Path:
    destination.mkdir(parents=True)
    with tarfile.open(archive_path, "r:gz") as archive_file:
        for member in archive_file.getmembers():
            candidate = Path(member.name)
            if candidate.is_absolute() or ".." in candidate.parts or member.issym() or member.islnk():
                raise ValueError("Git source archive contains an unsafe member")
            archive_file.extract(member, destination)
    source = destination / prefix
    if not source.is_dir():
        raise ValueError("Git source archive did not contain the expected project directory")
    return source


def run_build(source: Path, destination: Path, epoch: str) -> list[Path]:
    destination.mkdir(parents=True)
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = epoch
    environment["PYTHONHASHSEED"] = "0"
    completed = subprocess.run(
        # CI installs the exact, hash-verified backend first.  Do not let PEP
        # 517 create a second environment that retrieves an unhashed backend.
        [sys.executable, "-m", "build", "--no-isolation", "--sdist", "--wheel", "--outdir", str(destination), str(source)],
        cwd=source,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise ValueError(completed.stderr.strip() or "PEP 517 build failed")
    artifacts = sorted(path for path in destination.iterdir() if path.is_file())
    if len(artifacts) != 2 or sum(path.suffix == ".whl" for path in artifacts) != 1 or sum(path.name.endswith(".tar.gz") for path in artifacts) != 1:
        raise ValueError("PEP 517 build did not produce exactly one wheel and one source distribution")
    for artifact in artifacts:
        if artifact.name.endswith(".tar.gz"):
            canonicalize_sdist(artifact, int(epoch))
    return artifacts


def canonicalize_sdist(path: Path, epoch: int) -> None:
    """Make PEP 517's standard tar.gz output independent of clock metadata."""

    entries: list[tuple[tarfile.TarInfo, bytes | None]] = []
    with tarfile.open(path, "r:gz") as source:
        for member in source.getmembers():
            normalized = copy.copy(member)
            normalized.uid = 0
            normalized.gid = 0
            normalized.uname = ""
            normalized.gname = ""
            normalized.mtime = epoch
            normalized.pax_headers = {}
            contents = source.extractfile(member).read() if member.isfile() else None
            entries.append((normalized, contents))
    replacement = path.with_suffix(".tmp")
    with replacement.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as destination:
                for member, contents in entries:
                    destination.addfile(member, io.BytesIO(contents) if contents is not None else None)
    replacement.replace(path)


def build_python_distributions(release_version: str, commit: str, archive_path: Path, output_dir: Path, prefix: str) -> list[Path]:
    declared = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    expected = package_version(release_version)
    if declared != expected:
        raise ValueError(f"pyproject.toml version {declared!r} does not match release package version {expected!r}")
    epoch = source_date_epoch(commit)
    with tempfile.TemporaryDirectory(prefix="endeavor-python-distributions-") as temporary:
        temporary_root = Path(temporary)
        first_source = extract_source(archive_path, temporary_root / "first-source", prefix)
        second_source = extract_source(archive_path, temporary_root / "second-source", prefix)
        first = run_build(first_source, temporary_root / "first-dist", epoch)
        second = run_build(second_source, temporary_root / "second-dist", epoch)
        if [path.name for path in first] != [path.name for path in second]:
            raise ValueError("PEP 517 artifact names were not reproducible")
        for first_path, second_path in zip(first, second):
            if first_path.read_bytes() != second_path.read_bytes():
                raise ValueError(f"Python distribution is not byte-reproducible: {first_path.name}")
        copied: list[Path] = []
        for artifact in first:
            destination = output_dir / artifact.name
            shutil.copyfile(artifact, destination)
            copied.append(destination)
    return copied


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
    distributions = build_python_distributions(version, commit, archive_path, output_dir, prefix)
    sbom = output_dir / "sbom.cdx.json"
    shutil.copyfile(ROOT / "sbom.cdx.json", sbom)
    published = [archive_path, *distributions, sbom]
    manifest = {
        "format": "endeavor-release-manifest",
        "version": "1.0.0",
        "release-version": version,
        "source-commit": commit,
        "artifacts": {path.name: {"sha256": sha256(path)} for path in published},
    }
    manifest_path = output_dir / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in (*published, manifest_path)),
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
