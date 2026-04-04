---
title: "Module 0.1: What is a Computer?"
slug: prerequisites/zero-to-terminal/module-0.1-what-is-a-computer
sidebar:
  order: 2
---
> **Complexity**: `[QUICK]` - No technical experience needed
>
> **Time to Complete**: 20 minutes
>
> **Prerequisites**: None. Seriously, none. If you can read this, you're ready.

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Name** the four core parts of any computer (CPU, RAM, disk, OS) and explain what each one does
- **Predict** what happens when your computer runs out of RAM or disk space
- **Find** your own computer's specs using system tools or terminal commands
- **Explain** why servers run Linux and why that matters for Kubernetes

---

## Why This Module Matters

Every single thing you'll learn in this curriculum -- Kubernetes, containers, cloud computing -- runs on computers. But most people have never been told what's actually happening inside the box on their desk (or the slab in their pocket).

Understanding your computer's parts isn't just trivia. When something goes wrong later -- when a program is slow, when a server runs out of memory, when Kubernetes decides to restart your application -- you'll know *why* because you understand the hardware underneath.

This is where your journey begins.

---

## The Restaurant Kitchen

Imagine a restaurant kitchen. Not a fancy one -- just a regular, busy kitchen that needs to take orders, prepare food, and serve customers.

Your computer works exactly like this kitchen. Every part has a job, and when they work together, meals (or programs) get made.

Let's meet the kitchen staff and equipment.

---

## The CPU: Your Head Chef

The **CPU** (Central Processing Unit) is the chef. It's the part of the computer that actually *does the work*.

When you click a button, type a letter, or open a program, the CPU is the one carrying out those instructions. It reads instructions one by one (incredibly fast) and executes them.

```
Think of it this way:

  Order comes in: "Make a sandwich"
  Chef reads the recipe:
    Step 1: Get bread         ✓
    Step 2: Add lettuce       ✓
    Step 3: Add tomato        ✓
    Step 4: Serve             ✓
```

A faster CPU is like a faster chef -- they can handle more orders per second.

**What you'll see on your computer**: Something like "Intel Core i7" or "Apple M2" or "AMD Ryzen 5". These are brand names for CPUs, like saying "Chef Gordon" or "Chef Julia". The number of **cores** is like having multiple chefs -- a 4-core CPU has 4 chefs working at the same time.

---

## RAM: Your Counter Space

**RAM** (Random Access Memory) is the counter space in your kitchen -- the area where the chef does their active work.

When you open a program, it gets loaded from storage into RAM. Why? Because RAM is *fast*. The chef needs ingredients within arm's reach, not in a pantry down the hall.

Here's the critical thing about counter space: **when you close the kitchen (turn off the computer), the counter gets wiped clean.** Everything on it disappears. That's exactly how RAM works -- it only holds things while the power is on.

```
More RAM = More counter space = More things open at once

  4 GB RAM   → You can chop vegetables OR boil pasta (not both well)
  8 GB RAM   → You can comfortably prep a full meal
  16 GB RAM  → You can prep multiple meals simultaneously
  32 GB RAM  → You're running a professional kitchen
```

**When RAM fills up**, your computer gets slow. Just like a chef with no counter space has to keep putting things away and getting them back out, your computer starts "swapping" data back and forth to disk. This is painfully slow.

In 2017, a GitLab engineer accidentally deleted a production database. The recovery was slow partly because backup processes were competing for RAM and disk I/O with production traffic — understanding these resources isn't academic, it's what prevents outages.

> **Pause and predict**: You have 8 GB of RAM and you open a web browser with 30 tabs, a video editor, and a music player — all at once. What do you think happens? If you guessed "the computer gets painfully slow" — you're right. Each program needs counter space, and 30 browser tabs alone can eat 4-6 GB. The OS starts shuffling data between RAM and disk (swapping), and everything grinds to a crawl.

---

## Disk/SSD: Your Pantry

The **disk** (also called storage, hard drive, or SSD) is your pantry. This is where everything is stored *permanently*.

Unlike counter space (RAM), the pantry survives when you close the kitchen. Turn off your computer, turn it back on -- your files, photos, programs are all still there. They were in the pantry the whole time.

```
Two types of pantry:

  HDD (Hard Disk Drive):
    - Like a big walk-in pantry
    - Lots of space, affordable
    - Slower to find things (mechanical moving parts)

  SSD (Solid State Drive):
    - Like a well-organized shelf right outside the kitchen
    - Faster to find things (no moving parts)
    - More expensive per shelf
    - This is what most modern computers use
```

**What you'll see on your computer**: Storage is measured in gigabytes (GB) or terabytes (TB). 1 TB = 1,000 GB. A typical laptop has 256 GB to 1 TB of storage.

---

## The Operating System: Your Restaurant Manager

The **Operating System** (OS) is the restaurant manager. It doesn't cook anything itself, but *nothing works without it*.

The OS:
- Decides which chef (CPU core) handles which order (program)
- Manages counter space (RAM) so programs don't step on each other
- Organizes the pantry (disk) so files can be found
- Handles communication (networking, display, keyboard input)

```
The three main operating systems:

  Windows  → The most common (used by ~74% of desktop computers)
  macOS    → Apple's system (what runs on Macs)
  Linux    → The open-source one (runs most of the world's servers)
```

Here's a fact that will matter a LOT in your Kubernetes journey: **almost every server in the world runs Linux.** Your laptop might run Windows or macOS, but the cloud? That's Linux territory. That's why we'll be learning Linux commands in the next modules.

> **Stop and think**: Why do you think servers don't use Windows or macOS? Think about what servers need — they run 24/7, they don't need a graphical interface, they need to be stable and efficient. Linux is free, customizable, and uses fewer resources because it doesn't need to render a desktop. That's why even Microsoft runs Linux on most of its Azure cloud servers.

---

## Programs: Your Recipes

A **program** (also called an application or app) is a recipe. It's a set of instructions that tells the CPU what to do.

When you open a web browser, you're telling the restaurant manager (OS) to hand the browser recipe to the chef (CPU), set up counter space (RAM) for it, and let it do its thing.

```
Some "recipes" you use every day:

  Web browser (Chrome, Firefox)  → Recipe for displaying web pages
  Text editor (Word, Notepad)    → Recipe for editing text
  Terminal                       → Recipe for talking directly to the OS
```

That last one -- the **terminal** -- is what we'll spend most of our time with. It's like walking into the kitchen and talking directly to the staff, instead of placing orders through a waiter (the graphical interface).

---

## How It All Works Together

Let's trace what happens when you open a photo on your computer:

```
1. You double-click "vacation.jpg"

2. The OS (manager) sees your request
   → "Customer wants to see a photo"

3. The OS loads the photo viewer program from disk (pantry) into RAM (counter)
   → "Get the photo recipe and ingredients ready"

4. The OS loads vacation.jpg from disk into RAM
   → "Grab that specific dish from storage"

5. The CPU (chef) processes the image data
   → "Follow the recipe to prepare the photo for display"

6. The result appears on your screen
   → "Dish served!"
```

Every single thing your computer does follows this pattern. Every. Single. Thing.

---

## Why This Matters for Kubernetes

Here's where this gets exciting.

Kubernetes is a system that manages **thousands of these kitchens** (computers) at the same time. It decides:

- Which kitchen (server) should handle which order (program)
- How much counter space (RAM) each program gets
- What to do when a kitchen breaks down (move the orders to another kitchen)
- How to add more kitchens when the restaurant gets busy

You can't manage thousands of kitchens if you don't understand how *one* kitchen works. That's what this module gave you. Companies pay per GB of RAM and per CPU core in the cloud. AWS charges ~$0.05/hour for a server with 8 GB RAM. Misunderstanding these resources literally costs money.

---

## Did You Know?

- **Your phone is a computer too.** A modern smartphone has more computing power than the computers NASA used to land on the moon in 1969. The Apollo Guidance Computer had 74 KB of memory. Your phone has millions of times more.

- **RAM was once magnetic.** Early computers used tiny magnetic rings (called "core memory") for RAM. Each ring stored a single bit (0 or 1). A full megabyte would have needed over 8 million tiny rings. Today, your computer's RAM chip is smaller than a postage stamp and holds billions of bits.

- **SSDs have no moving parts.** Traditional hard drives have spinning metal disks and a moving arm (like a record player). SSDs store data in electronic circuits with zero moving parts, which is why they're faster, quieter, and more durable. Drop a laptop with an HDD and you might lose data. Drop one with an SSD and you probably won't.

- **The first computer bug was an actual bug.** In 1947, engineers working on the Harvard Mark II computer found a literal moth stuck in a relay, causing the machine to fail. They taped the moth into their logbook and noted it as the "first actual case of bug being found." The term "debugging" has been used in computer science ever since.

---

## Common Mistakes

| Mistake | Why It's a Problem | What to Do Instead |
|---------|-------------------|-------------------|
| Confusing RAM and storage | "I have 256 GB of memory" -- you probably mean storage, not RAM | RAM = temporary counter space (8-32 GB typical). Storage = permanent pantry (256 GB - 2 TB typical) |
| Thinking more storage = faster computer | A bigger pantry doesn't make the chef cook faster | Speed comes from CPU and RAM. Storage just means more room for files |
| Ignoring RAM when computer is slow | Opening 47 browser tabs and wondering why things crawl | Check how much RAM is in use. Close what you don't need |
| Over-provisioning cloud servers | "Let's just use the biggest server so it doesn't crash." | In the cloud, you pay for what you provision. A team might pay $400/month for a 32GB RAM server when their application only uses 2GB. Right-sizing saves thousands of dollars. |
| Assuming CPU speed solves internet lag | "My web pages load slowly, I need a better processor." | Internet speed depends on your network bandwidth and latency. Troubleshoot your router, Wi-Fi signal, or ISP connection first before blaming your computer hardware. |
| Never restarting the operating system | "I just close my laptop lid, why is my computer glitching?" | Restarting clears out the RAM completely and restarts background processes. Make it a habit to reboot at least once a week to clear temporary issues. |
| Judging a CPU only by its clock speed | "A 4 GHz CPU is always better than a 3 GHz one." | Look at the number of cores as well. A 3 GHz CPU with 8 cores can handle many simultaneous tasks much better than a 4 GHz CPU with only 2 cores. |

---

## Quiz

1. **You are hired to set up a new restaurant kitchen. You have a chef (CPU), counter space (RAM), and a pantry (Disk), but no one to take orders from customers, assign tasks to the chef, or organize the ingredients. What component is missing?**
   <details>
   <summary>Answer</summary>
   The Operating System (OS) is missing. Just like a restaurant manager, the OS does not process the data itself, but it coordinates all the hardware. It decides which CPU core handles which program, manages the RAM so programs do not overwrite each other's data, and organizes files on the disk. Without an OS, the hardware cannot communicate with the user or run any software. It essentially acts as the bridge between your instructions and the physical machine.
   </details>

2. **You're writing a document and the power goes out before you save. What is lost and what survives? Explain using the kitchen analogy.**
   <details>
   <summary>Answer</summary>
   The unsaved changes to your document are lost, but the original file and your other programs survive. Before you save, your work is kept in RAM, which is temporary "counter space" that requires electricity to hold data. When the power goes out, the counter is wiped clean. The files that survive were already stored on your disk, which acts as the "pantry" and permanently retains data even without power. This is why frequent saving or auto-save features are critical for protecting your work.
   </details>

3. **Your computer is running a video call and the video keeps freezing, but your internet speed test shows 100 Mbps. Which component is most likely the bottleneck — CPU, RAM, or disk? Why?**
   <details>
   <summary>Answer</summary>
   The CPU is the most likely bottleneck in this scenario. Processing live video requires the computer to constantly decode and encode images in real-time, which is a highly intensive task for the CPU "chef". If the internet is fast, the data is arriving on time, but the CPU simply cannot keep up with processing it fast enough. While RAM might also be a factor if it is completely full, video encoding and decoding are primarily bound by CPU performance. Closing other heavy applications can help free up CPU resources for the call.
   </details>

4. **Your friend says their computer is slow and asks if they should buy a bigger hard drive. What would you tell them, and what should they check first?**
   <details>
   <summary>Answer</summary>
   A bigger hard drive will not make their computer faster, because storage capacity does not affect processing speed. That would be like building a bigger pantry and expecting the chef to cook faster. They should first check their RAM and CPU usage to see if the system is overloaded with too many open programs. If their RAM is entirely full, the computer is likely "swapping" data back and forth to the slow disk, which causes the sluggishness. Upgrading the RAM or switching to an SSD (if they have an older HDD) would be more effective upgrades.
   </details>

5. **Your team is deploying a new web application to the cloud and debating whether to use Windows or Linux servers. Based on what you know about operating systems, why will they almost certainly choose Linux?**
   <details>
   <summary>Answer</summary>
   They will almost certainly choose Linux because it is optimized for server environments where stability and efficiency are critical. Unlike desktop operating systems, Linux can run perfectly without a graphical user interface, which means it consumes significantly less RAM and CPU overhead. This allows more hardware resources to be dedicated entirely to running the actual application instead of rendering screens. Furthermore, Linux is open-source and free, making it the cost-effective standard foundation for cloud infrastructure and platforms like Kubernetes. Its command-line focus also makes it far easier to automate at scale.
   </details>

6. **You are running a database server for your company's e-commerce site, and during a major sale, the server crashes. The monitoring logs show that CPU utilization was at 20%, but memory usage hit 100% right before the crash. What caused the crash, and how should you fix it?**
   <details>
   <summary>Answer</summary>
   The crash was caused by the server running out of RAM (memory exhaustion) rather than a lack of processing power. When the server reached 100% memory usage, the operating system had no more "counter space" to process the sudden influx of customer orders and likely killed the database process to protect itself. To fix this, you need to either provision a server with more RAM to handle the peak load, or optimize the database queries to use less memory. The low CPU utilization indicates that upgrading the processor would not have prevented this outage.
   </details>

7. **Your colleague accidentally spills coffee on their laptop, completely destroying the motherboard, CPU, and RAM. However, a technician manages to extract the internal SSD and connect it to a new computer. Will your colleague be able to recover their files? Why or why not?**
   <details>
   <summary>Answer</summary>
   Yes, your colleague will almost certainly be able to recover their files. The SSD acts as the computer's "pantry," where data is stored permanently even when the power is off or other components fail. Because the CPU and RAM only handle active processing and temporary data, their destruction does not erase the information saved on the storage drive. As long as the physical SSD itself was not damaged by the spill or encrypted without a backup key, all documents, photos, and installed programs remain intact and readable.
   </details>

---

## Hands-On Exercise: Check Your Computer's Specs

Time to look inside your own kitchen. Let's find out what hardware you're working with.

### On macOS (Apple):

Click the Apple menu (top-left corner) and select **About This Mac**. You'll see:
- **Chip** or **Processor**: Your CPU (the chef)
- **Memory**: Your RAM (the counter space)
- **Storage**: Click the Storage tab to see your disk (the pantry)

You can also open Terminal (search for "Terminal" in Spotlight) and type:

```bash
# See your CPU info
sysctl -n machdep.cpu.brand_string

# See your RAM (in bytes -- divide by 1073741824 to get GB)
sysctl -n hw.memsize

# See your disk space
df -h /
```

### On Windows:

Press `Windows key + I` to open Settings, then go to **System > About**. Or search for "System Information" in the Start menu. You'll see:
- **Processor**: Your CPU
- **Installed RAM**: Your counter space
- **Storage**: Open File Explorer and look at your C: drive

You can also open Command Prompt and type:

```
systeminfo
```

### On Linux:

Open a terminal and type:

```bash
# See your CPU info
lscpu

# See your RAM
free -h

# See your disk space
df -h
```

### What to Look For

Write down (yes, physically write it down or type it somewhere):

1. **My CPU is**: _____________
2. **I have ___ GB of RAM**
3. **I have ___ GB of storage**
4. **My operating system is**: _____________

**Success criteria**: You can name your CPU, how much RAM you have, and how much storage you have. You now know your kitchen better than most people know theirs.

### Stretch Challenge

Open Activity Monitor (macOS) / Task Manager (Windows) / top (Linux) and identify which program is using the most RAM. Can you predict what would happen if you closed it?

---

## What's Next?

In [Module 0.2: What is a Terminal?](../module-0.2-what-is-a-terminal/), you'll learn what the terminal actually is, why it exists alongside the graphical interface, and why every engineer eventually learns to use it.

The graphical interface is the dining room. The terminal is the kitchen. Time to find out what's behind that door.

---

> **You just used a tool that senior engineers use every day. You belong here.**