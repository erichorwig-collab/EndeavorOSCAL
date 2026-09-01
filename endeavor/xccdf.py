"""Bounded XCCDF 1.2 Results inventory parsing for the Phase 4 intake slice."""
from __future__ import annotations

import hashlib
import re
import stat
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlparse

from lxml import etree as ET

from .oval import OvalInputError

MAX_XCCDF_BYTES = 5 * 1024 * 1024
MAX_XCCDF_ELEMENTS = 50_000
XCCDF_NS = "http://checklists.nist.gov/xccdf/1.2"
VALID_RULE_RESULTS = frozenset({"pass", "fail", "error", "unknown", "notapplicable", "notchecked", "notselected", "informational", "fixed"})
FORBIDDEN_XML = re.compile(br"<!DOCTYPE|<!ENTITY", re.I)
ROOT = Path(__file__).parent / "schemas"
SCHEMA_ROOTS = (ROOT / "xccdf" / "1.2", ROOT / "cpe" / "2.3", ROOT / "common")


def _q(name: str) -> str:
    return f"{{{XCCDF_NS}}}{name}"


def _safe(path: Path) -> str:
    return path.name or "xccdf-results"


def _text(item: ET._Element | None) -> str | None:
    if item is None:
        return None
    value = (item.text or "").strip()
    return value or None


class _Resolver(ET.Resolver):
    def resolve(self, url: str, public_id: str | None, context: object) -> object:
        parsed = urlparse(url)
        if parsed.scheme not in ("", "file") or parsed.query or parsed.fragment:
            raise OSError("untrusted XCCDF schema import")
        candidate = Path(unquote(parsed.path) if parsed.scheme == "file" else url)
        if not candidate.is_absolute():
            candidate = ROOT / "xccdf" / "1.2" / candidate
        candidate = candidate.resolve()
        allowed = any(root == candidate or root in candidate.parents for root in SCHEMA_ROOTS)
        if candidate.suffix != ".xsd" or not candidate.is_file() or not allowed:
            raise OSError("untrusted XCCDF schema import")
        return self.resolve_filename(str(candidate), context)


@lru_cache(maxsize=1)
def _schema() -> ET.XMLSchema:
    parser = ET.XMLParser(no_network=True, resolve_entities=False, load_dtd=False, huge_tree=False)
    parser.resolvers.add(_Resolver())
    return ET.XMLSchema(ET.parse(str(ROOT / "xccdf" / "1.2" / "xccdf_1.2.xsd"), parser))


def _reference(item: ET._Element | None, fields: tuple[str, ...]) -> dict[str, str | None] | None:
    if item is None:
        return None
    return {field: item.get(field) for field in fields}


def _identity(item: ET._Element | None) -> dict[str, str | None] | None:
    if item is None:
        return None
    return {"name": _text(item), "authenticated": item.get("authenticated"), "privileged": item.get("privileged")}


def _rule_results(test: ET._Element, path: Path) -> list[dict[str, str | None]]:
    rules: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for item in test.findall(_q("rule-result")):
        identifier = item.get("idref", "")
        result = _text(item.find(_q("result")))
        if not identifier or identifier in seen or result not in VALID_RULE_RESULTS:
            raise OvalInputError(f"XCCDF rule results are invalid: {_safe(path)}")
        seen.add(identifier)
        rules.append({"idref": identifier, "result": result, "time": item.get("time"), "weight": item.get("weight")})
    return rules


def _test_result(test: ET._Element, root: ET._Element, path: Path) -> dict[str, object]:
    identifier = test.get("id", "")
    if not identifier:
        raise OvalInputError(f"XCCDF TestResult identifiers must be unique: {_safe(path)}")
    profile = test.find(_q("profile"))
    target_facts = [{"name": fact.get("name"), "value": _text(fact)} for fact in test.findall(f"{_q('target-facts')}/{_q('fact')}")]
    return {
        "id": identifier,
        "benchmark": _reference(test.find(_q("benchmark")), ("id", "href")) or {"id": root.get("id"), "href": None},
        "tailoring": _reference(test.find(_q("tailoring-file")), ("id", "href", "version", "time")),
        "title": [_text(item) for item in test.findall(_q("title")) if _text(item)],
        "organizations": [_text(item) for item in test.findall(_q("organization")) if _text(item)],
        "identity": _identity(test.find(_q("identity"))),
        "profile": profile.get("idref") if profile is not None else None,
        "test-system": test.get("test-system"),
        "start-time": test.get("start-time"),
        "end-time": test.get("end-time"),
        "targets": [_text(item) for item in test.findall(_q("target")) if _text(item)],
        "target-addresses": [_text(item) for item in test.findall(_q("target-address")) if _text(item)],
        "target-facts": target_facts,
        "platforms": [item.get("idref") for item in test.findall(_q("platform")) if item.get("idref")],
        "rule-results": _rule_results(test, path),
        "scores": [{"system": score.get("system"), "maximum": score.get("maximum"), "value": _text(score)} for score in test.findall(_q("score"))],
    }


def inspect_xccdf(path: Path) -> dict[str, object]:
    try:
        meta = path.lstat()
    except FileNotFoundError as exc:
        raise OvalInputError(f"XCCDF input does not exist: {_safe(path)}") from exc
    if stat.S_ISLNK(meta.st_mode) or not stat.S_ISREG(meta.st_mode):
        raise OvalInputError(f"XCCDF input must be a regular non-symlink file: {_safe(path)}")
    if meta.st_size > MAX_XCCDF_BYTES:
        raise OvalInputError(f"XCCDF input exceeds {MAX_XCCDF_BYTES} byte limit: {_safe(path)}")
    data = path.read_bytes()
    if FORBIDDEN_XML.search(data):
        raise OvalInputError(f"DOCTYPE and ENTITY declarations are not supported: {_safe(path)}")
    try:
        root = ET.fromstring(data, parser=ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, recover=False))
    except ET.XMLSyntaxError as exc:
        raise OvalInputError(f"malformed XML in {_safe(path)}: {exc}") from exc
    if sum(1 for _ in root.iter()) > MAX_XCCDF_ELEMENTS:
        raise OvalInputError(f"XCCDF input exceeds {MAX_XCCDF_ELEMENTS} element limit: {_safe(path)}")
    if root.tag != _q("Benchmark") or not _schema().validate(ET.ElementTree(root)):
        raise OvalInputError(f"XCCDF 1.2 validation failed: {_safe(path)}")
    tests = [_test_result(test, root, path) for test in root.findall(_q("TestResult"))]
    if not tests:
        raise OvalInputError(f"XCCDF Results must contain at least one TestResult: {_safe(path)}")
    if len({test["id"] for test in tests}) != len(tests):
        raise OvalInputError(f"XCCDF TestResult identifiers must be unique: {_safe(path)}")
    return {
        "format": "endeavor-xccdf-inventory",
        "version": "1.0.0",
        "source": {"path": path.name, "sha256": hashlib.sha256(data).hexdigest(), "xccdf-version": "1.2.1"},
        "benchmark": {"id": root.get("id"), "version": _text(root.find(_q("version"))), "resolved": root.get("resolved")},
        "test-results": tests,
    }
