# Timeline: Chapter 49 - The Custom Silicon

- **2006:** Google discusses whether GPUs, FPGAs, or custom ASICs should be deployed in its datacenters for special hardware acceleration; the idea is not yet compelling because few applications justify dedicated hardware. Source: Jouppi et al. 2017, p.2.
- **2013:** The hardware question changes when a projection says three minutes per day of voice search using DNN speech recognition would require Google to double datacenter capacity if served with conventional CPUs. Source: Jouppi et al. 2017, p.2; Google Cloud 2017 "The road to TPUs."
- **2013-2014:** Google starts a high-priority custom ASIC project for inference, buys off-the-shelf GPUs for training, and sets a 10x cost-performance goal over GPUs. Source: Jouppi et al. 2017, p.2.
- **2015:** TPU v1 is deployed in Google datacenters for neural-network inference. Source: Jouppi et al. 2017, p.1 abstract.
- **May 19, 2016:** Google publicly announces the Tensor Processing Unit as a custom ASIC for machine learning, tailored for TensorFlow, already running in datacenters for more than a year. Source: Norm Jouppi, Google Cloud Blog.
- **March 2016:** AlphaGo's matches against Lee Sedol use TPUs according to Google's 2016 announcement. Source: Norm Jouppi, Google Cloud Blog. Note: the chapter should not retell AlphaGo beyond this infrastructure fact.
- **April 16, 2017:** The TPU performance paper is submitted to arXiv. Source: arXiv:1704.04760 metadata.
- **May 12, 2017:** Google publishes a public technical explainer for TPU v1, including quantization, CISC instructions, systolic arrays, and performance-per-watt framing. Source: Sato and Young, Google Cloud Blog.
- **May 18, 2017:** Google announces second-generation Cloud TPUs for Google Cloud, including training plus inference, TPU pods, and TensorFlow Research Cloud. Source: Dean and Hoelzle, Google Cloud Blog.
- **June 24-28, 2017:** The TPU v1 paper appears at ISCA 2017 in Toronto. Source: Jouppi et al. 2017 arXiv/ACM metadata.
- **2019:** Hennessy and Patterson use TPU v1 as a public example of the domain-specific-architecture turn in computer architecture. Source: CACM "A New Golden Age for Computer Architecture."
