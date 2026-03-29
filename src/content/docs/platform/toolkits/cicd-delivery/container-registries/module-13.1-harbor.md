---
title: "Module 13.1: Harbor - Enterprise Container Registry"
slug: platform/toolkits/cicd-delivery/container-registries/module-13.1-harbor
sidebar:
  order: 2
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-60 minutes

## Overview

Harbor is the enterprise container registry that ate Docker Hub's lunch. When organizations realized they couldn't bet their production on rate limits and someone else's infrastructure, Harbor emerged as the answer. It's a CNCF Graduated project—the same tier as Kubernetes itself—trusted by thousands of enterprises worldwide.

This module teaches you to deploy, configure, and operate Harbor for enterprise container image management.

## Prerequisites

- Docker fundamentals (building, pushing, tagging)
- Kubernetes basics (Deployments, Services, PVCs)
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) - Supply chain security concepts
- Understanding of image registries and OCI format

## Why This Module Matters

**Every container you run came from somewhere.** In production, "somewhere" can't be DockerHub with 100 pull/hour limits, or an unknown registry with unscanned images. Harbor gives you:

- **Vulnerability scanning**: Know what's in your images before production
- **Access control**: Who can push to `production/` namespace?
- **Audit trails**: Who pushed what, when?
- **Replication**: Images where you need them, when you need them
- **Compliance**: Image signing, retention policies, quotas

When your security team asks "how do we know this image is safe?", Harbor is your answer.

## Did You Know?

- **Origin Story**: Harbor was created by VMware in 2014, open-sourced in 2016, and donated to CNCF in 2018. It graduated in 2020—faster than most projects.
- **Scale**: Some Harbor installations manage over 1 million images and handle 100,000+ pulls per day
- **The Name**: Harbor was named because it's a "safe harbor" for your container images—protecting them from the open seas of the internet
- **Trivy Integration**: Harbor switched from Clair to Trivy as the default scanner in v2.2, reducing scan times by 10x

## Harbor Architecture

Understanding Harbor's components is essential for successful deployment and troubleshooting:

```
HARBOR ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                            ┌─────────────────────────────────────────┐
                            │              NGINX Proxy                │
                            │         (SSL termination, routing)      │
                            └──────────────────┬──────────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
           │     Core       │         │   Registry     │         │     Portal     │
           │   (API, Auth)  │         │  (Distribution)│         │     (UI)       │
           │                │         │                │         │                │
           │ - Projects     │         │ - OCI storage  │         │ - Web UI       │
           │ - Users/RBAC   │         │ - Blob/Manifest│         │ - Dashboard    │
           │ - Webhooks     │         │ - GC           │         │ - Admin        │
           └───────┬────────┘         └────────────────┘         └────────────────┘
                   │
        ┌──────────┴──────────┬───────────────────────┬───────────────────────┐
        │                     │                       │                       │
        ▼                     ▼                       ▼                       ▼
┌────────────────┐   ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│   Job Service  │   │     Trivy      │      │    Notary      │      │  Redis/Cache   │
│                │   │   (Scanner)    │      │  (Signing)     │      │                │
│ - Replication  │   │                │      │                │      │ - Session      │
│ - GC jobs      │   │ - CVE scan     │      │ - Trust        │      │ - Job queues   │
│ - Retention    │   │ - DB updates   │      │ - Cosign       │      │ - Caching      │
└────────────────┘   └────────────────┘      └────────────────┘      └────────────────┘
        │                     │                       │                       │
        └─────────────────────┴───────────────────────┴───────────────────────┘
                                              │
                                              ▼
                              ┌───────────────────────────────┐
                              │       PostgreSQL              │
                              │   (Metadata, users, RBAC)     │
                              └───────────────────────────────┘
                                              │
                                              ▼
                              ┌───────────────────────────────┐
                              │        Storage Backend        │
                              │   (S3 / Azure / GCS / Local)  │
                              └───────────────────────────────┘

COMPONENT RESPONSIBILITIES:
─────────────────────────────────────────────────────────────────────────────
Core        → Authentication, authorization, project management, API
Registry    → OCI-compliant image storage (Docker Distribution v2)
Portal      → Web UI for administration
Job Service → Async jobs (replication, GC, scanning)
Trivy       → Vulnerability scanning (built-in since v2.2)
Notary      → Image signing (optional, Docker Content Trust)
Redis       → Job queues, session management, caching
PostgreSQL  → Persistent metadata storage
```

## Core Concepts

### Projects: The Organizational Unit

Projects in Harbor are like namespaces with superpowers:

```
PROJECT STRUCTURE
─────────────────────────────────────────────────────────────────────────────

                    ┌────────────────────────────────────────┐
                    │              Harbor Instance           │
                    │                                        │
                    │    ┌────────────────────────────────┐  │
                    │    │         library (public)       │  │
                    │    │  • Base images                 │  │
                    │    │  • Shared utilities            │  │
                    │    │  • Anyone can pull             │  │
                    │    └────────────────────────────────┘  │
                    │                                        │
                    │    ┌────────────────────────────────┐  │
                    │    │       team-backend (private)   │  │
                    │    │  • API services                │  │
                    │    │  • Team-only access            │  │
                    │    │  • Auto-scan enabled           │  │
                    │    └────────────────────────────────┘  │
                    │                                        │
                    │    ┌────────────────────────────────┐  │
                    │    │       production (private)     │  │
                    │    │  • Signed images only          │  │
                    │    │  • Strict retention            │  │
                    │    │  • Scan required for pull      │  │
                    │    └────────────────────────────────┘  │
                    │                                        │
                    └────────────────────────────────────────┘

IMAGE NAMING:
─────────────────────────────────────────────────────────────────────────────
harbor.example.com / team-backend / api-server : v1.2.3
└──────┬─────────┘   └────┬─────┘   └───┬────┘   └─┬──┘
    registry          project      repository    tag
```

### RBAC: Who Can Do What

Harbor's role-based access control is project-scoped:

| Role | Pull | Push | Delete | Manage Members | Project Admin |
|------|------|------|--------|----------------|---------------|
| **Guest** | Yes | No | No | No | No |
| **Developer** | Yes | Yes | No | No | No |
| **Maintainer** | Yes | Yes | Yes | No | No |
| **Project Admin** | Yes | Yes | Yes | Yes | Yes |

**Robot Accounts**: For CI/CD pipelines, create robot accounts with scoped permissions:

```yaml
# Robot account for CI/CD
Name: robot$ci-push
Permissions:
  - project: team-backend
    access:
      - resource: repository
        action: push
      - resource: tag
        action: create
  - project: library
    access:
      - resource: repository
        action: pull
```

### Vulnerability Scanning

Harbor uses Trivy for vulnerability scanning:

```
VULNERABILITY SCANNING FLOW
─────────────────────────────────────────────────────────────────────────────

              Push Image                      Scan Triggered
                  │                                │
                  ▼                                ▼
        ┌─────────────────┐             ┌─────────────────┐
        │  Image Layers   │────────────▶│     Trivy       │
        │   Stored        │             │    Scanner      │
        └─────────────────┘             └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │  Trivy CVE DB   │
                                        │  (NVD, Alpine,  │
                                        │   Debian, etc.) │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                    ┌────────────────────────────────────────────────────┐
                    │                 SCAN RESULTS                       │
                    │                                                    │
                    │  ┌─────────────────────────────────────────────┐  │
                    │  │ CRITICAL: 2 | HIGH: 5 | MEDIUM: 12 | LOW: 8│  │
                    │  └─────────────────────────────────────────────┘  │
                    │                                                    │
                    │  CVE-2024-1234  │ Critical │ openssl   │ Fixed    │
                    │  CVE-2024-5678  │ High     │ curl      │ Update   │
                    │  CVE-2024-9012  │ Medium   │ libc      │ No fix   │
                    │                                                    │
                    └────────────────────────────────────────────────────┘

SCAN POLICY OPTIONS:
─────────────────────────────────────────────────────────────────────────────
Scan on Push     → Auto-scan when image pushed
Scan on Schedule → Daily/weekly vulnerability DB updates
Block on Pull    → Prevent pull if CVE severity threshold exceeded
```

## Deploying Harbor

### Option 1: Docker Compose (Development/Testing)

The fastest way to get Harbor running:

```bash
# Download the installer
HARBOR_VERSION="v2.10.0"
wget https://github.com/goharbor/harbor/releases/download/${HARBOR_VERSION}/harbor-offline-installer-${HARBOR_VERSION}.tgz
tar xzf harbor-offline-installer-${HARBOR_VERSION}.tgz
cd harbor

# Copy and edit the configuration
cp harbor.yml.tmpl harbor.yml
```

Edit `harbor.yml`:

```yaml
# harbor.yml - key settings
hostname: harbor.example.com  # Your domain

# HTTPS configuration (production)
https:
  port: 443
  certificate: /your/certificate.crt
  private_key: /your/private.key

# For testing only - use HTTPS in production!
# http:
#   port: 80

# Admin password - CHANGE THIS!
harbor_admin_password: Harbor12345

# Database settings
database:
  password: root123  # Change this!
  max_idle_conns: 100
  max_open_conns: 900

# Storage backend
# Default is local filesystem
storage_service:
  filesystem:
    maxthreads: 100
    rootdirectory: /storage

# For S3-compatible storage:
# storage_service:
#   s3:
#     accesskey: your-access-key
#     secretkey: your-secret-key
#     region: us-west-1
#     bucket: harbor-images
#     encrypt: true

# Trivy scanner settings
trivy:
  ignore_unfixed: false
  skip_update: false
  insecure: false
```

Run the installer:

```bash
# Install Harbor
./install.sh --with-trivy

# Verify services
docker-compose ps

# Access UI at https://harbor.example.com
# Login: admin / Harbor12345
```

### Option 2: Kubernetes with Helm (Production)

For production Kubernetes deployments:

```bash
# Add Helm repository
helm repo add harbor https://helm.goharbor.io
helm repo update

# Create namespace
kubectl create namespace harbor
```

Create a values file for production:

```yaml
# harbor-values.yaml
expose:
  type: ingress
  tls:
    enabled: true
    certSource: secret
    secret:
      secretName: harbor-tls
  ingress:
    hosts:
      core: harbor.example.com
    className: nginx
    annotations:
      nginx.ingress.kubernetes.io/proxy-body-size: "0"
      nginx.ingress.kubernetes.io/ssl-redirect: "true"

externalURL: https://harbor.example.com

# Persistence
persistence:
  enabled: true
  resourcePolicy: "keep"
  persistentVolumeClaim:
    registry:
      storageClass: "fast-ssd"
      size: 100Gi
    database:
      storageClass: "fast-ssd"
      size: 5Gi
    redis:
      storageClass: "fast-ssd"
      size: 1Gi
    trivy:
      storageClass: "fast-ssd"
      size: 5Gi

# External database (recommended for production)
database:
  type: external
  external:
    host: "postgresql.example.com"
    port: "5432"
    username: "harbor"
    password: "secretpassword"
    coreDatabase: "harbor"

# External Redis (recommended for production)
redis:
  type: external
  external:
    addr: "redis.example.com:6379"
    password: "redis-password"

# Admin password
harborAdminPassword: "SecurePassword123!"

# Resource requests/limits
core:
  resources:
    requests:
      memory: 256Mi
      cpu: 100m
    limits:
      memory: 512Mi
      cpu: 500m

registry:
  resources:
    requests:
      memory: 256Mi
      cpu: 100m

trivy:
  enabled: true
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1
      memory: 1Gi

# Enable metrics for Prometheus
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
```

Deploy Harbor:

```bash
# Install Harbor
helm install harbor harbor/harbor \
  --namespace harbor \
  -f harbor-values.yaml

# Watch deployment progress
kubectl -n harbor get pods -w

# Verify all components are running
kubectl -n harbor get pods
# Expected output:
# harbor-core-xxx           Running
# harbor-database-xxx       Running
# harbor-jobservice-xxx     Running
# harbor-nginx-xxx          Running
# harbor-portal-xxx         Running
# harbor-redis-xxx          Running
# harbor-registry-xxx       Running
# harbor-trivy-xxx          Running
```

### Configuring Docker to Use Harbor

```bash
# For HTTP (development only!)
# Add to /etc/docker/daemon.json:
{
  "insecure-registries": ["harbor.example.com"]
}
sudo systemctl restart docker

# For HTTPS with self-signed cert
# Copy CA cert
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp ca.crt /etc/docker/certs.d/harbor.example.com/
sudo systemctl restart docker

# Login to Harbor
docker login harbor.example.com
# Username: admin
# Password: Harbor12345

# Push an image
docker tag nginx:latest harbor.example.com/library/nginx:latest
docker push harbor.example.com/library/nginx:latest
```

### Configuring Kubernetes to Pull from Harbor

```yaml
# Create image pull secret
kubectl create secret docker-registry harbor-creds \
  --docker-server=harbor.example.com \
  --docker-username=admin \
  --docker-password=Harbor12345 \
  --docker-email=admin@example.com \
  -n default

# Reference in Pod spec
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: harbor.example.com/library/nginx:latest
  imagePullSecrets:
  - name: harbor-creds

# Or attach to ServiceAccount (recommended)
kubectl patch serviceaccount default \
  -p '{"imagePullSecrets": [{"name": "harbor-creds"}]}'
```

## Harbor Operations

### Creating Projects

Using the API:

```bash
# Create a project
curl -X POST "https://harbor.example.com/api/v2.0/projects" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "project_name": "team-backend",
    "metadata": {
      "public": "false",
      "enable_content_trust": "false",
      "auto_scan": "true",
      "severity": "high",
      "reuse_sys_cve_allowlist": "true"
    },
    "storage_limit": 10737418240
  }'

# List projects
curl -s "https://harbor.example.com/api/v2.0/projects" \
  -u "admin:Harbor12345" | jq .
```

### Setting Up Replication

Replicate images between Harbor instances or to/from external registries:

```
REPLICATION PATTERNS
─────────────────────────────────────────────────────────────────────────────

PUSH-BASED (Harbor → Remote):
┌───────────────┐                    ┌───────────────┐
│  Harbor       │────Push Images────▶│  Remote       │
│  (Primary)    │                    │  Registry     │
│               │                    │  (DR/Edge)    │
└───────────────┘                    └───────────────┘

PULL-BASED (Remote → Harbor):
┌───────────────┐                    ┌───────────────┐
│  Harbor       │◀───Pull Images─────│  DockerHub    │
│  (Cache)      │                    │  (Upstream)   │
│               │                    │               │
└───────────────┘                    └───────────────┘
```

Create a replication rule via API:

```bash
# First, create a registry endpoint
curl -X POST "https://harbor.example.com/api/v2.0/registries" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "name": "dockerhub",
    "type": "docker-hub",
    "url": "https://hub.docker.com",
    "credential": {
      "type": "basic",
      "access_key": "your-dockerhub-username",
      "access_secret": "your-dockerhub-token"
    }
  }'

# Create a pull-based replication rule
curl -X POST "https://harbor.example.com/api/v2.0/replication/policies" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "name": "pull-nginx-from-dockerhub",
    "src_registry": {
      "id": 1
    },
    "dest_namespace": "library",
    "dest_namespace_replace_count": 1,
    "trigger": {
      "type": "scheduled",
      "trigger_settings": {
        "cron": "0 0 * * *"
      }
    },
    "filters": [
      {
        "type": "name",
        "value": "library/nginx"
      },
      {
        "type": "tag",
        "value": "1.*"
      }
    ],
    "enabled": true,
    "deletion": false,
    "override": true,
    "speed": -1
  }'
```

### Retention Policies

Prevent storage bloat with retention rules:

```bash
# Create retention policy for a project
curl -X POST "https://harbor.example.com/api/v2.0/retentions" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "algorithm": "or",
    "rules": [
      {
        "disabled": false,
        "action": "retain",
        "params": {
          "latestPushedK": 10
        },
        "scope_selectors": {
          "repository": [
            {
              "kind": "doublestar",
              "pattern": "**"
            }
          ]
        },
        "tag_selectors": [
          {
            "kind": "doublestar",
            "pattern": "**"
          }
        ]
      },
      {
        "disabled": false,
        "action": "retain",
        "params": {
          "latestPulledN": 5
        },
        "scope_selectors": {
          "repository": [
            {
              "kind": "doublestar",
              "pattern": "**"
            }
          ]
        },
        "tag_selectors": [
          {
            "kind": "doublestar",
            "pattern": "v*"
          }
        ]
      }
    ],
    "scope": {
      "level": "project",
      "ref": 1
    },
    "trigger": {
      "kind": "Schedule",
      "settings": {
        "cron": "0 0 0 * * *"
      }
    }
  }'
```

Common retention patterns:

| Pattern | Rule | Use Case |
|---------|------|----------|
| Keep latest N | `latestPushedK: 10` | Development images |
| Keep by age | `nDaysSinceLastPush: 30` | Clean old builds |
| Keep pulled | `latestPulledN: 5` | Active images |
| Keep tags | `pattern: "v*"` | Release versions |
| Keep always | `always: true` | Critical base images |

### Garbage Collection

Clean up deleted image layers:

```bash
# Trigger garbage collection via API
curl -X POST "https://harbor.example.com/api/v2.0/system/gc/schedule" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "schedule": {
      "type": "Manual"
    },
    "parameters": {
      "delete_untagged": true,
      "dry_run": false
    }
  }'

# Check GC job status
curl -s "https://harbor.example.com/api/v2.0/system/gc" \
  -u "admin:Harbor12345" | jq '.[-1]'

# Schedule automatic GC
curl -X PUT "https://harbor.example.com/api/v2.0/system/gc/schedule" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "schedule": {
      "type": "Weekly",
      "cron": "0 0 0 * * 0"
    },
    "parameters": {
      "delete_untagged": true
    }
  }'
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/build-push.yaml
name: Build and Push to Harbor

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: harbor.example.com
  PROJECT: team-backend
  IMAGE_NAME: api-server

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Harbor
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.HARBOR_USERNAME }}
          password: ${{ secrets.HARBOR_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.PROJECT }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.PROJECT }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.PROJECT }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

      - name: Wait for scan
        run: |
          # Wait for Harbor to scan the image
          sleep 30

          # Check scan results
          TAG=$(echo "${{ steps.meta.outputs.tags }}" | head -1 | cut -d: -f2)
          SCAN_URL="${{ env.REGISTRY }}/api/v2.0/projects/${{ env.PROJECT }}/repositories/${{ env.IMAGE_NAME }}/artifacts/${TAG}/additions/vulnerabilities"

          RESULT=$(curl -s -u "${{ secrets.HARBOR_USERNAME }}:${{ secrets.HARBOR_PASSWORD }}" "$SCAN_URL")

          CRITICAL=$(echo "$RESULT" | jq -r '.["application/vnd.security.vulnerability.report; version=1.1"].summary.critical // 0')
          HIGH=$(echo "$RESULT" | jq -r '.["application/vnd.security.vulnerability.report; version=1.1"].summary.high // 0')

          echo "Critical: $CRITICAL, High: $HIGH"

          if [ "$CRITICAL" -gt 0 ]; then
            echo "::error::Found $CRITICAL critical vulnerabilities!"
            exit 1
          fi
```

### GitLab CI

```yaml
# .gitlab-ci.yml
variables:
  REGISTRY: harbor.example.com
  PROJECT: team-backend
  IMAGE_NAME: api-server

stages:
  - build
  - scan
  - deploy

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - echo "$HARBOR_PASSWORD" | docker login $REGISTRY -u "$HARBOR_USERNAME" --password-stdin
  script:
    - |
      if [ -n "$CI_COMMIT_TAG" ]; then
        TAG="$CI_COMMIT_TAG"
      else
        TAG="$CI_COMMIT_SHORT_SHA"
      fi

      docker build -t $REGISTRY/$PROJECT/$IMAGE_NAME:$TAG .
      docker push $REGISTRY/$PROJECT/$IMAGE_NAME:$TAG

      # Also tag as latest for main branch
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        docker tag $REGISTRY/$PROJECT/$IMAGE_NAME:$TAG $REGISTRY/$PROJECT/$IMAGE_NAME:latest
        docker push $REGISTRY/$PROJECT/$IMAGE_NAME:latest
      fi

check-vulnerabilities:
  stage: scan
  image: curlimages/curl:latest
  script:
    - |
      if [ -n "$CI_COMMIT_TAG" ]; then
        TAG="$CI_COMMIT_TAG"
      else
        TAG="$CI_COMMIT_SHORT_SHA"
      fi

      # Wait for scan to complete
      sleep 30

      # Get scan results
      SCAN_URL="https://$REGISTRY/api/v2.0/projects/$PROJECT/repositories/$IMAGE_NAME/artifacts/$TAG/additions/vulnerabilities"
      RESULT=$(curl -s -u "$HARBOR_USERNAME:$HARBOR_PASSWORD" "$SCAN_URL")

      CRITICAL=$(echo "$RESULT" | jq -r '.["application/vnd.security.vulnerability.report; version=1.1"].summary.critical // 0')

      if [ "$CRITICAL" -gt 0 ]; then
        echo "Found $CRITICAL critical vulnerabilities!"
        exit 1
      fi
  needs:
    - build
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        REGISTRY = 'harbor.example.com'
        PROJECT = 'team-backend'
        IMAGE_NAME = 'api-server'
        HARBOR_CREDS = credentials('harbor-credentials')
    }

    stages {
        stage('Build') {
            steps {
                script {
                    def imageTag = env.TAG_NAME ?: env.GIT_COMMIT.take(7)

                    sh """
                        docker login ${REGISTRY} -u ${HARBOR_CREDS_USR} -p ${HARBOR_CREDS_PSW}
                        docker build -t ${REGISTRY}/${PROJECT}/${IMAGE_NAME}:${imageTag} .
                        docker push ${REGISTRY}/${PROJECT}/${IMAGE_NAME}:${imageTag}
                    """

                    env.IMAGE_TAG = imageTag
                }
            }
        }

        stage('Check Vulnerabilities') {
            steps {
                script {
                    sleep(30) // Wait for scan

                    def scanUrl = "https://${REGISTRY}/api/v2.0/projects/${PROJECT}/repositories/${IMAGE_NAME}/artifacts/${env.IMAGE_TAG}/additions/vulnerabilities"

                    def result = sh(
                        script: """
                            curl -s -u ${HARBOR_CREDS_USR}:${HARBOR_CREDS_PSW} "${scanUrl}" | \
                            jq -r '.["application/vnd.security.vulnerability.report; version=1.1"].summary'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Scan results: ${result}"

                    def critical = sh(
                        script: "echo '${result}' | jq -r '.critical // 0'",
                        returnStdout: true
                    ).trim().toInteger()

                    if (critical > 0) {
                        error("Found ${critical} critical vulnerabilities!")
                    }
                }
            }
        }
    }
}
```

## Monitoring Harbor

### Prometheus Metrics

Harbor exposes metrics on `/metrics`:

```yaml
# prometheus-scrape-config.yaml
- job_name: 'harbor'
  static_configs:
    - targets:
      - harbor-core:8001
      - harbor-registry:8001
      - harbor-jobservice:8001
      - harbor-exporter:8001
  metrics_path: /metrics
```

Key metrics to monitor:

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `harbor_project_total` | Number of projects | N/A |
| `harbor_repo_total` | Total repositories | N/A |
| `harbor_artifact_pulled` | Pull count | Baseline + 50% |
| `harbor_artifact_pushed` | Push count | Baseline + 50% |
| `harbor_task_concurrency` | Active jobs | > 100 |
| `harbor_gc_completion_time_seconds` | GC duration | > 3600 |

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Harbor Overview",
    "panels": [
      {
        "title": "Image Pulls/min",
        "targets": [{
          "expr": "rate(harbor_artifact_pulled[5m])"
        }]
      },
      {
        "title": "Image Pushes/min",
        "targets": [{
          "expr": "rate(harbor_artifact_pushed[5m])"
        }]
      },
      {
        "title": "Storage Used",
        "targets": [{
          "expr": "harbor_project_quota_usage_byte"
        }]
      },
      {
        "title": "Scan Queue Length",
        "targets": [{
          "expr": "harbor_task_queue_size{type=\"SCAN\"}"
        }]
      }
    ]
  }
}
```

## War Story: The DockerHub Dependency

A healthcare company learned this lesson the hard way during a critical production deployment:

**The Setup**:
- 50-node Kubernetes cluster
- All images pulled from DockerHub
- Rolling update to new application version

**The Disaster**:
At 9 AM on a Monday (peak DockerHub traffic), they initiated the deployment. Ten nodes successfully pulled the new image. Then the rate limiting kicked in.

```
Failed to pull image "nginx:1.23":
toomanyrequests: You have reached your pull rate limit
```

**The Fallout**:
- 40 nodes stuck in ImagePullBackOff
- Half running old version, half running new (version skew)
- API inconsistencies confusing users
- 4-hour outage during business hours

**The Fix**:
They deployed Harbor over a weekend:

```
Week 1: Deploy Harbor on Kubernetes
Week 2: Set up proxy cache for DockerHub
Week 3: Migrate CI/CD to push to Harbor
Week 4: Update all deployments to pull from Harbor
Week 5: Replicate to DR site
```

**The Result**:
- Zero rate limit issues
- Average pull time: 2s (was 15s from DockerHub)
- Full visibility into what's running where
- Security team happy with vulnerability scanning

**The Lesson**: Your container registry is production infrastructure. Treat it that way.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| HTTP in production | Man-in-the-middle attacks, credential theft | Always use HTTPS with valid certificates |
| Default admin password | Trivial to compromise | Change immediately, use strong password |
| No quotas | Single project fills storage | Set project and user quotas |
| No retention | Storage grows unbounded | Configure retention policies |
| Skip scanning | Unknown vulnerabilities deployed | Enable auto-scan, enforce policies |
| Single instance | SPOF for all deployments | Multi-site replication |
| No monitoring | Issues discovered too late | Prometheus + alerting |
| Robot accounts everywhere | Over-privileged automation | Scope robot accounts narrowly |

## Quiz

Test your understanding of Harbor:

<details>
<summary>1. What is the relationship between Projects and Repositories in Harbor?</summary>

**Answer**: Projects are organizational units that contain repositories. A project defines access policies, quotas, and scanning rules. Repositories within a project inherit these settings. Think of projects as namespaces—`harbor.example.com/project/repository:tag`.
</details>

<details>
<summary>2. What happens when you delete an image tag in Harbor?</summary>

**Answer**: Deleting a tag only removes the tag reference, not the underlying layers. The actual blob data remains until garbage collection runs. This is because multiple tags might reference the same layers. GC identifies orphaned blobs and reclaims storage.
</details>

<details>
<summary>3. How does Harbor's proxy cache feature help with DockerHub rate limits?</summary>

**Answer**: Harbor acts as a pull-through cache. When a node requests `library/nginx:latest`, Harbor checks its cache first. If cached, it serves locally (no DockerHub hit). If not cached, Harbor pulls once from DockerHub and caches it. All subsequent pulls from any node hit the local cache.
</details>

<details>
<summary>4. What's the difference between push-based and pull-based replication?</summary>

**Answer**: Push-based: Harbor actively sends images to remote registries (DR site, edge locations). Pull-based: Harbor fetches images from remote registries (proxy cache, sync from upstream). Push is better for disaster recovery; pull is better for caching upstream registries.
</details>

<details>
<summary>5. Why would you use robot accounts instead of user credentials in CI/CD?</summary>

**Answer**: Robot accounts are: (1) Scoped to specific projects and actions, (2) Don't expire with user offboarding, (3) Can be revoked independently, (4) Auditable separately from user activity, (5) Don't count against user license limits. Never use personal credentials in automation.
</details>

<details>
<summary>6. How can you enforce that only scanned images can be pulled?</summary>

**Answer**: In project settings, enable "Prevent vulnerable images from running" and set a severity threshold (e.g., Critical, High). Harbor will block pulls of images exceeding that threshold. Combined with auto-scan on push, this ensures only scanned, passing images deploy.
</details>

<details>
<summary>7. What components are required for a highly available Harbor deployment?</summary>

**Answer**: HA Harbor needs: (1) Multiple Harbor replicas behind load balancer, (2) External PostgreSQL with replication, (3) External Redis cluster, (4) Shared storage (S3/GCS/Azure) for registry data, (5) Session affinity or shared session store. The Helm chart supports all these.
</details>

<details>
<summary>8. How does Harbor integrate with Kubernetes admission controllers for image policy?</summary>

**Answer**: Harbor doesn't directly integrate with admission controllers, but works with them. Typical pattern: OPA/Gatekeeper policy requiring images from `harbor.example.com/*` + Cosign verification of signatures. Harbor stores the signed images and signatures; the admission controller enforces the policy.
</details>

## Hands-On Exercise: Deploy Harbor and Secure a Pipeline

### Objective
Deploy Harbor on a local Kubernetes cluster, configure a project with security policies, and create a CI/CD pipeline that enforces vulnerability scanning.

### Environment Setup

```bash
# Create kind cluster with extra port mappings
cat <<EOF | kind create cluster --name harbor-lab --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 80
  - containerPort: 30443
    hostPort: 443
EOF

# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Step 1: Deploy Harbor with Helm

```bash
# Add Harbor helm repo
helm repo add harbor https://helm.goharbor.io
helm repo update

# Create namespace
kubectl create namespace harbor

# Create minimal values for local development
cat <<EOF > harbor-values.yaml
expose:
  type: nodePort
  tls:
    enabled: false
  nodePort:
    ports:
      http:
        nodePort: 30080

externalURL: http://localhost

harborAdminPassword: "Harbor12345"

persistence:
  enabled: true
  persistentVolumeClaim:
    registry:
      size: 5Gi
    database:
      size: 1Gi
    redis:
      size: 1Gi
    trivy:
      size: 1Gi

trivy:
  enabled: true
EOF

# Install Harbor
helm install harbor harbor/harbor \
  --namespace harbor \
  -f harbor-values.yaml

# Wait for all pods to be ready (this takes 3-5 minutes)
kubectl -n harbor get pods -w

# Verify Harbor is running
curl -s http://localhost/api/v2.0/health | jq .
```

### Step 2: Configure Harbor

```bash
# Login to Harbor CLI
docker login localhost -u admin -p Harbor12345

# Create a project via API
curl -X POST "http://localhost/api/v2.0/projects" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "project_name": "secure-apps",
    "metadata": {
      "public": "false",
      "auto_scan": "true",
      "severity": "high",
      "prevent_vul": "true"
    }
  }'

# Create a robot account for CI/CD
ROBOT_RESPONSE=$(curl -s -X POST "http://localhost/api/v2.0/robots" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "name": "ci-push",
    "description": "CI/CD push robot",
    "duration": -1,
    "level": "project",
    "permissions": [
      {
        "namespace": "secure-apps",
        "kind": "project",
        "access": [
          {"resource": "repository", "action": "push"},
          {"resource": "repository", "action": "pull"},
          {"resource": "tag", "action": "create"},
          {"resource": "artifact", "action": "read"}
        ]
      }
    ]
  }')

echo "Robot token: $(echo $ROBOT_RESPONSE | jq -r '.secret')"
```

### Step 3: Build and Push a Test Image

```bash
# Create a simple Dockerfile
mkdir -p /tmp/harbor-test && cd /tmp/harbor-test

cat <<EOF > Dockerfile
FROM nginx:1.25
COPY index.html /usr/share/nginx/html/
EOF

cat <<EOF > index.html
<h1>Harbor Test</h1>
EOF

# Build and push
docker build -t localhost/secure-apps/test-app:v1 .
docker push localhost/secure-apps/test-app:v1

# Check scan results (wait a moment for scan to complete)
sleep 30
curl -s "http://localhost/api/v2.0/projects/secure-apps/repositories/test-app/artifacts/v1" \
  -u "admin:Harbor12345" | jq '.scan_overview'
```

### Step 4: Test Vulnerability Policy

```bash
# Build an image with known vulnerabilities (old alpine)
cat <<EOF > Dockerfile.vulnerable
FROM alpine:3.7
RUN apk add --no-cache curl
EOF

docker build -t localhost/secure-apps/vulnerable-app:v1 -f Dockerfile.vulnerable .
docker push localhost/secure-apps/vulnerable-app:v1

# Wait for scan
sleep 30

# Try to pull (should fail if vulnerabilities exceed threshold)
docker pull localhost/secure-apps/vulnerable-app:v1

# Check vulnerability details
curl -s "http://localhost/api/v2.0/projects/secure-apps/repositories/vulnerable-app/artifacts/v1/additions/vulnerabilities" \
  -u "admin:Harbor12345" | jq '.["application/vnd.security.vulnerability.report; version=1.1"].summary'
```

### Step 5: Configure Retention Policy

```bash
# Create retention policy
curl -X POST "http://localhost/api/v2.0/retentions" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d '{
    "algorithm": "or",
    "rules": [
      {
        "action": "retain",
        "params": {"latestPushedK": 5},
        "scope_selectors": {
          "repository": [{"kind": "doublestar", "pattern": "**"}]
        },
        "tag_selectors": [
          {"kind": "doublestar", "pattern": "**"}
        ]
      }
    ],
    "scope": {"level": "project", "ref": 2},
    "trigger": {"kind": "Schedule", "settings": {"cron": "0 0 0 * * *"}}
  }'

# Link retention policy to project
RETENTION_ID=$(curl -s "http://localhost/api/v2.0/retentions" -u "admin:Harbor12345" | jq '.[0].id')
curl -X PUT "http://localhost/api/v2.0/projects/secure-apps" \
  -H "Content-Type: application/json" \
  -u "admin:Harbor12345" \
  -d "{\"metadata\": {\"retention_id\": \"$RETENTION_ID\"}}"
```

### Success Criteria

- [ ] Harbor is running on Kubernetes
- [ ] `secure-apps` project created with auto-scan enabled
- [ ] Robot account created for CI/CD
- [ ] Test image pushed and scanned
- [ ] Vulnerable image blocked from pull
- [ ] Retention policy configured

### Cleanup

```bash
# Delete kind cluster
kind delete cluster --name harbor-lab

# Clean up test directory
rm -rf /tmp/harbor-test
```

## Key Takeaways

1. **Harbor is enterprise-ready**: CNCF Graduated, battle-tested at scale, actively maintained
2. **Projects are namespaces with policies**: Use them to organize teams, environments, and access
3. **Scanning is non-negotiable**: Enable auto-scan and enforce vulnerability thresholds
4. **Robot accounts for automation**: Never use personal credentials in CI/CD pipelines
5. **Replication enables resilience**: Multi-site for DR, proxy cache for upstream registries
6. **Garbage collection is essential**: Schedule regular GC to reclaim storage
7. **Retention prevents bloat**: Define policies before storage becomes a problem
8. **Monitor everything**: Prometheus metrics, alerting, and dashboards
9. **Plan for HA**: External database, Redis, and shared storage for production
10. **It's production infrastructure**: Your registry is as critical as your Kubernetes cluster

## Next Module

Continue to [Module 13.2: Zot](module-13.2-zot/) — The lightweight, OCI-native alternative for minimal footprint requirements.

---

*"If you don't control your container registry, you don't control your supply chain. Harbor gives you that control."*
