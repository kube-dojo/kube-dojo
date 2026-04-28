# Scene Sketches: Chapter 33 — Deep Blue

Five scenes mapped 1:1 to the Prose Capacity Plan layers in `brief.md`. Each scene lists its primary anchored beats from `sources.md`. The chapter-level Boundary Contract applies throughout: do not invent dialogue, internal states, or motives beyond what primary sources document.

---

## Scene 1 — The Long Approach (1985-1996)

**Plan budget:** 600-900 words. **Density:** moderate; this scene compresses 12 years.

**Anchored beats** (Scene-Level Claim Table rows 1, 2, 3):

- **Hsu at CMU, 1985.** Hsu begins doctoral work at Carnegie Mellon on a chess-specific VLSI move generator. Anchor: Hsu 1999 IEEE Micro p.70 ("Chess machines based on a move generator of my design").
- **The chip lineage.** ChipTest (1986-87) → Deep Thought (1988-91) → Deep Thought II (1992-95). Each held the title of top chess program in the world. Anchor: Hsu 1999 p.70.
- **The 1988 Fredkin Intermediate Prize.** Deep Thought wins the second Fredkin Intermediate Prize for sustained Grandmaster-level performance — 2650+ rating across 25 consecutive USCF games. Anchor: Hsu 1999 p.70. *Forward-pointer:* the Fredkin Prize was created for the first computer to beat a reigning world champion in a match — that prize ($100,000) is what the Deep Blue team will collect on June 30, 1997 after the rematch (Newborn 2003 ref [3]).
- **The IBM hire (late 1989).** IBM Research approaches the CMU group; Hsu and Campbell join Watson. The new project is renamed "Deep Blue" in a play on IBM's "Big Blue" nickname. Anchor: Greenemeier 2017 SciAm Campbell interview; IBM corporate history.
- **Philadelphia, February 1996.** First Kasparov-Deep Blue match. Game 1 is the first computer victory over a reigning world champion in regulation time. Kasparov adapts after Game 1 and wins the match 4-2. Anchor: Newborn 2003 Ch.6 pp. 91-112; Hsu 1999 p.71 ("In 1996 Deep Blue was even with Kasparov after four games in the first match. Kasparov pinpointed Deep Blue's weaknesses and won the remaining two games easily").
- **The lesson of Philadelphia.** Speed alone wasn't enough. Per Hsu 1999 p.71: "Computation speed alone apparently didn't suffice." The team identifies two countermeasures — put more chess knowledge directly on the chip, and make positional weights software-adjustable so they can be tuned between games. Joel Benjamin is hired as full-time grandmaster consultant. Anchor: Hsu 1999 p.71; Greenemeier 2017 SciAm Campbell interview on Benjamin's role.

**Boundary-contract reminders for prose:**
- Do not call the 1988 Fredkin Intermediate Prize "the AI prize"; it was a chess prize for sustained Grandmaster-level performance.
- Do not present Hsu's 1985 start as a thesis on "artificial intelligence"; his thesis title (per Hsu 1999 p.81) was *Large-Scale Parallelization of Alpha-Beta Search* — a search-architecture thesis, not a learning thesis.
- Do not retroactively assign the team a "build AGI" goal. Greenemeier 2017 SciAm Campbell quote: "they wanted to know if there was something special about the very best chess players in the world that was beyond what computers were capable of for the foreseeable future." The goal was scoped to chess.

---

## Scene 2 — The Chip and the Cabinet

**Plan budget:** 800-1,200 words. **Density:** highest; this is the most primary-anchored scene.

**Anchored beats** (rows 5-13, 26):

- **The chess chip itself.** 0.6-micron, three-metal-layer, 5-V CMOS. 40-50 ns cycle time. ~10 cycles per position evaluated. ~1 watt. (Hsu 1999 p.75.) Per chip throughput: 2-2.5 million positions/sec. (Hsu 1999 p.71.) Internal blocks: move generator (8×8 silicon chessboard), smart-move stack (with O(n) repetition detector), evaluation function (fast/slow), search control. (Hsu 1999 p.72.) Search algorithm in silicon: minimum-window alpha-beta variant — eliminates the value stack a regular alpha-beta would need. (Hsu 1999 p.80.)
- **Why silicon.** A single chess-chip "position" requires up to 40,000 general-purpose CPU instructions. At 2.5M positions/sec per chip, one chip is the equivalent of a 100-billion-instruction/sec supercomputer. (Hsu 1999 p.72.) This is the chapter's load-bearing engineering claim: brute force, but the brute force is concentrated in special-purpose silicon.
- **The cabinet.** 30 IBM RS/6000 SP nodes (28 × 120 MHz P2SC + 2 × 135 MHz P2SC, *Yellow on this split*). Each node controls 16 chess chips on 2 Micro Channel cards × 8 chips. 480 chess chips total. (Hsu 1999 p.71-72; Newborn 2003 p.122.)
- **The hybrid search.** Master node searches first ~4 plies; workers handle next ~4 plies; chess chips finish the last 4-5 plies in hardware. The software portion handles ~1% of total positions but controls ~⅔ of the search depth. (Hsu 1999 p.72.) Selective extensions deepen the search to ~40 plies along forcing lines, even though the non-extended search reaches only ~12 plies. (Hsu 1999 p.72.) Per-move position count: "on the order of 20 to 40 billion positions." (Campbell-Hoane-Hsu AAAI 1999 SS-99-07 p.1 abstract.) Sustained system throughput: ~200 million positions/sec / ~8 tera-ops. (Hsu 1999 p.72.)
- **The honest-throughput beat.** The "200 million positions per second" headline is a *sustained* speed during quieter positions; Campbell told *Scientific American* in 2017 the actual range was 100-200 million depending on position type. (Greenemeier 2017 SciAm Campbell quote.) The chapter must use the range, not the single number.
- **Joel Benjamin's role.** Tuned the evaluation function's positional-feature weights between games; curated the opening book; sparring partner who probed weaknesses. (Greenemeier 2017 SciAm Campbell quote.) Hsu 1999 p.71 documents the design choice that made this possible: "we made the weights associated with the positional features individually adjustable from software."
- **The architectural-dead-end framing.** The chess chip embeds chess into silicon: 8×8 board as combinatorial logic, repetition detector with hardware-cycle-time constants, evaluation function tuned by a grandmaster. None of this generalizes. The chapter lays the groundwork for the closing argument here.

**Boundary-contract reminders for prose:**
- Do not call alpha-beta "the AI algorithm." Alpha-beta is a 1975 Knuth-Moore search-tree pruning algorithm. Deep Blue used it in two variants: a software version with selective extensions on the SP nodes, and a minimum-window hardware version on the chips.
- Do not treat the "200 million positions per second" figure as a single deterministic number.
- Do not present the chip as "neural" or "learning." The chess chip's evaluation function is a hand-designed combinatorial circuit with software-adjustable weights — not a learned representation.
- Do not erase the 30/32 node conflict; cite it explicitly.

---

## Scene 3 — Move 44 and the Bug

**Plan budget:** 500-800 words. **Density:** narrative-tight; one game, one move.

**Anchored beats** (rows 14, 15, 16):

- **Game 1 setup.** May 3, 1997. Kasparov plays White, Réti / King's Indian Attack. (Wikipedia game record citing Pandolfini 1997 p.65.)
- **The middlegame.** Kasparov maintains a clear advantage from move 30 onward; Hsu watched, "his arm hung limply over the arm of the chair" (Newborn 2003 p.150 — a documented physical detail, usable in prose). After move 40, Campbell replaces Hsu at the board.
- **The bug.** Move 44. Deep Blue plays an "incredibly bad" move; its score drops about 300 points (three pawns). Anchor: Newborn 2003 p.150 — "On its 44th move, a devilish bug suddenly surfaced, causing a random, totally illogical move! Campbell later confided." The bug had surfaced in 1996, and again in early 1997 in a Deep Blue Junior vs. Larry Christiansen game (Newborn Appendix I). Five trigger paths had been identified; four had been fixed; the fifth was overlooked.
- **The overnight repair.** "The logs confirmed the presence of the bug, and that evening Hoane worked to eliminate it." (Newborn 2003 p.150.) Hoane fixes the bug.
- **The psychological aftermath.** Campbell's direct quote (Newborn 2003 p.151): "Kasparov saw this move and asked his own team why Deep Blue made it. They didn't know. They looked at alternatives, and found they lost also. So they conjectured that Deep Blue had looked 30-40 levels ahead at the alternatives — they were overestimating Deep Blue's talents here — and saw that all the moves lost, and that it didn't matter what was played, so it played a random move. Now, of course, this wasn't the case at all, but it perhaps gave Kasparov a false impression about what Deep Blue could do." Campbell continues: "this might have been a factor in the next game where, in the final position, Kasparov overestimated Deep Blue's strength."
- **Frame as Campbell's interpretation.** Kasparov has not corroborated this account in primary sources I've located. Silver (2012) *The Signal and the Noise* popularizes the same theory.

**Boundary-contract reminders for prose:**
- Do not assert that the bug *caused* Kasparov to lose Game 2. Frame it as Campbell's retrospective interpretation, well-anchored as such, but not as established psychological causation.
- Do not invent Kasparov's emotional state or his coach team's specific words. Newborn quotes Campbell on what Kasparov's team conjectured; that is the load-bearing source.
- Do not repeat the popular myth that Deep Blue "intentionally" made an inscrutable move. Newborn 2003 p.150 is explicit: it was a random fail-safe selection caused by an unfixed code path.

---

## Scene 4 — Move 36 and the Panic

**Plan budget:** 800-1,100 words. **Density:** moderate-high; this is the chapter's emotional centerpiece.

**Anchored beats** (rows 17, 18, 19, 20, 27):

- **Game 2 setup.** May 4, 1997. Deep Blue plays White, Ruy Lopez Smyslov Variation. After 19 moves the game is outside the extended opening book. (Wikipedia game record citing Pandolfini 1997 p.167; Campbell 1999 CACM "Knowledge discovery in deep blue.")
- **The panic-time engineering.** After 35.Bxd6 Bxd6, Deep Blue evaluates 36.Qb6. The 8-ply search returns +87. The 9-ply, 10-ply, and 11-ply searches return progressively lower scores. Midway through the 11-ply search, the program's panic-time logic triggers: it adds wall-clock time to consider alternatives. After ~100 additional seconds it completes 36.Qb6 (final eval +48). It then quickly evaluates 36.axb5 (eval +63), an improvement enough to commit. Anchor: Newborn 2003 pp.159-160 quoting Bruce Weber NYT 5/13/97.
- **Total time on move 36.** Over 6 minutes — the longest single move of the rematch. Across the rematch, Deep Blue spent more than 5 minutes on 12 separate moves; Newborn Appendix L lists them all (p.315). Each was a panic-time deepening. (Newborn 2003 p.160.)
- **The 37.Be4 character.** "A monumental positional move, preventing Kasparov from creating havoc in White's territory by pushing his potentially troublesome e-pawn." (Newborn 2003 p.160.) Not a material grab. Deep Blue had calculated 37.Qb6 Rxa2 38.Rxa2 Ra8 39.Rxa8 Qxa8 40.Qxd6 Qa1+ 41.Kh2 Qc1 led to an equal game.
- **Kasparov's accusation.** After resigning (45.Ra6, in a position later shown drawable by 45...Qe3), Kasparov accuses IBM of cheating: a human grandmaster must have intervened, because the move was uncharacteristically positional for a computer. (Wikipedia citing the *Game Over: Kasparov and the Machine* documentary; ChessBase 2015.)
- **The vindication.** Modern engines (Houdini 4, Stockfish 6, Komodo 8 — circa 2015) all select 36.axb5 as Deep Blue's preferred move. Anchor: Albert Silver, "Deep Blue's cheating move," ChessBase 2015 (*Yellow*).
- **The deeper irony.** Deep Blue's "great move" was selected by a *frightened* search routine, not by anything resembling grandmaster intuition. The machine's panic was its strength. The chapter's centerpiece argument lives here.

**Boundary-contract reminders for prose:**
- Do not present the 36.axb5 / 37.Be4 sequence as evidence that Deep Blue understood chess in a "human" way. The engineering account in Newborn 2003 pp.159-160 is unambiguous: panic-time deepening, alternatives compared on numerical evaluations, the "more positional" move selected because the alternative was scoring worse — not because Deep Blue valued positional play.
- Do not present Kasparov's cheating accusation as either vindicated or dismissed. Cite it as documented; cite the modern-engine vindication of the move (different question — was the move good?); cite the engineering reality (the move was selected by a frightened search routine).
- Do not infer Kasparov's reasoning beyond Newborn 2003 p.159: "Kasparov was expecting 36 Qb6 and not 36 axb5, believing that Deep Blue would attempt to grab material" (per Khodarkovsky, ref [3]). That is the documented expectation; speculation beyond it is out of bounds.

---

## Scene 5 — Game 6 and the Aftermath

**Plan budget:** 600-900 words. **Density:** narrative-and-argument.

**Anchored beats** (rows 21, 22, 23, 24, 25):

- **Game 6 setup.** May 11, 1997 (Mother's Day Sunday), Equitable Center, NYC. Score tied 2.5-2.5. Deep Blue plays White; Kasparov plays the Caro-Kann Defence (Steinitz Variation, ECO B17) — an opening he had not used in formal tournament play since the early 1980s, against the Yugoslavian chess grandmaster Predrag Nikolić (Newborn 2003 p.193). Kasparov's reasoning: the Caro-Kann would push Deep Blue out of its opening-book preparation. (Wikipedia citing Hsu 2002; Newborn 2003 Ch.13 pp. 187-190.)
- **The knight sacrifice.** Move 8: Deep Blue plays Nxe6 — a known refutation of the line Kasparov chose, pulled out of opening-book preparation rather than computed in the moment. Kasparov, expecting an engine to require a concrete material gain before sacrificing, did not anticipate the move. (Wikipedia game record; Newborn 2003 Ch.13.)
- **The miniature.** Kasparov resigns after 19.c4. Fewer than 20 moves. The shortest game of either match. (Newborn 2003 p.205-206.)
- **Final score.** Deep Blue 3.5, Kasparov 2.5. The first time a reigning world chess champion lost a match to a machine under classical tournament time controls. (Newborn 2003 p.205-206; Hsu 1999 p.80.)
- **Kasparov's performance estimate.** Per Hsu 1999 p.80: Kasparov ~2815 ELO during the rematch; Deep Blue's match performance ~2875. Hsu cautions: "we couldn't take this rating too seriously because of the small sample size."
- **The IBM decision.** IBM declines Kasparov's request for a rematch. Greenemeier 2017 SciAm Campbell quote: "We felt we had achieved our goal, to demonstrate that a computer could defeat the world chess champion in a match and that it was time to move on to other important research areas."
- **The retirement.** Reuters reports Deep Blue's retirement from chess matches, September 24, 1997. (Newborn 2003 ref [10] McCool Reuters 9/24/1997.)
- **The architectural-dead-end close.** The chess chip embedded chess rules into silicon. Its evaluation function — tuned by Joel Benjamin's hand — could not be reused for any other game. Hsu's own next move (per Hsu 1999 p.81) was to leave IBM and form a startup to build chess chips for consumers. The IBM team dispersed: Brody retired, Tan moved on. Deep Blue did not generalize. The chapter's closing argument lives here: this was a hardware victory in chess, not a generalizable AI breakthrough. The "AI has arrived" headlines were wrong; the next two decades of AI research would solve different problems via radically different methods (neural networks, Ch.43 onward; reinforcement learning, Ch.48; AlphaGo as an explicit philosophical successor).

**Boundary-contract reminders for prose:**
- Do not write "Deep Blue marked the moment AI arrived" — every primary source rejects that framing.
- Do not present the IBM retirement as triumphant in tone; Greenemeier 2017 SciAm Campbell quote frames it as goal-achieved-and-moving-on, not as a victory lap.
- Do not anticipate AlphaGo's philosophical critique of Deep Blue (Ch.48). Single-sentence forward pointer is permitted; full argument is not.
- Do not assert "Deep Blue went to the Smithsonian" as a single load-bearing fact; the rack disposition is Yellow until museum accession records verify.
