# Scene Sketches: Chapter 47 - The Depths of Vision

## Scene 1: Depth Becomes the Road

**Narrative purpose:** establish why "make it deeper" was an evidence-backed instinct, not a strawman.

AlexNet supplies the first beat: ImageNet scale, GPU training, and an eight-learned-layer CNN that made deep visual recognition feel newly practical. VGG supplies the second beat: the Oxford group makes depth itself the experimental variable, using 3x3 filters and pushing to 16-19 weight layers. The infrastructure is heavy and concrete: VGG's paper names Caffe-derived multi-GPU training, four Titan Black GPUs, and two to three weeks per network. End the scene with a question rather than a verdict: if depth keeps helping, what stops the field from just adding more layers?

Anchors: sources.md G1-G3. Capacity layer: 650-900 words.

## Scene 2: The Wall Inside the Training Curves

**Narrative purpose:** make the degradation problem precise and correct the vanishing-gradient shorthand.

Open on the ResNet paper's own puzzle. The authors know vanishing/exploding gradients are a historic obstacle, but they say initialization and normalization have largely addressed the "start converging" problem for tens-layer networks. The real surprise is stranger: a deeper plain network can show higher training error than a shallower one. This matters because a deeper model should, in principle, be able to copy the shallower model and set the added layers to identity. The solver's failure to find that constructed solution becomes the chapter's dramatic center.

Anchors: sources.md G6-G9, G16-G17. Capacity layer: 800-1,100 words.

## Scene 3: The Identity Detour

**Narrative purpose:** explain residual learning without turning it into generic textbook padding.

The conceptual turn is small enough to state directly. Instead of asking stacked layers to learn `H(x)`, He, Zhang, Ren, and Sun ask them to learn the residual `F(x) := H(x) - x`, then add the input back as `F(x) + x`. Figure 2 and Equation (1) give the prose a concrete object: a branch that carries `x` around two or three learned layers and adds it at the end. Identity shortcuts have no extra parameters or computational complexity. Projection shortcuts exist when dimensions need matching, but the paper's comparison says projection is not essential for addressing degradation.

Anchors: sources.md G10-G12, G18-G19. Capacity layer: 850-1,150 words.

## Scene 4: Engineering 152 Layers

**Narrative purpose:** show that ResNet is an optimization and infrastructure story, not only a diagram.

The ImageNet experiments run at the scale that made earlier systems hard: 1.28 million training images, 50k validation images, 100k test images. The recipe is specific enough to narrate without speculation: 224x224 crops, scale augmentation, batch normalization after convolutions, He initialization, mini-batch SGD, no dropout. Then the paper turns to economy. A 34-layer plain model is much cheaper than VGG-19 by FLOP count, and the 152-layer ResNet remains below VGG-16/19 complexity. The bottleneck block is not decorative; it is how the team can afford 50/101/152-layer models. Keep the unknowns visible: the paper does not state exact ImageNet GPU hardware or wall-clock training time.

Anchors: sources.md G13-G15, G20-G21, Y1. Capacity layer: 850-1,200 words.

## Scene 5: Victory, Limits, and Afterlife

**Narrative purpose:** land the historical consequence without claiming that depth became magic.

The headline result is clean: ResNet-152 reaches 4.49% single-model top-5 validation error, and an ensemble reaches 3.57% top-5 test error, winning ILSVRC 2015 classification. The official ImageNet page independently puts MSRA at the top of detection and localization-related standings, while the ResNet paper reports first places across ImageNet and COCO tracks. But the ending should resist triumphalism. On CIFAR-10, a 1202-layer ResNet trains, yet generalizes worse than a 110-layer network. The chapter closes by separating two claims: residual connections made very deep networks trainable; they did not make arbitrary depth automatically useful.

Anchors: sources.md G22-G26, Y3, R2. Capacity layer: 700-950 words.
