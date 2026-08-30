#!/usr/bin/env python3
"""Sanitize only disposable-container identifiers in a generated ARF."""

from __future__ import annotations

import argparse
from pathlib import Path

from lxml import etree as ET


REPLACEMENTS = {
    "fec021b96364": "endeavor-tailoring-fixture",
    "172.17.0.2": "127.0.0.1",
    "1E:C4:02:04:C5:95": "00:00:00:00:00:00",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    tree = ET.parse(str(args.input), ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False))
    for item in tree.iter():
        if item.text:
            for source, replacement in REPLACEMENTS.items():
                item.text = item.text.replace(source, replacement)
        for name, value in item.attrib.items():
            for source, replacement in REPLACEMENTS.items():
                value = value.replace(source, replacement)
            item.set(name, value)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(args.output), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
