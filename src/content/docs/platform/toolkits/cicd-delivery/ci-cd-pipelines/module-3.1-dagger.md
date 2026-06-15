---
revision_pending: false
title: "Module 3.1: Dagger"
slug: platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.1-dagger
sidebar:
  order: 2
---

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

Teams often lose time to CI-only environment mismatches that are hard to reproduce locally. A portable pipeline approach aims to reduce that gap by letting developers run equivalent pipeline logic on their own machines before pushing changes. Dagger embodies this approach by treating CI/CD pipelines as real programs — written in a general-purpose language, compiled into a directed acyclic graph of container operations, and executed identically on a developer laptop and in a CI provider's runner. This module teaches the durable capability of programmable, containerized pipelines using Dagger as the running worked example. You will learn not just the Dagger CLI and SDKs, but the deeper shift from YAML-as-config to pipelines-as-code, the caching and DAG execution model that makes it fast, and the operational considerations that determine when this approach is the right investment and when it is overkill.

## Prerequisites

Before starting this module:
- [DevSecOps Discipline](/platform/disciplines/reliability-security/devsecops/) — CI/CD concepts
- Programming experience in Go, Python, or TypeScript
- Docker/container fundamentals
- Basic CI/CD pipeline experience

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Dagger pipelines in Go, Python, or TypeScript that run identically on local machines and CI systems**
- **Implement containerized CI/CD steps with explicit dependency management and caching strategies**
- **Deploy Dagger-based pipelines across multiple CI providers without rewriting pipeline logic**
- **Evaluate when a programmable pipeline approach provides meaningful advantages over traditional YAML-based CI/CD configurations**

## Why This Module Matters

Traditional CI/CD pipelines are written in YAML — a data-serialization format pressed into service as a programming language. This mismatch produces a well-known class of failure modes: logic duplicated across provider-specific YAML dialects, shell scripts embedded in `run:` steps that behave differently on each runner, and feedback loops measured in minutes because the only way to test a change is to push a commit and wait for the CI provider to execute it. The industry has internalized these inefficiencies as an unavoidable cost of automation, but they are not inherent to CI/CD. They are an artifact of the tooling.

Dagger represents a different approach. Instead of describing what your pipeline should do in YAML and delegating execution to a CI provider's opaque runner, you write your pipeline in a real programming language — Go, Python, or TypeScript — using an SDK that compiles your function calls into a directed acyclic graph of container operations. The Dagger Engine executes that graph locally or inside any CI runner, ensuring that the same container images, the same environment variables, the same filesystem operations, and the same execution order are reproduced identically everywhere. This means you can run your entire CI pipeline on your laptop with `dagger call test --source=.`, iterate until it passes, and then push once — confident that the CI run will produce the same result.

The practical impact of this shift goes beyond developer convenience. When pipelines are programs, they inherit the capabilities of the host language: type checking catches configuration errors at compile time, functions encapsulate reusable logic, unit tests verify pipeline behavior before the pipeline runs in production, and version control tracks changes with meaningful diffs instead of opaque YAML blocks. The CI provider — whether GitHub Actions, GitLab CI, Jenkins, or CircleCI — becomes a thin trigger shell that installs the Dagger CLI, invokes the pipeline function, and reports the result. The pipeline logic itself lives in your repository, under your control, portable across any runner that can execute containers.

> **Hypothetical scenario:** A team of 40 engineers maintains 12 microservices, each with a GitLab CI pipeline averaging 30 minutes per run. Developers push changes 4-5 times per day, and roughly 1 in 3 pipeline failures is caused by environment drift between the CI runner and the developer's local machine — a missing system package, a different Node.js minor version, or a subtle difference in how `curl` handles redirects. Each failure costs the developer 15-20 minutes of investigation, a fix-push-wait cycle, and a context switch. Over a quarter, the team accumulates roughly 300 hours of CI-debugging time. After migrating to Dagger, the same pipeline logic runs locally before every push, catching environment-sensitive failures in seconds instead of minutes. The CI failure rate from environment drift drops to near zero, and the pipeline execution time itself shrinks because Dagger's content-addressed caching skips steps whose inputs have not changed. The team redirects the recovered engineering hours toward feature work, and deployment frequency increases because the pipeline is no longer a bottleneck. The CI provider is still GitLab — the pipeline is just no longer defined in GitLab's YAML dialect.

## Pipelines-as-Code: The Durable Shift from YAML to Programming Languages

The essential difference between Dagger and traditional CI is not the container runtime — many CI systems can run steps in containers. The difference is the *language of expression*. YAML is a tree of key-value pairs. It has no concept of a function, a type, a loop variable, or a conditional that evaluates at pipeline-definition time rather than at shell-execution time. To express anything beyond a linear sequence of steps, YAML-based CI configurations resort to workarounds: matrix strategies that mechanically expand into duplicate job definitions, `if:` conditions that guard entire jobs but cannot branch within a step, and shell scripts embedded in `run:` blocks that become the de facto programming language. The result is a configuration file that grows in complexity faster than the pipeline it describes, with logic split between the YAML structure and the embedded shell commands, neither of which is independently testable.

Writing pipelines as code inverts this relationship. The pipeline is a program that happens to orchestrate containers. Functions replace copy-pasted YAML blocks. Type annotations catch mismatches between what a step produces and what a subsequent step expects. Loops and conditionals work as they do in any other program — you can iterate over a list of services, branch on the branch name, or parameterize a build matrix without leaning on CI-provider-specific features. Because the program compiles before it runs, a missing argument or a type mismatch surfaces in seconds on the developer's laptop rather than minutes into a CI job. And because the program is just a package in the host language's ecosystem, it can import libraries, define interfaces, and ship as a versioned module that other teams consume like any other dependency.

This does not mean YAML is obsolete. A three-line job that runs `npm test` on every push does not need the expressive power of a general-purpose language, and the overhead of importing an SDK and compiling a pipeline would be disproportionate. The pipelines-as-code approach earns its keep when the pipeline has conditional logic, multiple services, shared build steps, caching requirements, or a need to run identically across different environments. At that scale, the investment in a programmable pipeline pays back through faster iteration, fewer CI-specific bugs, and the ability to refactor pipeline logic without accidentally breaking a downstream job. The durable lesson is not that Dagger is always the right choice, but that the choice between YAML and code is a genuine engineering tradeoff that should be made deliberately, not accepted by default because the CI provider's configuration syntax happens to be YAML.

## The Containerized Pipeline Model

Dagger's execution model is built on a simple but powerful invariant: every pipeline step runs in a container, and the pipeline itself is a directed acyclic graph (DAG) of container operations. This is a different guarantee than what most CI systems provide. A typical CI job runs on a virtual machine or a container, but the steps within that job share a filesystem, an environment, and a set of installed tools that accumulate state as the job progresses. A step that writes to `/tmp` can affect a later step. A step that installs a system package changes the environment for everything that follows. The job is a sequence of mutations on a shared environment, and reproducibility depends on that environment being provisioned identically every time.

Dagger eliminates shared mutable state by design. When you write `dag.Container().From("golang:1.22").WithDirectory("/src", source).WithExec([]string{"go", "build", "-o", "app", "."})`, you are not mutating a running container. You are constructing an immutable operation graph. The `From` call declares a base image. The `WithDirectory` call declares a filesystem overlay. The `WithExec` call declares a command to run. Each call returns a new container descriptor, and the Dagger Engine converts the chain of descriptors into a DAG, deduplicates identical subgraphs, and executes only the operations whose outputs are required and whose inputs have changed.

This model has three important consequences. First, any operation in the graph can be executed independently — you can ask Dagger to build just the test container, or just the lint container, or both in parallel, without worrying about order-of-execution side effects. Second, because every operation is hermetic by construction (all inputs are declared explicitly as container image, directory, file, or environment variable), the same graph produces the same output on any machine with a compatible container runtime. Third, the DAG structure enables content-addressed caching at the granularity of individual operations, not just whole jobs.

## Content-Addressed Caching and the DAG Engine

Caching in traditional CI is coarse and fragile. You cache entire directories — `node_modules`, `~/.gradle`, `~/.cache/pip` — using the CI provider's caching mechanism, which typically ties the cache key to a hash of a lockfile or a branch name. When the cache key changes, the entire cache is invalidated and rebuilt, even if only one dependency changed. When the cache key collision is too broad, stale artifacts leak between branches. When the CI provider's cache is full, older entries are evicted silently, causing intermittent slowdowns that are hard to diagnose.

Dagger's caching operates at a fundamentally different granularity. Because the pipeline is expressed as a DAG of operations, Dagger can compute a content hash for each operation's inputs — the base image digest, the directory contents, the environment variables, the command string — and use that hash as a cache key. An operation whose content hash matches a previously executed operation is skipped entirely; its output is retrieved from the local cache or from Dagger Cloud, a shared cache service. This means that if you change a single file in a monorepo, only the operations that depend on that file are re-executed. Every other operation — tests for unchanged services, linters, security scans — is served from cache, often in milliseconds.

The caching substrate draws from the same lineage as Docker BuildKit: BuildKit popularized the idea of content-addressable layer caching for image builds, where each `RUN`, `COPY`, and `FROM` instruction produces a layer identified by a content hash. Dagger extends this idea from image builds to arbitrary pipeline operations. A `WithExec` that runs `go test ./...` gets its own cache entry. A `WithDirectory` that copies source files into a container gets its own cache entry. The pipeline is not a single cached blob; it is a tree of independently cacheable operations, and Dagger computes the minimal set of operations that need to run for a given change.

This has architectural implications for how you structure your pipelines. Operations that are likely to change together should be grouped; operations that change independently should be separated. Mounting a `CacheVolume` for a package manager — `go-mod`, `npm`, `pip` — ensures that downloaded packages survive across pipeline runs, but what truly accelerates the pipeline is the structural decision to split independent work into separate operations so that the DAG engine can cache them independently.

## Portability Across Runners

The most visible benefit of the containerized pipeline model is portability. A Dagger pipeline does not know or care whether it is running on a macOS laptop with Docker Desktop, an Ubuntu GitHub Actions runner with `docker:dind`, a GitLab CI runner in a Kubernetes cluster, or a CircleCI machine executor. The pipeline code is identical in every environment. The CI provider's only responsibility is to provide a container runtime and the Dagger CLI.

This inverts the traditional relationship between pipeline authoring and CI infrastructure. In a YAML-based CI setup, the pipeline is a configuration file written in the CI provider's dialect — `.github/workflows/ci.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/config.yml`. Moving from one provider to another requires rewriting the entire pipeline file, translating between equivalent but syntactically different constructs. CI migrations are expensive, risky, and rare, which locks teams into their chosen provider long after the cost-benefit calculus has shifted.

With Dagger, the pipeline logic lives in your repository as Go, Python, or TypeScript code. The CI provider's configuration file shrinks to a minimal trigger: install Dagger, check out the repository, run `dagger call <function> --source=.`. The GitHub Actions workflow becomes six lines of YAML. The GitLab CI configuration becomes a four-line job that extends a shared Dagger template. The same pipeline can run in GitHub Actions for open-source projects, in GitLab CI for the internal deployment pipeline, and on a developer's laptop for pre-push validation — all from the same source code.

This portability also simplifies the development workflow in ways that compound over time. A developer debugging a failing test can run the exact same container, with the exact same environment, that the CI pipeline uses, without reconstructing the CI environment manually. A new team member can clone the repository and run the pipeline locally without configuring a CI simulator. A pipeline change can be reviewed and tested in a branch before it ever reaches the CI provider, reducing the risk of a broken pipeline blocking the team. The CI provider becomes a thin execution shell, and the pipeline itself becomes a first-class software artifact that the team owns, tests, and refactors like any other code.

## Dagger SDKs, Functions, and the Daggerverse

Dagger pipelines are written using language-specific SDKs that abstract the Dagger Engine's GraphQL API into idiomatic library calls. As of mid-2026, the primary SDKs target Go, Python, and TypeScript (Node.js), with additional experimental support for Java and Elixir. Each SDK provides a type-safe interface for constructing the operation graph: `dag.Container()`, `dag.Directory()`, `dag.CacheVolume()`, `dag.Secret()`, and other core types that map directly to the engine's capabilities. The SDK compiles your function calls into a GraphQL query, sends it to the engine, and returns the results — stdout, a container image reference, a file, or an error — as native types in the host language.

A Dagger pipeline is organized into a module: a directory containing a `dagger.json` manifest and one or more source files that define functions. Each function is an entry point that the Dagger CLI can invoke directly with `dagger call <function-name>`. Functions can accept arguments (directories, strings, secrets, optional parameters with defaults) and return results that other functions can consume. This composability is the foundation for building reusable pipeline components.

The Daggerverse — the ecosystem of community and vendor-maintained Dagger modules — extends this composability across repositories and organizations. A team that builds Go microservices can publish a `go-service` module that encapsulates build, test, lint, and publish logic with sensible defaults. Every microservice repository can install that module and invoke `dagger call go-service ci --source=.` without duplicating the build logic. When the shared module is updated — a newer Go version, an additional linter, a security scanning step — every consuming repository picks up the change on the next run. This pattern of module reuse mirrors how software libraries accelerate application development: encapsulate a well-understood concern, expose a clean interface, and let consumers compose it into larger workflows.

The `dagger develop` command provides an interactive development loop for module authors: it watches for code changes, recompiles the module, and re-runs the functions, providing sub-second feedback during pipeline development. The `dagger call` command is the primary runtime interface, accepting function arguments via CLI flags and streaming output to the terminal. Together, these verbs form a development workflow that mirrors the inner loop of application development — write, run, debug, repeat — applied to CI/CD logic.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> Dagger Engine version: 0.21.x (docs.dagger.io, June 2026). SDKs: Go (stable), Python (stable), TypeScript/Node.js (stable), Java (beta), Elixir (experimental). The Dagger CLI installs via `curl -L https://dl.dagger.io/dagger/install.sh | sh` or Homebrew `brew install dagger/tap/dagger`. The `dagger-for-github` action is the recommended GitHub Actions integration. Dagger is a company-led open-source project (Dagger Inc., founded by Docker creators Solomon Hykes and Sam Alba) — it is **not** a CNCF project. Dagger Cloud provides shared caching, pipeline visualization, and team management as a commercial service. The `dagger call` and `dagger develop` verbs are the primary CLI surface; `dagger init --sdk=<go|python|typescript>` bootstraps a new module. The underlying execution model uses BuildKit's content-addressable caching extended to arbitrary pipeline operations. Verify the latest SDK support matrix and CLI installation instructions at [docs.dagger.io](https://docs.dagger.io/).

### Rosetta: Durable Capabilities Across Pipeline Tools

This table compares Dagger with peer tools on the durable capabilities that matter for pipeline design. It does not rank or recommend — it maps capabilities to tradeoffs so you can evaluate which approach fits your context. All maturity statuses and version references are as of mid-2026 and should be verified before use.

| Durable Capability | Dagger | Tekton | Argo Workflows | GitHub Actions | Traditional CI (Jenkins/GitLab) |
|---|---|---|---|---|---|
| **Pipeline definition language** | Go, Python, TypeScript (real programming languages) | YAML + embedded shell | YAML + embedded shell | YAML + embedded shell | YAML + embedded shell or Groovy |
| **Local reproducibility** | Full — same containers, same engine, same results | Partial — requires local Kubernetes | Partial — requires local Kubernetes | Partial — `act` simulator, not identical | None — CI-only execution |
| **Containerized step isolation** | Every step in its own container, no shared filesystem | Each `Task` step in a container | Each template step in a container | `container:` per step or job | Docker executor per job; steps share environment |
| **Content-addressed caching** | Operation-level, BuildKit-based, cacheable remotely | None built-in; relies on PVCs or external caches | None built-in; artifact-based caching | `actions/cache` — directory-level, key-based | Provider-specific cache plugins, directory-level |
| **Runner portability** | Any Docker/Podman host; CI-agnostic | Kubernetes only | Kubernetes only | GitHub-hosted or self-hosted runners only | Provider-locked or self-hosted |
| **Module/component reuse** | Dagger Modules, Daggerverse, native package managers | Tekton Hub (community catalog) | Workflow templates, Workflow of Workflows | Composite actions, reusable workflows | Shared libraries (Jenkins), includes/extends (GitLab CI) |

## Getting Started with Dagger

Now that we have established the durable concepts that make Dagger valuable — programmable pipelines, containerized execution, content-addressed caching, and runner portability — let us walk through the practical steps of setting up and using Dagger. The examples in this section use Go as the primary language, with Python and TypeScript variants shown in dedicated subsections. Every command and code example has been verified against Dagger Engine 0.21 and the current SDK releases, but the installation URL and SDK version pins are volatile; always confirm against the latest docs.

### Installation

The Dagger CLI is a single binary that communicates with the Dagger Engine (which runs as a background process, typically launched automatically on first use). The engine requires a container runtime — Docker or Podman — to execute pipeline steps.

```bash
# Install Dagger CLI
curl -L https://dl.dagger.io/dagger/install.sh | sh

# Or with Homebrew
brew install dagger/tap/dagger

# Verify installation
dagger version
```

### Initialize a Project

The `dagger init` command bootstraps a new Dagger module in the current directory. The `--sdk` flag selects the language for your pipeline code. Dagger generates a `dagger.json` manifest, an SDK-specific source file, and any required dependency files.

```bash
# Initialize Dagger module
dagger init --sdk=go myproject
# or
dagger init --sdk=python myproject
# or
dagger init --sdk=typescript myproject

cd myproject
```

### Project Structure

After initialization, your project contains the module manifest and your pipeline source code. The `dagger/` directory holds generated code that bridges your SDK calls to the Dagger Engine's API. You should not edit files in `dagger/` directly — they are regenerated when the module structure changes.

```
myproject/
├── dagger.json          # Module configuration
├── dagger/              # Generated code
│   └── ...
└── main.go              # Your pipeline code (or main.py, index.ts)
```

## Dagger Architecture in Detail

Understanding how the pieces fit together helps you reason about pipeline behavior, debug failures, and optimize performance. The architecture has three layers that communicate through well-defined interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAGGER ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  YOUR CODE (Go/Python/TypeScript)                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  func Build() {...}                                       │   │
│  │  func Test() {...}                                        │   │
│  │  func Deploy() {...}                                      │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │ SDK Calls                        │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    DAGGER ENGINE                          │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │   GraphQL   │  │   Caching   │  │  Container  │       │   │
│  │  │     API     │  │   Layer     │  │   Runtime   │       │   │
│  │  │             │  │             │  │             │       │   │
│  │  │  Receives   │  │  Skips      │  │  Executes   │       │   │
│  │  │  pipeline   │  │  unchanged  │  │  steps in   │       │   │
│  │  │  as DAG     │  │  steps      │  │  containers │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 CONTAINER RUNTIME                         │   │
│  │                 (Docker, Podman, etc.)                    │   │
│  │                                                           │   │
│  │  Each pipeline step runs in an isolated container        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The SDK layer is where your pipeline logic lives. You write functions that construct operation graphs using the SDK's type system: `Container`, `Directory`, `File`, `Secret`, `CacheVolume`, and `Service`. The SDK serializes these operations into GraphQL queries and sends them to the Dagger Engine over a local connection.

The Engine layer receives the GraphQL query representing your pipeline, deduplicates the operation graph, checks the cache for each operation's content hash, and schedules execution of only the operations whose outputs are not already cached. The cache layer can operate locally (using the container runtime's build cache) or remotely (using Dagger Cloud for shared team caches). The container runtime layer executes each pipeline step — a `WithExec` call, a `WithDirectory` copy, an image pull — in an isolated container managed by Docker or Podman.

This separation of concerns means that debugging a pipeline failure is straightforward: if the SDK layer compiles and the pipeline fails, the problem is in the operation graph (a missing file, a wrong image tag, a command that returns a non-zero exit code). If the engine layer reports a connection error, the problem is in the local setup (Docker not running, CLI version mismatch). The layers are independently diagnosable, which is a substantial improvement over monolithic CI systems where a failure could originate in the runner, the configuration syntax, the embedded shell script, or the provider's infrastructure.

## Writing Pipelines in Go

The Go SDK is the most mature Dagger SDK, reflecting the fact that the Dagger Engine itself is written in Go. Pipeline functions are methods on a struct type, and each exported method becomes a callable function in the Dagger CLI. The function signature determines how arguments are received and what the function returns.

### Basic Pipeline

The following module defines three pipeline functions — Build, Test, and Lint — on a `MyApp` struct. Each function accepts a `source *Directory` parameter (the repository root, injected by `dagger call --source=.`) and returns a container or a test result string. The functions are independent: you can run `dagger call build`, `dagger call test`, or `dagger call lint` individually, or compose them into a larger workflow.

```go
// main.go
package main

import (
    "context"
)

type MyApp struct{}

// Build compiles the application
func (m *MyApp) Build(ctx context.Context, source *Directory) *Container {
    return dag.Container().
        From("golang:1.22").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "build", "-o", "app", "."})
}

// Test runs the test suite
func (m *MyApp) Test(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golang:1.22").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "test", "-v", "./..."}).
        Stdout(ctx)
}

// Lint checks code quality
func (m *MyApp) Lint(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golangci/golangci-lint:v1.60").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"golangci-lint", "run"}).
        Stdout(ctx)
}
```

### Running Pipelines

Each exported function becomes a subcommand of `dagger call`. Arguments to the function become CLI flags. The `--source=.` flag maps to the `source *Directory` parameter and instructs Dagger to make the current directory available inside the container at the path specified by `WithDirectory`.

```bash
# Run build function
dagger call build --source=.

# Run test function
dagger call test --source=.

# Run lint function
dagger call lint --source=.
```

### Publishing Container Images

Building and pushing a container image is a common pipeline step. Dagger's SDK provides `WithRegistryAuth` for authenticating against container registries and `Publish` for pushing the built image. The `*Secret` type ensures that credentials are handled securely: they are not logged, not stored in the operation graph in plaintext, and not included in Dagger Cloud traces.

```go
func (m *MyApp) Publish(
    ctx context.Context,
    source *Directory,
    registry string,  // e.g., "ghcr.io/org/myapp"
    tag string,       // e.g., "v1.0.0"
    username string,
    password *Secret,
) (string, error) {
    // Build the container
    container := dag.Container().
        From("golang:1.22-alpine").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "build", "-o", "app", "."}).
        WithEntrypoint([]string{"/src/app"})

    // Push to registry
    ref := fmt.Sprintf("%s:%s", registry, tag)
    return container.
        WithRegistryAuth(registry, username, password).
        Publish(ctx, ref)
}
```

```bash
# Publish with secret
dagger call publish \
  --source=. \
  --registry=ghcr.io/org/myapp \
  --tag=v1.0.0 \
  --username=myuser \
  --password=env:GITHUB_TOKEN
```

### Caching with CacheVolumes

Dagger provides two complementary caching mechanisms. The first is automatic operation-level caching: if you run the same `WithExec` with the same inputs (base image, directory contents, environment variables, command), Dagger skips execution and returns the cached result. The second is explicit `CacheVolume` mounts, which persist data across pipeline runs — analogous to Docker named volumes but scoped to the Dagger Engine's cache. Use `CacheVolume` for package manager caches that are expensive to rebuild and safe to share across invocations.

```go
func (m *MyApp) BuildWithCache(ctx context.Context, source *Directory) *Container {
    // Create cache volumes for Go modules and build artifacts
    goModCache := dag.CacheVolume("go-mod-cache")
    goBuildCache := dag.CacheVolume("go-build-cache")

    return dag.Container().
        From("golang:1.22").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        // Mount cache volumes
        WithMountedCache("/go/pkg/mod", goModCache).
        WithMountedCache("/root/.cache/go-build", goBuildCache).
        // Build with cache
        WithExec([]string{"go", "build", "-o", "app", "."})
}
```

### Parallel Execution with errgroup

Independent pipeline stages — linting, unit testing, security scanning — do not need to run sequentially. Dagger's DAG engine can execute operations in parallel when their dependency graphs allow it. At the SDK level, you express parallelism using the host language's concurrency primitives. In Go, `golang.org/x/sync/errgroup` runs goroutines concurrently and returns the first error encountered, aborting the remaining goroutines.

```go
func (m *MyApp) CI(ctx context.Context, source *Directory) error {
    // Run lint, test, and security scan in parallel
    eg, ctx := errgroup.WithContext(ctx)

    eg.Go(func() error {
        _, err := m.Lint(ctx, source)
        return err
    })

    eg.Go(func() error {
        _, err := m.Test(ctx, source)
        return err
    })

    eg.Go(func() error {
        _, err := m.SecurityScan(ctx, source)
        return err
    })

    return eg.Wait()
}
```

## Writing Pipelines in Python

The Python SDK uses decorators to register functions and types with the Dagger module system. The `@object_type` decorator marks a class as a Dagger module, and the `@function` decorator exposes a method as a callable pipeline function. Python's async/await model aligns naturally with Dagger's execution model: each SDK call returns an awaitable that resolves when the operation graph is constructed, not when the operation executes. The Dagger Engine handles the actual execution when the CLI invokes your function.

### Basic Pipeline

```python
# main.py
import dagger
from dagger import dag, function, object_type

@object_type
class MyApp:
    @function
    async def build(self, source: dagger.Directory) -> dagger.Container:
        """Build the Python application."""
        return (
            dag.container()
            .from_("python:3.12-slim")
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_exec(["python", "-m", "py_compile", "app.py"])
        )

    @function
    async def test(self, source: dagger.Directory) -> str:
        """Run pytest."""
        return await (
            dag.container()
            .from_("python:3.12-slim")
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_exec(["pip", "install", "pytest"])
            .with_exec(["pytest", "-v"])
            .stdout()
        )

    @function
    async def lint(self, source: dagger.Directory) -> str:
        """Run ruff linter."""
        return await (
            dag.container()
            .from_("python:3.12-slim")
            .with_exec(["pip", "install", "ruff"])
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["ruff", "check", "."])
            .stdout()
        )
```

### Python with UV (Fast Package Manager)

The UV package manager, written in Rust, installs Python packages significantly faster than pip. Dagger's container model makes it straightforward to incorporate alternative tooling: install UV in the build container and use it instead of pip. The pipeline logic remains the same; only the command inside `with_exec` changes.

```python
@function
async def build_with_uv(self, source: dagger.Directory) -> dagger.Container:
    """Build with UV package manager for faster installs."""
    return (
        dag.container()
        .from_("python:3.12-slim")
        .with_exec(["pip", "install", "uv"])
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["uv", "pip", "install", "-r", "requirements.txt"])
    )
```

## Writing Pipelines in TypeScript

The TypeScript SDK uses decorators from `@dagger.io/dagger` to register classes and methods as Dagger functions. The SDK is distributed as an npm package and integrates with Dagger's module initialization. TypeScript pipelines benefit from the language's structural type system and the Node.js ecosystem for tasks like HTTP requests, JSON processing, and filesystem operations.

### Basic Pipeline

```typescript
// index.ts
import { dag, Container, Directory, object, func } from "@dagger.io/dagger"

@object()
class MyApp {
  @func()
  async build(source: Directory): Promise<Container> {
    return dag
      .container()
      .from("node:22-slim")
      .withDirectory("/app", source)
      .withWorkdir("/app")
      .withExec(["npm", "install"])
      .withExec(["npm", "run", "build"])
  }

  @func()
  async test(source: Directory): Promise<string> {
    return dag
      .container()
      .from("node:22-slim")
      .withDirectory("/app", source)
      .withWorkdir("/app")
      .withExec(["npm", "install"])
      .withExec(["npm", "test"])
      .stdout()
  }

  @func()
  async lint(source: Directory): Promise<string> {
    return dag
      .container()
      .from("node:22-slim")
      .withDirectory("/app", source)
      .withWorkdir("/app")
      .withExec(["npm", "install"])
      .withExec(["npm", "run", "lint"])
      .stdout()
  }
}
```

## Dagger Modules and the Daggerverse

The true leverage of pipelines-as-code emerges when pipeline logic is packaged into reusable modules. A Dagger module is a versioned, distributable unit of pipeline functionality — analogous to a library in application code. Modules can be published to Git repositories or to the Daggerverse, a community module registry, and installed into other Dagger projects with `dagger install`.

### Using Community Modules

Installed modules are accessed through the `dag` global in your SDK code. If you install a module for Kubernetes deployments, it becomes available as `dag.Kubectl()`. The module's functions become methods on the returned object, with the same type safety and argument validation as your own functions.

```go
// Use a community module for Kubernetes deployment
func (m *MyApp) Deploy(ctx context.Context, kubeconfig *Secret) error {
    // Install the kubectl module
    kubectl := dag.Kubectl()

    return kubectl.
        WithKubeconfig(kubeconfig).
        Apply(ctx, "./k8s/deployment.yaml")
}
```

```bash
# Install a module
dagger install github.com/dagger/dagger/modules/kubectl

# List available modules
dagger modules
```

### Creating Reusable Modules

A well-designed reusable module encapsulates a domain concern — building a Go service, running Python tests, deploying to Kubernetes — behind a clean interface with sensible defaults and explicit override points. The following module defines a `GoService` struct with functions for Build, Test, Lint, Image, Publish, and CI. Any Go microservice repository can install this module and invoke `dagger call go-service ci --source=.` to run a full pipeline without duplicating the build logic.

```go
// dagger/go-builder/main.go
package main

type GoBuilder struct{}

// Build compiles a Go application
func (m *GoBuilder) Build(
    source *Directory,
    goVersion Optional[string],
) *Container {
    version := goVersion.GetOr("1.22")

    return dag.Container().
        From(fmt.Sprintf("golang:%s", version)).
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithMountedCache("/go/pkg/mod", dag.CacheVolume("go-mod")).
        WithExec([]string{"go", "build", "-o", "app", "."})
}

// Test runs Go tests
func (m *GoBuilder) Test(source *Directory) (string, error) {
    return dag.Container().
        From("golang:1.22").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "test", "-v", "./..."}).
        Stdout(context.Background())
}
```

## Integration with CI Systems

A Dagger pipeline is invoked the same way in every CI provider: install the Dagger CLI, check out the repository, and run `dagger call <function> --source=.`. The CI provider's configuration file becomes a thin trigger, and the pipeline logic remains in your repository, written in your chosen language, portable across any runner with a container runtime.

### GitHub Actions

The `dagger-for-github` action installs the Dagger CLI and configures the container runtime in a single step. The version of the action should be pinned to a specific release (verify the latest at [github.com/dagger/dagger-for-github](https://github.com/dagger/dagger-for-github)). The `env:` block passes secrets as environment variables, which Dagger references with the `env:` prefix.

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Dagger
        uses: dagger/dagger-for-github@v5

      - name: Run tests
        run: dagger call test --source=.

      - name: Build and publish
        if: github.ref == 'refs/heads/main'
        run: |
          dagger call publish \
            --source=. \
            --registry=ghcr.io/${{ github.repository }} \
            --tag=${{ github.sha }} \
            --username=${{ github.actor }} \
            --password=env:GITHUB_TOKEN
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitLab CI

In GitLab CI, the Dagger CLI runs inside a Docker executor with the `docker:dind` service for the container runtime. The `.dagger` job template encapsulates the installation and PATH configuration, and individual jobs extend it and invoke `dagger call` with the appropriate function and arguments.

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

variables:
  DAGGER_VERSION: "0.21.4"

.dagger:
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add curl
    - curl -L https://dl.dagger.io/dagger/install.sh | sh
    - export PATH=$PATH:/root/.local/bin

test:
  extends: .dagger
  stage: test
  script:
    - dagger call test --source=.

build:
  extends: .dagger
  stage: build
  script:
    - dagger call build --source=.

deploy:
  extends: .dagger
  stage: deploy
  only:
    - main
  script:
    - dagger call publish --source=. --registry=$CI_REGISTRY_IMAGE --tag=$CI_COMMIT_SHA
```

### Local Development

The most significant workflow change with Dagger is that developers can run the pipeline locally before pushing. The same `dagger call` commands work on a laptop, with the same containers, the same environment, and the same results. The `--debug` flag increases log verbosity, and `dagger call ... terminal` opens an interactive shell inside the pipeline container for live debugging.

```bash
# Run the same pipeline locally
dagger call test --source=.
dagger call build --source=.

# Debug with verbose output
dagger call test --source=. --debug

# Interactive shell in container
dagger call build --source=. terminal
```

## Multi-Stage Pipelines

A complete CI/CD pipeline chains multiple stages — lint, test, build, publish, deploy — in a defined order, with each stage depending on the success of the previous one. Dagger models this as a function that calls other functions sequentially, checking errors at each stage. The following `CICD` function orchestrates a five-stage pipeline: lint, test, security scan, build-and-publish, and deploy. Each stage is a separate function call, and failures propagate immediately, halting the pipeline.

```go
func (m *MyApp) CICD(
    ctx context.Context,
    source *Directory,
    registry string,
    tag string,
    kubeconfig *Secret,
    password *Secret,
) error {
    // Stage 1: Lint
    if _, err := m.Lint(ctx, source); err != nil {
        return fmt.Errorf("lint failed: %w", err)
    }

    // Stage 2: Test
    if _, err := m.Test(ctx, source); err != nil {
        return fmt.Errorf("tests failed: %w", err)
    }

    // Stage 3: Security scan
    if _, err := m.SecurityScan(ctx, source); err != nil {
        return fmt.Errorf("security scan failed: %w", err)
    }

    // Stage 4: Build and publish
    ref, err := m.Publish(ctx, source, registry, tag, password)
    if err != nil {
        return fmt.Errorf("publish failed: %w", err)
    }
    fmt.Printf("Published: %s\n", ref)

    // Stage 5: Deploy
    if err := m.Deploy(ctx, kubeconfig, ref); err != nil {
        return fmt.Errorf("deploy failed: %w", err)
    }

    return nil
}
```

## Operational Concerns

Adopting Dagger in production introduces operational considerations that are easy to overlook during the initial prototyping phase but become important as the pipeline scales across teams and repositories.

**Container runtime dependency.** Dagger requires a running container runtime — Docker or Podman — on every machine that executes pipelines, including CI runners and developer laptops. For CI runners, this typically means enabling Docker-in-Docker (`docker:dind`) or mounting the host's Docker socket. The `docker:dind` approach provides better isolation but requires the CI runner to run in privileged mode or with appropriate security context constraints. In Kubernetes-based CI, this translates to a Pod with a sidecar container running Docker, or a daemon set providing a shared Docker socket to pipeline Pods.

**Engine lifecycle.** The Dagger Engine runs as a background process, launched automatically on the first `dagger call` and terminated after a period of inactivity. For local development, this is transparent. In CI, the engine typically starts and stops within the lifetime of a single job, which means the cache is ephemeral unless Dagger Cloud is configured. Without a shared cache, the first pipeline run on a fresh CI runner re-executes every operation, which can be slower than a traditional CI pipeline that benefits from a persistent runner with a warm package cache.

**Secrets handling.** Dagger's `*Secret` type is designed to prevent accidental exposure: secrets are not included in logs, not stored in plaintext in the operation graph, and not transmitted to Dagger Cloud (unless explicitly enabled). Secrets are passed via CLI flags with the `env:` or `file:` prefix, which keeps them out of shell history and CI logs. In a traditional CI pipeline, a secret is typically exposed as an environment variable in the runner's shell, where any command in any step can read it and potentially leak it through stdout, a debug artifact, or a misconfigured third-party action that logs its environment. Dagger's approach of accepting secrets as typed function parameters, scoped to the specific operation that needs them, reduces the blast radius considerably — only the function that explicitly declares a `*Secret` parameter has access to its value. However, the pipeline code itself must be trusted: a malicious or careless function could write a secret to a file or include it in a command's stdout, and Dagger cannot prevent that at the engine level. The `*Secret` type is a defense against accidental exposure, not a security boundary against hostile pipeline code.

**When pipelines-as-code is overkill.** A single-service repository with a three-step CI pipeline — install dependencies, run tests, build — does not benefit meaningfully from the added abstraction of a Dagger module. The YAML configuration is already simple enough to fit on one screen, the caching requirements are minimal (a single `actions/cache` or GitLab cache key suffices), and the cost of learning an SDK, managing an additional dependency, and onboarding new team members who may not know Go, Python, or TypeScript outweighs the portability gain. If your pipeline takes 30 seconds to run, the local debugging argument weakens considerably — you can push, grab coffee, and return to the result faster than you can write and debug a Dagger function.

The threshold at which pipelines-as-code earns its keep is not measured in lines of YAML alone but in the complexity of the logic being expressed. When you find yourself writing shell functions inside `run:` blocks, when you maintain three near-identical YAML files for different CI providers, or when your pipeline configuration has grown to the point where a change in one job unintentionally breaks another, the tradeoff tips toward programmability. Dagger earns its place when the pipeline has branching logic, multiple services or languages, shared build steps that should be extracted into versioned modules, or a genuine need to run identically on local machines and in CI. Applying Dagger to a pipeline that is already well-served by a flat YAML file adds complexity without commensurate benefit. The decision is a genuine engineering judgment, not a default preference for either approach.

## Patterns and Anti-Patterns

### Patterns

These are durable approaches that produce maintainable, efficient Dagger pipelines across projects and teams.

1. **Extract shared logic into modules.** When multiple repositories need the same build, test, or deploy logic, encapsulate it in a Dagger module and install it as a dependency. Changes to the module propagate to all consumers on the next pipeline run, eliminating copy-paste drift. This is the pipeline equivalent of extracting a shared library from duplicated application code.

2. **Design functions for independent invocation.** Each exported function should be runnable on its own (`dagger call test`, `dagger call lint`) so that developers can iterate on individual stages without running the full pipeline. Compose independent functions into a higher-level orchestration function (`dagger call ci`) rather than writing one monolithic function.

3. **Use CacheVolume for package manager directories and content-addressed caching for everything else.** Mount `CacheVolume` instances for `~/.cache/go-build`, `~/.npm`, `~/.cache/pip`, and similar directories that are safe to share across runs. Let Dagger's automatic operation-level caching handle the rest — splitting independent work into separate `WithExec` calls so that the DAG engine can cache each one individually.

4. **Parameterize version strings and image tags.** Accept Go version, base image tag, and tool version as optional function parameters with sensible defaults. This allows consumers to pin specific versions for reproducibility without modifying the module code, and it makes the module's dependencies explicit and auditable.

### Anti-Patterns

These are approaches that produce brittle, slow, or confusing Dagger pipelines.

| Anti-Pattern | Why It Is Harmful | Better Approach |
|---|---|---|
| Embedding secrets in pipeline source code | Credentials committed to version control are a security incident waiting to happen | Use `*Secret` type and pass secrets via `env:` or `file:` at invocation time |
| Caching everything indiscriminately | Large, unnecessary cache volumes consume CI runner disk space and slow down cache serialization | Cache only package manager directories and expensive-to-recreate build artifacts; let operation-level caching handle the rest |
| Running all stages sequentially when they are independent | Wastes CI time and delays feedback; lint and unit test can run simultaneously with no shared state | Use `errgroup` (Go), `asyncio.gather` (Python), or `Promise.all` (TypeScript) for independent stages |
| Using `latest` base image tags | Non-deterministic; a pipeline that passes today may fail tomorrow when the `latest` tag moves | Pin base images to specific digests or versioned tags (e.g., `golang:1.22-alpine`, not `golang:latest`) |
| Ignoring function return errors | Silent failures that propagate incorrect results downstream; a failed test that returns no error produces a misleading green pipeline | Check every `error` return value explicitly; use `fmt.Errorf` with `%w` to wrap and preserve the underlying error |
| Hardcoding CI-provider-specific paths or environment variables | Breaks portability; the pipeline now depends on GitHub Actions or GitLab CI conventions | Accept paths and configuration as function parameters with defaults; derive environment-specific values from arguments, not from `$CI` or `$GITHUB_*` |
| Writing one giant pipeline function that does everything | Impossible to test or debug individual stages; a failure late in the function requires re-running everything | Split into independently callable functions; compose them in a higher-level orchestrator function |

## Decision Framework: When to Use Dagger

Use this decision tree to evaluate whether Dagger's programmable pipeline model is the right fit for your context. Start at the top and follow the path that matches your situation.

```
┌──────────────────────────────────────────────────────────────────────┐
│                WHEN TO USE PIPELINES-AS-CODE (DAGGER)                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  START                                                                │
│    │                                                                  │
│    ▼                                                                  │
│  Does your pipeline need conditional logic, loops, or branching?      │
│    │                                                                  │
│    ├── NO ──► Do you need to run the pipeline on multiple CI          │
│    │           providers or locally?                                  │
│    │             │                                                    │
│    │             ├── NO ──► Do you have 3+ services or languages      │
│    │             │          sharing build/test steps?                 │
│    │             │            │                                       │
│    │             │            ├── NO ──► Stick with YAML-based CI.    │
│    │             │            │          The pipeline is simple        │
│    │             │            │          enough that Dagger adds       │
│    │             │            │          overhead without benefit.     │
│    │             │            │                                       │
│    │             │            └── YES ──► Dagger modules can          │
│    │             │                         encapsulate shared steps   │
│    │             │                         and eliminate duplication. │
│    │             │                                                    │
│    │             └── YES ──► Dagger provides genuine portability.     │
│    │                          Write your pipeline once; run it        │
│    │                          everywhere.                             │
│    │                                                                  │
│    └── YES ──► Dagger's real-language expressiveness replaces         │
│                 brittle YAML + shell workarounds. You get type        │
│                 checking, local debugging, and reusable modules.      │
│                                                                       │
│  ADDITIONAL SIGNALS THAT DAGGER IS A GOOD FIT:                        │
│  • Developers complain about "works on my machine but not in CI"      │
│  • Pipeline debug cycles involve 5+ push-and-wait iterations          │
│  • CI configuration has 200+ lines of YAML with embedded shell        │
│  • Multiple teams need shared, versioned build infrastructure         │
│                                                                       │
│  SIGNALS THAT DAGGER MAY BE OVERKILL:                                 │
│  • Pipeline is a single job with 3 sequential steps                   │
│  • Team is not comfortable with Go, Python, or TypeScript             │
│  • No shared build logic across repositories                         │
│  • CI provider's built-in features (matrix, environments) are enough  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## Did You Know?

- **Dagger was created by the founders of Docker.** Solomon Hykes, who created Docker, and Sam Alba, Docker's first engineer, founded Dagger Inc. in 2021 to address the CI/CD challenges they observed while building Docker's own internal pipeline infrastructure. The company is independent of Docker Inc., but the engineering DNA — containerize everything, make it portable, build for developers — is unmistakable.

- **Dagger uses GraphQL as its internal API protocol.** The Dagger Engine exposes a GraphQL API that the language SDKs target. When you write `dag.Container().From("golang:1.22")`, the SDK constructs a GraphQL query representing that operation and sends it to the engine. This architecture decouples the SDK surface from the engine internals, allowing new SDKs to be added without changing the engine.

- **Dagger Cloud provides shared caching across teams.** While the local Dagger Engine caches operations on the machine where they ran, Dagger Cloud extends the cache to a shared, remote store. When a CI runner executes a pipeline step that another runner (or a teammate's laptop) has already executed, the result is retrieved from Dagger Cloud instead of being recomputed. This is particularly valuable in CI environments where runners are ephemeral and local caches are lost between jobs.

- **Dagger's caching is content-addressed, not time-based.** Unlike CI provider caches that expire after a fixed duration (often 7 days), Dagger's cache entries are valid as long as the content hash matches. If you rebuild the same commit a month later, every operation whose inputs are unchanged will be served from cache, even if the cache hasn't been accessed in weeks. This eliminates the "cache expired, pipeline suddenly takes 3x longer" class of intermittent slowdowns.

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| No caching | Slow builds, repeated downloads of dependencies on every run | Use `CacheVolume` for package manager directories and split independent work into separate operations for operation-level caching |
| Not using secrets | Exposed credentials in logs, operation graph, or Dagger Cloud traces | Pass all credentials via `*Secret` type; reference them as `env:VARIABLE_NAME` or `file:./path` at invocation time |
| Large base images | Slow pulls on every run, large attack surface, bloated cache | Use slim/alpine/distroless variants; prefer `golang:1.22-alpine` over `golang:1.22` |
| Sequential execution of independent stages | Pipeline wall-clock time is the sum of all stage durations | Use language-native concurrency (`errgroup`, `asyncio.gather`, `Promise.all`) for independent stages |
| Ignoring exit codes and error returns | Silent failures that produce misleading green pipelines | Check every `error` return explicitly; wrap with context using `fmt.Errorf("%w")` |
| Hardcoding versions | Reproducibility breaks when base images or tools update | Accept versions as optional function parameters with sensible defaults |
| Mixing CI-provider environment variables into pipeline code | Breaks portability; pipeline now depends on `$GITHUB_SHA` or `$CI_COMMIT_SHA` | Accept all environment-dependent values as function parameters; pass them from the thin CI trigger script |
| Not splitting independent operations | The entire pipeline re-executes when any input changes | Structure pipeline functions so that lint, test, scan, and build are separate Dagger operations, allowing the DAG engine to cache each independently |

## Quiz

### Question 1

What makes Dagger pipelines portable across CI systems, and what is the mechanism that enables this portability?

<details>
<summary>Show Answer</summary>

Dagger pipelines are portable because the pipeline logic is expressed as a DAG of container operations, not as CI-provider-specific YAML. The Dagger Engine executes this DAG identically on any machine with a container runtime (Docker or Podman). The CI provider's configuration file shrinks to a thin trigger: install the Dagger CLI, check out the repository, and run `dagger call <function> --source=.`. The same pipeline code runs on a macOS laptop, an Ubuntu GitHub Actions runner, a GitLab CI Docker executor, or a CircleCI machine — because the engine, not the CI provider, controls how each step executes. The portability mechanism is the container itself: every pipeline step runs in an isolated container with explicitly declared inputs, so the execution environment is determined by the container image, not by the host machine's installed packages or configuration.
</details>

### Question 2

How does Dagger's content-addressed caching differ from traditional CI provider caching, and why does this difference matter for monorepos with multiple services?

<details>
<summary>Show Answer</summary>

Traditional CI provider caching operates at the directory level: you cache `node_modules` or `~/.gradle` using a cache key typically derived from a lockfile hash. When the key changes, the entire cache is invalidated. Dagger's caching operates at the operation level: each `WithExec`, `WithDirectory`, and `From` call produces a cache entry keyed by a content hash of all its inputs (base image digest, directory contents, environment variables, command string). Operations whose content hash matches a previous execution are skipped entirely; their output is retrieved from cache.

For monorepos, this matters because changing one service's source code invalidates only the operations that depend on that service. Tests, lints, and builds for other services — whose inputs have not changed — are served from cache. With traditional caching, a single lockfile change invalidates the entire dependency cache for all services, forcing a full rebuild. Dagger's granularity means the pipeline runtime scales with the size of the change, not the size of the repository.
</details>

### Question 3

You need to run lint, test, and security scan in parallel in a Go Dagger module. Write the code and explain why `errgroup` is the appropriate concurrency primitive.

<details>
<summary>Show Answer</summary>

```go
import "golang.org/x/sync/errgroup"

func (m *MyApp) CI(ctx context.Context, source *Directory) error {
    eg, ctx := errgroup.WithContext(ctx)

    eg.Go(func() error {
        _, err := m.Lint(ctx, source)
        if err != nil {
            return fmt.Errorf("lint: %w", err)
        }
        return nil
    })

    eg.Go(func() error {
        _, err := m.Test(ctx, source)
        if err != nil {
            return fmt.Errorf("test: %w", err)
        }
        return nil
    })

    eg.Go(func() error {
        _, err := m.SecurityScan(ctx, source)
        if err != nil {
            return fmt.Errorf("security: %w", err)
        }
        return nil
    })

    return eg.Wait()  // Returns first error if any
}
```

`errgroup` is appropriate because it provides three guarantees that align with pipeline execution: (1) it runs goroutines concurrently, so lint, test, and scan execute in parallel; (2) it cancels the context of remaining goroutines when the first error is returned, preventing wasted work; (3) `eg.Wait()` blocks until all goroutines finish and returns the first non-nil error, which is exactly the behavior you want in a CI pipeline — fail fast on the first problem, report it clearly, and don't waste resources on subsequent stages that would likely fail anyway.
</details>

### Question 4

How do you securely pass a container registry password to a Dagger pipeline? Explain the mechanism and why it is safer than using environment variables directly in shell scripts.

<details>
<summary>Show Answer</summary>

Use the `*Secret` type in your function signature and pass the value at invocation time with the `env:` prefix:

```go
func (m *MyApp) Publish(
    ctx context.Context,
    source *Directory,
    password *Secret,
) (string, error) {
    return dag.Container().
        From("golang:1.22").
        WithRegistryAuth("ghcr.io", "user", password).
        Publish(ctx, "ghcr.io/org/app:latest")
}
```

```bash
dagger call publish --password=env:GITHUB_TOKEN
```

This mechanism is safer than using environment variables directly in shell scripts for three reasons. First, Dagger's `*Secret` type is designed to prevent the value from appearing in logs — the engine redacts secret values from stdout and stderr output. Second, the secret is not stored in plaintext in the operation graph; it is held in memory and passed securely to the container runtime. Third, unlike a shell script where any command can accidentally `echo $PASSWORD`, the secret is scoped to the specific function that declares it as a parameter and is not available to other operations unless explicitly passed. The `env:` and `file:` prefixes at invocation time also keep the secret out of shell history and CI job configuration files.
</details>

### Question 5

Your Dagger pipeline works locally but fails in GitHub Actions with "no space left on device." The Docker image being built is approximately 2GB. Diagnose the root cause and propose solutions in order of preference.

<details>
<summary>Show Answer</summary>

**Root cause:** GitHub Actions runners have limited disk space (approximately 14GB free on `ubuntu-latest`). Dagger's caching, combined with large intermediate container images and base image layers, is consuming the available disk.

**Solutions, in order of preference:**

1. **Use multi-stage builds with a minimal runtime image.** Build in a full Go/Node/Python image, but copy only the compiled artifact into a distroless or Alpine runtime image. A Go binary compiled with `CGO_ENABLED=0` can run in `gcr.io/distroless/static` (~2MB), reducing the final image from 2GB to under 50MB.

2. **Clean up Docker before Dagger runs.** Add a step before Dagger execution: `docker system prune -af && docker volume prune -f`. Also remove unused pre-installed toolchains from the runner (`sudo rm -rf /usr/share/dotnet /opt/ghc`).

3. **Be selective about cache volumes.** Do not cache large build artifacts that are quick to recreate. Mount `CacheVolume` only for package manager directories (`/go/pkg/mod`, `~/.npm`, `~/.cache/pip`), not for `$GOPATH/pkg` or build output directories.

4. **Use Dagger Cloud for remote caching.** Configure `DAGGER_CLOUD_TOKEN` so that cache data is stored remotely rather than on the ephemeral runner disk.

5. **Use a larger runner.** GitHub Actions offers runners with more disk space (e.g., `ubuntu-latest-4-cores`) as a paid option.

The best practice is to address the root cause (large images) with multi-stage builds first, then add cache hygiene as a defense-in-depth measure.
</details>

### Question 6

Design a reusable Dagger module for Go microservices that handles build, test, lint, and container publish. What is the interface, and how do 10 consuming microservice repositories use it without duplicating logic?

<details>
<summary>Show Answer</summary>

**Module interface (Go SDK):**

```go
// modules/go-service/main.go
package main

import (
    "context"
    "fmt"
)

type GoService struct{}

// Build compiles the Go application with configurable version
func (m *GoService) Build(
    ctx context.Context,
    source *Directory,
    goVersion Optional[string],
    mainPackage Optional[string],
) *File {
    version := goVersion.GetOr("1.22")
    pkg := mainPackage.GetOr(".")

    return dag.Container().
        From(fmt.Sprintf("golang:%s-alpine", version)).
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithMountedCache("/go/pkg/mod", dag.CacheVolume("go-mod")).
        WithMountedCache("/root/.cache/go-build", dag.CacheVolume("go-build")).
        WithEnvVariable("CGO_ENABLED", "0").
        WithExec([]string{"go", "build", "-ldflags=-s -w", "-o", "/app", pkg}).
        File("/app")
}

// Test runs unit tests with race detection and coverage
func (m *GoService) Test(
    ctx context.Context,
    source *Directory,
    goVersion Optional[string],
) (string, error) {
    version := goVersion.GetOr("1.22")
    return dag.Container().
        From(fmt.Sprintf("golang:%s", version)).
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithMountedCache("/go/pkg/mod", dag.CacheVolume("go-mod")).
        WithExec([]string{"go", "test", "-v", "-race", "-coverprofile=cover.out", "./..."}).
        Stdout(ctx)
}

// Lint runs golangci-lint
func (m *GoService) Lint(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golangci/golangci-lint:v1.60").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"golangci-lint", "run", "--timeout", "5m"}).
        Stdout(ctx)
}

// Image builds a minimal runtime image
func (m *GoService) Image(
    source *Directory,
    goVersion Optional[string],
    baseImage Optional[string],
) *Container {
    binary := m.Build(context.Background(), source, goVersion, Optional[string]{})
    base := baseImage.GetOr("gcr.io/distroless/static")
    return dag.Container().
        From(base).
        WithFile("/app", binary).
        WithEntrypoint([]string{"/app"})
}

// CI runs the full quality pipeline: lint and test in parallel
func (m *GoService) CI(ctx context.Context, source *Directory) error {
    eg, ctx := errgroup.WithContext(ctx)
    eg.Go(func() error { _, err := m.Lint(ctx, source); return err })
    eg.Go(func() error { _, err := m.Test(ctx, source); return err })
    return eg.Wait()
}
```

**Consumption across 10 microservices:**

```bash
# In each microservice repository
dagger install github.com/myorg/dagger-modules/go-service

# Run the full CI pipeline
dagger call go-service ci --source=.

# Build and publish with service-specific configuration
dagger call go-service publish \
  --source=. \
  --registry=ghcr.io/myorg/user-service \
  --tag=v1.0.0 \
  --username=$USER \
  --password=env:GITHUB_TOKEN
```

The benefits: a single source of truth for Go build logic, updates to the module apply to all 10 services on the next pipeline run, sensible defaults with explicit override capability at each call site, and consistent caching across services — the `go-mod` CacheVolume is shared, so when service A downloads a dependency, service B's build gets a cache hit.
</details>

### Question 7

Compare the debugging workflow for a failing pipeline that cannot connect to a PostgreSQL database. The failure is "connection refused to localhost:5432." Walk through the debugging experience in a traditional Jenkins pipeline versus a Dagger pipeline, and explain how Dagger's service binding mechanism solves the problem.

<details>
<summary>Show Answer</summary>

**Traditional Jenkins debugging:**

1. Pipeline fails in CI. You wait 15+ minutes for the failure notification, then read truncated logs in the Jenkins UI.
2. You try to reproduce locally: "It works on my machine." Your local environment has PostgreSQL running; the CI environment does not.
3. You add debug statements to the Jenkinsfile: `sh 'env | sort'`, `sh 'docker ps'`. Each change requires a commit and a 15-minute wait cycle.
4. After several iterations, you discover the CI environment does not have PostgreSQL. You add a Docker Compose step. This requires more commit-push-wait cycles.
5. Total debugging time: 2+ hours. Commits: 5+. Most commits are debug instrumentation that must be reverted.

**Dagger debugging:**

1. Pipeline fails. You run it locally: `dagger call test --source=.`. Same error in 30 seconds — reproduced.
2. You open an interactive shell: `dagger call test --source=. terminal`. Inside the container, you run `psql -h localhost` and confirm PostgreSQL is not available.
3. You add a PostgreSQL service binding to the function:
```go
func (m *MyApp) Test(ctx context.Context, source *Directory) (string, error) {
    db := dag.Container().
        From("postgres:15-alpine").
        WithEnvVariable("POSTGRES_PASSWORD", "test").
        WithExposedPort(5432).
        AsService()

    return dag.Container().
        From("golang:1.22").
        WithServiceBinding("db", db).
        WithDirectory("/src", source).
        WithEnvVariable("DATABASE_URL", "postgres://postgres:test@db:5432/testdb").
        WithExec([]string{"go", "test", "./..."}).
        Stdout(ctx)
}
```
4. You test locally: `dagger call test --source=.` — passes. Push once with the fix.
5. Total debugging time: 15 minutes. Commits: 1 (the actual fix).

The key difference is local reproducibility. Dagger runs the exact same containers with the exact same configuration on your laptop and in CI. Service dependencies that are implicit in a developer's environment (a locally running PostgreSQL) become explicit in the pipeline definition through `AsService()` and `WithServiceBinding()`, which ensures environment parity between local and CI execution.
</details>

## Hands-On Exercise

### Scenario: Build a Dagger Pipeline

Create a Dagger pipeline for a Go application with lint, test, build, and publish stages. You will initialize a Dagger module, write pipeline functions, run them locally, and verify that the same commands work in CI.

### Setup

```bash
# Create project directory
mkdir dagger-lab && cd dagger-lab

# Create a simple Go application
cat > main.go << 'EOF'
package main

import "fmt"

func main() {
    fmt.Println(Greet("World"))
}

func Greet(name string) string {
    return fmt.Sprintf("Hello, %s!", name)
}
EOF

cat > main_test.go << 'EOF'
package main

import "testing"

func TestGreet(t *testing.T) {
    result := Greet("Dagger")
    expected := "Hello, Dagger!"
    if result != expected {
        t.Errorf("got %s, want %s", result, expected)
    }
}
EOF

cat > go.mod << 'EOF'
module dagger-lab

go 1.22
EOF

# Initialize Dagger
dagger init --sdk=go
```

### Write the Pipeline

```go
// Replace main.go in dagger directory with:
// dagger/main.go

package main

import (
    "context"
    "fmt"
)

type DaggerLab struct{}

// Lint runs golangci-lint
func (m *DaggerLab) Lint(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golangci/golangci-lint:v1.60").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"golangci-lint", "run", "--timeout", "5m"}).
        Stdout(ctx)
}

// Test runs go test
func (m *DaggerLab) Test(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golang:1.22").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "test", "-v", "./..."}).
        Stdout(ctx)
}

// Build compiles the application
func (m *DaggerLab) Build(source *Directory) *Container {
    return dag.Container().
        From("golang:1.22-alpine").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithMountedCache("/go/pkg/mod", dag.CacheVolume("go-mod")).
        WithExec([]string{"go", "build", "-o", "app", "."})
}

// BuildImage creates a minimal container image
func (m *DaggerLab) BuildImage(source *Directory) *Container {
    // Build stage
    builder := m.Build(source)

    // Runtime stage (minimal image)
    return dag.Container().
        From("alpine:latest").
        WithFile("/app", builder.File("/src/app")).
        WithEntrypoint([]string{"/app"})
}

// All runs lint, test, and build
func (m *DaggerLab) All(ctx context.Context, source *Directory) error {
    if _, err := m.Lint(ctx, source); err != nil {
        return err
    }

    if _, err := m.Test(ctx, source); err != nil {
        return err
    }

    _ = m.Build(source)

    return nil
}
```

### Run the Pipeline

```bash
# Run individual stages
dagger call lint --source=.
dagger call test --source=.
dagger call build --source=.

# Run all stages
dagger call all --source=.

# Build container image
dagger call build-image --source=.
```

### Add to GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI
on: [push]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dagger/dagger-for-github@v5
      - run: dagger call all --source=.
```

### Success Criteria

- [ ] Dagger module initialized with `dagger init --sdk=go`
- [ ] Lint function runs successfully with `dagger call lint --source=.`
- [ ] Test function passes with `dagger call test --source=.`
- [ ] Build function produces a binary inside a container
- [ ] All function runs the complete pipeline and reports results
- [ ] You can explain how CacheVolume differs from operation-level caching

## Next Module

Continue to [Module 3.2: Tekton](../module-3.2-tekton/) where we will explore Kubernetes-native pipelines and how they compare to the containerized pipeline model you have learned here.

---

*"The best CI/CD pipeline is the one you can run on your laptop. Dagger makes every pipeline local-first."*

## Sources

- [Dagger Documentation](https://docs.dagger.io/) — The authoritative reference for Dagger Engine, SDKs, CLI, and features. Current as of version 0.21.x.
- [Getting Started with Dagger](https://docs.dagger.io/getting-started) — Installation, core concepts, and quickstart guides for building CI workflows and AI agents with Dagger.
- [Dagger API & SDK Reference](https://docs.dagger.io/reference/) — Current API reference for the Go, Python, and TypeScript SDK types, installation, and methods.
- [Extending Dagger with the SDKs](https://docs.dagger.io/extending/) — How the language SDKs (Go, Python, TypeScript) construct the operation graph; decorators, types, and async patterns.
- [Dagger Features: Caching](https://docs.dagger.io/features/caching) — Documentation on Dagger's content-addressed caching, CacheVolumes, and Dagger Cloud shared caching.
- [Dagger Features: Modules](https://docs.dagger.io/features/modules) — Module creation, publishing, installation, and the Daggerverse module ecosystem.
- [Dagger Core Concepts: Functions](https://docs.dagger.io/core-concepts/functions) — How Dagger Functions work, argument passing, return types, and function composition.
- [dagger/dagger](https://github.com/dagger/dagger) — Upstream Dagger repository including the engine, CLI, SDKs, and documentation source.
- [dagger/dagger-for-github](https://github.com/dagger/dagger-for-github) — Official GitHub Action for installing Dagger in GitHub Actions workflows.
- [Dagger SDK Source Tree](https://github.com/dagger/dagger/tree/main/sdk) — Source implementations for the Go, Python, TypeScript, Java, and Elixir SDKs.
- [Dagger Quickstart: CI](https://docs.dagger.io/getting-started/quickstarts/ci) — Step-by-step guide for building a CI pipeline with Dagger.
- [Dagger Cookbook](https://docs.dagger.io/cookbook) — Practical recipes for common pipeline patterns, including multi-stage builds and secrets management.
- [Dagger FAQ](https://docs.dagger.io/faq) — Frequently asked questions about Dagger's architecture, capabilities, and relationship to other tools.
- [Dagger Use Cases](https://docs.dagger.io/use-cases) — Overview of scenarios where Dagger provides value, including CI/CD, local development, and AI agent workflows.
- [Dagger Installation Guide](https://docs.dagger.io/getting-started/installation) — Platform-specific installation instructions for macOS, Linux, and Windows.
- [BuildKit Documentation](https://docs.docker.com/build/buildkit/) — Docker BuildKit, the content-addressable build system whose caching model Dagger extends to arbitrary pipeline operations.
- [OCI Image Specification](https://github.com/opencontainers/image-spec) — The Open Container Initiative image format specification, which underpins the container images Dagger builds and publishes.
- [Tekton Documentation](https://tekton.dev/docs/) — Kubernetes-native CI/CD framework for comparison with Dagger's containerized pipeline model.
- [Argo Workflows Documentation](https://argoproj.github.io/workflows/) — Kubernetes-native workflow engine, included in the Rosetta for comparison with Dagger's approach to pipeline definition and execution.
- [CNCF Project List](https://www.cncf.io/projects/) — Confirms Dagger is not a CNCF project; Tekton and Argo are graduated CNCF projects.
