# Governance readiness evidence

> Status: **ready to begin Governance planning**. This is not production-release approval.

This record collects the bounded evidence available after alpha acceptance. Run
the deterministic checker from the repository root:

```bash
python3 scripts/validate-governance-readiness.py
```

The JSON output hashes each input evidence document. It succeeds only when the
named alpha record is present and explicitly accepted. CI runs the checker after
the source tests, SBOM comparison, and representative alpha workflow.

## Completed gates

| Gate | Evidence |
| --- | --- |
| Source parsing, mapping, hostile-input, and schema validation | `tests/test_vertical_slice.py` |
| Representative mapped-evidence workflow | `scripts/validate-alpha-workflow.py` |
| Retained alpha execution manifest | CI artifact `alpha-workflow-manifest` (30-day retention) |
| Dependency inventory consistency | `sbom.cdx.json`, checked by `scripts/generate-sbom.py --check` |
| Human alpha acceptance | `docs/alpha-acceptance-record-v0.1.0-alpha.1.md` (candidate `83352a59db5ba2dfc4e64e65d23e6e4e01263ce5`) |
| Tested support boundaries | `docs/compatibility-matrix.md` |

## Standards-aligned baseline

| Control | Status | Evidence / boundary |
| --- | --- | --- |
| Secure development process | Implemented baseline | NIST SSDF-aligned source validation, reproducible test/SBOM checks, and documented disclosure process; this is not an SSDF certification. |
| Vulnerability disclosure | Implemented | `SECURITY.md` and GitHub private vulnerability reporting; no public vulnerability details. |
| Dependency update visibility | Implemented advisory | `.github/dependabot.yml` opens reviewable update pull requests for Actions, npm, and pip; it does not auto-merge. |
| Dependency vulnerability gate | Implemented | `.github/workflows/dependency-review.yml` rejects newly introduced high/critical vulnerabilities; exceptions are exact, approved, expiring records. |
| Independent vulnerability inventory | Implemented advisory | `.github/workflows/osv-scanner.yml` runs weekly/manual OSV scans and uploads SARIF without making database drift a merge gate. |
| Supply-chain posture visibility | Implemented advisory | `.github/workflows/scorecard.yml` runs the official OpenSSF Scorecard workflow weekly and on `main`, retains SARIF for five days, and uploads it to code scanning. CI actions are pinned to full commit SHAs. No score threshold is a merge or release gate. |
| Software inventory | Implemented | Deterministic CycloneDX 1.5 `sbom.cdx.json`, checked in CI. |
| Release provenance | Implemented and exercised | The protected `v0.1.0-alpha.1` tag produced a Git source archive, SBOM, manifest, SHA-256 checksums, and GitHub artifact attestations. Independent verification is recorded in `docs/release-verification-v0.1.0-alpha.1.md`. |

## Explicitly deferred from this gate

- ARF archive/container ingestion remains rejected until formats and resource
  limits are approved.
- Tailoring provenance is retained, but Endeavor does not interpret tailoring
  decisions.
- Cross-format conversion remains limited to the documented, explicitly mapped
  sources; it must not infer findings or controls.
- Accessible release notes remain a public-release control.

## Release evidence baseline

Only a `v*` tag can invoke the publication workflow. It re-runs the validation
suite against the frozen commit, builds the source archive twice with Git,
requires byte equality, then publishes the source archive, SBOM, manifest, and
SHA-256 checksums through GitHub Releases. GitHub artifact attestations provide
keyless OIDC/Sigstore provenance for those release assets. A release is not
authorized merely because this workflow exists: the candidate checklist still
requires tag protection, a human acceptance record for the exact candidate
commit, and independent checksum/attestation verification.

See [the quality strategy](quality-and-accessibility.md) and
[dependency policy](dependency-policy.md) for those release controls.
Use [the release-candidate checklist](release-candidate-checklist.md) to turn
this readiness evidence into a reviewed candidate without implicitly approving
the deferred publication decisions.
