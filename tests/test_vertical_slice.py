from __future__ import annotations

import json
import hashlib
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from lxml import etree as ET

from endeavor.oval import MAX_XML_BYTES, MAX_XML_ELEMENTS, OVAL_RESULTS_NS, OvalInputError, _schema, parse_definitions, parse_results
from endeavor.arf import inspect_arf
from endeavor.evidence import normalize_arf, normalize_oval, normalize_xccdf
from endeavor.xccdf import inspect_xccdf
from endeavor.mapping import parse_mapping as parse_oval_mapping
from endeavor.xccdf_mapping import parse_mapping as parse_xccdf_mapping
from endeavor.xccdf_convert import assessment_results as xccdf_assessment_results, assessment_results_from_arf
from endeavor.convert import assessment_results as oval_assessment_results


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "fixtures" / "oval-results"
DEFINITIONS = ROOT / "fixtures" / "oval-definitions" / "definitions.xml"
GOLDEN = ROOT / "fixtures" / "oscal-golden"
MAPPING = ROOT / "fixtures" / "mappings" / "example-v1.json"
SCHEMA_ROOT = ROOT / "endeavor" / "schemas" / "oval" / "5.11.3"
XCCDF_SCHEMA = ROOT / "endeavor" / "schemas" / "xccdf" / "1.2" / "xccdf_1.2.xsd"
XCCDF_FIXTURE = ROOT / "fixtures" / "xccdf-results" / "openscap-1.4.4-results-xccdf12.xml"
XCCDF_GOLDEN = ROOT / "fixtures" / "xccdf-results" / "openscap-1.4.4-results-xccdf12.inventory.json"
XCCDF_PROVENANCE_FIXTURE = ROOT / "fixtures" / "xccdf-results" / "provenance-companion-xccdf12.xml"
XCCDF_TAILORING = ROOT / "fixtures" / "xccdf-tailoring" / "openscap-1.4.4-baseline.tailoring.xml"
XCCDF_BASELINE = ROOT / "fixtures" / "xccdf-tailoring" / "openscap-1.4.4-baseline.xccdf.xml"
ARF_FIXTURE = ROOT / "fixtures" / "arf" / "openscap-1.4.4-xccdf-overrides.arf.xml"
ARF_GOLDEN = ROOT / "fixtures" / "arf" / "openscap-1.4.4-xccdf-overrides.manifest.json"
ARF_MAPPING = ROOT / "fixtures" / "mappings" / "arf-xccdf-example-v1.json"
ARF_TAILORING = ROOT / "fixtures" / "arf" / "openscap-1.4.4-tailoring-sanitized.arf.xml"
ARF_LINKAGE = ROOT / "fixtures" / "linkage" / "openscap-1.4.4-tailoring-v1.json"
ARF_LINKAGE_GOLDEN = ROOT / "fixtures" / "linkage" / "openscap-1.4.4-tailoring-v1.resolution.json"
ROCKY_CORPUS = ROOT / "fixtures" / "ga-corpus" / "rocky-linux-10.2-x86_64"
ROCKY_XCCDF = ROCKY_CORPUS / "results.xml"
ROCKY_ARF = ROCKY_CORPUS / "results.arf.xml"
ROCKY_XCCDF_OSCAL = ROCKY_CORPUS / "results.oscal.json"
ROCKY_ARF_OSCAL = ROCKY_CORPUS / "results.arf.oscal.json"
UBUNTU_CORPUS = ROOT / "fixtures" / "ga-corpus" / "ubuntu-24.04-x86_64"
UBUNTU_XCCDF = UBUNTU_CORPUS / "results.xml"
UBUNTU_ARF = UBUNTU_CORPUS / "results.arf.xml"
UBUNTU_XCCDF_OSCAL = UBUNTU_CORPUS / "results.oscal.json"
UBUNTU_ARF_OSCAL = UBUNTU_CORPUS / "results.arf.oscal.json"
COMPATIBILITY_MATRIX = ROOT / "docs" / "compatibility-matrix.md"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
BETTERLEAKS_WORKFLOW = ROOT / ".github" / "workflows" / "betterleaks.yml"
PYTHON_BUILD_LOCK_VALIDATOR = ROOT / "scripts" / "validate-python-build-lock.py"
EVIDENCE_GOLDEN = ROOT / "fixtures" / "evidence-golden"
XSD_NS = "{http://www.w3.org/2001/XMLSchema}"


class VerticalSliceTests(unittest.TestCase):
    def test_release_source_bundle_is_deterministic_and_hash_manifested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release"
            completed = subprocess.run([sys.executable, "scripts/build-release-source.py", "--version", "0.1.0-alpha.1", "--ref", "HEAD", "--output-dir", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((output / "release-manifest.json").read_text(encoding="utf-8"))
            archive = output / "EndeavorOSCAL-0.1.0-alpha.1-source.tar.gz"
            sdist = output / "endeavor_oscal-0.1.0a1.tar.gz"
            wheel = output / "endeavor_oscal-0.1.0a1-py3-none-any.whl"
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
            self.assertEqual(manifest["source-commit"], commit)
            for artifact in (archive, sdist, wheel):
                self.assertTrue(artifact.is_file())
                self.assertEqual(manifest["artifacts"][artifact.name]["sha256"], hashlib.sha256(artifact.read_bytes()).hexdigest())
                self.assertIn(f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  {artifact.name}", (output / "SHA256SUMS").read_text(encoding="utf-8"))
            verified = subprocess.run([sys.executable, "scripts/verify-python-distributions.py", "--wheel", str(wheel), "--sdist", str(sdist), "--package-version", "0.1.0a1"], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertEqual(json.loads(verified.stdout)["status"], "passed")
    def test_pinned_xccdf_tailoring_inputs_validate_and_hash(self) -> None:
        schema = ET.XMLSchema(ET.parse(str(XCCDF_SCHEMA)))
        self.assertTrue(schema.validate(ET.parse(str(XCCDF_BASELINE))), schema.error_log)
        self.assertTrue(schema.validate(ET.parse(str(XCCDF_TAILORING))), schema.error_log)
        self.assertEqual(hashlib.sha256(XCCDF_BASELINE.read_bytes()).hexdigest(), "401a2403a88a12922d833d95bc4e0b69b71da5757bf8e8269df9c95e0520c4e0")
        self.assertEqual(hashlib.sha256(XCCDF_TAILORING.read_bytes()).hexdigest(), "74f23255019049cad1e87bad47a367d418bf484febdf11489ee3e91421fb7a2a")

    def test_sanitized_arf_tailoring_fixture_preserves_embedded_tailoring(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(ARF_TAILORING)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        components = [component for stream in payload["report-requests"][0]["collection"]["data-streams"] for component in stream["components"]]
        tailoring = [component for component in components if component["payload"]["name"] == "Tailoring"]
        self.assertEqual(len(tailoring), 1)
        self.assertEqual(tailoring[0]["payload"]["id"], "xccdf_scap-workbench_tailoring_default")
        self.assertEqual(tailoring[0]["payload"]["profile-ids"], ["xccdf_com.example.www_profile_customized"])
        self.assertEqual(tailoring[0]["payload"]["version"], "1")
        self.assertIsNone(payload["reports"][0]["xccdf-result"]["tailoring"])
        self.assertNotIn("fec021b96364", ARF_TAILORING.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(ARF_TAILORING.read_bytes()).hexdigest(), "05d00bf7cc83d32dc04ebe0bdb9b9404780878b6992dc2e2d5d57d6f2c865543")

    def test_arf_sanitizer_replaces_only_schema_defined_target_facts(self) -> None:
        source = ARF_TAILORING.read_text(encoding="utf-8")
        source = source.replace("endeavor-tailoring-fixture", "raw-host.example.test")
        source = source.replace("127.0.0.1", "192.0.2.7")
        source = source.replace("0:0:0:0:0:0:0:1", "2001:db8:0:0:0:0:0:7")
        source = source.replace("00:00:00:00:00:00", "AA:BB:CC:DD:EE:FF")
        source = source.replace(
            '<identity authenticated="false" privileged="false">root</identity>',
            '<identity authenticated="false" privileged="false">operator@example.test</identity>',
        )
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.arf.xml"
            sanitized = Path(directory) / "sanitized.arf.xml"
            raw.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "scripts/sanitize-openscap-arf.py", str(raw), str(sanitized)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = inspect_arf(sanitized)
            self.assertEqual(payload["reports"][0]["xccdf-result"]["title"], "OSCAP Scan Result")
            text = sanitized.read_text(encoding="utf-8")
            for raw_value in ("raw-host.example.test", "192.0.2.7", "2001:db8:0:0:0:0:0:7", "AA:BB:CC:DD:EE:FF", "operator@example.test"):
                self.assertNotIn(raw_value, text)
            for canonical_value in ("endeavor-target", "endeavor-target.invalid", "127.0.0.1", "0:0:0:0:0:0:0:1", "00:00:00:00:00:00", "endeavor-fixture-user"):
                self.assertIn(canonical_value, text)
            self.assertIn("<interface_name>eth0</interface_name>", text)
            self.assertIn("cpe:/a:redhat:openscap:1.4.4", text)

    def test_rocky_102_corpus_is_sanitized_schema_valid_and_convertible(self) -> None:
        xccdf = inspect_xccdf(ROCKY_XCCDF)
        arf = inspect_arf(ROCKY_ARF)
        self.assertEqual(xccdf["source"]["sha256"], "45dfdb438004f550b9b30fafddfdfb3be6eabc7b5c0c004e67a5632ef0eb0e0e")
        self.assertEqual(arf["source"]["sha256"], "2ff5492934bdaea4beee1e75ae134f55f09a29038cf818ff22a89b410663d2b4")
        self.assertEqual(xccdf["test-results"][0]["targets"], ["endeavor-target"])
        self.assertEqual(xccdf["test-results"][0]["identity"]["name"], "endeavor-fixture-user")
        self.assertNotIn("localhost", ROCKY_XCCDF.read_text(encoding="utf-8"))
        self.assertNotIn("localhost", ROCKY_ARF.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            xccdf_output = Path(directory) / "xccdf.json"
            arf_output = Path(directory) / "arf.json"
            xccdf_completed = subprocess.run([sys.executable, "-m", "endeavor", "convert-xccdf", "--results", str(ROCKY_XCCDF), "--mapping", str(ARF_MAPPING), "--output", str(xccdf_output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(xccdf_completed.returncode, 0, xccdf_completed.stderr)
            arf_completed = subprocess.run([sys.executable, "-m", "endeavor", "convert-arf-xccdf", "--results", str(ROCKY_ARF), "--mapping", str(ARF_MAPPING), "--output", str(arf_output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(arf_completed.returncode, 0, arf_completed.stderr)
            self.assertEqual(xccdf_output.read_bytes(), ROCKY_XCCDF_OSCAL.read_bytes())
            self.assertEqual(arf_output.read_bytes(), ROCKY_ARF_OSCAL.read_bytes())

    def test_ubuntu_2404_corpus_is_sanitized_schema_valid_and_convertible(self) -> None:
        xccdf = inspect_xccdf(UBUNTU_XCCDF)
        arf = inspect_arf(UBUNTU_ARF)
        self.assertEqual(xccdf["source"]["sha256"], "5ec6516bc5f6ed76a145f664edb9f78314483d93582ac33bea7468e8ff045280")
        self.assertEqual(arf["source"]["sha256"], "f124fe580de14609cf8b4500cc63e1b5efe3fa4569ce94e82de2d5bb2af43458")
        self.assertEqual(xccdf["test-results"][0]["targets"], ["endeavor-target"])
        self.assertEqual(xccdf["test-results"][0]["identity"]["name"], "endeavor-fixture-user")
        self.assertEqual([item["result"] for item in xccdf["test-results"][0]["rule-results"]], ["fail", "pass"])
        self.assertNotIn("localhost", UBUNTU_XCCDF.read_text(encoding="utf-8"))
        self.assertNotIn("localhost", UBUNTU_ARF.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            xccdf_output = Path(directory) / "xccdf.json"
            arf_output = Path(directory) / "arf.json"
            xccdf_completed = subprocess.run([sys.executable, "-m", "endeavor", "convert-xccdf", "--results", str(UBUNTU_XCCDF), "--mapping", str(ARF_MAPPING), "--output", str(xccdf_output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(xccdf_completed.returncode, 0, xccdf_completed.stderr)
            arf_completed = subprocess.run([sys.executable, "-m", "endeavor", "convert-arf-xccdf", "--results", str(UBUNTU_ARF), "--mapping", str(ARF_MAPPING), "--output", str(arf_output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(arf_completed.returncode, 0, arf_completed.stderr)
            self.assertEqual(xccdf_output.read_bytes(), UBUNTU_XCCDF_OSCAL.read_bytes())
            self.assertEqual(arf_output.read_bytes(), UBUNTU_ARF_OSCAL.read_bytes())

    def test_results_sanitizer_replaces_typed_target_facts(self) -> None:
        source = ROCKY_XCCDF.read_text(encoding="utf-8")
        source = source.replace("endeavor-target.invalid", "raw-host.example.test")
        source = source.replace("endeavor-target", "raw-host")
        source = source.replace("127.0.0.1", "192.0.2.7")
        source = source.replace("0:0:0:0:0:0:0:1", "2001:db8:0:0:0:0:0:7")
        source = source.replace("00:00:00:00:00:00", "AA:BB:CC:DD:EE:FF")
        source = source.replace("endeavor-fixture-user", "operator@example.test")
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.xml"
            sanitized = Path(directory) / "sanitized.xml"
            raw.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "scripts/sanitize-openscap-results.py", str(raw), str(sanitized)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = inspect_xccdf(sanitized)
            self.assertEqual(payload["test-results"][0]["targets"], ["endeavor-target"])
            text = sanitized.read_text(encoding="utf-8")
            for raw_value in ("raw-host.example.test", "raw-host", "192.0.2.7", "2001:db8:0:0:0:0:0:7", "AA:BB:CC:DD:EE:FF", "operator@example.test"):
                self.assertNotIn(raw_value, text)

    def test_tailoring_arf_generator_has_valid_shell_syntax(self) -> None:
        completed = subprocess.run(["bash", "-n", "scripts/generate-openscap-tailoring-arf.sh"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_authored_arf_linkage_is_hash_bound_and_non_interpretive(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf-linkage", "--results", str(ARF_TAILORING), "--linkage", str(ARF_LINKAGE)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["oval-results-to-definitions"][0]["definition-count"], 2)
        self.assertFalse(payload["oval-results-to-definitions"][0]["conversion-supported"])
        self.assertFalse(payload["test-result-to-tailoring"][0]["source-profile-confirmed"])
        self.assertFalse(payload["test-result-to-tailoring"][0]["interpretation-supported"])
        self.assertEqual(completed.stdout.encode(), ARF_LINKAGE_GOLDEN.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            stale = Path(directory) / "stale.json"
            value = json.loads(ARF_LINKAGE.read_text(encoding="utf-8"))
            value["source"]["arf-sha256"] = "0" * 64
            stale.write_text(json.dumps(value), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf-linkage", "--results", str(ARF_TAILORING), "--linkage", str(stale)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("ARF hash does not match", completed.stderr)
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text(ARF_LINKAGE.read_text(encoding="utf-8").replace('"version": "1.0.0",', '"version": "1.0.0", "version": "1.0.0",', 1), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf-linkage", "--results", str(ARF_TAILORING), "--linkage", str(duplicate)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("not valid JSON", completed.stderr)

    def test_embedded_openscap_oval_511_results_validate_with_pinned_schema(self) -> None:
        root = ET.parse(str(ARF_TAILORING)).getroot()
        result = root.find(".//{http://scap.nist.gov/schema/asset-reporting-format/1.1}report/{http://scap.nist.gov/schema/asset-reporting-format/1.1}content/{http://oval.mitre.org/XMLSchema/oval-results-5}oval_results")
        self.assertIsNotNone(result)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "embedded-511-results.xml"
            source.write_bytes(ET.tostring(result))
            document = parse_results(source)
        self.assertEqual(document.generator.schema_version, "5.11")
        self.assertEqual({item.result for item in document.definitions}, {"not evaluated"})
        self.assertIsNotNone(_schema("5.11", OVAL_RESULTS_NS))

    def test_complete_oval_511_pair_converts_with_pinned_schema(self) -> None:
        source_results = (ROOT / "fixtures" / "generated-sanitized" / "oval-results.xml").read_text(encoding="utf-8")
        source_definitions = (ROOT / "fixtures" / "generated-sanitized" / "oval-definitions.xml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results-511.xml"
            definitions_path = Path(directory) / "definitions-511.xml"
            results_path.write_text(source_results.replace(">5.11.3</oval:schema_version>", ">5.11</oval:schema_version>"), encoding="utf-8")
            definitions_path.write_text(source_definitions.replace(">5.11.3</oval:schema_version>", ">5.11</oval:schema_version>"), encoding="utf-8")
            results, definitions = parse_results(results_path), parse_definitions(definitions_path)
        self.assertEqual(results.generator.schema_version, "5.11")
        self.assertEqual(definitions.generator.schema_version, "5.11")
        self.assertEqual(len(oval_assessment_results(results, definitions)["assessment-results"]["results"][0]["observations"]), 1)

    def test_compatibility_matrix_names_tested_profiles(self) -> None:
        matrix = COMPATIBILITY_MATRIX.read_text(encoding="utf-8")
        for value in ("OVAL 5.11 and 5.11.3", "XCCDF 1.2.1", "ARF 1.1", "OpenSCAP 1.4.4", "fixtures/generated-sanitized/", "fixtures/xccdf-results/", "fixtures/arf/"):
            self.assertIn(value, matrix)

    def test_cross_format_normalizers_preserve_only_provenance(self) -> None:
        xccdf = normalize_xccdf(inspect_xccdf(XCCDF_FIXTURE))
        arf = normalize_arf(inspect_arf(ARF_FIXTURE))
        self.assertEqual(xccdf["format"], "endeavor-evidence-contract")
        self.assertEqual({item["status"] for item in xccdf["assertions"]}, {"pass", "fail"})
        self.assertEqual({item["status"] for item in arf["assertions"] if item["kind"] == "oval-definition-result"}, {"true", "false", "not evaluated"})
        self.assertTrue(all("finding" not in item and "control-id" not in item for item in arf["assertions"]))
        self.assertTrue(all(item["evidence"] for item in arf["assertions"]))

    def test_oval_evidence_normalizer_preserves_results_and_definition_sources(self) -> None:
        results = parse_results(ROOT / "fixtures" / "generated-sanitized" / "oval-results.xml")
        definitions = parse_definitions(ROOT / "fixtures" / "generated-sanitized" / "oval-definitions.xml")
        evidence = normalize_oval(results, definitions)
        self.assertEqual([item["kind"] for item in evidence["sources"]], ["oval-results", "oval-definitions"])
        self.assertEqual(evidence["assertions"][0]["status"], "true")
        self.assertEqual(len(evidence["assertions"][0]["evidence"]), 2)

    def test_xccdf_mapping_requires_explicit_rule_outcome(self) -> None:
        mapping = parse_xccdf_mapping(ROOT / "fixtures" / "mappings" / "xccdf-example-v1.json")
        self.assertEqual(mapping.mappings[0].rule_id, "xccdf_moc.elpmaxe.www_rule_1")
        self.assertNotIn("pass", mapping.mappings[0].outcomes)

    def test_xccdf_mapping_report_leaves_unmapped_status_as_evidence(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "mapping-report-xccdf", "--results", str(XCCDF_FIXTURE), "--mapping", str(ROOT / "fixtures" / "mappings" / "xccdf-example-v1.json")], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["summary"], {"evaluated": 2, "mapped": 1, "unmapped": 1, "stale-mappings": 0})
        self.assertEqual(report["unmapped"][0]["result"], "pass")

    def test_xccdf_conversion_creates_only_explicit_findings(self) -> None:
        document = xccdf_assessment_results(inspect_xccdf(XCCDF_FIXTURE), parse_xccdf_mapping(ROOT / "fixtures" / "mappings" / "xccdf-example-v1.json"))
        result = document["assessment-results"]["results"][0]
        self.assertEqual(len(result["observations"]), 2)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["target"]["status"], {"state": "not-satisfied", "reason": "fail"})

    def test_convert_xccdf_writes_schema_valid_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "xccdf.json"
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert-xccdf", "--results", str(XCCDF_FIXTURE), "--mapping", str(ROOT / "fixtures" / "mappings" / "xccdf-example-v1.json"), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            validate = subprocess.run(["npm", "run", "validate:oscal", "--", "endeavor/schemas/oscal-1.2.0/assessment-results.schema.json", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertEqual(output.read_bytes(), (GOLDEN / "xccdf-mapped.json").read_bytes())

    def test_convert_arf_xccdf_writes_schema_valid_output(self) -> None:
        document = assessment_results_from_arf(inspect_arf(ARF_FIXTURE), parse_xccdf_mapping(ARF_MAPPING))
        result = document["assessment-results"]["results"][0]
        self.assertEqual(len(result["observations"]), 28)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["target"]["status"], {"state": "not-satisfied", "reason": "fail"})
        properties = result["observations"][0]["props"]
        self.assertEqual({item["name"] for item in properties if item["name"].startswith("arf-")}, {"arf-report-id", "arf-asset-id", "arf-collection-id", "arf-report-sha256"})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "arf.json"
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert-arf-xccdf", "--results", str(ARF_FIXTURE), "--mapping", str(ARF_MAPPING), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            validate = subprocess.run(["npm", "run", "validate:oscal", "--", "endeavor/schemas/oscal-1.2.0/assessment-results.schema.json", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertEqual(output.read_bytes(), (GOLDEN / "arf-xccdf-mapped.json").read_bytes())

    def test_inspect_evidence_matches_cross_format_goldens(self) -> None:
        for flag, fixture, golden in (("--xccdf", XCCDF_FIXTURE, EVIDENCE_GOLDEN / "xccdf.json"), ("--arf", ARF_FIXTURE, EVIDENCE_GOLDEN / "arf.json")):
            with self.subTest(flag=flag):
                completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-evidence", flag, str(fixture)], cwd=ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(completed.stdout.encode(), golden.read_bytes())

    def test_inspect_arf_reports_pinned_collection_manifest(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(ARF_FIXTURE)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["source"]["sha256"], "7d2845fdec85ff2b03564ea1212bec2c5f78f2f5eb6af91c9650f2ca14a7edab")
        self.assertEqual([item["id"] for item in payload["reports"]], ["xccdf1", "oval2", "oval3", "oval4"])
        self.assertEqual(payload["reports"][0]["content"]["name"], "TestResult")
        self.assertEqual(payload["reports"][0]["collection-id"], "collection1")
        self.assertEqual(payload["reports"][0]["asset-id"], "asset0")
        self.assertEqual(len(payload["report-requests"][0]["collection"]["data-streams"][0]["components"]), 5)
        linked = payload["reports"][0]["xccdf-result"]
        self.assertEqual(linked["profile"], "xccdf_org.ssgproject.content_profile_common")
        self.assertEqual(linked["benchmark"]["component-id"], "scap_org.open-scap_comp_ssg-fedora-xccdf-1.2.xml")
        self.assertIn(linked["profile"], payload["report-requests"][0]["collection"]["data-streams"][0]["components"][1]["payload"]["profile-ids"])
        self.assertEqual(linked["identity"], {"authenticated": "false", "name": "root", "privileged": "false"})
        self.assertEqual(linked["title"], "OSCAP Scan Result")
        self.assertEqual(linked["platforms"], ["cpe:/o:fedoraproject:fedora:20"])
        self.assertEqual(linked["scores"], [{"maximum": "100.000000", "system": "urn:xccdf:scoring:default", "value": "34.722221"}])
        self.assertEqual(linked["target-addresses"], ["127.0.0.1", "0:0:0:0:0:0:0:1"])
        self.assertEqual(linked["target-references"], [{"href": "", "name": "asset0", "system": "http://scap.nist.gov/schema/asset-identification/1.1"}])
        self.assertEqual({item["result"] for item in linked["rule-results"]}, {"pass", "fail", "notchecked", "notselected"})
        oval_reports = {item["id"]: item["oval-result"]["definition-results"] for item in payload["reports"] if "oval-result" in item}
        self.assertEqual({name: len(results) for name, results in oval_reports.items()}, {"oval2": 28, "oval3": 10, "oval4": 1})
        self.assertEqual(oval_reports["oval3"][0]["result"], "not evaluated")
        self.assertEqual(completed.stdout.encode(), ARF_GOLDEN.read_bytes())

    def test_inspect_arf_rejects_doctype_and_multiple_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            doctype = Path(directory) / "malicious.arf.xml"
            doctype.write_text('<!DOCTYPE x [<!ENTITY e "boom">]><x/>', encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(doctype)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            ambiguous = Path(directory) / "ambiguous.arf.xml"
            source = ARF_FIXTURE.read_text(encoding="utf-8").replace("</arf:content></arf:report>", "<extra/></arf:content></arf:report>", 1)
            ambiguous.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(ambiguous)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("ARF 1.1 validation failed", completed.stderr)

    def test_inspect_arf_rejects_archives_and_ignores_schema_hints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "report.arf"
            archive.write_bytes(b"PK\x03\x04not-an-arf")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(archive)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("archive containers", completed.stderr)
            hinted = Path(directory) / "hinted.arf.xml"
            source = ARF_FIXTURE.read_text(encoding="utf-8").replace('<arf:asset-report-collection ', '<arf:asset-report-collection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://scap.nist.gov/schema/asset-reporting-format/1.1 https://invalid.example/arf.xsd" ', 1)
            hinted.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(hinted)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_inspect_arf_rejects_remote_component_and_ambiguous_xccdf_linkage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            remote = Path(directory) / "remote.arf.xml"
            source = ARF_FIXTURE.read_text(encoding="utf-8").replace('#scap_org.open-scap_comp_ssg-fedora-xccdf-1.2.xml', 'https://invalid.example/component.xml', 1)
            remote.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(remote)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("local and resolvable", completed.stderr)
            ambiguous = Path(directory) / "ambiguous-link.arf.xml"
            source = ARF_FIXTURE.read_text(encoding="utf-8").replace('</core:relationships>', '<core:relationship type="arfvocab:createdFor" subject="xccdf1"><core:ref>collection1</core:ref></core:relationship></core:relationships>', 1)
            ambiguous.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(ambiguous)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("linkage is ambiguous", completed.stderr)

    def test_inspect_arf_rejects_missing_linked_xccdf_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-benchmark.arf.xml"
            source = ARF_FIXTURE.read_text(encoding="utf-8").replace('href="/usr/share/xml/scap/ssg/fedora/ssg-fedora-ds.xml" id="xccdf_org.ssgproject.content_benchmark_FEDORA"', 'href="https://invalid.example/benchmark.xml" id="xccdf_missing_benchmark"', 1)
            path.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("benchmark linkage is ambiguous or missing", completed.stderr)

    def test_inspect_arf_rejects_missing_linked_xccdf_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-profile.arf.xml"
            source = ARF_FIXTURE.read_text(encoding="utf-8").replace('profile idref="xccdf_org.ssgproject.content_profile_common"', 'profile idref="xccdf_missing_profile"', 1)
            path.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-arf", "--results", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("profile linkage is ambiguous or missing", completed.stderr)

    def test_vendored_xccdf_schema_bundle_compiles(self) -> None:
        self.assertIsNotNone(ET.XMLSchema(ET.parse(str(XCCDF_SCHEMA))))

    def test_upstream_xccdf_results_fixture_validates_with_pinned_schema(self) -> None:
        schema = ET.XMLSchema(ET.parse(str(XCCDF_SCHEMA)))
        self.assertTrue(schema.validate(ET.parse(str(XCCDF_FIXTURE))), schema.error_log)

    def test_inspect_xccdf_reports_pinned_fixture_inventory(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-xccdf", "--results", str(XCCDF_FIXTURE)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["source"]["path"], XCCDF_FIXTURE.name)
        self.assertEqual(payload["benchmark"]["id"], "xccdf_moc.elpmaxe.www_benchmark_test")
        self.assertEqual([(item["idref"], item["result"]) for item in payload["test-results"][0]["rule-results"]], [("xccdf_moc.elpmaxe.www_rule_1", "fail"), ("xccdf_moc.elpmaxe.www_rule_2", "pass")])
        self.assertEqual(completed.stdout.encode(), XCCDF_GOLDEN.read_bytes())

    def test_inspect_xccdf_preserves_execution_provenance_companion(self) -> None:
        completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-xccdf", "--results", str(XCCDF_PROVENANCE_FIXTURE)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)["test-results"][0]
        self.assertEqual(result["profile"], "xccdf_moc.elpmaxe.www_profile_companion")
        self.assertEqual(result["test-system"], "cpe:/a:open-scap:oscap:1.4.4")
        self.assertEqual(result["tailoring"]["href"], "https://example.invalid/tailoring.xml")
        self.assertEqual(result["identity"], {"authenticated": "true", "name": "scanner-user", "privileged": "false"})
        self.assertEqual(result["target-facts"], [{"name": "urn:xccdf:fact:asset:identifier", "value": "sanitized-asset"}])
        self.assertEqual(result["rule-results"][0]["time"], "2026-08-30T12:00:30Z")

    def test_inspect_xccdf_rejects_doctype(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malicious-xccdf.xml"
            path.write_text('<!DOCTYPE x [<!ENTITY e "boom">]><Benchmark/>', encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-xccdf", "--results", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("DOCTYPE and ENTITY", completed.stderr)

    def test_inspect_xccdf_ignores_attacker_schema_hint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hinted-xccdf.xml"
            source = XCCDF_FIXTURE.read_text(encoding="utf-8").replace('resolved="1">', 'resolved="1" xsi:schemaLocation="http://checklists.nist.gov/xccdf/1.2 https://invalid.example/attacker.xsd">')
            path.write_text(source, encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "inspect-xccdf", "--results", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_inspect_xccdf_rejects_xinclude_and_oversized_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            xinclude = Path(directory) / "xinclude.xml"
            source = XCCDF_FIXTURE.read_text(encoding="utf-8").replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xi="http://www.w3.org/2001/XInclude"').replace('<TestResult ', '<xi:include href="file:///not-opened.xml"/><TestResult ')
            xinclude.write_text(source, encoding="utf-8")
            rejected = subprocess.run([sys.executable, "-m", "endeavor", "inspect-xccdf", "--results", str(xinclude)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(rejected.returncode, 3)
            oversized = Path(directory) / "oversized.xml"
            oversized.write_bytes(b" " * (5 * 1024 * 1024 + 1))
            limited = subprocess.run([sys.executable, "-m", "endeavor", "inspect-xccdf", "--results", str(oversized)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(limited.returncode, 3)

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
                    result = document["assessment-results"]["results"][0]
                    self.assertEqual(result["props"], [
                        {"name": "oval-generator-product-name", "ns": "https://endeavor.dev/ns/oval", "value": "Endeavor synthetic evaluator"},
                        {"name": "oval-generator-product-version", "ns": "https://endeavor.dev/ns/oval", "value": "0.1.0"},
                        {"name": "oval-schema-version", "ns": "https://endeavor.dev/ns/oval", "value": "5.11.3"},
                        {"name": "oval-generator-timestamp", "ns": "https://endeavor.dev/ns/oval", "value": "2026-08-29T00:00:00Z"},
                    ])
                    self.assertEqual(output.read_bytes(), (GOLDEN / name.replace(".xml", ".json")).read_bytes())

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

    def test_excessive_xml_width_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "too-wide.xml"
            output = Path(directory) / "result.json"
            path.write_text("<x>" + "<y/>" * MAX_XML_ELEMENTS + "</x>", encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn(f"exceeds {MAX_XML_ELEMENTS} element limit", completed.stderr)
            self.assertFalse(output.exists())

    def test_deterministic_malformed_input_corpus_is_handled_without_output(self) -> None:
        generator = random.Random(20260830)
        payloads = [b"", b"<", b"\x00", b"<?xml version='1.0'?><x>\xff</x>"]
        payloads.extend(generator.randbytes(size) for size in range(1, 33))
        source = (RESULTS / "pass.xml").read_bytes()
        payloads.extend(source[:offset] for offset in (0, source.find(b"?>") + 2, source.find(b"<results>") + 4, len(source) // 2, source.rfind(b"</") + 3))
        self.assertGreaterEqual(len(payloads), 40)
        with tempfile.TemporaryDirectory() as directory:
            for index, payload in enumerate(payloads):
                with self.subTest(case=index):
                    path = Path(directory) / f"mutated-{index}.xml"
                    output = Path(directory) / f"mutated-{index}.json"
                    path.write_bytes(payload)
                    completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
                    self.assertEqual(completed.returncode, 3, completed.stderr)
                    self.assertNotIn("Traceback", completed.stderr)
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

    def test_mapping_report_is_deterministic_and_preserves_mapping_visibility(self) -> None:
        command = [sys.executable, "-m", "endeavor", "mapping-report", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING)]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        report = json.loads(first.stdout)
        self.assertEqual(report["summary"], {"evaluated": 1, "mapped": 1, "unmapped": 0, "stale-mappings": 0})
        self.assertEqual(report["mapping"]["path"], "example-v1.json")
        self.assertEqual(report["mapped"][0]["oval-definition-id"], "oval:org.endeavor:def:1")
        self.assertEqual(report["mapped"][0]["result"], "false")
        self.assertEqual(report["mapped"][0]["targets"], [{"type": "objective-id", "target-id": "ac-2.1_obj.1"}])
        self.assertNotIn(str(ROOT), first.stdout)

    def test_mapping_report_shows_unmapped_and_stale_ids(self) -> None:
        mapping = {"format": "endeavor-oval-oscal-mapping", "version": "1.0.0", "oscal-version": "1.2.0", "mappings": [{"oval-definition-id": "oval:org.endeavor:def:stale", "target": {"type": "statement-id", "target-id": "ac-2_smt.a"}, "outcomes": {"false": {"state": "not-satisfied", "reason": "fail"}}}]}
        with tempfile.TemporaryDirectory(prefix="endeavor-private-map-") as directory:
            path = Path(directory) / "mapping.json"
            path.write_text(json.dumps(mapping), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "mapping-report", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["summary"], {"evaluated": 1, "mapped": 0, "unmapped": 1, "stale-mappings": 1})
            self.assertEqual(report["unmapped"][0]["oval-definition-id"], "oval:org.endeavor:def:1")
            self.assertEqual(report["stale-mappings"], ["oval:org.endeavor:def:stale"])
            self.assertNotIn(directory, completed.stdout)

    def test_explicit_mapping_emits_schema_valid_finding_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            document = json.loads(output.read_text())
            result = document["assessment-results"]["results"][0]
            finding = result["findings"][0]
            self.assertEqual(finding["target"], {"type": "objective-id", "target-id": "ac-2.1_obj.1", "status": {"state": "not-satisfied", "reason": "fail"}})
            properties = finding["props"]
            self.assertIn({"name": "oval-result", "ns": "https://endeavor.dev/ns/oval", "value": "false"}, properties)
            self.assertIn({"name": "mapping-version", "ns": "https://endeavor.dev/ns/oval", "value": "1.0.0"}, properties)
            self.assertIn({"name": "source-observation-uuid", "ns": "https://endeavor.dev/ns/oval", "value": result["observations"][0]["uuid"]}, properties)
            self.assertNotIn("related-observations", finding)
            self.assertEqual(document["assessment-results"]["back-matter"]["resources"][2]["rlinks"][0]["href"], "example-v1.json")
            validate = subprocess.run(["npm", "run", "validate:oscal", "--", "endeavor/schemas/oscal-1.2.0/assessment-results.schema.json", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_findings_lists_explicit_mapped_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            convert = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(convert.returncode, 0, convert.stderr)
            completed = subprocess.run([sys.executable, "-m", "endeavor", "findings", "--results", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["summary"], {"findings": 1})
            self.assertEqual(report["assessment-results"]["path"], "result.json")
            self.assertEqual(report["findings"][0]["oval-definition-id"], "oval:org.endeavor:def:1")
            self.assertEqual(report["findings"][0]["target"], {"type": "objective-id", "target-id": "ac-2.1_obj.1", "state": "not-satisfied", "reason": "fail"})
            self.assertNotIn(directory, completed.stdout)

    def test_mapping_does_not_infer_finding_for_unknown_oval_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(RESULTS / "unknown.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text())["assessment-results"]["results"][0]
            self.assertNotIn("findings", result)

    def test_diff_reports_deterministic_oval_status_change(self) -> None:
        command = [sys.executable, "-m", "endeavor", "diff", "--before", str(GOLDEN / "pass.json"), "--after", str(GOLDEN / "fail.json")]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        report = json.loads(first.stdout)
        self.assertEqual(report["summary"], {"added": 0, "removed": 0, "changed": 1, "unchanged": 0})
        self.assertEqual(report["changed"], [{"oval-definition-id": "oval:org.endeavor:def:1", "before": "true", "after": "false"}])
        self.assertEqual(report["before"]["path"], "pass.json")
        self.assertEqual(report["after"]["path"], "fail.json")
        self.assertNotIn(str(ROOT), first.stdout)

    def test_diff_rejects_invalid_input_without_path_disclosure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="endeavor-private-diff-") as directory:
            invalid = Path(directory) / "invalid.json"
            invalid.write_text("[]", encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "diff", "--format", "json", "--before", str(invalid), "--after", str(GOLDEN / "fail.json")], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stderr)["error"]["code"], "input-invalid")
            self.assertNotIn(directory, completed.stderr)

    def test_report_writes_accessible_html_without_host_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            completed = subprocess.run([sys.executable, "-m", "endeavor", "report", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(MAPPING), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn('<main>', html)
            self.assertIn('<h1>Endeavor mapping coverage report</h1>', html)
            self.assertIn('<caption>Explicit OVAL-to-OSCAL targets</caption>', html)
            self.assertIn('scope="col"', html)
            self.assertIn("example-v1.json", html)
            self.assertNotIn(str(ROOT), html)

    def test_report_escapes_mapping_content(self) -> None:
        mapping = {"format": "endeavor-oval-oscal-mapping", "version": "1.0.0", "oscal-version": "1.2.0", "mappings": [{"oval-definition-id": "<script>alert(1)</script>", "target": {"type": "statement-id", "target-id": "ac-2_smt.a"}, "outcomes": {"false": {"state": "not-satisfied", "reason": "fail"}}}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.json"
            output = Path(directory) / "report.html"
            path.write_text(json.dumps(mapping), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "report", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(path), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            self.assertNotIn("<script>alert(1)</script>", html)

    def test_invalid_mapping_is_rejected_without_path_disclosure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="endeavor-private-map-") as directory:
            path = Path(directory) / "invalid-map.json"
            path.write_text("[]", encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "mapping-report", "--format", "json", "--results", str(RESULTS / "fail.xml"), "--definitions", str(DEFINITIONS), "--mapping", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            diagnostic = json.loads(completed.stderr)
            self.assertEqual(diagnostic["error"]["code"], "input-invalid")
            self.assertNotIn(directory, completed.stderr)

    def test_mapping_duplicate_members_are_rejected_before_conversion(self) -> None:
        fixtures = ((MAPPING, parse_oval_mapping), (ARF_MAPPING, parse_xccdf_mapping))
        with tempfile.TemporaryDirectory() as directory:
            for source, parser in fixtures:
                with self.subTest(mapping=source.name):
                    duplicate = Path(directory) / source.name
                    duplicate.write_text(source.read_text(encoding="utf-8").replace('"version": "1.0.0",', '"version": "1.0.0", "version": "1.0.0",', 1), encoding="utf-8")
                    with self.assertRaisesRegex(OvalInputError, "not valid JSON"):
                        parser(duplicate)

    def test_mapping_target_id_must_be_an_oscal_token(self) -> None:
        fixtures = ((MAPPING, parse_oval_mapping), (ARF_MAPPING, parse_xccdf_mapping))
        with tempfile.TemporaryDirectory() as directory:
            for source, parser in fixtures:
                with self.subTest(mapping=source.name):
                    invalid = Path(directory) / source.name
                    invalid.write_text(source.read_text(encoding="utf-8").replace('"target-id": "ac-2.1_obj.1"', '"target-id": "has space"', 1), encoding="utf-8")
                    with self.assertRaisesRegex(OvalInputError, "target-id must be an OSCAL token"):
                        parser(invalid)

    def test_xccdf_without_test_result_has_stable_input_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="endeavor-private-xccdf-") as directory:
            source = Path(directory) / "empty.xml"
            output = Path(directory) / "result.json"
            root = ET.parse(str(XCCDF_FIXTURE)).getroot()
            for test in root.findall("{http://checklists.nist.gov/xccdf/1.2}TestResult"):
                root.remove(test)
            source.write_bytes(ET.tostring(root))
            self.assertTrue(ET.XMLSchema(ET.parse(str(XCCDF_SCHEMA))).validate(ET.parse(str(source))))
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert-xccdf", "--format", "json", "--results", str(source), "--mapping", str(ARF_MAPPING), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(completed.stdout, "")
            diagnostic = json.loads(completed.stderr)
            self.assertEqual(diagnostic["error"]["code"], "input-invalid")
            self.assertIn("XCCDF Results must contain at least one TestResult: empty.xml", diagnostic["error"]["message"])
            self.assertNotIn("Traceback", completed.stderr)
            self.assertNotIn(directory, completed.stderr)
            self.assertFalse(output.exists())

    def test_release_workflow_keeps_build_steps_unprivileged(self) -> None:
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        build, publish = workflow.split("\n  publish:\n", 1)
        self.assertIn("permissions: {}", workflow)
        self.assertIn("  build:\n", build)
        self.assertIn("      contents: read", build)
        self.assertIn("persist-credentials: false", build)
        self.assertIn("actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a", build)
        self.assertIn("needs: build", publish)
        self.assertIn("actions/download-artifact@37930b1c2abaa49bbe596cd826c3c89aef350131", publish)
        self.assertIn("sha256sum --check --strict SHA256SUMS", publish)
        self.assertIn("contents: write", publish)
        self.assertIn("id-token: write", publish)
        self.assertIn("attestations: write", publish)
        self.assertNotIn("actions/checkout", publish)
        self.assertNotIn("pip install", publish)
        self.assertNotIn("npm ci", publish)
        self.assertNotIn("scripts/", publish)

    def test_betterleaks_workflow_is_checksum_pinned_and_non_validating(self) -> None:
        workflow = BETTERLEAKS_WORKFLOW.read_text(encoding="utf-8")
        policy = (ROOT / ".betterleaks.toml").read_text(encoding="utf-8")
        wrapper = (ROOT / "scripts" / "run-betterleaks.sh").read_text(encoding="utf-8")

        self.assertIn("contents: read", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("betterleaks_1.8.1_linux_x64.tar.gz", workflow)
        self.assertIn("efa407244e1ea8e35f582b8a42becdeac08bdead04f68eb752adda722d583c2a", workflow)
        self.assertIn("sha256sum --check --status", workflow)
        self.assertNotIn("--validation", workflow)
        self.assertNotIn("--validation", wrapper)
        self.assertNotIn("--validation-env-vars", workflow)
        self.assertNotIn("github", wrapper)
        self.assertIn("--redact=100", wrapper)
        self.assertIn("--confidence high", wrapper)
        self.assertIn("--ignore-gitleaks-allow", wrapper)
        self.assertIn("--timeout 300", wrapper)
        self.assertIn(".betterleaksignore", wrapper)
        self.assertIn(".gitleaksignore", wrapper)
        self.assertIn("env -i PATH=/usr/bin:/bin", workflow)
        self.assertFalse((ROOT / ".betterleaksignore").exists())
        self.assertFalse((ROOT / ".gitleaksignore").exists())
        self.assertIn("[extend]", policy)
        self.assertIn("useDefault = true", policy)

    def test_python_build_lock_is_hash_verified_and_used_by_ci(self) -> None:
        completed = subprocess.run([sys.executable, str(PYTHON_BUILD_LOCK_VALIDATOR)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Python build lock is valid.", completed.stdout)
        for workflow_path in (ROOT / ".github" / "workflows" / "validate.yml", RELEASE_WORKFLOW):
            workflow = workflow_path.read_text(encoding="utf-8")
            self.assertIn("--require-hashes --only-binary=:all: -r requirements-python-build.lock", workflow)
        self.assertIn('"--no-isolation"', (ROOT / "scripts" / "build-release-source.py").read_text(encoding="utf-8"))

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
            path.write_text(source.replace(">5.11.3</oval:schema_version>", ">5.10</oval:schema_version>"), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(path), "--definitions", str(DEFINITIONS), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("unsupported OVAL core schema version", completed.stderr)
            self.assertFalse(output.exists())

    def test_mismatched_results_and_definitions_schema_versions_are_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            definitions = Path(directory) / "definitions-511.xml"
            output = Path(directory) / "result.json"
            source = DEFINITIONS.read_text(encoding="utf-8")
            definitions.write_text(source.replace(">5.11.3</oval:schema_version>", ">5.11</oval:schema_version>"), encoding="utf-8")
            completed = subprocess.run([sys.executable, "-m", "endeavor", "convert", "--results", str(RESULTS / "pass.xml"), "--definitions", str(definitions), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("OVAL Results and Definitions schema versions must match (5.11.3 != 5.11)", completed.stderr)
            self.assertFalse(output.exists())

    def test_governance_readiness_evidence_is_complete_and_deterministic(self) -> None:
        command = [sys.executable, "scripts/validate-governance-readiness.py"]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["format"], "endeavor-governance-readiness")
        self.assertEqual(payload["status"], "ready-for-governance-planning")
        self.assertIn("docs/alpha-acceptance-record-v0.1.0-alpha.1.md", payload["evidence"])

    def test_ga_release_readiness_fails_closed_without_a_versioned_record(self) -> None:
        command = [
            sys.executable,
            "scripts/validate-ga-release-readiness.py",
            "--tag",
            "v9999.0.0",
            "--candidate-commit",
            "0" * 40,
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stderr)
        self.assertEqual(payload["format"], "endeavor-ga-release-readiness-validation")
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["record"], "ga-release-readiness-9999.0.0.json")

    def test_ga_release_readiness_binds_tag_commit_and_evidence_hashes(self) -> None:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            temporary = Path(directory)
            evidence: dict[str, dict[str, str]] = {}
            roles = (
                "human-acceptance",
                "accessibility-review",
                "license-review",
                "vulnerability-review",
                "reproducible-build",
                "release-notes",
                "support-policy",
                "compatibility-matrix",
            )
            for role in roles:
                path = temporary / f"{role}.md"
                path.write_text(f"Evidence for {role}\n", encoding="utf-8")
                evidence[role] = {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            record_path = temporary / "ga-release-readiness.json"
            record_path.write_text(
                json.dumps(
                    {
                        "format": "endeavor-ga-release-readiness",
                        "version": "1.0.0",
                        "status": "accepted",
                        "tag": "v1.2.3",
                        "candidate-commit": commit,
                        "reviewed-at": "2026-08-31T05:00:00Z",
                        "reviewer": "Test reviewer",
                        "evidence": evidence,
                    }
                ),
                encoding="utf-8",
            )
            command = [
                sys.executable,
                "scripts/validate-ga-release-readiness.py",
                "--tag",
                "v1.2.3",
                "--candidate-commit",
                commit,
                "--record",
                str(record_path),
            ]
            import runpy
            gate = runpy.run_path(ROOT / "scripts" / "validate-ga-release-readiness.py")
            verified = gate["validate"](json.loads(record_path.read_text(encoding="utf-8")), "v1.2.3", commit, record_path, enforce_filename=False)
            self.assertEqual(set(verified), set(roles))
            rejected_version = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(rejected_version.returncode, 1)
            self.assertIn("project package version does not match", rejected_version.stderr)
            (temporary / "license-review.md").write_text("changed\n", encoding="utf-8")
            rejected = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("license-review evidence SHA-256 does not match", rejected.stderr)

    def test_alpha_workflow_can_retain_a_hashed_execution_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            record_path = Path(directory) / "alpha-workflow-record.json"
            completed = subprocess.run([sys.executable, "scripts/validate-alpha-workflow.py", "--record", str(record_path)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            record = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(record["format"], "endeavor-alpha-workflow-validation")
            self.assertEqual(record["version"], "1.1.0")
            self.assertEqual(record["status"], "passed")
            self.assertEqual(len(record["repository-commit"]), 40)
            self.assertEqual(record["sources"]["definitions.xml"], hashlib.sha256(DEFINITIONS.read_bytes()).hexdigest())
            self.assertEqual(set(record["artifacts"]), {"pass.json", "fail.json", "mapping-report.html"})
            self.assertTrue(all(len(value) == 64 for value in record["artifacts"].values()))

    def test_vulnerability_exceptions_require_a_nonexpired_exact_disposition(self) -> None:
        command = [sys.executable, "scripts/validate-vulnerability-exceptions.py"]
        accepted = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertEqual(json.loads(accepted.stdout)["status"], "passed")
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "expired.json"
            record.write_text(json.dumps({"format": "endeavor-vulnerability-exceptions", "version": "1.0.0", "exceptions": [{"id": "EXC-0001", "package": "example", "ecosystem": "npm", "advisory": "GHSA-aaaa-bbbb-cccc", "affected-range": "< 1.0.0", "reason": "fixture", "compensating-control": "fixture", "approved-by": "maintainer", "approved-at": "2025-01-01T00:00:00Z", "expires-at": "2025-01-02T00:00:00Z"}]}), encoding="utf-8")
            rejected = subprocess.run(command + ["--record", str(record)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("expired", rejected.stderr)

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
