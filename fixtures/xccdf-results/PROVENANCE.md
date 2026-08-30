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

The fixture establishes schema and inventory behavior only. It does not prove
support for arbitrary XCCDF content, ARF collections, tailoring, or a real
OpenSCAP evaluator run.
