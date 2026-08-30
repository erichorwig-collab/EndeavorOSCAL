# Evidence handling and redaction boundary

The v0.1 OVAL adapter treats all supplied XML as potentially sensitive
assessment evidence. It is a local converter, not an evidence store or
telemetry service.

## Default behavior

- It reads only local regular, non-symlink XML files and does not upload them.
- It writes a derived OSCAL Assessment Results document only when conversion
  succeeds; it does not embed raw OVAL XML.
- Derived back-matter links contain a safe basename and a SHA-256 integrity
  value. They do not contain the caller's absolute path.
- Handled diagnostics contain a role-safe filename only. They never echo XML
  content, evaluator messages, paths, secrets, or source bytes.
- Temporary output files have mode `0600` while being atomically written, and
  are removed if the write fails.

`inspect` intentionally exposes the supported generator metadata, definition
IDs, statuses, SHA-256 values, and safe filenames. Treat its JSON as
assessment metadata: keep it in the same access boundary as the converted
output.

## Operator responsibilities

- Provide inputs from an approved evidence location and select an output
  location with the required access controls and retention policy.
- Do not commit real assessment results, raw Definitions, converted results,
  or CLI logs to this repository unless their redistribution and sanitization
  have been reviewed.
- Use the synthetic corpus or the documented sanitized OpenSCAP pair for CI.
  The generated-fixture provenance file records its transformations and source
  checksums.
- Before any future raw-evidence embedding or remote reporting feature, add an
  explicit opt-in, data classification, retention/deletion rule, and tests for
  sensitive-log redaction. That is outside v0.1.

These rules complement the stable diagnostic behavior in the
[CLI contract](v0.1-cli-contract.md) and are tested for absolute-path and raw
DOCTYPE-content exclusion.
