---
title: "Module 6.3: Security Assessments"
slug: k8s/kcsa/part6-compliance/module-6.3-security-assessments
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Conceptual knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 6.2: CIS Benchmarks](../module-6.2-cis-benchmarks/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Compare** assessment types: vulnerability scans, penetration tests, security audits, and threat models
2. **Evaluate** Kubernetes security posture using structured assessment methodologies
3. **Assess** findings from security assessments to prioritize remediation by risk
4. **Design** an ongoing security assessment program for Kubernetes environments

---

## Why This Module Matters

Security assessments evaluate your Kubernetes security posture through systematic analysis, testing, and review. Understanding assessment types and processes helps you identify gaps, prioritize improvements, and demonstrate security to stakeholders.

KCSA tests your understanding of threat modeling, security assessments, and audit processes.

---

## Assessment Types

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY ASSESSMENT TYPES                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VULNERABILITY ASSESSMENT                                  │
│  ├── Automated scanning of known vulnerabilities          │
│  ├── Image scanning, config scanning                      │
│  ├── Low skill barrier                                    │
│  └── Examples: Trivy, kube-bench                         │
│                                                             │
│  PENETRATION TESTING                                       │
│  ├── Active exploitation attempts                         │
│  ├── Simulates real attacker                              │
│  ├── Requires skilled testers                             │
│  └── Examples: kube-hunter, manual testing                │
│                                                             │
│  SECURITY AUDIT                                            │
│  ├── Review of policies, procedures, configurations       │
│  ├── May include interviews and document review           │
│  ├── Compliance-focused                                   │
│  └── Examples: SOC 2 audit, internal audit                │
│                                                             │
│  THREAT MODELING                                           │
│  ├── Systematic analysis of potential threats             │
│  ├── Design-time or runtime analysis                      │
│  ├── Identifies attack paths                              │
│  └── Examples: STRIDE, attack trees                       │
│                                                             │
│  RED TEAM EXERCISE                                         │
│  ├── Full adversary simulation                            │
│  ├── Tests detection and response                         │
│  ├── Highly skilled team                                  │
│  └── Combines multiple techniques                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Threat Modeling

### STRIDE Framework

```
┌─────────────────────────────────────────────────────────────┐
│              STRIDE THREAT MODEL                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STRIDE = Common threat categories                         │
│                                                             │
│  S - SPOOFING                                              │
│  ├── Pretending to be someone/something else              │
│  ├── K8s: Fake service account, stolen credentials        │
│  └── Control: Strong authentication, mutual TLS           │
│                                                             │
│  T - TAMPERING                                             │
│  ├── Modifying data or code                               │
│  ├── K8s: Image modification, config changes              │
│  └── Control: Signing, integrity checks, RBAC             │
│                                                             │
│  R - REPUDIATION                                           │
│  ├── Denying actions were performed                       │
│  ├── K8s: Deleting audit logs                             │
│  └── Control: Audit logging, immutable logs               │
│                                                             │
│  I - INFORMATION DISCLOSURE                                │
│  ├── Unauthorized access to information                   │
│  ├── K8s: Secret exposure, API enumeration                │
│  └── Control: Encryption, RBAC, network policies          │
│                                                             │
│  D - DENIAL OF SERVICE                                     │
│  ├── Making system unavailable                            │
│  ├── K8s: Resource exhaustion, API flooding               │
│  └── Control: Resource limits, rate limiting              │
│                                                             │
│  E - ELEVATION OF PRIVILEGE                                │
│  ├── Gaining unauthorized access                          │
│  ├── K8s: Container escape, RBAC escalation               │
│  └── Control: Least privilege, pod security               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: STRIDE identifies threats but doesn't tell you which are most dangerous. If you applied STRIDE to a Kubernetes ingress controller and found threats in all 6 categories, how would you decide which to address first?

### Threat Modeling Process

```
┌─────────────────────────────────────────────────────────────┐
│              THREAT MODELING STEPS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DECOMPOSE THE SYSTEM                                   │
│     ├── Identify components (pods, services, etc.)        │
│     ├── Map data flows                                    │
│     ├── Identify trust boundaries                         │
│     └── Document entry points                             │
│                                                             │
│  2. IDENTIFY THREATS                                       │
│     ├── Apply STRIDE to each component                    │
│     ├── Consider threat actors                            │
│     ├── Identify attack paths                             │
│     └── Document assumptions                              │
│                                                             │
│  3. ASSESS RISKS                                           │
│     ├── Likelihood × Impact                               │
│     ├── Consider existing controls                        │
│     ├── Prioritize threats                                │
│     └── Identify residual risk                            │
│                                                             │
│  4. MITIGATE                                               │
│     ├── Implement controls                                │
│     ├── Accept, transfer, or avoid risks                  │
│     ├── Document decisions                                │
│     └── Track remediation                                 │
│                                                             │
│  5. VALIDATE                                               │
│     ├── Verify controls work                              │
│     ├── Test attack scenarios                             │
│     └── Update model as system changes                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubernetes Attack Paths

```
┌─────────────────────────────────────────────────────────────┐
│              COMMON KUBERNETES ATTACK PATHS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL → INITIAL ACCESS                                 │
│  ├── Exposed dashboard (no auth)                          │
│  ├── Vulnerable application                               │
│  ├── Stolen credentials                                   │
│  ├── Supply chain (malicious image)                       │
│  └── Misconfigured ingress                                │
│                                                             │
│  POD → LATERAL MOVEMENT                                    │
│  ├── Service account token → API access                   │
│  ├── Network scanning → other pods                        │
│  ├── Mounted secrets → credentials                        │
│  └── Shared volumes → data access                         │
│                                                             │
│  POD → PRIVILEGE ESCALATION                                │
│  ├── Privileged container → host access                   │
│  ├── hostPath mount → host filesystem                     │
│  ├── RBAC → create privileged pod                         │
│  └── Container escape → node compromise                   │
│                                                             │
│  NODE → CLUSTER COMPROMISE                                 │
│  ├── Kubelet access → all pods on node                    │
│  ├── etcd access → all cluster data                       │
│  ├── Node credentials → cloud provider                    │
│  └── Pivot to other nodes                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Penetration Testing

### Kubernetes Penetration Testing Scope

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES PENTEST SCOPE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL TESTING                                          │
│  ├── API server access without credentials               │
│  ├── Exposed services (ingress, NodePort)                │
│  ├── Dashboard/UI access                                 │
│  ├── Application vulnerabilities                         │
│  └── Information disclosure                              │
│                                                             │
│  INTERNAL TESTING (from pod)                              │
│  ├── Service account token usage                         │
│  ├── API access from pods                                │
│  ├── Network reachability                                │
│  ├── Container escape attempts                           │
│  ├── Kubelet API access                                  │
│  └── Secrets access                                      │
│                                                             │
│  CONFIGURATION REVIEW                                      │
│  ├── RBAC permissions audit                              │
│  ├── Pod security settings                               │
│  ├── Network policy coverage                             │
│  └── CIS benchmark compliance                            │
│                                                             │
│  TOOLS:                                                    │
│  • kube-hunter - Automated security testing              │
│  • kubectl - Manual API exploration                      │
│  • Network tools - Scanning and enumeration              │
│  • Custom scripts - Specific attack scenarios            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### kube-hunter Usage

```bash
# Remote scanning (from outside cluster)
kube-hunter --remote 10.0.0.1

# Internal scanning (from inside pod)
kube-hunter --pod

# Network scanning
kube-hunter --cidr 10.0.0.0/24

# Active exploitation (use carefully!)
kube-hunter --active

# Output formats
kube-hunter --report json
kube-hunter --report yaml
```

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-HUNTER OUTPUT                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Vulnerabilities                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ID      : KHV001                                     │  │
│  │ Title   : Exposed API server                         │  │
│  │ Category: Information Disclosure                     │  │
│  │ Severity: Medium                                     │  │
│  │ Evidence: https://10.0.0.1:6443                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ID      : KHV005                                     │  │
│  │ Title   : Exposed Kubelet API                        │  │
│  │ Category: Remote Code Execution                      │  │
│  │ Severity: High                                       │  │
│  │ Evidence: https://10.0.0.2:10250/pods               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Audits

### Audit Process

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY AUDIT PROCESS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PLANNING                                               │
│     ├── Define scope (what's being audited)               │
│     ├── Identify stakeholders                             │
│     ├── Gather documentation                              │
│     ├── Schedule interviews                               │
│     └── Set timeline                                      │
│                                                             │
│  2. EVIDENCE GATHERING                                     │
│     ├── Configuration review                              │
│     ├── Policy documentation                              │
│     ├── Log analysis                                      │
│     ├── Automated scans                                   │
│     └── Interviews                                        │
│                                                             │
│  3. ANALYSIS                                               │
│     ├── Compare to requirements/standards                 │
│     ├── Identify gaps                                     │
│     ├── Assess control effectiveness                      │
│     └── Document findings                                 │
│                                                             │
│  4. REPORTING                                              │
│     ├── Executive summary                                 │
│     ├── Detailed findings                                 │
│     ├── Risk ratings                                      │
│     ├── Recommendations                                   │
│     └── Remediation timelines                             │
│                                                             │
│  5. REMEDIATION                                            │
│     ├── Create action plans                               │
│     ├── Implement fixes                                   │
│     ├── Verify fixes                                      │
│     └── Close findings                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What Auditors Look For

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES AUDIT CHECKLIST                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ACCESS CONTROL                                            │
│  ☐ RBAC configured with least privilege                   │
│  ☐ Service accounts properly managed                      │
│  ☐ Authentication mechanisms in place                     │
│  ☐ No anonymous access to API                             │
│  ☐ Regular access reviews documented                      │
│                                                             │
│  DATA PROTECTION                                           │
│  ☐ Secrets encrypted at rest                              │
│  ☐ TLS for all communications                             │
│  ☐ Secrets management process                             │
│  ☐ No sensitive data in environment variables             │
│                                                             │
│  LOGGING & MONITORING                                      │
│  ☐ Audit logging enabled and configured                   │
│  ☐ Log retention meets requirements                       │
│  ☐ Security monitoring in place                           │
│  ☐ Alerting configured                                    │
│                                                             │
│  NETWORK SECURITY                                          │
│  ☐ Network policies defined                               │
│  ☐ Ingress/egress controlled                              │
│  ☐ API server not publicly exposed                        │
│                                                             │
│  VULNERABILITY MANAGEMENT                                  │
│  ☐ Image scanning process                                 │
│  ☐ Patching procedures                                    │
│  ☐ Vulnerability tracking                                 │
│                                                             │
│  INCIDENT RESPONSE                                         │
│  ☐ Documented procedures                                  │
│  ☐ Contact lists                                          │
│  ☐ Evidence preservation                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Pause and predict**: A penetration test finds that kube-hunter can reach the kubelet API from inside a pod. The kubelet has anonymous auth disabled and uses webhook authorization. Is this still a finding, or has the defense worked as intended?

## Risk Assessment

### Risk Calculation

```
┌─────────────────────────────────────────────────────────────┐
│              RISK ASSESSMENT                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RISK = LIKELIHOOD × IMPACT                                │
│                                                             │
│  LIKELIHOOD FACTORS:                                       │
│  ├── Threat actor motivation                              │
│  ├── Attack complexity                                    │
│  ├── Existing controls                                    │
│  ├── Exposure level                                       │
│  └── Historical data                                      │
│                                                             │
│  IMPACT FACTORS:                                           │
│  ├── Data sensitivity                                     │
│  ├── System criticality                                   │
│  ├── Financial impact                                     │
│  ├── Reputational impact                                  │
│  └── Regulatory impact                                    │
│                                                             │
│  RISK MATRIX:                                              │
│               │ Low Impact │ Med Impact │ High Impact │    │
│  ─────────────┼────────────┼────────────┼─────────────│    │
│  High Likely  │   Medium   │    High    │  Critical   │    │
│  Med Likely   │    Low     │   Medium   │    High     │    │
│  Low Likely   │    Low     │    Low     │   Medium    │    │
│                                                             │
│  RESPONSE:                                                 │
│  Critical → Immediate action                              │
│  High → Action within days                                │
│  Medium → Action within weeks                             │
│  Low → Accept or plan for future                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Remediation Planning

```
┌─────────────────────────────────────────────────────────────┐
│              REMEDIATION PLANNING                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FOR EACH FINDING:                                         │
│                                                             │
│  1. UNDERSTAND                                             │
│     • What is the vulnerability?                          │
│     • What is the attack scenario?                        │
│     • What is the business impact?                        │
│                                                             │
│  2. PLAN                                                   │
│     • What is the fix?                                    │
│     • What are the dependencies?                          │
│     • What is the testing plan?                           │
│     • What is the rollback plan?                          │
│                                                             │
│  3. IMPLEMENT                                              │
│     • Make changes in non-prod first                      │
│     • Test thoroughly                                     │
│     • Document changes                                    │
│     • Get approval                                        │
│                                                             │
│  4. VERIFY                                                 │
│     • Re-test the vulnerability                           │
│     • Confirm fix is effective                            │
│     • Check for regression                                │
│                                                             │
│  5. CLOSE                                                  │
│     • Document evidence                                   │
│     • Update finding status                               │
│     • Notify stakeholders                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Metrics

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY METRICS                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VULNERABILITY METRICS                                     │
│  ├── Total vulnerabilities by severity                    │
│  ├── Mean time to remediate (MTTR)                        │
│  ├── Vulnerabilities past SLA                             │
│  └── New vs closed vulnerabilities                        │
│                                                             │
│  COMPLIANCE METRICS                                        │
│  ├── CIS benchmark pass rate                              │
│  ├── Policy violations                                    │
│  ├── Failed admissions                                    │
│  └── Compliance score over time                           │
│                                                             │
│  OPERATIONAL METRICS                                       │
│  ├── Audit log coverage                                   │
│  ├── Secrets rotation frequency                           │
│  ├── Image scan coverage                                  │
│  └── Network policy coverage                              │
│                                                             │
│  INCIDENT METRICS                                          │
│  ├── Mean time to detect (MTTD)                           │
│  ├── Mean time to respond (MTTR)                          │
│  ├── Incidents by category                                │
│  └── False positive rate                                  │
│                                                             │
│  TRACK OVER TIME:                                          │
│  • Trends matter more than absolute numbers               │
│  • Compare to baselines and targets                       │
│  • Report to leadership regularly                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **STRIDE was developed at Microsoft** in 1999 and remains one of the most widely used threat modeling frameworks.

- **Penetration testing on managed Kubernetes** requires cloud provider approval. AWS, GCP, and Azure have specific policies about testing their infrastructure.

- **Most security findings are misconfigurations**, not zero-days. Regular configuration assessments find more issues than penetration testing.

- **Threat modeling is most effective early**—it's cheaper to fix security issues during design than after deployment.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No threat model | Missing risks | Model before building |
| Testing only annually | Gaps accumulate | Continuous assessment |
| Not tracking metrics | Can't measure improvement | Build dashboards |
| Ignoring low findings | Chains to critical | Prioritize and plan all |
| No remediation tracking | Findings stay open | Use tracking system |

---

## Quiz

1. **You're threat-modeling a new microservice that processes customer PII. Using STRIDE, you identify 18 potential threats. Your team has capacity to address 6 before the launch deadline. How do you prioritize, and what do you do about the remaining 12?**
   <details>
   <summary>Answer</summary>
   Prioritize using Risk = Likelihood x Impact: rank each threat by how easily exploitable it is and how severe the consequences are. Focus on: Elevation of Privilege threats first (container escape, RBAC escalation — highest impact), then Information Disclosure for PII data (directly affects compliance and customers), then Spoofing of identity (enables other attacks). For the remaining 12: document them as known residual risks with specific owners and target dates, implement compensating controls where possible (e.g., monitoring to detect threats you can't prevent yet), and add them to the next sprint's backlog. Never treat unaddressed threats as "accepted" without explicit risk acceptance from management with awareness of the consequences.
   </details>

2. **A penetration tester runs kube-hunter from inside a pod and reports: "kubelet API reachable on port 10250." The kubelet has anonymous auth disabled and webhook authorization enabled. The tester marks this as a Medium finding. Your team argues it should be Informational since authentication is required. Who is correct?**
   <details>
   <summary>Answer</summary>
   Both have valid points, but the tester's Medium rating is more appropriate. While the kubelet's authentication prevents unauthorized access, network reachability to the kubelet API is still a finding because: (1) it increases attack surface — any future kubelet CVE (authentication bypass) is exploitable from any pod; (2) an attacker who obtains valid node credentials can access the kubelet; (3) the principle of least privilege says pods shouldn't reach infrastructure APIs they don't need. The defense is working (authentication blocks unauthorized access), but the exposure still exists. Proper remediation: NetworkPolicies blocking pod egress to node IP port 10250. This demonstrates that security assessments evaluate both current exploitability AND potential future risk.
   </details>

3. **Your organization conducts an annual penetration test and a quarterly vulnerability scan. Between assessments, a critical misconfiguration is introduced (default ServiceAccount given cluster-admin). It exists for 4 months before the next pentest finds it. How would you prevent this detection gap?**
   <details>
   <summary>Answer</summary>
   The 4-month gap illustrates why periodic assessments alone are insufficient. Prevention: (1) Continuous policy enforcement — Kyverno/OPA policy blocking cluster-admin bindings to default ServiceAccounts would prevent the misconfiguration from being created; (2) Continuous scanning — daily kube-bench or kubeaudit runs would detect it within 24 hours; (3) Git-based RBAC management — if all RBAC changes require PR review, the misconfiguration would be caught in code review; (4) Audit log alerting — a real-time alert on ClusterRoleBinding creation for cluster-admin would trigger within minutes; (5) Admission webhook — block the creation entirely. The best security programs combine periodic deep assessments (pentests) with continuous automated monitoring to eliminate blind spots between assessments.
   </details>

4. **An auditor asks for evidence that your Kubernetes cluster's access controls are effective. You provide a list of RBAC Roles and RoleBindings. The auditor says this is insufficient. What additional evidence demonstrates that access controls are not just configured but actually working?**
   <details>
   <summary>Answer</summary>
   RBAC configuration shows intent, not effectiveness. Additional evidence needed: (1) Audit logs showing access requests being denied (proves authorization is enforced) and allowed requests matching expected patterns; (2) Access review records showing regular RBAC reviews with specific changes made (outdated bindings removed); (3) Failed authentication logs showing unauthorized attempts are blocked; (4) Test results showing that a user without permissions actually receives "forbidden" errors; (5) Policy engine reports showing blocked admission requests (Kyverno/OPA violation counts); (6) Before/after evidence from a penetration test showing RBAC prevented escalation attempts. Auditors need evidence of control effectiveness over time (operational evidence), not just that controls are configured (design evidence). This is the difference between SOC 2 Type I (design) and Type II (operational effectiveness).
   </details>

5. **After completing a security assessment, you have findings across four categories: 3 Critical, 7 High, 15 Medium, and 25 Low. The total remediation estimate is 6 months of work. Management wants everything fixed in 3 months. How do you negotiate a realistic remediation plan?**
   <details>
   <summary>Answer</summary>
   Present a risk-based remediation plan: (1) Month 1: Fix all 3 Critical findings (these represent imminent compromise risk) and the 3 highest-impact High findings; (2) Month 2: Fix remaining 4 High findings and the 5 highest-risk Medium findings; (3) Month 3: Fix remaining 10 Medium findings with compensating controls for any that can't be completed; (4) Months 4-6: Address Low findings in normal sprint cycles. For findings that can't meet the 3-month deadline: implement compensating controls (monitoring to detect exploitation), document accepted residual risk with management sign-off, and track them on a compliance dashboard. Key negotiation points: Critical/High MUST be fixed within 3 months (regulatory risk), Medium/Low can follow an SLA (30/90 days) rather than a hard deadline. Risk acceptance decisions should come from business leadership, not the security team alone.
   </details>

---

## Hands-On Exercise: Threat Model

**Scenario**: Create a simple threat model for this architecture:

```
                    Internet
                        │
                   [Ingress]
                        │
            ┌───────────┴───────────┐
            │                       │
        [Frontend]             [Backend]
            │                       │
            └───────────┬───────────┘
                        │
                   [Database]
                        │
                    Secrets
```

**Apply STRIDE to each component:**

<details markdown="1">
<summary>Threat Model</summary>

**INGRESS:**

| Threat | Example | Mitigation |
|--------|---------|------------|
| S | Fake SSL cert | Valid certs, certificate pinning |
| T | Header injection | WAF, input validation |
| R | No access logs | Enable access logging |
| I | TLS downgrade | Force TLS 1.2+, HSTS |
| D | Request flooding | Rate limiting |
| E | Path traversal | Restrict paths, validate |

**FRONTEND:**

| Threat | Example | Mitigation |
|--------|---------|------------|
| S | Session hijacking | Secure cookies, short sessions |
| T | XSS | CSP, input sanitization |
| R | User denies actions | Audit logging |
| I | Source code exposure | Build optimization |
| D | Resource exhaustion | Resource limits |
| E | SA token abuse | No API access needed |

**BACKEND:**

| Threat | Example | Mitigation |
|--------|---------|------------|
| S | Stolen SA token | Disable auto-mount |
| T | Code injection | Input validation, parameterized queries |
| R | Missing audit trail | Application logging |
| I | Error message exposure | Generic errors |
| D | Query complexity attack | Query limits |
| E | RBAC escalation | Minimal permissions |

**DATABASE:**

| Threat | Example | Mitigation |
|--------|---------|------------|
| S | Credential theft | Rotate credentials, Vault |
| T | Data modification | Integrity constraints |
| R | Data changes | Database audit logs |
| I | SQL injection | Parameterized queries |
| D | Connection exhaustion | Connection pooling |
| E | Privilege escalation | Least privilege DB user |

**SECRETS:**

| Threat | Example | Mitigation |
|--------|---------|------------|
| S | Stolen credentials | Rotate regularly |
| T | Secret modification | RBAC, audit |
| R | Access without logs | Audit logging |
| I | Secret in logs | Scrub logs, don't log secrets |
| D | N/A | N/A |
| E | RBAC to read secrets | Minimal secret access |

**TOP RISKS:**
1. SA token leads to API access → Disable auto-mount
2. Database credentials exposed → Use Vault, rotate
3. No network isolation → NetworkPolicy
4. Missing audit logs → Enable audit logging

</details>

---

## Summary

Security assessments evaluate and improve Kubernetes security:

| Assessment Type | Purpose | Frequency |
|----------------|---------|-----------|
| **Threat Modeling** | Identify attack paths | Design time, major changes |
| **Vulnerability Scan** | Find known issues | Continuous |
| **Penetration Test** | Prove exploitability | Quarterly/annually |
| **Security Audit** | Verify compliance | Annually |

Key practices:
- Use STRIDE for systematic threat identification
- Combine automated and manual testing
- Track findings and remediation progress
- Measure security metrics over time
- Update threat models as systems change

---

## Congratulations!

You've completed the KCSA curriculum! You've learned:

- Cloud native security fundamentals (4 Cs)
- Kubernetes component security
- Security controls (RBAC, PSS, secrets, network policies)
- Threat modeling and attack surfaces
- Platform security and tooling
- Compliance frameworks and assessments

**Next Steps:**
1. Review areas where you feel less confident
2. Practice with hands-on exercises
3. Take practice exams
4. Schedule your KCSA exam

Good luck with your certification! 🎉

---

[← Back to KCSA Overview](../)
