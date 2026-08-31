# Independent release verification — v0.1.0-alpha.1

> Status: **passed**. The published alpha release is marked as a GitHub
> prerelease and is anchored by the protected `v0.1.0-alpha.1` tag.

## Release identity

- Verification date (UTC): 2026-08-31 04:12 UTC
- Tag: `v0.1.0-alpha.1`
- Tagged commit: `83352a59db5ba2dfc4e64e65d23e6e4e01263ce5`
- Release workflow: `https://github.com/erichorwig-collab/EndeavorOSCAL/actions/runs/33356195239`
- Release page: `https://github.com/erichorwig-collab/EndeavorOSCAL/releases/tag/v0.1.0-alpha.1`

## Independent verification

The release assets were downloaded fresh from GitHub into a temporary local
directory. `sha256sum -c SHA256SUMS` passed for every listed asset, and GitHub
artifact attestation verification passed for the source archive:

```sh
gh release download v0.1.0-alpha.1 --repo erichorwig-collab/EndeavorOSCAL
sha256sum -c SHA256SUMS
gh attestation verify EndeavorOSCAL-0.1.0-alpha.1-source.tar.gz \
  --repo erichorwig-collab/EndeavorOSCAL
```

| Asset | SHA-256 |
| --- | --- |
| `EndeavorOSCAL-0.1.0-alpha.1-source.tar.gz` | `60a05952f0178580082eba7dd529109a3374817831b7e5676dca1e498971389c` |
| `sbom.cdx.json` | `1b9ff4b74c3963c5d2efc51dc846bc8fcf4aa55d89fe0759c62bac2a6ffaa0e7` |
| `release-manifest.json` | `dbd8447b690a9a58331ca397a46dd8d1604081e39005cb41eaaf72a6f03feaa8` |

The temporary downloaded verification directory was not retained after this
record was created.
