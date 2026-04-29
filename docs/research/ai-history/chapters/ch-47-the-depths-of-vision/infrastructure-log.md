# Infrastructure Log: Chapter 47 - The Depths of Vision

## Scene 1 - Depth Becomes the Road

- **AlexNet hardware and time:** two GTX 580 3GB GPUs; five to six days of training. Anchor: sources.md G1.
- **AlexNet architecture scale:** five convolutional layers plus three fully connected layers; 60 million parameters and 650,000 neurons in the PDF abstract. Anchor: sources.md G1.
- **VGG hardware and time:** Caffe-derived multi-GPU implementation; four NVIDIA Titan Black GPUs; two to three weeks to train one network depending on architecture. Anchor: sources.md G3.
- **VGG architecture scale:** 16-19 weight layers using small 3x3 filters. Anchor: sources.md G2.

## Scene 2 - The Wall Inside the Training Curves

- **Training condition:** ResNet paper's degradation evidence is not a failure to start training; the authors cite normalized initialization and batch normalization as enabling tens-layer networks to converge at the beginning. Anchor: sources.md G7.
- **Observed failure mode:** deeper plain networks show higher training error, not just worse validation error. Anchors: sources.md G8, G16.
- **Important constraint:** the authors argue this is unlikely to be vanishing gradients because BN kept forward signals nonzero and backward gradients had healthy norms. Anchor: sources.md G17.

## Scene 3 - The Identity Detour

- **Core mechanism:** residual mapping `F(x) := H(x) - x`; output `F(x) + x`. Anchor: sources.md G10.
- **Shortcut cost:** identity shortcuts add no extra parameters or computational complexity and can be trained with SGD/backprop; common libraries such as Caffe can implement them without solver changes. Anchor: sources.md G11.
- **Projection path:** projection shortcuts are available when dimensions change, but are not the core requirement for solving degradation. Anchors: sources.md G12, G19.

## Scene 4 - Engineering 152 Layers

- **Dataset scale:** ImageNet experiments use 1.28 million training images, 50k validation images, and 100k test images reported by the server. Anchor: sources.md G15.
- **Optimization recipe:** scale augmentation, 224x224 crops, batch normalization after each convolution and before activation, He initialization, SGD mini-batch 256, weight decay 0.0001, momentum 0.9, and no dropout. Anchor: sources.md G14.
- **Compute accounting:** 34-layer plain baseline at 3.6 billion FLOPs; VGG-19 comparison at 19.6 billion FLOPs. Anchor: sources.md G13.
- **Bottleneck design:** 50/101/152-layer networks use 1x1, 3x3, 1x1 bottleneck blocks partly because of training-time concerns. Anchor: sources.md G20.
- **152-layer cost:** 152-layer ResNet at 11.3 billion FLOPs, below VGG-16/19's listed 15.3/19.6 billion FLOPs. Anchor: sources.md G21.
- **Known gap:** exact GPU hardware and wall-clock training time for the ImageNet ResNet runs are not anchored. Source status: Yellow Y1.

## Scene 5 - Victory, Limits, and Afterlife

- **Classification result:** ResNet-152 single model: 4.49% top-5 validation error; ensemble: 3.57% top-5 test error and ILSVRC 2015 classification first place. Anchor: sources.md G22.
- **Official competition cross-check:** ImageNet official results page anchors MSRA detection and classification+localization standings. Anchor: sources.md G25.
- **Transfer:** ResNet-101 replacing VGG-16 in Faster R-CNN improves COCO's standard detection metric by 6.0 points, a 28% relative improvement. Anchor: sources.md G24.
- **Limit case:** 1202-layer CIFAR-10 ResNet trains but generalizes worse than the 110-layer model, which the authors attribute to overfitting. Anchor: sources.md G23.
