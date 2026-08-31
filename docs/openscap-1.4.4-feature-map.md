# Endeavor and OpenSCAP 1.4.4 feature map

> Status: **product-gap map, not an OpenSCAP compatibility claim**. It compares
> Endeavor with the OpenSCAP 1.4.4 command-line capabilities verified in the
> pinned Rocky Linux 10.2 evaluator. OpenSCAP remains Endeavor's evaluation
> oracle; parity in evidence exchange must not be represented as parity in SCAP
> execution.

## Capability status

| OpenSCAP 1.4.4 capability | Endeavor status | Current Endeavor evidence / command | Product decision |
| --- | --- | --- | --- |
| Discover SCAP file metadata (`oscap info`) | Partial | `inspect`, `inspect-xccdf`, `inspect-arf`, and `inspect-evidence` inventory supported source artifacts | Expand into a unified content inventory only after source-datastream intake is supported. |
| Validate XCCDF, OVAL, CPE, source/result datastreams | Partial | Pinned OVAL/XCCDF/ARF schemas; hostile-input rejection and OSCAL validation | Preserve source-validation outcome. Do not reimplement full SCAP validation as a GA prerequisite. |
| Evaluate XCCDF profiles and OVAL checks | Not implemented by design | Endeavor ingests the resulting evidence | Remains an OpenSCAP responsibility. Replacing an evaluator requires an independent product/security program. |
| Collect OVAL system characteristics | Not implemented by design | OVAL Results/Definitions provenance and status preservation | Defer; collect operations need privileged platform probes and a separate trust model. |
| Analyse supplied OVAL system characteristics | Not implemented by design | None | Defer with evaluator work; it is not evidence conversion. |
| Resolve XCCDF content and export OVAL variables | Not implemented | Tailoring/profile references are retained as provenance in XCCDF/ARF paths | Future content-authoring/interoperability track. |
| Profile selection and tailoring | Provenance-only | XCCDF inventory and authored ARF linkage manifest | Tailoring-decision interpretation remains deferred; never infer decisions. |
| Generate XCCDF/OVAL HTML reports and guides | Partial, improved | `report` produces an accessible mapping-coverage HTML report | Continue accessible OSCAL-native reporting; do not duplicate OpenSCAP guides before content execution exists. |
| Generate or apply remediation | Not implemented by design | None | Explicitly deferred. Any future remediation must separate recommendation, approval, execution, and re-verification. |
| Emit XCCDF Results, OVAL Results, and ARF | Consumes supported forms | `inspect*`, `convert*`, explicit mapping reports | Add platform corpus coverage before broadening formats; ARF archive ingestion and unresolved embedded OVAL remain excluded. |
| Convert SCAP evidence to interoperable assessment records | Implemented, adapter-specific | Schema-valid OSCAL Assessment Results, deterministic JSON, source hashes and back-matter evidence | Endeavor improvement: preserve explicit mapping visibility and avoid inferred controls/findings. |
| Produce OSCAL findings / POA&M workflow inputs | Partial | Explicit OVAL/XCCDF mappings and findings report | Expand only through documented mappings; no automatic remediation or control inference. |
| Compare assessment output | Implemented, adapter-specific | `diff` with deterministic OSCAL Assessment Results | Expand to cross-run, cross-target comparison after corpus admission. |
| Local target execution | Not implemented by design | None | OpenSCAP-owned; Endeavor supports its output files. |
| Mounted filesystem / SSH / VM / container target helpers | Not implemented by design | None | Future integration layer, after a threat model and separate target-access controls. |
| Daemon scheduling, fleet scanning, task history | Not implemented | None | Future operations/integration track; use existing OpenSCAP automation as the producer initially. |
| Library, SWIG bindings, Python API | Not implemented | Python adapter API is internal/package-oriented, not an OpenSCAP library replacement | Defer unless consumers require embedded SCAP execution. |
| Platform coverage | In progress | Planned Rocky Linux 10.2 and Ubuntu 24.04 LTS container corpus | Admit only after generated/sanitized fixtures, goldens, and acceptance evidence are committed. |

## What “all OpenSCAP features” would require

Achieving full parity is a separate product, not an incremental extension of
the current adapter. It would require:

1. A maintained SCAP execution engine for XCCDF, OVAL, CPE, datastream
   resolution, variable handling, and result generation.
2. Privileged local, chroot, SSH, VM, and container target-access models,
   including credential, host-key, isolation, logging, and failure handling.
3. Safe remediation lifecycle controls and re-evaluation semantics.
4. Content-authoring, tailoring, guide, fix-script, report, scheduling, and
   library/API compatibility commitments.
5. A test matrix for every supported target architecture, operating-system
   family, content format, and security-sensitive probe.

That work would alter Endeavor's security boundary and must be separately
designed, threat-modeled, and governed. It is not a safe condition for the
first GA evidence-adapter release.

## Recommended release sequence

1. **Narrow GA:** retain the evidence-adapter boundary; admit the Rocky 10.2
   and Ubuntu 24.04 LTS corpus; complete version-specific acceptance and draft
   release verification.
2. **Evidence breadth:** add remaining source formats and platform corpora,
   beginning with Fedora, Debian, and SUSE-family inputs, without evaluating
   targets.
3. **OpenSCAP integration:** add an opt-in producer wrapper that invokes a
   separately installed OpenSCAP, retains command/provenance, and passes its
   outputs through Endeavor. It must not apply remediation.
4. **Execution parity assessment:** only after the integration path has a
   mature threat model should the project decide whether to implement any
   evaluator, target-access, or remediation capability.

## Source basis

- OpenSCAP 1.4.4 `oscap --help`, `oscap xccdf --help`, `oscap oval --help`,
  `oscap ds --help`, and `oscap cpe --help`, captured in the pinned Rocky
  Linux evaluator described in [the GA platform-corpus plan](ga-platform-corpus-plan.md).
- [OpenSCAP 1.4.4 release](https://github.com/OpenSCAP/openscap/releases/tag/1.4.4)
- [OpenSCAP user experience inventory](openscap-user-experience.md)
