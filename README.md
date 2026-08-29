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

## Status

Discovery and product definition. No production converter or release artifact exists yet.
