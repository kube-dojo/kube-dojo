---
citations_verified: true
title: "Module 1.11: eBPF Tracing Tools (bpftrace, BCC, Inspektor Gadget)"
slug: platform/toolkits/observability-intelligence/observability/module-1.11-ebpf-tracing-tools
sidebar:
  order: 12
revision_pending: false
---

## Complexity: `[MEDIUM]`

**Time to Complete**: 50 minutes, plus extra lab time if you need to install kernel headers, create a disposable Kubernetes cluster, or request temporary debugging privileges.

**Prerequisites**: [eBPF Fundamentals](/platform/foundations/ebpf/module-1.1-ebpf-fundamentals/), [Pixie](/platform/toolkits/observability-intelligence/observability/module-1.6-pixie/), [Continuous Profiling](/platform/toolkits/observability-intelligence/observability/module-1.9-continuous-profiling/), Linux command-line comfort, and basic Kubernetes debugging; the module assumes you understand why hooks, maps,
verifier checks, and privileged node access matter.

**Kubernetes Version Target**: 1.35+, with examples that also depend on the worker-node Linux kernel, container runtime, and cluster security policy rather than the Kubernetes API version alone.

**Environment Assumption**: The host examples assume a Linux node where eBPF tracing is allowed by the kernel, the user has root or the required capabilities, and BTF data is available for modern typed attachment. The Kubernetes examples assume a local `kind`, Minikube, or lab cluster where privileged DaemonSets are allowed.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Select** between bpftrace, BCC, Inspektor Gadget, Pixie, continuous profiling, and OTel eBPF auto-instrumentation based on whether the problem is immediate, repeated, cluster-wide, code-level, or telemetry-pipeline oriented.
- **Run** safe first bpftrace probes for syscall and TCP retransmission investigation while checking probe names, argument fields, BTF availability, and kernel-version constraints before trusting the output.
- **Explain** why BCC's Python frontend remains useful for sustained tools even though bpftrace is faster for one-liners, and adapt a small BCC tracing script without pretending it replaces upstream-maintained tools.
- **Operate** Inspektor Gadget and OpenTelemetry eBPF auto-instrumentation with realistic expectations about Kubernetes privileges, DaemonSet deployment, RBAC, trace context, encrypted traffic, and maturity boundaries.

---

## Read This Module as an Incident Probe Runbook

Read the examples as a sequence of investigation decisions rather
than as a catalog of clever commands. In a real incident, the
valuable move is rarely "run more eBPF." The valuable move is to
choose the event boundary that can separate two plausible causes,
attach for a bounded window, and then decide whether the evidence
points toward application code, a dependency, node behavior, network
path, runtime policy, or missing permanent telemetry.

The commands intentionally start with enumeration before observation.
That pattern looks slow when you already know the demo host, but it is
the habit that keeps production debugging honest across mixed kernels,
managed node images, distro backports, and plugin versions. If a probe
does not exist, if a field is named differently, or if a cluster policy
blocks the required privilege, you want to discover that before the
incident timeline depends on a misleading empty output stream.

The module also keeps the permanent observability tools in view. When
an ad-hoc trace produces a signal that would have prevented the page,
that is a design input for Pixie scripts, profiling coverage,
OpenTelemetry instrumentation, Prometheus metrics, or runbook-ready
gadgets. Temporary eBPF tracing is most valuable when it teaches the
platform which signal deserves to become boring, reviewed, and always
available.

---

## Why This Module Matters for On-Demand eBPF Debugging

Pixie and continuous profiling already gave you the always-on side of eBPF observability. Pixie watches Kubernetes workloads and lets you query observed traffic and process behavior without changing application code. Continuous profilers such as Parca and Pyroscope sample stacks over time so you can ask which functions burn CPU, memory, or wall time. Those tools are deliberately persistent: deploy the agent, keep collecting, query the history, and use the product experience to narrow a broad symptom into a defensible explanation.

This module is about a different operating mode. You have a problem right now. The dashboard says latency jumped, but application traces are sparse, logs are noisy, and nobody wants to roll a new build just to add temporary instrumentation. In that moment, the question is not "which observability product should own this signal forever?" The question is "which kernel or user-space probe can I attach for the next five minutes so I can prove or disprove a hypothesis without guessing?"

That imperative mindset changes the tool choice. bpftrace is the scalpel for one-liners: list probes, attach to one event, print a few fields, stop when the incident question is answered. BCC is the workbench for repeatable scripts: write a small Python frontend, embed a BPF C program, keep maps and perf buffers, and turn a useful one-off into a tool the team can run again. Inspektor Gadget is the Kubernetes-native version of the same idea: ask for a gadget against a namespace, pod, node, or container instead of SSHing into every worker and hand-running host tools.

Exercise scenario: A checkout endpoint is slow only during traffic spikes. Prometheus shows elevated p99 latency, but CPU and memory are normal. The application team has traces for the checkout process itself, yet the trace usually ends at a generic HTTP client span. A platform engineer lists TCP tracepoints, attaches a short `bpftrace` program to `tracepoint:tcp:tcp_retransmit_skb`, and sees retransmission events climb when the checkout pods call a downstream inventory service. That does not prove root cause by itself, but it changes the incident from "the API is slow" to "the API is waiting behind packet loss or congestion on one dependency path."

The lesson is not that bpftrace magically replaces metrics, logs, or traces. The lesson is that eBPF tracing can reveal behavior at the kernel boundary when the permanent telemetry is too coarse. You still need ordinary observability to decide impact, confirm recovery, and explain user-facing consequences. You still need application instrumentation for business semantics. The ad-hoc eBPF tools help you bridge the missing minutes between a vague symptom and the next precise investigation step.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> **bpftrace** and **BCC** are foundational open-source tracing tools maintained under the iovisor project; they are not CNCF projects. **Cilium** (which includes **Tetragon**) is a CNCF **Graduated** project (graduated October 11, 2023). **Inspektor Gadget** is CNCF **Sandbox** (accepted March 7, 2023). **Pixie** is CNCF **Sandbox** (accepted June 22, 2021). **Parca** is an independent open-source project (Apache 2 License) created by Polar Signals — it is not a CNCF project and has never been accepted into any CNCF maturity level. All of these tools occupy different points on the imperative-to-declarative spectrum: bpftrace and BCC are imperative terminal tools; Inspektor Gadget wraps common probes behind a Kubernetes-aware CLI; Pixie, Parca, and Pyroscope are persistent always-on observability and profiling platforms.

---

## Did You Know

- **Current bpftrace documentation uses dot syntax for tracepoint arguments**, such as `args.filename`, even though older blog posts and distro-era examples may show `args->filename`; verify your local `bpftrace --version` and use `bpftrace -lv` before pasting syntax across systems.
- **BCC predates the modern CO-RE-first tooling style**, but it remains valuable because many battle-tested operational tools, including TCP, filesystem, scheduler, and block-I/O tracers, already exist in the upstream tree.
- **Inspektor Gadget has moved toward image-based gadgets**, so the current upstream docs often show `kubectl gadget run trace_exec:latest` while older material and operator habits may say `kubectl gadget trace exec` for the same debugging shape.
- **OpenTelemetry eBPF Instrumentation is evolving quickly as of May 25, 2026**, so treat it as a strong candidate for zero-code application observability, but check the live compatibility matrix before designing an organization-wide standard around a specific runtime or protocol claim.

---

## Decision Matrix: Which eBPF Observability Shape Fits the Job

Start with the operational question before choosing the tool. A production incident rewards the tool that answers the narrowest useful question with the least new moving parts. A platform standard rewards the tool that produces durable, low-friction telemetry for many teams. Those are related goals, but they are not the same goal, and mixing them is how teams turn a five-minute trace into an accidental observability platform.

| Tool | Best for | Hook type | Cost/overhead | Maturity |
| --- | --- | --- | --- | --- |
| bpftrace | Quick one-liners, ad-hoc | tracepoints, kprobes, uprobes | Low (no daemon) | Mature |
| BCC | Sustained tools, complex logic | Same as bpftrace plus helpers | Med (Python) | Mature |
| Inspektor Gadget | Kubernetes-native debugging | DaemonSet plus gadgets | Low-med | Active (Inspektor Gadget org) |
| OTel eBPF | Auto-tracing without code changes | uprobes plus kernel and network observation | Med | Emerging |
| Pixie | Always-on Kubernetes auto-observability | eBPF collectors plus Kubernetes metadata | Med | See [module 1.6](/platform/toolkits/observability-intelligence/observability/module-1.6-pixie/) |
| Parca and Pyroscope | Always-on continuous profiling | perf events, stack unwinding, eBPF profilers | Low-med | See [module 1.9](/platform/toolkits/observability-intelligence/observability/module-1.9-continuous-profiling/) |

Use bpftrace when you can express the question in one or two probes and you are willing to stop the tool as soon as the hypothesis is answered. Use BCC when the one-liner grows state, formatting, per-event structs, or enough logic that shell quoting becomes the biggest risk. Use Inspektor Gadget when the object you care about is a Kubernetes workload and you want the CLI to understand namespaces, pods, containers, and nodes. Use OTel eBPF auto-instrumentation when the goal is not a terminal investigation but zero-code traces and RED metrics entering an OpenTelemetry pipeline.

The important distinction from Pixie is control style. Pixie is declarative and product-shaped: deploy it, query what it observes, and use PxL and the UI to move through workload evidence. bpftrace and BCC are imperative: decide the hook now, attach now, print now, remove now. Inspektor Gadget sits between those worlds by packaging common imperative probes behind a Kubernetes-aware command surface.

The distinction from continuous profiling is signal type. Profiling asks what code consumed resources over time. Tracing tools in this module ask what event just happened at a kernel, syscall, network, or user-space function boundary. A retransmitted TCP segment, a new process execution, a file open, or an unencrypted TLS SNI value can explain a symptom that a flame graph will not show clearly. A flame graph can explain CPU waste that a syscall trace will never attribute to a specific hot function.

---

## The Attachment Map: Where These Tools Hook Into the System

The [eBPF Fundamentals module](/platform/foundations/ebpf/module-1.1-ebpf-fundamentals/) introduced hooks, verifier checks, maps, BTF, and CO-RE. This module assumes that vocabulary. What changes here is the operator workflow: instead of designing a permanent eBPF product, you choose a probe family that exposes the event you need, run it long enough to collect evidence, and then remove it before the probe becomes a hidden source of noise or risk.

```text
                         user space
+-------------------------------------------------------------------+
|  app process       language runtime        shared libraries        |
|  checkout-api      Go net/http             OpenSSL, libc           |
|      |                  |                       |                  |
|      |                  |                       |                  |
|      v                  v                       v                  |
|  uprobes / uretprobes   USDT probes             TLS and libc hooks |
+-------------------------------------------------------------------+
            |                    |                         |
            v                    v                         v
+-------------------------------------------------------------------+
|                         kernel space                              |
|                                                                   |
|  syscalls         TCP stack          scheduler        perf events  |
|     |                |                  |                |         |
|     v                v                  v                v         |
|  tracepoints      kprobes/fentry      tracepoints      sampling    |
|                                                                   |
|  eBPF programs write events, counts, histograms, or stacks to maps |
+-------------------------------------------------------------------+
            |                    |                         |
            v                    v                         v
     bpftrace/BCC        Inspektor Gadget             profilers/OTel
```

Tracepoints are usually the safest first hook because they are named instrumentation points with a typed event format. A syscall tracepoint such as `tracepoint:syscalls:sys_enter_openat` exposes the fields that the kernel's tracepoint format declares, and bpftrace can list those fields before you run the probe. kprobes and fentry hooks are more flexible because they can attach to kernel functions, but they are more exposed to kernel implementation details. uprobes do the same style of attachment in user space, which is why TLS, libc, Go runtime, and language-library instrumentation often enters the discussion.

Perf events and profiling hooks matter because learners often put every eBPF observability tool in one bucket. Continuous profilers use sampling to answer "where is CPU time going?" An ad-hoc trace uses event attachment to answer "did this operation happen, with which fields, and how often?" OTel eBPF auto-instrumentation may combine user-space probes, executable inspection, and network observation so it can emit spans and metrics to a collector, but its operating model is still different from a terminal-driven trace.

The practical rule is simple: prefer the most stable hook that exposes the information you need. If a tracepoint has the field, use the tracepoint. If no tracepoint has the field and the kernel function is stable enough for your kernel fleet, consider a kprobe or fentry hook. If the interesting behavior is inside a language runtime or shared library, consider uprobes or a packaged tool that already handles symbol resolution and runtime drift.

---

## bpftrace: DTrace-Style One-Liners for Linux

bpftrace is the fastest path from a hypothesis to a kernel-observed event stream. The official project describes it as a high-level tracing language for Linux that uses eBPF and supports kprobes, uprobes, USDT probes, tracepoints, raw tracepoints, and hardware or software perf events. That breadth is why it feels like a shell for tracing rather than a library. You can list probes, attach a short action, aggregate counts in a map, and exit without building a long-running service.

Install it from the host distribution when possible, because the package will usually match the distro's LLVM, libbpf, and kernel-support assumptions better than a random binary. The official repository shows native package-manager installs for Debian, Ubuntu, Fedora, Alpine, Arch, Gentoo, Nix, and openSUSE. On a lab Ubuntu node, the starting point is intentionally boring:

```bash
sudo apt-get update
sudo apt-get install -y bpftrace
bpftrace --version
```

Before attaching a probe, list what your kernel actually exposes. This avoids two common failure modes: copying a tracepoint from a different kernel, and assuming a field name from a different bpftrace version. The current bpftrace language docs show `args.filename` dot access for tracepoint fields, and verbose listing mode is the way to confirm the real field layout on your host.

```bash
sudo bpftrace -l 'tracepoint:syscalls:*'
sudo bpftrace -lv 'tracepoint:syscalls:sys_enter_openat'
```

The first beginner command should be a low-volume syscall probe. The official bpftrace one-liners page includes the same shape for open events, and this module uses the current dot-argument form from the latest docs. On modern Linux systems, `openat` is often more visible than the older `open` syscall, so trace both when you are exploring file activity.

```bash
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_open { printf("%s %s\n", comm, str(args.filename)); }'
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args.filename)); }'
```

The TCP retransmission investigation uses the same discipline. First list and inspect the tracepoint. Then begin with a count or a minimal print rather than trying to decode every address field in one shot. Address decoding varies by kernel and bpftrace feature set, so a production-safe runbook should include `bpftrace -lv` output from the target kernel before it formats packet fields.

```bash
sudo bpftrace -l 'tracepoint:tcp:*retrans*'
sudo bpftrace -lv 'tracepoint:tcp:tcp_retransmit_skb'
sudo bpftrace -e 'tracepoint:tcp:tcp_retransmit_skb { @[comm] = count(); }'
```

That one-liner is intentionally modest. It answers whether retransmission events are rising while the incident happens and which current task names are associated with event handling. It does not claim to be a full network diagnosis. When you need source and destination addresses, TCP state, and cleaner formatting across kernels, graduate to a maintained tool such as BCC's `tcpretrans.py`, an Inspektor Gadget TCP gadget, or a dedicated network observability product.

bpftrace gotchas are mostly about environment drift. Old enterprise kernels may lack BTF or the tracepoint you copied from a newer host. Hardened nodes may require root, `CAP_BPF`, `CAP_PERFMON`, or `CAP_SYS_ADMIN` depending on kernel and distro settings. Some managed Kubernetes worker nodes do not expose the host tracing filesystem to ordinary pods. A probe that is harmless on a quiet test VM can flood a terminal on a busy production node if it fires on every syscall without a predicate.

The safest bpftrace habit is to make every probe answer one written question. "Which processes are opening this file?" is a good question. "Print every syscall in production for a while" is not. Use predicates, aggregate counts, limit duration, and record the exact command in the incident notes so another engineer can reproduce or challenge the evidence later.

---

## BCC: The Historical Workhorse for Sustained Tools

BCC, the BPF Compiler Collection, is a toolkit for building BPF-based tracing and performance tools. Its classic workflow embeds a small C-like BPF program inside a Python frontend. The frontend compiles and loads the program, attaches probes, reads maps or perf buffers, resolves symbols, and prints output in a form humans can use. That is heavier than bpftrace, but it is also the reason many durable operational tools were written in BCC before CO-RE and libbpf became the default for newer agents.

Install BCC from the distribution packages that match your kernel and headers. Package names vary by distro; on Debian and Ubuntu families, `bpfcc-tools` and the Python BCC bindings are the common starting point, while Fedora-family systems usually use `bcc-tools` and matching Python bindings. If an install guide asks for kernel headers, do not skip that step on older systems, because BCC often compiles programs against the running kernel's available headers.

```bash
sudo apt-get update
sudo apt-get install -y bpfcc-tools python3-bpfcc linux-headers-$(uname -r)
tcpretrans-bpfcc --help || true
```

The right way to trace TCP retransmits with BCC in production is usually to start with the upstream `tools/tcpretrans.py`, because it already handles address formatting, IPv4 and IPv6 details, tail-loss probes, and kernel differences better than a teaching snippet. The short script below is deliberately smaller. It demonstrates the Python frontend plus BPF program shape, attaches to the `tcp_retransmit_skb` kernel function, and prints the current task name when the function is hit. Use it as a learning scaffold, not as your fleet runbook.

```python
#!/usr/bin/env python3
from bcc import BPF

PROGRAM = r"""
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct event_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
};

BPF_PERF_OUTPUT(events);

int trace_retransmit(struct pt_regs *ctx) {
    struct event_t event = {};
    u64 id = bpf_get_current_pid_tgid();

    event.pid = id >> 32;
    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}
"""


def print_event(cpu, data, size):
    event = b["events"].event(data)
    print(f"pid={event.pid:<8} comm={event.comm.decode('utf-8', 'replace')}")


b = BPF(text=PROGRAM)
b.attach_kprobe(event="tcp_retransmit_skb", fn_name="trace_retransmit")
b["events"].open_perf_buffer(print_event)

print("Tracing tcp_retransmit_skb. Press Ctrl-C to stop.")
while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        break
```

```bash
chmod +x tcpretrans-mini.py
sudo ./tcpretrans-mini.py
```

This script is useful because it shows the parts bpftrace hides. There is an embedded BPF program. There is a named attachment call. There is a perf buffer for event delivery. There is Python code that owns formatting, looping, and exception handling. The moment you need structured output, multiple maps, periodic summaries, symbol resolution, or cross-event state, BCC becomes more comfortable than a heavily quoted bpftrace command.

The tradeoff is operational weight. BCC needs Python, LLVM, BCC libraries, and enough kernel headers or BTF support for the program you compile. Startup can be slower. Packaging a BCC tool into a minimal debug container is more awkward than pasting a bpftrace one-liner on a host that already has bpftrace installed. For long-lived platform agents, newer libbpf or CO-RE approaches often package better, which is why BCC is best viewed as a mature operator toolkit rather than the only future of eBPF development.

Compared with bpftrace, choose BCC when the script has become a tool. If you want a histogram, a map keyed by tuple, a reusable command-line interface, or a script that another engineer can run without editing shell quotes, BCC is a better fit. If the question is still a one-off probe you will throw away after the incident, bpftrace keeps the cognitive and dependency cost lower.

---

## Inspektor Gadget: Kubernetes-Native eBPF Debugging

Inspektor Gadget packages eBPF debugging workflows as Kubernetes-aware gadgets. Instead of SSHing into the node, discovering the container's host PID, mounting tracing filesystems by hand, and then running bpftrace or BCC, you run a `kubectl gadget` command that targets Kubernetes objects. The project can also run on plain Linux through the `ig` binary, but the curriculum value here is the Kubernetes workflow.

The current upstream quick start describes two Kubernetes modes. A permanent install deploys Inspektor Gadget on worker nodes and lets you run gadgets through the `kubectl gadget` plugin. A one-shot mode can use `kubectl debug node` with the `ig` container for a focused investigation. The permanent path is the one platform teams usually pilot because it gives responders a consistent CLI surface during incidents.

```bash
kubectl krew install gadget
kubectl gadget deploy
kubectl -n gadget get pods
```

That deployment is not a harmless ordinary app. The upstream install docs say Inspektor Gadget is composed of a client plugin and a DaemonSet in the cluster, and the quick deploy path installs the DaemonSet with its RBAC rules. It needs node-level visibility, access to kernel features, and enough privilege to load and run the eBPF programs behind each gadget. On restricted clusters, the platform team must approve the namespace, service account, Pod Security admission posture, AppArmor or seccomp choices, image provenance, and which users are authorized to run gadgets.

For process execution tracing, the current image-based command is `trace_exec`. Older examples and operator muscle memory may say `kubectl gadget trace exec`; translate that to the image-based form if your plugin version expects `run trace_exec:latest`. This distinction matters because Inspektor Gadget is active, and the command surface has evolved along with the gadget image model.

```bash
kubectl create namespace ebpf-lab
kubectl run exec-demo -n ebpf-lab --image=busybox:1.36 --restart=Never -- sleep 3600

kubectl gadget run trace_exec:latest -n ebpf-lab --podname exec-demo

# Older plugin releases may expose the equivalent workflow like this:
kubectl gadget trace exec -n ebpf-lab --podname exec-demo
```

Open another terminal and generate events inside the pod. The goal is not the command itself; it is watching the gadget enrich process execution events with Kubernetes metadata, so the output identifies the namespace, pod, container, command, and process context without making you reverse-map host PIDs.

```bash
kubectl exec -n ebpf-lab exec-demo -- sh -c 'date; cat /proc/version; sleep 1'
```

For crash forensics, `traceloop` is the important mental model. The upstream docs describe it as a flight recorder for system calls. Instead of only seeing events after you start staring at the terminal, traceloop can capture the sequence of syscalls around a failure so you can inspect what the process did before termination. In a Kubernetes incident, that is useful when a container exits too quickly for interactive debugging or when a failing command leaves little application log context.

```bash
kubectl gadget run traceloop:latest -n ebpf-lab --podname exec-demo
```

For TLS SNI visibility, current docs call the gadget `trace_sni`. The issue text uses the older descriptive label `snisniffer`, which is a useful memory hook, but the current command to test is `trace_sni`. The signal is intentionally narrow: it tracks Server Name Indication from TLS requests when the SNI is visible in the ClientHello. It is not a TLS decryptor, and encrypted ClientHello deployments can remove the hostname signal.

```bash
kubectl gadget run trace_sni:latest -n ebpf-lab
```

Inspektor Gadget also includes top-style gadgets for CPU, files, block I/O, TCP, and other activity. Those are best used when the question is Kubernetes-scoped and operational: which pod is opening files, which container is executing new processes, which workload is creating TCP churn, or what happened before a crash? When the question is "give every application team always-on traces," use Pixie or OTel instrumentation instead. When the question is "write a weird one-off probe against a kernel tracepoint," bpftrace is still the smaller tool.

---

## OpenTelemetry eBPF Auto-Instrumentation

OpenTelemetry eBPF auto-instrumentation changes the destination of the data. bpftrace, BCC, and many Inspektor Gadget runs print evidence to the operator. OTel eBPF auto-instrumentation tries to turn kernel-observed and user-space-observed behavior into telemetry that enters the OpenTelemetry pipeline as spans and metrics. That makes it tempting for platform teams that want traces from services they cannot rebuild, legacy workloads with weak instrumentation, or compiled services where adding SDK calls is slower than deploying an agent.

The main OSS names to know as of May 25, 2026 are OpenTelemetry eBPF Instrumentation, usually abbreviated OBI; OpenTelemetry Go Automatic Instrumentation, a Go-focused eBPF auto-instrumentation project; and Splunk's OpenTelemetry Collector distribution integration that has added OBI installation support. OBI's current docs describe automatic application observability for Linux HTTP/S and gRPC services, RED metrics, distributed traces, log enrichment, Kubernetes-native deployment, and support across multiple runtimes and protocols. The Go project separately describes tracing instrumentation for Go libraries using eBPF.

Under the hood, these systems are not magic business tracers. They can observe network calls, protocol boundaries, runtime functions, and library calls that are visible from eBPF attachment points. They can emit spans that look like normal OpenTelemetry data and send them toward an OpenTelemetry Collector. They can sometimes propagate or correlate trace context. They usually cannot infer a custom business span named `fraud_check_approved` unless that semantic meaning is visible in a supported protocol, runtime, library, or application metadata path.

The Java comparison is especially important. Traditional OpenTelemetry Java auto-instrumentation is a mature bytecode-agent model, not an eBPF-only model. OBI documentation currently lists Java among supported language environments, but the design and limitations differ from the Java agent that instruments inside the process. For Java services, evaluate whether you need semantic in-process spans from the Java agent, zero-code out-of-process visibility from OBI, or both with careful duplicate-span controls.

Maturity should be stated plainly. bpftrace and BCC are mature operator tools. Inspektor Gadget is active and Kubernetes-focused. OTel eBPF auto-instrumentation is emerging relative to those tools because runtime coverage, kernel requirements, TLS behavior, context propagation, and Collector integration are still moving quickly. That does not make it experimental in every environment, but it does mean a platform standard should start with a pilot, compatibility matrix, overhead measurement, and clear fallback to SDK or language-agent instrumentation.

Use OTel eBPF auto-instrumentation when the organization wants telemetry output, not just terminal evidence. Use it for first-mile visibility into services with no code changes, for migration paths toward OpenTelemetry, and for finding unknown service-to-service calls before application teams add semantic spans. Do not use it as an excuse to avoid manual instrumentation where business context, domain attributes, or custom span boundaries matter.

---

## Operational Workflow: From Symptom to Probe to Decision

An effective ad-hoc tracing session starts outside the tool. Write the symptom in ordinary operational language before choosing the probe: "checkout p99 jumped from normal to painful after 14:05," "pods restart after opening a config file," or "egress to one dependency retries under load." That sentence keeps the session honest. It prevents the common trap where the responder starts browsing every exciting eBPF hook and ends the hour with impressive output but no answer to the incident question.

Next translate the symptom into the smallest observable boundary. File questions usually map to syscall tracepoints such as `openat`, `read`, `write`, `rename`, or `unlink`. Network questions often start with TCP tracepoints, socket tracepoints, DNS gadgets, or SNI gadgets. Process-lifecycle questions map to `execve`, `fork`, `clone`, exit events, or Inspektor Gadget's `trace_exec`. Code-level resource questions should usually go to profiling rather than ad-hoc event tracing, because sampling stacks answer a different question more directly.

After choosing the boundary, list the probes on the target kernel. This is not optional ceremony. It is the difference between "the tool failed" and "this worker image does not expose the event I copied from a newer distribution." For bpftrace, `-l` proves the probe name and `-lv` proves the fields. For BCC, the maintained tool source and your local kernel headers or BTF availability tell you whether the script's assumptions still match the target. For Inspektor Gadget, the current gadget docs and plugin version decide whether you run image-based names such as `trace_exec:latest` or older subcommands.

Start with counts before prints. A count map tells you whether the event is present, whether the rate is plausible, and whether the probe is firing too often. Printing every event is useful only after you know the event volume will not drown the terminal or hide the pattern. A retransmission count by current task, a syscall count by command name, or a top-style gadget summary often gives enough evidence to decide the next step without capturing sensitive strings or overwhelming the node.

Add fields only when they change a decision. If the count proves retransmissions exist, the next decision might require remote address, namespace, pod, or cgroup context. If file opens are the question, the filename may be essential, but reading buffer contents is probably unnecessary and risky. If TLS SNI is enough to identify a dependency, do not escalate to deeper packet capture just because a tool can. The minimum useful field set is a production safety habit, not a limitation.

Stop and summarize quickly. Good tracing evidence has four parts: the exact command, the target host or Kubernetes object, the time window, and the decision the output supports. "Ran the retransmit count on node `worker-a` from 14:17 to 14:19; counts rose only while checkout called inventory; moving to network path and dependency health checks" is much more useful than a screenshot of a terminal full of events. If the output did not answer the question, write that down too, because disproving a hypothesis is progress.

Promote the signal only after the incident. If the same bpftrace command appears in three postmortems, it probably belongs in a maintained BCC tool, an Inspektor Gadget workflow, a Pixie script, an OTel Collector pipeline, or an ordinary application metric. Permanent telemetry should have ownership, dashboards, alert rules, retention, privacy review, and upgrade testing. Ad-hoc eBPF tracing is how you discover a missing signal; it is not how you should operate that missing signal forever.

Treat negative evidence carefully. If a probe sees no events, you have learned only that this probe did not observe the event under the tested conditions. The hook might be wrong, the traffic might use a different syscall path, the workload might be on another node, the kernel might lack the tracepoint, a container runtime boundary might hide the process you expected, or the symptom might have stopped. Negative eBPF evidence is valuable when paired with probe enumeration, workload placement checks, and a known stimulus that should have fired the event.

---

## Production Guardrails for Temporary eBPF Sessions

The most important guardrail is authorization. eBPF tracing tools often require privileges that can observe process names, filenames, network metadata, library calls, and sometimes request-adjacent information. A platform team should decide who can run host bpftrace, who can deploy or invoke Inspektor Gadget, where debug containers are allowed, and how incident evidence containing sensitive metadata is stored. The right answer is not "nobody can debug"; the right answer is a controlled path that responders can use without improvising access during an outage.

The second guardrail is scope. Prefer a lab node, a single affected node, a namespace, a pod, a cgroup, a PID, or a short time window before cluster-wide tracing. A broad probe may be technically correct and operationally careless. In Kubernetes, scope the gadget to a namespace or workload when possible. On a host, use predicates, command filters, cgroup filters, or specific PIDs when the tool supports them. Every unnecessary event is overhead, privacy exposure, and cognitive noise.

The third guardrail is compatibility tracking. Kernel versions, distro backports, BTF availability, lockdown mode, container runtime behavior, and security modules all affect eBPF tool behavior. Keep a short compatibility note for every supported node pool: kernel version, BTF path, bpftrace version, BCC package version, whether `bpftool` is available, whether privileged debug pods are permitted, and whether Inspektor Gadget is installed. This note turns emergency debugging from archaeology into checklist work.

The fourth guardrail is overhead measurement. A one-minute count-only probe is usually cheap, but "usually" is not an SLO. High-frequency hooks, stack collection, string reads, user-stack symbolication, large maps, and broad per-event printing can be expensive. If a command is going into a runbook, test it under load, document expected event rates, and include a stop condition. If a tool has tunables for ring-buffer pages, string length, map keys, or sampling frequency, keep the default conservative until the team has measured the impact.

The fifth guardrail is data handling. Filenames can reveal tenant names, customer IDs, secrets in bad paths, or application internals. SNI values can reveal third-party services and private endpoints. Process arguments can contain tokens if an application is careless. Ad-hoc debugging output should go into the incident record with the same care as logs and traces. Redact when needed, keep retention short, and avoid capturing payloads when metadata answers the question.

The sixth guardrail is cleanup. Temporary BPF programs usually disappear when the tracing process exits, but agents, DaemonSets, debug pods, pinned maps, and shell sessions can outlive the investigation if responders are tired. Make cleanup explicit in the runbook: stop the process, delete the debug pod or lab namespace, undeploy the temporary DaemonSet if it was not already approved as a standing platform component, and record whether any node-local state was intentionally left behind.

The final guardrail is humility about causality. A kernel trace can prove that an event happened, when it happened, and sometimes which task or workload was involved. It does not automatically prove why the event happened or whether users experienced it. Correlate the eBPF evidence with metrics, traces, logs, deployment events, network policy changes, node pressure, and dependency health before writing the incident conclusion. eBPF is powerful because it removes blind spots, not because it removes reasoning.

---

## Team Runbook Pattern for bpftrace, BCC, and Gadgets

A useful platform runbook should not be a pile of favorite commands. It should state the question, the environment requirement, the safe command, the expected healthy shape, the suspicious shape, and the escalation path. For bpftrace, that means a probe-list command, a field-inspection command, the actual one-liner, and a reminder to stop after the time window. For BCC, it means the package requirement, the upstream tool name, the local wrapper if one exists, and the output columns responders should trust. For Inspektor Gadget, it means the namespace and RBAC prerequisites, the gadget image name, the target flags, and cleanup.

Write runbooks in layers. The first layer is the lowest-risk observation, such as a count or top-style summary. The second layer adds identifying metadata, such as namespace, pod, process name, filename, or destination name. The third layer uses heavier capture, stack traces, deeper protocol inspection, or broader scope. Most incidents should stop in the first or second layer. If responders regularly need the third layer, the permanent observability design is probably missing a better signal.

Make version checks part of the command block. A runbook that starts with `bpftrace --version`, `uname -r`, `ls /sys/kernel/btf/vmlinux`, `kubectl gadget version`, or `kubectl -n gadget get pods` feels slower in a demo, but it saves time when a production node differs from the author's laptop. Include the output in the incident notes when the evidence will drive a high-impact decision, such as rolling back, failing over, or escalating to a provider.

Do not hide uncertainty in polished output. A BCC script that prints a neat table can look more authoritative than the underlying probe deserves. If a script depends on kprobe attachment to a kernel function, say so in the runbook. If the current task name in a TCP callback can be misleading under softirq context, say so. If `trace_sni` cannot see encrypted ClientHello, say so. Good platform tooling teaches responders where the evidence is strong and where it is only a clue.

Use cross-links rather than duplication in the curriculum and in internal docs. The permanent Pixie operating model belongs in the Pixie module. The profiling operating model belongs in the continuous profiling module. The eBPF safety model belongs in the fundamentals module. This module should stay focused on imperative, on-demand tracing because that is the gap learners need when an incident question cannot wait for a new dashboard or code deployment.

---

## Common Mistakes and Better Habits

These mistakes are common because the tools are powerful enough to produce convincing output quickly. Treat the table as a pre-flight review before a high-pressure tracing session, especially when the target is a production node or a shared Kubernetes cluster.

| Mistake | Why it hurts | Better habit |
| --- | --- | --- |
| Assuming BTF exists everywhere | Modern typed attachment and field access can fail on older or customized kernels. | Check `ls /sys/kernel/btf/vmlinux`, `bpftool btf`, and tool-specific compatibility docs before the incident. |
| Copying old bpftrace `args->field` syntax blindly | Current bpftrace docs use dot access for tracepoint args, and syntax drift wastes incident time. | Run `bpftrace --version` and `bpftrace -lv` on the target host before pasting examples. |
| Treating kprobes as stable APIs | Kernel function names and signatures can change across kernel versions and distro backports. | Prefer tracepoints when they expose enough information, and record kernel-version assumptions for kprobes. |
| Running broad probes without predicates | High-frequency syscalls or network events can flood output and add avoidable overhead. | Start with counts, filters, namespace scope, cgroup scope, or short timed runs. |
| Forgetting Inspektor Gadget privilege requirements | The DaemonSet needs node-level access, RBAC, and policy exceptions that many clusters restrict. | Approve namespace, service account, Pod Security posture, and allowed users before an incident. |
| Confusing `trace_sni` with TLS decryption | SNI capture only sees visible ClientHello hostnames and can be defeated by encrypted ClientHello. | Use it for destination clues, not payload inspection or guaranteed service identity. |
| Expecting OTel eBPF to replace semantic spans | Kernel and runtime observation cannot infer every business event or custom attribute. | Use OTel eBPF for zero-code visibility and add SDK or language-agent spans for domain meaning. |
| Leaving ad-hoc probes running after the question is answered | Temporary tools become hidden overhead and produce evidence nobody is watching. | Stop the probe, save the command and observation, and decide whether a permanent signal belongs elsewhere. |

---

## Quiz: eBPF Tracing Tools

Use these questions to check whether you can choose the tool and explain the tradeoff, not merely remember commands. The best answers connect the hook, the operating model, the privilege boundary, and the permanence of the signal.

<details>
<summary>1. Your teammate wants to know which files a process opens during the next minute on a Linux lab node. Which tool should you reach for first?</summary>

Use bpftrace first. The question is immediate, narrow, and expressible as a syscall tracepoint one-liner, so a no-daemon terminal probe is lower friction than BCC, Pixie, or OTel eBPF auto-instrumentation. BCC becomes useful if the one-liner grows into a reusable tool, and Pixie or OTel belongs in the conversation only if the team wants broader or persistent telemetry.

</details>

<details>
<summary>2. Why does this module prefer `args.filename` in current bpftrace examples instead of `args->filename`?</summary>

Current bpftrace language and one-liner documentation use dot syntax for tracepoint `args` fields, and `bpftrace -lv` is the supported way to inspect the field names on the target host. Older examples may show arrow syntax, so copying across versions without checking the installed bpftrace release can create a false tool failure during an incident.

</details>

<details>
<summary>3. When should a bpftrace retransmission one-liner turn into BCC or another maintained tool?</summary>

Move beyond the one-liner when you need stable address formatting, IPv6 handling, tail-loss probe support, structured output, state across events, or a command that multiple responders can run without editing shell quotes. The count-only bpftrace probe is a fast hypothesis check, while BCC's maintained `tcpretrans.py` style is better for repeatable TCP retransmission investigation.

</details>

<details>
<summary>4. What Kubernetes-specific problem does Inspektor Gadget solve compared with SSH plus host bpftrace?</summary>

Inspektor Gadget understands Kubernetes objects and enriches gadget output with node, namespace, pod, and container context. That saves responders from manually translating a Kubernetes symptom into host PIDs, container runtime paths, and node-local tracing setup. The tradeoff is that the DaemonSet and RBAC model require explicit platform approval because the tool needs node-level visibility.

</details>

<details>
<summary>5. What is the right expectation for the `trace_sni` gadget?</summary>

Expect destination-name clues from visible TLS Server Name Indication, not decrypted payloads and not guaranteed hostnames in every modern TLS deployment. If encrypted ClientHello hides the SNI, or if the workload does not expose the hostname in the observed handshake, the gadget cannot invent that information. Treat it as one network clue among metrics, DNS traces, and application telemetry.

</details>

<details>
<summary>6. Why is OTel eBPF auto-instrumentation not a full replacement for OpenTelemetry SDK instrumentation?</summary>

OTel eBPF auto-instrumentation can observe supported runtime, library, protocol, and network boundaries without code changes and can emit spans or metrics into an OpenTelemetry pipeline. It usually cannot infer business-specific span names, domain attributes, or custom events that only the application understands. Use it for zero-code coverage and migration help, then keep SDK or language-agent instrumentation for semantic detail.

</details>

<details>
<summary>7. A cluster has Pixie, Parca, and Inspektor Gadget available. Which one best fits a pod that crashes too quickly for interactive debugging?</summary>

Inspektor Gadget's `traceloop` is the best first fit because it is designed as a syscall flight recorder around short-lived or failing workloads. Pixie may still help with always-on traffic and process context, and Parca may help if the issue is resource consumption over time, but crash forensics around the exact system-call sequence is the `traceloop` shape.

</details>

---

## Hands-On Practice: Two Safe First Investigations

Complete these exercises on a Linux lab host and a disposable Kubernetes cluster. Do not run broad syscall traces on a busy shared production node, and do not deploy privileged DaemonSets into a cluster unless you are authorized to do node-level debugging there. The goal is to practice the probe-selection workflow, not to collect the most dramatic output.

- [ ] On a Linux lab host, install bpftrace, list syscall tracepoints with `sudo bpftrace -l 'tracepoint:syscalls:*'`, inspect `sys_enter_openat` with `sudo bpftrace -lv 'tracepoint:syscalls:sys_enter_openat'`, and run the current-docs open-file one-liner for less than one minute.
- [ ] On the same host, list TCP retransmission tracepoints with `sudo bpftrace -l 'tracepoint:tcp:*retrans*'`, inspect `tracepoint:tcp:tcp_retransmit_skb`, and run the count-only retransmission one-liner while a controlled network test or ordinary workload is active.
- [ ] In a disposable `kind` or Minikube cluster, install the `kubectl gadget` plugin, run `kubectl gadget deploy`, create the `exec-demo` BusyBox pod, and observe process execution with `kubectl gadget run trace_exec:latest -n ebpf-lab --podname exec-demo`.
- [ ] Still in the disposable cluster, start `traceloop` or `trace_sni` only long enough to understand the output fields, then remove the lab namespace and undeploy Inspektor Gadget if the cluster is shared.

```bash
kind create cluster --name ebpf-lab
kubectl krew install gadget
kubectl gadget deploy

kubectl create namespace ebpf-lab
kubectl run exec-demo -n ebpf-lab --image=busybox:1.36 --restart=Never -- sleep 3600

kubectl gadget run trace_exec:latest -n ebpf-lab --podname exec-demo
```

```bash
kubectl exec -n ebpf-lab exec-demo -- sh -c 'date; cat /proc/version; sleep 1'

kubectl delete namespace ebpf-lab
kubectl gadget undeploy
kind delete cluster --name ebpf-lab
```

Write down the exact probe or gadget, the kernel version, the node type, the command output you trusted, and the command output you chose not to trust. That note-taking habit matters because ad-hoc tracing produces evidence under local assumptions. If the incident moves to another node pool, distro, or kernel, the same command may attach to different fields, fail to attach, or show a different subset of behavior.

---

## Next Module

Next: [GitOps & Deployments Toolkit](/platform/toolkits/cicd-delivery/gitops-deployments/) continues the platform-tooling path after the observability toolkit, while this module remains the on-demand eBPF companion to Pixie and continuous profiling.

---

## Sources

- [bpftrace official repository](https://github.com/bpftrace/bpftrace)
- [bpftrace one-liners](https://bpftrace.org/one-liners)
- [bpftrace language documentation 0.25](https://bpftrace.org/docs/release_025/language)
- [bpftrace command-line documentation 0.25](https://bpftrace.org/docs/release_025/cli)
- [BCC official repository](https://github.com/iovisor/bcc)
- [BCC installation guide](https://github.com/iovisor/bcc/blob/master/INSTALL.md)
- [BCC reference guide](https://github.com/iovisor/bcc/blob/master/docs/reference_guide.md)
- [BCC tcpretrans tool source](https://github.com/iovisor/bcc/blob/master/tools/tcpretrans.py)
- [Inspektor Gadget quick start](https://inspektor-gadget.io/docs/latest/quick-start/)
- [Inspektor Gadget Kubernetes installation](https://inspektor-gadget.io/docs/latest/reference/install-kubernetes/)
- [Inspektor Gadget trace_exec gadget](https://inspektor-gadget.io/docs/latest/gadgets/trace_exec/)
- [Inspektor Gadget traceloop gadget](https://inspektor-gadget.io/docs/latest/gadgets/traceloop/)
- [Inspektor Gadget trace_sni gadget](https://inspektor-gadget.io/docs/latest/gadgets/trace_sni/)
- [OpenTelemetry eBPF Instrumentation documentation](https://opentelemetry.io/docs/zero-code/obi/)
- [OpenTelemetry eBPF Instrumentation repository](https://github.com/open-telemetry/opentelemetry-ebpf-instrumentation)
- [OpenTelemetry Go automatic instrumentation repository](https://github.com/open-telemetry/opentelemetry-go-instrumentation)
- [Splunk OpenTelemetry Collector releases](https://github.com/signalfx/splunk-otel-collector/releases)
