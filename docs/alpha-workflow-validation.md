# Representative alpha workflow validation

Phase 3 exits when a security engineer can trace two mapped evidence runs
without scraping output or inferring control semantics. The automated path is:

```bash
python3 scripts/validate-alpha-workflow.py
```

For a human review that retains the generated artifacts, follow the
[alpha tester packet](alpha-tester-packet.md).

It converts a passing and failing OVAL run with the versioned mapping, validates
both OSCAL outputs, inventories the explicit finding, reports the true-to-false
delta, and renders the semantic HTML mapping report. CI runs the same script.
CI retains a 30-day machine-readable manifest with the repository commit and
SHA-256 hashes of its fixture inputs, schema, and generated artifacts.

The release reviewer must also perform these human assertions once per alpha
candidate:

1. Open the generated report at normal browser zoom and verify the mapped,
   unmapped, and stale sections are understandable without raw XML.
2. Navigate its headings and tables with a keyboard or screen reader; captions
   and column headers must identify the information relationship.
3. Confirm the finding target/status came from the authored mapping, and that
   the source OVAL status remains visible.
4. Confirm the diff identifies the changed definition and both source statuses.
5. Record the command output, commit SHA, reviewer, and any known schema limits
   in a copy of the [alpha acceptance template](alpha-acceptance-template.md).

The pinned OSCAL schema currently rejects the standard related-observation
reference object; the converter therefore records the source observation UUID
as a namespaced finding property. The reviewer must acknowledge that documented
limitation before approving the alpha gate.
