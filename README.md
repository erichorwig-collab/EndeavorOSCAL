# Endeavor — OpenSCAP for OSCAL

Endeavor converts OpenSCAP assessment evidence into valid, provenance-preserving OSCAL artifacts. It is not a replacement SCAP/OVAL evaluator in its first release. OpenSCAP remains the execution engine; Endeavor makes its evidence useful in OSCAL assessment, authorization, continuous-monitoring, and remediation workflows.

## Product direction

- **Input:** OpenSCAP XCCDF/OVAL results, ARF collections, OVAL Definitions/Results, tailoring files, and optional control mappings.
- **Output:** Valid OSCAL Assessment Results, with optional companion Assessment Plan, POA&M candidates, and original SCAP artifacts in back matter.
- **Principle:** Never imply that an OSCAL finding is re-executable OVAL logic. Preserve the source artifact, schema/version, hashes, evaluator version, and result identifiers.
- **First users:** security engineers and GRC/authorization teams who run OpenSCAP today and must share assessment evidence in OSCAL.

## Documentation

- [OpenSCAP user experience and feature inventory](docs/openscap-user-experience.md)
- [OSCAL parity and improvement design](docs/oscal-experience-design.md)
- [Quality, security, and accessibility strategy](docs/quality-and-accessibility.md)
- [v0.1 OVAL Results to OSCAL mapping contract](docs/v0.1-oval-results-mapping.md)
- [v0.1 fixture corpus contract](fixtures/README.md)
- [v0.1 implementation architecture](docs/v0.1-implementation-architecture.md)
- [v0.1 upstream fixture research and intake requirements](docs/v0.1-upstream-fixture-research.md)

## Status

An executable v0.1 proof-of-concept is available for synthetic OVAL 5.12.2
Results and Definitions fixtures. It provides `inspect` and `convert`, exact
source-status preservation, SHA-256 evidence references, deterministic JSON,
and focused malformed-input tests. It validates OVAL with pinned local XSD
wrappers; its test suite validates emitted OSCAL with pinned AJV. It is not yet a
production converter: its fixture corpus is synthetic and platform-specific
content is represented only by safe target-identity and extension-presence
provenance, not semantically mapped into controls or findings.

## Try the vertical slice

```bash
python3 -m endeavor inspect \
  --results fixtures/oval-results/fail.xml \
  --definitions fixtures/oval-definitions/definitions.xml

python3 -m endeavor convert \
  --results fixtures/oval-results/fail.xml \
  --definitions fixtures/oval-definitions/definitions.xml \
  --output /tmp/endeavor-assessment-results.json
```

Run the focused test suite with `python3 -m unittest discover -s tests -v`.
