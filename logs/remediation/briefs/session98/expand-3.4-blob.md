Expand the module at: src/content/docs/cloud/azure-essentials/module-3.4-blob.md

Current body_words ≈ 1785 — needs to reach >= 5000. Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).
NOTE: this module also fails `sentence_length_12_28` — keep mean sentence length
in the 12-28 word band; break long sentences.

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Blob Storage depth, WHY before HOW):
1. **Access tiers & lifecycle** — Hot, Cool, Cold, and Archive tiers (online vs
   offline, rehydration latency and priority for Archive, minimum-retention/early-
   deletion fees per tier), and lifecycle management policies (rule-based tier-down
   and delete by last-modified/last-accessed). Explain blob-level vs account-level
   default tiering.
2. **Redundancy & durability** — LRS, ZRS, GRS, RA-GRS, GZRS, RA-GZRS: what each
   protects against (disk → datacenter → region), the read-access (RA) distinction,
   the eleven-nines durability framing, and failover (customer-managed vs
   Microsoft-managed) with its RPO implications.
3. **Security & access control** — the auth options ladder: account keys (avoid),
   SAS tokens (account/service/user-delegation SAS, the user-delegation SAS being
   Entra-backed and preferred), and Entra ID RBAC data-plane roles (Storage Blob
   Data Reader/Contributor). Plus private endpoints vs service endpoints vs firewall
   rules, blob versioning, soft delete, and immutability (time-based / legal hold /
   WORM) for ransomware/compliance.

### COST LENS: storage capacity by tier + transaction (operation) costs + data
egress + early-deletion penalties + the often-surprising cost of frequent reads on
Cool/Cold/Archive (per-GB retrieval charge); how lifecycle policies cut spend.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: pick the access tier by access frequency + retention; pick the
redundancy SKU by blast-radius requirement + budget).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
