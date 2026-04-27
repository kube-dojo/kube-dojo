# Brief: Chapter 31 - Reinforcement Learning Roots

## Thesis

Reinforcement learning became one of the mathematical roots of modern AI when researchers turned a vague behavioral idea - reward and punishment over time - into a computational problem about delayed credit, value functions, dynamic programming, temporal differences, and action values. The important move was not that machines suddenly learned like animals. It was narrower and more durable: Bellman's sequential decision machinery, Samuel's game-learning experiments, Barto/Sutton/Anderson's actor-critic pole-balancer, Sutton's temporal-difference methods, and Watkins/Dayan's Q-learning gave AI a way to learn from consequences that arrived after the action.

This chapter should show why delayed reward was different from supervised learning. In supervised learning, the teacher can often say what the correct answer was. In reinforcement learning, the system may only discover much later whether earlier decisions were useful. The roots of the field are therefore a story about temporal credit assignment, exploration versus exploitation, value estimation, and the emergence of agents that improve by acting.

## Scope

- IN SCOPE: Bellman's dynamic-programming and Markov-decision background; Samuel's checkers program as an early game-learning and value-function precursor; Barto, Sutton, and Anderson's 1983 adaptive critic / associative search pole-balancing system; Sutton's 1988 temporal-difference formulation; Watkins's 1989 *Learning from Delayed Rewards* thesis; Watkins and Dayan's 1992 Q-learning convergence paper; Tesauro's TD-Gammon as a closing demonstration that TD/self-play could produce surprising game performance; the exploration-exploitation trade-off; model-free learning; delayed reward and temporal credit assignment.
- OUT OF SCOPE: a full derivation of Bellman equations, stochastic approximation proofs, all RL algorithms, Sutton's 1984 dissertation as a separate scene, SARSA and the on-policy/off-policy distinction, Sutton and Barto 1998 as a retrospective field-definition source, Minsky/SNARC prehistory, policy gradients, actor-critic after the early 1990s, deep Q-networks, AlphaGo, robotics survey history beyond short context, neuroscience/dopamine claims unless a later chapter explicitly needs them.

## Boundary Contract

Do not claim reinforcement learning was invented by one person. The verified story crosses operations research, psychology, control, cybernetics, game-playing AI, and machine learning.

Do not equate "reinforcement" in psychology with the computer-science field without qualification. Kaelbling, Littman, and Moore explicitly warn that the computer-science usage resembles psychology but differs in details and terminology.

Do not claim Q-learning solved general intelligence. Watkins and Dayan proved convergence for restricted finite Markovian settings under repeated sampling and learning-rate conditions; the chapter should explain the historical power of that guarantee without making it broader than the theorem.

Do not present TD-Gammon as proof that RL was generally ready for arbitrary real-world tasks. Tesauro's own article and the 1996 survey make the result impressive but also discuss task structure, stochastic dice, self-play risks, and generalization questions.

## Scenes Outline

1. **The Problem Supervision Could Not See:** Open with delayed reward: a move, a controller pulse, or a decision may be judged only much later. Contrast this with supervised pattern learning from earlier chapters.
2. **Bellman and Samuel Give the Shape:** Bellman's recurrence makes sequential decision problems recursive; Samuel's checkers program shows a machine improving a value function from play rather than receiving a label for every position.
3. **The Pole-Balancing Critic:** Barto, Sutton, and Anderson use an associative search element and adaptive critic element to learn a difficult control problem from sparse evaluative feedback, not full state equations.
4. **Temporal Difference as a Credit-Assignment Machine:** Sutton 1988 turns successive predictions into the learning signal, bridging Monte Carlo outcome learning and dynamic-programming bootstrapping.
5. **Delayed Rewards Become Q Values:** Watkins reframes learning from delayed rewards around Markov decision processes, exploration-exploitation, and action values; Watkins and Dayan give the 1992 convergence proof for Q-learning.
6. **Self-Play Shows the Ambition and the Limit:** TD-Gammon shows temporal-difference self-play reaching surprising backgammon strength, while also exposing why task structure and exploration still mattered.

## 4k-5.5k Prose Capacity Plan

- 550-700 words: delayed reward as the chapter's central problem, anchored by Kaelbling/Littman/Moore 1996 p.237 and Tesauro 1995 pp.1-2.
- 650-850 words: Bellman and Samuel as background roots, anchored by Bellman 1957 p.679 and Samuel 1959 pp.535-536, with no claim that either source used the modern RL label in the later standardized sense. Bellman should be a short 120-180 word ancestry bridge because only p.679 is accessible; Samuel should carry the rest of this scene.
- 750-950 words: Barto/Sutton/Anderson pole-balancing actor-critic story, anchored by IEEE p.834 for abstract-level claims only: title, authors, cart-pole task, sparse failure feedback, ASE/ACE existence, and unknown-equations assumption. Anything deeper, including update rules, learning rates, decay terms, or performance comparisons, needs clean OCR or another text anchor.
- 750-950 words: Sutton 1988 temporal-difference methods, anchored by pp.9-11 and the random-walk/game-learning examples on pp.18-24.
- 850-1,100 words: Watkins 1989 and Watkins/Dayan 1992, anchored by Watkins thesis OCR pp.4, 19, 23 and Watkins/Dayan 1992 pp.279-282, 287, 291-292.
- 650-900 words: TD-Gammon as closing bridge to self-play and later deep RL, anchored by Tesauro 1995 pp.1-2, 6-11 and Kaelbling/Littman/Moore 1996 pp.273-276.

Honesty close: this is a 4,000-5,500 word chapter under the recorded reviewer decision that the Barto visual anchor is acceptable for abstract-level claims only. If prose needs Barto implementation details beyond p.834 or Watkins thesis claims beyond the first 30 OCRed pages, keep the chapter capped until those anchors are added.

## Citation Bar

- Minimum primary sources before prose: Sutton 1988; Watkins and Dayan 1992; Tesauro 1995; and Barto/Sutton/Anderson 1983 p.834 as a reviewer-approved visual anchor for abstract-level claims only.
- Minimum root/context sources: Bellman 1957 Markovian decision process abstract/full first page; Samuel 1959 checkers paper; Kaelbling/Littman/Moore 1996 survey.
- Current status: Gemini and Claude confirmed the Barto visual-anchor handling and Watkins thesis cap are acceptable after the scope constraints above. Ready for prose drafting within those limits.
