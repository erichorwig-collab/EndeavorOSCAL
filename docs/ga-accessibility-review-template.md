# General Availability accessibility review record template

> Status: **not accepted** until a named reviewer completes this record for one
> exact GA candidate. This template is not evidence, must not be cited by a GA
> readiness record, and must remain unchanged.

## Candidate and review environment

- GA tag:
- Candidate commit SHA (40 lowercase hexadecimal characters):
- Review date and time (UTC):
- Reviewer name, role, and organization:
- Operating system and version:
- Browser name and version:
- Assistive technology name and version (or `none used`):
- Input method(s) used (keyboard, mouse, switch, voice, other):

## Generated-report and static-check evidence

From the frozen candidate checkout, create a new temporary report directory
and run the static check. This check verifies report structure only; it does
not emulate a browser, keyboard use, layout/reflow, contrast, or a screen
reader.

```sh
mkdir -p /tmp/endeavor-ga-accessibility-review
python3 -m endeavor report \
  --results fixtures/oval-results/fail.xml \
  --definitions fixtures/oval-definitions/definitions.xml \
  --mapping fixtures/mappings/example-v1.json \
  --output /tmp/endeavor-ga-accessibility-review/mapping-report.html
python3 scripts/validate-report-accessibility.py \
  --report /tmp/endeavor-ga-accessibility-review/mapping-report.html
```

```text
<paste static-check JSON output and record the generated report SHA-256>
```

## Manual review assertions

Open the generated `mapping-report.html` in the listed browser and use the
listed input/assistive technology. Mark each assertion only after performing
it on the exact candidate report.

- [ ] The document has a meaningful title and language, and exposes one main
  landmark and a logical heading hierarchy.
- [ ] Keyboard navigation has a visible, logical focus path with no keyboard
  trap; the static report has no pointer-only action required to read it.
- [ ] Headings, summary content, and all three report sections are discoverable
  and understandable without reading raw XML.
- [ ] Each table exposes its caption, column headers, and cell relationships to
  the chosen assistive technology.
- [ ] At 200% browser zoom and a 320 CSS-pixel viewport, information and
  controls remain available without two-dimensional scrolling except where a
  table's data necessarily requires horizontal review.
- [ ] Status and mapping information remain understandable from text, not color
  alone, and contrast is adequate in the rendered browser.
- [ ] The report contains no unexpected focus movement, automatic speech,
  flashing, animation, or time limit.

## Reviewer conclusion

- [ ] Accepted for this GA tag.
- [ ] Not accepted; follow-up required.

Notes, observed barriers, assistive-technology behavior, and follow-up
issue/commit:

```text
<record notes>
```
