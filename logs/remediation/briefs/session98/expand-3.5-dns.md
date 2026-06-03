Expand the module at: src/content/docs/cloud/azure-essentials/module-3.5-dns.md

Current body_words ≈ 936 — needs to reach >= 5000. Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Azure DNS depth, WHY before HOW):
1. **Public DNS zones & records** — Azure DNS public zones, the record types
   (A, AAAA, CNAME, MX, TXT, SRV, CAA, NS, SOA), TTL tradeoffs, and **alias records**
   (alias to a Public IP / Traffic Manager / CDN / Front Door — what they solve over
   CNAME, apex-domain support, lifecycle tracking). Delegation: NS records and how to
   delegate a domain to Azure DNS name servers.
2. **Private DNS zones & resolution** — private zones, virtual-network links
   (registration vs resolution links), autoregistration, split-horizon DNS, and the
   **Azure DNS Private Resolver** (inbound/outbound endpoints, forwarding rulesets)
   for hybrid on-prem ↔ Azure name resolution. Contrast with the legacy
   default-provided Azure DNS (168.63.129.16).
3. **Traffic routing & integration** — how DNS ties into Traffic Manager
   (DNS-level global routing: priority/weighted/performance/geographic) vs Azure
   Front Door / Application Gateway (L7). Make the boundary explicit: when DNS-based
   routing is the right tool vs an L7 load balancer.

### COST LENS: hosted-zone monthly cost + per-million-query pricing for public and
private zones; Private Resolver endpoint hourly cost; Traffic Manager per-million-query
+ health-probe cost; how over-low TTLs raise query volume and cost.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: public vs private zone; alias record vs CNAME; Traffic Manager vs
Front Door for routing).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
