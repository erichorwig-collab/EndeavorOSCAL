#!/usr/bin/env python3
"""Validate version-bound evidence for an Endeavor general-availability tag."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
TAG = re.compile(r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_EVIDENCE = frozenset(
    {
        "human-acceptance",
        "accessibility-review",
        "license-review",
        "vulnerability-review",
        "reproducible-build",
        "release-notes",
        "support-policy",
        "compatibility-matrix",
    }
)
REQUIRED_RECORD_FIELDS = frozenset(
    {"format", "version", "status", "tag", "candidate-commit", "reviewed-at", "reviewer", "evidence"}
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timestamp(value: object) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("reviewed-at must be a UTC RFC 3339 timestamp ending in Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("reviewed-at must be a UTC RFC 3339 timestamp ending in Z") from error


def _candidate_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise ValueError("could not resolve the checked-out candidate commit")
    commit = completed.stdout.strip()
    if not COMMIT.fullmatch(commit):
        raise ValueError("could not resolve a full candidate commit SHA")
    return commit


def _package_version() -> str:
    try:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        version = project["version"]
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as error:
        raise ValueError("could not read the project package version") from error
    if not isinstance(version, str) or not version:
        raise ValueError("project package version must be a non-empty string")
    return version


def _evidence_path(value: object, role: str, record_path: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{role} evidence path must be a non-empty repository-relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{role} evidence path must stay within the repository")
    resolved = (ROOT / relative).resolve()
    if ROOT not in resolved.parents or not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"{role} evidence path must name a regular repository file")
    if resolved == record_path.resolve():
        raise ValueError(f"{role} evidence may not point to the GA readiness record itself")
    return resolved


def validate(payload: object, tag: str, candidate_commit: str, record_path: Path, enforce_filename: bool) -> dict[str, str]:
    if not TAG.fullmatch(tag):
        raise ValueError("tag must be a GA SemVer tag in the form vMAJOR.MINOR.PATCH (no prerelease suffix)")
    if not COMMIT.fullmatch(candidate_commit):
        raise ValueError("candidate commit must be a lowercase 40-character Git SHA")
    if not isinstance(payload, dict) or set(payload) != REQUIRED_RECORD_FIELDS:
        raise ValueError("record must contain exactly format, version, status, tag, candidate-commit, reviewed-at, reviewer, and evidence")
    if payload["format"] != "endeavor-ga-release-readiness" or payload["version"] != "1.0.0":
        raise ValueError("unsupported GA readiness record format or version")
    if payload["status"] != "accepted":
        raise ValueError("GA readiness record status must be accepted")
    if payload["tag"] != tag:
        raise ValueError("record tag does not match the requested GA tag")
    if payload["candidate-commit"] != candidate_commit:
        raise ValueError("record candidate-commit does not match the requested candidate commit")
    if not isinstance(payload["reviewer"], str) or not payload["reviewer"].strip():
        raise ValueError("reviewer must be a non-empty named accountable party")
    _timestamp(payload["reviewed-at"])
    if enforce_filename and record_path.name != f"ga-release-readiness-{tag[1:]}.json":
        raise ValueError("default GA readiness record filename must match the requested tag")

    evidence = payload["evidence"]
    if not isinstance(evidence, dict) or set(evidence) != REQUIRED_EVIDENCE:
        raise ValueError(f"evidence must contain exactly these roles: {', '.join(sorted(REQUIRED_EVIDENCE))}")
    verified: dict[str, str] = {}
    for role in sorted(REQUIRED_EVIDENCE):
        item = evidence[role]
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError(f"{role} evidence must contain exactly path and sha256")
        path = _evidence_path(item["path"], role, record_path)
        claimed = item["sha256"]
        if not isinstance(claimed, str) or not SHA256.fullmatch(claimed):
            raise ValueError(f"{role} evidence sha256 must be lowercase SHA-256")
        actual = _sha256(path)
        if actual != claimed:
            raise ValueError(f"{role} evidence SHA-256 does not match {Path(item['path']).name}")
        verified[role] = actual
    return verified


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="candidate GA tag, for example v1.0.0")
    parser.add_argument("--candidate-commit", help="full SHA for the candidate; defaults to checked-out HEAD")
    parser.add_argument("--record", type=Path, help="override the default versioned GA readiness record path")
    args = parser.parse_args(argv)
    tag = args.tag
    record = args.record or ROOT / "docs" / f"ga-release-readiness-{tag.removeprefix('v')}.json"
    try:
        candidate = args.candidate_commit or _candidate_commit()
        payload = json.loads(record.read_text(encoding="utf-8"))
        verified = validate(payload, tag, candidate, record, enforce_filename=args.record is None)
        if _package_version() != tag.removeprefix("v"):
            raise ValueError("project package version does not match the requested GA tag")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {
                    "format": "endeavor-ga-release-readiness-validation",
                    "status": "incomplete",
                    "tag": tag,
                    "record": record.name,
                    "error": str(error),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "format": "endeavor-ga-release-readiness-validation",
                "status": "passed",
                "tag": tag,
                "candidate-commit": candidate,
                "record": record.name,
                "evidence": verified,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
