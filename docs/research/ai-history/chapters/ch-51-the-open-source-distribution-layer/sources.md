# Sources: Chapter 51 - The Open Source Distribution Layer

## Verification Key

- Green: claim has primary evidence plus independent confirmation or internally consistent official data.
- Yellow: claim has one strong source, current/dynamic metadata, or a broad cultural inference.
- Red: claim should not be drafted except as blocked framing.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| arXiv, "About arXiv." URL: https://arxiv.org/about | Founding, scope, moderation boundary, and non-peer-review guardrail. | Green: page states arXiv is a curated research-sharing platform, hosts more than three million scholarly articles, serves fields including computer science and statistics, was founded by Paul Ginsparg in 1991, charges no submission fees, and is moderated but not peer-reviewed. |
| arXiv, "Category Taxonomy." URL: https://arxiv.org/category_taxonomy | Machine-learning category shelf. | Green: page defines cs.LG as Machine Learning and says it covers supervised, unsupervised, reinforcement learning, bandit problems, robustness, explanation, fairness, methodology, and applications; also lists stat.ML as Machine Learning. |
| arXiv, "Monthly Submissions" and CSV endpoint. URLs: https://arxiv.org/stats/monthly_submissions and https://arxiv.org/stats/get_monthly_submissions | Official submission-growth data. | Green for overall arXiv growth: local extraction on 2026-04-28 summed monthly CSV rows to 84,603 submissions in 2012, 123,523 in 2017, 178,329 in 2020, 185,692 in 2022, and 284,486 in 2025. Yellow for ML-specific growth unless a category-level source is added. |
| arXiv Annual Report 2021. URL: https://static.arxiv.org/static/arxiv.marxdown/0.1/about/reports/2021_arXiv_annual_report.pdf | Papers with Code integration and paper-to-code/dataset indexing. | Green: report states the Papers with Code integration was well received, expanded from AI and Machine Learning categories to all arXiv, added dataset links in May 2021, and had over 70,000 arXiv papers with at least one code link and over 60,000 with at least one dataset link. |
| Google, "TensorFlow: smarter machine learning, for everyone," 2015-11-09. URL: https://blog.google/technology/ai/tensorflow-smarter-machine-learning-for/ | TensorFlow open-source announcement and "working code rather than just research papers" framing. | Green: post announces TensorFlow, says Google is open-sourcing it, and explicitly hopes the ML community can exchange ideas more quickly through working code rather than just research papers. |
| Meta Engineering, "Announcing PyTorch 1.0 for both research and production," 2018-05-02. URL: https://engineering.fb.com/2018/05/02/ai-research/announcing-pytorch-1-0-for-both-research-and-production/ | PyTorch as open-source research-to-production framework. | Green: post presents PyTorch 1.0 as the next version of Facebook's open-source AI framework, describes rapid prototyping/research and production transition, and says opening papers, code, and models lets researchers and practitioners advance faster. |
| GitHub REST API repository records for `tensorflow/tensorflow`, `pytorch/pytorch`, and `huggingface/transformers`. URLs: https://api.github.com/repos/tensorflow/tensorflow, https://api.github.com/repos/pytorch/pytorch, https://api.github.com/repos/huggingface/transformers | Concrete repository metadata: creation date, current stars/forks, and repo existence. | Green for creation dates extracted on 2026-04-28: TensorFlow repo created 2015-11-07; PyTorch repo created 2016-08-13; Hugging Face Transformers repo created 2018-10-29. Yellow for stars/forks because they are dynamic current metrics, not historical adoption numbers. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Zhang et al., "An Explorative Study of GitHub Repositories of AI Papers," arXiv:1903.01555, 2019. URL: https://arxiv.org/pdf/1903.01555 | Empirical caveat: GitHub-hosted AI-paper code can be hard to reproduce, inactive, or poorly documented. | Green/Yellow: abstract and body state the study analyzed over 1,700 GitHub repositories of AI papers; it identifies abandoned/inactive repositories and reproducibility/documentation issues. Use as caveat, not as proof that all ML research code was open. |
| arXiv + Papers with Code public pages and blog posts. | Optional context for the code-tab integration. | Yellow unless the source is accessible without Cloudflare blocks; arXiv annual report is currently the stronger anchor. |
| Wikipedia pages on arXiv, GitHub, TensorFlow, PyTorch, and Papers with Code. | Discovery aid only. | Yellow/Red for citation: use only to find leads, never as a final prose anchor. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| arXiv is an open research-sharing platform founded by Paul Ginsparg in 1991, covering computer science and statistics among other fields. | Paper Server | arXiv About | arXiv monthly-submissions page | Green | Good opening infrastructure anchor. |
| arXiv is moderated but not peer-reviewed, so it accelerates circulation without replacing evaluation. | Paper Server | arXiv About | Later reproducibility caveat | Green | Blocks "arXiv replaced peer review" overclaim. |
| arXiv gives machine learning explicit category homes through cs.LG and stat.ML. | Machine Learning Gets Its Shelf | arXiv Category Taxonomy | arXiv About field list | Green | Do not claim ML-specific submission explosion unless another source is added. |
| Overall arXiv submissions grew substantially across the deep-learning era. | Machine Learning Gets Its Shelf | arXiv monthly-submissions CSV | arXiv About scale statement | Green | Use exact extracted totals with extraction date. |
| TensorFlow's open-source announcement explicitly framed working code as a faster medium for exchanging ML ideas than research papers alone. | Code Stops Being Optional Context | Google TensorFlow post | GitHub TensorFlow repo metadata | Green | Strongest "code as infrastructure" quote anchor. |
| PyTorch was framed by Meta/Facebook as an open-source AI framework bridging research prototyping and production deployment. | Frameworks Become Distribution Channels | Meta PyTorch 1.0 post | GitHub PyTorch repo metadata | Green | Keep as framework-distribution example, not full PyTorch history. |
| Major ML framework/model-library repositories were public GitHub projects created during 2015-2018. | Frameworks Become Distribution Channels | GitHub API repo records | Google/Meta posts | Green/Yellow | Green for creation dates; Yellow for current popularity metrics. |
| arXiv's Papers with Code integration linked papers to code and datasets at large scale by 2021. | Index Layer | arXiv Annual Report 2021 | Papers with Code public context optional | Green | Good bridge toward Chapter 54, but keep Hugging Face separate. |
| GitHub code availability did not guarantee reproducibility or maintenance. | Reproducibility Caveat | Zhang et al. 2019 | arXiv non-peer-review guardrail | Green/Yellow | Essential balance against open-source boosterism. |
| A 4,000-5,000 word chapter is feasible if it stays on infrastructure layers and avoids invented human scenes. | All | This source table and brief capacity plan | Ch24/Ch50 contract pattern | Green/Yellow | Larger draft needs more primary accounts or policy sources. |

## Conflict Notes

- Do not claim arXiv was peer review. It explicitly is not.
- Do not claim GitHub code release became universal or mandatory. The safe claim is "increasingly expected and infrastructural, but uneven."
- Do not claim open source broke corporate dominance. It lowered distribution friction while compute, data, and production still mattered.
- Do not use current GitHub stars/forks as historical evidence without date-stamping them.
- Do not turn Chapter 51 into Hugging Face. That belongs to Chapter 54.

## Page/Section Anchor Worklist

- arXiv About: Done for founding, scope, non-peer-review/moderation boundary, no-fee submission, and scale.
- arXiv Category Taxonomy: Done for cs.LG and stat.ML machine-learning category definitions.
- arXiv Monthly Submissions CSV: Done for overall annual totals; ML-specific category growth remains optional/Yellow.
- arXiv Annual Report 2021: Done for Papers with Code expansion and 70k/60k code/dataset link counts.
- Google TensorFlow post: Done for 2015 date and "working code rather than just research papers" framing.
- Meta PyTorch post: Done for open-source framework, research-to-production bridge, and papers/code/models framing.
- GitHub API: Done for repo creation dates and current metadata extraction date.
