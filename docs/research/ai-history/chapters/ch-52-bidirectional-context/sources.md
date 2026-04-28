# Sources: Chapter 52 - Bidirectional Context

## Verification Key

- Green: claim has primary evidence plus independent confirmation or internally corroborating paper sections/tables.
- Yellow: claim has one strong source, dynamic metadata, or broad cultural inference.
- Red: claim should not be drafted except as blocked framing.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova, "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding," arXiv:1810.04805, 2018. URL: https://arxiv.org/pdf/1810.04805 | Core source for architecture, MLM, NSP, pre-training/fine-tuning, data, TPU training, benchmark results, and ablations. | Green: Abstract says BERT is designed to pre-train deep bidirectional representations from unlabeled text by conditioning on both left and right context in all layers, and that fine-tuning adds one output layer; Section 1 contrasts feature-based and fine-tuning approaches and says standard language models are unidirectional; Section 3 defines the two-step pre-training/fine-tuning framework; Section 3.1 defines MLM, 15% WordPiece masking, 80/10/10 replacement, and NSP; Section 3.2 says fine-tuning is relatively inexpensive and gives the single Cloud TPU/few GPU-hours claim; Section 4 reports 11 NLP task results; Section 5.1 ablates NSP and left-to-right models; Appendix A.2 gives BooksCorpus/Wikipedia, 4/16 Cloud TPU pre-training, and 4-day runs. |
| Google Research, "Open Sourcing BERT: State-of-the-Art Pre-training for Natural Language Processing," 2018. URL: https://research.google/blog/open-sourcing-bert-state-of-the-art-pre-training-for-natural-language-processing/ | Release framing, code/model availability, public explanation of bidirectionality, benchmark claims, and infrastructure bridge. | Green: page says Google open sourced BERT; release included TensorFlow source code and pre-trained language representation models; anyone can train a state-of-the-art question-answering system in about 30 minutes on a single Cloud TPU or a few hours on a single GPU; BERT builds on GPT, ELMo, ULMFiT, etc.; it explains bank/account vs bank/river context; states Cloud TPUs and Transformer architecture were critical; reports SQuAD and GLUE improvements. |
| GitHub REST API record for `google-research/bert`. URL: https://api.github.com/repos/google-research/bert | Repository creation date and current repository metadata. | Green for creation date extracted on 2026-04-28: repo created 2018-10-25. Yellow for stars/forks because they are dynamic current metrics. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Dan Jurafsky and James H. Martin, *Speech and Language Processing*, 3rd ed. draft. | Optional textbook framing for contextual embeddings and Transformer encoders. | Yellow until exact chapter/section anchor is extracted. |
| GLUE, SQuAD, SWAG benchmark papers and leaderboards. | Optional independent benchmark context. | Yellow unless used directly; BERT paper and Google blog are enough for reported BERT results. |
| Wikipedia pages on BERT, contextual embeddings, and masked language modeling. | Discovery aid only. | Yellow/Red for citation: do not use as final prose anchor. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| BERT's distinguishing claim is deep bidirectional pre-training, not human-like comprehension. | Left-Context Constraint | BERT Abstract; Section 1; Google blog "What Makes BERT Different?" | BERT Section 5.1 ablation | Green | Use "representations," not "understanding" except in paper-title context. |
| GPT-style Transformer pre-training used constrained left-context attention, while BERT used bidirectional self-attention in the encoder. | Left-Context Constraint | BERT Section 3 model architecture; Figure 3 | Google blog architecture comparison | Green | Keep GPT details short; Chapter 53 owns GPT. |
| MLM masks 15% of WordPiece positions and predicts original tokens; BERT uses 80% [MASK], 10% random token, 10% unchanged token among selected positions. | Masking Trick | BERT Section 3.1 | Google blog explanation | Green | Good pedagogical core. |
| NSP trains whether sentence B follows sentence A, with 50% IsNext and 50% NotNext examples. | Sentence Relationships | BERT Section 3.1 | BERT Section 5.1 ablation | Green | Later literature may critique NSP; not needed here unless framed as future caveat. |
| BERT uses [CLS], [SEP], token, segment, and position embeddings to support sentence and sentence-pair tasks. | Sentence Relationships | BERT Section 3; Figure 2 | BERT fine-tuning sections | Green | Useful for explaining why one checkpoint can serve many task formats. |
| Pre-training used BooksCorpus (800M words) plus English Wikipedia (2,500M words). | Checkpoint Economy | BERT Appendix A.2 / Pre-training data | Google blog says pre-training uses unannotated web text/Wikipedia | Green | Use exact corpus names from paper. |
| BERTBASE and BERTLARGE had 110M and 340M parameters respectively. | Checkpoint Economy | BERT Section 3 model architecture | BERT Appendix A.2 training setup | Green | Parameter scale helps explain checkpoint value. |
| BERTBASE trained on 4 Cloud TPUs, BERTLARGE on 16 Cloud TPUs, and each pre-training took 4 days. | Checkpoint Economy | BERT Appendix A.2 | Google blog Cloud TPU discussion | Green | Blocks invented dollar-cost claims. |
| Fine-tuning was relatively inexpensive compared with pre-training: paper says all results can be replicated in at most 1 hour on a single Cloud TPU or a few hours on a GPU from the same pre-trained model. | Checkpoint Economy | BERT Section 3.2 | Google blog release framing | Green | Use exact wording; no dollar estimates. |
| BERT reported state-of-the-art results on 11 NLP tasks including GLUE, SQuAD, and SWAG. | Benchmark Break | BERT Abstract; Section 4; Tables 1-4 | Google blog results section | Green | Cite reported results, not permanent leaderboard dominance. |
| Google open-sourced BERT code and pre-trained models. | Open Release | Google blog; BERT paper code note | GitHub API repo creation date | Green | Bridge to Ch51/Ch54. |
| A 4,000-5,000 word chapter is feasible from current sources, but community adoption should stay Yellow without more sources. | All | This source table and brief capacity plan | Ch50/Ch51 contract pattern | Green/Yellow | Do not pad with invented user stories. |

## Conflict Notes

- Do not write "true comprehension" except to reject it.
- Do not write "anyone could cheaply train BERT from scratch." The release made fine-tuning accessible; pre-training remained expensive.
- Do not invent dollar costs. Use TPU/GPU time claims from the paper/blog.
- Do not make BERT a GPT chapter. GPT-style left-to-right modeling is context, not the center.
- Do not claim BERT was the final dominant NLP paradigm. Later GPT-style generative models change the story in Chapter 53.

## Page/Section Anchor Worklist

- BERT paper: Done for Abstract, Sections 1, 3, 3.1, 3.2, 4, 5.1, Appendix A.2, Tables 1-5, and Figure 3.
- Google BERT blog: Done for open-source release, public bidirectionality explanation, code/model release, TPU/GPU fine-tuning claims, and results framing.
- GitHub API: Done for `google-research/bert` creation date.
