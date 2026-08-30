"""Safe, deterministic finding inventory for converted Assessment Results."""

from __future__ import annotations

from .diff import NAMESPACE, _read_json
from .oval import OvalInputError


def findings_report(path):
    document, sha256 = _read_json(path)
    assessment_results = document.get("assessment-results")
    if not isinstance(assessment_results, dict) or not isinstance(assessment_results.get("results"), list):
        raise OvalInputError(f"assessment results has an unsupported shape: {path.name}")
    findings = []
    for result in assessment_results["results"]:
        if not isinstance(result, dict) or not isinstance(result.get("findings", []), list):
            raise OvalInputError(f"assessment results has an unsupported shape: {path.name}")
        for finding in result.get("findings", []):
            if not isinstance(finding, dict) or not isinstance(finding.get("target"), dict) or not isinstance(finding.get("props", []), list):
                raise OvalInputError(f"assessment results has an unsupported shape: {path.name}")
            props = {(item.get("name"), item.get("ns")): item.get("value") for item in finding["props"] if isinstance(item, dict)}
            target = finding["target"]
            status = target.get("status")
            if not all(isinstance(finding.get(key), str) for key in ("uuid", "title")) or not isinstance(target.get("type"), str) or not isinstance(target.get("target-id"), str) or not isinstance(status, dict) or not isinstance(status.get("state"), str):
                raise OvalInputError(f"assessment results has invalid finding data: {path.name}")
            findings.append({
                "uuid": finding["uuid"],
                "title": finding["title"],
                "oval-definition-id": props.get(("oval-definition-id", NAMESPACE)),
                "oval-result": props.get(("oval-result", NAMESPACE)),
                "target": {"type": target["type"], "target-id": target["target-id"], "state": status["state"], "reason": status.get("reason")},
            })
    findings.sort(key=lambda item: (str(item["oval-definition-id"]), str(item["target"]["type"]), str(item["target"]["target-id"])))
    return {"format": "endeavor-findings", "version": "1.0.0", "assessment-results": {"path": path.name, "sha256": sha256}, "summary": {"findings": len(findings)}, "findings": findings}
