# KubeDojo Labs — Project Plan (Killercoda Phase)

**Budget**: $0/mo (localStorage + Killercoda + GitHub Pages)
**Goal**: Ship interactive labs for existing curriculum with zero infrastructure cost

---

## Milestones Overview

| # | Milestone | Labs | Target |
|---|-----------|:---:|--------|
| M1 | Platform Foundation | 0 | Week 1-2 |
| M2 | First Labs — Prerequisites | 10 | Week 2-3 |
| M3 | CKA Labs — Core (Parts 0-2) | 21 | Week 3-6 |
| M4 | Linux Labs — Foundations | 13 | Week 6-8 |
| M5 | CKA Labs — Advanced (Parts 3-5) | 20 | Week 8-11 |
| M6 | Supabase + Dashboard | 0 | When pitching investors |

**Total: 64 labs in 11 weeks**

---

## Epic 1: Platform Foundation

**Milestone**: M1 (Week 1-2)
**Goal**: Set up the Killercoda repo, localStorage tracking, and integrate lab buttons into the Starlight site.

### E1.1 — Killercoda Scenarios Repository

**Description**: Create and configure the GitHub repo that Killercoda pulls scenarios from.

**Acceptance Criteria**:
- [ ] Public repo `kube-dojo/kubedojo-labs` created on GitHub
- [ ] Connected to Killercoda creator account (`killercoda.com/kubedojo`)
- [ ] Repo structure documented in README:
  ```
  kubedojo-labs/
  ├── README.md
  ├── prerequisites/
  │   └── zero-to-terminal/
  ├── linux/
  ├── k8s/
  │   └── cka/
  └── templates/           # reusable scenario templates
      ├── ubuntu-base/
      └── k8s-base/
  ```
- [ ] One "hello world" test scenario deployed and accessible at `killercoda.com/kubedojo/test`
- [ ] CI: GitHub Action validates `index.json` schema on PR

### E1.2 — Scenario Templates

**Description**: Create reusable base templates for the two environment types we'll use across all labs.

**Acceptance Criteria**:
- [ ] Ubuntu template: `templates/ubuntu-base/`
  - `index.json` with `"imageid": "ubuntu"`
  - Standard intro.md with KubeDojo branding
  - Standard finish.md with "Mark Complete" reminder + link back to module
  - setup.sh installs common tools (jq, tree, curl)
- [ ] K8s template: `templates/k8s-base/`
  - `index.json` with `"imageid": "kubernetes-kubeadm-1node"`
  - Standard intro.md with KubeDojo branding
  - Standard finish.md
  - setup.sh creates practice namespace, sets aliases (k=kubectl)
- [ ] Template usage documented in README

### E1.3 — localStorage Progress Tracking

**Description**: Implement client-side progress tracking using localStorage so users can see which labs they've started/completed.

**Acceptance Criteria**:
- [ ] `src/components/LabProgress.astro` component created
- [ ] localStorage schema:
  ```json
  {
    "kubedojo-labs": {
      "cka-2.1-pods": { "status": "completed", "completedAt": "2026-04-01T..." },
      "cka-2.2-deployments": { "status": "started", "startedAt": "2026-04-01T..." }
    }
  }
  ```
- [ ] Functions: `markStarted(labId)`, `markCompleted(labId)`, `getProgress()`, `getTrackProgress(track)`
- [ ] Progress persists across page navigations
- [ ] Export/import progress as JSON (backup for users who want to migrate devices)
- [ ] Unit tests for localStorage functions

### E1.4 — "Launch Lab" Button Component

**Description**: Astro component that shows a lab banner on module pages with launch + completion tracking.

**Acceptance Criteria**:
- [ ] `src/components/LabBanner.astro` component created
- [ ] Props: `labId`, `title`, `killercodeUrl`, `duration`, `difficulty`, `environment`
- [ ] Displays: environment badge (Ubuntu/K8s), duration, difficulty chip
- [ ] "Launch Lab" button opens Killercoda URL in new tab, calls `markStarted()`
- [ ] "Mark Complete" button appears after launch, calls `markCompleted()`
- [ ] Shows completion state if already completed (green checkmark)
- [ ] Responsive design matching KubeDojo design system
- [ ] Works without JavaScript (graceful degradation — just shows link)

### E1.5 — Lab Progress Bar Component

**Description**: Shows track-level progress on index pages and individual module pages.

**Acceptance Criteria**:
- [ ] `src/components/LabProgressBar.astro` component created
- [ ] Props: `track`, `total`
- [ ] Reads localStorage to calculate completed/total
- [ ] Visual progress bar with percentage and count (e.g., "3/10 labs completed")
- [ ] Color-coded by completion: 0% gray, 1-49% blue, 50-99% amber, 100% green
- [ ] Renders on track index pages (e.g., CKA index shows "5/41 labs completed")

### E1.6 — Module Page Integration

**Description**: Add LabBanner to existing module pages that have labs available.

**Acceptance Criteria**:
- [ ] Frontmatter schema extended with optional lab fields:
  ```yaml
  lab:
    id: "cka-2.1-pods"
    url: "https://killercoda.com/kubedojo/scenario/cka-2.1-pods"
    duration: "30 min"
    difficulty: "intermediate"
    environment: "kubernetes"
  ```
- [ ] LabBanner auto-renders when `lab` frontmatter is present
- [ ] Banner appears after title/meta chips, before first h2
- [ ] Lab reminder card appears before prev/next navigation
- [ ] No visual changes to pages without lab frontmatter

---

## Epic 2: First Labs — Prerequisites

**Milestone**: M2 (Week 2-3)
**Goal**: Ship the first 10 labs covering Zero to Terminal and Kubernetes Basics — the most beginner-friendly content.

### E2.1 — Zero to Terminal Labs (5 labs)

**Description**: Create Killercoda scenarios for the most hands-on prerequisite modules.

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `prereq-0.3-first-commands` | 0.3 First Commands | Ubuntu | 20 min | Beginner |
| `prereq-0.4-files-directories` | 0.4 Files and Directories | Ubuntu | 25 min | Beginner |
| `prereq-0.5-editing-files` | 0.5 Editing Files | Ubuntu | 20 min | Beginner |
| `prereq-0.7-servers-ssh` | 0.7 Servers and SSH | Ubuntu | 25 min | Beginner |
| `prereq-0.8-packages` | 0.8 Software and Packages | Ubuntu | 20 min | Beginner |

**Acceptance Criteria** (per lab):
- [ ] `index.json` with title, environment, steps defined
- [ ] `intro.md` with context linking back to KubeDojo module
- [ ] 3-6 guided steps with clear instructions in `stepN/text.md`
- [ ] `verify.sh` for each step that validates completion
- [ ] `setup.sh` seeds environment (creates files, users, etc.)
- [ ] `finish.md` with congratulations + link to next lab
- [ ] Tested manually on Killercoda — all steps completable
- [ ] Frontmatter added to corresponding KubeDojo module page

**Acceptance Criteria** (batch):
- [ ] All 5 labs accessible at `killercoda.com/kubedojo/scenario/prereq-*`
- [ ] All 5 KubeDojo module pages show LabBanner
- [ ] Prerequisites index page shows LabProgressBar
- [ ] `npm run build` passes with zero errors

### E2.2 — Kubernetes Basics Labs (5 labs)

**Description**: Create Killercoda scenarios for the K8s Basics prerequisite modules.

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `prereq-k8s-1-first-cluster` | First Cluster | K8s | 25 min | Beginner |
| `prereq-k8s-2-kubectl` | kubectl Basics | K8s | 30 min | Beginner |
| `prereq-k8s-3-pods` | Pods | K8s | 25 min | Beginner |
| `prereq-k8s-4-deployments` | Deployments | K8s | 30 min | Beginner |
| `prereq-k8s-5-services` | Services | K8s | 25 min | Beginner |

**Acceptance Criteria** (per lab): Same as E2.1 per-lab ACs.

**Acceptance Criteria** (batch):
- [ ] All 5 labs accessible at `killercoda.com/kubedojo/scenario/prereq-k8s-*`
- [ ] All 5 KubeDojo module pages show LabBanner
- [ ] K8s Basics index page shows LabProgressBar
- [ ] `npm run build` passes with zero errors

---

## Epic 3: CKA Labs — Core

**Milestone**: M3 (Week 3-6)
**Goal**: Ship labs for CKA Parts 0-2 — the highest-demand certification content.

### E3.1 — CKA Part 0: Environment Labs (4 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `cka-0.1-cluster-setup` | Cluster Setup | K8s | 30 min | Beginner |
| `cka-0.2-shell-mastery` | Shell Mastery | Ubuntu | 30 min | Intermediate |
| `cka-0.3-vim-yaml` | Vim & YAML | Ubuntu | 25 min | Intermediate |
| `cka-0.4-k8s-docs` | Navigating K8s Docs | K8s | 20 min | Beginner |

**Acceptance Criteria**: Same per-lab/batch structure as Epic 2.

### E3.2 — CKA Part 1: Cluster Architecture Labs (7 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `cka-1.1-control-plane` | Control Plane Deep-Dive | K8s | 40 min | Intermediate |
| `cka-1.2-extension-interfaces` | CNI, CSI, CRI | K8s | 35 min | Intermediate |
| `cka-1.3-helm` | Helm Package Manager | K8s | 40 min | Intermediate |
| `cka-1.4-kustomize` | Kustomize | K8s | 35 min | Intermediate |
| `cka-1.5-crds-operators` | CRDs & Operators | K8s | 40 min | Advanced |
| `cka-1.6-rbac` | RBAC | K8s | 45 min | Intermediate |
| `cka-1.7-kubeadm` | kubeadm Basics | K8s | 40 min | Intermediate |

**Acceptance Criteria**: Same per-lab/batch structure as Epic 2.

### E3.3 — CKA Part 2: Workloads & Scheduling Labs (9 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `cka-2.1-pods` | Pods Deep-Dive | K8s | 40 min | Intermediate |
| `cka-2.2-deployments` | Deployments & ReplicaSets | K8s | 45 min | Intermediate |
| `cka-2.3-daemonsets-statefulsets` | DaemonSets & StatefulSets | K8s | 40 min | Intermediate |
| `cka-2.4-jobs-cronjobs` | Jobs & CronJobs | K8s | 30 min | Intermediate |
| `cka-2.5-resource-management` | Resource Management | K8s | 40 min | Intermediate |
| `cka-2.6-scheduling` | Scheduling | K8s | 45 min | Advanced |
| `cka-2.7-configmaps-secrets` | ConfigMaps & Secrets | K8s | 45 min | Intermediate |
| `cka-2.8-scheduler-lifecycle` | Scheduler & Lifecycle Theory | K8s | 30 min | Advanced |
| `cka-2.9-autoscaling` | Workload Autoscaling | K8s | 40 min | Advanced |

**Acceptance Criteria**: Same per-lab/batch structure as Epic 2.

---

## Epic 4: Linux Labs — Foundations

**Milestone**: M4 (Week 6-8)
**Goal**: Ship labs for the most hands-on Linux modules.

### E4.1 — Linux Everyday Use Labs (5 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `linux-0.1-cli-power-user` | CLI Power User | Ubuntu | 30 min | Intermediate |
| `linux-0.2-environment-permissions` | Environment & Permissions | Ubuntu | 30 min | Intermediate |
| `linux-0.3-processes-resources` | Processes & Resources | Ubuntu | 35 min | Intermediate |
| `linux-0.4-services-logs` | Services & Logs | Ubuntu | 30 min | Intermediate |
| `linux-0.5-networking-tools` | Networking Tools | Ubuntu | 35 min | Intermediate |

**Acceptance Criteria**: Same per-lab/batch structure.

### E4.2 — Linux System Essentials Labs (4 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `linux-1.1-kernel-architecture` | Kernel Architecture | Ubuntu | 35 min | Advanced |
| `linux-1.2-processes-systemd` | Processes & systemd | Ubuntu | 35 min | Intermediate |
| `linux-1.3-filesystem-hierarchy` | Filesystem Hierarchy | Ubuntu | 30 min | Intermediate |
| `linux-1.4-users-permissions` | Users & Permissions | Ubuntu | 30 min | Intermediate |

**Acceptance Criteria**: Same per-lab/batch structure.

### E4.3 — Linux Networking Labs (4 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `linux-3.1-tcp-ip` | TCP/IP Essentials | Ubuntu | 35 min | Intermediate |
| `linux-3.2-dns` | DNS on Linux | Ubuntu | 30 min | Intermediate |
| `linux-3.3-network-namespaces` | Network Namespaces | Ubuntu | 40 min | Advanced |
| `linux-3.4-iptables` | iptables & Netfilter | Ubuntu | 45 min | Advanced |

**Acceptance Criteria**: Same per-lab/batch structure.

---

## Epic 5: CKA Labs — Advanced

**Milestone**: M5 (Week 8-11)
**Goal**: Complete CKA lab coverage with Parts 3-5.

### E5.1 — CKA Part 3: Services & Networking Labs (8 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `cka-3.1-services` | Services | K8s | 40 min | Intermediate |
| `cka-3.2-endpoints` | Endpoints | K8s | 30 min | Intermediate |
| `cka-3.3-dns` | DNS | K8s | 35 min | Intermediate |
| `cka-3.4-ingress` | Ingress | K8s | 40 min | Intermediate |
| `cka-3.5-gateway-api` | Gateway API | K8s | 40 min | Advanced |
| `cka-3.6-network-policies` | Network Policies | K8s | 45 min | Advanced |
| `cka-3.7-cni` | CNI | K8s | 35 min | Advanced |
| `cka-3.8-cluster-networking` | Cluster Networking Data Path | K8s | 40 min | Advanced |

### E5.2 — CKA Part 4: Storage Labs (5 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `cka-4.1-volumes` | Volumes | K8s | 35 min | Intermediate |
| `cka-4.2-pv-pvc` | PV & PVC | K8s | 40 min | Intermediate |
| `cka-4.3-storageclasses` | StorageClasses | K8s | 35 min | Intermediate |
| `cka-4.4-snapshots` | Snapshots | K8s | 30 min | Advanced |
| `cka-4.5-troubleshooting` | Storage Troubleshooting | K8s | 40 min | Advanced |

### E5.3 — CKA Part 5: Troubleshooting Labs (7 labs)

| Lab ID | Module | Environment | Duration | Difficulty |
|--------|--------|-------------|----------|------------|
| `cka-5.1-methodology` | Troubleshooting Methodology | K8s | 30 min | Intermediate |
| `cka-5.2-application-failures` | Application Failures | K8s | 45 min | Intermediate |
| `cka-5.3-control-plane` | Control Plane Issues | K8s | 45 min | Advanced |
| `cka-5.4-worker-nodes` | Worker Node Issues | K8s | 40 min | Advanced |
| `cka-5.5-networking` | Networking Issues | K8s | 45 min | Advanced |
| `cka-5.6-services` | Service Issues | K8s | 35 min | Intermediate |
| `cka-5.7-logging-monitoring` | Logging & Monitoring | K8s | 35 min | Intermediate |

**Acceptance Criteria** for all E5 sub-epics: Same per-lab/batch structure.

---

## Epic 6: Supabase Migration (When Pitching Investors)

**Milestone**: M6 (when needed)
**Goal**: Add real user accounts and server-side progress tracking for investor demo.

### E6.1 — Supabase Setup

**Acceptance Criteria**:
- [ ] Supabase project created (free tier)
- [ ] GitHub OAuth provider configured
- [ ] Database tables created: `users`, `lab_progress`, `daily_streaks`
- [ ] Row-level security policies: users can only read/write own data
- [ ] REST API tested with sample data

### E6.2 — Auth Integration

**Acceptance Criteria**:
- [ ] "Sign in with GitHub" button in site nav
- [ ] Supabase Auth JS client integrated (~5KB)
- [ ] Login/logout flow works
- [ ] User avatar + name shown when logged in
- [ ] Auth state persists across page loads (Supabase handles this)

### E6.3 — Progress Migration

**Acceptance Criteria**:
- [ ] On first login, localStorage progress auto-migrates to Supabase
- [ ] Subsequent progress saves to both localStorage (cache) and Supabase (source of truth)
- [ ] Dashboard page (`/labs/dashboard`) reads from Supabase
- [ ] Fallback to localStorage if Supabase unreachable
- [ ] Aggregate stats query: total users, total completions, popular labs

### E6.4 — Investor Dashboard

**Acceptance Criteria**:
- [ ] Admin-only page showing aggregate engagement metrics
- [ ] Metrics: total users, daily active users, labs completed/day, most popular labs, completion rates
- [ ] Exportable as CSV for pitch decks
- [ ] Protected by admin check (your GitHub username only)

---

## Scenario Authoring Standards

Every lab must follow these standards:

### File Structure
```
scenario-name/
├── index.json          # metadata + step definitions
├── intro.md            # context + objectives (link to KubeDojo module)
├── setup.sh            # seeds environment before user starts
├── step1/
│   ├── text.md         # instructions (what to do)
│   └── verify.sh       # validation script (exit 0 = pass, exit 1 = fail)
├── step2/
│   ├── text.md
│   └── verify.sh
├── ...
└── finish.md           # congratulations + link to next lab + "Mark Complete" reminder
```

### Scenario Guidelines
1. **3-6 steps per lab** — focused, completable within the time limit
2. **Each step = one concept** — don't overload a single step
3. **verify.sh must be deterministic** — check exact state, not output format
4. **setup.sh must be idempotent** — safe to run multiple times
5. **intro.md links back** to the corresponding KubeDojo module for theory
6. **finish.md links forward** to the next lab in sequence
7. **No copy-paste answers** — steps should require understanding, not just pasting commands
8. **Hints in text.md** — use collapsible sections for hints:
   ```markdown
   <details>
   <summary>Hint</summary>
   Try `kubectl get pods -n production`
   </details>
   ```

### verify.sh Pattern
```bash
#!/bin/bash
# Always use exact checks, not string matching on output
# Good:
kubectl get pod nginx -o jsonpath='{.status.phase}' 2>/dev/null | grep -q "Running"

# Bad (fragile):
kubectl get pods | grep "nginx" | grep "Running"
```

### Difficulty Calibration
| Difficulty | Steps | Hints | Hand-holding |
|---|:---:|---|---|
| Beginner | 3-4 | Generous, near-complete commands | High — almost tells you what to type |
| Intermediate | 4-5 | Concept hints, not command hints | Medium — tells you what to do, not how |
| Advanced | 5-6 | Minimal, doc references only | Low — just the objective, figure it out |

---

## Lab-to-Module Mapping Convention

**Lab ID format**: `{track}-{part}.{module}-{slug}`

Examples:
- `cka-2.1-pods` → CKA Part 2, Module 1 (Pods)
- `prereq-0.3-first-commands` → Prerequisites, Zero to Terminal, Module 3
- `linux-3.4-iptables` → Linux, Networking, Module 4

**Killercoda URL**: `https://killercoda.com/kubedojo/scenario/{lab-id}`

**Module frontmatter**:
```yaml
lab:
  id: "cka-2.1-pods"
  url: "https://killercoda.com/kubedojo/scenario/cka-2.1-pods"
  duration: "40 min"
  difficulty: "intermediate"
  environment: "kubernetes"
```

---

## Definition of Done (per lab)

- [ ] Scenario files in `kubedojo-labs` repo
- [ ] All steps completable on Killercoda (manual test)
- [ ] verify.sh passes for correct actions, fails for incorrect
- [ ] Corresponding KubeDojo module has `lab:` frontmatter
- [ ] LabBanner renders correctly on module page
- [ ] `npm run build` passes
- [ ] PR reviewed (scenario content + module frontmatter)
