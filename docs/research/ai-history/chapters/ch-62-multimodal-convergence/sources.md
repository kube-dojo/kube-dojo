# Sources: Chapter 62 - Multimodal Convergence

## Research Status

Contract is `capacity_plan_anchored` as of 2026-04-28. Sources below were
verified from arXiv/OpenAI PDFs, official OpenAI pages, and official Google
blog/report pages. Gemini gap-audited the scope and requested a lower
3,800-4,800 word natural cap to avoid padding from adjacent chapters.

## Primary Source Spine

| Source | Use | Verification |
|---|---|---|
| Alec Radford et al., "Learning Transferable Visual Models From Natural Language Supervision" (CLIP), arXiv:2103.00020. PDF: https://arxiv.org/pdf/2103.00020 | Research bridge: natural-language supervision for image representations and zero-shot visual concepts. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says CLIP trains from scratch on 400M image-text pairs and uses natural language to reference learned visual concepts for zero-shot transfer. Figure 1/page 2 describes joint image/text encoders for contrastive pretraining. |
| Jean-Baptiste Alayrac et al., "Flamingo: a Visual Language Model for Few-Shot Learning," arXiv:2204.14198. PDF: https://arxiv.org/pdf/2204.14198 | Interleaved image/video/text prompting and few-shot visual-language models. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says Flamingo handles arbitrarily interleaved visual and textual data and ingests images or videos. Section 1/pages 3-4 says it takes text interleaved with images/videos and produces free-form text. |
| OpenAI, "GPT-4 Technical Report," arXiv:2303.08774. PDF: https://arxiv.org/pdf/2303.08774 | GPT-4 as large multimodal model with image/text inputs and text outputs; visual-input example. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says GPT-4 can process image and text inputs and produce text outputs. Section 4.1/page 17 says prompts can contain arbitrarily interlaced text and images. |
| OpenAI, "GPT-4V(ision) System Card," September 2023. PDF: https://cdn.openai.com/papers/GPTV_System_Card.pdf | Deployment and safety of GPT-4 vision: image analysis, risk surfaces, Be My AI, jailbreaks, medical limits. | Green: PDF downloaded 2026-04-28. Page 1 says GPT-4V enables users to instruct GPT-4 to analyze image inputs. Pages 1-2 describe early access and image/text training. Pages 2-3 discuss Be My AI beta and hallucination/error issues. Pages 6-10 describe image-borne jailbreaks, scientific/medical limitations, and unsafe visual assumptions. |
| Google, "Gemini: A Family of Highly Capable Multimodal Models," arXiv:2312.11805. PDF: https://arxiv.org/pdf/2312.11805 | Source-bound native multimodality claim and Gemini family/product framing. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says Gemini exhibits capabilities across image, audio, video, and text. Introduction/page 1 says Gemini was trained jointly across image, audio, video, and text. Architecture section/pages 3-4 says Gemini models support interleaved text, image, audio, and video inputs and can produce text and image outputs. |
| OpenAI, "GPT-4o System Card," August 8, 2024. PDF: https://cdn.openai.com/gpt-4o-system-card.pdf | Omni model: real-time audio/vision/text interface, data/training and safety. | Green: PDF downloaded 2026-04-28. Introduction/page 1 says GPT-4o accepts any combination of text, audio, image, and video and generates text, audio, and image outputs; it is trained end-to-end across text, vision, and audio; it can respond to audio in as little as 232 ms, average 320 ms. Pages 2-6 discuss multimodal data, voice risks, and evaluation limitations. |
| OpenAI, "Hello GPT-4o," May 13, 2024. URL: https://openai.com/index/hello-gpt-4o/ | Product release framing for real-time audio, vision, and text; contrast with prior three-model voice pipeline. | Green: official OpenAI page opened 2026-04-28. Lines 27-32 announce GPT-4o and real-time audio/vision/text reasoning; lines 47-48 repeat input/output and latency claims; lines 82-84 contrast prior Voice Mode's three-model pipeline with GPT-4o's single end-to-end model. |
| OpenAI, "Video generation models as world simulators," February 15, 2024. URL: https://openai.com/index/video-generation-models-as-world-simulators/ | Sora technical report: spacetime patches, video/image latent codes, minute-scale video, limitations. | Green: official OpenAI page opened 2026-04-28. Lines 33-40 define Sora as text-conditional diffusion trained on videos/images and capable of up to one minute of high-fidelity video; lines 41-58 explain visual/spacetime patches and diffusion transformers; lines 118-139 give simulation claims and explicit limitations. |
| OpenAI, "Sora System Card," December 2024. URL: https://openai.com/index/sora-system-card/ | Sora deployment/safety, data categories, red teaming, moderation stack. | Green: official OpenAI page opened 2026-04-28. Lines 51-59 describe visual patches, dataset categories, and pretraining filtering; lines 60-75 describe deployment prep and red teaming; lines 84-104 describe evaluations and multimodal moderation. |
| Google, "New generative media models and tools, built with and for creators," May 14, 2024. URL: https://blog.google/innovation-and-ai/products/google-generative-ai-veo-imagen-3/ | Veo as competing video-generation product claim and responsible deployment framing. | Green/Yellow: official Google blog opened 2026-04-28. Lines 263-264 introduce Veo/Imagen 3; lines 311-322 describe Veo generating 1080p videos longer than a minute, natural-language/visual semantics, and private preview; lines 393-397 describe safety tests, filters, guardrails, SynthID, and watermarking. Use as product framing, not independent evaluation. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| CLIP trained image and text encoders on 400M image-text pairs and used natural language for zero-shot visual transfer. | Language Learns To Point | CLIP p.1/p.2 | N/A | Green | Use as precursor, not product-era chapter center. |
| Flamingo handled interleaved visual and textual data, including images and videos, and produced free-form text. | Language Learns To Point | Flamingo p.1 and Section 1 | Figure 3 | Green | Bridges CLIP-style alignment to assistant-style prompting. |
| GPT-4 was reported as a multimodal model that accepts image/text inputs and produces text outputs. | Vision Enters Chat | GPT-4 Technical Report p.1 | Section 4.1 p.17 | Green | Do not imply image/audio/video outputs. |
| GPT-4 visual prompts could interlace text and images over documents, diagrams, screenshots, and photos. | Vision Enters Chat | GPT-4 Section 4.1 p.17 | Appendix visual examples | Green | Good scene anchor for visual assistant. |
| GPT-4V expanded GPT-4 deployment to user-provided image inputs and introduced new multimodal risk surfaces. | Vision Enters Chat | GPT-4V System Card p.1 | Safety evaluation sections | Green | Include hallucination/error caveat. |
| Be My AI beta surfaced usefulness and hallucination/error limitations for blind and low-vision users. | Vision Enters Chat | GPT-4V System Card pp.2-3 | Be My Eyes deployment discussion | Green | Keep careful and source-bound. |
| GPT-4V red-teamers found scientific/medical visual limitations; OpenAI says GPT-4V is not fit for medical function or professional medical advice. | Vision Enters Chat | GPT-4V pp.7-10 | Figures 4-7 | Green | Essential no-overclaim guardrail. |
| Gemini report says Gemini was trained jointly across image, audio, video, and text. | Native Multimodality | Gemini p.1 | Architecture section pp.3-4 | Green | This is the safe definition of "natively multimodal." |
| Gemini supports interleaved text, image, audio, and video inputs and can produce text and image outputs. | Native Multimodality | Gemini pp.3-4 | Figure 2 | Green | Do not claim Gemini 1.0 produced audio/video outputs from this report. |
| GPT-4o accepts text/audio/image/video inputs and generates text/audio/image outputs. | Speech Collapses Interface | GPT-4o System Card p.1 | Hello GPT-4o lines 47-48 | Green | Explicitly no video output in the cited system card. |
| GPT-4o was trained end-to-end across text, vision, and audio, and could respond to audio in 232 ms minimum / 320 ms average. | Speech Collapses Interface | GPT-4o System Card p.1 | Hello GPT-4o lines 47, 82-84 | Green | Use as latency/product-interface shift. |
| Prior ChatGPT Voice Mode used a three-model pipeline, losing tone, multiple speakers, background noise, laughter/singing/emotion. | Speech Collapses Interface | Hello GPT-4o lines 82-84 | GPT-4o System Card p.1 | Green | Strong explanatory contrast. |
| GPT-4o's voice modality introduced risks around unauthorized voice generation, speaker identification, and disparate performance on voice inputs. | Speech Collapses Interface | GPT-4o System Card pp.8-13 | System Card evaluation sections | Green | Safety, not panic. |
| Sora trained text-conditional diffusion models jointly on videos and images using spacetime patches of video/image latent codes. | Video Hard Case | OpenAI world-simulators lines 33-55 | Sora System Card lines 51-52 | Green | Technical anchor for video-as-tokenization. |
| OpenAI described Sora as capable of generating up to one minute of high-fidelity video and videos/images of variable duration, resolution, and aspect ratio. | Video Hard Case | OpenAI world-simulators lines 33-40, 52-66 | Sora System Card | Green | Product/technical claim, not independent evaluation. |
| OpenAI explicitly says Sora has simulator limitations, including incorrect physics and object-state changes. | Video Hard Case | OpenAI world-simulators lines 118-139 | Sora System Card eval/safety sections | Green | Do not let "world simulator" become settled fact. |
| Veo was introduced as Google's video-generation model for 1080p videos longer than a minute. | Video Hard Case | Google blog lines 263-264, 311-322 | N/A | Yellow | Official product claim only; no independent evaluation. |
| Sora/Veo deployment discussion centered safety tests, red teams, filters, guardrails, provenance/watermarking. | Video Hard Case | Sora System Card lines 60-75, 84-104; Google blog lines 393-397 | N/A | Green/Yellow | Use as safety/evaluation complexity, not full copyright chapter. |

## Conflict Notes

- Do not infer physical understanding from plausible video. Sora page itself
  lists simulator limitations.
- Do not use "native multimodal" as a generic marketing adjective; attribute it
  to the Gemini report's joint-training claim.
- Do not let benchmark tables become Ch66. Mention only local technical
  evidence needed to explain the modality shift.
- Do not let data sourcing, artists, copyright, or Shutterstock/Pond5 become
  Ch68 here. Acknowledge and hand off.
- Do not make Veo a peer-reviewed technical anchor; it is official product
  framing unless a stronger technical report is added.

## Anchor Worklist For Prose

- Use CLIP/Flamingo for 600-800 words of precursor bridge at most.
- Use GPT-4 Section 4.1 and GPT-4V pp.1-10 for the visual assistant scene.
- Use Gemini p.1/pp.3-4 to define "natively multimodal" safely.
- Use GPT-4o System Card p.1 and Hello GPT-4o lines 47, 82-84 for audio latency
  and the three-model-pipeline contrast.
- Use Sora world-simulators lines 33-58 and 118-139 for video architecture and
  limitations; keep the Sora/Veo scene around 750-950 words unless a stronger
  technical Veo anchor is added.
- Use Sora System Card and Google Veo blog only for deployment/safety/product
  framing.
