# Dependency and SBOM policy

Endeavor's pre-alpha dependency inventory is the committed, deterministic
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
- Vulnerability scanning is advisory until a trusted scanner and an exception
  process are selected. It is not represented as a passing security gate yet.

Vendored OSCAL and OVAL schemas are separately tracked with source and tree
hashes in `endeavor/schemas/MANIFEST.md`; they are not package-manager
dependencies and must be reviewed as imported artifacts.
