# Infrastructure Log: Chapter 61
# Infrastructure Log: Chapter 61 - The Physics of Scale

## Systems To Track

- **Pipeline parallelism:** layer partitioning, micro-batches, synchronous update semantics, rematerialization, bubble overhead, load balancing.
- **Tensor parallelism:** intra-layer matrix partitioning, self-attention/MLP splits, all-reduce placement, keeping GPUs compute-bound.
- **Data parallelism:** model replicas, gradient synchronization, per-device batch-size limits, communication cost.
- **Optimizer memory:** Adam optimizer states, gradients, parameters, activation memory, temporary buffers, fragmentation, ZeRO partitioning stages.
- **Topology:** NVLink/intra-node links for tensor parallelism, inter-node links for pipeline/data parallelism, bisection bandwidth.
- **TPU-scale training:** Pathways, TPU v4 Pods, sharded data parallelism, model FLOPs utilization.

## Metrics And Numbers Anchored

- GPipe: 6B-parameter multilingual Transformer example; bubble overhead depends on micro-batches vs partitions.
- Megatron 2019: 8.3B Transformer language model; 512 GPUs; up to 76% scaling efficiency reported in the paper.
- ZeRO: staged memory reductions for optimizer states, gradients, and parameters; trillion-parameter analysis; 100B/170B evaluation claims in paper context.
- Megatron 2021: 1T-parameter iteration; 3072 GPUs; 502 petaFLOP/s; topology-specific bandwidth discussion.
- PaLM: 540B parameters; 6144 TPU v4 chips; two TPU v4 Pods; 46.2% model FLOPs utilization.
- Chinchilla: 70B parameters, 1.4T tokens, same compute budget as Gopher.

## Boundary

This chapter is training-scale mechanics. Serving throughput, KV cache, batching,
PagedAttention, and vLLM belong in Ch63. Power grids, chip export controls, and
datacenter capex belong in Ch70-Ch72.
