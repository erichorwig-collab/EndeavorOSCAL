# Endeavor work state

Updated: 2026-08-29

## Active milestone

Secure validation boundary for v0.1 OVAL Results to OSCAL Assessment Results.

## Completed evidence

- OVAL 5.12.2 schema set is vendored under `endeavor/schemas/oval-5.12.2`.
- OSCAL Assessment Results 1.2.0 JSON Schema is vendored under
  `endeavor/schemas/oscal-1.2.0`; provenance and hashes are in
  `endeavor/schemas/MANIFEST.md`.
- `python-lxml` and `python-jsonschema` are installed on the host.
- All synthetic Definitions and six Results fixtures validate against the
  vendored OVAL 5.12.2 XSDs.
- Results and Definitions compile through static trusted wrapper schemas. The
  Results wrapper pins the core Results schema plus all 23 vendored platform
  Definitions and System Characteristics extensions; document-provided schema
  hints cannot extend or replace that graph.
- Twelve proof-of-concept `inspect`/`convert` tests pass, including hostile
  schema-hint, duplicate-identifier, and symlink-input rejection cases.
- Observations now preserve the evaluated target's OS name/version,
  architecture, primary host name, and the namespaces of observed platform
  system-characteristics extensions. No platform payload is interpreted as a
  control or finding.

## Important limits

- The parser supports only the v0.1 normalized Results data it extracts;
  platform content is deliberately represented only by extension presence.
- Python `jsonschema` on Python 3.14 cannot evaluate OSCAL 1.2.0's ECMA-262
  Unicode-property regular expressions. Project-local AJV 8.17.1 now provides
  the compatible OSCAL schema gate; maintain its lockfile and CI coverage.
- The v0.1 contract and implementation now explicitly pin OVAL 5.12.2.
- The parser accepts only generator core schema declarations `5.12` or
  `5.12.2`; it rejects other declared versions before conversion.

## Next safe task

Before enabling non-synthetic input, obtain representative real producer
fixtures with an explicit redistribution review. Then decide whether any
platform-specific details should be mapped into OSCAL observations. CI is
present and passed remotely on commit `12765e0` (GitHub Actions run
`33289162253`).

The official OpenSCAP repository is LGPL-2.1, but its inspected
`tests/API/OVAL/results-good.xml` fixture declares OVAL 5.5, outside this
v0.1 compatibility boundary, so it was not copied into this repository.

## Resume procedure

1. Read this file and `git status --short`.
2. Run `python3 -m unittest discover -s tests -v`.
3. Continue the next safe task. Preserve the proof-of-concept boundary until
   the parser and compatible OSCAL validator are validated.

## Waiting-work rule

If a future package, signature, or graphical authorization action awaits the
user, record it here and continue independent parser, fixture, documentation,
and test work. Never ask for or handle a password.
