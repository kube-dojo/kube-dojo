---
title: "Module 0.10: Your First Server -- Putting It All Together"
slug: prerequisites/zero-to-terminal/module-0.10-your-first-server
sidebar:
  order: 11
---
> **Complexity**: `[MEDIUM]` - Capstone project
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: [Module 0.1](module-0.1-what-is-a-computer/) through [Module 0.9](module-0.9-what-is-the-cloud/) -- all of them

---

## Why This Module Matters

This is the final exam. The capstone. The moment where everything clicks.

You're going to **deploy a website that anyone can visit. Using nothing but your terminal.**

No fancy drag-and-drop website builders. No WordPress. No Squarespace. Just you, a terminal, and the skills you've been building since Module 0.1.

Think about where you started. In Module 0.1, you learned what a computer even *is*. Now you're about to use one to put something on the internet. That's not a small thing. That is exactly what professionals do every day -- and you're about to do it too.

This module has **two options**:

- **Option A: Local (free, no signup required)** -- Run a web server on your own machine using Docker
- **Option B: Cloud (free tier, requires signup)** -- Deploy to a real cloud server that the entire internet can reach

Option A is faster and simpler. Option B is closer to what happens in the real world. Both are valid. Pick the one that excites you, or do both.

---

## The Skills You've Built

Before we start, let's take stock. Every single module you've completed plays a role here:

| Module | Skill | How You'll Use It |
|--------|-------|-------------------|
| 0.1 | How computers work | Understanding what the server is actually doing |
| 0.2 | The terminal | Your only interface for this entire project |
| 0.3 | Commands | Navigating, creating files, checking status |
| 0.4 | Files and directories | Creating your website's HTML file |
| 0.5 | Editing files | Writing your web page with nano |
| 0.6 | Networking | Understanding ports, IPs, and how browsers find servers |
| 0.7 | Servers and SSH | Knowing what a server is (and connecting to one in Option B) |
| 0.8 | Packages | Installing software on a server |
| 0.9 | The cloud | Understanding where your server lives (Option B) |

If you skipped any of those modules, go back and do them first. This capstone assumes you have all nine skills ready.

---

## What is a Web Server?

Before we deploy anything, let's make sure we're clear on one concept.

A **web server** is a program that listens for requests and sends back web pages. That's it. When you type `google.com` in your browser, your browser sends a request to Google's web server, and the server sends back the HTML that your browser displays.

The most popular web server in the world is called **nginx** (pronounced "engine-X"). It powers about a third of all websites on the internet. We're going to use it today.

In our restaurant kitchen analogy: nginx is the **waiter**. It takes orders (HTTP requests from browsers) and delivers food (HTML pages) back to the customer.

---

## Option A: Local Server with Docker (Free, No Signup)

This option uses **Docker** -- a tool that runs applications in isolated "containers." You don't need to understand Docker deeply right now (that's what Cloud Native 101 is for). For now, just think of it as a way to run a program without installing it permanently on your machine.

### Step 1: Install a Container Runtime

You need a tool to run containers. Pick **any one** of these — they all work the same way for our exercise:

| Tool | Best for | License |
|------|----------|---------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Most popular, biggest community | Free for personal/small business |
| [OrbStack](https://orbstack.dev/) | macOS — fastest, lightest, best UX | Free for personal use |
| [Podman Desktop](https://podman-desktop.io/) | No daemon, rootless by default | Free and open source |
| [Rancher Desktop](https://rancherdesktop.io/) | Includes K8s built-in | Free and open source |

- **macOS/Windows**: Download and install any of the above
- **Linux**:
  ```bash
  # Option A: Docker
  sudo apt update && sudo apt install docker.io -y
  sudo systemctl start docker
  sudo usermod -aG docker $USER

  # Option B: Podman (no daemon, no root needed)
  sudo apt update && sudo apt install podman -y
  ```
  (If using Docker, log out and back in after the usermod command.)

> **Note**: If you install Podman, the commands are identical — just type `podman` instead of `docker`. You can even alias it: `alias docker=podman`

Verify Docker is working:

```bash
docker --version
```

You should see something like `Docker version 24.x.x` or newer. If you get "command not found," Docker isn't installed yet.

### Step 2: Run nginx

Here it is. One command to start a web server:

```bash
docker run -d -p 8080:80 --name my-website nginx
```

Let's break down every piece of that command (because understanding matters more than memorizing):

| Part | What It Does |
|------|-------------|
| `docker run` | Start a new container |
| `-d` | Run in the background (detached) so you get your terminal back |
| `-p 8080:80` | Connect your computer's port 8080 to the container's port 80 |
| `--name my-website` | Give the container a friendly name |
| `nginx` | Use the nginx image (Docker downloads it automatically) |

Remember Module 0.6 on networking? Port 80 is the standard port for web traffic. We're mapping it to 8080 on your machine so it doesn't conflict with anything else.

### Step 3: See it working

Open your web browser and go to:

```
http://localhost:8080
```

You should see a page that says **"Welcome to nginx!"**

That's a web server running on your machine. You just did that. With one command.

### Step 4: Create your own web page

Now let's replace that default page with something you made. Open your terminal and create an HTML file:

```bash
nano ~/index.html
```

Type (or paste) this:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My First Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 80px auto;
            text-align: center;
            background-color: #1a1a2e;
            color: #eee;
        }
        h1 { color: #00d4ff; }
        p { font-size: 1.2em; line-height: 1.6; }
        .badge {
            display: inline-block;
            background: #00d4ff;
            color: #1a1a2e;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Hello, Internet!</h1>
    <p>This page is running on a server that I set up myself,
       using nothing but the terminal.</p>
    <p>I went from "what is a computer" to "I deployed a website"
       in ten modules.</p>
    <div class="badge">Zero to Terminal: Complete</div>
</body>
</html>
```

Save and exit (`Ctrl + O`, Enter, `Ctrl + X`).

### Step 5: Copy your page into the server

Remember, the web server is running inside a Docker container. You need to copy your file into it:

```bash
docker cp ~/index.html my-website:/usr/share/nginx/html/index.html
```

That command says: "Copy `index.html` from my home directory into the container named `my-website`, placing it at `/usr/share/nginx/html/index.html`."

The path `/usr/share/nginx/html/` is where nginx looks for web pages to serve. This is just a directory -- exactly like the directories you worked with in Module 0.4.

### Step 6: See YOUR page

Go back to your browser and refresh `http://localhost:8080`.

You should see your custom page -- dark background, blue heading, your words.

**You just deployed a website.**

You created a file (Module 0.4), edited it with nano (Module 0.5), understood what port and localhost mean (Module 0.6), and served it from a running server process (Module 0.7). Everything connected.

### Cleaning up

When you're done admiring your work:

```bash
docker stop my-website
docker rm my-website
```

This stops and removes the container. Your `~/index.html` file is still on your machine.

---

## Option B: Cloud Server (Free Tier)

This option puts your website on a **real server on the internet** with a public IP address. Anyone in the world can visit it. This is exactly how real websites work.

You'll need a free-tier account with a cloud provider. The instructions below use a generic approach that works with AWS, GCP, or Oracle Cloud.

### Step 1: Get a free cloud VM

Sign up for a free tier at one of these providers:

- **Oracle Cloud** (most generous free tier -- always-free VMs): [cloud.oracle.com/free](https://cloud.oracle.com/free)
- **Google Cloud** ($300 free credit for 90 days): [cloud.google.com/free](https://cloud.google.com/free)
- **AWS** (750 hours/month of t2.micro for 12 months): [aws.amazon.com/free](https://aws.amazon.com/free)

Create the smallest available Linux VM (Ubuntu is easiest for beginners). During setup:

1. Choose **Ubuntu** as the operating system
2. Pick the **smallest free instance** (e.g., t2.micro on AWS, e2-micro on GCP)
3. **Download the SSH key** when prompted -- you'll need this to connect
4. Make sure the security group / firewall allows **port 22 (SSH)** and **port 80 (HTTP)**

Write down the **public IP address** of your new server. It will look something like `34.123.45.67`.

### Step 2: Connect via SSH

Remember Module 0.7? This is where SSH becomes real:

```bash
chmod 400 ~/Downloads/my-key.pem
ssh -i ~/Downloads/my-key.pem ubuntu@YOUR_PUBLIC_IP
```

Replace `YOUR_PUBLIC_IP` with the actual IP address of your VM. Replace the key path with wherever you saved yours.

If everything is configured correctly, you'll see a Linux welcome message and a command prompt. You're now inside a computer in a data center somewhere -- possibly on another continent.

### Step 3: Install nginx

Now use the package management skills from Module 0.8:

```bash
sudo apt update
sudo apt install nginx -y
```

That's it. nginx is installed and running. On Ubuntu, it starts automatically after installation.

Verify it's running:

```bash
sudo systemctl status nginx
```

You should see `active (running)` in green.

### Step 4: Test the default page

Open your browser on your own computer and visit:

```
http://YOUR_PUBLIC_IP
```

You should see the nginx default page. That page is being served from a machine in a data center, across the internet, to your browser. Take a moment to appreciate that.

### Step 5: Create your custom page

Still connected via SSH, edit the default web page:

```bash
sudo nano /var/www/html/index.html
```

> **Note**: The path is `/var/www/html/` on Ubuntu's nginx, not `/var/share/`. Different systems put web files in slightly different places.

Delete everything in the file (`Ctrl + K` repeatedly) and type your own HTML:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My First Cloud Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 80px auto;
            text-align: center;
            background-color: #1a1a2e;
            color: #eee;
        }
        h1 { color: #00d4ff; }
        p { font-size: 1.2em; line-height: 1.6; }
        .badge {
            display: inline-block;
            background: #00d4ff;
            color: #1a1a2e;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Hello, Internet!</h1>
    <p>This page is running on a real cloud server that I set up myself,
       using nothing but SSH and the terminal.</p>
    <p>I went from "what is a computer" to "I deployed a website
       on the internet" in ten modules.</p>
    <div class="badge">Zero to Terminal: Complete</div>
</body>
</html>
```

Save and exit (`Ctrl + O`, Enter, `Ctrl + X`).

### Step 6: See your page live on the internet

Refresh `http://YOUR_PUBLIC_IP` in your browser.

Your custom page is now **live on the internet**. You can send that IP address to a friend, and they'll see your page too. From their phone, from another country -- anywhere.

You did that with SSH (Module 0.7), package management (Module 0.8), file editing (Module 0.5), and an understanding of networking (Module 0.6) and cloud computing (Module 0.9).

### Important: Free tier warning

Cloud VMs can cost money if you exceed free-tier limits. When you're done with this exercise:

- **Stop or terminate your VM** through the cloud provider's console
- Or leave it running if your free tier allows it (Oracle's always-free tier, for example)
- **Never leave a cloud resource running that you've forgotten about** -- this is one of the most common (and expensive) beginner mistakes

To disconnect from SSH:

```bash
exit
```

---

## Did You Know?

- **The first website ever made is still online.** Tim Berners-Lee created it in 1991 at CERN. It was served from a NeXT computer with a handwritten note taped to it: "This machine is a server. DO NOT POWER IT DOWN!!" You can still visit it at [info.cern.ch](http://info.cern.ch). Your server setup today was more sophisticated than the one that launched the World Wide Web.

- **nginx was created to solve a bet.** In 2002, Igor Sysoev set out to solve the "C10K problem" -- handling 10,000 simultaneous connections on a single server. At the time, Apache (the dominant web server) struggled with this. Sysoev spent two years writing nginx, and it didn't just solve C10K -- modern nginx can handle over a million concurrent connections. It now serves roughly 34% of all websites on the internet.

- **Your website is served the same way Netflix is.** Seriously. Netflix, Airbnb, and Dropbox all use nginx as their web server. The difference between your setup and theirs is scale (they have thousands of servers) and configuration (they have teams of engineers tweaking settings). But the fundamental technology -- a process listening on port 80 and returning HTML -- is identical.

---

## Common Mistakes

| Mistake | Why It's a Problem | What to Do Instead |
|---------|-------------------|-------------------|
| Forgetting to open port 80 in cloud firewall | Your server is running but nobody can reach it | Check security groups / firewall rules; allow inbound HTTP on port 80 |
| Using `http://localhost` for the cloud option | `localhost` means *your* machine, not the remote server | Use the public IP address of your cloud VM |
| Editing the wrong `index.html` path | nginx won't serve your file if it's in the wrong directory | Ubuntu uses `/var/www/html/`, Docker uses `/usr/share/nginx/html/` |
| Forgetting `sudo` when editing files on the server | Web server files are owned by root; you'll get "Permission denied" | Use `sudo nano /var/www/html/index.html` |
| Leaving a cloud VM running after the exercise | Free tiers have limits; you might get charged | Stop or terminate the VM when you're done experimenting |
| Not downloading the SSH key during VM creation | You can't connect to your server without it | Always save the key file immediately; some providers only let you download it once |

---

## Quiz

1. **What does nginx do?**
   <details>
   <summary>Answer</summary>
   nginx is a web server. It listens for HTTP requests (from browsers) on a port (usually port 80) and responds with web pages (HTML files). It's the "waiter" that takes orders and delivers food in our restaurant analogy.
   </details>

2. **In the Docker command `docker run -d -p 8080:80 nginx`, what does `-p 8080:80` mean?**
   <details>
   <summary>Answer</summary>
   It maps port 8080 on your local machine to port 80 inside the Docker container. When you visit `localhost:8080` in your browser, the request gets forwarded to port 80 inside the container where nginx is listening. This is called port mapping or port forwarding.
   </details>

3. **Why is the path for web files different in Option A and Option B?**
   <details>
   <summary>Answer</summary>
   Different nginx installations and operating systems use different default directories. The official nginx Docker image serves files from `/usr/share/nginx/html/`, while Ubuntu's nginx package serves files from `/var/www/html/`. Both are just directories on a filesystem -- the nginx configuration file tells nginx where to look. This is a good reminder that paths are configurable, not magical.
   </details>

4. **Name at least five skills from earlier modules that you used in this capstone.**
   <details>
   <summary>Answer</summary>
   Any five of these: (1) understanding computer hardware and what a process is (Module 0.1), (2) using the terminal as your interface (Module 0.2), (3) running commands like `ls`, `cd`, and `cat` (Module 0.3), (4) understanding file paths and directories (Module 0.4), (5) editing files with nano (Module 0.5), (6) understanding ports, IP addresses, and localhost (Module 0.6), (7) knowing what a server is and using SSH (Module 0.7), (8) installing software with a package manager (Module 0.8), (9) understanding cloud VMs and free tiers (Module 0.9).
   </details>

---

## Hands-On Exercise: Make It Yours

You've deployed the template page. Now make it **truly yours**.

### The challenge

Customize your web page to include:

1. **Your name** (or a pseudonym -- this is the internet after all)
2. **Three things you learned** in this track that surprised you
3. **A link** to any website you like (use an `<a href="...">` tag)

Here's a hint for the link syntax:

```html
<a href="https://kubedojo.dev" style="color: #00d4ff;">KubeDojo</a>
```

### Success criteria

- Your custom page loads in a browser (either `localhost:8080` or a public IP)
- It contains your name, three things you learned, and at least one link
- You edited it using nano (not by pasting into a GUI text editor)
- You can explain to someone what nginx is doing and why the page appears

If you completed this, you've validated every skill in the Zero to Terminal track.

---

## What's Next? -- Choose Your Path

You've finished **Zero to Terminal**. You went from "what is a computer" to "I deployed a website" in ten modules. That is a real accomplishment.

Now you have a choice. The road forks into three paths, and all of them are valid.

### Path A: Linux Deep Dive

**You loved the terminal? Go deeper.**

The Linux track takes you inside the operating system itself -- the kernel, process management, filesystem internals, networking under the hood, permissions, and security. This is the knowledge that separates someone who *uses* Linux from someone who truly *understands* it.

If you want to become a systems engineer, SRE, or anyone who manages infrastructure, this path makes you dangerous (in the best way).

> Start here: [Linux Fundamentals](../../linux/)

### Path B: Cloud Native

**You want to build and deploy apps at scale? This is where the industry is heading.**

The Cloud Native track picks up right where you left off. You'll learn about containers (the technology behind that Docker command you just ran), then Docker in depth, then Kubernetes -- the system that manages thousands of containers across hundreds of servers automatically.

If you want to become a cloud engineer, DevOps engineer, or platform engineer, this is your path.

> Start here: [Cloud Native 101](../cloud-native-101/module-1.1-what-are-containers/)

### Path C: Both

**Most senior engineers know both.** They understand Linux internals *and* cloud-native tooling. Start with whichever excites you more. The other path will still be here when you're ready.

```
                    YOU ARE HERE
                         |
                    Module 0.10
                    (Capstone)
                         |
              +----------+----------+
              |                     |
         Path A                Path B
     Linux Deep Dive        Cloud Native 101
              |                     |
     Kernel, processes       Containers, Docker
     Networking internals    Kubernetes basics
     Security, hardening     CKA certification
              |                     |
              +----------+----------+
                         |
                  Platform Engineering
                  (SRE, GitOps, DevSecOps)
```

Both paths converge at Platform Engineering. Both are valuable. Neither is "better." Pick the one that makes you want to open a terminal right now.

---

## Final Words

You just deployed a website to the internet using nothing but text commands.

Ten modules ago you didn't know what a terminal was.

You learned what a computer is made of. You opened a terminal for the first time. You navigated a filesystem, created files, edited them. You learned how networks carry data across the planet. You connected to a remote server. You installed software. You understood what "the cloud" actually means.

And then you put it all together and shipped something real.

That's not beginner stuff. That's engineering.

**You belong here.**

---

> *"The expert in anything was once a beginner."* -- Helen Hayes
