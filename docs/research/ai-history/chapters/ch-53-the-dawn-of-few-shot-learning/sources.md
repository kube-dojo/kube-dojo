# Sources: Chapter 53 - The Dawn of Few-Shot Learning

## Verification Key

- Green: claim has direct primary evidence plus internal corroboration across paper sections, tables, or release documentation.
- Yellow: claim is supported by one primary source, dynamic metadata, or reasonable interpretation but should be phrased carefully.
- Red: claim should not be drafted unless new evidence is added.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Alec Radford, Jeffrey Wu, Rewon Child, David Luan, Dario Amodei, Ilya Sutskever, "Language Models are Unsupervised Multitask Learners," OpenAI, 2019. URL: https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf | GPT-2 thesis, WebText construction, byte-level BPE, model sizes, zero-shot transfer, and limitations. | Green: Abstract says language models begin to learn NLP tasks without explicit supervision on WebText, largest model is 1.5B parameters, and zero-shot results are state-of-the-art on 7 of 8 language-modeling datasets while still underfitting WebText. Section 1 says current systems remain narrow experts and the paper demonstrates zero-shot downstream tasks without parameter or architecture modification. Section 2.1 gives WebText details: outbound Reddit links with at least 3 karma, 45 million links, slightly over 8 million documents, 40 GB text, Wikipedia removed. Section 2.2 explains byte-level BPE. Table 2 and Section 2.3 give 117M/345M/762M/1542M model sizes, 1024-token context, and vocabulary 50,257. Section 7 says zero-shot performance is still far from usable for practical applications and many tasks may be no better than random. |
| Irene Solaiman, Miles Brundage, Jack Clark, Amanda Askell, Ariel Herbert-Voss, Jeff Wu, Alec Radford, Gretchen Krueger, Jong Wook Kim, Sarah Kreps, et al., "Release Strategies and the Social Impacts of Language Models," OpenAI Report, November 2019. URL: https://arxiv.org/pdf/1908.09203 | GPT-2 staged release timeline, misuse concerns, detection uncertainty, and publication-norm framing. | Green: Introduction and Section 1 say OpenAI released 124M in February, 355M in May, 774M in August, and 1.5B in November 2019; withheld larger models initially due to misuse concerns including fake news, impersonating others in email, and abusive social-media automation; staged release gave time for risk and benefit analyses; Appendix B repeats the timeline. Section 3.1/3.2 discusses synthetic-text detection and says existing research had not achieved perfect accuracy. |
| Tom B. Brown et al., "Language Models are Few-Shot Learners," arXiv:2005.14165, 2020. URL: https://arxiv.org/pdf/2005.14165 | GPT-3 core source: 175B autoregressive model, few-shot/one-shot/zero-shot definitions, no gradient updates, training mixture, model parallelism, results, limitations, and misuse framing. | Green: Abstract says GPT-3 has 175B parameters and is applied without gradient updates or fine-tuning, with tasks and demonstrations specified via text. Section 1 defines in-context learning and says terms remain agnostic on whether the model learns from scratch or recognizes patterns seen during training. Section 1/2 defines few-shot, one-shot, zero-shot, and notes GPT-3 could be fine-tuned in principle. Section 2.1 says eight model sizes from 125M to 175B, 2048-token context, 300B training tokens, and partitioning across GPUs by depth and width. Section 2.2 gives Common Crawl/WebText2/Books/Wikipedia training mixture. Section 3.2 gives closed-book QA examples. Section 3.9.4 gives human detection results for synthetic news. Sections 5 and 6 document limitations and broader impacts. |
| GitHub REST API record for `openai/gpt-2`. URL: https://api.github.com/repos/openai/gpt-2 | Public repository creation date and dynamic repository metadata. | Green for creation date extracted on 2026-04-28: repo created 2019-02-11. Yellow for stars/forks because they are dynamic current metrics. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Kaplan et al., "Scaling Laws for Neural Language Models," 2020. | Context bridge to Chapter 55 only. | Yellow here; Chapter 55 owns scaling-law exposition. Use only to say GPT-3 paper cites scaling-law expectations, not to explain the full result. |
| Wikipedia pages on GPT-2, GPT-3, OpenAI, and in-context learning. | Discovery aid for names, dates, and related sources. | Yellow/Red for citation: do not use as final prose anchor. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| GPT-2 framed broad web language modeling as a route to zero-shot task transfer without task-specific parameter or architecture changes. | From Fine-Tuning to Text Instructions | GPT-2 Abstract and Section 1 | GPT-2 Section 7 caveats | Green | Say "reported zero-shot task transfer," not "learned reasoning." |
| WebText was built from outbound Reddit links with at least 3 karma, producing slightly over 8 million documents and about 40 GB of cleaned text, with Wikipedia removed. | WebText and Zero-Shot Bet | GPT-2 Section 2.1 | GPT-2 evaluation caveat about overlap | Green | Avoid claiming WebText was representative of the whole web. |
| GPT-2 used byte-level BPE to retain broad string coverage while keeping a practical vocabulary. | WebText and Zero-Shot Bet | GPT-2 Section 2.2 | GPT-2 Section 2.3 vocabulary 50,257 | Green | Good pedagogy layer; do not overstate as solving all tokenization problems. |
| GPT-2 evaluated four model sizes, with the largest around 1.5B parameters and a 1024-token context. | WebText and Zero-Shot Bet | GPT-2 Table 2 and Section 2.3 | GPT-2 Abstract | Green | Use 1542M for table precision or 1.5B for prose. |
| GPT-2 achieved state-of-the-art zero-shot results on 7 of 8 tested language-modeling datasets while still underfitting WebText. | WebText and Zero-Shot Bet | GPT-2 Abstract | GPT-2 Section 3 and Section 7 | Green | Restrict "state of the art" to paper's tested language-modeling datasets. |
| GPT-2's own paper says zero-shot performance was promising but far from usable for practical applications and likely weak on many tasks. | Capability With Caveats | GPT-2 Section 7 | GPT-3 paper cites GPT-2 in-context results as far inferior to fine-tuning | Green | This is the anti-hype ballast. |
| OpenAI's GPT-2 release was staged: 124M in February 2019, 355M in May, 774M in August, and 1.5B in November. | Staged Release | Release Strategies Section 1 and Appendix B | GitHub API repo creation date for public repo | Green | Do not say the full model was never released. |
| OpenAI justified the staged release with misuse concerns and a desire for time to conduct risk/benefit analysis. | Staged Release | Release Strategies Introduction and Section 1 | Release Strategies Section 6 publication-norm discussion | Green | Safe wording is "OpenAI said" or "the report framed." |
| Detection was treated as promising but imperfect; the report says existing research had not achieved perfect accuracy and often assumed limited adversaries. | Staged Release | Release Strategies automated detection discussion | GPT-3 Section 6.1 later misuse framing | Green | Useful bridge from GPT-2 to GPT-3 risk continuity. |
| GPT-3 was a 175B-parameter autoregressive language model evaluated without gradient updates or fine-tuning, using prompts and demonstrations as text. | GPT-3 and Prompt as Training Set | GPT-3 Abstract; Sections 1 and 2 | GPT-3 Figure 2.1 definitions | Green | This is the chapter center. |
| In-context learning means the "inner loop" occurs inside the forward pass over a sequence, not by updating weights. | GPT-3 and Prompt as Training Set | GPT-3 Figure 1.1 caption and Section 1 | GPT-3 few-shot definition | Green | The paper explicitly remains agnostic about learn-from-scratch vs pattern recognition. |
| Few-shot, one-shot, and zero-shot are evaluation settings defined by how many demonstrations appear in the context window. | GPT-3 and Prompt as Training Set | GPT-3 Section 2 and Figure 2.1 | GPT-3 Section 1 definitions | Green | Explain simply with text examples; no API details unless sourced. |
| GPT-3 trained eight model sizes from 125M to 175B, for 300B tokens, with 2048-token context and GPU partitioning by depth and width. | GPT-3 and Prompt as Training Set | GPT-3 Table 2.1 and Section 2.1 | GPT-3 Abstract parameter claim | Green | Avoid dollar-cost or exact GPU-count claims unless another source is added. |
| GPT-3 training data mixed filtered Common Crawl, WebText2, Books1, Books2, and Wikipedia, weighted by quality rather than dataset size. | GPT-3 and Prompt as Training Set | GPT-3 Section 2.2 and Table 2.2 | GPT-3 Appendix A if needed | Green | Use exact token quantities only if prose needs them. |
| GPT-3 showed strong few-shot closed-book QA examples, including TriviaQA, but mixed results on WebQuestions and Natural Questions. | Capability With Caveats | GPT-3 Section 3.2 | GPT-3 limitations section | Green | Do not cherry-pick only wins. |
| GPT-3 news-generation experiments found human detection near chance for selected 175B outputs, under the paper's experimental setup. | Capability With Caveats | GPT-3 Section 3.9.4 and Table 3.11 | GPT-3 Section 6.1 misuse discussion | Green | Say "selected experimental setup," not general human indistinguishability. |
| GPT-3's own limitations include repetition, long-passage coherence failures, common-sense physics weakness, failures on WIC/ANLI/subsets of reading comprehension, lack of grounding, and bias/misuse risk. | Capability With Caveats | GPT-3 Sections 5 and 6 | GPT-2 staged-release report | Green | Essential for honesty-over-output. |
| GPT-3 should be called the beginning of the prompt era, not the end of fine-tuning. | All | GPT-3 says fine-tuning remains possible and future work; few-shot can underperform fine-tuned SOTA | Ch57/Ch59 book outline | Green/Yellow | This is interpretive but well supported. |

## Conflict Notes

- Do not write "emergence" as a source-backed GPT-3 paper claim unless quoting later literature added in another source. The GPT-3 paper uses in-context learning, meta-learning, and scale.
- Do not write "GPT-3 learned new tasks from scratch." The paper explicitly leaves open whether the model learns from scratch at inference time or recognizes patterns from training.
- Do not write "no fine-tuning was needed" without qualification. The evaluated setup used no gradient updates; fine-tuning remained possible and sometimes stronger.
- Do not write "OpenAI refused forever to release GPT-2." The full 1.5B model was released in November 2019.
- Do not invent exact compute cost, GPU count, cluster size, or training dates for GPT-3. Current anchor supports model parallel partitioning across GPUs, 300B tokens, and model sizes, not the full cluster bill.
- Do not lean on blocked OpenAI blog pages. The contract uses PDFs and GitHub API records that were directly fetched and parsed.

## Page/Section Anchor Worklist

- GPT-2 paper: Done for Abstract, Sections 1, 2.1, 2.2, 2.3, 3, 7, and Table 2.
- OpenAI release-strategy report: Done for Introduction, Section 1, automated-detection discussion, Section 6 framing, and Appendix B timeline.
- GPT-3 paper: Done for Abstract, Sections 1, 2, 2.1, 2.2, 3.2, 3.9.4, 5, 6, Figures 1.1/2.1, and Tables 2.1/2.2/3.11.
- GitHub API: Done for `openai/gpt-2` creation date.
