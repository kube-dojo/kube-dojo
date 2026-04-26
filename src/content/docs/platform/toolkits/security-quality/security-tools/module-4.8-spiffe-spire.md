---
title: "Module 4.8: SPIFFE/SPIRE - Cryptographic Workload Identity"
slug: platform/toolkits/security-quality/security-tools/module-4.8-spiffe-spire
sidebar:
  order: 9
---

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~60 minutes
>
> **Prerequisites**: [Security Principles Foundations](/platform/foundations/security-principles/), Kubernetes ServiceAccounts and RBAC, TLS and mTLS fundamentals, and basic Helm usage.
>
> **Environment Assumption**: Kubernetes 1.35+, `kubectl`, `helm`, `kind`, `jq`, and `openssl` are available on your workstation.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a SPIFFE identity scheme that separates trust domains, workload paths, and authorization decisions for Kubernetes services.
- **Configure** SPIRE registration entries that bind Kubernetes selectors to short-lived X.509-SVIDs without relying on shared secrets.
- **Debug** failed workload identity issuance by tracing the path from pod metadata through the SPIRE Agent, SPIRE Server, and Workload API socket.
- **Evaluate** when SPIFFE/SPIRE is a better fit than ServiceAccount tokens, cert-manager, or service mesh identity for a platform security requirement.
- **Implement** a basic SPIRE lab where two workloads receive distinct cryptographic identities and use those identities as the basis for mTLS authorization.

---

## Why This Module Matters

At 2 AM, a platform team discovered that a forgotten debug pod in a staging namespace had become the first step in a lateral movement incident. The pod used the same ServiceAccount as a legitimate internal tool, and several internal APIs accepted any valid in-cluster token as proof that the caller was allowed. The attacker did not need to break TLS, steal a database password, or exploit the Kubernetes API server. They only needed one weakly governed workload identity and a network path to services that treated "inside the cluster" as a security boundary.

The post-incident review exposed a subtle but common platform failure. Kubernetes ServiceAccount tokens identified a Kubernetes subject, but they did not prove that a specific workload process was the intended caller of a specific service. Certificates existed in the environment too, but they were issued manually, rotated inconsistently, and tied to DNS names instead of workload intent. The team could encrypt traffic, but it could not confidently answer the more important question: "Which workload is this, and should this workload be allowed to make this request?"

SPIFFE and SPIRE solve that problem by making workload identity cryptographic, short-lived, and automatically issued after attestation. SPIFFE defines the identity standard, including SPIFFE IDs and SVIDs. SPIRE implements the runtime system that attests nodes and workloads, issues identities, rotates credentials, and exposes them through a local Workload API. The result is not just "TLS with nicer certificates." It is a platform primitive that lets services authorize based on workload identity rather than network location, static secrets, or overloaded Kubernetes ServiceAccounts.

This module teaches SPIFFE/SPIRE as a practical platform engineering tool, not as a glossary of identity terms. You will start with the identity model, then build the architecture, register workloads, inspect issued certificates, reason through mTLS authorization, and debug common failure modes. By the end, you should be able to decide whether SPIRE belongs in an environment, describe the operational cost it introduces, and explain how it changes the blast radius of a compromised workload.

---

## Core Content

---

## 1. The Identity Problem SPIFFE Solves

Modern platforms have many ways to authenticate a caller, but they often identify the wrong thing. A Kubernetes ServiceAccount token identifies a ServiceAccount assigned to a pod. A TLS certificate often identifies a DNS name. A cloud IAM role may identify a VM, node, or federated subject. Those are useful signals, yet they are not always the same as "this exact workload is the intended payment API, running under this platform policy, and allowed to call the order service."

SPIFFE narrows the problem to workload identity. A workload is a running piece of software such as a Kubernetes pod, VM process, batch job, or service instance. Instead of assuming a workload is trustworthy because it came from an internal network, SPIFFE gives it a verifiable identity document. A peer service can then authenticate the identity and make an authorization decision based on that identity.

The SPIFFE identity model has four core pieces. The SPIFFE ID names the workload. The SVID proves that identity cryptographically. The trust domain defines who is allowed to issue those identities. The Workload API gives a workload a local, secretless way to obtain its identity. When these pieces fit together, developers do not distribute private keys, platform teams do not hand-write certificate renewal scripts, and services do not need to trust every pod in a namespace equally.

A SPIFFE ID is a URI with a trust domain and path. The trust domain is the authority that issues and signs identities, while the path is an operator-defined naming scheme for workloads. In Kubernetes, a common path includes namespace and ServiceAccount because those attributes are stable, meaningful, and already governed by platform policy.

```text
SPIFFE ID SHAPE
══════════════════════════════════════════════════════════════════════

  spiffe://trust-domain/path

  Example trust domain:
  spiffe://example.org

  Example Kubernetes workload identities:
  spiffe://example.org/ns/payments/sa/api-server
  spiffe://example.org/ns/orders/sa/order-service
  spiffe://example.org/ns/reporting/sa/exporter

  Example non-Kubernetes workload identity:
  spiffe://example.org/vm/region-eu-central-1/role/batch-worker
```

The path is flexible, but flexibility is not a license to invent a confusing taxonomy. A good identity path is stable enough for policy, specific enough for authorization, and boring enough that responders can understand it during an incident. Names that encode deployment hashes or pod names usually churn too much. Names that stop at the namespace usually collapse too many workloads into one identity.

> **Pause and predict:** If every workload in the `payments` namespace receives `spiffe://example.org/ns/payments`, what happens when only the `payment-api` should be allowed to call the card vault but a batch export job runs in the same namespace? Write down the authorization rule you would have to create, then compare it with a rule that uses separate ServiceAccount-level identities.

An SVID, or SPIFFE Verifiable Identity Document, is the cryptographic proof that a workload owns a SPIFFE ID. SPIFFE supports two major SVID forms. X.509-SVIDs are certificates with the SPIFFE ID encoded as a URI Subject Alternative Name, and they are the natural fit for mTLS. JWT-SVIDs are signed tokens with the SPIFFE ID as the subject, and they are useful for request-level authentication when TLS is terminated by an intermediary or when a downstream service expects bearer-token style verification.

| SVID Type | Format | Strong Fit | Watch Out For |
|---|---|---|---|
| X.509-SVID | X.509 certificate with SPIFFE ID in URI SAN | mTLS, long-running service connections, sidecarless service identity | The application or proxy must use the trust bundle and verify allowed SPIFFE IDs, not only certificate validity. |
| JWT-SVID | Signed JWT with SPIFFE ID as subject | HTTP APIs, identity propagation through selected gateways, token exchange patterns | JWTs authenticate a request but do not create mutual TLS by themselves. |
| Trust Bundle | CA certificates for one or more trust domains | Verifying peer SVIDs and supporting federation | Bundles rotate, so applications should consume them dynamically rather than baking files into images. |

The trust domain is the administrative root of identity. A SPIRE Server or SPIRE Server cluster signs identities for a trust domain, and workloads trust identities from that domain by trusting its bundle. Federation allows one trust domain to trust another, but that trust must be explicit. This distinction matters because multi-cluster identity can be designed as one shared trust domain, separate trust domains with federation, or separate domains with no runtime trust between them.

The Workload API is the mechanism that keeps private keys out of deployment manifests. A workload connects to a Unix domain socket exposed by the SPIRE Agent on the same node. The workload does not pass a password. Instead, the Agent inspects local process and container metadata, checks whether that caller matches a registration entry, and returns the correct SVID and trust bundle. This is why SPIRE is more than a certificate issuer: the local attestation path is part of the security model.

```text
SPIFFE IDENTITY MODEL
══════════════════════════════════════════════════════════════════════

  Trust Domain: example.org
  ┌────────────────────────────────────────────────────────────────┐
  │                                                                │
  │  Workload A                         Workload B                 │
  │  ┌─────────────────────────┐        ┌─────────────────────────┐ │
  │  │ SPIFFE ID               │        │ SPIFFE ID               │ │
  │  │ spiffe://example.org    │        │ spiffe://example.org    │ │
  │  │ /ns/payments/sa/api     │        │ /ns/orders/sa/service   │ │
  │  │                         │        │                         │ │
  │  │ X.509-SVID              │ mTLS   │ X.509-SVID              │ │
  │  │ ┌─────────────────────┐ │◄──────►│ ┌─────────────────────┐ │ │
  │  │ │ Cert with URI SAN   │ │        │ │ Cert with URI SAN   │ │ │
  │  │ │ Private key         │ │        │ │ Private key         │ │ │
  │  │ │ Trust bundle        │ │        │ │ Trust bundle        │ │ │
  │  │ └─────────────────────┘ │        │ └─────────────────────┘ │ │
  │  └─────────────▲───────────┘        └─────────────▲───────────┘ │
  │                │ Workload API socket              │             │
  │                │                                  │             │
  │  ┌─────────────┴──────────────────────────────────┴───────────┐ │
  │  │ SPIRE Agent on the node                                    │ │
  │  │ - Attests workload process and container metadata           │ │
  │  │ - Matches metadata against registration selectors           │ │
  │  │ - Caches and rotates issued SVIDs                           │ │
  │  └─────────────────────────────▲──────────────────────────────┘ │
  │                                │                                │
  │  ┌─────────────────────────────┴──────────────────────────────┐ │
  │  │ SPIRE Server                                                │ │
  │  │ - Signs SVIDs for the trust domain                          │ │
  │  │ - Stores registration entries                               │ │
  │  │ - Attests Agents before issuing workload identities          │ │
  │  │ - Publishes trust bundles                                   │ │
  │  └────────────────────────────────────────────────────────────┘ │
  └────────────────────────────────────────────────────────────────┘
```

Notice the direction of trust in this model. The workload does not tell SPIRE "I am the payment API, please believe me." The Agent observes the caller and asks whether the observed attributes match an entry that the platform team registered. That difference is what allows SPIRE to reduce reliance on developer-managed secrets.

---

## 2. SPIRE Architecture from First Request to Issued Identity

SPIRE has two main runtime components: the Server and the Agent. The Server is the signing and policy authority for a trust domain. The Agent runs close to workloads, normally as a DaemonSet on Kubernetes nodes, and handles local attestation. The separation matters because the Server should remain protected and highly available, while the Agent must be present wherever workloads need identities.

The SPIRE Server stores registration entries, signs SVIDs, manages bundles, and authenticates Agents through node attestation. In Kubernetes, node attestation commonly uses projected ServiceAccount tokens so the Server can verify that an Agent belongs to the expected cluster and ServiceAccount. Once attested, the Agent gets its own identity and can request workload SVIDs on behalf of processes running on its node.

The SPIRE Agent exposes the Workload API as a Unix domain socket. When a workload connects, the Agent determines which process owns that socket connection and derives selectors from the process, pod, namespace, ServiceAccount, labels, and container runtime metadata. The Agent then asks whether the selector set matches a registered entry. If there is a match, the Agent returns an SVID for the SPIFFE ID declared in that entry.

```text
REQUEST PATH FOR A WORKLOAD SVID
══════════════════════════════════════════════════════════════════════

  Workload container
  ┌──────────────────────────────────────────────────────────────┐
  │ Application or helper connects to local Workload API socket  │
  └─────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
  SPIRE Agent on same node
  ┌──────────────────────────────────────────────────────────────┐
  │ 1. Identify calling process from local socket metadata       │
  │ 2. Resolve Kubernetes pod, namespace, ServiceAccount, labels │
  │ 3. Build selector set such as k8s:ns and k8s:sa              │
  │ 4. Match selector set against registration entries           │
  │ 5. Return SVID and trust bundle when an entry matches        │
  └─────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
  SPIRE Server
  ┌──────────────────────────────────────────────────────────────┐
  │ 1. Confirms Agent identity and parent relationship           │
  │ 2. Signs short-lived SVID for the registered SPIFFE ID        │
  │ 3. Publishes current trust bundle to the Agent               │
  └──────────────────────────────────────────────────────────────┘
```

Registration entries are the heart of the system because they connect platform intent to runtime identity. An entry says that workloads matching a group of selectors should receive a specific SPIFFE ID under a specific parent identity. In Kubernetes, the parent identity is usually the Agent identity for a cluster or node attestation method. The selectors decide which pods are eligible.

| Selector Example | What It Matches | Good Use | Risk If Used Alone |
|---|---|---|---|
| `k8s:ns:payments` | Any workload in the `payments` namespace | Broad environment grouping or temporary diagnostics | Too broad for service-to-service authorization because unrelated workloads share identity. |
| `k8s:sa:api-server` | Pods using the `api-server` ServiceAccount | Stable service identity boundary | Reused ServiceAccounts can accidentally share identity across deployments. |
| `k8s:pod-label:app:api-server` | Pods with a specific label | Extra precision when labels are controlled by deployment policy | Mutable labels can drift if admission policy does not enforce them. |
| `k8s:container-name:app` | A specific container in a multi-container pod | Separating app and sidecar identities | Container names are useful but should not be the only security boundary. |

A strong registration entry uses selectors that are both stable and meaningful. Namespace plus ServiceAccount is a common baseline. Adding a controlled label can help distinguish services that share a namespace, while adding container name can help when a sidecar and application container need different identities. Adding every possible selector is not automatically better, because overly fragile selectors can break identity issuance during harmless deployment changes.

> **Pause and reason:** Your team uses one ServiceAccount named `default-app` for five deployments in the `orders` namespace. SPIRE registration uses `k8s:ns:orders` and `k8s:sa:default-app`. Which services can now obtain the same SVID, and what Kubernetes change would you make before tightening the SPIRE entry?

A useful mental model is that SPIRE authentication and application authorization are separate steps. SPIRE can prove that a caller is `spiffe://example.org/ns/payments/sa/api-server`. It does not automatically decide that this caller can invoke `POST /refunds` or read a card vault secret. Your services, proxies, authorization layer, or secret store must still check that the authenticated SPIFFE ID is allowed for the requested action.

This separation is a strength, not a weakness. It lets the platform team standardize identity issuance while each service or policy engine makes domain-specific authorization decisions. The mistake is treating a valid SVID as universal access. A valid SVID says "this workload is who it claims to be," not "this workload may do anything."

---

## 3. Deploying SPIRE on Kubernetes

A production SPIRE deployment deserves careful design, but a lab cluster is the best way to understand the moving pieces. The goal of the first deployment is to create a trust domain, run the SPIRE Server, run an Agent on each node, and expose the Workload API socket to selected pods through the SPIFFE CSI driver. Once those pieces are healthy, the rest of the module can focus on registration and verification.

The commands below use `kubectl` explicitly. Many platform teams alias `kubectl` to `k` for speed, but this module keeps the full command in the teaching path so the resource being controlled remains obvious. In your own shell, `alias k=kubectl` is fine after you understand what each command is doing.

```bash
kind create cluster --name spire-lab

kubectl cluster-info --context kind-spire-lab

helm repo add spire https://spiffe.github.io/helm-charts-hardened/
helm repo update

helm install spire spire/spire \
  --namespace spire-system \
  --create-namespace \
  --set global.spire.trustDomain=example.org \
  --set global.spire.clusterName=spire-lab \
  --wait \
  --timeout 300s
```

After installation, inspect the control plane before creating workloads. This is not busywork. SPIRE identity issuance depends on several components working together, and debugging is much easier when you know whether the Server, Agent, and CSI driver were healthy before you introduced your own manifests.

```bash
kubectl get pods -n spire-system -o wide

kubectl get daemonset,statefulset -n spire-system

kubectl exec -n spire-system spire-server-0 -- \
  spire-server healthcheck

kubectl exec -n spire-system spire-server-0 -- \
  spire-server agent list
```

A healthy lab should show one SPIRE Server pod, one or more SPIRE Agent pods, and CSI driver pods. The exact pod names vary by chart version and cluster shape, but the architectural rule is stable: every node that runs a workload needing a SPIFFE identity must have a healthy Agent and a way to expose the Workload API socket.

If the Agent list is empty, do not continue to workload registration. An empty Agent list means the Server has not attested any Agents, so workload SVID issuance cannot work. Check the Agent logs, the configured cluster name, the Server trust domain, and whether the Agent ServiceAccount is allowed to present the token expected by the node attestor.

```bash
kubectl logs -n spire-system statefulset/spire-server --tail=100

kubectl logs -n spire-system daemonset/spire-agent --tail=100
```

A lab can use the chart defaults, but production should not treat defaults as architecture. The Server datastore, upstream authority, bundle distribution, disaster recovery plan, and federation model all become operational decisions. The lab gives you the mechanics; the production design must answer what happens when a Server pod restarts, a signing key rotates, a cluster joins the platform, or a region loses connectivity.

---

## 4. Registering Workloads and Inspecting X.509-SVIDs

Registration is where a platform intent becomes a runtime identity. In this example, the payments API and order service receive separate SPIFFE IDs because they represent different authorization subjects. If both services shared an identity, downstream services would be unable to distinguish which workload made a request, and any policy based on that identity would be weaker.

First create the namespaces and ServiceAccounts. These Kubernetes objects are not SPIFFE identities by themselves. They are attributes that SPIRE can later observe and match through selectors.

```bash
kubectl create namespace payments
kubectl create serviceaccount api-server -n payments

kubectl create namespace orders
kubectl create serviceaccount order-service -n orders
```

Next retrieve the Agent parent identity. The parent ID ties workload entries to the attested Agent lineage. In a lab, there may be only one Agent identity to use. In larger environments, parent IDs and node selectors need more deliberate design so workloads are issued only through the intended attested infrastructure.

```bash
kubectl exec -n spire-system spire-server-0 -- \
  spire-server agent list -output json | jq .
```

For the lab, capture the first Agent path and use it to create two workload entries. If your chart emits a different JSON shape, inspect the output and adapt the `jq` filter rather than guessing. The important part is that `-parentID` must match an actual attested Agent identity in the `example.org` trust domain.

```bash
AGENT_PATH=$(kubectl exec -n spire-system spire-server-0 -- \
  spire-server agent list -output json | jq -r '.[0].id.path')

kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry create \
    -spiffeID spiffe://example.org/ns/payments/sa/api-server \
    -parentID spiffe://example.org${AGENT_PATH} \
    -selector k8s:ns:payments \
    -selector k8s:sa:api-server \
    -ttl 3600

kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry create \
    -spiffeID spiffe://example.org/ns/orders/sa/order-service \
    -parentID spiffe://example.org${AGENT_PATH} \
    -selector k8s:ns:orders \
    -selector k8s:sa:order-service \
    -ttl 3600

kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry show
```

Now deploy a workload that mounts the Workload API socket through the SPIFFE CSI driver. The application container in this lab sleeps so you can exec into it and fetch an SVID manually. In a real service, a SPIFFE-aware library or proxy would connect to the socket and keep credentials fresh without a human running a helper command.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: payments
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      serviceAccountName: api-server
      containers:
        - name: app
          image: ghcr.io/spiffe/spiffe-helper:latest
          command:
            - sleep
            - infinity
          volumeMounts:
            - name: spiffe-workload-api
              mountPath: /spiffe-workload-api
              readOnly: true
      volumes:
        - name: spiffe-workload-api
          csi:
            driver: csi.spiffe.io
            readOnly: true
```

Save that manifest as `payments-api.yaml`, then apply it and wait for readiness. If the pod does not become ready, debug the Kubernetes deployment first. SPIRE cannot issue identity to a workload that is not running on a node with a healthy Agent and mounted socket.

```bash
kubectl apply -f payments-api.yaml

kubectl wait --for=condition=ready pod \
  -l app=api-server \
  -n payments \
  --timeout=90s

kubectl describe pod -n payments -l app=api-server
```

Fetch the X.509-SVID from inside the workload. This command asks the local Agent through the mounted socket to issue the SVID associated with the process. The `-write /tmp/` flag writes certificate material for inspection in the lab; production applications should normally use SPIFFE libraries that keep credentials in memory and handle rotation.

```bash
kubectl exec -n payments deploy/api-server -- \
  /opt/spire/bin/spire-agent api fetch x509 \
    -socketPath /spiffe-workload-api/spire-agent.sock \
    -write /tmp/

kubectl exec -n payments deploy/api-server -- \
  openssl x509 -in /tmp/svid.0.pem -text -noout | sed -n '1,80p'
```

The certificate should include the SPIFFE ID in the Subject Alternative Name field. The exact certificate serial number and validity timestamps will differ in your cluster. The stable fact you care about is the URI SAN, because that is what a peer should authorize after validating the certificate chain against the trust bundle.

```text
EXPECTED CERTIFICATE FIELD
══════════════════════════════════════════════════════════════════════

  X509v3 Subject Alternative Name:
      URI:spiffe://example.org/ns/payments/sa/api-server

  What this proves:
      The workload matched the payments namespace and api-server ServiceAccount
      registration entry under the example.org trust domain.

  What this does not prove:
      The workload is allowed to call every service in the platform.
      Authorization still belongs in application, proxy, or policy logic.
```

> **Pause and predict:** Change the deployment to use `serviceAccountName: default`, then redeploy it without changing the registration entry. Before running the fetch command, predict whether the Workload API should return the same SVID, a different SVID, or no SVID. Explain which selector caused that result.

This worked example demonstrates the debug pattern you will reuse in production. First verify the pod metadata. Then verify the registration entry selectors. Then verify the Agent is present on the node. Then verify the socket is mounted. Finally inspect the SVID and compare its SPIFFE ID against the identity your policy expected.

```bash
kubectl get pod -n payments -l app=api-server \
  -o jsonpath='{.items[0].spec.serviceAccountName}{"\n"}'

kubectl get pod -n payments -l app=api-server \
  -o jsonpath='{.items[0].metadata.labels}{"\n"}'

kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry show \
    -selector k8s:ns:payments \
    -selector k8s:sa:api-server

kubectl get pod -n payments -l app=api-server -o wide

kubectl get pod -n spire-system -l app.kubernetes.io/name=spire-agent -o wide
```

The most common lab failure is a selector mismatch. The pod runs, the socket is mounted, and the Agent is healthy, but the workload does not match any registration entry. This is a useful failure because it proves the Agent is not blindly issuing identity to every process that can reach the socket. Denial by default is the behavior you want from workload identity infrastructure.

---

## 5. Using SPIFFE Identities for mTLS and Authorization

SPIFFE becomes powerful when two workloads authenticate each other without exchanging static credentials. During an mTLS handshake, each workload presents an X.509-SVID. Each side validates the peer certificate chain against the trust bundle, extracts the SPIFFE ID from the URI SAN, and checks whether that SPIFFE ID is allowed for the requested role or route. Encryption is only part of the value; peer identity and authorization are the platform security payoff.

```text
ZERO-CONFIG mTLS FLOW WITH EXPLICIT AUTHORIZATION
══════════════════════════════════════════════════════════════════════

  Payment API                                      Order Service
  ┌──────────────────────────────┐                ┌──────────────────────────────┐
  │ Fetch own X.509-SVID         │                │ Fetch own X.509-SVID         │
  │ from local Workload API      │                │ from local Workload API      │
  └──────────────┬───────────────┘                └──────────────┬───────────────┘
                 │                                               │
                 ▼                                               ▼
  ┌──────────────────────────────┐    TLS handshake              ┌──────────────────────────────┐
  │ Present certificate with     │───────────────────────────────►│ Present certificate with     │
  │ URI SAN spiffe://example...  │◄───────────────────────────────│ URI SAN spiffe://example...  │
  └──────────────┬───────────────┘                                └──────────────┬───────────────┘
                 │                                               │
                 ▼                                               ▼
  ┌──────────────────────────────┐                ┌──────────────────────────────┐
  │ Verify peer chain against    │                │ Verify peer chain against    │
  │ current trust bundle         │                │ current trust bundle         │
  └──────────────┬───────────────┘                └──────────────┬───────────────┘
                 │                                               │
                 ▼                                               ▼
  ┌──────────────────────────────┐                ┌──────────────────────────────┐
  │ Authorize allowed SPIFFE ID  │                │ Authorize allowed SPIFFE ID  │
  │ for this route or operation  │                │ for this route or operation  │
  └──────────────────────────────┘                └──────────────────────────────┘
```

The authorization step is where senior platform design shows up. If a server only checks that the certificate chains to the trust bundle, any valid workload in the trust domain may connect. That may still be better than unauthenticated plaintext, but it is not least privilege. A safer service checks both certificate validity and expected peer identity.

The following Go example shows the shape of a SPIFFE-aware mTLS server. It creates an X.509 source from the Workload API socket, uses that source for the server certificate and trust bundle, and authorizes exactly one expected client identity. The code is intentionally small because the point of SPIFFE is to move certificate issuance and rotation out of application business logic.

```go
package main

import (
	"context"
	"log"
	"net/http"

	"github.com/spiffe/go-spiffe/v2/spiffeid"
	"github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig"
	"github.com/spiffe/go-spiffe/v2/workloadapi"
)

func main() {
	ctx := context.Background()

	source, err := workloadapi.NewX509Source(ctx,
		workloadapi.WithClientOptions(
			workloadapi.WithAddr("unix:///spiffe-workload-api/spire-agent.sock"),
		),
	)
	if err != nil {
		log.Fatalf("create x509 source: %v", err)
	}
	defer source.Close()

	clientID := spiffeid.RequireFromString(
		"spiffe://example.org/ns/payments/sa/api-server",
	)

	tlsConfig := tlsconfig.MTLSServerConfig(
		source,
		source,
		tlsconfig.AuthorizeID(clientID),
	)

	mux := http.NewServeMux()
	mux.HandleFunc("/orders", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("authorized\n"))
	})

	server := &http.Server{
		Addr:      ":8443",
		Handler:   mux,
		TLSConfig: tlsConfig,
	}

	log.Fatal(server.ListenAndServeTLS("", ""))
}
```

This example does not name a certificate file or CA file. The source receives the SVID and bundle from SPIRE, and the TLS configuration uses the allowed SPIFFE ID as the authorization rule. Rotation is handled underneath the application because the source updates as SPIRE rotates credentials.

For services that cannot use SPIFFE libraries directly, a service mesh or sidecar proxy may terminate mTLS and enforce identity-based policy. This can be a good migration path because it avoids changing application code. The trade-off is that the proxy becomes part of the trust and authorization path, so platform teams must govern sidecar injection, policy distribution, and the handoff between proxy-authenticated identity and application-level decisions.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: allowed-spiffe-clients
  namespace: orders
data:
  clients.yaml: |
    allowedClients:
      - spiffe://example.org/ns/payments/sa/api-server
    deniedByDefault: true
```

The ConfigMap above is not a complete policy engine, but it illustrates a key design habit. Treat SPIFFE IDs as inputs to explicit policy. Do not let "valid certificate from our trust domain" silently become "allowed to use this service." The smallest secure rule is usually a pair: authenticated identity plus intended action.

---

## 6. Choosing SPIFFE/SPIRE Among Other Identity Tools

SPIFFE/SPIRE overlaps with several tools learners may already know, so the comparison must be precise. Kubernetes ServiceAccount tokens are excellent for authenticating to the Kubernetes API and for some in-cluster token-based patterns. cert-manager is excellent for certificate lifecycle automation. Service meshes are excellent for traffic management, mTLS, telemetry, and policy at the proxy layer. SPIFFE/SPIRE focuses on portable workload identity and attested credential issuance.

| Feature | Kubernetes ServiceAccount Tokens | SPIFFE/SPIRE | Service Mesh Identity | cert-manager |
|---|---|---|---|---|
| Primary identity object | JWT bound to a Kubernetes ServiceAccount | SPIFFE ID proven by X.509-SVID or JWT-SVID | Usually SPIFFE-like service identity presented by sidecar proxy | X.509 certificate requested by Kubernetes resources |
| Best scope | Kubernetes API authentication and selected in-cluster token flows | Multi-cluster, VM, bare metal, service-to-service identity | Mesh-managed service-to-service traffic | Certificate issuance and renewal workflows |
| mTLS support | Not by itself | Native through X.509-SVIDs and SPIFFE libraries | Native through sidecars or ambient mesh components | Possible, but applications must consume certs and trust bundles correctly |
| Workload attestation | Kubernetes admission and token projection, not process-level attestation | Agent observes local workload metadata and matches selectors | Proxy attachment and mesh control plane identity | Request approval policy depends on issuer and certificate request controls |
| Non-Kubernetes support | Limited | Strong design goal | Possible but mesh-specific | Possible for certificates, less focused on workload attestation |
| Operational cost | Low if already using Kubernetes defaults | Medium to high because identity infrastructure must be operated carefully | Medium to high because the mesh becomes runtime infrastructure | Medium because issuers, renewals, and consumers need governance |
| When it fits | Workloads need to call the Kubernetes API | Workloads need portable cryptographic identity and least-privilege peer auth | Platform already standardizes service-to-service traffic through a mesh | Teams need certificate automation but not a full workload identity system |

A practical decision starts with the resource being protected. If a pod needs to call the Kubernetes API, a bounded ServiceAccount token is usually the right primitive. If two services need to mutually authenticate and authorize each other across clusters or runtimes, SPIFFE is a stronger fit. If the organization already runs a service mesh and wants identity enforced without application changes, the mesh identity layer may be enough, and SPIRE may still serve as a pluggable authority behind it.

The senior-level question is not "which tool is best?" but "which identity claim is authoritative for this decision?" A DNS certificate can prove control of a name, but it may not prove the workload's deployment intent. A ServiceAccount token can prove Kubernetes assigned a ServiceAccount, but it may not separate multiple services sharing that account. A SPIFFE ID can prove an attested workload identity, but only if selectors and trust domains were designed carefully.

```text
DECISION PATH FOR WORKLOAD IDENTITY
══════════════════════════════════════════════════════════════════════

  Need to call Kubernetes API?
      │
      ├── Yes ──► Use scoped Kubernetes ServiceAccount tokens first.
      │
      └── No
          │
          ▼
  Need service-to-service mTLS with workload-level authorization?
      │
      ├── Yes ──► Consider SPIFFE/SPIRE or a mesh using SPIFFE identities.
      │
      └── No
          │
          ▼
  Need certificate issuance for ingress, DNS names, or app-owned certs?
      │
      ├── Yes ──► Consider cert-manager and issuer policy.
      │
      └── No
          │
          ▼
  Need portable identity across Kubernetes, VMs, and other runtimes?
      │
      ├── Yes ──► SPIFFE/SPIRE is usually the strongest candidate.
      │
      └── No ───► Keep the simpler native identity primitive and revisit later.
```

SPIRE also changes incident response. With stable workload identities, logs can show that `spiffe://example.org/ns/payments/sa/api-server` called the order service, rather than merely showing a pod IP, node IP, or namespace. That improves forensics only when services log authenticated peer identity and when teams can map SPIFFE paths back to owners. Identity without observability becomes another hidden control plane.

Federation deserves special caution. It is tempting to use one giant trust domain for every cluster because it feels simpler, but this can make blast radius and ownership unclear. Separate trust domains with explicit federation often map better to organizational boundaries, environments, or regions. The cost is that bundle distribution and cross-domain policy become more deliberate.

```text
TRUST DOMAIN OPTIONS
══════════════════════════════════════════════════════════════════════

  Option A: One shared trust domain
  ┌──────────────────────────────────────────────────────────────┐
  │ example.org                                                   │
  │ ├── cluster-a workloads                                       │
  │ ├── cluster-b workloads                                       │
  │ └── vm workloads                                              │
  └──────────────────────────────────────────────────────────────┘

  Useful when:
      One platform team owns the full identity lifecycle.

  Dangerous when:
      Environment, region, or business-unit boundaries need separate roots.

  Option B: Federated trust domains
  ┌──────────────────────────────┐       ┌──────────────────────────────┐
  │ prod.example.org             │◄─────►│ shared-services.example.org   │
  │ production workloads         │       │ platform services             │
  └──────────────────────────────┘       └──────────────────────────────┘

  Useful when:
      Each domain keeps its own root but selected identities need trust.

  Dangerous when:
      Federation is added broadly without explicit authorization policy.
```

A production rollout should therefore begin with naming and policy design, not with Helm installation. Decide the trust domain boundaries, path conventions, selector standards, ownership model, SVID TTLs, upstream authority, and federation requirements first. Then deploy SPIRE to implement those decisions. Installing SPIRE before designing identity is like deploying RBAC before deciding who should have access.

---

## Did You Know?

- **SPIFFE separates naming from implementation**: The SPIFFE standard defines workload identity concepts, while SPIRE is one implementation that issues and rotates SVIDs for those identities.
- **X.509-SVIDs use URI SANs**: A peer should verify the certificate chain and then authorize the SPIFFE ID from the URI Subject Alternative Name, not rely on a common name.
- **The Workload API is intentionally local**: Workloads receive identity through a Unix domain socket exposed by the node-local Agent, which lets the Agent inspect local process metadata.
- **SPIRE can support heterogeneous platforms**: The same identity model can cover Kubernetes pods, VMs, and other runtimes when appropriate node and workload attestors are configured.

---

## Common Mistakes

| Mistake | What Goes Wrong | Better Practice |
|---|---|---|
| Giving every pod in a namespace the same SPIFFE ID | Peer services cannot distinguish unrelated workloads, so authorization rules become too broad. | Use at least namespace plus ServiceAccount, and add governed labels or container selectors when they represent real service boundaries. |
| Treating any valid SVID as authorization | Every workload in the trust domain may be accepted even when only one caller should use the API. | Validate the certificate chain, extract the SPIFFE ID, and check it against route-specific or action-specific policy. |
| Reusing ServiceAccounts across many deployments | SPIRE selectors based on ServiceAccount collapse multiple services into the same identity. | Create ServiceAccounts per workload or per authorization subject before relying on ServiceAccount-based selectors. |
| Setting long SVID TTLs because rotation feels risky | A stolen credential remains useful longer, and teams avoid learning whether rotation really works. | Use short TTLs appropriate for the environment and verify libraries or proxies refresh credentials without restarts. |
| Debugging only the application logs | The app may report "no identity" while the real issue is Agent health, socket projection, parent ID, or selector mismatch. | Trace the full path: pod metadata, socket mount, Agent on node, Server health, Agent attestation, and registration entry selectors. |
| Hardcoding bundle and certificate files into images | Bundle rotation or trust-domain changes require image rebuilds and create stale trust material. | Consume SVIDs and bundles dynamically through SPIFFE libraries, the Workload API, or a managed proxy integration. |
| Designing federation as a shortcut for all clusters to trust all clusters | Compromise or misconfiguration in one domain can create surprising access in another domain. | Federate only where a real cross-domain call path exists, and still enforce explicit authorization on peer SPIFFE IDs. |
| Running the SPIRE Server as an unplanned single point of failure | Existing cached SVIDs may continue briefly, but new identities and rotations become fragile during outages. | Plan Server high availability, datastore durability, backup, recovery, upstream CA integration, and operational monitoring. |

---

## Quiz

### Question 1

Your team runs `payment-api`, `refund-worker`, and `settlement-exporter` in the `payments` namespace. A proposed SPIRE entry uses only `k8s:ns:payments` and issues `spiffe://example.org/ns/payments`. The card vault will allow that SPIFFE ID to read tokenized card data. How would you evaluate this design, and what would you change before approving it?

<details>
<summary>Show Answer</summary>

The design is too broad because every matching workload in the namespace can receive the same identity and therefore satisfy the card vault policy. The card vault needs to distinguish the specific workload that is allowed to read tokenized card data, not merely the namespace where the workload runs. A better design is to create a dedicated ServiceAccount for `payment-api`, register an identity such as `spiffe://example.org/ns/payments/sa/payment-api`, and make the card vault authorize only that identity for the relevant operation. If labels are governed by admission policy, an additional controlled app label selector can make the registration more precise.

</details>

### Question 2

A service successfully completes mTLS with a client certificate issued by the `example.org` trust domain, but the service does not check the SPIFFE ID after TLS validation. Later, an unrelated workload in the same trust domain connects successfully to an internal admin endpoint. What is the bug, and where should the fix live?

<details>
<summary>Show Answer</summary>

The bug is treating trust-domain certificate validity as authorization. TLS validation proves that the peer has an SVID issued by a trusted authority, but it does not prove that this peer is allowed to use the admin endpoint. The fix should live in application authorization logic, a sidecar or gateway policy, or another enforcement point that extracts the peer SPIFFE ID and checks it against allowed identities for that endpoint. The rule should be specific to the operation, such as allowing only `spiffe://example.org/ns/platform/sa/admin-controller` for the admin route.

</details>

### Question 3

A pod mounts `/spiffe-workload-api`, the SPIRE Agent is running on the same node, and the SPIRE Server healthcheck passes. The workload still receives no SVID. The registration entry has selectors `k8s:ns:orders` and `k8s:sa:order-service`, but the pod was deployed with `serviceAccountName: default`. What should you check and change?

<details>
<summary>Show Answer</summary>

The selectors do not match the workload. Since the registration requires `k8s:sa:order-service`, a pod using the `default` ServiceAccount should not receive that SVID. First verify the pod's actual ServiceAccount with `kubectl get pod -o jsonpath`, then update the Deployment to use `serviceAccountName: order-service` if that is the intended identity. Do not loosen the SPIRE entry to match `default` unless the default ServiceAccount truly represents the authorization subject, which is rarely a good platform design.

</details>

### Question 4

A platform team wants one identity system for Kubernetes services, VM-based batch workers, and a small number of bare-metal processes. Another team suggests using only Kubernetes ServiceAccount tokens because they already work in the cluster. How would you compare the options?

<details>
<summary>Show Answer</summary>

Kubernetes ServiceAccount tokens are a good fit for Kubernetes API authentication and selected in-cluster token flows, but they do not naturally cover VM or bare-metal workloads. SPIFFE/SPIRE is designed for portable workload identity across heterogeneous runtimes when appropriate node and workload attestors are configured. The recommendation would be to keep ServiceAccount tokens for Kubernetes API access, but evaluate SPIFFE/SPIRE for service-to-service identity across Kubernetes and non-Kubernetes workloads. The decision should include operational cost, trust-domain design, and whether services are ready to authorize based on SPIFFE IDs.

</details>

### Question 5

A production SPIRE deployment uses one SPIRE Server pod with the default datastore. During a maintenance window the Server becomes unavailable, and new workloads cannot receive identities. Existing services continue briefly because their Agents cached SVIDs. What architectural weakness did this reveal, and how should the team address it?

<details>
<summary>Show Answer</summary>

The deployment made the SPIRE Server and its datastore a fragile control-plane dependency. Agents may cache SVIDs and bundles, but new issuance, rotation, registration changes, and recovery still depend on Server availability and persistent state. The team should design SPIRE Server high availability, use a durable datastore appropriate for production, monitor issuance and rotation, document recovery procedures, and decide how the upstream authority is protected. The exact topology depends on the environment, but "one default Server pod" is not a sufficient production plan.

</details>

### Question 6

An application team copies SVID certificate files into a container image during a build because they want the service to start without mounting the Workload API socket. The certificates expire after deployment, and the team asks for longer TTLs. How should a platform engineer respond?

<details>
<summary>Show Answer</summary>

Copying SVIDs into images defeats the SPIFFE/SPIRE operating model. SVIDs are meant to be short-lived and delivered dynamically after workload attestation, not baked into artifacts that can be copied, leaked, and reused. The platform engineer should require the workload to consume the Workload API through a library, helper, or proxy, then verify that rotation works without restarts. Increasing TTLs may hide the symptom, but it increases compromise impact and does not fix the broken delivery pattern.

</details>

### Question 7

Two clusters use separate trust domains: `prod.example.org` and `shared.example.org`. A logging collector in `shared.example.org` must receive telemetry from a production service, but no other shared service should call production APIs. The team proposes full federation and broad allow rules for both domains. What design would you recommend instead?

<details>
<summary>Show Answer</summary>

Federation should be explicit and paired with narrow authorization. The domains can federate only where the telemetry call path requires trust, but production services should still authorize specific peer SPIFFE IDs rather than all identities from `shared.example.org`. For example, the production service or gateway can allow `spiffe://shared.example.org/ns/observability/sa/log-collector` for the telemetry endpoint while denying other shared-domain identities. Federation establishes the ability to verify identities across domains; it should not become blanket access.

</details>

---

## Hands-On Exercise

### Objective

Deploy SPIRE in a local Kubernetes cluster, register two workloads with different SPIFFE IDs, inspect an issued X.509-SVID, and debug one intentional selector mismatch. The exercise aligns with the module outcomes: you will configure identity issuance, verify certificate contents, and analyze why a workload does or does not receive an identity.

### Step 1: Create the Lab Cluster and Install SPIRE

Run the setup commands from a clean terminal. If a previous `spire-lab` cluster exists, delete it first so the exercise starts from known state.

```bash
kind delete cluster --name spire-lab || true

kind create cluster --name spire-lab

helm repo add spire https://spiffe.github.io/helm-charts-hardened/
helm repo update

helm install spire spire/spire \
  --namespace spire-system \
  --create-namespace \
  --set global.spire.trustDomain=example.org \
  --set global.spire.clusterName=spire-lab \
  --wait \
  --timeout 300s
```

Success criteria for this step:

- [ ] The `spire-system` namespace exists.
- [ ] `spire-server-0` is running or completed its readiness checks.
- [ ] At least one SPIRE Agent pod is running.
- [ ] `spire-server healthcheck` returns healthy.

Verify with:

```bash
kubectl get pods -n spire-system -o wide

kubectl exec -n spire-system spire-server-0 -- \
  spire-server healthcheck

kubectl exec -n spire-system spire-server-0 -- \
  spire-server agent list
```

### Step 2: Create Workload Namespaces and ServiceAccounts

Create two different workload subjects. The names intentionally match the SPIFFE paths you will register later.

```bash
kubectl create namespace payments
kubectl create serviceaccount api-server -n payments

kubectl create namespace orders
kubectl create serviceaccount order-service -n orders
```

Success criteria for this step:

- [ ] The `payments` namespace exists.
- [ ] The `orders` namespace exists.
- [ ] The `api-server` ServiceAccount exists in `payments`.
- [ ] The `order-service` ServiceAccount exists in `orders`.

Verify with:

```bash
kubectl get serviceaccount -n payments api-server

kubectl get serviceaccount -n orders order-service
```

### Step 3: Register Two SPIFFE Identities

Capture the Agent path and create registration entries for each workload. These entries bind Kubernetes selectors to SPIFFE IDs.

```bash
AGENT_PATH=$(kubectl exec -n spire-system spire-server-0 -- \
  spire-server agent list -output json | jq -r '.[0].id.path')

echo "${AGENT_PATH}"

kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry create \
    -spiffeID spiffe://example.org/ns/payments/sa/api-server \
    -parentID spiffe://example.org${AGENT_PATH} \
    -selector k8s:ns:payments \
    -selector k8s:sa:api-server \
    -ttl 3600

kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry create \
    -spiffeID spiffe://example.org/ns/orders/sa/order-service \
    -parentID spiffe://example.org${AGENT_PATH} \
    -selector k8s:ns:orders \
    -selector k8s:sa:order-service \
    -ttl 3600
```

Success criteria for this step:

- [ ] Two registration entries exist.
- [ ] The payments entry uses `spiffe://example.org/ns/payments/sa/api-server`.
- [ ] The orders entry uses `spiffe://example.org/ns/orders/sa/order-service`.
- [ ] Each entry has namespace and ServiceAccount selectors.
- [ ] Each entry uses a TTL of 3600 seconds.

Verify with:

```bash
kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry show
```

### Step 4: Deploy the Payments Workload

Create a file named `payments-api.yaml` with this manifest.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: payments
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      serviceAccountName: api-server
      containers:
        - name: app
          image: ghcr.io/spiffe/spiffe-helper:latest
          command:
            - sleep
            - infinity
          volumeMounts:
            - name: spiffe-workload-api
              mountPath: /spiffe-workload-api
              readOnly: true
      volumes:
        - name: spiffe-workload-api
          csi:
            driver: csi.spiffe.io
            readOnly: true
```

Apply it and wait for readiness.

```bash
kubectl apply -f payments-api.yaml

kubectl wait --for=condition=ready pod \
  -l app=api-server \
  -n payments \
  --timeout=90s
```

Success criteria for this step:

- [ ] The payments deployment exists.
- [ ] The pod uses the `api-server` ServiceAccount.
- [ ] The pod mounts `/spiffe-workload-api`.
- [ ] The pod is running on a node that has a SPIRE Agent.

Verify with:

```bash
kubectl get pod -n payments -l app=api-server -o wide

kubectl get pod -n payments -l app=api-server \
  -o jsonpath='{.items[0].spec.serviceAccountName}{"\n"}'

kubectl describe pod -n payments -l app=api-server | sed -n '/Mounts:/,/Conditions:/p'
```

### Step 5: Fetch and Inspect the Payments SVID

Ask the local Workload API for an X.509-SVID and inspect the certificate. In this lab, writing the certificate to `/tmp/` is acceptable because you are inspecting the result manually.

```bash
kubectl exec -n payments deploy/api-server -- \
  /opt/spire/bin/spire-agent api fetch x509 \
    -socketPath /spiffe-workload-api/spire-agent.sock \
    -write /tmp/

kubectl exec -n payments deploy/api-server -- \
  openssl x509 -in /tmp/svid.0.pem -text -noout \
  | sed -n '/Subject Alternative Name/,+2p'

kubectl exec -n payments deploy/api-server -- \
  openssl x509 -in /tmp/svid.0.pem -noout -dates
```

Success criteria for this step:

- [ ] The fetch command completes successfully.
- [ ] The certificate contains `URI:spiffe://example.org/ns/payments/sa/api-server`.
- [ ] The certificate has a short validity window consistent with the registration TTL.
- [ ] You can explain why the ServiceAccount selector allowed this SVID to be issued.

### Step 6: Deploy the Orders Workload and Confirm a Distinct Identity

Create `orders-service.yaml` with a similar manifest for the orders service.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: orders
spec:
  replicas: 1
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      serviceAccountName: order-service
      containers:
        - name: app
          image: ghcr.io/spiffe/spiffe-helper:latest
          command:
            - sleep
            - infinity
          volumeMounts:
            - name: spiffe-workload-api
              mountPath: /spiffe-workload-api
              readOnly: true
      volumes:
        - name: spiffe-workload-api
          csi:
            driver: csi.spiffe.io
            readOnly: true
```

Apply it and inspect its SVID.

```bash
kubectl apply -f orders-service.yaml

kubectl wait --for=condition=ready pod \
  -l app=order-service \
  -n orders \
  --timeout=90s

kubectl exec -n orders deploy/order-service -- \
  /opt/spire/bin/spire-agent api fetch x509 \
    -socketPath /spiffe-workload-api/spire-agent.sock \
    -write /tmp/

kubectl exec -n orders deploy/order-service -- \
  openssl x509 -in /tmp/svid.0.pem -text -noout \
  | sed -n '/Subject Alternative Name/,+2p'
```

Success criteria for this step:

- [ ] The orders workload receives an SVID.
- [ ] The orders certificate contains `URI:spiffe://example.org/ns/orders/sa/order-service`.
- [ ] The payments and orders workloads have distinct SPIFFE IDs.
- [ ] You can describe how those identities would support different authorization rules.

### Step 7: Create and Debug an Intentional Selector Mismatch

Patch the payments deployment to use the wrong ServiceAccount, then observe the result. This step proves that SPIRE is enforcing the registration selectors rather than issuing identities to any pod in the namespace.

```bash
kubectl patch deployment api-server -n payments \
  --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/serviceAccountName","value":"default"}]'

kubectl rollout status deployment/api-server -n payments

kubectl exec -n payments deploy/api-server -- \
  /opt/spire/bin/spire-agent api fetch x509 \
    -socketPath /spiffe-workload-api/spire-agent.sock \
    -write /tmp/ || true
```

Now debug the mismatch.

```bash
kubectl get pod -n payments -l app=api-server \
  -o jsonpath='{.items[0].spec.serviceAccountName}{"\n"}'

kubectl exec -n spire-system spire-server-0 -- \
  spire-server entry show \
    -selector k8s:ns:payments \
    -selector k8s:sa:api-server
```

Restore the correct ServiceAccount and verify identity issuance works again.

```bash
kubectl patch deployment api-server -n payments \
  --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/serviceAccountName","value":"api-server"}]'

kubectl rollout status deployment/api-server -n payments

kubectl exec -n payments deploy/api-server -- \
  /opt/spire/bin/spire-agent api fetch x509 \
    -socketPath /spiffe-workload-api/spire-agent.sock \
    -write /tmp/
```

Success criteria for this step:

- [ ] The workload fails to receive the payments SVID while using the `default` ServiceAccount.
- [ ] You identify the failed selector without changing the registration entry.
- [ ] Restoring `serviceAccountName: api-server` restores SVID issuance.
- [ ] You can explain why this denial is a security feature rather than a platform bug.

### Step 8: Clean Up the Lab

Remove the local cluster when you finish. This avoids leaving trust material and lab workloads on your workstation.

```bash
kind delete cluster --name spire-lab
```

Final success criteria for the full exercise:

- [ ] SPIRE Server, Agent, and CSI components were deployed and verified.
- [ ] Two workloads received two distinct SPIFFE IDs.
- [ ] You inspected the URI SAN in at least one X.509-SVID.
- [ ] You intentionally broke and fixed a selector mismatch.
- [ ] You can state where authentication ends and authorization begins in a SPIFFE-based mTLS design.

---

## Next Module

Return to the [Security Tools README](/platform/toolkits/security-quality/security-tools/) to review the rest of the security toolkit, or continue to the [Networking Toolkit](/platform/toolkits/infrastructure-networking/networking/) for service mesh, Cilium, and identity-aware traffic patterns.
