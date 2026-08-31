#!/usr/bin/env python3
"""Clean-install Endeavor's built wheel and source distribution outside the checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "fixtures" / "oval-results" / "pass.xml"
DEFINITIONS = ROOT / "fixtures" / "oval-definitions" / "definitions.xml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scripts_directory(environment: Path) -> Path:
    return environment / ("Scripts" if os.name == "nt" else "bin")


def verify(artifact: Path, package_version: str) -> dict[str, str]:
    if not artifact.is_file() or artifact.is_symlink():
        raise ValueError(f"artifact must be a regular file: {artifact.name}")
    with tempfile.TemporaryDirectory(prefix="endeavor-distribution-install-") as temporary:
        workspace = Path(temporary)
        environment = workspace / "venv"
        created = subprocess.run([sys.executable, "-m", "venv", str(environment)], cwd=workspace, text=True, capture_output=True, check=False)
        if created.returncode:
            raise ValueError(created.stderr.strip() or "could not create clean virtual environment")
        scripts = scripts_directory(environment)
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        endeavor = scripts / ("endeavor.exe" if os.name == "nt" else "endeavor")
        installed = subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(artifact)], cwd=workspace, text=True, capture_output=True, check=False)
        if installed.returncode:
            raise ValueError(installed.stderr.strip() or f"could not install {artifact.name}")
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONNOUSERSITE"] = "1"
        location = subprocess.run(
            [str(python), "-c", "import endeavor; print(endeavor.__file__)"],
            cwd=workspace,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if location.returncode or not location.stdout.strip().startswith(str(environment)):
            raise ValueError(f"installed package was not imported from the clean environment for {artifact.name}")
        version = subprocess.run([str(python), "-c", "from importlib.metadata import version; import endeavor; print(version('endeavor-oscal')); print(endeavor.__version__)"], cwd=workspace, env=env, text=True, capture_output=True, check=False)
        if version.returncode or version.stdout.splitlines() != [package_version, package_version]:
            raise ValueError(f"installed package version did not match {package_version!r}")
        inspected = subprocess.run([str(endeavor), "inspect", "--results", str(RESULTS), "--definitions", str(DEFINITIONS)], cwd=workspace, env=env, text=True, capture_output=True, check=False)
        if inspected.returncode:
            raise ValueError(inspected.stderr.strip() or f"installed console script failed for {artifact.name}")
        if json.loads(inspected.stdout)["results"]["path"] != "pass.xml":
            raise ValueError(f"installed console script returned an unexpected inspection payload for {artifact.name}")
    return {"filename": artifact.name, "sha256": sha256(artifact)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--sdist", type=Path, required=True)
    parser.add_argument("--package-version", required=True)
    args = parser.parse_args(argv)
    try:
        payload = {
            "format": "endeavor-python-distribution-validation",
            "version": "1.0.0",
            "status": "passed",
            "artifacts": {
                "wheel": verify(args.wheel, args.package_version),
                "sdist": verify(args.sdist, args.package_version),
            },
        }
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"python distribution validation failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
