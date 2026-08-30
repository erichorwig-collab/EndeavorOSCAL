# v0.1 fixture corpus

The manifest declares the minimum semantic cases for the first converter
vertical slice. The XML documents are deliberately synthetic and must be
schema-validated before they are committed. This avoids silently importing
vendor assessment results with unclear redistribution terms or sensitive
collected system data.

Each fixture must contain a generator, one evaluated definition, enough test
and system-characteristics context to make its result credible, and a paired
Definitions artifact. Tests must verify the emitted OSCAL document against the
contract and the pinned OSCAL schema.

`oscal-golden/` contains the canonical byte output for all six supported OVAL
result statuses. The test suite regenerates every artifact and compares it
byte-for-byte, so a mapping or serialization change is an explicit corpus
change rather than a silent behavior shift. Regenerate the corpus only after
reviewing such a contract change:

```bash
mkdir -p fixtures/oscal-golden
for fixture in pass fail unknown error not-applicable not-evaluated; do
  python3 -m endeavor convert \
    --results "fixtures/oval-results/${fixture}.xml" \
    --definitions fixtures/oval-definitions/definitions.xml \
    --output "fixtures/oscal-golden/${fixture}.json"
done
```

If a canonical OVAL Definitions file is vendored, record its exact source URL,
retrieval date, SHA-256, and license basis in this manifest. Do not vendor
third-party scan results without an explicit redistribution review.

The fixture source and licensing policy follows the
[OVAL FAQ](https://ovalproject.github.io/getting-started/faqs/) and the
[OVAL Community repository](https://github.com/OVAL-Community/OVAL).
