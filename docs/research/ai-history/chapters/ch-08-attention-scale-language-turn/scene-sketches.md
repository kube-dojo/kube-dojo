# Scene Sketches: Chapter 8

## Scene 1: The Sequential Traffic Jam
- **Setting:** Google Brain, circa 2015-2016.
- **Action:** Researchers are trying to improve translation. They are feeding massive datasets into LSTMs, but the training takes weeks. You can buy 1,000 GPUs, but because the algorithm reads words one by one, 999 GPUs sit idle waiting for the 1st one to finish the previous word.
- **Citation Anchor:** Sutskever (2014), MIT Tech Review (2024).
- **Infrastructural Point:** The algorithm is fundamentally hostile to the hardware it runs on.

## Scene 2: Designing for Matrix Math
- **Setting:** Google, 2017.
- **Action:** Vaswani, Shazeer, and the team realize that "attention" doesn't just improve context; it can replace the sequence entirely. By turning the sentence into a giant matrix multiplication, the math perfectly aligns with what TPUs do best.
- **Citation Anchor:** Vaswani (2017), Jouppi (2017).
- **Infrastructural Point:** The Transformer wasn't just a linguistic breakthrough; it was a masterclass in hardware-software co-design.

## Scene 3: The Scale-Up
- **Setting:** 2018-2020, the release of BERT and GPT.
- **Action:** With the sequential bottleneck removed, researchers realize they don't need to be clever anymore; they just need more compute. The race begins to build massive clusters and scrape the internet, giving birth to the modern LLM.
- **Citation Anchor:** Devlin (2018), Kaplan (2020).
- **Infrastructural Point:** Parallelization creates an insatiable appetite for data and compute, defining the modern AI industry.