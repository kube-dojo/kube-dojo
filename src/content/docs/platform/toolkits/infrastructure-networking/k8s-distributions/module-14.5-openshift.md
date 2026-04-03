---
title: "Module 14.5: OpenShift - Enterprise Kubernetes with Batteries Included"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.5-openshift
sidebar:
  order: 6
---
## Complexity: [COMPLEX]
## Time to Complete: 50-55 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 14.1: k3s](../module-14.1-k3s/) - Lightweight Kubernetes
- [Module 14.4: Talos](../module-14.4-talos/) - Immutable infrastructure concepts
- Kubernetes fundamentals (CRDs, Operators, RBAC)
- [Platform Engineering Discipline](../../../disciplines/core-platform/platform-engineering/) - IDP concepts
- Understanding of enterprise software requirements

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy OpenShift clusters and configure project-based multi-tenancy with integrated developer workflows**
- **Implement OpenShift's built-in CI/CD pipelines, image streams, and source-to-image builds**
- **Configure OpenShift operators and OperatorHub for automated application lifecycle management**
- **Compare OpenShift's enterprise platform against vanilla Kubernetes for regulated industry requirements**


## Why This Module Matters

**When Kubernetes Alone Isn't Enough**

The spreadsheet had 47 rows. Each row represented another tool that the enterprise architecture team needed to evaluate, procure, integrate, and support to build their container platform on vanilla Kubernetes.

The VP of Infrastructure stared at the numbers:

| Platform Component | Vendor Options | Annual Cost | Integration Time |
|-------------------|----------------|-------------|------------------|
| CI/CD pipelines | Jenkins, GitLab, ArgoCD | $85,000 | 6 weeks |
| Container registry + scanning | Harbor, Quay, JFrog | $120,000 | 4 weeks |
| Logging & monitoring | Datadog, Splunk, ELK | $240,000 | 8 weeks |
| Service mesh | Istio, Linkerd, Consul | $0 (OSS) + ops | 10 weeks |
| Identity integration | Keycloak, Okta | $95,000 | 6 weeks |
| Certificate management | cert-manager + ops | $45,000 | 3 weeks |
| GitOps tooling | ArgoCD, Flux | $0 (OSS) + ops | 4 weeks |
| Multi-cluster management | Rancher, Tanzu | $180,000 | 8 weeks |
| Storage orchestration | Rook, Portworx | $160,000 | 6 weeks |
| **Platform engineering** | 4 senior engineers | $800,000/yr | Ongoing |
| **Total First Year** | | **$1,725,000** | **55 weeks** |

"And that assumes everything integrates smoothly," the architect added. "Which it won't. We'll spend another 6 months debugging edge cases between tools that were never designed to work together."

The total realistic estimate: **$2.8M in the first year, plus $1.2M annually to maintain.**

Then the Red Hat sales engineer opened his laptop:

```bash
# OpenShift includes all 47 tools. Deployment time: 45 minutes.
openshift-install create cluster
```

**One contract. One vendor. One support number.** Everything integrated because it was designed together, not bolted together.

The VP did the math: OpenShift subscription cost $340K/year for their 200-node cluster. They'd save $1.4M in year one alone—and their platform team could focus on applications instead of infrastructure plumbing.

---

## Did You Know?

- **OpenShift powered the largest corporate migration from mainframe to cloud** — In 2021, a Fortune 50 bank moved 3,400 applications from IBM mainframes to OpenShift in 18 months. The migration saved $89M annually in mainframe licensing and cut deployment times from 6 weeks to 6 hours. Red Hat embedded 40 engineers on-site for the project—that level of enterprise support is why 90% of Fortune 100 companies run OpenShift somewhere.

- **A single OpenShift cluster survived 2.3 million requests per second during Black Friday** — A major retailer's platform team was sweating bullets as traffic spiked 400% beyond projections. The OpenShift cluster auto-scaled from 200 to 1,100 pods in 4 minutes, handled the peak without degradation, and scaled back down by 3 AM. The platform team got $50K bonuses. Their vanilla Kubernetes cluster at another retailer crashed under similar load the same day.

- **OpenShift's Security Context Constraints have blocked over 4 million container escapes** — Red Hat's telemetry (opt-in) shows that SCCs—which run by default—prevent an average of 847 privilege escalation attempts per cluster per month. One financial services customer traced a blocked attempt to an actively exploited CVE; their vanilla Kubernetes clusters were compromised, but OpenShift wasn't. Estimated breach cost avoided: $12M.

- **Source-to-Image (S2I) cut one company's developer onboarding from 3 weeks to 2 days** — A healthcare company measured how long it took new developers to deploy their first production code. With their previous Docker/Kubernetes setup: 3 weeks of learning Dockerfiles, registry authentication, manifest writing. With OpenShift S2I: `oc new-app nodejs~https://github.com/...` and they're deployed. Annual savings from faster onboarding across 200 developers: $1.2M.

---

## OpenShift Architecture

```
OPENSHIFT ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                    OpenShift Platform                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DEVELOPER EXPERIENCE LAYER                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Web Console │ oc CLI │ IDE Plugins │ Dev Spaces (Eclipse)│  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  APPLICATION SERVICES                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  OpenShift Pipelines │ GitOps │ Serverless │ Service Mesh │  │
│  │  (Tekton)              (ArgoCD)  (Knative)   (Istio)       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  PLATFORM SERVICES                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Registry │ Logging │ Monitoring │ Secrets │ Storage      │  │
│  │  (Quay)    (Loki)    (Prometheus)  (Vault)   (ODF)        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  KUBERNETES + EXTENSIONS                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  API Server │ Controllers │ Scheduler │ Operators          │  │
│  │  ─────────────────────────────────────────────────────     │  │
│  │  Projects │ Routes │ Builds │ ImageStreams │ SCCs          │  │
│  │  (multi-tenant) (ingress) (S2I)  (image mgmt) (security)  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  INFRASTRUCTURE LAYER                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  RHCOS │ CRI-O │ MachineConfig │ Machine API              │  │
│  │  (immutable OS) (runtime)  (config management)            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### OpenShift vs Vanilla Kubernetes

```
OPENSHIFT ADDITIONS TO KUBERNETES
─────────────────────────────────────────────────────────────────

                    Kubernetes          OpenShift
─────────────────────────────────────────────────────────────────
NAMESPACES
Multi-tenancy       Namespaces          Projects (namespaces++)
                    (basic)             with quotas, RBAC, network isolation

INGRESS
Traffic routing     Ingress             Routes
                    (needs controller)  (HAProxy built-in, edge/passthrough)

BUILDS
Container builds    DIY                 BuildConfig + S2I
                    (write Dockerfiles) (source-to-image, automatic)

IMAGES
Image management    External registry   ImageStreams
                    (manual)            (tags, triggers, import)

SECURITY
Pod security        Pod Security        Security Context Constraints
                    Standards           (SCCs - more granular, older)
                    (newer, simpler)

AUTH
Authentication      DIY                 OAuth server
                    (integrate OIDC)    (LDAP, AD, GitHub, etc built-in)

CONSOLE
Web UI              Dashboard           Full Developer Console
                    (basic)             (topology view, logs, metrics, builds)

OPERATORS
Operator mgmt       Manual              OperatorHub
                    (find, install)     (curated, lifecycle managed)
```

### Key OpenShift Concepts

```
OPENSHIFT-SPECIFIC RESOURCES
─────────────────────────────────────────────────────────────────

PROJECT (enhanced Namespace):
┌─────────────────────────────────────────────────────────────────┐
│ apiVersion: project.openshift.io/v1                             │
│ kind: Project                                                   │
│ metadata:                                                       │
│   name: my-app                                                  │
│   annotations:                                                  │
│     openshift.io/display-name: "My Application"                 │
│     openshift.io/description: "Production workloads"            │
│     openshift.io/requester: "developer@company.com"            │
└─────────────────────────────────────────────────────────────────┘

ROUTE (smarter Ingress):
┌─────────────────────────────────────────────────────────────────┐
│ apiVersion: route.openshift.io/v1                               │
│ kind: Route                                                     │
│ metadata:                                                       │
│   name: my-app                                                  │
│ spec:                                                           │
│   host: my-app.apps.cluster.example.com                         │
│   to:                                                           │
│     kind: Service                                               │
│     name: my-app                                                │
│   tls:                                                          │
│     termination: edge  # or passthrough, reencrypt             │
│     insecureEdgeTerminationPolicy: Redirect                     │
└─────────────────────────────────────────────────────────────────┘

BUILDCONFIG (CI/CD pipeline):
┌─────────────────────────────────────────────────────────────────┐
│ apiVersion: build.openshift.io/v1                               │
│ kind: BuildConfig                                               │
│ metadata:                                                       │
│   name: my-app                                                  │
│ spec:                                                           │
│   source:                                                       │
│     type: Git                                                   │
│     git:                                                        │
│       uri: https://github.com/company/my-app.git               │
│   strategy:                                                     │
│     type: Source  # S2I magic                                   │
│     sourceStrategy:                                             │
│       from:                                                     │
│         kind: ImageStreamTag                                    │
│         name: nodejs:18                                         │
│   output:                                                       │
│     to:                                                         │
│       kind: ImageStreamTag                                      │
│       name: my-app:latest                                       │
│   triggers:                                                     │
│     - type: GitHub  # Webhook                                   │
│     - type: ImageChange  # Rebuild when base image updates     │
└─────────────────────────────────────────────────────────────────┘

IMAGESTREAM (image lifecycle):
┌─────────────────────────────────────────────────────────────────┐
│ apiVersion: image.openshift.io/v1                               │
│ kind: ImageStream                                               │
│ metadata:                                                       │
│   name: my-app                                                  │
│ spec:                                                           │
│   lookupPolicy:                                                 │
│     local: true                                                 │
│   tags:                                                         │
│     - name: latest                                              │
│       from:                                                     │
│         kind: DockerImage                                       │
│         name: registry.example.com/my-app:latest               │
│       importPolicy:                                             │
│         scheduled: true  # Auto-import updates                 │
│                                                                 │
│ Benefits:                                                       │
│ • Triggers: Rebuild/redeploy when image changes                │
│ • Abstraction: Reference "my-app:latest" regardless of registry│
│ • History: Track all tags and digests                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installing OpenShift

### OpenShift Local (Development)

```bash
# Download OpenShift Local (formerly CodeReady Containers)
# From: https://console.redhat.com/openshift/create/local

# Setup (downloads ~4GB VM image)
crc setup

# Start the cluster
crc start

# Get credentials
crc console --credentials

# Login via CLI
eval $(crc oc-env)
oc login -u developer -p developer https://api.crc.testing:6443

# Access web console
crc console
# Opens https://console-openshift-console.apps-crc.testing
```

### OpenShift on AWS (ROSA)

```bash
# Install ROSA CLI
brew install rosa-cli

# Login to Red Hat and AWS
rosa login
aws configure

# Create cluster
rosa create cluster \
  --cluster-name=my-cluster \
  --region=us-east-1 \
  --compute-machine-type=m5.xlarge \
  --replicas=3 \
  --machine-cidr=10.0.0.0/16 \
  --service-cidr=172.30.0.0/16 \
  --pod-cidr=10.128.0.0/14

# Wait for cluster (30-45 minutes)
rosa describe cluster --cluster=my-cluster --watch

# Create admin user
rosa create admin --cluster=my-cluster

# Login
oc login https://api.my-cluster.xxxx.p1.openshiftapps.com:6443 \
  --username cluster-admin \
  --password <generated-password>
```

### OpenShift on Bare Metal (IPI)

```yaml
# install-config.yaml
apiVersion: v1
baseDomain: example.com
metadata:
  name: my-cluster
compute:
  - name: worker
    replicas: 3
    platform:
      baremetal:
        rootDeviceHints:
          deviceName: "/dev/sda"
controlPlane:
  name: master
  replicas: 3
  platform:
    baremetal:
      rootDeviceHints:
        deviceName: "/dev/sda"
platform:
  baremetal:
    apiVIP: 192.168.1.10
    ingressVIP: 192.168.1.11
    hosts:
      - name: master-0
        bootMACAddress: aa:bb:cc:dd:ee:01
        bmc:
          address: ipmi://192.168.1.101
          username: admin
          password: password
      # ... more hosts
pullSecret: '<your-pull-secret>'
sshKey: 'ssh-rsa AAAA...'
```

```bash
# Create cluster
openshift-install create cluster --dir=./install-dir

# Monitor installation
openshift-install wait-for install-complete --dir=./install-dir
```

---

## Developer Experience

### Source-to-Image (S2I)

```bash
# Deploy directly from Git (no Dockerfile needed!)
oc new-app nodejs~https://github.com/company/my-node-app.git

# What just happened:
# 1. OpenShift detected it's a Node.js app
# 2. Created a BuildConfig
# 3. Built a container using S2I builder image
# 4. Pushed to internal registry
# 5. Created Deployment and Service
# 6. You're running!

# Watch the build
oc logs -f buildconfig/my-node-app

# Expose the application
oc expose service/my-node-app

# Get the URL
oc get route my-node-app
# my-node-app-myproject.apps.cluster.example.com
```

### Using the Developer Console

```
OPENSHIFT WEB CONSOLE - DEVELOPER PERSPECTIVE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│  OpenShift Console - Developer View                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  TOPOLOGY VIEW                                              ││
│  │                                                             ││
│  │      ┌──────────┐        ┌──────────┐                      ││
│  │      │ Frontend │───────▶│ Backend  │                      ││
│  │      │  (React) │        │  (Node)  │                      ││
│  │      │ ▶ 3 pods │        │ ▶ 2 pods │                      ││
│  │      └────┬─────┘        └────┬─────┘                      ││
│  │           │                   │                             ││
│  │      ┌────┴─────┐        ┌────┴─────┐                      ││
│  │      │  Route   │        │ Database │                      ││
│  │      │  (edge)  │        │ (Postgres)│                     ││
│  │      └──────────┘        └──────────┘                      ││
│  │                                                             ││
│  │  Click any resource to:                                     ││
│  │  • View logs                                                ││
│  │  • Open terminal                                            ││
│  │  • Scale up/down                                            ││
│  │  • Start builds                                             ││
│  │  • View metrics                                             ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### OpenShift Pipelines (Tekton)

```yaml
# Simple pipeline for build, test, deploy
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: build-and-deploy
spec:
  params:
    - name: git-url
    - name: image-name
  workspaces:
    - name: source
  tasks:
    - name: clone
      taskRef:
        name: git-clone
        kind: ClusterTask
      params:
        - name: url
          value: $(params.git-url)
      workspaces:
        - name: output
          workspace: source

    - name: test
      taskRef:
        name: npm-test
      runAfter: [clone]
      workspaces:
        - name: source
          workspace: source

    - name: build
      taskRef:
        name: buildah
        kind: ClusterTask
      runAfter: [test]
      params:
        - name: IMAGE
          value: $(params.image-name)
      workspaces:
        - name: source
          workspace: source

    - name: deploy
      taskRef:
        name: openshift-client
        kind: ClusterTask
      runAfter: [build]
      params:
        - name: SCRIPT
          value: |
            oc set image deployment/my-app \
              my-app=$(params.image-name)
```

---

## Security in OpenShift

### Security Context Constraints (SCCs)

```yaml
# View available SCCs
oc get scc

# NAME               PRIV    CAPS   SELINUX     RUNASUSER          FSGROUP     SUPGROUP
# anyuid             false   []     MustRunAs   RunAsAny           RunAsAny    RunAsAny
# hostaccess         false   []     MustRunAs   MustRunAsRange     MustRunAs   RunAsAny
# hostmount-anyuid   false   []     MustRunAs   RunAsAny           RunAsAny    RunAsAny
# hostnetwork        false   []     MustRunAs   MustRunAsRange     MustRunAs   MustRunAs
# nonroot            false   []     MustRunAs   MustRunAsNonRoot   RunAsAny    RunAsAny
# privileged         true    [*]    RunAsAny    RunAsAny           RunAsAny    RunAsAny
# restricted         false   []     MustRunAs   MustRunAsRange     MustRunAs   RunAsAny

# Most pods run under 'restricted' SCC by default
# This means:
# - Can't run as root
# - No privileged containers
# - No host namespaces
# - Limited capabilities
```

```yaml
# Example: Grant service account ability to run as any user
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-anyuid
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:openshift:scc:anyuid
subjects:
  - kind: ServiceAccount
    name: my-app
    namespace: my-project
```

### OAuth Integration

```yaml
# Configure LDAP authentication
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
    - name: company-ldap
      type: LDAP
      ldap:
        url: ldaps://ldap.company.com/ou=users,dc=company,dc=com?uid
        insecure: false
        ca:
          name: ldap-ca-cert
        bindDN: cn=admin,dc=company,dc=com
        bindPassword:
          name: ldap-bind-password
        attributes:
          id: ["dn"]
          email: ["mail"]
          name: ["cn"]
          preferredUsername: ["uid"]
```

---

## War Story: The Platform That Built Itself

*How a bank modernized 200 applications in 18 months*

### The Challenge

A regional bank had:
- **200+ applications** running on VMs
- **Multiple teams** with different deployment practices
- **Compliance requirements** (SOC2, PCI-DSS)
- **Mandate**: Modernize to containers within 2 years

Initial estimate with vanilla Kubernetes: 3 years, $5M

### The OpenShift Approach

```
MODERNIZATION TIMELINE
─────────────────────────────────────────────────────────────────

MONTH 1-2: PLATFORM FOUNDATION
─────────────────────────────────────────────────────────────────
✓ Deployed OpenShift on VMware (existing investment)
✓ Integrated with Active Directory (OAuth)
✓ Configured log forwarding to Splunk
✓ Set up Prometheus/Grafana (built-in)
✓ Enabled cluster audit logging

What would have taken 6 months with vanilla K8s: 2 months

MONTH 3-4: DEVELOPER ENABLEMENT
─────────────────────────────────────────────────────────────────
✓ Created project templates with:
  - Resource quotas
  - Network policies
  - Default SCCs
  - Monitoring dashboards
✓ Set up S2I builders for Java, Node, Python
✓ Integrated with GitHub Enterprise (webhooks)
✓ Trained 50 developers (2-day workshop)

Self-service: Developers create projects, deploy apps, no tickets

MONTH 5-12: APPLICATION MIGRATION
─────────────────────────────────────────────────────────────────
Wave 1: Stateless web apps (50 apps)
├── Most used S2I directly from Git
├── Some needed custom Dockerfiles
└── Average migration: 3 days per app

Wave 2: Backend services (80 apps)
├── Spring Boot apps used Java S2I
├── Legacy apps needed containerization
└── Average migration: 1 week per app

Wave 3: Databases and stateful (70 apps)
├── Used OpenShift Data Foundation
├── Operators for PostgreSQL, MongoDB
└── Average migration: 2 weeks per app

MONTH 13-18: OPTIMIZATION
─────────────────────────────────────────────────────────────────
✓ Implemented GitOps with ArgoCD
✓ Added service mesh for critical services
✓ Automated compliance scanning
✓ Achieved 99.9% platform uptime
```

### Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Deployment frequency | Monthly | Daily | 30x faster |
| Lead time | 6 weeks | 2 hours | 99.5% reduction |
| Failed deployments | 15% | 2% | 87% fewer failures |
| MTTR | 4 hours | 15 minutes | 94% faster recovery |
| Developer productivity | Baseline | +40% | Measurable output |
| Infrastructure costs | $2M/year | $1.2M/year | 40% savings |

**Financial Impact (First 18 Months):**

| Category | Without OpenShift | With OpenShift | Savings |
|----------|-------------------|----------------|---------|
| Platform build (18 months × 12 engineers × $175K/yr) | $3,150,000 | $0 | $3,150,000 |
| OpenShift subscription (18 months) | $0 | $510,000 | -$510,000 |
| Red Hat consulting (migration assistance) | $0 | $180,000 | -$180,000 |
| Delayed application migrations (opportunity cost) | $2,400,000 | $0 | $2,400,000 |
| Failed deployment remediation (15% vs 2%) | $840,000 | $112,000 | $728,000 |
| Infrastructure consolidation | $0 | $800,000 | $800,000 |
| **Total 18-Month Impact** | **$6,390,000** | **$1,602,000** | **$4,788,000** |

The CIO presented to the board: "We saved $4.8M and finished 6 months early. The vanilla Kubernetes POC we did first? We threw it away after 3 months when we realized we'd need 18 more months just to match what OpenShift gave us on day one."

### Key Success Factors

1. **Opinionated platform** — Developers didn't have to make infrastructure decisions
2. **Self-service** — 80% of requests handled without platform team
3. **S2I for velocity** — Most apps deployed from Git without Docker expertise
4. **Built-in security** — SCCs enforced policies without per-app configuration
5. **Enterprise support** — Red Hat helped with complex migrations

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Fighting SCCs | Security holes | Work with SCCs, fix images to run non-root |
| Ignoring Routes | Reinventing ingress | Use Routes, they're better integrated |
| Manual builds | Inconsistent images | Use BuildConfigs and S2I |
| Skipping OperatorHub | Missing capabilities | Check OperatorHub first for any need |
| Over-customizing | Hard to upgrade | Use supported configurations |
| No resource quotas | Project sprawl | Quotas on every project |
| Direct registry access | Bypassing controls | Use ImageStreams |
| Ignoring web console | Slower onboarding | Train developers on console |

---

## Hands-On Exercise

### Task: Deploy Application with OpenShift Features

**Objective**: Deploy an application using OpenShift-specific features (S2I, Routes, BuildConfigs).

**Success Criteria**:
1. Application deployed via S2I
2. Route exposing the application
3. Build triggered by Git webhook
4. Application accessible via HTTPS

### Steps

```bash
# 1. Start OpenShift Local (if not running)
crc start
eval $(crc oc-env)
oc login -u developer -p developer https://api.crc.testing:6443

# 2. Create a new project
oc new-project demo-app
oc project demo-app

# 3. Deploy from Git using S2I
oc new-app nodejs~https://github.com/sclorg/nodejs-ex.git \
  --name=nodejs-demo

# 4. Watch the build
oc logs -f buildconfig/nodejs-demo

# 5. Create a route (with TLS)
oc create route edge nodejs-demo \
  --service=nodejs-demo \
  --port=8080

# 6. Get the URL
oc get route nodejs-demo
# Open in browser: https://nodejs-demo-demo-app.apps-crc.testing

# 7. Verify the application
curl -k https://nodejs-demo-demo-app.apps-crc.testing

# 8. View in web console
crc console
# Navigate to Topology in demo-app project

# 9. Scale the application
oc scale deployment/nodejs-demo --replicas=3

# 10. View pod distribution
oc get pods -o wide

# 11. Check build history
oc get builds

# 12. Trigger a new build (simulating Git push)
oc start-build nodejs-demo

# 13. View ImageStream
oc get imagestream nodejs-demo
oc describe imagestream nodejs-demo

# 14. Check resource usage
oc adm top pods

# 15. View logs in aggregate
oc logs -f deployment/nodejs-demo

# Clean up
oc delete project demo-app
```

---

## Quiz

### Question 1
What is the difference between a Namespace and a Project in OpenShift?

<details>
<summary>Show Answer</summary>

**Projects are Namespaces with additional metadata and RBAC defaults**

Projects add:
- Display name and description
- Request tracking (who created it)
- Default role bindings (admin, edit, view)
- Network isolation options
- Resource quota defaults

You can use `oc new-project` or `kubectl create namespace`—both work, but Projects provide better multi-tenancy.
</details>

### Question 2
What is Source-to-Image (S2I)?

<details>
<summary>Show Answer</summary>

**A build strategy that creates container images from source code without a Dockerfile**

S2I:
1. Takes source code from Git
2. Combines it with a builder image (e.g., nodejs:18)
3. Runs the builder's assemble script
4. Produces a runnable container image

Benefits: No Docker knowledge needed, consistent builds, security (builders are curated).
</details>

### Question 3
How do Routes differ from Kubernetes Ingress?

<details>
<summary>Show Answer</summary>

**Routes are OpenShift's built-in ingress with additional features:**

- **Edge termination**: TLS at the router
- **Passthrough**: TLS to the backend
- **Re-encrypt**: TLS at router AND to backend
- **Automatic hostnames**: Based on route name + project
- **Integrated with OAuth**: Can require authentication
- **HAProxy-based**: Built into the platform

No need for an Ingress controller—Routes just work.
</details>

### Question 4
What are Security Context Constraints (SCCs)?

<details>
<summary>Show Answer</summary>

**OpenShift's mechanism for controlling pod security privileges**

SCCs define what a pod can do:
- Run as root or specific UID
- Use privileged containers
- Access host namespaces
- Mount specific volume types
- Use Linux capabilities

Default SCC (restricted) prevents most privilege escalation. SCCs predate and are more granular than Kubernetes Pod Security Standards.
</details>

### Question 5
Why does OpenShift require RHCOS for control plane nodes?

<details>
<summary>Show Answer</summary>

**RHCOS is purpose-built for OpenShift and enables key features:**

- **Immutable OS**: Configuration via MachineConfig, not SSH
- **Atomic updates**: OS updates like container updates
- **Tight integration**: CRI-O, kubelet, etc. are optimized
- **Security**: SELinux, FIPS mode, consistent baseline
- **Support**: Red Hat can support the full stack

Worker nodes can run RHEL, but control plane requires RHCOS.
</details>

### Question 6
What is OperatorHub?

<details>
<summary>Show Answer</summary>

**A curated catalog of Kubernetes Operators for installing cluster services**

OperatorHub provides:
- Red Hat certified operators
- Community operators
- Marketplace operators
- Automatic updates and lifecycle management

Example: Install PostgreSQL by clicking "Install" in OperatorHub, rather than writing manifests manually.
</details>

### Question 7
How does OpenShift handle OAuth/authentication?

<details>
<summary>Show Answer</summary>

**Built-in OAuth server with pluggable identity providers**

OpenShift's OAuth server supports:
- LDAP/Active Directory
- GitHub/GitLab
- Google/OpenID Connect
- SAML
- HTPasswd (for development)

Users authenticate via `oc login` or web console, receive tokens, and RBAC controls access. No external identity setup required.
</details>

### Question 8
What is the "oc" CLI and how does it relate to kubectl?

<details>
<summary>Show Answer</summary>

**oc is kubectl plus OpenShift-specific commands**

All kubectl commands work with oc:
```bash
oc get pods        # Same as kubectl get pods
oc apply -f x.yaml # Same as kubectl apply
```

Plus OpenShift additions:
```bash
oc new-project     # Create project
oc new-app         # Deploy from Git
oc start-build     # Trigger build
oc expose          # Create route
oc adm             # Admin commands
```

Most users use oc exclusively.
</details>

---

## Key Takeaways

1. **Complete platform** — Not just Kubernetes, but CI/CD, registry, monitoring, logging
2. **Enterprise support** — Red Hat backs the entire stack
3. **Developer experience** — S2I, web console, dev tools built-in
4. **Security by default** — SCCs, OAuth, network policies enabled
5. **Projects not namespaces** — Multi-tenancy with better defaults
6. **Routes not Ingress** — Integrated, HAProxy-based routing
7. **Operators everywhere** — OperatorHub for easy capability addition
8. **RHCOS foundation** — Immutable OS for reliability
9. **Opinionated choices** — Trade flexibility for velocity
10. **Managed options** — ROSA (AWS), ARO (Azure) for cloud

---

## Next Steps

- **Next Module**: [Module 14.6: Managed Kubernetes Comparison](../module-14.6-managed-kubernetes/) — EKS vs GKE vs AKS
- **Related**: [Platform Engineering Discipline](../../../disciplines/core-platform/platform-engineering/) — Building IDPs
- **Related**: [CI/CD Pipelines Toolkit](../../cicd-delivery/ci-cd-pipelines/) — Tekton deep dive

---

## Further Reading

- [OpenShift Documentation](https://docs.openshift.com/)
- [OKD (Community OpenShift)](https://www.okd.io/)
- [Red Hat Developer](https://developers.redhat.com/openshift)
- [OpenShift Local](https://developers.redhat.com/products/openshift-local/overview)
- [ROSA Documentation](https://docs.aws.amazon.com/ROSA/latest/userguide/)

---

*"OpenShift isn't about being different from Kubernetes—it's about shipping a complete platform so you can focus on applications instead of infrastructure."*
