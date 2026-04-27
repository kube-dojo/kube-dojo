# Infrastructure Log: Chapter 31 - Reinforcement Learning Roots

- The chapter's "infrastructure" is mostly mathematical and experimental rather than industrial: dynamic-programming recurrences, Markov decision process assumptions, value functions, action values, exploration schedules, and finite state/action representations.
- Samuel's checkers program depends on machine-playing time, lookahead search, board-position records, evaluation polynomials, and stored board-position memory. Do not imply modern compute; the source emphasizes constrained game search and evaluation.
- Barto/Sutton/Anderson's pole-balancing setup depends on a simulated/controlled cart-pole task with a sparse failure signal. The cart-pole equations were assumed unknown to the learner. Gemini and Claude accepted p.834 as a visual anchor for these abstract-level claims only; stronger OCR is required before describing implementation details beyond the abstract.
- Sutton 1988 emphasizes incremental computation and memory savings: TD updates can be computed from successive predictions rather than retaining complete histories.
- Watkins and Dayan 1992 prove Q-learning for finite/discrete Markov settings under repeated action sampling and learning-rate conditions. The "infrastructure" is a table of state-action quality estimates, not a deep neural network.
- TD-Gammon uses a multilayer neural network, temporal-difference learning, self-play, random dice, final reward feedback, and later hand-crafted features. Treat it as a bridge to later neural/self-play chapters, not as the main origin of RL.
