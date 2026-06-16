---
title: "Module 7.14: AWX, Tower, and Event-Driven Ansible (EDA) Integration"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.14-awx-tower-eda
sidebar:
  order: 15
---

> **Complexity**: [COMPLEX]
>
> **Time to Complete**: ~120 minutes
>
> **Prerequisites**: [Module 7.12: Ansible Operator SDK Fundamentals](../module-7.12-ansible-operator-sdk/), [Module 7.4: Ansible](../module-7.4-ansible/), familiarity with Kubernetes custom resources, `kubectl`, `kustomize`, and Docker

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy** AWX into a Kubernetes cluster using the AWX Operator and verify the instance reaches Ready status
- **Design** the integration boundary between in-cluster Ansible Operator reconciliation and centralized AWX job template execution
- **Implement** an Event-Driven Ansible rulebook that sources Kubernetes API events, evaluates rule conditions, and triggers a job template via the AWX webhook receiver
- **Evaluate** the AAP vs AWX vs standalone Ansible Operator decision matrix for a given platform size, budget, and audit requirement
- **Configure** Kubernetes credentials, inventory plugins, and custom credential types in AWX to give job templates live cluster visibility

## Why This Module Matters

The Ansible Operator you built in Module 7.12 is a capable piece of machinery for a single CRD on a single cluster. It watches custom resources, reconciles child objects, and reports status back to users. The model works well at small scale: one platform team, one cluster, one or two operators, and a shared understanding of how the system works. The model starts to show seams as the platform grows.

Hypothetical scenario: a platform engineering team manages six clusters across two regions, serves twelve application teams, and runs more than twenty Ansible roles for day-two operations including certificate rotation, database failover, security scanning, and deployment approval. Each role started as a standalone playbook. Some graduated to Ansible Operators. But the operators cannot share secrets safely across clusters, they produce no unified audit log, application teams cannot self-service job launches without per-cluster RBAC delegation, and there is no mechanism to react automatically when a certificate approaches expiration or a deployment enters a crash loop. The platform team needs centralized job orchestration, credential management, and event-driven automation layered over the operator pattern they already know.

AWX, the open-source upstream of Red Hat's Ansible Automation Platform, solves the orchestration and centralization problem. It provides a web UI, REST API, team-based RBAC, encrypted credential storage, inventory management, job scheduling, and webhook receivers that let external systems launch Ansible automation. Event-Driven Ansible extends the model by removing the human from the trigger loop: instead of waiting for a webhook call or a scheduled run, EDA subscribes to event sources continuously, evaluates rulebooks, and automatically runs playbooks or job templates when conditions match.

This module builds on the operator vocabulary from Module 7.12. You will install AWX Operator, configure an AWX instance, learn where AWX fits relative to standalone operators, wire up EDA to react to Kubernetes API events, connect Alertmanager and GitHub Actions via webhooks, configure credentials and dynamic inventory, and explore the production decisions that separate a working AWX install from one that survives real workloads.

## AWX Operator Architecture on Kubernetes

The AWX Operator is itself an Ansible Operator built with Operator SDK — the exact pattern Module 7.12 teaches, applied to managing the AWX application lifecycle. When you deploy the AWX Operator into a cluster, it watches for `AWX` custom resources and reconciles the complete AWX application stack from those resources. This is a satisfying recursion: an Ansible Operator manages Ansible's own automation controller using the same `watches.yaml`, Ansible roles, and `kubernetes.core.k8s` tasks you already know.

The AWX application consists of several components that the operator wires together:

```text
+------------------------------------------------------------------------+
|                       AWX OPERATOR MANAGED STACK                       |
+------------------------------------------------------------------------+
|                                                                        |
|  awx-operator-controller-manager (Deployment)                         |
|  - Watches AWX CR, runs Ansible roles to reconcile all components     |
|                                                                        |
|   AWX CR (awx.ansible.com/v1beta1)                                    |
|   spec: service_type, hostname, storage, replicas, ingress, resources |
|         |                                                              |
|         v                                                              |
|  ┌──────────────────────────────────────────────────────────────────┐ |
|  │  awx-web (Deployment)    │  awx-task (Deployment)               │ |
|  │  Django REST API + UI     │  Celery worker + Receptor             │ |
|  │  Port 8052 inside pod     │  Runs ansible-runner subprocesses     │ |
|  └──────────────────────────────────────────────────────────────────┘ |
|                  |                         |                           |
|                  v                         v                           |
|  ┌────────────────────┐    ┌─────────────────────────────────────────┐|
|  │ PostgreSQL          │    │ Redis                                   │|
|  │ (StatefulSet)       │    │ Task queue + session cache              │|
|  │ Job history, creds  │    │ (Deployment)                            │|
|  └────────────────────┘    └─────────────────────────────────────────┘|
|                                                                        |
+------------------------------------------------------------------------+
```

The `awx-web` container serves the Django REST API and the React web UI. The `awx-task` container runs Celery workers that pull jobs from the Redis queue, execute ansible-runner subprocesses, and use Receptor for communication with remote execution nodes. PostgreSQL stores all persistent state: job history, encrypted credentials, inventories, templates, and RBAC assignments. Redis provides the task queue and caching layer.

This architecture matters for production resource planning because each component has distinct demands. The web container handles API requests and can be relatively light. The task container needs CPU and memory proportional to concurrent job executions — each running job spawns an ansible-runner subprocess. PostgreSQL needs sufficient IOPS and storage for job artifact retention. Under-provisioning the task container is the most common production failure mode; the symptom is jobs that queue but never start, or jobs that are OOM-killed mid-run.

On a managed Kubernetes service such as EKS or GKE, a minimum production AWX deployment with two task replicas, one web replica, and a PostgreSQL instance using 100 GiB of network storage typically lands on the order of a few hundred US dollars per month in compute and storage — a rough, region- and instance-dependent figure to validate against current cloud pricing rather than a quoted price. The main cost levers are: right-sizing task worker memory based on actual concurrent job counts (profile before provisioning), using preemptible or spot instances for task workers when job interruption is acceptable, and setting aggressive job artifact retention policies in the AWX settings to prevent PostgreSQL storage from growing unbounded over months of job history.

The AWX Operator installs from a kustomization that points to the operator's `config/default` directory at a specific release tag. The install sequence is: deploy the operator, then create an `AWX` CR. The operator reconciles all components from the CR spec.

```bash
# Create the AWX namespace
kubectl create namespace awx

# Deploy AWX Operator 2.19.1 (pairs with AWX 24.6.1)
# The upstream config/manager/kustomization.yaml ships with newTag: latest even at a tagged
# ref — a direct `kubectl apply -k github.com/...?ref=2.19.1` deploys :latest, not 2.19.1.
# Use a local overlay to pin the manager image to the release tag.
# code-verified-against: ansible/awx-operator tag 2.19.1 config/manager/kustomization.yaml
mkdir awx-operator-overlay
cat > awx-operator-overlay/kustomization.yaml <<'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: awx
resources:
  - github.com/ansible/awx-operator/config/default?ref=2.19.1
images:
  - name: quay.io/ansible/awx-operator
    newTag: "2.19.1"
EOF

kubectl apply -k awx-operator-overlay/

# Wait for the operator controller to become available
kubectl rollout status deployment/awx-operator-controller-manager \
  -n awx \
  --timeout=300s
```

After the operator is running, create the AWX instance CR. The minimal spec sets the service type. Additional fields control hostname, ingress, storage class, and resource requests. AWX requires persistent volumes for PostgreSQL data and for the projects directory shared between the web and task containers.

```yaml
# awx-instance.yaml
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx-instance
  namespace: awx
spec:
  service_type: NodePort
  nodeport_port: 30080
  # PostgreSQL storage — requires dynamic provisioning
  postgres_storage_class: standard
  postgres_storage_requirements:
    requests:
      storage: 8Gi
  # Projects directory shared between web and task Pods
  projects_persistence: true
  projects_storage_class: standard
  projects_storage_access_mode: ReadWriteOnce
```

Applying this CR and waiting for convergence takes several minutes on a first install. PostgreSQL must initialize its data directory, Django migrations must run, and the superuser account must be seeded. The AWX Operator publishes the admin password as a Kubernetes Secret named `<instance-name>-admin-password` in the same namespace.

```bash
kubectl apply -f awx-instance.yaml

# Watch the AWX CR status — cycles Pending → Running → Ready
kubectl get awx -n awx -w

# Retrieve the admin password once the instance is Ready
kubectl get secret awx-instance-admin-password \
  -n awx \
  -o jsonpath='{.data.password}' | base64 -d && echo
```

Pause and predict: the AWX Operator reconciles the AWX stack using the same pattern you learned in Module 7.12. If the `awx-instance-admin-password` Secret does not exist after the operator finishes, where do you look first — the AWX CR status, the operator controller logs, or the PostgreSQL Pod events? The AWX CR status is the right first stop: the operator writes phase information and error reasons there. If the status is stuck in Pending, operator controller logs are the second stop, not the PostgreSQL events.

## AAP, AWX, and Standalone Ansible Operator — Decision Matrix

Red Hat ships three overlapping products in the Ansible automation space, and the overlap confuses teams deciding what to run on their platform clusters. Understanding the relationship between them prevents expensive re-architecture later.

**AWX** is the open-source upstream project for the Ansible Automation Platform controller. It is community-supported, released frequently, and carries no licensing fees. AWX provides the full automation controller feature set — job templates, inventories, credentials, RBAC, schedules, workflow templates, notifications, and webhooks — at the cost of community-only support. Teams that can accept community support and want the latest upstream features with the flexibility to contribute back should consider AWX.

**Ansible Automation Platform (AAP)** is Red Hat's enterprise product built on AWX. It adds support contracts, extended maintenance windows, validated content collections, Automation Hub (a private content repository), Insights integration, and a certified container image supply chain. AAP also includes the EDA Controller as a managed component, removing the need to self-operate eda-server. Teams with Red Hat support contracts, regulated industry requirements, or Red Hat OpenShift as their platform should use AAP rather than AWX.

**Standalone Ansible Operator** (the Operator SDK pattern from Module 7.12) is a single Kubernetes controller that reconciles a specific CRD using Ansible roles. It has no UI, no shared credential vault, no team RBAC, and no audit log beyond container logs. Its strength is tight Kubernetes integration: it reacts to watch events, owns child resources, publishes CR status, and participates in controller-runtime lifecycle management. It is stateless, lightweight, and straightforward to reason about for a focused CRD domain.

| Dimension | AAP | AWX | Standalone Operator |
|---|---|---|---|
| **Licensing** | Subscription-based | Open-source (Apache 2.0) | Open-source (Apache 2.0) |
| **Support** | Red Hat enterprise SLA | Community only | Community only |
| **Web UI** | Full automation controller UI | Same UI, community-maintained | None |
| **Audit log** | Job history, activity stream, RBAC log | Job history, activity stream | Container logs only |
| **Team RBAC** | Organizations, teams, role-based access | Same | Kubernetes RBAC only |
| **Credentials** | Vault integration, 30+ built-in types | Same types (community-maintained) | k8s Secrets, env vars |
| **Inventory** | Dynamic plugins, smart inventories | Same plugins | In-cluster service account |
| **EDA** | EDA Controller (managed, supported) | Self-deploy eda-server | Not applicable |
| **Execution nodes** | Mesh topology with Receptor | Same architecture | In-pod ansible-runner |
| **K8s integration** | Kubernetes credential type, k8s inventory | Same | Native controller-runtime |
| **Scale** | Large multi-cluster fleets | Small to medium fleets | One CRD domain per operator |
| **Deployment complexity** | High (procurement + deployment) | Medium (AWX Operator) | Low (operator-sdk scaffold) |
| **Time to first output** | Weeks (procurement) | Hours (AWX Operator on kind) | Minutes (sdk scaffold) |

The practical decision rule is:

- **Choose standalone Ansible Operator** when you need a single CRD reconciled by Ansible logic, you have no need for a shared UI or audit trail, and the team can express the domain entirely in roles that run safely inside a controller process.
- **Choose AWX** when you need a shared automation controller for multiple teams or clusters, want job-level audit history, need credential management beyond k8s Secrets, or need event-driven automation spanning more than one namespace.
- **Choose AAP** when you have a Red Hat support contract, operate in a regulated environment, use Red Hat OpenShift, or need Automation Hub and the managed EDA Controller as enterprise-supported components.

These patterns are not mutually exclusive. Many mature platform teams run standalone operators for CRD-specific reconciliation while also running AWX or AAP for shared day-two job templates and event-driven workflows. The integration point is the AWX REST API: an Ansible Operator role can call the AWX `/api/v2/job_templates/{id}/launch/` endpoint to delegate a complex job to the centralized controller rather than running it inline.

## Event-Driven Ansible on Kubernetes

Event-Driven Ansible is a different execution model from the traditional push-or-poll Ansible approach. Instead of running a playbook on a schedule or on human demand, EDA subscribes to event sources continuously, applies rule conditions to each incoming event, and executes configured actions when conditions match. The action might be a playbook run, a job template launch in AWX, an Ansible module invocation, or a debug output for testing.

The core artifact in EDA is the **rulebook**. A rulebook is a YAML file that declares one or more rule sets, each containing sources, rules, conditions, and actions. The structure is intentionally readable: a source generates events, rules decide what each event means, and actions decide what to do about it.

<!-- code-verified-against: ansible/event-driven-ansible v2.12.0 event_source plugins — no upstream k8s source exists; see https://github.com/ansible/event-driven-ansible/tree/main/extensions/eda/plugins/event_source/ -->

> **Note on Kubernetes event sources**: As of `ansible.eda` 2.12.0, no upstream Kubernetes watch source plugin exists. The verified source list is: `alertmanager`, `aws_cloudtrail`, `aws_sqs_queue`, `azure_service_bus`, `file`, `file_watch`, `generic`, `journald`, `kafka`, `pg_listener`, `range`, `tick`, `url_check`, `webhook`. The recommended pattern uses `ansible.eda.webhook` as the EDA receiver combined with a separate Kubernetes informer process that watches the API and POSTs structured events to the webhook endpoint. (The community collection `sabre1041.eda` provides an experimental Kubernetes source, but it is not part of the upstream release.)

The two-component pattern separates responsibilities cleanly: a Kubernetes-native informer Deployment holds cluster credentials and watch logic; the EDA rulebook holds event evaluation logic and remains cluster-agnostic — multiple informers from different clusters can POST to the same webhook endpoint.

```yaml
# pod-monitor.yml — webhook-based Kubernetes event integration
# code-verified-against: ansible/event-driven-ansible v2.12.0 sources
---
- name: Kubernetes pod monitoring ruleset
  hosts: all
  sources:
    - ansible.eda.webhook:
        host: 0.0.0.0
        port: 5001
  rules:
    - name: Detect OOM-killed containers
      condition: >
        event.payload.event_type is defined and
        event.payload.event_type == "MODIFIED" and
        event.payload.reason is defined and
        event.payload.reason == "OOMKilled"
      action:
        run_job_template:
          name: "investigate-oom-event"
          organization: "Default"
          job_args:
            extra_vars:
              pod_name: "{{ event.payload.pod_name }}"
              namespace: "{{ event.payload.namespace }}"
              node: "{{ event.payload.node }}"
```

The companion Kubernetes informer translates watch events into structured POST payloads. Deployed as a Deployment with a service account that has `get`, `list`, and `watch` on Pods in the target namespaces:

```python
# pod-event-forwarder.py — deployed as a Kubernetes Deployment
# Watches Pods with a label selector and POSTs structured events to the EDA webhook.
import os, requests
from kubernetes import client, config, watch

config.load_incluster_config()
v1 = client.CoreV1Api()
EDA_WEBHOOK_URL = os.environ["EDA_WEBHOOK_URL"]  # http://rulebook-runner-svc.eda-lab:5001/

for event in watch.Watch().stream(
    v1.list_pod_for_all_namespaces,
    label_selector="app.kubernetes.io/part-of=payments"
):
    pod = event["object"]
    for cs in (pod.status.container_statuses or []):
        if cs.last_state and cs.last_state.terminated:
            requests.post(EDA_WEBHOOK_URL, json={
                "event_type": event["type"],
                "pod_name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "node": pod.spec.node_name,
                "reason": cs.last_state.terminated.reason,
            }, timeout=5)
```

The `label_selector` in the forwarder limits which Pods the informer watches — this performs the equivalent of server-side label filtering, keeping event volume low before events reach the rule engine. Different informer Deployments can use different selectors to target different teams or tiers without changing the rulebook.

The `ansible.eda.webhook` source populates `event.payload` with the POST body dictionary. The rule condition navigates those fields. It must guard against missing keys — a Pod MODIFIED event with no container restart status yet does not include `reason` — and must be specific enough to match only events that require action. A condition that fires on every `event_type == "MODIFIED"` without a specific status field check floods the action queue exactly as a broad condition on any source does.

```text
EVENT FLOW IN EDA (webhook + Kubernetes informer pattern)

 Kubernetes Side                               EDA Side
──────────────────────────────────────────    ──────────────────────────────────────
                                              
 k8s watch API ──event──▶  Pod informer ──HTTP POST──▶  ansible.eda.webhook
 (label_selector filter)   (forwarder)    (structured       source → Rule Engine
                                           payload)               │
                                                                   ▼
                                                          event.payload.reason
                                                          == "OOMKilled"?
                                                               │ No ──▶ discard
                                                               │ Yes
                                                               ▼
                                                        run_job_template ──▶ AWX job launch
                                                        "investigate-oom-event"
```

Throttling applies to webhook-sourced rulebooks exactly as it applies to any source. Ansible-rulebook's `throttle` modifier limits how frequently the same rule can fire for the same resource:

```yaml
      action:
        run_job_template:
          name: "investigate-oom-event"
          organization: "Default"
          throttle:
            once_within: 5m
            group_by_attributes:
              - event.payload.pod_name
              - event.payload.namespace
```

The `once_within: 5m` clause suppresses duplicate firings for the same `(pod_name, namespace)` tuple within a five-minute window. Without throttle, a Pod that OOM-kills and restarts repeatedly generates a POST for every restart cycle, launching a job per restart rather than once per incident.

The **EDA Controller** (eda-server) is the managed service that runs rulebooks persistently, tracks activations, provides a web UI for managing rulebook deployments, and integrates with AWX for job template launches. On a cluster running AWX without AAP, you can deploy eda-server from the `ansible/eda-server` repository, though the deployment requires more manual configuration than the AWX Operator because eda-server is not yet packaged as a Kubernetes Operator with the same install convenience. Teams running AAP get the EDA Controller as a managed, supported component.

The lightweight path for learning the event model is to run `ansible-rulebook` directly in a Kubernetes Deployment. This does not provide multi-rulebook management, HA, or audit, but it is sufficient for understanding the event flow before committing to the full EDA Controller.

```yaml
# rulebook-runner.yaml — learning use only, not production HA
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rulebook-runner
  namespace: eda-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rulebook-runner
  template:
    metadata:
      labels:
        app: rulebook-runner
    spec:
      serviceAccountName: eda-runner-sa
      containers:
        - name: rulebook-runner
          image: quay.io/ansible/eda-server:latest
          command:
            - ansible-rulebook
            - --rulebook
            - /rules/pod-monitor.yml
            - --inventory
            - /inventory/hosts.yml
            - --verbose
          ports:
            - containerPort: 5001
              protocol: TCP
          volumeMounts:
            - name: rulebooks
              mountPath: /rules
            - name: inventory
              mountPath: /inventory
      volumes:
        - name: rulebooks
          configMap:
            name: pod-monitor-rulebook
        - name: inventory
          configMap:
            name: eda-inventory
---
# Service so the Kubernetes informer forwarder can POST events to the webhook source
apiVersion: v1
kind: Service
metadata:
  name: rulebook-runner-svc
  namespace: eda-lab
spec:
  selector:
    app: rulebook-runner
  ports:
    - port: 5001
      targetPort: 5001
```

In the webhook-based pattern, the rulebook runner Deployment itself does not need Kubernetes API access — it only listens for HTTP POSTs. The companion informer forwarder Deployment (which watches the k8s API and POSTs events) needs `get`, `list`, and `watch` on the resource kinds it monitors. For Pod monitoring, the forwarder service account needs the `pods` verb in the target namespaces; for node-level monitoring, `nodes` at cluster scope.

Pause and predict: the webhook-based pattern has two separate authentication contexts — the Kubernetes informer forwarder uses its in-cluster service account token to watch the API, and the rulebook's `run_job_template` action uses an AWX API token to launch jobs. What happens if either credential expires mid-run? The forwarder exits with an API authentication error and stops POSTing events; the rulebook keeps running but receives no new events until the forwarder restarts. The AWX API call fails if the token is revoked, and the `run_job_template` action returns a 401 error that ansible-rulebook logs as a rule action failure. Design credential rotation and restart policies for both the informer and the rulebook Deployment before deploying to production.

## Webhook Integration: Alertmanager, GitHub Actions, and Argo Events

AWX exposes webhook endpoints for job templates through its REST API. Any system that can send an HTTP POST can trigger a job template launch, pass extra variables, and receive the job ID in the response. This makes AWX a compatible target for monitoring systems, CI/CD pipelines, and event routers without requiring them to understand Ansible internals.

The AWX webhook URL for a job template follows the pattern:

```
POST /api/v2/job_templates/{id}/launch/
Authorization: Bearer <your-api-token-here>
Content-Type: application/json

Body: {"extra_vars": {"key": "value"}, "limit": "hostname"}
```

AWX validates that the caller's token has permission to launch the specific template before accepting the request, and it returns HTTP 201 with the new job object including the job ID.

**Alertmanager to AWX**: Prometheus Alertmanager routes alerts to a generic webhook receiver that POSTs the alert payload to a configured URL. AWX does not natively parse Alertmanager's JSON schema, so the cleanest integration is an EDA rulebook with the `ansible.eda.alertmanager` source. The rulebook receives the alert payload from Alertmanager, maps the alert fields to AWX extra_vars in the rule action, and invokes the job template directly. This keeps the translation logic in Ansible's domain.

The `ansible.eda.alertmanager` source plugin binds to port 5000 by default. In production, front the endpoint with TLS termination (Ingress with TLS, or service mesh mTLS) so the webhook token is not transmitted in cleartext; the `http://` URL in the example is for in-cluster lab use only.

```yaml
# Alertmanager receiver configuration pointing at EDA webhook listener
# Production: use https:// with TLS termination at Ingress or service mesh layer
# code-verified-against: ansible.eda alertmanager source default port 5000
receivers:
  - name: eda-webhook-receiver
    webhook_configs:
      - url: http://eda-webhook-svc.eda-lab.svc.cluster.local:5000/endpoint
        send_resolved: false
        http_config:
          authorization:
            type: Bearer
            credentials: <your-webhook-auth-token-here>
```

An EDA rulebook receiving this alert can extract `event.payload.alerts[0].labels.alertname`, `event.payload.alerts[0].labels.namespace`, and `event.payload.alerts[0].annotations.summary` to build a precise job template invocation with the right scope and context.

**GitHub Actions to AWX**: A CI workflow can call the AWX REST API to trigger a deployment job template at the end of a build, on a release tag push, or when a PR label changes. The workflow passes the relevant context as extra_vars.

```yaml
# .github/workflows/trigger-awx-deploy.yml (relevant step only)
- name: Trigger AWX deployment job template
  run: |
    curl -s -X POST \
      -H "Authorization: Bearer ${{ secrets.AWX_API_TOKEN }}" \
      -H "Content-Type: application/json" \
      -d "{\"extra_vars\": {\"release_tag\": \"${{ github.ref_name }}\", \"target_env\": \"staging\"}}" \
      "https://awx.example.com/api/v2/job_templates/15/launch/"
```

The secrets reference in the workflow (`secrets.AWX_API_TOKEN`) should be a scoped OAuth2 Application token created in AWX for this integration, not the admin password. The token can be rotated without changing every workflow.

**Argo Events to ansible-rulebook**: Argo Events is a Kubernetes-native event framework that aggregates events from dozens of sources and routes them to sensors. An Argo Events sensor with an HTTP trigger can POST structured payloads to a rulebook's webhook source endpoint, or directly to the AWX REST API. This combination allows Argo Events to aggregate multi-source signals — GitHub webhooks, Kafka messages, S3 bucket notifications, Kubernetes events — and route them to Ansible automation as a unified dispatch layer.

The operational concern shared by all webhook integrations is authentication and scope. AWX API tokens for machine-to-machine integrations should use OAuth2 Application tokens rather than personal tokens, so they can be rotated independently and scoped to specific organizations. Alertmanager webhook targets must validate that requests carry the expected authorization header; if the endpoint is reachable without authentication, any actor who discovers it can trigger job launches. Wrapping the webhook endpoint behind an Ingress with authentication middleware or a service mesh with mTLS adds a meaningful defense layer.

## Credential Management: Vault, k8s Secrets, and Tower Credential Types

Credential management is one of the primary reasons to run AWX rather than standalone operators. AWX encrypts credentials at rest using a fernet key, decrypts them into environment variables or temporary files during job execution, and never exposes the plain-text values through the API after initial creation. This means job templates can use cloud provider keys, SSH private keys, and API tokens without the playbook author ever seeing those secrets in variable files or environment dumps.

AWX ships with more than thirty built-in credential types covering SSH machine access, source control authentication, cloud providers, container registries, and Kubernetes clusters. The **Kubernetes or OpenShift API Bearer Token** credential type accepts a service account token and an optional CA certificate. When a job template runs with this credential attached, AWX injects the KUBECONFIG context into the job execution environment so playbook tasks can target the cluster without storing any credentials in the playbook itself.

Creating a Kubernetes credential for AWX requires a service account in the target cluster, a long-lived token Secret, and the appropriate RBAC binding:

```yaml
# awx-job-runner-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: awx-job-runner
  namespace: default
---
apiVersion: v1
kind: Secret
metadata:
  name: awx-job-runner-token
  namespace: default
  annotations:
    kubernetes.io/service-account.name: awx-job-runner
type: kubernetes.io/service-account-token
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: awx-job-runner-view
subjects:
  - kind: ServiceAccount
    name: awx-job-runner
    namespace: default
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

After applying these resources, retrieve the token and CA certificate:

```bash
# Base64-encoded CA cert (paste into AWX credential form)
kubectl get secret awx-job-runner-token \
  -n default \
  -o jsonpath='{.data.ca\.crt}'

# Plain-text service account token (paste into AWX credential form)
kubectl get secret awx-job-runner-token \
  -n default \
  -o jsonpath='{.data.token}' | base64 -d
```

> **Token currency note**: the `type: kubernetes.io/service-account-token` Secret above mints a *long-lived, non-expiring* service-account token. Since Kubernetes 1.24 these are no longer auto-created, and for in-cluster workloads short-lived **bound** tokens issued through the TokenRequest API (or projected service-account-token volumes) are the modern, more secure default. A long-lived Secret token remains the pragmatic option for an *external* consumer like AWX that cannot mount a projected volume — but treat it as a credential to scope tightly and rotate on a schedule, not a set-and-forget value.

The **custom credential type** feature allows AWX administrators to define credential schemas with typed input fields and injectors that map those fields to environment variables or temporary files. A team that uses a proprietary secret manager, a custom OIDC flow, or a non-standard token format can model it as a custom credential type and grant teams permission to use credentials of that type without exposing the raw secrets.

**HashiCorp Vault integration** in AWX works through the `community.hashi_vault` collection combined with a custom credential type. The credential type stores a Vault AppRole role ID and secret ID; the injector calls the Vault API to fetch the target secret and writes it to an environment variable before the playbook runs. The Secrets Manager Plugin model in AAP formalizes this with a configurable pluggable lookup backend, but AWX achieves the same result with a custom credential type and a pre-task that fetches secrets from Vault before the main playbook logic begins.

The distinction between **static** and **dynamic** Vault secrets matters for how credentials appear in AWX job execution. A static Vault secret is a key-value pair stored at a Vault path that remains valid until explicitly rotated. AWX fetches it at job start via the custom credential type's injector, writes it to an environment variable, and runs the playbook. If the secret is rotated in Vault between job launches, the next launch picks up the new value automatically — no AWX credential object needs updating. A dynamic secret, generated by Vault's database secrets engine or PKI engine, is issued per-request with a short TTL and revoked automatically. For AWX job templates targeting databases, the dynamic approach is preferable: the credential is valid only for the job's duration, it is automatically cleaned up even if the playbook crashes, and Vault's audit log records every issuance independently. The custom credential type's injector for dynamic secrets calls the Vault API, retrieves the lease ID and credential value, and writes both to environment variables; the playbook can optionally renew the lease if the job runs longer than the initial TTL.

**External Secrets Operator (ESO) vs Sealed Secrets** are the two dominant patterns for injecting secrets into Kubernetes workloads managed through GitOps pipelines, and both interact differently with AWX. ESO watches `ExternalSecret` custom resources and syncs values from external stores — Vault, AWS Secrets Manager, GCP Secret Manager — into native Kubernetes Secrets on the cluster. AWX operator Pods can then mount those Secrets as environment variables, keeping the AWX deployment itself GitOps-managed without storing any sensitive values in the Git repository. Sealed Secrets encrypts the raw secret value in the repository using a cluster-specific public key, producing a `SealedSecret` object that only the Sealed Secrets controller on that cluster can decrypt. Sealed Secrets is simpler operationally (no external dependency) but harder to rotate at scale: each rotation requires re-encrypting and committing a new `SealedSecret`. ESO handles rotation automatically by polling the external store, making it better suited for high-rotation environments such as Vault dynamic secrets with short TTLs.

For standalone operators, the credential story is simpler but less centralized. The operator service account has whatever permissions the ClusterRole grants, and sensitive values live in Kubernetes Secrets mounted as environment variables or files in the operator Pod. This works well for single-cluster scenarios but creates a proliferation of individual Secrets across clusters that no single team can audit as a cohesive inventory.

## Kubernetes Inventory Plugins

AWX job templates execute Ansible against an inventory of hosts. For Kubernetes-centric automation, the hosts are often not traditional SSH-reachable servers; they are Kubernetes resources — nodes, namespaces, Pods with labels — or abstract targets representing cluster-level concepts.

> **Note**: The `kubernetes.core.k8s` inventory plugin was removed in `kubernetes.core` v6.0.0 (latest: v6.4.0). The recommended replacement is the `kubernetes.core.k8s_info` module combined with `ansible.builtin.add_host`, which builds dynamic in-memory host groups within the playbook itself.
<!-- code-verified-against: kubernetes.core collection changelog v6.0.0 — k8s inventory plugin removed; use kubernetes.core.k8s_info + ansible.builtin.add_host -->

The `k8s_info + add_host` pattern queries the cluster at job execution time using the Kubernetes credential attached to the template and builds host groups from resource metadata in a pre-task play:

```yaml
# dynamic-k8s-inventory.yml — inline inventory pattern replacing the removed kubernetes.core.k8s plugin
# code-verified-against: kubernetes.core v6.4.0 docs
- name: Build dynamic Kubernetes inventory
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Query pods with team label
      kubernetes.core.k8s_info:
        kind: Pod
        label_selectors:
          - "team = payments"
          - "env = production"
      register: payment_pods

    - name: Add pods to dynamic group
      ansible.builtin.add_host:
        name: "{{ item.metadata.name }}"
        groups: label_team_payments
        pod_namespace: "{{ item.metadata.namespace }}"
        pod_node: "{{ item.spec.nodeName }}"
        pod_labels: "{{ item.metadata.labels }}"
      loop: "{{ payment_pods.resources }}"

- name: Operate on payment pods
  hosts: label_team_payments
  gather_facts: false
  tasks:
    - name: Process pod
      ansible.builtin.debug:
        msg: "Processing {{ inventory_hostname }} on node {{ pod_node }}"
```

A playbook targeting the `label_team_payments` group operates on exactly the Pods with `team: payments` labels, without hardcoding hostnames or namespace lists. The `k8s_info` query runs at job start so the inventory reflects cluster state at execution time.

For targeted fact gathering within a playbook rather than via a full inventory source, the `kubernetes.core.k8s_info` module queries resources on demand. A role that needs to know all failing Pods before deciding which certificates to rotate can look them up inline:

```yaml
- name: Gather all nodes and check readiness
  kubernetes.core.k8s_info:
    kind: Node
  register: cluster_nodes

- name: Report nodes not in Ready state
  ansible.builtin.debug:
    msg: "Node {{ item.metadata.name }} is not Ready — investigate before proceeding"
  loop: "{{ cluster_nodes.resources }}"
  when: >
    not (
      item.status.conditions
      | selectattr('type', 'eq', 'Ready')
      | map(attribute='status')
      | first == 'True'
    )
```

This in-playbook query pattern is particularly useful in AWX job templates that perform pre-flight checks before destructive or time-sensitive operations, because it lets the playbook abort early with a clear message if the cluster is in a degraded state.

## Operator-as-AWX-Job vs Operator-as-Standalone Pattern

Once both an Ansible Operator and AWX are running in your platform, a recurring design question appears: should a particular reconciliation task run inline in the operator, or should the operator delegate it to AWX as a job template launch? There is no universal answer, but the decision factors are consistent.

The **operator-as-standalone** pattern keeps all reconciliation logic inside the controller process. The role runs in the operator Pod, converges child resources, and publishes status. This is the right choice when the reconciliation is fast, repeatable, idempotent, and tightly coupled to the custom resource lifecycle — the CR was created, update its children, report Ready. It is also the right choice when the automation must happen synchronously with the Kubernetes event and waiting for an AWX job queue is unacceptable.

The **operator-as-AWX-job** pattern delegates heavy or complex work to AWX. The operator role calls the AWX REST API to launch a job template, stores the job ID in the CR status, and either polls for completion or writes a pending status and returns. The AWX job runs with shared credentials, a managed inventory, an audit log, and potentially parallel execution nodes. This is the right choice when the automation is long-running, requires human-readable audit trails, involves shared credentials managed by multiple teams, or benefits from AWX's notification and approval workflow features.

| Factor | Stay in-operator | Delegate to AWX |
|---|---|---|
| **Execution time** | Seconds to low minutes | Minutes to hours |
| **Credentials needed** | In-cluster service account | External APIs, multi-cluster, cloud providers |
| **Audit requirement** | Kubernetes events and logs are enough | Job history, approval records required |
| **Team ownership** | Platform team owns the role | Multiple teams need to run or modify the job |
| **Idempotency** | Fully idempotent, safe to re-run frequently | Idempotent but heavy (DB migration, cert rotation) |
| **Approval gate** | Not required | AWX workflow approval step is needed |
| **Failure handling** | CR status and operator logs | AWX job failure notifications and retry UI |

Calling AWX from an operator role uses the `uri` module against the job template launch endpoint. Store the AWX job ID in the CR status so users and other automation can track the running job:

```yaml
- name: Launch AWX job template for certificate rotation
  ansible.builtin.uri:
    url: "https://{{ awx_host }}/api/v2/job_templates/{{ cert_rotation_template_id }}/launch/"
    method: POST
    headers:
      Authorization: "Bearer {{ awx_api_token }}"
      Content-Type: application/json
    body_format: json
    body:
      extra_vars:
        target_namespace: "{{ ansible_operator_meta.namespace }}"
        cert_name: "{{ ansible_operator_meta.name }}"
    status_code: 201
  register: awx_job_launch

- name: Update CR status with AWX job reference
  operator_sdk.util.k8s_status:
    api_version: certs.example.com/v1
    kind: CertRotation
    name: "{{ ansible_operator_meta.name }}"
    namespace: "{{ ansible_operator_meta.namespace }}"
    status:
      phase: Delegated
      awxJobId: "{{ awx_job_launch.json.id }}"
      awxJobUrl: "https://{{ awx_host }}/#/jobs/playbook/{{ awx_job_launch.json.id }}"
```

The operator returns after writing the Delegated status. A future reconcile cycle can inspect the AWX job status via a follow-up `uri` GET call and update the CR status to Complete or Failed once the AWX job finishes.

The **observability difference** between the two patterns is significant in practice. When reconciliation runs inline in the operator, the only visible output is the controller's container logs and the CR status conditions. A failed task produces a cryptic log line and a CR status message that may not survive log rotation. When reconciliation is delegated to AWX, the job run is stored permanently in AWX's PostgreSQL with full playbook stdout, task timing, variable values (excluding secrets), and the identity of which credential and template were used. Engineers on call can review the exact output of a failed rotation job days after it happened, replay it manually with different variables, and share a link to the job URL directly with the certificate authority team — none of which is possible with operator log lines.

**Debugging** the delegation pattern requires checking two systems rather than one. A CR stuck in `Delegated` phase means either the AWX job is still running, it failed silently, or the AWX job ID stored in the CR status is for a job from a previous reconcile cycle that was never cleaned up. The debugging sequence is: read `status.awxJobId` from the CR, call `GET /api/v2/jobs/{id}/` on the AWX API to check `status` and `failed`, inspect the job's stdout via `GET /api/v2/jobs/{id}/stdout/?format=txt` if failed, and update the CR status manually if the state machine is stuck.

The **escape hatch** when AWX is unavailable — planned maintenance, a failed upgrade, or a network partition — is to temporarily patch the operator's ConfigMap to disable the delegation path and run the rotation logic inline. Every delegated role should carry a `awx_delegation_enabled` variable, defaulting to `true`, that short-circuits the delegation block and runs the full task inline when set to `false`. This escape hatch lets the operator function in degraded mode without requiring a code change or a rollout, and it can be re-enabled by patching the ConfigMap once AWX recovers.

## Production Deployment Considerations

Running AWX in production on Kubernetes requires decisions beyond the basic Operator install. The four most critical are persistent storage, PostgreSQL backup, execution scaling, and upgrade strategy.

**Persistent storage** is non-negotiable for production. AWX's PostgreSQL instance holds encrypted credentials, job history, inventory data, and RBAC assignments. A PVC deletion wipes everything. Use a storage class backed by network storage — EBS gp3, GCE Persistent Disk, Azure Managed Disk, or Ceph — rather than a `local-path` provisioner that disappears when the node is replaced. Size generously: job artifacts and log content accumulate steadily, and resizing a PostgreSQL PVC without downtime requires careful planning.

**PostgreSQL backup** is AWX's most common production failure mode. Teams deploy AWX, accumulate months of job history and carefully managed credentials, lose a node or misconfigure a PVC, and discover they have no backup. The AWX Operator does not ship a backup CronJob. A practical approach is a CronJob using `pg_dump` against the AWX PostgreSQL service, encrypting the dump, and pushing it to object storage:

```yaml
# awx-postgres-backup.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: awx-postgres-backup
  namespace: awx
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: pg-backup
              image: postgres:16-alpine
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h awx-instance-postgres-svc \
                    -U awx \
                    -d awx \
                    > /backup/awx-$(date +%Y%m%d-%H%M).sql
              env:
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: awx-instance-postgres-configuration
                      key: password
              volumeMounts:
                - name: backup-vol
                  mountPath: /backup
          volumes:
            - name: backup-vol
              persistentVolumeClaim:
                claimName: awx-backup-pvc
```

Back up the `awx-instance-secret-key` Secret alongside the database dump. This Secret contains the fernet encryption key; without it, a restored database is unreadable even if all the data is intact.

**Scaling execution workers** uses the `task_replicas` field in the AWX CR. Each replica is a separate Celery worker that pulls jobs from the Redis queue independently. Adding replicas increases throughput for concurrent jobs. Monitor PostgreSQL connection counts and Redis memory as you scale — the database and Redis become the bottleneck before the workers do.

```yaml
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx-instance
  namespace: awx
spec:
  service_type: NodePort
  task_replicas: 3
  web_replicas: 2
  task_resource_requirements:
    requests:
      cpu: 500m
      memory: 2Gi
    limits:
      cpu: "2"
      memory: 4Gi
```

**Backup recovery testing** is the step that most teams skip and then regret. The backup CronJob above writes a dump file, but a dump that has never been restored is an unknown quantity. Schedule a quarterly recovery drill: spin up a fresh PostgreSQL instance from the latest dump, apply the `awx-instance-secret-key` Secret to a fresh AWX install pointing at the restored database, and verify that at least one non-trivial credential decrypts correctly and that job history is accessible. The drill catches three classes of failure: dumps that are structurally valid but contain schema-version drift incompatible with the new AWX version, the `secret-key` Secret backup being out of sync with the database because the key was rotated after the last backup, and the object storage path or IAM permissions for the backup bucket being misconfigured so the dump file is there but unreadable by the restore job. Set the CronJob backup cadence to daily for production environments that launch jobs continuously, and retain at least two weeks of daily dumps plus one monthly dump per quarter.

**Upgrade rollback strategy** requires planning before the upgrade, not after a failed migration. Before applying an operator version bump, snapshot the PostgreSQL PVC using a VolumeSnapshot if your storage class supports it. The snapshot takes seconds and provides a point-in-time recovery target that is faster than restoring from a `pg_dump` file. If the Django migration fails mid-upgrade — which can happen when a migration touches a large table with millions of job records — the operator may leave AWX in an inconsistent schema state. Rolling back the operator image tag without reverting the database schema produces a different inconsistency. The clean rollback path is: scale the operator down, restore the PVC from the pre-upgrade VolumeSnapshot, scale the operator back up at the previous image tag. Keep the previous operator image tag recorded in a runbook entry before every upgrade.

**PostgreSQL connection pooling** becomes necessary before you hit the `max_connections` ceiling, not after. Each Celery worker in the task container opens a connection pool; three task replicas with a pool size of five each consume fifteen connections plus overhead from the web container. The AWX CR exposes `extra_settings` to tune Django's `DB_OPTIONS`, but the simpler approach is to place PgBouncer in transaction-pooling mode in front of the AWX PostgreSQL Service. PgBouncer multiplexes hundreds of application-level connections onto a small number of server connections, removing the connection-count cap as a bottleneck. The AWX `awx-instance-postgres-svc` Service address becomes the PgBouncer target, and AWX points at the PgBouncer Service. This configuration also absorbs connection surges during rolliing task-pod restarts without spiking `pg_stat_activity` counts.

**Upgrade strategy**: AWX releases frequently. The AWX Operator supports in-place upgrades by updating the operator image tag and re-applying. Read the AWX release notes before upgrading; database migrations run automatically but occasionally require brief downtime, and API version changes can break integrations built against the previous schema.

## Patterns and Anti-Patterns

**Pattern: Inventory groups from Kubernetes labels.** Instead of hardcoding host groups in static inventory files, use the `kubernetes.core.k8s_info` module with `ansible.builtin.add_host` to build dynamic groups from resource labels at job execution time. Teams that apply `team: payments`, `env: production`, or `tier: cache` labels to their workloads can target job templates to `label_team_payments` or `label_env_production` groups without editing static inventory files. As of `kubernetes.core` v6.0.0, this `k8s_info + add_host` pattern replaces the removed `kubernetes.core.k8s` inventory plugin.

**Pattern: Credential-per-cluster.** Register a separate Kubernetes credential in AWX for each cluster the job templates may target. Grant each cluster's service account only the minimum RBAC needed for the job templates it supports. This creates a clean audit trail showing which credential was used for which job, makes credential rotation cluster-by-cluster straightforward, and prevents a compromise of one cluster's credentials from automatically propagating to others.

**Pattern: Rulebook-per-concern.** Keep each EDA rulebook focused on a single monitoring or event concern rather than writing a large rulebook with many source types and dozens of rules. A `pod-oom-rulebook.yml`, `cert-expiry-rulebook.yml`, and `deployment-failure-rulebook.yml` are easier to test, version, and debug independently. Each concern deploys as a separate Deployment with its own ConfigMap, service account, and restart policy.

**Anti-pattern: Catch-all MODIFIED conditions.** Running `ansible-rulebook` with a broad condition like `event.type == "MODIFIED"` on a busy namespace triggers hundreds of job launches per minute because MODIFIED fires for readiness probe state changes, annotation patches, resource version bumps, and container restart count increments. Add specific field checks — targeting an exact status transition or a specific annotation value — and test conditions against a namespace with representative traffic volume before enabling them in production.

**Anti-pattern: Deploying AWX without a backup.** The AWX Operator creates a PostgreSQL StatefulSet that holds all credentials encrypted with a fernet key stored in a Kubernetes Secret. If either the PVC or the Secret is lost without a backup, the credential vault is irrecoverable. Set up the backup CronJob and the Secret export procedure before creating the first job template, not after the first incident.

**Anti-pattern: Using the admin account token for operator-to-AWX calls.** Admin tokens have unlimited access to all AWX resources, cannot be scoped to specific templates, and cannot be rotated independently. Create a named OAuth2 Application token in AWX for each operator that needs to launch job templates, scope it to only the templates that operator uses, store the token in a Kubernetes Secret, and include it in a credential rotation plan.

## Decision Framework

Use this flowchart when a new automation concern arrives and the team must decide where it belongs:

```
Is this automation tightly coupled to a single CRD's lifecycle?
│
├─ Yes → Use standalone Ansible Operator
│         Reconcile child resources from spec, publish CR status,
│         no shared UI or audit trail needed.
│
└─ No: Does the automation need shared credentials, multi-team
        access, a web UI, or a job-level audit log?
        │
        ├─ No → Run ansible-rulebook in a Deployment (event-driven)
        │        or a CronJob (scheduled), no AWX needed.
        │
        └─ Yes: Is there a Red Hat support or compliance requirement?
                │
                ├─ Yes → Use Ansible Automation Platform (AAP)
                │         Managed EDA Controller, validated content,
                │         enterprise SLA, OpenShift-native.
                │
                └─ No → Use AWX
                          │
                          └─ Is the trigger event-driven or reactive?
                              ├─ Yes → Add ansible-rulebook Deployment
                              │        or self-manage eda-server, wire
                              │        rulebooks to AWX job templates.
                              └─ No → AWX job templates with webhooks
                                      or scheduled launches.
```

The pattern you pick today does not have to be permanent. Many teams start with standalone operators to prove a CRD contract, add AWX when the credential and audit requirements outgrow Kubernetes Secrets, and layer EDA on top when they need reactive automation. The custom resource interface is usually more durable than the first implementation layer below it.

## Did You Know?

- AWX 24.6.1 ships paired with AWX Operator 2.19.1. The version pairing is explicit in the AWX release notes because the operator's Ansible roles target specific AWX container image tags. Mismatching operator and AWX image versions can produce failed reconciliation cycles or silent migration errors during upgrades.

- The `ansible.eda` collection reached version 2.12.0 and requires ansible-rulebook 1.0.0 or later. Earlier versions of ansible-rulebook used a significantly different condition expression syntax, so rulebooks written before the 1.0.0 release will not run without modification on a current EDA installation.

- The AWX Operator is itself an Ansible Operator built with Operator SDK. Its `watches.yaml` maps the `AWX` custom resource to Ansible roles that install and configure the AWX application components. Reading the operator's own roles in the `ansible/awx-operator` GitHub repository shows exactly how a production Ansible Operator manages a stateful multi-component application — the patterns from Module 7.12 applied at real scale.

- As of `ansible.eda` 2.12.0, the upstream `ansible/event-driven-ansible` collection ships no Kubernetes watch source plugin. The full upstream source list is `alertmanager`, `aws_cloudtrail`, `aws_sqs_queue`, `azure_service_bus`, `file`, `file_watch`, `generic`, `journald`, `kafka`, `pg_listener`, `range`, `tick`, `url_check`, and `webhook`. Kubernetes-originated events reach EDA via a companion informer that POSTs to `ansible.eda.webhook`. A high-velocity informer (watching `kube-system` during a cluster upgrade) can generate thousands of POSTs per minute; rule conditions are evaluated synchronously in the rulebook engine, so a slow condition expression causes the engine to fall behind the event stream and drop events without warning.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Deploying AWX on `local-path` storage in production | Lab installs work fine; the mistake goes unnoticed until a node is replaced and the PVC is lost | Require a `postgres_storage_class` in the AWX CR that maps to a network-backed StorageClass; reject `local-path` for production in your runbook |
| Backing up only the PostgreSQL data without the fernet key Secret | Teams know to back up databases but miss the `awx-instance-secret-key` Secret that holds the encryption key for all credentials | Include the `awx-instance-secret-key` Secret export in the backup CronJob alongside `pg_dump`; test restoration end-to-end before relying on it |
| Writing rulebook conditions that fire on every MODIFIED event | Developers test on low-traffic namespaces where every MODIFIED event is intentional; production namespaces have orders of magnitude more noise | Test conditions against a namespace that mirrors production event volume; add specific field checks beyond `event.type` before enabling in production |
| Using the AWX admin account token for machine-to-machine calls | Admin tokens always work, so they are used for quick prototypes and never replaced | Create scoped OAuth2 Application tokens in AWX, store them in Kubernetes Secrets, and include rotation in the credential management plan |
| Scaling task replicas without monitoring PostgreSQL connections | Each Celery worker maintains a database connection pool; doubling replicas can exhaust PostgreSQL `max_connections` | Monitor `pg_stat_activity` connection counts before scaling; tune `max_connections` in the PostgreSQL configuration or add PgBouncer as a connection pooler |
| Accessing `event.resource.status` fields on DELETED events | DELETED events do not carry the full resource status; conditions that navigate status subfields throw evaluation errors | Guard status field access with `is defined` checks or narrow the condition with `event.type != "DELETED"` before accessing status paths |
| Registering the job runner with broad RBAC | Getting started quickly favors `cluster-admin`; the permission is never narrowed | Apply least-privilege RBAC from day one: enumerate the namespaces and verbs the job templates actually use, then create a targeted ClusterRole |
| Not pinning the AWX Operator image in the kustomization | Using `?ref=main` OR a tagged `?ref=2.19.1` still deploys `:latest` because `config/manager/kustomization.yaml` ships `newTag: latest` even at a tagged ref (verified at 2.19.1) | Use a local kustomize overlay that pins both the manifests ref and the image tag (`images: - name: quay.io/ansible/awx-operator, newTag: "2.19.1"`); apply from the local overlay directory, not directly from the remote URL |

## Quiz: Self-Check

<details>
<summary>Your team deploys AWX Operator. Three weeks later, a node running the PostgreSQL StatefulSet is terminated and its local disk is lost. After recovery, the AWX web UI accepts login but every job template shows "invalid credential" errors. What most likely happened, and how do you prevent it?</summary>

The PostgreSQL PVC used `local-path` or `hostPath` storage, so the database was wiped when the node's disk was lost. Even if a database dump existed, AWX encrypts all credentials at rest using a fernet key stored in the `awx-instance-secret-key` Kubernetes Secret. If that Secret was also lost, the restored database data is unreadable because the decryption key is gone. The prevention requires two measures: use a network-backed StorageClass for the PostgreSQL PVC so it survives node loss, and include both the `pg_dump` database backup and an export of the `awx-instance-secret-key` Secret in a regular, tested backup procedure. Backing up the database without the encryption key is equivalent to backing up a locked safe without keeping a copy of the key.

</details>

<details>
<summary>You write an EDA rulebook that receives all Pod events from a Kubernetes informer forwarder with the condition `event.payload.event_type == "MODIFIED"`. After enabling it, the AWX job queue fills completely and all job execution stalls. What happened and what are the correct steps to fix it?</summary>

The condition matches every MODIFIED event for every Pod in production. The informer fires for readiness probe state changes, container restart count increments, annotation patches from admission controllers, resource version bumps from the control plane, and label changes from operators. In a busy namespace this generates hundreds of POSTs per minute, each triggering a job template launch. The queue fills faster than workers can drain it. The fix has two parts: first, narrow the condition to the specific state you care about — for example, checking `event.payload.reason == "OOMKilled"` with an `is defined` guard — so only truly actionable events pass the rule. Second, test the refined condition against a namespace with representative production traffic volume before re-enabling, using the `--verbose` flag of ansible-rulebook to observe what fraction of events the condition matches.

</details>

<details>
<summary>An Ansible Operator role needs to rotate a TLS certificate. The rotation involves calling an external PKI API that takes up to 20 minutes to respond, then storing the certificate in a Kubernetes Secret. Should this run inline in the operator or be delegated to AWX? Justify your choice using the decision factors from this module.</summary>

This is a strong candidate for delegation to AWX. A blocking 20-minute wait inside the controller reconcile loop prevents the operator from processing any other events on its work queue during that window. If the operator Pod is restarted during the wait — due to a node drain, a rolling update, or an OOM event — the PKI call is lost and the rotation must start over with no status record showing the attempt. External PKI API credentials are better managed centrally in AWX rather than as individual Kubernetes Secrets per cluster. AWX provides an audit trail showing when the rotation ran, whether it succeeded, and which credential was used — information that is often required for certificate lifecycle compliance. The operator should call the AWX job template launch endpoint, write the AWX job ID to the CR status, and return. A subsequent reconcile cycle can poll the AWX job status and update the CR to Complete or Failed once the PKI call finishes.

</details>

<details>
<summary>A developer proposes using the AWX admin account token as the credential for all operator-to-AWX calls across the platform. What are the specific security and operational risks, and what is the correct approach?</summary>

Using the admin token creates several overlapping problems. Admin tokens carry unlimited access to every AWX resource — any credential leak gives an attacker control over all job templates, every credential in the vault, and all inventory configurations. Because admin tokens cannot be scoped to specific job templates or organizations, you violate least-privilege at the integration level. When the admin password changes (mandatory for compliance in many environments), every operator role referencing the admin token breaks simultaneously, requiring a coordinated update across all clusters. The correct approach is to create a named OAuth2 Application in AWX that represents each operator's identity, generate a scoped application token that allows only the specific job templates the operator needs to launch, store the token in a Kubernetes Secret, mount it as an environment variable in the operator Deployment, and build a credential rotation job template that automatically replaces the token before it expires.

</details>

<details>
<summary>You are evaluating AWX versus AAP for a healthcare platform team that operates six clusters, must satisfy HIPAA audit requirements, runs Red Hat OpenShift, and already holds a Red Hat Enterprise Agreement. Which product should the team choose and why?</summary>

The team should choose Ansible Automation Platform. The existing Red Hat Enterprise Agreement covers the AAP subscription, so there is no additional procurement cost for the automation control plane. HIPAA compliance audits typically require evidence of vendor-supported security controls — documented vulnerability response, CVE tracking, patch SLAs — that AWX's community support cannot provide. Red Hat validates AAP components on OpenShift-specific container runtime and network configurations, while AWX is tested on generic Kubernetes and may require additional work to pass an OpenShift security admission policy. AAP includes the EDA Controller as a supported, managed component, removing the need to self-manage eda-server. AWX remains useful as an experimentation and development platform for evaluating features before they arrive in the supported AAP release, but for six production clusters with regulatory requirements and an active Red Hat contract, AAP is the appropriate choice.

</details>

<details>
<summary>An EDA rulebook's `run_job_template` action fires successfully when a Pod enters a failing state — the AWX job launches and completes — but the Pod continues failing, another MODIFIED event fires, and another job launches. This loop continues indefinitely. How would you prevent runaway launches for the same resource?</summary>

This is an EDA throttling and deduplication problem. The rulebook engine does not natively deduplicate events for the same resource between consecutive rule firings. Several approaches address it. First, refine the condition to match only the first occurrence of the failure state rather than any presence of it: structure the informer forwarder payload to include a `restart_count` field, then match `event.payload.restart_count == 1` instead of `>= 1` so only the transition to the first restart triggers the action. Second, use ansible-rulebook's `throttle` action modifier to limit how frequently the same rule can fire within a time window for the same resource (`group_by_attributes: [event.payload.pod_name, event.payload.namespace]`). Third, design the triggered job template to annotate the Pod with `automation.example.com/investigating: "true"`, then add an exclusion to the rulebook condition: only fire if that annotation is not present. The annotation approach creates a machine-readable and human-readable record directly on the resource that both operators and subsequent automation can observe, and it survives rulebook restarts because the annotation persists in the Kubernetes API.

</details>

## Hands-On Exercise: AWX Operator on kind

This lab deploys AWX using the AWX Operator on a local kind cluster, retrieves the admin password, and registers a Kubernetes credential. AWX requires significant host RAM — plan for at least 6 GB of free memory. The first install takes 10–15 minutes on a laptop-class machine while PostgreSQL initializes and Django migrations run.

### Task 1: Create the kind Cluster

Create a kind cluster with a host port mapping so the AWX NodePort Service is reachable at `http://localhost:8080`.

```bash
cat <<'EOF' > awx-lab-kind.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
    listenAddress: "127.0.0.1"
    protocol: TCP
EOF

kind create cluster --name awx-lab --config awx-lab-kind.yaml
kubectl cluster-info --context kind-awx-lab
```

Confirm the context is `kind-awx-lab` before continuing. All subsequent commands deploy into this cluster.

<details>
<summary>Hint for Task 1</summary>

If `kubectl cluster-info` shows a different context, run `kubectl config use-context kind-awx-lab`. The port mapping in the kind config is what makes the AWX NodePort Service reachable at `localhost:8080` without a separate `kubectl port-forward`.

</details>

### Task 2: Install the AWX Operator

```bash
kubectl create namespace awx

# Deploy AWX Operator 2.19.1
# The upstream config/manager/kustomization.yaml ships newTag: latest even at a tagged ref;
# create a local overlay to pin the image to 2.19.1 explicitly.
# code-verified-against: ansible/awx-operator tag 2.19.1 config/manager/kustomization.yaml
mkdir awx-operator-overlay
cat > awx-operator-overlay/kustomization.yaml <<'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: awx
resources:
  - github.com/ansible/awx-operator/config/default?ref=2.19.1
images:
  - name: quay.io/ansible/awx-operator
    newTag: "2.19.1"
EOF

kubectl apply -k awx-operator-overlay/

# Wait for the operator controller to become available
kubectl rollout status deployment/awx-operator-controller-manager \
  -n awx \
  --timeout=300s

kubectl get pods -n awx
```

You should see the `awx-operator-controller-manager` Pod in Running state. The operator has no AWX application components yet — it is waiting for an `AWX` CR.

<details>
<summary>Hint for Task 2</summary>

If the remote kustomize fetch fails, clone the repository at the release tag and run `kubectl apply -k config/default -n awx` from the cloned directory. Make sure your `kubectl` version supports the `-k` flag natively (kubectl 1.27 or later).

</details>

### Task 3: Create the AWX Instance

```bash
cat <<'EOF' > awx-instance.yaml
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx-instance
  namespace: awx
spec:
  service_type: NodePort
  nodeport_port: 30080
EOF

kubectl apply -f awx-instance.yaml

# Watch the CR status — expect several minutes for the first install
kubectl get awx -n awx -w
```

While waiting, observe the Pods being created:

```bash
kubectl get pods -n awx -w
```

You should see PostgreSQL initialize, followed by the web and task containers starting. The AWX CR status transitions from `Pending` through `Running` before reaching a stable state.

<details>
<summary>Hint for Task 3</summary>

If the PostgreSQL Pod is stuck in `Init:0/1`, check `kubectl get pvc -n awx`. On kind, the `local-path` StorageClass is available by default; if no provisioner is running, check the `local-path-storage` namespace. If the AWX web Pod crashes immediately, inspect its logs for database connection errors — PostgreSQL may need more time to finish initialization.

</details>

### Task 4: Access AWX and Retrieve the Admin Password

```bash
# Retrieve the admin password
kubectl get secret awx-instance-admin-password \
  -n awx \
  -o jsonpath='{.data.password}' | base64 -d && echo

# Confirm the NodePort Service exists on port 30080
kubectl get service awx-instance-service -n awx
```

Open `http://localhost:8080` in a browser and log in with username `admin` and the retrieved password. You should see the AWX dashboard.

<details>
<summary>Hint for Task 4</summary>

If `http://localhost:8080` does not respond, verify the kind container is running with `docker ps | grep awx-lab-control-plane` and that port 8080 is bound on the host. If the service exists but shows a different port than 30080, update the `awx-instance.yaml` `nodeport_port` field and re-apply, or use the actual assigned port in the browser.

</details>

### Task 5: Create a Scoped Service Account and Register a Kubernetes Credential

Create a dedicated service account for AWX job runners and generate a long-lived token Secret.

```bash
kubectl create serviceaccount awx-job-runner -n default

cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: awx-job-runner-token
  namespace: default
  annotations:
    kubernetes.io/service-account.name: awx-job-runner
type: kubernetes.io/service-account-token
EOF

# Grant read access to cluster resources
kubectl create clusterrolebinding awx-job-runner-view \
  --clusterrole=view \
  --serviceaccount=default:awx-job-runner
```

Retrieve the values needed for the AWX credential form:

```bash
# Base64-encoded CA cert — paste into the "CA Certificate" field in AWX
kubectl get secret awx-job-runner-token \
  -n default \
  -o jsonpath='{.data.ca\.crt}'

# Plain-text bearer token — paste into the "API Authentication Bearer Token" field
kubectl get secret awx-job-runner-token \
  -n default \
  -o jsonpath='{.data.token}' | base64 -d

# API server URL reachable from inside the cluster
echo "https://kubernetes.default.svc:443"
```

In the AWX web UI, navigate to **Credentials** → **Add**, select the **Kubernetes/OpenShift API Bearer Token** credential type, and enter:
- Kubernetes API Endpoint: `https://kubernetes.default.svc:443`
- CA Certificate: the base64-decoded cert (paste the raw PEM, not the base64 value)
- API Authentication Bearer Token: the plain-text token

Save the credential and verify the connection using the **Test** button if available.

<details>
<summary>Hint for Task 5</summary>

The API server endpoint for in-cluster access is `https://kubernetes.default.svc:443`, not the external `localhost:PORT` URL that `kubectl cluster-info` shows. The AWX task Pod communicates with the API server through the cluster network, so the in-cluster DNS name is correct. If the credential test fails with a certificate error, confirm that the CA cert field contains the raw PEM text beginning with `-----BEGIN CERTIFICATE-----`, not the base64-encoded form.

</details>

### Task 6: Write a Minimal EDA Rulebook (Stretch)

Install ansible-rulebook locally and run a webhook-based rulebook that fires on incoming HTTP POST events. Use `curl` to simulate a Kubernetes-originated event without needing a full informer forwarder.

```bash
# Install ansible-rulebook locally (Python 3.9+ required)
pip install ansible-rulebook ansible-runner

# Install the EDA collection
ansible-galaxy collection install ansible.eda

# Create the rulebook — uses ansible.eda.webhook (verified in ansible.eda 2.12.0)
# code-verified-against: ansible/event-driven-ansible v2.12.0 sources
cat <<'EOF' > pod-watch-rulebook.yml
---
- name: Log pod events from webhook
  hosts: localhost
  sources:
    - ansible.eda.webhook:
        host: 127.0.0.1
        port: 5001
  rules:
    - name: Log pod creation
      condition: >
        event.payload.event_type is defined and
        event.payload.event_type == "ADDED"
      action:
        debug:
          msg: "New pod created: {{ event.payload.pod_name }} in {{ event.payload.namespace }}"
EOF

# Create a minimal inventory
cat <<'EOF' > localhost-inventory.yml
all:
  hosts:
    localhost:
      ansible_connection: local
EOF

kubectl create namespace eda-lab

# Run the rulebook in the background
ansible-rulebook \
  --rulebook pod-watch-rulebook.yml \
  --inventory localhost-inventory.yml \
  --verbose &

# Wait for the webhook listener to start
sleep 3

# Simulate a Kubernetes pod creation event via curl
curl -s -X POST http://127.0.0.1:5001/ \
  -H "Content-Type: application/json" \
  -d '{"event_type": "ADDED", "pod_name": "test-pod", "namespace": "eda-lab", "node": "kind-worker"}'

# Check the rulebook output — should log the pod name
sleep 2

# Stop the rulebook background process
kill %1 2>/dev/null
```

<details>
<summary>Hint for Task 6</summary>

If `ansible-rulebook` exits immediately, check that port 5001 is not already in use (`lsof -i :5001`). If the `curl` POST returns a connection error, wait an extra second for the webhook listener to bind — the delay between starting `ansible-rulebook` and the webhook source binding the port is typically 1–2 seconds. If the rulebook output shows "received event" but the rule does not fire, verify that the JSON payload keys match the condition field names exactly (`event_type`, not `type`).

</details>

### Task 7: Clean Up

```bash
# Stop any background ansible-rulebook process
kill %1 2>/dev/null

# Remove AWX and the lab namespace
kubectl delete awx awx-instance -n awx
kubectl delete namespace awx eda-lab

# Delete the kind cluster
kind delete cluster --name awx-lab
```

### Success Criteria

- [ ] You deployed the AWX Operator and created an AWX instance that reached a stable running state
- [ ] You retrieved the admin password from the Kubernetes Secret and logged into the AWX web UI
- [ ] You created a dedicated service account, generated a long-lived token Secret, and registered it as a Kubernetes credential in AWX
- [ ] You can articulate when a reconciliation task should run inline in an operator versus be delegated to AWX, citing at least two of the decision factors from this module
- [ ] You described the EDA rulebook structure — sources, rules, conditions, actions — and explained what prevents a MODIFIED condition from triggering runaway job launches
- [ ] You evaluated whether your current or target platform justifies AWX vs AAP vs standalone operator using the decision framework flowchart

## Sources

- https://github.com/ansible/awx-operator
- https://docs.ansible.com/projects/awx/en/latest/
- https://github.com/ansible/awx-operator/blob/devel/docs/installation/basic-install.md
- https://github.com/ansible/awx/releases
- https://github.com/ansible/event-driven-ansible
- https://github.com/ansible/eda-server
- https://github.com/ansible/ansible-rulebook
- https://docs.ansible.com/ansible/latest/collections/kubernetes/core/k8s_module.html
- https://prometheus.io/docs/alerting/latest/configuration/#webhook_config
- https://sdk.operatorframework.io/docs/building-operators/ansible/

## Next Module

Continue with **Module 7.15: Helm vs Ansible Operator Decision Framework** to learn when a Helm-managed application is a better fit than an Ansible role, how the two operator implementation styles compare for package-shaped vs automation-shaped domains, and how to migrate between them as a platform's needs evolve.
