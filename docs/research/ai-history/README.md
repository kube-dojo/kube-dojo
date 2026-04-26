# Epic: AI History book — Infrastructure-history of AI

## Angle
Chip Wars-style narrative history of AI — focused on the infrastructure that made each era possible (compute, data, networks, organizations), not just algorithm history.

## Workflow (lock-step, non-negotiable)
epic -> plan -> research wiki populated -> chapter contract locked -> outline review -> write -> cross-family review -> ship

## Chapters and ownership
| # | Chapter | Owner | Reviewer (cross-family) |
|---|---|---|---|
| 1 | The Dream Before the Machine (Cybernetics -> Dartmouth) | Gemini | Codex |
| 2 | The Summer AI Named Itself (Dartmouth + Cold War) | Claude | Gemini |
| 3 | The Perceptron and the First Hype Cycle | Claude | Gemini |
| 4 | Rules, Experts, and the Knowledge Bottleneck | Claude | Gemini |
| 5 | The Statistical Underground | Codex | Claude |
| 6 | Data Becomes Infrastructure (ImageNet) | Gemini | Codex |
| 7 | The GPU Coup (CUDA / AlexNet) | Codex | Claude |
| 8 | Attention, Scale, and the Language Turn | Gemini | Codex |
| 9 | The Product Shock (GPT-2 -> ChatGPT) | Claude | Gemini |
| 10 | The New Industrial Stack (K8s, inference economics, regulation) | Codex | Claude |

## Sourcing standard
- 2-3 independent sources per scene-level passage
- >= 1 primary (paper / memo / transcript / oral history)
- >= 1 high-quality secondary (contemporary tech journalism or verified retrospective)
- No invented dialogue or internal states
- Verification colors: Green (>= 2 independent confirmations), Yellow (1 source, plausible), Red (uncited / single source / disputed)

## Drafting Guidelines (The Golden Rules)
To ensure the book is both historically rigorous and highly engaging, all authors must adhere to the following when writing prose:
1. **The "Why" is Hardware:** Every algorithm introduced must explicitly answer what physical hardware limitation it overcame, or what hardware breakthrough made it possible. 
2. **Narrative Arcs over Textbooks:** Use scene-setting to make the infrastructural challenges feel visceral. Citations should anchor facts without interrupting the thriller-like flow (think *Chip Wars*).
3. **Adversarial Review is Law:** No chapter is final without cross-family review. The reviewer will reject prose that relies on uncited claims, invents internal monologues, or forgets the infrastructure thesis.
4. **Verified Reality over Myth:** Avoid mythologizing figures. Focus on the actual, often fractured historical reality (e.g., Krizhevsky's engineering feats, the tedious reality of Dartmouth). Check "vital status" terms carefully.
5. **Academic but Accessible:** Prose must pass quality pipelines and semantic linters. Maintain a C-level mastery tone—accessible but free of "semantic Surzhyk" or colloquial fluff.

## Output spec per chapter
- **Length:** ~1,800 to 2,000 words of narrative prose. This matches the density of *Chip War* chapters (which average ~1,850 words) and ensures we easily pass the KubeDojo quality pipeline's density gate (`prose_words >= 1500`, `w/ln >= 18`, `wpp >= 22`). Do not mistake the original "1500 lines" typo for a directive to write 27,000 words.
- **Location:** Live in `src/content/docs/ai-history/`
- **Routing:** Public-facing route under the top-level "AI History" tab in `astro.config.mjs`.
