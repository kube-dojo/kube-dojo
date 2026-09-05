# Mount namespace lab evidence — #2418

Scope: the mount worked example and Part 4 of the English namespaces module. Network-name ownership, other lab parts, and Ukrainian fidelity remain separate work.

The lead read the bodies of [unshare(1)](https://man7.org/linux/man-pages/man1/unshare.1.html), [mount_namespaces(7)](https://man7.org/linux/man-pages/man7/mount_namespaces.7.html), and [findmnt(8)](https://man7.org/linux/man-pages/man8/findmnt.8.html). Relevant contracts: explicit private propagation; namespace lifetime and persistence; successful full mount-table enumeration. `findmnt` exit 1 can indicate an error, so it is not sufficient evidence of absence. Installed GNU `mktemp --help` and `rmdir --help` were also read to confirm directory creation and empty-directory cleanup behavior.

Independent Fable source/design review accepted the tested Bash interior, with the invocation caveat resolved by an explicit `bash` here-document. This is source/design acceptance, not prose acceptance. The reviewed manuals describe newer releases than the installed utilities; command compatibility below is observed on the stated environment.

On 2026-09-05, the lead ran the candidate in a dedicated kind node (`kindest/node:v1.35.0`) on OrbStack, as UID 0. Installed versions: util-linux `unshare` and `findmnt` 2.38.1; kernel `7.0.14-orbstack-00380-ga7e0a2dc9535`. The final lesson block was extracted and executed at 17:15:40 UTC. Its interior SHA256 is `9fade2f36c60bec19327679c363e5f9d77d9034d96a2f06f5435b68b14d37201`.

Observed cases: normal exit 0; invalid tmpfs mount option exit 32; child self-TERM exit 143; parent self-TERM after child exit 143; non-empty cleanup refusal exit 1 with the injected file preserved. A separate pre-existing `/tmp/kd-mnt-lab` sentinel remained unchanged while a fresh suffixed directory was used. Every test-owned directory and sentinel was removed after inspection. Exit numbers are observations, not a portable error-code specification.

Normal output showed distinct parent/child namespace identifiers, `tmpfs` with `private` propagation inside the child, and no matching mount or file in the parent after the child exited. There was no explicit unmount before the parent check. This is sequential observation, not simultaneous inspection of both namespaces.

Limits: no `sudo` binary in the node; no sudo-policy test, non-root exercise, concurrent terminal Ctrl-C test, SIGKILL-cleanup guarantee, or general claim about other Linux environments. No background process or persistent namespace was created. The cleanup trap can report failure rather than remove a non-empty directory. Numeric rubric scores or these bounded executions do not establish whole-module correctness.
