# Chapter 9: The Product Shock (GPT-2 -> ChatGPT)

## Thesis
The transition from GPT-2 to ChatGPT was the moment AI shifted from a backend infrastructure component to an interactive consumer product layer. This required a new infrastructural paradigm: RLHF (Reinforcement Learning from Human Feedback) served as an alignment infrastructure, turning stochastic text generators into steerable, dialogue-based operating systems.

## Scope
- IN SCOPE: OpenAI's development of the GPT series, the shift from open-source release (GPT-2) to API-gated access (GPT-3), the realization of few-shot learning, and the implementation of RLHF (InstructGPT/ChatGPT).
- OUT OF SCOPE: The underlying Transformer architecture (belongs to Chapter 8); the macroeconomic supply chain of GPUs (belongs to Chapter 10).

## Scenes Outline
1. **The API Moat (GPT-3):** OpenAI trains GPT-3 on a massive Microsoft Azure cluster (10,000 GPUs). Recognizing the dual-use danger (and the commercial value) of extreme scale, they abandon the open-source model of GPT-2. AI becomes cloud infrastructure: accessed via API, completely divorcing the user from the hardware.
2. **The Alignment Problem:** GPT-3 is powerful but unpredictable. It acts like an autocomplete, not an assistant. The realization that raw scale is not a product.
3. **The RLHF Infrastructure (ChatGPT):** OpenAI employs armies of human labelers to rank model outputs, creating a reward model (InstructGPT). This Reinforcement Learning from Human Feedback turns the model into a conversational agent. The launch of ChatGPT in late 2022 initiates the fastest consumer product adoption in history, turning the LLM into a universal interface.