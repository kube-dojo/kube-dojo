# Sources: Chapter 39 - The Vision Wall

## Verification Key

- **Green**: claim has a verified page, section, DOI+page, or stable official-section anchor.
- **Yellow**: source is credible, but the specific claim lacks a page/figure/table anchor or needs edition-specific verification.
- **Red**: do not draft from this claim yet.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| David G. Lowe, "Distinctive Image Features from Scale-Invariant Keypoints," *International Journal of Computer Vision* 60, pp. 91-110 (2004). DOI: 10.1023/B:VISI.0000029664.99615.94. Springer page: https://link.springer.com/article/10.1023/B:VISI.0000029664.99615.94 | Anchor for SIFT as a hand-designed invariant local-feature method. | **Green** for bibliographic facts and abstract claims via Springer page: title/published/volume/pages lines 23-28; abstract lines 47-50; cite line 241. |
| Navneet Dalal and Bill Triggs, "Histograms of Oriented Gradients for Human Detection," CVPR 2005, pp. 886-893. Primary URL: https://hal.science/inria-00548512 (DOI 10.1109/CVPR.2005.177 currently returns HTTP 418 from Cloudflare; HAL is bibliographically equivalent and reachable). | Anchor for HOG as a gradient-feature descriptor evaluated with a linear SVM for human detection. | **Green** verified during anchor pass against HAL: pages 886-893, abstract lines 38-41 confirm linear-SVM detector, "significantly outperformed" framing, and 1,800-image dataset. Use HAL URL in prose footnotes. |
| PASCAL VOC2012 official site, "Visual Object Classes Challenge 2012 (VOC2012)." URL: https://www.robots.ox.ac.uk/~vgg/projects/pascal/VOC/voc2012/ | Anchor for VOC task design, 20 classes, challenge history, hidden test labels, 2010 ImageNet-associated challenge note, organizers, and infrastructure. | **Green** for official-section anchors: Introduction lines 45-64 and 77-80; Data lines 86-99; Best Practice lines 180-187; History and Background lines 225-280; Organizers lines 209-215. |
| Antonio Torralba and Alexei A. Efros, "Unbiased Look at Dataset Bias," CVPR 2011, pp. 1521-1528. DOI: 10.1109/CVPR.2011.5995347. PDF mirror: https://gwern.net/doc/ai/dataset/2011-torralba.pdf and CMU publication page: https://publications.ri.cmu.edu/unbiased-look-at-dataset-bias | Anchor for dataset bias, closed-world benchmarks, cross-dataset generalization, and data-value experiments. | **Green** for PDF page anchors: p. 1521 abstract; pp. 1522-1527 sections 2-6; RI page supplies bibliographic metadata and page range. |
| Mark Everingham, S. M. Ali Eslami, Luc Van Gool, Christopher K. I. Williams, John Winn, Andrew Zisserman, "The PASCAL Visual Object Classes Challenge: A Retrospective," *IJCV* 111(1), pp. 98-136 (2015). DOI: 10.1007/s11263-014-0733-5. URL: https://www.research.ed.ac.uk/en/publications/the-pascal-visual-object-classes-challenge-a-retrospective/ | Anchor for retrospective framing: VOC as dataset plus competition/workshop, five challenges, review of 2008-2012, limitations and weak points. | **Green** for abstract and bibliographic metadata via Edinburgh page lines 30-44 and 89-90. **Yellow** for figure-level performance claims until PDF pages are extracted. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Richard Szeliski, *Computer Vision: Algorithms and Applications*, 2nd ed. (2022). | Optional context for hand-engineered features and recognition pipelines. | Yellow. Open textbook exists, but no section anchor extracted in this contract. |
| Fei-Fei Li, *The Worlds I See* (2023). | Optional memoir context for ImageNet motivation in Ch40 transition only. | Yellow. No page anchor extracted; do not use for Ch39 load-bearing claims. |
| Dave Gershgorn, "The data that transformed AI research - and possibly the world," *Quartz* (2017). | Convenient journalistic bridge to ImageNet public memory. | Yellow. Secondary and not needed for the contract's Green backbone. |

## Green Claim Table

| ID | Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|---|
| G01 | Lowe's SIFT journal article was published in IJCV 60, pp. 91-110, in 2004. | 1 | Lowe 2004 Springer page, bibliographic lines 23-28 and cite line 241. | **Green** | Use 2004 IJCV as the main SIFT anchor; 1999 ICCV can be mentioned only as prior conference form if needed. |
| G02 | SIFT extracts distinctive invariant features for reliable matching across views; the abstract claims scale/rotation invariance and robustness to viewpoint, noise, and illumination changes. | 1 | Lowe 2004 Springer page, Abstract lines 47-50. | **Green** | Do not turn this into "SIFT solved vision"; keep it as local-feature evidence. |
| G03 | HOG studied robust visual object-recognition feature sets using linear-SVM human detection; its abstract says HOG descriptors significantly outperformed existing feature sets and introduced a harder dataset with over 1,800 annotated human images. | 1, 3 | Dalal & Triggs 2005, pp. 886-893, DOI 10.1109/CVPR.2005.177, Abstract in HAL/search result. | **Green** | Direct external `curl` was DNS-blocked, but the DOI/pages/abstract are consistently exposed in indexed scholarly pages. |
| G04 | VOC2012's main goal was recognizing objects from visual object classes in realistic scenes, as a supervised learning problem with labeled training images. | 2 | VOC2012 Introduction lines 45-47. | **Green** | This anchors the "realistic scenes" claim. |
| G05 | VOC2012 used twenty object classes spanning person, animals, vehicles, and indoor objects. | 2 | VOC2012 Introduction lines 47-59. | **Green** | Exact class list is anchored. |
| G06 | VOC2012 defined classification, detection, segmentation, action classification, ImageNet large-scale recognition, and person-layout tasks/competitions. | 2 | VOC2012 Introduction lines 53-80. | **Green** | Word carefully: three main competitions plus action, ImageNet, and person-layout taster. |
| G07 | The 2007 VOC year established the fixed 20 classes and had 9,963 images containing 24,640 annotated objects. | 2 | VOC2012 History and Background lines 237-249. | **Green** | "Fixed since then" is official-site language at line 249. |
| G08 | VOC2010 had 20 classes, 10,103 train/val images, 23,374 ROI annotated objects, and introduced an associated large-scale classification challenge based on ImageNet. | 2, 5 | VOC2012 History and Background lines 262-266. | **Green** | Use only as forward pointer. |
| G09 | VOC2011 and VOC2012 classification/detection trainval data had 11,530 images and 27,450 ROI annotated objects; VOC2012 reused the VOC2011 classification/detection data. | 2 | VOC2012 History and Background lines 270-280; VOC2012 vs VOC2011 lines 108-114. | **Green** | Supports compact dataset-scale comparison. |
| G10 | From VOC2008 onward, full test annotations were not released; results were submitted to an evaluation server, and best-practice guidance discouraged parameter tuning on the test set. | 2 | VOC2012 Data lines 96-99; Best Practice lines 180-187. | **Green** | This is the core infrastructure discipline claim. |
| G11 | A VOC classification example used bag-of-visual-words, Laplacian regions, SIFT descriptors, k-means visual words, spatial pyramids, and SVM classifiers. | 3 | VOC2012 Submission of Results example, lines 171-174. | **Green** | Treat as organizer-supplied summary of a previous method, not universal practice. |
| G12 | A VOC detection example used a discriminatively trained part-based model with HOG root/part templates and latent SVM, applied to all 20 VOC object detection challenges. | 3 | VOC2012 Submission of Results example, lines 175-178. | **Green** | Anchors HOG/SVM as benchmark-era machinery. |
| G13 | Torralba and Efros argued that datasets were central to progress but could narrow object-recognition research to benchmark numbers and become "closed worlds," explicitly including PASCAL VOC. | 4 | Torralba & Efros 2011 p. 1521, Abstract lines 7-24. | **Green** | The phrase may be quoted sparingly; no more than a short excerpt. |
| G14 | Their "Name That Dataset" toy experiment trained a 12-way linear SVM on 1,000 images per dataset and found identifiable dataset signatures. | 4 | Torralba & Efros 2011 p. 1521-1522, lines 43-54 and p. 1522 lines 62-90. | **Green** | Supports the "dataset signature" scene. |
| G15 | Torralba and Efros identify "creeping overfitting" in dataset competitions and cite PASCAL's changing datasets/withheld test set as mitigations; they also cite no statistically significant difference among the eight top-ranked 2010 PASCAL algorithms. | 2, 4 | Torralba & Efros 2011 p. 1522, lines 116-127. | **Green** | This is the best Green substitute for overbroad "plateau" language. |
| G16 | In the cross-dataset experiment, they used HOG detector plus linear SVM for detection and bag-of-words plus nonlinear SVM for classification. | 3, 4 | Torralba & Efros 2011 p. 1524, lines 228-239. | **Green** | Shows the standard baselines used to diagnose dataset bias. |
| G17 | Their Table 1 found large cross-dataset performance drops; for car classification, average self performance was 53.4% AP and mean-other performance was 27.5% AP. | 4 | Torralba & Efros 2011 p. 1524, Table 1 and lines 297-307. | **Green** | Avoid extrapolating to all real-world deployment. |
| G18 | They attributed dataset-bias problems to selection bias, capture bias, category/label bias, and negative-set bias. | 4 | Torralba & Efros 2011 p. 1524, lines 310-324. | **Green** | Good explanatory scaffold for prose. |
| G19 | They argued that a large negative set can be imperative, using the boat/water example, but that stress-testing negative-set sufficiency would require huge labeled data. | 4, 5 | Torralba & Efros 2011 p. 1525, lines 355-368. | **Green** | Useful for explaining "variance" without making up examples. |
| G20 | They framed benchmark improvement as coming either from better features/representations/learning algorithms or from more training data, but warned that data increases must be significant and bias-mismatched data may underperform. | 5 | Torralba & Efros 2011 p. 1525, lines 369-391. | **Green** | Direct bridge between algorithm and data infrastructure. |
| G21 | Their sample-value analysis found cross-dataset samples are devalued when used on another dataset; one example says 1 LabelMe car sample is worth 0.26 PASCAL car samples on the PASCAL benchmark. | 5 | Torralba & Efros 2011 p. 1526, Table 3 and lines 419-444. | **Green** | Use numbers carefully; do not generalize beyond paper setup. |
| G22 | Torralba and Efros concluded that modern datasets such as PASCAL VOC, ImageNet, and SUN09 fared comparatively well, while still emphasizing dataset quality as crucial for understanding the visual world. | 4, 5 | Torralba & Efros 2011 p. 1526, lines 461-473. | **Green** | This is the guardrail against blaming PASCAL too heavily. |
| G23 | Everingham et al. 2015 described VOC as both a public image/annotation/evaluation dataset and an annual competition/workshop, with five challenges and a review of 2008-2012. | 2 | Edinburgh page Abstract lines 30-34. | **Green** | Retrospective-level framing. |
| G24 | Everingham et al. 2015 is *IJCV* 111(1), pp. 98-136, DOI 10.1007/s11263-014-0733-5. | 2 | Edinburgh page lines 36-44 and 89-90. | **Green** | Bibliographic anchor. |
| G25 | Mark Everingham is described by the VOC2012 page as the key member of the VOC project; he died in 2012 and the VOC workshop at ECCV 2012 was dedicated to him. | 2 | VOC2012 page lines 10-12. | **Green** | People file anchor; avoid hagiographic expansion. |
| G26 | VOC2012 organizers listed Mark Everingham, Luc van Gool, Chris Williams, John Winn, and Andrew Zisserman. | 2 | VOC2012 Organizers lines 209-215. | **Green** | People file anchor. |
| G27 | VOC2012 images included Flickr images, with identities obscured for challenge/database-rights purposes. | 2, 5 | VOC2012 Database Rights lines 203-208. | **Green** | Useful infrastructure/legal detail. |
| G28 | VOC2012 was supported by the EU-funded PASCAL2 Network of Excellence. | 2 | VOC2012 Support lines 222-224. | **Green** | Institutional support anchor. |
| G29 | Since 2011, VOC submissions required an abstract of at least 500 characters describing the method. | 2 | VOC2012 Submission of Results lines 165-169. | **Green** | Shows evaluation-server social infrastructure. |

## Yellow Claim Table

| ID | Claim | Scene | Source | Status | Needed Anchor |
|---|---|---|---|---|---|
| Y01 | PASCAL VOC accuracy "plateaued around 2010." | 2, 5 | Everingham et al. 2015 likely figures/tables; Torralba & Efros p. 1522 supports statistical indistinguishability among top 2010 algorithms. | Yellow | Extract Everingham et al. 2015 PDF figure/table for annual AP curves before using "plateau" as a Green claim. |
| Y02 | Researchers spent years squeezing out tiny fractional gains on VOC. | 2 | General historical interpretation; Torralba & Efros p. 1522 supports incrementalism concern. | Yellow | Need workshop/proceedings or retrospective language quantifying incremental annual gains. |
| Y03 | Fei-Fei Li's ImageNet motivation was a direct response to the small/biased benchmark problem. | 5 | Fei-Fei Li memoir and ImageNet paper likely relevant. | Yellow | Need page anchor from *The Worlds I See* or Deng et al. 2009/ILSVRC sources. Mostly Ch40. |
| Y04 | ImageNet was designed specifically to break the PASCAL wall. | 5 | VOC2010 notes ImageNet-associated large-scale challenge; ImageNet sources not extracted here. | Yellow | Need ImageNet project paper/primary interview anchors; likely belongs in Ch40. |
| Y05 | Small datasets were the main reason deep neural networks did not dominate vision before 2012. | 5 | Plausible but cross-chapter claim involving compute, GPUs, architectures, and data. | Yellow | Need Ch40/Ch41 anchors; do not make it a Ch39 conclusion. |
| Y06 | Hand-engineered features were "the" blocker rather than one component of a broader data/evaluation wall. | 1, 5 | SIFT/HOG and Torralba-Efros support the components, not monocausal blame. | Yellow | Need comparative evidence separating algorithmic and data bottlenecks. |

## Red Claim Table

| ID | Claim | Scene | Why Red |
|---|---|---|---|
| R01 | Exact VOC annual leaderboard curves prove a 2010 plateau across almost all classes. | 2 | Everingham et al. 2015 PDF figures/tables were not extracted; do not state this precisely. |
| R02 | Private/internal ImageNet origin conversations show Li, Deng, or collaborators reacting directly to PASCAL limitations. | 5 | No archival, memoir-page, or interview anchor in this contract. |
| R03 | PASCAL-trained models failed catastrophically "in the real world." | 4 | Torralba-Efros measure cross-dataset generalization among datasets, not unconstrained real-world deployment. Use their measured setup instead. |

## Page Anchor Worklist

- Extract Everingham et al. 2015 accepted manuscript from Edinburgh/Oxford with `pdftotext` in an environment with network access. Needed: annual performance figures, statistical tests, and any explicit "limitations/weak points" conclusions beyond the abstract.
- Extract the official HAL PDF for Dalal-Triggs 2005 if shell network is available. The Green claim is strong enough for abstract-level use, but direct PDF text would improve the contract.
- Locate Deng et al. 2009 ImageNet and ILSVRC pages for Ch40 handoff only; do not pull Ch40's argument into this chapter.
- If using Li 2023 memoir, obtain physical/ebook page anchors. Do not cite by memory.

## Verification Notes

- Direct shell `curl` was attempted first per workflow but failed with DNS resolution errors in this sandbox. Browser verification was used for official pages and PDFs.
- The legacy Gemini prose was read only for scope. None of its citations were trusted without independent anchors.
