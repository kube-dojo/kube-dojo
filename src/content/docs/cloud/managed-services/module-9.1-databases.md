---
title: "Module 9.1: Relational Database Integration (RDS / Cloud SQL / Flexible Server)"
slug: cloud/managed-services/module-9.1-databases
sidebar:
  order: 2
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Cloud Essentials (any provider), Kubernetes networking basics

## Why This Module Matters

In September 2022, a Series B fintech startup ran their PostgreSQL database as a StatefulSet inside EKS. They had read every blog post about "running databases on Kubernetes" and felt confident. One Friday at 4:47 PM, a node auto-scaling event drained the database pod. The PersistentVolume was in us-east-1a, but the replacement node landed in us-east-1b. The pod sat in `Pending` for 22 minutes. During those 22 minutes, their payment processing pipeline -- which served 14,000 transactions per hour -- was completely dead. The postmortem estimated $89,000 in lost revenue and two enterprise customers who never came back.

The startup migrated to Amazon RDS the following Monday. Not because Kubernetes cannot run databases -- it absolutely can -- but because managed databases handle the hardest parts of database operations: automated failover, point-in-time recovery, patching, and cross-AZ replication. The real engineering challenge shifted from "keeping PostgreSQL alive" to "connecting Kubernetes workloads to managed databases securely, efficiently, and reliably."

This module teaches you the second part. You will learn how to connect Kubernetes pods to managed relational databases across all three major clouds using private networking, connection pooling, credential rotation, schema migrations in a GitOps workflow, and high-availability patterns that survive AZ failures without your on-call engineer losing sleep.

---

## Private Network Connectivity

The first rule of database connectivity from Kubernetes: **never expose your database to the public internet**. Every cloud provider offers private endpoint mechanisms that keep traffic on the provider's backbone network.

### Architecture: VPC-Native Connectivity

```
+---------------------------+          +---------------------------+
|   Kubernetes VPC          |          |   Database Service        |
|                           |          |                           |
|  +------+   +------+     |          |   +------------------+    |
|  | Pod A |   | Pod B |    |   VPC    |   |  Primary (AZ-a)  |    |
|  +---+---+   +---+---+    | Peering/ |   +------------------+    |
|      |           |        | Private  |                           |
|  +---+-----------+---+    | Endpoint |   +------------------+    |
|  | ClusterIP Service |----+----------+-->|  Replica (AZ-b)  |    |
|  +-------------------+    |          |   +------------------+    |
+---------------------------+          +---------------------------+
```

### AWS: RDS with VPC Private Subnets

On AWS, your EKS cluster and RDS instance should share the same VPC or use VPC peering. RDS instances deployed into private subnets are accessible from any resource within the VPC.

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

The `--manage-master-user-password` flag tells RDS to store the master password in AWS Secrets Manager automatically. No human ever sees or handles the password.

### GCP: Cloud SQL with Private Service Connect

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

### Azure: Flexible Server with Private Endpoint

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

Every database connection consumes memory on the server (roughly 5-10 MB per connection for PostgreSQL). Kubernetes makes this worse because pods scale horizontally. If you have 20 replicas, each maintaining a pool of 10 connections, that is 200 connections. During a rolling deployment, both old and new pods exist simultaneously -- suddenly 400 connections.

Managed databases have connection limits. An RDS `db.r6g.large` instance supports roughly 1,600 connections, but performance degrades well before that ceiling. The answer is connection pooling.

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

For 90% of Kubernetes workloads, `transaction` mode is the correct choice. It provides the best balance of connection reuse and compatibility.

---

## Credential Rotation

Hardcoded database passwords in Kubernetes Secrets are a ticking time bomb. When you need to rotate them -- and you will -- you face a coordination problem: update the password in the database, update the Secret in Kubernetes, restart every pod that uses it, and do all of this without downtime.

### External Secrets Operator (ESO) with Rotation

ESO syncs secrets from cloud provider secret managers into Kubernetes Secrets automatically.

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

### Dual-User Rotation Strategy

The safest rotation pattern uses two database users, alternating between them:

```
Time 0:  user_a (active)    user_b (standby)
Time 1:  Rotate user_b password in Secrets Manager
Time 2:  Update K8s Secret to point to user_b
Time 3:  Rolling restart -- pods pick up user_b credentials
Time 4:  user_a (standby)   user_b (active)
Time 5:  Rotate user_a password (safe -- nobody using it)
```

This ensures zero-downtime rotation because the old credentials remain valid throughout the entire rollout.

```bash
# AWS Secrets Manager rotation with dual-user strategy
aws secretsmanager rotate-secret \
  --secret-id production/database/credentials \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789:function:db-rotation \
  --rotation-rules '{"AutomaticallyAfterDays": 30}'
```

### Triggering Pod Restarts on Secret Change

Use Reloader or stakater/Reloader to automatically trigger rolling restarts:

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

Never make breaking schema changes in a single step. Instead:

```
Phase 1: EXPAND   - Add new column (nullable or with default)
Phase 2: MIGRATE  - Application writes to both old and new columns
Phase 3: CONTRACT - Remove old column after all pods use new schema
```

### Kubernetes Job for Migrations

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

The `argocd.argoproj.io/hook: PreSync` annotation tells Argo CD to run this Job before deploying new application pods. The migration runs, the schema updates, then the new application version rolls out.

### Migration Safety Checklist

| Rule | Reason |
|------|--------|
| Never drop columns in the same release that removes their usage | Old pods still running during rollout will crash |
| Always add columns as nullable or with defaults | INSERT statements from old code won't fail |
| Use advisory locks in migration scripts | Prevents two migration Jobs from running simultaneously |
| Set a statement timeout | A single `ALTER TABLE` locking for 10 minutes will block all queries |
| Test rollback before applying | `migrate down` should always work |

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
| Failover time | 60-120 seconds | ~30 seconds | ~60 seconds |
| Read from standby | No (Multi-AZ), Yes (Multi-AZ Cluster) | No | No |
| Cross-region | Separate feature (Read Replicas) | Cross-region replicas | Geo-replication |
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

- **AWS**: $0.01/GB per direction between AZs
- **GCP**: $0.01/GB between zones in the same region
- **Azure**: Free within the same region (as of 2025)

If your application in AZ-a talks to a database in AZ-b, every query and response crosses AZ boundaries. For a chatty application doing 10,000 queries per second, each returning 1 KB, that is roughly 864 GB/day -- about $17/day just in cross-AZ transfer.

**Mitigation strategies:**
1. Use topology-aware routing to prefer same-AZ replicas
2. Use connection pooling to reduce round-trips
3. Batch reads where possible
4. Cache frequently-accessed data (see Module 9.5)

---

## Did You Know?

1. **Amazon RDS manages over 1.2 million active database instances** as of 2024, making it by far the largest managed database fleet in the world. The service handles more than 350 billion transactions per day across all engines.

2. **PostgreSQL's maximum connection limit is not a hard cap** -- it is a function of available memory. Each connection uses a dedicated backend process consuming 5-10 MB of RAM. A db.r6g.xlarge instance (32 GB RAM) could theoretically support 3,200 connections but would have no memory left for actual query processing.

3. **Google Cloud SQL's "Private Service Connect" replaced the older VPC peering approach** in 2024 because VPC peering does not support transitive routing. If you had a hub-and-spoke network topology, Cloud SQL was unreachable from spoke VPCs -- a painful limitation that caught many multi-project architectures.

4. **Schema migration tools have been the #1 cause of production outages** at companies surveyed by the DORA team, ahead of bad deployments. The most common failure: a migration adds an index on a 500-million-row table without `CONCURRENTLY`, locking writes for 45 minutes.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Exposing the database with a public IP "for debugging" | Developers need to query from laptops | Use `kubectl port-forward` to a pod with database access |
| Not setting `volumeBindingMode: WaitForFirstConsumer` when self-hosting | Default StorageClass creates volumes immediately | Does not apply to managed DBs, but remember for dev environments |
| Allowing unlimited connections from pods | No connection pooling configured | Deploy PgBouncer (sidecar or centralized) with explicit limits |
| Storing database passwords in ConfigMaps | Confusion between ConfigMap and Secret | Use Secrets, and preferably ESO with a cloud secret manager |
| Running migrations in application startup code | Seems convenient -- every pod migrates on boot | Use a dedicated Job (PreSync hook) so migration runs exactly once |
| Ignoring cross-AZ data transfer costs | Not visible until the bill arrives | Monitor with VPC Flow Logs and use topology-aware routing |
| Using `session` pool mode in PgBouncer by default | It is the default setting | Explicitly set `transaction` mode for web workloads |
| Not testing database failover | "Multi-AZ handles it" | Schedule quarterly failover tests using `aws rds reboot-db-instance --force-failover` |

---

## Quiz

<details>
<summary>1. Why should you use an ExternalName Service to point to your managed database instead of hardcoding the endpoint in application config?</summary>

An ExternalName Service provides a layer of indirection. Your application connects to `db-write.production.svc.cluster.local`, and the actual database endpoint is defined in one place. If you migrate from RDS to Cloud SQL, or change regions, or switch to a different instance, you update the Service definition once rather than reconfiguring every application Deployment. This also makes it easy to swap endpoints for testing -- point the Service at a test database without touching application code.
</details>

<details>
<summary>2. What is the difference between PgBouncer's `transaction` and `session` pool modes, and why does `transaction` mode work better for Kubernetes workloads?</summary>

In `session` mode, a server connection is assigned to a client for the entire session (until disconnect). In `transaction` mode, the server connection is returned to the pool after each transaction completes. Kubernetes workloads benefit from `transaction` mode because pods scale horizontally, creating many concurrent clients. Transaction pooling multiplexes hundreds of client connections over a small pool of server connections, reducing the load on the database. The tradeoff is that session-level features like PREPARE, LISTEN/NOTIFY, and SET statements do not work in transaction mode.
</details>

<details>
<summary>3. Explain the expand-contract pattern for database schema migrations. Why is it necessary in a Kubernetes environment?</summary>

The expand-contract pattern splits breaking schema changes into safe phases. First, you "expand" by adding new columns or tables (backward-compatible). Then you deploy code that writes to both old and new structures. Finally, you "contract" by removing the old columns. In Kubernetes, this is necessary because rolling deployments mean old and new application versions run simultaneously. If you drop a column that old pods still reference, those pods crash immediately. The pattern ensures every version of your application can work with the current schema.
</details>

<details>
<summary>4. What happens during an RDS Multi-AZ failover, and how does Kubernetes handle it?</summary>

During an RDS Multi-AZ failover, AWS promotes the standby instance in another AZ to primary. The DNS CNAME record for the RDS endpoint is updated to point to the new primary (this takes 60-120 seconds). Kubernetes pods using the ExternalName Service will automatically resolve to the new IP after the DNS TTL expires. During the failover window, database connections will fail. Applications must implement retry logic with exponential backoff. PgBouncer helps here by queuing client requests briefly during the failover rather than immediately returning errors.
</details>

<details>
<summary>5. How does cross-AZ data transfer affect costs when your pods and database are in different Availability Zones?</summary>

Cross-AZ data transfer costs $0.01/GB per direction on AWS and GCP (Azure is free within the same region as of 2025). For a chatty application making thousands of queries per second, this can add up to hundreds of dollars per month. The cost is bilateral -- both the query and the response incur charges. Mitigation strategies include topology-aware routing to prefer same-AZ database replicas, connection pooling to reduce round-trips, read caching, and query batching.
</details>

<details>
<summary>6. Why does the Argo CD PreSync hook use `backoffLimit: 0` for database migration Jobs?</summary>

Setting `backoffLimit: 0` means the Job will not retry if the migration fails. This is intentional -- database migrations should not be retried automatically because a partial migration that failed midway could cause data corruption or duplicate schema changes if rerun. If the migration fails, the PreSync hook fails, which prevents Argo CD from deploying the new application version. The engineer must investigate the failure, fix the migration, and redeploy manually. This fail-fast behavior is a safety mechanism.
</details>

<details>
<summary>7. What is the dual-user rotation strategy and why is it safer than rotating a single user's password?</summary>

The dual-user strategy maintains two database users (e.g., user_a and user_b). At any time, one is "active" (used by pods) and one is "standby." To rotate, you change the standby user's password, then update the Kubernetes Secret to point to the standby user, then do a rolling restart. Throughout this process, the old active user's password has not changed, so pods still running with old credentials continue to work. Only after all pods have rolled to the new credentials do you rotate the old user's password. Single-user rotation has a dangerous window where old pods have the old password but the database only accepts the new one.
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

### Success Criteria

- [ ] ExternalName/headless Service resolves to PostgreSQL container
- [ ] PgBouncer Deployment has 2 ready replicas
- [ ] Test pod connects through PgBouncer successfully
- [ ] Migration Job completes and creates the `users` table
- [ ] Read endpoint returns data from the simulated replica

### Cleanup

```bash
kind delete cluster --name db-lab
docker rm -f lab-postgres
docker network rm db-lab
```

---

**Next Module**: [Module 9.2: Managed Message Brokers & Event-Driven Kubernetes](../module-9.2-message-brokers/) -- Learn how to integrate SQS, Pub/Sub, and Service Bus with Kubernetes workloads, and use KEDA to autoscale consumers based on queue depth.
