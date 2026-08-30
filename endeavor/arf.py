"""Bounded ARF 1.1 collection-manifest intake for the Phase 4 expansion."""
from __future__ import annotations

import hashlib
import re
import stat
from pathlib import Path

from lxml import etree as ET

from .oval import OvalInputError

MAX_ARF_BYTES = 5 * 1024 * 1024
MAX_ARF_ELEMENTS = 50_000
ARF_NS = "http://scap.nist.gov/schema/asset-reporting-format/1.1"
CORE_NS = "http://scap.nist.gov/schema/reporting-core/1.1"
FORBIDDEN_XML = re.compile(br"<!DOCTYPE|<!ENTITY", re.I)


def _q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def _safe(path: Path) -> str:
    return path.name or "arf"


def _read(path: Path) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise OvalInputError(f"ARF input does not exist: {_safe(path)}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise OvalInputError(f"ARF input must be a regular non-symlink file: {_safe(path)}")
    if metadata.st_size > MAX_ARF_BYTES:
        raise OvalInputError(f"ARF input exceeds {MAX_ARF_BYTES} byte limit: {_safe(path)}")
    data = path.read_bytes()
    if FORBIDDEN_XML.search(data):
        raise OvalInputError(f"DOCTYPE and ENTITY declarations are not supported: {_safe(path)}")
    return data


def _content_record(parent: ET._Element, path: Path) -> dict[str, str | None]:
    content = parent.find(_q(ARF_NS, "content"))
    if content is None or len(content) != 1:
        raise OvalInputError(f"ARF content must contain exactly one component: {_safe(path)}")
    component = content[0]
    return {
        "namespace": ET.QName(component).namespace,
        "name": ET.QName(component).localname,
        "id": component.get("id"),
        "sha256": hashlib.sha256(ET.tostring(component, method="c14n", with_comments=False)).hexdigest(),
    }


def inspect_arf(path: Path) -> dict[str, object]:
    data = _read(path)
    try:
        root = ET.fromstring(data, parser=ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, recover=False))
    except ET.XMLSyntaxError as exc:
        raise OvalInputError(f"malformed XML in {_safe(path)}: {exc}") from exc
    if sum(1 for _ in root.iter()) > MAX_ARF_ELEMENTS:
        raise OvalInputError(f"ARF input exceeds {MAX_ARF_ELEMENTS} element limit: {_safe(path)}")
    if root.tag != _q(ARF_NS, "asset-report-collection"):
        raise OvalInputError(f"unsupported ARF root element: {_safe(path)}")
    assets = [{"id": item.get("id")} for item in root.findall(f".//{_q(ARF_NS, 'asset')}")]
    reports = []
    identifiers: set[str] = set()
    for item in root.findall(f".//{_q(ARF_NS, 'report')}"):
        identifier = item.get("id")
        if not identifier or identifier in identifiers:
            raise OvalInputError(f"ARF report identifiers must be unique: {_safe(path)}")
        identifiers.add(identifier)
        reports.append({"id": identifier, "content": _content_record(item, path)})
    requests = []
    for item in root.findall(f".//{_q(ARF_NS, 'report-request')}"):
        identifier = item.get("id")
        if not identifier or identifier in identifiers:
            raise OvalInputError(f"ARF report identifiers must be unique: {_safe(path)}")
        identifiers.add(identifier)
        requests.append({"id": identifier, "content": _content_record(item, path)})
    relationships = []
    for item in root.findall(f".//{_q(CORE_NS, 'relationship')}"):
        references = [(entry.text or "").strip() for entry in item.findall(_q(CORE_NS, "ref")) if (entry.text or "").strip()]
        relationships.append({"type": item.get("type"), "subject": item.get("subject"), "references": references})
    return {
        "format": "endeavor-arf-manifest", "version": "1.0.0",
        "source": {"path": path.name, "sha256": hashlib.sha256(data).hexdigest(), "arf-version": "1.1"},
        "assets": assets, "report-requests": requests, "reports": reports, "relationships": relationships,
    }
