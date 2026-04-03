---
title: "Module 4.1: The Security Mindset"
slug: platform/foundations/security-principles/module-4.1-security-mindset
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Systems Thinking Track](../systems-thinking/) (recommended)
>
> **Track**: Foundations

### What You'll Be Able to Do

After completing this module, you will be able to:

1. **Apply** attacker-mindset thinking to evaluate infrastructure designs and identify the paths of least resistance an adversary would exploit
2. **Analyze** real-world breaches (supply chain, lateral movement, credential theft) to extract defensive lessons for your own systems
3. **Design** threat models that enumerate attack surfaces, trust boundaries, and high-value targets for a given architecture
4. **Evaluate** security tradeoffs between usability, cost, and protection level when proposing defensive controls

---

**December 2020. A software company's network monitoring tool sits quietly on 18,000 customer networks worldwide.**

A routine software update pushes to customers—government agencies, Fortune 500 companies, critical infrastructure operators. The update contains perfectly valid code, digitally signed by the vendor. It also contains a backdoor, inserted during the build process by nation-state attackers who had been inside the vendor's network for over a year.

The attackers didn't break encryption. They didn't exploit a zero-day. They compromised the software supply chain itself, turning the vendor's own update mechanism into a delivery system for malware. By the time anyone noticed, attackers had access to the networks of the Treasury Department, the Department of Homeland Security, and dozens of other organizations.

**The SolarWinds breach cost over $100 million in direct incident response.** The reputational damage was immeasurable. And it demonstrated a fundamental truth about security: attackers don't have to be smarter than defenders—they just have to find one way in while defenders protect everything.

This module teaches the security mindset—thinking like an attacker to build like a defender.

---

## Why This Module Matters

Every system you build will be attacked. Not might be—will be. The question isn't "if" but "when" and "how prepared are you?"

Security isn't a feature you add at the end. It's a way of thinking—a mindset that influences every design decision, every line of code, every operational process. Developers who understand security build better systems, even when they're not explicitly "doing security work."

This module introduces the security mindset: how attackers think, how defenders must think, and why security is everyone's responsibility.

> **The Castle Analogy**
>
> Medieval castles weren't just walls. They had moats, drawbridges, murder holes, multiple walls, keeps, and escape routes. Each layer assumed the previous one might fail. The architects thought like attackers: "If I breach the outer wall, what stops me next?" Security engineering is the same: assume breach, plan for failure, layer defenses.

---

## What You'll Learn

- How attackers think (and why you need to think like them)
- The difference between security theater and real security
- Core security principles that never change
- Why "trust" is the most dangerous word in security
- How to evaluate security trade-offs

---

## Part 1: Thinking Like an Attacker

### 1.1 The Attacker's Advantage

```
THE ASYMMETRY OF SECURITY
═══════════════════════════════════════════════════════════════

DEFENDER                           ATTACKER
─────────────────────────────────────────────────────────────
Must protect everything    vs.     Only needs one way in
Must be right every time   vs.     Only needs to be right once
Works within constraints   vs.     No rules, no ethics
Limited budget            vs.      Can be well-funded (or automated)
Must balance usability    vs.      Doesn't care about UX

The attacker chooses:
- WHEN to attack (wait for weekends, holidays)
- WHERE to attack (weakest point)
- HOW to attack (known or novel technique)

The defender must be ready always, everywhere, for everything.
```

### 1.2 The Attack Surface

Your **attack surface** is everything an attacker could potentially target:

```
ATTACK SURFACE
═══════════════════════════════════════════════════════════════

EXTERNAL SURFACE (Internet-facing)
├── Web applications
├── APIs
├── DNS
├── Email servers
├── VPN endpoints
└── Any public IP

INTERNAL SURFACE (assumes breach)
├── Internal services
├── Databases
├── Message queues
├── Admin interfaces
└── Developer machines

HUMAN SURFACE
├── Employees (phishing)
├── Contractors
├── Support staff (social engineering)
└── Executives (whale phishing)

SUPPLY CHAIN SURFACE
├── Third-party libraries
├── CI/CD pipeline
├── Build systems
└── Dependencies' dependencies
```

> **Try This (2 minutes)**
>
> List 5 things in your system that could be attacked:
> 1. ____________________
> 2. ____________________
> 3. ____________________
> 4. ____________________
> 5. ____________________
>
> Now think: which one would YOU attack if you were malicious?

### 1.3 Attacker Motivation

Not all attackers want the same thing:

| Attacker Type | Motivation | Targets | Sophistication |
|---------------|------------|---------|----------------|
| **Script Kiddies** | Fun, bragging rights | Easy targets | Low |
| **Hacktivists** | Political/social cause | Symbolic targets | Low-Medium |
| **Criminals** | Money | Valuable data, ransomware | Medium-High |
| **Competitors** | Business advantage | Trade secrets | Medium |
| **Nation-states** | Intelligence, disruption | Critical infrastructure | Very High |
| **Insiders** | Revenge, money | Whatever they can access | Varies |

```
THREAT MODELING QUESTION
═══════════════════════════════════════════════════════════════

"Who would want to attack us, and why?"

Small e-commerce site:
    - Criminals (credit card data)
    - Script kiddies (defacement)

Healthcare company:
    - Criminals (medical records worth more than credit cards)
    - Nation-states (intelligence)

Defense contractor:
    - Nation-states (classified information)
    - Competitors (bid information)

Your threat model determines your security investment.
```

---

## Part 2: Security Principles

### 2.1 Principle of Least Privilege

Grant only the minimum permissions necessary to perform a function.

```
LEAST PRIVILEGE
═══════════════════════════════════════════════════════════════

BAD: Application runs as root, has admin database access
┌─────────────────────────────────────────────────────────────┐
│  Web App (root)                                             │
│      │                                                      │
│      └──▶ Database (admin user)                            │
│           - Can read all tables                             │
│           - Can write all tables                            │
│           - Can drop tables                                 │
│           - Can create users                                │
│                                                             │
│  If compromised: attacker owns everything                   │
└─────────────────────────────────────────────────────────────┘

GOOD: Application runs as limited user, minimal DB access
┌─────────────────────────────────────────────────────────────┐
│  Web App (app-user)                                         │
│      │                                                      │
│      └──▶ Database (api-readonly on most, write on some)   │
│           - Can read: products, categories                  │
│           - Can write: orders, cart                         │
│           - Cannot: drop, create users, access admin tables │
│                                                             │
│  If compromised: attacker has limited access                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Defense in Depth

Never rely on a single security control. Layer defenses.

```
DEFENSE IN DEPTH
═══════════════════════════════════════════════════════════════

SINGLE LAYER (fragile)
                ┌─────────────┐
Internet ───▶   │  Firewall   │  ───▶  Everything else
                └─────────────┘
                      │
               If firewall fails,
               everything is exposed

MULTIPLE LAYERS (robust)
    ┌─────────────┐
    │  Firewall   │    ← Network layer
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │     WAF     │    ← Application layer
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Auth/AuthZ  │    ← Identity layer
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │Input Valid. │    ← Data layer
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Encryption │    ← Storage layer
    └─────────────┘

Each layer assumes the previous one might fail.
```

### 2.3 Zero Trust

Never trust, always verify. Assume the network is compromised.

```
TRADITIONAL (PERIMETER) MODEL
═══════════════════════════════════════════════════════════════

    Outside         │         Inside (trusted)
    (untrusted)     │
                    │
    ┌─────┐         │    ┌─────┐    ┌─────┐    ┌─────┐
    │Attacker│──X───│    │App A│◀──▶│App B│◀──▶│ DB  │
    └─────┘    │    │    └─────┘    └─────┘    └─────┘
               ▼    │
          [Firewall]│    "If you're inside, you're trusted"
                    │
                    │    Problem: Once inside, attacker moves freely

ZERO TRUST MODEL
═══════════════════════════════════════════════════════════════

Every request is verified, regardless of source:

    ┌─────┐         ┌─────┐         ┌─────┐
    │App A│──auth──▶│App B│──auth──▶│ DB  │
    └─────┘         └─────┘         └─────┘
       │               │               │
       └───────────────┴───────────────┘
                       │
              Every call authenticated
              Every action authorized
              Every connection encrypted

    "Never trust, always verify"
```

### 2.4 Fail Secure

When something fails, fail to a secure state, not an open one.

```
FAIL SECURE vs FAIL OPEN
═══════════════════════════════════════════════════════════════

FAIL OPEN (dangerous)
─────────────────────────────────────────────────────────────
Auth service down → Allow all requests (so users aren't blocked)
    Result: Attacker can bypass authentication

Validation error → Skip validation (so it doesn't crash)
    Result: Malicious input gets through

FAIL SECURE (correct)
─────────────────────────────────────────────────────────────
Auth service down → Deny all requests
    Result: Users inconvenienced, but system secure

Validation error → Reject the request
    Result: Legitimate requests might fail, but attacks blocked

The secure default is always to deny.
```

> **Try This (2 minutes)**
>
> For each scenario, which is the secure default?
>
> | Scenario | Fail Open | Fail Secure |
> |----------|-----------|-------------|
> | Firewall crashes | Allow traffic | Block traffic |
> | Permission check fails | Grant access | Deny access |
> | Rate limiter errors | Allow requests | Block requests |
> | Certificate validation fails | Allow connection | Reject connection |
>
> (All should be "Fail Secure")

---

## Part 3: Security vs. Security Theater

### 3.1 What is Security Theater?

**Security theater** is measures that provide the feeling of security without actually improving it.

```
SECURITY THEATER EXAMPLES
═══════════════════════════════════════════════════════════════

PASSWORDS
─────────────────────────────────────────────────────────────
Theater: Requiring password changes every 30 days
    Result: Users pick weak passwords with incrementing numbers
    Real security: Long passphrases + MFA

COMPLIANCE CHECKBOXES
─────────────────────────────────────────────────────────────
Theater: "We passed the audit"
    Result: Checked boxes, but real vulnerabilities remain
    Real security: Continuous security testing

NETWORK SECURITY
─────────────────────────────────────────────────────────────
Theater: "We have a firewall"
    Result: Firewall exists but rules are too permissive
    Real security: Properly configured, monitored firewall

ENCRYPTION
─────────────────────────────────────────────────────────────
Theater: "We encrypt everything"
    Result: Encryption at rest, but keys stored next to data
    Real security: Proper key management, encryption in transit too
```

### 3.2 How to Spot Security Theater

| Real Security | Security Theater |
|---------------|------------------|
| Reduces actual risk | Reduces perceived risk |
| Based on threat modeling | Based on compliance checkboxes |
| Measured by outcomes | Measured by presence |
| Evolves with threats | Static, set-and-forget |
| Tested regularly | Assumed to work |

### 3.3 The Security vs. Usability Trade-off

```
THE SECURITY-USABILITY SPECTRUM
═══════════════════════════════════════════════════════════════

HIGH SECURITY, LOW USABILITY
┌─────────────────────────────────────────────────────────────┐
│  - Air-gapped systems                                       │
│  - Multi-person authorization for everything                │
│  - Physical presence required                               │
│  - No remote access                                         │
│                                                             │
│  Result: Very secure, but hard to use                      │
│  Risk: Users find workarounds (sticky note passwords)      │
└─────────────────────────────────────────────────────────────┘

LOW SECURITY, HIGH USABILITY
┌─────────────────────────────────────────────────────────────┐
│  - No passwords                                             │
│  - Everyone is admin                                        │
│  - No audit logs                                            │
│                                                             │
│  Result: Easy to use, but trivially compromised            │
└─────────────────────────────────────────────────────────────┘

THE GOAL: Maximum security at acceptable usability
┌─────────────────────────────────────────────────────────────┐
│  - SSO (one login for everything)                          │
│  - MFA that's not annoying (push notifications)            │
│  - Role-based access (right permissions automatically)     │
│  - Security that's invisible when not needed               │
└─────────────────────────────────────────────────────────────┘
```

> **War Story: The $300 Million Firewall Failure**
>
> **March 2017.** A large financial services company proudly demonstrated their security posture to auditors. The dashboard showed a gleaming enterprise firewall—$2 million in hardware, 24/7 monitoring, intrusion detection enabled.
>
> Six months later, attackers exfiltrated 140 million customer records over a 76-day period.
>
> **How did they get past the firewall?** They didn't have to. Post-breach analysis revealed the firewall had 847 "temporary" exception rules accumulated over 8 years. One of those exceptions—added in 2012 for a contractor who left in 2013—created a path from a web server to the customer database.
>
> The attackers exploited a known vulnerability in a web application. The patch had been available for 2 months. The firewall rules that should have contained the breach were swiss cheese.
>
> **The Equifax breach cost over $1.4 billion** in settlements, remediation, and lost business. The firewall dashboard showed green the entire time.
>
> Real security isn't about having tools. It's about using them correctly.

---

## Part 4: Trust and Verification

### 4.1 The Problem with Trust

```
TRUST IS A VULNERABILITY
═══════════════════════════════════════════════════════════════

Every time you trust something, you create a potential attack vector:

"We trust our employees"
    → Insider threat, compromised credentials

"We trust our vendors"
    → Supply chain attacks (SolarWinds)

"We trust our internal network"
    → Lateral movement after initial breach

"We trust this library"
    → Malicious package, dependency confusion

"We trust input from our mobile app"
    → App can be reverse-engineered, requests forged

Trust should be:
- Explicit (documented what you trust and why)
- Minimal (trust as little as possible)
- Verified (check that trust is warranted)
- Revocable (can remove trust quickly)
```

### 4.2 Trust Boundaries

A **trust boundary** is where data or execution crosses between different trust levels.

```
TRUST BOUNDARIES
═══════════════════════════════════════════════════════════════

         UNTRUSTED           │         TRUSTED
                             │
    ┌──────────────┐         │
    │   Internet   │         │
    │              │─────────┼───▶ VALIDATE HERE
    │  User input  │         │
    │  API calls   │    Trust boundary
    │  Webhooks    │         │
    └──────────────┘         │

                             │
    ┌──────────────┐         │
    │  Third-party │         │
    │   services   │─────────┼───▶ VALIDATE HERE
    │              │         │
    └──────────────┘    Trust boundary
                             │

Every trust boundary needs:
- Input validation
- Authentication
- Authorization
- Rate limiting
- Logging
```

### 4.3 Verification Techniques

| What to Verify | Technique |
|----------------|-----------|
| User identity | Authentication (passwords, MFA, certificates) |
| User permissions | Authorization (RBAC, ABAC, policies) |
| Data integrity | Checksums, signatures, MACs |
| Data source | Digital signatures, certificate pinning |
| Code integrity | Code signing, reproducible builds |
| Request legitimacy | CSRF tokens, nonces, timestamps |

> **Try This (3 minutes)**
>
> Draw the trust boundaries in your system:
>
> 1. Where does untrusted data enter?
> 2. What do you implicitly trust that you shouldn't?
> 3. Where are you NOT validating input?

---

## Part 5: Building Security In

### 5.1 Shift Left

```
SECURITY IN THE DEVELOPMENT LIFECYCLE
═══════════════════════════════════════════════════════════════

TRADITIONAL (security at the end)
─────────────────────────────────────────────────────────────

Design → Develop → Test → Deploy → [Security Review] → Prod
                                          │
                                    "Fix it now or
                                     delay launch"
                                          │
                                    Expensive, rushed,
                                    often skipped

SHIFT LEFT (security throughout)
─────────────────────────────────────────────────────────────

[Threat Model] → [Secure Design] → [Code Review] → [SAST] → [DAST] → Prod
      │                │                │            │         │
  "What could      "How do we     "Any security   Automated  Automated
   go wrong?"       prevent it?"   issues?"       scanning   testing

Security is cheaper to fix early:

    Cost to fix
    ▲
    │                                              ████ Production
    │                                        ████
    │                                  ████
    │                           ████
    │                    ████
    │            ████
    │     ████
    └────────────────────────────────────────────────▶ Time
         Design   Code    Test    Deploy    Prod
```

### 5.2 Secure Development Practices

| Practice | What It Does | When |
|----------|--------------|------|
| **Threat modeling** | Identify what could go wrong | Design phase |
| **Secure coding standards** | Prevent common vulnerabilities | Coding |
| **Code review** | Human review for security issues | Before merge |
| **SAST** | Static analysis for vulnerabilities | CI pipeline |
| **DAST** | Dynamic testing of running app | Staging/Prod |
| **Dependency scanning** | Check for vulnerable libraries | CI pipeline |
| **Secret scanning** | Prevent credential leaks | Pre-commit, CI |
| **Penetration testing** | Find what automation misses | Periodically |

### 5.3 Security as Culture

```
SECURITY CULTURE
═══════════════════════════════════════════════════════════════

BAD CULTURE                          GOOD CULTURE
─────────────────────────────────────────────────────────────
"Security is the security team's    "Security is everyone's job"
 problem"

"We'll add security later"           "We design for security"

"That's too paranoid"                "What's the threat model?"

"It's just internal, doesn't        "All data deserves protection"
 matter"

"Nobody would do that"               "Assume attackers are smart
                                      and motivated"

"We've never been hacked"            "We haven't detected a hack"
```

---

## Did You Know?

- **The term "hacker"** originally meant someone who explored systems creatively. The malicious meaning came later. "Cracker" was the original term for malicious hackers, but media conflation made "hacker" the common term.

- **The first computer virus** (Creeper, 1971) wasn't malicious—it just displayed "I'm the creeper, catch me if you can." The first antivirus (Reaper) was written to delete it.

- **Social engineering** accounts for over 90% of successful attacks. Technical defenses matter less than training humans to recognize manipulation.

- **The "Morris Worm" of 1988** was the first major internet worm and was written by a Cornell graduate student. It accidentally replicated far more aggressively than intended, crashing about 10% of the internet (roughly 6,000 machines). Robert Morris became the first person convicted under the Computer Fraud and Abuse Act—and later became a tenured MIT professor.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Security as afterthought | Expensive to retrofit | Shift left, threat model early |
| Trusting the network | Lateral movement after breach | Zero trust architecture |
| Assuming perimeter is enough | Insiders, supply chain | Defense in depth |
| Security through obscurity | Attackers will figure it out | Assume your code is public |
| Ignoring usability | Users bypass security | Make security easy |
| One-time security review | Security degrades over time | Continuous security |

---

## Quiz

1. **Why do attackers have an inherent advantage over defenders?**
   <details>
   <summary>Answer</summary>

   Attackers have structural advantages:

   1. **Asymmetry of focus**: Defenders must protect everything; attackers only need one vulnerability
   2. **Asymmetry of success**: Defenders must be right every time; attackers only need to succeed once
   3. **No constraints**: Attackers don't have budgets, ethics, or usability requirements
   4. **Initiative**: Attackers choose when, where, and how to attack
   5. **Patience**: Attackers can wait for the right moment (holidays, key personnel away)

   This asymmetry is why defense in depth is essential—no single control will always work.
   </details>

2. **What is the principle of least privilege and why does it matter?**
   <details>
   <summary>Answer</summary>

   **Least privilege**: Grant only the minimum permissions necessary to perform a function.

   Why it matters:
   1. **Limits blast radius**: Compromised component can only do what it's authorized to do
   2. **Reduces accident damage**: Mistakes can't affect systems the user doesn't have access to
   3. **Simplifies auditing**: Fewer permissions to review and track
   4. **Contains insider threats**: Malicious employees have limited reach

   Example: A web application that only reads products should have read-only database access. If compromised, the attacker can't modify or delete data.
   </details>

3. **What's the difference between security and security theater?**
   <details>
   <summary>Answer</summary>

   **Security** actually reduces risk through effective controls.

   **Security theater** creates the appearance of security without substantive risk reduction.

   How to distinguish:
   - Security is based on threat modeling; theater is based on compliance checkboxes
   - Security is measured by outcomes; theater is measured by presence of controls
   - Security evolves with threats; theater is static
   - Security is tested; theater is assumed to work

   Example: A firewall is security. An improperly configured firewall with "allow all" rules is security theater—it exists but provides no protection.
   </details>

4. **Why is "shift left" important for security?**
   <details>
   <summary>Answer</summary>

   "Shift left" means integrating security earlier in the development lifecycle.

   Why it matters:
   1. **Cost**: Security issues found in production cost 100x more to fix than in design
   2. **Time**: Fixing security late delays releases
   3. **Quality**: Security-conscious design is fundamentally better design
   4. **Coverage**: Automated security checks in CI catch issues before humans would

   Traditional: Security review happens at the end (if at all)
   Shift left: Threat modeling in design, secure coding practices, automated scanning in CI, regular penetration testing

   Finding a SQL injection in code review costs minutes. Finding it in production costs days plus breach response.
   </details>

5. **A company has 500 external-facing endpoints and each has a 99.5% chance of not being vulnerable. What's the probability that at least one is vulnerable?**
   <details>
   <summary>Answer</summary>

   Probability of no vulnerabilities = 0.995^500 = 0.082 (8.2%)

   **Probability of at least one vulnerability = 1 - 0.082 = 91.8%**

   This illustrates the attacker's advantage mathematically. Even with "mostly secure" systems:
   - 100 endpoints × 99% secure = 63% chance of at least one vulnerability
   - 500 endpoints × 99.5% secure = 92% chance of at least one vulnerability
   - 1000 endpoints × 99.9% secure = 63% chance of at least one vulnerability

   The defender must secure every endpoint. The attacker only needs one to fail.
   </details>

6. **What are the four components of a trust boundary, and why does each matter?**
   <details>
   <summary>Answer</summary>

   A trust boundary is where data crosses between different trust levels. Each boundary needs:

   1. **Input validation**: Ensure data is well-formed and within expected ranges. Prevents injection attacks, buffer overflows, and logic errors.

   2. **Authentication**: Verify the identity of the sender. Prevents impersonation and ensures accountability.

   3. **Authorization**: Confirm the sender is allowed to perform the requested action. Prevents privilege escalation.

   4. **Rate limiting**: Restrict request frequency. Prevents DoS attacks and brute force attempts.

   5. **Logging**: Record what crossed the boundary. Enables detection and forensics.

   Missing any component creates an attack vector. For example, authenticating but not authorizing allows any authenticated user to access any resource.
   </details>

7. **An organization requires 90-day password rotations and 12-character passwords with uppercase, lowercase, numbers, and symbols. Why might this reduce security rather than improve it?**
   <details>
   <summary>Answer</summary>

   This policy often backfires because:

   1. **Predictable patterns**: Users pick base passwords and increment numbers: "Summer2024!" becomes "Fall2024!" becomes "Winter2024!"

   2. **Written passwords**: Complex requirements + frequent changes = passwords written on sticky notes

   3. **Password reuse**: Exhausted users reuse the same password across systems

   4. **Weaker base passwords**: To meet complexity rules, users choose simpler bases they can modify

   **NIST 2017 guidelines** recommend:
   - Long passphrases over complex passwords ("correct horse battery staple" vs "Tr0ub4dor&3")
   - Change passwords only when compromised, not on schedule
   - Check passwords against breach databases instead of complexity rules

   Security theater: Complex rotation rules
   Real security: Long unique passwords + MFA + breach detection
   </details>

8. **The SolarWinds attack compromised 18,000 organizations but attackers actively targeted only about 100. What security principle does this reveal, and why?**
   <details>
   <summary>Answer</summary>

   This reveals the principle of **supply chain as attack surface**.

   Key insights:

   1. **Trust amplification**: One vendor compromise = 18,000 potential victims. Attackers invested heavily in one target to gain access to thousands.

   2. **Implicit trust is dangerous**: Organizations trusted vendor updates without verification. The digitally signed malware passed security controls because the signature was valid.

   3. **Attack surface extends beyond your code**: Your security posture includes every dependency, vendor, and tool in your pipeline.

   4. **Targeted exploitation**: Attackers used broad access strategically—casting a wide net but carefully selecting high-value targets to avoid detection.

   Defensive lessons:
   - Verify software integrity beyond just signatures
   - Monitor for anomalous behavior even from "trusted" software
   - Assume third-party code might be compromised
   - Implement zero trust for all code, not just external users
   </details>

---

## Hands-On Exercise

**Task**: Perform a mini threat model for a web application.

**Scenario**: You're building a simple e-commerce site with:
- User registration and login
- Product catalog
- Shopping cart
- Checkout with credit card processing

**Part 1: Identify Assets (5 minutes)**

What data/capabilities does an attacker want?

| Asset | Value to Attacker |
|-------|-------------------|
| User credentials | |
| Credit card numbers | |
| Customer PII | |
| | |
| | |

**Part 2: Identify Threat Actors (5 minutes)**

Who might attack this system?

| Threat Actor | Motivation | Capability |
|--------------|------------|------------|
| | | |
| | | |
| | | |

**Part 3: Identify Attack Vectors (10 minutes)**

How could each asset be compromised?

| Asset | Attack Vector | Likelihood | Impact |
|-------|---------------|------------|--------|
| User credentials | Phishing | High | Medium |
| User credentials | SQL injection | Medium | High |
| Credit cards | | | |
| | | | |
| | | | |

**Part 4: Identify Controls (10 minutes)**

What controls would mitigate each attack?

| Attack Vector | Control | Type |
|---------------|---------|------|
| Phishing | MFA | Preventive |
| SQL injection | Parameterized queries | Preventive |
| | | |
| | | |

**Success Criteria**:
- [ ] At least 4 assets identified
- [ ] At least 3 threat actors with motivations
- [ ] At least 5 attack vectors with likelihood/impact
- [ ] At least 5 controls mapped to attacks

---

## Further Reading

- **"The Web Application Hacker's Handbook"** - Dafydd Stuttard. Comprehensive guide to web security from an attacker's perspective.

- **"Threat Modeling: Designing for Security"** - Adam Shostack. The definitive guide to threat modeling.

- **OWASP Top 10** - owasp.org/Top10. The most critical web application security risks, updated regularly.

---

## Key Takeaways Checklist

Before moving on, verify you can answer these:

- [ ] Can you explain why attackers have a structural advantage over defenders?
- [ ] Can you define and identify your system's attack surface (external, internal, human, supply chain)?
- [ ] Do you understand the principle of least privilege and why it limits blast radius?
- [ ] Can you distinguish security theater from real security?
- [ ] Do you understand trust boundaries and what controls each boundary needs?
- [ ] Can you explain "shift left" and why early security is cheaper than late security?
- [ ] Do you understand why complex password policies often backfire?
- [ ] Can you explain why supply chain attacks (like SolarWinds) are so dangerous?

---

## Next Module

[Module 4.2: Defense in Depth](../module-4.2-defense-in-depth/) - Layered security controls and how to implement them effectively.
