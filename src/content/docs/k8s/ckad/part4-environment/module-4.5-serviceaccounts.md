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

The 2018 Tesla cryptojacking incident (see *GUI Security*) <!-- incident-xref: tesla-2018-cryptojacking --> shows that auto-mounted credentials on weakly authenticated entry points can give attackers persistent control-path access.

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

> **Stop and think**: You create a ServiceAccount called `pod-manager` and assign it to your pod. When the pod tries to list other pods via the
