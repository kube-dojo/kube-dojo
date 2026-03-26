---
title: "Module 6.3: Enterprise Identity (AD/LDAP/OIDC)"
slug: on-premises/security/module-6.3-enterprise-identity
sidebar:
  order: 4
---

> **Complexity**: `[MEDIUM]` | Time: 60 minutes
>
> **Prerequisites**: [Kubernetes Basics](../../prerequisites/kubernetes-basics/), [CKA](../../k8s/cka/), [CKS](../../k8s/cks/)

---

## Why This Module Matters

A logistics company with 2,400 employees deployed Kubernetes on-premises in 2022. The platform team created individual kubeconfig files for each developer -- 180 in total -- using x509 client certificates signed by the cluster CA. Within six months, the system was unmanageable. When a developer left the company, their certificate could not be revoked (Kubernetes has no certificate revocation). When a developer moved teams, someone had to generate a new certificate with different group memberships. The platform team spent 15 hours per week on access management.

Their Active Directory already had every employee, every team, every role. HR updated it on every hire, termination, and transfer. The fix was straightforward: integrate Kubernetes with AD via OIDC. They deployed Keycloak as an OIDC provider fronting their AD, mapped AD groups to Kubernetes RBAC roles, and deleted all 180 client certificates. When an employee leaves, HR disables their AD account, and Kubernetes access is revoked within minutes -- automatically, with zero platform team involvement. The 15 hours per week dropped to zero.

> **The Hotel Key Card Analogy**
>
> Client certificates are like physical keys -- once cut, you cannot un-cut them. If someone leaves, you must change all the locks. OIDC tokens are like hotel key cards -- the front desk (your identity provider) can deactivate any card instantly. Expired cards stop working automatically. You never need to change a lock. Every enterprise already has a "front desk" (Active Directory). The question is whether your Kubernetes cluster uses it.

---

## What You'll Learn

- Why x509 client certificates are a bad fit for enterprise Kubernetes authentication
- How to integrate Active Directory and LDAP with Kubernetes
- Deploying Keycloak as an on-premises OIDC provider
- Configuring Dex as a lightweight OIDC connector for Kubernetes
- Mapping corporate AD/LDAP groups to Kubernetes RBAC
- Setting up SSO for the Kubernetes dashboard and other tools

---

## Authentication Options for On-Premises Kubernetes

```
┌──────────────────────────────────────────────────────────────────┐
│             KUBERNETES AUTHENTICATION METHODS                    │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ x509 Client    │  │ Static Token   │  │ OIDC (Recommended) │ │
│  │ Certificates   │  │ File           │  │                    │ │
│  ├────────────────┤  ├────────────────┤  ├────────────────────┤ │
│  │ No revocation  │  │ Restart to     │  │ Short-lived tokens │ │
│  │ No expiry mgmt │  │ add/remove     │  │ Instant revocation │ │
│  │ Manual renewal │  │ Plaintext file │  │ Group claims       │ │
│  │ No group sync  │  │ No groups      │  │ AD/LDAP backed     │ │
│  │ No audit trail │  │ No audit trail │  │ Full audit trail   │ │
│  │                │  │                │  │ SSO across tools   │ │
│  │ AVOID for      │  │ NEVER use      │  │ USE THIS           │ │
│  │ humans         │  │ in production  │  │                    │ │
│  └────────────────┘  └────────────────┘  └────────────────────┘ │
│                                                                  │
│  x509 is fine for: service accounts, kubelet bootstrap, CI/CD   │
│  OIDC is for: every human user, dashboard access, kubectl       │
└──────────────────────────────────────────────────────────────────┘
```

---

## The OIDC Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    OIDC AUTHENTICATION FLOW                      │
│                                                                  │
│  Developer          OIDC Provider        API Server              │
│  (kubectl)         (Keycloak/Dex)       (kube-apiserver)         │
│     │                    │                    │                   │
│     │  1. kubectl login  │                    │                   │
│     │───────────────────>│                    │                   │
│     │                    │                    │                   │
│     │  2. Redirect to    │                    │                   │
│     │     AD/LDAP login  │                    │                   │
│     │<───────────────────│                    │                   │
│     │                    │                    │                   │
│     │  3. User enters    │                    │                   │
│     │     AD credentials │                    │                   │
│     │───────────────────>│                    │                   │
│     │                    │  (validates        │                   │
│     │                    │   against AD)      │                   │
│     │  4. ID token       │                    │                   │
│     │     (JWT with      │                    │                   │
│     │      groups claim) │                    │                   │
│     │<───────────────────│                    │                   │
│     │                    │                    │                   │
│     │  5. API request with Bearer token       │                   │
│     │────────────────────────────────────────>│                   │
│     │                    │                    │  6. Validate JWT  │
│     │                    │                    │     signature     │
│     │                    │                    │  7. Extract       │
│     │                    │                    │     groups claim  │
│     │                    │                    │  8. RBAC lookup   │
│     │  9. Response       │                    │                   │
│     │<────────────────────────────────────────│                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Option 1: Keycloak as OIDC Provider

Keycloak is the most full-featured open-source identity provider. It supports AD/LDAP federation, group sync, MFA, and fine-grained authorization.

### Deploy Keycloak on Kubernetes

Deploy Keycloak as a 2-replica Deployment in the `identity` namespace using `quay.io/keycloak/keycloak:26.0`. Key configuration:

```bash
# Keycloak start arguments:
keycloak start \
  --hostname=keycloak.internal.corp \
  --https-certificate-file=/tls/tls.crt \
  --https-certificate-key-file=/tls/tls.key \
  --db=postgres \
  --db-url=jdbc:postgresql://postgres.identity.svc:5432/keycloak \
  --health-enabled=true
```

Store the database password and admin password in Kubernetes Secrets. Expose via a ClusterIP Service on port 443. Add a readiness probe on `/health/ready`.

### Configure Active Directory Federation in Keycloak

After Keycloak is running, configure AD federation through the Admin Console or CLI:

1. **Create a realm** named `kubernetes`
2. **Add User Federation** > LDAP provider with these settings:

| Setting | Value |
|---------|-------|
| Vendor | Active Directory |
| Connection URL | `ldaps://dc01.corp.internal:636` |
| Bind DN | `CN=svc-keycloak,OU=Service Accounts,DC=corp,DC=internal` |
| Users DN | `OU=Users,DC=corp,DC=internal` |
| Username attribute | `sAMAccountName` |
| Edit mode | READ_ONLY |
| Full sync period | 3600 seconds |
| Changed sync period | 60 seconds |

3. **Add a group mapper** pointing to `OU=K8s Groups,DC=corp,DC=internal`
4. **Create an OIDC client** named `kubernetes` (public client, redirect to `http://localhost:8000/*`)
5. **Add a "groups" protocol mapper** to include group memberships in the ID token `groups` claim

---

## Option 2: Dex as a Lightweight Alternative

Dex is a CNCF project that acts as an OIDC provider by proxying to upstream identity providers. It is lighter than Keycloak -- a single Go binary with YAML configuration.

```yaml
# dex-config.yaml (key sections)
issuer: https://dex.internal.corp
storage:
  type: kubernetes
  config:
    inCluster: true
connectors:
- type: ldap
  id: active-directory
  name: "Corporate AD"
  config:
    host: dc01.corp.internal:636
    rootCA: /certs/ad-ca.crt
    bindDN: CN=svc-dex,OU=Service Accounts,DC=corp,DC=internal
    bindPW: $DEX_LDAP_BIND_PW
    userSearch:
      baseDN: OU=Users,DC=corp,DC=internal
      filter: "(objectClass=person)"
      username: sAMAccountName
    groupSearch:
      baseDN: OU=K8s Groups,DC=corp,DC=internal
      filter: "(objectClass=group)"
      userMatchers:
      - userAttr: DN
        groupAttr: member
      nameAttr: cn
staticClients:
- id: kubernetes
  redirectURIs: ["http://localhost:8000/callback"]
  name: Kubernetes
  secret: $DEX_CLIENT_SECRET
```

### Dex vs Keycloak Decision Matrix

| Criteria | Keycloak | Dex |
|----------|----------|-----|
| Complexity | High (Java, needs PostgreSQL) | Low (single Go binary) |
| Features | MFA, user mgmt, admin UI, fine-grained authz | OIDC proxy only |
| AD/LDAP | Full federation with sync | LDAP connector (query-on-login) |
| Resource usage | 512MB-2GB RAM | 50-100MB RAM |
| Admin interface | Full web UI | None (YAML config only) |
| Best for | Large enterprises, multiple apps needing SSO | Kubernetes-only OIDC |
| SAML support | Yes (SP and IdP) | No |

---

## Configuring kube-apiserver for OIDC

Regardless of whether you use Keycloak or Dex, the API server configuration is the same:

```bash
# Add these flags to kube-apiserver (in /etc/kubernetes/manifests/kube-apiserver.yaml)
spec:
  containers:
  - command:
    - kube-apiserver
    # ... existing flags ...
    - --oidc-issuer-url=https://keycloak.internal.corp/realms/kubernetes
    - --oidc-client-id=kubernetes
    - --oidc-username-claim=preferred_username
    - --oidc-username-prefix="oidc:"
    - --oidc-groups-claim=groups
    - --oidc-groups-prefix="oidc:"
    - --oidc-ca-file=/etc/kubernetes/pki/oidc-ca.crt
```

### Important Parameters Explained

```
--oidc-issuer-url      The OIDC provider's issuer URL. The API server
                       fetches /.well-known/openid-configuration from here
                       to discover the JWKS endpoint for token validation.

--oidc-client-id       Must match the client ID configured in Keycloak/Dex.

--oidc-username-claim  Which JWT claim to use as the Kubernetes username.
                       "preferred_username" maps to the AD sAMAccountName.

--oidc-username-prefix  Prefix added to all OIDC usernames to avoid
                       collisions with other auth methods. "oidc:" means
                       AD user "jsmith" becomes "oidc:jsmith" in RBAC.

--oidc-groups-claim    Which JWT claim contains group memberships.
                       Must match the claim name configured in Keycloak/Dex.

--oidc-groups-prefix   Prefix for OIDC groups. "oidc:" means AD group
                       "k8s-admins" becomes "oidc:k8s-admins" in RBAC.
```

---

## RBAC Mapping to Corporate Groups

The real power of OIDC is mapping existing AD groups directly to Kubernetes RBAC:

### Active Directory Group Structure

```
OU=K8s Groups,DC=corp,DC=internal
├── CN=k8s-cluster-admins       --> cluster-admin ClusterRole
├── CN=k8s-platform-team        --> platform-admin ClusterRole (custom)
├── CN=k8s-dev-frontend          --> edit Role in frontend-* namespaces
├── CN=k8s-dev-backend           --> edit Role in backend-* namespaces
├── CN=k8s-dev-data              --> edit Role in data-* namespaces
├── CN=k8s-sre                   --> view ClusterRole + debug permissions
└── CN=k8s-readonly              --> view ClusterRole (all namespaces)
```

### RBAC Bindings

```yaml
# cluster-admins -- full cluster access
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: oidc-cluster-admins
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: Group
  name: "oidc:k8s-cluster-admins"
  apiGroup: rbac.authorization.k8s.io

---
# Frontend developers -- edit access to frontend namespaces only
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: oidc-frontend-devs
  namespace: frontend-app
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: edit
subjects:
- kind: Group
  name: "oidc:k8s-dev-frontend"
  apiGroup: rbac.authorization.k8s.io

---
# Read-only access for all authenticated users (optional)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: oidc-readonly
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
subjects:
- kind: Group
  name: "oidc:k8s-readonly"
  apiGroup: rbac.authorization.k8s.io

---
# SRE team -- custom ClusterRole with view + debug permissions
# (pods/exec, pods/log, pods/portforward, nodes, events)
# Bound to group "oidc:k8s-sre" via ClusterRoleBinding
```

---

## Configuring kubectl for OIDC Login

Developers need a way to authenticate via OIDC from the command line. The `kubelogin` plugin handles this:

```bash
# Install kubelogin (kubectl oidc-login plugin)
kubectl krew install oidc-login

# Configure kubeconfig for OIDC authentication
kubectl config set-credentials oidc-user \
  --exec-api-version=client.authentication.k8s.io/v1beta1 \
  --exec-command=kubectl \
  --exec-arg=oidc-login \
  --exec-arg=get-token \
  --exec-arg=--oidc-issuer-url=https://keycloak.internal.corp/realms/kubernetes \
  --exec-arg=--oidc-client-id=kubernetes \
  --exec-arg=--oidc-extra-scope=groups

# Set context to use OIDC user
kubectl config set-context oidc-context \
  --cluster=on-prem-cluster \
  --user=oidc-user
kubectl config use-context oidc-context

# First kubectl command triggers browser login
kubectl get pods -n frontend-app
# Browser opens -> AD login page -> redirect back -> token cached
```

---

## SSO for Kubernetes Dashboard and Tools

Once OIDC is configured, extend SSO to other Kubernetes tools:

### OAuth2 Proxy for Web UIs

For tools without native OIDC support, deploy `oauth2-proxy` as a reverse proxy that handles authentication. Deploy it in the same namespace as the target tool, configure it with the OIDC issuer URL and client credentials, and point it upstream to the tool's service. It intercepts unauthenticated requests, redirects to Keycloak for login, and passes the validated token through to the backend.

```bash
# Key oauth2-proxy flags for Kubernetes Dashboard:
# --provider=oidc
# --oidc-issuer-url=https://keycloak.internal.corp/realms/kubernetes
# --upstream=http://kubernetes-dashboard.kubernetes-dashboard.svc:443
# --pass-access-token=true  (forward token to backend)
# --scope=openid profile email groups
```

### Tools That Support OIDC Natively

| Tool | OIDC Support | Configuration |
|------|-------------|---------------|
| Kubernetes Dashboard | Via oauth2-proxy | See above |
| Grafana | Native OIDC | `auth.generic_oauth` in grafana.ini |
| ArgoCD | Native OIDC/Dex | Built-in Dex or external OIDC |
| Harbor | Native OIDC | Admin > Configuration > Authentication |
| Vault | Native OIDC | `vault auth enable oidc` |
| Gitea | Native OAuth2 | Admin > Authentication Sources |

---

## Did You Know?

- **Kubernetes has no built-in user database.** The API server trusts external identity providers entirely. There is no `kubectl create user` command. Users exist only in the identity provider (AD, LDAP, OIDC) and are referenced in RBAC bindings by name or group.

- **OIDC tokens are validated locally by the API server.** After fetching the JWKS (public keys) from the OIDC provider, the API server validates JWT signatures without contacting the provider for each request. This means OIDC authentication works even if the OIDC provider has a brief outage (tokens already issued remain valid until expiry).

- **The `oidc-groups-prefix` flag was added in Kubernetes 1.11** to prevent privilege escalation. Without it, an AD group named "system:masters" would grant cluster-admin access. The prefix ensures OIDC groups cannot collide with Kubernetes system groups.

- **Active Directory's LDAP implementation has quirks** that trip up every integration. The `memberOf` attribute is a "constructed attribute" that does not appear in search results unless explicitly requested. AD also uses `sAMAccountName` (case-insensitive, max 20 chars) instead of standard LDAP `uid`.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No OIDC username prefix | OIDC user "admin" collides with built-in admin | Always set `--oidc-username-prefix` (e.g., "oidc:") |
| No OIDC groups prefix | AD group could match "system:masters" | Always set `--oidc-groups-prefix` |
| Long-lived OIDC tokens | Terminated employee retains access until token expires | Set token lifetime to 15-60 minutes in Keycloak |
| LDAP bind account with write access | Compromised Keycloak/Dex could modify AD | Use a read-only service account for LDAP bind |
| Not testing group sync | Users authenticate but have no permissions | Verify group claims in JWT: `kubectl oidc-login get-token --oidc-issuer-url=... | jq -R 'split(".") | .[1] | @base64d | fromjson | .groups'` |
| Skipping MFA for cluster-admin | Single factor for highest privilege access | Require MFA in Keycloak for k8s-cluster-admins group |
| Hardcoded service account tokens for CI/CD | CI/CD uses human auth flow | Use Kubernetes service accounts with bound tokens for CI/CD |
| Single OIDC provider, no failover | Keycloak outage = nobody can authenticate | Deploy Keycloak HA (2+ replicas) with shared PostgreSQL |

---

## Quiz

### Question 1
A developer reports that `kubectl get pods` returns "Forbidden" even though they are in the correct AD group. How do you troubleshoot?

<details>
<summary>Answer</summary>

**Systematic troubleshooting steps:**

1. **Verify the JWT token contains the expected groups claim:**
   ```bash
   kubectl oidc-login get-token \
     --oidc-issuer-url=https://keycloak.internal.corp/realms/kubernetes \
     --oidc-client-id=kubernetes \
     | jq -R 'split(".") | .[1] | @base64d | fromjson'
   ```
   Check that the `groups` field contains the expected group name.

2. **Check the group name matches exactly (including prefix).** If `--oidc-groups-prefix=oidc:` is set, the RoleBinding must reference `oidc:k8s-dev-frontend`, not `k8s-dev-frontend`.

3. **Verify the RoleBinding exists in the correct namespace:**
   ```bash
   kubectl get rolebindings -n frontend-app -o yaml
   ```

4. **Check if Keycloak group sync has run.** If the user was just added to the AD group, Keycloak may not have synced yet (default: every 60 seconds for changed sync).

5. **Verify the API server OIDC flags** are correct -- especially `--oidc-groups-claim` must match the claim name in the JWT (e.g., "groups").

6. **Use `kubectl auth can-i` with impersonation to test:**
   ```bash
   kubectl auth can-i get pods -n frontend-app \
     --as=oidc:jsmith --as-group=oidc:k8s-dev-frontend
   ```

Most common cause: the group name in the RoleBinding does not match the claim value (case sensitivity, missing prefix, or wrong claim name).
</details>

### Question 2
Why should you use Keycloak or Dex instead of configuring the API server to query LDAP directly?

<details>
<summary>Answer</summary>

**Kubernetes does not support LDAP authentication natively.** The API server only supports these authentication methods: x509 certificates, bearer tokens, OIDC, and webhook token authentication. There is no `--ldap-url` flag.

**Keycloak/Dex serve as the translation layer** between LDAP/AD and OIDC:

1. **Protocol translation**: AD speaks LDAP. Kubernetes speaks OIDC. Keycloak/Dex bridge the gap.

2. **Token management**: LDAP has no concept of short-lived tokens. OIDC provides JWTs with expiry, refresh tokens, and scopes. Keycloak creates and manages these tokens.

3. **Group claims**: LDAP group membership must be queried with a separate LDAP search. OIDC embeds group memberships directly in the JWT, so the API server does not need to query anything at authentication time.

4. **MFA**: LDAP provides only username/password. Keycloak adds MFA (TOTP, WebAuthn, SMS) on top of LDAP authentication.

5. **Centralization**: Multiple clusters can share a single Keycloak/Dex instance. Each cluster only needs the OIDC issuer URL -- no LDAP connection details on every API server.

6. **Security**: LDAP credentials would need to be stored on every control plane node. With OIDC, only the public signing key (JWKS) is needed on the API server -- no secrets.
</details>

### Question 3
You have 5 Kubernetes clusters. How do you manage RBAC consistently across all of them using AD groups?

<details>
<summary>Answer</summary>

**Use a single OIDC provider (Keycloak) with GitOps-managed RBAC:**

1. **Single Keycloak instance** (HA) serves all 5 clusters. Each cluster's API server points to the same `--oidc-issuer-url`.

2. **Consistent AD group naming** convention: `k8s-{cluster}-{role}` for cluster-specific access (e.g., `k8s-prod-admin`), `k8s-all-{role}` for cross-cluster access (e.g., `k8s-all-readonly`).

3. **RBAC manifests in Git** managed by Flux/ArgoCD with Kustomize overlays: a `base/` directory for cross-cluster bindings and per-cluster overlays for cluster-specific admin/dev roles.

4. **Automate group creation** in AD using a script that reads the cluster inventory. When a new cluster is added, create `k8s-{newcluster}-admin`, `k8s-{newcluster}-dev`, etc.

5. **Audit**: Periodically compare AD group memberships against RBAC bindings to detect drift.
</details>

### Question 4
What happens to existing kubectl sessions when an employee is terminated and their AD account is disabled?

<details>
<summary>Answer</summary>

**The answer depends on the OIDC token lifetime:**

1. **Active sessions with valid tokens continue working** until the token expires. If the token lifetime is 60 minutes, the terminated employee could have up to 60 minutes of continued access.

2. **When the token expires**, kubectl attempts to refresh it. The refresh token is sent to Keycloak, which queries AD. AD returns "account disabled." Keycloak refuses to issue a new token. kubectl shows an authentication error.

3. **Mitigation strategies:**

   - **Short token lifetime (15 min)**: Reduces the window of exposure but increases authentication frequency for all users.

   - **Revocation endpoint**: Keycloak supports token revocation, but the Kubernetes API server does not check revocation lists (it validates tokens locally using JWKS). This means Keycloak revocation only affects token refresh, not already-issued tokens.

   - **Webhook token authentication**: For immediate revocation, use a webhook authenticator instead of or alongside OIDC. The webhook checks token validity with the IdP on every request. This adds latency but enables instant revocation.

   - **Network-level**: Revoke the employee's VPN access. If they cannot reach the API server, the token is useless.

**Practical recommendation**: 15-30 minute token lifetime combined with VPN revocation as part of the HR offboarding process.
</details>

---

## Hands-On Exercise: Configure OIDC Authentication with Dex

**Task**: Set up Dex as an OIDC provider for a local Kubernetes cluster using a static user (simulating AD).

### Steps

1. **Create a kind cluster with OIDC flags** -- configure `kube-apiserver` with `--oidc-issuer-url`, `--oidc-client-id=kubernetes`, `--oidc-username-claim=email`, `--oidc-groups-claim=groups`, and both prefix flags set to `oidc:`.

2. **Deploy Dex with a static user** (simulates AD) -- configure a `staticPasswords` entry for `jane@corp.internal` and a `staticClients` entry for the `kubernetes` client ID.

3. **Create RBAC binding for the static user**:
   ```bash
   kubectl create clusterrolebinding oidc-jane-admin \
     --clusterrole=view \
     --user="oidc:jane@corp.internal"
   ```

4. **Test with kubelogin**:
   ```bash
   kubectl oidc-login get-token \
     --oidc-issuer-url=https://dex.identity.svc:5556 \
     --oidc-client-id=kubernetes
   ```

### Success Criteria
- [ ] Kind cluster created with OIDC API server flags
- [ ] Dex deployed and accessible
- [ ] Static user can obtain a JWT token
- [ ] RBAC binding grants correct permissions to the OIDC user
- [ ] `kubectl auth can-i` confirms permissions match expectations

---

## Key Takeaways

1. **OIDC is the only viable authentication for enterprise Kubernetes** -- x509 certificates cannot be revoked and static tokens are a security anti-pattern
2. **Keycloak for full enterprise SSO**, Dex for lightweight Kubernetes-only OIDC
3. **Map AD groups to RBAC** and let HR manage Kubernetes access through existing processes
4. **Always use username and group prefixes** to prevent privilege escalation via name collision
5. **Short token lifetimes** (15-30 min) limit the window when a terminated employee retains access

---

## Next Module

Continue to [Module 6.4: Compliance for Regulated Industries](../module-6.4-compliance/) to learn how to map regulatory frameworks like HIPAA, SOC 2, and PCI DSS to your on-premises Kubernetes infrastructure.
