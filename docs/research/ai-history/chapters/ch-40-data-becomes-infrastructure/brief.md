# Brief: Chapter 40 - Data Becomes Infrastructure

## Thesis

ImageNet was not simply a larger benchmark. It turned labeled visual data into research infrastructure: WordNet supplied a semantic scaffold, web search supplied noisy candidate images, Amazon Mechanical Turk supplied scalable human verification, and the 2009 ImageNet paper made the pipeline visible as an engineering system. The chapter's claim is narrower than the later deep-learning triumph: before AlexNet, ImageNet mattered because it reframed object recognition around organized, clean, high-volume data that could be shared, benchmarked, and extended.

## Scope

- IN SCOPE: ImageNet's 2006-2009 construction arc; WordNet as the ontology of synsets and semantic relations; Fei-Fei Li's shift from model-centered visual recognition toward data-centered infrastructure; the Princeton ImageNet team around Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li, and Li Fei-Fei; web-image candidate collection; multilingual query expansion; AMT verification; redundancy and quality control; the 2009 CVPR paper; the creation of the ILSVRC handoff as a sparse forward pointer.
- OUT OF SCOPE: a full labor history of MTurk (Ch38); the PASCAL VOC wall and hand-engineered feature stack (Ch39); AlexNet, GPUs, and the 2012 error-rate break (Ch43); ImageNet bias, privacy, and people-subtree remediation except as a brief caveat if needed later; modern foundation-model dataset pipelines.

## Boundary Contract

This chapter must not claim that ImageNet by itself caused the deep-learning revolution. It can say ImageNet created a large, shared, manually verified visual-data infrastructure later used by ILSVRC and AlexNet, but the GPU/CNN breakthrough belongs to Ch43. It must not portray PASCAL VOC as a failure; Ch39 treats it as disciplined benchmark infrastructure whose scale limits became visible. It must not turn MTurk into an ImageNet-only invention; Ch38 owns the broader "human API" story.

The chapter must also avoid unanchored internal motives. Fei-Fei Li's public talks and later interviews support a broad "shift from modeling to data" framing, but precise private conversations, reviewer reactions, poster-session indifference, and claims that colleagues "ignored" the 2009 CVPR work remain Yellow or Red unless a page/slide/interview anchor is added. Use the 2017 ACM slide deck and the 2009 paper for verified scenes, not invented lab drama.

## Scenes Outline

1. **From Model Tuning to Data Scale.** Li's later ACM talk frames the move as a shift in visual recognition from modeling to data, after earlier few-shot/object-recognition work. The scene bridges from Ch39's benchmark wall without blaming PASCAL.
2. **WordNet Becomes a Visual Skeleton.** WordNet's synsets and semantic relations become ImageNet's backbone: not a folder of labels, but an ontology of visual concepts.
3. **Candidate Images From the Web.** The team turns each synset into search queries, expands those queries with parent-synset terms, translates them into other languages, and gathers noisy candidate pools large enough to survive cleaning.
4. **The Human Verification Machine.** AMT workers do not "label from scratch"; they verify candidate images against synset definitions. Multiple independent votes, confidence tables, and thresholds convert scattered human judgments into a clean dataset.
5. **A Dataset Becomes a Benchmark.** The 2009 paper reports 12 subtrees, 5,247 synsets, and 3.2 million images, then ILSVRC turns ImageNet into an annual benchmark. The closing pointer stops before AlexNet.

## Prose Capacity Plan

This chapter can support a substantial but capped narrative if it spends words on the verified infrastructure layers:

- 550-750 words: **From model tuning to data scale** - introduce the late-2000s transition from modeling emphasis to data emphasis, using Li's 2017 ACM talk as a retrospective primary anchor and Ch39 only as a short bridge. Anchored to: Green G13 (ACM slide deck pp.17-18, shift from modeling to data), G14 (slides pp.27-31, failed launch attempts and MTurk emergence), and Yellow Y01 for the 2006 origin. Scene: 1.
- 650-900 words: **WordNet as the semantic skeleton** - explain synsets, semantic relations, and why ImageNet's unit was a WordNet concept rather than an ad hoc class label. Anchored to: Green G01-G04 (WordNet PDF pp.1-6 and p.66) and G05-G07 (Deng et al. 2009 p.248 and p.249). Scene: 2.
- 650-900 words: **Candidate-image collection as infrastructure** - show the web-search pipeline, noisy search results, duplicate removal, parent-synset query expansion, and multilingual expansion. Anchored to: Green G08-G10 (Deng et al. 2009 Section 3.1, CVPR p.251). Scene: 3.
- 850-1,150 words: **AMT verification and quality control** - center the strongest operational scene on humans verifying each candidate image, the global labor platform, multiple independent votes, at least 10 votes in initial subsets, confidence thresholds, and reported precision. Anchored to: Green G11-G12 (Deng et al. 2009 Section 3.2, CVPR pp.251-252), G16 (ACM slide deck p.31 for 49k workers/167 countries), and G20-G21 from Ch38 for MTurk mechanics if a one-paragraph bridge is needed. Scene: 4.
- 700-1,000 words: **From ImageNet paper to benchmark handoff** - present the 2009 paper's scale, compare it carefully with earlier datasets, and close with ILSVRC's annual benchmark structure as a forward pointer. Anchored to: Green G17-G19 (Russakovsky et al. 2015 pp.1-3), G06/G23 (Deng et al. 2009 p.248/p.249), and G18 (ILSVRC 2010 scale). Scene: 5.

Total: **3,400-4,700 words**. Label: `3k-5k likely`.

If the verified evidence runs out, cap the chapter.

## Citation Bar

- Minimum primary/near-primary anchors before prose: Miller et al. WordNet PDF; Deng et al. 2009 ImageNet CVPR paper; Fei-Fei Li 2017 ACM TechTalk page/slides; Russakovsky et al. 2015 ILSVRC paper.
- Minimum secondary/context anchors before prose: Gershgorn 2017 only for public-memory framing if exact accessible anchors are located; Denton et al. 2021/2022 dataset genealogy only for later critique if page anchors are extracted; Li 2023 memoir only with edition-specific page anchors.
- The legacy Gemini prose is not an evidentiary source. It only identified likely scene scope.

## Conflict Notes

- **2009 paper scale vs later ImageNet scale:** Deng et al. report 3.2 million images across 5,247 synsets in the current 2009 version; Russakovsky et al. later report 14,197,122 annotated images across 21,841 synsets as of August 2014. Do not collapse those into one timeless number.
- **"15 million images" shorthand:** Li's 2017 slides use 15M total images for later ImageNet. The 2009 chapter scene should use the 2009 paper's 3.2M figure unless explicitly moving to later growth.
- **Motivation and reception:** "In 2006 Li started ruminating" and "reviewers ignored the dataset" are secondary/journalistic or memoir-dependent until page anchors are located. Keep them Yellow.
- **Causality:** Green sources support scale, organization, annotation, and benchmark creation. They do not prove ImageNet alone "made deep learning work."
- **Labor:** Li's slides give 49k workers from 167 countries for 2007-2010. Wage, conditions, and MTurk-origin claims belong mostly to Ch38 unless a short ethical caveat is necessary.

## Honest Prose-Capacity Estimate

The verified evidence supports a natural **3,400-4,700 word** chapter. The middle two scenes are strong because Deng et al. give implementation detail and Li's slides give a retrospective construction arc. The upper end would require edition-specific page anchors from *The Worlds I See*, a clean transcript of Li's 2017/2019 talks, or archival/interview anchors about reception at CVPR 2009. Without those, draft near 4,000 words and avoid invented conference drama.
