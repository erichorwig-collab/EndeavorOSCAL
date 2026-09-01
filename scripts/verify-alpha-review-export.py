#!/usr/bin/env python3
"""Verify guest export against a host-created manifest and copy trusted bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


ARTIFACTS = frozenset({"pass.json", "fail.json", "mapping-report.html"})
SOURCE_PATHS = {
    "definitions.xml": Path("fixtures/oval-definitions/definitions.xml"),
    "example-v1.json": Path("fixtures/mappings/example-v1.json"),
    "assessment-results.schema.json": Path("endeavor/schemas/oscal-1.2.0/assessment-results.schema.json"),
    "pass.xml": Path("fixtures/oval-results/pass.xml"),
    "fail.xml": Path("fixtures/oval-results/fail.xml"),
}
MAX_ARTIFACT_BYTES = 4 * 1024 * 1024
SHA256 = set("0123456789abcdef")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular_directory(path: Path, role: str) -> None:
    details = path.lstat()
    if not stat.S_ISDIR(details.st_mode) or stat.S_ISLNK(details.st_mode):
        raise ValueError(f"{role} must be a real directory")


def git_commit(candidate: Path) -> str:
    completed = subprocess.run(["git", "-C", str(candidate), "-c", f"safe.directory={candidate}", "rev-parse", "HEAD"], text=True, capture_output=True, check=False)
    if completed.returncode:
        raise ValueError("candidate is not a readable Git checkout")
    return completed.stdout.strip()


def expected_hashes(candidate: Path, expected: Path, candidate_commit: str) -> dict[str, str]:
    try:
        record = json.loads(expected.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("host expected manifest is not valid JSON") from error
    if not isinstance(record, dict) or record.get("format") != "endeavor-alpha-workflow-validation" or record.get("version") != "1.1.0" or record.get("status") != "passed" or record.get("repository-commit") != candidate_commit:
        raise ValueError("host expected manifest does not bind the candidate")
    sources, artifacts = record.get("sources"), record.get("artifacts")
    if not isinstance(sources, dict) or not isinstance(artifacts, dict) or set(sources) != set(SOURCE_PATHS) or set(artifacts) != ARTIFACTS:
        raise ValueError("host expected manifest has an unsupported evidence shape")
    for name, relative in SOURCE_PATHS.items():
        if not isinstance(sources[name], str) or sources[name] != sha256(candidate / relative):
            raise ValueError(f"host expected manifest source hash does not match: {name}")
    for name, value in artifacts.items():
        if not isinstance(value, str) or len(value) != 64 or set(value) - SHA256:
            raise ValueError("host expected manifest contains an invalid artifact hash")
    return artifacts


def read_verified(path: Path, expected: str) -> bytes:
    details = path.lstat()
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode) or details.st_size > MAX_ARTIFACT_BYTES:
        raise ValueError(f"export contains an unsafe artifact: {path.name}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        content = os.read(descriptor, MAX_ARTIFACT_BYTES + 1)
        if os.read(descriptor, 1):
            raise ValueError(f"export artifact exceeds {MAX_ARTIFACT_BYTES} bytes: {path.name}")
    finally:
        os.close(descriptor)
    if len(content) != details.st_size or hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"export artifact does not match host expected hash: {path.name}")
    return content


def write_destination(destination: Path, value: dict[str, bytes], record: dict[str, object]) -> None:
    if destination.exists() or destination.is_symlink():
        raise ValueError("verification destination must not already exist")
    destination.mkdir(mode=0o700, parents=True)
    try:
        for name, content in value.items():
            path = destination / name
            with path.open("xb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(content)
        with (destination / "export-verification.json").open("x", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception:
        for path in destination.iterdir():
            path.unlink()
        destination.rmdir()
        raise


def verify(candidate: Path, expected: Path, export: Path, candidate_commit: str, destination: Path) -> dict[str, object]:
    if git_commit(candidate) != candidate_commit:
        raise ValueError("candidate checkout does not match the expected commit")
    regular_directory(export, "export")
    if {entry.name for entry in export.iterdir()} != ARTIFACTS:
        raise ValueError("export must contain exactly the retained review artifacts")
    hashes = expected_hashes(candidate, expected, candidate_commit)
    content = {name: read_verified(export / name, hashes[name]) for name in sorted(ARTIFACTS)}
    with tempfile.TemporaryDirectory(prefix="endeavor-export-accessibility-") as temporary:
        report = Path(temporary) / "mapping-report.html"
        report.write_bytes(content["mapping-report.html"])
        accessibility = subprocess.run([sys.executable, str(candidate / "scripts/validate-report-accessibility.py"), "--report", str(report)], cwd=candidate, text=True, capture_output=True, check=False)
    if accessibility.returncode:
        raise ValueError("exported HTML report fails the host accessibility check")
    record = {"format": "endeavor-alpha-review-export-verification", "version": "1.0.0", "status": "passed", "candidate-commit": candidate_commit, "expected-manifest-sha256": sha256(expected), "artifacts": {name: {"sha256": hashes[name], "bytes": len(content[name])} for name in sorted(ARTIFACTS)}, "accessibility": json.loads(accessibility.stdout)}
    write_destination(destination, content, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--export", dest="export_dir", type=Path, required=True)
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = verify(args.candidate, args.expected, args.export_dir, args.candidate_commit, args.destination)
    except (OSError, ValueError) as error:
        print(f"Alpha review export verification failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
