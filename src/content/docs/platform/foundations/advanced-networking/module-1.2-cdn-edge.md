---
title: "Module 1.2: CDN & Edge Computing"
slug: platform/foundations/advanced-networking/module-1.2-cdn-edge
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 2.5 hours
>
> **Prerequisites**: HTTP basics (methods, status codes, headers), basic understanding of caching
>
> **Track**: Foundations — Advanced Networking

### What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** CDN caching strategies that maximize cache hit ratios while ensuring content freshness through TTLs, cache keys, and invalidation patterns
2. **Evaluate** CDN architectures (pull vs. push, multi-CDN, edge compute) and select the right approach for different content types and traffic patterns
3. **Implement** edge computing patterns that move application logic closer to users for latency-sensitive workloads
4. **Diagnose** CDN cache misses, stale content issues, and origin shielding failures using cache headers and CDN analytics

---

**November 24, 2017. Black Friday. At precisely 12:01 AM Eastern, the largest online shopping event of the year begins. In the first sixty seconds, millions of browsers simultaneously request the same product images, CSS files, JavaScript bundles, and promotional videos from thousands of retail sites.**

Without CDNs, this traffic would crush origin servers. A single popular retailer might serve 50,000 requests per second for the same hero image. From their single origin datacenter in Virginia. To users in Tokyo, Mumbai, Sao Paulo, and London. Each request traveling thousands of kilometers, competing for bandwidth, adding 100-300ms of latency.

But that's not what happens. Instead, **a user in Tokyo receives that hero image from a server in Tokyo. A user in Mumbai gets it from Mumbai. A user in London gets it from London.** The origin server in Virginia barely notices, because 98% of requests never reach it.

This is the magic of Content Delivery Networks. They transformed the internet from a system where every request traveled to a distant origin server into one where content lives at the edge, physically close to users. CDNs serve an estimated **73% of all internet traffic** as of 2025. Without them, the modern internet would be unusably slow.

---

## Why This Module Matters

Latency is the tax users pay for distance. Light in fiber optic cable travels at about 200,000 km/s — roughly two-thirds the speed of light in vacuum. A round trip from New York to Singapore is about 30,000 km through undersea cables, imposing a minimum 150ms delay that no amount of server optimization can eliminate.

CDNs solve this fundamental physics problem by moving content closer to users. But modern CDNs have evolved far beyond simple caching. They now offer TLS termination, DDoS protection, image optimization, A/B testing, authentication, and even full application logic at the edge.

Understanding CDN architecture isn't optional for anyone building applications that serve global users. It's the difference between a sub-100ms page load and a 3-second one. And in 2025, it's also the difference between running code in a central datacenter and running it at 300+ locations worldwide.

> **The Local Library Analogy**
>
> Imagine a world where the only library was in Washington, D.C. Every person in every city who wanted to read a book had to request it from D.C., wait for it to be shipped, read it, and ship it back. Absurd, right? CDNs are like building local library branches in every city, stocking them with copies of the most popular books. Most readers never need to contact the central library at all.

---

## What You'll Learn

- CDN architecture: PoPs, edge servers, peering, and tiered caching
- Cache mechanics: headers, invalidation, stale-while-revalidate
- Dynamic content acceleration and route optimization
- Edge compute: running code at CDN locations
- TLS at the edge: termination strategies and trade-offs
- Hands-on: Deploying a static site with CDN caching and edge functions

---

## Part 1: CDN Architecture

### 1.1 Points of Presence (PoPs)

```
CDN NETWORK ARCHITECTURE
═══════════════════════════════════════════════════════════════

A CDN is a globally distributed network of servers (PoPs)
that cache and serve content close to end users.

SINGLE PoP ANATOMY
─────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────┐
    │  PoP: Tokyo (TYO)                                    │
    │                                                      │
    │  ┌──────────────────────────────────────────────────┐ │
    │  │  Edge Servers (Cache Layer)                      │ │
    │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │ │
    │  │  │ E-1 │ │ E-2 │ │ E-3 │ │ E-4 │ │ E-5 │     │ │
    │  │  │256GB│ │256GB│ │256GB│ │256GB│ │256GB│     │ │
    │  │  │ SSD │ │ SSD │ │ SSD │ │ SSD │ │ SSD │     │ │
    │  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘     │ │
    │  └──────────────────────────────────────────────────┘ │
    │                                                      │
    │  ┌──────────────────────────────────────────────────┐ │
    │  │  TLS Terminators                                │ │
    │  │  (Handle HTTPS, offload crypto from origin)     │ │
    │  └──────────────────────────────────────────────────┘ │
    │                                                      │
    │  ┌──────────────────────────────────────────────────┐ │
    │  │  Load Balancers / Routers                        │ │
    │  │  (Direct traffic, Anycast, health checks)       │ │
    │  └──────────────────────────────────────────────────┘ │
    │                                                      │
    │  Network: 10-100 Gbps peering with local ISPs       │
    └──────────────────────────────────────────────────────┘

GLOBAL CDN SCALE (2025)
─────────────────────────────────────────────────────────────
    Cloudflare:     330+ cities, 120+ countries
    Akamai:         4,200+ PoPs, 135+ countries
    AWS CloudFront: 600+ PoPs, 100+ cities
    Fastly:         90+ PoPs (fewer but larger, programmable)
    Google Cloud CDN: 180+ PoPs via Google's network
```

### 1.2 Tiered Caching

```
TIERED CACHING — REDUCING ORIGIN LOAD
═══════════════════════════════════════════════════════════════

Without tiered caching:
    Every edge PoP with a cache miss goes directly to origin.
    100 PoPs × 1 cache miss each = 100 requests to origin

    ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     ┌────────┐
    │Tokyo│ │Seoul│ │Delhi│ │Dubai│ ···→ │ Origin │
    │ MISS│→│ MISS│→│ MISS│→│ MISS│     │Virginia│
    └─────┘ └─────┘ └─────┘ └─────┘     └────────┘
                                   100 requests!

With tiered caching (shield / midgress):
    Edge PoPs check a regional "shield" tier first.
    Shield has larger cache, fewer instances.

    ┌─────┐                 ┌──────────┐     ┌────────┐
    │Tokyo│── MISS ──→      │  Shield  │     │ Origin │
    │     │          │      │  (SIN)   │     │Virginia│
    └─────┘          │      │          │     │        │
    ┌─────┐          ├─────→│  Cache   │─?──→│        │
    │Seoul│── MISS ──┘      │  HIT! ✓  │     │        │
    │     │                 │          │     │        │
    └─────┘                 └──────────┘     └────────┘
    ┌─────┐                 ┌──────────┐
    │Delhi│── MISS ──┐      │  Shield  │
    │     │          ├─────→│  (BOM)   │
    └─────┘          │      │  HIT! ✓  │
    ┌─────┐          │      └──────────┘
    │Dubai│── MISS ──┘
    └─────┘

    Only 2 requests reach the shield. Only 1 reaches origin.

CLOUDFRONT ORIGIN SHIELD
─────────────────────────────────────────────────────────────
    Enable origin shield in the region closest to your origin.
    Adds one more cache layer between edge and origin.
    Reduces origin load by 50-80% in practice.

    Edge (330+ locations)
      → Regional Edge Cache (13 locations)
        → Origin Shield (1 location you choose)
          → Your Origin Server
```

### 1.3 How CDNs Connect: Peering and Transit

```
CDN NETWORK CONNECTIVITY
═══════════════════════════════════════════════════════════════

CDNs minimize hops between themselves and ISPs through
direct peering — physical connections in data centers.

INTERNET EXCHANGE POINTS (IXPs)
─────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────┐
    │  Internet Exchange Point (e.g., DE-CIX Frankfurt)│
    │                                                  │
    │  ┌────────┐  ┌────────┐  ┌────────┐            │
    │  │ ISP-A  │──│ Switch │──│ CDN    │            │
    │  │Deutsche│  │ Fabric │  │Akamai  │            │
    │  │Telekom │  │        │  │        │            │
    │  └────────┘  │        │  └────────┘            │
    │              │        │                         │
    │  ┌────────┐  │        │  ┌────────┐            │
    │  │ ISP-B  │──│        │──│ CDN    │            │
    │  │Vodafone│  │        │  │Cloudfl.│            │
    │  └────────┘  └────────┘  └────────┘            │
    └──────────────────────────────────────────────────┘

    Direct peering means CDN traffic to ISP subscribers
    crosses ONE network hop instead of traversing the
    public internet through multiple autonomous systems.

    DE-CIX Frankfurt: 1,100+ connected networks
    AMS-IX Amsterdam: 900+ connected networks
    LINX London:      950+ connected networks

EMBEDDED CACHING
─────────────────────────────────────────────────────────────
Some CDNs place servers INSIDE ISP networks.

    ┌──────────────────────────────────────────────────┐
    │  ISP Network (e.g., Comcast)                     │
    │                                                  │
    │  ┌──────────┐        ┌──────────┐              │
    │  │ Akamai   │        │ Netflix  │              │
    │  │ Cache    │        │ OCA      │              │
    │  │ Server   │        │ Server   │              │
    │  └──────────┘        └──────────┘              │
    │                                                  │
    │  CDN content never leaves the ISP network!      │
    │  Latency: <5ms. Bandwidth: free to ISP.         │
    └──────────────────────────────────────────────────┘

    Netflix Open Connect: 18,000+ servers in 6,000+ ISPs
    Serves 95%+ of Netflix traffic from within ISP networks
```

---

## Part 2: Cache Mechanics

### 2.1 Cache-Control Headers

```
HTTP CACHE-CONTROL — THE FULL PICTURE
═══════════════════════════════════════════════════════════════

The Cache-Control header tells CDNs (and browsers) how
to cache a response.

DIRECTIVES REFERENCE
─────────────────────────────────────────────────────────────

    CACHEABLE FOR A DURATION
    ─────────────────────────────────────────────
    Cache-Control: public, max-age=86400

    public:    Any cache can store (CDN, browser, proxy)
    max-age:   Cache for N seconds (86400 = 24 hours)

    DIFFERENT TTL FOR CDN vs BROWSER
    ─────────────────────────────────────────────
    Cache-Control: public, max-age=60, s-maxage=86400

    max-age:    Browser caches for 60 seconds
    s-maxage:   Shared caches (CDN) cache for 86400 seconds

    This lets you control browser freshness separately
    from CDN freshness. Very useful pattern.

    STALE CONTENT CONTROL
    ─────────────────────────────────────────────
    Cache-Control: public, max-age=300,
                   stale-while-revalidate=60,
                   stale-if-error=86400

    stale-while-revalidate:  Serve stale for 60s while
                              fetching fresh in background
    stale-if-error:          Serve stale for 24h if origin
                              is down (graceful degradation!)

    NEVER CACHE
    ─────────────────────────────────────────────
    Cache-Control: no-store

    no-store:  Never cache. Not in CDN, not in browser.
               Use for sensitive data (banking, health).

    ⚠️ Common mistake: Using "no-cache" when you mean
       "no-store." no-cache means "cache it, but revalidate
       with origin before serving" — NOT "don't cache."

    REVALIDATION
    ─────────────────────────────────────────────
    Cache-Control: no-cache
    ETag: "v1.2.3-abc123"

    CDN caches the response but checks with origin
    before every serve using If-None-Match header.
    Origin responds 304 Not Modified if unchanged.

PRACTICAL CACHING STRATEGIES
─────────────────────────────────────────────────────────────

    Static assets (images, fonts, JS/CSS with hash):
        Cache-Control: public, max-age=31536000, immutable
        (1 year! Safe because filename contains content hash)

        /assets/app.a1b2c3d4.js   ← change content = new hash
        /assets/style.e5f6g7h8.css

    HTML pages:
        Cache-Control: public, max-age=0, s-maxage=60,
                       stale-while-revalidate=30
        (Browser always revalidates, CDN caches 60s)

    API responses:
        Cache-Control: private, max-age=0
        (Never cache in shared caches — user-specific data)

    API responses (public, same for all users):
        Cache-Control: public, s-maxage=10,
                       stale-while-revalidate=5
        (CDN caches 10s, serves stale 5s while refreshing)
```

### 2.2 Cache Keys and Vary

```
CACHE KEYS — WHAT MAKES A REQUEST "THE SAME"?
═══════════════════════════════════════════════════════════════

A cache key determines if two requests can share a response.

DEFAULT CACHE KEY
─────────────────────────────────────────────────────────────
    Scheme + Host + Path + Query String

    https://example.com/image.png         → Key 1
    https://example.com/image.png?v=2     → Key 2  (different!)
    http://example.com/image.png          → Key 3  (different!)
    https://example.com/IMAGE.png         → Key 4  (depends on CDN)

THE Vary HEADER — SPLITTING CACHES
─────────────────────────────────────────────────────────────
    Vary tells the CDN: "The response changes based on
    these request headers. Cache separately for each value."

    Vary: Accept-Encoding
    ─────────────────────────────────────────────────
    Cache separately for gzip, brotli, identity.

        GET /app.js  Accept-Encoding: gzip   → Cached (gzip)
        GET /app.js  Accept-Encoding: br     → Cached (brotli)
        GET /app.js  (no encoding)           → Cached (plain)

    Vary: Accept-Language
    ─────────────────────────────────────────────────
    Cache separately per language. Sounds good, BUT:

        en, en-US, en-GB, en-AU, en-CA, en-us, EN-US...
        Each is a different cache key!

        ⚠️  Can destroy cache hit ratio. Normalize first!

    Vary: *
    ─────────────────────────────────────────────────
    NEVER cache. Every request is unique.
    This is almost always a mistake.

CACHE KEY BEST PRACTICES
─────────────────────────────────────────────────────────────
    ✓ Include only what affects the response
    ✓ Strip unnecessary query parameters (tracking: utm_*, fbclid)
    ✓ Sort query parameters (a=1&b=2 = b=2&a=1)
    ✓ Normalize Accept-Encoding to a few canonical values
    ✗ Don't Vary on Cookie (almost every user has different cookies)
    ✗ Don't Vary on User-Agent (thousands of unique values)
```

### 2.3 Cache Invalidation

```
CACHE INVALIDATION — "THE HARDEST PROBLEM"
═══════════════════════════════════════════════════════════════

    "There are only two hard things in Computer Science:
     cache invalidation and naming things."
     — Phil Karlton

STRATEGY 1: TTL-BASED EXPIRATION
─────────────────────────────────────────────────────────────
    Just wait for the cache to expire naturally.

    max-age=300 → Content refreshes every 5 minutes
    max-age=60  → Content refreshes every minute

    Pros: Simple, no invalidation infrastructure needed
    Cons: Users see stale content for up to TTL duration

STRATEGY 2: PURGE / BAN
─────────────────────────────────────────────────────────────
    Explicitly remove content from cache.

    # Purge a specific URL
    curl -X PURGE https://cdn.example.com/image.png

    # Ban by pattern (Fastly/Varnish)
    curl -X BAN https://cdn.example.com/ \
      -H "X-Ban-Pattern: /products/.*"

    Pros: Immediate invalidation
    Cons: Must know what to purge, propagation time across PoPs

    Propagation timing:
        Cloudflare:   <2 seconds globally
        CloudFront:   5-15 minutes (invalidation distribution)
        Fastly:       <150ms globally (Instant Purge)
        Akamai:       <5 seconds (Fast Purge)

STRATEGY 3: VERSIONED URLS (CACHE BUSTING)
─────────────────────────────────────────────────────────────
    Include a version/hash in the filename.

    Old: /assets/app.v1.js
    New: /assets/app.v2.js

    Or with content hashes (better):
    Old: /assets/app.a1b2c3.js
    New: /assets/app.d4e5f6.js

    HTML references the new filename → new cache key.
    Old version naturally expires. No purge needed.

    Pros: Perfect cache busting, immutable caching
    Cons: Only works for assets referenced from HTML/CSS
          Can't version API responses or HTML pages

STRATEGY 4: STALE-WHILE-REVALIDATE
─────────────────────────────────────────────────────────────
    Serve stale content while fetching fresh in background.

    Cache-Control: max-age=60, stale-while-revalidate=30

    Timeline:
    ─────────────────────────────────────────────────
    t=0      Content cached. Fresh.
    t=60     max-age expired. Content is "stale."
    t=61     Request arrives:
             → Serve stale content immediately (fast!)
             → Background: fetch fresh from origin
    t=61.5   Background fetch completes
             → Cache updated with fresh content
    t=62     Next request gets fresh content

    Best of both worlds:
    ✓ User always gets instant response
    ✓ Content is never more than max-age + stale-while-revalidate old
    ✗ One user sees stale content per refresh cycle
```

---

## Part 3: Beyond Static Caching

### 3.1 Dynamic Content Acceleration

```
DYNAMIC ACCELERATION — CDNs FOR UNCACHEABLE CONTENT
═══════════════════════════════════════════════════════════════

Not everything can be cached. API responses, personalized
pages, database queries — these are unique per request.
CDNs still help through network optimization.

OPTIMIZATION TECHNIQUES
─────────────────────────────────────────────────────────────

1. PERSISTENT CONNECTIONS (Connection Pooling)
─────────────────────────────────────────────────────────────
    Without CDN:
        Client → TLS handshake → Origin (150ms each time)

    With CDN:
        Client → TLS → Edge (20ms)
        Edge → pre-established connection → Origin (0ms setup)

    Edge keeps warm connections to origin.
    Saves 130ms+ on every new client connection.

2. TCP OPTIMIZATION
─────────────────────────────────────────────────────────────
    CDN edge servers tune TCP parameters for the
    last-mile connection to each client:

    - Larger initial congestion window (start faster)
    - BBR congestion control (better than Cubic on lossy links)
    - TCP Fast Open (reduce handshake RTT)

    Between edge and origin, use optimized backbone:
    - Dedicated fiber paths (less congestion)
    - Fewer hops (direct routing)
    - Larger buffers (handle bursts)

3. PROTOCOL OPTIMIZATION
─────────────────────────────────────────────────────────────
    Client → Edge:  HTTP/3 (QUIC, 0-RTT)
    Edge → Origin:  HTTP/2 (multiplexed, compressed)

    Edge can speak newer protocols to clients even if
    origin only supports HTTP/1.1.

    ┌────────┐  HTTP/3   ┌──────┐  HTTP/2  ┌────────┐
    │ Client │ ────────→ │ Edge │ ───────→ │ Origin │
    │ (QUIC) │  0-RTT    │      │  mux     │ (H/1.1)│
    └────────┘  ~20ms    └──────┘  warm    └────────┘

4. ROUTE OPTIMIZATION (Argo Smart Routing)
─────────────────────────────────────────────────────────────
    Internet routing (BGP) optimizes for policy, not speed.
    CDN backbone routing optimizes for latency.

    Public internet path: Client → 7 hops → Origin (120ms)
    CDN optimized path:   Client → Edge → 3 hops → Origin (75ms)

    Cloudflare Argo: ~30% latency reduction on average
    Measured by testing all paths and choosing fastest.
```

### 3.2 Image Optimization at the Edge

```
EDGE IMAGE OPTIMIZATION
═══════════════════════════════════════════════════════════════

Images are 40-60% of most web page weight.
Modern CDNs optimize images on the fly.

TRANSFORMATIONS
─────────────────────────────────────────────────────────────

    Original: product-photo.png (4.2 MB, 4000x3000, PNG)

    Desktop request:
      → Resize to 1200x900
      → Convert to WebP
      → Quality 85%
      → Result: 142 KB (97% smaller!)

    Mobile request:
      → Resize to 600x450
      → Convert to AVIF
      → Quality 75%
      → Result: 48 KB (99% smaller!)

    Format selection based on Accept header:
      Accept: image/avif,image/webp,image/*  → AVIF
      Accept: image/webp,image/*             → WebP
      Accept: image/*                        → Original format

URL-BASED TRANSFORMS (Cloudflare, imgix)
─────────────────────────────────────────────────────────────
    /cdn-cgi/image/width=800,quality=80,format=auto/photo.jpg

    Parameters:
      width=800        Resize width
      height=600       Resize height
      fit=cover        Crop strategy
      quality=80       Compression level
      format=auto      Best format for browser
      dpr=2            Device pixel ratio (retina)
      blur=50          Gaussian blur
      sharpen=2        Sharpen amount

    Each unique parameter set = separate cache entry.
    Transformed images are cached at edge, not re-generated.
```

---

## Part 4: Edge Computing

### 4.1 What is Edge Compute?

```
EDGE COMPUTE — CODE AT CDN LOCATIONS
═══════════════════════════════════════════════════════════════

Edge compute lets you run code at CDN PoP locations,
within milliseconds of users, instead of in a central
datacenter hundreds of milliseconds away.

THE EVOLUTION
─────────────────────────────────────────────────────────────

    Era 1: Static CDN (cache files)
        "Here's the image, cached at the edge."

    Era 2: Dynamic CDN (optimize delivery)
        "I'll optimize the connection and route."

    Era 3: Edge Compute (run logic)
        "I'll run your code at the edge and respond directly."

    ┌────────┐  request   ┌──────────────┐
    │ Client │ ──────────→│ Edge Worker  │
    │ Tokyo  │            │ Tokyo PoP    │
    │        │←───────────│              │
    └────────┘  response  │ Runs code,   │
        ~5ms              │ may call     │
                          │ origin or    │
                          │ edge DB      │
                          └──────────────┘

    No round trip to origin! Response in single-digit ms.

PLATFORMS
─────────────────────────────────────────────────────────────

    Cloudflare Workers
    ─────────────────────────────────────────────
    Runtime: V8 isolates (not containers)
    Startup: <5ms cold start (no container boot)
    Locations: 330+ cities
    Languages: JavaScript/TypeScript, Rust, C, C++ (WASM)
    Storage: Workers KV (eventually consistent key-value)
             Durable Objects (strongly consistent, single-leader)
             D1 (SQLite at the edge)
             R2 (S3-compatible object storage)
    Limits: 10ms CPU per request (free), 30s (paid)

    AWS Lambda@Edge / CloudFront Functions
    ─────────────────────────────────────────────
    Lambda@Edge:
      Runtime: Node.js, Python
      Locations: 13 regional edge caches
      Cold start: 50-200ms
      Limits: 5s (viewer triggers), 30s (origin triggers)

    CloudFront Functions:
      Runtime: JavaScript (limited)
      Locations: 600+ PoPs (runs everywhere)
      Startup: <1ms
      Limits: 2ms execution, no network calls
      Use for: Header manipulation, URL rewrites, simple auth

    Fastly Compute
    ─────────────────────────────────────────────
    Runtime: WebAssembly
    Startup: ~35μs cold start (microseconds!)
    Locations: 90+ PoPs
    Languages: Rust, Go, JavaScript (compiled to WASM)
    Limits: 120s execution, full network access

    Deno Deploy
    ─────────────────────────────────────────────
    Runtime: Deno (V8-based)
    Locations: 35+ regions
    Languages: TypeScript/JavaScript
    Storage: Deno KV (globally replicated)
```

### 4.2 Edge Compute Use Cases

```
WHAT TO RUN AT THE EDGE
═══════════════════════════════════════════════════════════════

AUTHENTICATION & AUTHORIZATION
─────────────────────────────────────────────────────────────
    Validate JWT tokens at the edge.
    Reject unauthorized requests before they reach origin.

    // Cloudflare Worker example
    export default {
      async fetch(request) {
        const token = request.headers.get("Authorization");
        if (!token) {
          return new Response("Unauthorized", { status: 401 });
        }

        try {
          const payload = await verifyJWT(token, JWT_SECRET);
          // Add user info as header for origin
          const newRequest = new Request(request);
          newRequest.headers.set("X-User-ID", payload.sub);
          return fetch(newRequest);
        } catch (e) {
          return new Response("Invalid token", { status: 403 });
        }
      }
    };

A/B TESTING
─────────────────────────────────────────────────────────────
    Route users to different origins based on cookies/headers.
    No client-side JavaScript, no flash of unstyled content.

    // Assign variant at edge
    const variant = request.headers.get("cookie")?.includes("variant=B")
      ? "B" : "A";
    const origin = variant === "B"
      ? "https://experiment-b.example.com"
      : "https://experiment-a.example.com";

SECURITY HEADERS
─────────────────────────────────────────────────────────────
    Add Content-Security-Policy, HSTS, X-Frame-Options
    consistently across all responses, regardless of origin.

    const securityHeaders = {
      "Content-Security-Policy": "default-src 'self'",
      "Strict-Transport-Security": "max-age=63072000",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "Permissions-Policy": "camera=(), microphone=()"
    };

GEOLOCATION ROUTING
─────────────────────────────────────────────────────────────
    Route requests based on user location, available
    automatically at the edge via request metadata.

    // Cloudflare provides country, city, timezone, etc.
    const country = request.cf.country;  // "JP"
    const city = request.cf.city;        // "Tokyo"

    if (country === "CN") {
      return Response.redirect("https://cn.example.com");
    }

URL REWRITING & REDIRECTS
─────────────────────────────────────────────────────────────
    Handle thousands of redirects at the edge.
    No origin request needed.

    const redirects = {
      "/old-page": "/new-page",
      "/blog/2023/post": "/articles/post",
      // ... thousands of rules
    };
```

---

## Part 5: TLS at the Edge

### 5.1 TLS Termination Strategies

```
TLS TERMINATION — WHERE TO DECRYPT
═══════════════════════════════════════════════════════════════

OPTION 1: FULL (STRICT) — Edge to Origin Encrypted
─────────────────────────────────────────────────────────────

    Client ── HTTPS ──→ Edge ── HTTPS ──→ Origin
              TLS 1.3          TLS 1.3
              Edge cert         Origin cert

    Edge verifies origin certificate (strict validation).
    End-to-end encryption. Most secure.

    ✓ Data encrypted everywhere
    ✓ Protects against MITM between edge and origin
    ✗ Must manage certificate on origin
    ✗ Slightly higher latency (TLS handshake to origin)

OPTION 2: FULL — Edge Encrypts, Doesn't Validate Origin
─────────────────────────────────────────────────────────────

    Client ── HTTPS ──→ Edge ── HTTPS ──→ Origin
              TLS 1.3          TLS 1.3
              Edge cert         Self-signed OK

    Edge connects to origin via HTTPS but accepts any cert.

    ✓ Encrypted in transit
    ✗ Origin certificate not validated (MITM possible)
    ✗ False sense of security

OPTION 3: FLEXIBLE — Encrypted to Edge Only
─────────────────────────────────────────────────────────────

    Client ── HTTPS ──→ Edge ── HTTP ──→ Origin
              TLS 1.3          Plaintext!

    ⚠️  Data is unencrypted between edge and origin.
        Only acceptable if edge and origin are in the
        same physical network (never over the internet).

    ✓ Simple origin setup (no certificate)
    ✗ Data exposed between edge and origin
    ✗ Common source of security vulnerabilities

OPTION 4: ORIGIN PULL CERTIFICATE (mTLS)
─────────────────────────────────────────────────────────────

    Client ── HTTPS ──→ Edge ── mTLS ──→ Origin
                               Both sides
                               present certs

    Origin ONLY accepts connections from CDN.
    Prevents direct-to-origin attacks bypassing CDN/WAF.

    ✓ Origin guaranteed that traffic comes from CDN
    ✓ Can't bypass CDN protections
    ✗ More complex certificate management

CERTIFICATE MANAGEMENT AT SCALE
─────────────────────────────────────────────────────────────
    CDNs manage millions of certificates automatically:

    Let's Encrypt integration:
        Auto-issue, auto-renew, zero downtime rotation.

    SAN certificates:
        One cert covering many domains (efficient for CDNs).

    Keyless SSL (Cloudflare):
        Private key never leaves your infrastructure.
        CDN handles TLS but calls your key server for signing.
        Required by some regulatory/compliance frameworks.
```

---

## Did You Know?

- **Netflix's Open Connect serves over 400 Gbps from a single ISP-embedded server.** Their custom-built CDN appliances use FreeBSD, nginx, and NVMe SSDs to stream video from within ISP networks. During peak hours, Netflix accounts for roughly 15% of all downstream internet traffic in the United States, and nearly all of it is served from these embedded boxes.

- **Akamai delivers between 15-30% of all web traffic worldwide.** Founded in 1998 by MIT mathematicians who won a challenge to solve internet congestion, Akamai now operates over 365,000 servers. When Akamai sneezes, the internet catches a cold — their outage in July 2021 briefly took down major banks, airlines, and government sites.

- **The `stale-while-revalidate` Cache-Control directive was standardized in RFC 5861 in 2010, but didn't see wide browser support until Chrome 75 in 2019.** For nearly a decade, this elegant caching strategy existed only in CDNs and reverse proxies. Now it works end-to-end, giving users instant responses while quietly refreshing content in the background.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Caching responses with `Set-Cookie` | Users see other users' sessions | `Cache-Control: private` for personalized content |
| `Vary: User-Agent` | Thousands of cache variants, near-zero hit rate | Normalize to device class (mobile/desktop/tablet) |
| No `s-maxage` distinct from `max-age` | Browser and CDN cache for same duration | Use `s-maxage` for CDN, `max-age` for browser |
| Cache busting via query string only | Some CDNs ignore query strings by default | Use filename hashing: `app.a1b2c3.js` |
| Flexible TLS (HTTP between edge and origin) | Data exposed on the wire between CDN and origin | Use Full (Strict) with validated origin certificate |
| Not setting `immutable` on hashed assets | Browsers revalidate on refresh despite long max-age | Add `immutable` to skip revalidation entirely |
| Ignoring CDN cache hit ratio | Poor performance, high origin load, wasted CDN spend | Monitor hit ratio; target >90% for static content |
| Edge functions calling origin on every request | Adds latency, defeats purpose of edge compute | Cache at edge, use edge KV stores when possible |
| Single CDN provider without failover | CDN outage = global outage | Consider multi-CDN with DNS-based failover |

---

## Quiz

1. **Explain the difference between `max-age`, `s-maxage`, and `stale-while-revalidate`. When would you use all three together?**
   <details>
   <summary>Answer</summary>

   - `max-age=N`: How long the **browser** (and any cache) considers the response fresh.
   - `s-maxage=N`: How long **shared caches** (CDNs, proxies) consider the response fresh. Overrides `max-age` for shared caches only.
   - `stale-while-revalidate=N`: After the response becomes stale, serve the stale version for up to N seconds while fetching a fresh copy in the background.

   Example combining all three:
   ```
   Cache-Control: public, max-age=0, s-maxage=300, stale-while-revalidate=60
   ```

   This means:
   - Browser: Always revalidate (max-age=0) — users always get fresh content on hard refresh
   - CDN: Cache for 5 minutes (s-maxage=300) — reduces origin load
   - CDN stale serving: After 5 minutes, serve stale for up to 60 seconds while fetching fresh in background — users never wait for origin

   Use all three together for HTML pages or API responses that change periodically but where instant freshness is less important than instant response.
   </details>

2. **Why does `Vary: User-Agent` destroy CDN cache hit rates? What's the correct approach for serving different content to mobile vs desktop?**
   <details>
   <summary>Answer</summary>

   `Vary: User-Agent` creates a separate cache entry for every unique User-Agent string. In 2025, there are thousands of unique User-Agent strings — different browser versions, OS versions, device models, and bot crawlers each have distinct strings.

   A page that should be cached once gets cached thousands of times, and each variation rarely gets a cache hit because the exact same User-Agent string repeats infrequently.

   Correct approach:
   1. **Client hints**: Use `Sec-CH-UA-Mobile` header and `Vary: Sec-CH-UA-Mobile` — only two values: `?0` (desktop) and `?1` (mobile).
   2. **CDN device detection**: Most CDNs (Cloudflare, Akamai, Fastly) provide a normalized device-type header (mobile/desktop/tablet). Vary on that header instead.
   3. **Responsive design**: Serve the same HTML and use CSS media queries for layout changes — no Vary header needed at all.
   4. **Edge function**: Detect device type in an edge function and rewrite to different origins or transform the response.
   </details>

3. **What is tiered caching and how does it reduce origin load?**
   <details>
   <summary>Answer</summary>

   Tiered caching adds intermediate cache layers between edge PoPs and the origin server.

   Without tiered caching, every edge PoP with a cache miss makes a separate request to the origin. With 300+ PoPs, a popular piece of new content could trigger 300 near-simultaneous requests to origin — a "thundering herd."

   With tiered caching:
   - **Edge tier**: Hundreds of PoPs, small caches, serve most hits
   - **Shield/midgress tier**: A few regional caches (5-15 locations), larger storage
   - **Origin**: Your actual server

   When an edge PoP has a cache miss, it checks the regional shield first. If the shield has the content (populated by an earlier request from a different edge PoP in the same region), the origin is never contacted.

   In practice, tiered caching reduces origin requests by 50-80%. It is especially effective for "long tail" content that is popular enough to be in the shield cache but not popular enough to stay in every individual edge cache.
   </details>

4. **Compare Cloudflare Workers, Lambda@Edge, and CloudFront Functions. When would you choose each?**
   <details>
   <summary>Answer</summary>

   **Cloudflare Workers**:
   - Best for: Full application logic at the edge, lowest latency globally
   - V8 isolates with <5ms cold start, 330+ locations
   - Rich ecosystem: KV, Durable Objects, D1, R2, Queues
   - Choose when: Building full edge applications, need consistent global performance, want edge-native storage

   **Lambda@Edge**:
   - Best for: Complex request/response manipulation tied to CloudFront
   - Node.js/Python, runs at 13 regional edge caches (not all PoPs)
   - 50-200ms cold starts, up to 30s execution
   - Choose when: Already on AWS, need to modify CloudFront behavior, need longer execution time or origin-facing triggers

   **CloudFront Functions**:
   - Best for: Simple, fast header manipulation and URL rewrites
   - JavaScript only, runs at all 600+ CloudFront PoPs
   - <1ms startup, but limited to 2ms execution, no network calls
   - Choose when: Need simple transformations at every PoP (redirect rules, header injection, simple auth token validation)

   Summary:
   - Need full edge app? → Cloudflare Workers or Fastly Compute
   - Need AWS integration with moderate logic? → Lambda@Edge
   - Need ultra-fast, ultra-simple transforms? → CloudFront Functions
   </details>

5. **Your e-commerce site has a product page that shows the same product info to all users but includes a "Welcome, {name}" header and a cart count badge. How would you architect this for CDN caching?**
   <details>
   <summary>Answer</summary>

   The challenge is that the page is 95% cacheable (product info) but 5% personalized (name, cart count). Several approaches:

   1. **Edge Side Includes (ESI)**: Cache the page body at the CDN and use ESI tags to inject personalized fragments. The CDN assembles the final page from cached + dynamic parts. Supported by Akamai, Fastly, Varnish.

   2. **Client-side personalization** (recommended for most cases):
      - Cache the full HTML page at CDN (`s-maxage=300`)
      - Use JavaScript to fetch user name and cart count from an API
      - API call: `GET /api/user/me` with `Cache-Control: private`
      - Page loads instantly from cache, personalization fills in within 100ms
      - This is how most major e-commerce sites work

   3. **Edge compute assembly**:
      - Edge function fetches cached page body from CDN cache
      - Edge function fetches user data from edge KV store (if available)
      - Assembles final HTML with personalization injected server-side
      - More complex but avoids client-side JavaScript flash

   4. **HTML streaming with edge injection**:
      - Stream the cached HTML from CDN
      - At the edge, inject personalized data into specific markers
      - User sees content progressively without waiting for full assembly

   The client-side approach (option 2) is simplest and most resilient. The page works even if the personalization API is slow or down.
   </details>

---

## Hands-On Exercise

**Objective**: Deploy a static site with CDN-style caching, custom cache headers, and an edge function that adds security headers.

**Environment**: kind cluster with nginx as origin + Varnish as CDN simulation

### Part 1: Deploy Origin Server (15 minutes)

```bash
# Create a kind cluster
kind create cluster --name cdn-lab

# Create a static site with different asset types
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: static-site
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head>
      <title>CDN Lab</title>
      <link rel="stylesheet" href="/assets/style.css">
    </head>
    <body>
      <h1>CDN & Edge Computing Lab</h1>
      <p>Served at: <span id="time"></span></p>
      <img src="/assets/logo.svg" alt="Logo">
      <script src="/assets/app.js"></script>
    </body>
    </html>
  style.css: |
    body { font-family: sans-serif; max-width: 800px; margin: 2em auto; }
    h1 { color: #2563eb; }
  app.js: |
    document.getElementById('time').textContent = new Date().toISOString();
  logo.svg: |
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
      <circle cx="50" cy="50" r="40" fill="#2563eb"/>
      <text x="50" y="55" text-anchor="middle" fill="white" font-size="16">CDN</text>
    </svg>
  nginx.conf: |
    server {
      listen 80;

      # HTML — short cache, revalidate
      location / {
        root /usr/share/nginx/html;
        index index.html;
        add_header Cache-Control "public, max-age=0, s-maxage=60, stale-while-revalidate=30";
        add_header X-Served-By "origin";
      }

      # Static assets — long cache, immutable
      location /assets/ {
        alias /usr/share/nginx/html/assets/;
        add_header Cache-Control "public, max-age=31536000, immutable";
        add_header X-Served-By "origin";
      }

      # Health check
      location /healthz {
        return 200 'OK';
        add_header Content-Type text/plain;
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: origin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: origin
  template:
    metadata:
      labels:
        app: origin
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          volumeMounts:
            - name: config
              mountPath: /etc/nginx/conf.d/default.conf
              subPath: nginx.conf
            - name: html
              mountPath: /usr/share/nginx/html/index.html
              subPath: index.html
            - name: assets-css
              mountPath: /usr/share/nginx/html/assets/style.css
              subPath: style.css
            - name: assets-js
              mountPath: /usr/share/nginx/html/assets/app.js
              subPath: app.js
            - name: assets-svg
              mountPath: /usr/share/nginx/html/assets/logo.svg
              subPath: logo.svg
      volumes:
        - name: config
          configMap:
            name: static-site
            items: [{ key: nginx.conf, path: nginx.conf }]
        - name: html
          configMap:
            name: static-site
            items: [{ key: index.html, path: index.html }]
        - name: assets-css
          configMap:
            name: static-site
            items: [{ key: style.css, path: style.css }]
        - name: assets-js
          configMap:
            name: static-site
            items: [{ key: app.js, path: app.js }]
        - name: assets-svg
          configMap:
            name: static-site
            items: [{ key: logo.svg, path: logo.svg }]
---
apiVersion: v1
kind: Service
metadata:
  name: origin
spec:
  selector:
    app: origin
  ports:
    - port: 80
EOF
```

### Part 2: Deploy Varnish as CDN Simulator (15 minutes)

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: varnish-config
data:
  default.vcl: |
    vcl 4.1;

    backend origin {
      .host = "origin";
      .port = "80";
      .probe = {
        .url = "/healthz";
        .interval = 5s;
        .timeout = 2s;
        .threshold = 3;
        .window = 5;
      }
    }

    sub vcl_recv {
      # Strip cookies for static assets (improve cache hit rate)
      if (req.url ~ "\.(css|js|svg|png|jpg|gif|ico|woff2)$") {
        unset req.http.Cookie;
      }
    }

    sub vcl_backend_response {
      # Add cache status header
      set beresp.http.X-Cache-TTL = beresp.ttl;
    }

    sub vcl_deliver {
      # Add hit/miss indicator
      if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
        set resp.http.X-Cache-Hits = obj.hits;
      } else {
        set resp.http.X-Cache = "MISS";
      }

      # Security headers (simulating edge function)
      set resp.http.X-Content-Type-Options = "nosniff";
      set resp.http.X-Frame-Options = "DENY";
      set resp.http.Referrer-Policy = "strict-origin-when-cross-origin";
      set resp.http.Strict-Transport-Security = "max-age=63072000; includeSubDomains";
      set resp.http.Content-Security-Policy = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'";
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cdn-edge
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cdn-edge
  template:
    metadata:
      labels:
        app: cdn-edge
    spec:
      containers:
        - name: varnish
          image: varnish:7.6
          ports:
            - containerPort: 80
          args:
            - "-f"
            - "/etc/varnish/default.vcl"
            - "-s"
            - "malloc,256m"
            - "-a"
            - "0.0.0.0:80"
          volumeMounts:
            - name: config
              mountPath: /etc/varnish/default.vcl
              subPath: default.vcl
      volumes:
        - name: config
          configMap:
            name: varnish-config
---
apiVersion: v1
kind: Service
metadata:
  name: cdn-edge
spec:
  selector:
    app: cdn-edge
  ports:
    - port: 80
EOF
```

### Part 3: Test Caching Behavior (20 minutes)

```bash
# Deploy a test client
kubectl run test-client --image=curlimages/curl:8.11.1 --rm -it -- sh

# Inside the test client:

# 1. First request (cache MISS)
curl -sI http://cdn-edge/ | grep -E "X-Cache|Cache-Control|X-Served"

# Expected:
# X-Cache: MISS
# Cache-Control: public, max-age=0, s-maxage=60, stale-while-revalidate=30

# 2. Second request (cache HIT)
curl -sI http://cdn-edge/ | grep -E "X-Cache|Cache-Control"

# Expected:
# X-Cache: HIT
# X-Cache-Hits: 1

# 3. Check security headers from "edge function"
curl -sI http://cdn-edge/ | grep -E "X-Content-Type|X-Frame|Referrer|Strict-Transport|Content-Security"

# 4. Test static assets (long cache)
curl -sI http://cdn-edge/assets/style.css | grep -E "X-Cache|Cache-Control"

# Expected:
# Cache-Control: public, max-age=31536000, immutable

# 5. Rapid requests — watch hit count increase
for i in $(seq 1 10); do
  echo "Request $i:"
  curl -sI http://cdn-edge/ | grep "X-Cache"
done
```

### Part 4: Measure Cache Effectiveness (10 minutes)

```bash
# Still inside test client:

# Compare direct origin vs CDN edge
echo "=== Direct to Origin ==="
time curl -so /dev/null http://origin/
time curl -so /dev/null http://origin/
time curl -so /dev/null http://origin/

echo "=== Via CDN Edge (cached) ==="
time curl -so /dev/null http://cdn-edge/
time curl -so /dev/null http://cdn-edge/
time curl -so /dev/null http://cdn-edge/

# The CDN responses should be faster after the first request
# because they're served from Varnish cache without hitting origin
```

### Clean Up

```bash
kind delete cluster --name cdn-lab
```

**Success Criteria**:
- [ ] Observed cache MISS on first request and HIT on subsequent requests
- [ ] Verified different Cache-Control headers for HTML vs static assets
- [ ] Confirmed security headers are injected by the CDN layer (Varnish)
- [ ] Measured latency difference between origin and cached responses
- [ ] Understood the relationship between `max-age`, `s-maxage`, and `stale-while-revalidate`
- [ ] Watched cache hit count increase with repeated requests

---

## Further Reading

- **"High Performance Browser Networking"** — Ilya Grigorik. Free online at hpbn.co. Essential reading on HTTP caching, CDNs, and network performance optimization.

- **"CDN Planet"** — Comprehensive CDN comparison site with real-world performance data across providers.

- **Cloudflare Blog: "How We Built Workers"** — Deep dive into V8 isolate architecture and why it enables sub-millisecond cold starts.

- **Netflix Open Connect** — Netflix's documentation on their custom CDN architecture, the largest single-purpose CDN in the world.

---

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **CDNs solve a physics problem**: No amount of code optimization overcomes the speed of light. CDNs move content physically closer to users
- [ ] **Tiered caching prevents origin overload**: Edge → Shield → Origin reduces origin requests by 50-80%
- [ ] **`s-maxage` separates CDN and browser caching**: Different TTLs for shared and private caches give you fine-grained control
- [ ] **`stale-while-revalidate` is the best of both worlds**: Users get instant responses while fresh content loads in the background
- [ ] **Cache keys determine hit rates**: Adding unnecessary Vary headers or query parameters destroys cache effectiveness
- [ ] **Edge compute runs code at CDN locations**: V8 isolates and WASM enable full application logic with sub-5ms cold starts
- [ ] **TLS termination strategy matters for security**: Full (Strict) with origin certificate validation should be the default, not Flexible
- [ ] **Client-side personalization beats ESI for most cases**: Cache the page, personalize with JavaScript — simplest and most resilient approach

---

## Next Module

[Module 1.3: WAF & DDoS Mitigation](../module-1.3-waf-ddos/) — How Web Application Firewalls protect against OWASP Top 10 attacks, and how DDoS mitigation works at scale.
