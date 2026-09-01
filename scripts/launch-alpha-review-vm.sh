#!/bin/sh
# Launch a loopback-only disposable Alpine VM for a frozen Endeavor review.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
runtime=${ENDEAVOR_VM_RUNTIME:-/tmp/endeavor-alpha-mvp}
ref=${1:-HEAD}
port=${ENDEAVOR_NOVNC_PORT:-18006}
vnc_port=${ENDEAVOR_VNC_WEBSOCKET_PORT:-5706}
offline_cache=${ENDEAVOR_VM_OFFLINE_CACHE:-}
allow_online_bootstrap=${ENDEAVOR_VM_ALLOW_ONLINE_BOOTSTRAP:-0}

for required in qemu-img qemu-system-x86_64 curl git python3 tar; do
    command -v "$required" >/dev/null 2>&1 || {
        echo "Required host command is unavailable: $required" >&2
        exit 1
    }
done

case "$port:$vnc_port" in
    *[!0-9:]* | :* | *:) echo "Ports must be numeric." >&2; exit 1 ;;
esac

if [ -e "$runtime" ]; then
    echo "Disposable VM runtime already exists: $runtime" >&2
    echo "Remove it only after saving any review record, then run this command again." >&2
    exit 1
fi

case "$allow_online_bootstrap" in
    0|1) ;;
    *) echo "ENDEAVOR_VM_ALLOW_ONLINE_BOOTSTRAP must be 0 or 1." >&2; exit 1 ;;
esac
if [ "$allow_online_bootstrap" = 0 ] && [ -z "$offline_cache" ]; then
    echo "A verified offline cache is required; set ENDEAVOR_VM_OFFLINE_CACHE." >&2
    echo "The legacy online bootstrap is explicitly non-GA: ENDEAVOR_VM_ALLOW_ONLINE_BOOTSTRAP=1." >&2
    exit 1
fi
if [ -n "$offline_cache" ] && { [ ! -d "$offline_cache" ] || [ -L "$offline_cache" ]; }; then
    echo "ENDEAVOR_VM_OFFLINE_CACHE must name a real directory." >&2
    exit 1
fi

candidate=$(git -C "$root" rev-parse --verify "${ref}^{commit}")
head=$(git -C "$root" rev-parse HEAD)
if [ "$candidate" != "$head" ] || ! git -C "$root" diff --quiet || ! git -C "$root" diff --cached --quiet; then
    echo "Launch only a clean checkout at its current HEAD; freeze a release candidate before VM review." >&2
    exit 1
fi
mkdir -p "$runtime/candidate/EndeavorOSCAL" "$runtime/export"
chmod 700 "$runtime/export"
git -C "$runtime/candidate/EndeavorOSCAL" init -q
git -C "$runtime/candidate/EndeavorOSCAL" -c protocol.file.allow=always fetch -q "$root" "$candidate"
git -C "$runtime/candidate/EndeavorOSCAL" checkout -q --detach FETCH_HEAD

if [ -n "$offline_cache" ]; then
    cp -a "$offline_cache" "$runtime/candidate/offline-cache"
    python3 "$root/scripts/validate-alpha-review-cache.py" \
        --cache "$runtime/candidate/offline-cache" \
        --candidate "$candidate" \
        --requirements "$runtime/candidate/EndeavorOSCAL/requirements.txt" \
        --package-lock "$runtime/candidate/EndeavorOSCAL/package-lock.json"
fi

# Create the trusted, host-owned expected artifact manifest before exposing the
# candidate to the guest. A guest record alone cannot prove hostile-root output.
python3 "$root/scripts/validate-alpha-workflow.py" \
    --record "$runtime/candidate/EXPECTED-ALPHA-REVIEW-MANIFEST.json" >/dev/null

printf '%s\n' "$candidate" >"$runtime/candidate/CANDIDATE-COMMIT.txt"
cat >"$runtime/candidate/s" <<EOF
#!/bin/sh
$(if [ "$allow_online_bootstrap" = 1 ]; then printf '%s\n' 'ip link set eth0 up 2>/dev/null || true' 'udhcpc -q -n -i eth0 >/dev/null 2>&1 || true' 'exec sh /shared/EndeavorOSCAL/scripts/prepare-alpha-review-vm.sh --allow-online-bootstrap'; else printf '%s\n' 'exec sh /shared/EndeavorOSCAL/scripts/prepare-alpha-review-vm.sh'; fi)
EOF
cat >"$runtime/candidate/r" <<EOF
#!/bin/sh
exec sh /shared/EndeavorOSCAL/scripts/prepare-alpha-review-vm.sh --retry $(if [ "$allow_online_bootstrap" = 1 ]; then printf '%s' --allow-online-bootstrap; fi)
EOF
cat >"$runtime/candidate/v" <<'EOF'
#!/bin/sh
set -eu
if [ -x /tmp/endeavor-venv-retry/bin/python ]; then
  python=/tmp/endeavor-venv-retry/bin/python
  work=/tmp/endeavor-work-retry
else
  python=/tmp/endeavor-venv/bin/python
  work=/tmp/endeavor-work
fi
# Detect an accidental wrong or modified guest workspace before validation.
# This is an operator-integrity check, not protection from a hostile root guest:
# `/shared` is a read-only candidate mount and host export verification remains
# necessary before trusting guest-produced evidence.
expected=$(cat /shared/CANDIDATE-COMMIT.txt)
actual=$(git -C "$work" rev-parse HEAD)
if [ "$actual" != "$expected" ] || ! git -C "$work" diff --quiet || ! git -C "$work" diff --cached --quiet; then
  echo "Review workspace commit does not match the staged candidate." >&2
  exit 1
fi
cd "$work"
exec "$python" scripts/validate-alpha-workflow.py --review-output /tmp/endeavor-alpha-review
EOF
cat >"$runtime/candidate/e" <<'EOF'
#!/bin/sh
set -eu
test -d /tmp/endeavor-alpha-review
test ! -e /export/endeavor-alpha-review
mkdir /export/endeavor-alpha-review
# Export only retained evidence; never delete or modify the frozen candidate.
for artifact in pass.json fail.json mapping-report.html; do
  test -f "/tmp/endeavor-alpha-review/$artifact"
  cp "/tmp/endeavor-alpha-review/$artifact" /export/endeavor-alpha-review/
done
EOF
chmod 755 "$runtime/candidate/s" "$runtime/candidate/r" "$runtime/candidate/v" "$runtime/candidate/e"
chmod -R a-w "$runtime/candidate"

iso="$runtime/alpine-virt-3.24.0-x86_64.iso"
iso_sha256=6cd1a38ae05cf96a5d0cbb2ddd6c630834babfeca1ecc5d1f05ec0b06b886102
iso_partial="$iso.partial"
trap 'rm -f "$iso_partial"' 0 1 2 15
curl -fsSL --retry 3 --output "$iso_partial" \
  https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-virt-3.24.0-x86_64.iso
printf '%s  %s\n' "$iso_sha256" "$iso_partial" | sha256sum --check --status - || {
    echo "Alpine ISO checksum verification failed." >&2
    exit 1
}
mv "$iso_partial" "$iso"
trap - 0 1 2 15
qemu-img create -f qcow2 "$runtime/storage.qcow2" 4G >/dev/null
novnc_commit=a8dfd6a3ea3c74244f5ebdaa5a7f1023007a7820
# The tag selects the shallow source; the immutable commit check binds what is
# subsequently executed, so a moved tag is rejected before noVNC starts.
git -c protocol.file.allow=never clone --depth 1 --branch v1.6.0 --recurse-submodules https://github.com/novnc/noVNC.git "$runtime/novnc" >/dev/null 2>&1
if [ "$(git -C "$runtime/novnc" rev-parse HEAD)" != "$novnc_commit" ]; then
    echo "noVNC source commit verification failed." >&2
    exit 1
fi

accelerator=tcg
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
  accelerator=kvm
fi

network_args=
if [ "$allow_online_bootstrap" = 1 ]; then
  network_args='-netdev user,id=guestnet -device virtio-net-pci,netdev=guestnet'
fi

if command -v systemd-run >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  systemd-run --user --unit=endeavor-alpha-novnc --collect --no-block \
    bash "$runtime/novnc/utils/novnc_proxy" --listen "127.0.0.1:$port" --vnc 127.0.0.1:5906 --web "$runtime/novnc" --file-only >/dev/null
  systemd-run --user --unit=endeavor-alpha-qemu --collect --no-block \
    qemu-system-x86_64 \
      -name endeavor-alpha-review \
      -accel "$accelerator" \
      -m 2048 -smp 2 \
      -drive file="$iso",media=cdrom,readonly=on \
      -drive file="$runtime/storage.qcow2",if=virtio \
      $network_args \
      -fsdev local,id=candidate,path="$runtime/candidate",security_model=none,readonly=on \
      -device virtio-9p-pci,fsdev=candidate,mount_tag=shared \
      -fsdev local,id=export,path="$runtime/export",security_model=none \
      -device virtio-9p-pci,fsdev=export,mount_tag=export \
      -vnc "127.0.0.1:6,websocket=$vnc_port" \
      -display none >/dev/null
  stop_command='systemctl --user stop endeavor-alpha-qemu.service endeavor-alpha-novnc.service'
  sleep 1
  systemctl --user is-active --quiet endeavor-alpha-qemu.service
else
  nohup bash "$runtime/novnc/utils/novnc_proxy" --listen "127.0.0.1:$port" --vnc 127.0.0.1:5906 --web "$runtime/novnc" --file-only >"$runtime/novnc.log" 2>&1 &
  novnc_pid=$!
  nohup qemu-system-x86_64 \
    -name endeavor-alpha-review \
    -accel "$accelerator" \
    -m 2048 -smp 2 \
    -drive file="$iso",media=cdrom,readonly=on \
    -drive file="$runtime/storage.qcow2",if=virtio \
    $network_args \
    -fsdev local,id=candidate,path="$runtime/candidate",security_model=none,readonly=on \
    -device virtio-9p-pci,fsdev=candidate,mount_tag=shared \
    -fsdev local,id=export,path="$runtime/export",security_model=none \
    -device virtio-9p-pci,fsdev=export,mount_tag=export \
    -vnc "127.0.0.1:6,websocket=$vnc_port" \
    -display none >"$runtime/qemu.log" 2>&1 &
  qemu_pid=$!
  sleep 1
  if ! kill -0 "$qemu_pid" 2>/dev/null; then
    kill "$novnc_pid" 2>/dev/null || true
    cat "$runtime/qemu.log" >&2
    exit 1
  fi
  stop_command="kill $qemu_pid $novnc_pid"
fi

printf '%s\n' "$stop_command" >"$runtime/STOP"
printf '%s\n' "Candidate: $candidate"
printf '%s\n' "Open: http://127.0.0.1:$port/vnc.html?autoconnect=true&host=127.0.0.1&port=$vnc_port"
printf '%s\n' "VM runtime: $runtime"
printf '%s\n' "After stopping the guest, verify and copy export on the host: python3 $root/scripts/verify-alpha-review-export.py --candidate $runtime/candidate/EndeavorOSCAL --expected $runtime/candidate/EXPECTED-ALPHA-REVIEW-MANIFEST.json --export $runtime/export/endeavor-alpha-review --candidate-commit $candidate --destination $runtime/verified-export"
printf '%s\n' "After review, stop both processes using: sh $runtime/STOP"
