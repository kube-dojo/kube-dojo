# Scene Sketches: Chapter 52

## Scene 1: The Left-Context Constraint
- **Action:** Explain GPT-style constrained self-attention and ELMo-style shallow bidirectionality as the setup for BERT's "deeply bidirectional" claim.
- **Evidence anchors:** BERT Section 1, Section 3, Figure 3; Google blog "What Makes BERT Different?"
- **Drafting warning:** Do not say left-to-right models have no value or no context. The precise claim is that they cannot condition each token on both left and right context at every layer during pre-training.

## Scene 2: The Masking Trick
- **Action:** Show why naive bidirectional prediction would let a token see itself, then introduce MLM as the workaround: mask selected tokens and predict the originals.
- **Evidence anchors:** BERT Section 3.1; Google blog masking example.
- **Drafting warning:** Keep the 15% and 80/10/10 mechanics exact.

## Scene 3: Sentence-Pair Plumbing
- **Action:** Explain [CLS], [SEP], segment embeddings, and NSP as infrastructure for QA, NLI, paraphrase, and other paired-input tasks.
- **Evidence anchors:** BERT Section 3 input representation and NSP; Section 3.2 fine-tuning examples.
- **Drafting warning:** Later critique of NSP is not a blocker; do not retroactively judge the 2018 result unless sourced.

## Scene 4: The Checkpoint Economy
- **Action:** Contrast expensive pre-training with relatively cheap fine-tuning from the released checkpoint.
- **Evidence anchors:** BERT Appendix A.2; BERT Section 3.2; Google blog release.
- **Drafting warning:** No dollar-cost estimates. Use hardware/time: 4/16 Cloud TPUs for pre-training; one Cloud TPU or a few GPU hours for fine-tuning.

## Scene 5: The Benchmark Break
- **Action:** Move through GLUE, SQuAD, and SWAG as receipts that the same pre-trained model could be adapted across task families.
- **Evidence anchors:** BERT Abstract; Section 4; Tables 1-4; Google blog results section.
- **Drafting warning:** Do not imply leaderboard permanence. Say "reported" or "at the time of the paper/blog."

## Scene 6: The Released Artifact
- **Action:** End with source code and pre-trained models as distribution artifacts: BERT is a checkpoint people can adapt, not merely a paper to read.
- **Evidence anchors:** Google blog; GitHub API; BERT paper code note.
- **Drafting warning:** Hugging Face and general model hubs stay in Chapter 54.
