# EndeavorOSCAL Alpha Review VM

This temporary VM is limited to the Alpha review kit. The guest has a private
copy of the project under `/shared/EndeavorOSCAL`; edits there do not change the
authoritative project checkout.

## Reviewer workflow

1. Open a terminal in the guest, mount the supplied review kit, and open this
   guide:

   ```sh
   mkdir -p /shared
   mount -t 9p -o trans=virtio,version=9p2000.L shared /shared
   cd /shared/EndeavorOSCAL
   sed -n '1,240p' docs/alpha-tester-packet.md
   ```

2. Prepare the disposable guest workspace. The shared review kit is intentionally
   read-only, so dependency installation and review output remain inside the VM:

   ```sh
   cat >/etc/apk/repositories <<'EOF'
   https://dl-cdn.alpinelinux.org/alpine/v3.24/main
   https://dl-cdn.alpinelinux.org/alpine/v3.24/community
   EOF
   apk update
   apk add --no-cache python3 py3-pip py3-virtualenv nodejs npm git
   cp -a /shared/EndeavorOSCAL /tmp/endeavor-work
   cd /tmp/endeavor-work
   python3 -m venv /tmp/endeavor-venv
   . /tmp/endeavor-venv/bin/activate
   python3 -m pip install --disable-pip-version-check -r requirements.txt
   npm ci
   ```

3. Follow the **Review procedure** in the packet. The exact validation command
   is:

   ```sh
   python3 scripts/validate-alpha-workflow.py --review-output /tmp/endeavor-alpha-review
   ```

4. Complete `docs/alpha-acceptance-template.md` after reviewing the retained
   evidence. Return the completed record to the project maintainer through the
   approved collaboration channel; do not place credentials or sensitive
   evidence in this VM.

## VM boundaries

- noVNC is bound only to `127.0.0.1:18006` on the host;
- the VM uses a dedicated temporary disk at `/tmp/endeavor-alpha-mvp/storage`;
- the VM mounts only this review-kit snapshot as `/shared`;
- the VM has no access to any systems or storage beyond the review kit and its
  dedicated temporary disk.

The test VM and its disk can be deleted after acceptance is recorded.
