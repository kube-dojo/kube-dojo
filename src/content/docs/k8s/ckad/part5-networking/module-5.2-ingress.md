---
revision_pending: false
title: "Module 5.2: Ingress"
slug: k8s/ckad/part5-networking/module-5.2-ingress
sidebar:
  order: 2
lab:
  id: ckad-5.2-ingress
  url: https://killercoda.com/kubedojo/scenario/ckad-5.2-ingress
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Important for external access, multiple concepts
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 5.1 (Services), understanding of HTTP and DNS

---

## Learning Outcomes

After completing this module, you will be able to:

- **Create** Ingress resources with host-based and path-based routing rules that connect external HTTP traffic to internal Services.
- **Configure** TLS termination and multiple backend Services in one Ingress while keeping namespace and certificate boundaries correct.
- **Debug** Ingress routing failures by checking controller status, IngressClass binding, backend Service ports, Endpoints, and controller logs.
- **Evaluate** when Ingress is the right exposure mechanism compared with LoadBalancer Services, NodePort Services, and Gateway API.

## Why This Module Matters

Hypothetical scenario: your team ships a small product with a web frontend, an API, and an admin interface. Each workload already has a ClusterIP Service, so traffic works inside the cluster, but users outside the cluster need friendly HTTPS URLs such as `app.example.com`, `api.example.com`, and `app.example.com/admin`. You could expose each Service with a separate cloud load balancer, but that choice spreads routing, TLS, and cost across multiple objects that are harder to reason about during an incident.

Ingress gives Kubernetes a standard HTTP routing contract for that situation. The Ingress object describes host names, URL paths, TLS secrets, and backend Services, while an Ingress controller turns that description into real proxy or load balancer configuration. The object by itself does not open a socket, allocate a public IP, or terminate TLS; it is closer to a written routing request that a controller must reconcile.

The CKAD exam usually focuses on the application-owner side of this contract. You are expected to create and inspect Ingress resources, choose `Prefix` or `Exact` path matching, bind to the right backend Service port, and recognize when a missing controller or wrong class explains an empty address. You are not usually asked to design a production edge architecture, but the same mental model helps you avoid exam mistakes and production outages.

Kubernetes 1.35+ still supports `networking.k8s.io/v1` Ingress, but Ingress is a stable, deliberately limited API. It handles HTTP and HTTPS routing well, yet it does not try to model every modern load-balancing feature. Treat this module as the practical CKAD foundation, then compare it with Gateway API when you need richer traffic splitting, cross-namespace attachment, or a more expressive platform contract.

## Ingress as a Routing Contract

Ingress sits one layer above the Service abstraction you learned in Module 5.1. A Service gives Pods a stable virtual address inside the cluster, while an Ingress tells an edge controller how external HTTP requests should reach those Services. The controller might be Traefik, Kong, Cilium, Envoy Gateway, NGINX Gateway Fabric, or another implementation that understands Ingress resources and owns the external entry point.

The most important separation is between desired state and implementation. The Ingress resource is stored in the Kubernetes API server, but it does not proxy traffic by itself. A controller watches Ingress resources, watches related Services and Endpoints, and updates its own runtime configuration whenever the desired state changes. Without that controller, the YAML can be perfectly valid and still route no traffic.

This is the same control-loop pattern you have seen with Deployments. A Deployment does not launch containers directly; it describes a desired rollout, and controllers create ReplicaSets and Pods. Ingress follows that pattern at the network edge: you write the rule, the controller reconciles the rule, and the controller's load balancer or proxy handles the packets.

The hotel reception analogy is useful if you keep the roles precise. Guests arrive at one entrance, ask for a restaurant, spa, or room, and the receptionist routes them to the correct place. In Kubernetes terms, the entrance is the controller's external address, the request host and path are what the guest asks for, and the destination room is a backend Service that already knows how to reach healthy Pods.

Pause and predict: if you apply an Ingress with valid YAML and `kubectl get ingress` keeps showing an empty `ADDRESS`, what part of the system would you inspect before changing the routing rules? The fastest answer is usually the controller and class binding, not the Service selector, because no address means the edge implementation has not claimed or published the route yet.

```bash
# Check if you have an Ingress controller
kubectl get pods -n ingress-nginx
# or
kubectl get pods -A | grep -i ingress
```

The namespace in that command is intentionally controller-specific. Many older labs use an `ingress-nginx` namespace, while newer clusters may run Traefik, Cilium, Kong, Envoy Gateway, or a managed cloud controller in a different namespace. For exam work, first discover what exists, then adapt the class name and controller log command to the environment you are given.

An Ingress resource needs the usual Kubernetes object envelope plus a `spec` that contains rules. Each rule can match a host, then one or more HTTP paths, and each path points to a backend Service by name and port. The backend Service must live in the same namespace as the Ingress unless the API explicitly says otherwise, and the standard Service backend shown here is the normal CKAD shape.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

Read the backend section as a pointer into an existing Service, not directly into a Pod. That detail matters when debugging because a working Ingress can still return a controller-generated 503 if the Service has no ready Endpoints. The request path is Ingress controller, then Service, then Endpoints or EndpointSlices, then Pods; every hop must agree on names, ports, and readiness.

The resource also has an important defaulting story. Some clusters define a default IngressClass, which lets an Ingress omit `spec.ingressClassName`; other clusters require you to name the class explicitly. For portable manifests and exam clarity, prefer an explicit class when the environment exposes one, and use `kubectl get ingressclass` before assuming the controller name.

The following diagram is the original module's request-flow picture, with the same protected asset preserved for orientation. It is intentionally static rather than a sequence diagram because the key idea is component placement: the controller owns the external address, the Ingress stores rules, and Services remain the bridge to Pods.

```
┌─────────────────────────────────────────────────────────────┐
│                    Ingress Flow                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet                                                   │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────┐                   │
│  │     Ingress Controller              │                   │
│  │     (traefik, kong, cilium, etc.)   │                   │
│  │                                      │                   │
│  │  Reads Ingress rules                │                   │
│  │  Routes based on host/path          │                   │
│  └─────────────────────────────────────┘                   │
│     │                                                       │
│     │ api.example.com/users                                │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────┐                   │
│  │         Ingress Resource            │                   │
│  │                                      │                   │
│  │  rules:                             │                   │
│  │  - host: api.example.com            │                   │
│  │    paths:                           │                   │
│  │    - /users → user-svc:80           │                   │
│  │    - /orders → order-svc:80         │                   │
│  │  - host: web.example.com            │                   │
│  │    paths:                           │                   │
│  │    - / → frontend-svc:80            │                   │
│  └─────────────────────────────────────┘                   │
│     │                                                       │
│     ▼                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ user-svc │  │order-svc │  │frontend  │                 │
│  │   :80    │  │   :80    │  │svc :80   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The practical implication is that Ingress debugging begins with ownership. If no controller claims the Ingress, there is no edge configuration to inspect. If a controller claims it but returns an error, the next question is whether the rule matches the request host and path. If the rule matches but the controller cannot reach a backend, the Service and Endpoints become the next layer of evidence.

## Path Matching and Routing Rules

Ingress routing is built from two visible parts of an HTTP request: the `Host` header and the URL path. The host decides which virtual site the request is trying to reach, and the path decides which part of that site should handle the request. This makes Ingress a good fit for many application layouts, such as `api.example.com` for API traffic and `example.com/docs` for documentation traffic.

The first path type you should reach for is `Prefix`. Kubernetes defines this as element-wise prefix matching on path segments, so `/api` matches `/api`, `/api/`, and `/api/users`, but it does not mean arbitrary substring matching. That distinction prevents a route for `/api` from unexpectedly matching a path such as `/apix` when the controller follows the Kubernetes semantics correctly.

```yaml
pathType: Prefix
path: /api
# Matches: /api, /api/, /api/users, /api/users/123
```

`Exact` is stricter and useful when one URL should mean one backend with no child paths. A route for `/api` with `Exact` does not match `/api/` or `/api/users`, so it is rarely the right choice for a whole API surface. It is useful for a health page, a callback endpoint, or an intentionally narrow route that should not swallow adjacent traffic.

```yaml
pathType: Exact
path: /api
# Matches: /api only
# Does NOT match: /api/, /api/users
```

`ImplementationSpecific` delegates path interpretation to the IngressClass implementation. That can be attractive when you depend on a controller-specific feature, but it weakens portability because another controller may interpret the same path differently. In CKAD practice, prefer `Prefix` or `Exact` unless the task explicitly asks for controller-specific behavior.

When multiple paths match, Kubernetes path precedence favors the longest matching path before considering path type. That means `/api/v2` is a more specific match than `/api` for a request such as `/api/v2/users`. Before running this, what output do you expect if an Ingress contains both rules and you curl `/api/v2/users` with the correct host header? The answer should be the backend behind the longer matching path, assuming the controller implements the standard precedence rules.

Host-based routing is the cleanest design when different DNS names represent different applications or security boundaries. It keeps URL paths simple, lets TLS certificates map naturally to hostnames, and reduces the chance that one application accidentally depends on another application's path prefix. The tradeoff is that DNS and certificates become part of every environment you test.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-routing
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

Path-based routing is useful when one hostname represents a product but different Services own different URL prefixes. It is common for small systems, documentation portals, and internal tools, but it can become fragile if applications assume they are mounted at `/`. When an application generates absolute links, redirects, cookies, or OpenAPI paths, you must verify that it behaves correctly behind the chosen prefix.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-routing
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

Stop and think: an Ingress has two path rules, `/api` with `pathType: Prefix` and `/api/v2` with `pathType: Prefix`. A request comes in for `/api/v2/users`. Which backend receives the traffic, and what single command would you run afterward to confirm the controller's rendered backend list?

A default backend is the catch-all path for requests that do not match any host or path rule. Some controllers configure a global default backend outside your Ingress object, while Kubernetes also allows an Ingress-level `spec.defaultBackend`. In application modules, use it deliberately for a known fallback Service, not as a way to hide ambiguous routes.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: with-default
spec:
  defaultBackend:
    service:
      name: default-service
      port:
        number: 80
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

The risk with catch-all routing is observability. If a wrong hostname or misspelled path silently lands on a default page, users may report confusing behavior instead of a clear error. For exam tasks, a default backend is straightforward; for production design, pair it with logging, a distinctive response body, and monitoring that separates expected fallback traffic from broken route traffic.

The backend Service port in every route must match the Service's exposed port, not necessarily the Pod container port. If your Service exposes `port: 80` and maps to `targetPort: 8080`, the Ingress backend should usually reference Service port `80`. Many 503 investigations start with someone checking the Pod container port and missing that the Ingress talks to the Service abstraction.

Another routing detail appears when multiple Ingress objects describe the same host. Controllers commonly merge compatible rules, but conflicts are implementation-specific and can be hard to notice from one manifest alone. If two teams both create paths under `example.com`, the route that works in development may collide in a shared cluster. During troubleshooting, inspect all Ingress objects in the namespace, and use `kubectl get ingress -A` when cluster policy allows cross-namespace visibility.

Wildcard hosts deserve the same caution. Kubernetes supports wildcard hostnames in a limited form, but a wildcard certificate, wildcard DNS record, and wildcard Ingress rule are three different pieces of state. They must agree before traffic behaves cleanly. A wildcard route can be useful for preview environments, yet it can also make accidental hostnames look valid, so pair it with explicit ownership and clear cleanup rules.

Path rewrites are where many simple designs become controller-specific. A backend mounted at `/` may not understand that users reached it through `/api`, so teams add a rewrite annotation to strip the prefix. That can be correct, but it changes what the application sees compared with what the client requested. When debugging login redirects, generated links, or OpenAPI docs, ask whether the backend receives the original path or a rewritten path.

## TLS Termination and HTTPS Boundaries

TLS in a standard Ingress usually means termination at the controller. The client connects to the controller over HTTPS, the controller presents a certificate from a Kubernetes Secret, and the controller then forwards the request to the backend Service using the protocol configured by that controller. The Kubernetes Ingress API models the TLS host and Secret reference, but controller-specific annotations may be needed for advanced backend TLS behavior.

The Secret type for certificate material is `kubernetes.io/tls`, and `kubectl create secret tls` creates that shape from a certificate and private key. The Secret must be in the same namespace as the Ingress that references it. That namespace boundary is a common exam and production failure because the Ingress spec only names `secretName`; it does not include a namespace field for the TLS Secret.

```bash
# Create TLS secret from cert and key
kubectl create secret tls my-tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

The Ingress `tls` list maps hostnames to Secret names. The hostname in the TLS block should align with the hostname in the rule and with the certificate's Subject Alternative Name. If the Secret contains a valid certificate for a different host, the controller may still load it, but browsers will reject the connection because certificate identity is checked by the client.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  tls:
  - hosts:
    - secure.example.com
    secretName: my-tls-secret
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-service
            port:
              number: 80
```

Modern controllers usually support SNI, which lets multiple HTTPS hostnames share the same external address while presenting the certificate that matches each requested host. That is one reason a single Ingress controller can front many applications without one load balancer per Service. SNI does not remove the need for correct DNS, Secret placement, and certificate hostnames; it only lets the controller choose among certificates during the TLS handshake.

For CKAD troubleshooting, separate TLS problems from routing problems. A certificate warning before any application response points toward the Secret, certificate name, or TLS host configuration. A clean certificate followed by a 404 or 503 means TLS succeeded and you should inspect host rules, path rules, Services, and Endpoints. This ordering keeps you from changing YAML that the request never reached.

There is also a security boundary to remember. If the controller terminates TLS and forwards plain HTTP to the Service, traffic inside the cluster is not encrypted by that Ingress setting alone. Some platforms accept that because the cluster network is trusted; others require controller-specific backend TLS, mTLS, a service mesh, or Gateway API features. Ingress gives you the edge termination contract, not a complete end-to-end encryption design.

Certificate rotation is another place where the Ingress API is deliberately small. The Ingress references a Secret name, and the controller watches that Secret, but the API does not say who obtains, renews, or audits the certificate. Some clusters use cert-manager, some use external automation, and some rely on a platform team. As an application author, you should verify the Secret name, namespace, and hostnames without assuming that the renewal system is part of Ingress itself.

For local testing, remember that HTTPS validates names, not just IP addresses. If you curl the controller IP directly, the certificate for `secure.example.com` will not match that IP unless it was issued with a matching IP subject alternative name. A better test sends the correct host header or configures local name resolution so the client asks for the same hostname that appears in the Ingress rule and certificate.

## IngressClass and Controller-Specific Behavior

IngressClass answers a simple but important question: which controller is responsible for this Ingress? A cluster can run more than one controller, such as an internal-only controller and an internet-facing controller. If your Ingress does not name a class and no default class exists, the controller may ignore it, leaving the object present in the API with no useful external address.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: nginx    # Which controller
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

The older `kubernetes.io/ingress.class` annotation is still visible in old examples, but `spec.ingressClassName` is the Kubernetes field to use in current manifests. A default class can be marked on the IngressClass object by the platform team, but application authors should not assume that default exists. On an unfamiliar cluster, list the available classes before deciding whether to set the field.

```bash
# List available IngressClasses
kubectl get ingressclass
```

Annotations are still common because Ingress is intentionally small. Rewrites, redirect behavior, request body limits, upstream protocol choices, and timeout settings are often controller-specific, so the standard API leaves them to controller documentation. This flexibility is useful, but it means annotations are not portable contracts across controllers.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: annotated-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

The annotations in that preserved example are intentionally NGINX-style, so read them as controller-specific examples rather than universal Kubernetes settings. A Traefik, Kong, Cilium, or cloud-controller deployment may use different annotations or custom resources for the same intent. When a copied annotation appears to do nothing, first confirm that the running controller supports that exact key.

Common NGINX annotations include URL rewriting, HTTPS redirect behavior, and maximum request body size. The concept transfers across controllers even when the syntax changes: you are asking the edge implementation to alter request handling beyond the standard host, path, backend, and TLS fields. That boundary helps you decide whether a problem belongs in portable Kubernetes YAML or in controller documentation.

Ingress status is also controller-owned. The `status.loadBalancer.ingress` field is not something you normally set in the manifest, because the controller updates it after publishing an address or hostname. If status never changes, the controller may be absent, watching a different class, blocked by permissions, or unable to provision its external dependency. That is different from an application-level failure where the address exists but the backend returns an error.

Default IngressClass behavior is convenient but can hide platform changes. If a cluster admin changes which class is default, new Ingresses without `ingressClassName` may start landing on a different controller while older objects keep their previous status. Explicit class names are slightly more verbose, yet they make reviews and incident timelines clearer because the intended controller is written into the application manifest.

The quick reference below preserves the original module's command inventory with the runnable shorthand corrected. Use it as a diagnostic sequence, not as a random command list. Start by confirming the Ingress object, then inspect its rendered rules and events, then check the address, class, and controller logs if the route is not behaving as expected.

```bash
# Create Ingress imperatively (limited)
kubectl create ingress my-ingress --class=nginx \
  --rule="host.example.com/path=service:port"

# View Ingress
kubectl get ingress
kubectl describe ingress NAME

# Get Ingress address (ip and/or hostname — kind/minikube often use hostname)
kubectl get ingress NAME -o jsonpath='{.status.loadBalancer.ingress[0].ip}{"\n"}{.status.loadBalancer.ingress[0].hostname}'

# Check IngressClass
kubectl get ingressclass

# View controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

Imperative creation is handy during exam drills, but declarative YAML is better for anything you intend to review or reuse. The imperative command cannot express every controller-specific annotation, TLS layout, or multi-rule design comfortably. Use `kubectl create ingress` when speed matters and the task is simple; switch to a manifest when clarity, reviewability, or repeatability matters more.

## Debugging the Request Path

A reliable Ingress debugging routine follows the same direction as a request. Confirm the client reaches the controller address, confirm the controller has accepted the Ingress, confirm the host and path match the expected rule, confirm the backend Service name and port exist, and finally confirm the Service has ready endpoints. Jumping directly to Pod logs can waste time when the route never selected those Pods.

The `kubectl describe ingress` output is often the best first artifact because it combines rules, backends, address information, annotations, class, and events. If the backend section shows the Service but no endpoint addresses, the controller has enough information to find the Service but not enough healthy targets to proxy. That usually points at a Service selector mismatch, readiness probe failure, or wrong `targetPort`.

When the symptom is an empty address, ask ownership questions first. Is there a controller running? Does the Ingress name the right `ingressClassName`? Does the cluster define a default IngressClass? Does the controller have permission to update Ingress status? These questions belong before path matching because a rule that has not been claimed cannot route any request.

When the symptom is a 404 from the controller, the controller is probably reachable but did not match the request to the intended rule. Check the request's `Host` header, the DNS name or local `/etc/hosts` mapping, the path prefix, and whether another Ingress owns a more specific rule. A backend application 404 is different; it proves the request reached a Pod, so inspect application routing rather than Ingress matching.

When the symptom is a 503 from the controller, the rule usually matched but the backend is unavailable. Inspect the Service, Endpoints, EndpointSlices, and Pod readiness. The Ingress does not make an unready Pod healthy, and it does not bypass the Service selector. A Service with zero endpoints is a broken bridge between the route and the workload.

Testing tools can accidentally change the problem you are trying to observe. A browser follows redirects, caches HSTS decisions, and may reuse connections, while curl can send an exact host header and path. When diagnosing a route, write down the host, path, scheme, and expected backend before testing. That small discipline turns "Ingress is broken" into a falsifiable statement about one request shape.

DNS is outside the Ingress object but inside the user experience. The Ingress may publish an address correctly while `app.example.com` still points somewhere else or has not propagated. In a lab, you may simulate DNS with a local hosts file or a curl resolve option. In production, include DNS records and certificate issuance in the rollout checklist because users do not interact with Kubernetes object status directly.

Exercise scenario: you create `api.example.com` routing to `api-service:80`, the certificate is valid, and the controller log shows upstream connection errors. In that situation, changing the TLS Secret is low-value because TLS already succeeded. The better path is to inspect `api-service`, verify its selector, confirm ready Pods, and compare Service `port` with Pod `targetPort`.

Controller logs are still valuable, but read them after you know which controller owns the Ingress. The original quick reference uses an `ingress-nginx` label because older labs often did, yet a modern cluster might expose Traefik, Cilium, Kong, Envoy Gateway, or a cloud provider controller. `kubectl get pods -A | grep -i ingress` gives you candidates, and the IngressClass tells you which candidate should be reconciling your object.

Your mental model should also include propagation delay. Applying an Ingress updates the API server immediately, but external load balancer allocation, DNS updates, certificate reloads, and controller reconciliation may take longer. During an exam this delay is usually short; in real clusters it can vary by cloud provider and controller. Re-run focused inspection commands before making unrelated edits.

Events often reveal the first useful controller complaint. A rejected backend, missing Secret, invalid annotation value, or class mismatch may appear in `kubectl describe ingress` before it is obvious from the rendered route. Events are not a durable log store, so use them as fast local evidence, then move to controller logs if you need a longer history. This keeps the investigation grounded in the object that is failing.

## Worked Example: Combining Hosts, Paths, TLS, and Backends

Suppose you need one external entry point for a small application with a frontend and API. Host-based routing would give the API its own DNS name, while path-based routing could put it under the same hostname. The design choice depends on client expectations, certificate ownership, and whether the applications are written to live under a path prefix.

For an exam task, the simplest valid answer is often a single Ingress with two Services and either two host rules or two path rules. You do not need a separate Ingress for every backend unless the task asks for separate ownership, different annotations, or different TLS behavior. Fewer objects can be easier to inspect, but one giant shared Ingress can become a coordination problem in larger teams.

If the API must be reachable as `api.local` and the web UI as `web.local`, host rules keep each backend isolated. If both must share `myapp.local`, path rules such as `/frontend` and `/backend` work, but only if the applications tolerate those prefixes. This is why the hands-on exercise asks you to practice both shapes rather than memorizing only one.

Which approach would you choose here and why: a single hostname with `/api`, or separate `api.example.com` and `web.example.com` names? A strong answer mentions more than YAML length. It should consider browser behavior, cookies, certificates, client bookmarks, path rewriting needs, and how easily an on-call engineer can see which Service should receive a request.

The default backend variant adds a fallback for unmatched traffic. That can be useful for a friendly landing page or an internal diagnostic response, but it also hides mistakes if every typo returns something that looks valid. In a learning lab, it demonstrates API shape; in production, it deserves logging and a very intentional response.

TLS then adds a Secret reference and a hostname identity check. If you test with a self-signed certificate, expect browser trust warnings unless you trust the certificate locally, but still verify that the Ingress loads the Secret and the rule points at the intended Service. The controller status, events, and logs tell you whether it accepted the certificate material.

Now add ownership to the worked example. If the frontend and API are owned by the same team, one Ingress may be a reasonable unit of change because one review can cover the shared host and certificate. If separate teams own them, separate Ingress resources or Gateway API route ownership may reduce coordination risk. The Kubernetes API lets you represent both choices, so choose the shape that matches operational responsibility.

Rollback planning is part of the route design. A host-based split can often roll back by changing DNS or route ownership, while a path-based split may require removing only one path rule. If the Ingress also contains unrelated paths, a rushed rollback can accidentally disturb healthy traffic. Keep manifests small enough that a human can identify the affected host and path under pressure.

The rest of the module turns that reasoning into repeatable decisions, then asks you to build the same patterns in a cluster. Keep the request path in your head while you work: external client, controller address, host and path rule, Service port, endpoints, and ready Pods. That sequence is the shortest route from a symptom to the broken layer.

## Patterns & Anti-Patterns

Patterns and anti-patterns for Ingress are mostly about ownership boundaries. A good Ingress design makes it obvious who owns a hostname, which Service receives a path, where TLS material lives, and which controller-specific behavior is required. A weak design spreads those answers across annotations, implicit defaults, copied snippets, and Services whose selectors nobody checked.

| Pattern | When to Use It | Why It Works |
|---------|----------------|--------------|
| Explicit `ingressClassName` | The cluster has more than one controller, or you are not sure whether a default class exists. | It makes controller ownership visible and prevents a valid Ingress from being ignored by every controller. |
| Host-based routing for separate products | Different teams, clients, cookies, certificates, or security policies belong to different applications. | Hostnames make ownership and TLS identity clear, and they avoid path-prefix surprises inside applications. |
| Path-based routing for one cohesive site | One product naturally shares a hostname, and applications can run correctly under their assigned prefixes. | It keeps DNS and certificates simple while still separating backend Services behind one entry point. |
| Controller annotations kept close to the route | A route needs rewrites, redirects, body-size changes, or timeouts that are specific to one controller. | The manifest documents the non-portable behavior beside the route that depends on it. |

An explicit class is the most important operational pattern because it prevents silent ambiguity. In a cluster with internal and external controllers, omitting the class can expose an application on the wrong edge or leave it unclaimed. Even when a default class exists, naming the class in learning manifests makes your intent easier to review.

Host-based routing is a strong default when applications are independently owned. It maps cleanly to DNS, certificates, browser origins, and access policies. The cost is extra DNS and certificate work, but that work often buys clearer troubleshooting because the hostname itself tells you which route should match.

Path-based routing works best when applications are designed for it. If the backend assumes it runs at `/`, a prefix such as `/api` may require rewrites or application configuration. That is not a Kubernetes failure; it is a mismatch between application URL assumptions and edge routing design.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Installing no controller and only applying Ingress YAML | The API object exists, but no proxy watches it or publishes an address. | Confirm the controller and class before treating the route as live. |
| Copying controller annotations across implementations | The new controller ignores keys or interprets them differently. | Read the running controller's documentation and keep portable fields separate from implementation-specific settings. |
| Pointing Ingress at a Pod port instead of a Service port | The backend appears correct to humans but fails because the Service exposes a different port. | Inspect the Service and reference `service.spec.ports[].port` from the Ingress backend. |
| Using a broad default backend to hide all unmatched traffic | Typos and wrong host headers return plausible pages instead of clear failures. | Use explicit host rules and make fallback responses distinctive and observable. |

The recurring theme is not "use fewer annotations" or "always prefer one routing style." The stronger rule is to make every non-obvious behavior inspectable from Kubernetes objects and controller documentation. If another engineer can run `kubectl describe ingress`, inspect the Service, and predict the request path, the design is probably maintainable.

## Decision Framework

Start the exposure decision with the protocol. If the workload needs raw TCP or UDP, standard Ingress is the wrong first abstraction because it is defined for HTTP and HTTPS routing. If the workload is HTTP, ask whether the route needs simple host/path rules or richer traffic policy such as weighted splits, cross-namespace references, or advanced listener ownership. Simple rules fit Ingress; richer platform contracts often point toward Gateway API.

| Need | Prefer | Reason |
|------|--------|--------|
| One internal-only stable address | ClusterIP Service | The traffic stays inside the cluster and does not need edge routing. |
| One external address directly tied to one Service | LoadBalancer Service | The cloud or platform load balancer can front the Service without host/path routing. |
| Many HTTP routes sharing one entry point | Ingress | Host and path rules consolidate routing through a controller. |
| Rich traffic policy or platform/team separation | Gateway API | Gateway and HTTPRoute separate infrastructure ownership from route ownership more explicitly. |
| Quick local or exam exposure without DNS | NodePort or port-forward | Useful for temporary access, but usually not the clean production edge. |

Use this mental flow when choosing an Ingress shape. First, confirm the traffic is HTTP or HTTPS. Second, identify whether hostnames or paths are the natural user-facing contract. Third, decide whether one controller class is sufficient or whether internal and external traffic need separate classes. Fourth, add TLS only after the hostnames are stable enough to match certificate identities.

The decision between host-based and path-based routing is not only stylistic. Host-based routing gives each application its own browser origin, which affects cookies, CORS, and certificate planning. Path-based routing creates one origin, which can simplify clients but may force prefix-aware applications or rewrite annotations. The right choice follows client behavior and application assumptions, not just YAML compactness.

The decision between Ingress and LoadBalancer Service depends on how much HTTP intelligence you need at the edge. A LoadBalancer Service is straightforward for one externally reachable Service, but it usually does not express multiple hostnames and paths in one Kubernetes object. Ingress adds that HTTP routing layer, but it also depends on a controller and controller-specific operations.

The decision between Ingress and Gateway API is about future shape. Ingress remains useful for CKAD tasks and many straightforward applications, but the Kubernetes project treats Gateway API as the more expressive direction for newer routing use cases. When you need listeners, route attachment rules, traffic splitting, or clearer platform ownership, evaluate Gateway API instead of forcing everything through annotations.

For the exam, optimize for a working standard Ingress manifest with correct `apiVersion`, backend Service names, Service ports, `pathType`, and class. For real systems, optimize for a route that another engineer can audit under pressure. Those goals overlap, but production adds certificate lifecycle, DNS ownership, logging, controller upgrades, and platform policy to the basic YAML.

There is one more practical decision: whether the application team or platform team owns the controller. Application teams usually own Ingress objects because they know hostnames, paths, and backend Services. Platform teams usually own controller installation, external load balancers, default classes, and shared annotations policy. Blurring that boundary can create incidents where the application manifest is correct but the controller cannot provision infrastructure.

Use labels and naming conventions to make that boundary searchable. A route named `api` in a namespace named `prod` tells you less than `orders-api-public` with labels that identify the owning app and exposure tier. Naming is not a substitute for correct YAML, but it shortens the first minute of an incident. Ingress objects are few enough that clear names pay back quickly.

## Did You Know?

- **Ingress is configuration, not a Service.** The resource is stored in the Kubernetes API, but the actual routing is done by controller Pods or managed load balancer integrations that watch it.
- **Ingress entered general availability in Kubernetes 1.19.** The older beta API was removed from served APIs in Kubernetes 1.22, which is why current manifests use `networking.k8s.io/v1`.
- **The `kubernetes.io/ingress.class` annotation is legacy.** Current manifests should use `spec.ingressClassName`, while platforms can mark a default IngressClass when they want omitted class names to be assigned automatically.
- **Standard Ingress only models HTTP and HTTPS routing.** For raw TCP or UDP exposure, use a Service type or a controller-specific feature, and compare Gateway API for newer route models.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| No Ingress controller installed | Learners assume the API object itself proxies traffic, so `kubectl apply` feels like enough. | Confirm a controller is running and that it owns the class used by the Ingress. |
| Wrong or missing `ingressClassName` | The cluster has multiple controllers or no default class, so the resource is valid but unclaimed. | Run `kubectl get ingressclass`, then set `spec.ingressClassName` to the intended class. |
| Wrong `pathType` | `Exact` and `Prefix` behave differently, especially for nested application paths. | Use `Prefix` for path trees and `Exact` only for one precise URL path. |
| Service name or port mismatch | The Ingress backend points at a Service port that does not exist or is not the exposed Service port. | Describe the Service and reference `service.spec.ports[].port` in the Ingress backend. |
| Service has no ready endpoints | The route matches, but the controller has nowhere healthy to send traffic. | Check Endpoints or EndpointSlices, Pod readiness, labels, and the Service selector. |
| TLS Secret in the wrong namespace | The Ingress can only reference a Secret by name in its own namespace. | Create or copy the `kubernetes.io/tls` Secret into the same namespace as the Ingress. |
| Copying unsupported annotations | Controller-specific snippets are pasted into a cluster running a different controller. | Verify the running controller and use only annotations documented for that implementation. |

## Quiz

1. **Your Ingress manifest applies successfully, but `kubectl get ingress` shows an empty `ADDRESS` after several reconciliation loops. Other Services in the namespace are healthy. What should you check first, and why?**
   <details>
   <summary>Answer</summary>
   Start with controller ownership rather than backend Pods. An empty address usually means no controller has claimed or published the Ingress, so check whether an Ingress controller is running and whether the resource has the correct `ingressClassName`. Then run `kubectl get ingressclass` and compare the class names with your manifest. Service endpoints matter later, but they do not explain why the edge address was never assigned.
   </details>

2. **Users reach `https://secure.example.com`, but the browser warns that the certificate is not valid for the site. The Ingress rule and TLS block both mention `secure.example.com`. What are two likely causes?**
   <details>
   <summary>Answer</summary>
   First, the Secret may contain a certificate whose Subject Alternative Name does not include `secure.example.com`; the Ingress field does not rewrite certificate identity. Second, the controller may be loading a different Secret because the named Secret is absent or invalid in the Ingress namespace. Verify the Secret exists beside the Ingress, then inspect the certificate names. Backend Service health is not the first suspect because the warning happens during TLS identity validation.
   </details>

3. **A request to `example.com/api/v2/users` is routed to the legacy API even though a newer `/api/v2` backend exists in the same Ingress. What details would you inspect?**
   <details>
   <summary>Answer</summary>
   Confirm that the newer rule actually uses `path: /api/v2` with `pathType: Prefix` and that the controller rendered it for the same host. Kubernetes path precedence should favor the longest matching prefix, so a correct `/api/v2` rule should beat `/api`. If the rule is missing, assigned to another host, or ignored because of controller-specific behavior, the broader `/api` route can win. Also check whether another Ingress for the same host contributes overlapping paths.
   </details>

4. **An Ingress returns a controller-generated 503 for `/api`, and `kubectl describe ingress` shows backend `api-service:80`. The controller has an address and the host matches. What is your next debugging sequence?**
   <details>
   <summary>Answer</summary>
   A 503 after rule matching usually points to backend availability. Describe `api-service`, verify that port `80` exists on the Service, then inspect Endpoints or EndpointSlices for ready addresses. If the endpoint list is empty, compare the Service selector with Pod labels and check Pod readiness. Controller logs can add detail, but they should be read alongside Service and endpoint state.
   </details>

5. **Your team wants `shop.example.com` for the storefront and `blog.example.com` for articles, but also wants `/blog` under the shop host for old links. How would you structure the Ingress?**
   <details>
   <summary>Answer</summary>
   Use host-based rules for both primary hostnames, then add a path rule under `shop.example.com` that sends `/blog` to the blog Service. The shop host should also have a `/` prefix route to the storefront Service. The `/blog` route is more specific than `/`, so it should receive old blog links when the host is `shop.example.com`. Verify the blog application works under that prefix or add controller-supported rewrite behavior.
   </details>

6. **A copied manifest includes `nginx.ingress.kubernetes.io/rewrite-target: /`, but the cluster uses a Traefik controller and the rewrite does not happen. What is the root issue?**
   <details>
   <summary>Answer</summary>
   The annotation is implementation-specific, not part of the portable Ingress API. A Traefik controller is not required to honor an NGINX annotation key, so the route may match while the rewrite is ignored. Confirm the running controller through IngressClass and controller Pods, then use the documentation and configuration model for that controller. The standard fields for host, path, backend, and TLS remain portable; the annotation behavior does not.
   </details>

7. **You need to expose an HTTP app for a CKAD-style task. You can choose NodePort, LoadBalancer Service, or Ingress. The task mentions host-based routing and TLS. Which object should you create, and what existing object must already work?**
   <details>
   <summary>Answer</summary>
   Create an Ingress because host-based routing and TLS termination are standard Ingress concerns. The backend Service must already work, because the Ingress points to a Service name and Service port rather than directly to Pods. You should also confirm that an Ingress controller and suitable class exist in the cluster. NodePort or LoadBalancer alone can expose a Service, but they do not express the requested host routing in the same way.
   </details>

## Hands-On Exercise

This exercise preserves the original module's practical workflow while making the intent more explicit. You will create two simple Deployments, expose them with Services, create three Ingress variants, and then clean up. If your lab cluster does not include an Ingress controller, the objects can still be created and described, but live HTTP testing will depend on the environment's controller setup.

The first goal is not to memorize YAML. The goal is to see how small changes in host, path, default backend, class, and TLS fields change the controller's routing contract. Read each manifest before applying it, predict which Service should receive traffic, then use `kubectl describe ingress` to compare your prediction with the rendered rule list.

### Setup

This lab assumes the lab platform already has the ingress-nginx controller and the `nginx` IngressClass installed. Verify both before creating application resources, because the Ingress manifests below bind explicitly to `spec.ingressClassName: nginx`.

```bash
kubectl get pods -n ingress-nginx
kubectl get ingressclass nginx
```

Only continue when the controller Pods are running and the `nginx` IngressClass exists. If either command fails, install or enable ingress-nginx through your lab environment first.

```bash
# Create two deployments
kubectl create deployment web --image=nginx
kubectl create deployment api --image=nginx

# Create services
kubectl expose deployment web --port=80
kubectl expose deployment api --port=80

# Wait for Deployments (avoids racing pod scheduling)
kubectl wait --for=condition=Available deployment/web deployment/api --timeout=60s
```

### Part 1: Simple Ingress

This first Ingress sends all HTTP traffic that reaches the controller for this namespace and rule set to the `web` Service. It is intentionally minimal, so it is useful for proving that the controller can claim an Ingress and that the Service backend is healthy before adding host or path complexity.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
EOF

kubectl get ingress simple-ingress
kubectl describe ingress simple-ingress
```

<details>
<summary>Solution notes</summary>
The describe output should show a `/` prefix rule pointing to `web:80`. If the backend has ready endpoint addresses, the Service selector and Pods are aligned. If the address is empty, inspect the IngressClass and controller rather than rewriting the backend section first.
</details>

### Part 2: Path-Based Routing

The second Ingress splits one entry point by URL prefix. Requests under `/web` should select the `web` Service, while requests under `/api` should select the `api` Service. This is the lab version of a shared hostname design, and it is where prefix behavior becomes visible.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
EOF

kubectl describe ingress path-ingress
```

<details>
<summary>Solution notes</summary>
The rendered rules should list both `/web` and `/api` with their matching Services. If both show the same backend, the manifest was edited incorrectly. If one backend has no endpoints, return to the matching Service and Deployment before changing the Ingress path rule.
</details>

### Part 3: Host-Based Routing

The third Ingress uses hostnames instead of path prefixes. In a real cluster you would point DNS or local host entries at the controller address before testing. In a lab, the important inspection step is confirming that `web.local` and `api.local` appear as distinct host rules with separate backend Services.

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: web.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
  - host: api.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
EOF

kubectl describe ingress host-ingress
```

<details>
<summary>Solution notes</summary>
The output should show two host sections. If you test with curl, include the correct host header or DNS name; otherwise the request may not match either host rule. A correct Service can look broken when the client sends the wrong host.
</details>

### Cleanup

```bash
kubectl delete ingress simple-ingress path-ingress host-ingress
kubectl delete deployment web api
kubectl delete svc web api
```

### Practice Drills

The drills below preserve the original timed practice assets with runnable commands corrected. Treat the target times as a pressure exercise after you understand the routing model, not as the first pass through the material. If a drill fails, write down which layer failed before trying again: controller ownership, route match, Service port, endpoints, or TLS material.

#### Drill 1: Simple Ingress (Target: 2 minutes)

```bash
kubectl create deployment drill1 --image=nginx
kubectl expose deployment drill1 --port=80

cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill1
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: drill1
            port:
              number: 80
EOF

kubectl get ingress drill1
kubectl delete ingress drill1
kubectl delete deployment drill1
kubectl delete svc drill1
```

#### Drill 2: Host-Based Routing (Target: 3 minutes)

```bash
kubectl create deployment app1 --image=nginx
kubectl create deployment app2 --image=nginx
kubectl expose deployment app1 --port=80
kubectl expose deployment app2 --port=80

cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill2
spec:
  ingressClassName: nginx
  rules:
  - host: app1.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1
            port:
              number: 80
  - host: app2.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2
            port:
              number: 80
EOF

kubectl describe ingress drill2
kubectl delete ingress drill2
kubectl delete deployment app1 app2
kubectl delete svc app1 app2
```

#### Drill 3: Path-Based Routing (Target: 3 minutes)

```bash
kubectl create deployment frontend --image=nginx
kubectl create deployment backend --image=nginx
kubectl expose deployment frontend --port=80
kubectl expose deployment backend --port=80

cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill3
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /frontend
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
      - path: /backend
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 80
EOF

kubectl get ingress drill3
kubectl delete ingress drill3
kubectl delete deployment frontend backend
kubectl delete svc frontend backend
```

#### Drill 4: Ingress with Default Backend (Target: 3 minutes)

```bash
kubectl create deployment default-app --image=nginx
kubectl create deployment api-app --image=nginx
kubectl expose deployment default-app --port=80
kubectl expose deployment api-app --port=80

cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill4
spec:
  ingressClassName: nginx
  defaultBackend:
    service:
      name: default-app
      port:
        number: 80
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-app
            port:
              number: 80
EOF

kubectl describe ingress drill4
kubectl delete ingress drill4
kubectl delete deployment default-app api-app
kubectl delete svc default-app api-app
```

#### Drill 5: Create Ingress Imperatively (Target: 2 minutes)

```bash
kubectl create deployment drill5 --image=nginx
kubectl expose deployment drill5 --port=80

# Create ingress imperatively
kubectl create ingress drill5 --class=nginx --rule="drill5.local/=drill5:80"

kubectl get ingress drill5
kubectl describe ingress drill5

kubectl delete ingress drill5
kubectl delete deployment drill5
kubectl delete svc drill5
```

#### Drill 6: Ingress with TLS (Target: 4 minutes)

```bash
# Create self-signed cert (for demo)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tls.key -out /tmp/tls.crt \
  -subj "/CN=secure.local" 2>/dev/null

# Create TLS secret
kubectl create secret tls drill6-tls --cert=/tmp/tls.crt --key=/tmp/tls.key

kubectl create deployment drill6 --image=nginx
kubectl expose deployment drill6 --port=80

cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drill6
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - secure.local
    secretName: drill6-tls
  rules:
  - host: secure.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: drill6
            port:
              number: 80
EOF

kubectl describe ingress drill6

kubectl delete ingress drill6
kubectl delete secret drill6-tls
kubectl delete deployment drill6
kubectl delete svc drill6
rm /tmp/tls.key /tmp/tls.crt
```

### Success Criteria

- [ ] You can explain why an Ingress resource needs a controller before it can route traffic.
- [ ] You can create a simple Ingress that points to a Service by name and Service port.
- [ ] You can compare host-based routing with path-based routing for the same two backend Services.
- [ ] You can describe when `Prefix` and `Exact` path matching should be used.
- [ ] You can configure a TLS Secret reference and identify namespace or hostname mismatches.
- [ ] You can debug a failing route by walking from controller ownership to Service endpoints.

## Learner check

> On kind/minikube and many cloud load balancers, `status.loadBalancer.ingress` may populate `hostname` instead of `ip`, so a jsonpath that only reads `.ip` can look empty even when the Ingress is healthy.

Before you move on, explain why the hands-on exercise waits on `deployment/web` and `deployment/api` with `condition=Available` instead of `kubectl wait` on `pod -l app=web` or `app=api`. A solid answer mentions ReplicaSet rollout, pod scheduling races, and why Deployment availability is the stable readiness signal before creating Ingress backends.

## Sources

- [Kubernetes Ingress concept documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Kubernetes Service concept documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes TLS Secret documentation](https://kubernetes.io/docs/concepts/configuration/secret/#tls-secrets)
- [Kubernetes Ingress API reference](https://kubernetes.io/docs/reference/kubernetes-api/service-resources/ingress-v1/)
- [Kubernetes IngressClass API reference](https://kubernetes.io/docs/reference/kubernetes-api/service-resources/ingress-class-v1/)
- [kubectl create ingress reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_create/kubectl_create_ingress/)
- [kubectl create secret tls reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_create/kubectl_create_secret_tls/)
- [Gateway API documentation](https://gateway-api.sigs.k8s.io/)
- [Ingress-NGINX controller documentation](https://kubernetes.github.io/ingress-nginx/)
- [Traefik Kubernetes Ingress provider documentation](https://doc.traefik.io/traefik/providers/kubernetes-ingress/)
- [Cilium Ingress documentation](https://docs.cilium.io/en/stable/network/servicemesh/ingress/)
- [Kong Kubernetes Ingress Controller documentation](https://docs.konghq.com/kubernetes-ingress-controller/latest/)

## Next Module

[Module 5.3: NetworkPolicies](../module-5.3-networkpolicies/) - Control pod-to-pod communication.
