---
title: "Module 0.9: What is the Cloud?"
slug: prerequisites/zero-to-terminal/module-0.9-what-is-the-cloud
sidebar:
  order: 10
---
> **Complexity**: `[QUICK]` - Concepts that click into place
>
> **Time to Complete**: 20 minutes
>
> **Prerequisites**: [Module 0.7 - Servers and SSH](module-0.7-servers-and-ssh/)

---

## Why This Module Matters

"The cloud" is one of the most used and least understood terms in technology. People hear it and imagine something ethereal -- data floating in the sky, software living in the mist.

The reality is much more concrete, and you already have the building blocks to understand it. After learning about computers (Module 0.1) and servers (Module 0.7), the cloud is the natural next step.

Here's why this matters: **Kubernetes runs in the cloud.** When you hear "deploy to the cloud," "cloud-native application," or "cloud infrastructure," you need to know what those words actually mean. After this module, you will.

---

## "The Cloud is Just Someone Else's Computer"

You've probably seen this meme. It's funny, and it's *partially* true.

At its core, cloud computing means: **instead of buying and maintaining your own servers, you rent them from someone else.**

But calling it "just someone else's computer" misses the bigger picture. It's like saying a hotel is "just someone else's bed." Technically true, but the hotel also handles cleaning, maintenance, security, room service, and everything else so you don't have to.

---

## The Kitchen Analogy: Build vs. Rent

Imagine you want to start a restaurant.

### Option 1: Build Your Own Kitchen

```
- Buy a building                        ($$$$$)
- Install commercial ovens, fridges     ($$$$$)
- Set up plumbing and electrical        ($$$$)
- Hire maintenance staff                ($$$)
- Fix things when they break            (ongoing cost)
- If you get MORE customers:
    Build an extension (takes months)
- If you get FEWER customers:
    You still pay for the empty kitchen
```

This is like buying your own servers. Companies used to do this -- they'd build a "data center" (a room full of servers) and manage everything themselves. This is called **on-premises** (or "on-prem") infrastructure.

### Option 2: Rent a Commercial Kitchen

```
- Walk in and start cooking             (pay hourly)
- Ovens, fridges already there          (included)
- Plumbing, electrical already done     (included)
- Maintenance handled by the landlord   (included)
- If you get MORE customers:
    Rent a bigger kitchen (takes minutes)
- If you get FEWER customers:
    Downsize to a smaller kitchen, pay less
```

This is cloud computing. Someone else built and maintains the infrastructure. You just use it and pay for what you consume.

---

## Why the Cloud Exists

The cloud exists because of three problems:

### Problem 1: Buying Servers is Expensive and Slow

```
Company: "We need 10 servers for our new project."
IT department: "OK. We need to:
  - Get budget approval (2 weeks)
  - Order the hardware (4 weeks)
  - Ship it to our data center (1 week)
  - Rack and cable it (3 days)
  - Install the OS (1 day)
  - Configure networking (2 days)
  Total: about 2 months."

Company: "But we need to launch next week..."
```

With the cloud:

```
Engineer: "We need 10 servers."
*types a command*
Cloud: "Here are your 10 servers. They're ready now."
Time elapsed: about 2 minutes.
```

### Problem 2: Guessing Capacity is Hard

If you buy your own servers, you have to predict how many you'll need. Get it wrong and you either:
- **Bought too few**: Your website crashes when it gets popular
- **Bought too many**: You're paying for servers that sit idle

With the cloud, you can scale up and down as needed. Black Friday traffic spike? Add more servers. Sunday at 3 AM? Scale down and save money.

### Problem 3: Maintenance is a Full-Time Job

Servers need:
- Power (with backup generators)
- Cooling (they generate a LOT of heat)
- Physical security (locked buildings, cameras)
- Network connections (redundant, fast)
- Replacement parts (hard drives fail, power supplies die)
- Software updates (operating systems, security patches)

Cloud providers handle all of this. You focus on your actual business.

---

## The Big Three Cloud Providers

Three companies dominate cloud computing. Think of them as the three biggest commercial kitchen chains in the world -- different branding, different menus, but the same fundamental concept.

### Amazon Web Services (AWS)

```
- The first major cloud provider (launched 2006)
- The largest by market share (~31%)
- The "original" -- most companies' first cloud
- Kitchen analogy: The biggest chain, the one everyone knows
```

### Microsoft Azure

```
- Launched 2010
- Second largest (~25%)
- Popular with companies already using Microsoft products
- Kitchen analogy: The chain that integrates with your existing equipment
```

### Google Cloud Platform (GCP)

```
- Launched 2008 (public in 2011)
- Third largest (~11%)
- Known for data analytics and machine learning
- Fun fact: Kubernetes was INVENTED at Google
- Kitchen analogy: The chain with the fanciest kitchen technology
```

There are also smaller providers: DigitalOcean, Linode (now Akamai), Hetzner, OVH, and many more. They're like independent commercial kitchens -- smaller, sometimes cheaper, sometimes better for specific needs.

**You don't need to pick one right now.** The concepts are the same across all of them, and the skills you'll learn transfer between them.

---

## What the Cloud Actually Offers

Cloud providers sell services in categories. Here are the main ones, in kitchen terms:

### Compute: Rent a Server

```
"I need a computer that runs 24/7."

Cloud service: Virtual Machine (VM) / Instance
  - AWS calls it: EC2 (Elastic Compute Cloud)
  - Azure calls it: Virtual Machines
  - GCP calls it: Compute Engine

Kitchen analogy: Renting a cooking station.
  You choose the size (small burner or industrial oven)
  and pay by the hour.
```

### Storage: Rent a Pantry

```
"I need to store files, images, backups."

Cloud service: Object Storage
  - AWS calls it: S3 (Simple Storage Service)
  - Azure calls it: Blob Storage
  - GCP calls it: Cloud Storage

Kitchen analogy: Renting pantry shelves.
  You pay per shelf used, per month.
```

### Networking: Rent the Delivery Fleet

```
"My servers need to talk to each other and to the internet."

Cloud service: Virtual Networks, Load Balancers
  - AWS calls it: VPC (Virtual Private Cloud)
  - Azure calls it: Virtual Network
  - GCP calls it: VPC

Kitchen analogy: Renting the delivery drivers and route planning.
  Your kitchens need roads between them and routes to customers.
```

### Databases: Rent a Recipe Book System

```
"I need to store and query structured data."

Cloud service: Managed Databases
  - AWS calls it: RDS (Relational Database Service)
  - Azure calls it: Azure SQL Database
  - GCP calls it: Cloud SQL

Kitchen analogy: A managed filing system for all your recipes,
  orders, and inventory. Someone else maintains the filing cabinets.
```

---

## Pay-As-You-Go: Only Pay for What You Cook

One of the most revolutionary aspects of cloud computing is the pricing model.

Traditional IT: "Buy 10 servers for $200,000. Use them for 5 years."

Cloud: "Rent a server for $0.05 per hour. Turn it off when you don't need it."

```
Example:
  A small server costs about $0.01/hour on AWS
  Running it 24/7 for a month: $0.01 x 24 x 30 = $7.20

  Need it only 8 hours a day for testing?
  $0.01 x 8 x 22 workdays = $1.76/month

  Need 100 servers for 2 hours for a big processing job?
  $0.01 x 100 x 2 = $2.00
```

This is like paying for a commercial kitchen by the hour instead of buying the building. Use it during lunch rush, shut it down at night, pay only for when the burners are on.

---

## Where Kubernetes Fits

Here's where everything in the Zero to Terminal track comes together:

```
Module 0.1: You learned about one computer (one kitchen)
Module 0.3: You learned to give commands to that kitchen
Module 0.5: You learned to write instructions (recipes/scripts)
Module 0.7: You learned to connect to remote kitchens
Module 0.9: You learned that the cloud has THOUSANDS of kitchens for rent

NOW: Kubernetes is the system that manages all of those kitchens.
```

Kubernetes (often written "K8s" -- the 8 stands for the 8 letters between K and s) was created at Google to solve this problem:

> "We have thousands of servers. How do we automatically decide which server runs which program, handle failures, and scale up when things get busy?"

Without Kubernetes:
```
Engineer: "Deploy the app to server-42."
*server-42 crashes at 3 AM*
Engineer's phone: *RING RING*
Engineer: "Ugh... let me move it to server-43 manually."
```

With Kubernetes:
```
Engineer: "I need 3 copies of this app running."
Kubernetes: "Done. Running on server-42, server-67, and server-91."
*server-42 crashes at 3 AM*
Kubernetes: "Server-42 is down. Moving that copy to server-15. Done."
Engineer: *sleeping peacefully*
```

Kubernetes is the **restaurant manager for the cloud** -- it manages thousands of kitchens, decides which kitchen handles which orders, and automatically handles problems without waking anyone up.

---

## Your Learning Path

You've now completed the Zero to Terminal track. Here's where you stand and where you're going:

```
Zero to Terminal (YOU ARE HERE -- COMPLETE!)
  ✓ Understand computers
  ✓ Use the terminal
  ✓ Edit files
  ✓ Understand servers and SSH
  ✓ Understand cloud computing

        ↓

Cloud Native 101 (NEXT)
  → What are containers?
  → Docker fundamentals
  → What is Kubernetes?
  → The cloud-native ecosystem

        ↓

Kubernetes Basics
  → Your first cluster
  → kubectl basics
  → Pods, Deployments, Services

        ↓

CKA Certification Track
  → Certified Kubernetes Administrator
  → Your first professional credential

        ↓

Platform Engineering
  → SRE, GitOps, DevSecOps, MLOps
  → Building platforms that other developers use
```

**You now know more about cloud computing than 90% of people.** The rest is details -- important details that you'll learn step by step, but details nonetheless. The hard part was building the mental model, and you've done that.

---

## Did You Know?

- **AWS started as a side project.** Amazon built massive computing infrastructure to run their online store. Someone realized they could rent out the spare capacity to other companies. AWS launched in 2006 and now generates over $90 billion in annual revenue -- more than Amazon's retail profits. The side project became one of the most profitable businesses in history.

- **Cloud data centers are enormous.** A single AWS data center campus in Virginia covers over 2 million square feet -- that's about 34 football fields. It contains hundreds of thousands of servers, uses enough electricity to power a small city, and is cooled by systems that move thousands of gallons of water per minute. There are hundreds of these facilities worldwide.

- **Kubernetes means "helmsman" in Greek.** The people at Google who created it named it after the person who steers a ship. The K8s logo is a ship's wheel with seven spokes. The idea is that Kubernetes "steers" your containers through the cloud. The project was originally called "Project Seven" internally at Google (after the Star Trek character Seven of Nine -- yes, really).

---

## Common Mistakes

| Mistake | Why It's a Problem | What to Do Instead |
|---------|-------------------|-------------------|
| Thinking the cloud is always cheaper | For steady, predictable workloads, owning servers can be cheaper | Cloud is cheapest when demand varies. Evaluate based on your actual needs |
| Leaving cloud servers running when not needed | You're paying by the hour for a kitchen that's not cooking | Turn off development and test servers when you're not using them |
| Choosing a cloud provider based on hype | "Everyone uses AWS" isn't a technical argument | Learn the concepts (they're the same everywhere), then choose based on your actual needs |
| Thinking you need to learn ALL cloud services | AWS alone has 200+ services. No one uses them all | Start with compute, storage, and networking. Add services as you need them |
| Being intimidated by cloud complexity | The cloud seems overwhelming at first | You already understand the fundamentals: it's computers, storage, and networking. Everything else is built on top of these three |

---

## Quiz

1. **In plain terms, what is cloud computing?**
   <details>
   <summary>Answer</summary>
   Cloud computing is renting computing resources (servers, storage, networking) from a provider instead of buying and maintaining your own. Like renting a commercial kitchen instead of building one -- someone else handles the building, equipment, and maintenance, and you pay for what you use.
   </details>

2. **Name the three major cloud providers and one thing each is known for.**
   <details>
   <summary>Answer</summary>
   AWS (Amazon Web Services) -- the largest and oldest major cloud, launched in 2006. Azure (Microsoft) -- popular with enterprises already using Microsoft products. GCP (Google Cloud Platform) -- known for data analytics, machine learning, and being the birthplace of Kubernetes.
   </details>

3. **What are the three fundamental categories of cloud services?**
   <details>
   <summary>Answer</summary>
   Compute (renting servers/processing power), Storage (renting space for files and data), and Networking (connecting servers to each other and to the internet). Every other cloud service is built on top of these three fundamentals.
   </details>

4. **What problem does Kubernetes solve?**
   <details>
   <summary>Answer</summary>
   Kubernetes manages the deployment of applications across many servers automatically. It decides which server runs which application, scales applications up or down based on demand, and handles failures by automatically moving workloads from broken servers to healthy ones -- all without human intervention. It's the "restaurant manager" for cloud kitchens.
   </details>

5. **Why is pay-as-you-go pricing a big deal?**
   <details>
   <summary>Answer</summary>
   Traditional IT requires buying servers upfront (large capital expense) and paying for them whether you use them or not. Pay-as-you-go means you only pay for what you actually use, by the hour or even by the second. You can spin up 100 servers for an hour and pay almost nothing. This makes it possible for a startup to use the same infrastructure as a giant corporation, because you don't need $200,000 upfront for hardware.
   </details>

---

## Hands-On Exercise: Explore Free Cloud Tiers

The major cloud providers all offer free tiers so you can experiment without paying. Let's take a look at what's available.

### Step 1: Visit the free tier pages

Open these pages in your browser:

- **AWS Free Tier**: [https://aws.amazon.com/free](https://aws.amazon.com/free)
- **Google Cloud Free Tier**: [https://cloud.google.com/free](https://cloud.google.com/free)
- **Azure Free Tier**: [https://azure.microsoft.com/free](https://azure.microsoft.com/free)

### Step 2: Look for these specific things

On each page, try to find:

1. **Free compute**: How much free server time do they offer? (Look for "EC2" on AWS, "Compute Engine" on GCP, "Virtual Machines" on Azure.)

2. **Free storage**: How much free storage? (Look for "S3" on AWS, "Cloud Storage" on GCP, "Blob Storage" on Azure.)

3. **Duration**: Is the free tier "12 months" or "always free"? Many services are free for 12 months after signup, then start charging. Some are always free within certain limits.

### Step 3: Write down what you found

Open your terminal and create a notes file:

```bash
nano ~/cloud-notes.txt
```

Write what you found. Something like:

```
My Cloud Research Notes
=======================
Date: March 2026

AWS Free Tier:
- EC2: 750 hours/month of t2.micro for 12 months
- S3: 5 GB storage for 12 months
- ...

GCP Free Tier:
- e2-micro instance: always free
- 5 GB Cloud Storage: always free
- ...

Azure Free Tier:
- 750 hours of B1S VM for 12 months
- 5 GB Blob Storage for 12 months
- ...

Notes:
- All three require a credit card to sign up (but won't charge for free tier)
- GCP has the most "always free" services
- AWS has the most services overall
```

Save and exit (`Ctrl + O`, Enter, `Ctrl + X`).

### Step 4: Verify your notes

```bash
cat ~/cloud-notes.txt
```

**You do NOT need to sign up for any of these right now.** Just looking at the pages and understanding what's available is the exercise. When you reach the Kubernetes track, we'll guide you through setting up a free cluster.

**Success criteria**: You visited at least one free tier page, understood the types of services offered, and saved notes about what you found. You can now speak intelligently about cloud computing -- what it is, who provides it, and what it costs.

---

## What's Next?

Congratulations -- you've completed the **Zero to Terminal** track!

You started knowing nothing about computers or terminals, and now you understand:
- How computers work (CPU, RAM, disk, OS)
- How to navigate and manage files from the terminal
- How to edit files and write scripts
- What servers are and how to connect to them
- What the cloud is and where Kubernetes fits

Your next step is [Cloud Native 101](../cloud-native-101/module-1.1-what-are-containers/), where you'll learn about containers -- the technology that makes Kubernetes possible. Containers are like standardized shipping containers for software, and they changed everything about how we build and deploy applications.

The foundation is solid. The kitchen is built. Time to start cooking.

---

> **You just used a tool that senior engineers use every day. You belong here.**
