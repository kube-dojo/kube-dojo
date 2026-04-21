---
title: "Single-GPU Local Fine-Tuning"
slug: ai-ml-engineering/advanced-genai/module-1.10-single-gpu-local-fine-tuning
sidebar:
  order: 811
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 2-3
---
**Reading Time**: 2-3 hours
**Prerequisites**: Fine-tuning LLMs, LoRA & Parameter-Efficient Fine-Tuning, Home AI Workstation Fundamentals, and Reproducible Python, CUDA, and ROCm Environments
---

## What You'll Be Able to Do

By the end of this module, you will:
- plan a realistic single-GPU fine-tuning workflow instead of guessing from scattered advice
- choose parameter-efficient methods that fit constrained VRAM budgets
- structure small local datasets and evaluations responsibly
- understand checkpoint, quantization, and runtime trade-offs for home-scale tuning
- know when single-GPU fine-tuning is a good idea and when it is not

**Why this matters**: for many learners, the first real fine-tuning experiment no longer happens on a research cluster. It happens on one consumer GPU. That is powerful, but it only works well when expectations are disciplined.

---

## The Most Important Truth About Single-GPU Fine-Tuning

Single-GPU local fine-tuning is real.

It is also narrow.

It is best for:
- learning the workflow
- adapting small or medium open models
- style or task specialization
- tightly scoped domain adaptation

It is not the default answer for:
- every knowledge problem
- massive model adaptation
- large-scale training
- weakly defined data

The home-scale version of fine-tuning works because modern PEFT techniques reduce the cost enough to make experimentation realistic. It does not remove the need for judgment.

---

## When Fine-Tuning Is the Right Tool

Use single-GPU fine-tuning when you need:
- repeatable behavior shifts
- domain-specific response style
- specialized formatting
- stronger task adaptation than prompting alone provides

Examples:
- adapting a local coding model to your team's conventions
- teaching a model to respond in a fixed support format
- specializing a small open model for a narrow internal corpus and task pattern

Do not fine-tune first when the real problem is:
- missing factual knowledge
- stale knowledge
- changing reference docs

That is usually a retrieval problem, not a weight-update problem.

---

## The Three Constraints You Cannot Ignore

### 1. VRAM

This determines:
- what base model is practical
- which quantization path is realistic
- how large your batch and sequence settings can be
- how frustrating the whole experiment will feel

### 2. Dataset Quality

Local fine-tuning does not rescue weak data.

If the examples are:
- noisy
- contradictory
- badly formatted
- too small for the task

then the model will faithfully learn the wrong thing.

### 3. Evaluation Discipline

Without evaluation, local fine-tuning becomes folklore:
- "it feels better"
- "the responses look nicer"
- "I think it learned"

That is not enough.

You need at least a small, separate check set and a clear sense of what improved.

---

## A Realistic Workflow

A disciplined single-GPU loop looks like this:

1. define the task
2. choose a base model that actually fits the hardware
3. prepare a small, clean dataset
4. reserve a validation split
5. choose a PEFT method
6. run a controlled training job
7. compare baseline vs adapted model
8. keep or discard based on evidence

The discard step matters.

A failed local tuning run is not waste if it teaches you that:
- the data is weak
- the task needs retrieval instead
- the base model is wrong
- the hardware constraint is too tight

---

## Why PEFT Is the Default Here

On a single GPU, [parameter-efficient methods are usually the practical path](https://arxiv.org/abs/2106.09685).

Why:
- lower VRAM pressure
- smaller artifacts
- faster iteration
- less risk than full fine-tuning

This is why the prerequisite modules matter.

You are not trying to brute-force full model retraining at home.
You are trying to learn disciplined adaptation.

---

## Data Preparation Rules for Home-Scale Tuning

Keep the dataset:
- narrow in purpose
- consistent in format
- clear in expected outputs
- small enough to inspect manually

Beginners often make one of two mistakes:

### Too Little Structure

Examples are inconsistent, so the model learns noise.

### Too Much Ambition

The dataset tries to solve multiple tasks at once:
- summarization
- classification
- instruction following
- style transfer

That usually weakens the result.

For a single-GPU first pass, choose one narrow adaptation target and optimize for clarity.

---

## Checkpoints and Storage Reality

Fine-tuning creates artifacts quickly:
- adapters
- logs
- configs
- intermediate checkpoints
- merged outputs

At home scale, checkpoint hygiene matters because storage is limited and mistakes are expensive.

Keep:
- final adapter
- training config
- evaluation notes
- one or two meaningful checkpoints if needed

Avoid keeping:
- every checkpoint forever
- random experiments with unclear names
- outputs you cannot map back to a configuration

You should be able to answer:
- which base model this came from
- which dataset this used
- which settings produced this adapter

If not, the artifact is not useful.

---

## Quantization and Local Reality

Single-GPU tuning often lives next to quantization decisions.

That creates a common confusion:
- quantization makes local work feasible
- [quantization also changes performance and compatibility expectations](https://arxiv.org/abs/2305.14314)

The right learner mindset is:
- use quantization to fit the workflow into real hardware
- do not assume every quantized setup behaves identically
- compare baseline and tuned outputs in the actual runtime you care about

Do not evaluate a tuning result in a way completely disconnected from how you plan to use the model later.

---

## What Good Results Actually Look Like

A good single-GPU tuning result usually looks like:
- better consistency on the narrow task
- better formatting discipline
- stronger adherence to the expected response pattern
- acceptable latency and memory use for the intended environment

A bad result often looks like:
- no meaningful improvement
- overfit style mimicry
- degraded general behavior
- weak transfer outside the tiny training examples

This is normal.

Local fine-tuning is not guaranteed value. It is a controlled experiment.

---

## When Not to Keep Going

Stop the tuning path and reassess if:
- the hardware barely sustains the run
- the dataset is too weak to trust
- retrieval would solve the problem more cleanly
- the task is broader than local tuning should handle
- evaluation shows little or no gain

Many learners lose time because they treat every failed tuning attempt as a reason to push harder.

Often the better move is architectural, not stubborn.

---

## Common Mistakes

| Mistake | What Goes Wrong | Better Move |
|---|---|---|
| using fine-tuning to solve a retrieval problem | stale or brittle behavior | use RAG when the issue is factual knowledge |
| choosing a base model too large for the hardware | unstable or miserable runs | choose the model by VRAM reality first |
| mixing multiple adaptation goals into one dataset | noisy learning signal | narrow the task definition |
| evaluating only by intuition | false confidence | compare baseline and tuned outputs deliberately |
| keeping chaotic checkpoints and artifacts | no reproducibility | keep only named, documented outputs |

---

## Check Your Understanding

1. Why is single-GPU fine-tuning best treated as a narrow adaptation workflow instead of general model training?
2. What is the difference between a tuning problem and a retrieval problem?
3. Why is a small, clean dataset often better than a larger but inconsistent one for first local tuning runs?
4. What evidence would justify discarding a local fine-tuning attempt?

---

<!-- v4:generated type=no_quiz model=codex turn=1 -->
## Quiz


**Q1.** Your team wants a local model to answer employee questions about a handbook that changes every month. One engineer suggests doing a single-GPU fine-tuning run on last quarter's documents so the model "knows the company policy." Based on this module, what is the better approach, and why?

<details>
<summary>Answer</summary>
Use retrieval, not fine-tuning, as the first solution.

The module explains that missing, stale, or frequently changing factual knowledge is usually a retrieval problem rather than a weight-update problem. Fine-tuning is better for repeatable behavior shifts, style, formatting, or narrow task adaptation, not for keeping up with changing reference docs.
</details>

**Q2.** You have one consumer GPU with limited VRAM, and a teammate insists on starting with the largest open model you can find because "bigger models always fine-tune better." After repeated out-of-memory errors and tiny batch settings, what should you change first?

<details>
<summary>Answer</summary>
Choose a base model that realistically fits the GPU, then use a parameter-efficient method such as LoRA.

The module says VRAM determines what base model is practical, which quantization path is realistic, and how usable the whole experiment will be. On a single GPU, PEFT is the default practical path because it lowers VRAM pressure, reduces artifact size, and speeds iteration.
</details>

**Q3.** A support team is building its first local fine-tuning dataset. They mix ticket classification examples, long-form summarization, friendly tone rewriting, and strict JSON incident reports into one small dataset. The tuned model becomes inconsistent. What dataset change would most likely improve the next run?

<details>
<summary>Answer</summary>
Narrow the dataset to one clear adaptation target with a consistent format.

The module warns that beginners often make the dataset too ambitious by combining multiple tasks at once. For a first single-GPU pass, the dataset should be narrow in purpose, consistent in structure, and clear about expected outputs so the model learns a strong signal instead of noise.
</details>

**Q4.** After a weekend fine-tuning run, your teammate says, "The tuned model feels smarter now," but they only tried a few prompts from memory and did not compare against the original model. What is missing from the workflow?

<details>
<summary>Answer</summary>
A separate evaluation process with a reserved validation or check set and a baseline comparison.

The module says evaluation discipline is one of the three constraints you cannot ignore. Without comparing baseline versus adapted behavior on a separate set, the result becomes folklore instead of evidence. "It feels better" is not enough to justify keeping the run.
</details>

**Q5.** You fine-tuned a model on one GPU and ended up with dozens of checkpoints named `test1`, `final2`, `really_final`, and `new_run_fixed`. A month later, nobody can tell which adapter came from which base model or dataset. According to the module, what should checkpoint hygiene look like instead?

<details>
<summary>Answer</summary>
Keep only the final adapter, the training config, evaluation notes, and at most one or two meaningful checkpoints, all with traceable names.

The module emphasizes that home-scale storage is limited and artifacts are only useful if you can identify which base model, dataset, and settings produced them. Keeping every checkpoint forever and using unclear names destroys reproducibility and makes the outputs hard to trust.
</details>

**Q6.** You use quantization so a training workflow fits on your single GPU. After tuning, a colleague evaluates the model in a different runtime and declares the fine-tuning a success even though that is not how the model will actually be deployed. Why is that a problem?

<details>
<summary>Answer</summary>
Because quantization affects performance and compatibility, so you should evaluate in the same runtime context you actually care about.

The module says quantization can make local work feasible, but not every quantized setup behaves identically. Baseline and tuned outputs should be compared in the real runtime environment you plan to use later, not in a disconnected setup that may hide practical differences.
</details>

**Q7.** Your single-GPU run technically completes, but the GPU is barely sustaining the job, the dataset is inconsistent, and evaluation shows almost no gain over the base model. One person argues you should just train longer. Based on the module, what is the better decision?

<details>
<summary>Answer</summary>
Stop the tuning path and reassess the approach instead of pushing harder.

The module explicitly says to reassess when hardware barely sustains the run, the dataset is too weak, retrieval would solve the problem more cleanly, or evaluation shows little improvement. A failed local tuning run is still useful if it shows the data, model choice, or architecture is wrong.
</details>

<!-- /v4:generated -->
<!-- v4:generated type=no_exercise model=codex turn=1 -->
## Hands-On Exercise


Goal: complete a reproducible single-GPU LoRA fine-tuning run on a small instruct model, compare baseline vs tuned behavior on a narrow task, and keep only artifacts you can trace back to the dataset and configuration.

- [ ] Create a clean project workspace for one experiment only.
  ```bash
  mkdir -p single-gpu-ft/{data,eval,artifacts,logs}
  cd single-gpu-ft
  pwd
  ```

- [ ] Record hardware limits before picking a base model so the run is sized to real VRAM, not guesswork.
  ```bash
  nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
  df -h .
  ```

- [ ] Choose one small open instruct model that realistically fits a single GPU with LoRA or QLoRA, and write the choice down in `logs/run-notes.md` with the task you want to improve.
  ```bash
  cat > logs/run-notes.md <<'EOF'
  Base model:
  Target task:
  GPU VRAM:
  PEFT method:
  Why this task is fine-tuning and not retrieval:
  EOF
  cat logs/run-notes.md
  ```

- [ ] Build a narrow training dataset in JSONL format with one output style only, such as strict JSON answers, support-template replies, or fixed classification labels.
  ```bash
  cat > data/train.jsonl <<'EOF'
  {"instruction":"Classify the ticket priority and return strict JSON.","input":"Database errors are preventing checkout for all users.","output":"{\"priority\":\"critical\",\"reason\":\"revenue-impacting outage\"}"}
  {"instruction":"Classify the ticket priority and return strict JSON.","input":"One internal dashboard widget loads slowly for a single analyst.","output":"{\"priority\":\"low\",\"reason\":\"limited user impact\"}"}
  {"instruction":"Classify the ticket priority and return strict JSON.","input":"Customers cannot reset passwords from the login page.","output":"{\"priority\":\"high\",\"reason\":\"authentication flow broken\"}"}
  EOF
  wc -l data/train.jsonl
  ```

- [ ] Reserve a separate evaluation set and keep it out of training so you can compare baseline versus tuned behavior honestly.
  ```bash
  cat > eval/check.jsonl <<'EOF'
  {"instruction":"Classify the ticket priority and return strict JSON.","input":"Payment confirmation emails are delayed by several hours.","expected":"{\"priority\":\"medium\",\"reason\":\"degraded customer communication\"}"}
  {"instruction":"Classify the ticket priority and return strict JSON.","input":"The public status page is unreachable during an active incident.","expected":"{\"priority\":\"high\",\"reason\":\"incident visibility impaired\"}"}
  EOF
  wc -l eval/check.jsonl
  ```

- [ ] Create a minimal reproducible config that records the base model, LoRA settings, batch size, sequence length, output directory, and checkpoint policy.
  ```bash
  cat > artifacts/config.yaml <<'EOF'
  base_model: your-chosen-model
  peft_method: lora
  lora_r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 8
  learning_rate: 2e-4
  num_train_epochs: 1
  max_seq_length: 1024
  save_total_limit: 2
  output_dir: artifacts/adapter
  EOF
  sed -n '1,120p' artifacts/config.yaml
  ```

- [ ] Run one short baseline check with the untuned model on the evaluation prompts and save the outputs for comparison.
  ```bash
  printf '%s\n' "Prompt 1: Payment confirmation emails are delayed by several hours." > eval/baseline.txt
  printf '%s\n' "Prompt 2: The public status page is unreachable during an active incident." >> eval/baseline.txt
  cat eval/baseline.txt
  ```
  Use the inference command for your chosen stack and append the raw model responses to `eval/baseline.txt`.

- [ ] Start a short LoRA or QLoRA training run that is small enough to finish locally without exhausting VRAM.
  ```bash
  nvidia-smi
  ```
  Run the training command for your framework, and save the exact command line in `logs/run-notes.md`.

- [ ] Verify that training produced a traceable adapter rather than a pile of unnamed checkpoints.
  ```bash
  find artifacts -maxdepth 3 -type f | sort
  du -sh artifacts
  ```

- [ ] Run the same evaluation prompts against the tuned adapter and save the outputs beside the baseline.
  ```bash
  printf '%s\n' "Prompt 1: Payment confirmation emails are delayed by several hours." > eval/tuned.txt
  printf '%s\n' "Prompt 2: The public status page is unreachable during an active incident." >> eval/tuned.txt
  cat eval/tuned.txt
  ```
  Use the same inference path as before, but load the adapter and append the tuned responses to `eval/tuned.txt`.

- [ ] Compare baseline and tuned outputs for the exact behavior you targeted, not for vague impressions.
  ```bash
  diff -u eval/baseline.txt eval/tuned.txt || true
  ```

- [ ] Keep only the final adapter, config, dataset, and evaluation notes, then delete throwaway checkpoints that do not help reproduce the result.
  ```bash
  ls -R artifacts eval logs
  ```

Success criteria:
- The run uses a base model and PEFT method that fit a single local GPU without repeated out-of-memory failures.
- `data/train.jsonl` and `eval/check.jsonl` are separate and narrowly focused on one task.
- The experiment has a saved config, saved baseline outputs, and saved tuned outputs.
- The tuned model shows a measurable improvement in the target format or behavior on the held-out prompts.
- The final artifacts are named clearly enough that someone else can identify the base model, dataset, and settings used.

<!-- /v4:generated -->
## Next Modules

- [Modern PEFT: DoRA and PiSSA](./module-1.9-modern-peft-dora-pissa/)
- [Notebooks to Production for ML/LLMs](../mlops/module-1.11-notebooks-to-production-for-ml-llms/)
- [Multi-GPU and Home-Lab Fine-Tuning](./module-1.11-multi-gpu-home-lab-fine-tuning/)

## Sources

- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — Original LoRA paper for claims about freezing base weights, training low-rank adapters, parameter-count reduction, memory savings, and PEFT trade-offs versus full fine-tuning.
- [PEFT LoRA Developer Guide](https://huggingface.co/docs/peft/developer_guides/lora) — Official implementation guide for LoRA configuration in PEFT, including rank, alpha, initialization, adapter behavior, and practical library-level fine-tuning mechanics.
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) — Primary source for 4-bit fine-tuning, NF4, double quantization, paged optimizers, and realistic single-GPU fine-tuning claims under constrained VRAM.
- [Transformers bitsandbytes Quantization Guide](https://huggingface.co/docs/transformers/en/quantization/bitsandbytes) — Official source for practical 8-bit and 4-bit quantization, QLoRA-related setup, device mapping, nested quantization, and hardware compatibility constraints relevant to local tuning.
