# Compatibility matrix

This matrix defines the tested Endeavor support profile. “Inventory” means
bounded parsing and provenance retention; it does not imply evaluator
replacement, remediation, or automatic OSCAL control mapping.

| Source format | Producer / version | Tested fixture | Public command | Supported behavior | Explicit limit |
| --- | --- | --- | --- | --- | --- |
| OVAL Results + Definitions | OpenSCAP 1.4.4; OVAL 5.11.3 | `fixtures/generated-sanitized/`, plus six semantic cases in `fixtures/manifest.yaml` | `inspect`, `convert`, `findings`, `diff` | Pinned-XSD validation, all six OVAL statuses, deterministic OSCAL conversion with explicit mappings | Generated-sanitized fixture is not an upstream scan; OVAL 5.12/5.12.2 is future-release work |
| XCCDF Results | OpenSCAP 1.4.4; XCCDF 1.2.1 | `fixtures/xccdf-results/openscap-1.4.4-results-xccdf12.xml` | `inspect-xccdf` | Pinned-XSD validation and execution/provenance inventory | Inventory only; no OSCAL conversion or evaluator replacement |
| XCCDF provenance fields | Schema-valid sanitized companion | `fixtures/xccdf-results/provenance-companion-xccdf12.xml` | `inspect-xccdf` | Profile, tailoring reference, evaluator, identity, target facts, rule timing/weight, score | Companion is not a production assessment and does not expand producer support |
| ARF collection | OpenSCAP 1.4.4; ARF 1.1 | `fixtures/arf/openscap-1.4.4-xccdf-overrides.arf.xml` | `inspect-arf` | Bounded manifest; local component resolution; canonical component hashes; XCCDF report/asset/collection/benchmark/profile traceability | No remote dereference; no archive support; no ARF-to-OSCAL conversion |
| ARF embedded OVAL reports | Same ARF fixture | `fixtures/arf/openscap-1.4.4-xccdf-overrides.arf.xml` | `inspect-arf` | Exact OVAL definition IDs/statuses and canonical report-content hash | Fixture has no authoritative, unique definitions-component relationship; Endeavor leaves it unlinked |

## CI evidence

`tests/test_vertical_slice.py` compares committed OVAL, XCCDF, and ARF golden
outputs and exercises hostile-input rejections. `.github/workflows/validate.yml`
runs that suite, validates the SBOM, and executes the representative alpha
workflow. Fixture source provenance and input hashes are recorded beside each
fixture in `fixtures/*/PROVENANCE.md`.

## Deferred before Governance

1. ARF archive/container limits and schema validation.
2. A real, unambiguous ARF tailoring fixture and normalization of tailoring
   decisions.
3. A shared source-to-OSCAL evidence contract for supported XCCDF/ARF results,
   with no inferred controls or findings.
4. Cross-format conversion goldens and a human reviewer acceptance record for
   the alpha workflow.
