---
title: "Fine-tuning LLMs"
slug: ai-ml-engineering/advanced-genai/module-1.1-fine-tuning-llms
sidebar:
  order: 802
---

> **Prerequisites**: generative AI fundamentals, tokenization, the PyTorch training loop, basic model evaluation, and comfort reading small Python data pipelines.

## Learning Outcomes

- **Diagnose** whether prompt engineering, RAG, full fine-tuning, or PEFT best fits a request that changes model behavior, domain language, response format, or factual access.
- **Design** an SFT dataset and loss-masking plan using chat templates, completion-only labels, validation splits, and data-quality review before running a training job.
- **Configure** LoRA or full fine-tuning tradeoffs by reasoning about trainable parameters, optimizer state, mixed precision, gradient checkpointing, packing, and sequence length.
- **Evaluate** fine-tuned models with loss curves, holdout prompts, overfitting checks, and regression tests for catastrophic forgetting against baseline capabilities.
- **Operate** a reproducible training job with pinned libraries, adapter checkpoints, container boundaries, and a Kubernetes handoff path suitable for later home-lab modules.

## Why This Module Matters

Amazon's experimental recruiting tool is a useful warning because it was not a science-fiction failure mode. The AI Incident Database catalogues reports that Amazon started building an internal resume-ranking system in 2014, trained it on a decade of historical hiring data, and later abandoned it after the system showed gender-biased behavior such as penalizing resumes containing the word "women's" and downgrading graduates of all-women's colleges. The lesson for fine-tuning is not "never train models"; the lesson is that training data becomes behavior. If the examples encode yesterday's unfair pattern, the model can learn that pattern with more confidence than any prompt reviewer intended.

Fine-tuning is powerful because it changes the model's learned behavior instead of merely adding context around one request. A retrieval system can show a policy document to a model at runtime, and a prompt can remind the model to answer in a particular tone, but fine-tuning adjusts parameters or adapters so the desired pattern is easier for the model to produce by default. That permanence is exactly why fine-tuning deserves more care than prompt editing. You are not attaching a sticky note to the model; you are changing the training signal that shapes future token probabilities.

The practical problem is that many teams reach for fine-tuning for the wrong reason. They want the model to know yesterday's support article, calculate a current price, or follow a policy that will change next month. Those are usually retrieval, tool, or prompt-management problems. Fine-tuning becomes the right tool when the desired change is durable: a schema that must be emitted reliably, a domain dialect the model must internalize, a narrow task family with many high-quality examples, or a smaller serving model that needs to imitate a stable behavior from a larger teacher.

Think of an LLM as a skilled translator joining a specialized operations team. Prompting is a briefing before each shift. RAG is a binder of current procedures the translator can consult while working. Fine-tuning is an apprenticeship in the team's actual style, edge cases, and habits. Apprenticeship is worth the investment when the work pattern repeats every day. It is dangerous when the apprentice learns from sloppy notes, outdated rules, or examples that quietly reward the wrong outcome.

## Choosing the Right Adaptation Strategy

The first decision is whether you need to change knowledge access, response behavior, or model capacity. Prompt engineering is the lightest option when the base model can already perform the task and only needs clearer instructions, examples, or output constraints. RAG is the right default when the missing ingredient is external knowledge that is large, private, frequently updated, or auditable. Fine-tuning is appropriate when repeated examples should make the model respond differently even without long prompts or retrieved context.

This distinction matters because model weights are a poor database. A fine-tuned model cannot cite which training example made it answer a question, cannot forget one bad paragraph without another training run, and cannot reliably distinguish "the policy changed yesterday" from "the old pattern is still statistically likely." RAG keeps facts outside the model so they can be updated, deleted, access-controlled, and traced. Fine-tuning should shape how the model uses language and structure, not serve as the primary store for volatile facts.

There is also a middle ground called parameter-efficient fine-tuning, or PEFT. Full fine-tuning updates every trainable weight in the base model. PEFT methods freeze the base model and train smaller adapter components, soft prompts, or low-rank matrices that steer the model while leaving most learned representations untouched. LoRA and QLoRA are the PEFT variants you will study next, while DoRA and PiSSA appear later in this sub-track as newer refinements to the same general idea.

For a production architecture review, ask four questions before writing any training code. First, does the desired behavior need to survive without retrieved context? Second, can the team produce enough high-quality examples that show the target behavior and its boundaries? Third, will the adapted behavior remain stable long enough to justify a retraining and evaluation cycle? Fourth, can the organization evaluate regressions against the base model, especially safety, reasoning, and general-language tasks that were not the direct tuning objective?

Prompting wins when the answer to the first question is no. RAG wins when the behavior is already present but the facts are missing or changing. PEFT often wins when the behavior is stable, examples are good, and the team needs a cheap, reversible adaptation. Full fine-tuning is reserved for cases where adapter capacity is not enough, the team controls the training infrastructure, and the cost of changing all weights is justified by a durable business or research requirement.

```text
Need current private facts?       -> RAG or tools
Need clearer instruction only?    -> prompt engineering
Need stable format or tone?       -> SFT or PEFT
Need new domain dialect?          -> SFT, often PEFT first
Need broad capability shift?      -> full fine-tuning or continued training
Need preference between outputs?  -> DPO/RLHF family, covered later
```

The durable habit is to start with the least permanent intervention that can meet the requirement. This does not mean prompt everything forever. It means you should earn the right to fine-tune by proving that prompting and retrieval cannot reliably produce the behavior, then use a training method whose blast radius matches the desired change. Fine-tuning is not an upgrade badge; it is an architectural commitment.

The wrong question is "Can we fine-tune this?" because the answer is usually yes if you have access to weights or a managed tuning API. The better question is "What failure becomes easier to prevent after fine-tuning, and what failure becomes easier to create?" A support model that must always emit a strict JSON schema may benefit because schema-following becomes the default continuation. A compliance model that needs last week's regulatory update will suffer because the update belongs in an auditable source system, not in a parameter update that cannot explain itself.

You should also separate "the model does not know our words" from "the model does not know our facts." Domain language can be a legitimate tuning target when the model repeatedly misuses internal terms, confuses role names, or writes in a tone that breaks workflow expectations. Domain facts are different. A model can learn that "Sev2" means a particular escalation class, but the current owner, escalation room, or mitigation checklist should still come from retrieval or tools because those details change and need traceability.

The adaptation choice also affects product latency and cost, but treat those as design constraints rather than universal promises. A shorter prompt can reduce request size, and a tuned smaller model can sometimes replace a larger general model for a narrow task. Those outcomes depend on traffic, serving stack, model size, and evaluation tolerance. Do not sell fine-tuning as guaranteed cost reduction. Sell it as a way to move stable behavior from repeated prompt context into a trained behavior, then measure whether that trade actually helps the workload.

Finally, fine-tuning should have an exit strategy. If the tuned model fails evaluation, can you unload the adapter and return to the base model? If a customer-specific adapter becomes stale, can you retire it without rebuilding the serving stack? If the dataset contains a policy error, can you identify which runs used that dataset snapshot? These operational questions are part of the adaptation strategy, not paperwork after the interesting ML work is done.

## Full Fine-Tuning and PEFT

Full fine-tuning exposes every model weight to gradient updates. For a small transformer, that can be perfectly reasonable. For a multi-billion-parameter LLM, it changes the operational shape of the project because the optimizer must track additional state for every trainable parameter, activations must be kept or recomputed for backpropagation, and checkpoints can become large enough to slow iteration. The upside is maximum flexibility. The downside is cost, fragility, and a larger chance of damaging capabilities the base model already had.

PEFT changes the training surface. Instead of asking the optimizer to move the entire network, LoRA inserts trainable low-rank matrices beside selected linear layers while keeping the original weights frozen. During inference, the adapter contribution is added to the frozen layer output. During training, the gradients update the adapter matrices, not the base model. This sharply reduces the number of trainable parameters and makes adapter artifacts easier to store, review, roll back, and swap.

The low-rank idea rests on a practical observation: many task adaptations do not need a full-rank update to every large matrix. If the base model already knows language, code, or customer-support style, the fine-tuning job often needs to nudge existing representations rather than relearn them. LoRA constrains the update through a rank `r`, which is a capacity knob. Too low and the adapter may underfit. Too high and the adapter becomes more expensive and easier to overfit.

QLoRA adds quantization to the picture. The base model is loaded in a lower-precision representation, while the trainable adapter path keeps enough precision for optimization. This is a memory strategy, not a magic accuracy guarantee. Quantization reduces the memory footprint of frozen weights, but the training job still needs room for activations, gradients for trainable parameters, temporary buffers, tokenizer batches, and evaluation. The mental model is "fit the frozen base more cheaply, train the adapter carefully."

Full fine-tuning, LoRA, and QLoRA are not moral categories. They are tools with different failure modes. Full fine-tuning can learn larger behavior changes but can forget broad abilities faster and requires heavier checkpoint discipline. LoRA is easier to experiment with and roll back, but adapter capacity and target-module choices matter. QLoRA extends LoRA to tighter memory budgets, but it adds quantization assumptions and backend dependencies that must be verified in the exact environment.

The next module goes deep on LoRA math, so this module keeps the strategic view. You should be able to explain why freezing the base model reduces trainable state, why adapter artifacts are operationally attractive, and why "parameter-efficient" does not mean "evaluation-optional." A tiny adapter can still encode a harmful shortcut if the dataset rewards that shortcut, and a cheap run can still produce an expensive incident if it ships without regression tests.

Full fine-tuning is most defensible when the target behavior is broad enough that adapters cannot express it cleanly, when the team has a mature distributed training stack, and when the release process can absorb a full model artifact. Examples might include research on a new base model checkpoint, continued training on a large domain corpus before instruction tuning, or an internal foundation model program where the organization owns the complete lifecycle. Even then, the team needs baseline comparisons because a full-weight update can improve the target benchmark while weakening unrelated abilities.

PEFT is most defensible when the target behavior is narrow, reversible, or customer-specific. An adapter can represent a support style, a compliance drafting pattern, or a domain-specific extraction schema without forcing every deployment to carry a separate full model. This reversibility changes how you operate experiments. You can keep the base model constant, compare multiple adapters against the same prompt suite, and archive or unload an adapter whose behavior is no longer approved. That is a major governance advantage, not only a memory advantage.

The adapter boundary also clarifies responsibility between model training and model serving. If the base model is a shared platform dependency, product teams can own adapters that encode their workflow-specific behavior while the platform team owns base-model updates, safety gates, and serving infrastructure. This split is not free because adapter compatibility can still break when the base model changes. It is easier to manage than a world where every team creates an untracked full-model fork with different weights, tokenizer assumptions, and release notes.

Rank, target modules, and dropout are not decorations on a LoRA config. Rank controls the size of the low-rank update. Target modules decide where the adapter can influence the network, such as attention projections or feed-forward layers. Dropout can reduce overfitting on small datasets but can also slow learning if the target behavior is already subtle. Treat the first adapter run as a measurement instrument. It tells you whether the task has enough signal, whether the chosen modules are plausible, and whether the dataset produces the expected gradients.

When QLoRA enters the design, separate storage precision from training behavior. Loading frozen weights in 4-bit form can make a model fit in memory that would otherwise be inaccessible, but the optimizer still needs a numerically stable path for the trainable adapter weights. Backend support, GPU architecture, driver versions, and library versions become part of the experiment. That is why durable curriculum should teach quantization as a memory-management concept and quarantine exact support claims in a dated snapshot.

## How SFT Changes Behavior

Supervised fine-tuning, or SFT, trains the model on examples of the behavior you want. In a causal language model, the core objective is next-token prediction over formatted sequences. If the example contains a user request and an assistant answer, the trainer tokenizes the sequence, shifts labels by one token, and computes cross-entropy on the target tokens. The model is rewarded for assigning higher probability to the desired continuation.

The subtle part is deciding which tokens should contribute to the loss. If the model is trained on the entire chat transcript, it can spend capacity learning to reproduce user prompts and system messages. For many assistant-tuning jobs, you want loss on assistant messages only or on completion tokens only. That masking choice tells the optimizer, "learn to answer like this," rather than "learn to imitate every token in the whole conversation." This is one of the easiest places to silently train the wrong behavior.

Chat templates are the second common trap. Chat models are not trained on abstract JSON roles; they see a serialized token sequence with role markers, separators, end-of-turn tokens, and sometimes generation markers. A dataset with `messages` fields must be converted through the tokenizer's chat template so the sequence matches what the model expects. Handwritten templates can work, but a one-token mismatch at the turn boundary can cause expensive confusion during training and strange generations afterward.

Instruction tuning, domain adaptation, and continued pretraining are related but distinct. Instruction tuning teaches the model to follow task instructions and produce helpful responses. Domain adaptation teaches a model the language, conventions, and examples of a specialized area, such as legal drafting or incident response. Continued pretraining keeps training on raw or lightly structured text to shift the base distribution before later supervised tuning. These approaches can be combined, but they answer different questions and require different evaluation sets.

Data quality matters more than raw example count because every example is a training vote. A thousand carefully reviewed examples that show the desired behavior, edge cases, refusal boundaries, and formatting constraints can be more useful than a much larger scrape of inconsistent outputs. Duplicate prompts, contradictory labels, hidden personally identifiable information, unreviewed synthetic data, and stale policy examples all teach the model that sloppy behavior is acceptable. The optimizer has no concept of "this row was a draft."

Good SFT datasets usually contain three layers. The happy path teaches the normal behavior. The boundary path teaches what to refuse, escalate, ask for, or retrieve instead of answering. The regression path protects base abilities that the adapted model must not lose, such as arithmetic, harmless small talk, multilingual behavior, or safety rules. Without the third layer, you can celebrate a falling training loss while quietly making the model worse at everything outside the tuning set.

Packing, epochs, learning rate, and sequence length are not independent knobs. Packing combines shorter examples into fixed-length sequences to reduce padding waste, but it can complicate loss masks and example boundaries if the data pipeline is not built for it. More epochs give the adapter more chances to fit the dataset, but they also increase overfitting risk. Longer sequences preserve multi-turn context, but they raise activation memory. Higher learning rates can help adapters learn quickly, but they can destabilize small, repetitive datasets.

Overfitting signals are rarely subtle if you look for them early. Training loss keeps falling while validation loss flattens or rises. The model repeats exact training answers when asked paraphrased prompts. The model becomes overconfident in the fine-tuned domain and starts forcing unrelated questions into that domain. Evaluation prompts outside the target task degrade. These symptoms are not solved by declaring the benchmark too hard; they are evidence that the training distribution, run length, or regularization needs work.

Catastrophic forgetting is the broader version of this problem. Continual fine-tuning research has documented that language models can lose earlier knowledge or capabilities while adapting to new tasks. PEFT reduces the blast radius by freezing the base model, but it does not erase the need to test the composed model plus adapter. If the adapter strongly steers outputs toward a narrow pattern, the deployed behavior can still look like forgetting even though the frozen base weights remain intact.

The SFT loop begins before training with schema design. A conversational dataset should make the role boundaries explicit, and a prompt-completion dataset should make the prompt and target continuation separable. Mixing these formats casually is a common source of broken loss masking. If your examples are originally stored as tickets, email threads, or documents, convert them into the training format with a deterministic script and keep the original record identifier. That makes it possible to audit a suspicious output back to the source example.

Loss masking deserves the same level of review as labels in a supervised classifier. In a classifier, nobody would accept a dataset where the positive and negative labels were accidentally shifted by one row. In SFT, the equivalent error can be less visible because the script still runs and loss still decreases. A quick inspection should show input IDs, decoded text, and label positions where ignored tokens are marked. If the user prompt contributes to the loss when you intended assistant-only training, stop the run and fix preprocessing.

Learning rate and epochs should be interpreted through data diversity. A high-quality dataset with many varied examples can tolerate more training than a tiny dataset of near-duplicates. A small adapter on a narrow schema may learn quickly, which means extra epochs can move from useful adaptation to memorization. Instead of copying a learning rate from a tutorial, run short probes and compare validation behavior. The probe run is not wasted; it tells you whether the loss curve is smooth, whether outputs move in the expected direction, and whether the dataset contains enough signal.

Packing is another place where efficiency can fight clarity. When many short examples are packed into one sequence, GPU utilization can improve because less computation is spent on padding. The price is that example boundaries and loss masks must remain correct after packing. For early debugging, leave packing off until you trust the formatting. After the labels are verified, enable packing deliberately and compare a small batch before and after. If the packed examples blend conversations in a way your trainer does not handle correctly, the throughput gain is not worth it.

Continued pretraining should not be disguised as SFT. If you have a large corpus of domain documents and no explicit input-output behavior, you are shifting the language-model distribution, not teaching the model a task response. That can be useful before SFT, especially when the base model lacks domain vocabulary, but it raises different risks. The model may absorb stale or biased prose, and the evaluation should include domain-language fluency as well as downstream task behavior. A raw document corpus is not a substitute for reviewed instruction examples.

Instruction tuning and preference tuning also solve different problems. SFT shows the model target answers. Preference optimization methods, covered later, show relative judgments between outputs or optimize against reward signals. If you only have correct examples, SFT is the natural starting point. If you have chosen and rejected answers for the same prompt, preference optimization may become relevant. For this module, the important boundary is that every training method encodes a data contract; using a fancier loss cannot rescue a dataset that lacks the fields the method requires.

The safest SFT projects create a small evaluation harness before the first expensive run. The harness should ask the base model and the tuned model the same prompts, store responses, and summarize differences. Include target prompts where the tuned model should improve, near-miss prompts where it should ask a clarifying question, and unrelated prompts where it should behave like the base model. This makes quality review concrete. Reviewers can argue about outputs instead of arguing about whether a loss number "feels good."

## Data, Memory, and Evaluation Discipline

A training job fails in two ways: it can fail mechanically, or it can succeed mechanically while producing a model you should not deploy. Mechanical failure is easier to notice. The process runs out of memory, gradients become `NaN`, the tokenizer has no pad token, the trainer rejects a dataset schema, or the checkpoint directory contains the wrong artifacts. Behavioral failure is harder because the logs can look normal while the model learns a brittle shortcut.

Memory math begins with the distinction between frozen weights, trainable weights, optimizer state, gradients, and activations. In full fine-tuning, optimizer state and gradients scale with every trainable parameter. With Adam-style optimizers, the optimizer maintains moment estimates in addition to the parameter values, so the training footprint is far larger than the raw model weights. In PEFT, frozen base weights still consume memory, but optimizer state is concentrated in the adapter parameters, which is why adapter training is so much lighter.

Activations often surprise new fine-tuning teams. During the forward pass, the model stores intermediate tensors needed for the backward pass. Sequence length, batch size, hidden dimension, layer count, and attention implementation all affect this footprint. Gradient checkpointing trades extra compute for lower activation memory by recomputing some intermediates during backpropagation instead of storing them all. Mixed precision reduces memory and bandwidth for many tensors, but it must be matched to hardware support and numerical stability.

The effective batch size is the product of per-device batch size, gradient accumulation steps, and data-parallel workers. If you can fit only one or two examples per GPU, gradient accumulation can still give the optimizer a larger effective batch over several micro-steps. This does not make the run free. It changes wall-clock time, logging cadence, and how quickly the optimizer sees enough examples to make a stable update. Treat it as a deliberate scheduling decision, not a hidden default.

Evaluation should be designed before training. Keep a holdout split that represents the same task family, and keep a separate regression set that represents capabilities you do not want to damage. Track loss, but also inspect outputs. Use deterministic decoding for some regression checks so comparisons are stable, then use realistic decoding for product-like review. Store prompts, model IDs, adapter hashes, library versions, and data snapshots together so a surprising result can be reproduced.

A useful fine-tuning review has at least four artifacts. The data card explains where examples came from, what was removed, and which known gaps remain. The run card records versions, hyperparameters, hardware, and random seeds. The eval card compares base and tuned behavior on target prompts, adversarial prompts, and regression prompts. The release card states whether the adapter is loaded dynamically, merged into a model artifact, or held for more review.

Kubernetes does not make a bad training plan good, but it can make the workload reproducible and observable. A `Job` gives the run a named lifecycle, resource limits, restart policy, logs, and a place to attach GPU scheduling constraints. For early experiments, a local script is enough. For repeated team workflows, a containerized training job with explicit input and output mounts is easier to audit than a long-lived shell session on a shared GPU host.

Data review should be staged like code review. The first pass removes unsafe or out-of-scope records, the second pass checks whether examples actually demonstrate the desired behavior, and the final pass samples tokenized records to verify the training representation. Synthetic data can be useful when human-written examples are scarce, but it should be treated as generated draft material. Reviewers need to ask whether the synthetic answer is correct, whether it is diverse enough, and whether it leaks the style or mistakes of the teacher model.

Deduplication is not only about saving tokens. Duplicate examples overstate the importance of a pattern and can make validation look better than it is if near-identical rows appear in both splits. For text data, exact hashing catches only the easiest duplicates. Teams often need normalized text, approximate matching, and reviewer judgment for paraphrases. The practical rule is simple: if a human would say two examples teach the same behavior with the same wording, do not let them dominate both training and evaluation.

Privacy and licensing belong in the fine-tuning plan because training can preserve sensitive patterns even when no obvious secret appears in the final checkpoint. Customer tickets may contain names, account identifiers, health details, or contractual terms. Internal documents may be licensed for reading but not for creating derivative model artifacts. A data card should state what categories were excluded, how redaction was performed, and who approved the source. That record is boring only until someone asks why the model produced a phrase that looks like a real customer note.

The memory plan should start with a budget table in your run card, even if the numbers are rough. List the base model loading precision, adapter rank, sequence length, per-device batch size, gradient accumulation, checkpointing choice, and expected output artifact. Then run a small batch and record actual memory use. This habit makes scaling less mysterious. When a later run fails, you can see whether the change was sequence length, batch size, target modules, precision, or a library upgrade.

Gradient checkpointing is best understood as controlled forgetfulness during training. The forward pass keeps fewer intermediate activations, and the backward pass recomputes some of them when needed. This lowers memory pressure at the cost of extra compute. It is often a good trade for long-sequence SFT on constrained GPUs, but it changes wall-clock expectations. If a team enables checkpointing without updating job timeouts and progress monitoring, a healthy run can look stalled simply because each step takes longer.

Mixed precision is similarly practical rather than fashionable. Lower precision can reduce memory and improve throughput on supported hardware, but unsupported or unstable combinations can create underflow, overflow, or backend errors. The right setting depends on the GPU, framework, and model. Record the precision mode, test a short run, and watch for `NaN` loss or abnormal gradient norms. If stability is uncertain, a slower stable run is more useful than a faster run whose numeric behavior you cannot trust.

Evaluation should include negative space: prompts where the model should not use the tuned behavior. A legal-drafting adapter should not turn a request for a poem into a contract clause. A support-summary adapter should not force every general question into incident format. These tests catch overgeneralization, which is often the product symptom users notice first. The model may not have forgotten the base skill in a strict weight-space sense; the adapter may simply steer too aggressively for the deployment context.

Release review should name the loading path. Adapter-only release means the serving layer loads the base model plus adapter and can often disable that adapter quickly. Merged release means the adapter contribution is folded into model weights, which may simplify inference but makes rollback and provenance different. Neither is always right. The important point is that the release artifact must match the operational expectation, and the evaluation report should test the same composition that production will serve.

## Landscape Snapshot: Current HF Training Stack

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> | Surface | Verified snapshot |
> |---|---|
> | Package versions visible from PyPI in this environment | `transformers==5.10.2`, `trl==1.5.1`, and `peft==0.19.1` are current downloadable releases. |
> | TRL SFT API | `SFTTrainer` accepts `args=SFTConfig(...)`, `processing_class=...`, `train_dataset=...`, `eval_dataset=...`, `peft_config=...`, and `formatting_func=...`; older snippets using `tokenizer=` and trainer-level `max_seq_length=` should be rechecked before copying. |
> | SFT data formats | TRL documents language-modeling and prompt-completion datasets in both standard and conversational forms, including `messages`, `prompt`, and `completion` fields. |
> | Loss masking knobs | `SFTConfig` includes `assistant_only_loss`, `completion_only_loss`, `packing`, `max_length`, and `loss_type`, with defaults that can differ from plain `TrainingArguments`. |
> | Example model IDs verified on the Hub | `Qwen/Qwen3-0.6B`, `Qwen/Qwen2.5-0.5B-Instruct`, `HuggingFaceTB/SmolLM2-135M-Instruct`, and `TinyLlama/TinyLlama-1.1B-Chat-v1.0` are real Hugging Face model repositories. |
>
> This table is illustrative, not a leaderboard or endorsement. Pin your own stack, record exact versions in the run card, and reread upstream docs before reusing any model ID or trainer argument.

The snapshot is intentionally small because library details age faster than the concept. The durable lesson is that trainer APIs are part of your experiment state. A model card, dataset hash, and adapter checkpoint are not enough if the preprocessing code changed between runs. In modern Hugging Face stacks, the difference between `tokenizer`, `processing_class`, automatic chat-template application, and assistant-only masking can determine whether a run trains the intended behavior or a subtly different one.

The following minimal script follows the 2026-06 TRL shape. It is intentionally a toy run: tiny data, a small public model ID, a short sequence length, and a few steps. Its purpose is to make the pipeline structure concrete, not to produce a deployable adapter.

```python
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer
from trl import SFTConfig, SFTTrainer


MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

records = [
    {
        "prompt": [
            {"role": "system", "content": "You write concise incident handoff notes."},
            {"role": "user", "content": "Summarize: API errors rose after the cache deploy."},
        ],
        "completion": [
            {"role": "assistant", "content": "Impact: API errors increased after the cache deploy. Next: roll back the cache change, compare error rates, and preserve logs."},
        ],
    },
    {
        "prompt": [
            {"role": "system", "content": "You write concise incident handoff notes."},
            {"role": "user", "content": "Summarize: queue latency is high and workers are CPU-bound."},
        ],
        "completion": [
            {"role": "assistant", "content": "Impact: queue latency is elevated because workers are CPU-bound. Next: scale workers, profile hot paths, and watch backlog drain time."},
        ],
    },
    {
        "prompt": [
            {"role": "system", "content": "You write concise incident handoff notes."},
            {"role": "user", "content": "Summarize: checkout recovered after database failover."},
        ],
        "completion": [
            {"role": "assistant", "content": "Impact: checkout recovered after database failover. Next: confirm write latency, check replica health, and document the failover timeline."},
        ],
    },
    {
        "prompt": [
            {"role": "system", "content": "You write concise incident handoff notes."},
            {"role": "user", "content": "Summarize: no customer impact, but alert noise doubled."},
        ],
        "completion": [
            {"role": "assistant", "content": "Impact: no customer impact was observed, but alert noise doubled. Next: tune alert thresholds and review noisy labels."},
        ],
    },
]

dataset = Dataset.from_list(records)
split = dataset.train_test_split(test_size=0.25, seed=7)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

peft_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)

args = SFTConfig(
    output_dir="out/qwen-incident-adapter",
    max_steps=20,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=1e-4,
    max_length=256,
    packing=False,
    completion_only_loss=True,
    eval_strategy="steps",
    eval_steps=10,
    save_steps=20,
    logging_steps=5,
    report_to=[],
    fp16=False,
    bf16=False,
)

trainer = SFTTrainer(
    model=MODEL_ID,
    args=args,
    processing_class=tokenizer,
    train_dataset=split["train"],
    eval_dataset=split["test"],
    peft_config=peft_config,
)

trainer.train()
trainer.save_model("out/qwen-incident-adapter/final")
```

If you adapt this script, make the first production change about data rather than hyperparameters. Replace the toy examples with reviewed examples, preserve the prompt-completion boundary, add a validation split that contains realistic paraphrases, and inspect tokenized samples before spending GPU time. The highest-leverage debugging command is often not a profiler; it is printing five formatted examples and confirming that the assistant answer, not the user prompt, is what contributes to the loss.

## Did You Know?

- **LoRA freezes the base model during adapter training**: the original paper framed low-rank adapters as a way to train a small set of added parameters while preserving the pretrained weights, which is why adapter-only artifacts are easier to review and roll back.
- **TRL can mask assistant messages directly**: current `SFTConfig` exposes `assistant_only_loss=True`, but that behavior depends on compatible conversational data and chat-template support, so inspect the processed labels before trusting the setting.
- **Chat templates are model-specific contracts**: Hugging Face Transformers documents `apply_chat_template` because two chat models can use the same JSON roles while requiring different serialized control tokens.
- **Catastrophic forgetting is measurable, not mystical**: continual fine-tuning studies evaluate whether a model loses prior knowledge or reasoning performance after adapting to new tasks, so every tuned model needs regression prompts outside the target domain.

## Common Mistakes

| Mistake | Why it happens | How to fix |
|---|---|---|
| Fine-tuning for volatile facts | The team treats weights like a searchable knowledge base because the first demo answers a few memorized questions correctly. | Put changing facts in RAG or tools, and reserve fine-tuning for durable behavior, format, tone, and domain language. |
| Training on the whole transcript | A dataset is serialized without masking, so user, system, and assistant tokens all contribute to the same loss. | Use prompt-completion or conversational masking, then inspect labels and confirm ignored tokens are marked correctly. |
| Trusting example count over example quality | A large scrape feels statistically impressive but contains duplicates, contradictions, stale policies, and unreviewed synthetic answers. | Build a data review loop, deduplicate aggressively, keep source metadata, and prefer fewer examples with clear target behavior. |
| Copying stale trainer snippets | Hugging Face APIs change, and older tutorials may use argument names that no longer match the pinned stack. | Pin `transformers`, `trl`, and `peft`, record versions in the run card, and check the live docs or source before launch. |
| Hiding overfitting behind low loss | Training loss keeps improving because the model is memorizing a narrow dataset rather than learning a reusable pattern. | Watch validation loss, test paraphrases, reduce epochs, increase diversity, and keep exact-match leakage out of the eval set. |
| Ignoring base-model regressions | The target task improves, so reviewers skip arithmetic, safety, multilingual, or general-helpfulness prompts. | Compare base and tuned outputs on a regression suite before release, and block deployment on unacceptable degradation. |
| Saving the wrong artifact | The script merges or saves the full model when the release process expected adapter-only output. | Decide adapter-only versus merged release up front, verify `adapter_config.json` and adapter weights, and document the load path. |

## Knowledge Check

1. Scenario: A product manager asks you to fine-tune a model so it can answer questions from a policy handbook that changes every week. How do you **diagnose** whether prompt engineering, RAG, full fine-tuning, or PEFT is the right choice?

<details>
<summary>Answer</summary>

Use RAG or a tool-backed retrieval path for the changing handbook, not fine-tuning. The missing capability is current knowledge access, and the source needs deletion, replacement, permissions, and citations. Prompt engineering can improve how the model uses retrieved passages, while PEFT or full fine-tuning would only make sense if the stable requirement were a durable response style or schema that should apply across many handbook questions.

</details>

2. Scenario: Your SFT dataset uses `messages` with system, user, and assistant roles. The first run learns to echo user prompts before answering. How should you **design** the dataset and loss-masking plan differently?

<details>
<summary>Answer</summary>

Keep the conversational structure, but verify that the tokenizer's chat template serializes the roles correctly and that the loss is applied only to the assistant response when that is the intended behavior. In TRL, that means reviewing whether `assistant_only_loss` or completion-only training matches the dataset format, then printing tokenized examples and labels to confirm prompt tokens are ignored rather than trained as targets.

</details>

3. Scenario: A team wants full fine-tuning because "adapters are too small to matter," but they have one GPU and a narrow formatting task. How do you **configure** the LoRA versus full fine-tuning tradeoff?

<details>
<summary>Answer</summary>

Start with LoRA or QLoRA because the task is narrow and the hardware budget is constrained. Full fine-tuning would require optimizer state and gradients for every trainable base parameter, while LoRA concentrates trainable state in adapter matrices. Configure a modest rank, target the relevant projection modules, use a validation set for format adherence, and escalate only if adapter capacity demonstrably underfits.

</details>

4. Scenario: Training loss keeps dropping, validation loss has flattened, and the tuned model repeats exact examples when prompts are paraphrased. How do you **evaluate** the overfitting risk before release?

<details>
<summary>Answer</summary>

Treat this as overfitting until proven otherwise. Compare base and tuned outputs on held-out paraphrases, exact-leakage checks, and realistic prompts that were not in the training set. Shorten the run, reduce epochs or steps, improve data diversity, and keep a separate regression suite so the model cannot pass merely by memorizing the training distribution.

</details>

5. Scenario: After domain adaptation, the model handles internal incident summaries well but performs worse on basic general questions. How should you **evaluate** catastrophic forgetting and decide whether the adapter is safe?

<details>
<summary>Answer</summary>

Evaluate the tuned model against the base model on a regression suite outside the incident-summary domain. Include general reasoning, harmless factual questions, safety refusals, and representative user tasks that must remain intact. If regressions are unacceptable, reduce adapter strength, improve mixed-domain training data, shorten training, or keep the adapter scoped to workflows where the narrowed behavior is acceptable.

</details>

6. Scenario: A training job runs out of memory after you double sequence length and batch size at the same time. How do you reason about trainable parameters, optimizer state, mixed precision, gradient checkpointing, and packing?

<details>
<summary>Answer</summary>

Separate parameter memory from activation memory. With PEFT, trainable parameters and optimizer state may be small, but longer sequences and larger batches increase activations sharply. Reduce per-device batch size, use gradient accumulation for effective batch size, enable gradient checkpointing if wall-clock cost is acceptable, choose mixed precision that your hardware supports, and use packing only after verifying masks and boundaries.

</details>

7. Scenario: You need to hand a successful local SFT experiment to the platform team for repeated runs. What should the **operate** checklist include for pinned libraries, adapter checkpoints, containers, and Kubernetes?

<details>
<summary>Answer</summary>

Record package versions, model ID, dataset snapshot, seed, hyperparameters, and evaluation results in a run card. Save adapter-only artifacts unless the release explicitly requires a merged model. Build a container with the same pinned training stack, mount inputs and outputs explicitly, and run it as a Kubernetes `Job` with GPU resource limits, logs, and a restart policy that matches the checkpointing strategy.

</details>

## Hands-On Exercise

This exercise is a pipeline audit, not a race to produce a high-quality model. You will create a toy SFT script, run a short adapter training job in an environment where you have accepted the model license and installed the ML stack, then inspect the artifacts and evaluation notes. The goal is to prove that you can keep data, masking, versions, and checkpoints visible before scaling the experiment.

Create an isolated environment outside this documentation repository or inside a disposable lab directory. The exact dependency stack changes quickly, so pin versions for your run and record them in a `RUN_CARD.md` file before training. The commands below use a local virtual environment and avoid relying on the KubeDojo site venv.

```bash
mkdir sft-lab
cd sft-lab
python -m venv .venv
.venv/bin/python -m pip install \
  "transformers==5.10.2" \
  "trl==1.5.1" \
  "peft==0.19.1" \
  "datasets" \
  "accelerate" \
  "torch"
```

Copy the minimal script from the landscape section into `train_sft.py`, then add a short `RUN_CARD.md` that names the model, package versions, dataset source, masking choice, and expected artifact path. If your environment does not have enough memory for the example model, switch to another verified small model from the snapshot and record that substitution explicitly.

```bash
.venv/bin/python train_sft.py
find out/qwen-incident-adapter -maxdepth 3 -type f | sort
```

If you later hand this to a Kubernetes cluster, keep the manifest boring. Use a container image built from the same pinned stack, mount the dataset read-only, mount an output volume for adapters, request the GPU resource explicitly, and choose retries based on checkpointing. Blindly retrying a non-checkpointed job that always fails on the same batch wastes hardware time and hides the root cause.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: sft-incident-adapter
  namespace: ml-workloads
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: trainer
          image: registry.example.com/ml/sft-trainer:2026-06
          command: ["/bin/sh", "-c", "python /workspace/train_sft.py && find /outputs -maxdepth 3 -type f | sort"]
          resources:
            limits:
              nvidia.com/gpu: "1"
          volumeMounts:
            - name: dataset
              mountPath: /data
              readOnly: true
            - name: outputs
              mountPath: /outputs
      volumes:
        - name: dataset
          persistentVolumeClaim:
            claimName: incident-sft-dataset
        - name: outputs
          persistentVolumeClaim:
            claimName: incident-sft-outputs
```

**Success Checklist**

- [ ] Your `RUN_CARD.md` lists the model ID, exact package versions, masking setting, sequence length, learning rate, steps, and dataset snapshot.
- [ ] You inspected at least three tokenized training examples and confirmed the assistant answer is the intended loss target.
- [ ] The output directory contains adapter-oriented artifacts rather than an accidental full-model dump, or your run card explains why you intentionally saved a merged model.
- [ ] Your evaluation notes compare base and tuned outputs on at least three target prompts and three unrelated regression prompts.
- [ ] If you drafted the Kubernetes handoff, the `Job` has explicit GPU limits, input/output mounts, and a retry policy that matches the checkpointing design.

## Next Module

Continue with [Module 1.2: LoRA & Parameter-Efficient Fine-tuning](../module-1.2-lora-parameter-efficient-fine-tuning/) to study the adapter math, rank choices, initialization options, and PEFT implementation details that this module only introduced at the decision-framework level.

## Sources

- [AI Incident Database Report 603](https://incidentdatabase.ai/reports/603/) — Catalogues reporting on Amazon's experimental recruiting tool and the gender-bias behavior used as the module's opening cautionary example.
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — Primary paper for frozen-base low-rank adapters and the parameter-efficient adaptation framing used throughout the module.
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) — Primary source for 4-bit adapter fine-tuning concepts, NF4, double quantization, and paged optimizer motivation.
- [TRL SFTTrainer Documentation](https://huggingface.co/docs/trl/en/sft_trainer) — Official source for the current `SFTTrainer`, `SFTConfig`, dataset formats, masking options, packing, and PEFT integration.
- [Transformers Chat Templates](https://huggingface.co/docs/transformers/en/chat_templating) — Official source for model-specific chat serialization and `apply_chat_template` behavior.
- [PEFT LoRA Developer Guide](https://huggingface.co/docs/peft/en/developer_guides/lora) — Official implementation guide for LoRA configuration, target modules, adapter behavior, and PEFT-specific tradeoffs.
- [Transformers bitsandbytes Quantization Guide](https://huggingface.co/docs/transformers/en/quantization/bitsandbytes) — Official source for 8-bit and 4-bit quantization concepts relevant to QLoRA-style memory planning.
- [Transformers Trainer and TrainingArguments](https://huggingface.co/docs/transformers/main_classes/trainer) — Official reference for Trainer infrastructure, evaluation strategy, checkpointing, mixed precision, and distributed training arguments.
- [Qwen/Qwen2.5-0.5B-Instruct Model Card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) — Verifies the small public model ID used in the toy SFT script.
- [Qwen/Qwen3-0.6B Model Card](https://huggingface.co/Qwen/Qwen3-0.6B) — Verifies a current small Qwen model ID used in the examples.
- [HuggingFaceTB/SmolLM2-135M-Instruct Model Card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) — Verifies another small model repository suitable for learners comparing example IDs.
- [An Empirical Study of Catastrophic Forgetting in Large Language Models During Continual Fine-tuning](https://arxiv.org/abs/2308.08747) — Supports the discussion of forgetting and the need for regression evaluation after adaptation.
- [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — Canonical source for instruction tuning as part of the broader alignment pipeline, including supervised fine-tuning before preference optimization.
- [OpenAI Model Optimization Guide](https://developers.openai.com/api/docs/guides/model-optimization) — Official managed-model customization guide used as a reminder that provider capabilities and terminology change over time.
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) — Official reference for using `Job` resources, restart policy, and backoff behavior for bounded training workloads.
- [Kubernetes GPU Scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) — Official reference for requesting GPU resources in Kubernetes workloads.
