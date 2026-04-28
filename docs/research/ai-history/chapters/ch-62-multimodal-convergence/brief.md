# Brief: Chapter 62 - Multimodal Convergence

## Thesis

By the mid-2020s, "language model" was no longer a sufficient category. Systems
that had been marketed through chat windows became interfaces for images,
screens, audio, video, and mixed media. This chapter should explain multimodal
convergence as a product, architecture, and evaluation shift: text stayed the
control surface, but the model's world became visual, audible, temporal, and
interactive.

## Boundary Contract

- IN SCOPE: CLIP/Flamingo as research precursors; GPT-4/GPT-4V as the visual
  assistant turn; Gemini's source-bound "natively multimodal" framing; GPT-4o
  real-time audio/vision/text interface; Sora and Veo as video-generation
  frontier claims; media-specific safety/evaluation difficulties.
- OUT OF SCOPE: full film-industry history, complete image-diffusion history
  (Ch58), benchmark politics as product weapon (Ch66), copyright/data labor
  fights (Ch68), inference economics (Ch63), and broad claims that video models
  already understand physics.
- Transition from Ch61: training-scale systems made frontier multimodal models
  possible, but Ch62 focuses on what changed when inputs and outputs stopped
  being text-only.
- Transition to Ch63/66/68: media inputs increase cost, latency, evaluation
  difficulty, and data-rights stakes, but those detailed arguments belong in
  later chapters.

## Required Scenes

1. **Language Learns To Point:** CLIP shows that natural language can supervise
   visual concepts at web scale; Flamingo turns interleaved images/videos/text
   into a few-shot visual-language interface.
2. **Vision Enters The Chat Window:** GPT-4's report and GPT-4V's system card
   make images part of a GPT-style assistant, while exposing new risks around
   hallucination, medical use, person identification, and image-borne jailbreaks.
3. **Native Multimodality Becomes A Product Claim:** Gemini frames the model as
   jointly trained across text, image, audio, and video, and as supporting
   interleaved media sequences.
4. **Speech Collapses The Interface:** GPT-4o makes audio latency and
   speech-to-speech interaction central, while the system card shows that voice
   introduces new safety and evaluation surfaces.
5. **Video Becomes The Hard Case:** Sora and Veo move multimodality into
   time, motion, and creative production; the prose must pair impressive claims
   with explicit limitations and safety filters.
6. **The Category Breaks:** Close on why "LLM" became shorthand but not a full
   description of these systems.

## Prose Capacity Plan

Target range: 3,800-4,800 words.

- 450-650 words: bridge from scale and agents to media interfaces; define why
  text-only "LLM" became too narrow.
- 600-800 words: CLIP and Flamingo as the research bridge from language
  supervision to interleaved visual-language prompting.
- 750-950 words: GPT-4/GPT-4V visual assistant turn, including image/text
  prompts, Be My Eyes/Be My AI, and risk surfaces.
- 700-900 words: Gemini and GPT-4o as product-era multimodal convergence:
  joint training claims, audio/vision/text inputs, real-time speech, and safety.
- 750-950 words: Sora/Veo video frontier: spacetime patches, variable
  duration/resolution/aspect ratio, video editing, 1080p/minute-scale claims,
  safety stack, and explicit simulator limitations.
- 350-550 words: category-collapse close and handoff to inference economics,
  benchmarks, copyright/data labor, and energy/chip constraints.

## Guardrails

- Do not treat demo videos as proof of robust world modeling.
- Do not claim "native multimodal" except as Gemini's source-bound wording and
  explain that it means joint training across modalities in that report.
- Do not turn this into a Sora-only chapter.
- Do not add copyright or data-labor material here except as a pointer to Ch68.
- Do not import benchmark-politics analysis; Ch66 owns that.
- Do not claim GPT-4o generated video outputs; its system card says text, audio,
  and image outputs.
