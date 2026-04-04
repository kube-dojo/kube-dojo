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

## What You'll Be Able to Do

After this module, you will be able to:
- **Build** a Docker image from a Dockerfile and explain what each instruction does
- **Run** containers with port mapping, environment variables, and volume mounts
- **Debug** a failing container by reading logs and exec-ing into it
- **Explain** the image layer system and why layer ordering matters for build speed

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

> **Pause and predict**: When you run the command below, what happens if port 8080 on your host machine is already in use by another application? The command will fail because Docker cannot bind to an already occupied host port. You would need to choose a different host port, like `-p 8081:80`.

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

> **Debugging mindset**: When a container isn't behaving right, these three commands are your debugging toolkit — in this order: `docker logs` (what happened?), `docker exec -it ... bash` (let me look inside), `docker inspect` (show me the full configuration). This same pattern applies in Kubernetes later: `kubectl logs`, `kubectl exec`, `kubectl describe`.

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

# Note: Docker images are content-addressable. The SHA256 hash of an image is its true identifier. Tags are just human-readable aliases.

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

> **War Story: The 5GB Docker Context**
> A developer once typed `docker build .` in their home directory instead of the project directory. Because they lacked a `.dockerignore` file, Docker dutifully attempted to copy their entire `Documents`, `Downloads`, and `Pictures` folders into the Docker build context. The build hung for 20 minutes before crashing the machine's memory. Always use a `.dockerignore` file to exclude `.git`, `node_modules`, and local environment files to keep your build context small and fast.

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

> **Stop and think**: Think about this — if you change one line of your Python code, do you want Docker to reinstall all your dependencies (which might take 2 minutes)? Or just copy the changed file (which takes 1 second)? The answer depends entirely on the ORDER of instructions in your Dockerfile. Read the BAD vs GOOD example below and see if you can spot why ordering matters.

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

> **Stop and think**: If you have a web application and a database, why is it a bad idea to put them both in the same Dockerfile and container? How would you scale the web application independently of the database if they were coupled together?

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

### Base Image Comparison

Choosing the right base image is critical for security and size:

| Base Image Type | Example | Size | Security Surface | Best For |
|-----------------|---------|------|------------------|----------|
| Full OS | `ubuntu:22.04` | ~70MB | Large (contains full utilities) | Complex legacy apps needing many system dependencies |
| Slim | `python:3.11-slim` | ~40MB | Medium (stripped down Debian) | Most standard applications, good balance of size and compatibility |
| Alpine | `python:3.11-alpine`| ~15MB | Small (uses musl instead of glibc) | Ultra-small images, but can cause compilation issues with C-extensions |
| Distroless | `gcr.io/distroless/static`| ~2MB | Minimal (no shell or package manager) | Production deployments of compiled languages (Go, Rust) |

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

- **Multi-stage builds reduce image size dramatically.** Build in one stage, copy only artifacts to final stage.
- **The `latest` tag is not special.** Docker doesn't automatically update it. It's just a convention that means "whatever was last pushed."
- **Docker Desktop is not Docker.** Docker (the tool) is free. Docker Desktop (the GUI/VM for Mac/Windows) has licensing requirements for businesses.
- **BuildKit is the default builder.** Since Docker 23.0, the BuildKit engine is the default, offering parallel execution, better caching, and improved performance over the legacy builder.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Using `latest` tag | Unpredictable versions | Use specific tags (`:1.25.3`) |
| Running as root | Security risk | Add `USER` instruction |
| Ignoring layer order | Slow rebuilds | Put changing things last |
| Copying everything | Large images, secrets leaked | Use `.dockerignore` |
| Not cleaning up | Disk fills up | `docker system prune` regularly |
| Hardcoding secrets | Passwords leaked in image | Use build secrets or inject at runtime |
| Using ADD instead of COPY | Unexpected archive extraction | Default to `COPY` unless extracting a tarball |
| Ignoring multi-stage builds | Compilers left in production image | Separate build tools from runtime environment |

### Exercise: Spot the Bugs

> **Stop and think**: Look at the following Dockerfile. There are at least three major anti-patterns or bugs. Can you identify them before reading the answers?

```dockerfile
FROM node:18
COPY . .
RUN npm install
CMD npm start
```

<details>
<summary>View the answers</summary>

1. **Missing .dockerignore or selective COPY**: Copying `.` to `.` before running `npm install` means the local `node_modules` folder might be copied over, which is bloated and platform-specific. Also, any code change invalidates the `npm install` cache.
2. **Ignoring layer caching**: It should `COPY package*.json ./` first, then `RUN npm install`, and *then* `COPY . .`. This ensures dependencies are only reinstalled when the package.json changes.
3. **Using a full OS base image**: `node:18` is nearly 1GB. It should use `node:18-slim` or `node:18-alpine` to reduce the attack surface and image pull time.
4. **Running as root**: There is no `USER` specified, meaning the Node process runs as the root user inside the container, which is a security risk.

</details>

---

## Quiz

1. **Scenario: You are building a Node.js application. Every time you change a single line of CSS, Docker takes 3 minutes to rebuild the image because it reinstalls all NPM packages. How can you rewrite your Dockerfile to fix this build time issue?**
   <details>
   <summary>Answer</summary>
   You should separate the copying of your dependency files from your source code. First, `COPY package.json` and `RUN npm install`. Then, use a separate `COPY . .` command for the rest of your source code. This leverages Docker's layer cache: Docker will only rerun the `npm install` layer if the `package.json` file changes, reducing your CSS code changes to a near-instantaneous build.
   </details>

2. **Scenario: You have a database container running locally, but when you restart it, all your saved users disappear. Which Docker run flag are you missing, and how does it solve the problem?**
   <details>
   <summary>Answer</summary>
   You are missing a volume mount, specifically using the `-v` or `--mount` flag (e.g., `-v db_data:/var/lib/postgresql/data`). By default, containers are ephemeral, meaning any data written to the container's writable layer is destroyed when the container is removed. A volume persists data outside the container's lifecycle directly on the host machine. This ensures your database records survive container restarts or replacements without being permanently lost.
   </details>

3. **Scenario: Your web application container starts successfully, but when you visit `localhost:8080`, it returns a generic 500 Internal Server Error instead of your application content. What are the first two Docker commands you should run to diagnose this issue, and what are you looking for?**
   <details>
   <summary>Answer</summary>
   The very first command should be `docker logs <container_id>` to check the application's standard output and standard error streams for Python/Node stack traces or crash reports. If the logs are inconclusive, the next step is `docker exec -it <container_id> sh` to get an interactive shell inside the running container. Once inside, you can manually inspect configuration files, verify environment variables, or run local curl commands to see if the internal application process is actually listening on the expected port. This two-step process isolates whether the issue is a crash during startup or a runtime misconfiguration.
   </details>

4. **Scenario: A developer attempts to reduce an image size by writing `RUN rm -rf /tmp/large-data` in a step immediately following the `RUN curl -o /tmp/large-data https://example.com/file` step. However, the final image size does not decrease. Why did the image size remain exactly the same despite deleting the file?**
   <details>
   <summary>Answer</summary>
   Docker images are built using a union file system where each instruction in the Dockerfile (like `RUN`, `COPY`, `ADD`) creates a new, immutable layer. When the developer downloaded the file, it was permanently baked into that specific layer. The subsequent `RUN rm` command creates a *new* layer that marks the file as deleted, hiding it from the final container view, but the underlying data still exists in the previous layer, consuming disk space. To actually save space, the download and deletion must happen in the exact same `RUN` instruction connected by `&&`.
   </details>

5. **Scenario: You are deploying a compiled Go binary to production. Your security team mandates that the container image must contain absolutely zero shell utilities (like `bash` or `curl`) to minimize the attack surface in case of a breach. Which base image type (Full OS, Slim, Alpine, or Distroless) is the correct choice, and why?**
   <details>
   <summary>Answer</summary>
   The correct choice is a Distroless base image (such as `gcr.io/distroless/static`). Distroless images contain only your application and its runtime dependencies, stripping away package managers, shells, and standard Unix utilities entirely. Alpine is small but still includes a package manager (`apk`) and a shell (`sh`), which a malicious actor could use if they gained remote code execution. By using Distroless, you guarantee that even if the application is compromised, the attacker has no built-in tools to pivot or download malware.
   </details>

6. **Scenario: You have a Docker Compose file defining a `frontend` service and a `backend` service. Your frontend code is trying to fetch data using `http://localhost:5000/api`, but the connection is refused, even though both containers are running. Why is `localhost` failing here, and what should the frontend use instead?**
   <details>
   <summary>Answer</summary>
   In the context of a container, `localhost` refers exclusively to the container's own internal network interface, not the host machine or other containers. The frontend container is looking for a backend process running inside itself, which doesn't exist. Instead, the frontend should use `http://backend:5000/api` because Docker Compose automatically sets up an internal DNS network where service names resolve to the correct container IP addresses. This internal DNS makes service-to-service communication seamless without needing to hardcode IP addresses.
   </details>

7. **Scenario: A container running a batch processing script crashes with an Out of Memory error and is now in an `Exited` state. You want to run `docker exec -it <container_id> bash` to inspect the temporary files it left behind. What happens when you run this command, and what is the proper way to access those files?**
   <details>
   <summary>Answer</summary>
   The `docker exec` command will fail because it can only spawn new processes inside a container that is currently in a `Running` state. You cannot execute a shell inside a stopped container. To access the files, you should use `docker cp <container_id>:/path/to/files ./local-dir` to copy the files out to your host machine. Alternatively, you could commit the stopped container to a new image using `docker commit` and then `docker run` a new interactive container from that image to explore its state.
   </details>

8. **Scenario: You have a local `archive.tar.gz` file containing static assets that need to be placed directly into the `/var/www/html` directory of your container image. Should you use `ADD archive.tar.gz /var/www/html/` or `COPY archive.tar.gz /var/www/html/`, and what is the functional difference between the two?**
   <details>
   <summary>Answer</summary>
   You should use `ADD` in this specific scenario because it has a built-in auto-extraction feature for local tar archives. `ADD archive.tar.gz /var/www/html/` will automatically unpack the contents of the zip file directly into the target directory during the build. If you used `COPY`, it would simply move the compressed `.tar.gz` file exactly as it is into the directory, forcing you to write an additional `RUN tar -xzf` command (and require the `tar` utility in the image) to extract it. However, for standard file copying, `COPY` is generally preferred as its behavior is more transparent and predictable.
   </details>

---

## Hands-On Challenge

### Level 1: The Basics (Build and Run)
**Task**: Build and run a custom web server image.
1. Create a directory and inside it, create an `index.html` file with the text "Hello KubeDojo!".
2. Create a `Dockerfile` that uses `nginx:alpine` as the base image.
3. Copy your `index.html` to `/usr/share/nginx/html/index.html` inside the image.
4. Build the image as `dojo-web:v1`.
5. Run the container in detached mode, mapping port 8080 on your host to port 80 in the container.
6. Verify by running `curl http://localhost:8080`.

### Level 2: Intermediate (Environment and Logs)
**Task**: Debug a failing container using logs and environment variables.
1. Run `docker run -d --name db postgres:15`.
2. Check its status with `docker ps -a`. Notice it exited immediately.
3. Check why it failed using `docker logs db`. (Hint: it complains about a missing password).
4. Remove the failed container.
5. Run it again, this time passing the required environment variable `POSTGRES_PASSWORD=secret`.
6. Verify it stays running.

### Level 3: Advanced (Optimization and Exec)
**Task**: Optimize a build and explore the running container.
1. Write a Dockerfile that installs `curl` in an `ubuntu` base image.
2. Ensure you use `apt-get update && apt-get install -y curl` in a single `RUN` instruction. Explain why this is important for layer caching.
3. Build and run the container interactively (`-it`) with the `bash` command.
4. Inside the container, prove you are running as root by typing `whoami`.
5. Type `exit` to leave. Notice the container stops. How would you keep it running in the background and execute into it later?

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

[Module 1.3: What Is Kubernetes?](../module-1.3-what-is-kubernetes/) - High-level overview of container orchestration.