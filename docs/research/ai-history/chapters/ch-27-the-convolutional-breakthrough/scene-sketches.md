# Scene Sketches: Chapter 27
# Scene Sketches: Chapter 27 - The Convolutional Breakthrough

## Scene 1: Pixels With Structure

Open with the difference between a generic vector and an image. A handwritten digit can shift a little and still be the same digit. That fact should become the bridge to convolution and shared weights, not a modern CNN lecture.

Evidence needed:
- LeCun 1989 domain-constraint passage.
- LeCun 1998 architecture explanation.

## Scene 2: From Neocognitron to Backprop

Fukushima provides the lineage: hierarchical visual recognition that tolerates shifts. The narrative then turns to Bell Labs, where similar architectural intuitions are paired with supervised gradient learning.

Evidence needed:
- Fukushima 1980 architecture passage.
- LeCun 1998 historical discussion, if present.

## Scene 3: The Postal Code Laboratory

The USPS digit task gives the chapter a concrete setting: messy handwritten digits, standardized images, and a task valuable enough to justify engineering. Keep this grounded in the source; do not invent a mailroom scene unless a source supplies operational detail.

Evidence needed:
- LeCun 1989 USPS passage.
- Training/test data and performance page anchors.

## Scene 4: Checks, Throughput, and Engineering

LeNet-5 should appear as part of document recognition infrastructure. The story is strongest if the 1998 paper anchors check-processing claims, preprocessing, segmentation, and how the network fit into a larger system.

Evidence needed:
- LeCun 1998 LeNet-5 and deployment passages.
- Exact throughput/production claims if used.

## Scene 5: Why It Waited

Close by explaining why CNNs did not immediately dominate all vision: the method needed larger datasets, faster hardware, and broader software ecosystems. This hands off to the GPU/ImageNet chapters without making the 1990s seem like failure.

Evidence needed:
- LeCun/Bengio/Hinton 2015 retrospective or another stable survey.
