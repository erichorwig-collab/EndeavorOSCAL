#!/usr/bin/env python3
"""Generate Endeavor's deterministic CycloneDX dependency inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tomllib
from uuid import NAMESPACE_URL, uuid5


ROOT = Path(__file__).resolve().parents[1]
BUILD_TOOLCHAIN = (
    ("build", "1.3.0", "MIT"),
    ("packaging", "26.3", "Apache-2.0 OR BSD-2-Clause"),
    ("pyproject-hooks", "1.2.0", "MIT"),
    ("setuptools", "83.0.0", "MIT"),
)


def _component(*, name: str, version: str, purl: str, component_type: str, license_id: str | None = None, license_expression: str | None = None, scope: str | None = None) -> dict[str, object]:
    component: dict[str, object] = {"type": component_type, "name": name, "version": version, "purl": purl, "bom-ref": purl}
    if license_id:
        component["licenses"] = [{"license": {"id": license_id}}]
    if license_expression:
        component["licenses"] = [{"license": {"expression": license_expression}}]
    if scope:
        component["scope"] = scope
    return component


def generate() -> dict[str, object]:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    lxml_dependency = next((item for item in project["dependencies"] if item.startswith("lxml==")), None)
    if lxml_dependency is None:
        raise ValueError("pyproject.toml must exactly pin lxml for the SBOM")
    lxml_version = lxml_dependency.removeprefix("lxml==")
    if (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines() != [lxml_dependency]:
        raise ValueError("requirements.txt must match the pinned lxml runtime dependency")
    expected_build_requirements = [f"{name.replace('-', '_')}=={version}" for name, version, _ in BUILD_TOOLCHAIN[:-1]]
    if (ROOT / "requirements-release-build.txt").read_text(encoding="utf-8").splitlines() != ["# Pinned PEP 517 frontend and its direct runtime dependencies for release builds.", *expected_build_requirements]:
        raise ValueError("requirements-release-build.txt must match the pinned release build toolchain")
    build_system = pyproject.get("build-system", {})
    if build_system.get("requires") != ["setuptools==83.0.0"]:
        raise ValueError("pyproject.toml must pin setuptools for release builds")
    name = project["name"]
    version = project["version"]
    root_purl = f"pkg:generic/{name}@{version}"
    components = [_component(name="lxml", version=lxml_version, purl=f"pkg:pypi/lxml@{lxml_version}", component_type="library", license_id="BSD-3-Clause", scope="required")]
    for build_name, build_version, build_license in BUILD_TOOLCHAIN:
        purl = f"pkg:pypi/{build_name}@{build_version}"
        if " OR " in build_license:
            components.append(_component(name=build_name, version=build_version, purl=purl, component_type="library", license_expression=build_license, scope="optional"))
        else:
            components.append(_component(name=build_name, version=build_version, purl=purl, component_type="library", license_id=build_license, scope="optional"))
    for location, package in sorted(lock["packages"].items()):
        if not location.startswith("node_modules/"):
            continue
        package_name = location.removeprefix("node_modules/")
        components.append(_component(name=package_name, version=package["version"], purl=f"pkg:npm/{package_name}@{package['version']}", component_type="library", license_id=package.get("license"), scope="optional" if package.get("dev") else "required"))
    components.sort(key=lambda item: str(item["bom-ref"]))
    references = [str(component["bom-ref"]) for component in components]
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid5(NAMESPACE_URL, root_purl)}",
        "version": 1,
        "metadata": {"component": _component(name=name, version=version, purl=root_purl, component_type="application", license_id="Apache-2.0")},
        "components": components,
        "dependencies": [{"ref": root_purl, "dependsOn": references}],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "sbom.cdx.json")
    parser.add_argument("--check", type=Path, metavar="PATH", help="fail if PATH differs from generated output")
    args = parser.parse_args(argv)
    rendered = json.dumps(generate(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.check.is_file() or args.check.read_text(encoding="utf-8") != rendered:
            print(f"SBOM is stale: {args.check}", file=sys.stderr)
            return 1
        return 0
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
