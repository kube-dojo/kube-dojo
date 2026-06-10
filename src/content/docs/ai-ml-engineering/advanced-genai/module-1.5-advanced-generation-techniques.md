---
title: "Advanced Generation Techniques"
slug: ai-ml-engineering/advanced-genai/module-1.5-advanced-generation-techniques
sidebar:
  order: 806
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 3-4 hours
>
> **Prerequisites**: Transformer attention mechanics, basic probability and softmax, comfort running Python with Hugging Face Transformers or an OpenAI-compatible inference API. Alignment training (RLHF, DPO, Constitutional AI) is covered in [Module 1.4: RLHF & Alignment](../module-1.4-rlhf-alignment/); this module focuses on what happens at inference time when logits become text.

## Learning Outcomes

By the end of this module, you will be able to:

- **Explain** how autoregressive language models convert next-token logits into sampled tokens through softmax, temperature, and the decode loop.
- **Compare** greedy decoding, beam search, and stochastic sampling strategies when latency, determinism, and creativity requirements differ.
- **Configure** temperature, top-k, top-p, repetition penalties, and stop sequences for production inference workloads.
- **Describe** speculative decoding, grammar-constrained generation, and inference-time scaling techniques such as self-consistency.
- **Implement** a small decoding experiment that measures how sampling parameters change output diversity and repetition.

## Why This Module Matters

Training teaches a model what language looks like; decoding decides what language you actually get. Two deployments can share identical weights yet produce radically different user experiences because one streams greedy argmax tokens while the other samples with nucleus filtering and repetition control. When product teams report that a model is "too robotic," "too random," or "keeps repeating itself," the failure is usually not a mysterious alignment regression — it is a decoding configuration problem sitting one layer above the weights.

Hypothetical scenario: an engineering team ships a customer-support assistant that answers correctly in offline evals but frustrates users in production. Offline tests used temperature zero and a short max token cap, so every answer looked crisp and deterministic. Production enabled default sampling to sound more conversational, but nobody adjusted top-p or repetition penalties. The model began meandering through polite filler, occasionally restating the same apology paragraph, and sometimes hallucinating policy details that were not in the retrieval context. The weights did not change between environments; the decoding policy did, and that policy was invisible in the training metrics dashboard.

Understanding generation mechanics is what lets you separate model quality from serving quality. You need to know why greedy decoding is appropriate for JSON field extraction but harmful for creative drafting, why beam search can look fluent yet dull in open-ended chat, and why speculative decoding can cut latency without changing the target model's output distribution when implemented correctly. You also need a vocabulary for constrained outputs — JSON mode, grammar-guided decoding, tool-call schemas — because enterprise applications increasingly require machine-readable structure, not just plausible prose. For alignment concerns such as refusal behavior and preference optimization, see [Module 1.4](../module-1.4-rlhf-alignment/); here we stay on the inference path from logits to tokens.

Decoding is also where safety and product policy meet physics. Alignment training shapes refusal tendencies and helpfulness, but decoding choices determine whether the model meanders into over-long justifications, emits disallowed formatting, or repeats policy text verbatim. Runtime filters — blocklists, classifiers, grammar masks — sit adjacent to decoding rather than inside it, yet they are configured together in practice. When you read incident postmortems, look for whether the failure was a policy violation the model considered unlikely, or a policy violation the decoder made likely by suppressing better alternatives.

The gap between research demos and production assistants is often a decoding gap. Research notebooks frequently run with generous token limits, manual cherry-picking, and implicit human filtering of bad samples. Production systems must handle adversarial prompts, bursty concurrency, and strict latency budgets while still returning a single stream the user sees. When you debug a bad answer, ask two questions in order: did the model assign low probability to the correct continuation, or did the decoding policy never allow that continuation to be sampled? The first question points to data, fine-tuning, or retrieval. The second points to temperature, masks, penalties, or stop sequences. Mixing those diagnoses wastes weeks of alignment work on what is actually a serving configuration ticket.

Generation parameters also interact with context construction. A retrieval-augmented prompt may place the answer in the documents, but high temperature on the final completion can still introduce unsupported details. A low-temperature extractor may emit valid JSON while omitting nullable fields your schema expects. That is why mature teams version decoding presets per endpoint the same way they version model weights: `extractor-v3-greedy`, `chat-v7-nucleus`, `tool-router-v2-schema-greedy`. The presets encode product intent more directly than a single global default copied from a model card.

> **The Thermostat Analogy**
>
> Think of decoding parameters as a thermostat for randomness, not as a second model inside the model. Temperature, top-k, and top-p do not add new facts; they reshape which high-probability continuations the engine is allowed to pick. Turn the randomness down and you get predictable, sometimes brittle text. Turn it up and you explore more of the distribution, which helps creativity but increases the risk of drift and repetition. Production engineering is the art of picking a room temperature for each workload rather than copying defaults from a playground screenshot.

## From Logits to Tokens: The Autoregressive Loop

Every causal language model inference step produces a vector of logits — one unnormalized score per vocabulary entry for the next token. The engine selects a token, appends it to the context, runs another forward pass, and repeats until a stop condition fires. That loop is simple to describe and surprisingly easy to misconfigure, because each knob changes the geometry of the distribution from which tokens are drawn.

Softmax converts logits into a probability distribution. For logits vector \(z\) and vocabulary index \(i\), the probability is \(p_i = \exp(z_i / T) / \sum_j \exp(z_j / T)\), where \(T\) is temperature. When \(T\) approaches zero, the distribution collapses toward the argmax token; when \(T\) increases, probability mass spreads across more candidates. Temperature is not a quality dial; it is a diversity dial. Lower temperature reduces surprise but can also lock the model into repetitive high-likelihood phrases when the context strongly favors them.

Greedy decoding chooses the argmax token every step. It is fast, deterministic, and easy to cache, which makes it attractive for extraction tasks, classification-style prompts, and any workflow where you want the same input to yield the same output. Teams sometimes call this "temperature zero" in API docs even though the implementation details differ slightly across engines; the product meaning is the same: remove sampling noise so QA and compliance teams can reproduce outputs during audits. The weakness is structural: greedy paths are locally optimal but globally brittle. A slightly lower-probability token early in a sentence can open much better continuations later, but greedy search never explores that branch. That is why greedy outputs can look terse, repetitive, or oddly overconfident even when the underlying model is capable.

Sampling draws tokens from the softmax distribution (possibly modified by top-k, top-p, penalties, or grammar masks). Stochastic decoding introduces run-to-run variation, which is often desirable for brainstorming, marketing copy, and synthetic data generation. It also complicates testing: you must evaluate distributions of outputs, not a single golden string. Production systems therefore store decoding parameters alongside model version in telemetry, because reproducing a bug without the exact sampling seed and policy is difficult.

Consider a toy vocabulary of four tokens — `therefore`, `however`, `because`, `maybe` — where logits after context are `[2.0, 1.5, 1.0, 0.1]`. Greedy decoding always picks `therefore`. With temperature `2.0`, probabilities spread and `however` or `because` appear more often. With top-k equals two, only the two highest-logit tokens (`therefore`, `however`) survive, so both `because` and `maybe` are removed before sampling even if temperature would otherwise admit them. With top-p equals `0.9`, the engine might keep `{therefore, however, because}` because their cumulative mass crosses the threshold while excluding the long tail. This toy example is not realistic scale, but it shows why engineers combine filters: temperature alone does not remove junk tail tokens in huge vocabularies, while top-p alone does not add creativity when the distribution is already sharp.

The following diagram shows the per-step data flow inside a typical autoregressive server. Prefill computes logits for the prompt in parallel; decode repeats single-token steps until stopping criteria trigger.

```text
Prompt tokens ──► Transformer forward pass ──► logits [vocab]
                                                    │
                                                    ▼
                                           softmax + temperature
                                                    │
                     ┌──────────────────────────────┼──────────────────────────────┐
                     ▼                              ▼                              ▼
               greedy argmax                  top-k / top-p mask            grammar / JSON mask
                     │                              │                              │
                     └──────────────────────────────┴──────────────────────────────┘
                                                    │
                                                    ▼
                                           sample or select token
                                                    │
                                                    ▼
                                    append token ──► next decode step
```

Most serving engines expose this loop through a `generate` or `sampling_params` API. The weights define what is likely; the decoding policy defines what is allowed. Keeping those concerns separate in your mental model prevents you from fine-tuning a model to fix a problem that is actually caused by `temperature=1.2` on a extraction prompt.

Stopping criteria are part of the decode loop even though they are not a sampling strategy. Engines stop when they emit an end-of-sequence token, match a configured stop string, or reach `max_new_tokens`. Stop sequences are deceptively powerful: adding `"\n\nUser:"` can prevent a chat model from hallucinating the next user turn, while omitting a stop token on tool-call templates can leak closing braces into the user-visible stream. Always test stop behavior with streaming enabled, because partial token chunks can delay stop detection until a buffer flushes.

Logits processors and warpers form another layer between raw model outputs and token selection. A processor might ban repeated n-grams; a warper might apply temperature or top-p. In Hugging Face Transformers these hooks chain together before softmax sampling or argmax selection. Conceptually, think of them as a pipeline: raw logits, optional bias adjustments, temperature scaling, masking illegal tokens, penalty adjustments, normalization, then selection. Serving engines implement the same pipeline with different names, which is why porting settings between frameworks requires checking each stage rather than copying numeric values blindly.

The decode loop also interacts with KV-cache memory. Each generated token extends the cache, so long completions increase memory footprint per request even when compute per step stays roughly constant. Aggressive `max_new_tokens` defaults therefore hurt cluster stability under load, not just user experience. When you tune decoding for quality, simultaneously watch cache growth and time-to-first-token, because a policy that encourages rambling answers can degrade throughput for unrelated requests on the same GPU.

## Decoding Strategies: Greedy, Beam Search, and Sampling

Different tasks need different search strategies. The durable question is not "which strategy is best," but which objective you are optimizing: exact reproducibility, fluent constrained translation, open-ended creativity, or structured machine output.

Greedy decoding selects the highest-probability token at each step. Implementation cost is minimal and latency is predictable because there is no branching. Use greedy or near-greedy settings when you want deterministic JSON keys, stable unit-test outputs, or rigid templates. Avoid greedy decoding for long-form creative generation when local argmax choices funnel the model into generic, repetitive phrasing.

Beam search keeps the top `b` partial hypotheses at each step and expands each one. It explores multiple futures simultaneously and often improves performance on tasks with strong lexical overlap constraints, such as machine translation or summarization with reference n-grams. Beam search is less popular in modern chat models for open-ended dialogue because it increases compute, can favor safe but bland continuations, and interacts poorly with sampling-based diversity goals. A practical rule: reach for beam search when you have an external scoring target and narrow output space; reach for sampling when human readers judge subjective quality.

Beam width is not "more intelligence for free." Wider beams increase memory and compute roughly linearly in many implementations because each step must score and store multiple partial sequences. Diminishing returns appear quickly once the beam is wide enough to capture obvious alternatives. In production, teams sometimes use beam search only for internal reranking: generate several candidates with sampling, then score them with a cheap metric, which separates diversity from selection more cleanly than an enormous beam during decoding.

Length normalization is another beam-search detail that matters in practice. Without normalization, beams that add short common tokens can accumulate artificially high scores. Engines therefore divide by length raised to a power or apply coverage penalties in summarization systems. You do not need to implement these penalties manually in modern libraries, but you should know they exist so you can interpret why two beam configurations with the same width produce different length profiles.

Stochastic sampling is the default family for conversational assistants. Within that family, engineers combine several filters. The filters are commutative in intent but not in implementation order: penalties usually apply to logits before temperature scaling in many stacks, while grammar masks apply after logits are computed but before sampling. When porting settings between frameworks, compare pipeline diagrams in documentation rather than assuming identical math.

Typical sampling also applies repetition penalties. Frequency penalty reduces logits proportional to how often a token already appeared; presence penalty fires once if a token appeared at all. These heuristics are not principled Bayesian inference, but they are cheap and effective for preventing "the the the" style collapse in long completions. Pair them with sensible `max_tokens` limits and stop sequences for endpoints you control. On long documents, also watch **context repetition**: if the prompt itself repeats boilerplate, penalties may suppress legitimate tokens that happen to appear often in the source material.

Modern chat models with large vocabularies benefit from **min-p** style floors that discard tokens whose probability is tiny relative to the top candidate. The intuition is that enormous vocabularies contain thousands of plausible-looking low-probability tokens; without a floor, even top-p sampling occasionally admits a bizarre tail token that derails tone. Min-p does not replace top-p; it complements it by removing tokens that are technically inside the nucleus but still orders of magnitude less likely than the leader.

When users complain that the model "sounds like a template," the fix is often a bundle: slightly higher temperature, top-p around `0.85`–`0.95`, modest repetition penalty, and a prompt that encourages specificity. When users complain that answers "drift off topic," the fix is usually lower temperature, tighter top-p, and stronger adherence to retrieved context — not a larger model. Building a decoding preset library with named policies helps product teams describe changes in human language while engineers retain reproducible configs.

| Technique | What it does | When it helps | Risk if misused |
|-----------|--------------|---------------|-----------------|
| Temperature | Rescales logits before softmax | Tune creativity vs determinism | Very low values on chat prompts sound robotic; very high values increase nonsense |
| Top-k | Keeps only the k highest logits | Caps wild tail tokens cheaply | Fixed k across tasks ignores context-dependent vocabulary breadth |
| Top-p (nucleus) | Keeps smallest set whose cumulative prob ≥ p | Adapts candidate count to context | High p with high temperature can still admit rare tokens |
| Min-p | Drops tokens below a probability floor relative to the top token | Reduces low-probability junk in modern vocabularies | Aggressive floors can truncate valid rare names |
| Repetition / frequency / presence penalties | Down-weights tokens already generated | Reduces loops in long outputs | Too much penalty creates broken grammar or topic drift |
| No-repeat n-gram | Forbids repeating n-grams | Stops copy loops in summarization | Can block legitimate repeated entities ("Paris... Paris") |

Nucleus sampling, introduced in Holtzman et al.'s work on neural text degeneration, keeps the smallest set of top tokens whose cumulative probability exceeds a threshold `p`. Unlike fixed top-k, nucleus sampling adapts to sharp or flat distributions. When the model is confident, the nucleus may contain only a handful of tokens; when uncertain, it widens. That adaptivity is why top-p became a common default in open-ended generation pipelines.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

| Surface | Example parameter names | Notes |
|---------|-------------------------|-------|
| Hugging Face `generate` | `temperature`, `top_k`, `top_p`, `repetition_penalty`, `no_repeat_ngram_size` | Widely used in research scripts and smaller deployments |
| vLLM `SamplingParams` | `temperature`, `top_k`, `top_p`, `min_p`, `presence_penalty`, `frequency_penalty` | Exposed by many OpenAI-compatible servers |
| OpenAI-compatible APIs | `temperature`, `top_p`, `presence_penalty`, `frequency_penalty`, `stop` | Names map closely but defaults differ by provider |

This table is illustrative, not a leaderboard or endorsement. Teach the concepts first; verify exact field names in your engine's documentation before shipping.

Choosing decoding settings should begin with a workload taxonomy rather than a random grid search. Extraction workloads need deterministic or low-entropy settings, strict stop sequences, and often grammar masks. Conversational assistants need moderated stochasticity with repetition control and context-dependent temperature overrides for sensitive subflows. Code generation frequently benefits from moderate sampling plus execution-based verification external to the decoder. Summarization over known documents sometimes still uses beam search when metrics reward n-gram overlap, but abstractive summaries for human readers often prefer nucleus sampling with penalties tuned to reduce copying from the source.

When you run A/B tests on decoding parameters, hold the model weights, prompt template, and retrieval context constant. Change one knob at a time: first temperature, then top-p, then penalties. Log enough telemetry to reconstruct each completion's policy. Teams that change multiple parameters simultaneously often ship a "winning" configuration they cannot reproduce, which becomes painful the moment a new model version arrives and the old magic numbers stop working.

## Speculative and Assisted Decoding

Autoregressive decoding is sequential: one forward pass per generated token. That sequential structure makes decode latency dominate interactive chat once prompts are long. Speculative decoding attacks the serial bottleneck without changing the target model's output distribution when implemented with a correct accept/reject step.

The core idea is draft-then-verify. A smaller draft model (or a cheaper draft mechanism such as n-gram lookup, Medusa heads, or EAGLE-style feature prediction) proposes several candidate tokens quickly. The large target model evaluates those candidates in parallel. Accepted prefixes extend the sequence in one shot; rejected prefixes truncate at the first mismatch and resample that position from the *normalized residual distribution* — the target distribution with the draft's already-proposed probability mass subtracted out, `(p_target − p_draft)₊` renormalized — rather than from the raw target distribution. That residual-resampling step is precisely what makes speculative decoding *exactly* distribution-preserving rather than merely approximate. Because verification uses the target model's true conditional probabilities, you preserve exact sampling properties relative to the target model, unlike naive distillation that permanently alters weights.

Picture two writers collaborating under deadline. A fast junior writer drafts a paragraph quickly; a senior editor checks each sentence against a style guide. Sentences that match are accepted in bulk; the first mismatch sends the team back to rewrite from that point. Speculative decoding is the same division of labor applied to token streams. The junior model must be cheap enough to run on every step; the senior model remains authoritative. If the junior writer invents facts the senior would never approve, acceptance collapses and speedups vanish. That is why draft selection is an engineering problem tied to your specific target checkpoint, not a universal constant.

Some deployments expose speculative decoding as a server flag; others require loading a draft model into GPU memory explicitly. Memory planning must include both models or the added heads. If your service already runs near GPU memory limits because of long contexts, speculative decoding may be impossible without reducing concurrent requests or shrinking context windows. Treat speculative decoding as a latency tool validated by benchmarks, not a checkbox feature.

Leviathan et al. describe speculative decoding as sampling from the target model while amortizing forward passes across multiple tokens. Medusa and EAGLE extend the idea with additional prediction heads or draft features trained to align with the target model's hidden states. Assisted generation in Hugging Face Transformers follows the same pattern: a draft model proposes, the target confirms. The engineering tradeoff is memory for an extra model versus latency savings that grow with acceptance rate.

Acceptance rate depends on draft-target agreement. If the draft model diverges sharply from the target, most proposals are rejected and you pay verification overhead without benefit. Speculative decoding therefore works best when the draft is small but stylistically aligned — often a distilled sibling model or an earlier checkpoint from the same family. For serving configuration details (continuous batching, KV cache, OpenAI-compatible flags), see [Module 1.3: vLLM and sglang Inference](../../ai-infrastructure/module-1.3-vllm-sglang-inference/); this module stays on the algorithmic accept/reject pattern.

```text
Target model distribution ────────────────────────────────────────────────┐
                                                                          │
Context ──► Draft model proposes tokens d1,d2,d3,d4                       │
                │                                                         │
                ▼                                                         │
         Target verifies (p_target(d_i | context))                        │
                │                                                         │
       ┌────────┴────────┐                                                │
       ▼                 ▼                                                │
  accept prefix      reject at first mismatch                             │
       │                 │                                                │
       └────────► append accepted tokens ──► continue from corrected state┘
```

Assisted decoding is not free speed. You must budget GPU memory for draft weights, tune how many speculative tokens to propose per step, and measure end-to-end latency under your real concurrency pattern. Still, for latency-sensitive chat, speculative paths are among the few optimizations that reduce decode time without asking users to accept a smaller model.

N-gram lookup drafts are a lightweight variant when repeated phrases dominate, such as templated support macros or boilerplate legal clauses. Medusa-style multi-head drafts add trainable heads that predict several future tokens from the target model's hidden states, which can raise acceptance rates when tuned for a specific base checkpoint. EAGLE-family approaches reason about feature uncertainty rather than relying solely on a smaller autoregressive draft model. The engineering pattern remains: propose cheaply, verify with the target distribution, accept a prefix or resample.

When evaluating speculative decoding, report both single-request latency and batch throughput. A configuration that helps one isolated stream may contend for memory bandwidth when dozens of streams verify drafts simultaneously. Pair microbenchmarks with load tests on the same scheduler settings you run in production, because continuous batching changes acceptance dynamics by altering batch composition mid-flight.

## Constrained and Structured Generation

Many production workflows require outputs that are not merely plausible sentences but valid JSON documents, SQL snippets, configuration files, or tool-call envelopes. Plain sampling makes syntax errors likely because any token with nontrivial probability can appear. Constrained generation restricts the logits mask at each step so only tokens that keep the partial output valid remain.

JSON mode and schema-guided generation are the most common enterprise patterns. Instead of prompting "return JSON only" and hoping, the engine maintains a parser state — often a finite automaton derived from a grammar — and zeroes logits for tokens that would violate the grammar. Libraries such as Outlines, Guidance, lm-format-enforcer, and XGrammar implement variations of this masked decoding approach. The durable principle is the same: treat structure as a hard constraint on the action space, not as a post-hoc `json.loads` repair step.

Prompt-only structural instructions fail in predictable ways. Models may wrap JSON in markdown fences, prepend commentary, or emit trailing commas that break strict parsers. Retry loops that ask the model to "fix your JSON" sometimes work but add latency and cost unpredictably. Masked decoding attacks the failure at the source by never sampling illegal tokens. The remaining failures are semantic — wrong field values, swapped units, invented identifiers — which is why downstream validation still matters.

Function calling interfaces usually specify a JSON schema for arguments. The runtime should validate returned objects against that schema before invoking tools. If validation fails, return a structured error to the model in a follow-up turn rather than silently coercing types. Coercion hides bugs and teaches the model that malformed outputs are acceptable because something downstream will guess the intent.

Grammar-based constrained decoding uses context-free or regular grammars (GBNF is a compact grammar notation used in several inference stacks) to describe allowed token sequences. Regex constraints are a narrower special case. Function and tool calling extends the idea to typed argument objects: the model must emit a machine-parseable call record that your runtime dispatches. Reliability improves because invalid branches never get sampled, though you still need application-level validation for semantic correctness — a valid JSON object can still contain wrong field values.

Logit bias offers a lighter-weight constraint: add a scalar bias to specific token IDs to encourage or discourage particular strings. This is useful for forcing yes/no answers or nudging ISO date formats, but it does not guarantee validity the way grammar masks do. Use logit bias when the constraint is soft; use grammar or schema masks when invalid syntax would break downstream parsers.

Constrained decoding interacts with sampling. You can apply top-p sampling within the legal mask, or you can remain greedy inside the grammar for maximum determinism. A common production pattern is greedy or low-temperature decoding inside a JSON schema for tool routing, then higher temperature for the natural-language user message in a separate call. Splitting tasks keeps structure reliable without forcing the entire assistant voice into argmax blandness.

Regex-guided constraints sit between logit bias and full grammars. They are convenient for enforcing simple patterns — dates, identifiers, enumerated literals — but become brittle when nested structure grows. JSON Schema-to-automaton compilation is the scalable direction: compile the schema once, mask illegal tokens during generation, then validate with a standard schema library afterward for defense in depth. If the compile step fails, fall back to a smaller manual grammar rather than silently dropping constraints.

Tool-call reliability improves when the runtime separates **selection** from **argument filling**. A first constrained decode chooses the tool name from a closed set; a second decode fills arguments conditioned on that choice. Monolithic prompts that ask for everything at once increase combinatorial error rates because the model must simultaneously reason about intent and syntax. Multi-stage constrained decoding adds latency but reduces catastrophic parse failures that break agent loops.

Security note: constrained decoding prevents malformed syntax, not malicious semantics. A model can still emit valid JSON with unsafe shell commands in a string field. Combine grammar masks with outbound policy checks, sandboxed execution, and least-privilege tool credentials. Treat structured generation as a parser guarantee, not an authorization layer.

## Inference-Time Scaling for Quality

Training-time scaling increases capability by growing data, parameters, and compute. Inference-time scaling spends extra forward passes at request time to improve answer quality without changing weights. The unifying idea is to sample or search multiple reasoning paths, then aggregate with voting, scoring, or verification.

Self-consistency decoding generates several chain-of-thought completions at nonzero temperature, then selects the majority answer among final choices. It trades compute for robustness on reasoning-heavy prompts where a single greedy path is fragile. Best-of-N sampling draws multiple completions and ranks them with a verifier — which may be a reward model, a unit test, a JSON schema check, or a domain-specific scorer. The verifier must be cheaper or more reliable than the failure it prevents; otherwise you are paying twice for unclear benefit.

A useful decision checklist for inference-time scaling starts with three questions. First, is the final answer checkable with an automated test cheaper than generating another full completion? If yes, best-of-N or generate-and-test loops are attractive. Second, does the task have a discrete answer space where majority vote is meaningful? If yes, self-consistency is a natural fit. Third, does latency already dominate user satisfaction? If yes, any multi-sample technique needs a gated trigger — for example run self-consistency only when the first greedy answer fails a confidence heuristic.

These techniques also appear in agent frameworks under different names: parallel tool planning, candidate plan scoring, or reflection loops that rewrite answers. The decoding-level view in this module is the foundation: you are spending extra forward passes to explore alternative token sequences. Higher-level agent orchestration should still log how many passes occurred and whether the uplift justified the cost, otherwise agents silently become GPU multipliers.

Chain-of-thought prompting is not a decoding algorithm by itself, but it couples tightly with inference-time scaling: you allocate more generated tokens so the model can externalize intermediate steps before committing to an answer. That allocation is controlled by the same `max_new_tokens` and stop policies you configure for any other completion, so reasoning budgets are decoding budgets too. Reasoning-oriented training methods such as GRPO change the weight landscape; this module focuses on what you can do at serve time with a fixed checkpoint. For training recipes aimed at long reasoning traces, see [Module 1.12: Reasoning Models and GRPO](../module-1.12-reasoning-models-and-grpo/).

Use inference-time scaling selectively. A support bot answering FAQ lookups does not need five parallel reasoning rolls; a code-generation agent with executable tests might. Telemetry should record how many extra passes ran, their latency cost, and uplift on task-specific success metrics. Without that instrumentation, teams often enable best-of-N globally and wonder why GPU costs doubled while user-visible quality barely moved.

Self-consistency works best when answers pass through a discrete extractor: multiple choice, numeric results, or classification labels parsed from a final line. Free-form essays do not lend themselves to majority vote unless you define a similarity clustering step, which introduces its own hyperparameters. Best-of-N needs a verifier whose failures correlate with user pain. Executable unit tests, compiler errors, retrieval overlap scores, and schema validators are common verifiers in agent systems. Learned reward models can rank samples but inherit reward-model blind spots; treat them as one signal among several.

Chain-of-thought decoding budgets tokens for intermediate reasoning. Even without special training, many models become more reliable on multi-step math when allowed to produce scratch work before the final answer. The cost is latency and the risk of leaking scratch work to end users. Production UIs often hide reasoning traces while still storing them for debugging. If you train models with reasoning-specific reinforcement learning, decoding budgets and stop sequences should align with the format the model saw during training; otherwise the model may emit malformed reasoning tags that break downstream parsers.

## Watermarking and Provenance

Generated text can be misused for spam, astroturfing, and academic dishonesty. Watermarking embeds detectable statistical signals during decoding by skewing logits toward a pseudorandom greenlist of tokens derived from a secret key and prior context. Detection algorithms estimate whether the observed token distribution is improbably aligned with that greenlist structure. Because the bias is pseudorandom with respect to public text, casual readers should not rely on visual inspection; detection is a statistical test with configurable thresholds, not a highlighter for suspicious words. A detector with the key can estimate whether text likely came from a watermarked generator. Watermarks are not cryptographic proofs — paraphrasing attacks and translation can weaken them — but they provide a lightweight provenance channel for platforms that control both generation and auditing.

Operationally, watermarking is a decoding-time policy like temperature. It changes token probabilities, so quality and detectability trade off. Enterprise teams sometimes pair watermark metadata with broader content credentials and logging rather than relying on detection alone. Treat watermarking as one layer in a provenance stack, not a substitute for access control, human review, or policy enforcement.

Watermark strength is not monotonic. Aggressive greenlist bias can distort phrasing in ways users notice before detectors do, while weak bias may be invisible to users yet also invisible to detectors after light editing. If your product requires provenance, document whether detection is intended for automated moderation, forensic audit, or public-facing claims. Each use case implies different false-positive tolerance. Watermarks also interact with constrained decoding: grammar masks may shrink the feasible token set until watermark bias fights the grammar, so test both together rather than enabling them independently in separate tickets.

## Did You Know?

- **Nucleus sampling was proposed to fight degeneration**: Holtzman et al. showed that maximizing likelihood under greedy or beam search can yield surprisingly dull, repetitive text, and that adaptive nucleus filtering often produces more human-like variation without abandoning fluency.
- **Speculative decoding can be distribution-preserving**: When verification uses the target model's true conditional probabilities with the correct accept/reject rule, speculative decoding accelerates inference without changing the target model's mathematical sampling distribution.
- **Grammar-constrained decoding reduces parse failures**: Masking illegal tokens during generation is typically more reliable than generating free text and repairing syntax afterward, because repair heuristics cannot guarantee schema compliance under adversarial sampling noise.
- **Self-consistency trades compute for stability**: Wang et al. demonstrated that sampling diverse reasoning paths and taking a majority vote can improve multi-step reasoning benchmarks, which is one reason inference-time scaling reappears in agent systems even when base models are already large.

## Common Mistakes

| Mistake | Why it happens | How to fix |
|---------|----------------|------------|
| Using greedy decoding for creative long-form chat | Teams copy extraction settings into conversational products | Raise temperature modestly, enable top-p, and add repetition penalties tuned on real prompts |
| Applying beam search to open-ended dialogue | Legacy NLP habits from translation systems | Switch to nucleus sampling for subjective quality; reserve beam search for scored, constrained tasks |
| Ignoring decoding telemetry | Dashboards track model version but not sampling params | Log temperature, top-p, penalties, and seeds with each request ID for reproducibility |
| Expecting JSON mode to guarantee semantic correctness | Syntax and semantics are different validation layers | Add schema validation and application tests; constrain decoding for syntax, verify meaning separately |
| Turning repetition penalties too high | Aggressive settings look like a quick fix for loops | Increase gradually; pair with `max_tokens` and stop sequences instead of maxing penalties |
| Enabling speculative decoding without measuring acceptance | Draft models are exciting in blog posts | Benchmark acceptance rate and p95 latency under production concurrency before rolling out |
| Using best-of-N without a trustworthy verifier | Inference-time scaling sounds cheaper than training | Define a verifier correlated with user outcomes; otherwise you pay N× compute for noise |
| Confusing alignment training with decoding policy | Both affect user-visible text | Route alignment issues to fine-tuning or preference optimization; route repetitive or random tone to decoding knobs |

## Quiz

Test your understanding of advanced generation techniques.

<details>
<summary>1. A billing extraction service must return the same structured fields for the same invoice text every time. Which decoding setting is the best primary choice?</summary>

Use **greedy decoding** or **temperature near zero** with a grammar or schema constraint for the JSON fields. The workload prioritizes determinism and valid structure over creative variation, so stochastic sampling would introduce unnecessary run-to-run drift without user benefit.
</details>

<details>
<summary>2. An open-ended marketing copy assistant sounds repetitive and safe even though users expect fresh phrasing. The team already uses top-p=0.9. What should they adjust next?</summary>

Raise **temperature** slightly and add a **repetition or presence penalty** tuned on real prompts. Repetition often comes from locally greedy high-probability phrases, not from top-p alone. Evaluate diversity with human or automated metrics rather than a single example.
</details>

<details>
<summary>3. Why can beam search underperform nucleus sampling in casual chat even when beam search looks more "optimal"?</summary>

Beam search optimizes cumulative likelihood under a branching search, which favors safe, high-probability continuations. Casual chat rewards subjective engagement and variety, which stochastic **nucleus sampling** explores more naturally. Beam search remains useful when an external metric rewards overlap with references.
</details>

<details>
<summary>4. Speculative decoding proposes four tokens, but the target model rejects the third. What happens next?</summary>

The engine accepts the verified prefix up to the mismatch, then **resamples the rejected position from the normalized residual distribution** — the target distribution with the draft's already-proposed mass removed, `(p_target − p_draft)₊` renormalized. This preserves the target model's exact output distribution and prevents draft errors from permanently biasing the stream.
</details>

<details>
<summary>5. Your API returns valid JSON objects that frequently contain incorrect numeric totals. JSON mode is already enabled. What is the missing layer?</summary>

JSON mode enforces **syntax**, not **semantics**. Add downstream validation, calculators, or tool execution checks that verify totals against source data. Constrained decoding reduces parse errors but cannot ensure the model chose the right numbers.
</details>

<details>
<summary>6. A reasoning agent runs five chain-of-thought samples and picks the majority final answer. Which inference-time scaling technique is this?</summary>

This is **self-consistency decoding**: multiple stochastic reasoning paths followed by majority vote on the final outcome. It spends extra forward passes to reduce variance on fragile reasoning steps.
</details>

<details>
<summary>7. When should you reach for grammar-guided decoding instead of logit bias?</summary>

Use **grammar-guided decoding** when invalid tokens must never appear — for example SQL templates, configuration grammars, or nested JSON with strict nesting rules. **Logit bias** is better for soft nudges, such as encouraging yes/no tokens, not for guaranteeing syntax.
</details>

<details>
<summary>8. Support chat latency spikes even though prefill is fast. The deployment already uses a large target model. Name one decoding-level optimization and its main risk.</summary>

**Speculative decoding** with a smaller draft model can reduce decode latency by accepting multi-token prefixes after target verification. The main risk is low **acceptance rate**: a mismatched draft wastes verification compute and can even slow the system if not tuned.
</details>

## Hands-On Exercise: Compare Decoding Policies on the Same Prompt

In this exercise you run the same prompt through multiple decoding configurations and inspect how logits policies change repetition, length, and diversity. You need Python, PyTorch, and a small causal language model from Hugging Face Transformers.

### Success Checklist

- [ ] Install `transformers` and download a small causal LM (for example `gpt2` or another open model you are licensed to run).
- [ ] Generate at least three outputs with greedy decoding, nucleus sampling, and repetition penalty enabled.
- [ ] Record qualitative differences in repetition, tone, and length across configurations.
- [ ] Capture the exact `GenerationConfig` or keyword arguments used for each run.
- [ ] Write one sentence recommending which configuration fits a deterministic extractor vs a brainstorming assistant.

### Setup

```bash
python -m venv .venv-decode-lab
source .venv-decode-lab/bin/activate
pip install --upgrade pip
pip install torch transformers
```

### Script

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

MODEL_ID = "gpt2"
PROMPT = (
    "Write three bullet points explaining why decoding parameters matter "
    "in production LLM systems:"
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
inputs = tokenizer(PROMPT, return_tensors="pt")

configs = {
    "greedy": dict(do_sample=False, max_new_tokens=80),
    "nucleus": dict(do_sample=True, temperature=0.9, top_p=0.92, max_new_tokens=80),
    "anti_repeat": dict(
        do_sample=True,
        temperature=0.8,
        top_p=0.9,
        repetition_penalty=1.2,
        max_new_tokens=80,
    ),
}

set_seed(42)
for name, kwargs in configs.items():
    output_ids = model.generate(**inputs, pad_token_id=tokenizer.eos_token_id, **kwargs)
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    print(f"\n=== {name} ===\n{text}\n")
```

### Verification

Re-run the nucleus configuration with a different seed to confirm stochastic outputs change while greedy output stays identical:

```bash
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
MODEL_ID='gpt2'
PROMPT='Say hello in one creative sentence:'
tok=AutoTokenizer.from_pretrained(MODEL_ID)
mod=AutoModelForCausalLM.from_pretrained(MODEL_ID)
inp=tok(PROMPT, return_tensors='pt')
set_seed(1)
a=tok.decode(mod.generate(**inp, do_sample=True, temperature=0.9, top_p=0.9, max_new_tokens=20, pad_token_id=tok.eos_token_id)[0], skip_special_tokens=True)
set_seed(2)
b=tok.decode(mod.generate(**inp, do_sample=True, temperature=0.9, top_p=0.9, max_new_tokens=20, pad_token_id=tok.eos_token_id)[0], skip_special_tokens=True)
print('sample A:', a)
print('sample B:', b)
print('different:', a != b)
"
```

You should see `different: True` for stochastic settings on creative prompts, while greedy runs remain stable across seeds.

### Reflection prompts

Decide which configuration you would assign to a JSON invoice parser and which you would assign to a marketing brainstorming tool. Note that small public models exaggerate repetition; production models respond to the same knobs with different sensitivity, which is why tuning must happen on the target model and prompt distribution.

### Extending the experiment

Once the basic script works, extend it deliberately rather than tweaking random numbers. First, hold decoding fixed and change only the prompt length to see how repetition penalties interact with longer contexts. Second, add a JSON-only prompt such as "Return a JSON object with keys `risk` and `mitigation`" and compare free-form sampling against greedy decoding while measuring how often `json.loads` succeeds without repair. Third, log the first ten generated tokens' probabilities if your framework exposes logits, so you can see how sharply the distribution peaks under greedy vs nucleus settings.

Document results in a short table with columns for configuration, average output length, qualitative repetition score from one to five, and whether the output matches the task intent. This mirrors how platform teams evaluate decoding presets before promoting them from staging to production. The goal is not a perfect metric; the goal is a repeatable process that connects parameter changes to user-visible behavior.

If you have access to an OpenAI-compatible server with configurable `SamplingParams`, rerun a subset of tests through HTTP instead of local Transformers. The numerical knobs share names, but defaults differ, which is a common source of "works in notebook, drifts in prod" reports. Aligning names while misaligning defaults is worse than admitting two separate preset systems because teams assume equivalence and skip side-by-side tests.

## Next Module

Continue to [Module 1.6: LLM Evaluation](../module-1.6-llm-evaluation/) to learn how to measure whether your decoding and model choices actually improve outcomes in production, not just in a playground. Evaluation closes the loop opened here: decoding presets should be promoted or rolled back based on task-specific benchmarks, not intuition alone. Carry forward the habit of logging sampling parameters with every trace so evaluators can stratify failures by policy version instead of blaming the model checkpoint generically.

## Sources

- [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) — Introduces nucleus (top-p) sampling and explains why likelihood-maximizing decoding can yield repetitive, degenerate open-ended text.
- [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — Leviathan et al. draft-then-verify speculative decoding with distribution-preserving acceptance tests.
- [Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774) — Additional draft heads that propose multiple continuations for parallel verification.
- [EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077) — Feature-level speculative decoding that aligns draft predictions with target hidden states.
- [Efficient Guided Generation for Large Language Models](https://arxiv.org/abs/2307.09702) — Outlines paper on finite-state and grammar-guided generation for structured outputs.
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171) — Majority vote over multiple sampled reasoning paths at inference time.
- [Hugging Face: Generation strategies](https://huggingface.co/docs/transformers/generation_strategies) — Practical reference for greedy, sampling, beam search, and assisted generation APIs.
- [Hugging Face: Generation configuration](https://huggingface.co/docs/transformers/main_classes/text_generation) — Documents temperature, top-k, top-p, penalties, and stopping criteria on `GenerationConfig`.
- [vLLM: Sampling parameters](https://docs.vllm.ai/en/latest/dev/sampling_params.html) — Serving-side decoding parameters exposed by a widely used OpenAI-compatible inference engine.
- [llama.cpp: GBNF grammars](https://github.com/ggerganov/llama.cpp/blob/master/grammars/README.md) — Grammar notation used for constrained decoding in several local inference stacks.
- [A Watermark for Large Language Models](https://arxiv.org/abs/2301.10226) — Foundational greenlist watermarking approach embedded during decoding.
