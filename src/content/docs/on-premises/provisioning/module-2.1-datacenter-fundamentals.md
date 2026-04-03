---
title: "Module 2.1: Datacenter Fundamentals"
slug: on-premises/provisioning/module-2.1-datacenter-fundamentals
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` | Time: 45 minutes
>
> **Prerequisites**: [Module 1.2: Server Sizing](../planning/module-1.2-server-sizing/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** datacenter facility requirements including power redundancy, cooling capacity, and physical security for Kubernetes deployments
2. **Design** rack layouts with proper power distribution, cable management, and network connectivity for bare-metal clusters
3. **Diagnose** physical infrastructure failures (PDU trips, cooling issues, network cabling) that manifest as Kubernetes outages
4. **Plan** colocation facility selection criteria and negotiate SLAs that align with your availability targets

---

## Why This Module Matters

At 2:47 AM on a Tuesday in 2019, an SRE at a fintech company received an alert: "API server unreachable." She SSH'd into the jump box — connection refused. Tried the VPN — timeout. Called the colocation facility. The night operator confirmed: "Your rack is dark. Both PDU feeds tripped." A firmware bug in the rack PDU had caused a cascading overcurrent shutdown when a scheduled firmware update ran on the UPS during a power test. The UPS entered bypass mode, the PDU detected an overvoltage condition, and both A and B feeds tripped simultaneously.

The SRE drove 45 minutes to the datacenter, badged in, walked to row 7, rack 14, and manually reset both PDUs. The cluster came back in 8 minutes. Total outage: 1 hour 23 minutes. Total revenue impact: $84K in failed transactions.

She later told her team: "I have a PhD in distributed systems, but the thing that brought us down was a 20-amp circuit breaker and a firmware bug in a power strip. Every layer of abstraction sits on top of physical infrastructure, and if you don't understand that physical layer, you can't debug the failures that come from it."

If you are operating on-premises Kubernetes, you need to understand the physical infrastructure. Not at an electrician's level of detail, but enough to make smart decisions, talk to facilities teams, and debug failures that start below the OS.

> **The Building Foundation Analogy**
>
> The datacenter is the foundation of your house. Nobody talks about the foundation at dinner parties. You never interact with it directly. But if it cracks, everything above it shifts, breaks, and becomes uninhabitable. Understanding racks, power, cooling, and network cabling is understanding the foundation that your Kubernetes clusters stand on.

---

## What You'll Learn

- Rack standards and physical server layout
- Power distribution: PDUs, UPS, redundancy (A+B feeds)
- Cooling: hot aisle/cold aisle, kW per rack capacity
- Out-of-band management: IPMI, BMC, iDRAC, iLO, Redfish
- Cabling: structured cabling, fiber vs copper, cable management
- Colocation vs owned datacenter considerations

---

## The Rack: Your Basic Unit

### Standard Rack Dimensions

```
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

### Server Form Factors

| Form Factor | Height | Use Case | Pros | Cons |
|------------|--------|----------|------|------|
| 1U | 1.75" | High density, simple workloads | Max servers per rack | Limited expansion, louder fans |
| 2U | 3.5" | Most K8s workloads | Good balance of density and expandability | Standard choice |
| 4U | 7" | GPU servers, high storage | Room for 4-8 GPUs or 24+ drives | Lower density |
| Blade | Varies | Very high density | Shared power/cooling/networking | Vendor lock-in, expensive chassis |

**For Kubernetes, 2U servers are the standard.** They support dual CPU sockets, 16-32 DIMM slots, 8-24 drive bays, and sufficient PCIe slots for NICs and NVMe.

---

## Power Distribution

### Redundant Power (A+B Feeds)

Every production server has two power supply units (PSUs). Each connects to a different power distribution unit (PDU). Each PDU connects to a different utility feed:

```
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

### PDU Types

| Type | Description | Use Case |
|------|-------------|----------|
| Basic | Power distribution only, no monitoring | Budget deployments |
| Metered | Shows total power draw per PDU | Standard production |
| Switched | Per-outlet power control (remote on/off) | Remote power cycling |
| Intelligent | Per-outlet monitoring + switching + alerts | Mission-critical |

**Recommendation**: Metered or switched PDUs. Intelligent PDUs are worth the premium for remote power management — being able to power-cycle a server from your desk at 3 AM instead of driving to the datacenter saves hours per incident.

### Power Budget Calculation

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

---

## Cooling

### Hot Aisle / Cold Aisle

```
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

### Cooling Capacity

```
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

---

## Out-of-Band Management

### IPMI / BMC / Redfish

Every enterprise server has a dedicated management processor (BMC — Baseboard Management Controller) that operates independently of the server's OS:

```
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

### Common BMC Operations

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

---

## Cabling

### Structured Cabling Standards

| Cable Type | Speed | Max Distance | Use Case |
|-----------|-------|-------------|----------|
| Cat6 (copper) | 10GbE | 55m | Short runs, management |
| Cat6a (copper) | 10GbE | 100m | In-rack and short between-rack |
| OM4 MMF (fiber) | 100GbE | 100m | Between-rack, between-row |
| OS2 SMF (fiber) | 100GbE+ | 10km+ | Between buildings, to WAN |
| DAC (copper twinax) | 25/100GbE | 5m | Within-rack switch-to-server |

**For Kubernetes clusters**: Use DAC cables for within-rack connections (server to ToR switch) and OM4 fiber for between-rack connections (ToR to spine switch). DAC is cheaper and lower latency for short runs.

```
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

---

## Did You Know?

- **A typical datacenter rack weighs 1,000-2,500 lbs fully loaded.** Many office buildings cannot support this weight — standard office floors are rated for 50-100 lbs per square foot, while a loaded rack exerts 300-500 lbs per square foot. This is why datacenters have reinforced floors.

- **UPS batteries last 3-5 years and are the most common point of failure** in power systems. A UPS that has not had a battery replacement in 4+ years may provide only 30 seconds of backup instead of the rated 10-15 minutes. Test your UPS under load annually.

- **Datacenter fires are extremely rare but devastating.** The OVHcloud Strasbourg fire (March 2021) destroyed an entire datacenter and partially damaged another. 3.6 million websites went offline. The cause: a faulty UPS caught fire, and the building lacked an automatic fire extinguishing system entirely — it was not temporarily disabled, it simply did not exist.

- **The Redfish API is replacing IPMI.** IPMI was designed in 1998 and has known security vulnerabilities (including cleartext password transmission). Redfish uses HTTPS, JSON, and modern authentication. If you are buying new servers, insist on Redfish support.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Single PDU feed | Power loss = server down | Always use A+B redundant feeds |
| BMC on production network | Security risk; BMC has full hardware control | Isolated management VLAN with firewall |
| No cable labeling | Cannot trace cables during incidents | Label both ends of every cable with rack/port |
| Mixing hot/cold aisles | Hot exhaust recirculates to cold intakes | Strict hot/cold aisle discipline |
| Ignoring weight limits | Floor or rack collapses | Check floor rating; distribute weight evenly |
| Default BMC passwords | Anyone on mgmt network can power off your servers | Change all BMC passwords; use certificates where possible |
| No UPS testing | Battery fails when needed | Annual UPS load test; replace batteries at 3-4 years |
| Over-provisioning power | Paying for 20 kW but using 5 kW | Right-size PDU capacity to actual draw + 30% headroom |

---

## Quiz

### Question 1
Your rack has two 30A/208V PDUs (A and B feeds). What is the maximum sustained IT load you should run?

<details>
<summary>Answer</summary>

**Approximately 5 kW sustained.**

Each PDU: 30A × 208V = 6,240W capacity. At 80% derating: 4,992W usable.

With A+B redundancy, the design requirement is that **either feed alone must handle the full load** (N+1 power redundancy). Therefore, your total IT load must not exceed the capacity of a single PDU:

Maximum sustained load = 4,992W ≈ 5 kW

If you need more than 5 kW per rack, upgrade to higher-amperage PDUs (40A or 60A) or distribute the load across two racks.

Common mistake: adding up both PDUs (12.5 kW) and filling to that capacity. If feed A fails, feed B cannot handle the load and the rack goes dark.
</details>

### Question 2
Why should the BMC/IPMI network be on an isolated management VLAN?

<details>
<summary>Answer</summary>

The BMC has **full hardware control**: it can power cycle the server, access the BIOS, mount virtual media, view the console, and even modify firmware. If an attacker reaches the BMC, they can:

1. **Power off all servers** (instant cluster outage)
2. **Boot from a malicious ISO** (compromise the OS before it starts)
3. **Read server console output** (potentially see secrets during boot)
4. **Flash malicious firmware** (persistent compromise that survives OS reinstall)

IPMI also has a history of serious vulnerabilities (CVE-2013-4786: cipher zero bypass, CVE-2019-6260: buffer overflow). Isolating the BMC network with firewall rules that only allow access from a jump host or automation server significantly reduces the attack surface.

Best practice: BMC on a separate VLAN (e.g., 10.0.100.0/24), accessible only from a hardened management jump box. No BMC access from the production network or the internet.
</details>

### Question 3
You need to remotely reinstall the OS on a server. The server is powered on but the OS is unresponsive (kernel panic). What steps do you take using out-of-band management?

<details>
<summary>Answer</summary>

Using the BMC (via Redfish or IPMI):

1. **Verify server state** via BMC console:
   ```bash
   curl -k -u admin:pass https://bmc-ip/redfish/v1/Systems/1 | jq '.PowerState'
   # "On" — server is powered but OS is unresponsive
   ```

2. **Set next boot device to PXE** (for network-based OS install):
   ```bash
   curl -k -u admin:pass -X PATCH https://bmc-ip/redfish/v1/Systems/1 \
     -H "Content-Type: application/json" \
     -d '{"Boot": {"BootSourceOverrideTarget": "Pxe", "BootSourceOverrideEnabled": "Once"}}'
   ```

3. **Force restart the server** (graceful shutdown won't work with kernel panic):
   ```bash
   curl -k -u admin:pass -X POST \
     https://bmc-ip/redfish/v1/Systems/1/Actions/ComputerSystem.Reset \
     -d '{"ResetType": "ForceRestart"}'
   ```

4. **Watch the BMC console** (virtual KVM) to verify PXE boot starts and the OS installer runs.

5. **After OS installation**, the server will boot normally and you can re-join it to the Kubernetes cluster.

This entire process is done remotely — no physical datacenter access needed. This is why BMC access is essential for on-premises operations.
</details>

### Question 4
A server's temperature sensor shows the inlet temperature rising from 22C to 35C over 30 minutes. What might be happening?

<details>
<summary>Answer</summary>

**Possible causes in order of likelihood:**

1. **CRAC/CRAH failure** — The in-row or room cooling unit has stopped working. Check if other servers in the same row/room are also heating up. If yes, this is a cooling unit failure.

2. **Hot aisle containment breach** — A blanking panel is missing or a cable cutout is unsealed, allowing hot exhaust air to recirculate to the cold aisle. Check for physical gaps.

3. **Adjacent rack overload** — A nearby rack has added high-power equipment (GPU servers) that exceeds the cooling zone's capacity.

4. **Raised floor tile displacement** — In raised-floor datacenters, a displaced tile reduces cold air delivery to your row.

**Action sequence:**
1. Check other servers in the row (is it localized or widespread?)
2. Alert the facilities team immediately (this is a physical infrastructure issue)
3. If temperature exceeds 40C: consider gracefully draining Kubernetes pods from affected nodes to prevent thermal throttling
4. At 45C+: servers will thermal-throttle (performance drops 30-50%)
5. At 50C+: servers will thermal-shutdown (protective circuit trips)

**Prevention**: Set up BMC temperature alerts at 30C (warning) and 38C (critical). Monitor with Prometheus using the IPMI exporter.
</details>

---

## Hands-On Exercise: Inventory and Manage a Server

**Task**: Use out-of-band management to inventory and perform basic operations on a server.

> **Note**: This exercise requires access to a server with IPMI/BMC. If you do not have physical hardware, you can practice the Redfish API calls against the DMTF Redfish Mockup Server: `docker run -p 8000:8000 dmtf/redfish-mockup-server`

### Steps

1. **Discover BMC information:**

```bash
# If you have ipmitool installed
ipmitool -I lanplus -H <BMC_IP> -U admin -P password mc info

# Using Redfish
curl -k -u admin:password https://<BMC_IP>/redfish/v1/ | jq '.'
```

2. **Read hardware sensors:**

```bash
# IPMI sensors
ipmitool -I lanplus -H <BMC_IP> -U admin -P password sensor list | grep -E "Temp|Fan|Power"

# Redfish thermal
curl -k -u admin:password \
  https://<BMC_IP>/redfish/v1/Chassis/1/Thermal | jq '.Temperatures[]'
```

3. **Check power consumption:**

```bash
# Redfish power
curl -k -u admin:password \
  https://<BMC_IP>/redfish/v1/Chassis/1/Power | jq '.PowerControl[0].PowerConsumedWatts'
```

4. **Practice power operations** (on a non-production server):

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

### Success Criteria
- [ ] BMC accessible via network
- [ ] Hardware sensors readable (temperature, fan speed, power)
- [ ] Power consumption measured
- [ ] Power cycle performed successfully (non-production only)
- [ ] Redfish API or IPMI tool used to interact with BMC

---

## Next Module

Continue to [Module 2.2: OS Provisioning & PXE Boot](../module-2.2-pxe-provisioning/) to learn how to automatically install operating systems on bare metal servers over the network.
