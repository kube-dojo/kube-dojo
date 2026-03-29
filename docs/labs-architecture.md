# KubeDojo Interactive Labs — Architecture Document

## 1. Overview

KubeDojo Labs provides browser-based, interactive practice environments for every curriculum module. Users get real terminals connected to real containers and Kubernetes clusters — no local setup required.

**Strategy**: Hybrid approach — launch on Killercoda for validation (weeks 1-4), build custom platform in parallel (weeks 2-10).

## 2. Scale & Scope

| Track | Total Modules | Lab-Worthy | Priority |
|-------|:---:|:---:|:---:|
| Prerequisites | 33 | ~10 | P2 |
| Linux | 37 | ~25 | P2 |
| Cloud | 84 | ~40 | P3 |
| K8s Certifications | 175 | ~150 | **P1** |
| Platform Engineering | 209 | ~120 | P3 |
| On-Premises | 30 | ~20 | P3 |
| **Total** | **568** | **~365** | |

Target: 10-50 concurrent users initially.

## 3. Lab Tiers

| Tier | Environment | Resources | Session | Use Case |
|------|------------|-----------|---------|----------|
| **Tier 1** | Single container | 128MB RAM, 0.1 vCPU | 30 min | Linux basics, shell exercises |
| **Tier 2** | vCluster (single-node) | 512MB RAM, 0.5 vCPU | 30 min | Basic K8s (pods, deployments) |
| **Tier 3** | vCluster (multi-node) | 2GB RAM, 1.0 vCPU | 60 min | CKA/CKS (networking, storage, troubleshooting) |
| **Tier 4** | vCluster + Helm charts | 3GB RAM, 1.5 vCPU | 60 min | Platform Eng (Prometheus, ArgoCD, etc.) |

## 4. Architecture

```
                    ┌─────────────────────────────────┐
                    │         User's Browser           │
                    │  ┌───────────┬─────────────────┐ │
                    │  │Instructions│   xterm.js      │ │
                    │  │  (React)   │  (WebSocket)    │ │
                    │  └───────────┴────────┬────────┘ │
                    └───────────────────────┼──────────┘
                                            │
                              HTTPS / WSS   │
                                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      Lab Gateway (Go)                        │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│  │  Auth     │  │  Session  │  │  WebSocket│  │  Rate      │  │
│  │  (GitHub  │  │  Router   │  │  Proxy    │  │  Limiter   │  │
│  │  OAuth)   │  │           │  │           │  │            │  │
│  └──────────┘  └──────────┘  └───────────┘  └────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   Kubernetes Host Cluster                     │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Session Manager                         │ │
│  │  - Creates/destroys lab sessions (K8s CRDs)             │ │
│  │  - Enforces TTL (30/60 min)                             │ │
│  │  - Tracks state in Redis                                │ │
│  │  - Manages vCluster lifecycle                           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Lab      │  │  Lab      │  │  Lab      │  │  Lab     │    │
│  │  Session  │  │  Session  │  │  Session  │  │  Session │    │
│  │  ns-a1b2  │  │  ns-c3d4  │  │  ns-e5f6  │  │  ns-g7h8│    │
│  │           │  │           │  │           │  │          │    │
│  │ ┌───────┐│  │ ┌───────┐ │  │ ┌───────┐ │  │┌───────┐│    │
│  │ │vCluster││  │ │vCluster│ │  │ │Container│ │  ││vClust.││    │
│  │ │  v1.31 ││  │ │  v1.31│ │  │ │ (Tier 1)│ │  ││+Helm ││    │
│  │ │(Tier 3)││  │ │(Tier 2)│ │  │ │        │ │  ││(Tier4)││    │
│  │ └───────┘│  │ └───────┘ │  │ └───────┘ │  │└───────┘│    │
│  │ ┌───────┐│  │           │  │           │  │┌───────┐│    │
│  │ │Validatr││  │           │  │           │  ││Validtr││    │
│  │ │sidecar ││  │           │  │           │  ││sidecar││    │
│  │ └───────┘│  │           │  │           │  │└───────┘│    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  ┌───────────┐  ┌───────────────┐  ┌──────────────────────┐ │
│  │   Redis    │  │  Cleanup       │  │  Autoscaler          │ │
│  │  (sessions │  │  Controller    │  │  (Karpenter/CAS)     │ │
│  │   + state) │  │  (TTL reaper)  │  │                      │ │
│  └───────────┘  └───────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## 5. Component Details

### 5.1 Web Terminal (Frontend)
- **xterm.js** — battle-tested terminal emulator in the browser
- WebSocket connection to Lab Gateway
- Embedded in Starlight module pages via Astro component
- Split-pane layout: instructions (left 45%) + terminal (right 55%)
- Resizable divider, multiple terminal tabs

### 5.2 Lab Gateway (Go service)
- **Authentication**: GitHub OAuth (JWT tokens)
- **Session routing**: Maps user sessions to correct pod/namespace
- **WebSocket proxy**: Bidirectional terminal I/O
- **Rate limiting**: Max 2 concurrent sessions per user
- **Health checks**: Monitors session liveness

### 5.3 Session Manager (K8s Controller)
- Custom CRD: `LabSession`
- Creates namespace per session with resource quotas
- Provisions vCluster (Tier 2-4) or bare pod (Tier 1)
- Runs setup scripts from scenario definition
- Manages TTL-based cleanup
- Stores session state in Redis (for fast lookups)

### 5.4 Scenario Engine
Each lab is defined in YAML:

```yaml
# labs/k8s/cka/part1/lab-1.3-fix-broken-deployment.yaml
apiVersion: kubedojo.io/v1
kind: LabScenario
metadata:
  name: cka-1.3-fix-broken-deployment
spec:
  title: "Fix a Broken Deployment"
  track: k8s-certifications
  certification: CKA
  part: 1
  module: "1.3"
  tier: 3
  duration: 45m
  difficulty: intermediate

  environment:
    vcluster:
      version: "1.31"
      workers: 2
    namespace: production

  setup:
    - kubectl create namespace production
    - kubectl apply -f /lab/fixtures/broken-nginx-deploy.yaml

  steps:
    - title: "Investigate the deployment"
      description: "Use kubectl to check the deployment status"
      check:
        command: "kubectl get deploy nginx-app -n production -o json"
        condition: "jq '.status.readyReplicas == 0'"
      hint: "Try: kubectl describe deploy nginx-app -n production"

    - title: "Fix the image name"
      description: "The deployment uses an incorrect image. Fix it."
      check:
        command: "kubectl get deploy nginx-app -n production -o jsonpath='{.spec.template.spec.containers[0].image}'"
        condition: "grep 'nginx:1.25'"
      hint: "kubectl set image deploy/nginx-app nginx=nginx:1.25 -n production"

    - title: "Verify all replicas are ready"
      description: "Ensure all 3 replicas are Running."
      check:
        command: "kubectl get deploy nginx-app -n production -o jsonpath='{.status.readyReplicas}'"
        condition: "grep '3'"

  fixtures:
    - name: broken-nginx-deploy.yaml
      content: |
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: nginx-app
          namespace: production
        spec:
          replicas: 3
          selector:
            matchLabels:
              app: nginx
          template:
            metadata:
              labels:
                app: nginx
            spec:
              containers:
              - name: nginx
                image: ngnix:latest  # intentional typo
                ports:
                - containerPort: 80
```

### 5.5 Validator Sidecar
- Runs as a sidecar container in each lab session
- Exposes gRPC API for step validation
- Executes check commands defined in scenario YAML
- Reports step completion back to Session Manager
- Powers the "Check" button in the UI

### 5.6 Cleanup Controller
- Watches `LabSession` CRDs for TTL expiry
- Gracefully terminates sessions (warning at 5 min, force at 0)
- Deletes namespace + all resources
- Logs session metrics (duration, steps completed, resource usage)

## 6. Data Layer (Supabase)

User data must be stored even during the Killercoda-only phase (progress, completions, streaks). **Supabase free tier** provides this with zero backend code.

### Why Supabase
- GitHub OAuth built-in (our chosen auth method)
- PostgreSQL database with auto-generated REST API
- Row-level security (users can only access their own data)
- Called directly from the browser — no backend server needed
- Free tier: 500MB DB, 50K monthly API requests, unlimited auth users

### Killercoda Phase Flow
```
User clicks "Launch Lab" on KubeDojo
  → GitHub OAuth via Supabase (if not logged in)
  → Save "lab_started" event to Supabase
  → Redirect to Killercoda scenario
  → User completes lab on Killercoda
  → Returns to KubeDojo, clicks "Mark Complete"
  → Save completion to Supabase
  → Dashboard reads progress from Supabase
```

Note: Killercoda has no webhook for auto-completion detection. Users self-report via "Mark Complete" button. This becomes automatic when we build the custom platform (validator sidecar detects completion).

### Custom Platform Phase Flow
```
User clicks "Launch Lab"
  → GitHub OAuth via Supabase
  → Lab Gateway creates session
  → Validator sidecar auto-detects step completion
  → Progress saved to Supabase in real-time
  → No manual "Mark Complete" needed
```

### Supabase Cost Projection
| Phase | Tier | Monthly Cost |
|-------|------|:---:|
| Killercoda (0-100 users) | Free | $0 |
| Custom platform (100-1000 users) | Free | $0 |
| Scaling (1000+ users) | Pro | $25/mo |

## 7. Infrastructure

### 7.1 EU Cloud Provider Comparison

All 5 providers have EU data centers. Prices in EUR (AWS converted from USD at ~0.92).

#### Node Pricing: 4 vCPU, 16GB RAM (the ideal lab node)

| Provider | Instance | CPU Type | Price/mo | Control Plane | 3-Node Cluster |
|---|---|---|---:|---:|---:|
| **Hetzner** | CCX23 | Dedicated | **€31.49** | Free (managed) | **€94** |
| **Hetzner** | CX43 (8vCPU/16GB) | Shared | **€11.99** | Free (managed) | **€36** |
| **OVHcloud** | b3-16 | Shared | **~€68** | Free | **~€204** |
| **Scaleway** | PRO2-XS | Dedicated | **€80.30** | Free | **€241** |
| **Scaleway** | PLAY2-MICRO (4/8GB) | Shared | **€39.42** | Free | **€118** |
| **AWS** | t3.xlarge (on-demand) | Burstable | **~€111** | €67/mo | **€400** |
| **AWS** | t3.xlarge (spot) | Burstable | **~€29** | €67/mo | **€154** |
| **IONOS** | Flex (4/16) | Dedicated | **~€55** | Free | **~€165** |

> Note: Hetzner prices increase 30-37% from April 1, 2026. Post-increase CCX23 estimated ~€41/mo.

#### Control Plane Cost

| Provider | Managed K8s | Control Plane Cost |
|---|---|---:|
| Hetzner | Yes (managed) | **Free** |
| OVHcloud | Yes (MKS) | **Free** |
| Scaleway | Yes (Kapsule) | **Free** |
| IONOS | Yes | **Free** |
| AWS | Yes (EKS) | **€67/mo** ($73) |

Every EU provider offers free control planes. AWS is the only one charging.

#### Additional Costs

| Resource | Hetzner | Scaleway | OVHcloud | AWS |
|---|---:|---:|---:|---:|
| Load Balancer | €6/mo | €10/mo | €10/mo | ~€17/mo |
| Storage (100GB) | ~€5/mo | €8/mo | ~€5/mo | ~€9/mo |
| Egress (100GB) | **Free** (20TB incl) | **Free** (incl) | **Free** (incl) | ~€8/mo |
| IPv4 address | €4/mo | €3/mo | Free (1 incl) | €3.36/mo |
| Redis | Self-host | Self-host | Self-host | €14/mo (ElastiCache) |

#### Full 3-Node Cluster Total (with extras)

| Provider | Nodes | Control | LB + Storage | Egress | **Total/mo** |
|---|---:|---:|---:|---:|---:|
| **Hetzner (shared)** | €36 | Free | €11 | Free | **~€47** |
| **Hetzner (dedicated)** | €94 | Free | €11 | Free | **~€105** |
| **Scaleway (shared)** | €118 | Free | €18 | Free | **~€136** |
| **Scaleway (dedicated)** | €241 | Free | €18 | Free | **~€259** |
| **OVHcloud** | €204 | Free | €15 | Free | **~€219** |
| **IONOS** | €165 | Free | ~€15 | Free | **~€180** |
| **AWS (spot)** | €87 | €67 | €26 | €8 | **~€188** |
| **AWS (on-demand)** | €333 | €67 | €26 | €8 | **~€434** |

### 7.2 Provider Recommendation

| Criteria | Winner | Why |
|---|---|---|
| **Cheapest overall** | **Hetzner** | €47-105/mo, unbeatable on price |
| **Best managed K8s** | **Scaleway** | Free CP, good API, autoscaling to 500 nodes |
| **GDPR simplest** | **Scaleway / Hetzner** | EU companies, no US parent |
| **Spot instances** | **AWS** | 70% savings, but adds complexity |
| **Most EU locations** | **OVHcloud** | 12+ EU datacenters |
| **Best support** | **Scaleway** | Good docs, active community |

**Our recommendation: Pick ONE provider, don't mix.**

| Phase | Provider | Config | Cost |
|---|---|---|---:|
| PoC | **Hetzner** | 1x CX43 (shared) | **~€18/mo** |
| Early production | **Hetzner** | 3x CCX23 (dedicated) | **~€105/mo** |
| Scale (50+ users) | **Scaleway** | 3x PRO2-XS + autoscaling | **~€259/mo** |
| Large scale | **AWS EU** | EKS + spot + autoscaling | **~€188+/mo** |

Start Hetzner (cheapest PoC), migrate to Scaleway or AWS only when you need autoscaling beyond what Hetzner offers.

#### Why NOT mix providers
- WebSocket terminal latency requires <50ms — cross-provider adds 10-30ms
- vCluster sessions can't span providers
- Double ops burden (two credential sets, two monitoring stacks, two billing)
- No cost benefit — sessions are self-contained, not distributed

### 7.2 Recommended Configurations by Phase

#### Phase 1: Killercoda Only — $0/mo infra
| Resource | Provider | Cost |
|---|---|:---:|
| Static site | GitHub Pages | $0 |
| Database + Auth | Supabase free | $0 |
| Labs | Killercoda | $0 |
| **Total** | | **$0/mo** |

#### Phase 2: PoC (Tier 1 only) — ~€18/mo
| Resource | Provider | Cost |
|---|---|:---:|
| 1x CX43 node (8vCPU/16GB) | Hetzner | €12 |
| Managed K8s control plane | Hetzner | Free |
| Supabase | Free tier | €0 |
| Load Balancer | Hetzner | €6 |
| **Total** | | **~€18/mo** |

#### Phase 3: Production (10-50 concurrent) — ~€105/mo
| Resource | Provider | Cost |
|---|---|:---:|
| 3x CCX23 nodes (4vCPU/16GB dedicated) | Hetzner | €94 |
| Managed K8s control plane | Hetzner | Free |
| Supabase | Free tier | €0 |
| Load Balancer | Hetzner | €6 |
| Block storage (100GB) | Hetzner | €5 |
| **Total (Hetzner)** | | **~€105/mo** |

#### Phase 4: Scale (50+ concurrent) — migrate if needed
| Resource | Provider | Cost |
|---|---|:---:|
| 3-10x PRO2-XS nodes (autoscaling) | Scaleway | €241-800 |
| Kapsule control plane | Scaleway | Free |
| Supabase | Pro tier | €25 |
| Load Balancer + Storage | Scaleway | €18 |
| **Total (Scaleway)** | | **~€284-843/mo** |

#### Side-by-Side Summary

| | Hetzner | Scaleway | AWS (Spot) |
|---|:---:|:---:|:---:|
| Phase 2 (PoC) | **€18/mo** | €49/mo | ~€83/mo |
| Phase 3 (Production) | **€105/mo** | €259/mo | ~€188/mo |
| CPU type | Dedicated | Dedicated | Burstable + interruptible |
| Egress | Free (20TB) | Free | Paid |
| Autoscaling | Basic | Up to 500 nodes | Full (Karpenter) |
| GDPR | German company | French company | US company (EU region) |

**Recommendation**: Start Hetzner → scale to Scaleway or AWS when autoscaling is needed

### 7.3 Per-Session Cost (Scaleway-based)

| Lab Tier | Resources | Cost/session (30min) | Cost/session (60min) |
|----------|-----------|:---:|:---:|
| Tier 1 (Terminal) | 128MB, 0.1 vCPU | €0.002 | €0.004 |
| Tier 2 (Single K8s) | 512MB, 0.5 vCPU | €0.008 | €0.016 |
| Tier 3 (Multi K8s) | 2GB, 1.0 vCPU | €0.028 | €0.055 |
| Tier 4 (K8s+Tools) | 3GB, 1.5 vCPU | €0.042 | €0.083 |

### 7.4 Monthly Cost Projection (Hetzner-based)

| Concurrent Users | Avg Sessions/day | Base Infra | Approx Total/mo |
|:---:|:---:|:---:|:---:|
| 5 | ~20 | €18 (1 node) | **~€18** |
| 10 | ~40 | €105 (3 nodes) | **~€105** |
| 25 | ~100 | €105 (3 nodes) | **~€115** |
| 50 | ~200 | €140 (4 nodes) | **~€155** |

*At 50+ concurrent users, consider migrating to Scaleway for better autoscaling.*

### 7.5 Autoscaling Strategy
- **Node autoscaler**: Scale 1-10 nodes based on pending pods
- **Scale to near-zero**: 1 node during off-hours (keep gateway + Redis alive)
- **Pre-warming**: Keep 2-3 vCluster instances ready for instant launch
- **Spot (AWS only)**: Use for lab workloads (sessions are ephemeral, interruption is acceptable)
- **Scaleway Savings Plan**: 25% off with commitment (worth it once demand is stable)

## 8. Security

| Concern | Mitigation |
|---------|-----------|
| Container escape | vCluster isolation + PodSecurityStandards (restricted) |
| Network attacks | NetworkPolicies per namespace, no inter-session traffic |
| Resource abuse | ResourceQuotas per namespace, CPU/memory limits per tier |
| Crypto mining | CPU throttling, session TTL, anomaly detection |
| Data persistence | Ephemeral storage only, no PVCs, teardown on completion |
| Auth bypass | GitHub OAuth required, JWT validation at gateway |
| DDoS | Rate limiting (2 sessions/user), Cloudflare in front |

## 9. User Flow

```
1. User reads module on KubeDojo site
2. Clicks "Launch Lab" button embedded in module page
3. Redirected to GitHub OAuth (if not logged in)
4. Lab Gateway creates LabSession CRD
5. Session Manager provisions namespace + vCluster (10-30s)
6. WebSocket connection established to terminal
7. User sees split view: instructions (left) + terminal (right)
8. User works through steps, clicks "Check" to validate
9. Validator sidecar runs check commands, reports pass/fail
10. On completion: congratulations screen, progress saved
11. On timeout: warning at 5 min, session terminated at 0
12. Namespace + all resources cleaned up
```

## 10. Data Model

```
User (GitHub OAuth)
├── id, github_username, avatar_url
├── created_at, last_active
└── sessions[]

Session
├── id, user_id, scenario_id
├── tier, status (pending/running/completed/terminated)
├── namespace, vcluster_name
├── started_at, expires_at, completed_at
├── steps_completed, total_steps
└── resource_usage (cpu_seconds, memory_mb_seconds)

Scenario
├── id, track, certification, part, module
├── title, tier, duration, difficulty
├── setup_commands[], steps[]
└── fixtures[]

Progress (per user per scenario)
├── user_id, scenario_id
├── best_completion (steps/total)
├── attempts, total_time_spent
└── first_completed_at, last_attempted_at
```

## 11. Implementation Phases

### Phase 1: Killercoda Validation (Weeks 1-4)
- Author 10-15 CKA scenarios in Killercoda format
- Embed Killercoda iframes/links in KubeDojo module pages
- Measure engagement: launches, completions, drop-off points
- **Cost: $0** (Killercoda free tier)
- **Deliverable**: Validated demand + reusable scenario content

### Phase 2: Terminal PoC (Weeks 2-5)
- xterm.js component embedded in Astro/Starlight
- Lab Gateway (Go) with WebSocket proxy
- Tier 1 labs only (single container, no K8s)
- GitHub OAuth login
- Deploy on single Hetzner node
- **Cost: ~$30/mo**
- **Deliverable**: Working terminal-in-browser for 5 Linux labs

### Phase 3: K8s Labs (Weeks 5-8)
- vCluster integration (Tier 2-3)
- Scenario YAML engine + validator sidecar
- Session Manager with CRDs and TTL cleanup
- 30 CKA labs authored
- 3-node Hetzner cluster
- **Cost: ~$105/mo**
- **Deliverable**: Full K8s lab experience for CKA

### Phase 4: Scale & Polish (Weeks 8-12)
- User dashboard with progress tracking
- Achievements/badges system
- Autoscaling (node pool + pre-warming)
- Admin monitoring dashboard
- 100+ labs across tracks
- **Cost: ~$150-300/mo** (depending on usage)
- **Deliverable**: Production-ready labs platform

### Phase 5: Full Coverage (Ongoing)
- Tier 4 labs (K8s + tools)
- All 365 labs authored
- Contributor guide for lab authoring
- Monetization decision (if needed)

## 12. Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | Astro/Starlight + xterm.js + React (terminal component) |
| Gateway | Go (net/http, gorilla/websocket) |
| Session Management | Kubernetes CRDs + controller-runtime |
| Virtual Clusters | vCluster (open source, Loft Labs) |
| Validation | Go sidecar + shell commands |
| Auth | GitHub OAuth 2.0 + JWT |
| Data (Killercoda phase) | Supabase free tier (PostgreSQL + Auth + REST API) |
| Data (Custom phase) | Supabase + Redis (session state) |
| Monitoring | Prometheus + Grafana |
| Infrastructure | Hetzner (PoC/prod) → Scaleway/AWS EU (scale) |
| CI/CD | GitHub Actions |
| DNS/TLS | Cloudflare + Let's Encrypt |

## 13. Design PoC Pages

Interactive HTML mockups for demo purposes:

| Page | File | Description |
|------|------|-------------|
| Landing | `poc-labs-landing.html` | Hero, track cards, how it works, featured labs |
| Catalog | `poc-labs-catalog.html` | Browse/filter labs by cert, sidebar navigation |
| Session | `poc-labs-session.html` | Split-pane terminal + instructions (core UX) |
| Dashboard | `poc-labs-dashboard.html` | User progress, streaks, achievements |
| Admin | `poc-labs-admin.html` | Ops monitoring, sessions, infra, costs |
