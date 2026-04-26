---
title: "Module 4.5: Runtime Security"
slug: platform/disciplines/reliability-security/devsecops/module-4.5-runtime-security
sidebar:
  order: 7
---

# Module 4.5: Runtime Security

> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 45-60 min

## Prerequisites

Before starting this module:

- **Required**: [Module 4.4: Supply Chain Security](../module-4.4-supply-chain-security/) because runtime defense assumes you already understand image provenance, signing, and build-time controls.
- **Required**: Kubernetes basics, including Pods, Deployments, namespaces, Services, labels, and how controllers replace failed Pods.
- **Recommended**: [Security Principles Track](/platform/foundations/security-principles/) because runtime security is an applied version of least privilege, blast-radius reduction, and defense in depth.
- **Helpful**: Linux process, file permission, capability, and syscall concepts because container runtime security is ultimately enforced by the kernel.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** a Kubernetes workload's runtime attack surface by tracing how an attacker could move from initial code execution to persistence, privilege escalation, or lateral movement.
- **Design** layered runtime controls using security contexts, Pod Security Standards, seccomp, and NetworkPolicy so that a compromised container has fewer useful options.
- **Implement** runtime detection with Falco-style behavioral rules and distinguish high-signal alerts from normal operator activity.
- **Debug** common runtime-security failures, including rejected Pods, broken DNS after default-deny egress, noisy shell alerts, and workloads that need narrowly scoped Linux capabilities.
- **Build** a containment workflow that preserves useful evidence, limits blast radius, and feeds lessons back into build, deployment, and policy controls.

---

## Why This Module Matters

At 02:30, a platform engineer receives a cost alert that does not look like a security incident at first. The cluster autoscaler has added nodes twice in under an hour, CPU is pinned across a frontend Deployment, and the application dashboards still show normal request volume. The image was signed, the deployment passed admission checks, and the pipeline had no suspicious changes, so the obvious build-time explanations do not fit.

By 03:10, the team discovers the uncomfortable truth: the workload was compromised after deployment. An application bug allowed remote code execution, the attacker wrote a miner into a writable directory, and outbound traffic to a mining pool was allowed because the namespace had no egress policy. The supply chain controls helped prove the image was not tampered with before deployment, but they did not stop new behavior that appeared after the container started.

Runtime security exists for that gap between "we shipped something clean" and "the process is still behaving safely right now." It assumes prevention can fail, then asks what the workload can do, what it can reach, what the kernel will allow, what the cluster will admit, what suspicious behavior will be detected, and how responders will contain the workload without destroying the evidence they need. A senior platform team treats runtime security as an operating model, not as one tool installed after an audit finding.

The practical goal is not to make every container impossible to compromise. That is not a credible standard for real systems. The goal is to make compromise less useful, easier to detect, harder to spread, and faster to recover from. This module builds that model in layers: first the attack path, then workload hardening, then network containment, then behavioral detection, and finally incident response.

---

## Runtime Threat Model: Start With What The Attacker Can Do

Runtime security begins after a workload is running, so the first question is not "is the image clean" but "what can this process do if an attacker gains control of it." A container is not a security boundary by itself; it is a process tree with namespaces, cgroups, filesystem mounts, Linux capabilities, runtime defaults, and Kubernetes configuration wrapped around it. Those layers can reduce risk, but only if you deliberately configure them.

```ascii
+--------------------------------------------------------------------+
|                       RUNTIME ATTACK PATH                           |
|                                                                    |
|  Initial Access       Execution          Persistence                |
|  +-------------+      +-------------+    +-------------+            |
|  | App exploit |----->| Run shell   |--->| Drop binary |            |
|  | or stolen   |      | or command  |    | or modify   |            |
|  | credential  |      | in Pod      |    | filesystem  |            |
|  +-------------+      +-------------+    +-------------+            |
|                              |                    |                 |
|                              v                    v                 |
|  Lateral Movement      Privilege Escalation    Data Exfiltration    |
|  +-------------+      +-------------+          +-------------+      |
|  | Reach API,  |<-----| Abuse caps, |--------->| Read secrets|      |
|  | DB, cache,  |      | host paths, |          | and send to |      |
|  | or metadata |      | or syscalls |          | attacker    |      |
|  +-------------+      +-------------+          +-------------+      |
|                                                                    |
|  Runtime controls reduce options, detect behavior, and guide        |
|  containment after the workload is already live.                    |
+--------------------------------------------------------------------+
```

A useful threat model separates three ideas that are often blurred together. A **preventive control** blocks an action before it succeeds, such as Pod Security Admission rejecting a privileged Pod or seccomp denying a dangerous syscall. A **detective control** observes suspicious behavior, such as Falco alerting when a shell appears inside a production container. A **responsive control** changes the environment after detection, such as applying a quarantine label that triggers a deny-all NetworkPolicy.

| Control Layer | Primary Question | Example Control | Failure Mode If Missing |
|---|---|---|---|
| Container identity | Who does the process run as, and what kernel privileges does it hold? | `runAsNonRoot`, dropped capabilities, no privilege escalation | A compromised process can write broadly, bind privileged ports, or use unnecessary kernel powers. |
| Filesystem | Can the process modify its own runtime environment? | Read-only root filesystem plus explicit writable volumes | Malware can persist in writable paths or replace application files inside the container. |
| Admission | Which Pod specs are allowed into a namespace? | Pod Security Standards with `restricted` enforcement | A team can accidentally deploy privileged or host-mounted workloads. |
| Network | What can the compromised Pod reach? | Default-deny NetworkPolicy with explicit allow rules | Initial compromise becomes database access, metadata access, or outbound command-and-control. |
| Syscalls | Which kernel operations can the process request? | `RuntimeDefault` or custom seccomp profiles | Dangerous kernel operations remain available even when the application never needs them. |
| Behavior detection | What runtime behavior is suspicious in context? | Falco, Tetragon, KubeArmor, or equivalent runtime sensors | The first confirmed incident signal may be a bill, a customer report, or data loss. |
| Response | What happens in the first minutes after detection? | Quarantine policy, evidence capture, secret rotation | Responders delete Pods too quickly, lose evidence, and miss the real entry point. |

The important design habit is to map controls to attacker choices. If an attacker can execute a command, `readOnlyRootFilesystem` makes it harder to drop tooling. If they can reach the network, egress policy can stop direct access to internal services or external endpoints. If they try to spawn a shell, runtime detection gives responders a signal. No single layer is the strategy; the strategy is making every next step harder or louder.

> **Active check:** Imagine a production API Pod that runs as root, has a writable root filesystem, allows all egress, and has no runtime detection. Which two attacker actions would you expect first after code execution, and which control in the table would interrupt each action?

A beginner mistake is to think runtime security starts with installing Falco. A senior practitioner starts by asking what a normal workload should be able to do, then removes permissions and network paths that do not support that behavior. Detection is still essential, but detection works best when the environment is already constrained enough that unusual behavior stands out.

The rest of the module follows that order. First, harden the workload so the process has fewer useful privileges. Next, contain the network so compromise does not automatically become lateral movement. Then, add behavioral detection to catch actions that static policy cannot fully prevent. Finally, practice a response flow that preserves evidence and improves the system after the incident.

---

## Harden Workloads Before They Run

Kubernetes runtime hardening starts in the Pod spec because the Pod spec is what admission controllers and kubelets can evaluate. A Dockerfile might contain a non-root `USER`, but Pod Security Standards evaluate the Kubernetes object, not your intent. If the security properties matter, declare them explicitly in the Pod or workload template.

```ascii
+--------------------------------------------------------------------+
|                       POD HARDENING STACK                           |
|                                                                    |
|  Namespace Policy                                                  |
|  +--------------------------------------------------------------+  |
|  | Pod Security Admission: baseline, restricted, audit, warn     |  |
|  +-----------------------------+--------------------------------+  |
|                                |                                   |
|  Pod Spec                      v                                   |
|  +--------------------------------------------------------------+  |
|  | securityContext: runAsNonRoot, runAsUser, fsGroup, seccomp    |  |
|  +-----------------------------+--------------------------------+  |
|                                |                                   |
|  Container Spec                v                                   |
|  +--------------------------------------------------------------+  |
|  | allowPrivilegeEscalation: false, readOnlyRootFilesystem,      |  |
|  | capabilities.drop: [ALL], specific writable volume mounts     |  |
|  +-----------------------------+--------------------------------+  |
|                                |                                   |
|  Linux Kernel                  v                                   |
|  +--------------------------------------------------------------+  |
|  | UID/GID checks, capabilities, seccomp syscall filtering       |  |
|  +--------------------------------------------------------------+  |
+--------------------------------------------------------------------+
```

Here is a hardened Pod that is intentionally boring. It runs as a non-root user, drops every Linux capability, blocks privilege escalation, uses the runtime's default seccomp profile, and makes the root filesystem read-only. Because most applications still need somewhere to write temporary files, the manifest adds an explicit `emptyDir` mounted at `/tmp` rather than leaving the whole image filesystem writable.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: runtime-demo
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
---
apiVersion: v1
kind: Pod
metadata:
  name: secure-web
  namespace: runtime-demo
  labels:
    app: secure-web
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 101
    runAsGroup: 101
    fsGroup: 101
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: nginx
      image: nginxinc/nginx-unprivileged:stable
      ports:
        - containerPort: 8080
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
  volumes:
    - name: tmp
      emptyDir: {}
    - name: cache
      emptyDir: {}
    - name: run
      emptyDir: {}
```

Apply it in a cluster where you have permission to create a namespace. The first command creates both the namespace and the Pod, while the second command verifies that the Pod passed restricted admission and reached `Running` or `Completed` depending on timing.

```bash
kubectl apply -f secure-web.yaml
kubectl get pod secure-web -n runtime-demo -o wide
```

The hardened fields are not decorative. `runAsNonRoot` prevents accidental root execution, while `runAsUser` makes the intended UID explicit. `allowPrivilegeEscalation: false` blocks setuid and related escalation paths. `capabilities.drop: [ALL]` removes kernel privileges that are often unnecessary for application code. `readOnlyRootFilesystem: true` turns many "drop a binary and run it" attack paths into failed writes unless the attacker finds a writable mount.

| Setting | What It Changes | Why It Matters | Common Trade-Off |
|---|---|---|---|
| `runAsNonRoot: true` | Requires the container process to run without UID 0. | Many privilege escalation paths assume root inside the container. | Images that were built with root-owned paths may fail until ownership is fixed. |
| `runAsUser` and `runAsGroup` | Pins the runtime UID and GID instead of relying only on image metadata. | Admission and reviewers can see the intended identity directly in the workload spec. | Shared volumes may need `fsGroup` or adjusted file ownership. |
| `allowPrivilegeEscalation: false` | Prevents a process from gaining more privileges than its parent. | Setuid binaries and similar paths become less useful to an attacker. | Some legacy images rely on privilege-changing startup scripts. |
| `capabilities.drop: [ALL]` | Removes Linux capabilities unless explicitly added back. | A non-root process can still be dangerous if it keeps powerful capabilities. | Rare workloads need specific additions such as `NET_BIND_SERVICE`. |
| `readOnlyRootFilesystem: true` | Prevents writes to the image filesystem. | Dropped tools, modified app files, and persistence attempts become harder. | The app must use explicit writable mounts for cache, temp, and runtime files. |
| `seccompProfile: RuntimeDefault` | Applies the container runtime's default syscall filter. | The process loses access to syscalls that most containers do not need. | Unusual runtimes or debugging tools may require a custom profile. |
| `privileged: false` | Keeps the container from receiving broad host-level privileges. | A privileged container is close to host access in many practical scenarios. | Some node agents need elevated access and should be isolated from app namespaces. |

Linux capabilities deserve special attention because they explain why "non-root" is necessary but not sufficient. Linux splits some root powers into separate capabilities, so a process can be UID 1000 and still hold a capability that lets it perform sensitive operations. The safest default is to drop all capabilities, then add back only the one that a workload can justify.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-low-port
  namespace: runtime-demo
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 101
    runAsGroup: 101
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: nginxinc/nginx-unprivileged:stable
      ports:
        - containerPort: 8080
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
  volumes:
    - name: tmp
      emptyDir: {}
    - name: cache
      emptyDir: {}
    - name: run
      emptyDir: {}
```

The example chooses a better design than adding a capability: run the container on port `8080` and map the Service to port `80`. That keeps the container unprivileged while preserving the external interface users expect. Adding `NET_BIND_SERVICE` can be appropriate in some environments, but changing the internal container port is usually simpler and safer for ordinary web services.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: secure-web
  namespace: runtime-demo
spec:
  selector:
    app: secure-web
  ports:
    - name: http
      port: 80
      targetPort: 8080
      protocol: TCP
```

| Capability | What It Allows | Runtime Security Decision |
|---|---|---|
| `NET_BIND_SERVICE` | Bind to ports below `1024`. | Prefer unprivileged container ports plus a Service mapping; add only when truly needed. |
| `NET_RAW` | Create raw and packet sockets. | Avoid for applications because it can support network scanning and spoofing behavior. |
| `SYS_PTRACE` | Inspect or trace other processes. | Reserve for controlled debugging workflows, not normal production runtime. |
| `SYS_ADMIN` | A broad collection of administrative operations. | Treat as a near-root escape hatch and avoid in application workloads. |
| `CHOWN` | Change file ownership. | Usually unnecessary after images and volumes are prepared correctly. |
| `DAC_OVERRIDE` | Bypass discretionary file permission checks. | Dangerous for applications because it weakens filesystem boundaries. |

> **Pause and predict:** If a Pod sets `runAsNonRoot: true` but the image starts as UID `0`, what should happen when the kubelet tries to start the container? Write down your prediction before reading the next paragraph.

The container should fail to start because the runtime cannot satisfy the declared security requirement. This is a useful failure, not a nuisance. It exposes a mismatch between the image and the workload spec before the application enters production, and it gives the team a precise remediation path: rebuild the image with a non-root user or set a valid non-root `runAsUser` that works with the image's filesystem permissions.

Pod Security Standards move this from a per-manifest habit to a namespace-level policy. The `privileged` profile is intentionally open, `baseline` blocks common privilege escalation paths, and `restricted` reflects the hardened posture most application namespaces should work toward. In Kubernetes 1.35 and current supported releases, Pod Security Admission uses namespace labels to enforce, warn, or audit these profiles.

```ascii
+--------------------------------------------------------------------+
|                    POD SECURITY STANDARD LEVELS                     |
|                                                                    |
|  Privileged                                                        |
|  +--------------------------------------------------------------+  |
|  | No meaningful restrictions. Use for trusted system workloads  |  |
|  | only when lower-privilege designs cannot work.                |  |
|  +--------------------------------------------------------------+  |
|                               |                                    |
|                               v                                    |
|  Baseline                                                          |
|  +--------------------------------------------------------------+  |
|  | Blocks broad known privilege escalation paths while allowing  |  |
|  | many ordinary application patterns.                            |  |
|  +--------------------------------------------------------------+  |
|                               |                                    |
|                               v                                    |
|  Restricted                                                        |
|  +--------------------------------------------------------------+  |
|  | Enforces current Pod hardening expectations for application   |  |
|  | workloads, including non-root and seccomp requirements.       |  |
|  +--------------------------------------------------------------+  |
+--------------------------------------------------------------------+
```

| Check | Baseline | Restricted | Why The Difference Matters |
|---|---|---|---|
| `privileged: false` | Required | Required | Privileged containers can cross container boundaries in ways applications should not need. |
| `hostNetwork: false` | Required | Required | Host networking weakens network isolation and can bypass assumptions in policy design. |
| `hostPID: false` | Required | Required | Host PID access lets a container observe or interact with host processes. |
| `hostIPC: false` | Required | Required | Host IPC access expands visibility into host-level shared memory and process communication. |
| `allowPrivilegeEscalation: false` | Not always required | Required | Restricted treats privilege escalation prevention as a normal application baseline. |
| `runAsNonRoot: true` | Not always required | Required | Restricted requires explicit non-root intent in the Pod spec. |
| `capabilities.drop: [ALL]` | Not always required | Required | Restricted starts from no capabilities and permits narrow additions only when allowed. |
| `seccompProfile: RuntimeDefault` | Not always required | Required | Restricted expects syscall filtering to be part of ordinary runtime hygiene. |

You can test Pod Security Admission without permanently changing a namespace by using server-side dry run. This command asks the API server whether applying the label would succeed, including admission checks, but it does not persist the label.

```bash
kubectl label namespace runtime-demo \
  pod-security.kubernetes.io/enforce=restricted \
  --dry-run=server \
  -o yaml
```

A senior runtime-security review asks whether the policy is enforceable for the team, not merely whether it is strict. If every third workload breaks under `restricted`, the answer is not to abandon hardening; the answer is to find the specific fields that break, separate system workloads from application namespaces, fix base images, and use `warn` or `audit` during migration. Enforcement works best when teams can see violations before the day a hard gate blocks an urgent deployment.

Seccomp is the next layer below the Kubernetes object model. It filters syscalls, which are the requests a process makes to the Linux kernel. Most applications need ordinary file, network, memory, and process syscalls, but they do not need unrestricted access to every kernel operation. `RuntimeDefault` is the minimum production baseline because it applies the container runtime's maintained default filter without requiring each application team to handcraft a profile.

```ascii
+--------------------------------------------------------------------+
|                         SECCOMP FILTERING                           |
|                                                                    |
|  Application Process                                               |
|          |                                                         |
|          | syscall: read(), write(), connect(), mount(), ptrace()   |
|          v                                                         |
|  +--------------------------------------------------------------+  |
|  | Seccomp Profile                                               |  |
|  |                                                              |  |
|  | read()       -> allow                                         |  |
|  | write()      -> allow                                         |  |
|  | connect()    -> allow                                         |  |
|  | mount()      -> deny or log, depending on profile             |  |
|  | ptrace()     -> deny or log, depending on profile             |  |
|  +--------------------------------------------------------------+  |
|          |                                                         |
|          v                                                         |
|  Linux Kernel                                                      |
+--------------------------------------------------------------------+
```

Custom seccomp profiles are valuable, but they are not the first step for most teams. Start with `RuntimeDefault`, observe whether any application fails, and only move to custom profiles for high-value workloads where the team can test normal behavior thoroughly. A custom profile that is guessed from incomplete traffic can turn into an outage during rare code paths, so profile generation should be treated like performance testing: observe realistic behavior, validate in staging, and roll out gradually.

---

## Contain Traffic With Network Policy

If workload hardening limits what a compromised process can do locally, NetworkPolicy limits what it can reach. Kubernetes networking is permissive by default: a Pod can usually talk to other Pods unless a CNI plugin enforces policies and relevant NetworkPolicy objects select the traffic. That default is convenient for early development and dangerous for production blast radius.

```ascii
+--------------------------------------------------------------------+
|                 DEFAULT CLUSTER NETWORKING BEHAVIOR                 |
|                                                                    |
|      +------------+         +------------+         +------------+   |
|      | Frontend   |<------->| API        |<------->| Database   |   |
|      | app=web    |         | app=api    |         | app=db     |   |
|      +------------+         +------------+         +------------+   |
|             ^                     ^                      ^         |
|             |                     |                      |         |
|             +---------------------+----------------------+         |
|                                                                    |
|  If the frontend is compromised, it may be able to probe the API,   |
|  database, cache, metadata endpoints, and external networks.        |
+--------------------------------------------------------------------+
```

A good policy model starts with "deny by default, then allow known paths." That sounds simple, but it has two details that routinely surprise teams. First, default-deny only affects Pods selected by a NetworkPolicy, so a policy with `podSelector: {}` is a deliberate namespace-wide choice. Second, DNS is egress traffic; if you deny all egress and forget DNS, applications fail in ways that look like service outages rather than security changes.

```ascii
+--------------------------------------------------------------------+
|                 MICROSEGMENTED APPLICATION TRAFFIC                  |
|                                                                    |
|      +------------+         +------------+         +------------+   |
|      | Frontend   |-------->| API        |-------->| Database   |   |
|      | app=web    |  8080   | app=api    |  5432   | app=db     |   |
|      +------------+         +------------+         +------------+   |
|             |                     |                      ^         |
|             | blocked             | DNS allowed          |         |
|             v                     v                      |         |
|      +------------+         +------------+                |         |
|      | Other Pods |         | kube-dns   |----------------+         |
|      +------------+         +------------+                          |
|                                                                    |
|  The policy describes the application graph instead of trusting     |
|  every Pod in the namespace equally.                                |
+--------------------------------------------------------------------+
```

The following policy establishes default deny for both ingress and egress in the `runtime-demo` namespace. It is intentionally severe because the next policies will add back the minimum required paths. Apply it only in a demo namespace unless you have already mapped application dependencies.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: runtime-demo
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

DNS should be restored explicitly. The example below allows Pods in `runtime-demo` to reach CoreDNS in `kube-system` on UDP and TCP port `53`. The namespace selector uses the standard Kubernetes namespace label so the policy is readable and does not depend on an environment-specific namespace UID.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: runtime-demo
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

Now add application-specific ingress. This policy lets only Pods labeled `app: frontend` call Pods labeled `app: api` on port `8080`. Notice that the policy selects the destination Pods with `spec.podSelector`; the `from` block describes allowed sources. Many broken policies come from reversing those two ideas.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow-frontend
  namespace: runtime-demo
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
```

Add the database path the same way. The database does not need to accept traffic from the frontend, job runners, or arbitrary Pods in the namespace. It needs traffic from the API on its database port, and the policy should say exactly that.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-allow-api
  namespace: runtime-demo
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api
      ports:
        - protocol: TCP
          port: 5432
```

| Policy Design Choice | Good Use | Risk To Watch |
|---|---|---|
| Namespace-wide default deny | Establishes a clear baseline for production namespaces. | Breaks hidden dependencies if introduced without discovery and staged rollout. |
| Explicit DNS egress | Keeps service discovery working while other egress stays denied. | Label differences across DNS deployments can make selectors environment-specific. |
| App-to-app allow rules | Documents the intended service graph in Kubernetes objects. | Missing labels or drifting labels can silently disconnect services. |
| External egress allowlist | Limits command-and-control and data exfiltration paths. | Broad `0.0.0.0/0` exceptions can recreate the original risk. |
| Separate ingress and egress policies | Makes traffic direction clear during review and troubleshooting. | Too many small policies can become hard to reason about without naming conventions. |
| CNI enforcement verification | Confirms policy objects actually affect traffic. | NetworkPolicy resources may be accepted by the API but ignored by an unsupported CNI. |

> **Active check:** Your team applies default-deny egress and the application immediately reports database hostname resolution failures. What is the fastest hypothesis to test, and which policy from this section would you inspect first?

The fastest hypothesis is that DNS egress was denied or incorrectly selected. Check whether the `allow-dns` policy exists, whether it selects the affected Pod, whether the DNS namespace label matches the cluster, and whether both UDP and TCP `53` are allowed. After DNS works, continue testing the database path separately so you do not mistake name resolution failure for database reachability failure.

A worked example makes the troubleshooting sequence concrete. Suppose a frontend Pod should call the API, but the request times out after a default-deny rollout. You should verify labels before rewriting policy because NetworkPolicy is label-driven and a single typo can make a correct-looking policy select nothing.

```bash
kubectl get pod -n runtime-demo --show-labels
kubectl describe networkpolicy api-allow-frontend -n runtime-demo
kubectl run netcheck -n runtime-demo \
  --image=curlimages/curl:8.10.1 \
  --labels=app=frontend \
  --restart=Never \
  --command -- sleep 3600
kubectl exec -n runtime-demo netcheck -- curl -sS -m 5 http://api:8080/health
```

If the `netcheck` Pod has label `app=frontend` and the API Pods have label `app=api`, the request should be allowed by `api-allow-frontend`. If it still times out, inspect the Service selector, endpoint readiness, CNI behavior, and whether an egress policy also selects the frontend. NetworkPolicy debugging is methodical: confirm source label, destination label, port, direction, namespace, then CNI enforcement.

External egress deserves a separate decision because it is where many runtime incidents turn into data loss or infrastructure abuse. Some workloads genuinely need outbound HTTPS to a payment provider, package registry, or managed API. That does not mean every Pod needs unrestricted internet access. Prefer narrow egress based on DNS-aware CNI features when available, or carefully scoped CIDR rules when the provider publishes stable ranges.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-allow-api-and-dns-only
  namespace: runtime-demo
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: api
      ports:
        - protocol: TCP
          port: 8080
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

A senior review of NetworkPolicy asks whether the policies match the real application graph. That means policies should be tested as part of deployment, not only inspected as YAML. Use temporary diagnostic Pods, application health checks, and CNI observability to prove allowed traffic works and denied traffic is actually denied. A policy that looks strict but is not enforced by the CNI gives a false sense of security, which is worse than a visible gap.

---

## Detect Runtime Behavior With Falco And Related Tools

Preventive controls reduce the attacker's room to maneuver, but they cannot fully describe every malicious behavior. Runtime detection watches what processes actually do. In Kubernetes, that usually means observing syscalls, process execution, file access, network connections, Kubernetes audit events, or a combination of those signals.

```ascii
+--------------------------------------------------------------------+
|                    RUNTIME DETECTION ARCHITECTURE                   |
|                                                                    |
|  Linux Kernel / Kubernetes API                                      |
|  +--------------------------------------------------------------+  |
|  | syscalls, process starts, file opens, network connects,       |  |
|  | container metadata, Kubernetes audit events                    |  |
|  +-----------------------------+--------------------------------+  |
|                                |                                   |
|                                v                                   |
|  Sensor Layer                                                       |
|  +--------------------------------------------------------------+  |
|  | Falco driver, eBPF programs, audit log collector, or agent     |  |
|  +-----------------------------+--------------------------------+  |
|                                |                                   |
|                                v                                   |
|  Rule Engine                                                        |
|  +--------------------------------------------------------------+  |
|  | Conditions combine behavior with context: namespace, image,    |  |
|  | process name, command line, user, container, and file path      |  |
|  +-----------------------------+--------------------------------+  |
|                                |                                   |
|                                v                                   |
|  Response Channels                                                  |
|  +--------------------------------------------------------------+  |
|  | Logs, SIEM, Slack, PagerDuty, ticket, quarantine automation     |  |
|  +--------------------------------------------------------------+  |
+--------------------------------------------------------------------+
```

Falco is a common starting point because it provides cloud-native runtime detection with a rule language and Kubernetes context. Tetragon is often chosen when teams want deep eBPF-based process and network visibility, especially in Cilium environments. KubeArmor is useful when teams want policy-driven runtime enforcement around process, file, and network behavior. The tool choice matters, but the design question is the same: what behavior is suspicious for this workload, and what context turns a noisy signal into a useful alert?

| Tool Or Approach | Strength | Best Fit | Design Caution |
|---|---|---|---|
| Falco | Mature rule ecosystem for suspicious runtime behavior. | Detecting shells, sensitive file access, unexpected process execution, and known attack patterns. | Rules need tuning by namespace and workload to avoid alert fatigue. |
| Tetragon | eBPF-based visibility into process execution, network events, and policy-aware tracing. | Teams already using Cilium or needing rich runtime observability at scale. | Deep visibility can produce high event volume without careful filters. |
| KubeArmor | Runtime policy and enforcement for process, file, and network actions. | Workloads that benefit from explicit runtime allow or block policies. | Enforcement policies need staged rollout to avoid breaking legitimate behavior. |
| Kubernetes audit logs | API-level visibility into actions such as `exec`, secret reads, or role changes. | Detecting control-plane actions and user-driven Kubernetes operations. | Audit policy must capture the events you care about before the incident. |
| CNI flow logs | Network behavior between workloads and destinations. | Proving or investigating lateral movement and unexpected egress. | Flow data explains connectivity, not process intent, unless correlated with other signals. |

Install Falco in a demo or lab cluster with Helm if your environment allows privileged node-level sensors. Managed clusters vary in what they permit, so treat installation failures as an environment constraint rather than a curriculum failure. The command below uses the eBPF driver, which is a common modern choice.

```bash
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=ebpf \
  --set tty=true
kubectl get pods -n falco
```

A Falco rule combines a condition, an output message, a priority, and tags. The built-in rule set already includes many useful detections, so custom rules should focus on organization-specific context rather than duplicating everything. A shell in a development namespace may be routine debugging; a shell inside a production payment workload at night may be a high-priority incident.

```yaml
- rule: Shell Spawned In Production Container
  desc: Detect an interactive or non-interactive shell process started inside a production container
  condition: >
    spawned_process and
    container and
    k8s.ns.name = "production" and
    proc.name in (bash, sh, dash, zsh, ash)
  output: >
    Shell spawned in production container
    (user=%user.name namespace=%k8s.ns.name pod=%k8s.pod.name
    container=%container.name process=%proc.name parent=%proc.pname
    cmdline=%proc.cmdline)
  priority: WARNING
  tags:
    - container
    - shell
    - production
    - mitre_execution
```

Notice what this rule can and cannot prove. It can detect that a shell process started inside a production container. It cannot, by itself, prove whether the shell came from `kubectl exec`, an application exploit, a startup script, or a compromised dependency. That distinction comes from correlation with Kubernetes audit logs, deployment events, application logs, identity provider logs, and recent operator activity.

Here is a second rule for a cryptomining pattern. It detects known miner process names and command lines that contain mining-pool protocol strings. The rule is useful, but it is not complete because attackers can rename binaries and change arguments. That is why you combine it with read-only filesystems, egress restrictions, CPU anomaly alerts, and investigation workflows.

```yaml
- rule: Cryptocurrency Mining Behavior In Container
  desc: Detect common miner processes or mining pool command-line patterns inside containers
  condition: >
    spawned_process and
    container and
    (
      proc.name in (xmrig, minerd, ethminer) or
      proc.cmdline contains "stratum+tcp" or
      proc.cmdline contains "cryptonight"
    )
  output: >
    Possible cryptocurrency mining in container
    (namespace=%k8s.ns.name pod=%k8s.pod.name container=%container.name
    process=%proc.name parent=%proc.pname cmdline=%proc.cmdline)
  priority: CRITICAL
  tags:
    - cryptomining
    - container
    - mitre_execution
```

> **Pause and predict:** If an attacker renames `xmrig` to `nginx-helper` but still connects to a mining pool using `stratum+tcp`, should the second rule fire? Which part of the condition makes your answer true?

The rule should still fire because the condition checks both process names and command-line content. This demonstrates a useful runtime-detection pattern: combine several weak indicators so one trivial evasion does not make the rule useless. The same principle applies more broadly; a process name, a namespace, a file path, a parent process, and a network destination become more meaningful together than any one field alone.

A worked example shows how detection, prevention, and response fit together. Suppose a frontend vulnerability lets an attacker run commands in a container. In a weak runtime posture, the attacker downloads a miner to `/tmp`, starts it, reaches an external mining pool, and the first visible symptom is a CPU and cost spike. In a stronger posture, the read-only root filesystem limits write locations, NetworkPolicy blocks unknown egress, and Falco alerts on the miner command line or shell activity.

```bash
kubectl top pods -A --sort-by=cpu
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=100
kubectl get networkpolicy -n runtime-demo
kubectl get pod -n runtime-demo -l app=frontend -o wide
```

The investigation sequence matters. Start by identifying the affected workload and signal source, then preserve current state before deleting anything. If you delete the Pod first, the ReplicaSet may create a clean replacement while the evidence disappears. If you isolate first, you can reduce ongoing harm while keeping enough state to understand whether this was an exploit, stolen credential, malicious image, or misused operational access.

| Alert Signal | First Interpretation | Correlate With | Likely Immediate Action |
|---|---|---|---|
| Shell spawned in production | Could be operator debugging or attacker execution. | Audit logs, change tickets, user identity, parent process, time of day. | Confirm authorization, then isolate if unexplained. |
| Miner process or mining protocol | Strong sign of unauthorized compute abuse. | CPU metrics, egress flow logs, filesystem writes, image digest. | Isolate workload, preserve evidence, redeploy clean image after root cause analysis. |
| Sensitive file read | Could be normal app behavior or credential discovery. | Process name, file path, service account permissions, recent deployment. | Investigate access path and rotate exposed secrets if necessary. |
| Unexpected outbound connection | Could be new dependency or exfiltration. | DNS logs, destination reputation, release notes, egress policy changes. | Block destination if unauthorized and review application dependency changes. |
| New executable written | Could be package install, plugin behavior, or malware staging. | Image design, writable mounts, command history, parent process. | Preserve filesystem evidence and tighten write paths. |
| Privileged Pod admitted | Could be approved node agent or policy gap. | Namespace, service owner, admission logs, exception records. | Verify exception or move workload to a controlled system namespace. |

Falco alerts should not go directly from "any warning" to waking a human. The better pattern is severity routing. Critical alerts such as known miner behavior in production can page the on-call responder. Warnings such as shell activity can create a ticket or chat alert unless correlated with other suspicious signals. Notices can feed dashboards and detection tuning. Alert routing is a product decision for the security platform, not just a Helm value.

```yaml
falcosidekick:
  enabled: true
  config:
    slack:
      webhookurl: "https://hooks.slack.com/services/REPLACE/THIS/VALUE"
      channel: "#security-alerts"
      minimumpriority: "warning"
    webhook:
      address: "https://runtime-alert-router.example.internal/falco"
      minimumpriority: "critical"
```

Treat the webhook URL in the example as a placeholder, not a secret to commit. In a real platform, store notification secrets in an approved secret manager or deployment system, and keep alert routing configuration under review like any other production behavior. A runtime security system that leaks its own credentials or floods responders with low-value alerts will lose trust quickly.

Detection quality improves when rules are tied to ownership and expected behavior. A shell in `production` is suspicious, but a shell in a break-glass maintenance namespace may be expected during a documented incident. A database process writing to a data directory is normal, while a web container writing an executable into `/tmp` is suspicious. Runtime security becomes senior-level work when teams stop asking "is this event bad in general" and start asking "is this event legitimate for this workload, in this namespace, at this time, by this identity."

---

## Respond Without Destroying Evidence

Runtime response has a tension that beginners often miss. You want to stop harm quickly, but you also need enough evidence to understand what happened. Deleting a Pod may reduce immediate risk, yet it can erase process lists, writable files, temporary tooling, and logs that explain the entry point. A strong response plan defines the first minutes before the alert happens.

```ascii
+--------------------------------------------------------------------+
|                  RUNTIME INCIDENT RESPONSE LOOP                     |
|                                                                    |
|  Detect                                                            |
|  +-------------+                                                   |
|  | Alert, flow |                                                   |
|  | log, metric |                                                   |
|  +------+------+                                                   |
|         |                                                          |
|         v                                                          |
|  Contain             Preserve             Investigate              |
|  +-------------+     +-------------+      +-------------+          |
|  | Isolate Pod |---->| Capture Pod |----->| Trace entry |          |
|  | or namespace|     | spec, logs, |      | point and   |          |
|  | safely      |     | files, data |      | blast radius|          |
|  +------+------+     +------+------+      +------+------+          |
|         |                   |                    |                 |
|         v                   v                    v                 |
|  Recover             Improve Controls      Verify                  |
|  +-------------+     +-------------+      +-------------+          |
|  | Redeploy    |---->| Patch app,   |---->| Test policy |          |
|  | clean image |     | rules, image |      | and alert   |          |
|  | rotate keys |     | and policies |      | behavior    |          |
|  +-------------+     +-------------+      +-------------+          |
+--------------------------------------------------------------------+
```

The safest first containment move is often network isolation based on a label. You pre-create a policy that denies ingress and egress for Pods labeled `runtime.kubedojo.io/quarantine: "true"`, then responders can isolate a Pod by applying the label. This is faster and less error-prone than writing emergency YAML during an incident.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine-labeled-pods
  namespace: runtime-demo
spec:
  podSelector:
    matchLabels:
      runtime.kubedojo.io/quarantine: "true"
  policyTypes:
    - Ingress
    - Egress
```

With that policy in place, containment becomes a single label operation. The command below changes the Pod's labels, which causes the CNI to enforce the quarantine policy for selected traffic. In a real incident, you would record the time, operator, alert ID, and reason in your incident notes.

```bash
kubectl label pod secure-web -n runtime-demo \
  runtime.kubedojo.io/quarantine=true \
  --overwrite
kubectl get pod secure-web -n runtime-demo --show-labels
```

Evidence capture should happen before deletion when conditions allow. The exact commands depend on your environment and legal requirements, but the core idea is consistent: capture the Pod spec, events, logs, previous logs, relevant runtime alerts, and any writable paths that may contain dropped files. If you have ephemeral containers enabled, `kubectl debug` can help inspect a running Pod without changing the original container image.

```bash
mkdir -p evidence/runtime-demo-secure-web
kubectl get pod secure-web -n runtime-demo -o yaml \
  > evidence/runtime-demo-secure-web/pod.yaml
kubectl describe pod secure-web -n runtime-demo \
  > evidence/runtime-demo-secure-web/describe.txt
kubectl logs secure-web -n runtime-demo \
  > evidence/runtime-demo-secure-web/current.log
kubectl logs secure-web -n runtime-demo --previous \
  > evidence/runtime-demo-secure-web/previous.log
kubectl get events -n runtime-demo \
  --field-selector involvedObject.name=secure-web \
  > evidence/runtime-demo-secure-web/events.log
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=500 \
  > evidence/runtime-demo-secure-web/falco.log
```

If the workload had access to secrets, assume exposure until you can prove otherwise. A process inside the Pod may have been able to read mounted service account tokens, environment variables, application credentials, or files on writable volumes. Secret rotation is not a punishment for the application team; it is a containment step that recognizes the attacker may have copied data before detection.

| Response Decision | Prefer This When | Avoid This When |
|---|---|---|
| Label-based quarantine | The Pod should remain available for evidence collection while network access stops. | The CNI does not enforce NetworkPolicy or the workload can still harm local host resources. |
| Immediate deletion | The workload is actively causing harm that isolation cannot stop. | You have no other evidence source and the Pod contains volatile clues. |
| Scale Deployment to zero | Multiple replicas may be compromised and replacement would recreate risk. | Availability requirements demand a clean replacement first. |
| Roll out known-good image | The entry point is patched or configuration can block the exploit path. | You have not fixed the vulnerability and will redeploy the same weakness. |
| Rotate credentials | The Pod could read secrets, tokens, or outbound credentials. | You have not identified dependent services and rotation would cause unmanaged outage. |
| Add a detection rule | The incident exposed behavior that should be caught next time. | The proposed rule only detects this exact sample and creates noisy false positives. |
| Tighten admission policy | The incident used a preventable Pod spec weakness. | The namespace still contains workloads that cannot pass and need a migration plan. |

> **Active check:** A Falco alert reports a shell in a production Pod, but the release engineer says they ran `kubectl exec` for debugging five minutes earlier. What evidence would you collect before deciding whether this is benign?

You should correlate the alert time, Kubernetes audit logs, the user identity, the Pod name, the command that was executed, the parent process reported by the runtime sensor, and any change or incident ticket authorizing the action. If the shell came from the release engineer and the command matches the maintenance record, you may classify it as expected but still review whether production `exec` needs tighter process controls. If the parent process suggests the application spawned the shell, or the audit trail does not match, treat it as suspicious.

Recovery closes the loop only when the team changes something durable. That could mean patching the vulnerable dependency, rebuilding the image as non-root, adding egress policy, tightening Pod Security labels, improving audit policy, or tuning detection rules. A response that ends with "deleted the Pod" leaves the system waiting for the same attack to work again.

Senior teams also distinguish containment automation from remediation automation. Automatically quarantining a Pod after a critical miner alert may be reasonable in some environments. Automatically deleting every Pod with a shell alert is riskier because it may destroy evidence and disrupt legitimate emergency work. The right automation depends on signal confidence, workload criticality, and the team's ability to observe side effects.

The runtime-security operating model is therefore a feedback loop. Preventive controls reduce the attacker's options, detection identifies suspicious behavior that prevention cannot eliminate, response limits harm while preserving evidence, and post-incident improvements make the next attempt harder or louder. When the loop is working, runtime security becomes part of everyday platform engineering rather than a separate tool owned by a distant security team.

---

## Worked Example: Diagnose And Improve A Cryptominer Incident

This worked example ties the layers together before you solve a similar problem in the hands-on exercise. The scenario starts with symptoms rather than a clean security alert because real incidents often begin as performance, cost, or reliability anomalies. The goal is to practice the reasoning sequence: observe, contain, preserve, explain, and improve.

A production frontend Deployment suddenly consumes much more CPU than its normal baseline. The image digest matches the signed release, no new deployment happened overnight, and the application still returns successful responses. That combination points away from supply-chain tampering and toward runtime compromise or unexpected runtime behavior.

```bash
kubectl top pods -n production --sort-by=cpu
kubectl get deploy frontend -n production -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl get pods -n production -l app=frontend -o wide
```

The first question is whether the high CPU belongs to the expected application process. If you have runtime detection logs, check those first because executing into a compromised Pod can change evidence and may be restricted by policy. If your incident policy permits inspection, capture state before running exploratory commands.

```bash
mkdir -p evidence/production-frontend
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=500 \
  > evidence/production-frontend/falco.log
kubectl get pods -n production -l app=frontend -o yaml \
  > evidence/production-frontend/pods.yaml
kubectl describe pod -n production -l app=frontend \
  > evidence/production-frontend/describe.txt
```

Suppose the Falco logs show a process command line containing `stratum+tcp`, and CPU metrics show all frontend replicas are saturated. The right immediate move is containment, not a long debate about the original exploit. Apply the quarantine label if the policy exists, or use a namespace-level emergency policy if the blast radius is larger.

```bash
kubectl label pod -n production -l app=frontend \
  runtime.kubedojo.io/quarantine=true \
  --overwrite
kubectl get pods -n production -l app=frontend --show-labels
```

After containment, collect evidence from logs and writable paths if allowed by your incident process. This is where earlier hardening pays off. If the root filesystem was read-only and only `/tmp` was writable, you know where to inspect first. If every path was writable, evidence collection becomes broader and less reliable.

```bash
kubectl logs -n production -l app=frontend \
  > evidence/production-frontend/frontend.log
kubectl get events -n production \
  --sort-by=.lastTimestamp \
  > evidence/production-frontend/events.log
```

The improvements should map directly to the observed attack path. If the attacker wrote a binary, make the root filesystem read-only and restrict writable mounts. If the attacker reached a mining pool, add egress restrictions. If the only detection came from cost metrics, add runtime behavior alerts. If the application exploit was the entry point, patch the dependency and add tests or scanning controls upstream.

| Observed Incident Step | Control That Would Have Helped | Why It Helps Next Time |
|---|---|---|
| Application allowed command execution | Dependency patch, input validation, WAF rule, or code fix | Removes or reduces the entry point before runtime controls are needed. |
| Binary written into the container | Read-only root filesystem and explicit writable mounts | Limits where tools can be dropped and makes suspicious writes easier to spot. |
| Miner reached external pool | Default-deny egress with explicit allowed destinations | Converts compute abuse into failed network connections or visible policy violations. |
| CPU spike was the first signal | Falco rule, metrics alert, and CNI flow visibility | Detects behavior earlier and gives responders richer context. |
| Pod was deleted before evidence capture | Quarantine workflow and evidence checklist | Preserves enough state to identify root cause and prevent repeat compromise. |

The key teaching point is that each control answers a specific part of the incident. Do not say "install Falco" as the whole fix if the attacker used unrestricted egress and writable filesystems. Do not say "add NetworkPolicy" as the whole fix if the workload still runs as root with broad capabilities. Runtime security is a chain of small constraints and signals that make the attacker's path narrower.

---

## Did You Know?

1. [**Falco was created at Sysdig in 2016** and donated to CNCF in 2018](https://www.cncf.io/announcements/2024/02/29/cloud-native-computing-foundation-announces-falco-graduation/). Its graduation in the CNCF reflects how important runtime threat detection has become for cloud-native operations.

2. **`CAP_SYS_ADMIN` is often treated as "the new root"** because it covers a very broad set of administrative operations. A container that is non-root but keeps powerful capabilities can still violate least-privilege expectations.

3. **Kubernetes NetworkPolicy objects require an enforcing CNI plugin**. The API server can accept policy YAML even when the cluster networking layer does not enforce those rules, so verification traffic tests are part of the security control.

4. **Pod Security Standards evaluate the Pod spec, not your intentions**. A Dockerfile `USER` instruction is useful, but restricted admission still expects explicit Kubernetes security context fields for many checks.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Treating image signing as runtime security | A signed image can still be exploited after it starts, so runtime behavior may diverge from build-time assurance. | Keep supply-chain controls, then add runtime hardening, network containment, and behavioral detection. |
| Running application containers as root for convenience | Root inside a container increases the usefulness of many exploit paths and often hides image ownership problems. | Build images for non-root execution and declare `runAsNonRoot`, `runAsUser`, and related fields in the Pod spec. |
| Dropping no Linux capabilities | Non-root processes can still hold dangerous kernel privileges when defaults are not tightened. | Use `capabilities.drop: [ALL]` and add back only a specific capability with a documented reason. |
| Enforcing default-deny egress without DNS | Applications fail with confusing name-resolution errors, and teams may roll back the whole policy. | Add an explicit DNS egress policy and test DNS separately from application connectivity. |
| Assuming NetworkPolicy is enforced everywhere | Some clusters accept NetworkPolicy resources without enforcing them, depending on the CNI. | Run connectivity tests and verify the CNI's documented NetworkPolicy support. |
| Sending every runtime alert to a pager | Noisy alerts train responders to ignore the system and hide the genuinely urgent signals. | Route by severity, namespace, workload criticality, and correlation with audit or metric data. |
| Deleting suspicious Pods before collecting evidence | The team may remove the only copy of useful logs, process state, and dropped files. | Prefer quarantine and evidence capture when immediate deletion is not required to stop harm. |
| Writing incident fixes that do not map to the attack path | Generic remediation leaves the original weakness or detection gap in place. | Tie each improvement to a specific observed step: entry, execution, persistence, movement, or exfiltration. |

---

## Quiz: Runtime Security Scenarios

### Question 1

Your team deploys a payment API into a namespace labeled with restricted Pod Security enforcement. The Pod is rejected because `allowPrivilegeEscalation` is not set to `false`, but the developer argues that the container already runs as a non-root user. How should you fix the deployment, and why is the non-root setting not enough by itself?

<details>
<summary>Show Answer</summary>

Fix the Pod template by explicitly setting the required security context fields rather than weakening the namespace policy. A non-root UID reduces risk, but `allowPrivilegeEscalation: false` addresses a different class of behavior: whether the process can gain additional privileges through mechanisms such as setuid binaries.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payment-api
  template:
    metadata:
      labels:
        app: payment-api
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: api
          image: registry.example.com/payment-api:v1.2.3
          ports:
            - containerPort: 8080
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
```

The key reasoning is that runtime hardening is layered. `runAsNonRoot` controls identity, `allowPrivilegeEscalation` controls privilege changes, dropped capabilities control kernel powers, and seccomp controls syscall access. Passing restricted admission requires the Pod spec to declare those properties explicitly.

</details>

### Question 2

A frontend Deployment is compromised through an application bug. The attacker can run commands inside the container, but attempts to write a binary to `/usr/local/bin` fail. They then write to `/tmp` and try to connect to an external mining pool. Which controls are working, which gap remains, and what would you add next?

<details>
<summary>Show Answer</summary>

The read-only root filesystem is working because it blocks writes to `/usr/local/bin`. The remaining writable `/tmp` path is expected if the application needs temporary storage, but it becomes an attacker staging location unless you pair it with detection and network containment. The attempted mining-pool connection shows an egress gap.

Add or tighten default-deny egress, then explicitly allow only required destinations such as the API service and DNS. Add a runtime detection rule for mining process names or mining-pool command-line patterns, and review whether `/tmp` needs execution restrictions through runtime policy tooling where available. Also patch the application bug because runtime controls reduce impact but do not remove the entry point.

</details>

### Question 3

After applying a namespace-wide default-deny NetworkPolicy, an API can no longer connect to `postgres.production.svc.cluster.local`. The database Pod is healthy, and the Service has endpoints. What do you check in order before changing the database policy?

<details>
<summary>Show Answer</summary>

Check DNS first because default-deny egress commonly blocks DNS and makes service names fail before database traffic is attempted. Verify that an `allow-dns` egress policy selects the API Pod, points to the correct DNS namespace and Pod labels, and allows both UDP and TCP port `53`. Then test name resolution from a diagnostic Pod with the same labels as the API.

After DNS works, check the egress policy that selects the API source and the ingress policy that selects the database destination. Confirm source labels, destination labels, port `5432`, namespace selectors if traffic crosses namespaces, and CNI enforcement. Do not rewrite the database policy until you have separated name resolution failure from database reachability failure.

</details>

### Question 4

Falco alerts that a shell was spawned in a production container at the same time an engineer says they were debugging an incident with `kubectl exec`. What evidence determines whether this is expected operator activity or a likely compromise?

<details>
<summary>Show Answer</summary>

Correlate the runtime alert with Kubernetes audit logs, the engineer's identity, the exact Pod name, the command, the timestamp, the incident ticket, and the parent process reported by the runtime sensor. If the audit event shows the engineer performed `pods/exec` against the same Pod at the same time and the action was authorized, classify it as expected but review whether the process should be allowed in production.

If there is no matching audit event, the command line differs, the parent process indicates the application spawned the shell, or other alerts show suspicious file writes or outbound connections, treat the alert as a potential compromise. Isolate the Pod, preserve evidence, and continue investigation before deleting it.

</details>

### Question 5

A developer wants to add `SYS_ADMIN` to a container because a startup script fails with a permission error. The workload is a normal web application, not a node agent or storage driver. How do you evaluate the request and propose a safer path?

<details>
<summary>Show Answer</summary>

Reject `SYS_ADMIN` as the first fix because it grants a broad set of administrative powers that a web application should not need. Ask what operation fails, inspect the exact error, and determine whether the script is trying to change ownership, mount filesystems, write to a root-owned path, or perform another setup task that belongs in the image build or volume preparation process.

A safer path is to fix file ownership during the image build, run the container as a known non-root UID, mount explicit writable directories, and keep `capabilities.drop: [ALL]`. If a capability is truly required, add the narrowest capability that matches the operation, document the reason, and test whether Pod Security Admission allows it in the target namespace.

</details>

### Question 6

Your team installs Falco and immediately receives many shell alerts from development, staging, and production. The security team wants to page on all of them. What routing and tuning strategy would you recommend?

<details>
<summary>Show Answer</summary>

Do not page on every shell alert without context because alert fatigue will make the system less effective. Route by namespace, workload criticality, time, identity, and correlation with other suspicious behavior. For example, a shell in production with no matching audit event can page, a shell in staging can create a ticket, and a shell in development can be logged or posted to a lower-urgency channel.

Tune the rule output so responders see namespace, Pod, container, process, parent process, command line, and user fields. Add allowlists for documented maintenance workflows only when they are narrow and reviewable. Keep a feedback loop so false positives become rule improvements rather than reasons to ignore runtime detection.

</details>

### Question 7

During an incident, an on-call engineer wants to delete a suspicious Pod immediately. CPU usage is high, but the Pod is still reachable and you have a pre-created quarantine NetworkPolicy. What response sequence should you recommend, and when would deletion be justified?

<details>
<summary>Show Answer</summary>

Apply the quarantine label first so NetworkPolicy blocks ingress and egress for the suspicious Pod while preserving evidence. Then capture the Pod spec, describe output, logs, previous logs, events, relevant runtime alerts, and any allowed writable paths according to your incident procedure. After evidence capture, redeploy a known-good version or scale the workload safely based on the root cause and availability requirements.

Immediate deletion is justified when the Pod is causing harm that quarantine cannot stop, such as destructive local activity, host-level risk, or an uncontrolled resource impact that threatens the cluster. Even then, record the reason and collect whatever external evidence remains, such as audit logs, runtime alerts, metrics, and events.

</details>

---

## Hands-On Exercise: Build A Runtime Security Baseline

In this exercise, you will secure a demo namespace with Pod Security Admission, a hardened workload, default-deny networking, DNS restoration, a quarantine policy, and optional Falco detection. The exercise intentionally mirrors the worked example: you will first build preventive controls, then test what breaks, then add detection or response hooks.

### Part 1: Create A Restricted Namespace

Create a namespace that enforces the restricted Pod Security Standard. This makes the namespace reject Pod specs that do not declare the runtime security posture expected for ordinary application workloads.

```bash
kubectl create namespace runtime-demo
kubectl label namespace runtime-demo \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/warn-version=latest \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/audit-version=latest
kubectl get namespace runtime-demo --show-labels
```

Test that an ordinary `kubectl run nginx` style Pod is rejected or warned depending on your cluster version and defaults. The point is to see that admission evaluates the Pod spec before the container starts.

```bash
kubectl run rejected-nginx \
  --image=nginx:stable \
  --namespace=runtime-demo \
  --restart=Never
```

### Part 2: Deploy A Hardened Workload

Create a file named `runtime-demo-secure-web.yaml` with a hardened Pod and Service. The Pod uses an unprivileged NGINX image, a non-root UID, dropped capabilities, a read-only root filesystem, and explicit writable mounts for runtime paths.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-web
  namespace: runtime-demo
  labels:
    app: secure-web
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 101
    runAsGroup: 101
    fsGroup: 101
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: nginx
      image: nginxinc/nginx-unprivileged:stable
      ports:
        - containerPort: 8080
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
  volumes:
    - name: tmp
      emptyDir: {}
    - name: cache
      emptyDir: {}
    - name: run
      emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: secure-web
  namespace: runtime-demo
spec:
  selector:
    app: secure-web
  ports:
    - name: http
      port: 80
      targetPort: 8080
      protocol: TCP
```

Apply the file and verify that the Pod starts. If it fails, read the event message before changing anything; the failure is usually a useful clue about security context, writable paths, or admission.

```bash
kubectl apply -f runtime-demo-secure-web.yaml
kubectl get pod secure-web -n runtime-demo -o wide
kubectl describe pod secure-web -n runtime-demo
```

### Part 3: Add Default-Deny Networking And Restore DNS

Apply a namespace-wide default-deny policy for ingress and egress. This is the baseline that forces you to describe allowed communication explicitly.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: runtime-demo
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
EOF
```

Add DNS egress back. If your cluster does not use the `k8s-app: kube-dns` label, inspect the CoreDNS Pods and adjust the selector to match your environment.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: runtime-demo
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
EOF
```

Create a diagnostic Pod with a restricted-compatible security context. Use it to test DNS and to confirm that arbitrary external egress is blocked.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: netcheck
  namespace: runtime-demo
  labels:
    app: netcheck
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: curl
      image: curlimages/curl:8.10.1
      command:
        - sleep
        - "3600"
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
EOF
kubectl wait --for=condition=Ready pod/netcheck -n runtime-demo --timeout=90s
kubectl exec -n runtime-demo netcheck -- nslookup kubernetes.default.svc.cluster.local
kubectl exec -n runtime-demo netcheck -- curl -sS -m 5 https://example.com
```

The DNS lookup should succeed if your DNS selector matches the cluster. The external `curl` should fail or time out after default-deny egress, unless your CNI does not enforce NetworkPolicy. If external egress succeeds, verify CNI support before assuming the policy is wrong.

### Part 4: Add A Quarantine Response Policy

Create a quarantine policy that isolates any Pod with a specific label. This gives responders a fast containment action during runtime incidents.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine-labeled-pods
  namespace: runtime-demo
spec:
  podSelector:
    matchLabels:
      runtime.kubedojo.io/quarantine: "true"
  policyTypes:
    - Ingress
    - Egress
EOF
```

Apply the quarantine label to the diagnostic Pod and verify that DNS now fails for that Pod. Then remove the label so the Pod returns to the namespace's normal policy state.

```bash
kubectl label pod netcheck -n runtime-demo \
  runtime.kubedojo.io/quarantine=true \
  --overwrite
kubectl exec -n runtime-demo netcheck -- nslookup kubernetes.default.svc.cluster.local
kubectl label pod netcheck -n runtime-demo runtime.kubedojo.io/quarantine-
kubectl exec -n runtime-demo netcheck -- nslookup kubernetes.default.svc.cluster.local
```

### Part 5: Optional Falco Detection

Install Falco only if your cluster permits the required node-level sensor. Some managed or restricted lab clusters block this, so treat this part as optional and document the constraint if installation is not allowed.

```bash
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=ebpf \
  --set tty=true
kubectl get pods -n falco
```

Watch the Falco logs in one terminal, then attempt a shell in the demo Pod from another terminal. Depending on your cluster, image, and Falco rules, you should see a shell-related event or a similar process-execution signal.

```bash
kubectl logs -n falco -l app.kubernetes.io/name=falco -f
```

```bash
kubectl exec -n runtime-demo secure-web -- /bin/sh -c 'id && whoami'
```

### Part 6: Capture Evidence Before Cleanup

Practice evidence capture even in the demo. The habit matters because incident response is harder to improvise under pressure.

```bash
mkdir -p evidence/runtime-demo
kubectl get pod secure-web -n runtime-demo -o yaml \
  > evidence/runtime-demo/secure-web-pod.yaml
kubectl describe pod secure-web -n runtime-demo \
  > evidence/runtime-demo/secure-web-describe.txt
kubectl logs secure-web -n runtime-demo \
  > evidence/runtime-demo/secure-web.log
kubectl get networkpolicy -n runtime-demo -o yaml \
  > evidence/runtime-demo/networkpolicies.yaml
kubectl get events -n runtime-demo \
  --sort-by=.lastTimestamp \
  > evidence/runtime-demo/events.log
```

### Success Criteria

- [ ] The `runtime-demo` namespace has restricted Pod Security labels for `enforce`, `warn`, and `audit`.
- [ ] A non-hardened Pod is rejected or produces a restricted-policy warning, depending on your cluster behavior.
- [ ] The `secure-web` Pod runs with non-root identity, dropped capabilities, no privilege escalation, `RuntimeDefault` seccomp, and a read-only root filesystem.
- [ ] A namespace-wide default-deny NetworkPolicy exists for both ingress and egress.
- [ ] DNS works only after an explicit DNS egress policy is present and correctly selects the cluster DNS Pods.
- [ ] Arbitrary external egress from the diagnostic Pod is blocked, or you have documented that the cluster CNI does not enforce NetworkPolicy.
- [ ] A quarantine label causes the selected Pod to lose network access through the quarantine policy.
- [ ] Evidence files are collected before cleanup.
- [ ] Optional: Falco or an equivalent runtime sensor records a shell or process-execution signal from the demo workload.

### Cleanup

Remove the demo namespace when you are finished. If you installed Falco only for this exercise, uninstall it as well.

```bash
kubectl delete namespace runtime-demo
helm uninstall falco -n falco
kubectl delete namespace falco
```

---

## Next Module

Continue to [Module 4.6: Security Culture and Automation](../module-4.6-security-culture/) to learn how runtime security practices become sustainable through team habits, automation, exception management, and continuous improvement.

---

## Sources

- [CNCF Announces Falco Graduation](https://www.cncf.io/announcements/2024/02/29/cloud-native-computing-foundation-announces-falco-graduation/) — Confirms Falco's project history, including its Sysdig origins and CNCF milestones.
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) — Authoritative reference for the privileged, baseline, and restricted profiles discussed in the module.
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — Defines how Kubernetes NetworkPolicy works and when policy resources do or do not take effect.
- [Seccomp and Kubernetes](https://kubernetes.io/docs/reference/node/seccomp/) — Explains seccomp profile types, inheritance rules, and runtime behavior for Kubernetes workloads.
