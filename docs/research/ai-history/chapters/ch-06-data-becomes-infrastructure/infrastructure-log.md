# Infrastructure Log: Chapter 6

## Technical Metrics & Constraints

### The Data Status Quo (pre-ImageNet)
- **PASCAL VOC (circa 2006-2008):**
  - Scope: 20 classes.
  - Scale: Tens of thousands of images.
  - Constraint: Models trained on this overfit rapidly; they learned the dataset, not the world.

### The New Infrastructure
- **Amazon Mechanical Turk (AMT):**
  - Workforce: Global, distributed human intelligence.
  - Role in AI: Treated as an API call for human labeling; a computational pipeline rather than just labor.
- **ImageNet (2009 release):**
  - Scale: 3.2 million labeled images.
  - Taxonomy: 5,247 synsets (categories) based on WordNet.
  - Ultimate Scale: Grew to over 14 million images and 21,000+ synsets.