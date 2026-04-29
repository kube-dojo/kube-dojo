# Sources: Chapter 47 - The Depths of Vision

## Verification Key

- **Green**: claim has a verified page, section, or stable official-source anchor.
- **Yellow**: source is credible, but the exact claim is not yet page-located or needs another anchor.
- **Red**: do not draft this claim unless new evidence is found.

## Source Access Note

The local shell could not resolve external hosts during this pass (`curl: (6) Could not resolve host: arxiv.org`). Anchors below were verified through browser-backed PDF/HTML extraction and should be re-checkable from the listed stable URLs. No page numbers, URLs, DOIs, or quotes are fabricated.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun, "Deep Residual Learning for Image Recognition," CVPR 2016, pp. 770-778. CVF: https://openaccess.thecvf.com/content_cvpr_2016/html/He_Deep_Residual_Learning_CVPR_2016_paper.html PDF: https://openaccess.thecvf.com/content_cvpr_2016/papers/He_Deep_Residual_Learning_CVPR_2016_paper.pdf arXiv: https://arxiv.org/pdf/1512.03385 | Core primary source for degradation, residual learning, shortcuts, architecture, ImageNet/CIFAR/COCO results. | **Green**. Browser PDF extraction verified the relevant text on PDF pp. 770-778 (also arXiv PDF pp. 1-8). CVF page verifies CVPR venue and proceedings pp. 770-778. |
| Alex Krizhevsky, Ilya Sutskever, Geoffrey Hinton, "ImageNet Classification with Deep Convolutional Neural Networks," NeurIPS 2012. Proceedings page: https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-network PDF: https://papers.nips.cc/paper_files/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf | Context for AlexNet's ImageNet CNN, GPU dependence, and eight learned layers. | **Green** for specific claims in G1. Browser PDF extraction verified pp. 1-4. |
| Karen Simonyan and Andrew Zisserman, "Very Deep Convolutional Networks for Large-Scale Image Recognition," ICLR 2015 / arXiv:1409.1556. PDF: https://arxiv.org/pdf/1409.1556 | Context for pre-ResNet depth escalation, VGG's 16-19 layers, 3x3 filters, and training cost. | **Green** for specific claims in G2-G3. Browser PDF extraction verified pp. 1-5. |
| ILSVRC2015 Results, ImageNet official page. URL: https://image-net.org/challenges/LSVRC/2015/results | Competition-result cross-check for MSRA detection/localization standings and official metrics. | **Green** for specific results in G25. HTML section anchors verified. Pure classification table not found in fetched text; see Y3. |

## Secondary / Context Sources

| Source | Use | Verification |
|---|---|---|
| CVF ResNet landing page, "Deep Residual Learning for Image Recognition." | Venue, authors, CVPR 2016 proceedings pp. 770-778, abstract-level summary. | **Green** as official venue metadata; use paper PDF for technical claims. |
| Richard Szeliski, *Computer Vision: Algorithms and Applications*, 2nd ed. (Springer, 2022). Book page: https://szeliski.org/Book/ | Potential secondary context for modern computer vision reception. | Yellow. Page/section anchor not extracted; do not use for load-bearing claims yet. |
| Ian Goodfellow, Yoshua Bengio, Aaron Courville, *Deep Learning* (MIT Press, 2016). | Broad context on optimization/deep nets if needed. | Yellow. No ResNet-specific page anchor extracted in this pass. |

## Scene-Level Claim Table

| ID | Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|---|
| G1 | AlexNet used a large ImageNet CNN with five convolutional and three fully connected layers; it trained on two GTX 580 3GB GPUs for five to six days. | 1 | Krizhevsky et al. 2012 PDF p. 1 (architecture and winning result), pp. 2-3 (two GTX 580 GPUs), p. 4 (Figure 2 architecture) | NeurIPS proceedings page abstract | **Green** | Use only as context. The NeurIPS page abstract differs slightly from the PDF on dataset/result numbers; prefer the PDF when naming exact values. |
| G2 | VGG showed that ImageNet accuracy improved by pushing depth to 16-19 weight layers with small 3x3 filters. | 1 | Simonyan and Zisserman 2015 PDF p. 1 (abstract), pp. 2-3 (Table 1 configurations and 3x3 discussion) | ResNet paper p. 770 cites VGG as 16-layer evidence | **Green** | Anchor for "depth was already the road." |
| G3 | VGG training used a Caffe-derived multi-GPU implementation; on four NVIDIA Titan Black GPUs, a single network took two to three weeks depending on architecture. | 1, 4 | Simonyan and Zisserman 2015 PDF p. 5, Section 3.3 "Implementation Details" | VGG paper p. 5 | **Green** | Infrastructure contrast for ResNet; do not transfer VGG hardware to ResNet. |
| G4 | He, Zhang, Ren, and Sun's ResNet paper appeared at CVPR 2016, pp. 770-778, from Microsoft Research. | 2-5 | CVF ResNet landing page; ResNet PDF p. 770 author block | CVF proceedings metadata | **Green** | Venue/metadata row. |
| G5 | The ResNet abstract claims up to 152 layers, 3.57% ImageNet test error as an ensemble, and first place in ILSVRC 2015 classification. | 5 | ResNet PDF p. 770 (abstract) | CVF landing page abstract | **Green** | Use detailed result rows G22-G25 for prose. |
| G6 | Before ResNet, leading ImageNet results used "very deep" models of roughly 16 to 30 layers, prompting the question of whether stacking more layers was enough. | 1, 2 | ResNet PDF p. 770, Section 1 | VGG PDF p. 1; GoogLeNet CVPR 2015 abstract says 22 layers | **Green** | GoogLeNet is supporting context only. |
| G7 | The ResNet paper says vanishing/exploding gradients had been largely addressed by normalized initialization and intermediate normalization layers, enabling tens-layer nets to start converging. | 2 | ResNet PDF p. 770, Section 1 | BatchNorm paper context (not page-anchored here) | **Green** | This is the correction to the legacy stub. |
| G8 | The degradation problem is that as depth increases, accuracy saturates and then degrades; the paper says this was not caused by overfitting and led to higher training error. | 2 | ResNet PDF p. 770, Section 1 and Figure 1 | ResNet PDF pp. 773-774, Fig. 4/Table 2 | **Green** | Draft as optimization degradation, not generic vanishing gradients. |
| G9 | The authors argue by construction that a deeper model could copy a shallower model and use identity mappings in added layers, so it should not have higher training error in principle. | 2, 3 | ResNet PDF p. 770, Section 1 | ResNet PDF p. 772, Section 3.1 | **Green** | Good explanatory bridge into residual learning. |
| G10 | Residual learning reformulates the desired mapping `H(x)` so stacked layers fit `F(x) := H(x) - x`, making the original mapping `F(x) + x`. | 3 | ResNet PDF p. 771, Section 1; p. 772, Section 3.1 | ResNet Figure 2 | **Green** | Can be explained pedagogically; do not invent analogies that imply source claims. |
| G11 | Shortcut connections skip one or more layers; identity shortcuts add no extra parameters or computational complexity and can be trained end-to-end with SGD/backprop. | 3, 4 | ResNet PDF p. 771, Section 1 | ResNet PDF p. 772, Section 3.2 | **Green** | The paper also says implementation can use common libraries such as Caffe without solver modification. |
| G12 | The residual block is formalized as `y = F(x, {Wi}) + x`; projection shortcuts are formalized as `y = F(x, {Wi}) + Wsx` when dimensions need matching. | 3 | ResNet PDF p. 772, Equations (1) and (2) | ResNet Figure 2 | **Green** | Equation anchors for prose-capacity layer 3. |
| G13 | A 34-layer plain baseline in ResNet used 3.6 billion FLOPs, about 18% of VGG-19's 19.6 billion FLOPs. | 4 | ResNet PDF p. 772, Section 3.3 | Table 1 p. 774 lists FLOPs for deeper variants | **Green** | Infrastructure/efficiency detail. |
| G14 | ImageNet ResNet implementation used scale augmentation, 224x224 crops, batch normalization after each convolution and before activation, He initialization, SGD mini-batch 256, weight decay 0.0001, momentum 0.9, and no dropout. | 4 | ResNet PDF p. 773, Section 3.4 | VGG PDF p. 5 for related training practice | **Green** | Do not infer hardware from this. |
| G15 | The ImageNet experiments trained on 1.28 million images, evaluated on 50k validation images, and reported final test-server results on 100k test images. | 4, 5 | ResNet PDF p. 773, Section 4.1 | AlexNet PDF p. 2 gives ILSVRC scale context | **Green** | Dataset-size anchor. |
| G16 | On ImageNet, the deeper 34-layer plain net had higher validation and training error than the 18-layer plain net. | 2 | ResNet PDF pp. 773-774, Section 4.1, Figure 4, Table 2 | ResNet PDF p. 770 Figure 1 for CIFAR analog | **Green** | Central scene anchor. |
| G17 | The authors argue the 34-layer plain-net difficulty is unlikely to be vanishing gradients because BN keeps forward signals nonzero and backward gradients had healthy norms. | 2 | ResNet PDF p. 774, Section 4.1 | G7 | **Green** | Must be included to prevent the old misframing. |
| G18 | Adding identity shortcuts to the 34-layer ResNet reverses the situation: the 34-layer ResNet beats the 18-layer ResNet and shows lower training error. | 3 | ResNet PDF p. 774, Table 2 and residual-net observations | ResNet PDF p. 775, Tables 3-4 | **Green** | This is the "it worked" moment. |
| G19 | Projection shortcuts were not essential for addressing degradation; the paper chooses economical options to reduce memory/time complexity and model size. | 3, 4 | ResNet PDF p. 775, "Identity vs. Projection Shortcuts" | ResNet Table 3 p. 775 | **Green** | Avoid overstating projection as the core trick. |
| G20 | For 50/101/152-layer ImageNet nets, ResNet uses bottleneck blocks because of training-time concerns; replacing identity shortcuts with projections in bottlenecks would double time complexity and model size. | 4 | ResNet PDF pp. 775-776, "Deeper Bottleneck Architectures" | ResNet Table 1 p. 774 | **Green** | Good infrastructure detail. |
| G21 | The 152-layer ResNet has 11.3 billion FLOPs, lower than VGG-16/19's 15.3/19.6 billion FLOPs, and the 50/101/152-layer ResNets did not show degradation in the ImageNet experiments. | 4 | ResNet PDF p. 776, "101-layer and 152-layer ResNets" | Table 1 p. 774; Tables 3-4 p. 775 | **Green** | Supports the "depth plus path plus efficiency" theme. |
| G22 | ResNet-152 achieved 4.49% single-model top-5 validation error, and a six-model ensemble achieved 3.57% top-5 test error and won ILSVRC 2015 classification. | 5 | ResNet PDF p. 776; Tables 4-5 on p. 775 | ResNet PDF p. 770 abstract | **Green** | This is better than the legacy "human-level" claim and is fully anchored. |
| G23 | On CIFAR-10, the 1202-layer ResNet trained without optimization difficulty and reached training error below 0.1%, but its 7.93% test error was worse than the 110-layer model, which the authors attribute to overfitting. | 5 | ResNet PDF p. 777, "Exploring Over 1000 layers"; Table 6/Figure 6 | ResNet PDF p. 777 | **Green** | Use for honest close. |
| G24 | Replacing VGG-16 with ResNet-101 in Faster R-CNN improved COCO's standard detection metric by 6.0 points, a 28% relative improvement, attributed to learned representations. | 5 | ResNet PDF p. 777, Section 4.3 and Table 8 | ResNet PDF p. 770 abstract | **Green** | Keep as downstream evidence; do not turn into a full COCO chapter. |
| G25 | The official ILSVRC2015 results page lists MSRA first by mean AP in object detection with provided training data, and MSRA entries at the top of classification+localization with classification error 0.03567. | 5 | ImageNet results page, "Task 1a" detection table and "Task 2a" localization/classification table | ResNet paper p. 777 says the team won several ILSVRC/COCO tracks | **Green** | Official HTML anchor; pure classification table not surfaced here. |
| G26 | The ResNet paper says the method won first places in ImageNet detection, ImageNet localization, COCO detection, and COCO segmentation in ILSVRC/COCO 2015. | 5 | ResNet PDF p. 777, Section 4.3 | ImageNet official results page for detection/localization | **Green** | COCO official page not fetched; paper is primary for COCO claim. |
| Y1 | The exact GPU model/count and wall-clock training time for the 152-layer ImageNet ResNet runs. | 4 | None found in ResNet paper | VGG/AlexNet hardware anchors show the era, not ResNet hardware | Yellow | Do not infer from VGG's four Titan Blacks or AlexNet's two GTX 580s. |
| Y2 | Highway Networks' causal influence on ResNet beyond being listed as concurrent related work. | 3 | ResNet PDF pp. 771-772 related-work section mentions Highway Networks | Highway paper not page-anchored here | Yellow | It is safe to mention as related/concurrent; unsafe to claim direct inspiration. |
| Y3 | Official ImageNet 2015 pure classification table independently confirming the 3.57% ResNet classification entry. | 5 | ResNet PDF p. 776 and p. 770 | ImageNet official results page fetched here did not expose pure classification table | Yellow | The ResNet paper's test-server claim is Green; this row is only about an official external table. |
| R1 | Which individual author first proposed the residual block or the exact internal development sequence inside Microsoft Research. | 3 | None | None | Red | Needs interview, lab notebook, or archival source. Do not invent. |
| R2 | ResNet's 3.57% result should be described as "human-level" or "superhuman." | 5 | None in ResNet paper | PReLU/BatchNorm human-rater sources not anchored here | Red | Use the anchored 3.57% ILSVRC result instead. |
| R3 | Lab drama, late-night training scenes, deadline pressure, or naming anecdotes around "ResNet." | 3-5 | None | None | Red | No archival/interview evidence in this contract. |

## Page Anchor Worklist

### Done

- ResNet CVPR/arXiv PDF: degradation, residual mapping, shortcuts, equations, ImageNet implementation, ImageNet results, CIFAR-10 1202-layer analysis, COCO/object-detection gains.
- AlexNet NeurIPS PDF: ImageNet scale, eight-layer architecture, two-GPU training, training time.
- VGG arXiv/ICLR PDF: 16-19 layer depth, 3x3 filters, multi-GPU/Titan Black training.
- ImageNet official ILSVRC2015 results page: MSRA detection/localization standings.

### Still Useful

- Highway Networks paper for a precise related-work note.
- Batch Normalization paper if the prose needs more detail on why "vanishing gradients" is the wrong shorthand.
- PReLU paper only if the human-rater comparison is revived.
- Oral histories or interviews with He/Zhang/Ren/Sun for internal development process and training infrastructure.
