---
title: "Module 3.6: Security Basics (Theory)"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.6-security-basics
sidebar:
  order: 7
---

> **Complexity**: `[QUICK]` - Foundations only
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Modules 3.1-3.5 (Cloud Native Architecture)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the key Kubernetes security concepts: RBAC, NetworkPolicies, Secrets, and Pod Security Standards
2. **Identify** common security misconfigurations that lead to real-world breaches
3. **Compare** authentication, authorization, and admission control as layers of API security
4. **Evaluate** whether a given cluster configuration follows security best practices

---

## Why This Module Matters

In February 2018, security researchers discovered that Tesla's Kubernetes dashboard was publicly accessible with no authentication. Attackers had slipped in, deployed cryptocurrency mining containers across Tesla's cloud infrastructure, and hid the evidence by keeping CPU usage artificially low. The breach was not caused by a sophisticated zero-day exploit. It was caused by a missing password on an admin console.

This incident illustrates a pattern that repeats across the industry: most Kubernetes security failures come from misconfiguration, not from advanced attacks. Default settings left unchanged, overly permissive access controls, and unvetted container images account for the vast majority of real-world breaches.

This module gives you the conceptual foundation to understand Kubernetes security. You will not configure anything here -- that is for higher-level certifications like CKS and KCSA. Instead, you will learn the mental model that makes all of those hands-on skills make sense.

---

## The Three Gates: A Building Security Analogy

Imagine entering a secure office building. You pass through three checkpoints, and each one catches a different category of threat.

```
THE THREE SECURITY GATES

  YOU ──► GATE 1 ──► GATE 2 ──► GATE 3 ──► INSIDE
          Badge       Bag Check   Seatbelt

  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
  │   GATE 1:      │  │   GATE 2:      │  │   GATE 3:      │
  │   BADGE         │  │   BAG CHECK    │  │   SEATBELT     │
  │                │  │                │  │                │
  │ "Who are you?" │  │ "What are you  │  │ "What can you  │
  │ "What can you  │  │  bringing in?" │  │  do once        │
  │  access?"      │  │                │  │  inside?"      │
  │                │  │                │  │                │
  │ K8s: RBAC      │  │ K8s: Image     │  │ K8s: Pod       │
  │ Identity &     │  │ trust, scans,  │  │ Security,      │
  │ permissions    │  │ provenance     │  │ NetworkPolicy  │
  └────────────────┘  └────────────────┘  └────────────────┘
```

**Gate 1 -- Badge (Identity & Access)**: Your badge determines who you are and which doors you can open. In Kubernetes, RBAC controls which users and service accounts can perform which actions on which resources.

**Gate 2 -- Bag Check (Image Trust)**: Security scans your bag before you enter. In Kubernetes, image scanning and provenance verification ensure that only trusted, vulnerability-free software runs in your cluster.

**Gate 3 -- Seatbelt (Runtime Safety)**: Once inside, seatbelts, fire exits, and safety rules limit the damage if something goes wrong. In Kubernetes, Pod Security Standards and NetworkPolicies restrict what containers can do and who they can talk to.

Each gate is independent. A failure at any single gate can lead to a breach, even if the other two are solid. Defense in depth means all three must be in place.

---

## Gate 1: Identity and Access Control (RBAC)

Role-Based Access Control (RBAC) is the primary authorization mechanism in Kubernetes. It answers two questions: "Who is this?" and "What are they allowed to do?"

### Subjects, Roles, and Bindings

RBAC has three building blocks:

```
RBAC FLOW

  SUBJECT              BINDING              ROLE               RESOURCE
  (who)                (glue)               (permissions)      (what)

  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
  │ User     │    │              │    │ Role         │    │ Pods     │
  │ Group    │───►│ RoleBinding  │───►│ (namespace)  │───►│ Secrets  │
  │ Service  │    │ or Cluster   │    │ or Cluster   │    │ ConfigMaps│
  │ Account  │    │ RoleBinding  │    │ Role (global)│    │ Deploys  │
  └──────────┘    └──────────────┘    └──────────────┘    └──────────┘

  "Who"            "connects"           "can do what"       "to which
                    who to what                              things"
```

- **Subject**: A user, a group, or a ServiceAccount (the identity used by pods).
- **Role / ClusterRole**: A list of permissions (which verbs on which resources). A Role is scoped to a single namespace. A ClusterRole applies cluster-wide.
- **RoleBinding / ClusterRoleBinding**: The glue that attaches a subject to a role.

### Example: A Minimal RBAC Configuration

This Role grants read-only access to ConfigMaps and Secrets in a single namespace, and the RoleBinding attaches it to a ServiceAccount named `app`:

```yaml
# Minimal Role + Binding example (namespace-scoped)
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: read-config
rules:
- apiGroups: [""]
  resources: ["configmaps","secrets"]
  verbs: ["get","list"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: bind-read-config
subjects:
- kind: ServiceAccount
  name: app
roleRef:
  kind: Role
  name: read-config
  apiGroup: rbac.authorization.k8s.io
```

### The Principle of Least Privilege

Every subject should have only the permissions it needs and nothing more. In practice this means:

- Create dedicated ServiceAccounts per workload instead of using the `default` SA.
- Use namespace-scoped Roles instead of ClusterRoles when possible.
- Never grant wildcard verbs (`*`) or wildcard resources (`*`) unless you have an explicit, documented reason.
- Audit who has `cluster-admin` -- this role can do anything to anything.

---

## Gate 2: Image Trust

A container image is a black box of software. If you run an image you have not verified, you are trusting whoever built it with full access to your cluster's resources.

### Why Tags Lie

Consider this image reference: `nginx:1.25`. The tag `1.25` looks specific, but tags are mutable pointers. The image behind `nginx:1.25` today might be different from the one behind `nginx:1.25` tomorrow. Someone could push a compromised image under the same tag.

An image digest, on the other hand, is a cryptographic hash of the image contents:

```
TAG (mutable -- can change)
  nginx:1.25

DIGEST (immutable -- content-addressed)
  nginx@sha256:6a5db2a1c89e0deaf...

If a single byte changes, the digest changes.
Tags can be re-pointed. Digests cannot be faked.
```

For production workloads, referencing images by digest guarantees you are running exactly the image you tested.

### Image Scanning

Image scanning tools inspect the layers of a container image and compare installed packages against databases of known vulnerabilities (CVEs). Scanning answers questions like:

- Does this image contain a version of OpenSSL with a known critical vulnerability?
- Is the base image outdated?
- Are there packages installed that the application does not need?

Scanning does not make images secure by itself. It gives you visibility so you can make informed decisions about what to deploy.

### Image Provenance

Provenance answers the question: "Where did this image come from, and was it built by a trusted pipeline?" Signing images with tools like cosign or Notary creates a verifiable chain of custody from source code to running container. At the KCNA level, you just need to know the concept exists and why it matters.

---

## Gate 3: Pod Security and Network Segmentation

Once a workload is running, you need to limit the damage it can cause if it is compromised.

### What Running as Root Means

By default, many container images run their processes as the `root` user inside the container. If an attacker exploits a vulnerability in that application, they inherit root privileges. Combined with certain misconfigurations (like a mounted host filesystem or extra Linux capabilities), this can lead to a full node compromise -- meaning the attacker escapes the container entirely and controls the underlying machine.

### Why Host Networking Is Dangerous

A pod with `hostNetwork: true` shares the node's network namespace. It can see all network traffic on the node, bind to any port, and potentially intercept traffic meant for other pods. This bypasses Kubernetes networking entirely and should only be used for specific infrastructure components like CNI plugins.

### Pod Security Standards

Kubernetes defines three levels of pod security restriction, enforced by the built-in Pod Security Admission controller:

| Level | What It Allows | Use Case |
|---|---|---|
| **Privileged** | Everything. No restrictions. | System-level infrastructure (CNI, storage drivers) |
| **Baseline** | Blocks the most dangerous settings (hostNetwork, privileged containers, hostPath) while remaining broadly compatible | General-purpose workloads with minimal changes |
| **Restricted** | Requires running as non-root, drops all capabilities, enforces read-only root filesystem | Security-sensitive and hardened workloads |

Think of these as presets. Most workloads should target Baseline at minimum. Security-conscious teams aim for Restricted.

### Network Segmentation with NetworkPolicies

By default, every pod in a Kubernetes cluster can communicate with every other pod. This means a compromised pod in one namespace could reach databases, admin interfaces, or internal APIs in another namespace.

NetworkPolicies act as firewall rules for pods. They let you declare which pods can talk to which other pods, and on which ports:

```
WITHOUT NetworkPolicy          WITH NetworkPolicy

  ┌─────┐     ┌─────┐          ┌─────┐     ┌─────┐
  │ Web │────►│ DB  │          │ Web │────►│ DB  │
  └─────┘     └─────┘          └─────┘     └─────┘
      │                                        X
      │                                        │ (blocked)
  ┌─────┐     ┌─────┐          ┌─────┐     ┌─────┐
  │ Log │────►│ DB  │          │ Log │     │ DB  │
  └─────┘     └─────┘          └─────┘     └─────┘

  Everyone can reach              Only Web can
  everything                      reach DB
```

At the KCNA level, know that NetworkPolicies exist, that they are namespace-scoped, and that they implement a default-deny posture when configured -- meaning traffic is blocked unless a policy explicitly allows it.

---

## Did You Know?

1. **The default ServiceAccount in every namespace automatically gets mounted into every pod** that does not specify a different one. If that SA has broad permissions, every pod in the namespace inherits them -- even pods that never need to call the Kubernetes API.

2. **Over 60% of container images in public registries contain at least one known critical or high-severity vulnerability**, according to recurring industry surveys. Running unscanned public images is like inviting strangers into your building without a bag check.

3. **Kubernetes RBAC was not always the default**. Before Kubernetes 1.8, the default authorization mode was ABAC (Attribute-Based Access Control), which required restarting the API server to change policies. RBAC was promoted to stable in 1.8 and became the standard.

4. **A single pod with `privileged: true` and `hostPID: true`** can see and interact with every process on the node, effectively giving it full control of the host machine. This is why the Restricted Pod Security Standard explicitly forbids both settings.

---

## Common Mistakes

| Mistake | Why It Is Dangerous | What To Do Instead |
|---|---|---|
| Using the `default` ServiceAccount for all workloads | Every pod gets the same permissions; one compromised pod exposes everything | Create a dedicated SA per workload with only the RBAC it needs |
| Granting `cluster-admin` to CI/CD pipelines | A compromised pipeline can delete any resource in any namespace | Create a scoped Role with only the verbs and resources the pipeline uses |
| Referencing images by tag (`:latest` or `:v2`) | Tags are mutable; the image can change without you knowing | Use digests (`@sha256:...`) for production deployments |
| Running containers as root | Container escape vulnerabilities become full node compromises | Set `runAsNonRoot: true` in the pod's security context |
| No NetworkPolicies in any namespace | Every pod can talk to every other pod, including databases and admin APIs | Apply a default-deny ingress policy per namespace, then allow specific traffic |
| Using wildcard RBAC rules (`verbs: ["*"]`) | Accidentally grants destructive permissions (delete, escalate) | List each verb explicitly: `get`, `list`, `watch`, `create`, `update` |

---

## Knowledge Check

**Question 1**: Your company uses `myapp:production` as the image tag for all deployments. A developer pushes a new build to the same tag. What security risk does this create, and how would you address it?

<details>
<summary>Answer</summary>

Mutable tags mean the image content can change without the reference changing. A deployment using `myapp:production` might pull a different image on each node or after a restart, potentially running untested or compromised code. This also breaks reproducibility -- you cannot tell which exact image is running. The fix is to reference images by their content-addressable digest (e.g., `myapp@sha256:abc123...`), which guarantees immutability. If the image content changes, the digest changes too.

</details>

**Question 2**: An intern deployed a pod with `privileged: true`. What risks does this create?

<details>
<summary>Answer</summary>

A privileged container has full access to all Linux capabilities and can interact with the host kernel directly. If an attacker compromises the application running in that pod, they can escape the container, access the host filesystem, manipulate other containers on the same node, and potentially pivot to other nodes. This effectively turns a single application vulnerability into a full cluster compromise. The pod should be redeployed without privileged mode and with a Restricted or Baseline Pod Security Standard enforced on the namespace.

</details>

**Question 3**: A team creates a single ClusterRole with `resources: ["*"]` and `verbs: ["*"]`, then binds it to all developers via a ClusterRoleBinding. Why is this a problem?

<details>
<summary>Answer</summary>

This grants every developer full administrative access to every resource in every namespace, including the ability to read Secrets, delete Deployments, modify RBAC rules, and even escalate their own permissions further. It violates the principle of least privilege entirely. If any developer's credentials are compromised, the attacker gains unlimited cluster access. Instead, each team should receive namespace-scoped Roles with only the specific verbs and resources they need for their workloads.

</details>

**Question 4**: Your cluster has no NetworkPolicies configured. A pod in the `frontend` namespace is compromised. What can the attacker reach?

<details>
<summary>Answer</summary>

Without NetworkPolicies, Kubernetes allows all pod-to-pod communication by default. The attacker can reach every pod in every namespace -- databases in the `backend` namespace, admin tools in the `monitoring` namespace, and any internal API. They can also attempt to reach the Kubernetes API server if the pod's ServiceAccount has permissions. The mitigation is to apply default-deny NetworkPolicies to each namespace and then create explicit allow rules only for the traffic flows that are actually required.

</details>

**Question 5**: A security audit finds that 200 pods across 15 namespaces are all using the `default` ServiceAccount. The `default` SA has a ClusterRoleBinding to a role that allows reading Secrets cluster-wide. What is the blast radius, and how would you remediate it?

<details>
<summary>Answer</summary>

The blast radius is severe: every one of those 200 pods can read every Secret in every namespace, including database passwords, API keys, and TLS certificates. A compromise of any single pod gives the attacker access to all cluster secrets. Remediation requires two steps: first, remove the ClusterRoleBinding from the `default` ServiceAccount; second, create individual ServiceAccounts for each workload with only the specific permissions each one needs. Pods that do not need Kubernetes API access should have `automountServiceAccountToken: false` set.

</details>

---

## Security Audit Exercise

Review the following eight pod configurations. For each one, identify which of the Three Gates it violates (Badge, Bag Check, or Seatbelt) and explain why.

| # | Pod Configuration | Which Gate? | Why? |
|---|---|---|---|
| 1 | Uses the `default` ServiceAccount with `cluster-admin` binding | ? | ? |
| 2 | Image referenced as `myapp:latest` from Docker Hub | ? | ? |
| 3 | `privileged: true` in the security context | ? | ? |
| 4 | No NetworkPolicy in the namespace; pod connects to all backends | ? | ? |
| 5 | ServiceAccount with `verbs: ["*"]` on all resources | ? | ? |
| 6 | Image from a private registry, pinned by digest, but not scanned | ? | ? |
| 7 | Runs as root with `hostPath: /` mounted | ? | ? |
| 8 | Uses a scoped SA and scanned image, but `hostNetwork: true` | ? | ? |

<details>
<summary>Answers</summary>

| # | Gate Violated | Explanation |
|---|---|---|
| 1 | Badge (Gate 1) | The default SA with cluster-admin means every pod in the namespace has unlimited access. This is an identity and access control failure. |
| 2 | Bag Check (Gate 2) | The `:latest` tag is mutable and the image comes from a public registry with no mention of scanning. You do not know what you are running. |
| 3 | Seatbelt (Gate 3) | Privileged mode removes all container isolation. A compromised process has full host access. |
| 4 | Seatbelt (Gate 3) | No NetworkPolicy means no network segmentation. The pod can reach any other pod, expanding the blast radius. |
| 5 | Badge (Gate 1) | Wildcard verbs on all resources violates least privilege. This SA can delete, create, and escalate anything. |
| 6 | Bag Check (Gate 2) | Pinning by digest ensures immutability, but without scanning you do not know if the image contains known vulnerabilities. |
| 7 | Seatbelt (Gate 3) | Running as root with the entire host filesystem mounted means a container escape gives full node control. |
| 8 | Seatbelt (Gate 3) | Host networking bypasses all Kubernetes network controls. The pod can sniff traffic and bind to node ports. |

</details>

---

## What Is Next?

Continue to [Module 3.7: Community and Collaboration](/k8s/kcna/part3-cloud-native-architecture/module-3.7-community-collaboration/) to learn how open-source governance, SIGs, and the CNCF ecosystem shape Kubernetes development.
