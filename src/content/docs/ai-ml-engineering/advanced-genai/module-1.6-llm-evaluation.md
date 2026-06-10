---
title: "LLM Evaluation"
slug: ai-ml-engineering/advanced-genai/module-1.6-llm-evaluation
sidebar:
  order: 807
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6 Hours

> **Prerequisites**: RLHF & Alignment (module 1.4), generative-AI fundamentals, basic model evaluation, and comfort reading small Python data pipelines.

## Learning Outcomes

- **Diagnose** why LLM evaluation is harder than deterministic testing by separating open-ended quality, benchmark contamination, subjective judgment, and Goodhart-style metric gaming into distinct engineering risks.
- **Compare** capability benchmarks across knowledge, reasoning, code, and instruction-following tasks while explaining what each benchmark measures, what it omits, and why leaderboard results are not deployment guarantees.
- **Design** LLM-as-a-judge workflows that choose pairwise, pointwise, or reference-based grading intentionally, then reduce position, verbosity, and self-enhancement bias through swaps, rubrics, calibration, and human agreement checks.
- **Apply** statistical rigor to model comparisons using confidence intervals, paired tests, sample-size thinking, online A/B tests, and regression suites instead of relying on a few impressive examples.
- **Build** an evaluation pipeline that combines offline golden sets, RAG-specific checks, task-level agent evaluation, and CI or Kubernetes jobs so model changes are measured before and after production release.

## Why This Module Matters

Hypothetical scenario: a team ships a support assistant after it passes a few friendly prompts, a handful of static benchmark checks, and one demo in front of stakeholders. The first production week looks calm because the assistant answers simple questions fluently, but then customers begin asking ambiguous, multi-turn, domain-specific questions that were never represented in the demo set. The model sounds confident, follows the desired tone guide, and still gives subtly wrong answers whenever the policy text conflicts with the retrieved snippets.

The failure is not that the team forgot to run a test. The failure is that they confused easy-to-measure behavior with the behavior they actually needed. LLM evaluation is difficult because the object being measured is open-ended, multi-dimensional, and partly subjective. You care about correctness, helpfulness, calibration, faithfulness to retrieved context, instruction-following, latency, refusal behavior, cost, and regression risk at the same time. A single score cannot faithfully represent that whole surface.

Traditional software testing asks whether a deterministic program returned the expected output for a known input. LLM evaluation asks whether a probabilistic system produced an acceptable response for a distribution of possible tasks, users, policies, and contexts. That means you need test sets, rubrics, judges, statistics, human calibration, and production monitoring that reinforce each other instead of pretending that one leaderboard rank proves readiness.

Think of LLM evaluation like an aircraft instrument panel rather than a single speedometer. Airspeed matters, but so do altitude, heading, fuel, engine temperature, weather radar, and warnings from the ground. A pilot who watches only the fastest-moving needle is not being data-driven. They are ignoring the rest of the system. Good LLM evaluation gives you several imperfect instruments, teaches you what each instrument can and cannot see, and makes risky changes visible before users discover them.

The practical consequence is that evaluation must be designed backward from a decision. If the decision is "can we replace the current prompt," the eval needs paired comparisons against the current prompt on representative cases. If the decision is "can we expose this model to customers," the eval needs risk cases, latency checks, escalation behavior, and production monitoring. If the decision is "which retriever setting should we use," the eval needs retrieval diagnostics instead of only final answer scores.

A strong evaluation program therefore has two jobs. It must create enough evidence to support the immediate change, and it must leave behind artifacts that make the next change safer. Raw outputs, reviewed failures, rubric revisions, and confidence intervals are not bureaucracy. They are the memory of the system. Without them, every model upgrade becomes a new debate about taste, and every incident starts from the same vague question: why did our tests miss this?

This module focuses on evaluation. Red-teaming and prompt-injection attack design belong in [Module 1.7: AI Red Teaming](../module-1.7-ai-red-teaming/). Runtime guardrails, content moderation, jailbreak defense, and production safety controls belong in [Module 1.8: AI Safety & Alignment](../module-1.8-ai-safety-alignment/). Here, the central question is narrower and more foundational: how do you measure whether a model, prompt, retrieval system, or agentic workflow is actually improving?

## Why LLM Evaluation Is Hard

The first trap is open-endedness. A classifier can often be evaluated with a confusion matrix because each example has a small set of allowed labels. A chat model can answer the same question in many acceptable ways, and the correct answer may depend on tone, context, recency, user expertise, and local policy. Two responses can both be factually correct while one is too vague to be useful and the other is too detailed for the user's immediate need.

The second trap is multidimensional quality. A response can be safe but unhelpful, concise but incomplete, fluent but unsupported, or correct but too slow and expensive for the product. Evaluation therefore becomes a portfolio of measurements. You might measure exact match for a calculation task, code execution for a programming task, faithfulness for a RAG answer, rubric score for a support response, and latency or token cost for a serving path. None of those metrics replaces the others.

The third trap is emergence. A small prompt edit, model upgrade, retrieval chunking change, or tool schema update can improve one behavior while degrading another. LLM systems are often composed of multiple probabilistic stages, so the failure mode may come from the interaction between components rather than from one isolated model call. A retriever can surface the right document, the generator can ignore it, and the judge can still give a high score because the answer sounds polished.

The fourth trap is subjectivity. Human evaluators frequently disagree on style, helpfulness, and sufficiency, especially when the task has no single reference answer. LLM judges can scale evaluation, but they inherit their own biases and must be validated against human labels. Treating a judge model as an oracle is just another form of unmeasured automation risk.

Goodhart's Law is the name usually attached to a simple pattern: when a measure becomes the target, it can stop measuring the thing you care about. In LLM work, teams can over-optimize for a benchmark, a judge prompt, a refusal rate, or a public leaderboard while neglecting the messy production distribution. The cure is not to reject metrics. The cure is to use metrics as instruments, rotate and refresh them, hold back test data, examine failures qualitatively, and preserve room for human review.

There is also a granularity problem. A single conversation can contain retrieval, planning, factual synthesis, policy interpretation, tone control, and formatting. If you score only the final answer, you may miss which subskill changed. A model upgrade might improve synthesis while worsening instruction-following, or a new retriever might improve context recall while adding distracting chunks that reduce answer relevance. Useful evaluation decomposes the workflow enough that failures point toward an engineering action.

Static benchmarks are useful, but they age. Public benchmark items can leak into pretraining corpora, fine-tuning data, tutorials, GitHub repositories, and prompt examples. Even when contamination is accidental, it can make a model appear to generalize when it has partly memorized the exam. That is why durable evaluation programs mix public benchmarks with private golden sets, newly written tasks, adversarially perturbed examples, and production-derived samples that are reviewed before reuse.

Evaluation also has an uncomfortable social dimension. A model that wins a benchmark may not be the right model for your users, your latency budget, your compliance constraints, or your incident response process. Public scores are often measured under conditions that differ from your prompt format, decoding parameters, retrieval stack, tool access, and failure tolerance. The only trustworthy evaluation is the one that matches the decision you are actually making.

## Landscape Snapshot

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

| Family | Examples | What it is useful for | Main caveat |
|---|---|---|---|
| Knowledge and academic breadth | MMLU, MMLU-Pro, HELM scenarios | Broad coverage across subjects, tasks, and metrics | Public results can hide prompt sensitivity, contamination, and domain mismatch |
| Mathematical reasoning | GSM8K, MATH | Multi-step arithmetic or competition-style math reasoning | Correct final answers can mask brittle reasoning or benchmark familiarity |
| Code generation and repair | HumanEval, MBPP, SWE-bench | Function synthesis, test-passing code, and real repository issue resolution | Passing small tasks is not the same as maintaining a large production codebase |
| Instruction following | IFEval and similar verifiable-instruction suites | Objective checks for constraints such as format, length, and required terms | Verifiable constraints are narrower than real user satisfaction |
| Evaluation harnesses | lm-evaluation-harness, HELM, Ragas-style RAG evaluators | Repeatable offline runs, shared task adapters, and pipeline metrics | Harness results still depend on task design, model adapters, prompts, and statistical treatment |

This table is illustrative, not a leaderboard or endorsement. The stable lesson is not that any named benchmark is permanent. The stable lesson is that evaluation tools occupy different layers: broad capability probes, task-specific suites, judge-based preference tests, retrieval diagnostics, and production experiments. You choose the layer that matches the risk you are trying to reduce.

## Capability Benchmarks Without Leaderboard Theater

Capability benchmarks are controlled probes. They ask a model to perform a class of tasks under a specified format, then report a score that can be compared across systems. They are valuable because they create a shared vocabulary. Without them, every team would rely on anecdotes and marketing screenshots. With them, you can at least ask whether a change affects knowledge breadth, mathematical reasoning, code execution, or instruction-following under a repeatable protocol.

Knowledge benchmarks such as MMLU and MMLU-Pro probe broad academic and professional subject matter. MMLU covers many subjects, while MMLU-Pro was designed to make the task more challenging and reasoning-heavy. These benchmarks are useful when you need a rough signal of breadth, but they do not prove that a model understands your domain-specific policy, private schema, or current operating procedure. A high score on public multiple-choice questions does not mean the model will answer your internal support ticket correctly.

Reasoning benchmarks such as GSM8K and MATH focus on multi-step mathematical problem solving. They are helpful because reasoning failures are often invisible in fluent prose. A model can write a confident explanation and still make an arithmetic or algebraic error halfway through. These benchmarks measure specific distributions of math tasks, not general reliability. If your production task is financial analysis, logistics planning, or scientific calculation, you still need domain-specific examples with the units, constraints, and edge cases your system will face.

Code benchmarks illustrate another evaluation lesson: execution beats impression. HumanEval and MBPP use testable programming tasks, so the evaluator can run code rather than merely admire style. SWE-bench moves closer to real software engineering by asking systems to modify repositories in response to actual issue-style tasks. Even there, the benchmark is not your codebase. Real development involves architectural taste, compatibility constraints, flaky tests, security review, maintainability, and coordination with humans.

Instruction-following benchmarks such as IFEval are useful because some instructions are objectively checkable. If the prompt asks for more than a certain number of words, a required keyword, or a specific output structure, a deterministic checker can validate that constraint. This is especially valuable for production systems that must emit JSON, follow a policy format, or obey formatting rules. The limitation is that many real instructions are not so clean. "Be helpful but concise" is not the same as "mention this word three times."

Leaderboards become misleading when they are treated as procurement tools rather than measurement artifacts. A leaderboard score compresses a bundle of choices: model version, prompt template, few-shot examples, decoding settings, task implementation, contamination assumptions, and scoring logic. If any of those differ from your environment, the score may still be interesting, but it is no longer direct evidence for your release decision. Good evaluation asks what decision the score is supposed to support before deciding whether the score is relevant.

Benchmark gaming can happen without bad intent. Researchers and vendors naturally improve against visible tests because visible tests provide feedback. Over time, that feedback loop can shift effort toward the benchmark distribution. Private held-out sets, dynamic tasks, contamination checks, and fresh production samples help counteract this tendency. They are not perfect, but they make it harder for your evaluation program to become a memorized exam.

A practical benchmark taxonomy should include three labels for every suite you run. The first label is capability: what behavior is this suite trying to measure? The second is evidence strength: is the score deterministic, judge-based, human-rated, or a proxy? The third is decision fit: what product or engineering decision would change if this score moved? If you cannot answer the third question, the benchmark may be interesting research context but weak release evidence.

Capability benchmarks become more useful when they are paired with error buckets rather than reported only as totals. If a code model fails because it misunderstands the prompt, writes syntactically invalid code, chooses the wrong algorithm, or misses an edge case, each bucket suggests a different remedy. If a reasoning model fails because it performs the wrong operation, loses a constraint, or copies an intermediate error forward, the aggregate score alone is too blunt. Evaluation should produce engineering clues, not just applause or disappointment.

You should also distinguish capability from controllability. A model may be capable of solving a task when prompted carefully but unreliable when the prompt is embedded in your application. Capability asks whether the model can do the work under favorable conditions. Controllability asks whether your system can make it do the work consistently under production conditions. Most product failures happen in the gap between those two questions, so release suites need to evaluate the actual prompt, tool context, and retrieval wrapper rather than only the base model.

## LLM-as-a-Judge

LLM-as-a-judge evaluation uses a language model to score, compare, or critique outputs from another model or system. It exists because many important LLM tasks do not have exact reference answers. A customer-support answer, a summarization, or a troubleshooting explanation can be correct in multiple forms. Human review is valuable but slow and expensive, so automated judging can help teams run larger experiments more frequently.

There are three common judging modes. Pointwise judging asks the judge to score one answer against a rubric, such as factuality, completeness, tone, and instruction-following. Pairwise judging gives the judge two candidate answers for the same input and asks which is better. Reference-based judging supplies a gold answer, source context, policy excerpt, or checklist so the judge can compare the candidate against known evidence rather than relying only on preference.

Pointwise scoring is simple to aggregate, but it can be noisy because judges may use the scale inconsistently. Pairwise comparisons are often easier because choosing between two answers can be less ambiguous than assigning an absolute number. Reference-based judging is usually more grounded when reliable references exist, but it requires maintaining those references and ensuring they actually cover the question. None of the modes is universally superior; each answers a different evaluation question.

Judge bias is the central risk. Position bias occurs when a judge favors the first or second answer because of where it appears in the prompt. Verbosity bias occurs when a judge rewards length, polish, or extra caveats even when the shorter answer is more useful. Self-enhancement or self-preference bias occurs when a judge favors outputs that resemble its own model family, style, or policy habits. These biases are not hypothetical curiosities. They can change rankings if you do not design around them.

Concrete debiasing starts with position swapping. In pairwise evaluation, evaluate answer A before answer B, then repeat with the order reversed and aggregate the result. If the winner changes when positions change, mark the item as unstable or send it to a human. Next, anchor the rubric. Tell the judge exactly what matters, what does not matter, and how to handle ties. Penalize unsupported claims, unnecessary verbosity, and failure to use provided context. Keep the rubric short enough that the judge can apply it consistently.

Calibration is the validity check. Before trusting a judge, compare it against a small set of human-labeled examples that match your task. Measure agreement, inspect disagreements, and revise the rubric based on concrete failures rather than vibes. A judge that agrees with humans on generic chat preferences may still fail on your compliance-heavy support answers. The agreement set should include easy wins, close calls, bad hallucinations, partial answers, refusals, and examples where style conflicts with factuality.

Judge provenance matters as much as judge prompting. Record which judge model, prompt, rubric, temperature, reference context, and output schema produced each score. If the judge changes silently, your historical trend line becomes suspect. If the rubric changes, old and new scores may no longer be comparable. A mature pipeline treats judges as versioned measurement instruments. You can improve the instrument, but you must know when the instrument changed.

Human review should be used strategically rather than sprinkled randomly. Ask humans to label calibration sets, adjudicate close calls, review high-impact failures, and audit judge drift. Do not spend scarce expert attention on cases where deterministic checks already answer the question. Conversely, do not hide ambiguous or high-stakes cases behind an automated score simply because the pipeline can produce one. The point of automation is to focus human judgment where it has the highest value.

The following small example is intentionally runnable without API keys. It uses a deterministic mock judge so you can see the mechanics of a rubric, pairwise comparison, position swapping, and confidence intervals. In production, the `score_answer` function is where you would call an LLM judge with the same rubric and then validate that judge against human labels.

```python
from __future__ import annotations

from dataclasses import dataclass
from math import comb
from random import Random
from statistics import mean


@dataclass(frozen=True)
class EvalCase:
    prompt: str
    reference_terms: tuple[str, ...]
    risk_terms: tuple[str, ...]


CASES = [
    EvalCase(
        prompt="Explain why public benchmark scores are not enough for release.",
        reference_terms=("contamination", "domain", "regression"),
        risk_terms=("guarantee", "always safe"),
    ),
    EvalCase(
        prompt="Describe how to evaluate a RAG answer about an internal policy.",
        reference_terms=("faithfulness", "context", "relevance"),
        risk_terms=("use memory", "ignore sources"),
    ),
    EvalCase(
        prompt="Explain how to compare two prompt templates statistically.",
        reference_terms=("paired", "confidence", "sample"),
        risk_terms=("one example", "looks better"),
    ),
]

ANSWERS_A = [
    "A leaderboard is enough because it ranks the model against many peers.",
    "Ask a judge whether the answer sounds good and use the highest score.",
    "Try both prompts once, read the outputs, and keep the one that looks better.",
]

ANSWERS_B = [
    "Public benchmark scores help, but release evals also need contamination checks, domain-specific cases, and regression coverage for the actual workflow.",
    "A RAG eval should check faithfulness to retrieved context, answer relevance to the question, and whether the context was useful enough to support the response.",
    "Use the same cases for both prompt templates, compute paired deltas, report a confidence interval, and increase the sample when the interval is too wide.",
]


def score_answer(case: EvalCase, answer: str) -> tuple[int, list[str]]:
    text = answer.lower()
    score = 0
    notes: list[str] = []

    for term in case.reference_terms:
        if term in text:
            score += 2
            notes.append(f"uses expected concept: {term}")

    for term in case.risk_terms:
        if term in text:
            score -= 3
            notes.append(f"contains risky claim: {term}")

    word_count = len(text.split())
    if 18 <= word_count <= 55:
        score += 1
        notes.append("stays within the desired answer length")
    elif word_count > 75:
        score -= 1
        notes.append("too verbose for this rubric")

    return score, notes


def compare(case: EvalCase, left: str, right: str) -> int:
    left_score, _ = score_answer(case, left)
    right_score, _ = score_answer(case, right)
    if right_score > left_score:
        return 1
    if left_score > right_score:
        return -1
    return 0


def bootstrap_mean_delta(deltas: list[int], rounds: int = 2000) -> tuple[float, float]:
    rng = Random(7)
    means = []
    for _ in range(rounds):
        sample = [rng.choice(deltas) for _ in deltas]
        means.append(mean(sample))
    means.sort()
    return means[int(0.025 * rounds)], means[int(0.975 * rounds)]


def sign_test_p_value(deltas: list[int]) -> float:
    wins = sum(1 for delta in deltas if delta > 0)
    losses = sum(1 for delta in deltas if delta < 0)
    n = wins + losses
    if n == 0:
        return 1.0
    extreme = min(wins, losses)
    return min(1.0, 2 * sum(comb(n, k) * (0.5 ** n) for k in range(extreme + 1)))


deltas: list[int] = []
for case, answer_a, answer_b in zip(CASES, ANSWERS_A, ANSWERS_B):
    forward = compare(case, answer_a, answer_b)
    swapped = -compare(case, answer_b, answer_a)
    if forward != swapped:
        print("UNSTABLE POSITION EFFECT:", case.prompt)
        continue
    deltas.append(forward)
    print(case.prompt)
    print("  winner:", "B" if forward > 0 else "A" if forward < 0 else "tie")

low, high = bootstrap_mean_delta(deltas)
print("\npaired deltas:", deltas)
print("mean delta:", round(mean(deltas), 3))
print("95% bootstrap CI:", (round(low, 3), round(high, 3)))
print("sign-test p-value:", round(sign_test_p_value(deltas), 4))
```

The example is deliberately small: with these identical toy deltas the percentile bootstrap collapses to a zero-width interval, so the honest small-sample warning here is the conservative sign-test p-value, not the bootstrap CI. That is the point. A tiny eval can catch obvious regressions, but it cannot justify a sweeping release claim. Real judge pipelines need enough examples to cover the decision, enough disagreement analysis to detect judge failure, and enough statistical treatment to separate signal from noise.

## Statistical Rigor

The most dangerous sentence in LLM evaluation is "it looks better." Looking better is a useful observation, but it is not evidence by itself. A model can look better because you sampled easier prompts, changed decoding temperature, chose memorable examples, or inspected only the outputs that confirmed your expectation. Statistical rigor is how you keep evaluation from becoming a storytelling exercise.

Start with paired comparisons whenever possible. If you are comparing model A with model B, run both systems on the same evaluation items. The item-level difference matters more than the two aggregate scores in isolation because LLM tasks vary greatly in difficulty. A paired design asks whether B improved on the same questions where A struggled, not merely whether B happened to see a friendlier sample.

Report confidence intervals around the difference, not just around each system's score. If model A scores 74 percent and model B scores 76 percent, the question is not whether the numbers are different on the page. The question is whether the observed two-point delta is large compared with the uncertainty created by sample size, item mix, judge noise, and random decoding. Bootstrap intervals are practical because they resample evaluation items and estimate how much the measured delta moves under plausible resamples.

Use significance tests as guardrails against over-claiming. Paired bootstrap resampling, approximate randomization, and sign tests each make assumptions, but they all force the same discipline: compare item-level outcomes rather than cherry-picked examples. A statistically significant result is not automatically important, and a non-significant result is not automatically useless. It means the evidence is limited under the test you ran, so you should increase sample size, improve the eval design, or avoid claiming a reliable improvement.

Sample size is a product decision disguised as statistics. A low-risk copywriting prompt may tolerate a small eval because regressions are cheap to notice and repair. A compliance assistant, medical summarizer, or financial workflow needs a larger and more targeted suite because rare failures are costly. You do not need infinite examples. You need enough examples that the confidence interval around the decision is narrower than the smallest difference you would act on.

Regression suites protect you from accidental backsliding. Every time you fix a failure, add a representative case to the suite unless the case is sensitive or redundant. Keep separate splits for development and final release checks. If engineers tune prompts directly against the final release set, the release set becomes another training loop. That is benchmark contamination at team scale.

Power thinking helps you decide whether an eval is worth running before you run it. If your suite is so small that only enormous improvements can be detected, it may still be useful as a smoke test but weak as a comparison test. If your expected improvement is tiny, you need either more examples, lower-noise metrics, or a clearer decision threshold. Many teams skip this reasoning and then argue over ambiguous results that the experiment was never large enough to resolve.

Be explicit about practical significance. A statistically reliable one-point improvement may not justify higher latency, higher cost, or new operational risk. A statistically uncertain improvement may still justify a limited rollout if the downside is low and the online measurement plan is strong. The goal is not to worship p-values. The goal is to make the evidence, uncertainty, and tradeoffs visible enough that the release decision can be defended.

Online A/B testing answers a different question from offline evaluation. Offline eval asks whether a change behaves better on curated cases before release. A/B testing asks whether the change improves real user outcomes under controlled production traffic. For LLM systems, online metrics should include task success and user behavior, but also guardrail metrics such as escalation rate, latency, cost, refusal rate, and complaint patterns. Otherwise a model that sounds more confident can win the engagement metric while quietly increasing downstream risk.

Statistical rigor does not remove judgment. It makes judgment inspectable. When a team says "we are shipping because the new prompt improved faithfulness by eight points, the paired confidence interval excludes zero, no critical regressions appeared in the holdout suite, and the A/B guardrail metrics stayed within limits," the decision can be challenged and audited. When a team says "the demo felt much better," no one can tell whether the release was measured or merely persuasive.

## Evaluation Pipelines

An evaluation pipeline is the repeatable path from an input set to a release decision. It should record the prompt, model identifier, decoding settings, retrieval configuration, tool schema, dataset version, judge rubric, raw outputs, scores, confidence intervals, and reviewer notes. Without that provenance, you cannot reproduce a surprising result or explain why yesterday's model passed and today's model failed.

Offline evaluation is the first layer. It runs before production release and should be cheap enough to execute on every meaningful change. A small smoke suite catches broken JSON, prompt-template errors, missing tools, and obvious regressions. A larger release suite measures quality on a broader golden set. A specialized risk suite covers high-stakes edge cases such as contradictory context, insufficient evidence, ambiguous user intent, and instructions that should trigger escalation rather than confident guessing.

Golden sets are curated examples with expected behavior. They are not just random logs. Each case should include the user request, relevant context, expected answer shape, unacceptable answer patterns, and the reason the case exists. A good golden set is like a museum of failures the team has already paid to understand. It should grow from incidents, support escalations, human review, and domain-expert examples, but it must be deduplicated and periodically refreshed.

Harden the pipeline against accidental leakage. Developers need a development set for prompt iteration, a validation set for candidate comparison, and a held-out release set for final checks. If the same examples are repeatedly viewed, discussed, and tuned against, they stop measuring generalization. This is especially easy to miss in small teams because everyone remembers the hardest examples. Treat eval examples as test assets with ownership, change control, and review history.

Dataset governance is part of evaluation engineering. Each case should have a source, a review status, a sensitivity level, and a reason for inclusion. Production-derived examples may need redaction or synthetic rewriting before they enter a shared repository. Synthetic examples can be useful for coverage, but they should be marked as synthetic and periodically compared with real traffic. Otherwise the suite can drift toward neat artificial tasks that no longer resemble user behavior.

Release policies should be written before the result is known. Decide which failures block release, which failures require owner sign-off, which score drops trigger rollback, and which improvements are too small to matter. This prevents a familiar pattern where teams relax the gate after seeing a result they want to ship. Evaluation is strongest when the rule is agreed upon before the candidate system appears.

Use harnesses where they save work. An `lm-eval`-style harness standardizes model adapters, task loading, prompt formatting, and metric calculation. That consistency is valuable because subtle differences in prompts or decoding can change scores. Still, a harness cannot decide what your product values. It executes the measurement you define. The hard work remains task selection, rubric design, failure analysis, and release policy.

CI integration turns evaluation into a habit. A fast suite can run on pull requests that change prompts, routing rules, retrieval settings, or model configuration. A deeper suite can run nightly or before release. The output should fail loudly on schema breakage, critical regressions, and statistically meaningful drops. It should also store artifacts so reviewers can inspect raw model outputs rather than trusting only aggregate numbers.

In Kubernetes, batch evaluation usually maps cleanly to a `Job` or scheduled `CronJob`. The container reads a pinned dataset, calls the candidate model endpoint or local inference server, writes raw outputs to object storage, and publishes a compact report. The important point is reproducibility, not Kubernetes ceremony. Pin the image, dataset revision, model endpoint, prompt bundle, and judge configuration so the result can be rerun when a score changes unexpectedly.

Production monitoring is the final layer. Offline suites are curated, but users are creative. Log enough metadata to sample real failures without collecting unnecessary sensitive content. Review low-confidence answers, escalations, user corrections, and retrieval misses. Promote representative production failures into the golden set after privacy review. Evaluation is not a one-time gate; it is the feedback system that keeps the application honest as the world, the model, and the product change.

A useful report separates release summary from investigation detail. The summary should tell reviewers whether the candidate passed, where it improved, where it regressed, and what uncertainty remains. The detail should preserve raw examples, judge rationales, metric distributions, and failure labels. Leaders need the concise decision view, but engineers need the artifacts that explain how to fix the next failure. Both views should come from the same run.

## RAG and Agent Evaluation

RAG evaluation must separate retrieval quality from generation quality. If the answer is wrong, the retriever may have missed the right document, the reranker may have buried it, the generator may have ignored it, or the policy source may be ambiguous. A single "answer quality" score hides that diagnostic chain. Good RAG eval asks whether the retrieved context was relevant, whether it contained enough evidence, whether the answer stayed faithful to that evidence, and whether the response actually addressed the user's question.

Faithfulness measures whether the answer's claims are supported by the retrieved context. It is not the same as truth in the broad philosophical sense. A claim can be true in the world and still unfaithful if the provided context does not support it. This distinction matters because a RAG application often promises grounded answers. If the model uses unstated background knowledge when it should rely on policy text, the user loses the audit trail.

Answer relevance measures whether the response addresses the prompt. A faithful answer can still be irrelevant if it quotes the right document but misses the user's actual question. Context precision asks whether the retrieved chunks were useful rather than noisy. Context recall asks whether the system retrieved enough of the necessary evidence. Together, these metrics help localize whether you should tune chunking, embeddings, reranking, prompt instructions, or generation behavior.

RAG metrics should be paired with human review for high-stakes domains. Automated faithfulness checks can miss subtle contradictions, source ambiguity, and policy exceptions. Human reviewers can label why a case failed: missing document, stale document, retrieval mismatch, unsupported synthesis, over-refusal, or poor explanation. Those failure labels become more useful than a single score because they tell engineers where to intervene.

Agent evaluation adds another layer because the output is not only text. An agent may choose tools, call APIs, inspect files, execute code, ask clarifying questions, or stop early. Task-level success matters, but so do intermediate decisions. Did the agent select the right tool? Did it pass valid arguments? Did it recover from an error? Did it avoid unnecessary actions? Did it know when to ask for help? A final answer can look good while the trace reveals unsafe or wasteful behavior.

For agentic workflows, use scenario tests with observable success criteria. The evaluation case should define the starting state, available tools, user goal, forbidden actions, expected artifacts, and acceptable stopping conditions. Store the trace, not only the final message. A trace lets reviewers distinguish lucky success from reliable procedure. It also helps identify where a model upgrade changed behavior: planning, tool selection, argument formation, observation interpretation, or final synthesis.

The practical sequence is simple but demanding. First, define what good means for the workflow. Second, create cases that exercise common paths and known failure modes. Third, run candidates side by side on the same cases. Fourth, score with deterministic checks wherever possible and judge or human review where necessary. Fifth, analyze failures by component. Finally, promote the cases into CI so the next model, prompt, or retriever change cannot quietly reintroduce the same bug.

RAG and agent evaluations should include negative controls. A RAG system should be tested with questions whose answer is absent from the retrieved corpus so you can verify that it says it lacks evidence instead of inventing an answer. An agent should be tested with goals that require stopping, asking a clarifying question, or refusing an unsafe tool call. Negative controls keep the system from learning that every prompt deserves a confident completion.

The most useful failure reviews end with an owner and a next measurement. A retrieval miss might assign ownership to search tuning, a faithful but irrelevant answer to prompt design, an unsafe tool call to agent policy, and a judge disagreement to rubric calibration. Each fix should name the eval case that will prove it worked. That discipline closes the loop between measurement and engineering, which is the entire reason to evaluate in the first place.

## Did You Know?

- MMLU was introduced as a broad multitask benchmark spanning 57 subjects, which makes it useful for breadth checks but too general to validate a private product workflow by itself. A model can show strong academic coverage and still fail a narrow support, compliance, or troubleshooting task that depends on local policy details.
- MMLU-Pro was designed to make MMLU-style evaluation harder by adding more reasoning-focused questions and expanding multiple-choice options, which illustrates how benchmarks evolve after older formats become easier to optimize. This is a recurring pattern in LLM evaluation: useful tests attract optimization pressure, then harder or more targeted tests become necessary.
- IFEval focuses on verifiable instructions, such as length and keyword constraints, showing why some instruction-following behavior can be checked deterministically instead of judged by preference alone. That does not make IFEval a complete user-satisfaction measure; it makes it a useful instrument for one narrow class of objective constraints.
- RAGAS-style RAG metrics split evaluation into dimensions such as faithfulness, response relevance, and context precision, which helps engineers diagnose whether retrieval or generation caused a bad answer. The split matters because the same poor final response can come from missing evidence, noisy context, unsupported synthesis, or failure to answer the actual question.

## Common Mistakes

| Mistake | Why it happens | How to fix |
|---|---|---|
| Treating a leaderboard score as a release decision | Public benchmarks are visible, easy to cite, and more convenient than building a domain-specific suite. | Use public benchmarks for orientation, then require private golden sets, regression checks, and production-fit metrics before release. |
| Optimizing one judge score until it improves | A single rubric can become the target, especially when prompt changes are tuned against it repeatedly. | Rotate held-out cases, inspect raw outputs, calibrate against human labels, and track several metrics that expose tradeoffs. |
| Comparing models on different samples | Teams often run one model on a new batch and another on an old batch because it is operationally convenient. | Use paired evaluation on the same cases, then report item-level deltas and uncertainty around the difference. |
| Ignoring judge bias | LLM judges feel authoritative because they produce detailed explanations and numeric scores. | Use position swaps, concise rubrics, reference grounding, tie options, multiple judges when justified, and human agreement checks. |
| Letting the golden set leak into prompt tuning | Small teams remember every hard example and gradually overfit the prompt to those visible cases. | Split development, validation, and release sets, then restrict final-set access and refresh examples from reviewed production failures. |
| Scoring RAG as one black box | It is faster to ask whether the final answer was good than to diagnose retrieval and generation separately. | Measure context relevance, context precision or recall, answer faithfulness, and answer relevance as separate failure surfaces. |
| Shipping after offline eval only | Offline suites cannot fully represent real user behavior, traffic mix, or production latency constraints. | Follow offline gates with staged rollout, A/B testing, guardrail metrics, human review sampling, and rollback criteria. |

## Knowledge Check

<details>
<summary><strong>Question 1: A model upgrade improves a public knowledge benchmark by several points, but your support assistant's private policy suite is unchanged and the hallucination examples look slightly worse. Which learning outcome does this test, and what should you do?</strong></summary>

This tests your ability to compare capability benchmarks without treating them as deployment guarantees. The public benchmark is useful evidence about broad capability, but the private policy suite is closer to the release decision. You should inspect the regressions, compare paired item-level deltas, and avoid shipping solely because the public score improved.
</details>

<details>
<summary><strong>Question 2: Your pairwise LLM judge picks answer A when A appears first, then picks answer B when B appears first. What failure mode is showing up, and how should the pipeline respond?</strong></summary>

This is position bias or at least position instability. The pipeline should run position-swapped comparisons by default, aggregate only stable results, and route unstable cases to a human reviewer or a more grounded reference-based rubric. Forcing a winner from an unstable judge makes the evaluation look precise while hiding the actual uncertainty.
</details>

<details>
<summary><strong>Question 3: A RAG answer quotes the correct policy document but does not answer the user's question. Which RAG metric dimension catches this, and why is faithfulness alone insufficient?</strong></summary>

Faithfulness checks whether claims are supported by retrieved context, so the answer may be faithful and still unhelpful. Answer or response relevance catches whether the response addresses the prompt. This is why RAG evaluation separates retrieval usefulness, faithfulness to context, and relevance to the user request instead of collapsing everything into one score.
</details>

<details>
<summary><strong>Question 4: Two prompt templates differ by two percentage points on a 40-item evaluation set. The examples feel better, but the confidence interval around the paired delta crosses zero. What conclusion is justified?</strong></summary>

The justified conclusion is that the current evaluation does not provide strong evidence of a reliable improvement. The new prompt may still be promising, but you should avoid a broad claim, increase the sample size, improve the test distribution, or ship only behind a controlled rollout with guardrail metrics. The phrase "looks better" is not enough.
</details>

<details>
<summary><strong>Question 5: A team keeps editing its prompt until every example in the golden set passes, then uses that same set as the final release gate. What evaluation problem did they create?</strong></summary>

They contaminated their own release set. The golden set became part of the development feedback loop, so it no longer measures generalization. The fix is to split development, validation, and held-out release sets, limit access to the final gate, and refresh examples from reviewed production failures rather than tuning against the same visible cases forever.
</details>

<details>
<summary><strong>Question 6: Your agent succeeds on a task, but the trace shows it called an unnecessary tool, ignored an error message, and reached the right answer only because a later tool call happened to compensate. How should agent evaluation handle this?</strong></summary>

Agent evaluation should score the trace as well as the final answer. Task success is important, but reliable agents also need appropriate tool selection, valid arguments, error recovery, and safe stopping behavior. A lucky final answer should become a diagnostic case so future changes reward robust procedure rather than accidental success.
</details>

<details>
<summary><strong>Question 7: An executive asks for one number that summarizes whether the new model is safe to deploy. How can you answer without pretending that one metric captures everything?</strong></summary>

Use a release scorecard instead of one magic number. Include capability results, private golden-set deltas, judge-human agreement, RAG faithfulness and relevance, latency and cost, critical regression count, and online guardrail metrics if a staged rollout has started. The decision can still be concise, but the evidence should remain multi-dimensional.
</details>

## Hands-On Exercise

In this exercise, you will build a tiny evaluation harness that compares two candidate answer sets with a rubric, position-swapped pairwise judging, bootstrap confidence intervals, and a sign test. The goal is not to create a production judge. The goal is to practice the evaluation shape: same cases, explicit rubric, paired deltas, uncertainty, and an artifact you can rerun.

Create a scratch directory, then paste the script below. It uses only the Python standard library, so it should run in the project virtual environment without installing packages.

```bash
mkdir -p eval-lab
cd eval-lab
cat > llm_eval_lab.py <<'PY'
from __future__ import annotations

from dataclasses import dataclass
from math import comb
from random import Random
from statistics import mean


@dataclass(frozen=True)
class Case:
    name: str
    prompt: str
    must_include: tuple[str, ...]
    must_avoid: tuple[str, ...]


CASES = [
    Case(
        name="benchmark_limit",
        prompt="Why is a benchmark score not enough for release?",
        must_include=("domain", "contamination", "regression"),
        must_avoid=("guarantee", "proof of safety"),
    ),
    Case(
        name="rag_grounding",
        prompt="How should a policy RAG answer be evaluated?",
        must_include=("faithfulness", "context", "relevance"),
        must_avoid=("ignore", "memory alone"),
    ),
    Case(
        name="judge_bias",
        prompt="How do you reduce pairwise judge bias?",
        must_include=("position", "swap", "rubric"),
        must_avoid=("always trust", "single score"),
    ),
    Case(
        name="statistics",
        prompt="How do you compare two prompt templates?",
        must_include=("paired", "confidence", "sample"),
        must_avoid=("one example", "vibes"),
    ),
]


CANDIDATE_A = {
    "benchmark_limit": "A public score proves the model is ready because it was tested broadly.",
    "rag_grounding": "Read the final answer and decide whether it sounds useful to the user.",
    "judge_bias": "Ask the judge once and always trust the single score it returns.",
    "statistics": "Try one example and keep the prompt that has better vibes.",
}


CANDIDATE_B = {
    "benchmark_limit": "A benchmark score helps, but release evidence also needs domain cases, contamination awareness, and regression coverage.",
    "rag_grounding": "Evaluate faithfulness to the retrieved context, relevance to the question, and whether the context contains enough evidence.",
    "judge_bias": "Use a clear rubric, compare both position orders with a swap, and send unstable ties to human review.",
    "statistics": "Run both prompts on the same sample, compute paired deltas, and report a confidence interval before claiming improvement.",
}


def score(case: Case, answer: str) -> int:
    text = answer.lower()
    total = 0
    for term in case.must_include:
        if term in text:
            total += 2
    for term in case.must_avoid:
        if term in text:
            total -= 3
    words = len(text.split())
    if 14 <= words <= 40:
        total += 1
    return total


def judge_pair(case: Case, left: str, right: str) -> int:
    left_score = score(case, left)
    right_score = score(case, right)
    if right_score > left_score:
        return 1
    if left_score > right_score:
        return -1
    return 0


def bootstrap_ci(values: list[int], rounds: int = 3000) -> tuple[float, float]:
    rng = Random(42)
    means = []
    for _ in range(rounds):
        sample = [rng.choice(values) for _ in values]
        means.append(mean(sample))
    means.sort()
    return means[int(0.025 * rounds)], means[int(0.975 * rounds)]


def sign_test(values: list[int]) -> float:
    wins = sum(1 for value in values if value > 0)
    losses = sum(1 for value in values if value < 0)
    n = wins + losses
    if n == 0:
        return 1.0
    smaller_tail = min(wins, losses)
    return min(1.0, 2 * sum(comb(n, k) * (0.5 ** n) for k in range(smaller_tail + 1)))


def main() -> None:
    deltas: list[int] = []
    for case in CASES:
        answer_a = CANDIDATE_A[case.name]
        answer_b = CANDIDATE_B[case.name]
        forward = judge_pair(case, answer_a, answer_b)
        swapped = -judge_pair(case, answer_b, answer_a)
        stable = forward == swapped
        if stable:
            deltas.append(forward)
        print(f"{case.name}: winner={'B' if forward > 0 else 'A' if forward < 0 else 'tie'} stable={stable}")

    low, high = bootstrap_ci(deltas)
    print(f"paired_deltas={deltas}")
    print(f"mean_delta={mean(deltas):.3f}")
    print(f"bootstrap_95_ci=({low:.3f}, {high:.3f})")
    print(f"sign_test_p_value={sign_test(deltas):.4f}")


if __name__ == "__main__":
    main()
PY

../.venv/bin/python llm_eval_lab.py
```

The final command uses the project virtual environment from inside the scratch directory. The expected result is that candidate B wins the paired cases, the position-swapped comparison remains stable, and the statistical output reminds you that four examples are still too few for a broad release claim.

Now adapt the script for a real workflow you own or can imagine clearly. Replace the four cases with domain-specific examples, write the rubric terms that matter for each case, and add at least one intentionally close call where both candidates are partially acceptable. If the close call changes winner when you swap positions, mark it for human review rather than forcing the judge to choose.

Finally, sketch how this would run in CI. A pull request that changes prompts, retrieval settings, model routing, or tool schemas should run the smoke set and fail on schema errors or critical regressions. A nightly job can run the larger suite, write raw outputs and scores as artifacts, and compare candidate deltas against the current baseline. In Kubernetes, the same script can run as a batch Job with a pinned container image, mounted evaluation dataset, model endpoint secret, and artifact upload path.

### Success Checklist

- [ ] The script runs with `.venv/bin/python` or `../.venv/bin/python` and prints a winner for each evaluation case without installing third-party packages.
- [ ] Each case uses the same prompt for both candidates so the comparison is paired rather than two unrelated aggregate scores.
- [ ] The judge applies an explicit rubric with required concepts and risky claims instead of relying on generic preference language.
- [ ] The pairwise comparison is evaluated in both answer orders so obvious position sensitivity can be detected before aggregation.
- [ ] The final output reports paired deltas, a bootstrap confidence interval, and a sign-test p-value so uncertainty is visible.
- [ ] Your adapted suite includes at least one close-call case that would be reasonable to send to human review if the judge is unstable.

## Next Module

Now that you can measure model behavior with benchmarks, judges, statistics, and production-aware pipelines, the next step is to intentionally search for failure modes. Continue with [Module 1.7: AI Red Teaming](../module-1.7-ai-red-teaming/) to learn how adversarial testing complements evaluation without replacing it.

## Sources

- [Measuring Massive Multitask Language Understanding](https://arxiv.org/abs/2009.03300) — Establishes MMLU as a broad multitask benchmark and documents its subject coverage.
- [MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark](https://arxiv.org/abs/2406.01574) — Explains why harder, reasoning-focused variants emerged after older benchmark formats became less discriminative.
- [Training Verifiers to Solve Math Word Problems](https://arxiv.org/abs/2110.14168) — Introduces GSM8K and motivates verifier-style reasoning evaluation for math word problems.
- [Measuring Mathematical Problem Solving With the MATH Dataset](https://arxiv.org/abs/2103.03874) — Provides the MATH benchmark context for competition-style mathematical reasoning evaluation.
- [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374) — Introduces HumanEval and the idea of execution-based code-generation evaluation.
- [Program Synthesis with Large Language Models](https://arxiv.org/abs/2108.07732) — Introduces MBPP and supports the code-benchmark taxonomy used in the snapshot.
- [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770) — Grounds the discussion of repository-level software engineering evaluation.
- [Instruction-Following Evaluation for Large Language Models](https://arxiv.org/abs/2311.07911) — Defines IFEval and its focus on objectively verifiable instruction constraints.
- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) — Documents LLM-as-a-judge methods, human agreement checks, and judge bias categories.
- [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926) — Provides evidence and mitigation ideas for position bias in LLM judge comparisons.
- [Holistic Evaluation of Language Models](https://arxiv.org/abs/2211.09110) — Motivates multi-metric evaluation across accuracy, calibration, robustness, fairness, bias, toxicity, and efficiency.
- [Recent Advances in Large Language Model Benchmarks against Data Contamination](https://arxiv.org/abs/2502.17521) — Surveys static benchmark contamination risks and dynamic evaluation responses.
- [Goodhart's Law Applies to NLP's Explanation Benchmarks](https://aclanthology.org/2024.findings-eacl.88/) — Shows how optimizing benchmark metrics can produce misleading progress signals.
- [Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) — Provides the upstream harness example for repeatable offline benchmark execution.
- [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) — Introduces reference-free RAG evaluation concepts such as faithfulness and answer relevance.
- [Ragas Faithfulness Metric](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/) — Documents faithfulness as consistency between generated responses and retrieved context.
- [Ragas Context Precision Metric](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/) — Documents context precision as a way to judge whether retrieved contexts are useful.
- [Ragas Response Relevancy Metric](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/) — Documents response relevance as a RAG answer-quality dimension.
- [Randomized Significance Tests in Machine Translation](https://aclanthology.org/W14-3333/) — Supports paired bootstrap and approximate randomization as practical significance-test approaches for NLP evaluation.
- [Controlled Experiments on the Web: Survey and Practical Guide](https://robotics.stanford.edu/~ronnyk/2009controlledExperimentsOnTheWebSurvey.pdf) — Grounds the online A/B testing discussion in controlled-experiment practice.
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) — Documents the batch Job primitive referenced for running repeatable evaluation workloads in clusters.
