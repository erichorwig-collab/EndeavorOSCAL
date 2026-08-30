"""OSCAL Assessment Results emission for supported OVAL Results evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import uuid

from .mapping import MAPPING_FORMAT, MAPPING_VERSION, MappingDocument
from .oval import OvalDocument, OvalInputError


NAMESPACE = "https://endeavor.dev/ns/oval"
UUID_NAMESPACE = uuid.UUID("0b5c72b8-3a31-4ba2-b5c9-703dc149d51b")


def _uuid(*parts: str) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, "\x1f".join(parts)))


def _timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def assessment_results(results: OvalDocument, definitions: OvalDocument, mapping: MappingDocument | None = None) -> dict:
    definitions_by_id = {item.identifier: item for item in definitions.definitions}
    missing = [item.identifier for item in results.definitions if item.identifier not in definitions_by_id]
    if missing:
        raise OvalInputError("results reference definitions absent from Definitions input: " + ", ".join(missing))
    run_id = _uuid(results.sha256, definitions.sha256, results.generator.timestamp, *([mapping.sha256] if mapping else []))
    timestamp = _timestamp(results.generator.timestamp)
    resources = []
    for document, kind in ((results, "oval-results"), (definitions, "oval-definitions")):
        resource_id = _uuid(document.sha256)
        resources.append({
            "uuid": resource_id,
            "title": f"Source {kind}: {document.path.name}",
            "props": [{"name": "source-artifact-type", "ns": NAMESPACE, "value": kind}],
            "rlinks": [{"href": document.path.name, "media-type": "application/xml", "hashes": [{"algorithm": "SHA-256", "value": document.sha256}]}],
        })
    if mapping:
        resources.append({
            "uuid": _uuid(mapping.sha256),
            "title": f"Source OVAL mapping: {mapping.path.name}",
            "props": [
                {"name": "source-artifact-type", "ns": NAMESPACE, "value": "oval-oscal-mapping"},
                {"name": "mapping-format", "ns": NAMESPACE, "value": MAPPING_FORMAT},
                {"name": "mapping-version", "ns": NAMESPACE, "value": MAPPING_VERSION},
            ],
            "rlinks": [{"href": mapping.path.name, "media-type": "application/json", "hashes": [{"algorithm": "SHA-256", "value": mapping.sha256}]}],
        })
    observations = []
    findings = []
    mappings_by_id: dict[str, list] = {}
    if mapping:
        for entry in mapping.mappings:
            mappings_by_id.setdefault(entry.oval_definition_id, []).append(entry)
    for source in results.definitions:
        definition = definitions_by_id[source.identifier]
        properties = [
            {"name": "oval-definition-id", "ns": NAMESPACE, "value": source.identifier},
            {"name": "oval-result", "ns": NAMESPACE, "value": source.result},
            {"name": "oval-definition-class", "ns": NAMESPACE, "value": definition.definition_class},
        ]
        if results.system_identity is not None:
            properties.extend([
                {"name": "target-os-name", "ns": NAMESPACE, "value": results.system_identity.os_name},
                {"name": "target-os-version", "ns": NAMESPACE, "value": results.system_identity.os_version},
                {"name": "target-architecture", "ns": NAMESPACE, "value": results.system_identity.architecture},
                {"name": "target-host-name", "ns": NAMESPACE, "value": results.system_identity.primary_host_name},
            ])
            for namespace in results.system_identity.platform_extension_namespaces:
                properties.append({"name": "oval-platform-system-characteristics-namespace", "ns": NAMESPACE, "value": namespace})
        if source.message:
            properties.append({"name": "oval-result-message", "ns": NAMESPACE, "value": source.message})
        observation_id = _uuid(run_id, source.identifier)
        observations.append({
            "uuid": observation_id,
            "title": definition.title,
            "description": definition.description,
            "methods": ["TEST"],
            "collected": timestamp,
            "types": ["discovery"],
            "props": properties,
            "relevant-evidence": [{"href": "#" + _uuid(results.sha256), "description": "OVAL Results source evidence."}, {"href": "#" + _uuid(definitions.sha256), "description": "OVAL Definitions source evidence."}],
        })
        for entry in mappings_by_id.get(source.identifier, []):
            outcome = entry.outcomes.get(source.result)
            if outcome is None:
                continue
            findings.append({
                "uuid": _uuid(run_id, source.identifier, entry.target.type, entry.target.identifier, outcome["state"], outcome["reason"]),
                "title": f"Mapped OVAL evaluation: {definition.title}",
                "description": f"Explicit mapping of OVAL definition {source.identifier} to {entry.target.type} {entry.target.identifier}.",
                "props": [
                    {"name": "oval-definition-id", "ns": NAMESPACE, "value": source.identifier},
                    {"name": "oval-result", "ns": NAMESPACE, "value": source.result},
                    {"name": "mapping-sha256", "ns": NAMESPACE, "value": mapping.sha256},
                    {"name": "mapping-version", "ns": NAMESPACE, "value": MAPPING_VERSION},
                    {"name": "source-observation-uuid", "ns": NAMESPACE, "value": observation_id},
                ],
                "target": {"type": entry.target.type, "target-id": entry.target.identifier, "status": outcome},
            })
    result = {"uuid": _uuid(run_id, "result"), "title": "OVAL evaluation evidence", "description": "Evidence converted from OVAL Results without inferring control findings.", "start": timestamp, "end": timestamp, "reviewed-controls": {"control-selections": [{"include-all": {}}]}, "observations": observations}
    if findings:
        result["findings"] = findings
    return {
        "assessment-results": {
            "uuid": run_id,
            "metadata": {"title": "Endeavor OVAL assessment results", "last-modified": timestamp, "version": "0.1.0a0", "oscal-version": "1.2.0"},
            "import-ap": {"href": "REQUIRED-ASSESSMENT-PLAN.oscal.json", "remarks": "v0.1 requires the caller to associate this evidence with an Assessment Plan before authorization use."},
            "results": [result],
            "back-matter": {"resources": resources},
        }
    }
