---
title: "Module 1.8: API Aggregation & Extension API Servers"
slug: k8s/extending/module-1.8-api-aggregation
sidebar:
  order: 9
---
> **Complexity**: `[COMPLEX]` - Building custom API servers
>
> **Time to Complete**: 5 hours
>
> **Prerequisites**: Module 1.6 (Admission Webhooks), understanding of TLS, HTTP REST APIs

---

## Why This Module Matters

CRDs are the easy path to extending the Kubernetes API: define a schema, apply it, and the API Server handles storage, CRUD operations, and watch streams automatically. But CRDs have hard limits. They store data in etcd (no external database), they support only CRUD operations (no custom verbs), they use standard Kubernetes RBAC (no custom authorization), and they cannot implement custom storage or subresources beyond status and scale.

**API Aggregation** removes all of those limits. An aggregated API server is a full HTTP server that responds to the Kubernetes API conventions but can do anything: query an external database, proxy to a SaaS API, compute metrics on the fly, implement custom authorization, or serve data from an entirely different storage backend. The `metrics-server` that powers `kubectl top` is an aggregated API server. So is the `custom-metrics-apiserver` that powers HPA with custom metrics.

When CRDs are not enough, API Aggregation is the answer.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Build** a custom aggregated API server that serves resources from an external data source (database, SaaS API, computed metrics)
2. **Register** an APIService object and configure the kube-aggregator to route requests to your custom server
3. **Implement** authentication delegation and authorization so your aggregated API respects cluster RBAC
4. **Evaluate** when to use API Aggregation vs. CRDs by comparing storage, authorization, and subresource requirements

> **The Embassy Analogy**
>
> If the Kubernetes API Server is a country's government building, CRDs are like adding new departments inside the building -- they use the existing infrastructure (etcd, RBAC, admission). An aggregated API server is like an embassy of another country inside the same building. Visitors (kubectl, controllers) enter through the same front door and follow the same protocols, but when they request something from the embassy, their request is routed to the embassy staff (your custom server) who handle it with their own rules, their own database, and their own logic. The building (kube-aggregator) just handles the routing.

---

## What You'll Learn

By the end of this module, you will be able to:
- Decide when to use API Aggregation vs CRDs
- Understand how kube-aggregator routes requests
- Register an APIService to proxy requests to your server
- Build a minimal Extension API Server in Go
- Handle discovery, versioning, and Kubernetes API conventions
- Deploy and test an aggregated API server

---

## Did You Know?

- **kube-aggregator is built into the API Server**: It is not a separate component. The main API Server binary includes the aggregation proxy. When an APIService resource is created, the built-in aggregator starts proxying matching requests to the specified backend service.

- **`kubectl top` does not query the API Server directly**: It queries `metrics.k8s.io`, which is an aggregated API served by `metrics-server`. The metrics are computed from kubelet's resource metrics endpoint and served through the Kubernetes API conventions, making them accessible via standard clients.

- **The API Aggregation layer handles about 15% of API traffic** in a cluster with metrics-server, custom metrics, and external secrets. Most of this is from HPA polling for metrics every 15 seconds.

---

## Part 1: CRDs vs API Aggregation

### 1.1 Decision Matrix

| Requirement | CRD | API Aggregation |
|------------|-----|-----------------|
| CRUD on YAML-like resources | Yes | Yes |
| Stored in etcd | Yes (automatic) | No (bring your own storage) |
| Standard RBAC | Yes (automatic) | You implement |
| Custom storage backend | No | Yes |
| Custom subresources (beyond status/scale) | No | Yes |
| Custom verbs (connect, proxy) | No | Yes |
| Computed/dynamic responses | No | Yes |
| Short-lived / volatile data | Wasteful (etcd) | Ideal |
| Custom admission logic | Via webhooks | Built-in |
| Kubernetes watch support | Automatic | You implement |
| Effort to implement | Low | High |

### 1.2 When to Choose API Aggregation

Use API Aggregation when you need:

1. **External data sources**: Your API reads from a database, SaaS API, or metric store
2. **Computed resources**: Data is calculated at query time (e.g., metrics, reports)
3. **Custom protocols**: You need `connect` or `proxy` subresources (like `kubectl exec`)
4. **Non-CRUD operations**: Custom HTTP verbs or streaming responses
5. **Volatile data**: High-frequency data that should not be stored in etcd

Use CRDs for everything else. CRDs are simpler, more maintainable, and get automatic features (watch, server-side apply, schema validation, admission, etc.).

> **Stop and think**: Imagine you are building an integration with a legacy enterprise identity system. The system requires complex LDAP queries that take 3-5 seconds to resolve, and the data changes constantly. If you were forced to use a CRD instead of an Aggregated API, what specific architectural bottlenecks and scaling issues would your cluster face?

### 1.3 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                 API Aggregation Architecture                         │
│                                                                     │
│   kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods              │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │  kube-apiserver                                           │     │
│   │                                                           │     │
│   │  1. Authentication (as usual)                             │     │
│   │  2. Authorization (as usual)                              │     │
│   │  3. kube-aggregator checks APIService registry            │     │
│   │                                                           │     │
│   │     /apis/metrics.k8s.io → APIService exists?             │     │
│   │     ├── No → 404 Not Found                               │     │
│   │     └── Yes → Proxy to backend service                   │     │
│   │                                                           │     │
│   │  4. Proxies request to service (with user impersonation)  │     │
│   └──────────────────────────────┬───────────────────────────┘     │
│                                  │ HTTPS                           │
│                                  ▼                                  │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │  Extension API Server (your code)                         │     │
│   │                                                           │     │
│   │  Service: metrics-server.kube-system                      │     │
│   │                                                           │     │
│   │  Handles:                                                 │     │
│   │  - /apis/metrics.k8s.io/v1beta1 (discovery)              │     │
│   │  - /apis/metrics.k8s.io/v1beta1/pods (resource list)     │     │
│   │  - /apis/metrics.k8s.io/v1beta1/nodes (resource list)    │     │
│   │                                                           │     │
│   │  Storage: In-memory (scraped from kubelets)               │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: The APIService Resource

### 2.1 Registering an APIService

An APIService tells kube-aggregator: "proxy requests for this API group/version to this backend service."

```yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1alpha1.data.kubedojo.io     # {version}.{group}
spec:
  group: data.kubedojo.io
  version: v1alpha1
  service:
    name: kubedojo-data-api            # Service name
    namespace: kubedojo-system          # Service namespace
    port: 443
  groupPriorityMinimum: 1000          # Priority over other groups
  versionPriority: 15                  # Priority over other versions
  caBundle: <base64-encoded-CA-cert>   # CA to verify backend TLS
  insecureSkipTLSVerify: false         # Never true in production
```

### 2.2 APIService Fields

| Field | Description | Typical Value |
|-------|------------|---------------|
| `group` | API group this service handles | `data.kubedojo.io` |
| `version` | API version | `v1alpha1` |
| `service.name` | Kubernetes Service pointing to your server | `kubedojo-data-api` |
| `service.namespace` | Namespace of the Service | `kubedojo-system` |
| `service.port` | Port of the Service | `443` |
| `groupPriorityMinimum` | Priority for API group discovery (higher = more important) | `1000` |
| `versionPriority` | Priority within the group (higher = preferred version) | `15` |
| `caBundle` | Base64 CA cert for TLS verification | CA cert bytes |
| `insecureSkipTLSVerify` | Skip TLS verification (dev only) | `false` |

### 2.3 How the Proxy Works

When the aggregator proxies a request:

1. The original user's credentials are stripped
2. The aggregator adds impersonation headers: `Impersonate-User`, `Impersonate-Group`
3. The request is forwarded to the backend service over HTTPS
4. Your server sees the original user identity via these headers
5. Your server can implement its own authorization based on this identity

```
Original request:
  GET /apis/data.kubedojo.io/v1alpha1/namespaces/default/records
  Authorization: Bearer <user-token>

Proxied request to your server:
  GET /apis/data.kubedojo.io/v1alpha1/namespaces/default/records
  Impersonate-User: alice
  Impersonate-Group: developers
  Impersonate-Group: system:authenticated
  Authorization: Bearer <aggregator-token>
```

> **Pause and predict**: The kube-aggregator passes the original user's identity via `Impersonate-User` headers. If your extension API server is exposed on a NodePort and a malicious pod inside the cluster connects directly to your extension server's IP, forging these headers, what is the result? How must your extension server's authentication be configured to prevent this bypass?

---

## Part 3: Building an Extension API Server

### 3.1 What Your Server Must Implement

At minimum, an extension API server must handle these endpoints:

| Endpoint | Purpose | Required |
|----------|---------|----------|
| `/apis/{group}/{version}` | API resource discovery | Yes |
| `/apis/{group}` | Group discovery | Yes (for proper kubectl behavior) |
| `/apis` | Root discovery | Optional (aggregator handles this) |
| `/apis/{group}/{version}/{resource}` | List resources | Yes |
| `/apis/{group}/{version}/namespaces/{ns}/{resource}` | List namespaced resources | If namespaced |
| `/apis/{group}/{version}/namespaces/{ns}/{resource}/{name}` | Get single resource | Yes |
| `/healthz` | Health check | Yes |
| `/openapi/v2` or `/openapi/v3` | OpenAPI schema | Recommended |

### 3.2 Project Structure

```
extension-api-server/
├── go.mod
├── go.sum
├── cmd/
│   └── server/
│       └── main.go          # Entry point
├── pkg/
│   ├── apiserver/
│   │   └── apiserver.go     # Server setup
│   ├── handlers/
│   │   ├── discovery.go     # API discovery endpoints
│   │   └── records.go       # Resource CRUD handlers
│   ├── storage/
│   │   └── storage.go       # Backend storage interface
│   └── types/
│       └── types.go         # API types
└── manifests/
    ├── apiservice.yaml
    ├── deployment.yaml
    ├── rbac.yaml
    └── service.yaml
```

### 3.3 API Types

```go
// pkg/types/types.go
package types

import metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

// DataRecord represents a record from an external database.
type DataRecord struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   DataRecordSpec   `json:"spec"`
	Status DataRecordStatus `json:"status,omitempty"`
}

type DataRecordSpec struct {
	// Source is the external database that holds this record.
	Source string `json:"source"`

	// Query is the query or key used to retrieve this record.
	Query string `json:"query"`

	// Data holds the record data as key-value pairs.
	Data map[string]string `json:"data,omitempty"`
}

type DataRecordStatus struct {
	// LastSyncTime is when the record was last read from the source.
	LastSyncTime metav1.Time `json:"lastSyncTime,omitempty"`

	// SyncStatus indicates whether the record is current.
	SyncStatus string `json:"syncStatus,omitempty"`
}

// DataRecordList is a list of DataRecord resources.
type DataRecordList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []DataRecord `json:"items"`
}
```

### 3.4 Storage Backend

```go
// pkg/storage/storage.go
package storage

import (
	"fmt"
	"sync"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/kubedojo/extension-api/pkg/types"
)

// Store is an in-memory store that simulates an external database.
// In production, this would be a real database client.
type Store struct {
	mu      sync.RWMutex
	records map[string]map[string]*types.DataRecord // namespace -> name -> record
}

// NewStore creates a new in-memory store with seed data.
func NewStore() *Store {
	s := &Store{
		records: make(map[string]map[string]*types.DataRecord),
	}
	s.seed()
	return s
}

func (s *Store) seed() {
	now := metav1.Now()

	seedData := []types.DataRecord{
		{
			TypeMeta: metav1.TypeMeta{
				APIVersion: "data.kubedojo.io/v1alpha1",
				Kind:       "DataRecord",
			},
			ObjectMeta: metav1.ObjectMeta{
				Name:              "user-config",
				Namespace:         "default",
				CreationTimestamp: now,
				ResourceVersion:   "1",
				UID:               "a1b2c3d4-0001-0001-0001-000000000001",
			},
			Spec: types.DataRecordSpec{
				Source: "postgres",
				Query:  "SELECT * FROM config WHERE env='production'",
				Data: map[string]string{
					"max_connections": "100",
					"timeout_ms":     "5000",
					"log_level":      "info",
				},
			},
			Status: types.DataRecordStatus{
				LastSyncTime: now,
				SyncStatus:   "Current",
			},
		},
		{
			TypeMeta: metav1.TypeMeta{
				APIVersion: "data.kubedojo.io/v1alpha1",
				Kind:       "DataRecord",
			},
			ObjectMeta: metav1.ObjectMeta{
				Name:              "feature-flags",
				Namespace:         "default",
				CreationTimestamp: now,
				ResourceVersion:   "2",
				UID:               "a1b2c3d4-0001-0001-0001-000000000002",
			},
			Spec: types.DataRecordSpec{
				Source: "redis",
				Query:  "HGETALL feature:flags",
				Data: map[string]string{
					"dark_mode":      "true",
					"new_dashboard":  "false",
					"beta_api":       "true",
				},
			},
			Status: types.DataRecordStatus{
				LastSyncTime: now,
				SyncStatus:   "Current",
			},
		},
		{
			TypeMeta: metav1.TypeMeta{
				APIVersion: "data.kubedojo.io/v1alpha1",
				Kind:       "DataRecord",
			},
			ObjectMeta: metav1.ObjectMeta{
				Name:              "metrics-config",
				Namespace:         "monitoring",
				CreationTimestamp: now,
				ResourceVersion:   "3",
				UID:               "a1b2c3d4-0001-0001-0001-000000000003",
			},
			Spec: types.DataRecordSpec{
				Source: "consul",
				Query:  "kv/monitoring/config",
				Data: map[string]string{
					"scrape_interval": "15s",
					"retention_days":  "30",
				},
			},
			Status: types.DataRecordStatus{
				LastSyncTime: metav1.NewTime(now.Add(-5 * time.Minute)),
				SyncStatus:   "Stale",
			},
		},
	}

	for i := range seedData {
		record := &seedData[i]
		ns := record.Namespace
		if s.records[ns] == nil {
			s.records[ns] = make(map[string]*types.DataRecord)
		}
		s.records[ns][record.Name] = record
	}
}

// List returns all records in a namespace (empty string = all namespaces).
func (s *Store) List(namespace string) []types.DataRecord {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var result []types.DataRecord

	if namespace == "" {
		for _, nsRecords := range s.records {
			for _, r := range nsRecords {
				result = append(result, *r)
			}
		}
	} else {
		nsRecords, ok := s.records[namespace]
		if !ok {
			return nil
		}
		for _, r := range nsRecords {
			result = append(result, *r)
		}
	}

	return result
}

// Get returns a single record by namespace and name.
func (s *Store) Get(namespace, name string) (*types.DataRecord, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	nsRecords, ok := s.records[namespace]
	if !ok {
		return nil, fmt.Errorf("not found")
	}

	record, ok := nsRecords[name]
	if !ok {
		return nil, fmt.Errorf("not found")
	}

	return record, nil
}
```

### 3.5 HTTP Handlers

```go
// pkg/handlers/discovery.go
package handlers

import (
	"encoding/json"
	"net/http"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// HandleGroupDiscovery returns the API group information.
func HandleGroupDiscovery(w http.ResponseWriter, r *http.Request) {
	group := metav1.APIGroup{
		TypeMeta: metav1.TypeMeta{
			Kind:       "APIGroup",
			APIVersion: "v1",
		},
		Name: "data.kubedojo.io",
		Versions: []metav1.GroupVersionForDiscovery{
			{
				GroupVersion: "data.kubedojo.io/v1alpha1",
				Version:      "v1alpha1",
			},
		},
		PreferredVersion: metav1.GroupVersionForDiscovery{
			GroupVersion: "data.kubedojo.io/v1alpha1",
			Version:      "v1alpha1",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(group)
}

// HandleResourceDiscovery returns the available resources in the API group version.
func HandleResourceDiscovery(w http.ResponseWriter, r *http.Request) {
	resourceList := metav1.APIResourceList{
		TypeMeta: metav1.TypeMeta{
			Kind:       "APIResourceList",
			APIVersion: "v1",
		},
		GroupVersion: "data.kubedojo.io/v1alpha1",
		APIResources: []metav1.APIResource{
			{
				Name:         "datarecords",
				SingularName: "datarecord",
				Namespaced:   true,
				Kind:         "DataRecord",
				Verbs: metav1.Verbs{
					"get", "list",
				},
				ShortNames: []string{"dr"},
				Categories: []string{"all", "kubedojo"},
			},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resourceList)
}
```

```go
// pkg/handlers/records.go
package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/kubedojo/extension-api/pkg/storage"
	"github.com/kubedojo/extension-api/pkg/types"
)

// RecordHandler handles DataRecord requests.
type RecordHandler struct {
	Store *storage.Store
}

// HandleList handles LIST requests.
func (h *RecordHandler) HandleList(w http.ResponseWriter, r *http.Request) {
	namespace := extractNamespace(r.URL.Path)

	// Log the impersonated user (set by kube-aggregator)
	user := r.Header.Get("X-Remote-User")
	groups := r.Header.Get("X-Remote-Group")
	if user != "" {
		log.Printf("Request from user=%s groups=%s namespace=%s",
			user, groups, namespace)
	}

	records := h.Store.List(namespace)

	list := types.DataRecordList{
		TypeMeta: metav1.TypeMeta{
			APIVersion: "data.kubedojo.io/v1alpha1",
			Kind:       "DataRecordList",
		},
		ListMeta: metav1.ListMeta{
			ResourceVersion: "1",
		},
		Items: records,
	}

	if list.Items == nil {
		list.Items = []types.DataRecord{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(list)
}

// HandleGet handles GET requests for a single resource.
func (h *RecordHandler) HandleGet(w http.ResponseWriter, r *http.Request) {
	namespace := extractNamespace(r.URL.Path)
	name := extractName(r.URL.Path)

	record, err := h.Store.Get(namespace, name)
	if err != nil {
		status := metav1.Status{
			TypeMeta: metav1.TypeMeta{
				Kind:       "Status",
				APIVersion: "v1",
			},
			Status:  "Failure",
			Message: "datarecords \"" + name + "\" not found",
			Reason:  metav1.StatusReasonNotFound,
			Code:    http.StatusNotFound,
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(status)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(record)
}

// extractNamespace extracts the namespace from the URL path.
// Path format: /apis/data.kubedojo.io/v1alpha1/namespaces/{namespace}/datarecords/...
func extractNamespace(path string) string {
	parts := strings.Split(path, "/")
	for i, part := range parts {
		if part == "namespaces" && i+1 < len(parts) {
			return parts[i+1]
		}
	}
	return "" // cluster-scoped or list all
}

// extractName extracts the resource name from the URL path.
func extractName(path string) string {
	parts := strings.Split(strings.TrimSuffix(path, "/"), "/")
	return parts[len(parts)-1]
}
```

### 3.6 Main Server

```go
// cmd/server/main.go
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/kubedojo/extension-api/pkg/handlers"
	"github.com/kubedojo/extension-api/pkg/storage"
)

const (
	certFile = "/etc/apiserver/certs/tls.crt"
	keyFile  = "/etc/apiserver/certs/tls.key"
)

func main() {
	store := storage.NewStore()
	recordHandler := &handlers.RecordHandler{Store: store}

	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	// API group discovery
	mux.HandleFunc("/apis/data.kubedojo.io", func(w http.ResponseWriter, r *http.Request) {
		// Handle both /apis/data.kubedojo.io and /apis/data.kubedojo.io/
		if r.URL.Path == "/apis/data.kubedojo.io" ||
			r.URL.Path == "/apis/data.kubedojo.io/" {
			handlers.HandleGroupDiscovery(w, r)
			return
		}
		http.NotFound(w, r)
	})

	// Version resource discovery
	mux.HandleFunc("/apis/data.kubedojo.io/v1alpha1", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/apis/data.kubedojo.io/v1alpha1" ||
			r.URL.Path == "/apis/data.kubedojo.io/v1alpha1/" {
			handlers.HandleResourceDiscovery(w, r)
			return
		}
		http.NotFound(w, r)
	})

	// Namespaced resource endpoints
	mux.HandleFunc("/apis/data.kubedojo.io/v1alpha1/namespaces/", func(w http.ResponseWriter, r *http.Request) {
		path := r.URL.Path

		// Match: /apis/.../namespaces/{ns}/datarecords
		// Match: /apis/.../namespaces/{ns}/datarecords/{name}
		if strings.Contains(path, "/datarecords") {
			parts := strings.Split(strings.TrimSuffix(path, "/"), "/")
			// Find index of "datarecords"
			drIdx := -1
			for i, p := range parts {
				if p == "datarecords" {
					drIdx = i
					break
				}
			}

			if drIdx == -1 {
				http.NotFound(w, r)
				return
			}

			if drIdx == len(parts)-1 {
				// List: .../datarecords
				recordHandler.HandleList(w, r)
			} else {
				// Get: .../datarecords/{name}
				recordHandler.HandleGet(w, r)
			}
			return
		}

		http.NotFound(w, r)
	})

	// Cluster-wide list (all namespaces)
	mux.HandleFunc("/apis/data.kubedojo.io/v1alpha1/datarecords", func(w http.ResponseWriter, r *http.Request) {
		recordHandler.HandleList(w, r)
	})

	server := &http.Server{
		Addr:         ":8443",
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	// Graceful shutdown
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		log.Println("Shutting down extension API server")
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		server.Shutdown(ctx)
	}()

	log.Println("Starting extension API server on :8443")
	if err := server.ListenAndServeTLS(certFile, keyFile); err != http.ErrServerClosed {
		log.Fatalf("Server failed: %v", err)
	}
}
```

---

## Part 4: Deployment

### 4.1 TLS Setup with cert-manager

```yaml
# manifests/certificate.yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: api-selfsigned
  namespace: kubedojo-system
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: kubedojo-data-api-cert
  namespace: kubedojo-system
spec:
  secretName: kubedojo-data-api-tls
  duration: 8760h
  renewBefore: 720h
  issuerRef:
    name: api-selfsigned
    kind: Issuer
  dnsNames:
  - kubedojo-data-api.kubedojo-system.svc
  - kubedojo-data-api.kubedojo-system.svc.cluster.local
```

### 4.2 Deployment and Service

```yaml
# manifests/deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kubedojo-system
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubedojo-data-api
  namespace: kubedojo-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kubedojo-data-api
  template:
    metadata:
      labels:
        app: kubedojo-data-api
    spec:
      serviceAccountName: kubedojo-data-api
      containers:
      - name: server
        image: kubedojo-data-api:v0.1.0
        ports:
        - containerPort: 8443
        volumeMounts:
        - name: certs
          mountPath: /etc/apiserver/certs
          readOnly: true
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 15
          periodSeconds: 20
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
      volumes:
      - name: certs
        secret:
          secretName: kubedojo-data-api-tls
---
apiVersion: v1
kind: Service
metadata:
  name: kubedojo-data-api
  namespace: kubedojo-system
spec:
  selector:
    app: kubedojo-data-api
  ports:
  - port: 443
    targetPort: 8443
    protocol: TCP
```

### 4.3 RBAC

```yaml
# manifests/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubedojo-data-api
  namespace: kubedojo-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubedojo-data-api
rules:
# The extension API server needs to read authentication config
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list", "watch"]
# For auth delegation (authn/authz)
- apiGroups: ["authentication.k8s.io"]
  resources: ["tokenreviews"]
  verbs: ["create"]
- apiGroups: ["authorization.k8s.io"]
  resources: ["subjectaccessreviews"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubedojo-data-api
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubedojo-data-api
subjects:
- kind: ServiceAccount
  name: kubedojo-data-api
  namespace: kubedojo-system
---
# Allow the kube-aggregator to authenticate to the extension API server
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubedojo-data-api:system:auth-delegator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
- kind: ServiceAccount
  name: kubedojo-data-api
  namespace: kubedojo-system
---
# Allow reading the auth configmap
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kubedojo-data-api:auth-reader
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: extension-apiserver-authentication-reader
subjects:
- kind: ServiceAccount
  name: kubedojo-data-api
  namespace: kubedojo-system
```

### 4.4 Register the APIService

```yaml
# manifests/apiservice.yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1alpha1.data.kubedojo.io
  annotations:
    cert-manager.io/inject-ca-from: kubedojo-system/kubedojo-data-api-cert
spec:
  group: data.kubedojo.io
  version: v1alpha1
  service:
    name: kubedojo-data-api
    namespace: kubedojo-system
    port: 443
  groupPriorityMinimum: 1000
  versionPriority: 15
  insecureSkipTLSVerify: false
```

---

## Part 5: Testing the Aggregated API

### 5.1 Verification

```bash
# Check APIService status
k get apiservice v1alpha1.data.kubedojo.io
# Should show "Available: True"

# Describe for details
k describe apiservice v1alpha1.data.kubedojo.io

# Check API discovery
k api-resources | grep kubedojo
# Should show: datarecords  dr  data.kubedojo.io/v1alpha1  true  DataRecord

# List all data records
k get datarecords --all-namespaces
# or using short name
k get dr -A

# Get records in a specific namespace
k get dr -n default

# Get a specific record
k get dr user-config -n default -o yaml

# Raw API access
k get --raw /apis/data.kubedojo.io/v1alpha1 | python3 -m json.tool
k get --raw /apis/data.kubedojo.io/v1alpha1/namespaces/default/datarecords | python3 -m json.tool
```

### 5.2 Debugging

```bash
# Check if the APIService is available
k get apiservice v1alpha1.data.kubedojo.io -o yaml

# Common status conditions:
# Available: True → working
# Available: False, reason: FailedDiscoveryCheck → server not responding
# Available: False, reason: ServiceNotFound → service does not exist

# Check the extension API server logs
k logs -n kubedojo-system -l app=kubedojo-data-api -f

# Test connectivity directly
k run test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -vk https://kubedojo-data-api.kubedojo-system.svc:443/healthz

# Check if the aggregator can reach the service
k get endpoints -n kubedojo-system kubedojo-data-api
```

---

## Part 6: Production Considerations

### 6.1 Performance

| Concern | Solution |
|---------|----------|
| Database query latency | Cache results with TTL |
| High request volume | Add caching layer (in-memory or Redis) |
| Connection pooling | Use database connection pools |
| Large response payloads | Implement pagination via `?limit=` and `continue` token |

### 6.2 High Availability

```yaml
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: kubedojo-data-api
              topologyKey: kubernetes.io/hostname
```

### 6.3 Implementing Watch (Optional but Valuable)

For full Kubernetes compatibility, implement the Watch protocol:

```go
// Simplified watch implementation
func (h *RecordHandler) HandleWatch(w http.ResponseWriter, r *http.Request) {
    flusher, ok := w.(http.Flusher)
    if !ok {
        http.Error(w, "streaming not supported", http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("Transfer-Encoding", "chunked")
    w.WriteHeader(http.StatusOK)
    flusher.Flush()

    // Send events as they happen
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-r.Context().Done():
            return
        case <-ticker.C:
            // Check for changes and send MODIFIED events
            event := map[string]interface{}{
                "type":   "MODIFIED",
                "object": record,
            }
            json.NewEncoder(w).Encode(event)
            flusher.Flush()
        }
    }
}
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Wrong APIService name format | Registration fails | Must be `{version}.{group}` exactly |
| Missing CA bundle | API Server cannot verify TLS | Use cert-manager CA injection annotation |
| No health endpoint | APIService shows `FailedDiscoveryCheck` | Implement `/healthz` returning 200 |
| Wrong discovery response format | `kubectl api-resources` does not list your types | Return proper `APIResourceList` structure |
| Not handling impersonation headers | No user context in your server | Read `X-Remote-User` and `X-Remote-Group` headers |
| Missing RBAC for auth delegation | Extension server cannot authenticate users | Bind `system:auth-delegator` and `extension-apiserver-authentication-reader` |
| Service port mismatch | Requests not reaching your server | APIService port must match Service port (usually 443) |
| Not returning `metav1.Status` on errors | kubectl shows raw HTTP errors | Return proper Status objects with reason and code |
| Forgetting cluster-scoped list endpoint | `kubectl get dr -A` fails | Implement the non-namespaced list endpoint too |

---

## Quiz

1. **You are designing a system to expose billions of historical IoT telemetry records to Kubernetes users so they can query them via standard `kubectl` commands. You must decide between a CRD and an Aggregated API. Which do you choose and why, specifically concerning the underlying storage architecture?**
   <details>
   <summary>Answer</summary>
   You should choose an Aggregated API because the telemetry data volume would immediately overwhelm etcd, which is designed for small, declarative configuration data, not high-volume time-series data. CRDs automatically force the API server to store their custom objects in the cluster's etcd ring, which is strictly limited in size (typically 2-8GB) and write throughput. An Aggregated API allows you to leave the billions of records in their native database (like TimescaleDB or Cassandra) while simply translating incoming Kubernetes API HTTP requests into the appropriate database queries on the fly, keeping etcd safe and stable.
   </details>

2. **A developer complains that their `kubectl get mycustomresources` command fails with a 403 Forbidden error from your new Aggregated API server, even though they have ClusterRole bindings granting them access. When you check your custom server's logs, you see the request arriving, but it lacks any JWT bearer token from the developer. How exactly is the user's identity supposed to reach your server, and what component in the request path is responsible for this?**
   <details>
   <summary>Answer</summary>
   The user's identity reaches your server via HTTP impersonation headers (e.g., `X-Remote-User`, `X-Remote-Group`), not via the original JWT bearer token. When the user sends a request to the main Kubernetes API server, the main API server authenticates the user, strips their original credentials, and then the kube-aggregator component proxies the request to your backend service. The aggregator attaches these headers to securely inform your extension server who originally made the request, while authenticating itself to your server using a front-proxy client certificate, meaning your server must be configured to extract these specific headers for its internal authorization checks rather than looking for a standard user token.
   </details>

3. **After deploying your `APIService` manifest and the backing Deployment, you notice `kubectl api-resources` does not list your new custom resources. Running `kubectl get apiservice` shows `Available: False` with the reason `FailedDiscoveryCheck`. You verified the Pods are running and the Service is correctly selecting them. What specific endpoints is the aggregator attempting to reach, and what must your application return to resolve this error?**
   <details>
   <summary>Answer</summary>
   The kube-aggregator is continuously polling your extension server's discovery endpoints, specifically the `/healthz`, `/apis/{group}`, and `/apis/{group}/{version}` paths. To resolve the `FailedDiscoveryCheck` error, your server must return an HTTP 200 OK on the health endpoint, and return correctly formatted Kubernetes `APIGroup` and `APIResourceList` JSON structures on the discovery paths. If your application returns a 404, times out, or returns improperly formatted JSON (such as missing the GVK or supported verbs), the aggregator will mark the APIService as unavailable and refuse to route traffic to it, preventing your resources from appearing in `kubectl`.
   </details>

4. **You are hardening your extension API server's deployment and decide to remove all ClusterRoleBindings to follow least-privilege principles. Immediately, your server begins rejecting all proxied requests from the kube-aggregator with authentication errors. Which specific RBAC roles must you restore to the extension server's ServiceAccount, and what exact API calls do these roles allow your server to make back to the main control plane?**
   <details>
   <summary>Answer</summary>
   You must restore bindings to the `system:auth-delegator` ClusterRole and the `extension-apiserver-authentication-reader` Role in the `kube-system` namespace. The `system:auth-delegator` role is critical because it grants your extension server permission to POST to the `/apis/authentication.k8s.io/v1/tokenreviews` and `/apis/authorization.k8s.io/v1/subjectaccessreviews` endpoints on the main API server, allowing your custom server to delegate authorization checks back to the cluster's central RBAC system. The `extension-apiserver-authentication-reader` role allows your server to read the `extension-apiserver-authentication` ConfigMap, which contains the client CA certificates necessary to cryptographically verify that the incoming proxy requests genuinely originated from the kube-aggregator and not a malicious actor spoofing headers.
   </details>

5. **A data science team wants to use the Horizontal Pod Autoscaler (HPA) to scale their Jupyter deployments based on real-time, hardware-level GPU temperature metrics scraped every 5 seconds. A junior engineer suggests creating a `GPUTemperature` CRD and writing a controller to update it continuously. Why is this a dangerous anti-pattern, and how does an Aggregated API solve this specific scenario?**
   <details>
   <summary>Answer</summary>
   Using a CRD for high-frequency, ephemeral metric updates is a dangerous anti-pattern because every update triggers a write to etcd, which would quickly exhaust the cluster's storage I/O and etcd database size limits, potentially crashing the entire control plane. CRDs are strictly intended for declarative configuration state, not for volatile telemetry data. An Aggregated API solves this by bypassing etcd entirely; when the HPA queries the custom metrics API, the kube-aggregator routes the request to your extension server, which can dynamically fetch the current temperature directly from the nodes or a Prometheus backend in memory, returning the result instantly without ever persisting the raw data into the cluster's critical datastore.
   </details>

6. **Your team has deployed an extension API server handling the `data.kubedojo.io` group. A user runs `kubectl get datarecords -n default`, but the request mysteriously hangs and times out, even though `kubectl get datarecords` (cluster-scoped) works perfectly. Looking at your Go HTTP multiplexer configuration, what structural routing requirement for aggregated APIs have you likely missed?**
   <details>
   <summary>Answer</summary>
   You have likely failed to explicitly implement the namespace-scoped routing path (`/apis/{group}/{version}/namespaces/{namespace}/{resource}`) in your HTTP multiplexer, only implementing the cluster-scoped path (`/apis/{group}/{version}/{resource}`). Unlike CRDs where the main API server automatically handles the URL routing hierarchy for namespaced resources, an extension API server is just a raw HTTP server that receives exactly the URL path requested by the client. If your server does not explicitly parse the URL to extract the namespace parameter and route it to the appropriate handler, the request will fall through to a 404 handler or hang, causing namespace-specific queries to fail while global lists succeed.
   </details>

7. **You are deploying a custom API server that serves the `v1alpha1` version of the `apps` API group to experiment with a new Deployment controller. However, after applying your `APIService` manifest, users report that standard `kubectl get deployments` commands are suddenly failing or returning unexpected schemas. Based on the `APIService` specification, what field was misconfigured to cause this collision with the core Kubernetes APIs, and why?**
   <details>
   <summary>Answer</summary>
   The `groupPriorityMinimum` and `versionPriority` fields in your `APIService` manifest were likely set higher than the priority of the built-in Kubernetes `apps` API group. The kube-aggregator uses these priority values to determine which API group and version should be preferred when a client requests a resource without fully specifying the version path, and also dictates the order of group discovery. By assigning your experimental extension API a higher priority than the core controllers (which typically sit in the 17000-18000 range), the aggregator effectively hijacked the default route for Deployment objects, routing standard user requests to your experimental server instead of the native Kubernetes API server.
   </details>

8. **During development of your extension API server, you set `insecureSkipTLSVerify: true` in the `APIService` manifest to save time. A security auditor flags this before production deployment, demanding you use a `caBundle` instead. Detail the specific attack vector that becomes possible if you ignore the auditor and deploy with TLS verification disabled.**
   <details>
   <summary>Answer</summary>
   Leaving `insecureSkipTLSVerify: true` enabled allows for a severe Man-in-the-Middle (MitM) attack within the cluster network, because the kube-aggregator will blindly trust any server that answers on the target Service IP without verifying its cryptographic identity. If a malicious actor compromises a pod in the cluster, they could potentially use ARP spoofing or DNS poisoning to hijack the traffic destined for your extension API service. Without the `caBundle` verifying the server's certificate against a trusted authority, the aggregator would happily send the attacker the highly sensitive impersonation headers and proxy tokens, allowing the attacker to intercept, read, or modify administrative API requests without detection.
   </details>

---

## Hands-On Exercise

**Task**: Build and deploy an extension API server that serves `DataRecord` resources backed by an in-memory store, register it via APIService, and access it with kubectl.

**Setup**:
```bash
kind create cluster --name aggregation-lab

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.17.0/cert-manager.yaml
kubectl wait --for=condition=Available deployment -n cert-manager --all --timeout=120s
```

**Steps**:

1. **Create the Go project**:
```bash
mkdir -p ~/extending-k8s/extension-api && cd ~/extending-k8s/extension-api
go mod init github.com/kubedojo/extension-api
go get k8s.io/apimachinery@latest
```

2. **Copy the source files** from Parts 3.3 through 3.6 into the appropriate directories

3. **Build the container image**:
```bash
# Create Dockerfile (similar to Part 3 of Module 1.7)
cat << 'DOCKERFILE' > Dockerfile
FROM golang:1.23 AS builder
WORKDIR /workspace
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o apiserver ./cmd/server/

FROM gcr.io/distroless/static:nonroot
COPY --from=builder /workspace/apiserver /apiserver
USER 65532:65532
ENTRYPOINT ["/apiserver"]
DOCKERFILE

docker build -t kubedojo-data-api:v0.1.0 .
kind load docker-image kubedojo-data-api:v0.1.0 --name aggregation-lab
```

4. **Deploy everything**:
```bash
# Create namespace
k create namespace kubedojo-system

# Apply RBAC, cert, deployment, service from Part 4
k apply -f manifests/rbac.yaml
k apply -f manifests/certificate.yaml
k apply -f manifests/deployment.yaml

# Wait for the certificate and pods
k wait --for=condition=Ready certificate -n kubedojo-system kubedojo-data-api-cert --timeout=60s
k wait --for=condition=Ready pod -n kubedojo-system -l app=kubedojo-data-api --timeout=60s

# Register the APIService
k apply -f manifests/apiservice.yaml
```

5. **Verify the APIService**:
```bash
k get apiservice v1alpha1.data.kubedojo.io
# Should show Available: True

k api-resources | grep data.kubedojo
# Should show: datarecords  dr  data.kubedojo.io/v1alpha1  true  DataRecord
```

6. **Access the resources with kubectl**:
```bash
# List all data records
k get datarecords -A

# Get records in default namespace
k get dr -n default

# Get a specific record
k get dr user-config -n default -o yaml

# Get records in monitoring namespace
k get dr -n monitoring -o yaml

# Try raw API access
k get --raw /apis/data.kubedojo.io/v1alpha1 | python3 -m json.tool
k get --raw /apis/data.kubedojo.io/v1alpha1/namespaces/default/datarecords | python3 -m json.tool
```

7. **Verify it behaves like a real Kubernetes API**:
```bash
# Tab completion should work (after discovering the resource)
k get datarecords -n default user-config -o jsonpath='{.spec.data}'

# Describe should work
k describe dr user-config -n default
```

8. **Cleanup**:
```bash
kind delete cluster --name aggregation-lab
```

**Success Criteria**:
- [ ] Extension API server builds and runs
- [ ] cert-manager issues a valid TLS certificate
- [ ] APIService shows `Available: True`
- [ ] `kubectl api-resources` lists `datarecords`
- [ ] `kubectl get dr -A` returns all seed records
- [ ] `kubectl get dr -n default` returns namespace-filtered records
- [ ] `kubectl get dr user-config -n default -o yaml` returns full YAML
- [ ] Non-existent records return proper 404 with `metav1.Status`
- [ ] Short name `dr` works
- [ ] Extension server logs show requests with user identity

---

## Summary: Extending Kubernetes Track

Congratulations on completing the entire Extending Kubernetes track. Here is what you have learned:

| Module | Topic | Key Skill |
|--------|-------|-----------|
| 1.1 | API Deep Dive | Understanding the API Server pipeline and client-go |
| 1.2 | CRDs Advanced | Building production-grade Custom Resource Definitions |
| 1.3 | Controllers | Writing controllers from scratch with client-go |
| 1.4 | Kubebuilder | Using frameworks for efficient operator development |
| 1.5 | Advanced Operators | Finalizers, conditions, events, and testing |
| 1.6 | Admission Webhooks | Intercepting and modifying API requests |
| 1.7 | Scheduler Plugins | Customizing Kubernetes scheduling decisions |
| 1.8 | API Aggregation | Building custom API servers |

You now have the knowledge to extend Kubernetes at every level: the API surface (CRDs, API Aggregation), the request pipeline (webhooks), the control loop (controllers/operators), and the scheduler. These are the building blocks of every major Kubernetes platform tool.