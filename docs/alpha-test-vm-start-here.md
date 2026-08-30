# EndeavorOSCAL Alpha Review VM

This temporary VM is limited to the Alpha review kit. The guest has a private
copy of the project under `/shared/EndeavorOSCAL`; edits there do not change the
authoritative project checkout.

## Reviewer workflow

1. Use the noVNC sidebar on the left edge of the viewer and choose **Clipboard**.
   Paste each complete command block below into that panel, then return focus to
   the console. This avoids retyping commands in the guest.

2. Mount the supplied review kit and run the bootstrap script:

   ```sh
   mkdir -p /shared && mount -t 9p -o trans=virtio,version=9p2000.L shared /shared && sh /shared/EndeavorOSCAL/scripts/prepare-alpha-review-vm.sh
   ```

3. Run the same retained-evidence validation required by the
   [alpha tester packet](alpha-tester-packet.md):

   ```sh
   . /tmp/endeavor-venv/bin/activate && cd /tmp/endeavor-work && python3 scripts/validate-alpha-workflow.py --review-output /tmp/endeavor-alpha-review
   ```

4. Export the retained report to the host-visible review share, then open
   `mapping-report.html` from that exported directory in the host browser at
   normal zoom:

   ```sh
   cp -a /tmp/endeavor-alpha-review /shared/
   ```

5. Complete `docs/alpha-acceptance-template.md` after reviewing the retained
   evidence. Return the completed record to the project maintainer through the
   approved collaboration channel; do not place credentials or sensitive
   evidence in this VM.

## VM boundaries

- noVNC is bound only to `127.0.0.1:18006` on the host;
- the VM uses a dedicated temporary disk at `/tmp/endeavor-alpha-mvp/storage`;
- the VM mounts only this disposable review-kit snapshot as `/shared`;
- the VM has no access to any systems or storage beyond the review kit and its
  dedicated temporary disk.

The test VM, its exported review output, and its disk can be deleted after
acceptance is recorded.
