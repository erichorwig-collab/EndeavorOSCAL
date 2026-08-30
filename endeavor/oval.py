"""Bounded OVAL XML parsing for the v0.1 evidence-adapter slice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import re
import stat
from urllib.parse import unquote, urlparse
from functools import lru_cache

from lxml import etree as ET


MAX_XML_BYTES = 5 * 1024 * 1024
OVAL_RESULTS_NS = "http://oval.mitre.org/XMLSchema/oval-results-5"
OVAL_DEFINITIONS_NS = "http://oval.mitre.org/XMLSchema/oval-definitions-5"
OVAL_COMMON_NS = "http://oval.mitre.org/XMLSchema/oval-common-5"
OVAL_SYSTEM_CHARACTERISTICS_NS = "http://oval.mitre.org/XMLSchema/oval-system-characteristics-5"
VALID_RESULTS = frozenset({"true", "false", "unknown", "error", "not evaluated", "not applicable"})
SUPPORTED_CORE_SCHEMA_VERSIONS = frozenset({"5.11.3"})
FORBIDDEN_XML = re.compile(br"<!DOCTYPE|<!ENTITY", re.IGNORECASE)
SCHEMA_ROOTS = {
    "5.11.3": (Path(__file__).parent / "schemas" / "oval" / "5.11.3").resolve(),
}


class OvalInputError(ValueError):
    """An input cannot be processed as supported OVAL evidence."""


class _TrustedSchemaResolver(ET.Resolver):
    """Permit only vendored XSD imports while compiling trusted wrappers."""

    def __init__(self, schema_root: Path) -> None:
        super().__init__()
        self.schema_root = schema_root
        self.allowed_roots = (schema_root, schema_root.parents[1] / "common")

    def resolve(self, url: str, public_id: str | None, context: object) -> object:
        parsed = urlparse(url)
        if parsed.scheme not in ("", "file") or parsed.params or parsed.query or parsed.fragment:
            raise OSError(f"untrusted schema import URL: {url}")
        raw_path = unquote(parsed.path) if parsed.scheme == "file" else url
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = self.schema_root / candidate
        candidate = candidate.resolve()
        if not any(candidate == root or root in candidate.parents for root in self.allowed_roots) or candidate.suffix != ".xsd" or not candidate.is_file():
            raise OSError(f"untrusted schema import path: {url}")
        return self.resolve_filename(str(candidate), context)


@dataclass(frozen=True)
class Generator:
    product_name: str
    product_version: str
    schema_version: str
    timestamp: str


@dataclass(frozen=True)
class OvalDefinition:
    identifier: str
    result: str
    title: str
    description: str
    definition_class: str
    message: str | None


@dataclass(frozen=True)
class SystemIdentity:
    os_name: str
    os_version: str
    architecture: str
    primary_host_name: str
    platform_extension_namespaces: tuple[str, ...]


@dataclass(frozen=True)
class OvalDocument:
    path: Path
    sha256: str
    generator: Generator
    definitions: tuple[OvalDefinition, ...]
    system_identity: SystemIdentity | None = None


def _q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def _text(element: ET._Element | None, default: str = "") -> str:
    return (element.text or default).strip() if element is not None else default


def _read_xml(path: Path) -> bytes:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise OvalInputError(f"input does not exist: {path}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise OvalInputError(f"input must be a regular non-symlink file: {path}")
    size = metadata.st_size
    if size > MAX_XML_BYTES:
        raise OvalInputError(f"input exceeds {MAX_XML_BYTES} byte limit: {path}")
    data = path.read_bytes()
    if FORBIDDEN_XML.search(data):
        raise OvalInputError(f"DOCTYPE and ENTITY declarations are not supported: {path}")
    return data


@lru_cache(maxsize=2)
def _schema(version: str, namespace: str) -> ET.XMLSchema:
    name = {OVAL_RESULTS_NS: "endeavor-results-wrapper.xsd", OVAL_DEFINITIONS_NS: "endeavor-definitions-wrapper.xsd"}.get(namespace)
    if name is None:
        raise OvalInputError(f"no trusted schema for namespace {namespace}")
    schema_root = SCHEMA_ROOTS.get(version)
    if schema_root is None:
        raise OvalInputError(f"no trusted schema bundle for OVAL {version}")
    path = schema_root / name
    parser = ET.XMLParser(no_network=True, resolve_entities=False, load_dtd=False, huge_tree=False)
    parser.resolvers.add(_TrustedSchemaResolver(schema_root))
    return ET.XMLSchema(ET.parse(str(path), parser=parser))


def _parse_root(path: Path, expected_namespace: str, expected_name: str) -> tuple[ET._Element, bytes]:
    data = _read_xml(path)
    try:
        root = ET.fromstring(data, parser=ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, recover=False))
    except ET.XMLSyntaxError as exc:
        raise OvalInputError(f"malformed XML in {path}: {exc}") from exc
    if root.tag != _q(expected_namespace, expected_name):
        raise OvalInputError(f"unsupported root element in {path}: {root.tag}")
    version = _declared_core_schema_version(root, path)
    tree = ET.ElementTree(root)
    schema = _schema(version, expected_namespace)
    if not schema.validate(tree):
        error = schema.error_log.last_error
        raise OvalInputError(f"OVAL {version} XSD validation failed in {path.name}: {error.message if error else 'unknown schema error'}")
    return root, data


def _generator_element(root: ET._Element, path: Path) -> ET._Element:
    generator = root.find(_q(OVAL_RESULTS_NS, "generator"))
    if generator is None:
        generator = root.find(_q(OVAL_DEFINITIONS_NS, "generator"))
    if generator is None:
        raise OvalInputError(f"missing generator in {path}")
    return generator


def _declared_core_schema_version(root: ET._Element, path: Path) -> str:
    generator = _generator_element(root, path)
    core_versions = [
        _text(item)
        for item in generator.findall(_q(OVAL_COMMON_NS, "schema_version"))
        if item.get("platform") is None
    ]
    if len(core_versions) != 1:
        raise OvalInputError(f"generator must declare exactly one core schema_version in {path}")
    version = core_versions[0]
    if version not in SUPPORTED_CORE_SCHEMA_VERSIONS:
        raise OvalInputError(f"unsupported OVAL core schema version {version!r} in {path}")
    return version


def _generator(root: ET._Element, path: Path) -> Generator:
    generator = _generator_element(root, path)
    values = {
        "product_name": _text(generator.find(_q(OVAL_COMMON_NS, "product_name"))),
        "product_version": _text(generator.find(_q(OVAL_COMMON_NS, "product_version"))),
        "schema_version": _declared_core_schema_version(root, path),
        "timestamp": _text(generator.find(_q(OVAL_COMMON_NS, "timestamp"))),
    }
    if not all(values.values()):
        raise OvalInputError(f"generator is incomplete in {path}")
    try:
        datetime.fromisoformat(values["timestamp"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise OvalInputError(f"generator timestamp is invalid in {path}") from exc
    return Generator(**values)


def _system_identity(root: ET._Element) -> SystemIdentity:
    system_info = root.find(f".//{_q(OVAL_SYSTEM_CHARACTERISTICS_NS, 'system_info')}")
    if system_info is None:
        raise OvalInputError("Results document is missing required system_info")
    values = {
        "os_name": _text(system_info.find(_q(OVAL_SYSTEM_CHARACTERISTICS_NS, "os_name"))),
        "os_version": _text(system_info.find(_q(OVAL_SYSTEM_CHARACTERISTICS_NS, "os_version"))),
        "architecture": _text(system_info.find(_q(OVAL_SYSTEM_CHARACTERISTICS_NS, "architecture"))),
        "primary_host_name": _text(system_info.find(_q(OVAL_SYSTEM_CHARACTERISTICS_NS, "primary_host_name"))),
    }
    if not all(values.values()):
        raise OvalInputError("Results document has incomplete system_info")
    extensions = {
        ET.QName(item).namespace
        for item in root.findall(f".//{_q(OVAL_SYSTEM_CHARACTERISTICS_NS, 'system_data')}/*")
        if ET.QName(item).namespace and ET.QName(item).namespace != OVAL_SYSTEM_CHARACTERISTICS_NS
    }
    return SystemIdentity(**values, platform_extension_namespaces=tuple(sorted(extensions)))


def _require_unique_identifiers(definitions: list[OvalDefinition], path: Path) -> None:
    seen: set[str] = set()
    duplicate = next((item.identifier for item in definitions if item.identifier in seen or seen.add(item.identifier)), None)
    if duplicate is not None:
        raise OvalInputError(f"duplicate definition identifier {duplicate!r} in {path}")


def parse_results(path: Path) -> OvalDocument:
    root, data = _parse_root(path, OVAL_RESULTS_NS, "oval_results")
    definitions: list[OvalDefinition] = []
    for item in root.findall(f".//{_q(OVAL_RESULTS_NS, 'definition')}"):
        result = item.get("result", "")
        if result not in VALID_RESULTS:
            raise OvalInputError(f"unsupported definition result {result!r} in {path}")
        identifier = item.get("definition_id", "")
        if not identifier:
            raise OvalInputError(f"definition without definition_id in {path}")
        message = _text(item.find(_q(OVAL_RESULTS_NS, "message"))) or None
        definitions.append(OvalDefinition(identifier, result, identifier, "OVAL evaluation result.", item.get("class", "unknown"), message))
    if not definitions:
        raise OvalInputError(f"no evaluated definitions in {path}")
    _require_unique_identifiers(definitions, path)
    return OvalDocument(path, hashlib.sha256(data).hexdigest(), _generator(root, path), tuple(definitions), _system_identity(root))


def parse_definitions(path: Path) -> OvalDocument:
    root, data = _parse_root(path, OVAL_DEFINITIONS_NS, "oval_definitions")
    definitions: list[OvalDefinition] = []
    for item in root.findall(f".//{_q(OVAL_DEFINITIONS_NS, 'definition')}"):
        identifier = item.get("id", "")
        if not identifier:
            raise OvalInputError(f"definition without id in {path}")
        metadata = item.find(_q(OVAL_DEFINITIONS_NS, "metadata"))
        definitions.append(OvalDefinition(identifier, "", _text(metadata.find(_q(OVAL_DEFINITIONS_NS, "title")) if metadata is not None else None, identifier), _text(metadata.find(_q(OVAL_DEFINITIONS_NS, "description")) if metadata is not None else None, "No source description."), item.get("class", "unknown"), None))
    if not definitions:
        raise OvalInputError(f"no definitions in {path}")
    _require_unique_identifiers(definitions, path)
    return OvalDocument(path, hashlib.sha256(data).hexdigest(), _generator(root, path), tuple(definitions))


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
