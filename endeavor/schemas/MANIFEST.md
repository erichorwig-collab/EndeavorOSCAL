# Vendored schema manifest

| Artifact | Version | Source | SHA-256 |
| --- | --- | --- | --- |
| OVAL schema bundle | 5.11.3 | Fedora 43 `openscap-1:1.4.4-1.fc43`, extracted from `/usr/share/openscap/schemas/oval/5.11.3` | `8ed054b51c79fb4fb89792ce10ae75eff74e072c5fee0fd92cc528c068ebdf9c` |
| Shared schema bundle | Fedora 43 | Fedora 43 `openscap-1:1.4.4-1.fc43`, extracted from `/usr/share/openscap/schemas/common` | `38c49db22d4a3a6be19e2b9506874e8ba1d5c0b630a2f1b2d1951181d7415ada` |
| OVAL schema archive | 5.12.2 | https://github.com/OVAL-Community/OVAL/releases/download/v5.12.2/schemas-5.12.2.zip | `bdfeae8dc14b322d712508d9b5005af9881f7e9390caddd131f4574c2105337e` |
| OSCAL Assessment Results JSON Schema | 1.2.0 | https://github.com/usnistgov/OSCAL/releases/download/v1.2.0/oscal_assessment-results_schema.json | `a587b1580651f435a376d04dde78aaba6783c58ceb6f93f482d0b61d0c8afa59` |

The complete OVAL archive is vendored because the core Results and Definitions
schemas have local imports and extension points. The archive's release hash is
the integrity pin for its extracted contents. Source documents must not use
`xsi:schemaLocation` to select a schema.

The 5.11.3 profile uses the exact XSDs packaged by the provenance-pinned Fedora
43 OpenSCAP evaluator image
`registry.fedoraproject.org/fedora:43@sha256:26a6fa6061ce1cf1e1592079e072c0dac77c0cdc50e8e306690febca1165b674`.
The listed hashes are deterministic hashes of sorted per-file SHA-256 records
for 52 OVAL XSDs and four shared XSDs, respectively. Static wrappers are
generated from these locally vendored files by
`scripts/generate-oval-schema-wrappers.py`; document schema hints remain
ignored.

The OSCAL schema is retained as the exact released JSON Schema artifact. Python
`jsonschema` cannot currently evaluate all of this schema under Python 3.14
because it contains ECMA-262 Unicode property escapes (`\\p{...}`) that the
Python `re` engine rejects. Project-local AJV 8.17.1 is the pinned compatible
validator and is exercised by the vertical-slice test; retain its lockfile and
add the same command to CI before a public release.
