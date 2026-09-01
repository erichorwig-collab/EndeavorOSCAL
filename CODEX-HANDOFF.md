# EndeavorOSCAL Codex handoff

> Update this file whenever a decision, gate, candidate, or operating boundary
> changes. It contains no credentials, raw evidence, or private scan output.

## Resume point

- Repository: `erichorwig-collab/EndeavorOSCAL`.
- Local branch at handoff: `main`, tracking `origin/main`.
- Current baseline: this committed handoff. At resume, record the authoritative
  candidate with `git rev-parse HEAD` rather than relying on a stale SHA here.
- Latest completed work: a reproducible Alpine 3.24 offline-review-cache
  stager and its user-namespace regression coverage are merged through
  protected pull requests. The cache was staged and semantically consumed
  without guest networking; see the cache state below.
- Docker access: do **not** enable it for the current state. The verification
  VM is also intentionally inactive.
- Security review: see `docs/security-best-practices-review-2026-08-31.md`.
  SEC-01 through SEC-06 are mitigated or resolved; the remaining release
  control is the named independent reviewer in SEC-07.

## Product decision and GA boundary

The first GA release remains the narrow evidence-adapter contract:

- Inputs: explicit-mapping OVAL Results + Definitions, OpenSCAP `1.4.4`, OVAL
  `5.11`/`5.11.3`, with documented XCCDF `1.2.1` and linked ARF provenance.
- Output: OSCAL Assessment Results `1.2.0`.
- Execution: local, offline conversion after OpenSCAP completes the assessment.
- Exclusions: evaluator/remote-target/remediation capability, ARF archive or
  container ingestion, embedded-OVAL conversion without authoritative linkage,
  tailoring-decision interpretation, inferred controls, and OVAL 5.12 support.
- Legacy RHEL 6.3 is explicitly post-GA research. Do not claim EL6 support or
  run Endeavor natively there; its modern runtime requires Python 3.11+.

## Evidence and human gates

### Offline review cache

- A validated cache for commit
  `8b46c5932c7eba4bcfa5db004292acbc59579aef` is retained outside Git at
  `/home/elo/Work/Endeavor-review-cache/8b46c5932c7eba4bcfa5db004292acbc59579aef`.
  It is owned by `elo`, mode `0700`, and its `SHA256SUMS` digest is
  `dabb01db5c3e57c222794a6c5aa63180dcf467d452816bd303d81ad98c7a4b17`.
- Its provenance records Alpine `3.24.1` and the immutable image digest
  `alpine@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b`.
  A networkless disposable-container check successfully installed the staged
  APK closure, `lxml==6.1.2`, and the npm lockfile dependencies.
- The disposable image and containers were removed. Do not launch the review
  VM merely because the cache exists. Rebuild the cache after any candidate,
  `requirements.txt`, or `package-lock.json` change using
  `scripts/stage-alpha-review-cache.sh` and
  `scripts/validate-alpha-review-cache.py`.

Two automated corpus candidates are ready but **not yet supported**:

| Candidate | Automated state | Human action still required |
| --- | --- | --- |
| Rocky Linux 10.2 x86_64 container | Committed provenance, sanitized fixtures, goldens, and tests | Independent sanitization review using `docs/rocky-linux-10.2-sanitization-review-guide.md` |
| Ubuntu 24.04 LTS x86_64 container | Committed provenance, sanitized fixtures, goldens, and tests | Independent sanitization review using `docs/ubuntu-24.04-sanitization-review-guide.md` and `output/pdf/ubuntu-24.04-human-sanitization-review-guide.pdf` |

Both reviews must record the full reviewed commit, retained hashes, reviewer,
UTC date, decision, sensitive-data result, and SCAP-preservation result in the
respective `PROVENANCE.md`. Reject rather than edit evidence in place when
uncertain. Do not add either row to `docs/compatibility-matrix.md` before both
admission records and the version-specific GA record are complete.

## Remaining path to `v0.1.0`

1. Obtain independent approvals for both corpus candidates.
2. Add the approved corpus rows and hashes to the compatibility matrix and
   version-specific GA readiness record.
3. Freeze a clean commit; set package version `0.1.0`, tag target `v0.1.0`,
   and update the changelog/release notes.
4. Complete fresh named human and accessibility acceptance records for that
   exact commit. Alpha acceptance does not substitute.
5. Run the version-bound vulnerability, license, SBOM, reproducible-build, and
   GA readiness checks.
6. Complete the remaining pre-GA assurance items in
   `docs/security-best-practices-review-2026-08-31.md`.
7. Create the protected tag, inspect the generated draft release, verify
   SHA-256 checksums and GitHub OIDC attestations, then publish.

## Security and governance controls already in place

- `main` requires PR validation, Dependency Review, and CodeQL; force pushes
  and deletion are blocked.
- Release tags matching `v*` are protected; the release maintainer is the
  explicit bypass.
- GitHub Actions are SHA-pinned; Dependabot, OSV advisory scanning, CodeQL,
  OpenSSF Scorecard, SBOM validation, fixed-seed XML fuzz regression, and
  hostile-input tests are configured.
- GitHub keyless OIDC/Sigstore artifact attestations are the selected release
  provenance mechanism; long-lived maintainer signing keys are deferred.
- The independent `main` approval threshold remains intentionally deferred
  until the designated reviewer is known.

## Local validation note

The focused parser, corpus, fuzz, and SBOM checks pass in this host sandbox.
The full local suite has two environment-only failures: isolated package builds
cannot resolve PyPI for pinned `setuptools`, and the `build` module is absent.
Do not change project dependencies to work around that sandbox condition;
GitHub's protected validation workflow is the authoritative clean-build check.

## Safe next action

Do not start Docker, the VM, a release, or a tag solely to resume work. The
next productive action is to give the independent reviewer the Rocky and
Ubuntu review guides, then commit their decision records in a protected PR.
Consult `docs/verification-vm-build-and-configuration.md` before any future
disposable-VM launch.
