---
title: "Module 13.2: Zot - The Minimal OCI-Native Registry"
slug: platform/toolkits/cicd-delivery/container-registries/module-13.2-zot
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

Zot is the registry that asks: "What if we started from scratch?" While Harbor evolved from Docker's ecosystem, Zot was built from the ground up for the OCI (Open Container Initiative) specification. The result? A single binary under 20MB that's fully OCI-compliant, needs no database, and runs anywhere from Kubernetes to a Raspberry Pi.

This module teaches you to deploy and operate Zot for scenarios where minimal footprint matters.

## Prerequisites

- Docker fundamentals (building, pushing, tagging)
- Basic understanding of container registries
- Familiarity with OCI artifacts (images, Helm charts, signatures)
- Command-line comfort with curl and JSON

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Zot as a minimal OCI-native registry with zero external dependencies**
- **Configure Zot for OCI artifact storage including Helm charts, WASM modules, and container images**
- **Implement registry mirroring and content synchronization between Zot instances**
- **Compare Zot's single-binary architecture against Harbor for resource-constrained environments**


## Why This Module Matters

Not every registry needs to be Harbor. Sometimes you need:

- **Edge deployments**: Registry on a 1GB RAM device
- **Air-gapped simplicity**: No database to configure
- **Development speed**: Start in seconds, not minutes
- **CI/CD caching**: Local registry for build caching
- **OCI artifact storage**: Not just images—Helm charts, signatures, SBOMs

Zot fills these niches with elegant minimalism. It's the "Alpine Linux of registries."

## Did You Know?

- **Single Binary**: Zot is distributed as a ~15MB binary with zero runtime dependencies
- **OCI Native**: First registry built purely for OCI spec (no Docker Registry v1 legacy)
- **Project Origin**: Created by Cisco engineers who wanted a clean-slate OCI implementation
- **Helm Charts**: Zot natively stores Helm charts as OCI artifacts—no separate ChartMuseum needed
- **Cosign Built-in**: Signature verification integrated without external dependencies

## Zot Architecture

Zot's architecture is refreshingly simple:

```
ZOT ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                    ┌─────────────────────────────────────────┐
                    │              ZOT BINARY                 │
                    │                                         │
                    │  ┌─────────────────────────────────────┐│
                    │  │           HTTP Server               ││
                    │  │      (OCI Distribution API)         ││
                    │  └─────────────────┬───────────────────┘│
                    │                    │                    │
                    │  ┌─────────────────┼───────────────────┐│
                    │  │                 │                   ││
                    │  │  ┌──────────────▼──────────────┐   ││
                    │  │  │       Storage Engine        │   ││
                    │  │  │  (filesystem / S3 / etc)    │   ││
                    │  │  └─────────────────────────────┘   ││
                    │  │                                     ││
                    │  │  ┌─────────────┐ ┌─────────────┐   ││
                    │  │  │   Search    │ │    Sync     │   ││
                    │  │  │  (optional) │ │  (optional) │   ││
                    │  │  └─────────────┘ └─────────────┘   ││
                    │  │                                     ││
                    │  │  ┌─────────────┐ ┌─────────────┐   ││
                    │  │  │   Metrics   │ │  Extensions │   ││
                    │  │  │ (Prometheus)│ │   (lint,    │   ││
                    │  │  │             │ │  scrub,etc) │   ││
                    │  │  └─────────────┘ └─────────────┘   ││
                    │  │                                     ││
                    │  └─────────────────────────────────────┘│
                    │                                         │
                    └─────────────────────────────────────────┘
                                        │
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │            STORAGE BACKEND              │
                    │                                         │
                    │   Local FS  │  S3   │  GCS  │  Azure   │
                    └─────────────────────────────────────────┘

NO EXTERNAL DEPENDENCIES:
─────────────────────────────────────────────────────────────────────────────
✓ No PostgreSQL
✓ No Redis
✓ No separate UI service
✓ No job queue
✓ Single process

COMPARISON TO HARBOR:
─────────────────────────────────────────────────────────────────────────────
                        Zot             Harbor
─────────────────────────────────────────────────────────────────────────────
Binary size            ~15MB           ~500MB (images)
RAM minimum            50MB            2GB+
Components             1               8+
Database               None            PostgreSQL
Startup time           <1 second       2-3 minutes
Configuration          Single JSON     Multiple YAMLs
```

## Core Concepts

### OCI Distribution Specification

Zot implements the OCI Distribution Specification completely:

```
OCI DISTRIBUTION API
─────────────────────────────────────────────────────────────────────────────

Endpoint                          Method   Description
─────────────────────────────────────────────────────────────────────────────
/v2/                              GET      Check API version
/v2/_catalog                      GET      List repositories
/v2/{name}/tags/list              GET      List tags for repo
/v2/{name}/manifests/{ref}        GET      Get manifest
/v2/{name}/manifests/{ref}        PUT      Push manifest
/v2/{name}/manifests/{ref}        DELETE   Delete manifest
/v2/{name}/blobs/{digest}         GET      Get blob (layer)
/v2/{name}/blobs/{digest}         DELETE   Delete blob
/v2/{name}/blobs/uploads/         POST     Start blob upload
/v2/{name}/blobs/uploads/{uuid}   PATCH    Upload chunk
/v2/{name}/blobs/uploads/{uuid}   PUT      Complete upload

OCI ARTIFACT TYPES (All stored the same way):
─────────────────────────────────────────────────────────────────────────────
Container Images    application/vnd.oci.image.manifest.v1+json
Helm Charts         application/vnd.cncf.helm.config.v1+json
Cosign Signatures   application/vnd.dev.cosign.simplesigning.v1+json
SBOM               application/spdx+json
```

### Storage Layout

Zot uses content-addressable storage:

```
FILESYSTEM STORAGE LAYOUT
─────────────────────────────────────────────────────────────────────────────

/var/lib/zot/
├── myapp/                           # Repository
│   ├── blobs/
│   │   └── sha256/
│   │       ├── abc123...            # Layer blob
│   │       ├── def456...            # Config blob
│   │       └── ghi789...            # Manifest blob
│   └── index.json                   # Tag → digest mapping
│
├── library/
│   └── nginx/
│       ├── blobs/
│       │   └── sha256/
│       │       └── ...
│       └── index.json
│
└── _uploads/                        # Temporary upload chunks
    └── {uuid}/
        └── data

index.json structure:
{
  "schemaVersion": 2,
  "manifests": [
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:abc123...",
      "size": 1234,
      "annotations": {
        "org.opencontainers.image.ref.name": "v1.0.0"
      }
    }
  ]
}
```

## Deploying Zot

### Option 1: Binary Installation

The simplest deployment—just download and run:

```bash
# Download the latest release
ZOT_VERSION="v2.0.1"
curl -Lo zot https://github.com/project-zot/zot/releases/download/${ZOT_VERSION}/zot-linux-amd64
chmod +x zot

# Create minimal configuration
cat > config.json <<EOF
{
  "distSpecVersion": "1.1.0",
  "storage": {
    "rootDirectory": "/var/lib/zot"
  },
  "http": {
    "address": "0.0.0.0",
    "port": "5000"
  },
  "log": {
    "level": "info"
  }
}
EOF

# Create storage directory
sudo mkdir -p /var/lib/zot
sudo chown $USER /var/lib/zot

# Run Zot
./zot serve config.json

# Test it
curl http://localhost:5000/v2/
# {"distSpecVersion":"1.1.0"}
```

### Option 2: Docker Container

```bash
# Run Zot in Docker
docker run -d \
  --name zot \
  -p 5000:5000 \
  -v zot-data:/var/lib/zot \
  ghcr.io/project-zot/zot-linux-amd64:latest

# Verify
curl http://localhost:5000/v2/

# Push an image
docker tag nginx:alpine localhost:5000/library/nginx:alpine
docker push localhost:5000/library/nginx:alpine

# List repositories
curl -s http://localhost:5000/v2/_catalog | jq .
```

### Option 3: Kubernetes Deployment

```yaml
# zot-deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: zot
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: zot-config
  namespace: zot
data:
  config.json: |
    {
      "distSpecVersion": "1.1.0",
      "storage": {
        "rootDirectory": "/var/lib/zot",
        "gc": true,
        "gcDelay": "1h",
        "gcInterval": "6h"
      },
      "http": {
        "address": "0.0.0.0",
        "port": "5000"
      },
      "log": {
        "level": "info"
      },
      "extensions": {
        "metrics": {
          "enable": true,
          "prometheus": {
            "path": "/metrics"
          }
        },
        "search": {
          "enable": true,
          "cve": {
            "updateInterval": "2h"
          }
        }
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zot
  namespace: zot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zot
  template:
    metadata:
      labels:
        app: zot
    spec:
      containers:
      - name: zot
        image: ghcr.io/project-zot/zot-linux-amd64:v2.0.1
        ports:
        - containerPort: 5000
          name: registry
        volumeMounts:
        - name: config
          mountPath: /etc/zot
        - name: data
          mountPath: /var/lib/zot
        args:
        - serve
        - /etc/zot/config.json
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /v2/
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /v2/
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: zot-config
      - name: data
        persistentVolumeClaim:
          claimName: zot-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: zot-data
  namespace: zot
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: zot
  namespace: zot
spec:
  selector:
    app: zot
  ports:
  - port: 5000
    targetPort: 5000
    name: registry
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: zot
  namespace: zot
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "0"
spec:
  ingressClassName: nginx
  rules:
  - host: zot.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: zot
            port:
              number: 5000
```

Apply the configuration:

```bash
kubectl apply -f zot-deployment.yaml

# Wait for deployment
kubectl -n zot rollout status deployment/zot

# Test via port-forward
kubectl -n zot port-forward svc/zot 5000:5000 &
curl http://localhost:5000/v2/
```

## Configuration Deep Dive

### Full Configuration Example

```json
{
  "distSpecVersion": "1.1.0",

  "storage": {
    "rootDirectory": "/var/lib/zot",
    "dedupe": true,
    "gc": true,
    "gcDelay": "1h",
    "gcInterval": "6h",
    "commit": true,
    "subPaths": {
      "/production": {
        "rootDirectory": "/mnt/fast-ssd/production",
        "dedupe": true
      },
      "/cache": {
        "rootDirectory": "/mnt/large-hdd/cache",
        "dedupe": false
      }
    }
  },

  "http": {
    "address": "0.0.0.0",
    "port": "5000",
    "realm": "zot",
    "tls": {
      "cert": "/certs/server.crt",
      "key": "/certs/server.key"
    },
    "auth": {
      "htpasswd": {
        "path": "/etc/zot/htpasswd"
      }
    },
    "accessControl": {
      "repositories": {
        "**": {
          "anonymousPolicy": ["read"],
          "policies": [
            {
              "users": ["admin"],
              "actions": ["read", "create", "update", "delete"]
            },
            {
              "users": ["ci-user"],
              "actions": ["read", "create"]
            }
          ]
        },
        "production/**": {
          "policies": [
            {
              "users": ["admin", "release-manager"],
              "actions": ["read", "create", "update", "delete"]
            },
            {
              "users": ["developer"],
              "actions": ["read"]
            }
          ]
        }
      }
    }
  },

  "log": {
    "level": "info",
    "output": "/var/log/zot/zot.log",
    "audit": "/var/log/zot/audit.log"
  },

  "extensions": {
    "metrics": {
      "enable": true,
      "prometheus": {
        "path": "/metrics"
      }
    },
    "search": {
      "enable": true,
      "cve": {
        "updateInterval": "2h",
        "trivy": {
          "DBRepository": "ghcr.io/aquasecurity/trivy-db"
        }
      }
    },
    "ui": {
      "enable": true
    },
    "sync": {
      "enable": true,
      "registries": [
        {
          "urls": ["https://registry-1.docker.io"],
          "onDemand": true,
          "content": [
            {
              "prefix": "library/**"
            }
          ],
          "tlsVerify": true,
          "maxRetries": 3,
          "retryDelay": "5m"
        }
      ]
    },
    "scrub": {
      "enable": true,
      "interval": "24h"
    },
    "lint": {
      "enable": true,
      "mandatoryAnnotations": [
        "org.opencontainers.image.source",
        "org.opencontainers.image.licenses"
      ]
    }
  }
}
```

### Configuration Sections Explained

| Section | Purpose | Key Settings |
|---------|---------|--------------|
| **storage** | Where and how to store blobs | `rootDirectory`, `dedupe`, `gc`, `subPaths` |
| **http** | Network and authentication | `port`, `tls`, `auth`, `accessControl` |
| **log** | Logging configuration | `level`, `output`, `audit` |
| **extensions.sync** | Mirror/cache upstream registries | `registries`, `onDemand`, `content` |
| **extensions.search** | Enable CVE scanning | `cve.updateInterval`, `trivy` |
| **extensions.metrics** | Prometheus metrics | `prometheus.path` |
| **extensions.scrub** | Verify storage integrity | `interval` |
| **extensions.lint** | Enforce image metadata | `mandatoryAnnotations` |

## Authentication and Access Control

### htpasswd Authentication

```bash
# Create htpasswd file
htpasswd -Bbn admin secretpassword > /etc/zot/htpasswd
htpasswd -Bbn ci-user cipassword >> /etc/zot/htpasswd
htpasswd -Bbn developer devpassword >> /etc/zot/htpasswd

# In config.json:
{
  "http": {
    "auth": {
      "htpasswd": {
        "path": "/etc/zot/htpasswd"
      }
    }
  }
}
```

### LDAP Authentication

```json
{
  "http": {
    "auth": {
      "ldap": {
        "address": "ldap.example.com",
        "port": 636,
        "startTLS": false,
        "baseDN": "ou=users,dc=example,dc=com",
        "userAttribute": "uid",
        "userGroupAttribute": "memberOf",
        "bindDN": "cn=admin,dc=example,dc=com",
        "bindPassword": "ldap-password",
        "skipVerify": false,
        "subtreeSearch": true
      }
    },
    "accessControl": {
      "repositories": {
        "**": {
          "policies": [
            {
              "groups": ["cn=developers,ou=groups,dc=example,dc=com"],
              "actions": ["read", "create"]
            },
            {
              "groups": ["cn=admins,ou=groups,dc=example,dc=com"],
              "actions": ["read", "create", "update", "delete"]
            }
          ]
        }
      }
    }
  }
}
```

### OAuth2/OIDC Authentication

```json
{
  "http": {
    "auth": {
      "openid": {
        "providers": {
          "github": {
            "clientid": "your-client-id",
            "clientsecret": "your-client-secret",
            "issuer": "https://token.actions.githubusercontent.com",
            "scopes": ["openid", "email"]
          },
          "keycloak": {
            "clientid": "zot-client",
            "clientsecret": "your-secret",
            "issuer": "https://keycloak.example.com/realms/main",
            "scopes": ["openid", "profile", "email"]
          }
        }
      }
    }
  }
}
```

## Sync and Replication

### On-Demand Proxy Cache

Cache images from upstream registries on first pull:

```json
{
  "extensions": {
    "sync": {
      "enable": true,
      "registries": [
        {
          "urls": ["https://registry-1.docker.io"],
          "onDemand": true,
          "content": [
            {
              "prefix": "library/**"
            }
          ],
          "tlsVerify": true,
          "maxRetries": 3,
          "retryDelay": "5m",
          "pollInterval": "6h"
        },
        {
          "urls": ["https://ghcr.io"],
          "onDemand": true,
          "content": [
            {
              "prefix": "**"
            }
          ]
        }
      ]
    }
  }
}
```

Using the proxy cache:

```bash
# Pull through Zot (first request fetches from DockerHub)
docker pull zot.example.com/library/nginx:latest

# Subsequent pulls come from local cache
docker pull zot.example.com/library/nginx:latest  # Instant!

# Works for any configured upstream
docker pull zot.example.com/ghcr.io/kubernetes/kubectl:latest
```

### Scheduled Synchronization

Pre-fetch specific images:

```json
{
  "extensions": {
    "sync": {
      "enable": true,
      "registries": [
        {
          "urls": ["https://registry-1.docker.io"],
          "onDemand": false,
          "pollInterval": "6h",
          "content": [
            {
              "prefix": "library/nginx",
              "tags": {
                "regex": "^1\\.2[0-9].*"
              }
            },
            {
              "prefix": "library/alpine",
              "tags": {
                "regex": "^3\\.(1[789]|20).*"
              }
            }
          ]
        }
      ]
    }
  }
}
```

### Multi-Site Replication

```
ZOT-TO-ZOT REPLICATION
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────┐         ┌─────────────────────────┐
│    US-East (Primary)    │         │    EU-West (Replica)    │
│                         │         │                         │
│  ┌───────────────────┐  │         │  ┌───────────────────┐  │
│  │       Zot         │──┼────────▶│──│       Zot         │  │
│  │                   │  │  sync   │  │                   │  │
│  └───────────────────┘  │         │  └───────────────────┘  │
│                         │         │                         │
└─────────────────────────┘         └─────────────────────────┘

US-East config (source):
{
  "extensions": {
    "sync": {
      "enable": true,
      "registries": []  // Primary doesn't pull from anywhere
    }
  }
}

EU-West config (replica):
{
  "extensions": {
    "sync": {
      "enable": true,
      "registries": [
        {
          "urls": ["https://zot-us-east.example.com"],
          "onDemand": true,
          "pollInterval": "15m",
          "content": [
            {
              "prefix": "**"
            }
          ],
          "credentials": {
            "username": "sync-user",
            "password": "sync-password"
          }
        }
      ]
    }
  }
}
```

## OCI Artifacts: Beyond Container Images

### Storing Helm Charts

Zot natively supports Helm charts as OCI artifacts:

```bash
# Enable OCI in Helm
export HELM_EXPERIMENTAL_OCI=1

# Login to Zot
helm registry login zot.example.com

# Package and push chart
helm package mychart/
helm push mychart-1.0.0.tgz oci://zot.example.com/charts

# Pull and install
helm pull oci://zot.example.com/charts/mychart --version 1.0.0
helm install myrelease oci://zot.example.com/charts/mychart --version 1.0.0

# List chart versions
curl -s https://zot.example.com/v2/charts/mychart/tags/list | jq .
```

### Storing Cosign Signatures

```bash
# Sign an image with cosign
cosign sign --key cosign.key zot.example.com/myapp:v1.0.0

# Verify signature
cosign verify --key cosign.pub zot.example.com/myapp:v1.0.0

# Signatures are stored alongside the image
curl -s https://zot.example.com/v2/myapp/tags/list | jq .
# Shows: ["v1.0.0", "sha256-abc123.sig"]
```

### Storing SBOMs

```bash
# Generate SBOM with syft
syft zot.example.com/myapp:v1.0.0 -o spdx-json > sbom.json

# Attach SBOM to image with cosign
cosign attach sbom --sbom sbom.json zot.example.com/myapp:v1.0.0

# Download SBOM
cosign download sbom zot.example.com/myapp:v1.0.0
```

## Vulnerability Scanning

Zot has built-in CVE scanning via Trivy:

```json
{
  "extensions": {
    "search": {
      "enable": true,
      "cve": {
        "updateInterval": "2h",
        "trivy": {
          "DBRepository": "ghcr.io/aquasecurity/trivy-db"
        }
      }
    }
  }
}
```

Query CVEs via the search API:

```bash
# Get CVEs for an image
curl -s "https://zot.example.com/v2/_zot/ext/search?query=%7B%0A%20%20CVEListForImage(image%3A%22myapp%3Av1.0.0%22)%20%7B%0A%20%20%20%20Tag%0A%20%20%20%20CVEList%20%7B%0A%20%20%20%20%20%20Id%0A%20%20%20%20%20%20Severity%0A%20%20%20%20%20%20Title%0A%20%20%20%20%20%20PackageList%20%7B%0A%20%20%20%20%20%20%20%20Name%0A%20%20%20%20%20%20%20%20InstalledVersion%0A%20%20%20%20%20%20%20%20FixedVersion%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D" | jq .

# The query (URL-decoded):
# {
#   CVEListForImage(image:"myapp:v1.0.0") {
#     Tag
#     CVEList {
#       Id
#       Severity
#       Title
#       PackageList {
#         Name
#         InstalledVersion
#         FixedVersion
#       }
#     }
#   }
# }

# Find images affected by specific CVE
curl -s "https://zot.example.com/v2/_zot/ext/search?query=%7BImageListForCVE(id%3A%22CVE-2024-1234%22)%7BName%20Tags%7D%7D" | jq .
```

## War Story: The Edge Registry

A logistics company needed container registries at 200 warehouse locations:

**The Challenge**:
- Warehouses have limited bandwidth (10 Mbps shared)
- IT staff on-site is minimal (forklift drivers, not sysadmins)
- Devices range from industrial PCs to Raspberry Pis
- Images need to be available even during internet outages

**Why Harbor Didn't Work**:
- 2GB RAM minimum—their edge devices had 1GB
- PostgreSQL dependency—one more thing to break
- Complex deployment—required trained staff
- Recovery from failure required external support

**The Zot Solution**:

```bash
# Edge deployment script (runs on any Linux)
#!/bin/bash
set -e

# Download Zot binary
curl -Lo /usr/local/bin/zot https://github.com/project-zot/zot/releases/download/v2.0.1/zot-linux-arm64
chmod +x /usr/local/bin/zot

# Create minimal config
cat > /etc/zot/config.json <<EOF
{
  "storage": {
    "rootDirectory": "/data/zot"
  },
  "http": {
    "address": "0.0.0.0",
    "port": "5000"
  },
  "extensions": {
    "sync": {
      "enable": true,
      "registries": [{
        "urls": ["https://harbor.hq.example.com"],
        "onDemand": true,
        "pollInterval": "6h",
        "content": [{"prefix": "warehouse/**"}]
      }]
    }
  }
}
EOF

# Create systemd service
cat > /etc/systemd/system/zot.service <<EOF
[Unit]
Description=Zot Container Registry
After=network.target

[Service]
ExecStart=/usr/local/bin/zot serve /etc/zot/config.json
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now zot
```

**The Results**:
- RAM usage: 45MB (vs 2GB+ for Harbor)
- Startup time: <1 second (vs 3 minutes)
- Recovery: Just restart the service
- Offline operation: Works for days without HQ connectivity
- Deployment: Fully automated, no on-site IT needed

**The Architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Headquarters                              │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                 Harbor (Enterprise)                     │    │
│   │   • CI/CD pushes new images                            │    │
│   │   • Vulnerability scanning                              │    │
│   │   • RBAC, audit logs                                    │    │
│   └────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
   │  Warehouse 1  │   │  Warehouse 2  │   │  Warehouse N  │
   │               │   │               │   │               │
   │  ┌─────────┐  │   │  ┌─────────┐  │   │  ┌─────────┐  │
   │  │   Zot   │  │   │  │   Zot   │  │   │  │   Zot   │  │
   │  │ (proxy) │  │   │  │ (proxy) │  │   │  │ (proxy) │  │
   │  └────┬────┘  │   │  └────┬────┘  │   │  └────┬────┘  │
   │       │       │   │       │       │   │       │       │
   │       ▼       │   │       ▼       │   │       ▼       │
   │  ┌─────────┐  │   │  ┌─────────┐  │   │  ┌─────────┐  │
   │  │ Edge K8s│  │   │  │ Edge K8s│  │   │  │ Edge K8s│  │
   │  │ (k3s)   │  │   │  │ (k3s)   │  │   │  │ (k3s)   │  │
   │  └─────────┘  │   │  └─────────┘  │   │  └─────────┘  │
   └───────────────┘   └───────────────┘   └───────────────┘

Sync flow:
1. HQ Harbor has authoritative images
2. Edge Zot instances sync on schedule + on-demand
3. Local k3s pulls from local Zot
4. Internet outage? Local cache continues working
```

**The Lesson**: The right tool depends on the context. Zot's simplicity isn't a weakness—it's a feature.

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No TLS in production | Credentials transmitted in clear text | Always configure TLS for production |
| Storage on tmpfs | Data lost on restart | Use persistent storage |
| No garbage collection | Storage grows forever | Enable `gc` in config |
| onDemand without limits | Cache grows unbounded | Combine with retention policies |
| No backup strategy | Data loss on failure | Backup storage directory regularly |
| Single sync URL | Single point of failure | Configure multiple upstream URLs |
| Ignoring scrub results | Silent data corruption | Monitor scrub extension output |
| No access control | Anyone can push/delete | Configure authentication and policies |

## Quiz

Test your understanding of Zot:

<details>
<summary>1. What makes Zot different from Harbor architecturally?</summary>

**Answer**: Zot is a single binary with no external dependencies (no PostgreSQL, no Redis), while Harbor consists of 8+ components requiring a database and cache. Zot was built from scratch for OCI specification; Harbor evolved from Docker Registry. Zot uses ~50MB RAM minimum; Harbor needs 2GB+.
</details>

<details>
<summary>2. How does Zot's on-demand sync work?</summary>

**Answer**: When configured with `onDemand: true`, Zot acts as a pull-through cache. When a client requests an image that doesn't exist locally, Zot fetches it from the upstream registry, stores it locally, and serves it. Subsequent requests are served from local cache without upstream contact.
</details>

<details>
<summary>3. What types of OCI artifacts can Zot store?</summary>

**Answer**: Zot stores any OCI-compliant artifact: container images, Helm charts, Cosign signatures, SBOMs (SPDX/CycloneDX), attestations, and any custom artifact types. They're all stored as manifests + blobs using content-addressable storage.
</details>

<details>
<summary>4. How does Zot's subPaths feature work?</summary>

**Answer**: subPaths let you route different repository prefixes to different storage backends. For example, `/production/*` could go to fast SSD storage while `/cache/*` goes to cheaper HDD storage. This enables tiered storage within a single Zot instance.
</details>

<details>
<summary>5. What's the purpose of the scrub extension?</summary>

**Answer**: The scrub extension periodically verifies storage integrity by checking that all blobs match their content-addressed hashes. It detects bit rot, incomplete uploads, or filesystem corruption before they cause problems during image pulls.
</details>

<details>
<summary>6. How do you configure per-repository access control in Zot?</summary>

**Answer**: Use the `accessControl.repositories` configuration with glob patterns. For each pattern, define policies mapping users/groups to allowed actions (read, create, update, delete). Patterns are matched in order; first match wins. Use `**` for catch-all.
</details>

<details>
<summary>7. Why might you choose Zot over Harbor?</summary>

**Answer**: Choose Zot when: (1) Resources are constrained (edge/IoT), (2) Simplicity is paramount, (3) No database dependency desired, (4) Pure OCI compliance needed, (5) Quick startup required, (6) Operations staff is limited. Choose Harbor when enterprise features (RBAC, replication UI, project quotas) are required.
</details>

<details>
<summary>8. How does Zot's deduplication work?</summary>

**Answer**: When `dedupe: true`, identical blobs (layers) are stored only once regardless of which repositories reference them. Zot uses hard links or reflinks (depending on filesystem) to share storage. This is especially effective for base images shared across many repositories.
</details>

## Hands-On Exercise: Deploy Zot as a Proxy Cache

### Objective
Deploy Zot as a caching proxy for DockerHub, demonstrating bandwidth savings and offline capability.

### Environment Setup

```bash
# Create kind cluster
kind create cluster --name zot-lab

# Create namespace
kubectl create namespace zot
```

### Step 1: Deploy Zot with Proxy Cache

```bash
# Create ConfigMap
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: zot-config
  namespace: zot
data:
  config.json: |
    {
      "distSpecVersion": "1.1.0",
      "storage": {
        "rootDirectory": "/var/lib/zot",
        "gc": true,
        "gcDelay": "1h",
        "gcInterval": "6h",
        "dedupe": true
      },
      "http": {
        "address": "0.0.0.0",
        "port": "5000"
      },
      "log": {
        "level": "info"
      },
      "extensions": {
        "sync": {
          "enable": true,
          "registries": [
            {
              "urls": ["https://registry-1.docker.io"],
              "onDemand": true,
              "maxRetries": 3,
              "retryDelay": "5m",
              "content": [
                {
                  "prefix": "library/**"
                }
              ]
            },
            {
              "urls": ["https://gcr.io"],
              "onDemand": true,
              "content": [
                {
                  "prefix": "**"
                }
              ]
            }
          ]
        },
        "metrics": {
          "enable": true,
          "prometheus": {
            "path": "/metrics"
          }
        },
        "search": {
          "enable": true
        }
      }
    }
EOF

# Create Deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zot
  namespace: zot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zot
  template:
    metadata:
      labels:
        app: zot
    spec:
      containers:
      - name: zot
        image: ghcr.io/project-zot/zot-linux-amd64:v2.0.1
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: config
          mountPath: /etc/zot
        - name: data
          mountPath: /var/lib/zot
        args: ["serve", "/etc/zot/config.json"]
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: config
        configMap:
          name: zot-config
      - name: data
        emptyDir: {}
EOF

# Create Service
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: zot
  namespace: zot
spec:
  selector:
    app: zot
  ports:
  - port: 5000
    targetPort: 5000
EOF

# Wait for deployment
kubectl -n zot rollout status deployment/zot
```

### Step 2: Test Proxy Cache

```bash
# Port-forward to Zot
kubectl -n zot port-forward svc/zot 5000:5000 &
sleep 2

# Verify Zot is running
curl -s http://localhost:5000/v2/ | jq .

# Pull nginx through Zot (first pull - fetches from DockerHub)
echo "First pull (from DockerHub)..."
time docker pull localhost:5000/library/nginx:alpine

# Check what's cached
curl -s http://localhost:5000/v2/_catalog | jq .

# Pull again (from cache - should be instant)
echo "Second pull (from cache)..."
docker rmi localhost:5000/library/nginx:alpine
time docker pull localhost:5000/library/nginx:alpine

# Pull another image
docker pull localhost:5000/library/alpine:3.19

# List all cached images
curl -s http://localhost:5000/v2/_catalog | jq .
```

### Step 3: Configure Kubernetes to Use Zot

```bash
# Deploy a pod using the cached image
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx-test
  namespace: default
spec:
  containers:
  - name: nginx
    # Use Zot's in-cluster DNS name
    image: zot.zot.svc.cluster.local:5000/library/nginx:alpine
    ports:
    - containerPort: 80
EOF

# Check pod status
kubectl get pod nginx-test

# View pod events (should show pull from Zot)
kubectl describe pod nginx-test | grep -A5 "Events:"
```

### Step 4: Monitor Cache Usage

```bash
# Get Prometheus metrics
curl -s http://localhost:5000/metrics | grep -E "^zot_"

# Key metrics:
# zot_http_requests_total - Total HTTP requests
# zot_repo_downloads_total - Image downloads
# zot_repo_uploads_total - Image uploads
# zot_storage_bytes - Storage used

# Use the search API to explore
curl -s "http://localhost:5000/v2/_zot/ext/search?query=%7BImageList%7BName%20Tags%7D%7D" | jq .
```

### Step 5: Test Offline Capability

```bash
# Simulate network failure to DockerHub
# (In real scenario, this would be firewall rule)

# Try pulling a cached image - should work
docker pull localhost:5000/library/nginx:alpine

# The image is served from local cache even if DockerHub is unreachable
```

### Success Criteria

- [ ] Zot deployed and running in Kubernetes
- [ ] First image pull fetches from DockerHub
- [ ] Subsequent pulls served from local cache (faster)
- [ ] Multiple images cached successfully
- [ ] Pod in Kubernetes pulls from Zot
- [ ] Metrics available on `/metrics`

### Cleanup

```bash
# Kill port-forward
pkill -f "port-forward.*zot"

# Delete cluster
kind delete cluster --name zot-lab
```

## Key Takeaways

1. **Minimalism is a feature**: Single binary, no database, <50MB RAM
2. **OCI-native**: Built for the OCI spec, not Docker legacy
3. **Perfect for edge**: Runs on Raspberry Pi to cloud VMs
4. **Proxy cache superpower**: Cache DockerHub, GHCR, any registry
5. **All OCI artifacts**: Images, Helm charts, signatures, SBOMs
6. **Easy operations**: One process to manage, one config file
7. **Fast recovery**: Restart and it's back—no database migrations
8. **Complement to Harbor**: Use Zot at edge, Harbor at core
9. **Built-in scanning**: Trivy integration for CVE detection
10. **Production-ready**: Used by enterprises at scale

## Next Module

Continue to [Module 13.3: Dragonfly](../module-13.3-dragonfly/) — P2P image distribution for massive-scale deployments.

---

*"The best tool is the simplest one that solves your problem. For many registry use cases, that's Zot."*
