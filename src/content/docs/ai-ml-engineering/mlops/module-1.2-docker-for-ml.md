---
title: "Docker for ML"
slug: ai-ml-engineering/mlops/module-5.2-docker-for-ml
sidebar:
  order: 603
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6
## The $165 Million Bug That Containers Could Have Prevented

**NASA's Jet Propulsion Laboratory. September 23, 1999.**

The Mars Climate Orbiter had traveled 286 days and 416 million miles through space. As it approached Mars for orbital insertion, ground controllers sent the commands to slow down and enter orbit. Nine minutes of radio silence followed—normal for a maneuver behind the planet.

The signal never returned.

The spacecraft had approached Mars 100 kilometers too low, skipping off the atmosphere and burning up. The root cause? **Lockheed Martin's navigation software produced thrust data in pound-force seconds. NASA's system expected newton-seconds.** One team's environment assumed imperial units; another assumed metric.

**Chris Mattmann**, now Chief Technology and Innovation Officer at NASA JPL and a long-time open source contributor, has spent years advocating for better software engineering practices in aerospace. He later wrote: *"The Mars Climate Orbiter wasn't lost to physics. It was lost to environment assumptions. The code worked perfectly—in the environment it was written for."*

This is the "it works on my machine" problem at its most extreme. And while your ML model probably won't crash into Mars, the same class of problem—code that works in one environment but fails in another—costs organizations billions of dollars annually.

Containers are the solution. They package your code, dependencies, and environment assumptions into a single, portable unit that behaves identically everywhere it runs.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Understand why containers are essential for ML reproducibility (and why virtual environments aren't enough)
- Master Docker fundamentals: images, containers, layers, and registries
- Build optimized ML Docker images using multi-stage builds
- Handle large ML artifacts (models, data) without bloating your images
- Configure GPU containers with NVIDIA Container Toolkit
- Create Docker Compose stacks for ML development environments
- Apply production best practices that security teams will actually approve

---

## Why This Module Matters

### The Reproducibility Crisis Nobody Talks About

Here's a dirty secret of machine learning: **most ML research cannot be reproduced**. And it's not because researchers are sloppy—it's because ML has an environment problem that's worse than traditional software.

**Did You Know?** In 2019, **Odd Erik Gundersen** and **Sigbjørn Kjensmo** at the Norwegian University of Science and Technology surveyed 400 machine learning papers and found that only 6% provided all the information needed to reproduce the results. The missing pieces weren't the algorithms—they were the environments. Which version of PyTorch? Which CUDA? Which cuDNN? Which random number generator?

```
THE "IT WORKS ON MY MACHINE" PROBLEM IN ML
==========================================

Your Laptop                     Production Server
-----------                     -----------------
Python 3.10.4                   Python 3.10.1      ← Minor version = different bytecode
PyTorch 2.0.1                   PyTorch 2.0.0      ← Different numerical precision
CUDA 11.8                       CUDA 11.7          ← Different kernel implementations
cuDNN 8.6.0                     cuDNN 8.5.0        ← Different convolution algorithms
Ubuntu 22.04                    Ubuntu 20.04       ← Different glibc, different syscalls
libc 2.35                       libc 2.31          ← Affects everything that uses C
numpy 1.24.0                    numpy 1.23.5       ← Different BLAS binding

Your model accuracy:            Production accuracy:
         94.2%                              91.7%

You: "But I didn't change anything!"
Reality: You changed EVERYTHING by moving machines.
```

### Why Virtual Environments Aren't Enough

"But wait," you might say, "I use virtualenv/conda/poetry. Isn't that enough?"

No. Here's why:

**Virtual environments only isolate Python packages.** They don't isolate:
- System libraries (libc, libstdc++, OpenSSL)
- CUDA toolkit and cuDNN
- System Python patches
- Operating system differences
- File system structure
- Environment variables set by the OS

**Did You Know?** **Donald Stufft**, a maintainer of pip and PyPI, once traced a "pip install tensorflow" failure across 47 different system configurations. The same pip command produced 12 different outcomes depending on the OS, Python build, and installed system libraries. His conclusion: *"pip install reproduces packages, not environments."*

### What Containers Actually Solve

Containers give you something virtual environments can't: **a complete, isolated environment that includes everything from the kernel up** (except the kernel itself, which is shared).

```
CONTAINER ISOLATION MODEL
=========================

┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR CONTAINER                               │
├─────────────────────────────────────────────────────────────────────┤
│  Your Application Code                                               │
│  ├── train.py                                                       │
│  ├── model.py                                                       │
│  └── requirements.txt                                               │
├─────────────────────────────────────────────────────────────────────┤
│  Python Packages (pip/conda)                                         │
│  ├── torch==2.0.1                                                   │
│  ├── transformers==4.30.0                                           │
│  └── (exact versions, always)                                       │
├─────────────────────────────────────────────────────────────────────┤
│  CUDA Toolkit & cuDNN                                               │
│  └── cuda-11.8, cudnn-8.6.0                                        │
├─────────────────────────────────────────────────────────────────────┤
│  System Libraries                                                    │
│  ├── libc-2.35                                                      │
│  └── libstdc++-11                                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Base OS (Ubuntu 22.04, exact version)                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    (Only this is shared)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         HOST KERNEL                                  │
│  Linux 5.15.x (or whatever the host runs)                           │
└─────────────────────────────────────────────────────────────────────┘

Everything INSIDE the container is frozen, versioned, and reproducible.
Move this container to any Linux machine with Docker = identical behavior.
```

**Did You Know?** **Solomon Hykes** created Docker in 2013 while working at dotCloud, a platform-as-a-service company. The insight that made Docker revolutionary wasn't the underlying technology (Linux had LXC containers since 2008). It was the developer experience: a simple `Dockerfile` that anyone could write, and a `docker run` command that anyone could use. Hykes later said: *"Docker isn't about containers. It's about shipping code. Containers are just the best tool we have for that."*

---

##  Docker Fundamentals: The Mental Model

### Containers vs. Virtual Machines: The Apartment Analogy

Imagine you're moving to a new city. Think of virtual machines like buying a house and containers like renting an apartment. It's similar to choosing between building from scratch versus moving into existing infrastructure.

**Virtual Machines = Houses**
- Each house has its own foundation, plumbing, electrical, HVAC
- You can customize everything
- Very isolated from neighbors
- But expensive: you're paying for a lot of infrastructure you might not need
- Building a new house takes a long time

**Containers = Apartments**
- Apartments share the building's foundation, plumbing, electrical
- You customize the inside, but not the infrastructure
- Less isolated (thin walls), but good enough for most purposes
- Cheap: you only pay for your unit's space
- Moving in takes minutes, not months

```
VIRTUAL MACHINE                    CONTAINER
===============                    =========

┌─────────────────┐               ┌─────────────────┐
│   Application   │               │   Application   │
├─────────────────┤               ├─────────────────┤
│   Bins/Libs     │               │   Bins/Libs     │
├─────────────────┤               ├─────────────────┤
│   Guest OS      │               │    (nothing)    │
│   (Full Linux)  │               │                 │
├─────────────────┤               ├─────────────────┤
│   Hypervisor    │               │ Container Engine│
├─────────────────┤               ├─────────────────┤
│   Host OS       │               │   Host OS       │
├─────────────────┤               ├─────────────────┤
│   Hardware      │               │   Hardware      │
└─────────────────┘               └─────────────────┘

Disk: 10-50 GB                    Disk: 100 MB - 2 GB
Boot: 30-60 seconds               Boot: < 1 second
Isolation: Hardware-level         Isolation: Process-level
Overhead: 5-20% CPU               Overhead: < 1% CPU
```

### Images vs. Containers: The Recipe Analogy

This distinction confuses everyone at first, so let me be very clear:

- **Image** = A recipe (or blueprint). It defines what goes into the environment but isn't running.
- **Container** = A dish cooked from the recipe. It's the actual running environment.

You can cook multiple dishes from the same recipe. You can run multiple containers from the same image.

```
THE IMAGE/CONTAINER RELATIONSHIP
================================

                    ┌─────────────────┐
                    │                 │
         ┌──────────│  Docker Image   │──────────┐
         │          │  (myapp:v1.0)   │          │
         │          │                 │          │
         │          └─────────────────┘          │
         │                  │                    │
         ▼                  ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Container  │    │  Container  │    │  Container  │
│  (web-1)    │    │  (web-2)    │    │  (web-3)    │
│  Running    │    │  Running    │    │  Stopped    │
└─────────────┘    └─────────────┘    └─────────────┘

Same image → Same starting point
Different containers → Can diverge at runtime (but shouldn't)
```

### The Layer System: How Docker Saves Your Time

Here's where Docker gets clever. Think of it as similar to how version control works—you only store the differences, not complete copies. Docker images aren't monolithic blobs—they're made of layers, stacked like a cake.

**Did You Know?** **Jérôme Petazzoni**, one of Docker's early engineers, designed the layer caching system. His key insight was that most Dockerfiles follow the same pattern: base OS, then language runtime, then dependencies, then code. If the first three layers haven't changed, why rebuild them? The caching system he designed saves millions of hours of build time daily across Docker users worldwide.

```
LAYER ARCHITECTURE
==================

┌─────────────────────────────────────────┐
│  Layer 6: COPY app.py .                 │  ← Changes every commit
├─────────────────────────────────────────┤
│  Layer 5: COPY model.pkl .              │  ← Changes when model updates
├─────────────────────────────────────────┤
│  Layer 4: RUN pip install -r req.txt    │  ← Changes when deps change
├─────────────────────────────────────────┤
│  Layer 3: COPY requirements.txt .       │  ← Changes when deps change
├─────────────────────────────────────────┤
│  Layer 2: RUN apt-get install python    │  ← Changes rarely
├─────────────────────────────────────────┤
│  Layer 1: FROM ubuntu:22.04             │  ← Almost never changes
└─────────────────────────────────────────┘

CACHE RULES:
1. If a layer changes, all layers ABOVE it are rebuilt
2. Unchanged layers below are reused from cache
3. Order matters: put stable layers first, volatile layers last

PRACTICAL IMPACT:
- Full build from scratch: 10 minutes
- Code-only change (Layer 6): 5 seconds
- This is why we COPY requirements.txt BEFORE COPY app.py
```

### Essential Docker Commands

```bash
# ============================================================
# IMAGE COMMANDS (Working with blueprints)
# ============================================================

docker build -t myapp:v1 .              # Build image from Dockerfile
docker images                            # List all local images
docker pull pytorch/pytorch:2.0.0       # Download from registry
docker push myrepo/myapp:v1             # Upload to registry
docker rmi myapp:v1                     # Delete image
docker history myapp:v1                 # Show layer history
docker image prune                      # Remove unused images

# ============================================================
# CONTAINER COMMANDS (Working with running instances)
# ============================================================

docker run myapp:v1                     # Create + start container
docker run -it myapp:v1 bash            # Interactive mode with shell
docker run -d myapp:v1                  # Detached (background) mode
docker run --name mycontainer myapp:v1  # Named container
docker run -p 8000:8000 myapp:v1        # Map port 8000
docker run -v /host/path:/container/path myapp:v1  # Mount volume
docker run --gpus all myapp:v1          # Enable GPU access

docker ps                               # List running containers
docker ps -a                            # List ALL containers
docker stop mycontainer                 # Stop gracefully
docker kill mycontainer                 # Force stop
docker rm mycontainer                   # Remove stopped container
docker logs mycontainer                 # View stdout/stderr
docker logs -f mycontainer              # Follow logs (like tail -f)
docker exec -it mycontainer bash        # Shell into running container
docker inspect mycontainer              # Detailed JSON info
docker stats                            # Live resource usage

# ============================================================
# CLEANUP COMMANDS (Reclaim disk space)
# ============================================================

docker system df                        # Show disk usage
docker system prune                     # Remove all unused data
docker system prune -a                  # Remove everything unused
docker volume prune                     # Remove unused volumes
```

---

##  Writing Dockerfiles for ML

### The Naive Approach (And Why It's Problematic)

Let's start with what most people write first:

```dockerfile
#  NAIVE DOCKERFILE - Don't do this
FROM python:3.10

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "train.py"]
```

This works. Your container runs. But it has serious problems:

1. **Huge image size**: Python base is ~900MB. With ML deps, easily 5-10GB.
2. **Poor cache utilization**: Any code change rebuilds all dependencies.
3. **Security risk**: Runs as root user.
4. **No GPU support**: Won't see your NVIDIA GPUs.
5. **Development cruft**: Tests, docs, .git all included.

**Did You Know?** **Itamar Turner-Trauring**, author of "Docker Packaging for Python Developers," analyzed 1,000 public ML Dockerfiles and found the average image was 4.2GB. After applying best practices, the same functionality averaged 1.1GB—a 74% reduction. Smaller images mean faster deployments, lower storage costs, and reduced attack surface.

### The Optimized Approach: Multi-Stage Builds

Multi-stage builds are Docker's secret weapon. The idea: use one "builder" stage with all your build tools, then copy only the artifacts you need into a clean "production" stage.

```dockerfile
#  OPTIMIZED ML DOCKERFILE

# ==============================================================
# STAGE 1: Builder
# Contains build tools, downloads deps, compiles wheels
# ==============================================================
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies (only needed for compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
# Copy requirements FIRST for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================
# STAGE 2: Production
# Clean, minimal image with only runtime requirements
# ==============================================================
FROM python:3.10-slim AS production

WORKDIR /app

# Copy virtual environment from builder (not the build tools!)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash appuser

# Copy only production code (not tests, docs, .git)
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup models/ ./models/

# Switch to non-root user
USER appuser

# Environment settings for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose the service port
EXPOSE 8000

# Health check for orchestrators
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with production server
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### The Size Difference Is Dramatic

```
IMAGE SIZE COMPARISON
=====================

Naive Dockerfile:
┌─────────────────────────────────────────┐
│  python:3.10 base              (900 MB) │
│  build-essential              (300 MB) │  ← Still there!
│  pip packages                 (2.5 GB) │
│  source code + tests + .git   (100 MB) │
├─────────────────────────────────────────┤
│  TOTAL: ~3.8 GB                         │
└─────────────────────────────────────────┘

Multi-Stage Dockerfile:
┌─────────────────────────────────────────┐
│  python:3.10-slim base        (150 MB) │
│  pip packages (runtime only)  (2.0 GB) │
│  source code only              (20 MB) │
├─────────────────────────────────────────┤
│  TOTAL: ~2.2 GB                         │  ← 42% smaller!
└─────────────────────────────────────────┘

Build tools, compilers, dev dependencies = GONE from production.
```

---

##  GPU Containers with NVIDIA Container Toolkit

### The GPU Problem

GPUs are special. They're hardware devices that require kernel drivers to function. How can a container—which shares the host kernel—access a GPU that needs specific driver versions?

**Did You Know?** **Felix Abecassis** and the team at NVIDIA spent two years developing what became the NVIDIA Container Toolkit (originally nvidia-docker). The challenge wasn't just technical—it was philosophical. Containers are supposed to be isolated, but GPU access requires kernel-level permissions. Their solution was a carefully designed runtime hook that maintains isolation while allowing controlled GPU access.

### How GPU Containers Actually Work

```
GPU CONTAINER ARCHITECTURE
==========================

┌─────────────────────────────────────────────────────────────────┐
│                         CONTAINER                                │
├─────────────────────────────────────────────────────────────────┤
│  Your ML Application                                             │
│  ├── PyTorch / TensorFlow                                       │
│  └── Your model code                                            │
├─────────────────────────────────────────────────────────────────┤
│  CUDA Toolkit Libraries (inside container)                       │
│  ├── nvcc (compiler)                                            │
│  ├── cuBLAS (linear algebra)                                    │
│  ├── cuDNN (neural network primitives)                          │
│  └── NCCL (multi-GPU communication)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  NVIDIA Container │
                    │     Toolkit       │  ← The magic bridge
                    └─────────┬─────────┘
                              │
                    (Mounts these at runtime:)
                    /dev/nvidia0, /dev/nvidia1, ...
                    libnvidia-ml.so, libcuda.so
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                         HOST                                     │
├─────────────────────────────────────────────────────────────────┤
│  NVIDIA Driver (installed on host)                               │
│  └── Must be >= CUDA version in container                       │
├─────────────────────────────────────────────────────────────────┤
│  Linux Kernel                                                    │
├─────────────────────────────────────────────────────────────────┤
│  GPU Hardware (RTX 4090, A100, H100, etc.)                      │
└─────────────────────────────────────────────────────────────────┘

KEY INSIGHT:
- CUDA toolkit goes IN the container (versioned, reproducible)
- NVIDIA driver stays ON the host (shared, kernel-level)
- Container Toolkit bridges them at runtime
```

### GPU Dockerfile for ML Training

```dockerfile
# GPU-enabled ML Training Dockerfile
FROM nvidia/cuda:11.8-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    python3.10-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

WORKDIR /app

# Install PyTorch with CUDA support
# IMPORTANT: PyTorch CUDA version must match container CUDA version
RUN pip install --no-cache-dir \
    torch==2.0.1+cu118 \
    torchvision==0.15.2+cu118 \
    torchaudio==2.0.2+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118

# Install other ML dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy training code
COPY src/ ./src/

# Environment variables for NVIDIA runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Data and output directories (to be mounted as volumes)
VOLUME ["/data", "/output", "/checkpoints"]

# Training entry point
ENTRYPOINT ["python", "-m", "src.train"]
# Arguments can be passed at runtime:
# docker run --gpus all myapp:gpu --epochs 100 --lr 0.001
```

### Running GPU Containers

```bash
# Basic GPU access
docker run --gpus all myapp:gpu

# Specific GPUs (for multi-GPU machines)
docker run --gpus '"device=0"' myapp:gpu           # First GPU only
docker run --gpus '"device=0,1"' myapp:gpu         # First two GPUs
docker run --gpus '"device=GPU-3a2c..."' myapp:gpu # By UUID

# With shared memory (important for DataLoader workers!)
docker run --gpus all --shm-size=16g myapp:gpu

# With data volumes mounted
docker run --gpus all \
    -v /data/datasets:/data \
    -v /data/outputs:/output \
    -v /data/checkpoints:/checkpoints \
    myapp:gpu

# Verify GPU access inside container
docker run --gpus all nvidia/cuda:11.8-base nvidia-smi
```

### CUDA Version Compatibility: The Gotcha

This is where many people get burned. The CUDA version in your container must be compatible with the driver on the host.

```
CUDA COMPATIBILITY MATRIX
=========================

Host Driver Version    Supports Container CUDA Versions
-------------------    ---------------------------------
550.x (newest)         CUDA 12.4 and ALL earlier versions
535.x                  CUDA 12.2 and ALL earlier versions
525.x                  CUDA 12.0 and ALL earlier versions
515.x                  CUDA 11.7 and ALL earlier versions
470.x                  CUDA 11.4 and ALL earlier versions

THE RULE: Host driver must be >= container CUDA toolkit
          (Forward compatible, NOT backward compatible)

EXAMPLE:
- Host has driver 525.85 (supports up to CUDA 12.0)
- Container with CUDA 11.8   Works perfectly
- Container with CUDA 12.1   Fails: "CUDA driver version insufficient"

PRO TIP: Use `nvidia-smi` on host to check driver version
         Look at "CUDA Version" in top right = max supported
```

**Did You Know?** NVIDIA's driver versioning scheme is deliberately confusing. **Bryan Catanzaro**, VP of Applied Deep Learning Research at NVIDIA, once joked at a conference: *"Our driver version numbers are designed to keep developers humble."* The version number (like 525.85) encodes the supported CUDA versions, but you need to look up the compatibility matrix to decode it.

---

##  Handling Large ML Artifacts

### The Model Size Problem

ML models are big. Really big.

```
MODEL SIZE HALL OF FAME (2024)
==============================

BERT-base-uncased:           440 MB
GPT-2:                       1.5 GB
Stable Diffusion v1.5:       4 GB
LLaMA-7B:                    13 GB
Mistral-7B:                  14 GB
LLaMA-70B:                   140 GB
gpt-5 (rumored):             ~1.7 TB (!)

If you bake these into Docker images:
- Image size explodes
- Every model update = new image
- Registry storage costs skyrocket
- `docker pull` takes forever
- Your CI/CD pipeline cries
```

### Strategy 1: Download at Runtime

Keep your image lean. Download the model when the container starts.

```dockerfile
# Image stays small
FROM python:3.10-slim

COPY download_model.py .
COPY src/ ./src/

# Model downloaded at runtime, not build time
CMD ["sh", "-c", "python download_model.py && python -m src.serve"]
```

```python
# download_model.py
"""Download model at container startup if not cached."""

import os
from pathlib import Path
from huggingface_hub import snapshot_download

MODEL_ID = os.environ.get("MODEL_ID", "bert-base-uncased")
CACHE_DIR = Path(os.environ.get("MODEL_CACHE", "/models"))

def download_if_needed():
    model_path = CACHE_DIR / MODEL_ID.replace("/", "--")

    if model_path.exists():
        print(f" Model {MODEL_ID} already cached at {model_path}")
        return model_path

    print(f"⬇️  Downloading {MODEL_ID}...")
    path = snapshot_download(
        MODEL_ID,
        cache_dir=CACHE_DIR,
        local_dir=model_path,
    )
    print(f" Downloaded to {path}")
    return path

if __name__ == "__main__":
    download_if_needed()
```

### Strategy 2: Volume Mounts

Keep models on the host, mount into container.

```bash
# Host manages the model files
/host/models/
├── bert-base-uncased/
├── gpt2/
└── custom-model-v3/

# Mount at runtime
docker run -v /host/models:/models myapp:v1

# Or use Docker volumes for persistence across container restarts
docker volume create ml-models
docker run -v ml-models:/models myapp:v1

# Pre-populate the volume
docker run -v ml-models:/models myapp:v1 python download_model.py
```

### Strategy 3: Model Registry Integration

Let your model registry (MLflow, W&B, custom) manage versioning.

```python
# src/serve.py
"""Serve models from MLflow registry."""

import os
import mlflow

# Model coordinates from environment
MLFLOW_URI = os.environ["MLFLOW_TRACKING_URI"]
MODEL_NAME = os.environ["MODEL_NAME"]
MODEL_STAGE = os.environ.get("MODEL_STAGE", "Production")

mlflow.set_tracking_uri(MLFLOW_URI)

# Load the model (downloaded automatically)
model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
print(f"Loading model from {model_uri}")
model = mlflow.pyfunc.load_model(model_uri)

# Use the model...
```

```bash
docker run \
    -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
    -e MODEL_NAME=fraud-detector \
    -e MODEL_STAGE=Production \
    myapp:v1
```

### Strategy 4: Layered Model Images

For when you really need models in the image (air-gapped environments, etc.).

```dockerfile
# Layer 1: Base inference image (reusable)
FROM python:3.10-slim AS inference-base
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
# This layer is cached and shared

# Layer 2: Model-specific image (extends base)
FROM inference-base AS model-bert
COPY models/bert/ ./models/
ENV MODEL_PATH=/app/models/bert

# Different model, same base (shares all but last layer)
FROM inference-base AS model-gpt2
COPY models/gpt2/ ./models/
ENV MODEL_PATH=/app/models/gpt2
```

```bash
# Build different model variants
docker build --target model-bert -t myapp:bert .
docker build --target model-gpt2 -t myapp:gpt2 .

# They share base layers, so second build is fast
```

---

##  Docker Compose for ML Development

### Why Compose?

ML systems are never just one container. A realistic development environment includes:

```
TYPICAL ML DEVELOPMENT STACK
============================

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Model   │  │   API    │  │  Vector  │  │  Redis   │       │
│  │ Training │  │  Server  │  │    DB    │  │  Cache   │       │
│  │ (GPU)    │  │          │  │ (Qdrant) │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│       │             │             │             │               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ MLflow   │  │ Jupyter  │  │ Postgres │                     │
│  │ Tracking │  │   Lab    │  │ (meta)   │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│       │             │             │                             │
│       └─────────────┴─────────────┘                             │
│                     │                                           │
│              ┌──────┴──────┐                                    │
│              │   Docker    │                                    │
│              │   Network   │                                    │
│              └─────────────┘                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Managing this with individual `docker run` commands = nightmare
Docker Compose = one file, one command, everything works
```

### Complete ML Development docker-compose.yml

```yaml
# docker-compose.yml - ML Development Environment
version: '3.8'

services:
  # ============================================================
  # ML API Server (Your main application)
  # ============================================================
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src              # Hot reload during development
      - model-cache:/app/models     # Shared model cache
    environment:
      - MODEL_PATH=/app/models
      - QDRANT_HOST=qdrant
      - REDIS_HOST=redis
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - LOG_LEVEL=DEBUG
    depends_on:
      - redis
      - qdrant
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ============================================================
  # Vector Database (for embeddings/RAG)
  # ============================================================
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"     # REST API
      - "6334:6334"     # gRPC
    volumes:
      - qdrant-data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

  # ============================================================
  # Redis (caching, rate limiting)
  # ============================================================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  # ============================================================
  # MLflow (experiment tracking)
  # ============================================================
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.8.0
    ports:
      - "5000:5000"
    volumes:
      - mlflow-data:/mlflow
      - ./mlruns:/mlflow/mlruns
    environment:
      - MLFLOW_TRACKING_URI=sqlite:///mlflow/mlflow.db
    command: >
      mlflow server
      --host 0.0.0.0
      --port 5000
      --backend-store-uri sqlite:///mlflow/mlflow.db
      --default-artifact-root /mlflow/artifacts

  # ============================================================
  # Jupyter Lab (notebooks, experimentation)
  # ============================================================
  jupyter:
    build:
      context: .
      dockerfile: Dockerfile.jupyter
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/app/notebooks
      - ./src:/app/src
      - model-cache:/app/models
    environment:
      - JUPYTER_TOKEN=dev-token-change-in-prod
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # ============================================================
  # PostgreSQL (for MLflow metadata, optional)
  # ============================================================
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=mlflow
      - POSTGRES_PASSWORD=mlflow_password
      - POSTGRES_DB=mlflow

# ============================================================
# Named Volumes (persist data across restarts)
# ============================================================
volumes:
  model-cache:
    name: ml-model-cache
  qdrant-data:
    name: ml-qdrant-data
  redis-data:
    name: ml-redis-data
  mlflow-data:
    name: ml-mlflow-data
  postgres-data:
    name: ml-postgres-data

# ============================================================
# Custom Network (optional, Compose creates one automatically)
# ============================================================
networks:
  default:
    name: ml-network
```

### Docker Compose Commands

```bash
# Start everything
docker-compose up

# Start in background (detached)
docker-compose up -d

# Start specific services
docker-compose up api redis qdrant

# Rebuild images before starting
docker-compose up --build

# View logs (all services)
docker-compose logs

# View logs (specific service, follow mode)
docker-compose logs -f api

# Stop everything (keeps volumes)
docker-compose down

# Stop and remove volumes (destructive!)
docker-compose down -v

# Restart a service
docker-compose restart api

# Scale stateless services
docker-compose up --scale api=3

# Execute command in running container
docker-compose exec api python -c "print('hello')"
```

### Development vs Production Configurations

```yaml
# docker-compose.yml (base - always loaded)
version: '3.8'
services:
  api:
    build: .
    environment:
      - MODEL_PATH=/app/models
```

```yaml
# docker-compose.override.yml (development - loaded automatically)
version: '3.8'
services:
  api:
    volumes:
      - ./src:/app/src                    # Live code reload
    environment:
      - LOG_LEVEL=DEBUG
      - RELOAD=true
    ports:
      - "8000:8000"                       # Expose for local access
```

```yaml
# docker-compose.prod.yml (production - must specify explicitly)
version: '3.8'
services:
  api:
    image: myregistry/api:v1.0.0          # Use pre-built image
    environment:
      - LOG_LEVEL=WARNING
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

```bash
# Development (override loaded automatically)
docker-compose up

# Production (explicit file selection)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

##  Production Best Practices

### Security Hardening

**Did You Know?** In 2020, **Aqua Security's** container security research team found that 51% of Docker images on Docker Hub contained at least one critical vulnerability. Most were in the base image or unused dependencies that shouldn't have been included. Security isn't about paranoia—it's about not inheriting other people's problems.

```dockerfile
# SECURITY-HARDENED DOCKERFILE

# 1. Use specific versions, never 'latest'
FROM python:3.10.12-slim-bookworm

# 2. Don't run as root
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --no-create-home appuser

WORKDIR /app

# 3. Minimize installed packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 4. Set restrictive permissions
RUN chown -R appuser:appgroup /app

# 5. Install dependencies as root, then drop privileges
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup src/ ./src/

# 6. Switch to non-root user
USER appuser

# 7. Expose only necessary ports
EXPOSE 8000

# 8. Use exec form for CMD (no shell injection)
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Run container with additional security:
# docker run --read-only --cap-drop=ALL --security-opt=no-new-privileges myapp
```

### The .dockerignore File

Just like `.gitignore` for Git, `.dockerignore` tells Docker what NOT to include in the build context.

```
# .dockerignore for ML Projects

# Version control
.git
.gitignore
.gitattributes

# Environment files (often contain secrets!)
.env
.env.*
*.env

# Documentation
*.md
docs/
README*

# Test files
tests/
test_*.py
*_test.py
pytest.ini
.pytest_cache/

# Development tools
.vscode/
.idea/
*.sublime-*
.editorconfig

# Jupyter artifacts
notebooks/
*.ipynb
.ipynb_checkpoints/

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.eggs/
dist/
build/
*.egg

# Type checking / linting caches
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Large data files (should be mounted, not copied)
data/
*.csv
*.parquet
*.h5
*.hdf5

# Model files (should use volumes or download at runtime)
models/
*.pkl
*.joblib
*.pt
*.pth
*.onnx
*.safetensors

# ML experiment tracking
wandb/
mlruns/
lightning_logs/

# Docker files (avoid inception)
Dockerfile*
docker-compose*
.dockerignore

# Misc
Makefile
*.log
*.tmp
```

### Health Checks That Actually Work

```python
# src/health.py
"""Health check endpoints for container orchestration."""

from fastapi import FastAPI, Response, status
import torch
import psutil
import os

app = FastAPI()

# Global model reference (set by your main app)
model = None
model_ready = False


@app.get("/health")
async def health():
    """
    Basic health check: Is the container running?
    Used by: Docker HEALTHCHECK, basic monitoring
    Returns 200 if process is alive.
    """
    return {"status": "healthy", "pid": os.getpid()}


@app.get("/ready")
async def ready(response: Response):
    """
    Readiness check: Is the service ready to accept traffic?
    Used by: Kubernetes readinessProbe, load balancers
    Returns 200 only when model is loaded and service is ready.
    """
    checks = {
        "model_loaded": model is not None,
        "model_ready": model_ready,
        "memory_ok": psutil.virtual_memory().percent < 90,
    }

    if torch.cuda.is_available():
        checks["gpu_available"] = True
        checks["gpu_memory_ok"] = (
            torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() < 0.95
            if torch.cuda.max_memory_allocated() > 0
            else True
        )

    all_ready = all(checks.values())

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"ready": all_ready, "checks": checks}


@app.get("/live")
async def live(response: Response):
    """
    Liveness check: Should the container be restarted?
    Used by: Kubernetes livenessProbe
    Returns 200 unless something is catastrophically wrong.
    """
    try:
        # Basic sanity checks
        _ = 1 + 1  # Python is running
        _ = os.getcwd()  # Filesystem is accessible

        if torch.cuda.is_available():
            _ = torch.cuda.current_device()  # GPU is accessible

        return {"live": True}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"live": False, "error": str(e)}
```

---

##  Debugging Docker Containers

### Common Issues and Solutions

```
ISSUE: "ModuleNotFoundError: No module named 'xyz'"
-----------------------------------------------
CAUSE: Package not installed, or wrong Python environment
DEBUG: docker run -it myapp:v1 pip list
FIX:
  - Add package to requirements.txt
  - Check you're using the right Python (python vs python3)
  - Verify virtualenv is activated (PATH includes /opt/venv/bin)


ISSUE: "CUDA out of memory"
---------------------------
CAUSE: Model + batch don't fit in GPU memory
DEBUG: docker run --gpus all myapp:v1 nvidia-smi
FIX:
  - Reduce batch size
  - Use gradient checkpointing
  - Add --shm-size=16g for DataLoader workers
  - Use smaller model or quantization


ISSUE: Container exits immediately
----------------------------------
CAUSE: CMD completes or crashes during startup
DEBUG: docker run -it myapp:v1 bash  # then run CMD manually
FIX:
  - Check docker logs <container>
  - Add error handling to startup
  - Ensure CMD is a long-running process


ISSUE: "Permission denied" errors
---------------------------------
CAUSE: Running as non-root, file ownership mismatch
DEBUG: docker run -it myapp:v1 id && ls -la
FIX:
  - Use --chown in COPY instructions
  - Ensure directories exist before writing
  - Check volume mount permissions


ISSUE: Build is slow / cache not working
----------------------------------------
CAUSE: Layer order wrong, or .dockerignore missing
DEBUG: docker build --progress=plain to see layer cache status
FIX:
  - Order Dockerfile: base → system deps → Python deps → code
  - Add .dockerignore to exclude unnecessary files
  - COPY requirements.txt BEFORE COPY source code
```

### Debugging Commands

```bash
# Run interactive shell in image (to explore)
docker run -it myapp:v1 bash

# Shell into RUNNING container (to debug live)
docker exec -it <container_id> bash

# View logs (stdout/stderr)
docker logs <container_id>
docker logs -f <container_id>          # Follow (like tail -f)
docker logs --tail 100 <container_id>  # Last 100 lines

# Inspect container configuration
docker inspect <container_id>
docker inspect <container_id> | jq '.[0].Config.Env'  # Just environment

# Resource usage
docker stats <container_id>

# Copy files out of container for analysis
docker cp <container_id>:/app/logs ./local-logs

# Build with full output (see cache hits/misses)
docker build --progress=plain -t myapp:v1 .

# Build without cache (force full rebuild)
docker build --no-cache -t myapp:v1 .
```

---

##  Production War Stories: Container Lessons Learned

### The Black Friday Meltdown

**Seattle. November 2022. Major E-commerce retailer.**

Everything was ready for Black Friday. The ML team had deployed their recommendation model—carefully tested, achieving 94% accuracy in offline evaluation. The Docker image was built, pushed to the registry, and deployed to 50 Kubernetes pods.

At 6:00 AM PST, traffic started ramping up. By 7:30 AM, the recommendation service was crashing. Not slowly—catastrophically. Pods were restarting every 2-3 minutes. The fallback static recommendations kicked in, but conversion rates dropped 23%.

**The post-mortem revealed the problem**: The team had tested with `python:3.10` base image locally. In production, the CI/CD pipeline used `python:3.10-slim`. The slim image didn't include `libgomp1`, a library that numpy needs for parallel operations. Under load, numpy tried to parallelize—and crashed.

The fix? A single line:
```dockerfile
RUN apt-get install -y libgomp1
```

**Financial impact**: Estimated $4.2 million in lost revenue during the 3.5 hours of degraded performance.

**Lesson**: Test your production images, not just your development images. The difference between `python:3.10` and `python:3.10-slim` is about 600MB of system libraries—and any one of them might be critical.

> **Did You Know?** A 2023 survey by Datadog found that 67% of container incidents in production were caused by differences between development and production images. The most common culprits: missing system libraries, different Python versions, and environment variable mismatches.

---

### The GPU Memory Leak That Took Down Production

**San Francisco. March 2023. AI startup serving real-time image generation.**

The Stable Diffusion service had been running smoothly for weeks. Then, without warning, all inference requests started failing with CUDA out-of-memory errors. GPU utilization showed 100%, but no requests were being processed.

Restarting the containers fixed it—for about 4 hours. Then it happened again.

**The detective work**: The team added monitoring and discovered that GPU memory usage was increasing by 50MB per hour, even with consistent traffic. After 4-5 hours, it hit the 24GB limit of their A100 GPUs.

**The root cause**: The model warmup code ran inside the request handler:

```python
#  The bug
async def generate_image(prompt: str):
    model = load_model()  # Called every request
    image = model(prompt)
    return image

# The model wasn't being garbage collected because PyTorch
# caches intermediate tensors for potential backward passes.
# Every request added ~2MB of cached tensors.
```

**The fix**:
```python
#  Load model once at container startup
model = None

def get_model():
    global model
    if model is None:
        model = load_model()
        model.eval()  # Disable gradient computation
        torch.cuda.empty_cache()
    return model

async def generate_image(prompt: str):
    with torch.no_grad():  # No gradient caching
        image = get_model()(prompt)
    return image
```

**Financial impact**: 2 days of engineering time debugging, plus the reputational cost of a degraded service.

**Lesson**: GPU containers need special attention to memory management. Always use `torch.no_grad()` for inference, load models once at startup, and monitor GPU memory over time—not just at peak load.

---

### The Docker Image That Was Too Big to Deploy

**Austin. June 2023. MLOps team at a financial services company.**

The team built a beautiful multi-model serving system. It included BERT for text classification, a custom fraud detection model, and a time series forecasting model. All in one Docker image—for convenience.

Image size: 18.7 GB.

Deployment time from "click deploy" to "first request served": 47 minutes. Most of that was waiting for the image to pull.

During an incident response, when they needed to roll back to a previous version, that 47-minute delay meant 47 minutes of degraded service.

**The redesign**:
```dockerfile
# Base image: Shared across all models
FROM python:3.10-slim AS base
RUN pip install torch transformers fastapi

# Model-specific images: Only what's different
FROM base AS bert-service
COPY models/bert /models/bert
CMD ["python", "-m", "serve_bert"]

FROM base AS fraud-service
COPY models/fraud /models/fraud
CMD ["python", "-m", "serve_fraud"]

FROM base AS forecast-service
COPY models/forecast /models/forecast
CMD ["python", "-m", "serve_forecast"]
```

**Result**:
- Base image: 2.8 GB (shared, cached on all nodes)
- Model images: 500MB - 1.2GB each
- Deployment time: 4-8 minutes (90% improvement)
- Rollback time: Under 2 minutes (using pre-cached base)

**Lesson**: One monolithic image seems convenient until you need to deploy it. Split services, share base layers, and keep model artifacts separate from code.

---

##  Common Mistakes and How to Avoid Them

### Mistake 1: Using `latest` Tag in Production

**Wrong**:
```dockerfile
FROM python:latest
FROM nvidia/cuda:latest
```

**Problem**: `latest` isn't a version—it's "whatever was pushed most recently." Your image that worked yesterday might break tomorrow because the base changed.

**Right**:
```dockerfile
FROM python:3.10.12-slim-bookworm
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
```

Pin exact versions. Yes, it's more work to maintain. No, you don't have a choice if you want reproducibility.

---

### Mistake 2: COPY . . Before Installing Dependencies

**Wrong**:
```dockerfile
WORKDIR /app
COPY . .  # Copy everything first
RUN pip install -r requirements.txt
```

**Problem**: Any code change invalidates the `pip install` cache. You rebuild dependencies every time you change a single line of code.

**Right**:
```dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  # Code goes last
```

Dependencies change rarely; code changes constantly. Order your layers accordingly.

---

### Mistake 3: Running as Root

**Wrong**:
```dockerfile
FROM python:3.10
COPY . .
CMD ["python", "app.py"]  # Runs as root
```

**Problem**: If your application is compromised, the attacker has root access to the container. That's bad.

**Right**:
```dockerfile
FROM python:3.10

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to non-root
USER appuser

CMD ["python", "app.py"]
```

Security teams will thank you. Actually, they'll stop blocking your deployments.

---

### Mistake 4: Not Setting Shared Memory for PyTorch

**Wrong**:
```bash
docker run --gpus all myapp:gpu
# DataLoader workers crash with "bus error" or just hang
```

**Problem**: Docker containers get 64MB of shared memory by default. PyTorch's DataLoader workers communicate via shared memory. With multiple workers loading large tensors, 64MB is nothing.

**Right**:
```bash
docker run --gpus all --shm-size=16g myapp:gpu
```

Or in docker-compose:
```yaml
services:
  training:
    shm_size: '16gb'
```

Rule of thumb: Set `shm-size` to at least `num_workers * batch_size * tensor_size`.

---

### Mistake 5: Ignoring Layer Cache During CI/CD

**Wrong**:
```yaml
# CI pipeline
- docker build -t myapp:$GIT_SHA .  # Full rebuild every time
```

**Problem**: Your CI takes 15 minutes because it rebuilds from scratch every commit. Nobody's happy.

**Right**:
```yaml
# CI pipeline with cache
- docker pull myregistry/myapp:cache || true
- docker build \
    --cache-from myregistry/myapp:cache \
    -t myapp:$GIT_SHA \
    .
- docker tag myapp:$GIT_SHA myregistry/myapp:cache
- docker push myregistry/myapp:cache
```

Pull the previous build, use it as cache source, push the new cache layer. CI drops from 15 minutes to 2 minutes.

---

##  Economics of Containerization for ML

### Cost Comparison: VMs vs Containers

| Cost Component | Virtual Machines | Containers |
|----------------|-----------------|------------|
| **Infrastructure** | | |
| Instance startup time | 30-60 seconds | < 1 second |
| Resource overhead | 10-20% CPU, 500MB+ RAM | < 1% CPU, < 10MB RAM |
| Disk per deployment | 10-50 GB | 1-5 GB |
| **Operations** | | |
| Deployment time | 5-15 minutes | 30 seconds - 2 minutes |
| Rollback time | 5-15 minutes | < 30 seconds |
| Scaling time | Minutes | Seconds |
| **Engineering Time** | | |
| Environment setup | 4-8 hours per new developer | 30 minutes (`docker-compose up`) |
| "Works on my machine" debugging | 2-4 hours per incident | Eliminated (same environment) |
| Dependency conflicts | Regular occurrence | Isolated per container |

### ROI Calculation: ML Team of 8

| Metric | Before Containers | After Containers | Annual Savings |
|--------|------------------|------------------|----------------|
| Environment setup time | 40 hours/year | 4 hours/year | 36 hours |
| Environment debugging | 80 hours/year | 8 hours/year | 72 hours |
| Deployment time | 200 hours/year | 30 hours/year | 170 hours |
| Rollback incidents | 20 hours/year | 2 hours/year | 18 hours |
| **Total engineering time saved** | | | **296 hours/year** |
| **Value at $150/hour** | | | **$44,400/year** |

### Hidden Costs of NOT Containerizing

```
REAL COSTS OF "IT WORKS ON MY MACHINE"
──────────────────────────────────────

┌────────────────────────────────────────────────────────────┐
│  Issue                        │  Typical Cost              │
├────────────────────────────────────────────────────────────┤
│  Production bug from env      │  $10K-100K per incident    │
│  difference                   │  (debugging + downtime)    │
├────────────────────────────────────────────────────────────┤
│  Failed deployment during     │  $50K-500K (lost revenue   │
│  high-traffic event           │  + reputation)             │
├────────────────────────────────────────────────────────────┤
│  Security vulnerability in    │  $100K-1M (breach cost,    │
│  untracked dependency         │  compliance fines)         │
├────────────────────────────────────────────────────────────┤
│  Onboarding delay for new     │  $5K-20K per hire          │
│  ML engineer                  │  (productivity loss)       │
└────────────────────────────────────────────────────────────┘
```

> **Did You Know?** According to a 2023 Puppet State of DevOps report, organizations using containers deploy 200x more frequently than those using traditional deployments, with 24x faster recovery from failures. The median time to restore service after an incident drops from days to hours.

---

##  Interview Preparation: Docker for ML

### Q1: "Why would you use containers instead of virtual environments for ML?"

**Strong Answer**:
"Virtual environments like conda or venv solve one problem well: isolating Python packages. But they don't isolate system libraries, CUDA toolkit versions, OS differences, or environment variables that affect ML behavior.

I've seen models that achieved 94% accuracy in development drop to 91% in production—not because of bugs, but because production had a different numpy linked against different BLAS, and floating-point operations had slightly different precision.

Containers package everything from the OS up—system libraries, CUDA, Python, your code—into a single artifact that behaves identically everywhere. Think of it like shipping your entire development laptop configuration, not just your Python packages.

The tradeoff is complexity: containers require understanding Docker, registries, and orchestration. But for production ML, the reproducibility benefits far outweigh the learning curve."

### Q2: "How would you optimize a 10GB ML Docker image?"

**Strong Answer**:
"I'd attack it from multiple angles:

First, use a multi-stage build. Keep build tools like gcc and cmake in a builder stage, then copy only runtime artifacts to a slim production stage. This typically saves 500MB-2GB.

Second, use slim or alpine base images. `python:3.10-slim` is 150MB versus 900MB for full Python. Add only the system packages you actually need.

Third, separate model artifacts from code. Models shouldn't be baked into images—they should be downloaded at runtime or mounted as volumes. A 5GB model in your image means every code change creates a 5GB push.

Fourth, clean up after apt-get: `rm -rf /var/lib/apt/lists/*`. Clear pip cache with `pip install --no-cache-dir`. These small optimizations add up.

Fifth, order layers properly. Put stable layers first, volatile layers last. `COPY requirements.txt` before `COPY src/` means you only rebuild Python deps when they actually change.

In practice, I've taken 10GB images down to 2-3GB with these techniques—sometimes 80% reduction."

### Q3: "Explain how GPU containers work with NVIDIA."

**Strong Answer**:
"It's a clever architecture that splits responsibilities between the container and host.

The CUDA toolkit—libraries like cuDNN, cuBLAS, NCCL—goes inside the container. This is versioned and reproducible, just like your Python packages.

The NVIDIA driver stays on the host machine. It's kernel-level software that talks directly to the GPU hardware.

The NVIDIA Container Toolkit is the bridge. When you run `docker run --gpus all`, it intercepts the container startup and mounts the GPU devices and driver libraries into the container at runtime. The container sees `/dev/nvidia0`, the driver shared libraries, and everything it needs.

The critical constraint: the host driver must support the CUDA version in your container. Drivers are forward-compatible, so a 525.x driver supports CUDA 12.0 and all earlier versions. If your container has CUDA 12.1 but your host only has driver 515, it fails.

This architecture means you can have different containers with different CUDA versions running on the same machine, all sharing the same physical GPU and driver."

### Q4: "How do you handle ML model versioning with Docker?"

**Strong Answer**:
"I separate model versioning from image versioning because they change at different rates.

The approach I prefer: keep models out of the image entirely. The image contains inference code with a model loader that accepts a path or URL. At runtime, mount the model as a volume or download from a model registry like MLflow, HuggingFace Hub, or S3.

This gives you several benefits. First, code changes don't require re-downloading the model—the image stays small and deploys fast. Second, you can A/B test models without building new images—just point different pods at different model versions. Third, rollback is instant—switch the model mount, not the whole deployment.

The container image is versioned with git SHA or semantic version. The model is versioned separately in the model registry. They're linked through environment variables or config: 'image v1.2.3 + model v7.0' is a complete deployment specification.

For air-gapped environments where you can't download at runtime, I use layered images: a base inference image, then model-specific layers that add the model file. They share base layers, so only the model diff gets pushed."

### System Design: Containerized ML Platform

**Prompt**: "Design a containerized ML platform that handles training, serving, and experimentation for a team of 10 ML engineers."

**Strong Answer**:

"I'd build this with four main components:

**1. Container Registry & Base Images**:
```
Registry: Harbor or AWS ECR
  - Base images (rebuilt weekly):
    - ml-python:3.10-cuda11.8 (GPU training)
    - ml-python:3.10-slim (CPU inference)
    - ml-jupyter:latest (experimentation)
  - Team images (built by CI on PR merge):
    - fraud-detection-api:v1.2.3
    - recommender-training:v2.0.1
```

**2. Development Environment**:
```yaml
# docker-compose.yml - every engineer gets identical setup
services:
  jupyter:
    image: registry/ml-jupyter:latest
    volumes:
      - ./notebooks:/work
      - shared-data:/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1

  mlflow:
    image: mlflow/mlflow:latest
    ports: ["5000:5000"]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
```

**3. Training Infrastructure**:
```dockerfile
# Training image - optimized for GPU
FROM nvidia/cuda:11.8-cudnn8-devel-ubuntu22.04

# PyTorch with distributed training support
RUN pip install torch torchvision --extra-index-url ...
RUN pip install lightning wandb

# Mount points for data and outputs
VOLUME ["/data", "/checkpoints", "/logs"]

# Distributed training entrypoint
ENTRYPOINT ["python", "-m", "torch.distributed.launch"]
```

Jobs submitted via Kubernetes or Slurm, pulling images from registry, outputting to shared storage.

**4. Serving Infrastructure**:
```
Load Balancer
     │
     ├── Model A (3 replicas)
     │   └── image: registry/model-a:v1.2.0
     │       └── model: s3://models/model-a/v7
     │
     └── Model B (5 replicas)
         └── image: registry/model-b:v2.1.0
             └── model: s3://models/model-b/v12
```

**Workflow**:
1. Engineer develops in containerized Jupyter
2. Training job runs in GPU container, outputs model to S3 + MLflow
3. CI builds serving image on PR merge
4. CD deploys image, model mounted at runtime
5. Canary deployment → full rollout

**Cost estimate**:
- Registry: $200/month
- Development: $500/month (GPU instances)
- Training: Variable, ~$2K/month
- Serving: $1K-5K/month depending on traffic

Total platform cost: ~$5K/month for 10 engineers—far cheaper than the engineering time saved."

---

##  Hands-On Exercises

### Exercise 1: Basic ML Dockerfile

Create a Dockerfile for a simple scikit-learn inference service:
- Python 3.10 slim base
- Install scikit-learn and fastapi
- Copy a pre-trained model (pickle file)
- Expose port 8000
- Run with uvicorn

### Exercise 2: Multi-Stage Optimization

Convert your Dockerfile to multi-stage:
- Builder stage: install build tools, compile dependencies
- Production stage: slim base, only runtime requirements
- Compare image sizes before and after

### Exercise 3: GPU Training Container

Create a GPU-enabled training container:
- NVIDIA CUDA base image
- PyTorch with CUDA support
- Volume mounts for data, checkpoints, and outputs
- Run with `--gpus all --shm-size=16g`

### Exercise 4: Complete Compose Stack

Create a docker-compose.yml with:
- ML API service (your model)
- Qdrant for vector search
- Redis for caching
- MLflow for experiment tracking
- Jupyter for development

---

##  Further Reading

### Official Documentation
- [Docker Documentation](https://docs.docker.com/) - The authoritative source
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/) - GPU container setup
- [Docker Compose Specification](https://docs.docker.com/compose/compose-file/) - Complete reference

### Best Practices
- [Docker Best Practices for Python](https://testdriven.io/blog/docker-best-practices/) - Comprehensive guide
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/) - Official recommendations
- [NVIDIA NGC Catalog](https://catalog.ngc.nvidia.com/containers) - Pre-built ML containers

### Research
- "Reproducibility in Machine Learning for Health" (McDermott et al., 2019) - Why ML reproducibility matters
- "The State of Machine Learning Infrastructure" (Algorithmia, 2020) - Industry survey on ML deployment

---

##  Key Takeaways

1. **Virtual environments aren't enough** - They isolate Python packages but not system libraries, CUDA, or OS differences. Containers isolate everything except the kernel.

2. **Images are blueprints, containers are instances** - One image can spawn many containers. Images are immutable; containers can diverge at runtime.

3. **Layer ordering matters for cache performance** - Put stable layers (OS, system deps) first, volatile layers (your code) last. A well-ordered Dockerfile builds in seconds for code changes.

4. **Multi-stage builds dramatically reduce image size** - Keep build tools in the builder stage, copy only runtime artifacts to production. Expect 40-70% size reduction.

5. **GPU containers need careful version matching** - CUDA toolkit in container, driver on host. Host driver version must be >= container CUDA version.

6. **Don't bake models into images** - Use volume mounts, download at runtime, or pull from model registries. Keeps images lean and deployments fast.

7. **Security defaults are important** - Run as non-root, use specific versions, minimize packages, scan for vulnerabilities. Don't inherit other people's security problems.

---

## ⏭️ Next Steps

You now understand Docker for ML! This foundation enables:
- **CI/CD pipelines** (Module 45) - Automate building and testing containers
- **Kubernetes deployments** (Modules 46-47) - Orchestrate containers at scale
- **MLOps experiment tracking** (Module 48) - Reproducible experiments in containers

**Up Next**: Module 45 - CI/CD for AI/ML Development

---

*Module 44 Complete! You now have the containerization skills to ship ML code that runs the same everywhere.*

*Remember the Mars Climate Orbiter: environment assumptions killed a $165 million spacecraft. Containers make environment assumptions explicit, versioned, and reproducible. That's not overhead—that's engineering.*

*"It works on my machine" → "It works in this container, which runs everywhere."*
