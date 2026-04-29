# Sources: Chapter 43 - The ImageNet Smash

## Verification Key

- **Green**: claim has a verified page, section, line, DOI, or stable page anchor.
- **Yellow**: source exists, but the exact claim needs a stronger page/line anchor, is interpretive, or should be hedged.
- **Red**: no verifiable anchor yet; do not draft as fact.

Note: shell `curl` was attempted first for the AlexNet, ImageNet, and ILSVRC PDFs/pages, but DNS resolution failed in this sandbox. Browser extraction was used for public PDFs/pages. No legacy Gemini prose claim was promoted without an independent anchor.

## Primary and Near-Primary Sources

| Source | Use | Verification |
|---|---|---|
| Alex Krizhevsky, Ilya Sutskever, and Geoffrey E. Hinton, "ImageNet Classification with Deep Convolutional Neural Networks," NIPS 2012. NeurIPS page: https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks. PDF mirror used for extraction: https://www.nvidia.com/content/tesla/pdf/machine-learning/imagenet-classification-with-deep-convolutional-nn.pdf | Load-bearing primary technical source for AlexNet architecture, ImageNet/ILSVRC dataset details, GPU training, ReLU/dropout/augmentation, and 2012 result table. | **Green** for NeurIPS metadata lines 5-14; PDF p.0 lines 12-21; p.1 lines 41-66; p.2 lines 95-136; pp.3-6 architecture/training details; p.6 lines 342-356; p.7 lines 399-411. |
| Official ILSVRC2012 results page. URL: https://image-net.org/challenges/LSVRC/2012/results | Official scoreboard for task 1 classification, task 2 localization, team abstracts, and competitor descriptions. | **Green** for Task 1 table lines 14-21; team abstract lines 64-65; ISI/VGG descriptions lines 51-64; task 2 lines 32-41. |
| Official ILSVRC2012 main page. URL: https://image-net.org/challenges/LSVRC/2012/ | Challenge schedule, task description, validation/test/training-data description, top-5 error definition, and news dates. | **Green** for news lines 16-29; workshop schedule lines 30-36; introduction/data lines 37-47; Task 1 metric lines 50-53; timetable lines 61-66. |
| Official ILSVRC2012 analysis page. URL: https://www.image-net.org/challenges/LSVRC/2012/analysis/ | Official analysis of 2012 classification performance across categories and comparison of SuperVision to ISI. | **Green** for classification challenge method lines 661-665; overview line 13; categories section lines 673-723 if prose needs category examples. |
| Olga Russakovsky et al., "ImageNet Large Scale Visual Recognition Challenge," arXiv:1409.0575v3 / IJCV 2015. URL: https://arxiv.org/pdf/1409.0575. DOI: 10.1007/s11263-015-0816-y | Near-primary retrospective by ILSVRC organizers: benchmark structure, scale, pre-2012 methods, 2012 turning point, post-2012 adoption, statistical significance, and later error reductions. | **Green** for DOI via Princeton metadata; arXiv p.1 lines 43-55; p.2 lines 163-170; p.16-17 lines 1106-1158; p.17 lines 1171-1177; p.18-19 lines 1191-1193; p.21-23 lines 1267-1426; p.32 lines 1921-1930. |
| Jia Deng et al., "ImageNet: A Large-Scale Hierarchical Image Database," CVPR 2009, pp.248-255. DOI: 10.1109/CVPR.2009.5206848. URL: https://image-net.org/static_files/papers/imagenet_cvpr09.pdf | Background only: ImageNet construction and scale. Chapter 40 owns the full ImageNet construction story. | **Green via Ch40 contract** for p.248 lines 4-19; p.248 lines 33-47; p.251-252 lines 242-326. Use only for brief handoff, not a full scene. |
| ACM, "2018 ACM A.M. Turing Award." URL: https://awards.acm.org/about/2018-turing | Context source for Hinton/LeCun/Bengio persistence, early-2000s skepticism, and ACM's later statement that Hinton's 2012 work with Krizhevsky and Sutskever almost halved object-recognition error. | **Green** for lines 239-247, 256-259, and 263-269. Use as retrospective context and do not overload it as a 2012 participant account. |
| Fei-Fei Li, "ImageNet: Where Have We Gone? Where Are We Going?" ACM TechTalk slides, September 21, 2017. | Background on ImageNet/ILSVRC handoff and data-centered framing. Chapter 40 owns this source. | **Green via Ch40 contract** for slides pp.17-18, pp.31, pp.38-39. Use only as continuity if needed. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| CACM version of Krizhevsky, Sutskever, and Hinton, "ImageNet Classification with Deep Convolutional Neural Networks," June 2017. URL: https://cacm.acm.org/research/imagenet-classification-with-deep-convolutional-neural-networks/ | Useful because it reprints the AlexNet paper with prologue/epilogue and clean web sections. | Yellow. Browser search exposed the page body and table of contents, but direct open returned 403. Use the NIPS PDF mirror for Green anchors. |
| Dave Gershgorn, "The data that transformed AI research-and possibly the world," Quartz, July 26, 2017. URL: https://qz.com/1034972/the-data-that-changed-the-direction-of-ai-research-and-possibly-the-world | Public narrative for ImageNet's social reception and later significance. | Yellow. Ch40 found only search-snippet-level access. Do not use for quotes or Green claims without full article extraction. |
| Fei-Fei Li, *The Worlds I See* (Flatiron, 2023). | Possible source for richer ImageNet reception and project motivation. | Yellow. No edition-specific page anchors extracted in this worktree. |
| Ian Goodfellow, Yoshua Bengio, and Aaron Courville, *Deep Learning* (MIT Press, 2016). | Textbook context for CNN/deep learning history. | Yellow. Useful for technical background, but no page anchors extracted for this contract. |
| Later NVIDIA/Tom's Hardware/New Yorker reporting on AlexNet and NVIDIA's AI turn. | Potential context for corporate aftermath. | Yellow. Not needed for this chapter's Green core; avoid corporate pivot claims unless page anchors are added. |

## Green Claim Table

| ID | Claim | Scene | Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|---|
| G01 | ILSVRC had been running annually since 2010 and consisted of a public dataset plus annual competition/workshop. | 1 | Russakovsky et al. 2015 p.1 lines 43-55. | Ch40 sources G17. | **Green** | Establishes benchmark infrastructure. |
| G02 | ILSVRC2012 scaled standardized evaluation to 1,000 object classes and 1,431,167 annotated images, compared with PASCAL VOC 2012's 20 classes and 21,738 images. | 1 | Russakovsky et al. 2015 p.2 lines 163-170. | Ch40 sources G18 gives related 2010 scaling. | **Green** | Use "ILSVRC2012," not all ImageNet. |
| G03 | The AlexNet paper describes the ILSVRC subset as roughly 1.2M training images, 50K validation images, and 150K testing images across 1,000 categories. | 1 | AlexNet PDF p.1 lines 61-66. | Russakovsky et al. 2015 p.3-4 task description. | **Green** | Strong dataset-size anchor for Ch43. |
| G04 | Pre-2012 ILSVRC classification leaders used SIFT/LBP/Fisher-vector style feature pipelines with SVMs or linear classifiers. | 1 | Russakovsky et al. 2015 p.17 lines 1115-1133. | Official results page lines 51-63 for ISI/VGG descriptions. | **Green** | Avoid "all of vision"; say ILSVRC leaders. |
| G05 | The NeurIPS proceedings page identifies "ImageNet Classification with Deep Convolutional Neural Networks" as a NIPS 2012 paper by Krizhevsky, Sutskever, and Hinton. | 2 | NeurIPS page lines 5-14. | PDF title/authors p.0 lines 0-10. | **Green** | Bibliographic anchor. |
| G06 | The AlexNet paper says the authors trained one of the largest CNNs to date on ILSVRC-2010/2012 subsets and achieved the best results then reported on those datasets. | 2 | AlexNet PDF p.1 lines 44-55. | Russakovsky et al. 2015 p.17 lines 1134-1140. | **Green** | Use as authors' claim plus organizer confirmation. |
| G07 | The network had about 60 million parameters, 650,000 neurons, five convolutional layers, and three fully connected layers. | 2 | AlexNet PDF p.0 lines 12-21. | Official results team abstract lines 64-65. | **Green** | Do not mix with NeurIPS metadata's 500,000-neuron abstract discrepancy. |
| G08 | By the early 2000s, ACM describes LeCun, Hinton, and Bengio as among a small group committed to neural networks despite skepticism. | 2 | ACM Turing Award page lines 239-247. | ACM media release mirrors same wording. | **Green** | Retrospective award framing; do not overdramatize. |
| G09 | Russakovsky et al. call ILSVRC2012 a turning point when large-scale deep neural networks entered the scene, and identify SuperVision as the undisputed winner of classification and localization. | 2, 4 | Russakovsky et al. 2015 p.17 lines 1134-1140. | Official results lines 14-18 and 32-35. | **Green** | "Undisputed" is source wording; paraphrase if possible. |
| G10 | The AlexNet paper says the network size was limited mainly by GPU memory and tolerable training time, and that it trained five to six days on two GTX 580 3GB GPUs. | 3 | AlexNet PDF p.1 lines 56-59. | AlexNet PDF p.6 lines 321-325. | **Green** | Core infrastructure detail. |
| G11 | A single GTX 580 had 3GB memory; the authors spread the network across two GPUs and allowed communication only in certain layers. | 3 | AlexNet PDF p.2 lines 120-136. | Figure 2 caption p.4 lines 210-214. | **Green** | Hardware constraint, not bedroom anecdote. |
| G12 | AlexNet used data augmentation and dropout to reduce overfitting in a 60M-parameter network. | 3 | AlexNet PDF p.4 lines 223-241; p.5 lines 262-275. | Abstract p.0 lines 15-21. | **Green** | Keep at historical/technical level. |
| G13 | The model was trained for roughly 90 cycles through 1.2M images, taking five to six days on two NVIDIA GTX 580 3GB GPUs. | 3 | AlexNet PDF p.5-6 lines 321-325. | G10. | **Green** | Distinct from introductory summary. |
| G14 | ReLUs trained several times faster than saturating units; the paper says this enabled experiments with such large networks. | 3 | AlexNet PDF p.2 lines 95-112. | Abstract p.0 lines 17-18. | **Green** | Good for explaining not just "more layers." |
| G15 | Official ILSVRC2012 Task 1 results list SuperVision at 0.15315 top-5 error with extra ImageNet Fall 2011 data, and 0.16422 using only supplied training data. | 4 | Official ILSVRC results lines 14-18. | Russakovsky et al. 2015 p.18-19 lines 1191-1193. | **Green** | Use conditions carefully. |
| G16 | Official ILSVRC results identify SuperVision as Alex Krizhevsky, Ilya Sutskever, and Geoffrey Hinton from University of Toronto, with a large deep CNN trained on raw RGB pixels and two NVIDIA GPUs for about a week. | 2, 4 | Official ILSVRC results lines 64-65. | AlexNet PDF p.0 lines 0-21; p.1 lines 56-59. | **Green** | Good people/infrastructure anchor. |
| G17 | The AlexNet paper reports 15.3% top-5 test error for a seven-CNN averaged model pre-trained on ImageNet Fall 2011, compared with 26.2% for the second-best entry. | 4 | AlexNet PDF p.6 lines 342-356. | Official results lines 16-18. | **Green** | This is the canonical 10.9-point comparison; legacy "10.8%" is acceptable rounded from 26.2-15.3. |
| G18 | Russakovsky et al. Table 8 reports 2012 SuperVision at 15.32% top-5 error with external data, 16.42% without, and ISI at 26.17%, with 99.9% confidence intervals. | 4 | Russakovsky et al. 2015 p.23 lines 1363-1426. | Official results lines 16-18. | **Green** | Statistical significance anchor. |
| G19 | Following SuperVision's 2012 success, Russakovsky et al. say the vast majority of ILSVRC2013 entries used deep CNNs, and almost all ILSVRC2014 teams did. | 5 | Russakovsky et al. 2015 p.17 lines 1153-1177. | Table 6/7 entries p.19-21. | **Green** | This supports benchmark-field shift, not all computer vision. |
| G20 | From 2012 to 2014, with the dataset unchanged since 2012, image classification error fell from 16.4% to 6.7%. | 5 | Russakovsky et al. 2015 p.21-22 lines 1267-1302. | Table 8 p.23 lines 1363-1385. | **Green** | Use as ILSVRC progress, not solely AlexNet causation. |
| G21 | Russakovsky et al. conclude that major object-recognition breakthroughs would not have been possible on a smaller scale. | 5 | Russakovsky et al. 2015 p.32 lines 1921-1930. | AlexNet PDF p.1 lines 41-59. | **Green** | Good closing anchor for scale thesis. |
| G22 | ACM's Turing Award page says Hinton's 2012 work with Krizhevsky and Sutskever improved CNNs with ReLUs/dropout and almost halved object-recognition error in ImageNet. | 5 | ACM Turing Award page lines 263-269. | Russakovsky Table 8 and AlexNet result table. | **Green** | Use as retrospective confirmation. |
| G23 | The official ILSVRC2012 analysis says SuperVision consistently outperformed ISI in the classification challenge. | 4 | ILSVRC2012 analysis lines 661-665. | Official results lines 16-18. | **Green** | Supports "across categories" without overclaiming every category. |
| G24 | The official ILSVRC2012 results page describes ISI and VGG systems with SIFT/Fisher-vector/GIST/LBP/color-statistics feature pipelines and linear/SVM classifiers. | 1, 4 | Official ILSVRC results lines 51-63 and 77-79. | Russakovsky et al. 2015 p.17 lines 1140-1148. | **Green** | Concrete "feature engineering" comparison. |

## Yellow Claim Table

| ID | Claim | Scene | Source | Status | Needed Anchor |
|---|---|---|---|---|---|
| Y01 | Krizhevsky and Sutskever trained the model in an apartment or bedroom, with heat/noise from the GPUs. | 3 | Legacy prose; later popular retellings. | Yellow | First-person interview, memoir, photo caption, or contemporaneous account. Do not draft as fact. |
| Y02 | Reviewers or conference attendees initially thought the result was a mistake. | 4 | Common narrative; prior citation-seed audit marked this unsalvageable without source. | Yellow | Traceable interview or conference report. |
| Y03 | The ImageNet result directly triggered a specific Google acquisition price for Hinton's startup. | 5 | Popular accounts. | Yellow | Primary acquisition reporting or company/legal source with amount and causal framing. |
| Y04 | Fei-Fei Li's personal reaction to AlexNet in 2012 can be narrated in detail. | 5 | Possible memoir/interview source. | Yellow | *The Worlds I See* page anchors or transcript timestamps. |
| Y05 | AlexNet "ended feature engineering" across all computer vision. | 5 | Interpretive shorthand. | Yellow | Broader bibliometric evidence; current Green supports ILSVRC adoption only. |
| Y06 | NVIDIA internally pivoted toward AI immediately because of AlexNet. | 5 | Later NVIDIA-centered journalism. | Yellow | NVIDIA annual reports, executive interview transcript, or dated strategy source. |
| Y07 | The exact date/time/place when the final ILSVRC results reached the Toronto team. | 4 | Legacy-style anecdote. | Yellow | Email, blog, interview, or official announcement timestamp tied to the team. |

## Red Claim Table

| ID | Claim | Scene | Status | Reason |
|---|---|---|---|---|
| R01 | AlexNet invented convolutional neural networks. | 2 | Red | False; CNN history belongs to Ch27. |
| R02 | AlexNet proved that GPUs alone caused the deep-learning revolution. | 3, 5 | Red | Sources show data, architecture, regularization, training method, and benchmark infrastructure all mattered. |
| R03 | The 2012 result made all hand-engineered vision systems obsolete immediately. | 4, 5 | Red | ILSVRC 2013/2014 adoption shifted quickly, but broader immediate obsolescence is unsupported. |
| R04 | The Toronto system was trained on a datacenter GPU cluster. | 3 | Red | The paper anchors two GTX 580 3GB GPUs. |
| R05 | AlexNet directly caused modern foundation models or ChatGPT. | 5 | Red | Later scale/deep-learning continuity belongs to later chapters and needs separate causal evidence. |

## Page Anchor Worklist

### Done

- AlexNet PDF: dataset, architecture, ReLU, multi-GPU split, dropout/data augmentation, training time, and ILSVRC2012 result table anchors extracted via browser PDF text.
- Official ILSVRC2012 results page: Task 1 score table, Task 2 score table, team abstracts, and feature-engineering competitor descriptions anchored.
- Official ILSVRC2012 analysis page: classification metric and SuperVision-vs-ISI category-level comparison anchored.
- Russakovsky et al. 2015 ILSVRC paper: benchmark structure, PASCAL comparison, pre-2012 methods, 2012 turning point, 2013/2014 adoption, Table 8 significance, and conclusion anchors extracted.
- Ch40 imported ImageNet construction anchors remain available but should be used only as handoff background.

### Still Needed

- First-person or archival anchor for physical training environment, if the prose wants a domestic hardware scene.
- Fei-Fei Li memoir/interview page anchors for human reaction and ImageNet reception.
- Company/press anchors for the Hinton startup acquisition and post-2012 corporate acceleration, if later prose wants a business aftermath.
- Better line-located open access for the CACM 2017 reprint/prologue; direct open returned 403 here.

## Verification Notes

- Direct shell network extraction failed with DNS errors for `papers.nips.cc`, `image-net.org`, and `arxiv.org`; browser extraction supplied stable line/page anchors.
- The source table deliberately keeps the dramatic "GPU bedroom" and "reviewers thought it was a mistake" claims Yellow. They are usable only as open questions, not prose facts.
