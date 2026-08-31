# General Availability readiness map

> Status: **not ready for GA**. `v0.1.0-alpha.1` is a verified prerelease and
> establishes the release foundation; it is not evidence of broad production
> support.

## Required product decision

Choose one support contract before implementing the GA gate:

1. **Narrow GA (recommended):** explicit-mapping OVAL Results + Definitions,
   plus the already documented XCCDF and linked-ARF provenance profiles. This
   retains the documented exclusions for ARF archive ingestion, embedded-OVAL
   conversion without authoritative linkage, tailoring-decision interpretation,
   and inferred control mappings.
2. **Broad SCAP/OSCAL GA:** the full product direction described in the README.
   This requires multi-producer XCCDF/ARF/OVAL interoperability coverage and
   implementation of each claimed output before GA.

The remainder of this map assumes the recommended narrow contract. Selecting
the broad contract expands, rather than replaces, these gates.

## GA blockers

| Gate | Required evidence | Current state |
| --- | --- | --- |
| Contractual support boundary | Versioned support policy naming input profiles, OpenSCAP/OVAL versions, operating platforms, non-goals, support period, and deprecation process | Implemented in `SUPPORT.md`; GA candidate must validate it against the compatibility matrix |
| GA-specific acceptance | A fresh named human and accessibility acceptance record for the exact `v0.1.0` tag candidate | Not started |
| Version-aware GA gate | CI verifies tag/package/version consistency, changelog, SBOM/license review, vulnerability disposition, accepted GA record, reproducible source, and post-publication verification for the exact release | Alpha-only checker is hard-coded to the alpha candidate |
| Main protection | Active `main` ruleset requiring a pull request and passing validation, while blocking deletion and force pushes | Implemented as GitHub ruleset `21899103`; the repository owner may bypass only through a pull request. A future independent reviewer will be added before requiring an approval threshold. |
| Untrusted-input assurance | Bounded parser/property fuzzing with regression retention and Python/JavaScript SAST on pull requests and `main` | Implemented: fixed-seed OVAL/XCCDF/ARF mutation regression runs in CI and release workflows; pinned CodeQL covers Python and JavaScript |
| Interoperability corpus | Sanitized, provenance-recorded fixtures from each supported producer/version profile and target-distro combination | Intake protocol is defined in `docs/ga-interoperability-corpus.md`; the required target-environment corpus is still incomplete |
| Installability | Wheel/sdist or equivalent supported distribution, install/upgrade/uninstall documentation, and clean-environment installed-CLI end-to-end test | Source archive only |
| Accessibility release gate | Automated report accessibility check and repeatable manual keyboard/screen-reader GA review | Static generated-report semantic checks run in the representative workflow; a fresh GA manual keyboard/screen-reader review remains required |
| Maintainer operations | CONTRIBUTING, support/EOL policy, maintainer/governance, incident/change-control, and release-note accessibility process | Contribution, support, conduct, and disclosure policies are present; GA release/change-control evidence remains required |

## Recommended GA controls

- Dependabot vulnerability alerts and automated security fixes are enabled;
  review and disposition alerts under the vulnerability-release gate.
- Make High/Critical dependency findings release-blocking unless covered by an
  exact, approved, expiring exception.
- Document whether GitHub OIDC artifact attestations are the GA trust mechanism
  or whether signed tags are additionally required.
- Require GitHub Actions SHA pinning in repository settings as well as in
  workflow source.
- Establish performance and resource-limit benchmarks for supported input
  sizes, then retain their results as regression evidence.

## Explicitly post-GA under the narrow contract

- OVAL 5.12/5.12.2 support.
- ARF archive/container ingestion.
- Embedded ARF OVAL conversion without authoritative Results-to-Definitions
  linkage.
- Tailoring-decision interpretation.
- Package-registry publication and broader OSCAL output types.

## Next action

Ratify the GA support contract, then implement the GA-specific gate and its
evidence in the order listed above. Do not relabel the alpha release as GA
until every blocker has a version-specific, reproducible record.
