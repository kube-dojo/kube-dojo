# Sources: Chapter 48 - AlphaGo

## Verification Key

- **Green**: the specific claim has a verified page, section, line-stable web anchor, DOI+page, figure, table, or official post section.
- **Yellow**: the source is credible and anchored, but the exact claim needs a stronger page/section match, a primary-source check, or more careful wording.
- **Red**: do not draft this claim except as an explicit open question.

## Primary And Official Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| S1 | David Silver et al., "Mastering the game of Go with deep neural networks and tree search," *Nature* 529, 484-489 (2016). DOI: `10.1038/nature16961`. Open PDF: `https://storage.googleapis.com/deepmind-media/alphago/AlphaGoNaturePaper.pdf`; Nature page: `https://www.nature.com/articles/nature16961` | Load-bearing technical source: Go search scale, AlphaGo architecture, training pipeline, Fan Hui result, hardware tables, author contributions. | **Green** for page anchors cited in G1-G8, G19-G20. Web tool opened the PDF text directly; shell `curl` was attempted but DNS resolution is blocked in this sandbox. |
| S2 | Demis Hassabis, "AlphaGo: using machine learning to master the ancient game of Go," Google Keyword / Google Blog, January 27, 2016. URL: `https://blog.google/technology/ai/alphago-machine-learning-game-go/` | Official launch narrative: Go cultural setup, complexity framing, policy/value network explanation, training on expert moves and self-play, Google Cloud Platform use, Fan Hui match, Lee Sedol challenge announcement. | **Green** for section anchors cited in G9-G14. |
| S3 | Demis Hassabis, "AlphaGo's ultimate challenge: a five-game match against the legendary Lee Sedol," Google Keyword / Google Blog, March 8-15, 2016. URL: `https://blog.google/innovation-and-ai/products/alphagos-ultimate-challenge/` | Official match log: schedule, rules, time controls, prize terms, each game result, score, and official post-game summaries. | **Green** for section anchors cited in G15-G22. |
| S4 | Google DeepMind YouTube livestream descriptions for the 2016 Challenge Match, especially "Match 2 - Google DeepMind Challenge Match: Lee Sedol vs AlphaGo" and "Match 4 - Google DeepMind Challenge Match: Lee Sedol vs AlphaGo." | Official video metadata for match date/time, participants, commentary by Michael Redmond and Chris Garlock, and Fan Hui 5-0 context. | **Yellow** here because the current contract did not extract transcript timecodes. Descriptions are useful as secondary support for S3, not as standalone Green anchors for spoken claims. |

## Secondary Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| S5 | Cade Metz, "How Google's AI Viewed the Move No Human Could Understand," *WIRED*, March 14, 2016. URL: `https://www.wired.com/2016/03/googles-ai-viewed-move-no-human-understand/` | On-site reporting for Move 37, David Silver's post-game explanation, Fan Hui's reaction, and the "one in ten thousand" claim. | **Green** for anchored article sections cited in G23-G24; secondary but first-hand reporting with named sources. |
| S6 | Cade Metz, "In Two Moves, AlphaGo and Lee Sedol Redefined the Future," *WIRED*, March 16, 2016. URL: `https://www.wired.com/2016/03/two-moves-alphago-lee-sedol-redefined-future/` | Reception source comparing AlphaGo's Move 37 and Lee Sedol's Move 78, with on-site context and Silver/Hassabis explanations. | **Green** for anchored article sections cited in G25; use sparingly because it is interpretive. |
| S7 | British Go Association, "Google DeepMind Challenge Match - Lee Sedol v AlphaGo - match report." URL: `https://www.britgo.org/alphago-leesedol` | Go-community match report: final score, venue, livestream details, Aja Huang placing AlphaGo stones, per-game summaries, Move 37 and Move 78 reception. | **Green** for anchored factual match report rows G26-G28; secondary organization source. |
| S8 | Melanie Mitchell, *Artificial Intelligence: A Guide for Thinking Humans* (2019). | Secondary interpretation of AlphaGo as a public inflection point in deep learning and reinforcement learning. | **Yellow** until exact edition/page anchors are extracted from a physical or digital copy. |
| S9 | Greg Kohs, *AlphaGo* documentary (2017). | Useful for atmosphere, on-camera participants, Lee Sedol/Fan Hui reception, and match-room staging. | **Yellow** until timecodes are extracted from a verified copy. Do not quote from memory. |

## Scene-Level Claim Table

| ID | Claim | Scene | Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|---|
| G1 | Go's game tree made exhaustive search infeasible at the scale AlphaGo confronted: Silver et al. give chess as roughly breadth 35/depth 80 and Go as roughly breadth 250/depth 150, then state exhaustive search is infeasible. | 1 | S1, *Nature* PDF p.484, lines 12-20; DOI `10.1038/nature16961`. | S2, Jan. 27 blog, "Go is a game of profound complexity" section. | **Green** | Use the paper's `b approx 250, d approx 150`; avoid loose "10^170 search tree" unless separately anchored. |
| G2 | Prior game AI successes reduced search depth with position evaluation or breadth with policies; that recipe worked in chess/checkers/othello but was believed intractable in Go. | 1 | S1, p.484, lines 21-32. | S2, lines 264-266. | **Green** | Good bridge from Deep Blue to AlphaGo without claiming AlphaGo was "not search." |
| G3 | The strongest pre-AlphaGo Go programs used Monte Carlo tree search enhanced by policies trained on expert moves, but had reached only strong amateur play. | 1 | S1, p.484, lines 33-45. | S1 references 13-16; S2 says computers still played Go as amateurs at launch. | **Green** | Useful for showing AlphaGo built on MCTS rather than replacing it. |
| G4 | AlphaGo treated the Go board as a 19x19 image and used convolutional layers to represent the position. | 2 | S1, p.484, lines 49-53. | S2, lines 266-267. | **Green** | This is the chapter's clearest "deep learning changes the representation" anchor. |
| G5 | AlphaGo used policy networks to reduce breadth/select moves and a value network to reduce depth/evaluate positions. | 2 | S1, p.484, lines 51-65; S2, lines 266-267. | Nature abstract lines 72-80. | **Green** | Safe plain-language formulation: policy = move selection, value = position evaluation. |
| G6 | The supervised policy network was trained from about 30 million KGS positions and predicted expert moves with 57.0% accuracy using all features. | 2 | S1, p.485, lines 90-94; PDF/web P7 methods, lines 1677-1680 for 29.4 million positions from 160,000 games. | S2, line 268. | **Green** | Say "about 30 million" in prose to reconcile 30 million vs 29.4 million. |
| G7 | Reinforcement learning improved the policy network by self-play; the RL policy won more than 80% against the supervised policy and 85% against Pachi with no search. | 2 | S1, p.485, lines 101-126. | S2, line 269. | **Green** | Good evidence layer for why AlphaGo exceeded imitation. |
| G8 | The value network was trained on 30 million distinct self-play positions and a single value-network evaluation approached RL rollouts while using 15,000 times less computation. | 2 | S1, p.486, lines 234-243. | S1 Figure 2 caption, p.485, lines 158-170. | **Green** | Do not overstate as "equal" to rollouts; paper says approached. |
| G9 | AlphaGo's search combined policy and value networks inside Monte Carlo tree search: leaf nodes were evaluated by the value network and by rollouts, and the root move was chosen by visit count. | 2 | S1, p.486, lines 244-293. | S1 Figure 3 caption, p.486, lines 298-301 and following. | **Green** | This is the algorithmic spine of the chapter. |
| G10 | The Google launch post framed Go as played by intuition and feel, with more legal positions than atoms in the universe and vastly more than chess. | 1 | S2, Jan. 27 blog, lines 261-264. | S1, p.484, lines 12-20. | **Green** | "Atoms" is official blog framing, not the Nature paper's technical anchor. |
| G11 | DeepMind said traditional search-tree methods "don't have a chance" in Go, and described AlphaGo as advanced tree search plus deep neural networks. | 1, 2 | S2, lines 266-267. | S1, p.484-p.486 technical sections. | **Green** | Use as official public framing, not as a substitute for S1 technical detail. |
| G12 | DeepMind said AlphaGo used Google Cloud Platform during training/experimentation. | 3 | S2, line 269. | S1 hardware tables show CPU/GPU configurations. | **Green** | Only Green for "made extensive use of GCP"; exact Lee Sedol deployment location remains Yellow. |
| G13 | Before Lee Sedol, AlphaGo beat other top Go programs in 499 of 500 games and beat Fan Hui 5-0 in a closed-door October 2015 match. | 3 | S2, lines 270-271. | S1 abstract, p.484, lines 72-80; S1 Fig. 4/6 and Extended Data Table 1. | **Green** | "499 of 500" comes from Google post; Nature abstract gives 99.8%. |
| G14 | The Fan Hui match was the first time a computer program defeated a human professional Go player on the full-sized game. | 3 | S1 abstract, p.484, lines 72-80; S2, line 271. | S3 pre-match update line 356. | **Green** | Phrase as "professional Go player," not "world champion." |
| G15 | The Lee Sedol match was scheduled in Seoul for March 9, 10, 12, 13, and 15, 2016. | 4 | S3, pre-match update, lines 364-368. | S7, lines 23-24. | **Green** | Use exact dates. |
| G16 | Match rules: Chinese rules, 7.5-point komi, two hours per player, three 60-second byoyomi periods, even games, $1 million prize. | 4 | S3, lines 358-360. | S7, lines 23-24 and game reports. | **Green** | Prize donation only if AlphaGo won is also in S3. |
| G17 | Game 1, March 9: AlphaGo won after a complex fighting game; Lee had nearly 30 minutes left while AlphaGo used almost all its time. | 4 | S3, Game 1 section, lines 344-345. | S7, lines 28-35. | **Green** | Keep compact; this is setup, not a full game recap. |
| G18 | Game 2, March 10: AlphaGo took a 2-0 lead; official Google summary says its creative moves surprised expert commentators and both sides entered byoyomi overtime. | 4 | S3, Game 2 section, lines 325-337. | S5, lines 71-75; S7, lines 38-49. | **Green** | This supports Move 37 scene without overquoting. |
| G19 | Game 3, March 12: AlphaGo won its third straight game and claimed overall match victory after 176 moves. | 4 | S3, Game 3 section, lines 305-311. | S7, lines 51-59. | **Green** | "Overall victory" occurs before all five games were played. |
| G20 | Game 4, March 13: Lee Sedol won by resignation after 180 moves; the Google post identifies Lee's move 78 and AlphaGo's following move 79 as key. | 5 | S3, Game 4 section, lines 286-294 and 296-298. | S6, Move 78 section, lines 112-114; S7, lines 60-68. | **Green** | This keeps Lee's win in the chapter rather than making AlphaGo invincible. |
| G21 | Game 5, March 15: AlphaGo won after 280 moves; the final score was AlphaGo 4, Lee Sedol 1. | 5 | S3, Game 5 section, lines 269-275. | S7, lines 69-90; Guardian/other contemporary reports. | **Green** | Also anchors donation of the $1 million prize. |
| G22 | Official Google summaries framed AlphaGo's match as a major milestone reached roughly a decade earlier than many predicted. | 5 | S3, lines 271-275. | S1 abstract, p.484, lines 72-80 says the Fan Hui feat had been thought at least a decade away. | **Green** | Avoid universalizing beyond Google/DeepMind's framing. |
| G23 | In Extended Data Table 6, distributed AlphaGo used 1,202 CPUs and 176 GPUs in a 5-second-per-move tournament setting and reached Elo 3140. | 3 | S1, Extended Data Table 6, PDF/web P14, lines 1941-1955. | S1 Extended Data Table 8 scalability table. | **Green** | This is not necessarily the Lee Sedol match configuration. |
| G24 | In Extended Data Table 8, the largest tested distributed configuration listed 64 search threads, 1,920 CPUs, 280 GPUs, and Elo 3168 at 2 seconds per move. | 3 | S1, Extended Data Table 8, PDF/web P16, lines 1971-1988. | S1 Extended Data Table 6. | **Green** | Safe wording: "tested configuration," not "the match machine." |
| G25 | Silver et al. credit different teams for search implementation, neural-network training, evaluation framework, project management, and paper writing. | 2, 3 | S1, Author Contributions, lines 435-437. | Author list, S1 p.484 lines 3-11. | **Green** | Useful for people map; avoid reducing AlphaGo to one inventor. |
| G26 | WIRED's on-site report says AlphaGo's Game 2 move flummoxed commentators and Lee Sedol; Lee left the room for a spell and took nearly fifteen minutes to respond. | 4 | S5, lines 71-75. | S7, lines 43-49. | **Green** | Secondary but precise first-hand reporting; avoid invented room atmosphere. |
| G27 | David Silver told WIRED that AlphaGo's human-move model gave Move 37 a probability of one in ten thousand, but other training made the move look promising. | 4 | S5, "A One in Ten Thousand Probability" section, lines 98-102. | S6, lines 96-106. | **Green** | Do not quote beyond short excerpts; paraphrase. |
| G28 | British Go Association reports that Aja Huang transferred AlphaGo's moves on the physical board during the match. | 4 | S7, Game 1 section, lines 33-35. | S5, lines 84-87. | **Green** | Good physical-scene anchor. |
| Y1 | AlphaGo used exactly 1,920 CPUs and 280 GPUs for the Lee Sedol match. | 3, 4 | S1 Extended Data Table 8 confirms a 1,920/280 tested distributed configuration, but not that it was the live match configuration. | Frequently repeated in secondary accounts. | Yellow | Keep as Yellow until an official DeepMind/Google match-configuration source is anchored. |
| Y2 | AlphaGo's servers for the Lee Sedol match were located in the United States and connected to Seoul over the network. | 3, 4 | Wikipedia-like summaries repeat this; S2 only anchors Google Cloud Platform use generally. | S5 mentions an "all important Internet connection" at the Four Seasons, lines 84-87. | Yellow | Needs primary Google/DeepMind technical post, match FAQ, or documentary timecode. |
| Y3 | Lee Sedol was an 18-time world champion. | 4 | Contemporary journalism and encyclopedic summaries repeat this. | Google official source anchors "best Go player of the last decade," not title count. | Yellow | Use Google's "best Go player of the last decade" unless exact title-count source is extracted. |
| Y4 | The match reached roughly 200 million viewers. | 5 | Widely repeated in later retrospectives. | No primary media-measurement source anchored in this contract. | Yellow | Do not use exact audience number in prose without a source. |
| Y5 | Fan Hui's world ranking rose sharply after months of training with AlphaGo. | 5 | S6, lines 123-126 says his world ranking "skyrocketed." | Documentary may corroborate. | Yellow | "Skyrocketed" needs actual ranking data before Green. |
| R1 | AlphaGo's Move 37 proves the system possessed humanlike intuition or creativity in the psychological sense. | 4 | No source can verify the mental-state claim. | Sources support novelty and surprise, not inner experience. | Red | Reframe as "produced a move humans read as creative." |
| R2 | DeepMind engineers knew before Game 2 that Move 37 would become the symbolic moment of the match. | 4 | No anchor. | None. | Red | Do not draft clairvoyant lab drama. |
| R3 | AlphaGo's Lee Sedol victory directly caused modern generative AI. | 5 | Later commentators make broad analogies. | Causal chain is too large for this chapter. | Red | Boundary contract: forward pointer only, no causal overreach. |

## Anchor Worklist

### Done

- S1 *Nature* PDF: p.484-p.486 for game-search framing, policy/value/MCTS architecture, supervised learning, reinforcement learning, value-network training; PDF/web P14-P16 extended data tables for CPU/GPU configurations.
- S2 Google January 2016 post: official public framing for Go complexity, policy/value networks, expert data, self-play, Google Cloud Platform, Fan Hui 5-0.
- S3 Google March 2016 match post: official match schedule, rules, game-by-game results, final 4-1 score.
- S5/S6 WIRED: on-site Move 37 and Move 78 reception, Silver/Hassabis explanations.
- S7 British Go Association: Go-community match log, Aja Huang board transfer, per-game capsule reports.

### Still Needed Before Prose Expansion

- A primary or official source for the actual Lee Sedol match compute configuration, especially whether 1,920 CPUs/280 GPUs were used live.
- Transcript timecodes from Google DeepMind match videos or the *AlphaGo* documentary for Move 37 commentary and post-game press conference claims.
- Exact page anchors from Melanie Mitchell 2019 or another scholarly secondary source for the historical interpretation of AlphaGo's public meaning.
- A primary source for the commonly repeated Lee Sedol "18 world titles" claim if the prose wants that number.

## Conflict Notes

- **Hardware numbers:** Nature's extended tables verify tested and tournament configurations, but not the live Seoul match hardware. Do not silently convert Table 8 into a match-machine claim.
- **"Intuition" language:** Google used "intuition and feel" to describe human Go; the Nature paper describes policies, values, and search. Prose may say AlphaGo produced moves humans interpreted as intuitive, but must not ascribe inner states.
- **Fan Hui versus Lee Sedol milestone:** Fan Hui anchors the first professional full-board victory; Lee Sedol anchors the public defeat of a player Google called the best of the prior decade. Keep those milestones separate.
- **Move 37 mythology:** Move 37 is strong narrative material, but its technical explanation should remain tethered to Silver's probability account and the policy/value/search architecture rather than mystical language.
