# EndeavorOSCAL Alpha Review VM

This temporary VM is limited to the Alpha review kit. The guest receives a
read-only frozen project snapshot under `/shared/EndeavorOSCAL`; it cannot edit
that snapshot. Retained review files are exported only through `/export`.

## Maintainer launch

From the clean, frozen candidate checkout on the host, start a new guest with:

```bash
ENDEAVOR_VM_OFFLINE_CACHE=/absolute/path/to/verified-offline-cache sh scripts/launch-alpha-review-vm.sh HEAD
```

The launcher stages only the selected Git commit under `/shared`, validates the
offline cache against that exact commit, binds noVNC only to loopback, and
prints the viewer URL and exact candidate SHA. It needs `qemu-base`, `curl`,
`git`, and Python 3 on the host. It does not reuse a prior VM runtime; stop the
printed process IDs and remove the explicit temporary runtime only after the
review record is retained. Strict mode has no guest network device. The legacy
online escape hatch is not eligible for GA evidence. noVNC is unauthenticated
and must remain loopback-only.

## Reviewer workflow

1. Use the noVNC sidebar on the left edge of the viewer and choose **Clipboard**.
   Paste the following short commands **one at a time**. The console can drop
   portions of long pasted commands, so do not paste multi-command lines.

2. Create the mount point and mount the supplied review kit:

   ```sh
   mkdir -p /shared
   ```

   ```sh
   mount -t 9p -o ro shared /shared
   ```

   ```sh
   mkdir -p /export && mount -t 9p export /export
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
- noVNC/VNC has no authentication, so any local host process able to reach the
  loopback listener can view the session;
- the VM uses a dedicated temporary disk at `/tmp/endeavor-alpha-mvp/storage`;
- the VM mounts a read-only candidate snapshot as `/shared` and a separate
  writable export directory as `/export`;
- strict review mode has no QEMU network device;
- the cache, candidate snapshot, and exported review files are disposable and
  never alter the authoritative checkout; and
- the guest's local root account has no password and is not a host credential.

The test VM, its exported review output, and its disk can be deleted after
acceptance is recorded.
