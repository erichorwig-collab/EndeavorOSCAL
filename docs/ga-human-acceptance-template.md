# General Availability human acceptance record template

> Status: **not accepted** until a named reviewer completes this record for one
> exact GA candidate. This template is not evidence, must not be cited by a GA
> readiness record, and must remain unchanged.

## Candidate

- GA tag:
- Candidate commit SHA (40 lowercase hexadecimal characters):
- Review date and time (UTC):
- Reviewer name, role, and organization:
- Test environment (OS/version, CPU architecture, Python version):

## Automated evidence observed by the reviewer

Run the commands from the frozen candidate checkout. Record each command's
result or link/hash to its retained output; do not reuse an alpha result.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/fuzz-untrusted-xml.py --seed <documented-seed> --cases <documented-count>
python3 scripts/validate-alpha-workflow.py --record <new-retained-manifest-path>
```

```text
<paste command outputs, CI run URLs, or retained-artifact SHA-256 values>
```

## Human assertions

Mark an assertion only after performing it against the exact candidate above.

- [ ] The published support boundary, compatibility matrix, known limitations,
  and non-goals are clear and match the candidate behavior I reviewed.
- [ ] A supported OVAL Results + Definitions pair converts successfully, and
  the generated OSCAL Assessment Results validates with the declared schema.
- [ ] Source definition identifiers, statuses, hashes, evaluator metadata, and
  explicit mappings are retained without implying re-executable OVAL logic.
- [ ] Unsupported, malformed, oversized, and unsafe inputs fail without
  writing a trusted partial output or disclosing sensitive host paths/content.
- [ ] The installed `endeavor` command works from a clean environment outside
  the source checkout using the supported installation method.
- [ ] I understand the documented limits for ARF archives, embedded OVAL
  linkage, tailoring interpretation, and inferred control mappings.

## Reviewer conclusion

- [ ] Accepted for this GA tag.
- [ ] Not accepted; follow-up required.

Notes, defects, limitations, and follow-up issue/commit:

```text
<record notes>
```
