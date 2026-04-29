# Brief: Chapter 48 - AlphaGo

## Thesis

AlphaGo did not defeat Go by abandoning search or by brute-forcing a larger tree than Deep Blue. It won by changing what search meant: deep neural networks learned policy and value estimates from expert games and self-play, then Monte Carlo tree search used those estimates to look selectively through a game that had long resisted exhaustive computation. The public drama of the Lee Sedol match made that technical shift visible. Move 37 was not magic, sentience, or a proof of machine creativity; it was a moment when a system trained beyond human imitation selected a move that human experts initially found strange, then retrospectively legible.

## Scope

- IN SCOPE: Go as a long-standing AI challenge; the DeepMind AlphaGo team; the 2015 Fan Hui match; the 2016 *Nature* paper; AlphaGo's policy networks, value network, reinforcement learning, self-play, Monte Carlo tree search, and CPU/GPU infrastructure; the March 2016 Lee Sedol match; Move 37 and Lee's Game 4 victory; the public and Go-community reception immediately around the match.
- OUT OF SCOPE: AlphaGo Zero and AlphaZero except as sparse forward references; AlphaFold; Gemini/modern foundation models; a full biography of Demis Hassabis, David Silver, Lee Sedol, or Fan Hui; a complete move-by-move Go commentary; detailed rules instruction beyond what a reader needs to follow the stakes.

## Boundary Contract

This chapter must not say AlphaGo "solved Go." It defeated selected professional opponents under match conditions; perfect play on full-board Go remains a different claim. It must not describe AlphaGo as a brute-force descendant of Deep Blue, because the verified architecture combines learned policy/value networks with Monte Carlo tree search. It must not describe Move 37 as evidence of consciousness, intention, or humanlike intuition. The strongest anchored phrasing is that AlphaGo's training and search made a low-human-probability move look valuable to the system.

The chapter must also keep the Fan Hui and Lee Sedol milestones distinct. Fan Hui anchors the first victory over a professional Go player on a full board; Lee Sedol anchors the public defeat of a player Google described as the best of the prior decade. Later "from AlphaGo to AGI/generative AI" claims are out of scope except for a short pointer to Ch49.

## Scenes Outline

1. **The Board That Broke Brute Force.** Go's board looks simple but creates a search problem far beyond chess. Establish the verified breadth/depth numbers and why pre-AlphaGo computer Go had remained around strong amateur strength.
2. **Policy, Value, Search.** Follow the AlphaGo pipeline: supervised learning on expert positions, reinforcement learning by self-play, a value network trained on self-play positions, and MCTS that uses both networks.
3. **The Hidden Machine.** Move from algorithm to infrastructure: KGS data, Google Cloud Platform, CPU/GPU configurations, team roles, and the Fan Hui closed-door result that made the Lee Sedol challenge plausible.
4. **Seoul And Move 37.** The March 2016 match as a public test: schedule, rules, Aja Huang placing stones, AlphaGo's first three wins, and the Game 2 move that experts initially found strange.
5. **The Human Reply And The Aftermath.** Lee Sedol's Game 4 Move 78 and win prevent a triumphalist story. Game 5 gives AlphaGo the 4-1 result, while the chapter closes on the narrower historical meaning: deep learning plus search had crossed a visible threshold, but not every later AI claim belongs here.

## Prose Capacity Plan

This chapter can support a medium-long narrative if the prose spends words where the anchors are dense:

- 650-900 words: **The board that broke brute force** - Scene 1. Explain Go's search scale and why MCTS-era Go programs had not reached elite professional play. Anchored to `sources.md` G1 (S1 *Nature* p.484, breadth/depth), G2 (S1 p.484, depth/breadth reduction), G3 (S1 p.484, MCTS programs at strong amateur play), and G10-G11 (S2 official Go complexity/search framing).
- 950-1,300 words: **AlphaGo's technical pipeline** - Scene 2. Give the reader a clear but non-textbook account of policy networks, value networks, supervised expert imitation, self-play reinforcement learning, and MCTS. Anchored to `sources.md` G4-G9 (S1 *Nature* p.484-p.486), G6-G8 (training/results), and G25 (team contributions).
- 600-850 words: **Infrastructure and pre-match credibility** - Scene 3. Show the data and machine substrate: KGS positions, Google Cloud Platform, CPU/GPU configurations, and Fan Hui's 5-0 loss. Anchored to `sources.md` G6, G12-G14, G23-G24. Keep Y1-Y2 hedged: Nature verifies configurations, not the exact live Seoul match machine.
- 900-1,250 words: **The Seoul match and Move 37** - Scene 4. Use the official schedule/rules/results plus anchored on-site reports to narrate Game 2 without inventing dialogue or mind-reading. Anchored to `sources.md` G15-G18, G26-G28, and G27 (Silver's one-in-ten-thousand explanation).
- 650-950 words: **Lee Sedol's answer and the honest close** - Scene 5. Cover Game 4's Move 78, Game 5's 4-1 result, and the precise historical claim AlphaGo can bear. Anchored to `sources.md` G20-G22, S6 Move 78 section, and conflict notes R1-R3.

Total: **3,750-5,250 words**. Label: `4k-7k stretch` - the lower-middle range is strongly supported now; the upper end requires timecoded match-video/documentary anchors and better secondary page anchors for reception. Without those, cap near 4,200-4,700 words.

If the verified evidence runs out, cap the chapter.

## Citation Bar

- Minimum primary/official sources before drafting: Silver et al. 2016 *Nature* PDF; Google January 2016 AlphaGo launch post; Google March 2016 Lee Sedol match log.
- Minimum secondary sources before drafting: WIRED on-site Move 37/Move 78 reporting; British Go Association match report.
- Optional strengthening before expansion: Google DeepMind video timecodes, *AlphaGo* documentary timecodes, Melanie Mitchell 2019 page anchors, primary source for exact Lee Sedol title count, primary source for exact live match compute.

## Conflict Notes

- **Hardware:** The common 1,920 CPU / 280 GPU number is verified in Nature as a tested distributed configuration, not yet as the live Lee Sedol match machine. Draft this as infrastructure scale, not as a match-specific claim.
- **Search versus learning:** AlphaGo was not "just deep learning" and not "just search." The paper's core claim is the combination.
- **Move 37:** Strong scene, weak metaphysics. Describe the move's measured low probability under a human-move model and its later reception; do not call it proof of consciousness or creativity.
- **Victory hierarchy:** Fan Hui was the first professional full-board milestone; Lee Sedol was the globally visible elite-player milestone.
- **Later AI:** Keep AlphaGo Zero/AlphaZero/AlphaFold/generative AI to sparse forward references ("see Ch49") unless the next chapter's contract explicitly invites a bridge.

## Honest Prose-Capacity Estimate

Current anchored estimate: **3,750-5,250 words**. Confidence the lower bound is achievable: high, because the Nature paper and official Google match log are dense. Confidence above 5,000 words: moderate-low without video/documentary timecodes and secondary-book page anchors. A faithful chapter should likely land around **4,200-4,700 words** unless another agent extracts those missing anchors.
