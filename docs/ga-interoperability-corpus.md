# GA interoperability corpus protocol

This protocol turns the narrow GA support boundary into reproducible
interoperability evidence. It does not broaden the supported profile.

## Required corpus before the first GA tag

For each supported row in the compatibility matrix, retain at least one
sanitized representative result from the declared OpenSCAP version and target
environment. For the narrow GA profile, the required set is:

| Profile | Minimum evidence | Expected check |
| --- | --- | --- |
| OVAL Results + Definitions 5.11/5.11.3 | One paired result/definitions capture per supported schema version | `inspect`, explicit-mapped `convert`, OSCAL schema validation, stable golden output |
| XCCDF 1.2.1 | One result from each declared target environment | `inspect-xccdf`, explicit-mapped `convert-xccdf`, OSCAL schema validation |
| ARF 1.1 | One locally resolved XCCDF report and one authoritative linkage-manifest case | `inspect-arf`, `convert-arf-xccdf`, and linkage resolution without network access |

The first GA target environments are Linux x86_64 systems evaluated by
OpenSCAP 1.4.4. The GA corpus must include Rocky Linux 10.2 x86_64 and Ubuntu
24.04 LTS x86_64 targets. The first covers the RHEL-compatible enterprise Linux
family; the second covers a Debian-family LTS. Their pinned producer paths and
container-only boundary are in the [GA platform-corpus plan](ga-platform-corpus-plan.md).
The exact image, OpenSCAP package build or source hash, and target facts must
be recorded in each corpus item's `PROVENANCE.md`; this is required test
coverage, not a claim that every RHEL or Ubuntu deployment is supported. A new
environment becomes supported only when its corpus item and
compatibility-matrix row are added in the same change.

## Intake record

Each corpus directory must include `PROVENANCE.md` with:

- source producer name and exact version;
- evaluated target environment and non-sensitive target characteristics;
- input, output, and source-command SHA-256 hashes;
- upstream licensing/redistribution status;
- a sanitization review describing removed or transformed data;
- the expected Endeavor commands and output hashes; and
- reviewer, review date, and regression disposition.

Never commit an unsanitized scan, credentials, hostnames, addresses, user
identifiers, installed-package inventories, or system characteristics that are
not needed for the declared assertion.

## Acceptance and regression

An intake change must run the full test suite and add golden assertions for
the declared profile. The GA acceptance record must list every accepted corpus
directory and its committed SHA-256 values. A malformed or rejected sample can
be retained only when it is labeled as negative-test evidence, never as
compatibility evidence.

Changes to parsing, mapping, source-schema support, or target environments
require re-running the corresponding corpus and recording any changed golden
output as an intentional compatibility decision.
