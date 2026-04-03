---
title: "Module 6.2: Hardware Security (HSM/TPM)"
slug: on-premises/security/module-6.2-hardware-security
sidebar:
  order: 3
---

> **Complexity**: `[ADVANCED]` | Time: 60 minutes
>
> **Prerequisites**: [Physical Security & Air-Gapped Environments](../module-6.1-air-gapped/), [CKS](../../k8s/cks/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** HSM-backed encryption for etcd secrets and Kubernetes signing keys using PKCS#11 integration
2. **Configure** TPM-based measured boot and node attestation to verify bare-metal server integrity before cluster admission
3. **Design** a key management architecture where master encryption keys never exist outside hardware security boundaries
4. **Evaluate** HSM deployment models (network HSM, PCIe HSM, cloud HSM) based on performance, compliance, and cost requirements

---

## Why This Module Matters

In 2021, a fintech company running Kubernetes on-premises stored their etcd encryption key in a Kubernetes Secret. That Secret was base64-encoded (not encrypted) and backed up nightly to an NFS share. A contractor with read access to the NFS share decoded the Secret, extracted the etcd encryption key, and used it to decrypt a backup of etcd -- which contained every Secret in the cluster: database passwords, API keys, TLS certificates, and service account tokens for 340 microservices. The breach was not detected for 11 weeks.

The root cause was not a Kubernetes vulnerability. It was a key management failure. The encryption key that protected everything was itself unprotected. On AWS, you would use KMS -- a hardware-backed key service where the master key never leaves the HSM. On-premises, you need the same capability, but you must build it yourself using Hardware Security Modules (HSMs) and Trusted Platform Modules (TPMs). These are not optional luxuries for regulated environments -- they are the foundation that makes all other encryption meaningful.

> **The Vault Door Analogy**
>
> Encrypting etcd without an HSM is like putting a combination lock on a bank vault but writing the combination on a Post-it note stuck to the door. The lock is real, the vault is real, but the security is theater. An HSM is a second vault -- one that holds the combination. The combination never leaves the vault; the vault performs the unlock operation internally. Even the vault manufacturer cannot extract the key once it is generated inside the HSM.

---

## What You'll Learn

- What HSMs and TPMs are and how they differ
- How TPM enables measured boot and secure boot for Kubernetes nodes
- Configuring HashiCorp Vault with an HSM backend via PKCS#11
- Replacing cloud KMS for Kubernetes encryption at rest
- Disk encryption with LUKS + TPM auto-unlock
- Key lifecycle management in on-premises environments

---

## HSM vs TPM: Understanding the Hardware

```
┌──────────────────────────────────────────────────────────────────┐
│                    HSM vs TPM COMPARISON                         │
│                                                                  │
│  HSM (Hardware Security Module)       TPM (Trusted Platform      │
│                                       Module)                    │
│  ┌─────────────────────────────┐     ┌──────────────────────┐   │
│  │  Network-attached appliance │     │  Chip soldered to    │   │
│  │  or PCIe card               │     │  the motherboard     │   │
│  │                             │     │                      │   │
│  │  - FIPS 140-2/3 Level 3    │     │  - FIPS 140-2 L1-2  │   │
│  │  - Tamper-evident/proof    │     │  - Tamper-resistant  │   │
│  │  - High throughput         │     │  - Low throughput    │   │
│  │  - $5,000 - $50,000+      │     │  - $0-$20 (on-board)│   │
│  │  - Shared by many servers  │     │  - One per server    │   │
│  │  - Key ceremony required   │     │  - Auto-provisioned  │   │
│  └─────────────────────────────┘     └──────────────────────┘   │
│                                                                  │
│  Use HSM for:                        Use TPM for:               │
│  - CA root keys                      - Measured/secure boot     │
│  - etcd encryption master key        - Disk encryption (LUKS)   │
│  - Vault unseal keys                 - Node attestation         │
│  - Code signing keys                 - Platform integrity       │
│  - Payment processing (PCI)          - SSH host keys            │
└──────────────────────────────────────────────────────────────────┘
```

### HSM Form Factors

| Form Factor | Example | Throughput | Cost | Use Case |
|-------------|---------|------------|------|----------|
| Network appliance | Thales Luna, Entrust nShield | 10,000+ ops/sec | $20K-$100K | Enterprise PKI, payment processing |
| PCIe card | Thales Luna PCIe, Utimaco | 5,000+ ops/sec | $5K-$30K | Single server, Vault backend |
| USB token | YubiHSM 2 | 50 ops/sec | $650 | Small deployments, dev/test |
| Cloud HSM | AWS CloudHSM, Azure Dedicated HSM | Varies | $1.50/hr | Hybrid environments |

---

## TPM for Measured Boot

Measured boot uses the TPM to create a chain of trust from firmware to the running OS. Each stage measures (hashes) the next stage before executing it, storing the measurement in TPM Platform Configuration Registers (PCRs).

```
┌──────────────────────────────────────────────────────────────┐
│                  MEASURED BOOT CHAIN                         │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐ │
│  │ UEFI     │───>│ Boot-    │───>│ Kernel + │───>│ Init  │ │
│  │ Firmware │    │ loader   │    │ Initramfs│    │ System│ │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └───┬───┘ │
│       │               │               │              │      │
│       ▼               ▼               ▼              ▼      │
│  PCR[0-1]        PCR[4-5]        PCR[8-9]       PCR[10+]   │
│  Firmware        Bootloader     Kernel           OS config  │
│  hashes          hash           + initrd hash    hashes     │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    TPM 2.0 CHIP                         │ │
│  │  PCR[0]: a3f2...  (firmware)                            │ │
│  │  PCR[4]: 7b1c...  (bootloader)                          │ │
│  │  PCR[8]: e9d4...  (kernel)                              │ │
│  │  PCR[9]: 12ab...  (initramfs)                           │ │
│  │                                                         │ │
│  │  If ANY measurement changes, PCR values change.         │ │
│  │  Sealed secrets (LUKS keys) will not unseal.            │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: If an attacker replaces the kernel on a Kubernetes node, which PCR values will change? How does the TPM detect this without any network connectivity or external verification service?

### Verifying TPM and Measured Boot on Kubernetes Nodes

These commands check whether TPM 2.0 hardware is present and read the Platform Configuration Registers that store the hash chain from boot. If any PCR value is all zeros, measured boot is not active.

```bash
# Check if TPM 2.0 is available
ls -la /dev/tpm0 /dev/tpmrm0

# Read PCR values to verify measured boot is active
tpm2_pcrread sha256:0,1,4,7,8,9

# Expected output (values will differ per system):
#   sha256:
#     0 : 0x3DCB05B32D60C4...   (firmware)
#     1 : 0xA4B7C3E9F1D2...     (firmware config)
#     4 : 0x7B1C8E2F5A9D...     (bootloader)
#     7 : 0xE5F6A7B8C9D0...     (Secure Boot policy)
#     8 : 0x1A2B3C4D5E6F...     (kernel)
#     9 : 0x9F8E7D6C5B4A...     (initramfs)

# If PCR[0] is all zeros, measured boot is not active
# Common cause: TPM not enabled in BIOS

# Verify Secure Boot status
mokutil --sb-state
# Expected: SecureBoot enabled
```

### Enabling TPM in a Talos Linux Cluster

Talos Linux (used for immutable Kubernetes nodes) has built-in TPM support:

```yaml
# talos-machine-config.yaml
machine:
  install:
    disk: /dev/sda
    bootloader: true
    wipe: false
  systemDiskEncryption:
    ephemeral:
      provider: luks2
      keys:
        - tpm: {}          # Seal LUKS key to TPM PCRs
          slot: 0
    state:
      provider: luks2
      keys:
        - tpm: {}
          slot: 0
```

---

## HashiCorp Vault with HSM Backend (PKCS#11)

Vault is the standard secrets manager for Kubernetes. In cloud environments, Vault uses cloud KMS for auto-unseal. On-premises, you replace cloud KMS with an HSM via the PKCS#11 interface.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              VAULT + HSM ARCHITECTURE                        │
│                                                              │
│  ┌──────────────────────┐       ┌──────────────────────┐    │
│  │  Kubernetes Cluster  │       │  HSM Appliance       │    │
│  │                      │       │  (Thales Luna /      │    │
│  │  ┌────────────────┐  │       │   Entrust nShield)   │    │
│  │  │  Vault Pod     │  │       │                      │    │
│  │  │                │◄─┼──────►│  Master Key (never   │    │
│  │  │  PKCS#11 lib   │  │       │  leaves the HSM)     │    │
│  │  │  (client)      │  │ mTLS  │                      │    │
│  │  └────────────────┘  │       │  PKCS#11 API         │    │
│  │         │            │       └──────────────────────┘    │
│  │         ▼            │                                    │
│  │  ┌────────────────┐  │       Auto-unseal: HSM unwraps   │
│  │  │  etcd (Vault   │  │       the Vault master key at    │
│  │  │  storage)      │  │       startup. No Shamir shares  │
│  │  └────────────────┘  │       needed.                    │
│  └──────────────────────┘                                    │
└──────────────────────────────────────────────────────────────┘
```

> **Stop and think**: Without HSM auto-unseal, Vault requires multiple keyholders to perform a "key ceremony" every time Vault restarts. In a Kubernetes environment where pods can be rescheduled at any time, why is this operationally untenable?

### Configure Vault with HSM Auto-Unseal

The following Vault configuration uses PKCS#11 to communicate with an HSM for automatic unsealing. The `seal "pkcs11"` stanza replaces cloud KMS -- the master key never leaves the HSM boundary.

```hcl
# vault-config.hcl
storage "raft" {
  path = "/vault/data"
  node_id = "vault-0"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_cert_file = "/vault/tls/tls.crt"
  tls_key_file  = "/vault/tls/tls.key"
}

# HSM seal configuration (replaces cloud KMS)
seal "pkcs11" {
  lib            = "/usr/lib/softhsm/libsofthsm2.so"  # Path to PKCS#11 library
  slot           = "0"                                   # HSM slot number
  pin            = "env://VAULT_HSM_PIN"                # PIN from environment
  key_label      = "vault-master-key"                   # Label of the key in HSM
  hmac_key_label = "vault-hmac-key"                     # Label for HMAC key
  mechanism      = "0x0001"                             # CKM_RSA_PKCS
  generate_key   = "true"                               # Generate key if not exists
}

api_addr = "https://vault.vault.svc:8200"
cluster_addr = "https://vault-0.vault-internal.vault.svc:8201"
```

### Deploy Vault with HSM on Kubernetes

Deploy Vault as a 3-replica StatefulSet using the Vault Helm chart. Key configuration points:

- Use `hashicorp/vault-enterprise` image (PKCS#11 seal requires Enterprise)
- Mount the HSM client library from the host (`/usr/lib/softhsm` or vendor path) as a read-only volume
- Inject the HSM PIN from a Kubernetes Secret via environment variable
- Mount TLS certificates for the Vault API endpoint
- Use Raft storage with a PVC per replica (10Gi recommended)

### Using YubiHSM 2 for Smaller Deployments

For clusters where a $50,000 network HSM is overkill, the YubiHSM 2 ($650) provides FIPS 140-2 Level 3 security in a USB form factor. Install the YubiHSM connector on the Vault node, generate an RSA key via `yubihsm-shell`, and configure Vault's seal stanza to use the YubiHSM PKCS#11 library (`yubihsm_pkcs11.so`). The configuration is identical to the network HSM case -- only the `lib` path changes.

---

## Replacing Cloud KMS for Kubernetes Encryption at Rest

In cloud environments, you configure Kubernetes to use cloud KMS for encrypting Secrets in etcd. On-premises, you use Vault with HSM as the KMS provider.

### Kubernetes KMS v2 Provider with Vault

```yaml
# kms-vault-plugin-config.yaml
# This runs on every control plane node
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps
    providers:
      - kms:
          apiVersion: v2
          name: vault-kms
          endpoint: unix:///var/run/kms-vault/kms.sock
          timeout: 10s
      - identity: {}    # Fallback: unencrypted (for migration)
```

```bash
# Install the KMS plugin on control plane nodes
# The plugin translates Kubernetes KMS gRPC calls to Vault API calls

# Start the KMS plugin
kms-vault-provider \
  --listen unix:///var/run/kms-vault/kms.sock \
  --vault-addr https://vault.vault.svc:8200 \
  --vault-token-path /var/run/secrets/vault/token \
  --transit-key kubernetes-secrets \
  --transit-mount transit/

# Configure kube-apiserver to use the plugin
# Add to kube-apiserver flags:
#   --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
```

---

## Disk Encryption with LUKS + TPM

Every Kubernetes node should have encrypted disks. LUKS (Linux Unified Key Setup) provides disk encryption, and TPM can automatically unseal the disk at boot -- but only if the boot chain is unmodified.

> **Pause and predict**: LUKS encryption with TPM auto-unlock means the disk decrypts automatically at boot. If someone steals the entire server (disk + TPM together), does the encryption still protect the data? Why or why not?

### Setting Up LUKS with TPM Auto-Unlock

The `systemd-cryptenroll` command seals the LUKS decryption key to specific TPM PCR values. The key is only released when the boot chain matches the expected measurements -- a modified kernel or bootloader will cause the unlock to fail.

```bash
# Encrypt a data partition with LUKS2
cryptsetup luksFormat --type luks2 /dev/sdb

# Add a TPM-sealed key (systemd-cryptenroll)
systemd-cryptenroll /dev/sdb \
  --tpm2-device=auto \
  --tpm2-pcrs=0+1+4+7+8    # Seal to firmware + bootloader + Secure Boot + kernel

# Configure auto-unlock at boot via /etc/crypttab
echo "k8s-data /dev/sdb - tpm2-device=auto" >> /etc/crypttab

# Test: reboot and verify automatic unlock
systemctl restart systemd-cryptsetup@k8s-data

# Verify the volume is unlocked
lsblk -f
# Expected: k8s-data (crypt) mounted and active
```

### What Happens on Tamper

```
NORMAL BOOT:
  UEFI ──> Bootloader ──> Kernel ──> TPM PCRs match ──> LUKS unseals ──> OK

TAMPERED BOOT (e.g., modified kernel):
  UEFI ──> Bootloader ──> Kernel* ──> TPM PCRs CHANGED ──> LUKS REFUSES ──> FAIL

  * The modified kernel produces a different hash in PCR[8].
    The LUKS key was sealed to the original PCR[8] value.
    The TPM will not release the key. The disk stays encrypted.
    The node fails to boot. An alert is generated.
```

---

## Did You Know?

- **FIPS 140-3 replaced FIPS 140-2 in 2019** but transition was delayed. As of 2025, most HSMs are still certified under FIPS 140-2 Level 3. The new standard adds physical security testing against fault injection attacks (voltage glitching, electromagnetic probing).

- **The Shamir's Secret Sharing scheme** used by Vault's default seal was invented by Adi Shamir in 1979 -- the same Shamir as in RSA (Rivest-Shamir-Adleman). With HSM auto-unseal, Shamir shares are replaced by a single HSM-protected key, eliminating the "key ceremony" problem of gathering multiple keyholders.

- **TPM 2.0 was mandated by Microsoft for Windows 11**, which dramatically accelerated TPM adoption in server hardware. Before 2021, many server vendors shipped TPM as a $50 add-on module. Now it is standard on virtually all enterprise servers.

- **Google's Titan chip** is a custom TPM equivalent that validates the boot firmware of every server in Google's fleet. It was created after Google discovered that some server BMC firmwares from major vendors contained backdoors planted during manufacturing.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Storing HSM PIN in a ConfigMap | PIN exposed to anyone with RBAC read | Use a Kubernetes Secret with strict RBAC, or inject via init container |
| Single HSM with no HA | HSM failure = Vault cannot unseal = cluster-wide secret outage | Deploy HSM in HA pair (active/standby) or use multiple USB HSMs |
| Sealing LUKS to PCR[7] only | Only measures Secure Boot policy, not actual kernel | Seal to PCRs 0+1+4+7+8 (firmware, config, bootloader, SB, kernel) |
| Not rotating HSM keys | Compromised key has unlimited lifetime | Define key rotation policy (annually or per compliance requirement) |
| Running Vault without HSM seal | Vault unseal keys are Shamir shares stored by humans | Use HSM auto-unseal; eliminate human key management |
| Ignoring TPM event log | Cannot detect what changed when PCR mismatch occurs | Ship TPM event logs to SIEM; review on boot failures |
| HSM on same network as workloads | Compromised pod could attempt HSM operations | Isolate HSM on dedicated management VLAN |
| No HSM backup strategy | HSM hardware failure = permanent key loss | Use HSM key export (wrapped) to backup HSM or secure offline storage |

---

## Quiz

### Question 1
Your Vault cluster uses HSM auto-unseal. The HSM appliance suffers a hardware failure at 2 AM. What happens to running workloads, and what is your recovery plan?

<details>
<summary>Answer</summary>

**Immediate impact on running workloads: None.**

Running pods that already have their secrets (injected via Vault Agent or CSI driver) will continue operating normally. Kubernetes does not re-fetch secrets continuously -- they are cached in pod memory or tmpfs volumes.

**What breaks:**
1. New pods cannot start if they require secrets from Vault (Vault Agent sidecar init will timeout).
2. Secret rotation stops -- any automated rotation policies will fail.
3. If a Vault pod restarts, it cannot unseal (the HSM is unavailable for the unseal operation).

**Recovery plan:**
1. **Short-term (minutes)**: If you have an HSM HA pair, the standby HSM takes over automatically. Vault auto-unseal retries and succeeds.

2. **If no HA HSM**: Vault pods that are already running and unsealed continue serving requests. Do not restart them. Contact the HSM vendor for emergency replacement.

3. **Disaster recovery**: If all Vault pods restart before the HSM is restored, you cannot unseal Vault. Recovery keys generated during `vault operator init` with HSM auto-unseal are for recovery operations (e.g., generating a new root token) -- they **cannot** be used to unseal Vault. You must either restore the HSM, provision a replacement HSM with the same key material (from HSM backups), or migrate the seal type.

4. **Prevention**: Always deploy HSMs in pairs. The $50K cost of a second HSM is trivial compared to the cost of a secrets management outage across the cluster.
</details>

### Question 2
Explain why TPM-sealed LUKS encryption prevents a "stolen disk" attack but not a "stolen server" attack.

<details>
<summary>Answer</summary>

**Stolen disk scenario:**
An attacker removes the disk from the server. They connect it to a different machine. The different machine has a different TPM with different PCR values (or no TPM at all). The LUKS key was sealed to the original server's TPM PCRs. The TPM on the new machine cannot unseal the key. The disk is encrypted and unreadable. Attack defeated.

**Stolen server scenario:**
An attacker steals the entire server -- disk, motherboard, and TPM chip together. On normal power-on, the same firmware runs, the same bootloader loads, the same kernel starts. PCR values match. The TPM releases the LUKS key. The disk decrypts. The attacker has full access.

**Mitigations for stolen server:**
1. **PIN + TPM**: Require a boot-time PIN in addition to TPM (`systemd-cryptenroll --tpm2-with-pin=yes`). The attacker needs both the server and the PIN.

2. **Network-bound disk encryption (NBDE)**: Use Clevis + Tang. The LUKS key is sealed to a network server (Tang) that is only reachable on the datacenter network. Stolen server outside the network cannot reach Tang, cannot unseal.

3. **Physical security**: Rack locks, tamper-evident seals, exit controls. Detect the theft before the server can be booted.

4. **Remote attestation**: The server must attest to a central service before the OS fully boots. If attestation fails (wrong network, unexpected location), the boot process halts.
</details>

### Question 3
You need to replace AWS KMS for encrypting Kubernetes Secrets at rest in an on-premises cluster. What is the architecture?

<details>
<summary>Answer</summary>

**Architecture: Kubernetes KMS v2 Provider with Vault + HSM.**

The chain is:

1. **Kubernetes API server** receives a request to create a Secret.
2. The API server calls the **KMS v2 plugin** via a Unix socket (gRPC).
3. The KMS plugin calls **Vault's Transit secrets engine** to encrypt the data encryption key (DEK).
4. Vault's Transit engine uses a key encryption key (KEK) stored in Vault.
5. Vault's seal wraps the KEK using the **HSM** via PKCS#11. The HSM master key never leaves the hardware.
6. The encrypted DEK and encrypted Secret are stored in **etcd**.

This is the "envelope encryption" pattern -- the same pattern used by AWS KMS, Azure Key Vault, and GCP Cloud KMS:

```
Secret data --> DEK encrypts data --> KEK encrypts DEK --> HSM protects KEK
(plaintext)     (Kubernetes)          (Vault Transit)     (Hardware)
```

**Components needed:**
- HSM appliance or YubiHSM 2
- Vault Enterprise (PKCS#11 seal requires Enterprise) or Vault Community with SoftHSM for non-production
- KMS v2 plugin binary on each control plane node
- Encryption configuration in kube-apiserver

**Key advantage over cloud KMS:** You own the HSM. The key material is physically in your datacenter. No cloud provider can be compelled to provide access to your keys.
</details>

### Question 4
Why is SoftHSM acceptable for development but not for production?

<details>
<summary>Answer</summary>

**SoftHSM is a software implementation of the PKCS#11 interface.** It stores keys in files on the filesystem, protected only by OS file permissions.

**Why it is fine for development:**
- It implements the same API as a real HSM (PKCS#11), so your Vault configuration, KMS plugin, and automation scripts work identically.
- It is free and requires no special hardware.
- You can test key generation, rotation, and seal/unseal workflows.

**Why it is unacceptable for production:**

1. **No hardware protection**: Keys are stored in regular files. Anyone with root access (or a disk image) can extract them. A real HSM stores keys in tamper-proof hardware -- extracting them triggers key destruction.

2. **No tamper evidence**: If someone copies the SoftHSM key files, there is no indication. A physical HSM has tamper-evident seals and intrusion detection.

3. **No FIPS certification**: SoftHSM cannot be FIPS 140-2/3 certified because it lacks hardware security boundaries. Regulated industries (finance, healthcare, government) require FIPS-certified key storage.

4. **Keys in memory**: SoftHSM keys exist in process memory, vulnerable to memory dumps, cold boot attacks, and swap file extraction. HSMs have dedicated security processors with memory that is cleared on tamper detection.

5. **No audit trail**: SoftHSM does not generate a hardware audit log. HSMs produce tamper-evident logs of every cryptographic operation.

**Bottom line:** SoftHSM lets you test the integration. A real HSM provides the security guarantees. Never use SoftHSM for production secrets.
</details>

---

## Hands-On Exercise: Set Up Vault with SoftHSM Auto-Unseal

**Task**: Configure a development Vault instance using SoftHSM to simulate HSM auto-unseal.

### Prerequisites
- A Linux machine or VM (Ubuntu 22.04 recommended)
- Docker installed

### Steps

1. **Install SoftHSM**:
   ```bash
   apt-get install -y softhsm2

   # Initialize a token
   softhsm2-util --init-token --slot 0 \
     --label "vault-hsm" \
     --pin 1234 --so-pin 0000

   # Verify
   softhsm2-util --show-slots
   ```

2. **Start Vault with PKCS#11 seal**:
   ```bash
   cat > /tmp/vault-config.hcl <<'EOF'
   storage "file" {
     path = "/tmp/vault-data"
   }
   listener "tcp" {
     address     = "127.0.0.1:8200"
     tls_disable = true
   }
   seal "pkcs11" {
     lib            = "/usr/lib/softhsm/libsofthsm2.so"
     slot           = "0"
     pin            = "1234"
     key_label      = "vault-key"
     hmac_key_label = "vault-hmac"
     generate_key   = "true"
   }
   EOF

   mkdir -p /tmp/vault-data
   vault server -config=/tmp/vault-config.hcl &
   ```

3. **Initialize and verify auto-unseal**:
   ```bash
   export VAULT_ADDR="http://127.0.0.1:8200"
   vault operator init -recovery-shares=1 -recovery-threshold=1

   # Note: with HSM seal, Vault uses "recovery keys" instead of "unseal keys"
   # The HSM handles unsealing automatically

   vault status
   # Sealed: false  (auto-unsealed via SoftHSM)
   ```

4. **Test auto-unseal by restarting Vault**:
   ```bash
   kill %1        # Stop Vault
   vault server -config=/tmp/vault-config.hcl &

   sleep 2
   vault status
   # Sealed: false  (auto-unsealed again without manual intervention)
   ```

### Success Criteria
- [ ] SoftHSM token initialized with a PIN
- [ ] Vault starts with PKCS#11 seal configuration
- [ ] `vault operator init` uses recovery keys (not unseal keys)
- [ ] Vault auto-unseals on restart without manual intervention
- [ ] Understand why this setup is for development only

---

## Key Takeaways

1. **HSMs protect the keys that protect everything else** -- without them, encryption at rest is security theater
2. **TPM provides measured boot** -- a tampered kernel or bootloader changes PCR values, preventing disk unlock
3. **Vault + HSM replaces cloud KMS** -- PKCS#11 is the standard interface
4. **LUKS + TPM encrypts node disks** but protect against stolen servers with PIN or NBDE (Tang)
5. **SoftHSM for dev, real HSM for production** -- the API is the same, the security guarantees are not

---

## Next Module

Continue to [Module 6.3: Enterprise Identity (AD/LDAP/OIDC)](../module-6.3-enterprise-identity/) to learn how to integrate Kubernetes authentication with your organization's existing identity systems.
