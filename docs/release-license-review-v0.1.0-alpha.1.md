# Dependency license review — v0.1.0-alpha.1

> Status: **approved by the project maintainer**. This is a distribution
> compatibility record, not legal advice.

## Candidate and decision

- Review date (UTC): 2026-08-31 04:08 UTC
- Reviewer: Erich Orwig, project maintainer
- Candidate commit: `83352a59db5ba2dfc4e64e65d23e6e4e01263ce5`
- Distribution license: Apache-2.0
- Maintainer decision: approved the listed MIT and BSD-3-Clause dependencies
  for `v0.1.0-alpha.1`.

## Reviewed SBOM inventory

The committed CycloneDX SBOM contains no `NOASSERTION` license entries for this
candidate. The package/version/license inventory reviewed was:

| Package | Version | SPDX license | Package URL |
| --- | --- | --- | --- |
| ajv | 8.20.0 | MIT | `pkg:npm/ajv@8.20.0` |
| fast-deep-equal | 3.1.3 | MIT | `pkg:npm/fast-deep-equal@3.1.3` |
| fast-uri | 3.1.6 | BSD-3-Clause | `pkg:npm/fast-uri@3.1.6` |
| json-schema-traverse | 1.0.0 | MIT | `pkg:npm/json-schema-traverse@1.0.0` |
| lxml | 6.1.2 | BSD-3-Clause | `pkg:pypi/lxml@6.1.2` |
| require-from-string | 2.0.2 | MIT | `pkg:npm/require-from-string@2.0.2` |

## Outcome and retention

The reviewed licenses are permissive and compatible with the intended
Apache-2.0 source distribution. Retain the repository `LICENSE`, the committed
`sbom.cdx.json`, and any applicable third-party notices in the release source
archive. Repeat this review if the SBOM inventory or any license identifier
changes.
