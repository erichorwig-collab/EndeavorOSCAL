"""Tests for deterministic accessibility validation of generated reports."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "fixtures" / "oval-results" / "fail.xml"
DEFINITIONS = ROOT / "fixtures" / "oval-definitions" / "definitions.xml"
MAPPING = ROOT / "fixtures" / "mappings" / "example-v1.json"
VALIDATOR = ROOT / "scripts" / "validate-report-accessibility.py"


class ReportAccessibilityTests(unittest.TestCase):
    def test_generated_mapping_report_passes_static_accessibility_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "mapping-report.html"
            generated = subprocess.run(
                [sys.executable, "-m", "endeavor", "report", "--results", str(RESULTS), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING), "--output", str(report)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            validated = subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(json.loads(validated.stdout)["status"], "passed")

    def test_static_validator_fails_closed_for_missing_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "incomplete.html"
            report.write_text("<!doctype html><html><body><table><tr><td>missing</td></tr></table></body></html>", encoding="utf-8")
            validated = subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validated.returncode, 1)
            payload = json.loads(validated.stderr)
            self.assertEqual(payload["status"], "failed")
            self.assertIn("document must have one html element with lang", payload["violations"])
