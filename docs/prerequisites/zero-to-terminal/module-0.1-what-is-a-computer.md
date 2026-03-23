# Module 0.1: What is a Computer?

> **Complexity**: `[QUICK]` - No technical experience needed
>
> **Time to Complete**: 20 minutes
>
> **Prerequisites**: None. Seriously, none. If you can read this, you're ready.

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

You can't manage thousands of kitchens if you don't understand how *one* kitchen works. That's what this module gave you.

---

## Did You Know?

- **Your phone is a computer too.** A modern smartphone has more computing power than the computers NASA used to land on the moon in 1969. The Apollo Guidance Computer had 74 KB of memory. Your phone has millions of times more.

- **RAM was once magnetic.** Early computers used tiny magnetic rings (called "core memory") for RAM. Each ring stored a single bit (0 or 1). A full megabyte would have needed over 8 million tiny rings. Today, your computer's RAM chip is smaller than a postage stamp and holds billions of bits.

- **SSDs have no moving parts.** Traditional hard drives have spinning metal disks and a moving arm (like a record player). SSDs store data in electronic circuits with zero moving parts, which is why they're faster, quieter, and more durable. Drop a laptop with an HDD and you might lose data. Drop one with an SSD and you probably won't.

---

## Common Mistakes

| Mistake | Why It's a Problem | What to Do Instead |
|---------|-------------------|-------------------|
| Confusing RAM and storage | "I have 256 GB of memory" -- you probably mean storage, not RAM | RAM = temporary counter space (8-32 GB typical). Storage = permanent pantry (256 GB - 2 TB typical) |
| Thinking more storage = faster computer | A bigger pantry doesn't make the chef cook faster | Speed comes from CPU and RAM. Storage just means more room for files |
| Ignoring RAM when computer is slow | Opening 47 browser tabs and wondering why things crawl | Check how much RAM is in use. Close what you don't need |
| Thinking all computers are the same | "A computer is a computer" | A laptop, a phone, a server, and a smartwatch are all computers -- but built for very different jobs |

---

## Quiz

1. **What does the CPU do?**
   <details>
   <summary>Answer</summary>
   The CPU (Central Processing Unit) is the part of the computer that executes instructions. It's the "chef" that does the actual work -- processing data, running calculations, and carrying out every action you ask your computer to perform.
   </details>

2. **What happens to everything in RAM when you turn off your computer?**
   <details>
   <summary>Answer</summary>
   It disappears. RAM is temporary (volatile) memory. Like counter space in a kitchen, it only holds things while the kitchen is open. When power is off, RAM is wiped clean. That's why your files are saved to disk (the pantry), not kept only in RAM.
   </details>

3. **What's the difference between an HDD and an SSD?**
   <details>
   <summary>Answer</summary>
   An HDD (Hard Disk Drive) has spinning metal disks and a moving arm to read/write data -- it's like a record player. It's cheaper but slower. An SSD (Solid State Drive) stores data in electronic circuits with no moving parts -- it's faster, quieter, and more durable, but costs more per gigabyte.
   </details>

4. **Why does almost every server run Linux?**
   <details>
   <summary>Answer</summary>
   Linux is open-source (free to use and modify), extremely stable, highly customizable, and efficient with resources. For servers that need to run 24/7 without a graphical interface, Linux is the natural choice. This is also why learning Linux commands is essential for working with Kubernetes.
   </details>

5. **In the kitchen analogy, what is the Operating System?**
   <details>
   <summary>Answer</summary>
   The restaurant manager. It doesn't cook (process data) itself, but it coordinates everything: deciding which chef handles which order, managing counter space so programs don't interfere with each other, organizing storage, and handling communication with the outside world.
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

---

## What's Next?

In [Module 0.3: First Terminal Commands](module-0.3-first-commands.md), you'll open the terminal and start typing commands. You'll navigate your computer's file system, create folders and files, and move things around -- all without clicking a single button.

The graphical interface is the dining room. The terminal is the kitchen. Time to step into the kitchen.

---

> **You just used a tool that senior engineers use every day. You belong here.**
