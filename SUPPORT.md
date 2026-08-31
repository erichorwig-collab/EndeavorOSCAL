# Endeavor support policy

## GA support boundary

The first Generally Available Endeavor release supports the **narrow GA
profile** only:

- OVAL Results paired with OVAL Definitions, using OVAL 5.11 or 5.11.3;
- XCCDF 1.2.1 Results from OpenSCAP 1.4.4, for provenance inventory and
  explicitly mapped conversion; and
- ARF 1.1 from OpenSCAP 1.4.4 when a local XCCDF report is resolved or an
  authoritative linkage manifest resolves OVAL Results to Definitions.

The exact tested fixtures, commands, and limits are the
[compatibility matrix](docs/compatibility-matrix.md). OpenSCAP remains the
evaluation engine. Endeavor does not claim to evaluate SCAP content or infer
controls, findings, remediation, or tailoring decisions.

## Explicit non-goals

- OVAL 5.12 and 5.12.2;
- ARF archive/container ingestion;
- embedded ARF OVAL conversion without authoritative Results-to-Definitions
  linkage;
- tailoring-decision interpretation; and
- remote artifact dereferencing, remediation execution, and package-registry
  distribution.

Unsupported inputs must fail safely or remain provenance-only as documented;
they must not be represented as supported semantic conversion.

## Support lifecycle

The current GA minor line receives security fixes and critical correctness
fixes until the next GA minor line is released, and for at least 90 days after
that successor release. Supported versions are listed in `SECURITY.md`.

Deprecations are announced in release notes and the compatibility matrix at
least one minor release, or 90 days, before removal. A security or data-loss
emergency may require a shorter notice; the release notes will explain why.

## Getting help

Use GitHub Issues for reproducible bugs and supported-input questions. Include
the Endeavor version, command, sanitized input characteristics, and exact
diagnostic output. Do not attach sensitive assessment evidence to public
issues. Report vulnerabilities through GitHub private vulnerability reporting
as described in `SECURITY.md`.
