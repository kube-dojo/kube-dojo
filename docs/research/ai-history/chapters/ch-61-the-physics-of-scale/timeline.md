# Timeline: Chapter 61 - The Physics of Scale

- **2019-03:** NVIDIA/Megatron-LM repository exists as ongoing research training Transformer models at scale.
- **2019-07:** GPipe arXiv v5 describes micro-batch pipeline parallelism and demonstrates scaling to large AmoebaNet and Transformer models.
- **2019-10 / 2020-03:** Megatron-LM paper presents intra-layer tensor model parallelism and reports an 8.3B Transformer language model on 512 GPUs.
- **2019-10 / 2020-05:** ZeRO paper develops optimizer-state, gradient, and parameter partitioning for memory-efficient training.
- **2020-01:** DeepSpeed repository is created; use as context for the ZeRO implementation ecosystem.
- **2021-04:** Megatron-LM GPU-cluster paper composes pipeline, tensor, and data parallelism and reports a 1T-parameter training iteration on 3072 GPUs.
- **2022-03:** Chinchilla paper argues compute-optimal training should scale parameters and training tokens together.
- **2022-04 / 2022-10:** PaLM paper reports training a 540B dense Transformer on 6144 TPU v4 chips using Pathways.
