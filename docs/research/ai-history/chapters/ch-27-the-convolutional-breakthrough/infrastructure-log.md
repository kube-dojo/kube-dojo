# Infrastructure Log: Chapter 27 - The Convolutional Breakthrough

## Data

- LeCun et al. 1989 p.542 anchors 9,298 segmented handwritten numerals from real U.S. Mail passing through the Buffalo, NY post office, with 7,291 training and 2,007 test examples.
- LeCun et al. 1990 pp.397-398 corroborate the Buffalo USPS data and add printed-font augmentation details.
- LeCun et al. 1998 pp.2286-2287 anchor MNIST as a later modified NIST dataset, with 60,000 training and 10,000 test images. Do not present MNIST as the original 1989 USPS dataset.

## Architecture

- Convolution/weight sharing encodes image locality and translation tolerance, reducing the burden on a generic fully connected network.
- Subsampling/pooling-style operations should be described historically using LeCun et al.'s own terminology: feature maps, shared weights, local averaging, and subsampling.
- The key infrastructure idea is architectural constraint: domain knowledge moved into network shape.
- Fukushima 1980 pp.193-194 and 197-199 support hierarchy and shift-tolerant lineage; LeCun et al. 1989 pp.544-546 and LeCun et al. 1998 pp.2283-2284 support trained convolutional feature maps and parameter reduction.

## Compute and Hardware

- LeCun et al. 1989 pp.546-550 anchors SUN-4/260 training and DSP/PC implementation details.
- LeCun et al. 1990 pp.402-403 anchors SN2 on a Sun SPARCstation 1 and AT&T DSP-32C throughput.
- LeCun et al. 1998 pp.2291-2292 anchors LeNet-5 training time on a Silicon Graphics Origin 2000 server and explains why a recognizer as complex as LeNet-5 was not considered in 1989.
- LeNet's significance is partly that the task was small enough and constrained enough for available compute.

## Production Workflow

- Document recognition is a pipeline: image capture, normalization, segmentation, recognition, and downstream business rules.
- LeCun et al. 1998 p.2278 anchors field extraction, segmentation, recognition, language modeling, commercial deployment, and several million checks per day.
- LeCun et al. 1998 pp.2296-2298 and 2304-2305 anchor segmentation graphs, GTNs, Viterbi interpretation, and replicated convolutional recognizers.
- Avoid turning the chapter into "neural net magic"; old-fashioned engineering and preprocessing likely mattered.

## Claims Not Yet Safe

- "First CNN."
- Exact commercial deployment timeline beyond the 1998 paper's NCR/check-system statements.
- Broader Bell Labs lineage unless Denker et al. 1988/1989 is added.
