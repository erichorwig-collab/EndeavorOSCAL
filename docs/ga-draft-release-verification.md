# GA draft-release verification

Final GA tags create a GitHub **draft** release. This gives an authorized
release maintainer a final, independently verifiable checkpoint before the
release becomes public. SemVer prerelease tags continue to publish immediately
as prereleases.

## Verify the draft

After the tagged release workflow succeeds, use an authenticated GitHub CLI
session with access to the repository. Substitute the exact GA tag:

```sh
export ENDEAVOR_TAG=v1.0.0
export ENDEAVOR_REPO=erichorwig-collab/EndeavorOSCAL
mkdir -p /tmp/endeavor-ga-release-verify
cd /tmp/endeavor-ga-release-verify
gh release download "$ENDEAVOR_TAG" --repo "$ENDEAVOR_REPO"
sha256sum -c SHA256SUMS
gh attestation verify "EndeavorOSCAL-${ENDEAVOR_TAG#v}-source.tar.gz" \
  --repo "$ENDEAVOR_REPO"
```

Every checksum must report `OK`, and `gh attestation verify` must report a
verified GitHub build provenance for this repository. Also inspect the draft's
release notes and confirm the attached source archive, SBOM, checksum file,
and release manifest identify the exact frozen candidate. Record the release
URL, verifier, UTC time, and command output location in the completed GA
release evidence.

Do not publish on a failed, incomplete, or ambiguous result. Correct the
candidate through the normal review process and create a new version/tag; do
not retarget a protected release tag.

## Publish the verified draft

Only after the checks pass, publish the exact draft:

```sh
gh release edit "$ENDEAVOR_TAG" --repo "$ENDEAVOR_REPO" --draft=false
```

Publishing is the deliberate final public-release action. Keep the local
temporary download only as long as needed for the recorded evidence, then
remove it according to the evidence-retention policy.
