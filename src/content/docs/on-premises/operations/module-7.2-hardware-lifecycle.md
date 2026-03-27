---
title: "Module 7.2: Hardware Lifecycle & Firmware"
slug: on-premises/operations/module-7.2-hardware-lifecycle
sidebar:
  order: 3
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 7.1: Kubernetes Upgrades on Bare Metal](module-7.1-upgrades/), [Module 2.1: Datacenter Fundamentals](../provisioning/module-2.1-datacenter-fundamentals/)

---

## Why This Module Matters

In February 2024, a healthcare company running a 70-node bare metal Kubernetes cluster received a critical BIOS vulnerability advisory from Dell. The CVE allowed privilege escalation through the BMC interface, and their compliance team gave them 30 days to patch all servers. The infrastructure team's first instinct was to schedule a weekend maintenance window, power down all servers, update BIOS via USB drives, and power them back up. That would have meant 4-8 hours of complete cluster downtime -- unacceptable for a system processing patient data 24/7.

Instead, they built a rolling firmware update pipeline: cordon a node, drain its workloads, use the Redfish API to stage the BIOS update, reboot the server into the firmware update mode, wait for it to come back, verify the new BIOS version via IPMI, uncordon, and move to the next node. The process took 12 days but caused zero downtime. Three servers failed to reboot after the BIOS update due to a known bug with their specific DIMM configuration. Because they were updating one node at a time, these failures were contained. The spare capacity absorbed the missing nodes while the team worked with Dell support to recover them.

In the cloud, you never think about BIOS versions or disk firmware. The cloud provider handles it. On bare metal, hardware lifecycle management is a continuous operational responsibility that directly affects your cluster's security posture, reliability, and performance.

---

## What You'll Learn

- BIOS and firmware update strategies without cluster downtime
- Cordon/drain workflows for hardware maintenance windows
- Disk replacement procedures for running Kubernetes nodes
- Predictive failure detection with SMART monitoring
- Using the Redfish API for out-of-band firmware management
- Building a hardware maintenance calendar

---

## Firmware Update Architecture

```
+---------------------------------------------------------------+
|            FIRMWARE UPDATE PIPELINE (ZERO DOWNTIME)            |
|                                                                |
|  +---------+    +--------+    +----------+    +---------+     |
|  | Cordon  |--->| Drain  |--->| Stage FW |--->| Reboot  |     |
|  | Node    |    | Pods   |    | via      |    | into FW |     |
|  |         |    |        |    | Redfish  |    | update  |     |
|  +---------+    +--------+    +----------+    +---------+     |
|                                                    |           |
|  +---------+    +--------+    +----------+    +----v----+     |
|  | Update  |<---| Verify |<---| Wait for |<---| Server  |     |
|  | CMDB    |    | FW ver |    | node     |    | reboots |     |
|  |         |    | via    |    | Ready    |    | with    |     |
|  |         |    | IPMI   |    |          |    | new FW  |     |
|  +---------+    +--------+    +----------+    +---------+     |
|       |                                                        |
|  +----v----+                                                   |
|  |Uncordon |                                                   |
|  | Node    |                                                   |
|  +---------+                                                   |
+---------------------------------------------------------------+
```

### Types of Firmware to Manage

| Component | Update Method | Reboot Required | Risk Level |
|-----------|--------------|-----------------|------------|
| BIOS/UEFI | Redfish/IPMI, USB, in-band tool | Yes | High |
| BMC/iDRAC/iLO | Redfish API | Usually no | Medium |
| NIC firmware | Vendor tool (ethtool, mlxfwmanager) | Sometimes | Medium |
| Disk firmware | Vendor tool (smartctl, perccli) | Sometimes | High |
| GPU firmware | nvidia-smi | Yes | High |
| RAID controller | Vendor CLI (storcli, perccli) | Yes | High |

---

## Cordon and Drain for Maintenance Windows

### The Maintenance Workflow

```bash
#!/bin/bash
# maintenance-drain.sh — safe node drain for hardware maintenance
set -euo pipefail

NODE="$1"
REASON="${2:-hardware-maintenance}"

echo "=== Starting maintenance drain for ${NODE} ==="
echo "Reason: ${REASON}"
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Step 1: Label the node with maintenance reason
kubectl label node "$NODE" \
  maintenance.kubedojo.io/reason="$REASON" \
  maintenance.kubedojo.io/started="$(date +%s)" \
  --overwrite

# Step 2: Cordon (prevent new pods)
kubectl cordon "$NODE"

# Step 3: Check what needs to be evicted
POD_COUNT=$(kubectl get pods --field-selector spec.nodeName="$NODE" \
  --all-namespaces --no-headers | wc -l)
echo "Pods to evict: ${POD_COUNT}"

# Step 4: Drain with timeout
kubectl drain "$NODE" \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --timeout=600s \
  --grace-period=60

echo "=== Node ${NODE} drained and ready for maintenance ==="
```

### Post-Maintenance Return

```bash
#!/bin/bash
# maintenance-return.sh — return node to service after maintenance
set -euo pipefail

NODE="$1"

echo "=== Returning ${NODE} to service ==="

# Step 1: Verify the node is Ready
STATUS=$(kubectl get node "$NODE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
if [ "$STATUS" != "True" ]; then
  echo "WARN: Node not Ready (status: ${STATUS}). Waiting 60s..."
  sleep 60
  STATUS=$(kubectl get node "$NODE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
  if [ "$STATUS" != "True" ]; then
    echo "FAIL: Node still not Ready. Investigate before uncordoning."
    exit 1
  fi
fi

# Step 2: Verify kubelet version matches cluster
NODE_VERSION=$(kubectl get node "$NODE" -o jsonpath='{.status.nodeInfo.kubeletVersion}')
echo "Node kubelet version: ${NODE_VERSION}"

# Step 3: Uncordon
kubectl uncordon "$NODE"

# Step 4: Remove maintenance labels
kubectl label node "$NODE" \
  maintenance.kubedojo.io/reason- \
  maintenance.kubedojo.io/started-

echo "=== Node ${NODE} returned to service ==="
```

---

## BIOS and Firmware Updates via Redfish

Redfish is the modern replacement for IPMI for out-of-band server management. It provides a RESTful API for firmware updates, power control, and hardware inventory.

### Querying Firmware Inventory

```bash
# Get current firmware versions via Redfish
curl -sk -u admin:password \
  https://bmc-worker-01.internal/redfish/v1/UpdateService/FirmwareInventory \
  | jq '.Members[] | ."@odata.id"'

# Get specific BIOS version
curl -sk -u admin:password \
  https://bmc-worker-01.internal/redfish/v1/Systems/1/Bios \
  | jq '{BiosVersion: .BiosVersion, Model: .Model}'
```

### Staging a BIOS Update

```bash
# Stage firmware via Redfish SimpleUpdate (Dell iDRAC example)
# The BMC pulls the image from an HTTP server — host the firmware file
# on an internal web server accessible from the BMC management network
curl -sk -u admin:password \
  -X POST \
  -H "Content-Type: application/json" \
  https://bmc-worker-01.internal/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate \
  -d '{"ImageURI": "http://internal-web-server/firmware/BIOS_P4GKN_LN_2.19.1.bin",
       "TransferProtocol": "HTTP",
       "@Redfish.OperationApplyTime": "OnReset"}'

# Check update status
curl -sk -u admin:password \
  https://bmc-worker-01.internal/redfish/v1/TaskService/Tasks \
  | jq '.Members'
```

The rolling firmware update script follows the same pattern: for each node, call `maintenance-drain.sh`, stage firmware via Redfish `SimpleUpdate`, trigger a `GracefulRestart` via Redfish, wait for the node to return to `Ready`, verify the new firmware version, and call `maintenance-return.sh`. Add a 5-minute cooldown between nodes to catch issues early.

---

## Disk Replacement Procedures

Disk failures are the most common hardware event in a bare metal cluster. With Ceph or other distributed storage, disk replacement can be non-disruptive -- but the procedure must be followed precisely.

### SMART Monitoring for Predictive Failure

```bash
# Check SMART health on all disks
for DISK in /dev/sd{a..h}; do
  echo "=== ${DISK} ==="
  smartctl -H "$DISK" | grep "SMART overall-health"
  smartctl -A "$DISK" | grep -E "(Reallocated_Sector|Current_Pending|Offline_Uncorrectable)"
done
```

### Key SMART Attributes to Monitor

```
+---------------------------------------------------------------+
|            SMART ATTRIBUTES FOR PREDICTIVE FAILURE             |
|                                                                |
|  Attribute                   Warning Threshold  Action         |
|  ------------------------------------------------------------ |
|  Reallocated Sector Count    > 0                Monitor        |
|  Reallocated Sector Count    > 100              Replace soon   |
|  Current Pending Sectors     > 0                Investigate    |
|  Offline Uncorrectable       > 0                Replace soon   |
|  UDMA CRC Error Count        Rising             Check cable    |
|  Wear Leveling (SSD)         < 10%              Plan replace   |
|  Media Wearout (NVMe)        < 10%              Plan replace   |
|                                                                |
|  For NVMe drives, use:                                         |
|  nvme smart-log /dev/nvme0n1                                   |
|  Key field: percentage_used (replace at > 90%)                 |
+---------------------------------------------------------------+
```

### Disk Replacement Workflow (Ceph OSD)

```bash
# Step 1: Identify the failing disk
ceph osd tree  # find which OSD is on the failing disk

# Step 2: Set OSD noout to prevent rebalancing during replacement
ceph osd set noout

# Step 3: Mark the OSD down and out
ceph osd down osd.5
ceph osd out osd.5

# Step 4: Remove the OSD from the cluster
# (purge removes the OSD from CRUSH, deletes its auth keys, and removes it from the map)
ceph osd purge osd.5 --yes-i-really-mean-it

# Step 5: Physically replace the disk (or wait for datacenter hands)

# Step 6: Prepare the new disk
ceph-volume lvm create --data /dev/sdc

# Step 7: Unset noout to allow rebalancing
ceph osd unset noout

# Step 8: Monitor rebalancing
ceph -w  # watch rebalancing progress
```

---

## Building a Hardware Maintenance Calendar

```
+---------------------------------------------------------------+
|         ANNUAL HARDWARE MAINTENANCE CALENDAR                   |
|                                                                |
|  Monthly:                                                      |
|  - SMART health check on all disks (automated)                 |
|  - Review BMC event logs for warnings                          |
|  - Check PSU redundancy status                                 |
|                                                                |
|  Quarterly:                                                    |
|  - Apply critical firmware updates (BIOS, BMC)                 |
|  - Review NIC firmware versions against vendor advisories      |
|  - Test IPMI/Redfish connectivity to all BMCs                  |
|  - Verify backup power (UPS battery tests)                     |
|                                                                |
|  Annually:                                                     |
|  - Full hardware inventory audit                               |
|  - Warranty status review (identify expiring warranties)       |
|  - Thermal audit (clean dust filters, check airflow)           |
|  - Cable audit (reseat suspect connections)                    |
|  - Evaluate hardware refresh candidates                        |
|                                                                |
|  As-needed:                                                    |
|  - Emergency firmware patches (CVEs)                           |
|  - Disk replacements (SMART alerts)                            |
|  - Memory DIMM replacements (ECC error alerts)                 |
|  - PSU replacements (redundancy lost alerts)                   |
+---------------------------------------------------------------+
```

---

## Prometheus Alerts for Hardware Health

```yaml
# hardware-alerts.yaml — Prometheus alerting rules
groups:
  - name: hardware-health
    rules:
      - alert: DiskSmartPrefailure
        expr: smartmon_device_smart_healthy == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk SMART prefailure on {{ $labels.instance }}"
          description: "Disk {{ $labels.disk }} reports SMART health check failed."
          runbook: "Follow disk replacement procedure in ops runbook."

      - alert: DiskWearoutHigh
        expr: smartmon_wear_leveling_count_value < 20
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSD wear leveling low on {{ $labels.instance }}"
          description: "Disk {{ $labels.disk }} has {{ $value }}% life remaining."

      - alert: MemoryECCErrors
        expr: node_edac_correctable_errors_total > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "ECC memory errors on {{ $labels.instance }}"
          description: "{{ $value }} correctable ECC errors detected. DIMM may be failing."

      - alert: PSURedundancyLost
        expr: ipmi_sensor_state{name=~".*PSU.*",state="critical"} == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PSU redundancy lost on {{ $labels.instance }}"
          description: "Server is running on a single PSU. Replace failed PSU immediately."
```

---

## Did You Know?

- **Dell ships approximately 50 BIOS updates per server model over its 5-year lifecycle.** Most are cumulative, so you do not need to apply every one -- but skipping more than 2-3 versions increases the risk of hitting a bug that was fixed in an intermediate release.

- **Redfish was developed by the DMTF (Distributed Management Task Force) starting in 2014** as a replacement for IPMI, which was designed in 1998. While IPMI uses a binary protocol on port 623, Redfish uses HTTPS with JSON payloads. Most servers shipped after 2018 support both, but IPMI is being deprecated by major vendors.

- **NVMe drives do not use SMART in the traditional sense.** They use the NVMe health log (`nvme smart-log`), which reports `percentage_used` -- a value that can exceed 100% because it measures total bytes written against the vendor's endurance rating. A drive at 150% used may still work fine but is operating beyond its warranty.

- **The "bathtub curve" describes hardware failure rates**: high failure rate in the first 90 days (infant mortality), low and stable for years (useful life), then rising failure rate as components age (wear-out). Plan your spare inventory accordingly -- you need more spares in the first quarter after a hardware refresh and in years 4-5 of the lifecycle.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Updating BIOS on all nodes simultaneously | Cluster-wide outage if update fails | Rolling update, one node at a time |
| No SMART monitoring | Disk failures are surprises | Deploy smartmon_exporter, alert on prefailure |
| Ignoring ECC memory errors | Correctable errors precede uncorrectable ones | Alert on correctable errors, replace DIMMs proactively |
| Skipping BMC firmware updates | BMC vulnerabilities allow remote compromise | Include BMC in firmware update cycle |
| No spare disk inventory | Hours/days waiting for replacement parts | Keep 5-10% spare disks on-site |
| Updating NIC firmware without testing | Network driver compatibility issues | Test NIC firmware in staging first |
| Not documenting which firmware is on which node | Cannot audit compliance, cannot reproduce issues | Maintain CMDB with firmware versions |
| Forgetting to unset Ceph noout after maintenance | Ceph stops rebalancing indefinitely | Script the unset into maintenance-return workflow |

---

## Quiz

### Question 1
You need to update the BIOS on 40 bare metal Kubernetes nodes to patch a critical CVE. Your compliance deadline is 14 days. Each BIOS update requires a reboot that takes approximately 8 minutes. How do you plan this?

<details>
<summary>Answer</summary>

**Plan: Rolling BIOS update, 4 nodes per day, completing in 10 working days.**

**Calculation:**
- Per node: drain (5 min) + stage firmware (2 min) + reboot (8 min) + verify (5 min) + uncordon (1 min) = ~21 min
- With a 5-minute buffer between nodes: ~26 min per node
- 4 nodes per day = ~2 hours of active maintenance per day
- 40 nodes / 4 per day = 10 days (within 14-day deadline)

**Why 4 per day, not more?**
- Maintains spare capacity (90% of cluster remains available)
- Allows monitoring between updates to catch issues early
- If a node fails to return, you have time to investigate before the next batch

**Procedure:**
1. Stage firmware on all 40 BMCs via Redfish (can be done in parallel, no reboot needed)
2. Each day: cordon, drain, reboot (triggers staged update), wait for Ready, verify BIOS version, uncordon
3. Track progress in a spreadsheet: node, old version, new version, timestamp, status

**Risk mitigation:**
- Keep 2 buffer days (days 11-12) for failed updates
- Have Dell/HPE support case pre-opened in case of boot failures
- Test on 1 node from each hardware generation on day 1
</details>

### Question 2
A SMART check on `/dev/sdb` shows `Reallocated_Sector_Count = 47` and `Current_Pending_Sector = 3`. The disk is part of a Ceph OSD. What do you do?

<details>
<summary>Answer</summary>

**This disk is showing signs of imminent failure and should be replaced proactively.**

**Interpretation:**
- `Reallocated_Sector_Count = 47`: The drive has already remapped 47 bad sectors to spare sectors. This is not immediately fatal but indicates the media is degrading.
- `Current_Pending_Sector = 3`: Three sectors have pending read errors that the drive cannot resolve. These will either be reallocated (if a write succeeds) or become `Offline_Uncorrectable` (data loss).

**Action plan:**
1. **Set Ceph noout** to prevent unnecessary rebalancing:
   ```bash
   ceph osd set noout
   ```
2. **Mark the OSD out** to begin data migration away from this disk:
   ```bash
   ceph osd out osd.X
   ```
3. **Wait for data to migrate** (watch `ceph -w` until all PGs are active+clean)
4. **Purge the OSD**:
   ```bash
   ceph osd purge osd.X --yes-i-really-mean-it
   ```
5. **Replace the physical disk** (schedule datacenter hands if remote)
6. **Create new OSD on replacement disk**:
   ```bash
   ceph-volume lvm create --data /dev/sdb
   ```
7. **Unset noout**:
   ```bash
   ceph osd unset noout
   ```

**Do not wait** for the disk to fail completely. With `Current_Pending_Sector > 0`, the risk of data unavailability increases with each day. Ceph's replication protects you, but only if you act before multiple disks fail.
</details>

### Question 3
You are managing firmware updates for a mixed fleet: 20 Dell R640s, 15 Dell R740s, and 10 HPE DL380 Gen10s. Each vendor has different Redfish API endpoints. How do you handle this?

<details>
<summary>Answer</summary>

**Build an abstraction layer that maps vendor-specific APIs to a common interface.**

**Approach:**
1. **Create a hardware inventory database** (CMDB) with:
   - Hostname, BMC IP, vendor, model, current firmware versions
   - Redfish API base URL and credentials (from a secrets manager)

2. **Write vendor-specific adapters:**
   ```bash
   # Dell iDRAC Redfish endpoint for BIOS update
   POST /redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate

   # HPE iLO Redfish endpoint for BIOS update
   POST /redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate
   # (Same standard endpoint, but authentication and image staging differ)
   ```

3. **Use a configuration file per vendor:**
   ```yaml
   vendors:
     dell:
       bios_uri: /redfish/v1/Systems/System.Embedded.1/Bios
       update_uri: /redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate
       auth_type: basic
     hpe:
       bios_uri: /redfish/v1/Systems/1/Bios
       update_uri: /redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate
       auth_type: session
   ```

4. **Alternatively, use existing tools:**
   - **Dell**: `racadm` CLI or Dell OpenManage
   - **HPE**: `ilorest` CLI or HPE OneView
   - **Multi-vendor**: `sushy-tools` (OpenStack's Redfish library) or Ansible modules (`community.general.redfish_*`)

5. **Test each vendor's update path independently** before running a mixed-fleet rolling update.

The Redfish standard (DMTF) aims for vendor interoperability, but implementations diverge on authentication, image staging, and task tracking. Always test with actual hardware.
</details>

### Question 4
After a BIOS update, a server fails to boot and sits at a blank screen. The BMC (iDRAC/iLO) is still reachable. What are your recovery options?

<details>
<summary>Answer</summary>

**Recovery options, in order of preference:**

1. **Roll back BIOS via BMC:**
   ```bash
   # Dell iDRAC: restore previous BIOS version
   curl -sk -u admin:password \
     -X POST \
     "https://bmc-addr/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Oem/DellManager.BIOSRollback"

   # HPE iLO: BIOS has a backup ROM, boot from it
   # Use iLO virtual console to select "Boot from Backup ROM"
   ```

2. **Use BMC virtual console + virtual media:**
   - Mount a recovery ISO via iDRAC/iLO virtual media
   - Boot from the ISO
   - Flash the previous BIOS version from within the recovery environment

3. **Reset BIOS to factory defaults:**
   ```bash
   # Via Redfish
   curl -sk -u admin:password \
     -X POST \
     "https://bmc-addr/redfish/v1/Systems/1/Bios/Actions/Bios.ResetBios"
   ```
   This loses custom BIOS settings (boot order, SR-IOV, virtualization) but should make the server bootable.

4. **Physical intervention:**
   - Clear CMOS via jumper on the motherboard
   - Requires datacenter hands or physical access

**Impact on Kubernetes:**
- The node was already drained before the BIOS update (if you followed the procedure)
- Workloads are running on other nodes
- No data loss (no pods were running on this node during the update)
- You have time to recover without pressure

**Prevention:** Always test BIOS updates on one node from each hardware generation before rolling to the fleet.
</details>

---

## Hands-On Exercise: Build a Hardware Health Dashboard

**Task**: Deploy SMART monitoring and create Prometheus alerts for disk health.

### Setup

```bash
# Deploy smartmon_exporter (example using node_exporter textfile collector)
cat <<'SMARTEOF' > /tmp/smartmon-collector.sh
#!/bin/bash
# Collects SMART metrics for node_exporter textfile collector
OUTPUT="/var/lib/node_exporter/textfile/smartmon.prom"

for DISK in /dev/sd{a..z}; do
  [ -b "$DISK" ] || continue
  DEVICE=$(basename "$DISK")

  HEALTH=$(smartctl -H "$DISK" 2>/dev/null | grep -c "PASSED" || echo 0)
  echo "smartmon_device_smart_healthy{disk=\"${DEVICE}\"} ${HEALTH}"

  REALLOC=$(smartctl -A "$DISK" 2>/dev/null | awk '/Reallocated_Sector/ {print $10}' || echo 0)
  echo "smartmon_reallocated_sector_count{disk=\"${DEVICE}\"} ${REALLOC:-0}"

  PENDING=$(smartctl -A "$DISK" 2>/dev/null | awk '/Current_Pending/ {print $10}' || echo 0)
  echo "smartmon_current_pending_sector{disk=\"${DEVICE}\"} ${PENDING:-0}"

  # SSD wear leveling (Wear_Leveling_Count or Media_Wearout_Indicator)
  WEAR=$(smartctl -A "$DISK" 2>/dev/null | awk '/Wear_Leveling_Count|Media_Wearout_Indicator/ {print $4}' || echo -1)
  [ "$WEAR" != "-1" ] && echo "smartmon_wear_leveling_count_value{disk=\"${DEVICE}\"} ${WEAR}"
done > "$OUTPUT"
SMARTEOF
chmod +x /tmp/smartmon-collector.sh
```

### Steps

1. **Review the collector script** and understand which SMART attributes it exports
2. **Create Prometheus alerting rules** for disk prefailure conditions
3. **Define escalation thresholds:**
   - Warning: Reallocated sectors > 0
   - Critical: Current pending sectors > 0 or SMART health check failed
4. **Plan the disk replacement workflow** as a runbook document

### Success Criteria

- [ ] Understand which SMART attributes indicate imminent failure
- [ ] Can explain the difference between reallocated, pending, and uncorrectable sectors
- [ ] Know the Ceph OSD replacement procedure (noout, out, purge, replace, create)
- [ ] Can use Redfish API to query firmware versions
- [ ] Understand the rolling firmware update workflow (drain, update, reboot, verify, uncordon)

---

## Next Module

Continue to [Module 7.3: Node Failure & Auto-Remediation](../operations/module-7.3-node-remediation/) to learn how to detect and automatically recover from node failures using Machine Health Checks and node problem detector.
