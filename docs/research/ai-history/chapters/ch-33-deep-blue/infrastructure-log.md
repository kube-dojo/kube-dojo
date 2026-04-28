# Infrastructure Log: Chapter 33 — Deep Blue

What computing infrastructure each scene relied on, with primary or page-anchored secondary citation.

## Scene 1 — The Long Approach (1985-1996)

### CMU lab (1985-1989)

- ChipTest (1986-87) and Deep Thought (1988-91) were built around Hsu's custom chess move generator. Search speeds: ~500,000 positions/sec (ChipTest), ~700,000 positions/sec (Deep Thought). (Hsu 1999 IEEE Micro p.70; Campbell-Hoane-Hsu 2002 §1.1, slide-deck rendering — Yellow.)
- ChipTest's chip was fabricated using student-design VLSI services. Newborn 2003 p.79: "Hsu's VLSI chess chip, the heart of the system, was designed using 3-micron technology." (Newborn 2003 Ch.4, p.79.)

### IBM Watson Research Center (Yorktown Heights, NY) — Deep Thought II era (1992-1995)

- Newborn 2003 p.87: 24 chess engines running on a multiprocessor configuration; the same move generator chip as Deep Thought, but with medium-scale multiprocessing, larger evaluation-function RAMs, and improved search software. (Hsu 1999 p.70; Newborn 2003 Ch.5 pp. 69-90.)

### Philadelphia (Feb 1996)

- The 1996 Deep Blue used a new chess chip designed at IBM Research over three years. (Hsu 1999 p.70.)
- Per Hsu's own retrospective in the IEEE Micro paper p.71: in 1996 Deep Blue "had serious gaps in their grasp of chess knowledge, which a human opponent would simply exploit." Kasparov adapted mid-match and won 4-2. (Newborn 2003 Ch.6 pp. 91-112.)

## Scene 2 — The Chip and the Cabinet (1997)

### The chess chip (Deep Blue II revision)

- **Process:** 0.6-micron, three-metal-layer, 5-V CMOS. (Hsu 1999 IEEE Micro p.75.)
- **Cycle time:** 40-50 nanoseconds. (Hsu 1999 p.75.)
- **Cycles per position:** ~10. (Hsu 1999 p.75.)
- **Power:** ~1 watt per chip. (Hsu 1999 p.75.)
- **Throughput:** 2-2.5 million chess positions per second per chip. (Hsu 1999 p.71, p.72.)
- **Chip blocks:** move generator + smart-move stack + evaluation function (fast + slow) + search control. The move generator is "implemented as an 8 × 8 array of combinatorial logic, which is effectively a silicon chessboard." (Hsu 1999 p.72.)
- **Search algorithm in silicon:** Minimum-window alpha-beta (Knuth-Moore 1975 alpha-beta variant). Eliminates the need for a value stack on the chip. (Hsu 1999 p.80.)
- **Per-chip "compute equivalent":** Hsu 1999 p.72 — "On a general-purpose computer, the computation done by the chess chip for a single chess position requires up to 40,000 general-purpose instructions. At 2 to 2.5 million chess positions/s, one chess chip operates as the equivalent of a 100-billion-instruction/s supercomputer."

### The full Deep Blue II system

- **Topology (per Hsu 1999 IEEE Micro pp.71-72 and Newborn 2003 p.122):**
  - 30 IBM RS/6000 SP nodes (28 with 120 MHz P2SC processors; 2 with 135 MHz P2SC processors per Campbell, Hoane, Hsu 2002 slide-deck rendering — *Yellow on the 28+2 split*).
  - Each node controls up to 16 chess chips, distributed over two Micro Channel cards × 8 chips each.
  - Total: 480 chess chips on 60 accelerator cards.
  - Each node has 1 GB of RAM and 4 GB of disk. (Campbell-Hoane-Hsu 2002 slide-deck rendering, *Yellow*.)
- **Aggregate throughput:** Sustained ~200 million chess positions/sec, ~8 tera-ops; "guaranteed not to exceed" headline ~1 billion positions/sec ≈ 40 tera-ops. (Hsu 1999 p.72.)
- **Match-time per-position throughput range:** 100-200 million positions/sec depending on position type. (Greenemeier 2017 SciAm Campbell quote.)
- **Match-time average vs. peak (Yellow):** 126 million average, 330 million peak — sourced to Campbell-Hoane-Hsu 2002 slide-deck rendering only; the journal version of the paper would unlock these as Green.
- **Search structure:** 3-layer hierarchical hardware/software search:
  - Master node searches first ~4 plies in software.
  - Worker nodes (29 of them) search next ~4 plies in software.
  - Chess chips search final 4-5 plies in hardware (including quiescence search). (Hsu 1999 p.72.)
- **Search depth (per move):** 12 plies non-extended; up to ~40 plies along forcing lines. The software portion handles ~1% of the total positions but controls ~⅔ of the search depth. (Hsu 1999 p.72.)
- **Positions examined per move:** "On the order of 20 to 40 billion positions." (Campbell-Hoane-Hsu AAAI SS-99-07 1999, p.1 abstract.)
- **Per-move clock budget:** 3 minutes per move (regulation tournament time control). (Hsu 1999 p.71.)

### The match-site infrastructure

- **Venue:** Equitable Center, midtown Manhattan, NYC. (Newborn 2003 pp.122-123, multiple references.)
- **Physical setup:** Two cabinets (the Deep Blue II SP2 system) in a private room; a fast deskside RS/6000 backup workstation in the IBM operations room at the Equitable Center; the Philadelphia-era 30-computer SP2 at Yorktown Heights as a remote second backup. (Newborn 2003 p.123.)
- **System arrival:** Truck transport from Poughkeepsie (where Deep Blue II was assembled and tested) to Manhattan, April 26, 1997, 100 miles. Operational at the Equitable Center on April 28. (Newborn 2003 p.123.)
- **Code freeze:** "In theory" April 15, 1997. (Newborn 2003 p.123.)

## Scene 3 — Game 1 (May 3, 1997)

- The 1997 Deep Blue II SP2 was running at the Equitable Center; its software state (frozen April 15) included a known intermittent bug — five trigger paths identified, four fixed, one missed. The bug had previously surfaced in 1996 and in early 1997 in a Deep Blue Junior vs. Larry Christiansen game (Newborn 2003 Appendix I). (Newborn 2003 pp. 150-151.)
- Hoane "worked to eliminate it" overnight after Game 1 (Newborn 2003 p.150). The chapter's prose may treat this as a documented overnight repair, not as a reconstructed scene.

## Scene 4 — Game 2 (May 4, 1997)

- Deep Blue II's search-control state machine includes a "panic time" extension: when the iterative-deepening search returns a score that is dropping by more than ~¼ pawn between plies, the machine adds extra wall-clock time to evaluate alternatives. (Newborn 2003 pp.159-160 quoting Bruce Weber NYT 5/13/97.)
- During Game 2 move 36, Deep Blue spent more than 6 minutes — a panic-time-triggered deepening. Across the rematch, the machine spent more than 5 minutes on 12 distinct moves; Newborn 2003 Appendix L (p.315) lists all 12. (Newborn 2003 p.160.)

## Scene 5 — Game 6 and Aftermath

- The Game 6 system was the same Deep Blue II SP2 in continuous operation throughout the rematch; no infrastructure change between games beyond evaluation-function weight adjustments between games (Hsu 1999 p.71: "we did change the weights for the positional features between games").
- After the match (September 1997), IBM retired Deep Blue. (Reuters 9/24/1997, per Newborn 2003 ref [10].) Newborn 2003 p.221-222 describes the team's clocks remaining on Watson Research Center shelves and the team's Smithsonian intent.

## Build-Quality Caveats (Pending Verification)

- **Memory per node (1 GB RAM, 4 GB disk).** Sourced only to the Campbell-Hoane-Hsu 2002 slide-deck rendering. Pending journal-version access. Yellow.
- **The 28-vs-2 split between 120 MHz and 135 MHz P2SC processors.** Same provenance as memory claim; same Yellow status.
- **Chip count of 480 vs. an alternative claim of 256 chess processors.** IBM's pre-match event website said 32 nodes / 256 chess processors (8 chips × 32 nodes). The post-match designer accounts (Hsu 1999 p.71-72, Newborn 2003 p.122) say 30 nodes / 480 chips. The post-match accounting is the as-built figure; the pre-match marketing material may have reflected an earlier configuration target.
