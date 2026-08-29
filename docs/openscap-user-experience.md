# OpenSCAP user experience and feature inventory

## Typical user journey

OpenSCAP is primarily a CLI-first assessment workflow. A practitioner acquires SCAP content, discovers available benchmarks/profiles, selects or tailors a profile, executes an assessment against a local or remote target, reviews a machine-readable result plus HTML report, and optionally generates or applies remediation.

```text
content source -> oscap info -> profile/tailoring -> oscap evaluation
              -> XCCDF/OVAL/ARF evidence + HTML report -> triage/remediation -> re-scan
```

This workflow is efficient for an experienced Linux operator: one command can create a report and ARF bundle, but the user must understand SCAP content identifiers, output artifact choices, privilege boundaries, and remediation risk.

## Personas and jobs to be done

| Persona | Job | Primary friction today |
| --- | --- | --- |
| Security engineer | Assess a system against a selected benchmark/profile | Discovering the right datastream, profile, values, and output flags. |
| Content author | Create/test XCCDF and OVAL checks | Validating semantics across platforms and separating source content from results. |
| Compliance analyst | Explain pass/fail evidence to an assessor | ARF/XCCDF/OVAL are rich but difficult to consume outside SCAP tooling. |
| Platform engineer | Scan fleets or images repeatedly | Remote/offline/container targeting, scheduling, aggregation, and stable automation contracts. |
| System owner | Remediate failed controls safely | Distinguishing proposed fixes, applied fixes, validation, and exceptions. |

## Feature inventory

| Capability | Typical OpenSCAP experience | Artifacts / controls | Endeavor relevance |
| --- | --- | --- | --- |
| Content discovery | `oscap info` lists datastreams, benchmarks, profiles, components, and metadata. | SCAP source datastream, XCCDF, OVAL | Preserve source identities and expose a human-readable inventory. |
| Content validation | Schema and content validation before evaluation; users may skip validation only deliberately. | XCCDF, OVAL, CPE, SCAP datastream | Treat validation outcome as evidence, never silently accept invalid input. |
| Profile selection | `oscap xccdf eval --profile …`; profile IDs are often opaque. | XCCDF profile | Map selected profile and tailored values to OSCAL profile/control context. |
| Tailoring | SCAP Workbench or `autotailor` selects rules and values without modifying baseline content. | XCCDF tailoring file | Model tailoring decisions/provenance explicitly; retain original tailoring file. |
| Local assessment | `oscap xccdf eval` runs checks and reports per-rule status. | XCCDF Results, optional OVAL Results | Convert results, not undocumented interpretation. |
| Standalone OVAL | `oscap oval eval` evaluates definitions; `oval collect` collects system characteristics. | OVAL Definitions, Results, System Characteristics | Phase-one source type for OVAL-to-OSCAL evidence conversion. |
| CPE applicability | Content uses CPE and applicable-platform logic to determine scope. | CPE dictionaries, OVAL/XCCDF metadata | Record applicability decisions and inputs; do not flatten `notapplicable` into pass. |
| Rich evidence | `--results`, `--oval-results`, `--results-arf`, and `--report` produce different evidence/report forms. | XCCDF, OVAL, ARF, HTML | Offer explicit evidence bundles and output selection. |
| Reporting | Static HTML reports and command output support local review. | HTML, stdout/stderr | Generate accessible reports from OSCAL rather than opaque format dumps. |
| Remediation | `--remediate` applies attached fixes; `generate fix` supports review-first scripts. | XCCDF fix, remediation output, re-scan results | Separate recommended, approved, executed, and verified remediation states. |
| Offline/remote targets | `oscap-chroot`, `oscap-ssh`, `oscap-vm`, and `oscap-docker` cover mounted filesystems, SSH, VMs, and containers. | Target metadata, ARF/results | Normalize target identity and assessment asset metadata. |
| Automation | CLI exit status, stable files, optional daemon/scheduling ecosystem. | Files, logs, task history | Provide deterministic CLI JSON, idempotent conversion, and CI-friendly exit codes. |

## OpenSCAP experience principles worth retaining

1. **Content-first, explicit execution.** Users choose exactly what content/profile runs.
2. **Offline-capable operation.** Collection and evaluation can be performed without a centralized service.
3. **Evidence-rich output.** ARF/OVAL result detail makes decisions auditable.
4. **Automation-first CLI.** Human output is useful, but files and return codes are stable integration points.
5. **Reviewable remediation.** Generated fixes enable review before execution.

## Pain points Endeavor should solve

- Multiple SCAP artifact types obscure which file is authoritative for a given question.
- Profile, tailoring, target, evaluator, and result provenance are hard to correlate across runs.
- A fail result is not naturally connected to OSCAL controls, findings, risks, or POA&M work.
- HTML reports are convenient but not structured, accessible evidence exchanges.
- Fleet comparison requires custom ARF parsing and schema-specific tooling.

## Source basis

- [OpenSCAP User Manual](https://static.open-scap.org/openscap-1.4.1/oscap_user_manual.html)
- [OpenSCAP `oscap-ssh` supported commands](https://github.com/OpenSCAP/openscap/blob/main/utils/oscap-ssh)
- [OpenSCAP daemon capabilities](https://github.com/OpenSCAP/openscap-daemon)
