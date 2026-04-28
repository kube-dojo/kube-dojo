# Infrastructure Log: Chapter 54

## Technical Metrics & Constraints
- **Repository creation:** GitHub API reports `huggingface/transformers` was created 2018-10-29. Current stars/forks are dynamic and should not be used as historical facts.
- **Library scope in the 2020 paper:** Open-source Apache 2.0 library, available on GitHub, maintained by Hugging Face with support from over 400 external contributors.
- **Core abstractions:** Tokenizer, Transformer base model, and task head. Auto classes provide a unified API for fast switching between models and frameworks.
- **Model Hub 2020 snapshot:** The Transformers paper reports 2,097 user models in the Model Hub.
- **Model Hub mechanics:** Uploaded models receive canonical names, model pages, metadata, model cards, and optional live inference widgets. The paper's FlauBERT example loads tokenizer and model with `AutoTokenizer.from_pretrained(...)` and `AutoModel.from_pretrained(...)`.
- **Framework bridge:** The paper says models are available in PyTorch and TensorFlow with interoperability; legacy v4.0.1 docs describe deep interoperability between TensorFlow 2.0 and PyTorch.
- **Deployment bridge:** The paper mentions TorchScript, TensorFlow serving options, ONNX, JAX/XLA, TVM, and CoreML as deployment/intermediate-format paths.
- **Present-day Hub framing:** Current Hub docs describe models, datasets, and spaces as Git repositories, with version control and collaboration as core elements. Use this only as present-day continuity.

## Unknowns / Do Not Invent
- Exact internal decision process for the chatbot-to-library pivot is not anchored.
- Exact first release date of the original PyTorch BERT wrapper is not anchored beyond the GitHub repo creation date.
- Current Hub model counts are not historical 2020 counts.
- Production success stories beyond the paper's case studies are not anchored.
