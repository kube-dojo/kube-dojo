---
name: cks-expert
description: CKS exam knowledge. Use for Kubernetes security certification, cluster hardening, runtime security. Triggers on "CKS", "security specialist", "cluster security", "Falco", "Trivy".
---

# CKS Expert Skill

Authoritative knowledge source for CKS (Certified Kubernetes Security Specialist) exam preparation. Advanced security certification requiring active CKA.

## When to Use
- Writing or reviewing CKS curriculum content
- Answering questions about Kubernetes security
- Cluster hardening and security best practices
- Security tool recommendations (Falco, Trivy, OPA)

## CKS Exam Overview

### Exam Format
- **Duration**: 2 hours (120 minutes)
- **Questions**: ~15-20 performance-based tasks
- **Passing Score**: 67%
- **Prerequisite**: Active CKA certification
- **Environment**: Ubuntu-based, kubeadm clusters
- **Resources Allowed**: kubernetes.io, helm.sh, github.com/kubernetes, Trivy docs, Falco docs

### Domain Weights

| Domain | Weight |
|--------|--------|
| Cluster Setup | 10% |
| Cluster Hardening | 15% |
| System Hardening | 15% |
| Minimize Microservice Vulnerabilities | 20% |
| Supply Chain Security | 20% |
| Monitoring, Logging and Runtime Security | 20% |

## Key Topics

### Cluster Setup (10%)
- Network security policies
- CIS Benchmarks for Kubernetes
- Ingress security (TLS)
- Node metadata protection
- GUI access restrictions

### Cluster Hardening (15%)
- RBAC (advanced)
- ServiceAccount security
- Restrict API access
- Upgrade Kubernetes frequently
- Minimize platform access

### System Hardening (15%)
- Minimize host OS footprint
- Minimize IAM roles
- Minimize external access to network
- AppArmor, seccomp profiles
- Kernel hardening

### Minimize Microservice Vulnerabilities (20%)
- Security contexts
- Pod Security Standards/Admission
- Secrets management
- Container sandboxing (gVisor, Kata)
- mTLS, service mesh security

### Supply Chain Security (20%)
- Minimize base image footprint
- Image signing and verification
- Static analysis (kubesec, etc.)
- Image vulnerability scanning (Trivy)
- SBOM (Software Bill of Materials)

### Monitoring and Runtime Security (20%)
- Behavioral analytics
- Falco for threat detection
- Immutable containers
- Audit logs
- Investigate runtime incidents

## Key Security Tools

| Tool | Purpose |
|------|---------|
| **Trivy** | Container image vulnerability scanning |
| **Falco** | Runtime threat detection |
| **OPA/Gatekeeper** | Policy enforcement |
| **kube-bench** | CIS benchmark checking |
| **kubesec** | Static analysis of manifests |

## CKS vs CKA

CKS builds on CKA with:
- Deeper RBAC scenarios
- Advanced NetworkPolicies
- Security-specific tools
- Threat modeling mindset
- Compliance requirements

## Exam Strategy

Security-focused three-pass:
1. **Pass 1**: Quick RBAC, basic NetworkPolicies
2. **Pass 2**: Security contexts, Pod Security Admission
3. **Pass 3**: Falco rules, incident investigation, complex scenarios

## 2024/2025 Updates

Recent additions:
- Cilium (CNI with security features)
- SBOM requirements
- Trivy emphasis
- Supply chain security focus

## Official Resources

- [CNCF Curriculum](https://github.com/cncf/curriculum)
- [CKS Program](https://training.linuxfoundation.org/certification/certified-kubernetes-security-specialist/)
- [CKS Program Changes](https://training.linuxfoundation.org/cks-program-changes/)
- [Falco Docs](https://falco.org/docs/)
- [Trivy Docs](https://aquasecurity.github.io/trivy/)
