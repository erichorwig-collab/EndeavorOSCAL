# GA platform-corpus plan

> Status: **planned, not yet supported**. This document fixes the first GA
> target environments and their reproducible producer paths. Support begins
> only after sanitized evidence, provenance, golden assertions, and a GA
> acceptance record are committed under the
> [interoperability-corpus protocol](ga-interoperability-corpus.md).

## Chosen targets

| Target | Producer path | Why this target | Boundary |
| --- | --- | --- | --- |
| Rocky Linux 10.2 x86_64 container | Rocky AppStream `openscap-scanner-1.4.4-1.el10_2` | RHEL-compatible enterprise Linux coverage with a native OpenSCAP 1.4.4 package | Container userland evidence only; it is not a claim of bare-metal, VM, or every RHEL deployment support. |
| Ubuntu 24.04 LTS x86_64 container | Build the upstream OpenSCAP 1.4.4 release source in a pinned Ubuntu image | Debian-family LTS coverage while retaining Endeavor's declared OpenSCAP 1.4.4 / OVAL 5.11.3 producer contract | Ubuntu's native `openscap-scanner` 1.3.9 is not a substitute: its OVAL capability is outside the declared producer profile. |

Rocky is an independently built RHEL-compatible downstream, not “unbranded
RHEL.” A future licensed-RHEL evaluation is still needed before representing
vendor-supported RHEL deployments as tested.

The [Rocky Linux 10.2 evidence candidate](../fixtures/ga-corpus/rocky-linux-10.2-x86_64/PROVENANCE.md)
is retained with schema-aware conversion goldens. Its human sanitization review
is still pending, so the compatibility matrix remains unchanged.

## Immutable producer inputs

- Resolve each base-image digest for `linux/amd64` immediately before the
  generation run and record the digest in that corpus directory.
- Rocky uses the exact package NEVRA above, recorded with `rpm -q` output.
- Ubuntu uses the upstream `openscap-1.4.4` source release with SHA-256
  `25b1b046822121204e6d53d877a532c88bf7fde14b94c9c72297cd5709b03478`.
- Both targets use the source-pinned inputs in `fixtures/xccdf-tailoring/`.

## Required retained evidence

For each target, create an isolated directory beneath `fixtures/ga-corpus/`
containing sanitized XCCDF Results and ARF output, command and environment
metadata, `PROVENANCE.md`, expected conversion outputs, and regression tests.
Raw output is hashed, reviewed, and deleted; it is never committed. The
provenance record must include the image digest, OpenSCAP version/NEVRA or
source hash, `oscap --version`, `/etc/os-release`, architecture, commands,
input/output hashes, licensing basis, sanitization review, and reviewer.

During evaluation, use a read-only input mount, a dedicated writable output
mount, `--network none`, `--read-only`, `--cap-drop ALL`,
`--security-opt no-new-privileges`, a fixed non-sensitive hostname, and only
the required temporary writable filesystem. A nonzero `oscap xccdf eval`
status is expected for the deliberately failing upstream test input and must be
recorded rather than suppressed.

## Admission criteria

Before either row is moved into the compatibility matrix's tested support
profile:

1. The sanitizer must be target-aware and prove that raw hostnames, interface
   addresses, MAC addresses, and execution identities are absent from the
   committed output. It changes only schema-defined asset-identification,
   OVAL system-characteristics, and XCCDF identity/target fields (including
   named asset-identifier facts); it does not perform unsafe generic
   replacement of ARF content, identifiers, CPE names, or unrelated facts.
2. Endeavor must inspect and convert the retained XCCDF Results and ARF without
   external access; their expected output is covered by golden tests.
3. The full test suite, SBOM check, and human sanitization review must pass.
4. The exact corpus paths and SHA-256 values are included in the versioned GA
   acceptance record.

This two-target corpus is the first platform-expansion gate. Fedora, Debian,
and SUSE-family coverage are future additions under the same protocol.
