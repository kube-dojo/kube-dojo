# Scene Sketches: Chapter 40 - Data Becomes Infrastructure

## Scene 1: From Model Tuning to Data Scale

Open with the conceptual pivot, not with a fabricated conference scene. Ch39 has just shown a computer-vision culture disciplined by features, classifiers, datasets, and evaluation servers. Li's 2017 ACM slides offer a clean retrospective bridge: visual recognition needed to shift from modeling to data, and then to lots of data. The scene can briefly mention her earlier few-shot/object-recognition work only as background if sourced elsewhere; the Green center is the slide-deck framing.

The strongest dramatic material is the failed scaling math. The slide deck describes an early psychophysics/undergraduate approach and a calculation involving 40,000 synsets, 10,000 candidate images per synset, 2-5 verifiers, and a result of about 19 years. Treat this as Li's retrospective slide calculation, not as a formal archival budget. The point is that data infrastructure forced a labor and systems question before it became a model question.

Anchors: G13, G14, G15. Yellow texture: Y01, Y04.

## Scene 2: WordNet Becomes a Visual Skeleton

Turn WordNet into the chapter's first concrete machine. WordNet was a Princeton lexical database, not a vision dataset. It organized meanings as synsets and connected them with semantic relations such as hypernym/hyponym pointers. That mattered because ImageNet needed categories that were disambiguated before images were attached to them. A "bank" could not simply be a word; it had to be a specific sense.

Then show ImageNet's move: the 2009 paper says ImageNet is a large-scale ontology of images built on WordNet, aiming at most of WordNet's roughly 80,000 noun synsets with 500-1,000 clean full-resolution images each. The scene should make the ontology visible as infrastructure: a semantic skeleton that let the project ask for dog breeds, vehicles, instruments, flowers, and other visual concepts systematically rather than by ad hoc benchmark labels.

Anchors: G01-G06.

## Scene 3: Candidate Images From the Web

This scene is procedural. Each synset becomes a search problem. The team queries image search engines with WordNet synonyms, faces the search engines' retrieval limits and noise, expands queries with parent-synset terms, and translates queries into Chinese, Spanish, Dutch, and Italian to widen the candidate pool. The paper's detail lets the prose avoid vague "scraping millions of images" language.

The key tension is that the internet was abundant but dirty. Deng et al. report average search-result accuracy around 10% and a target of 500-1,000 clean images per synset, so the system must overcollect candidates before cleaning. That is the infrastructure story: scale first creates a quality problem, then the pipeline has to solve it.

Anchors: G08-G10.

## Scene 4: The Human Verification Machine

Center the chapter's strongest operational scene here. AMT workers are not magic label generators; they verify candidate images against target synset definitions. The task page presents image sets and a definition, and users decide whether each image contains objects of that synset. This is where Ch38's human-API abstraction becomes a concrete computer-vision data factory.

The prose should spend real time on redundancy and disagreement. Deng et al. explain that users make mistakes, not all users follow instructions, and subtle synsets create disagreement. The solution is multiple independent votes, initial subsets with at least 10 votes per image, confidence score tables, and threshold-based stopping for remaining images. Li's later slides add scale: 49k workers from 167 countries over 2007-2010. The scene should respect the workers as people while keeping the labor-history deep dive in Ch38.

Anchors: G11-G12, G16, G20-G21, G23.

## Scene 5: A Dataset Becomes a Benchmark

Close with publication and handoff. In 2009, the paper reports 12 subtrees, 5,247 synsets, and 3.2 million images. It also argues that ImageNet is larger, more diverse, and more accurate than contemporary image datasets, and it demonstrates uses in object recognition, classification, and clustering. Keep those as reported claims, not omniscient hindsight.

Then move one step forward to ILSVRC. Russakovsky et al. say ILSVRC has run annually since 2010 as a public dataset plus annual competition/workshop. The scale jump from PASCAL VOC 2010 to ILSVRC 2010 makes the infrastructural shift legible: 20 classes and 19,737 images becomes 1,000 classes and 1,461,406 images. End with a pointer that this infrastructure will matter when neural networks and GPUs arrive in Ch43, but do not draft the AlexNet argument here.

Anchors: G07, G17-G19, G23. Yellow texture: Y02, Y07.
