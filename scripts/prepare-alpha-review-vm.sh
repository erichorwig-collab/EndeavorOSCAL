#!/bin/sh
# Prepare the disposable Alpine Alpha-review guest. This script must run as root
# inside the VM after its /shared 9p review-kit mount is available.
set -eu

retry_mode=N
allow_online_bootstrap=N
while [ "$#" -gt 0 ]; do
  case "$1" in
    --retry) retry_mode=Y ;;
    --allow-online-bootstrap) allow_online_bootstrap=Y ;;
    *) break ;;
  esac
  shift
done

source_dir=${1:-/shared/EndeavorOSCAL}
if [ "$retry_mode" = Y ]; then
  work_dir=${ENDEAVOR_WORK_DIR:-/tmp/endeavor-work-retry}
  venv_dir=${ENDEAVOR_VENV_DIR:-/tmp/endeavor-venv-retry}
else
  work_dir=${ENDEAVOR_WORK_DIR:-/tmp/endeavor-work}
  venv_dir=${ENDEAVOR_VENV_DIR:-/tmp/endeavor-venv}
fi
cache_root=${ENDEAVOR_OFFLINE_CACHE:-/shared/offline-cache}
package_cache="$cache_root/apk"
wheelhouse="$cache_root/python"
npm_cache="$cache_root/npm"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as the VM's local root user." >&2
  exit 1
fi

if [ ! -f "$source_dir/requirements.txt" ] || [ ! -f "$source_dir/package.json" ]; then
  echo "Alpha review kit not found at: $source_dir" >&2
  exit 1
fi

if [ -e "$work_dir" ] || [ -e "$venv_dir" ]; then
  echo "A previous workspace exists. Restart the disposable VM or set ENDEAVOR_WORK_DIR and ENDEAVOR_VENV_DIR." >&2
  exit 1
fi

set -- "$package_cache"/*.apk
if [ "$allow_online_bootstrap" = N ]; then
  [ -f "$1" ] && [ -f "$wheelhouse/lxml-6.1.2-cp314-cp314-musllinux_1_2_x86_64.whl" ] && [ -d "$npm_cache" ] || {
    echo "Verified offline review cache is incomplete; do not use online bootstrap for GA." >&2
    exit 1
  }
  echo "Installing verified pre-fetched Alpine packages from $package_cache"
  apk add --no-network --no-cache "$@"
else
  echo "WARNING: online bootstrap is legacy-only and is not eligible for GA evidence." >&2
  series=$(cut -d. -f1,2 /etc/alpine-release)
  cat >/etc/apk/repositories <<EOF
https://dl-cdn.alpinelinux.org/alpine/v${series}/main
https://dl-cdn.alpinelinux.org/alpine/v${series}/community
EOF
  apk update
  apk add --no-cache python3 py3-pip py3-virtualenv nodejs npm git
fi

cp -a "$source_dir" "$work_dir"
python3 -m venv "$venv_dir"

if [ "$allow_online_bootstrap" = N ]; then
  "$venv_dir/bin/python" -m pip install --disable-pip-version-check --no-index --find-links "$wheelhouse" -r "$work_dir/requirements.txt"
else
  "$venv_dir/bin/python" -m pip install --disable-pip-version-check -r "$work_dir/requirements.txt"
fi

if [ "$allow_online_bootstrap" = N ]; then
  (cd "$work_dir" && npm ci --offline --ignore-scripts --cache "$npm_cache")
else
  (cd "$work_dir" && npm ci --ignore-scripts)
fi

cat <<'EOF'

Alpha review workspace is ready.

In the supplied VM, run this short noVNC-safe command next:
  sh /shared/v

After validation, export the review output with:
  sh /shared/e
EOF
