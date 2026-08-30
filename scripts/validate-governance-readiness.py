#!/usr/bin/env python3
"""Validate deterministic evidence required to begin Governance planning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "SECURITY.md",
    ".github/dependabot.yml",
    ".github/workflows/scorecard.yml",
    ".github/workflows/dependency-review.yml",
    ".github/workflows/osv-scanner.yml",
    "docs/alpha-acceptance-record-2026-08-30.md",
    "docs/compatibility-matrix.md",
    "docs/dependency-policy.md",
    "docs/governance-readiness.md",
    "docs/quality-and-accessibility.md",
    "security/vulnerability-exceptions.json",
    "security/vulnerability-exceptions.schema.json",
    "sbom.cdx.json",
)
ACCEPTANCE_RECORD = "docs/alpha-acceptance-record-2026-08-30.md"
ACCEPTANCE_MARKER = "> Status: **accepted** by the named reviewer below."
CONCLUSION_MARKER = "- [x] Accepted for the alpha gate."


def main() -> int:
    missing = [relative for relative in REQUIRED_FILES if not (ROOT / relative).is_file()]
    record_path = ROOT / ACCEPTANCE_RECORD
    if record_path.is_file():
        record = record_path.read_text(encoding="utf-8")
        if ACCEPTANCE_MARKER not in record or CONCLUSION_MARKER not in record:
            missing.append("accepted alpha conclusion")
    security_path = ROOT / "SECURITY.md"
    if security_path.is_file() and "Report a vulnerability" not in security_path.read_text(encoding="utf-8"):
        missing.append("private vulnerability-reporting instructions")
    dependabot_path = ROOT / ".github" / "dependabot.yml"
    if dependabot_path.is_file() and "package-ecosystem: github-actions" not in dependabot_path.read_text(encoding="utf-8"):
        missing.append("GitHub Actions dependency updates")
    scorecard_path = ROOT / ".github" / "workflows" / "scorecard.yml"
    if scorecard_path.is_file():
        scorecard = scorecard_path.read_text(encoding="utf-8")
        if "permissions: read-all" not in scorecard or "ossf/scorecard-action@" not in scorecard:
            missing.append("least-privilege Scorecard workflow")
    exception_check = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-vulnerability-exceptions.py")], cwd=ROOT, text=True, capture_output=True, check=False)
    if exception_check.returncode:
        missing.append("valid, unexpired vulnerability exception record")
    for relative in (".github/workflows/validate.yml", ".github/workflows/scorecard.yml", ".github/workflows/dependency-review.yml", ".github/workflows/osv-scanner.yml"):
        path = ROOT / relative
        if path.is_file():
            actions = re.findall(r"^\s*uses:\s+[^@\s]+@([^\s#]+)", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
            if not actions or any(not re.fullmatch(r"[0-9a-f]{40}", action) for action in actions):
                missing.append(f"pinned GitHub Actions in {relative}")
    payload: dict[str, object] = {
        "format": "endeavor-governance-readiness",
        "version": "1.0.0",
        "status": "ready-for-governance-planning" if not missing else "incomplete",
        "evidence": {
            relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            for relative in REQUIRED_FILES
            if (ROOT / relative).is_file()
        },
        "deferred-scope": [
            "ARF archive/container ingestion",
            "tailoring-decision interpretation",
            "source-to-OSCAL scope expansion",
            "trusted vulnerability scanner and exception process",
            "production release controls",
        ],
    }
    if missing:
        payload["missing"] = sorted(missing)
    print(json.dumps(payload, sort_keys=True))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
