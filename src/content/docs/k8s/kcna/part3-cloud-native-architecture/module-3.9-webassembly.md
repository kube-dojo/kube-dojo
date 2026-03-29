---
title: "Module 3.9: WebAssembly and Cloud Native"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.9-webassembly
sidebar:
  order: 10
---
> **Complexity**: `[MEDIUM]` - Conceptual awareness
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles), Module 3.3 (Cloud Native Patterns)

---

## Why This Module Matters

WebAssembly (Wasm) is the most significant new runtime technology since containers. Originally built for browsers, it is now breaking into server-side and cloud native computing. Wasm workloads start in milliseconds, weigh kilobytes, and run in a secure sandbox. KCNA expects you to understand where Wasm fits in the cloud native landscape and how it relates to containers.

> *"If WASM+WASI existed in 2008, we wouldn't have needed to create Docker."*
> — **Solomon Hykes**, co-founder of Docker (2019)

That quote shook the container world. It does not mean containers are going away — it means Wasm solves some of the same problems, sometimes better.

---

## What is WebAssembly?

```
┌─────────────────────────────────────────────────────────────┐
│              WEBASSEMBLY (WASM)                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Portable, compact BYTECODE format                         │
│                                                             │
│  Originally: Run near-native code in web browsers          │
│  Now:        Run anywhere — servers, edge, IoT, cloud      │
│                                                             │
│  Key Properties:                                            │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  PORTABLE    Compile once, run on any Wasm runtime          │
│              (like Java bytecode, but lighter)              │
│                                                             │
│  FAST        Near-native execution speed                    │
│              Millisecond cold starts (not seconds)          │
│                                                             │
│  SECURE      Sandboxed by default — no file/network         │
│              access unless explicitly granted               │
│                                                             │
│  COMPACT     Binaries measured in KB, not MB or GB          │
│                                                             │
│  POLYGLOT    Compile from Rust, Go, C/C++, Python,          │
│              JavaScript, and more                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### WASI: The System Interface

Wasm in the browser can talk to the DOM. But on a server, it needs access to files, network, clocks, and environment variables. That is what **WASI** (WebAssembly System Interface) provides.

Think of WASI as "POSIX for Wasm" — a standard interface between Wasm modules and the host operating system, but with a capability-based security model where each permission is explicitly granted.

```
┌─────────────────────────────────────────────────────────────┐
│  Your Code (Rust, Go, etc.)                                 │
│       │                                                     │
│       ▼  compile                                            │
│  Wasm Binary (.wasm)                                        │
│       │                                                     │
│       ▼  runs on                                            │
│  Wasm Runtime (WasmEdge, Wasmtime, etc.)                    │
│       │                                                     │
│       ▼  talks to OS via                                    │
│  WASI (file access, network, env vars)                      │
│       │                                                     │
│       ▼                                                     │
│  Host Operating System                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Wasm vs Containers

This is the comparison KCNA is most likely to test. Know the trade-offs.

| Aspect | Containers (OCI) | WebAssembly |
|--------|-------------------|-------------|
| **Startup time** | Seconds | Milliseconds |
| **Binary size** | MBs to GBs | KBs to low MBs |
| **Security model** | Shares host kernel, needs isolation layers | Sandboxed by default, capability-based |
| **Portability** | Runs on same OS/arch (or multi-arch builds) | True "compile once, run anywhere" |
| **Ecosystem maturity** | Very mature — huge library of images | Early stage — growing fast |
| **Language support** | Any language (full OS in container) | Growing but not all languages supported well |
| **System access** | Full (unless restricted) | Explicitly granted via WASI |
| **Use cases** | General-purpose applications | Functions, edge, plugins, lightweight services |
| **Orchestration** | Kubernetes, Docker Swarm | Emerging (SpinKube, runwasi) |

```
┌─────────────────────────────────────────────────────────────┐
│              STARTUP TIME COMPARISON                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Container:  ████████████████████████████████  ~1-5 seconds │
│  Wasm:       ██                                ~1-5 ms     │
│                                                             │
│  IMAGE SIZE COMPARISON                                      │
│  ─────────────────────────────────────────────────────────  │
│  Container:  ████████████████████████████████  50-500 MB    │
│  Wasm:       █                                 0.1-5 MB     │
│                                                             │
│  This matters for:                                          │
│  • Serverless (cold start penalty)                         │
│  • Edge computing (limited storage/bandwidth)              │
│  • Scale-to-zero (restart cost must be low)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Key insight for KCNA**: Wasm does not replace containers. They are complementary. Use containers for complex, full-featured applications. Use Wasm where startup speed, size, and sandboxing matter most.

---

## Wasm Runtimes

A Wasm runtime executes .wasm binaries, similar to how a container runtime (containerd, CRI-O) runs container images.

| Runtime | Key Characteristics |
|---------|---------------------|
| **Wasmtime** | Reference implementation by Bytecode Alliance; production-grade, standards-focused |
| **WasmEdge** | CNCF Sandbox project; optimized for edge and cloud native; supports networking and AI extensions |
| **Spin** | Developer framework by Fermyon; build and run serverless Wasm apps easily |
| **wasmCloud** | CNCF Sandbox project; distributed platform for building Wasm applications with a component model |

> **For KCNA**: Know that WasmEdge and wasmCloud are CNCF projects. You do not need to know runtime internals.

---

## Wasm on Kubernetes

Running Wasm workloads on Kubernetes is possible today through containerd shims — the same interface containers use.

```
┌─────────────────────────────────────────────────────────────┐
│              WASM ON KUBERNETES                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  How containers run on K8s:                                 │
│  ─────────────────────────────────────────────────────────  │
│  kubelet → containerd → runc → Linux container             │
│                                                             │
│  How Wasm runs on K8s:                                      │
│  ─────────────────────────────────────────────────────────  │
│  kubelet → containerd → runwasi → Wasm runtime             │
│                                                             │
│  Same kubelet, same containerd, different shim!            │
│                                                             │
│  Key Projects:                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  runwasi     containerd shim that runs Wasm instead of     │
│              Linux containers. Drop-in replacement for runc │
│                                                             │
│  SpinKube    Run Spin (Wasm) apps on Kubernetes using       │
│              custom resources. Manages Wasm apps like K8s  │
│              manages containers                             │
│                                                             │
│  Both use RuntimeClass to tell K8s "this Pod runs Wasm"    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### RuntimeClass: The Bridge

Kubernetes uses **RuntimeClass** to select which runtime handles a Pod. A cluster can run both container Pods and Wasm Pods side by side:

```
┌──────────────────────────────────────────┐
│           Kubernetes Cluster              │
│                                          │
│  ┌──────────────┐  ┌──────────────┐      │
│  │ Container Pod │  │   Wasm Pod   │      │
│  │ runtimeClass: │  │ runtimeClass:│      │
│  │   (default)   │  │   wasmtime   │      │
│  │               │  │              │      │
│  │  containerd   │  │  containerd  │      │
│  │  → runc       │  │  → runwasi   │      │
│  │  → Linux      │  │  → Wasmtime  │      │
│  └──────────────┘  └──────────────┘      │
│                                          │
└──────────────────────────────────────────┘
```

---

## When to Use Wasm

### Good Fit

| Use Case | Why Wasm Excels |
|----------|-----------------|
| **Serverless functions** | Millisecond cold starts make scale-to-zero practical |
| **Edge computing** | Tiny binaries, low resource requirements, runs on constrained devices |
| **Plugin systems** | Safe sandboxing — plugins cannot access host unless permitted |
| **Short-lived request handlers** | No startup penalty, minimal overhead |
| **Multi-tenant isolation** | Each Wasm module is sandboxed without needing full container isolation |

### Not a Good Fit (Yet)

| Use Case | Why Containers Are Better |
|----------|--------------------------|
| **Complex applications** | Full OS libraries, mature debugging tools, broad language support |
| **Database servers** | Need direct hardware access, complex system calls |
| **Apps needing mature ecosystem** | Container images exist for almost everything; Wasm ecosystem is still growing |
| **Heavy I/O workloads** | WASI I/O is still maturing compared to native Linux I/O |
| **Legacy applications** | Recompiling to Wasm is non-trivial for large codebases |

---

## The Component Model

The **Wasm Component Model** is an emerging standard that lets Wasm modules compose together, regardless of the language they were written in:

```
┌─────────────────────────────────────────────────────────────┐
│  Rust component ──┐                                         │
│                   ├──→ Composed application                 │
│  Go component ────┤    (linked at the Wasm level,          │
│                   │     not at the OS/container level)      │
│  JS component ────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

This is still early, but it represents a fundamentally different approach to building distributed systems — composing at the module level rather than the container level.

---

## Did You Know?

- **All major browsers ship a Wasm runtime** — Chrome, Firefox, Safari, and Edge all run Wasm natively. It is the fourth official web language alongside HTML, CSS, and JavaScript. This browser heritage is why Wasm is so portable and secure — it was designed to run untrusted code safely.

- **Wasm binaries are architecture-neutral** — Unlike container images that need separate builds for amd64 and arm64, a single .wasm file runs on any architecture. No multi-arch builds, no platform-specific images. This is especially valuable for edge computing where you might deploy to x86 servers, ARM devices, and RISC-V boards.

- **Fermyon ran 5,000 Wasm apps on a single node** — In benchmarks, a single Kubernetes node ran thousands of Wasm microservices simultaneously, compared to dozens of containers. The tiny footprint and fast startup make density dramatically higher.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "Wasm replaces containers" | Leads to wrong architectural decisions | Wasm complements containers — use each where it fits best |
| "Wasm is only for browsers" | Misses the server-side revolution | WASI enables Wasm to run anywhere: servers, edge, cloud, IoT |
| Thinking any app can be compiled to Wasm | Not all languages/libraries support Wasm well yet | Rust and Go have good support; complex C++ apps with many system calls are harder |
| Ignoring the ecosystem gap | Building on immature tooling causes pain | Container ecosystem (images, registries, debugging) is far more mature today |
| Confusing Wasm runtimes with container runtimes | They solve different problems | Wasm runtimes (Wasmtime, WasmEdge) execute .wasm bytecode; container runtimes (runc, crun) manage Linux namespaces/cgroups |

---

## Quiz

**1. What was WebAssembly originally designed for?**

A) Replacing Docker containers
B) Running near-native code in web browsers
C) GPU computing
D) Database query optimization

<details>
<summary>Answer</summary>

**B) Running near-native code in web browsers.** Wasm was created to run performance-sensitive code (like games and video editing) in browsers at near-native speed. Its use in server-side and cloud native computing came later.
</details>

**2. What is WASI?**

A) A Wasm-based container image format
B) A web framework for building Wasm apps
C) A system interface that lets Wasm modules access host resources like files and network
D) A Kubernetes controller for Wasm workloads

<details>
<summary>Answer</summary>

**C) A system interface that lets Wasm modules access host resources like files and network.** WASI (WebAssembly System Interface) is the standard API between Wasm modules and the operating system, using a capability-based security model.
</details>

**3. How does Kubernetes run Wasm workloads alongside containers?**

A) A separate Wasm cluster is required
B) Using runwasi as a containerd shim, selected via RuntimeClass
C) Wasm Pods replace all container Pods on a node
D) By converting Wasm to container images first

<details>
<summary>Answer</summary>

**B) Using runwasi as a containerd shim, selected via RuntimeClass.** runwasi plugs into containerd just like runc does for containers. RuntimeClass tells Kubernetes which runtime to use for each Pod, so containers and Wasm run side by side on the same cluster.
</details>

**4. Which of the following is a CNCF project in the WebAssembly space?**

A) Wasmtime
B) Spin
C) WasmEdge
D) Docker

<details>
<summary>Answer</summary>

**C) WasmEdge.** WasmEdge is a CNCF Sandbox project optimized for edge and cloud native use cases. Wasmtime is a Bytecode Alliance project. Spin is by Fermyon. wasmCloud is also a CNCF Sandbox project.
</details>

**5. What is the biggest advantage of Wasm over containers for serverless functions?**

A) Better language support
B) Millisecond cold start times vs seconds for containers
C) More mature ecosystem
D) Built-in database support

<details>
<summary>Answer</summary>

**B) Millisecond cold start times vs seconds for containers.** Serverless functions that scale to zero need to start quickly when a request arrives. Wasm modules start in 1-5 milliseconds compared to 1-5 seconds for containers, eliminating the cold start penalty.
</details>

**6. Which statement best describes the relationship between Wasm and containers?**

A) Wasm will replace containers within 5 years
B) Containers are always better than Wasm
C) They are complementary — each excels at different use cases
D) Wasm is just a container image format

<details>
<summary>Answer</summary>

**C) They are complementary — each excels at different use cases.** Containers are mature and work for almost anything. Wasm excels where fast startup, small size, and strong sandboxing matter (serverless, edge, plugins). Most organizations will use both.
</details>

---

## Summary

- **WebAssembly** is a portable bytecode format — originally for browsers, now expanding to server-side and cloud native
- **WASI** provides system access (files, network) with capability-based security
- Wasm vs containers: **faster startup** (ms vs s), **smaller** (KB vs MB), **sandboxed by default** — but less mature ecosystem
- **Wasm runtimes**: Wasmtime, WasmEdge (CNCF), Spin, wasmCloud (CNCF)
- **Wasm on K8s**: runwasi shim + RuntimeClass lets Wasm and containers coexist
- **Best for**: serverless, edge, plugins, multi-tenant isolation
- **Not ready for**: complex apps, heavy I/O, legacy migrations
- Wasm complements containers — it does not replace them

---

## Next Module

[Module 3.10: Green Computing and Sustainability](../module-3.10-green-computing/) - How cloud native practices intersect with environmental sustainability and carbon-aware computing.
