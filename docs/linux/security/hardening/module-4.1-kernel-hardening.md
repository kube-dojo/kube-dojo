# Module 4.1: Kernel Hardening & sysctl

> **Linux Security** | Complexity: `[MEDIUM]` | Time: 25-30 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: Kernel & Architecture](../../foundations/system-essentials/module-1.1-kernel-architecture.md)
- **Required**: [Module 3.1: TCP/IP Essentials](../../foundations/networking/module-3.1-tcp-ip-essentials.md)
- **Helpful**: Understanding of basic security concepts

---

## Why This Module Matters

The Linux kernel has hundreds of tunable parameters that affect security. Many are insecure by default for compatibility reasons. Proper hardening reduces attack surface and prevents common exploits.

Understanding kernel hardening helps you:

- **Secure Kubernetes nodes** — CIS benchmarks require specific sysctl settings
- **Pass CKS exam** — Kernel hardening is directly tested
- **Prevent network attacks** — Disable IP forwarding, ICMP redirects
- **Protect against memory exploits** — ASLR, exec-shield, etc.

When a security scanner flags sysctl settings or a CIS benchmark fails, you need to understand these parameters.

---

## Did You Know?

- **The Linux kernel has over 1,000 sysctl parameters** — Most are safe defaults, but dozens are security-critical. The CIS Benchmark for Linux covers about 50 of them.

- **ASLR (Address Space Layout Randomization) has been default since 2005** — It randomizes where programs load in memory, making exploits much harder. Disabling it (`kernel.randomize_va_space=0`) is a major security mistake.

- **IP forwarding disabled by default is intentional** — A workstation shouldn't route packets. Enabling it without proper firewall rules turns your machine into an open router.

- **sysctl changes are not persistent by default** — Running `sysctl -w` changes only last until reboot. Files in `/etc/sysctl.d/` make them permanent.

---

## sysctl Basics

### What is sysctl?

**sysctl** modifies kernel parameters at runtime. These parameters live in `/proc/sys/` as virtual files.

```
/proc/sys/
├── kernel/          # Kernel behavior
│   ├── randomize_va_space
│   ├── pid_max
│   └── ...
├── net/             # Network stack
│   ├── ipv4/
│   │   ├── ip_forward
│   │   ├── tcp_syncookies
│   │   └── ...
│   └── ipv6/
├── vm/              # Virtual memory
│   ├── swappiness
│   ├── overcommit_memory
│   └── ...
└── fs/              # Filesystem
    ├── file-max
    └── ...
```

### Using sysctl

```bash
# View a parameter
sysctl kernel.randomize_va_space
# Or
cat /proc/sys/kernel/randomize_va_space

# View all parameters
sysctl -a

# Set temporarily (lost at reboot)
sudo sysctl -w net.ipv4.ip_forward=0

# Set permanently
echo "net.ipv4.ip_forward = 0" | sudo tee /etc/sysctl.d/99-security.conf
sudo sysctl -p /etc/sysctl.d/99-security.conf

# Reload all sysctl files
sudo sysctl --system
```

---

## Network Hardening

### IP Forwarding

```bash
# Should be 0 on non-routers (1 needed for containers/K8s)
sysctl net.ipv4.ip_forward

# Disable (if not needed)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# On Kubernetes nodes, forwarding MUST be enabled
# But should be combined with proper firewall rules
```

### ICMP Hardening

```bash
# Ignore ICMP broadcasts (prevent Smurf attacks)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Don't accept ICMP redirects (prevent MITM)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Don't send ICMP redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
```

### Source Routing & Spoofing

```bash
# Disable source routing (attacker-controlled routing)
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Enable reverse path filtering (anti-spoofing)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log spoofed packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
```

### TCP SYN Protection

```bash
# Enable SYN cookies (prevent SYN flood attacks)
net.ipv4.tcp_syncookies = 1

# Reduce SYN-ACK retries
net.ipv4.tcp_synack_retries = 2

# Reduce orphaned connection timeout
net.ipv4.tcp_fin_timeout = 15

# Limit connection tracking
net.netfilter.nf_conntrack_max = 1000000
```

---

## Memory Protection

### ASLR (Address Space Layout Randomization)

```bash
# Check current setting
sysctl kernel.randomize_va_space

# Values:
# 0 = Disabled (INSECURE!)
# 1 = Conservative randomization
# 2 = Full randomization (recommended)

# Enable full ASLR
kernel.randomize_va_space = 2
```

### Memory Protections

```bash
# Restrict ptrace (prevent debugging other processes)
kernel.yama.ptrace_scope = 1
# 0 = Classic ptrace (anyone can trace)
# 1 = Restricted (only parent can trace)
# 2 = Admin only
# 3 = No ptrace

# Restrict access to kernel pointers
kernel.kptr_restrict = 2
# 0 = No restrictions
# 1 = Hide from non-root
# 2 = Hide from everyone

# Restrict dmesg access
kernel.dmesg_restrict = 1

# Restrict perf events
kernel.perf_event_paranoid = 3
```

### Disable Magic SysRq

```bash
# SysRq key allows keyboard-triggered kernel commands
# Useful for debugging, dangerous if physical access
kernel.sysrq = 0
# 0 = Disabled
# 1 = All functions enabled
# See Documentation/admin-guide/sysrq.rst for bitmask values
```

---

## Filesystem Security

```bash
# Protect hardlinks and symlinks
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# Protect FIFOs and regular files in sticky directories
fs.protected_fifos = 2
fs.protected_regular = 2

# Increase file descriptor limit
fs.file-max = 2097152
```

---

## System Integrity Verification

Beyond runtime kernel settings, you need to verify that system files haven't been tampered with. AIDE (Advanced Intrusion Detection Environment) and `rpm -V` detect unauthorized changes to critical files.

### AIDE (Advanced Intrusion Detection Environment)

AIDE creates a database of file checksums, permissions, and timestamps, then compares the current state against that baseline.

```bash
# Install AIDE
sudo apt install -y aide      # Debian/Ubuntu
sudo dnf install -y aide       # RHEL/Rocky

# Initialize the database (takes a few minutes — scans all configured paths)
sudo aideinit                  # Debian/Ubuntu
sudo aide --init               # RHEL/Rocky

# The new database is created at /var/lib/aide/aide.db.new
# Move it into place as the reference baseline
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Check system integrity against the baseline
sudo aide --check
# Output shows any files that changed: added, removed, or modified

# After legitimate changes (patching, config updates), update the baseline
sudo aide --update
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

### Package Verification with rpm -V

On RPM-based systems (RHEL, Rocky, Fedora), you can verify installed packages against their original checksums:

```bash
# Verify a specific package
rpm -V openssh-server
# No output = everything matches
# Output shows what changed:
#   S = file Size differs
#   5 = MD5 checksum differs
#   T = modification Time differs
#   c = config file

# Verify ALL installed packages (takes time)
rpm -Va

# Example output:
# S.5....T.  c /etc/ssh/sshd_config    ← config was modified (expected)
# ..5....T.    /usr/bin/ssh             ← binary changed (suspicious!)
```

> **Exam tip**: AIDE questions on the LFCS typically involve initializing a baseline and running a check. Remember the workflow: `aide --init`, move the database, then `aide --check`. On RPM systems, `rpm -V` is a quick way to verify individual packages.

---

## Kubernetes Node Hardening

### Required for Kubernetes

```bash
# These MUST be enabled for Kubernetes to work

# IP forwarding (for pod networking)
net.ipv4.ip_forward = 1

# Bridge netfilter (for iptables on bridges)
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# Load br_netfilter module first
modprobe br_netfilter
```

### Recommended for Kubernetes Nodes

```bash
# /etc/sysctl.d/99-kubernetes-hardening.conf

# Network security (compatible with K8s)
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.tcp_syncookies = 1

# Memory protection
kernel.randomize_va_space = 2
kernel.yama.ptrace_scope = 1
kernel.kptr_restrict = 1
kernel.dmesg_restrict = 1

# Filesystem protection
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# Connection tracking for high pod counts
net.netfilter.nf_conntrack_max = 1000000
```

### CIS Benchmark Compliance

```bash
# Key CIS Benchmark sysctl requirements:

# 3.1.1 - Disable IP forwarding (unless routing needed)
# 3.1.2 - Disable packet redirect sending
# 3.2.1 - Disable source routed packets
# 3.2.2 - Disable ICMP redirects
# 3.2.3 - Disable secure ICMP redirects
# 3.2.4 - Log suspicious packets
# 3.2.7 - Enable reverse path filtering
# 3.2.8 - Enable TCP SYN cookies
# 3.2.9 - Disable IPv6 router advertisements

# Verify compliance
grep -r "." /proc/sys/net/ipv4/conf/*/accept_redirects
```

---

## Applying sysctl Settings

### Persistent Configuration

```bash
# Create configuration file
cat <<EOF | sudo tee /etc/sysctl.d/99-hardening.conf
# Network hardening
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.tcp_syncookies = 1

# Memory protection
kernel.randomize_va_space = 2
kernel.yama.ptrace_scope = 1
kernel.kptr_restrict = 1

# Filesystem
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
EOF

# Apply
sudo sysctl --system

# Verify
sysctl kernel.randomize_va_space
```

### Loading Order

```
/run/sysctl.d/*.conf
/etc/sysctl.d/*.conf
/usr/local/lib/sysctl.d/*.conf
/usr/lib/sysctl.d/*.conf
/lib/sysctl.d/*.conf
/etc/sysctl.conf

(Later files override earlier ones)
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Disabling ASLR | Makes exploits easier | Keep randomize_va_space=2 |
| IP forwarding on workstation | Acts as open router | Disable unless needed |
| Changes not persistent | Lost at reboot | Use /etc/sysctl.d/ |
| Hardening breaks K8s | Networking fails | Keep required K8s settings |
| Not verifying changes | Settings not applied | Use `sysctl -a | grep` |
| Hardening without testing | Production breakage | Test in staging first |

---

## Quiz

### Question 1
What does `kernel.randomize_va_space = 2` do?

<details>
<summary>Show Answer</summary>

**Full ASLR (Address Space Layout Randomization)** — Randomizes:
- Stack location
- mmap base
- VDSO location
- Heap location

This makes buffer overflow and return-to-libc attacks much harder because memory addresses are unpredictable.

</details>

### Question 2
Why is `net.ipv4.ip_forward = 1` required for Kubernetes but risky elsewhere?

<details>
<summary>Show Answer</summary>

**IP forwarding** enables packet routing between interfaces.

- **Kubernetes needs it**: Pods on different nodes communicate through the host
- **Risky elsewhere**: Your machine becomes a router; without proper firewall rules, it could forward malicious traffic

Kubernetes combines forwarding with iptables rules that control what's actually forwarded.

</details>

### Question 3
What does `net.ipv4.tcp_syncookies = 1` protect against?

<details>
<summary>Show Answer</summary>

**SYN flood attacks** — A denial of service where attackers send many TCP SYN packets without completing the handshake.

SYN cookies encode connection state in the sequence number, so the server doesn't need to store state for half-open connections. Legitimate clients can still connect; attackers waste resources.

</details>

### Question 4
How do you make sysctl changes persistent across reboots?

<details>
<summary>Show Answer</summary>

Create a file in `/etc/sysctl.d/`:

```bash
echo "net.ipv4.ip_forward = 0" | sudo tee /etc/sysctl.d/99-myconfig.conf
sudo sysctl --system
```

Files are loaded in alphabetical order; higher numbers load later and override.

</details>

### Question 5
What does `kernel.yama.ptrace_scope = 1` do?

<details>
<summary>Show Answer</summary>

**Restricts ptrace to parent processes only**:
- Only a process's direct parent can trace/debug it
- Prevents arbitrary process debugging
- Stops attackers from attaching debuggers to steal secrets

Values:
- 0 = No restrictions
- 1 = Parent only (recommended)
- 2 = Admin only
- 3 = Disabled completely

</details>

---

## Hands-On Exercise

### Kernel Hardening

**Objective**: Audit and harden kernel parameters.

**Environment**: Linux system with root access

#### Part 1: Audit Current Settings

```bash
# 1. Check ASLR
sysctl kernel.randomize_va_space

# 2. Check IP forwarding
sysctl net.ipv4.ip_forward
sysctl net.ipv6.conf.all.forwarding

# 3. Check ICMP settings
sysctl net.ipv4.conf.all.accept_redirects
sysctl net.ipv4.conf.all.send_redirects

# 4. Check source routing
sysctl net.ipv4.conf.all.accept_source_route

# 5. Check SYN cookies
sysctl net.ipv4.tcp_syncookies

# 6. Check ptrace restrictions
sysctl kernel.yama.ptrace_scope

# 7. Check filesystem protections
sysctl fs.protected_hardlinks
sysctl fs.protected_symlinks
```

#### Part 2: Create Hardening Config

```bash
# 1. Create hardening file
cat <<'EOF' | sudo tee /etc/sysctl.d/99-security-hardening.conf
# Security hardening settings

# Memory protection
kernel.randomize_va_space = 2
kernel.yama.ptrace_scope = 1
kernel.kptr_restrict = 1

# ICMP hardening
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Enable reverse path filtering
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1

# TCP hardening
net.ipv4.tcp_syncookies = 1

# Filesystem protection
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
EOF

# 2. Apply settings
sudo sysctl --system

# 3. Verify
sysctl kernel.randomize_va_space
sysctl net.ipv4.tcp_syncookies
```

#### Part 3: Test Impact

```bash
# 1. Test ASLR (run multiple times)
cat /proc/self/maps | grep stack
# Address should be different each time

# 2. Check for martian logging
sudo dmesg | grep martian

# 3. Test ptrace restriction (as non-root)
strace -p 1 2>&1 | head -3
# Should fail with permission error
```

#### Part 4: Compare with CIS Benchmark

```bash
# Create a simple audit script
cat <<'EOF' > /tmp/audit-sysctl.sh
#!/bin/bash
echo "=== CIS Benchmark Sysctl Audit ==="

check() {
    current=$(sysctl -n $1 2>/dev/null)
    if [ "$current" = "$2" ]; then
        echo "[PASS] $1 = $current"
    else
        echo "[FAIL] $1 = $current (expected $2)"
    fi
}

check "kernel.randomize_va_space" "2"
check "net.ipv4.conf.all.accept_redirects" "0"
check "net.ipv4.conf.all.send_redirects" "0"
check "net.ipv4.conf.all.accept_source_route" "0"
check "net.ipv4.tcp_syncookies" "1"
check "fs.protected_hardlinks" "1"
check "fs.protected_symlinks" "1"
EOF

chmod +x /tmp/audit-sysctl.sh
/tmp/audit-sysctl.sh
```

### Success Criteria

- [ ] Audited current kernel parameters
- [ ] Created persistent hardening configuration
- [ ] Verified settings were applied
- [ ] Understand the purpose of key parameters
- [ ] Ran basic CIS compliance check

---

## Key Takeaways

1. **sysctl controls kernel behavior** — Hundreds of tunable parameters

2. **Network hardening is critical** — Disable redirects, source routing, enable SYN cookies

3. **Memory protection matters** — ASLR, ptrace restrictions, pointer hiding

4. **Persistence requires files** — Use /etc/sysctl.d/ for permanent changes

5. **Kubernetes needs some "insecure" settings** — IP forwarding, bridge netfilter

---

## What's Next?

In **Module 4.2: AppArmor Profiles**, you'll learn mandatory access control for applications—constraining what programs can do beyond traditional permissions.

---

## Further Reading

- [Linux Kernel sysctl Documentation](https://www.kernel.org/doc/Documentation/admin-guide/sysctl/)
- [CIS Benchmark for Linux](https://www.cisecurity.org/benchmark/distribution_independent_linux)
- [NSA Linux Hardening Guide](https://media.defense.gov/2020/Aug/18/2002479461/-1/-1/0/HARDENING_YOUR_SYSTEMS.PDF)
- [Red Hat Security Hardening](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/security_hardening/)
