"""Validated, explicit OVAL-to-OSCAL mapping inventory for the alpha workflow."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import stat

from lxml import etree as ET

from .oval import OvalDocument, OvalInputError


MAX_MAPPING_BYTES = 1024 * 1024
MAPPING_FORMAT = "endeavor-oval-oscal-mapping"
MAPPING_VERSION = "1.0.0"
OSCAL_VERSION = "1.2.0"
OUTCOMES = frozenset({"true", "false"})
TARGET_TYPES = frozenset({"objective-id", "statement-id"})


@dataclass(frozen=True)
class Target:
    type: str
    identifier: str


@dataclass(frozen=True)
class Mapping:
    oval_definition_id: str
    target: Target
    outcomes: dict[str, dict[str, str]]


@dataclass(frozen=True)
class MappingDocument:
    path: Path
    sha256: str
    mappings: tuple[Mapping, ...]


def _safe_name(path: Path) -> str:
    return path.name or "mapping"


def _read_mapping(path: Path) -> bytes:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise OvalInputError(f"mapping does not exist: {_safe_name(path)}") from exc
    except OSError as exc:
        raise OvalInputError(f"mapping cannot be read: {_safe_name(path)}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise OvalInputError(f"mapping must be a regular non-symlink file: {_safe_name(path)}")
    if metadata.st_size > MAX_MAPPING_BYTES:
        raise OvalInputError(f"mapping exceeds {MAX_MAPPING_BYTES} byte limit: {_safe_name(path)}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise OvalInputError(f"mapping cannot be read: {_safe_name(path)}") from exc


def _require_exact_keys(value: object, keys: set[str], role: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise OvalInputError(f"mapping {role} has an unsupported shape")
    return value


def _require_text(value: object, role: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OvalInputError(f"mapping {role} must be a non-empty string")
    return value


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object while rejecting ambiguous duplicate members."""
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


def _require_target_id(value: object) -> str:
    """Require an OSCAL TokenDatatype identifier before creating output."""
    identifier = _require_text(value, "target-id")
    try:
        # lxml enforces XML NCName syntax, which is the OSCAL TokenDatatype
        # constraint used by the bundled Assessment Results schema.
        ET.Element(identifier)
    except (TypeError, ValueError) as exc:
        raise OvalInputError("mapping target-id must be an OSCAL token") from exc
    return identifier


def parse_mapping(path: Path) -> MappingDocument:
    raw = _read_mapping(path)
    try:
        value = json.loads(raw, object_pairs_hook=_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise OvalInputError(f"mapping is not valid JSON: {_safe_name(path)}") from exc
    root = _require_exact_keys(value, {"format", "version", "oscal-version", "mappings"}, "document")
    if root["format"] != MAPPING_FORMAT or root["version"] != MAPPING_VERSION or root["oscal-version"] != OSCAL_VERSION:
        raise OvalInputError(f"mapping has an unsupported format or version: {_safe_name(path)}")
    if not isinstance(root["mappings"], list):
        raise OvalInputError("mapping mappings must be an array")
    mappings: list[Mapping] = []
    seen: set[tuple[str, str, str]] = set()
    for item in root["mappings"]:
        entry = _require_exact_keys(item, {"oval-definition-id", "target", "outcomes"}, "entry")
        oval_identifier = _require_text(entry["oval-definition-id"], "oval-definition-id")
        target_value = _require_exact_keys(entry["target"], {"type", "target-id"}, "target")
        target = Target(_require_text(target_value["type"], "target type"), _require_target_id(target_value["target-id"]))
        if target.type not in TARGET_TYPES:
            raise OvalInputError("mapping target type is unsupported")
        if not isinstance(entry["outcomes"], dict) or not entry["outcomes"] or not set(entry["outcomes"]).issubset(OUTCOMES):
            raise OvalInputError("mapping outcomes must explicitly define true and/or false")
        outcomes: dict[str, dict[str, str]] = {}
        for result, outcome_value in entry["outcomes"].items():
            outcome = _require_exact_keys(outcome_value, {"state", "reason"}, "outcome")
            state = _require_text(outcome["state"], "outcome state")
            reason = _require_text(outcome["reason"], "outcome reason")
            if state not in {"satisfied", "not-satisfied"} or reason not in {"pass", "fail", "other"}:
                raise OvalInputError("mapping outcome state or reason is unsupported")
            outcomes[result] = {"state": state, "reason": reason}
        key = (oval_identifier, target.type, target.identifier)
        if key in seen:
            raise OvalInputError("mapping contains a duplicate OVAL definition target")
        seen.add(key)
        mappings.append(Mapping(oval_identifier, target, outcomes))
    return MappingDocument(path, hashlib.sha256(raw).hexdigest(), tuple(mappings))


def mapping_report(results: OvalDocument, definitions: OvalDocument, mapping: MappingDocument) -> dict[str, object]:
    definitions_by_id = {item.identifier: item for item in definitions.definitions}
    targets_by_id: dict[str, list[Target]] = {}
    for entry in mapping.mappings:
        targets_by_id.setdefault(entry.oval_definition_id, []).append(entry.target)
    mapped = []
    unmapped = []
    for result in sorted(results.definitions, key=lambda item: item.identifier):
        definition = definitions_by_id[result.identifier]
        targets = sorted(targets_by_id.get(result.identifier, []), key=lambda item: (item.type, item.identifier))
        record = {"oval-definition-id": result.identifier, "result": result.result}
        if targets:
            mapped.append({**record, "targets": [{"type": target.type, "target-id": target.identifier} for target in targets]})
        else:
            unmapped.append({**record, "title": definition.title, "class": definition.definition_class})
    stale = sorted({entry.oval_definition_id for entry in mapping.mappings} - set(definitions_by_id))
    return {
        "format": "endeavor-mapping-report",
        "version": "1.0.0",
        "mapping": {"path": mapping.path.name, "sha256": mapping.sha256, "format": MAPPING_FORMAT, "version": MAPPING_VERSION},
        "results": {"path": results.path.name, "sha256": results.sha256},
        "summary": {"evaluated": len(results.definitions), "mapped": len(mapped), "unmapped": len(unmapped), "stale-mappings": len(stale)},
        "mapped": mapped,
        "unmapped": unmapped,
        "stale-mappings": stale,
    }
