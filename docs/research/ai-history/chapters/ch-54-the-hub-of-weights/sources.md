# Sources: Chapter 54 - The Hub of Weights

## Verification Key

- Green: claim has direct primary/near-primary evidence plus paper sections, documentation, or contemporary reporting.
- Yellow: claim is supported by one source, dynamic metadata, or current documentation that should be phrased as present-day context.
- Red: claim should not be drafted unless new evidence is added.

## Primary and Near-Primary Sources

| Source | Use | Verification |
|---|---|---|
| Thomas Wolf et al., "Transformers: State-of-the-Art Natural Language Processing," EMNLP System Demonstrations, 2020. URL: https://aclanthology.org/2020.emnlp-demos.6.pdf | Core source for Transformers library, unified API, Model Hub, contributors, model count, loading/caching, model cards, inference widgets, case studies, and deployment bridge. | Green: Abstract and Introduction say Transformers is an open-source library to open model-pretraining advances to the wider ML community; the library provides state-of-the-art Transformer architectures under a unified API backed by pretrained models available for the community; the system supports distribution, fine-tuning, deployment, and compression. Section 2 distinguishes Transformers from Torch Hub/TensorFlow Hub by its domain-specific NLP support. Section 3 describes tokenizer/transformer/head abstractions, Auto classes, and framework switching. Section 4 says the Model Hub held 2,097 user models, stores canonical names, model pages, model cards, live inference widgets, and supports two-line download/cache/run for fine-tuning or inference. Section 5 says models are available in PyTorch and TensorFlow with interoperability, plus deployment pathways including TorchScript, TensorFlow serving options, ONNX, JAX/XLA, TVM, and CoreML. |
| Hugging Face Transformers v4.0.1 documentation, legacy docs. URL: https://huggingface.co/transformers/v4.0.1/index.html | Historical documentation for the library name, supported frameworks, model breadth, and stated low-barrier goals around sharing trained models. | Green/Yellow: docs say Transformers was formerly known as `pytorch-transformers` and `pytorch-pretrained-bert`; it provided BERT, GPT-2, RoBERTa, XLM, DistilBERT, XLNet and others; it claimed 32+ pretrained models in 100+ languages and deep interoperability between TensorFlow 2.0 and PyTorch; feature list says researchers can share trained models instead of always retraining and users can move a single model between TF2/PyTorch. Historical because it is versioned legacy documentation, but still documentation rather than a paper. |
| GitHub REST API record for `huggingface/transformers`. URL: https://api.github.com/repos/huggingface/transformers | Repository creation date and dynamic current metadata. | Green for creation date extracted on 2026-04-28: repo created 2018-10-29. Yellow for stars/forks because they are dynamic current metrics. |
| Hugging Face Model Hub documentation. URL: https://huggingface.co/docs/hub/models-the-hub | Present-day description of the Model Hub role. | Yellow: current docs say the Model Hub lets the community host model checkpoints for storage, discovery, and sharing, and download pretrained models with `huggingface_hub`, Transformers, or integrated libraries. Use as present-day continuity, not proof of the 2020 state. |
| Hugging Face Hub repository documentation. URL: https://huggingface.co/docs/hub/repositories | Present-day anchor for Git-based repository framing. | Yellow: current docs say models, spaces, and datasets are hosted as Git repositories and that version control and collaboration are core elements of the Hub. Use as current infrastructure framing, not a 2020 historical metric. |

## Contemporary Reporting

| Source | Use | Verification |
|---|---|---|
| Romain Dillet, "Hugging Face wants to become your artificial BFF," TechCrunch, March 9, 2017. URL: https://techcrunch.com/2017/03/09/hugging-face-wants-to-become-your-artificial-bff/ | Chatbot origin, founders named in 2017 coverage, consumer-app framing. | Green/Yellow: article describes Hugging Face as a new chatbot app for bored teenagers, co-founded by Clement Delangue and Julien Chaumond, with a digital friend/chat interface and AI-for-fun framing. It does not name Thomas Wolf as a co-founder in this article. |
| Romain Dillet, "Hugging Face raises $15 million to build the definitive natural language processing library," TechCrunch, December 17, 2019. URL: https://techcrunch.com/2019/12/17/hugging-face-raises-15-million-to-build-the-definitive-natural-language-processing-library/ | Contemporary pivot evidence from chatbot app to open-source NLP library and early adoption metrics. | Green/Yellow: article says the company first built an artificial-BFF chatbot app, more recently released an open-source NLP library, and that Transformers had over a million downloads and 19,000 GitHub stars at the time. Treat download/star numbers as reported 2019 snapshots, not current values. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| The practical problem after BERT/GPT was not only model invention but distribution, fine-tuning, deployment, compression, framework support, and reuse. | Research Artifact Problem | Transformers paper Abstract/Introduction | Transformers paper Related Work | Green | Use this as the chapter's systems thesis. |
| Hugging Face began publicly as a consumer chatbot app before becoming known for NLP tooling. | Chatbot Company Finds Tooling Problem | TechCrunch 2017 chatbot article | TechCrunch 2019 funding/library article | Green/Yellow | Do not invent internal motives; "coverage shows" is safe. |
| By December 2019, TechCrunch framed Hugging Face as building an open-source NLP library, with over a million downloads and 19,000 GitHub stars. | Chatbot Company Finds Tooling Problem | TechCrunch 2019 | GitHub API current metadata as dynamic continuity | Yellow | Reported snapshot only; do not update 2019 values from current API. |
| Transformers used a unified API over many Transformer model variants and Auto classes to switch between models and frameworks. | Adapter Layer | Transformers paper Section 3 | v4.0.1 docs | Green | Keep the API explanation concrete. |
| Transformers organizes model use around tokenizers, base Transformer models, and task heads. | Adapter Layer | Transformers paper Section 3 and Figure 2 | Examples in Section 3 | Green | Good pedagogical spine. |
| Transformers maintained PyTorch/TensorFlow interoperability and supported deployment paths like TorchScript, TensorFlow serving options, ONNX, and CoreML. | Adapter Layer / Limits | Transformers paper Section 5 | v4.0.1 docs framework notes | Green | Do not imply every model worked equally in every framework. |
| The Model Hub had 2,097 user models in the paper's 2020 snapshot. | Model Hub | Transformers paper Section 4 | Figure 1 download trend | Green | Historical number, not current count. |
| The Model Hub gave models canonical names and enabled two-line download/cache/run for fine-tuning or inference. | Model Hub | Transformers paper Section 4 | v4.0.1 docs | Green | This is the core "weights become packages" scene. |
| Model pages could include metadata, model cards, citations, datasets, caveats, live inference widgets, benchmark links, and visualizations. | Model Hub | Transformers paper Section 4 and Figure 3 | Current Model Hub docs | Green/Yellow | Model-card details are Green from paper; current docs are continuity. |
| Current Hub documentation describes models/datasets/spaces as Git repositories, making version control and collaboration core Hub elements. | Model Hub / Epilogue | Hub repository docs | Current Model Hub docs | Yellow | Present-day epilogue only; do not project current Xet/safetensors details backward to 2020. |
| Hugging Face lowered friction for open model reuse, but did not erase compute, quality, safety, licensing, or deployment constraints. | Lowering Friction | Transformers paper deployment/limitations by implication | Current docs and model-card caveats | Green/Yellow | Interpretive but essential guardrail. |

## Conflict Notes

- Do not write "Hugging Face solved access to foundation models." It made reuse easier for shared/open models.
- Do not write "GitHub for AI" as a literal sourced claim. The current docs support Git-based repositories; the phrase is a metaphor at best.
- Do not claim all model weights were open, safe, or production-ready because they appeared on the Hub.
- Do not invent a scene where Delangue/Wolf "realized" the side project was more popular than the chatbot. Use contemporary coverage and paper evidence.
- Do not say Hugging Face alone created open-source NLP infrastructure. The paper explicitly situates Transformers among Torch Hub, TensorFlow Hub, AllenNLP, Fairseq, OpenNMT, Texar, Megatron-LM, Marian NMT, spaCy, Stanza, and others.
- Do not use current Model Hub counts as historical 2020 facts.
- Do not write "three lines of code" unless a separate source is added. The anchored paper example uses two `from_pretrained(...)` calls.

## Page/Section Anchor Worklist

- Transformers paper: Done for Abstract, Introduction, Sections 2, 3, 4, 5, Figures 1/3, and Conclusion.
- v4.0.1 Transformers docs: Done for former names, model breadth, framework interoperability, and share-rather-than-retrain framing.
- GitHub API: Done for `huggingface/transformers` creation date.
- TechCrunch 2017: Done for chatbot app origin and founders named in article.
- TechCrunch 2019: Done for chatbot-to-library pivot coverage and reported 2019 adoption snapshot.
- Current Hub docs: Done for Model Hub and Git repository present-day framing.
