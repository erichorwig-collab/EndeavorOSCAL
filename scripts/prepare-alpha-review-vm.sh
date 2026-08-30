#!/bin/sh
# Prepare the disposable Alpine Alpha-review guest. This script must run as root
# inside the VM after its /shared 9p review-kit mount is available.
set -eu

retry_mode=N
if [ "${1:-}" = "--retry" ]; then
  retry_mode=Y
  shift
fi

source_dir=${1:-/shared/EndeavorOSCAL}
if [ "$retry_mode" = Y ]; then
  work_dir=${ENDEAVOR_WORK_DIR:-/tmp/endeavor-work-retry}
  venv_dir=${ENDEAVOR_VENV_DIR:-/tmp/endeavor-venv-retry}
else
  work_dir=${ENDEAVOR_WORK_DIR:-/tmp/endeavor-work}
  venv_dir=${ENDEAVOR_VENV_DIR:-/tmp/endeavor-venv}
fi
package_cache=${ENDEAVOR_APK_CACHE:-/shared/apk-cache-v3.24}
wheelhouse=${ENDEAVOR_WHEELHOUSE:-/shared/python-wheelhouse}
node_modules_cache=${ENDEAVOR_NODE_MODULES_CACHE:-/shared/node_modules}

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
if [ -f "$1" ]; then
  echo "Installing pre-fetched Alpine packages from $package_cache"
  apk add --no-network --no-cache --force-non-repository "$@"
else
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

if [ -d "$wheelhouse" ] && [ -f "$wheelhouse/lxml-6.1.2-cp314-cp314-musllinux_1_2_x86_64.whl" ]; then
  "$venv_dir/bin/python" -m pip install --disable-pip-version-check --no-index --find-links "$wheelhouse" -r "$work_dir/requirements.txt"
else
  "$venv_dir/bin/python" -m pip install --disable-pip-version-check -r "$work_dir/requirements.txt"
fi

if [ -d "$node_modules_cache" ]; then
  cp -a "$node_modules_cache" "$work_dir/node_modules"
else
  (cd "$work_dir" && npm ci)
fi

cat <<EOF

Alpha review workspace is ready.

Copy and paste this next command into the VM:
  . "$venv_dir/bin/activate" && cd "$work_dir" && python3 scripts/validate-alpha-workflow.py --review-output /tmp/endeavor-alpha-review

After validation, copy the review output back to the host-visible share:
  cp -a /tmp/endeavor-alpha-review /shared/
EOF
