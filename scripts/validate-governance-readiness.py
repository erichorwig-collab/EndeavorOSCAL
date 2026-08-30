#!/usr/bin/env python3
"""Validate deterministic evidence required to begin Governance planning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "docs/alpha-acceptance-record-2026-08-30.md",
    "docs/compatibility-matrix.md",
    "docs/dependency-policy.md",
    "docs/governance-readiness.md",
    "docs/quality-and-accessibility.md",
    "sbom.cdx.json",
)
ACCEPTANCE_MARKER = "> Status: **accepted** by the named reviewer below."
CONCLUSION_MARKER = "- [x] Accepted for the alpha gate."


def main() -> int:
    missing = [relative for relative in REQUIRED_FILES if not (ROOT / relative).is_file()]
    record_path = ROOT / REQUIRED_FILES[0]
    if record_path.is_file():
        record = record_path.read_text(encoding="utf-8")
        if ACCEPTANCE_MARKER not in record or CONCLUSION_MARKER not in record:
            missing.append("accepted alpha conclusion")
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
