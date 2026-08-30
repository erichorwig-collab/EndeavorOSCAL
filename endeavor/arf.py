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
DS_NS = "http://scap.nist.gov/schema/scap/source/1.2"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
XCCDF_NS = "http://checklists.nist.gov/xccdf/1.2"
OVAL_RESULTS_NS = "http://oval.mitre.org/XMLSchema/oval-results-5"
VALID_OVAL_RESULTS = frozenset({"true", "false", "unknown", "error", "not evaluated", "not applicable"})
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


def _unique_by_id(items: list[ET._Element], label: str, path: Path) -> dict[str, ET._Element]:
    records: dict[str, ET._Element] = {}
    for item in items:
        identifier = item.get("id")
        if not identifier or identifier in records:
            raise OvalInputError(f"ARF {label} identifiers must be unique: {_safe(path)}")
        records[identifier] = item
    return records


def _collection_manifest(request: ET._Element, path: Path) -> dict[str, object]:
    content = request.find(_q(ARF_NS, "content"))
    if content is None or len(content) != 1 or content[0].tag != _q(DS_NS, "data-stream-collection"):
        raise OvalInputError(f"ARF report request must contain one data-stream collection: {_safe(path)}")
    collection = content[0]
    components = _unique_by_id(collection.findall(_q(DS_NS, "component")), "component", path)
    streams = []
    for stream in collection.findall(_q(DS_NS, "data-stream")):
        component_refs = []
        for reference in stream.findall(f".//{_q(DS_NS, 'component-ref')}"):
            href = reference.get(XLINK_HREF, "")
            if not href.startswith("#") or href[1:] not in components:
                raise OvalInputError(f"ARF component references must be local and resolvable: {_safe(path)}")
            component = components[href[1:]]
            payload = component[0] if len(component) == 1 else None
            if payload is None:
                raise OvalInputError(f"ARF components must contain exactly one payload: {_safe(path)}")
            payload_record: dict[str, object] = {"namespace": ET.QName(payload).namespace, "name": ET.QName(payload).localname, "id": payload.get("id")}
            if payload.tag == _q(XCCDF_NS, "Benchmark"):
                payload_record["profile-ids"] = [profile.get("id") for profile in payload.findall(_q(XCCDF_NS, "Profile")) if profile.get("id")]
            if payload.tag == _q(XCCDF_NS, "Tailoring"):
                benchmark = payload.find(_q(XCCDF_NS, "benchmark"))
                version = payload.find(_q(XCCDF_NS, "version"))
                payload_record["benchmark-href"] = benchmark.get("href") if benchmark is not None else None
                payload_record["version"] = (version.text or "").strip() if version is not None else None
                payload_record["version-time"] = version.get("time") if version is not None else None
                payload_record["profile-ids"] = [profile.get("id") for profile in payload.findall(_q(XCCDF_NS, "Profile")) if profile.get("id")]
            component_refs.append({
                "id": reference.get("id"), "component-id": href[1:],
                "section": ET.QName(reference.getparent()).localname,
                "payload": payload_record,
                "sha256": hashlib.sha256(ET.tostring(component, method="c14n", with_comments=False)).hexdigest(),
            })
        streams.append({"id": stream.get("id"), "scap-version": stream.get("scap-version"), "use-case": stream.get("use-case"), "components": component_refs})
    if not streams:
        raise OvalInputError(f"ARF collection must contain a data stream: {_safe(path)}")
    return {"id": collection.get("id"), "schematron-version": collection.get("schematron-version"), "data-streams": streams}


def _single_relationship(relationships: list[dict[str, object]], relationship_type: str, subject: str, path: Path) -> str:
    matches = [item["references"] for item in relationships if item["type"] == relationship_type and item["subject"] == subject]
    if len(matches) != 1 or len(matches[0]) != 1:
        raise OvalInputError(f"ARF report linkage is ambiguous or missing: {_safe(path)}")
    return matches[0][0]


def _section_items(root: ET._Element, section: str, item: str) -> list[ET._Element]:
    container = root.find(_q(ARF_NS, section))
    return container.findall(_q(ARF_NS, item)) if container is not None else []


def _linked_xccdf_result(report: ET._Element, collection: dict[str, object], path: Path) -> dict[str, object]:
    content = report.find(_q(ARF_NS, "content"))
    result = content[0] if content is not None and len(content) == 1 else None
    if result is None or result.tag != _q(XCCDF_NS, "TestResult"):
        raise OvalInputError(f"ARF XCCDF report content is invalid: {_safe(path)}")
    benchmark = result.find(_q(XCCDF_NS, "benchmark"))
    profile = result.find(_q(XCCDF_NS, "profile"))
    benchmark_id = benchmark.get("id") if benchmark is not None else None
    streams = collection["data-streams"]
    matches = [component for stream in streams for component in stream["components"] if component["payload"]["namespace"] == XCCDF_NS and component["payload"]["name"] == "Benchmark" and component["payload"]["id"] == benchmark_id]
    if len(matches) != 1:
        raise OvalInputError(f"ARF XCCDF benchmark linkage is ambiguous or missing: {_safe(path)}")
    profile_id = profile.get("idref") if profile is not None else None
    if profile_id and matches[0]["payload"].get("profile-ids", []).count(profile_id) != 1:
        raise OvalInputError(f"ARF XCCDF profile linkage is ambiguous or missing: {_safe(path)}")
    rules = []
    for rule in result.findall(_q(XCCDF_NS, "rule-result")):
        outcome = rule.find(_q(XCCDF_NS, "result"))
        rules.append({"idref": rule.get("idref"), "result": (outcome.text or "").strip() if outcome is not None else None, "time": rule.get("time"), "severity": rule.get("severity"), "weight": rule.get("weight")})
    identity = result.find(_q(XCCDF_NS, "identity"))
    title = result.find(_q(XCCDF_NS, "title"))
    target_facts = [{"name": item.get("name"), "value": (item.text or "").strip() or None} for item in result.findall(f"{_q(XCCDF_NS, 'target-facts')}/{_q(XCCDF_NS, 'fact')}")]
    target_references = [{"system": item.get("system"), "href": item.get("href"), "name": item.get("name")} for item in result.findall(_q(XCCDF_NS, "target-id-ref"))]
    return {
        "id": result.get("id"), "benchmark": {"id": benchmark_id, "href": benchmark.get("href") if benchmark is not None else None, "component-id": matches[0]["component-id"]},
        "profile": profile_id,
        "title": (title.text or "").strip() or None if title is not None else None,
        "test-system": result.get("test-system"),
        "identity": {"name": (identity.text or "").strip() or None, "authenticated": identity.get("authenticated"), "privileged": identity.get("privileged")} if identity is not None else None,
        "start-time": result.get("start-time"), "end-time": result.get("end-time"),
        "targets": [(item.text or "").strip() for item in result.findall(_q(XCCDF_NS, "target")) if (item.text or "").strip()],
        "target-addresses": [(item.text or "").strip() for item in result.findall(_q(XCCDF_NS, "target-address")) if (item.text or "").strip()],
        "target-facts": target_facts,
        "target-references": target_references,
        "platforms": [item.get("idref") for item in result.findall(_q(XCCDF_NS, "platform")) if item.get("idref")],
        "scores": [{"system": item.get("system"), "maximum": item.get("maximum"), "value": (item.text or "").strip() or None} for item in result.findall(_q(XCCDF_NS, "score"))],
        "rule-results": rules,
    }


def _oval_result(report: ET._Element, path: Path) -> dict[str, object]:
    content = report.find(_q(ARF_NS, "content"))
    result = content[0] if content is not None and len(content) == 1 else None
    if result is None or result.tag != _q(OVAL_RESULTS_NS, "oval_results"):
        raise OvalInputError(f"ARF OVAL report content is invalid: {_safe(path)}")
    definitions = []
    identifiers: set[str] = set()
    for item in result.findall(f".//{_q(OVAL_RESULTS_NS, 'definition')}"):
        identifier, outcome = item.get("definition_id"), item.get("result")
        if not identifier or identifier in identifiers or outcome not in VALID_OVAL_RESULTS:
            raise OvalInputError(f"ARF OVAL definition results are invalid: {_safe(path)}")
        identifiers.add(identifier)
        definitions.append({"id": identifier, "result": outcome})
    if not definitions:
        raise OvalInputError(f"ARF OVAL report has no definition results: {_safe(path)}")
    return {"definition-results": definitions}


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
    assets = [{"id": item.get("id")} for item in _section_items(root, "assets", "asset")]
    if len({item["id"] for item in assets if item["id"]}) != len(assets) or any(not item["id"] for item in assets):
        raise OvalInputError(f"ARF asset identifiers must be unique: {_safe(path)}")
    asset_ids = {item["id"] for item in assets if item["id"]}
    reports = []
    identifiers: set[str] = set()
    for item in _section_items(root, "reports", "report"):
        identifier = item.get("id")
        if not identifier or identifier in identifiers:
            raise OvalInputError(f"ARF report identifiers must be unique: {_safe(path)}")
        identifiers.add(identifier)
        reports.append({"id": identifier, "content": _content_record(item, path), "_element": item})
    requests = []
    for item in _section_items(root, "report-requests", "report-request"):
        identifier = item.get("id")
        if not identifier or identifier in identifiers:
            raise OvalInputError(f"ARF report identifiers must be unique: {_safe(path)}")
        identifiers.add(identifier)
        requests.append({"id": identifier, "content": _content_record(item, path), "collection": _collection_manifest(item, path)})
    relationships = []
    relationship_container = root.find(_q(CORE_NS, "relationships"))
    for item in relationship_container.findall(_q(CORE_NS, "relationship")) if relationship_container is not None else []:
        references = [(entry.text or "").strip() for entry in item.findall(_q(CORE_NS, "ref")) if (entry.text or "").strip()]
        relationships.append({"type": item.get("type"), "subject": item.get("subject"), "references": references})
    request_ids = {item["id"] for item in requests}
    collections = {item["id"]: item["collection"] for item in requests}
    for report in reports:
        content = report["content"]
        if content["namespace"] == XCCDF_NS and content["name"] == "TestResult":
            collection_id = _single_relationship(relationships, "arfvocab:createdFor", report["id"], path)
            asset_relationship = next((kind for kind in ("arfrel:isAbout", "arfvocab:isAbout") if any(item["type"] == kind and item["subject"] == report["id"] for item in relationships)), None)
            if asset_relationship is None:
                raise OvalInputError(f"ARF report linkage is ambiguous or missing: {_safe(path)}")
            asset_id = _single_relationship(relationships, asset_relationship, report["id"], path)
            if collection_id not in request_ids or asset_id not in asset_ids:
                raise OvalInputError(f"ARF report linkage does not resolve locally: {_safe(path)}")
            report["collection-id"] = collection_id
            report["asset-id"] = asset_id
            report["xccdf-result"] = _linked_xccdf_result(report["_element"], collections[collection_id], path)
        elif content["namespace"] == OVAL_RESULTS_NS and content["name"] == "oval_results":
            report["oval-result"] = _oval_result(report["_element"], path)
        del report["_element"]
    return {
        "format": "endeavor-arf-manifest", "version": "1.0.0",
        "source": {"path": path.name, "sha256": hashlib.sha256(data).hexdigest(), "arf-version": "1.1"},
        "assets": assets, "report-requests": requests, "reports": reports, "relationships": relationships,
    }
