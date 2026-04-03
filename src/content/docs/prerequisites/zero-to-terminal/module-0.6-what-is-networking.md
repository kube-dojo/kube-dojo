---
title: "Module 0.6: What is Networking?"
slug: prerequisites/zero-to-terminal/module-0.6-what-is-networking
sidebar:
  order: 7
---
> **Complexity**: `[QUICK]` - Absolute beginner
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 0.4: Files and Directories](../module-0.4-files-and-directories/) — You should be comfortable running commands and navigating directories.

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

> 1. **The internet relies on physical cables under the ocean.** Over 550 submarine cables span the ocean floor, carrying 99% of intercontinental data. When you visit a website hosted in another continent, your request literally travels through a cable on the seabed. These cables are about the thickness of a garden hose and stretch for thousands of miles.
>
> 2. **The port number 80 for HTTP was chosen somewhat arbitrarily.** Tim Berners-Lee, the inventor of the World Wide Web, picked port 80 in 1991 simply because it wasn't already claimed by another service. Port 443 for HTTPS came later when encryption was added.
>
> 3. **DNS was invented because memorizing IP addresses was too hard.** Before DNS existed (1983), there was literally a single text file called `hosts.txt` that listed every computer on the internet and its address. Someone maintained it by hand. As the internet grew, this became impossible, so Paul Mockapetris invented DNS to automate the process.

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

**Question 1**: What is an IP address?

<details>
<summary>Show Answer</summary>

A unique number that identifies a computer on a network, like a street address identifies a building. Example: `192.168.1.42`

</details>

**Question 2**: If an IP address is a street address, what is a port?

<details>
<summary>Show Answer</summary>

A port is the **apartment number** (or door number). It identifies a specific service or program on that computer. For example, port 80 is for web traffic, port 22 is for SSH.

</details>

**Question 3**: What does DNS do?

<details>
<summary>Show Answer</summary>

DNS translates human-readable domain names (like `google.com`) into IP addresses (like `142.250.80.46`) that computers can use to find each other. It's the phone book of the internet.

</details>

**Question 4**: What command would you use to check if a server is reachable?

<details>
<summary>Show Answer</summary>

```bash
$ ping -c 4 servername.com
```

`ping` sends a small message and waits for a reply. If you get replies, the server is reachable. Use `-c 4` to limit it to 4 attempts.

</details>

**Question 5**: You see `curl: (6) Could not resolve host: fakename.xyz`. What does this mean?

<details>
<summary>Show Answer</summary>

DNS could not translate `fakename.xyz` into an IP address. This means either the domain name doesn't exist, is misspelled, or there's a DNS issue on your network.

</details>

---

## Hands-On Exercise: Exploring the Network

### Objective

Use networking commands to explore connections, look up addresses, and fetch web content.

### Steps

1. **Ping a website:**

```bash
$ ping -c 4 google.com
```

Note the IP address it resolves to and the response times.

2. **Ping another website and compare:**

```bash
$ ping -c 4 cloudflare.com
```

Are the response times faster or slower? The difference depends on how far their servers are from you.

3. **Find your local IP address:**

On macOS:
```bash
$ ipconfig getifaddr en0
```

On Linux:
```bash
$ hostname -I
```

Write down your local IP. It should start with `192.168.`, `10.`, or `172.`.

4. **Find your public IP address:**

```bash
$ curl -s ifconfig.me
```

This is the IP address the rest of the internet sees for you. It'll be different from your local IP.

5. **Look up a domain name:**

```bash
$ nslookup github.com
```

Find the IP address for `github.com` in the output.

6. **Fetch a web page:**

```bash
$ curl -s example.com
```

You should see the raw HTML of the example.com page.

7. **Check the response headers:**

```bash
$ curl -I example.com
```

Look for `HTTP/1.1 200 OK` — that means success!

8. **Try a page that doesn't exist:**

```bash
$ curl -I example.com/this-page-does-not-exist
```

Look for `404` in the response — that means "not found."

9. **Save a web page to a file** (combining networking with file skills!):

```bash
$ curl -s example.com > ~/kubedojo-practice/my-first-webpage.html
$ cat ~/kubedojo-practice/my-first-webpage.html
```

You just downloaded a web page and saved it as a file!

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

> 💡 You just used a tool that senior engineers use every day. You belong here.

---

## What's Next?

You now understand how computers find and talk to each other. IP addresses, ports, DNS, and basic networking commands are in your toolkit.

**Next Module**: [Module 0.7: Servers and SSH](../module-0.7-servers-and-ssh/) — Learn what a server is, where they live, and how to connect to them remotely.
