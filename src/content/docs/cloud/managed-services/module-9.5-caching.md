---
title: "Module 9.5: Advanced Caching Services (ElastiCache / Memorystore)"
slug: cloud/managed-services/module-9.5-caching
sidebar:
  order: 6
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2h | **Prerequisites**: Module 9.1 (Databases), Module 9.4 (Object Storage), Redis fundamentals

## Why This Module Matters

In November 2023, an e-commerce platform ran their product catalog API on GKE. Every product page required three database queries: product details, pricing, and reviews. During a flash sale, traffic jumped from 3,000 to 45,000 requests per second. Cloud SQL hit its connection limit at 15,000 connections. The auto-scaler was adding pods, but each new pod opened more database connections, making the problem worse. The site went down for 28 minutes during peak sale time. Estimated lost revenue: $2.3 million.

The team had a Redis cluster running in GKE -- but it was a self-managed StatefulSet with 3 nodes and no monitoring. They did not discover until the postmortem that Redis had silently evicted 60% of the cache 20 minutes before the sale started due to a memory limit that nobody had reviewed since initial deployment. The database was hit with the full 45,000 RPS because the cache was effectively empty.

They migrated to Google Memorystore for Redis with proper memory sizing, connection limits, and eviction monitoring. The next sale handled 62,000 RPS with the database seeing only 800 QPS -- a 98% cache hit rate. Caching is not optional for production Kubernetes workloads. It is the difference between your database being a bottleneck and your database being a safety net.

---

## Redis vs Memcached: Choosing Your Engine

### Decision Matrix

| Factor | Redis | Memcached |
|--------|-------|-----------|
| Data structures | Strings, hashes, lists, sets, sorted sets, streams | Strings only (key-value) |
| Persistence | Optional (RDB snapshots, AOF) | None (pure cache) |
| Replication | Primary-replica with automatic failover | None (each node independent) |
| Clustering | Redis Cluster (data sharding) | Client-side sharding |
| Pub/Sub | Built-in | Not available |
| Lua scripting | Yes | No |
| Max item size | 512 MB | 1 MB (default) |
| Multi-threaded | Single-threaded (I/O threads since 6.0) | Multi-threaded |
| Best for | Complex caching, sessions, leaderboards, pub/sub | Simple key-value, large working sets, multi-threaded reads |

**For 90% of Kubernetes workloads, Redis is the right choice.** Memcached is simpler but far less capable. Choose Memcached only when you need pure key-value caching at extremely high throughput with no need for data structures, persistence, or replication.

### Managed Service Comparison

| Feature | AWS ElastiCache Redis | GCP Memorystore Redis | Azure Cache for Redis |
|---------|----------------------|----------------------|----------------------|
| Max memory | 6.1 TB (cluster mode) | 300 GB (standard) | 1.2 TB (Enterprise) |
| Cluster mode | Yes (up to 500 shards) | Yes (since 2024) | Yes (Premium/Enterprise) |
| Multi-AZ failover | Automatic | Automatic (Standard tier) | Automatic (Premium+) |
| Encryption at rest | Yes (KMS) | Yes (CMEK) | Yes (managed keys) |
| Encryption in transit | TLS | TLS | TLS |
| VPC integration | VPC subnets | VPC network | VNET injection |

---

## Caching Strategies

The "right" caching strategy depends on your read/write ratio and consistency requirements.

### Cache-Aside (Lazy Loading)

The most common pattern. The application checks the cache first; on a miss, it reads from the database and populates the cache.

```
  Client Request
       |
       v
  [Check Cache] --hit--> Return cached data
       |
      miss
       |
       v
  [Query Database]
       |
       v
  [Write to Cache]
       |
       v
  Return data
```

```python
import redis
import json

r = redis.Redis(host='redis-master.cache.svc', port=6379, decode_responses=True)

def get_product(product_id):
    # Step 1: Check cache
    cache_key = f"product:{product_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    # Step 2: Cache miss -- query database
    product = db.query("SELECT * FROM products WHERE id = %s", product_id)

    # Step 3: Populate cache with TTL
    r.setex(cache_key, 300, json.dumps(product))  # 5-minute TTL

    return product
```

**Pros**: Only caches data that is actually requested. Simple to implement.
**Cons**: Cache miss penalty (extra latency on first request). Data can become stale until TTL expires.

### Write-Through

Every write goes to both the cache and the database simultaneously.

```
  Write Request
       |
       v
  [Write to Cache] --> [Write to Database]
       |
       v
  Return success
```

```python
def update_product_price(product_id, new_price):
    # Write to database first
    db.execute("UPDATE products SET price = %s WHERE id = %s", new_price, product_id)

    # Update cache (same transaction boundary)
    product = db.query("SELECT * FROM products WHERE id = %s", product_id)
    cache_key = f"product:{product_id}"
    r.setex(cache_key, 300, json.dumps(product))

    return product
```

**Pros**: Cache is always consistent with the database. No stale reads after writes.
**Cons**: Write latency increases (two writes per operation). Caches data that may never be read.

### Write-Behind (Write-Back)

Writes go to the cache immediately and are asynchronously flushed to the database.

```
  Write Request
       |
       v
  [Write to Cache] --> Return success (fast!)
       |
       v (async, batched)
  [Flush to Database]
```

**Pros**: Extremely fast writes. Database load is smoothed by batching.
**Cons**: Risk of data loss if cache fails before flush. Complex to implement correctly. Not suitable for critical data.

### Strategy Selection Guide

| Scenario | Strategy | Why |
|----------|----------|-----|
| Product catalog (read-heavy) | Cache-aside | Most reads, occasional writes |
| User sessions | Write-through | Must be consistent after login/logout |
| Analytics counters | Write-behind | High write volume, eventual consistency OK |
| API rate limiting | Cache-aside + TTL | Natural expiration, no DB needed |
| Shopping cart | Write-through | Consistency critical for commerce |
| Leaderboard scores | Cache-aside + sorted sets | Redis sorted sets are purpose-built for this |

---

## Connecting Kubernetes to Managed Redis

### ElastiCache Redis from EKS

```bash
# Create ElastiCache Redis cluster
aws elasticache create-replication-group \
  --replication-group-id app-cache \
  --replication-group-description "App caching layer" \
  --engine redis --engine-version 7.1 \
  --cache-node-type cache.r7g.large \
  --num-cache-clusters 3 \
  --multi-az-enabled \
  --automatic-failover-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --cache-subnet-group-name eks-cache-subnets \
  --security-group-ids sg-0abc123def456
```

```yaml
# Kubernetes Service for Redis endpoint
apiVersion: v1
kind: Service
metadata:
  name: redis-primary
  namespace: cache
spec:
  type: ExternalName
  externalName: app-cache.abc123.ng.0001.use1.cache.amazonaws.com
---
apiVersion: v1
kind: Service
metadata:
  name: redis-reader
  namespace: cache
spec:
  type: ExternalName
  externalName: app-cache-ro.abc123.ng.0001.use1.cache.amazonaws.com
```

### Application Deployment with Redis

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
          image: mycompany/api-server:3.0.0
          env:
            - name: REDIS_PRIMARY_HOST
              value: redis-primary.cache.svc.cluster.local
            - name: REDIS_READER_HOST
              value: redis-reader.cache.svc.cluster.local
            - name: REDIS_PORT
              value: "6379"
            - name: REDIS_TLS_ENABLED
              value: "true"
            - name: REDIS_AUTH_TOKEN
              valueFrom:
                secretKeyRef:
                  name: redis-auth
                  key: token
            - name: REDIS_MAX_CONNECTIONS
              value: "20"
            - name: REDIS_CONNECT_TIMEOUT_MS
              value: "2000"
            - name: REDIS_COMMAND_TIMEOUT_MS
              value: "500"
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
```

---

## Cache Stampede Prevention

A cache stampede (also called "thundering herd") happens when a popular cache key expires and hundreds of pods simultaneously query the database to rebuild it.

```
Normal:
  100 pods --> [Cache HIT] --> Return cached data     (DB: 0 queries)

Stampede (key expires):
  100 pods --> [Cache MISS] --> 100 database queries  (DB: 100 queries)
                            --> 100 cache writes
```

### Prevention Strategies

#### 1. Probabilistic Early Expiration (PER)

Refresh the cache before it expires, with a probability that increases as the TTL decreases:

```python
import random
import time

def get_with_per(key, ttl=300, beta=1.0):
    """Probabilistic early refresh to prevent stampedes."""
    cached = r.get(key)
    if cached:
        data = json.loads(cached)
        remaining_ttl = r.ttl(key)
        # As TTL decreases, probability of refresh increases
        # beta controls aggressiveness (higher = earlier refresh)
        delta = ttl * beta * random.random()
        if remaining_ttl < delta:
            # This pod refreshes the cache early
            return refresh_cache(key, ttl)
        return data
    return refresh_cache(key, ttl)

def refresh_cache(key, ttl):
    data = db.query_product(key.split(':')[1])
    r.setex(key, ttl, json.dumps(data))
    return data
```

#### 2. Distributed Lock (Mutex)

Only one pod rebuilds the cache; others wait or serve stale data:

```python
def get_with_lock(key, ttl=300):
    cached = r.get(key)
    if cached:
        return json.loads(cached)

    lock_key = f"lock:{key}"
    # Try to acquire lock (NX = set if not exists, EX = expiry)
    acquired = r.set(lock_key, "1", nx=True, ex=10)

    if acquired:
        # This pod rebuilds the cache
        try:
            data = db.query_product(key.split(':')[1])
            r.setex(key, ttl, json.dumps(data))
            return data
        finally:
            r.delete(lock_key)
    else:
        # Another pod is rebuilding -- wait briefly, then retry
        time.sleep(0.1)
        cached = r.get(key)
        if cached:
            return json.loads(cached)
        # Fallback: query database directly (rare)
        return db.query_product(key.split(':')[1])
```

#### 3. Background Refresh (Never Expire)

Cache entries never expire. A background process refreshes them on a schedule:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cache-warmer
  namespace: production
spec:
  schedule: "*/4 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: warmer
              image: mycompany/cache-warmer:1.0.0
              env:
                - name: REDIS_HOST
                  value: redis-primary.cache.svc.cluster.local
              command:
                - python
                - -c
                - |
                  import redis, json
                  r = redis.Redis(host='redis-primary.cache.svc.cluster.local')

                  # Refresh top 1000 products
                  products = db.query("SELECT id FROM products ORDER BY view_count DESC LIMIT 1000")
                  for p in products:
                      data = db.query_product(p['id'])
                      r.setex(f"product:{p['id']}", 600, json.dumps(data))
                  print(f"Warmed {len(products)} products")
```

---

## Connection Limits and Pool Management

Managed Redis instances have maximum connection limits based on instance size. Exceeding them causes connection refused errors.

### Connection Budget

| Instance Type | Max Connections | With 50 pods (20 conn each) | Remaining |
|---------------|-----------------|------------------------------|-----------|
| cache.r7g.large | 65,000 | 1,000 | 64,000 |
| cache.r7g.xlarge | 65,000 | 1,000 | 64,000 |
| cache.t4g.micro | 65,000 | 1,000 | 64,000 |

Redis connection limits are generous, but the bottleneck is often on the client side. Each connection consumes memory and a file descriptor in the pod.

### Redis Connection Pooling

```python
# Good: Connection pool (shared connections)
import redis

pool = redis.ConnectionPool(
    host='redis-primary.cache.svc.cluster.local',
    port=6379,
    max_connections=20,       # Per pod
    socket_timeout=2.0,       # Fail fast
    socket_connect_timeout=1.0,
    retry_on_timeout=True,
    health_check_interval=30,
    ssl=True,
)
r = redis.Redis(connection_pool=pool)

# Bad: New connection per request (connection leak)
# r = redis.Redis(host='redis-primary.cache.svc.cluster.local')  # DON'T
```

### Monitoring Connection Usage

```yaml
# PrometheusRule for Redis connection alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: redis-alerts
  namespace: monitoring
spec:
  groups:
    - name: redis
      rules:
        - alert: RedisConnectionsHigh
          expr: redis_connected_clients / redis_config_maxclients > 0.8
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Redis connection usage above 80%"
        - alert: RedisCacheHitRateLow
          expr: |
            rate(redis_keyspace_hits_total[5m]) /
            (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) < 0.9
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Redis cache hit rate below 90%"
```

---

## Envoy Sidecar Caching

For HTTP-based APIs, you can add caching at the proxy layer using Envoy as a sidecar. This caches responses without modifying application code.

### Architecture

```
  Client
    |
    v
  K8s Service
    |
    v
  +--Pod---------------------------+
  |                                |
  |  Envoy Sidecar (port 8080)    |
  |    |                           |
  |    |--> [Local Cache]          |
  |    |        |                  |
  |    |       miss                |
  |    |        |                  |
  |    +--> App Container (8081)   |
  |                                |
  +--------------------------------+
```

### Envoy Cache Filter Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: envoy-cache-config
  namespace: production
data:
  envoy.yaml: |
    static_resources:
      listeners:
        - name: listener_0
          address:
            socket_address:
              address: 0.0.0.0
              port_value: 8080
          filter_chains:
            - filters:
                - name: envoy.filters.network.http_connection_manager
                  typed_config:
                    "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                    stat_prefix: ingress
                    http_filters:
                      - name: envoy.filters.http.cache
                        typed_config:
                          "@type": type.googleapis.com/envoy.extensions.filters.http.cache.v3.CacheConfig
                          typed_config:
                            "@type": type.googleapis.com/envoy.extensions.http.cache.simple_http_cache.v3.SimpleHttpCacheConfig
                      - name: envoy.filters.http.router
                        typed_config:
                          "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
                    route_config:
                      virtual_hosts:
                        - name: backend
                          domains: ["*"]
                          routes:
                            - match:
                                prefix: "/"
                              route:
                                cluster: local_app
      clusters:
        - name: local_app
          type: STATIC
          load_assignment:
            cluster_name: local_app
            endpoints:
              - lb_endpoints:
                  - endpoint:
                      address:
                        socket_address:
                          address: 127.0.0.1
                          port_value: 8081
```

Your application must return proper `Cache-Control` headers:

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/products/<product_id>')
def get_product(product_id):
    product = fetch_product(product_id)
    response = jsonify(product)
    response.headers['Cache-Control'] = 'public, max-age=60'
    return response
```

---

## Did You Know?

1. **Redis processes over 100,000 operations per second on a single core** in typical workloads. Despite being single-threaded for command execution, Redis achieves this throughput because it operates entirely in memory and uses efficient data structures like skip lists and hash tables. Since version 6.0, I/O threading handles network reads/writes on separate threads while command execution remains single-threaded.

2. **The term "cache stampede" was formally studied in a 2009 paper** titled "Optimal Probabilistic Cache Stampede Prevention" by Vattani, Chierichetti, and Lowenstein. The "probabilistic early expiration" technique from that paper is now standard practice at companies like Facebook, where cache stampedes on popular content could otherwise bring down entire database clusters.

3. **AWS ElastiCache Serverless (launched 2023) automatically scales Redis** with no capacity planning required. It charges per ECPU (ElastiCache Compute Unit) and per GB of storage, eliminating the need to choose instance types. For workloads with variable traffic, this can reduce costs by 40-60% compared to provisioned instances.

4. **Google Memorystore for Redis Cluster** became generally available in 2024, supporting up to 25 shards with 250 GB total capacity. Before this, GCP customers who needed Redis clustering had to self-manage Redis on GKE or use third-party services -- a gap that existed for over five years.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Not setting TTL on cache entries | "We will invalidate manually" | Always set TTL as a safety net, even with manual invalidation |
| Using the same Redis for cache and persistent data | "One cluster is simpler" | Separate cache (can be flushed) from persistent data (sessions, queues) |
| Ignoring memory eviction policy | Default is `noeviction` (errors when full) | Set `maxmemory-policy allkeys-lru` for cache workloads |
| Opening new Redis connection per request | Framework default or developer habit | Use connection pooling; configure `max_connections` per pod |
| No monitoring of cache hit rate | "It is just a cache, it either works or it does not" | Track hit rate, memory usage, evictions, and connection count |
| Caching errors/null results | Cache miss returns null, null gets cached | Check for valid data before caching; use "negative cache" with short TTL only intentionally |
| No circuit breaker when Redis is down | Redis failure cascades to database overload | Implement circuit breaker; serve stale data or degrade gracefully |
| Storing serialized objects larger than 100 KB | Convenient to cache entire API responses | Cache individual fields or use Redis hashes; large values cause latency spikes |

---

## Quiz

<details>
<summary>1. Explain the cache-aside pattern and when you would use write-through instead.</summary>

Cache-aside (lazy loading) means the application first checks the cache, and on a miss, queries the database and populates the cache. Data is only cached when requested. Use it for read-heavy workloads where most data is rarely accessed. Write-through writes to both cache and database on every write operation. Use it when consistency between cache and database is critical -- for example, shopping carts or user session data where reading stale data after a write is unacceptable. Write-through has higher write latency but guarantees the cache is always up-to-date.
</details>

<details>
<summary>2. What is a cache stampede and describe two different strategies to prevent it.</summary>

A cache stampede occurs when a popular cache key expires and many concurrent requests simultaneously miss the cache and hit the database. Two prevention strategies: (1) Distributed locking -- when a cache miss occurs, the first request acquires a lock and rebuilds the cache while other requests either wait or serve stale data. The lock prevents multiple pods from querying the database simultaneously. (2) Probabilistic early expiration -- before the TTL expires, each request has an increasing probability of refreshing the cache. This spreads cache rebuilding over time so only one or two requests refresh the cache before it actually expires, preventing the sudden stampede.
</details>

<details>
<summary>3. Why should you separate your Redis cache instance from your Redis persistent data store?</summary>

A cache instance can be flushed, restarted, or scaled without data loss -- the database is the source of truth. A persistent data store (sessions, job queues, rate limiters) contains data that cannot be regenerated from the database. If you use the same instance for both, memory pressure from cache entries can cause eviction of persistent data, or a cache flush operation can accidentally destroy session data. Different eviction policies are appropriate too: `allkeys-lru` for cache (evict least-recently-used when full) vs `noeviction` for persistent data (reject writes rather than lose data).
</details>

<details>
<summary>4. How do you calculate the connection budget for a Redis instance in a Kubernetes cluster?</summary>

Multiply the maximum number of pods by the connection pool size per pod. For example, 50 pods with `max_connections=20` each requires 1,000 connections. During rolling deployments, both old and new pods exist, so double this to 2,000. Add connections for monitoring tools, CronJobs, and any other clients. The total must be well under the Redis instance's max connection limit. For managed Redis (ElastiCache, Memorystore), the default limit is typically 65,000, but the practical limit is lower because each connection consumes memory on the Redis server. Monitor `redis_connected_clients` and alert at 80% capacity.
</details>

<details>
<summary>5. When would you use Envoy sidecar caching instead of application-level Redis caching?</summary>

Envoy sidecar caching is best when you cannot modify the application code (third-party services, legacy applications) or when you want HTTP-level caching that respects standard Cache-Control headers. It requires no application changes -- just proper HTTP cache headers. It caches at the pod level, reducing calls to the backend service. However, it is limited to HTTP responses and cannot cache arbitrary data structures like Redis can. Use application-level Redis caching when you need to cache database query results, computed values, or complex data structures that are not tied to specific HTTP endpoints.
</details>

<details>
<summary>6. What happens when Redis reaches its memory limit and the eviction policy is set to `noeviction`?</summary>

With `noeviction` policy, Redis returns an error (OOM -- Out of Memory) for any write command when the memory limit is reached. Read commands continue to work. This is the default policy and is appropriate for persistent data stores where data loss is unacceptable. For cache workloads, this is problematic because new cache entries cannot be written, causing all cache misses to fall through to the database. Cache workloads should use `allkeys-lru` (evict least recently used keys) or `volatile-lru` (evict least recently used keys with a TTL set), which make room for new entries by removing old ones.
</details>

---

## Hands-On Exercise: Redis Caching with Stampede Prevention

### Setup

```bash
# Create kind cluster
kind create cluster --name cache-lab

# Install Redis
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install redis bitnami/redis \
  --namespace cache --create-namespace \
  --set architecture=standalone \
  --set auth.password=cache-lab-pass \
  --set master.persistence.enabled=false \
  --set master.resources.requests.memory=128Mi
k wait --for=condition=ready pod -l app.kubernetes.io/name=redis \
  --namespace cache --timeout=120s
```

### Task 1: Implement Cache-Aside Pattern

Deploy a pod that demonstrates cache-aside with Redis.

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -n cache -f -
apiVersion: v1
kind: Pod
metadata:
  name: cache-aside-demo
spec:
  restartPolicy: Never
  containers:
    - name: demo
      image: python:3.12-slim
      command:
        - /bin/sh
        - -c
        - |
          pip install redis -q
          python3 << 'PYEOF'
          import redis
          import json
          import time

          r = redis.Redis(
              host='redis-master.cache.svc.cluster.local',
              port=6379,
              password='cache-lab-pass',
              decode_responses=True,
              socket_timeout=2.0,
              max_connections=10,
          )

          # Simulated database
          DATABASE = {
              "prod-101": {"name": "Widget Pro", "price": 29.99, "stock": 150},
              "prod-102": {"name": "Gadget Max", "price": 49.99, "stock": 75},
              "prod-103": {"name": "Tool Kit", "price": 89.99, "stock": 200},
          }

          def get_product(product_id):
              """Cache-aside pattern."""
              cache_key = f"product:{product_id}"

              # Step 1: Check cache
              cached = r.get(cache_key)
              if cached:
                  print(f"  CACHE HIT: {product_id}")
                  return json.loads(cached)

              # Step 2: Cache miss -- "query database"
              print(f"  CACHE MISS: {product_id} (querying DB)")
              time.sleep(0.05)  # Simulate DB latency
              product = DATABASE.get(product_id)

              if product:
                  # Step 3: Populate cache (TTL = 60 seconds)
                  r.setex(cache_key, 60, json.dumps(product))

              return product

          # Demo: First call is a miss, second is a hit
          print("=== Cache-Aside Demo ===")
          for round_num in range(1, 4):
              print(f"\nRound {round_num}:")
              for pid in ["prod-101", "prod-102", "prod-103"]:
                  result = get_product(pid)

          # Show cache stats
          info = r.info("stats")
          print(f"\nHits: {info['keyspace_hits']}, Misses: {info['keyspace_misses']}")
          hit_rate = info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']) * 100
          print(f"Hit rate: {hit_rate:.1f}%")
          PYEOF
EOF

k wait --for=condition=ready pod/cache-aside-demo -n cache --timeout=60s
sleep 5
k logs cache-aside-demo -n cache
```
</details>

### Task 2: Demonstrate Cache Stampede

Simulate a stampede by launching many concurrent requests after a cache key expires.

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -n cache -f -
apiVersion: v1
kind: Pod
metadata:
  name: stampede-demo
spec:
  restartPolicy: Never
  containers:
    - name: demo
      image: python:3.12-slim
      command:
        - /bin/sh
        - -c
        - |
          pip install redis -q
          python3 << 'PYEOF'
          import redis
          import json
          import time
          import threading

          r = redis.Redis(
              host='redis-master.cache.svc.cluster.local',
              port=6379,
              password='cache-lab-pass',
              decode_responses=True,
          )

          db_queries = {"count": 0}
          lock = threading.Lock()

          def simulate_db_query():
              """Simulate an expensive database query."""
              with lock:
                  db_queries["count"] += 1
              time.sleep(0.1)  # 100ms DB latency
              return {"name": "Popular Product", "price": 99.99}

          def get_without_protection(product_id):
              """No stampede protection -- every miss hits DB."""
              cached = r.get(f"product:{product_id}")
              if cached:
                  return json.loads(cached)
              data = simulate_db_query()
              r.setex(f"product:{product_id}", 5, json.dumps(data))
              return data

          def get_with_lock_protection(product_id):
              """Distributed lock prevents stampede."""
              cache_key = f"product:{product_id}"
              cached = r.get(cache_key)
              if cached:
                  return json.loads(cached)

              lock_key = f"lock:{cache_key}"
              acquired = r.set(lock_key, "1", nx=True, ex=5)

              if acquired:
                  try:
                      data = simulate_db_query()
                      r.setex(cache_key, 5, json.dumps(data))
                      return data
                  finally:
                      r.delete(lock_key)
              else:
                  time.sleep(0.15)  # Wait for rebuilder
                  cached = r.get(cache_key)
                  return json.loads(cached) if cached else simulate_db_query()

          # Test 1: Without protection
          r.flushall()
          db_queries["count"] = 0
          threads = []
          for i in range(50):
              t = threading.Thread(target=get_without_protection, args=("hot-product",))
              threads.append(t)
              t.start()
          for t in threads:
              t.join()
          print(f"WITHOUT protection: {db_queries['count']} DB queries from 50 requests")

          # Test 2: With lock protection
          r.flushall()
          db_queries["count"] = 0
          threads = []
          for i in range(50):
              t = threading.Thread(target=get_with_lock_protection, args=("hot-product",))
              threads.append(t)
              t.start()
          for t in threads:
              t.join()
          print(f"WITH lock protection: {db_queries['count']} DB queries from 50 requests")
          PYEOF
EOF

k wait --for=condition=ready pod/stampede-demo -n cache --timeout=60s
sleep 10
k logs stampede-demo -n cache
```
</details>

### Task 3: Monitor Redis Metrics

Create a pod that reports Redis statistics.

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -n cache -f -
apiVersion: v1
kind: Pod
metadata:
  name: redis-monitor
spec:
  restartPolicy: Never
  containers:
    - name: monitor
      image: redis:7
      command:
        - /bin/sh
        - -c
        - |
          echo "=== Redis Health Report ==="
          echo ""

          echo "--- Memory ---"
          redis-cli -h redis-master -a cache-lab-pass INFO memory 2>/dev/null | grep -E "used_memory_human|maxmemory_human|mem_fragmentation"

          echo ""
          echo "--- Clients ---"
          redis-cli -h redis-master -a cache-lab-pass INFO clients 2>/dev/null | grep -E "connected_clients|blocked_clients|maxclients"

          echo ""
          echo "--- Stats ---"
          redis-cli -h redis-master -a cache-lab-pass INFO stats 2>/dev/null | grep -E "keyspace_hits|keyspace_misses|evicted_keys|total_commands"

          echo ""
          echo "--- Keyspace ---"
          redis-cli -h redis-master -a cache-lab-pass INFO keyspace 2>/dev/null

          echo ""
          echo "--- Eviction Policy ---"
          redis-cli -h redis-master -a cache-lab-pass CONFIG GET maxmemory-policy 2>/dev/null

          echo ""
          echo "=== Report Complete ==="
EOF

k wait --for=condition=ready pod/redis-monitor -n cache --timeout=30s
sleep 3
k logs redis-monitor -n cache
```
</details>

### Task 4: Configure Eviction Policy

Change the Redis eviction policy and demonstrate eviction behavior.

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -n cache -f -
apiVersion: v1
kind: Pod
metadata:
  name: eviction-demo
spec:
  restartPolicy: Never
  containers:
    - name: demo
      image: python:3.12-slim
      command:
        - /bin/sh
        - -c
        - |
          pip install redis -q
          python3 << 'PYEOF'
          import redis

          r = redis.Redis(
              host='redis-master.cache.svc.cluster.local',
              port=6379,
              password='cache-lab-pass',
              decode_responses=True,
          )

          # Set a small maxmemory for demonstration
          r.config_set('maxmemory', '1mb')
          r.config_set('maxmemory-policy', 'allkeys-lru')
          print("Set maxmemory=1MB, policy=allkeys-lru")

          # Fill cache until evictions happen
          evicted_before = int(r.info('stats')['evicted_keys'])
          for i in range(5000):
              r.set(f"item:{i}", "x" * 200)  # ~200 bytes each

          evicted_after = int(r.info('stats')['evicted_keys'])
          total_keys = r.dbsize()

          print(f"Attempted to write 5000 keys")
          print(f"Keys in Redis: {total_keys}")
          print(f"Keys evicted: {evicted_after - evicted_before}")
          print(f"Eviction policy working correctly: {evicted_after > evicted_before}")

          # Reset maxmemory
          r.config_set('maxmemory', '0')
          r.flushall()
          PYEOF
EOF

k wait --for=condition=ready pod/eviction-demo -n cache --timeout=60s
sleep 8
k logs eviction-demo -n cache
```
</details>

### Success Criteria

- [ ] Cache-aside demo shows cache hits on second and third rounds
- [ ] Stampede demo shows fewer DB queries with lock protection
- [ ] Redis monitor reports memory, clients, and keyspace stats
- [ ] Eviction demo shows allkeys-lru evicting keys when memory is full

### Cleanup

```bash
kind delete cluster --name cache-lab
```

---

**Next Module**: [Module 9.6: Search & Analytics Engines (OpenSearch / Elasticsearch)](../module-9.6-search/) -- Learn how to ingest Kubernetes logs into managed search engines, configure index lifecycle management, and optimize queries for operational analytics.
