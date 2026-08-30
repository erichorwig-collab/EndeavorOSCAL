# Vendored schema manifest

| Artifact | Version | Source | SHA-256 |
| --- | --- | --- | --- |
| OVAL schema bundle | 5.11.3 | Fedora 43 `openscap-1:1.4.4-1.fc43`, extracted from `/usr/share/openscap/schemas/oval/5.11.3` | `8ed054b51c79fb4fb89792ce10ae75eff74e072c5fee0fd92cc528c068ebdf9c` |
| OVAL schema bundle | 5.11 | OVALProject Language commit `7a3efac6429f9378fea3b3929cdf316ecf14d491`, `schemas/` | `12df70d237c7b530ac23b4dda1b42db1793d070676cd517492918d34796768b0` |
| Shared schema bundle | Fedora 43 | Fedora 43 `openscap-1:1.4.4-1.fc43`, extracted from `/usr/share/openscap/schemas/common` | `38c49db22d4a3a6be19e2b9506874e8ba1d5c0b630a2f1b2d1951181d7415ada` |
| OVAL schema archive | 5.12.2 | https://github.com/OVAL-Community/OVAL/releases/download/v5.12.2/schemas-5.12.2.zip | `bdfeae8dc14b322d712508d9b5005af9881f7e9390caddd131f4574c2105337e` |
| OSCAL Assessment Results JSON Schema | 1.2.0 | https://github.com/usnistgov/OSCAL/releases/download/v1.2.0/oscal_assessment-results_schema.json | `a587b1580651f435a376d04dde78aaba6783c58ceb6f93f482d0b61d0c8afa59` |
| XCCDF schema bundle | 1.2.1 | OpenSCAP 1.4.4 / Fedora 43 `openscap-1:1.4.4-1.fc43`; CPE naming from OpenSCAP tag `1.4.4` | `a7f650c414e99ffc4b642cfb5bc48597b47ea2c503728d48ed067f3b3ec0101e` (XCCDF), `4b1ca823262492c26f8f19541368279d2e77a81ff4164a3d4836e900398a6e4f` (CPE language), `f121640ed45501eb166a8332f66b52983ff54e242fe015df156931edf6081983` (CPE naming), `650e29d406c52596d4cd416da9f937a80a4b068cd4a1f56dc25cb8b7d13d18c4` (XML) |
| ARF schema bundle | 1.1.1 | OpenSCAP 1.4.4 tag `1.4.4` | `5a0a73807d959740827a40187bc639fb8f4cdcc23b708464366e007baa96391a` (ARF), `9a6fb5d3e65732731005c9afa384bcad277e2f4f1ca92f39155052e05f7c3644` (asset ID), `4b194a19df5200eb232e1dc7b6cf24fb343adf309ea803b4e2e2060133584c98` (reporting core), `cc8353e803f2ccb594cea247b00935477d672f2c5b5affc95a04cb3721a50f0e` (xAL), `0ecd4af2be33b00ebe7d55dd66c5794b432a0d2befeb49e6f30aaed92be29f8d` (xNL) |

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

The 5.11 profile uses the archived OVALProject Language schema source, which
identifies OVAL 5.11.2 schema artifacts and retains the upstream license
headers. Its local wrapper schemas are generated using the same script and
resolver restrictions as 5.11.3.

The OSCAL schema is retained as the exact released JSON Schema artifact. Python
`jsonschema` cannot currently evaluate all of this schema under Python 3.14
because it contains ECMA-262 Unicode property escapes (`\\p{...}`) that the
Python `re` engine rejects. Project-local AJV 8.17.1 is the pinned compatible
validator and is exercised by the vertical-slice test; retain its lockfile and
add the same command to CI before a public release.

The XCCDF 1.2 bundle is a Phase 4 intake prerequisite only. Its restricted
resolver profile must allow exactly `xccdf_1.2.xsd`, `cpe-language_2.3.xsd`,
`cpe-naming_2.3.xsd`, and `common/xml.xsd`; instance schema hints and every
network or out-of-bundle location remain untrusted.

The ARF 1.1 resolver permits only these five files plus the already-pinned
common XLink/XML and CPE naming schemas. Instance schema hints, remote imports,
and any other local locations remain untrusted.
