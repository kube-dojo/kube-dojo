---
title: "Module 2.1: Datacenter Fundamentals"
slug: on-premises/provisioning/module-2.1-datacenter-fundamentals
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` | Time: 60 minutes
>
> **Prerequisites**: [Module 1.2: Server Sizing](/on-premises/planning/module-1.2-server-sizing/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** datacenter facility requirements including power redundancy, cooling capacity, and physical security against the availability target your platform actually needs to meet.
2. **Design** a rack layout with correct PDU sizing, cable management, hot/cold-aisle orientation, and out-of-band networking for a bare-metal Kubernetes cluster.
3. **Diagnose** physical infrastructure failures (PDU trips, cooling regression, BMC misconfiguration, cabling errors) when they manifest as Kubernetes-level outages, and decide what to fix in the OS versus what to escalate to facilities.
4. **Plan** colocation facility selection by scoring power, cooling, network, operations, security, and contract terms, and then negotiate SLA clauses that mathematically support a 99.9% / 99.95% / 99.99% target.
5. **Justify** the redundancy choices in a deployment to non-engineering stakeholders (procurement, finance, leadership) using the operational and incident data you would collect in production.

---

## Why This Module Matters

At 2:43 AM on a Tuesday in 2019, an SRE at a fintech company received an alert that read simply "API server unreachable." She SSH'd into the jump box and got connection refused, tried the VPN and watched it time out, then phoned the colocation facility. The night operator answered after four rings and confirmed the bad news without much ceremony: "Your rack is dark. Both PDU feeds tripped." A firmware bug in the rack PDU had caused a cascading overcurrent shutdown when a scheduled firmware update ran on the UPS during a routine power test. The UPS entered bypass mode, the PDU detected an overvoltage condition that did not actually exist, and both A and B feeds tripped within milliseconds of each other. Every layer of redundancy the team had paid for collapsed at once because the redundancy lived inside one shared firmware code path.

The SRE drove forty-five minutes to the datacenter, badged through the mantrap, walked to row 7, rack 14, and manually reset both PDUs by hand. The cluster came back online in eight minutes once power returned. Total wall-clock outage was one hour and twenty-three minutes. Total revenue impact, measured later by the finance team from settlement logs, was eighty-four thousand dollars in failed transactions plus an unknown amount of customer trust that does not show up on a spreadsheet.

She told her team the next morning, in a sentence that has been quoted by several engineers since: "I have a PhD in distributed systems, but the thing that brought us down was a 20-amp circuit breaker and a firmware bug in a power strip. Every layer of abstraction sits on top of physical infrastructure, and if you don't understand that physical layer, you can't debug the failures that come from it." That is the entire thesis of this module. If you operate on-premises Kubernetes, you do not need an electrician's depth of knowledge, but you do need enough literacy to size a rack, talk to a facilities engineer without translation, read a colocation SLA critically, and recognize the failure modes that begin somewhere below the OS.

> **The Building Foundation Analogy**
>
> The datacenter is the foundation of your house. Nobody talks about the foundation at dinner parties, you never interact with it directly, and most of the time it is invisible. But if it cracks, everything above it shifts, breaks, and becomes uninhabitable, and no amount of clever interior design fixes the problem. Understanding racks, power, cooling, cabling, and out-of-band management is understanding the foundation that your Kubernetes clusters stand on. Every Pod you schedule eventually resolves to a transistor on a die in a server in a rack on a floor in a building, and the building has weather.

---

## What You'll Learn

- Rack standards, server form factors, and how physical layout shapes capacity planning
- Power distribution end to end: utility feeds, UPS, PDUs, A+B redundancy, and how to budget kW correctly
- Cooling principles: hot aisle / cold aisle, kW-per-rack capacity, containment, and the limits of air cooling
- Out-of-band management: BMC architecture, IPMI vs Redfish, and the security model around the management network
- Structured cabling: copper vs DAC vs fiber, when to use each, and how cable hygiene affects mean time to repair
- Physical security controls and how to verify them on a site visit instead of trusting marketing copy
- Colocation selection scoring, SLA clauses that actually pay out during incidents, and how to map availability targets to contractual language

---

## The Rack: Your Basic Unit

Everything in a datacenter is organized around the 19-inch rack. The rack is the smallest unit of capacity you will plan against, the smallest unit of power and cooling you will reason about, and almost always the smallest unit of failure when something physical goes wrong. Before you size a Kubernetes cluster on bare metal, you should be able to picture exactly how many servers fit into a rack, how much power they draw, and how the rack ties into the rest of the facility. Once that picture is solid, every higher-level decision (replica counts, anti-affinity rules, failure domains) becomes much easier to ground.

### Standard Rack Dimensions

```ascii
┌─────────────────────────────────────────────────────────────┐
│                42U STANDARD RACK                             │
│         (19" wide, ~78" tall, ~36" deep)                    │
│                                                               │
│  1U = 1.75 inches (44.45mm) of vertical space              │
│  42U = total usable height                                   │
│                                                               │
│  ┌──────────────────────────────┐                           │
│  │ U42: Patch panel             │ ← networking              │
│  │ U41: ToR switch 1            │                           │
│  │ U40: ToR switch 2            │                           │
│  │ U39: Management switch       │                           │
│  │ U38: ── blank panel ──       │ ← airflow gap             │
│  │ U37-36: Server (2U)          │ ← compute starts here     │
│  │ U35-34: Server (2U)          │                           │
│  │ U33-32: Server (2U)          │                           │
│  │ U31-30: Server (2U)          │                           │
│  │ U29-28: Server (2U)          │                           │
│  │ U27-26: Server (2U)          │                           │
│  │ U25-24: Server (2U)          │                           │
│  │ U23-22: Server (2U)          │                           │
│  │ U21-01: ── expansion ──      │ ← 21U for growth         │
│  │ PDU-A  PDU-B (vertical mount)│ ← power (not in U space) │
│  └──────────────────────────────┘                           │
│                                                               │
│  Capacity: 8-16 servers (2U each) + networking              │
│  Weight: 1,000-2,500 lbs fully loaded                       │
│  Power: 5-20 kW depending on servers                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

A standard 42U rack gives you about 73.5 inches of usable vertical space, which is split between networking gear at the top, compute below it, and (usually vertical-mount) PDUs that do not consume rack-units at all. Notice that the layout above leaves real white space: blank panels for airflow, several U of growth at the bottom, and only eight servers populated even though sixteen would physically fit. That is intentional. A rack filled to the bolt is a rack with no room for the next generation of servers, no room for an unexpected NIC upgrade, and no room for the cabling sprawl that always grows over the lifetime of the cluster. Plan for sixty to seventy percent populated on day one.

### Server Form Factors

| Form Factor | Height | Use Case | Pros | Cons |
|------------|--------|----------|------|------|
| 1U | 1.75" | High density, simple workloads | Max servers per rack | Limited expansion, louder fans |
| 2U | 3.5" | Most K8s workloads | Good balance of density and expandability | Standard choice |
| 4U | 7" | GPU servers, high storage | Room for 4-8 GPUs or 24+ drives | Lower density |
| Blade | Varies | Very high density | Shared power/cooling/networking | Vendor lock-in, expensive chassis |

For Kubernetes workers, the 2U server is the boring, correct default. It accommodates dual-socket CPUs, sixteen to thirty-two DIMM slots, eight to twenty-four drive bays, and enough PCIe lanes to run a redundant pair of high-speed NICs without forcing trade-offs between storage and networking. 1U pizza-box servers maximise density on paper but pay for it in fan noise, fewer expansion slots, and aggressive thermal limits that throttle CPUs sooner under sustained load. 4U chassis are the right answer when GPUs, NVMe-heavy storage nodes, or serious accelerator counts are on the menu, and you can usually fit two of them stacked with a blank panel between them for airflow. Blade systems can look attractive in vendor slide decks, but the shared chassis becomes both a single point of failure and a long-term lock-in problem; for an open Kubernetes platform, prefer rackmount over blade unless density is the dominant constraint.

---

## Power Distribution

Power is the failure mode that surprises newcomers the most. Networking failures are familiar, disk failures are well-understood, but power failures are where the lessons get expensive. Every production deployment must be designed assuming that one of the two power feeds will fail at the worst possible moment, because that is exactly what eventually happens. The discipline below is not paranoia — it is what an experienced on-prem operator builds by default and never has to defend afterwards.

### Redundant Power (A+B Feeds)

Every production server has two power supply units (PSUs). Each PSU connects to a different power distribution unit (PDU). Each PDU connects to a different utility feed, traced all the way back through the building to ideally separate transformers and ideally separate substations. The diagram below shows the textbook arrangement, and it is worth lingering on because almost every power-related outage is the result of a violation somewhere along this chain (two PDUs sharing one breaker, two PSUs cabled into the same PDU by mistake, one UPS feeding both sides because the second UPS is in maintenance).

```ascii
┌─────────────────────────────────────────────────────────────┐
│               REDUNDANT POWER (A+B)                          │
│                                                               │
│  Utility Feed A              Utility Feed B                  │
│       │                           │                          │
│   ┌───▼───┐                   ┌───▼───┐                    │
│   │ UPS A │                   │ UPS B │                    │
│   └───┬───┘                   └───┬───┘                    │
│       │                           │                          │
│   ┌───▼───┐                   ┌───▼───┐                    │
│   │ PDU A │                   │ PDU B │                    │
│   │(rack) │                   │(rack) │                    │
│   └───┬───┘                   └───┬───┘                    │
│       │                           │                          │
│   ┌───▼───────────────────────────▼───┐                    │
│   │         SERVER                     │                    │
│   │  ┌─────────┐    ┌─────────┐       │                    │
│   │  │  PSU A  │    │  PSU B  │       │                    │
│   │  │(active) │    │(active) │       │                    │
│   │  └─────────┘    └─────────┘       │                    │
│   └───────────────────────────────────┘                    │
│                                                               │
│  Either feed can fail → server stays running                │
│  Both PSUs are hot-swappable                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

The key insight is that redundancy only protects you when each side can carry the full load alone. A pair of 30A PDUs does not give you "60 amps of capacity" — it gives you 30 amps of capacity with a backup. When teams treat the second feed as additional capacity instead of as a failover, they create a hidden single point of failure: under normal conditions both feeds carry roughly half the load and everything looks fine, but the moment one feed trips the other immediately overloads, trips its breaker, and takes the entire rack down. This is the classic "redundant in name only" topology, and it produces some of the most embarrassing outage post-mortems in the industry.

> **Pause and predict**: Your rack has two 30A/208V PDUs in an A+B redundant configuration. An engineer suggests you can safely run 10kW of servers because "we have 12kW total across both PDUs." Why is this reasoning dangerous? What is the actual safe limit, and what would happen one second after the A feed tripped under that 10kW load?

### PDU Types

| Type | Description | Use Case |
|------|-------------|----------|
| Basic | Power distribution only, no monitoring | Budget deployments |
| Metered | Shows total power draw per PDU | Standard production |
| Switched | Per-outlet power control (remote on/off) | Remote power cycling |
| Intelligent | Per-outlet monitoring + switching + alerts | Mission-critical |

For any production Kubernetes platform, metered PDUs are the floor and switched or intelligent PDUs are the right answer. The reason is operational rather than electrical: when a node hangs at three in the morning and the BMC is itself unresponsive, the only remaining recovery without a site visit is to cut power at the outlet and let the server cold-boot. Without a switched PDU, you are driving to the datacenter or paying remote-hands. With a switched PDU and a hardened jump host, you are running one curl command and going back to sleep. Over the lifetime of the cluster, the marginal cost of switched PDUs is paid back many times over in avoided drives.

### Power Budget Calculation

The conservative way to size power is to start from the server's worst-case nameplate draw, not from "typical" workloads. Workloads change, batch jobs spike, and a single misbehaving pod can pin every CPU core. The example below uses a Dell PowerEdge R760 in a representative configuration and walks through both average and peak. The point is not the specific numbers — those vary by SKU and generation — but the discipline of computing both numbers and sizing against the harder one.

```bash
# Per-server TDP (Thermal Design Power)
# Check server datasheet — example: Dell PowerEdge R760
# Max config: 2x Xeon 8490H (350W each) + 2TB RAM + 8 NVMe
# Server max draw: ~1,400W

# Typical K8s workload: 40-60% utilization = ~700W average

# Per-rack power budget:
# 8 servers x 700W avg = 5,600W = 5.6 kW average
# 8 servers x 1,400W max = 11,200W = 11.2 kW peak

# PDU rating: most colo racks provide 2x 30A @ 208V = 2x 6.24 kW
# With A+B redundancy, you can safely use ~5-6 kW continuous
# (one feed must handle full load if the other fails)

# Rule: never exceed 80% of a single PDU's capacity
# Single PDU capacity: 30A x 208V x 0.8 = 4,992W ≈ 5 kW
# Your 5.6 kW average exceeds this → need higher PDU rating
# Solution: upgrade to 2x 40A PDUs or reduce servers to 7
```

The 80% rule comes directly from the National Electrical Code in the United States and equivalent standards elsewhere: continuous loads (loads that run for three hours or more, which describes essentially every Kubernetes workload) must not exceed 80% of the circuit's rated capacity. That is not a margin you negotiate against — it is the legal and practical operating limit. When the math above says the average load is 5.6 kW and the per-feed budget is 4.99 kW, the answer is to drop a server out of the rack or upgrade the circuit. Squeezing in "just one more node" because the meter still reads green at the moment is exactly how the next outage starts.

---

## Cooling

Cooling is the silent partner of power. Every watt of electrical energy that goes into a server comes back out as heat almost immediately, and that heat has to be removed continuously or the entire room becomes a hazard within minutes. The cooling system is rated in kilowatts or in tons (one ton equals 3.517 kW of heat removal), and it is matched to the IT load by design — not by happy accident.

### Hot Aisle / Cold Aisle

```ascii
┌─────────────────────────────────────────────────────────────┐
│              HOT AISLE / COLD AISLE                           │
│                                                               │
│        COLD AISLE          HOT AISLE          COLD AISLE    │
│     (server intakes)    (server exhausts)   (server intakes)│
│                                                               │
│  ┌────┐ ◄── air ──── ┌────┐ ──── air ──► ┌────┐           │
│  │Rack│    intake     │Rack│    exhaust    │Rack│           │
│  │ A  │    (cool)     │ B  │    (hot)      │ C  │           │
│  │    │               │    │               │    │           │
│  │ ◄◄ │               │ ►► │               │ ◄◄ │           │
│  └────┘               └────┘               └────┘           │
│                                                               │
│  ▲ Cool air from         ▲ Hot air rises to                 │
│  │ raised floor           │ ceiling return                   │
│  │ or in-row cooling      │ (CRAC/CRAH units)               │
│                                                               │
│  Rule: Front of servers face cold aisle                     │
│  Rule: Back of servers face hot aisle                       │
│  Rule: Never mix orientations in the same row               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

The hot-aisle / cold-aisle pattern is what allows a room full of servers to be cooled efficiently. Cold air arrives at the front of every rack from a raised floor or in-row cooling unit, passes through the servers from front to back, and leaves the rear of the rack as hot exhaust into a dedicated hot aisle that returns to the cooling unit. The whole scheme depends on the physical separation of cold and hot air streams. The moment a server is installed backwards, a blanking panel is missing, or a cable cutout is left unsealed, hot exhaust short-circuits back to a cold intake and the local temperature rises rapidly. Most "mysterious" thermal alerts in well-run facilities turn out to be a containment breach somewhere within a few racks of the affected node, not a cooling unit failure.

### Cooling Capacity

```text
Cooling capacity is measured in kW or tons:
  1 ton of cooling = 3.517 kW of heat removal

Rule of thumb: 1 ton per 3-3.5 kW of IT load (depending on PUE)

Example:
  Rack load: 8 kW
  Cooling needed: 8 kW / 3.5 = 2.3 tons per rack
  10-rack deployment: 23 tons of cooling capacity

GPU racks can draw 15-30 kW → need 4-9 tons per rack
Some require liquid cooling (rear-door heat exchangers)
```

The reason GPU and accelerator racks demand a different conversation is that they cross the practical ceiling of air cooling. A traditional air-cooled facility tops out around 12 to 15 kW per rack before airflow becomes the limiting factor: even with perfect containment, you simply cannot move enough cubic feet per minute through a 19-inch rack to remove twenty kilowatts of heat. Above that ceiling, rear-door heat exchangers, in-row liquid coolers, or full direct-to-chip liquid cooling become non-optional. If your roadmap includes GPU training nodes, this is the conversation to have with the colocation provider on day one, not after the equipment arrives.

| Cooling Approach | Practical Ceiling | When To Use |
|---|---|---|
| Standard CRAC/CRAH with hot/cold aisle | 8-12 kW/rack | General compute, most CPU-heavy K8s clusters |
| Hot/cold aisle containment (curtains/doors) | 12-18 kW/rack | Dense compute, mixed CPU/GPU |
| Rear-door heat exchanger (water-cooled door) | 30-40 kW/rack | High-density GPU and accelerator nodes |
| Direct-to-chip liquid cooling | 40-100+ kW/rack | Large-scale AI training, HPC |

---

## Out-of-Band Management

The single most important capability for an on-prem operator is the ability to talk to a server when its operating system is dead. Every production-grade server includes a dedicated management processor — the BMC (Baseboard Management Controller) — that runs independently of the main CPUs, has its own NIC, its own firmware, its own IP address, and its own user database. The BMC can power-cycle the box, mount virtual media, attach a remote console, expose hardware sensors, and apply firmware updates, none of which require the OS to be running. Treating the BMC as a first-class part of the architecture is what separates "we'll drive there" from "we just fixed it remotely."

### IPMI / BMC / Redfish

```ascii
┌─────────────────────────────────────────────────────────────┐
│           OUT-OF-BAND MANAGEMENT                             │
│                                                               │
│  ┌────────────────────────────────────────┐                 │
│  │              SERVER                     │                 │
│  │                                         │                 │
│  │  ┌─────────┐       ┌──────────────┐   │                 │
│  │  │  BMC    │       │  Main OS     │   │                 │
│  │  │         │       │  (Linux)     │   │                 │
│  │  │ • Power │       │              │   │                 │
│  │  │   on/off│       │  Kubernetes  │   │                 │
│  │  │ • KVM   │       │  kubelet     │   │                 │
│  │  │ • Serial│       │              │   │                 │
│  │  │ • Sensor│       │              │   │                 │
│  │  │ • BIOS  │       │              │   │                 │
│  │  └────┬────┘       └──────────────┘   │                 │
│  │       │ (dedicated management NIC)     │                 │
│  └───────┼────────────────────────────────┘                 │
│          │                                                   │
│    Management Network (1GbE, isolated VLAN)                 │
│                                                               │
│  Vendor implementations:                                     │
│  • Dell: iDRAC (Integrated Dell Remote Access Controller)   │
│  • HPE: iLO (Integrated Lights-Out)                         │
│  • Lenovo: XCC (XClarity Controller)                        │
│  • Supermicro: IPMI                                         │
│                                                               │
│  Modern standard: Redfish API (RESTful, replaces IPMI)      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

The vendor names look like alphabet soup but they all describe the same thing: an embedded management controller with the same essential capabilities, exposed through either the legacy IPMI 2.0 protocol or the modern Redfish HTTPS API. New deployments should target Redfish because it is RESTful, JSON-based, properly versioned, and free of the long list of IPMI security weaknesses. IPMI remains the lowest common denominator and is still useful for one-off scripts against older hardware, but the strategic direction is unambiguous. When you procure new servers, treat first-class Redfish support as a non-negotiable line item rather than a nice-to-have.

> **Stop and think**: Your monitoring alerts you that a server in rack 7 is unreachable — the OS is not responding to SSH or pings. You are forty-five minutes away from the datacenter. What options does out-of-band management give you that in-band management does not? List at least three actions you could take remotely.

### Common BMC Operations

The BMC operates independently of the server's main OS, which means you can interact with the hardware even when the operating system has crashed or has not yet been installed. The ipmitool commands below connect over a dedicated management network to the BMC processor, bypassing the production network entirely. The Redfish examples that follow do the same thing through a modern REST API; pick one or the other based on what your hardware supports, but write the automation against Redfish whenever possible because you will not regret it three years from now.

```bash
# Using ipmitool (legacy, works with all vendors)
# Power operations
ipmitool -I lanplus -H 10.0.100.10 -U admin -P password chassis power status
ipmitool -I lanplus -H 10.0.100.10 -U admin -P password chassis power on
ipmitool -I lanplus -H 10.0.100.10 -U admin -P password chassis power cycle

# Check hardware sensors
ipmitool -I lanplus -H 10.0.100.10 -U admin -P password sensor list
# Inlet Temp     | 22.000     | degrees C  | ok  | 3.000 | 42.000
# CPU1 Temp      | 58.000     | degrees C  | ok  | 0.000 | 95.000
# Fan1           | 7200.000   | RPM        | ok  | 600   | na

# Set boot device for PXE (next boot only)
ipmitool -I lanplus -H 10.0.100.10 -U admin -P password chassis bootdev pxe

# Using Redfish API (modern, RESTful)
# Get system info
curl -k -u admin:password \
  https://10.0.100.10/redfish/v1/Systems/1 | jq '.PowerState, .Status'

# Power on
curl -k -u admin:password -X POST \
  https://10.0.100.10/redfish/v1/Systems/1/Actions/ComputerSystem.Reset \
  -H "Content-Type: application/json" \
  -d '{"ResetType": "On"}'

# Set PXE boot
curl -k -u admin:password -X PATCH \
  https://10.0.100.10/redfish/v1/Systems/1 \
  -H "Content-Type: application/json" \
  -d '{"Boot": {"BootSourceOverrideTarget": "Pxe", "BootSourceOverrideEnabled": "Once"}}'
```

The non-obvious operational rule here is that the BMC must be on its own VLAN, behind a firewall, reachable only from a hardened jump host, and never directly exposed to the production network. The BMC is the most powerful interface to the server that exists — anyone who reaches it can power it off, mount a malicious ISO and boot from it, capture the console, or flash firmware that survives an OS reinstall. Treating the management network as "just another VLAN" is one of the most common and most consequential security mistakes in on-prem deployments, and it is also one of the easiest to fix on day one.

---

## Cabling

Cables are the part of a datacenter that newcomers underestimate and senior engineers obsess over. A well-cabled rack is debuggable, expandable, and survives a hardware swap at three in the morning without taking the rest of the rack down by accident. A badly cabled rack is the kind of thing where a junior on-call hesitates to touch any single cable because they cannot tell which one will cause an outage. This is the kind of operational debt that compounds silently until it bites.

> **Pause and predict**: You need to connect 8 servers in a rack to the ToR switch (within 2 meters) and the ToR switch to a spine switch in a different row (40 meters away). For each connection, would you choose DAC, Cat6a, or OM4 fiber? Consider both cost and performance, and think about which cable type would be most painful if you had to swap it during an outage at midnight.

### Structured Cabling Standards

| Cable Type | Speed | Max Distance | Use Case |
|-----------|-------|-------------|----------|
| Cat6 (copper) | 10GbE | 55m | Short runs, management |
| Cat6a (copper) | 10GbE | 100m | In-rack and short between-rack |
| OM4 MMF (fiber) | 100GbE | 100m | Between-rack, between-row |
| OS2 SMF (fiber) | 100GbE+ | 10km+ | Between buildings, to WAN |
| DAC (copper twinax) | 25/100GbE | 5m | Within-rack switch-to-server |

For a Kubernetes cluster, the workhorse combination is DAC inside the rack and OM4 multimode fiber between racks. DAC cables are passive copper with the optics already integrated into the connector, which makes them cheaper than a fiber-plus-transceiver pair and gives lower latency over short distances. They have one important constraint: each end is paired to a specific switch and NIC vendor combination, so plan the SKUs alongside the hardware order, not after it arrives. For runs longer than five meters, fiber wins by default — OM4 reaches one hundred meters at 100 GbE, which is enough to span any reasonable row-to-row path inside a single facility.

```ascii
┌─────────────────────────────────────────────────────────────┐
│                CABLING TOPOLOGY                              │
│                                                               │
│  Server ──DAC 25GbE──► ToR Switch ──OM4 100GbE──► Spine    │
│  (2x ports,             (per rack)                 (2x for  │
│   LACP bond)                                       redundancy)│
│                                                               │
│  Server ──Cat6 1GbE──► Mgmt Switch ──Cat6──► Mgmt Network  │
│  (BMC/IPMI port)        (per rack)                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

Cable hygiene is the operational hygiene most often skipped under deadline pressure, and most regretted afterwards. Every cable should be labeled at both ends with the source rack/server/port and destination rack/switch/port; every cable should follow a documented path through the cable management arms; spare cables should be procured and stored on-site instead of ordered when they are needed; and the inventory of every cable should live in the same source-of-truth system that tracks servers and IP addresses. None of this is glamorous, but every datacenter veteran has a story about a four-hour outage that started with someone tugging a single unlabelled cable.

---

## Physical Security Checklist

Power and cooling get most of the engineering attention because they are the most common cause of unplanned outages, but physical security is part of availability engineering too. A facility that is easy to enter, poorly monitored, or too loose with escorting third-party vendors can turn a routine hardware incident into a security incident, and a security incident into a regulated-data incident. Physical security is also the single area where it is hardest to fix problems after the contract is signed, so it deserves the most rigour during selection.

### What To Verify In A Facility

| Control | What good looks like | Why it matters |
|---|---|---|
| Perimeter access | badge + biometric or staffed access at entry | prevents casual entry and badge sharing |
| Mantrap / controlled entry | single-person transition into secure area | reduces tailgating risk |
| Rack locking | locked cages or locking racks with audited key access | protects against direct hardware tampering |
| CCTV retention | camera coverage with retained footage and documented access | supports forensics after incidents |
| Visitor and vendor escorting | escorts required outside pre-approved maintenance flows | reduces third-party access risk |
| Media destruction process | documented disk handling and destruction workflow | avoids data leakage during decommission or RMA |
| Asset inventory | rack position, serial, and owner recorded | lets you prove what hardware exists and where |
| Incident logging | every physical access event is logged and reviewable | essential for regulated or shared environments |

### Quick Facility Walkthrough Questions

Before you sign a colocation contract or approve a private room, the following questions are the ones that separate a facility that has thought about security from one that has only written about it on a marketing page. Bring this list to the site visit and write the answers down. Vague answers are themselves a result.

- Who can physically enter the cage or room without your team present, and how is that list maintained?
- How are emergency vendors or facilities engineers admitted after hours, and who approves the entry?
- How long are camera feeds and access logs retained, and how do you request them?
- What happens if a drive fails and the vendor wants to take it away for RMA — who controls the chain of custody?
- Can you require locked cages, dual authorization, or named-access lists, and at what additional cost?

If the answers are vague, hand-wavy, or "we'd have to check," the security posture is weak even if the marketing brochure says "enterprise grade." A facility that takes security seriously can answer all of these questions in a single conversation with confidence and specificity.

### Minimum On-Prem Physical Security Baseline

For any production Kubernetes platform, the following are non-negotiable: a named-access list for your racks or cage, camera coverage for entry points and your physical footprint, a documented disk handling and destruction policy, no shared BMC network with other tenants, locked racks or locked cage doors, and the ability to retrieve access logs after an incident. Anything below this baseline should be treated as a hard reject regardless of price, because retrofitting these controls into a facility that does not provide them is operationally impractical.

### Facility Verification Checklist

Use this during a site visit, an annual review, or a post-incident audit. Do not accept "yes, we do that" without evidence — the entire point of an audit is that the answer is on paper, dated, and signed. The "Accept only if" column is what separates a control that exists from a control that works.

| Verify | Evidence to request | Accept only if |
|---|---|---|
| Access control | sample access log export, named-access policy | every entry is attributable to a named person and logs can be retrieved on demand |
| After-hours entry | written escalation and identity verification process | no unescorted after-hours access without a documented approval path |
| Rack or cage locking | live demonstration of locks and key/card ownership | your hardware is separately lockable from neighboring tenants |
| CCTV coverage | camera map and retention period | entry paths and your footprint are covered for at least 90 days |
| Visitor handling | visitor register and escort procedure | visitors and vendors are time-bound, logged, and escorted |
| Media handling | disk RMA and destruction workflow | failed drives stay under your control or are destroyed with certificate |
| Management network isolation | network diagram for BMC/IPMI access | BMC traffic stays on a dedicated management network with tenant separation |
| Incident evidence | sample incident report or security event workflow | the provider can correlate badge, camera, and ticket data during an investigation |

A simple pass rule for production: reject the facility if any of the following are missing — auditable access logs, locked rack or cage access, documented media handling, or isolated management networking. These four are the floor below which no amount of negotiation will produce a safe environment for production data.

---

## Colocation Selection And SLA Framework

Do not choose a facility on rack price alone. The wrong contract can be cheap on paper and expensive during outages, and the difference is rarely visible until the first major incident. The framework below scores facilities across six dimensions, sets hard gates on the dimensions that cannot be compensated for elsewhere, and then ties the chosen contract back to the platform availability target so that the SLA language actually supports the math.

### Facility Selection Matrix

| Area | What to evaluate | Red flag |
|---|---|---|
| Power | A+B feeds, contracted kW, generator test process, UPS maintenance window policy | only one real utility path or vague bypass procedures |
| Cooling | stated per-rack density, containment design, hot-spot escalation process | no practical answer for high-density or GPU racks |
| Network | carrier diversity, cross-connect lead time, remote hands for cabling | single carrier dependency or slow change lead times |
| Operations | 24/7 staffed presence, remote hands SLA, incident escalation path | "best effort" support without timelines |
| Security | access controls, visitor handling, audit logs, rack/cage options | shared access or poor access logging |
| Contract | service credits, exit clauses, growth terms, renewal uplift | credits too small to matter or opaque repricing |

Score each area from one to five during evaluation and weight the result instead of treating every row as equal. A reasonable starting weighting is power thirty percent, cooling twenty, network twenty, operations fifteen, security ten, and contract five — adjusted for your specific risk profile. The reason power dominates is empirical: in nearly every published on-prem outage post-mortem, a power event is somewhere in the causal chain. The reason contract is the smallest weight is also empirical: a great contract cannot save you from a poorly run facility, and a mediocre contract can be fixed at renewal if the underlying operations are sound.

For a production Kubernetes platform, set hard gates before any price comparison: reject any site that scores below four out of five in Power, Operations, or Security; reject any site that cannot document dual-feed design, twenty-four-by-seven staffing, and named incident escalation contacts; and only compare total annual cost after a site clears those technical gates. This sequencing prevents a cheap site with weak operations or weak physical controls from winning on spreadsheet price alone, which is the single most common procurement failure mode when engineering is not in the room.

### SLA Clauses That Actually Matter

When negotiating the contract, push on these items explicitly because the standard boilerplate will paper over all of them. A "99.99% uptime" promise on the front page is meaningless if the credits are capped at one month of fees and the response times for remote hands are buried in an appendix as "commercially reasonable efforts."
These clauses keep procurement accountable: power continuity commitments, cooling outage coverage, emergency response guarantees, maintenance notice windows, cross-connect delivery timelines, outage communication cadence, and expansion or exit terms.
For real-world examples of physical security failures, see [Defense in Depth](../../platform/foundations/security-principles/module-4.2-defense-in-depth/).
<!-- incident-xref: target-2013 -->

### Practical Negotiation Rule

Tie the colocation contract back to your target availability and let the math do the arguing for you. If your platform target is 99.95%, but the facility only offers weak credits and "commercially reasonable efforts" for remote hands, you do not actually have infrastructure aligned to that goal — you have a marketing target with no contractual support. The facility is part of the platform, not just the building around it, and the contract is the part of the platform that lives in legal's filing system instead of in Git.

### Map SLA Terms To Availability Targets

Start with your platform target, then ask whether the facility contract materially supports it. The downtime budget column below is annualized — at 99.95%, you have roughly four hours and twenty-three minutes of total outage in a year, including planned maintenance, network blips, and any provider-side incident. Spend it carefully.

| Platform target | Annual downtime budget | Facility expectation |
|---|---|---|
| 99.9% | 8h 45m | acceptable for non-production or internal platforms; remote hands can be slower and credits are less critical |
| 99.95% | 4h 23m | dual power, dual carriers, urgent remote hands within 30 minutes, cooling covered in SLA, incident updates every 30 minutes |
| 99.99% | 52m 36s | concurrent maintainability, strong power and cooling credits, urgent remote hands within 15 minutes, clear maintenance exclusions, fast cross-connect delivery |

If the facility promises only "commercially reasonable efforts," that wording is not aligned to a 99.95% or 99.99% platform target, and no amount of clever Kubernetes design will close the gap. The cluster's availability is bounded above by the facility's availability minus your own operational error rate, and the contract is the only durable record of what the facility owes you when it fails to deliver.

### Example SLA Clauses To Take To Procurement

Use wording like the following as a negotiation starting point with procurement and legal. None of this is legal advice, but it gives engineering, procurement, and legal teams concrete language to negotiate against instead of accepting generic availability promises.

- `Power event`: "Loss of either contracted redundant feed serving Customer Equipment for more than 5 consecutive minutes constitutes an SLA event."
- `Cooling event`: "Rack inlet temperature above 27C for more than 15 consecutive minutes constitutes an SLA event."
- `Remote hands`: "Urgent incidents are acknowledged within 15 minutes and a technician is at the rack within 30 minutes, 24x7."
- `Incident communications`: "Provider sends initial customer notice within 15 minutes of a site-impacting event and status updates at least every 30 minutes until closure."
- `Network handoff`: "Standard cross-connect orders are delivered within 5 business days; missed delivery dates earn fee credits."
- `Service credits`: "Credits scale with duration and severity, including separate credits for power, cooling, and missed remote-hands response times."

---

## Did You Know?

- **A typical datacenter rack weighs 1,000 to 2,500 pounds fully loaded.** Many office buildings physically cannot support this weight: standard office floors are rated for fifty to one hundred pounds per square foot, while a fully loaded rack exerts three hundred to five hundred pounds per square foot on a roughly six-square-foot footprint. This is why purpose-built datacenters have reinforced floors, structural engineering reviews, and explicit per-tile weight limits, and why you cannot simply "convert a closet" into a server room past a few servers.

- **UPS batteries last three to five years and are the most common single point of failure in power systems.** A UPS that has not had a battery replacement in four or more years may provide only thirty seconds of runtime instead of the rated ten or fifteen minutes, and you will not find that out until the next utility blip. Best-in-class operators test their UPSes under load annually, schedule battery replacements on a calendar rather than on failure, and treat the test report as a contractual deliverable from the colocation provider.

- **Datacenter fires are extremely rare but devastating when they occur.** The OVHcloud Strasbourg fire in March 2021 destroyed an entire datacenter building and damaged another, taking 3.6 million websites offline. The cause was a faulty UPS, and the facility did not have an automatic fire-extinguishing system installed at all — not temporarily disabled, not under maintenance, simply never installed. Verify the fire suppression system on every site visit; "we have one" is not the same as "we have a tested one with a recent inspection certificate."

- **The Redfish API is steadily replacing IPMI as the standard for server management.** IPMI was designed in 1998 and has known security vulnerabilities, including cleartext password transmission in some configurations and the well-publicized cipher zero authentication bypass. Redfish uses HTTPS, JSON, modern authentication, and is properly versioned with a clear deprecation path for old endpoints. If you are buying new servers, insist on Redfish support as a procurement requirement and audit the endpoints during burn-in.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Single PDU feed (or both PSUs into one PDU by accident) | Power loss = entire server down even though it has dual PSUs | Always cable PSU A to PDU A and PSU B to PDU B; verify with a labeled photograph after install |
| BMC on production network | BMC has full hardware control; one compromised host can power off the cluster or boot a malicious ISO | Isolated management VLAN behind a firewall, accessible only from a hardened jump host |
| No cable labeling | Cannot trace cables during incidents; recovery time balloons at three in the morning | Label both ends of every cable with rack/server/port and rack/switch/port; record in source of truth |
| Mixing hot and cold aisles in the same row | Hot exhaust recirculates to cold intakes; localized thermal alarms appear out of nowhere | Strict hot/cold-aisle discipline; blank panels in every empty U; sealed cable cutouts |
| Ignoring rack and floor weight limits | Floor tile collapse or rack tipping during installation | Check floor rating before delivery; distribute weight evenly across the rack; secure the rack to the floor |
| Default BMC passwords left in place | Anyone reaching the management network can power off your cluster or flash firmware | Rotate all BMC passwords during burn-in; prefer per-host credentials managed by a vault; enable certificate auth where supported |
| No UPS load testing | Battery is silently dead when it is finally needed; the entire redundancy investment is fictional | Annual UPS load test as a contractual deliverable; replace batteries proactively at three to four years |
| Sizing rack power to both feeds combined | The redundant feed carries half the load instead of acting as a true backup; one trip cascades into a full outage | Size sustained IT load to one feed at 80% derating; treat the second feed as failover, not capacity |

---

## Quiz

### Question 1
Your rack has two 30A/208V PDUs (A and B feeds). A new team requests space for ten servers that draw approximately 700 watts each at typical Kubernetes utilization. Operations approves the request because "ten times 700 is 7 kW, and we have 12 kW of total PDU capacity." A week after install, during a routine UPS maintenance window that briefly drops the A feed, the entire rack goes dark. Walk through the math and explain the failure.

<details>
<summary>Answer</summary>

Each PDU has a circuit capacity of 30 A × 208 V = 6,240 W, but the National Electrical Code (and equivalent codes elsewhere) requires that continuous loads — anything running for three hours or more, which describes every Kubernetes workload — be limited to 80% of the rated capacity. That gives 4,992 W per PDU as the usable continuous limit, or roughly 5 kW.

The reasoning failure is treating "12 kW of total PDU capacity" as a single shared budget. With A+B redundancy, the design contract is that **either feed alone must carry the full load**, because the entire point of the second feed is failover, not additional headroom. The maximum sustained IT load for this rack is therefore the capacity of one PDU at 80%: about 5 kW.

At 7 kW of normal load, both feeds happily carry roughly 3.5 kW each and everything looks fine on the dashboards. The instant the A feed dropped, the entire 7 kW landed on the B feed, which immediately exceeded its 80% derated limit. The breaker on the B feed tripped within seconds of the trip current, and the rack went dark. The post-mortem reads "redundant power failure" but the real cause was a sizing error baked in months earlier.

The fix is to either reduce the rack to seven servers (about 4.9 kW), upgrade to higher-amperage PDUs (40 A would give ~6.6 kW per feed at 80%), or split the workload across two racks.
</details>

### Question 2
You need to remotely reinstall the OS on a server. The server is powered on but the OS is unresponsive (kernel panic) and SSH is refused. You are an hour away from the datacenter, and there is no remote-hands response available for several hours. Walk through the exact steps you would take using out-of-band management, including what you would verify after each step.

<details>
<summary>Answer</summary>

Working through the BMC (via Redfish here, but the same flow works with ipmitool):

1. **Verify the server's actual state.** Do not assume the OS hang means the server is dead — confirm the BMC sees it as powered on and not, for example, halfway through a stuck shutdown.
   ```bash
   curl -k -u admin:pass https://bmc-ip/redfish/v1/Systems/1 | jq '.PowerState, .Status'
   # "On", "Health": "OK" — server hardware is fine, OS is stuck
   ```

2. **Capture forensic state before rebooting.** Open the virtual console (KVM-over-IP) through the BMC web UI or take a screenshot of the current console output via Redfish. Kernel panic messages and stack traces vanish on reboot, and you will want them in the post-mortem. Skipping this step is the most common operational mistake.

3. **Set the next boot to PXE, one-shot only.** This protects you from reboot loops if the install fails — the server will only PXE-boot once before falling back to its normal boot order.
   ```bash
   curl -k -u admin:pass -X PATCH https://bmc-ip/redfish/v1/Systems/1 \
     -H "Content-Type: application/json" \
     -d '{"Boot": {"BootSourceOverrideTarget": "Pxe", "BootSourceOverrideEnabled": "Once"}}'
   ```

4. **Force-restart the server.** Graceful shutdown will not work because the OS is unresponsive — `ForceRestart` is the BMC equivalent of holding the power button.
   ```bash
   curl -k -u admin:pass -X POST \
     https://bmc-ip/redfish/v1/Systems/1/Actions/ComputerSystem.Reset \
     -d '{"ResetType": "ForceRestart"}'
   ```

5. **Watch the virtual console** to verify PXE boot starts, the installer pulls its image, and the install completes. If anything goes wrong, you can intervene through the same console.

6. **After OS install completes**, verify the node rejoins the Kubernetes cluster via `kubectl get nodes` and that the kubelet logs show clean startup. Write up the post-mortem with the panic trace you captured in step 2.

The whole sequence happens from your laptop, which is exactly why isolated, well-secured BMC access is non-negotiable for on-prem operations.
</details>

### Question 3
Your monitoring shows that a single server's inlet temperature rose from 22C to 35C over thirty minutes, while the other servers in the same rack show stable inlet temperatures around 22C. What is the most likely cause and how does that diagnosis differ from the case where every server in the row warms up at the same rate?

<details>
<summary>Answer</summary>

When **only one server in a rack warms up** while its neighbors stay cool, the cause is almost always something local to that server or its position in the rack — not a facility-wide cooling event:

- A blanking panel directly above the affected server has been removed, allowing hot exhaust from the rear to circulate to the front.
- The server has been reinstalled backwards after maintenance, drawing in the rack's own hot exhaust as its intake.
- A cable cutout immediately above the server is unsealed, creating a hot-air bypass.
- The server's own front-bezel filter is clogged or the airflow inside the chassis is degraded (a failed fan, a dislodged shroud).

**When the entire row warms up together**, the diagnosis is very different — that points at the facility:

- The CRAC/CRAH unit serving that row has failed or gone into limp mode.
- A raised-floor tile has been displaced, reducing cold-air delivery to the row.
- Adjacent containment has been opened (curtains pulled aside, doors propped open).
- A neighboring rack has been densely loaded with new equipment that exceeds the cooling zone's capacity.

The action sequence in either case is similar but with different first responders:
1. Localized → check the rack physically (or via remote photos) for blanking panels, server orientation, and cable cutouts; this is usually a colo remote-hands ticket.
2. Row-wide → page facilities immediately and ask whether a cooling unit alarm is active; this is a building-systems incident.
3. In both cases, drain Kubernetes pods proactively from the affected nodes if temperature is approaching 38–40C, because thermal throttling will silently degrade workload performance and at 50C+ the servers will protective-shutdown on their own.

Setting BMC temperature alerts at 30C (warning) and 38C (critical), exposed to Prometheus via the IPMI exporter, is what makes this diagnosis possible before the user impact starts.
</details>

### Question 4
You are designing the cabling for a new rack. The rack contains eight Kubernetes worker nodes, two ToR switches at the top of the rack, and one management switch. Each worker has two 25 GbE ports that need to LACP-bond to the two ToRs, and each worker also has a 1 GbE BMC port. The ToRs uplink to a spine switch in another row, forty meters away. Describe the cable type, count, and labeling scheme you would specify, and explain the trade-offs you considered.

<details>
<summary>Answer</summary>

**Cable choices, with reasoning:**

- **Server data plane (within rack)**: 16 × DAC twinax cables at 25 GbE. Each worker needs two 25 GbE links — one to ToR-1 and one to ToR-2 — for an LACP bond that survives a single switch failure. DAC is the right choice for these short, in-rack runs because it is cheaper than fiber-plus-transceivers, has lower latency, and uses less power. The five-meter limit on DAC is well within the rack's vertical span. Trade-off: DAC cables are vendor-paired (the optics inside the connector are matched to specific NIC and switch SKUs), so they must be ordered alongside the hardware, not as an afterthought.

- **Server BMC (within rack)**: 8 × Cat6 patch cables to the management switch. 1 GbE is more than sufficient for BMC traffic, copper is cheap and easy to swap, and the cable run from any U position to the top-of-rack management switch is well under the 55-meter Cat6 limit. The BMC cables go to a separate switch on a separate VLAN, never the data-plane ToRs.

- **ToR uplinks (between rack and spine, 40m)**: 4 × OM4 multimode fiber at 100 GbE (two from each ToR for redundancy). DAC cannot reach 40 meters; Cat6a tops out at 10 GbE and would bottleneck the uplink. OM4 fiber comfortably supports 100 GbE at this distance and gives headroom for the future 200/400 GbE upgrade path. Trade-off: optics on each end add cost and a small failure surface, but the alternative does not exist for this distance and speed.

- **Management switch uplink**: 2 × Cat6 to the building's management network distribution layer (or 2 × OM4 if the run exceeds 55m).

**Labeling scheme**: every cable labeled at both ends with `srcRack/srcUnit/srcPort -> dstRack/dstUnit/dstPort`, recorded in the source-of-truth inventory (NetBox or equivalent), and physically routed through the cable management arms in a documented path. The labels should survive being unplugged and replugged, which means printed adhesive labels on heat-shrink, not handwritten paper tags. Redundant cables (e.g., the second ToR uplink) should follow physically separate paths through the cable arms so a single accident does not sever both.

The total bill of materials looks underwhelming on paper but unambiguously specifies what arrives at the loading dock, which is what prevents the standard "we ordered the wrong DAC SKU" delay during install.
</details>

### Question 5
Your platform has an availability target of 99.95% and currently runs in a colocation facility whose contract promises "commercially reasonable efforts" for remote hands and caps total monthly service credits at one month of recurring fees. During a recent incident, a single failed PSU took six hours to replace because the night-shift technician needed approval from a manager who was unreachable. Make the case to your engineering leadership for renegotiating or replacing the contract, grounding the argument in the SLA framework from this module.

<details>
<summary>Answer</summary>

The argument has three layers: math, contract, and operational evidence.

**1. The math.** A 99.95% availability target gives an annualized downtime budget of roughly 4 hours and 23 minutes — across all causes, including planned maintenance, network blips, and incidents. A single six-hour PSU replacement has already consumed more than the entire annual downtime budget on a single hardware event, with eleven months still remaining in the year. If incidents like this are even mildly frequent, the platform cannot mathematically achieve its target regardless of how well the Kubernetes layer is operated above it.

**2. The contract.** "Commercially reasonable efforts" is unenforceable language that gives the provider unilateral discretion over response time. For a 99.95% target, the SLA framework calls for: urgent remote hands acknowledged within 15 minutes and on-rack within 30 minutes, twenty-four-by-seven; cooling covered explicitly (not just total-site outages); incident updates at least every 30 minutes until closure; and service credits that scale with duration and severity rather than capping at a single month of fees. The current contract has none of these properties. The cap on credits in particular means the provider has no financial incentive to prevent long incidents — once they have hit the cap, additional outage costs them nothing.

**3. The operational evidence.** The six-hour PSU replacement was caused by a process failure (manager approval unreachable), not by a parts shortage. That tells leadership the facility's operations are immature: it lacks documented escalation paths, it lacks delegated authority for routine hardware swaps, and its night-shift staffing model assumes daytime decision-making. These are systemic operational problems that will recur on every incident, and they are exactly the dimensions the framework's "Operations" score (weighted 15%) is meant to surface during selection.

**Recommendation to leadership**: either renegotiate the contract with concrete clauses (15-minute acknowledgment, 30-minute technician response, named escalation contacts, separate credits for power/cooling/remote-hands, no monthly cap until totals exceed two months of fees) or initiate an evaluation of two alternative facilities using the six-dimension scoring matrix and treat Power, Operations, and Security as hard gates before price comparison. The facility is part of the platform — when its operations are below the target's requirements, the rest of the stack cannot compensate.
</details>

### Question 6
You inherit an on-prem cluster from a previous team. On your first walkthrough you notice four things: (a) the BMC network is on the same VLAN as the production Kubernetes nodes; (b) all BMCs use the vendor's default credentials; (c) the rack PDUs are basic (no monitoring); and (d) the ToR switch uplinks are two DAC cables routed through the same cable arm. Rank these issues by severity and explain the order.

<details>
<summary>Answer</summary>

**Order from most to least urgent: (b) → (a) → (d) → (c).**

**(b) Default BMC credentials — fix first, today, before doing anything else.** Default credentials on the BMC mean that anyone who can reach the management network — which, given (a), is the same as anyone who can reach the production network — can power-cycle every server, mount a malicious ISO, view consoles for secrets being typed during boot, or flash firmware that survives a reinstall. This is the single highest-impact, easiest-to-exploit, and easiest-to-fix issue in the list. Rotate all BMC passwords immediately, ideally with a vault-managed per-host credential, and audit BMC access logs for any prior unauthorized activity.

**(a) BMC on the production VLAN — fix in the same sprint.** Even after rotating credentials, exposing BMCs on the production network is a permanent design flaw. Any compromised pod, escaped container, or careless network ACL gives an attacker a path to the most powerful interface in the building. The fix is a dedicated management VLAN, firewall rules that allow access only from a hardened jump host, and ideally a separate physical NIC on each server for the BMC. This is more invasive than (b) — it requires a maintenance window — but it must follow immediately after the credential rotation, otherwise the credential rotation only buys time, not security.

**(d) DAC uplinks routed through the same cable arm — fix at next maintenance window.** Two redundant uplinks that share a physical path are not redundant against the failure mode that most often takes down both at once: a human pulling on the wrong cable bundle, or a cable arm closing on both at the same time. The fix is to route the two uplinks through physically separate arms or paths, ideally on opposite sides of the rack. This is an availability issue rather than a security issue, and it can be scheduled rather than rushed.

**(c) Basic PDUs with no monitoring — plan for the next refresh cycle.** This is a real operational gap, but it is a long-term cost rather than an acute risk. Without metering, you cannot precisely size capacity, you cannot detect creeping over-utilization, and you cannot remotely power-cycle a hung server. All of these matter, but none of them is currently exploitable or imminently failing. Schedule the upgrade to switched PDUs as a planned procurement item, ideally synchronized with the next hardware refresh.

The general rule the ranking demonstrates: security issues with low effort to exploit and full hardware control beat availability issues, which beat operational ergonomics, with the additional rule that "default credentials anywhere on a privileged interface" is always the very first thing fixed.
</details>

### Question 7
You are presented with a vendor pitch for a new colocation facility. The brochure highlights "redundant power, redundant cooling, 24/7 staffing, world-class security, and 100% uptime SLA." You have one site visit scheduled. Write the five questions you would ask during the visit, and explain what each answer (or lack of answer) would tell you about whether the facility actually delivers on the brochure.

<details>
<summary>Answer</summary>

**Question 1: "Walk me through the path from the utility transformer to my rack's PDU A and PDU B. Are the two paths physically and electrically separate from substation to PDU?"**

A confident answer traces the path through two transformers, two utility feeds, two UPSes, two distribution paths, and two PDUs, with no shared single points of failure. A vague answer ("they're redundant") almost always means there is a shared switchgear, a shared bus, or a shared transfer switch somewhere in the middle that converts the "redundant" pair into a single point of failure. The OVHcloud Strasbourg fire and the original story that opens this module are both examples of "redundant" systems sharing a hidden component that took everything down at once.

**Question 2: "What is the contracted kW per rack, and how do you handle a rack that wants to exceed that — both in terms of cooling and in terms of physical room?"**

This question separates facilities that have actually thought about density from those that have only thought about square footage. A serious answer talks about hot-aisle containment, in-row cooling, rear-door heat exchangers, and the specific kW ceiling at which they require liquid cooling. A weak answer is "we'd have to talk to engineering," which means the answer is "we don't know and we will figure it out at your expense."

**Question 3: "What is the mean response time for urgent remote hands at 3 AM on a Sunday, and what does the technician have authority to do without further approval?"**

The first part of the answer reveals the staffing model; the second part reveals the operational maturity. A serious facility answers in minutes (15 to 30) and lists explicitly what the night-shift technician can do without paging a manager (replace failed parts from spares stock, power-cycle servers, swap drives in marked failure states). A weak facility answers in hours, or says "we'd page our on-call engineering manager," which means six-hour incidents like the one in Question 5 are the floor, not the exception.

**Question 4: "Show me a sample access log for a rack from the last week, with names redacted. How are visitor entries distinguished from staff entries, and how long are these retained?"**

The act of producing the log on demand reveals whether logging actually works or only exists on paper. A facility with mature controls hands you a sample within a few minutes. A facility without them tells you they will "have to check" or refers you to a sales rep. Retention shorter than ninety days makes post-incident forensics functionally impossible for any but the most recent events.

**Question 5: "Tell me about the worst incident this facility has had in the last two years and how it was resolved."**

This is a behavioral interview question for the facility itself. A mature operations team answers it candidly, with a real incident, a real timeline, a real root cause, and a real set of changes that resulted. An operations team that has never had a serious incident is either lying or new; either way, this is the answer that tells you whether the people running the building know how to recover from a bad day. "We've never had a major incident" is the worst possible answer.

The "100% uptime SLA" promise on the brochure is meaningless without these answers — every facility has had outages, and the question is only whether the contract pays out enough to matter and the operations team learns from each incident.
</details>

---

## Hands-On Exercise: Inventory and Manage a Server

**Task**: Use out-of-band management to inventory and perform basic operations on a server, then capture the results in a runbook.

> **Note**: This exercise requires access to a server with IPMI/BMC. If you do not have physical hardware, you can practice the Redfish API calls against the DMTF Redfish Mockup Server: `docker run -p 8000:8000 dmtf/redfish-mockup-server`. The mockup behaves like a real BMC for read-only operations, which covers most of the steps below.

### Steps

1. **Discover BMC information** for the target server, recording the vendor, firmware version, and management NIC IP in your runbook.

```bash
# If you have ipmitool installed
ipmitool -I lanplus -H <BMC_IP> -U admin -P password mc info

# Using Redfish
curl -k -u admin:password https://<BMC_IP>/redfish/v1/ | jq '.'
```

2. **Read hardware sensors** and record the baseline: inlet temperature, CPU temperatures, fan RPMs, and PSU status.

```bash
# IPMI sensors
ipmitool -I lanplus -H <BMC_IP> -U admin -P password sensor list | grep -E "Temp|Fan|Power"

# Redfish thermal
curl -k -u admin:password \
  https://<BMC_IP>/redfish/v1/Chassis/1/Thermal | jq '.Temperatures[]'
```

3. **Check power consumption** to verify the server is in the expected range for its workload, and record both the instantaneous draw and the configured power cap if any.

```bash
# Redfish power
curl -k -u admin:password \
  https://<BMC_IP>/redfish/v1/Chassis/1/Power | jq '.PowerControl[0].PowerConsumedWatts'
```

4. **Practice power operations** on a non-production server, capturing the time taken for each operation in your runbook so future on-call engineers know what to expect.

```bash
# Power status
curl -k -u admin:password \
  https://<BMC_IP>/redfish/v1/Systems/1 | jq '.PowerState'

# Graceful shutdown
curl -k -u admin:password -X POST \
  https://<BMC_IP>/redfish/v1/Systems/1/Actions/ComputerSystem.Reset \
  -d '{"ResetType": "GracefulShutdown"}'

# Power on
curl -k -u admin:password -X POST \
  https://<BMC_IP>/redfish/v1/Systems/1/Actions/ComputerSystem.Reset \
  -d '{"ResetType": "On"}'
```

5. **Set a one-shot PXE boot** and observe via the virtual console that the server actually attempts PXE on the next reboot, then resets the boot order to its normal disk-first state.

6. **Write a short runbook entry** that captures the BMC IP, sample commands for the four most common operations (status, force-restart, set PXE, sensor read), the expected output for each, and the security notes for who should be allowed to run them.

### Success Criteria
- [ ] BMC accessible via the dedicated management network (not the production VLAN).
- [ ] Hardware sensors readable for temperature, fan speed, and power consumption.
- [ ] Power consumption measured and recorded in a baseline note.
- [ ] At least one power cycle performed successfully on a non-production server, with the time-to-power-on recorded.
- [ ] Redfish API used end-to-end for at least one operation, even if IPMI is your fallback for older hardware.
- [ ] Runbook entry committed to your team's documentation source of truth, including security notes on access control.

---

## Next Module

Continue to [Module 2.2: OS Provisioning & PXE Boot](../module-2.2-pxe-provisioning/) to learn how to automatically install operating systems on bare-metal servers over the network using the BMC and PXE infrastructure introduced in this module.
