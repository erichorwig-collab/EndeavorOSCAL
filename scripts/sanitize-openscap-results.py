#!/usr/bin/env python3
"""Sanitize disposable-container identifiers in a generated OVAL Results file."""

from __future__ import annotations

import argparse
from pathlib import Path

from lxml import etree as ET


SYSTEM_NS = "http://oval.mitre.org/XMLSchema/oval-system-characteristics-5"


def q(name: str) -> str:
    return f"{{{SYSTEM_NS}}}{name}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    tree = ET.parse(str(args.input), ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False))
    system_info = tree.find(f".//{q('system_info')}")
    if system_info is None:
        raise ValueError("generated Results has no system_info")
    hostname = system_info.find(q("primary_host_name"))
    interfaces = system_info.find(q("interfaces"))
    if hostname is None or interfaces is None:
        raise ValueError("generated Results has incomplete system_info")
    hostname.text = "endeavor-oval-fixture"
    interfaces.clear()
    interface = ET.SubElement(interfaces, q("interface"))
    ET.SubElement(interface, q("interface_name")).text = "loopback"
    ET.SubElement(interface, q("ip_address")).text = "127.0.0.1"
    ET.SubElement(interface, q("mac_address")).text = "00:00:00:00:00:00"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(args.output), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
