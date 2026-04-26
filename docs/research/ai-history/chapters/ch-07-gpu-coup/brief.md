# Chapter 7: The GPU Coup (CUDA / AlexNet)

## Thesis
The "Deep Learning Revolution" of 2012 was primarily a hardware coup. The algorithmic concepts behind convolutional neural networks (CNNs) had existed since the 1980s, but they remained computationally intractable until researchers realized they could repurpose consumer gaming graphics cards (GPUs) as massive, cheap parallel supercomputers, facilitated by Nvidia's CUDA platform.

## Scope
- IN SCOPE: The release of Nvidia's CUDA (2006), the infrastructural hacking required to train neural networks on GPUs, Alex Krizhevsky and Ilya Sutskever's creation of AlexNet (using two GTX 580 GPUs), and the 2012 ImageNet victory.
- OUT OF SCOPE: The creation of the ImageNet dataset itself (belongs to Chapter 6); the later shift to TPUs/Transformers for NLP (belongs to Chapter 8).

## Scenes Outline
1. **The Graphics Hack (2006-2009):** The introduction of Nvidia's Compute Unified Device Architecture (CUDA) in 2006. Prior to CUDA, using a GPU for general-purpose math meant disguising the math as graphics pixels. CUDA provided a C-like API, turning every consumer gaming PC into a potential parallel supercomputer for matrix math.
2. **The GTX 580 Sweatshop (2011-2012):** Alex Krizhevsky and Ilya Sutskever at the University of Toronto. They realize that training a deep CNN on ImageNet requires more memory than a single GPU possesses. The intense infrastructural engineering required to split the network across two consumer-grade Nvidia GTX 580 GPUs, dealing with cooling, memory bandwidth, and custom CUDA kernels.
3. **The 2012 ImageNet Smash:** The ILSVRC 2012 competition. AlexNet destroys the traditional computer vision establishment, halving the error rate. The sudden realization across the academic world that deep learning + gaming hardware is the new undisputed paradigm.