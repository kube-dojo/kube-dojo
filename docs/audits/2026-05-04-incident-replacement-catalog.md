# Incident replacement catalog — 2026-05-04

> Read alongside `docs/audits/2026-05-04-incident-canonicals.md`. This catalog supplies replacement incidents for non-canonical modules. Hard rule per user 2026-05-04: each incident in this catalog may be used in at MOST one module (same hard rule as canonicals). Once a sweep PR claims an incident, mark it claimed here; the CI guardrail in `scripts/check_incident_reuse.py` also enforces this.

## How to use this catalog

Pick the bucket that matches your module's core lesson. Choose any unclaimed incident from that bucket. Adapt the suggested opener phrasing — it is a starting point, not a paste target. Verify the primary source URL still resolves before committing. Mark the incident as `[CLAIMED — module path]` in this file in the same PR that uses it.

---

## Bucket 1 — Fleet drift / partial deployment / config desync

*Alternatives to Knight Capital 2012. Use when the module teaches version consistency across nodes, partial rollout blast-radius, or "some servers got the change, others didn't."*

### Cloudflare BGP policy reorder — June 2022 [CLAIMED — `prerequisites/modern-devops/module-1.2-gitops.md`]

- **What happened (≤60 words):** Cloudflare deployed BGP community updates that reordered policy terms, placing a `REJECT-THE-REST` rule ahead of site-local advertisement terms. Nineteen data centers — handling ~50% of global traffic — withdrew their routes and became unreachable for ~75 minutes. The change was applied non-atomically; some PoPs received the correct order, others did not.
- **Lesson it teaches:** A partial, ordered deployment of network policy can leave different nodes in conflicting states, indistinguishable from a full rollout until traffic collapses.
- **Primary source:** https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In June 2022, Cloudflare engineers pushed what looked like a routine BGP community update. The deployment applied cleanly to most of the network. In nineteen data centers it did not — a single term reordering placed a blanket REJECT rule above every site-local advertisement. Those nineteen locations handled half of Cloudflare's global traffic. Within minutes they vanished from the internet entirely. The change had partially landed, and the partial landing was worse than no change at all.
- **Notes / caveats:** Cloudflare confirmed "not the result of an attack." Duration was ~75 minutes total.

---

### GitHub October 2018 database failover — split-brain [CLAIMED — `prerequisites/git-deep-dive/module-2-advanced-merging.md`]

- **What happened (≤60 words):** During routine optical hardware maintenance, GitHub lost connectivity between its US-East hub and primary database for 43 seconds. Automated failover triggered, but the two data centers had each accepted writes during the window. The reconciliation took 24 hours; ~200,000 webhook payloads were dropped permanently.
- **Lesson it teaches:** Automatic failover that fires mid-write creates two partially-advanced states neither of which is canonical — the synchronisation gap is the cost of a partial transition.
- **Primary source:** https://github.blog/2018-10-30-oct21-post-incident-analysis/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In October 2018, a GitHub engineer disconnected a failing optical cable — routine maintenance. The 43-second connectivity gap was enough for automatic failover to promote the US-West database. The problem: the US-East primary had also kept accepting writes. Both data centers held authoritative-looking records for the same rows. GitHub spent the next 24 hours reconciling two diverged timelines while degraded service continued and 200,000 webhook payloads timed out and were discarded.
- **Notes / caveats:** GitHub stated "no user data was lost" in final analysis, but 200k webhook events were permanently dropped.

---

### AWS ELB state deletion — December 2012

- **What happened (≤60 words):** An AWS engineer ran a maintenance process against the production ELB state store instead of a test environment. Configuration data for 6.8% of running load balancers was logically deleted. Affected load balancers could still forward traffic but could not be reconfigured. The outage lasted ~22 hours over Christmas Eve and Christmas Day 2012.
- **Lesson it teaches:** When a maintenance script targets the wrong environment, partial deletion leaves infrastructure in a zombie state — operational but unmanageable.
- **Primary source:** https://aws.amazon.com/message/680587/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On Christmas Eve 2012, an AWS engineer ran a routine maintenance process. The process targeted the wrong store: production Elastic Load Balancing state data, not the test copy. Configuration records for thousands of load balancers were logically deleted. The balancers kept forwarding traffic — they just could not be changed, drained, or destroyed. AWS engineers spent Christmas Eve and Christmas Day manually reconstructing state while customers' deployments were frozen in place.
- **Notes / caveats:** AWS described 6.8% of running ELBs impacted at peak. Full recovery 12:05 PM PST Dec 25.

---

### Cloudflare WAF regex CPU exhaustion — July 2019 [CLAIMED — `prerequisites/modern-devops/module-1.3-cicd-pipelines.md`]

- **What happened (≤60 words):** Cloudflare deployed a new WAF rule containing a backtracking regex that consumed 100% of CPU on every edge node worldwide. The rule was tested but the safeguard that would have caught catastrophic backtracking had been removed weeks earlier in a refactor. Traffic dropped 82% in 27 minutes before the WAF was disabled globally.
- **Lesson it teaches:** A single misconfigured component deployed uniformly to all nodes fails uniformly — there is no partial success to hide behind; the blast radius equals fleet size.
- **Primary source:** https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On July 2, 2019, Cloudflare pushed a WAF rule to every edge node on its network simultaneously. The rule contained a pathological regular expression — one whose backtracking behaviour was quadratic. Within seconds, CPU on every machine serving HTTP traffic saturated to 100%. Cloudflare traffic dropped 82%. The fix — removing the rule globally — took 27 minutes. A safety mechanism that would have caught the regex had been deleted in a refactor weeks before.
- **Notes / caveats:** Cloudflare called it their first global outage in six years.

---

## Bucket 2 — Exposed admin interface / weak authentication on management plane

*Alternatives to Tesla 2018 Kubernetes dashboard. Use when the module teaches UI authentication, unauthenticated endpoints, or management-plane exposure.*

### Cloudflare November 2023 Thanksgiving security incident

- **What happened (≤60 words):** Using an OAuth service token and three service accounts stolen from the October 2023 Okta breach, an attacker accessed Cloudflare's self-hosted Atlassian instance for four days before detection. Cloudflare had failed to rotate the credentials post-Okta. The attacker read 202 wiki pages, 36 bug tickets, and 76 source code repositories.
- **Lesson it teaches:** An unrotated credential after a known third-party breach is an open admin door — the authentication mechanism is intact but the keys are compromised.
- **Primary source:** https://blog.cloudflare.com/thanksgiving-2023-security-incident/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On November 14, 2023, a threat actor logged into Cloudflare's internal Atlassian instance using credentials stolen five weeks earlier in the Okta breach. Cloudflare had been notified about Okta. The credentials had not been rotated. For four days the attacker browsed internal wiki pages, bug reports, and source repositories before Cloudflare's detection systems flagged the access. The door had been locked; someone had quietly swapped the key.
- **Notes / caveats:** Cloudflare confirmed no customer data or production network was reached. Attacker used Sliver malware for persistence.

---

### Cloudflare July 2022 SMS phishing — FIDO2 containment

- **What happened (≤60 words):** Over 76 Cloudflare employees received convincing SMS phishing messages linking to `cloudflare-okta.com`. Three employees submitted credentials and TOTP codes to the attacker's relay in real time. Login attempts failed because Cloudflare requires FIDO2 hardware keys that bind to the origin domain, making the phished OTPs useless.
- **Lesson it teaches:** Weak authentication factors (password + TOTP) can be relayed in real time; FIDO2 hardware keys are the architectural boundary that stops this class of attack.
- **Primary source:** https://blog.cloudflare.com/2022-07-sms-phishing-attacks/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In July 2022, 76 Cloudflare employees received text messages directing them to a fake Okta login page. Three submitted their credentials and time-based one-time passwords. A real-time relay forwarded the codes to the attacker before they expired. Every login attempt failed. Cloudflare's requirement for FIDO2 hardware keys — which cryptographically bind to the real origin domain — made the stolen credentials worthless. The authentication layer had been designed to survive exactly this attack.
- **Notes / caveats:** Same attacker also hit Twilio successfully — that incident is a separate story.

---

### Okta support system breach — October 2023

- **What happened (≤60 words):** An attacker gained access to Okta's customer support case management system by stealing a session token from a support ticket containing an HTTP Archive file. The attacker used access to the support portal to browse customer-uploaded files and session cookies from hundreds of Okta customers.
- **Lesson it teaches:** A support portal is a management-plane interface; files uploaded to it (HAR files, screenshots) may contain live session tokens — scoping support tool permissions matters.
- **Primary source:** https://sec.okta.com/harfiles — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In October 2023, Okta's customer support portal became an attack vector. An engineer had uploaded a HAR file for troubleshooting — a browser network capture that still contained active session cookies. An attacker who had obtained access to the support system used those cookies to authenticate as the engineer's customer. Okta's support tool had access to all support ticket attachments. The management interface for resolving problems had become the problem.
- **Notes / caveats:** Okta initially reported limited scope; subsequent investigation found the breach affected all customer support users. Downstream victims included Cloudflare, 1Password, and BeyondTrust.

---

### AWS EBS / US-East re-mirroring storm — April 2011

- **What happened (≤60 words):** A network configuration change was applied to the wrong router path, simultaneously disconnecting both primary and redundant EBS networks in a single Availability Zone. Isolated nodes triggered a re-mirroring storm that exhausted cluster capacity. At peak, 13% of EBS volumes were stuck; 0.07% were permanently unrecoverable.
- **Lesson it teaches:** Management-plane network changes that bypass intended redundancy paths can take down storage control planes, not just connectivity.
- **Primary source:** https://aws.amazon.com/message/65648/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In April 2011, an AWS engineer applied a capacity upgrade that was supposed to route traffic through the redundant network. The change routed it the other way, disconnecting both the primary and fallback paths at the same moment. EBS nodes in US-East lost visibility to one another and began simultaneously re-mirroring their data. The re-mirroring traffic saturated the cluster. Volumes stopped accepting I/O. A few of them never recovered.
- **Notes / caveats:** Single AZ impact but caused widespread customer outages due to multi-AZ RDS failover failures (2.5% did not auto-failover).

---

## Bucket 3 — Cloud IAM / metadata-service / SSRF / credential extraction

*Alternatives to Capital One 2019. Use when the module teaches IMDSv1, SSRF, instance metadata abuse, or cloud credential hygiene.*

### MyEtherWallet BGP / DNS hijack — April 2018

- **What happened (≤60 words):** eNet Inc (AS10297) hijacked Amazon Route 53 DNS servers by advertising more-specific BGP routes. DNS resolvers in eleven cities, including Cloudflare's 1.1.1.1, returned a Russian IP for `myetherwallet.com`. Users logging into the fake site had session cookies and Ethereum credentials relayed to attackers. Estimated $160,000 in Ethereum was stolen.
- **Lesson it teaches:** Cloud DNS is a trust boundary; BGP prefix injection bypasses IAM and TLS certificate warnings to harvest credentials at the protocol layer.
- **Primary source:** https://blog.cloudflare.com/bgp-leaks-and-crypto-currencies/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** For roughly two hours on April 24, 2018, anyone using Cloudflare's 1.1.1.1 DNS resolver in Chicago, Sydney, or nine other cities who typed `myetherwallet.com` into their browser was sent to a server in Russia. The BGP routes for Amazon's Route 53 had been hijacked. The fake site had an invalid TLS certificate. Enough users clicked through the warning that the attackers collected an estimated $160,000 in Ethereum before the routes were withdrawn.
- **Notes / caveats:** Dollar figure from Forbes reporting cited in the Cloudflare post — mark as press estimate, not confirmed by Cloudflare or Amazon.

---

### AWS Kinesis cascade — November 2020

- **What happened (≤60 words):** A capacity addition to AWS Kinesis front-end servers exceeded the OS thread limit, preventing the fleet from constructing its internal membership cache. Because Kinesis underpins Cognito authentication, CloudWatch alarms, and Lambda metrics, the failure cascaded: Cognito auth failed, CloudWatch alarms entered INSUFFICIENT_DATA, and Lambda experienced memory contention. The outage ran ~17 hours.
- **Lesson it teaches:** A shared credential and authentication service (Cognito) is infrastructure, not an application; its failure propagates to every service that relies on it for IAM calls.
- **Primary source:** https://aws.amazon.com/message/11201/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In November 2020, AWS added capacity to its Kinesis data-streaming service. The new servers exceeded the maximum thread count allowed by the operating system. Without threads, the servers could not build their routing cache. Kinesis could not authenticate requests. Cognito — the IAM service for millions of applications — depended on Kinesis. CloudWatch alarms could not fire. Lambda functions began failing. A thread limit on one service had quietly become a credentials outage for the entire region.
- **Notes / caveats:** AWS US-EAST-1. Duration approximately 5:15 AM – 10:23 PM PST November 25, 2020.

---

### AWS US-East-1 network surge — December 2021

- **What happened (≤60 words):** An automated internal network scaling event triggered unexpected behaviour in AWS's internal network client, generating a surge of connection attempts that overwhelmed networking devices between the internal and main AWS networks. EKS, ECS, Fargate, STS, and the AWS Console all lost connectivity. The outage lasted approximately 7 hours.
- **Lesson it teaches:** When the cloud control plane's authentication layer (STS) is unreachable, no service can validate IAM credentials — cluster orchestration, scaling, and console access all fail simultaneously.
- **Primary source:** https://aws.amazon.com/message/12721/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On December 7, 2021, an internal scaling routine at AWS triggered a connection storm that overwhelmed the network boundary between AWS's internal services and its customer-facing infrastructure. STS — the token service that backs every IAM call — became unreachable. Engineers could not log into the AWS console. EKS and ECS clusters could not validate service account tokens. For seven hours, the credential layer of an entire AWS region was effectively offline.
- **Notes / caveats:** EKS/ECS specifically called out. US-EAST-1. Full recovery 4:37 PM PST.

---

### CircleCI January 2023 — session token exfiltration from CI secrets store

- **What happened (≤60 words):** A threat actor deployed malware on a CircleCI engineer's laptop on December 16, 2022, stealing session cookies and escalating to production access. The attacker exfiltrated customer environment variables, tokens, and SSH keys from production databases. Encryption keys were extracted from running processes, potentially enabling decryption of stored secrets. CircleCI advised all customers to rotate every secret immediately.
- **Lesson it teaches:** A CI platform stores live secrets for thousands of customers; compromising one employee with production access is equivalent to a credential breach across every connected customer environment.
- **Primary source:** https://circleci.com/blog/jan-4-2023-incident-report/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In early January 2023, CircleCI told every customer to rotate every secret they had ever stored on the platform. The reason: an attacker had stolen session cookies from an engineer's laptop two weeks earlier, used them to reach CircleCI's production databases, and extracted environment variables, API tokens, and SSH keys. The data was encrypted at rest. The attacker had also extracted the encryption keys from memory. CircleCI's CI environment — trusted by thousands of engineering teams to hold their secrets — had been the point of failure.
- **Notes / caveats:** Breach window December 16, 2022 – January 4, 2023. No specific customer count given.

---

## Bucket 4 — Unpatched component / dependency vulnerability

*Alternatives to Equifax 2017 Apache Struts. Use when the module teaches patch management, vulnerability windows, or unpatched transitive dependencies.*

### Cloudbleed memory leak — February 2017

- **What happened (≤60 words):** A Cloudflare HTML parser written in Ragel had an off-by-one buffer overread triggered by three rarely-used features landing simultaneously. Edge nodes were returning fragments of other customers' HTTP responses — including session tokens, passwords, and private messages — in random responses. The bug had been active for ~5 months before a Google Project Zero researcher found it.
- **Lesson it teaches:** Parsing code with unsafe pointer arithmetic creates data exfiltration at scale; a component that was correct in isolation became exploitable when combined with other features.
- **Primary source:** https://blog.cloudflare.com/incident-report-on-memory-leak-caused-by-cloudflare-parser-bug/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** For five months in late 2016 and early 2017, Cloudflare's edge servers were leaking fragments of other customers' HTTP traffic into random responses. A Google Project Zero researcher spotted a private Slack message appearing in a public API response. The root cause: an HTML parser with an off-by-one pointer error, triggered when three rarely-used features landed on the same page. Somewhere in those five months, session tokens and plaintext passwords had been served to strangers.
- **Notes / caveats:** Cloudflare confirmed the bug originated in a Ragel-generated HTML parser. The bug had been active in production for approximately 5 months before disclosure.

---

### Kubernetes CVE-2018-1002105 — privilege escalation via API proxy

- **What happened (≤60 words):** A flaw in kube-apiserver's error handling for proxied upgrade requests allowed unauthenticated users to establish backend connections and send arbitrary requests using the API server's TLS credentials. CVSS 9.8 critical. All Kubernetes versions prior to 1.10.11 / 1.11.5 / 1.12.3 were affected. Disclosed and patched December 2018.
- **Lesson it teaches:** Running an unpatched API server exposes every cluster resource regardless of RBAC configuration — the vulnerability bypasses the authorization layer entirely.
- **Primary source:** https://nvd.nist.gov/vuln/detail/CVE-2018-1002105 — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In December 2018, Kubernetes disclosed CVE-2018-1002105: a critical flaw in the API server's proxy request handling. An unauthenticated user who could reach the API server could open a backend connection and issue requests that carried the API server's own TLS credentials. RBAC rules were irrelevant — the authorization layer was never reached. Every cluster running Kubernetes before 1.10.11 was exposed. The patch was already available; clusters that had not updated were a single unauthenticated request away from full compromise.
- **Notes / caveats:** CVSS 9.8. Fix: upgrade to 1.10.11+, 1.11.5+, or 1.12.3+. Widely reported as the worst Kubernetes CVE to that date.

---

### Travis CI secret exposure — September 2021

- **What happened (≤60 words):** A bug in Travis CI allowed forked public repositories to read secret environment variables (API keys, tokens, passwords) from upstream repositories via pull requests. The vulnerability was active September 3–10, 2021. Travis CI patched it silently and issued no postmortem. CVE-2021-41077. Ethereum developers discovered it independently and disclosed publicly.
- **Lesson it teaches:** CI secrets exposed to fork builds are exposed to any public contributor — environment variable scoping is a security boundary, not a convenience setting.
- **Primary source:** https://nvd.nist.gov/vuln/detail/CVE-2021-41077 — verified YES 2026-05-04 via WebFetch (NVD description: "The activation process in Travis CI, for certain 2021-09-03 through 2021-09-10 builds, causes secret data to have unexpected sharing that is not specified by the customer-controlled .travis.yml file.")
- **Suggested opener phrasing (≤80 words):** For seven days in September 2021, any developer who submitted a pull request to a public GitHub repository using Travis CI could read that repository's secret environment variables. API keys. Deploy tokens. Database passwords. Travis CI patched the issue on September 10 without notifying affected projects and published no postmortem. The Ethereum team, who discovered the bug independently, eventually forced a public disclosure. Ethereum's team lead noted: "No analysis, no security report, no postmortem."
- **Notes / caveats:** Travis CI stated no evidence of exploitation but issued no forensics confirmation.

---

## Bucket 5 — DNS / global routing / configuration blast-radius

*Alternatives to Facebook 2021 BGP outage. Use when the module teaches DNS, global routing, configuration propagation scope, or "one change takes out everything."*

### Verizon BGP optimizer leak — June 2019

- **What happened (≤60 words):** A Pennsylvania ISP used a BGP optimizer to fragment IP prefixes into smaller, more-specific routes. The routes leaked through Allegheny Technologies to Verizon, which re-advertised them globally without prefix filtering or RPKI validation. Amazon, Cloudflare, and Linode traffic was misrouted through an under-capacity link. Cloudflare lost ~15% of global traffic for several hours.
- **Lesson it teaches:** A BGP routing leak amplified by a major transit provider without RPKI validation can redirect significant global traffic through an unprepared bottleneck.
- **Primary source:** https://blog.cloudflare.com/how-verizon-and-a-bgp-optimizer-knocked-large-parts-of-the-internet-offline-today/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On June 24, 2019, a small ISP in Pennsylvania ran a BGP optimizer to improve its own routing. The optimizer generated thousands of more-specific route advertisements. Those routes leaked through two intermediate networks and landed on Verizon — one of the internet's largest transit providers — which dutifully re-announced them to the entire internet without validation. Amazon, Cloudflare, and Linode traffic was sucked into a link that could not handle it. Fifteen percent of Cloudflare's global traffic vanished.
- **Notes / caveats:** Verizon did not apply IRR-based filtering or RPKI. Incident lasted several hours; Verizon provided no public comment.

---

### Cloudflare November 2020 Byzantine switch failure

- **What happened (≤60 words):** A network switch at a Cloudflare data center entered a partially-operating state: control-plane protocols worked but data-plane packet processing failed intermittently. The inconsistency caused Cloudflare's etcd cluster members to have conflicting views of network state. Repeated leadership elections blocked database writes, triggering a replica rebuild that overwhelmed the authentication database. API success rates dropped to 75% for 6.5 hours.
- **Lesson it teaches:** Partial hardware failure is harder to diagnose than total failure; a component that reports healthy to monitoring can still corrupt distributed consensus.
- **Primary source:** https://blog.cloudflare.com/a-byzantine-failure-in-the-real-world/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In November 2020, a Cloudflare network switch degraded without fully failing. Control-plane protocols said it was up; the data plane was silently dropping packets. Cloudflare's etcd cluster — relying on that switch — received contradictory heartbeat signals. Nodes began electing new leaders. Repeated elections blocked writes. The database promoted a replica. Rebuilding the replica saturated the authentication service. For six and a half hours, Cloudflare's API ran at 75% success rate while engineers tried to identify a switch that all monitoring said was fine.
- **Notes / caveats:** A textbook Byzantine fault in production infrastructure. Duration 6 hours 33 minutes, November 2, 2020.

---

### GitHub March 2023 CDN SSL certificate binding failure

- **What happened (≤60 words):** GitHub Actions workflows failed for 2 hours 18 minutes after unexpected SSL certificate binding issues on their CDN infrastructure. A configuration change caused certificate-to-endpoint bindings to break, making workflow job dispatch fail across regions.
- **Lesson it teaches:** TLS certificate management in CDN configuration is load-bearing infrastructure; a binding mismatch silently breaks encrypted endpoints without triggering obvious connectivity alarms.
- **Primary source:** https://github.blog/engineering/infrastructure/github-availability-report-march-2023/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On March 2, 2023, GitHub Actions workflows began failing across regions. The cause was not a code change or a capacity problem: SSL certificate bindings on GitHub's CDN infrastructure had been invalidated by a configuration update. The encrypted connection between GitHub's dispatch layer and its CDN endpoints broke silently. For over two hours, CI pipelines across thousands of repositories returned errors. The certificates were valid; the binding configuration that pointed to them was not.
- **Notes / caveats:** Duration 2 hours 18 minutes. Listed in the March 2023 availability report with investigation noted as complete.

---

## Bucket 6 — Build-environment compromise / supply-chain attack

*Alternatives to SolarWinds 2020 and Codecov 2021. Use when the module teaches CI/CD artifact provenance, build-environment trust, or inserting malicious code upstream.*

### XZ Utils backdoor (CVE-2024-3094) — March 2024

- **What happened (≤60 words):** A threat actor using the identity "Jia Tan" spent ~2 years becoming a trusted maintainer of the XZ Utils compression library. They inserted obfuscated code into release tarballs — not the git source — that modified liblzma's dynamic linking to intercept and backdoor SSH authentication. CVE-2024-3094 CVSS 10.0 critical. A Microsoft engineer discovered it by accident via SSH latency anomalies.
- **Lesson it teaches:** Long-term social engineering of open-source maintainer access is a viable build-environment compromise; tarballs and git sources can diverge without obvious detection.
- **Primary source:** https://openwall.com/lists/oss-security/2024/03/29/4 — verified YES 2026-05-04 via WebFetch (Andres Freund's original disclosure)
- **Secondary source:** https://nvd.nist.gov/vuln/detail/CVE-2024-3094 — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In March 2024, Andres Freund noticed that SSH logins on his Debian system were 500ms slower than usual. He traced the latency to liblzma, a compression library. Looking more carefully, he found obfuscated machine code embedded in the XZ Utils release tarball — code not present in the git repository. The maintainer who had landed the change had spent two years earning commit access. The backdoor was designed to intercept SSH authentication at the dynamic linker level before any application code ran.
- **Notes / caveats:** Caught before wide distribution adoption. CVSS 10.0. Red Hat immediately issued CVE-2024-3094. Andres Freund is credited with the discovery.

---

### npm event-stream / flatmap-stream attack — November 2018

- **What happened (≤60 words):** An attacker using the handle "right9ctrl" gained maintainer access to the unmaintained `event-stream` npm package (downloaded ~8 million times in the incident window). They added `flatmap-stream` as a dependency, which contained obfuscated code that stole bitcoin wallets from applications using the Copay wallet app. Active September–November 2018, discovered by a community member.
- **Lesson it teaches:** Abandoned open-source packages with high download counts are acquisition targets; new "maintainers" can inject malicious transitive dependencies that ship to millions of downstream consumers.
- **Primary source:** https://snyk.io/blog/malicious-code-found-in-npm-package-event-stream/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In September 2018, a new contributor appeared on GitHub, offered to take over maintenance of `event-stream` — an npm package downloaded millions of times weekly — and the original author accepted. The new maintainer's first change was to add a new dependency. The dependency contained obfuscated bitcoin-stealing code, targeting the Copay cryptocurrency wallet. The malicious package shipped to production for two months before a curious developer reading a deobfuscated source file raised an alarm.
- **Notes / caveats:** ~8 million downloads occurred during the active window. Target was specifically Copay wallet, not general key theft.

---

### Heroku / Travis CI OAuth token theft — April 2022

- **What happened (≤60 words):** An attacker stole OAuth tokens that Heroku and Travis CI used to integrate with GitHub. The tokens gave read access to private repositories. The attacker used them to exfiltrate private source code from GitHub, including Heroku's own repositories. GitHub revoked all affected tokens; Heroku took its GitHub integration offline for weeks.
- **Lesson it teaches:** OAuth tokens stored by a CI/CD platform are as sensitive as deploy credentials; a compromised CI intermediary exposes all connected private repositories.
- **Primary source:** https://www.heroku.com/blog/april-2022-incident-review — verified YES 2026-05-04 via WebFetch (Heroku quote: "On April 7, 2022, a threat actor obtained access to a Heroku database and downloaded stored customer GitHub integration OAuth tokens.")
- **Suggested opener phrasing (≤80 words):** In April 2022, GitHub notified Heroku and Travis CI that OAuth tokens belonging to their GitHub integration apps had been stolen and used to download private repository data. The tokens had been stored in a Heroku database. An attacker who accessed that database could authenticate to GitHub as the integration app, with read access to every private repository that had authorized the app. Heroku's own source code was among the repositories exfiltrated.
- **Notes / caveats:** GitHub disclosed April 15, 2022. Heroku disabled GitHub integration for ~30 days. Root cause: stolen OAuth tokens from Heroku's internal systems.

---

## Bucket 7 — Transitive-dependency CVE / library-vuln cascade

*Alternatives to Log4Shell. Use when the module teaches dependency graphs, CVE triage in transitive dependencies, or the propagation of a library vulnerability.*

### colors.js / faker.js intentional sabotage — January 2022

- **What happened (≤60 words):** The maintainer of `colors` (20M weekly downloads, 19,000 dependents) and `faker` (2M weekly downloads) intentionally published sabotaged versions. `colors` 1.4.44 contained an infinite loop that crashed any Node.js server on startup. `faker` 6.6.6 was published empty. Both were triggered by the maintainer's frustration over unpaid open-source work.
- **Lesson it teaches:** Any dependency update, including a minor bump from a trusted maintainer, can be deliberately destructive; version pinning and lock files are not just reproducibility tools — they are a security boundary.
- **Primary source:** https://snyk.io/blog/open-source-npm-packages-colors-faker/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On January 8, 2022, `colors` — an npm package used in over four million JavaScript projects — published version 1.4.44. The new version started an infinite loop on initialization. Every Node.js application that installed it that morning crashed on boot. The maintainer had published it intentionally, alongside an empty `faker` package he also maintained. Millions of CI pipelines and production servers were broken by a single npm install. The maintainer had not been compromised. He had made a choice.
- **Notes / caveats:** No legal action was taken. The incident is widely cited in open-source sustainability debates. Both packages were subsequently forked by the community.

---

### Kubernetes CVE-2022-3294 — node proxy validation bypass

- **What happened (≤60 words):** A validation bypass in kube-apiserver allowed authenticated users to circumvent restrictions on proxy requests, potentially reaching API server private network endpoints not intended for direct access. CVSS 8.8 (NIST) / 6.6 (Kubernetes CNA). Affected all Kubernetes versions through 1.22.15, 1.23.x through 1.23.13, 1.24.x through 1.24.7, and 1.25.x through 1.25.3. Patched March 2023.
- **Lesson it teaches:** A transitive security assumption — "only the API server can reach internal endpoints" — can be violated by a validation gap that ships unnoticed across many minor releases.
- **Primary source:** https://nvd.nist.gov/vuln/detail/CVE-2022-3294 — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** Kubernetes 1.25.3 shipped in late 2022 with a bug. Any authenticated user who knew about CVE-2022-3294 could bypass the validation that restricts which endpoints a proxy request may target, potentially reaching internal API server network addresses. The flaw had been present in the codebase across four minor release series. Organizations running Kubernetes in this range had an authenticated network path to resources the API server was supposed to protect on their behalf.
- **Notes / caveats:** CVSS 8.8 NIST / 6.6 Kubernetes CNA (disagreement on severity). Published March 1, 2023.

---

### ua-parser-js npm hijack — October 2021

- **What happened (≤60 words):** The npm account for `ua-parser-js` (a widely-used browser detection library) was compromised. Attackers published versions 0.7.29, 0.8.0, and 1.0.0 containing a cryptocurrency miner and a password-stealing trojan. The package had millions of weekly downloads and appeared as a transitive dependency in many major projects, including Facebook's tools.
- **Lesson it teaches:** Compromised maintainer credentials, not code bugs, can inject malware into a trusted package overnight — account security for maintainers is supply-chain security.
- **Primary source:** https://github.com/faisalman/ua-parser-js/issues/536 — verified YES 2026-05-04 via WebFetch (GitHub issue from October 22, 2021 — original maintainer disclosure)
- **Suggested opener phrasing (≤80 words):** On October 22, 2021, the maintainer of `ua-parser-js` woke up to find that his npm account had published three new versions he had not written. The versions contained a cryptocurrency miner and a credential-harvesting trojan. The package appeared as a dependency in millions of Node.js projects. npm's advisory instructed all users to "assume all secrets and keys stored on that computer were compromised." The package's code had not changed in git. Only the published artifact had.
- **Notes / caveats:** npm issued advisory immediately. CISA issued alert AA21-296A. CVE-2021-41627 assigned.

---

## Bucket 8 — Third-party trust boundary / lateral movement

*Alternatives to Target 2013. Use when the module teaches vendor trust chains, network segmentation, or lateral movement via a trusted third party.*

### Cloudflare October 2023 — Okta breach lateral movement

- **What happened (≤60 words):** After the October 2023 Okta customer support breach, an attacker used a session token stolen from a Cloudflare support ticket to compromise two Cloudflare employee Okta accounts. Cloudflare detected the intrusion more than 24 hours before Okta notified them. Zero Trust architecture and rapid incident response contained the breach with no customer data exposure.
- **Lesson it teaches:** A third-party support portal is a trust boundary; tokens uploaded for debugging can be reused by an attacker who has compromised that portal.
- **Primary source:** https://blog.cloudflare.com/how-cloudflare-mitigated-yet-another-okta-compromise/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** When Okta's customer support system was breached in October 2023, the attacker's first move was to find session tokens uploaded by Okta customers to support tickets. Cloudflare had uploaded one. The attacker used it to log into Cloudflare's Okta instance and access two employee accounts. Cloudflare's security team detected the intrusion through anomaly detection — 24 hours before Okta sent a notification. The Okta integration was a trust boundary; a stolen debugging file had opened it.
- **Notes / caveats:** Downstream victims also included 1Password and BeyondTrust. This incident (Oct 2023 lateral movement) is distinct from the Thanksgiving 2023 source-code intrusion.

---

### Twilio August 2022 — smishing attack, lateral movement to 209 customers

- **What happened (≤60 words):** Threat actors sent SMS phishing messages to Twilio employees impersonating IT staff, harvesting credentials to Twilio's internal admin tools. Using those tools, attackers accessed data for 209 Twilio customers and registered unauthorized devices on 93 Authy accounts. The attacker group (0ktapus) ran simultaneous campaigns against Okta, Cloudflare, and other SaaS providers using the same technique.
- **Lesson it teaches:** A vendor's internal admin portal is a trust boundary for every customer using that vendor; employee credential compromise at a SaaS provider is customer data exposure at scale.
- **Primary source:** https://www.twilio.com/blog/august-2022-social-engineering-attack — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In August 2022, Twilio employees began receiving text messages from what appeared to be the company's IT department. Several clicked the link and submitted credentials to a fake Okta portal. The attackers used those credentials to access Twilio's internal customer management tools. Two hundred and nine customers found that an attacker with access to a Twilio employee's session had browsed their account data. The customers had not been phished. Their vendor had.
- **Notes / caveats:** Twilio confirmed 209 customers affected out of 270,000+. Attacker group identified as 0ktapus / Scatter Swine. No API keys or auth tokens were exposed.

---

## Bucket 9 — Hardcoded credentials / secrets in code or registry

*Alternatives to Uber 2022. Use when the module teaches secrets scanning, credential rotation, or the danger of committing secrets.*

### Microsoft CVE-2023-23397 — Outlook NTLM credential theft

- **What happened (≤60 words):** A critical vulnerability in Microsoft Outlook (CVSS 9.8) allowed an attacker to send a calendar invite with a UNC path to an attacker-controlled server. When Outlook processed the invite, it automatically connected to the UNC path and leaked the user's NTLM hash — no user interaction required. Russian state actor APT28 exploited it before the patch was released in March 2023.
- **Lesson it teaches:** NTLM hashes are credentials — any code path that auto-initiates outbound authenticated connections (email clients, file shares) can exfiltrate credentials without the user clicking anything.
- **Primary source:** https://nvd.nist.gov/vuln/detail/CVE-2023-23397 — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In early 2023, Microsoft patched CVE-2023-23397 — an Outlook vulnerability that allowed an attacker to steal Windows NTLM hashes by sending a calendar invitation. No user action was required. When Outlook pre-fetched the reminder's UNC path to an attacker-controlled server, Windows automatically sent the user's credential hash. Microsoft attributed active exploitation to APT28 before the patch was available. The credential had not been hardcoded; it had been automatically transmitted by a trusted email client to an untrusted host.
- **Notes / caveats:** CVSS 9.8. CISA added to Known Exploited Vulnerabilities catalog. Affects Outlook 2013 through Microsoft 365.

---

## Bucket 10 — Production typo / single-keystroke blast radius

*Alternatives to AWS S3 us-east-1 2017. Use when the module teaches blast-radius reduction, dry-run enforcement, or the cost of irreversible commands without safeguards.*

### Cloudflare dashboard fiber disconnection — April 2020

- **What happened (≤60 words):** During decommissioning of unused hardware, a Cloudflare technician disconnected patch-panel cables that were also carrying live redundant fiber. All redundant connections from a production data center cabinet were severed in three minutes. The Cloudflare dashboard and API became unavailable for 4 hours 21 minutes; customer traffic continued normally.
- **Lesson it teaches:** Physical infrastructure changes in production without a lockout/tagout procedure carry the same blast radius as a software misconfiguration — one wrong cable disconnection can take down a management plane.
- **Primary source:** https://blog.cloudflare.com/cloudflare-dashboard-and-api-outage-on-april-15-2020/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On April 15, 2020, a Cloudflare technician decommissioning unused hardware in a data center cabinet disconnected a patch panel. The patch panel also carried the redundant fiber connections for production systems in the same cabinet. All redundant paths were severed in three minutes. Cloudflare's dashboard and API went dark for over four hours. The core network kept running; the management plane did not. The change had no ticket, no second pair of eyes, and no reversibility.
- **Notes / caveats:** No attack, no software bug. Physical change without change-management controls. Duration 4h 21m.

---

### GitHub January 2023 git binary upgrade — archive checksum break

- **What happened (≤60 words):** GitHub upgraded a production git binary that changed the internal gzip implementation. Source archives downloaded from GitHub began producing checksum mismatches, causing build systems worldwide to fail validation. No content was actually altered; only the compression algorithm changed. The fix was a rollback. The incident lasted 7 hours.
- **Lesson it teaches:** A "trivial" binary upgrade in production infrastructure that changes deterministic outputs (checksums, hashes) is a breaking change that requires explicit rollout gates.
- **Primary source:** https://github.blog/engineering/infrastructure/github-availability-report-january-2023/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On January 30, 2023, GitHub upgraded its production git binary. The new version used a different internal gzip implementation. Every source archive downloaded from GitHub that day produced a different checksum than the same archive had produced yesterday. Build pipelines around the world began failing SHA verification. The content was identical. The compression was not. GitHub rolled back the binary after seven hours. An unannounced change to a checksum function is a breaking API change, regardless of how internal it seems.
- **Notes / caveats:** No data loss. Duration 7 hours. GitHub stated "no content was changed."

---

## Bucket 11 — BGP misconfiguration

*Alternatives to Cloudflare 2020 BGP (the canonical at `platform/foundations/advanced-networking/module-1.4-bgp-routing.md`). Use when the module needs a different BGP story.*

### Pakistan Telecom / YouTube BGP hijack — February 2008

- **What happened (≤60 words):** Pakistan Telecom (AS17557) announced an unauthorized more-specific prefix for YouTube's IP space to block YouTube access domestically. Its upstream provider PCCW Global propagated the announcement globally without filtering. YouTube traffic worldwide was redirected to Pakistani servers for approximately 2 hours until PCCW withdrew the routes.
- **Lesson it teaches:** A single AS announcing a more-specific prefix propagates globally if upstream providers lack prefix filtering; BGP has no built-in origin authentication.
- **Primary source:** https://www.ripe.net/publications/news/industry-developments/youtube-hijacking-a-ripe-ncc-ris-case-study/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On February 24, 2008, Pakistan Telecom announced a BGP route for a YouTube IP prefix to block YouTube access within Pakistan. Its upstream provider, PCCW Global, forwarded the route to the global internet without filtering it. YouTube traffic from around the world began arriving at Pakistani servers. YouTube engineers noticed the hijack within minutes and counter-announced the prefix. The entire episode lasted about two hours. Pakistan Telecom had not attacked the internet; it had simply made a routing announcement nobody checked.
- **Notes / caveats:** RIPE NCC documented the incident using Routing Information Service data. Duration approximately 2 hours 14 minutes (18:47–21:01 UTC). Frequently cited in BGP security literature.

---

## Bucket 12 — Certificate / cryptographic expiration

*No current canonical. Cross-references to other certificate / TLS incidents in Buckets 5 and 7 (see below). The Ericsson December 2018 incident was investigated for this bucket but Ericsson's press release URL and major secondary sources (Reuters, theregister, BBC) were not reachable from this session — per the project's `feedback_citation_verify_or_remove.md` honesty rule, an unverified citation cannot ship. If a sweep agent finds a working primary source for that incident, append it here.*

### GitHub March 2023 CDN SSL binding failure

*(Listed also in Bucket 5 — choose ONE bucket per module; do not use this incident twice.)*

---

### Cloudflare Byzantine failure — etcd cert / TLS cascade

*(Listed also in Bucket 5 — choose ONE bucket per module; do not use this incident twice.)*

---

### HTTP/2 Rapid Reset zero-day — October 2023

- **What happened (≤60 words):** A zero-day in the HTTP/2 protocol's stream cancellation mechanism allowed a botnet of ~20,000 machines to generate 201 million requests per second — three times any previously recorded DDoS peak. Cloudflare, Google, and AWS jointly disclosed the vulnerability and coordinated patches on October 10, 2023. CVE-2023-44487.
- **Lesson it teaches:** Protocol-level assumptions about stream lifecycle become cryptographic attack surfaces; TLS and HTTP/2 are not independent — a flaw in the application-layer protocol bypasses transport-layer rate limits.
- **Primary source:** https://blog.cloudflare.com/zero-day-rapid-reset-http2-record-breaking-ddos-attack/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On October 10, 2023, Cloudflare, Google, and Amazon jointly disclosed a zero-day in the HTTP/2 protocol. An attacker could open a stream, immediately cancel it, and repeat thousands of times per second per connection — exploiting the protocol's own cancellation mechanism to generate server-side work without receiving responses. A botnet of 20,000 machines used this technique to generate 201 million requests per second, three times any previous record. The vulnerability was in the protocol specification itself.
- **Notes / caveats:** CVE-2023-44487. CVSS 7.5. Coordinated multi-vendor disclosure.

---

## Bucket 13 — Database / data-loss recovery gap

*Alternatives to GitLab 2017 db1 (canonical #4). Use when the module teaches backup verification, RTO/RPO, or the failure of recovery assumptions.*

### Atlassian April 2022 cloud data deletion [CLAIMED — `prerequisites/git-deep-dive/module-4-undo-recovery.md`]

- **What happened (≤60 words):** Atlassian permanently deleted the cloud sites of approximately 400 enterprise customers during a maintenance operation that ran a "delete script" against the wrong environment. The deletion affected Jira, Confluence, and other products. Full data restoration took up to two weeks for some customers. Atlassian's backup and restore procedures had not been tested at this scale.
- **Lesson it teaches:** A bulk deletion without environment confirmation and without a tested restore procedure converts a routine maintenance script into a two-week customer emergency.
- **Primary source:** https://www.atlassian.com/engineering/post-incident-review-april-2022-outage — verified YES 2026-05-04 via WebFetch (Atlassian quote: "On Tuesday, April 5th, 2022, starting at 7:38 UTC, 775 Atlassian customers lost access to their Atlassian products.")
- **Secondary source:** https://www.atlassian.com/blog/statement/april-2022-outage-update — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In April 2022, Atlassian ran a maintenance script that deleted the Jira and Confluence environments of approximately 400 enterprise customers. The script targeted the wrong set of sites. Atlassian's backups existed; restoring them at scale took up to two weeks. For those two weeks, affected customers had no access to their project tracking, documentation, and service management systems. The data was recoverable. The gap between "recoverable" and "recovered" cost customers hundreds of work-hours of lost productivity.
- **Notes / caveats:** Atlassian's PIR refers to 775 customers as the impact; press coverage initially reported ~400. Restoration took up to 14 days for the longest-affected sites.

---

### GitHub October 2018 database split-brain — webhook data loss

*(Listed also in Bucket 1 — choose ONE bucket per module; do not use this incident twice.)*

---

### AWS EBS re-mirroring storm — April 2011 (permanent volume loss)

*(Listed also in Bucket 2 — choose ONE bucket per module; do not use this incident twice.)*

---

### Google Cloud europe-west2 cooling failure — July 2022

- **What happened (≤60 words):** A cooling failure in one building of Google Cloud's europe-west2-a zone caused Google to power down capacity to prevent equipment damage. Persistent Disk volumes that were replicated ran in single-redundant mode; a minority of HDD-backed volumes experienced I/O errors. The incident lasted ~39 hours; some data was unrecoverable.
- **Lesson it teaches:** Zone-level failure can degrade persistence guarantees even for replicated storage; multi-zone replication is the only reliable guard against physical infrastructure failure in a single zone.
- **Primary source:** https://status.cloud.google.com/incidents/XVq5om2XEDSqLtJZUvcH — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In July 2022, the cooling system for one building in Google Cloud's europe-west2-a zone failed. Google powered down the affected capacity rather than risk hardware damage from overheating. Persistent Disks that replicated across the zone suddenly had only one replica. Some HDD-backed volumes began returning I/O errors even after the initial mitigation. The incident lasted 39 hours. For workloads deployed in a single zone, the cooling failure in one building became a data-durability event.
- **Notes / caveats:** Google Cloud status page incident ID XVq5om2XEDSqLtJZUvcH. July 19–20, 2022. Small customer subset affected.

---

## Bucket 14 — Outage observability / mean-time-to-diagnose

*Use when the module teaches alerting, distributed tracing, on-call runbooks, or the cost of poor observability. Also usable: the Cloudflare Byzantine failure (Bucket 5) — its core lesson is that monitoring can lie; the AWS Kinesis cascade (Bucket 3) where CloudWatch alarms entered INSUFFICIENT_DATA during the outage.*

### GitHub August 2021 — MySQL degraded state from bad query [CLAIMED — `prerequisites/modern-devops/module-1.4-observability.md`]

- **What happened (≤60 words):** An edge case in a high-traffic application generated a poorly-performing query that degraded a MySQL primary. Retry and queuing logic prevented automatic recovery. GitHub's internal tooling, which depended on the same database, also failed — engineers lost the observability instruments they needed to diagnose the problem. Total impact: 1 hour 17 minutes for the first wave, with a second incident 4 hours later.
- **Lesson it teaches:** When a database failure takes down the monitoring infrastructure that runs on that same database, mean-time-to-diagnose increases non-linearly — observability tooling must be isolated from the systems it observes.
- **Primary source:** https://github.blog/engineering/infrastructure/github-availability-report-august-2021/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** In August 2021, a single slow database query at GitHub triggered a cascade. The query came from one of GitHub's most active internal applications. The MySQL primary entered a degraded state. The queuing and retry logic meant the cluster could not self-recover. When engineers opened their dashboards to diagnose the problem, the dashboards were also down — they ran on the same cluster. GitHub spent part of its incident response time diagnosing why it couldn't see what was broken.
- **Notes / caveats:** Two separate incidents in one day (August 10, 2021): 1h 17m and 3h 6m. The second incident was a service discovery misconfiguration during GitHub Actions setup.

---

### GitHub April 2023 — infrastructure change deletes live database nodes

- **What happened (≤60 words):** During a planned database infrastructure change, GitHub deleted nodes that were still handling live traffic, creating a brief window where requests failed before traffic rerouted. Issues and pull requests were unavailable for 11 minutes. The root cause: the change procedure did not include traffic verification before node removal.
- **Lesson it teaches:** Infrastructure changes in production require a "verify traffic is drained" gate before destruction — delete operations that assume prior steps completed are latent outages.
- **Primary source:** https://github.blog/engineering/infrastructure/github-availability-report-april-2023/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** On April 18, 2023, GitHub deleted database nodes as part of a planned infrastructure change. The change worked as written. It had not been written to verify that traffic had stopped flowing to those nodes before deleting them. For eleven minutes, requests for GitHub Issues and Pull Requests hit nodes that no longer existed. The change procedure completed successfully. The success criteria had been missing a step.
- **Notes / caveats:** Duration 11 minutes. GitHub improved change management review process in response.

---

## Bucket 15 — Cluster / orchestration-specific failures

*Real Kubernetes-specific incidents — useful for K8s module openers across CKA, CKAD, and CKS tracks. Also usable from other buckets: CVE-2018-1002105 (Bucket 4) and CVE-2022-3294 (Bucket 7).*

### Siloscape — Windows container escape targeting Kubernetes clusters

- **What happened (≤60 words):** Malware named Siloscape was discovered in March 2021 (active since January 2020) that exploited vulnerabilities in Windows containers to escape to the underlying host and move laterally through Kubernetes clusters. It specifically targeted poorly-configured clusters, opening a backdoor to an IRC-based C2 server. 23 active victims were identified at discovery.
- **Lesson it teaches:** Container escape vulnerabilities are cluster-level threats; a single compromised pod on a poorly-configured cluster becomes a persistent foothold on every node.
- **Primary source:** https://unit42.paloaltonetworks.com/siloscape/ — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** For over a year before its discovery, Siloscape malware had been running inside Kubernetes clusters. It arrived as a web application compromise, then used a Windows container escape technique to reach the underlying host. From the host, it navigated the cluster, opened a backdoor to an IRC command-and-control server, and waited. Researchers found 23 active victims when they cracked the C2 server in March 2021. The clusters had all been running. Nothing obvious had been wrong.
- **Notes / caveats:** Unit 42 / Palo Alto Networks research. Windows containers only. C2 server had 23 victims at time of research.

---

### Kubernetes CVE-2021-25735 — admission webhook bypass

- **What happened (≤60 words):** A validation bypass in kube-apiserver allowed authenticated users to update Node objects in ways that should have been rejected by Validating Admission Webhooks. The webhook was not called for certain earlier field updates, allowing policy enforcement to be bypassed. CVSS 6.5 medium. Affected Kubernetes prior to 1.18.18, 1.19.0–1.19.9, and 1.20.0–1.20.5.
- **Lesson it teaches:** Admission webhooks are not the last line of defense — if the API server can bypass them for specific field paths, policy-as-code tooling (OPA, Kyverno) may have silent gaps.
- **Primary source:** https://nvd.nist.gov/vuln/detail/CVE-2021-25735 — verified YES 2026-05-04 via WebFetch
- **Suggested opener phrasing (≤80 words):** A common assumption in Kubernetes security hardening is that Validating Admission Webhooks see every write to the API server. CVE-2021-25735 broke that assumption for Node object updates: certain field paths bypassed the webhook call entirely. An operator who had written a webhook policy to enforce Node constraints would see the policy pass silently on writes that the API server never submitted for validation. The clusters appeared protected. The protection had a gap the size of a specific API path.
- **Notes / caveats:** CVSS 6.5. Published September 6, 2021. Fix: upgrade past 1.18.18 / 1.19.10 / 1.20.6.

---

*End of catalog — 2026-05-04. After cleanup: ~35 incidents across 15 buckets. Every remaining primary-source URL was reached via WebFetch on 2026-05-04 — entries that could not be verified (Ericsson 2018, Samsung 2022 source-code leak, Meta October 2021 BGP — the last because it conflicted with the Facebook 2021 canonical) were removed per `feedback_citation_verify_or_remove.md`. Bucket 12 (Certificate / cryptographic expiration) is intentionally thin until a verifiable source is found. If a sweep agent locates a working source, append it here.*
