#!/usr/bin/env python3
"""Sanitize target facts in a generated ARF without altering SCAP metadata."""

from __future__ import annotations

import argparse
import ipaddress
from pathlib import Path

from lxml import etree as ET


ASSET_IDENTIFICATION_NS = "http://scap.nist.gov/schema/asset-identification/1.1"
OVAL_SYSTEM_NS = "http://oval.mitre.org/XMLSchema/oval-system-characteristics-5"
XCCDF_NS = "http://checklists.nist.gov/xccdf/1.2"

TARGET_FACTS = {
    (ASSET_IDENTIFICATION_NS, "hostname"): "endeavor-target",
    (ASSET_IDENTIFICATION_NS, "fqdn"): "endeavor-target.invalid",
    (ASSET_IDENTIFICATION_NS, "ip-v4"): "127.0.0.1",
    (ASSET_IDENTIFICATION_NS, "ip-v6"): "0:0:0:0:0:0:0:1",
    (ASSET_IDENTIFICATION_NS, "mac-address"): "00:00:00:00:00:00",
    (OVAL_SYSTEM_NS, "primary_host_name"): "endeavor-target",
    (OVAL_SYSTEM_NS, "ip_address"): "127.0.0.1",
    (OVAL_SYSTEM_NS, "mac_address"): "00:00:00:00:00:00",
    (XCCDF_NS, "identity"): "endeavor-fixture-user",
}


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
    """Replace only schema-defined target facts, never generic ARF content."""
    hostnames = {
        item.text
        for item in tree.iter()
        if isinstance(item.tag, str)
        and ET.QName(item).namespace in (ASSET_IDENTIFICATION_NS, OVAL_SYSTEM_NS)
        and ET.QName(item).localname in ("hostname", "fqdn", "primary_host_name")
        and item.text
    }
    for item in tree.iter():
        if not isinstance(item.tag, str):
            continue
        qualified_name = ET.QName(item)
        replacement = TARGET_FACTS.get((qualified_name.namespace, qualified_name.localname))
        if replacement is not None:
            item.text = replacement
        elif qualified_name.namespace == XCCDF_NS and qualified_name.localname == "target" and item.text in hostnames:
            item.text = "endeavor-target"
        elif qualified_name.namespace == XCCDF_NS and qualified_name.localname == "target-address" and item.text:
            item.text = _target_address(item.text) or item.text
        elif qualified_name.namespace == XCCDF_NS and qualified_name.localname == "fact":
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
