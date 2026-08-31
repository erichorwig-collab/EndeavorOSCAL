#!/usr/bin/env python3
"""Sanitize target facts in generated OpenSCAP XCCDF Results."""

from __future__ import annotations

import argparse
import ipaddress
from pathlib import Path

from lxml import etree as ET


SYSTEM_NS = "http://oval.mitre.org/XMLSchema/oval-system-characteristics-5"
XCCDF_NS = "http://checklists.nist.gov/xccdf/1.2"


def _target_address(value: str) -> str | None:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return None
    return "127.0.0.1" if address.version == 4 else "0:0:0:0:0:0:0:1"


def _fact_replacement(name: str) -> str | None:
    normalized = name.lower()
    if normalized.endswith(("fqdn", "host_name", "hostname")):
        return "endeavor-target.invalid"
    if normalized.endswith(("mac", "mac_address")):
        return "00:00:00:00:00:00"
    if normalized.endswith("ipv4"):
        return "127.0.0.1"
    if normalized.endswith("ipv6"):
        return "0:0:0:0:0:0:0:1"
    return None


def sanitize_tree(tree: ET._ElementTree) -> None:
    """Replace schema-defined target facts while preserving execution meaning."""
    hostnames = {
        item.text
        for item in tree.iter()
        if isinstance(item.tag, str)
        and ET.QName(item).namespace == SYSTEM_NS
        and ET.QName(item).localname == "primary_host_name"
        and item.text
    }
    hostnames.update(
        item.text
        for item in tree.iter()
        if isinstance(item.tag, str)
        and ET.QName(item).namespace == XCCDF_NS
        and ET.QName(item).localname == "fact"
        and _fact_replacement(item.get("name", "")) == "endeavor-target.invalid"
        and item.text
    )
    hostnames.update(name.split(".", 1)[0] for name in tuple(hostnames) if "." in name)
    for item in tree.iter():
        if not isinstance(item.tag, str):
            continue
        name = ET.QName(item)
        if name.namespace == SYSTEM_NS:
            if name.localname == "primary_host_name":
                item.text = "endeavor-target"
            elif name.localname == "ip_address":
                item.text = "127.0.0.1"
            elif name.localname == "mac_address":
                item.text = "00:00:00:00:00:00"
        elif name.namespace == XCCDF_NS:
            if name.localname == "identity":
                item.text = "endeavor-fixture-user"
            elif name.localname == "target" and item.text in hostnames:
                item.text = "endeavor-target"
            elif name.localname == "target-address" and item.text:
                item.text = _target_address(item.text) or item.text
            elif name.localname == "fact":
                replacement = _fact_replacement(item.get("name", ""))
                if replacement is not None:
                    item.text = replacement


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    tree = ET.parse(str(args.input), ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False))
    sanitize_tree(tree)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(args.output), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
