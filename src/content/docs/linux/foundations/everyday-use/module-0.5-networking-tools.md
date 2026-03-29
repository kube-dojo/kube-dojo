---
title: "Module 0.5: Everyday Networking Tools"
slug: linux/foundations/everyday-use/module-0.5-networking-tools
sidebar:
  order: 6
---
> **Everyday Use** | Complexity: `[QUICK]` | Time: 45 min

## Prerequisites

Before starting this module:
- **Required**: [Module 0.2 — Environment & Permissions](../module-0.2-environment-permissions/) (you need to be comfortable with sudo and basic file paths)
- **Helpful**: [Module 0.4 — Services & Logs Demystified](../module-0.4-services-logs/) (the exercise references checking services with `ss`)

---

## Why This Module Matters

Something is broken. The app won't connect. DNS isn't resolving. The API returns a weird status code. A pod can't reach its database.

What do you do?

You **investigate**. And the tools in this module are your detective kit. Every DevOps engineer, every SRE, every platform engineer reaches for these tools first — before reading logs, before checking dashboards, before asking anyone else. They are the stethoscope you press against the network to hear what's going on.

The difference between a junior and senior engineer troubleshooting a network issue? The senior already knows which five commands to run. After this module, so will you.

---

## Did You Know?

- **`ping` is one of the oldest networking tools still in daily use.** Mike Muuss wrote it in December 1983 — he named it after sonar ping sounds from submarine movies. The tool has barely changed in 40+ years because it does one thing perfectly.

- **`curl` supports over 25 protocols**, including HTTP, HTTPS, FTP, SFTP, MQTT, and even Gopher. Its creator, Daniel Stenberg, has maintained it since 1998 and it's installed on over 20 billion devices. Yes, *billion*.

- **Google's public DNS (8.8.8.8) handles over 1 trillion queries per day.** When you `ping 8.8.8.8` or `dig @8.8.8.8`, you're talking to one of the busiest services on Earth — and it still responds in milliseconds.

- **The `traceroute` tool was written by Van Jacobson in 1987** by cleverly abusing the TTL (Time to Live) field in IP packets. Each hop decrements TTL by 1, and when it hits 0, the router sends back an error. By incrementing TTL from 1 upward, traceroute maps every router along the path. Brilliant hack.

---

## Tool 1: Testing Connectivity with `ping`

`ping` is the first thing you reach for when something seems unreachable. It sends ICMP echo requests to a host and reports whether (and how fast) they come back.

### Basic Usage

```bash
# Ping a host — press Ctrl+C to stop
ping google.com

# Ping with a specific number of packets (no need for Ctrl+C)
ping -c 4 google.com

# Ping an IP address directly (bypasses DNS)
ping -c 4 8.8.8.8
```

### Reading the Output

Here's what `ping` output actually looks like:

```
PING google.com (142.250.80.46) 56(84) bytes of data.
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=1 ttl=117 time=5.42 ms
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=2 ttl=117 time=5.38 ms
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=3 ttl=117 time=5.51 ms
64 bytes from lhr25s34-in-f14.1e100.net (142.250.80.46): icmp_seq=4 ttl=117 time=5.44 ms

--- google.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 5.380/5.437/5.510/0.047 ms
```

Let's decode every field:

| Field | Meaning |
|-------|---------|
| `64 bytes` | Size of the response packet |
| `icmp_seq=1` | Sequence number — if numbers skip, packets were lost |
| `ttl=117` | **Time to Live** — starts at 64, 128, or 255 (depending on OS) and decreases by 1 at each router hop. TTL of 117 from a starting value of 128 means ~11 hops away |
| `time=5.42 ms` | **Round-trip latency** — how long the packet took to go there and come back |
| `0% packet loss` | The critical metric — any loss indicates a problem |
| `rtt min/avg/max/mdev` | Latency statistics — `mdev` is jitter (variance in latency) |

### What TTL Tells You

TTL is a detective's clue. Different operating systems start with different TTL values:

| Starting TTL | Operating System |
|-------------|-----------------|
| 64 | Linux |
| 128 | Windows |
| 255 | Network equipment (routers, switches) |

If you ping a server and see `ttl=52`, it's probably a Linux box (64 - 12 hops = 52). If you see `ttl=115`, likely Windows (128 - 13 hops = 115).

### When Ping Fails

No response doesn't always mean the host is down. Many servers and firewalls block ICMP. Cloud providers often drop ping traffic. If ping fails, try `curl` next — the host might be alive but just ignoring your pings.

---

## Tool 2: HTTP Interaction with `curl`

`curl` is the Swiss Army knife of network tools. If ping tells you "the host is alive," curl tells you "and here's what it's saying."

### Basic Requests

```bash
# Simple GET request — shows the response body
curl https://httpbin.org/get

# Follow redirects (many sites redirect HTTP → HTTPS)
curl -L http://google.com

# Save output to a file
curl -o page.html https://example.com

# Silent mode (no progress bar) — great for scripts
curl -s https://httpbin.org/get
```

### Verbose Mode: See Everything

This is where curl becomes a real detective tool. The `-v` flag shows the full conversation between your machine and the server:

```bash
curl -v https://httpbin.org/get
```

Output (annotated):

```
* Trying 3.230.169.85:443...                      ← Connecting to IP on port 443
* Connected to httpbin.org (3.230.169.85)          ← TCP connection established
* SSL connection using TLS 1.3                     ← TLS handshake details
> GET /get HTTP/2                                  ← YOUR request (lines start with >)
> Host: httpbin.org
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/2 200                                       ← SERVER response (lines start with <)
< content-type: application/json
< content-length: 256
< server: gunicorn/19.9.0
<
{                                                  ← Response body
  "headers": { ... },
  "origin": "203.0.113.42",
  "url": "https://httpbin.org/get"
}
```

Key insight: lines with `>` are what **you sent**, lines with `<` are what **the server replied**. This is invaluable for debugging API issues.

### Viewing Just Headers

Sometimes you only care about the response headers, not the body:

```bash
# Show headers only
curl -I https://example.com

# Show headers AND body
curl -i https://example.com
```

### Downloading Files

```bash
# Download and save with the remote filename
curl -O https://example.com/file.tar.gz

# Download with a custom name
curl -o myfile.tar.gz https://example.com/file.tar.gz

# Resume a broken download
curl -C - -O https://example.com/large-file.iso
```

### A Quick Word on `wget`

`wget` is another download tool. The main differences:

| Feature | `curl` | `wget` |
|---------|--------|--------|
| Protocols | 25+ | HTTP, HTTPS, FTP |
| API interaction | Excellent | Basic |
| Recursive downloads | No | Yes (`wget -r`) |
| Resume downloads | `curl -C -` | `wget -c` |
| Installed by default | Most distros | Most distros |
| Best for | APIs, debugging | Downloading files/sites |

**Rule of thumb**: use `curl` for APIs and debugging, `wget` for bulk downloading.

```bash
# wget basics
wget https://example.com/file.tar.gz          # Download a file
wget -c https://example.com/large.iso          # Resume interrupted download
wget -q https://example.com/file.tar.gz        # Quiet mode
```

---

## Tool 3: Checking Open Ports with `ss`

`ss` (socket statistics) shows you what's listening on your machine. When you deploy a service and wonder "is it actually running and accepting connections?" — this is your answer.

> **Note**: You might see older references to `netstat`. The `ss` command replaced it — it's faster and provides more information. Use `ss`.

### The Key Command

```bash
# Show all listening TCP and UDP ports with process names
sudo ss -tulpn
```

Let's break down those flags:

| Flag | Meaning |
|------|---------|
| `-t` | Show TCP sockets |
| `-u` | Show UDP sockets |
| `-l` | Show only **listening** sockets (waiting for connections) |
| `-p` | Show the **process** using each socket |
| `-n` | Show port **numbers** instead of service names |

### Reading the Output

```
State    Recv-Q   Send-Q   Local Address:Port    Peer Address:Port   Process
LISTEN   0        128      0.0.0.0:22            0.0.0.0:*           users:(("sshd",pid=892,fd=3))
LISTEN   0        511      0.0.0.0:80            0.0.0.0:*           users:(("nginx",pid=1234,fd=6))
LISTEN   0        4096     127.0.0.1:5432        0.0.0.0:*           users:(("postgres",pid=567,fd=5))
LISTEN   0        4096     [::]:6443             [::]:*              users:(("kube-apiserver",pid=2345,fd=7))
```

Here's what each column means:

| Column | Meaning |
|--------|---------|
| `State` | `LISTEN` means it's waiting for connections |
| `Recv-Q / Send-Q` | Queue sizes — usually 0. If they grow, the service is struggling |
| `Local Address:Port` | **What interface and port** the service listens on |
| `Peer Address:Port` | For listening sockets, always `*` (accepting from anyone) |
| `Process` | The actual program and its PID |

### Understanding Local Addresses

The local address tells you **who can connect**:

| Address | Who Can Connect |
|---------|----------------|
| `0.0.0.0:80` | Anyone (all interfaces) — typical for web servers |
| `127.0.0.1:5432` | Only localhost — typical for databases |
| `[::]:6443` | Anyone (IPv6 all interfaces) |
| `10.0.1.5:8080` | Only via that specific IP |

### Useful Variations

```bash
# Find what's listening on a specific port
sudo ss -tulpn | grep :80

# Show all established connections (not just listening)
ss -tn

# Count connections per state
ss -s
```

---

## Tool 4: DNS Lookups with `dig` and `host`

DNS translates names to IP addresses. When "the website isn't loading," the first question is: **is DNS working?**

### Quick Lookups with `host`

`host` is the fast-and-simple option:

```bash
# Basic lookup — name to IP
host google.com

# Reverse lookup — IP to name
host 8.8.8.8

# Query a specific DNS server
host google.com 1.1.1.1
```

Output:

```
google.com has address 142.250.80.46
google.com has IPv6 address 2a00:1450:4009:822::200e
google.com mail is handled by 10 smtp.google.com.
```

### Detailed Lookups with `dig`

`dig` gives you the full picture. It's what you use when you need to understand *exactly* what DNS is doing:

```bash
# Basic A record lookup
dig google.com

# Query for a specific record type
dig google.com A          # IPv4 addresses
dig google.com AAAA       # IPv6 addresses
dig google.com CNAME      # Canonical name (alias)
dig google.com MX         # Mail servers
dig google.com NS         # Name servers
dig google.com TXT        # Text records (SPF, verification, etc.)

# Short answer only (great for scripts)
dig +short google.com

# Query a specific DNS server
dig @8.8.8.8 google.com

# Trace the full DNS resolution path
dig +trace google.com
```

### Reading `dig` Output

```bash
dig google.com
```

```
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

The key parts:

| Section | What It Tells You |
|---------|-------------------|
| `status: NOERROR` | DNS resolution succeeded. `NXDOMAIN` means "no such domain" |
| `QUESTION SECTION` | What you asked for |
| `ANSWER SECTION` | The actual DNS record(s) returned |
| `179` | **TTL in seconds** — how long the result is cached. After 179s, the resolver will ask again |
| `IN A` | Record class (Internet) and type (A = IPv4 address) |
| `Query time: 5 msec` | How long the lookup took |
| `SERVER: 127.0.0.53` | Which DNS server answered your query |

### A vs CNAME Records

Two record types you'll encounter constantly:

- **A record**: Maps a name directly to an IP address.
  `google.com → 142.250.80.46`

- **CNAME record**: Maps a name to another name (alias).
  `www.example.com → example.com → 93.184.216.34`

```bash
# See the CNAME chain
dig www.github.com

# You'll see:
# www.github.com.    CNAME   github.com.
# github.com.        A       140.82.121.3
```

CNAMEs are how CDNs and load balancers work — `myapp.example.com` might CNAME to `d1234.cloudfront.net`, which resolves to different IPs depending on your location.

---

## Tool 5: Tracing Network Paths with `traceroute`

`ping` tells you if a host is reachable. `traceroute` tells you **the path packets take to get there** — every router along the way.

### How It Works

Remember TTL from the ping section? `traceroute` exploits it brilliantly:

1. Send a packet with TTL=1 → first router decrements to 0, sends back "time exceeded"
2. Send a packet with TTL=2 → second router sends back "time exceeded"
3. Send a packet with TTL=3 → third router replies
4. Repeat until you reach the destination

### Basic Usage

```bash
# Trace the route to a host
traceroute google.com

# Use TCP instead of UDP (better for getting through firewalls)
traceroute -T google.com

# Alternative: tracepath (doesn't need root, uses UDP)
tracepath google.com
```

### Reading the Output

```
traceroute to google.com (142.250.80.46), 30 hops max, 60 byte packets
 1  gateway (192.168.1.1)     1.234 ms  1.112 ms  1.098 ms
 2  isp-router.example.net (10.0.0.1)   8.432 ms  8.215 ms  8.556 ms
 3  * * *
 4  core-router.isp.com (203.0.113.1)   12.654 ms  11.987 ms  12.123 ms
 5  google-peer.isp.com (198.51.100.1)   11.345 ms  11.456 ms  11.234 ms
 6  lhr25s34-in-f14.1e100.net (142.250.80.46)  5.678 ms  5.543 ms  5.612 ms
```

| Column | Meaning |
|--------|---------|
| Hop number | Each line is a router along the path |
| Hostname (IP) | The router's identity |
| Three times | Three probes sent — shows latency to *that* hop |
| `* * *` | Router didn't respond (firewall, ICMP disabled — not necessarily a problem) |

### What to Look For

- **Sudden latency jump**: If hop 4 is 12ms and hop 5 is 150ms, there's a slow link between them (or geographic distance — packets crossing an ocean will jump by 60-100ms)
- **Consistent high latency from a hop onward**: Problem is at that hop or the link before it
- **Stars (`* * *`)**: Often just means that router blocks ICMP. Don't panic unless *all* remaining hops are stars
- **Asymmetric paths**: The return path might be different from the outgoing path — a common source of confusion

### `traceroute` vs `tracepath`

| Feature | `traceroute` | `tracepath` |
|---------|-------------|-------------|
| Requires root | Usually (for raw sockets) | No |
| Probe method | UDP, ICMP, or TCP | UDP only |
| MTU discovery | No | Yes |
| Installed by default | Usually | Usually |

For most everyday troubleshooting, either works fine.

---

## Tool 6: Downloading and Verifying Files

In DevOps, you constantly download binaries — kubectl, helm, terraform, container images. But how do you know the file wasn't tampered with? **Checksums.**

### The Pattern: Download, Then Verify

```bash
# Step 1: Download the file
curl -LO https://example.com/tool-v1.2.3-linux-amd64.tar.gz

# Step 2: Download the checksum file
curl -LO https://example.com/tool-v1.2.3-linux-amd64.tar.gz.sha256

# Step 3: Verify
sha256sum -c tool-v1.2.3-linux-amd64.tar.gz.sha256
```

If the checksums match, you'll see:

```
tool-v1.2.3-linux-amd64.tar.gz: OK
```

If they don't match — **do not use the file.** It may be corrupted or tampered with.

### Manual Verification

Sometimes you need to compare checksums manually:

```bash
# Generate the checksum for a downloaded file
sha256sum tool-v1.2.3-linux-amd64.tar.gz

# Output: a1b2c3d4e5f6...  tool-v1.2.3-linux-amd64.tar.gz

# Compare visually (or in a script) with the published checksum
```

### Real-World Example: kubectl

This is exactly how you install kubectl safely:

```bash
# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Download the checksum
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"

# Verify
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

# Expected output: kubectl: OK
```

If you skip verification and install a compromised binary, you've just given an attacker kubectl access to your clusters. Always verify.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Assuming ping failure = host down | Many hosts and firewalls block ICMP | Use `curl` or `ss` to check if the service port is actually reachable |
| Using `curl` without `-L` for redirects | You get a 301/302 response instead of the actual content | Always use `curl -L` when downloading or following URLs |
| Forgetting `sudo` with `ss -p` | The process column appears empty without root | Use `sudo ss -tulpn` to see which process owns each socket |
| Not specifying a DNS server with `dig` | You get cached or split-horizon results | Use `dig @8.8.8.8 domain.com` to query a specific, known resolver |
| Ignoring the TTL in `dig` output | You don't understand why DNS changes "aren't working" | Check TTL — old records may be cached. Wait for TTL to expire or flush local cache |
| Running `traceroute` and panicking at `* * *` | Stars just mean that hop doesn't respond to probes | Only worry if the destination itself is unreachable. Intermediate stars are normal |
| Downloading binaries without checksum verification | You could install corrupted or tampered files | Always download `.sha256` files and verify with `sha256sum -c` |
| Using `netstat` instead of `ss` | `netstat` is deprecated and slower on busy systems | Use `ss` — it's the modern replacement, faster and more informative |

---

## Quiz

Test your understanding:

### Question 1
You ping a server and get `ttl=52` in the response. What can you infer about the remote server's operating system and how many hops away it is?

<details>
<summary>Show Answer</summary>

The TTL of 52 most likely indicates a **Linux server** (starting TTL of 64). The packet crossed **12 router hops** to reach you (64 - 52 = 12). If the starting TTL were 128 (Windows), it would mean 76 hops — far too many for a typical internet path. So Linux is the most reasonable guess.

</details>

### Question 2
You run `curl -v https://api.example.com/health` and see `< HTTP/2 503` in the output. What does this tell you, and which lines show your request versus the server's response?

<details>
<summary>Show Answer</summary>

The `503` status code means **Service Unavailable** — the server is up and responding, but the application behind it (or the load balancer) can't handle the request right now. Lines starting with `>` show **your request** (what curl sent). Lines starting with `<` show the **server's response**. This is critical for debugging — you can see exactly what headers you sent and what the server replied with.

</details>

### Question 3
You run `sudo ss -tulpn` and see a service listening on `127.0.0.1:5432`. Can a remote machine connect to this service? Why or why not?

<details>
<summary>Show Answer</summary>

**No, a remote machine cannot connect.** The address `127.0.0.1` (localhost/loopback) means the service only accepts connections originating from the same machine. For remote access, the service would need to listen on `0.0.0.0:5432` (all interfaces) or a specific external IP address. This is a common security practice for databases like PostgreSQL — they listen on localhost by default to prevent unauthorized remote access.

</details>

### Question 4
You run `dig +short example.com` and get no output, but `dig +short example.com @8.8.8.8` returns `93.184.216.34`. What's the most likely issue?

<details>
<summary>Show Answer</summary>

Your **local DNS resolver is failing or misconfigured**. The first command uses your system's default DNS server (configured in `/etc/resolv.conf`), which returned no answer. The second command bypasses it entirely by querying Google's public DNS directly, which works fine. Fix your local DNS configuration — check `/etc/resolv.conf` and your network settings, or restart `systemd-resolved` if applicable.

</details>

### Question 5
Why is it dangerous to skip checksum verification when downloading a binary like kubectl?

<details>
<summary>Show Answer</summary>

Without checksum verification, you have no way to confirm the file is **authentic and intact**. The risks include:

- **Supply chain attacks**: An attacker could compromise the download server or perform a man-in-the-middle attack, serving you a modified binary with a backdoor
- **Corrupted downloads**: Network issues could produce a partially downloaded or corrupted file that behaves unpredictably
- **Compromised infrastructure**: If you install a tampered `kubectl`, the attacker gets access to every Kubernetes cluster you manage with it

The `sha256sum` verification takes seconds and confirms the file matches exactly what the maintainers published.

</details>

---

## Hands-On Exercise

### Network Detective Challenge

**Objective**: Use all five categories of networking tools to investigate and verify connectivity on your system.

**Environment**: Any Linux system with internet access (VM, WSL2, or native). If you completed Module 0.4 and have nginx or another service running, even better.

#### Part 1: Investigate Latency with `ping`

```bash
# Ping Google's public DNS and observe the results
ping -c 5 8.8.8.8
```

**Record your findings:**
- What is the average round-trip time?
- What is the TTL value? How many hops away is Google's DNS?
- Is there any packet loss?

#### Part 2: Explore HTTP Headers with `curl`

```bash
# Make a verbose request to httpbin.org and examine the conversation
curl -v https://httpbin.org/headers 2>&1

# Now request just the response headers
curl -I https://httpbin.org/get

# Fetch your apparent IP address (as seen by the server)
curl -s https://httpbin.org/ip
```

**Record your findings:**
- What HTTP version did the server use?
- What `Content-Type` header did the server return?
- What is your public IP address according to httpbin?

#### Part 3: Query DNS Records with `dig`

```bash
# Look up google.com A records
dig google.com

# Get just the IP (short form)
dig +short google.com

# Check for CNAME records on www.github.com
dig www.github.com

# Query using Google's DNS server specifically
dig @8.8.8.8 google.com
```

**Record your findings:**
- What IP address(es) does `google.com` resolve to?
- What is the TTL on the record?
- Does `www.github.com` have a CNAME? If so, what does it point to?

#### Part 4: Check Local Listening Services with `ss`

```bash
# Show all listening TCP and UDP ports with process names
sudo ss -tulpn

# If you have nginx running from Module 0.4, verify it's listening
sudo ss -tulpn | grep :80
```

**Record your findings:**
- How many services are currently listening on your system?
- Is SSH listening? On what address and port?
- If nginx is running, what address is it bound to — `127.0.0.1` or `0.0.0.0`?

#### Part 5: Trace the Network Path

```bash
# Trace the route to Google's public DNS
traceroute 8.8.8.8

# If traceroute isn't installed or hangs, try:
tracepath 8.8.8.8
```

**Record your findings:**
- How many hops to reach 8.8.8.8?
- Does the hop count roughly match what you calculated from the TTL in Part 1?
- Are there any `* * *` entries? (This is normal — don't worry about them.)

#### Bonus: Download and Verify a File

```bash
# Download the kubectl checksum file and verify the pattern
# (You don't need to install kubectl — just practice the verification flow)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

# Clean up
rm -f kubectl kubectl.sha256
```

### Success Criteria

- [ ] Pinged 8.8.8.8 and can explain TTL, latency, and packet loss from the output
- [ ] Used `curl -v` to inspect HTTP headers and identified request (`>`) vs response (`<`) lines
- [ ] Queried DNS with `dig` and can read the answer section, TTL, and record type
- [ ] Listed listening ports with `sudo ss -tulpn` and identified at least one running service
- [ ] Ran a traceroute and can explain what each hop represents
- [ ] (Bonus) Downloaded a file and verified its SHA-256 checksum

---

## Key Takeaways

1. **`ping` is your first responder** — It tells you if a host is reachable and how fast the connection is. Read the TTL to estimate hops and guess the OS.

2. **`curl -v` is your HTTP microscope** — It shows the full request/response conversation. Learn to read the `>` and `<` lines for debugging any API or web issue.

3. **`ss -tulpn` answers "is it listening?"** — Before blaming the network, check that your service is actually bound to the right address and port.

4. **`dig` shows you DNS truth** — When names won't resolve, `dig` tells you exactly what DNS is returning (or not returning), and querying a known-good server like 8.8.8.8 isolates whether it's your resolver or the domain.

5. **`traceroute` maps the path** — When connectivity is slow or failing, traceroute shows you where the problem is along the route.

6. **Always verify downloads** — `sha256sum` takes seconds and protects you from corrupted or tampered binaries. Never skip it.

---

## What's Next?

Congratulations — you've completed the **Everyday Use** series! You can now navigate the CLI, manage permissions, wrangle processes, work with services and logs, and investigate network issues like a pro. These are the tools you'll reach for every single day.

You're ready for the deep dive. In [**Module 1.1: Kernel & Architecture**](../../foundations/system-essentials/module-1.1-kernel-architecture/), you'll learn how Linux *actually* works under the hood — the kernel, system calls, and the architecture that makes everything you've learned so far possible. The everyday tools got you comfortable; now it's time to understand the machine.

---

## Further Reading

- [curl Documentation](https://curl.se/docs/) — Daniel Stenberg's comprehensive docs
- [dig Manual](https://linux.die.net/man/1/dig) — Full reference for DNS queries
- [ss(8) Man Page](https://man7.org/linux/man-pages/man8/ss.8.html) — Socket statistics reference
- [An Introduction to DNS Terminology](https://www.digitalocean.com/community/tutorials/an-introduction-to-dns-terminology-components-and-concepts) — Great primer on DNS concepts
- [How Traceroute Works](https://networklessons.com/cisco/ccna-routing-switching-icnd1-100-105/traceroute) — Visual explanation of the TTL trick
