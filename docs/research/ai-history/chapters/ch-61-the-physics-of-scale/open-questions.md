# Open Questions

## Resolved In This Contract

- **Primary source spine:** GPipe, Megatron-LM 2019, ZeRO, Megatron-LM 2021, PaLM, and Chinchilla were downloaded as PDFs and parsed with `pdftotext`.
- **Scope:** Chapter is about training-scale mechanics, not inference serving, energy, chips, or data exhaustion.
- **Repository metadata:** NVIDIA/Megatron-LM and DeepSpeed GitHub metadata can support project context only; do not use current star counts as historical adoption evidence.

## Remaining Review Questions

- **Claude source-fidelity review:** Changes requested on three page locators and then applied: Megatron 2019 Section 3 is pages 4-5, PaLM Section 4 is pages 7-9, and Chinchilla's 70B/1.4T claim is p.1 abstract plus p.2 introduction. Claude confirmed the Megatron 2021 null bytes are figure-symbol extraction noise and do not threaten source fidelity.
- **Gemini gap/capacity audit:** Confirm 4,600-5,800 words is honest and that PaLM/Chinchilla do not pull too much material from later Part 9 chapters.
- **Optional PipeDream/GShard:** Not required for current contract. Add only if a reviewer sees a real narrative gap; otherwise the GPipe/Megatron/ZeRO/PaLM spine is already dense enough.
