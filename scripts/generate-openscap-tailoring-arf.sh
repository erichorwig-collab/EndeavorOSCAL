#!/usr/bin/env bash
# Generate the committed sanitized tailoring ARF; requires authorized Docker access.
set -euo pipefail

project_root=$(cd "$(dirname "$0")/.." && pwd)
inputs="$project_root/fixtures/xccdf-tailoring"
output="$project_root/fixtures/arf"
raw="$output/openscap-1.4.4-tailoring-generated.arf.xml"
sanitized="$output/openscap-1.4.4-tailoring-sanitized.arf.xml"
image="registry.fedoraproject.org/fedora:43@sha256:26a6fa6061ce1cf1e1592079e072c0dac77c0cdc50e8e306690febca1165b674"

for input in openscap-1.4.4-baseline.xccdf.xml openscap-1.4.4-baseline.tailoring.xml baseline.oval.xml; do
    test -f "$inputs/$input" || { echo "missing pinned input: $input" >&2; exit 2; }
done

rm -f "$raw"
docker run --rm -v "$inputs:/work:ro" -v "$output:/output" "$image" bash -lc '
    dnf -y install openscap-scanner >/dev/null
    oscap xccdf eval --tailoring-file /work/openscap-1.4.4-baseline.tailoring.xml \
      --results-arf /output/openscap-1.4.4-tailoring-generated.arf.xml \
      /work/openscap-1.4.4-baseline.xccdf.xml
'
python3 "$project_root/scripts/sanitize-openscap-arf.py" "$raw" "$sanitized"
rm -f "$raw"
sha256sum "$sanitized"
