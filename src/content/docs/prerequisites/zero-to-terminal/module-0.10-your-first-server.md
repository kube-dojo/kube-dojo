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
> **Prerequisites**: [Module 0.1](../module-0.1-what-is-a-computer/) through [Module 0.9](../module-0.9-what-is-the-cloud/) -- all of them

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Deploy** a simple web server from the terminal and understand what it does under the hood
- **Trace** an HTTP request from browser to server and back, explaining each step
- **Test** a running server using `curl` from the command line
- **Connect** the concepts from all previous modules: files, networking, ports, SSH — it all comes together here

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

> **Stop and think**: You're mapping port 8080 to port 80. If another program on your computer is already using port 8080 (like another web server or a local development tool), what do you expect this Docker command to do? Will it override the existing program, or will it fail?

Let's break down every piece of that command (because understanding matters more than memorizing):

| Part | What It Does |
|------|-------------|
| `docker run` | Start a new container |
| `-d` | Run in the background (detached) so you get your terminal back |
| `-p 8080:80` | Connect your computer's port 8080 to the container's port 80 |
| `--name my-website` | Give the container a friendly name |
| `nginx` | Use the nginx image (Docker downloads it automatically) |

Remember Module 0.6 on networking? Port 80 is the standard port for web traffic. We're mapping it to 8080 on your machine so it doesn't conflict with anything else.

> **Connect the dots**: The `-p 8080:80` flag is Module 0.6 (ports) in action. Your browser sends a request to port 8080 on your machine. Docker forwards it to port 80 inside the container, where nginx is listening. The response travels back the same path. Every concept from these modules is working together right now.

### Step 3: See it working

Open your web browser and go to:

```
http://localhost:8080
```

You should see a page that says **"Welcome to nginx!"**

That's a web server running on your machine. You just did that. With one command.

### Step 4: Create your own web page

> **Pause and predict**: What do you think happens if you replace the default nginx page with your own HTML file inside the container? Will it show immediately, or do you need to restart something? Try to guess — then follow along and see if you were right.

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

> **Pause and predict**: You just installed nginx, and it started automatically. Before you even open a web browser, what command could you run right here in the terminal to verify that the server is actually responding to requests on your VM?

### Step 4: Test the default page

Open your browser on your own computer and visit:

```
http://YOUR_PUBLIC_IP
```

You should see the nginx default page. That page is being served from a machine in a data center, across the internet, to your browser. Take a moment to appreciate that.

### Step 5: Create your custom page

> **Stop and think**: The default nginx page is located at `/var/www/html/index.html`. If you were to create a second file named `about.html` in that same directory, what exact URL would you type into your browser to view it?

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

1. **You are explaining the role of a web server to a colleague who is setting up a new application. They ask, "I wrote my HTML files, why do I need this nginx thing running on the server?" How do you explain the specific role nginx plays in delivering those files to users?**
   <details>
   <summary>Answer</summary>
   Nginx acts as the "waiter" or intermediary between the server's filesystem and the outside internet. While you have HTML files sitting on a hard drive, a browser cannot simply reach into your computer and read them. Nginx actively listens on a specific network port (usually 80 or 443) for incoming HTTP requests. When a request arrives, nginx interprets it, locates the corresponding HTML file on the filesystem, packages it into a valid HTTP response, and sends it back across the network to the user's browser. Without this active listening and responding mechanism, your HTML files are completely inaccessible to the web.
   </details>

2. **You successfully ran `docker run -d -p 9090:80 nginx` on your local machine. However, out of habit, you open your browser and navigate to `http://localhost:8080`. What happens exactly, and why did changing the first number in the `-p` flag cause this result?**
   <details>
   <summary>Answer</summary>
   Your browser will display a "connection refused" or "site can't be reached" error. The `-p 9090:80` flag tells Docker to map port 9090 on your physical machine (the host) to port 80 inside the isolated container where nginx is actually listening. By visiting `localhost:8080`, your browser is knocking on a network door (port 8080) that no application is currently listening to. Nginx is happily running inside the container and waiting for traffic on its internal port 80, but that traffic is now exclusively routed from port 9090 on your local machine, not 8080.
   </details>

3. **You deploy a website using the cloud VM method (Option B) and successfully copy your custom `index.html` to `/var/www/html/index.html`. Later, you try the Docker method (Option A) and copy your exact same HTML file to `/var/www/html/index.html` inside the container, but the browser still shows the default "Welcome to nginx!" page. What went wrong, and what does this teach you about software configuration?**
   <details>
   <summary>Answer</summary>
   The container is ignoring your custom file because the official nginx Docker image is configured by its creators to look for web files in a different directory—specifically, `/usr/share/nginx/html/`. Software like nginx doesn't have a single universal, magical location where it finds files; instead, it relies on a configuration file that dictates the exact filesystem path it should serve. The package maintainers for Ubuntu (Option B) chose `/var/www/html/` as their standard, while the Docker image maintainers chose `/usr/share/nginx/html/`. This teaches us that paths are arbitrary configuration choices made by system administrators or package maintainers, and you must always adapt to the specific environment's configuration rather than assuming universal defaults.
   </details>

4. **Trace what happens step-by-step when you type `http://YOUR_PUBLIC_IP` in a browser and your nginx server returns your custom page. Include DNS, TCP, port, nginx, and the filesystem.**
   <details>
   <summary>Answer</summary>
   When you type the URL, your browser checks if it needs to resolve a domain name via DNS (though here we use a raw IP, skipping DNS resolution). Next, your computer initiates a TCP connection to that IP address specifically on port 80, the default port for HTTP traffic. Once the TCP handshake completes, the browser sends an HTTP GET request asking for the root document (`/`). The nginx web server listening on port 80 receives this request, looks at its configuration to find the corresponding directory on the filesystem (like `/var/www/html/`), and reads the `index.html` file found there. Finally, nginx sends the contents of that file back through the TCP connection as an HTTP response, which your browser renders into the visible web page.
   </details>

5. **Your browser shows "connection refused" when visiting `localhost:8080`. List three possible causes and how you'd diagnose each.**
   <details>
   <summary>Answer</summary>
   "Connection refused" typically means nothing is actively listening on that port, which points to a few common culprits. First, the Docker container might have crashed or stopped; you can diagnose this by running `docker ps` to see if your `my-website` container is still actively running. Second, you might have mapped the wrong ports in your run command, such as `-p 8080:8080` instead of `-p 8080:80`; verify this by checking the port mappings in the `docker ps` output. Third, another application might already be using port 8080 on your host machine, preventing Docker from binding to it; you can check this using a command like `lsof -i :8080` or `netstat` to see what process is holding the port.
   </details>

6. **You can reach your cloud VM via SSH but not via browser on port 80. What's the most likely cause and what command would you run to verify?**
   <details>
   <summary>Answer</summary>
   The most likely cause is a firewall blocking incoming web traffic, as cloud providers usually block port 80 by default while allowing port 22 for SSH. Because SSH works, we know the server is online and reachable, so the issue must be specific to HTTP traffic. To verify if the server itself is working correctly internally, you can connect via SSH and run `curl http://localhost`. If `curl` returns the HTML content locally, it confirms nginx is running perfectly and the problem is definitely the cloud provider's external firewall or security group settings blocking external access to port 80.
   </details>

7. **You deployed your server and want to test if it's returning the correct HTML before opening a browser. How would you use `curl` to verify this, and what exactly are you looking for in the output?**
   <details>
   <summary>Answer</summary>
   You can use the command `curl http://localhost:8080` (or `curl http://YOUR_PUBLIC_IP`) directly from your terminal to simulate a basic browser request. This tool sends an HTTP GET request and prints the raw response body directly to your screen, bypassing any graphical rendering. You are looking to see if the terminal outputs the raw HTML code of your custom page, such as your `<h1>Hello, Internet!</h1>` tags. If it returns the expected HTML, you know the server is successfully processing requests and serving the correct file, proving the backend works even before a browser is involved.
   </details>

---

## Hands-On Exercise: Make It Yours

You've deployed the template page. Now make it **truly yours**.

### Part 1: The Customization Challenge

Customize your web page to include:

1. **Your name** (or a pseudonym -- this is the internet after all)
2. **Three things you learned** in this track that surprised you
3. **A link** to any website you like (use an `<a href="...">` tag)

Here's a hint for the link syntax:

```html
<a href="https://kubedojo.dev" style="color: #00d4ff;">KubeDojo</a>
```

### Part 2: The "Break It and Fix It" Challenge

Now that your server is working, let's intentionally break it and practice diagnosing the issue. In the real world, troubleshooting is just as important as deploying.

**Step 1: Break your deployment**
Depending on which option you chose, deliberately introduce a configuration error:
- **Option A (Local)**: Stop your working container (`docker stop my-website` and `docker rm my-website`). Start a new one with a broken port mapping: `docker run -d -p 9090:80 --name broken-site nginx`.
- **Option B (Cloud)**: Connect to your VM and intentionally rename your index file to something nginx isn't looking for: `sudo mv /var/www/html/index.html /var/www/html/broken.html`.

**Step 2: Observe the failure**
- **Option A**: Try to visit `http://localhost:8080` in your browser. What exact error message do your browser and network give you? Why did it happen?
- **Option B**: Try to visit your public IP in your browser. What exact error message do you see? Why did it happen?

**Step 3: Diagnose and fix**
Use your terminal skills to investigate the problem. Think about how the traffic flows from your browser, to the port, to the server, and finally to the filesystem. Once you understand the break, run the necessary terminal commands to fix it so your custom website is reachable again on the correct URL.

### Success criteria

- Your custom page loads in a browser (either `localhost:8080` or a public IP)
- It contains your name, three things you learned, and at least one link
- You edited it using nano (not by pasting into a GUI text editor)
- You successfully broke your server, observed the specific error, and restored it to working order
- You can explain to someone what nginx is doing and why the page appears

### Self-Assessment Rubric

Use this rubric to gauge your depth of understanding, not just a binary pass/fail:

- **Basic**: Your custom page loads with your name and a link. You successfully broke the server and blindly followed commands to fix it, achieving the desired result.
- **Good**: Your custom page loads, and you understand *why*. You can confidently explain the difference between the local port (`8080`) and the container port (`80`), explain why `sudo` was needed for the cloud option, and articulate the exact reason your "Break It and Fix It" scenario failed before you restored it.
- **Excellent**: You modified the nginx command or HTML significantly (e.g., adding an image, changing ports, or mapping a local directory instead of copying the file). You used `curl` from the terminal to test the server's response before opening the browser, proving you understand the underlying HTTP mechanism. You intentionally broke your server in a new, unguided way and successfully troubleshot it using terminal tools.

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
