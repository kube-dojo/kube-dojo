# Scene Sketches: Chapter 27 - The Convolutional Breakthrough

## Scene 1: Pixels With Structure

Open with the difference between a generic vector and an image. A handwritten digit can shift a little and still be the same digit. That fact should become the bridge to convolution and shared weights, not a modern CNN lecture.

Evidence anchors:
- LeCun et al. 1989 pp.541, 544-546 for task-domain constraints, feature maps, local receptive fields, weight sharing, and parameter reduction.
- LeCun et al. 1998 pp.2283-2284 for LeNet-5, convolutional architecture, shared weights, subsampling, and robustness to shifts/distortions.

## Scene 2: From Neocognitron to Backprop

Fukushima provides the lineage: hierarchical visual recognition that tolerates shifts. The narrative then turns to Bell Labs, where similar architectural intuitions are paired with supervised gradient learning.

Evidence anchors:
- Fukushima 1980 pp.193-194 and 197-199 for hierarchy, S-cells/C-cells, widening receptive fields, and shift tolerance.
- LeCun et al. 1990 pp.399-400 and LeCun et al. 1998 pp.2283-2284 for the distinction between neocognitron lineage and supervised backpropagation training.

## Scene 3: The Postal Code Laboratory

The USPS digit task gives the chapter a concrete setting: messy handwritten digits, standardized images, and a task valuable enough to justify engineering. Keep this grounded in the source; do not invent a mailroom scene unless a source supplies operational detail.

Evidence anchors:
- LeCun et al. 1989 p.542 for Buffalo USPS data, train/test split, contractor preprocessing, and 16x16 normalization.
- LeCun et al. 1989 pp.547-550 and LeCun et al. 1990 pp.402-403 for training, test/rejection results, hardware, DSP implementation, and throughput.

## Scene 4: Checks, Throughput, and Engineering

LeNet-5 should appear as part of document recognition infrastructure. The story is strongest if the 1998 paper anchors check-processing claims, preprocessing, segmentation, and how the network fit into a larger system.

Evidence anchors:
- LeCun et al. 1998 pp.2278-2279 for document-system modules, commercial check deployment, and check-volume claims.
- LeCun et al. 1998 pp.2296-2298 and 2304-2305 for segmentation graphs, GTNs, and replicated convolutional recognizers.

## Scene 5: Why It Waited

Close by explaining why CNNs did not immediately dominate all vision: the method needed larger datasets, faster hardware, and broader software ecosystems. This hands off to the GPU/ImageNet chapters without making the 1990s seem like failure.

Evidence anchors:
- LeCun/Bengio/Hinton 2015 retrospective or another stable survey.
- LeCun et al. 1998 pp.2291-2292 for compute/training context and why LeNet-5-scale recognizers were not considered in 1989.
