#!/bin/sh
# Launch a loopback-only disposable Alpine VM for a frozen Endeavor review.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
runtime=${ENDEAVOR_VM_RUNTIME:-/tmp/endeavor-alpha-mvp}
ref=${1:-HEAD}
port=${ENDEAVOR_NOVNC_PORT:-18006}
vnc_port=${ENDEAVOR_VNC_WEBSOCKET_PORT:-5706}

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

candidate=$(git -C "$root" rev-parse --verify "${ref}^{commit}")
mkdir -p "$runtime/share/EndeavorOSCAL"
git -C "$runtime/share/EndeavorOSCAL" init -q
git -C "$runtime/share/EndeavorOSCAL" -c protocol.file.allow=always fetch -q "$root" "$candidate"
git -C "$runtime/share/EndeavorOSCAL" checkout -q --detach FETCH_HEAD

printf '%s\n' "$candidate" >"$runtime/share/CANDIDATE-COMMIT.txt"
cat >"$runtime/share/s" <<'EOF'
#!/bin/sh
ip link set eth0 up 2>/dev/null || true
udhcpc -q -n -i eth0 >/dev/null 2>&1 || true
exec sh /shared/EndeavorOSCAL/scripts/prepare-alpha-review-vm.sh
EOF
cat >"$runtime/share/r" <<'EOF'
#!/bin/sh
exec sh /shared/EndeavorOSCAL/scripts/prepare-alpha-review-vm.sh --retry
EOF
cat >"$runtime/share/v" <<'EOF'
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
# `/shared` remains writable and any exported evidence is re-checked on host.
expected=$(cat /shared/CANDIDATE-COMMIT.txt)
actual=$(git -C "$work" rev-parse HEAD)
if [ "$actual" != "$expected" ] || ! git -C "$work" diff --quiet || ! git -C "$work" diff --cached --quiet; then
  echo "Review workspace commit does not match the staged candidate." >&2
  exit 1
fi
cd "$work"
exec "$python" scripts/validate-alpha-workflow.py --review-output /tmp/endeavor-alpha-review
EOF
cat >"$runtime/share/e" <<'EOF'
#!/bin/sh
set -eu
test -d /tmp/endeavor-alpha-review
rm -rf /shared/endeavor-alpha-review
mkdir -p /shared/endeavor-alpha-review
# The 9p share does not permit preserving guest ownership.  Copy content
# without archive metadata so a successful export has a successful exit code.
cp -R /tmp/endeavor-alpha-review/. /shared/endeavor-alpha-review/
EOF
chmod 755 "$runtime/share/s" "$runtime/share/r" "$runtime/share/v" "$runtime/share/e"

iso="$runtime/alpine-virt-3.24.0-x86_64.iso"
curl -fsSL --retry 3 --output "$iso" \
  https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-virt-3.24.0-x86_64.iso
qemu-img create -f qcow2 "$runtime/storage.qcow2" 4G >/dev/null
git clone --depth 1 --branch v1.6.0 --recurse-submodules https://github.com/novnc/noVNC.git "$runtime/novnc" >/dev/null 2>&1

accelerator=tcg
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
  accelerator=kvm
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
      -netdev user,id=guestnet \
      -device virtio-net-pci,netdev=guestnet \
      -fsdev local,id=review,path="$runtime/share",security_model=none \
      -device virtio-9p-pci,fsdev=review,mount_tag=shared \
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
    -netdev user,id=guestnet \
    -device virtio-net-pci,netdev=guestnet \
    -fsdev local,id=review,path="$runtime/share",security_model=none \
    -device virtio-9p-pci,fsdev=review,mount_tag=shared \
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
printf '%s\n' "After review, stop both processes using: sh $runtime/STOP"
