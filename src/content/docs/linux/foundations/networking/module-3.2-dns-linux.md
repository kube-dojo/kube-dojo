---
title: "Module 3.2: DNS in Linux"
slug: linux/foundations/networking/module-3.2-dns-linux
sidebar:
  order: 3
---
> **Linux Foundations** | Complexity: `[MEDIUM]` | Time: 25-30 min

## Prerequisites

Before starting this module:
- **Required**: [Module 3.1: TCP/IP Essentials](../module-3.1-tcp-ip-essentials/)
- **Helpful**: Understanding of hostname resolution concepts

---

## Why This Module Matters

DNS translates names to IP addresses. Every time you access a service by name—whether `google.com` or `my-service.default.svc.cluster.local`—DNS is involved.

Understanding DNS in Linux helps you:

- **Debug Kubernetes service discovery** — Why can't my pod find the service?
- **Troubleshoot resolution failures** — "Name or service not known"
- **Configure CoreDNS** — Kubernetes DNS server
- **Understand /etc/resolv.conf** — How containers find DNS servers

DNS problems are some of the most common (and frustrating) issues in Kubernetes. This module arms you with the knowledge to solve them.

---

## Did You Know?

- **DNS was created in 1983** to replace the HOSTS.TXT file that was manually distributed to every computer on ARPANET. Yes, there used to be a single file listing every hostname on the internet!

- **Kubernetes CoreDNS handles millions of queries per hour** in busy clusters. Every service lookup, every pod resolution, every external DNS query flows through it.

- **The `search` directive in resolv.conf** is why you can just type `my-service` instead of `my-service.default.svc.cluster.local`. It automatically appends domain suffixes.

- **DNS uses port 53** for both UDP (most queries) and TCP (large responses, zone transfers). If port 53 is blocked, DNS breaks.

---

## How DNS Resolution Works

### The Resolution Process

```
┌─────────────────────────────────────────────────────────────────┐
│              DNS RESOLUTION PROCESS                              │
│                                                                  │
│  Application: "Connect to api.example.com"                      │
│       │                                                          │
│       ▼                                                          │
│  1. Check /etc/hosts                                            │
│     ┌─────────────────────────────────────────┐                 │
│     │ 127.0.0.1  localhost                    │                 │
│     │ 192.168.1.10 api.example.com  ← Found?  │                 │
│     └─────────────────────────────────────────┘                 │
│       │ Not found                                                │
│       ▼                                                          │
│  2. Check /etc/resolv.conf for DNS server                       │
│     ┌─────────────────────────────────────────┐                 │
│     │ nameserver 10.96.0.10                   │                 │
│     │ search default.svc.cluster.local ...    │                 │
│     └─────────────────────────────────────────┘                 │
│       │                                                          │
│       ▼                                                          │
│  3. Query DNS server (10.96.0.10)                               │
│       │                                                          │
│       ▼                                                          │
│  4. DNS server returns: 93.184.216.34                           │
│       │                                                          │
│       ▼                                                          │
│  5. Application connects to 93.184.216.34                       │
└─────────────────────────────────────────────────────────────────┘
```

### Resolution Order (/etc/nsswitch.conf)

```bash
cat /etc/nsswitch.conf | grep hosts

# Output: hosts: files dns
# Meaning: Check files (/etc/hosts) first, then DNS
```

---

## /etc/resolv.conf

The DNS configuration file.

### Format

```bash
# /etc/resolv.conf

# DNS servers to query (up to 3)
nameserver 10.96.0.10    # Primary DNS
nameserver 8.8.8.8       # Secondary DNS

# Domain search list
search default.svc.cluster.local svc.cluster.local cluster.local

# Options
options ndots:5 timeout:2 attempts:2
```

### Key Directives

| Directive | Purpose | Example |
|-----------|---------|---------|
| nameserver | DNS server IP | nameserver 8.8.8.8 |
| search | Domain suffixes to try | search example.com |
| domain | Default domain | domain example.com |
| options | Resolver behavior | options ndots:5 |

### The ndots Option

**ndots** determines when to use the search list:

```
ndots:5 means:
- If hostname has < 5 dots → try search domains first
- If hostname has >= 5 dots → try as absolute first

Example with ndots:5 and search: default.svc.cluster.local

Query: "api" (0 dots < 5)
  Try: api.default.svc.cluster.local  ← First!
  Try: api.svc.cluster.local
  Try: api.cluster.local
  Try: api  (absolute)

Query: "api.example.com" (2 dots < 5)
  Try: api.example.com.default.svc.cluster.local  ← Wastes time!
  Try: api.example.com.svc.cluster.local
  Try: api.example.com.cluster.local
  Try: api.example.com  ← What we wanted

Query: "a.b.c.d.example.com" (4 dots < 5)
  Still tries search domains first! (need 5+ dots)
```

### Kubernetes resolv.conf

```bash
# In a Kubernetes pod
cat /etc/resolv.conf

# Output:
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

This means:
- DNS server is CoreDNS (10.96.0.10)
- Short names try cluster domains first
- ndots:5 optimizes for internal service discovery

---

## /etc/hosts

Static hostname mappings.

```bash
# /etc/hosts
127.0.0.1       localhost
::1             localhost
192.168.1.100   myserver.local myserver
10.0.0.50       database.internal db
```

### Priority

- /etc/hosts is checked BEFORE DNS
- Useful for testing, overrides, local development
- Kubernetes uses it for pod hostname

```bash
# In a Kubernetes pod
cat /etc/hosts

# Output:
127.0.0.1       localhost
10.244.1.5      my-pod-name
```

---

## DNS Query Tools

### dig (Domain Information Groper)

The most powerful DNS tool.

```bash
# Basic query
dig example.com

# Query specific record type
dig example.com A      # IPv4 address
dig example.com AAAA   # IPv6 address
dig example.com MX     # Mail server
dig example.com NS     # Name servers
dig example.com TXT    # Text records
dig example.com CNAME  # Canonical name

# Short output
dig +short example.com

# Use specific DNS server
dig @8.8.8.8 example.com

# Trace full resolution path
dig +trace example.com

# Reverse lookup
dig -x 8.8.8.8
```

### Example dig Output

```bash
dig example.com

; <<>> DiG 9.16.1 <<>> example.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 12345
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;example.com.                   IN      A

;; ANSWER SECTION:
example.com.            3600    IN      A       93.184.216.34

;; Query time: 25 msec
;; SERVER: 10.96.0.10#53(10.96.0.10)
;; WHEN: Mon Dec 01 10:00:00 UTC 2024
;; MSG SIZE  rcvd: 56
```

### nslookup

Simpler alternative to dig.

```bash
# Basic lookup
nslookup example.com

# Use specific server
nslookup example.com 8.8.8.8

# Reverse lookup
nslookup 8.8.8.8
```

### host

Simplest DNS tool.

```bash
# Basic lookup
host example.com

# Reverse lookup
host 8.8.8.8

# Find mail servers
host -t MX example.com
```

### getent

Uses system resolver (respects /etc/hosts and nsswitch.conf).

```bash
# Resolve like applications do
getent hosts example.com

# This respects /etc/hosts!
```

---

## Kubernetes DNS

### CoreDNS

Kubernetes uses CoreDNS for cluster DNS.

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES DNS                                │
│                                                                  │
│  Pod Query: "my-service.default.svc.cluster.local"              │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    CoreDNS                               │    │
│  │                 (10.96.0.10)                             │    │
│  │                                                          │    │
│  │  Cluster queries:                                        │    │
│  │    *.cluster.local → Answer from Kubernetes API         │    │
│  │                                                          │    │
│  │  External queries:                                       │    │
│  │    *.* → Forward to upstream DNS                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│       │                                                          │
│       ▼                                                          │
│  Returns: 10.96.45.123 (Service ClusterIP)                      │
└─────────────────────────────────────────────────────────────────┘
```

### Kubernetes DNS Names

```
Service: my-service.namespace.svc.cluster.local
         │         │         │   │
         │         │         │   └── Cluster domain
         │         │         └── "svc" = service
         │         └── Namespace
         └── Service name

Pod (with hostname): pod-name.subdomain.namespace.svc.cluster.local
```

### Testing DNS in Kubernetes

```bash
# Run a test pod
kubectl run dnstest --image=busybox --rm -it -- sh

# Inside the pod:
nslookup kubernetes
nslookup kubernetes.default.svc.cluster.local

# Check resolv.conf
cat /etc/resolv.conf

# Test external DNS
nslookup google.com
```

### Common Kubernetes DNS Issues

```bash
# Issue: "nslookup: can't resolve 'kubernetes'"

# Debug steps:
# 1. Check CoreDNS is running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 2. Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# 3. Check CoreDNS service
kubectl get svc -n kube-system kube-dns

# 4. Verify pod can reach DNS service
kubectl run test --image=busybox --rm -it -- \
  nc -zv 10.96.0.10 53
```

---

## DNS Caching

### systemd-resolved

Modern Ubuntu/Debian uses systemd-resolved for DNS caching.

```bash
# Check status
systemd-resolve --status

# Flush cache
systemd-resolve --flush-caches

# Statistics
systemd-resolve --statistics
```

### DNS Cache Issues

```bash
# Symptom: Old DNS record still being used

# Solutions:
# 1. Flush local cache
sudo systemd-resolve --flush-caches

# 2. Check TTL in response
dig example.com | grep -E "^example.*IN.*A"
# The number after IN is TTL in seconds

# 3. In Kubernetes, restart CoreDNS if needed
kubectl rollout restart deployment coredns -n kube-system
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Missing trailing dot in DNS | `example.com` vs `example.com.` | Add dot for FQDN in configs |
| Wrong ndots setting | Slow DNS resolution | Tune ndots or use FQDNs |
| /etc/hosts not checked | Entry ignored | Verify nsswitch.conf order |
| DNS over TCP blocked | Large queries fail | Ensure port 53 TCP open |
| External DNS in pods | Can't resolve public domains | Check CoreDNS upstream config |
| resolv.conf overwritten | Changes lost | Use proper DNS config method |

---

## Quiz

### Question 1
What does the `search` directive in /etc/resolv.conf do?

<details>
<summary>Show Answer</summary>

The `search` directive lists domain suffixes to append when resolving short hostnames.

Example:
```
search example.com corp.internal
```

Query for `server` tries:
1. `server.example.com`
2. `server.corp.internal`
3. `server` (absolute)

This is how Kubernetes lets you use short service names like `redis` instead of `redis.default.svc.cluster.local`.

</details>

### Question 2
Why might `dig kubernetes` fail but `getent hosts kubernetes` succeed in a Kubernetes pod?

<details>
<summary>Show Answer</summary>

`dig` queries DNS directly without using the search domains unless you specify them.

`getent hosts` uses the system resolver, which:
1. Checks /etc/hosts first
2. Applies search domains from /etc/resolv.conf

In Kubernetes, `dig kubernetes` would need the full name or search domains:
```bash
dig kubernetes.default.svc.cluster.local  # Works
dig +search kubernetes                      # Uses search domains
getent hosts kubernetes                     # Uses system resolver
```

</details>

### Question 3
What does ndots:5 mean and why does Kubernetes use it?

<details>
<summary>Show Answer</summary>

`ndots:5` means:
- Names with **fewer than 5 dots**: Try search domains first
- Names with **5 or more dots**: Try as absolute name first

Kubernetes uses ndots:5 because:
- Service FQDNs have 4 dots: `my-service.default.svc.cluster.local`
- With ndots:5, short names try cluster domains first (faster for internal)
- External domains (usually 1-2 dots) also try search first, which can be slower

</details>

### Question 4
How do you find what DNS server a Kubernetes pod is using?

<details>
<summary>Show Answer</summary>

```bash
# Option 1: Check resolv.conf
kubectl exec pod-name -- cat /etc/resolv.conf

# Option 2: Check the kube-dns service
kubectl get svc -n kube-system kube-dns -o wide

# The nameserver in resolv.conf should match the kube-dns ClusterIP
```

</details>

### Question 5
What's the difference between `dig example.com` and `dig +short example.com`?

<details>
<summary>Show Answer</summary>

- `dig example.com` — Full output including headers, question, answer, authority, timing
- `dig +short example.com` — Only the answer (just the IP address)

```bash
dig example.com
# ... lots of output ...
# example.com.  3600  IN  A  93.184.216.34
# ... query time, server, etc ...

dig +short example.com
# 93.184.216.34
```

</details>

---

## Hands-On Exercise

### DNS Exploration

**Objective**: Master DNS troubleshooting in Linux and Kubernetes.

**Environment**: Linux system (bonus: Kubernetes cluster)

#### Part 1: Local DNS Configuration

```bash
# 1. Check your DNS servers
cat /etc/resolv.conf

# 2. Check resolution order
cat /etc/nsswitch.conf | grep hosts

# 3. Check hosts file
cat /etc/hosts

# 4. Test resolution using system resolver
getent hosts localhost
getent hosts google.com
```

#### Part 2: DNS Queries with dig

```bash
# 1. Basic query
dig google.com

# 2. Short output
dig +short google.com

# 3. Query different record types
dig google.com A
dig google.com MX
dig google.com NS
dig +short google.com AAAA

# 4. Use specific DNS server
dig @8.8.8.8 google.com
dig @1.1.1.1 google.com

# 5. Reverse lookup
dig -x 8.8.8.8

# 6. Trace resolution
dig +trace google.com
```

#### Part 3: Understanding Search Domains

```bash
# 1. Check your search domains
grep search /etc/resolv.conf

# 2. Test with search domains
dig +search myservice  # Uses search domains
dig myservice          # May or may not (depends on ndots)

# 3. Check ndots
grep ndots /etc/resolv.conf
```

#### Part 4: Kubernetes DNS (if available)

```bash
# 1. Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 2. Run a test pod
kubectl run dnstest --image=busybox --rm -it --restart=Never -- sh

# Inside the pod:
# 3. Check resolv.conf
cat /etc/resolv.conf

# 4. Resolve cluster services
nslookup kubernetes
nslookup kubernetes.default
nslookup kubernetes.default.svc.cluster.local

# 5. Resolve external
nslookup google.com

# 6. Exit
exit
```

#### Part 5: DNS Cache (Ubuntu/Debian)

```bash
# 1. Check if systemd-resolved is active
systemctl status systemd-resolved

# 2. View stats
resolvectl statistics

# 3. Flush cache
sudo resolvectl flush-caches

# 4. View current DNS servers
resolvectl status
```

### Success Criteria

- [ ] Identified your DNS configuration
- [ ] Successfully used dig for various queries
- [ ] Understood how search domains work
- [ ] (Kubernetes) Resolved cluster services by name
- [ ] Know how to flush DNS cache

---

## Key Takeaways

1. **Resolution order matters** — /etc/hosts before DNS (check nsswitch.conf)

2. **resolv.conf is key** — nameserver, search, and ndots control resolution

3. **dig is your friend** — Most powerful DNS debugging tool

4. **Kubernetes DNS is CoreDNS** — Service discovery relies on it

5. **Search domains enable short names** — Why `redis` works instead of full FQDN

---

## What's Next?

In **Module 3.3: Network Namespaces & veth**, you'll learn how Linux creates isolated network stacks for containers—the foundation of pod networking.

---

## Further Reading

- [CoreDNS Manual](https://coredns.io/manual/)
- [Kubernetes DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [DNS Debugging in Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)
- [dig HOWTO](https://www.madboa.com/geek/dig/)
