# Sources: Chapter 45 - Generative Adversarial Networks

## Verification Key

- **Green**: claim has a verified page, section, DOI, or stable source anchor.
- **Yellow**: source exists, but the exact claim needs a stronger page/section anchor or primary confirmation.
- **Red**: do not draft as fact yet.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Ian J. Goodfellow et al., "Generative Adversarial Nets," *Advances in Neural Information Processing Systems 27*, 2014. URL: https://proceedings.nips.cc/paper_files/paper/2014/file/f033ed80deb0234979a61f95710dbe25-Paper.pdf | Core source for the 2014 formulation, analogy, minimax objective, experiments, infrastructure acknowledgments, and limitations. | **Green**. Web PDF extraction verified pages 1-8. |
| Ian Goodfellow, "NIPS 2016 Tutorial: Generative Adversarial Networks," arXiv:1701.00160v4, April 3, 2017; Stanford course mirror PDF. URL: https://graphics.stanford.edu/courses/cs348n-22-winter/PapersReferenced/Tutorial%20Goodfellow%20Generative%20Adversarial%20Networks%201701.00160.pdf | Retrospective technical tutorial for why generative modeling mattered, GAN taxonomy, comparison to other generative models, and mode collapse/non-convergence. | **Green**. Web PDF extraction verified pages 2-17, 26-37. |
| Alec Radford, Luke Metz, Soumith Chintala, "Unsupervised Representation Learning with Deep Convolutional Generative Adversarial Networks," arXiv:1511.06434v2, January 7, 2016. URL: https://arxiv.org/pdf/1511.06434 | DCGAN bridge: convolutional architecture constraints, prior instability, latent-vector arithmetic, and Titan-X GPU acknowledgment. | **Green**. Web PDF extraction verified pages 1-11. |
| Tero Karras, Timo Aila, Samuli Laine, Jaakko Lehtinen, "Progressive Growing of GANs for Improved Quality, Stability, and Variation," NVIDIA Research page. URL: https://research.nvidia.com/publication/2018-04_progressive-growing-gans-improved-quality-stability-and-variation | Official abstract, date, venue, and 1024x1024 CelebA-HQ claim. | **Green** for NVIDIA page sections Abstract, Publication Date, Published In. |
| `tkarras/progressive_growing_of_gans`, official TensorFlow implementation README. URL: https://github.com/tkarras/progressive_growing_of_gans | Infrastructure anchor for TensorFlow/Theano versions, GPU requirements, DGX-1 recommendation, and training-time estimates. | **Green** for README sections Versions, System requirements, Training networks. |
| Tero Karras, Samuli Laine, Timo Aila, "A Style-Based Generator Architecture for Generative Adversarial Networks," NVIDIA Research page. URL: https://research.nvidia.com/publication/2019-06_style-based-generator-architecture-generative-adversarial-networks | Official abstract, CVPR 2019 publication date, and StyleGAN claims about style/noise separation and FFHQ. | **Green** for NVIDIA page sections Abstract, Publication Date, Published In. |
| `NVlabs/stylegan`, official TensorFlow implementation README. URL: https://github.com/NVlabs/stylegan | Infrastructure anchor for StyleGAN system requirements, pre-trained FFHQ network, 1024x1024 output, training-time table, and generator use. | **Green** for README sections System requirements, Using pre-trained networks, Training networks, Evaluating quality and disentanglement. |
| Jurgen Schmidhuber, "Learning Factorial Codes by Predictability Minimization," *Neural Computation* 4(6):863-879, 1992. DOI: 10.1162/neco.1992.4.6.863; author page: https://people.idsia.ch/~juergen/factorial/ | Priority-boundary source for predictability minimization's opposing predictor/representation forces. | **Green** for DOI, bibliographic pages, and author-page abstract. |

## Secondary Sources

| Source | Use | Verification |
|---|---|---|
| Martin Giles, "The GANfather: The man who's given machines the gift of imagination," *MIT Technology Review*, February 21, 2018. Original site blocked by robots in this environment; mirrored copy used: https://buzzpost.com/2018/02/21/the-ganfather-the-man-whos-given-machines-the-gift-of-imagination/ | Secondary narrative source for Les 3 Brasseurs, friends asking Goodfellow about a photo-generating project, same-night coding, "worked the first time," later Google Brain role, and risk framing. | **Green** only for article-section anchoring as a secondary profile. Do not use as a primary transcript. |
| NeurIPS 2016 tutorial page, "Generative Adversarial Networks," Ian Goodfellow. URL: https://nips.cc/virtual/2016/tutorial/6202 | Confirms tutorial venue/year and gives concise abstract of GANs as realistic-sample generative models. | **Green** for page metadata and abstract. |
| NVIDIA Research StyleGAN2 page. URL: https://research.nvidia.com/index.php/publication/2020-06_analyzing-and-improving-image-quality-stylegan | Context only for later artifact fixes and the fact that StyleGAN2 revised StyleGAN. | Yellow. Useful for boundary note; not needed for main chapter. |

## Scene-Level Claim Table

| ID | Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|---|
| G1 | Goodfellow et al. 2014 was authored by Ian Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, and Yoshua Bengio at/around Universite de Montreal, with footnotes noting Goodfellow did the work as a UdeM student. | 1 | Goodfellow et al. 2014 PDF p.1 | NeurIPS paper page metadata | **Green** | Use "Goodfellow and collaborators," not solo-inventor framing except when discussing the later profile's origin story. |
| G2 | A later MIT Technology Review profile reports the idea emerging during a 2014 night at Les 3 Brasseurs in Montreal and says Goodfellow coded a first version that night. | 1 | MIT Technology Review profile mirror, opening section before "The GANfather, Part II" | Goodfellow et al. 2014 PDF p.8 thanks Les Trois Brasseurs | **Green** for the attributed profile report | Do not write dialogue; the exact private sequence is tracked separately as Y1. |
| G3 | The 2014 paper acknowledges Les Trois Brasseurs for "stimulating our creativity." | 1 | Goodfellow et al. 2014 PDF p.8 Acknowledgments | MIT Technology Review profile mirror | **Green** | Short quote only if needed. |
| G4 | The 2014 paper proposes a framework for estimating generative models by training a generator G and discriminator D simultaneously. | 2 | Goodfellow et al. 2014 PDF p.1 Abstract | Goodfellow 2016 tutorial PDF p.17 | **Green** | Core formulation. |
| G5 | The 2014 paper states the framework corresponds to a minimax two-player game. | 2 | Goodfellow et al. 2014 PDF p.1 Abstract and p.3 Eq. 1 | Goodfellow 2016 tutorial PDF pp.17-19 | **Green** | Keep equation accessible. |
| G6 | The original paper uses a counterfeiter/police analogy for generator and discriminator. | 2 | Goodfellow et al. 2014 PDF p.1 Introduction | Goodfellow 2016 tutorial PDF p.17 | **Green** | This is the chapter's safest analogy. |
| G7 | In the non-parametric theoretical result, the global optimum is achieved iff the model distribution equals the data distribution, with the discriminator outputting 1/2. | 2 | Goodfellow et al. 2014 PDF pp.4-5, Proposition 1/Theorem 1 | Goodfellow 2016 tutorial PDF p.19 | **Green** | Explain assumptions; do not imply practical convergence is guaranteed. |
| G8 | Goodfellow et al. frame deep generative models before GANs as hampered by intractable probabilistic computations and difficulty using piecewise-linear units. | 3 | Goodfellow et al. 2014 PDF p.1 Introduction | Goodfellow 2016 tutorial PDF pp.10-16 taxonomy | **Green** | Good bridge from Ch44 latent-space setup. |
| G9 | GANs train with backpropagation and sample by forward propagation without approximate inference or Markov chains. | 3 | Goodfellow et al. 2014 PDF pp.1-2 | Goodfellow 2016 tutorial PDF pp.15-17 | **Green** | Avoid saying "no approximation anywhere"; the point is no MCMC/variational machinery in this formulation. |
| G10 | Goodfellow 2016 presents GANs as implicit density models that can generate samples in a single step and in parallel. | 3 | Goodfellow 2016 tutorial PDF pp.16-17 | Goodfellow et al. 2014 Table 2, PDF p.8 | **Green** | Useful infrastructure/computation angle. |
| G11 | Goodfellow 2016 says GANs introduced a new disadvantage: training requires finding a Nash equilibrium, harder than optimizing an objective function. | 3 | Goodfellow 2016 tutorial PDF p.17 | Goodfellow et al. 2014 PDF p.6 synchronization warning | **Green** | Important caveat. |
| G12 | Goodfellow et al. identify predictability minimization as the most relevant prior work with competing networks and list three differences from GANs. | 3 | Goodfellow et al. 2014 PDF pp.2-3 | Schmidhuber 1992 DOI/author-page abstract | **Green** | Priority conflict bounded here. |
| G13 | The 2014 experiments trained adversarial nets on MNIST, Toronto Face Database, and CIFAR-10. | 4 | Goodfellow et al. 2014 PDF p.6 Experiments | Goodfellow 2016 tutorial references original paper | **Green** | Do not imply large-scale photorealism. |
| G14 | The 2014 paper used Gaussian Parzen-window log-likelihood estimates and warned this evaluation had high variance and poor high-dimensional behavior. | 4 | Goodfellow et al. 2014 PDF p.6 Experiments | Goodfellow 2016 tutorial broader evaluation discussion | **Green** | Prevents overclaiming metrics. |
| G15 | The 2014 paper says generated samples were not claimed to be better than existing methods, only competitive enough to highlight the framework's potential. | 4 | Goodfellow et al. 2014 PDF p.6 Experiments | DCGAN p.2 later describes early GAN images as noisy/incomprehensible | **Green** | Key honesty claim. |
| G16 | The 2014 paper identifies discriminator/generator synchronization and "Helvetica scenario" collapse as disadvantages. | 4 | Goodfellow et al. 2014 PDF pp.6, 8 Table 2 | Goodfellow 2016 tutorial PDF pp.34-35 | **Green** | Use "mode collapse" after defining it. |
| G17 | The 2014 paper acknowledges Pylearn2, Theano, Compute Canada, Calcul Quebec, CIFAR, and Canada Research Chairs. | 4 | Goodfellow et al. 2014 PDF p.8 Acknowledgments | Theano references in paper bibliography | **Green** | Infrastructure-log anchor. |
| G18 | DCGAN introduced a class of CNN-based GANs with architectural constraints intended to make training stable in most settings. | 5 | Radford/Metz/Chintala 2015 PDF p.1 | Goodfellow 2016 tutorial PDF p.26 | **Green** | "Most settings" is the authors' scoped wording. |
| G19 | DCGAN notes GANs had been unstable and often produced nonsensical outputs before its architecture constraints. | 5 | DCGAN PDF p.1 Introduction | Goodfellow 2016 tutorial PDF pp.34-35 | **Green** | Good transition from instability scene. |
| G20 | DCGAN demonstrated latent-vector arithmetic and pose manipulation in generated faces. | 5 | DCGAN PDF pp.8-10, Figures 7-8 | Goodfellow 2016 tutorial PDF p.26 | **Green** | Phrase as demonstration, not proof of semantic understanding. |
| G21 | DCGAN thanks NVIDIA for donating a Titan-X GPU used in the work. | 5 | DCGAN PDF p.11 Acknowledgments | NVIDIA GPU ecosystem context in later GAN READMEs | **Green** | Infrastructure detail. |
| G22 | Progressive GAN's official NVIDIA abstract says progressive growing starts at low resolution, adds layers over training, stabilizes/speeds training, and enables 1024x1024 CelebA images. | 5 | NVIDIA Progressive GAN page, Abstract section | Official Progressive GAN GitHub README Abstract | **Green** | Use 1024x1024, not generic "all high-resolution images." |
| G23 | The official Progressive GAN README reports TensorFlow and Theano versions, recommends DGX-1 with 8 Tesla V100 GPUs, and gives CelebA-HQ training-time estimates from 2 days on 8 GPUs to weeks/months on fewer GPUs. | 5 | `tkarras/progressive_growing_of_gans` README, Versions/System requirements/Training networks | NVIDIA Progressive GAN page | **Green** | Strong infrastructure layer. |
| G24 | StyleGAN's official NVIDIA page says the architecture separates high-level attributes from stochastic variation, improves quality/interpolation/disentanglement metrics, and introduces FFHQ. | 5 | NVIDIA StyleGAN page, Abstract section | `NVlabs/stylegan` README Abstract | **Green** | Anchor for "faces that do not exist" without relying on the website `thispersondoesnotexist.com`. |
| G25 | The official StyleGAN README specifies TensorFlow 1.10+, high-end NVIDIA GPUs with at least 11GB DRAM, DGX-1/8 V100 recommendation, FFHQ 1024x1024 pretrained network, and 8-GPU training times. | 5 | `NVlabs/stylegan` README, System requirements/Using pre-trained networks/Training networks | NVIDIA StyleGAN page | **Green** | Infrastructure anchor for compute-intensive photorealism. |
| Y1 | Goodfellow's same-night code "worked the first time." | 1 | MIT Technology Review profile mirror, opening section | None primary located | Yellow | Draft only as "the profile reports"; do not make it a primary fact. |
| Y2 | The exact identities of all friends in the Les 3 Brasseurs conversation and the project they were proposing. | 1 | MIT Technology Review profile mirror | No primary transcript located | Yellow | Avoid naming unnamed participants. |
| Y3 | The first public demo chronology between initial private code, arXiv/NeurIPS submission, and later talks. | 1, 2 | Paper publication metadata only | Needs arXiv submission history and conference records | Yellow | Not necessary for current plan. |
| Y4 | Whether DCGAN was the single most important step between original GANs and ProGAN/StyleGAN. | 5 | DCGAN and Goodfellow 2016 support importance | Needs broader survey/citation analysis | Yellow | Use "a key step," not "the key step." |
| Y5 | The exact relationship between StyleGAN and `thispersondoesnotexist.com`. | 5 | No source in current anchor set | Popular knowledge, not anchored here | Yellow | Do not draft unless sourced. |
| R1 | Any invented dialogue at Les 3 Brasseurs. | 1 | None | None | Red | Prohibited. |
| R2 | Claim that GANs solved unsupervised learning or machine imagination. | All | None; sources contradict overbroad version | Goodfellow 2016 and later instability literature | Red | Use narrower thesis. |
| R3 | Claim that Goodfellow invented adversarial neural networks with no predecessors. | 3 | Contradicted by Goodfellow et al. 2014 pp.2-3 | Schmidhuber 1992 | Red | Use "modern GAN formulation." |

## Anchor Worklist

### Done

- Goodfellow et al. 2014 NeurIPS PDF: p.1 authors/abstract/analogy, p.3 minimax equation and Algorithm 1, pp.4-5 theoretical optimum, p.6 experiments/evaluation/limitations, p.8 acknowledgments and Table 2.
- Goodfellow 2016 tutorial PDF: pp.2-5 generative modeling motivation, pp.10-17 taxonomy and comparison, pp.17-19 GAN framework/Nash equilibrium, pp.26-27 DCGAN summary, pp.34-37 mode collapse/non-convergence.
- DCGAN PDF: p.1 abstract/contributions, p.2 prior image-generation limitations, pp.8-10 latent-vector arithmetic/pose, p.11 Titan-X acknowledgment.
- NVIDIA Progressive GAN page and official README: abstract/date/venue, versions, system requirements, training-time table.
- NVIDIA StyleGAN page and official README: abstract/date/venue, system requirements, FFHQ 1024x1024 pretrained networks, training/evaluation notes.
- Schmidhuber predictability-minimization DOI and author-page abstract.
- MIT Technology Review profile mirror for the Les 3 Brasseurs scene, kept as secondary.

### Still useful

- Original MIT Technology Review page capture, if accessible outside this sandbox, to replace the mirror.
- A Goodfellow talk transcript or oral-history interview that independently confirms the same-night coding story.
- ArXiv submission history / NeurIPS camera-ready dates if the prose wants a more precise publication chronology.
- A serious survey on GAN variants between 2014 and 2018, if the chapter needs to justify why DCGAN/ProGAN/StyleGAN are the selected path.

## Conflict Notes

- The chapter should credit the 2014 paper's full author list and not let the profile scene erase the collaboration.
- "Photorealistic human faces" belongs to the later NVIDIA arc. The 2014 paper's own language is cautious.
- "GANfather" is a profile headline, not the chapter's voice.
