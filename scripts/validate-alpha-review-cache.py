#!/usr/bin/env python3
"""Validate a staged, offline-only dependency cache for the review VM."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import stat
import sys


SHA256 = re.compile(r"([0-9a-f]{64})  ([^\n]+)$")
REQUIRED_METADATA = frozenset({"format", "version", "candidate-commit", "requirements-sha256", "package-lock-sha256", "alpine-version"})


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        details = path.lstat()
        if stat.S_ISLNK(details.st_mode) or not (stat.S_ISREG(details.st_mode) or stat.S_ISDIR(details.st_mode)):
            raise ValueError(f"cache contains unsafe path: {path.relative_to(root)}")
        if stat.S_ISREG(details.st_mode):
            files.append(path)
    return files


def metadata(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if not separator or key not in REQUIRED_METADATA or not value or key in values:
            raise ValueError("cache metadata has an unsupported shape")
        values[key] = value
    if set(values) != REQUIRED_METADATA or values["format"] != "endeavor-alpha-review-offline-cache" or values["version"] != "1.0.0" or values["alpine-version"] != "3.24":
        raise ValueError("cache metadata has an unsupported format or version")
    return values


def validate(cache: Path, candidate: str, requirements: Path, package_lock: Path) -> None:
    if not cache.is_dir() or cache.is_symlink():
        raise ValueError("cache must be a real directory")
    files = regular_files(cache)
    names = {path.relative_to(cache).as_posix() for path in files}
    if not any(name.startswith("apk/") and name.endswith(".apk") for name in names):
        raise ValueError("cache does not contain Alpine packages")
    if not any(name.startswith("python/lxml-6.1.2-") and name.endswith(".whl") for name in names):
        raise ValueError("cache does not contain the pinned lxml wheel")
    if not any(name.startswith("npm/") for name in names):
        raise ValueError("cache does not contain an npm cache")
    if {"CACHE-METADATA", "SHA256SUMS"} - names:
        raise ValueError("cache is missing its metadata or checksum manifest")
    values = metadata(cache / "CACHE-METADATA")
    if values["candidate-commit"] != candidate or values["requirements-sha256"] != digest(requirements) or values["package-lock-sha256"] != digest(package_lock):
        raise ValueError("cache metadata does not bind this frozen candidate")
    expected: dict[str, str] = {}
    for line in (cache / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        match = SHA256.fullmatch(line)
        if match is None or match.group(2) in expected or match.group(2).startswith("/") or ".." in Path(match.group(2)).parts:
            raise ValueError("cache checksum manifest has an unsupported shape")
        expected[match.group(2)] = match.group(1)
    actual = names - {"SHA256SUMS"}
    if set(expected) != actual:
        raise ValueError("cache checksum manifest does not cover exactly its files")
    for relative, expected_digest in expected.items():
        if digest(cache / relative) != expected_digest:
            raise ValueError(f"cache checksum does not match: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--package-lock", required=True, type=Path)
    args = parser.parse_args()
    try:
        validate(args.cache, args.candidate, args.requirements, args.package_lock)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f"Offline review cache validation failed: {error}", file=sys.stderr)
        return 1
    print("Offline review cache is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
