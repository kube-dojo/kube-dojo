# Sources: Chapter 40 - Data Becomes Infrastructure

## Verification Key

- **Green**: claim has a verified page, section, line, DOI, or stable document anchor.
- **Yellow**: source is credible, but the specific claim lacks a page/slide anchor, needs edition-specific verification, or should be hedged.
- **Red**: no verifiable anchor yet; do not draft as fact.

## Primary and Near-Primary Sources

| Source | Use | Verification |
|---|---|---|
| George A. Miller, Richard Beckwith, Christiane Fellbaum, Derek Gross, and Katherine Miller, "Introduction to WordNet: An On-line Lexical Database," revised August 1993, in the Princeton WordNet five-paper PDF. URL: https://wordnetcode.princeton.edu/5papers.pdf | WordNet origin, synsets, semantic relations, and noun hierarchy background for ImageNet's ontology. | **Green** for PDF pp.1-6 and p.66 via browser extraction: online lexical reference/system design lines 0-7; 1985 Princeton group and "WordNet is the result" lines 53-58; 1990 report line 29; synset representation lines 229-232; semantic relations and pointers lines 250-262; hypernym/hyponym table p.66 lines 2629-2684. |
| Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li, and Li Fei-Fei, "ImageNet: A Large-Scale Hierarchical Image Database," CVPR 2009, pp.248-255. DOI: 10.1109/CVPR.2009.5206848. URL: https://image-net.org/static_files/papers/imagenet_cvpr09.pdf | Load-bearing primary source for ImageNet's design, scale, WordNet backbone, web candidate collection, AMT cleaning, and quality control. | **Green** for DOI/pages via Princeton/CoLab metadata; PDF verified via browser extraction: abstract CVPR p.248 lines 4-19; WordNet and 80,000 noun-synset ambition p.248 lines 33-40; 12 subtrees/5,247 synsets/3.2M images p.248 lines 41-47; Section 3 construction pp.251-252 lines 242-326; precision pp.249-250 lines 127-143. Direct shell `curl` failed with DNS resolution errors in this sandbox. |
| Fei-Fei Li, "ImageNet: Where Have We Gone? Where Are We Going?" ACM TechTalk, September 21, 2017, with slides. Page: https://learning.acm.org/techtalks/ImageNet. Slides: https://learning.acm.org/binaries/content/assets/leaning-center/webinar-slides/2017/imagenet_2017_acm_webinar_compressed.pdf | Retrospective primary/near-primary source for Li's data-centered framing, construction attempts, WordNet explanation, team acknowledgments, 49k AMT workers/167 countries, and the ILSVRC handoff. | **Green** for ACM page lines 145-155 and slide PDF pp.17-38: shift from modeling to data pp.17-18; WordNet/synset slides pp.19-23; launch attempts pp.27-31; 49k workers/167 countries and 2007-2010 p.31; 15M later scale p.36; ILSVRC 2010-2017 pp.38-39. |
| Olga Russakovsky et al., "ImageNet Large Scale Visual Recognition Challenge," arXiv:1409.0575v3 / IJCV 2015. URL: https://arxiv.org/pdf/1409.0575 | Anchor for the benchmark handoff, ILSVRC annual structure, ImageNet 2014 scale, and PASCAL comparison. | **Green** for arXiv PDF pp.1-3: annual challenge since 2010 and benchmark structure lines 43-55; PASCAL-to-ILSVRC scaling p.2 lines 75-83; ImageNet as ILSVRC backbone and 14,197,122 images/21,841 synsets as of Aug. 2014 p.3 lines 136-147; PASCAL VOC 2012 vs ILSVRC2012 scale p.3 lines 163-170. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Dave Gershgorn, "The data that transformed AI research-and possibly the world," *Quartz*, July 26, 2017. URL: https://qz.com/1034972/the-data-that-changed-the-direction-of-ai-research-and-possibly-the-world | Public narrative for 2006 origin and Li's belief that data, not only algorithms, was the bottleneck. | Yellow. Search snippet exposes the headline/date and 2006/motivation framing, but the page body was not extractable here beyond title. Do not use for exact quotes or detailed claims. |
| Denton et al., "On the genealogy of machine learning datasets: A critical history of ImageNet," 2021/2022. | Later critical history of ImageNet construction and dataset politics. | Yellow. Search result shows relevant discussion of failed labeling attempts and cites Li 2017, but exact open PDF/page anchors were not extracted. |
| Fei-Fei Li, *The Worlds I See* (Flatiron, 2023). | Memoir context for personal origin, reception, and stakes. | Yellow. No edition-specific page anchors extracted; do not use for Green claims yet. |

## Green Claim Table

| ID | Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|---|
| G01 | WordNet was developed by a Princeton group beginning in 1985 and was reported in the five-paper WordNet collection as of 1990. | 2 | Miller et al. WordNet PDF p.1 lines 53-58; p.1 line 29. | **Green** | Good people/timeline anchor. |
| G02 | WordNet is an online lexical reference system inspired by psycholinguistic theories, with nouns, verbs, and adjectives organized into synonym sets linked by relations. | 2 | Miller et al. WordNet PDF p.1 lines 0-7. | **Green** | Use concise paraphrase. |
| G03 | WordNet represents meanings through synonym sets or "synsets"; the paper gives examples where synsets disambiguate meanings. | 2 | Miller et al. WordNet PDF pp.5-6 lines 229-232. | **Green** | Explains why ImageNet can attach images to concepts, not spellings. |
| G04 | WordNet's semantic relations are pointers between synsets; its relation table includes noun hyponym and hypernym relations. | 2 | Miller et al. WordNet PDF p.6 lines 250-262; p.66 lines 2629-2684. | **Green** | Supports the hierarchy/skeleton scene. |
| G05 | The ImageNet paper introduces ImageNet as a large-scale ontology of images built on the WordNet structure. | 2 | Deng et al. 2009 p.248 lines 4-12; p.248 lines 29-33. | **Green** | Load-bearing thesis anchor. |
| G06 | ImageNet aimed to populate most of WordNet's roughly 80,000 noun synsets with 500-1,000 clean full-resolution images each. | 2, 5 | Deng et al. 2009 p.248 lines 33-40. | **Green** | Ambition, not 2009 completion. |
| G07 | The 2009 paper reports 12 subtrees, 5,247 synsets, and 3.2 million images in the current ImageNet version. | 5 | Deng et al. 2009 p.248 lines 13-18; p.248 lines 41-47. | **Green** | Use 2009-specific wording. |
| G08 | ImageNet's construction section says its goal was around 50 million images and describes the method for ensuring scale/accuracy/diversity. | 3 | Deng et al. 2009 Section 3, CVPR p.251 lines 242-247. | **Green** | Goal claim; avoid implying achieved by 2009. |
| G09 | Candidate-image collection queried several image search engines using WordNet synonyms, then expanded queries with parent-synset words when useful. | 3 | Deng et al. 2009 Section 3.1, CVPR p.251 lines 249-263. | **Green** | Specific pipeline detail. |
| G10 | The candidate pool was enlarged and diversified by translating queries into Chinese, Spanish, Dutch, and Italian using WordNets in those languages. | 3 | Deng et al. 2009 Section 3.1, CVPR p.251 lines 264-267. | **Green** | Good infrastructure detail. |
| G11 | ImageNet relied on humans using AMT to verify each candidate image for a given synset, presenting image sets and target-synset definitions. | 4 | Deng et al. 2009 Section 3.2, CVPR p.251 lines 268-282. | **Green** | Use "verify," not "label from scratch." |
| G12 | ImageNet quality control used multiple independent users, initial subsets with at least 10 votes per image, confidence score tables, and thresholds for remaining candidate images. | 4 | Deng et al. 2009 p.251-252 lines 303-326. | **Green** | Prevents "raw clicks" overclaim. |
| G13 | Li's 2017 ACM slide deck frames ImageNet as a shift in visual recognition from modeling to data and "lots of data." | 1 | Li 2017 ACM slides pp.17-18 lines 118-124. | **Green** | Retrospective framing; do not quote beyond short phrase. |
| G14 | Li's 2017 slides describe three launch attempts: a psychophysics/undergraduate approach, a human-in-the-loop idea, and crowdsourced labor via AMT. | 1, 4 | Li 2017 ACM slides pp.27-31 lines 185-216. | **Green** | Supports scene shape; slide-deck shorthand needs prose care. |
| G15 | Li's 2017 slides show the psychophysics attempt calculation reaching about 19 years for 40,000 synsets, 10,000 candidate images per synset, and 2-5 verifiers. | 1, 4 | Li 2017 ACM slides p.28 lines 192-198. | **Green** | Use as retrospective slide calculation, not a formal project estimate. |
| G16 | Li's 2017 slides state ImageNet used 49k workers from 167 countries during 2007-2010. | 4 | Li 2017 ACM slides p.31 lines 210-216. | **Green** | Stronger than legacy "nearly 50,000" but still slide-deck source. |
| G17 | ILSVRC has run annually since 2010 and consists of a public dataset plus annual competition/workshop. | 5 | Russakovsky et al. 2015 p.1 lines 43-55. | **Green** | Handoff only; stop before AlexNet. |
| G18 | Scaling from PASCAL VOC 2010 to ILSVRC 2010 meant moving from 19,737 images/20 classes to 1,461,406 images/1,000 classes, making small-group annotation infeasible and motivating crowdsourcing. | 5 | Russakovsky et al. 2015 p.2 lines 75-83. | **Green** | Good Ch39-to-Ch40 bridge if needed. |
| G19 | As of August 2014, ImageNet contained 14,197,122 annotated images organized by WordNet hierarchy across 21,841 synsets. | 5 | Russakovsky et al. 2015 p.3 lines 136-147. | **Green** | Later-scale claim; keep distinct from G07. |
| G20 | AMT mechanics in the period used requesters, workers/Turkers, HITs, rewards, qualifications, approvals, bonuses, and Amazon-mediated transactions. | 4 | Ch38 sources.md Green G15: Snow et al. 2008 p.255 lines 113-142. | **Green** | Imported bridge anchor from Ch38; cite Ch38 if used. |
| G21 | Amazon publicly announced MTurk on November 2, 2005 as a web-services API for "Artificial Artificial Intelligence." | 4 | Ch38 sources.md Green G6-G9: AWS announcement title/date/body lines 27-32. | **Green** | Short bridge only; Ch38 owns full MTurk origin. |
| G22 | ACM's TechTalk page describes Li as the inventor of ImageNet and the ImageNet Challenge, and as an associate professor at Stanford/director of SAIL at the time. | 1, 5 | ACM TechTalk page lines 145-155. | **Green** | Good people-file anchor. |
| G23 | The 2009 paper reports ImageNet achieved about 99.7% precision on sampled synsets. | 4, 5 | Deng et al. 2009 pp.249-250 lines 127-143. | **Green** | "Reported" precision; do not universalize. |

## Yellow Claim Table

| ID | Claim | Scene | Source | Status | Needed Anchor |
|---|---|---|---|---|---|
| Y01 | In 2006, Fei-Fei Li began formulating the idea that a much larger visual dataset was the field's bottleneck. | 1 | Gershgorn 2017 search snippet; Li 2017 slides imply the arc but do not date the first idea precisely. | Yellow | Exact article lines, memoir pages, or talk transcript. |
| Y02 | CVPR 2009 reception was muted, with many researchers treating ImageNet as "just data" rather than science. | 5 | Legacy prose; common journalistic retelling. | Yellow | Need page/quote from Li memoir, interview, conference report, or reviewer account. |
| Y03 | Jia Deng personally engineered the main scraping/MTurk pipeline. | 3, 4 | Legacy prose and common accounts; 2009 paper author list includes Deng first. | Yellow | Need Li memoir/interview or project-history page assigning individual engineering role. |
| Y04 | Undergraduates were miserable or the early psychophysics labeling attempt failed due to worker burden. | 1, 4 | Li 2017 slides p.27 says "Miserable Undergrads" but slide shorthand is not enough for detailed prose. | Yellow | Transcript or memoir page for exact context. |
| Y05 | ImageNet's creators explicitly designed it as a direct answer to PASCAL VOC's scale limit. | 1, 5 | Russakovsky et al. supports PASCAL-to-ILSVRC scaling; Li slides call PASCAL an inspiration. | Yellow | Direct interview/talk transcript or paper statement tying ImageNet's original design to VOC. |
| Y06 | ImageNet's ontology was underused by later deep-learning practitioners. | 5 | Li 2017 slides pp.58-64 say "Ontological Structure Not Used as Much" and "Most works still use 1M images." | Yellow | Could be Green if this later reflection is needed, but it is mostly Ch43/later and not central here. |
| Y07 | The project had about 15 million images by 2010. | 5 | Li 2017 slides p.36 says 15M; Russakovsky 2015 gives 14,197,122 as of Aug. 2014. | Yellow | Need version/date reconciliation before using as a precise dated claim. |

## Red Claim Table

| ID | Claim | Scene | Why Red |
|---|---|---|---|
| R01 | ImageNet proved deep-learning algorithms were fundamentally sound. | 5 | That is a Ch43/AlexNet interpretation, not supported by the 2009 construction sources alone. |
| R02 | Researchers at CVPR 2009 literally ignored Li's poster or walked past it. | 5 | No conference-floor source or memoir page anchor. |
| R03 | ImageNet was the first dataset large enough to train deep neural networks without overfitting. | 5 | Needs technical and historical comparison; false or at least overbroad without Ch43 anchors. |
| R04 | MTurk workers in ImageNet were paid a specific wage or completed a specific number of labels per hour. | 4 | No ImageNet-period wage/task-rate anchor extracted. Ch38 has later wage studies only. |
| R05 | WordNet was created specifically for AI vision or for ImageNet. | 2 | WordNet predates ImageNet and was a lexical/psycholinguistic database. |

## Page Anchor Worklist

### Done

- WordNet five-paper PDF: origin, synsets, semantic relations, and hypernym/hyponym table anchors extracted.
- Deng et al. 2009 ImageNet PDF: ontology, scale, web-image collection, AMT verification, quality control, and precision anchors extracted.
- Fei-Fei Li 2017 ACM TechTalk page/slides: data-shift framing, construction attempts, 49k/167 worker slide, WordNet slides, and ILSVRC slide anchors extracted.
- Russakovsky et al. 2015 ILSVRC PDF: annual benchmark structure, PASCAL scaling comparison, and 2014 ImageNet scale anchors extracted.

### Still Needed

- Edition-specific anchors from Fei-Fei Li, *The Worlds I See* (2023), for personal motivation, reception, and individual project roles.
- Extractable Quartz article body or another accessible interview for the 2006 origin story.
- A transcript/video timestamp for Li's 2017 ACM or 2019 talk if the prose needs richer scene texture than slide text supports.
- A primary source assigning specific engineering ownership to Jia Deng beyond first authorship.
- Historical reception evidence from CVPR 2009, reviewer comments, or interviews before drafting the "muted reception" scene.

## Verification Notes

- Per workflow, shell `curl` was attempted first for the ImageNet and WordNet PDFs, but DNS resolution failed in this sandbox. Browser verification was used for public PDFs/pages, and the Ch38 contract's prior `pdftotext` anchors were cross-checked where relevant.
- No legacy Gemini source or prose claim was promoted without independent anchoring.
