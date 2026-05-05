---
title: "Module 0.5: Everyday Networking Tools"
slug: linux/foundations/everyday-use/module-0.5-networking-tools
revision_pending: false
sidebar:
  order: 6
lab:
  id: "linux-0.5-networking-tools"
  url: "https://killercoda.com/kubedojo/scenario/linux-0.5-networking-tools"
  duration: "35 min"
  difficulty: "intermediate"
  environment: "ubuntu"
---
# Module 0.5: Everyday Networking Tools

> **Everyday Use** | Complexity: `[QUICK]` | Time: 45 min

## Prerequisites

Before starting this module, you should be comfortable with basic shell navigation, file paths, and `sudo` from [Module 0.2: Environment & Permissions](../module-0.2-environment-permissions/). It also helps if you have seen service inspection in [Module 0.4: Services & Logs Demystified](../module-0.4-services-logs/), because several examples connect network symptoms back to listening processes and service logs.

KubeDojo uses Kubernetes 1.35+ in cluster-facing examples. When a command needs `kubectl`, define the standard shortcut with `alias k=kubectl`; after that, a command such as `k get pods -A` means the same thing as the longer form. This module mostly stays on the Linux host, but the habit matters because real Kubernetes troubleshooting often starts by proving whether the host network, DNS, or local firewall is healthy before blaming the cluster.

## Learning Outcomes

- **Diagnose** reachability and latency failures with `ping`, `traceroute`, and `tracepath` before escalating to application debugging.
- **Debug** HTTP and API behavior with `curl` verbose output, headers, redirects, and safe checksum verification.
- **Inspect** listening ports and service binding choices with `ss` before blaming remote networks or firewalls.
- **Evaluate** DNS resolver, cache, record, and TTL evidence with `dig` and `host`.
- **Implement** a local firewall troubleshooting sequence with `ufw` and `iptables` that protects Linux and Kubernetes 1.35+ hosts.

## Why This Module Matters

On July 2, 2021, Kaseya disclosed a supply-chain attack that cascaded through managed service providers and disrupted hundreds of downstream organizations. The incident was not a simple "network outage," but responders still had to answer network questions under pressure: which systems could reach command-and-control infrastructure, which services were exposed, which downloads were trustworthy, and which firewall rules could contain the blast radius without breaking recovery. In incidents like that, the expensive part is not typing a command; it is knowing which fact the command proves and which conclusions it does not prove.

Smaller failures feel less dramatic, but they follow the same pattern. A deployment looks green, yet customers see timeouts. A database process is running, yet no remote client can connect. A DNS change was made correctly at the provider, yet one office still resolves the old address. Engineers lose hours when they jump straight from symptom to theory, because every theory sounds plausible when the network is treated as a black box. The practical skill is to turn that black box into a chain of observable questions: can packets leave, can names resolve, is the service listening, does the firewall pass the port, and does the application answer?

This module gives you that chain. You will not memorize every flag in `ping`, `curl`, `ss`, `dig`, `traceroute`, `ufw`, or `iptables`; that would produce a brittle reference habit. Instead, you will learn how each tool narrows a different layer of the problem, what evidence to trust, and where false positives hide. A senior engineer's advantage is not mystical intuition. It is the disciplined habit of collecting cheap, local proof before making expensive changes.

## Build a Troubleshooting Ladder Before Running Commands

Networking tools are most useful when they are arranged as a ladder instead of scattered like a drawer of spare cables. At the bottom of the ladder is reachability: can this machine send a packet toward the target and receive any answer? Above that is name resolution: does the name point to the address you think it points to, and which resolver gave you that answer? Higher still is service behavior: is a process listening on the expected address and port, and can an HTTP or API request complete? At the top are policy and trust checks, including firewalls and checksum verification for tools you download during the fix.

The ladder matters because every step changes the set of likely causes. If `ping` to an IP address works but `curl https://api.example.com/health` fails, the network path probably exists and the failure may be DNS, TLS, HTTP, or application health. If `dig` returns the new address from a public resolver but not from your office resolver, the provider record is probably fine and your local cache or resolver policy deserves attention. If `ss` shows PostgreSQL listening only on `127.0.0.1:5432`, no amount of remote retry logic will make a separate host connect, because the service accepted only loopback traffic by design.

Think of the ladder as a set of receipts. Each command should let you say, "I have evidence for this layer, so I can stop guessing about it." That is why the order often starts with the cheapest tests and moves toward more specific tools. `ping` and `tracepath` test the path broadly, `dig` tests naming, `ss` tests the local socket table, `curl` tests the application protocol, and `ufw` or `iptables` tests host policy. The tools overlap, but they do not replace each other, because a passing result at one layer can hide a failure at another layer.

Here is the mental model you should keep beside the terminal:

```text
+--------------------+     +--------------------+     +--------------------+
| Client process     | --> | Local kernel       | --> | Network path       |
| curl, app, script  |     | sockets, routing   |     | routers, NAT, ACLs |
+--------------------+     +--------------------+     +--------------------+
          |                          |                          |
          v                          v                          v
+--------------------+     +--------------------+     +--------------------+
| DNS resolver       |     | Host firewall      |     | Remote service     |
| dig, host, cache   |     | ufw, iptables      |     | ss, HTTP, TLS      |
+--------------------+     +--------------------+     +--------------------+
```

This diagram is deliberately host-centered. In a Kubernetes 1.35+ cluster, the same questions appear with more layers: pod DNS, Service routing, NetworkPolicy, node firewalls, and cloud load balancers. You still start with evidence. If a node cannot resolve a name, a pod scheduled there inherits a bad starting point. If the host firewall drops a port, a perfectly healthy application may look dead from outside. Before running this ladder on a production issue, pause and predict: which layer would you test first if an IP address works but the hostname fails, and what result would let you move on with confidence?

## Reachability and Path Evidence with `ping` and `traceroute`

`ping` is the first responder because it asks a simple question with a fast answer: can the target receive an ICMP echo request and can your machine receive the reply? That question is narrower than people think. A successful ping proves that one packet type can make a round trip, but it does not prove that TCP port 443 is open or that an application is healthy. A failed ping also does not prove the host is down, because many firewalls and cloud providers block ICMP while leaving normal service ports available.

```bash
# Ping a host - press Ctrl+C to stop
ping google.com

# Ping with a specific number of packets
ping -c 4 google.com

# Ping an IP address directly, which bypasses DNS
ping -c 4 8.8.8.8
```

The most useful habit is to compare name and address behavior. If `ping -c 4 8.8.8.8` succeeds but `ping google.com` fails before it sends packets, the path to the internet may be fine while DNS is broken. If both fail, you may have a local route, VPN, wireless, cloud security group, or upstream firewall problem. If the name ping resolves and sends packets but receives no replies, move to `curl` or a TCP-based traceroute before declaring the host unavailable.

```text
PING google.com (142.250.80.46) 56(84) bytes of data.
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=1 ttl=117 time=5.42 ms
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=2 ttl=117 time=5.38 ms
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=3 ttl=117 time=5.51 ms
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=4 ttl=117 time=5.44 ms

--- google.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 5.380/5.437/5.510/0.047 ms
```

Read the output like a measurement sheet, not like decoration. `icmp_seq` tells you whether replies arrived in order or whether packets disappeared. `time` gives round-trip latency, which includes the outbound trip, remote processing, and return trip. Packet loss is often more important than average latency, because intermittent loss produces flaky deployments, slow package installs, and failed health checks that disappear during a manual retest.

| Field | Meaning |
|-------|---------|
| `64 bytes` | Size of the response packet |
| `icmp_seq=1` | Sequence number; skipped numbers indicate packet loss |
| `ttl=117` | Time to Live after routers decremented the packet on the path |
| `time=5.42 ms` | Round-trip latency for one request and reply |
| `0% packet loss` | The critical health signal for basic reachability |
| `rtt min/avg/max/mdev` | Latency statistics; `mdev` shows jitter or variance |

TTL is a clue, not a fingerprint. Linux often starts at 64, Windows often starts at 128, and network equipment often starts at 255. When you receive a reply with `ttl=52`, a Linux origin about 12 hops away is plausible. When you receive `ttl=115`, a Windows origin about 13 hops away is plausible. The inference is useful during triage, but you should avoid turning it into certainty, because middleboxes, containers, and custom kernel settings can change starting values.

| Starting TTL | Common Source |
|--------------|---------------|
| 64 | Linux and many Unix-like systems |
| 128 | Windows systems |
| 255 | Routers, switches, and network appliances |

`traceroute` complements ping by asking where packets travel, not merely whether they return. It works by sending probes with increasing TTL values. The first probe expires at the first router, the second expires at the second router, and so on until the destination or a maximum hop count is reached. This trick, written by Van Jacobson in 1987, turns a protective IP field into a path discovery tool.

```bash
# Trace the route to a host
traceroute google.com

# Use TCP instead of UDP, which can pass through some firewalls more reliably
traceroute -T google.com

# Alternative: tracepath does not need root and uses UDP
tracepath google.com
```

The trap with traceroute is overconfidence. Asterisks at an intermediate hop often mean only that one router refused to answer probes; they do not automatically mean traffic stopped there. A real path problem is more convincing when latency jumps at one hop and stays high afterward, or when all later hops fail including the destination. When you are debugging customer reports, compare traces from multiple vantage points if possible, because internet routing is asymmetric and the return path may differ from the path you can see.

```text
traceroute to google.com (142.250.80.46), 30 hops max, 60 byte packets
 1  gateway (192.168.1.1)                       1.234 ms   1.112 ms   1.098 ms
 2  isp-router.example.net (10.0.0.1)           8.432 ms   8.215 ms   8.556 ms
 3  * * *
 4  core-router.isp.com (203.0.113.1)          12.654 ms  11.987 ms  12.123 ms
 5  google-peer.isp.com (198.51.100.1)         11.345 ms  11.456 ms  11.234 ms
 6  lhr25s34-in-f14.1e100.net (142.250.80.46)  5.678 ms   5.543 ms   5.612 ms
```

| Column | Meaning |
|--------|---------|
| Hop number | Each line is a router or endpoint along the path |
| Hostname and IP | The identity returned for that hop, when available |
| Three times | Three probe timings to that hop |
| `* * *` | The hop did not answer probes; this is not always a fault |

| Feature | `traceroute` | `tracepath` |
|---------|--------------|-------------|
| Requires root | Usually, depending on probe method | No |
| Probe method | UDP, ICMP, or TCP | UDP |
| MTU discovery | Not the main feature | Reports path MTU details |
| Everyday use | Flexible path testing | Quick non-root path testing |

> **War Story: The misleading hop.** A retail platform saw checkout latency jump during a regional incident. The first traceroute showed stars at an ISP router, so the team blamed that router and opened a low-quality carrier ticket. A second trace from another region showed normal intermediate stars but a consistent latency jump only after traffic crossed an ocean. The useful evidence was not the stars; it was the point where delay became persistent.

Pause and predict: if `ping -c 4 8.8.8.8` succeeds with low latency, but `traceroute -T api.example.com` reaches the destination and `curl` still times out, which layer should you inspect next? The best next step is not another path test. You have enough evidence that packets can travel, so you should move to DNS, port binding, firewall policy, or application protocol behavior depending on the exact timeout.

## HTTP and Download Evidence with `curl` and `wget`

`curl` is the network tool you use when the question becomes protocol-specific. `ping` can tell you that a host may be reachable, but `curl` can show whether a TCP connection opens, whether TLS negotiates, whether the server redirects, which headers return, and whether the body matches your expectation. That makes it the everyday microscope for APIs, load balancers, package endpoints, health checks, and webhook integrations.

```bash
# Simple GET request that shows the response body
curl https://httpbin.org/get

# Follow redirects, such as HTTP to HTTPS
curl -L http://google.com

# Save output to a file
curl -o page.html https://example.com

# Silent mode, useful for scripts that parse the response
curl -s https://httpbin.org/get
```

The first choice is usually whether you want the body, the headers, or the full conversation. A monitoring script that checks a static website every minute may prefer `curl -I` because headers are enough to prove an HTTP response without transferring a large body. An engineer debugging a broken API call should usually prefer `curl -v`, because the verbose stream separates DNS, TCP, TLS, request headers, response headers, and response body. Before running this, what output do you expect if the service is reachable but overloaded: a timeout, a connection refusal, or an HTTP 503 response?

```bash
curl -v https://httpbin.org/get
```

```text
* Trying 3.230.169.85:443...
* Connected to httpbin.org (3.230.169.85)
* SSL connection using TLS 1.3
> GET /get HTTP/2
> Host: httpbin.org
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/2 200
< content-type: application/json
< content-length: 256
< server: gunicorn/19.9.0
<
{
  "headers": { "...": "..." },
  "origin": "203.0.113.42",
  "url": "https://httpbin.org/get"
}
```

The direction markers are the key. Lines beginning with `>` are what your client sent, and lines beginning with `<` are what the server returned. If you see `Connected` followed by an HTTP status, you have proven more than reachability: the port accepted TCP, TLS probably completed for HTTPS, and the server generated an application-layer response. If the status is `429 Too Many Requests`, the fix is not another firewall rule; it is rate-limit handling, backoff, or quota review.

> **War Story: The API rate-limit trap.** A developer wrote a script that called a third-party API with ordinary `curl` output redirected away. The script appeared to fail randomly after 100 requests, and the first investigation chased DNS and firewall theories. Switching to `curl -v` showed `HTTP/1.1 429 Too Many Requests` and a `Retry-After: 60` header, which proved the network was fine and the client needed pacing.

Headers alone are powerful when you are checking redirects, cache behavior, content type, or load balancer identity. `curl -I` makes a HEAD request, while `curl -i` includes response headers before the body. Some services handle HEAD differently from GET, so if a health check built with `curl -I` disagrees with a browser or an application client, test with `curl -i` or `curl -v` before trusting the conclusion.

```bash
# Show headers only
curl -I https://example.com

# Show headers and body together
curl -i https://example.com
```

For downloads, `curl` and `wget` overlap but have different personalities. `curl` is excellent for explicit protocol work and scripts that need headers, methods, uploads, and precise flags. `wget` is convenient when you want files, recursive site downloads, or simple resume behavior. In infrastructure automation, the more important decision is not which tool feels nicer; it is whether the script handles redirects, failures, checksums, and partial files predictably.

```bash
# Download and save with the remote filename
curl -O https://example.com/file.tar.gz

# Download with a custom name
curl -o myfile.tar.gz https://example.com/file.tar.gz

# Resume a broken download
curl -C - -O https://example.com/large-file.iso
```

| Feature | `curl` | `wget` |
|---------|--------|--------|
| Protocols | 25+ | HTTP, HTTPS, FTP |
| API interaction | Excellent | Basic |
| Recursive downloads | No | Yes, with `wget -r` |
| Resume downloads | `curl -C -` | `wget -c` |
| Installed by default | Most distributions | Most distributions |
| Best for | APIs and debugging | Downloading files or sites |

```bash
# wget basics
wget https://example.com/file.tar.gz
wget -c https://example.com/large.iso
wget -q https://example.com/file.tar.gz
```

Downloading a tool is not the same as safely installing it. Infrastructure scripts often fetch `kubectl`, Helm, Terraform, or a vendor agent during CI, then immediately execute the file. That pattern is attractive because it is short, but it expands a supply-chain failure into your build or cluster environment. A safe script downloads the artifact, downloads the published checksum from the same release source, verifies the exact bytes, and only then makes the binary executable.

```bash
# Step 1: Download the file
curl -LO https://example.com/tool-v1.35.0-linux-amd64.tar.gz

# Step 2: Download the checksum file
curl -LO https://example.com/tool-v1.35.0-linux-amd64.tar.gz.sha256

# Step 3: Verify
sha256sum -c tool-v1.35.0-linux-amd64.tar.gz.sha256
```

```text
tool-v1.35.0-linux-amd64.tar.gz: OK
```

When the checksum fails, stop. A mismatch may be a corrupted transfer, a stale checksum file, a mirror problem, or active tampering. The reason does not matter during the first response; the file is not the file the publisher described. The same principle applies when installing Kubernetes 1.35+ tooling. Your script can use the `k` alias after installation, but the binary itself should be verified before it ever talks to a cluster.

```bash
# Generate the checksum for a downloaded file
sha256sum tool-v1.35.0-linux-amd64.tar.gz

# Compare the output with the published checksum before using the file
```

```bash
# Download kubectl targeting current stable v1.35.0
curl -LO "https://dl.k8s.io/release/v1.35.0/bin/linux/amd64/kubectl"

# Download the checksum
curl -LO "https://dl.k8s.io/release/v1.35.0/bin/linux/amd64/kubectl.sha256"

# Verify
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

# Expected output: kubectl: OK
```

The security and reliability implications of artifact trust are further analyzed in Modern DevOps 1.6 (*DevSecOps*).
<!-- incident-xref: codecov-2021-bash-uploader -->
<!-- incident-xref: codecov-2021 -->

## Local Socket Evidence with `ss`

When a remote client cannot connect, the local server may still be the problem. A service can be installed, enabled, and logging "started" while listening on the wrong address or not listening at all. `ss` reads the kernel's socket table and answers a question that logs often blur: which processes own which local sockets right now? That makes it the tool to run before editing firewall rules or blaming the network team.

```bash
# Show all listening TCP and UDP ports with process names
sudo ss -tulpn
```

Each flag removes ambiguity. `-t` and `-u` include TCP and UDP sockets, `-l` keeps only listeners, `-p` asks for owning processes, and `-n` keeps numeric ports instead of translating them into service names. The command often needs `sudo` because process ownership is sensitive. Without elevated permissions, the port may still appear, but the process column can be empty, which robs you of the evidence you needed.

| Flag | Meaning |
|------|---------|
| `-t` | Show TCP sockets |
| `-u` | Show UDP sockets |
| `-l` | Show listening sockets waiting for connections |
| `-p` | Show the process using each socket |
| `-n` | Show port numbers instead of service names |

```text
State    Recv-Q   Send-Q   Local Address:Port    Peer Address:Port   Process
LISTEN   0        128      0.0.0.0:22            0.0.0.0:*           users:(("sshd",pid=892,fd=3))
LISTEN   0        511      0.0.0.0:80            0.0.0.0:*           users:(("nginx",pid=1234,fd=6))
LISTEN   0        4096     127.0.0.1:5432        0.0.0.0:*           users:(("postgres",pid=567,fd=5))
LISTEN   0        4096     [::]:6443             [::]:*              users:(("kube-apiserver",pid=2345,fd=7))
```

The local address is the field that turns vague troubleshooting into concrete design. `0.0.0.0:80` means the process is listening on all IPv4 interfaces, so remote clients can attempt to connect if routing and firewall policy allow it. `127.0.0.1:5432` means only processes on the same host can connect, which is a safe default for many databases but a blocker for a remote microservice. `[::]:6443` is the IPv6 all-interfaces form and often appears for services that also accept IPv4 depending on system configuration.

| Column | Meaning |
|--------|---------|
| `State` | `LISTEN` means the process is waiting for connections |
| `Recv-Q / Send-Q` | Queue sizes; growing values can indicate pressure |
| `Local Address:Port` | The local interface and port the service uses |
| `Peer Address:Port` | For listeners, usually any peer |
| `Process` | Program name, process ID, and file descriptor |

| Address | Who Can Connect |
|---------|-----------------|
| `0.0.0.0:80` | Anyone who can route to the host and pass firewall rules |
| `127.0.0.1:5432` | Only local processes on the same machine |
| `[::]:6443` | IPv6 all interfaces, often relevant for Kubernetes API servers |
| `10.0.1.5:8080` | Clients that can reach that specific private interface |

Useful variations let you narrow the view without losing the underlying proof. Searching for a port is practical during deployment checks, but remember that `grep :80` can match unrelated values in some outputs. `ss -tn` shows established TCP connections rather than listeners, which is useful when you need to know whether clients are currently connected. `ss -s` summarizes socket state and can reveal a host drowning in connections even before you know which process deserves blame.

```bash
# Find what is listening on a specific port
sudo ss -tulpn | grep :80

# Show all established TCP connections
ss -tn

# Count connections per state
ss -s
```

> **War Story: The localhost database.** A team moved a reporting worker from the database host to a separate VM and immediately saw connection refused errors. PostgreSQL was running, logs looked clean, and the firewall allowed the port. `sudo ss -tulpn` showed `127.0.0.1:5432`, which meant the service had never been exposed beyond loopback. The fix was a deliberate database bind-address and access-control change, not a retry loop.

Pause and predict: on a fresh cloud server where you are connected over SSH, which service and port must already be listening for your current terminal session to exist? You should expect an SSH daemon, commonly on TCP port 22, bound to an address reachable from your client. If it is missing from `ss`, either the session is using a different transport, the service name is hidden by permissions, or you are inspecting the wrong machine.

## DNS Evidence with `dig` and `host`

DNS failures are frustrating because they look like network failures from the application side. A browser says a site cannot be reached, a deployment cannot pull from a registry, or a pod cannot connect to a service by name. The first discipline is to separate name resolution from packet delivery. If an IP address works but a name fails, do not keep testing the IP path; collect DNS evidence from the resolver that the system actually uses and from another resolver you trust for comparison.

`host` is the quick tool. It turns a name into addresses, an address into a reverse name, or a query through a specific resolver with minimal ceremony. That makes it useful for a first pass or for scripts that need a compact answer. It is not as detailed as `dig`, but it often tells you whether the problem is "no answer at all" or "the answer is not what I expected."

```bash
# Basic lookup: name to IP
host google.com

# Reverse lookup: IP to name
host 8.8.8.8

# Query a specific DNS server
host google.com 1.1.1.1
```

```text
google.com has address 142.250.80.46
google.com has IPv6 address 2a00:1450:4009:822::200e
google.com mail is handled by 10 smtp.google.com.
```

`dig` is the tool you use when the details matter. It shows the status, answer section, record type, TTL, query time, and server that answered. Those details are how you distinguish a provider mistake from a local cache, a stale corporate resolver, split-horizon DNS, or a missing record type. When you query a specific server with `dig @8.8.8.8`, you bypass the default resolver and collect a second opinion.

```bash
# Basic A record lookup
dig google.com

# Query for specific record types
dig google.com A
dig google.com AAAA
dig google.com CNAME
dig google.com MX
dig google.com NS
dig google.com TXT

# Short answer only, useful for scripts
dig +short google.com

# Query a specific DNS server
dig @8.8.8.8 google.com

# Trace the full DNS resolution path
dig +trace google.com
```

```bash
dig google.com
```

```text
; <<>> DiG 9.18.18 <<>> google.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 54321
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;google.com.                    IN      A

;; ANSWER SECTION:
google.com.             179     IN      A       142.250.80.46

;; Query time: 5 msec
;; SERVER: 127.0.0.53#53(127.0.0.53) (UDP)
;; WHEN: Mon Mar 24 10:00:00 UTC 2026
;; MSG SIZE  rcvd: 55
```

| Section | What It Tells You |
|---------|-------------------|
| `status: NOERROR` | DNS resolution succeeded; `NXDOMAIN` means no such domain |
| `QUESTION SECTION` | The name and record type you requested |
| `ANSWER SECTION` | The returned DNS records |
| `179` | TTL in seconds, meaning how long the answer may be cached |
| `IN A` | Internet class and IPv4 address record type |
| `Query time: 5 msec` | How long the lookup took |
| `SERVER: 127.0.0.53` | Which resolver answered your query |

TTL explains why correct changes still appear wrong. If a record had a 3600-second TTL, a resolver that cached the old value can keep returning it until the timer expires. Your authoritative provider may already have the new value, while a nearby recursive resolver still serves the previous answer. Querying multiple resolvers and checking the TTL lets you tell the difference between a bad change and a normal propagation delay.

A and CNAME records solve different design problems. An A record maps a name directly to an IPv4 address. A CNAME maps one name to another name, and the final target then resolves to one or more addresses. CNAMEs are common with CDNs and managed load balancers because the provider can change the final addresses without asking every customer to edit their DNS. The tradeoff is that CNAME chains add another place to inspect when a name points somewhere surprising.

```bash
# See the CNAME chain
dig www.github.com
```

```text
www.github.com.    CNAME   github.com.
github.com.        A       140.82.121.3
```

> **War Story: The split-horizon surprise.** A company moved an internal API behind a new load balancer and updated public DNS correctly. Engineers on the VPN still reached the old IP because the internal resolver served a private zone with the same name. `dig @8.8.8.8 api.example.com` and `dig api.example.com` returned different answers, which proved the record was not globally wrong; the internal resolver policy was overriding it.

Which approach would you choose here and why: flushing your laptop DNS cache, changing the public record again, or querying the authoritative nameserver first? If the public resolver and authoritative nameserver already show the expected value, changing the record again only creates churn. The better path is to identify which resolver still serves the old value, then decide whether waiting for TTL expiry, flushing a local cache, or updating an internal zone is appropriate.

## Firewall and Policy Evidence with `ufw` and `iptables`

Firewalls create the most confusing symptom in everyday troubleshooting: silence. A refused connection usually tells you that a host answered and no service was listening on the port. A timeout can mean packets disappeared anywhere along the path, including the local host firewall, a cloud security group, a router ACL, or a remote policy device. That is why firewall checks come after you prove the service is listening and before you blame the application.

Ubuntu and Debian systems commonly use `ufw` as a friendly frontend for firewall policy. It is not a separate kernel firewall; it configures packet filtering rules underneath. The value of `ufw` is readability. During an incident, `sudo ufw status verbose` can quickly show whether a host denies inbound traffic by default, which ports are allowed, and whether a specific source has been blocked.

```bash
# Check firewall status and active rules
sudo ufw status verbose

# Allow incoming HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block a specific malicious documentation-range IP address
sudo ufw deny from 203.0.113.50

# Delete a rule if you accidentally blocked something
sudo ufw delete deny from 203.0.113.50
```

Raw `iptables` remains an important fallback skill because many systems, appliances, container runtimes, and older runbooks still expose netfilter policy that way. Reading rules with packet counters and line numbers shows which chain is active and whether packets are matching a rule. You do not need to become a firewall engineer in this module, but you should recognize `INPUT`, `FORWARD`, and `OUTPUT`, and you should know that a default `DROP` policy requires explicit `ACCEPT` rules for expected inbound services.

```bash
# List all active iptables rules with line numbers and packet counts
sudo iptables -L -n -v --line-numbers
```

> **War Story: The silent drop outage.** A Redis cache listened on the expected private interface, and `ss` proved the process owned port 6379. The application still timed out because the host's `INPUT` policy dropped inbound traffic without logging. The team spent hours changing Redis settings before checking firewall counters. The durable fix was a runbook that required `ss`, then `ufw`, then raw `iptables` evidence for every timeout.

In Kubernetes 1.35+ environments, be cautious before changing host firewalls. Nodes may rely on rules installed by kube-proxy, a CNI plugin, or cloud integration. A hasty flush can break pod networking, Services, or node health checks. The safe everyday pattern is read first, make the smallest source-and-port-specific change you can justify, record the reason, and verify with a client from the correct network location. If you use `k get pods -A` during the same incident, keep host evidence and cluster evidence separate so you do not confuse a node firewall issue with an application rollout issue.

## Worked Example: A Timeout That Looks Like Everything

The hardest beginner incidents are the ones where every layer has a partial truth. Imagine an internal API that should listen on `api.internal.example.com:8080`. A developer says DNS is broken because the hostname fails from a laptop. An operations engineer says the service is healthy because systemd reports it as active. A network engineer says the path is fine because the VM responds to ping. Each statement may be true, but none of them is enough to explain why a real client receives a timeout.

```text
+----------------------+     +----------------------+     +----------------------+
| Laptop client        | --> | API virtual machine  | --> | API process          |
| resolver, curl       |     | firewall, routing    |     | bind address, port   |
+----------------------+     +----------------------+     +----------------------+
+----------------------+     +----------------------+     +----------------------+
| dig evidence         |     | ufw/iptables proof   |     | ss/curl evidence     |
+----------------------+     +----------------------+     +----------------------+
+----------------------+     +----------------------+     +----------------------+
+----------------------+     +----------------------+     +----------------------+
```

Start with the client symptom and write it down in operational language: "from the laptop network, `curl -v http://api.internal.example.com:8080/health` times out." That wording is better than "the API is down" because it includes a source, a protocol, a name, a port, and a path. If you change the source to the server itself, the result may change. If you change the name to an IP address, the result may change. If you change the port, the result may change. Those differences are not noise; they are the clues.

The first useful split is name versus address. Run `dig api.internal.example.com` from the affected laptop or from a host on the same network segment. If the resolver returns no answer, an old address, or a private answer that differs from the expected environment, you have a DNS branch to investigate. Querying `dig @8.8.8.8 api.internal.example.com` can help, but only if the name is meant to be public. For internal names, the better second opinion may be the authoritative internal resolver, because public DNS may correctly know nothing about that private zone.

If the name resolves to the expected private IP, move to reachability without pretending ping is a complete service test. A successful `ping -c 4` to the API VM shows that ICMP can make a round trip, which lowers suspicion about basic routing. A failed ping does not end the investigation, because the VM or network may drop ICMP while allowing TCP. When ping is blocked but the symptom is HTTP, a TCP-flavored check such as `curl -v` or `traceroute -T` is more relevant than repeating ICMP tests until someone gets a different result.

Next, inspect the server from the inside. `sudo ss -tulpn` should show whether anything listens on port 8080, which address it binds to, and which process owns it. If the API is listening on `127.0.0.1:8080`, the service can answer local health checks while remaining unreachable from remote clients. If it listens on `10.0.1.5:8080`, clients must route to that private address and pass policy controls. If no process listens, firewall work is premature; the server has no application socket ready to accept the connection.

After the socket evidence looks correct, test the application locally with `curl -v http://127.0.0.1:8080/health` and, if appropriate, `curl -v http://10.0.1.5:8080/health` from the server. This catches a common configuration split where the process listens on all interfaces but the application rejects requests because the Host header, route, or upstream dependency is wrong. A local HTTP 503 points to application or dependency health. A local connection refusal points back to the listener. A local success with remote timeout points toward policy or path.

Only then should you inspect host firewall policy. `sudo ufw status verbose` tells you whether a high-level rule permits the port from the client network. `sudo iptables -L -n -v --line-numbers` can show packet counters increasing on a drop rule, which is stronger evidence than simply seeing a default deny. Packet counters matter because they connect the symptom to the rule: if counters increase while the client retries, you have direct evidence that traffic reaches the host and is discarded there.

This example also shows why changing two things at once is dangerous. If you change DNS and open the firewall together, then the next successful request does not tell you which change mattered. If the request still fails, you now have more states to reason about. The disciplined path is to preserve the before state, run one test, make one narrow change, and repeat the same test from the same source. That rhythm feels slow only when the incident starts; it becomes faster when the room fills with competing theories.

The same ladder works for Kubernetes 1.35+ incidents, but the boundaries move. A pod may resolve through CoreDNS rather than the node resolver. A Service may route through kube-proxy or an eBPF data plane. NetworkPolicy may drop traffic before it reaches the destination container. Still, the host tools remain valuable because they tell you whether the node itself has working DNS, whether a node-level firewall is interfering, and whether a downloaded diagnostic binary was verified before use. Cluster tools add context; they do not remove the need for Linux evidence.

When you write the final incident note, avoid saying only "fixed firewall." A useful note says that DNS returned the expected private IP, ICMP reached the VM, `ss` showed the API listening on `10.0.1.5:8080`, local `curl` succeeded, remote `curl` timed out, and `iptables` counters increased on a drop rule that lacked an allow entry for the client subnet. That sentence teaches the next responder how the conclusion was reached. It also protects the team from undoing the wrong change later.

## Patterns & Anti-Patterns

Patterns are repeated choices that keep troubleshooting disciplined. They are not scripts to run blindly; they are ways to preserve evidence while narrowing the search area. The most reliable pattern is to prove the layer below the one you want to change. Before editing an application health endpoint, prove that TCP and HTTP reach the service. Before changing DNS, prove which resolver returned the bad answer. Before opening a firewall, prove the service listens on the intended address and port.

Anti-patterns usually come from impatience, not ignorance. Under pressure, teams rerun the same command because it feels productive, change multiple layers at once because each change sounds harmless, or treat a single failure as universal proof. That behavior makes incidents longer because it destroys the ability to compare before and after evidence. The better alternative is slower for the first minute and faster for the next hour: write down the symptom, test one layer, record the result, and change only the layer that evidence implicates.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| IP before name | A hostname fails or behaves differently across locations | Separates DNS from packet reachability | Test from the same network as the affected client |
| Listener before firewall | Remote connections time out or refuse | Proves whether a process is actually accepting on the target port | On shared hosts, confirm the owning process before changing policy |
| Verbose protocol check | HTTP, API, TLS, or redirect behavior is unclear | Shows request and response details rather than a vague success or failure | Capture only safe headers; avoid leaking credentials in tickets |
| Checksum before execute | Automation downloads a binary or script | Verifies the bytes match the publisher's release | Pin versions and checksums in repeatable pipelines |

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Assuming ping failure means host down | ICMP may be blocked while TCP services work | Test the actual service port with `curl` or another protocol tool |
| Editing DNS repeatedly during TTL delay | Creates more cache states and hides the original evidence | Query authoritative and recursive resolvers, then wait or flush intentionally |
| Opening `0.0.0.0` without policy review | A private service may become reachable from too many networks | Bind to a specific private address and allow only required sources |
| Flushing firewall rules on cluster nodes | Container networking and Service routing can break unexpectedly | Read counters first and make narrow, reversible changes |

## Decision Framework

The decision framework is simple: choose the tool that can falsify the next likely explanation. If you cannot name the explanation, stop and describe the symptom more precisely. "The app is down" is too broad. "The app host can reach 8.8.8.8, resolves the API name to the old address through the office resolver, and receives HTTP 503 from the load balancer through a public resolver" is actionable because it separates network path, DNS cache, and application health.

| Symptom | First Tool | If It Passes | If It Fails |
|---------|------------|--------------|-------------|
| Hostname does not resolve | `dig` or `host` | Compare resolvers and TTLs | Check local resolver, VPN, or zone configuration |
| IP address seems unreachable | `ping` and `tracepath` | Test the actual service protocol | Check routing, VPN, gateway, or upstream filtering |
| Web or API request fails | `curl -v` | Read status, headers, TLS, and redirects | Distinguish timeout, refusal, DNS, and TLS errors |
| Service should be running locally | `sudo ss -tulpn` | Verify bind address and process owner | Check service status and logs |
| Remote client times out | `ss`, then `ufw`, then `iptables` | Test from the client network | Review local and upstream firewall policy |
| Downloaded tool will run in automation | `sha256sum` | Make executable and continue | Stop and replace the artifact or checksum source |

Use `ping` when the question is broad reachability, but do not use it as the final judge of service health. Use `curl` when HTTP semantics matter, especially for health checks, API debugging, redirects, TLS negotiation, and rate limits. Use `ss` when you control or can log into the server and need local truth about listeners. Use `dig` and `host` when names, TTLs, resolvers, or record types matter. Use `traceroute` and `tracepath` when you need path evidence. Use `ufw` and `iptables` when silence points to policy.

## Did You Know?

- Mike Muuss wrote `ping` in December 1983 and named it after sonar sounds. Its staying power comes from its narrow contract: send an ICMP echo request, measure the reply, and report loss and latency without pretending to test the whole application.
- `curl` began in 1998 and now supports more than 25 protocols, including HTTP, HTTPS, FTP, SFTP, MQTT, and Gopher. That breadth is why it appears in everything from one-line health checks to release automation.
- Google Public DNS at `8.8.8.8` handles more than 1 trillion queries per day. When you compare your resolver with `dig @8.8.8.8`, you are asking one of the busiest public DNS services for an independent answer.
- `traceroute` was written by Van Jacobson in 1987 by using the IP TTL field in a clever way. Increasing TTL one hop at a time lets routers reveal a path even though the field was designed to prevent packets from looping forever.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Assuming ping failure means the host is down | Many hosts and firewalls block ICMP even while service ports are open | Test the actual protocol with `curl`, and compare name versus IP behavior |
| Using `curl` without `-L` for redirected downloads | The request saves a redirect response instead of the intended file | Use `curl -L` when redirects are expected, and verify status codes in scripts |
| Forgetting `sudo` with `ss -p` | The process column can be hidden from unprivileged users | Run `sudo ss -tulpn` when you need the owning process |
| Ignoring bind addresses in `ss` output | A service can listen on loopback while remote clients need access | Distinguish `127.0.0.1`, `0.0.0.0`, specific private IPs, and IPv6 listeners |
| Querying only the default DNS resolver | Local caches, VPN resolvers, or split-horizon zones can hide the authoritative answer | Compare `dig domain`, `dig @8.8.8.8 domain`, and provider or authoritative results |
| Treating `* * *` in traceroute as automatic failure | Intermediate routers often refuse to answer probes while forwarding real traffic | Look for persistent latency jumps or destination failure, not isolated stars |
| Downloading binaries without checksum verification | Automation may execute corrupted or tampered files with high privileges | Download the published checksum and verify with `sha256sum` before execution |
| Changing firewall rules before proving a listener exists | A closed or localhost-only service can look like a policy problem | Run `ss` first, then inspect `ufw` or `iptables` if the listener is correct |

## Quiz

<details><summary>Question 1: Your team reports that a partner API is slow. `ping` replies show `ttl=52`, no packet loss, and an average latency near 90 ms. A colleague says the TTL proves the partner runs Windows and the network is broken. How do you respond?</summary>

The TTL more likely suggests a Linux or Unix-like system that started near 64 and crossed about 12 hops, but TTL is only a clue. The lack of packet loss means basic ICMP reachability looks stable, while the 90 ms average may be normal if geography is involved. You should not conclude that the API is broken from ping alone, because ICMP is not the application protocol. The next useful checks are `curl -v` against the API endpoint and perhaps `traceroute` or `tracepath` to see whether a persistent path latency jump exists.

</details>

<details><summary>Question 2: A deployment health check fails, but `curl -v https://api.example.com/health` shows a completed TLS connection and `< HTTP/2 503`. What layer has been proven healthy enough to move past, and what should you inspect next?</summary>

The verbose output proves DNS, TCP connectivity, and TLS negotiation were healthy enough for the server to return an HTTP response. A 503 means the request reached an HTTP-speaking component, but that component could not serve the request successfully. You should inspect application health, load balancer upstreams, rate limits, or dependency status rather than opening network ports blindly. The `>` lines show what your client sent, and the `<` lines show the server response that carries the useful status.

</details>

<details><summary>Question 3: A reporting worker on another VM cannot reach PostgreSQL. On the database server, `sudo ss -tulpn` shows `127.0.0.1:5432` owned by `postgres`. Can the worker connect, and what change would you evaluate?</summary>

The worker cannot connect to that listener because `127.0.0.1` accepts only local connections from the database host itself. The service is running, but it is bound to loopback rather than a private network interface. The change to evaluate is a deliberate database bind-address update to a private IP or, if appropriate, `0.0.0.0`, paired with database access controls and firewall rules. After the change, rerun `ss` to verify the listener and test from the worker network.

</details>

<details><summary>Question 4: A DNS change should point `app.example.com` to a new address. `dig app.example.com` on your laptop returns the old address with a TTL of 2800, while `dig @8.8.8.8 app.example.com` returns the new address. What does this tell you?</summary>

The provider record may already be correct, while your default resolver is serving a cached or split-horizon answer. The remaining TTL explains why the old value can persist without another provider-side mistake. The right next step is to identify which resolver your laptop uses, whether VPN or office DNS overrides the zone, and whether waiting or flushing a local cache is enough. Editing the public record again would likely create more confusing cache states.

</details>

<details><summary>Question 5: A CI pipeline downloads `kubectl` for Kubernetes 1.35+ with `curl` and immediately executes it. The review blocks the change. What exact risk is being blocked, and what should the script add?</summary>

The risk is executing unverified bytes inside automation that may have access to infrastructure credentials or clusters. A compromised endpoint, stale mirror, interrupted transfer, or tampered artifact could become a trusted binary. The script should download the official checksum file, verify the binary with `sha256sum --check`, and only then make it executable or use it. After installation, defining `alias k=kubectl` is fine for operator convenience, but it does not replace artifact verification.

</details>

<details><summary>Question 6: A remote client times out connecting to an internal API on port 8080. You can SSH to the server. Design the first three checks using the tools in this module.</summary>

First, run `sudo ss -tulpn` on the server to prove whether the API is listening on port 8080 and whether it is bound to a reachable address. Second, test the service locally with `curl -v http://127.0.0.1:8080` or the private address as appropriate, because that separates the application from the remote path. Third, inspect `sudo ufw status verbose` or `sudo iptables -L -n -v --line-numbers` to see whether local policy drops the client's traffic. This order prevents you from changing firewall rules for a service that is not listening.

</details>

<details><summary>Question 7: `traceroute` to a service shows `* * *` at hop 3, normal responses at hops 4 and 5, and the destination responds. A teammate wants to escalate the hop 3 router as the outage. What evidence is missing?</summary>

The missing evidence is that traffic actually stops or degrades at hop 3. Because later hops and the destination respond, hop 3 is probably forwarding traffic while refusing to answer traceroute probes. You would need persistent packet loss, a latency jump that remains high after that point, failure at all later hops, or corroborating traces from affected clients before blaming that router. Isolated stars are common and should not drive escalation by themselves.

</details>

## Hands-On Exercise

### Network Detective Challenge

The goal of this exercise is to build evidence in layers instead of running commands at random. Use any Linux system with internet access, including a VM, WSL2, or a native installation. If you completed Module 0.4 and still have nginx or another service running, you can use that local service for the `ss` and `curl` parts; otherwise, the public examples are enough to practice the method.

#### Task 1: Investigate latency and reachability with `ping`

```bash
# Ping Google's public DNS and observe the results
ping -c 5 8.8.8.8
```

Record the average round-trip time, packet loss, and TTL. Estimate the likely hop count by comparing the received TTL with common starting TTL values. Then write one sentence explaining what this test proves and one sentence explaining what it does not prove.

<details><summary>Solution guidance</summary>

You should be able to identify packet loss, average latency, and a TTL value from the output. If packet loss is 0%, basic ICMP reachability looks healthy, but that does not prove HTTP, DNS, or a specific service port works. The TTL can help you estimate distance, but it should not be treated as a guaranteed operating system fingerprint.

</details>

#### Task 2: Inspect HTTP behavior with `curl`

```bash
# Make a verbose request to httpbin.org and examine the conversation
curl -v https://httpbin.org/headers 2>&1

# Now request just the response headers
curl -I https://httpbin.org/get

# Fetch your apparent IP address as seen by the server
curl -s https://httpbin.org/ip
```

Identify which lines are your request and which lines are the server response. Note the HTTP version, the `Content-Type`, and the public IP reported by httpbin. If a command fails, classify the failure as DNS, connection, TLS, HTTP status, or body-content related.

<details><summary>Solution guidance</summary>

In verbose output, `>` lines are sent by your client and `<` lines are returned by the server. A completed HTTP response means the path and protocol handshake worked far enough to reach the application layer. `curl -I` is efficient for headers, while `curl -v` is better when you need to see the entire conversation.

</details>

#### Task 3: Query DNS records with `dig`

```bash
# Look up google.com A records
dig google.com

# Get just the IP in short form
dig +short google.com

# Check for CNAME records on www.github.com
dig www.github.com

# Query using Google's DNS server specifically
dig @8.8.8.8 google.com
```

Record the returned address, TTL, resolver, and whether `www.github.com` uses a CNAME. Compare the default resolver answer with the answer from `8.8.8.8`. If they differ, explain whether TTL, cache, VPN DNS, or split-horizon policy could explain the difference.

<details><summary>Solution guidance</summary>

The `ANSWER SECTION` tells you which record was returned, while the `SERVER` line tells you which resolver answered. A different answer from a public resolver does not automatically mean one is wrong; it may reflect cache state, internal zones, or geography-aware DNS. TTL gives you the time window during which cached answers may remain valid.

</details>

#### Task 4: Check local listening services with `ss`

```bash
# Show all listening TCP and UDP ports with process names
sudo ss -tulpn

# If you have nginx running from Module 0.4, verify it is listening
sudo ss -tulpn | grep :80
```

Count the listeners, identify at least one process owner, and classify one local address as loopback, all interfaces, IPv6 all interfaces, or a specific private address. If nginx or another web server is running, explain who can connect based on its bind address.

<details><summary>Solution guidance</summary>

The important fields are `Local Address:Port` and `Process`. A listener on `127.0.0.1` is local-only, while `0.0.0.0` accepts traffic on all IPv4 interfaces if firewall and routing policy allow it. If process names are missing, rerun with `sudo` before drawing conclusions.

</details>

#### Task 5: Trace the network path

```bash
# Trace the route to Google's public DNS
traceroute 8.8.8.8

# If traceroute is not installed or hangs, try:
tracepath 8.8.8.8
```

Record the hop count, any `* * *` entries, and whether latency jumps at a point and stays high afterward. Compare the hop count with your TTL estimate from Task 1. Explain why the two numbers may not match exactly.

<details><summary>Solution guidance</summary>

Traceroute shows the outbound path visible to probes, while TTL in ping reflects the return packet's remaining value from the destination. Routes can be asymmetric, and routers may refuse to answer probes while still forwarding traffic. Treat persistent patterns as evidence, not isolated stars.

</details>

#### Task 6: Practice download verification

```bash
# Download the kubectl checksum file and verify the pattern.
# You do not need to install kubectl; this is checksum practice.
curl -LO "https://dl.k8s.io/release/v1.35.0/bin/linux/amd64/kubectl"
curl -LO "https://dl.k8s.io/release/v1.35.0/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

# Clean up
rm -f kubectl kubectl.sha256
```

Explain why checksum verification belongs before execution in a CI/CD pipeline. If the check fails, do not retry by running the binary manually; inspect whether the file, checksum, version, or download source is wrong.

<details><summary>Solution guidance</summary>

The expected success output is `kubectl: OK`. That result means the downloaded bytes match the published checksum. It does not prove the publisher is perfect, but it protects you from corrupted transfers and many tampering scenarios between the release source and your machine.

</details>

### Success Criteria

- [ ] Diagnosed reachability and latency with `ping`, including TTL, packet loss, and what the test does not prove.
- [ ] Debugged HTTP behavior with `curl -v`, identifying request lines, response lines, status, and headers.
- [ ] Evaluated DNS resolver evidence with `dig`, including TTL, record type, and resolver differences.
- [ ] Inspected listening ports with `sudo ss -tulpn` and classified at least one bind address correctly.
- [ ] Compared path evidence from `traceroute` or `tracepath` with the ping TTL estimate.
- [ ] Implemented a safe download verification flow with `curl` and `sha256sum`.

## Key Takeaways

Everyday networking troubleshooting is a discipline of narrowing uncertainty. Start with the question that removes the most guesswork at the lowest cost, then move upward only when the evidence justifies it. `ping` and `tracepath` tell you about reachability and path shape, but they do not prove service health. `dig` and `host` tell you what the resolver believes, but they do not prove the application accepts traffic. `ss` tells you what the local kernel is listening on, but it does not prove remote policy allows the connection.

`curl` connects those layers to application behavior because it exposes the actual HTTP conversation. Firewalls explain silence only after you have proven that a listener exists and the client is testing the right address and port. Checksums protect the tooling you bring into an environment while fixing it. The skill is not running all commands every time; it is choosing the next command because it can prove or disprove a specific explanation.

## Next Module

Next, move into [Module 1.1: Kernel & Architecture](/linux/foundations/system-essentials/module-1.1-kernel-architecture/) to connect these everyday commands to the kernel mechanisms, sockets, and system calls that make Linux networking work.

## Further Reading

- [curl Documentation](https://curl.se/docs/)
- [curl Manual](https://curl.se/docs/manpage.html)
- [dig Manual](https://linux.die.net/man/1/dig)
- [ss(8) Man Page](https://man7.org/linux/man-pages/man8/ss.8.html)
- [ip(8) Man Page](https://man7.org/linux/man-pages/man8/ip.8.html)
- [An Introduction to DNS Terminology](https://www.digitalocean.com/community/tutorials/an-introduction-to-dns-terminology-components-and-concepts)
- [How Traceroute Works](https://networklessons.com/cisco/ccna-routing-switching-icnd1-100-105/traceroute)
- [Linux Kernel Networking Documentation](https://www.kernel.org/doc/html/latest/networking/index.html)
- [Netfilter Documentation](https://www.netfilter.org/documentation/)
- [firewalld Documentation](https://firewalld.org/documentation/)
- [Install kubectl on Linux](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
