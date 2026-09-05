# Replica recovery lab: evidence and validation contract — #2438

Scope: complexity module Hands-On Part A at `b37b1ec41e445f9259fac894b392957a36922047`. Part B and other lesson claims remain separate. This note maps documentation and defines candidate validation; no lab outcome is claimed.

## Official sources inspected

All links below use the Kubernetes v1.35 documentation host. Root read the specified body spans on 2026-09-05; these are documentation accounts, not measurements of the local cluster.

| Source and locator | Supported claim | Lab disposition |
|---|---|---|
| [ReplicaSet](https://v1-35.docs.kubernetes.io/docs/concepts/workloads/controllers/replicaset/), “How a ReplicaSet works,” first two paragraphs | ReplicaSets create/delete Pods toward the requested count; Pod owner references identify the owning ReplicaSet. | Inspect the owner chain and replacement identity. Attribute replacement to the ReplicaSet controller rather than collapsing all work into the Deployment controller. |
| [Deployments](https://v1-35.docs.kubernetes.io/docs/concepts/workloads/controllers/deployment/), opening and first use case; creating-a-Deployment explanation | A Deployment manages ReplicaSets; the example's ReplicaSet creates the Pods. | Teach Deployment → ReplicaSet → Pod relationships. A desired count is not a measured recovery deadline. |
| [Readiness probes](https://v1-35.docs.kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/#readiness-probe), opening and deletion note | Readiness affects Service endpoint eligibility; deletion also changes endpoint readiness. | Observe readiness alongside actual HTTP requests. A Pod-state watch does not measure uninterrupted client success. |
| [Object IDs](https://v1-35.docs.kubernetes.io/docs/concepts/overview/working-with-objects/names/#uids), UID section | UIDs distinguish object instances, including historical occurrences with similar names. | Record the namespace UID created by this run; a matching name alone is insufficient ownership evidence. |
| [kubectl wait](https://v1-35.docs.kubernetes.io/docs/reference/kubectl/generated/kubectl_wait/), readiness/deletion examples and timeout options | Conditions and deletion can be awaited with explicit bounds; request timeout and wait timeout are separate controls. | Replace unbounded watches as the sole completion gate. A timeout is an observation to diagnose, not a reason to claim successful recovery. |
| [kubectl v0.35.0 delete implementation](https://github.com/kubernetes/kubectl/blob/v0.35.0/pkg/cmd/delete/delete.go#L275-L306), raw validation and dispatch | Raw DELETE accepts one local file or stdin and passes it to the raw request helper. | A candidate can submit DeleteOptions with a UID precondition; verify the exact command rather than assuming ordinary name-based deletion supplies that precondition. |
| [API metadata v0.35.0](https://github.com/kubernetes/apimachinery/blob/v0.35.0/pkg/apis/meta/v1/types.go), `DeleteOptions.Preconditions` and `Preconditions.UID` | Delete preconditions must hold; failure returns conflict, and UID can constrain the target object instance. | Test rejection with an incorrect UID before accepting cleanup. A client-side read/compare followed by a name-only delete leaves a race; use the server precondition. |

## Required candidate behavior

The existing fixed `chaos-lab` sequence lacks a stop-on-create-failure/ownership boundary before apply and delete. The replacement must target an explicitly selected disposable context, create its own namespace, stop on setup failure, retain that namespace's identity, and avoid deleting an unrelated or replaced namespace. This is a lab-safety design requirement, not a guarantee supplied by the UID documentation. Cleanup needs its own observed completion evidence.

Retain the Service and compare its HTTP observations with replica reconciliation. Record Pod identities, owner references, ready counts, request attempts/results and observation intervals around deletion of one and then two Pods. A finite sequence of successful requests supports only that observation window; it cannot prove uninterrupted availability or future resilience. Do not invent a guaranteed event order or replacement time.

Capture the tested Kubernetes version, image references and resolved image identities. Bound setup/recovery waits and HTTP attempts. Report scheduling, image-pull or readiness failures if encountered; do not rewrite expected outcomes to match a failing run. Explain replica recovery as a controller-coordination example rather than treating it as empirical validation of a general emergence theory.

## Acceptance and scope

Before published edits: independent SOURCE acceptance of this map. Before release: exercise the exact candidate commands on the existing dedicated local Kubernetes 1.35 cluster, preserving default context and unrelated resources; retain command/outcome/cleanup receipts. Include an ownership failure-path check. No VPS migration, CNI/network-policy changes or production chaos test is included.

Separate independent-family technical/PROSE review, pipeline tests, site build/render checks, CI and live-page verification follow. Split setup/cleanup and observation/explanation changes if needed to keep each PR below 200 aggregate changed lines. This note does not accept a candidate script, claim any requests have succeeded, or close the whole module or Ukrainian work.
