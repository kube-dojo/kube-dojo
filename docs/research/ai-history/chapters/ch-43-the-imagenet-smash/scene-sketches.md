# Scene Sketches: Chapter 43 - The ImageNet Smash

## Scene 1: The Scoreboard Was Already Waiting

Start with the contest rather than the neural network. ILSVRC had already turned ImageNet into a public ritual: teams received training data, submitted predictions against hidden test labels, and gathered around an annual workshop where progress could be compared. This matters because AlexNet's result was persuasive precisely because the target was not private. The benchmark inherited ImageNet's scale and WordNet organization from Ch40, but Ch43 should not retell the whole data-construction story. The new beat is the scoreboard: 1,000 categories, roughly 1.2 million training images in the AlexNet paper's working set, and a hidden-test discipline that could expose a real gap.

The scene should also establish the old regime without caricature. The pre-2012 winners were not fools; they represented sophisticated feature engineering and large-scale classification practice. Russakovsky et al. describe SIFT, LBP, Fisher-vector, compression, and SVM/linear-classifier systems as strong across the early years. That lets the prose say what AlexNet beat without claiming "computer vision was dead."

Anchors: G01, G02, G03, G04, G24.

## Scene 2: A Neural-Network Team Enters a Feature-Engineering Field

Move from the scoreboard to Toronto. The SuperVision team is Krizhevsky, Sutskever, and Hinton, and the system is a large deep CNN trained on raw RGB pixel values. The chapter can use ACM's later Turing Award framing to show that neural networks had been a minority commitment through skepticism, but it should stay disciplined: this is a background condition, not a license for invented underdog dialogue.

The technical center of the scene is scale as design pressure. The paper's abstract gives the architecture in one compact inventory: 60 million parameters, 650,000 neurons, five convolutional layers, and three fully connected layers. The prose should explain why this differs from feature-engineering pipelines: the system learns internal features from pixels, but only because ImageNet-scale data and GPU implementation make the experiment plausible.

Anchors: G05, G06, G07, G08, G09, G16.

## Scene 3: The Two-GPU Constraint

This is the chapter's main infrastructure scene, but keep it factual. The verified story is not a bedroom with heat shimmer; it is a memory and communication problem. A single GTX 580 had 3GB of memory, and the network was too large for one card. Krizhevsky et al. therefore split the network across two GPUs and allowed communication only at certain layers. Figure 2 shows the two halves; the architecture text describes where kernels connect across or stay within GPU partitions.

The prose should make the hardware constraint legible to non-specialists: this model was not simply "run on GPUs"; it was shaped by GPU memory, training time, and the need to keep communication below the cost of computation. Add the training rhythm: roughly 90 passes through 1.2 million images, five to six days on two GTX 580 3GB GPUs. Then show the supporting recipe: ReLUs made large experiments train faster, dropout and augmentation fought overfitting, and the system used raw RGB patches rather than hand-designed local descriptors.

Anchors: G10, G11, G12, G13, G14.

## Scene 4: The Smash

The result scene should be numerical and calm. Official ILSVRC Task 1 results list SuperVision at 0.15315 top-5 error using extra ImageNet Fall 2011 data and 0.16422 using only supplied training data. The ISI runner-up entry reports 0.26172 and describes a feature-fusion pipeline using SIFT/FV, LBP/FV, GIST/FV, and CSIFT/FV. The AlexNet paper tells the same basic story as 15.3% versus 26.2%, and Russakovsky et al. later give the same range with 99.9% confidence intervals.

Avoid vague awe language. The gap is strong enough without saying the establishment "was stunned" unless a source is found. The scene should instead explain the error metric, the data-condition caveat, and why a 10.9-point top-5 gap on a hidden test set was hard to dismiss. The "smash" is the public measurement, not a private emotional reaction.

Anchors: G15, G16, G17, G18, G23, G24.

## Scene 5: The Field Moves

End with the aftermath that is actually anchored. Russakovsky et al. say SuperVision's influence was clearly visible in ILSVRC2013 and ILSVRC2014: the vast majority of 2013 entries used deep CNNs, and almost all 2014 teams did. They also report that image-classification error fell from 16.4% to 6.7% between 2012 and 2014 on the unchanged post-2012 dataset. ACM's later Turing Award page gives the wider retrospective recognition: the 2012 Hinton/Krizhevsky/Sutskever work improved CNNs with ReLUs and dropout and almost halved object-recognition error.

The close should return to the thesis. AlexNet did not erase earlier vision work, invent CNNs, or prove that more compute alone wins. It showed that a public benchmark, a massive labeled dataset, a deep CNN, and commodity GPU parallelism could make learned features beat the strongest hand-engineered pipelines. That is enough. The next chapters can take up the platform race and deeper architectures.

Anchors: G19, G20, G21, G22.
