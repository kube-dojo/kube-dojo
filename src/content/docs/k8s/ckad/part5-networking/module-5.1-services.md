---
revision_pending: false
title: "Module 5.1: Services"
slug: k8s/ckad/part5-networking/module-5.1-services
sidebar:
  order: 1
lab:
  id: ckad-5.1-services
  url: https://killercoda.com/kubedojo/scenario/ckad-5.1-services
  duration: "45-55 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core networking concept, multiple types to understand
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: [Module 1.1 (Pods)](../part1-design-build/module-1.3-multi-container-pods/), [Module 2.1 (Deployments)](../part2-deployment/module-2.1-deployments/), understanding of basic networking

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design and create** ClusterIP, NodePort, LoadBalancer, ExternalName, and headless Services for realistic application exposure paths
- **Debug Service connectivity** by inspecting selectors, endpoints, EndpointSlices, DNS names, and port mappings
- **Evaluate and compare** Service types for internal calls, node-level exposure, cloud load balancing, and direct pod discovery
- **Implement multi-port Services and session affinity** without hiding how `port`, `targetPort`, and `nodePort` control traffic flow

## Why This Module Matters

Hypothetical scenario: you have just shipped a three-replica API Deployment for a checkout workflow, and the pods are healthy, Ready, and serving traffic on their container port. Another Deployment tries to call it by pod IP because that worked during a quick smoke test. One rolling restart later, the pod IPs change, half the calls fail, and the real bug is not the application code at all; the team skipped the stable networking contract that Kubernetes Services provide.

Services matter because Kubernetes treats pods as replaceable implementation details. A Deployment can create new pods during a rollout, move them to another node after a drain, or replace them after a failed readiness probe. A Service gives clients a durable name and virtual address while Kubernetes keeps the backing endpoint set current, much like a company phone directory keeps the department extension stable even when individual employees change desks.

The CKAD exam expects you to create Services quickly, but speed alone is not enough for production work. You need to reason from symptoms to mechanisms: whether DNS resolved the name, whether the Service selector matched pods, whether the Service had ready endpoints, whether the client used the Service port, and whether kube-proxy or the data plane could forward the packet. This module targets Kubernetes 1.35 or newer and focuses on the decisions and debugging moves that keep those layers separate in your head.

## Service Types and Traffic Paths

A Service is a small API object with an outsized job: it separates the identity that clients use from the pods that happen to be alive at this moment. Without that separation, a client would need to discover every pod IP, remove dead ones, add new ones, and decide how to balance requests every time the workload changed. Kubernetes centralizes that bookkeeping by letting you declare a selector and a set of ports, then it continuously derives the current endpoint set from matching pods.

The Service type decides where the stable entry point is reachable. `ClusterIP` creates an internal virtual IP that other pods can use inside the cluster. `NodePort` builds on that internal Service and opens a static port on each node. `LoadBalancer` asks the environment, usually a cloud provider or local load balancer implementation, to provision an external address that forwards to the Service. `ExternalName` is different because it creates a DNS alias instead of a proxying Service address.

The virtual IP is not a pod and it is not a server process listening inside your namespace. It is an address that the cluster data plane recognizes and translates toward ready endpoints, usually through rules programmed by kube-proxy or an equivalent implementation supplied by the networking stack. That distinction matters when you debug: restarting the destination pods might change endpoints, but it does not recreate the Service address, and deleting the Service removes the stable contract even if every pod remains healthy.

Service routing also depends on readiness, not just existence. A pod can match the selector while still being excluded from normal Service traffic because its readiness probe has not passed. This is why `kubectl get pods` and `kubectl get endpoints` answer different questions. The pod list tells you what the workload controller created; the endpoint view tells you what the Service is currently willing to send traffic toward. In real incidents, that distinction is often the difference between an application bug and a rollout health gate doing its job.

ClusterIP is the default because most Kubernetes traffic is service-to-service traffic. Internal callers do not need to know which node hosts the destination pod, and they do not need public exposure just to reach another component in the same cluster. The Service below exposes port `80` to clients while forwarding to container port `8080`, which is common when you want a conventional service port but the application listens on a framework-specific port inside the container.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP          # Default, can be omitted
  selector:
    app: my-app
  ports:
  - port: 80               # Service port
    targetPort: 8080       # Container port
```

The imperative form is useful during the CKAD exam because `kubectl expose deployment` copies the Deployment selector into the Service. That helps you avoid hand-typing selector labels under time pressure, but you should still inspect the result because copied labels only help when the Deployment's pod template labels are already correct. The curls shown here are meant to run from a pod or other in-cluster execution context, not from your laptop shell.

ClusterIP Services can also be affected by cluster-level address family choices. On clusters configured for dual-stack networking, a Service may have IPv4 and IPv6 families according to its `ipFamilyPolicy` and related fields. You do not need to master dual-stack policy for this module, but you should know that the Service API owns those stable addresses and that clients should still use the Service name instead of hard-coding whichever IP family they happen to see first.

```bash
# Create imperatively (--name overrides the default Service name my-app)
kubectl expose deployment my-app --name=my-service --port=80 --target-port=8080

# Access from within cluster
curl http://my-service:80
curl http://my-service.default.svc.cluster.local:80
```

NodePort is the next layer outward. Kubernetes still creates a ClusterIP Service, but it also allocates or accepts a port from the Service node port range, which defaults to `30000-32767`. A packet sent to `<node-ip>:30080` reaches the node, enters the cluster networking rules, and is forwarded to one of the Service endpoints unless policy, firewall, or data-plane configuration blocks the path.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-nodeport
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
  - port: 80               # Service port (ClusterIP)
    targetPort: 8080       # Container port
    nodePort: 30080        # Node port (30000-32767)
```

NodePort is often misunderstood because it exposes every node, not only the nodes currently running matching pods. With the default traffic policy, a node that receives the packet can forward it across the cluster network to a pod on another node. That behavior is convenient for simple labs, but in production it means the path from external client to pod can include cloud firewalls, node security groups, kube-proxy rules, CNI routing, and readiness-driven endpoint selection.

The default NodePort behavior also affects source IP visibility. When traffic can hop from the receiving node to an endpoint on another node, the backend may see a translated source address depending on the data plane and traffic policy. `externalTrafficPolicy: Local` is sometimes used when preserving the original client source IP is more important than accepting traffic on every node, but it changes failure behavior because nodes without local ready endpoints should not receive traffic successfully. That is an operations choice, not just a YAML decoration.

```bash
# Create imperatively (--node-port pins the port shown in the YAML above)
kubectl expose deployment my-app --name=my-nodeport --type=NodePort --port=80 --target-port=8080 --node-port=30080

# Access from outside cluster
curl http://<node-ip>:30080
```

LoadBalancer Services keep the same Service abstraction but delegate the public entry point to infrastructure outside the Kubernetes API server. In a managed cloud cluster, the cloud controller manager usually creates a provider load balancer and writes its address into the Service status. In a local cluster, you may need a component such as MetalLB or the distribution's built-in load balancer support, otherwise the external address can remain pending even though the Service object is valid.

That pending state is a useful example of why Service status and Service spec are different. The spec says what you asked Kubernetes to create; status says what the environment has actually provisioned. A LoadBalancer Service with a pending external address can still have a ClusterIP and ready endpoints, so in-cluster clients may work while external clients cannot start. The right fix is to inspect provider integration, load balancer class, quotas, or local load balancer support rather than rewriting the application Deployment.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-loadbalancer
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

The command looks deceptively similar to the NodePort command because Kubernetes intentionally keeps the API shape consistent. The difference is in who can reach the Service and who owns the external address lifecycle. A LoadBalancer Service is the right tool when you need a layer-four external entry point, but HTTP host routing, path routing, certificate termination, and shared virtual hosts usually belong in the Ingress or Gateway layer covered later.

LoadBalancer is also not a promise that every cloud provider behaves identically. Some environments allocate health check node ports, some support provider-specific annotations, and some require a specific load balancer class. The portable part for CKAD is the Service contract: type, selector, ports, status, and endpoints. Provider-specific fields may be necessary in production, but they should not obscure the base Kubernetes model you can inspect with ordinary `kubectl` commands.

```bash
# Create imperatively
kubectl expose deployment my-app --name=my-loadbalancer --type=LoadBalancer --port=80 --target-port=8080

# Get external IP
kubectl get svc my-loadbalancer
# EXTERNAL-IP column shows the LB IP
```

Pause and predict: you have a Deployment with three replicas labeled `app: web`, then you create a Service with selector `app: webapp`. Before running any command, predict how many endpoints the Service will have and which single field you would inspect first to prove your answer. This prediction matters because a Service with no endpoints can still have a ClusterIP, DNS name, and valid YAML, so the object can look healthy while it forwards to nothing.

ExternalName solves a different problem from the proxying Service types. It lets pods use a Kubernetes Service-shaped name while DNS returns an external canonical name, such as a managed database name outside the cluster. There is no selector, no ClusterIP, no endpoint load balancing, and no kube-proxy forwarding, so ExternalName is useful for naming consistency but not for traffic control, readiness filtering, or protocol-aware routing.

Because ExternalName is DNS-only, it can surprise teams that expect the rest of the Service toolbox to apply. You cannot inspect Kubernetes endpoints for the external target because Kubernetes did not select any pods. You cannot fix external target health by changing a readiness probe because no pod readiness feeds the alias. You can still use it to keep application configuration stable while the external DNS name changes, but you should review it as a naming abstraction rather than a network proxy.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: database.example.com
```

The practical decision is to choose the smallest exposure surface that satisfies the caller. If only pods call the workload, start with ClusterIP. If something outside the cluster needs a quick layer-four path in a lab, NodePort may be sufficient. If the environment can provision a stable external load balancer and the application needs direct TCP or UDP exposure, use LoadBalancer. If the target is already an external DNS name and Kubernetes should only provide an internal alias, use ExternalName.

## Service Discovery, Selectors, and Endpoints

Service discovery has two halves: name resolution and endpoint selection. DNS turns names such as `my-service.default.svc.cluster.local` into a Service address or alias. Selectors and endpoint controllers decide which pod IPs are eligible to receive traffic behind that name. Debugging gets much easier when you ask which half failed instead of treating every connection failure as a generic networking problem.

Kubernetes creates DNS records for Services using a predictable hierarchy. A pod can usually resolve a Service in the same namespace by the short name, but cross-namespace calls need at least the namespace-qualified form. The fully qualified name is more verbose, yet it is valuable in examples because it makes the namespace and `svc` domain explicit instead of relying on the pod's resolver search path.

The search path is convenient until it hides the namespace you meant to call. A pod in `orders` that asks for `payments` may search `orders.svc.cluster.local` before it ever considers anything in `billing`. That is why cross-namespace examples should show the namespace even when the short name worked in a same-namespace test. When debugging, a DNS failure should lead you to verify the caller namespace, the Service namespace, the Service name, and the resolver search path before editing Service ports.

```
<service-name>.<namespace>.svc.cluster.local
```

| DNS Name | Resolves To |
|----------|-------------|
| `my-service` | Same namespace |
| `my-service.default` | default namespace |
| `my-service.default.svc` | default namespace, svc |
| `my-service.default.svc.cluster.local` | Full FQDN |

Environment variables are the older discovery mechanism, and they still matter because you may see them while debugging. Kubernetes injects Service-related environment variables only for Services that exist before the pod starts, so they are not a complete dynamic discovery system. DNS is usually the better habit because it tracks Service creation and changes without forcing every client pod to restart.

There is another practical reason to prefer DNS in lessons and manifests: environment variables create hidden startup ordering assumptions. If a client pod starts before a Service exists, that pod will not receive the Service variables until it is recreated. DNS avoids that particular trap because the name lookup happens when the client resolves the name, not when the pod was admitted. You may still need retries in the application, but you do not need to restart the client simply because the Service appeared later.

```bash
# Inside a pod
env | grep MY_SERVICE
# MY_SERVICE_SERVICE_HOST=10.96.0.1
# MY_SERVICE_SERVICE_PORT=80
```

The diagram below is the compact mental model to keep during the exam. ClusterIP is the internal base layer, NodePort adds a node-level entry point, and LoadBalancer adds an infrastructure-managed external address in front of that stack. The Service port is what the client uses, `targetPort` is what the pod receives, and `nodePort` exists only for Service types that expose a node-level port.

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Types                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ClusterIP (Internal Only)                                  │
│  ┌─────────────────────────────────────┐                   │
│  │  cluster.local:80 ──► Pod:8080      │                   │
│  │                   ──► Pod:8080      │                   │
│  │                   ──► Pod:8080      │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  NodePort (ClusterIP + Node Access)                        │
│  ┌─────────────────────────────────────┐                   │
│  │  <NodeIP>:30080 ──► ClusterIP:80 ──► Pods              │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  LoadBalancer (NodePort + External LB)                     │
│  ┌─────────────────────────────────────┐                   │
│  │  <ExternalIP>:80 ──► NodePort ──► ClusterIP ──► Pods   │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  Service Port Flow:                                        │
│  ┌──────────────────────────────────────────────────┐     │
│  │                                                   │     │
│  │  External ──► nodePort ──► port ──► targetPort   │     │
│  │    :80         :30080      :80       :8080       │     │
│  │                                                   │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Selectors are plain label queries, not ownership links. A Service does not point at a Deployment by name, and it does not care which controller created a pod. It asks for pods whose labels match all selector keys and values, then endpoint controllers publish the matching ready pod addresses for the Service. That design is flexible, but it also means one misspelled label can produce a perfectly valid Service with no backends.

```yaml
# Service
spec:
  selector:
    app: my-app
    tier: frontend

# Pod (must match ALL labels)
metadata:
  labels:
    app: my-app
    tier: frontend
```

Endpoints are the visible result of that selector match. Modern Kubernetes also uses EndpointSlices for scalable endpoint tracking, but `kubectl get endpoints` remains useful in CKAD-style debugging because it gives you a quick answer: does the Service have any ready backend addresses? If the list is empty, do not waste time testing external load balancers before you verify labels, readiness, and the target port.

EndpointSlices divide endpoint data into smaller API objects so large Services do not depend on one ever-growing Endpoints object. For day-to-day CKAD work, you can treat them as the scalable representation behind the same Service concept: selected, ready backend addresses with port information. In production debugging, EndpointSlices can show additional hints such as address type and conditions, which helps when a Service has many replicas or dual-stack addresses. The principle stays the same: endpoints are derived state, not a list you usually hand-maintain for selector-based Services.

```bash
# View endpoints
kubectl get endpoints my-service
# NAME         ENDPOINTS                         AGE
# my-service   10.244.0.5:8080,10.244.0.6:8080   5m

# Describe shows pod IPs
kubectl describe endpoints my-service
```

Before running this, what output do you expect if the Service selector is correct but every pod is failing its readiness probe? A careful answer distinguishes Running pods from ready endpoints. The pods may exist and even accept `kubectl logs`, but the Service should not send normal traffic to them until they become ready, which protects callers from pods that started but are not yet serving correctly.

When a Service has no matching pods, the endpoint view gives the cleanest signal. You can then compare the selector on the Service with the actual labels on the pods, rather than guessing from names. Names are for humans; labels are the data that the Service controller reads. This is why a Deployment named `web` can serve a Service named `frontend` as long as the labels match.

```bash
kubectl get endpoints my-service
# NAME         ENDPOINTS   AGE
# my-service   <none>      5m
```

Exercise scenario: a developer renames a Deployment from `api` to `orders-api` and updates the container image, but leaves an older Service selector behind. Clients still resolve the Service DNS name, and `kubectl get svc` still shows a ClusterIP, so the first symptom is an application timeout rather than an obvious API error. The reliable debug sequence is to inspect the Service selector, list pods with labels, inspect endpoints, then test from an in-cluster pod using the Service DNS name.

When the endpoint set exists but traffic still fails, move one layer deeper instead of looping on labels. Check whether the Service target port matches the actual container listener, whether NetworkPolicy allows the source pod to reach the destination pod, and whether the application responds when contacted through an in-cluster test pod. The Service object gives you the path, but it does not make a container listen on the right port or override policy that intentionally blocks traffic.

## Port Mapping, Multi-Port Services, and Session Affinity

Service ports are a source of many avoidable mistakes because the field names describe different sides of the connection. `port` is the port exposed by the Service and used by the client. `targetPort` is the port on the selected pod that receives the forwarded traffic. `nodePort` is the port opened on nodes for NodePort and many LoadBalancer Services. If `targetPort` is omitted, Kubernetes defaults it to the same value as `port`, which is convenient only when the container listens on that same number.

Think of the three port fields as three doors in a hallway. The outside door is `nodePort` when node-level exposure is enabled, the hallway door is the Service `port`, and the room door is the pod `targetPort`. A request can pass the first two doors and still fail at the room if the container is not listening there. That analogy keeps you from assuming a visible Service port proves that the backend listener is correct.

The distinction is not cosmetic. A Service with `port: 80` and `targetPort: 8080` can be perfectly correct for an application that listens on `8080`, but it will fail for an application that listens only on `80`. The error often appears as a timeout or connection refusal depending on where the packet dies, so the fix is not to recreate the Service blindly. The fix is to compare the Service target port with the container's actual listening port and readiness configuration.

Readiness probes deserve to be checked with the same discipline as Service ports. A pod may listen on the application port but fail readiness because the probe checks a different path, hostname, or port. In that case the Service correctly excludes the pod, and the endpoint list tells the truth even though a manual `kubectl exec` test might reach the process. Good debugging asks whether the Service cannot find pods, cannot reach their port, or is intentionally withholding traffic because readiness says they are not ready.

Multi-port Services are useful when one logical backend needs to expose separate ports under the same stable name, such as HTTP traffic and metrics scraping. Kubernetes requires each port entry to have a name when a Service has more than one port. Those names are not decoration; clients, probes, and other objects can refer to named ports, and the names keep each mapping unambiguous when humans inspect the YAML.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-port
spec:
  selector:
    app: my-app
  ports:
  - name: http           # Name required for multi-port
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
```

Named ports become especially helpful when pod templates evolve. If a container exposes a port named `http`, a Service can use `targetPort: http` rather than a literal number, allowing the pod template to own the numeric value. The original example uses numeric target ports because that is the most direct CKAD form, but in real manifests a named `targetPort` can reduce accidental drift between workload and Service YAML.

Port names should describe the protocol or purpose, not the current number. A name such as `http` or `metrics` remains meaningful when the numeric port changes, while a name such as `port-8080` becomes misleading after the first refactor. Kubernetes validates port names with DNS-label-like rules, so short lowercase names with hyphens are the safest habit. This small naming discipline pays off when Services, probes, monitors, and policies all need to refer to the same listener.

Session affinity changes how the Service chooses backends for repeated traffic from the same client IP. The default behavior is no sticky session guarantee; the data plane can distribute connections across ready endpoints. With `sessionAffinity: ClientIP`, Kubernetes tries to route traffic from the same client IP to the same backend for a period of time, which can help older applications that keep temporary state in memory. It does not replace application-level session storage, and it can create uneven load if many users arrive behind a small number of NAT addresses.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sticky-service
spec:
  selector:
    app: my-app
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  ports:
  - port: 80
```

Use session affinity deliberately, not as a first response to every intermittent bug. If clients fail because pods disagree about state, the stronger fix is usually shared storage, external session state, or a stateless design. Affinity can reduce user-visible churn during a migration, but it also hides distribution problems and can make load less even. On the exam, you mostly need to recognize the field and understand that it changes backend selection, not DNS, selectors, or port mapping.

The timeout value is another clue that session affinity is a routing hint, not a permanent assignment. Backends can disappear during rollouts, nodes can fail, and endpoint sets can change while clients continue to send requests. A Service cannot keep a user attached to a pod that no longer exists or is no longer ready. Design stateful behavior so the application remains correct when affinity breaks, then use affinity only when it improves compatibility or user experience.

The quick reference below preserves the commands you need when speed matters. It is still worth reading command output instead of assuming success, because the API server can accept a Service that later has no endpoints or cannot be reached from outside the cluster. Treat these commands as a starting point for verification, not as proof that traffic works.

```bash
# Create Service
kubectl expose deployment NAME --port=80 --target-port=8080
kubectl expose deployment NAME --type=NodePort --port=80
kubectl expose deployment NAME --type=LoadBalancer --port=80

# View Services
kubectl get svc
kubectl describe svc NAME

# View Endpoints
kubectl get endpoints NAME
kubectl get ep NAME

# Debug DNS
kubectl run tmp --image=busybox --rm -i --restart=Never -- nslookup my-service

# Test connectivity
kubectl run tmp --image=busybox --rm -i --restart=Never -- wget -qO- my-service:80
```

## Headless Services and External Discovery

Headless Services are for cases where clients need to discover individual pod addresses instead of sending traffic through a single virtual Service IP. Setting `clusterIP: None` tells Kubernetes not to allocate a ClusterIP for the Service. DNS can then return records for the backing pods, which is useful for StatefulSets, databases, peer discovery systems, and protocols where the client must know each member rather than any healthy member.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: headless-svc
spec:
  clusterIP: None          # Makes it headless
  selector:
    app: my-app
  ports:
  - port: 80
```

The important tradeoff is that headless discovery shifts more responsibility to the client. With a normal ClusterIP Service, the client can call one address and let the Service data plane pick a backend. With a headless Service, the client may receive multiple pod records and must decide how to connect, retry, or handle membership changes. That is exactly what some clustered systems need, but it is unnecessary complexity for a simple stateless web API.

Headless does not mean unmanaged. With a selector, Kubernetes still tracks which pods belong to the Service and publishes DNS records from that selected set. Without a selector, a Service can be paired with manually managed endpoints or EndpointSlices for advanced integrations, but that is outside the normal beginner path and easy to misuse. For CKAD, the important version is `clusterIP: None` plus a selector, because it demonstrates direct pod discovery without abandoning Kubernetes labels.

```bash
# Returns multiple A records (one per pod)
nslookup headless-svc.default.svc.cluster.local
```

For StatefulSets, headless Services also support stable network identity when paired with predictable pod names. A database member can be addressed by a stable DNS name tied to its ordinal, which matters for replication and peer membership. The Service is still not a database clustering solution by itself; it only provides the naming and discovery substrate that the application protocol can use.

This is why headless Services are a precision tool rather than a default. A stateless API usually benefits from not knowing which replica answered the request, because that lets Kubernetes and the data plane spread load over any ready endpoint. A clustered database may require the opposite because each member has a role, identity, or replication position. The Service type should match the application protocol's expectations instead of forcing every workload into one exposure pattern.

ExternalName belongs in the same mental family as discovery, not load balancing. It lets in-cluster clients use a Service-like name for something outside the cluster, but the returned DNS name points elsewhere and Kubernetes does not create endpoint objects. This means NetworkPolicy, readiness, Service target ports, and kube-proxy rules do not operate on the external target the way they do for selected pods. If you need policy and observability around egress, you will need additional controls beyond ExternalName.

Which approach would you choose here and why: a stateless frontend calling a replicated API, a database cluster whose members must find each other, or a pod that needs a stable internal name for a managed database DNS record? The best answers are ClusterIP for the frontend-to-API call, a headless Service for direct member discovery, and ExternalName only for the external DNS alias. The reasoning is more important than the names because each option gives clients a different contract.

## Patterns & Anti-Patterns

Good Service design starts with caller scope. Internal callers should usually get an internal name and nothing more, because every wider exposure path adds infrastructure, firewall, monitoring, and ownership questions. External exposure is not wrong, but it should be selected because a real client needs it, not because a tutorial used it first. The table below turns that judgment into repeatable patterns you can apply under exam pressure and in review.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| ClusterIP for service-to-service traffic | Backends called only by pods inside the cluster | Keeps exposure internal while DNS and endpoint updates follow pods | Pair with NetworkPolicy when namespace boundaries need enforcement |
| NodePort for controlled lab or infrastructure integration | You need a simple node-level TCP path and can manage firewall rules | Builds on ClusterIP and avoids requiring a cloud load balancer | Validate every node path unless using a traffic policy that narrows routing |
| LoadBalancer for direct external layer-four access | The platform can provision a stable external address for TCP or UDP | Offloads public address lifecycle to the environment | Use Ingress or Gateway when many HTTP routes should share one entry point |
| Headless Service for member discovery | Clients need individual pod records rather than a single virtual IP | DNS exposes backing pod addresses directly | Make sure the client handles multiple records and membership changes |

Anti-patterns usually come from collapsing distinct layers into one vague idea of "the Service is broken." A Service can be created successfully while DNS fails in the client pod, selectors match no ready pods, a target port points to the wrong container port, or a cloud firewall blocks the NodePort. Separating these layers lets you fix the narrow problem without replacing working objects.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Using pod IPs in application configuration | Restarts and rollouts replace pod IPs, so clients keep stale destinations | Use the Service DNS name and let endpoints change behind it |
| Exposing every workload with NodePort | Each Service opens a node-level port and increases firewall surface | Start with ClusterIP, then add Ingress, Gateway, or LoadBalancer only for external callers |
| Guessing selectors from object names | Names and labels drift, creating Services with no endpoints | Compare `kubectl describe svc` selectors with `kubectl get pods --show-labels` |
| Treating ExternalName as a proxy | Kubernetes only returns a DNS alias and does not health-check the target | Use a real proxy, gateway, or egress control when health and policy are required |

The pattern that scales best is to make the Service contract boring. Give it a clear name, keep selectors stable, expose the fewest ports necessary, and write manifests so a reviewer can tell which client side and backend side each port describes. That is not style advice; it reduces the number of layers you must inspect during an outage or exam scenario.

One review question catches many Service mistakes: "Who is the first legitimate caller?" If the answer is another pod, ClusterIP is usually enough. If the answer is a user on the internet, you probably need to decide between LoadBalancer, Ingress, or Gateway rather than jumping straight to NodePort. If the answer is a database peer, headless discovery may be right. Framing the decision around the caller prevents exposure choices from being copied mechanically between unrelated workloads.

Another useful review question is "What must remain stable when pods change?" For most applications, the stable thing is the Service name and port, while the endpoint list is allowed to move. For StatefulSet members, individual DNS identities may also need to remain stable. For ExternalName, the stable thing is the in-cluster alias, not the health or reachability of the external target. Clear stability requirements lead to clearer manifests.

## Decision Framework

When you choose a Service type, start with the caller and work inward. The first question is whether the caller is inside the cluster, outside the cluster, or not really calling a Kubernetes backend at all. The second question is whether the caller needs any healthy pod, a specific pod identity, or an external DNS alias. The third question is whether the infrastructure around the cluster can provision and protect the exposure you are requesting.

| Requirement | Prefer | Avoid | Reason |
|-------------|--------|-------|--------|
| Pods call a replicated backend in the same cluster | ClusterIP | NodePort by default | Internal DNS and endpoint selection are enough |
| A quick lab needs node-level access from outside | NodePort | LoadBalancer when no provider exists | NodePort is explicit and easy to inspect |
| A production TCP service needs a public address | LoadBalancer | Manually curling random node IPs | The platform owns the external address lifecycle |
| Clients must discover every database member | Headless Service | Normal ClusterIP | The client needs pod records, not a single virtual IP |
| In-cluster pods need a name for an external DNS target | ExternalName | Selectorless hacks with fake pod labels | DNS aliasing matches the real problem |

For debugging, invert the same framework. If the client is inside the cluster, test DNS from a temporary pod before investigating cloud load balancers. If the Service has no endpoints, inspect labels and readiness before testing NodePorts. If a NodePort works on one node and not another, check external firewall and node data-plane differences before changing the Deployment. Each branch narrows the search space by asking where the packet should enter and where Kubernetes should choose the backend.

The CKAD-friendly flow is simple enough to memorize. First, `kubectl get svc` confirms the object exists and shows its type, ClusterIP, ports, and external address state. Second, `kubectl describe svc` shows selectors and events. Third, `kubectl get endpoints` or EndpointSlices confirms ready backends. Fourth, an in-cluster test pod checks DNS and HTTP reachability. Only after those checks should you focus on node firewalls, cloud load balancer provisioning, or client-side configuration.

That order keeps you from chasing the loudest symptom. A DNS error is not fixed by editing `targetPort`, an empty endpoint set is not fixed by opening a firewall, and a pending external IP is not fixed by relabeling pods. Good operators do not memorize every possible failure; they preserve the boundary between discovery, selection, forwarding, and infrastructure exposure, then test one boundary at a time.

For exam work, the framework should become a short mental checklist rather than a long essay. Name resolves, Service exists, selector matches, endpoints exist, port mapping is correct, and exposure path is reachable. If one item fails, fix that item before moving down the list. This is faster than random edits because every command either confirms or rejects one specific assumption about the path from caller to pod.

For production review, add ownership and blast radius to the same decision. A ClusterIP Service is usually owned by the application team and protected by namespace policy. A LoadBalancer Service often involves platform quotas, DNS records, certificates elsewhere in the stack, and incident response expectations from teams outside the namespace. A NodePort Service may look small in YAML while creating a node-wide ingress surface. The right Service type is the one whose operational owners can actually support the exposure it creates.

## Did You Know?

- **kube-proxy doesn't actually proxy most Service traffic in the common iptables and IPVS modes.** Despite its name, it programs kernel forwarding rules so traffic can flow through the node data plane instead of through a long-running user-space proxy process.
- **Services are namespaced API objects, but their ClusterIP can be reached across namespaces when network policy and routing allow it.** The namespace mainly affects naming and ownership, which is why `payments.billing` and `payments.default` are different DNS targets.
- **NodePort uses all nodes by default.** With the usual cluster traffic policy, even nodes without the target pods can accept the node port and forward traffic to a ready endpoint elsewhere in the cluster.
- **The default NodePort range is `30000-32767`, and cluster administrators can change it with the kube-apiserver `--service-node-port-range` flag.** That range is high enough to avoid most well-known ports while still being predictable for firewall rules.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Selector does not match pod labels | The Service object is valid, but the endpoint controller finds no ready pods for the selector | Run `kubectl describe svc NAME`, compare with `kubectl get pods --show-labels`, then fix either the selector or labels |
| Wrong `targetPort` | The client reaches the Service port, but traffic is forwarded to a port where the container is not listening | Inspect the container ports and application config, then set `targetPort` to the actual backend listener |
| Using pod IP instead of Service DNS | A copied pod IP works briefly and then breaks after rollout, rescheduling, or restart | Configure clients with the Service name, namespace-qualified name, or full Service FQDN |
| Forgetting namespace in DNS | Short names resolve only through the caller pod's namespace search path | Use `service.namespace` or `service.namespace.svc.cluster.local` for cross-namespace calls |
| NodePort reachable on one node only | External firewall, security group, or node data-plane state differs between nodes | Confirm the assigned node port, test multiple nodes, and align firewall rules across the node pool |
| Expecting ExternalName to health-check traffic | ExternalName returns a DNS alias and has no Kubernetes endpoints to mark ready or unready | Use ExternalName only for naming, and add a proxy or gateway if health, policy, or retries are required |
| Hiding several protocols behind unnamed ports | Multi-port Services without clear names are hard to read and may be rejected by the API | Give every Service port a stable name such as `http`, `https`, or `metrics` |

## Quiz

<details>
<summary>Question 1: A developer creates a Service with `port: 80` and `targetPort: 8080`. Clients connect to the Service on port `80` but get connection refused, and the pods are Running with the application listening on port `80`. What is wrong and how do you fix it?</summary>

The Service is forwarding traffic to the wrong backend port. `port` is the client-facing Service port, while `targetPort` is the pod-side port, so this Service sends traffic to `8080` even though the container listens on `80`. Fix the Service so `targetPort: 80`, then verify endpoints and test from an in-cluster pod. Recreating the pods is not the primary fix because the mismatch is in the Service mapping, not pod scheduling.

</details>

<details>
<summary>Question 2: After deploying a new application, `kubectl get endpoints myservice` shows `<none>` even though three pods are Running and Ready. The Service was created with `kubectl expose deployment myapp --port=80`. What is the most likely cause, and what two commands would you run next?</summary>

The most likely cause is a selector and label mismatch, especially if the pods were created separately or the pod template labels changed after the Service was created. Run `kubectl describe svc myservice` to inspect the selector, then run `kubectl get pods --show-labels` to compare the actual pod labels. If the labels do not match, patch the Service selector or correct the pod labels so the endpoint controller can publish ready backend addresses. DNS and ClusterIP checks are less useful until the Service has endpoints.

</details>

<details>
<summary>Question 3: A pod in the `orders` namespace needs to call a Service named `payments` in the `billing` namespace. The developer tries `curl http://payments:80` and gets a DNS resolution failure. What URL should they use, and why?</summary>

They should use `http://payments.billing:80` or the full name `http://payments.billing.svc.cluster.local:80`. The short name `payments` is resolved using the caller pod's namespace search path, so a pod in `orders` first looks for a Service named `payments` in `orders`. Adding the namespace tells cluster DNS which Service object to resolve. Changing the Service type would not solve this specific failure because the client has not resolved the correct name yet.

</details>

<details>
<summary>Question 4: A team exposes an application with a NodePort Service. External users can reach `node1:30080` but not `node2:30080`, while both nodes are Ready and the Service has endpoints. What should you check before changing the Deployment?</summary>

Check the external path to `node2`, especially firewall rules, cloud security groups, and node-level data-plane health for the assigned node port. A NodePort Service should listen on each node by default, even when the selected pod runs elsewhere, so a one-node failure often points outside the Deployment. Confirm the node port with `kubectl get svc`, verify endpoints, then compare connectivity to each node. Changing replicas or image versions would not address a blocked node-level entry path.

</details>

<details>
<summary>Question 5: A StatefulSet-based database needs each member to discover the other members by pod identity. A teammate proposes a normal ClusterIP Service because it gives the application one stable IP. Would you accept that design?</summary>

For member discovery, a headless Service is usually the better fit because the client needs individual pod records rather than one virtual IP. A normal ClusterIP Service intentionally hides individual pod identity behind a single Service address, which is useful for stateless backends but wrong for protocols that manage peers explicitly. The StatefulSet can pair with a headless Service to produce stable DNS identities for members. You would still need the database to handle membership and replication correctly because Kubernetes only supplies discovery.

</details>

<details>
<summary>Question 6: A Service exposes both application traffic and metrics. The manifest has two `ports` entries but no names, and the API server rejects it. What change should you make, and what names would be reasonable?</summary>

Add a unique `name` field to every port entry in the multi-port Service. Reasonable names would be `http` for the application listener and `metrics` for the scrape endpoint, or `https` if the second port carries TLS traffic. Kubernetes requires names for multi-port Services so each mapping is unambiguous to clients, controllers, and humans reading the object. Changing the selector would not fix this validation error because the problem is in the Service port list.

</details>

<details>
<summary>Question 7: An application team enables `sessionAffinity: ClientIP` because users sometimes lose state when requests land on different pods. What risk should you call out in review, and what stronger design should they consider?</summary>

ClientIP affinity can reduce churn, but it can also create uneven backend load and hide the deeper problem that user state lives inside individual pods. If many users arrive through the same NAT address, they may stick to the same backend and overload it. A stronger design stores session state outside the pod or makes the application stateless, then lets the Service distribute traffic normally. Affinity can be a temporary compatibility choice, but it should not be treated as a substitute for application design.

</details>

## Hands-On Exercise

In this exercise, you will create and test the Service shapes from the lesson, then deliberately break a selector to practice endpoint debugging. The tasks move from the safe default, ClusterIP, to node-level exposure and then to a broken Service that looks valid but has no backends. Run these commands in a disposable namespace or lab cluster, because the cleanup removes the objects created by the exercise.

### Task

Create and test different Service types while explaining which layer each command verifies. The lab intentionally uses nginx because the application behavior is predictable, leaving the Service mechanics visible. If a command fails, do not skip ahead; classify the failure as object creation, selector matching, DNS resolution, port mapping, or external exposure before applying a fix.

### Success Criteria

- [ ] Create an nginx Deployment with three Ready replicas
- [ ] Expose the Deployment with a ClusterIP Service and test DNS from inside the cluster
- [ ] Replace the ClusterIP Service with a NodePort Service and identify the assigned node port
- [ ] Create a broken Service, prove it has no endpoints, and repair its selector
- [ ] Clean up the Deployment and every Service created during the exercise
- [ ] Complete at least two practice drills without using a kubectl alias in runnable commands

### Setup

The setup creates the backend that every later Service will target. Waiting for readiness before exposing the Deployment keeps the first endpoint check easy to interpret: if the Service selector is correct, you should see ready endpoints shortly after the Service is created. In a real rollout, you would also inspect pod events and readiness probes when endpoints do not appear.

```bash
# Create a deployment
kubectl create deployment web --image=nginx --replicas=3

# Wait for pods
kubectl wait --for=condition=Ready pod -l app=web --timeout=60s
```

### Part 1: ClusterIP Service

The first task uses the default Service type because the client is another pod inside the cluster. Notice that the test pod calls `web:80`, not a pod IP. That is the behavior you want applications to copy: the Service name is stable while the endpoint set can change behind it.

<details>
<summary>Solution for Part 1</summary>

```bash
# Create ClusterIP service
kubectl expose deployment web --port=80 --target-port=80

# Verify endpoints
kubectl get endpoints web

# Test from within cluster
kubectl run test --image=busybox --rm -i --restart=Never -- wget -qO- web:80

# Check DNS
kubectl run test --image=busybox --rm -i --restart=Never -- nslookup web.default.svc.cluster.local
```

</details>

### Part 2: NodePort Service

The second task replaces the internal-only Service with a NodePort Service. The goal is not to rely on NodePort for every workload, but to see how Kubernetes reports the assigned port and how the node-level entry path differs from the ClusterIP name. If your lab environment does not expose node IPs to your browser, confirming the Service object and assigned node port is still useful.

<details>
<summary>Solution for Part 2</summary>

```bash
# Delete ClusterIP service
kubectl delete svc web

# Create NodePort service
kubectl expose deployment web --type=NodePort --port=80 --target-port=80

# Get assigned NodePort
kubectl get svc web -o jsonpath='{.spec.ports[0].nodePort}'
echo

# Test (if you have node access)
# curl http://<node-ip>:<nodeport>
```

</details>

### Part 3: Debug No Endpoints

The third task creates a Service that has a valid ClusterIP and valid YAML but no matching pods. This is the most important debugging pattern in the module because it separates object creation from traffic readiness. You should be able to explain the failure before applying the patch: the selector asks for `app: wrong-label`, while the Deployment pods are labeled `app: web`.

<details>
<summary>Solution for Part 3</summary>

```bash
# Create service with wrong selector
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: broken-svc
spec:
  selector:
    app: wrong-label
  ports:
  - port: 80
EOF

# Check endpoints (should be empty)
kubectl get endpoints broken-svc

# Fix by patching selector
kubectl patch svc broken-svc -p '{"spec":{"selector":{"app":"web"}}}'

# Verify endpoints now exist
kubectl get endpoints broken-svc
```

</details>

### Cleanup

Cleanup is part of the exercise because stale Services create misleading DNS names and endpoint output during later labs. Delete the workload first or the Services first; either order is acceptable here because the objects are simple. If a delete reports that an object is already gone, inspect the remaining Services before leaving the environment.

<details>
<summary>Cleanup commands</summary>

```bash
kubectl delete deployment web
kubectl delete svc web broken-svc
```

</details>

### Practice Drills

These drills preserve the short exam-speed repetitions from the original module, but they should not replace the reasoning work above. Use them after you can already explain the traffic path, because the commands are only valuable when you can interpret their output. The targets are intentionally short to build fluency, not to imply that production debugging should be rushed.

### Drill 1: Create ClusterIP Service (Target: 1 minute)

```bash
kubectl create deployment drill1 --image=nginx
kubectl expose deployment drill1 --port=80
kubectl get svc drill1
kubectl get ep drill1
kubectl delete deploy drill1 svc drill1
```

### Drill 2: Create NodePort Service (Target: 2 minutes)

```bash
kubectl create deployment drill2 --image=nginx
kubectl expose deployment drill2 --type=NodePort --port=80 --target-port=80

# Get NodePort
kubectl get svc drill2 -o jsonpath='{.spec.ports[0].nodePort}'
echo

kubectl delete deploy drill2 svc drill2
```

### Drill 3: Test DNS Resolution (Target: 2 minutes)

```bash
kubectl create deployment drill3 --image=nginx
kubectl expose deployment drill3 --port=80

# Test DNS
kubectl run dns-test --image=busybox --rm -i --restart=Never -- nslookup drill3

kubectl delete deploy drill3 svc drill3
```

### Drill 4: Service with Named Port (Target: 2 minutes)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: drill4
spec:
  selector:
    app: drill4
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: metrics
    port: 9090
    targetPort: 9090
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill4
spec:
  replicas: 2
  selector:
    matchLabels:
      app: drill4
  template:
    metadata:
      labels:
        app: drill4
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Endpoints list both ports; nginx listens on 80 only — port 9090 appears before traffic succeeds
kubectl get svc drill4
kubectl get ep drill4
kubectl delete deploy drill4 svc drill4
```

### Drill 5: Debug Service Connectivity (Target: 3 minutes)

```bash
# Create deployment and broken service
kubectl create deployment drill5 --image=nginx
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: drill5
spec:
  selector:
    app: wrong
  ports:
  - port: 80
EOF

# Debug
kubectl get ep drill5                        # No endpoints
kubectl get pods --show-labels               # Check pod labels
kubectl describe svc drill5 | grep Selector  # Check service selector

# Fix
kubectl patch svc drill5 -p '{"spec":{"selector":{"app":"drill5"}}}'
kubectl get ep drill5                        # Should now have endpoints

kubectl delete deploy drill5 svc drill5
```

### Drill 6: Cross-Namespace Service Access (Target: 3 minutes)

```bash
# Create namespace and service
kubectl create ns drill6
kubectl create deployment drill6-app --image=nginx -n drill6
kubectl expose deployment drill6-app --port=80 -n drill6

# Access from default namespace
kubectl run test --image=busybox --rm -i --restart=Never -- wget -qO- drill6-app.drill6:80

kubectl delete ns drill6
```

## Learner check

> The imperative form is useful during the CKAD exam because `kubectl expose deployment` copies the Deployment selector into the Service. That helps you avoid hand-typing selector labels under time pressure, but you should still inspect the result because copied labels only help when the Deployment's pod template labels are already correct.

## Sources

- https://kubernetes.io/docs/concepts/services-networking/service/
- https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
- https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/
- https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/
- https://kubernetes.io/docs/reference/kubernetes-api/service-resources/service-v1/
- https://kubernetes.io/docs/reference/kubernetes-api/service-resources/endpoints-v1/
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- https://kubernetes.io/docs/tutorials/services/source-ip/
- https://kubernetes.io/docs/concepts/services-networking/dual-stack/
- https://kubernetes.io/docs/concepts/services-networking/ingress/

## Next Module

[Module 5.2: Ingress](../module-5.2-ingress/) introduces HTTP routing and TLS termination, building on the Service contracts you debugged here so one external entry point can route to many internal backends.
