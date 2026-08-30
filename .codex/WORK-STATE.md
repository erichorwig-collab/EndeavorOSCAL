# Endeavor work state

Updated: 2026-08-29

## Active milestone

Validated OpenSCAP OVAL 5.11.3 evidence fixture and compatibility boundary.

## Completed evidence

- The selected 5.11.3 profile uses the exact Fedora 43/OpenSCAP 1.4.4 schema
  tree at `endeavor/schemas/oval/5.11.3`, plus its required shared schemas.
  The 5.12.2 schema set remains vendored as future-release compatibility work.
- OSCAL Assessment Results 1.2.0 JSON Schema is vendored under
  `endeavor/schemas/oscal-1.2.0`; provenance and hashes are in
  `endeavor/schemas/MANIFEST.md`.
- `python-lxml` and `python-jsonschema` are installed on the host.
- Six synthetic status fixtures and one generated-sanitized, genuine OpenSCAP
  Results + Definitions pair use the supported 5.11.3 generator declaration.
- Results and Definitions compile through static trusted wrapper schemas. The
  Results wrapper pins the core Results schema plus all 23 vendored platform
  Definitions and System Characteristics extensions; document-provided schema
  hints cannot extend or replace that graph.
- Thirteen proof-of-concept `inspect`/`convert` tests pass, including hostile
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
- The public v0.1 interoperability profile accepts only the 5.11.3 generator
  declaration, as produced by current OpenSCAP. The retained 5.12/5.12.2
  schema work is explicitly deferred to a future release.

## Next safe task

Decide whether any platform-specific details should be mapped into OSCAL
observations. CI is
present and passed remotely on commit `12765e0` (GitHub Actions run
`33289162253`).

The official OpenSCAP repository is LGPL-2.1, but its inspected
`tests/API/OVAL/results-good.xml` fixture declares OVAL 5.5, outside this
v0.1 compatibility boundary, so it was not copied into this repository.

Upstream fixture research is recorded in
`docs/v0.1-upstream-fixture-research.md`. No public OVAL 5.12/5.12.2 matching
Results-plus-Definitions pair was found. A project-authored, sanitized real
OpenSCAP 5.11.3 pair is now vendored under `fixtures/generated-sanitized`.

OpenSCAP 1.4.3 supports OVAL only through 5.11.3. The user explicitly selected
that version as the current compatibility profile; do not claim 5.12/5.12.2
interoperability until a future release validates it with a compatible producer
and dedicated regression corpus.

## Resume procedure

1. Read this file and `git status --short`.
2. Run `python3 -m unittest discover -s tests -v`.
3. Continue the next safe task. Preserve the proof-of-concept boundary until
   the parser and compatible OSCAL validator are validated.

## Waiting-work rule

If a future package, signature, or graphical authorization action awaits the
user, record it here and continue independent parser, fixture, documentation,
and test work. Never ask for or handle a password.
