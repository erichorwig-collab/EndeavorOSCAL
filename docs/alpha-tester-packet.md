# Alpha tester packet

Use this packet for the human Phase 3 acceptance gate. It is intentionally
separate from automated CI: the reviewer must inspect the rendered report and
record their own conclusion.

## Prepare the candidate

From a clean checkout of the candidate commit:

```bash
python3 -m pip install --disable-pip-version-check -r requirements.txt
npm ci
git rev-parse HEAD
python3 scripts/validate-alpha-workflow.py --review-output /tmp/endeavor-alpha-review
```

For the supplied disposable Alpha-review VM, first follow the
[Alpha VM start guide](alpha-test-vm-start-here.md). Its bootstrap creates the
same clean checkout, virtual environment, and Node dependencies under `/tmp`.
Then run the same validation command shown above. Export the retained output to
`/shared/endeavor-alpha-review` and open `mapping-report.html` from that
host-visible directory in a normal browser.

The last command prints the machine-readable validation record and retains:

- `/tmp/endeavor-alpha-review/pass.json`
- `/tmp/endeavor-alpha-review/fail.json`
- `/tmp/endeavor-alpha-review/mapping-report.html`

Open `mapping-report.html` in a browser at normal zoom. Review the generated
JSON and HTML before deleting the directory.

## Complete the gate

1. Copy [the alpha acceptance template](alpha-acceptance-template.md) into
   your approval record.
2. Paste the validation command's JSON output and the commit SHA.
3. Perform every human assertion in the template, including keyboard or
   screen-reader navigation.
4. Record any limitation or follow-up, then mark Accepted or Not accepted.

The related-observation schema limitation must be acknowledged: the converter
records the source observation UUID as a namespaced finding property.

Do not put passwords, host identities, or unredacted scan evidence in the
acceptance record.
