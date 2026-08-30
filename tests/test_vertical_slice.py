from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lxml import etree as ET

from endeavor.oval import MAX_XML_BYTES, OVAL_RESULTS_NS, _schema


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "fixtures" / "oval-results"
DEFINITIONS = ROOT / "fixtures" / "oval-definitions" / "definitions.xml"
SCHEMA_ROOT = ROOT / "endeavor" / "schemas" / "oval" / "5.11.3"
XSD_NS = "{http://www.w3.org/2001/XMLSchema}"


class VerticalSliceTests(unittest.TestCase):
    def test_results_wrapper_has_exact_pinned_import_graph(self) -> None:
        wrapper = SCHEMA_ROOT / "endeavor-results-wrapper.xsd"
        imports = ET.parse(str(wrapper)).getroot().findall(f"{XSD_NS}import")
        expected = {("http://oval.mitre.org/XMLSchema/oval-results-5", "oval-results-schema.xsd")}
        expected.update((ET.parse(str(path)).getroot().get("targetNamespace"), path.name) for path in SCHEMA_ROOT.glob("*-definitions-schema.xsd") if path.name != "oval-definitions-schema.xsd")
        expected.update((ET.parse(str(path)).getroot().get("targetNamespace"), path.name) for path in SCHEMA_ROOT.glob("*-system-characteristics-schema.xsd") if path.name != "oval-system-characteristics-schema.xsd")
        actual = {(item.get("namespace"), item.get("schemaLocation")) for item in imports}
        self.assertEqual(actual, expected)
        self.assertTrue(all(namespace and location and "/" not in location and location.endswith(".xsd") for namespace, location in actual))
        self.assertEqual(len(imports), len(expected))
        self.assertIsNotNone(_schema("5.11.3", OVAL_RESULTS_NS))

    def test_each_declared_status_is_preserved(self) -> None:
        cases = {
            "pass.xml": "true",
            "fail.xml": "false",
            "unknown.xml": "unknown",
            "error.xml": "error",
            "not-applicable.xml": "not applicable",
            "not-evaluated.xml": "not evaluated",
        }
        for name, expected in cases.items():
            with self.subTest(result=name):
                with tempfile.TemporaryDirectory() as directory:
                    output = Path(directory) / "result.json"
                    completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(RESULTS / name), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    document = json.loads(output.read_text())
                    observation = document["assessment-results"]["results"][0]["observations"][0]
                    self.assertIn({"name": "oval-result", "ns": "https://endeavor.dev/ns/oval", "value": expected}, observation["props"])
                    self.assertIn({"name": "target-host-name", "ns": "https://endeavor.dev/ns/oval", "value": "fixture"}, observation["props"])
                    self.assertEqual(observation["methods"], ["TEST"])
                    self.assertEqual(observation["types"], ["discovery"])

    def test_doctype_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malicious.xml"
            output = Path(directory) / "result.json"
            path.write_text('<!DOCTYPE x [<!ENTITY e "boom">]><oval_results/>', encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("DOCTYPE and ENTITY declarations", completed.stderr)
            self.assertFalse(output.exists())

    def test_json_input_diagnostic_is_single_line_and_redacts_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="endeavor-secret-path-") as directory:
            path = Path(directory) / "malicious.xml"
            output = Path(directory) / "result.json"
            path.write_text('<!DOCTYPE x [<!ENTITY e "boom">]><oval_results/>', encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--format", "json", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(len(completed.stderr.splitlines()), 1)
            diagnostic = json.loads(completed.stderr)
            self.assertEqual(diagnostic["error"]["code"], "input-invalid")
            self.assertEqual(diagnostic["error"]["exit-code"], 3)
            self.assertIn("malicious.xml", diagnostic["error"]["message"])
            self.assertNotIn(directory, completed.stderr)
            self.assertNotIn("<!DOCTYPE", completed.stderr)
            self.assertFalse(output.exists())

    def test_invalid_utf8_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-utf8.xml"
            output = Path(directory) / "result.json"
            path.write_bytes(b"<?xml version='1.0' encoding='UTF-8'?><oval_results>\xff</oval_results>")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("malformed XML", completed.stderr)
            self.assertFalse(output.exists())

    def test_xinclude_is_not_resolved_and_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="endeavor-xinclude-") as directory:
            path = Path(directory) / "xinclude.xml"
            output = Path(directory) / "result.json"
            source = (RESULTS / "pass.xml").read_text(encoding="utf-8")
            source = source.replace('xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5">', 'xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5" xmlns:xi="http://www.w3.org/2001/XInclude">')
            source = source.replace("<results>", f'<results><xi:include href="file://{directory}/not-opened.xml" parse="xml"/>')
            path.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("XSD validation failed", completed.stderr)
            self.assertNotIn(directory, completed.stderr)
            self.assertFalse(output.exists())

    def test_oversized_input_is_rejected_before_parsing_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.xml"
            output = Path(directory) / "result.json"
            path.write_bytes(b" " * (MAX_XML_BYTES + 1))
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn(f"exceeds {MAX_XML_BYTES} byte limit", completed.stderr)
            self.assertFalse(output.exists())

    def test_excessive_xml_depth_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "too-deep.xml"
            output = Path(directory) / "result.json"
            path.write_text("<x>" * 300 + "</x>" * 300, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("malformed XML", completed.stderr)
            self.assertFalse(output.exists())

    def test_usage_error_has_stable_exit_code(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "convert"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("endeavor: usage:", completed.stderr)

    def test_inspect_reports_only_safe_filenames(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect", "--results", str(RESULTS / "pass.xml"), "--definitions", str(DEFINITIONS)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["results"]["path"], "pass.xml")
        self.assertEqual(payload["definitions"]["path"], "definitions.xml")
        self.assertNotIn(str(ROOT), completed.stdout)

    def test_conversion_is_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            command = [sys.executable, "-m", "endeavor", "convert", "--results", str(RESULTS / "pass.xml"), "--definitions", str(DEFINITIONS)]
            for output in (first, second):
                completed = subprocess.run([*command, "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_xsd_invalid_results_are_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.xml"
            output = Path(directory) / "result.json"
            path.write_text((RESULTS / "pass.xml").read_text(encoding="utf-8").replace("<oval-sc:oval_system_characteristics>", "<oval-sc:removed>").replace("</oval-sc:oval_system_characteristics>", "</oval-sc:removed>"), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("XSD validation failed", completed.stderr)
            self.assertFalse(output.exists())

    def test_instance_schema_hints_cannot_replace_pinned_results_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hinted.xml"
            output = Path(directory) / "result.json"
            source = (RESULTS / "pass.xml").read_text(encoding="utf-8")
            source = source.replace('xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5">', 'xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://oval.mitre.org/XMLSchema/oval-results-5 https://invalid.example/attacker.xsd http://oval.mitre.org/XMLSchema/oval-definitions-5#linux file:///__endeavor_must_not_be_opened__.xsd">')
            path.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output.exists())

    def test_linux_system_characteristics_extension_is_schema_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "linux-extension.xml"
            output = Path(directory) / "result.json"
            source = (RESULTS / "pass.xml").read_text(encoding="utf-8")
            source = source.replace('xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5">', 'xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5" xmlns:linux-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5#linux">')
            source = source.replace("</oval-sc:oval_system_characteristics>", '<oval-sc:system_data><linux-sc:dpkginfo_item id="1" status="exists"><linux-sc:name>endeavor-fixture</linux-sc:name></linux-sc:dpkginfo_item></oval-sc:system_data></oval-sc:oval_system_characteristics>')
            path.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            observation = json.loads(output.read_text())["assessment-results"]["results"][0]["observations"][0]
            self.assertIn({"name": "oval-platform-system-characteristics-namespace", "ns": "https://endeavor.dev/ns/oval", "value": "http://oval.mitre.org/XMLSchema/oval-system-characteristics-5#linux"}, observation["props"])

    def test_duplicate_result_definition_identifier_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.xml"
            output = Path(directory) / "result.json"
            source = (RESULTS / "pass.xml").read_text(encoding="utf-8")
            definition = '<definition definition_id="oval:org.endeavor:def:1" version="1" class="inventory" result="true"/>'
            path.write_text(source.replace(definition, definition + definition), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("XSD validation failed", completed.stderr)
            self.assertFalse(output.exists())

    def test_symlink_input_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results-link.xml"
            output = Path(directory) / "result.json"
            path.symlink_to(RESULTS / "pass.xml")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("regular non-symlink", completed.stderr)
            self.assertFalse(output.exists())

    def test_unsupported_declared_schema_version_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "old-version.xml"
            output = Path(directory) / "result.json"
            source = (RESULTS / "pass.xml").read_text(encoding="utf-8")
            path.write_text(source.replace(">5.11.3</oval:schema_version>", ">5.11</oval:schema_version>"), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("unsupported OVAL core schema version", completed.stderr)
            self.assertFalse(output.exists())

    def test_unknown_extension_cannot_be_authorized_by_instance_schema_hint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unknown-extension.xml"
            output = Path(directory) / "result.json"
            source = (RESULTS / "pass.xml").read_text(encoding="utf-8")
            source = source.replace('xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5">', 'xmlns:oval-sc="http://oval.mitre.org/XMLSchema/oval-system-characteristics-5" xmlns:evil="https://attacker.invalid/oval" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://attacker.invalid/oval file:///__endeavor_must_not_be_opened__.xsd">')
            source = source.replace("<results>", "<results><evil:unknown/>")
            path.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("XSD validation failed", completed.stderr)
            self.assertFalse(output.exists())

    def test_generated_oscal_validates_with_ajv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            convert = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(RESULTS / "pass.xml"), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(convert.returncode, 0, convert.stderr)
            validate = subprocess.run(["npm", "run", "validate:oscal", "--", "endeavor/schemas/oscal-1.2.0/assessment-results.schema.json", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_timezone_less_openscap_timestamp_is_normalized_for_oscal(self) -> None:
        generated = ROOT / "fixtures" / "generated-sanitized"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            convert = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(generated / "oval-results.xml"), "--definitions", str(generated / "oval-definitions.xml"), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(convert.returncode, 0, convert.stderr)
            document = json.loads(output.read_text())
            self.assertEqual(document["assessment-results"]["metadata"]["last-modified"], "2026-08-30T03:23:11Z")
            validate = subprocess.run(["npm", "run", "validate:oscal", "--", "endeavor/schemas/oscal-1.2.0/assessment-results.schema.json", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(validate.returncode, 0, validate.stderr)
