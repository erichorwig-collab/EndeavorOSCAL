# OpenSCAP ARF fixture provenance

`openscap-1.4.4-xccdf-overrides.arf.xml` is an upstream OpenSCAP synthetic
unit-test fixture, not an assessment of a production target. It is intentionally
retained unchanged to establish a bounded ARF collection-manifest intake slice.

| Field | Value |
| --- | --- |
| Source | `https://github.com/OpenSCAP/openscap/blob/1.4.4/tests/API/XCCDF/unittests/test_xccdf_overrides.arf.xml` |
| Immutable source commit | `4ac56ce0e6dfdea7215b5ad202b3db20855d2507` |
| Retrieval | 2026-08-30 |
| Producer/version context | OpenSCAP 1.4.4 source test corpus; ARF 1.1 |
| SHA-256 | `7d2845fdec85ff2b03564ea1212bec2c5f78f2f5eb6af91c9650f2ca14a7edab` |
| Size | 338,127 bytes |
| Transformations | None; upstream synthetic fixture reviewed for test-only target values. |

The fixture contains one asset, four reports, five embedded components, and an
XCCDF TestResult with profile, identity, target facts, rule metadata, and
scores. It contains no tailoring reference or evaluator `test-system`; those
remain separately required before ARF-to-normalized-evidence support is claimed.
It does not alter the representative alpha workflow inputs.

The expected collection manifest is
`openscap-1.4.4-xccdf-overrides.manifest.json` (SHA-256
`c2835b72bb7e5547206e0fd4d590a528185e58e49f7867ee8e386cb43a0f03c1`).
Embedded content hashes use XML C14N without comments, making them stable for
the exact parsed component rather than a filesystem path or fetched resource.
