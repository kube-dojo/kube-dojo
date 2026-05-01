You are drafting a new KubeDojo curriculum module: **Module 9.3: KServe — Production Model Serving on Kubernetes**.

Place this NEW module under issue #379 (Phase A.2 greenfield MLOps deep-dives). Codex drafts; Claude (orchestrator) reviews source-fidelity before merge.

# Binding spec

Follow `scripts/prompts/module-writer.md` as the BINDING quality + structure spec. Read the file at the top of your run. It enforces:
- 600-800+ lines of CONTENT minimum (visual aids don't count toward this)
- 3-5 Bloom L3+ Learning Outcomes (verbs: design / debug / evaluate / compare / configure)
- "Why This Module Matters" — third-person dramatic real-world opening
- 3-6 core content sections with theory-before-practice
- Patterns & Anti-Patterns + Decision Framework (this is `[COMPLEX]`)
- EXACTLY 4 "Did You Know?" facts with real numbers/dates
- Common Mistakes table with 6-8 rows
- Quiz with 6-8 questions, AT LEAST 4 scenario-based, `<details><summary>` answers (no recall)
- Hands-On Exercise — 4-6 progressive tasks with `<details>` solutions and success-criteria checklist
- At least 2 inline active learning prompts distributed through core content (not back-loaded)
- ASCII diagrams properly aligned; Mermaid for sequence/flow; tables for comparisons
- All code runnable; YAML 2-space indent; ` ```bash ` / ` ```yaml ` language tags
- kubectl alias `k` after explained once; K8s 1.35+
- NEVER repeat the number 47 (known LLM pattern); vary numbers
- NO emojis
- NO secrets that match real patterns (use `your-token-here`, `https://hooks.slack.com/services/YOUR/WEBHOOK/HERE`, etc.)

# Module specification

- **Title**: `Module 9.3: KServe`
- **File path**: `src/content/docs/platform/toolkits/data-ai-platforms/ml-platforms/module-9.3-kserve.md`
- **Slug**: `platform/toolkits/data-ai-platforms/ml-platforms/module-9.3-kserve`
- **Sidebar order**: `4` (after 9.1 Kubeflow=2, 9.2 MLflow=3)
- **Complexity**: `[COMPLEX]`
- **Time**: 55-65 minutes
- **Prerequisites**:
  - [Module 5.4: Model Serving](../../../disciplines/data-ai/mlops/module-5.4-model-serving/) — discipline-level overview that names KServe as a serving framework to evaluate
  - [Module 9.1: Kubeflow](module-9.1-kubeflow/) — KServe is the serving component of Kubeflow
  - [Module 9.2: MLflow](module-9.2-mlflow/) — Model Registry feeds InferenceService storageUri
  - Kubernetes fundamentals: Deployments, Services, HPA, custom resources, Ingress, PVCs
  - Familiarity with REST APIs and request/response contracts
  - Optional: Knative Serving exposure (KServe's serverless mode is Knative-based)
- **Next Module**: Plain-text "Module 9.4: vLLM (planned)" — do NOT add a `:::tip` or link block, just a one-line teaser at the bottom

# Topic coverage (must hit all of these)

1. **KServe architecture & control flow** — KServe controller, ServingRuntime CRD, InferenceService CRD, the hand-off to Knative Serving (in serverless mode) or to a vanilla Deployment (in raw mode). Show both control-plane and data-plane diagrams (ASCII).
2. **InferenceService anatomy** — `spec.predictor` (model + runtime), `spec.transformer` (pre/post-processing), `spec.explainer` (interpretability). Walk through a complete YAML for a sklearn iris classifier with each field explained.
3. **Model storage and runtimes** — Storage URIs (`s3://`, `gs://`, `pvc://`, `http(s)://`), Storage Initializer init container, ServingRuntime CRDs, multi-framework support (sklearn, XGBoost, TensorFlow, PyTorch, ONNX via Triton, HuggingFace, custom predictor images). Compare TF Serving / Triton / TorchServe / MLServer as runtimes inside KServe.
4. **Serverless mode vs Raw Deployment mode** — the most important pedagogical fork in KServe. Serverless = Knative + scale-to-zero + cold-start cost; Raw = Deployment + HPA + always-on. When to choose which. Show YAML for both. Include a comparison table with scaling characteristics, GPU implications, latency profile, complexity cost.
5. **Rollout strategies** — Canary via `canaryTrafficPercent`, traffic-splitting via Knative revision routing, blue/green via tag-based routing, shadow deployments. Show concrete `kubectl apply` flow for promoting a canary from 10% → 100%.
6. **Autoscaling and resource management** — KPA (Knative Pod Autoscaler) vs HPA, concurrency-based vs RPS-based scaling, GPU autoscaling, scaling to zero risk profile, batching for throughput optimisation. Cover `containerConcurrency`, `minReplicas`, `maxReplicas`, GPU resource requests.
7. **Multi-model and inference graphs** — ModelMesh for high-density serving (many small models per pod) vs InferenceGraph for ensembles/chains/A-B testing. Show one InferenceGraph YAML.
8. **Production concerns** — Observability (Prometheus metrics, OpenTelemetry traces, request logging), security (mTLS via Istio sidecars, AuthorizationPolicy, model artifact integrity), GPU scheduling integration, ingress (Istio Gateway / Knative Domain Mapping), monitoring drift via integrated explainers.

The "Current Landscape" section should compare KServe vs Seldon Core vs BentoML vs Ray Serve vs raw K8s Deployments. Be honest about KServe's tradeoffs (Knative dependency complexity, ModelMesh learning curve, GPU autoscaling rough edges).

# Hands-On Exercise concept

Deploy a real model end-to-end on a local K8s cluster. Required tasks:

1. **Setup** — Install KServe (Quick Install via `kserve-quickstart-environments` or full install) on `kind` or `minikube`. Verify the KServe controller pod and ServingRuntime CRDs.
2. **First InferenceService** — Deploy the sklearn iris model from KServe's example repository. Curl the prediction endpoint via Istio Ingress.
3. **Add a transformer** — Custom Python transformer for input preprocessing. Show how the request flows: Transformer → Predictor → response.
4. **Canary rollout** — Deploy a v2 of the model. Configure `canaryTrafficPercent: 10`. Send mixed traffic. Promote to 100%.
5. **Switch to raw deployment mode** — Annotate the InferenceService with `serving.kserve.io/deploymentMode: RawDeployment`. Compare behavior (no scale-to-zero, no cold start).
6. **(Optional bonus)** — Add an explainer using KServe's Alibi integration; query the explanation endpoint.

Each task should have:
- Setup/run commands (complete, runnable on `kind`)
- Expected output snippet
- Solution in `<details>` tag
- A `- [ ]` success criterion

# Sources discipline

Required `## Sources` section at the bottom with VERIFIED URLs. Use these as the primary anchor pool — verify each is reachable when you draft (`curl -sI` or open):
- KServe website (master): https://kserve.github.io/website/master/
- KServe GitHub: https://github.com/kserve/kserve
- InferenceService API reference: https://kserve.github.io/website/master/reference/api/
- ServingRuntime concept: https://kserve.github.io/website/master/modelserving/servingruntimes/
- Serverless vs Raw deployment: https://kserve.github.io/website/master/admin/serverless/serverless/
- ModelMesh: https://kserve.github.io/website/master/modelserving/mms/modelmesh/overview/
- InferenceGraph: https://kserve.github.io/website/master/modelserving/inference_graph/
- Knative Serving (KServe's serverless backbone): https://knative.dev/docs/serving/
- KServe canary rollout: https://kserve.github.io/website/master/modelserving/v1beta1/rollout/
- Triton, TF Serving, TorchServe, MLServer official docs (one URL each)

CRITICAL per `feedback_citation_verify_or_remove.md`: every URL in body text MUST appear in `## Sources`. If you can't verify a URL is reachable + supports the claim it's cited for, remove the citation. "Unverified = remove."

# Anti-gaming protections

Per `feedback_codex_prose_meta_diction_leak.md`: do NOT leak orchestrator-process language into reader-facing prose. Forbidden words/phrases in body: "the contract", "Yellow", "anchor", "deliberately cautious", "load-bearing", "boundary contract", "unverified", "out-of-scope", "scope creep". These belong in research notes, not in a learner-facing module.

Per `feedback_teaching_not_listicles.md`: this is a TEACHING module, not a fact dump. Every section needs prose explanation between code blocks. The reader should leave able to design + deploy + debug a KServe inference service, not just recognise the YAML.

# Output

Write the file directly to `src/content/docs/platform/toolkits/data-ai-platforms/ml-platforms/module-9.3-kserve.md`. Do NOT edit any other files (the orchestrator will update the toolkit `index.md` and run `npm run build` after reviewing your draft).

After writing, report back with:
- Line count (`wc -l`)
- Content line count (excluding code blocks and ASCII tables)
- Word count (`wc -w`)
- Number of `<details>` quiz/answer blocks
- Number of `## Sources` rows
- Any URLs you could not verify (so the orchestrator can curl-check them in review)
- Any topic from the brief above you couldn't cover at depth (and why)

Do NOT mark `revision_pending: true` in frontmatter — this is a brand-new module, not a #388 rewrite candidate.
