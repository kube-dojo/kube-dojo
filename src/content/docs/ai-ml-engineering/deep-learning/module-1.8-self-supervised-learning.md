---
title: "Self-Supervised Learning"
description: "Decide when self-supervised pretraining is the right tool, choose between contrastive / masked / self-distillation families, design augmentation and evaluation protocols, and use DINOv2 / MAE off the shelf when pretraining your own would be wasteful."
slug: ai-ml-engineering/deep-learning/module-1.8-self-supervised-learning
sidebar:
  order: 8
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 90-120 minutes
> Prerequisites: [Module 1.4: CNNs & Computer Vision](module-1.4-cnns-computer-vision/), [Module 1.6: Backpropagation Deep Dive](module-1.6-backpropagation-deep-dive/), and [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../../machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration/).
Self-supervised learning, usually shortened to SSL, is the part of deep learning
where you pretrain a model without human labels by forcing it to predict structure
that already exists inside the data.
In vision, that usually means learning stable image features before you spend
scarce annotation effort on the final supervised task.
The reason practitioners care is not novelty.
It is leverage when labeled examples are scarce, expensive, stale, or badly
matched to the environment where the model will actually run.
The dominant pitfall is using SSL as a default upgrade when it is really a
regime-specific tool for label-scarce, domain-mismatched problems, not an
automatic improvement over a strong supervised baseline.

## Learning Outcomes
- **Decide** whether self-supervised pretraining is justified for a given data regime, annotation budget, and domain-shift profile.
- **Choose** between contrastive, masked-modeling, and self-distillation families by matching their inductive biases and infrastructure demands to the problem.
- **Design** augmentation, masking, and evaluation protocols that measure representation quality honestly instead of flattering a brittle pretraining recipe.
- **Evaluate** SSL backbones with linear probes, k-NN checks, and selective fine-tuning so that downstream decisions rest on evidence rather than striking visualizations.
- **Debug** a disappointing SSL transfer result by triaging batch size, augmentations, feature head usage, domain mismatch, and evaluation leakage before launching a larger run.

## Why This Module Matters
Picture an engineer joining a manufacturing vision team on a Monday morning.
The team has three thousand labeled defect images,
two hundred thousand unlabeled production images,
and a model card from a supervised ImageNet ResNet-50 baseline that has stalled
around seventy percent on the target defect classifier.
No one doubts that more labels would help.
The problem is that more labels would also require weeks of specialist review,
and the line is already running.
The first bad instinct in that room is to say,
"Self-supervised learning is the new standard, so we should pretrain our own
model immediately."
That is exactly the wrong starting point.
SSL is expensive relative to ordinary fine-tuning,
and it only earns that cost when labels are genuinely scarce,
the target domain differs enough from public data that transfer weakens,
and there is enough unlabeled in-domain data to teach a better representation.
That is why an off-the-shelf feature extractor often deserves the first trial.
The DINOv2 paper frames the goal clearly:
learn all-purpose visual features that work across image distributions and tasks
without fine-tuning when the pretraining data and recipe are strong enough
([Oquab, Darcet et al., 2023](https://arxiv.org/abs/2304.07193)).
If a public DINOv2 backbone already separates normal parts from defects well
under a frozen-feature linear probe,
the engineering answer is probably "use it" rather than "reproduce a research
pipeline."
The second bad instinct is to jump from "labels are scarce" to
"contrastive learning will save us."
SimCLR is foundational because it showed how much representation quality depends
on augmentations, projection heads, large batches, and long training, while also
showing that large-batch contrastive learning can be very effective
([Chen et al., 2020](https://arxiv.org/abs/2002.05709)).
But that same paper is the warning label.
Its published recipe benefited from very large batches,
so a team with one modest GPU should not expect paper-like behavior from an
unchanged SimCLR setup.
Masked Autoencoders offer a different angle.
MAE showed that vision transformers can learn useful representations by masking
a high proportion of image patches and reconstructing pixels,
using an encoder that processes only the visible subset and a lightweight decoder
that is discarded after pretraining
([He et al., 2021](https://arxiv.org/abs/2111.06377)).
That is attractive when you have lots of unlabeled images and want a pretext task
that does not depend on mining thousands of negatives every step.
This module matters because a practitioner rarely needs to invent a new SSL
method.
They need to decide whether SSL belongs in the plan at all,
which family fits the data and hardware,
how to evaluate transfer honestly,
and when public pretrained features already solve the business problem.
The dangerous mistake is not "failing to know every paper."
It is spending weeks on self-supervised pretraining when the real answer was
either a better supervised baseline or an off-the-shelf DINOv2 or MAE backbone.

## Section 1: What SSL is, and what it isn't
Self-supervised learning is pretraining without manual labels by asking the model
to predict structure already present in the data.
In language, BERT made this family of ideas mainstream by pretraining deep
bidirectional representations from unlabeled text through masked language
modeling
([Devlin et al., 2018](https://arxiv.org/abs/1810.04805)).
In vision, SimCLR showed that you could create a prediction task from two
augmented views of the same image and learn useful representations without class
labels
([Chen et al., 2020](https://arxiv.org/abs/2002.05709)).
That definition matters because SSL is not magic unsupervised intelligence.
It is an engineering trick for turning raw data into a training signal.
The trick can be good or bad depending on whether the invented pretext task
actually teaches invariances that help the downstream task.
If the pretext objective teaches the model to ignore the exact information your
production classifier needs,
you paid for pretraining and still lost signal.
SSL is also not the same thing as downstream task training.
The usual workflow is two-stage.
First you pretrain a general encoder on unlabeled data.
Then you evaluate that encoder with a frozen-feature linear probe or a selective
fine-tune on the labeled task.
The fact that these are separate stages is why evaluation discipline matters so
much.
You can have a beautiful pretraining loss curve and still learn a poor
representation.
The regime rule should stay boring.
Use SSL when labels are scarce or expensive,
unlabeled in-domain data is plentiful,
and public pretrained features do not transfer cleanly enough under honest
evaluation.
Do not use SSL when labels are already abundant,
a strong supervised or public pretrained model already performs well on the real
task,
or there is too little unlabeled data to justify the added machinery.
The practical corollary is that SSL is mostly about representation learning under
constraint.
When the constraint disappears,
the rationale often disappears with it.
That is why experienced teams ask about data regime first and architecture second.

## Section 2: Two big families plus a third
The first large family is contrastive SSL.
SimCLR and MoCo are the canonical examples.
They teach the model that two augmented views of the same underlying image should
map nearby in feature space while other images should map farther away.
This is conceptually simple and often powerful,
but it places pressure on augmentation design,
negative sampling,
or some other mechanism that resists trivial collapse.
BYOL and SimSiam live close to this family even though they do not rely on
explicit negatives in the same way.
The second large family is masked modeling.
BERT established the basic logic in language by hiding tokens and training the
model to infer missing content from context
([Devlin et al., 2018](https://arxiv.org/abs/1810.04805)).
MAE applied that philosophy to vision by masking image patches and reconstructing
the missing content,
while iBOT connected masked image modeling to richer token-level objectives
([He et al., 2021](https://arxiv.org/abs/2111.06377);
[Zhou et al., 2021](https://arxiv.org/abs/2111.07832)).
This family usually feels more natural to teams that already think in transformer
terms.
The third family is self-distillation.
DINO and DINOv2 train a student to match a teacher network that is itself updated
from the student through momentum rather than labels
([Caron et al., 2021](https://arxiv.org/abs/2104.14294);
[Oquab, Darcet et al., 2023](https://arxiv.org/abs/2304.07193)).
The surprising result is that a no-label,
no-negative training setup can still produce very strong visual features.
This family is especially important for practitioners because DINOv2 gives a
credible off-the-shelf starting point for many downstream vision problems.

## Section 3: SimCLR — the contrastive prototype
SimCLR is the cleanest place to understand modern vision SSL because almost every
later discussion either inherits its logic or reacts to its costs.
The pipeline begins by taking one image and creating two stochastic views of it.
Those two views are the positive pair.
Every other image in the batch provides negatives.
An encoder maps each view to a representation,
and a small projection head maps that representation into the space where the
contrastive loss is applied.
The loss is usually described as NT-Xent.
In prose,
it says that the representation of one view should assign high similarity to its
partner view and low similarity to the other views in the batch.
The temperature term controls how sharply the similarity scores are converted into
relative preference.
That makes the batch itself part of the learning signal.
If the batch is tiny,
the model sees only a weak and noisy contrastive dictionary each step.
SimCLR's paper is explicit about the ingredients that mattered most.
The authors report that augmentation composition plays a critical role,
that a learnable nonlinear transformation between representation and contrastive
loss improves learned representations,
and that contrastive learning benefits from larger batch sizes and longer training
than supervised learning
([Chen et al., 2020](https://arxiv.org/abs/2002.05709)).
In the published setup,
the best ImageNet experiments used a batch size of 4096 on TPUs.
That detail is not trivia.
It explains why naive "small GPU SimCLR" reproductions often disappoint.
The augmentation story deserves extra attention.
SimCLR made random resized crop,
color distortion,
and Gaussian blur central rather than decorative.
Those transforms define what the model is asked to treat as invariant.
If the downstream task really should ignore crop location and color shifts,
the augmentations help.
If the downstream task depends on subtle color or texture cues,
that same recipe can teach the wrong invariance.
The projection head is another detail that turns out not to be a detail.
The encoder learns a general representation.
The projection head shapes the space where the contrastive objective is easiest to
optimize.
After pretraining,
the projection head is usually discarded and the encoder output is reused for the
downstream task.
That separation lets the model sacrifice some information inside the contrastive
space without forcing the backbone representation itself to become equally narrow.

> **Pause and predict:** If the projection head helped SimCLR during pretraining, why is it usually discarded at transfer time, and what job was it doing that the backbone should not be forced to keep doing forever?

The answer is that the projection head acts as a task-specific buffer between the
general representation and the geometry demanded by the contrastive loss.
SimCLR showed that the nonlinear transformation improved downstream
representation quality precisely because the model could place some loss-specific
distortion in that head rather than in the backbone itself
([Chen et al., 2020](https://arxiv.org/abs/2002.05709)).
If you keep swapping between pre-projection and post-projection embeddings during
evaluation,
you are no longer testing one consistent representation.
Practically,
the backbone output is the reusable asset and the projection head is scaffolding.
The operational lesson is simple.
SimCLR is powerful when you can support its batch,
augmentation,
and training-budget demands.
It is not a free lunch for small hardware or fragile domains.

## Section 4: MoCo — momentum encoder and queue
MoCo keeps the contrastive idea but attacks SimCLR's hardware pressure directly.
The MoCo paper describes contrastive learning as dictionary look-up,
then builds a dynamic dictionary with a queue and a moving-averaged encoder
([He et al., 2019](https://arxiv.org/abs/1911.05722)).
That phrase captures both innovations.
The queue means you do not need all negatives to live in the current batch.
Instead of relying only on same-step examples,
MoCo stores a rolling bank of encoded keys from recent batches.
That enlarges the effective set of negatives without requiring the current step to
hold thousands of images in memory at once.
The moving-averaged encoder,
often called the momentum encoder,
matters because the keys entering that queue need to remain reasonably consistent.
If both sides of the contrastive pair changed too abruptly from step to step,
the dictionary would drift.
By updating the key encoder as a momentum-smoothed copy of the online encoder,
MoCo makes the target representations more stable across time
([He et al., 2019](https://arxiv.org/abs/1911.05722)).
This is why MoCo became important for practitioners outside the largest labs.
It offered a path to strong contrastive learning on smaller hardware than the
published SimCLR recipe demanded.
You still pay for careful augmentation and tuning,
but the queue reduces the need for extreme batches.
MoCo v2 then moved even closer to SimCLR's strongest recipe by adopting the
stronger augmentation stack and the projection head.
The broader lesson is that "contrastive" is not one fixed recipe.
It is a family whose success depends on how you stabilize positives,
source negatives,
and define invariance.
When you choose between SimCLR and MoCo,
you are partly choosing between two scaling strategies.
SimCLR asks for very large synchronous batches.
MoCo asks for a stable momentum target and a queue that approximates a large
dictionary over time.
On modest hardware,
that distinction often decides what is feasible.

## Section 5: BYOL and SimSiam — contrastive without negatives
BYOL and SimSiam matter because they violate a piece of contrastive common sense.
At first glance,
it seems obvious that a system trained to make representations similar without
explicit negatives should collapse to a constant vector.
These methods showed that asymmetric architecture choices can prevent that
collapse in practice.
The key pattern is an online branch,
a target branch,
and a deliberate asymmetry between them.
The online branch usually includes a predictor head.
The target branch is stop-gradient or otherwise prevented from receiving the same
updates directly.
Instead of comparing against many negatives,
the online branch learns to predict the target branch's representation of another
view of the same image.
That sounds suspicious until you remember how much structure is hidden inside the
optimization path itself.
The predictor,
the target-update rule,
and the stop-gradient path shape the space of trivial solutions.
The result was surprising because it relaxed the belief that strong vision SSL
must always be driven by massive negative sets.
For practitioners,
the main consequence is not that BYOL or SimSiam magically dominate every
contrastive baseline.
It is that the design space for SSL is broader than "bigger batch,
more negatives."
If your environment cannot support SimCLR-like batches,
an asymmetric non-contrastive method can still be worth exploring,
provided you evaluate transfer rigorously and do not assume collapse prevention is
automatic in every reimplementation.
The other practical consequence is social.
Once people see that collapse can be avoided without explicit negatives,
they start treating architectural details as replaceable.
They are not.
Online-versus-target asymmetry,
predictor placement,
and gradient blocking are the method.
Remove them casually and the stability story changes.

## Section 6: Masked Autoencoders for vision
MAE starts from a different pretraining question.
Instead of asking,
"Can two views of the same image be brought together in embedding space,"
it asks,
"Can the model infer missing visual content from the visible remainder."
The model sees a heavily masked image,
encodes only the visible patches,
and then uses a lightweight decoder to reconstruct the original pixels.
The MAE paper reports two ideas as central.
First,
the encoder operates only on the visible subset of patches,
without mask tokens.
Second,
a high masking ratio such as seventy-five percent creates a nontrivial
self-supervisory task
([He et al., 2021](https://arxiv.org/abs/2111.06377)).
Those ideas work together.
If only twenty-five percent of patches are visible,
the encoder processes far fewer tokens than a fully visible ViT would.
That is where the compute advantage comes from.
The encoder,
which is the expensive part,
sees only the unmasked patches.
The small decoder then handles reconstruction work over the full patch set.
The MAE paper says this asymmetric design accelerates training by three times or
more while improving accuracy
([He et al., 2021](https://arxiv.org/abs/2111.06377)).
The Hugging Face `ViTMAEForPreTraining` documentation exposes the pretraining
interface directly and notes a default `mask_ratio=0.75`
([Hugging Face ViTMAE docs](https://huggingface.co/docs/transformers/main/en/model_doc/vit_mae)).
This is why the decoder is intentionally small and temporary.
Its job is not to become the transferable feature extractor.
Its job is to make the reconstruction problem solvable during pretraining while
keeping most compute in the encoder where reusable features are learned.
After pretraining,
the decoder is discarded and the encoder is retained.

> **Stop and think:** Why is the MAE decoder kept lightweight, and why is the real efficiency gain tied to the encoder skipping masked patches rather than to the decoder reconstructing pixels?

The answer is that the decoder does not dominate cost.
The encoder does.
If the encoder had to process every mask token anyway,
you would lose most of the savings.
MAE gets efficiency because the expensive transformer stack processes only the
visible subset,
while the decoder is deliberately cheap enough that reconstructing the missing
content does not erase that benefit.
The small decoder is therefore an enabler of the training objective,
not the asset you plan to transfer.
MAE is especially attractive when you want a vision-transformer-native objective
that does not depend on giant negative sets.
It still requires significant unlabeled data and careful evaluation,
but it fits a different hardware and objective profile than SimCLR.

## Section 7: Masked language modeling, briefly
Masked modeling in vision makes more sense if you already understand why it worked
in language.
BERT pre-trained deep bidirectional representations from unlabeled text by jointly
conditioning on left and right context while recovering masked content
([Devlin et al., 2018](https://arxiv.org/abs/1810.04805)).
That is the conceptual ancestor of masked image modeling:
hide part of the input,
force the model to use context,
then transfer the encoder.
For downstream adaptation patterns on large pretrained transformer models,
cross-link rather than re-teach.
If you need the operational playbook for fine-tuning,
read [Module 1.1: Fine-Tuning LLMs](../../advanced-genai/module-1.1-fine-tuning-llms/).
If you need the parameter-efficiency mindset for selective updates versus frozen
backbones,
read [Module 1.2: LoRA & PEFT](../../advanced-genai/module-1.2-lora-parameter-efficient-fine-tuning/).
The details differ between language and vision,
but the question is the same:
when do you reuse a frozen representation and when do you update the model
itself.

## Section 8: Self-distillation — DINO and DINOv2
DINO replaces explicit labels and explicit negatives with a student-teacher
training loop.
The teacher is updated from the student through momentum.
The student sees augmented views and learns to match the teacher's outputs for
corresponding views.
Centering and sharpening on the teacher side help stabilize the target
distribution,
which is one reason DINO can avoid collapse without the usual contrastive recipe
([Caron et al., 2021](https://arxiv.org/abs/2104.14294)).
The original DINO result mattered for two reasons.
First,
it showed that self-distillation with vision transformers could learn strong
representations without labels or negatives.
Second,
it produced striking emergent attention behavior that made it visually obvious
the model had learned object-centric structure.
That visual story is memorable,
but it is not your evaluation protocol.
Attention maps can be suggestive and still fail to deliver the transfer accuracy
your downstream task requires.
DINOv2 takes the same general direction and scales it into a practical foundation
feature story.
The paper says the goal is all-purpose visual features that work across image
distributions and tasks without fine-tuning,
and it describes combining different techniques to scale pretraining in data and
model size while stabilizing training
([Oquab, Darcet et al., 2023](https://arxiv.org/abs/2304.07193)).
It also emphasizes curated diverse data rather than a purely uncurated crawl,
plus distillation from a larger ViT into smaller deployable models.
In practice,
DINOv2 is the default recommendation for most teams facing a new vision
downstream task with limited labels.
The Hugging Face DINOv2 docs expose `AutoModel.from_pretrained("facebook/dinov2-base")`
and `AutoImageProcessor.from_pretrained("facebook/dinov2-base")`,
returning standard transformer outputs that include token-level hidden states and
pooling interfaces
([Hugging Face DINOv2 docs](https://huggingface.co/docs/transformers/main/en/model_doc/dinov2)).
That means you can test the backbone on your own data quickly,
without rebuilding the pretraining stack.
The docs also make an operationally important point:
you can obtain a CLS-like pooled representation and per-patch features from the
same model interface
([Hugging Face DINOv2 docs](https://huggingface.co/docs/transformers/main/en/model_doc/dinov2)).
That gives you multiple downstream entry points,
from image-level classification to patch-level inspection.
It does not mean every task should use every output.
It means you can experiment under a stable pretrained API.
DINOv2 also absorbed ideas from related masked and distillation work,
including iBOT-style token supervision,
and the official codebase includes details such as register tokens that matter
for reproducing paper behavior
([DINOv2 codebase](https://github.com/facebookresearch/dinov2)).
Most practitioners should treat those details as a reason to prefer public
weights rather than as an invitation to rebuild the recipe casually.
The pitfall to remember is simple.
DINO attention visualizations are compelling.
Production decisions should still be made on downstream metrics,
starting with frozen-feature linear probes and only then selective fine-tuning.
If the probe is bad,
the picture is not evidence.

## Section 9: iBOT, briefly
iBOT is useful to know because it sits between the neat families people like to
teach.
The paper describes a framework that performs masked prediction with an online
tokenizer and combines self-distillation on masked patch tokens with
self-distillation on the class token
([Zhou et al., 2021](https://arxiv.org/abs/2111.07832)).
That makes it a bridge between masked image modeling and DINO-style
self-distillation.
Practically,
iBOT reminds you that the family boundaries are not rigid.
Strong modern systems often mix ideas rather than choosing one slogan.
That is another reason off-the-shelf backbones have so much value.
The best recipe is often a hybrid that is much harder to re-create faithfully
than a high-level survey makes it sound.

## Section 10: Linear probe vs fine-tune evaluation
A frozen-feature linear probe asks one narrow question:
how linearly useful are the representations already learned by the encoder.
You freeze the backbone,
extract embeddings,
train a linear classifier on top,
and evaluate on a clean validation or test split.
That makes it the best first read on representation quality because the head is
not allowed to hide backbone weakness behind full-model adaptation.
Fine-tuning asks a different question.
What is the best task performance you can achieve after letting the encoder move.
That matters for deployment,
but it is a weaker tool for comparing representations because a strong optimizer
and enough labeled data can erase meaningful differences between two backbones.
A model that linear-probes poorly but fine-tunes well may still require more
labeled data,
longer iteration loops,
or more unstable hyperparameter searches than a backbone with better frozen
features.

k-NN evaluation is a faster proxy.
Once you have embeddings,
you can ask whether nearest neighbors in feature space tend to share labels.
It is cheap,
often directionally useful,
and good for quick sanity checks before you invest in a full probe.
It is not a replacement for a carefully tuned linear probe,
but it can catch obviously broken features early.
This is the same evaluation-discipline problem you already saw in
[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../../machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration/).
Do not leak test information into representation tuning.
Do not over-read one split.
Do not compare one model by linear probe and another by full fine-tune and then
pretend the numbers answer the same question.
There is also a variance trap here that looks familiar if you remember how RL
evaluation can be distorted by single-seed stories in
[Module 1.1: RL Practitioner Foundations](../../reinforcement-learning/module-1.1-rl-practitioner-foundations/).
The linear probe head can move by several points across random seeds,
especially on small labeled datasets.
If you plan to make a high-cost pretraining decision from a two-point difference,
run multiple seeds for the probe and report the spread.
Evaluation determines whether SSL remains engineering or turns into ritual.
If you skip the probe and only inspect the final fine-tune number,
you lose the ability to answer the core question:
did pretraining improve the representation,
or did the downstream optimizer simply work around a mediocre one.

> **Pause and decide:** A teammate reports "we tried DINOv2 and ResNet50 ImageNet pretraining and DINOv2 wins by 4 points after fine-tuning the whole network on our labels." Should you accept that as evidence DINOv2 produces better representations for your problem, or is the comparison ambiguous? What single follow-up experiment would resolve it? (Answer: ambiguous. Full fine-tuning lets the downstream optimizer recover from a worse starting representation given enough labels and steps; the gap may reflect representation quality, capacity, or fine-tune budget. The follow-up is a frozen-feature linear probe with the same labels — that isolates representation quality from fine-tune dynamics.)

## Section 11: The pretraining-then-finetune workflow
The practitioner playbook should start with the cheapest credible option.
Step one is to try a public pretrained backbone first.
For current vision tasks,
that usually means DINOv2 small or base sized variants,
loaded through Hugging Face or `timm`,
followed by a frozen-feature linear probe on your labeled data
([Hugging Face DINOv2 docs](https://huggingface.co/docs/transformers/main/en/model_doc/dinov2);
[timm docs](https://huggingface.co/docs/timm/index)).
If the backbone already separates your classes cleanly,
there is nothing virtuous about more pretraining.
Step two is selective adaptation rather than full reinvention.
If the probe is close but not enough,
fine-tune the classifier head and perhaps the last few transformer blocks.
This is the same strategic question as parameter-efficient adaptation in language:
how much of the model really needs to move to capture domain specifics.
For that mindset,
revisit [Module 1.2: LoRA & PEFT](../../advanced-genai/module-1.2-lora-parameter-efficient-fine-tuning/).
You may not literally apply LoRA in every vision stack,
but the discipline of minimal effective adaptation still holds.
Step three is the expensive branch.
Only if public backbones fail under honest probing and selective fine-tuning,
and only if you have strong unlabeled in-domain data,
should you consider pretraining your own SSL encoder.
For SimCLR,
MoCo,
BYOL,
and DINO-style experimentation,
LightlySSL provides a practical library surface for self-supervised workflows
([LightlySSL docs](https://docs.lightly.ai/self-supervised-learning/)).
For MAE and DINOv2 reproduction-grade work,
the official Meta codebases are the references
([MAE codebase](https://github.com/facebookresearch/mae);
[DINOv2 codebase](https://github.com/facebookresearch/dinov2)).
This order is not conservative for the sake of being conservative.
It is economically honest.
Most teams do not need their own SSL pretraining pipeline.
They need evidence that a public backbone is insufficient before they accept the
time,
cost,
and evaluation burden of custom pretraining.

## Section 12: Ecosystem and tooling
PyTorch remains the default execution layer for serious SSL work.
Its tensor and module APIs are the substrate beneath nearly every public
reference implementation you are likely to touch
([PyTorch docs](https://docs.pytorch.org/docs/stable/index.html)).
That matters less as branding than as interoperability.
If the model weights,
data pipeline,
and evaluation loop all live comfortably in PyTorch,
you can move between official code and your downstream task without translation
friction.
Hugging Face Transformers is the fastest route to using public SSL backbones
without rebuilding research code.
The DINOv2 and ViTMAE model docs expose production-friendly pretrained loading,
standard outputs,
and task-specific classes for pretraining or feature extraction
([Hugging Face docs index](https://huggingface.co/docs/transformers/index);
[Hugging Face DINOv2 docs](https://huggingface.co/docs/transformers/main/en/model_doc/dinov2);
[Hugging Face ViTMAE docs](https://huggingface.co/docs/transformers/main/en/model_doc/vit_mae)).

`timm` remains a practical backbone library for vision experiments and pretrained
model access,
especially when you want a quick supervised or self-supervised baseline under a
consistent interface
([timm docs](https://huggingface.co/docs/timm/index)).
It is not a replacement for source-aware evaluation.
It is a convenience layer that lowers the cost of trying a strong backbone before
you consider training your own.
LightlySSL fits a different niche.
It provides self-supervised learning building blocks,
examples,
and method coverage for families such as SimCLR,
BYOL,
DINO,
iBOT,
and MAE
([LightlySSL docs](https://docs.lightly.ai/self-supervised-learning/)).
That is useful when the off-the-shelf model failed and you need a controlled
experimentation surface,
not a from-scratch rewrite of every paper.
The stance of this module is therefore intentionally narrow.
Most teams should begin with pretrained DINOv2 or MAE-style backbones off the
shelf.
Pretrain your own SSL model only after a linear probe and selective fine-tune show
that the public option really does not transfer.

## Section 13: When SSL is the wrong tool
The first failure regime is abundant labels.
If you already have a large,
representative,
well-maintained labeled dataset for the target task,
SSL usually adds process without adding decisive information.
The model can learn directly from the supervised objective you actually care
about.
At that point the marginal gain from an intermediate pretext task is often
smaller than the gain from better curation,
better class balancing,
or better evaluation.
The second failure regime is "public pretrained already covers the domain."
If an off-the-shelf DINOv2 or supervised ViT probe performs strongly on your data,
custom SSL pretraining is usually wasteful.
You should spend your effort on downstream calibration,
failure analysis,
and operational thresholds.
The point of transfer learning is to reuse representation work that has already
been paid for.
The third failure regime is lack of unlabeled domain data.
SSL without labels still needs data.
If you have only a few hundred or a few thousand unlabeled examples,
the pretraining stage may be too small to teach anything more useful than the
public backbone already knows.
In that setting,
better augmentation,
careful supervision,
or classical feature engineering from
[Module 1.4: Feature Engineering & Preprocessing](../../machine-learning/module-1.4-feature-engineering-and-preprocessing/)
can outperform an underpowered pretraining plan.
The fourth failure regime is tabular data.
Modern SSL ideas exist outside vision and language,
but this module's families are not your default tool for ordinary tabular
classification or small structured datasets.
If the problem is really about low-dimensional signals,
distance structure,
or classical decision boundaries,
the better references are
[Module 1.10: Dimensionality Reduction](../../machine-learning/module-1.10-dimensionality-reduction/)
and [Module 1.7: Naive Bayes, k-NN and SVMs](../../machine-learning/module-1.7-naive-bayes-knn-and-svms/).
Do not force a vision-style SSL story onto data that does not want it.
The fifth failure regime is sequential decision-making.
If the core difficulty is that actions change future states and rewards arrive
over time,
that is an RL problem,
not a self-supervised image-pretraining problem.
Representation learning can still appear inside the pipeline,
but the main logic belongs to
[Module 1.1: RL Practitioner Foundations](../../reinforcement-learning/module-1.1-rl-practitioner-foundations/).
Confusing these problem classes leads to expensive category errors.
The sixth failure regime is frontier-scale generative model training.
Large language model pretraining is self-supervised in a broad sense,
but the economics,
data contracts,
and alignment pipeline are radically different from the practitioner vision
regimes in this module.
If that is your problem,
you want [Module 1.1: Fine-Tuning LLMs](../../advanced-genai/module-1.1-fine-tuning-llms/)
for adaptation patterns and [Module 1.4: RLHF & Alignment](../../advanced-genai/module-1.4-rlhf-alignment/)
for post-pretraining behavior shaping.
Do not treat "SSL" as one undifferentiated recipe across all of deep learning.

## Decision-keyed regime table
If you compress the module into one operator-facing artifact,
it should be a regime table rather than a slogan.
The table below is deliberately decision-keyed.
It starts from the data situation,
then tells you what to do and why.

| Situation | Use | Why |
|---|---|---|
| Abundant labels and a public pretrained backbone already covers the domain | Fine-tune the supervised or public pretrained model | SSL adds cost without solving a real data bottleneck |
| Scarce labels but a public pretrained backbone already covers the domain | Start with the public pretrained model and verify with a linear probe | You may already have enough representation quality without custom pretraining |
| Scarce labels, lots of unlabeled domain data, and public pretrained features look domain-mismatched | Try DINOv2 off the shelf first, then probe honestly | Public all-purpose features are cheaper to test than a custom SSL run |
| Very scarce labels, lots of unlabeled domain data, and DINOv2 fails under a linear probe | Consider MAE or DINO-style domain pretraining via LightlySSL or official code | Now the unlabeled data may be able to teach task-relevant invariances the public model missed |
| Mostly tabular or small structured data | Do not default to vision-style SSL; see [Module 1.10: Dimensionality Reduction](../../machine-learning/module-1.10-dimensionality-reduction/) and [Module 1.7: Naive Bayes, k-NN and SVMs](../../machine-learning/module-1.7-naive-bayes-knn-and-svms/) | The representation and evaluation assumptions are different |
| Sequential control or decision-making under delayed rewards | Do not use this module as the main tool; see [Module 1.1: RL Practitioner Foundations](../../reinforcement-learning/module-1.1-rl-practitioner-foundations/) | The core problem is policy learning, not static representation pretraining |

## Did You Know?
1. SimCLR's abstract explicitly says that the composition of data augmentations
plays a critical role and that larger batch sizes help contrastive learning
([SimCLR](https://arxiv.org/abs/2002.05709)).
2. MAE's paper reports that masking a high proportion such as seventy-five percent
creates a meaningful self-supervisory task and that the asymmetric encoder-decoder
design accelerates training by three times or more
([MAE](https://arxiv.org/abs/2111.06377)).
3. DINOv2 frames its goal as learning all-purpose visual features that work across
image distributions and tasks without fine-tuning when trained at sufficient scale
([DINOv2](https://arxiv.org/abs/2304.07193)).
4. The Hugging Face DINOv2 interface exposes pretrained loading through
`AutoModel` and `AutoImageProcessor`,
which is one reason linear-probe evaluation can be set up quickly on custom data
([Hugging Face DINOv2 docs](https://huggingface.co/docs/transformers/main/en/model_doc/dinov2)).

## Common Mistakes
| Mistake | Why It Breaks | Better Practice |
|---|---|---|
| Using SSL when labels are abundant and a supervised pretrained model already works | You add pretraining cost without addressing the actual bottleneck | Start from the simplest strong supervised or public pretrained baseline and require evidence before escalating |
| Running SimCLR with batch 64 on one GPU and expecting paper-level results | SimCLR's strongest published behavior depended on very large batches and carefully tuned augmentations | Treat small-batch contrastive runs as new experiments, not faithful reproductions, and consider MoCo or public backbones first |
| Treating fine-tune accuracy as the only evaluation signal | Full fine-tuning can hide representation-quality differences between backbones | Run frozen-feature linear probes first, then fine-tune only after you know what the encoder already gives you |
| Reusing SimCLR's augmentation recipe unchanged on a domain like grayscale medical images | Color jitter or aggressive crops may erase signal the downstream task needs | Redesign augmentations around domain-valid invariances and verify with ablations |
| Ignoring the projection head and mixing pre-projection with post-projection embeddings | You stop measuring one consistent representation and can report misleading comparisons | Decide which feature output you are evaluating and keep that choice fixed across experiments |
| Treating DINO attention maps as proof of production value | Striking visualization is not the same as downstream task utility | Judge the backbone by probe and fine-tune metrics on the target task |
| Pretraining your own SSL model when DINOv2 off the shelf already works | You spend time rebuilding a representation you already have | Prefer public weights first and only pretrain when honest transfer evaluation says you must |

## Quiz
1. A surface-inspection team has 4,000 labeled images of scratches,
180,000 unlabeled factory images,
and a DINOv2 linear probe that already reaches the business threshold.
Should they launch a custom MAE pretraining job next?
<details>
<summary>Answer</summary>
No.
The probe result says the public backbone already provides enough representation
quality for the stated requirement.
The correct next step is downstream validation,
threshold setting,
and maybe selective fine-tuning if there is a measurable reason.
Custom SSL pretraining would be an unjustified cost at this point.
</details>

2. A researcher trains SimCLR on histopathology tiles with heavy color jitter
copied from the paper recipe,
then finds that transfer performance on stain-sensitive labels is poor.
What is the first diagnosis?
<details>
<summary>Answer</summary>
The pretext augmentations likely taught invariances that conflict with the
downstream task.
If color carries signal,
aggressive color jitter can erase exactly what the classifier later needs.
The first fix is not a larger model.
It is redesigning augmentations around domain-valid transformations and rerunning
the evaluation.
</details>

3. A team has only 1,200 labeled satellite images,
250,000 unlabeled in-domain images,
and a public ImageNet backbone that linear-probes badly.
What should they try before building a full SimCLR stack from scratch?
<details>
<summary>Answer</summary>
They should first test an off-the-shelf DINOv2 backbone under the same linear
probe.
If that still fails,
the evidence for domain mismatch becomes stronger and a custom MAE or DINO-style
pretraining run becomes more defensible.
The decision order matters because DINOv2 is much cheaper to test than a custom
pipeline.
</details>

4. Two SSL backbones end up with similar full fine-tune accuracy,
but one is three points better under a frozen linear probe.
Which one has the stronger representation signal?
<details>
<summary>Answer</summary>
The backbone with the stronger linear probe.
Fine-tuning measures what the full stack can become with enough adaptation.
The probe measures what is already present in the representation.
If probe quality matters for label efficiency or deployment simplicity,
the better probe is meaningful even when fine-tune numbers look similar.
</details>

5. A small lab wants to reproduce SimCLR exactly on one workstation with limited
VRAM.
The run is unstable and underperforms.
What family-level alternative should they consider and why?
<details>
<summary>Answer</summary>
MoCo is the most obvious family-level alternative because its queue and momentum
encoder reduce the need for extremely large current-step batches.
The problem is not simply "bad luck."
It is that the hardware profile does not match the original SimCLR scaling story.
</details>

6. A manager is impressed by DINO attention maps that highlight object regions and
wants to skip probe evaluation.
Why is that a mistake?
<details>
<summary>Answer</summary>
Because attention visualization is not a downstream metric.
It can suggest useful structure,
but it does not answer whether the backbone separates the target classes under the
real labeling regime.
A linear probe or task-specific fine-tune is still required for a decision-grade
evaluation.
</details>

7. A team with 30,000 labeled examples and 40,000 unlabeled examples in a mature
consumer-photo domain is debating custom SSL pretraining.
What should be the skeptical default?
<details>
<summary>Answer</summary>
Assume SSL is unnecessary until proven otherwise.
That amount of labeled data plus a mature public vision domain usually means a
strong supervised or public pretrained backbone deserves first priority.
The burden of proof is on the custom SSL plan,
not on the baseline.
</details>

## Hands-On Exercise
The goal of this exercise is to make one evidence-based decision:
does an off-the-shelf DINOv2 backbone already solve enough of your target problem
that custom SSL pretraining would be wasteful.

- [ ] Pick a small labeled target dataset with a clean train and validation split.
  Keep it small enough that embedding extraction and probe training are fast.

- [ ] Load the DINOv2 base model and image processor from Hugging Face.
  Use the standard API rather than custom wrappers.

```python
import torch
from transformers import AutoImageProcessor, AutoModel

device = "cuda" if torch.cuda.is_available() else "cpu"
processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
model = AutoModel.from_pretrained("facebook/dinov2-base").to(device)
model.eval()
```

- [ ] Extract one embedding per image on the train and validation splits.
  Be explicit about whether you use the pooled output,
  the first token,
  or an averaged hidden-state representation.
  Keep that choice fixed for the rest of the exercise.

```python
import torch

def embed_batch(images):
    inputs = processor(images=images, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0]
```

- [ ] Train a linear probe on the frozen embeddings.
  Report validation accuracy,
  macro F1 if the classes are imbalanced,
  and at least a couple of random seeds if the dataset is small.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class LinearProbe(nn.Module):
    def __init__(self, in_dim, num_classes):
        super().__init__()
        self.head = nn.Linear(in_dim, num_classes)

    def forward(self, x):
        return self.head(x)
```

- [ ] Compare the linear probe to a k-NN evaluation on the same embeddings.
  If k-NN and the probe disagree sharply,
  inspect normalization,
  class imbalance,
  and feature-choice consistency before drawing a conclusion.

- [ ] Optionally fine-tune the last transformer block plus a classifier head.
  Do not jump straight to full-model fine-tuning.
  The purpose is to see whether small adaptation closes the gap enough to avoid
  custom pretraining.

- [ ] Write a short decision memo.
  State whether the frozen probe is already good enough,
  whether selective fine-tuning changes the answer,
  and whether custom SSL pretraining on your unlabeled data would likely be worth
  attempting.
  Your memo should explicitly say what evidence would justify escalating to MAE,
  DINO,
  or MoCo rather than assuming that escalation by default.

## Sources
- [PyTorch documentation index](https://docs.pytorch.org/docs/stable/index.html): canonical reference for tensors, modules, autograd, and model execution APIs used in SSL workflows.
- [Hugging Face Transformers documentation index](https://huggingface.co/docs/transformers/index): central API reference for pretrained transformer models and processors used in transfer workflows.
- [Hugging Face DINOv2 documentation](https://huggingface.co/docs/transformers/main/en/model_doc/dinov2): documents `AutoModel.from_pretrained("facebook/dinov2-base")` and standard model outputs for image and patch features.
- [Hugging Face ViTMAE documentation](https://huggingface.co/docs/transformers/main/en/model_doc/vit_mae): documents `ViTMAEForPreTraining` and the default `mask_ratio=0.75` interface for MAE pretraining.
- [timm documentation](https://huggingface.co/docs/timm/index): reference for the pretrained vision backbone ecosystem commonly used for baseline comparisons.
- [LightlySSL documentation](https://docs.lightly.ai/self-supervised-learning/): practical documentation for self-supervised learning methods including SimCLR, BYOL, DINO, iBOT, and MAE workflows.
- [SimCLR](https://arxiv.org/abs/2002.05709): showed that augmentation composition, a nonlinear projection head, and large batches are central to contrastive representation learning.
- [MoCo](https://arxiv.org/abs/1911.05722): introduced a moving-averaged encoder and a queue-based dictionary to make contrastive learning practical without extreme batch sizes.
- [DINO](https://arxiv.org/abs/2104.14294): established self-distillation with vision transformers as a strong no-label, no-negative route to visual representations.
- [DINOv2](https://arxiv.org/abs/2304.07193): argued that sufficiently scaled self-supervised pretraining can produce all-purpose visual features across tasks and image distributions.
- [MAE](https://arxiv.org/abs/2111.06377): showed that masking seventy-five percent of patches and encoding only visible patches yields efficient and strong vision pretraining.
- [BERT](https://arxiv.org/abs/1810.04805): established masked language modeling as a powerful pretraining pattern for unlabeled text representations.
- [iBOT](https://arxiv.org/abs/2111.07832): connected masked image modeling and self-distillation through online tokenization and patch-level prediction.
- [DINO reference implementation](https://github.com/facebookresearch/dino): official codebase for the original DINO method.
- [MAE reference implementation](https://github.com/facebookresearch/mae): official codebase for Masked Autoencoders in vision.
- [DINOv2 reference implementation](https://github.com/facebookresearch/dinov2): official codebase for DINOv2, including reproduction details beyond the high-level paper summary.

## Next Module
[Module 1.9: Graph Neural Networks](module-1.9-graph-neural-networks/)
