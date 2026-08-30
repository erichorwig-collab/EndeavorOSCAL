"""Schema-shaped OSCAL Assessment Results from explicit XCCDF mappings."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .xccdf_mapping import MappingDocument

NAMESPACE = "https://endeavor.dev/ns/xccdf"
UUID_NAMESPACE = uuid.UUID("0b5c72b8-3a31-4ba2-b5c9-703dc149d51b")


def _uuid(*parts: str) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, "\x1f".join(parts)))


def _time(value: str | None) -> str:
    parsed = datetime.fromisoformat((value or "1970-01-01T00:00:00").replace("Z", "+00:00"))
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).isoformat().replace("+00:00", "Z")


def assessment_results(inventory: dict[str, object], mapping: MappingDocument) -> dict[str, object]:
    source = inventory["source"]
    run_id = _uuid(source["sha256"], mapping.sha256)
    resources = [{"uuid": _uuid(source["sha256"]), "title": f"Source XCCDF Results: {source['path']}", "props": [{"name": "source-artifact-type", "ns": NAMESPACE, "value": "xccdf-results"}], "rlinks": [{"href": source["path"], "media-type": "application/xml", "hashes": [{"algorithm": "SHA-256", "value": source["sha256"]}]}]}, {"uuid": _uuid(mapping.sha256), "title": f"Source XCCDF mapping: {mapping.path.name}", "props": [{"name": "source-artifact-type", "ns": NAMESPACE, "value": "xccdf-oscal-mapping"}], "rlinks": [{"href": mapping.path.name, "media-type": "application/json", "hashes": [{"algorithm": "SHA-256", "value": mapping.sha256}]}]}]
    observations, findings = [], []
    start = _time(inventory["test-results"][0].get("start-time"))
    for test in inventory["test-results"]:
        benchmark_id = test["benchmark"]["id"]
        for rule in test["rule-results"]:
            observation_id = _uuid(run_id, test["id"], rule["idref"])
            props = [{"name": "xccdf-benchmark-id", "ns": NAMESPACE, "value": benchmark_id}, {"name": "xccdf-test-result-id", "ns": NAMESPACE, "value": test["id"]}, {"name": "xccdf-rule-id", "ns": NAMESPACE, "value": rule["idref"]}, {"name": "xccdf-result", "ns": NAMESPACE, "value": rule["result"]}]
            observations.append({"uuid": observation_id, "title": f"XCCDF rule result: {rule['idref']}", "description": "Evidence converted from XCCDF without inferring a control finding.", "methods": ["TEST"], "collected": _time(rule.get("time") or test.get("end-time")), "types": ["discovery"], "props": props, "relevant-evidence": [{"href": "#" + _uuid(source["sha256"]), "description": "XCCDF Results source evidence."}]})
            for entry in mapping.mappings:
                outcome = entry.outcomes.get(rule["result"])
                if entry.benchmark_id == benchmark_id and entry.rule_id == rule["idref"] and outcome:
                    findings.append({"uuid": _uuid(run_id, rule["idref"], entry.target.type, entry.target.identifier), "title": f"Mapped XCCDF evaluation: {rule['idref']}", "description": f"Explicit mapping of XCCDF rule {rule['idref']} to {entry.target.type} {entry.target.identifier}.", "props": [{"name": "xccdf-rule-id", "ns": NAMESPACE, "value": rule["idref"]}, {"name": "xccdf-result", "ns": NAMESPACE, "value": rule["result"]}, {"name": "mapping-sha256", "ns": NAMESPACE, "value": mapping.sha256}, {"name": "source-observation-uuid", "ns": NAMESPACE, "value": observation_id}], "target": {"type": entry.target.type, "target-id": entry.target.identifier, "status": outcome}})
    result = {"uuid": _uuid(run_id, "result"), "title": "XCCDF evaluation evidence", "description": "Evidence converted from XCCDF Results without inferring control findings.", "start": start, "end": start, "reviewed-controls": {"control-selections": [{"include-all": {}}]}, "observations": observations}
    if findings: result["findings"] = findings
    return {"assessment-results": {"uuid": run_id, "metadata": {"title": "Endeavor XCCDF assessment results", "last-modified": start, "version": "0.2.0a0", "oscal-version": "1.2.0"}, "import-ap": {"href": "REQUIRED-ASSESSMENT-PLAN.oscal.json"}, "results": [result], "back-matter": {"resources": resources}}}
