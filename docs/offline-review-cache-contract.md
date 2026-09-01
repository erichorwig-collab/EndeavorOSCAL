# Offline review-cache contract

The disposable verification VM starts in strict offline mode. Before a
maintainer may launch it, they must stage an external cache directory and pass
its absolute path as `ENDEAVOR_VM_OFFLINE_CACHE`. The launcher copies that
directory into the read-only candidate share, verifies it, and refuses to start
on a mismatch. The cache is intentionally external to Git because it contains
platform packages and may be large.

## Required layout

```text
offline-cache/
  CACHE-METADATA
  SHA256SUMS
  apk/                         # complete Alpine 3.24 package closure
  python/lxml-6.1.2-...whl     # Alpine Python 3.14 musllinux wheel
  npm/                         # npm cache usable by npm ci --offline
```

`CACHE-METADATA` has exactly these newline-delimited `key=value` fields:

```text
format=endeavor-alpha-review-offline-cache
version=1.0.0
candidate-commit=<40-character frozen Git commit>
requirements-sha256=<SHA-256 of requirements.txt at that commit>
package-lock-sha256=<SHA-256 of package-lock.json at that commit>
alpine-version=3.24
```

`SHA256SUMS` contains one `sha256␠␠relative/path` entry for every regular file
in the cache except itself, including `CACHE-METADATA`. It must contain no
absolute paths, `..` segments, duplicate paths, symlinks, device files, or
unlisted files.

## Controlled staging procedure

1. Freeze the candidate commit and record `git rev-parse HEAD`.
2. In an approved disposable Alpine 3.24 staging environment, fetch the full
   package closure for `python3`, `py3-pip`, `py3-virtualenv`, `nodejs`, `npm`,
   and `git`. Preserve the signed `.apk` files under `apk/`.
3. Obtain the exact Alpine/Python 3.14 `lxml==6.1.2` wheel under `python/`.
4. Populate `npm/` from the selected candidate's `npm ci` cache. The lockfile
   retains npm's package-integrity assertions; the cache manifest additionally
   detects staging corruption.
5. Write the metadata using hashes from the selected candidate, generate the
   sorted SHA-256 manifest, and retain the staging provenance with the release
   record.
6. Run the validator before any launch:

   ```sh
   python3 scripts/validate-alpha-review-cache.py --cache /absolute/path/to/offline-cache --candidate "$(git rev-parse HEAD)" --requirements requirements.txt --package-lock package-lock.json
   ```

7. Launch only after it passes:

   ```sh
   ENDEAVOR_VM_OFFLINE_CACHE=/absolute/path/to/offline-cache sh scripts/launch-alpha-review-vm.sh HEAD
   ```

The `ENDEAVOR_VM_ALLOW_ONLINE_BOOTSTRAP=1` escape hatch is retained only for
legacy alpha troubleshooting. It is deliberately non-GA-eligible and must not
be used for acceptance evidence.
