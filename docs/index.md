# KubeDojo

**Free, comprehensive cloud native education.**

Kubernetes certifications. Platform engineering. SRE. DevSecOps. MLOps.

No paywalls. No upsells. Theory-first.

> **March 2026 Update**: Now covering **21 certifications** including PCA, ICA, CCA, CGOA, LFCS, and FinOps. 40+ new modules, K8s 1.35 support, every module quality-reviewed. [See what's new &rarr;](changelog.md)

---

## 🇺🇦 Присвята

*Цей проєкт присвячується українським ІТ-інженерам, які віддали своє життя, захищаючи Батьківщину.*

*Вони були розробниками, DevOps-інженерами, системними адміністраторами. Вони будували системи, писали код, підтримували інфраструктуру. Коли прийшла війна, вони залишили клавіатури й взяли зброю.*

*Їхній код живе. Їхня жертва — вічна. Слава Україні.*

### Заповіт
*Тарас Шевченко, 1845*

> Як умру, то поховайте  
> Мене на могилі,  
> Серед степу широкого,  
> На Вкраїні милій,  
> Щоб лани широкополі,  
> І Дніпро, і кручі  
> Було видно, було чути,  
> Як реве ревучий.
>
> Як понесе з України  
> У синєє море  
> Кров ворожу... отойді я  
> І лани і гори —  
> Все покину і полину  
> До самого Бога  
> Молитися... а до того  
> Я не знаю Бога.
>
> Поховайте та вставайте,  
> Кайдани порвіте  
> І вражою злою кров'ю  
> Волю окропіте.  
> І мене в сем'ї великій,  
> В сем'ї вольній, новій,  
> Не забудьте пом'янути  
> Незлим тихим словом.

---

## Learning Path

```
                              KUBEDOJO
    ═══════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   PREREQUISITES                        "Why Kubernetes?"│
    │   └── docs/prerequisites/                               │
    │       ├── Philosophy & Design          4 modules        │
    │       ├── Cloud Native 101             5 modules        │
    │       ├── Kubernetes Basics            8 modules        │
    │       └── Modern DevOps                6 modules        │
    │                                                         │
    └────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────────────┐   ┌─────────────────────────┐
    │                         │   │                         │
    │   LINUX DEEP DIVE       │   │   CERTIFICATIONS        │
    │   └── docs/linux/       │   │   └── docs/k8s/         │
    │       │                 │   │       │                 │
    │       ├── foundations/  │   │       │  ENTRY LEVEL    │
    │       │  System · Cgroup│   │       ├── KCNA          │
    │       │  Network        │   │       ├── KCSA          │
    │       │                 │   │       │                 │
    │       ├── security/     │   │       │  PRACTITIONER   │
    │       │  Hardening      │   │       ├── CKAD          │
    │       │                 │   │       ├── CKA           │
    │       └── operations/   │   │       ├── CKS           │
    │          Perf · Debug   │   │       │                 │
    │          Shell Scripts  │   │       │  SPECIALIST     │
    │                         │   │       ├── CNPE          │
    │                         │   │       │                 │
    │                         │   │       │  TOOL CERTS     │
    │                         │   │       ├── PCA  (Prometheus)
    │                         │   │       ├── ICA  (Istio)  │
    │                         │   │       ├── CCA  (Cilium) │
    │                         │   │       ├── CBA  (Backstage)
    │                         │   │       ├── OTCA (OTel)   │
    │                         │   │       ├── KCA  (Kyverno)│
    │                         │   │       ├── CAPA (Argo)   │
    │                         │   │       ├── CGOA (GitOps) │
    │                         │   │       │                 │
    │                         │   │       │  OTHER          │
    │  + LFCS (Linux Sysadmin)│   │       ├── CNPA (Platform)
    │                         │   │       └── FinOps        │
    │                         │   │                         │
    └────────────┬────────────┘   └────────────┬────────────┘
                 │                             │
                 └──────────────┬──────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   PLATFORM ENGINEERING              Beyond Certifications│
    │   └── docs/platform/                                    │
    │       │                                                 │
    │       ├── foundations/         Theory that doesn't change│
    │       │   Systems Thinking · Reliability · Distributed  │
    │       │   Systems · Observability Theory · Security     │
    │       │                                                 │
    │       ├── disciplines/         Applied practices        │
    │       │   SRE · Platform Engineering · GitOps ·         │
    │       │   DevSecOps · MLOps · AIOps · IaC              │
    │       │                                                 │
    │       └── toolkits/            Current tools (evolving) │
    │           Prometheus · ArgoCD · Vault · Backstage ·     │
    │           Kyverno · Cilium · Kubeflow · OpenCost ·     │
    │           Rook/Ceph · MetalLB · SPIFFE · and more...   │
    │                                                         │
    └─────────────────────────────────────────────────────────┘

    ═══════════════════════════════════════════════════════════
```

---

## Status

| Track | Modules | Status |
|-------|---------|--------|
| [Prerequisites](prerequisites/README.md) | 23 | ✅ Complete |
| [CKA](k8s/cka/README.md) | 41 | ✅ Complete (K8s 1.35) |
| [CKAD](k8s/ckad/README.md) | 24 | ✅ Complete (K8s 1.35) |
| [CKS](k8s/cks/README.md) | 30 | ✅ Complete (K8s 1.34) |
| [KCNA](k8s/kcna/README.md) | 25 | ✅ Complete |
| [KCSA](k8s/kcsa/README.md) | 26 | ✅ Complete |
| [CNPE](k8s/cnpe/README.md) | Learning Path | ✅ Maps 60+ modules |
| [CBA](k8s/cba/README.md) | Learning Path | ✅ Backstage cert prep |
| [OTCA](k8s/otca/README.md) | Learning Path | ✅ OpenTelemetry cert prep |
| [KCA](k8s/kca/README.md) | Learning Path | ✅ Kyverno cert prep |
| [CAPA](k8s/capa/README.md) | Learning Path | ✅ Argo Project cert prep |
| [PCA](k8s/pca/README.md) | Learning Path | ✅ Prometheus cert prep |
| [ICA](k8s/ica/README.md) | Learning Path | ✅ Istio cert prep |
| [CCA](k8s/cca/README.md) | Learning Path | ✅ Cilium cert prep |
| [CGOA](k8s/cgoa/README.md) | Learning Path | ✅ GitOps cert prep |
| [CNPA](k8s/cnpa/README.md) | Learning Path | ✅ Platform Associate prep |
| [LFCS](k8s/lfcs/README.md) | Learning Path | ✅ Linux Sysadmin cert prep |
| [FinOps](k8s/finops/README.md) | Learning Path | ✅ FinOps Practitioner prep |
| [Linux Deep Dive](linux/README.md) | 30 | ✅ Complete |
| [Platform Engineering](platform/README.md) | 154 | ✅ Complete |
| **Total** | **370+** | |

---

## Where to Start

| You are... | Start here |
|------------|------------|
| New to containers/K8s | [Prerequisites](prerequisites/README.md) |
| Want deep Linux knowledge | [Linux Deep Dive](linux/README.md) |
| Want K8s admin certification | [CKA](k8s/cka/README.md) |
| Want K8s developer certification | [CKAD](k8s/ckad/README.md) |
| Want K8s security certification | [CKS](k8s/cks/README.md) |
| Entry-level K8s cert | [KCNA](k8s/kcna/README.md) (general) or [KCSA](k8s/kcsa/README.md) (security) |
| Platform engineer | [CNPE Learning Path](k8s/cnpe/README.md) |
| Prometheus cert | [PCA](k8s/pca/README.md) |
| Istio / Service Mesh cert | [ICA](k8s/ica/README.md) |
| Cilium / Networking cert | [CCA](k8s/cca/README.md) |
| GitOps cert | [CGOA](k8s/cgoa/README.md) |
| Backstage / OTel / Kyverno / Argo cert | [CBA](k8s/cba/README.md) · [OTCA](k8s/otca/README.md) · [KCA](k8s/kca/README.md) · [CAPA](k8s/capa/README.md) |
| Linux sysadmin cert | [LFCS](k8s/lfcs/README.md) |
| Cloud cost management | [FinOps](k8s/finops/README.md) |
| Already certified, want depth | [Platform Engineering](platform/README.md) |

---

## Why This Exists

A free, text-based curriculum for learning Kubernetes and platform engineering.

- **Free** — No paywalls, open source
- **Theory-first** — Understand principles before tools
- **Text-based** — Searchable, version-controlled, no videos

**What we are not:** A replacement for paid courses like KodeKloud or Udemy. We don't offer mock exams, video lessons, or hands-on labs for every module. For exam simulation, use [killer.sh](https://killer.sh). For interactive labs, use [killercoda.com](https://killercoda.com).

---

## Philosophy

**Theory before hands-on.** You can't troubleshoot what you don't understand.

**No memorization.** K8s docs are available during exams. We teach navigation, not YAML memorization.

**Principles over tools.** Tools change. Foundations don't. Learn both, in that order.

---

## Contributing

**What we need:**
- **Hands-on exercises** — Real scenarios, not toy examples
- **War stories** — Production incidents that teach lessons
- **Tool expertise** — Deep-dives on ArgoCD, Prometheus, Vault, etc.
- **Error fixes** — Typos, outdated commands, broken YAML

**What we don't build:**
- Exam simulators — Use [killer.sh](https://killer.sh) (included with exam purchase)
- Lab environments — Use [killercoda.com](https://killercoda.com) or local kind/minikube
- Video content — Text-first, searchable, version-controlled

**How to contribute:**
- Open an issue to discuss before large PRs
- Follow existing module structure
- Test all commands and YAML before submitting

---

## License

MIT License. Free to use, share, and modify.

---

*"In the dojo, everyone starts as a white belt. What matters is showing up to train."*
