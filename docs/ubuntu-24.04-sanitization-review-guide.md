# Human sanitization review: Ubuntu 24.04 evidence candidate

Use this short guide to decide whether the committed Ubuntu 24.04 evidence
candidate can enter the GA compatibility matrix. Review the committed,
sanitized files only. Do not recover, request, or retain raw scan output.

## Stop immediately if

Reject the candidate if you find a real hostname, FQDN, address, MAC address,
user identifier, package inventory, credential, token, private path, or any
other unnecessary system characteristic. Also reject it if a required CPE,
SCAP identifier, component reference, rule result, schema version, or retained
hash is missing or different. When uncertain, reject: do not edit evidence in
place.

## 1. Start from a clean checkout

Run on the review host:

```sh
cd /home/elo/Work/Endeavor
git status --short
git rev-parse HEAD
```

The first command must print nothing. Record the exact output of
`git rev-parse HEAD` in the decision record; do not approve a later checkout
against an earlier review. Review only these five files:

- `fixtures/ga-corpus/ubuntu-24.04-x86_64/PROVENANCE.md`
- `fixtures/ga-corpus/ubuntu-24.04-x86_64/results.xml`
- `fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.xml`
- `fixtures/ga-corpus/ubuntu-24.04-x86_64/results.oscal.json`
- `fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.oscal.json`

## 2. Verify the files before reading them

```sh
sha256sum fixtures/ga-corpus/ubuntu-24.04-x86_64/results.xml \
  fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.xml \
  fixtures/ga-corpus/ubuntu-24.04-x86_64/results.oscal.json \
  fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.oscal.json

python3 -m endeavor inspect-xccdf \
  --results fixtures/ga-corpus/ubuntu-24.04-x86_64/results.xml

python3 -m endeavor inspect-arf \
  --results fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.xml
```

Compare all four hashes with `PROVENANCE.md`. Inspection must show only these
canonical target facts: target `endeavor-target`, identity
`endeavor-fixture-user`, IPv4 `127.0.0.1`, IPv6 `0:0:0:0:0:0:0:1`, and MAC
`00:00:00:00:00:00`.

## 3. Review the SCAP evidence

Open `results.xml` and `results.arf.xml`. Confirm the canonical target facts
above and preserve these required meanings:

- OpenSCAP `1.4.4`, SCAP `1.3`, XCCDF `1.2`, OVAL `5.11.3`, CPE `2.3`, and
  ARF `1.1` producer capabilities;
- CPE, benchmark, component, and `/input/` references; and
- expected rule outcomes for the deliberately failing fixture.

The following non-sensitive platform facts are required and allowed: Ubuntu
`24.04.4 LTS`, architecture `x86_64`, loopback interface `lo`, and fixed
`/input/` container paths. They are not reviewer-host paths or an installed
package inventory.

```sh
rg -n -i 'localhost|hostname|fqdn|target-address|mac-address|mac_address|ip-v4|ip-v6|ip_address|identity|token|password|secret|/home/' \
  fixtures/ga-corpus/ubuntu-24.04-x86_64/results.xml \
  fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.xml
```

Every target-related match must be a canonical value above or a documented,
non-sensitive SCAP field.

## 4. Verify the generated OSCAL files

```sh
python3 -m endeavor convert-xccdf \
  --results fixtures/ga-corpus/ubuntu-24.04-x86_64/results.xml \
  --mapping fixtures/mappings/arf-xccdf-example-v1.json \
  --output /tmp/endeavor-ubuntu-xccdf-review.json

python3 -m endeavor convert-arf-xccdf \
  --results fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.xml \
  --mapping fixtures/mappings/arf-xccdf-example-v1.json \
  --output /tmp/endeavor-ubuntu-arf-review.json

cmp /tmp/endeavor-ubuntu-xccdf-review.json \
  fixtures/ga-corpus/ubuntu-24.04-x86_64/results.oscal.json
cmp /tmp/endeavor-ubuntu-arf-review.json \
  fixtures/ga-corpus/ubuntu-24.04-x86_64/results.arf.oscal.json
rm -f /tmp/endeavor-ubuntu-xccdf-review.json /tmp/endeavor-ubuntu-arf-review.json
```

Both `cmp` commands must be silent and return status 0.

## 5. Record the decision

Add this to `fixtures/ga-corpus/ubuntu-24.04-x86_64/PROVENANCE.md` in a review
change. Do not approve the matrix row until the Rocky review and the
version-specific GA acceptance record are also complete.

```text
Human sanitization review
- Reviewer: <name or approved reviewer identifier>
- Date (UTC): <YYYY-MM-DD>
- Reviewed commit: <full output of git rev-parse HEAD>
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
