# Infrastructure Log: Chapter 39 - The Vision Wall

## Feature Infrastructure

- **SIFT:** Local invariant image features, designed for matching across scale, rotation, viewpoint, noise, and illumination changes. Recognition pipeline in Lowe's abstract: nearest-neighbor feature matching, Hough-transform clustering, and pose verification. Sources: G01-G02.
- **HOG:** Dense grid of histogram-of-oriented-gradient descriptors, local contrast normalization in overlapping blocks, and linear-SVM detection in the Dalal-Triggs human-detection setup. Source: G03.
- **Bag-of-visual-words and SVMs:** VOC's own example classification summary uses SIFT descriptors, k-means visual words, histograms, spatial pyramids, and SVM classifiers. Source: G11.
- **Part-based HOG and latent SVM:** VOC's example detection summary uses a HOG root template, higher-resolution HOG part templates, and latent-SVM training. Source: G12.

## Benchmark Infrastructure

- **VOC task shape:** Realistic-scene recognition with labeled training images, 20 object classes, and classification/detection/segmentation tasks. Sources: G04-G06.
- **Dataset scale:** VOC2007 had 9,963 images and 24,640 objects; VOC2010 train/val had 10,103 images and 23,374 ROI objects; VOC2011/2012 trainval had 11,530 images and 27,450 ROI objects. Sources: G07-G09.
- **Hidden tests:** From VOC2008 onward, full test annotations were not released; test results went through the evaluation server. Sources: G10.
- **Submission discipline:** VOC2012 expected method descriptions and, from 2011, required abstracts of at least 500 characters. Source: G29.
- **Institutional support:** VOC2012 lists support from the EU-funded PASCAL2 Network of Excellence and organizers at Leeds, ETHZ, Edinburgh, Microsoft Research Cambridge, and Oxford. Sources: G26-G28.

## Data-Bias Infrastructure

- **Dataset signatures:** Torralba and Efros's 12-way "Name That Dataset" experiment found that datasets had recognizable signatures. Sources: G13-G14.
- **Cross-dataset testing:** Their experiments used shared object classes across SUN09, LabelMe, PASCAL VOC 2007, ImageNet, Caltech-101, and MSRC. Source: G16.
- **Measured generalization drop:** For car classification, self performance averaged 53.4% AP while mean-other performance averaged 27.5% AP. Source: G17.
- **Bias categories:** Selection, capture, category/label, and negative-set bias. Source: G18.
- **Scale pressure:** Their data-value analysis says larger training sets can help, but the increase must be substantial and bias-mismatched data is discounted. Sources: G19-G21.

## Explicit Unknowns

- Exact compute hardware used by VOC participants is not anchored in this contract. Do not invent GPU/CPU details.
- Exact annual leaderboard curves from the Everingham retrospective are not extracted. Keep "plateau" Yellow until figure/table anchors are obtained.
