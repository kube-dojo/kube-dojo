# Scene Sketches: Chapter 48 - AlphaGo

## Scene 1 - The Board That Broke Brute Force

Open on the apparent simplicity of a Go board: black and white stones, intersections, territory. Then tighten quickly to the verified search problem. The *Nature* paper gives the clean numerical contrast: chess at about breadth 35 and depth 80; Go at about breadth 250 and depth 150. That is the reason the chapter cannot borrow the Deep Blue template. The scene should show why old game-AI confidence failed here: position evaluation and move pruning had worked elsewhere, while computer Go remained at strong amateur level before AlphaGo.

Evidence anchors: `sources.md` G1-G3, G10-G11.

## Scene 2 - Policy, Value, Search

This is the technical center. Present AlphaGo as a pipeline rather than a black box. First, the board becomes a 19x19 input image. A supervised policy network learns from expert KGS games. Reinforcement learning then pushes beyond imitation through self-play. A value network learns to estimate outcomes from self-play positions. MCTS wraps these learned judgments into a search procedure that expands promising branches, evaluates leaves, and chooses moves by visit counts.

Keep the prose concrete: policy narrows what to look at; value estimates how good a position is; MCTS tests those guesses under lookahead. Do not imply the network alone played the match.

Evidence anchors: `sources.md` G4-G9, G25.

## Scene 3 - The Hidden Machine

Shift from algorithm to infrastructure. The public saw stones on a board, but the system had been built from millions of expert positions, self-play games, Google Cloud Platform, and CPU/GPU search configurations. Use the Fan Hui match as the private rehearsal: a closed-door 5-0 result against the European champion that gave DeepMind enough confidence to challenge Lee Sedol.

This scene must preserve the hardware caveat. Nature verifies distributed configurations and a largest tested 1,920 CPU / 280 GPU setup, but this contract has not verified that exact setup as the live Seoul match machine.

Evidence anchors: `sources.md` G6, G12-G14, G23-G24; Yellow caveat Y1-Y2.

## Scene 4 - Seoul And Move 37

Use the official Google match log for structure: Seoul, March 9-15, Chinese rules, 7.5 komi, two hours plus byoyomi, five scheduled games. Aja Huang sits at the physical board to play AlphaGo's moves. AlphaGo wins Game 1, then in Game 2 makes the move that becomes mythic. WIRED and the British Go Association give the safe factual beats: experts found it strange; Lee left the room for a spell and took nearly fifteen minutes to respond; Fan Hui read beauty into it afterward; David Silver later explained that AlphaGo's human-move model saw it as a one-in-ten-thousand human move.

Do not write the scene as if AlphaGo "wanted" to surprise Lee. The strongest source-backed claim is that its training/search assigned value where human priors did not.

Evidence anchors: `sources.md` G15-G18, G26-G28, G27.

## Scene 5 - The Human Reply And The Aftermath

Resist the easy triumphal ending. AlphaGo wins Game 3 and clinches the match, but Lee Sedol wins Game 4 after Move 78 and AlphaGo's following mistake. That game matters because it keeps the chapter honest: AlphaGo was historically decisive and still fallible. Game 5 produces the final 4-1 score and the public milestone.

Close by narrowing the lesson. AlphaGo showed that deep learning, self-play, value estimation, and search could cross a boundary that had looked distant. It did not prove that neural systems were conscious, that Go was solved, or that every later AI development flowed directly from Seoul. The forward pointer is short: later systems will ask what happens when the human expert data is removed or the game setting is generalized (see Ch49).

Evidence anchors: `sources.md` G19-G22, G20, G21, and Red boundaries R1-R3.
