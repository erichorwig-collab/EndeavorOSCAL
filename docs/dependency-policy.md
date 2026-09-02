# Dependency and SBOM policy

Endeavor's alpha dependency inventory is the committed, deterministic
[CycloneDX 1.5 SBOM](../sbom.cdx.json). Regenerate it with:

```bash
python3 scripts/generate-sbom.py
python3 scripts/generate-sbom.py --check sbom.cdx.json
```

The validation workflow fails if the committed SBOM differs from the manifests.
It therefore identifies the exact runtime XML parser and the locked AJV
validation dependency closure used by the current OVAL vertical slice.

## Update rule

- Runtime Python dependencies are exact pins in both `pyproject.toml` and
  `requirements.txt`; the PEP 517 release frontend is pinned in
  `requirements-release-build.txt` and the isolated build backend is pinned in
  `pyproject.toml`; Node validation dependencies are locked in
  `package-lock.json` and installed with `npm ci`.
- A dependency update requires a maintainer review of the release notes,
  license, supported Python/Node versions, and relevant security advisories.
  The current reviewed allow-list is MIT, Apache-2.0, BSD-2-Clause, and
  BSD-3-Clause. Apache-2.0 OR BSD-2-Clause is specifically required by the
  pinned PyPA `packaging` release-build dependency.
- Regenerate the SBOM, run the focused test suite, and retain the CI result in
  the change record before merging.
- GitHub Dependency Review is the pull-request gate for newly introduced high
  or critical vulnerabilities in runtime and development dependencies.
  Dependabot supplies update pull requests. Weekly OSV-Scanner inventory is an
  independent advisory signal; its changing advisory data does not by itself
  block a release.
- The separately pinned Betterleaks binary scans complete Git history on pull
  requests and `main`. Its project-owned policy is
  [`.betterleaks.toml`](../.betterleaks.toml); the workflow verifies the
  release-asset SHA-256 before execution. The scan uses full redaction and
  high-confidence findings to keep the corpus meaningful. It deliberately does
  **not** enable live-secret validation, external-source scans, reports, or
  artifact uploads. The wrapper rejects repository ignore files and inline
  allow-directives, and the workflow starts it with an otherwise empty
  environment. Updating the scanner requires reviewing its release notes and
  replacing both the version and checksum together.
- A vulnerability exception must be an exact, approved, version-controlled
  record in `security/vulnerability-exceptions.json`. It needs the advisory,
  package, affected range, rationale, compensating control, approver, and a
  future expiry. Run `python3 scripts/validate-vulnerability-exceptions.py`.
  An exception never silently disables a scanner or creates an open-ended
  waiver.

For a GA tag, the frozen checkout is scanned again and
[`validate-ga-vulnerability-disposition.py`](../scripts/validate-ga-vulnerability-disposition.py)
blocks unresolved High, Critical, and unclassified OSV findings. The scheduled
OSV workflow remains advisory for ordinary development and alpha releases; see
[the GA disposition gate](ga-vulnerability-disposition.md).

Vendored OSCAL and OVAL schemas are separately tracked with source and tree
hashes in `endeavor/schemas/MANIFEST.md`; they are not package-manager
dependencies and must be reviewed as imported artifacts.
