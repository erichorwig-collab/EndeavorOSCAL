# OSCAL parity and improvement design

## Product boundary

Endeavor is an **evidence adapter**:

```text
OpenSCAP execution -> SCAP evidence bundle -> Endeavor normalization/mapping
                   -> OSCAL Assessment Results -> findings, risks, POA&M candidates
```

It does not initially reimplement OpenSCAP probes, XCCDF evaluation, OVAL evaluation, or remediation execution. This protects semantic fidelity and keeps responsibility clear.

## OSCAL representation

| OpenSCAP concept | Endeavor OSCAL representation | Fidelity rule |
| --- | --- | --- |
| Benchmark/profile/tailoring | Imported OSCAL profile plus back-matter links to original SCAP artifacts | Do not invent a control mapping; require a supplied mapping or mark it unmapped. |
| Scan configuration and target | Assessment Plan activities, subjects, assets, and metadata | Preserve command line, evaluator version, timestamps, target IDs, and privilege context. |
| Rule/definition result | Observation and, when mapped, Finding in Assessment Results | Preserve raw status and source identifier as properties. |
| OVAL system characteristics | Evidence resource / linked attachment | Hash and link it; do not flatten sensitive collected values into generic prose. |
| Fail/error/unknown/not-applicable | Source-status property plus outcome mapping | `notapplicable`, `notchecked`, `unknown`, and `error` remain distinct. |
| Remediation script/output | Proposed or executed remediation task and evidence | Require explicit execution status; never describe generated script as applied. |
| Repeat scan | Separate result UUID/version, with stable source and target correlations | Make changes and regressions queryable. |

OSCAL Assessment Results must reference an Assessment Plan and can express observations, findings, risks, remediation, and back-matter evidence. [NIST Assessment Results model](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/)

## Parity experience

| OpenSCAP action | Endeavor command / UI experience | OSCAL output |
| --- | --- | --- |
| Inspect content | `endeavor inspect scap-content.xml` | Source inventory and validation report; no conversion implied. |
| Run scan | Keep `oscap` execution external in v1; optionally orchestrate later. | Captured run manifest and source evidence. |
| Review profile/tailoring | `endeavor explain profile …` and accessible report | Mapped controls, tailoring deltas, unmapped source IDs. |
| Convert results | `endeavor convert --arf … --mapping … --assessment-plan …` | Assessment Results JSON by default; XML/YAML on request. |
| Review failures | `endeavor findings` / web report | Findings linked to observations, controls, source evidence, and risk/POA&M candidates. |
| Compare runs | `endeavor diff previous-ar.json current-ar.json` | Stable delta report keyed by target, source ID, and control mapping. |
| Generate remediation | `endeavor remediate plan` only in v1 | OSCAL remediation proposals; no execution. |

## Improvements enabled by OSCAL

1. **End-to-end context.** Link a result to an assessment plan, system implementation, selected profile, and control catalog rather than shipping a stand-alone scan report.
2. **First-class governance.** Promote mapped failures into findings, risks, and POA&M candidates without lossy spreadsheet translation.
3. **Provenance and reproducibility.** Include SHA-256 hashes, source schema versions, evaluator version, command manifest, and evidence-resource links.
4. **Multi-format interchange.** Emit OSCAL JSON, XML, and YAML from one normalized model while retaining raw SCAP evidence.
5. **Fleet and time-series comparisons.** Provide deterministic IDs and explicit target identity so continuous-monitoring deltas are reliable.
6. **Privacy-aware evidence.** Support redaction policies and detached/encrypted evidence references for system characteristics that contain sensitive paths, accounts, or package inventories.
7. **Safer remediation lifecycle.** Keep generation, approval, execution, and verification separate; turn only verified work into closed remediation evidence.
8. **Accessible human review.** Produce semantic HTML reports with clear status explanations and machine-readable downloads.

## Non-goals for v1

- Generic, lossless translation of arbitrary executable OVAL logic into native OSCAL.
- Replacing OpenSCAP as an OVAL/XCCDF evaluator.
- Automatic remediation execution.
- Claims of conformance beyond schema validation and documented, versioned test coverage.

## Recommended release slices

1. **v0.1:** OVAL Results + source Definitions to OSCAL Assessment Results; provenance and validation.
2. **v0.2:** ARF/XCCDF result ingestion, mapping files, accessible HTML report, and run diffs.
3. **v0.3:** Assessment Plan generation, POA&M candidates, signed evidence manifests, and CI integration.
4. **v1.0:** Stable CLI/API, published mapping specification, reproducible corpus, and supported migration guides.
