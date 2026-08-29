# Quality, security, and accessibility strategy

## Testing strategy

| Layer | Required tests | Acceptance signal |
| --- | --- | --- |
| Parsing | Valid and malformed OVAL, XCCDF, ARF, and OSCAL fixtures | Strict rejection with actionable location/error; no partial silently trusted output. |
| Semantic mapping | Golden fixtures for pass/fail/error/unknown/not-applicable/notchecked, variables, tailoring, and multiple targets | Stable OSCAL output and explicit source-status preservation. |
| Schema | OVAL/XCCDF/ARF source validation where schemas are available; OSCAL schema and CLI validation | Every emitted artifact validates against its declared OSCAL version. |
| Provenance | Hash, source-link, timestamp, evaluator-version, and command-manifest tests | Evidence can be traced from each OSCAL observation to its source artifact. |
| Determinism | Same input, mapping, and clock/UUID strategy | Byte-stable canonical output or documented expected UUID/time differences. |
| Security | Malformed XML, entity-expansion, path traversal, archive-bomb, unsafe URI, and secret-redaction tests | Secure parser configuration; bounded resource use; no external retrieval by default. |
| Compatibility | Supported OpenSCAP versions, OVAL schema versions, OSCAL versions, and target distro fixtures | Published compatibility matrix and CI coverage. |
| CLI | Exit-code, JSON output, noninteractive, and stderr-contract tests | Automation does not need to scrape human text. |

## Accessibility baseline

WCAG applies to Endeavor's web reports, documentation site, and any interactive web UI; it does not replace CLI accessibility requirements. The initial target is **WCAG 2.2 Level AA** for every shipped web surface.

### Web/report requirements

- Semantic headings, landmarks, tables with headers, form labels, and meaningful link text.
- Complete keyboard operation, visible focus, logical focus order, and no pointer-only action.
- Text and status indicators meet contrast requirements; never rely only on color for pass/fail/error.
- Accessible names and live announcements for conversion progress and validation errors.
- Responsive reflow at 320 CSS pixels; no information loss at 200% zoom.
- Error messages identify the artifact, location, cause, and recovery action without exposing sensitive content.
- Automated axe-core checks plus manual keyboard and screen-reader smoke tests in CI/release review.

### CLI and documentation requirements

- Plain-text, pipe-safe output; `--format json`; no color by default when stdout is non-TTY; `--no-color` always available.
- Stable headings and concise diagnostics suitable for screen readers and logs.
- Examples include expected result status and recovery paths.
- Documentation uses semantic Markdown/HTML and publishes accessible HTML, not image-only diagrams.

## Security and privacy defaults

- Treat every input artifact as untrusted.
- Disable network retrieval and external XML entities by default; require an explicit allow-list flag for remote resources.
- Bound decompression size, XML depth, artifact count, and processing time.
- Redact secrets and personally sensitive system characteristics in human logs; retain raw evidence only under an explicit storage policy.
- Sign release artifacts, publish checksums and SBOMs, and record dependency provenance.
- Separate read-only conversion from any future remediation execution workflow.

## Publication quality gate

Before each public release: schema validation, golden corpus, fuzz/regression suite, dependency scan, SBOM, license review, changelog, signed tag/artifacts, accessible release notes, and reproducible build verification.
