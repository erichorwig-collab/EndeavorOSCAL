# Alpha acceptance record template

> Status: **not accepted** until a named human reviewer completes and signs
> this record. This template is not an approval artifact.

## Candidate

- Review date (UTC):
- Reviewer name and role:
- Reviewed commit SHA:
- Environment/browser/assistive technology (if used):

## Automated evidence

Run this command from the reviewed commit and paste its JSON output below:

```bash
python3 scripts/validate-alpha-workflow.py
```

```text
<paste command output>
```

## Human assertions

Mark each item only after performing it on the generated HTML report.

- [ ] At normal browser zoom, the mapped, unmapped, and stale sections are
  understandable without reading raw XML.
- [ ] Keyboard or screen-reader navigation exposes meaningful headings, table
  captions, and column headers.
- [ ] The finding target and status match the authored mapping, while the
  original OVAL status remains visible.
- [ ] The diff identifies the changed definition and both source statuses.
- [ ] I acknowledge the documented schema limit: the source observation UUID
  is currently represented as a namespaced finding property rather than an
  OSCAL related-observation object.

## Reviewer conclusion

- [ ] Accepted for the alpha gate.
- [ ] Not accepted; follow-up required.

Notes, limitations, and follow-up issue/commit:

```text
<record notes>
```
