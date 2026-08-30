# Changelog

All notable user-visible changes are recorded here. Endeavor follows the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) structure and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) once public releases
begin.

## [Unreleased]

## [0.1.0-alpha.1] - 2026-08-30

### Added

- Provenance-preserving OVAL, XCCDF, and bounded ARF evidence-adapter slices.
- Deterministic governance and alpha-workflow evidence manifests.
- Security policy, private vulnerability reporting, Dependabot, and advisory
  OpenSSF Scorecard and OSV vulnerability reporting.
- Tag-only GitHub Release workflow with deterministic source archive, CycloneDX
  SBOM, SHA-256 checksums, manifest, and GitHub artifact attestations.

### Security

- Pinned GitHub Actions to immutable commit identifiers.
- Updated AJV to 8.20.0 to address GHSA-2g4f-4pwh-qvx6.

### Known limitations

- The alpha supports the documented OVAL, XCCDF, and bounded ARF evidence
  profiles only. ARF archive ingestion, tailoring-decision interpretation, and
  unmapped source-to-OSCAL expansion remain out of scope.
- The release workflow is configured but no release tag or public release has
  been created. A named human acceptance record for the frozen candidate commit
  is still required.

## Release-entry rule

Before a release candidate is tagged, maintainers must replace `Unreleased`
with the proposed version and UTC date, summarize behavior changes and known
limits in plain language, and link relevant security advisories without
including exploit details.
