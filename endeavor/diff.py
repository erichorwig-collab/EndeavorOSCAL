"""Deterministic status deltas between Endeavor Assessment Results artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

from .oval import OvalInputError


MAX_RESULTS_BYTES = 5 * 1024 * 1024
NAMESPACE = "https://endeavor.dev/ns/oval"


def _safe_name(path: Path) -> str:
    return path.name or "assessment-results"


def _read_json(path: Path) -> tuple[dict[str, object], str]:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise OvalInputError(f"assessment results does not exist: {_safe_name(path)}") from exc
    except OSError as exc:
        raise OvalInputError(f"assessment results cannot be read: {_safe_name(path)}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise OvalInputError(f"assessment results must be a regular non-symlink file: {_safe_name(path)}")
    if metadata.st_size > MAX_RESULTS_BYTES:
        raise OvalInputError(f"assessment results exceeds {MAX_RESULTS_BYTES} byte limit: {_safe_name(path)}")
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OvalInputError(f"assessment results is not valid JSON: {_safe_name(path)}") from exc
    if not isinstance(value, dict):
        raise OvalInputError(f"assessment results has an unsupported shape: {_safe_name(path)}")
    return value, hashlib.sha256(raw).hexdigest()


def _status_by_definition(document: dict[str, object], path: Path) -> dict[str, str]:
    try:
        results = document["assessment-results"]
        runs = results["results"] if isinstance(results, dict) else None
    except KeyError as exc:
        raise OvalInputError(f"assessment results has an unsupported shape: {_safe_name(path)}") from exc
    if not isinstance(runs, list):
        raise OvalInputError(f"assessment results has an unsupported shape: {_safe_name(path)}")
    statuses: dict[str, str] = {}
    for run in runs:
        if not isinstance(run, dict):
            raise OvalInputError(f"assessment results has an unsupported shape: {_safe_name(path)}")
        observations = run.get("observations", [])
        if not isinstance(observations, list):
            raise OvalInputError(f"assessment results has an unsupported shape: {_safe_name(path)}")
        for observation in observations:
            if not isinstance(observation, dict) or not isinstance(observation.get("props", []), list):
                raise OvalInputError(f"assessment results has an unsupported shape: {_safe_name(path)}")
            props = {(item.get("name"), item.get("ns")): item.get("value") for item in observation["props"] if isinstance(item, dict)}
            identifier = props.get(("oval-definition-id", NAMESPACE))
            status = props.get(("oval-result", NAMESPACE))
            if identifier is None and status is None:
                continue
            if not isinstance(identifier, str) or not isinstance(status, str) or identifier in statuses:
                raise OvalInputError(f"assessment results has invalid OVAL observation provenance: {_safe_name(path)}")
            statuses[identifier] = status
    return statuses


def assessment_results_diff(before_path: Path, after_path: Path) -> dict[str, object]:
    before_document, before_hash = _read_json(before_path)
    after_document, after_hash = _read_json(after_path)
    before = _status_by_definition(before_document, before_path)
    after = _status_by_definition(after_document, after_path)
    added = [{"oval-definition-id": identifier, "after": after[identifier]} for identifier in sorted(set(after) - set(before))]
    removed = [{"oval-definition-id": identifier, "before": before[identifier]} for identifier in sorted(set(before) - set(after))]
    changed = [{"oval-definition-id": identifier, "before": before[identifier], "after": after[identifier]} for identifier in sorted(set(before) & set(after)) if before[identifier] != after[identifier]]
    unchanged = sorted(identifier for identifier in set(before) & set(after) if before[identifier] == after[identifier])
    return {
        "format": "endeavor-assessment-results-diff",
        "version": "1.0.0",
        "before": {"path": before_path.name, "sha256": before_hash},
        "after": {"path": after_path.name, "sha256": after_hash},
        "summary": {"added": len(added), "removed": len(removed), "changed": len(changed), "unchanged": len(unchanged)},
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }
