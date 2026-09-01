# Disposable verification VM: build and configuration record

> Status: **inactive by design**. This document records the prior alpha review
> environment so a future frozen-candidate review can be reproduced without
> enabling Docker or starting a VM at handoff.

## Purpose and non-goals

The VM is a disposable, loopback-only reviewer workspace. It validates a
frozen Endeavor checkout and exports the retained workflow evidence for host
browser/accessibility review. It is not a target evaluator, a production
environment, a Docker workload, or a connection to another host.

## Build recipe

The host launcher is `scripts/launch-alpha-review-vm.sh <git-ref>`. Before it
starts anything, it resolves the supplied ref to an immutable commit, creates
a temporary review-kit snapshot, and writes that SHA to
`CANDIDATE-COMMIT.txt`. It then obtains:

- Alpine Linux `3.24.0` virtual ISO, verified against its recorded SHA-256;
- noVNC `v1.6.0`, verified as commit `a8dfd6a3ea3c74244f5ebdaa5a7f1023007a7820`; and
- a 4 GiB qcow2 disk under the explicit temporary runtime directory.

The guest is Alpine Linux, runs as its local `root` only because package setup
requires it, and receives the frozen review kit through a read-only 9p mount
tagged `shared`. A separate writable 9p mount tagged `export` receives only
the retained review output. The guest-side bootstrap is
`scripts/prepare-alpha-review-vm.sh`.

The source checks protect the launch inputs before QEMU or noVNC executes.
The launcher now requires a hash-manifested offline APK, Python-wheel, and npm
cache by default. Its `ENDEAVOR_VM_ALLOW_ONLINE_BOOTSTRAP=1` escape hatch is
legacy-only and cannot produce GA evidence.

## Network and storage boundaries

| Surface | Configuration |
| --- | --- |
| noVNC viewer | `127.0.0.1:18006` only |
| QEMU VNC websocket | `127.0.0.1:5706` only |
| Guest networking | Absent by default; legacy online bootstrap requires an explicit host opt-in and is not GA eligible |
| Candidate mount | Read-only `/shared`, containing the frozen snapshot, wrappers, and validated offline cache |
| Export mount | Writable `/export`, empty at launch and limited to retained review artifacts |
| Guest disk | `/tmp/endeavor-alpha-mvp/storage.qcow2` |
| Host source checkout | copied into the review kit; never mounted read/write |
| Docker | not used by this VM workflow; no Docker permission is required |

The launcher prefers KVM only when the host exposes it as readable and
writable; otherwise it uses QEMU software emulation. This must be recorded in
the acceptance evidence, not assumed.

noVNC and VNC have no authentication. Loopback binding prevents direct remote
access, but local host processes able to reach the listener can view the
session. The Alpine live guest uses its local root account without a password;
that account is not a host credential.

## Reviewer commands

After the launcher has been deliberately run for an exact candidate, the
reviewer enters these commands separately in noVNC:

```sh
mkdir -p /shared
```

```sh
mount -t 9p -o ro shared /shared
```

```sh
mkdir -p /export && mount -t 9p export /export
```

```sh
sh /shared/s
```

```sh
sh /shared/v
```

```sh
sh /shared/e
```

`s` bootstraps only from the verified offline cache, `v` performs
retained-evidence validation, and `e` exports only the retained review files.
Open
the exported report on the host, not from the guest browser.

## Inactive-state verification

At this handoff, no new VM should be started. Before later use, confirm:

```sh
test ! -e /tmp/endeavor-alpha-mvp && echo "No prior VM runtime"
pgrep -af 'qemu-system-x86_64.*endeavor-alpha|novnc_proxy.*endeavor-alpha' || true
```

The expected clean state is no runtime directory and no matching process. If a
prior review exists, retain its acceptance record first, then use the printed
`STOP` command and remove only its explicit `/tmp/endeavor-alpha-mvp` runtime.

## Cleanup and evidence retention

Keep only the completed acceptance record and intentionally retained review
output required by that record. Delete the guest disk, staged review kit, ISO,
and noVNC checkout after acceptance. Never place credentials, raw scan output,
or production evidence in the guest or its shared directory.
