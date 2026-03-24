# Part 2 Cumulative Quiz: Workloads & Scheduling

> **Purpose**: Test your retention across all Part 2 modules before moving to Part 3.
>
> **Target Score**: 80% (22/28) to proceed confidently
>
> **Time Limit**: 20 minutes

---

## Instructions

Answer all 28 questions without referring to the modules. This quiz covers 15% of the CKA exam content.

---

## Questions

### Pods Deep-Dive (Module 2.1)

1. **What's the fastest way to create a Pod YAML template without applying it?**
   <details>
   <summary>Answer</summary>
   `kubectl run <name> --image=<image> --dry-run=client -o yaml`
   </details>

2. **What container type runs to completion before main containers start?**
   <details>
   <summary>Answer</summary>
   Init containers
   </details>

3. **What probe type determines if a container should receive traffic?**
   <details>
   <summary>Answer</summary>
   Readiness probe
   </details>

4. **How do containers in the same Pod communicate?**
   <details>
   <summary>Answer</summary>
   Via localhost (they share the same network namespace)
   </details>

### Deployments & ReplicaSets (Module 2.2)

5. **What command creates a Deployment with 3 replicas?**
   <details>
   <summary>Answer</summary>
   `kubectl create deployment <name> --image=<image> --replicas=3`
   </details>

6. **What command updates a Deployment's image?**
   <details>
   <summary>Answer</summary>
   `kubectl set image deployment/<name> <container>=<new-image>`
   </details>

7. **What command shows rollout history for a Deployment?**
   <details>
   <summary>Answer</summary>
   `kubectl rollout history deployment/<name>`
   </details>

8. **What's the default rolling update strategy parameter maxUnavailable?**
   <details>
   <summary>Answer</summary>
   25%
   </details>

### DaemonSets & StatefulSets (Module 2.3)

9. **What workload type ensures one Pod per node?**
   <details>
   <summary>Answer</summary>
   DaemonSet
   </details>

10. **What type of Service is required for StatefulSets?**
    <details>
    <summary>Answer</summary>
    Headless Service (clusterIP: None)
    </details>

11. **In a StatefulSet named "web" with 3 replicas, what is the hostname of the first Pod?**
    <details>
    <summary>Answer</summary>
    web-0
    </details>

12. **What StatefulSet field creates per-Pod PVCs?**
    <details>
    <summary>Answer</summary>
    volumeClaimTemplates
    </details>

### Jobs & CronJobs (Module 2.4)

13. **What field makes a Job run 5 tasks in parallel?**
    <details>
    <summary>Answer</summary>
    `parallelism: 5`
    </details>

14. **What CronJob schedule means "every day at midnight"?**
    <details>
    <summary>Answer</summary>
    `0 0 * * *`
    </details>

15. **What Job field controls how many times a failed Pod is retried?**
    <details>
    <summary>Answer</summary>
    `backoffLimit`
    </details>

16. **What restartPolicy must be used for Job Pods?**
    <details>
    <summary>Answer</summary>
    `Never` or `OnFailure` (not `Always`)
    </details>

### Resource Management (Module 2.5)

17. **What's the difference between resource requests and limits?**
    <details>
    <summary>Answer</summary>
    Requests: guaranteed minimum (used for scheduling). Limits: maximum allowed (enforced at runtime).
    </details>

18. **What QoS class does a Pod get when requests equal limits for all containers?**
    <details>
    <summary>Answer</summary>
    Guaranteed
    </details>

19. **What resource sets namespace-wide quotas for CPU/memory?**
    <details>
    <summary>Answer</summary>
    ResourceQuota
    </details>

20. **What happens when a container exceeds its memory limit?**
    <details>
    <summary>Answer</summary>
    The container is OOMKilled (terminated)
    </details>

### Scheduling (Module 2.6)

21. **What Pod field assigns a Pod to a node with a specific label?**
    <details>
    <summary>Answer</summary>
    `nodeSelector`
    </details>

22. **What command adds a taint to a node?**
    <details>
    <summary>Answer</summary>
    `kubectl taint nodes <node> key=value:effect` (e.g., `kubectl taint nodes node1 dedicated=gpu:NoSchedule`)
    </details>

23. **What tolerations effect allows scheduling but prefers other nodes?**
    <details>
    <summary>Answer</summary>
    `PreferNoSchedule`
    </details>

24. **What's the difference between requiredDuringScheduling and preferredDuringScheduling?**
    <details>
    <summary>Answer</summary>
    Required: hard constraint (Pod won't schedule if unmet). Preferred: soft constraint (scheduler tries but will schedule elsewhere if needed).
    </details>

### ConfigMaps & Secrets (Module 2.7)

25. **What command creates a ConfigMap from literal values?**
    <details>
    <summary>Answer</summary>
    `kubectl create configmap <name> --from-literal=key=value`
    </details>

26. **What happens to environment variables when you update a ConfigMap?**
    <details>
    <summary>Answer</summary>
    They don't update - the Pod must be restarted
    </details>

27. **How do you decode a base64-encoded Secret value?**
    <details>
    <summary>Answer</summary>
    `kubectl get secret <name> -o jsonpath='{.data.<key>}' | base64 -d`
    </details>

28. **What's wrong with `echo 'password' | base64` for creating Secrets?**
    <details>
    <summary>Answer</summary>
    It includes a newline character. Use `echo -n 'password' | base64` instead.
    </details>

---

## Scoring

Count your correct answers:

| Score | Assessment | Action |
|-------|------------|--------|
| 25-28 | Excellent | Ready for Part 3 |
| 20-24 | Good | Review missed topics, then proceed |
| 15-19 | Fair | Re-read relevant modules, repeat quiz |
| <15 | Needs work | Complete all module exercises again |

---

## Weak Area Review

If you missed questions, review these specific sections:

- Q1-4: Module 2.1 - Pods Deep-Dive
- Q5-8: Module 2.2 - Deployments & ReplicaSets
- Q9-12: Module 2.3 - DaemonSets & StatefulSets
- Q13-16: Module 2.4 - Jobs & CronJobs
- Q17-20: Module 2.5 - Resource Management
- Q21-24: Module 2.6 - Scheduling
- Q25-28: Module 2.7 - ConfigMaps & Secrets

---

## Practical Assessment

Before proceeding, ensure you can do these without help:

- [ ] Create a multi-container Pod with shared volume in under 3 minutes
- [ ] Deploy and scale a Deployment, then rollback to a previous revision
- [ ] Create a Job that runs 5 parallel tasks with 10 total completions
- [ ] Configure a Pod with resource requests, limits, and a readiness probe
- [ ] Schedule a Pod to a specific node using nodeSelector
- [ ] Taint a node and create a Pod with matching toleration
- [ ] Create ConfigMaps and Secrets, inject both as env vars and volume mounts
- [ ] Decode a Secret value from the command line

---

## Speed Drill Challenge

Time yourself on these common exam tasks:

| Task | Target Time |
|------|-------------|
| Create Pod with specific image | 15 seconds |
| Create Deployment with 3 replicas | 20 seconds |
| Update Deployment image | 15 seconds |
| Create ConfigMap from literals | 20 seconds |
| Create Secret and mount in Pod | 90 seconds |
| Add resource limits to existing Pod | 60 seconds |
| Create CronJob that runs hourly | 45 seconds |

If you can't meet these times, practice the drill sections in each module.

---

## Next Steps

When you score 20/28 or higher and complete the practical assessment:

→ Continue to [Part 3: Services & Networking](../part3-services-networking/README.md)

This covers 20% of the exam and teaches how Pods communicate within and outside the cluster.

---

## Part 2 Quick Reference

### Essential Commands

```bash
# Pods
k run <name> --image=<img> $do           # Generate Pod YAML
k run <name> --image=<img> --restart=Never # Create Job-like Pod

# Deployments
k create deploy <name> --image=<img> --replicas=N
k set image deploy/<name> <container>=<new-image>
k rollout status/history/undo deploy/<name>
k scale deploy/<name> --replicas=N

# Jobs
k create job <name> --image=<img> -- <command>
k create cronjob <name> --image=<img> --schedule="*/5 * * * *" -- <cmd>

# Config
k create configmap <name> --from-literal=k=v --from-file=path
k create secret generic <name> --from-literal=k=v
k get secret <name> -o jsonpath='{.data.<key>}' | base64 -d

# Scheduling
k taint nodes <node> key=value:NoSchedule
k taint nodes <node> key=value:NoSchedule-  # Remove taint
k label nodes <node> key=value
```

### Key YAML Patterns

```yaml
# Resource Management
resources:
  requests:
    memory: "128Mi"
    cpu: "250m"
  limits:
    memory: "256Mi"
    cpu: "500m"

# Probes
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

# Node Selection
nodeSelector:
  disk: ssd

# Tolerations
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "gpu"
  effect: "NoSchedule"

# ConfigMap as env
envFrom:
- configMapRef:
    name: app-config

# Secret as volume
volumes:
- name: secret-vol
  secret:
    secretName: app-secret
```
