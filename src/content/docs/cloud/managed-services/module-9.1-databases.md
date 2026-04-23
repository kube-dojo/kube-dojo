---
title: "Module 9.1: Relational Database Integration (RDS / Cloud SQL / Flexible Server)"
slug: cloud/managed-services/module-9.1-databases
sidebar:
  order: 2
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Cloud Essentials (any provider), Kubernetes networking basics

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure private connectivity from Kubernetes pods to managed databases (RDS, Cloud SQL, Flexible Server) using VPC-native networking**
- **Implement connection pooling with PgBouncer or ProxySQL sidecars to optimize database connection management from pods**
- **Deploy automated credential rotation for database secrets using cloud-native rotation with Kubernetes External Secrets Operator**
- **Design high-availability database architectures with cross-AZ failover that Kubernetes workloads survive transparently**

---

## Why This Module Matters

Teams that run stateful databases on Kubernetes can hit painful outages when storage placement, scheduling, and availability-zone constraints are misaligned, which is one reason many production teams choose managed database services instead.

The startup migrated to Amazon RDS the following Monday. Not because Kubernetes cannot run databases -- it absolutely can -- but because managed databases handle the hardest parts of database operations: automated failover, point-in-time recovery, patching, and cross-AZ replication. The real engineering challenge shifted from "keeping PostgreSQL alive" to "connecting Kubernetes workloads to managed databases securely, efficiently, and reliably."

This module teaches you the second part. You will learn how to connect Kubernetes pods to managed relational databases across all three major clouds using private networking, connection pooling, credential rotation, schema migrations in a GitOps workflow, and high-availability patterns that survive AZ failures without your on-call engineer losing sleep.

---

## Private Network Connectivity

The first rule of database connectivity from Kubernetes: **avoid exposing your database to the public internet whenever possible**. Every cloud provider offers private endpoint mechanisms that keep traffic on the provider's backbone network.

### Architecture: VPC-Native Connectivity

```mermaid
flowchart LR
    subgraph K8sVPC [Kubernetes VPC]
        PodA[Pod A]
        PodB[Pod B]
        Svc[ClusterIP Service]
        PodA --> Svc
        PodB --> Svc
    end
    
    subgraph DBSvc [Database Service]
        Primary[Primary AZ-a]
        Replica[Replica AZ-b]
    end
    
    Svc -- VPC Peering/Private Endpoint ---> Primary
```

> **Stop and think**: If your pod in `us-east-1a` queries a database in `us-east-1b`, the traffic is private and secure. However, what other consequence does crossing an Availability Zone boundary have? (Hint: Think about your cloud provider's monthly billing statement).

### AWS: RDS with VPC Private Subnets

On AWS, your EKS cluster and RDS instance should share the same VPC or use VPC peering. [RDS instances deployed into private subnets are accessible from any resource within the VPC](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html).

```bash
# Create a DB subnet group using private subnets
aws rds create-db-subnet-group \
  --db-subnet-group-name eks-database-subnets \
  --db-subnet-group-description "Private subnets for RDS from EKS" \
  --subnet-ids subnet-0a1b2c3d4e5f00001 subnet-0a1b2c3d4e5f00002

# Create a security group allowing traffic from EKS node CIDR
aws ec2 create-security-group \
  --group-name rds-from-eks \
  --description "Allow PostgreSQL from EKS nodes" \
  --vpc-id vpc-0abc123def456

SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=rds-from-eks" \
  --query 'SecurityGroups[0].GroupId' --output text)

# Allow port 5432 from EKS pod CIDR (check your VPC CNI config)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp --port 5432 \
  --cidr 10.0.0.0/16

# Create RDS instance in private subnets
aws rds create-db-instance \
  --db-instance-identifier app-postgres \
  --db-instance-class db.r6g.large \
  --engine postgres --engine-version 16.4 \
  --master-username appadmin \
  --manage-master-user-password \
  --allocated-storage 100 --storage-type gp3 \
  --db-subnet-group-name eks-database-subnets \
  --vpc-security-group-ids $SG_ID \
  --multi-az --storage-encrypted \
  --no-publicly-accessible
```

The [`--manage-master-user-password` flag tells RDS to store the master password in AWS Secrets Manager automatically](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html). RDS generates and stores the password in Secrets Manager so you can avoid hardcoding or manually distributing it.

### GCP: Cloud SQL with Private IP Connectivity

```bash
# Allocate IP range for Private Service Connect
gcloud compute addresses create google-managed-services \
  --global --purpose=VPC_PEERING \
  --addresses=10.100.0.0 --prefix-length=16 \
  --network=my-vpc

# Create the private connection
gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --ranges=google-managed-services \
  --network=my-vpc

# Create Cloud SQL with private IP only
gcloud sql instances create app-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-custom-4-16384 \
  --region=us-central1 \
  --network=my-vpc \
  --no-assign-ip \
  --availability-type=REGIONAL \
  --storage-type=SSD --storage-size=100GB \
  --storage-auto-increase

# Get the private IP
gcloud sql instances describe app-postgres \
  --format='value(ipAddresses.filter("type=PRIVATE").ipAddress)'
```

### Azure: Flexible Server with Private Access (VNet Integration)

```bash
# Create a private DNS zone for PostgreSQL
az network private-dns zone create \
  --resource-group myRG \
  --name privatelink.postgres.database.azure.com

# Link DNS zone to the VNET
az network private-dns zone vnet-link create \
  --resource-group myRG \
  --zone-name privatelink.postgres.database.azure.com \
  --name aks-link --virtual-network aks-vnet \
  --registration-enabled false

# Create Flexible Server with VNET integration
az postgres flexible-server create \
  --resource-group myRG --name app-postgres \
  --version 16 --sku-name Standard_D4ds_v5 \
  --storage-size 128 \
  --vnet aks-vnet --subnet db-subnet \
  --private-dns-zone privatelink.postgres.database.azure.com \
  --high-availability ZoneRedundant
```

### Kubernetes Service for Database Endpoints

Regardless of cloud, create an ExternalName or headless Service so your application code uses a Kubernetes-native DNS name:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-database
  namespace: production
spec:
  type: ExternalName
  externalName: app-postgres.abc123.us-east-1.rds.amazonaws.com
```

Your application connects to `app-database.production.svc.cluster.local`. If you migrate from RDS to Cloud SQL, you change the Service -- not every application config.

---

## Connection Pooling with PgBouncer

Every database connection consumes server memory, so large numbers of idle connections waste capacity. Kubernetes makes this worse because pods scale horizontally. If you have 20 replicas, each maintaining a pool of 10 connections, that is 200 connections. During a rolling deployment, both old and new pods exist simultaneously -- suddenly 400 connections.

Managed databases have connection limits, and real performance usually degrades before you reach the configured maximum. The answer is connection pooling.

### PgBouncer as a Sidecar

The sidecar pattern places PgBouncer in the same pod as your application. Each pod gets its own pooler.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: production
spec:
  replicas: 10
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
        - name: api
          image: mycompany/api-server:2.1.0
          ports:
            - containerPort: 8080
          env:
            - name: DATABASE_URL
              value: "postgresql://appuser:$(DB_PASSWORD)@localhost:6432/appdb?sslmode=require"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
        - name: pgbouncer
          image: bitnami/pgbouncer:1.23.0
          ports:
            - containerPort: 6432
          env:
            - name: PGBOUNCER_DATABASE
              value: appdb
            - name: POSTGRESQL_HOST
              value: app-postgres.abc123.us-east-1.rds.amazonaws.com
            - name: POSTGRESQL_PORT
              value: "5432"
            - name: POSTGRESQL_USERNAME
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: POSTGRESQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            - name: PGBOUNCER_POOL_MODE
              value: transaction
            - name: PGBOUNCER_DEFAULT_POOL_SIZE
              value: "5"
            - name: PGBOUNCER_MAX_CLIENT_CONN
              value: "100"
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
```

### PgBouncer as a Centralized Proxy

For larger clusters, a centralized PgBouncer Deployment is more efficient:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
  namespace: database
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: pgbouncer
      containers:
        - name: pgbouncer
          image: bitnami/pgbouncer:1.23.0
          ports:
            - containerPort: 6432
          env:
            - name: PGBOUNCER_POOL_MODE
              value: transaction
            - name: PGBOUNCER_DEFAULT_POOL_SIZE
              value: "25"
            - name: PGBOUNCER_MAX_CLIENT_CONN
              value: "1000"
            - name: PGBOUNCER_MAX_DB_CONNECTIONS
              value: "150"
          readinessProbe:
            tcpSocket:
              port: 6432
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: pgbouncer
  namespace: database
spec:
  selector:
    app: pgbouncer
  ports:
    - port: 5432
      targetPort: 6432
```

### Pool Mode Decision Matrix

| Pool Mode | How It Works | Best For | Watch Out |
|-----------|-------------|----------|-----------|
| **session** | Connection assigned for entire client session | Legacy apps using PREPARE/LISTEN | Fewest pooling benefits |
| **transaction** | Connection returned after each transaction | Most web applications | Cannot use session-level features |
| **statement** | Connection returned after each statement | Simple read workloads | Breaks multi-statement transactions |

> **Pause and predict**: If you use `session` pooling with a modern microservice that opens and closes database connections rapidly for each HTTP request, what will happen to the backend connections on your PostgreSQL server?

For many stateless web workloads, `transaction` mode is a strong default because it balances connection reuse with broad application compatibility.

---

## Credential Rotation

Hardcoded database passwords in Kubernetes Secrets are a ticking time bomb. When you need to rotate them -- and you will -- you face a coordination problem: update the password in the database, update the Secret in Kubernetes, restart every pod that uses it, and do all of this without downtime.

### External Secrets Operator (ESO) with Rotation

ESO [syncs secrets from cloud provider secret managers into Kubernetes Secrets automatically](https://github.com/external-secrets/external-secrets).

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: production/database/credentials
        property: username
    - secretKey: password
      remoteRef:
        key: production/database/credentials
        property: password
    - secretKey: host
      remoteRef:
        key: production/database/credentials
        property: host
```

When the secret rotates in Secrets Manager (via an AWS Lambda rotation function or equivalent), ESO picks up the new value within the `refreshInterval` window.

> **Stop and think**: How does the External Secrets Operator authenticate with AWS Secrets Manager without using hardcoded IAM user keys? (Hint: Think about Kubernetes Service Accounts and IAM OIDC Workload Identity.)

### Dual-User Rotation Strategy

The safest rotation pattern uses two database users, alternating between them:

```mermaid
sequenceDiagram
    participant SM as Secrets Manager
    participant K8s as Kubernetes
    participant Pods as Application Pods
    participant DB as Database

    Note over DB: Time 0: user_a (active), user_b (standby)
    SM->>DB: Time 1: Rotate user_b password
    SM->>K8s: Time 2: Update Secret to point to user_b
    K8s->>Pods: Time 3: Trigger rolling restart
    Pods->>DB: Pods connect using user_b credentials
    Note over DB: Time 4: user_b (active), user_a (standby)
    SM->>DB: Time 5: Rotate user_a password (safe)
```

This ensures zero-downtime rotation because the [old credentials remain valid throughout the entire rollout](https://docs.aws.amazon.com/secretsmanager/latest/userguide/tutorials_rotation-alternating.html).

```bash
# AWS Secrets Manager rotation with dual-user strategy
aws secretsmanager rotate-secret \
  --secret-id production/database/credentials \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789:function:db-rotation \
  --rotation-rules '{"AutomaticallyAfterDays": 30}'
```

### Triggering Pod Restarts on Secret Change

Use Reloader or stakater/Reloader to [automatically trigger rolling restarts](https://github.com/stakater/Reloader):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  annotations:
    reloader.stakater.com/auto: "true"
spec:
  # ... Reloader watches for Secret changes and triggers rolling updates
```

---

## Schema Migrations in GitOps

Running `ALTER TABLE` in production is nerve-wracking enough. Doing it automatically through a GitOps pipeline requires careful design to avoid breaking running applications.

### The Expand-Contract Pattern

Avoid making breaking schema changes in a single step. Instead:

```mermaid
flowchart LR
    P1["Phase 1: EXPAND<br/>(Add new column)"] --> P2["Phase 2: MIGRATE<br/>(Write to both)"]
    P2 --> P3["Phase 3: CONTRACT<br/>(Remove old column)"]
```

| Phase | Database Schema | Application Behavior |
| :--- | :--- | :--- |
| **1: EXPAND** | `[ id | name | email ]` (email is NEW, nullable) | App v1: Writes `[name]` |
| **2: MIGRATE** | `[ id | name | email ]`<br>*(Backfill script populates email)* | App v2: Writes both<br>Reads `[email]` |
| **3: CONTRACT**| `[ id | email ]`<br>*(name column dropped)* | App v3: Writes `[email]` |

### Kubernetes Job for Migrations

> **Stop and think**: Why is it dangerous to run database migrations as an `initContainer` within your application Deployment? Consider what happens when a Deployment horizontally scales from 2 to 10 replicas during an unexpected load spike.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate-v42
  namespace: production
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: mycompany/api-server:2.1.0
          command: ["./migrate", "--direction=up", "--steps=1"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: connection-string
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
      serviceAccountName: db-migrator
```

The [`argocd.argoproj.io/hook: PreSync` annotation tells Argo CD to run this Job before deploying new application pods](https://argo-cd.readthedocs.io/en/latest/user-guide/sync-waves/). The migration runs, the schema updates, then the new application version rolls out.

### Migration Safety Checklist

| Rule | Reason |
|------|--------|
| Avoid dropping columns in the same release that removes their usage | Old pods still running during rollout can crash |
| Add columns as nullable or with defaults in rolling deployments | INSERT statements from old code won't fail |
| Use advisory locks in migration scripts | Prevents two migration Jobs from running simultaneously |
| Set a statement timeout | A long-running `ALTER TABLE` lock can block queries until the lock is released |
| Test rollback before applying | `migrate down` should work for the rollback path you expect to use |

```sql
-- Safe migration example with timeout and lock
SET lock_timeout = '5s';
SET statement_timeout = '30s';

ALTER TABLE orders ADD COLUMN shipping_method VARCHAR(50) DEFAULT 'standard';
CREATE INDEX CONCURRENTLY idx_orders_shipping ON orders(shipping_method);
```

---

## High Availability and Read Replicas

### Multi-AZ Architecture

All three clouds support Multi-AZ deployments for managed databases. The failover mechanics differ:

| Feature | AWS RDS Multi-AZ | GCP Cloud SQL Regional | Azure Flexible Server ZR |
|---------|-------------------|------------------------|--------------------------|
| Failover time | 60-120 seconds | ~60 seconds | 60-120 seconds |
| Read from standby | [No (Multi-AZ), Yes (Multi-AZ Cluster)](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html) | No | No |
| Cross-region | Separate feature (Read Replicas) | [Cross-region replicas](https://cloud.google.com/sql/docs/postgres/replication/cross-region-replicas) | [Geo-replication](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-read-replicas-geo) |
| Endpoint changes on failover | No (DNS CNAME updated) | No (IP stays same) | No (DNS updated) |

### Read Replica Routing in Kubernetes

Create separate Services for read and write traffic:

```yaml
# Write endpoint (primary)
apiVersion: v1
kind: Service
metadata:
  name: db-write
  namespace: production
spec:
  type: ExternalName
  externalName: app-postgres.abc123.us-east-1.rds.amazonaws.com
---
# Read endpoint (replicas)
apiVersion: v1
kind: Service
metadata:
  name: db-read
  namespace: production
spec:
  type: ExternalName
  externalName: app-postgres-ro.abc123.us-east-1.rds.amazonaws.com
```

Your application then uses two connection strings:

```python
# Application configuration
WRITE_DB = "postgresql://user:pass@db-write.production.svc:5432/appdb"
READ_DB = "postgresql://user:pass@db-read.production.svc:5432/appdb"
```

### Cross-AZ Traffic Costs

This catches many teams off guard. Cross-AZ data transfer costs money on every cloud:

- **AWS**: [$0.01/GB per direction between AZs](https://aws.amazon.com/blogs/networking-and-content-delivery/optimizing-data-transfer-costs-when-using-aws-network-load-balancer/)
- **GCP**: [$0.01/GB between zones in the same region](https://cloud.google.com/vpc/pricing)
- **Azure**: [Free within the same region](https://azure.microsoft.com/en-us/pricing/details/bandwidth) (as of 2025)

If your application in AZ-a talks to a database in AZ-b, every query and response crosses AZ boundaries. For a chatty application doing 10,000 queries per second, each returning 1 KB, that is roughly 864 GB/day -- about $17/day just in cross-AZ transfer.

**Mitigation strategies:**
1. Use topology-aware routing to prefer same-AZ replicas
2. Use connection pooling to reduce round-trips
3. Batch reads where possible
4. Cache frequently-accessed data (see Module 9.5)

---

## Did You Know?

1. **Amazon RDS operates at very large fleet scale**, which is one reason managed databases can absorb operational work that would otherwise fall on platform teams.

2. **PostgreSQL connection capacity is constrained by server memory and per-connection process overhead**, so practical limits are often lower than the largest `max_connections` value you can configure.

3. **Cloud SQL now offers newer private connectivity patterns for multi-network topologies**, while older private-IP approaches had routing limitations that mattered in hub-and-spoke designs.

4. **Schema migrations are a common source of production risk**, especially when they take heavyweight locks or assume a deployment can change application code and database shape at the same instant.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Exposing the database with a public IP "for debugging" | Developers need to query from laptops | Use `kubectl port-forward` to a pod with database access |
| Not setting `volumeBindingMode: WaitForFirstConsumer` when self-hosting | [Default StorageClass creates volumes immediately](https://kubernetes.io/docs/concepts/storage/storage-classes/) | Does not apply to managed DBs, but remember for dev environments |
| Allowing unlimited connections from pods | No connection pooling configured | Deploy PgBouncer (sidecar or centralized) with explicit limits |
| Storing database passwords in ConfigMaps | Confusion between ConfigMap and Secret | Use Secrets, and preferably ESO with a cloud secret manager |
| Running migrations in application startup code | Seems convenient -- every pod migrates on boot | Use a dedicated Job (PreSync hook) so migration runs exactly once |
| Ignoring cross-AZ data transfer costs | Not visible until the bill arrives | Monitor with VPC Flow Logs and use topology-aware routing |
| Using `session` pool mode in PgBouncer by default | It is the default setting | Explicitly set `transaction` mode for web workloads |
| Not testing database failover | "Multi-AZ handles it" | Schedule quarterly failover tests using [`aws rds reboot-db-instance --force-failover`](https://docs.aws.amazon.com/cli/v1/reference/rds/reboot-db-instance.html) |

---

## Quiz

<details>
<summary>1. Your team is migrating a legacy application to Kubernetes. The application currently hardcodes the RDS endpoint `prod-db.abc123.us-east-1.rds.amazonaws.com` in its configuration files. You suggest creating a Kubernetes Service to represent the database instead. If the database is still hosted in RDS, how does introducing a Kubernetes Service improve the architecture, and what specific type of Service should you use?</summary>

An ExternalName Service provides a layer of indirection, decoupling the application's configuration from the physical database location. By using an ExternalName Service, the application connects to a stable internal DNS name like `db-write.production.svc.cluster.local`. If you need to migrate the database, promote a read replica to primary, or switch to a different cloud provider, you only update the Service definition once. The application pods do not need to be reconfigured or restarted, minimizing risk and operational overhead during database maintenance.
</details>

<details>
<summary>2. A high-traffic e-commerce API is experiencing latency spikes. You notice the PostgreSQL database is hitting its maximum connection limit. The API is written in Go and opens a connection, runs a quick SELECT query, and closes it for every request. You deploy PgBouncer, but the database connection count doesn't drop significantly. You realize PgBouncer is using `session` mode. Why did `session` mode fail to solve the problem, and how would switching to `transaction` mode fix it?</summary>

In `session` mode, PgBouncer assigns a backend server connection to a client for the entire duration of the client's session. Because the Go API opens and closes connections rapidly, each request ties up a backend connection, providing minimal pooling benefits. Switching to `transaction` mode resolves this by returning the backend connection to the pool immediately after each transaction completes. This allows PgBouncer to multiplex thousands of brief client transactions over a small, stable pool of backend database connections, drastically reducing memory overhead and connection churn on the PostgreSQL server.
</details>

<details>
<summary>3. Your team needs to rename the `user_status` column to `account_state` in the primary database. The lead developer plans to run `ALTER TABLE users RENAME COLUMN user_status TO account_state;` during the next Argo CD sync. You block the PR, explaining that this will cause an outage during the rolling deployment. Why will a simple rename cause an outage in Kubernetes, and how should the team apply the expand-contract pattern to execute this change safely?</summary>

A simple rename causes an outage because Kubernetes rolling deployments run old and new pod versions simultaneously. The older pods still running during the rollout will attempt to query the `user_status` column, which no longer exists, causing them to fail as soon as they hit that code path. The expand-contract pattern solves this by breaking the change into additive phases, starting with expanding the schema to include the new `account_state` column. Next, you deploy application code that writes to both columns, and finally, once all pods are updated and data is backfilled, you contract by removing the old `user_status` column. This incremental approach ensures every version of the application can safely interact with the database schema at any given moment.
</details>

<details>
<summary>4. At 3:00 AM, the primary RDS instance in `us-east-1a` suffers a hardware failure. The database is configured for Multi-AZ, and a standby exists in `us-east-1b`. The failover completes in 60 seconds, but your Kubernetes pods continue throwing connection errors for 5 minutes before recovering. Assuming the pods are using an ExternalName Service pointing to the RDS endpoint, what caused this extended downtime, and how does Kubernetes eventually resolve the connection?</summary>

During an RDS Multi-AZ failover, AWS promotes the standby instance and updates the DNS CNAME record of the database endpoint to point to the new primary's IP address. However, Kubernetes pods and nodes often cache DNS lookups based on the Time-To-Live (TTL) of the record. The extended downtime occurs because the pods continue sending traffic to the old, dead IP address until their local DNS cache expires. Once the TTL expires, the pods re-resolve the ExternalName Service, receive the new IP address of the promoted instance, and successfully re-establish their database connections.
</details>

<details>
<summary>5. Your monthly cloud bill shows a massive spike in "Cross-AZ Data Transfer" costs. Your EKS nodes are spread across `us-west-2a`, `2b`, and `2c`, while your RDS instance is primarily in `us-west-2a`. The application makes thousands of small queries per second. Why is this architecture generating data transfer charges, and what are two architectural changes you could make to reduce this specific line item on the bill?</summary>

Cloud providers charge for data transfer that crosses Availability Zone boundaries, even within the same region. Because your pods are distributed across three AZs but the database is in one, roughly two-thirds of your application queries and their corresponding result sets are crossing AZ boundaries, incurring bilateral charges. To reduce this cost, you can implement topology-aware routing to force pods to prefer reading from a read replica in their local AZ. Alternatively, you can implement connection pooling or application-level caching to drastically reduce the total volume of round-trips made to the database.
</details>

<details>
<summary>6. A developer notices that a database migration Job deployed via an Argo CD PreSync hook occasionally fails due to a timeout. To ensure the deployment eventually succeeds, they propose changing the Job's `backoffLimit` from `0` to `3`. You reject this change. What is the danger of automatically retrying a failed database migration Job, and why is failing the entire deployment process the safer alternative?</summary>

Automatically retrying a database migration Job is dangerous because migrations are rarely idempotent by default. If a migration script fails halfway through—for example, it successfully creates a table but times out creating an index—retrying the Job will cause it to attempt creating the table again, resulting in a fatal error that requires manual database surgery to fix. By keeping `backoffLimit: 0`, a failure immediately stops the Argo CD sync process. This fail-fast behavior preserves the state of the database and forces an engineer to investigate the partial migration, manually rectify the schema, and safely resume the deployment.
</details>

<details>
<summary>7. Your security team mandates that database passwords be rotated every 30 days. You write a script that updates the password in RDS, then updates the Kubernetes Secret, and finally triggers a rolling restart of the application Deployments. During the next rotation, the application experiences 45 seconds of downtime where database authentication fails. How would implementing a dual-user rotation strategy eliminate this downtime window?</summary>

The downtime occurs because there is an unavoidable race condition: old pods still running during the rolling restart have the old password, but the database only accepts the new password. The dual-user rotation strategy eliminates this by maintaining two active database users. When rotation occurs, you change the password of the standby user, update Kubernetes to use the standby user, and trigger the rolling restart. Because the original user's password remains unchanged during the rollout, the old pods continue to function while the new pods connect using the newly rotated credentials.
</details>

---

## Hands-On Exercise: Connect Kind Cluster to Local PostgreSQL

Since managed databases require cloud accounts, we will simulate the architecture locally using Docker and kind.

### Setup

```bash
# Create a Docker network shared between kind and PostgreSQL
docker network create db-lab

# Start PostgreSQL in Docker
docker run -d --name lab-postgres \
  --network db-lab \
  -e POSTGRES_USER=appadmin \
  -e POSTGRES_PASSWORD=lab-secret-123 \
  -e POSTGRES_DB=appdb \
  -p 5432:5432 \
  postgres:16

# Create a kind cluster attached to the same Docker network
cat > /tmp/kind-db-lab.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

kind create cluster --name db-lab --config /tmp/kind-db-lab.yaml

# Connect kind nodes to the db-lab network
docker network connect db-lab db-lab-control-plane
docker network connect db-lab db-lab-worker
docker network connect db-lab db-lab-worker2

# Get PostgreSQL's IP on the db-lab network
PG_IP=$(docker inspect lab-postgres \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' | head -1)
echo "PostgreSQL IP: $PG_IP"
```

### Task 1: Create an ExternalName Service

Create a Service that points to the PostgreSQL container.

<details>
<summary>Solution</summary>

Since ExternalName requires a DNS name (not an IP), use a headless Service with Endpoints:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-database
  namespace: default
spec:
  clusterIP: None
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: v1
kind: Endpoints
metadata:
  name: app-database
  namespace: default
subsets:
  - addresses:
      - ip: "${PG_IP}"   # Replace with actual IP from setup
    ports:
      - port: 5432
```

```bash
# Apply (replace PG_IP with actual value)
sed "s/\${PG_IP}/$PG_IP/" /tmp/db-service.yaml | k apply -f -
```
</details>

### Task 2: Deploy PgBouncer as a Centralized Proxy

Deploy a PgBouncer Deployment with 2 replicas and a ClusterIP Service.

<details>
<summary>Solution</summary>

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
stringData:
  username: appadmin
  password: lab-secret-123
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      containers:
        - name: pgbouncer
          image: bitnami/pgbouncer:1.23.0
          ports:
            - containerPort: 6432
          env:
            - name: PGBOUNCER_DATABASE
              value: appdb
            - name: POSTGRESQL_HOST
              value: app-database
            - name: POSTGRESQL_PORT
              value: "5432"
            - name: POSTGRESQL_USERNAME
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: POSTGRESQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            - name: PGBOUNCER_POOL_MODE
              value: transaction
            - name: PGBOUNCER_DEFAULT_POOL_SIZE
              value: "10"
          readinessProbe:
            tcpSocket:
              port: 6432
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: pgbouncer
spec:
  selector:
    app: pgbouncer
  ports:
    - port: 5432
      targetPort: 6432
```

```bash
k apply -f /tmp/pgbouncer.yaml
k wait --for=condition=ready pod -l app=pgbouncer --timeout=60s
```
</details>

### Task 3: Test Connectivity Through PgBouncer

Run a test pod that connects through PgBouncer and creates a table.

<details>
<summary>Solution</summary>

```bash
k run db-test --rm -it --image=postgres:16 --restart=Never -- \
  psql "postgresql://appadmin:lab-secret-123@pgbouncer:5432/appdb" \
  -c "CREATE TABLE test_connection (id serial PRIMARY KEY, created_at timestamp DEFAULT now());
      INSERT INTO test_connection DEFAULT VALUES;
      SELECT * FROM test_connection;"
```
</details>

### Task 4: Simulate a Schema Migration Job

Create a Kubernetes Job that runs a migration script.

<details>
<summary>Solution</summary>

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: migration-v1
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: postgres:16
          command:
            - psql
            - "postgresql://appadmin:lab-secret-123@pgbouncer:5432/appdb"
            - -c
            - |
              BEGIN;
              SET lock_timeout = '5s';
              CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
              );
              INSERT INTO users (email, name) VALUES
                ('alice@example.com', 'Alice'),
                ('bob@example.com', 'Bob');
              COMMIT;
```

```bash
k apply -f /tmp/migration-job.yaml
k wait --for=condition=complete job/migration-v1 --timeout=30s
k logs job/migration-v1
```
</details>

### Task 5: Verify Read/Write Split

Create a second endpoint Service simulating a read replica and test routing.

<details>
<summary>Solution</summary>

```bash
# Create read-only Service (same PostgreSQL in this lab, but separate Service)
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: db-read
spec:
  clusterIP: None
  ports:
    - port: 5432
EOF

# Create Endpoints pointing to same PG (simulating a read replica)
cat <<EOF | k apply -f -
apiVersion: v1
kind: Endpoints
metadata:
  name: db-read
subsets:
  - addresses:
      - ip: "$PG_IP"
    ports:
      - port: 5432
EOF

# Test reading from the "replica"
k run read-test --rm -it --image=postgres:16 --restart=Never -- \
  psql "postgresql://appadmin:lab-secret-123@db-read:5432/appdb" \
  -c "SELECT * FROM users;"
```
</details>

### Task 6: Simulate Credential Rotation

Implement a manual credential rotation to see how workloads behave when secrets change.

<details>
<summary>Solution</summary>

```bash
# 1. Create a dummy Deployment using the secret
cat <<EOF | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-worker
  template:
    metadata:
      labels:
        app: api-worker
    spec:
      containers:
        - name: worker
          image: postgres:16
          command: ["sleep", "3600"]
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
EOF

k wait --for=condition=available deployment/api-worker --timeout=30s

# 2. Update the secret in Kubernetes (simulating an external rotation)
k create secret generic db-credentials \
  --from-literal=username=appadmin \
  --from-literal=password=new-rotated-secret-456 \
  --dry-run=client -o yaml | k apply -f -

# 3. Notice the pod doesn't automatically get the new password
# In a real environment, you need Reloader to trigger this automatically
k rollout restart deployment api-worker
k rollout status deployment api-worker

# 4. Verify the new pod has the new password
k exec deploy/api-worker -- env | grep DB_PASSWORD
```
</details>

### Success Criteria

- [ ] ExternalName/headless Service resolves to PostgreSQL container
- [ ] PgBouncer Deployment has 2 ready replicas
- [ ] Test pod connects through PgBouncer successfully
- [ ] Migration Job completes and creates the `users` table
- [ ] Read endpoint returns data from the simulated replica
- [ ] Credential rotation successfully triggers new pod creation via rollout

### Cleanup

```bash
kind delete cluster --name db-lab
docker rm -f lab-postgres
docker network rm db-lab
```

---

**Next Module**: [Module 9.2: Managed Message Brokers & Event-Driven Kubernetes](../module-9.2-message-brokers/) -- Learn how to integrate SQS, Pub/Sub, and Service Bus with Kubernetes workloads, and use KEDA to autoscale consumers based on queue depth.

## Sources

- [docs.aws.amazon.com: USER VPC.WorkingWithRDSInstanceinaVPC.html](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html) — AWS documents that RDS instances in a VPC have private IPs and can be hidden from the public internet.
- [docs.aws.amazon.com: rds secrets manager.html](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html) — The RDS Secrets Manager documentation explicitly ties this CLI flag to automatic password generation and lifecycle management in Secrets Manager.
- [github.com: external secrets](https://github.com/external-secrets/external-secrets) — The upstream project README explicitly states this core ESO behavior.
- [docs.aws.amazon.com: tutorials rotation alternating.html](https://docs.aws.amazon.com/secretsmanager/latest/userguide/tutorials_rotation-alternating.html) — AWS explicitly recommends alternating-users rotation when high availability is required.
- [github.com: Reloader](https://github.com/stakater/Reloader) — The upstream README documents automatic rollout behavior on Secret and ConfigMap updates.
- [argo-cd.readthedocs.io: sync waves](https://argo-cd.readthedocs.io/en/latest/user-guide/sync-waves/) — Argo CD's sync phases documentation explicitly defines `PreSync` as executing prior to manifest application.
- [docs.aws.amazon.com: Concepts.MultiAZ.html](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html) — AWS explicitly distinguishes single-standby Multi-AZ DB instances from Multi-AZ DB clusters that can serve reads.
- [cloud.google.com: cross region replicas](https://cloud.google.com/sql/docs/postgres/replication/cross-region-replicas) — Google Cloud documents cross-region replicas as a Cloud SQL feature for migration and DR.
- [learn.microsoft.com: concepts read replicas geo](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-read-replicas-geo) — Microsoft documents geo-replication as cross-region replica support for Flexible Server.
- [aws.amazon.com: optimizing data transfer costs when using aws network load balancer](https://aws.amazon.com/blogs/networking-and-content-delivery/optimizing-data-transfer-costs-when-using-aws-network-load-balancer/) — An official AWS networking post states the current inter-zone charge as $0.01 per GB in each direction.
- [cloud.google.com: pricing](https://cloud.google.com/vpc/pricing) — Google's VPC pricing page lists same-region inter-zone VM traffic at $0.01 per GiB and states Cloud SQL same-region pricing follows VM-to-VM rates.
- [azure.microsoft.com: bandwidth](https://azure.microsoft.com/en-us/pricing/details/bandwidth) — Azure's bandwidth pricing FAQ says data transfer between Azure services in the same region is not charged.
- [kubernetes.io: storage classes](https://kubernetes.io/docs/concepts/storage/storage-classes/) — The Kubernetes StorageClass documentation directly defines both the default and the purpose of `WaitForFirstConsumer`.
- [docs.aws.amazon.com: reboot db instance.html](https://docs.aws.amazon.com/cli/v1/reference/rds/reboot-db-instance.html) — The AWS CLI command reference explicitly documents the `--force-failover` option.
- [Service | Kubernetes](https://kubernetes.io/docs/concepts/services-networking/service/) — Explains `ExternalName`, headless Services, and the DNS behavior the module relies on for stable database hostnames.
- [Learn about using private IP | Cloud SQL](https://cloud.google.com/sql/docs/sqlserver/private-ip) — Clarifies Cloud SQL private IP connectivity and helps separate private services access from Private Service Connect.
