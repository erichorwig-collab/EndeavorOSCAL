# Release-candidate checklist

> This checklist prepares a release candidate. It does not authorize a public
> release or claim certification.

## Candidate identity and scope

- [ ] Select the candidate semantic version and document the supported source
  formats in [the compatibility matrix](compatibility-matrix.md).
- [ ] Confirm the candidate excludes the intentionally deferred archive,
  tailoring-interpretation, and cross-format-expansion work.
- [ ] Update [the changelog](../CHANGELOG.md) with a UTC date, known limits,
  accessibility impact, and security-relevant changes.

## Required evidence

- [ ] Record a clean commit SHA and successful CI run URL.
- [ ] Obtain a named human alpha acceptance record for that exact candidate
  commit. A record for an earlier commit is evidence for its reviewed behavior,
  not approval of a later candidate.
- [ ] Run `python3 -m unittest discover -s tests -v`.
- [ ] Run `python3 scripts/generate-sbom.py --check sbom.cdx.json`.
- [ ] Run `python3 scripts/validate-alpha-workflow.py --record <new-path>` and
  retain the resulting manifest.
- [ ] Run `python3 scripts/validate-governance-readiness.py`.
- [ ] Review the current OpenSSF Scorecard SARIF result; it is advisory unless
  a future policy makes a score threshold mandatory.
- [ ] Review dependency advisories and record any accepted exception with its
  owner, rationale, expiry, and compensating control.
- [ ] Review dependency licenses against the distribution intent and record the
  reviewer and outcome.

## Publication controls requiring an explicit decision

- [ ] Choose the release artifact(s) and publication destination.
- [ ] Choose the signing identity, key custody/recovery approach, and tag
  protection policy.
- [ ] Select a trusted vulnerability scanner and exception authority.
- [ ] Define reproducible-build inputs and an independent verification method.
- [ ] Enable SLSA provenance only after the artifact and publication decisions
  above are recorded.

## Approval record

- Candidate version:
- Commit SHA:
- CI run URL:
- Reviewer(s) and UTC approval time:
- Accepted limitations and exception references:
