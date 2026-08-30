# OpenSCAP XCCDF Results fixture provenance

`openscap-1.4.4-results-xccdf12.xml` is an upstream OpenSCAP test fixture,
not an assessment of a real target. It contains two intentionally small XCCDF
rule results (`fail` and `pass`) and the placeholder target `Test Target`.
It is retained unchanged so the exact upstream source remains auditable.

| Field | Value |
| --- | --- |
| Source | `https://github.com/OpenSCAP/openscap/blob/1.4.4/tests/API/XCCDF/report/results-xccdf12.xml` |
| Retrieval | 2026-08-30 |
| Producer/version context | OpenSCAP 1.4.4 source test corpus; XCCDF 1.2.1 schema profile |
| SHA-256 | `38e72324eefab5554d711afb0eec6bd9c502066d6bdebc09be73f3ebcf1ef4c2` |
| Transformations | None; upstream synthetic test fixture, reviewed for absence of real target data. |

The expected normalized inventory is
`openscap-1.4.4-results-xccdf12.inventory.json` (SHA-256
`d1032f22100fb83c63432f8649351d25fe3722a099718690ac1f86006d15961a`).
The test suite regenerates and compares it byte-for-byte; any fixture or
normalization change must update this provenance record in the same commit.

The fixture establishes schema and inventory behavior only. It does not prove
support for arbitrary XCCDF content, ARF collections, tailoring, or a real
OpenSCAP evaluator run.

`provenance-companion-xccdf12.xml` is a separate, schema-valid sanitized
companion derived from the shape of the pinned fixture. It is **not** an
upstream assessment artifact and contains only reserved documentation target
values. It exercises preservation of evaluator, selected profile, tailoring
reference, execution identity, target facts, per-rule time/weight, and score.
Its addition does not change the recorded representative alpha workflow input.

The companion's SHA-256 is
`b3dea671d99b77ec56902242908edc122b11a473520f797274c6a52fba714ff7`.
