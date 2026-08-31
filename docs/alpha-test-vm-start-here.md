# EndeavorOSCAL Alpha Review VM

This temporary VM is limited to the Alpha review kit. The guest has a private
copy of the project under `/shared/EndeavorOSCAL`; edits there do not change the
authoritative project checkout.

## Maintainer launch

From the clean, frozen candidate checkout on the host, start a new guest with:

```bash
sh scripts/launch-alpha-review-vm.sh HEAD
```

The launcher stages only the selected Git commit under `/shared`, binds noVNC
only to loopback, and prints the viewer URL and exact candidate SHA. It needs
`qemu-base`, `curl`, `git`, and Python 3 on the host. It does not reuse a prior
VM runtime; stop the printed process IDs and remove the explicit temporary
runtime only after the review record is retained.

## Reviewer workflow

1. Use the noVNC sidebar on the left edge of the viewer and choose **Clipboard**.
   Paste the following short commands **one at a time**. The console can drop
   portions of long pasted commands, so do not paste multi-command lines.

2. Create the mount point and mount the supplied review kit:

   ```sh
   mkdir -p /shared
   ```

   ```sh
   mount -t 9p shared /shared
   ```

3. Run the host-supplied setup wrapper:

   ```sh
   sh /shared/s
   ```

   If a prior setup attempt failed before printing **“Alpha review workspace is
   ready”**, use the fresh-workspace retry wrapper instead:

   ```sh
   sh /shared/r
   ```

4. Run the same retained-evidence validation required by the
   [alpha tester packet](alpha-tester-packet.md):

   ```sh
   sh /shared/v
   ```

5. Export the retained report to the host-visible review share, then open
   `mapping-report.html` from that exported directory in the host browser at
   normal zoom:

   ```sh
   sh /shared/e
   ```

6. Complete `docs/alpha-acceptance-template.md` after reviewing the retained
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
