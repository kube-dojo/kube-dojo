---
title: "Module 4.5: ServiceAccounts"
slug: k8s/ckad/part4-environment/module-4.5-serviceaccounts
sidebar:
  order: 5
lab:
  id: ckad-4.5-serviceaccounts
  url: https://killercoda.com/kubedojo/scenario/ckad-4.5-serviceaccounts
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---

> **Complexity**: `[MEDIUM]` - Important for API access and identity
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 4.4 (SecurityContexts), understanding of RBAC basics

---

## Learning Outcomes

After completing this module, you will be able to:
- **Configure** pods to use specific ServiceAccounts for API server authentication.
- **Explain** how ServiceAccount tokens are dynamically mounted and used by applications inside pods.
- **Debug** API permission errors by tracing from pod identity to ServiceAccount and through to Role bindings.
- **Design** a least-privilege ServiceAccount architecture that strictly limits pod access to only required resources.
- **Diagnose** compromised token attack vectors by analyzing auto-mount configurations and legacy secrets.
- **Evaluate** the security posture of an existing namespace by auditing default ServiceAccount configurations.

---

## Why This Module Matters

In early 2018, hackers successfully infiltrated Tesla's Amazon Web Services (AWS) environment to secretly mine cryptocurrency. They did not achieve this by cracking complex edge firewalls or executing sophisticated zero-day exploits against the kernel. Instead, they simply found an exposed Kubernetes dashboard that did not require proper external authentication. Because this dashboard pod was running with a highly privileged, auto-mounted ServiceAccount token, the attackers immediately possessed administrative rights over the entire cluster infrastructure. They used this access to retrieve sensitive AWS credentials, deploy malicious cryptocurrency mining pods, and run up massive compute bills. 

The financial impact of cryptojacking incidents can run into hundreds of thousands of dollars in stolen compute resources, not to mention the immense cost of incident response, forensic auditing, and the severe reputational damage associated with a public security breach. This incident perfectly illustrates why pod identity is a tier-one security concern in modern cloud-native architectures. ServiceAccounts are the fundamental bedrock of how workloads authenticate to the Kubernetes API. When your application needs to list pods, read ConfigMaps, or provision new resources, it proves its identity using a ServiceAccount token. 

By default, Kubernetes mounts a credential token into every single pod, giving every container a potential pathway to the API server. For the CKAD exam and real-world platform engineering, mastering ServiceAccounts means understanding the principle of least privilege. You must know how to mint specific identities, bind them to scoped roles, securely project short-lived tokens, and—crucially—cut off API access entirely for the vast majority of applications that simply do not require cluster interaction.

---

## The Identity Crisis: What is a ServiceAccount?

In Kubernetes, there are two distinct categories of users that interact with the control plane: human users and service accounts. Human users are typically managed externally via OpenID Connect (OIDC), Active Directory, or cloud IAM providers like AWS IAM or Google Cloud IAM. Kubernetes deliberately does not have a native `User` object for humans. However, workloads running inside the cluster need a secure, native way to identify themselves to the API server. This is exactly where ServiceAccounts enter the picture. A ServiceAccount is a native Kubernetes object that provides a distinct identity for processes running within a Pod.

### Default ServiceAccount

By default, every time you create a new namespace, the Kubernetes control plane automatically provisions a ServiceAccount named `default`. If you create a Pod without explicitly specifying a ServiceAccount, the cluster automatically injects this `default` ServiceAccount into the Pod's configuration during the admission phase.

```bash
# View default ServiceAccount
k get serviceaccount
# NAME      SECRETS   AGE
# default   0         10d

# Describe it
k describe sa default
```

### Every Pod Gets a ServiceAccount

Because of the automatic injection mechanism, it is virtually impossible to have a Pod without an assigned identity. You can easily verify the identity assigned to any running workload by querying the API.

```bash
# Check pod's ServiceAccount
k get pod my-pod -o jsonpath='{.spec.serviceAccountName}'
# default

# Or in describe
k describe pod my-pod | grep "Service Account"
```

> **The Employee Badge Analogy**
>
> ServiceAccounts are like employee ID badges in a highly secure corporate building. Every employee (pod) gets a badge (ServiceAccount) that identifies them to the security systems (API server). The standard default badge (the `default` ServiceAccount) gets you through the front door into the lobby, but it does not grant access to any restricted areas. If an employee needs to enter the server room or the financial records office, they need a specific badge tied to specific permissions. Without a badge, you cannot even interact with the security desk.

---

## The Pod Admission Controller: How Identities are Assigned

When you submit a Pod manifest to the Kubernetes API, the system does not simply save the YAML to the etcd datastore blindly. It processes the manifest through a highly orchestrated chain of Admission Controllers. One of the most critical controllers in this chain is the ServiceAccount Admission Controller. 

This controller performs a strict sequence of operations:
1. It inspects the incoming Pod manifest to see if the `spec.serviceAccountName` field is populated.
2. If the field is blank, the controller mutates the manifest on the fly, setting the value to `default`.
3. It then queries the target namespace to verify that the specified ServiceAccount actually exists. If it does not exist, the controller rejects the Pod creation entirely.
4. It evaluates the token mounting rules (which we will cover in depth) and mutates the Pod definition to include a projected volume containing the cryptographic identity tokens.

Understanding this invisible mutation process is critical for debugging why a Pod might fail to start or why a Pod unexpectedly possesses credentials you did not explicitly define in your YAML files.

---

## Creating and Assigning Identity

To apply the principle of least privilege, you must stop relying on the `default` ServiceAccount and instead create bespoke identities tailored to the exact needs of individual applications.

### Imperative

The fastest way to generate a new identity during the CKAD exam or in a rapid troubleshooting scenario is using imperative commands.

```bash
# Create ServiceAccount
k create serviceaccount my-app-sa

# In specific namespace
k create sa my-app-sa -n my-namespace
```

### Declarative

For production environments, identities should always be codified as infrastructure-as-code and stored in version control systems.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: default
```

### In Pod Spec

Once the custom identity exists in the cluster, you must explicitly instruct your workloads to assume this identity by populating the `serviceAccountName` field in the Pod specification.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: my-app-sa    # Use this ServiceAccount
  containers:
  - name: app
    image: nginx
```

### In Deployment

When working with higher-level controllers like Deployments, DaemonSets, or StatefulSets, the identity must be defined within the Pod template specification. The controller will then ensure that every replica it stamps out inherits this precise identity.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      serviceAccountName: my-app-sa    # Pod template uses this SA
      containers:
      - name: app
        image: nginx
```

---

## Token Mounting and The Anatomy of a Token

Merely assigning a name to a Pod does not magically authenticate its network requests. The API server requires cryptographically secure proof of identity. Kubernetes provides this proof by mounting physical files into the running container's filesystem.

### Automatic Token Mounting (Default)

By default, the Kubernetes kubelet automatically provisions a special type of volume and mounts it at a standardized path inside every container in the Pod: `/var/run/secrets/kubernetes.io/serviceaccount/`. 

```bash
# View mounted token files
k exec my-pod -- ls /var/run/secrets/kubernetes.io/serviceaccount/
# ca.crt
# namespace
# token

# View the token
k exec my-pod -- cat /var/run/secrets/kubernetes.io/serviceaccount/token
```

### Token Contents

Inside this tightly controlled directory, you will find exactly three files. Each serves a distinct and vital purpose in establishing secure communication with the control plane.

| File | Purpose |
|------|---------|
| `token` | JWT token for API authentication |
| `ca.crt` | CA certificate to verify API server |
| `namespace` | Pod's namespace |

1. **The Token**: This is the actual credential. It is a signed JSON Web Token (JWT) that the application must attach to the `Authorization: Bearer` header of its HTTP requests. 
2. **The CA Certificate**: This file contains the public certificate of the cluster's internal Certificate Authority. The application uses this to verify that the API server it is talking to is legitimate, preventing Man-in-the-Middle (MitM) attacks.
3. **The Namespace File**: A simple plaintext file containing the name of the namespace the Pod resides in. This is incredibly useful for scripts that need to execute commands relative to their own namespace without having the namespace name hardcoded into the application logic.

---

## Deep Dive: The Mechanics of JSON Web Tokens (JWTs)

When you run `cat token`, you see a long string of seemingly random characters separated by two periods. This is a JSON Web Token (JWT). A JWT consists of three distinct parts: the Header, the Payload, and the Signature.

The Header defines the cryptographic algorithm used (typically RS256). The Payload contains the "claims"—statements about the identity. In Kubernetes, these claims include the ServiceAccount name, the namespace, the unique ID of the Pod that the token is bound to, and an expiration timestamp. Finally, the Signature is generated by hashing the Header and Payload together and encrypting them with the API server's private cryptographic key.

When the Pod sends this token back to the API server, the server uses its public key to cryptographically verify the signature. If a malicious actor intercepts the token and tries to alter the payload (for example, changing the ServiceAccount name from `guest` to `admin`), the signature will instantly become invalid, and the API server will outright reject the modified token.

---

## Securing the Perimeter: Disabling Auto-Mounts

> **Pause and predict**: Every pod gets the `default` ServiceAccount's token mounted automatically. Why might this be a security concern for pods that never call the Kubernetes API?

If your application is a simple NGINX web server serving static HTML files, it has absolutely no business communicating with the Kubernetes API. However, if the token is automatically mounted, a vulnerability in your web application (such as a directory traversal flaw or a remote code execution exploit) could allow an external attacker to read the token file. Once the attacker possesses the token, they can pivot from the compromised container and begin executing API requests against the cluster control plane.

### Disabling Automatic Token Mount

To severely limit the attack surface of your cluster, it is considered a fundamental security best practice to disable token mounting for all pods that do not require API access. This can be configured at two different levels.

**On Pod:**
Setting the flag directly on the Pod specification explicitly controls the behavior for that specific workload, overriding any defaults.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-api-access
spec:
  automountServiceAccountToken: false    # Don't mount token
  containers:
  - name: app
    image: nginx
```

**On ServiceAccount:**
Alternatively, you can configure the restriction at the ServiceAccount level. Any Pod that assumes this ServiceAccount will inherit the restriction by default, unless the Pod explicitly overrides it.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: restricted-sa
automountServiceAccountToken: false    # Default for pods using this SA
```

---

## Modern Token Architecture vs. Legacy Systems

The way Kubernetes handles ServiceAccount credentials has evolved drastically to address critical security vulnerabilities found in early cluster architectures.

### Bound Service Account Tokens (Kubernetes 1.22+)

In modern Kubernetes environments (v1.35+), the system relies exclusively on Projected Service Account Tokens (PSAT). These modern tokens are vastly superior for three main reasons:
- **Time-limited**: They expire automatically after a predefined duration (defaulting to one hour). The kubelet automatically requests fresh tokens and rotates them on the filesystem before they expire.
- **Audience-bound**: They can be restricted so they are only valid for specific external systems (like HashiCorp Vault or cloud identity providers).
- **Object-bound**: They are cryptographically tied to the exact Pod instance. If the Pod is deleted, the token is instantly invalidated.

```yaml
# Request token with specific audience
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: my-app-sa
  containers:
  - name: app
    image: my-app
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600    # 1 hour
          audience: my-audience
```

### Legacy Tokens (pre-1.24)

Historically, before the shift to the modern dynamic token system, long-lived tokens were generated automatically and stored persistently as Kubernetes Secret objects. This legacy approach is highly insecure because if a token was compromised, it would remain valid indefinitely unless an administrator manually hunted down and deleted the corresponding Secret. The following command demonstrates the legacy methodology which is now deprecated.

```bash
# Old way (deprecated) - DO NOT use
k create token my-app-sa    # Creates short-lived token instead
```

---

## Inside the Pod: Talking to the API

When a workload actually needs to interact with the API server, it must construct HTTP requests that properly utilize the three mounted files. The process involves reading the token into memory, specifying the CA certificate to validate the server's identity, and attaching the token as a Bearer authorization header.

```bash
# Inside a pod, query the API
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

# List pods in current namespace
curl -s --cacert $CACERT \
  -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces/$NAMESPACE/pods
```

To request a token manually from your local workstation for testing purposes or for external scripts, you utilize the `kubectl create token` command. This uses the TokenRequest API directly.

```bash
# Create short-lived token
k create token my-app-sa

# Create token with duration
k create token my-app-sa --duration=1h
```

### Visualization

```mermaid
flowchart TD
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
    A["1. Create ServiceAccount\n<code>k create sa my-app-sa</code>"] --> B["2. Assign to Pod\n<code>spec:</code>\n<code>  serviceAccountName: my-app-sa</code>"]
    B --> C["3. Token Mounted Automatically\n<code>/var/run/secrets/kubernetes.io/serviceaccount/</code>\n<code>├── token     ← JWT token</code>\n<code>├── ca.crt    ← API CA cert</code>\n<code>└── namespace ← Pod namespace</code>"]
    C --> D["4. Pod Uses Token for API Access\n<code>curl -H \"Authorization: Bearer $(cat /var/run/...)\"</code>\n<code>https://kubernetes/api/v1/...</code>"]
```

---

## The RBAC Connection: Binding Permissions

> **Stop and think**: You create a ServiceAccount called `pod-manager` and assign it to your pod. When the pod tries to list other pods via the API, it gets a 403 Forbidden error. What's missing?

A ServiceAccount alone is merely an identity—a name badge. By itself, it grants zero permissions. Kubernetes operates on a strict default-deny authorization model. To actually allow the ServiceAccount to perform actions against the API, you must integrate it with Role-Based Access Control (RBAC).

This requires the complete triad:
1. The **ServiceAccount** (The Subject)
2. The **Role** (The Permissions)
3. The **RoleBinding** (The Connection)

```yaml
# 1. Create ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-reader-sa
---
# 2. Create Role with permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
# 3. Bind Role to ServiceAccount
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
subjects:
- kind: ServiceAccount
  name: pod-reader-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

---

## War Story: The Compromised CI/CD Pipeline

In a major tech enterprise, a developer needed to create an automated deployment pipeline that ran inside the cluster. Seeking a quick solution, they assigned the heavily privileged `cluster-admin` ClusterRole directly to the `default` ServiceAccount in the `ci-cd` namespace. Several months later, a completely unrelated and vulnerable logging application was deployed into that same namespace. 

Because the logging pod did not specify a custom ServiceAccount, it automatically inherited the `default` account and its mounted token. When an external attacker exploited a remote code execution vulnerability in the logging application, they did not just gain a minor foothold—they immediately possessed full cluster administrative privileges because the token was automatically mounted and inherently overpowered. The attacker wiped the entire cluster infrastructure within minutes. The lesson? Never attach sweeping permissions to a default ServiceAccount, and always disable auto-mounting for pods that do not explicitly require it.

---

## Quick Reference

```bash
# Create ServiceAccount
k create sa NAME

# View ServiceAccounts
k get sa
k describe sa NAME

# Assign to pod
spec:
  serviceAccountName: NAME

# Disable auto-mount
spec:
  automountServiceAccountToken: false

# Create short-lived token
k create token NAME

# Check pod's SA
k get pod POD -o jsonpath='{.spec.serviceAccountName}'
```

---

## Did You Know?

- **The default ServiceAccount has no special permissions.** It can't do anything unless you add RBAC rules. This is secure by default.
- **Tokens are JWTs.** You can decode them to see claims: `cat token | cut -d. -f2 | base64 -d | jq`
- **ServiceAccounts are namespaced.** A ServiceAccount in namespace A cannot be used by pods in namespace B.
- **`kubectl auth can-i --as=system:serviceaccount:default:my-sa`** lets you test what a ServiceAccount can do.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Expecting default SA to have permissions | API calls fail with 403 Forbidden | Create specific RBAC Role and RoleBinding for the SA |
| Using deprecated long-lived tokens | Massive security risk if credentials leak | Use `k create token` or short-lived bound tokens |
| Not disabling mount when unneeded | Creates an unnecessary attack surface in the pod | Set `automountServiceAccountToken: false` |
| Wrong ServiceAccount name | Pod falls back to default SA, lacking permissions | Verify identity with `k describe pod` |
| Confusing SA with RBAC | SA alone is just an identity and doesn't grant access | Deploy the complete triad: SA + Role + RoleBinding |
| Creating SA in the wrong namespace | Pod cannot find the identity and fails to initialize | Always explicitly define the namespace parameter |
| Hardcoding API server IP addresses | Causes connection failures when control plane IPs change | Rely on the `ca.crt` and the internal `kubernetes.default.svc` DNS |

---

## Quiz

1. **A developer creates a ServiceAccount called `deployer-sa` and assigns it to a pod that needs to list Deployments. The pod starts successfully, but when it calls the Kubernetes API to list deployments, it gets a 403 Forbidden error. What is missing and what steps are needed to fix it?**
   <details>
   <summary>Answer</summary>
   A ServiceAccount by itself has no permissions — it's just an identity. You need three things: (1) a Role that grants the `list` verb on `deployments` in the `apps` apiGroup, (2) a RoleBinding that binds that Role to the `deployer-sa` ServiceAccount. Without RBAC, the ServiceAccount is like an employee badge that gets you through the front door but doesn't open any office doors. You can verify what the SA can do with `kubectl auth can-i list deployments --as=system:serviceaccount:default:deployer-sa`.
   </details>

2. **During a security audit, the team discovers that a frontend pod (which never calls the Kubernetes API) has a ServiceAccount token mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`. An attacker who compromises this pod could use the token to query the API server. How do you eliminate this attack surface?**
   <details>
   <summary>Answer</summary>
   Set `automountServiceAccountToken: false` in the pod spec (or on the ServiceAccount itself). This prevents Kubernetes from mounting the token, CA certificate, and namespace file into the pod. For pods that don't need API access — which is most application pods — this is a security best practice. You can set it on the pod spec level (affects just that pod) or on the ServiceAccount definition (affects all pods using that SA). Pod-level setting takes precedence if both are specified.
   </details>

3. **A pod is configured with `serviceAccountName: custom-sa`, but `kubectl describe pod` shows it's using the `default` ServiceAccount instead. What could have gone wrong?**
   <details>
   <summary>Answer</summary>
   The most likely cause is that the ServiceAccount `custom-sa` doesn't exist in the pod's namespace. When you specify a non-existent ServiceAccount, the behavior depends on the cluster configuration — some clusters reject the pod, others fall back to the default SA. Check with `kubectl get sa custom-sa` in the correct namespace. If it doesn't exist, create it with `kubectl create sa custom-sa`. Another possibility: the pod was created in a different namespace than where the SA exists (ServiceAccounts are namespaced). Always verify both the SA and pod are in the same namespace.
   </details>

4. **Your team manages two applications: an internal monitoring tool that needs to list pods across all namespaces, and a web frontend that only needs to read ConfigMaps in its own namespace. How would you set up ServiceAccounts and RBAC for each following least-privilege principles?**
   <details>
   <summary>Answer</summary>
   For the monitoring tool: create a ServiceAccount (e.g., `monitor-sa`), a ClusterRole with `list` and `get` verbs on `pods` resources, and a ClusterRoleBinding connecting them. ClusterRole + ClusterRoleBinding is needed because it must work across all namespaces. For the web frontend: create a ServiceAccount (e.g., `frontend-sa`), a Role (namespace-scoped) with `get` and `list` on `configmaps`, and a RoleBinding in the frontend's namespace. This follows least privilege — each SA gets exactly the permissions it needs, no more. The monitoring tool can only list pods (not delete or create), and the frontend can only read ConfigMaps in its own namespace.
   </details>

5. **A team is migrating a legacy Python application to a modern Kubernetes v1.35 cluster. They notice their deployment scripts, which traditionally ran `kubectl get secret my-sa-token -o yaml` to extract credentials, are suddenly failing with a "Not Found" error. Why?**
   <details>
   <summary>Answer</summary>
   Historically, Kubernetes automatically created a long-lived Secret for every ServiceAccount to store its token. In modern Kubernetes versions, this auto-generation was removed to eliminate the security risk of stale, non-expiring credentials. Applications must now use the TokenRequest API to dynamically provision time-limited, projected tokens. The legacy script fails because the expected Secret object simply is not generated by the cluster anymore.
   </details>

6. **You configure `automountServiceAccountToken: false` on the `default` ServiceAccount in the `prod` namespace, but a pod explicitly configured with `automountServiceAccountToken: true` is still getting the token mounted. Why did this happen?**
   <details>
   <summary>Answer</summary>
   Kubernetes evaluates configurations hierarchically. While the ServiceAccount defines the baseline default behavior for all pods that use it, the explicit configuration within an individual pod's specification always takes absolute precedence. By setting `automountServiceAccountToken: true` directly on the pod, the developer overrode the secure default established at the ServiceAccount level, instructing the admission controller to mount the token regardless of the broader restriction.
   </details>

7. **You are designing an automated CI/CD pipeline pod that needs to deploy resources to any arbitrary namespace in the cluster on demand. Should its ServiceAccount be bound to a Role or a ClusterRole?**
   <details>
   <summary>Answer</summary>
   The pipeline pod requires a ClusterRoleBinding connected to a ClusterRole. A standard RoleBinding is inherently confined to a single, specific namespace; it cannot grant permissions to create or modify resources across multiple namespaces. Because the CI/CD pod needs cluster-wide access to deploy into any target namespace dynamically, the authorization mechanism must be elevated to the cluster scope.
   </details>

---

## Hands-On Exercise

**Task 1: Create a Custom Identity**
Establish a dedicated ServiceAccount that your applications will use instead of falling back to the default identity.
<details>
<summary>Solution</summary>

```bash
k create sa app-sa

# Verify
k get sa app-sa
```
</details>

**Task 2: Launch a Pod using the Custom Identity**
Create a pod that explicitly assumes the identity you just created and inspect its mounted token directory.
<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sa-demo
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'cat /var/run/secrets/kubernetes.io/serviceaccount/namespace && sleep 3600']
EOF

# Verify SA assigned
k get pod sa-demo -o jsonpath='{.spec.serviceAccountName}'
echo

# Check token mount
k exec sa-demo -- ls /var/run/secrets/kubernetes.io/serviceaccount/
```
</details>

**Task 3: Launch a Pod with API Access Explicitly Disabled**
Demonstrate the principle of least privilege by launching a pod that actively rejects the automatic token mount.
<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-token
spec:
  serviceAccountName: app-sa
  automountServiceAccountToken: false
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls /var/run/secrets 2>&1 || echo "No secrets mounted" && sleep 3600']
EOF

k logs no-token
# Should show: No secrets mounted (or directory not found)
```
</details>

**Task 4: Environment Cleanup**
Remove the resources created during this exercise to maintain a clean cluster state.
<details>
<summary>Solution</summary>

```bash
k delete pod sa-demo no-token
k delete sa app-sa
```
</details>

### Success Checklist
- [ ] You can create a ServiceAccount using declarative and imperative methods.
- [ ] You can assign a specific identity to a pod.
- [ ] You can verify the presence or absence of a mounted token.
- [ ] You understand how to harden pods by disabling automatic token mounting.

---

## Practice Drills

### Drill 1: Create ServiceAccount (Target: 1 minute)

```bash
k create sa drill1-sa
k get sa drill1-sa
k delete sa drill1-sa
```

### Drill 2: Pod with ServiceAccount (Target: 2 minutes)

```bash
k create sa drill2-sa

cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill2
spec:
  serviceAccountName: drill2-sa
  containers:
  - name: app
    image: busybox
    command: ['sleep', '3600']
EOF

k get pod drill2 -o jsonpath='{.spec.serviceAccountName}'
echo

k delete pod drill2 sa drill2-sa
```

### Drill 3: Check Token Location (Target: 2 minutes)

```bash
k run drill3 --image=busybox --restart=Never -- sleep 3600

k exec drill3 -- ls /var/run/secrets/kubernetes.io/serviceaccount/
k exec drill3 -- cat /var/run/secrets/kubernetes.io/serviceaccount/namespace

k delete pod drill3
```

### Drill 4: Disable Token Mount (Target: 2 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill4
spec:
  automountServiceAccountToken: false
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'ls /var/run/secrets/kubernetes.io/serviceaccount 2>&1; sleep 3600']
EOF

k logs drill4
# Should show error (directory doesn't exist)

k delete pod drill4
```

### Drill 5: Create Token (Target: 2 minutes)

```bash
k create sa drill5-sa

# Create short-lived token
k create token drill5-sa

# Create with duration
k create token drill5-sa --duration=30m

k delete sa drill5-sa
```

### Drill 6: Deployment with ServiceAccount (Target: 3 minutes)

```bash
k create sa drill6-sa

cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill6
spec:
  replicas: 2
  selector:
    matchLabels:
      app: drill6
  template:
    metadata:
      labels:
        app: drill6
    spec:
      serviceAccountName: drill6-sa
      containers:
      - name: app
        image: nginx
EOF

# Verify all pods use correct SA
k get pods -l app=drill6 -o jsonpath='{.items[*].spec.serviceAccountName}'
echo

k delete deploy drill6 sa drill6-sa
```

---

## Next Module

[Module 4.6: Custom Resource Definitions](../module-4.6-crds/) - Ready to break beyond the built-in objects? In the next module, we explore Custom Resource Definitions (CRDs) and learn how to teach the API server entirely new concepts, allowing you to build truly custom cloud-native platforms.