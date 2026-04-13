---
title: "Module 1.7: Namespaces and Labels"
slug: prerequisites/kubernetes-basics/module-1.7-namespaces-labels
sidebar:
  order: 8
---

# Module 1.7: Namespaces and Labels

**Complexity:** [MEDIUM]  
**Time to Complete:** 35-40 minutes  
**Prerequisites:** [Module 1.4: Deployments](/prerequisites/kubernetes-basics/module-1.4-deployments/), [Module 1.5: Services](/prerequisites/kubernetes-basics/module-1.5-services/)

## Learning Outcomes

After completing this module, you will be able to:
- Segment a monolithic Kubernetes cluster into isolated logical environments using Namespaces and context switching.
- Design label taxonomies that enable targeted resource selection for Services, Deployments, and operational tooling.
- Differentiate between equality-based and set-based selectors to query and manipulate specific subsets of resources.
- Defend cluster stability by implementing namespace-level ResourceQuotas and LimitRanges to prevent resource starvation.
- Contrast the use cases of Labels versus Annotations for attaching metadata to Kubernetes objects.

## Why This Module Matters

It is 2:00 AM on a Friday, and the platform engineering team is paged for a catastrophic cluster failure. The primary database backing the production e-commerce site has been evicted, and critical internal APIs are failing. The root cause? A junior developer deployed a load-testing tool in the `default` namespace without resource limits, which consumed 95% of the cluster's CPU and memory. Because there was no logical isolation or resource quota enforcing boundaries between the development testing tools and the production workloads sharing the same cluster, a simple mistake brought down the entire business. 

As your Kubernetes adoption grows, the physical cluster becomes a shared commodity. Running separate physical clusters for every team, environment (dev, staging, prod), and project is financially ruinous and operationally complex. Instead, you need a way to slice a single large cluster into dozens of "virtual clusters," where teams can operate autonomously without stepping on each other's toes or hoarding resources. You also need a standardized way to organize, search, and link thousands of disparate objects running inside those slices.

Namespaces are the walls that divide your cluster into manageable rooms. Labels are the sticky notes you attach to everything inside those rooms so you can find and connect them. Mastering these two concepts is the difference between a chaotic, fragile cluster where one command accidentally deletes production, and a highly structured, multi-tenant platform where blast radii are strictly contained.

## Section 1: Namespaces – The Virtual Clusters

At its core, a Namespace is a logical partition within a Kubernetes cluster. When you first install Kubernetes, you are dropped into a flat landscape where every Pod, Service, and ConfigMap lives side-by-side. As the number of resources grows, naming collisions become inevitable (you can only have one Service named `redis` in a given namespace), and managing permissions becomes a nightmare. 

Namespaces solve this by providing scope for names. You can have a `redis` Service in the `frontend` namespace and a completely different `redis` Service in the `backend` namespace. 

### What Namespaces Isolate (and What They Do Not)

It is crucial to understand exactly what a Namespace provides out of the box, because many engineers assume it provides strict security isolation. It does not.

```mermaid
graph TD
    subgraph "Kubernetes Cluster"
        subgraph "Cluster-Scoped Resources (No Namespace)"
            N1[Node 1]
            N2[Node 2]
            PV[Persistent Volumes]
            CR[ClusterRoles]
        end
        
        subgraph "Namespace: prod-frontend"
            P1[Pod: web-prod]
            S1[Service: web-svc]
            R1[Role: frontend-admin]
        end
        
        subgraph "Namespace: dev-backend"
            P2[Pod: api-dev]
            S2[Service: api-svc]
            R2[Role: backend-dev]
        end
        
        P1 -. "Network traffic is ALLOWED by default!" .-> P2
    end
```

**Namespaces DO isolate:**
1.  **Naming:** Resource names must be unique within a namespace, but not across namespaces.
2.  **DNS Records:** Kubernetes assigns DNS names to Services in the format `<service-name>.<namespace>.svc.cluster.local`. This means a Pod in namespace `prod-frontend` can talk to a Service in namespace `dev-backend` by querying its fully qualified domain name (FQDN). DNS queries from a Pod are namespace-scoped by default; an unqualified lookup targets the Pod's own namespace first (e.g., a query for `data` in the `test` namespace will not resolve a service in the `prod` namespace, while `data.prod` will, thanks to `/etc/resolv.conf` search list expansions).
3.  **Role-Based Access Control (RBAC):** You can grant a user full admin rights in the `dev` namespace while giving them zero access to the `prod` namespace using RoleBindings.
4.  **Resource Quotas:** You can restrict the total amount of CPU, Memory, or Storage that can be consumed by all resources combined within a single namespace.

**Namespaces DO NOT isolate:**
1.  **Network Traffic:** By default, the Kubernetes network is entirely flat. A Pod in the `dev` namespace can ping, port-scan, and connect to a Pod in the `prod` namespace. Namespaces do not provide network segmentation. (To isolate traffic, you must implement `NetworkPolicy` objects).
2.  **Node Placement:** Unless configured otherwise with NodeSelectors or Taints, Pods from different namespaces will be scheduled onto the exact same underlying worker nodes, sharing the same host kernel and container runtime.
3.  **Cluster-Scoped Resources:** Certain foundational resources are not bound to any namespace. Examples include Nodes, PersistentVolumes (the storage itself, not the claim), StorageClasses, and ClusterRoles. 

### The Default Namespaces

When you spin up a fresh cluster, Kubernetes pre-populates it with four standard namespaces:

*   `default`: The catch-all namespace. If you run `kubectl apply` without specifying a namespace, it goes here. In a mature production cluster, the `default` namespace should ideally be empty, as all workloads should be deployed to explicit, purpose-built namespaces.
*   `kube-system`: The engine room. This is where the Kubernetes control plane components run. If you inspect this namespace, you will see critical Pods like CoreDNS (for service discovery), kube-proxy (for network routing), and your CNI plugin (like Calico or Cilium). You should rarely modify resources here unless you are operating the cluster infrastructure itself.
*   `kube-public`: An automatically created namespace intended for resources that should be readable by all users (including unauthenticated ones). It was historically used to bootstrap clusters, but is rarely used in modern setups.
*   `kube-node-lease`: Contains Lease objects associated with each node. These leases act as heartbeats. Instead of the control plane constantly pinging massive Node status objects, each node simply updates a tiny Lease object in this namespace every few seconds. If a lease expires, the node is considered dead.

### Namespace Naming and Best Practices

When creating custom namespaces, the name must be a valid RFC 1123 DNS label. The Kubernetes documentation explicitly warns against creating namespaces with the `kube-` prefix, as this is conventionally reserved for system namespaces. Furthermore, you should avoid naming a namespace exactly like a public top-level domain (such as `com` or `org`), because it can create DNS short-name overlap risks. Finally, note that the Kubernetes control plane automatically attaches an immutable `kubernetes.io/metadata.name` label to every namespace upon creation, which is highly useful when writing policies or selectors that target specific namespaces.

### Interacting with Namespaces

Managing namespaces via the command line is straightforward, but constantly appending `-n <namespace>` to every `kubectl` command is tedious and prone to error.

To create a namespace imperatively:
```bash
kubectl create namespace team-frontend
```

To list all namespaces:
```bash
kubectl get namespaces
```

To run a command against a specific namespace:
```bash
kubectl get pods -n team-frontend
```

**Context Switching:**
Instead of specifying the namespace on every command, you can change your default namespace context within your `kubeconfig` file. 

```bash
# View your current context configuration to see your active namespace
kubectl config view --minify | grep namespace:

# Set the default namespace for your current context to 'team-frontend'
kubectl config set-context --current --namespace=team-frontend

# Now this command automatically looks in 'team-frontend'
kubectl get pods
```

*(War Story: A senior engineer once meant to delete a broken deployment in the `staging` namespace. They forgot the `-n staging` flag. Their context was set to `production`. They deleted the primary ingress controller for the entire company. Always verify your context before running destructive commands, and use tools like `kubectx` and `kubens` to make context switching visible and safe.)*

---

### Active Learning Prompt 1

**Scenario:** You are trying to deploy a new monitoring agent that needs to discover all Nodes in the cluster. You define the `DaemonSet` in the `monitoring` namespace. However, when you try to list the nodes using a `Role` bound to that namespace, it fails with a permissions error. 

**Question:** Based on how namespaces partition resources, why is your agent failing to list the Nodes, and how would you conceptually fix it?

<details>
<summary>Click for the Answer</summary>
Nodes are cluster-scoped resources, meaning they do not belong to any namespace. A <code>Role</code> and <code>RoleBinding</code> only grant permissions within a specific namespace. To grant permissions to list Nodes, you must use a <code>ClusterRole</code> and a <code>ClusterRoleBinding</code>, which operate outside the boundaries of namespaces and apply cluster-wide.
</details>

---

## Section 2: Labels and Selectors – The Glue of Kubernetes

If Namespaces are the walls, Labels are the organization system. Labels are simply key-value pairs attached to the metadata of Kubernetes objects. While names and UIDs identify objects uniquely, labels identify objects logically.

Kubernetes is a highly decoupled system. Deployments do not "own" Pods through a hardcoded list of IDs in a database. Services do not route traffic to Pods based on static IP addresses. Instead, they find each other dynamically using **Label Selectors**. This design allows the cluster to be incredibly dynamic—Pods can die and be recreated with new IPs and new names, and as long as they possess the correct labels, the system instantly self-heals the connections.

### Label Naming Conventions

A label key consists of an optional prefix and a name, separated by a slash (`/`).
*   **Prefix:** Must be a valid DNS subdomain (e.g., `company.com/`). The `kubernetes.io/` and `k8s.io/` prefixes are reserved for core Kubernetes components. Using a prefix is best practice for custom labels to avoid collisions with other tools. Automated system components adding labels to end-user objects should always use label key prefixes.
*   **Name:** Must be 63 characters or less, beginning and ending with an alphanumeric character.
*   **Value:** Must be 63 characters or less (can be empty, but must be alphanumeric at the ends when non-empty).

**Real-World Labeling Strategy:**
Do not randomly label resources. Adopt a standardized taxonomy across your organization. The Kubernetes documentation recommends a set of standard labels, but you can define your own. A mature labeling strategy enables granular cost allocation, security auditing, and operational triage.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: payment-processor-v2
  namespace: team-backend
  labels:
    app.kubernetes.io/name: payment-processor
    app.kubernetes.io/version: "2.1.4"
    app.kubernetes.io/part-of: e-commerce-suite
    tier: backend
    environment: production
    cost-center: "finance-ops"
spec:
  containers:
  - name: app
    image: payment-app:2.1.4
```

With these labels in place, you can query your cluster exactly like a database.

```bash
# Find all backend pods
kubectl get pods -l tier=backend

# Find all production payment processors
kubectl get pods -l app.kubernetes.io/name=payment-processor,environment=production
```

### Equality-Based vs. Set-Based Selectors

When querying or linking resources, Kubernetes supports two types of selectors. It is critical to know which resources support which type.

**1. Equality-Based Selectors**
These allow filtering by exact matches. Operators are `=`, `==`, and `!=`. Multiple requirements are separated by commas and act as a logical AND.

```bash
# Select pods where environment is exactly 'production'
kubectl get pods -l environment=production

# Select pods where tier is NOT 'frontend'
kubectl get pods -l tier!=frontend
```

In YAML, Services and ReplicationControllers currently *only* support equality-based selectors:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: payment-svc
spec:
  selector:
    app.kubernetes.io/name: payment-processor
    environment: production
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
```

> **Stop and think**: You need to find all pods in the `production` or `staging` environment that are NOT part of the `cache` tier. Write the `kubectl` selector expression to achieve this before reading the next section.

**2. Set-Based Selectors**
These allow filtering according to a set of values, enabling much more expressive queries. Operators are `in`, `notin`, `exists` (checking if the key exists, regardless of value), and `doesnotexist`. Note that `in` and `notin` require non-empty value lists. Selector expressions do not support a top-level logical OR operator (`||`), so set-based mechanisms are essential for matching multiple values.

```bash
# Select pods where environment is either 'production' OR 'staging'
kubectl get pods -l 'environment in (production, staging)'

# Select pods that have the 'release' label, regardless of its value
kubectl get pods -l release
```

In YAML, newer controllers like Deployments, Jobs, ReplicaSets, and DaemonSets use set-based selectors via `matchExpressions`, while still supporting equality via `matchLabels` (which internally translates to an `In` operator for a single value):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-deploy
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: payment-processor
    matchExpressions:
      - {key: environment, operator: In, values: [production, staging]}
      - {key: release, operator: Exists}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: payment-processor
        environment: production
        release: "true"
    spec:
      containers:
      - name: payment-processor
        image: payment-app:2.1.4
```

### The Power of Decoupling: Canary Deployments

Because Services route traffic based purely on labels, you can manipulate traffic flow without touching the Service itself. This is the foundation of advanced deployment strategies like blue/green and canary releases.

Imagine you have a Service selecting `app=frontend`. You have a Deployment with 10 Pods labeled `app=frontend, version=v1`. All traffic flows to `v1`.

You want to test `v2` with a small amount of live traffic. You simply deploy a single Pod (or a small Deployment) labeled `app=frontend, version=v2`. 

Because both versions share the `app=frontend` label, the Service will automatically begin routing ~10% of traffic (1 out of 11 Pods) to the new `v2` Pod. If it fails, you delete the `v2` Pod. If it succeeds, you scale up `v2` and scale down `v1`. The Service never knew what happened; it just routed to whatever matched its selector.

```mermaid
graph TD
    User-->SVC[Service\nselector: app=frontend]
    
    subgraph "Deployment v1 (10 Replicas)"
        P1[Pod\napp=frontend\nversion=v1]
        P2[Pod\napp=frontend\nversion=v1]
        P3[...]
    end
    
    subgraph "Deployment v2 (1 Replica - Canary)"
        P4[Pod\napp=frontend\nversion=v2]
    end
    
    SVC-->P1
    SVC-->P2
    SVC-->P3
    SVC-. "10% Traffic" .->P4
```

---

## Section 3: Annotations – Metadata for Machines

Labels are used by Kubernetes to select and group objects. **Annotations**, on the other hand, are used to attach arbitrary, non-identifying metadata to objects. 

If you try to put a 500-character JSON string into a Label, Kubernetes will reject it. Labels have strict length limits and are indexed by the API server for incredibly fast querying. Annotations are not indexed, cannot be used to select objects, and have a massive size limit (256KB).

> **Pause and predict**: Look at these 5 metadata items: 1) team name for filtering, 2) Git SHA of the commit, 3) Prometheus scrape config (`true`), 4) cost center for billing grouping, 5) SSL certificate directive for an ingress controller. Which ones should be Labels and which should be Annotations? Why?

**When to use Labels:**
*   Grouping (e.g., `tier: frontend`)
*   Selecting (e.g., linking a Service to Pods, or a Deployment to ReplicaSets)
*   Filtering output in `kubectl`

**When to use Annotations:**
*   Storing build/release information (e.g., the Git commit SHA that triggered the deployment)
*   Providing configuration directives to external controllers (e.g., telling an Ingress Controller which SSL certificate to use, or telling a cloud provider to provision an internal load balancer)
*   Adding contact information for the team responsible for the resource

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: reporting-job
  labels:
    app: reporting
  annotations:
    builder/author: "jane.doe@company.com"
    build/commit-sha: "a1b2c3d4e5f6g7h8i9j0"
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
spec:
  containers:
  - name: reporting
    image: reporting-job:latest
```
In the example above, Prometheus (a monitoring tool running in the cluster) will scan the API server, look for the `prometheus.io/scrape` annotation on Pods, and know exactly how to pull metrics from this specific pod, without cluttering the indexed Labels.

---

### Active Learning Prompt 2

**Scenario:** You are deploying a new internal wiki. You want the IT department to easily find it using `kubectl get pods -l dept=it`. You also need to pass a 400-character JSON configuration string to a third-party backup tool that watches the cluster for new deployments. 

**Task:** Write the `metadata` section of the Pod YAML that satisfies both requirements.

<details>
<summary>Click for the Answer</summary>

```yaml
metadata:
  name: internal-wiki
  labels:
    dept: it
  annotations:
    backup.company.com/config: '{"schedule": "0 2 * * *", "retention_days": 30, "storage_class": "cold-archive", "exclude_paths": ["/tmp", "/var/cache"]}'
```
*Explanation:* The `dept=it` requirement is used for selection/filtering, so it must be a Label. The 400-character JSON string is non-identifying configuration for an external tool and exceeds label limits, so it must be an Annotation.
</details>

---

## Section 4: ResourceQuotas and LimitRanges

If you give a team a Namespace, they now have a sandbox. But without limits, a child can build a sandcastle so big it spills out of the sandbox and crushes the rest of the playground. 

In Kubernetes, resource management happens in two phases:
1.  **Requests:** What a Pod says it needs to run. The `kube-scheduler` uses requests to find a Node with enough available capacity to fit the Pod.
2.  **Limits:** The hard ceiling on what a Pod can actually consume at runtime. If a Pod uses more memory than its limit, the `kubelet` terminates it (OOMKilled). If it tries to use more CPU, it is throttled.

By default, a Pod in any namespace can consume as much CPU and memory as the underlying node possesses. To prevent the "noisy neighbor" problem—where one runaway application starves every other application on the cluster—you must enforce boundaries at the Namespace level.

### ResourceQuotas: The Namespace Budget

A `ResourceQuota` limits the **total aggregate consumption** and object count across an entire namespace. It acts as a strict budget. Quota enforcement is namespace-scoped and is active only where at least one quota object exists.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: frontend-quota
  namespace: team-frontend
spec:
  hard:
    requests.cpu: "4"         # Total CPU requests cannot exceed 4 cores
    requests.memory: "8Gi"    # Total memory requests cannot exceed 8 Gigabytes
    limits.cpu: "8"           # Total CPU limits cannot exceed 8 cores
    limits.memory: "16Gi"     # Total memory limits cannot exceed 16 Gigabytes
    pods: "20"                # Cannot create more than 20 pods total
    services.loadbalancers: "2" # Cannot request more than 2 cloud LoadBalancers
```

If the `team-frontend` namespace currently uses 3.5 CPU cores, and a developer tries to deploy a new Pod requesting 1 CPU core, the API server will reject the Pod creation with a `403 Forbidden` error, stating the quota has been exceeded.

### LimitRanges: The Default Guardrails

ResourceQuotas have a severe catch: Once you apply a quota for CPU or Memory to a namespace, **every single Pod created in that namespace MUST specify CPU and Memory requests/limits**. If a Pod omits them, it will be instantly rejected by the admission controller.

Developers often forget to add these blocks to their YAML. To prevent frustration, you use a `LimitRange`. A LimitRange is a namespace-scoped policy constraining resource allocations for applicable resources like Pods and PersistentVolumeClaims. It automatically injects default CPU/Memory requests and limits into any Pod that forgets to declare them. It also sets minimum and maximum boundaries for a single Pod to prevent someone from deploying a Pod that takes up the entire namespace quota.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: frontend-limits
  namespace: team-frontend
spec:
  limits:
  - default:
      cpu: "500m"        # If limit is omitted, inject this
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"        # If request is omitted, inject this
      memory: "256Mi"
    max:
      cpu: "2"           # No single container can request/limit more than 2 CPU
      memory: "4Gi"
    min:
      cpu: "10m"         # No single container can request/limit less than 10m CPU
      memory: "64Mi"
    type: Container
```

**The Interplay:** The `LimitRange` ensures every Pod has a defined size (either explicitly or by default injection). The `ResourceQuota` ensures the sum of all those sizes does not exceed the namespace's total budget. You should never implement a ResourceQuota without a LimitRange.

> **Stop and think**: A namespace has a ResourceQuota of 4 CPU cores and a LimitRange default of 500m CPU. A developer deploys 7 Pods without specifying resources. What happens when they try to deploy an 8th? Walk through the math.

---

## Did You Know?

*   **Labels are strictly strings:** Even if you type `version: 1.0` in your YAML, Kubernetes will treat it as a string. However, unquoted numbers can cause parsing errors in some YAML parsers (e.g. interpreting `1.0` as a float), which is why it is best practice to always quote label values: `version: "1.0"`.
*   **A Namespace cannot be deleted quickly:** When you run `kubectl delete namespace <name>`, it deletes all resources within that namespace and the namespace itself enters a `Terminating` state. It will hang in this asynchronous state until every single object inside it is successfully garbage collected. If a resource has a broken finalizer that hangs, the namespace deletion will block indefinitely until the finalizer is manually patched.
*   **The 63-character limit is historical:** The 63-character limit for label keys and values originates from the DNS standard RFC 1123, which restricts DNS labels to 63 characters. Kubernetes adopted this to ensure labels could safely map to DNS structures and internal naming conventions.
*   **Annotations can hold 256KB:** While label values are severely restricted, a single annotation value can hold up to 256 kilobytes of data. This makes it large enough to store entire configuration files, small shell scripts, or massive JSON policy documents.

---

## Common Mistakes

| Mistake | Why It Happens | How To Fix It |
| :--- | :--- | :--- |
| **Assuming Namespaces isolate network traffic** | Namespaces provide logical isolation, but the underlying overlay network is flat by default. Any pod can ping any pod. | Implement Kubernetes `NetworkPolicy` objects to explicitly deny cross-namespace ingress/egress traffic. |
| **Using Equality-Based Selectors in Deployments** | The `matchLabels` block in a Deployment looks like equality, but Deployments actually require the more robust set-based selector engine under the hood to manage ReplicaSets. | Use `matchLabels` (which converts to `In`) or explicitly use `matchExpressions` in `apps/v1` Deployments. |
| **Storing large JSON configs in Labels** | Misunderstanding the purpose of labels vs annotations. Labels have strict length limits and are indexed, causing API server bloat if misused. | Move any non-identifying metadata, configuration blobs, or human-readable notes into `annotations`. |
| **Creating ResourceQuotas without LimitRanges** | The cluster admin locks down the namespace with a quota, causing all existing CI/CD pipelines to fail because the Pods lack explicit resource requests. | Always deploy a `LimitRange` with default values *before* or *alongside* enforcing a `ResourceQuota`. |
| **Creating objects in `default` namespace** | Laziness or lack of context awareness. Leads to a cluttered, unmanageable cluster where blast radii overlap heavily. | Always define `namespace: <name>` in your YAML metadata, or use tools like `kubens` to strictly set your context. |
| **Mutating immutable label selectors** | Trying to change the `matchLabels` selector of an existing Deployment. The API server will reject it because the Deployment would lose track of its existing ReplicaSets. | You must delete the Deployment (and its associated resources) and recreate it if the core selector taxonomy changes. |

---

## Quiz

<details>
<summary><strong>Question 1:</strong> You have a namespace called <code>analytics</code>. You deploy a Service named <code>data-sink</code> in this namespace. What is the fully qualified DNS name (FQDN) that a Pod in the <code>default</code> namespace should use to connect to it?</summary>
<p><strong>Answer:</strong> <code>data-sink.analytics.svc.cluster.local</code>. By default, Kubernetes DNS searches for services within the same namespace as the querying Pod. Because the querying Pod is in the <code>default</code> namespace and the target Service is in the <code>analytics</code> namespace, a short name like <code>data-sink</code> will fail to resolve. To cross the logical namespace boundary, the Pod must provide the fully qualified domain name (FQDN), which explicitly includes the target namespace, the <code>svc</code> subdomain, and the cluster's base domain. This robust DNS implementation guarantees that name collisions are avoided while still permitting explicit cross-namespace communication.</p>
</details>

<details>
<summary><strong>Question 2:</strong> A severe latency issue is affecting your user-facing applications. You need to immediately restart all Pods that belong to either the <code>frontend</code> or the <code>cache</code> tier to clear their memory, but you must leave the <code>database</code> and <code>backend</code> tiers alone. What <code>kubectl</code> selector command would you run to target exactly these two tiers?</summary>
<p><strong>Answer:</strong> You would use the set-based selector command: <code>kubectl delete pods -l 'tier in (frontend, cache)'</code>. Equality-based selectors (like <code>tier=frontend</code>) only support exact matches and logical AND operations, meaning they cannot express an "OR" condition. Set-based selectors introduce operators like <code>in</code>, <code>notin</code>, and <code>exists</code>, allowing you to evaluate multiple potential values for a single label key in a single query. By using the <code>in</code> operator, you effectively target multiple tiers simultaneously. This ensures the command selectively restarts only the problematic pods while preserving the stability of the remaining backend infrastructure.</p>
</details>

<details>
<summary><strong>Question 3:</strong> A developer complains that their new Deployment is failing to create its Pods, and the ReplicaSet event log says <code>forbidden: exceeded quota: pod-quota, requested: pods=1, used: 10, limited: 10</code>. What is the root cause?</summary>
<p><strong>Answer:</strong> The namespace has a <code>ResourceQuota</code> named <code>pod-quota</code> that enforces a hard limit of exactly 10 Pods for the entire namespace. The developer is attempting to scale up to an 11th Pod, but the admission controller intercepts the ReplicaSet's creation request and calculates that it would violate the quota. Consequently, the API server rejects the creation of the Pod outright, leaving the controller unable to fulfill the desired state. Resource quotas act as strict budgets to prevent any single team from starving the cluster of resources. Without deleting an active pod or negotiating a higher quota limit with the cluster administrator, these additional pods will never be created.</p>
</details>

<details>
<summary><strong>Question 4:</strong> You need to store the email address of the team responsible for a Deployment so that a custom alerting script can notify them if the Deployment fails. Should you use a Label or an Annotation?</summary>
<p><strong>Answer:</strong> You should use an Annotation. Labels are designed strictly for identifying and grouping objects within Kubernetes, and they are indexed by the API server to facilitate fast querying (like matching a Service to Pods). An email address is non-identifying metadata intended for external tools or human operators, and you will never natively ask Kubernetes to "select all pods by this email address." Using an Annotation prevents cluttering the API server's index while providing ample space (up to 256KB) for the data. This ensures the control plane remains highly performant while still making critical operational metadata accessible to your external scripts.</p>
</details>

<details>
<summary><strong>Question 5:</strong> You apply a new <code>LimitRange</code> with a default CPU limit of <code>200m</code> to a namespace that already has 10 running Pods. These existing Pods were deployed without any resource limits. A developer panics, arguing that their currently running CPU-heavy batch jobs will immediately be throttled and fail. Are they correct?</summary>
<p><strong>Answer:</strong> No, the developer is incorrect. Kubernetes evaluates <code>LimitRange</code> (and <code>ResourceQuota</code>) policies strictly via Admission Controllers at the exact moment an object is created or updated. Existing Pods that are already running are completely ignored by these new rules and will not be retroactively modified, throttled, or evicted. The new <code>200m</code> CPU limit will only apply to new Pods deployed after the <code>LimitRange</code> was created, or if the existing Pods are restarted. This design ensures that introducing new governance policies does not inadvertently cause destructive outages to running production workloads.</p>
</details>

<details>
<summary><strong>Question 6:</strong> A junior developer needs to be able to delete and restart Pods to troubleshoot their application. However, security policies dictate they must not have this permission anywhere except within the <code>sandbox</code> namespace. Can namespaces provide this level of security isolation?</summary>
<p><strong>Answer:</strong> Yes, namespaces excel at this specific type of logical security isolation. Namespaces natively integrate with Kubernetes Role-Based Access Control (RBAC). By creating a <code>Role</code> that permits Pod deletion, and a <code>RoleBinding</code> that assigns this Role to the developer specifically within the <code>sandbox</code> namespace, you restrict their permissions entirely to that boundary. They will have no access to view or delete Pods in <code>default</code>, <code>production</code>, or any other namespace. This creates a secure boundary that empowers developers to manage their own environments without risking the integrity of critical cluster resources.</p>
</details>

---

## Hands-On Exercise: The Multi-Tenant Sandbox

In this exercise, you will create an isolated namespace, establish resource guardrails, and use labels to orchestrate a simulated canary deployment.

### Task 1: Create the Isolation Zone

Create a new namespace for a simulated development team and switch your active context to it.

<details>
<summary><strong>Solution</strong></summary>

```bash
# Create the namespace
kubectl create namespace alpha-team

# Switch your context to the new namespace
kubectl config set-context --current --namespace=alpha-team

# Verify you are in the new namespace
kubectl config view --minify | grep namespace:
```
</details>

### Task 2: Establish the Guardrails

Apply a `LimitRange` to the `alpha-team` namespace to ensure no developer can deploy a Pod without bounds, and no single Pod can consume more than 500m CPU.

1. Create a file named `guardrails.yaml`.
2. Define a `LimitRange` setting the default CPU request to `100m`, default limit to `200m`, and max limit to `500m`.
3. Apply it.

<details>
<summary><strong>Solution</strong></summary>

```yaml
# guardrails.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-guardrails
  namespace: alpha-team
spec:
  limits:
  - default:
      cpu: "200m"
    defaultRequest:
      cpu: "100m"
    max:
      cpu: "500m"
    type: Container
```

```bash
kubectl apply -f guardrails.yaml

# Verify the LimitRange
kubectl describe limitrange cpu-guardrails
```
</details>

### Task 3: Deploy the Stable Release

Deploy a simple NGINX application representing the stable version of your app. It should consist of 3 replicas. 
Label the deployment with `app: web` and `version: v1`.

<details>
<summary><strong>Solution</strong></summary>

```yaml
# web-v1.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
      version: v1
  template:
    metadata:
      labels:
        app: web
        version: v1
    spec:
      containers:
      - name: nginx
        image: nginx:1.26-alpine
```

```bash
kubectl apply -f web-v1.yaml
kubectl get pods --show-labels
```
*(Notice that even though you didn't specify CPU limits in the Pod template, if you `kubectl describe` the pods, they will have the 200m limit automatically injected by the LimitRange you created in Task 2).*
</details>

### Task 4: Expose the App

Create a Service named `web-svc` that routes traffic to your application. It should select traffic based **only** on the `app: web` label (ignoring the version).

<details>
<summary><strong>Solution</strong></summary>

```yaml
# web-svc.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
```

```bash
kubectl apply -f web-svc.yaml

# Verify the service is finding the 3 v1 pods
kubectl get endpoints web-svc
```
</details>

### Task 5: The Canary Release

Deploy a single Pod representing the new `v2` version of your application. Label it with `app: web` and `version: v2`. 

Observe how the Service handles this new Pod.

<details>
<summary><strong>Solution</strong></summary>

```yaml
# web-v2-canary.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-v2-canary
  labels:
    app: web
    version: v2
spec:
  containers:
  - name: nginx
    image: nginx:1.27-alpine
```

```bash
kubectl apply -f web-v2-canary.yaml

# Check the endpoints again
kubectl get endpoints web-svc
```
*Observation:* The Service's endpoint list now contains 4 IP addresses. Because the Service selector only looks for `app: web`, and both `v1` and `v2` have that label, the Service automatically load-balances traffic across both versions. You have successfully executed a basic canary release!
</details>

### Task 6: Cleanup

Delete the namespace to instantly destroy all resources created in this exercise, and return to the default namespace.

<details>
<summary><strong>Solution</strong></summary>

```bash
# Delete the namespace (this takes a few moments as it cleans up everything inside it)
kubectl delete namespace alpha-team

# Reset your context back to default
kubectl config set-context --current --namespace=default
```
</details>

---

## Next Module

You have now mastered the art of organizing and isolating resources. You understand how controllers find Pods dynamically, and how namespaces keep teams from colliding. However, creating these resources via imperative `kubectl create` commands is a path to unmaintainable, brittle infrastructure. It is time to speak the native language of the Kubernetes API.

**[Proceed to Module 1.8: YAML for Kubernetes](/prerequisites/kubernetes-basics/module-1.8-yaml-kubernetes/)** — Master the language Kubernetes speaks to learn how to declare your desired state in code, making your infrastructure repeatable, version-controllable, and bulletproof.