# Scene Sketches: Chapter 45 - Generative Adversarial Networks

## Scene 1: The Montreal Spark

- **Action:** Open in Montreal, not as myth but as constrained memory: a later profile places Goodfellow at Les 3 Brasseurs in 2014, asked about a photo-generating project; the paper itself later thanks Les Trois Brasseurs. Then pull back to the verified author block: this becomes a University of Montreal collaboration, not a lone-genius fable.
- **Evidence anchors:** sources.md G1, G2, G3.
- **Prose density:** Brief, atmospheric, careful. The scene can set a hook but should not spend many words on invented private details.

## Scene 2: The Game on One Page

- **Action:** Put the reader inside the 2014 paper's compact move: train two networks at once. The generator pushes noise into samples; the discriminator judges data vs generated samples; the generator improves through the discriminator's signal. Use the paper's counterfeiter/police analogy, then show the minimax value function in words before naming the theoretical equilibrium.
- **Evidence anchors:** sources.md G4, G5, G6, G7.
- **Prose density:** Highest technical density. The reader should understand why the idea was elegant without drowning in notation.

## Scene 3: Why This Was Different

- **Action:** Step back from the analogy to the pre-GAN generative-model problem. Earlier deep generative models could generate or estimate densities, but often paid with Markov chains, variational approximations, or sequential generation costs. GANs avoided some of that machinery by becoming an implicit, one-step sample generator, but the price was game dynamics.
- **Evidence anchors:** sources.md G8, G9, G10, G11, G12.
- **Prose density:** Use Goodfellow 2016 as the explanatory spine. Include the predictability-minimization boundary in one disciplined paragraph.

## Scene 4: The First Images and the Instability Tax

- **Action:** Return to 2014 results: MNIST, TFD, CIFAR-10, actual samples, Parzen-window caveats, and the paper's cautious language. Then name the tax: discriminator/generator synchronization, Helvetica scenario, non-convergence, and mode collapse. The scene should feel like an engineering tradeoff, not a triumph montage.
- **Evidence anchors:** sources.md G13, G14, G15, G16, G17.
- **Prose density:** Medium-high. Pair the math with infrastructure: Theano, Pylearn2, Compute Canada, Calcul Quebec.

## Scene 5: From DCGAN to StyleGAN Faces

- **Action:** Follow the visual ramp. DCGAN applies convolutional constraints and demonstrates latent arithmetic; Progressive GAN grows generator and discriminator resolution by resolution until 1024x1024 CelebA-HQ; StyleGAN adds style/noise controls and FFHQ. Close with the infrastructure behind the apparent magic: Titan-X, DGX-1, V100s, TensorFlow/Theano, TFRecords, pre-trained pickles, and weeks of training on high-end GPUs.
- **Evidence anchors:** sources.md G18, G19, G20, G21, G22, G23, G24, G25.
- **Prose density:** Broad but bounded. This is the visual payoff, but avoid implying every later synthetic-media tool was a GAN or that diffusion did not later change the story.
