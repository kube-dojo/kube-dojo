# Infrastructure Log: Chapter 45 - Generative Adversarial Networks

## Scene 1 - Montreal Spark

- **Institutional base:** University of Montreal / Montreal deep learning group. Anchored by Goodfellow et al. 2014 PDF p.1 author block and footnotes.
- **Local scene anchor:** Les Trois Brasseurs appears in the paper acknowledgments on p.8 and in the later MIT Technology Review profile. This supports color, not detailed reconstruction.

## Scene 2 - The Game on One Page

- **Software/algorithmic constraint:** The original formulation depends on differentiable generator and discriminator functions, stochastic gradient updates, backpropagation, dropout, and forward propagation. Anchored by Goodfellow et al. 2014 pp.1-3.
- **Computational advantage claimed:** No Markov chains or unrolled approximate inference networks during training or generation. Anchored by Goodfellow et al. 2014 pp.1-2 and Goodfellow 2016 tutorial pp.15-17.

## Scene 3 - Why This Was Different

- **Generative-model bottleneck:** Earlier deep generative approaches often required intractable likelihood approximations, variational bounds, or Markov chains. Anchored by Goodfellow et al. 2014 pp.1-2 and Goodfellow 2016 tutorial taxonomy pp.10-17.
- **New cost:** The computational simplification came with a training-control problem: finding a Nash equilibrium and keeping generator/discriminator updates synchronized. Anchored by Goodfellow 2016 tutorial p.17 and Goodfellow et al. 2014 p.6.

## Scene 4 - First Images and Instability

- **Datasets:** MNIST, Toronto Face Database, and CIFAR-10. Anchored by Goodfellow et al. 2014 p.6.
- **Metrics:** Gaussian Parzen-window log-likelihood estimates, with the paper warning of high variance and poor high-dimensional behavior. Anchored by Goodfellow et al. 2014 p.6.
- **Code stack:** Pylearn2 and Theano are thanked in the paper acknowledgments, including a note that Frederic Bastien rushed a Theano feature. Anchored by Goodfellow et al. 2014 p.8.
- **Compute support:** CIFAR, Canada Research Chairs, Compute Canada, and Calcul Quebec are acknowledged. Anchored by Goodfellow et al. 2014 p.8.
- **Instability:** Synchronization problems and mode collapse/"Helvetica scenario" are identified in the 2014 paper and expanded in Goodfellow 2016 tutorial pp.34-35.

## Scene 5 - From DCGAN to StyleGAN Faces

- **DCGAN stack:** Convolutional architecture constraints; Adam optimizer in Goodfellow tutorial's DCGAN summary; NVIDIA Titan-X GPU donation in DCGAN acknowledgments. Anchored by DCGAN PDF pp.1, 11 and Goodfellow 2016 tutorial p.26.
- **Progressive GAN stack:** Official README says there are TensorFlow and original Theano versions, recommends one or more high-end NVIDIA Pascal/Volta GPUs with 16GB DRAM and DGX-1 with 8 Tesla V100 GPUs, and lists training times from 2 days on 8 V100s to weeks/months on fewer GPUs. Anchored by `tkarras/progressive_growing_of_gans` README sections Versions, System requirements, Training networks.
- **StyleGAN stack:** Official README specifies TensorFlow 1.10+, NVIDIA GPUs with at least 11GB DRAM, DGX-1/8 V100 recommendation, FFHQ 1024x1024 pre-trained network, and quality/disentanglement metrics using Inception-v3, VGG-16/LPIPS, and attribute classifiers. Anchored by `NVlabs/stylegan` README sections System requirements, Using pre-trained networks, Evaluating quality and disentanglement.
