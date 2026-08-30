#!/usr/bin/env python3
"""Exercise the representative mapped-evidence workflow used for alpha exit."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "fixtures" / "oval-results"
DEFINITIONS = ROOT / "fixtures" / "oval-definitions" / "definitions.xml"
MAPPING = ROOT / "fixtures" / "mappings" / "example-v1.json"
SCHEMA = ROOT / "endeavor" / "schemas" / "oscal-1.2.0" / "assessment-results.schema.json"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(args)}\n{completed.stderr}")
    return completed


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="endeavor-alpha-workflow-") as directory:
        output = Path(directory)
        passed = output / "pass.json"
        failed = output / "fail.json"
        report = output / "mapping-report.html"
        base = (sys.executable, "-m", "endeavor", "convert", "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING))
        run(*base, "--results", str(RESULTS / "pass.xml"), "--output", str(passed))
        run(*base, "--results", str(RESULTS / "fail.xml"), "--output", str(failed))
        coverage = json.loads(run(sys.executable, "-m", "endeavor", "mapping-report", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING)).stdout)
        run("npm", "run", "validate:oscal", "--", str(SCHEMA), str(passed))
        run("npm", "run", "validate:oscal", "--", str(SCHEMA), str(failed))
        findings = json.loads(run(sys.executable, "-m", "endeavor", "findings", "--results", str(failed)).stdout)
        delta = json.loads(run(sys.executable, "-m", "endeavor", "diff", "--before", str(passed), "--after", str(failed)).stdout)
        run(sys.executable, "-m", "endeavor", "report", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING), "--output", str(report))
        html = report.read_text(encoding="utf-8")
        assert coverage["summary"] == {"evaluated": 1, "mapped": 1, "unmapped": 0, "stale-mappings": 0}
        assert findings["summary"] == {"findings": 1}
        assert findings["findings"][0]["target"]["state"] == "not-satisfied"
        assert delta["changed"] == [{"oval-definition-id": "oval:org.endeavor:def:1", "before": "true", "after": "false"}]
        assert "<main>" in html and 'scope="col"' in html and "example-v1.json" in html
        record = {"format": "endeavor-alpha-workflow-validation", "version": "1.0.0", "status": "passed", "artifacts": {"pass.json": hashlib.sha256(passed.read_bytes()).hexdigest(), "fail.json": hashlib.sha256(failed.read_bytes()).hexdigest(), "mapping-report.html": hashlib.sha256(report.read_bytes()).hexdigest()}}
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
