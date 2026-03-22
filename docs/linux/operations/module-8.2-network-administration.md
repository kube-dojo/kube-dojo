# Module 8.2: Network Administration

> **Operations — LFCS** | Complexity: `[COMPLEX]` | Time: 45-55 min

## Prerequisites

Before starting this module:
- **Required**: [Module 3.1: TCP/IP Essentials](../foundations/networking/module-3.1-tcp-ip-essentials.md) for IP addressing, subnets, and routing
- **Required**: [Module 3.4: iptables & netfilter](../foundations/networking/module-3.4-iptables-netfilter.md) for packet filtering fundamentals
- **Helpful**: [Module 1.2: Processes & systemd](../foundations/system-essentials/module-1.2-processes-systemd.md) for service management

---

## Why This Module Matters

TCP/IP knowledge tells you how packets flow. This module teaches you how to control that flow — who gets in, who gets out, which interfaces bond together, and how to harden your network services.

Understanding network administration helps you:

- **Secure servers** — Firewalls are your first and last line of defense
- **Build reliable networks** — Bonding and bridging prevent single points of failure
- **Enable routing** — NAT and masquerading let private networks reach the internet
- **Pass the LFCS exam** — Networking is 25% of the exam, the largest single domain

If your server is on the internet without a properly configured firewall, it's not a question of *if* it gets compromised — it's *when*.

---

## Did You Know?

- **firewalld replaced iptables as the default** on RHEL/CentOS 7+ and Fedora. Under the hood, firewalld uses nftables (the successor to iptables) as its backend. Ubuntu uses `ufw` by default but firewalld works there too.

- **Network bonding can survive cable pulls** — With active-backup bonding, you can physically unplug a network cable and traffic seamlessly switches to the other interface. Data centers use this everywhere.

- **NTP matters more than you think** — A time drift of just a few seconds can break Kerberos authentication, cause TLS certificate failures, and make log correlation impossible. Chrony replaced ntpd because it syncs faster and handles virtual machines better.

---

## Firewall Management with firewalld

### Why firewalld Over Raw iptables

Raw iptables rules are powerful but fragile. One mistake can lock you out. firewalld adds:
- **Zones**: Group interfaces and rules by trust level
- **Runtime vs permanent**: Test rules before making them permanent
- **Services**: Pre-defined rule sets (ssh, http, https, etc.)
- **Rich rules**: Complex rules without raw iptables syntax

### Installing and Starting firewalld

```bash
# Install (may already be present)
sudo apt install -y firewalld

# Start and enable
sudo systemctl enable --now firewalld

# Check status
sudo firewall-cmd --state
# running

# Check active zones
sudo firewall-cmd --get-active-zones
# public
#   interfaces: eth0
```

### Zones

Zones define the trust level for network connections:

| Zone | Purpose | Default Behavior |
|------|---------|-----------------|
| `drop` | Untrusted networks | Drop all incoming, no reply |
| `block` | Untrusted networks | Reject incoming with ICMP |
| `public` | Public networks (default) | Reject incoming except selected |
| `external` | NAT/masquerading | Masquerade outbound traffic |
| `dmz` | DMZ servers | Limited incoming allowed |
| `work` | Work networks | Trust some services |
| `home` | Home networks | Trust more services |
| `internal` | Internal networks | Similar to work |
| `trusted` | Trust everything | Allow all traffic |

```bash
# List all zones
sudo firewall-cmd --get-zones

# Show default zone
sudo firewall-cmd --get-default-zone
# public

# Change default zone
sudo firewall-cmd --set-default-zone=public

# Assign interface to a zone
sudo firewall-cmd --zone=internal --change-interface=eth1 --permanent
sudo firewall-cmd --reload

# Show zone details
sudo firewall-cmd --zone=public --list-all
```

### Managing Services

```bash
# List available pre-defined services
sudo firewall-cmd --get-services

# List services enabled in current zone
sudo firewall-cmd --list-services
# dhcpv6-client ssh

# Add a service (runtime only — lost on reload)
sudo firewall-cmd --add-service=http
sudo firewall-cmd --add-service=https

# Add a service permanently
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --reload

# Remove a service
sudo firewall-cmd --remove-service=http --permanent
sudo firewall-cmd --reload

# Add a custom port
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --add-port=3000-3100/tcp --permanent
sudo firewall-cmd --reload
```

### Rich Rules

Rich rules provide fine-grained control when simple service/port rules aren't enough:

```bash
# Allow SSH only from specific subnet
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" service name="ssh" accept' --permanent

# Block a specific IP
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="10.0.0.50" drop' --permanent

# Rate-limit connections (prevent brute force)
sudo firewall-cmd --add-rich-rule='rule family="ipv4" service name="ssh" accept limit value="3/m"' --permanent

# Log and drop traffic from a subnet
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="203.0.113.0/24" log prefix="BLOCKED: " level="warning" drop' --permanent

# Apply changes
sudo firewall-cmd --reload

# List rich rules
sudo firewall-cmd --list-rich-rules
```

### Runtime vs Permanent

```bash
# Runtime rule (test it first)
sudo firewall-cmd --add-service=http

# If it works, make it permanent
sudo firewall-cmd --runtime-to-permanent

# Or start over — reload drops runtime-only rules
sudo firewall-cmd --reload

# This workflow prevents lockouts:
# 1. Add rule (runtime)
# 2. Test access
# 3. If good: --runtime-to-permanent
# 4. If bad: --reload to revert
```

---

## nftables (The Modern Backend)

nftables replaces iptables as the Linux kernel packet filtering framework. firewalld uses nftables under the hood, but you should know the basics for the LFCS.

```bash
# Check if nftables is active
sudo nft list ruleset

# List tables
sudo nft list tables

# Create a simple firewall from scratch
sudo nft add table inet filter
sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
sudo nft add chain inet filter forward '{ type filter hook forward priority 0; policy drop; }'
sudo nft add chain inet filter output '{ type filter hook output priority 0; policy accept; }'

# Allow established connections
sudo nft add rule inet filter input ct state established,related accept

# Allow loopback
sudo nft add rule inet filter input iifname "lo" accept

# Allow SSH
sudo nft add rule inet filter input tcp dport 22 accept

# Allow ICMP (ping)
sudo nft add rule inet filter input ip protocol icmp accept

# View rules
sudo nft list chain inet filter input

# Save rules persistently
sudo nft list ruleset | sudo tee /etc/nftables.conf
sudo systemctl enable nftables
```

> **Exam tip**: On the LFCS exam (Ubuntu), you'll most likely use `ufw` or `firewalld`. But understanding that nftables is the underlying framework helps when debugging.

---

## NAT and Masquerading

NAT (Network Address Translation) lets machines on a private network access the internet through a gateway machine. Masquerading is a form of NAT where the source address is dynamically replaced with the gateway's address.

### Enable IP Forwarding

```bash
# Check current status
cat /proc/sys/net/ipv4/ip_forward
# 0 = disabled, 1 = enabled

# Enable temporarily
sudo sysctl -w net.ipv4.ip_forward=1

# Enable permanently
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-ip-forward.conf
sudo sysctl -p /etc/sysctl.d/99-ip-forward.conf
```

### Masquerading with firewalld

```bash
# Enable masquerading on external zone
sudo firewall-cmd --zone=external --add-masquerade --permanent

# Assign external interface to external zone
sudo firewall-cmd --zone=external --change-interface=eth0 --permanent

# Assign internal interface to internal zone
sudo firewall-cmd --zone=internal --change-interface=eth1 --permanent

# Allow forwarding from internal to external
sudo firewall-cmd --zone=internal --add-forward --permanent

sudo firewall-cmd --reload

# Verify masquerading is enabled
sudo firewall-cmd --zone=external --query-masquerade
# yes
```

### Port Forwarding

```bash
# Forward port 8080 on external to internal server 192.168.1.100:80
sudo firewall-cmd --zone=external --add-forward-port=port=8080:proto=tcp:toport=80:toaddr=192.168.1.100 --permanent

sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --zone=external --list-forward-ports
```

---

## Network Bonding and Bridging

### Network Bonding (Link Aggregation)

Bonding combines multiple network interfaces for redundancy or throughput:

| Mode | Name | Use Case |
|------|------|----------|
| 0 | balance-rr | Round-robin, increased throughput |
| 1 | active-backup | Failover, one active at a time |
| 2 | balance-xor | Transmit based on hash |
| 4 | 802.3ad (LACP) | Dynamic link aggregation (requires switch support) |
| 6 | balance-alb | Adaptive load balancing |

**Mode 1 (active-backup)** is the most common in production — simple, reliable, no switch configuration needed.

```bash
# Create a bond using nmcli
sudo nmcli connection add type bond \
  con-name bond0 \
  ifname bond0 \
  bond.options "mode=active-backup,miimon=100"

# Add slave interfaces to the bond
sudo nmcli connection add type ethernet \
  con-name bond0-slave1 \
  ifname eth1 \
  master bond0

sudo nmcli connection add type ethernet \
  con-name bond0-slave2 \
  ifname eth2 \
  master bond0

# Configure IP on the bond
sudo nmcli connection modify bond0 \
  ipv4.addresses 192.168.1.10/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8 8.8.4.4" \
  ipv4.method manual

# Bring up the bond
sudo nmcli connection up bond0

# Verify
cat /proc/net/bonding/bond0
# Shows which slave is active, link status, etc.

# Test failover: bring down one slave
sudo nmcli connection down bond0-slave1
# Traffic continues on bond0-slave2
```

### Network Bridging

Bridges connect two network segments at Layer 2. In Linux, they're essential for virtual machines and containers.

```bash
# Create a bridge
sudo nmcli connection add type bridge \
  con-name br0 \
  ifname br0

# Add physical interface to bridge
sudo nmcli connection add type ethernet \
  con-name br0-port1 \
  ifname eth1 \
  master br0

# Configure IP on bridge
sudo nmcli connection modify br0 \
  ipv4.addresses 192.168.1.20/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.method manual

# Bring up
sudo nmcli connection up br0

# Verify
bridge link show
ip addr show br0
```

> **War story**: A team set up LACP bonding (mode 4) on their servers but forgot to configure the matching port-channel on the network switch. Both interfaces came up, traffic flowed... sort of. Packets were being load-balanced across two independent links, causing out-of-order delivery, TCP retransmissions, and random 50% packet loss. The monitoring showed the interfaces as "up" with good throughput, but applications were timing out. It took two days to figure out because everyone assumed "the network is fine — both links are up." The fix was a 5-minute switch configuration. Lesson: bonding mode 4 (LACP) requires BOTH sides to be configured. Mode 1 (active-backup) is forgiving and needs no switch changes.

---

## Time Synchronization with Chrony

Accurate time is critical for log correlation, certificate validation, authentication (Kerberos), and distributed systems.

### Why Chrony Over ntpd

- **Faster initial sync** — Chrony syncs in seconds; ntpd can take minutes
- **Better for VMs** — Handles clock jumps from VM suspend/resume
- **Lower resource usage** — Lightweight and efficient
- **Default on modern distros** — RHEL 8+, Ubuntu 22.04+ use chrony

### Configuration

```bash
# Install chrony
sudo apt install -y chrony

# Check configuration
cat /etc/chrony/chrony.conf
```

Key configuration in `/etc/chrony/chrony.conf`:

```
# NTP servers (pool is preferred — auto-selects nearby servers)
pool ntp.ubuntu.com        iburst maxsources 4
pool 0.ubuntu.pool.ntp.org iburst maxsources 1
pool 1.ubuntu.pool.ntp.org iburst maxsources 1
pool 2.ubuntu.pool.ntp.org iburst maxsources 2

# Record the rate at which the system clock gains/drifts
driftfile /var/lib/chrony/chrony.drift

# Allow NTP clients from local network (if acting as NTP server)
# allow 192.168.1.0/24

# Step the clock if offset is larger than 1 second (first 3 updates)
makestep 1.0 3
```

```bash
# Start and enable
sudo systemctl enable --now chrony

# Check synchronization status
chronyc tracking
# Reference ID    : A9FEA9FE (time.cloudflare.com)
# Stratum         : 3
# Ref time (UTC)  : Sun Mar 22 14:30:00 2026
# System time     : 0.000000123 seconds fast of NTP time
# Last offset     : +0.000000045 seconds

# List NTP sources
chronyc sources -v

# Force immediate sync
sudo chronyc makestep

# Check if chrony is being used
timedatectl
# Look for: NTP service: active
```

### Setting Timezone

```bash
# List timezones
timedatectl list-timezones | grep America

# Set timezone
sudo timedatectl set-timezone UTC

# Verify
timedatectl
date
```

---

## SSH Hardening

SSH is the primary remote access method for Linux servers. Default configurations are rarely secure enough for production.

### Key-Based Authentication

```bash
# Generate an SSH key pair (on client machine)
ssh-keygen -t ed25519 -C "admin@company.com"
# Ed25519 is preferred over RSA — shorter, faster, more secure

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server

# Or manually:
cat ~/.ssh/id_ed25519.pub | ssh user@server "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Test key login
ssh -i ~/.ssh/id_ed25519 user@server
```

### Hardening sshd_config

Edit `/etc/ssh/sshd_config`:

```bash
# Disable password authentication (key-only)
PasswordAuthentication no

# Disable root login
PermitRootLogin no

# Use only SSH protocol 2
Protocol 2

# Limit to specific users or groups
AllowUsers admin deploy
# Or: AllowGroups sshusers

# Change default port (security through obscurity — helps with noise)
Port 2222

# Disable empty passwords
PermitEmptyPasswords no

# Set idle timeout (disconnect after 5 minutes of inactivity)
ClientAliveInterval 300
ClientAliveCountMax 0

# Limit authentication attempts
MaxAuthTries 3

# Disable X11 forwarding (unless needed)
X11Forwarding no

# Disable TCP forwarding (unless needed)
AllowTcpForwarding no
```

```bash
# Test configuration before restarting
sudo sshd -t
# No output = no errors

# Restart SSH
sudo systemctl restart sshd

# CRITICAL: Test from another terminal BEFORE closing your current session
# If config is wrong, you can still fix it from the existing session
```

### Fail2ban for Brute Force Protection

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Create local config (never edit jail.conf directly)
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

Edit `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
backend = systemd
maxretry = 3
bantime = 24h
```

```bash
# Start fail2ban
sudo systemctl enable --now fail2ban

# Check status
sudo fail2ban-client status sshd
# Status for the jail: sshd
# |- Filter
# |  |- Currently failed: 0
# |  `- Total failed: 12
# `- Actions
#    |- Currently banned: 2
#    `- Total banned: 5

# Unban an IP
sudo fail2ban-client set sshd unbanip 192.168.1.50

# View banned IPs
sudo fail2ban-client get sshd banned
```

---

## IPv4/IPv6 Configuration with nmcli

### IPv4 Configuration

```bash
# List connections
nmcli connection show

# Show device status
nmcli device status

# Configure static IPv4
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.1.100/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8 1.1.1.1" \
  ipv4.method manual

# Switch to DHCP
sudo nmcli connection modify "Wired connection 1" \
  ipv4.method auto

# Apply changes
sudo nmcli connection up "Wired connection 1"

# Verify
ip addr show
ip route show
```

### IPv6 Configuration

```bash
# Add static IPv6 address
sudo nmcli connection modify "Wired connection 1" \
  ipv6.addresses "fd00::100/64" \
  ipv6.gateway "fd00::1" \
  ipv6.method manual

# Enable both IPv4 and IPv6
sudo nmcli connection modify "Wired connection 1" \
  ipv4.method manual \
  ipv4.addresses 192.168.1.100/24 \
  ipv6.method manual \
  ipv6.addresses "fd00::100/64"

# Disable IPv6 (if needed)
sudo nmcli connection modify "Wired connection 1" \
  ipv6.method disabled

# Apply
sudo nmcli connection up "Wired connection 1"

# Verify
ip -6 addr show
ip -6 route show
```

### Adding Static Routes

```bash
# Add a static route
sudo nmcli connection modify "Wired connection 1" \
  +ipv4.routes "10.10.0.0/16 192.168.1.254"

# Add route with metric
sudo nmcli connection modify "Wired connection 1" \
  +ipv4.routes "10.10.0.0/16 192.168.1.254 100"

# Apply
sudo nmcli connection up "Wired connection 1"

# Verify
ip route show
```

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| `firewall-cmd` without `--permanent` | Rule lost on reload/reboot | Add `--permanent` and `--reload` |
| Blocking SSH before adding allow rule | Locked out of server | Always allow SSH first, then set default deny |
| Bonding mode 4 without switch config | Packet loss, retransmissions | Use mode 1 (active-backup) or configure switch |
| `PasswordAuthentication no` without testing key login | Locked out completely | Test key auth in separate session first |
| No `nofail` on network mounts in fstab | Server won't boot if NFS down | Always use `nofail,_netdev` for network mounts |
| Forgetting `sysctl ip_forward` for NAT | Packets arrive but don't get forwarded | Enable `net.ipv4.ip_forward=1` |
| Editing `jail.conf` instead of `jail.local` | Changes overwritten on update | Always create and edit `jail.local` |

---

## Quiz

Test your network administration knowledge:

**Question 1**: What is the difference between a runtime and permanent firewalld rule? How do you safely test a new rule?

<details>
<summary>Show Answer</summary>

- **Runtime**: Active immediately but lost on `firewall-cmd --reload` or reboot
- **Permanent**: Saved to config but not active until `--reload`

Safe testing workflow:
1. Add rule without `--permanent` (runtime only)
2. Test that it works as expected
3. If good: `firewall-cmd --runtime-to-permanent`
4. If bad: `firewall-cmd --reload` to revert

This prevents lockouts from misconfigured rules.

</details>

**Question 2**: You need a server with two NICs to survive a cable failure. Which bonding mode requires no switch configuration?

<details>
<summary>Show Answer</summary>

**Mode 1 (active-backup)** requires no switch configuration. One interface is active at a time; the other takes over if the primary fails.

Mode 4 (LACP/802.3ad) provides better throughput but requires matching configuration on the network switch.

</details>

**Question 3**: What command enables IP forwarding permanently, and why is it needed for NAT?

<details>
<summary>Show Answer</summary>

```bash
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-ip-forward.conf
sudo sysctl -p /etc/sysctl.d/99-ip-forward.conf
```

IP forwarding is needed because by default, the Linux kernel drops packets that aren't destined for any of its own IP addresses. For NAT/masquerading to work, the kernel must forward packets from the internal network out through the external interface.

</details>

**Question 4**: Name three SSH hardening measures that should be applied to any production server.

<details>
<summary>Show Answer</summary>

1. **Disable password authentication** — `PasswordAuthentication no` (use key-based only)
2. **Disable root login** — `PermitRootLogin no`
3. **Install fail2ban** — Automatically bans IPs after failed login attempts

Additional measures: change default port, set `MaxAuthTries 3`, configure `AllowUsers`/`AllowGroups`, disable X11 forwarding.

</details>

**Question 5**: A server's clock is 30 seconds off. What tool and command would you use to fix it immediately?

<details>
<summary>Show Answer</summary>

```bash
# Force immediate time step with chrony
sudo chronyc makestep
```

Chrony will immediately step the clock to match the NTP source. For ongoing accuracy, ensure chrony is enabled: `sudo systemctl enable --now chrony`.

Check status with `chronyc tracking` and `timedatectl`.

</details>

---

## Hands-On Exercise: Secure a Server from Scratch

**Objective**: Configure firewall rules, harden SSH, set up NTP, and configure network interfaces.

**Environment**: A Linux VM (Ubuntu 22.04 preferred) with at least one network interface.

### Task 1: Configure firewalld

```bash
# Install and start firewalld
sudo apt install -y firewalld
sudo systemctl enable --now firewalld

# Set default zone to public
sudo firewall-cmd --set-default-zone=public

# Allow only SSH and HTTPS
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --add-service=https --permanent

# Add a custom port for your application
sudo firewall-cmd --add-port=8443/tcp --permanent

# Block a test IP with rich rule
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="10.99.99.99" drop' --permanent

# Reload and verify
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

**Expected output**: Default zone is public with ssh, https, and port 8443 allowed, plus a rich rule blocking 10.99.99.99.

### Task 2: Harden SSH

```bash
# Backup original config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# Generate a key pair (if you don't have one)
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519

# Add your key to authorized_keys
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Harden sshd_config
sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
sudo sed -i 's/#ClientAliveInterval.*/ClientAliveInterval 300/' /etc/ssh/sshd_config
sudo sed -i 's/X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config

# Test config
sudo sshd -t

# Restart
sudo systemctl restart sshd
```

### Task 3: Configure Time Synchronization

```bash
# Install and enable chrony
sudo apt install -y chrony
sudo systemctl enable --now chrony

# Set timezone to UTC
sudo timedatectl set-timezone UTC

# Force sync
sudo chronyc makestep

# Verify
chronyc tracking
timedatectl
```

### Task 4: Configure a Static IP with nmcli

```bash
# Show current connections
nmcli connection show

# Create a new connection with static IP (adjust interface name)
sudo nmcli connection add type ethernet \
  con-name static-eth0 \
  ifname eth0 \
  ipv4.addresses 192.168.1.200/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8 1.1.1.1" \
  ipv4.method manual

# Verify (don't activate if this is your only connection over SSH!)
nmcli connection show static-eth0
```

### Success Criteria

- [ ] firewalld running with custom rules (ssh, https, 8443, rich rule)
- [ ] SSH hardened: root login disabled, max auth tries limited
- [ ] Chrony running and time synchronized
- [ ] Static IP configured via nmcli
- [ ] All changes persist across reboot (`--permanent`, config files)

### Cleanup

```bash
# Restore SSH config
sudo cp /etc/ssh/sshd_config.bak /etc/ssh/sshd_config
sudo systemctl restart sshd

# Remove firewalld test rules
sudo firewall-cmd --remove-service=https --permanent
sudo firewall-cmd --remove-port=8443/tcp --permanent
sudo firewall-cmd --remove-rich-rule='rule family="ipv4" source address="10.99.99.99" drop' --permanent
sudo firewall-cmd --reload

# Remove test nmcli connection
sudo nmcli connection delete static-eth0
```

---

## Next Module

You've now covered the key LFCS gaps in storage and networking. Return to the [LFCS Learning Path](../../k8s/lfcs/) to review remaining study areas, or continue strengthening your Linux fundamentals with [Module 5.1: The USE Method](performance/module-5.1-use-method.md) for performance analysis.
