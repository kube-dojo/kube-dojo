---
title: "Module 4.6: KubeArmor - Runtime Security with Least Privilege"
slug: platform/toolkits/security-quality/security-tools/module-4.6-kubearmor
sidebar:
  order: 7
---

## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes

**Prerequisites**: Module 4.3 (Falco), Module 4.5 (Tetragon basics), working knowledge of Linux permissions, Kubernetes Deployments, labels, and basic runtime security concepts such as AppArmor, SELinux, and Linux capabilities.

**Track**: Platform Toolkits

---

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** when KubeArmor is the right runtime security control compared with Falco detection, Tetragon enforcement, Kubernetes NetworkPolicies, and admission policies.
- **Design** least-privilege KubeArmor policies that constrain process execution, file access, network protocols, and Linux capabilities without breaking normal application behavior.
- **Debug** KubeArmor policy results by reading security events, checking selectors, validating supported enforcement backends, and separating policy mistakes from application defects.
- **Implement** a staged rollout path that moves from visibility, to audit, to selective blocking, to production enforcement with rollback criteria.
- **Compare** allow-list and block-list security models by reasoning through realistic compromise paths rather than memorizing policy syntax.

---

## Why This Module Matters

A platform team inherits a production cluster where every container image has passed vulnerability scanning, every Deployment has resource limits, and every namespace has a NetworkPolicy. Then one supplier publishes a compromised image under a trusted tag. The container starts successfully because the image is valid, the Pod is admitted because the manifest is compliant, and the application still answers health checks while an unexpected binary runs beside it. Nothing in the deployment pipeline asked the most important runtime question: what is this container actually allowed to do after it starts?

KubeArmor matters because many security controls stop at the edge of the workload. Admission control can reject risky Pod specs before scheduling, image scanners can detect known vulnerable packages, and NetworkPolicies can restrict pod-to-pod traffic. Those controls are valuable, but they do not directly say that an `nginx` container may execute `nginx` and read its configuration, while it may not start `/bin/sh`, read service account tokens, write miner configuration under `/var/tmp`, or create raw sockets. KubeArmor moves that decision into the running node, where process, file, network, and capability activity actually happens.

The practical lesson is not that KubeArmor replaces the rest of your security stack. It gives the platform team a least-privilege enforcement layer that complements detection tools and deployment-time policy. A senior platform engineer uses it carefully: first to observe real behavior, then to narrow permissions in staging, then to enforce high-confidence controls in production, and finally to feed alerts into the same incident workflow as Falco, Tetragon, audit logs, and SIEM events.

---

## Core Content

### 1. The Security Model Problem KubeArmor Solves

Most container environments begin as default-allow systems. A Pod may have a small application entrypoint, but the filesystem often contains shells, package manager helpers, interpreters, certificate bundles, temporary directories, and service account material. If an attacker can reach a remote code execution path inside the application, the container's installed tools become the attacker's toolbox unless another control narrows what runtime behavior is permitted.

KubeArmor addresses this by applying security policies at runtime through Linux security mechanisms. Instead of relying only on "detect and respond" after suspicious activity begins, it can block selected behavior before that behavior completes. The key shift is from asking "Which bad tools should we block?" to asking "Which operations does this workload legitimately need?" That second question is harder at first, but it produces a more stable security boundary because unknown tools and unexpected paths are denied by policy rather than allowed by omission.

```text
+-----------------------------------------------------------------------+
|                 Traditional Block-List Runtime Model                  |
|                                                                       |
|  Container starts with broad permissions. Security team blocks known   |
|  bad behaviors after learning about them from incidents, detections,   |
|  threat feeds, or previous failures.                                  |
|                                                                       |
|     Allowed by default:                                               |
|                                                                       |
|       +--------+   +--------+   +--------+   +--------+   +--------+  |
|       |  app   |   |  sh    |   | wget   |   | python |   | unknown|  |
|       |  yes   |   |  yes   |   |  yes   |   |  yes   |   |  yes   |  |
|       +--------+   +--------+   +--------+   +--------+   +--------+  |
|                                                                       |
|     Block rules: xmrig, ncat, suspicious paths, selected protocols     |
|                                                                       |
|  Weakness: the next attack only needs a tool or path you did not name. |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
|                  KubeArmor Least-Privilege Runtime Model              |
|                                                                       |
|  Container behavior is constrained around known-good operations.       |
|  Discovery and audit help identify normal behavior before enforcement. |
|                                                                       |
|     Allowed by explicit policy:                                       |
|                                                                       |
|       +--------+   +--------+   +--------+   +--------+   +--------+  |
|       |  app   |   |  sh    |   | wget   |   | python |   | unknown|  |
|       |  yes   |   |  no    |   |  no    |   |  no    |   |  no    |  |
|       +--------+   +--------+   +--------+   +--------+   +--------+  |
|                                                                       |
|     Allow rules: /usr/sbin/nginx, /etc/nginx read-only, tcp, udp DNS   |
|                                                                       |
|  Strength: unexpected behavior fails even when the image still starts. |
+-----------------------------------------------------------------------+
```

A useful mental model is that image scanning asks what is inside the image, admission control asks whether the Pod should be accepted, and KubeArmor asks what the running workload may do. Those questions overlap, but they are not the same. If you confuse them, you may expect a scanner to stop runtime misuse or expect a NetworkPolicy to prevent local file reads. KubeArmor is valuable precisely because it controls behaviors that are inside the container boundary.

**Pause and predict:** imagine a compromised web image where the legitimate server process is `/usr/sbin/nginx`, but a malicious post-start script attempts to run `/bin/sh -c "wget http://example.invalid/payload"`. If the KubeArmor policy allows only `/usr/sbin/nginx` and blocks recursive execution from `/`, which part of the attack fails first, and what evidence would you expect in the KubeArmor logs?

A beginner often wants to write one large policy immediately, but a senior engineer starts by identifying the behavior classes. Process controls answer "Which binaries may execute?" File controls answer "Which files and directories may be read or written?" Network protocol controls answer "Which protocol families are acceptable from this workload?" Capability controls answer "Which privileged kernel operations should remain available?" The exact policy syntax matters, but the design skill is in mapping application behavior to those categories without overfitting one lucky test run.

| Runtime question | KubeArmor policy area | Example decision | Operational risk if ignored |
|---|---|---|---|
| Which programs may start? | `process` | Allow `/usr/sbin/nginx`, block shells and interpreters | Remote code execution gains a ready-made toolbox |
| Which files may be touched? | `file` | Allow `/etc/nginx/` read-only and cache directories writable | Secrets, tokens, and host-mounted files may be exposed |
| Which protocol families may be used? | `network` | Allow TCP and UDP, block raw sockets | Workload can attempt low-level probing or packet crafting |
| Which privileged kernel powers remain? | `capabilities` | Block `net_admin`, `sys_admin`, or unnecessary bind powers | Container escape and node abuse paths become easier |
| Which pods receive the policy? | `selector` | Match `app: checkout` in the target namespace | Policy silently misses workloads or hits the wrong ones |

The security model also has a cost. A poorly designed allow-list can break legitimate startup, health checks, DNS lookups, certificate reads, temporary file writes, or language runtime behavior. That cost is why the recommended path is visibility first, audit second, and blocking only after the platform team understands the workload's normal activity. Least privilege is not a slogan; it is a rollout process.

### 2. KubeArmor Architecture and Enforcement Boundaries

KubeArmor is Kubernetes-native from the operator's point of view, but the enforcement work happens on each node. The cluster stores policy objects as CRDs, and a node-level agent observes workload metadata, resolves which policies apply to which containers, and programs enforcement through the available Linux security backend. This separation is important because a policy that looks correct in the API is not useful unless the target node supports an enforcer capable of applying it.

```text
+--------------------------------------------------------------------------------+
|                              Kubernetes Cluster                                |
|                                                                                |
|  +------------------------------ Control Plane View -------------------------+  |
|  |                                                                          |  |
|  |   +-------------------+      +----------------------------------------+   |  |
|  |   | KubeArmor         |      | KubeArmor CRDs                         |   |  |
|  |   | Operator          |----->| - KubeArmorPolicy                      |   |  |
|  |   |                   |      | - KubeArmorHostPolicy                  |   |  |
|  |   +-------------------+      | - KubeArmorClusterPolicy               |   |  |
|  |                              +----------------------------------------+   |  |
|  +--------------------------------------------------------------------------+  |
|                                                                                |
|  +--------------------------- Node Runtime View ----------------------------+   |
|  |                                                                          |   |
|  |   +-------------+       +----------------+       +-------------------+    |   |
|  |   | Pod labels  | ----> | KubeArmor      | ----> | Linux enforcer    |    |   |
|  |   | namespace   |       | Agent          |       | AppArmor / LSM    |    |   |
|  |   | container   |       | DaemonSet      |       | SELinux / BPF-LSM |    |   |
|  |   +-------------+       +----------------+       +-------------------+    |   |
|  |                                  |                                       |   |
|  |                                  v                                       |   |
|  |                         +----------------+                               |   |
|  |                         | Alerts and logs |                               |   |
|  |                         | via Relay / CLI |                               |   |
|  |                         +----------------+                               |   |
|  +--------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------+
```

The architecture has three boundaries learners should keep separate. First, Kubernetes selectors decide which Pods the policy intends to target. Second, the node agent connects that policy intent to real containers on a real node. Third, the Linux enforcer decides whether a process, file, network, or capability operation is allowed, audited, or blocked. When troubleshooting, you move through those boundaries in order instead of guessing from the YAML alone.

| Component | Role | What you check when debugging |
|---|---|---|
| KubeArmor Operator | Installs and manages KubeArmor components | Operator and DaemonSet are healthy in the `kubearmor` namespace |
| KubeArmor Agent | Runs on each node and applies policy to local workloads | Agent logs show the node has an active enforcer |
| KubeArmor Relay | Aggregates events from agents | `karmor logs` receives events from the expected namespace |
| `karmor` CLI | Probes, discovers, and streams policy activity | CLI can reach the cluster and report runtime status |
| `KubeArmorPolicy` | Namespaced workload policy | Policy namespace and selector match the target Pod labels |
| `KubeArmorClusterPolicy` | Cluster-scoped workload policy | Selector is narrow enough to avoid accidental global impact |
| `KubeArmorHostPolicy` | Node or host protection policy | Host targeting is deliberate and tested separately from Pod policy |

KubeArmor can use different enforcement backends depending on the node operating system and kernel support. Platform engineers should treat this as a compatibility requirement, not a trivia item. A policy design that works in a homogeneous Ubuntu node pool may behave differently when workloads move to a RHEL-based node pool, a managed Kubernetes runtime with different kernel configuration, or a pool where BPF-LSM support is absent.

| Backend | Typical environment | Strength | Design caution |
|---|---|---|---|
| AppArmor | Common on Ubuntu and Debian nodes | Mature profile-based enforcement for process and file behavior | Requires AppArmor support and profile loading on the node |
| SELinux | Common on RHEL, Fedora, and enterprise Linux nodes | Strong label-based enforcement model | Existing SELinux policy posture may affect expectations |
| BPF-LSM | Newer kernels with required BPF and LSM support | Flexible enforcement through Linux security hooks | Kernel configuration and managed-provider support must be verified |
| Visibility-only mode | Nodes without a usable enforcer or during discovery | Useful for learning behavior safely | It does not provide the same protection as blocking enforcement |

**Stop and think:** your staging cluster uses Ubuntu nodes and reports AppArmor enforcement, while production includes a newer managed node pool where the provider image may expose a different enforcer. Before you approve production rollout, what command output would you collect, and why is "the YAML applied successfully" not enough evidence?

The `karmor probe` command is the fastest way to verify whether KubeArmor is running and which enforcer is active. The exact output varies by version and environment, so the important habit is to look for three facts: KubeArmor components are reachable, each expected node is represented, and an enforcer is active where you expect blocking behavior. A policy can exist in Kubernetes while still failing to enforce if the node layer is not ready.

```bash
kubectl get pods -n kubearmor
```

After using `kubectl` once, many Kubernetes operators prefer the short alias `k`. The remaining commands in this module use `k` for compactness; define it in your shell before running the examples.

```bash
alias k=kubectl

k get nodes -o wide
k get pods -n kubearmor
karmor probe
```

When a team says "KubeArmor is not working," the failure usually sits in one of four places. The policy may not select the Pod, the Pod may not be on a node with enforcement enabled, the tested command may not actually exercise the policy rule, or the logs may be filtered too narrowly. Senior troubleshooting avoids changing policy first. It proves the path from selector to node to enforcer to event stream, then edits the smallest possible rule.

### 3. Designing KubeArmorPolicy From Behavior, Not Syntax

A KubeArmor policy starts with a selector because runtime security is workload-specific. A policy for `nginx` should not accidentally constrain a migration job, and a cluster-wide baseline should not silently apply to system controllers unless that is the intended design. Labels therefore become part of the security contract. If the platform standard allows ambiguous labels, KubeArmor policies become easier to misapply.

The smallest useful policy has three parts: metadata that scopes the policy, a selector that finds the workload, and rules that describe process, file, network, or capability behavior. The example below is intentionally modest. It does not try to solve every security problem at once; it blocks interactive shell execution for a specific application label so the team can verify that policy selection and event logging work before moving to stricter least privilege.

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: web-block-shells
  namespace: production
spec:
  selector:
    matchLabels:
      app: web
  process:
    matchPaths:
      - path: /bin/sh
        action: Block
      - path: /bin/bash
        action: Block
      - path: /usr/bin/sh
        action: Block
      - path: /usr/bin/bash
        action: Block
```

This is not a complete allow-list. It is a targeted block policy that proves the enforcement path and removes common interactive shells. That distinction matters because "KubeArmor policy" does not automatically mean "default-deny allow-list." You can write targeted block rules, audit rules, or allow-oriented policies depending on the stage of rollout and the behavior you are trying to control. The senior design choice is to match the strictness of the policy to the confidence you have in the workload model.

| Policy style | Best use | Example | Main risk |
|---|---|---|---|
| Audit selected behavior | Learning and validating assumptions | Audit shell use, sensitive file reads, or raw sockets | No prevention if the behavior is malicious |
| Block known-dangerous behavior | Fast hardening with low application impact | Block shells in server containers | Attackers may use another allowed tool |
| Allow known-good behavior | Mature least-privilege enforcement | Allow only expected binaries and directories | Under-modeled behavior can cause outages |
| Cluster baseline | Organization-wide minimum standard | Block dangerous capabilities in app namespaces | Broad selectors can hit workloads with special needs |
| Host policy | Node protection beyond containers | Protect host paths or node processes | Blast radius is higher and rollback must be rehearsed |

A worked example makes the design process concrete. Suppose a platform team runs an `nginx:alpine` Deployment that only serves static content. The desired behavior is narrow: start `nginx`, read configuration and web content, write runtime files under expected cache and log directories, perform TCP connections for normal service behavior, and use UDP only where DNS is required. The undesired behavior includes starting shells, fetching remote payloads with helper tools, reading service account tokens, modifying `/etc/nginx`, and using raw sockets.

The team should first translate that story into behavior categories before writing YAML. Process rules should allow the `nginx` binary and block recursive execution where the container should not run arbitrary tools. File rules should make configuration and content read-only while preserving writable paths needed by the server. Network rules should permit ordinary protocols but block raw socket behavior. The policy below demonstrates the pattern, but a real team would still validate it in staging because images and entrypoints vary.

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: static-web-least-privilege
  namespace: production
spec:
  selector:
    matchLabels:
      app: static-web
  process:
    matchPaths:
      - path: /usr/sbin/nginx
        action: Allow
    matchDirectories:
      - dir: /
        recursive: true
        action: Block
  file:
    matchDirectories:
      - dir: /etc/nginx/
        recursive: true
        readOnly: true
        action: Allow
      - dir: /usr/share/nginx/html/
        recursive: true
        readOnly: true
        action: Allow
      - dir: /var/cache/nginx/
        recursive: true
        action: Allow
      - dir: /var/log/nginx/
        recursive: true
        action: Allow
      - dir: /var/run/
        recursive: true
        action: Allow
    matchPaths:
      - path: /etc/passwd
        readOnly: true
        action: Allow
      - path: /etc/group
        readOnly: true
        action: Allow
      - path: /var/run/secrets/kubernetes.io/serviceaccount/token
        action: Block
  network:
    matchProtocols:
      - protocol: tcp
        action: Allow
      - protocol: udp
        action: Allow
      - protocol: raw
        action: Block
```

**Pause and predict:** if this policy is applied to a container whose startup script runs `/docker-entrypoint.sh` before launching `/usr/sbin/nginx`, what failure might appear even though `nginx` itself is allowed? Which rule would you relax temporarily in audit mode to confirm your hypothesis without removing the whole policy?

That example also shows why discovery is helpful but not magic. Discovery can observe the entrypoint, runtime reads, writes, and network protocols during a representative test window. It cannot prove that every future maintenance path, certificate reload, feature flag, or rare error-handling branch was exercised. Discovery output should be reviewed like generated code: useful as a starting draft, unsafe as an unquestioned production artifact.

```bash
karmor discover --namespace production --deployment static-web --output static-web-observed.yaml

sed -n '1,220p' static-web-observed.yaml
k apply --dry-run=server -f static-web-observed.yaml
```

A mature policy review asks whether each allowed path is required, whether each blocked path has a clear rationale, and whether the selector matches only the intended workload. It also checks whether the policy uses writable directories narrowly. Allowing all of `/tmp` may be necessary for some applications, but it should be a conscious decision, not a reflex copied into every policy. Attackers prefer writable directories because they can stage payloads, configuration, and temporary files there.

| Review question | Good answer | Weak answer |
|---|---|---|
| Why is this process allowed? | It is the container entrypoint or a verified helper used during normal startup | The image contains it, so we allowed it |
| Why is this directory writable? | The application writes cache files there during request handling | Some containers need temporary files |
| Why is UDP allowed? | DNS resolution is required and tested with policy logs enabled | It seemed safer to allow both TCP and UDP |
| Why is the selector safe? | It matches a deployment-owned label unique to this workload | It matches a broad label such as `app` across namespaces |
| How was this tested? | Staging traffic, health checks, failure paths, and rollback were exercised | The manifest applied without validation errors |

### 4. Rollout Strategy: Visibility, Audit, Enforce, Operate

The biggest operational mistake with runtime enforcement is skipping straight to blocking. A platform team can create a technically valid policy that breaks production because the application performs legitimate behavior that was invisible during casual testing. KubeArmor should be introduced as a controlled rollout, especially for workloads with dynamic languages, shell-based entrypoints, certificate reloads, backup hooks, or debugging conventions.

A safe rollout begins with visibility. The team installs KubeArmor, verifies node support, streams logs, and observes workload behavior without trying to stop anything. During this stage, the goal is not to find every attack. The goal is to build confidence that KubeArmor sees the target namespace, that events contain useful workload metadata, and that normal operations produce understandable traces.

```bash
k get pods -n kubearmor
k get deploy -n production --show-labels
karmor logs --namespace production
```

The next stage is audit. Audit policies are useful because they test selectors and rule intent while allowing the operation to proceed. If an audit rule unexpectedly fires during normal traffic, the team has found a modeling gap without causing an outage. If an audit rule never fires when a test should trigger it, the team has found a selector, path, backend, or test-design problem before relying on enforcement.

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: checkout-audit-risky-behavior
  namespace: production
spec:
  selector:
    matchLabels:
      app: checkout
  process:
    matchPaths:
      - path: /bin/sh
        action: Audit
      - path: /usr/bin/wget
        action: Audit
      - path: /usr/bin/curl
        action: Audit
  file:
    matchDirectories:
      - dir: /var/run/secrets/kubernetes.io/serviceaccount/
        recursive: true
        action: Audit
  network:
    matchProtocols:
      - protocol: raw
        action: Audit
```

After audit, move selected controls to blocking. The safest early blocks are behaviors that production applications should rarely need: raw sockets in ordinary web workloads, interactive shell execution in immutable server containers, access to service account tokens for workloads that do not call the Kubernetes API, and unnecessary Linux capabilities. The more application-specific the rule, the more evidence you need before enforcing it.

```text
+--------------------------------------------------------------------------------+
|                              KubeArmor Rollout Path                             |
|                                                                                |
|   1. Install and probe                                                         |
|      Confirm agents, relay, CLI access, and active enforcer on expected nodes. |
|                                                                                |
|   2. Observe                                                                   |
|      Stream logs during startup, health checks, traffic, reloads, and errors.  |
|                                                                                |
|   3. Audit                                                                     |
|      Add audit rules for risky behavior and verify events without disruption.  |
|                                                                                |
|   4. Enforce selected controls                                                 |
|      Convert high-confidence audit rules to Block with rollback instructions.  |
|                                                                                |
|   5. Expand least privilege                                                    |
|      Add tighter process, file, network, and capability rules per workload.    |
|                                                                                |
|   6. Operate                                                                   |
|      Monitor alerts, review drift, and update policy with application changes. |
+--------------------------------------------------------------------------------+
```

A rollback plan is part of the policy, even if Kubernetes does not store it in the object. Before blocking, decide how to remove or relax the policy, who can approve the rollback, which alert indicates user impact, and how long the team will observe after the change. Runtime security controls fail operationally when they are treated as one-way gates. They become manageable when each enforcement step has a clear escape path.

| Rollout stage | Primary command | Evidence to collect | Promotion criteria |
|---|---|---|---|
| Install | `k get pods -n kubearmor` | KubeArmor Pods are healthy | Agents run on intended nodes |
| Probe | `karmor probe` | Active enforcer is reported | Blocking is supported where required |
| Observe | `karmor logs --namespace <ns>` | Events include target workload metadata | Logs are understandable and routed |
| Audit | `k apply -f audit-policy.yaml` | Expected test actions produce audit events | No unexpected normal-path audit hits |
| Enforce | `k apply -f block-policy.yaml` | Blocked tests fail and app health remains good | Health checks, traffic, and logs are clean |
| Operate | SIEM or alert pipeline | Events are triaged with ownership | Policy drift is reviewed during releases |

KubeArmor events are only useful if operators can interpret them. A policy event should answer what happened, which policy matched, which workload was involved, and what action was taken. If the event stream is too noisy, the team will ignore it. If it is too sparse, the team will not trust it. Good policy design includes event design: meaningful policy names, namespace scoping, labels that identify service ownership, and runbooks that connect common alerts to next actions.

```bash
karmor logs --namespace production --logFilter=policy
karmor logs --namespace production --json | jq '.'
```

**Stop and think:** your team blocks shell execution in production, and a deployment immediately fails its readiness probe. The application container is still running, but the probe command uses `/bin/sh -c` inside the image. Should you remove the KubeArmor policy, rewrite the probe, or create an exception? What evidence would make one choice better than the others?

The correct answer depends on ownership and risk. If the shell-based probe is accidental and can be replaced with an HTTP probe, rewriting the probe improves both reliability and security. If a vendor image genuinely requires a shell entrypoint during startup, the team may need a narrow exception while filing a hardening ticket. If user traffic is failing and the policy was just deployed, rollback may be the right immediate action while preserving logs for review. Senior security engineering is not "always block"; it is making the least risky change with the evidence available.

### 5. Choosing KubeArmor Alongside Falco, Tetragon, and Kubernetes Controls

KubeArmor sits in a crowded security toolkit, and confusion between tools leads to weak architectures. Falco is primarily used for runtime detection and alerting. Tetragon uses eBPF-based visibility and enforcement patterns, especially attractive in Cilium-heavy environments. Kubernetes NetworkPolicies constrain traffic between Pods and network endpoints. Admission controllers prevent noncompliant resources from entering the cluster. KubeArmor focuses on workload and host runtime enforcement through Linux security hooks.

| Feature | KubeArmor | Tetragon | Falco | Kubernetes NetworkPolicy | Admission policy |
|---|---|---|---|---|---|
| Primary job | Least-privilege runtime enforcement | eBPF observability and selected enforcement | Runtime detection and alerting | Pod network segmentation | Pre-deployment policy control |
| Typical question | May this container do this operation? | What process or kernel event occurred? | Is this behavior suspicious? | May this Pod talk to that endpoint? | Should this object be admitted? |
| Enforcement timing | During runtime operation | During selected runtime events | Usually alert-only | During network flow | Before object persistence or scheduling |
| Main scope | Processes, files, protocols, capabilities | Kernel events, processes, network context | Behavioral rules and detections | Network traffic | Kubernetes API objects |
| Best strength | Allow-list and block workload behavior | Deep eBPF-powered event context | Rich detection ecosystem | Simple traffic isolation | Preventing risky specs early |
| Common pairing | KubeArmor blocks, Falco alerts, NetworkPolicy segments | Tetragon traces, KubeArmor constrains | Falco detects what is not blocked | NetworkPolicy narrows connectivity | Admission requires labels and baselines |

Do not choose between these tools as if they were interchangeable. A production platform often uses more than one because they answer different failure modes. Admission policy can require non-root containers and approved labels. NetworkPolicy can limit which services the workload can reach. KubeArmor can block the workload from executing shells or reading tokens. Falco or Tetragon can alert on suspicious behavior that remains outside the enforced policy or occurs on nodes and workloads not yet covered.

A helpful design pattern is "prevent what you understand, detect what you cannot yet prevent." If the team knows that a static web server should never use raw sockets, blocking raw sockets is reasonable. If the team suspects unusual child processes may indicate compromise but has not finished modeling the application's startup behavior, auditing or detecting child processes may be safer before enforcement. Over time, repeated low-noise detections can graduate into KubeArmor blocking rules.

```text
+--------------------------------------------------------------------------------+
|                         Layered Runtime Security Design                         |
|                                                                                |
|  Build time                                                                     |
|    Image scan, SBOM, signing, provenance                                        |
|                                                                                |
|  Admission time                                                                 |
|    Reject privileged Pods, require labels, require approved registries           |
|                                                                                |
|  Network runtime                                                                |
|    NetworkPolicy or CNI policy restricts service-to-service traffic              |
|                                                                                |
|  Workload runtime                                                               |
|    KubeArmor controls process, file, network protocol, and capabilities          |
|                                                                                |
|  Detection and response                                                         |
|    Falco, Tetragon, audit logs, SIEM, incident workflow                          |
|                                                                                |
|  Feedback loop                                                                  |
|    Incidents and noisy alerts become better policies or better application code  |
+--------------------------------------------------------------------------------+
```

There are also cases where KubeArmor is not the first tool to reach for. If the immediate problem is that Pods are being deployed as privileged with hostPath mounts, admission control should stop that earlier. If the problem is east-west service access, NetworkPolicy or CNI policy is the direct control. If the problem is broad threat hunting across kernel events, a detection-oriented tool may provide richer context. KubeArmor shines when the team needs to narrow what a workload or host may do after it is already running.

A senior rollout also accounts for organizational ownership. Application teams know normal behavior, platform teams know cluster enforcement, and security teams know risk appetite and detection workflows. KubeArmor policies work best when those groups share a review process. The platform team can provide templates and guardrails, application owners can validate behavior, and security can decide which behaviors become mandatory baselines across namespaces.

### 6. Worked Incident: Blocking a Compromised Image Without Breaking Checkout

Consider a checkout service written in Node.js. The service normally starts `/usr/local/bin/node`, reads code under `/app`, reads CA certificates, writes temporary cache files, and connects to payment and inventory services over TCP. A supplier image update adds a miner binary under `/usr/bin/xmrig` and a small script that tries to write configuration under `/var/tmp` before contacting a mining pool. Image scanning does not flag a known CVE because the problem is malicious content, not a vulnerable package.

The platform team does not begin by guessing a giant production policy. First, it observes the known-good release in staging during startup, health checks, normal traffic, payment failures, and restart behavior. Then it writes an audit policy for risky behavior: shell execution, miner-like binaries, writes outside expected directories, service account token reads, and raw socket usage. Only after the audit window shows no legitimate hits does the team convert the strongest controls to blocking.

```bash
k create namespace checkout-demo

k apply -n checkout-demo -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  labels:
    app: checkout
spec:
  replicas: 1
  selector:
    matchLabels:
      app: checkout
  template:
    metadata:
      labels:
        app: checkout
    spec:
      containers:
        - name: checkout
          image: node:22-alpine
          command: ["node", "-e"]
          args:
            - |
              const http = require('http');
              const server = http.createServer((req, res) => {
                res.end('checkout ok\n');
              });
              server.listen(8080, '0.0.0.0');
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: checkout
spec:
  selector:
    app: checkout
  ports:
    - port: 8080
      targetPort: 8080
EOF

k wait --for=condition=available deployment/checkout -n checkout-demo --timeout=90s
```

The first policy audits behaviors that should not occur during normal request handling. This is deliberate. The team wants a low-risk signal before blocking, and it wants to prove that KubeArmor sees this Deployment. If a normal health check triggers `/bin/sh`, the audit event is not a failure of KubeArmor. It is useful evidence that the workload model needs refinement before enforcement.

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: checkout-risk-audit
  namespace: checkout-demo
spec:
  selector:
    matchLabels:
      app: checkout
  process:
    matchPaths:
      - path: /bin/sh
        action: Audit
      - path: /usr/bin/wget
        action: Audit
      - path: /usr/bin/curl
        action: Audit
      - path: /usr/bin/xmrig
        action: Audit
  file:
    matchDirectories:
      - dir: /var/run/secrets/kubernetes.io/serviceaccount/
        recursive: true
        action: Audit
      - dir: /var/tmp/
        recursive: true
        action: Audit
  network:
    matchProtocols:
      - protocol: raw
        action: Audit
```

After validation, the team chooses a smaller blocking policy rather than turning every observed path into a rigid allow-list on day one. It blocks shells, known downloader tools, token reads, and raw sockets. It leaves full process allow-listing for a later hardening step because the Node image includes startup and runtime behavior that needs more careful modeling. This staged decision reduces risk while still neutralizing much of the compromise path.

```yaml
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: checkout-risk-block
  namespace: checkout-demo
spec:
  selector:
    matchLabels:
      app: checkout
  process:
    matchPaths:
      - path: /bin/sh
        action: Block
      - path: /usr/bin/wget
        action: Block
      - path: /usr/bin/curl
        action: Block
      - path: /usr/bin/xmrig
        action: Block
  file:
    matchDirectories:
      - dir: /var/run/secrets/kubernetes.io/serviceaccount/
        recursive: true
        action: Block
  network:
    matchProtocols:
      - protocol: raw
        action: Block
```

The important reasoning is that the policy blocks the attack chain at multiple points. The miner cannot execute if its binary path is blocked. The staging script cannot conveniently fetch another payload if common downloader tools are blocked. The process cannot read the Kubernetes service account token if token access is denied. Raw socket behavior is unavailable for low-level network tricks. The legitimate checkout service still runs because the policy did not block Node itself or the application directories it needs.

```text
+--------------------------------------------------------------------------------+
|                         Compromised Checkout Attack Chain                       |
|                                                                                |
|  Attacker goal: run miner and contact external mining pool                      |
|                                                                                |
|     1. Start injected helper script                                             |
|            |                                                                   |
|            v                                                                   |
|     2. Execute /usr/bin/xmrig             KubeArmor process rule blocks here    |
|            |                                                                   |
|            v                                                                   |
|     3. Write config under /var/tmp        File audit reveals staging behavior   |
|            |                                                                   |
|            v                                                                   |
|     4. Read service account token         KubeArmor file rule blocks here       |
|            |                                                                   |
|            v                                                                   |
|     5. Open unusual network behavior      Raw protocol rule blocks here         |
|                                                                                |
|  Defender goal: block attacker behavior while preserving normal Node service    |
+--------------------------------------------------------------------------------+
```

The incident also demonstrates a subtle platform lesson. A perfectly strict policy is not always the first production policy. The first production policy should be the one that meaningfully reduces risk while meeting the team's evidence threshold. Over time, the team can use discovery output, application owner review, and release testing to move from targeted blocks toward a fuller allow-list for process and file behavior.

---

## Did You Know?

- KubeArmor can protect both Kubernetes workloads and host resources, but host policy has a larger blast radius and should be rolled out with stricter change control than namespaced workload policy.
- KubeArmor policy quality depends heavily on Kubernetes labels because selectors decide which workloads receive enforcement; weak label hygiene becomes a security problem.
- Audit mode is valuable even for teams that plan to block aggressively because it tests policy matching, event routing, and workload assumptions without immediately disrupting traffic.
- Runtime least privilege improves incident response because blocked events describe attempted behavior, giving responders concrete evidence instead of only a generic "container compromised" signal.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Applying a broad cluster policy first | A selector that matches too many workloads can break unrelated services and create distrust in runtime enforcement | Start with one namespace or one workload, then promote proven controls into baselines |
| Treating discovery output as production-ready | Discovery only sees behavior exercised during the observation window and may miss rare startup, reload, or failure paths | Review generated policy with application owners and test known edge cases before blocking |
| Forgetting entrypoint and helper processes | A policy that allows only the final server binary may block startup scripts or language runtime helpers | Observe startup separately and decide whether helpers are legitimate or should be removed |
| Blocking DNS-related UDP accidentally | Applications may appear healthy until they need name resolution, then fail with confusing network symptoms | Test DNS lookups under audit and explicitly account for required UDP behavior |
| Allowing writable directories too broadly | Broad writable paths give attackers places to stage payloads and configuration | Keep writable paths narrow and explain why each write location is required |
| Ignoring node enforcer differences | A policy that applied through the API may not enforce the same way across heterogeneous node pools | Run `karmor probe` and include node compatibility in rollout criteria |
| Using vague policy names | Alerts become hard to triage when policy names do not reveal intent or ownership | Name policies after workload and behavior, such as `checkout-block-token-read` |

---

## Quiz

### Question 1

Your team deploys KubeArmor to staging and applies a policy that blocks `/bin/sh` for a web Deployment. The test `k exec deploy/web -- sh -c "id"` fails as expected, but the next rollout hangs because the container entrypoint uses a shell script before starting the server. What should you do before promoting this policy to production?

<details>
<summary>Show Answer</summary>

Do not blindly promote the policy. First confirm whether the shell-based entrypoint is required or just inherited from the image. If it can be replaced with a direct executable entrypoint, fix the image or manifest and keep the shell block. If it is genuinely required for now, use audit mode or a narrower exception during startup while creating a hardening follow-up. The key is to distinguish attacker shell access from legitimate startup behavior before enforcing globally.
</details>

### Question 2

A checkout service does not call the Kubernetes API, but KubeArmor audit logs show reads under `/var/run/secrets/kubernetes.io/serviceaccount/` during normal traffic. The application owner says the service still works. How should a platform engineer evaluate the next step?

<details>
<summary>Show Answer</summary>

The team should investigate which process reads the token and why, then remove token mounting if the service does not need it or block token access with KubeArmor after testing. The fact that the service still works suggests the token read may be unnecessary or caused by a library, sidecar, or diagnostic behavior. Blocking the path is reasonable only after confirming the read is not part of a required Kubernetes API workflow.
</details>

### Question 3

Production runs two node pools. One reports AppArmor enforcement in `karmor probe`, while the other does not show an active enforcer. A Deployment protected by KubeArmor can schedule onto either pool. What is the operational risk, and how would you reduce it?

<details>
<summary>Show Answer</summary>

The risk is inconsistent enforcement. Pods on the supported node pool may be blocked as expected, while Pods on the unsupported pool may only provide visibility or no effective blocking. Reduce the risk by constraining protected workloads to compatible nodes, fixing node image support, or delaying blocking rollout until all target nodes report an active enforcer. Also include node placement in verification, not just policy application.
</details>

### Question 4

A team wants to use KubeArmor instead of NetworkPolicies because their policy already allows TCP and UDP for a workload. During review, you notice the workload can still reach every service in the namespace. What misunderstanding do you need to correct?

<details>
<summary>Show Answer</summary>

KubeArmor network protocol rules are not a replacement for Kubernetes NetworkPolicies. Allowing or blocking protocol families at the container level does not define which Pods, namespaces, or IP ranges the workload may contact. The team should use NetworkPolicy or CNI policy for service-to-service segmentation and KubeArmor for process, file, capability, and protocol-level runtime constraints.
</details>

### Question 5

An application fails only when a certificate rotates. KubeArmor logs show blocked reads under a certificate directory that was not used during the initial discovery window. What does this teach about discovery mode, and how should the policy be adjusted?

<details>
<summary>Show Answer</summary>

Discovery mode reflects the behavior exercised during observation; it does not prove that rare maintenance paths were covered. The policy should be adjusted to allow the specific certificate path or directory required for rotation, preferably read-only, and the rollout test plan should add certificate reload or rotation as a scenario. This is a modeling gap, not a reason to abandon least privilege.
</details>

### Question 6

Security asks for a cluster-wide policy that blocks all shells, interpreters, and package managers in every namespace. The platform team is worried about controllers, jobs, and vendor images. How would you redesign the request into a safer rollout?

<details>
<summary>Show Answer</summary>

Start with audit mode and narrower selectors, such as application namespaces with clear ownership labels. Review audit hits by workload class, then convert low-risk behaviors to blocking for selected services. Keep system namespaces and special-purpose jobs out of the first wave unless they have dedicated testing. The security intent is valid, but cluster-wide blocking without evidence creates avoidable outage risk.
</details>

### Question 7

A KubeArmor policy is applied successfully, but a blocked test command still runs. The YAML selector uses `app: api`, while `k get pods --show-labels` shows the Pod has `app.kubernetes.io/name=api` and no `app` label. What should you check and change?

<details>
<summary>Show Answer</summary>

The policy is not selecting the Pod. Check the target Pod labels, policy namespace, and selector fields, then update the selector to match the actual stable label or add the intended label through the Deployment template. A successful API apply only proves the policy object is valid; it does not prove that any workload matched it.
</details>

---

## Hands-On Exercise: Build and Validate a Staged KubeArmor Policy

**Objective**: Create a safe rollout path for a small web workload by observing behavior, auditing risky actions, enforcing selected blocks, and verifying both application health and security events.

### Scenario

You are the platform engineer responsible for hardening a simple web Deployment. The application should serve HTTP traffic, but it should not provide interactive shell access, read Kubernetes service account tokens, or use raw sockets. Your goal is not to write the strictest possible policy immediately. Your goal is to practice the rollout discipline that prevents runtime security from becoming a production outage.

### Step 1: Confirm KubeArmor Is Installed

```bash
alias k=kubectl

k get pods -n kubearmor
karmor probe
```

If KubeArmor is not installed in your environment, install it using your platform's approved method before continuing. In a shared learning cluster, ask the instructor or platform owner whether the node pool supports AppArmor, SELinux, or BPF-LSM enforcement. The rest of the exercise assumes `karmor probe` reports a usable KubeArmor deployment and an active enforcer for the node running your test Pod.

Success criteria:

- [ ] KubeArmor Pods are running in the `kubearmor` namespace.
- [ ] `karmor probe` reports cluster connectivity and node runtime information.
- [ ] You know which enforcer is active on the node that will run your demo workload.

### Step 2: Deploy the Demo Workload

```bash
k create namespace kubearmor-demo

k apply -n kubearmor-demo -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: nginx
          image: nginx:1.29-alpine
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  selector:
    app: web-app
  ports:
    - port: 80
      targetPort: 80
EOF

k wait --for=condition=available deployment/web-app -n kubearmor-demo --timeout=90s
k get pods -n kubearmor-demo --show-labels
```

Success criteria:

- [ ] The `web-app` Deployment becomes available.
- [ ] The Pod label includes `app=web-app`.
- [ ] You can identify the namespace and label selector your KubeArmor policy will use.

### Step 3: Observe Normal and Risky Behavior

Open one terminal for KubeArmor logs and keep it running while you test behavior from another terminal.

```bash
karmor logs --namespace kubearmor-demo
```

In another terminal, run a normal web request from inside the container and then try a few risky actions. Some commands may succeed before policy is applied; that is the point of the baseline.

```bash
k exec -n kubearmor-demo deploy/web-app -- wget -q -O- http://127.0.0.1
k exec -n kubearmor-demo deploy/web-app -- sh -c 'id'
k exec -n kubearmor-demo deploy/web-app -- cat /var/run/secrets/kubernetes.io/serviceaccount/token
```

Success criteria:

- [ ] You generated normal web activity.
- [ ] You attempted at least one risky shell action.
- [ ] You attempted to read the service account token path.
- [ ] You observed whether KubeArmor produced visibility events in your environment.

### Step 4: Apply an Audit Policy

Create an audit policy for the risky actions. Audit mode should let the commands proceed while producing policy evidence, which makes it useful for validating selectors and event flow.

```bash
k apply -f - <<'EOF'
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: web-app-risk-audit
  namespace: kubearmor-demo
spec:
  selector:
    matchLabels:
      app: web-app
  process:
    matchPaths:
      - path: /bin/sh
        action: Audit
      - path: /usr/bin/wget
        action: Audit
  file:
    matchDirectories:
      - dir: /var/run/secrets/kubernetes.io/serviceaccount/
        recursive: true
        action: Audit
  network:
    matchProtocols:
      - protocol: raw
        action: Audit
EOF
```

Repeat the risky commands and watch the log stream.

```bash
k exec -n kubearmor-demo deploy/web-app -- sh -c 'id'
k exec -n kubearmor-demo deploy/web-app -- cat /var/run/secrets/kubernetes.io/serviceaccount/token
karmor logs --namespace kubearmor-demo --logFilter=policy
```

Success criteria:

- [ ] The audit policy applies without validation errors.
- [ ] The policy selector matches the `web-app` Pod.
- [ ] Risky test actions generate audit events or equivalent policy logs.
- [ ] The web application remains available while audit mode is active.

### Step 5: Convert High-Confidence Rules to Blocking

Now block shell execution and service account token reads. Leave `wget` out of the block rule for this exercise because the normal web test used it inside the container. This forces you to make a real design choice instead of copying every audit rule into enforcement.

```bash
k apply -f - <<'EOF'
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: web-app-risk-block
  namespace: kubearmor-demo
spec:
  selector:
    matchLabels:
      app: web-app
  process:
    matchPaths:
      - path: /bin/sh
        action: Block
  file:
    matchDirectories:
      - dir: /var/run/secrets/kubernetes.io/serviceaccount/
        recursive: true
        action: Block
  network:
    matchProtocols:
      - protocol: raw
        action: Block
EOF
```

Test both application health and blocked behavior. If a command behaves differently across container images or node backends, use the KubeArmor logs and Pod events to understand what happened before changing the policy.

```bash
k exec -n kubearmor-demo deploy/web-app -- wget -q -O- http://127.0.0.1
k exec -n kubearmor-demo deploy/web-app -- sh -c 'id'
k exec -n kubearmor-demo deploy/web-app -- cat /var/run/secrets/kubernetes.io/serviceaccount/token
karmor logs --namespace kubearmor-demo --logFilter=policy
```

Success criteria:

- [ ] The web application still serves a local HTTP response.
- [ ] Shell execution is blocked or fails because of the policy.
- [ ] Service account token access is blocked or produces a policy event.
- [ ] KubeArmor logs identify the matched policy and action.
- [ ] You can explain why `wget` was audited earlier but not blocked in the final policy.

### Step 6: Debug a Selector Mistake

Create a deliberately wrong policy by changing the selector label. Apply it, run the same test, and observe that policy application success does not equal workload coverage.

```bash
k apply -f - <<'EOF'
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: web-app-wrong-selector
  namespace: kubearmor-demo
spec:
  selector:
    matchLabels:
      app: does-not-match
  process:
    matchPaths:
      - path: /bin/sh
        action: Block
EOF

k get pods -n kubearmor-demo --show-labels
k exec -n kubearmor-demo deploy/web-app -- sh -c 'echo selector-test'
```

After the test, delete the deliberately wrong policy.

```bash
k delete kubearmorpolicy web-app-wrong-selector -n kubearmor-demo
```

Success criteria:

- [ ] You confirmed that the wrong selector does not match the target Pod.
- [ ] You can explain why the policy object can exist without protecting any workload.
- [ ] You removed the deliberately wrong policy before cleanup.

### Step 7: Write the Runbook Decision

In your notes, write a short production rollout decision for this workload. Include the evidence you collected, which controls you would block first, which behaviors need more observation, and how you would roll back if readiness checks or user traffic failed. This written step matters because runtime security is an operational practice, not just a YAML exercise.

Success criteria:

- [ ] Your decision names the workload, namespace, and selector.
- [ ] Your decision lists at least two blocked behaviors and why they are safe to block.
- [ ] Your decision lists at least one behavior that needs more observation before blocking.
- [ ] Your rollback plan includes the policy name and the command or Git revert path you would use.

### Cleanup

```bash
k delete namespace kubearmor-demo
```

Cleanup success criteria:

- [ ] The `kubearmor-demo` namespace is deleted.
- [ ] No demo KubeArmor policies remain in the cluster.
- [ ] You preserved your notes about selector validation, audit evidence, and rollout decision.

---

## Next Module

You've completed the security tools toolkit. Continue to [Platform Engineering Disciplines](/platform/disciplines/) to learn how runtime security controls fit into broader platform operating models.
