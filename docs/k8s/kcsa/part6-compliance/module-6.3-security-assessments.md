# Module 6.3: Security Assessments

> **Complexity**: `[MEDIUM]` - Conceptual knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 6.2: CIS Benchmarks](module-6.2-cis-benchmarks.md)

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

1. **What does STRIDE stand for?**
   <details markdown="1">
   <summary>Answer</summary>
   Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege. It's a threat modeling framework that categorizes common security threats to help systematically identify potential attacks.
   </details>

2. **What's the difference between vulnerability assessment and penetration testing?**
   <details markdown="1">
   <summary>Answer</summary>
   Vulnerability assessment uses automated tools to identify known vulnerabilities without exploiting them. Penetration testing actively attempts to exploit vulnerabilities to demonstrate real-world impact. Vulnerability assessment is broader but shallower; penetration testing is deeper but more focused.
   </details>

3. **Why is threat modeling done at design time?**
   <details markdown="1">
   <summary>Answer</summary>
   It's cheaper and easier to address security issues during design than after deployment. Threat modeling identifies attack paths early when changes are less costly. It also ensures security is considered from the start rather than bolted on afterward.
   </details>

4. **What makes a finding "Critical" vs "High"?**
   <details markdown="1">
   <summary>Answer</summary>
   Risk = Likelihood × Impact. Critical findings have both high likelihood and high impact—they're easily exploitable and would cause significant damage. High findings may have slightly lower likelihood or impact but still require urgent attention.
   </details>

5. **What evidence do auditors typically need?**
   <details markdown="1">
   <summary>Answer</summary>
   Configuration exports (RBAC, policies), audit logs showing security controls working, scan reports (vulnerability, compliance), documentation (policies, procedures), and sometimes interviews with personnel. Evidence should demonstrate that controls exist and are effective over time.
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

[← Back to KCSA Overview](../README.md)
