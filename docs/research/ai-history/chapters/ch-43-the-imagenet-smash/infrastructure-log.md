# Infrastructure Log: Chapter 43 - The ImageNet Smash

## Scene 1: Benchmark Infrastructure

- **Dataset/evaluation form:** ILSVRC consisted of a public dataset plus annual competition/workshop, with hidden test annotations submitted through an evaluation server. Sources: G01; Russakovsky et al. 2015 p.1 lines 60-67.
- **Scale:** ILSVRC2012 standardized 1,000 classes and 1,431,167 annotated images, far beyond PASCAL VOC 2012's 20 classes and 21,738 images. Source: G02.
- **AlexNet paper's working subset:** roughly 1.2M training images, 50K validation images, and 150K test images across 1,000 categories. Source: G03.
- **Metric:** Top-5 error counts an image as correct if the true label is among up to five predicted classes. Source: AlexNet PDF p.1 lines 67-72; ILSVRC analysis lines 661-663.

## Scene 2: Model Infrastructure

- **Architecture size:** about 60M parameters and 650K neurons, with five convolutional and three fully connected layers. Source: G07.
- **Input pipeline:** images were downsampled to 256x256, then 224x224 crops and horizontal reflections were used during training/testing. Sources: AlexNet PDF p.1 lines 73-77; G12.
- **Training techniques:** ReLUs for faster learning, dropout in the first two fully connected layers, data augmentation, local response normalization, overlapping pooling, and SGD with momentum/weight decay. Sources: G12-G14; AlexNet PDF pp.3-6.

## Scene 3: GPU Infrastructure

- **Hardware:** two NVIDIA GTX 580 3GB GPUs. Sources: G10-G13.
- **Memory constraint:** one GTX 580 had only 3GB, so the model was split across two GPUs. Source: G11.
- **Communication pattern:** GPUs communicated only at selected layers; Figure 2 explicitly delineates layer responsibilities across the two GPUs. Source: G11.
- **Training duration:** roughly 90 cycles through 1.2M images, five to six days on the two GPUs. Source: G13.
- **Boundary:** No Green source places the GPUs in a bedroom, apartment, or describes heat/noise. Keep physical atmosphere generic or omit it. Source: Y01.

## Scene 4: Scoreboard Infrastructure

- **Official Task 1 result:** SuperVision 0.15315 top-5 error with extra Fall 2011 data; SuperVision 0.16422 using supplied data; ISI 0.26172. Source: G15.
- **Paper result framing:** Krizhevsky et al. report 15.3% for seven CNNs pre-trained on ImageNet Fall 2011, compared with 26.2% for the second-best entry. Source: G17.
- **Statistical follow-up:** Russakovsky et al. Table 8 gives 99.9% confidence intervals and says winners/runners-up were significantly different at that level. Source: G18.

## Scene 5: Post-2012 Infrastructure

- **Adoption in the benchmark:** vast majority of ILSVRC2013 entries and almost all ILSVRC2014 teams used deep CNNs as the basis of submissions. Source: G19.
- **Measured progress:** ILSVRC classification error fell from 16.4% to 6.7% between 2012 and 2014 on the unchanged post-2012 dataset. Source: G20.
- **Lesson:** ILSVRC organizers later argued that major object-recognition breakthroughs would not have been possible on a smaller scale. Source: G21.
- **Boundary:** This chapter stops at the benchmark turn. Later accelerator stacks, cuDNN, Tensor Cores, ResNet, and foundation-model scaling should not be backfilled into 2012.
