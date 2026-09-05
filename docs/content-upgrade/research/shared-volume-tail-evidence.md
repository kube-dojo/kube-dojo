# Shared-volume reader: missing-file evidence

Scoped evidence for #2418, parent #2279, epic #2272. Only the `shared-volume-demo` reader flag and its explanation are accepted by this packet; no IPC, signalling, whole-module or Ukrainian acceptance.

## Inspected implementation and observed tests

The tested `busybox:1.36` image resolved to digest `sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662` on arm64. Its own `tail --help` identified BusyBox1.36.1 and described `-F` as retaining retry behavior. This binary help is the primary implementation evidence; an unversioned web option list did not describe the tested binary correctly. No GNU flag equivalence or rotation behavior is inferred.

On September5,2026, isolated Docker/OrbStack runs showed `tail -f` exiting1 when its file was absent. A second run created a file after one second; `tail -F` printed the supplied line. The harness deliberately ended that persistent observer after four seconds, recording143. This is a controlled observation, not an application failure or a reliability measurement.

A dedicated Kubernetes1.35.0 node test used two ordinary containers sharing an `emptyDir`. To expose the missing-file condition, the writer waited five seconds before creating the file, and both comparison pods used `restartPolicy: Never`. The `-f` reader exited1; the `-F` reader printed the supplied lines, remained running and had zero restarts. This modified test does not measure the unmodified example's failure frequency or its default restart behavior.

After independent source/design review, the exact proposed manifest was tested separately: the only change from the published YAML was reader `-f` to `-F`. Kubernetes admitted the default `Always` policy; both containers were running with zero restarts, and the sidecar printed the writer's timestamp. This single run does not guarantee startup order or future health. Test environment: node1.35.0, containerd2.2.0, kernel7.0.14-orbstack-00380-ga7e0a2dc9535, arm64. No claim for other architectures or image digests.

Each test namespace was created with a generated name. The lead checked its recorded UID before deletion and verified absence afterward. For the comparison test, absence verification was a separate post-harness check, explicitly recorded as such; the exact-candidate harness includes its own wait and absence check. No pre-existing namespace was removed.

## Review and disposition

Grok SOURCE/DESIGN review (session `885aec63-a575-4095-85cd-83d4136feb48`) accepted the bounded flag change before prose. It correctly flagged that the original comparison harness itself did not record the lead's later cleanup check or node metadata; the receipt now distinguishes those observations from harness output. The exact-candidate receipt records its own cleanup and environment observations. Subsequent prose review must inspect both the lesson change and these limits.

Use `-F` to tolerate a file that is not yet present, and explain the possible initial open error. Keep two ordinary containers, the writer command, volume and mount paths. Do not describe retrying as a startup-order guarantee, health check, default restart test, or native-sidecar lifecycle change. Writer-side `touch` alone does not order the reader's start. No production readiness or learner-success outcome was measured.
