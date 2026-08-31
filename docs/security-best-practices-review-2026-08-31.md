# Security and compliance review - 2026-08-31

## Executive summary

This review covered the Python evidence adapter, shell tooling, GitHub Actions,
release controls, and disposable reviewer-VM documentation at commit
`cdca6d1`. No critical application-level command injection, XXE, unsafe
deserialization, or shell-injection path was found. The XML parser has strong
bounded, offline defaults and the release process has meaningful provenance
controls.

Two high-priority assurance gaps must be resolved before GA: the release job
installs third-party dependencies while holding publication credentials, and
the review VM runs downloads that are not integrity-pinned. These findings do
not change the current narrow product scope; they affect release and reviewer
assurance.

The project is not a hosted web application and has no Python web framework.
The available framework-specific security guidance was therefore not
applicable; this review used the repository's Python, shell, CI, OSCAL/SCAP,
and supply-chain controls.

## Findings

### SEC-01 - High: privileged release job installs dependencies

`.github/workflows/release.yml` grants `contents: write`, `id-token: write`,
and `attestations: write` to the release job before it runs `pip install` and
`npm ci` (lines 13-31 and 67-83). A compromised package or install hook could
run with publication capabilities.

Before GA, split validation/build into an unprivileged job. Publish and attest
only from a separate protected-environment job that receives the built,
checksummed artifacts. Set checkout `persist-credentials: false` in jobs that
do not push, and hash-pin Python build inputs.

### SEC-02 - High: verification VM downloads are not integrity-pinned

`scripts/launch-alpha-review-vm.sh` downloads the Alpine ISO without checksum
verification and clones noVNC by mutable tag before running `novnc_proxy`
(lines 70-74, 81-83, and 101). `scripts/prepare-alpha-review-vm.sh` can also
install current APK, PyPI, and npm content when caches are unavailable (lines
39-65).

Before a GA VM review, pin noVNC to an immutable commit/archive checksum,
verify the Alpine release checksum/signature, and use a hash-manifested offline
APK/wheel/npm cache. The current VM is intentionally inactive; do not treat it
as a reproducible GA environment until this is complete.

### SEC-03 - Medium: mapping targets can create schema-invalid output

Mapping parsers accept any nonempty target identifier
(`endeavor/mapping.py:69-104` and `endeavor/xccdf_mapping.py:43-55`), while
the CLI writes conversion output without runtime OSCAL-schema validation
(`endeavor/cli.py:132-175`). For example, an identifier containing a space can
be emitted then rejected by the bundled OSCAL TokenDatatype constraint.

Before GA, validate mapping target identifiers at intake and add a final
schema-validation gate before atomic output replacement. Retain a regression
test for invalid identifier syntax.

### SEC-04 - Medium: duplicate JSON keys are ambiguous mapping input

OVAL and XCCDF mapping parsers use default `json.loads`
(`endeavor/mapping.py:75-80` and `endeavor/xccdf_mapping.py:32-37`), which
silently accepts duplicate keys. The linkage-manifest parser correctly rejects
them (`endeavor/arf_linkage.py:46-52` and 90-97).

Before GA, reuse the duplicate-key rejection hook for every integrity-sensitive
JSON mapping input and add duplicate-key regression cases.

### SEC-05 - Medium: VM boundary and snapshot integrity

The previous VM guide described a fully isolated guest even though it has
user-mode outbound networking and a writable 9p review share. This handoff
updates `docs/alpha-test-vm-start-here.md` and
`docs/verification-vm-build-and-configuration.md` to describe the real
boundary. The VM wrapper now also detects an accidentally wrong or modified
workspace before validation.

This is not protection against a hostile root guest: a writable shared mount
cannot provide that. Before GA, use separate read-only candidate and narrowly
writable export shares, then validate all exported evidence on the host.

### SEC-06 - Low: malformed empty XCCDF can bypass stable diagnostics

A schema-valid XCCDF input with no `TestResult` can reach list indexing in
`endeavor/xccdf_convert.py:28` after inspection
(`endeavor/xccdf.py:132-140`), producing an uncaught `IndexError` rather than
the documented CLI diagnostic contract.

Before GA, reject zero-TestResult conversion input as an input error and add a
final sanitized internal-error handler with a regression test.

### SEC-07 - Low: reviewer identity is not independently authenticated

`scripts/validate-ga-release-readiness.py:97-109` requires a nonempty reviewer
identity but does not independently authenticate it. The planned independent
`main` reviewer/approval control remains unconfigured.

Before GA, name the reviewer and require protected-review approval, CODEOWNERS,
or a separately signed reviewer record for corpus and GA acceptance evidence.

## Positive controls verified

- Bounded XML size/element limits, DTD/entity rejection, no-network parsers,
  trusted vendored-schema resolution, and non-symlink inputs.
- Atomic output replacement with owner-only temporary files.
- Escaped HTML reporting and deterministic OSCAL serialization.
- SHA-pinned GitHub Actions, Dependency Review, CodeQL, OSV advisory scan,
  OpenSSF Scorecard, SBOM validation, fixed-seed parser fuzzing, and
  fail-closed vulnerability disposition.
- Protected `main` and `v*` tag rules, reproducible source builds, checksums,
  and GitHub keyless OIDC/Sigstore artifact attestations.

## Compliance interpretation

The review confirms that the documented GA boundary is appropriately narrow:
Endeavor preserves and converts evidence; OpenSCAP remains the evaluator. The
project should not make a platform, evaluator, remediation, legacy-RHEL, or
general SCAP-to-OSCAL compatibility claim beyond its admitted corpus and
versioned support policy. Corpus approvals must remain human, hash-bound, and
sanitization-reviewed.

## Recommended remediation order

1. SEC-01 and SEC-02 before any GA candidate or reviewer VM use.
2. SEC-03 and SEC-04 before accepting external mapping input for GA.
3. SEC-05 through SEC-07 during GA release-control preparation.
