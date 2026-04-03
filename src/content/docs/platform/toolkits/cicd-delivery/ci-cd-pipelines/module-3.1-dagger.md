---
title: "Module 3.1: Dagger"
slug: platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.1-dagger
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

The senior engineer stared at the CI failure notification—the third one this hour. "It works on my machine," came the familiar refrain from the developer who'd pushed the change. After 40 minutes of debugging Jenkins logs and another 20 minutes trying to reproduce the issue, she finally found the problem: a subtle difference in the environment variable handling between the CI runner and local development. "If only we could run the exact same pipeline locally," she thought. Six months later, after migrating to Dagger, that wish became reality. Their CI pipeline became truly portable—developers ran the same pipeline on their laptops, catching 73% of issues before pushing. The company estimated the saved debugging time at **$180,000 per year** across their 45-person engineering team.

## Prerequisites

Before starting this module:
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) — CI/CD concepts
- Programming experience in Go, Python, or TypeScript
- Docker/container fundamentals
- Basic CI/CD pipeline experience

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Dagger pipelines in Go, Python, or TypeScript that run identically on local machines and CI systems**
- **Implement containerized CI/CD steps with explicit dependency management and caching strategies**
- **Deploy Dagger-based pipelines across multiple CI providers (GitHub Actions, GitLab CI, CircleCI) without rewriting logic**
- **Evaluate when Dagger's portable pipeline approach outperforms traditional YAML-based CI/CD configurations**


## Why This Module Matters

Traditional CI/CD pipelines are written in YAML—declarative, hard to test, impossible to debug locally. Dagger flips this: write your pipelines in real programming languages, run them anywhere, and debug locally before pushing.

Dagger is the "Docker for CI/CD"—portable pipelines that work the same on your laptop, in GitHub Actions, and in any CI system. No more "works on CI but not locally" debugging nightmares.

## Did You Know?

- **Dagger was founded by the creators of Docker**—Solomon Hykes, the creator of Docker, started Dagger to solve CI/CD the same way Docker solved environments
- **Dagger pipelines are 100% portable**—the same pipeline runs in GitHub Actions, GitLab CI, Jenkins, CircleCI, or your laptop
- **Dagger caches at the layer level like Docker**—unchanged pipeline steps are skipped, just like Docker layer caching
- **The name "Dagger" comes from the CI acronym**—"Devkit for Application Generation and Execution in Reproducible environments"

## What Makes Dagger Different

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL vs DAGGER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRADITIONAL CI (YAML)                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  jobs:                                                    │   │
│  │    build:                                                 │   │
│  │      runs-on: ubuntu-latest  ← Tied to runner            │   │
│  │      steps:                                               │   │
│  │        - run: npm install    ← Can't test locally        │   │
│  │        - run: npm test                                    │   │
│  │        - run: docker build   ← Different behavior local  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Problems:                                                       │
│  • Can't run locally                                            │
│  • Can't debug                                                  │
│  • Vendor lock-in                                               │
│  • YAML isn't a programming language                            │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  DAGGER (Code)                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  func (m *MyApp) Build(ctx context.Context) *Container { │   │
│  │    return dag.Container().                                │   │
│  │      From("node:20").                                     │   │
│  │      WithDirectory("/app", m.Source).                     │   │
│  │      WithExec([]string{"npm", "install"}).               │   │
│  │      WithExec([]string{"npm", "test"})                   │   │
│  │  }                                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Benefits:                                                       │
│  ✓ Run anywhere (laptop, CI, cloud)                             │
│  ✓ Real debugging (breakpoints, logs)                          │
│  ✓ Type safety and IDE support                                 │
│  ✓ Testable as regular code                                    │
│  ✓ Reusable modules                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Dagger Architecture

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

## Getting Started

### Installation

```bash
# Install Dagger CLI
curl -L https://dl.dagger.io/dagger/install.sh | sh

# Or with Homebrew
brew install dagger/tap/dagger

# Verify installation
dagger version
```

### Initialize a Project

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

```
myproject/
├── dagger.json          # Module configuration
├── dagger/              # Generated code
│   └── ...
└── main.go              # Your pipeline code (or main.py, index.ts)
```

## Writing Pipelines in Go

### Basic Pipeline

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
        From("golang:1.21").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "build", "-o", "app", "."})
}

// Test runs the test suite
func (m *MyApp) Test(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golang:1.21").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "test", "-v", "./..."}).
        Stdout(ctx)
}

// Lint checks code quality
func (m *MyApp) Lint(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golangci/golangci-lint:latest").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"golangci-lint", "run"}).
        Stdout(ctx)
}
```

### Running Pipelines

```bash
# Run build function
dagger call build --source=.

# Run test function
dagger call test --source=.

# Run lint function
dagger call lint --source=.
```

### Publishing Container Images

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
        From("golang:1.21-alpine").
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

### Caching

```go
func (m *MyApp) BuildWithCache(ctx context.Context, source *Directory) *Container {
    // Create a cache volume for Go modules
    goModCache := dag.CacheVolume("go-mod-cache")
    goBuildCache := dag.CacheVolume("go-build-cache")

    return dag.Container().
        From("golang:1.21").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        // Mount cache volumes
        WithMountedCache("/go/pkg/mod", goModCache).
        WithMountedCache("/root/.cache/go-build", goBuildCache).
        // Build with cache
        WithExec([]string{"go", "build", "-o", "app", "."})
}
```

### Parallel Execution

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
            .from_("python:3.11-slim")
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
            .from_("python:3.11-slim")
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
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "ruff"])
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["ruff", "check", "."])
            .stdout()
        )
```

### Python with UV (Fast Package Manager)

```python
@function
async def build_with_uv(self, source: dagger.Directory) -> dagger.Container:
    """Build with UV package manager for faster installs."""
    return (
        dag.container()
        .from_("python:3.11-slim")
        .with_exec(["pip", "install", "uv"])
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["uv", "pip", "install", "-r", "requirements.txt"])
    )
```

## Writing Pipelines in TypeScript

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
      .from("node:20-slim")
      .withDirectory("/app", source)
      .withWorkdir("/app")
      .withExec(["npm", "install"])
      .withExec(["npm", "run", "build"])
  }

  @func()
  async test(source: Directory): Promise<string> {
    return dag
      .container()
      .from("node:20-slim")
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
      .from("node:20-slim")
      .withDirectory("/app", source)
      .withWorkdir("/app")
      .withExec(["npm", "install"])
      .withExec(["npm", "run", "lint"])
      .stdout()
  }
}
```

## Dagger Modules

### Using Community Modules

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

```go
// Create a reusable Go builder module
// dagger/go-builder/main.go

package main

type GoBuilder struct{}

// Build compiles a Go application
func (m *GoBuilder) Build(
    source *Directory,
    goVersion Optional[string],
) *Container {
    version := goVersion.GetOr("1.21")

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
        From("golang:1.21").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "test", "-v", "./..."}).
        Stdout(context.Background())
}
```

## Integration with CI Systems

### GitHub Actions

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

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

variables:
  DAGGER_VERSION: "0.9.0"

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
    fmt.Println("🔍 Running lint...")
    if _, err := m.Lint(ctx, source); err != nil {
        return fmt.Errorf("lint failed: %w", err)
    }

    // Stage 2: Test
    fmt.Println("🧪 Running tests...")
    if _, err := m.Test(ctx, source); err != nil {
        return fmt.Errorf("tests failed: %w", err)
    }

    // Stage 3: Security scan
    fmt.Println("🔒 Running security scan...")
    if _, err := m.SecurityScan(ctx, source); err != nil {
        return fmt.Errorf("security scan failed: %w", err)
    }

    // Stage 4: Build and publish
    fmt.Println("📦 Building and publishing...")
    ref, err := m.Publish(ctx, source, registry, tag, password)
    if err != nil {
        return fmt.Errorf("publish failed: %w", err)
    }
    fmt.Printf("Published: %s\n", ref)

    // Stage 5: Deploy
    fmt.Println("🚀 Deploying...")
    if err := m.Deploy(ctx, kubeconfig, ref); err != nil {
        return fmt.Errorf("deploy failed: %w", err)
    }

    fmt.Println("✅ CICD complete!")
    return nil
}
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| No caching | Slow builds, repeated downloads | Use `CacheVolume` for package managers |
| Not using secrets | Exposed credentials in logs | Pass secrets via `*Secret` type |
| Large base images | Slow pulls, big attack surface | Use slim/alpine variants |
| Sequential when parallel is possible | Slow pipelines | Use `errgroup` for parallel execution |
| Ignoring exit codes | Silent failures | Check errors explicitly |
| Hardcoding versions | Reproducibility issues | Parameterize versions |

## War Story: The $2.3 Million 45-Minute Pipeline

A fintech startup with 65 engineers had a Jenkins pipeline from 2018 that nobody wanted to touch. It took **45 minutes per run**, with 8-12 runs per developer per day. Each step installed dependencies from scratch—no caching. Debugging required pushing commits and waiting. Nobody knew why certain Jenkins plugins were installed or what would break if removed.

The pipeline was so slow that developers started batching changes, leading to larger PRs, harder code reviews, and more merge conflicts. Friday deployments were banned because the pipeline would inevitably fail late in the day.

```
THE 45-MINUTE PIPELINE BREAKDOWN
─────────────────────────────────────────────────────────────────
Stage 1: Checkout                 2 min
Stage 2: Install Node             3 min (downloads every time)
Stage 3: npm install             12 min (no cache)
Stage 4: Lint                     4 min
Stage 5: Unit tests               8 min
Stage 6: Integration tests        6 min (sequential, not parallel)
Stage 7: Build                    5 min
Stage 8: Docker build             3 min
Stage 9: Push to registry         2 min
                                  ─────
TOTAL:                           45 min per run

Developer pattern: Push → Wait 45 min → Find typo → Fix → Wait 45 min
Average debug cycles per PR: 2.3
```

Then the release deadline incident happened.

```
THE RELEASE DEADLINE INCIDENT
─────────────────────────────────────────────────────────────────
THURSDAY, 3:00 PM    Critical security patch ready for release
THURSDAY, 3:05 PM    PR merged, pipeline starts
THURSDAY, 3:50 PM    Pipeline fails: "npm test timeout"
THURSDAY, 4:10 PM    Re-run pipeline (flaky test suspected)
THURSDAY, 4:55 PM    Pipeline fails: "Docker build OOM"
THURSDAY, 5:20 PM    Jenkins node restarted, retry
THURSDAY, 6:05 PM    Pipeline passes! Staging deployment
THURSDAY, 6:10 PM    QA finds regression
THURSDAY, 6:15 PM    Hotfix PR submitted
THURSDAY, 7:00 PM    Pipeline still running...
THURSDAY, 8:30 PM    Release finally deployed (5.5 hours late)
THURSDAY, 9:00 PM    Customer SLA violated, incident declared
```

**Financial Impact:**

```
ANNUAL COST OF SLOW PIPELINES
─────────────────────────────────────────────────────────────────
Developer wait time:
  - 65 devs × 3 runs/day × 45 min × 220 workdays
  - 1,930,500 minutes/year = 32,175 hours
  - At $75/hr effective rate = $2,413,125/year

Additional costs:
  - Larger PRs → more bugs → ~$150,000/year in bug fixes
  - Batched releases → more risk → ~$100,000/year in incidents
  - Friday deployment ban → delayed features → ~$200,000 opportunity cost
  - Jenkins infrastructure → $80,000/year

CI/CD inefficiency impact: ~$2,943,125/year
─────────────────────────────────────────────────────────────────
```

**The Dagger Migration:**

```go
// NEW: Dagger pipeline with caching and parallelism
func (m *Fintech) CI(ctx context.Context, source *Directory) error {
    // Cache volumes persist across runs
    nodeModules := dag.CacheVolume("node-modules")
    npmCache := dag.CacheVolume("npm-cache")

    base := dag.Container().
        From("node:20-slim").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithMountedCache("/app/node_modules", nodeModules).
        WithMountedCache("/root/.npm", npmCache).
        WithExec([]string{"npm", "ci"})  // Now ~30 seconds with cache

    // Run lint, unit tests, and security scan in PARALLEL
    eg, ctx := errgroup.WithContext(ctx)

    eg.Go(func() error { return m.Lint(ctx, base) })
    eg.Go(func() error { return m.UnitTest(ctx, base) })
    eg.Go(func() error { return m.SecurityScan(ctx, base) })

    if err := eg.Wait(); err != nil {
        return err
    }

    // Integration tests (must be sequential)
    return m.IntegrationTest(ctx, base)
}
```

```
NEW PIPELINE PERFORMANCE
─────────────────────────────────────────────────────────────────
Stage 1: Checkout                 0 min (Dagger handles)
Stage 2: npm ci with cache        0.5 min (was 12 min)
Stage 3: Parallel block           4 min total (was 12 min sequential)
         - Lint                   [parallel]
         - Unit tests             [parallel]
         - Security scan          [parallel]
Stage 4: Integration tests        3 min
Stage 5: Build + Docker           2 min (multi-stage, cached)
Stage 6: Push                     0.5 min
                                  ─────
TOTAL:                            10 min (was 45 min)

IMPROVEMENT: 77% faster
```

**ROI Calculation:**

```
SAVINGS AFTER DAGGER MIGRATION
─────────────────────────────────────────────────────────────────
Developer time saved:
  - Old: 45 min × 3 runs = 135 min/day
  - New: 10 min × 3 runs = 30 min/day
  - Savings: 105 min/dev/day

Annual savings:
  - 105 min × 65 devs × 220 days = 1,501,500 min = 25,025 hours
  - At $75/hr = $1,876,875/year

Local debugging (prevented CI roundtrips):
  - 1.5 fewer CI runs per PR (devs catch issues locally)
  - 65 devs × 1.5 runs × 35 min × 220 days = 750,750 min saved
  - Additional $937,687/year

Migration cost:
  - 2 engineers × 6 weeks = $120,000

NET ANNUAL SAVINGS: $2,694,562
PAYBACK PERIOD: 2.4 weeks
─────────────────────────────────────────────────────────────────
```

**Lessons Learned:**

1. **Local-first changes everything**—developers run `dagger call test` before pushing, catching 73% of issues locally
2. **Caching is exponential**—the second run of a pipeline should be 10x faster than the first
3. **Parallelism isn't optional**—sequential lint + test + scan is 3x slower than parallel
4. **Real code > YAML**—Go/Python/TS pipelines can be debugged, tested, and refactored
5. **Portability matters**—same pipeline works on laptop, GitHub Actions, GitLab, anywhere

## Quiz

### Question 1
What makes Dagger pipelines portable across CI systems?

<details>
<summary>Show Answer</summary>

Dagger pipelines run inside containers managed by the Dagger Engine. The CI system (GitHub Actions, GitLab, Jenkins) only needs to:
1. Install the Dagger CLI
2. Have Docker (or a compatible container runtime)
3. Run `dagger call <function>`

The pipeline logic is in your code, not in CI-specific YAML. The same code runs identically in any environment with Docker, including your laptop.
</details>

### Question 2
How does Dagger caching work?

<details>
<summary>Show Answer</summary>

Dagger caching works at two levels:

1. **Layer caching**: Like Docker, unchanged pipeline steps are cached. If you run the same container operations with the same inputs, Dagger reuses the cached result.

2. **Volume caching**: `CacheVolume` creates persistent volumes that survive across pipeline runs. Use these for package manager caches (npm, pip, go mod).

```go
goCache := dag.CacheVolume("go-mod")
container.WithMountedCache("/go/pkg/mod", goCache)
```

The cache persists locally and on CI (with proper CI cache configuration). Unchanged steps are skipped entirely.
</details>

### Question 3
You need to run lint, test, and security scan in parallel. Write the Go code.

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

The `errgroup` package runs goroutines concurrently and returns the first error encountered.
</details>

### Question 4
How do you securely pass a registry password to Dagger?

<details>
<summary>Show Answer</summary>

Use the `*Secret` type, which Dagger handles securely (never logged, encrypted in transit):

```go
func (m *MyApp) Publish(
    ctx context.Context,
    source *Directory,
    password *Secret,  // Secret type
) (string, error) {
    return dag.Container().
        From("golang:1.21").
        WithRegistryAuth("ghcr.io", "user", password).
        Publish(ctx, "ghcr.io/org/app:latest")
}
```

Pass secrets via CLI:
```bash
# From environment variable
dagger call publish --password=env:GITHUB_TOKEN

# From file
dagger call publish --password=file:./token.txt
```

Secrets are never exposed in logs or Dagger Cloud traces.
</details>

### Question 5
Calculate the time savings for a monorepo with 5 services. Each service has: npm install (8 min uncached, 30s cached), tests (4 min), build (2 min). Compare sequential vs parallel with Dagger caching.

<details>
<summary>Show Answer</summary>

**Sequential Execution (Traditional CI):**

```
SEQUENTIAL PIPELINE (per run)
─────────────────────────────────────────────────────────────────
Service A: npm install (8 min) + test (4 min) + build (2 min) = 14 min
Service B: npm install (8 min) + test (4 min) + build (2 min) = 14 min
Service C: npm install (8 min) + test (4 min) + build (2 min) = 14 min
Service D: npm install (8 min) + test (4 min) + build (2 min) = 14 min
Service E: npm install (8 min) + test (4 min) + build (2 min) = 14 min
                                                               ─────
TOTAL: 70 minutes
```

**Parallel with Dagger + Caching (First Run):**

```
FIRST RUN (cache miss)
─────────────────────────────────────────────────────────────────
All 5 services run in parallel:
- npm install: 8 min (shared cache starts building)
- tests: 4 min (parallel)
- build: 2 min (parallel)

Longest path determines total time:
  npm install + test + build = 8 + 4 + 2 = 14 min

TOTAL: 14 minutes (5x faster than sequential)
```

**Parallel with Dagger + Caching (Subsequent Runs):**

```
SUBSEQUENT RUNS (cache hit)
─────────────────────────────────────────────────────────────────
All 5 services run in parallel:
- npm install: 30 sec (CACHED!)
- tests: 4 min (parallel, some cached if unchanged)
- build: 2 min (parallel, layer caching)

Longest path: 0.5 + 4 + 2 = 6.5 min

TOTAL: 6.5 minutes (10.7x faster than sequential)
```

**Time Savings Calculation:**

```
DAILY SAVINGS (assuming 10 runs/day)
─────────────────────────────────────────────────────────────────
Sequential: 10 runs × 70 min = 700 min/day
Dagger (avg): 10 runs × 8 min (1 cold + 9 cached) = 80 min/day

Daily savings: 620 minutes
Weekly savings: 3,100 minutes (~52 hours)
Annual savings: ~2,700 hours

At $75/hr engineering cost: $202,500/year saved
```

**The Dagger code:**

```go
func (m *Monorepo) CI(ctx context.Context, source *Directory) error {
    services := []string{"service-a", "service-b", "service-c", "service-d", "service-e"}
    npmCache := dag.CacheVolume("npm-cache")

    eg, ctx := errgroup.WithContext(ctx)
    for _, svc := range services {
        svc := svc  // capture loop variable
        eg.Go(func() error {
            return m.BuildService(ctx, source.Directory(svc), npmCache)
        })
    }
    return eg.Wait()
}
```
</details>

### Question 6
Your Dagger pipeline works locally but fails in GitHub Actions with "no space left on device". The Docker image being built is 2GB. Diagnose and fix.

<details>
<summary>Show Answer</summary>

**The Problem:**

GitHub Actions runners have limited disk space (~14GB free on ubuntu-latest). Dagger's caching and the large image are consuming it.

**Diagnosis:**

```yaml
# Add this step to see disk usage
- name: Check disk space
  run: df -h
```

**Solutions (in order of preference):**

**1. Use multi-stage builds (reduce image size):**

```go
func (m *MyApp) BuildImage(source *Directory) *Container {
    // Build stage
    builder := dag.Container().
        From("golang:1.21").
        WithDirectory("/src", source).
        WithExec([]string{"go", "build", "-o", "app", "."})

    // Runtime stage (minimal)
    return dag.Container().
        From("gcr.io/distroless/static").  // ~2MB instead of 700MB
        WithFile("/app", builder.File("/src/app")).
        WithEntrypoint([]string{"/app"})
}
// Result: 2GB image → 50MB image
```

**2. Clean up Docker before Dagger runs:**

```yaml
- name: Free disk space
  run: |
    docker system prune -af
    docker volume prune -f
    sudo rm -rf /usr/share/dotnet
    sudo rm -rf /opt/ghc
```

**3. Use larger runners (paid):**

```yaml
jobs:
  build:
    runs-on: ubuntu-latest-4-cores  # More disk space
```

**4. Limit Dagger cache size:**

```go
// Don't cache everything - be selective
func (m *MyApp) Build(source *Directory) *Container {
    // Only cache what's expensive to recreate
    goModCache := dag.CacheVolume("go-mod")

    return dag.Container().
        From("golang:1.21-alpine").  // Alpine = smaller
        WithMountedCache("/go/pkg/mod", goModCache).
        // Don't cache build artifacts if they're huge
        WithDirectory("/src", source).
        WithExec([]string{"go", "build", "-o", "app", "."})
}
```

**5. Use Dagger Cloud (offload caching):**

```yaml
- name: Run Dagger
  env:
    DAGGER_CLOUD_TOKEN: ${{ secrets.DAGGER_CLOUD_TOKEN }}
  run: dagger call build --source=.
  # Dagger Cloud stores cache externally
```

**Best practice:** Always use multi-stage builds and distroless/Alpine base images. A 2GB image is almost always unnecessary.
</details>

### Question 7
Design a Dagger module that can be shared across 10 microservices. It should handle: Go build, test, lint, and container publish. What's the interface?

<details>
<summary>Show Answer</summary>

**Reusable Dagger Module Design:**

```go
// modules/go-service/main.go
package main

import (
    "context"
    "fmt"
)

// GoService is a reusable module for Go microservices
type GoService struct{}

// Config holds build configuration
type Config struct {
    GoVersion   string // e.g., "1.21"
    BaseImage   string // e.g., "gcr.io/distroless/static"
    BinaryName  string // e.g., "api-server"
    MainPackage string // e.g., "./cmd/server"
}

// WithDefaults returns config with sensible defaults
func (c Config) WithDefaults() Config {
    if c.GoVersion == "" {
        c.GoVersion = "1.21"
    }
    if c.BaseImage == "" {
        c.BaseImage = "gcr.io/distroless/static"
    }
    if c.BinaryName == "" {
        c.BinaryName = "app"
    }
    if c.MainPackage == "" {
        c.MainPackage = "."
    }
    return c
}

// Build compiles the Go application
func (m *GoService) Build(
    ctx context.Context,
    source *Directory,
    goVersion Optional[string],
    mainPackage Optional[string],
) *File {
    version := goVersion.GetOr("1.21")
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

// Test runs unit tests with coverage
func (m *GoService) Test(
    ctx context.Context,
    source *Directory,
    goVersion Optional[string],
) (string, error) {
    version := goVersion.GetOr("1.21")

    return dag.Container().
        From(fmt.Sprintf("golang:%s", version)).
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithMountedCache("/go/pkg/mod", dag.CacheVolume("go-mod")).
        WithExec([]string{"go", "test", "-v", "-race", "-coverprofile=cover.out", "./..."}).
        Stdout(ctx)
}

// Lint runs golangci-lint
func (m *GoService) Lint(
    ctx context.Context,
    source *Directory,
) (string, error) {
    return dag.Container().
        From("golangci/golangci-lint:v1.55").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"golangci-lint", "run", "--timeout", "5m"}).
        Stdout(ctx)
}

// Image builds a minimal container image
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

// Publish builds and pushes to registry
func (m *GoService) Publish(
    ctx context.Context,
    source *Directory,
    registry string,
    tag string,
    username string,
    password *Secret,
) (string, error) {
    image := m.Image(source, Optional[string]{}, Optional[string]{})
    ref := fmt.Sprintf("%s:%s", registry, tag)

    return image.
        WithRegistryAuth(registry, username, password).
        Publish(ctx, ref)
}

// CI runs full pipeline: lint, test, build
func (m *GoService) CI(
    ctx context.Context,
    source *Directory,
) error {
    eg, ctx := errgroup.WithContext(ctx)

    eg.Go(func() error {
        _, err := m.Lint(ctx, source)
        return err
    })

    eg.Go(func() error {
        _, err := m.Test(ctx, source)
        return err
    })

    return eg.Wait()
}
```

**Usage from microservices:**

```bash
# Install the shared module
dagger install github.com/myorg/dagger-modules/go-service

# Use in any microservice
dagger call go-service ci --source=.
dagger call go-service publish \
  --source=. \
  --registry=ghcr.io/myorg/user-service \
  --tag=v1.0.0 \
  --username=$USER \
  --password=env:GITHUB_TOKEN
```

**Benefits:**
- Single source of truth for build logic
- Updates to module apply to all 10 services
- Sensible defaults with override capability
- Consistent caching across services
</details>

### Question 8
Compare the debugging experience between a failing Jenkins pipeline and a failing Dagger pipeline. Your test is failing with "connection refused to localhost:5432" (PostgreSQL).

<details>
<summary>Show Answer</summary>

**Jenkins Debugging Experience:**

```
JENKINS DEBUGGING WORKFLOW
─────────────────────────────────────────────────────────────────
1. Pipeline fails in CI
   - Wait 15 minutes for failure notification
   - Read truncated logs in Jenkins UI

2. Try to reproduce locally
   - "It works on my machine"
   - Local has PostgreSQL running, CI doesn't
   - No way to run Jenkins pipeline locally

3. Add debugging to Jenkinsfile
   - Add: sh 'env | sort'
   - Push commit
   - Wait 15 minutes for new run

4. Check PostgreSQL service
   - Add: sh 'docker ps'
   - Push commit
   - Wait 15 minutes...

5. Still failing
   - Add more debug statements
   - Push commit
   - Wait 15 minutes...

Time to debug: 2+ hours
Commits polluted with debug statements: 5+
Developer frustration: HIGH
```

**Dagger Debugging Experience:**

```
DAGGER DEBUGGING WORKFLOW
─────────────────────────────────────────────────────────────────
1. Pipeline fails (same error)

2. Run locally:
   dagger call test --source=.
   # Same error: "connection refused to localhost:5432"
   # ← Reproduced in 30 seconds!

3. Debug with interactive shell:
   dagger call test --source=. terminal
   # Opens shell inside the container
   root@abc123:/app# psql -h localhost
   # Connection refused - PostgreSQL not running

4. Fix: Add PostgreSQL as a service
   func (m *MyApp) Test(ctx context.Context, source *Directory) (string, error) {
       postgres := dag.Container().
           From("postgres:15").
           WithEnvVariable("POSTGRES_PASSWORD", "test").
           AsService()

       return dag.Container().
           From("golang:1.21").
           WithServiceBinding("db", postgres).  // ← The fix!
           WithDirectory("/src", source).
           WithEnvVariable("DATABASE_URL", "postgres://postgres:test@db:5432/test").
           WithExec([]string{"go", "test", "./..."}).
           Stdout(ctx)
   }

5. Test locally:
   dagger call test --source=.
   # PASS

6. Push once with the fix

Time to debug: 15 minutes
Commits: 1 (the actual fix)
Developer frustration: LOW
```

**Key Differences:**

| Aspect | Jenkins | Dagger |
|--------|---------|--------|
| Reproduce locally | Usually impossible | Always works |
| Debug cycle time | 15+ minutes | Seconds |
| Interactive debugging | None | `dagger call ... terminal` |
| Service dependencies | Complex Docker Compose | `AsService()` built-in |
| Log access | Truncated UI | Full local logs |
| Environment parity | CI ≠ Local | CI = Local |

**Dagger Service Binding Pattern:**

```go
// The database isn't at "localhost" - it's a service binding
func (m *MyApp) TestWithDB(ctx context.Context, source *Directory) (string, error) {
    // Start PostgreSQL as a Dagger service
    db := dag.Container().
        From("postgres:15-alpine").
        WithEnvVariable("POSTGRES_PASSWORD", "test").
        WithEnvVariable("POSTGRES_DB", "testdb").
        WithExposedPort(5432).
        AsService()

    // Run tests with database bound
    return dag.Container().
        From("golang:1.21").
        WithServiceBinding("postgres", db).  // Available as "postgres:5432"
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithEnvVariable("DB_HOST", "postgres").
        WithEnvVariable("DB_PORT", "5432").
        WithExec([]string{"go", "test", "-v", "./..."}).
        Stdout(ctx)
}
```
</details>

## Hands-On Exercise

### Scenario: Build a Dagger Pipeline

Create a Dagger pipeline for a Go application with lint, test, build, and publish stages.

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

go 1.21
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
        From("golangci/golangci-lint:v1.55").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"golangci-lint", "run", "--timeout", "5m"}).
        Stdout(ctx)
}

// Test runs go test
func (m *DaggerLab) Test(ctx context.Context, source *Directory) (string, error) {
    return dag.Container().
        From("golang:1.21").
        WithDirectory("/src", source).
        WithWorkdir("/src").
        WithExec([]string{"go", "test", "-v", "./..."}).
        Stdout(ctx)
}

// Build compiles the application
func (m *DaggerLab) Build(source *Directory) *Container {
    return dag.Container().
        From("golang:1.21-alpine").
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
    fmt.Println("🔍 Linting...")
    if _, err := m.Lint(ctx, source); err != nil {
        return err
    }

    fmt.Println("🧪 Testing...")
    if _, err := m.Test(ctx, source); err != nil {
        return err
    }

    fmt.Println("🔨 Building...")
    _ = m.Build(source)

    fmt.Println("✅ All checks passed!")
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

# Export the image
dagger call build-image --source=. export --path=./image.tar
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

- [ ] Dagger module initialized
- [ ] Lint function works
- [ ] Test function works
- [ ] Build function produces binary
- [ ] All function runs complete pipeline
- [ ] Understand caching with CacheVolume

### Cleanup

```bash
cd .. && rm -rf dagger-lab
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain why Dagger pipelines are portable (containerized execution, same locally and in CI)
- [ ] Initialize a Dagger module with `dagger init --sdk=go/python/typescript`
- [ ] Write pipeline functions that return `*Container`, `*File`, or `(string, error)`
- [ ] Use `CacheVolume` to persist package manager caches across runs
- [ ] Implement parallel execution with `errgroup` for independent tasks
- [ ] Pass secrets securely with `*Secret` type and `env:/file:` references
- [ ] Add service dependencies with `AsService()` and `WithServiceBinding()`
- [ ] Debug pipelines locally with `dagger call ... terminal` for interactive access
- [ ] Create reusable Dagger modules for shared build logic
- [ ] Integrate Dagger with GitHub Actions, GitLab CI, or any CI system

## Next Module

Continue to [Module 3.2: Tekton](../module-3.2-tekton/) where we'll explore Kubernetes-native pipelines.

---

*"The best CI/CD pipeline is the one you can run on your laptop. Dagger makes every pipeline local-first."*
