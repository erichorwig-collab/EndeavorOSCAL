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
| Dependency inventory consistency | `sbom.cdx.json`, checked by `scripts/generate-sbom.py --check` |
| Human alpha acceptance | `docs/alpha-acceptance-record-2026-08-30.md` |
| Tested support boundaries | `docs/compatibility-matrix.md` |

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
