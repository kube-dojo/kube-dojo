---
title: "Module 5.1: Container Image Security"
slug: k8s/cks/part5-supply-chain-security/module-5.1-image-security
sidebar:
  order: 1
lab:
  id: cks-5.1-image-security
  url: https://killercoda.com/kubedojo/scenario/cks-5.1-image-security
  duration: "40-45 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Core CKS skill
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Docker/container basics, Module 0.3 (Security Tools)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Create** hardened Dockerfiles using multi-stage builds, minimal base images, and non-root users
2. **Configure** image pull policies and private registry authentication for clusters
3. **Implement** image digest pinning to prevent tag-based supply chain attacks
4. **Audit** container images for unnecessary packages, setuid binaries, and embedded secrets

## Why This Module Matters

Container image security is where Kubernetes workload hardening begins, because the cluster only schedules what the image already contains. A Pod can have restricted capabilities, a read-only root filesystem, and a tight NetworkPolicy, yet still start from an image that includes a vulnerable runtime, a compromised dependency, a leaked token, or a shell toolkit an attacker can use after the first foothold. CKS treats this as a practical skill: you need to inspect image references, tighten Dockerfiles, configure registry credentials, and explain why a tag that looked harmless at review time can become a different artifact at runtime.

Consider the October 2021 `ua-parser-js` compromise. The npm package maintainer reported that an attacker hijacked the npm account and published three malicious versions: `0.7.29`, `0.8.0`, and `1.0.0`. GitHub's advisory and CNCF TAG Security's compromise catalog both document that the affected versions carried embedded malware, and the CNCF entry notes that the package had more than seven million weekly downloads at the time. A build pipeline that ran `npm install` during `docker build` could therefore produce a legitimate-looking application image containing attacker-supplied code, even though the Kubernetes YAML, Deployment owner, and registry hostname all looked normal. The cluster sees one opaque image reference; the attacker used the build's dependency graph to decide what bytes entered that image.

The Codecov Bash Uploader incident illustrates the CI-side variant of
the same lesson — credentials, signing keys, and deploy secrets can be
exposed by a compromised build tool before any Kubernetes admission
policy runs. See [DevSecOps](/prerequisites/modern-devops/module-1.6-devsecops/)
for the canonical write-up. <!-- incident-xref: codecov-2021 -->

Those incidents connect directly to day-to-day Kubernetes operations. If you deploy `myregistry/app:prod`, the kubelet resolves the tag at container start time according to the pull policy and node cache. If the registry tag was overwritten after review, a restarted Pod may run bytes that never passed the original scan. If the Dockerfile uses a full distribution image, the attacker who compromises the app may find package managers, shells, setuid binaries, and network tools already installed. If the image was built with a broad `.dockerignore`, a `.env` file or private key may still be sitting in an earlier layer even after a later `RUN rm` command. A secure image strategy closes these gaps with minimal base images, reproducible build inputs, digest pinning, signed artifacts, private registry controls, and runtime settings that match the image's assumptions.

For the exam, this module is also a speed exercise. You are unlikely to design an enterprise supply-chain platform from scratch during CKS, but you may need to diagnose why a Pod is in `ImagePullBackOff`, replace a mutable tag with a digest, create an `imagePullSecret`, identify an insecure Dockerfile instruction, or explain why a scanner result should trigger a base image rebuild rather than an application code change. The fastest answers come from understanding the "why": each image reference is a trust decision, each Dockerfile line adds or removes runtime attack surface, and each registry credential defines who is allowed to move software into the cluster.

## Image Security Risks

An image is both a filesystem and a supply-chain record. The filesystem contains your application, language runtime, operating system packages, metadata, default user, exposed ports, entrypoint, labels, and sometimes accidental secrets. The supply-chain record includes the base image, package repositories, dependency lock files, build arguments, CI identity, registry permissions, signatures, vulnerability reports, and promotion path. A weak review that only checks the Deployment YAML misses most of that record, while a weak scanner-only process misses insecure defaults that do not have CVE numbers.

The first risk is vulnerable inherited software. A base image such as `ubuntu`, `debian`, `python`, `node`, or `openjdk` brings operating system packages and language tooling that may be unrelated to your application at runtime. A CVE in `curl` may not be reachable through the business logic, but if a compromised process can launch `curl`, it becomes useful for exfiltration and lateral movement. A CVE in a shared library may matter only when your binary actually loads it, yet scanners often report it because the package is present. Your job is to reduce the package set enough that scanner output becomes actionable instead of a permanent backlog.

The second risk is malicious or unexpected build input. Dependency registries, package mirrors, base images, CI helpers, and generated artifacts are all inputs to the final image. The `ua-parser-js` incident matters because it turned an ordinary package install into malware delivery. The Codecov incident is another example of trusted CI tooling becoming
a leak vector. <!-- incident-xref: codecov-2021 -->

The third risk is privilege baked into the image. Many images run as root by default because no `USER` instruction is present. Some include setuid or setgid binaries that were inherited from the distribution. Some use shell-form entrypoints, which force commands through `/bin/sh -c` and create quoting and signal-handling problems. Kubernetes can override parts of this with `securityContext`, but relying only on the Pod spec is fragile. The image should be safe by default, and the Pod spec should reinforce that default with `runAsNonRoot`, `allowPrivilegeEscalation: false`, dropped capabilities, and a read-only root filesystem where possible.

The fourth risk is mutable identity. A tag is a human-friendly pointer, not a content guarantee. Registry owners can repush a tag, automated rebuilds can move it, and an attacker with push rights can replace it. A digest is different because it names the manifest content by hash. Tags are useful for humans and automation, but production promotion should record and deploy the exact digest that passed scanning and review. This does not eliminate the need for signing, because a digest only proves content stability, not author identity, but it prevents a large class of tag-spoofing and cache confusion failures.

The fifth risk is scanner blindness caused by context, metadata, or timing. A scanner can report known CVEs for packages it can identify, but it does not know whether the image was built by the approved pipeline, whether the tag was overwritten after the scan, whether a build secret leaked into logs, or whether a non-root runtime setting was lost in the Pod template. That is why image security should be reviewed as a chain of evidence. The image should have a known base, a narrow dependency lock, a reproducible build command, a scan report tied to the digest, a signature or attestation from the build identity, and a deployment record that references the same digest. If one of those links is missing, the cluster may still run the workload, but the operator has lost the proof needed to trust it.

Attackers also benefit from operational shortcuts that look harmless during delivery pressure. A hotfix image pushed manually from a laptop may bypass CI signing. A temporary registry token placed in a namespace may never be rotated. A debug tag with a shell may be promoted because it fixed an urgent outage. A base image exception may be copied into the next service because it "already worked." These are not exotic failures; they are normal workflow drift. The defense is to make the secure path the easiest path: golden Dockerfile templates, registry immutability, automated digest promotion, admission checks, and short runbooks that explain exactly how to ship an emergency image without losing provenance.

```text
Image risk review
  |
  +-- Filesystem contents: packages, shells, tools, setuid files, secrets
  +-- Build inputs: base image, dependencies, package mirrors, CI helpers
  +-- Runtime defaults: user, entrypoint, writable paths, exposed services
  +-- Registry identity: tag mutability, digest, signatures, credentials
```

## Base Image Selection

The base image is the largest security decision in a Dockerfile because every downstream layer inherits it. A full distribution image gives familiar tools and easy debugging, but it also ships shells, package managers, libraries, users, configuration files, and utilities your application may never need. A minimal base image removes much of that surface, but it can make diagnostics and compatibility harder. The right answer is not always the smallest possible image; it is the smallest image that still lets the application run predictably, receive patches, expose enough metadata for scanners, and be operated by your team.

Distroless images are a strong production default for many compiled or runtime-specific workloads. Google's distroless project describes these images as containing the application and runtime dependencies without a general-purpose distribution userland. Kubernetes documentation for ephemeral containers calls out the operational consequence: distroless images reduce attack surface and exposure to vulnerabilities, but they lack a shell and debugging utilities, so `kubectl exec` alone may be insufficient during troubleshooting. That is a feature when an attacker lands inside the container and a cost when an operator needs to inspect it. Plan for the cost with debug images, ephemeral containers, strong logs, and readiness probes rather than shipping Bash in production.

Alpine is another common choice because it is small and still behaves like a Linux distribution with a package manager. Its musl libc implementation can be excellent for simple services but can surprise teams that assume glibc behavior, especially around DNS, native extensions, and some language runtimes. Slim variants such as `python:3.12-slim`, `node:22-slim`, or Debian slim images are often a pragmatic middle ground. They keep enough distribution structure for compatibility while removing documentation, build tools, and broad package sets. Full images are acceptable for builder stages, local development, or special cases, but they should require a clear runtime justification in production.

Base image trust is about maintenance and provenance as much as size. Prefer official images, verified publishers, internal golden images, or images built by a platform team with a documented rebuild cadence. An image that is tiny but abandoned is worse than a slightly larger image that receives patches, publishes SBOMs, and is signed. Docker's best-practices documentation emphasizes trusted sources, small images, multi-stage builds, and rebuilding often because images are immutable snapshots. That immutability is a trap if you never rebuild: a six-month-old image may still start perfectly while its vulnerability report changes underneath it as new advisories are published.

The base image decision should also account for how your organization handles ownership. If every application team chooses its own base, the security team must understand many package managers, many rebuild schedules, many signing identities, and many exception processes. A curated base image program narrows that review surface. The platform team can publish a small set of blessed runtimes, rebuild them when upstream packages change, sign them, document the default user, and provide debug companions for production incidents. Application teams still own their code, but they no longer need to solve distribution hardening alone. This is especially useful in Kubernetes because many workloads share nodes; a weak image in one namespace can become a node-level incident if it combines with a runtime or kernel flaw.

There is one important caution when moving toward `scratch` or very small distroless images: runtime dependencies become your responsibility. A statically linked Go binary may run happily in `scratch`, but a TLS client still needs certificate roots, a DNS lookup still depends on resolver behavior, and an application that maps usernames may need `/etc/passwd` or a numeric UID that Kubernetes can validate. Distroless images often include useful runtime pieces such as CA certificates and a non-root user, which makes them easier than raw `scratch` for many teams. Test the image under the final Kubernetes security context, not just with `docker run`, because the Pod may enforce read-only filesystems, dropped capabilities, or numeric user constraints that reveal missing runtime assumptions.

In CKS tasks, translate base image choice into observable checks. Look at the `FROM` lines first, then ask whether the final stage contains compilers, package managers, shells, or debugging tools that were only needed during build. Check whether the image has a named non-root user or numeric UID. Check whether the application needs CA certificates, timezone data, DNS files, or shared libraries that a `scratch` image would omit. A careful minimal-image migration usually starts with a multi-stage build, copies only the runtime artifact and required config, then validates the Pod under the same security context production will use.

## Dockerfile Security Best Practices

A secure Dockerfile is a build contract. It should make clear which source image is trusted, which files enter the image, which tools are present only during build, which user runs the process, and which command starts the application. The most common mistake is treating the Dockerfile as a shell script that happens to produce an image. Docker builds preserve layers, cache intermediate results, and record metadata. A secret copied in one layer and removed in a later layer can still be recoverable from image history or build cache. A package installed for compilation can remain available to an attacker unless the final stage excludes it.

Use specific base references and rebuild deliberately. A floating tag such as `ubuntu:latest` or `node:latest` hides a moving dependency behind a stable string. A specific tag such as `debian:12.8-slim` is better for review, while a digest is better for exact reproducibility. The tradeoff is patch flow: digest pinning prevents silent changes, so your process must update digests when base images receive security rebuilds. Treat that as a feature. The update becomes a reviewable event with a scan, build, and deployment record instead of a silent registry-side change discovered during an outage.

Control the build context. `.dockerignore` is a security feature because Docker sends the build context to the builder before instructions run. If the context includes `.env`, SSH keys, kubeconfigs, test fixtures with tokens, or local cache directories, a later `COPY . .` can put them into the image or leak them to a remote builder. Prefer copying dependency manifests first, installing dependencies from lock files, then copying only the application files required for the build. Avoid broad `ADD` unless you need its archive or remote URL behavior; `COPY` is easier to reason about and does less implicit work.

Set a non-root user in the final stage and make file ownership match that user. A common failure is adding `USER 65532` after copying files owned by root, then discovering that the application needs to write logs, cache files, or temporary data. The fix is not to return to root; it is to create or use a known UID, copy files with correct ownership where supported, and write only to intended writable paths such as `/tmp` or a mounted volume. In Kubernetes, reinforce the image with `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, and explicit writable mounts for data that genuinely changes.

Use exec-form `ENTRYPOINT` and `CMD` so the application receives signals directly and does not rely on shell parsing. Shell-form commands are tempting for quick variable expansion, but they require a shell in the image and can produce confusing termination behavior during rolling updates. Keep package installation tight with `--no-install-recommends` on Debian-based images, clean package indexes in the same `RUN` layer, and avoid installing interactive tools such as editors, SSH clients, and network scanners into the final image. If operators need diagnostics, build a separate debug image or use ephemeral containers.

Build-time secrets need special treatment because they are often invisible in a final filesystem review. Modern Docker BuildKit supports secret mounts that make a file available to a single `RUN` instruction without baking it into an image layer. That is safer than `ARG TOKEN=...`, `ENV TOKEN=...`, or `COPY token.txt`, all of which can leak through history, metadata, logs, or cache. The same principle applies to package manager credentials and private module access. Give the builder the narrow credential needed for the fetch, make the instruction deterministic, and ensure the final stage receives only built artifacts. A reviewer should be able to inspect `docker history`, the Dockerfile, and the build logs without finding credentials.

File permissions are another place where Dockerfile and Kubernetes controls meet. If the image copies application files as root and then switches to a non-root user, the process may start but fail later when it writes a cache, loads a plugin, or rotates a local file. If the Dockerfile creates writable directories with broad permissions, the application may work but an attacker can tamper with more of the filesystem than necessary. Prefer explicit ownership and narrow writable paths. In Kubernetes, mount writable state through volumes and keep the root filesystem read-only. This makes write attempts visible as errors during testing and helps separate application data from immutable program files.

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.22-bookworm AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -o /out/server ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /
COPY --from=build /out/server /server
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/server"]
```

Pause and predict: on a CKS Dockerfile task, which `FROM` line would you change first, and what would you replace it with? Write the base image and final-stage runtime you expect before you read the multi-stage section, because exam fixes usually start at inheritance rather than at application code.

## Multi-Stage Builds

Multi-stage builds separate "what is needed to create the program" from "what is needed to run the program." That distinction is essential for security because build stages often need compilers, package managers, test tools, credential helpers, and source trees. Runtime stages usually need far less: a binary, a runtime interpreter, CA certificates, application assets, and configuration defaults. When the final stage copies only specific artifacts from the builder, the compiler and package cache do not become part of the production filesystem.

The security value is not only image size. A smaller final image reduces the number of packages that can have CVEs, but it also removes tools an attacker would otherwise use after compromise. No shell means no simple `sh -i`; no package manager means no `apt install nmap`; no compiler means no quick local build of exploit code. These removals are not a sandbox, and a compromised process can still use its own network permissions and mounted credentials, but the attacker's post-exploitation path becomes narrower and more visible. That is why multi-stage builds pair naturally with non-root users, read-only filesystems, dropped capabilities, and restricted egress.

Multi-stage builds also improve review quality. A reviewer can inspect the final `FROM` stage and ask exactly which files cross the stage boundary. `COPY --from=build /out/server /server` is clearer than a long chain of package installation, compilation, cleanup, and deletion in one image. For language runtimes, the pattern is similar: install dependencies in a builder or virtual environment, then copy the production dependency set into a slim or distroless runtime image. Avoid copying entire source directories from the builder into the final stage unless the runtime actually needs them.

The main trap is assuming that a multi-stage build automatically makes the image secure. If the final stage still starts from a full image, runs as root, copies `/root/.cache`, or includes environment secrets, the build split did not solve the problem. Another trap is losing scanner visibility. Some minimal images omit package database metadata, which can make OS-package vulnerability matching harder for certain tools. That does not make the image safer by itself; it means you need SBOM generation during build, scanner support for the chosen base, and a clear update path for the runtime dependencies you copy.

Layer boundaries also affect patching. Suppose the builder downloads modules, compiles a binary, and copies the result into a final image. If a vulnerability appears in the builder image but none of its packages reach production, the production risk is different from a vulnerability in the final runtime image. The builder still matters because a compromised build environment can alter the artifact, but the response may be rebuilding in a clean builder rather than emergency redeploying every runtime Pod. Conversely, if the final stage uses a vulnerable OpenSSL package for outbound TLS, the application may need a fresh runtime base even when the source code did not change. Multi-stage builds make those decisions more precise because they identify which stage owns which risk.

For interpreted languages, the same discipline applies even when there is no single compiled binary. A Python service can build wheels in one stage and copy a virtual environment into a distroless Python or slim runtime stage. A Node service can install dependencies with a lock file, prune development packages, build static assets, and copy only `node_modules`, compiled output, and package metadata needed at runtime. A Java service can build with Maven or Gradle in a builder image and run the JAR on a smaller JRE base. The goal is not to force every language into the same pattern; it is to make development dependencies unable to become production tools by accident.

In an exam scenario, look for build tools in the final image and convert the Dockerfile with the least disruptive edit. Name the first stage `builder`, compile or install there, and make the second stage minimal. Keep commands runnable in the test environment. For a Go binary, a distroless static or `scratch` final stage may be reasonable. For Python, Java, or Node, use an appropriate distroless runtime or slim runtime and copy only dependency directories plus application code. Then add `USER` and exec-form entrypoint in the final stage, not only in the builder.

## Image Tags and Digests

Tags are convenient names, but they are mutable pointers. A registry tag such as `v1.4.2`, `stable`, or `prod` can be moved to a different manifest if the registry allows it and someone has permission to push. That can be legitimate when maintainers rebuild an image with patched base layers, or malicious when an attacker gains registry credentials. Kubernetes does not store an immutable copy of a tag's historical meaning. When a Pod starts, the kubelet follows the configured pull policy, resolves the image reference, and runs the content available at that time or from the node cache.

A digest reference pins the manifest content by cryptographic hash, for example `registry.example.com/payments/api@sha256:...`. If a registry tag later moves, the digest still identifies the original content. This is the strongest simple control against tag-spoofing because it turns deployment promotion into a content-addressed decision. The usual workflow is to build and push an image with a human-readable tag, scan and sign it, capture the resulting digest, and promote that digest into Kubernetes manifests. Humans can still keep tags for discovery, but production runs the digest that passed gates.

Digest pinning has operational tradeoffs. If your Deployment references only a digest, it is less obvious which release name a human is looking at unless labels, annotations, Git metadata, or image tag comments preserve that context. If a base image receives security fixes, your pinned application image does not change until you rebuild and promote a new digest. That is exactly what you want for reproducibility, but it means automation should detect stale base digests and raise pull requests. Immutable deployment is not the same as frozen maintenance.

Multi-architecture images add another subtle point. A tag can resolve to an OCI index that contains different platform-specific manifests for `linux/amd64`, `linux/arm64`, and other platforms. The digest of the index and the digest of the platform manifest are related but not identical. Kubernetes nodes pull the platform-specific content they need, and scanners or signing tools may report either the index digest or the manifest digest depending on command and registry behavior. In mixed-architecture clusters, make sure the digest you promote and verify matches the artifact your policy expects. A release process that scans only one architecture while deploying another leaves a gap even though the tag string is the same.

Signatures and digests solve different problems. A digest proves that a reference resolves to specific content; it does not prove who produced that content. A signature from Sigstore cosign, Notary Project notation, or another trusted signing system binds an identity or key to the artifact descriptor. In production, use both: deploy by digest to prevent silent content drift, and verify signatures or attestations to enforce that the digest came from the approved build pipeline. Admission controllers such as Kyverno, policy-controller, Ratify, or custom webhooks can enforce those rules, while CKS expects you to understand the underlying artifact semantics.

```bash
# Capture the digest that a tag currently resolves to.
docker build -t registry.local:5000/payments-api:v1 .
docker push registry.local:5000/payments-api:v1
docker buildx imagetools inspect registry.local:5000/payments-api:v1

# Kubernetes can run the content-addressed reference directly.
kubectl set image deployment/payments-api \
  api=registry.local:5000/payments-api@sha256:REPLACE_WITH_DIGEST
```

## Private Registries

Private registries reduce anonymous exposure but do not automatically make images safe. They answer "who can push and pull here?" rather than "is this image hardened, scanned, signed, and approved?" A strong registry design separates push rights from pull rights, uses robot or workload identities instead of shared human passwords, limits credentials by repository or namespace, and records promotion events. A weak private registry becomes a quiet place where mutable tags, leaked credentials, and broad pull tokens spread across environments.

In Kubernetes, image pull credentials are usually stored as Secrets of type `kubernetes.io/dockerconfigjson` and referenced through `imagePullSecrets` on a Pod or ServiceAccount. The kubelet uses those credentials when pulling from the registry. The Secret must exist in the same namespace as the Pod, and the credential needs access to the registry hostname used in the image reference. If a Pod is in `ImagePullBackOff`, check the event message, image name, namespace, Secret type, Secret name, and registry server value before changing unrelated security settings.

ServiceAccount-level `imagePullSecrets` are useful when many Pods in a namespace use the same registry. Instead of repeating the secret on every Pod template, attach it to a dedicated ServiceAccount and make workloads use that account. Avoid placing powerful pull credentials on the default ServiceAccount across every namespace unless there is a clear platform policy and audit trail. Pull access can expose proprietary code, embedded configuration, and old vulnerable images. Treat it as a supply-chain permission, not just a convenience for avoiding anonymous rate limits.

Registry credentials also interact with node caches. Historically, operators sometimes assumed that if an image was already cached on a node, a Pod could start without proving it still had pull rights. In Kubernetes 1.35, `KubeletEnsureSecretPulledImages` is beta and enabled by default, so the kubelet can verify that pull credentials are still valid before using a cached image on the node. The operational lesson is still broader than that one control: do not rely on node caches as an authorization boundary. Use namespace-scoped pull secrets, short-lived credentials where possible, registry audit logs, and admission policies that restrict allowed registry hostnames.

Registry topology affects availability as well as security. Many production clusters use a private registry, pull-through cache, or regional mirror so node scale-ups do not depend on anonymous public pulls. That reduces exposure to Docker Hub rate limits and public registry outages, but it creates a responsibility to mirror the exact artifact you reviewed. A mirror that refreshes tags automatically can reintroduce mutability unless promotion records the digest and the mirror preserves it. A mirror that caches vulnerable images forever can hide upstream deletion or deprecation events. Treat the mirror as part of the supply chain: restrict who can populate it, log what digest was mirrored, and periodically garbage-collect images that no longer have a supported release owner.

Credential scope should follow the deployment boundary. A build pipeline identity may need push rights to a staging repository, but a kubelet pull secret should need only pull rights for the release repository. A developer's personal registry token should not be placed in a cluster Secret because it ties workload availability to a human account and makes revocation painful. For cloud registries, prefer workload or managed identities that can be rotated and audited centrally. For static credentials, give them an expiration calendar and test the rotation path before the old token is disabled. Many `ImagePullBackOff` incidents are really credential lifecycle incidents with Kubernetes error messages at the end.

```bash
kubectl create namespace image-lab

kubectl -n image-lab create secret docker-registry registry-creds \
  --docker-server=registry.local:5000 \
  --docker-username=labuser \
  --docker-password=labpassword \
  --docker-email=labuser@example.com

kubectl -n image-lab create serviceaccount app-runner
kubectl -n image-lab patch serviceaccount app-runner \
  -p '{"imagePullSecrets":[{"name":"registry-creds"}]}'
```

## Image Pull Policies

Before reading on: what pull policy does `nginx` with no tag get by default, and why is that a supply-chain risk when the registry tag can move? Write your answer, then compare it to the defaults below.

`imagePullPolicy` controls when the kubelet checks the registry and when it uses a cached local image. Kubernetes defaults are easy to miss: if you omit the field and use `:latest` or no tag, the policy becomes `Always`; if you omit the field and use a non-`latest` tag, the policy becomes `IfNotPresent`; if you omit the field and reference the image by digest only (for example `nginx@sha256:...` with no tag), the policy also becomes `IfNotPresent`. The policy is set when the object is created and does not automatically change later if you edit the image tag. That detail matters in exam troubleshooting because changing `nginx:1.25` to `nginx:latest` does not guarantee the pull policy becomes `Always` unless you set it explicitly.

`Always` does not mean "download every layer every time." Kubernetes documentation states that the kubelet resolves the name to a digest each time it launches a container, then uses the cached image if the exact digest is already present. This gives fresh tag resolution while still benefiting from layer and digest caching. The security benefit is that mutable tags are rechecked; the reliability cost is that container start now depends on registry reachability and credentials. During a registry outage or network partition, workloads with `Always` and no cached resolved digest may fail to start even if a previous image exists locally.

`IfNotPresent` is useful when you deploy immutable references or pre-pulled images and want faster startup with less registry dependency. It is dangerous when paired with mutable tags because different nodes may run different cached content for the same tag. One node may already have yesterday's `app:prod`, another node may pull today's `app:prod`, and both Pods appear to use the same spec. Digest pinning makes `IfNotPresent` much safer because the content identity is explicit. If the digest is absent, kubelet pulls it; if it is present, kubelet uses the same content.

`Never` belongs to special cases: air-gapped clusters, preloaded lab images, or environments where image distribution is handled outside normal registry pulls. With `Never`, the kubelet does not contact a registry at all. If the image is not already present on the node, the Pod fails with `ErrImageNeverPull` / `ImageNeverPull`, not `ImagePullBackOff`. That failure mode can be useful during exams when a task states that images are preloaded. It is not a general hardening setting. If you set `Never` on a normal cluster without a node image distribution process, Pods fail because the image is missing locally, and no security control has improved.

For production, combine explicit pull policies with immutable references. Use digests for release manifests, set `IfNotPresent` when the digest itself is the freshness boundary, and use `Always` where a mutable tag is unavoidable during development or a controlled automation path. For CKS, be ready to explain the defaults, inspect the effective Pod spec, and fix the mismatch that causes either stale content or unnecessary registry dependency.

Image garbage collection and pre-pulling can make pull policy behavior look confusing. A node may run a digest from cache for weeks, then suddenly need the registry after kubelet garbage collection removes old layers. A DaemonSet that pre-pulls images can improve rollout speed, but it does not prove the image is still authorized unless credentials and policy are checked when the workload starts. A cluster autoscaler event can add fresh nodes with empty caches, exposing registry DNS, proxy, certificate, or credential problems that existing nodes hid. When troubleshooting, compare old and new nodes, inspect Pod events, and check whether the failure is name resolution, authentication, authorization, rate limiting, or missing content.

Air-gapped clusters make the same point in a stricter form. The secure path is to import signed, scanned digests into an internal registry and deploy those internal references. The risky path is to save arbitrary tar archives, load them manually on nodes, and set `imagePullPolicy: Never` without a record of what was imported. CKS lab tasks sometimes use preloaded images for convenience, but production air gaps still need provenance. Keep a manifest of imported digests, scan results, signatures, and source registry metadata so an operator can answer what is running without internet access.

## Real Exam Scenarios

In a Dockerfile review scenario, start with the final stage. A task may show `FROM ubuntu:latest`, a long `apt-get install` list, no `USER`, a copied `.env`, and shell-form `ENTRYPOINT`. Do not rewrite the whole application. Pin or narrow the base image, move build tools into a builder stage, add `.dockerignore` coverage, remove secrets from image construction, set a non-root user, and use exec-form command syntax. Then connect the image default to Kubernetes `securityContext` so the Pod does not need root to run.

In an image reference scenario, find mutable tags quickly. `kubectl get pods -A -o json` plus `jq` can identify images ending in `:latest` or lacking an explicit tag. For a Deployment, update the image to a digest that was produced by the scan or registry inspection step, then set an appropriate pull policy. If the task asks why the running Pod still shows the old tag, inspect `status.containerStatuses[].imageID`; Kubernetes often records the resolved digest there even when the spec contains a tag. The exam wants you to distinguish requested image from running image identity.

In a private registry scenario, read events before guessing. `ErrImagePull` and `ImagePullBackOff` commonly come from a wrong registry hostname, missing namespace Secret, wrong Secret type, bad credentials, or a ServiceAccount that does not reference the pull Secret. Create the Secret with `kubectl create secret docker-registry`, attach it to the Pod or ServiceAccount, and verify the Pod uses that ServiceAccount. If the error remains, compare the `--docker-server` value with the exact registry prefix in the image name. `registry.example.com/team/app` and `https://registry.example.com` are not always treated the way humans expect.

In a hardening scenario, remember that image and Pod settings reinforce each other. A distroless image with `USER nonroot` can still fail if the application writes to `/var/cache` on a read-only root filesystem. A Pod with `runAsNonRoot: true` can fail if the image metadata has no numeric user and Kubernetes is unable to prove it runs non-root. A base image without a shell can make `kubectl exec -- sh` fail, which is not itself a broken workload. Use logs, probes, and ephemeral debug containers rather than weakening the production image.

In a signing or policy scenario, keep the order of checks clear. First identify the image reference and resolve it to a digest. Then verify whether that digest has the expected signature, certificate identity, key, or attestation. Finally, enforce the result at admission or promotion time. If the question gives you an unsigned image that already runs, changing only the Deployment tag does not create provenance. You need a signed artifact from the approved build path or a policy exception with a clear reason. In real clusters, exceptions should be time-bound and tied to a digest, not to a mutable tag that could later point somewhere else.

In a scanner scenario, do not treat every CVE row as equal. Ask which package owns the finding, whether the package is in the final runtime stage, whether the fixed version exists in the chosen base, and whether the vulnerable code is reachable by the application. The exam usually expects practical remediation, not a debate about theoretical exploitability. Rebuild on a patched base, move build tools out of the final image, or switch to a smaller runtime where the vulnerable package is absent. When the finding belongs to the application dependency graph, update the lock file and rebuild rather than trying to hide the package from the scanner.

```bash
kubectl get pods -A -o json | jq -r '
  .items[] as $pod
  | (
      ($pod.spec.containers // []) + ($pod.spec.initContainers // []) + ($pod.spec.ephemeralContainers // [])
    )[]
  | select(.image | split("/")[-1] | (test("[:@]") | not) or endswith(":latest"))
  | "\($pod.metadata.namespace)/\($pod.metadata.name) \(.name) \(.image)"
'

kubectl -n image-lab describe pod private-app
kubectl -n image-lab get pod private-app -o jsonpath='{.status.containerStatuses[0].imageID}'
```

## Did You Know?

- **Docker Hub pull limits can affect Kubernetes rollouts.** Docker's current docs list 100 pulls per six hours for unauthenticated users by IPv4 address or IPv6 `/64`, and 200 pulls per six hours for authenticated Personal users, so a node scale-up can fail for reasons that look like ordinary image pull errors.

- **`imagePullPolicy: Always` still uses digest caching.** The kubelet resolves the tag to a digest when launching the container, then reuses a cached image if that exact digest is already present, which means `Always` is a registry freshness check rather than a guaranteed full download.

- **Distroless images are easier to operate when debug is planned separately.** Kubernetes documentation recommends ephemeral containers for cases where `kubectl exec` is insufficient, and distroless images are a prime example because they intentionally omit shells and debugging utilities.

- **A digest does not replace a signature.** The digest proves content identity, while cosign or Notation verification proves that an expected key or identity signed the artifact descriptor used by that content.

## Common Mistakes

| Mistake | Why it happens | Fix |
|---|---|---|
| Pinning production to `:latest` | The tag feels like a convenient way to receive updates without editing YAML. | Promote scanned image digests into manifests and reserve mutable tags for development or discovery. |
| Running as root because the base image default is root | Many official images work out of the box without a `USER` instruction, so the privilege is invisible. | Set a non-root user in the final image and reinforce it with `runAsNonRoot` in the Pod security context. |
| Including `.env`, kubeconfig, or SSH material in the build context | `COPY . .` is easy and the sensitive file may not be obvious in a large repository. | Maintain `.dockerignore`, copy only required paths, and keep build secrets out of image layers and logs. |
| Using `ADD` when `COPY` is enough | `ADD` examples are copied from old Dockerfiles without considering its extra archive and URL behavior. | Use `COPY` for local files, and use explicit download plus verification steps when remote content is required. |
| Forgetting `imagePullSecrets` in the workload namespace | The Secret exists elsewhere, or a developer tested with local Docker credentials. | Create a `kubernetes.io/dockerconfigjson` Secret in the target namespace and attach it to the Pod or ServiceAccount. |
| Shipping build tools in the final image | The Dockerfile compiles and runs in one stage, so cleanup is treated as optional. | Use multi-stage builds and copy only runtime artifacts into a minimal final stage. |
| Assuming distroless means no operational work | Teams focus on CVE reduction and discover later that shell-based debugging no longer works. | Add logs, probes, debug images, and ephemeral-container runbooks before switching production workloads. |
| Setting `imagePullPolicy: Never` as a hardening shortcut | The policy sounds restrictive, so it is mistaken for a security control. | Use `Never` only for preloaded or air-gapped workflows; use registry policy, digest pinning, and signatures for trust. |

## Quiz

1. **A Deployment uses `registry.example.com/payments/api:prod` with `imagePullPolicy: IfNotPresent`. Two replicas land on different nodes after a rollout, and only one shows the new behavior. How do you diagnose and fix the image control problem?**

   <details>
   <summary>Answer</summary>
   Inspect each Pod's `status.containerStatuses[].imageID` to compare the resolved digests, because the spec tag can be identical while cached node content differs. The root issue is a mutable tag combined with `IfNotPresent`, which lets nodes reuse whatever local image already matches the tag. The durable fix is to promote the exact scanned digest, such as `registry.example.com/payments/api@sha256:...`, and deploy that digest consistently. If tags must remain in a development path, use `Always` there and keep production on digest-based promotion.
   </details>

2. **A Dockerfile copies `.env` during build and later runs `rm .env` before the final `CMD`. The image scanner reports no active secret file in the final filesystem. Why is this still unsafe, and what Dockerfile pattern fixes it?**

   <details>
   <summary>Answer</summary>
   Docker image layers and build cache can preserve files that were copied in an earlier layer, even if a later layer removes them from the merged filesystem. The secret may also have been sent to a remote builder as part of the build context. The fix is to keep `.env` out of the context with `.dockerignore`, avoid copying broad source trees before filtering, and use runtime Kubernetes Secrets or build secret mounts for values needed only during build. A multi-stage build helps, but only if the secret never crosses into a persisted stage.
   </details>

3. **A Pod using `gcr.io/distroless/static-debian12:nonroot` starts successfully, but `kubectl exec pod/app -- sh` fails during troubleshooting. What should the responder do without weakening the production image?**

   <details>
   <summary>Answer</summary>
   The failure is expected because distroless images intentionally omit shells and debugging utilities. The responder should use logs, metrics, readiness probes, and an ephemeral debug container or a separate debug image rather than adding a shell to the production image. If process inspection is required, enable or use process namespace sharing where appropriate and attach a tool image through `kubectl debug`. The security point is that production runtime images stay minimal while diagnostics are supplied through a controlled break-glass path.
   </details>

4. **A private registry Pod is stuck in `ImagePullBackOff`. The Secret `registry-creds` exists in namespace `default`, while the Pod runs in namespace `payments` and uses `payments-registry.local/api:v1`. What commands and checks are most relevant?**

   <details>
   <summary>Answer</summary>
   First inspect `kubectl -n payments describe pod <name>` for the exact pull error. Then ensure a Docker registry Secret exists in the `payments` namespace with a `--docker-server` value matching `payments-registry.local`, and attach it through `imagePullSecrets` or the Pod's ServiceAccount. A Secret in `default` is not available to Pods in `payments`. After patching the ServiceAccount or Pod template, restart the Pod so kubelet retries with the correct namespace-scoped credentials.
   </details>

5. **Your CI system signs images with cosign, but the Kubernetes manifest still deploys `app:stable`. An attacker obtains registry push rights and replaces the `stable` tag with an unsigned image. Which controls should block or limit the attack?**

   <details>
   <summary>Answer</summary>
   Digest pinning limits the tag replacement because production manifests reference the exact signed digest that passed CI, not the mutable tag. Signature verification limits the attack because admission policy can reject images whose digest lacks a trusted cosign signature or expected identity. Registry permissions and immutable tags reduce the chance of replacement, but they should not be the only controls. A strong workflow signs the pushed digest, records it in the release manifest, and enforces verification before admission.
   </details>

6. **A Go service currently builds in `golang:1.22` and ships that same image to production. The scanner reports many vulnerabilities in compilers and package tools that the binary does not use. What rewrite reduces the risk while keeping the build process intact?**

   <details>
   <summary>Answer</summary>
   Use a multi-stage build. Keep `golang:1.22` as the builder stage, compile the binary there, then copy only the binary into a minimal final stage such as `gcr.io/distroless/static-debian12:nonroot` or `scratch` if the binary and certificates requirements allow it. Set `USER nonroot:nonroot` where the base supports it, and use exec-form `ENTRYPOINT`. This removes compilers and package tools from the production filesystem while preserving the same build commands in the builder stage.
   </details>

7. **A reviewer sees `imagePullPolicy: Always` and says the cluster will download the image on every restart, so the team should switch to `IfNotPresent` for performance. What correction should you make?**

   <details>
   <summary>Answer</summary>
   `Always` makes kubelet resolve the image name to a digest whenever it launches the container, but if the exact digest is already cached locally, kubelet can use the cached content. The performance concern is real only when registry resolution, credentials, or missing layers slow startup. The policy decision should be based on whether the reference is mutable. For digest-pinned production images, `IfNotPresent` is usually reasonable; for mutable development tags, `Always` makes tag movement visible at restart time.
   </details>

## Hands-On Exercise

This lab uses `kind`, a local registry, Docker-compatible build commands, and Trivy or Grype. Run it on a disposable workstation cluster where you can create namespaces, build images, and push to a local registry. The goal is to build a hardened image, scan it before deployment, pull it from a private registry path, and prove that digest pinning protects the running workload from tag movement.

- [ ] Create a local registry container named `kind-registry` on port `5001` if it is not already running: `docker run -d --restart=always -p 127.0.0.1:5001:5000 --name kind-registry registry:2`.
- [ ] Create a kind cluster with a registry mirror for `localhost:5001`, then connect the registry container to the kind network so nodes can pull through `kind-registry:5000`.
```yaml
# kind-with-registry.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
  - |-
    [plugins."io.containerd.grpc.v1.cri".registry]
      config_path = "/etc/containerd/certs.d"
nodes:
  - role: control-plane
```

```bash
kind create cluster --name image-lab --config kind-with-registry.yaml

docker network connect kind kind-registry

for node in $(kind get nodes --name image-lab); do
  docker exec "$node" mkdir -p /etc/containerd/certs.d/localhost:5001
  cat <<EOT | docker exec -i "$node" tee /etc/containerd/certs.d/localhost:5001/hosts.toml
server = "http://localhost:5001"

[host."http://kind-registry:5000"]
  capabilities = ["pull", "resolve"]
EOT
done
```
- [ ] Create a working directory with a tiny Go or static HTTP application, a `go.mod` if needed, and a `.dockerignore` that excludes `.git`, `.env`, `*.key`, `kubeconfig`, and local build output.
- [ ] Write a multi-stage Dockerfile that compiles in a builder stage and copies only the final binary or static files into `gcr.io/distroless/static-debian12:nonroot` or another minimal non-root runtime image.
- [ ] Build the image as `localhost:5001/cks/image-secure:v1` and inspect it with `docker image inspect` to verify the configured user and entrypoint are not root and shell-form.
- [ ] Scan the local image with `trivy image localhost:5001/cks/image-secure:v1` or `grype localhost:5001/cks/image-secure:v1`, then record which findings come from the base image and which come from application dependencies.
- [ ] Push the image to the local registry and capture its digest using `docker buildx imagetools inspect localhost:5001/cks/image-secure:v1` or an equivalent registry inspection command.
- [ ] Create namespace `image-lab`, then create a Docker registry Secret for `localhost:5001` to practice the `imagePullSecrets` workflow even though the local registry may not enforce authentication.
- [ ] Create a ServiceAccount named `image-runner` in `image-lab` and attach the registry Secret through the ServiceAccount `imagePullSecrets` field.
- [ ] Deploy the application by digest through `localhost:5001/cks/image-secure@sha256:REPLACE_WITH_DIGEST`, set `imagePullPolicy: IfNotPresent`, and use the `image-runner` ServiceAccount.
- [ ] Add a Pod security context with `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, and `capabilities.drop: ["ALL"]`; add an `emptyDir` mount if the application needs a writable temporary path.
- [ ] Wait for the Pod to become Ready, then verify `kubectl -n image-lab get pod -o jsonpath='{.items[0].status.containerStatuses[0].imageID}'` reports the expected digest.
- [ ] Rebuild a visibly different image and push it to the same `v1` tag, but do not change the Deployment digest; restart the Pod and verify it still runs the originally pinned digest.
- [ ] Patch the Deployment to the new digest, wait for rollout, and confirm that the digest changes only after the manifest changes.
- [ ] Clean up with `kubectl delete namespace image-lab`, delete the kind cluster, and remove the local registry container if it was created only for this lab.

## Learner check

> A digest proves content identity, but it does not prove who built the image; production promotion should pair digest pinning with signature or attestation checks from the approved pipeline.

Before you move on, explain why `imagePullPolicy: Never` is not a hardening control and which error you expect when the image is missing from the node. A solid answer names `ErrImageNeverPull` / `ImageNeverPull`, not `ImagePullBackOff`.

## Sources

- [Kubernetes Images](https://kubernetes.io/docs/concepts/containers/images/) — documents image names, pull policy defaults, digest resolution, private registry references, and credential verification behavior.
- [Kubernetes: Pull an Image from a Private Registry](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) — shows the supported `docker-registry` Secret workflow and Pod `imagePullSecrets` usage.
- [Kubernetes Ephemeral Containers](https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/) — explains why distroless images need a separate debugging path when `kubectl exec` is insufficient.
- [Kubernetes Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) — provides the Pod and container fields used to reinforce non-root image defaults.
- [Docker Build Best Practices](https://docs.docker.com/build/building/best-practices/) — covers trusted base images, multi-stage builds, rebuild cadence, `.dockerignore`, and Dockerfile instruction guidance.
- [Docker Hub Pull Usage and Limits](https://docs.docker.com/docker-hub/usage/pulls/) — lists current Docker Hub pull limits and explains how pull accounting and `429` responses work.
- [GoogleContainerTools Distroless](https://github.com/GoogleContainerTools/distroless) — source project for Google's distroless runtime images and examples.
- [Sigstore Cosign Verification](https://docs.sigstore.dev/cosign/verifying/verify/) — documents `cosign verify` and the identity checks used for signed container artifacts.
- [Notary Project Quickstart](https://notaryproject.dev/docs/quickstart/) — introduces Notation signing and verification for OCI artifacts.
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker) — benchmark source for Docker daemon, image, Dockerfile, and runtime hardening guidance.
- [NIST SP 800-190: Application Container Security Guide](https://csrc.nist.gov/pubs/sp/800/190/final) — NIST guidance on image, registry, orchestrator, host OS, and runtime container security.
- [NVD CVE-2024-21626](https://nvd.nist.gov/vuln/detail/CVE-2024-21626) — runc advisory for a container escape class involving leaked file descriptors and host filesystem access.
- [NVD CVE-2021-32760](https://nvd.nist.gov/vuln/detail/CVE-2021-32760) — containerd advisory showing how crafted image extraction can affect host filesystem permissions.
- [Codecov Bash Uploader Security Update](https://about.codecov.io/security-update/) — real CI supply-chain incident with documented malicious uploader behavior and affected time windows.
- [GitHub Advisory: Embedded malware in ua-parser-js](https://github.com/advisories/GHSA-pjwm-rvh2-c87w) — advisory for malicious `ua-parser-js` versions `0.7.29`, `0.8.0`, and `1.0.0`.
- [CNCF TAG Security: ua-parser-js compromise](https://tag-security.cncf.io/community/catalog/compromises/2021/ua-parser-js/) — compromise catalog entry linking package hijack details to cloud-native supply-chain practice.
- [CNCF TAG Security Software Supply Chain Best Practices v2](https://tag-security.cncf.io/blog/software-supply-chain-security-best-practices-v2/) — CNCF guidance on build inputs, attestations, artifact security, and deployment policy.
- [KodeKloud CKS Exam Verification Guide](https://kodekloud.com/blog/certified-kubernetes-security-specialist-cks-exam-verification-guide/) — CKS preparation reference that includes supply-chain security, image scanning, signing, and Dockerfile security topics.

## Next Module

[Module 5.2: Image Scanning with Trivy](../module-5.2-image-scanning/) - Find known vulnerabilities, misconfigurations, and embedded secrets in container images before deployment.
