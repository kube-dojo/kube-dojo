# Sources: Chapter 17 - The Perceptron's Fall

## Source Table

| Source | Type | Anchor | Use | Status |
|---|---|---|---|---|
| Office of Naval Research, [*Digital Computer Newsletter*, Vol. 12 No. 3](https://nsarchive.gwu.edu/sites/default/files/documents/5008457/Office-of-Naval-Research-Mathematical-Science.pdf), July 1960, "Perceptron Mark I - Cornell Aeronautical Laboratory" | Primary/in-period institutional | pp.1-3 of newsletter item | Mark I demo, ONR/RADC sponsorship, research-device caveat, 20x20 photocell eye, 512 association units, error-correction training, generalization claims | Green |
| Frank Rosenblatt, ["The Perceptron: A Probabilistic Model for Information Storage and Organization in the Brain"](https://lucidar.me/en/neural-networks/files/1958-the-perceptron-a-probabilistic-model-for-information-storage-and-organization-in-the-brain.pdf), *Psychological Review* 65(6), 386-408 (1958) | Primary | pp.386-389, 403-405 | Connectionist memory framing, perceptron as hypothetical nervous system/machine, probabilistic/statistical brain-model program, cautious claims about learning/generalization | Green |
| Frank Rosenblatt, [*Principles of Neurodynamics: Perceptrons and the Theory of Brain Mechanisms*](https://lucidar.me/en/neural-networks/files/1961-principles-of-neurodynamics-perceptrons-and-the-theory-of-brain-mechanisms.pdf) (1961) | Primary | pp.5, 94-95, 303-308, 575-576 | Larger perceptron program, minimal three-layer series-coupled systems, deficiencies of generalization/analysis, and multilayer/cross-coupled hopes | Green |
| Marvin Minsky and Seymour Papert, [*Perceptrons: An Introduction to Computational Geometry*](https://papers.baulab.info/papers/Minsky-1969.pdf) (1969; 1988 expanded edition intro excerpt) | Primary | Introduction pp.7-8, 12-14, 16-20 | Predicate/locality definitions, connectedness theorem, diameter-limited perceptron result, prior-structure critique, caution against quasi-universal random perceptrons | Green |
| Leon Bottou, [Foreword to MIT Press 2017 reissue](https://leon.bottou.org/publications/pdf/perceptrons-2017.pdf) of the 1988 expanded *Perceptrons* | Secondary/near-primary framing | pp.vii-viii | Real-world application gap, funding no longer forthcoming, mid-1980s revival, Papert's 1988 response, "fatal flaw" framing | Green |
| Mikel Olazaran, ["A Sociological Study of the Official History of the Perceptrons Controversy"](https://gwern.net/doc/ai/1996-olazaran.pdf), *Social Studies of Science* 26(3), 611-659 (1996) | Secondary historiography with interview evidence | pp.613, 629-631, 637-641 | Official-history caution, single-layer proof boundary, parity/XOR/connectedness interpretation, ARPA/ONR funding context, non-abandonment claim | Green after OCR |

## Claim Matrix

| Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|
| The Mark I perceptron was demonstrated publicly at Cornell Aeronautical Laboratory and funded by ONR with RADC assistance. | Machine That Learned Letters | ONR Digital Computer Newsletter July 1960 p.1 | Green | Institutional, in-period source. |
| Mark I was explicitly a limited-capacity research device, not an application-ready product. | Machine That Learned Letters | ONR Digital Computer Newsletter July 1960 p.1 | Green | Important anti-hype guardrail. |
| Mark I used a 20x20 photocell sensory unit, 512 association units, and eight response units. | Machine That Learned Letters | ONR Digital Computer Newsletter July 1960 pp.2-3 | Green | Hardware detail supports infrastructure layer. |
| ONR reported an error-correction training procedure and an errorless 26-letter demo after 40 exposures per letter. | Machine That Learned Letters | ONR Digital Computer Newsletter July 1960 p.2 | Green | Use cautiously as demo report, not general deployment proof. |
| Rosenblatt framed perceptron theory around recognition, generalization, storage, memory, and behavior. | Rosenblatt's Connectionist Bet | Rosenblatt 1958 p.386 | Green | Direct opening frame. |
| Rosenblatt's theory took the empiricist/connectionist position: retained information is in connections/associations rather than topographic image representations. | Rosenblatt's Connectionist Bet | Rosenblatt 1958 pp.386-387 | Green | Core conceptual scene. |
| Rosenblatt described the perceptron as a hypothetical nervous system or machine meant to illustrate properties of intelligent systems in general. | Rosenblatt's Connectionist Bet | Rosenblatt 1958 p.387 | Green | Avoid overclaiming full biological realism. |
| Rosenblatt claimed trial-and-error learning and some generalization were possible under stated conditions. | Rosenblatt's Connectionist Bet | Rosenblatt 1958 pp.396-405 | Yellow-Green | Green for cautious "claimed/argued"; avoid treating as broad proof. |
| Rosenblatt's 1961 book explicitly treats three-layer series-coupled perceptrons as "minimal perceptrons" and separates them from multilayer and cross-coupled systems where more work remained. | Rosenblatt's Connectionist Bet | Rosenblatt 1961 p.5 and pp.94-95 | Green | Helps prevent straw-manning Rosenblatt as single-layer-only. |
| Rosenblatt said three-layer series-coupled perceptrons were universal in principle but practically deficient in generalization, analysis, size, learning time, and external-evaluation dependence. | Scaling/Prior Structure | Rosenblatt 1961 pp.303-308 | Green | Good bridge to Minsky/Papert without making Rosenblatt naive. |
| Rosenblatt's summary says adding a fourth layer or cross-coupling can solve some generalization problems, while multi-layer pattern recognition may improve efficiency for detailed high-resolution fields. | Scaling/Prior Structure | Rosenblatt 1961 pp.575-576 | Green | Use cautiously; it is Rosenblatt's claim, not modern backprop. |
| Minsky/Papert define a perceptron as computing predicates linear in a set of partial predicates. | Mathematical Turn | *Perceptrons* intro p.12 | Green | Use for technical explanation. |
| Minsky/Papert prove `connected` is not conjunctively local of any order. | Mathematical Turn | *Perceptrons* intro pp.7-8 | Green | Strong exact theorem anchor. |
| Minsky/Papert prove no diameter-limited perceptron can compute connectedness. | Parity, Connectedness, and Scale | *Perceptrons* intro pp.12-14 | Green | Strong exact theorem anchor. |
| Minsky/Papert argue meaningful learning at meaningful rates needs prior structure, and that quasi-universal perceptrons are poor for high-order problems. | Scaling/Prior Structure | *Perceptrons* intro pp.16-17 | Green | Protects against "anti-learning" caricature. |
| Minsky/Papert say many perceptron projects worked on simple problems but deteriorated as tasks became harder. | Scaling/Prior Structure | *Perceptrons* intro pp.19-20 | Green | Use as their critique, not independent performance audit. |
| Bottou says perceptron research became unfashionable, funding was no longer forthcoming, and revival came with PDP/backprop in the mid-1980s. | From Theorem to Winter | Bottou 2017 foreword p.viii | Green | Secondary framing; good for bridge, not sole causality proof. |
| Olazaran says the "official history" held that Minsky/Papert showed neural-net progress impossible, but he argues the view emerged through controversy closure and neural nets were not completely abandoned. | From Theorem to Winter | Olazaran 1996 p.613 | Green after OCR | Key myth-correction anchor. |
| Olazaran says strictly speaking Minsky/Papert showed limitations for a class of single-layer nets, while multilayer pessimism was a learning conjecture. | From Theorem to Winter | Olazaran 1996 p.629 | Green after OCR | Critical anti-overclaim guardrail. |
| Olazaran connects parity to XOR and summarizes the order-growth interpretation for parity and connectedness. | Parity, Connectedness, and Scale | Olazaran 1996 pp.630-631 | Green after OCR | Lets prose mention XOR only as shorthand, not as whole story. |
| Olazaran says ARPA explicitly backed symbolic AI and rejected neural-net funding, with ONR funding levels much smaller. | From Theorem to Winter | Olazaran 1996 pp.637-638 | Green after OCR | Use as historiographic/interview-based account. |
| Olazaran says the abandonment narrative was exaggerated and some neural-net work continued outside AI. | Door Left Open | Olazaran 1996 pp.640-641 | Green after OCR | Important close/handoff. |

## Citation Bar

Minimum sources before prose:

- ONR Digital Computer Newsletter July 1960 pp.1-3.
- Rosenblatt 1958 pp.386-389 and pp.396-405.
- Rosenblatt 1961 pp.5, 94-95, 303-308, 575-576.
- Minsky/Papert *Perceptrons* intro pp.7-8, 12-14, 16-20.
- Bottou 2017 foreword pp.vii-viii.
- Olazaran 1996 pp.613, 629-631, 637-641.

## Source Discipline Notes

- Wikipedia may be used only for discovery and title/date sanity checks. It is
  not a prose claim anchor.
- The issue title's "XOR proof reveals computational intractability of
  multi-layer networks" is not safe as written. Treat XOR as a parity shorthand
  and keep the proof boundary to single-layer/local/order-restricted perceptrons.
- Rosenblatt 1961 is Green only for the anchored claims listed above. Do not
  generalize from it to modern multilayer perceptrons or backpropagation.
