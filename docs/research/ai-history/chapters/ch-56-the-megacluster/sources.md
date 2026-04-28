# Sources: Chapter 56 - The Megacluster

## Verification Key

- Green: claim has direct primary evidence from a source with a section, date, or line-level web anchor.
- Yellow: claim is interpretive, sourced to company framing only, or requires careful wording.
- Red: claim should not be drafted unless new evidence is added.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Greg Brockman, Ilya Sutskever, OpenAI, "OpenAI LP," OpenAI, March 11, 2019. URL: https://openai.com/index/openai-lp/ | Core source for OpenAI's capped-profit structure, capital rationale, compute/talent/supercomputer needs, capped returns, and nonprofit control. | Green: announcement says OpenAI had experienced that dramatic AI systems used the most computational power, had decided to scale faster than planned, and would need to invest billions in large-scale cloud compute, talent, and AI supercomputers. It says OpenAI wanted more ability to raise capital while serving its mission, created OpenAI LP as a capped-profit hybrid, capped investor/employee returns, and kept OpenAI Nonprofit in control. |
| Microsoft, "OpenAI forms exclusive computing partnership with Microsoft to build new Azure AI supercomputing technologies," Microsoft Source, July 22, 2019. URL: https://news.microsoft.com/source/2019/07/22/openai-forms-exclusive-computing-partnership-with-microsoft-to-build-new-azure-ai-supercomputing-technologies/ | Core source for the 2019 partnership, $1 billion investment, Azure supercomputing plan, OpenAI services moving to Azure, and Microsoft preferred commercialization role. | Green: release headline and deck describe an exclusive computing partnership and a $1 billion Microsoft investment. The partnership bullet list says Microsoft and OpenAI would jointly build Azure AI supercomputing technologies, OpenAI would port services to Azure, and Microsoft would become OpenAI's preferred partner for commercializing new AI technologies. |
| Microsoft, "Microsoft announces new supercomputer, lays out vision for future AI work," Microsoft Source, May 19, 2020. URL: https://news.microsoft.com/source/features/ai/openai-azure-supercomputer/ | Core source for the OpenAI Azure supercomputer, published hardware scale, and platform strategy. | Green: feature says Microsoft built one of the top five publicly disclosed supercomputers, developed in collaboration with and exclusively for OpenAI, hosted in Azure, and designed for training large AI models. It gives more than 285,000 CPU cores, 10,000 GPUs, and 400 Gbps network connectivity for each GPU server. It also says Microsoft wanted large models, training tools, and supercomputing resources available through Azure AI services and GitHub. |
| Microsoft Research, "Turing-NLG: A 17-billion-parameter language model by Microsoft," February 13, 2020. URL: https://www.microsoft.com/en-us/research/blog/turing-nlg-a-17-billion-parameter-language-model-by-microsoft/ | Context source for Microsoft's own large-model work, DeepSpeed, ZeRO, and the need to parallelize large models across multiple GPUs. | Green/Yellow: post describes Turing-NLG as a 17B-parameter Microsoft language model, links its training to DeepSpeed and ZeRO, and explains that models above 1.3B parameters cannot fit on a single 32GB GPU and must be parallelized across multiple GPUs. Use as platform context, not as evidence about the OpenAI cluster itself. |

## Secondary / Context Sources

| Source | Use | Verification |
|---|---|---|
| Ron Miller, "Microsoft invests $1 billion in OpenAI," TechCrunch, July 22, 2019. URL: https://techcrunch.com/2019/07/22/microsoft-invests-1-billion-in-openai/ | Secondary confirmation that contemporary technology press understood the announcement as a $1 billion Microsoft investment and cloud partnership. | Yellow: useful for external framing, but do not use it to infer exact cash/cloud-credit allocation. |
| TechTarget, "Microsoft and OpenAI deal fuels AI products, services on Azure," July 2019. URL: https://www.techtarget.com/searchenterpriseai/news/252467178/Microsoft-and-OpenAI-deal-fuels-AI-products-services-on-Azure | Secondary context on enterprise/cloud implications of the partnership. | Yellow: use only for context if prose needs external reaction; primary claims should come from OpenAI and Microsoft. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| OpenAI said dramatic AI systems used large amounts of computational power and that it needed to invest billions of dollars in large-scale cloud compute, talent, and AI supercomputers. | Capital Problem | OpenAI LP announcement, opening paragraphs | Microsoft 2019 release later frames partnership as supercomputing foundation | Green | Safe replacement for "nonprofit could not afford it." |
| OpenAI LP was created as a capped-profit hybrid to raise capital while serving OpenAI's mission. | Capital Problem | OpenAI LP announcement, capped-profit explanation | N/A | Green | Keep governance details clear and concise. |
| OpenAI LP investor and employee returns were capped, excess returns belonged to OpenAI Nonprofit, and OpenAI Nonprofit retained control. | Capital Problem | OpenAI LP "mission comes first" section | N/A | Green | Useful for explaining why this was not a standard startup conversion. |
| Microsoft announced a $1 billion investment and exclusive computing partnership with OpenAI in July 2019. | Partnership | Microsoft 2019 release title and summary | TechCrunch 2019 | Green | Do not infer exact allocation between cash and credits. |
| Microsoft and OpenAI said they would jointly build Azure AI supercomputing technologies. | Partnership | Microsoft 2019 release bullet list | Microsoft 2020 supercomputer feature says partnership began in 2019 | Green | This sets up the 2020 machine. |
| OpenAI would port its services to Azure and use Azure to create new AI technologies, while Microsoft became the preferred partner for commercialization. | Partnership | Microsoft 2019 release bullet list | TechTarget/TechCrunch context | Green | Avoid claiming exclusivity beyond the source language. |
| Microsoft described the 2020 system as one of the top five publicly disclosed supercomputers, built in collaboration with and exclusively for OpenAI. | Machine | Microsoft 2020 feature opening paragraphs | 2019 release partnership plan | Green | "Publicly disclosed" matters; include it. |
| The 2020 OpenAI supercomputer had more than 285,000 CPU cores, 10,000 GPUs, and 400 Gbps network connectivity for each GPU server. | Machine | Microsoft 2020 hardware paragraph | N/A | Green | Do not add GPU model, cost, InfiniBand, or location without new sources. |
| Microsoft framed the OpenAI machine as a first step toward making large models, optimization tools, and supercomputing resources available through Azure AI services and GitHub. | Platform | Microsoft 2020 AI at Scale sections | Turing-NLG and DeepSpeed context | Green | Supports the "private cluster to platform" scene. |
| DeepSpeed and ONNX Runtime are part of Microsoft's distributed-training platform story around large models. | Platform | Microsoft 2020 feature; Microsoft Research Turing-NLG post | N/A | Green/Yellow | Use as software ecosystem context, not proof of OpenAI's internal training stack. |
| The Microsoft/OpenAI partnership changed frontier AI from a lab-scale research problem into a cloud-scale industrial systems problem. | Close | Synthesis from OpenAI LP, Microsoft 2019, Microsoft 2020 | Ch55 scaling-law context | Yellow | Interpretive thesis; keep grounded in the sourced infrastructure details. |

## Conflict Notes

- "Microsoft gave OpenAI $1B largely in Azure compute credits" is not supported by current sources. The safe claim is "a $1 billion investment" plus Azure partnership.
- "InfiniBand" is not supported by current sources. The safe claim is "400 Gbps network connectivity for each GPU server."
- "Sovereign-level capital expenditure" is not supported and belongs to later chapters if sourced.
- "OpenAI's nonprofit could not afford scaling" is too strong. The safe claim is OpenAI's own statement that it needed to raise capital and invest billions.
- "Scaling laws mathematically proved AGI" is false for this contract. Chapter 55 supports empirical language-model loss scaling with caveats.
- "Top five supercomputer" must be written as "top five publicly disclosed supercomputer" and attributed to Microsoft.

## Anchor Worklist

- OpenAI LP 2019: Done for compute/talent/supercomputer capital rationale, capped-profit structure, capped returns, nonprofit control, and mission-first governance.
- Microsoft 2019 partnership: Done for $1 billion investment, exclusive computing partnership, Azure supercomputing development, OpenAI porting services to Azure, and preferred commercialization partnership.
- Microsoft 2020 supercomputer: Done for top-five public claim, OpenAI exclusivity/collaboration, Azure hosting, 285,000+ CPU cores, 10,000 GPUs, 400 Gbps network connectivity per GPU server, Azure AI services/GitHub platform framing, DeepSpeed, and ONNX Runtime.
- Microsoft Research Turing-NLG: Done for 17B-parameter context, multi-GPU model parallelism, DeepSpeed, and ZeRO.
