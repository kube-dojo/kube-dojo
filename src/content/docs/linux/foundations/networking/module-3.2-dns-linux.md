---
title: "Module 3.2: DNS in Linux"
slug: linux/foundations/networking/module-3.2-dns-linux
sidebar:
  order: 3
lab:
  id: "linux-3.2-dns"
  url: "https://killercoda.com/kubedojo/scenario/linux-3.2-dns"
  duration: "30 min"
  difficulty: "intermediate"
  environment: "ubuntu"
---

> **Linux Foundations** | Complexity: `[HIGH]` | Time: 45-60 min

## Prerequisites

Before starting this module:
- **Required**: [Module 3.1: TCP/IP Essentials](../module-3.1-tcp-ip-essentials/)
- **Helpful**: Basic understanding of networking concepts and command-line interfaces.

## What You'll Be Able to Do

After completing this module, you will be able to:
- **Diagnose** common DNS resolution failures in Linux environments, leveraging `/etc/hosts` and `/etc/resolv.conf`.
- **Debug** complex DNS issues within Kubernetes clusters using `kubectl` and specialized tools like `dig` and `nslookup`.
- **Evaluate** the impact of `ndots` and search domains on DNS performance and resolution order in both bare-metal and containerized setups.
- **Implement** effective strategies for DNS caching and cache invalidation to optimize application connectivity and ensure service resilience.

## Why This Module Matters

In October 2021, a configuration update at Facebook (now Meta) led to a global outage of its services, including WhatsApp, Instagram, and Messenger, for nearly six hours. The root cause? A DNS issue. Specifically, a faulty configuration change inadvertently severed connections between Meta's DNS servers and the broader internet. This single point of failure cascaded, rendering billions of users unable to access services and costing the company an estimated $100 million in revenue, alongside a significant blow to its reputation.

This incident, far from unique, dramatically illustrates a fundamental truth in modern computing: DNS is the invisible backbone of nearly all network communication. Whether you're accessing a public website, communicating with a cloud API, or ensuring microservices can discover each other within a Kubernetes cluster, DNS is the silent arbiter. When DNS malfunctions, the internet as we know it effectively grinds to a halt. Understanding DNS is not just about knowing a few commands; it's about mastering the core mechanism that connects applications to their destinations, making it an indispensable skill for any robust system design, troubleshooting, or operational role. This module equips you with the in-depth knowledge and practical tools to dissect, diagnose, and resolve the often-elusive "name or service not known" errors, ensuring your systems remain resilient, performant, and reachable.

## Did You Know?

- **DNS was created in 1983** by Paul Mockapetris to replace the HOSTS.TXT file, a manually distributed flat file that listed every hostname on the ARPANET. This massive architectural change was crucial for the internet to scale beyond a few hundred machines to the global network it is today.
- **Kubernetes' CoreDNS handles millions of queries per hour** in large clusters. Every service lookup, every pod-to-pod communication, and every external DNS query flows through it, making it a critical control point for application connectivity and a prime candidate for performance optimization and debugging.
- **The `search` directive in `/etc/resolv.conf` is a performance optimization and convenience feature** that allows users and applications to type short service names (like `my-service`) instead of fully qualified domain names (like `my-service.default.svc.cluster.local`). This convenience, however, comes with subtle implications for resolution order, latency, and potential security concerns if not managed correctly.
- **DNS primarily uses UDP port 53 for queries**, due to its connectionless and low-overhead nature, making it ideal for quick, single-packet transactions. However, it switches to TCP port 53 for larger responses (like zone transfers) or when UDP packets are truncated, especially in scenarios involving DNSSEC. Blocking TCP port 53 can lead to intermittent and hard-to-diagnose DNS failures, particularly in complex network environments.

## The Pillars of Linux DNS Resolution

At its core, DNS resolution in Linux is handled by the C library's resolver (`glibc` for most distributions, or `musl` in Alpine Linux). When an application needs to resolve a hostname to an IP address, it doesn't directly query a DNS server. Instead, it makes a system call to the resolver library, which then follows a defined, configurable process to find the corresponding IP address. This layered approach ensures flexibility and local control over the resolution flow.

### The Resolution Process: A Step-by-Step Walkthrough

The journey from a hostname to an IP address involves several stages, with local configuration files taking precedence over network queries. Understanding this flow is paramount for effective troubleshooting.

```mermaid
graph TD
    A[Application: "Connect to api.example.com"] --> B{1. Check /etc/hosts};
    B -- Not found --> C{2. Check /etc/resolv.conf for DNS server};
    B -- Found --> E[Application connects to 192.168.1.10];
    C --> D[3. Query DNS server (10.96.0.10)];
    D --> F[4. DNS server returns: 93.184.216.34];
    F --> E[5. Application connects to 93.184.216.34];

    subgraph etc_hosts_lookup [/etc/hosts content]
        H1["127.0.0.1 localhost"]
        H2["192.168.1.10 api.example.com"]
    end
    subgraph resolv_conf_content [/etc/resolv.conf content]
        R1["nameserver 10.96.0.10"]
        R2["search default.svc.cluster.local ..."]
    end
    B -- Check --> H1;
    B -- Check --> H2;
    C -- Read --> R1;
    C -- Read --> R2;
```
1.  **Application Request**: An application requests to connect to a hostname, e.g., `api.example.com`.
2.  **`/etc/hosts` Check**: The resolver first checks the local `/etc/hosts` file for a static mapping. This file acts as a simple, high-priority local DNS cache and override mechanism.
3.  **`/etc/resolv.conf` Consult**: If the hostname is not found in `/etc/hosts`, the resolver reads `/etc/resolv.conf` to determine which external DNS servers to query and which domain suffixes to try for unqualified names.
4.  **DNS Server Query**: The resolver sends a DNS query to the configured DNS server(s), typically using UDP port 53.
5.  **DNS Server Response**: The DNS server responds with the corresponding IP address, along with other information like the Time To Live (TTL).
6.  **Application Connects**: The application uses the resolved IP address to establish a connection, bypassing the need for further name resolution until the cached entry expires.

### `/etc/nsswitch.conf`: The Resolver's Order of Operations

The `/etc/nsswitch.conf` file (Name Service Switch configuration) is the master control for how a Linux system performs lookups for various databases, including `hosts`, `passwd`, and `groups`. For DNS resolution, it dictates the exact order in which sources are consulted.

```bash
cat /etc/nsswitch.conf | grep hosts

# Output: hosts: files dns
# Meaning: Check files (/etc/hosts) first, then DNS
```
In this typical configuration, `files` (referring to `/etc/hosts`) are consulted first. If a match is found, the lookup stops. If not, the system proceeds to `dns` (querying the servers specified in `/etc/resolv.conf`). If `dns` were listed first, or `files` omitted, the resolution behavior would change significantly, potentially leading to performance issues or unexpected overrides.

### `/etc/hosts`: The Local Override

The `/etc/hosts` file provides a simple, static mapping of IP addresses to hostnames. It's the first place the resolver looks (if `nsswitch.conf` is configured to do so) and offers a powerful, fast way to override DNS resolution locally without involving network traffic.

```bash
# /etc/hosts
127.0.0.1       localhost
::1             localhost
192.168.1.100   myserver.local myserver
10.0.0.50       database.internal db
```
This file is incredibly useful for:
-   **Local Development**: Mapping internal service names to `localhost` or specific development IP addresses, speeding up iteration.
-   **Testing**: Temporarily redirecting traffic for a production domain to a staging environment without changing global DNS records.
-   **Blocking Sites**: Mapping undesirable domains to `127.0.0.1` or `0.0.0.0` to prevent access at the operating system level.

#### Kubernetes and `/etc/hosts`
Even in Kubernetes, `/etc/hosts` plays a role within each pod. It primarily maps `localhost` and the pod's own IP address to its hostname, ensuring basic network functionality.

```bash
# In a Kubernetes pod
cat /etc/hosts

# Output:
127.0.0.1       localhost
10.244.1.5      my-pod-name
```

> **Pause and predict**: Imagine your application needs to connect to a legacy internal service at `legacy-api.example.com`. To ensure high availability during a migration, you've added an entry to `/etc/hosts` on your application server: `10.0.0.150 legacy-api.example.com`. However, the production DNS record for `legacy-api.example.com` unexpectedly changes to `10.0.0.151`. What IP address will your application attempt to connect to, and why? What's the immediate impact if `10.0.0.150` becomes unresponsive?

## Mastering `/etc/resolv.conf`: The DNS Configuration Hub

While `/etc/hosts` provides static overrides, `/etc/resolv.conf` is where the dynamic world of DNS resolution is configured. It explicitly tells your system which DNS servers to query and how to construct queries for unqualified hostnames. A well-configured `resolv.conf` is essential for both performance and correct service discovery.

### Format and Key Directives

The `resolv.conf` file is typically generated automatically by network management tools, but its contents are straightforward, primarily containing `nameserver`, `search`, `domain`, and `options` directives.

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

| Directive  | Purpose                                           | Example                     |
|------------|---------------------------------------------------|-----------------------------|
| `nameserver` | IP address of a DNS server to query. Up to 3 can be listed. | `nameserver 8.8.8.8`        |
| `search`   | List of domain suffixes to append to unqualified hostnames. | `search example.com corp.internal` |
| `domain`   | Default domain name; overridden by `search` if both are present. | `domain example.com`        |
| `options`  | Various resolver options, like `ndots`, `timeout`, `attempts`. | `options ndots:5`           |

### The Nuance of `ndots`

The `ndots` option is often overlooked but profoundly impacts DNS query behavior, especially in environments like Kubernetes where short hostnames are common. It determines when an unqualified hostname (one without a dot) or a partially qualified hostname is considered "absolute" and when search domains should be appended.

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

**Real-world implication**: A high `ndots` value (like Kubernetes' default of 5) means that even a seemingly fully qualified external domain name like `www.google.com` (2 dots) will first have all search domains appended to it. This results in multiple failed queries before the resolver eventually tries `www.google.com` as an absolute name, introducing significant latency and unnecessary DNS traffic. To mitigate this, always prefer using fully qualified domain names (FQDNs) with a trailing dot (e.g., `www.google.com.`) for external services to explicitly bypass the search path.

### Kubernetes and `resolv.conf`

Every pod in Kubernetes is assigned its own `/etc/resolv.conf` file, which is meticulously managed by the Kubelet. This configuration is critical as it points to the cluster's CoreDNS service and includes search paths specific to the pod's namespace and the overall cluster domain.

```bash
# In a Kubernetes pod
cat /etc/resolv.conf

# Output:
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

This configuration implies:
-   The primary DNS server for the pod is the ClusterIP of the `kube-dns` service (which CoreDNS implements). This IP is internal to the cluster.
-   Short hostnames (e.g., `my-service`) will automatically try to resolve within the pod's current namespace, then the broader cluster, thanks to the `search` directive.
-   `ndots:5` is specifically set to optimize for Kubernetes internal service discovery. Service FQDNs (e.g., `my-service.default.svc.cluster.local`) typically have 4 dots, meaning they'll be treated as "absolute" names and queried directly. However, as noted above, this can introduce performance penalties for external DNS lookups.

> **Stop and think**: You're debugging a `web-app` pod in the `staging` namespace that is failing to connect to `db-service`. The `web-app` is attempting to connect using the short name `db-service`. Given a typical Kubernetes pod's `/etc/resolv.conf` with `ndots:5` and `search staging.svc.cluster.local svc.cluster.local cluster.local`, outline the precise sequence of DNS queries the `web-app` pod's resolver will attempt. Why is understanding this sequence crucial for effective debugging?

## The DNS Debugger's Toolkit: `dig`, `nslookup`, `host`, `getent`

When DNS issues strike, knowing your tools is half the battle. Linux provides several command-line utilities, each with its unique strengths, to query DNS servers and inspect resolution paths. Mastering these tools will significantly accelerate your troubleshooting process.

### `dig` (Domain Information Groper)

`dig` is the most powerful and flexible command-line tool for querying DNS name servers. It's indispensable for detailed diagnostics, offering fine-grained control over query types, servers, and output format.

```bash
# Basic query: Resolves A record for example.com using default DNS server
dig example.com

# Query specific record type: Fetch only IPv4 address
dig example.com A

# Query specific record type: Fetch only IPv6 address
dig example.com AAAA

# Query specific record type: Fetch Mail Exchanger records
dig example.com MX

# Query specific record type: Fetch Name Server records
dig example.com NS

# Query specific record type: Fetch Text records (often used for SPF, DKIM, DMARC)
dig example.com TXT

# Query specific record type: Fetch Canonical Name record
dig example.com CNAME

# Short output: Displays only the answer section (useful for scripting)
dig +short example.com

# Use specific DNS server: Query Google's public DNS (8.8.8.8)
dig @8.8.8.8 example.com

# Trace full resolution path: Shows iterative queries from root servers down
dig +trace example.com

# Reverse lookup: Resolves IP address to hostname (PTR record)
dig -x 8.8.8.8
```

#### Example `dig` Output
A typical `dig` query provides extensive information about the resolution process, including request/response headers, question, answer, authority, and additional sections. This level of detail is invaluable for advanced debugging.

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
The `ANSWER SECTION` clearly shows the resolved IP address (93.184.216.34) and its TTL (3600 seconds). The `SERVER` line indicates precisely which DNS server processed and provided the answer, which is crucial for identifying misconfigurations or problematic upstream resolvers.

#### `dig` vs `dig +short`
The `+short` option is incredibly useful for quickly extracting just the IP address or relevant record, making it ideal for scripting or quick command-line checks where verbose output is unnecessary.

```bash
dig example.com
# ... lots of output ...
# example.com.  3600  IN  A  93.184.216.34
# ... query time, server, etc ...

dig +short example.com
# 93.184.216.34
```

### `nslookup`

`nslookup` is a simpler, interactive tool for querying DNS. While `dig` is generally preferred for advanced diagnostics due to its richer features and more standardized output, `nslookup` is often pre-installed and serves as an easier entry point for basic lookups. It can operate in interactive or non-interactive modes.

```bash
# Basic lookup: Resolves example.com using default DNS server
nslookup example.com

# Use specific server: Query Google's public DNS (8.8.8.8)
nslookup example.com 8.8.8.8

# Reverse lookup: Resolves IP address to hostname
nslookup 8.8.8.8
```

### `host`

The `host` command offers an even simpler and more concise output compared to `nslookup`, making it an excellent choice for quick, human-readable lookups. It provides a good balance between brevity and utility.

```bash
# Basic lookup: Resolves example.com
host example.com

# Reverse lookup: Resolves IP address to hostname
host 8.8.8.8

# Find mail servers: Queries MX records
host -t MX example.com
```

### `getent`

The `getent` (get entries) command is unique because it queries the Name Service Switch (NSS) libraries, which means it respects the entire resolution order defined in `/etc/nsswitch.conf`. This includes checking `/etc/hosts` before querying DNS servers. This makes `getent` a particularly valuable tool for understanding how applications *actually* perform name resolution on your system, as it mimics the system calls applications make.

```bash
# Resolve like applications do: Checks /etc/hosts, then DNS, respecting nsswitch.conf
getent hosts example.com

# This command is crucial because it mimics the behavior of system calls that applications make.
# If 'getent' succeeds where 'dig' fails, it often points to an issue with /etc/hosts or search domains.
```

## Kubernetes DNS: The Heart of Service Discovery

Kubernetes relies heavily on DNS for its internal service discovery mechanism. Every service and pod within a cluster is automatically assigned a DNS name, enabling applications to communicate by logical names rather than ephemeral IP addresses. This abstraction is a cornerstone of microservices architecture in Kubernetes.

### CoreDNS: The Cluster Resolver

CoreDNS is the default DNS server for Kubernetes. It runs as a set of pods (typically in the `kube-system` namespace) and is responsible for handling all internal and external DNS queries originating from pods within the cluster.

```mermaid
graph TD
    P[Pod Query: "my-service.default.svc.cluster.local"] --> C(CoreDNS);
    C -- Cluster queries: *.cluster.local --> K[Answer from Kubernetes API];
    C -- External queries: *.* --> U[Forward to upstream DNS];
    K --> R[Returns: 10.96.45.123 (Service ClusterIP)];
    U --> R;

    subgraph CoreDNS_Server [CoreDNS (10.96.0.10)]
        C
    end
```
CoreDNS is configured through its `Corefile` to perform two primary functions:
-   **Resolve cluster names**: Any query ending with `.cluster.local` (or your configured cluster domain) is intercepted and resolved by looking up Services and Pods via the Kubernetes API, which maintains an authoritative list of cluster resources.
-   **Forward external names**: Queries for external domains (e.g., `google.com`) are forwarded to upstream DNS servers, which are typically configured in CoreDNS's `Corefile` to point to public DNS resolvers.

### Kubernetes DNS Naming Conventions

Kubernetes enforces a consistent and predictable naming scheme for services and pods, making service discovery straightforward.

```mermaid
graph TD
    A[Service Fully Qualified Domain Name (FQDN)] --> B("my-service.namespace.svc.cluster.local")
    B --> C{Components of the FQDN}
    C --> D[Service Name: my-service]
    C --> E[Namespace: namespace]
    C --> F[Service Type Indicator: svc]
    C --> G[Cluster Domain: cluster.local]
```
-   **Service FQDN**: `my-service.namespace.svc.cluster.local`
    -   `my-service`: The name of the Kubernetes Service.
    -   `namespace`: The namespace the Service resides in (e.g., `default`, `staging`, `production`).
    -   `svc`: A static indicator denoting this is a Service record.
    -   `cluster.local`: The cluster domain, configurable during cluster setup.
-   **Pod FQDN (with hostname)**: `pod-name.subdomain.namespace.svc.cluster.local` (e.g., for headless services)

The ability to use short names (e.g., `my-service` instead of `my-service.default.svc.cluster.local`) within a pod's namespace is a direct result of the `search` directive in the pod's `/etc/resolv.conf`, which automatically appends appropriate suffixes.

### Testing DNS in Kubernetes

When troubleshooting, it's crucial to test DNS resolution directly from within a pod. This replicates the application's exact network environment and configuration, providing the most accurate debugging context.

```bash
# Run a temporary busybox pod to test DNS resolution
kubectl run dnstest --image=busybox --rm -it --restart=Never -- sh

# Inside the pod:
# 1. Resolve the Kubernetes API service (short name)
nslookup kubernetes

# 2. Resolve the Kubernetes API service (fully qualified name)
nslookup kubernetes.default.svc.cluster.local

# 3. Inspect the pod's resolv.conf
cat /etc/resolv.conf

# 4. Test external DNS resolution
nslookup google.com

# 5. Exit the busybox pod
exit
```
This sequence allows you to quickly verify internal service discovery, external connectivity, and inspect the pod's specific DNS configuration.

### Troubleshooting Common Kubernetes DNS Issues

The error message "nslookup: can't resolve 'kubernetes'" or similar "name or service not known" is a classic Kubernetes DNS debugging scenario. A systematic approach is key:

```bash
# Issue: "nslookup: can't resolve 'kubernetes'"

# Debug steps:
# 1. Check if CoreDNS pods are running and healthy
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 2. Check CoreDNS pod logs for any errors or configuration issues
kubectl logs -n kube-system -l k8s-app=kube-dns

# 3. Verify the kube-dns service exists and has a ClusterIP
kubectl get svc -n kube-system kube-dns

# 4. Verify that the pod can reach the CoreDNS service IP (typically 10.96.0.10) on port 53 (UDP/TCP)
# This uses netcat (nc) from a busybox pod to test connectivity
kubectl run test --image=busybox --rm -it -- \
  nc -zv 10.96.0.10 53
```
These steps help isolate the problem: Is CoreDNS running? Is it misconfigured? Is there a network connectivity issue preventing pods from reaching CoreDNS?

#### Finding a Kubernetes Pod's DNS Server
To definitively confirm what DNS server a Kubernetes pod is actually configured to use:

```bash
# Option 1: Exec into the pod and check its resolv.conf
kubectl exec pod-name -- cat /etc/resolv.conf

# Option 2: Get the ClusterIP of the kube-dns service
kubectl get svc -n kube-system kube-dns -o wide

# The 'nameserver' entry in the pod's resolv.conf should match the 'ClusterIP' of the kube-dns service.
```
This comparison helps verify if the pod's DNS configuration correctly points to the cluster's CoreDNS service.

#### `dig kubernetes` vs `getent hosts kubernetes` in a Pod
Understanding the subtle differences between these commands is paramount in a Kubernetes context:

```bash
dig kubernetes.default.svc.cluster.local  # Works by directly querying the FQDN
dig +search kubernetes                      # Explicitly tells dig to use search domains
getent hosts kubernetes                     # Uses the system resolver, respecting /etc/hosts and search domains
```
`dig` performs a direct DNS query, bypassing local files (`/etc/hosts`) and search paths unless explicitly directed (`+search`). `getent hosts`, however, is a more holistic tool that mimics how applications resolve names, adhering to the NSS configuration (`/etc/nsswitch.conf`). If `getent` succeeds where `dig` fails, it strongly suggests the issue lies with `/etc/hosts` entries or the `search` domain configuration rather than CoreDNS itself.

## DNS Caching: Speed vs. Freshness

DNS queries, especially those traversing the internet, can introduce significant latency. To mitigate this, DNS responses are frequently cached at various levels: client-side (applications, browsers), operating system, and intermediate DNS servers (e.g., CoreDNS, ISP resolvers). While caching dramatically improves performance, it can also lead to issues with stale records if updates are not propagated promptly.

### `systemd-resolved` (Modern Linux Caching)

Many modern Linux distributions (like Ubuntu and Debian) utilize `systemd-resolved` as a sophisticated system service for network name resolution. It provides a caching DNS resolver and acts as a local stub resolver for applications, centralizing DNS management.

```bash
# Check the current status of systemd-resolved
systemd-resolve --status

# Flush the DNS cache maintained by systemd-resolved
systemd-resolve --flush-caches

# Display statistics about systemd-resolved operations
systemd-resolve --statistics
```
Alternatively, the `resolvectl` command provides a more comprehensive and user-friendly interface for interacting with `systemd-resolved`:

```bash
# Check if systemd-resolved is active
systemctl status systemd-resolved

# View statistics (cache hits, misses, current cache size)
resolvectl statistics

# Flush cache (clears all cached entries)
sudo resolvectl flush-caches

# View current DNS servers and domains configured
resolvectl status
```

### Diagnosing and Flushing Cache Issues

A common and frustrating scenario is when a DNS record for a service has been updated (e.g., an IP address change), but your application or system continues to use an old, cached IP address, leading to connectivity failures.

```bash
# Symptom: An application connects to an old IP address for a domain, even after DNS records have been updated.

# Solutions:
# 1. Flush the local DNS cache (if systemd-resolved is in use)
sudo systemd-resolve --flush-caches
# Or using resolvectl
sudo resolvectl flush-caches

# 2. Check the Time To Live (TTL) of the DNS record to understand how long it's designed to be cached
dig example.com | grep -E "^example.*IN.*A"
# The number after 'IN' in the ANSWER SECTION is the TTL in seconds. A low TTL means changes propagate faster.

# 3. In Kubernetes, if CoreDNS is caching stale external records, you might need to restart its pods to force a refresh
kubectl rollout restart deployment coredns -n kube-system
```
Understanding TTLs is critical for setting expectations on DNS propagation. A short TTL (e.g., 60 seconds) means changes will be reflected quickly, while a long TTL (e.g., 24 hours) will cause delays.

## Common Mistakes

DNS troubleshooting can be tricky and often involves sifting through layers of configuration. Here are some frequent pitfalls and their practical solutions:

| Mistake                        | Problem                                                                  | Solution                                                                |
|--------------------------------|--------------------------------------------------------------------------|-------------------------------------------------------------------------|
| Missing trailing dot in FQDN   | `example.com` is relative, `example.com.` is absolute. Search domains can be appended unnecessarily, leading to slow or incorrect resolution. | Always use a trailing dot for Fully Qualified Domain Names (FQDNs) in configurations or when explicitly bypassing search paths to ensure absolute resolution. |
| Incorrect `ndots` setting      | Too high: Slows down external lookups due to excessive search domain attempts. Too low: Breaks internal service discovery in microservices environments. | Tune `ndots` in `/etc/resolv.conf` (or Pod's `dnsPolicy`) carefully, or standardize on always using FQDNs for clarity and predictability. |
| `/etc/hosts` ignored           | A crucial local override isn't taking effect, or a static mapping is unexpectedly missed by the system resolver. | Verify the `hosts` entry in `/etc/nsswitch.conf` is correctly ordered (e.g., `hosts: files dns`) to ensure local files are checked first. |
| DNS over TCP blocked           | Large DNS responses (e.g., DNSSEC records, zone transfers) or queries for large records fail intermittently, causing hard-to-debug issues. | Ensure firewall rules allow TCP port 53 traffic to and from your DNS servers, in addition to UDP port 53. |
| External DNS in Pods fails     | Pods cannot resolve public domain names (e.g., `google.com`), hindering internet connectivity for containerized applications. | Check the CoreDNS `Corefile` configuration for correct upstream DNS forwarders. Ensure those upstream servers are reachable. |
| `/etc/resolv.conf` overwritten | Manual changes to `/etc/resolv.conf` are lost after reboot, network restart, or by network managers, leading to transient DNS problems. | Use network manager tools (`netplan`, `NetworkManager`) or `resolvconf` utility to manage `resolv.conf` persistently, or ensure changes are applied dynamically. |
| Stale DNS Cache                | Updated DNS records are not reflected, causing applications to connect to old IP addresses and leading to connectivity issues. | Flush local DNS caches (`systemd-resolved`, browser cache, application-specific caches) and check DNS record TTLs to understand propagation times. Restarting CoreDNS might be needed in Kubernetes. |
| Firewall blocks DNS            | DNS queries fail entirely, resulting in "host not found" or "connection timed out" errors across the board. | Ensure UDP/TCP port 53 is open for outbound traffic to your configured DNS servers at all firewall layers (host, network, cloud security groups). |

## Quiz

Test your understanding of DNS in Linux and Kubernetes. Each question provides a scenario to solidify your diagnostic and debugging skills.

### Question 1: Understanding Search Directives
What does the `search` directive in `/etc/resolv.conf` do, and why is it particularly useful in a microservices environment like Kubernetes?

<details>
<summary>Show Answer</summary>

The `search` directive specifies a list of domain suffixes that the resolver will append, in order, to unqualified hostnames (those without a dot, or with fewer dots than specified by `ndots`) until a successful resolution is found.

Example:
```
search example.com corp.internal
```

If you query for `server`, the system will first try `server.example.com`, then `server.corp.internal`, and finally `server` as an absolute name.

In microservices, this is incredibly useful because it allows services to refer to each other by convenient short names (e.g., `redis` instead of `redis.default.svc.cluster.local`). This reduces verbosity, makes configurations more portable across different environments or namespaces, and simplifies application code by abstracting away the full DNS hierarchy.
</details>

### Question 2: `dig` vs `getent hosts` in Kubernetes
You're inside a Kubernetes pod and `dig kubernetes` fails with "host not found," but `getent hosts kubernetes` successfully returns the ClusterIP for the Kubernetes API service. Explain in detail why this discrepancy occurs and how you might make `dig kubernetes` succeed without changing the pod's `resolv.conf`.

<details>
<summary>Show Answer</summary>

This discrepancy occurs because `dig` performs a direct DNS query against the configured nameserver(s) (typically CoreDNS in Kubernetes), bypassing the Name Service Switch (NSS) configuration. By default, `dig` does not apply the `search` domains from `/etc/resolv.conf` unless explicitly told to. Thus, `dig kubernetes` queries for `kubernetes.` (an absolute, unqualified name), which CoreDNS may not resolve directly.

`getent hosts`, however, respects the NSS configuration (typically `/etc/nsswitch.conf`), which instructs the system to check `/etc/hosts` first, and then to apply the `search` domains from `/etc/resolv.conf` before making a direct DNS query. When `getent hosts kubernetes` is run, the resolver tries `kubernetes.default.svc.cluster.local` (due to the search path) and successfully resolves it.

To make `dig kubernetes` succeed without changing the pod's `resolv.conf`, you would need to either:
1.  Provide the fully qualified domain name (FQDN): `dig kubernetes.default.svc.cluster.local`
2.  Explicitly tell `dig` to use the search domains: `dig +search kubernetes`

```bash
dig kubernetes.default.svc.cluster.local  # Works
dig +search kubernetes                      # Uses search domains
getent hosts kubernetes                     # Uses system resolver
```
</details>

### Question 3: The `ndots` Option and Performance
Explain the purpose of the `ndots:5` option in `/etc/resolv.conf` and discuss its potential impact on both internal Kubernetes service resolution and external domain resolution performance.

<details>
<summary>Show Answer</summary>

The `ndots:5` option is an `options` directive in `/etc/resolv.conf` that instructs the resolver library to treat any hostname containing fewer than 5 dots as an unqualified name. This means that for such names, the resolver will first append each domain listed in the `search` directive (in order) before attempting to resolve the name as an absolute FQDN. If a hostname has 5 or more dots, it is immediately treated as an absolute FQDN and queried directly.

In Kubernetes, this is highly beneficial for internal service resolution because typical service FQDNs like `my-service.default.svc.cluster.local` have exactly 4 dots. With `ndots:5`, these names are correctly interpreted as FQDNs immediately, bypassing unnecessary search path attempts and ensuring efficient resolution within the cluster.

However, for external domain names like `www.google.com` (which has only 2 dots), `ndots:5` causes the resolver to first append all search domains (e.g., `www.google.com.default.svc.cluster.local`), resulting in multiple failed and unnecessary queries. This can introduce noticeable latency for external lookups, as the system must exhaust the search path before resolving the intended external domain.
</details>

### Question 4: Identifying a Pod's DNS Server
You suspect a Kubernetes pod is using an incorrect DNS server, leading to intermittent resolution failures. Describe two distinct methods to verify which DNS server the pod is configured to use and what specific information you would expect to see for a correctly configured pod.

<details>
<summary>Show Answer</summary>

**Method 1: Inspecting the Pod's `/etc/resolv.conf` from the Host**
You can exec into the pod and directly inspect its `resolv.conf` file, which is its source of truth for DNS configuration:
```bash
kubectl exec <pod-name> -- cat /etc/resolv.conf
```
For a correctly configured pod, you would expect to see an entry like `nameserver 10.96.0.10` (or similar ClusterIP), which is the internal IP address of the cluster's CoreDNS service.

**Method 2: Checking the `kube-dns` Service and Comparing**
First, identify the ClusterIP of the `kube-dns` service (which CoreDNS implements) in the `kube-system` namespace:
```bash
kubectl get svc -n kube-system kube-dns -o wide
```
Then, compare the `nameserver` IP address found in the pod's `resolv.conf` (from Method 1) with the `ClusterIP` displayed for the `kube-dns` service. For correct configuration, these IP addresses **must match**. If they don't, it indicates that the pod might be misconfigured, or an intermediate component is redirecting DNS traffic incorrectly.
</details>

### Question 5: DNS Record TTL and Caching
A critical external service has just changed its IP address, but your applications deployed in Kubernetes are still connecting to the old, invalid IP address, resulting in connection timeouts. How would you diagnose this as a DNS caching issue, and what immediate steps would you take to force your applications to use the new IP address?

<details>
<summary>Show Answer</summary>

To diagnose this as a DNS caching issue, you would first use `dig` from a debug pod within your Kubernetes cluster to query the service's domain. You would inspect the `ANSWER SECTION` for the `TTL` (Time To Live) value. A high TTL (e.g., 86400 seconds = 24 hours) indicates that the record is designed to be cached for a longer duration. If `dig` returns the *new* IP but your application pods are still using the *old* one, it strongly confirms a caching problem within your cluster's DNS infrastructure (CoreDNS) or application-level caches.

Immediate steps to force an update:
1.  **Restart CoreDNS pods**: The most effective way to clear CoreDNS's internal cache is to restart its pods. This forces them to re-read configurations and perform fresh lookups for external domains.
    ```bash
    kubectl rollout restart deployment coredns -n kube-system
    ```
2.  **Restart application pods**: Many applications maintain their own DNS caches. Restarting the affected application pods will force them to re-resolve hostnames using the (now refreshed) CoreDNS.
3.  **Check external TTL**: Communicate with the external service provider to confirm the TTL of their DNS records. Request a temporary reduction of the TTL if frequent changes are anticipated during migrations.
</details>

### Question 6: Reverse DNS Lookup for Security Audit
You're performing a security audit and notice unusual outgoing connections from one of your Kubernetes worker nodes to an IP address (`192.0.2.1`). You want to identify the hostname associated with this IP to determine if it's a legitimate service or a potential threat. What command would you use on the worker node to perform this lookup, and how is this type of lookup generally useful for security or network troubleshooting?

<details>
<summary>Show Answer</summary>

To identify the hostname associated with the IP address `192.0.2.1`, you would perform a reverse DNS lookup. The `dig -x` command is the most precise tool for this:
```bash
dig -x 192.0.2.1
# Alternatively, 'host 192.0.2.1' or 'nslookup 192.0.2.1' can also be used.
```
This type of lookup queries for `PTR` (Pointer) records, which map IP addresses back to hostnames.

Reverse DNS lookups are extremely useful for:
-   **Security**: Identifying unknown IP addresses connecting to your infrastructure, helping determine if they belong to known malicious domains, legitimate third-party services, or misconfigured internal resources.
-   **Troubleshooting**: Verifying if an IP address correctly maps back to its expected hostname, which can uncover misconfigurations in DNS records, especially for services that rely on reverse DNS (e.g., email servers for SPF/DKIM checks, some logging systems).
-   **Logging and Analytics**: Enriching network logs by associating IP addresses with human-readable hostnames, making log analysis more insightful.
</details>

### Question 7: Debugging "Name or service not known" in a Container
A newly deployed containerized application is consistently failing with a "Name or service not known" error when attempting to connect to an external API (`api.external.com`). This error occurs *inside* the container. What sequence of commands would you execute *from within the container* to systematically debug this issue, assuming the container has basic network tools (`cat`, `grep`, `dig`, `nslookup`, `nc`) available?

<details>
<summary>Show Answer</summary>

Here's a systematic sequence of commands to debug this issue from within the container:

1.  **Inspect `/etc/resolv.conf`**:
    ```bash
    cat /etc/resolv.conf
    # Verify the configured nameservers and search domains. Ensure a valid DNS server IP is present and reachable.
    ```
2.  **Check `nsswitch.conf` (if available)**:
    ```bash
    cat /etc/nsswitch.conf | grep hosts
    # Confirm the resolution order (e.g., 'hosts: files dns'). This determines if /etc/hosts is checked.
    ```
3.  **Inspect `/etc/hosts` file**:
    ```bash
    cat /etc/hosts
    # Rule out any local overrides or misconfigurations that might be blocking or redirecting the external API domain.
    ```
4.  **Test DNS server reachability**:
    ```bash
    nc -zv <nameserver_ip_from_resolv.conf> 53
    # Verify that the container can establish a network connection to its configured DNS server on port 53 (UDP/TCP). A failure here points to network/firewall issues.
    ```
5.  **Test external resolution with `dig`**:
    ```bash
    dig api.external.com
    # Use 'dig' to see if the configured DNS server itself can resolve the external API. This will show if the problem is with the DNS server's ability to resolve, or if the container's resolver configuration is incorrect.
    ```
    If `dig` fails, try `dig @<upstream_dns_ip> api.external.com` using a known public DNS (e.g., 8.8.8.8) to check if the issue is with the container's *primary* DNS server or a broader network block.
</details>

## Hands-On Exercise: DNS Mastery Challenge

**Objective**: Gain practical mastery over DNS configuration and troubleshooting in Linux and Kubernetes environments.

**Environment**: A Linux system (e.g., Ubuntu VM, WSL) and optionally, access to a Kubernetes cluster. You'll need `sudo` for some commands.

### Part 1: Local DNS Configuration Deep Dive

Explore how your local Linux system handles hostname resolution. This will form the foundation for understanding more complex environments.

1.  **Identify your DNS Servers**: Inspect the `/etc/resolv.conf` file to see which DNS servers your system is configured to use.
    <details>
    <summary>Solution</summary>

    ```bash
    cat /etc/resolv.conf
    # Look for lines starting with 'nameserver'. These are the IPs of your configured DNS resolvers.
    ```
    </details>
2.  **Understand Resolution Order**: Check your `/etc/nsswitch.conf` to discover the precedence of resolution sources for hostnames. This file is often overlooked but critical.
    <details>
    <summary>Solution</summary>

    ```bash
    cat /etc/nsswitch.conf | grep hosts
    # Expected output: hosts: files dns (or similar). This line tells you if /etc/hosts is checked before DNS queries are sent out.
    ```
    </details>
3.  **Inspect Local Hostname Mappings**: Examine the contents of `/etc/hosts`. Note any custom entries or default mappings like `localhost`. Can you explain why `localhost` is typically defined here?
    <details>
    <summary>Solution</summary>

    ```bash
    cat /etc/hosts
    # Note any custom entries or default mappings like localhost. 'localhost' is defined here to ensure it always resolves to 127.0.0.1 or ::1, even if DNS is unavailable or misconfigured, providing a reliable loopback interface.
    ```
    </details>
4.  **Test System Resolver with `getent`**: Use `getent hosts` to verify how your system resolves well-known hostnames.
    <details>
    <summary>Solution</summary>

    ```bash
    getent hosts localhost
    getent hosts google.com
    # Compare these results with your /etc/hosts and direct DNS queries. 'getent' mimics how applications resolve names.
    ```
    </details>

### Part 2: Advanced DNS Queries with `dig`

Hone your skills with `dig`, the ultimate DNS diagnostic tool. This section will empower you to perform detailed DNS investigations.

1.  **Perform a Basic Query**: Resolve `google.com` using your default DNS server. Pay attention to the `ANSWER SECTION` and the `SERVER` line.
    <details>
    <summary>Solution</summary>

    ```bash
    dig google.com
    # Observe the ANSWER SECTION for the IP address and its TTL. Note the SERVER from which the response was received.
    ```
    </details>
2.  **Get Short Output**: Resolve `google.com` and display only the IP address. This is incredibly useful for scripting.
    <details>
    <summary>Solution</summary>

    ```bash
    dig +short google.com
    ```
    </details>
3.  **Query Different Record Types**: Find the Mail Exchange (MX) records and Name Servers (NS) for `google.com`. Also, find the IPv6 (AAAA) address for `google.com`.
    <details>
    <summary>Solution</summary>

    ```bash
    dig google.com MX
    dig google.com NS
    # For IPv6 addresses:
    dig +short google.com AAAA
    ```
    </details>
4.  **Use Specific DNS Servers**: Query `example.com` using Google's (8.8.8.8) and Cloudflare's (1.1.1.1) public DNS servers.
    <details>
    <summary>Solution</summary>

    ```bash
    dig @8.8.8.8 example.com
    dig @1.1.1.1 example.com
    # Compare the 'SERVER' line in the output for each command to confirm which server responded.
    ```
    </details>
5.  **Perform a Reverse Lookup**: Identify the hostname associated with `8.8.8.8`. What type of DNS record is typically used for reverse lookups?
    <details>
    <summary>Solution</summary>

    ```bash
    dig -x 8.8.8.8
    # Look for PTR records (Pointer records) in the ANSWER SECTION. PTR records are used for reverse DNS.
    ```
    </details>
6.  **Trace Full Resolution Path**: Observe the entire iterative resolution process for `google.com` starting from the root servers. This command provides a deep insight into how DNS works globally.
    <details>
    <summary>Solution</summary>

    ```bash
    dig +trace google.com
    # This command shows the delegation path from root servers, through TLD servers, to authoritative name servers.
    ```
    </details>

### Part 3: Unraveling Search Domains and `ndots`

Understand how search domains and the `ndots` option subtly yet significantly influence hostname resolution, especially in complex network environments.

1.  **Identify your Search Domains**: Check `/etc/resolv.conf` for the `search` directive.
    <details>
    <summary>Solution</summary>

    ```bash
    grep search /etc/resolv.conf
    # Note the listed domain suffixes. These are appended to unqualified hostnames.
    ```
    </details>
2.  **Test with and without Search Domains**: Try resolving a non-existent short name (e.g., `myservice-test`) and then a non-existent FQDN (e.g., `myservice-test.yourdomain.com`) that is *not* in your search path. Observe the difference in resolution attempts. Then, try `dig +search myservice-test` to explicitly leverage search domains.
    <details>
    <summary>Solution</summary>

    ```bash
    dig myservice-test # May fail immediately or try search domains based on ndots
    dig myservice-test.example.com # If example.com is not in your search list, this will be tried directly
    dig +search myservice-test # This forces the use of search domains, simulating how an application would use them.
    ```
    </details>
3.  **Check `ndots` Setting**: Look for the `ndots` option in `/etc/resolv.conf`. How would a change in this value impact resolution performance for frequently accessed external FQDNs?
    <details>
    <summary>Solution</summary>

    ```bash
    grep ndots /etc/resolv.conf
    # A common value is 1 or 5. A lower 'ndots' (e.g., ndots:1) would make the resolver try an unqualified name as an absolute FQDN more quickly, potentially speeding up external lookups if they are true FQDNs. A higher 'ndots' means more search path attempts for multi-dot external FQDNs.
    ```
    </details>

### Part 4: Kubernetes DNS Exploration (Optional, if Kubernetes cluster available)

Dive into how DNS functions within a Kubernetes cluster. This section requires access to a functional Kubernetes cluster and `kubectl`.

1.  **Verify CoreDNS Status**: Ensure CoreDNS pods are running and healthy in your cluster. They are usually in the `kube-system` namespace.
    <details>
    <summary>Solution</summary>

    ```bash
    kubectl get pods -n kube-system -l k8s-app=kube-dns
    # Expect to see one or more coredns pods in 'Running' state. If not, investigate why.
    ```
    </details>
2.  **Run a Test Pod**: Deploy a temporary `busybox` pod to conduct DNS tests from within the cluster's network environment.
    <details>
    <summary>Solution</summary>

    ```bash
    kubectl run dnstest --image=busybox --rm -it --restart=Never -- sh
    # You will be dropped into a shell inside the pod. This is your isolated test environment.
    ```
    </details>
3.  **Inspect Pod's `resolv.conf`**: From within the `dnstest` pod, check its DNS configuration. Note the `nameserver` IP and `search` domains.
    <details>
    <summary>Solution</summary>

    ```bash
    cat /etc/resolv.conf
    # Note the nameserver (ClusterIP of kube-dns) and search domains specific to the pod's namespace and cluster.
    ```
    </details>
4.  **Resolve Cluster Services**: Test resolution for internal Kubernetes services (e.g., `kubernetes`, `kubernetes.default`, `kubernetes.default.svc.cluster.local`). Observe how short names resolve using the search path.
    <details>
    <summary>Solution</summary>

    ```bash
    nslookup kubernetes
    nslookup kubernetes.default
    nslookup kubernetes.default.svc.cluster.local
    # Observe how short names resolve using the search path. The first two should succeed due to search domains.
    ```
    </details>
5.  **Resolve External Domains**: Test resolution for an external domain (e.g., `google.com`). This verifies that CoreDNS is correctly forwarding requests to upstream DNS servers.
    <details>
    <summary>Solution</summary>

    ```bash
    nslookup google.com
    # Verify that external resolution works, implying CoreDNS is forwarding correctly. If it fails, investigate CoreDNS configuration.
    ```
    </details>
6.  **Exit the Test Pod**: Clean up the temporary pod.
    <details>
    <summary>Solution</summary>

    ```bash
    exit
    # This will terminate the busybox pod due to the '--rm' flag used when running it.
    ```
    </details>

### Part 5: Managing DNS Cache (for `systemd-resolved` users)

Understand how to interact with and manage the `systemd-resolved` cache, a common source of stale DNS issues.

1.  **Check `systemd-resolved` Status**: Verify if the service is active on your system. This service is responsible for local DNS caching on many modern Linux distributions.
    <details>
    <summary>Solution</summary>

    ```bash
    systemctl status systemd-resolved
    # Look for 'Active: active (running)'. If it's not running, your system might be using a different resolver or no local caching.
    ```
    </details>
2.  **View DNS Cache Statistics**:
    <details>
    <summary>Solution</summary>

    ```bash
    resolvectl statistics
    # Observe cache hits, misses, and the current cache size. This gives insight into the effectiveness of your local cache.
    ```
    </details>
3.  **Flush DNS Cache**: Clear the `systemd-resolved` cache. This is a crucial step when diagnosing stale DNS records.
    <details>
    <summary>Solution</summary>

    ```bash
    sudo resolvectl flush-caches
    # Rerun 'resolvectl statistics' immediately after to see the effect – the cache size should reset to zero.
    ```
    </details>
4.  **View Current DNS Servers and Domains**:
    <details>
    <summary>Solution</summary>

    ```bash
    resolvectl status
    # This shows the DNS servers being used by systemd-resolved and their current configuration, including Link-specific and Global settings.
    ```
    </details>

### Success Criteria

-   [x] You can confidently identify your system's DNS configuration files (`/etc/hosts`, `/etc/resolv.conf`, `/etc/nsswitch.conf`).
-   [x] You can use `dig` to perform various types of DNS queries (A, AAAA, MX, NS, PTR) and interpret the verbose output or extract specific information with `+short`.
-   [x] You understand how `search` domains and the `ndots` option affect hostname resolution and can predict their impact on performance.
-   [x] (If Kubernetes available) You can debug DNS resolution issues from within a Kubernetes pod by inspecting its `resolv.conf` and testing resolution for both internal and external services.
-   [x] You know how to manage your local system's DNS cache using `systemd-resolved` or `resolvectl`, including flushing it to resolve stale record issues.
-   [x] You can articulate the key differences in how `dig`, `nslookup`, `host`, and `getent` interact with the system resolver.

## Key Takeaways

1.  **Resolution Order Matters**: The system resolver checks `/etc/hosts` before querying DNS servers, as dictated by `/etc/nsswitch.conf`. This hierarchy is fundamental to understanding and troubleshooting name resolution.
2.  **`/etc/resolv.conf` is Central**: This file explicitly configures the DNS servers (`nameserver`), search domains (`search`), and resolver behavior (`options ndots`) that govern how your system performs dynamic lookups.
3.  **`dig` is Your Indispensable Friend**: For detailed DNS diagnostics, `dig` offers unparalleled control and insight into the query process, record types, and server responses. It's the go-to tool for deep dives.
4.  **Kubernetes DNS is CoreDNS**: Within a Kubernetes cluster, CoreDNS provides robust service discovery, translating logical service names to ClusterIPs and forwarding external queries to upstream resolvers.
5.  **Search Domains and `ndots` are Double-Edged**: While the `search` directive enables convenient short hostname resolution for internal services, the `ndots` option can introduce performance overhead for external domains if not carefully managed or bypassed with FQDNs ending in a trailing dot.
6.  **Caching Improves Performance but Requires Management**: Local DNS caches (e.g., `systemd-resolved`) speed up resolution but can serve stale records. Knowing how to diagnose and flush these caches is crucial for resolving propagation issues.

## What's Next?

Having mastered DNS, you're now ready to delve deeper into the network stack's foundational elements. In **Module 3.3: Network Namespaces & veth**, you'll learn how Linux creates isolated network stacks—the very foundation of how containers and pods achieve network isolation and communication within a single host. You'll explore the kernel primitives that enable this intricate dance of network segmentation.

## Further Reading

-   [CoreDNS Manual](https://coredns.io/manual/) - The official and comprehensive documentation for Kubernetes' default DNS server, including its powerful `Corefile` configuration options.
-   [Kubernetes DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) - The authoritative guide to DNS within Kubernetes from the official documentation, covering naming, service discovery, and policies.
-   [DNS Debugging in Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/) - A highly practical guide to troubleshooting common DNS issues in your Kubernetes clusters, detailing systematic debugging steps.
-   [dig HOWTO](https://www.madboa.com/geek/dig/) - A detailed tutorial on using the `dig` command effectively, covering its various options and how to interpret its rich output for advanced diagnostics.
-   [Module 3.1: TCP/IP Essentials](../module-3.1-tcp-ip-essentials/)