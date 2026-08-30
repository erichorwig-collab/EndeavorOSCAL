"""Strict authored XCCDF-to-OSCAL mapping inventory."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .mapping import MAX_MAPPING_BYTES, OSCAL_VERSION, TARGET_TYPES, Target, _read_mapping, _require_exact_keys, _require_text
from .oval import OvalInputError

MAPPING_FORMAT = "endeavor-xccdf-oscal-mapping"
MAPPING_VERSION = "1.0.0"
XCCDF_OUTCOMES = frozenset({"pass", "fail", "error", "unknown", "notapplicable", "notchecked", "notselected", "informational", "fixed"})


@dataclass(frozen=True)
class Mapping:
    benchmark_id: str
    rule_id: str
    target: Target
    outcomes: dict[str, dict[str, str]]


@dataclass(frozen=True)
class MappingDocument:
    path: Path
    sha256: str
    mappings: tuple[Mapping, ...]


def parse_mapping(path: Path) -> MappingDocument:
    raw = _read_mapping(path)
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OvalInputError(f"mapping is not valid JSON: {path.name}") from exc
    root = _require_exact_keys(value, {"format", "version", "oscal-version", "mappings"}, "document")
    if root["format"] != MAPPING_FORMAT or root["version"] != MAPPING_VERSION or root["oscal-version"] != OSCAL_VERSION or not isinstance(root["mappings"], list):
        raise OvalInputError(f"mapping has an unsupported format or version: {path.name}")
    mappings, seen = [], set()
    for item in root["mappings"]:
        entry = _require_exact_keys(item, {"benchmark-id", "rule-id", "target", "outcomes"}, "entry")
        benchmark_id, rule_id = _require_text(entry["benchmark-id"], "benchmark-id"), _require_text(entry["rule-id"], "rule-id")
        target_value = _require_exact_keys(entry["target"], {"type", "target-id"}, "target")
        target = Target(_require_text(target_value["type"], "target type"), _require_text(target_value["target-id"], "target-id"))
        if target.type not in TARGET_TYPES or not isinstance(entry["outcomes"], dict) or not entry["outcomes"] or not set(entry["outcomes"]).issubset(XCCDF_OUTCOMES):
            raise OvalInputError("mapping target or outcomes are unsupported")
        outcomes = {}
        for status, outcome_value in entry["outcomes"].items():
            outcome = _require_exact_keys(outcome_value, {"state", "reason"}, "outcome")
            state, reason = _require_text(outcome["state"], "outcome state"), _require_text(outcome["reason"], "outcome reason")
            if state not in {"satisfied", "not-satisfied"} or reason not in {"pass", "fail", "other"}:
                raise OvalInputError("mapping outcome state or reason is unsupported")
            outcomes[status] = {"state": state, "reason": reason}
        key = (benchmark_id, rule_id, target.type, target.identifier)
        if key in seen:
            raise OvalInputError("mapping contains a duplicate XCCDF rule target")
        seen.add(key)
        mappings.append(Mapping(benchmark_id, rule_id, target, outcomes))
    return MappingDocument(path, hashlib.sha256(raw).hexdigest(), tuple(mappings))
