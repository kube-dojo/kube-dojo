# Infrastructure Log: Chapter 27
# Infrastructure Log: Chapter 27 - The Convolutional Breakthrough

## Data

- The 1989 paper uses handwritten zip-code digits from the U.S. Postal Service according to the MIT Press abstract.
- MNIST is later and should not be presented as the original 1989 dataset.
- Need exact training/test sizes before drafting numeric claims.

## Architecture

- Convolution/weight sharing encodes image locality and translation tolerance, reducing the burden on a generic fully connected network.
- Subsampling/pooling-style operations should be described historically using the paper's own terminology once page anchors are extracted.
- The key infrastructure idea is architectural constraint: domain knowledge moved into network shape.

## Compute and Hardware

- Do not name specific machines for 1989 or 1998 until sourced.
- LeNet's significance is partly that the task was small enough and constrained enough for available compute.
- If the 1998 paper specifies hardware or throughput, capture exact pages before drafting.

## Production Workflow

- Document recognition is a pipeline: image capture, normalization, segmentation, recognition, and downstream business rules.
- Bank-check or postal deployment claims need exact primary anchors.
- Avoid turning the chapter into "neural net magic"; old-fashioned engineering and preprocessing likely mattered.

## Claims Not Yet Safe

- Specific check-volume numbers.
- "First CNN."
- Exact commercial deployment timeline.
- Hardware names/speeds.
