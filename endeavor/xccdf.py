"""Bounded XCCDF 1.2 Results inventory parsing for the Phase 4 intake slice."""
from __future__ import annotations
import hashlib, re, stat
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

def _q(name): return f"{{{XCCDF_NS}}}{name}"
def _safe(path): return path.name or "xccdf-results"
class _Resolver(ET.Resolver):
    def resolve(self, url, public_id, context):
        parsed = urlparse(url)
        if parsed.scheme not in ("", "file") or parsed.query or parsed.fragment: raise OSError("untrusted XCCDF schema import")
        path = Path(unquote(parsed.path) if parsed.scheme == "file" else url)
        if not path.is_absolute(): path = ROOT / "xccdf" / "1.2" / path
        path = path.resolve()
        if path.suffix != ".xsd" or not path.is_file() or not any(root in path.parents or path == root for root in (ROOT / "xccdf" / "1.2", ROOT / "cpe" / "2.3", ROOT / "common")): raise OSError("untrusted XCCDF schema import")
        return self.resolve_filename(str(path), context)

@lru_cache(maxsize=1)
def _schema():
    parser = ET.XMLParser(no_network=True, resolve_entities=False, load_dtd=False, huge_tree=False)
    parser.resolvers.add(_Resolver())
    return ET.XMLSchema(ET.parse(str(ROOT / "xccdf" / "1.2" / "xccdf_1.2.xsd"), parser))

def inspect_xccdf(path: Path):
    try: meta = path.lstat()
    except FileNotFoundError as exc: raise OvalInputError(f"XCCDF input does not exist: {_safe(path)}") from exc
    if stat.S_ISLNK(meta.st_mode) or not stat.S_ISREG(meta.st_mode): raise OvalInputError(f"XCCDF input must be a regular non-symlink file: {_safe(path)}")
    if meta.st_size > MAX_XCCDF_BYTES: raise OvalInputError(f"XCCDF input exceeds {MAX_XCCDF_BYTES} byte limit: {_safe(path)}")
    data = path.read_bytes()
    if FORBIDDEN_XML.search(data): raise OvalInputError(f"DOCTYPE and ENTITY declarations are not supported: {_safe(path)}")
    try: root = ET.fromstring(data, parser=ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, recover=False))
    except ET.XMLSyntaxError as exc: raise OvalInputError(f"malformed XML in {_safe(path)}: {exc}") from exc
    if sum(1 for _ in root.iter()) > MAX_XCCDF_ELEMENTS: raise OvalInputError(f"XCCDF input exceeds {MAX_XCCDF_ELEMENTS} element limit: {_safe(path)}")
    if root.tag != _q("Benchmark") or not _schema().validate(ET.ElementTree(root)): raise OvalInputError(f"XCCDF 1.2 validation failed: {_safe(path)}")
    tests=[]; seen=set()
    for test in root.findall(_q("TestResult")):
        identifier=test.get("id", "")
        if not identifier or identifier in seen: raise OvalInputError(f"XCCDF TestResult identifiers must be unique: {_safe(path)}")
        seen.add(identifier); rules=[]; rule_seen=set()
        for item in test.findall(_q("rule-result")):
            rule=item.get("idref", ""); result=(item.findtext(_q("result")) or "").strip()
            if not rule or rule in rule_seen or result not in VALID_RULE_RESULTS: raise OvalInputError(f"XCCDF rule results are invalid: {_safe(path)}")
            rule_seen.add(rule); rules.append({"idref":rule,"result":result})
        tests.append({"id":identifier,"profile":test.get("profile"),"start-time":test.get("start-time"),"end-time":test.get("end-time"),"targets":[(x.text or "").strip() for x in test.findall(_q("target")) if (x.text or "").strip()],"rule-results":rules})
    return {"format":"endeavor-xccdf-inventory","version":"1.0.0","source":{"path":path.name,"sha256":hashlib.sha256(data).hexdigest(),"xccdf-version":"1.2.1"},"benchmark":{"id":root.get("id"),"version":root.findtext(_q("version"))},"test-results":tests}
