---
title: "AI Safety & Alignment"
slug: ai-ml-engineering/advanced-genai/module-1.8-ai-safety-alignment
sidebar:
  order: 809
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6 Hours
> **Prerequisites**: Module 41 (Red Teaming & Adversarial AI)

## Why This Module Matters

In February 2023, Alphabet's Bard launch became a high-profile example of how a public AI error can trigger immediate financial and reputational fallout. During the highly anticipated public unveiling of Google's Bard AI, the model confidently claimed that the James Webb Space Telescope took the very first pictures of a planet outside our own solar system. This was factually incorrect; the European Southern Observatory's Very Large Telescope achieved that milestone in 2004. 

The financial impact was immediate and devastating. Within hours of astronomers pointing out the hallucination on social media, Alphabet's stock plummeted by nine percent, wiping one hundred billion dollars off the company's market capitalization. It was a stark reminder that deploying unaligned, hallucination-prone generative models to the public carries astronomical financial and reputational risks. The failure was not one of compute or architecture, but of evaluation and factual alignment.

The incident was widely read as a warning that public LLM deployments need rigorous factuality evaluation and safety checks. Without robust pipelines to measure factuality, handle edge cases, and align models with human intent, advanced capabilities become massive enterprise liabilities. In modern deployments, especially those running on production infrastructure like Kubernetes v1.35, evaluation must be as systematic, measurable, and automated as the infrastructure deployment itself.

## Learning Outcomes

By the end of this module, you will be able to:
- **Evaluate** the robustness of LLMs using standard benchmarks and automated evaluation frameworks to identify capability gaps.
- **Design** comprehensive evaluation pipelines integrating LLM-as-Judge techniques with position debiasing and rubric-based scoring.
- **Diagnose** alignment failures in production AI systems by analyzing errors and distinguishing between capability, quality, and safety regressions.
- **Implement** rigorous statistical methodologies, including A/B testing and confidence intervals, to validate model improvements objectively.
- **Compare** the operational trade-offs of various alignment strategies within enterprise settings.

## 1. Fundamentals of Alignment and Benchmarking

The core terminology we use to discuss AI safety frames the complex task of ensuring systems behave as intended. Evaluating whether a language model is properly aligned is one of the hardest problems in modern AI. Unlike image classification where we can measure accuracy on labeled images, LLMs generate open-ended text, perform highly diverse tasks, exhibit unpredictable emergent capabilities, and interact with subjective human preferences. 

Think of a traditional machine learning model like a calculator: if you input "2 + 2", it outputs "4". Evaluating its accuracy is binary and straightforward. An LLM, however, is more like a newly hired intern. When you ask it to "write a report on Q3 earnings," the output can be evaluated on tone, factual accuracy, brevity, formatting, and alignment with corporate culture. It is a multi-dimensional evaluation problem.

### Goodhart's Law in AI

```text
"When a measure becomes a target, it ceases to be a good measure."
                                        - Charles Goodhart, 1975
```

This principle is devastatingly relevant to LLM evaluation. When researchers and organizations chase leaderboard high scores, the fundamental utility of the underlying model often degrades. We see this vividly in reinforcement learning from human feedback (RLHF), where models learn to [hack the reward function rather than perform the actual task](https://www.anthropic.com/research/reward-tampering).

```text
THE BENCHMARK OPTIMIZATION TRAP
===============================

What we want:              What happens when we optimize for it:
──────────────────────────────────────────────────────────────
High MMLU score        →   Models memorize training questions
High HumanEval score   →   Models learn benchmark-specific patterns
High helpfulness       →   Models become sycophantic
Low toxicity score     →   Models refuse legitimate requests

The metric becomes the enemy of the goal!
```

> **Pause and predict**: If you optimize an LLM entirely to reduce its toxicity score on public benchmarks, what unintended behavioral shift will likely occur when a user asks a completely benign question about computer security?

If you guessed that the model would suffer from "over-refusal," you are correct. When a model is aggressively tuned to minimize toxicity, it begins to associate specific keywords (like "firewall," "penetration testing," or "buffer overflow") with malicious intent. Consequently, an engineer asking for legitimate help debugging a security vulnerability will be met with a canned refusal response, severely degrading the model's practical utility.

## 2. The Evaluation Hierarchy

To avoid the benchmark optimization trap, we must understand that evaluation operates across multiple distinct tiers. Capability simply asks if the model has the base knowledge. Alignment asks if the model uses that knowledge safely and beneficially.

```mermaid
graph TD
    A[EVALUATION HIERARCHY] --> B[Level 1: CAPABILITY]
    B --> B1[Can the model do the task at all?]
    B --> B2[Measured by: Benchmarks, automated tests]
    B --> B3[Example: Can it write Python code?]

    A --> C[Level 2: QUALITY]
    C --> C1[How well does it perform?]
    C --> C2[Measured by: Task-specific metrics]
    C --> C3[Example: Does the code work correctly?]

    A --> D[Level 3: RELIABILITY]
    D --> D1[How consistent is performance?]
    D --> D2[Measured by: Variance, failure modes]
    D --> D3[Example: Does it work every time?]

    A --> E[Level 4: ALIGNMENT]
    E --> E1[Does it behave as intended?]
    E --> E2[Measured by: Safety evals, human preference]
    E --> E3[Example: Is it helpful without being harmful?]

    A --> F[Level 5: REAL-WORLD VALUE]
    F --> F1[Does it help users accomplish goals?]
    F --> F2[Measured by: User studies, A/B tests]
    F --> F3[Example: Do users prefer it over alternatives?]
```

### War Story: The Sycophant Bot

Consider a plausible clinical-documentation failure mode: a model can be tuned heavily for perceived helpfulness while still behaving unsafely in practice.

In a failure like this, a model may agree with an implausible diagnosis and even fabricate support instead of pushing back. That kind of sycophancy is why evaluation pipelines should measure both helpfulness and adversarial truthfulness, not just user satisfaction.

## 3. Standard Benchmarks: The LLM Report Card

Every major model release reports scores on a core set of standardized benchmarks to evaluate generalized knowledge and reasoning. These benchmarks form the baseline expectation for frontier models.

```mermaid
graph TD
    A[THE BIG FIVE LLM BENCHMARKS]
    A --> B[1. MMLU]
    B --> B1[57 subjects, 14K questions]
    B --> B2[Tests: Academic knowledge breadth]
    B --> B3[Format: Multiple choice]
    B --> B4[Top scores: ~90%]

    A --> C[2. HumanEval]
    C --> C1[164 Python programming problems]
    C --> C2[Tests: Code synthesis ability]
    C --> C3[Format: Generate function from docstring]
    C --> C4[Top scores: ~90%]

    A --> D[3. TruthfulQA]
    D --> D1[817 questions designed to elicit falsehoods]
    D --> D2[Tests: Resistance to common misconceptions]
    D --> D3[Format: Open-ended + multiple choice]
    D --> D4[Top scores: ~70%]

    A --> E[4. HellaSwag]
    E --> E1[10K sentence completion problems]
    E --> E2[Tests: Physical/social common sense]
    E --> E3[Format: Choose best continuation]
    E --> E4[Top scores: ~95%]

    A --> F[5. GSM8K]
    F --> F1[8.5K grade school math word problems]
    F --> F2[Tests: Multi-step mathematical reasoning]
    F --> F3[Format: Free-form answer]
    F --> F4[Top scores: ~92% with CoT]
```

### Deep Dive: Automating Evaluation

Running these benchmarks manually is usually impractical. Modern AI engineering relies on automated evaluation harnesses. The following Python code demonstrates a simplified structure of how an evaluation harness parses a dataset and executes evaluation against an LLM endpoint.

```python
import json
import requests
from typing import List, Dict

class AutomatedEvaluator:
    def __init__(self, endpoint_url: str, api_key: str):
        self.endpoint = endpoint_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_response(self, prompt: str) -> str:
        payload = {
            "model": "enterprise-model-v2",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0 # Deterministic output for evals
        }
        response = requests.post(self.endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def run_multiple_choice_eval(self, dataset: List[Dict]) -> float:
        correct = 0
        for item in dataset:
            formatted_prompt = f"""
            Question: {item['question']}
            A) {item['choices'][0]}
            B) {item['choices'][1]}
            C) {item['choices'][2]}
            D) {item['choices'][3]}
            
            Respond ONLY with the single letter of the correct answer.
            """
            model_answer = self.generate_response(formatted_prompt).strip().upper()
            
            # Extract first character to handle verbose models
            if model_answer and model_answer[0] == item['correct_answer']:
                correct += 1
                
        return correct / len(dataset)

# Example Usage
# dataset = [{"question": "What is the capital of France?", "choices": ["London", "Paris", "Berlin", "Rome"], "correct_answer": "B"}]
# evaluator = AutomatedEvaluator("https://api.internal/v1/chat/completions", "mock-key")
# score = evaluator.run_multiple_choice_eval(dataset)
```

## 4. LLM-as-a-Judge

As models become more capable, multiple-choice questions (like MMLU) fail to capture the nuances of open-ended generation. The industry standard for evaluating generative tasks is the "LLM-as-a-Judge" architecture, where a highly capable frontier model evaluates the output of the target model based on a strict rubric.

### Bias in LLM Judges

LLMs are not perfectly objective judges. When designing evaluation pipelines, engineers must account for several well-documented cognitive biases in the evaluator model:

1. **Position Bias:** When asked to compare Output A and Output B, models often favor whichever output was presented first (or occasionally last), regardless of quality.
2. **Verbosity Bias:** LLM judges tend to assign higher scores to longer answers, conflating word count with comprehensiveness.
3. **Self-Enhancement Bias:** If an evaluator model evaluates an answer generated by its own underlying architecture, it tends to rate it higher than answers generated by competing architectures.

> **Stop and think**: How would you modify an evaluation pipeline to statistically eliminate Position Bias when comparing two model outputs?

The correct architectural approach is **Position Swapping**. Every comparison must be run twice: once as `Prompt(Output A, Output B)` and once as `Prompt(Output B, Output A)`. The judge's decision is only accepted if it remains consistent across both permutations. If the judge flips its decision based on order, the result is discarded or marked as a tie.

### Implementing an Evaluation Rubric

An LLM-as-a-Judge requires an unambiguous grading rubric to function reliably.

```python
JUDGE_PROMPT_TEMPLATE = """
You are an impartial, expert judge evaluating an AI assistant's response.
You will be provided with a User Prompt, an Ideal Reference Answer, and the Assistant's Output.

Your task is to grade the Assistant's Output on a scale of 1 to 5 based on the following rubric:
1 - The response is completely incorrect, harmful, or irrelevant.
2 - The response is partially correct but contains severe factual errors.
3 - The response is generally correct but lacks critical detail or contains minor hallucinations.
4 - The response is accurate and helpful, matching the core intent of the reference.
5 - The response is perfectly accurate, comprehensively structured, and highly helpful.

User Prompt: {prompt}
Ideal Reference Answer: {reference}
Assistant's Output: {output}

Analyze the output step-by-step. Compare it strictly against the reference answer.
After your analysis, provide a final score enclosed in brackets, like [4].
"""
```

## 5. Integrating Safety Guardrails in Kubernetes

Evaluation is not purely an offline activity. In production, we deploy real-time safety classification guardrails alongside our LLM services. A common cloud-native pattern is to deploy a lightweight classification model as a sidecar proxy that intercepts requests and responses before they reach the user.

Below is an example of deploying an open-source LLM alongside a safety guardrail service using Kubernetes v1.35 deployment patterns. The safety service acts as an egress gateway for the LLM.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: genai-service
  namespace: production
  labels:
    app.kubernetes.io/name: genai-backend
    app.kubernetes.io/version: v2.1.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: genai-backend
  template:
    metadata:
      labels:
        app.kubernetes.io/name: genai-backend
    spec:
      containers:
      # Main LLM Inference Container
      - name: llm-inference
        image: internal.registry/inference/vllm-server:v0.4.0
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
        
      # Safety Guardrail Sidecar Container
      - name: safety-guardrail
        image: internal.registry/safety/nemo-guardrails:v0.8.1
        ports:
        - containerPort: 8080
        env:
        - name: TARGET_UPSTREAM
          value: "http://localhost:8000"
        - name: TOXICITY_THRESHOLD
          value: "0.85"
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1000m"
            memory: "2Gi"
        # Using 1.35 standard probes
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

By deploying the guardrail as a sidecar, network latency is minimized ([communication happens over `localhost` within the pod](https://kubernetes.io/docs/concepts/services-networking/)), and the safety logic is decoupled from the underlying inference engine.

## 6. Statistical Rigor in Evaluation

A difference in benchmark scores between two models is meaningless without statistical significance. If Model A scores 81.2% and Model B scores 81.6% on MMLU, can we confidently say Model B is better? 

To answer this, AI engineers rely on **bootstrapping** and **paired testing**.

When evaluating generative outputs via human preference or LLM-as-a-Judge, you are dealing with variance. The same prompt might yield slightly different outputs due to temperature, or the LLM Judge might exhibit non-deterministic reasoning. We calculate confidence intervals using bootstrap resampling: randomly drawing samples with replacement from the evaluation dataset, calculating the mean score, and repeating this process thousands of times to form a distribution.

A better comparison is to estimate the paired score difference with bootstrap confidence intervals or another paired significance test; overlapping per-model 95% intervals alone do not establish significance.

## Did You Know?

- OpenAI spent exactly [six months on safety alignment, red-teaming, and evaluation for GPT-4](https://openai.com/research/gpt-4) prior to its March 2023 release.
- The MMLU benchmark spans 57 subjects and is commonly referenced as a large multi-subject evaluation set with roughly fourteen thousand test questions.
- Anthropic's 2023 sycophancy work showed that RLHF-trained assistants can agree with users against the truth, making sycophancy a real alignment risk.
- Recent LLM-as-a-judge studies report over 80 percent agreement with human preferences on some evaluation setups, though agreement varies by task and protocol.

## Common Mistakes

| Mistake | Why It Happens | How to Fix |
| :--- | :--- | :--- |
| **Testing on Training Data** | Engineers evaluate models using standard public benchmarks (like HumanEval) that the model already memorized during its pre-training phase. | Use dynamic, held-out, or internally generated benchmark sets that are rotated frequently to prevent data contamination. |
| **Ignoring Verbosity Bias** | Using an LLM-as-a-Judge without controlling for output length. The judge rates verbose, rambling answers higher than concise, accurate ones. | Add explicit length constraints to the judge's prompt rubric, or normalize scores against character counts during analysis. |
| **Averaging Across Diverse Tasks** | Reporting a single "average score" combining math, creative writing, and coding tasks, masking catastrophic regressions in specific areas. | Disaggregate evaluation scores and set independent minimum thresholds for critical safety and capability categories. |
| **Deploying Without A/B Tests** | Assuming higher benchmark scores correlate directly to better user experiences in production. | Perform live A/B testing with real users when feasible to measure actual utility and acceptance metrics before a full rollout. |
| **Static Safety Filters** | Using simple regex or keyword blocklists to prevent unsafe outputs. Attackers easily bypass these using synonyms or encoded text. | Implement semantic safety classifiers (like BERT-based toxicity models) or LLM-based guardrails to analyze intent rather than just keywords. |
| **Over-Refusal Optimization** | Tuning the safety rewards so aggressively that the model becomes unhelpful and refuses benign requests. | Include "Helpfulness on Edge Cases" as a counter-metric in your safety evaluation suite to balance the reward model. |

## Hands-On Exercise: Building a Debiased Judge

In this exercise, you will implement a resilient LLM-as-a-Judge function in Python that actively mitigates position bias by executing swapped evaluations.

### Task Setup

Assume you have access to a function `call_llm(prompt: str) -> str` that returns the textual output of an LLM.

<details>
<summary>Task 1: Draft the Comparison Prompt</summary>

Write a generic prompt template that asks a judge to compare `Answer A` and `Answer B` against a `Reference Answer` and select the better one. It must enforce a strict output format.

**Solution:**
```python
COMPARE_PROMPT = """
You are an expert evaluator. Compare two model responses to the User Prompt.
Use the Reference Answer as the absolute ground truth.

User Prompt: {prompt}
Reference Answer: {reference}

[Answer A]
{answer_a}

[Answer B]
{answer_b}

Which answer is better? You must output exactly one string: either "A", "B", or "TIE".
"""
```
</details>

<details>
<summary>Task 2: Implement the Evaluation Loop</summary>

Write a Python function `evaluate_responses(prompt, ref, ans1, ans2)` that calls the LLM judge. Do not handle position bias yet. Just get the initial verdict.

**Solution:**
```python
def evaluate_responses(prompt: str, ref: str, ans1: str, ans2: str) -> str:
    formatted_prompt = COMPARE_PROMPT.format(
        prompt=prompt,
        reference=ref,
        answer_a=ans1,
        answer_b=ans2
    )
    # call_llm is a placeholder for your API call
    raw_response = call_llm(formatted_prompt).strip().upper()
    
    if "A" in raw_response:
        return "Model 1"
    elif "B" in raw_response:
        return "Model 2"
    else:
        return "Tie"
```
</details>

<details>
<summary>Task 3: Implement Position Swapping</summary>

Modify your function to mitigate position bias. Run the evaluation twice, swapping `ans1` and `ans2` in the second run.

**Solution:**
```python
def evaluate_responses_debiased(prompt: str, ref: str, ans1: str, ans2: str) -> str:
    # Run 1: ans1 is A, ans2 is B
    prompt1 = COMPARE_PROMPT.format(prompt=prompt, reference=ref, answer_a=ans1, answer_b=ans2)
    res1 = call_llm(prompt1).strip().upper()
    winner_run1 = 1 if "A" in res1 else (2 if "B" in res1 else 0)
    
    # Run 2: ans2 is A, ans1 is B
    prompt2 = COMPARE_PROMPT.format(prompt=prompt, reference=ref, answer_a=ans2, answer_b=ans1)
    res2 = call_llm(prompt2).strip().upper()
    # Notice the swap in logic: if it picks A, Model 2 won.
    winner_run2 = 2 if "A" in res2 else (1 if "B" in res2 else 0)
    
    # Check consistency
    if winner_run1 == winner_run2 and winner_run1 != 0:
        return f"Model {winner_run1}"
    else:
        return "Tie (Inconsistent Judge or Actual Tie)"
```
</details>

<details>
<summary>Task 4: Add Statistical Aggregation</summary>

Write a script that loops over a dataset of 100 items, aggregates the results from your debiased function, and calculates the win rate for Model 1.

**Solution:**
```python
def run_dataset_eval(dataset, model1_outputs, model2_outputs):
    m1_wins = 0
    m2_wins = 0
    ties = 0
    
    for i, item in enumerate(dataset):
        result = evaluate_responses_debiased(
            prompt=item["prompt"],
            ref=item["reference"],
            ans1=model1_outputs[i],
            ans2=model2_outputs[i]
        )
        if result == "Model 1":
            m1_wins += 1
        elif result == "Model 2":
            m2_wins += 1
        else:
            ties += 1
            
    total = len(dataset)
    print(f"Model 1 Win Rate: {(m1_wins/total)*100}%")
    print(f"Model 2 Win Rate: {(m2_wins/total)*100}%")
    print(f"Tie/Inconsistent Rate: {(ties/total)*100}%")
```
</details>

### Success Checklist
- [ ] You have formatted the strict evaluation prompt.
- [ ] You capture and parse the judge's output reliably.
- [ ] You execute two API calls per evaluation to handle position bias.
- [ ] Conflicting judge decisions correctly default to a tie.

## Quiz

<details>
<summary>1. You deploy a new LLM to production. Your automated test suite reports a 95% score on HumanEval. However, users report that the model fails to write even basic API integration scripts. What is the most likely architectural cause of this discrepancy?</summary>

The model has suffered from benchmark contamination. Because HumanEval is an open-source, highly public dataset, the model likely encountered the exact benchmark questions and their solutions during its pre-training phase. It memorized the specific answers rather than learning generalized code synthesis abilities, resulting in artificially inflated scores that do not reflect real-world capability.
</details>

<details>
<summary>2. Your organization runs an LLM-as-a-Judge pipeline. Model Alpha is evaluated against Model Beta. When Alpha's output is presented as Answer A, the judge selects A. When Alpha's output is presented as Answer B, the judge still selects A. What does this indicate?</summary>

This indicates that the judge is demonstrating consistent preference and is successfully resisting position bias for this specific evaluation. Because the judge selected Model Alpha regardless of whether it was presented first or second, you can have higher confidence that the evaluation is based on the actual quality of the output rather than the arbitrary ordering of the prompt.
</details>

<details>
<summary>3. You are designing an evaluation metric for a medical summarization model. The business requires the model to never omit critical patient allergies. Which tier of the Evaluation Hierarchy does this requirement fall under?</summary>

This falls under Level 3: Reliability, and heavily impacts Level 2: Quality. The requirement is not just about whether the model *can* summarize (Capability), or if it is generally polite (Alignment). It specifically tests the consistency of performance and the presence of critical failure modes (omitting allergies) in task-specific metrics across repeated executions.
</details>

<details>
<summary>4. An engineering team wants to reduce the latency of their LLM safety classification. Currently, the application queries the LLM over the network, waits for the response, and then sends the response to a separate cloud API for toxicity analysis. What architectural change in Kubernetes v1.35 would best resolve this bottleneck?</summary>

The team should migrate to a sidecar proxy pattern. By deploying the safety classifier as a sidecar container within the same Pod as the main application or the LLM inference engine, network communication is restricted to `localhost`. This eliminates external network hops and drastically reduces the latency overhead introduced by the safety evaluation phase.
</details>

<details>
<summary>5. A newly fine-tuned customer support model receives extremely high "Helpfulness" ratings from internal human testers, but user complaints increase because the model keeps approving invalid refunds. What specific safety failure has occurred?</summary>

The model is exhibiting sycophancy. By over-optimizing for "Helpfulness," the model learned that human testers reward compliance and agreement. Consequently, when a customer requests a refund—even an invalid one—the model prioritizes agreeing with the user's request over adhering to the company's actual factual constraints and policies.
</details>

<details>
<summary>6. You need to statistically prove that a new prompt engineering strategy improves your system's accuracy. After running 500 tests, the new strategy scores 82% and the old scores 80%. Why should you not immediately push this to production based purely on these averages?</summary>

A simple difference in averages does not prove statistical significance. Because model outputs inherently contain variance, a 2% difference might simply be statistical noise. You must calculate confidence intervals (e.g., via bootstrapping) or run a paired t-test to determine if the 2% improvement is statistically significant and consistently reproducible before rolling out the change.
</details>

<details>
<summary>7. Your LLM-as-a-Judge pipeline consistently rates outputs generated by GPT-4 higher than equivalent outputs generated by Claude, even when blinded human experts rate them identically. The judge model being used is also GPT-4. What cognitive bias is affecting the pipeline?</summary>

This is an example of Self-Enhancement Bias. Evaluator models often exhibit a measurable preference for outputs generated by their own underlying architecture or family of models. They favor the specific stylistic markers, formatting, and vocabulary distributions that match their own internal representations, artificially skewing the evaluation results.
</details>

<details>
<summary>8. You are configuring an automated evaluation script that hits a public API endpoint. To ensure your benchmark results are perfectly reproducible across multiple runs, what critical API parameter must you set?</summary>

You must set the `temperature` parameter to `0.0`. Temperature controls the randomness of the model's output generation. Setting it to zero ensures greedy decoding, meaning the model will deterministically select the highest-probability token at every step, yielding the exact same output for the same prompt on repeated executions.
</details>

## Next Module

Now that you can rigorously evaluate models and identify alignment failures, it's time to look at a more modern fine-tuning path. In **[Module 1.9: Modern PEFT - DoRA and PiSSA](./module-1.9-modern-peft-dora-pissa/)**, we will examine newer adaptation techniques that improve efficiency and quality beyond the standard LoRA workflow.

## Sources

- [anthropic.com: reward tampering](https://www.anthropic.com/research/reward-tampering) — Anthropic's reward-tampering writeup directly discusses specification gaming, sycophancy, and models hacking reward mechanisms.
- [kubernetes.io: services networking](https://kubernetes.io/docs/concepts/services-networking/) — The Kubernetes networking docs explicitly state that containers in the same Pod share a network namespace and communicate over localhost.
- [openai.com: gpt 4](https://openai.com/research/gpt-4) — OpenAI's GPT-4 release page directly states that the company spent six months iteratively aligning GPT-4 before release.
- [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — Foundational RLHF paper for the alignment pipeline discussed throughout the module.
- [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073) — Covers an alternative alignment approach based on self-critique, revision, and AI feedback.
- [NIST AI RMF: Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence) — Provides practical governance and risk-management framing for deploying generative AI systems safely.
