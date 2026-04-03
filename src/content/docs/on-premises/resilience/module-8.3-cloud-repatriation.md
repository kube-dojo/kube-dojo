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

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** cloud repatriation economics with accurate 5-year TCO models that include hidden migration and staffing costs
2. **Design** a phased migration plan that replaces cloud-managed services (RDS, ElastiCache, ALB) with self-managed on-premises equivalents
3. **Implement** workload migration strategies that maintain service continuity during the transition from cloud to bare metal
4. **Plan** staffing and operational readiness requirements for self-managing infrastructure previously handled by cloud providers

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

> **Pause and predict**: 37signals spent $3.2M/year on AWS and estimated on-prem would cost $776K/year. But they also hired 2 additional engineers. At what cloud spend level does the engineering cost make repatriation not worthwhile?

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
---
apiVersion: metallb.io/v1beta1
kind: BGPAdvertisement
metadata:
  name: production-advertisement
  namespace: metallb-system
spec:
  ipAddressPools:
  - production-pool
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

> **Stop and think**: You need to migrate 50TB of data from AWS S3 to on-premises Ceph RGW over a 1 Gbps Direct Connect. At best, that is ~7 days of continuous transfer. During that time, the application is still writing new data to S3. How do you handle the gap between the initial sync and the final cutover?

### EBS to Ceph RBD

The migration pattern for block storage is: snapshot the EBS volume, mount it on a transfer instance, rsync the data to a migration pod on the on-premises cluster that writes to a Ceph RBD PVC. For databases, stop the application first to ensure consistency.

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

`rclone` provides an idempotent sync operation that can resume after interruptions and run incremental syncs to catch up with new data written during the migration period.

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
Your company spends $800K/year on AWS running a 50-node Kubernetes cluster. The CFO reads about 37signals saving millions through cloud repatriation and asks you to plan a move to on-premises. Your estimate: $600K/year operating cost plus 2 additional SRE hires at $200K each. Should you recommend proceeding?

<details>
<summary>Answer</summary>

**No. At 50 nodes, the economics do not justify repatriation.**

**The math**: On-premises operating cost is $600K/year + $400K/year for 2 SREs = $1M/year ongoing. Add $500K in hardware CapEx (amortized over 4 years = $125K/year) and $200-400K in migration engineering costs. First-year total: $1.5-1.7M. Ongoing: $1.125M/year. This is MORE expensive than the $800K/year cloud bill.

**The better approach**: Optimize cloud spend without migrating. Reserved Instances or Savings Plans reduce EC2 costs by 30-40%. Right-sizing instances (most are over-provisioned) saves another 10-20%. Spot instances for batch workloads save 60-90%. These optimizations can reduce the $800K bill to $480-560K/year with minimal engineering effort.

**When to revisit**: If the company grows to 150+ nodes and the cloud bill exceeds $2M/year, repatriation economics become compelling because the infrastructure staff cost is fixed while cloud costs scale linearly. The breakeven point where on-prem becomes cheaper is typically 50-100 nodes, depending on workload density, cloud discounts, and staff costs.

**Key insight from 37signals**: They spent $3.2M/year on cloud (hundreds of servers). At that scale, the $400K/year SRE cost is 12% of savings. At $800K/year, the same SRE cost is 50% of the total -- a completely different equation.
</details>

### Question 2
Your AWS-hosted application uses an ALB with three annotations: `certificate-arn` (for TLS termination), `wafv2-acl-arn` (for web application firewall), and `ssl-redirect: "443"` (for HTTPS redirect). You are migrating to on-premises Kubernetes with NGINX Ingress. How do you replicate each capability?

<details>
<summary>Answer</summary>

**Each AWS-managed capability maps to a specific on-premises tool:**

1. **`certificate-arn` (TLS certificates)**: Deploy cert-manager with a ClusterIssuer. For internet-facing services, use Let's Encrypt ACME. For internal services, use an internal CA. Reference the issuer via `cert-manager.io/cluster-issuer` annotation on the Ingress resource. cert-manager handles certificate issuance, renewal, and rotation automatically -- replacing the manual ACM certificate management workflow.

2. **`wafv2-acl-arn` (Web Application Firewall)**: Enable ModSecurity in the NGINX Ingress ConfigMap with `enable-modsecurity: "true"` and `enable-owasp-modsecurity-crs: "true"`. The OWASP Core Rule Set provides protection against SQL injection, XSS, and other common attacks. For more advanced WAF needs, deploy a dedicated WAF like Coraza (the successor to ModSecurity) as a sidecar or upstream proxy.

3. **`ssl-redirect: "443"` (HTTPS redirect)**: Set `nginx.ingress.kubernetes.io/force-ssl-redirect: "true"` on the Ingress resource. This configures NGINX to return a 308 redirect for all HTTP requests to their HTTPS equivalent.

**Key difference from AWS**: On AWS, these three features are a few annotations on a single ALB resource. On-premises, they require three separate systems (cert-manager, ModSecurity, NGINX config) that you must install, configure, and maintain. This operational overhead is often underestimated during migration planning.
</details>

### Question 3
You are using rclone to migrate 50TB of data from AWS S3 to on-premises Ceph RGW over a 1 Gbps Direct Connect. How long will the transfer take, what are the risks, and how do you handle data that changes during the migration?

<details>
<summary>Answer</summary>

**Transfer time calculation**: At 80% effective throughput (accounting for protocol overhead, TCP windowing, and S3 API latency), you get ~100 MB/s. 50 TB / 100 MB/s = ~500,000 seconds = ~5.8 days. With retries, throttling, and real-world variability, plan for 7-10 days.

**Risks and mitigations**:

1. **Connection interruption**: Direct Connect circuits can experience brief outages. Use `rclone sync` (idempotent -- only transfers changed/missing files on retry) rather than `rclone copy`. If interrupted, re-running the same command resumes from where it left off.

2. **Data changing during transfer**: The application continues writing new objects to S3 during the 7-10 day initial sync. Solution: start the bulk sync 2-3 weeks before cutover. Run incremental `rclone sync` nightly to catch new and modified objects. The final sync before cutover will only transfer the delta from the last 24 hours -- typically minutes, not days.

3. **S3 API rate limits**: AWS throttles to 5,500 GET requests per second per prefix. With 50TB of small files, you may hit this limit. Monitor for 503 SlowDown errors and use `--transfers 16` (not 64) to stay within limits.

4. **Bandwidth contention**: If production traffic also uses the Direct Connect, the migration competes for bandwidth. Use `--bwlimit 500M` during business hours and remove the limit overnight.

**Strategy**: Start bulk sync 2-3 weeks early. Nightly incremental syncs. Final sync in a 2-hour maintenance window. Verify with `rclone check` before cutover.
</details>

### Question 4
After migrating from AWS to on-premises, your application pods cannot authenticate to the self-managed PostgreSQL database. On AWS, the application used IRSA (IAM Roles for Service Accounts) to obtain temporary credentials for RDS IAM database authentication. What broke, and how do you fix it?

<details>
<summary>Answer</summary>

**The entire authentication chain is AWS-specific and breaks completely on-premises.**

**What broke**: IRSA works through a mutating webhook that injects AWS STS tokens into pods based on their ServiceAccount annotation (`eks.amazonaws.com/role-arn`). The application SDK (e.g., AWS SDK) uses these tokens to call AWS STS and receive temporary credentials, which are then presented to RDS for IAM-based database authentication. On-premises, there is no STS endpoint, no IRSA webhook, and self-managed PostgreSQL does not support AWS IAM authentication. Every link in the chain is missing.

**Fix options (in order of preference)**:

1. **Standard PostgreSQL authentication**: Create database users with password authentication. Store credentials in Kubernetes Secrets. The application needs a configuration change (connection string) but no code change if using standard database drivers.

2. **External Secrets Operator + Vault**: Use Vault to generate dynamic PostgreSQL credentials with automatic rotation. ESO syncs credentials to Kubernetes Secrets. This provides similar security properties to IRSA (short-lived credentials, automatic rotation) without AWS dependencies.

3. **Keycloak OIDC for service identity**: If the application supports OIDC-based database authentication (e.g., via a custom auth plugin), configure Keycloak to issue tokens for service accounts. This is the most complex option and rarely necessary.

**Key lesson**: Before migration, audit all pods for `eks.amazonaws.com/role-arn` annotations. Every pod with this annotation requires a migration plan for its authentication mechanism. IRSA is the single most common "hidden" AWS dependency.
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
