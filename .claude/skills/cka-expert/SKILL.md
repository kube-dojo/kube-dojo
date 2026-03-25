---
name: cka-expert
description: CKA 2025 exam knowledge. Use for Kubernetes certification questions, exam strategy, curriculum accuracy. Triggers on "CKA", "exam", "certification", "kubernetes admin".
---

# CKA Expert Skill

Authoritative knowledge source for CKA (Certified Kubernetes Administrator) exam preparation. Provides accurate, up-to-date information aligned with the CKA 2025 curriculum.

## When to Use
- Writing or reviewing CKA curriculum content
- Answering questions about CKA exam topics
- Verifying technical accuracy of Kubernetes content
- Providing exam-specific tips and strategies

## CKA 2025 Curriculum

### Exam Format
- **Duration**: 2 hours (120 minutes)
- **Questions**: 16 performance-based tasks
- **Passing Score**: 66%
- **Environment**: Ubuntu-based, kubeadm clusters
- **Resources Allowed**: kubernetes.io, helm.sh, github.com/kubernetes

### Domain Weights

| Domain | Weight | ~Questions |
|--------|--------|------------|
| Troubleshooting | 30% | 5 |
| Cluster Architecture, Installation & Configuration | 25% | 4 |
| Services & Networking | 20% | 3-4 |
| Workloads & Scheduling | 15% | 2-3 |
| Storage | 10% | 1-2 |

### 2025 Curriculum Changes

#### Added Topics (MUST COVER)
- **Helm**: Package management, charts, releases, values
- **Kustomize**: Configuration management, overlays, patches
- **Gateway API**: HTTPRoute, Gateway, GatewayClass (replacing Ingress focus)
- **CRDs & Operators**: Custom Resource Definitions, extending the API
- **Pod Security Admission**: Security contexts, PSA modes

#### Removed/Deprioritized
- etcd backup/restore (mention but don't emphasize)
- Cluster version upgrades (deprioritized)
- Infrastructure provisioning (removed)

### Key Technical Knowledge

#### Cluster Architecture
- Control plane components: API server, etcd, scheduler, controller-manager
- Node components: kubelet, kube-proxy, container runtime (containerd)
- Extension interfaces: CNI, CSI, CRI

#### Workloads
- Pod lifecycle and states
- Deployments, ReplicaSets, DaemonSets, StatefulSets
- Jobs, CronJobs
- Resource requests and limits, QoS classes

#### Scheduling
- nodeSelector, node affinity/anti-affinity
- Taints and tolerations
- Pod topology spread constraints
- Priority and preemption

#### Networking
- Service types: ClusterIP, NodePort, LoadBalancer, ExternalName
- DNS: CoreDNS configuration and troubleshooting
- NetworkPolicies: ingress, egress rules
- Gateway API: Gateway, GatewayClass, HTTPRoute
- Ingress (legacy but still relevant)

#### Storage
- Volumes: emptyDir, hostPath, configMap, secret
- PersistentVolumes, PersistentVolumeClaims
- StorageClasses, dynamic provisioning
- Access modes: RWO, ROX, RWX, RWOP
- Reclaim policies: Retain, Delete

#### Security
- RBAC: Roles, ClusterRoles, RoleBindings, ClusterRoleBindings
- ServiceAccounts
- Pod Security Admission
- Security contexts

### Exam Strategy: Three-Pass Method

1. **Pass 1 - Quick Wins** (1-3 min tasks)
   - Create pods, deployments, services
   - Add labels, scale replicas
   - Simple kubectl commands

2. **Pass 2 - Medium Tasks** (4-6 min)
   - RBAC setup
   - NetworkPolicies
   - PVC configuration
   - Helm operations

3. **Pass 3 - Complex Tasks** (remaining time)
   - Troubleshooting scenarios
   - Multi-step problems
   - Cluster-level issues

### Critical Exam Tips

1. **Always switch context first** - Every question specifies a cluster
2. **Use imperative commands** - Faster than writing YAML
3. **Generate YAML templates** - `kubectl ... --dry-run=client -o yaml`
4. **Know kubectl explain** - Faster than searching docs
5. **Partial credit exists** - Attempt everything
6. **Good enough > perfect** - Don't over-engineer

### Common Exam Mistakes

| Mistake | Impact | Prevention |
|---------|--------|------------|
| Wrong cluster context | 0 points | Always `kubectl config use-context` first |
| Perfectionism | Time loss | "Good enough" mindset |
| Linear approach | Miss easy points | Three-pass method |
| Not verifying | Silent failures | Always check your work |
| Memorizing YAML | Unnecessary | Use docs and `--dry-run` |

## Official Resources

- [CNCF Curriculum](https://github.com/cncf/curriculum)
- [CKA Program Changes](https://training.linuxfoundation.org/certified-kubernetes-administrator-cka-program-changes/)
- [kubernetes.io/docs](https://kubernetes.io/docs/)
- [helm.sh/docs](https://helm.sh/docs/)
