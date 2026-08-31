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
  `requirements.txt`; Node validation dependencies are locked in
  `package-lock.json` and installed with `npm ci`.
- A dependency update requires a maintainer review of the release notes,
  license, supported Python/Node versions, and relevant security advisories.
- Regenerate the SBOM, run the focused test suite, and retain the CI result in
  the change record before merging.
- GitHub Dependency Review is the pull-request gate for newly introduced high
  or critical vulnerabilities in runtime and development dependencies.
  Dependabot supplies update pull requests. Weekly OSV-Scanner inventory is an
  independent advisory signal; its changing advisory data does not by itself
  block a release.
- A vulnerability exception must be an exact, approved, version-controlled
  record in `security/vulnerability-exceptions.json`. It needs the advisory,
  package, affected range, rationale, compensating control, approver, and a
  future expiry. Run `python3 scripts/validate-vulnerability-exceptions.py`.
  An exception never silently disables a scanner or creates an open-ended
  waiver.

Vendored OSCAL and OVAL schemas are separately tracked with source and tree
hashes in `endeavor/schemas/MANIFEST.md`; they are not package-manager
dependencies and must be reviewed as imported artifacts.
