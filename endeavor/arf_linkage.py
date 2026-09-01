"""Strict authored provenance links for otherwise-unlinked ARF evidence."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from lxml import etree as ET

from .arf import ARF_NS, DS_NS, OVAL_RESULTS_NS, XCCDF_NS, inspect_arf
from .mapping import MAX_MAPPING_BYTES, _json_object, _read_mapping, _require_exact_keys, _require_text
from .oval import OvalInputError

FORMAT = "endeavor-arf-linkage-manifest"
VERSION = "1.0.0"
CORE_NS = "http://scap.nist.gov/schema/reporting-core/1.1"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class Link:
    report_id: str
    report_sha256: str
    report_request_id: str
    data_stream_id: str
    component_ref_id: str
    component_id: str
    component_sha256: str
    test_result_id: str | None = None
    tailoring_id: str | None = None
    profile_id: str | None = None


@dataclass(frozen=True)
class LinkageDocument:
    path: Path
    sha256: str
    arf_sha256: str
    oval: tuple[Link, ...]
    tailoring: tuple[Link, ...]


def _hash(value: object, role: str) -> str:
    value = _require_text(value, role)
    if not SHA256.fullmatch(value):
        raise OvalInputError(f"linkage {role} must be a lowercase SHA-256")
    return value


def _link(value: object, tailoring: bool) -> Link:
    keys = {"report-id", "report-sha256", "report-request-id", "data-stream-id", "component-ref-id", "component-id", "component-sha256"}
    if tailoring:
        keys.update({"test-result-id", "tailoring-id", "profile-id"})
    entry = _require_exact_keys(value, keys, "link")
    return Link(
        report_id=_require_text(entry["report-id"], "report-id"),
        report_sha256=_hash(entry["report-sha256"], "report-sha256"),
        report_request_id=_require_text(entry["report-request-id"], "report-request-id"),
        data_stream_id=_require_text(entry["data-stream-id"], "data-stream-id"),
        component_ref_id=_require_text(entry["component-ref-id"], "component-ref-id"),
        component_id=_require_text(entry["component-id"], "component-id"),
        component_sha256=_hash(entry["component-sha256"], "component-sha256"),
        test_result_id=_require_text(entry["test-result-id"], "test-result-id") if tailoring else None,
        tailoring_id=_require_text(entry["tailoring-id"], "tailoring-id") if tailoring else None,
        profile_id=_require_text(entry["profile-id"], "profile-id") if tailoring else None,
    )


def _links(value: object, tailoring: bool) -> tuple[Link, ...]:
    if not isinstance(value, list):
        raise OvalInputError("linkage links must be arrays")
    links = tuple(_link(item, tailoring) for item in value)
    if len({item.report_id for item in links}) != len(links):
        raise OvalInputError("linkage contains duplicate report links")
    return links


def parse_linkage(path: Path) -> LinkageDocument:
    raw = _read_mapping(path)
    if len(raw) > MAX_MAPPING_BYTES:
        raise OvalInputError(f"linkage exceeds {MAX_MAPPING_BYTES} byte limit: {path.name}")
    try:
        value = json.loads(raw, object_pairs_hook=_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise OvalInputError(f"linkage is not valid JSON: {path.name}") from exc
    root = _require_exact_keys(value, {"format", "version", "source", "links"}, "document")
    source = _require_exact_keys(root["source"], {"arf-sha256"}, "source")
    links = _require_exact_keys(root["links"], {"oval-results-to-definitions", "test-result-to-tailoring"}, "links")
    if root["format"] != FORMAT or root["version"] != VERSION:
        raise OvalInputError(f"linkage has an unsupported format or version: {path.name}")
    oval = _links(links["oval-results-to-definitions"], False)
    tailoring = _links(links["test-result-to-tailoring"], True)
    if not oval and not tailoring:
        raise OvalInputError("linkage must contain at least one link")
    return LinkageDocument(path, hashlib.sha256(raw).hexdigest(), _hash(source["arf-sha256"], "arf-sha256"), oval, tailoring)


def _q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def _component(root: ET._Element, link: Link, path: Path) -> ET._Element:
    request = next((item for item in root.findall(f".//{_q(ARF_NS, 'report-request')}") if item.get("id") == link.report_request_id), None)
    if request is None:
        raise OvalInputError(f"linkage report request does not resolve: {path.name}")
    stream = next((item for item in request.findall(f".//{_q(DS_NS, 'data-stream')}") if item.get("id") == link.data_stream_id), None)
    if stream is None:
        raise OvalInputError(f"linkage data stream does not resolve: {path.name}")
    refs = [item for item in stream.findall(f".//{_q(DS_NS, 'component-ref')}") if item.get("id") == link.component_ref_id and item.get(XLINK_HREF) == f"#{link.component_id}"]
    components = [item for item in request.findall(f".//{_q(DS_NS, 'component')}") if item.get("id") == link.component_id]
    if len(refs) != 1 or len(components) != 1:
        raise OvalInputError(f"linkage component reference is ambiguous or missing: {path.name}")
    component = components[0]
    if hashlib.sha256(ET.tostring(component, method="c14n", with_comments=False)).hexdigest() != link.component_sha256:
        raise OvalInputError(f"linkage component hash does not match: {path.name}")
    if len(component) != 1:
        raise OvalInputError(f"linkage component payload is invalid: {path.name}")
    return component


def _report(root: ET._Element, link: Link, path: Path) -> tuple[ET._Element, ET._Element]:
    reports = [item for item in root.findall(f".//{_q(ARF_NS, 'report')}") if item.get("id") == link.report_id]
    if len(reports) != 1:
        raise OvalInputError(f"linkage report is ambiguous or missing: {path.name}")
    content = reports[0].find(_q(ARF_NS, "content"))
    if content is None or len(content) != 1:
        raise OvalInputError(f"linkage report content is invalid: {path.name}")
    payload = content[0]
    if hashlib.sha256(ET.tostring(payload, method="c14n", with_comments=False)).hexdigest() != link.report_sha256:
        raise OvalInputError(f"linkage report hash does not match: {path.name}")
    return reports[0], payload


def resolve_linkage(path: Path, linkage: LinkageDocument) -> dict[str, object]:
    manifest = inspect_arf(path)
    if manifest["source"]["sha256"] != linkage.arf_sha256:
        raise OvalInputError(f"linkage ARF hash does not match: {path.name}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != linkage.arf_sha256:
        raise OvalInputError(f"linkage ARF changed while resolving: {path.name}")
    root = ET.fromstring(data, parser=ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, recover=False))
    resolved_oval, resolved_tailoring = [], []
    for link in linkage.oval:
        report, result = _report(root, link, path)
        component = _component(root, link, path)
        definitions = component[0]
        if result.tag != _q(OVAL_RESULTS_NS, "oval_results") or definitions.tag != _q("http://oval.mitre.org/XMLSchema/oval-definitions-5", "oval_definitions"):
            raise OvalInputError(f"linkage OVAL payload kinds do not match: {path.name}")
        result_ids = [item.get("definition_id") for item in result.findall(f".//{_q(OVAL_RESULTS_NS, 'definition')}")]
        definition_ids = [item.get("id") for item in definitions.findall(f".//{_q('http://oval.mitre.org/XMLSchema/oval-definitions-5', 'definition')}")]
        if not result_ids or len(result_ids) != len(set(result_ids)) or len(definition_ids) != len(set(definition_ids)) or not set(result_ids).issubset(definition_ids):
            raise OvalInputError(f"linkage OVAL definitions do not cover report results: {path.name}")
        resolved_oval.append({"report-id": report.get("id"), "report-sha256": link.report_sha256, "report-request-id": link.report_request_id, "data-stream-id": link.data_stream_id, "component-ref-id": link.component_ref_id, "component-id": link.component_id, "component-sha256": link.component_sha256, "definition-count": len(result_ids), "conversion-supported": False, "conversion-limit": "embedded OVAL conversion requires a complete Results and Definitions pair in the supported parser profile"})
    for link in linkage.tailoring:
        report, result = _report(root, link, path)
        component = _component(root, link, path)
        tailoring = component[0]
        native = result.get("id") if result.tag == _q(XCCDF_NS, "TestResult") else None
        selected_profile = result.find(_q(XCCDF_NS, "profile")) if result.tag == _q(XCCDF_NS, "TestResult") else None
        profiles = [item.get("id") for item in tailoring.findall(_q(XCCDF_NS, "Profile")) if item.get("id")]
        report_manifest = next((item for item in manifest["reports"] if item["id"] == link.report_id), None)
        if native != link.test_result_id or tailoring.tag != _q(XCCDF_NS, "Tailoring") or tailoring.get("id") != link.tailoring_id or (selected_profile is not None and selected_profile.get("idref") != link.profile_id) or profiles.count(link.profile_id) != 1 or report_manifest is None or report_manifest.get("collection-id") != link.report_request_id:
            raise OvalInputError(f"linkage tailoring payload does not match TestResult: {path.name}")
        resolved_tailoring.append({"report-id": report.get("id"), "test-result-id": native, "tailoring-id": link.tailoring_id, "profile-id": link.profile_id, "source-profile-confirmed": selected_profile is not None, "report-sha256": link.report_sha256, "report-request-id": link.report_request_id, "data-stream-id": link.data_stream_id, "component-ref-id": link.component_ref_id, "component-id": link.component_id, "component-sha256": link.component_sha256, "interpretation-supported": False, "interpretation-limit": "tailoring decisions require a separately validated tailoring interpreter"})
    return {"format": "endeavor-arf-linkage-resolution", "version": VERSION, "source": manifest["source"], "linkage": {"path": linkage.path.name, "sha256": linkage.sha256}, "oval-results-to-definitions": resolved_oval, "test-result-to-tailoring": resolved_tailoring}
