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
git -C "$root" archive --format=tar "$candidate" | tar -xf - -C "$runtime/share/EndeavorOSCAL"

printf '%s\n' "$candidate" >"$runtime/share/CANDIDATE-COMMIT.txt"
cat >"$runtime/share/s" <<'EOF'
#!/bin/sh
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
cd "$work"
exec "$python" scripts/validate-alpha-workflow.py --review-output /tmp/endeavor-alpha-review
EOF
cat >"$runtime/share/e" <<'EOF'
#!/bin/sh
set -eu
test -d /tmp/endeavor-alpha-review
rm -rf /shared/endeavor-alpha-review
cp -a /tmp/endeavor-alpha-review /shared/
EOF
chmod 755 "$runtime/share/s" "$runtime/share/r" "$runtime/share/v" "$runtime/share/e"

iso="$runtime/alpine-virt-3.24.0-x86_64.iso"
curl -fsSL --retry 3 --output "$iso" \
  https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-virt-3.24.0-x86_64.iso
qemu-img create -f qcow2 "$runtime/storage.qcow2" 4G >/dev/null
git clone --depth 1 --branch v1.6.0 https://github.com/novnc/noVNC.git "$runtime/novnc" >/dev/null 2>&1

python3 -m http.server "$port" --bind 127.0.0.1 --directory "$runtime/novnc" >"$runtime/novnc.log" 2>&1 &
novnc_pid=$!
qemu-system-x86_64 \
  -name endeavor-alpha-review \
  -accel kvm:tcg \
  -m 2048 -smp 2 \
  -drive file="$iso",media=cdrom,readonly=on \
  -drive file="$runtime/storage.qcow2",if=virtio \
  -fsdev local,id=review,path="$runtime/share",security_model=none \
  -device virtio-9p-pci,fsdev=review,mount_tag=shared \
  -vnc "127.0.0.1:6,websocket=$vnc_port" \
  -display none >"$runtime/qemu.log" 2>&1 &
qemu_pid=$!

cat >"$runtime/STOP" <<EOF
kill $qemu_pid $novnc_pid
EOF
printf '%s\n' "Candidate: $candidate"
printf '%s\n' "Open: http://127.0.0.1:$port/vnc.html?autoconnect=true&host=127.0.0.1&port=$vnc_port"
printf '%s\n' "VM runtime: $runtime"
printf '%s\n' "After review, stop both processes using: sh $runtime/STOP"
