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
| Human alpha acceptance | `docs/alpha-acceptance-record-2026-08-30.md` |
| Tested support boundaries | `docs/compatibility-matrix.md` |

## Standards-aligned baseline

| Control | Status | Evidence / boundary |
| --- | --- | --- |
| Secure development process | Implemented baseline | NIST SSDF-aligned source validation, reproducible test/SBOM checks, and documented disclosure process; this is not an SSDF certification. |
| Vulnerability disclosure | Implemented | `SECURITY.md` and GitHub private vulnerability reporting; no public vulnerability details. |
| Dependency update visibility | Implemented advisory | `.github/dependabot.yml` opens reviewable update pull requests for Actions, npm, and pip; it does not auto-merge. |
| Supply-chain posture visibility | Implemented advisory | `.github/workflows/scorecard.yml` runs the official OpenSSF Scorecard workflow weekly and on `main`, retains SARIF for five days, and uploads it to code scanning. CI actions are pinned to full commit SHAs. No score threshold is a merge or release gate. |
| Software inventory | Implemented | Deterministic CycloneDX 1.5 `sbom.cdx.json`, checked in CI. |
| Release provenance | Deferred | Signing and SLSA provenance await a release-artifact and publication policy. |

## Explicitly deferred from this gate

- ARF archive/container ingestion remains rejected until formats and resource
  limits are approved.
- Tailoring provenance is retained, but Endeavor does not interpret tailoring
  decisions.
- Cross-format conversion remains limited to the documented, explicitly mapped
  sources; it must not infer findings or controls.
- Vulnerability scanning remains advisory until a scanner and exception process
  are selected.
- Release signing, reproducible builds, license review, changelog, and
  accessible release notes remain public-release controls.

See [the quality strategy](quality-and-accessibility.md) and
[dependency policy](dependency-policy.md) for those release controls.
