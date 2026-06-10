---
title: "Multimodal-First AI Design"
slug: ai-ml-engineering/multimodal-ai/module-1.4-multimodal-first-design
sidebar:
  order: 905
---

> **AI/ML Engineering Track** | Phase 9 | Complexity: `[COMPLEX]` | Time: 60-75 minutes | Prerequisites: [Voice & Audio AI](../module-1.1-voice-audio-ai/), [Vision AI](../module-1.2-vision-ai/), and [Video AI](../module-1.3-video-ai/)

## Learning Outcomes

By the end of this module, you will be able to:

- **Distinguish** composite multimodal pipelines from native multimodal architectures and explain the tradeoffs in latency, auditability, cost, and semantic retention.
- **Design** shared-context payloads that keep text, audio, image, and video evidence aligned without duplicating modality deep dives from the previous modules.
- **Plan** streaming interactions that handle partial results, endpointing, barge-in, cancellation, and context truncation as first-class state transitions.
- **Map** a multimodal application onto Kubernetes using gateway routing, sidecars, modality services, back-pressure, and GPU-aware scheduling boundaries.
- **Evaluate** whether a use case should use early fusion, late fusion, specialist tools, or a native multimodal model based on failure modes rather than hype.

## Why This Module Matters

Hypothetical scenario: A support team ships a voice assistant by wiring together speech-to-text, a text-only language model, and text-to-speech. The demo works in a quiet conference room because every sentence arrives as a clean transcript, every response is short, and nobody interrupts the bot. The first production pilot feels different. Callers pause, mumble, talk over the assistant, switch languages, send screenshots, and expect the system to react while the conversation is still happening. The team keeps adding retries, transcript cleanup, silence timers, and client-side buffer hacks, but the user experience still feels brittle because the architecture treats audio, text, and visual evidence as separate jobs rather than one interaction.

The deeper failure is not that any one model is weak. The deeper failure is that the system throws information away too early and then asks later components to infer what was lost. A transcript can preserve words, but it does not reliably preserve hesitation, urgency, overlapping speakers, background sound, or whether the user interrupted before the assistant finished speaking. An image caption can preserve a few objects, but it may discard layout, small text, spatial relationships, and uncertainty. A sampled video frame can preserve a scene, but it may miss the gesture or event that happened between frames. Once those details are compressed into a narrow intermediate representation, downstream reasoning can look confident while being grounded in an incomplete view of the situation.

Multimodal-first design starts from the opposite assumption: the user's experience is the unit of design, not the model endpoint. Sometimes that means using a native multimodal model that can attend across audio, image, video, and text representations in one context. Sometimes it means using a composite pipeline because a specialized detector, policy layer, or audit trail is more important than direct end-to-end reasoning. The engineering skill is knowing which boundary to draw, how to keep modalities aligned, how to stream partial evidence without corrupting state, and how to deploy the system on Kubernetes without turning GPU placement, back-pressure, and media routing into afterthoughts.

This module is the design-patterns layer for the multimodal sub-track. The details of speech, vision, and video are handled in their own modules; here we focus on the architecture that joins them. By the end, you should be able to look at a proposed "multimodal" product and ask sharper questions: Where is information lost? Which components own timing? What is the shared state model? How does an interruption change history? Which pods need GPUs, which paths need low latency, and which payloads should never be sent to a general model at all?

## Composite Versus Native Multimodal Design

A composite multimodal system is a pipeline built from specialized models and services. A voice assistant might use one service to transcribe audio, a language model to reason over text, a retrieval layer to fetch product information, a moderation model to screen the response, and a speech synthesizer to speak back to the caller. A visual support assistant might use OCR, object detection, an image captioner, a language model, and a workflow engine. This pattern is not obsolete. It remains useful when each stage has a clear contract, when the organization needs separate observability for each decision, or when a specialized model solves a narrow problem better than a general model.

The drawback is that composite systems create semantic checkpoints. Every handoff decides what counts as the "truth" of the previous modality. Speech becomes text. An image becomes tags. A video becomes sampled frames. A screen recording becomes OCR plus event logs. These transformations are often necessary, but they are lossy. They also make the pipeline sequential unless you deliberately parallelize and reconcile the branches. If transcription waits for a full utterance, the language model cannot reason until the utterance is finished. If the language model waits for a complete answer before speech synthesis begins, the user hears silence. If a video summarizer waits for a full clip, the system cannot react to the live event that matters.

Native multimodal design tries to reduce these losses by allowing one model family to ingest multiple modalities into a shared context. The application can send text instructions, audio chunks, image inputs, or video-derived tokens to one reasoning surface rather than forcing every modality through a text bottleneck first. The word "native" is easy to overuse, so treat it as a design claim that needs evidence. A genuinely native path should preserve modality-specific cues long enough for the model to use them, support interleaved inputs rather than only preprocessed captions, and expose streaming semantics if the user interaction is real time. If the system secretly transcribes, captions, and stitches outputs behind the scenes, it may still be useful, but it behaves like a composite pipeline from an architectural risk perspective.

The first tradeoff is latency. A composite voice chain can optimize each component independently, but the user pays for the sum of capture delay, transcription delay, model delay, synthesis delay, network hops, and buffering. A native speech-to-speech path can begin reasoning over audio representations without waiting for a final transcript, and it can stream output audio as the response forms. That does not make latency vanish; network jitter, GPU queueing, tool calls, safety checks, and playback buffers still matter. The design improvement is that the system has fewer mandatory serialization points, so there are fewer places where a completed artifact must exist before the next step can start.

The second tradeoff is error compounding. In a composite pipeline, each stage can turn uncertainty into an apparently clean input for the next stage. If speech recognition mishears a medication name, the language model may produce a fluent answer grounded in the wrong string. If OCR drops a minus sign from a screenshot, the reasoning layer may never know there was ambiguity. If a frame sampler misses the moment a worker removes a protective guard, the safety assistant may infer that the scene is stable. Native multimodal models can still be wrong, but they have a better chance of using raw or richer evidence when the relevant signal is not easily represented as text.

The third tradeoff is control. Composite systems are often easier to inspect, gate, and certify because every stage can emit logs, confidence scores, and intermediate artifacts. A regulated workflow may need an auditable transcript, a separate medical-device classifier, or a deterministic business-rule engine even when a native model is available. Native models reduce glue code, but they can also concentrate behavior into a larger black box. Good multimodal-first architecture does not blindly prefer native models; it chooses the narrowest boundary that preserves the evidence needed for the task while keeping safety, cost, and operations understandable.

Think of the design choice like airport security. A composite pipeline is a sequence of checkpoints: identity check, bag scan, metal detector, manual inspection, boarding pass validation. Each checkpoint is specialized and inspectable, but the passenger moves through them one at a time. A native multimodal model is closer to an experienced supervisor watching the whole flow at once: the person, the bag, the timing, the behavior, and the context are interpreted together. The supervisor can notice patterns the individual checkpoints miss, but you still need checkpoints for accountability, throughput, and policy enforcement. Multimodal-first design is deciding which work belongs to the supervisor, which work belongs to checkpoints, and how evidence moves between them.

> **Landscape snapshot - as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

| Capability family | Public example docs | Design note to verify before production |
|---|---|---|
| Realtime native audio sessions | [OpenAI Realtime and audio](https://developers.openai.com/api/docs/guides/realtime) and [OpenAI Realtime with WebRTC](https://developers.openai.com/api/docs/guides/realtime-webrtc) | Confirm current model IDs, supported transports, audio formats, tool-calling behavior, pricing, and regional availability. |
| Realtime voice and vision streams | [Gemini Live API](https://ai.google.dev/gemini-api/docs/live-api) | Confirm current input/output modalities, session limits, SDK behavior, and whether your deployment path uses the developer API or cloud platform controls. |
| Open-model multimodal serving | [vLLM multimodal inputs](https://docs.vllm.ai/en/stable/features/multimodal_inputs/) | Confirm supported model architectures, media input schemas, batching behavior, and whether the serving engine treats a modality as stable or experimental. |

> This snapshot is illustrative, not a leaderboard or endorsement. The durable design question is not "which vendor is ahead this month"; it is which interaction contract your system needs and what evidence each contract preserves.

The practical decision framework is simple enough to use in design review. Use a composite pipeline when you need strong audit boundaries, specialized deterministic tools, independent scaling of stages, or a modality-specific model that clearly outperforms general reasoning for the task. Use a native multimodal model when the interaction depends on cues that would be damaged by translation into text or tags, when real-time turn-taking matters, or when cross-modal relationships are the point of the task. Use a hybrid when the model should perceive rich evidence but still call specialist tools for measurements, policy decisions, retrieval, or final actions.

## Shared Latent Space, Fusion, and Cross-Modal Tokens

The phrase "shared latent space" sounds abstract, but the engineering idea is concrete. Transformers operate over sequences of vectors. Text tokens, image patches, audio windows, and video tubelets all need to become vectors with compatible dimensions before attention can compare them. A model may use different front-end encoders for each modality, but once those encoders project their inputs into the model's working representation, the core network can learn relationships across modalities. A patch containing a red warning light, an audio segment containing a harsh engine knock, and text asking "is this safe to drive?" can influence the same reasoning process.

The first design pattern is early fusion. In early fusion, modality representations are joined before or inside the main reasoning stack. The model can attend across text, image, and audio evidence during reasoning rather than treating one modality as a precomputed annotation. This is powerful when meaning depends on relationships: a spoken "this one" while the user points at a screen, a diagram whose labels must be read with the question, or a video where the timing of a sound explains the visual event. Early fusion is also expensive because the model must carry more tokens through attention, and attention cost grows quickly as context length grows.

The second design pattern is late fusion. In late fusion, specialized components produce outputs that are combined later by a reasoning layer or decision engine. A production inspection system might run a defect detector on images, an audio anomaly detector on machine sound, and a rules engine over sensor thresholds, then send a compact summary to an LLM for explanation. Late fusion can be cheaper, more auditable, and easier to scale because each branch can be optimized separately. Its weakness is that cross-modal nuance may be lost before the final join. If the relevant clue is the alignment between a sound and a motion, late fusion has to preserve timing explicitly or the final reasoning layer will see disconnected facts.

The third design pattern is retrieval-mediated fusion. Instead of sending every media object directly into the model, the system indexes modality-specific embeddings and retrieves only the relevant evidence. CLIP-style image-text embeddings, ImageBind-style joint embeddings, OCR indexes, transcript indexes, and event metadata can help the system find the right media slice before the expensive multimodal call. This pattern is especially useful for long videos, support archives, security footage, and industrial telemetry where the raw corpus is far larger than any context window. The risk is retrieval blindness: if the index representation misses the crucial signal, the model never receives the evidence.

Tokenization is where many hidden design choices live. Text tokenizers split strings into subword units and map them to embeddings. Vision transformer style encoders split images into patches, flatten or project those patches, and add positional information so the model can reason about layout. Audio encoders may represent waveform windows, spectrogram patches, or learned audio tokens across time. Video encoders may form spatiotemporal "tubelets" so a token carries both appearance and motion. These are not just implementation details. They decide which distinctions are cheap, which are expensive, and which are impossible after preprocessing.

Alignment is the training and evaluation problem behind the architecture. If a model is trained so that related text and image representations land near each other, it can answer questions about images using text instructions. If audio, depth, thermal, or motion representations are also aligned, the system can reason across more kinds of evidence. Alignment is never perfect. A model may align common objects well and rare industrial signals poorly. It may associate tone with sentiment in consumer conversations but fail in noisy factory audio. It may read large text in screenshots but miss small labels. Multimodal-first design therefore includes domain evaluation, not just endpoint integration.

Context ordering matters because multimodal prompts are not bags of evidence. A user might say, "Compare this sound with the second image, not the first one," or provide a screenshot, then a correction, then an audio clip. Your payload structure should preserve the conversational and temporal order in which evidence arrived. Interleaved visual-language research such as Flamingo made this explicit: a model can use alternating text and media context when the architecture supports it. In applications, that means your request builder must avoid flattening everything into one caption or one transcript unless that is a deliberate design choice.

State also matters after the model responds. If a native voice model outputs audio directly, the application still needs a representation of what happened for memory, audit, and future turns. The safe approach is to store layered state: raw media references when policy allows, derived artifacts such as transcripts or captions, model-visible context, user-visible playback spans, and action logs. Do not assume that the generated text equivalent of an audio response is identical to what the user heard. If the user interrupted at the halfway point, the future context should reflect the half that was actually played, not the full response the model intended to produce.

The design review question for shared representation is: what must remain aligned across time? For a voice agent, align incoming audio chunks, endpointing events, outgoing audio chunks, tool calls, and the playback cursor. For a vision support agent, align the original image, crop coordinates, OCR text, model answer, and any human annotations. For a video agent, align timestamps, sampled frames, motion events, audio tracks, and selected keyframes. When you cannot answer how alignment is represented, the system is likely to fail under interruptions, retries, or dispute review.

## Streaming Design for Real-Time Multimodal Interaction

Real-time multimodal systems are not normal request-response applications with larger payloads. They are continuous state machines. Audio arrives while the model is thinking. The model may speak while it is still deciding whether to call a tool. The user may interrupt while output audio is buffered locally. Network conditions may reorder or delay chunks. A safety layer may need to stop generation after a partial response has already started. The architecture must define what can happen concurrently and which component owns the truth when events overlap.

The minimum streaming loop has four paths. The capture path reads microphone frames, camera frames, screen frames, or sensor data and encodes them into transport messages. The ingress path authenticates the session, validates media shape, and applies back-pressure before forwarding data to inference. The inference path turns streaming evidence into model state and emits partial outputs. The egress path delivers response deltas to the client and tracks what the user actually received. Treating these as one blocking function is the fastest way to create jitter and stale context.

Endpointing is the decision that the user has completed a turn, or at least paused long enough for the system to respond. In a composite pipeline, endpointing is often tied to speech recognition: wait for silence, finalize a transcript, send text to the LLM. In a native streaming path, endpointing can be softer. The model may receive audio continuously, maintain partial understanding, and begin preparing a response before a final transcript exists. The application still needs explicit events for "user started speaking," "user likely finished," "assistant started speaking," and "assistant audio was played through timestamp T." Without those events, barge-in handling becomes guesswork.

Barge-in is the name for user interruption during assistant output. It is not a polish feature; it is a correctness feature. If the user says "stop" or "actually, I meant the other image" while the assistant is speaking, the system must stop playback quickly, cancel or revise generation, and update conversation history to match reality. The dangerous bug is appending the assistant's full generated response to history even though the user heard only the first part. Future model turns will then assume the user knows information that was never delivered. This creates confusing, sometimes unsafe conversations where the assistant refers back to invisible content.

Partial results require similar discipline. A streaming model may emit text deltas, audio chunks, function-call arguments, safety annotations, or intermediate tool-call plans. The client should not treat every partial token as committed state. Some deltas are speculative until the model finalizes a message. Some audio chunks are committed once played. Some function calls should be held until a complete argument object validates against schema. A robust design separates "received from model," "validated," "sent to user," "played by user," and "committed to conversation history." That separation feels verbose in diagrams, but it prevents entire classes of bugs.

Back-pressure is the other half of streaming correctness. If the client sends audio faster than the server can process it, buffers grow and latency becomes unbounded. If video frames arrive faster than the model path can accept them, the system must choose between dropping frames, lowering resolution, sampling keyframes, or switching to an event-driven summary. The wrong answer is silently queueing everything. Queues are useful only when their maximum size, drop policy, and user-visible behavior are intentional. A voice agent should usually prefer fresh audio over stale audio; a compliance recorder may prefer completeness over immediacy; a robotics controller may need deterministic deadlines.

Transport choice shapes the operational model. WebSockets provide a persistent bidirectional channel that fits server-mediated streaming and works well for many backend-to-model paths. WebRTC is designed for real-time media, browser capture, jitter handling, and audio/video transport, and many browser voice applications benefit from its media stack. HTTP streaming can work for one-way deltas but is awkward for full-duplex interaction. The choice is not purely a developer convenience. It changes authentication, session handoff, load balancer behavior, packet loss handling, client implementation, and where you can observe the stream.

Latency budgets should be broken into components rather than stated as a single marketing number. Capture buffering, codec work, client scheduling, network transit, gateway processing, queue wait, prefill, decoding, tool calls, safety checks, response transport, and audio playback all contribute. A native model can reduce mandatory conversions, but it cannot rescue a design that sends media through distant regions, lets GPU queues grow without admission control, or forces every turn through a slow synchronous tool. In design review, ask for a latency budget table with owners and measurement points, even if the first version uses approximate targets rather than fixed service-level objectives.

Observability must also be multimodal. A text-only log of the final answer is not enough to debug a streaming failure. You need event timelines, chunk counters, queue depths, dropped-frame counts, endpointing decisions, cancellation events, tool-call boundaries, and playback acknowledgements. When privacy policy permits, store short-lived encrypted media references for debugging, but do not make raw-media retention the default unless the product and legal requirements justify it. Good observability lets you answer whether a bad answer came from missing evidence, bad retrieval, model reasoning, stale context, transport jitter, or a client playback bug.

## Kubernetes Architecture for Multimodal Systems

Kubernetes does not make a multimodal system reliable by itself. It gives you primitives for routing, scheduling, isolation, rollout, and observation, but you still have to map the media and inference flows onto those primitives deliberately. A clean architecture usually separates the realtime edge, modality preprocessing, model serving, tool execution, state storage, and offline evaluation paths. Combining all of them into one giant pod may be simple for a demo, but it makes latency, scaling, and failure isolation harder when traffic becomes uneven across modalities.

A practical cluster layout starts with a gateway layer. The gateway terminates external connections, enforces authentication, applies coarse rate limits, and routes sessions to the right backend. For ordinary HTTP traffic, Gateway API or an ingress controller may be enough. For realtime media, the gateway must also respect long-lived connections, connection draining during deploys, sticky session requirements, and protocol differences between WebSocket and WebRTC flows. If the model provider is external, the gateway may broker ephemeral credentials so browsers do not hold long-lived secrets. If inference is internal, the gateway should route users to healthy regional or node-local serving pools.

Behind the gateway, a session coordinator owns conversation state and modality routing. It decides whether a turn goes to a native multimodal model, a speech specialist, an OCR service, a video summarizer, a retrieval service, or a policy engine. The coordinator should not become a place where every media byte is copied forever. Its job is to hold references, sequence numbers, timestamps, and state transitions. It should know that audio chunk 184 arrived before the user interruption, that outgoing chunks 90 through 112 were played, that frame sample 17 corresponds to timestamp 12.4 seconds, and that a tool call was cancelled before execution.

Sidecars are useful when a concern must be close to the workload but should not live inside model-serving code. A media-normalization sidecar can transcode incoming PCM, downscale frames, enforce payload limits, or attach timing metadata before the main container receives input. A policy sidecar can redact obvious secrets from screenshots or block disallowed file types. A metrics sidecar can emit chunk-level telemetry without modifying a vendor SDK. Use sidecars sparingly, because every sidecar adds CPU, memory, rollout, and debugging complexity. The design test is whether co-location solves a real latency, security, or ownership problem.

Modality services should scale according to their bottlenecks. Audio normalization is usually CPU and network sensitive. OCR may be CPU, GPU, or accelerator sensitive depending on model choice. Video sampling can be CPU-heavy and bandwidth-heavy before it ever reaches a model. Native multimodal inference is usually GPU-memory and decode-throughput sensitive. Tool execution may be I/O-bound. If all paths share one deployment and one autoscaler, the busiest modality can starve the others. Split services where scaling curves differ, but keep the session model unified so cross-modal alignment does not disappear into service boundaries.

GPU placement requires explicit scheduling boundaries. Kubernetes exposes vendor-specific accelerators through device plugins, and pods request those resources like extended resources. That gets a pod onto a node with a GPU, but it does not solve model cold starts, memory fragmentation, topology, or queueing. A native multimodal serving pod may need a large model resident in GPU memory, while a lightweight frame sampler should not consume a GPU at all. Use node labels, node affinity, taints, tolerations, and topology spread constraints to keep expensive inference workloads on the right nodes and keep stateless edge services resilient across zones or failure domains.

Resource requests and quality of service matter because realtime workloads fail badly under noisy neighbors. If an audio gateway is CPU-throttled, users hear stutter. If a session coordinator is evicted, active conversations break. If a GPU server accepts unlimited sessions, queue wait dominates every turn. Kubernetes requests, limits, priority classes, and pod disruption budgets are not paperwork; they define which workloads survive pressure and how rollouts affect live sessions. For latency-sensitive paths, prefer admission control and graceful degradation over optimistic overcommit. It is better to reject or downgrade a new video stream than to make every active voice call unusable.

Back-pressure belongs at multiple layers. The client should know when to lower frame rate or stop sending optional video. The gateway should enforce maximum message sizes, connection counts, and session rates. The coordinator should track downstream queue health and switch strategies when inference is saturated. The model-serving layer should expose queue depth, prefill time, decode time, and cancellation behavior. The storage layer should not block realtime turns because a debug artifact upload is slow. Each layer needs a small set of explicit overload decisions; otherwise overload becomes accidental buffering.

The following high-level diagram shows one workable pattern. It is not a reference architecture to copy blindly. It is a map of ownership boundaries that you can adapt to your provider, privacy model, and latency target.

```text
Browser / mobile client
  |  audio, frames, text, interruption events
  v
Realtime gateway
  |  auth, rate limits, sticky session, protocol handling
  v
Session coordinator
  |  state machine, modality routing, sequence numbers
  +--> audio normalizer sidecar/service
  +--> image/OCR service
  +--> video sampler/event extractor
  +--> retrieval and tool services
  |
  v
Native multimodal serving pool
  |  GPU nodes, admission control, streaming deltas
  v
Response egress
  |  playback ack, cancellation, committed history
  v
State store + observability pipeline
```

Rollouts require special care for long-lived sessions. A normal stateless web deployment can terminate old pods as new pods become ready. A realtime voice pod may hold active sessions for several minutes. Use readiness gates, connection draining, maximum session age, and explicit handoff behavior. If handoff is impossible, the product should define what users experience during deploys: finish current sessions on old pods, refuse new sessions during drain, and preserve enough state to recover if a pod dies. Avoid a rollout strategy that silently drops every active stream because the deployment controller saw enough new replicas become ready.

Security and privacy boundaries are part of the architecture, not a separate checklist. Multimodal inputs often contain voices, faces, screens, documents, locations, and bystanders. A gateway that accepts arbitrary screenshots may receive secrets even when users were not trying to share them. A video stream can reveal a workplace layout. Audio can include people who did not consent. The coordinator should know which media can be stored, which must be redacted, which can leave a region, which can be sent to an external provider, and which must be converted into a safer derived artifact first. The more native the model path, the more carefully you need to decide what raw evidence is allowed into it.

## Voice, Vision, and Video as Design Illustrations

Voice is the easiest place to see why multimodal-first design changes architecture, but this module intentionally does not reteach the voice stack. For microphone capture, codecs, speech recognition, synthesis, prosody, and voice-specific safety, go back to [Voice & Audio AI](../module-1.1-voice-audio-ai/). The design lesson here is narrower: voice systems are timing systems. A useful voice agent needs capture, endpointing, generation, playback, interruption, and committed history to agree about what happened. If those clocks disagree, the model may be smart while the conversation feels broken.

The common voice design choice is whether to keep a transcript-centered architecture or move the live path to native audio. Transcript-centered systems are attractive because text is easy to log, search, redact, evaluate, and pass through existing LLM tools. Native audio systems are attractive because tone, timing, and direct audio output can matter for user experience. A hybrid architecture often works well: use native audio for the live turn, create transcripts and summaries asynchronously for audit and search, and make sure future model context distinguishes between what the model heard, what the transcript says, and what the user actually heard in response.

Vision has a different failure shape. The user often provides a still image, screenshot, scan, or camera frame, and latency may be less strict than voice. The hard part is preserving spatial evidence. A caption such as "a dashboard with warning lights" may be enough for a casual explanation, but not enough for troubleshooting because the position, color, label, and surrounding context of each warning light may matter. For image preprocessing, OCR, object detection, layout reasoning, and prompt patterns, use [Vision AI](../module-1.2-vision-ai/). The design lesson here is that the system should keep references to crops, coordinates, OCR spans, and original media so answers can be checked and corrected.

A strong visual support flow often combines native vision reasoning with specialist tools. The model can inspect the whole screenshot and infer user intent, while OCR extracts exact text, a UI automation tool verifies current state, and a policy layer blocks sensitive actions. This is not a step backward from native multimodal design. It is a hybrid that respects the limits of each component. Native perception gives broad context; tools provide exact measurements and actions; state tracking records which evidence justified the answer.

Video is where bandwidth and context limits dominate. The previous [Video AI](../module-1.3-video-ai/) module owns the details of frame sampling, action recognition, temporal reasoning, and high-bandwidth media tradeoffs. The design lesson here is that video is not simply many images. If your system samples one frame every few seconds, it may understand a scene but miss a brief event. If it sends too many frames, it may drown the model in visual tokens and blow the latency budget. If it summarizes video too early, it may lose the temporal relationship that explained the event.

Good video architecture starts with intent. A live safety monitor, a sports coaching assistant, a screen-recording tutor, and an archive search tool have different freshness requirements. The safety monitor may prefer low-resolution frequent frames plus event detectors. The archive search tool may prefer offline indexing and retrieval. The screen tutor may need OCR and UI event alignment more than raw frame rate. The sports coach may need short high-resolution bursts around detected motion. Multimodal-first design does not mean "send all pixels to the largest model." It means preserve the evidence that the task actually needs.

Across all three modalities, the same pattern repeats. Keep raw evidence only when policy and cost justify it. Create derived artifacts for search, audit, and debugging. Preserve alignment metadata so those artifacts can be traced back to the original event. Decide which decisions are made by native reasoning and which are made by specialist tools. Measure latency and loss at each boundary. The strongest multimodal systems are not the ones with the most modalities in the prompt; they are the ones where every modality has a clear reason to be present and a clear path through the system.

## Did You Know?

<blockquote>

- The WebSocket API is defined for two-way interactive communication between a browser and a server, which is why it often appears in server-mediated realtime model sessions.
- WebRTC exposes browser APIs for realtime audio, video, and data exchange, which makes it a natural fit for client-side speech and video interactions when the application needs media-aware transport.
- Kubernetes device plugins are the standard framework for advertising hardware such as GPUs to kubelet, so GPU-aware multimodal serving depends on cluster hardware integration as well as model code.
- ImageBind demonstrated a joint embedding approach across images, text, audio, depth, thermal, and IMU data, showing why shared representation is a design concept rather than a text-only trick.

</blockquote>

## Common Mistakes

| Mistake | Why it happens | How to fix |
|---|---|---|
| Treating native multimodal as automatically better | Teams hear "single model" and assume the architecture is simpler in every dimension. | Compare evidence preservation, audit needs, cost, latency, and operational control before choosing native, composite, or hybrid boundaries. |
| Hiding a composite pipeline behind a native-sounding API name | Product demos describe the user experience, while engineering docs omit intermediate transcription, captioning, or summarization stages. | Document the real data path and list every lossy transformation that happens before model reasoning. |
| Appending unplayed assistant output to history | The server generated a full response, but the user interrupted before hearing all of it. | Commit only the output spans that were delivered or played, and store cancellation events as first-class conversation state. |
| Letting video queues grow without a drop policy | Engineers want complete evidence and avoid deciding which frames to discard under load. | Define freshness rules per use case: drop stale frames for live assistance, preserve complete media for offline audit, or degrade resolution intentionally. |
| Sending every modality to the most expensive model | The system lacks routing logic, so all inputs follow the same path regardless of task. | Route by intent and evidence need: OCR for exact text, detectors for narrow signals, native multimodal reasoning for cross-modal interpretation. |
| Scaling all modality paths with one deployment | Early prototypes put gateway, preprocessing, coordination, and model calls in one service. | Split services where bottlenecks differ, but keep shared session IDs, timestamps, and state transitions consistent across the split. |
| Ignoring GPU admission control | Kubernetes schedules the pod, so the team assumes inference capacity is handled. | Track model queue depth, active sessions, prefill/decode time, and reject or degrade new sessions before queues create user-visible lag. |
| Logging only the final text answer | Text logs are familiar, but they hide media timing, partial output, cancellation, and playback behavior. | Capture event timelines, chunk counters, playback acknowledgements, and derived artifacts that let you debug multimodal state safely. |

## Knowledge Check

<details>
<summary>1. Scenario: A team proposes replacing a transcript-centered call-center bot with a native speech-to-speech model. What should you ask before approving the redesign?</summary>

Ask which user-visible failures the redesign is supposed to fix and which controls must remain outside the native model. Native speech may preserve timing and tone better than a transcript-only pipeline, but the team may still need transcripts for audit, retrieval, compliance review, human handoff, and quality measurement. A good design explains how live audio, derived transcripts, tool calls, cancellation events, and committed playback history coexist rather than claiming that one model endpoint removes every architecture concern.
</details>

<details>
<summary>2. Scenario: A video assistant misses a brief safety event even though the model answers accurately about sampled frames. Is this primarily a reasoning failure?</summary>

Not necessarily. It is likely an evidence-selection failure. If the frame sampler did not include the moment when the event happened, the model could not reason over it. The fix may be to adjust frame rate, add event detectors, preserve short bursts around motion, or route the use case to a lower-latency path. Multimodal systems often fail before inference because preprocessing decides which evidence exists.
</details>

<details>
<summary>3. Scenario: Your voice agent keeps referring to details from an explanation the user interrupted. Which state boundary is probably wrong?</summary>

The system is probably committing generated output rather than played output. When a user interrupts, future history should contain only what the user actually heard, plus the interruption event. If the full generated response is appended to context, the model believes the user received information that was never delivered, so later turns become confusing.
</details>

<details>
<summary>4. Scenario: A product manager asks why you do not send every screenshot, audio clip, and video frame to one native model. How do you evaluate whether the use case should use early fusion, late fusion, specialist tools, or a native multimodal model?</summary>

Explain that native multimodal reasoning is valuable when cross-modal interpretation matters, but specialist tools still provide exact measurements, policy controls, retrieval, and cheaper preprocessing. OCR may be better for exact text, an object detector may be better for a narrow visual signal, and a rules engine may be required for final action. A hybrid design sends the native model the evidence it needs while keeping deterministic work in components that are easier to test and audit.
</details>

<details>
<summary>5. Scenario: A Kubernetes deployment has enough GPU nodes, but realtime sessions still feel slow during traffic spikes. What metrics would you inspect first?</summary>

Inspect active sessions per model replica, model queue depth, prefill time, decode time, cancellation latency, gateway queueing, dropped or buffered media chunks, and client playback delay. Having GPU nodes only proves that pods can be scheduled. It does not prove that admission control, batching, model memory, network paths, or streaming egress are healthy under load.
</details>

<details>
<summary>6. Scenario: A visual troubleshooting assistant stores only final answers and no image references or crop coordinates. What review problem does this create?</summary>

It makes the answer difficult to audit or correct. If the model says "replace the upper valve," reviewers need to know which image, crop, label, or OCR span led to that answer. Without evidence references, a wrong answer is hard to debug because you cannot tell whether the failure came from missing image detail, bad OCR, hallucinated spatial reasoning, or a downstream business rule.
</details>

<details>
<summary>7. Scenario: A WebSocket-based prototype works locally, but browser users experience unstable audio over poor networks. Why might WebRTC be considered?</summary>

WebRTC is designed for realtime media transport in browsers, including audio and video handling, whereas a raw WebSocket stream leaves more media behavior to application code. WebSockets can still be appropriate for server-mediated events or backend streams, but browser speech and video applications often benefit from media-aware transport. The right answer depends on provider support, client complexity, observability, and deployment constraints.
</details>

<details>
<summary>8. Scenario: An architecture diagram shows separate audio, image, video, retrieval, and model-serving services. What must be shared so cross-modal reasoning does not fall apart?</summary>

They need shared session identity, ordering, timestamps, payload references, state transitions, and commitment rules. Service separation helps scaling and ownership only if the system preserves alignment metadata across those services. Otherwise each branch produces plausible artifacts that cannot be reliably joined into one user interaction.
</details>

## Hands-On Exercise

In this exercise you will build a local design checker for a multimodal session envelope. The goal is not to call a vendor API. The goal is to practice the architecture habit this module has been teaching: represent modality events, preserve ordering, simulate back-pressure, and commit only the assistant output that the user actually received. The script uses only the Python standard library, so it should run in the repository environment without extra dependencies.

Create a file named `multimodal_design_check.py` at the repository root (a throwaway scratch file — delete it afterward and do not commit it), paste the code below, and run it from that same repository root with `.venv/bin/python multimodal_design_check.py`. The script builds a session with text, audio, image, and video events, validates ordering and required metadata, simulates a saturated video path, and demonstrates context truncation after a user interruption.

```python
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Event:
    sequence: int
    timestamp_ms: int
    modality: str
    payload_ref: str
    committed: bool = False


# NOTE: these modality tags are illustrative. Real bidirectional audio contracts use
# different capture vs. playback rates — e.g. Gemini Live expects 16 kHz PCM input and
# emits 24 kHz PCM output — so match the exact format your provider documents rather than
# assuming one rate for both directions.
REQUIRED_MODALITY_METADATA = {
    "text": "utf8",
    "audio": "pcm16-24khz-mono",
    "image": "jpeg-or-png",
    "video": "sampled-frame-or-event",
    "assistant_audio": "pcm16-24khz-mono",
}


def validate_session(events: Iterable[Event]) -> list[str]:
    problems: list[str] = []
    previous_sequence = -1
    previous_timestamp = -1

    for event in events:
        if event.sequence <= previous_sequence:
            problems.append(f"sequence moved backward at {event}")
        if event.timestamp_ms < previous_timestamp:
            problems.append(f"timestamp moved backward at {event}")
        if event.modality not in REQUIRED_MODALITY_METADATA:
            problems.append(f"unknown modality {event.modality!r}")
        if not event.payload_ref:
            problems.append(f"missing payload reference at sequence {event.sequence}")
        previous_sequence = event.sequence
        previous_timestamp = event.timestamp_ms

    return problems


def apply_video_backpressure(events: list[Event], max_video_events: int) -> list[Event]:
    kept: list[Event] = []
    video_seen = 0

    for event in events:
        if event.modality != "video":
            kept.append(event)
            continue
        video_seen += 1
        if video_seen <= max_video_events:
            kept.append(event)

    return kept


def commit_played_audio(events: list[Event], interruption_ms: int) -> list[Event]:
    committed: list[Event] = []

    for event in events:
        if event.modality != "assistant_audio":
            committed.append(event)
            continue
        if event.timestamp_ms <= interruption_ms:
            committed.append(
                Event(
                    sequence=event.sequence,
                    timestamp_ms=event.timestamp_ms,
                    modality=event.modality,
                    payload_ref=event.payload_ref,
                    committed=True,
                )
            )

    return committed


session = [
    Event(1, 0, "text", "user:compare-dashboard-and-sound"),
    Event(2, 20, "audio", "audio/chunk-0001.pcm"),
    Event(3, 40, "audio", "audio/chunk-0002.pcm"),
    Event(4, 60, "image", "images/dashboard-warning.jpg"),
    Event(5, 80, "video", "video/frame-0001.jpg"),
    Event(6, 100, "video", "video/frame-0002.jpg"),
    Event(7, 120, "video", "video/frame-0003.jpg"),
    Event(8, 140, "assistant_audio", "assistant/chunk-0001.pcm"),
    Event(9, 160, "assistant_audio", "assistant/chunk-0002.pcm"),
    Event(10, 180, "assistant_audio", "assistant/chunk-0003.pcm"),
]

problems = validate_session(session)
if problems:
    raise SystemExit("\n".join(problems))

reduced = apply_video_backpressure(session, max_video_events=2)
committed = commit_played_audio(reduced, interruption_ms=160)

print("validated events:", len(session))
print("events after video back-pressure:", len(reduced))
print("committed assistant chunks:", [e.payload_ref for e in committed if e.committed])
```

Expected output:

```text
validated events: 10
events after video back-pressure: 9
committed assistant chunks: ['assistant/chunk-0001.pcm', 'assistant/chunk-0002.pcm']
```

Now modify the script in three small ways. First, add a second image event after the video events and verify that ordering still passes. Second, change one timestamp so it moves backward and confirm the validator rejects the session. Third, change `max_video_events` from `2` to `1` and explain what kind of product would prefer that drop policy. A live assistant might prefer lower latency and fresher frames, while an offline audit system would usually preserve the full media record somewhere outside the realtime model path.

### Success Checklist

- [ ] The script runs with `.venv/bin/python` and produces the expected output before you modify it.
- [ ] You can identify which events are raw user evidence, which are assistant output, and which are committed history.
- [ ] You can explain why the third assistant audio chunk is not committed after an interruption at `160` ms.
- [ ] You can describe a video back-pressure policy in product terms instead of only saying "drop frames."
- [ ] You can name which Kubernetes component in your design would enforce message size, session rate, and downstream queue limits.

## Next Module

Multimodal AI is the last module in Phase 9. Continue to the next AI/ML Engineering section with [Deep Learning Foundations: NumPy, Pandas, and Data Tooling](../deep-learning/module-1.1-numpy-pandas-data-tooling/), where you will strengthen the model-building fundamentals that sit underneath many of the architectures discussed here.

## Sources

- [OpenAI Realtime and audio](https://developers.openai.com/api/docs/guides/realtime) - Documents realtime sessions as the path for live audio use cases and anchors the module's streaming voice-agent design discussion.
- [OpenAI Realtime API with WebRTC](https://developers.openai.com/api/docs/guides/realtime-webrtc) - Explains the WebRTC connection path for browser-based speech-to-speech applications and supports the transport tradeoff section.
- [Gemini Live API overview](https://ai.google.dev/gemini-api/docs/live-api) - Documents low-latency realtime voice and vision interactions for Gemini and supports the dated landscape snapshot.
- [vLLM Multimodal Inputs](https://docs.vllm.ai/en/stable/features/multimodal_inputs/) - Shows how open-model serving frameworks represent multimodal inputs and why schemas, caching, and model support must be verified.
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) - Documents two-way browser-server communication, which underpins the WebSocket streaming explanation.
- [MDN WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API) - Documents realtime audio, video, and data capabilities in browsers and supports the WebRTC design discussion.
- [Kubernetes Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) - Explains the Kubernetes GPU scheduling path and the role of device plugins for accelerator-backed workloads.
- [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) - Provides the official device-plugin framework reference for advertising GPUs and other specialized hardware.
- [Kubernetes Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/) - Documents Gateway API as a routing and infrastructure-provisioning family of Kubernetes APIs, supporting the gateway layer discussion.
- [Kubernetes Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) - Supports the explanation of requests, limits, and resource isolation for latency-sensitive services.
- [Kubernetes Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) - Supports the placement and resilience discussion for spreading workloads across failure domains.
- [NVIDIA Kubernetes Device Plugin](https://github.com/NVIDIA/k8s-device-plugin) - Provides a concrete vendor device-plugin example for exposing NVIDIA GPUs to Kubernetes workloads.
- [ImageBind: One Embedding Space To Bind Them All](https://arxiv.org/abs/2305.05665) - Primary research source for joint embeddings across images, text, audio, depth, thermal, and IMU data.
- [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020) - The CLIP paper supports the discussion of contrastive image-text embedding spaces and retrieval-mediated fusion.
- [An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929) - Primary source for the vision-transformer patch-tokenization concept used in the shared-token discussion.
- [ViViT: A Video Vision Transformer](https://arxiv.org/abs/2103.15691) - Primary source for spatiotemporal video tokens and efficient handling of long video token sequences.
- [Flamingo: a Visual Language Model for Few-Shot Learning](https://arxiv.org/abs/2204.14198) - Supports the explanation of interleaved visual and textual inputs in multimodal context.
- [Token Merging: Your ViT But Faster](https://arxiv.org/abs/2210.09461) - Supports the video and vision token-efficiency discussion without turning the module into a video deep dive.
