# Scene Sketches: Chapter 39 - The Vision Wall

## Scene 1: A Feature Has To Be Designed

Open with a feature, not a failure. Lowe's SIFT article describes a method for extracting distinctive invariant features from images, robust across scale, rotation, viewpoint, noise, and illumination; Dalal and Triggs then show HOG as a carefully engineered grid of gradient descriptors for human detection with a linear SVM. The scene should make hand design feel impressive and concrete: gradients, local normalization, keypoints, matching, Hough clusters, SVM windows. It should not mock these systems from deep-learning hindsight.

Anchors: G01-G03. Prose budget: 650-900 words.

## Scene 2: The Benchmark Becomes the Room

Move to PASCAL VOC as infrastructure. The official VOC2012 page defines the goal as recognizing objects from visual classes in realistic scenes, lists the 20 fixed classes, and describes classification, detection, segmentation, action classification, person layout, and the associated ImageNet large-scale challenge. The scene should show how a benchmark becomes a room the field can meet inside: public data, training/validation splits, hidden test labels, evaluation server, workshops, organizers, and method abstracts.

Anchors: G04-G10, G23-G29. Prose budget: 750-1,000 words.

## Scene 3: The Winning Stack

Show what "state of the art" looked like before the ImageNet turn. The VOC page's own method examples describe SIFT descriptors becoming visual words, histograms, spatial pyramids, and SVM classifiers; the detection example describes HOG templates and latent SVMs. Torralba and Efros use HOG+linear SVM and bag-of-words+nonlinear SVM as standard baselines for cross-dataset testing. The point is not that every system was identical, but that the era had a recognizable feature/classifier toolkit.

Anchors: G11-G12, G15-G16, plus G01-G03. Prose budget: 550-800 words.

## Scene 4: Name That Dataset

This is the empirical heart. Torralba and Efros invite the community to identify datasets from sample images, then train a classifier to do the same. The results reveal dataset signatures. Their cross-dataset experiments make the cost visible: car classification self performance averaging 53.4% AP drops to 27.5% AP on other datasets. Bias is not one thing but selection, capture, category/label, and negative-set bias. Include their guardrail: PASCAL and ImageNet often generalize comparatively well among modern datasets. The wall is structural, not a simple indictment of one benchmark.

Anchors: G13-G18, G22. Prose budget: 900-1,200 words.

## Scene 5: The Wall Points Forward

Close on scale pressure. Torralba and Efros frame two ways to improve benchmark performance: improve features/representations/learning algorithms, or enlarge training data. But more data has value only if it carries the right variance; cross-dataset samples are discounted, and adequate negative sets may require huge labeled data. The VOC2010 page's ImageNet-associated challenge note gives a restrained forward pointer: the next chapter can tell the ImageNet story. Ch39 ends at the wall, not beyond it.

Anchors: G08, G19-G21, G23. Prose budget: 550-800 words.
