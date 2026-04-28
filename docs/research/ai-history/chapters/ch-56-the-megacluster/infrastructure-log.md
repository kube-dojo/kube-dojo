# Infrastructure Log: Chapter 56 - The Megacluster

## Organizational Infrastructure

- **OpenAI LP:** Capped-profit hybrid announced March 11, 2019.
  - Purpose: increase ability to raise capital while serving OpenAI's mission.
  - Capital rationale: OpenAI said it would need billions of dollars for large-scale cloud compute, attracting/retaining talent, and building AI supercomputers.
  - Governance: OpenAI Nonprofit retained control; OpenAI LP's primary fiduciary obligation was to advance the OpenAI Charter; investor/employee returns were capped.
  - Constraint: Do not simplify this to "became a normal startup." The source emphasizes mission-first constraints and capped returns.

## Cloud / Partnership Infrastructure

- **Microsoft/OpenAI partnership:** Announced July 22, 2019.
  - Published investment: $1 billion from Microsoft.
  - Technical plan: jointly build new Azure AI supercomputing technologies.
  - Platform commitment: OpenAI would port services to Microsoft Azure.
  - Commercial commitment: Microsoft would become OpenAI's preferred partner for commercializing new AI technologies.
  - Constraint: Current sources do not support an exact allocation of the $1 billion between cash, cloud credits, compute, or other forms.

## Hardware Infrastructure

- **Azure supercomputer for OpenAI:** Announced May 19, 2020.
  - Microsoft description: one of the top five publicly disclosed supercomputers.
  - Relationship: developed in collaboration with and exclusively for OpenAI; hosted in Azure.
  - Published scale: more than 285,000 CPU cores, 10,000 GPUs, and 400 Gbps network connectivity for each GPU server.
  - Constraint: Current sources do not identify GPU model, interconnect vendor/technology, exact cost, data-center location, training duration, or GPT-3-specific use.

## Software / Platform Infrastructure

- **AI at Scale:** Microsoft's broader initiative for large AI models, optimization tools, and supercomputing resources through Azure AI services and GitHub.
- **Turing-NLG:** Microsoft Research's 17B-parameter language model, announced February 2020, useful as evidence that Microsoft was also building its own large-model capability.
- **DeepSpeed and ZeRO:** Microsoft-distributed training tooling discussed in the Turing-NLG post and the 2020 supercomputer feature. Safe use: explain model/data parallelism and the software side of training large models.
- **ONNX Runtime distributed training support:** Mentioned in the 2020 feature as part of Microsoft's platform/tooling story.

## Pedagogical Explanation Targets

- **Why 400 Gbps matters:** In distributed training, GPUs must exchange model updates and data shards. A slow network can turn expensive accelerators into idle hardware. Use this explanation without naming InfiniBand.
- **Why the cluster is more than hardware:** A usable frontier cluster needs cloud scheduling, storage, distributed training libraries, runtime optimization, networking, monitoring, and organizational access.
- **Why this chapter follows scaling laws:** If performance can be forecast against compute within empirical limits, the next question becomes who can buy, build, and operate enough compute.
