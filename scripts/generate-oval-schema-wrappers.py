#!/usr/bin/env python3
"""Generate static trusted OVAL wrapper schemas from one vendored release."""

from __future__ import annotations

import argparse
from pathlib import Path

from lxml import etree as ET


XSD_NS = "http://www.w3.org/2001/XMLSchema"


def namespace(path: Path) -> str:
    root = ET.parse(str(path)).getroot()
    value = root.get("targetNamespace")
    if not value:
        raise ValueError(f"no target namespace in {path}")
    return value


def wrapper(imports: list[tuple[str, str]]) -> bytes:
    root = ET.Element(f"{{{XSD_NS}}}schema", nsmap={"xsd": XSD_NS})
    root.insert(0, ET.Comment("Trusted local wrapper: document xsi schema hints are never used."))
    for target_namespace, name in imports:
        ET.SubElement(root, f"{{{XSD_NS}}}import", namespace=target_namespace, schemaLocation=name)
    return ET.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def extensions(root: Path, suffix: str, core_name: str) -> list[tuple[str, str]]:
    files = sorted(path for path in root.glob(f"*{suffix}") if path.name != core_name)
    return [(namespace(path), path.name) for path in files]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema_root", type=Path)
    args = parser.parse_args()
    root = args.schema_root.resolve()
    definitions_core = root / "oval-definitions-schema.xsd"
    results_core = root / "oval-results-schema.xsd"
    definitions = [(namespace(definitions_core), definitions_core.name)] + extensions(root, "-definitions-schema.xsd", definitions_core.name)
    systems = extensions(root, "-system-characteristics-schema.xsd", "oval-system-characteristics-schema.xsd")
    (root / "endeavor-definitions-wrapper.xsd").write_bytes(wrapper(definitions))
    (root / "endeavor-results-wrapper.xsd").write_bytes(wrapper([(namespace(results_core), results_core.name), *definitions[1:], *systems]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
