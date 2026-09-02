#!/bin/sh
# Run the pinned Betterleaks binary against the complete local Git history.
# The caller supplies the binary after independently verifying its checksum.
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 /path/to/betterleaks" >&2
  exit 64
fi

scanner=$1
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

case "$($scanner version)" in
  1.8.1) ;;
  *)
    echo "Betterleaks v1.8.1 is required" >&2
    exit 65
    ;;
esac

cd "$project_root"
for ignored_path in .betterleaksignore .gitleaksignore; do
  if [ -e "$ignored_path" ]; then
    echo "repository ignore files are not permitted: $ignored_path" >&2
    exit 66
  fi
done

"$scanner" config check .betterleaks.toml
"$scanner" git . \
  --config .betterleaks.toml \
  --git-workers 4 \
  --confidence high \
  --timeout 300 \
  --max-target-megabytes 20 \
  --max-archive-depth 1 \
  --max-decode-depth 2 \
  --ignore-gitleaks-allow \
  --no-banner \
  --no-color \
  --redact=100
