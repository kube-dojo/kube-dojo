---
title: "Module 0.7: Servers and SSH"
slug: prerequisites/zero-to-terminal/module-0.7-servers-and-ssh
sidebar:
  order: 8
lab:
  id: "prereq-0.7-servers-ssh"
  url: "https://killercoda.com/kubedojo/scenario/prereq-0.7-servers-ssh"
  duration: "25 min"
  difficulty: "beginner"
  environment: "ubuntu"
---
> **Complexity**: `[QUICK]` - Concepts and a hands-on connection
>
> **Time to Complete**: 25 minutes
>
> **Prerequisites**: [Module 0.5 - Editing Files](module-0.5-editing-files/)

---

## Why This Module Matters

Everything you've done so far has been on *your* computer. Your kitchen, your files, your terminal. But in the real world of technology, most of the action happens on computers that are *somewhere else* -- in a data center, in the cloud, in a rack of machines you'll never physically touch.

These other computers are called **servers**, and the way you talk to them is through **SSH**.

When you work with Kubernetes, you'll be managing servers (lots of them). Understanding what servers are and how to connect to them is not optional -- it's fundamental.

---

## What is a Server?

A server is just a computer. That's it. No magic, no mystery.

The word "server" describes what the computer *does*, not what it *is*. A server is a computer whose job is to **serve** things to other computers.

```
Your laptop:
  - Has a screen, keyboard, trackpad
  - Designed for ONE person to sit in front of
  - Runs a graphical interface (windows, icons, mouse)
  - You browse the web, write documents, watch videos

A server:
  - Often has NO screen, keyboard, or mouse
  - Designed to serve MANY users/computers simultaneously
  - Usually runs ONLY a terminal interface (no desktop)
  - It hosts websites, runs databases, processes data
```

### The Kitchen Analogy

Think of it this way:

- **Your laptop** is a home kitchen. You cook for yourself. You eat in the same room where you cook. The "chef" and the "customer" are the same person.

- **A server** is a restaurant kitchen. It exists to prepare food and send it *out* to a dining room full of customers. The kitchen has no dining tables -- that's not its job. Its job is to cook and serve.

When you visit a website, your browser (the customer in the dining room) sends a request to a server (the kitchen in the back). The server prepares the response (cooks the meal) and sends it back to your browser (serves the dish).

---

## Your Laptop vs. a Server

Under the hood, they have the same basic parts:

| Component | Your Laptop | A Typical Server |
|-----------|-------------|-----------------|
| CPU | 4-8 cores | 16-128 cores |
| RAM | 8-32 GB | 64-512 GB |
| Storage | 256 GB - 2 TB | 1 TB - 100 TB+ |
| Screen | Yes | Usually no |
| Keyboard | Yes | Usually no |
| Operating System | macOS/Windows | Linux (almost always) |
| Purpose | One person, many tasks | Many clients, specific tasks |

A server is basically a beefy computer optimized for serving many requests at once, running 24/7, and being managed remotely.

---

## Local vs. Remote

Two words you'll hear constantly:

- **Local** = your computer, right here, in front of you
- **Remote** = a different computer, somewhere else, that you connect to over a network

```
Local:  Your kitchen. You're standing in it.
Remote: A kitchen in another city. You call them on the phone to give orders.
```

When you type `ls` in your terminal right now, that command runs **locally** -- on your computer.

When you connect to a server and type `ls`, that command runs **remotely** -- on the server. But it looks exactly the same in your terminal. That's the beauty of it.

---

## SSH: Your Secure Tunnel to Remote Kitchens

**SSH** stands for **S**ecure **Sh**ell. It's a program that lets you open a terminal session on a remote computer, securely.

Think of SSH as a **secure phone line to a remote kitchen**. You pick up the phone (open SSH), dial the number (connect to the server), and start giving orders (typing commands). The chef in the remote kitchen carries them out, and you hear the results through the phone.

The "secure" part is important: everything you send over SSH is encrypted. Nobody can listen in on your conversation. It's like having a private, scrambled phone line.

### A Quick Word About Environment Variables

You'll sometimes see things like `$USER` or `$HOME` in commands or documentation. These are **environment variables** -- named boxes that your system fills with useful values automatically.

- `$USER` holds your username
- `$HOME` holds the path to your home directory

Try them out:

```bash
echo $USER
echo $HOME
```

You don't need to set these -- your computer does it for you when you log in. We mention this now because SSH commands often use `$USER`, and you'll see environment variables throughout your career.

### The SSH Command

The basic SSH command looks like this:

```bash
ssh username@ip-address
```

Let's break that down:

- `ssh` -- the program you're running
- `username` -- your account name on the remote server (like your name badge at the remote kitchen)
- `@` -- just a separator (the "at" sign)
- `ip-address` -- the address of the remote server (like the phone number of the kitchen)

A real example might look like:

```bash
ssh chef@192.168.1.100
```

Or with a domain name instead of an IP address:

```bash
ssh chef@kitchen.example.com
```

### What Happens When You Connect

```
1. You type: ssh chef@kitchen.example.com
2. SSH contacts the remote server
3. The server asks: "Who are you? Prove it."
4. You provide proof (password or key -- more on this below)
5. The server says: "Welcome, chef. Here's your terminal."
6. Your prompt changes to show the remote server's name
7. Every command you type now runs on the REMOTE server
8. Type "exit" to disconnect and return to your local terminal
```

Your terminal prompt might change from:

```
yourname@your-laptop ~ $
```

to:

```
chef@remote-server ~ $
```

That's how you know you're connected to a different machine.

---

## Passwords vs. SSH Keys

There are two ways to prove your identity to a remote server:

### Passwords

The simple way. The server asks for a password, you type it.

```bash
ssh chef@kitchen.example.com
# Server asks: chef@kitchen.example.com's password:
# You type your password (it won't show on screen -- that's normal)
```

Passwords work, but they have problems:
- You have to type them every time
- They can be guessed or stolen
- They're annoying for automated systems

### SSH Keys (The Better Way)

SSH keys work like a lock-and-key system:

```
You have a KEY (private key) -- kept on your computer, never shared.
The server has a LOCK (public key) -- it knows what key fits.

When you connect:
1. You present your key
2. The server checks: "Does this key fit my lock?"
3. If yes: "Come in!" (no password needed)
4. If no: "Access denied."
```

This is like having a physical key to the remote kitchen's door. You don't need to tell anyone a password -- you just unlock the door.

**Generating SSH keys** (you don't need to do this right now, just know how):

```bash
ssh-keygen -t ed25519
```

This creates two files:
- `~/.ssh/id_ed25519` -- Your **private key** (the key). NEVER share this with anyone.
- `~/.ssh/id_ed25519.pub` -- Your **public key** (the lock). You can share this freely.

You copy the public key to the server, and from then on, you can connect without a password.

> **Think of it this way**: The private key is your house key. The public key is a copy of the lock on your door. You can give the lock to anyone and say "put this on your door." Now your key opens their door too. But nobody can make a key from looking at the lock.

---

## Common SSH Options

| Option | What It Does | Example |
|--------|-------------|---------|
| `-p` | Connect on a different port (default is 22) | `ssh -p 2222 chef@server.com` |
| `-i` | Use a specific key file | `ssh -i ~/.ssh/mykey chef@server.com` |
| `-v` | Verbose mode (shows what's happening -- useful for debugging) | `ssh -v chef@server.com` |

---

## The Lifecycle of a Connection

```
Your computer                          Remote server
    |                                       |
    |  --- ssh chef@server.com ---------->  |
    |                                       |  "Connection request received"
    |  <--- "Prove your identity" --------  |
    |                                       |
    |  --- sends key/password ----------->  |
    |                                       |  "Identity confirmed"
    |  <--- "Welcome! Here's a shell" ----  |
    |                                       |
    |  --- ls, pwd, nano, etc. --------->  |  (commands run HERE, on the server)
    |  <--- results sent back -----------  |
    |                                       |
    |  --- exit ------------------------->  |
    |                                       |  "Goodbye"
    |  (back to local terminal)             |
```

**Key insight**: When you're connected via SSH, your terminal *looks* the same, but every command runs on the remote machine. If you create a file, it's created on the server, not your laptop. If you run `pwd`, it shows the server's directory, not yours.

---

## Why This Matters for Kubernetes

Kubernetes runs on servers -- usually many of them. A typical Kubernetes cluster might have:

- 3 servers for the "control plane" (the restaurant management office)
- 10-100+ servers as "worker nodes" (the kitchens that do the actual cooking)

You'll use SSH to connect to these servers, troubleshoot problems, check logs, and manage configurations. The commands you learned in previous modules -- `ls`, `cd`, `nano`, `cat` -- work exactly the same on these remote servers.

---

## Did You Know?

- **SSH was invented in 1995 by a Finnish researcher** named Tatu Ylonen, after a password-sniffing attack hit his university network. Before SSH, people used `telnet` to connect to remote computers, which sent everything (including passwords) in plain text that anyone on the network could read. SSH encrypted the connection, making it secure. It was such a good idea that it became a global standard almost overnight.

- **Port 22 was assigned personally.** When Tatu Ylonen created SSH, he needed a port number. He emailed the organization that manages port numbers (IANA), and they simply assigned him port 22. He got it within a day. Today, port 22 is one of the most recognized port numbers in computing.

- **The International Space Station uses SSH.** Astronauts and ground control use SSH to securely manage the station's computer systems. The same tool you're learning about in this module is used to manage computers in orbit around Earth.

---

## Common Mistakes

| Mistake | Why It's a Problem | What to Do Instead |
|---------|-------------------|-------------------|
| Sharing your private key | Anyone with your private key can access your servers | Never share `id_ed25519` (the file WITHOUT `.pub`). Only share the `.pub` file |
| Forgetting you're on a remote server | You might delete files or change things on the wrong machine | Always check your prompt and use `hostname` to verify which machine you're on |
| Typing your password in the wrong field | SSH hides password input (no dots, no asterisks). People think it's broken and type it somewhere visible | When SSH asks for a password, just type it blind and press Enter. It IS receiving your keystrokes |
| Not disconnecting when done | Leaving SSH sessions open wastes server resources and can be a security risk | Type `exit` or press `Ctrl + D` when you're done |
| Panicking when the connection drops | Network interruptions happen -- it doesn't mean something is broken | Just reconnect with the same SSH command. Your files on the server are still there |

---

## Quiz

1. **What is the difference between your laptop and a server?**
   <details>
   <summary>Answer</summary>
   Physically, they're very similar -- both have CPUs, RAM, and storage. The difference is their purpose. Your laptop is designed for one person to use with a screen and keyboard. A server is designed to serve many clients simultaneously, often has no screen or keyboard, and typically runs Linux with only a terminal interface. A server is usually more powerful (more CPU cores, more RAM) because it handles many requests at once.
   </details>

2. **What does SSH stand for, and what does it do?**
   <details>
   <summary>Answer</summary>
   SSH stands for Secure Shell. It lets you open a terminal session on a remote computer over an encrypted connection. You type commands on your local machine, they execute on the remote machine, and the results are sent back to you. The "secure" part means all communication is encrypted so nobody can eavesdrop.
   </details>

3. **What is the difference between a private key and a public key?**
   <details>
   <summary>Answer</summary>
   The private key stays on your computer and must never be shared -- it's like your house key. The public key can be shared freely and is placed on servers you want to access -- it's like the lock. When you connect, the server checks if your private key matches its stored public key. If it matches, you're in. Knowing the public key doesn't help anyone impersonate you -- you need the private key for that.
   </details>

4. **When you're connected to a remote server via SSH and you type `touch recipe.txt`, where is the file created?**
   <details>
   <summary>Answer</summary>
   On the remote server, not on your local machine. When you're connected via SSH, every command you type runs on the remote server. The file `recipe.txt` is created on the server's file system. Your local machine doesn't get a copy. To verify which machine you're on, check the terminal prompt or type `hostname`.
   </details>

---

## Hands-On Exercise: SSH to Localhost

We'll practice SSH by connecting to your own computer. This might sound pointless ("I'm already here!"), but it demonstrates exactly how SSH works -- and the experience is identical to connecting to a real remote server.

### On macOS:

First, enable Remote Login (SSH) if it's not already enabled:

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **General > Sharing**
3. Turn on **Remote Login**

Now, in your terminal:

```bash
ssh localhost
```

You'll see something like:

```
The authenticity of host 'localhost (127.0.0.1)' can't be established.
ED25519 key fingerprint is SHA256:AbCdEf123456...
Are you sure you want to continue connecting (yes/no)?
```

Type `yes` and press Enter. (This only appears the first time you connect to a new server. The computer is saying "I've never talked to this server before -- are you sure it's legit?")

Enter your Mac password when prompted.

Now you're "connected." Try:

```bash
hostname
pwd
ls
echo "Hello from SSH!"
```

Everything looks the same because you're SSH-ing to yourself. But the mechanism is identical to connecting to a server across the world.

To disconnect:

```bash
exit
```

### On Linux:

Most Linux systems have SSH enabled by default. If not:

```bash
sudo apt install openssh-server    # Debian/Ubuntu
sudo systemctl start sshd          # Start the SSH service
```

Then:

```bash
ssh localhost
```

Follow the same steps as macOS above.

### On Windows:

SSH to localhost is trickier on Windows. Instead, just practice the command syntax:

```
# This is what connecting to a real server would look like:
ssh yourname@192.168.1.100

# You would see:
yourname@192.168.1.100's password:

# After entering the password:
yourname@remote-server:~$

# Now every command runs on the remote server.
# Type "exit" to disconnect.
```

### What Would Happen With a Real Server

If you had a cloud server (you'll get one when you start the Kubernetes track), the experience would be:

```bash
# Connect to a server in the cloud
ssh ubuntu@54.123.45.67

# You'd see:
ubuntu@ip-54-123-45-67:~$

# Now you're inside a Linux server in a data center somewhere
# Every command runs there:
ls          # Shows files on the server
pwd         # Shows your path on the server
nano        # Opens nano on the server
cat /etc/os-release    # Shows the server's operating system

# Disconnect when done
exit
```

It would look, feel, and work exactly like the localhost exercise. The only difference is the physical location of the computer.

**Success criteria**: You successfully (or conceptually understand how to) open an SSH connection, verify you're connected to a different machine (or the same machine via SSH), run commands, and disconnect. You understand that SSH gives you a remote terminal and that commands execute on the server, not your laptop.

---

## What's Next?

In [Module 0.9: What is the Cloud?](module-0.9-what-is-the-cloud/), you'll learn what happens when you take thousands of servers, put them in massive buildings, and let anyone rent them by the hour. That's cloud computing, and it's where Kubernetes lives.

---

> **You just used a tool that senior engineers use every day. You belong here.**
