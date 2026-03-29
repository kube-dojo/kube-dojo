---
title: "Module 1.2: Docker Fundamentals"
slug: prerequisites/cloud-native-101/module-1.2-docker-fundamentals
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Hands-on practice required
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 1 (What Are Containers?)

---

## Why This Module Matters

Docker is the most common tool for building container images. Even though Kubernetes doesn't use Docker as its runtime anymore, Docker remains the standard for:
- Building container images
- Local development
- Testing and debugging

You need "just enough" Docker to understand Kubernetes—not Docker mastery.

---

## Installing Docker

### macOS
```bash
# Install Docker Desktop
# Download from https://docker.com/products/docker-desktop
# Or use Homebrew:
brew install --cask docker
```

### Linux (Ubuntu/Debian)
```bash
# Official installation
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

### Verify Installation
```bash
docker --version
# Docker version 24.x.x, build xxxxx

docker run hello-world
# Should show "Hello from Docker!" message
```

---

## Your First Container

```bash
# Run nginx (a web server)
docker run -d -p 8080:80 nginx

# What happened:
# - Pulled nginx image from Docker Hub
# - Created a container from the image
# - Started the container in detached mode (-d)
# - Mapped port 8080 (host) to port 80 (container)
```

```bash
# Test it
curl http://localhost:8080
# Returns nginx welcome page HTML

# View running containers
docker ps
# CONTAINER ID  IMAGE  COMMAND                 STATUS         PORTS                  NAMES
# a1b2c3d4e5f6  nginx  "/docker-entrypoint.…"  Up 10 seconds  0.0.0.0:8080->80/tcp   tender_tesla

# Stop the container
docker stop a1b2c3d4e5f6

# Remove the container
docker rm a1b2c3d4e5f6
```

---

## Essential Docker Commands

### Container Lifecycle

```bash
# Run a container
docker run [OPTIONS] IMAGE [COMMAND]

# Common options:
docker run -d nginx                    # Detached (background)
docker run -it ubuntu bash             # Interactive terminal
docker run -p 8080:80 nginx           # Port mapping
docker run -v /host/path:/container/path nginx  # Volume mount
docker run --name myapp nginx         # Named container
docker run -e MY_VAR=value nginx      # Environment variable
docker run --rm nginx                 # Remove when stopped

# Container management
docker ps                              # List running containers
docker ps -a                           # List all containers
docker stop CONTAINER                  # Stop gracefully
docker kill CONTAINER                  # Force stop
docker rm CONTAINER                    # Remove stopped container
docker rm -f CONTAINER                 # Force remove (stop + rm)
```

### Inspecting Containers

```bash
# View logs
docker logs CONTAINER
docker logs -f CONTAINER               # Follow (tail)
docker logs --tail 100 CONTAINER       # Last 100 lines

# Execute command in running container
docker exec -it CONTAINER bash         # Interactive shell
docker exec CONTAINER ls /app          # Run command

# Inspect container details
docker inspect CONTAINER               # Full JSON details
docker stats                           # Resource usage
docker top CONTAINER                   # Running processes
```

### Image Management

```bash
# Pull images
docker pull nginx
docker pull nginx:1.25
docker pull gcr.io/project/image:tag

# List images
docker images

# Remove images
docker rmi nginx
docker image prune                     # Remove unused images

# Build images (we'll cover this next)
docker build -t myapp:v1 .
```

---

## Building Container Images

### The Dockerfile

A Dockerfile is a text file with instructions to build an image:

```dockerfile
# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (documentation)
EXPOSE 8000

# Default command
CMD ["python", "app.py"]
```

### Build and Run

```bash
# Build image
docker build -t myapp:v1 .

# Run container from image
docker run -d -p 8000:8000 myapp:v1
```

### Dockerfile Instructions

| Instruction | Purpose |
|-------------|---------|
| `FROM` | Base image to build upon |
| `WORKDIR` | Set working directory |
| `COPY` | Copy files from host to image |
| `ADD` | Like COPY but can extract archives and fetch URLs |
| `RUN` | Execute command during build |
| `ENV` | Set environment variable |
| `EXPOSE` | Document which port the app uses |
| `CMD` | Default command when container starts |
| `ENTRYPOINT` | Command that always runs (CMD becomes arguments) |

---

## Practical Example: Python Web App

Create a simple Python application:

**app.py**
```python
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    name = os.getenv('NAME', 'World')
    return f'Hello, {name}!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

**requirements.txt**
```
flask==3.0.0
```

**Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

EXPOSE 8000

CMD ["python", "app.py"]
```

**Build and Run**
```bash
# Build
docker build -t hello-flask:v1 .

# Run
docker run -d -p 8000:8000 -e NAME=Docker hello-flask:v1

# Test
curl http://localhost:8000
# Hello, Docker!

# Cleanup
docker rm -f $(docker ps -q --filter ancestor=hello-flask:v1)
```

---

## Layer Caching

Docker caches layers for faster builds. Order matters:

```dockerfile
# BAD: Code changes invalidate dependency cache
FROM python:3.11-slim
WORKDIR /app
COPY . .                              # Any change busts cache
RUN pip install -r requirements.txt   # Reinstalls every time!
CMD ["python", "app.py"]

# GOOD: Dependencies cached separately
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .               # Only changes when deps change
RUN pip install -r requirements.txt   # Cached unless deps change
COPY . .                              # App changes don't bust pip cache
CMD ["python", "app.py"]
```

---

## Docker Compose (Local Multi-Container)

For local development with multiple services:

**docker-compose.yml**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_PASSWORD=secret
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

**Note**: Docker Compose is for local development. Kubernetes replaces it for production.

---

## Visualization: Docker Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER WORKFLOW                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. WRITE                                                   │
│     ┌─────────────┐                                        │
│     │ Dockerfile  │                                        │
│     └──────┬──────┘                                        │
│            │                                                │
│            ▼                                                │
│  2. BUILD                                                   │
│     ┌─────────────┐                                        │
│     │docker build │──────► Image (myapp:v1)                │
│     └──────┬──────┘                                        │
│            │                                                │
│            ▼                                                │
│  3. PUSH (optional)                                        │
│     ┌─────────────┐                                        │
│     │docker push  │──────► Registry (Docker Hub, ECR...)   │
│     └──────┬──────┘                                        │
│            │                                                │
│            ▼                                                │
│  4. RUN                                                     │
│     ┌─────────────┐                                        │
│     │docker run   │──────► Container (running instance)    │
│     └─────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### Image Size

```dockerfile
# BAD: Full OS, huge image
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y python3 python3-pip
COPY . .
RUN pip3 install -r requirements.txt

# GOOD: Slim base, smaller image
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# BETTER: Alpine (tiny base)
FROM python:3.11-alpine
# Note: Alpine uses apk, not apt, and musl instead of glibc
```

### Security

```dockerfile
# BAD: Running as root
FROM python:3.11-slim
COPY . .
CMD ["python", "app.py"]  # Runs as root!

# GOOD: Non-root user
FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "app.py"]
```

### One Process Per Container

```
# BAD: Multiple services in one container
Container: nginx + python app + redis

# GOOD: Separate containers
Container 1: nginx
Container 2: python app
Container 3: redis
(Use Docker Compose or Kubernetes to orchestrate)
```

---

## Did You Know?

- **Docker images are content-addressable.** The SHA256 hash of an image is its true identifier. Tags are just human-readable aliases.

- **Multi-stage builds reduce image size dramatically.** Build in one stage, copy only artifacts to final stage.

- **The `latest` tag is not special.** Docker doesn't automatically update it. It's just a convention that means "whatever was last pushed."

- **Docker Desktop is not Docker.** Docker (the tool) is free. Docker Desktop (the GUI/VM for Mac/Windows) has licensing requirements for businesses.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using `latest` tag | Unpredictable versions | Use specific tags (`:1.25.3`) |
| Running as root | Security risk | Add `USER` instruction |
| Ignoring layer order | Slow rebuilds | Put changing things last |
| Copying everything | Large images, secrets leaked | Use `.dockerignore` |
| Not cleaning up | Disk fills up | `docker system prune` regularly |

---

## Quiz

1. **What does `docker run -d -p 8080:80 nginx` do?**
   <details>
   <summary>Answer</summary>
   Runs an nginx container in detached mode (-d, background), mapping host port 8080 to container port 80. You can access nginx at http://localhost:8080.
   </details>

2. **Why should you put `COPY requirements.txt` before `COPY . .` in a Dockerfile?**
   <details>
   <summary>Answer</summary>
   Layer caching. If requirements.txt hasn't changed, Docker uses the cached layer for `pip install`. Copying all files first would bust the cache whenever any file changes, forcing dependency reinstallation.
   </details>

3. **What's the difference between `CMD` and `RUN`?**
   <details>
   <summary>Answer</summary>
   `RUN` executes during image build (installing packages, setting up). `CMD` defines the default command when a container starts. RUN creates image layers; CMD just sets metadata.
   </details>

4. **Why use Docker Compose instead of multiple `docker run` commands?**
   <details>
   <summary>Answer</summary>
   Docker Compose manages multiple containers as a single application. It handles networking between services, volume creation, dependency ordering, and is defined declaratively in one file.
   </details>

---

## Hands-On Exercise

**Task**: Build and run a custom image.

1. Create a project directory:
```bash
mkdir hello-docker && cd hello-docker
```

2. Create `app.py`:
```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hello from Docker!\n')

HTTPServer(('', 8000), Handler).serve_forever()
```

3. Create `Dockerfile`:
```dockerfile
FROM python:3.11-alpine
WORKDIR /app
COPY app.py .
EXPOSE 8000
CMD ["python", "app.py"]
```

4. Build and run:
```bash
docker build -t hello-docker:v1 .
docker run -d -p 8000:8000 --name hello hello-docker:v1
curl http://localhost:8000
docker rm -f hello
```

**Success criteria**: `curl http://localhost:8000` returns "Hello from Docker!"

---

## Summary

Essential Docker for Kubernetes:

**Commands**:
- `docker run` - Start containers
- `docker ps` - List containers
- `docker logs` - View output
- `docker exec` - Run commands in containers
- `docker build` - Create images
- `docker push/pull` - Share images

**Dockerfile basics**:
- `FROM` - Base image
- `COPY` - Add files
- `RUN` - Execute during build
- `CMD` - Default runtime command

**Best practices**:
- Use specific image tags
- Optimize layer caching
- Run as non-root
- One process per container

---

## Next Module

[Module 3: What Is Kubernetes?](../module-1.3-what-is-kubernetes/) - High-level overview of container orchestration.
