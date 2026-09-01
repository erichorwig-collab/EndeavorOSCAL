#!/bin/sh
# Build a hash-bound offline dependency cache inside disposable Alpine 3.24.
#
# This script intentionally performs downloads only in a dedicated staging
# environment. The resulting directory is later consumed by the networkless
# review VM. It refuses to overwrite an existing cache or use a dirty source.
set -eu

source_dir=${1:-/source}
output_dir=${2:-/output}

# The read-only host bind mount can have a different owner in a user-namespaced
# Docker daemon. Scope Git's safe-directory exception to this explicit source.
source_git() {
  git -c safe.directory="$source_dir" -C "$source_dir" "$@"
}

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this cache stager as root inside its disposable Alpine environment." >&2
  exit 1
fi
if [ ! -f "$source_dir/requirements.txt" ] || [ ! -f "$source_dir/package-lock.json" ]; then
  echo "Candidate source is incomplete: $source_dir" >&2
  exit 1
fi
if [ -L "$output_dir" ]; then
  echo "Cache output must not be a symlink." >&2
  exit 1
fi
mkdir -p "$output_dir"
if [ -n "$(find "$output_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  echo "Cache output must be empty; refusing to overwrite: $output_dir" >&2
  exit 1
fi

apk update
apk add --no-cache python3 py3-pip nodejs npm git
if ! source_git rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
   [ -n "$(source_git status --porcelain)" ]; then
  echo "Stage only a clean, frozen Git candidate checkout." >&2
  exit 1
fi
candidate=$(source_git rev-parse HEAD)
requirements_sha256=$(sha256sum "$source_dir/requirements.txt" | awk '{print $1}')
package_lock_sha256=$(sha256sum "$source_dir/package-lock.json" | awk '{print $1}')
work_dir=$(mktemp -d /tmp/endeavor-cache-source.XXXXXX)
trap 'rm -rf "$work_dir"' EXIT HUP INT TERM
mkdir -p "$output_dir/apk" "$output_dir/python" "$output_dir/npm"
# Fetch the recursive dependency closure that the guest installs with apk.
apk fetch --recursive --output "$output_dir/apk" \
  python3 py3-pip py3-virtualenv nodejs npm git

# Work on a writable copy: npm ci must create node_modules, while the frozen
# candidate is mounted read-only by the staging wrapper.
cp -a "$source_dir/." "$work_dir/"
python3 -m pip wheel --disable-pip-version-check --no-cache-dir \
  --only-binary=:all: --no-deps --wheel-dir "$output_dir/python" \
  -r "$work_dir/requirements.txt"
(cd "$work_dir" && npm ci --ignore-scripts --cache "$output_dir/npm")

wheel="$output_dir/python/lxml-6.1.2-cp314-cp314-musllinux_1_2_x86_64.whl"
if [ ! -f "$wheel" ]; then
  echo "Expected Alpine Python 3.14 lxml wheel was not staged: $wheel" >&2
  exit 1
fi

cat >"$output_dir/CACHE-METADATA" <<EOF
format=endeavor-alpha-review-offline-cache
version=1.0.0
candidate-commit=$candidate
requirements-sha256=$requirements_sha256
package-lock-sha256=$package_lock_sha256
alpine-version=3.24
EOF
cat >"$output_dir/STAGING-PROVENANCE" <<EOF
format=endeavor-alpha-review-cache-provenance
candidate-commit=$candidate
staged-at-utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
alpine-release=$(cat /etc/alpine-release)
staging-image=${ENDEAVOR_STAGING_IMAGE:-unrecorded}
EOF
(cd "$output_dir" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sed 's|  \./|  |' >SHA256SUMS)

echo "Offline cache staged at: $output_dir"
