# Timeline: Chapter 33 — Deep Blue

All dates anchored to a primary or page-anchored secondary source. Where the source attributes a date approximately, that is noted.

## The Chip Lineage (CMU period)

- **1985.** Feng-hsiung Hsu begins doctoral work at Carnegie Mellon University on a chess-specific VLSI move generator. (Source: Hsu 1999 IEEE Micro p.70 — "Chess machines based on a move generator of my design"; Newborn 2003 Ch. 4 pp. 55-67.)
- **1986-1987.** ChipTest (CMU). First-generation Hsu/Anantharaman/Campbell chess machine. Top chess program of its era. (Hsu 1999 p.70.) Wins the 1987 North American Computer Chess Championship. (IBM corporate history.)
- **1988.** The Deep Thought team (Hsu, Anantharaman, Campbell) wins the second Fredkin Intermediate Prize for sustained Grandmaster-level performance — a 2650+ rating across 25 consecutive USCF games. (Hsu 1999 p.70.)
- **1988-1991.** Deep Thought (CMU then IBM). Search speed ~700,000 positions/sec. (Hsu 1999 p.70 — "ChipTest (1986-1987), Deep Thought (1988-1991), and Deep Thought II (1992-1995) — claimed spots as the top chess programs in the world.")
- **1989.** Hsu and Campbell join IBM Research at the T. J. Watson Research Center in Yorktown Heights, NY, to develop Deep Thought's successor. IBM renames the project "Deep Blue." (Greenemeier 2017 SciAm Campbell interview, "in late 1989"; Newborn 2003 Ch.5 pp. 69-90; IBM corporate history.)
- **1989.** Kasparov plays a two-game exhibition match against Deep Thought in October and wins both games. (Newborn 2003 Ch. 5; Greenemeier 2017 SciAm Campbell interview.)

## Deep Blue Era

- **1992-1995.** Deep Thought II (also known as the Deep Blue prototype). Twenty-four chess engines, the same move-generator chip as Deep Thought but with medium-scale multiprocessing and enhanced evaluation hardware. (Hsu 1999 p.70 reference; Campbell, Hoane, Hsu 2002 paper §1.2 — slide-deck rendering verified, journal version pending.)
- **February 10-17, 1996.** First Kasparov-Deep Blue match, ACM Chess Challenge, Philadelphia. Deep Blue wins Game 1 (the first computer victory over a reigning world champion in regulation time controls). Kasparov wins the match 4-2 by adapting after Game 1. (Newborn 2003 Ch.6 pp. 91-112; Hsu 1999 p.71; IBM corporate history.)
- **1996-1997.** A new chess chip is designed. Joel Benjamin (US grandmaster) is hired as full-time consultant to tune the evaluation function and curate the opening book. (Greenemeier 2017 SciAm Campbell interview; Newborn 2003 Ch.8 pp. 119-126.)

## Rematch Logistics

- **April 1, 1997.** The new RS/6000 SP2 system, with the new VLSI chess chips and accelerator cards, is operational. (Newborn 2003 p.123.)
- **April 15, 1997.** System testing complete; code "frozen, in theory." (Newborn 2003 p.123.)
- **April 26, 1997.** Two-cabinet system loaded onto a truck and driven 100 miles from Poughkeepsie to the Equitable Center in midtown Manhattan. (Newborn 2003 p.123.)
- **April 28, 1997.** System running at the Equitable Center. Two backup systems set up: the Philadelphia-era 30-computer SP2 at Yorktown Heights, and a fast deskside RS/6000 workstation in the IBM operations room at the Equitable Center. (Newborn 2003 p.123.)

## The Rematch (May 3-11, 1997)

- **May 3, 1997 — Game 1.** Kasparov plays White; Réti / King's Indian Attack (ECO A07). Kasparov wins in 45 moves; Deep Blue's 44th move (Rxd3) is later confirmed as a known intermittent bug. Final move: 45.g7 1-0 (resignation). (Newborn 2003 Ch.10 pp. 139-152, especially p.150; Wikipedia game record citing Pandolfini 1997 p.65 and chessgames.com.)
- **May 4, 1997 — Game 2.** Deep Blue plays White; Ruy Lopez Smyslov Variation (ECO C93). 36.axb5 (selected via "panic time" search extension when 36.Qb6's evaluation was dropping); 37.Be4 (positional rather than material-grabbing). Kasparov resigns after 45.Ra6. Post-game analysis shows a draw was available via 45...Qe3 46.Qxd6 Re8 (perpetual check). After the game Kasparov accuses IBM of cheating. (Newborn 2003 Ch.11 pp. 153-166, especially pp. 159-160 quoting Bruce Weber NYT 5/13/97; Wikipedia game record.)
- **May 6, 1997 — Game 3.** Kasparov plays White; Mieses Opening / English (ECO A28). Drawn (½-½). (Newborn 2003 Ch.12 pp. 167-186.)
- **May 7, 1997 — Game 4.** Deep Blue plays White; Caro-Kann transposing to Pirc (ECO B07). Drawn. Kasparov in time trouble; sub-optimal moves may have cost him victory. (Newborn 2003 Ch.12.)
- **May 10, 1997 — Game 5.** Kasparov plays White; Réti / KIA (ECO A07). Drawn. Later analysis shows Kasparov had a win available beginning with 44.Rg7+. (Newborn 2003 Ch.12.)
- **May 11, 1997 — Game 6 (Mother's Day Sunday, NYC).** Deep Blue plays White; Caro-Kann Defence Steinitz Variation (ECO B17). Kasparov plays the Caro-Kann — an opening he had not used in formal tournament play since the early 1980s. On move 8, Deep Blue sacrifices a knight: 8.Nxe6. Kasparov resigns after 19.c4. The game is a "miniature," fewer than 20 moves. Final match score: Deep Blue 3.5, Kasparov 2.5. (Newborn 2003 Ch.13 pp. 187-206, especially pp. 205-206 for the final score; Hsu 1999 p.80; Wikipedia game record.)

## Aftermath

- **May 12, 1997.** *New York Times* coverage by Laurence Zuckerman ("Grandmaster sat at the chessboard, but the real opponent was Gates"). (Newborn 2003 ref [5].)
- **May 13, 1997.** *New York Times* coverage by Bruce Weber, "Mean Chess-Playing Computer Tears at the Meaning of Thought" — first reporting of the engineering account behind Deep Blue's Game 2 36th move. (Newborn 2003 ref [38]/[44]; cited inline at Newborn p.159-160.)
- **May 26, 1997.** Kasparov, "IBM Owes Me a Rematch," *Time* magazine, pp. 38-39. (Newborn 2003 ref [7].)
- **June 30, 1997.** Deep Blue team awarded $100,000 Fredkin Prize for the first computer to defeat a reigning world chess champion. (Loviglio, NYT 6/30/1997, per Newborn 2003 ref [3].)
- **September 23-24, 1997.** IBM announces Deep Blue's retirement from chess matches. (Phil Waga USA Today 9/23/1997; Grant McCool Reuters 9/24/1997 — Newborn 2003 refs [9-10].)
- **Later.** Deep Blue racks split — one rack reported to the Smithsonian Institution (Washington), one reported to the Computer History Museum (Mountain View). (Smithsonian intent attested at Newborn 2003 p.221-222; specific dual-museum disposition is Yellow.)
- **June 2, 2017.** Murray Campbell, in a *Scientific American* 20-year retrospective interview with Larry Greenemeier, confirms IBM declined Kasparov's rematch request because "we had achieved our goal" and explains the actual per-move position throughput as "between 100 million and 200 million positions per second, depending on the type of position."

## Pending Date Confirmations (Yellow)

- Exact month/day in 1989 of Hsu and Campbell's IBM hire ("late 1989" per Greenemeier 2017 SciAm; finer date not anchored).
- Exact date of Kasparov-Deep Thought 1989 exhibition match (Newborn 2003 attests "October 1989" but the precise date is not anchored in primary I've extracted).
- Specific 1996 Philadelphia game-by-game dates beyond the Feb 10-17 envelope.
- Exact Smithsonian and CHM accession dates for the two Deep Blue racks.
