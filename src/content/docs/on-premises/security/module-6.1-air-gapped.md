---
title: "Module 6.1: Physical Security & Air-Gapped Environments"
slug: on-premises/security/module-6.1-air-gapped
sidebar:
  order: 2
---

> **Complexity**: `[ADVANCED]` | Time: 60 minutes
>
> **Prerequisites**: [Planning & Economics](../planning/), [Bare Metal Provisioning](../provisioning/), [CKS](../../k8s/cks/)

---

## Why This Module Matters

A defense contractor running classified workloads on Kubernetes learned the hardest possible lesson in 2022. Their "air-gapped" cluster was not truly disconnected -- a junior engineer had plugged in a USB WiFi adapter to download a container image he needed for testing. The adapter associated with a nearby guest network. An automated scanner on that guest network found the adapter within 40 minutes and began probing. The incident triggered a full security audit, a 90-day remediation, and $2.3 million in costs -- not from a breach (there was none) but from the investigation, re-accreditation, and mandatory hardware replacement.

The real cost was organizational: the program lost its Authority to Operate (ATO) for 4 months. Every workload on that cluster was frozen. Downstream teams lost access to CI/CD pipelines. The root cause was not malice -- it was a process failure. Nobody had documented how to get new container images into the air-gapped environment, so engineers improvised. The contractor then spent 6 months building a proper image pipeline with Harbor, a transfer workstation, and an approval workflow. What should have been designed on day one became a $3 million afterthought.

> **The Submarine Analogy**
>
> An air-gapped cluster is like a submarine. It must carry everything it needs before diving. Resupply requires surfacing at a controlled point, transferring cargo through a single hatch, and inspecting every crate. If someone drills a hole in the hull "just for a quick connection," the entire vessel is compromised. Your image pipeline is that supply hatch -- design it before you dive.

---

## What You'll Learn

- Physical security controls for datacenters housing Kubernetes infrastructure
- How to design and operate truly disconnected (air-gapped) Kubernetes clusters
- Setting up Harbor as a local container registry with image mirroring
- Sneakernet workflows for transferring images and updates
- Air-gapped GitOps with Flux using local Git servers
- Common failures in air-gapped environments and how to prevent them

---

## Datacenter Physical Controls

Physical security is the foundation. If someone can touch the hardware, every software control is moot.

### The Seven Layers of Physical Security

```
┌──────────────────────────────────────────────────────────────┐
│                    PHYSICAL SECURITY LAYERS                  │
│                                                              │
│  Layer 7: Port-level control (USB disable, IPMI isolation)   │
│  Layer 6: Rack-level locks (keyed, electronic, biometric)    │
│  Layer 5: Cage/zone (locked cage, separate HVAC zone)        │
│  Layer 4: Server room (mantrap, badge + biometric)           │
│  Layer 3: Building (security desk, visitor log)              │
│  Layer 2: Perimeter (fence, bollards, cameras)               │
│  Layer 1: Site selection (flood zone, flight path, distance) │
│                                                              │
│  An attacker must defeat ALL layers to reach hardware.       │
│  Most organizations stop at Layer 4 and skip Layers 6-7.    │
└──────────────────────────────────────────────────────────────┘
```

### Port Control on Bare Metal Nodes

Disable unused physical ports at the BIOS and OS level:

```bash
# Disable USB storage at the kernel level (Linux)
echo "blacklist usb-storage" > /etc/modprobe.d/disable-usb-storage.conf
echo "blacklist uas" >> /etc/modprobe.d/disable-usb-storage.conf
update-initramfs -u

# Verify USB storage is blocked
modprobe usb-storage 2>&1  # Should fail

# Disable Thunderbolt/DMA attack vectors
echo "blacklist thunderbolt" > /etc/modprobe.d/disable-thunderbolt.conf

# Lock down IPMI/BMC to management VLAN only
# (Done at network switch level -- restrict BMC ports to mgmt VLAN)
ipmitool lan set 1 ipsrc static
ipmitool lan set 1 ipaddr 10.99.0.11    # Management VLAN
ipmitool lan set 1 netmask 255.255.255.0
```

### BIOS/UEFI Hardening

```
BIOS Settings for Air-Gapped Kubernetes Nodes:
─────────────────────────────────────────────
1. Set BIOS admin password           -- prevent boot order changes
2. Disable USB boot                  -- prevent booting from removable media
3. Disable PXE boot (after install)  -- prevent network reimaging
4. Enable Secure Boot                -- only signed bootloaders
5. Disable serial/COM ports          -- no console access from outside
6. Set boot order: disk only         -- no fallback to network/USB
7. Enable TPM 2.0                    -- measured boot (see Module 6.2)
8. Disable AMT/Intel ME if possible  -- reduce remote management surface
```

---

## Air-Gapped Kubernetes Architecture

A truly air-gapped cluster has zero network connectivity to the internet or any untrusted network. All software enters through a controlled transfer process.

```
┌─────────────────────────────────────────────────────────────────┐
│                   AIR-GAPPED ARCHITECTURE                       │
│                                                                 │
│  CONNECTED SIDE              GAP              DISCONNECTED SIDE │
│  ─────────────              ─────             ──────────────── │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │ Internet     │   │ Transfer     │   │ Air-Gapped       │   │
│  │ Mirror       │──>│ Workstation  │──>│ K8s Cluster      │   │
│  │ Station      │   │ (diode/USB)  │   │                  │   │
│  └──────────────┘   └──────────────┘   │ ┌──────────────┐ │   │
│                                         │ │ Harbor       │ │   │
│  Pull images        Scan, approve,     │ │ (registry)   │ │   │
│  from Docker Hub,   burn to media      │ └──────────────┘ │   │
│  Quay, GitHub        or push via       │ ┌──────────────┐ │   │
│                      data diode        │ │ Gitea/GitLab │ │   │
│  ┌──────────────┐                      │ │ (local Git)  │ │   │
│  │ Vendor       │                      │ └──────────────┘ │   │
│  │ Packages     │                      │ ┌──────────────┐ │   │
│  │ (RPM/DEB)    │                      │ │ Flux         │ │   │
│  └──────────────┘                      │ │ (GitOps)     │ │   │
│                                         │ └──────────────┘ │   │
│                                         └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Transfer Methods

| Method | Bandwidth | Security | Use Case |
|--------|-----------|----------|----------|
| USB/removable media (sneakernet) | Low (hours) | High (physical control) | Classified environments, < 50 images |
| Data diode (hardware) | Medium | Very high (physics-enforced one-way) | Defense, nuclear, critical infrastructure |
| Cross-domain solution (CDS) | Medium-High | High (certified product) | Government, multi-level security |
| Scheduled batch transfer | High | Medium (network-based, time-limited) | Financial, healthcare (not true air-gap) |

---

## Setting Up Harbor as a Local Registry

Harbor is the standard choice for air-gapped container registries. It provides image scanning, replication, RBAC, and content trust.

### Install Harbor (Air-Gapped Side)

```bash
# On the connected side: download Harbor installer
curl -LO https://github.com/goharbor/harbor/releases/download/v2.11.0/harbor-offline-installer-v2.11.0.tgz
curl -LO https://github.com/goharbor/harbor/releases/download/v2.11.0/harbor-offline-installer-v2.11.0.tgz.asc

# Verify signature
gpg --verify harbor-offline-installer-v2.11.0.tgz.asc

# Transfer to air-gapped side via approved method
# ... (sneakernet, data diode, etc.)

# On the air-gapped side: install Harbor
tar xzf harbor-offline-installer-v2.11.0.tgz
cd harbor

# Configure harbor.yml
cat > harbor.yml <<'HARBOREOF'
hostname: registry.internal.corp
http:
  port: 80
https:
  port: 443
  certificate: /etc/harbor/certs/registry.crt
  private_key: /etc/harbor/certs/registry.key
harbor_admin_password: <change-me>
database:
  password: <change-me>
  max_idle_conns: 50
  max_open_conns: 1000
data_volume: /data/harbor
trivy:
  ignore_unfixed: false
  skip_update: true          # Critical: no internet for DB updates
  offline_scan: true         # Use bundled vulnerability DB
HARBOREOF

# Install with Trivy (offline mode)
./install.sh --with-trivy
```

### Mirror Images for Transfer

On the connected side, use `skopeo` or `crane` to create portable image bundles:

```bash
# Create a manifest of required images
cat > image-list.txt <<'EOF'
registry.k8s.io/kube-apiserver:v1.31.4
registry.k8s.io/kube-controller-manager:v1.31.4
registry.k8s.io/kube-scheduler:v1.31.4
registry.k8s.io/kube-proxy:v1.31.4
registry.k8s.io/etcd:3.5.16-0
registry.k8s.io/coredns/coredns:v1.12.0
registry.k8s.io/pause:3.10
quay.io/cilium/cilium:v1.16.5
ghcr.io/fluxcd/flux-cli:v2.4.0
ghcr.io/fluxcd/source-controller:v1.4.1
ghcr.io/fluxcd/kustomize-controller:v1.4.0
goharbor/harbor-core:v2.11.0
EOF

# Mirror all images to a local directory
mkdir -p /transfer/images
while IFS= read -r image; do
  # Create directory-safe name
  dir_name=$(echo "$image" | tr '/:' '_')
  skopeo copy \
    "docker://${image}" \
    "oci-archive:/transfer/images/${dir_name}.tar"
done < image-list.txt

# Calculate checksums for integrity verification
cd /transfer/images
sha256sum *.tar > SHA256SUMS

# Write to approved media
# (Encrypted USB, write-once optical media, etc.)
```

### Import Images on the Air-Gapped Side

```bash
# Verify checksums after transfer
cd /transfer/images
sha256sum -c SHA256SUMS || { echo "INTEGRITY CHECK FAILED"; exit 1; }

# Push each image to Harbor
while IFS= read -r image; do
  dir_name=$(echo "$image" | tr '/:' '_')
  # Retag for local registry
  local_image="registry.internal.corp/${image#*/}"
  skopeo copy \
    "oci-archive:/transfer/images/${dir_name}.tar" \
    "docker://${local_image}" \
    --dest-tls-verify=true \
    --dest-creds admin:<harbor-password>
done < image-list.txt

echo "Import complete. Verify in Harbor UI: https://registry.internal.corp"
```

---

## Sneakernet Update Workflow

Updates to an air-gapped cluster require a disciplined process. This is the most failure-prone part of air-gapped operations.

```
┌─────────────────────────────────────────────────────────────────┐
│               SNEAKERNET UPDATE WORKFLOW                         │
│                                                                 │
│   1. PREPARE (connected side)                                   │
│      ├── Pull new container images                              │
│      ├── Download OS packages (RPM/DEB)                         │
│      ├── Pull Helm charts / Flux manifests                      │
│      ├── Update Trivy vulnerability DB                          │
│      └── Generate SHA256 checksums                              │
│                                                                 │
│   2. REVIEW (approval gate)                                     │
│      ├── Security team reviews image list                       │
│      ├── Change advisory board approves transfer                │
│      └── Two-person integrity rule for media handling           │
│                                                                 │
│   3. TRANSFER (physical movement)                               │
│      ├── Write to encrypted removable media                     │
│      ├── Transport via approved courier/method                  │
│      └── Log chain of custody                                   │
│                                                                 │
│   4. IMPORT (air-gapped side)                                   │
│      ├── Verify checksums on arrival                            │
│      ├── Scan all images with Trivy (offline DB)                │
│      ├── Push to Harbor                                         │
│      └── Update local Git repo with new manifests               │
│                                                                 │
│   5. DEPLOY (via air-gapped GitOps)                             │
│      ├── Flux detects changes in local Gitea                    │
│      ├── Reconciles cluster to desired state                    │
│      └── Verify rollout, run smoke tests                        │
└─────────────────────────────────────────────────────────────────┘
```

### Automating the Connected Side

```bash
#!/bin/bash
# weekly-mirror.sh -- Run on connected mirror station
set -euo pipefail
TRANSFER_DIR="/transfer/weekly-$(date +%Y%m%d)"
mkdir -p "${TRANSFER_DIR}"/{images,charts,os-packages,trivy-db}

# 1. Mirror container images from image-list.txt
while IFS= read -r image; do
  dir_name=$(echo "$image" | tr '/:' '_')
  skopeo copy "docker://${image}" \
    "oci-archive:${TRANSFER_DIR}/images/${dir_name}.tar" --retry-times 3
done < /etc/mirror/image-list.txt

# 2. Mirror Helm charts
helm pull cilium/cilium --version 1.16.5 -d "${TRANSFER_DIR}/charts/"

# 3. Download OS packages
dnf download --resolve --destdir="${TRANSFER_DIR}/os-packages/" \
  kernel container-selinux cri-o kubernetes-cni

# 4. Download Trivy offline DB
oras pull ghcr.io/aquasecurity/trivy-db:2 -o "${TRANSFER_DIR}/trivy-db/"

# 5. Generate checksums and sign
find "${TRANSFER_DIR}" -type f \( -name '*.tar' -o -name '*.tgz' -o -name '*.rpm' \) \
  | sort > "${TRANSFER_DIR}/MANIFEST.txt"
cd "${TRANSFER_DIR}" && sha256sum $(cat MANIFEST.txt) > SHA256SUMS
gpg --detach-sign --armor SHA256SUMS
```

---

## Air-Gapped GitOps with Flux

GitOps in an air-gapped environment requires a local Git server (Gitea or GitLab) instead of GitHub.

### Set Up Gitea (Local Git Server)

Deploy Gitea as a single-replica Deployment in the `gitea` namespace. Use the image from Harbor (`registry.internal.corp/gitea/gitea:1.22.4`), expose ports 3000 (HTTP) and 22 (SSH), and mount a PVC for persistent storage. Create a ClusterIP Service for internal access.

```bash
kubectl create namespace gitea
# Deploy Gitea (Deployment + Service + PVC)
# Image: registry.internal.corp/gitea/gitea:1.22.4
# Ports: 3000 (HTTP), 22 (SSH)
# Storage: PVC mounted at /data
```

### Configure Flux for Air-Gapped Operation

```bash
# Bootstrap Flux pointing to local Gitea
# (Flux images must already be in Harbor)
flux bootstrap git \
  --url=http://gitea.gitea.svc:3000/platform/cluster-config.git \
  --branch=main \
  --path=clusters/production \
  --components-extra=image-reflector-controller,image-automation-controller \
  --registry=registry.internal.corp/fluxcd

# Configure Flux to use Harbor for all image pulls
cat > clusters/production/registry-mirror.yaml <<'EOF'
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: cilium-chart
  namespace: flux-system
spec:
  interval: 10m
  url: oci://registry.internal.corp/charts/cilium
  ref:
    tag: "1.16.5"
EOF
```

### Update Workflow

When new manifests arrive via sneakernet:

```bash
# On the transfer workstation, push updated manifests to Gitea
cd /transfer/manifests/cluster-config
git remote add local http://gitea.internal.corp:3000/platform/cluster-config.git
git push local main

# Flux will detect the change and reconcile automatically
# Monitor the reconciliation
flux get kustomizations --watch
```

---

## Updating Trivy's Vulnerability Database Offline

Trivy cannot fetch vulnerability data in an air-gapped environment. Include the Trivy DB in every weekly transfer bundle: download it on the connected side with `oras pull ghcr.io/aquasecurity/trivy-db:2`, transfer it, then copy to Harbor's Trivy data directory and restart the Trivy container. Verify the DB freshness via Harbor's system info API.

---

## Did You Know?

- **The US Nuclear Regulatory Commission requires a hardware data diode** (not a software firewall) for any network carrying safety system data. A data diode is a fiber optic link with the receive fiber physically cut on one side -- making reverse communication a physics impossibility, not a software configuration.

- **Kubernetes v1.24 removed dockershim**, which was a problem for many air-gapped environments that had built their image pipelines around `docker save/docker load`. The migration to containerd required updating transfer scripts to use `ctr` or `skopeo` instead.

- **Harbor's "robot accounts"** were designed specifically for automated image mirroring in air-gapped environments. Unlike user accounts, robot accounts have no password expiry and can be scoped to specific repositories -- perfect for import scripts.

- **The largest known air-gapped Kubernetes deployment** is believed to be in the US Department of Defense, running Platform One (a CNCF-based DevSecOps platform) across multiple classification levels. Each security domain has its own independent cluster with no cross-domain container image sharing.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| USB ports left enabled | DMA attacks, unauthorized data transfer | Disable USB storage in kernel modules and BIOS |
| No image signature verification | Tampered images could enter the cluster | Use Cosign with a local key server, verify on import |
| Stale vulnerability database | Trivy reports no CVEs (false sense of security) | Transfer Trivy DB weekly alongside images |
| Single-person transfer process | No accountability, higher insider threat risk | Two-person integrity rule for all media handling |
| No manifest of expected images | Cannot detect if images were added or removed | Generate and sign image manifests on connected side |
| IPMI/BMC on production network | Remote management bypass of air gap | Isolate BMC on dedicated management VLAN |
| Forgetting DNS in air-gapped cluster | CoreDNS cannot resolve external names | Configure internal DNS with all needed records |
| No process for emergency patches | Critical CVE with no fast path to deploy fix | Pre-approve emergency transfer process in runbook |

---

## Quiz

### Question 1
Your air-gapped cluster runs Harbor for container images. A critical CVE is published affecting your base OS image. Walk through the steps to patch all affected workloads.

<details>
<summary>Answer</summary>

**Step-by-step patching workflow for air-gapped clusters:**

1. **Connected side**: Pull the patched base image from the upstream registry. Verify the CVE fix by checking the image's changelog or scanning with Trivy.

2. **Rebuild**: If you maintain custom images built on this base, rebuild them with the patched base. Tag with a new version (never overwrite existing tags).

3. **Bundle**: Use `skopeo copy` to export the patched images to OCI archives. Generate SHA256 checksums and sign with GPG.

4. **Approve**: Submit the transfer request to the change advisory board. For critical CVEs, use the pre-approved emergency process.

5. **Transfer**: Write to encrypted removable media with two-person integrity. Transport to the air-gapped side.

6. **Import**: Verify checksums, scan with Trivy (offline DB), push to Harbor.

7. **Update manifests**: Update image tags in the Git repository hosted on Gitea. Push to the local Git server.

8. **Deploy**: Flux detects the manifest change and rolls out updated deployments. Monitor with `kubectl rollout status`.

9. **Verify**: Confirm all pods are running the patched image: `kubectl get pods -o jsonpath='{.items[*].spec.containers[*].image}'`.

The entire process typically takes 4-8 hours for a critical CVE in a well-run air-gapped environment.
</details>

### Question 2
What is the difference between a data diode and a firewall, and why do classified environments require diodes?

<details>
<summary>Answer</summary>

**A firewall is a software/hardware device that filters traffic based on rules.** It can be misconfigured, bypassed by exploits, or disabled by an administrator. A firewall allows bidirectional communication and relies on correct rule configuration to block unwanted traffic.

**A data diode is a hardware device that physically enforces one-way data flow.** Typically implemented with fiber optics where the receive fiber on one side is physically absent or cut. Data can flow from the low-security side to the high-security side (or vice versa, depending on architecture) but never in the reverse direction. No software exploit can overcome a missing physical fiber.

**Why classified environments require diodes:**

1. **Assurance level**: A firewall rule can be changed by anyone with admin access. A data diode requires physical hardware modification to reverse.

2. **Certification**: Government security frameworks (e.g., NIAP Common Criteria) certify data diodes to higher assurance levels than firewalls.

3. **Insider threat**: A compromised admin can reconfigure a firewall. They cannot make data flow backward through a physically one-way connection.

4. **Audit simplicity**: Proving "no data can flow out" is trivial with a diode (physics) but complex with a firewall (rule review, log analysis, penetration testing).
</details>

### Question 3
You need to add a new application to your air-gapped cluster that requires 15 container images not currently in Harbor. Describe your process.

<details>
<summary>Answer</summary>

**Process for introducing new images to an air-gapped cluster:**

1. **Document**: Create an image manifest listing all 15 images with exact tags. Include a justification for each image (what component needs it).

2. **Security review**: Submit the image list to the security team. They review each image for:
   - Known vulnerabilities (scan with Trivy on connected side)
   - Base image provenance (is it from a trusted publisher?)
   - License compliance (some images have restrictive licenses)

3. **Pull and scan**: On the connected mirror station, pull all 15 images. Run Trivy scans. If critical CVEs are found, work with the application team to find patched versions.

4. **Export**: Use `skopeo copy` to create OCI archives for each image. Generate SHA256 checksums and sign the checksum file with GPG.

5. **Approve transfer**: Submit to the change advisory board with scan results and signed manifest.

6. **Transfer and import**: Write to encrypted media (two-person integrity). On the air-gapped side, verify checksums, scan with Trivy, push to Harbor. Create a Harbor project if needed.

7. **Update configs**: Ensure containerd mirror configuration redirects upstream registries to `registry.internal.corp`. Add images to `/etc/mirror/image-list.txt` for future weekly transfers.
</details>

### Question 4
Why is it insufficient to "just block outbound traffic with a firewall" instead of a true air gap?

<details>
<summary>Answer</summary>

**A firewall-based "air gap" has several failure modes that a true air gap does not:**

1. **Misconfiguration risk**: A single incorrect rule (e.g., `allow any any` added during troubleshooting and never removed) breaks the entire isolation. Studies show that 95% of firewall breaches are due to misconfiguration, not exploit.

2. **Bidirectional path exists**: Even if outbound is blocked, the physical network connection still exists. An attacker inside the network could potentially exploit the firewall itself (firmware vulnerabilities, management interface exploits) to open a path.

3. **DNS and timing channels**: Sophisticated attackers can exfiltrate data through DNS query patterns, ICMP timing, or even TCP sequence number modulation -- traffic that may pass through "block outbound" rules if DNS is allowed.

4. **Software updates**: Firewalls need patches. A vulnerability in the firewall software (e.g., CVE-2023-27997 in FortiGate) could allow an attacker to bypass all rules.

5. **Administrative access**: Anyone with firewall admin credentials can change the rules. In a true air gap, there are no rules to change because there is no connection.

6. **Regulatory non-compliance**: Frameworks like NIST SP 800-82 (industrial control systems) and CNSSI 1253 (national security systems) distinguish between "network isolation" and "air gap." A firewall-based approach may not meet the air-gap requirement for certification.

A true air gap provides defense through physics (no wire, no fiber). A firewall provides defense through configuration (which can be wrong).
</details>

---

## Hands-On Exercise: Build an Air-Gapped Image Pipeline

**Task**: Simulate an air-gapped image transfer using two directories as "connected" and "disconnected" environments.

### Scenario
You manage an air-gapped Kubernetes cluster. A new version of CoreDNS needs to be deployed. Simulate the full pipeline.

### Steps

1. **Set up the "connected side"**:
   ```bash
   mkdir -p /tmp/connected-side/images
   cd /tmp/connected-side

   # Pull the image
   skopeo copy \
     docker://registry.k8s.io/coredns/coredns:v1.12.0 \
     oci-archive:images/coredns_v1.12.0.tar

   # Generate checksums
   cd images && sha256sum *.tar > SHA256SUMS
   ```

2. **Simulate the transfer** (copy to "air-gapped side"):
   ```bash
   mkdir -p /tmp/airgapped-side/incoming
   cp -r /tmp/connected-side/images/* /tmp/airgapped-side/incoming/
   ```

3. **Verify and import on the "air-gapped side"**:
   ```bash
   cd /tmp/airgapped-side/incoming
   sha256sum -c SHA256SUMS

   # If you have a local registry (kind with registry):
   skopeo copy \
     oci-archive:coredns_v1.12.0.tar \
     docker://localhost:5000/coredns/coredns:v1.12.0 \
     --dest-tls-verify=false
   ```

4. **Verify the image is available**:
   ```bash
   skopeo inspect docker://localhost:5000/coredns/coredns:v1.12.0 \
     --tls-verify=false | jq '.Digest'
   ```

### Success Criteria
- [ ] Image exported with `skopeo` to OCI archive
- [ ] SHA256 checksums generated and verified after transfer
- [ ] Image pushed to local registry
- [ ] Image digest matches between source and destination
- [ ] Process documented in a repeatable script

---

## Key Takeaways

1. **Physical security is non-negotiable** -- disable unused ports, lock racks, control IPMI access
2. **Air-gapped means air-gapped** -- firewalls are not air gaps; there must be no physical connection
3. **Harbor is the standard** for air-gapped registries with offline Trivy scanning
4. **The transfer process is the hardest part** -- design it before you need it, with checksums and two-person integrity
5. **GitOps works air-gapped** -- use Gitea/GitLab locally with Flux pointing to internal Git

---

## Next Module

Continue to [Module 6.2: Hardware Security (HSM/TPM)](../module-6.2-hardware-security/) to learn how hardware security modules and TPM protect your on-premises cluster's cryptographic keys and boot integrity.
