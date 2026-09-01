# Security and compliance review - 2026-08-31

## Executive summary

This review covered the Python evidence adapter, shell tooling, GitHub Actions,
release controls, and disposable reviewer-VM documentation. This remediation
update records the state after the high-priority code changes on the associated
protected pull request. No critical application-level command injection, XXE, unsafe
deserialization, or shell-injection path was found. The XML parser has strong
bounded, offline defaults and the release process has meaningful provenance
controls.

Publication privileges are now separated from dependency installation, and the
VM launcher verifies its Alpine ISO and noVNC source before use. A
hash-manifested offline guest dependency cache and a separate read-only source
mount remain pre-GA assurance work. These findings do not change the current
narrow product scope; they affect release and reviewer assurance.

The project is not a hosted web application and has no Python web framework.
The available framework-specific security guidance was therefore not
applicable; this review used the repository's Python, shell, CI, OSCAL/SCAP,
and supply-chain controls.

## Findings

### SEC-01 - High: privileged release job installs dependencies — mitigated

`.github/workflows/release.yml` grants `contents: write`, `id-token: write`,
and `attestations: write` to the release job before it runs `pip install` and
`npm ci` (lines 13-31 and 67-83). A compromised package or install hook could
run with publication capabilities.

The release workflow now builds and validates with only `contents: read` and a
non-persistent checkout credential. It transfers the immutable build artifact
by artifact ID to the `release` environment, where a separate job verifies the
file boundary, SHA-256 manifest, version, and source commit before it attests
and publishes. The privileged job performs no checkout, dependency install,
or repository-script execution. Python requirement hashes remain a defense in
depth supply-chain task, but the publication-token exposure is mitigated.

### SEC-02 - High: verification VM downloads are not integrity-pinned — mitigated

`scripts/launch-alpha-review-vm.sh` downloads the Alpine ISO without checksum
verification and clones noVNC by mutable tag before running `novnc_proxy`
(lines 70-74, 81-83, and 101). `scripts/prepare-alpha-review-vm.sh` can also
install current APK, PyPI, and npm content when caches are unavailable (lines
39-65).

The launcher now verifies Alpine `3.24.0` ISO SHA-256
`6cd1a38ae05cf96a5d0cbb2ddd6c630834babfeca1ecc5d1f05ec0b06b886102`
before QEMU uses it and rejects noVNC unless tag `v1.6.0` resolves to immutable
commit `a8dfd6a3ea3c74244f5ebdaa5a7f1023007a7820`. Before a GA VM review,
uses a required cache bundle whose metadata binds the frozen candidate and the
requirements/package-lock hashes, and validates every cache file by SHA-256.
Strict mode does not configure a guest network device and uses offline APK,
pip, and npm operations. The explicit legacy online mode is labeled
non-GA-only. The current VM remains intentionally inactive.

### SEC-03 - Medium: mapping targets can create schema-invalid output — resolved

Mapping parsers accept any nonempty target identifier
(`endeavor/mapping.py:69-104` and `endeavor/xccdf_mapping.py:43-55`), while
the CLI writes conversion output without runtime OSCAL-schema validation
(`endeavor/cli.py:132-175`). For example, an identifier containing a space can
be emitted then rejected by the bundled OSCAL TokenDatatype constraint.

Both mapping parsers now reject a target ID unless it meets OSCAL's XML NCName
TokenDatatype constraint before conversion begins. Regression tests cover an
identifier containing a space. The bundled schema validation remains part of
the release workflow.

### SEC-04 - Medium: duplicate JSON keys are ambiguous mapping input — resolved

OVAL and XCCDF mapping parsers use default `json.loads`
(`endeavor/mapping.py:75-80` and `endeavor/xccdf_mapping.py:32-37`), which
silently accepts duplicate keys. The linkage-manifest parser correctly rejects
them (`endeavor/arf_linkage.py:46-52` and 90-97).

OVAL, XCCDF, and linkage-manifest JSON now use one duplicate-member rejecting
object hook. Regression tests cover both mapping formats.

### SEC-05 - Medium: VM boundary and snapshot integrity — mitigated

The VM now uses a read-only candidate 9p mount and a separate, empty writable
export mount. Strict mode has no guest network device. The VM wrapper also
detects an accidentally wrong or modified workspace before validation.

Raw output is still guest-produced, but the launcher now creates a trusted,
candidate-bound expected artifact manifest before the guest starts. After the
guest is stopped, the host verifier accepts only the exact three expected
regular files, rechecks hashes and report accessibility, and copies verified
bytes to a new host-owned directory. Do not open raw guest export.

### SEC-06 - Low: malformed empty XCCDF can bypass stable diagnostics — resolved

A schema-valid XCCDF input with no `TestResult` can reach list indexing in
`endeavor/xccdf_convert.py:28` after inspection
(`endeavor/xccdf.py:132-140`), producing an uncaught `IndexError` rather than
the documented CLI diagnostic contract.

Inspection now rejects zero-TestResult input before conversion reaches list
indexing. A regression test confirms the JSON diagnostic contract, no
traceback, and no output artifact.

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

1. Complete SEC-07 by naming the independent reviewer and requiring the
   corresponding GitHub environment or protected-review approval.
