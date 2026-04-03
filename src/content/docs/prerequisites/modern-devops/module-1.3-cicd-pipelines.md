---
title: "Module 1.3: CI/CD Pipelines"
slug: prerequisites/modern-devops/module-1.3-cicd-pipelines
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Essential automation
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Module 1 (IaC), basic Git

---

## Why This Module Matters

Every time you push code, it should be automatically tested, built, and prepared for deployment. CI/CD pipelines eliminate the "it works on my machine" problem and ensure consistent, reliable releases. For Kubernetes applications, CI/CD is how container images get built and how deployments get triggered.

---

## CI vs CD

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD PIPELINE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTINUOUS INTEGRATION (CI)                                │
│  "Merge code frequently, validate every change"            │
│                                                             │
│  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────────┐            │
│  │Code │───►│Build│───►│Test │───►│Artifact │            │
│  │Push │    │     │    │     │    │(image)  │            │
│  └─────┘    └─────┘    └─────┘    └─────────┘            │
│                                                             │
│  CONTINUOUS DELIVERY (CD)                                   │
│  "Always deployable, one-click production deploy"          │
│                                                             │
│  ┌─────────┐    ┌───────────┐    ┌──────────┐            │
│  │Artifact │───►│Deploy to  │───►│ Manual   │            │
│  │(image)  │    │Staging    │    │ Approval │            │
│  └─────────┘    └───────────┘    └────┬─────┘            │
│                                       │                    │
│                                       ▼                    │
│                              ┌──────────────┐             │
│                              │Deploy to Prod│             │
│                              └──────────────┘             │
│                                                             │
│  CONTINUOUS DEPLOYMENT                                      │
│  "Every change goes straight to production"                │
│  (Same as above, but no manual approval step)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CI Pipeline Stages

### 1. Source

```yaml
# Trigger on code push
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

### 2. Build

```yaml
# Build the application
steps:
  - name: Build
    run: |
      npm install
      npm run build
```

### 3. Test

```yaml
# Run all tests
steps:
  - name: Unit Tests
    run: npm test

  - name: Integration Tests
    run: npm run test:integration

  - name: Lint
    run: npm run lint
```

### 4. Security Scan

```yaml
# Scan for vulnerabilities
steps:
  - name: Security Scan
    run: |
      npm audit
      trivy fs .
```

### 5. Build Image

```yaml
# Create container image
steps:
  - name: Build Docker Image
    run: |
      docker build -t myapp:${{ github.sha }} .
      docker push myapp:${{ github.sha }}
```

---

## CI/CD Tools Landscape

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD TOOLS                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLOUD-HOSTED (SaaS)                                       │
│  ├── GitHub Actions     (integrated with GitHub)           │
│  ├── GitLab CI/CD       (integrated with GitLab)           │
│  ├── CircleCI           (cloud-native, fast)               │
│  └── Travis CI          (open source friendly)             │
│                                                             │
│  SELF-HOSTED                                               │
│  ├── Jenkins            (most flexible, oldest)            │
│  ├── GitLab Runner      (self-hosted GitLab CI)            │
│  ├── Drone              (container-native)                 │
│  └── Tekton             (Kubernetes-native)                │
│                                                             │
│  KUBERNETES-NATIVE                                          │
│  ├── Tekton             (pipelines as CRDs)                │
│  ├── Argo Workflows     (workflow orchestration)           │
│  └── JenkinsX           (Jenkins for K8s)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## GitHub Actions (Most Popular)

### Basic Workflow

```yaml
# .github/workflows/ci.yaml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Run lint
        run: npm run lint

  build:
    needs: test  # Only run if tests pass
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Push image
        run: |
          docker tag myapp:${{ github.sha }} ghcr.io/${{ github.repository }}:${{ github.sha }}
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| `workflow` | A configurable automated process |
| `job` | A set of steps that run on the same runner |
| `step` | Individual task (run command or action) |
| `action` | Reusable unit of code |
| `runner` | Machine that executes the workflow |
| `secrets` | Encrypted environment variables |

---

## GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  image: node:20
  script:
    - npm ci
    - npm test
    - npm run lint
  cache:
    paths:
      - node_modules/

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $DOCKER_IMAGE .
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $DOCKER_IMAGE
  only:
    - main

deploy_staging:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$DOCKER_IMAGE
  environment:
    name: staging
  only:
    - main

deploy_production:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$DOCKER_IMAGE
  environment:
    name: production
  when: manual  # Requires click to deploy
  only:
    - main
```

---

## Pipeline for Kubernetes

A typical Kubernetes CI/CD pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CI/CD PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CODE                                                    │
│     └── Developer pushes to Git                            │
│                                                             │
│  2. BUILD                                                   │
│     ├── Run unit tests                                     │
│     ├── Run integration tests                              │
│     ├── Static analysis (lint, security)                   │
│     └── Build container image                              │
│                                                             │
│  3. PUBLISH                                                 │
│     ├── Tag image with commit SHA                          │
│     ├── Push to container registry                         │
│     └── Scan image for vulnerabilities                     │
│                                                             │
│  4. UPDATE MANIFESTS                                        │
│     └── Update Kubernetes YAML with new image tag          │
│         (For GitOps: commit to GitOps repo)               │
│                                                             │
│  5. DEPLOY                                                  │
│     ├── GitOps: Agent detects change and syncs            │
│     └── Or: Pipeline applies kubectl/helm                  │
│                                                             │
│  6. VERIFY                                                  │
│     ├── Smoke tests against deployed app                   │
│     └── Rollback if failed                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Complete Example

```yaml
# .github/workflows/kubernetes.yaml
name: Kubernetes CI/CD

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go test ./...

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  update-manifests:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: myorg/gitops-repo
          token: ${{ secrets.GITOPS_TOKEN }}

      - name: Update image tag
        run: |
          cd apps/myapp
          kustomize edit set image myapp=${{ needs.build-and-push.outputs.image-tag }}

      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Update myapp to ${{ github.sha }}"
          git push
```

---

## Pipeline Best Practices

### 1. Fast Feedback

```yaml
# Run quick checks first
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: npm run lint  # Fast, catches obvious issues

  unit-test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test      # Medium speed

  integration-test:
    needs: [lint, unit-test]  # Only if fast checks pass
    runs-on: ubuntu-latest
    steps:
      - run: npm run test:e2e  # Slow, but important
```

### 2. Cache Dependencies

```yaml
- name: Cache node modules
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### 3. Use Matrix Builds

```yaml
# Test on multiple versions
jobs:
  test:
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test
```

### 4. Secure Secrets

```yaml
# Never echo secrets!
- name: Deploy
  env:
    KUBE_CONFIG: ${{ secrets.KUBECONFIG }}
  run: |
    echo "$KUBE_CONFIG" | base64 -d > kubeconfig
    kubectl --kubeconfig=kubeconfig apply -f manifests/
    rm kubeconfig  # Clean up
```

---

## CI/CD Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Manual steps | Human error, slow | Automate everything |
| Flaky tests | Ignore failures, lose trust | Fix or delete flaky tests |
| Long pipelines | Slow feedback | Parallelize, cache |
| Deploy from laptop | No audit trail | Always deploy via pipeline |
| Shared credentials | Security risk | Service accounts per env |
| No rollback plan | Stuck with broken release | Automate rollback |

---

## Did You Know?

- **Jenkins is 20+ years old** (started as Hudson in 2004). Despite its age, it still runs millions of pipelines daily.

- **GitHub Actions runners** are fresh VMs for each job. You get a clean environment every time, preventing "works on my machine" issues.

- **The world's largest CI system** is Google's. It runs millions of builds per day on a distributed test infrastructure called TAP (Test Automation Platform).

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Tests in Docker build | Slow builds, cached test failures | Separate test and build stages |
| Latest tag for base images | Unpredictable builds | Pin versions |
| Not validating YAML | Runtime failures | Add validation step |
| Long-lived feature branches | Merge conflicts | Short branches, frequent merges |
| Skipping CI for "small changes" | Small bugs slip through | CI for everything |

---

## Quiz

1. **What's the difference between Continuous Delivery and Continuous Deployment?**
   <details>
   <summary>Answer</summary>
   Continuous Delivery: Every change is deployable, but production deployment requires manual approval. Continuous Deployment: Every change automatically goes to production (no manual step).
   </details>

2. **Why should you tag container images with commit SHA instead of "latest"?**
   <details>
   <summary>Answer</summary>
   Commit SHA provides traceability (know exactly what code is running), enables rollback (deploy previous SHA), and prevents caching issues ("latest" might be cached as an old version).
   </details>

3. **What's the purpose of caching in CI pipelines?**
   <details>
   <summary>Answer</summary>
   Caching reuses expensive operations (like downloading dependencies) across pipeline runs. This speeds up pipelines significantly, often from 10+ minutes to 1-2 minutes.
   </details>

4. **How does CI/CD integrate with GitOps?**
   <details>
   <summary>Answer</summary>
   CI builds and pushes images. Then CI updates the GitOps repo with the new image tag. The GitOps agent detects the change and syncs to the cluster. CI doesn't directly touch the cluster.
   </details>

---

## Hands-On Exercise

**Task**: Create a local CI simulation.

```bash
# This simulates what a CI pipeline does

# 1. Create project structure
mkdir -p ~/ci-demo
cd ~/ci-demo

# 2. Create a simple app
cat << 'EOF' > app.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

if __name__ == "__main__":
    print("Hello from CI demo!")
EOF

# 3. Create tests
cat << 'EOF' > test_app.py
import app

def test_add():
    assert app.add(2, 3) == 5

def test_subtract():
    assert app.subtract(5, 3) == 2
EOF

# 4. Create Dockerfile
cat << 'EOF' > Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
EOF

# 5. Simulate CI stages

echo "=== STAGE: Lint ==="
# In real CI: run linter
python3 -m py_compile app.py && echo "Lint passed!"

echo ""
echo "=== STAGE: Test ==="
# In real CI: pytest
pip3 install pytest -q 2>/dev/null
python3 -m pytest test_app.py -v

echo ""
echo "=== STAGE: Build ==="
# Build image
docker build -t ci-demo:$(git rev-parse --short HEAD 2>/dev/null || echo "local") .

echo ""
echo "=== STAGE: Security Scan ==="
# In real CI: trivy, snyk, etc.
echo "Scanning image... (simulated)"
echo "No vulnerabilities found!"

echo ""
echo "=== STAGE: Push ==="
echo "Would push to: registry/ci-demo:$(git rev-parse --short HEAD 2>/dev/null || echo "local")"
echo "(Skipping actual push for demo)"

# 6. Cleanup
cd ..
rm -rf ~/ci-demo

echo ""
echo "=== CI Pipeline Complete ==="
```

**Success criteria**: Understand the stages of a CI pipeline.

---

## Summary

**CI/CD pipelines** automate the path from code to production:

**CI (Continuous Integration)**:
- Merge frequently
- Build and test every change
- Catch issues early

**CD (Continuous Delivery/Deployment)**:
- Always deployable
- Automated deployment
- Quick rollback

**Key practices**:
- Fast feedback (quick stages first)
- Cache dependencies
- Secure secrets
- Immutable artifacts (SHA-tagged images)

**For Kubernetes**:
- CI builds and pushes images
- Pipeline updates manifests (or GitOps repo)
- Deployment handled by kubectl/helm or GitOps agent

---

## Next Module

[Module 1.4: Observability Fundamentals](../module-1.4-observability/) - Monitoring, logging, and tracing.
