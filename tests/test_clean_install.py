"""Packaging smoke tests that execute the installed Endeavor CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "fixtures" / "oval-results" / "pass.xml"
DEFINITIONS = ROOT / "fixtures" / "oval-definitions" / "definitions.xml"
PACKAGE_VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


class CleanInstallTests(unittest.TestCase):
    def test_clean_install_exposes_console_script_and_vendored_schemas(self) -> None:
        """A wheel-style installation must work outside the source checkout."""

        with tempfile.TemporaryDirectory(prefix="endeavor-clean-install-") as directory:
            workspace = Path(directory)
            environment = workspace / "venv"
            create = subprocess.run(
                [sys.executable, "-m", "venv", str(environment)],
                cwd=workspace,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(create.returncode, 0, create.stderr)
            scripts = environment / ("Scripts" if os.name == "nt" else "bin")
            python = scripts / ("python.exe" if os.name == "nt" else "python")
            endeavor = scripts / ("endeavor.exe" if os.name == "nt" else "endeavor")
            installed = subprocess.run(
                [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(ROOT)],
                cwd=workspace,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            isolated_environment = os.environ.copy()
            isolated_environment.pop("PYTHONPATH", None)
            isolated_environment["PYTHONNOUSERSITE"] = "1"
            location = subprocess.run(
                [str(python), "-c", "import endeavor; print(endeavor.__file__)"],
                cwd=workspace,
                env=isolated_environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(location.returncode, 0, location.stderr)
            self.assertTrue(location.stdout.strip().startswith(str(environment)), location.stdout)
            versions = subprocess.run(
                [str(python), "-c", "from importlib.metadata import version; import endeavor; print(version('endeavor-oscal')); print(endeavor.__version__)"],
                cwd=workspace,
                env=isolated_environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(versions.returncode, 0, versions.stderr)
            self.assertEqual(versions.stdout.splitlines(), [PACKAGE_VERSION, PACKAGE_VERSION])
            completed = subprocess.run(
                [str(endeavor), "inspect", "--results", str(RESULTS), "--definitions", str(DEFINITIONS)],
                cwd=workspace,
                env=isolated_environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["results"]["path"], "pass.xml")
