---
title: "Vision AI"
slug: ai-ml-engineering/multimodal-ai/module-1.2-vision-ai
sidebar:
  order: 903
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6 hours | Prerequisites: [Module 1.1: Voice and Audio AI](../module-1.1-voice-audio-ai/)

## Learning Outcomes

- **Explain** how Vision Transformers convert images into patch tokens, use positional embeddings, and rely on attention rather than convolutional locality.
- **Apply** CLIP-style contrastive embeddings for zero-shot classification and natural-language image search while recognizing where similarity is not the same as grounded reasoning.
- **Analyze** common VLM architectures, including the frozen vision encoder, projection connector, and language-model attention pattern used by BLIP-2 and LLaVA-style systems.
- **Design** multimodal prompts and production pipelines for OCR, structured extraction, grounding, batching, preprocessing, caching, and human review.
- **Evaluate** reliability risks such as hallucinated layout, OCR transposition, spatial confusion, prompt overloading, and vendor-specific cost or latency changes.

## Why This Module Matters

Hypothetical scenario: a support operations team adds a vision-language model to its returns workflow. The first demo looks excellent: upload a photo of a damaged shipment, ask for a description, and receive a tidy paragraph that mentions the torn corner, the visible product label, and the likely replacement category. The prototype moves quickly because the model accepts images and text in one request, so the team does not need to train a separate detector, OCR model, layout parser, and language model before showing value. Two weeks later the same system starts routing valid returns to manual review because glossy packaging creates reflections that the model interprets as damage. The model has not "seen" the business rule; it has converted visual tokens into a plausible language answer.

That gap is the reason vision AI matters for AI/ML engineers. A modern visual system is no longer just an image classifier that chooses from a fixed label set. It may retrieve product photos by natural language, read a scanned invoice, compare a build diagram with an implementation screenshot, describe an accessibility image, or answer a user question about a chart. Each task asks the model to bind pixels, text, spatial layout, and domain instructions into one decision. The engineering challenge is to understand how the binding works well enough to design prompts, preprocess images, choose model families, measure failures, and add guardrails where generative answers are too unreliable.

The durable spine of this module is not a particular vendor API or model name. Those change quickly. The durable spine is the sequence of ideas that made vision-language systems practical: Vision Transformers turn images into token sequences, CLIP-style contrastive learning aligns image and text embeddings, VLM architectures connect visual features to a language model, multimodal prompts steer attention and output shape, and production systems control image quality, latency, cost, and verification. When you understand those layers, you can evaluate a new provider announcement without treating it as magic.

## Part 1: From Pixels to Vision Tokens

Traditional computer vision was dominated for years by convolutional neural networks because convolutions express a useful prior: nearby pixels usually matter together. A convolutional filter slides across an image and looks for local patterns such as edges, corners, textures, and eventually larger shapes. This works extremely well for many tasks because images are not random grids; objects have locality, translation matters, and early features often repeat across the frame. The tradeoff is that global relationships are built gradually. A small patch in the top left and another patch in the bottom right influence each other only after many layers, pooling steps, or architectural additions.

The Vision Transformer changes the default assumption. Instead of starting with local filters, it starts by treating an image as a sequence of patches, much like a language transformer treats a sentence as a sequence of tokens. A common teaching example is a 224 by 224 RGB image split into 16 by 16 patches. That produces a 14 by 14 grid, or 196 patch tokens, and each patch carries the pixel information for a small square of the image. The model linearly projects each flattened patch into an embedding vector, adds a positional embedding so the transformer knows where the patch came from, and feeds the resulting sequence into self-attention layers.

The patch embedding step is easy to underestimate because it looks like a preprocessing detail, but it defines what the transformer can attend over. If the patch size is large, the sequence is short and attention is cheaper, but fine visual detail may be compressed before the model can reason about it. If the patch size is small, the sequence preserves more local detail, but attention becomes more expensive because every token can attend to every other token. This is the same scaling pressure you already know from language models: longer sequences give the model more evidence, but attention cost grows quickly as sequence length rises.

The `[CLS]` token in a ViT is a learnable summary token that travels through the transformer alongside the image patches. During classification training, the final representation of this token becomes the input to the classifier head. You can think of it as a place where the model learns to gather task-relevant evidence from the patch sequence, although the model is not literally storing a human-readable explanation there. For dense tasks such as detection or segmentation, architectures often need different heads or feature extraction strategies because one global summary is not enough to locate many objects precisely.

```text
Image tensor
  |
  | split into non-overlapping patches
  v
Patch vectors + position embeddings + CLS token
  |
  | transformer encoder self-attention
  v
Contextual visual token representations
  |
  | task head or connector
  v
Classification, retrieval, captioning, or VLM input
```

The key difference between ViTs and CNNs is inductive bias. A CNN assumes locality and translation-friendly filters from the beginning, which helps when data is limited because the architecture already matches many visual patterns. A pure ViT has weaker built-in visual assumptions. It can learn global relationships directly through attention, but it often needs more data, stronger augmentation, or large-scale pretraining before it catches up. This explains why the ViT paper emphasized scale: the architecture is flexible, but flexibility is not free.

This also explains why modern systems often combine ideas rather than treating CNNs and transformers as religious camps. Some vision models keep convolutional stems for early feature extraction, some use hierarchical transformer stages, and some use specialized attention windows for efficiency. As an engineer, the practical question is not "CNN or transformer forever?" The practical question is what visual evidence your task needs, how much data you have, what latency budget you must hit, and whether global relationships matter enough to pay for broader attention.

## Part 2: CLIP and Shared Image-Text Spaces

CLIP made a different move from ordinary image classification. Instead of training an image model to predict one fixed label from a curated label set, CLIP trains an image encoder and a text encoder together so matching image-text pairs land near each other in a shared embedding space. During training, the model receives a batch of images and their associated captions. It computes image embeddings, text embeddings, and a similarity matrix where correct pairs should score higher than mismatched pairs. The learning signal is contrastive: pull matching pairs together and push non-matching pairs apart.

That shared space is what makes zero-shot classification possible. Suppose you have an image and three candidate labels: "a photo of a forklift", "a photo of a bicycle", and "a photo of a server rack". You encode the image once, encode each text prompt, and choose the text embedding with the highest similarity to the image embedding. No new classifier head is required for those categories. The category definitions are supplied by language, which means prompt wording, synonyms, and domain vocabulary can change the result.

```text
Images in batch       Captions in batch
      |                     |
      v                     v
Vision encoder        Text encoder
      |                     |
      v                     v
Image embeddings      Text embeddings
      \_____________________/
             |
             v
Similarity matrix: correct image-caption pairs should score highest
```

CLIP is powerful because it changes the interface from "train a classifier for each taxonomy" to "describe the visual concept in text." That makes it useful for image search, deduplication, weak labeling, content triage, product matching, and dataset exploration. You can embed a large image corpus offline, embed a text query at request time, and retrieve visually relevant candidates by cosine similarity. This is often a much better product primitive than a hard classifier because users rarely search with the exact labels your team used during training.

The limitation is that similarity is not the same as understanding. A CLIP-style model can tell you that an image is closer to "a damaged box" than to "a pristine box", but it does not inherently produce a faithful damage report, read every character on a label, or prove that an object is in a safe physical state. It also inherits biases from the image-text pairs used for training. If a concept is common in captions but visually subtle, the model may learn a useful shortcut rather than the visual distinction you care about. If your business decision needs exact evidence, CLIP retrieval should usually feed a second verification step rather than act alone.

Prompt design matters even for zero-shot CLIP. "dog", "a dog", "a photo of a dog", and "a product photo of a dog toy" are not equivalent descriptions. The text encoder embeds the whole phrase, so the surrounding context changes the decision boundary. In practice, teams often test prompt templates, average multiple templates, and add negative prompts for confusing classes. A warehouse model distinguishing "empty shelf", "stocked shelf", and "blocked aisle" may need prompts that reflect the camera angle and environment, not generic web-photo labels.

SigLIP and OpenCLIP illustrate the broader family rather than a replacement story. SigLIP explores a sigmoid loss that avoids requiring a global softmax over the whole batch, while OpenCLIP provides an open implementation and training ecosystem for CLIP-like models. The durable lesson is that image-text representation learning is now a reusable substrate. Whether the implementation uses the original CLIP loss, a sigmoid variant, or a newer training recipe, the engineering pattern remains: build embeddings that make text queries and images comparable.

## Part 3: Vision-Language Models

A Vision-Language Model goes beyond retrieval by connecting visual evidence to a generative language model. The common pattern is a vision encoder, a connector, and an LLM. The vision encoder turns the image into visual features. The connector projects those features into the embedding space expected by the language model. The language model then attends over a combined context containing visual embeddings and text prompt tokens, producing a natural-language answer, structured JSON, or tool call instruction.

BLIP-2 is a useful reference architecture because it makes the connector explicit. Rather than retraining every component end to end, it uses frozen pretrained image encoders and frozen large language models, then learns a lightweight bridge called a Querying Transformer. The point is not that every production VLM literally uses BLIP-2. The point is that bridging modalities is an engineering problem: visual features have one geometry, language tokens have another, and the connector decides what information crosses the boundary.

LLaVA demonstrates another influential pattern: connect a pretrained CLIP visual encoder to an instruction-tuned language model through a projection layer, then train on multimodal instruction-following data. This makes the model behave more like an assistant than a classifier. You can ask, "What is unusual about this diagram?" or "Which item in the photo violates the checklist?" and receive a conversational answer. That assistant behavior is convenient, but it is also where hallucination enters. The language model can produce a fluent answer even when the visual evidence is weak.

```text
Image
  |
  v
Vision encoder
  |
  v
Visual feature tokens
  |
  v
Projection connector or query transformer
  |
  v
LLM-compatible visual embeddings + user text tokens
  |
  v
Generative language model
  |
  v
Answer, JSON, classification rationale, or next action
```

Images become "tokens" in a conceptual sense, but the details vary by model family. Some systems represent an image as many patch-derived embeddings. Some resample visual features into a smaller fixed set of tokens. Some use dynamic resolution so a document page receives more tokens than a simple thumbnail. The important production consequence is that image size, aspect ratio, detail level, and the number of images can change latency and cost. If you do not control preprocessing, a user can accidentally turn a simple request into an expensive multimodal context.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> | Family or project | Durable role in this module | Volatile detail to verify before use |
> |---|---|---|
> | OpenAI vision-capable models | Hosted APIs for image inputs, visual reasoning, and structured multimodal responses | Current model IDs, image token accounting, pricing, and preferred endpoint |
> | Anthropic Claude vision | Hosted image analysis through the Messages API and related Claude surfaces | Current model IDs, request-size limits, supported media types, and partner-platform constraints |
> | Google Gemini vision | Hosted multimodal image tasks including captioning, classification, visual QA, and object detection-style use cases | Current model IDs, file upload rules, region or product availability, and quota behavior |
> | Qwen-VL family | Open vision-language model family with document, chart, grounding, and agentic visual examples in its published materials | Current checkpoint names, licenses, serving stack, hardware needs, and safety policy |
> | LLaVA family | Research and open-source pattern for visual instruction tuning with a vision encoder connected to an LLM | Current forks, licenses, base models, benchmark claims, and inference requirements |
> | BLIP-2-style architectures | Reference pattern for frozen visual encoders, frozen LLMs, and a learned modality bridge | Which components are frozen, which connector is trained, and whether the released checkpoint fits the task |
>
> This table is illustrative, not a ranking or endorsement.

The snapshot belongs in one place because vendor and model details age quickly. A module that says "use model X because it is cheapest" can become wrong before the learner finishes the track. Durable engineering prose should instead teach the questions: Does the system need exact OCR or semantic reasoning? Does it need low latency or high recall? Can it run locally, or must it call a hosted API? Can failed cases be routed to humans? Does the model return bounding boxes, points, citations, or only prose? Those questions survive model releases.

VLMs also differ from dedicated computer vision models in their failure shape. An object detector usually returns boxes, scores, and classes. A VLM returns language. Language can compress uncertainty, hide missing evidence, and overfit to the user's implied goal. If the prompt asks, "Which safety violation is visible?" the model may search for a violation even when none is present. Production systems should ask neutral observation questions first, request evidence, and separate perception from policy judgment.

The connector is where many architectural tradeoffs hide. A simple linear projection can be enough when the visual encoder already produces features that line up well with the language model's embedding space, but it may pass too many tokens or too little task-specific information. A query transformer, resampler, or learned pooling layer can compress many visual features into a smaller set of language-compatible vectors. Compression improves latency and context pressure, but it can discard small evidence such as a serial-number digit, a checkbox mark, or a tiny icon in a dense diagram. When you evaluate a VLM, ask what information the connector is allowed to preserve.

Training usually happens in stages because fully end-to-end multimodal training is expensive and can damage capabilities that were already learned. A first stage may align image features with the language model's token space, often using caption-like data or image-text pairs. A later stage may teach instruction following with examples such as "describe the image", "answer this chart question", or "extract these fields as JSON." Some systems freeze the vision encoder and LLM, some fine-tune the connector, and some update more of the stack. The frozen-component pattern is attractive because it reuses strong pretrained models, but it can also preserve their blind spots.

The phrase "the LLM attends to the image" should be read carefully. The LLM does not see pixels. It receives embedding vectors produced by the visual side of the system, and those vectors are shaped by patch size, resolution handling, connector design, and training data. If the image encoder never captured a faint watermark, the language model cannot recover it by reasoning harder. If the connector compressed a table too aggressively, the generated answer may sound precise while silently losing row structure. Prompting helps only after the evidence survives the visual path.

This is why a VLM should not automatically replace specialized vision models. If your task is real-time obstacle detection, a dedicated detector or segmentation model may be faster, easier to calibrate, and easier to audit. If your task is answering a natural-language question about a messy screenshot, a VLM may be more useful because it can combine visible text, layout, and domain instructions. Strong systems often use both: a detector produces grounded candidates, OCR extracts text spans, CLIP retrieves related examples, and a VLM performs the final explanation or structured synthesis.

## Part 4: Multimodal Prompting and Grounding

A multimodal prompt is not just a text prompt with an image attached. The image determines the evidence available to the model, while the text determines what the model should attend to, how it should serialize the answer, and how it should handle uncertainty. A weak prompt asks, "What is in this image?" and receives a broad caption. A stronger prompt names the task, defines the output fields, asks the model to distinguish observed evidence from inference, and tells it what to do when the image is unreadable.

For visual question answering, split the work into observation and decision. First ask the model to describe only visible evidence relevant to the task. Then ask it to apply the rule or choose an output label. This reduces the chance that a policy label appears before the visual evidence has been enumerated. The pattern is especially useful in safety, compliance, medical-adjacent, legal, finance, and operations contexts where a confident-looking answer can trigger a real workflow.

```text
Weak prompt:
What is wrong with this shipment photo?

Better prompt:
List visible evidence only: packaging condition, readable labels, exposed product,
water damage, crushed corners, and missing seals. If evidence is unclear, say
"unclear". After the evidence list, classify the return reason as one of:
no visible damage, cosmetic damage, shipping damage, unreadable image.
Return JSON with evidence and classification.
```

OCR and document parsing are related but not identical. OCR extracts characters. Parsing preserves structure: which value belongs to which field, which row contains which line item, which signature box is empty, and which footnote modifies a table. A VLM can sometimes infer layout that plain OCR loses, but it can also hallucinate plausible structure when the page is faint, rotated, cropped, or visually dense. A robust document pipeline often combines image preprocessing, OCR with coordinates, VLM semantic extraction, schema validation, and human review for low-confidence cases.

Grounding means connecting an answer back to a visual location. In a simple system, grounding may be a visible grid overlay where the model says "cell B3". In a model that supports localization outputs, grounding may be a bounding box or point. In a product workflow, grounding might be a cropped evidence image stored with the decision. The goal is to avoid answers that cannot be audited. "The seal is broken" is less useful than "The seal appears torn on the upper-right flap; confidence is low because glare crosses the same region."

Structured extraction requires strict output contracts. If you need JSON, provide the schema, allowed enum values, null behavior, and validation expectations. Do not ask for a beautiful explanation and then parse it with brittle string splitting. If the model response must feed another system, validate it with a parser, reject invalid fields, and retry with a narrower prompt when necessary. For high-value workflows, store the prompt, image hash, model family, response, validation result, and human correction so future evaluations can reproduce the case.

Multi-image prompting introduces another layer of ambiguity. Passing two product images as separate inputs usually preserves the distinction better than concatenating them into one wide collage, because the model and API can represent the images as separate items in the request. When comparing before-and-after photos, listing photos against customer uploads, or architecture diagrams against screenshots, label each image in the text prompt and ask the model to reason by image identity. The phrase "left image" becomes unreliable once images are resized, reflowed, or passed through different clients.

Pointing and bounding-box workflows need explicit coordinate conventions. If a model or tool returns `[x1, y1, x2, y2]`, define whether those values are pixels, normalized coordinates, percentages, or grid cells. Define whether the origin is top-left, whether boxes include the boundary pixel, and how rotated images are handled. Many downstream bugs in visual systems are not neural-network failures; they are coordinate-system mismatches between the model response, frontend overlay, stored crop, and reviewer UI. A prompt that says "return a bounding box" is incomplete unless the application contract defines the coordinate frame.

For structured extraction, prompt examples should include negative and partial cases rather than only perfect documents. A good invoice prompt says what to do when a field is missing, unreadable, crossed out, duplicated, or present only in a logo. A good chart prompt distinguishes title, axes, legend, visible datapoints, and inferred trend. A good screenshot prompt separates UI text that is actually visible from likely product knowledge. These distinctions reduce hallucinated structure because the model has an allowed path for uncertainty.

The safest mental model is that a multimodal prompt sets up a small protocol. The image provides evidence, the system prompt defines non-negotiable behavior, the user prompt defines the task, the schema defines the output boundary, and the validator enforces that boundary. If any one of those pieces is missing, the model will fill the gap with a statistically plausible response. Production prompt engineering is therefore less about clever phrasing and more about removing ambiguity from the handoff between perception, reasoning, and software.

## Part 5: Building Vision AI Applications

The simplest useful vision application is semantic image search. You compute CLIP embeddings for a corpus of images, store the normalized vectors, and compare a user's text query embedding against the image embeddings. This can support natural-language browsing over diagrams, screenshots, product photos, or support attachments. The offline-online split is important: expensive image embedding happens once during ingestion, while query embedding and vector search happen on demand. The same pattern can also bootstrap labeling by retrieving visually similar examples for review.

```python
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


class LocalClipSearch:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.image_paths = []
        self.image_embeddings = None

    def index_folder(self, folder):
        embeddings = []
        for path in sorted(Path(folder).glob("*.jpg")):
            image = Image.open(path).convert("RGB")
            inputs = self.processor(images=image, return_tensors="pt")
            with torch.no_grad():
                vector = self.model.get_image_features(**inputs)
                vector = vector / vector.norm(dim=-1, keepdim=True)
            embeddings.append(vector.cpu().numpy())
            self.image_paths.append(str(path))
        self.image_embeddings = np.vstack(embeddings)

    def search(self, query, top_k=3):
        inputs = self.processor(text=[query], return_tensors="pt", padding=True)
        with torch.no_grad():
            text_vector = self.model.get_text_features(**inputs)
            text_vector = text_vector / text_vector.norm(dim=-1, keepdim=True)
        scores = (text_vector.cpu().numpy() @ self.image_embeddings.T)[0]
        order = np.argsort(scores)[::-1][:top_k]
        return [(self.image_paths[i], float(scores[i])) for i in order]
```

A visual QA application adds a generative model after image ingestion. The application must encode or upload the image, attach a task prompt, receive the model response, validate it, and decide whether to accept, retry, escalate, or store the result. The tempting mistake is to let the VLM be the whole application. The stronger design treats the VLM as one component inside a workflow that also owns preprocessing, schema validation, observability, and policy decisions.

Image preprocessing is part of model quality, not just performance tuning. Normalize color mode to RGB unless the model or library requires another format. Strip corrupt metadata. Rotate based on EXIF orientation when appropriate. Resize according to task: a coarse scene classifier can use smaller images, while OCR and dense diagrams need enough resolution to preserve text. For document pages, consider contrast enhancement, deskewing, and cropping before the model call. A bad preprocessing pipeline can make a strong model look unreliable.

Batching and caching determine whether a prototype survives production traffic. If many users upload the same asset, hash the image bytes and cache the model response for deterministic prompts. If many images need the same embedding model, batch them to use hardware efficiently. If hosted VLM calls dominate latency, separate ingestion-time analysis from user-facing request time where possible. A product catalog can precompute captions and embeddings before search traffic arrives; a live inspection workflow may need a fast first pass and a slower escalation path.

Human review is not a failure of automation. It is a design control for ambiguous visual evidence. The review queue should include the original image, any cropped evidence, the model's observed evidence, the requested output, confidence or uncertainty signals if available, and validation failures. The reviewer should correct the structured fields rather than write free-form notes only, because those corrections become evaluation data. Over time, the team can measure which image conditions, prompt shapes, or model families trigger review most often.

The deployment boundary should be chosen by failure cost. If a wrong answer only changes image search ranking, you can usually tolerate approximate embeddings, periodic offline evaluation, and lightweight rollback. If a wrong answer pays an invoice, rejects a customer return, unlocks an account, or classifies a safety condition, the VLM should not be the sole decision maker. Put deterministic checks around it, store evidence, and require a second path for expensive or irreversible actions. This is the same engineering instinct used in distributed systems: unreliable components can be useful when the surrounding protocol limits blast radius.

Another practical boundary is freshness. Product photos, UI screenshots, handwritten forms, and industrial labels can drift faster than the underlying model. A team may blame the provider when accuracy falls, but the real change may be a new camera app, a supplier label redesign, or a workflow that starts accepting screenshots from a different device class. Capture enough input metadata to separate model regression from data drift. Without that separation, teams often switch models repeatedly while leaving the actual ingestion problem untouched.

## Part 6: Production Reliability and Cost Control

Vision workloads have a different cost profile from text-only workloads because image payloads can be large, tokenized into many visual tokens, and slow to upload or preprocess. The exact accounting depends on the provider and changes over time, so do not hard-code pricing assumptions into architecture docs. Instead, design with cost controls that remain valid: resize images before sending them, reject unsupported formats early, cap the number of images per request, cache repeated analyses, and route simple cases to cheaper local or specialized models when they meet the quality bar.

Latency is also multi-part. There is client upload time, image decoding, resizing, model queueing, visual encoding, language generation, validation, and retry behavior. A system that feels instant in a notebook can feel slow in a web app because the user uploads a large phone photo over a weak connection. For user-facing workflows, return early progress states, compress safely, and avoid asking one VLM call to do ten unrelated jobs. For backend workflows, process images asynchronously and make the human-facing state explicit.

Failure modes deserve their own test set. Include blurry photos, cropped documents, glare, rotated labels, handwriting, low-contrast watermarks, dense diagrams, screenshots with small fonts, visually similar classes, adversarially placed text, and normal negative cases where nothing interesting is happening. The negative cases matter because multimodal models often try to satisfy the user's implied request. If every evaluation image contains a defect, the model can learn or appear to learn that a defect should always be found.

OCR transposition is a practical risk. A VLM may swap adjacent digits, normalize a serial number into a more familiar pattern, or infer a missing character from context. That is dangerous for invoices, bank documents, medication labels, shipping IDs, and compliance evidence. When exact text matters, compare the VLM output against a dedicated OCR engine, apply checksums or format validation when possible, and mark low-quality regions for review. The VLM is often better at explaining layout than guaranteeing every character.

Hallucinated structure is the document version of the same problem. The model may invent a table column that seems semantically likely, attach a total to the wrong line item, or summarize away a footnote. You can reduce this risk by requesting extracted fields with coordinates or evidence snippets, validating totals arithmetically, and separating "read what is present" from "infer what it means." If the image does not support a required field, the correct output is `null` or `unclear`, not a plausible guess.

Security and privacy controls should be designed before launch. Images can contain faces, addresses, documents, screens, keys, barcodes, location clues, and proprietary diagrams. Decide whether images may leave your environment, whether you need redaction before model calls, how long images and responses are retained, and who can inspect failed cases. A local open-weight model may reduce data transfer risk but add operational risk; a hosted API may reduce operations but require stricter data-sharing review. The right answer depends on the data classification, not model popularity.

A reliable production pattern is a tiered pipeline. Use deterministic validation and lightweight models first, then escalate when evidence is ambiguous. For example, a support workflow might hash and cache the image, check resolution, run OCR, retrieve similar historical cases with CLIP, call a VLM for structured evidence, validate the JSON schema, and route uncertain cases to review. This pattern is slower to build than a single API call, but it gives you levers to improve quality without rewriting the whole product.

Evaluation should be task-specific rather than benchmark-shaped. A public benchmark may tell you that a model can answer general image questions, but your product may care about one narrow distinction such as "is the tamper seal intact?", "does this network diagram contain an unmanaged ingress path?", or "which invoice total is payable after tax?" Build an evaluation set from real or realistically staged examples, label the expected evidence, and score both the final answer and the supporting observation. A model that gets the right label for the wrong visual reason is still risky.

Observability should capture enough context to debug visual failures without exposing more sensitive data than necessary. At minimum, store an image hash, preprocessing metadata, prompt version, model family, validation outcome, latency, retry count, and reviewer disposition. For privacy-sensitive images, store redacted crops or references rather than raw images when policy requires it. The key is to make failures reproducible: if a reviewer reports a transposed serial number, the team should know which prompt, model, crop, and preprocessing path produced the mistake.

Drift appears in vision systems through input changes as much as model changes. A new mobile app may compress photos differently. A warehouse may change label printers. A product team may add dark-mode screenshots. A vendor may change model routing behind an API name. Monitor image dimensions, file types, OCR confidence, review rates, schema failures, and task-specific disagreement over time. When those signals move, investigate before assuming that the VLM has become worse or better in a general sense.

## Did You Know?

- > The ViT paper showed that a pure transformer can process image patches directly, but its strongest results depend on large-scale pretraining rather than a built-in convolutional prior.
- > The CLIP paper trained image and text encoders with natural-language supervision, making zero-shot transfer possible by comparing images with text prompts instead of training a new classifier head.
- > BLIP-2 is a reference point for efficient VLM construction because it bridges frozen image encoders and frozen language models with a learned querying transformer.
- > LLaVA helped popularize visual instruction tuning by connecting a CLIP visual encoder to a language model and training the combined system to follow image-plus-text instructions.

## Common Mistakes

| Mistake | Why it happens | How to fix |
|---|---|---|
| Treating VLM prose as verified evidence | The language model can produce fluent explanations even when the visual signal is weak or ambiguous. | Ask for observed evidence separately, require `unclear` for missing evidence, and validate outputs before acting. |
| Sending raw high-resolution images to every API call | Teams optimize for demo simplicity and forget that upload size, visual tokens, and provider accounting affect cost and latency. | Resize by task, cap dimensions, cache image hashes, and document model-specific accounting in a dated snapshot. |
| Using CLIP similarity as a business decision | Contrastive embeddings are excellent for retrieval but do not prove exact object state, text content, or policy compliance. | Use CLIP for candidate generation, then add VLM verification, specialized detectors, OCR, or human review. |
| Flattening document OCR before reasoning | Plain text extraction often destroys table layout, field proximity, checkboxes, and signatures. | Preserve coordinates, page images, crops, and schema validation so the model can reason with layout evidence. |
| Concatenating multiple images into one collage | The model may mix visual evidence across regions, and resizing can make labels such as "left" or "right" unreliable. | Pass images as separate inputs when the API supports it, label each image in the prompt, and request per-image evidence. |
| Asking one prompt to perform many unrelated tasks | The model divides attention across counting, OCR, classification, comparison, and summarization, causing omissions. | Decompose workflows into focused calls or staged prompts, then combine validated intermediate outputs. |
| Ignoring negative and low-quality test cases | Demos usually contain clean images where the expected answer is present, hiding false positives and uncertainty handling. | Build an evaluation set with normal images, unclear images, glare, blur, small text, rotated pages, and adversarial text. |

## Knowledge Check

<details>
<summary><strong>Question 1</strong>: A team increases ViT patch size from 16 by 16 to 32 by 32 for a fixed-size image and sees faster inference but worse small-text recognition. What changed?</summary>

The larger patch size reduces the number of tokens, so self-attention has a shorter sequence and inference can be faster. The tradeoff is that each token now compresses a larger region of pixels before attention can operate. Small characters, thin lines, and subtle visual details may be averaged into one representation too early. For OCR-like tasks, smaller patches or higher-resolution processing can preserve evidence that a coarse patch grid loses.
</details>

<details>
<summary><strong>Question 2</strong>: Your CLIP search system retrieves "safety helmet" images for the query "worker without helmet." Why is this not surprising?</summary>

CLIP-style retrieval measures similarity between an image and a text prompt; it does not reliably implement logical negation. The words "worker" and "helmet" may dominate the embedding, while "without" may not create the negative concept you intend. A better design retrieves candidate worker images, then uses a detector or VLM verification prompt that asks for visible evidence of helmet presence and allows an explicit `unclear` outcome.
</details>

<details>
<summary><strong>Question 3</strong>: A document pipeline sends OCR text alone to an LLM and gets line-item totals attached to the wrong products. Why can the original page image help?</summary>

The OCR text may flatten a two-dimensional page into a one-dimensional string, losing columns, row alignment, checkboxes, and spatial proximity. The page image preserves layout evidence that helps associate a price with the correct row or table region. A robust pipeline can combine OCR coordinates, page crops, VLM semantic extraction, and arithmetic validation rather than relying on flattened text alone.
</details>

<details>
<summary><strong>Question 4</strong>: A VLM returns valid JSON for every invoice, but reviewers find that missing purchase-order numbers are replaced by plausible-looking values. What should change?</summary>

The schema should define missing or unreadable fields as `null` or `unclear`, and the prompt should explicitly forbid guessing. The application should validate field formats, compare extracted values against OCR snippets or crops, and route low-confidence cases to review. Valid JSON only proves the response parsed; it does not prove the visual evidence supported every value.
</details>

<details>
<summary><strong>Question 5</strong>: A quality-control app concatenates "before" and "after" photos into one image, then asks the VLM to compare them. The model mixes details across the two sides. What is the better request shape?</summary>

Pass the photos as separate image inputs when the API supports it, label them clearly in the prompt, and request evidence per image before asking for a comparison. Concatenation relies on the model preserving the human-intended boundary after resizing and tokenization. Separate inputs make it easier for the system and prompt to maintain image identity throughout the reasoning step.
</details>

<details>
<summary><strong>Question 6</strong>: A support workflow uses a hosted VLM for every uploaded image and then sees unpredictable monthly spend. Which controls should be added first?</summary>

Add deterministic controls before changing models: cap image dimensions, reject unsupported formats, hash and cache repeated images, limit the number of images per request, and split simple classification from expensive reasoning. Then measure latency and cost by task type. Pricing details change across providers, but preprocessing, caching, batching, and routing remain durable cost-control techniques.
</details>

<details>
<summary><strong>Question 7</strong>: A team builds a BLIP-2 or LLaVA-style VLM by freezing a vision encoder, training only a projection connector, and attaching an instruction-tuned LLM. The answers are fluent, but tiny serial numbers disappear. Which component is most likely responsible?</summary>

The projection connector or visual resampling path is the first place to inspect, because it controls how much visual detail survives from the frozen vision encoder into the LLM-compatible embedding sequence. The language model never sees raw pixels; it sees projected visual embeddings. If the connector compresses many patch features into too few tokens, small evidence can disappear before generation begins. A better design may need higher-resolution visual features, a less aggressive connector, OCR support, or a specialized crop path for serial-number regions.
</details>

<details>
<summary><strong>Question 8</strong>: A prototype works on clean demo photos but fails on real phone uploads with glare, rotation, and blur. What evaluation mistake caused this?</summary>

The evaluation set represented the demo distribution rather than the production distribution. Vision systems need test cases for poor lighting, motion blur, rotated pages, compression artifacts, small text, reflections, normal negative examples, and ambiguous images. Without those cases, the team cannot measure false positives, uncertainty handling, preprocessing needs, or review volume before launch.
</details>

## Hands-On Exercise

In this exercise, you will build a small local CLIP image search lab and a deterministic preprocessing check. The goal is not to deploy a full VLM service; it is to practice the foundation that many production systems use before calling a generative model. You will create a tiny image corpus, index it with CLIP, query it with natural language, and inspect how prompt wording changes retrieval. The commands assume you are running from the KubeDojo repository root so the project `.venv` is available.

```bash
LAB_DIR="${TMPDIR:-/tmp}/vision-ai-lab"
mkdir -p "$LAB_DIR/images"
cd "$LAB_DIR"

# Wikimedia Commons re-hashes file paths over time, so we use the hash-independent
# Special:FilePath redirect (resolves to the current canonical URL) instead of a
# pinned /a/ab/ hash path that can 404 after a re-hash or file deletion.
curl -L -o images/cat.jpg   "https://commons.wikimedia.org/wiki/Special:FilePath/Cat_November_2010-1a.jpg"
curl -L -o images/dog.jpg   "https://commons.wikimedia.org/wiki/Special:FilePath/Labrador_Retriever_(1210559).jpg"
curl -L -o images/house.jpg "https://commons.wikimedia.org/wiki/Special:FilePath/Snowy_house.jpg"
curl -L -o images/bird.jpg  "https://commons.wikimedia.org/wiki/Special:FilePath/Eopsaltria_australis_-_Mogo_Campground.jpg"
```

Create `$LAB_DIR/clip_search_lab.py` with the following script. It indexes all downloaded JPEG files, runs three natural-language queries, and prints the top matches. The script also normalizes image color mode and rejects very small images so you can see where preprocessing belongs in the application boundary.

```python
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


def load_image(path):
    image = Image.open(path).convert("RGB")
    if min(image.size) < 224:
        raise ValueError(f"{path} is too small for this lab: {image.size}")
    return image


class ClipIndex:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.paths = []
        self.embeddings = None

    def index(self, image_dir):
        vectors = []
        for path in sorted(Path(image_dir).glob("*.jpg")):
            image = load_image(path)
            inputs = self.processor(images=image, return_tensors="pt")
            with torch.no_grad():
                vector = self.model.get_image_features(**inputs)
                vector = vector / vector.norm(dim=-1, keepdim=True)
            vectors.append(vector.cpu().numpy())
            self.paths.append(path)
        self.embeddings = np.vstack(vectors)

    def search(self, query, top_k=2):
        inputs = self.processor(text=[query], return_tensors="pt", padding=True)
        with torch.no_grad():
            vector = self.model.get_text_features(**inputs)
            vector = vector / vector.norm(dim=-1, keepdim=True)
        scores = (vector.cpu().numpy() @ self.embeddings.T)[0]
        order = np.argsort(scores)[::-1][:top_k]
        return [(self.paths[i].name, round(float(scores[i]), 4)) for i in order]


if __name__ == "__main__":
    index = ClipIndex()
    index.index("images")
    queries = [
        "a photo of a household pet",
        "a snowy building",
        "a small bird perched outdoors",
    ]
    for query in queries:
        print(query)
        for name, score in index.search(query):
            print(f"  {name}: {score}")
```

Run the script from the repository root so it uses the project virtual environment and installed dependencies. If the `transformers`, `torch`, or `pillow` packages are not installed in your local environment, install them into the project venv first using the same interpreter.

```bash
# From the KubeDojo repository root:
.venv/bin/python -m pip install transformers torch pillow numpy
.venv/bin/python "${TMPDIR:-/tmp}/vision-ai-lab/clip_search_lab.py"
```

After the first successful run, edit the query `"a photo of a household pet"` into `"a product catalog image of a household pet"` and run the script again. The labels in this tiny corpus may not change, but the scores usually move because the text encoder embeds the whole prompt. In a real system, you would record those prompt variants as evaluation cases rather than treating a single query string as the truth.

**Success Checklist**

- [ ] The four sample images exist under `$LAB_DIR/images`.
- [ ] The script rejects no images for size or decoding errors.
- [ ] Each query returns two ranked filenames with numeric similarity scores.
- [ ] You changed one prompt template and observed whether scores or rankings moved.
- [ ] You can explain why this CLIP lab is retrieval, not grounded visual reasoning.

## Next Module

Next: [Module 1.3: Video AI](../module-1.3-video-ai/) extends the same multimodal reasoning problem into time, where frame sampling, temporal grounding, and long-context evidence management become the central engineering constraints.

## Sources

- [An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale](https://arxiv.org/abs/2010.11929) — foundational ViT paper for patch embeddings, transformer encoders, and scale-dependent visual pretraining.
- [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020) — primary CLIP paper for contrastive image-text pretraining and zero-shot classification with text prompts.
- [BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models](https://arxiv.org/abs/2301.12597) — reference architecture for frozen visual encoders, frozen LLMs, and a learned modality bridge.
- [Visual Instruction Tuning](https://arxiv.org/abs/2304.08485) — LLaVA paper explaining visual instruction tuning and the vision-encoder-to-LLM connector pattern.
- [Sigmoid Loss for Language Image Pre-Training](https://arxiv.org/abs/2303.15343) — SigLIP paper showing an alternative loss for language-image pretraining.
- [OpenCLIP repository](https://github.com/mlfoundations/open_clip) — open implementation ecosystem for training and evaluating CLIP-style image-text models.
- [Hugging Face Transformers CLIP documentation](https://huggingface.co/docs/transformers/en/model_doc/clip) — practical API reference for CLIP encoders, feature extraction, and similarity scoring.
- [OpenAI Images and Vision guide](https://developers.openai.com/api/docs/guides/images-vision) — official OpenAI documentation for image inputs and vision-capable API workflows.
- [Claude Vision documentation](https://platform.claude.com/docs/en/build-with-claude/vision) — official Anthropic documentation for Claude image inputs, limits, and multimodal usage patterns.
- [Gemini Image Understanding documentation](https://ai.google.dev/gemini-api/docs/image-understanding) — official Google AI documentation for Gemini image input and visual task support.
- [Qwen2.5-VL release notes](https://qwenlm.github.io/blog/qwen2.5-vl/) — Qwen team's published overview of its vision-language model family, grounding, document, and structured-output examples.
- [LLaVA project page](https://llava-vl.github.io/) — project documentation for LLaVA's visual instruction data, CLIP visual encoder connection, and open-source release context.
