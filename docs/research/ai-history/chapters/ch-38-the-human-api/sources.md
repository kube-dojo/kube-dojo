# Sources: Chapter 38 - The Human API

## Verification Key

- **Green**: claim has a verified page, section, line, DOI, or stable document anchor.
- **Yellow**: source exists, but the exact claim needs a better page/section anchor, stronger attribution, or conflict resolution.
- **Red**: no verifiable anchor yet; do not draft as fact.

## Primary and Near-Primary Sources

| Source | Use | Verification |
|---|---|---|
| Harinarayan, Venky, Anand Rajaraman, and Anand Ranganathan. US7197459B1, "Hybrid machine/human computing arrangement." Google Patents mirror: https://patents.google.com/patent/US7197459B1/en | Engineering abstraction behind a human/computer task API: subtasks, central server, human-operated nodes, accuracy/time/cost parameters. | **Green** for Info section and Summary/Description anchors listed below: prior art date 2001-03-19; filing 2001-10-12; inventors; original assignee Amazon Technologies; Summary lines 258-262; API description lines 317-325; claims lines 403-408. |
| Amazon Web Services, "Announcing Amazon Mechanical Turk," November 2, 2005. https://aws.amazon.com/about-aws/whats-new/2005/11/02/announcing-amazon-mechanical-turk/ (live page is now JS-rendered with empty static body — use Wayback mirror https://web.archive.org/web/2007/https://aws.amazon.com/about-aws/whats-new/2005/11/02/announcing-amazon-mechanical-turk/ for the announcement prose) | Public launch, "Artificial Artificial Intelligence," and web-services API framing. | **Green** for title/date and body, lines 27-32 (verified against Wayback capture during anchor pass; live URL kept as canonical, Wayback as parallel anchor). |
| Martens, China. "Bezos offers a look at 'hidden Amazon'." *Computerworld*, September 27, 2006. https://www.computerworld.com/article/1651038/bezos-offers-a-look-at-hidden-amazon.html | Contemporary report of Bezos's MIT Emerging Technologies keynote; MTurk grouped with S3 and EC2 as AWS developer services. | **Green** for lines 228-242. |
| Snow, Rion, Brendan O'Connor, Daniel Jurafsky, and Andrew Y. Ng. "Cheap and Fast - But is it Good? Evaluating Non-Expert Annotations for Natural Language Tasks." EMNLP 2008, pp. 254-263. https://aclanthology.org/D08-1027.pdf | Early academic validation of MTurk for NLP annotation, task mechanics, cost, redundancy, and quality. | **Green** for ACL metadata and PDF pages 254-263, especially p.254 lines 18-36, p.255 lines 113-142, p.256-257 lines 242-249, p.262 lines 607-613. DOI metadata via Crossref/CiNii: 10.3115/1613715.1613751. |
| Deng, Jia, Wei Dong, Richard Socher, Li-Jia Li, Kai Li, and Li Fei-Fei. "ImageNet: A Large-Scale Hierarchical Image Database." CVPR 2009, pp. 248-255. https://www.image-net.org/static_files/papers/imagenet_cvpr09.pdf | ImageNet scale, WordNet structure, AMT cleaning pipeline, multiple-user quality control. | **Green** for DOI 10.1109/CVPR.2009.5206848 and PDF pp.248-252: abstract p.248 lines 4-19; construction p.250 lines 242-276; cleaning/quality p.251-252 lines 303-326; future-work p.254 lines 555-566. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Schwartz, Oscar. "Untold History of AI: How Amazon's Mechanical Turkers Got Squeezed Inside the Machine." *IEEE Spectrum*, April 22, 2019. https://spectrum.ieee.org/untold-history-of-ai-mechanical-turk-revisited-tktkt | Secondary account of duplicate-catalog origin, Harinarayan patent, and invisibility of worker labor. | **Green** for lines 97-109. Use as secondary, not primary. |
| Pew Research Center, "What is Mechanical Turk?" July 11, 2016. https://www.pewresearch.org/internet/2016/07/11/what-is-mechanical-turk/ | Explainer for name origin, Bezos/NYT quotation trail, HIT mechanics, and requesters/workers. | **Green** for lines 145-148 and surrounding "How the marketplace works" section if needed. |
| Hara, Kotaro, Abigail Adams, Kristy Milland, Saiph Savage, Chris Callison-Burch, and Jeffrey P. Bigham. "A Data-Driven Analysis of Workers' Earnings on Amazon Mechanical Turk." CHI 2018. arXiv preprint: https://arxiv.org/pdf/1712.05796 (canonical `callison-burch.github.io` URL flagged ANCHOR_BROKEN by Claude verifier — returns 404; ACM DOI 10.1145/3173574.3174023 is paywalled to anonymous fetch, arXiv preprint is open and content-equivalent) | Later empirical boundary source on worker earnings and unpaid work. | **Green** verified against arXiv preprint during anchor pass: 2,676 workers / 3.8M HITs, median ~$2/h, 4% earned >$7.25/h, three sources of unpaid time (search, rejected work, unsubmitted work). |
| von Ahn, Luis, and Laura Dabbish. "Labeling Images with a Computer Game." CHI 2004, pp. 319-326. DOI 10.1145/985692.985733. Open PDF mirror: https://www.lri.fr/~mbl/ENS/CSCW/2017/papers/vonAhn-CHI04.pdf | Boundary source: MTurk did not invent human computation or image labeling; ESP Game predates MTurk. | Yellow for prose until local page extraction is done; search result and DOI verified, but exact PDF page anchors not extracted into this contract. |
| ILO, Berg et al., *Digital labour platforms and the future of work*, 2018. https://www.ilo.org/publications/digital-labour-platforms-and-future-work-towards-decent-work-online-world | Broader labor context if later prose needs one sentence beyond Hara et al. | Yellow for this chapter; report metadata and abstract verified, but page-level wage/work-condition anchors not extracted. |
| Pontin, Jason. "Artificial Intelligence, With Help From the Humans." *The New York Times*, March 25, 2007. URL known via citations: https://www.nytimes.com/2007/03/25/business/yourmoney/25Stream.html | Bezos quotation and public framing of artificial artificial intelligence. | Yellow. Article text blocked by robots/paywall in this environment; do not quote directly from it. Pew and later papers cite it, but exact NYT page text is not verified here. |

## Green/Yellow/Red Claim Table

| ID | Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|---|
| G1 | US7197459B1 is titled "Hybrid machine/human computing arrangement"; it lists Venky Harinarayan, Anand Rajaraman, and Anand Ranganathan as inventors and Amazon Technologies Inc. as original assignee. | 1 | US7197459B1 Info, lines 0-34; inventors/original assignee lines 21-28. | **Green** | Use for engineering lineage, not as sole proof of MTurk product launch. |
| G2 | The patent has prior art date 2001-03-19, filing date 2001-10-12, and publication/grant date 2007-03-27. | 1 | US7197459B1 Info, lines 15-39. | **Green** | Helps separate invention timeline from 2005 launch. |
| G3 | The patent describes a hybrid arrangement with a central coordinating server and human-operated nodes to help a computer solve tasks. | 1 | US7197459B1 Summary, lines 258-262. | **Green** | Core "human API" infrastructure anchor. |
| G4 | The patent says a computer can decompose tasks such as image or speech comparison into human-performed subtasks and request those performances using an API. | 1 | US7197459B1 definitions/summary, lines 91-97 and 260-262. | **Green** | Load-bearing technical claim. |
| G5 | The patent's API can describe task nature, input data, expected accuracy, security level, time limit, and cost. | 1 | US7197459B1 API description, lines 317-325. | **Green** | Supports "callable, meterable" prose. |
| G6 | Amazon publicly announced Amazon Mechanical Turk on November 2, 2005. | 2 | AWS announcement, title/date lines 27-29. | **Green** | Public launch anchor. |
| G7 | AWS framed MTurk around tasks humans still did better than powerful computers, including identifying objects in photographs. | 2 | AWS announcement body, lines 30-31. | **Green** | Do not overclaim all vision tasks; use the example. |
| G8 | AWS described MTurk as reversing the normal request flow: a computer program could ask a human to perform a task and return results. | 2 | AWS announcement body, lines 30-32. | **Green** | Core scene language. |
| G9 | AWS said MTurk provided a web-services API for computers to integrate "Artificial Artificial Intelligence" into their processing. | 2 | AWS announcement body, line 32. | **Green** | Use exact phrase sparingly. |
| G10 | Bezos presented MTurk, S3, and EC2 together at MIT on September 27, 2006 as part of Amazon's developer web-services push. | 3 | Computerworld lines 228-232. | **Green** | Contemporary report, not transcript. |
| G11 | Computerworld reported about 200,000 developers had registered for Amazon's 10 web services by the time of Bezos's 2006 keynote. | 3 | Computerworld lines 231-232. | **Green** | Keep as reported figure, not audited total. |
| G12 | Bezos framed the web services as internal work Amazon already had to do and was exposing to others. | 3 | Computerworld lines 239-240. | **Green** | Supports infrastructure thesis. |
| G13 | Snow et al. state that human linguistic annotation is crucial for many NLP tasks but expensive and time-consuming. | 4 | Snow et al. 2008 p.254, lines 18-24 and 37-48. | **Green** | Annotation bottleneck anchor. |
| G14 | Snow et al. used MTurk on five NLP tasks: affect recognition, word similarity, textual entailment, temporal event ordering, and word sense disambiguation. | 4 | Snow et al. 2008 p.254, lines 25-36 and 50-59. | **Green** | Exact task list. |
| G15 | Snow et al. describe AMT as an online labor market using HITs, requesters, workers/Turkers, rewards, qualifications, approval, bonuses, and Amazon-mediated transactions. | 4 | Snow et al. 2008 p.255, lines 113-142. | **Green** | Good mechanics paragraph. |
| G16 | In the affect experiment, Snow et al. collected ten independent annotations per item and used redundancy to study quality improvement. | 4 | Snow et al. 2008 p.256, lines 143-153. | **Green** | Supports aggregation, not single-worker magic. |
| G17 | Snow et al. report $2 for 7,000 affect labels, interpreting the rate as 3,500 non-expert labels per USD and at least 875 expert-equivalent labels per USD. | 4 | Snow et al. 2008 p.257, lines 242-249. | **Green** | Cost claim. |
| G18 | Snow et al. conclude that, for many tasks, only a small number of non-expert annotations per item are needed to equal expert annotator performance, and bias control improves quality. | 4 | Snow et al. 2008 p.262, lines 607-613. | **Green** | Use "many tasks," not all annotation. |
| G19 | ImageNet's 2009 paper reports 12 subtrees, 5,247 synsets, and 3.2 million images, and says it describes a data-collection scheme with AMT. | 5 | Deng et al. 2009 p.248, lines 13-18; p.248 lines 41-57. | **Green** | Core scale anchor. |
| G20 | ImageNet aimed to populate most of WordNet's roughly 80,000 noun synsets with 500-1,000 clean full-resolution images each. | 5 | Deng et al. 2009 p.248, lines 33-40. | **Green** | Ambition, not completed state. |
| G21 | Deng et al. say ImageNet could no longer rely on traditional data-collection methods and describe using AMT to construct it. | 5 | Deng et al. 2009 p.248, lines 55-57; p.250 lines 242-247. | **Green** | Transition to infrastructure. |
| G22 | Deng et al. relied on humans using AMT to verify candidate images, presenting image sets and synset definitions to users. | 5 | Deng et al. 2009 p.250-251, lines 268-282. | **Green** | Specific workflow. |
| G23 | ImageNet quality control used multiple independent users, initial subsets with at least 10 votes per image, and confidence thresholds for remaining candidate images. | 5 | Deng et al. 2009 p.251-252, lines 303-326. | **Green** | Avoid implying raw votes were blindly trusted. |
| G24 | ImageNet reported about 99.7% average precision on sampled synsets in the 2009 paper. | 5 | Deng et al. 2009 p.249, lines 127-143. | **Green** | Use as reported result. |
| G25 | Hara et al. recorded 2,676 workers performing 3.8 million tasks on AMT and found median hourly wages around $2/h with only 4% above $7.25/h. | 5 | Hara et al. 2018 p.1, lines 7-18; p.4 lines 402-421. | **Green** | Later boundary source, not 2005-2009 condition. |
| G26 | Hara et al. identify unpaid work components including searching for tasks, rejected work, and work not submitted. | 5 | Hara et al. 2018 p.1-2, lines 103-112; p.3 lines 310-317. | **Green** | Use to qualify "cheap." |
| G27 | IEEE Spectrum reports that Amazon's duplicate-product catalog problem motivated the internal system and that software attempts were described as "insurmountable." | 1 | IEEE Spectrum lines 97-100. | **Green** | Secondary anchor. Use "reports," not archival certainty. |
| G28 | IEEE Spectrum reports Harinarayan's solution as subtasks distributed to networked human workers and later turned into a marketplace. | 1, 2 | IEEE Spectrum lines 101-107. | **Green** | Secondary, corroborated by patent architecture. |
| G29 | Pew explains the Mechanical Turk name by reference to the 18th-century chess-playing automaton that appeared mechanical but hid a person. | 2 | Pew lines 145-148. | **Green** | Short name-origin paragraph only. |
| Y1 | Jeff Bezos personally originated MTurk as a website/product concept. | 1, 2 | Pew lines 147-148; conflicts/tension with IEEE and patent inventor list. | Yellow | Attribute carefully; do not make a sole-inventor claim. |
| Y2 | Bezos used the exact phrase "human-as-a-service" in the 2006 MIT talk. | 3 | Fair Crowd Work cites a 2006 MIT lecture, but no primary transcript located. | Yellow | Can be mentioned only as reported by secondary source; better to avoid. |
| Y3 | The internal Amazon version first used Amazon employees before public workers. | 1 | Fair Crowd Work platform history reports this, but its cited sources were not fully extracted. | Yellow | Needs original source or stronger page anchor. |
| Y4 | Pontin's 2007 New York Times article contains the canonical Bezos quote about a computer calling a human instead of a computer service. | 2 | Pew quotes/cites NYT, but NYT text blocked here. | Yellow | Do not quote NYT directly; quote Pew only if necessary. |
| Y5 | Academic AI labs broadly and quickly adopted MTurk after Snow et al. | 4 | Snow and ImageNet show two strong cases; broad adoption needs bibliometric or survey anchor. | Yellow | Phrase as "early examples," not "floodgates." |
| Y6 | MTurk requesters in 2005-2009 could routinely complete 10,000 labels in hours. | 4, 5 | Plausible and later common, but no exact period anchor extracted. | Yellow | Avoid numeric timing unless sourced per case. |
| R1 | MTurk was designed specifically to train AI systems that would replace MTurk workers. | 5 | No period anchor. | Red | This is retrospective overclaim; do not draft. |
| R2 | The exact number of active MTurk workers during 2005-2009. | 2, 3 | No verified source in this contract. | Red | Do not invent. |
| R3 | A direct causal chain from MTurk to AlexNet's 2012 win. | 5 | Ch39/ImageNet later history needed. | Red | Only forward-reference ImageNet. |

## Page Anchor Worklist

### Done

- AWS launch page: title/date and full announcement body anchored.
- US7197459B1 patent: metadata, summary, API description, and relevant claims anchored.
- Computerworld 2006 MIT report: developer-services framing anchored.
- Snow et al. 2008 ACL PDF: abstract, AMT mechanics, cost, redundancy, and conclusion anchored.
- Deng et al. 2009 ImageNet PDF: scale, WordNet goals, AMT verification, quality control, and precision anchored.
- Hara et al. 2018 CHI PDF: wage distribution and unpaid work anchors extracted.
- IEEE Spectrum 2019 and Pew 2016: secondary origin/name anchors extracted.

### Still Needed

- Legitimate access to Pontin 2007 New York Times article text.
- Bezos MIT Emerging Technologies 2006 transcript/video.
- Amazon internal MTurk design or launch materials connecting duplicate catalog cleanup to the public product.
- Exact page anchors from von Ahn and Dabbish 2004 if the prose needs a stronger pre-MTurk human-computation boundary paragraph.
- Broader bibliometric or survey evidence for MTurk adoption across AI/ML beyond Snow and ImageNet.

## Conflict Notes

- The patent proves a general hybrid human/computer API design; IEEE Spectrum/Pew provide the catalog origin story. Keep those evidentiary levels separate.
- Hara et al. 2018 contains one likely erroneous line saying "AMT was launched in 2008"; do not use that line. AWS directly anchors the 2005 public launch.
- The phrase "Artificial Artificial Intelligence" is primary-anchored by AWS; the fuller Bezos quote is not primary-anchored here.
