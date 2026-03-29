---
title: "Module 6.3: GKE Workload Identity and Security"
slug: cloud/gke-deep-dive/module-6.3-gke-identity
sidebar:
  order: 4
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: Module 6.1 (GKE Architecture)

## Why This Module Matters

In January 2024, a logistics company discovered that every pod in their GKE cluster had read/write access to every Cloud Storage bucket and every Pub/Sub topic in their project. A junior developer had deployed a debug pod that scraped all Pub/Sub messages from the production order queue and wrote them to a personal GCS bucket for "testing." The data included customer addresses, phone numbers, and delivery instructions for 2.1 million orders. The root cause was depressingly common: when the cluster was created, the default node service account was granted the `Editor` role on the project, and every pod on the cluster inherited that identity. No one had configured Workload Identity. The remediation cost $890,000 in legal fees, notification costs, and a GDPR fine. The fix---configuring Workload Identity and scoping IAM permissions per pod---took two days.

This incident illustrates the most dangerous default in GKE: without Workload Identity, every pod on a node shares the same GCP identity. A compromised pod, a rogue container, or even a developer with kubectl access can impersonate the node's service account and access any GCP resource that account can reach. Workload Identity solves this by binding individual Kubernetes ServiceAccounts to individual GCP service accounts, giving each workload only the permissions it needs.

In this module, you will learn how Workload Identity Federation for GKE works, how to configure Binary Authorization to ensure only trusted container images run in your cluster, how Shielded and Confidential Nodes protect the node itself, and how to integrate Secret Manager with GKE. By the end, you will set up a pod that securely accesses Pub/Sub using Workload Identity and enforce a Binary Authorization policy that blocks unsigned images.

---

## The Problem: Node-Level Identity

Without Workload Identity, GKE pods access GCP services using the **node's service account**. Every VM (node) in a node pool runs with a GCP service account attached, and every pod on that node can access the metadata server to obtain OAuth tokens for that account.

```text
  Without Workload Identity:
  ┌─────────────────────────────────────────────────────┐
  │  Node (VM)                                          │
  │  Service Account: node-sa@project.iam               │
  │  Roles: Editor (or similar broad role)              │
  │                                                     │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
  │  │  App Pod  │  │  Debug   │  │  Rogue   │         │
  │  │          │  │  Pod     │  │  Pod     │         │
  │  │  Needs:  │  │  Needs:  │  │  Wants:  │         │
  │  │  GCS     │  │  Nothing │  │  EVERYTHING│        │
  │  │  read    │  │          │  │          │         │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
  │       │              │              │               │
  │       ▼              ▼              ▼               │
  │  ┌─────────────────────────────────────────┐       │
  │  │  Metadata Server (169.254.169.254)      │       │
  │  │  Returns: node-sa token (Editor access) │       │
  │  └─────────────────────────────────────────┘       │
  └─────────────────────────────────────────────────────┘

  ALL three pods get the SAME token with the SAME permissions.
```

This is a violation of the **principle of least privilege**. The app pod only needs GCS read access, but it gets Editor. The debug pod needs nothing, but it gets Editor. The rogue pod gets Editor too.

---

## Workload Identity Federation for GKE

Workload Identity Federation (WIF) for GKE maps Kubernetes ServiceAccounts to GCP IAM service accounts. Each pod gets credentials scoped to exactly the GCP resources it needs.

### How It Works

```text
  With Workload Identity:
  ┌─────────────────────────────────────────────────────┐
  │  Node (VM)                                          │
  │  Node SA: restricted-node-sa (minimal permissions)  │
  │                                                     │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
  │  │  App Pod  │  │  Debug   │  │  Batch   │         │
  │  │  KSA:     │  │  Pod     │  │  Pod     │         │
  │  │  app-sa   │  │  KSA:    │  │  KSA:    │         │
  │  │          │  │  default  │  │  batch-sa│         │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
  │       │              │              │               │
  │       ▼              ▼              ▼               │
  │  ┌───────────────────────────────────────────┐     │
  │  │  GKE Metadata Server (replaces default)   │     │
  │  │                                           │     │
  │  │  app-sa → gcs-reader@proj.iam             │     │
  │  │  default → (no GCP SA, access denied)     │     │
  │  │  batch-sa → pubsub-writer@proj.iam        │     │
  │  └───────────────────────────────────────────┘     │
  └─────────────────────────────────────────────────────┘

  Each pod gets ONLY its own GCP identity.
```

### Setting Up Workload Identity

```bash
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Step 1: Enable Workload Identity on the cluster (if not already)
# Best practice: enable at cluster creation with --workload-pool
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --workload-pool=$PROJECT_ID.svc.id.goog

# Step 2: Create a GCP service account for the workload
gcloud iam service-accounts create gcs-reader-sa \
  --display-name="GCS Reader for App Pod"

# Step 3: Grant the GCP SA only the permissions it needs
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:gcs-reader-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Step 4: Create a Kubernetes ServiceAccount
kubectl create serviceaccount app-sa --namespace=default

# Step 5: Bind the Kubernetes SA to the GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  gcs-reader-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/app-sa]"

# Step 6: Annotate the Kubernetes SA with the GCP SA email
kubectl annotate serviceaccount app-sa \
  --namespace=default \
  iam.gke.io/gcp-service-account=gcs-reader-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### Using Workload Identity in a Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gcs-reader
  namespace: default
spec:
  serviceAccountName: app-sa  # This is the key line
  containers:
  - name: reader
    image: google/cloud-sdk:slim
    command: ["sleep", "infinity"]
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
```

```bash
# Deploy and verify
kubectl apply -f gcs-reader-pod.yaml

# Exec into the pod and verify the identity
kubectl exec -it gcs-reader -- gcloud auth list
# Should show: gcs-reader-sa@PROJECT_ID.iam.gserviceaccount.com

# Test GCS access (should work)
kubectl exec -it gcs-reader -- gsutil ls gs://some-readable-bucket/

# Test Pub/Sub access (should be denied)
kubectl exec -it gcs-reader -- gcloud pubsub topics list
# Should fail with permission denied
```

### Fleet Workload Identity Federation (Cross-Project)

For multi-project setups, Fleet Workload Identity Federation allows pods in one project to access resources in another project without creating service accounts in every project.

```bash
# Register the cluster with a Fleet
gcloud container fleet memberships register my-cluster \
  --gke-cluster=$REGION/my-cluster \
  --enable-workload-identity

# Grant cross-project access using the Fleet identity
gcloud projects add-iam-policy-binding OTHER_PROJECT_ID \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]" \
  --role="roles/storage.objectViewer"
```

---

## Binary Authorization

Binary Authorization ensures that only trusted container images can be deployed to your GKE cluster. It works by requiring cryptographic attestations on images before they are allowed to run.

### How Binary Authorization Works

```text
  Developer pushes code
       │
       ▼
  Cloud Build builds image
       │
       ▼
  Image pushed to Artifact Registry
       │
       ▼
  Attestor signs the image digest ◄── Human review, vulnerability scan pass, etc.
       │
       ▼
  Developer creates Deployment
       │
       ▼
  GKE Admission Controller checks:
  ┌──────────────────────────────────────────┐
  │  1. Is Binary Authorization enabled?     │
  │  2. Does the image have a valid          │
  │     attestation from a trusted attestor? │
  │  3. Does the image match the policy?     │
  │                                          │
  │  YES → Allow pod to start               │
  │  NO  → Block pod, log violation          │
  └──────────────────────────────────────────┘
```

### Setting Up Binary Authorization

```bash
# Step 1: Enable Binary Authorization API
gcloud services enable binaryauthorization.googleapis.com \
  --project=$PROJECT_ID

# Step 2: Enable Binary Authorization on the cluster
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --binauthz-evaluation-mode=PROJECT_SINGLETON_POLICY_ENFORCE

# Step 3: View the default policy
gcloud container binauthz policy export

# Step 4: Create a policy that allows only Artifact Registry images
cat <<'EOF' > /tmp/binauthz-policy.yaml
admissionWhitelistPatterns:
- namePattern: gcr.io/google-containers/*
- namePattern: gcr.io/google-samples/*
- namePattern: us-docker.pkg.dev/google-samples/*
defaultAdmissionRule:
  enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
  evaluationMode: ALWAYS_DENY
globalPolicyEvaluationMode: ENABLE
clusterAdmissionRules:
  us-central1.my-cluster:
    enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
    evaluationMode: REQUIRE_ATTESTATION
    requireAttestationsBy:
    - projects/PROJECT_ID/attestors/build-attestor
EOF

# Step 5: Import the policy
gcloud container binauthz policy import /tmp/binauthz-policy.yaml
```

### Creating an Attestor

```bash
# Create a key ring and key for signing
gcloud kms keyrings create binauthz-keyring \
  --location=global

gcloud kms keys create attestor-key \
  --keyring=binauthz-keyring \
  --location=global \
  --purpose=asymmetric-signing \
  --default-algorithm=ec-sign-p256-sha256

# Create a Container Analysis note
cat <<EOF > /tmp/note.json
{
  "attestation": {
    "hint": {
      "humanReadableName": "Build Attestor Note"
    }
  }
}
EOF

curl -X POST \
  "https://containeranalysis.googleapis.com/v1/projects/$PROJECT_ID/notes/?noteId=build-attestor-note" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d @/tmp/note.json

# Create the attestor
gcloud container binauthz attestors create build-attestor \
  --attestation-authority-note=build-attestor-note \
  --attestation-authority-note-project=$PROJECT_ID

# Add the KMS key to the attestor
gcloud container binauthz attestors public-keys add \
  --attestor=build-attestor \
  --keyversion-project=$PROJECT_ID \
  --keyversion-location=global \
  --keyversion-keyring=binauthz-keyring \
  --keyversion-key=attestor-key \
  --keyversion=1

# Sign an image
IMAGE_PATH="us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/my-app"
IMAGE_DIGEST=$(gcloud container images describe $IMAGE_PATH:latest \
  --format="value(image_summary.digest)")

gcloud container binauthz attestations sign-and-create \
  --artifact-url="$IMAGE_PATH@$IMAGE_DIGEST" \
  --attestor=build-attestor \
  --attestor-project=$PROJECT_ID \
  --keyversion-project=$PROJECT_ID \
  --keyversion-location=global \
  --keyversion-keyring=binauthz-keyring \
  --keyversion-key=attestor-key \
  --keyversion=1
```

### Testing Binary Authorization

```bash
# This should succeed (signed image or whitelisted pattern)
kubectl run trusted --image=gcr.io/google-samples/hello-app:1.0

# This should be BLOCKED (unsigned image from Docker Hub)
kubectl run untrusted --image=nginx:latest
# Error: admission webhook "imagepolicywebhook.image-policy.k8s.io"
# denied the request: Image nginx:latest denied by Binary Authorization policy

# Check audit logs for denials
gcloud logging read \
  'resource.type="k8s_cluster" AND protoPayload.response.reason="BINARY_AUTHORIZATION"' \
  --limit=5
```

**War Story**: A team enabled Binary Authorization in enforce mode on a Friday afternoon. On Monday morning, their CI/CD pipeline had broken because Cloud Build was pushing images but not creating attestations. Every deployment for 48 hours was blocked. Start with `DRYRUN_AUDIT_LOG_ONLY` mode to identify what would be blocked before switching to enforce mode.

---

## Shielded GKE Nodes and Confidential Nodes

### Shielded GKE Nodes

Shielded nodes provide verifiable integrity for your cluster nodes, protecting against rootkits and boot-level tampering.

| Feature | Protection | How It Works |
| :--- | :--- | :--- |
| **Secure Boot** | Prevents unsigned kernel modules | Only Google-signed boot components load |
| **vTPM** | Measured boot integrity | Stores measurements for remote attestation |
| **Integrity Monitoring** | Detects runtime tampering | Compares boot measurements to known-good baseline |

```bash
# Shielded nodes are enabled by default on new GKE clusters
# Verify on an existing cluster:
gcloud container clusters describe my-cluster \
  --region=us-central1 \
  --format="yaml(shieldedNodes)"

# Explicitly enable if not set:
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --enable-shielded-nodes
```

### Confidential GKE Nodes

Confidential Nodes go beyond Shielded Nodes by encrypting data **in memory** using AMD SEV (Secure Encrypted Virtualization). Even if an attacker has physical access to the server or can perform a cold-boot attack, they cannot read the node's memory.

```bash
# Create a node pool with Confidential Nodes
gcloud container node-pools create confidential-pool \
  --cluster=my-cluster \
  --region=us-central1 \
  --machine-type=n2d-standard-4 \
  --num-nodes=1 \
  --enable-confidential-nodes

# Note: Confidential Nodes require N2D machine types (AMD EPYC)
# and are available in limited regions
```

| Feature | Shielded Nodes | Confidential Nodes |
| :--- | :--- | :--- |
| **Boot integrity** | Yes | Yes |
| **Memory encryption** | No | Yes (AMD SEV) |
| **Performance impact** | None | ~2-6% overhead |
| **Machine types** | All | N2D only (AMD) |
| **Cost** | No additional cost | ~10% premium |
| **Use case** | All production clusters | Financial, healthcare, PII |

---

## GKE Security Posture Dashboard

The Security Posture dashboard provides a centralized view of security issues across your GKE clusters. It scans for misconfigurations, vulnerability exposure, and policy violations.

### What It Detects

```bash
# Enable Security Posture on the cluster
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --security-posture=standard \
  --workload-vulnerability-scanning=standard

# Check security posture findings via gcloud
gcloud container security-posture findings list \
  --project=$PROJECT_ID \
  --format="table(finding.severity, finding.category, finding.description)"
```

The dashboard checks for:

- **Workload configuration**: Pods running as root, missing security contexts, privileged containers
- **Container vulnerabilities**: CVEs in container images from Artifact Registry
- **Network exposure**: Services exposed to the internet without authentication
- **RBAC issues**: Overly permissive ClusterRoleBindings
- **Supply chain**: Images not from trusted registries

### Hardening Pod Security

GKE supports Pod Security Standards (PSS) through the built-in Pod Security Admission controller:

```bash
# Enforce restricted Pod Security Standard on a namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/audit=restricted
```

```yaml
# A pod that passes the "restricted" security standard
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: us-central1-docker.pkg.dev/my-project/repo/app:v1
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 256Mi
```

---

## Secret Manager Integration

GKE integrates with Google Cloud Secret Manager through the **Secret Manager add-on**, which uses the Secrets Store CSI Driver to mount secrets as files in pods.

### Setting Up Secret Manager CSI Driver

```bash
# Enable the Secret Manager add-on on the cluster
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --enable-secret-manager

# Verify the driver is installed
kubectl get csidriver secrets-store.csi.k8s.io

# Create a secret in Secret Manager
echo -n "my-database-password" | gcloud secrets create db-password \
  --data-file=- \
  --replication-policy=automatic

# Grant the workload's GCP SA access to the secret
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:app-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Mounting Secrets in Pods

```yaml
# SecretProviderClass defines which secrets to mount
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: gcp-secrets
spec:
  provider: gcp
  parameters:
    secrets: |
      - resourceName: "projects/PROJECT_NUMBER/secrets/db-password/versions/latest"
        path: "db-password"
      - resourceName: "projects/PROJECT_NUMBER/secrets/api-key/versions/latest"
        path: "api-key"

---
apiVersion: v1
kind: Pod
metadata:
  name: app-with-secrets
spec:
  serviceAccountName: app-sa  # Must have Workload Identity configured
  containers:
  - name: app
    image: us-central1-docker.pkg.dev/my-project/repo/app:v1
    volumeMounts:
    - name: secrets
      mountPath: /var/secrets
      readOnly: true
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
  volumes:
  - name: secrets
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: gcp-secrets
```

```bash
# After deploying, verify the secret is mounted
kubectl exec app-with-secrets -- cat /var/secrets/db-password
# Output: my-database-password

# Secrets are NOT stored in etcd, reducing the blast radius
# if the cluster's etcd encryption is compromised
```

### Secret Manager vs Kubernetes Secrets

| Aspect | Kubernetes Secrets | Secret Manager + CSI |
| :--- | :--- | :--- |
| **Storage** | etcd (in cluster) | Google-managed (external) |
| **Encryption at rest** | Application-layer encryption | Automatic, Google-managed keys or CMEK |
| **Versioning** | No (replace only) | Full version history |
| **Rotation** | Manual (update + rollout) | Automatic with periodic sync |
| **Audit logging** | Kubernetes audit logs | Cloud Audit Logs (who accessed what, when) |
| **Cross-cluster sharing** | Not supported | Same secret across clusters/projects |
| **Access control** | RBAC (namespace-scoped) | IAM (project/org-scoped) |

---

## Did You Know?

1. **Before Workload Identity existed, the recommended workaround was to distribute service account JSON key files as Kubernetes Secrets.** This meant private key material was stored in etcd, potentially logged, and visible to anyone with RBAC access to the namespace. Google internal security audits in 2019 found that 34% of GKE clusters in a sample had service account keys stored as Kubernetes Secrets. Workload Identity, launched in 2019, eliminated the need for key files entirely by using short-lived, automatically-rotated tokens.

2. **Binary Authorization attestations are immutable and tied to the exact image digest (SHA-256), not the tag.** If someone pushes a new image with the tag `v1.0` (overwriting the old one), the attestation on the original image becomes invalid for the new image because the digest changed. This prevents a supply chain attack where an attacker replaces a trusted image with a malicious one while keeping the same tag. Always deploy by digest in production: `image: us-central1-docker.pkg.dev/proj/repo/app@sha256:abc123...`

3. **Confidential GKE Nodes encrypt each node's memory with a unique key that changes on every boot.** The key is generated inside the AMD Secure Processor and never leaves the CPU. Google's hypervisor, host OS, and other VMs on the same physical host cannot read the node's memory. The performance overhead is typically 2-6% for most workloads because the encryption happens in the CPU's memory controller at hardware speed, not in software.

4. **The GKE metadata server that enables Workload Identity intercepts all traffic to 169.254.169.254** (the standard cloud metadata endpoint) from pods. When a pod with Workload Identity configured requests an access token, the GKE metadata server contacts Google's Security Token Service (STS) to exchange the Kubernetes ServiceAccount token for a short-lived GCP access token scoped to the mapped GCP service account. These tokens expire after 1 hour and are automatically refreshed. Pods without Workload Identity receive a "permission denied" response instead of the node's credentials.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using the default Compute Engine service account for nodes | Cluster created without specifying a custom node SA | Create a dedicated node SA with minimal permissions; use `--service-account` flag |
| Not annotating the Kubernetes ServiceAccount | Workload Identity binding created but annotation forgotten | Always annotate: `iam.gke.io/gcp-service-account=GSA@PROJECT.iam` |
| Enabling Binary Authorization in enforce mode immediately | Wanting security without testing impact first | Start with `DRYRUN_AUDIT_LOG_ONLY` mode; review logs for 1-2 weeks before enforcing |
| Granting `roles/editor` to workload service accounts | "Editor" seems like a reasonable default | Use least-privilege roles: `storage.objectViewer`, `pubsub.subscriber`, etc. |
| Storing secrets as Kubernetes Secrets without encryption | Assuming K8s Secrets are encrypted by default | Enable application-layer encryption or use Secret Manager CSI driver |
| Forgetting to create the IAM binding for Workload Identity | Creating the KSA and GSA but not connecting them | The `iam.workloadIdentityUser` binding on the GSA is required for the mapping to work |
| Not setting `pod-security.kubernetes.io` labels | Assuming GKE blocks unsafe pods by default | Apply Pod Security Standards labels to namespaces; start with `warn` mode |
| Using image tags instead of digests with Binary Authorization | Tags are mutable and can be overwritten | Deploy by digest (`@sha256:...`) to ensure attestation matches the exact image |

---

## Quiz

<details>
<summary>1. How does Workload Identity Federation prevent the "shared identity" problem?</summary>

Without Workload Identity, every pod on a node shares the node VM's GCP service account. Any pod can call the metadata server (`169.254.169.254`) and receive an access token for that shared identity. Workload Identity Federation replaces this by running a **GKE metadata server** as a DaemonSet on each node. This server intercepts metadata requests from pods and, instead of returning the node's credentials, it checks which Kubernetes ServiceAccount the pod uses. It then exchanges the pod's Kubernetes SA token for a short-lived GCP access token scoped to the specific GCP service account mapped to that Kubernetes SA. Pods without a mapping receive no GCP credentials at all. This ensures each pod has only the permissions explicitly granted to its identity.
</details>

<details>
<summary>2. What is the difference between Binary Authorization "enforce" mode and "dry run" mode?</summary>

In **enforce** mode (`ENFORCED_BLOCK_AND_AUDIT_LOG`), Binary Authorization actively blocks pods from starting if their container images do not have valid attestations matching the policy. The pod creation fails with an admission webhook error, and the event is logged to Cloud Audit Logs. In **dry run** mode (`DRYRUN_AUDIT_LOG_ONLY`), Binary Authorization evaluates every pod against the policy but does not block anything. Instead, it logs what **would** have been blocked. This allows you to deploy the policy, observe its impact for days or weeks, fix any legitimate images that lack attestations, and then switch to enforce mode with confidence. Always start with dry run in production.
</details>

<details>
<summary>3. Why should you deploy container images by digest rather than by tag?</summary>

Tags are **mutable**: someone can push a new image with the same tag (e.g., `v1.0`), replacing the original image with completely different content. The digest (SHA-256 hash of the image manifest) is **immutable** and uniquely identifies the exact bytes of the image. For Binary Authorization, attestations are bound to the digest, not the tag. If you deploy by tag and the underlying image changes, the attestation from the original image does not apply to the new one. Deploying by digest (`image: repo/app@sha256:abc123...`) guarantees you are running the exact image that was scanned, tested, and attested. This is critical for supply chain security and audit compliance.
</details>

<details>
<summary>4. How does Secret Manager CSI driver differ from creating Kubernetes Secrets manually?</summary>

With Kubernetes Secrets, secret values are stored in the cluster's etcd database and managed through the Kubernetes API. Anyone with RBAC access to read Secrets in a namespace can see the values. With the Secret Manager CSI driver, secrets are stored in Google Cloud Secret Manager (outside the cluster) and mounted into pods as files at runtime. The secrets never pass through etcd. Access is controlled by IAM (not RBAC), providing finer-grained access control. Secret Manager also offers versioning, automatic rotation support, cross-cluster sharing, and comprehensive audit logging through Cloud Audit Logs. The trade-off is additional complexity in setup and a dependency on an external service.
</details>

<details>
<summary>5. What protections do Shielded GKE Nodes provide that standard nodes do not?</summary>

Shielded Nodes add three protections. **Secure Boot** ensures that only Google-signed boot components (bootloader, kernel, kernel modules) are loaded during startup, blocking rootkits and bootkits. **Virtual Trusted Platform Module (vTPM)** creates a measured boot chain where each component's hash is recorded before execution. These measurements can be remotely verified to prove the node booted in a known-good state. **Integrity Monitoring** continuously compares the boot measurements against a known-good baseline and raises alerts if tampering is detected. Together, these prevent an attacker from modifying the node's boot process to install persistent malware that survives reboots.
</details>

<details>
<summary>6. What happens if you enable Workload Identity on a cluster that already has pods using the node's service account?</summary>

Enabling Workload Identity on an existing cluster changes how the metadata server responds to pods. Pods that previously obtained tokens from the node's service account by calling `169.254.169.254` will now receive responses from the GKE metadata server instead. If those pods do not have a Kubernetes ServiceAccount annotated with a GCP service account mapping, they will **lose access** to GCP services. This can break running applications. The safe migration path is to: (1) enable Workload Identity on the cluster, (2) create and configure the KSA/GSA mappings for each workload, (3) update Deployments to use the new ServiceAccounts, and (4) verify access before removing the old node SA permissions. Do this during a maintenance window.
</details>

---

## Hands-On Exercise: Workload Identity for Pub/Sub and Binary Authorization

### Objective

Configure Workload Identity to securely access Pub/Sub from a pod, and set up Binary Authorization to block untrusted images.

### Prerequisites

- `gcloud` CLI installed and authenticated
- A GCP project with billing enabled
- GKE, Pub/Sub, Binary Authorization, and KMS APIs enabled

### Tasks

**Task 1: Create a GKE Cluster with Workload Identity**

<details>
<summary>Solution</summary>

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1

# Enable required APIs
gcloud services enable \
  container.googleapis.com \
  pubsub.googleapis.com \
  binaryauthorization.googleapis.com \
  cloudkms.googleapis.com \
  --project=$PROJECT_ID

# Create cluster with Workload Identity
gcloud container clusters create security-demo \
  --region=$REGION \
  --num-nodes=1 \
  --machine-type=e2-standard-2 \
  --release-channel=regular \
  --enable-ip-alias \
  --workload-pool=$PROJECT_ID.svc.id.goog \
  --enable-shielded-nodes

# Get credentials
gcloud container clusters get-credentials security-demo --region=$REGION
```
</details>

**Task 2: Set Up Workload Identity for Pub/Sub Access**

<details>
<summary>Solution</summary>

```bash
# Create a Pub/Sub topic and subscription
gcloud pubsub topics create demo-orders
gcloud pubsub subscriptions create demo-orders-sub \
  --topic=demo-orders

# Create a GCP service account for the publisher
gcloud iam service-accounts create pubsub-publisher \
  --display-name="Pub/Sub Publisher"

# Grant Pub/Sub publisher role
gcloud pubsub topics add-iam-policy-binding demo-orders \
  --member="serviceAccount:pubsub-publisher@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

# Create Kubernetes ServiceAccount
kubectl create serviceaccount pubsub-sa

# Bind KSA to GSA
gcloud iam service-accounts add-iam-policy-binding \
  pubsub-publisher@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/pubsub-sa]"

# Annotate KSA
kubectl annotate serviceaccount pubsub-sa \
  iam.gke.io/gcp-service-account=pubsub-publisher@$PROJECT_ID.iam.gserviceaccount.com
```
</details>

**Task 3: Deploy a Pod That Publishes to Pub/Sub**

<details>
<summary>Solution</summary>

```bash
# Deploy a pod with Workload Identity
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: publisher
spec:
  serviceAccountName: pubsub-sa
  containers:
  - name: publisher
    image: google/cloud-sdk:slim
    command: ["sleep", "3600"]
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
EOF

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/publisher --timeout=120s

# Verify Workload Identity is working
kubectl exec publisher -- gcloud auth list
# Should show pubsub-publisher@PROJECT_ID.iam.gserviceaccount.com

# Publish a message
kubectl exec publisher -- \
  gcloud pubsub topics publish demo-orders \
  --message='{"order_id": "12345", "item": "widget", "qty": 3}'

# Verify the message was published
gcloud pubsub subscriptions pull demo-orders-sub --auto-ack --limit=1

# Try to access a resource NOT granted (should fail)
kubectl exec publisher -- gsutil ls gs://
# Should fail with permission denied (403)
```
</details>

**Task 4: Enable Binary Authorization in Dry Run Mode**

<details>
<summary>Solution</summary>

```bash
# Enable Binary Authorization on the cluster
gcloud container clusters update security-demo \
  --region=$REGION \
  --binauthz-evaluation-mode=PROJECT_SINGLETON_POLICY_ENFORCE

# Export and examine the current policy
gcloud container binauthz policy export

# Create a policy that blocks everything except Google images (dry run)
cat <<EOF > /tmp/binauthz-policy.yaml
admissionWhitelistPatterns:
- namePattern: gcr.io/google-containers/*
- namePattern: gcr.io/google-samples/*
- namePattern: gke.gcr.io/*
- namePattern: gcr.io/gke-release/*
- namePattern: $REGION-docker.pkg.dev/$PROJECT_ID/*
- namePattern: registry.k8s.io/*
- namePattern: google/cloud-sdk*
defaultAdmissionRule:
  enforcementMode: DRYRUN_AUDIT_LOG_ONLY
  evaluationMode: ALWAYS_DENY
globalPolicyEvaluationMode: ENABLE
EOF

gcloud container binauthz policy import /tmp/binauthz-policy.yaml

echo "Binary Authorization is now in DRY RUN mode."
echo "Unsigned images will be LOGGED but not blocked."
```
</details>

**Task 5: Test Binary Authorization Behavior**

<details>
<summary>Solution</summary>

```bash
# Deploy an image from Docker Hub (would be blocked in enforce mode)
kubectl run nginx-test --image=nginx:1.27 --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"nginx-test","image":"nginx:1.27","resources":{"requests":{"cpu":"100m","memory":"64Mi"}}}]}}'

# In dry run mode, this will succeed but generate an audit log
kubectl get pod nginx-test

# Check audit logs for Binary Authorization dry-run violations
sleep 30  # Give logs time to propagate
gcloud logging read \
  'resource.type="k8s_cluster" AND protoPayload.methodName="io.k8s.core.v1.pods.create" AND labels."binaryauthorization.googleapis.com/decision"="DENIED"' \
  --limit=5 \
  --format="table(timestamp, protoPayload.resourceName)"

# Clean up test pod
kubectl delete pod nginx-test

echo "In a real deployment, you would:"
echo "1. Review dry-run logs for 1-2 weeks"
echo "2. Whitelist or attest all legitimate images"
echo "3. Switch to ENFORCED_BLOCK_AND_AUDIT_LOG mode"
```
</details>

**Task 6: Clean Up**

<details>
<summary>Solution</summary>

```bash
# Delete the cluster
gcloud container clusters delete security-demo \
  --region=$REGION --quiet

# Delete Pub/Sub resources
gcloud pubsub subscriptions delete demo-orders-sub --quiet
gcloud pubsub topics delete demo-orders --quiet

# Delete the GCP service account
gcloud iam service-accounts delete \
  pubsub-publisher@$PROJECT_ID.iam.gserviceaccount.com --quiet

# Reset Binary Authorization policy to allow all
cat <<EOF > /tmp/binauthz-default.yaml
defaultAdmissionRule:
  enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
  evaluationMode: ALWAYS_ALLOW
globalPolicyEvaluationMode: ENABLE
EOF
gcloud container binauthz policy import /tmp/binauthz-default.yaml

# Clean up temp files
rm -f /tmp/binauthz-policy.yaml /tmp/binauthz-default.yaml /tmp/note.json

echo "Cleanup complete."
```
</details>

### Success Criteria

- [ ] Cluster created with Workload Identity enabled
- [ ] Pub/Sub topic and subscription created
- [ ] Pod successfully publishes to Pub/Sub using Workload Identity (no key files)
- [ ] Pod cannot access resources not granted to its service account
- [ ] Binary Authorization enabled in dry run mode
- [ ] Audit logs show denied images from untrusted sources
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 6.4: GKE Storage](../module-6.4-gke-storage/)** --- Master Persistent Disk CSI drivers, regional PD failover, Filestore for shared NFS, Cloud Storage FUSE for object storage access, and Backup for GKE to protect your stateful workloads.
