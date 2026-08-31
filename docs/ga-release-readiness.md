# GA release-readiness gate

This gate is intentionally separate from the completed alpha gate and the
governance-planning checker. It fails closed until the exact GA candidate has a
version-bound evidence record. It does not create a tag or replace the required
post-publication checksum and attestation verification.

Before creating a GA tag such as `v1.0.0`, create
`docs/ga-release-readiness-1.0.0.json`. The record must use this shape:

```json
{
  "format": "endeavor-ga-release-readiness",
  "version": "1.0.0",
  "status": "accepted",
  "tag": "v1.0.0",
  "candidate-commit": "<40-character lowercase Git SHA>",
  "reviewed-at": "<UTC RFC 3339 timestamp ending in Z>",
  "reviewer": "<named accountable reviewer>",
  "evidence": {
    "human-acceptance": {"path": "docs/<record>.md", "sha256": "<SHA-256>"},
    "accessibility-review": {"path": "docs/<record>.md", "sha256": "<SHA-256>"},
    "license-review": {"path": "docs/<record>.md", "sha256": "<SHA-256>"},
    "vulnerability-review": {"path": "docs/<record>.md", "sha256": "<SHA-256>"},
    "reproducible-build": {"path": "docs/<record>.md", "sha256": "<SHA-256>"},
    "release-notes": {"path": "docs/<record>.md", "sha256": "<SHA-256>"},
    "support-policy": {"path": "docs/<record>.md", "sha256": "<SHA-256>"},
    "compatibility-matrix": {"path": "docs/<record>.md", "sha256": "<SHA-256>"}
  }
}
```

Each evidence path is repository-relative, names a regular non-symlink file,
and is SHA-256-bound in the record. One document may support more than one
role only when its content genuinely supplies each required decision.

Validate the frozen checkout before tagging:

```sh
python3 scripts/validate-ga-release-readiness.py \
  --tag v1.0.0 \
  --candidate-commit "$(git rev-parse HEAD)"
```

The command returns nonzero and a machine-readable `incomplete` result until
the version-matched record exists and every referenced evidence hash verifies.
