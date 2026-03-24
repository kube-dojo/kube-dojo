# Part 1 Cumulative Quiz: Cluster Architecture

> **Purpose**: Test your retention across all Part 1 modules before moving to Part 2.
>
> **Target Score**: 80% (20/25) to proceed confidently
>
> **Time Limit**: 20 minutes

---

## Instructions

Answer all 25 questions without referring to the modules. This quiz covers 25% of the CKA exam content.

---

## Questions

### Control Plane (Module 1.1)

1. **Which component stores all cluster state?**
   <details>
   <summary>Answer</summary>
   etcd - the distributed key-value store
   </details>

2. **What component decides which node a pod runs on?**
   <details>
   <summary>Answer</summary>
   kube-scheduler
   </details>

3. **Which component creates pods when you create a Deployment?**
   <details>
   <summary>Answer</summary>
   kube-controller-manager (specifically the Deployment controller and ReplicaSet controller)
   </details>

4. **What command checks API server health?**
   <details>
   <summary>Answer</summary>
   `kubectl get --raw='/readyz'` or `kubectl get --raw='/healthz'`
   </details>

### Extension Interfaces (Module 1.2)

5. **What interface does Calico implement?**
   <details>
   <summary>Answer</summary>
   CNI (Container Network Interface)
   </details>

6. **What interface does containerd implement?**
   <details>
   <summary>Answer</summary>
   CRI (Container Runtime Interface)
   </details>

7. **What command lists containers using CRI?**
   <details>
   <summary>Answer</summary>
   `crictl ps` (or `sudo crictl ps`)
   </details>

8. **Where are CNI configurations typically stored?**
   <details>
   <summary>Answer</summary>
   `/etc/cni/net.d/`
   </details>

### Helm (Module 1.3)

9. **What command installs a chart with custom values?**
   <details>
   <summary>Answer</summary>
   `helm install <release> <chart> -f values.yaml` or `--set key=value`
   </details>

10. **How do you upgrade a release while keeping existing values?**
    <details>
    <summary>Answer</summary>
    `helm upgrade <release> <chart> --reuse-values`
    </details>

11. **What command rolls back to a previous release revision?**
    <details>
    <summary>Answer</summary>
    `helm rollback <release> <revision>`
    </details>

12. **How do you see all configurable values for a chart?**
    <details>
    <summary>Answer</summary>
    `helm show values <chart>`
    </details>

### Kustomize (Module 1.4)

13. **What command previews Kustomize output without applying?**
    <details>
    <summary>Answer</summary>
    `kubectl kustomize <directory>` or `kustomize build <directory>`
    </details>

14. **What flag applies Kustomize directly with kubectl?**
    <details>
    <summary>Answer</summary>
    `-k` (e.g., `kubectl apply -k ./overlay/`)
    </details>

15. **In Kustomize, what's the difference between base and overlay?**
    <details>
    <summary>Answer</summary>
    Base contains original resources; overlay contains environment-specific modifications that reference the base
    </details>

### CRDs & Operators (Module 1.5)

16. **What command lists all Custom Resource Definitions?**
    <details>
    <summary>Answer</summary>
    `kubectl get crd`
    </details>

17. **What must be created before you can create custom resource instances?**
    <details>
    <summary>Answer</summary>
    The CRD (CustomResourceDefinition) must exist first
    </details>

18. **What's the difference between a CRD and a CR?**
    <details>
    <summary>Answer</summary>
    CRD defines the schema/structure; CR (Custom Resource) is an instance of that type
    </details>

### RBAC (Module 1.6)

19. **What's the difference between Role and ClusterRole?**
    <details>
    <summary>Answer</summary>
    Role is namespaced; ClusterRole is cluster-wide
    </details>

20. **What command tests if a user can perform an action?**
    <details>
    <summary>Answer</summary>
    `kubectl auth can-i <verb> <resource> --as=<user>`
    </details>

21. **How do you grant a ServiceAccount permissions in a namespace?**
    <details>
    <summary>Answer</summary>
    Create a Role and RoleBinding that references the ServiceAccount
    </details>

22. **What are the three subject types in RBAC bindings?**
    <details>
    <summary>Answer</summary>
    User, Group, ServiceAccount
    </details>

### kubeadm (Module 1.7)

23. **What command prevents new pods from being scheduled on a node?**
    <details>
    <summary>Answer</summary>
    `kubectl cordon <node>`
    </details>

24. **What's the difference between cordon and drain?**
    <details>
    <summary>Answer</summary>
    Cordon only prevents new pods; drain also evicts existing pods
    </details>

25. **What command generates a new join token for worker nodes?**
    <details>
    <summary>Answer</summary>
    `kubeadm token create --print-join-command`
    </details>

---

## Scoring

Count your correct answers:

| Score | Assessment | Action |
|-------|------------|--------|
| 23-25 | Excellent | Ready for Part 2 |
| 20-22 | Good | Review missed topics, then proceed |
| 16-19 | Fair | Re-read relevant modules, repeat quiz |
| <16 | Needs work | Complete all module exercises again |

---

## Weak Area Review

If you missed questions, review these specific sections:

- Q1-4: Module 1.1 - Control Plane
- Q5-8: Module 1.2 - Extension Interfaces
- Q9-12: Module 1.3 - Helm
- Q13-15: Module 1.4 - Kustomize
- Q16-18: Module 1.5 - CRDs & Operators
- Q19-22: Module 1.6 - RBAC
- Q23-25: Module 1.7 - kubeadm

---

## Practical Assessment

Before proceeding, ensure you can do these without help:

- [ ] Create a complete RBAC setup (SA, Role, RoleBinding) in under 3 minutes
- [ ] Install, upgrade, and rollback a Helm release
- [ ] Create a Kustomize overlay with namespace and patches
- [ ] Create a simple CRD and custom resource
- [ ] Cordon, drain, and uncordon a node
- [ ] Generate YAML for any resource using `kubectl ... $do`

---

## Next Steps

When you score 20/25 or higher and complete the practical assessment:

→ Continue to [Part 2: Workloads & Scheduling](../part2-workloads-scheduling/README.md)

This covers 15% of the exam and builds directly on cluster architecture concepts.
