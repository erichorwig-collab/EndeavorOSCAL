# GA human acceptance runbook

This runbook produces the two fresh human evidence documents required by the
version-bound GA readiness record. It must be performed for the exact frozen
GA candidate; completed alpha records, alpha reports, and alpha acceptance do
not substitute for this work.

## 1. Freeze and identify the candidate

Choose a final SemVer tag without a prerelease suffix, for example `v1.0.0`.
From the checkout that will be tagged, record its full commit SHA:

```sh
git rev-parse HEAD
```

Do not change the candidate, dependencies, mappings, generated artifacts, or
release notes after beginning review. If it changes, restart the review on the
new commit.

## 2. Create versioned records from the templates

Leave the templates untouched. Copy them to new versioned files and complete
the copies:

```sh
cp docs/ga-human-acceptance-template.md docs/ga-human-acceptance-<MAJOR.MINOR.PATCH>.md
cp docs/ga-accessibility-review-template.md docs/ga-accessibility-review-<MAJOR.MINOR.PATCH>.md
```

Replace every candidate placeholder with the GA tag, exact full commit SHA,
review UTC timestamp, reviewer, and actual observed result. A reviewer must
select either accepted or not accepted in each file; a missing or conditional
conclusion is not acceptance.

## 3. Run the human and accessibility reviews

Follow each versioned record exactly. The human record covers the support
boundary and normal/unsafe conversion behavior. The accessibility record
requires a fresh static validation result plus manual browser, keyboard, and
assistive-technology review. Retain any non-sensitive output referenced by the
record under the approved evidence storage policy.

## 4. Bind both records into the GA readiness record

After all other GA evidence is complete, create
`docs/ga-release-readiness-<MAJOR.MINOR.PATCH>.json` using the required shape
in [the GA release-readiness gate](ga-release-readiness.md). Its
`human-acceptance` and `accessibility-review` entries must point to the two
completed versioned records and include their current SHA-256 values.

Generate those hashes from the frozen checkout:

```sh
sha256sum \
  docs/ga-human-acceptance-<MAJOR.MINOR.PATCH>.md \
  docs/ga-accessibility-review-<MAJOR.MINOR.PATCH>.md
```

The remaining readiness roles must be bound to their own current evidence.
The templates do not approve the license, vulnerability, reproducible-build,
release-notes, support-policy, or compatibility-matrix roles.

## 5. Verify before the tag is created

Run the closed GA gate against the candidate and inspect its passed JSON
output:

```sh
python3 scripts/validate-ga-release-readiness.py \
  --tag v<MAJOR.MINOR.PATCH> \
  --candidate-commit "$(git rev-parse HEAD)"
```

Only after this command passes, the candidate is approved under the release
process, and the protected tag namespace permits it, create the GA tag. A
final GA tag creates a GitHub **draft** release. Follow the
[GA draft-release verification runbook](ga-draft-release-verification.md) to
verify its assets and provenance before publishing it. SemVer prerelease tags
retain the existing immediate-prerelease publication behavior.
