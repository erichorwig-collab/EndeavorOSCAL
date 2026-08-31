# Ubuntu 24.04 x86_64 OpenSCAP evidence candidate

Status: **sanitized candidate; human sanitization review pending**. This corpus
is not a claim of tested platform support until the GA corpus admission
criteria are complete.

## Producer

- Target: Ubuntu 24.04.4 LTS x86_64 container.
- Base image: `ubuntu@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`.
- Evaluator image ID: `sha256:0977bf15475271bfbec71074d9adf9a048a2f7ac13581b1bebc12ee6cefde641`.
- OpenSCAP source: upstream `openscap-1.4.4` release archive, SHA-256
  `25b1b046822121204e6d53d877a532c88bf7fde14b94c9c72297cd5709b03478`.
- Producer capabilities: OpenSCAP 1.4.4; SCAP 1.3; XCCDF 1.2; OVAL 5.11.3;
  CPE 2.3; Asset Identification 1.1; ARF 1.1.

The evaluator was built by
[`docker/ubuntu-24.04-openscap-1.4.4.Dockerfile`](../../../docker/ubuntu-24.04-openscap-1.4.4.Dockerfile)
from the pinned Ubuntu base and exact upstream source checksum. It evaluated
the source-pinned baseline XCCDF and OVAL inputs using profile
`xccdf_com.example.www_profile_baseline1`.

| Input | SHA-256 |
| --- | --- |
| `openscap-1.4.4-baseline.xccdf.xml` | `401a2403a88a12922d833d95bc4e0b69b71da5757bf8e8269df9c95e0520c4e0` |
| `baseline.oval.xml` | `177fe196551e72d4d0c9509f45a59bb4479c2606dd79731bf4cd4b27b4500baf` |

The separate tailoring input was deliberately not selected: its temporary
OpenSCAP ARF linkage is ambiguous, and Endeavor correctly rejects it rather
than inferring a relationship. This corpus therefore does not claim tailoring
interpretation support.

## Evaluation boundary

The evaluator used a read-only input mount, dedicated writable temporary
output, `--network none`, `--read-only`, `--cap-drop ALL`,
`--security-opt no-new-privileges`, a non-sensitive hostname, and a `/tmp`
tmpfs. The deliberately failing fixture returned OpenSCAP exit status `2`.

Raw outputs were hashed before sanitization and deleted:

| Raw artifact | SHA-256 |
| --- | --- |
| XCCDF Results | `916efefef5b6f41403d279686516384365f2b62f7cfba91437762ce8b81495bd` |
| ARF | `cfeef2cc098e70f2fff323e32f92b08f416485011c7698a72b3cca7e2e4b4fd5` |

The committed outputs were produced by the target-aware sanitizer. It
canonicalizes only typed host, address, MAC, identity, and named
asset-identifier facts; it preserves SCAP identifiers, CPEs, references, and
unrelated facts. Automated schema-aware intake and conversion checks passed.
Human sanitization review remains required before admission.

## Retained artifacts

| Artifact | SHA-256 |
| --- | --- |
| `results.xml` | `5ec6516bc5f6ed76a145f664edb9f78314483d93582ac33bea7468e8ff045280` |
| `results.arf.xml` | `f124fe580de14609cf8b4500cc63e1b5efe3fa4569ce94e82de2d5bb2af43458` |
| `results.oscal.json` | `2cb57979b05cbe928c1e1b78a4faf6eaedbefbc181383baebbe6ac60f66a71e2` |
| `results.arf.oscal.json` | `4cf7bf699aa6e97f38c989440874b452bce943e2f9d39a868fb96b430f8c1b2a` |

`results.oscal.json` is the expected conversion of `results.xml` through
`fixtures/mappings/arf-xccdf-example-v1.json`; `results.arf.oscal.json` is the
corresponding ARF conversion using the same explicit mapping. The corpus is
Apache-2.0 project test evidence; producer components retain their respective
upstream licenses.
