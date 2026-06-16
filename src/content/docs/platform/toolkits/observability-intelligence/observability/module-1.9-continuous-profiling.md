---
revision_pending: false
title: "Module 1.9: Continuous Profiling - The 4th Pillar of Observability"
slug: platform/toolkits/observability-intelligence/observability/module-1.9-continuous-profiling
complexity: "[MEDIUM]"
time_to_complete: "60-75 minutes"
prerequisites: "Module 1.1: Prometheus; Module 1.2: OpenTelemetry; Module 1.5: Distributed Tracing; Basic Kubernetes 1.35 workload operations"
sidebar:
  order: 10
---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Explain continuous profiling as the fourth observability signal that connects service-level symptoms to the exact functions, stack frames, and allocation paths consuming resources in production.**
- **Compare eBPF whole-system profiling, in-process SDK profiling, and ad-hoc language profilers so you can choose a collection strategy that matches risk, labels, and runtime depth.**
- **Read flame graphs and differential profiles to identify CPU, memory, goroutine, lock, and blocking regressions between time windows, releases, or workload versions.**
- **Deploy Parca or Pyroscope as worked examples while keeping the durable mental model focused on always-on sampling, labels, retention, tenancy, and operational workflow.**
- **Integrate profiles with metrics and traces so a platform team can move from "which service is slow" to "which code path changed" without rebuilding the incident from scratch.**

## Why This Module Matters

Hypothetical scenario: A platform team owns a checkout service that usually runs at comfortable headroom, but a routine release pushes several pods close to their CPU limit during the evening peak. Metrics show utilization climbing from around half of a core to around two cores per replica, traces show that the checkout handler is slower, and logs show no useful error because the service is still technically succeeding. The team can roll back, raise limits, or stare at code reviews, but none of those actions explains which function changed the resource curve. A continuous profile from the same time window shows a new request-normalization helper dominating CPU samples, and a diff against the previous release makes the regression obvious enough to fix deliberately.

That scenario is why profiling belongs beside metrics, logs, and traces in a mature observability practice. Metrics tell you that a resource or service-level objective is drifting. Traces tell you where a request spent wall-clock time across services. Logs tell you what a program chose to record at particular moments. Profiles show what code actually consumed CPU, allocated memory, held locks, blocked goroutines, or waited off CPU while the program was running. They do not replace the other signals; they make the final step of performance debugging less dependent on guesswork, reproduction luck, and heroic familiarity with every line of the codebase.

The durable shift is the word "continuous." Traditional profiling is often ad hoc: a developer reproduces a problem locally, captures a short `pprof` file, or attaches a profiler to one process after an incident has already started. That workflow is useful, but it is late and selective. Continuous profiling samples production systems all the time at a low enough rate to keep overhead acceptable, then stores those samples with useful labels so teams can compare a quiet baseline, a busy hour, and a new deployment after the fact. The value is not just a flame graph; it is the ability to ask historical questions about code-level resource use.

The "fourth pillar" phrase can sound like marketing if you treat pillars as products. Treat it instead as a diagnostic boundary. Metrics aggregate behavior, traces follow transactions, logs preserve chosen events, and profiles summarize runtime execution. A latency alert may say the payment API is slow, and a trace may isolate a span inside the authorization service, but a CPU profile can show whether the cost is JSON encoding, regex compilation, TLS handshakes, lock contention, garbage collection pressure, or an unexpectedly expensive library call. That distinction turns an incident from "the service is slow" into "this call stack got wider after this deploy."

Continuous profiling also changes how teams talk about efficiency. Without profiles, cost discussions often collapse into coarse actions such as raising CPU requests, splitting services, adding replicas, or rewriting hot paths because a senior engineer has a suspicion. Profiles let you rank resource consumption by code path before you choose a remedy. Sometimes the answer is to optimize a function, sometimes it is to cache a result, sometimes it is to lower allocation churn, and sometimes it is to accept the cost because the work is essential. The important practice is that you make those tradeoffs with runtime evidence instead of folk memory.

This module uses Parca and Grafana Pyroscope as worked examples because they expose the main capability axes you will see across the profiling ecosystem. Parca emphasizes always-on eBPF collection and a label model that feels familiar to Prometheus users. Pyroscope emphasizes a Grafana-native, multi-tenant profiling backend with SDK, scrape, and OpenTelemetry ingestion paths. Those details will change over time, so the teaching spine is not "pick a winner." The spine is always-on sampling, trustworthy labels, readable flame graphs, diffable history, and integration with the signals your incident workflow already uses.

## Continuous Profiling as the Fourth Signal

Observability starts with questions, not tools. When an alert fires, the first question is usually whether the system is unhealthy, and metrics are excellent at answering that with rates, errors, duration, saturation, and resource gauges. The next question is often which service, endpoint, dependency, or queue is involved, and traces are excellent at showing the path of one request through a distributed system. Logs help when the program emitted a useful event, especially if the event carries request IDs, user-safe context, or domain-specific state. Profiling answers a different question: while the program was serving real traffic, which code paths consumed the resources that made the symptom visible?

That question matters because performance failures hide below service boundaries. A trace span named `POST /checkout` can be slow for many reasons: serialization, database driver behavior, retry loops, DNS resolution, lock contention, memory allocation pressure, encryption, queue waits, or a library update. A metric can show CPU saturation, but not which stack was running when the CPU burned. A log can say an operation exceeded a deadline, but not what the scheduler, runtime, allocator, or call stack was doing before the deadline. A profile turns runtime behavior into aggregated evidence that engineers can inspect at the function level.

The simplest mental model is a camera taking frequent snapshots of stack traces. At a regular interval, the profiler asks "what is this thread, goroutine, process, or CPU doing right now?" Each answer is a stack sample. After many samples, the profiler aggregates repeated stacks and shows the total shape of work. If one function appears in many CPU samples, it probably consumed a meaningful share of on-CPU time. If one allocation site appears in many heap or allocation samples, it probably creates memory pressure. If many goroutines are parked on a mutex or channel, the profiler can reveal contention that looks like ordinary latency from the outside.

The fourth-signal idea becomes practical when profiles are labeled and retained. A one-off profile file from a developer laptop can be useful, but it cannot answer whether a production regression started at deploy time, only affects one namespace, or appears on a particular node architecture. Continuous profilers attach labels such as service, namespace, pod, container, version, environment, node, language runtime, and sometimes trace or span identifiers. Those labels let you filter a large body of samples into the operational slice you care about, then compare that slice with another time window or deployment.

The analogy is medical imaging. Metrics are vital signs, traces are the path a patient took through the clinic, logs are notes in the chart, and profiles are an image that shows where the body is actually using energy or experiencing blockage. A doctor would not order imaging for every question, and an engineer should not open profiles for every alert. But when the question is "which code is burning cycles, allocating memory, or waiting on a lock," the other signals can only point you toward the area. The profile shows the shape of the work itself.

This boundary keeps profiling from becoming a dumping ground for all performance debugging. Profiles are strongest when a symptom has already been scoped to a workload, endpoint, release, or time window. If you have no idea whether the problem is user traffic, a batch job, an upstream dependency, or a noisy neighbor, start with metrics and traces. Once those signals isolate a target, use profiling to decide whether the target is doing necessary work, wasteful work, duplicate work, or blocked work. That sequence keeps the incident workflow calm and avoids opening the most detailed tool before you know what to ask.

## How Sampling Profilers Work

Most continuous profilers use statistical sampling rather than tracing every function call. The difference is important. Instrumenting every function entry and exit can produce beautiful detail, but the overhead and data volume are usually too high for always-on production use. Sampling accepts that each individual snapshot is incomplete, then relies on a steady stream of snapshots to build a statistically useful picture over time. A hot function appears often because it is on the stack often. A cold function may be missed in a short window, but that is an acceptable tradeoff when the goal is low-overhead fleet visibility.

For CPU profiles, a sampling profiler typically interrupts execution or observes scheduler/perf events at a configured rate and records the current call stack. The stack is a chain of frames from the current function back through its callers. If the profiler collects thousands of samples over a representative interval, it can aggregate identical or similar stacks and estimate where CPU time went. The estimate is not a perfect ledger of every instruction; it is a map of where the program spent enough time to be sampled repeatedly. That is exactly the map you need when a small number of hot paths dominate resource use.

Memory profiles measure a different kind of cost. A heap profile may describe live objects, while an allocation profile may describe where allocations occurred over time, even if some objects were later freed. Those two views answer different questions. If memory usage keeps rising, live heap can identify retained objects and possible leaks. If garbage collection is expensive even though live memory remains stable, allocation profiling can identify short-lived objects that churn through the allocator and collector. Treat "memory is high" as an incomplete symptom until you know whether the problem is retained memory, allocation rate, fragmentation, or runtime overhead.

Concurrency profiles are especially useful in Go and JVM-heavy environments because latency can come from waiting rather than active CPU. A goroutine profile shows where goroutines currently sit. A mutex profile shows where lock contention costs accumulate. A block profile can reveal waiting on channels or other blocking operations. Off-CPU profiling generalizes this idea by asking where execution was waiting while not running on CPU. These profiles are easy to misuse if you read them like CPU flame graphs, because "wide" may mean "waited often" rather than "burned CPU." The practice is to match the profile type to the symptom before interpreting width as waste.

Sampling keeps overhead low because the profiler observes periodically instead of recording every event. That does not mean overhead is zero or that every runtime behaves the same. Higher sample rates create more detail and more cost. Deeper stack unwinding creates better attribution and more work. Symbolization, label enrichment, compression, retention, and query fan-out also consume resources in the profiling backend. The operational target is not "free." The target is "cheap enough to leave enabled so the evidence exists when the incident begins." Continuous profiling is valuable precisely because you cannot always reproduce production timing later.

Stack unwinding is the technical work that turns a sampled instruction pointer into a useful call stack. Compiled languages may expose frame pointers, DWARF debug information, or runtime-specific metadata. Interpreted runtimes may require language-aware unwinding to recover Python, Ruby, JVM, or JavaScript frames rather than only native interpreter frames. Containerized workloads add another layer because symbol files and build IDs may live in images, debug packages, or artifact stores. When a profiler shows `[unknown]` frames, that is not cosmetic. It means the tool can see time being spent but cannot yet translate it into code a team can act on.

Aggregation is where raw samples become a debugging interface. The profiler groups stack traces, applies labels, stores profiles over time, and exposes queries. A production system with hundreds of pods does not need hundreds of unrelated profile files; it needs a way to ask for `service=checkout`, `namespace=prod`, `version=2026.06.12`, and `profile_type=cpu` over a meaningful interval. That query should produce a readable result, and the same label vocabulary should support comparisons across versions, namespaces, tenants, and nodes. This is why profiling tools often borrow ideas from metrics systems: labels are how runtime samples become operational data.

The most important habit is to read sampled profiles probabilistically. A flame graph that says a function accounts for a large share of samples is telling you where to investigate first, not proving that deleting that function will improve user latency by the same percentage. Maybe the function is necessary work, maybe it appears wide because its children are expensive, or maybe traffic mix changed during the window. Sampling gives you a strong clue, and diffing gives you an even stronger clue when one code path got wider after a release. The engineering step is still to connect the observed stack to the service behavior and validate the fix.

## Reading Flame Graphs and Profile Types

A flame graph is an aggregated picture of stack samples. Each rectangle is a stack frame, and the rectangles above it are functions it called. Width represents cumulative samples for that frame and its children, not elapsed time from left to right. The x-axis is a space-filling layout, often sorted to make repeated stacks line up; it is not a timeline. The y-axis is stack depth. The useful question is not "what happened first?" but "which stacks occupy the most area, and which leaf functions or callers explain that area?"

For CPU profiles, wide towers usually show where on-CPU execution accumulated. Start by finding broad plateaus near the top because they often represent leaf functions doing work rather than merely calling other functions. Then walk downward to understand the caller path that reached them. A wide `encoding/json` frame under one handler has a different remediation path than the same frame spread across every handler. The bottom frames explain ownership and request path; the top frames explain the expensive work. Good profile reading moves between both levels instead of staring only at the widest colored box.

For memory allocation profiles, the same visual grammar can mislead you if you forget the sample type. A wide allocation frame does not mean CPU time was spent there; it means many sampled bytes or objects were allocated there. The remedy might be pooling, reducing intermediate objects, streaming instead of buffering, caching compiled patterns, or accepting that allocation is unavoidable for a particular request. For live heap, width can mean retained memory rather than allocation churn. That distinction matters because a high allocation rate can increase garbage collection pressure without leaving a large retained heap, while a leak can grow retained heap without obvious CPU hotspots.

For goroutine, mutex, block, and off-CPU profiles, width often points to waiting, accumulation, or contention. A goroutine profile may show many goroutines parked in a channel receive, which could be normal for workers or pathological if a sender died. A mutex profile may show a small critical section causing many callers to wait under concurrency. An off-CPU profile may show that requests are not slow because they burn CPU, but because they spend time in I/O, kernel scheduling, or runtime blocking states. These profiles are powerful when paired with traces because a slow span can be explained by CPU work or by waiting.

Profile type selection should follow the symptom. If CPU saturation is the alert, start with CPU samples. If memory limits or garbage collection pauses are the pain, compare live heap and allocation profiles. If latency rises while CPU remains flat, look at traces first, then consider wall-clock, block, mutex, goroutine, or off-CPU profiles. If a single runtime exposes language-specific profiles, use them when they map to the problem. If the problem crosses many languages on one node, whole-system eBPF profiles may provide the broadest starting point even if they need extra symbol work for perfect attribution.

The `pprof` family of formats and tools is worth understanding because many profilers either emit pprof-compatible data or can ingest it. In Go, `runtime/pprof` and `net/http/pprof` provide built-in ways to expose CPU, heap, goroutine, block, mutex, and related profiles. That does not make ad-hoc `pprof` the same as continuous profiling. The difference is operational: an ad-hoc profile is a snapshot you remembered to take, while continuous profiling retains a labeled history. Still, learning pprof locally is one of the easiest ways to build intuition before you read fleet profiles in Parca or Pyroscope.

The first visual anti-pattern is treating color as meaning. In many flame graphs, color is chosen to distinguish frames visually, not to mark danger, ownership, or severity. Diff flame graphs are different because color often marks change between two profiles, such as increased or decreased sample share. The second visual anti-pattern is treating the left side as earlier and the right side as later. Flame graphs compress stacks by shape, not by clock order. The third is optimizing the first wide frame you see without asking whether it is necessary business logic, runtime overhead caused by another allocation pattern, or a symptom of changed traffic.

The strongest practice is to pair every flame graph observation with a falsifiable next step. If `compressPayload` dominates CPU after a release, check whether payload size changed, whether compression settings changed, and whether the function is present in the previous release profile. If `regexp.Compile` appears wide, verify whether a regex is compiled per request and write a benchmark for caching it. If allocation profiles show repeated buffer growth, reproduce with representative payloads and measure the change. Profiling narrows the search space; disciplined engineering still validates the conclusion.

## eBPF Whole-System Profiling and In-Process Profiling

The major collection-axis decision is where the profiler observes execution. In-process profilers run inside the application process through a language SDK, runtime endpoint, Java agent, Go `pprof`, Python package, or similar mechanism. They can expose rich runtime-specific data because they understand the language environment from inside. They can also attach useful application labels directly, such as tenant, endpoint, build version, or feature flag. The tradeoff is operational reach: every language and service may need its own configuration, and missing instrumentation creates blind spots.

eBPF whole-system profiling observes from the Linux kernel side. An eBPF profiler can run as a privileged node agent and sample processes across the host, including containers, without adding an SDK to each application. That is a durable capability shift for platform teams because it changes profiling from "convince every service owner to instrument" into "collect a baseline across the node fleet." It is especially attractive in heterogeneous clusters where Go, Java, Python, Ruby, Rust, C++, and third-party workloads share nodes. You can discover hotspots before every team has adopted a profiling library.

The eBPF approach has its own constraints. The agent needs kernel access and permissions that security teams must review carefully. Stack unwinding can be harder because the profiler observes from outside the runtime and may need frame pointers, DWARF information, runtime-specific unwinders, debug symbols, or build IDs to produce names that developers recognize. Some language runtimes move stacks, JIT code, or interpreter frames in ways that require special support. A whole-system profile with unknown frames can still reveal that a process burns CPU, but it may not immediately tell the owning team which source line changed.

In-process profiling has the opposite shape. It usually requires code, configuration, or runtime agent changes, but it can produce deeper labels and runtime-specific views. A Go service can expose goroutine, heap, mutex, and block profiles through `net/http/pprof`. A JVM service can use Java profiling agents that understand JIT and allocation behavior. A Python service may expose wall-clock profiles that capture interpreter-level stacks. Those profiles can be linked to application metadata more directly than a kernel-only view. The tradeoff is that platform coverage depends on adoption, and misconfigured endpoints can become security risks if exposed broadly.

The practical answer is often layered rather than either-or. Start with eBPF whole-system profiling when you need broad coverage, unknown workload discovery, or a low-friction baseline across Kubernetes nodes. Add in-process profiling for critical services where language-specific detail, span labels, tenant labels, allocation types, or runtime contention profiles matter. Keep ad-hoc pprof or local profilers in the developer toolbox for reproduction and fix validation. The collection strategy should follow risk and question shape, not tool enthusiasm.

Kubernetes adds another operational boundary: labels. A node-level profiler must enrich raw process samples with pod, namespace, container, image, node, and workload metadata, or the data will be too anonymous for service teams to use. An in-process profiler must attach service and version labels consistently, or profiles will be hard to compare across releases. The label model is the contract between runtime samples and platform operations. If labels are inconsistent, teams will argue about ownership instead of reading the profile.

Security review is not optional for either approach. eBPF agents commonly need elevated privileges to load programs and inspect host processes. In-process `pprof` endpoints can expose sensitive stack, path, and memory information if bound to public interfaces. SDK profilers may send code symbols, package names, paths, labels, and sometimes tenant context to a backend. A production profiling rollout should define who can query profiles, how long profiles are retained, which labels are allowed, how symbol files are handled, and whether profile data is covered by the same privacy and compliance rules as logs and traces.

The durable engineering question is: what is the minimum collection method that gives you trustworthy attribution for the decision you need to make? If you only need to know which service version doubled CPU on a node pool, eBPF with good Kubernetes labels may be enough. If you need to know which customer plan triggers a Python allocation spike, you probably need in-process labels and careful privacy controls. If you need to prove a one-line optimization worked, a local or CI benchmark profile may be clearer than a fleet-wide view. Tool selection is a consequence of the diagnostic question.

## Differential Profiling and Release Workflows

Continuous profiling becomes operationally powerful when you compare two profiles. A single flame graph tells you where resources went during one window, but a diff tells you what changed. That change can be between two releases, a canary and a stable deployment, a quiet period and an incident window, two Kubernetes namespaces, two node images, or two configuration states. The diff view is the bridge between profiling and CI/CD because most platform incidents are not mysteries in isolation; they are regressions relative to a known baseline.

A differential flame graph usually highlights functions that grew or shrank between profiles. The exact color scheme depends on the tool, but the practice is stable: define a baseline, define a comparison, and inspect the frames with meaningful deltas. If a deployment added CPU cost, the changed frames often appear far faster in a diff than in two side-by-side flame graphs. If a memory optimization worked, allocation paths should shrink. If a runtime upgrade moved cost from application code into garbage collection, the diff can show that the symptom changed shape rather than disappeared.

The hardest part of differential profiling is choosing fair windows. Comparing a weekday peak to a weekend idle period can produce dramatic but useless differences. Comparing one release serving checkout traffic to another release serving a batch backfill can blame the wrong code. A good comparison keeps traffic mix, time range, labels, and load close enough that the change is plausible. For release analysis, compare the same service, endpoint if possible, namespace, and similar load windows before and after the deployment. When traffic cannot be controlled, use traces and metrics to explain the traffic mix before trusting the diff.

Canary releases are a natural fit. If ten percent of traffic runs version B and the rest runs version A, profiles can be filtered by version label and compared during the same wall-clock interval. That removes many traffic and time-of-day confounders. If version B shows a new allocation hotspot or a much wider CPU path under the same endpoint, you can stop the rollout before the regression becomes a fleet-wide problem. This is one of the places where profiling pays for the label discipline required to make it useful.

Performance budgets also become more concrete with profiles. A service-level objective may define availability or latency, but a platform team can add guardrails for resource regressions during release review. For example, the release process can ask whether CPU samples for critical handlers changed materially, whether allocation paths grew unexpectedly, or whether lock contention appeared under canary traffic. The gate should not be a simplistic "no function got wider" rule because real features do more work. The gate should require explanation for meaningful changes in code-level resource shape.

Diffs are also useful outside deployments. If one node pool shows higher CPU than another, compare profiles by node label and look for kernel, runtime, or workload differences. If one tenant reports latency but global metrics look normal, compare tenant-scoped profiles if tenant labels are allowed and privacy-reviewed. If a cost optimization moved workloads to a different instance type, compare profiles before and after the migration to see whether CPU savings were offset by lock waits, cache misses, or runtime behavior. Continuous profiling gives you a historical microscope for infrastructure changes as well as application releases.

The common failure mode is treating a profile diff as a verdict instead of a lead. A wider function after a deploy may be the regression, but it may also be a symptom of different input sizes, a shifted endpoint mix, or work that was previously done elsewhere. The responsible workflow is to use the diff to identify a candidate, then verify with code review, targeted benchmarks, load tests, or a second production window. Profiles shorten the search dramatically, but they do not remove the need for engineering judgment.

## Worked Examples: Parca and Pyroscope

Parca is a useful worked example for platform-wide profiling because it centers on always-on collection and a label-oriented query model. The Parca project describes itself as continuous profiling that collects, stores, and makes profiles queryable over time, while Parca Agent is documented as an always-on eBPF sampling profiler that can observe user-space and kernel-space stacks. In Kubernetes, that maps naturally to a server that stores and queries profiles plus node agents that collect samples and enrich them with metadata. The durable capability is broad coverage: get profiling data for workloads before each application team has completed SDK integration.

The Parca mental model feels familiar if you already operate Prometheus. Targets and labels matter, profile samples become time-scoped data, and the useful queries are filtered by dimensions such as namespace, pod, container, job, process, node, or service. That does not make profiles metrics; a profile is structured stack data rather than a scalar time series. But the operational ergonomics are similar enough that platform teams can reuse habits: consistent labels, careful cardinality, retention choices, and dashboards or links that start from an alert and land in the right slice of data.

Pyroscope is a useful worked example for teams that already use Grafana for exploration and correlation. Grafana's current Pyroscope documentation describes it as an open source continuous profiling project and a multi-tenant profiling aggregation system that integrates with Grafana so profiles can be correlated with metrics, logs, and traces. That makes the key capability less about one collection path and more about backend workflow: store profiles centrally, query them by labels, visualize flame graphs in the same environment used for other signals, and support tenant isolation when multiple teams share the service.

Pyroscope also illustrates why the profiling landscape moves quickly. Grafana Labs acquired Pyroscope in 2023 and merged it with Grafana Phlare under the Grafana Pyroscope name. In April 2026, Grafana announced Pyroscope 2.0 as a ground-up rearchitecture of the open source profiling database, with v2 storage becoming the default in the 2.0 release notes and native support for OTLP profiling. Those are important current facts, but they are volatile implementation facts. The durable lesson is not "memorize the latest Pyroscope architecture." The lesson is to check whether your profiling backend supports your scale, retention, tenancy, ingestion, and correlation requirements today.

The two projects are peers that emphasize different axes. Parca is a clean way to teach eBPF whole-system profiling, Kubernetes labels, and Prometheus-flavored operations. Pyroscope is a clean way to teach a profiling backend integrated into Grafana workflows, multi-tenancy, SDK ingestion, scrape-style ingestion, and OpenTelemetry-oriented ingestion. You can run one, the other, both, or a commercial backend depending on constraints. The comparison should stay capability-based: how profiles are collected, how labels are attached, how data is stored, how diffs work, how access is controlled, and how engineers pivot from an alert to a profile.

Language `pprof` remains part of the Rosetta even if you adopt Parca or Pyroscope. A Go service exposing `net/http/pprof` can be scraped or queried directly, and `runtime/pprof` teaches the underlying profile types. Local pprof remains useful for validating a fix under controlled input. The difference is that pprof alone is not a fleet workflow. It has no inherent Kubernetes label model, no central retention, no cross-release comparison unless you build one, and no automatic link from a production alert. Continuous profiling systems operationalize the profile data that language runtimes already know how to produce.

Commercial APM profilers appear in many organizations because teams want managed storage, language agents, access control, and integration with existing paid dashboards. They are legitimate peers in the capability comparison, but avoid treating vendor convenience as a technical proof. A managed profiler may reduce operational burden and add support for particular runtimes, while a self-hosted profiler may give more control over data residency, cost model, and labels. The decision should be explicit: what data leaves the cluster, who can query it, which languages are supported deeply, how pricing scales, and whether the backend can represent the comparisons your release process needs.

## OpenTelemetry Profiles and Signal Correlation

OpenTelemetry is the important standardization story to watch, but precision matters. OpenTelemetry itself is a CNCF graduated project as of May 2026, while the Profiles signal is documented as alpha and under active development. The project has been adding profiles as another signal alongside traces, metrics, and logs, but alpha status means teams should expect changes and verify collector, SDK, protocol, and backend support before relying on details. Do not describe OpenTelemetry profiling as stable or generally available. Describe it as the emerging cross-vendor profiling path that is becoming easier to test.

The durable value of OpenTelemetry profiles is interoperability. Without a common model, each profiler can use its own format, labels, ingestion protocol, and correlation conventions. That creates lock-in and translation work. A profile signal in OpenTelemetry can give producers and backends a shared language for samples, mappings, stack traces, attributes, resources, and links to other signals. Even if the details continue to change, the direction is clear: profiles should be collected, processed, routed, and correlated through observability pipelines rather than treated as isolated files.

Correlation is the operational payoff. A trace tells you a particular request had a slow span. A span-to-profile link can help you inspect CPU or wall-clock samples that overlapped that span or trace. A metric exemplar can help you pivot from a latency spike to a representative trace, and then from the trace to a profile. A log line with a trace ID can provide domain context, while the profile explains runtime cost. The ideal workflow is not four separate tabs; it is a series of pivots that preserve time range, service, environment, version, and request context.

There are limits to this vision. Profiles are aggregated samples, while traces are request-scoped records. Joining them perfectly can be difficult because sampling windows, runtime threads, goroutines, async execution, and context propagation do not always align neatly. A profile may show all CPU used by a process while one trace represents one request. Some tools support span profiles for particular languages or runtimes, while whole-system eBPF profilers may need trace correlation support to connect kernel-observed samples back to request context. Treat correlation as a powerful workflow when available, not as a magic guarantee.

The OpenTelemetry Collector is likely to become an important control point because platform teams already use it to receive, process, and export telemetry. For profiling, the same pipeline questions apply: where do agents send data, which attributes are kept, how are tenants separated, how is sensitive metadata removed, what is sampled or dropped, and which backends receive profiles. The difference is that profile payloads and symbol data can be large, so collector sizing and backend economics need their own testing. Reusing the collector does not eliminate capacity planning.

For a platform team, the right posture is active monitoring rather than premature dependence. Track the OpenTelemetry profiles specification, collector support, backend support, and SDK maturity. Run small experiments for services where profiling correlation would materially improve incident response. Avoid building irreversible platform contracts around alpha fields. When a vendor says it supports OTLP profiles, verify which profile types, languages, labels, and correlation features actually work with your collector and backend versions. The standardization direction is promising, but production contracts require version-specific evidence.

## Landscape Snapshot and Rosetta

> **Landscape snapshot - as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.** Parca is a Polar Signals project with an Apache-2.0 licensed repository, and its current documentation describes Parca Agent as an always-on eBPF sampling profiler. Grafana Pyroscope is Grafana Labs open source software; Grafana acquired Pyroscope in 2023, merged it with Phlare, and announced Pyroscope 2.0 on 2026-04-21 as a rearchitecture with OTLP profiling support. OpenTelemetry is a CNCF graduated project, but the OpenTelemetry Profiles signal is alpha, so profile schemas and implementations should be treated as active-development surfaces. The CNCF project catalog lists OpenTelemetry and does not list Parca or Pyroscope, so this module treats Parca and Pyroscope as vendor OSS projects rather than CNCF projects.

This snapshot is intentionally quarantined because tool facts age quickly. A module about continuous profiling should not depend on a chart version, an acquisition headline, or a maturity badge to teach the durable practice. You still need those facts when making a production decision, because license, tenancy, protocol status, and deployment mode can change operational risk. The pattern is to place current facts in a dated section, cite primary sources, and keep the main body focused on capabilities that will remain useful when the product pages change.

| Durable capability | Parca | Grafana Pyroscope | Language `pprof` | Commercial APM profiler |
|---|---|---|---|---|
| eBPF whole-system profiling | Core worked example through Parca Agent and Kubernetes node collection | Supported through OpenTelemetry eBPF profiler ingestion paths in current docs | Not a whole-system model by itself | Varies by vendor and agent design |
| In-process SDK profiling | Possible through profile ingestion, but not the main teaching axis here | Common path through language SDKs, agents, scrape, and Grafana Alloy options | Native for Go and similar runtime-specific tools | Often the main collection path |
| Flame graph exploration | Built into Parca UI and query workflow | Built into Pyroscope and Grafana profile exploration | Available through `go tool pprof` and related viewers | Usually built into vendor UI |
| Differential comparison | Core operational workflow for time windows and releases | Core operational workflow for time windows and releases | Manual unless you store and compare files yourself | Usually available, details vary |
| OTLP profiling | Watch current support and OTel eBPF profiler direction | Current docs and Pyroscope 2.0 materials emphasize OTLP profiling ingest | Not an OTLP pipeline by itself | Varies by vendor and collector integration |
| Multi-tenancy | Design depends on deployment and access-control choices | Documented as a multi-tenant profiling aggregation system | Not provided by local pprof alone | Usually part of managed platforms |

The Rosetta is not a scorecard. It is a translation table between durable needs and tool shapes. If your platform requirement is "profile every process on a node with minimal application changes," the eBPF row matters. If the requirement is "attach request, tenant, and runtime-specific labels from inside the service," the in-process row matters. If the requirement is "let many teams share a backend without reading each other's data," the tenancy row matters. The right answer is the one whose tradeoffs match your operational constraints.

## Operating Model for Production Profiling

A production profiling rollout should start with an explicit question set. Decide whether the first goal is cost visibility, release regression detection, memory leak investigation, incident response, runtime education, or capacity planning. The goal shapes collection, retention, and user experience. A cost-visibility rollout may prioritize broad CPU and allocation coverage across namespaces. A release-regression rollout may prioritize version labels and diff views. An incident-response rollout may prioritize trace pivots and low-friction access for on-call engineers. A memory leak rollout may prioritize heap profiles and symbol quality.

Label governance is the first platform contract. At minimum, profiles should carry service, namespace, workload, pod, container, environment, version, and node labels where applicable. If you allow tenant, user segment, endpoint, or feature labels, review privacy and cardinality carefully. High-cardinality labels can make profile storage and query paths expensive, and sensitive labels can turn profiles into regulated data. Keep the same naming discipline used for metrics and traces. A profile without trustworthy labels is a pile of stack traces; a profile with good labels is a production debugging asset.

Access control is the second contract. Profiles can expose package names, source paths, function names, dependency choices, and workload behavior. In some languages, profile labels may include request context if teams add it without review. Treat profile access like access to logs and traces, not like access to a harmless dashboard. Define who can query production profiles, whether teams can see only their namespaces, how break-glass access works during incidents, and how long profile data is retained. Multi-tenancy is not only a backend feature; it is an operational promise.

Symbol management is the third contract. Engineers cannot optimize `[unknown]` frames. For compiled code, decide whether builds preserve frame pointers, whether debug symbols are available, how build IDs map to artifacts, and how container images expose enough metadata for unwinding. For interpreted languages, verify that the profiler can recover language-level frames rather than only interpreter internals. For JIT runtimes, test representative workloads rather than assuming documentation covers your exact version. A profiling backend can be correctly deployed and still produce weak evidence if symbolization is neglected.

Overhead testing is the fourth contract. Sampling is designed to be low overhead, but every environment is different. Measure agent CPU, memory, network, storage, query cost, and application impact during a controlled rollout. Test at realistic pod density and traffic mix, not only on a toy cluster. Watch for kernel compatibility, runtime support, debug-symbol upload cost, and collector pressure if OTLP profiles are involved. The point of continuous profiling is to leave it on, so the rollout is only successful if the overhead remains acceptable during normal operation and incidents.

Retention should match the questions you plan to ask. If you only retain profiles for a few hours, you can debug active incidents but not weekly release regressions. If you retain profiles for months, storage, privacy, and query economics matter more. Many teams choose shorter high-resolution retention for incident debugging plus longer aggregated retention for trend and regression analysis. Whatever the policy, make it explicit. Engineers need to know whether they can compare this morning's canary with last week's baseline before they promise that workflow in a runbook.

Finally, train teams to use profiles as part of the incident path. A dashboard link that lands in a profile view is useful only if on-call engineers know how to read it. Practice with known hotspots, synthetic load, and post-release comparisons before the first real incident. Write examples that show how a metric alert pivots to traces and then to profiles. Record the difference between CPU, allocation, heap, mutex, block, and goroutine profiles in your local runbooks. The goal is not to create profiling specialists; it is to make code-level evidence normal during performance debugging.

## Patterns & Anti-Patterns

Patterns are the repeatable practices that make continuous profiling more than another dashboard. The first pattern is baseline-first profiling: keep profiles enabled during normal operation so every incident and release has a comparison window. The second pattern is label-aligned profiling: make service, version, environment, namespace, and workload labels consistent with metrics and traces. The third pattern is diff-driven release review: compare profiles across canaries, stable deployments, and rollback windows when performance changes. The fourth pattern is trace-to-profile pivoting: use traces to scope the request path, then profiles to inspect the code path.

Anti-patterns usually come from treating profiles as either too magical or too dangerous. The first anti-pattern is incident-only profiling, where a team enables profiling after a regression and discovers there is no baseline. The second is unowned profiles, where a platform team collects stack data but does not provide labels, access rules, or training, so service teams ignore it. The third is screenshot debugging, where someone pastes a flame graph into chat without the query, time range, labels, profile type, or comparison window. The fourth is optimization theater, where engineers change the widest function without proving it affects the user-visible symptom.

| Decision point | Choose this direction when... | Be careful about... |
|---|---|---|
| eBPF whole-system first | You need broad Kubernetes coverage, unknown workload discovery, and low application-team adoption friction | Kernel permissions, symbol quality, runtime-specific unwinding, and security review |
| In-process SDK first | You need language-specific profiles, request labels, tenant labels, or deep runtime views | Adoption burden, endpoint exposure, label privacy, and per-language support gaps |
| Parca-style self-hosting | You want platform-owned profiling with strong eBPF and label-oriented operations | Running and upgrading storage, UI, access control, and symbol pipelines yourself |
| Pyroscope-style Grafana workflow | You want profiles close to Grafana metrics, logs, traces, and multi-tenant exploration | Backend scale, object storage, chart changes, and version-specific OTLP support |
| Commercial managed profiler | You want managed operations and already accept the vendor's agents and data model | Data residency, pricing shape, export options, and lock-in around correlation workflows |
| Local `pprof` workflow | You need fast reproduction, developer education, or validation of a proposed optimization | Lack of fleet history, labels, tenancy, and production baseline comparison |

The decision framework should be run with real constraints rather than preferences. For a regulated platform, access control and data residency may outrank convenience. For a polyglot platform, eBPF coverage may be the fastest way to find unknown hotspots. For a small Go-heavy team, pprof plus a simple backend may be enough. For a multi-tenant internal platform, query isolation and retention controls may dominate every other feature. A good profiling decision memo explains which questions the tool must answer, which questions it intentionally will not answer yet, and how the team will revisit the decision as OpenTelemetry profiles mature.

## Did You Know?

- **Google-Wide Profiling helped establish the modern continuous-profiling pattern** because it described profiling across data-center workloads with low overhead, historical storage, and production-scale analysis rather than one-off local debugging.

- **A flame graph is not a timeline** because the horizontal layout represents aggregated stack width, so the safest reading habit is to find wide frames, inspect callers and callees, then verify against the profile type.

- **Unknown stack frames are an operational signal** because they often mean symbol, frame-pointer, runtime-unwinding, or artifact-mapping work is missing, and that work determines whether service teams can act on profiles.

- **OpenTelemetry Profiles being alpha is still useful information** because it tells platform teams to experiment and watch the standard while avoiding production promises that depend on fields or protocol behavior changing.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---|---|---|
| Enabling profiling only after an incident begins | There is no normal baseline, so the incident profile has nothing fair to compare against | Keep low-overhead profiling enabled continuously for selected workloads or node pools |
| Treating CPU profiles as latency profiles | A request can be slow because it waits, blocks, retries, or performs I/O while CPU remains low | Use traces to scope latency, then choose CPU, wall, block, mutex, goroutine, or off-CPU profiles based on the symptom |
| Ignoring labels and versions | Profiles cannot be tied to namespaces, services, releases, or canaries, so ownership and comparison become ambiguous | Standardize service, namespace, workload, version, environment, node, and profile-type labels before broad rollout |
| Exposing pprof endpoints broadly | Stack traces and runtime data can reveal implementation details and sensitive operational context | Bind debug endpoints privately, protect access, or use controlled scrape paths through profiling infrastructure |
| Reading flame graph color as severity | Many flame graphs use color for visual separation, not risk or priority, except in explicit diff views | Read width, stack position, profile type, and diff legend before choosing an optimization target |
| Optimizing the widest frame without context | The wide frame may represent necessary work, changed traffic mix, or a child cost rather than the real regression | Compare with a baseline, inspect callers, reproduce with representative input, and measure the fix |
| Skipping symbolization work | Profiles show unknown frames or runtime internals, making them hard for teams to use | Preserve frame pointers where appropriate, publish debug symbols, map build IDs, and test unwinding per runtime |
| Claiming tool maturity from memory | Tool ownership, license, protocol support, and CNCF maturity can change quickly | Put volatile facts in a dated landscape snapshot and verify against primary docs before production decisions |

## Quiz

1. **Scenario:** A checkout service shows high CPU after a release. Metrics identify the service, and traces show the checkout handler is slower, but logs contain no useful error. Which observability signal should you add next, and why?

<details>
<summary>Answer</summary>

Use continuous profiling next because the remaining question is which function or stack path is consuming CPU in the running service. Metrics already told you that CPU is high, and traces already scoped the slow request path. A CPU profile can show whether the cost sits in serialization, hashing, compression, runtime overhead, or another code path. A differential profile against the previous release makes the regression easier to isolate.
</details>

2. **Scenario:** Your platform has Go, Java, Python, and third-party workloads on the same Kubernetes nodes, and most teams have not adopted language profiling SDKs. Which collection strategy gives the broadest starting coverage?

<details>
<summary>Answer</summary>

An eBPF whole-system profiler is the broadest starting point because it can sample processes from the node side without requiring every service team to add an SDK first. This is the collection model Parca is useful for teaching, and a Parca deployment should be evaluated around privileges, labels, retention, and symbol quality. Pyroscope can be deployed when the team wants a Grafana-native backend, multi-tenant profile storage, SDK ingestion, scrape ingestion, or OTLP profile ingest. In-process SDKs can be added later for critical services that need richer labels or runtime-specific profiles.
</details>

3. **Scenario:** A flame graph shows `encodeResponse` as a wide frame, but the team is unsure whether that means requests got slower after the last deploy. What should the team check before changing code?

<details>
<summary>Answer</summary>

The team should compare the same service, version labels, traffic window, and profile type against a fair baseline from before the deploy. A wide frame in one flame graph shows cumulative samples, not necessarily a regression. A differential flame graph can show whether `encodeResponse` grew relative to the previous release. The team should then validate the suspected code path with representative input or a benchmark before shipping an optimization.
</details>

4. **Scenario:** Memory usage is stable, but garbage collection time is rising and latency gets worse under load. Which profile type is more likely to explain the problem: live heap or allocation profile?

<details>
<summary>Answer</summary>

An allocation profile is usually the better first choice because rising garbage collection cost with stable live memory often means the service creates many short-lived objects. A live heap profile shows retained objects, which is better for leak investigation. Allocation profiles can reveal the functions producing churn even when those objects are freed quickly. The answer should still be checked against runtime metrics and a representative load window.
</details>

5. **Scenario:** A team wants to route profiles through an OpenTelemetry pipeline and claims profiling is now stable because OpenTelemetry graduated in CNCF. What is wrong with that claim?

<details>
<summary>Answer</summary>

OpenTelemetry as a project is CNCF graduated, but the Profiles signal is documented as alpha. That means profile schemas, collector behavior, SDK support, and backend support can still change. The team can experiment with OTLP profiles and should watch the standard, but it should not promise stable production contracts without verifying the exact versions in use. The correct posture is active evaluation, not a blanket maturity claim.
</details>

6. **Scenario:** Your on-call flow starts from a latency alert, jumps to a trace for one slow request, and then needs to find the code path responsible inside one service. What integration makes this workflow efficient?

<details>
<summary>Answer</summary>

Trace-to-profile or span-to-profile linking makes the workflow efficient because it preserves the service, time range, and request context while moving from distributed tracing into code-level runtime evidence. Metrics identify the symptom, traces identify the request path, and profiles identify the function or stack shape consuming CPU, allocating memory, or waiting. The integration is not perfect for every runtime or profiler, so teams should verify how their backend correlates samples with spans. Even partial correlation is valuable when it prevents a manual search across unrelated profile windows.
</details>

7. **Scenario:** A platform team deploys a profiler and sees many `[unknown]` frames in production flame graphs. What should they improve before judging whether the profiler is useful?

<details>
<summary>Answer</summary>

They should improve symbolization and unwinding before judging the profiler's value. Unknown frames often mean missing debug symbols, frame-pointer settings, build-ID mapping, runtime-specific unwinders, or artifact access. Without readable frames, profiles may prove that resources are consumed but fail to show service teams which code to change. Symbol quality is part of the production operating model, not an optional polish task.
</details>

## Hands-On

This exercise deploys Parca in a local Kubernetes cluster and profiles a deliberately expensive Go workload. It uses Parca because the eBPF collection model demonstrates whole-node coverage without adding a profiling SDK to the sample application. If your local machine does not allow privileged eBPF workloads inside kind, read the commands and run them in a disposable Linux-based test cluster instead. The important practice is the workflow: create a baseline, generate load, filter by workload labels, and inspect the hot stack.

```bash
kind create cluster --name profiling-lab

kubectl create namespace profiling

helm repo add parca https://parca-dev.github.io/helm-charts/
helm repo update parca

helm install parca parca/parca \
  --namespace profiling

kubectl -n profiling rollout status deployment/parca --timeout=180s
kubectl -n profiling rollout status daemonset/parca-agent --timeout=180s
```

The current Parca Helm chart renders a server service named `parca-server` and an agent DaemonSet named `parca-agent`. The server is where you query profiles, while the agent runs on nodes and samples processes. In a production cluster you would review privileges, retention, resources, network policy, and access control before installing a profiler. In this lab, the short-lived cluster keeps the focus on reading the resulting profile.

```bash
kubectl create namespace demo

kubectl apply -n demo -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hotspot-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hotspot-app
  template:
    metadata:
      labels:
        app: hotspot-app
        version: v1
    spec:
      containers:
        - name: app
          image: golang:1.24
          imagePullPolicy: IfNotPresent
          command: ["/bin/sh", "-c"]
          args:
            - |
              cat > /tmp/main.go <<'GOEOF'
              package main

              import (
                  "crypto/sha256"
                  "encoding/hex"
                  "fmt"
                  "log"
                  "net/http"
                  "strings"
              )

              func expensiveHash(data string) string {
                  value := []byte(data)
                  for i := 0; i < 2000; i++ {
                      sum := sha256.Sum256(value)
                      encoded := make([]byte, hex.EncodedLen(len(sum)))
                      hex.Encode(encoded, sum[:])
                      value = encoded
                  }
                  return string(value)
              }

              func cheapHandler(w http.ResponseWriter, r *http.Request) {
                  _, _ = fmt.Fprintln(w, "ok")
              }

              func hotspotHandler(w http.ResponseWriter, r *http.Request) {
                  payload := strings.Repeat("profiling-lab", 100)
                  result := expensiveHash(payload)
                  _, _ = fmt.Fprintf(w, "hash=%s\n", result[:16])
              }

              func main() {
                  http.HandleFunc("/cheap", cheapHandler)
                  http.HandleFunc("/hotspot", hotspotHandler)
                  log.Println("listening on :8080")
                  log.Fatal(http.ListenAndServe(":8080", nil))
              }
              GOEOF
              cd /tmp
              go run main.go
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: hotspot-app
spec:
  selector:
    app: hotspot-app
  ports:
    - name: http
      port: 8080
      targetPort: 8080
EOF

kubectl -n demo rollout status deployment/hotspot-app --timeout=180s
```

Now generate traffic long enough for the profiler to collect useful samples. The load generator alternates a cheap endpoint with the intentionally expensive endpoint so the flame graph has a clear contrast. In a real service, you would use production traffic, a canary slice, or a representative load test rather than a loop inside the cluster.

```bash
kubectl -n demo run loadgen \
  --image=busybox:1.36 \
  --restart=Never \
  --command -- sh -c '
    while true; do
      wget -q -O /dev/null http://hotspot-app:8080/hotspot
      wget -q -O /dev/null http://hotspot-app:8080/cheap
      sleep 0.1
    done
  '

sleep 120

kubectl -n profiling port-forward svc/parca-server 7070:7070
```

Open `http://127.0.0.1:7070` while the port-forward is running. Filter for the `demo` namespace or the `hotspot-app` workload labels, choose a recent CPU profile window, and look for frames related to `expensiveHash`, `sha256.Sum256`, and hex encoding. Then stop the `loadgen` pod, wait for a quieter window, and compare the busy interval against the quiet interval. The point is not that hashing is bad; the point is that a sampled production profile can identify the exact stack path responsible for a resource change.

- [ ] Parca server and Parca Agent are both rolled out in the `profiling` namespace, and you can explain why the agent needs node-level access in this lab.
- [ ] The `hotspot-app` deployment is ready in the `demo` namespace, and the load generator has sent traffic to both `/hotspot` and `/cheap` for at least two minutes.
- [ ] The Parca UI is reachable through `http://127.0.0.1:7070`, and a CPU flame graph filtered to `hotspot-app` shows the hashing path as a dominant stack.
- [ ] You can compare a busy time window with a quieter window and describe which stack frames changed rather than only naming the widest frame in one graph.
- [ ] You can state which labels made the profile usable, which frames would be difficult to act on if symbolization failed, and which follow-up benchmark would validate an optimization.

Clean up the lab resources when you are done. This removes the load generator, sample app, profiler, and kind cluster so the privileged profiler does not remain on a machine where you are not actively using it.

```bash
kubectl -n demo delete pod loadgen --ignore-not-found
kubectl delete namespace demo
helm uninstall parca -n profiling
kubectl delete namespace profiling
kind delete cluster --name profiling-lab
```

## Sources

- [Grafana Pyroscope documentation](https://grafana.com/docs/pyroscope/latest/) - Primary documentation for Pyroscope's profiling backend, Grafana integration, multi-tenancy language, and traces-to-profiles navigation.
- [Grafana Pyroscope OSS page](https://grafana.com/oss/pyroscope/) - Primary project page for Grafana Pyroscope as open source continuous profiling software and its Phlare/Pyroscope origin.
- [Introducing Pyroscope 2.0](https://grafana.com/blog/pyroscope-2-0-release/) - Grafana's 2026-04-21 announcement for Pyroscope 2.0, OTLP profiling support, and the rearchitecture context.
- [Pyroscope 2.0 release notes](https://grafana.com/docs/pyroscope/latest/release-notes/v2-0/) - Version-specific source for Pyroscope 2.0 storage architecture and release behavior.
- [Pyroscope and Grafana Phlare join together](https://grafana.com/blog/pyroscope-grafana-phlare-join-for-oss-continuous-profiling/) - Grafana's 2023 acquisition and merge announcement for Pyroscope and Phlare.
- [Deploy Pyroscope using the Helm chart](https://grafana.com/docs/pyroscope/latest/deploy-kubernetes/helm/) - Primary deployment source for the Grafana Pyroscope Helm chart.
- [Parca overview](https://parca.dev/docs/overview/) - Primary Parca documentation for continuous profiling concepts and server responsibilities.
- [Parca ingestion documentation](https://parca.dev/docs/ingestion/) - Primary source for Parca Agent's always-on eBPF sampling model and pprof-formatted profile ingestion.
- [Parca GitHub repository](https://github.com/parca-dev/parca) - Primary repository source for Parca project ownership, purpose, and Apache-2.0 license link.
- [Parca Kubernetes documentation](https://parca.dev/docs/kubernetes/) - Primary deployment source for running Parca and Parca Agent in Kubernetes.
- [Introduction to Parca Agent](https://www.polarsignals.com/blog/posts/2023/01/19/introduction-to-parca-agent) - Polar Signals explanation of Parca Agent and whole-system eBPF profiling.
- [OpenTelemetry Profiles concept documentation](https://opentelemetry.io/docs/concepts/signals/profiles/) - Primary source for the OpenTelemetry Profiles signal status and concepts.
- [OpenTelemetry Profiles enters public alpha](https://opentelemetry.io/blog/2026/profiles-alpha/) - OpenTelemetry's 2026 alpha announcement for the Profiles signal.
- [OpenTelemetry Profiles specification](https://opentelemetry.io/docs/specs/otel/profiles/) - Specification source for profiles as an OpenTelemetry signal.
- [CNCF OpenTelemetry project page](https://www.cncf.io/projects/opentelemetry/) - CNCF source for OpenTelemetry maturity dates and graduated status.
- [CNCF project catalog](https://www.cncf.io/projects/) - CNCF catalog used to verify that Parca and Pyroscope are not listed as CNCF projects as of this snapshot.
- [Brendan Gregg's Flame Graphs](https://www.brendangregg.com/flamegraphs.html) - Canonical flame graph reference and visualization background.
- [Go runtime/pprof package](https://pkg.go.dev/runtime/pprof) - Go standard-library source for runtime profiling support.
- [Go net/http/pprof package](https://pkg.go.dev/net/http/pprof) - Go standard-library source for exposing pprof-compatible HTTP endpoints.
- [Google-Wide Profiling paper](https://research.google/pubs/google-wide-profiling-a-continuous-profiling-infrastructure-for-data-centers/) - Canonical research source for data-center-scale continuous profiling history.

## Next Module

Continue to [Module 1.10: SLO Tooling](../module-1.10-slo-tooling/), where you will connect observability signals to service-level objectives, burn-rate alerts, and operational decision-making.
