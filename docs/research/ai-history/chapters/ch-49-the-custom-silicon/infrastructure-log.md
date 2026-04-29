# Infrastructure Log: Chapter 49 - The Custom Silicon

## Scene 1 - The Projection That Changed the Hardware Question

- **Workload pressure:** DNN speech recognition for voice search; three minutes per day per user was projected to require doubling datacenter capacity if served with conventional CPUs. Anchor: Jouppi et al. 2017, p.2.
- **Hardware alternatives:** GPUs, FPGAs, and ASICs had been discussed as early as 2006. Anchor: Jouppi et al. 2017, p.2.
- **Strategic split:** Google bought off-the-shelf GPUs for training and pursued a custom ASIC for inference. Anchor: Jouppi et al. 2017, p.2.

## Scene 2 - A Card Built for Existing Racks

- **Deployment model:** TPU v1 deployed in Google datacenters since 2015; public announcement in May 2016 said TPUs had been running internally for more than a year. Anchors: Jouppi et al. 2017, p.1; Google Cloud 2016 announcement.
- **Server integration:** Coprocessor on PCIe I/O bus; host sends TPU instructions; Google Cloud explainer says card fit into an SATA hard-disk slot. Anchors: Jouppi et al. 2017, p.2; Google Cloud 2017 "The road to TPUs."
- **Software stack:** TensorFlow compatibility and a TPU software stack split between user-space and kernel drivers. Anchor: Jouppi et al. 2017, p.4.

## Scene 3 - The Systolic Heart

- **Matrix unit:** 256x256 MAC array, 65,536 8-bit MACs, one 256-element partial sum per clock cycle. Anchor: Jouppi et al. 2017, p.3.
- **Memory:** 24 MiB Unified Buffer, 4 MiB accumulators, 8 GiB Weight Memory for read-only inference weights. Anchor: Jouppi et al. 2017, p.3.
- **Instruction set:** About a dozen CISC-style instructions, with key operations for host memory, weight reads, MatrixMultiply/Convolve, Activate, and host writeback. Anchor: Jouppi et al. 2017, p.3.
- **Dataflow:** Systolic wavefront reduces repeated buffer access by moving activations and weights through the array. Anchor: Jouppi et al. 2017, p.4; Google Cloud 2017 "The heart of the TPU: A systolic array."

## Scene 4 - The Benchmark Is a Business Argument

- **Benchmarks:** Six NN applications represent 95% of TPU datacenter inference workload in July 2016. Anchor: Jouppi et al. 2017, p.2, Table 1.
- **Baselines:** Intel Haswell server CPU and Nvidia K80 GPU, contemporaries deployed in the same datacenters. Anchor: Jouppi et al. 2017, p.1 and comparison sections.
- **Result envelope:** 15x-30x faster than contemporary CPU/GPU baselines; 30x-80x TOPS/Watt improvement. Anchor: Jouppi et al. 2017, p.1-p.2.
- **Latency constraint:** MLP0 Table 4: 7 ms longest allowable 99th-percentile response time; TPU at 225,000 IPS and 7.0 ms. Anchor: Jouppi et al. 2017, p.8.
- **Limits:** Several workloads were memory-bandwidth limited; the paper models a hypothetical GDDR5-memory variant. Anchor: Jouppi et al. 2017, p.2 and p.12.

## Scene 5 - From Internal ASIC to Cloud Primitive

- **Second-generation Cloud TPU:** May 2017 announcement says second-generation TPUs could train and run ML models; each device up to 180 teraflops. Anchor: Dean and Hoelzle, Google Cloud 2017.
- **Pods:** A TPU pod contains 64 second-generation TPUs and up to 11.5 petaflops. Anchor: Dean and Hoelzle, Google Cloud 2017.
- **Cloud access:** Cloud TPUs via Google Compute Engine; users could choose CPUs, Nvidia GPUs, or Cloud TPUs. Anchor: Dean and Hoelzle, "Introducing Cloud TPUs."
- **Research access:** 1,000 Cloud TPUs promised for qualified researchers through TensorFlow Research Cloud. Anchor: Dean and Hoelzle, "Introducing the TensorFlow Research Cloud."
- **Architecture frame:** Hennessy and Patterson later present TPU v1 as an example of the domain-specific-architecture opportunity after slowing general-purpose performance gains. Anchor: CACM 2019 sections.
