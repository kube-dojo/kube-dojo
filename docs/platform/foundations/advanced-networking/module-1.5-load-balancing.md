# Module 1.5: Cloud Load Balancing Deep Dive

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 3 hours
>
> **Prerequisites**: [Module 1.1: DNS at Scale](module-1.1-dns-at-scale.md), basic understanding of TCP/IP and HTTP
>
> **Track**: Foundations — Advanced Networking

---

**November 14, 2023. AWS experiences an extended outage in us-east-1. Thousands of applications go offline. But a curious pattern emerges in the post-incident analysis: applications using Network Load Balancers (NLBs) recovered faster than those on Application Load Balancers (ALBs). Applications with properly configured health checks and connection draining experienced near-zero user-visible errors during failover. Applications without them dropped thousands of in-flight requests.**

The difference between graceful degradation and catastrophic failure during that outage came down to load balancing configuration — not the load balancers themselves, but how engineers configured health checks, draining timeouts, cross-zone settings, and connection handling. The same infrastructure, the same outage, wildly different outcomes.

This pattern repeats across every major cloud incident. Load balancers are the front door to every serious application, handling connection management, TLS termination, health monitoring, and traffic distribution. Yet most engineers treat them as black boxes — click a few settings in the console and forget about them. When the load balancer behaves unexpectedly during a failure, they have no mental model for what's happening and no tools to debug it.

This module opens the black box. You'll understand exactly how L4 and L7 load balancers work, why their differences matter for your architecture, and how to configure them for resilience instead of just convenience.

---

## Why This Module Matters

Every request to your production application passes through a load balancer. It's the single most impactful piece of infrastructure between your users and your code. Get it right, and your application handles failures gracefully, scales seamlessly, and maintains consistent performance. Get it wrong, and you'll spend 3 AM incidents debugging connection resets, asymmetric routing, lost client IPs, and mysterious 502 errors.

Cloud load balancers are deceptively simple to set up and deceptively complex to operate well. The default settings work for demos. Production requires understanding connection draining (how long to wait before killing active connections), health check tuning (fast enough to detect failures, slow enough to avoid false positives), cross-zone load balancing (and its cost implications), Proxy Protocol (preserving client IPs through L4 proxies), and the fundamental architectural differences between L4 and L7 load balancing.

> **The Traffic Cop vs The Hotel Concierge**
>
> An L4 load balancer is like a traffic cop at an intersection. It sees cars (packets) and directs them to different lanes (servers) based on simple rules — it doesn't know or care what's inside the cars. An L7 load balancer is like a hotel concierge. It opens your luggage (HTTP request), reads your reservation (path, headers, cookies), and personally escorts you to the right room (backend). The concierge is smarter but slower. The traffic cop handles more throughput but can't make content-aware decisions.

---

## What You'll Learn

- L4 vs L7 load balancing: mechanics, trade-offs, and when to use each
- Connection draining: graceful shutdown without dropping requests
- Session affinity: sticky sessions and their hidden costs
- Proxy Protocol v1 and v2: preserving client IP through L4 proxies
- Cross-zone load balancing: behavior, costs, and failure domains
- Cloud LB architectures: AWS NLB/ALB, Google Maglev, Azure LB
- Hands-on: NLB with Proxy Protocol, upstream Kubernetes Ingress, verifying client IP preservation

---

## Part 1: L4 vs L7 Load Balancing

### 1.1 Layer 4 Load Balancing

```
LAYER 4 LOAD BALANCING (Transport Layer)
═══════════════════════════════════════════════════════════════

L4 load balancers operate on TCP/UDP connections.
They see: Source IP, Source Port, Dest IP, Dest Port, Protocol.
They DON'T see: HTTP headers, URLs, cookies, request body.

HOW L4 LOAD BALANCING WORKS
─────────────────────────────────────────────────────────────

    Client 1.2.3.4:54321 → LB 10.0.0.1:443

    LB selects backend server (e.g., 10.0.1.5:443)

    Method 1: DSR (Direct Server Return)
    ─────────────────────────────────────────────
    LB rewrites destination MAC address.
    Packet goes to backend at L2.
    Backend responds DIRECTLY to client (bypasses LB).

    Client → LB → Backend
    Client ← ─ ─ ─ Backend  (response bypasses LB!)

    ✓ Massive throughput (LB only handles inbound)
    ✓ LB doesn't become bandwidth bottleneck
    ✗ LB can't inspect or modify responses
    ✗ Backend must be L2-adjacent to LB
    ✗ Backend must be configured to accept traffic for LB's IP

    Method 2: DNAT (Destination NAT)
    ─────────────────────────────────────────────
    LB rewrites destination IP to backend IP.
    Backend responds to LB. LB rewrites source back.

    Client → LB → Backend
    Client ← LB ← Backend

    ✓ Works across L3 networks
    ✓ LB sees all traffic (can do health tracking)
    ✗ LB handles both directions (bandwidth)
    ✗ Must maintain connection tracking table

    Method 3: Tunneling (IP-in-IP / GUE)
    ─────────────────────────────────────────────
    LB encapsulates packet in outer IP header.
    Backend decapsulates and responds directly.
    Used by Google Maglev, AWS NLB.

    Client → LB → [Outer IP → Backend][Original Packet]
    Client ← ─ ─ ─ Backend  (direct response)

L4 LOAD BALANCING ALGORITHMS
─────────────────────────────────────────────────────────────

    Round Robin:
        Server A → Server B → Server C → Server A → ...
        Simple, even distribution. No awareness of server load.

    Weighted Round Robin:
        Server A (weight 3): gets 3x traffic
        Server B (weight 1): gets 1x traffic
        Useful when servers have different capacity.

    Least Connections:
        Route to server with fewest active connections.
        Better than round robin when requests have varying duration.

    Source IP Hash (Consistent Hashing):
        hash(client_ip) % num_servers
        Same client always goes to same server.
        Used for basic session affinity at L4.

    Maglev Hashing (Google):
        Consistent hash with minimal disruption on server changes.
        When one server is removed, only 1/N traffic shifts.
        Used in Google Cloud Load Balancing.

L4 CHARACTERISTICS
─────────────────────────────────────────────────────────────
    Throughput:       Millions of connections/second
    Latency added:    <1ms (often microseconds)
    TLS:              Pass-through (backend handles TLS)
                      OR TLS termination (with SNI routing)
    Protocols:        Any TCP or UDP protocol
    Connection state: Tracked per 5-tuple
    Use cases:        Database traffic, non-HTTP protocols,
                      highest-performance requirements,
                      upstream to L7 load balancers
```

### 1.2 Layer 7 Load Balancing

```
LAYER 7 LOAD BALANCING (Application Layer)
═══════════════════════════════════════════════════════════════

L7 load balancers operate on HTTP/HTTPS.
They see EVERYTHING: URL, headers, cookies, body, method.
They must fully terminate the TCP and TLS connection.

HOW L7 LOAD BALANCING WORKS
─────────────────────────────────────────────────────────────

    Client ──TLS──→ L7 LB ──new connection──→ Backend

    1. Client opens TCP connection to LB
    2. TLS handshake completes (LB terminates TLS)
    3. Client sends HTTP request
    4. LB parses the full HTTP request
    5. LB applies routing rules (path, headers, etc.)
    6. LB opens NEW connection to selected backend
    7. LB forwards request to backend
    8. Backend responds to LB
    9. LB forwards response to client

    Two separate connections!
    ─────────────────────────────────────────────
    Client ←──Connection A──→ LB ←──Connection B──→ Backend

    This is why L7 LBs are also called "reverse proxies."

ROUTING CAPABILITIES
─────────────────────────────────────────────────────────────

    PATH-BASED ROUTING
    ─────────────────────────────────────────────
    /api/*        → api-service (port 8080)
    /static/*     → cdn-origin (port 80)
    /admin/*      → admin-service (port 8443)
    /             → frontend (port 3000)

    HOST-BASED ROUTING
    ─────────────────────────────────────────────
    app.example.com     → app-backend
    api.example.com     → api-backend
    admin.example.com   → admin-backend

    HEADER-BASED ROUTING
    ─────────────────────────────────────────────
    X-Version: canary   → canary-backend (10% traffic)
    X-Version: stable   → stable-backend (90% traffic)

    COOKIE-BASED ROUTING
    ─────────────────────────────────────────────
    JSESSIONID=abc123   → server-A (session affinity)

    WEIGHTED ROUTING
    ─────────────────────────────────────────────
    Backend-A: 90%  (current version)
    Backend-B: 10%  (canary deployment)

L7 CHARACTERISTICS
─────────────────────────────────────────────────────────────
    Throughput:       Tens of thousands of requests/second
    Latency added:    1-5ms (TLS termination + parsing)
    TLS:              TERMINATED at LB (can inspect traffic)
    Protocols:        HTTP/1.1, HTTP/2, WebSocket, gRPC
    Connection state: HTTP-level (request/response)
    Use cases:        Web applications, microservices routing,
                      TLS termination, request manipulation
```

### 1.3 L4 vs L7 Decision Matrix

```
WHEN TO USE L4 vs L7
═══════════════════════════════════════════════════════════════

REQUIREMENT                    L4              L7
──────────────────────────── ──────────────── ───────────────
Maximum throughput             ✓ Best          ✗ Limited
Lowest latency                 ✓ <1ms          ✗ 1-5ms
HTTP path/header routing       ✗ Can't see     ✓ Full control
TLS termination                ✗ Pass-through  ✓ Terminates
WebSocket support              ✓ Transparent   ✓ Managed
gRPC load balancing            ✗ Per-connection ✓ Per-request
Non-HTTP protocols (DB, SMTP)  ✓ Any protocol  ✗ HTTP only
Request/response modification  ✗ No access     ✓ Full access
Cookie-based session affinity  ✗ No cookies    ✓ Cookie aware
Client certificate (mTLS)      ✗ Pass-through  ✓ Validates
Health checks (HTTP)           ✗ TCP only*     ✓ HTTP checks
Connection draining            ✓ Timer-based   ✓ Request-aware
Cost                           ✓ Lower         ✗ Higher

* Some L4 LBs support limited HTTP health checks

COMMON ARCHITECTURE: L4 + L7 TOGETHER
─────────────────────────────────────────────────────────────

    Internet → L4 (NLB) → L7 (ALB or Ingress Controller) → Pods

    Why both?
    - NLB handles TLS passthrough and raw throughput
    - NLB preserves client IP via Proxy Protocol
    - Ingress Controller (nginx/envoy) handles HTTP routing
    - Best of both worlds: performance + routing flexibility

    ┌────────┐     ┌─────────┐     ┌──────────┐     ┌──────┐
    │ Client │────→│  NLB    │────→│  nginx   │────→│ Pods │
    │        │     │  (L4)   │     │ Ingress  │     │      │
    │        │     │         │     │  (L7)    │     │      │
    └────────┘     └─────────┘     └──────────┘     └──────┘

    NLB adds:  Proxy Protocol header (client IP)
    nginx reads: Proxy Protocol, routes by path/host
    Pod sees:  X-Forwarded-For: original client IP
```

---

## Part 2: Connection Draining

### 2.1 The Problem: Killing Active Connections

```
CONNECTION DRAINING — GRACEFUL SHUTDOWN
═══════════════════════════════════════════════════════════════

When a backend server is removed (health check failure,
scaling down, deployment), what happens to active connections?

WITHOUT CONNECTION DRAINING
─────────────────────────────────────────────────────────────

    t=0   Server has 50 active connections
    t=0   Health check fails → server marked unhealthy
    t=0   LB immediately drops all 50 connections
          → 50 users see connection reset errors
          → In-flight API calls return with no response
          → File uploads are truncated
          → WebSocket connections are severed

    User experience: ERROR, ERROR, ERROR

WITH CONNECTION DRAINING (Deregistration Delay)
─────────────────────────────────────────────────────────────

    t=0     Server has 50 active connections
    t=0     Health check fails → server enters "draining" state
    t=0     LB stops sending NEW connections to this server
    t=0     Existing 50 connections continue normally
    t=10s   45 connections complete naturally
    t=30s   48 connections complete naturally
    t=60s   49 connections complete naturally
    t=300s  Draining timeout reached → last connection closed
            (or all connections complete before timeout)

    User experience: Most requests complete successfully.
    Only extremely long requests (>5 min) might be dropped.

DRAINING STATE DIAGRAM
─────────────────────────────────────────────────────────────

    ┌──────────┐                      ┌──────────┐
    │ HEALTHY  │ ─── health check ──→ │ DRAINING │
    │          │     failure           │          │
    │ Receives │                      │ No new   │
    │ new +    │                      │ conns.   │
    │ existing │                      │ Existing │
    │ traffic  │                      │ continue.│
    └──────────┘                      └─────┬────┘
         ▲                                  │
         │                                  │ All connections
         │     health check passes          │ complete OR
         │                                  │ timeout reached
         │                                  ▼
    ┌────┴─────┐                      ┌──────────┐
    │ INITIAL  │                      │ REMOVED  │
    │          │                      │          │
    │ Just     │                      │ No more  │
    │ registered│                     │ traffic  │
    └──────────┘                      └──────────┘

KUBERNETES GRACEFUL SHUTDOWN
─────────────────────────────────────────────────────────────

    Kubernetes pods have a similar concept:

    1. Pod enters "Terminating" state
    2. preStop hook runs (if configured)
    3. SIGTERM sent to container
    4. Container should:
       - Stop accepting new connections
       - Complete in-flight requests
       - Close gracefully
    5. After terminationGracePeriodSeconds (default 30s):
       SIGKILL sent (forced kill)

    Common issue: Endpoint is removed from Service before
    pod receives SIGTERM. Add a preStop sleep:

    lifecycle:
      preStop:
        exec:
          command: ["sh", "-c", "sleep 5"]

    This gives kube-proxy time to remove the endpoint
    before the pod starts shutting down.

DRAINING TIMEOUT GUIDELINES
─────────────────────────────────────────────────────────────
    API endpoints (fast):       30 seconds
    Web applications:           60 seconds
    WebSocket connections:      300 seconds (5 min)
    File upload endpoints:      600 seconds (10 min)
    Long-running streams:       3600 seconds (1 hour)
    Database connections:       60 seconds (with query timeout)
```

---

## Part 3: Session Affinity (Sticky Sessions)

### 3.1 Types of Session Affinity

```
SESSION AFFINITY — KEEPING CLIENTS ON ONE SERVER
═══════════════════════════════════════════════════════════════

Session affinity ensures the same client always reaches
the same backend server. Several implementation methods:

SOURCE IP AFFINITY (L4)
─────────────────────────────────────────────────────────────

    hash(client_ip) % num_servers = selected_server

    Client 1.2.3.4 → always hits Server-A
    Client 5.6.7.8 → always hits Server-B

    ✓ Works at L4 (no HTTP inspection needed)
    ✓ Zero overhead per request
    ✗ Breaks behind NAT (all users behind same IP → same server)
    ✗ Uneven distribution (some IPs generate more traffic)
    ✗ No affinity when servers are added/removed (rehashing)

COOKIE-BASED AFFINITY (L7)
─────────────────────────────────────────────────────────────

    LB sets a cookie on first response:
    Set-Cookie: AWSALB=server-a; Path=/; HttpOnly

    Subsequent requests include cookie:
    Cookie: AWSALB=server-a

    LB reads cookie → routes to server-a.

    ✓ Precise per-user affinity
    ✓ Survives NAT, proxies, VPNs
    ✓ LB controls cookie (application-transparent)
    ✗ Requires L7 (TLS termination)
    ✗ Cookie adds bytes to every request
    ✗ Doesn't work for non-browser clients without cookie support

APPLICATION-GENERATED AFFINITY (L7)
─────────────────────────────────────────────────────────────

    Application sets its own session cookie:
    Set-Cookie: JSESSIONID=abc123

    LB is configured to route based on JSESSIONID value.

    ✓ Application controls session semantics
    ✓ Session can encode server identity
    ✗ Application must generate appropriate cookie values
    ✗ Tighter coupling between app and LB config

HEADER-BASED AFFINITY (L7)
─────────────────────────────────────────────────────────────

    Route based on a custom header (e.g., user ID).

    X-User-ID: 12345 → Server-A
    X-User-ID: 67890 → Server-B

    ✓ Works for API clients (no cookies)
    ✓ Can use any consistent identifier
    ✗ Client must send the header
    ✗ Requires L7 inspection

THE CASE AGAINST STICKY SESSIONS
─────────────────────────────────────────────────────────────

    Problems:
    ─────────────────────────────────────────────
    1. UNEVEN LOAD: Popular users stuck on one server
       → that server overloaded while others are idle

    2. CASCADING FAILURE: Server dies → all its sticky users
       are redistributed → other servers overloaded
       → more servers die → cascade

    3. SCALING DIFFICULTY: Adding a server doesn't immediately
       help — existing users stay on old servers

    4. DEPLOYMENT COMPLEXITY: Rolling update means users
       must be drained from old servers to new ones

    Better alternative:
    ─────────────────────────────────────────────
    Store session state externally (Redis, Memcached, DynamoDB).
    Any server can handle any request.
    No affinity needed.

    ┌────────┐     ┌──────┐     ┌──────────┐
    │ Client │────→│  LB  │────→│ Server A │──→┐
    │        │     │      │     │ Server B │──→├→ Redis
    │        │     │      │     │ Server C │──→┘  (shared
    └────────┘     └──────┘     └──────────┘      session)
```

---

## Part 4: Proxy Protocol

### 4.1 The Client IP Problem

```
PROXY PROTOCOL — PRESERVING CLIENT IP THROUGH L4 PROXIES
═══════════════════════════════════════════════════════════════

THE PROBLEM
─────────────────────────────────────────────────────────────

    L7 load balancers can add X-Forwarded-For headers because
    they parse HTTP. L4 load balancers can't — they just
    forward TCP connections.

    Without Proxy Protocol:
    ┌────────────┐         ┌──────┐         ┌────────┐
    │ Client     │ ──TCP──→│ NLB  │ ──TCP──→│Backend │
    │ 203.0.113.5│         │      │         │        │
    └────────────┘         └──────┘         └────────┘

    Backend sees source IP of: NLB internal IP (10.0.1.x)
    Client's real IP is LOST.

    This breaks:
    - Access logging (who made the request?)
    - Geo-targeting (where is the user?)
    - Rate limiting (by client IP)
    - IP-based access control
    - Fraud detection
    - Compliance/audit trails

PROXY PROTOCOL V1 (Text)
─────────────────────────────────────────────────────────────

    Prepends a single text line before the TCP data stream.

    PROXY TCP4 203.0.113.5 10.0.0.1 54321 443\r\n
    [original TCP data follows]

    Format:
    PROXY <protocol> <src_ip> <dst_ip> <src_port> <dst_port>\r\n

    Examples:
    PROXY TCP4 203.0.113.5 10.0.0.1 54321 443\r\n
    PROXY TCP6 2001:db8::1 2001:db8::2 54321 443\r\n
    PROXY UNKNOWN\r\n   (health check or internal connection)

    ✓ Human-readable (easy to debug with tcpdump)
    ✓ Simple to implement
    ✗ Text parsing overhead
    ✗ Limited to IP and port information

PROXY PROTOCOL V2 (Binary)
─────────────────────────────────────────────────────────────

    Binary format. More efficient, extensible with TLV fields.

    ┌─────────────┬──────┬────────┬──────────┬──────────────┐
    │ Signature   │ Ver/ │ Length │ Addresses│ TLV          │
    │ (12 bytes)  │ Cmd  │        │          │ Extensions   │
    │ \r\n\r\n... │ \x21 │        │          │              │
    └─────────────┴──────┴────────┴──────────┴──────────────┘

    TLV (Type-Length-Value) extensions can carry:
    - TLS version and cipher negotiated
    - Client certificate details
    - AWS VPC endpoint ID
    - Custom application data

    ✓ More efficient (binary parsing)
    ✓ Extensible (TLV fields)
    ✓ Carries TLS metadata
    ✗ Not human-readable
    ✗ More complex to implement

HOW IT WORKS IN PRACTICE
─────────────────────────────────────────────────────────────

    ┌────────────┐      ┌──────────────┐      ┌───────────────┐
    │ Client     │      │ NLB          │      │ nginx         │
    │ 203.0.113.5│      │ (L4)         │      │ (Ingress)     │
    │            │      │              │      │               │
    │ Sends:     │──TCP─│ Prepends:    │──TCP─│ Reads PP      │
    │ GET /api   │      │ PROXY TCP4   │      │ header first  │
    │            │      │ 203.0.113.5  │      │               │
    │            │      │ 10.0.0.1     │      │ Sets:         │
    │            │      │ 54321 443    │      │ $remote_addr  │
    │            │      │ \r\n         │      │ = 203.0.113.5 │
    │            │      │ [GET /api]   │      │               │
    └────────────┘      └──────────────┘      │ Adds header:  │
                                              │ X-Forwarded-  │
                                              │ For:          │
                                              │ 203.0.113.5   │
                                              └───────────────┘

    Backend application sees:
    - X-Forwarded-For: 203.0.113.5 (real client IP!)
    - X-Real-IP: 203.0.113.5
```

### 4.2 Proxy Protocol Configuration

```
PROXY PROTOCOL CONFIGURATION
═══════════════════════════════════════════════════════════════

⚠️  CRITICAL: Both sides must agree!
    If LB sends Proxy Protocol but backend doesn't expect it,
    backend sees "PROXY TCP4..." as garbage → connection fails.
    If backend expects Proxy Protocol but LB doesn't send it,
    backend waits for PP header → timeout → connection fails.

NGINX CONFIGURATION (Receiving Proxy Protocol)
─────────────────────────────────────────────────────────────

    server {
        # Enable Proxy Protocol on the listen directive
        listen 443 ssl proxy_protocol;

        # Use the real client IP from Proxy Protocol
        set_real_ip_from 10.0.0.0/8;     # Trust NLB's IP range
        real_ip_header proxy_protocol;    # Get IP from PP header

        # Pass real IP to backend as header
        proxy_set_header X-Real-IP       $proxy_protocol_addr;
        proxy_set_header X-Forwarded-For $proxy_protocol_addr;
    }

HAPROXY CONFIGURATION
─────────────────────────────────────────────────────────────

    # Receiving Proxy Protocol
    frontend web
        bind *:443 accept-proxy ssl crt /etc/ssl/cert.pem

    # Sending Proxy Protocol to backend
    backend servers
        server s1 10.0.1.5:8080 send-proxy-v2

ENVOY CONFIGURATION
─────────────────────────────────────────────────────────────

    # Listener receiving Proxy Protocol
    listener_filters:
      - name: envoy.filters.listener.proxy_protocol
        typed_config:
          "@type": type.googleapis.com/
            envoy.extensions.filters.listener.proxy_protocol.v3.ProxyProtocol

AWS NLB + PROXY PROTOCOL
─────────────────────────────────────────────────────────────

    Target Group settings:
      Proxy Protocol v2: Enabled

    ⚠️  NLB sends Proxy Protocol v2 (binary).
    Your backend MUST support v2 (nginx, HAProxy, envoy do).

COMMON GOTCHA: HEALTH CHECKS
─────────────────────────────────────────────────────────────

    NLB health checks do NOT send Proxy Protocol headers.
    If your backend requires Proxy Protocol on ALL connections,
    NLB health checks will fail.

    Solution 1: Use a separate port for health checks
                (without Proxy Protocol requirement)

    Solution 2: Configure backend to accept connections
                both with and without Proxy Protocol
                (nginx: listen 443 ssl; on a separate server block)
```

---

## Part 5: Cross-Zone Load Balancing

### 5.1 The Cross-Zone Problem

```
CROSS-ZONE LOAD BALANCING
═══════════════════════════════════════════════════════════════

Cloud load balancers span multiple Availability Zones.
Cross-zone determines whether traffic can flow across zones.

WITHOUT CROSS-ZONE (Zone-Isolated)
─────────────────────────────────────────────────────────────

    Each AZ's LB node only sends to backends in its own AZ.

    AZ-A (2 targets)          AZ-B (8 targets)
    ┌─────────────────┐       ┌─────────────────┐
    │  LB Node A      │       │  LB Node B      │
    │  (50% traffic)  │       │  (50% traffic)  │
    │       │         │       │       │         │
    │    ┌──┴──┐      │       │  ┌────┼────┐    │
    │    │     │      │       │  │ │  │  │ │    │
    │   T-1   T-2    │       │ T-3 T-4 T-5 T-6│
    │   25%   25%    │       │  T-7 T-8 T-9 T-10│
    │                 │       │ 6.25% each      │
    └─────────────────┘       └─────────────────┘

    Problem: T-1 and T-2 each get 25% of total traffic
             T-3 through T-10 each get 6.25%
             AZ-A targets are 4x overloaded!

WITH CROSS-ZONE (Default for ALB, optional for NLB)
─────────────────────────────────────────────────────────────

    Each LB node distributes evenly across ALL backends.

    AZ-A (2 targets)          AZ-B (8 targets)
    ┌─────────────────┐       ┌─────────────────┐
    │  LB Node A      │       │  LB Node B      │
    │       │         │       │       │         │
    │    Sends to     │       │    Sends to     │
    │    ALL 10       │       │    ALL 10       │
    │    targets      │       │    targets      │
    │    evenly       │       │    evenly       │
    └─────────────────┘       └─────────────────┘

    Each of the 10 targets gets exactly 10% of traffic.
    Even distribution regardless of AZ placement.

TRADE-OFFS
─────────────────────────────────────────────────────────────

    Cross-Zone ON:
    ✓ Even distribution across all targets
    ✓ Better utilization of all backends
    ✗ Cross-AZ data transfer charges ($0.01/GB on AWS)
    ✗ Slightly higher latency for cross-AZ traffic (~0.5-1ms)
    ✗ AZ failure might affect traffic in other AZs

    Cross-Zone OFF:
    ✓ No cross-AZ data transfer charges
    ✓ Failure domain isolation (AZ failure = AZ impact only)
    ✓ Lower latency (all traffic stays in-zone)
    ✗ Uneven distribution if target count differs per AZ
    ✗ Must carefully balance target count across AZs

AWS DEFAULTS
─────────────────────────────────────────────────────────────
    ALB: Cross-zone ON (always, can't disable per target group)
    NLB: Cross-zone OFF (can enable per target group)
    CLB: Cross-zone ON (default since 2014)

    NLB cross-zone cost: $0.006/GB inter-AZ traffic

    For high-traffic NLBs (>100 TB/month), cross-zone OFF
    saves thousands of dollars. But you must ensure even
    target distribution across AZs.
```

---

## Part 6: Cloud Load Balancer Architectures

### 6.1 AWS Load Balancers

```
AWS LOAD BALANCER COMPARISON
═══════════════════════════════════════════════════════════════

NETWORK LOAD BALANCER (NLB)
─────────────────────────────────────────────────────────────
    Layer:          4 (TCP, UDP, TLS)
    Performance:    Millions of requests/sec, <100μs latency
    IPs:            Static (Elastic IP per AZ)
    Protocols:      TCP, UDP, TLS, TCP_UDP
    Targets:        EC2, IP, ALB (!)
    Proxy Protocol: v2 supported
    TLS:            Terminates OR pass-through
    Health checks:  TCP, HTTP, HTTPS
    Pricing:        Per NLCU (capacity unit)
    Cross-zone:     Off by default

    Architecture:
    ┌──────────────────────────────────────────────────┐
    │  NLB uses flow hash for connection distribution   │
    │  Hash: src_ip, src_port, dst_ip, dst_port, proto │
    │  Same 5-tuple → same target (for connection life) │
    │                                                  │
    │  Internally: Hyperplane (software-defined LB)    │
    │  Distributed across all hosts in the AZ          │
    │  No single point of failure, scales elastically  │
    └──────────────────────────────────────────────────┘

APPLICATION LOAD BALANCER (ALB)
─────────────────────────────────────────────────────────────
    Layer:          7 (HTTP, HTTPS, gRPC)
    Performance:    Thousands of new connections/sec
    IPs:            Dynamic (DNS-based resolution)
    Protocols:      HTTP/1.1, HTTP/2, gRPC, WebSocket
    Targets:        EC2, IP, Lambda
    Routing:        Path, host, header, query, source IP
    TLS:            Terminates (required)
    Health checks:  HTTP, HTTPS (with path/matcher)
    Auth:           OIDC, Cognito integration
    Pricing:        Per LCU (capacity unit)
    Cross-zone:     Always on

    Advanced features:
    - Weighted target groups (canary deployments)
    - Sticky sessions (cookie-based)
    - Request/response header modification
    - Redirect and fixed-response actions
    - AWS WAF integration

NLB + ALB PATTERN
─────────────────────────────────────────────────────────────
    NLB can target an ALB. This gives you:

    Internet → NLB (static IPs, Proxy Protocol)
             → ALB (HTTP routing, WAF, auth)
             → Targets

    Why: Some use cases need BOTH static IPs (firewall
    allowlisting) AND L7 features (path routing).
```

### 6.2 Google Maglev

```
GOOGLE MAGLEV — SOFTWARE-DEFINED L4 LOAD BALANCING
═══════════════════════════════════════════════════════════════

Maglev is Google's custom L4 load balancer. It powers
Google Cloud Load Balancing and all Google services.

ARCHITECTURE
─────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────┐
    │  Google's Edge PoP                                   │
    │                                                      │
    │  ┌──────────────────────────────────────────────────┐│
    │  │  Maglev Machines (commodity Linux servers)       ││
    │  │                                                  ││
    │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  ││
    │  │  │Maglev-1│ │Maglev-2│ │Maglev-3│ │Maglev-N│  ││
    │  │  │        │ │        │ │        │ │        │  ││
    │  │  │ ECMP   │ │ ECMP   │ │ ECMP   │ │ ECMP   │  ││
    │  │  │ (equal │ │        │ │        │ │        │  ││
    │  │  │ share) │ │        │ │        │ │        │  ││
    │  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘  ││
    │  │      │          │          │          │        ││
    │  │      └──────────┼──────────┼──────────┘        ││
    │  │                 │          │                    ││
    │  │      All use Maglev consistent hashing          ││
    │  │      Same flow → Same backend (regardless       ││
    │  │      of which Maglev machine handles it)        ││
    │  └──────────────────────────────────────────────────┘│
    │                                                      │
    │  GRE/GUE encapsulation → Backend VMs                │
    └──────────────────────────────────────────────────────┘

MAGLEV CONSISTENT HASHING
─────────────────────────────────────────────────────────────

    Problem with standard consistent hashing:
    When a backend is removed, ~1/N flows are redistributed.
    But which specific flows? Unpredictable.

    Maglev hashing guarantees:
    - Same 5-tuple always maps to same backend
    - ANY Maglev machine produces the SAME mapping
    - When a backend is removed, ONLY that backend's flows
      are redistributed (minimal disruption)

    This means multiple Maglev machines can handle traffic
    via ECMP without coordination, and all agree on backend
    selection. No shared state needed!

    Lookup table size: 65,537 entries (prime number)
    Lookup time: O(1) — single table access

KEY PROPERTIES
─────────────────────────────────────────────────────────────
    Throughput:   ~10 Mpps per machine (10M packets/second)
    Line rate:    Each machine saturates 10 Gbps
    Scaling:      Add more machines, ECMP distributes
    Failover:     Machine failure → ECMP re-distributes
                  Backend failure → consistent hash re-maps
    No state:     Each machine is independent (stateless*)

    * Connection tracking table is local, not shared.
      But consistent hashing means the SAME machine
      naturally gets the same flow after ECMP reconvergence.
```

### 6.3 Kubernetes Load Balancing

```
KUBERNETES SERVICE LOAD BALANCING
═══════════════════════════════════════════════════════════════

CLUSTERIP (Internal L4)
─────────────────────────────────────────────────────────────
    Virtual IP (kube-proxy iptables or IPVS).
    Round-robin across endpoints.

    Service: 10.96.0.100:80
    Endpoints: [10.244.1.5:8080, 10.244.2.8:8080]

    iptables: DNAT 10.96.0.100 → random(10.244.1.5, 10.244.2.8)

    IPVS mode (better for large clusters):
    - Supports weighted round robin, least connections
    - O(1) connection forwarding vs O(n) iptables chains
    - Better performance with >1000 services

NODEPORT
─────────────────────────────────────────────────────────────
    Opens a port (30000-32767) on every node.
    External traffic → any Node IP:NodePort → Pod

    ⚠️  Double-hop problem:
    Traffic hits Node A → Pod is on Node B → forwarded to B
    Return traffic goes from B → back through A → client
    Extra hop, SNAT hides client IP.

    externalTrafficPolicy: Local
    - Only routes to pods on the receiving node
    - Preserves client IP (no SNAT)
    - But: if no pod on that node → connection refused

LOADBALANCER
─────────────────────────────────────────────────────────────
    Cloud provider provisions external LB automatically.

    AWS: NLB or CLB (configurable via annotation)
    GCP: Network LB (regional) or HTTP(S) LB (global)
    Azure: Azure Load Balancer (L4)

    Annotations control behavior:
    ─────────────────────────────────────────────
    # AWS NLB
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-proxy-protocol: "*"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"

    # Target type (instance vs IP)
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"

    instance mode: NLB → NodePort → kube-proxy → Pod
    ip mode:       NLB → Pod directly (requires VPC CNI)

INGRESS (L7)
─────────────────────────────────────────────────────────────
    Ingress Controller (nginx, envoy, traefik) provides L7.
    Typically behind a LoadBalancer Service.

    Internet → Cloud LB → Ingress Controller → Services → Pods

    Gateway API (newer, preferred):
    ─────────────────────────────────────────────
    GatewayClass → Gateway → HTTPRoute → Service → Pod

    More expressive than Ingress:
    - Header-based routing
    - Traffic splitting (canary)
    - Request/response modification
    - TLS configuration per route
```

---

## Did You Know?

- **Google's Maglev handles all of Google's external traffic** — every search query, YouTube video, Gmail message, and Cloud Platform API call passes through Maglev. At peak, this is millions of packets per second per machine, across hundreds of machines at each of Google's edge PoPs. The design was published in a 2016 NSDI paper that has become a reference for building software load balancers.

- **AWS NLB can handle millions of requests per second with single-digit microsecond latency** because it runs on Hyperplane, AWS's internal software-defined networking platform. Unlike ALB, which runs on EC2 instances, NLB is embedded in the network fabric itself. This is why NLB supports static Elastic IPs while ALB's IPs are dynamic — they're fundamentally different architectures.

- **The Proxy Protocol specification was created by Willy Tarreau, the author of HAProxy, in 2010.** What started as a simple solution for HAProxy has become an industry standard supported by every major load balancer, web server, and CDN. Version 2 added binary encoding and TLV extensions that carry TLS metadata, AWS VPC information, and custom application data — far beyond the original "just pass the client IP" use case.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No connection draining configured | Active requests dropped during deployments | Set deregistration delay (300s for most apps) |
| Proxy Protocol mismatch | Backend expects PP but LB doesn't send (or vice versa) → connection failures | Enable/disable on BOTH sides simultaneously |
| NLB health checks failing with Proxy Protocol | NLB health checks don't send PP headers | Use separate health check port or HTTP health check |
| Sticky sessions hiding backend failures | Unhealthy server keeps receiving sticky traffic | Always combine stickiness with health checks |
| Using ALB when you need static IPs | ALB IPs change; firewall allowlists break | Use NLB (static EIPs) in front of ALB, or use Global Accelerator |
| Cross-zone off with uneven target distribution | Some targets get 4x more traffic than others | Either enable cross-zone or ensure equal targets per AZ |
| Not setting `externalTrafficPolicy: Local` | Client IP lost due to SNAT on the second hop | Set to Local (but ensure pods exist on all receiving nodes) |
| Ingress controller without readiness gates | Pods receive traffic before they're ready | Use pod readiness gates tied to LB target health |
| Ignoring NLB connection idle timeout | Long-lived connections (WebSocket) silently dropped at 350s | Set idle timeout appropriately; use TCP keepalive |

---

## Quiz

1. **Explain the fundamental difference between L4 and L7 load balancing. Why can't an L4 load balancer do path-based routing?**
   <details>
   <summary>Answer</summary>

   L4 load balancers operate at the transport layer (TCP/UDP). They see the 5-tuple: source IP, source port, destination IP, destination port, and protocol. They make routing decisions based on these fields and forward raw TCP/UDP streams without understanding the content.

   L7 load balancers operate at the application layer (HTTP). They terminate the client's TCP and TLS connections, parse the HTTP request, and then create a new connection to the selected backend. This means they can inspect URLs, headers, cookies, and even the request body.

   An L4 load balancer cannot do path-based routing because the URL path is inside the HTTP request body, which is inside the TLS-encrypted TCP stream. The L4 LB only sees TCP headers — it never decrypts TLS or parses HTTP. The path `/api/users` is opaque data as far as L4 is concerned.

   The one exception: L4 LBs can use TLS SNI (Server Name Indication) for host-based routing, because SNI is sent in cleartext during the TLS handshake. But this only gives you the hostname, not the path.
   </details>

2. **What is connection draining and why is a 5-second draining timeout dangerous for a production application?**
   <details>
   <summary>Answer</summary>

   Connection draining is the process of gracefully removing a backend from a load balancer. When a backend enters the "draining" state, the LB stops sending new connections but allows existing in-flight connections to complete, up to a configured timeout.

   A 5-second timeout is dangerous because:

   1. **Long-running requests**: Any request that takes more than 5 seconds (large file upload, complex database query, report generation) will be forcibly terminated. The client receives a connection reset with no error message.

   2. **WebSocket connections**: WebSockets are long-lived. A 5-second timeout kills every active WebSocket connection during any deployment or health check failure.

   3. **Deployment frequency**: If you deploy multiple times per day, each deployment drains and replaces backends. Short timeouts mean frequent connection drops across the fleet.

   4. **Cascading drain events**: If a health check flaps (passes, fails, passes), the backend enters and exits draining repeatedly. With a 5-second window, many requests are still in progress when the drain completes.

   Recommended timeouts:
   - API endpoints: 30-60 seconds
   - WebSocket: 300+ seconds
   - File upload endpoints: 600+ seconds
   - Default for most applications: 300 seconds
   </details>

3. **Why are sticky sessions (session affinity) considered an anti-pattern for stateless microservices? When are they still justified?**
   <details>
   <summary>Answer</summary>

   Sticky sessions are considered an anti-pattern because they:

   1. **Create uneven load**: Popular users or heavy sessions get stuck on one server, creating hotspots while other servers are underutilized.

   2. **Complicate scaling**: Adding servers doesn't immediately help because existing sessions stay on old servers. Removing servers requires draining all their sticky sessions.

   3. **Reduce resilience**: When a server fails, all its sticky sessions must be re-established elsewhere. Users lose their session state. If the replacement servers are already loaded, this can cascade.

   4. **Conflict with deployment strategies**: Rolling deployments must migrate sticky sessions from old pods to new ones, adding complexity and risk.

   **When still justified**:
   - **Legacy applications** that store session state in-process and cannot be refactored to use external session storage
   - **Connection-oriented protocols** (WebSocket, gRPC streaming) where the connection itself is stateful by nature
   - **Caching optimization**: Routing the same user to the same server improves local cache hit rates (e.g., in-memory caches of user-specific data)
   - **Licensing constraints**: Some enterprise software is licensed per-server and sessions must stay on one server

   The better alternative is external session storage (Redis, DynamoDB) so any server can handle any request. This is the standard approach for cloud-native applications.
   </details>

4. **You configure an NLB with Proxy Protocol v2 enabled, but your backend application shows the NLB's internal IP in access logs instead of the client IP. What are the three most likely causes?**
   <details>
   <summary>Answer</summary>

   Three most likely causes:

   1. **Backend not configured to read Proxy Protocol**: The backend web server (nginx, HAProxy, envoy) must be explicitly configured to expect and parse the Proxy Protocol header. Without this configuration, the binary PP v2 header is treated as garbage data (and possibly causes connection errors) while the backend reads the TCP source IP (NLB's IP).

      Fix for nginx: Add `proxy_protocol` to the `listen` directive:
      ```
      listen 443 ssl proxy_protocol;
      real_ip_header proxy_protocol;
      set_real_ip_from 10.0.0.0/8;
      ```

   2. **Proxy Protocol enabled on NLB but not on the target group**: In AWS, Proxy Protocol v2 is configured per target group, not on the NLB itself. If the target group attribute `proxy_protocol_v2.enabled` is not set to `true`, the NLB does not prepend the PP header.

   3. **Intermediate proxy stripping the information**: If there's a proxy between the NLB and the backend (e.g., a sidecar, a service mesh proxy, or kube-proxy in iptables mode), it may not pass through the Proxy Protocol header. Each proxy in the chain must either forward the PP header or translate it (e.g., to X-Forwarded-For).

   Debugging approach: Use `tcpdump` on the backend to verify whether the Proxy Protocol header is present in the TCP stream.
   </details>

5. **Explain the cross-zone load balancing problem. You have 2 targets in AZ-A and 6 targets in AZ-B. With cross-zone disabled, what percentage of total traffic does each target receive?**
   <details>
   <summary>Answer</summary>

   With cross-zone disabled, each AZ's LB node distributes traffic only to targets in its own AZ. DNS round-robin between the AZ endpoints means each AZ node receives 50% of total traffic.

   **AZ-A (2 targets, 50% of traffic)**:
   - Target 1: 50% / 2 = **25%** of total traffic
   - Target 2: 50% / 2 = **25%** of total traffic

   **AZ-B (6 targets, 50% of traffic)**:
   - Each target: 50% / 6 = **~8.3%** of total traffic

   AZ-A targets receive 3x more traffic than AZ-B targets (25% vs 8.3%). If all targets have the same capacity, AZ-A targets will be overloaded while AZ-B targets are underutilized.

   With cross-zone enabled, all 8 targets receive equal traffic: 100% / 8 = **12.5% each**.

   Solutions when cross-zone is disabled (to avoid inter-AZ charges):
   - Maintain equal target counts per AZ (3 in A, 3 in B, or 4 in each)
   - Use auto-scaling groups with per-AZ min/max settings
   - Accept the uneven distribution and size AZ-A targets larger
   </details>

6. **In Kubernetes, what is the "double-hop" problem with NodePort services, and how does `externalTrafficPolicy: Local` solve it? What new problem does it introduce?**
   <details>
   <summary>Answer</summary>

   **The double-hop problem**:
   When external traffic arrives at a node via NodePort, kube-proxy may forward it to a pod on a different node:

   1. Traffic arrives at Node A (port 30080)
   2. kube-proxy on Node A randomly selects a pod — Pod on Node B
   3. Packet is SNAT'd (source NAT) to Node A's IP and forwarded to Node B
   4. Pod on Node B processes the request, responds to Node A
   5. Node A forwards response to client

   Problems: Extra network hop (latency), client IP is lost (SNAT replaces it with Node A's IP).

   **How `externalTrafficPolicy: Local` solves it**:
   With this setting, kube-proxy only routes traffic to pods running on the same node where the traffic arrived. No SNAT, no extra hop.

   1. Traffic arrives at Node A (port 30080)
   2. kube-proxy routes to a pod on Node A only
   3. Client IP is preserved (no SNAT needed)

   **The new problem it introduces**:
   If a node has no pods for the service, traffic arriving at that node is dropped (connection refused). The load balancer's health check must detect this and stop sending traffic to nodes without local pods.

   This means:
   - Uneven traffic distribution (nodes with more pods get more traffic)
   - Nodes with zero pods are excluded, wasting capacity
   - Must ensure pods are spread across all nodes (topology spread constraints)
   - Health checks must target the NodePort's health check port (allocated automatically by Kubernetes)
   </details>

---

## Hands-On Exercise

**Objective**: Set up an L4 load balancer with Proxy Protocol forwarding to a Kubernetes Ingress controller, and verify that the real client IP is preserved in application logs.

**Environment**: kind cluster + MetalLB (L4 LB simulation) + nginx Ingress

### Part 1: Create the Cluster (10 minutes)

```bash
cat <<'EOF' > /tmp/lb-lab-cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

kind create cluster --name lb-lab --config /tmp/lb-lab-cluster.yaml
```

### Part 2: Deploy nginx Ingress with Proxy Protocol Support (15 minutes)

```bash
# Install nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.0/deploy/static/provider/kind/deploy.yaml

# Wait for ingress controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Configure nginx to accept Proxy Protocol
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
data:
  use-proxy-protocol: "true"
  compute-full-forwarded-for: "true"
  use-forwarded-headers: "true"
  proxy-real-ip-cidr: "0.0.0.0/0"
EOF

# Restart the ingress controller to pick up the config
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx
kubectl rollout status deployment ingress-nginx-controller -n ingress-nginx
```

### Part 3: Deploy Backend Application with IP Logging (10 minutes)

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ip-logger-code
data:
  server.py: |
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    import os

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Collect all IP-related headers
            ip_info = {
                "pod_name": os.environ.get("HOSTNAME", "unknown"),
                "remote_addr": self.client_address[0],
                "x_forwarded_for": self.headers.get("X-Forwarded-For", "not set"),
                "x_real_ip": self.headers.get("X-Real-IP", "not set"),
                "x_forwarded_proto": self.headers.get("X-Forwarded-Proto", "not set"),
                "all_headers": dict(self.headers),
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(ip_info, indent=2).encode())

        def log_message(self, format, *args):
            xff = self.headers.get("X-Forwarded-For", "-") if hasattr(self, 'headers') else "-"
            print(f"[{self.client_address[0]}] XFF={xff} {args[0]}")

    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ip-logger
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ip-logger
  template:
    metadata:
      labels:
        app: ip-logger
    spec:
      containers:
        - name: app
          image: python:3.12-slim
          command: ["python", "/app/server.py"]
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /
              port: 8080
            initialDelaySeconds: 3
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ip-logger
spec:
  selector:
    app: ip-logger
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ip-logger
  annotations:
    nginx.ingress.kubernetes.io/proxy-set-headers: "ingress-nginx/custom-headers"
spec:
  ingressClassName: nginx
  rules:
    - host: ip-test.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ip-logger
                port:
                  number: 80
EOF
```

### Part 4: Test Client IP Preservation (15 minutes)

```bash
# Get the ingress controller's cluster IP
INGRESS_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.clusterIP}')

# Deploy test client
kubectl run test-client --image=curlimages/curl:8.11.1 --rm -it -- sh

# Test 1: Request through Ingress (with Proxy Protocol support)
echo "=== Test 1: Via Ingress ==="
curl -s -H "Host: ip-test.local" http://${INGRESS_IP}/ | python3 -m json.tool

# Observe:
# - x_forwarded_for should contain the test client's pod IP
# - x_real_ip should contain the test client's pod IP
# - remote_addr is the ingress controller's IP

# Test 2: Multiple requests — observe load balancing
echo "=== Test 2: Load Balancing Distribution ==="
for i in $(seq 1 12); do
  POD=$(curl -s -H "Host: ip-test.local" http://${INGRESS_IP}/ | python3 -c "import sys,json; print(json.load(sys.stdin)['pod_name'])")
  echo "Request $i → $POD"
done

# You should see requests distributed across all 3 replicas

# Test 3: Check X-Forwarded-* headers
echo "=== Test 3: Header Inspection ==="
curl -s -H "Host: ip-test.local" \
  -H "X-Custom-Header: test-value" \
  http://${INGRESS_IP}/ | python3 -m json.tool
```

### Part 5: Observe Connection Draining (15 minutes)

```bash
# In one terminal: continuous requests
kubectl run load-gen --image=curlimages/curl:8.11.1 --rm -it -- sh -c '
  while true; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: ip-test.local" http://ip-logger/)
    echo "$(date +%H:%M:%S) HTTP $STATUS"
    sleep 0.5
  done
'

# In another terminal: scale down to 1 replica
kubectl scale deployment ip-logger --replicas=1

# Watch the load-gen output:
# - You should see continuous 200 responses
# - No 502 or 503 errors during scale-down
# - This is connection draining in action

# Scale back up
kubectl scale deployment ip-logger --replicas=3

# Scale to 0 (all pods removed)
kubectl scale deployment ip-logger --replicas=0

# Now watch load-gen — should see 503 errors
# (no backends available)

# Restore
kubectl scale deployment ip-logger --replicas=3
```

### Part 6: Test Session Affinity (10 minutes)

```bash
# Enable cookie-based session affinity on the Ingress
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ip-logger
  annotations:
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/affinity-mode: "persistent"
    nginx.ingress.kubernetes.io/session-cookie-name: "SERVERID"
    nginx.ingress.kubernetes.io/session-cookie-max-age: "172800"
spec:
  ingressClassName: nginx
  rules:
    - host: ip-test.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ip-logger
                port:
                  number: 80
EOF

# Test without cookie (different pods)
echo "=== Without Session Cookie ==="
for i in $(seq 1 6); do
  POD=$(curl -s -H "Host: ip-test.local" http://${INGRESS_IP}/ | python3 -c "import sys,json; print(json.load(sys.stdin)['pod_name'])")
  echo "Request $i → $POD"
done

# Test with cookie (same pod every time)
echo "=== With Session Cookie ==="
COOKIE=$(curl -s -c - -H "Host: ip-test.local" http://${INGRESS_IP}/ | grep SERVERID | awk '{print $NF}')
for i in $(seq 1 6); do
  POD=$(curl -s -b "SERVERID=$COOKIE" -H "Host: ip-test.local" http://${INGRESS_IP}/ | python3 -c "import sys,json; print(json.load(sys.stdin)['pod_name'])")
  echo "Request $i → $POD (sticky)"
done

# All sticky requests should hit the same pod!
```

### Clean Up

```bash
kind delete cluster --name lb-lab
```

**Success Criteria**:
- [ ] nginx Ingress controller deployed and accepting connections
- [ ] Client IP visible in X-Forwarded-For header in application response
- [ ] Observed load balancing across 3 replicas (roughly even distribution)
- [ ] Scaling down to 1 replica produced no error responses (connection draining)
- [ ] Scaling to 0 replicas produced 503 errors (no backends)
- [ ] Cookie-based session affinity routed all requests to the same pod
- [ ] Without session cookie, requests distributed across pods

---

## Further Reading

- **"Maglev: A Fast and Reliable Software Network Load Balancer"** (Google, NSDI 2016) — The paper describing Google's L4 load balancer architecture. Required reading for anyone building software load balancers.

- **AWS Elastic Load Balancing documentation** — Detailed deep dives on NLB, ALB, and Gateway LB architecture, particularly the "How Elastic Load Balancing Works" section.

- **"HAProxy Architecture Guide"** — The HAProxy documentation includes excellent explanations of L4 vs L7 load balancing, connection management, and Proxy Protocol.

- **"Proxy Protocol Specification"** (HAProxy) — The official specification for Proxy Protocol v1 and v2, including TLV extension format.

---

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **L4 load balancers forward connections, L7 load balancers proxy requests**: L4 is faster (microseconds, millions of CPS) but cannot inspect HTTP content; L7 terminates TLS and parses HTTP for rich routing
- [ ] **Connection draining prevents dropped requests**: Configure deregistration delay to match your longest expected request duration; 300 seconds is a safe default
- [ ] **Sticky sessions create operational complexity**: Prefer external session storage (Redis); use sticky sessions only when refactoring is impractical
- [ ] **Proxy Protocol preserves client IP through L4 proxies**: Both LB and backend must be configured; mismatch causes connection failures
- [ ] **Cross-zone load balancing trades cost for evenness**: On by default for ALB, off for NLB. Uneven target distribution without cross-zone creates hotspots
- [ ] **NLB + Ingress Controller is a powerful pattern**: NLB provides static IPs and Proxy Protocol; Ingress provides HTTP routing and TLS termination
- [ ] **Kubernetes `externalTrafficPolicy: Local` preserves client IP**: But requires pods on all nodes receiving traffic, or health checks must exclude empty nodes
- [ ] **Maglev consistent hashing enables stateless L4 LBs**: Any LB machine produces the same backend selection for the same flow, no shared state needed

---

## Next Module

[Module 1.6: Zero Trust Networking & VPN Alternatives](module-1.6-zero-trust.md) — Moving beyond perimeter security to identity-based access, with practical deployment of identity-aware proxies and SSE solutions.
