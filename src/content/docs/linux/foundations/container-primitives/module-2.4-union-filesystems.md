---
title: "Module 2.4: Union Filesystems"
slug: linux/foundations/container-primitives/module-2.4-union-filesystems
sidebar:
  order: 5
---
> **Linux Foundations** | Complexity: `[MEDIUM]` | Time: 25-30 min

## Prerequisites

Before starting this module:
- **Required**: [Module 1.3: Filesystem Hierarchy](../system-essentials/module-1.3-filesystem-hierarchy/)
- **Required**: [Module 2.1: Linux Namespaces](../module-2.1-namespaces/) (mount namespace concept)
- **Helpful**: Understanding of container images

---

## Why This Module Matters

Every time you pull a container image, run `docker build`, or start a Kubernetes pod, union filesystems are at work. They make containers efficient by:

- **Sharing common layers** — 100 containers from the same image don't need 100 copies
- **Copy-on-write** — Only changed files use additional storage
- **Fast startup** — No need to copy entire image for each container

Understanding union filesystems helps you:

- **Optimize images** — Know why layer order matters
- **Debug storage issues** — Why is my container using so much space?
- **Understand image caching** — Why did Docker rebuild this layer?
- **Troubleshoot container filesystem problems** — Why can't I see my file?

---

## Did You Know?

- **OverlayFS merged into the Linux kernel in 2014** (kernel 3.18). Before that, containers used AUFS, which never made it into the mainline kernel—Docker had to patch kernels to use it.

- **A single layer can be shared by thousands of containers** — If you run 1000 containers from the same base image, you have ONE copy of the base layer, not 1000. This is why container density is so high.

- **Each Dockerfile instruction creates a layer** — But only instructions that modify the filesystem (RUN, COPY, ADD) create meaningful layers. ENV and LABEL create metadata-only layers.

- **The container's writable layer is ephemeral** — When the container is removed, the layer is gone. This is why volumes exist—to persist data beyond container lifecycle.

---

## What Is a Union Filesystem?

A **union filesystem** merges multiple directories (layers) into a single unified view.

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNION FILESYSTEM VIEW                         │
│                                                                  │
│                     What the container sees:                     │
│                     ┌─────────────────────┐                     │
│                     │ /                   │                     │
│                     │ ├── bin/            │                     │
│                     │ ├── etc/nginx/      │                     │
│                     │ ├── var/log/        │                     │
│                     │ └── app/myapp       │                     │
│                     └─────────────────────┘                     │
│                              ▲                                   │
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              │    Union/Merge Operation      │                  │
│              └───────────────────────────────┘                  │
│                      ▲       ▲       ▲                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Container    │  │ Image Layer  │  │ Base Layer   │          │
│  │ Layer (RW)   │  │    (RO)      │  │    (RO)      │          │
│  │              │  │              │  │              │          │
│  │ /var/log/    │  │ /etc/nginx/  │  │ /bin/        │          │
│  │   app.log    │  │   nginx.conf │  │   bash       │          │
│  │ /app/myapp   │  │              │  │   ls         │          │
│  │   (modified) │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│      upperdir          lowerdir          lowerdir               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| Layer | A directory containing filesystem changes |
| Lower layers | Read-only base layers (image) |
| Upper layer | Read-write container layer |
| Merged view | What the container sees |
| Copy-on-write | Copies file to upper layer when modified |
| Whiteout | Marks deleted files (without removing from lower) |

---

## OverlayFS

**OverlayFS** is the default storage driver for Docker and containerd.

### How OverlayFS Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        OVERLAYFS                                 │
│                                                                  │
│  Mount command:                                                  │
│  mount -t overlay overlay -o \                                  │
│    lowerdir=/lower1:/lower2, \                                  │
│    upperdir=/upper, \                                           │
│    workdir=/work \                                              │
│    /merged                                                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                    /merged (unified view)               │     │
│  └────────────────────────────────────────────────────────┘     │
│                              ▲                                   │
│      ┌───────────────────────┼───────────────────────┐          │
│      │                       │                       │          │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐              │
│  │/upper  │  │/work   │  │/lower1 │  │/lower2 │              │
│  │(RW)    │  │(scratch│  │(RO)    │  │(RO)    │              │
│  │        │  │ space) │  │        │  │        │              │
│  └────────┘  └────────┘  └────────┘  └────────┘              │
│                                                                  │
│  Changes go    Temporary      Image layers (read-only,          │
│  here          operations     stacked with lower1 on top)       │
└─────────────────────────────────────────────────────────────────┘
```

### OverlayFS Operations

| Operation | What Happens |
|-----------|--------------|
| **Read** | Return file from highest layer that has it |
| **Write (new file)** | Create in upper layer |
| **Write (existing)** | Copy from lower to upper, then modify (COW) |
| **Delete** | Create "whiteout" file in upper layer |
| **Rename dir** | Complex; may copy entire directory |

### Try This: Create an Overlay Mount

```bash
# Create directories
mkdir -p /tmp/overlay/{lower,upper,work,merged}

# Add some files to lower
echo "base file" > /tmp/overlay/lower/base.txt
echo "will be modified" > /tmp/overlay/lower/modify.txt
echo "will be deleted" > /tmp/overlay/lower/delete.txt

# Mount overlay
sudo mount -t overlay overlay \
    -o lowerdir=/tmp/overlay/lower,upperdir=/tmp/overlay/upper,workdir=/tmp/overlay/work \
    /tmp/overlay/merged

# View merged filesystem
ls /tmp/overlay/merged/
# Shows: base.txt  delete.txt  modify.txt

# Read from lower layer
cat /tmp/overlay/merged/base.txt
# Output: base file

# Create new file (goes to upper)
echo "new file" > /tmp/overlay/merged/new.txt
ls /tmp/overlay/upper/
# Shows: new.txt

# Modify existing (copy-on-write)
echo "modified content" > /tmp/overlay/merged/modify.txt
ls /tmp/overlay/upper/
# Shows: modify.txt  new.txt

# Delete file (creates whiteout)
rm /tmp/overlay/merged/delete.txt
ls -la /tmp/overlay/upper/
# Shows: delete.txt (whiteout character device)

# Original still exists in lower
ls /tmp/overlay/lower/
# Shows: base.txt  delete.txt  modify.txt

# Cleanup
sudo umount /tmp/overlay/merged
rm -rf /tmp/overlay
```

---

## Container Image Layers

### Anatomy of an Image

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER IMAGE STRUCTURE                        │
│                                                                  │
│  docker pull nginx:alpine                                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Layer 5: COPY nginx.conf /etc/nginx/ (2KB)              │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ Layer 4: RUN apk add nginx (10MB)                       │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ Layer 3: RUN apk update (5MB)                           │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ Layer 2: ENV PATH=/usr/local/sbin:... (metadata only)   │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ Layer 1: Alpine base image (5MB)                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Total: ~22MB (but shared with other alpine-based images)       │
└─────────────────────────────────────────────────────────────────┘
```

### Viewing Image Layers

```bash
# See layers
docker history nginx:alpine

# Detailed layer info
docker inspect nginx:alpine | jq '.[0].RootFS.Layers'

# Layer storage location
ls /var/lib/docker/overlay2/
```

### Layer Sharing

```
Container 1 (nginx:alpine)    Container 2 (nginx:alpine)
┌─────────────────────────┐   ┌─────────────────────────┐
│ Container Layer (RW)    │   │ Container Layer (RW)    │
│ /var/log/nginx/access.. │   │ /var/cache/nginx/...   │
└───────────┬─────────────┘   └───────────┬─────────────┘
            │                             │
            └──────────┬──────────────────┘
                       │
                       ▼  SHARED (one copy!)
            ┌─────────────────────────┐
            │ nginx:alpine layers     │
            │ (read-only)             │
            └─────────────────────────┘
```

100 containers from nginx:alpine = 1 copy of image + 100 thin container layers

---

## Copy-on-Write (COW)

### How COW Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     COPY-ON-WRITE                                │
│                                                                  │
│  BEFORE MODIFICATION:                                           │
│  ┌───────────────┐                                              │
│  │ Upper (empty) │                                              │
│  ├───────────────┤                                              │
│  │ Lower         │                                              │
│  │ nginx.conf    │ ← Container reads from here                  │
│  └───────────────┘                                              │
│                                                                  │
│  DURING MODIFICATION:                                           │
│  1. Copy nginx.conf from lower to upper                         │
│  2. Modify the copy in upper                                    │
│                                                                  │
│  AFTER MODIFICATION:                                            │
│  ┌───────────────┐                                              │
│  │ Upper         │                                              │
│  │ nginx.conf    │ ← Container now reads modified version      │
│  ├───────────────┤                                              │
│  │ Lower         │                                              │
│  │ nginx.conf    │ ← Still exists, unchanged                   │
│  └───────────────┘                                              │
│                                                                  │
│  Lower layer is NEVER modified (other containers use it!)       │
└─────────────────────────────────────────────────────────────────┘
```

### COW Performance Implications

| Operation | Performance |
|-----------|-------------|
| Reading small file | Fast (direct read) |
| Reading large file | Fast (direct read) |
| Writing new small file | Fast (write to upper) |
| Modifying small file | Medium (copy + write) |
| Modifying large file | SLOW (full copy + write) |
| Modifying file frequently | Can be slow (consider volume) |

**Best Practice**: For frequently modified files, use volumes instead of container layer.

---

## Dockerfile Layer Optimization

### Bad: Creates Many Large Layers

```dockerfile
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN rm -rf /var/lib/apt/lists/*   # Too late! Previous layers have it
```

Each RUN creates a layer. The `rm` in the last layer doesn't reduce image size—the files still exist in earlier layers!

### Good: Single Optimized Layer

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*   # Same layer, so files are never stored
```

### Layer Ordering Matters

```dockerfile
# BAD: Copy code before installing dependencies
# Every code change invalidates pip install layer
FROM python:3.11
COPY . /app                    # Changes frequently
RUN pip install -r /app/requirements.txt  # Reinstalled every time!

# GOOD: Install dependencies first
FROM python:3.11
COPY requirements.txt /app/    # Changes rarely
RUN pip install -r /app/requirements.txt  # Cached!
COPY . /app                    # Only this layer rebuilds
```

### .dockerignore

```
# .dockerignore
.git
node_modules
__pycache__
*.pyc
.env
*.log
```

---

## Storage Drivers

### Available Drivers

| Driver | Used By | Backing Filesystem |
|--------|---------|-------------------|
| overlay2 | Default | xfs, ext4 |
| btrfs | Some systems | btrfs |
| zfs | Some systems | zfs |
| devicemapper | Legacy RHEL | Any |
| vfs | Testing only | Any |

### Check Your Driver

```bash
# Docker
docker info | grep "Storage Driver"

# containerd
cat /etc/containerd/config.toml | grep snapshotter

# Podman
podman info | grep graphDriverName
```

### Storage Location

```bash
# Docker layer storage
ls /var/lib/docker/overlay2/

# Each directory is a layer
# l/ contains shortened symlinks for path length
# diff/ contains actual layer contents
# merged/ is the union view (for running containers)
# work/ is overlay work directory
```

---

## Troubleshooting Storage

### Container Using Too Much Space

```bash
# Check container sizes
docker ps -s

# SIZE: Virtual = image + writable layer
# SIZE: Actual writable layer

# Find large files in container
docker exec container-id du -sh /* 2>/dev/null | sort -h | tail -10

# Check what's in writable layer
docker diff container-id
# A = Added
# C = Changed
# D = Deleted
```

### Image Layer Analysis

```bash
# See layer sizes
docker history --no-trunc nginx:alpine

# Use dive tool for detailed analysis
# https://github.com/wagoodman/dive
dive nginx:alpine
```

### Disk Full Issues

```bash
# Docker disk usage
docker system df

# Detailed breakdown
docker system df -v

# Clean up
docker system prune        # Remove unused data
docker system prune -a     # Also remove unused images
docker builder prune       # Clear build cache
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Multiple RUN commands | Bloated image | Combine into single RUN |
| rm in separate layer | Files still in earlier layer | Delete in same layer |
| Wrong COPY order | Cache invalidation | Copy dependencies first |
| Writing to container layer | Slow, data lost on restart | Use volumes |
| Not using .dockerignore | Large context, slow builds | Exclude unnecessary files |
| Forgetting layer caching | Slow rebuilds | Order Dockerfile by change frequency |

---

## Quiz

### Question 1
Why don't 100 containers from the same image use 100x the storage?

<details>
<summary>Show Answer</summary>

**Layer sharing.** Union filesystems share read-only layers between containers. Only ONE copy of the image layers exists, regardless of how many containers use it.

Each container only needs its own thin writable layer for changes. Most containers write very little, so the actual storage overhead is minimal.

</details>

### Question 2
What is copy-on-write, and when does it happen?

<details>
<summary>Show Answer</summary>

**Copy-on-write (COW)** means files are only copied when modified:

1. File exists in lower (read-only) layer
2. Container tries to modify the file
3. File is copied to upper (writable) layer
4. Modification applies to the copy

This saves storage (unmodified files aren't duplicated) but can be slow for large files that are frequently modified.

</details>

### Question 3
Why doesn't this Dockerfile optimization work?

```dockerfile
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
```

<details>
<summary>Show Answer</summary>

Each `RUN` creates a separate layer. The `rm` command runs in layer 3, but the apt cache from layers 1 and 2 is already committed and stored.

Layers are immutable—you can't remove data from earlier layers, only hide it with whiteouts (which doesn't reclaim space in the image).

**Fix**: Combine into one layer:
```dockerfile
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
```

</details>

### Question 4
What happens to the container writable layer when the container is deleted?

<details>
<summary>Show Answer</summary>

**It's deleted too.** The writable layer only exists for the lifetime of the container. This is why:

- Container data is ephemeral by default
- Volumes are needed for persistent data
- Logs and temp files should go to volumes if they need to persist

</details>

### Question 5
Why should frequently changing files be in volumes, not the container layer?

<details>
<summary>Show Answer</summary>

Two reasons:

1. **Performance**: Every write to an existing file triggers copy-on-write. For frequently modified files (logs, databases), this creates overhead.

2. **Persistence**: Container layer is deleted with the container. Volumes persist independently.

Volumes bypass the union filesystem entirely, writing directly to the host filesystem—no COW overhead.

</details>

---

## Hands-On Exercise

### Exploring Union Filesystems

**Objective**: Understand layers, COW, and container storage.

**Environment**: Linux with Docker installed

#### Part 1: Create a Manual Overlay

```bash
# 1. Create directories
mkdir -p /tmp/overlay-test/{lower,upper,work,merged}

# 2. Add content to lower
echo "original file" > /tmp/overlay-test/lower/readme.txt
mkdir /tmp/overlay-test/lower/subdir
echo "nested file" > /tmp/overlay-test/lower/subdir/nested.txt

# 3. Mount overlay
sudo mount -t overlay overlay \
    -o lowerdir=/tmp/overlay-test/lower,upperdir=/tmp/overlay-test/upper,workdir=/tmp/overlay-test/work \
    /tmp/overlay-test/merged

# 4. Explore
ls -la /tmp/overlay-test/merged/

# 5. Create new file
echo "new content" > /tmp/overlay-test/merged/newfile.txt

# 6. Check upper layer
ls /tmp/overlay-test/upper/
# newfile.txt is here!

# 7. Modify existing file
echo "modified" > /tmp/overlay-test/merged/readme.txt
ls /tmp/overlay-test/upper/
# readme.txt copied here (COW)

# 8. Delete a file
rm /tmp/overlay-test/merged/subdir/nested.txt
ls -la /tmp/overlay-test/upper/subdir/
# Whiteout file created

# 9. Cleanup
sudo umount /tmp/overlay-test/merged
rm -rf /tmp/overlay-test
```

#### Part 2: Examine Docker Layers

```bash
# 1. Pull an image
docker pull alpine:3.18

# 2. View layers
docker history alpine:3.18

# 3. Inspect layer IDs
docker inspect alpine:3.18 | jq '.[0].RootFS.Layers'

# 4. Find storage location
docker info | grep "Docker Root Dir"

# 5. List overlay directories
sudo ls /var/lib/docker/overlay2/ | head -10
```

#### Part 3: Container Layer in Action

```bash
# 1. Start container
docker run -d --name test-overlay alpine sleep 3600

# 2. Check initial size
docker ps -s --filter name=test-overlay

# 3. Write to container
docker exec test-overlay sh -c 'dd if=/dev/zero of=/bigfile bs=1M count=50'

# 4. Check size again
docker ps -s --filter name=test-overlay
# SIZE should show ~50MB now

# 5. See what changed
docker diff test-overlay
# Shows: A /bigfile

# 6. Find container layer
CONTAINER_ID=$(docker inspect test-overlay --format '{{.Id}}')
sudo ls /var/lib/docker/overlay2/ | grep -i ${CONTAINER_ID:0:12} || \
    echo "Layer is at: $(docker inspect test-overlay --format '{{.GraphDriver.Data.UpperDir}}')"

# 7. Cleanup
docker rm -f test-overlay
```

#### Part 4: Dockerfile Layer Optimization

```bash
# 1. Create bad Dockerfile
mkdir /tmp/dockerfile-test && cd /tmp/dockerfile-test
cat > Dockerfile.bad << 'EOF'
FROM alpine:3.18
RUN apk update
RUN apk add curl
RUN rm -rf /var/cache/apk/*
EOF

# 2. Build and check size
docker build -f Dockerfile.bad -t bad-layers .
docker images bad-layers

# 3. Create good Dockerfile
cat > Dockerfile.good << 'EOF'
FROM alpine:3.18
RUN apk update && apk add curl && rm -rf /var/cache/apk/*
EOF

# 4. Build and compare
docker build -f Dockerfile.good -t good-layers .
docker images | grep layers
# good-layers should be smaller

# 5. Compare layers
docker history bad-layers
docker history good-layers

# 6. Cleanup
docker rmi bad-layers good-layers
rm -rf /tmp/dockerfile-test
```

### Success Criteria

- [ ] Created manual overlay mount and understood COW
- [ ] Examined Docker image layers
- [ ] Observed container layer growth
- [ ] Compared optimized vs unoptimized Dockerfiles

---

## Key Takeaways

1. **Union filesystems merge layers** — Multiple read-only layers plus one read-write layer

2. **Layer sharing is the magic** — Thousands of containers can share the same base layers

3. **Copy-on-write for efficiency** — Files only copied when modified

4. **Dockerfile order matters** — Put frequently changing content last for cache efficiency

5. **Container layer is ephemeral** — Use volumes for persistent data

---

## What's Next?

Congratulations! You've completed **Container Primitives**. You now understand that containers are:
- Namespaces (isolation)
- Cgroups (limits)
- Capabilities/LSMs (security)
- Union filesystems (efficient storage)

Next, move to **Section 3: Networking** to learn how Linux networking underpins container and Kubernetes networking.

---

## Further Reading

- [OverlayFS Documentation](https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html)
- [Docker Storage Drivers](https://docs.docker.com/storage/storagedriver/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Dive - Image Layer Explorer](https://github.com/wagoodman/dive)
