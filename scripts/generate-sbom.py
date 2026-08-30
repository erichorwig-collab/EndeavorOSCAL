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


def _component(*, name: str, version: str, purl: str, component_type: str, license_id: str | None = None, scope: str | None = None) -> dict[str, object]:
    component: dict[str, object] = {"type": component_type, "name": name, "version": version, "purl": purl, "bom-ref": purl}
    if license_id:
        component["licenses"] = [{"license": {"id": license_id}}]
    if scope:
        component["scope"] = scope
    return component


def generate() -> dict[str, object]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    lxml_dependency = next((item for item in project["dependencies"] if item.startswith("lxml==")), None)
    if lxml_dependency is None:
        raise ValueError("pyproject.toml must exactly pin lxml for the SBOM")
    lxml_version = lxml_dependency.removeprefix("lxml==")
    if (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines() != [lxml_dependency]:
        raise ValueError("requirements.txt must match the pinned lxml runtime dependency")
    name = project["name"]
    version = project["version"]
    root_purl = f"pkg:generic/{name}@{version}"
    components = [_component(name="lxml", version=lxml_version, purl=f"pkg:pypi/lxml@{lxml_version}", component_type="library", license_id="BSD-3-Clause", scope="required")]
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
