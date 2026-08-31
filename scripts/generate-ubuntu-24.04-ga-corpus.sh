#!/usr/bin/env bash
# Generate sanitized Ubuntu 24.04 / OpenSCAP 1.4.4 GA-corpus candidate evidence.
set -euo pipefail

project_root=$(cd "$(dirname "$0")/.." && pwd)
inputs="$project_root/fixtures/xccdf-tailoring"
output=${1:?usage: generate-ubuntu-24.04-ga-corpus.sh OUTPUT_DIRECTORY}
image='endeavor-ga-ubuntu-24.04-openscap:1.4.4'
dockerfile="$project_root/docker/ubuntu-24.04-openscap-1.4.4.Dockerfile"
mapping="$project_root/fixtures/mappings/arf-xccdf-example-v1.json"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

for input in openscap-1.4.4-baseline.xccdf.xml baseline.oval.xml; do
    test -f "$inputs/$input" || { echo "missing pinned input: $input" >&2; exit 2; }
done
test ! -e "$output" || { echo "output directory already exists: $output" >&2; exit 2; }
mkdir -p "$work/raw" "$work/sanitized" "$output"
chmod 777 "$work/raw"

docker build --file "$dockerfile" --tag "$image" "$project_root"
set +e
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m --hostname endeavor-target \
    --mount "type=bind,src=$inputs,dst=/input,readonly" \
    --mount "type=bind,src=$work/raw,dst=/output" \
    "$image" xccdf eval --profile xccdf_com.example.www_profile_baseline1 \
    --results /output/results.xml --results-arf /output/results.arf.xml \
    /input/openscap-1.4.4-baseline.xccdf.xml
oscap_status=$?
set -e
test "$oscap_status" -eq 2 || { echo "unexpected OpenSCAP exit: $oscap_status" >&2; exit 1; }

sha256sum "$work/raw/results.xml" "$work/raw/results.arf.xml"
python3 "$project_root/scripts/sanitize-openscap-results.py" "$work/raw/results.xml" "$work/sanitized/results.xml"
python3 "$project_root/scripts/sanitize-openscap-arf.py" "$work/raw/results.arf.xml" "$work/sanitized/results.arf.xml"
python3 -m endeavor convert-xccdf --results "$work/sanitized/results.xml" --mapping "$mapping" --output "$work/sanitized/results.oscal.json"
python3 -m endeavor convert-arf-xccdf --results "$work/sanitized/results.arf.xml" --mapping "$mapping" --output "$work/sanitized/results.arf.oscal.json"
cp "$work/sanitized/results.xml" "$work/sanitized/results.arf.xml" "$work/sanitized/results.oscal.json" "$work/sanitized/results.arf.oscal.json" "$output/"
sha256sum "$output"/*
