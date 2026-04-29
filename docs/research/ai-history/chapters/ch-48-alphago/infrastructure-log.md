# Infrastructure Log: Chapter 48 - AlphaGo

## Scene 1 - The Board That Broke Brute Force

- **Computational constraint:** Silver et al. model games as search trees of about `b^d`; they give chess as `b approx 35, d approx 80` and Go as `b approx 250, d approx 150`, then state exhaustive search is infeasible. Anchor: `sources.md` G1.
- **Pre-AlphaGo baseline:** Strong Go programs used MCTS plus learned policies, but the paper characterizes the best prior systems as strong amateur level. Anchor: `sources.md` G3.

## Scene 2 - Policy, Value, Search

- **Input representation:** Board position as a 19x19 image processed by convolutional layers. Anchor: `sources.md` G4.
- **Training data:** About 30 million KGS expert positions; methods specify 29.4 million positions from 160,000 KGS 6-9 dan games. Anchor: `sources.md` G6.
- **Supervised policy network:** 13-layer policy network; 57.0% expert-move prediction accuracy with all input features. Anchor: `sources.md` G6.
- **Reinforcement learning:** Policy-gradient self-play improves the policy; RL policy wins over 80% against the supervised policy and 85% against Pachi without search. Anchor: `sources.md` G7.
- **Value network:** 30 million distinct self-play positions; single value-network evaluation approaches stronger rollouts at far lower computation. Anchor: `sources.md` G8.
- **Search:** AlphaGo MCTS stores action values, visit counts, and prior probabilities; leaf nodes are evaluated by both value network and rollout, and the final move is selected by root visit count. Anchor: `sources.md` G9.

## Scene 3 - The Hidden Machine

- **Google Cloud Platform:** DeepMind's launch post says training made extensive use of Google Cloud Platform. Anchor: `sources.md` G12.
- **Tournament hardware:** Nature Extended Data Table 6 lists distributed AlphaGo with 1,202 CPUs and 176 GPUs in a 5-second-per-move tournament setting. Anchor: `sources.md` G23.
- **Scalability hardware:** Nature Extended Data Table 8 lists tested distributed configurations up to 64 search threads, 1,920 CPUs, and 280 GPUs. Anchor: `sources.md` G24.
- **Critical caveat:** The exact Lee Sedol live-match compute configuration is not Green. Do not write "AlphaGo used 1,920 CPUs and 280 GPUs in Seoul" unless Y1 is resolved.

## Scene 4 - Seoul And Move 37

- **Match interface:** Aja Huang transferred AlphaGo's moves to the physical board. Anchor: `sources.md` G28.
- **Time controls:** Two hours each plus three 60-second byoyomi periods under Chinese rules with 7.5 komi. Anchor: `sources.md` G16.
- **Operational setting:** WIRED reports the DeepMind team monitored infrastructure and commentaries from a control room, but exact server location and match compute remain Yellow. Anchors: `sources.md` S5 lines 84-89; Y2.

## Scene 5 - The Human Reply And Aftermath

- **Post-match substrate:** The $1 million prize was to be donated after AlphaGo's win. Anchor: `sources.md` G21.
- **Reuse boundary:** AlphaGo Zero/AlphaZero later changed the training setup, but this chapter should not use later systems to explain the 2016 machine retroactively.
