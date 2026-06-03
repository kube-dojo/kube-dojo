Expand the module at: src/content/docs/cloud/azure-essentials/module-3.3-vms.md

Current body_words ≈ 1675 — needs to reach >= 5000. Follow ALL rules in
logs/remediation/briefs/session98/_shared-expand-rules.md (read it first).
NOTE: this module also fails `sentence_length_12_28` — keep mean sentence length
in the 12-28 word band; break long sentences.

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Azure VM depth, WHY before HOW):
1. **VM families & sizing** — the VM size series taxonomy (B-burstable, D-general
   purpose, E-memory-optimized, F-compute-optimized, L-storage-optimized, N-GPU),
   how to read a size name (e.g. Standard_D4s_v5: family/vCPU/features/version), and
   the right-sizing workflow. Cover the `s` (premium-storage-capable) suffix and
   generation differences.
2. **Availability & resiliency** — clearly separate Availability Sets (fault/update
   domains, single-DC), Availability Zones (zonal vs zone-redundant), and Virtual
   Machine Scale Sets (uniform vs flexible orchestration, autoscale). Give the SLA
   tiers (single VM with premium/ultra disk vs zones vs set) and when each applies.
3. **Managed disks & performance** — disk SKUs (Standard HDD, Standard SSD, Premium
   SSD, Premium SSD v2, Ultra Disk), the IOPS/throughput model (provisioned vs
   baseline+burst), how disk caching (None/ReadOnly/ReadWrite) interacts with the VM,
   and disk-vs-VM IOPS-cap interplay (a fast disk throttled by the VM's cap).

### COST LENS: pay-as-you-go vs Reserved Instances (1/3-yr) vs Savings Plans vs Spot
(eviction model, when safe); how disk tier + provisioned IOPS drive cost; the
"stopped (deallocated)" vs "stopped" billing distinction (deallocated = no compute
charge, still paying for disks).

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: when to use Availability Set vs Zones vs Scale Set; Spot vs
Reserved vs PAYG).

Web-verify every new fact against learn.microsoft.com. Report final body_words.
