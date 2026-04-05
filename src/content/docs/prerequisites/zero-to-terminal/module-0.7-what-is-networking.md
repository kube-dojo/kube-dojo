---
title: "Module 0.7: What is Networking?"
slug: prerequisites/zero-to-terminal/module-0.7-what-is-networking
sidebar:
  order: 8
---
> **Complexity**: `[QUICK]` - Absolute beginner
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 0.4: Files and Directories](../module-0.4-files-and-directories/) — You should be comfortable running commands and navigating directories.

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Explain** how computers find each other using IP addresses and DNS
- **Distinguish** between local and public IP addresses and know when each matters
- **Use** `ping`, `curl`, and `nslookup` to diagnose basic connectivity issues
- **Interpret** HTTP status codes (200, 404) and explain what they mean

---

## Why This Module Matters

Kubernetes is a system for running applications across **multiple computers** that talk to each other over a **network**. If you don't understand what a network is, what an IP address means, or what a port does, Kubernetes will feel like magic — and not the good kind.

This module gives you the mental model. By the end, you'll understand how computers find each other, how they communicate, and you'll have used real networking commands from your terminal.

---

## What is a Network?

A **network** is two or more computers connected together so they can share information.

That's it. That's the whole concept.

Your home Wi-Fi? That's a network. The internet? That's a network of networks — millions of computers all connected. When you visit google.com, your computer sends a message across the network to Google's computer, which sends a message back.

> Restaurant kitchen analogy: A network is like the **intercom system** in a large restaurant chain. Each kitchen (computer) has its own intercom (network connection). Any kitchen can call any other kitchen to share recipes, request supplies, or coordinate orders. The intercom system connecting all the kitchens? That's the network.

### Local vs. Internet

| Type | What It Is | Example |
|------|-----------|---------|
| **Local Network (LAN)** | Computers near each other, connected directly | Your laptop and printer on home Wi-Fi |
| **Internet (WAN)** | Computers anywhere in the world, connected through infrastructure | Your laptop talking to a server in Tokyo |

In Kubernetes, you'll work with both: local networks inside a cluster (where containers talk to each other) and internet connections from the outside world to your applications.

---

## IP Addresses: How Computers Find Each Other

Every computer on a network has an **IP address** — a unique number that identifies it, like a street address identifies a building.

```
192.168.1.42
```

This is an IP address. It's four numbers separated by dots, each between 0 and 255.

### The Street Address Analogy

| Concept | Network | Real World |
|---------|---------|-----------|
| IP Address | `192.168.1.42` | 123 Main Street |
| What it does | Identifies one specific computer | Identifies one specific building |
| Who assigns it | Your router (for local) or your ISP (for internet) | The city planning office |

### Types of IP Addresses

**Private IP addresses** — used inside your local network:

```
192.168.x.x    (most common for home networks)
10.x.x.x       (common in offices and data centers)
172.16-31.x.x  (less common but valid)
```

These only work within your local network. It's like apartment numbers — they make sense inside the building, but someone outside wouldn't know which building you mean.

**Public IP addresses** — your address on the internet:

Your router has a public IP that the rest of the internet can see. Every device behind your router shares this one public address.

### Finding Your IP Address

**On macOS:**

```bash
$ ipconfig getifaddr en0
192.168.1.42
```

**On Linux:**

```bash
$ hostname -I
192.168.1.42
```

**On any system (your public IP):**

```bash
$ curl -s ifconfig.me
203.0.113.55
```

> Don't worry if the output looks different from the examples. The numbers will vary — that's expected, because every computer gets its own unique address.

---

## Ports: Many Doors on One Address

> **Stop and think**: Imagine a single physical server hosting three different company websites and an internal email system, all sharing the exact same public IP address. When a customer's browser sends a request to that IP, what mechanical sorting process ensures the request reaches the correct website instead of the email system?

So every computer has an IP address. But a computer runs many programs at once — a web browser, an email client, a chat app. How does the computer know which program should receive an incoming message?

That's what **ports** are for.

A **port** is a number (from 0 to 65535) that identifies a specific program or service on a computer.

### The Apartment Building Analogy

If an IP address is a **street address** (the building), then a port is the **apartment number** (which unit inside the building).

```
IP Address:  192.168.1.42     = 123 Main Street
Port:        80               = Apartment 80

Full address: 192.168.1.42:80 = 123 Main Street, Apt 80
```

The colon `:` separates the IP address from the port number.

### Common Ports

| Port | Service | What It Does |
|------|---------|-------------|
| 80 | HTTP | Regular web traffic (when you visit a website) |
| 443 | HTTPS | Secure web traffic (the padlock in your browser) |
| 22 | SSH | Secure remote terminal access |
| 53 | DNS | Domain name lookups |
| 6443 | Kubernetes API | How `kubectl` talks to your cluster |

> In Kubernetes, you'll see ports everywhere. Every service has a port. Every container exposes ports. Understanding this concept now saves you enormous confusion later.

---

## DNS: The Phone Book of the Internet

When you type `google.com` in your browser, your computer doesn't actually know where `google.com` is. Computers only understand IP addresses (numbers). So how does it work?

> **Pause and predict**: If you disconnect your computer from the internet, you can still reach your home router by typing `192.168.1.1` into your browser, but typing `router.local` might fail. Based on how computers identify each other, what specific infrastructure piece is missing when you try to use the human-readable name offline?

**DNS** — the **Domain Name System** — translates human-friendly names into IP addresses.

```
You type:    google.com
DNS returns: 142.250.80.46
Your computer connects to: 142.250.80.46
```

### The Phone Book Analogy

| Without DNS | With DNS |
|-------------|----------|
| "Call 142.250.80.46" | "Call Google" |
| You need to memorize numbers | You just remember names |
| Like the old days of memorizing phone numbers | Like your phone's contact list |

DNS is why you don't need to type `142.250.80.46` every time you want to search something. You type `google.com` and DNS looks up the number for you.

### How DNS Works (Simplified)

```
1. You type: google.com
2. Your computer asks your router: "What's the IP for google.com?"
3. Your router asks a DNS server: "What's the IP for google.com?"
4. The DNS server responds: "142.250.80.46"
5. Your computer connects to 142.250.80.46
```

This all happens in milliseconds. You never notice it.

---

## Putting It All Together: Sending a Letter

Let's use one big analogy to connect everything:

**Visiting a website is like sending a letter.**

```
1. You want to send a letter to "Google HQ"
   (You type google.com)

2. You look up the address in the phone book
   (DNS translates google.com → 142.250.80.46)

3. You write the street address on the envelope
   (IP address: 142.250.80.46)

4. You write the apartment/department number
   (Port: 443 for HTTPS)

5. You put the letter in the mailbox
   (Your computer sends the request over the network)

6. Google receives it and sends a reply
   (The web page comes back to your browser)
```

And just like that, you understand the basics of networking.

---

## Your First Networking Commands

Let's get our hands dirty. Open your terminal and try these.

### `ping` — "Are You There?"

`ping` sends a tiny message to another computer and waits for a reply. It's like knocking on someone's door to see if they're home.

```bash
$ ping -c 4 google.com
PING google.com (142.250.80.46): 56 data bytes
64 bytes from 142.250.80.46: icmp_seq=0 ttl=118 time=11.4 ms
64 bytes from 142.250.80.46: icmp_seq=1 ttl=118 time=10.8 ms
64 bytes from 142.250.80.46: icmp_seq=2 ttl=118 time=11.2 ms
64 bytes from 142.250.80.46: icmp_seq=3 ttl=118 time=10.9 ms
```

- `-c 4` means "send 4 pings then stop." Without this, ping will run forever (on Linux/macOS) until you press **Ctrl+C**.
- `time=11.4 ms` means the round trip took 11.4 milliseconds. That's how fast light (well, electrical signals) can travel to Google's server and back.

> If you see `Request timeout`, the server either doesn't exist, is blocking pings, or there's a network issue.

### `curl` — "Give Me That Web Page"

`curl` fetches content from a URL. Think of it as a web browser in your terminal — but it shows you the raw text instead of rendering a pretty page.

```bash
$ curl -s example.com
```

You'll see raw HTML:

```html
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
...
```

The `-s` flag means "silent" — it hides the progress bar so you just see the content.

**Fetching just the headers** (metadata about the response):

```bash
$ curl -I example.com
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
...
```

`200 OK` means the server received your request and everything is fine. You'll learn more about HTTP status codes later, but the important ones are:

| Code | Meaning | Analogy |
|------|---------|---------|
| 200 | OK — here's what you asked for | "Order up! Here's your food." |
| 404 | Not found — that page doesn't exist | "Sorry, we don't have that dish on the menu." |
| 500 | Server error — something broke on their end | "The kitchen is on fire." |

### `nslookup` or `dig` — "Look Up the Address"

These commands manually ask DNS to translate a name to an IP address:

```bash
$ nslookup google.com
Server:    192.168.1.1
Address:   192.168.1.1#53

Non-authoritative answer:
Name:   google.com
Address: 142.250.80.46
```

This confirms that `google.com` translates to `142.250.80.46` (your result may differ — Google has many servers around the world).

---

## Did You Know?

> 1. **A common production issue: DNS caching.** Sometimes, even after a server migration is completed and DNS records are updated, your application keeps connecting to the old IP address because it cached the old DNS result. This has caused real, prolonged outages at major scale. For instance, a global e-commerce giant once suffered a 4-hour outage during a migration when their payment gateways aggressively cached outdated DNS records, costing an estimated $3.2 million in lost transactions because the application simply refused to look up the new address.
>
> 2. **NAT (Network Address Translation) and "It works on my machine".** Your local machine might have an IP like `192.168.1.42`, but the internet only sees your router's public IP. When you run a server on your laptop, it's bound to your local IP. This is why you can access it locally, but your friend across town gets a "connection refused" error — they cannot route traffic through the public internet directly to your private local IP without NAT rules on your router.
>
> 3. **DNS was invented because memorizing IP addresses was too hard.** Before DNS existed (1983), there was literally a single text file called `hosts.txt` that listed every computer on the internet and its address. Someone maintained it by hand. As the internet grew, this became impossible, so Paul Mockapetris invented DNS to automate the process.
>
> 4. **IP address exhaustion is real.** The original IP address system (IPv4) only has about 4.3 billion addresses. By the 2010s, we effectively ran out. To solve this, engineers created IPv6, which has so many addresses (340 undecillion) that we could assign one to every atom on the surface of the Earth and still have plenty left over. However, moving the entire internet to IPv6 is taking decades, which is why NAT (mentioned above) is so crucial today to share IPv4 addresses.

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| Forgetting `-c` with ping | Ping runs forever | Press **Ctrl+C** to stop it, or always use `ping -c 4` |
| Pinging a site that blocks ping | `Request timeout` — looks like it's down | The site might be fine — many servers block ping. Use `curl` instead |
| Confusing IP address and port | Connecting to the wrong thing | IP = which computer. Port = which service on that computer. `192.168.1.42:80` |
| Thinking your local IP is your public IP | Confusion when sharing with others | `192.168.x.x` is local only. Use `curl ifconfig.me` for your public IP |
| Forgetting `http://` with curl | Sometimes curl guesses wrong or errors | Be explicit: `curl http://example.com` or `curl https://example.com` |
| Thinking DNS failure means the site is down | Can't reach the site | The site might be fine but DNS can't resolve the name. Try using the IP directly |

---

## Quiz

**Question 1**: Your friend says their new laptop's address is `192.168.1.42` and asks you to connect to it from your house. You try, but it fails. Based on the type of address provided, why didn't this work?

<details>
<summary>Show Answer</summary>

The address `192.168.1.42` is a private, local IP address designated specifically for internal networks. It only identifies computers within the same local network (LAN) and is completely invisible to the outside internet. Since you are at your house and your friend is at theirs, you are on two entirely separate local networks. To connect over the internet, your computer would need to target their router's public IP address, and their router would need a rule to forward that traffic to their specific laptop.

</details>

**Question 2**: You are setting up a new web application. You can successfully run `ping 203.0.113.55` and receive replies, indicating the server is online. However, running `curl http://203.0.113.55` simply times out. What layer of the network is likely causing the problem?

<details>
<summary>Show Answer</summary>

The issue is occurring at the port or application layer, not the network routing layer. The successful `ping` command proves that the IP address is reachable, the server is powered on, and the network path is clear. However, `curl` specifically attempts to connect to a web service on port 80 (HTTP). The timeout indicates that either a firewall is blocking traffic specifically to port 80, or the web server software has crashed and isn't listening for connections on that port.

</details>

**Question 3**: A user reports they cannot access your company's API at `api.example.com`. You run `ping api.example.com` and it immediately says `cannot resolve api.example.com: Unknown host`. However, you know the server's public IP is `203.0.113.100`, and `curl http://203.0.113.100` returns a `200 OK`. Diagnose the exact point of failure.

<details>
<summary>Show Answer</summary>

The failure is isolated to the DNS resolution system, meaning the 'phone book' of the internet is failing to translate the name. Because the `curl` command works perfectly with the direct IP address and returns a `200 OK`, we can definitively prove the server is running, the network path is clear, and the application is healthy. The `Unknown host` error from `ping` shows that your computer cannot figure out which IP address belongs to `api.example.com`. To fix this, the DNS records for the domain need to be investigated and updated to point to `203.0.113.100`.

</details>

**Question 4**: A customer complains that your company's website is down. You run `curl -I https://example.com` and receive a `500 Internal Server Error` response. Is the problem with the customer's internet connection, DNS, or your company's server?

<details>
<summary>Show Answer</summary>

The problem is definitively with your company's server and application infrastructure. A 500-level HTTP status code is generated by the web server itself, which means the customer's internet connection works, DNS resolved correctly, and the network successfully delivered the request. The server received the request, but the application code encountered a fatal error (like a database connection failure or a syntax error) while trying to process it and build the webpage. You need to check the server's application logs to find the exact software bug causing the crash.

</details>

**Question 5**: A junior developer runs `ping -c 4 api.example.com` and it returns `Request timeout` for every packet. They immediately declare, "The API server is completely down and broken!" You run `curl -I https://api.example.com` on the same machine and receive `HTTP/1.1 200 OK`. Why was the junior developer's conclusion wrong, and what is actually happening?

<details>
<summary>Show Answer</summary>

The junior developer incorrectly assumed that a failed `ping` definitively means a server is offline or network-unreachable. In reality, `ping` uses a specific type of diagnostic network traffic (ICMP) that many modern servers and corporate firewalls intentionally drop for security reasons. Meanwhile, they allow normal web traffic (TCP) through on ports 80 and 443. The successful `curl` command proved that the web server is actively running, network routing is fine, and it is serving content successfully to legitimate web requests. The ping simply failed because the server's firewall is configured to ignore diagnostic knocks.

</details>

**Question 6**: You are helping a colleague troubleshoot an application that connects to a database. The database is supposed to be running on `10.0.5.50:5432`. The application logs show an error: `Connection refused to 10.0.5.50 on port 80`. Based on this log, what is the most likely cause of the failure?

<details>
<summary>Show Answer</summary>

The application is trying to connect to the database using the wrong port number. While the target IP address `10.0.5.50` is correct, the application is attempting to communicate over port 80, which is the default port for regular unencrypted web traffic. The database service is actually listening on port 5432, leaving port 80 completely unattended. Because there is no service listening on port 80 at that address, the operating system on the database server actively rejects the connection attempt, resulting in the 'Connection refused' error. The application's configuration file must be updated to explicitly specify port 5432.

</details>

**Question 7**: Your team just launched a new marketing site at `promo.company.com`. When you type this into your browser, it fails to load. You run `nslookup promo.company.com` and the command returns `server can't find promo.company.com: NXDOMAIN`. However, the lead engineer says the server is running perfectly at `198.51.100.22`. What specific system needs to be updated to fix this issue?

<details>
<summary>Show Answer</summary>

The Domain Name System (DNS) records for the company's domain need to be updated. The `NXDOMAIN` (Non-Existent Domain) error from the `nslookup` command proves that there is no public DNS record linking the human-readable name `promo.company.com` to any IP address. Even though the server is fully operational at `198.51.100.22`, browsers on the internet have no way to discover that routing information because the 'phone book' entry is missing. The infrastructure team must log into the DNS provider and create an 'A record' that points the new subdomain to the correct public IP address.

</details>

---

## Hands-On Exercise: Exploring the Network

### Objective

Use networking commands to explore connections, look up addresses, and fetch web content.

### Steps

1. **Verify network connectivity to a popular website:**
Use the terminal tool that sends small messages to a server to see if it responds. Send exactly 4 messages to `google.com` so the command doesn't run forever. Note the IP address it resolves to and the response times.

2. **Compare latency with another service:**
Run the exact same command from step 1, but target `cloudflare.com` instead. Are the response times faster or slower? The difference depends on how far their servers are from you.

3. **Find your local IP address:**
Use the appropriate command to find your local IP:

On macOS:
```bash
$ ipconfig getifaddr en0
```

On Linux:
```bash
$ hostname -I
```

Write down your local IP. It should start with `192.168.`, `10.`, or `172.`.

4. **Discover your public IP address:**
Use `curl` in silent mode (with the `-s` flag) to fetch the page at `ifconfig.me`. This will output the IP address the rest of the internet sees for you. Notice how it differs from your local IP.

5. **Manually resolve a domain name:**
Use the DNS lookup tool you learned about (like `nslookup`) to find the exact IP address for `github.com`. Locate the IP address in the resulting output.

6. **Fetch a web page:**

```bash
$ curl -s example.com
```

You should see the raw HTML of the example.com page.

7. **Examine server response headers:**
Instead of getting the full HTML, use `curl` to ask `example.com` just for its metadata headers (using the `-I` flag). Look for `HTTP/1.1 200 OK` in the output — that means success!

8. **Trigger a specific HTTP error code:**
Use `curl` to request only the headers for a path that you know doesn't exist on `example.com` (such as `example.com/this-page-does-not-exist`). Look for the `404` status in the response — that means "not found."

9. **Combine networking with file skills:**
Fetch the raw HTML of `example.com` silently again, but this time, redirect the output into a new file called `my-first-webpage.html` inside a `~/kubedojo-practice/` directory. Then, use a file reading command to output the contents of that new file to the screen to verify it worked.

### Success Criteria

You've completed this exercise when you can:

- [ ] Ping a website and see response times
- [ ] Find your local IP address
- [ ] Find your public IP address
- [ ] Look up a domain name with `nslookup`
- [ ] Fetch a web page with `curl`
- [ ] Identify a 200 (OK) and 404 (Not Found) response
- [ ] Save a web page to a file

---

> You just used a tool that senior engineers use every day. You belong here.

---

## What's Next?

You now understand how computers find and talk to each other. IP addresses, ports, DNS, and basic networking commands are in your toolkit.

**Next Module**: [Module 0.8: Servers and SSH](../module-0.8-servers-and-ssh/) — Learn what a server is, where they live, and how to connect to them remotely.