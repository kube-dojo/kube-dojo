---
revision_pending: false
title: "Module 3.9: WebAssembly and Cloud Native"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.9-webassembly
sidebar:
  order: 10
---

# Module 3.9: WebAssembly and Cloud Native

> **Complexity**: `[MEDIUM]` - Runtime architecture and workload placement
>
> **Time to Complete**: 45-60 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles), Module 3.3 (Cloud Native Patterns), Module 3.6 (Security Basics)

## Learning Outcomes

After completing this module, you will be able to make defensible runtime decisions rather than repeat surface-level claims about WebAssembly. Each outcome below is tied to the teaching sections, the quiz scenarios, and the hands-on placement review so you can practice the same judgment KCNA expects from a cloud native practitioner.

1. **Compare** WebAssembly, WASI, and containers using startup behavior, artifact size, portability, and isolation tradeoffs.
2. **Design** a Kubernetes 1.35+ workload placement plan that uses `RuntimeClass` for Wasm where it fits and normal containers where they remain stronger.
3. **Evaluate** Wasm use cases such as serverless functions, edge services, plugin systems, and multi-tenant execution against operational constraints.
4. **Diagnose** migration risks caused by language support, filesystem access, networking maturity, observability, and debugging gaps.
5. **Implement** a local inspection workflow that documents runtime choice, verifies cluster objects with `k`, and records success criteria for a Wasm pilot.

## Why This Module Matters

During a checkout surge, a retail platform allowed merchants to run custom discount logic directly in the purchase path. The old design isolated that third-party code with heavyweight service boundaries, so every checkout carried extra network hops, capacity planning, and failure modes. When the company moved that extension model to WebAssembly, the engineering problem changed: instead of provisioning separate services for each merchant script, the platform could execute small, sandboxed modules synchronously inside a strict runtime with predictable latency. That kind of redesign is not a small optimization; at the scale of online commerce, shaving tens of milliseconds from a critical path can protect conversion rate, infrastructure cost, and customer trust at the same time.

Cloud native teams are now facing the same architectural question in smaller forms. They already know how to package applications as OCI images, deploy Pods, and let Kubernetes schedule containers, but some workloads feel awkward inside that model. A function that runs for a few milliseconds does not need a full Linux userspace. A customer-supplied plugin should not inherit broad filesystem and network access. An edge node with limited storage should not pull hundreds of megabytes when the useful code is a tiny parser. WebAssembly, usually shortened to Wasm, gives platform teams another runtime shape for those cases, and KCNA expects you to know where that shape fits.

This module treats Wasm as a cloud native runtime choice rather than a trend to memorize. You will compare Wasm with containers, trace how WASI gives server-side modules controlled access to host capabilities, examine how Kubernetes can dispatch Wasm workloads through `containerd` shims and `RuntimeClass`, and practice deciding when a Wasm pilot is worth the operational cost. All Kubernetes examples assume Kubernetes 1.35 or newer. When a command uses kubectl, run `alias k=kubectl` once in your shell and then use the shorter `k` form consistently, because the same habit keeps operational runbooks concise.

```bash
alias k=kubectl
k version --client=true
```

## What WebAssembly Changes About Runtime Design

WebAssembly is a portable bytecode format, which means it is not a container image, a programming language, or a Kubernetes feature by itself. Developers compile source code from languages such as Rust, C, C++, TinyGo, or AssemblyScript into a `.wasm` artifact, and a Wasm runtime executes that artifact inside a sandbox. The easiest analogy is a shipping container versus a sealed instrument cartridge. A Linux container carries an application together with a filesystem layout, shared libraries, process assumptions, and a specific operating-system personality. A Wasm module carries a compact instruction format and asks the host runtime for only the capabilities it needs.

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

The original browser use case explains a lot about the server-side value. Browsers routinely execute code from strangers, so the runtime had to assume hostile input, strict boundaries, and rapid startup from the beginning. When cloud platforms adopted the same execution model outside the browser, they inherited those useful defaults. A Wasm module cannot casually inspect host files, open arbitrary sockets, or fork a process unless the host exposes those abilities. That default-deny posture is why Wasm is attractive for plugin systems and multi-tenant platforms, but it is also why some normal server applications become painful to port.

WASI, the WebAssembly System Interface, is the bridge between the sealed module and the host environment. Browser Wasm can call browser APIs such as the DOM through JavaScript integration, but server-side Wasm needs clocks, files, standard streams, environment variables, random numbers, and eventually richer networking. WASI defines standardized host calls for those needs while keeping permissions explicit. Instead of mounting an entire filesystem because an application might read one configuration file, a runtime can grant a pre-opened directory or a specific environment value, and the module stays unable to wander beyond that grant.

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

That capability model changes how you reason about application boundaries. In a container, you usually start broad and then restrict with seccomp, AppArmor, SELinux, read-only filesystems, dropped Linux capabilities, and network policy. In Wasm, the runtime starts with a smaller surface and grants capabilities deliberately. This does not make Wasm magically secure, because buggy host functions, vulnerable runtimes, and unsafe embedding code can still create serious exposure. It does mean the default mental model is different: a Wasm module should be treated like a function asking for named handles, not like a process that begins with broad operating-system expectations.

Pause and predict: if a module is allowed to write only to `/tmp/output` through a WASI pre-opened directory, what should happen when the same code tries to read `/etc/passwd` or open a random network connection? The important answer is not merely "it fails." The useful operational answer is that the runtime should deny the call because the host never granted that capability, and your observability should make the denied operation visible enough to debug without broadening permissions blindly.

The strongest Wasm candidates are small, stateless, and written in languages with mature Wasm toolchains. Rust is common because it compiles efficiently to Wasm and gives precise control over dependencies. TinyGo is practical for many Go-shaped functions, although standard Go can produce larger artifacts because of runtime assumptions. C and C++ can work well for libraries, but system-call-heavy programs can be hard to port. Interpreted languages can run through embedded interpreters, but that often erodes the size and startup benefits that motivated Wasm in the first place.

A useful worked example is a tax-calculation function in an e-commerce checkout. The function receives a postal code and cart total, reads a small rules table, returns a number, and should not access the network or inspect customer records beyond its input. That shape maps naturally to Wasm because the execution is short, the dependency graph is small, and the platform benefits from sandboxing merchant-specific logic. The same platform's payment ledger, database migrations, and fraud-analysis service are different shapes. They need mature storage, observability, network behavior, and language ecosystems, so containers remain the conservative choice.

Solomon Hykes, Docker's co-founder, famously wrote in 2019 that if WASM and WASI had existed in 2008, Docker might not have needed to be created. Treat that quote as a provocation, not a migration plan. Docker and Kubernetes solved packaging, distribution, orchestration, networking, and operational workflow problems for full applications. Wasm solves a narrower runtime problem exceptionally well in certain places. The architect's job is to recognize those places without turning every workload decision into a referendum on containers.

## Wasm and Containers Are Complementary, Not Replacements

KCNA candidates often get tested on the comparison between Wasm and containers because the two technologies sit near the same decision point: how should code be packaged and isolated before it runs? Containers package a process with its filesystem dependencies and rely on the host kernel for isolation primitives such as namespaces and cgroups. Wasm packages instructions for a virtual machine and relies on a runtime sandbox plus explicit host capabilities. Both can be deployed in cloud native systems, but they optimize for different costs.

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

Startup time is the easiest advantage to remember, but it is not always the deciding factor. A service that runs continuously for weeks does not care much whether startup takes ten milliseconds or four seconds. A scale-to-zero function, a request-scoped plugin, or an edge handler does care because every cold start lands on a user-facing path. That is why a simple comparison table must be connected to workload behavior. You evaluate Wasm by asking how frequently code starts, how long it runs, how much dependency weight it carries, and whether the sandbox boundary maps to a real risk.

Artifact size matters in the same contextual way. A 300 MB image is not automatically wrong if it contains a JVM service with mature debugging and a predictable release process. The same image size is wasteful if the useful logic is a tiny string parser shipped to thousands of edge locations over constrained links. Wasm's compact artifacts make distribution cheaper and faster, especially where network bandwidth, storage, and update windows are limited. The tradeoff is that you may spend engineering time slimming dependencies, changing libraries, or choosing a language subset that compiles well.

Security isolation is also more nuanced than a slogan. Containers share the host kernel, so a hardened container environment depends on kernel isolation, runtime configuration, image hygiene, admission policy, and workload identity. Wasm modules run inside a language-neutral sandbox that denies host access unless the runtime grants it. That can be a stronger default for untrusted plugins, but the platform still needs supply-chain controls, runtime patching, tenant separation, resource limits, and logs. A sandbox reduces one class of risk; it does not remove the need for platform engineering discipline.

Before running a pilot, ask which failure mode you are trying to improve. If the pain is slow scale-to-zero startup, Wasm may be a strong candidate. If the pain is large image distribution to edge nodes, Wasm may help. If the pain is that a legacy service has too many operating-system dependencies, Wasm may make the problem harder because those dependencies need to be removed or replaced. This is where the complementary model matters: Kubernetes can run normal Pods for the broad application estate and Wasm workloads for the narrower functions that benefit from a compact sandbox.

Consider five workload choices. A massive Java Spring Boot monolith connected to an Oracle database belongs in a container because the JVM, drivers, operational tooling, and database transaction behavior already fit the container ecosystem. A lightweight image-resizing function that executes thousands of times per second and scales to zero when idle is a Wasm candidate because cold starts and artifact size dominate. A multi-tenant SaaS platform running untrusted customer code is also a Wasm candidate because default-deny capabilities matter. A PostgreSQL database remains a container or VM workload because storage and kernel behavior are central. A tiny data parser on a constrained edge network can justify Wasm because distribution weight and portability are decisive.

Which approach would you choose here and why: a fraud-scoring service written in Python loads a large native machine-learning library, serves long-running HTTP requests, and needs GPU access on selected nodes? The practical answer is containers, even if the request handler itself is small. GPU integration, native dependencies, Python packaging, and observability are already mature in the container path. Choosing Wasm only because one part of the system is "function-like" would move complexity from runtime overhead into unsupported tooling.

The war story pattern is familiar in platform teams. A small innovation group proves a Wasm function is fast, then leadership asks whether all services should migrate. The correct response is a portfolio analysis, not enthusiasm or dismissal. List each service by startup sensitivity, artifact size, tenant trust boundary, dependency complexity, statefulness, and debugging expectations. The result is usually a hybrid plan: a few request-scoped or edge functions move first, plugin execution becomes safer, and the majority of existing services stay in containers until a concrete constraint justifies change.

## WASI, Runtimes, and the Cloud Native Ecosystem

A Wasm runtime executes `.wasm` binaries in the same broad sense that a container runtime executes container workloads, but the internal contract is different. Container runtimes such as `runc` and `crun` create Linux processes with namespace and cgroup isolation. Wasm runtimes such as Wasmtime and WasmEdge validate bytecode, compile or interpret it, provide memory isolation, and expose selected host functions. Frameworks such as Spin and platforms such as wasmCloud then add developer workflow, distribution, service invocation, and higher-level application patterns around that runtime core.

| Runtime | Key Characteristics |
|---------|---------------------|
| **Wasmtime** | Reference implementation by Bytecode Alliance; production-grade, standards-focused |
| **WasmEdge** | CNCF Sandbox project; optimized for edge and cloud native; supports networking and AI extensions |
| **Spin** | Developer framework by Fermyon; build and run serverless Wasm apps easily |
| **wasmCloud** | CNCF Sandbox project; distributed platform for building Wasm applications with a component model |

The ecosystem is young enough that names matter less than categories. Wasmtime is important because it is standards-focused and widely used as an embeddable runtime. WasmEdge is important in KCNA context because it is a CNCF Sandbox project and explicitly targets edge and cloud native scenarios. Spin is useful because it gives developers a pleasant framework for building event-driven Wasm applications without hand-assembling every host interface. wasmCloud is useful because it treats Wasm components as portable actors connected through providers, which changes how distributed applications can be assembled.

WASI is the point where many pilots either become practical or stall. A function that reads input, writes output, and performs pure computation usually ports well. A service that expects arbitrary POSIX behavior, process spawning, filesystem traversal, raw sockets, or dynamic linking may hit missing or evolving WASI support. Networking is especially important to evaluate because historical WASI support was stronger for filesystem and standard-stream patterns than for rich outbound service clients. Newer component-model and WASI proposals continue to improve the story, but the safe operational stance is to test the exact libraries you plan to use.

Language support should be evaluated at the dependency level, not the language logo level. Saying "Go supports Wasm" is less useful than asking whether this codebase can compile with TinyGo, whether its HTTP library works in the target runtime, and whether generated binaries meet size goals. Saying "Python can run in Wasm" is less useful than measuring whether embedding an interpreter removes the cold-start and distribution advantages. Rust often looks strong in Wasm pilots because it compiles without a garbage-collected runtime and has an ecosystem that embraces explicit dependencies, but the team still needs the skills to maintain Rust code.

Debugging changes significantly when you move from containers to Wasm. With a container, an operator might inspect logs, run `k exec`, check process lists, examine mounted files, or reproduce behavior with the same image locally. With Wasm, the failure may appear as a trap, a denied capability, a missing import, or a runtime-specific error. That is not a reason to reject Wasm, but it is a reason to design diagnostics into the platform before production. Capture denied host calls, runtime versions, module checksums, input shape, and execution duration from the start, because retrofitting that visibility after an outage is unpleasant.

The component model deserves attention because it points beyond "small functions." The idea is to define interfaces between components so modules written in different languages can compose at the Wasm level rather than the container or process level. In a mature version of that world, a Rust parser, a Go policy evaluator, and a JavaScript transformation component could share typed interfaces without each becoming a separate service with its own image, sidecar, and network hop. That vision is early, but it explains why cloud native Wasm is not limited to browser history or edge functions.

```
┌─────────────────────────────────────────────────────────────┐
│  Rust component ──┐                                         │
│                   ├──→ Composed application                 │
│  Go component ────┤    (linked at the Wasm level,          │
│                   │     not at the OS/container level)      │
│  JS component ────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

Pause and predict: if two teams publish Wasm components with typed interfaces, what operational problem might disappear compared with deploying them as separate HTTP services? One likely answer is that some internal network boundaries, service discovery entries, and per-service rollout mechanics can be replaced by component composition. The tradeoff is that version compatibility and interface governance move closer to build and release workflows, so the platform still needs clear ownership.

Real-world adoption shows both the upside and the maturity warning. Shopify has described using WebAssembly to run custom commerce logic with tight latency boundaries. Fastly Compute uses Wasm in an edge platform where very fast startup and isolation are central to the product. Cloudflare Workers supports Wasm modules alongside its isolate-based model for performance-sensitive code. These examples are credible because they connect Wasm to a specific constraint: edge latency, plugin safety, or request-scoped compute. They are not proof that every backend service should be rewritten.

The migration reality check is blunt. Rust, C, C++, Zig, and TinyGo are usually easier paths than large dynamic-language applications. Debugging is less mature than the container ecosystem, where logs, shells, profilers, and image scanners are familiar. Networking and filesystem assumptions must be tested early. If your application relies on a deep chain of native libraries, process control, or kernel tuning, a Wasm pilot can become a rewrite disguised as a packaging change. The responsible platform engineer writes those risks into the design review before the first demo.

## Running Wasm on Kubernetes 1.35+

Kubernetes does not need to become a Wasm-specific orchestrator to run Wasm workloads. The more practical model is to preserve the Kubernetes API and swap the runtime path below `containerd`. In a normal Linux container flow, kubelet asks `containerd` to create a container, and `containerd` delegates to a low-level runtime such as `runc`. In a Wasm flow, kubelet still talks through the Container Runtime Interface, `containerd` still participates, but a shim such as `runwasi` launches a Wasm runtime instead of a Linux container process.

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

RuntimeClass is the Kubernetes object that lets a Pod select a runtime handler. The cluster operator installs and configures the runtime handler on compatible nodes, then creates a `RuntimeClass` object with a handler name understood by the container runtime configuration. Application teams opt in by setting `runtimeClassName` on a Pod spec. This is the same API pattern used for runtime variants such as sandboxed containers or VM-backed runtimes, so it fits Kubernetes' broader extensibility model rather than inventing a separate scheduling surface.

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

A minimal RuntimeClass object is small, but the object is only the visible tip of the operational work. The handler value must match node runtime configuration, compatible nodes must be labeled or otherwise selected, and admission policy should prevent teams from scheduling Wasm Pods onto nodes that cannot run them. The RuntimeClass API also supports scheduling fields, so a class can steer workloads toward nodes prepared for that runtime. Treat the YAML as a contract between cluster operations and application teams, not as a magic switch.

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: wasmtime
handler: wasmtime
scheduling:
  nodeSelector:
    runtime.kubedojo.io/wasm: "true"
```

Once the class exists and nodes are prepared, a Pod can request the runtime by name. The exact image format and runtime annotations depend on the chosen stack, so production pilots should follow the runtime project's current installation guide rather than copying random manifests. The important KCNA concept is stable: the workload still looks like a Kubernetes workload, and the runtime selection is explicit in the Pod spec. That keeps Services, labels, Deployments, RBAC, and observability patterns familiar even when the execution engine below the Pod is different.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tax-calculator-wasm
  labels:
    app: tax-calculator
spec:
  runtimeClassName: wasmtime
  restartPolicy: Never
  containers:
    - name: calculator
      image: ghcr.io/example-org/tax-calculator-wasm:v1
      command: ["/tax-calculator.wasm"]
      args: ["--postal-code=10001", "--subtotal=125.00"]
```

From an operator's view, the first verification step is not whether the function returns the right tax amount; it is whether the cluster understands the runtime contract. You can inspect RuntimeClass objects, candidate nodes, and Pods using normal Kubernetes commands. These commands do not prove that every Wasm runtime feature works, but they give you a repeatable checklist for the cluster-level pieces before application debugging begins.

```bash
k get runtimeclass
k describe runtimeclass wasmtime
k get nodes -l runtime.kubedojo.io/wasm=true
k get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,RUNTIME:.spec.runtimeClassName,PHASE:.status.phase'
```

The architecture decision tells you something important about Kubernetes. Kubelet does not need to know whether the underlying implementation is a Linux namespace, a VM-backed sandbox, or a Wasm runtime as long as the configured runtime handler satisfies the expected container runtime contract. That abstraction boundary is powerful, but it also creates responsibility. If a Pod fails because the handler is missing on one node, the Kubernetes API object may look valid while the runtime layer rejects the start. Good runbooks therefore inspect both Kubernetes objects and node runtime configuration.

The e-commerce example makes the placement choice concrete. A `payment-processor` written in Java with database transactions, tracing agents, and JVM tuning should use the default container runtime. A `tax-calculator` written in Rust, stateless, and invoked at checkout can use a Wasm RuntimeClass if latency and sandboxing justify the operational setup. A `recommendation-engine` using Python GPU libraries should remain a container workload because direct hardware integration and native dependencies matter more than cold-start speed. The value of RuntimeClass is that all three can live in one cluster without pretending they have the same runtime needs.

War story: one platform team tried to schedule every Wasm pilot onto generic worker nodes because the Pod spec was the only visible change. Half the failures looked like ordinary image pull or startup problems until operators realized the runtime handler existed only on a subset of nodes. The fix was not clever application code; it was node labeling, RuntimeClass scheduling, admission validation, and a runbook that checked handler availability before debugging the module itself. Runtime diversity is still infrastructure, and infrastructure needs inventory.

## Evaluating Workload Fit and Migration Risk

The best Wasm decisions begin with the shape of the workload, not with the technology. A good fit is usually small, stateless, short-lived, dependency-light, and sensitive to startup time or sandbox boundaries. A poor fit is usually stateful, system-call-heavy, deeply tied to a mature language runtime, or dependent on kernel features. Most real applications sit in the middle, so the evaluation process should produce a scoped pilot rather than a yes-or-no verdict for the entire system.

| Use Case | Why Wasm Excels |
|----------|-----------------|
| **Serverless functions** | Millisecond cold starts make scale-to-zero practical |
| **Edge computing** | Tiny binaries, low resource requirements, runs on constrained devices |
| **Plugin systems** | Safe sandboxing — plugins cannot access host unless permitted |
| **Short-lived request handlers** | No startup penalty, minimal overhead |
| **Multi-tenant isolation** | Each Wasm module is sandboxed without needing full container isolation |

| Use Case | Why Containers Are Better |
|----------|--------------------------|
| **Complex applications** | Full OS libraries, mature debugging tools, broad language support |
| **Database servers** | Need direct hardware access, complex system calls |
| **Apps needing mature ecosystem** | Container images exist for almost everything; Wasm ecosystem is still growing |
| **Heavy I/O workloads** | WASI I/O is still maturing compared to native Linux I/O |
| **Legacy applications** | Recompiling to Wasm is non-trivial for large codebases |

When you evaluate a candidate, start with latency and lifetime. If a workload starts rarely and runs continuously, Wasm's cold-start advantage is mostly irrelevant. If it starts for each request, scales to zero, or runs at the edge where instances churn constantly, startup becomes a first-class requirement. Then evaluate artifact movement. If the same code must reach thousands of small nodes, a few megabytes versus hundreds of megabytes can alter rollout speed and reliability. Finally, evaluate trust. If the platform executes code from tenants, partners, or internal teams with different risk profiles, capability-based sandboxing may be more valuable than raw performance.

The next filter is dependency realism. Ask whether the source language compiles cleanly to Wasm, whether the dependency tree assumes POSIX behavior, whether outbound calls work through the selected runtime, and whether logs and metrics are available in your platform. The earlier you run this filter, the cheaper the pilot becomes. Teams often over-focus on a tiny benchmark and discover late that their production library for TLS, compression, database access, or image codecs depends on host features the runtime does not provide in the chosen mode.

Observability deserves its own decision point because Wasm failures can be unfamiliar. You need to know which module version ran, which runtime version executed it, which capabilities were granted, how long execution took, and whether any host call was denied. In Kubernetes, you also need normal Pod status, events, node placement, and restart behavior. If your incident process depends on opening a shell in the container and inspecting a process tree, you must design a replacement workflow before production. That replacement may be better, but it will not appear automatically.

Before running this, what output do you expect from a placement audit that lists every Pod's `runtimeClassName`? In a healthy mixed cluster, most Pods will have an empty runtime field because they use the default container runtime, while the Wasm pilot Pods should explicitly show the Wasm class. That output helps detect both mistakes: accidental Wasm scheduling for container services and accidental default scheduling for Wasm services.

```bash
k get pods -A -o custom-columns='NS:.metadata.namespace,NAME:.metadata.name,RUNTIME:.spec.runtimeClassName,NODE:.spec.nodeName,PHASE:.status.phase'
```

Cost modeling should include engineering time, not only CPU and memory. A Wasm function may reduce cold-start cost and improve density, but the team may spend time changing libraries, learning a runtime, building a new CI target, updating security scans, and training on new debugging workflows. That investment is reasonable when the workload sits on a high-value path such as checkout customization, edge request handling, or untrusted plugin execution. It is harder to justify for a low-traffic internal service that already runs reliably in a container.

The migration plan should be reversible. Start with one function or plugin class, define measurable success criteria, and keep a container fallback until the runtime path is proven. Use traffic shadowing or non-critical paths when possible. Record the exact constraints being tested: cold-start target, artifact size, denied capability behavior, runtime memory limit, and operational runbook quality. If the pilot succeeds, expand to adjacent workloads with the same shape. If it fails, the evaluation still produced useful evidence about language support, runtime maturity, or platform readiness.

A mature evaluation also names who owns the runtime after the prototype. Application teams may own module code, but platform teams usually own node preparation, runtime upgrades, admission policy, and incident response. Security teams may own signing requirements and capability review. SRE teams may own dashboards, alerts, and rollback drills. If those responsibilities are unclear, the pilot can pass a benchmark and still fail as a service. Runtime selection is an operating model choice, not only a compiler target, and ownership is what makes the runtime supportable during real incidents.

## Patterns & Anti-Patterns

Patterns help you turn the comparison into repeatable engineering choices. The first strong pattern is the sandboxed extension point. Use Wasm when a platform needs to run third-party or tenant-provided logic close to a request path without granting broad host access. It works because each module can receive narrowly scoped inputs and capabilities, and the platform can treat execution as a bounded call. The scaling concern is governance: you need versioning, resource limits, module signing, and logs for each extension, not just a fast runtime.

The second pattern is the edge function. Use Wasm when code must be distributed to many locations, start quickly, and run with modest dependencies. It works because small artifacts and architecture-neutral execution reduce rollout friction across varied hardware. The scaling concern is observability across many sites. A function that starts in milliseconds is still hard to operate if failures are invisible, runtime versions drift, or edge nodes cannot report denied capabilities in a useful way.

The third pattern is the hybrid Kubernetes runtime pool. Use normal containers for stateful services, complex frameworks, and ecosystem-heavy applications, while using RuntimeClass-selected Wasm Pods for narrow functions that benefit from sandboxing or startup speed. It works because Kubernetes already provides a familiar control plane, scheduling model, and service abstraction. The scaling concern is node preparation. Runtime handlers, labels, admission policies, and operational runbooks must stay aligned as the cluster grows.

The first anti-pattern is the "Wasm replaces containers" mandate. Teams fall into it because benchmark numbers are exciting and the Docker quote is memorable. The result is wasted migration effort against workloads that depend on mature OS behavior, databases, language runtimes, or debugging tools. The better alternative is a workload portfolio review that chooses Wasm only where startup time, artifact size, portability, or sandboxing is a concrete requirement.

The second anti-pattern is compiling first and evaluating permissions later. A demo may succeed with broad host capabilities, but production safety depends on knowing exactly which files, environment values, clocks, and network calls the module can use. Teams fall into this because they treat Wasm as another packaging target rather than a capability model. The better alternative is to define allowed capabilities in the design review and test denial cases deliberately.

The third anti-pattern is using RuntimeClass without node inventory. A Pod spec can reference a runtime class that appears valid while only some nodes can actually run that handler. Teams fall into this because Kubernetes hides runtime diversity behind a small field. The better alternative is node labeling, RuntimeClass scheduling, admission checks, and a verification command in the deployment checklist. A runtime choice should be visible in both the application manifest and the cluster operations model.

| Pattern or Anti-Pattern | Use When | Why It Works or Fails | Scaling Consideration |
|-------------------------|----------|-----------------------|-----------------------|
| Sandboxed extension point | Tenants or partners supply request-path logic | Capability grants keep host access narrow | Requires signing, quotas, versioning, and per-module logs |
| Edge function | Code ships to many constrained sites | Small artifacts and fast startup reduce distribution cost | Needs fleet-wide runtime version and telemetry discipline |
| Hybrid runtime pool | Containers and Wasm serve different workload shapes | Kubernetes APIs stay familiar while runtime choice varies | Requires node inventory, RuntimeClass scheduling, and admission policy |
| Replacement mandate | Leadership wants every service on Wasm | Ignores databases, legacy dependencies, and tooling maturity | Produces expensive rewrites with weak operational gain |
| Permissions afterthought | Demo works with broad access | Breaks the security reason for adopting Wasm | Denial behavior must be tested as a success criterion |
| RuntimeClass without inventory | Manifests change before nodes are prepared | Pods fail at runtime despite valid YAML | Handler availability must be managed like any node capability |

## Decision Framework

Use this decision framework when a team proposes Wasm for a Kubernetes or cloud native workload. Start with the value claim, then test the constraints that can invalidate it. If the value claim is startup speed, measure cold starts under realistic traffic. If the value claim is sandboxing, define denied capabilities and prove they are denied. If the value claim is edge distribution, measure artifact size and rollout behavior. If nobody can name the value claim, the workload should stay in the container path until a real constraint appears.

```text
Start
  |
  v
Is the workload small, stateless, and short-lived?
  |-- no --> Prefer containers or VMs; revisit after decomposition.
  |
  yes
  |
  v
Does it benefit from fast startup, tiny artifacts, or sandboxed untrusted code?
  |-- no --> Containers are simpler and more mature.
  |
  yes
  |
  v
Can the language, dependencies, filesystem, and networking fit the selected Wasm runtime?
  |-- no --> Prototype the blocker or keep the workload containerized.
  |
  yes
  |
  v
Can the platform observe, limit, schedule, and roll back the module safely?
  |-- no --> Build the operational controls before production.
  |
  yes
  |
  v
Run a scoped Wasm pilot with explicit success criteria.
```

| Decision Signal | Lean Toward Wasm | Lean Toward Containers |
|-----------------|------------------|------------------------|
| Startup behavior | Request-scoped, bursty, scale-to-zero | Long-running service with rare restarts |
| Artifact movement | Edge fleet, constrained bandwidth, frequent updates | Central cluster with normal image cache behavior |
| Trust boundary | Tenant plugins, untrusted extensions, strict capability grants | Internal trusted service with mature controls |
| Dependencies | Rust/TinyGo/C library with small dependency tree | JVM, Python ML stack, database, kernel-specific tooling |
| Operations | Runtime telemetry and denial logs are planned | Team depends on shell access and mature container debugging |
| Kubernetes fit | RuntimeClass nodes and admission policy are ready | Cluster runtime inventory is unclear or unmanaged |

The framework should produce a written decision, not just a meeting consensus. A good decision record says which runtime was chosen, what alternatives were considered, which constraints mattered, and how the team will know the decision is wrong. For a Wasm pilot, the rollback trigger might be runtime errors above a threshold, missing observability fields during an incident drill, artifact size above a target, or denied capability logs that are too vague to debug. For a container decision, the record should also be honest: the team may revisit Wasm later if cold starts, edge distribution, or plugin safety become painful enough.

Apply the framework to the earlier e-commerce architecture. The payment processor fails the first filter because it is not small or short-lived, and its database behavior makes containers the safer choice. The tax calculator passes because it is stateless, narrow, and latency-sensitive, provided the Rust implementation and runtime telemetry work. The recommendation engine fails the dependency filter because GPU-bound Python libraries and native drivers dominate the design. This kind of explicit reasoning is exactly what KCNA wants: not tool worship, but workload-aware runtime selection.

One useful way to write the final decision is as a short operating contract. State that the Wasm runtime is approved only for the named workload class, that the module must declare its required capabilities, that the node pool must advertise the matching runtime label, and that rollback remains a container implementation until the pilot has passed failure-mode drills. This turns architecture judgment into something reviewers, operators, and developers can all inspect. It also prevents the common drift where a successful demo becomes an undocumented platform exception.

## Did You Know?

- **WebAssembly became a W3C Recommendation in December 2019.** That matters because Wasm is not just a vendor experiment; it is a standardized execution format with browser and server-side implementations building around a shared specification.

- **All major browsers ship a Wasm runtime.** Chrome, Firefox, Safari, and Edge can execute Wasm, and that browser heritage explains why portability and sandboxing were part of the design from the beginning rather than later cloud features.

- **Fastly has publicly described Compute cold starts in the microsecond range.** The exact number depends on platform details, but the important lesson is that edge platforms care about startup overhead at a scale where ordinary container cold starts would dominate request latency.

- **CNCF hosts Wasm-related projects such as WasmEdge, wasmCloud, and SpinKube.** KCNA does not require runtime internals, but it does expect you to recognize that Wasm is now part of the cloud native project landscape rather than only a browser technology.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating Wasm as a universal container replacement | Benchmarks and quotes make the runtime sound like a full platform substitute | Classify workloads by startup sensitivity, dependency weight, statefulness, and trust boundary before choosing |
| Ignoring WASI permissions during design | Teams focus on compiling the code and postpone the host access model | Define required files, environment values, clocks, and network access before the first production pilot |
| Choosing Wasm for a dependency-heavy service | The top-level function looks small, but libraries assume a normal OS process | Compile the real dependency tree early and keep JVM, Python ML, database, and kernel-tuned workloads in containers |
| Creating a RuntimeClass without prepared nodes | The Kubernetes YAML is small, so teams underestimate node runtime configuration | Label compatible nodes, use RuntimeClass scheduling, and verify handler availability with `k get runtimeclass` and node checks |
| Measuring only happy-path latency | A tiny benchmark hides denial behavior, runtime errors, and cold observability gaps | Include denied capability tests, runtime version logging, module checksums, and failure-mode drills in success criteria |
| Shipping untrusted plugins without supply-chain controls | The sandbox feels strong enough to replace normal release discipline | Require module signing, provenance, resource limits, version policy, and tenant-level audit logs |
| Assuming source language support means application support | Language logos hide compiler limitations and unsupported libraries | Test the exact source code, compiler target, runtime, and library set planned for production |

## Quiz

<details><summary>Your team runs a Rust tax-calculation function during checkout, and container cold starts are adding visible latency during burst traffic. The function is stateless, dependency-light, and receives all input in the request. Would you evaluate Wasm, and what would you test first?</summary>

Yes, this is a strong Wasm candidate because the workload is short-lived, small, stateless, and latency-sensitive. The first tests should measure realistic cold-start latency, artifact size, and behavior under denied capabilities rather than only a synthetic benchmark. You should also confirm that the Rust dependencies compile cleanly to the selected runtime and that platform logs show runtime version, module checksum, execution duration, and failure reason. If those tests pass, a scoped pilot is reasonable.

</details>

<details><summary>A CTO asks whether a PostgreSQL database should be moved to WebAssembly because Wasm artifacts are smaller than container images. How should you respond?</summary>

PostgreSQL should remain a container or VM workload because the decisive requirements are storage, mature filesystem behavior, kernel interaction, observability, and operational tooling. Wasm's compact artifact size does not compensate for weak fit with heavy stateful I/O and database administration. The better response is to preserve containers for the database while looking for request-scoped functions, plugins, or edge handlers where Wasm's startup and sandboxing advantages actually matter. That answer compares workload shape rather than rejecting Wasm broadly.

</details>

<details><summary>A Pod specifies `runtimeClassName: wasmtime`, but it stays pending or fails to start on some nodes. What cluster-level checks should you perform before debugging application code?</summary>

Start by checking that the `RuntimeClass` exists and that its handler name matches the node runtime configuration. Then verify that compatible nodes are labeled or selected by the class scheduling rules and that the Pod actually landed on a prepared node. Use `k describe runtimeclass wasmtime`, inspect node labels, and review Pod events for handler or sandbox creation errors. Application debugging comes later because a missing runtime handler is an infrastructure inventory problem.

</details>

<details><summary>A platform wants to run customer-provided discount scripts inside the checkout path. Why might Wasm be safer than ordinary containers for this specific plugin model, and what controls are still required?</summary>

Wasm is attractive because the runtime can execute compact modules in a default-deny sandbox and grant only the capabilities needed for the discount calculation. That maps well to untrusted or semi-trusted tenant code because the plugin should not need arbitrary filesystem, process, or network access. The platform still needs module signing, tenant quotas, input validation, runtime patching, audit logs, and observability for denied calls. Sandboxing is a strong boundary, not a complete governance program.

</details>

<details><summary>A Python recommendation service uses native GPU libraries and long-running model workers, but one handler function is small. Should the team move the service to Wasm?</summary>

The service should stay containerized because the real workload is dominated by native dependencies, GPU integration, long-running workers, and mature Python operational tooling. The small handler does not determine the runtime choice when the dependency and hardware requirements sit elsewhere. A better architecture might extract a separate narrow function if it has a Wasm-friendly shape, but the recommendation engine itself is a poor pilot. This diagnosis protects the team from turning a packaging experiment into a difficult rewrite.

</details>

<details><summary>A Wasm pilot shows excellent latency, but failures appear as vague runtime traps with no module version or denied capability logs. Is the pilot production-ready?</summary>

No, the pilot is missing operational readiness even if happy-path latency is impressive. Production teams need enough telemetry to diagnose which module version ran, which runtime executed it, what input shape triggered the error, and whether the module attempted a denied host call. Without that information, incidents become guesswork and operators may broaden permissions just to debug. The fix is to add runtime-level logging, checksums, denial events, and failure-mode drills before production traffic.

</details>

<details><summary>You are designing a mixed Kubernetes 1.35+ cluster with Java services, Rust request functions, and tenant plugins. How would you place workloads across runtimes?</summary>

Keep the Java services on the default container runtime because they benefit from the mature JVM, container debugging, and existing image ecosystem. Place the Rust request functions on a Wasm RuntimeClass only if their dependencies, networking, and telemetry pass a scoped pilot. Run tenant plugins through a Wasm-based extension platform where capability grants, signing, quotas, and audit logs are explicit. This design uses Kubernetes as the shared control plane while treating runtime choice as a workload-specific decision.

</details>

## Hands-On Exercise

In this exercise, you will produce a practical Wasm placement review for a hypothetical Kubernetes 1.35+ platform. You do not need a Wasm runtime installed to complete the reasoning work, but the inspection commands are written so they can run against a real cluster that has `kubectl` access. The goal is to practice the operational workflow: document the candidate, define runtime criteria, inspect cluster support with `k`, and write a reversible pilot plan.

### Setup

Run the alias once in your shell if you are connected to a test cluster. If you do not have a cluster, read the commands and write down the output you would expect from a mixed runtime environment. The important skill is connecting Kubernetes objects to the runtime decision rather than memorizing a specific project installation.

```bash
alias k=kubectl
k get runtimeclass
```

### Tasks

- [ ] **Compare** the three candidate workloads: `payment-processor`, `tax-calculator`, and `recommendation-engine` by startup sensitivity, dependency weight, statefulness, and trust boundary.
- [ ] **Design** a RuntimeClass placement plan that keeps container workloads on the default runtime and routes only the Wasm candidate through a prepared runtime handler.
- [ ] **Evaluate** whether the Wasm candidate has a clear success claim, such as lower cold-start latency, smaller edge artifact size, or safer tenant execution.
- [ ] **Diagnose** at least four migration risks, including language support, WASI permissions, networking assumptions, and debugging or observability gaps.
- [ ] **Implement** an inspection checklist using `k get runtimeclass`, node label checks, Pod runtime columns, and Pod event review.
- [ ] **Record** rollback criteria that would move the candidate back to containers if the pilot fails operationally.

<details><summary>Solution Guide</summary>

A strong answer places `payment-processor` on the default container runtime because it is a complex Java service with database transactions and mature JVM operational needs. It places `tax-calculator` on a Wasm RuntimeClass if the Rust implementation compiles cleanly, needs narrow capabilities, and benefits from checkout-path startup speed or sandboxing. It keeps `recommendation-engine` in containers because GPU-bound Python libraries and long-running workers are poor Wasm candidates. The RuntimeClass plan should include prepared node labels, a handler name agreed with cluster operations, and an admission or review process that prevents accidental scheduling to unsupported nodes.

The migration-risk section should name concrete risks rather than generic caution. Good examples include TinyGo or Rust dependency compatibility, missing WASI networking features for a chosen library, vague trap errors without denied capability logs, lack of module signing, node runtime drift, and rollback complexity if traffic routing assumes only one implementation. The inspection checklist should use normal Kubernetes commands to verify `RuntimeClass`, node labels, Pod `runtimeClassName`, and events. Rollback criteria might include cold starts above target, missing observability fields during a drill, runtime errors above an agreed threshold, or artifact size larger than the edge distribution budget.

</details>

### Success Criteria

- [ ] Your comparison explains why Wasm and containers are complementary rather than replacements.
- [ ] Your design uses `RuntimeClass` only for workloads that benefit from Wasm-specific properties.
- [ ] Your evaluation names a measurable success claim for the Wasm pilot.
- [ ] Your diagnosis includes at least one risk for language support, one for WASI permissions, and one for observability.
- [ ] Your inspection workflow includes `k` commands for RuntimeClass, node readiness, Pod placement, and events.
- [ ] Your rollback criteria are specific enough that another engineer could apply them during a review.

## Sources

- [WebAssembly specification](https://webassembly.github.io/spec/core/)
- [WebAssembly System Interface documentation](https://wasi.dev/)
- [W3C WebAssembly Recommendation](https://www.w3.org/TR/wasm-core-1/)
- [Bytecode Alliance Wasmtime documentation](https://docs.wasmtime.dev/)
- [WasmEdge documentation](https://wasmedge.org/docs/)
- [CNCF WasmEdge project page](https://www.cncf.io/projects/wasmedge/)
- [wasmCloud documentation](https://wasmcloud.com/docs/)
- [Spin documentation](https://developer.fermyon.com/spin/v3/index)
- [SpinKube documentation](https://www.spinkube.dev/docs/)
- [containerd runwasi repository](https://github.com/containerd/runwasi)
- [Kubernetes RuntimeClass documentation](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- [Kubernetes 1.35 documentation](https://kubernetes.io/docs/home/)

## Next Module

[Module 3.10: Green Computing and Sustainability](../module-3.10-green-computing/) - The next lesson connects runtime and platform choices to energy-aware operations, carbon signals, and the sustainability tradeoffs that appear when cloud native systems run at large scale.
