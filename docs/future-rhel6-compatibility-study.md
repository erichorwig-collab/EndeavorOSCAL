# Future work: legacy RHEL 6.3 compatibility study

This is a post-GA research item. It does not add RHEL 6.3, CentOS 6.3, or any
other Enterprise Linux 6 system to the Endeavor support contract.

## Why this is separate

Endeavor currently requires Python 3.11 or later. An untouched EL6 system is
therefore not a supported local Endeavor runtime. Rocky Linux is also not an
EL6 comparator: its first supported major release is EL8.

The possible future use case is different: evaluate a legacy target using its
appropriate OpenSCAP tooling, export a sanitized evidence pair, then convert
the evidence on a supported modern Endeavor host.

## Preconditions for a study

1. Obtain customer-authorized RHEL 6.3 media and representative, sanitized
   SCAP content. A licensed RHEL 6.3 VM is required before any vendor-RHEL
   compatibility claim.
2. If a freely redistributable historical comparison is useful, use CentOS 6.3
   only as an isolated best-effort fixture and label it unsupported/EOL.
3. Use a full, no-network QEMU/KVM virtual machine. Containers share the host
   kernel and cannot prove 2.6.32-era kernel or userland behavior.
4. Retain only sanitized results, definitions, version metadata, hashes, and
   review records. Delete raw evidence after the approved workflow.

## Study exit criteria

- Record the exact blocker: customer workload/kernel ABI, OpenSCAP evaluator,
  SCAP content, or the Endeavor conversion runtime.
- Establish whether the legacy evaluator's schemas and output meet a new,
  explicit producer profile.
- Add a target-specific corpus, reproducible golden tests, human sanitization
  review, and a versioned support-policy amendment before any compatibility
  claim.

Until then, the supported operational pattern is a modern offline conversion
station for evidence originating from legacy systems, without claiming that
the evidence is accepted or that the legacy target is supported.
