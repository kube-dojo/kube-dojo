---
title: "Module 2.9: GCP Secret Manager"
slug: cloud/gcp-essentials/module-2.9-secret-manager
sidebar:
  order: 10
---
**Complexity**: [MEDIUM] | **Time to Complete**: 1.5h | **Prerequisites**: Module 2.1 (IAM & Resource Hierarchy)

## Why This Module Matters

In January 2023, a code review at a mid-sized SaaS company revealed that database credentials for their production PostgreSQL instance had been hardcoded in a Kubernetes ConfigMap for over two years. The credentials had been committed to Git, synced to the cluster via ArgoCD, and were visible in plaintext to anyone with `kubectl get configmap` access---which included every developer in the company. When the security team investigated, they found that the same database password had been shared via Slack three times, copied into a local `.env` file on at least 12 developer laptops, and had never been rotated. A former employee who left the company 8 months ago still had a working copy. The company spent six weeks conducting a full credential rotation across 42 services, updating and redeploying each one. During the rotation, three production outages occurred because services failed to pick up the new credentials.

This story is painfully common. Secrets---database passwords, API keys, TLS certificates, encryption keys, OAuth tokens---are the most sensitive data in any organization, yet they are routinely handled with the same care as regular configuration data. They end up in environment variables, ConfigMaps, CI/CD pipelines, and chat messages. Secret Manager exists to solve this problem by providing a **centralized, versioned, IAM-controlled store for all sensitive data**. Secrets are encrypted at rest and in transit, access is audited through Cloud Audit Logs, and rotation can be automated.

In this module, you will learn how to create and manage secrets, understand the versioning model, configure fine-grained IAM access, integrate secrets with Cloud Run and Compute Engine, and design a rotation strategy that does not cause outages.

---

## Secret Manager Fundamentals

### Secrets and Versions

Secret Manager uses a two-level model: **Secrets** and **Versions**.

```text
  ┌────────────────────────────────────────────────┐
  │  Secret: prod-database-password                 │
  │  Project: my-project                            │
  │  Replication: automatic                         │
  │                                                  │
  │  Versions:                                       │
  │  ┌──────────────────────────────────────────┐   │
  │  │ Version 3 (latest, ENABLED)               │   │
  │  │ Created: 2024-01-15                       │   │
  │  │ Data: "n3wS3cur3P@ss!"                    │   │
  │  └──────────────────────────────────────────┘   │
  │  ┌──────────────────────────────────────────┐   │
  │  │ Version 2 (ENABLED)                       │   │
  │  │ Created: 2023-07-20                       │   │
  │  │ Data: "0ldP@ssw0rd123"                    │   │
  │  └──────────────────────────────────────────┘   │
  │  ┌──────────────────────────────────────────┐   │
  │  │ Version 1 (DISABLED)                      │   │
  │  │ Created: 2023-01-10                       │   │
  │  │ Data: "initialP@ss"                       │   │
  │  └──────────────────────────────────────────┘   │
  └────────────────────────────────────────────────┘
```

**Secret**: A named container that holds versions. The secret itself has IAM policies, labels, and replication settings, but does not contain the actual sensitive data.

**Version**: The actual secret data (up to 64 KiB per version). Each version is immutable---once created, the data cannot be changed. To update a secret, you add a new version. Versions can be in one of three states:

| State | Description | Accessible | Billed |
| :--- | :--- | :--- | :--- |
| **ENABLED** | Active, can be accessed | Yes | Yes |
| **DISABLED** | Temporarily inaccessible | No (returns error) | Yes |
| **DESTROYED** | Permanently deleted | No (irrecoverable) | No |

---

## Creating and Managing Secrets

### Creating Secrets

```bash
# Enable the Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create a secret (empty, no version yet)
gcloud secrets create prod-db-password \
  --replication-policy="automatic" \
  --labels="env=prod,service=database"

# Create a secret and add the first version in one command
echo -n "s3cur3P@ssw0rd!" | gcloud secrets create api-key \
  --replication-policy="automatic" \
  --data-file=-

# Create a secret from a file (e.g., a TLS certificate)
gcloud secrets create tls-cert \
  --replication-policy="automatic" \
  --data-file=./server.crt

# List all secrets
gcloud secrets list --format="table(name, createTime, labels)"
```

**Important**: The `-n` flag in `echo -n` prevents a trailing newline from being included in the secret data. A common bug is storing a password with a trailing newline, which causes authentication failures.

### Adding and Accessing Versions

```bash
# Add a new version to an existing secret
echo -n "n3wP@ssw0rd2024!" | gcloud secrets versions add prod-db-password \
  --data-file=-

# Access the latest version
gcloud secrets versions access latest --secret=prod-db-password

# Access a specific version by number
gcloud secrets versions access 2 --secret=prod-db-password

# List all versions of a secret
gcloud secrets versions list prod-db-password \
  --format="table(name, state, createTime)"
```

### Disabling and Destroying Versions

```bash
# Disable a version (makes it inaccessible but recoverable)
gcloud secrets versions disable 1 --secret=prod-db-password

# Re-enable a disabled version
gcloud secrets versions enable 1 --secret=prod-db-password

# Destroy a version (PERMANENT, irrecoverable)
gcloud secrets versions destroy 1 --secret=prod-db-password

# Delete an entire secret (destroys all versions)
gcloud secrets delete prod-db-password --quiet
```

### Replication Policies

| Policy | Description | Use Case |
| :--- | :--- | :--- |
| **Automatic** | GCP manages replication across regions | Most use cases (recommended) |
| **User-managed** | You specify which regions store the secret | Data residency compliance |

```bash
# Automatic replication (Google chooses regions)
gcloud secrets create my-secret --replication-policy="automatic"

# User-managed replication (specific regions)
gcloud secrets create eu-only-secret \
  --replication-policy="user-managed" \
  --locations="europe-west1,europe-west4"
```

---

## IAM Access Control

Secret Manager supports fine-grained IAM at both the project level and the individual secret level.

### Secret Manager Roles

| Role | Permissions | Typical User |
| :--- | :--- | :--- |
| `roles/secretmanager.viewer` | List secrets and metadata (NOT access data) | Auditors, security reviewers |
| `roles/secretmanager.secretAccessor` | Access secret version data | Applications, Cloud Run services |
| `roles/secretmanager.secretVersionAdder` | Add new versions (cannot read existing) | Rotation scripts |
| `roles/secretmanager.secretVersionManager` | Add, disable, enable, destroy versions | Operations team |
| `roles/secretmanager.admin` | Full control over secrets | Platform engineers |

```bash
# Grant a service account access to read a specific secret
gcloud secrets add-iam-policy-binding prod-db-password \
  --member="serviceAccount:my-api@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Grant a rotation service account write-only access
gcloud secrets add-iam-policy-binding prod-db-password \
  --member="serviceAccount:secret-rotator@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretVersionAdder"

# View IAM policy for a secret
gcloud secrets get-iam-policy prod-db-password

# Grant access to all secrets in a project (less recommended)
gcloud projects add-iam-binding my-project \
  --member="serviceAccount:my-api@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### IAM Conditions for Time-Based Access

```bash
# Grant temporary access (expires after 24 hours)
gcloud secrets add-iam-policy-binding prod-db-password \
  --member="user:oncall@example.com" \
  --role="roles/secretmanager.secretAccessor" \
  --condition="expression=request.time < timestamp('2024-01-16T00:00:00Z'),title=temporary-access,description=On-call access for 24 hours"
```

---

## Integrating with Cloud Run

Cloud Run has native integration with Secret Manager. You can mount secrets as environment variables or files.

### As Environment Variables

```bash
# Deploy Cloud Run with a secret as an environment variable
gcloud run deploy my-api \
  --image=us-central1-docker.pkg.dev/my-project/docker-repo/my-api:v1.0.0 \
  --region=us-central1 \
  --set-secrets="DB_PASSWORD=prod-db-password:latest"

# Multiple secrets
gcloud run deploy my-api \
  --image=us-central1-docker.pkg.dev/my-project/docker-repo/my-api:v1.0.0 \
  --region=us-central1 \
  --set-secrets="DB_PASSWORD=prod-db-password:latest,API_KEY=api-key:latest,TLS_CERT=tls-cert:3"

# Pin to a specific version (recommended for production)
gcloud run deploy my-api \
  --region=us-central1 \
  --set-secrets="DB_PASSWORD=prod-db-password:3"
```

### As Mounted Files

```bash
# Mount a secret as a file (useful for certificates, key files)
gcloud run deploy my-api \
  --image=us-central1-docker.pkg.dev/my-project/docker-repo/my-api:v1.0.0 \
  --region=us-central1 \
  --set-secrets="/app/secrets/db-password=prod-db-password:latest"

# In the container, read the file:
# with open("/app/secrets/db-password", "r") as f:
#     password = f.read()
```

### Latest vs Pinned Versions

| Approach | Syntax | Behavior | Best For |
| :--- | :--- | :--- | :--- |
| **Latest** | `secret:latest` | Always gets newest version | Dev/staging environments |
| **Pinned** | `secret:3` | Always gets version 3 | Production (deterministic) |

**Important**: When using `latest`, Cloud Run resolves the version at **deployment time**, not at request time. If you add a new secret version, Cloud Run will not automatically pick it up. You must redeploy the service to get the new version. This is a safety feature that prevents untested secrets from being used in production.

---

## Integrating with Compute Engine

VMs access secrets through the Secret Manager API using the client libraries or `gcloud`.

### From a Startup Script

```bash
# Create a VM that reads a secret during startup
gcloud compute instances create app-server \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --service-account=my-api@my-project.iam.gserviceaccount.com \
  --scopes=cloud-platform \
  --metadata=startup-script='#!/bin/bash
    # Install gcloud if not present (usually pre-installed on GCP images)
    # Fetch the database password
    DB_PASSWORD=$(gcloud secrets versions access latest --secret=prod-db-password)

    # Write to a config file (with restricted permissions)
    echo "DATABASE_PASSWORD=$DB_PASSWORD" > /etc/app/config.env
    chmod 600 /etc/app/config.env

    # Start the application
    systemctl start myapp'
```

### From Application Code

```python
# Python: Access a secret programmatically
from google.cloud import secretmanager

def get_secret(project_id, secret_id, version_id="latest"):
    """Access a secret version from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})

    return response.payload.data.decode("UTF-8")

# Usage
db_password = get_secret("my-project", "prod-db-password")
api_key = get_secret("my-project", "api-key", version_id="3")
```

```go
// Go: Access a secret programmatically
package main

import (
    "context"
    "fmt"
    secretmanager "cloud.google.com/go/secretmanager/apiv1"
    secretmanagerpb "cloud.google.com/go/secretmanager/apiv1/secretmanagerpb"
)

func getSecret(projectID, secretID, versionID string) (string, error) {
    ctx := context.Background()
    client, err := secretmanager.NewClient(ctx)
    if err != nil {
        return "", fmt.Errorf("failed to create client: %w", err)
    }
    defer client.Close()

    name := fmt.Sprintf("projects/%s/secrets/%s/versions/%s",
        projectID, secretID, versionID)

    result, err := client.AccessSecretVersion(ctx,
        &secretmanagerpb.AccessSecretVersionRequest{Name: name})
    if err != nil {
        return "", fmt.Errorf("failed to access secret: %w", err)
    }

    return string(result.Payload.Data), nil
}
```

---

## Integrating with Cloud Functions

```bash
# Deploy a Cloud Function with secret environment variables
gcloud functions deploy my-function \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=handler \
  --trigger-http \
  --set-secrets="DB_PASSWORD=prod-db-password:latest"

# Deploy with a secret mounted as a file
gcloud functions deploy my-function \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=handler \
  --trigger-http \
  --set-secrets="/app/certs/tls.crt=tls-cert:latest"
```

---

## Secret Rotation

### Manual Rotation Pattern

```bash
# Step 1: Generate a new password
NEW_PASSWORD=$(openssl rand -base64 24)

# Step 2: Add the new version to Secret Manager
echo -n "$NEW_PASSWORD" | gcloud secrets versions add prod-db-password --data-file=-

# Step 3: Update the database with the new password
# (this step depends on your database)

# Step 4: Redeploy services to pick up the new version
gcloud run services update my-api --region=us-central1 \
  --set-secrets="DB_PASSWORD=prod-db-password:latest"

# Step 5: Disable the old version (after confirming new one works)
gcloud secrets versions disable 2 --secret=prod-db-password

# Step 6: Destroy the old version (after grace period)
# Wait 7 days, then:
gcloud secrets versions destroy 2 --secret=prod-db-password
```

### Automated Rotation with Cloud Functions

```text
  ┌────────────────┐     Triggers      ┌────────────────┐
  │  Cloud Scheduler│ ─────────────────>│  Cloud Function │
  │  (every 90 days)│                    │  (rotate-secret)│
  └────────────────┘                    └───────┬────────┘
                                                │
                                    1. Generate new credential
                                    2. Update the service (DB, API)
                                    3. Add new version to Secret Manager
                                    4. Disable old version
                                                │
                                        ┌───────▼────────┐
                                        │ Secret Manager  │
                                        │ (new version)   │
                                        └────────────────┘
```

```python
# rotation_function/main.py
import functions_framework
import secrets
import string
from google.cloud import secretmanager

@functions_framework.http
def rotate_secret(request):
    """Rotate a database password."""
    client = secretmanager.SecretManagerServiceClient()

    project_id = "my-project"
    secret_id = "prod-db-password"

    # Generate a new secure password
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    new_password = ''.join(secrets.choice(alphabet) for _ in range(32))

    # Add the new version
    parent = f"projects/{project_id}/secrets/{secret_id}"
    response = client.add_secret_version(
        request={
            "parent": parent,
            "payload": {"data": new_password.encode("UTF-8")}
        }
    )

    new_version = response.name.split("/")[-1]
    print(f"Created new version: {new_version}")

    # TODO: Update the actual database password here
    # update_database_password(new_password)

    # Disable the previous version (version N-1)
    prev_version = str(int(new_version) - 1)
    if int(prev_version) >= 1:
        version_name = f"{parent}/versions/{prev_version}"
        client.disable_secret_version(
            request={"name": version_name}
        )
        print(f"Disabled version: {prev_version}")

    return f"Rotated to version {new_version}", 200
```

```bash
# Deploy the rotation function
gcloud functions deploy rotate-db-password \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=./rotation_function \
  --entry-point=rotate_secret \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=secret-rotator@my-project.iam.gserviceaccount.com

# Schedule rotation every 90 days
gcloud scheduler jobs create http rotate-db-password-schedule \
  --location=us-central1 \
  --schedule="0 3 1 */3 *" \
  --uri="$(gcloud functions describe rotate-db-password --gen2 --region=us-central1 --format='value(serviceConfig.uri)')" \
  --http-method=POST \
  --oidc-service-account-email=secret-rotator@my-project.iam.gserviceaccount.com
```

---

## Audit Logging

Every access to Secret Manager is logged in Cloud Audit Logs.

```bash
# Query who accessed a secret
gcloud logging read '
  resource.type="secretmanager.googleapis.com/Secret"
  AND protoPayload.methodName="google.cloud.secretmanager.v1.SecretManagerService.AccessSecretVersion"
  AND protoPayload.resourceName:"secrets/prod-db-password"
' --limit=20 --format="table(timestamp, protoPayload.authenticationInfo.principalEmail, protoPayload.resourceName)"

# Query who created or modified secrets
gcloud logging read '
  resource.type="secretmanager.googleapis.com/Secret"
  AND protoPayload.methodName:"AddSecretVersion"
' --limit=10 --format=json
```

---

## Did You Know?

1. **Secret Manager encrypts all secret data with Google-managed AES-256 encryption keys** by default. You can also use Customer-Managed Encryption Keys (CMEK) via Cloud KMS for additional control. With CMEK, you control the encryption key lifecycle---you can rotate it, disable it (making all secrets inaccessible), or even destroy it (permanently losing access to the encrypted secrets).

2. **The maximum size of a single secret version is 64 KiB**. This is large enough for most secrets (passwords, API keys, certificates) but not for large data blobs. If you need to store larger sensitive data, encrypt it with a Cloud KMS key and store the encrypted data in Cloud Storage; store only the KMS key reference in Secret Manager.

3. **Secret Manager supports automatic replication to 6+ GCP regions** with the "automatic" replication policy. This means your secrets are available even if an entire region goes down. The service's SLA is 99.95%, and Google has maintained 100% availability since the service launched in 2020.

4. **You can set expiration dates on secrets**. When a secret expires, it is automatically deleted along with all its versions. This is useful for temporary credentials, short-lived API keys, or access tokens that should not persist beyond a known timeframe. Set it with `--expire-time` or `--ttl` during creation.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Hardcoding secrets in code or ConfigMaps | "Just for now" during development | Always use Secret Manager, even in dev environments |
| Granting `secretmanager.admin` to applications | Quick fix for permission errors | Applications only need `secretmanager.secretAccessor` on specific secrets |
| Using `latest` in production without redeployment | Expecting automatic pickup of new versions | Pin to a specific version in production; redeploy when rotating |
| Including a trailing newline in the secret | Using `echo` without `-n` | Always use `echo -n` or `printf` when piping to `--data-file=-` |
| Not auditing secret access | Not knowing audit logging exists | Enable Data Access audit logs and monitor for unexpected access |
| Storing secrets in environment variables in CI/CD | CI/CD platform variables seem equivalent | Use Workload Identity Federation + Secret Manager in CI/CD pipelines |
| Never rotating secrets | Rotation seems complex and risky | Implement automated rotation; start with a 90-day cadence |
| Destroying versions too quickly after rotation | Wanting to clean up immediately | Keep old versions enabled for 24-48 hours as a rollback safety net |

---

## Quiz

<details>
<summary>1. What is the difference between a Secret and a Secret Version in Secret Manager?</summary>

A **Secret** is a named container (like `prod-db-password`) that holds metadata, IAM policies, labels, and replication settings. It does not contain the actual sensitive data. A **Secret Version** is the actual secret data (the password, API key, or certificate content). Versions are immutable---once created, their data cannot be changed. To update a secret, you add a new version. Each version has a state (ENABLED, DISABLED, or DESTROYED) and a version number. You can access a specific version by number or use the `latest` alias to get the most recent enabled version.
</details>

<details>
<summary>2. A Cloud Run service is deployed with --set-secrets="DB_PASSWORD=prod-db-password:latest". You add a new version to the secret. Does the running service automatically use the new version?</summary>

**No.** When using `latest`, Cloud Run resolves the version at **deployment time**, not at runtime. The service continues using the version that was "latest" when it was last deployed. To pick up the new secret version, you must **redeploy** the service (or run `gcloud run services update` with the same `--set-secrets` flag). This is a deliberate safety feature that prevents untested secret changes from automatically propagating to production services. For this reason, it is recommended to pin to a specific version number in production and explicitly redeploy when rotating secrets.
</details>

<details>
<summary>3. What is the difference between disabling and destroying a secret version?</summary>

**Disabling** a version makes it temporarily inaccessible---any attempt to access it returns an error. However, the version still exists and can be **re-enabled** at any time. The secret data is preserved. You are still billed for the storage of a disabled version. **Destroying** a version permanently deletes the secret data. It is irrecoverable---there is no undo. The version number still appears in listings (showing state DESTROYED), but the data is gone. You are no longer billed for destroyed versions. Use disable as a safe first step during rotation; destroy only after you are confident the old version is no longer needed.
</details>

<details>
<summary>4. Why should you use echo -n instead of echo when piping a secret value to Secret Manager?</summary>

The `echo` command appends a trailing newline character (`\n`) to its output by default. If you pipe `echo "mypassword"` to Secret Manager, the stored secret is actually `mypassword\n` (with a newline). When your application reads this secret and uses it as a database password, it sends `mypassword\n` to the database, which does not match the actual password `mypassword`. This causes authentication failures that are extremely difficult to debug because the secret *looks* correct when displayed. Using `echo -n` suppresses the trailing newline, ensuring the secret data is exactly what you intend.
</details>

<details>
<summary>5. How would you implement a secret rotation strategy that avoids downtime?</summary>

Use a **dual-version strategy**: (1) Generate a new credential and add it as a new version in Secret Manager. (2) Update the backend service (database, API provider) to accept **both** the old and new credentials simultaneously. (3) Redeploy your application services to use the new version. (4) Verify that all services are successfully using the new credential. (5) Disable the old version in Secret Manager (but do not destroy it yet). (6) After a grace period (24-48 hours), update the backend to only accept the new credential. (7) Destroy the old version after the grace period. The key is that the backend accepts both credentials during the transition window, so there is no moment where a credential mismatch causes downtime.
</details>

<details>
<summary>6. What IAM role should a Cloud Run service have to read secrets, and where should the binding be applied?</summary>

The Cloud Run service account needs the `roles/secretmanager.secretAccessor` role. This should be granted **at the individual secret level**, not at the project level. Granting it at the project level would allow the service to read every secret in the project, violating the principle of least privilege. Use `gcloud secrets add-iam-policy-binding SECRET_NAME --member="serviceAccount:SA_EMAIL" --role="roles/secretmanager.secretAccessor"` for each secret the service needs. If the service needs to read 3 secrets, create 3 IAM bindings. This ensures that if the service is compromised, the attacker can only access the specific secrets the service was authorized to use.
</details>

---

## Hands-On Exercise: Secrets Lifecycle with Cloud Run Integration

### Objective

Create secrets, manage versions, integrate with Cloud Run, and simulate a secret rotation.

### Prerequisites

- `gcloud` CLI installed and authenticated
- A GCP project with billing enabled

### Tasks

**Task 1: Create Secrets**

<details>
<summary>Solution</summary>

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create a database password secret
echo -n "initialP@ssw0rd2024" | gcloud secrets create lab-db-password \
  --replication-policy="automatic" \
  --labels="env=lab,service=database" \
  --data-file=-

# Create an API key secret
echo -n "sk_live_abc123def456ghi789" | gcloud secrets create lab-api-key \
  --replication-policy="automatic" \
  --labels="env=lab,service=external-api" \
  --data-file=-

# Verify secrets were created
gcloud secrets list --filter="labels.env=lab" \
  --format="table(name, createTime, labels)"

# Access the secrets to verify content
echo "DB Password: $(gcloud secrets versions access latest --secret=lab-db-password)"
echo "API Key: $(gcloud secrets versions access latest --secret=lab-api-key)"
```
</details>

**Task 2: Add Multiple Versions and Manage State**

<details>
<summary>Solution</summary>

```bash
# Add version 2 to the database password
echo -n "r0tatedP@ss2024v2" | gcloud secrets versions add lab-db-password --data-file=-

# Add version 3
echo -n "r0tatedP@ss2024v3" | gcloud secrets versions add lab-db-password --data-file=-

# List all versions
gcloud secrets versions list lab-db-password \
  --format="table(name, state, createTime)"

# Access specific versions
echo "Version 1: $(gcloud secrets versions access 1 --secret=lab-db-password)"
echo "Version 2: $(gcloud secrets versions access 2 --secret=lab-db-password)"
echo "Version 3 (latest): $(gcloud secrets versions access latest --secret=lab-db-password)"

# Disable version 1 (simulate post-rotation)
gcloud secrets versions disable 1 --secret=lab-db-password

# Verify version 1 is disabled
gcloud secrets versions access 1 --secret=lab-db-password 2>&1 || echo "Access denied (expected)"

# Re-enable version 1 (test recovery)
gcloud secrets versions enable 1 --secret=lab-db-password
echo "Re-enabled: $(gcloud secrets versions access 1 --secret=lab-db-password)"
```
</details>

**Task 3: Configure IAM for a Service Account**

<details>
<summary>Solution</summary>

```bash
# Create a service account for the application
gcloud iam service-accounts create lab-app-sa \
  --display-name="Lab Application SA"

export APP_SA="lab-app-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant access to ONLY the db-password secret (not all secrets)
gcloud secrets add-iam-policy-binding lab-db-password \
  --member="serviceAccount:$APP_SA" \
  --role="roles/secretmanager.secretAccessor"

# Verify the binding
gcloud secrets get-iam-policy lab-db-password \
  --format="table(bindings.role, bindings.members)"

# The SA should NOT be able to access lab-api-key
# (no binding exists for that secret)
```
</details>

**Task 4: Deploy a Cloud Run Service with Secrets**

<details>
<summary>Solution</summary>

```bash
# Create a simple app that displays (masked) secret info
mkdir -p /tmp/secret-lab && cd /tmp/secret-lab

cat > main.py << 'PYEOF'
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    db_password = os.environ.get("DB_PASSWORD", "NOT_SET")
    api_key = os.environ.get("API_KEY", "NOT_SET")

    return jsonify({
        "db_password_set": db_password != "NOT_SET",
        "db_password_preview": db_password[:4] + "****" if len(db_password) > 4 else "****",
        "api_key_set": api_key != "NOT_SET",
        "api_key_preview": api_key[:6] + "****" if len(api_key) > 6 else "****"
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
PYEOF

cat > requirements.txt << 'EOF'
flask>=3.0.0
gunicorn>=21.2.0
EOF

cat > Dockerfile << 'DEOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
DEOF

# Grant the service account access to both secrets
gcloud secrets add-iam-policy-binding lab-api-key \
  --member="serviceAccount:$APP_SA" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with secrets
gcloud run deploy secret-lab-app \
  --source=. \
  --region=$REGION \
  --allow-unauthenticated \
  --service-account=$APP_SA \
  --set-secrets="DB_PASSWORD=lab-db-password:latest,API_KEY=lab-api-key:latest" \
  --memory=256Mi

# Get the URL and test
SERVICE_URL=$(gcloud run services describe secret-lab-app \
  --region=$REGION --format="value(status.url)")
curl -s $SERVICE_URL | python3 -m json.tool
```
</details>

**Task 5: Simulate Secret Rotation**

<details>
<summary>Solution</summary>

```bash
# Add a new version (simulating rotation)
echo -n "brand-N3w-Rot@ted-P@ss!" | gcloud secrets versions add lab-db-password --data-file=-

# The running service still uses the old version (resolved at deploy time)
echo "=== Before redeployment (still old version) ==="
curl -s $SERVICE_URL | python3 -m json.tool

# Redeploy to pick up the new version
gcloud run services update secret-lab-app \
  --region=$REGION \
  --set-secrets="DB_PASSWORD=lab-db-password:latest,API_KEY=lab-api-key:latest"

# Wait for deployment
sleep 10

echo "=== After redeployment (new version) ==="
curl -s $SERVICE_URL | python3 -m json.tool

# Disable the old version
gcloud secrets versions disable 3 --secret=lab-db-password

# List versions to see the state
gcloud secrets versions list lab-db-password \
  --format="table(name, state, createTime)"
```
</details>

**Task 6: Clean Up**

<details>
<summary>Solution</summary>

```bash
# Delete Cloud Run service
gcloud run services delete secret-lab-app --region=$REGION --quiet

# Delete secrets
gcloud secrets delete lab-db-password --quiet
gcloud secrets delete lab-api-key --quiet

# Delete service account
gcloud iam service-accounts delete $APP_SA --quiet

# Clean up local files
rm -rf /tmp/secret-lab

echo "Cleanup complete."
```
</details>

### Success Criteria

- [ ] Secrets created with correct data (no trailing newlines)
- [ ] Multiple versions added and version states managed
- [ ] Per-secret IAM configured for the service account
- [ ] Cloud Run deployed with secrets as environment variables
- [ ] Secret rotation simulated (new version, redeploy, disable old)
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 2.10: Cloud Operations (Monitoring & Logging)](module-2.10-operations/)** --- Learn Cloud Logging (log routers, sinks, and log-based metrics), Cloud Monitoring (dashboards, PromQL/MQL, alerting), and uptime checks to keep your services observable and reliable.
