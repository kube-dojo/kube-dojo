---
revision_pending: false
title: "Module 0.2: Security Lab Setup"
slug: k8s/cks/part0-environment/module-0.2-security-lab
sidebar:
  order: 2
lab:
  id: cks-0.2-security-lab
  url: https://killercoda.com/kubedojo/scenario/cks-0.2-security-lab
  duration: "45-60 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Multiple tools to install
>
> **Time to Complete**: 45-60 minutes
>
> **Prerequisites**: Working Kubernetes cluster (from CKA), kubectl configured

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Deploy** a reproducible CKS security lab with audit logging, Trivy, Falco, kube-bench, kubesec, and vulnerable practice targets.
2. **Configure** Kubernetes 1.35+ nodes and API server settings for audit logging, AppArmor, and seccomp validation.
3. **Diagnose** security tool installation failures by comparing driver choice, node support, log output, and expected cluster state.
4. **Evaluate** lab findings from scanners, runtime alerts, and CIS checks to choose a safe remediation practice path.

---

## Why This Module Matters

Exercise scenario: You have a working Kubernetes cluster from CKA practice, but the first CKS drill asks you to scan an image, inspect an audit log, harden a risky pod, and explain a runtime alert under exam pressure. Nothing in that workflow is difficult when the lab is prepared, yet each step becomes slow if the scanner database is missing, the API server has no audit policy, or Falco cannot load the right driver for the node kernel. A security lab is the difference between learning the exam skill and debugging the study environment.

The CKS exam is practical, so the lab must behave like a small security workstation rather than a generic cluster. Trivy gives you a fast feedback loop for image and manifest scanning, kube-bench turns CIS benchmark checks into repeatable evidence, kubesec gives you static manifest feedback, and Falco turns runtime behavior into alerts you can read and reason about. Audit logging, AppArmor, and seccomp are not separate trivia topics here; they are the cluster surfaces that make those tools meaningful.

This module builds a focused lab around Kubernetes 1.35+ concepts while preserving the lightweight setup that makes repeated practice possible. You will choose between a kind cluster and a kubeadm cluster, add audit logging where the API server can actually write logs, install the tools with clear validation points, and deploy deliberately vulnerable workloads inside an isolated namespace. The goal is not to make an internet-exposed training cluster; the goal is to create a controlled environment where bad security posture is visible, measurable, and reversible.

---

## Lab Architecture

The lab has three layers that should stay mentally separate while you work. The cluster layer provides Kubernetes primitives such as the API server, kubelet, container runtime, namespaces, and admission controls. The observation layer adds tools that inspect those primitives from different angles: Trivy sees images and manifests, Falco sees runtime events, kube-bench sees host and component configuration, and kubesec sees static pod specifications. The practice layer contains intentionally insecure workloads that give the tools something useful to report.

```text
┌─────────────────────────────────────────────────────────────┐
│              CKS SECURITY LAB                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Kubernetes Cluster                        │   │
│  │                                                     │   │
│  │  Security Tools Deployed:                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐            │   │
│  │  │ Falco   │ │ Trivy   │ │ kube-bench│            │   │
│  │  │(runtime)│ │(scanner)│ │(CIS audit)│            │   │
│  │  └─────────┘ └─────────┘ └───────────┘            │   │
│  │                                                     │   │
│  │  Security Features Enabled:                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────┐            │   │
│  │  │AppArmor │ │ seccomp │ │  Audit    │            │   │
│  │  │profiles │ │profiles │ │  Logging  │            │   │
│  │  └─────────┘ └─────────┘ └───────────┘            │   │
│  │                                                     │   │
│  │  Vulnerable Apps (for practice):                   │   │
│  │  ┌─────────────────────────────────────────┐      │   │
│  │  │ Intentionally insecure deployments      │      │   │
│  │  │ for scanning and hardening practice     │      │   │
│  │  └─────────────────────────────────────────┘      │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The diagram shows a single cluster boundary because the first rule of this lab is containment. Vulnerable pods, privileged containers, and old images belong in a namespace that exists only for study, not in a shared development cluster. Treat the namespace like a workshop bench: you can place sharp tools on it because you control the room, label the work clearly, and clean up when the drill is complete.

The second rule is that every security signal should have a known source. If Trivy reports vulnerable packages, you should know whether it scanned a registry image, a filesystem, or a Kubernetes manifest. If Falco raises an alert, you should know whether the event came from a process in a container, a file operation on the host, or a Kubernetes metadata enrichment path. If kube-bench reports a failed control, you should know whether the check belongs to the API server, kubelet, etcd, or node operating system.

The third rule is reproducibility. A lab that works once but cannot be rebuilt is a liability during exam preparation, because the broken state becomes indistinguishable from the lesson state. Keep cluster creation, tool installation, vulnerable workloads, and validation commands close together in versioned notes so you can reset after experiments. For CKS practice, a quick rebuild is often more valuable than preserving a messy cluster that has accumulated unknown changes.

Think of the lab as an evidence factory. Every drill should produce one artifact you can inspect: a scanner report, an audit event, a Falco alert, a kube-bench result, or a changed pod spec. When the artifact is missing, the missing artifact is the bug to diagnose. This framing keeps the module practical because you are not simply installing tools; you are proving that each part of the environment can generate evidence when a security-relevant action happens.

The tools also differ in time horizon, which affects how you interpret their results. Trivy and kubesec are strongest before deployment because they inspect inputs that can be changed before a workload runs. Audit logs and Falco are strongest during and after activity because they record behavior and control-plane requests. kube-bench sits between those views by checking cluster configuration against a benchmark. A senior operator compares the time horizon of the tool to the time horizon of the risk before deciding what to fix.

> **Stop and think**: Why do you think audit logging is not enabled by default in Kubernetes? Consider disk usage, event volume, sensitive request bodies, and the operational cost of retaining logs before you decide where audit data belongs in a study lab.

---

## Build the Cluster and Audit Trail

Start with the cluster decision because it determines how close your lab is to exam mechanics. A kind cluster is fast, disposable, and excellent for repeated scanner, manifest, and admission practice. A kubeadm cluster is slower to rebuild, but it exposes static pod manifests and node-level paths in a way that looks much closer to what you see during CKA and CKS drills. Both are valid, but they teach slightly different failure modes.

For most learners, kind is the right first lab because it removes infrastructure noise while keeping Kubernetes behavior real enough for useful practice. The configuration below creates a control-plane node with audit policy and audit log mounts, then adds two workers so scheduling behavior is not overly artificial. Notice that the API server flags reference files inside the node container, while `extraMounts` maps those paths back to files and directories on your host.

The kind configuration deserves a slow read before you run it. The `kubeadmConfigPatches` section changes the control-plane configuration used inside the kind node, while `extraMounts` changes what files from your workstation appear inside that node. Those two mechanisms must agree on the same paths. If the API server flag points at `/etc/kubernetes/audit-policy.yaml` but the host file is mounted somewhere else, the cluster can fail to start or start without the policy you intended to test.

The audit policy levels also deserve deliberate choices. `Metadata` records who, what, when, and where without storing the full object body, which is often enough for Secrets and ConfigMaps in a study lab. `Request` records the request body but not the response, which is helpful when you want to see pod creation details. `RequestResponse` records more, but it can capture sensitive content and create more volume. Choose the lightest level that supports the exercise you are running.

```bash
# Create kind cluster with audit logging enabled
cat <<EOF > kind-cks.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        audit-policy-file: /etc/kubernetes/audit-policy.yaml
        audit-log-path: /var/log/kubernetes/audit.log
        audit-log-maxage: "30"
        audit-log-maxbackup: "3"
        audit-log-maxsize: "100"
      extraVolumes:
      - name: audit-policy
        hostPath: /etc/kubernetes/audit-policy.yaml
        mountPath: /etc/kubernetes/audit-policy.yaml
        readOnly: true
        pathType: File
      - name: audit-logs
        hostPath: /var/log/kubernetes
        mountPath: /var/log/kubernetes
        pathType: DirectoryOrCreate
  extraMounts:
  - hostPath: ./audit-policy.yaml
    containerPath: /etc/kubernetes/audit-policy.yaml
    readOnly: true
  - hostPath: ./audit-logs
    containerPath: /var/log/kubernetes
- role: worker
- role: worker
EOF

# Create the audit log directory on the host
mkdir -p audit-logs

# Create basic audit policy
cat <<EOF > audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Request
  resources:
  - group: ""
    resources: ["pods"]
- level: None
  users: ["system:kube-proxy"]
  verbs: ["watch"]
  resources:
  - group: ""
    resources: ["endpoints", "services"]
- level: Metadata
  omitStages:
  - RequestReceived
EOF

# Create the cluster
kind create cluster --name cks-lab --config kind-cks.yaml

# Prove audit logging before installing security tools
kubectl wait --for=condition=Ready node --all --timeout=120s

kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: audit-test
  namespace: default
spec:
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.10
EOF

kubectl wait --for=condition=Ready pod/audit-test --timeout=60s
sleep 2

# Host-mounted audit log (kind maps /var/log/kubernetes inside the node to ./audit-logs)
grep '"resource":"pods"' audit-logs/audit.log | tail -5
grep '"verb":"create"' audit-logs/audit.log | grep audit-test | tail -3

kubectl delete pod audit-test --wait=false
```

The audit policy is intentionally small because this is a lab, not an enterprise logging architecture. It records metadata for Secrets and ConfigMaps, request bodies for Pods, suppresses noisy kube-proxy watch traffic, and drops the earliest stage to reduce duplicate records. That gives you enough signal to practice reading audit output without filling the host directory with every watch event produced by normal cluster operation.

Before running this, predict where the first useful audit event will appear after you create a pod. If you answered "inside the API server container only," look again at the host mount and log path relationship. The API server writes to `/var/log/kubernetes/audit.log` from its perspective, but kind maps that directory back to `./audit-logs` on your workstation, which lets you inspect the file without entering the node container.

After the cluster comes up, create one harmless pod and then inspect the newest audit log lines before installing any security tools. This early check prevents a common study trap where learners install Trivy, Falco, and kube-bench successfully, then discover later that audit evidence was never configured. The correct sequence is cluster, audit evidence, tool installation, vulnerable targets, and validation. Reordering that sequence is possible, but it makes failures harder to attribute.

A kubeadm cluster teaches the same concept through static pod manifests. The API server is a pod launched by kubelet from `/etc/kubernetes/manifests/kube-apiserver.yaml`, so a configuration mistake often appears as a control-plane pod restart rather than a neat command failure. That is useful exam preparation because you need to connect file edits, kubelet reconciliation, mounted host paths, and API server startup behavior under time pressure.

When editing the kubeadm API server manifest, make one class of change at a time. Add the policy file on disk first, then add the log directory, then add the volume and mount entries, and finally add the audit flags. This order gives kubelet a real file and directory to mount before the API server starts with the new arguments. If you add flags first and paths later, the API server may fail in a way that looks like an argument problem even though the missing host path is the root cause.

```bash
# Enable audit logging on existing cluster
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml on control plane

# Add these flags to the API server:
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# --audit-log-path=/var/log/kubernetes/audit.log
# --audit-log-maxage=30
# --audit-log-maxbackup=3
# --audit-log-maxsize=100

# You must also add these volumeMounts inside the container spec:
# - mountPath: /etc/kubernetes/audit-policy.yaml
#   name: audit-policy
#   readOnly: true
# - mountPath: /var/log/kubernetes
#   name: audit-logs

# And these volumes at the bottom of the pod spec:
# - hostPath:
#     path: /etc/kubernetes/audit-policy.yaml
#     type: File
#   name: audit-policy
# - hostPath:
#     path: /var/log/kubernetes
#     type: DirectoryOrCreate
#   name: audit-logs

# Create the audit policy file
sudo mkdir -p /etc/kubernetes
sudo tee /etc/kubernetes/audit-policy.yaml <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods"]
    verbs: ["create", "delete"]
- level: Metadata
  omitStages:
  - RequestReceived
EOF

# Create log directory
sudo mkdir -p /var/log/kubernetes
```

The kubeadm path has one extra risk: a YAML indentation error in a static pod manifest can temporarily remove your API server. That sounds dramatic, but kubelet keeps trying to reconcile the file, so the fix is usually to correct the manifest and wait for the control plane to come back. In an exam-style environment, always keep a second terminal available on the control-plane node so you can inspect kubelet logs or move a malformed manifest out of the watched directory if needed.

Do not turn audit logging into a maximal data capture exercise. Request bodies can include sensitive material, log volume grows quickly, and audit retention is part of the design. In this lab, the policy should be just broad enough to demonstrate create, delete, and metadata events for security-relevant resources. In production, the policy would be reviewed with storage, privacy, legal retention, and incident-response requirements in mind.

There is one more audit habit worth building now: always record the action that should create the event. If you apply a pod, write down the namespace, pod name, verb, and approximate time before searching logs. Audit records are structured, but they are still easy to misread when several controllers are active. Looking for a specific create or delete event trains you to use audit logs as evidence rather than as a scrolling wall of JSON.

---

## Install Security Tools as Feedback Loops

Install the tools with a clear mental model instead of treating them as a shopping list. Trivy answers "what known weaknesses are present before or at deployment time," Falco answers "what suspicious behavior is happening at runtime," kube-bench answers "how this cluster compares to CIS benchmark checks," and kubesec answers "what risky fields are visible in a manifest." When you know the question each tool answers, you can diagnose wrong output faster.

Trivy is the first tool because it gives quick feedback with very little cluster dependency. The command below preserves the familiar Debian repository installation, a macOS Homebrew path, a version check, and a test scan against `nginx:latest`. In real work you should pin images and avoid relying on `latest`, but scanning a common tag during setup is useful because it quickly proves that the scanner can download its vulnerability database and read image metadata.

Scanner setup has two separate success conditions. The binary must run, and the vulnerability database must be available. A version command proves only the first condition. A real image scan proves the second because Trivy has to resolve the image layers, download or read its database, and match packages against known vulnerability records. If the scan fails because of network or cache problems, fix that before introducing Kubernetes manifests into the test.

```bash
# Install Trivy CLI
# On Ubuntu/Debian
sudo apt-get install wget apt-transport-https gnupg lsb-release -y
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy -y

# On macOS
brew install trivy

# Verify installation
trivy --version

# Test scan
trivy image nginx:latest
```

Raw vulnerability counts are a poor decision metric. An image can show many low-severity findings because it contains a general-purpose operating system layer, while a smaller image can still contain one critical vulnerability that matters immediately. During practice, run the broad scan first to confirm the tool works, then repeat with severity filters, fixed-version checks, and manifest scans so you learn how to turn noisy findings into an action plan.

For exam practice, the important Trivy move is to narrate your triage. Say which image you scanned, which severities you filtered for, whether fixed versions exist, and what workload would consume the image. That narration prevents a shallow answer such as "use a smaller image" when the real fix might be to update one package, choose a maintained tag, or block the deployment until a patched base image is available. The command is simple; the decision is the skill.

Falco is a different class of tool because it must observe kernel-level events from the nodes that run your containers. That means driver choice matters more than chart installation success. The modern eBPF driver is the preferred path on supported kernels, while some local clusters require the kernel module driver or another fallback. A Helm release can be deployed cleanly and still fail at runtime if the node cannot load the required probe.

Treat Falco installation as a negotiation between the chart, the node kernel, and the container runtime. The chart chooses how Falco tries to observe events, the kernel decides which mechanisms are available, and the runtime shapes which container metadata Falco can enrich into alerts. A namespace full of healthy-looking Kubernetes objects is not enough. You need a running Falco pod and logs that show the driver initialized successfully.

```bash
# Install Falco using Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install Falco with modern eBPF driver
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=modern_ebpf \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# For kind clusters, use kernel module driver instead
# helm install falco falcosecurity/falco \
#   --namespace falco \
#   --create-namespace \
#   --set driver.kind=kmod

# Verify Falco is running
kubectl get pods -n falco

# Check Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco
```

Pause and predict: if the Falco pods show `CrashLoopBackOff`, what evidence would let you distinguish a bad Helm value from an unsupported kernel driver? Start with pod events and Falco logs, then connect the error to node kernel capability. If the logs mention unsupported eBPF features, upgrading the chart will not fix the node; you need a compatible driver, a different cluster, or a host kernel that supports the required eBPF behavior.

FalcoSidekick and its web UI are included because they make alerts easier to inspect during practice, not because every exam task requires a dashboard. The essential skill is reading the alert fields and connecting them to the workload that produced the behavior. If you later remove the UI for a leaner lab, keep the core Falco logs available because those logs are the evidence you will use when the dashboard is absent.

Once Falco runs, generate a harmless test event and read the alert before moving on. A common practice is to execute an interactive shell in a test container or run a command that triggers one of Falco's default rules. Do this only in the lab namespace, then map the alert fields back to the pod, container, process, and rule name. That exercise proves the runtime path is functioning and teaches you what normal Falco evidence looks like.

kube-bench works best when you view it as a benchmark interpreter rather than a magic score generator. It maps cluster configuration to CIS Kubernetes Benchmark controls, then reports pass, fail, warn, or manual checks. In a kind cluster, some checks are expected to look unusual because the control plane runs inside containers; in a kubeadm cluster, the output is closer to the host paths and static manifests covered by CKA practice.

The benchmark language matters because a failed check is not always a command to change the cluster immediately. Some controls are not applicable to a specific distribution, some are managed by a provider, and some are intentionally different in a local lab. During CKS preparation, practice explaining the evidence chain: the control ID, the file or flag checked, the current value, the expected value, and whether the lab environment makes remediation appropriate.

```bash
# Run kube-bench as a job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Wait for completion
kubectl wait --for=condition=complete job/kube-bench --timeout=120s

# View results
kubectl logs job/kube-bench

# For detailed output on a kubeadm control-plane node (Linux amd64 shell — not a macOS laptop)
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.15.5/kube-bench_0.15.5_linux_amd64.tar.gz -o kube-bench.tar.gz
tar -xvf kube-bench.tar.gz
./kube-bench run --targets=master
```

The job-based run is convenient because it keeps the workflow inside Kubernetes, but the direct node run is often more revealing. Some benchmark checks need access to host files such as kubelet configuration, static pod manifests, and certificate paths. If a job cannot see the relevant host path, the result may tell you more about the container environment than the node configuration. That is why the module preserves both approaches.

kubesec gives you a lightweight static analysis pass over manifests. It does not know your full threat model, but it quickly highlights fields such as `runAsUser: 0`, missing security context, broad capabilities, privileged mode, and absent resource controls. That makes it useful before you apply a manifest, especially when you are learning to recognize risky pod settings by sight.

kubesec is also useful as a teaching mirror. When it flags a risky field, open the manifest and ask which Kubernetes control would prevent or mitigate that risk. A privileged container might be blocked by Pod Security Admission, a root process might be changed with `runAsNonRoot`, and missing resource settings might be addressed with LimitRange defaults or review policy. This turns one static finding into a map of possible controls.

```bash
# Scan a manifest with Docker (primary on macOS/arm64 and when no local binary is installed)
docker run --rm -i kubesec/kubesec:v2.14.0 scan /dev/stdin <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
  - name: test
    image: nginx
    securityContext:
      runAsUser: 0
EOF

# Optional binary install — match host OS and architecture (uname -m)
ARCH=$(uname -m)
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
case "${OS}-${ARCH}" in
  linux-x86_64|linux-amd64)
    KUBESEC_URL=https://github.com/controlplaneio/kubesec/releases/download/v2.14.0/kubesec_linux_amd64.tar.gz ;;
  linux-aarch64|linux-arm64)
    KUBESEC_URL=https://github.com/controlplaneio/kubesec/releases/download/v2.14.0/kubesec_linux_arm64.tar.gz ;;
  darwin-x86_64|darwin-amd64)
    KUBESEC_URL=https://github.com/controlplaneio/kubesec/releases/download/v2.14.0/kubesec_darwin_amd64.tar.gz ;;
  darwin-arm64|darwin-aarch64)
    KUBESEC_URL=https://github.com/controlplaneio/kubesec/releases/download/v2.14.0/kubesec_darwin_arm64.tar.gz ;;
  *)
    echo "No binary for ${OS}-${ARCH}; use the Docker one-liner above" >&2; exit 1 ;;
esac
curl -L "$KUBESEC_URL" -o kubesec.tar.gz
tar -xvf kubesec.tar.gz kubesec
sudo mv kubesec /usr/local/bin/
```

Static analysis is not a substitute for admission policy or runtime monitoring. It sees the document you give it, not every mutation that might occur before a pod is admitted, and not the behavior that happens after the container starts. Use kubesec to train your eyes, use admission and policy controls to block bad manifests, and use runtime tools to catch behavior that was not obvious from YAML alone.

The four tools now form a layered feedback loop. Trivy checks software supply risk, kubesec checks manifest posture, kube-bench checks cluster configuration, and Falco checks runtime behavior. None of those views is complete, but together they give you a practical way to answer "where did this risk enter, where should it have been blocked, and where did we observe it?" That is the question behind many CKS troubleshooting tasks.

---

## Verify Node-Level Security Primitives

AppArmor and seccomp are node-level mechanisms, so a Kubernetes API check alone is not enough. The API can accept a pod spec that references a profile, but the kubelet and container runtime still need the relevant support on the node where the pod lands. That scheduling detail matters: a custom profile on one node does not magically exist on every other node unless you place it there or automate distribution.

On a kind cluster hosted from macOS or Windows, node paths such as `/sys/module/apparmor` and `/boot/config-$(uname -r)` live inside the kind node container, not on your laptop kernel. Run the checks below with `docker exec` against a kind node, or SSH to a kubeadm/Linux node and run the kubeadm branch there.

```bash
# kind: check AppArmor inside the control-plane node (not on the macOS host)
CP_NODE=$(kind get nodes --name cks-lab 2>/dev/null | head -1)
if [ -n "$CP_NODE" ]; then
  docker exec "$CP_NODE" cat /sys/module/apparmor/parameters/enabled   # Should output: Y
  docker exec "$CP_NODE" aa-status 2>/dev/null | head -20 || true
else
  # kubeadm/Linux node shell only
  cat /sys/module/apparmor/parameters/enabled
  sudo aa-status
fi
# containerd enables AppArmor support by default when the node kernel provides it
```

AppArmor is easiest to understand as a named rule set loaded into the Linux kernel and then attached to a process. Kubernetes lets you request AppArmor behavior for a container, but the node must have the profile loaded before the workload can use it. In a lab, that means you should verify support on the node itself, then run a small pod experiment after you know the operating system layer is ready.

Do not confuse profile availability with policy intent. A node can have AppArmor enabled and still run containers under a permissive or default profile that does not demonstrate the restriction you wanted to test. For a meaningful lab, record the profile name, the node where it is loaded, the pod field or annotation that requests it, and the behavior you expect it to block. Without that chain, a successful pod start tells you very little.

Seccomp is similar in spirit but different in what it restricts. Instead of naming file and capability rules like AppArmor, seccomp filters system calls, which are the low-level requests a process makes to the kernel. Kubernetes supports the `RuntimeDefault` profile and custom localhost profiles, but a custom profile must be present under the kubelet seccomp root on the node that runs the pod.

The `RuntimeDefault` profile is a useful baseline because it gives you a safer default without managing a custom JSON file for every exercise. Custom profiles are still worth practicing because they teach the locality rule and the failure mode when a profile cannot be found. Start with `RuntimeDefault` when the learning goal is general hardening, then use a localhost profile when the learning goal is path placement and node-specific troubleshooting.

```bash
# kind: check seccomp support inside the node (host /boot/config on macOS is the wrong kernel)
CP_NODE=$(kind get nodes --name cks-lab 2>/dev/null | head -1)
if [ -n "$CP_NODE" ]; then
  docker exec "$CP_NODE" sh -c 'grep CONFIG_SECCOMP /boot/config-$(uname -r) 2>/dev/null || zgrep CONFIG_SECCOMP /proc/config.gz 2>/dev/null'
  docker exec "$CP_NODE" ls /var/lib/kubelet/seccomp/ 2>/dev/null || true
else
  # kubeadm/Linux node shell only
  grep CONFIG_SECCOMP /boot/config-$(uname -r)   # Should see: CONFIG_SECCOMP=y
  ls /var/lib/kubelet/seccomp/
  sudo mkdir -p /var/lib/kubelet/seccomp/profiles
fi
```

Pause and predict: you create `profiles/audit-only.json` on the control-plane node, then schedule a pod onto a worker that references `localhost/profiles/audit-only.json`. What error path do you expect, and where would you look first? The useful answer is not just "the pod fails"; it is that the kubelet on the selected worker asks the runtime for a local profile path that does not exist on that worker.

This is where lab discipline pays off. Label nodes, use explicit scheduling when a profile exists only on one node, and write down which security features are host requirements rather than cluster-wide objects. For Kubernetes 1.35+ practice, the API surface may look clean, but the exam skill is often recognizing whether a failure belongs to admission, kubelet, container runtime, or the host kernel.

One practical diagnostic pattern is to read pod status from the outside in. Start with `kubectl describe pod` to see scheduling and container creation events, then inspect kubelet or runtime logs on the selected node if the event points below the API layer. If the failure mentions a missing profile, do not edit RBAC or NetworkPolicy. Go to the node path, confirm the file exists, confirm the profile name matches the pod reference, and then retry with controlled scheduling.

---

## Deploy Practice Targets and Validate the Lab

Intentionally insecure workloads are useful only when they are isolated, labeled, and disposable. The namespace in the command below is a practice boundary, not a permission boundary by itself. You should still avoid exposing these pods outside your machine, avoid connecting them to shared credentials, and delete the namespace when the drill is done. The point is to create predictable bad examples that scanners and hardening tools can report against.

The namespace should be named plainly because future you will forget why a privileged pod exists. Labels and names such as `insecure-apps`, `privileged-pod`, and `vulnerable-image` make the intent obvious when you review audit logs or scanner output later. Avoid clever names in a security lab. Clear names reduce the chance that an intentionally bad resource is mistaken for an accidental production-like workload.

```bash
# Create namespace for practice
kubectl create namespace insecure-apps

# Deploy vulnerable app 1: Privileged container
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    securityContext:
      privileged: true
EOF

# Deploy vulnerable app 2: Root user
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: root-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    securityContext:
      runAsUser: 0
EOF

# Deploy vulnerable app 3: No resource limits
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: unlimited-pod
  namespace: insecure-apps
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    # No resources specified = unlimited
EOF

# Deploy vulnerable app 4: Vulnerable image
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: vulnerable-image
  namespace: insecure-apps
spec:
  containers:
  - name: app
    image: vulnerables/web-dvwa  # Known vulnerable image
EOF
```

Before applying those pods, ask which controls would block each one in a hardened cluster. Pod Security Admission in a restricted namespace should reject privileged containers and root-friendly settings. An image policy or admission controller could block known vulnerable images before scheduling. ResourceQuota and LimitRange objects could force resource requests and limits, while RBAC controls would decide who is allowed to create the namespace and pods in the first place.

The practice target list is deliberately simple because each pod teaches one diagnostic dimension. The privileged pod trains you to notice dangerous container privileges. The root pod trains you to inspect identity settings. The unlimited pod trains you to connect resource hygiene with reliability and denial-of-service risk. The vulnerable image trains you to separate image findings from runtime behavior and manifest hardening.

This is also a good place to practice control ordering. A vulnerable image can be detected before deployment by a scanner, blocked at admission by policy, observed at runtime if exploited, and later investigated through logs. A privileged pod follows a similar path through static analysis, Pod Security Admission, kubelet admission, and runtime detection. When you can describe the same bad resource across those stages, you are learning the security model rather than memorizing a command.

Validation closes the loop by proving that the lab has the signals you expect. A good validation script does not assert that every finding is clean; in a security lab, some findings should be intentionally bad. Instead, it verifies that the cluster responds, the scanners run, Falco is present if installed, kube-bench can produce output, host features can be checked, and audit logging is at least visible in the API server configuration.

The validation script is intentionally conservative. It avoids changing cluster policy, does not assume Falco is mandatory for every local environment, and reports missing tools without hiding the rest of the checks. That makes it useful during incremental setup. You can run it after the cluster is created, again after scanner installation, and again after vulnerable targets are deployed, then compare the output to see which layer changed.

```bash
#!/bin/bash
echo "=== CKS Lab Validation ==="
echo ""

# Check cluster
echo "1. Cluster Status:"
kubectl cluster-info | head -2
echo ""

# Check Trivy
echo "2. Trivy:"
if command -v trivy &> /dev/null; then
    trivy --version
else
    echo "   NOT INSTALLED"
fi
echo ""

# Check Falco
echo "3. Falco:"
kubectl get pods -n falco -l app.kubernetes.io/name=falco --no-headers 2>/dev/null | head -1 || echo "   NOT RUNNING"
echo ""

# Check kube-bench
echo "4. kube-bench:"
if command -v kube-bench &> /dev/null; then
    echo "   Installed"
else
    echo "   Available as Job"
fi
echo ""

# Check AppArmor
echo "5. AppArmor:"
CP_NODE=$(kind get nodes --name cks-lab 2>/dev/null | head -1)
if [ -n "$CP_NODE" ] && docker exec "$CP_NODE" test -f /sys/module/apparmor/parameters/enabled 2>/dev/null; then
    docker exec "$CP_NODE" cat /sys/module/apparmor/parameters/enabled
elif [ -f /sys/module/apparmor/parameters/enabled ]; then
    cat /sys/module/apparmor/parameters/enabled
else
    echo "   Check inside cluster nodes (kind: docker exec; kubeadm: SSH to node)"
fi
echo ""

# Check Audit Logging
echo "6. Audit Logging:"
if kubectl get pods -n kube-system -l component=kube-apiserver -o yaml 2>/dev/null | grep -q "audit-log-path"; then
    echo "   API server flags: Enabled"
    if [ -f audit-logs/audit.log ]; then
        echo "   Host log lines: $(wc -l < audit-logs/audit.log)"
        grep '"resource":"pods"' audit-logs/audit.log | tail -1 || echo "   No pod events yet — create a test pod"
    fi
else
    echo "   Check API server config"
fi
echo ""

echo "=== Validation Complete ==="
```

Read the validation output as a routing table for your next action. If `kubectl cluster-info` fails, no security tool diagnosis matters yet because the cluster connection is broken. If Trivy is missing, fix the local workstation package path before touching Kubernetes. If Falco is absent or crash looping, inspect the Helm release and driver logs. If audit logging is not visible, return to the API server configuration before expecting meaningful audit exercises.

The most important habit is to capture expected failures separately from unexpected failures. A vulnerable image producing a scary scan is expected. A kube-bench warning caused by a known kind limitation may be expected. A missing audit log file after you deliberately created pods is not expected, because the lab was configured specifically to observe that behavior. That distinction keeps practice productive instead of turning every warning into a panic.

Keep a small lab journal as you validate. For each tool, write the command you ran, the resource it inspected, the expected signal, and the actual signal. This can be a short note, but it should be concrete enough that you can rebuild the lab a week later and know what "ready" meant. Security practice improves fastest when you compare evidence over time instead of relying on memory of a successful setup.

---

## Patterns & Anti-Patterns

The strongest lab pattern is to build feedback loops around one question at a time. If you scan images, evaluate image findings and then change the image or package layer. If you test runtime detection, trigger a behavior and then read Falco's alert fields. If you run kube-bench, choose one failed control and trace it to a file, flag, or kubelet setting. Small loops create durable exam skill because you can explain each result.

The weakest pattern is installing every tool and treating the first output as the lesson. Security tools produce data, but the CKS skill is turning that data into a safe action. That means you should preserve command output for a moment, identify the resource or node involved, decide whether the finding is expected in the lab, and then apply one remediation. If the remediation changes several variables at once, you lose the evidence trail.

Another useful pattern is to maintain one clean baseline and one intentionally broken state. The clean baseline proves the lab itself is healthy. The broken state proves the tool can see the problem. Move between those states deliberately by applying and deleting a small manifest, changing one chart value, or rebuilding a disposable cluster. If the lab is always partially broken, you stop learning which change produced which result.

| Pattern or Anti-Pattern | When It Appears | Operational Consequence | Better Move |
|-------------------------|-----------------|-------------------------|-------------|
| Pattern: disposable kind lab | You need fast scanner and manifest practice | Rebuilds are quick, but host-level realism is limited | Use kind first, then repeat node-path drills on kubeadm |
| Pattern: kubeadm realism | You need static pod, kubelet, and node-path practice | Failures resemble exam tasks, but rebuilds take longer | Snapshot notes before editing control-plane manifests |
| Pattern: isolated insecure namespace | You need practice targets with known bad posture | Findings are intentional and easy to clean up | Label the namespace and delete it after each drill |
| Anti-pattern: chasing raw vulnerability totals | A scan reports a large count | Learners optimize for fewer lines instead of risk | Filter severity, fixed versions, exploitability, and workload context |
| Anti-pattern: ignoring driver compatibility | Falco installs but crashes | The chart looks correct while the node cannot support the probe | Inspect Falco logs and choose a compatible driver |
| Anti-pattern: assuming profiles are cluster objects | A seccomp or AppArmor pod fails on one node | Profiles exist on one host but not where the pod runs | Verify node placement and distribute profiles intentionally |

Patterns are not laws; they are defaults that keep the lab honest. A kind cluster is excellent for repetition, but it can hide host details. A kubeadm cluster is excellent for node realism, but it can waste time if every failed pod turns into infrastructure repair. Use the pattern that teaches the current skill, then switch when the limitation becomes the lesson.

A mature lab also has an exit condition. When the exercise is done, you should know whether to delete a namespace, uninstall a Helm release, remove a benchmark job, or rebuild the cluster. Cleanup is part of security practice because stale vulnerable resources create false signals in later drills. If you cannot explain why a risky pod is still running, the safest assumption is that it should be removed.

---

## Decision Framework

Choose the lab path by asking what evidence you need from the environment. If the evidence is a scanner report, manifest score, or admission result, kind is usually enough. If the evidence is a kubelet path, static pod manifest, kernel profile, or benchmark check that touches the host, kubeadm is usually better. If the evidence is runtime behavior, either cluster can work, but Falco driver support becomes the deciding factor.

| Decision Point | Choose Kind When | Choose Kubeadm When | Risk to Watch |
|----------------|------------------|---------------------|---------------|
| Audit logging | You want quick API server audit practice with host-mounted logs | You want static pod manifest practice and real control-plane paths | Bad manifest edits can interrupt the API server |
| Trivy and kubesec | You mainly need image and YAML feedback loops | You want the same scanner workflow against a longer-lived lab | Scanner output can become noisy without severity triage |
| Falco | Your host kernel and driver choice are known to work | You need more realistic node-level runtime inspection | Driver mismatch can look like a Helm failure |
| kube-bench | You want a quick report for practice interpretation | You need host-level benchmark checks close to exam shape | Containerized jobs may not see every host path |
| AppArmor and seccomp | You only need API-level references and simple experiments | You need to place and validate profiles on actual nodes | Profile location must match the scheduled node |

Use a two-pass approach if you have time. First, build the kind lab and rehearse the tool workflow until commands, namespaces, and cleanup feel routine. Second, repeat the audit, kube-bench, AppArmor, and seccomp tasks on kubeadm so you learn the node paths and static pod behavior. This sequencing keeps the first pass fast while still exposing the operational mechanics that matter on exam-like systems.

When a validation step fails, classify the failure before fixing it. Workstation failures include missing binaries, unreachable package repositories, and scanner database download problems. Cluster failures include broken kubeconfig, failed pods, missing namespaces, and absent API server flags. Node failures include unsupported kernel features, missing profiles, and inaccessible host paths. A correct classification prevents random changes that make the lab harder to reason about.

Use the same classification for remediation planning. Workstation failures usually need package, cache, credential, or network fixes. Cluster failures usually need Kubernetes object inspection, Helm release changes, or API server configuration. Node failures usually need shell access, host file checks, kernel capability checks, or workload rescheduling. If your proposed fix belongs to a different layer than the evidence, pause before applying it.

The decision framework should also account for time. Before a timed practice session, prefer the path with fewer moving parts so you can focus on the exam skill. During a deeper study block, choose the path that exposes the underlying mechanism, even if setup is slower. The lab is not one environment forever; it is a set of tradeoffs you select based on the behavior you need to observe.

---

## Did You Know?

These facts are worth remembering because they explain why the lab has several tools instead of one universal scanner.

- **Falco was originally created in 2016** ([Sysdig release announcement, May 2016](https://sysdig.com/blog/sysdig-falco)) and later became a [CNCF](https://www.cncf.io/projects/falco/) project focused on runtime threat detection for cloud-native workloads.

- **Trivy scans more than container images**; it can inspect filesystems, repositories, Kubernetes resources, and infrastructure-as-code inputs, which makes it useful before and after deployment.

- **The [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes) includes more than 200 checks** across control-plane, etcd, node, policy, and managed-service areas ([kube-bench implements these checks](https://github.com/aquasecurity/kube-bench)), so kube-bench output needs triage rather than blind score chasing.

- **AppArmor and SELinux solve a similar containment problem differently**; Ubuntu-family systems commonly use AppArmor, while RHEL-family systems commonly use SELinux, and CKS practice often emphasizes AppArmor mechanics.

---

## Common Mistakes

Most lab failures are ordinary setup mistakes disguised as security complexity. Use the table as a diagnostic checklist before rebuilding the whole cluster.

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| No audit logging enabled | The cluster starts fine without audit flags, so the missing evidence is noticed only during an exercise | Configure the API server audit policy, log path, retention flags, and required host volumes before running audit drills |
| Falco not running | Helm installation succeeds but the selected driver cannot load on the node kernel | Check Falco pod logs, confirm the driver error, and install with a driver compatible with the lab host |
| Only scanning images once | The first Trivy report feels like completion even though remediation workflow was not practiced | Re-scan after changing image tags, severity filters, package versions, or manifest settings |
| Skipping vulnerable app setup | The tools have no realistic targets, so every drill becomes abstract output reading | Deploy isolated intentionally insecure pods and document which finding each pod is meant to trigger |
| Not checking node-level tools | AppArmor and seccomp are treated like API objects even though profiles and kernel support live on nodes | SSH or enter the node, verify kernel support, profile paths, and scheduling placement |
| Treating kube-bench as a pass/fail badge | Benchmark output is easier to quote than to trace to concrete configuration | Pick one failed check, locate the related file or flag, and decide whether the lab environment makes it expected |
| Leaving practice workloads behind | Insecure pods remain after the drill and confuse later validation output | Delete the `insecure-apps` namespace or rebuild the disposable cluster after each practice session |

---

## Quiz

Use these scenarios to test whether you can route a lab problem to the right layer before changing commands.

<details>
<summary>1. Exercise scenario: You run `trivy image nginx:latest` and get over 140 vulnerabilities. A teammate wants to switch every workload to Alpine-based images immediately. Is that the right response, and what would you do first?</summary>

Switching base images may reduce the number of packages, but it is not automatically the right response. First, filter the report by severity, fixed version availability, package location, and whether the vulnerable component is reachable in the workload. Alpine, distroless, and slim images each have tradeoffs, so the safer action is to evaluate the findings, update or replace the base image deliberately, and re-scan to prove the remediation changed the risk rather than just changing the count.
</details>

<details>
<summary>2. Exercise scenario: You create a custom seccomp profile under `/etc/seccomp/profiles/`, reference it from a pod, and the pod fails during container creation. What went wrong?</summary>

Kubernetes localhost seccomp profiles are resolved relative to the kubelet seccomp directory, commonly `/var/lib/kubelet/seccomp/`, on the node that runs the pod. Placing the file under a general operating-system path does not make it available to kubelet or the container runtime. Move the profile under the kubelet path, reference it with the correct localhost profile name, and make sure the pod schedules onto a node where the file actually exists.
</details>

<details>
<summary>3. Exercise scenario: A reviewer notices `vulnerables/web-dvwa` in the `insecure-apps` namespace and asks why the lab deploys a deliberately vulnerable image. How do you justify it safely?</summary>

The image is a controlled practice target, not a production dependency. It gives Trivy real findings to report and gives the learner a concrete workload to harden with security context, admission policy, and network controls. The safe justification depends on isolation: the namespace must be clearly for lab use, the cluster must not hold real credentials, external exposure must be avoided, and cleanup must be part of the exercise.
</details>

<details>
<summary>4. Exercise scenario: Falco was installed with `driver.kind=modern_ebpf`, but every Falco pod enters `CrashLoopBackOff` and logs mention unsupported kernel features. How do you diagnose and fix it?</summary>

Start with the pod logs and events because the Helm release can exist even when the driver cannot load. The error points to node capability, so upgrading random chart values is unlikely to help. Choose a driver that matches the lab host, such as the kernel module path when appropriate, or move the lab to a host kernel that supports the modern eBPF requirements. After changing the driver, verify with pod status and a simple runtime event.
</details>

<details>
<summary>5. Exercise scenario: kube-bench reports several failed controls when run as a Kubernetes Job in kind. Should you immediately edit every reported setting?</summary>

No. First decide whether each finding reflects the benchmark target, the kind environment, or a real configuration issue you intend to practice. Containerized benchmark jobs may not see every host path the same way a direct node run does, and kind has different control-plane packaging than kubeadm. Pick one check, trace it to the relevant file or flag, and only then decide whether remediation is meaningful in that lab.
</details>

<details>
<summary>6. Exercise scenario: Your audit policy is present, the API server pod is running, but no expected pod-create events appear after you deploy a test pod. What do you check next?</summary>

Check the relationship between the API server flags, mounted policy file, mounted log directory, and the host path where you expect to read logs. The API server might be writing inside its container path while the host directory you inspect is not actually mounted. Also confirm the policy rule includes pod create events at a level that records what you expect. Once the path and rule match, repeat a new pod create action rather than searching for an event that happened before the fixed configuration loaded.
</details>

<details>
<summary>7. Exercise scenario: kubesec flags a pod for `runAsUser: 0`, but the pod is already running in your lab. What is the security lesson and what action would you practice?</summary>

kubesec is static analysis, so it tells you the manifest is risky; it does not retroactively prevent a running pod. The lesson is to separate detection from enforcement. Practice updating the manifest to run as a non-root user, add a stronger security context, and then consider which admission control would block the risky form before it reaches the cluster. Re-run the static scan and inspect the pod spec after redeployment to confirm the change.
</details>

---

## Hands-On Exercise

The exercise turns the module into a repeatable readiness check. Work through the tasks in order because each one narrows the possible failure domain for the next. If a task fails, stop and fix that layer before continuing; a broken cluster connection makes scanner installation irrelevant, and a missing scanner makes vulnerable workload findings less useful.

Do the exercise with a timer only after you have completed it slowly once. The first pass is for building the mental map: which file belongs to the API server, which output proves Trivy is functional, which Falco error points to a driver, and which node path matters for seccomp. The timed pass is for exam fluency. Mixing those goals too early encourages memorized commands without the diagnostic judgment CKS tasks require.

```bash
# 1. Verify cluster is running
kubectl get nodes

# 2. Prove audit logging records pod events (kind: host-mounted ./audit-logs)
kubectl wait --for=condition=Ready node --all --timeout=120s
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: audit-test
  namespace: default
spec:
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.10
EOF
kubectl wait --for=condition=Ready pod/audit-test --timeout=60s
sleep 2
grep '"verb":"create"' audit-logs/audit.log | grep audit-test | tail -3
kubectl delete pod audit-test --wait=false

# 3. Install Trivy and scan an image
trivy image nginx:latest | head -50

# 4. Check Falco is running (if installed)
kubectl get pods -n falco

# 5. Run kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=120s
kubectl logs job/kube-bench | head -100

# 6. Create a test pod and scan the image (apply avoids default SA race on fresh kind 1.35)
until kubectl get sa default -n default >/dev/null 2>&1; do sleep 1; done
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:1.25
EOF
kubectl wait --for=condition=Ready pod/test-pod --timeout=60s
trivy image nginx:1.25

# 7. Cleanup
kubectl delete pod test-pod
kubectl delete job kube-bench
```

- [ ] **Task 1: Deploy or select the lab cluster.** Use the kind configuration when you want fast rebuilds, or use a kubeadm cluster when you want static pod and node-path realism.

<details>
<summary>Solution guidance</summary>

Confirm `kubectl get nodes` returns at least one Ready node before installing security tools. If you use kind, inspect the local audit log directory after creating a small pod. If you use kubeadm, verify the API server static pod remains healthy after adding audit flags and volumes.
</details>

- [ ] **Task 2: Configure audit logging and prove it records a pod action.** Create a pod, delete it, and locate the corresponding audit event through the configured log path.

<details>
<summary>Solution guidance</summary>

For kind, check the host-mounted `audit-logs` directory. For kubeadm, check the configured control-plane log path. If no event appears, inspect the API server flags, the policy rules, and whether the action happened after the API server reloaded the configuration.
</details>

- [ ] **Task 3: Install and validate Trivy, Falco, kube-bench, and kubesec.** Record one successful command or status check from each tool so you can tell installation failure from security findings.

<details>
<summary>Solution guidance</summary>

Use `trivy --version`, `kubectl get pods -n falco`, kube-bench job logs or a direct node run, and a small kubesec scan. If Falco fails, classify the error as chart configuration, namespace setup, or driver compatibility before changing values.
</details>

- [ ] **Task 4: Deploy the isolated vulnerable practice targets.** Keep them in `insecure-apps`, scan them, and identify which tool reports which kind of problem.

<details>
<summary>Solution guidance</summary>

The privileged pod should teach manifest hardening, the root pod should teach identity settings, the unlimited pod should teach resource governance, and the vulnerable image should teach scanner triage. Do not expose these workloads outside the lab.
</details>

- [ ] **Task 5: Evaluate lab findings and choose one remediation path.** Pick one finding, explain whether it came from image scanning, runtime detection, benchmark comparison, or static analysis, then apply or describe the narrow fix.

<details>
<summary>Solution guidance</summary>

A strong answer names the evidence source and the layer it belongs to. Examples include changing a risky pod security context after kubesec output, filtering Trivy findings before changing an image, or adjusting Falco driver settings after reading runtime logs. Clean up the test pod, kube-bench job, and vulnerable namespace when the drill is complete.
</details>

Success criteria:

- [ ] The cluster is reachable with `kubectl get nodes`.
- [ ] Audit logging is configured and produces an event for a pod create or delete action.
- [ ] Trivy scans an image and you can explain at least one high-severity finding or why it is not actionable.
- [ ] Falco is either running successfully or you have documented the driver reason it is not running in this lab.
- [ ] kube-bench produces output through a job or direct node run.
- [ ] kubesec scans a manifest and flags a risky security context.
- [ ] The `insecure-apps` namespace is deleted or the disposable cluster is rebuilt after practice.

---

## Learner check

> Host-mounted audit log (kind maps /var/log/kubernetes inside the node to ./audit-logs)

Before you move on, explain why `grep audit-logs/audit.log` on your workstation can show pod create events even though the API server process runs inside the kind control-plane container. A solid answer connects the API server `--audit-log-path` flag, the in-node `/var/log/kubernetes` directory, and the kind `extraMounts` mapping that exposes that directory as `./audit-logs` on the host.

---

## Sources

- [Kubernetes audit logging](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [Kubernetes seccomp tutorial](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [Kubernetes AppArmor tutorial](https://kubernetes.io/docs/tutorials/security/apparmor/)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes admission controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [kind configuration docs](https://kind.sigs.k8s.io/docs/user/configuration/)
- [Trivy documentation](https://aquasecurity.github.io/trivy/latest/)
- [Trivy Kubernetes scanning](https://aquasecurity.github.io/trivy/latest/docs/target/kubernetes/)
- [Trivy Debian repository key](https://aquasecurity.github.io/trivy-repo/deb/public.key)
- [Trivy Debian repository](https://aquasecurity.github.io/trivy-repo/deb)
- [Falco documentation](https://falco.org/docs/)
- [Falco Kubernetes setup](https://falco.org/docs/setup/kubernetes/)
- [Falco Helm charts](https://falcosecurity.github.io/charts)
- [kube-bench repository](https://github.com/aquasecurity/kube-bench)
- [kube-bench Kubernetes Job manifest](https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml)
- [kube-bench v0.15.5 release archive](https://github.com/aquasecurity/kube-bench/releases/download/v0.15.5/kube-bench_0.15.5_linux_amd64.tar.gz)
- [Sysdig Falco release announcement (May 2016)](https://sysdig.com/blog/sysdig-falco)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [kubesec repository](https://github.com/controlplaneio/kubesec)
- [kubesec v2.14.0 release archive](https://github.com/controlplaneio/kubesec/releases/download/v2.14.0/kubesec_linux_amd64.tar.gz)
- [KubeDojo CKS lab scenario](https://killercoda.com/kubedojo/scenario/cks-0.2-security-lab)

## Next Module

[Module 0.3: Security Tool Mastery](../module-0.3-security-tools/) - Deep dive into Trivy, Falco, and kube-bench usage.
