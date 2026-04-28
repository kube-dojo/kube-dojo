# Infrastructure Log: Chapter 53 - The Dawn of Few-Shot Learning

## Technical Metrics & Constraints
- **GPT-2 WebText corpus:** Built from outbound Reddit links with at least 3 karma. The GPT-2 paper reports 45 million links, slightly over 8 million documents after cleaning/deduplication, about 40 GB of text, and Wikipedia removal to reduce benchmark overlap complications.
- **GPT-2 input representation:** Byte-level BPE, vocabulary 50,257, context size 1024 tokens. Safe explanation: combines byte-level coverage with word-level efficiency; do not claim it solved tokenization.
- **GPT-2 model sizes:** Four models approximately 117M, 345M, 762M, and 1542M parameters. The largest is the 1.5B GPT-2 model.
- **GPT-2 training/evaluation caveat:** GPT-2 paper says all models still underfit WebText; Section 7 says practical zero-shot performance remained far from usable on many tasks.
- **GPT-2 release infrastructure:** Public `openai/gpt-2` GitHub repository was created 2019-02-11. Stars/forks are dynamic and should not be used for historical claims except with extraction date.
- **GPT-2 staged-release sequence:** 124M in February 2019, 355M in May 2019, 774M in August 2019, 1.5B in November 2019.
- **GPT-3 model scale:** GPT-3 paper reports eight model sizes from 125M to 175B parameters. The 175B model is the named GPT-3 model.
- **GPT-3 architecture/training:** Same broad model family as GPT-2, with alternating dense and locally banded sparse attention patterns; all models trained for 300B tokens; context window 2048 tokens; model partitioned across GPUs along depth and width for data-transfer/load-balancing reasons.
- **GPT-3 training mixture:** Filtered Common Crawl, WebText2, Books1, Books2, and English-language Wikipedia. Table 2.2 reports 410B filtered Common Crawl tokens, 19B WebText2, 12B Books1, 55B Books2, and 3B Wikipedia, with training weights not proportional to raw size.
- **GPT-3 evaluation interface:** Few-shot/one-shot/zero-shot demonstrations are placed in the prompt/context. No gradient updates or fine-tuning are performed in these evaluated settings.

## Unknowns / Do Not Invent
- Exact GPT-3 training GPU count, cluster topology, cost, wall-clock training time, and energy use are not anchored in the current sources.
- Exact GPT-2 training cost and cluster details are not anchored in the current sources.
- Specific OpenAI internal deliberations are not anchored beyond the published staged-release report.
