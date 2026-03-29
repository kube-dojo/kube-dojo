---
title: "Module 6.4: Network Debugging"
slug: linux/operations/troubleshooting/module-6.4-network-debugging
sidebar:
  order: 5
---
> **Linux Troubleshooting** | Complexity: `[COMPLEX]` | Time: 30-35 min

## Prerequisites

Before starting this module:
- **Required**: [Module 3.1: TCP/IP Essentials](../../foundations/networking/module-3.1-tcp-ip-essentials/)
- **Required**: [Module 3.4: iptables & netfilter](../../foundations/networking/module-3.4-iptables-netfilter/)
- **Helpful**: [Module 6.1: Systematic Troubleshooting](../module-6.1-systematic-troubleshooting/)

---

## Why This Module Matters

"The network is down" is the most common blame target for application issues. Network debugging skills let you verify whether the network is actually the problem—and pinpoint exactly where.

Understanding network debugging helps you:

- **Prove network issues** — Or rule them out
- **Debug connectivity** — DNS, firewalls, routing
- **Analyze traffic** — See what's actually happening
- **Troubleshoot Kubernetes** — Service discovery, pod networking

Most "network problems" turn out to be configuration or application issues.

---

## Did You Know?

- **tcpdump can capture gigabytes per second** — Without proper filtering, you'll fill disks fast. Always use filters in production.

- **ss replaced netstat** — netstat parses /proc files, ss talks directly to the kernel. ss is faster and shows more information.

- **DNS failures cause cascading issues** — A slow or broken DNS can make everything seem slow. Always check DNS early.

- **TCP handshake reveals a lot** — SYN → SYN-ACK → ACK takes three packets. If it fails, you know connection isn't established.

---

## Network Debugging Methodology

### Layer-by-Layer Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                    NETWORK DEBUGGING                             │
│                                                                  │
│  Start at layer 1, work up:                                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Layer 7: Application   curl, wget, app-specific      │       │
│  ├──────────────────────────────────────────────────────┤       │
│  │ Layer 4: Transport     ss, netstat, tcpdump (ports)  │       │
│  ├──────────────────────────────────────────────────────┤       │
│  │ Layer 3: Network       ping, traceroute, ip route    │       │
│  ├──────────────────────────────────────────────────────┤       │
│  │ Layer 2: Data Link     ip link, arp                  │       │
│  ├──────────────────────────────────────────────────────┤       │
│  │ Layer 1: Physical      ethtool, cable, switch        │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  Each layer depends on layers below                             │
│  If layer 3 fails, layer 7 can't work                          │
└─────────────────────────────────────────────────────────────────┘
```

### Quick Connectivity Check

```bash
# 1. Interface up?
ip link show eth0

# 2. IP address assigned?
ip addr show eth0

# 3. Default gateway?
ip route | grep default

# 4. Can reach gateway?
ping -c 3 $(ip route | grep default | awk '{print $3}')

# 5. DNS working?
dig google.com +short

# 6. Can reach internet?
curl -I --max-time 5 https://google.com
```

---

## Basic Tools

### ping

```bash
# Basic connectivity
ping -c 4 192.168.1.1

# Continuous until stopped
ping 192.168.1.1

# Set packet size (MTU testing)
ping -s 1472 192.168.1.1  # 1472 + 28 header = 1500

# Flood ping (need root, careful!)
sudo ping -f -c 1000 192.168.1.1

# Set interface
ping -I eth0 192.168.1.1
```

### traceroute / tracepath

```bash
# Trace route to destination
traceroute google.com
# Shows each hop and latency

# Or tracepath (no root needed)
tracepath google.com

# TCP traceroute (bypasses ICMP filters)
traceroute -T -p 443 google.com

# MTU discovery
tracepath -n google.com | grep pmtu
```

### DNS Tools

```bash
# Quick lookup
dig google.com +short
# 142.250.185.206

# Full query
dig google.com
# Shows query time, server used, full response

# Specific record types
dig MX google.com
dig TXT google.com
dig NS google.com

# Query specific server
dig @8.8.8.8 google.com

# Reverse lookup
dig -x 8.8.8.8

# Check DNS resolution chain
dig +trace google.com
```

---

## ss (Socket Statistics)

### Basic Usage

```bash
# All sockets
ss

# Listening sockets
ss -l

# TCP sockets
ss -t

# UDP sockets
ss -u

# Common combination: listening TCP with process
ss -tlnp
# -t = TCP
# -l = listening
# -n = numeric (no DNS)
# -p = process (needs root for others' processes)
```

### Filtering

```bash
# By state
ss -t state established
ss -t state time-wait
ss -t state close-wait

# By port
ss -tn sport = :22          # Source port 22
ss -tn dport = :443         # Destination port 443
ss -tn '( sport = :22 or dport = :22 )'

# By address
ss -tn dst 192.168.1.0/24

# Complex filters
ss -tn 'dst 192.168.1.1 and dport = :80'
```

### Connection Analysis

```bash
# All connections with process info
sudo ss -tunap

# Connection counts by state
ss -tan | awk '{print $1}' | sort | uniq -c

# Many TIME_WAIT? Normal for high traffic
# Many CLOSE_WAIT? App not closing connections properly

# Connections per remote IP
ss -tn | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head

# Queue sizes (send/recv buffers)
ss -tnm
```

---

## tcpdump

### Basic Capture

```bash
# All traffic on interface
sudo tcpdump -i eth0

# Limit packets
sudo tcpdump -i eth0 -c 100

# Don't resolve names (faster)
sudo tcpdump -i eth0 -n

# Show hex dump
sudo tcpdump -i eth0 -X

# Write to file
sudo tcpdump -i eth0 -w /tmp/capture.pcap

# Read from file
tcpdump -r /tmp/capture.pcap
```

### Filtering

```bash
# By host
sudo tcpdump -i eth0 host 192.168.1.1

# By port
sudo tcpdump -i eth0 port 80
sudo tcpdump -i eth0 port 80 or port 443

# By protocol
sudo tcpdump -i eth0 tcp
sudo tcpdump -i eth0 udp
sudo tcpdump -i eth0 icmp

# Source or destination
sudo tcpdump -i eth0 src host 192.168.1.1
sudo tcpdump -i eth0 dst port 443

# Complex filters
sudo tcpdump -i eth0 'tcp port 80 and host 192.168.1.1'
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0'  # SYN packets only
```

### Useful Options

```bash
# Verbose output
sudo tcpdump -v -i eth0
sudo tcpdump -vv -i eth0  # More verbose

# ASCII output
sudo tcpdump -A -i eth0 port 80  # See HTTP headers

# Line buffered (for piping)
sudo tcpdump -l -i eth0 | grep pattern

# Snapshot length
sudo tcpdump -s 96 -i eth0  # Capture only headers
sudo tcpdump -s 0 -i eth0   # Capture full packets
```

### Common Patterns

```bash
# See TCP handshakes
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0'

# See HTTP requests
sudo tcpdump -i eth0 -A 'tcp port 80 and tcp[32:4] = 0x47455420'  # GET
sudo tcpdump -i eth0 -A 'tcp port 80 and tcp[32:4] = 0x504f5354'  # POST

# See DNS queries
sudo tcpdump -i eth0 udp port 53

# Capture for Wireshark
sudo tcpdump -i eth0 -w capture.pcap -s 0 port 443
# Then open capture.pcap in Wireshark
```

---

## Debugging Common Issues

### "Connection Refused"

```bash
# Means: TCP connection reached host, but nothing listening

# 1. Check if service is listening
ss -tlnp | grep :80

# 2. Check if on correct interface
ss -tlnp | grep :80
# 127.0.0.1:80 = only localhost
# 0.0.0.0:80 = all interfaces
# :::80 = all IPv6

# 3. Check firewall
sudo iptables -L -n | grep 80

# 4. Check service status
systemctl status nginx
```

### "Connection Timed Out"

```bash
# Means: No response at all (firewall, routing, or host down)

# 1. Can you reach the host at all?
ping target_host

# 2. What happens to packets?
traceroute target_host

# 3. Is it just that port?
nc -zv target_host 22  # Try SSH
nc -zv target_host 80  # Try HTTP

# 4. Check routing
ip route get target_ip

# 5. Capture and see what's happening
sudo tcpdump -i eth0 host target_host
```

### "No Route to Host"

```bash
# Means: Kernel doesn't know how to reach this network

# 1. Check routing table
ip route
ip route get target_ip

# 2. Is default route present?
ip route | grep default

# 3. Is gateway reachable?
ping $(ip route | grep default | awk '{print $3}')

# 4. Check interface is up
ip link show
ip addr show
```

### DNS Issues

```bash
# 1. Is DNS configured?
cat /etc/resolv.conf

# 2. Can reach DNS server?
ping $(grep nameserver /etc/resolv.conf | head -1 | awk '{print $2}')

# 3. Does query work?
dig @8.8.8.8 google.com  # Use known-good DNS
dig google.com           # Use configured DNS

# 4. Check for NXDOMAIN vs timeout
dig nonexistent.google.com  # NXDOMAIN is normal
dig google.com              # Timeout means DNS issue

# 5. Slow DNS?
dig google.com | grep "Query time"
# >100ms is slow
```

---

## Kubernetes Network Debugging

### Pod Networking

```bash
# Get pod IP
kubectl get pod my-pod -o wide

# Check connectivity from another pod
kubectl exec other-pod -- curl my-pod-ip:8080
kubectl exec other-pod -- ping my-pod-ip

# DNS resolution
kubectl exec my-pod -- nslookup kubernetes
kubectl exec my-pod -- nslookup my-service

# Check service endpoints
kubectl get endpoints my-service
```

### Service Debugging

```bash
# Does service exist?
kubectl get svc my-service

# Does it have endpoints?
kubectl get endpoints my-service
# Empty = no pods matching selector

# Test from inside cluster
kubectl run debug --rm -it --image=alpine -- sh
# Inside: wget -qO- my-service:80

# Check DNS
kubectl exec my-pod -- nslookup my-service.default.svc.cluster.local
```

### Node Networking

```bash
# On node, check CNI
ls /etc/cni/net.d/

# Check kube-proxy
iptables -t nat -L KUBE-SERVICES -n | head -20

# Check node can reach pod network
ip route | grep -E "10.244|10.96"

# tcpdump on node
sudo tcpdump -i any host <pod-ip>
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| tcpdump without filter | Massive output, fill disk | Always filter |
| Forgetting -n | DNS lookups slow things down | Use numeric output |
| Blaming network first | Missing app issue | Verify with tcpdump |
| Ignoring firewall | Rules drop traffic | Check iptables |
| Wrong interface | Traffic on different NIC | Check with ip link |
| Not checking DNS | Everything seems slow | dig first |

---

## Quiz

### Question 1
How do you check what's listening on port 443?

<details>
<summary>Show Answer</summary>

```bash
# Best option
ss -tlnp | grep :443

# Or netstat (older)
netstat -tlnp | grep :443

# Or lsof
lsof -i :443
```

Output shows:
- State (LISTEN)
- Local address (0.0.0.0:443 or 127.0.0.1:443)
- Process name and PID (-p flag, needs root)

</details>

### Question 2
What's the difference between "connection refused" and "connection timed out"?

<details>
<summary>Show Answer</summary>

**Connection refused**:
- TCP RST packet received
- Host is reachable
- Nothing listening on port
- Or firewall sending RST

**Connection timed out**:
- No response at all
- Host unreachable (down, routing, firewall DROP)
- Packets being silently dropped

"Refused" is actually good news — you reached the host. "Timeout" means connectivity problem somewhere in the path.

</details>

### Question 3
How do you capture only TCP SYN packets?

<details>
<summary>Show Answer</summary>

```bash
sudo tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'
```

This captures:
- SYN (connection initiation)
- SYN-ACK (connection response)

For only SYN (no SYN-ACK):
```bash
sudo tcpdump -i eth0 'tcp[tcpflags] == tcp-syn'
```

Useful for seeing connection attempts without all the data.

</details>

### Question 4
A service returns "502 Bad Gateway". How do you determine if it's network or application?

<details>
<summary>Show Answer</summary>

502 means proxy reached backend but backend failed. Steps:

```bash
# 1. Check if backend is listening
ss -tlnp | grep :backend_port

# 2. Test connectivity to backend directly
curl http://backend:port/health

# 3. Capture traffic
sudo tcpdump -i any port backend_port

# 4. Check backend logs
journalctl -u backend-service

# 5. Check proxy error logs
tail /var/log/nginx/error.log
```

If backend responds correctly to direct requests but proxy shows 502, the issue is proxy configuration or intermittent backend failures.

</details>

### Question 5
How do you find which process has many TIME_WAIT connections?

<details>
<summary>Show Answer</summary>

TIME_WAIT is a TCP state after close — normal for clients.

```bash
# Count TIME_WAIT
ss -tan state time-wait | wc -l

# By remote address
ss -tan state time-wait | awk '{print $4}' | cut -d: -f1 | sort | uniq -c | sort -rn

# The process that created the connection is no longer associated
# TIME_WAIT is kernel state, not process state

# To find which application is creating connections:
# 1. Look at ESTABLISHED first
ss -tnp state established | grep ":target_port"

# 2. Monitor in real-time
watch 'ss -tan state time-wait | wc -l'
```

Many TIME_WAIT is normal for high-traffic servers.

</details>

---

## Hands-On Exercise

### Network Debugging Practice

**Objective**: Use network debugging tools to diagnose connectivity.

**Environment**: Linux system with network access

#### Part 1: Basic Connectivity

```bash
# 1. Check your network config
ip addr show
ip route

# 2. Test gateway
GATEWAY=$(ip route | grep default | awk '{print $3}')
echo "Gateway: $GATEWAY"
ping -c 3 $GATEWAY

# 3. Test internet
ping -c 3 8.8.8.8

# 4. Test DNS
dig google.com +short
```

#### Part 2: ss Socket Analysis

```bash
# 1. Listening sockets
ss -tlnp

# 2. All connections
ss -tan | head -20

# 3. Count by state
ss -tan | awk 'NR>1 {print $1}' | sort | uniq -c

# 4. Filter to specific port
ss -tn 'dport = :443' | head -10

# 5. Show process info (needs root)
sudo ss -tlnp | grep LISTEN
```

#### Part 3: tcpdump Basics

```bash
# 1. Capture any traffic (brief)
sudo timeout 5 tcpdump -i any -c 20 -n

# 2. Capture ping
# In one terminal:
sudo tcpdump -i any icmp
# In another:
ping -c 3 8.8.8.8

# 3. Capture DNS
sudo tcpdump -i any udp port 53 -c 10 &
dig google.com
# Wait for capture

# 4. Capture HTTP (if you have a web server)
sudo tcpdump -i any tcp port 80 -c 20 -A
```

#### Part 4: Diagnose Connectivity

```bash
# Simulate debugging flow

# 1. Check if service reachable
nc -zv google.com 443 && echo "Port 443 reachable"

# 2. Check DNS resolution
dig google.com +short || echo "DNS failed"

# 3. Check routing
ip route get 8.8.8.8

# 4. Traceroute
tracepath -n google.com 2>/dev/null | head -10 || traceroute -n google.com 2>/dev/null | head -10
```

#### Part 5: DNS Debugging

```bash
# 1. Check configured DNS
cat /etc/resolv.conf

# 2. Test DNS server
dig @$(grep nameserver /etc/resolv.conf | head -1 | awk '{print $2}') google.com +short

# 3. Query time
dig google.com | grep "Query time"

# 4. Trace resolution
dig +trace google.com | tail -20
```

#### Part 6: Create and Debug

```bash
# Start a simple server (Python 3)
python3 -m http.server 8888 &
SERVER_PID=$!
sleep 2

# 1. Find it listening
ss -tlnp | grep 8888

# 2. Test connection
curl -I http://localhost:8888

# 3. Capture the traffic
sudo timeout 5 tcpdump -i lo port 8888 -n &
sleep 1
curl -s http://localhost:8888 > /dev/null

# 4. Clean up
kill $SERVER_PID 2>/dev/null
```

### Success Criteria

- [ ] Verified network configuration with ip
- [ ] Analyzed sockets with ss
- [ ] Captured packets with tcpdump
- [ ] Tested DNS resolution with dig
- [ ] Traced network path with traceroute/tracepath
- [ ] Debugged connectivity to a service

---

## Key Takeaways

1. **Layer by layer** — Start from physical, work up to application

2. **ss over netstat** — Faster, more features, better filtering

3. **tcpdump proves problems** — Captures show exactly what's happening

4. **DNS first** — Many "network" issues are DNS issues

5. **Filter tcpdump** — Unfiltered captures are useless and dangerous

---

## What's Next?

In **Module 7.1: Bash Fundamentals**, you'll learn shell scripting basics—automating the debugging and operational tasks you've learned.

---

## Further Reading

- [tcpdump Man Page](https://www.tcpdump.org/manpages/tcpdump.1.html)
- [ss Man Page](https://man7.org/linux/man-pages/man8/ss.8.html)
- [Wireshark User Guide](https://www.wireshark.org/docs/wsug_html/)
- [Kubernetes Debugging Services](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/)
