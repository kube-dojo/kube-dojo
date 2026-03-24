# Kubernetes Certifications

**The Kubestronaut Path** — All 5 certifications required for [Kubestronaut](https://www.cncf.io/training/kubestronaut/) status.

---

## Overview

```
                        KUBESTRONAUT PATH
    ════════════════════════════════════════════════════════

    ENTRY LEVEL (multiple choice, 90 min)
    ┌──────────────────────────────────────────────────────┐
    │  KCNA   Kubernetes & Cloud Native Associate          │
    │         └── Conceptual understanding of K8s & CNCF   │
    │                                                      │
    │  KCSA   Kubernetes & Cloud Native Security Associate │
    │         └── Security concepts and threat modeling    │
    └──────────────────────────────────────────────────────┘
                             │
                             ▼
    PRACTITIONER LEVEL (hands-on lab, 2 hours)
    ┌──────────────────────────────────────────────────────┐
    │  CKAD   Certified Kubernetes Application Developer   │
    │         └── Build and deploy applications            │
    │                                                      │
    │  CKA    Certified Kubernetes Administrator           │
    │         └── Install, configure, manage clusters      │
    │                                                      │
    │  CKS    Certified Kubernetes Security Specialist     │
    │         └── Secure clusters end-to-end (requires CKA)│
    └──────────────────────────────────────────────────────┘

    ════════════════════════════════════════════════════════
```

---

## Certifications

| Cert | Name | Type | Modules | Curriculum |
|------|------|------|---------|------------|
| [KCNA](kcna/README.md) | Kubernetes & Cloud Native Associate | Multiple choice | 21 | [Details](kcna/README.md) |
| [KCSA](kcsa/README.md) | Security Associate | Multiple choice | 25 | [Details](kcsa/README.md) |
| [CKAD](ckad/README.md) | Application Developer | Hands-on lab | 28 | [Details](ckad/README.md) |
| [CKA](cka/README.md) | Administrator | Hands-on lab | 38 | [Details](cka/README.md) |
| [CKS](cks/README.md) | Security Specialist | Hands-on lab | 30 | [Details](cks/README.md) |
| | **Total** | | **142** | |

---

## Suggested Order

**Option 1: Breadth First** (understand the landscape)
```
KCNA → KCSA → CKAD → CKA → CKS
```

**Option 2: Depth First** (production admin focus)
```
CKA → CKAD → CKS → KCNA → KCSA
```

**Option 3: Developer Path**
```
KCNA → CKAD → (stop here or continue to CKA)
```

**Option 4: Security Path**
```
CKA → CKS → KCSA
```

---

## Exam Tips

All exams share these characteristics:
- **PSI Bridge proctoring** — Strict environment, webcam required
- **kubernetes.io allowed** — Official docs are your friend
- **Time pressure** — Speed matters as much as knowledge

For hands-on exams (CKAD, CKA, CKS):
- Practice with `kubectl` until it's muscle memory
- Master vim/nano for YAML editing
- Use `kubectl explain` and `--dry-run=client -o yaml`
- [killer.sh](https://killer.sh) included with exam purchase — use it

---

## Curriculum Sources

We track official CNCF curricula:
- [CNCF Curriculum Repository](https://github.com/cncf/curriculum)
- [CKA Program Changes](https://training.linuxfoundation.org/certified-kubernetes-administrator-cka-program-changes/)
- [CKS Program Changes](https://training.linuxfoundation.org/cks-program-changes/)
