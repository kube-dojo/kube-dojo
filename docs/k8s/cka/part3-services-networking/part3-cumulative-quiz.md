# Part 3 Cumulative Quiz: Services & Networking

> **Time Limit**: 45 minutes
>
> **Passing Score**: 80% (24/30 questions)
>
> **Format**: Multiple choice and short answer

This quiz covers all modules from Part 3:
- Module 3.1: Services
- Module 3.2: Endpoints & EndpointSlices
- Module 3.3: DNS & CoreDNS
- Module 3.4: Ingress
- Module 3.5: Gateway API
- Module 3.6: Network Policies
- Module 3.7: CNI & Cluster Networking

---

## Section 1: Services (7 questions)

### Q1: Service Types
What service type would you use to expose an application externally with automatic cloud load balancer provisioning?

<details>
<summary>Answer</summary>

**LoadBalancer**

LoadBalancer service type provisions an external load balancer (on supported cloud providers) that routes traffic to NodePorts on cluster nodes.

</details>

### Q2: Port Configuration
A service has `port: 80` and `targetPort: 8080`. What does this mean?

<details>
<summary>Answer</summary>

The service listens on port 80, but forwards traffic to port 8080 on the pods. Clients connect to the service on port 80, and the traffic is routed to the container's port 8080.

</details>

### Q3: Creating Services
Write the command to expose a deployment named `web` as a NodePort service on port 80:

<details>
<summary>Answer</summary>

```bash
kubectl expose deployment web --port=80 --type=NodePort
```

</details>

### Q4: Service Selectors
A service shows `<none>` for ENDPOINTS. What's the most likely cause?

<details>
<summary>Answer</summary>

The service's selector doesn't match any running pod's labels. Check the selector with `kubectl describe svc <name>` and verify pods have matching labels with `kubectl get pods --show-labels`.

</details>

### Q5: ExternalName Service
What type of DNS record does an ExternalName service create?

<details>
<summary>Answer</summary>

**CNAME record**

An ExternalName service returns a CNAME record that aliases the service name to the specified external DNS name. No proxying occurs.

</details>

### Q6: Session Affinity
How do you configure a service to route requests from the same client to the same pod?

<details>
<summary>Answer</summary>

Set `sessionAffinity: ClientIP` in the service spec:

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

</details>

### Q7: NodePort Range
What is the default NodePort range in Kubernetes?

<details>
<summary>Answer</summary>

**30000-32767**

This range is configurable via the `--service-node-port-range` flag on the API server.

</details>

---

## Section 2: Endpoints & EndpointSlices (4 questions)

### Q8: Endpoints Purpose
What is the relationship between Services and Endpoints?

<details>
<summary>Answer</summary>

Endpoints track the pod IPs that back a service. When pods match a service's selector, their IPs are added to the Endpoints object. The endpoint controller automatically creates and updates Endpoints based on pod label matching and readiness.

</details>

### Q9: Manual Endpoints
When would you create a service without a selector and manual Endpoints?

<details>
<summary>Answer</summary>

When pointing to:
- External databases or services outside the cluster
- Services in other clusters
- Any IP-based resource that isn't a Kubernetes pod

Create the service without selector, then create an Endpoints object with the same name containing the external IPs.

</details>

### Q10: EndpointSlices
Why were EndpointSlices introduced?

<details>
<summary>Answer</summary>

To improve scalability. A single Endpoints object for services with thousands of pods became a performance bottleneck. EndpointSlices split endpoints into chunks of up to 100, so updates only affect one slice instead of the entire object.

</details>

### Q11: NotReady Addresses
In an Endpoints object, what's the difference between `addresses` and `notReadyAddresses`?

<details>
<summary>Answer</summary>

- `addresses`: Pod IPs that are ready and will receive traffic
- `notReadyAddresses`: Pod IPs that aren't passing readiness probes and won't receive traffic

Traffic is only routed to addresses in the `addresses` list.

</details>

---

## Section 3: DNS & CoreDNS (5 questions)

### Q12: DNS Name Format
What's the FQDN for a service named `api` in namespace `production`?

<details>
<summary>Answer</summary>

`api.production.svc.cluster.local`

Format: `<service>.<namespace>.svc.<cluster-domain>`

</details>

### Q13: Cross-Namespace Resolution
A pod in namespace `dev` needs to reach service `cache` in namespace `prod`. What DNS name should it use?

<details>
<summary>Answer</summary>

`cache.prod` or `cache.prod.svc.cluster.local`

The short name `cache` alone won't work from a different namespace.

</details>

### Q14: CoreDNS Configuration
Where is CoreDNS configuration stored?

<details>
<summary>Answer</summary>

In a ConfigMap named `coredns` in the `kube-system` namespace. The configuration is in the `Corefile` key.

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

</details>

### Q15: ndots Setting
What does `ndots:5` in `/etc/resolv.conf` mean?

<details>
<summary>Answer</summary>

If a query has fewer than 5 dots, try appending search domains first before querying as an absolute name. This optimizes resolution for Kubernetes names like `web-svc.default.svc.cluster.local` (4 dots) - they're tried with search domains first.

</details>

### Q16: Headless Service DNS
How does DNS behavior differ for a headless service?

<details>
<summary>Answer</summary>

Regular services return a single A record (the ClusterIP). Headless services (with `clusterIP: None`) return multiple A records - one for each pod IP. Clients receive all pod IPs and can implement their own load balancing or connect to specific pods.

</details>

---

## Section 4: Ingress (4 questions)

### Q17: Ingress vs LoadBalancer
What's the main advantage of Ingress over LoadBalancer services?

<details>
<summary>Answer</summary>

Ingress provides Layer 7 (HTTP/HTTPS) routing with:
- Path-based routing (multiple services behind one IP)
- Virtual hosts (host-based routing)
- TLS termination
- URL rewriting

LoadBalancer is Layer 4 and requires one cloud LB per service. Ingress consolidates multiple services behind a single external IP.

</details>

### Q18: Ingress Address
An Ingress shows no ADDRESS. What's the likely cause?

<details>
<summary>Answer</summary>

No Ingress controller is installed, or the `ingressClassName` doesn't match any installed controller.

Fix: Install an Ingress controller and/or verify the IngressClass configuration.

</details>

### Q19: Path Types
What's the difference between `pathType: Prefix` and `pathType: Exact`?

<details>
<summary>Answer</summary>

- `Prefix`: Matches any path starting with the value. `/api` matches `/api`, `/api/users`, `/api/v1/...`
- `Exact`: Only matches the exact path. `/api` matches only `/api`, not `/api/` or `/api/users`

</details>

### Q20: TLS Configuration
What two things are needed to configure HTTPS on an Ingress?

<details>
<summary>Answer</summary>

1. A TLS Secret containing the certificate and key
2. A `tls` section in the Ingress spec referencing the secret and specifying which hosts it applies to

```yaml
spec:
  tls:
  - hosts:
    - example.com
    secretName: example-tls
```

</details>

---

## Section 5: Gateway API (4 questions)

### Q21: Gateway API Resources
What are the three main Gateway API resources and who typically creates each?

<details>
<summary>Answer</summary>

1. **GatewayClass** - Created by Infrastructure Provider (defines controller)
2. **Gateway** - Created by Cluster Operator (configures listeners, addresses)
3. **HTTPRoute** - Created by Application Developer (defines routing rules)

This role-based separation is a key improvement over Ingress.

</details>

### Q22: Traffic Splitting
How do you configure 90/10 traffic split in Gateway API?

<details>
<summary>Answer</summary>

Use `weight` in backendRefs:

```yaml
rules:
- backendRefs:
  - name: stable
    port: 80
    weight: 90
  - name: canary
    port: 80
    weight: 10
```

</details>

### Q23: Gateway API vs Ingress
Name two features Gateway API has that Ingress doesn't have natively:

<details>
<summary>Answer</summary>

Any two of:
- **Header-based routing** (native support, not annotations)
- **Traffic splitting/weights** (native support)
- **Multi-protocol support** (TCP, UDP, TLS, gRPC, not just HTTP)
- **Role-oriented design** (separate resources by role)
- **Cross-namespace routing** with ReferenceGrant
- **Request/response header modification** (native)

</details>

### Q24: ReferenceGrant
What is a ReferenceGrant used for?

<details>
<summary>Answer</summary>

ReferenceGrant allows resources in one namespace to reference resources in another namespace. For example, allowing an HTTPRoute in namespace `frontend` to route traffic to a Service in namespace `backend`.

Without ReferenceGrant, cross-namespace references are denied by default.

</details>

---

## Section 6: Network Policies (4 questions)

### Q25: Default Behavior
What is the default network behavior for pods without any NetworkPolicy?

<details>
<summary>Answer</summary>

All traffic is allowed. Pods can communicate with any other pod in the cluster without restrictions. Kubernetes has a flat network model with no isolation by default.

</details>

### Q26: Deny All Ingress
Write a NetworkPolicy that denies all ingress traffic to pods in the current namespace:

<details>
<summary>Answer</summary>

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}          # Selects all pods
  policyTypes:
  - Ingress                # No ingress rules = deny all
```

</details>

### Q27: Selector Logic
What's the difference between these two ingress rules?

```yaml
# Version A
ingress:
- from:
  - podSelector: {matchLabels: {app: a}}
  - namespaceSelector: {matchLabels: {name: x}}

# Version B
ingress:
- from:
  - podSelector: {matchLabels: {app: a}}
    namespaceSelector: {matchLabels: {name: x}}
```

<details>
<summary>Answer</summary>

**Version A: OR logic**
Allows traffic from pods with `app=a` OR from any pod in namespace with `name=x`.

**Version B: AND logic**
Allows traffic only from pods with `app=a` that are also in namespace with `name=x`.

The difference is whether selectors are in the same `from` array item (AND) or separate items (OR).

</details>

### Q28: DNS and Egress
Why is it important to allow DNS egress when restricting outbound traffic?

<details>
<summary>Answer</summary>

Pods need DNS (port 53) to resolve service names. Without DNS egress, pods can't look up `my-service.default.svc.cluster.local`, breaking service discovery.

Always include DNS in egress policies:
```yaml
egress:
- to:
  - namespaceSelector: {}
  ports:
  - port: 53
    protocol: UDP
  - port: 53
    protocol: TCP
```

</details>

---

## Section 7: CNI & Cluster Networking (2 questions)

### Q29: CNI and NetworkPolicy
Which common CNI plugin does NOT support NetworkPolicy?

<details>
<summary>Answer</summary>

**Flannel**

Flannel is a simple overlay network focused only on connectivity. It doesn't implement NetworkPolicy enforcement. Use Calico, Cilium, or Weave for NetworkPolicy support.

</details>

### Q30: kube-proxy Modes
What are the two main kube-proxy modes and which is better for large clusters?

<details>
<summary>Answer</summary>

**iptables mode**: Uses iptables rules for service routing. Good for most clusters.

**IPVS mode**: Uses kernel IPVS (IP Virtual Server) for routing. Better for large clusters because:
- O(1) lookup time vs O(n) for iptables
- Supports more load balancing algorithms
- Better performance with many services/endpoints

</details>

---

## Scoring

Count your correct answers:

| Score | Result |
|-------|--------|
| 27-30 | Excellent! Ready for Part 4 |
| 24-26 | Good. Review missed topics, then proceed |
| 20-23 | Review the related modules before continuing |
| <20 | Re-study Part 3 modules |

---

## Review Resources

If you scored below 80%, review these modules:

- **Services questions (Q1-Q7)**: [Module 3.1](module-3.1-services.md)
- **Endpoints questions (Q8-Q11)**: [Module 3.2](module-3.2-endpoints.md)
- **DNS questions (Q12-Q16)**: [Module 3.3](module-3.3-dns.md)
- **Ingress questions (Q17-Q20)**: [Module 3.4](module-3.4-ingress.md)
- **Gateway API questions (Q21-Q24)**: [Module 3.5](module-3.5-gateway-api.md)
- **Network Policy questions (Q25-Q28)**: [Module 3.6](module-3.6-network-policies.md)
- **CNI questions (Q29-Q30)**: [Module 3.7](module-3.7-cni.md)

---

## Next Part

Proceed to [Part 4: Storage](../part4-storage/README.md) to learn about PersistentVolumes, StorageClasses, and data management in Kubernetes.
