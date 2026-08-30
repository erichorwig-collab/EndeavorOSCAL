# Compatibility matrix

This matrix defines the tested Endeavor support profile. “Inventory” means
bounded parsing and provenance retention; it does not imply evaluator
replacement, remediation, or automatic OSCAL control mapping.

| Source format | Producer / version | Tested fixture | Public command | Supported behavior | Explicit limit |
| --- | --- | --- | --- | --- | --- |
| OVAL Results + Definitions | OpenSCAP 1.4.4; OVAL 5.11 and 5.11.3 | `fixtures/generated-sanitized/`, plus six semantic cases in `fixtures/manifest.yaml` | `inspect`, `convert`, `findings`, `diff` | Pinned-XSD validation, all six OVAL statuses, deterministic OSCAL conversion with explicit mappings | Generated-sanitized conversion fixture is 5.11.3; OVAL 5.12/5.12.2 is future-release work |
| XCCDF Results | OpenSCAP 1.4.4; XCCDF 1.2.1 | `fixtures/xccdf-results/openscap-1.4.4-results-xccdf12.xml` | `inspect-xccdf`, `convert-xccdf` | Pinned-XSD validation, provenance inventory, and schema-valid conversion with explicit mappings | No evaluator replacement; unmapped rules remain evidence only |
| XCCDF provenance fields | Schema-valid sanitized companion | `fixtures/xccdf-results/provenance-companion-xccdf12.xml` | `inspect-xccdf` | Profile, tailoring reference, evaluator, identity, target facts, rule timing/weight, score | Companion is not a production assessment and does not expand producer support |
| ARF collection | OpenSCAP 1.4.4; ARF 1.1 | `fixtures/arf/openscap-1.4.4-xccdf-overrides.arf.xml` | `inspect-arf`, `convert-arf-xccdf` | Bounded manifest; local component resolution; canonical component hashes; XCCDF report/asset/collection/benchmark/profile traceability; schema-valid conversion of the one linked XCCDF report using an explicit mapping | No remote dereference or archive support; embedded OVAL remains unconverted |
| ARF embedded OVAL reports | Same ARF fixture | `fixtures/arf/openscap-1.4.4-xccdf-overrides.arf.xml` | `inspect-arf` | Exact OVAL definition IDs/statuses and canonical report-content hash | Fixture has no authoritative, unique definitions-component relationship; Endeavor leaves it unlinked |
| Authored ARF linkage manifest | Generated-sanitized OpenSCAP 1.4.4 tailoring ARF | `fixtures/linkage/openscap-1.4.4-tailoring-v1.json` | `inspect-arf-linkage` | SHA-256-bound, exact local OVAL Results-to-Definitions and TestResult-to-Tailoring provenance resolution | The embedded Definitions component lacks required generator metadata; tailoring linkage is provenance, not decision interpretation |

## CI evidence

`tests/test_vertical_slice.py` compares committed OVAL, XCCDF, and ARF golden
outputs and exercises hostile-input rejections. `.github/workflows/validate.yml`
runs that suite, validates the SBOM, and executes the representative alpha
workflow and the governance-readiness evidence checker. The accepted human
review record is `docs/alpha-acceptance-record-2026-08-30.md`. Fixture source
provenance and input hashes are recorded beside each fixture in
`fixtures/*/PROVENANCE.md`.

## Deferred before Governance

1. ARF archive/container ingestion beyond the explicit archive rejection.
2. A generated-sanitized ARF tailoring result from the pinned OpenSCAP 1.4.4
   baseline/tailoring inputs in `fixtures/xccdf-tailoring/`, and normalization
   of tailoring decisions.
3. Extending the shared source-to-OSCAL evidence contract beyond the linked
   XCCDF report, with no inferred controls or findings.

The alpha human-review gate is complete; its accepted record is retained in
`docs/alpha-acceptance-record-2026-08-30.md`.
