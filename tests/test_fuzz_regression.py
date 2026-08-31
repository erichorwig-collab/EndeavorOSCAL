from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FuzzRegressionTests(unittest.TestCase):
    def test_fixed_seed_mutation_corpus_is_reproducible_and_bounded(self) -> None:
        command = [sys.executable, "scripts/fuzz-untrusted-xml.py", "--seed", "20260831", "--cases", "18"]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["format"], "endeavor-untrusted-xml-fuzz-regression")
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(len(payload["cases"]), 18)
        self.assertEqual({item["source"] for item in payload["cases"]}, {"oval-results", "xccdf-results", "arf-collection"})
        self.assertGreaterEqual(sum(item["outcome"] == "accepted-identical" for item in payload["cases"]), 3)

    def test_mutation_corpus_rejects_an_unbounded_case_count(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/fuzz-untrusted-xml.py", "--cases", "97"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("cases must be between 18 and 96", completed.stderr)
