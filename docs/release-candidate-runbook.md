# Release candidate runbook: v0.1.0-alpha.1

This runbook freezes and reviews the first Endeavor alpha candidate. It does
not authorize a tag or a public release until every gate below is complete.

## Candidate identity

- Public release tag: `v0.1.0-alpha.1`
- Python package version: `0.1.0a1`
- Candidate commit: record the immutable `git rev-parse HEAD` output after the
  candidate-preparation commit is pushed.

## 1. Protect version tags in GitHub

In the repository, open **Settings → Rules → Rulesets → New ruleset** and
create an active ruleset named **Protect version tags**:

| Setting | Value |
| --- | --- |
| Target | Tags |
| Include | `v*` |
| Rules | Restrict creations, Restrict updates, Restrict deletions |
| Bypass | Add the authorized release maintainer explicitly |

Do not leave the bypass list empty when creation is restricted: that could
prevent the authorized maintainer from creating the reviewed release tag.
Do not grant a broad bypass to ordinary contributors. After saving, confirm
that the ruleset is **Active** and applies to `refs/tags/v0.1.0-alpha.1`.

Repository administrator access (or GitHub's **Edit repository rules**
permission) is required. The `Protect Endeavor release tags` ruleset is active
for the published alpha; retain this control for every future release.

## 2. Freeze and test the candidate

The release tag must not be created before acceptance because tags beginning
with `v` invoke publication. Freeze the candidate by retaining its full commit
SHA in the acceptance record and CI URL. From the clean checkout:

```bash
git rev-parse HEAD
python3 -m unittest discover -s tests -v
python3 scripts/generate-sbom.py --check sbom.cdx.json
python3 scripts/validate-governance-readiness.py
```

Use the disposable VM only with a review-kit snapshot and verified offline cache
made for that exact commit. In the VM, run the short commands one at a time:

```sh
mkdir -p /shared
```

```sh
mount -t 9p -o ro shared /shared
```

```sh
mkdir -p /export && mount -t 9p export /export
```

```sh
sh /shared/s
```

```sh
sh /shared/v
```

```sh
sh /shared/e
```

Open the exported `mapping-report.html` on the host at normal zoom. Complete a
new acceptance record copied from
[`alpha-acceptance-template.md`](alpha-acceptance-template.md), naming this
candidate SHA. The disposable VM may then be deleted.

After acceptance, re-confirm the SHA has not changed and create the reviewed
tag from that exact commit:

```bash
git tag -a v0.1.0-alpha.1 <candidate-sha> -m "EndeavorOSCAL v0.1.0-alpha.1"
git push origin v0.1.0-alpha.1
```

That push invokes the release workflow. It creates the GitHub Release only if
the frozen source passes all validation and builds the source archive twice
with byte-identical output. Tags with a SemVer prerelease suffix (for example,
`v0.1.0-alpha.1`) are published as GitHub prereleases.

## 3. Review dependency licenses

The committed [CycloneDX SBOM](../sbom.cdx.json) is the review inventory. The
current alpha closure contains only MIT and BSD-3-Clause third-party entries:

```bash
jq -r '.components[] | [.name, .version, (.licenses[0].license.id // "NOASSERTION"), .purl] | @tsv' sbom.cdx.json
```

Review the displayed package/version/license list against the intended
Apache-2.0 distribution and record the reviewer and outcome in the candidate
approval record. This inventory is not a substitute for reading an upstream
license when a package or license changes.

## 4. Verify published assets and attestations

After the GitHub Release completes, download its assets from the release page
or with the GitHub CLI:

```bash
mkdir -p /tmp/endeavor-release-verify
cd /tmp/endeavor-release-verify
gh release download v0.1.0-alpha.1 --repo erichorwig-collab/EndeavorOSCAL
sha256sum -c SHA256SUMS
gh attestation verify EndeavorOSCAL-0.1.0-alpha.1-source.tar.gz --repo erichorwig-collab/EndeavorOSCAL
```

Success requires every checksum to report `OK` and `gh attestation verify` to
report a verified GitHub build provenance for the repository. Preserve the
release URL and the verification output in the final approval record.
