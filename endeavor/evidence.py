"""Pure provenance-only normalizers for the v0.2 cross-format contract."""
from __future__ import annotations


def _source(source: dict[str, str], kind: str, role: str) -> dict[str, str]:
    return {"id": f"sha256:{source['sha256']}", "kind": kind, "path": source["path"], "sha256": source["sha256"], "schema-version": source.get("xccdf-version", source.get("arf-version", "unknown")), "role": role}


def normalize_xccdf(inventory: dict[str, object]) -> dict[str, object]:
    source = _source(inventory["source"], "xccdf-results", "results")
    executions, assertions = [], []
    for result in inventory["test-results"]:
        execution_id = f"{source['id']}#{result['id']}"
        executions.append({"id": execution_id, "source-id": source["id"], "native-id": result["id"], "format": "xccdf", "evaluator": {"test-system": result.get("test-system")}, "start-time": result.get("start-time"), "end-time": result.get("end-time"), "profile": result.get("profile"), "benchmark": result.get("benchmark"), "tailoring": result.get("tailoring"), "targets": {"names": result.get("targets", []), "addresses": result.get("target-addresses", []), "facts": result.get("target-facts", []), "references": []}})
        for rule in result.get("rule-results", []):
            assertions.append({"id": f"{execution_id}#{rule['idref']}", "execution-id": execution_id, "kind": "xccdf-rule-result", "native-id": rule["idref"], "status": rule["result"], "details": {"time": rule.get("time"), "weight": rule.get("weight")}, "evidence": [source["id"]], "links": {"arf-report-id": None, "arf-collection-id": None, "definitions-component-id": None}})
    return {"format": "endeavor-evidence-contract", "version": "1.0.0", "sources": [source], "executions": executions, "assertions": assertions}


def normalize_arf(manifest: dict[str, object]) -> dict[str, object]:
    source = _source(manifest["source"], "arf", "collection")
    sources, executions, assertions = [source], [], []
    for report in manifest["reports"]:
        content = report["content"]
        report_source = {"id": f"{source['id']}#{report['id']}", "kind": "arf-report", "path": source["path"], "sha256": content["sha256"], "schema-version": content["namespace"], "role": "report"}
        sources.append(report_source)
        if "xccdf-result" in report:
            result = report["xccdf-result"]
            execution_id = f"{report_source['id']}#{result['id']}"
            executions.append({"id": execution_id, "source-id": report_source["id"], "native-id": result["id"], "format": "xccdf", "evaluator": {"test-system": result.get("test-system")}, "start-time": result.get("start-time"), "end-time": result.get("end-time"), "profile": result.get("profile"), "benchmark": result.get("benchmark"), "tailoring": result.get("tailoring"), "targets": {"names": result.get("targets", []), "addresses": result.get("target-addresses", []), "facts": result.get("target-facts", []), "references": result.get("target-references", [])}, "asset": {"arf-asset-id": report.get("asset-id")}})
            for rule in result.get("rule-results", []):
                assertions.append({"id": f"{execution_id}#{rule['idref']}", "execution-id": execution_id, "kind": "xccdf-rule-result", "native-id": rule["idref"], "status": rule["result"], "details": {"time": rule.get("time"), "severity": rule.get("severity"), "weight": rule.get("weight")}, "evidence": [source["id"], report_source["id"]], "links": {"arf-report-id": report["id"], "arf-collection-id": report.get("collection-id"), "definitions-component-id": None}})
        if "oval-result" in report:
            execution_id = f"{report_source['id']}#oval-results"
            executions.append({"id": execution_id, "source-id": report_source["id"], "native-id": "oval-results", "format": "oval", "evaluator": {}, "start-time": None, "end-time": None, "profile": None, "benchmark": None, "tailoring": None, "targets": {"names": [], "addresses": [], "facts": [], "references": []}})
            for item in report["oval-result"]["definition-results"]:
                assertions.append({"id": f"{execution_id}#{item['id']}", "execution-id": execution_id, "kind": "oval-definition-result", "native-id": item["id"], "status": item["result"], "details": {}, "evidence": [source["id"], report_source["id"]], "links": {"arf-report-id": report["id"], "arf-collection-id": None, "definitions-component-id": None}})
    return {"format": "endeavor-evidence-contract", "version": "1.0.0", "sources": sources, "executions": executions, "assertions": assertions}
