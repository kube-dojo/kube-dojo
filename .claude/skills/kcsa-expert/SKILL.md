---
name: kcsa-expert
description: KCSA exam knowledge. Use for Kubernetes security associate certification, security fundamentals, threat modeling. Triggers on "KCSA", "security associate", "cloud native security fundamentals".
---

# KCSA Expert Skill

Authoritative knowledge source for KCSA (Kubernetes and Cloud Native Security Associate) exam preparation. Associate-level multiple choice certification covering security fundamentals.

## When to Use
- Writing or reviewing KCSA curriculum content
- Explaining Kubernetes security concepts
- Bridging gap between CKA and CKS
- Security fundamentals for beginners

## KCSA Exam Overview

### Exam Format
- **Duration**: 90 minutes
- **Questions**: ~60 multiple choice questions
- **Passing Score**: 75%
- **Format**: Multiple choice (NOT hands-on)
- **Prerequisites**: None (but CKA knowledge helpful)

### Domain Weights

| Domain | Weight |
|--------|--------|
| Overview of Cloud Native Security | 14% |
| Kubernetes Cluster Component Security | 22% |
| Kubernetes Security Fundamentals | 22% |
| Kubernetes Threat Model | 16% |
| Platform Security | 16% |
| Compliance and Security Frameworks | 10% |

## Key Topics

### Overview of Cloud Native Security (14%)
- The 4 Cs of cloud native security (Cloud, Cluster, Container, Code)
- Cloud provider security responsibilities
- Security principles (defense in depth, least privilege)

### Kubernetes Cluster Component Security (22%)
- Control plane security (API server, etcd, scheduler)
- Node security (kubelet, container runtime)
- Network security (CNI, service mesh)
- PKI and certificate management

### Kubernetes Security Fundamentals (22%)
- Pod security (SecurityContext, Pod Security Standards)
- Secrets management
- RBAC fundamentals
- ServiceAccount security
- Network policies

### Kubernetes Threat Model (16%)
- Attack surfaces in Kubernetes
- Common vulnerabilities
- Threat actors and motivations
- Container escape risks
- Supply chain threats

### Platform Security (16%)
- Image security and scanning
- Registry security
- Admission controllers
- Runtime security concepts
- Audit logging

### Compliance and Security Frameworks (10%)
- CIS Benchmarks
- NIST frameworks
- Compliance requirements
- Security assessment tools

## KCSA vs CKS

| Aspect | KCSA | CKS |
|--------|------|-----|
| Format | Multiple choice | Hands-on |
| Difficulty | Associate | Specialist |
| Focus | Security concepts | Security implementation |
| Duration | 90 min | 120 min |
| Prerequisites | None | Active CKA |

## Study Approach

Conceptual security focus:
- **The 4 Cs model** of cloud native security
- **Threat modeling** mindset
- **Security frameworks** (CIS, NIST)
- **Common vulnerabilities** and mitigations

## Exam Strategy

For multiple choice security:
1. **Think "defense in depth"** - usually the most secure answer
2. **Least privilege principle** - restrict by default
3. **Know the 4 Cs** - many questions map to this model
4. **Understand attack vectors** not just defenses

## Bridge to CKS

KCSA concepts prepare for CKS hands-on:
- Understand WHY before HOW
- Security theory → practical implementation
- Framework knowledge helps prioritize CKS study

## Official Resources

- [CNCF Curriculum](https://github.com/cncf/curriculum)
- [KCSA Program](https://training.linuxfoundation.org/certification/kubernetes-and-cloud-native-security-associate-kcsa/)
- [Kubernetes Security Documentation](https://kubernetes.io/docs/concepts/security/)
