# Human sanitization review: Rocky Linux 10.2 evidence candidate

This guide is for the human review required before the Rocky Linux 10.2
container corpus can be represented as tested support. It reviews the
committed, sanitized evidence only. Do not recover, request, or retain raw
scan output.

## Outcome and stop conditions

Approve only when all required target facts are canonical and all required
SCAP meaning is preserved. Stop and reject the candidate if you find:

- a real hostname, FQDN, address, MAC address, user identifier, package
  inventory, credential, token, private file path, or other unnecessary system
  characteristic;
- a changed or missing CPE, SCAP identifier, component reference, benchmark
  reference, rule result, schema version, or retained source hash;
- an output hash that does not match the provenance record; or
- any uncertainty about whether a value is sensitive.

On rejection, do not edit the evidence in place. Record the reason, remove the
candidate from admission consideration, regenerate it in a disposable
environment, and submit a new review.

## 1. Establish the review scope

Work from the project root on the host:

```sh
cd /home/elo/Work/Endeavor
git rev-parse HEAD
git status --short
```

The worktree must be clean. Review only these files:

- `fixtures/ga-corpus/rocky-linux-10.2-x86_64/PROVENANCE.md`
- `fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.xml`
- `fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.xml`
- `fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.oscal.json`
- `fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.oscal.json`

Do not use a recovered raw artifact for comparison. The provenance document
records raw hashes only to prove deletion and lineage.

## 2. Verify integrity before reading content

Run these commands on the host from the project root:

```sh
sha256sum \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.xml \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.xml \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.oscal.json \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.oscal.json

python3 -m endeavor inspect-xccdf \
  --results fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.xml

python3 -m endeavor inspect-arf \
  --results fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.xml
```

Compare the four hashes to the table in `PROVENANCE.md`. The inspection
output must show:

- target: `endeavor-target`;
- identity: `endeavor-fixture-user`;
- IPv4 address: `127.0.0.1`;
- IPv6 address: `0:0:0:0:0:0:0:1`; and
- MAC address: `00:00:00:00:00:00`.

## 3. Inspect the two SCAP evidence files

Open `results.xml` and `results.arf.xml` in a text editor. Confirm that
host and execution identifiers use only the canonical values above. Confirm
that the retained scanner facts remain visible:

- OpenSCAP version `1.4.4`;
- the OpenSCAP CPE / test-system reference;
- benchmark and component references under `/input/`; and
- the expected not-selected rule outcomes for the deliberately failing test
  input.

The `/input/` paths are fixed container paths, not host paths. They are
required SCAP evidence and are allowed.

Use this bounded search to find likely sensitive values:

```sh
rg -n -i \
  'localhost|hostname|fqdn|target-address|mac-address|mac_address|ip-v4|ip-v6|ip_address|identity|token|password|secret|/home/' \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.xml \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.xml
```

Every target-related match must be either a canonical value above or an
explicitly documented, non-sensitive SCAP field. Scanner metadata and
Rocky/OpenSCAP version identifiers are in scope and may remain.

## 4. Verify the derived OSCAL artifacts

The two JSON files are golden outputs. Confirm they do not introduce a target
fact absent from their SCAP source and that they preserve provenance without
claiming evaluator semantics.

```sh
python3 -m endeavor convert-xccdf \
  --results fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.xml \
  --mapping fixtures/mappings/arf-xccdf-example-v1.json \
  --output /tmp/endeavor-rocky-xccdf-review.json

python3 -m endeavor convert-arf-xccdf \
  --results fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.xml \
  --mapping fixtures/mappings/arf-xccdf-example-v1.json \
  --output /tmp/endeavor-rocky-arf-review.json

cmp /tmp/endeavor-rocky-xccdf-review.json \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.oscal.json

cmp /tmp/endeavor-rocky-arf-review.json \
  fixtures/ga-corpus/rocky-linux-10.2-x86_64/results.arf.oscal.json
```

Both `cmp` commands must return silently with exit status 0. Remove the two
temporary review files after the review.

## 5. Record the decision

Add this entry to `PROVENANCE.md` in a review change:

```text
Human sanitization review
- Reviewer: <name or approved reviewer identifier>
- Date (UTC): <YYYY-MM-DD>
- Decision: approved | rejected
- Evidence reviewed: results.xml, results.arf.xml, results.oscal.json,
  results.arf.oscal.json
- Integrity: all four retained SHA-256 values matched
- Sensitive-data review: canonical target, identity, address, and MAC values
  confirmed; no unnecessary host data found
- SCAP preservation: identifiers, CPEs, references, schema versions, and rule
  results confirmed
- Notes: <none or concise exception/rejection reason>
```

An approval completes only the human sanitization-review gate. The Rocky row
must remain outside the tested compatibility matrix until the GA acceptance
record includes it and the Ubuntu corpus gate is also complete.
