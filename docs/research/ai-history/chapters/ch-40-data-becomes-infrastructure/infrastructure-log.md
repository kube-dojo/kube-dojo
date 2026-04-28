# Infrastructure Log: Chapter 40 - Data Becomes Infrastructure

## Scene 1: From Model Tuning to Data Scale

- **Conceptual infrastructure:** Li's retrospective ACM slides frame the project as moving visual recognition emphasis from modeling to data and "lots of data." Source: G13.
- **Failed launch infrastructure:** The slide-deck calculation for a psychophysics/undergraduate approach reaches about 19 years under the stated assumptions, motivating scalable labor. Source: G15.

## Scene 2: WordNet Becomes a Visual Skeleton

- **Lexical database:** WordNet organizes word meanings as synsets and connects them through semantic relations. Sources: G02-G04.
- **Ontology transfer:** ImageNet uses WordNet's hierarchy as the backbone for visual categories. Sources: G05-G06.
- **Boundary:** WordNet was not built for ImageNet or computer vision. It was a lexical/psycholinguistic database repurposed as visual infrastructure. Source: R05.

## Scene 3: Candidate Images From the Web

- **Search engines:** ImageNet queried multiple image search engines for each synset using WordNet synonyms. Source: G09.
- **Query expansion:** The team added parent-synset terms when the same word appeared in a target gloss, e.g. expanding a specific term with a broader animal/category term. Source: G09.
- **Multilingual expansion:** Candidate pools were diversified using Chinese, Spanish, Dutch, and Italian translations from other WordNets. Source: G10.
- **Noise constraint:** The paper reports average search-result accuracy around 10%, requiring large candidate pools before cleaning. Source: G09.

## Scene 4: The Human Verification Machine

- **AMT service layer:** AMT provided the online labor platform; Ch38 anchors requesters, HITs, workers/Turkers, rewards, qualifications, approval, and bonuses. Sources: G20-G21.
- **Verification task:** Workers saw candidate images and a target synset definition and verified whether the image contained that synset. Source: G11.
- **Redundancy/quality:** Multiple independent votes, at least 10 votes on initial subsets, confidence score tables, and threshold stopping rules turned individual judgments into a dataset-cleaning process. Source: G12.
- **Scale:** Li's 2017 slides report 49k workers from 167 countries during 2007-2010. Source: G16.
- **Reported accuracy:** Deng et al. report 99.7% precision on sampled synsets. Source: G23.

## Scene 5: A Dataset Becomes a Benchmark

- **2009 state:** The paper reports 12 subtrees, 5,247 synsets, and 3.2 million images. Source: G07.
- **Later scale:** As of August 2014, Russakovsky et al. report 21,841 synsets and 14,197,122 annotated images. Source: G19.
- **Benchmark infrastructure:** ILSVRC has a public dataset plus annual competition/workshop and hidden test annotations/evaluation flow. Source: G17.
- **Scale jump from VOC:** ILSVRC 2010 moved to 1,000 classes and 1,461,406 images from PASCAL VOC 2010's 20 classes and 19,737 images. Source: G18.
- **Boundary:** The GPU/CNN training infrastructure and AlexNet result are deferred to Ch43.
