---
title: "Module 1.2: Container Fundamentals"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.2-container-fundamentals
sidebar:
  order: 3
---
> **Complexity**: `[QUICK]` - Foundational concepts
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 1.1

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** what containers are and how they differ from virtual machines
2. **Identify** the Linux kernel features (namespaces, cgroups) that enable container isolation
3. **Compare** container runtimes (Docker, containerd, CRI-O) and their roles in Kubernetes
4. **Explain** the OCI image and runtime specifications and why they matter for portability

---

## Why This Module Matters

You can't understand Kubernetes without understanding containers. KCNA tests your knowledge of container concepts—not how to build Dockerfiles, but what containers are and how they work.

---

## What is a Container?

A container is a **lightweight, standalone, executable package** that includes everything needed to run a piece of software:

```
┌─────────────────────────────────────────────────────────────┐
│              WHAT'S INSIDE A CONTAINER                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    CONTAINER                         │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Application Code                            │    │   │
│  │  │  (your app, scripts, binaries)              │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Dependencies                                │    │   │
│  │  │  (libraries, packages, frameworks)          │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Runtime                                     │    │   │
│  │  │  (Python, Node.js, Java JVM, etc.)          │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  System Tools & Libraries                    │    │   │
│  │  │  (minimal OS userspace)                     │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  NOT included: Kernel (shared with host)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Containers vs Virtual Machines

```
┌─────────────────────────────────────────────────────────────┐
│         VIRTUAL MACHINES vs CONTAINERS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VIRTUAL MACHINES                    CONTAINERS             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────┐ ┌─────┐ ┌─────┐          ┌─────┐ ┌─────┐ ┌─────┐ │
│  │App A│ │App B│ │App C│          │App A│ │App B│ │App C│ │
│  ├─────┤ ├─────┤ ├─────┤          ├─────┤ ├─────┤ ├─────┤ │
│  │Bins │ │Bins │ │Bins │          │Bins │ │Bins │ │Bins │ │
│  │Libs │ │Libs │ │Libs │          │Libs │ │Libs │ │Libs │ │
│  ├─────┤ ├─────┤ ├─────┤          └──┬──┘ └──┬──┘ └──┬──┘ │
│  │Guest│ │Guest│ │Guest│             │       │       │     │
│  │ OS  │ │ OS  │ │ OS  │             │       │       │     │
│  └──┬──┘ └──┬──┘ └──┬──┘             └───────┼───────┘     │
│     └───────┼───────┘                        │             │
│             │                        ┌───────┴───────┐     │
│     ┌───────┴───────┐                │Container      │     │
│     │  Hypervisor   │                │Runtime        │     │
│     └───────┬───────┘                └───────┬───────┘     │
│             │                                │             │
│     ┌───────┴───────┐                ┌───────┴───────┐     │
│     │   Host OS     │                │   Host OS     │     │
│     └───────┬───────┘                └───────┬───────┘     │
│             │                                │             │
│     ┌───────┴───────┐                ┌───────┴───────┐     │
│     │   Hardware    │                │   Hardware    │     │
│     └───────────────┘                └───────────────┘     │
│                                                             │
│  Each VM has full OS                 Containers share      │
│  (heavy, slow to start)             host kernel (light)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Comparison Table

| Aspect | Virtual Machine | Container |
|--------|-----------------|-----------|
| **Size** | GBs | MBs |
| **Startup** | Minutes | Seconds |
| **Isolation** | Strong (separate kernel) | Process-level (shared kernel) |
| **Overhead** | High | Low |
| **Density** | ~10s per host | ~100s per host |
| **Portability** | Medium | High |

---

## How Containers Work

Containers use Linux kernel features:

### 1. Namespaces (Isolation)

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX NAMESPACES                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Namespace     What It Isolates                            │
│  ─────────────────────────────────────────────────────────  │
│  PID           Process IDs (container sees own PIDs)       │
│  Network       Network interfaces, IPs, ports              │
│  Mount         Filesystem mounts                           │
│  UTS           Hostname and domain name                    │
│  IPC           Inter-process communication                 │
│  User          User and group IDs                          │
│                                                             │
│  Each container gets its own namespaces                    │
│  → Appears to have its own isolated system                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: If containers share the host kernel (unlike VMs which have their own), what security implications does this have? What happens if a container exploits a kernel vulnerability?

### 2. Cgroups (Resource Limits)

```
┌─────────────────────────────────────────────────────────────┐
│              CONTROL GROUPS (cgroups)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cgroups limit and track resources:                        │
│                                                             │
│  CPU:      "Container A gets max 2 cores"                  │
│  Memory:   "Container B gets max 512MB"                    │
│  Disk I/O: "Container C gets max 100MB/s"                  │
│  Network:  "Container D gets max 100Mbps"                  │
│                                                             │
│  Without cgroups:                                          │
│  One container could consume ALL resources                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Union Filesystems (Layers)

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER IMAGE LAYERS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Container Image (read-only layers):                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 4: Application code       (your app)         │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Layer 3: Dependencies           (npm packages)     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Layer 2: Runtime                (Node.js)          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Layer 1: Base OS                (Ubuntu slim)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Running Container adds:                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Writable layer  (runtime changes, logs, temp files)│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Benefits:                                                 │
│  • Layers are cached and reused                           │
│  • Multiple containers share base layers                  │
│  • Efficient storage and transfer                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Container Images

### What is an Image?

An **image** is a read-only template used to create containers:

| Concept | Analogy |
|---------|---------|
| Image | Recipe / Blueprint |
| Container | Cake / Building |

### Image Naming Convention

```
registry/repository:tag

Examples:
docker.io/library/nginx:1.25
gcr.io/google-containers/pause:3.9
mycompany.com/myapp:v2.1.0

Parts:
• registry:    Where image is stored (docker.io, gcr.io)
• repository:  Name of the image (nginx, myapp)
• tag:         Version identifier (1.25, latest, v2.1.0)
```

### Image Registries

| Registry | Description |
|----------|-------------|
| Docker Hub | Default public registry |
| gcr.io | Google Container Registry |
| ECR | Amazon Elastic Container Registry |
| ACR | Azure Container Registry |
| Quay.io | Red Hat registry |

---

> **Stop and think**: Docker was deprecated as a Kubernetes runtime in version 1.24. If Docker is the most popular container tool, why would Kubernetes drop support for it? What does Kubernetes actually need from a runtime?

## Container Runtimes

Kubernetes doesn't run containers directly—it uses a **container runtime**:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER RUNTIME INTERFACE (CRI)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Kubernetes                               │
│                         │                                   │
│                         │ CRI (standard interface)          │
│                         │                                   │
│         ┌───────────────┼───────────────┐                  │
│         │               │               │                   │
│         ▼               ▼               ▼                   │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│   │containerd│   │  CRI-O   │   │  Docker  │              │
│   │          │   │          │   │(via shim)│              │
│   └──────────┘   └──────────┘   └──────────┘              │
│                                                             │
│  containerd: Default in most K8s distributions            │
│  CRI-O:      Lightweight, Kubernetes-focused              │
│  Docker:     Deprecated in K8s 1.24+                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key point for KCNA**: Kubernetes uses CRI to talk to container runtimes. The most common runtime is containerd.

---

## Container Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER LIFECYCLE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Pull Image                                             │
│     Download image from registry                           │
│                    │                                        │
│                    ▼                                        │
│  2. Create Container                                       │
│     Prepare filesystem, namespaces, cgroups               │
│                    │                                        │
│                    ▼                                        │
│  3. Start Container                                        │
│     Execute the container's entry point                   │
│                    │                                        │
│                    ▼                                        │
│  4. Running                                                │
│     Container is executing                                 │
│                    │                                        │
│         ┌─────────┴─────────┐                              │
│         │                   │                               │
│         ▼                   ▼                               │
│  5a. Stop              5b. Crash                          │
│      Graceful              Unexpected                      │
│      shutdown              termination                     │
│         │                   │                               │
│         └─────────┬─────────┘                              │
│                   │                                         │
│                   ▼                                         │
│  6. Remove Container                                       │
│     Clean up resources                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Hands-On Exercise: Container Inspection

In this exercise, you will interact with a container runtime to understand isolation and image layers. You can use Docker or containerd (`nerdctl`) if installed on your local machine.

**Step 1: Run a Simple Container**
Start an interactive Alpine Linux container:
```bash
docker run -it alpine sh
```

**Step 2: Observe Process Isolation (Namespaces)**
Inside the container, list the running processes:
```bash
ps aux
```
*Notice that the shell (`sh`) is PID 1. You cannot see the processes running on your host machine due to PID namespace isolation.*

**Step 3: Exit and Observe Container State**
Type `exit` to leave the container. Check if it's still running:
```bash
docker ps -a
```
*The container is in an 'Exited' state because its main process (PID 1) terminated.*

**Step 4: Explore Image Layers**
Pull an image and inspect its layers:
```bash
docker pull nginx:latest
docker image inspect nginx:latest | grep -A 10 "Layers"
```
*You will see multiple SHA256 hashes, each representing a read-only filesystem layer within the union filesystem.*

**Success Criteria:**
- [ ] You successfully started an interactive container.
- [ ] You verified that the container has its own isolated process tree (PID 1).
- [ ] You inspected an image to see its composed layers.

---

## War Story: The "Noisy Neighbor" Outage

A financial services company migrated their monolithic application to containers but failed to set resource limits. During a high-traffic event, a minor memory leak in a reporting container caused it to consume 100% of the host node's RAM. Because no cgroup limits were applied, this single container starved the host's operating system and all other critical containers running on the same node. The entire node crashed, triggering a cascading failure across the cluster. This outage highlighted a painful lesson: while containers provide namespace isolation out of the box, you must explicitly configure cgroup limits to prevent noisy neighbors from hoarding shared kernel resources.

---

## Operational Lessons

- **Set Resource Requests and Limits:** Always define CPU and memory limits (using cgroups) for every container to ensure predictable performance and fair resource sharing.
- **Use Immutable Tags:** Never use the `latest` tag in production environments. Always pin to specific, immutable versions (e.g., `v1.2.4`) to guarantee consistent and repeatable deployments.
- **Run as Non-Root:** By default, containers run as the root user. Always configure your containers to run as a non-privileged user to minimize the blast radius in the event of a security breach.

---

## Did You Know?

- **Containers aren't new** - The concepts date back to Unix chroot (1979) and FreeBSD jails (2000). Docker popularized them in 2013.
- **Docker isn't required for Kubernetes** - Since K8s 1.24, containerd is the default. Docker as a runtime is deprecated.
- **The OCI defines standards** - Open Container Initiative standardizes image formats and runtimes, ensuring portability.
- **Containers share the host kernel** - This is why Windows containers can't run on Linux and vice versa (without virtualization).

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "Containers are lightweight VMs" | Missing the architectural difference | Containers share kernel; VMs don't |
| "Each container has its own OS" | Wastes resources mentally | Containers share host kernel |
| "Docker = Containers" | Docker is just one runtime | containerd, CRI-O also run containers |
| "Images and containers are the same" | Confuses template vs instance | Image is template; container is running instance |
| Running containers as root by default | Expands the blast radius if the container is compromised | Always configure processes to run as a non-root user |
| Using the `latest` tag in production | Causes unpredictable deployments if the tag gets overwritten | Pin image versions using specific, immutable tags |
| Ignoring image layer ordering | Results in slow builds and wasted caching efficiency | Place frequently changing files (like app code) in the final layers |
| Not setting cgroup resource limits | Allows one noisy neighbor container to starve the host node | Always define CPU and memory limits to restrict resource usage |

---

## Quiz

1. **A developer says "containers are just lightweight VMs." How would you correct this misconception, and why does the distinction matter?**
   <details>
   <summary>Answer</summary>
   Containers and VMs have fundamentally different architectures. VMs include a full guest operating system and run on a hypervisor, providing strong isolation at the cost of heavy resource usage. Containers share the host kernel and use Linux namespaces and cgroups for isolation -- they are isolated processes, not virtual machines. This distinction matters because sharing the kernel means containers start in seconds (not minutes), use megabytes (not gigabytes), and you can run hundreds per host (not just tens). However, it also means containers have weaker isolation than VMs since a kernel vulnerability could affect all containers on the host.
   </details>

2. **Your team builds a container image on a developer's laptop using Docker. Can that same image run in a Kubernetes cluster that uses containerd instead of Docker? Why or why not?**
   <details>
   <summary>Answer</summary>
   Yes, the image will work. Container images follow the OCI (Open Container Initiative) standard, which defines a common image format. Docker, containerd, and CRI-O all understand OCI images. The image you build with Docker produces an OCI-compliant image that any compliant runtime can execute. This portability is one of the key benefits of container standardization -- you build once and run on any OCI-compatible runtime.
   </details>

3. **A container image has four layers: base OS, runtime, dependencies, and application code. If you update only your application code, what happens to the other three layers when you rebuild?**
   <details>
   <summary>Answer</summary>
   The other three layers are reused from cache. Container images use a union filesystem where each layer builds on the previous one. Only layers that change (and layers above them) need rebuilding. Since your application code is the top layer, the base OS, runtime, and dependency layers remain cached. This is why layer ordering matters in Dockerfiles -- put frequently-changing content in later layers. It also means that multiple containers sharing the same base layers on a node only store those layers once, saving disk space.
   </details>

4. **You learn that Kubernetes deprecated Docker as a runtime in version 1.24. A worried colleague asks if all their Docker-built images will stop working. What would you explain?**
   <details>
   <summary>Answer</summary>
   Their images will continue working perfectly. Kubernetes deprecated Docker as a container runtime (the component that runs containers), not Docker images. Docker images are OCI-standard images that containerd (the new default runtime) fully supports. What was removed was the "dockershim" -- a compatibility layer that let Kubernetes talk to Docker's API. Since containerd was always the component inside Docker that actually ran containers, removing Docker just removes an unnecessary middle layer. Images built with `docker build` work identically on containerd.
   </details>

5. **An organization needs strong security isolation between workloads from different customers on the same host. Would containers alone provide sufficient isolation? What alternative approach might they consider?**
   <details>
   <summary>Answer</summary>
   Containers alone may not provide sufficient isolation for multi-tenant workloads with strict security requirements. Since containers share the host kernel, a kernel vulnerability could allow one tenant's container to access another's data. For stronger isolation, the organization could consider: running containers inside lightweight VMs (like Kata Containers or Firecracker), using gVisor which interposes a user-space kernel between containers and the host, or using separate nodes per tenant. The choice depends on the security requirements versus the performance and cost trade-offs.
   </details>

6. **A new engineer notices that the application's container image uses the `latest` tag in the production deployment manifest. They argue this is good because the app will automatically get the newest security patches. Why is this practice dangerous in a production environment?**
   <details>
   <summary>Answer</summary>
   Using the `latest` tag in production is dangerous because it makes deployments unpredictable and non-reproducible. The `latest` tag is simply a mutable pointer that changes every time a new image is pushed without a specific tag. If a node fails and Kubernetes needs to reschedule the pod, it might pull a newer, untested version of the application that breaks compatibility or introduces bugs. Instead, production deployments should always use specific, immutable tags (like `v1.2.3`) or image digests to ensure that exactly the same code is running across all nodes and deployments.
   </details>

7. **During a security audit, the team discovers that their Node.js container is running its main process as the `root` user. The lead developer says this is fine because containers are isolated. Why is the security team still concerned, and what should be done?**
   <details>
   <summary>Answer</summary>
   The security team is concerned because containers share the underlying host's kernel and do not offer the same boundary as a virtual machine. While namespaces provide process isolation, a process running as root inside a container still possesses root-level privileges from the kernel's perspective. If an attacker exploits a vulnerability in the application and manages to break out of the container (known as a container escape), they would land on the host node as the root user, potentially taking over the entire machine. To mitigate this, containers should always be configured to run as a non-root, unprivileged user using the `USER` directive in the Dockerfile.
   </details>

8. **A cluster node crashes because a single container consumed all of the node's memory. Which underlying Linux kernel feature was not properly configured, and how does it prevent this scenario?**
   <details>
   <summary>Answer</summary>
   The cgroups (control groups) feature was not properly configured for this container. While namespaces isolate what a container can see, cgroups limit the physical resources (CPU, memory, disk I/O) a container is allowed to use. When resource limits are not set, a single "noisy neighbor" container can consume all available memory on the host, causing the host operating system to become unstable or crash. By setting memory and CPU limits, the kernel ensures the container is restricted to its allocated quota and gets terminated if it exceeds it, protecting the rest of the node.
   </details>

---

## Summary

**Containers are**:
- Lightweight, isolated processes
- Packaged with dependencies
- Created from images
- Share the host kernel

**Key technologies**:
- **Namespaces**: Process isolation
- **Cgroups**: Resource limits
- **Union filesystems**: Layered images

**Container runtimes**:
- containerd (default)
- CRI-O
- Docker (deprecated in K8s)

**Images vs Containers**:
- Image = read-only template
- Container = running instance

---

## Next Module

[Module 1.3: Kubernetes Architecture - Control Plane](../module-1.3-control-plane/) - Understanding the brain of Kubernetes.