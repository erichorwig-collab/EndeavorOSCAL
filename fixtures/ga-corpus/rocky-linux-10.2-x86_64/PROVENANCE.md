# Rocky Linux 10.2 x86_64 OpenSCAP evidence candidate

Status: **sanitized candidate; human sanitization review pending**. This
corpus is not a claim of tested platform support until the GA corpus admission
criteria are complete.

## Producer

- Target: Rocky Linux 10.2 (Red Quartz) x86_64 container.
- Base image: `rockylinux/rockylinux@sha256:827d37bc128288ccf160ee318bb3cb92d591164cb217e92f8bc61e3982ae1834`.
- Evaluator image: `endeavor-ga-rocky-10.2-openscap@sha256:eefa82d30a2940e0fbb4f36689c6a08f9a78efa722413b121a0ac5eaef18b3e6`.
- OpenSCAP packages: `openscap-1.4.4-1.el10_2.x86_64` and
  `openscap-scanner-1.4.4-1.el10_2.x86_64`.
- Producer capabilities: OpenSCAP 1.4.4; SCAP 1.3; XCCDF 1.2; OVAL 5.11.3;
  CPE 2.3; Asset Identification 1.1; ARF 1.1.

The evaluator was built from the pinned base image with the exact scanner
package version. It evaluated only the source-pinned inputs:

| Input | SHA-256 |
| --- | --- |
| `openscap-1.4.4-baseline.xccdf.xml` | `401a2403a88a12922d833d95bc4e0b69b71da5757bf8e8269df9c95e0520c4e0` |
| `openscap-1.4.4-baseline.tailoring.xml` | `74f23255019049cad1e87bad47a367d418bf484febdf11489ee3e91421fb7a2a` |
| `baseline.oval.xml` | `177fe196551e72d4d0c9509f45a59bb4479c2606dd79731bf4cd4b27b4500baf` |

## Evaluation boundary

The evaluator used a read-only input mount, dedicated writable temporary
output, `--network none`, `--read-only`, `--cap-drop ALL`,
`--security-opt no-new-privileges`, a non-sensitive hostname, and a
`/tmp` tmpfs. The deliberately failing fixture returned OpenSCAP exit status
`2`, which was expected and retained in the generation record.

Raw outputs were hashed before sanitization and deleted:

| Raw artifact | SHA-256 |
| --- | --- |
| XCCDF Results | `bba190971612553803699de378c111feccaa469dd4fb4ea1b75295f575559bdb` |
| ARF | `59b674561ec2ba22d78a04b0a2df7392f5e9527a6de4d999ad2d48770d65d736` |

The committed outputs were produced by the target-aware sanitizer. It
canonicalizes only typed host, address, MAC, identity, and named
asset-identifier facts; it preserves SCAP identifiers, CPEs, references, and
unrelated facts. Automated schema-aware intake and conversion tests passed.
Human sanitization review remains required before admission.

## Retained artifacts

| Artifact | SHA-256 |
| --- | --- |
| `results.xml` | `45dfdb438004f550b9b30fafddfdfb3be6eabc7b5c0c004e67a5632ef0eb0e0e` |
| `results.arf.xml` | `2ff5492934bdaea4beee1e75ae134f55f09a29038cf818ff22a89b410663d2b4` |
| `results.oscal.json` | `69b84dff4de3384dccf534b041dee04fb3125e01ce7e8948cf9d21f36bca36ba` |
| `results.arf.oscal.json` | `645be3e82da6e8cd08a663c967081a625a7eb943830dbf6bef86a3650874f4f9` |

`results.oscal.json` is the expected conversion of `results.xml` through
`fixtures/mappings/arf-xccdf-example-v1.json`; `results.arf.oscal.json` is
the corresponding ARF conversion using the same explicit mapping. The corpus
is Apache-2.0 project test evidence; the producer components retain their
respective upstream licenses.
