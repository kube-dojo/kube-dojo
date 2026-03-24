# Part 5: Troubleshooting - Cumulative Quiz

> **30% of CKA Exam** | 35 Questions | Target: 85%+

This quiz covers all troubleshooting topics from Part 5. Test yourself before moving to mock exams.

---

## Instructions

1. Answer each question before revealing the solution
2. Track your score: ___/35
3. Review any topics where you score below 80%
4. Retake after reviewing weak areas

---

## Section 1: Troubleshooting Methodology (5 questions)

### Q1: First Steps
A user reports "the application isn't working." What's your first troubleshooting action?

<details>
<summary>Answer</summary>

**Identify the symptom specifically.** Ask clarifying questions:
- Is the pod running? (`k get pods`)
- Is the service accessible? (`k get svc, endpoints`)
- What error are they seeing?

Then follow the framework: Identify → Isolate → Diagnose → Fix

</details>

### Q2: Describe vs Logs
Why should you check `kubectl describe pod` before `kubectl logs`?

<details>
<summary>Answer</summary>

The **Events section** in describe often reveals the problem immediately without needing logs:
- Scheduling failures
- Image pull errors
- Volume mount issues
- Configuration errors

Logs are useful for application-level issues, but many problems are caught at the Kubernetes level first.

</details>

### Q3: Event Retention
You're investigating an issue that happened 3 hours ago. Events show nothing. Why?

<details>
<summary>Answer</summary>

**Events expire after 1 hour** by default. The evidence is gone. This is why it's important to:
- Check events immediately after incidents
- Have a log aggregation solution for historical data
- Note event messages when you see them

</details>

### Q4: Exit Codes
Container exit code is 137. What does this indicate?

<details>
<summary>Answer</summary>

Exit code 137 = 128 + 9 (SIGKILL). Usually means:
- **OOMKilled** - Container exceeded memory limit
- Process was killed by the system

Check: `k describe pod | grep -i oom` and verify memory limits.

</details>

### Q5: Troubleshooting Order
List the correct troubleshooting order for a pod stuck in Pending:

<details>
<summary>Answer</summary>

1. `k describe pod <pod>` - Check Events section for scheduling messages
2. Check node availability: `k get nodes`
3. Check node resources: `k describe nodes | grep -A 5 "Allocated resources"`
4. Check taints: `k get nodes -o custom-columns='NAME:.metadata.name,TAINTS:.spec.taints[*].key'`
5. Check pod's nodeSelector/affinity: `k get pod <pod> -o yaml`

</details>

---

## Section 2: Application Failures (6 questions)

### Q6: CrashLoopBackOff
Pod is in CrashLoopBackOff. What's the maximum backoff time between restarts?

<details>
<summary>Answer</summary>

**5 minutes (300 seconds)**

Backoff doubles: 10s → 20s → 40s → 80s → 160s → 300s (max)

After 10 minutes of running successfully, the counter resets.

</details>

### Q7: Image Pull Failure
Pod shows ImagePullBackOff. List 3 possible causes.

<details>
<summary>Answer</summary>

1. **Image doesn't exist** - Wrong name or tag
2. **Registry authentication failed** - Missing or wrong imagePullSecrets
3. **Registry unreachable** - Network issues or firewall
4. **Rate limited** - Docker Hub pull limits exceeded
5. **Private registry not configured** - Missing registry credentials

</details>

### Q8: Missing ConfigMap
Pod is stuck in ContainerCreating. Events show "configmap 'app-config' not found". Fix it.

<details>
<summary>Answer</summary>

```bash
# Create the missing ConfigMap
k create configmap app-config --from-literal=key=value

# Or if you have the data
k create configmap app-config --from-file=config.yaml

# Verify pod starts
k get pods -w
```

</details>

### Q9: Previous Logs
How do you view logs from a container that has crashed?

<details>
<summary>Answer</summary>

```bash
k logs <pod> --previous

# For multi-container pod
k logs <pod> -c <container> --previous
```

This shows logs from the previous container instance before it died.

</details>

### Q10: Deployment Rollback
Deployment rollout is stuck with new pods failing. What's the fastest fix?

<details>
<summary>Answer</summary>

```bash
k rollout undo deployment/<name>
```

This immediately rolls back to the previous working version. Investigate the issue later.

</details>

### Q11: OOMKilled
Pod keeps getting OOMKilled. How do you verify and fix?

<details>
<summary>Answer</summary>

```bash
# Verify
k describe pod <pod> | grep -i oom
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'

# Check current limit
k get pod <pod> -o jsonpath='{.spec.containers[0].resources.limits.memory}'

# Fix by increasing limit
k patch deployment <name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

</details>

---

## Section 3: Control Plane Failures (5 questions)

### Q12: Static Pod Location
Where are control plane static pod manifests stored in kubeadm clusters?

<details>
<summary>Answer</summary>

```
/etc/kubernetes/manifests/
```

Contains:
- kube-apiserver.yaml
- kube-scheduler.yaml
- kube-controller-manager.yaml
- etcd.yaml

</details>

### Q13: API Server Down
kubectl commands are timing out. You SSH to the control plane. What do you check first?

<details>
<summary>Answer</summary>

```bash
# Check if API server container is running
crictl ps | grep kube-apiserver

# If not running
crictl ps -a | grep kube-apiserver  # See if it exists
journalctl -u kubelet | grep apiserver  # Check kubelet logs

# Check manifest
cat /etc/kubernetes/manifests/kube-apiserver.yaml
```

</details>

### Q14: Scheduler vs Controller Manager
New pods stay Pending but Deployments show correct replica count. Which component is failing?

<details>
<summary>Answer</summary>

**Scheduler**

- Controller manager creates ReplicaSets (working - correct replica count)
- Scheduler assigns pods to nodes (failing - pods stuck Pending)

</details>

### Q15: etcd Health
Write the command to check etcd cluster health.

<details>
<summary>Answer</summary>

```bash
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

</details>

### Q16: Certificate Expiry
How do you check if Kubernetes certificates are expired?

<details>
<summary>Answer</summary>

```bash
kubeadm certs check-expiration
```

To renew:
```bash
kubeadm certs renew all
```

</details>

---

## Section 4: Worker Node Failures (5 questions)

### Q17: Node NotReady
A node shows NotReady status. What's your SSH troubleshooting sequence?

<details>
<summary>Answer</summary>

```bash
ssh <node>

# 1. Check kubelet
sudo systemctl status kubelet
sudo journalctl -u kubelet -n 50

# 2. Check container runtime
sudo systemctl status containerd
sudo crictl ps

# 3. Check network to API server
curl -k https://<api-server>:6443/healthz

# 4. Check disk space
df -h
```

</details>

### Q18: kubelet Not Running
How do you start kubelet and ensure it starts on boot?

<details>
<summary>Answer</summary>

```bash
sudo systemctl start kubelet
sudo systemctl enable kubelet
sudo systemctl status kubelet
```

</details>

### Q19: crictl vs kubectl
When do you use crictl instead of kubectl?

<details>
<summary>Answer</summary>

Use **crictl** when:
- kubelet or API server is down
- kubectl won't work
- Debugging at container runtime level
- Node is NotReady

crictl talks directly to containerd, bypassing Kubernetes API.

</details>

### Q20: Node Drain
What's the command to safely drain a node for maintenance?

<details>
<summary>Answer</summary>

```bash
k drain <node> --ignore-daemonsets --delete-emptydir-data
```

After maintenance:
```bash
k uncordon <node>
```

</details>

### Q21: MemoryPressure
Node shows MemoryPressure=True. What are the effects?

<details>
<summary>Answer</summary>

1. **No new pods scheduled** to this node
2. **Existing pods may be evicted** (starting with BestEffort, then Burstable)
3. Node marked as having pressure in conditions

Fix: Free memory by evicting pods, killing processes, or adding capacity.

</details>

---

## Section 5: Network Troubleshooting (6 questions)

### Q22: DNS Resolution Test
How do you test DNS resolution from inside a pod?

<details>
<summary>Answer</summary>

```bash
# Test cluster DNS
k exec <pod> -- nslookup kubernetes

# Test service DNS
k exec <pod> -- nslookup <service-name>

# Test external DNS
k exec <pod> -- nslookup google.com

# Check DNS config
k exec <pod> -- cat /etc/resolv.conf
```

</details>

### Q23: CoreDNS Troubleshooting
All DNS queries fail. What do you check?

<details>
<summary>Answer</summary>

```bash
# Check CoreDNS pods
k -n kube-system get pods -l k8s-app=kube-dns

# Check CoreDNS logs
k -n kube-system logs -l k8s-app=kube-dns

# Check kube-dns service
k -n kube-system get svc kube-dns
k -n kube-system get endpoints kube-dns
```

</details>

### Q24: Empty Endpoints
Service exists but `k get endpoints <svc>` shows `<none>`. Cause?

<details>
<summary>Answer</summary>

**Selector mismatch** - service selector doesn't match any pod labels, or matching pods aren't Ready.

```bash
# Check selector
k get svc <svc> -o jsonpath='{.spec.selector}'

# Find matching pods
k get pods -l <selector>

# Check if pods are Ready
k get pods -l <selector> -o wide
```

</details>

### Q25: Cross-Node Communication
Pods on the same node communicate, but cross-node fails. What's likely broken?

<details>
<summary>Answer</summary>

**CNI plugin's cross-node networking** is not working:
- CNI pods not running on all nodes
- Network connectivity between nodes blocked
- Overlay network (VXLAN/IPinIP) misconfigured
- MTU mismatch

```bash
k -n kube-system get pods -o wide | grep <cni-name>
```

</details>

### Q26: NetworkPolicy Default
You create a NetworkPolicy selecting pods with only ingress rules. What happens to egress?

<details>
<summary>Answer</summary>

It depends on `policyTypes`:
- If `policyTypes: [Ingress]` only → Egress **unrestricted**
- If `policyTypes: [Ingress, Egress]` with no egress rules → All egress **denied**

NetworkPolicies only affect traffic types listed in policyTypes.

</details>

### Q27: CNI Troubleshooting
Pods stuck in ContainerCreating with "network not ready". What do you check?

<details>
<summary>Answer</summary>

```bash
# Check CNI pods
k -n kube-system get pods | grep -E "calico|flannel|weave|cilium"

# Check CNI configuration on node
ls /etc/cni/net.d/

# Check CNI binaries
ls /opt/cni/bin/

# Check CNI pod logs
k -n kube-system logs <cni-pod>
```

</details>

---

## Section 6: Service Troubleshooting (4 questions)

### Q28: Port vs TargetPort
Service has `port: 80, targetPort: 8080`. Container listens on 80. Will it work?

<details>
<summary>Answer</summary>

**No.** Traffic arrives at service port 80 but is forwarded to pod port 8080, where nothing is listening.

Fix: Change `targetPort: 80` or make container listen on 8080.

</details>

### Q29: NodePort Not Working
NodePort works from inside cluster but not externally. What's wrong?

<details>
<summary>Answer</summary>

**Firewall or security group** blocking the port externally:
- Node iptables
- Cloud security groups
- Network ACLs

NodePort must be open on all nodes from external network.

</details>

### Q30: LoadBalancer Pending
LoadBalancer service stays `<pending>` for EXTERNAL-IP. Why?

<details>
<summary>Answer</summary>

No cloud controller or MetalLB:
- Cloud controller manager not installed
- Wrong cloud credentials
- No LoadBalancer support (bare metal without MetalLB)

```bash
k -n kube-system get pods | grep cloud-controller
k get events --field-selector involvedObject.name=<svc>
```

</details>

### Q31: kube-proxy
All services stop working on a node. What's likely the issue?

<details>
<summary>Answer</summary>

**kube-proxy** not running or misconfigured on that node:

```bash
k -n kube-system get pods -l k8s-app=kube-proxy -o wide
k -n kube-system logs -l k8s-app=kube-proxy

# Check iptables rules
sudo iptables -t nat -L KUBE-SERVICES | head
```

</details>

---

## Section 7: Logging & Monitoring (4 questions)

### Q32: Previous Container Logs
When do you use `--previous` flag with kubectl logs?

<details>
<summary>Answer</summary>

When container has **crashed and restarted** (CrashLoopBackOff). Shows logs from the previous instance before it died.

```bash
k logs <pod> --previous
```

</details>

### Q33: Metrics Server
`kubectl top pods` returns "metrics not available". How do you fix it?

<details>
<summary>Answer</summary>

**Install Metrics Server**:

```bash
# Check if installed
k -n kube-system get pods | grep metrics-server

# If not, install it
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

</details>

### Q34: Log Locations
Where are container logs stored on a node?

<details>
<summary>Answer</summary>

```
/var/log/containers/<pod>_<namespace>_<container>-<id>.log
```

These are symlinks managed by the container runtime. kubelet handles log rotation.

</details>

### Q35: kubelet Logs
How do you view kubelet logs on a node?

<details>
<summary>Answer</summary>

```bash
# SSH to node
ssh <node>

# View logs
journalctl -u kubelet

# Follow logs
journalctl -u kubelet -f

# Recent errors
journalctl -u kubelet --since "10 minutes ago" | grep -i error
```

</details>

---

## Scoring

| Score | Assessment |
|-------|------------|
| 32-35 (90%+) | Excellent - Ready for troubleshooting questions |
| 28-31 (80-89%) | Good - Review missed topics |
| 24-27 (70-79%) | Fair - Need more practice |
| <24 (<70%) | Review Part 5 modules thoroughly |

**Your Score: ___/35 = ___%**

---

## Topic Review Guide

If you scored low on specific sections:

| Section | Review Module |
|---------|---------------|
| Methodology | 5.1 |
| Application Failures | 5.2 |
| Control Plane | 5.3 |
| Worker Nodes | 5.4 |
| Network | 5.5 |
| Services | 5.6 |
| Logging | 5.7 |

---

## Next Steps

With Part 5 complete, you've covered:
- Part 0: Environment (5 modules)
- Part 1: Cluster Architecture (7 modules) - 25% of exam
- Part 2: Workloads & Scheduling (7 modules) - 15% of exam
- Part 3: Services & Networking (7 modules) - 20% of exam
- Part 4: Storage (5 modules) - 10% of exam
- Part 5: Troubleshooting (7 modules) - 30% of exam

**Total: 38 modules covering 100% of CKA exam domains**

Continue to [Part 6: Mock Exams](../part6-mock-exams/README.md) for timed practice under exam conditions.
