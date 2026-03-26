---
title: "Module 8.3: Cloud Repatriation & Migration"
slug: on-premises/resilience/module-8.3-cloud-repatriation
sidebar:
  order: 4
---

> **Complexity**: `[ADVANCED]` | Time: 60 minutes
>
> **Prerequisites**: [Module 8.1: Multi-Site & Disaster Recovery](../resilience/module-8.1-multi-site-dr/), [Module 8.2: Hybrid Cloud Connectivity](../resilience/module-8.2-hybrid-connectivity/)

---

## Why This Module Matters

In 2022, 37signals published a detailed accounting of their cloud exit. They spent $3.2 million per year on AWS -- EC2, RDS, S3, and EKS. Their CTO calculated that equivalent hardware would cost $600,000 upfront, with $840,000 annual operations. Over five years, the on-prem path would save over $7 million.

The migration took eight months. It was not lift-and-shift. Every AWS-managed service had to be replaced: RDS became self-managed PostgreSQL, ElastiCache became self-hosted Redis, ALB became HAProxy, CloudWatch became Prometheus and Grafana. Containers were the easy part. The hard part was everything around them -- load balancing, DNS, storage, secrets, monitoring, and dozens of AWS services quietly adopted over five years.

They completed the migration in early 2023 with a 60% infrastructure cost reduction. But they also hired two additional engineers and spent six months stabilizing self-managed PostgreSQL. Cloud repatriation is real, the economics can be compelling, and the execution is harder than anyone expects.

> **The Moving House Analogy**
>
> Moving from cloud to on-prem is like moving from a furnished rental to a house you buy. The rental included furniture (managed services) and a maintenance crew (cloud ops). Your house is cheaper long-term, but you buy all the furniture and learn to fix your own plumbing.

---

## What You'll Learn

- When cloud repatriation makes economic sense
- Translating cloud load balancers (ALB/NLB) to MetalLB
- Storage migration from EBS/EFS to Ceph
- IAM translation from AWS IAM to Keycloak
- Data gravity and migration sequencing
- Phased migration with rollback plans

---

## When Repatriation Makes Sense

```
  Annual cloud spend > $1M?
    No  ──► STAY (savings won't justify effort)
    Yes ──► Workloads steady-state (not bursty)?
              No  ──► STAY (on-prem can't burst)
              Yes ──► < 10 managed services?
                        No  ──► PARTIAL (move compute, keep managed)
                        Yes ──► Can hire 2-4 infra engineers?
                                  No  ──► STAY (can't operate on-prem)
                                  Yes ──► PROCEED WITH PLANNING
```

| Factor | Cloud (Annual) | On-Prem (Annual) |
|--------|---------------|-----------------|
| Compute (200 nodes) | $1,200,000 | $180,000 (amortized 4yr) |
| Storage (100TB) | $240,000 | $40,000 (Ceph, amortized) |
| Network egress | $180,000 (20TB/mo) | $12,000 (colo bandwidth) |
| Managed services | $360,000 | $0 (self-managed) |
| Additional staff | $0 | $400,000 (2 SREs) |
| Colocation | $0 | $144,000 |
| **Total** | **$1,980,000** | **$776,000 (61% savings)** |

> **Warning**: At 20 nodes, cloud is almost always cheaper when you factor in staff time. Breakeven is typically 50-100 nodes depending on workload density and cloud discounts (Reserved Instances, Committed Use Discounts).

---

## Translating Cloud Load Balancers to MetalLB

```
  CLOUD (AWS)                         ON-PREM (MetalLB)
  Internet ──► ALB (managed) ──►     Internet ──► Border Router ──►
               NodePort                            MetalLB Speaker
               Pods                                (BGP announces IPs)
                                                   Pods
```

```yaml
# MetalLB with BGP mode
apiVersion: metallb.io/v1beta2
kind: BGPPeer
metadata:
  name: datacenter-router
  namespace: metallb-system
spec:
  myASN: 64500
  peerASN: 64501
  peerAddress: 10.0.0.1
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: production-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.240/28    # 14 usable IPs for LoadBalancer services
```

### AWS ALB Annotation Translation

| AWS Annotation | On-Prem Equivalent |
|---------------|-------------------|
| `scheme: internet-facing` | MetalLB IPAddressPool with routable IPs |
| `certificate-arn` | cert-manager with Let's Encrypt or internal CA |
| `wafv2-acl-arn` | ModSecurity in NGINX Ingress |
| `target-type: ip` | Default kube-proxy behavior |
| `healthcheck-path` | NGINX Ingress `health-check-path` annotation |
| `ssl-redirect: "443"` | `nginx.ingress.kubernetes.io/force-ssl-redirect: "true"` |

---

## Storage Migration: EBS/EFS to Ceph

```
  AWS (Source)                     On-Prem (Target)
  ┌────────────────┐              ┌────────────────┐
  │ EBS Volumes    │──rsync──────►│ Ceph RBD       │
  │ EFS (NFS)      │──rsync──────►│ CephFS         │
  │ S3 Buckets     │──rclone─────►│ Ceph RGW (S3)  │
  └────────────────┘              └────────────────┘
```

### EBS to Ceph RBD

```bash
# On AWS: snapshot and mount to a transfer instance
aws ec2 create-snapshot --volume-id vol-0123456789abcdef

# On on-prem: create StorageClass and PVC
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-block
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  clusterID: rook-ceph
  pool: replicapool
  imageFormat: "2"
reclaimPolicy: Retain
allowVolumeExpansion: true
EOF

# Transfer via a migration pod
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: data-migration
  namespace: production
spec:
  containers:
  - name: rsync
    image: instrumentisto/rsync-ssh:latest
    command: ["rsync", "-avz", "--progress",
      "-e", "ssh -i /keys/transfer-key",
      "ubuntu@aws-transfer.example.com:/mnt/ebs-data/",
      "/target-data/"]
    volumeMounts:
    - name: target-vol
      mountPath: /target-data
  volumes:
  - name: target-vol
    persistentVolumeClaim:
      claimName: app-data
  restartPolicy: Never
EOF
```

### S3 to Ceph RGW

```bash
# Configure rclone for both endpoints
rclone config  # Set up aws-s3 and ceph-rgw remotes

# Sync
rclone sync aws-s3:app-assets ceph-rgw:app-assets --progress --transfers 16

# Verify
rclone check aws-s3:app-assets ceph-rgw:app-assets
```

---

## IAM Translation: AWS IAM to Keycloak

```
  AWS IAM               On-Prem (Keycloak)
  IAM Users       ──►   Keycloak Users
  IAM Groups      ──►   Keycloak Groups
  IAM Roles       ──►   Keycloak Roles
  IRSA (OIDC)     ──►   Keycloak OIDC + ServiceAccount
  AWS SSO         ──►   Keycloak Identity Brokering
```

### Kubernetes OIDC with Keycloak

```yaml
# kube-apiserver flags
- --oidc-issuer-url=https://keycloak.example.com/realms/kubernetes
- --oidc-client-id=kubernetes-apiserver
- --oidc-username-claim=preferred_username
- --oidc-groups-claim=groups
- --oidc-ca-file=/etc/kubernetes/pki/keycloak-ca.crt
```

```yaml
# RBAC binding for Keycloak groups
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: keycloak-platform-admins
subjects:
- kind: Group
  name: platform-admins     # Matches Keycloak group
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: keycloak-developers
  namespace: development
subjects:
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: edit
  apiGroup: rbac.authorization.k8s.io
```

> **Warning**: IRSA (IAM Roles for Service Accounts) is deeply AWS-specific. Any application using IRSA needs code or configuration changes to authenticate with Keycloak OIDC instead of AWS STS. Audit your pods for `eks.amazonaws.com/role-arn` annotations before migration.

---

## Data Gravity

Data gravity is the principle that large datasets attract applications. Moving 100TB takes days or weeks. Moving the application that reads it takes minutes. This means your migration sequence must follow the data -- migrate storage first, then the applications that depend on it.

---

## Phased Migration and Cutover

```
  Month 1-2        Month 3-4        Month 5-6        Month 7-8
  PREPARATION      DATA MIGRATION   APP MIGRATION    CUTOVER
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ Provision │    │ rclone/   │    │ Deploy    │    │ DNS swap  │
  │ hardware  │    │ rsync     │    │ apps      │    │ to on-prem│
  │ Install K8s│    │ ongoing   │    │ Run both  │    │ Monitor   │
  │ Set up     │    │ sync      │    │ in        │    │ Decommis- │
  │ network    │    │           │    │ parallel  │    │ sion cloud│
  │ Deploy     │    │ IAM       │    │ Shadow    │    │ (30 days) │
  │ platform   │    │ migration │    │ traffic   │    │           │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Rollback Plan

```
  Cutover complete. Error rate > 5%?
    │
   Yes ──► Fixable in 30 min?
              Yes ──► Fix and monitor
              No  ──► Data issue?
                        Yes ──► IMMEDIATE ROLLBACK (DNS back to cloud)
                        No  ──► Performance issue?
                                  Yes ──► Split traffic 50/50, investigate
                                  No  ──► ROLLBACK if unresolved in 2 hours
```

```bash
# Pre-cutover validation
rclone check aws-s3:production-data ceph-rgw:production-data
kubectl --context on-prem get pods -n production | grep -v Running  # Should be empty

# Rollback: redirect DNS back to cloud
kubectl --context cloud annotate service api-gateway \
  external-dns.alpha.kubernetes.io/hostname=api.example.com

# Sync any data written to on-prem back to cloud
rclone sync ceph-rgw:production-data aws-s3:production-data --progress
```

---

## Did You Know?

1. **Dropbox moved 90% of storage from AWS S3** to custom infrastructure ("Magic Pocket") in 2016, saving ~$75 million over two years. They kept unpredictable workloads (ML training, experiments) on AWS.

2. **Cloud data egress is asymmetric by design.** AWS charges $0.09/GB out but $0.00/GB in. A 100TB dataset costs ~$9,200 just to download -- the "Hotel California" pricing model makes leaving expensive.

3. **MetalLB in BGP mode makes your cluster look like a router.** Each LoadBalancer IP is a BGP route. If a speaker node goes down, another takes over in 1-3 seconds (BGP hold timer) -- faster than DNS failover.

4. **Self-hosted Keycloak handles 2,500+ auth requests per second** on a single instance. AWS Cognito's soft limit is 120/s per user pool. A three-replica Keycloak cluster supports 500,000+ users.

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Big-bang migration | Impatience | Migrate in phases: non-critical first, production last |
| Ignoring data egress costs | Focus on destination | Budget $0.09/GB for AWS egress upfront |
| Forgetting managed service deps | Developers use services silently | Audit all AWS API calls via CloudTrail |
| No parallel running period | "We tested in staging" | Run both environments 2-4 weeks with shadow traffic |
| Hardcoded cloud endpoints | SDK defaults (s3.amazonaws.com) | Use env vars for all endpoints; grep for cloud URLs |
| No rollback plan | Optimism bias | Document and rehearse rollback; keep cloud running 30 days |

---

## Quiz

### Question 1
Company spends $800K/year on AWS (50 nodes). CFO wants repatriation. On-prem estimate: $600K/year + 2 engineers. Should you recommend it?

<details>
<summary>Answer</summary>

No. At 50 nodes, savings are marginal (~$137K/year after hardware amortization) with a 1.5-3 year payback. Migration itself costs $200-400K in engineering time. Better approach: optimize cloud spend with reserved instances (30-40% savings) and right-sizing (10-20%), reducing the bill to $480-560K/year -- cheaper than on-prem. Revisit repatriation at 150+ nodes.
</details>

### Question 2
Migrating from AWS ALB with `certificate-arn`, `wafv2-acl-arn`, and `ssl-redirect`. How do you replicate each on-prem?

<details>
<summary>Answer</summary>

**certificate-arn**: Deploy cert-manager with a ClusterIssuer (Let's Encrypt ACME or internal CA). Reference via `cert-manager.io/cluster-issuer` annotation on Ingress. **wafv2-acl-arn**: Enable ModSecurity in NGINX Ingress ConfigMap with `enable-modsecurity: "true"` and `enable-owasp-modsecurity-crs: "true"`. **ssl-redirect**: Set `nginx.ingress.kubernetes.io/force-ssl-redirect: "true"` on the Ingress.
</details>

### Question 3
Using rclone to migrate 50TB over 1 Gbps Direct Connect. How long, and what are the risks?

<details>
<summary>Answer</summary>

At ~80% throughput (0.1 GB/s), raw transfer: ~5.8 days. With overhead, expect 7-10 days. Risks: (1) Connection interruption -- use `rclone sync` (idempotent, resumes). (2) Data changing during transfer -- run final sync in maintenance window. (3) S3 API rate limits (5,500 GET/s per prefix) -- monitor for 503 SlowDown. (4) Bandwidth contention with production traffic -- use `--bwlimit` or schedule off-peak. Strategy: start bulk sync 2-3 weeks early, incremental nightly syncs, final sync at cutover.
</details>

### Question 4
After migrating from AWS IAM (IRSA) to Keycloak, pods cannot authenticate to PostgreSQL. Most likely cause?

<details>
<summary>Answer</summary>

The app used IRSA to get temporary AWS credentials for RDS IAM database authentication. On-prem, there is no STS, no IRSA webhook, and self-managed PostgreSQL does not support IAM auth. The entire authentication chain breaks. Fix: switch to standard PostgreSQL auth (credentials in Kubernetes Secrets), or configure Keycloak OIDC for service identity. Use External Secrets Operator to manage credential rotation. Key lesson: IRSA is deeply AWS-specific; any app using it needs code or config changes.
</details>

---

## Hands-On Exercise: Simulate Cloud-to-On-Prem Migration

**Objective**: Migrate a workload between two kind clusters, translating cloud endpoints to on-prem equivalents.

```bash
# 1. Create clusters
kind create cluster --name cloud-sim
kind create cluster --name onprem-sim

# 2. Deploy "cloud" app with cloud-specific config
kubectl config use-context kind-cloud-sim
kubectl create namespace webapp
kubectl create configmap app-settings -n webapp \
  --from-literal=DB_HOST=rds.aws.example.com \
  --from-literal=CACHE_HOST=elasticache.aws.example.com \
  --from-literal=S3_ENDPOINT=https://s3.amazonaws.com
kubectl create deployment webapp --image=nginx:1.27 -n webapp --replicas=3

# 3. Deploy on on-prem with translated config
kubectl config use-context kind-onprem-sim
kubectl create namespace webapp
kubectl create configmap app-settings -n webapp \
  --from-literal=DB_HOST=postgres.database.svc.cluster.local \
  --from-literal=CACHE_HOST=redis.cache.svc.cluster.local \
  --from-literal=S3_ENDPOINT=https://rgw.onprem.example.com
kubectl create deployment webapp --image=nginx:1.27 -n webapp --replicas=3

# 4. Compare configurations
echo "=== Cloud ==="
kubectl --context kind-cloud-sim get configmap app-settings -n webapp -o yaml
echo "=== On-Prem ==="
kubectl --context kind-onprem-sim get configmap app-settings -n webapp -o yaml

# 5. Clean up
kind delete cluster --name cloud-sim
kind delete cluster --name onprem-sim
```

### Success Criteria
- [ ] Application deployed on both clusters
- [ ] ConfigMap translated from cloud to on-prem endpoints
- [ ] Both environments verified with running pods
- [ ] Differences between configurations documented

---

## Next Module

This is the final module in the Resilience & Migration section. Return to the [Resilience & Migration overview](../resilience/) to review the full section, or continue to the next section in the on-premises track.
