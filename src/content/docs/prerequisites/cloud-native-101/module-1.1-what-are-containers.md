---
title: "Module 1.1: What Are Containers?"
slug: prerequisites/cloud-native-101/module-1.1-what-are-containers/
sidebar:
  order: 2
---
> **Complexity**: `[QUICK]` - Foundational concepts
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: None

---

## Why This Module Matters

Containers are the building blocks of modern application deployment. Before you can understand Kubernetes (a container orchestrator), you need to understand what containers are and what problems they solve.

This isn't about memorizing technical details—it's about understanding the "why" that makes everything else make sense.

---

## The Problem Containers Solve

### The Classic Deployment Problem

```
Developer: "It works on my machine!"
Operations: "But it doesn't work in production."
Developer: "My machine has Python 3.9, the right libraries, correct paths..."
Operations: "Production has Python 3.7, different libraries, different paths..."
Everyone: 😤
```

This is the **environment consistency problem**. Applications depend on:
- Operating system version
- Runtime versions (Python, Node, Java)
- Library versions
- Configuration files
- Environment variables
- File paths

When any of these differ between development and production, things break.

### Traditional Solutions (That Didn't Scale)

**Solution 1: Detailed Documentation**
```
README.md:
1. Install Python 3.9.7
2. Run `pip install -r requirements.txt`
3. Set environment variables...
4. Configure paths...
(Nobody reads this. When they do, it's outdated.)
```

**Solution 2: Virtual Machines**
```
Ship the entire operating system:
- Works consistently
- But 10GB+ per application
- Minutes to start
- Heavy resource usage
- Hard to manage at scale
```

### The Container Solution

```
What if we could package:
- The application
- Its dependencies
- Its configuration
- Everything it needs to run

Into a lightweight, portable unit that runs the same everywhere?

That's a container.
```

---

## Containers vs. Virtual Machines

```
┌─────────────────────────────────────────────────────────────┐
│              VMs vs CONTAINERS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VIRTUAL MACHINES                 CONTAINERS                │
│  ┌─────────────────────┐         ┌─────────────────────┐   │
│  │ App A │ App B │ App C│         │ App A │ App B │ App C│   │
│  ├───────┼───────┼──────┤         ├───────┼───────┼──────┤   │
│  │Guest  │Guest  │Guest │         │Container Runtime     │   │
│  │OS     │OS     │OS    │         │(containerd)          │   │
│  ├───────┴───────┴──────┤         ├──────────────────────┤   │
│  │    Hypervisor        │         │    Host OS           │   │
│  ├──────────────────────┤         ├──────────────────────┤   │
│  │    Host OS           │         │    Hardware          │   │
│  ├──────────────────────┤         └──────────────────────┘   │
│  │    Hardware          │                                    │
│  └──────────────────────┘                                    │
│                                                             │
│  Each VM: Full OS copy            Containers: Share host OS │
│  Size: Gigabytes                  Size: Megabytes           │
│  Start: Minutes                   Start: Seconds            │
│  Isolation: Hardware-level        Isolation: Process-level  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Differences

| Aspect | Virtual Machine | Container |
|--------|-----------------|-----------|
| Size | Gigabytes | Megabytes |
| Startup | Minutes | Seconds |
| OS | Full guest OS per VM | Shared host kernel |
| Isolation | Hardware virtualization | Process isolation |
| Portability | VM image formats vary | Universal container images |
| Density | ~10-20 VMs per server | ~100s of containers per server |

---

## How Containers Work

Containers use Linux kernel features to create isolated environments:

### 1. Namespaces (Isolation)

Namespaces make a process think it has its own system:

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX NAMESPACES                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Namespace    What It Isolates                              │
│  ─────────────────────────────────────────────────────────  │
│  PID          Process IDs (container sees PID 1)           │
│  NET          Network interfaces, IPs, ports               │
│  MNT          Filesystem mounts                             │
│  UTS          Hostname and domain                           │
│  IPC          Inter-process communication                   │
│  USER         User and group IDs                            │
│                                                             │
│  Result: Process thinks it's alone on the system            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Control Groups (Resource Limits)

cgroups limit how much resource a container can use:

```
Container A: max 512MB RAM, 0.5 CPU
Container B: max 1GB RAM, 1 CPU
Container C: max 256MB RAM, 0.25 CPU

Each container is limited, can't starve others
```

### 3. Union Filesystems (Layered Images)

Container images are built in layers:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER IMAGE LAYERS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────┐  ← Your app code  │
│  │ Layer 4: COPY app.py /app           │     (tiny)        │
│  ├─────────────────────────────────────┤                   │
│  │ Layer 3: pip install flask          │  ← Dependencies   │
│  ├─────────────────────────────────────┤     (cached)      │
│  │ Layer 2: apt-get install python3    │  ← Runtime        │
│  ├─────────────────────────────────────┤     (cached)      │
│  │ Layer 1: Ubuntu 22.04 base          │  ← Base OS        │
│  └─────────────────────────────────────┘     (shared)      │
│                                                             │
│  Benefits:                                                  │
│  - Layers are shared between images                        │
│  - Only changed layers need rebuilding                     │
│  - Efficient storage and transfer                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Container Images and Registries

### What's a Container Image?

A container image is a read-only template containing:
- A minimal operating system (often Alpine Linux, ~5MB)
- Your application code
- Dependencies (libraries, runtimes)
- Configuration

Think of it like a **class** in programming—it's the blueprint.

### What's a Container?

A container is a **running instance** of an image.

Think of it like an **object**—it's the instantiation.

```
Image → Container
(Class → Object)
(Blueprint → Building)
(Recipe → Meal)
```

### Container Registries

Images are stored in registries:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER REGISTRIES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Public Registries:                                        │
│  ┌────────────────────────────────────────────┐            │
│  │ Docker Hub        hub.docker.com           │            │
│  │ GitHub Container  ghcr.io                  │            │
│  │ Quay.io          quay.io                   │            │
│  └────────────────────────────────────────────┘            │
│                                                             │
│  Cloud Registries:                                         │
│  ┌────────────────────────────────────────────┐            │
│  │ AWS ECR          *.dkr.ecr.*.amazonaws.com │            │
│  │ Google GCR       gcr.io                    │            │
│  │ Azure ACR        *.azurecr.io              │            │
│  └────────────────────────────────────────────┘            │
│                                                             │
│  Usage:                                                     │
│  docker pull nginx              # From Docker Hub          │
│  docker pull gcr.io/project/app # From Google              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Image Naming

Container images have a specific naming format:

```
[registry/][namespace/]repository[:tag]

Examples:
nginx                           # Docker Hub, library/nginx:latest
nginx:1.25                      # Docker Hub, specific version
mycompany/myapp:v1.0.0         # Docker Hub, custom namespace
gcr.io/myproject/myapp:latest  # Google Container Registry
ghcr.io/username/app:sha-abc123 # GitHub Container Registry
```

### Tags Are Important

```
nginx:latest     # Whatever is newest (unpredictable!)
nginx:1.25       # Specific version (better)
nginx:1.25.3     # Exact version (best for production)

Rule: Never use :latest in production
```

---

## Did You Know?

- **Containers aren't new.** Unix had chroot in 1979. FreeBSD Jails came in 2000. Linux Containers (LXC) in 2008. Docker just made it accessible (2013).

- **Most containers use Alpine Linux** as their base. It's only 5MB. Compare to Ubuntu (~70MB) or a full VM (gigabytes).

- **Container images are immutable.** Once built, they never change. This is key to reproducibility.

- **The Docker whale** is named Moby Dock. The whale carries containers (shipping containers) on its back.

---

## Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "Containers are lightweight VMs" | Containers share the host kernel. VMs have their own kernel. Fundamentally different. |
| "Containers are less secure" | Different threat model, not worse. Properly configured containers are very secure. |
| "Docker equals containers" | Docker popularized containers but isn't the only option. containerd, CRI-O, Podman all work. |
| "Containers replace VMs entirely" | VMs still valuable for different OS kernels, strong isolation, legacy apps. |

---

## The Analogy: Shipping Containers

The name "container" comes from shipping containers:

```
Before Shipping Containers (1950s):
- Each product packed differently
- Manual loading/unloading
- Products damaged in transit
- Ships specialized for cargo types
- Slow, expensive, unreliable

After Shipping Containers:
- Standard size for everything
- Automated loading/unloading
- Protected contents
- Any ship can carry any container
- Fast, cheap, reliable

Software Containers:
- Standard format for any application
- Automated deployment
- Protected from environment differences
- Runs anywhere containers run
- Fast, portable, reliable
```

---

## Quiz

1. **What problem do containers primarily solve?**
   <details>
   <summary>Answer</summary>
   Environment consistency—ensuring applications run the same way across development, testing, and production environments. "It works on my machine" becomes "it works in the container."
   </details>

2. **What's the key difference between a container and a virtual machine?**
   <details>
   <summary>Answer</summary>
   Containers share the host operating system kernel, while VMs have their own guest OS. This makes containers much smaller (MB vs GB), faster to start (seconds vs minutes), and more efficient (higher density per server).
   </details>

3. **What are the two Linux kernel features that enable containers?**
   <details>
   <summary>Answer</summary>
   Namespaces (for isolation—making processes think they have their own system) and Control Groups/cgroups (for resource limits—controlling CPU, memory, etc.).
   </details>

4. **What's the difference between a container image and a container?**
   <details>
   <summary>Answer</summary>
   An image is a read-only template (like a class or blueprint). A container is a running instance of an image (like an object or building). You can run multiple containers from one image.
   </details>

---

## Hands-On Exercise

**Task**: Explore container isolation (if you have Docker installed).

```bash
# 1. Run a container and explore its isolated view
docker run -it --rm alpine sh

# Inside the container, you'll see:
# - PID 1 is your shell (isolated PID namespace)
# - Only the container's filesystem (isolated mount namespace)
# - Its own hostname (isolated UTS namespace)

# Check processes - you only see container processes
ps aux

# Check hostname
hostname

# Check filesystem
ls /

# Exit the container
exit

# 2. Compare with your host
# On your host, run:
ps aux | wc -l    # Hundreds/thousands of processes
hostname          # Your machine's name
ls /              # Full host filesystem

# 3. See the container from outside
# In one terminal, run a container:
docker run -it --rm --name mycontainer alpine sleep 1000

# In another terminal, see it from host perspective:
docker exec mycontainer ps aux  # Limited view inside
ps aux | grep sleep             # Visible from host!

# The container thinks it's alone, but it's just isolated.
```

**Success criteria**: Understand that containers provide isolation, not virtualization—processes still run on the host kernel.

---

## Summary

Containers solve the environment consistency problem by packaging:
- Application code
- Dependencies
- Configuration
- Everything needed to run

They achieve this through:
- **Namespaces**: Process isolation
- **Control groups**: Resource limits
- **Union filesystems**: Efficient layered images

Containers are:
- **Lightweight**: Megabytes, not gigabytes
- **Fast**: Seconds to start, not minutes
- **Portable**: Run anywhere containers run
- **Immutable**: Built once, unchanged

---

## Next Module

[Module 2: Docker Fundamentals](module-1.2-docker-fundamentals/) - Hands-on with building and running containers.
