# Infrastructure Log: Chapter 10 — The Imitation Game

Technical and institutional metrics relevant to the chapter's infrastructure-history thesis. Each row is what made the Imitation Game *operationally* meaningful (or what its operational limits were). Verification colors are tracked because infrastructure claims that look like throwaway facts are often the ones secondary sources copy from each other without primary evidence.

## The Test Apparatus (as Turing actually specified it)

| Item | Value | Verification |
|---|---|---|
| Number of rooms | Three: one for the interrogator (C), one for player A, one for player B. C is in a separate room from A and B. | **Green** — Mind 1950 §1, p. 433. Verified by `pdftotext` (Claude 2026-04-28). |
| Communication channel | Typed messages, "or better still, typewritten." Turing names "the ideal arrangement" as "a teleprinter communicating between the two rooms." Alternatively, an intermediary may relay questions and answers. | **Green** — Mind 1950 §1, p. 433. Verified. |
| Why typed and not voice | "In order that tones of voice may not help the interrogator." | **Green** — Mind 1950 §1, p. 433. Verified — direct quotation. |
| Why no visual contact | The §2 critique decouples physical and intellectual capacities; the design "prevents the interrogator from seeing or touching the other competitors, or hearing their voices." | **Green** — Mind 1950 §2, p. 434. Verified — direct quotation. |
| Original (gender) game | C tries to determine which of A and B is the man and which is the woman. A's object is to make C identify wrongly; B's object is to help C identify correctly. | **Green** — Mind 1950 §1, p. 433. Verified. |
| Machine-substituted game | A is replaced by a machine. The question becomes: does C identify wrongly as often as in the original gender game? | **Green** — Mind 1950 §1, p. 434. Verified. |
| Pass/fail criterion as Turing states it | Not a binary pass/fail. The §6 prediction states a quantitative threshold: an "average interrogator" should not have "more than 70 per cent chance of making the right identification after five minutes of questioning." | **Green** — Mind 1950 §6 opening, p. 442. Verified by `pdftotext` (Claude 2026-04-28) and cross-confirmed by Saygin et al 2000 §2.4 (pp. 472-473). |

## Storage Capacity Estimates and Predictions

| Item | Value | Verification |
|---|---|---|
| Turing's 1947 estimate of human-brain memory | "of the order of ten thousand million binary digits" — i.e. ~10¹⁰ bits | **Green** — 1947 LMS lecture (seminarTEXT pp. 12-13 / Carpenter & Doran 1986). Verified by `pdftotext` (Claude 2026-04-28). |
| Turing's 1947 estimate of useful working memory for limited intelligence | "a few million digits" — i.e. ~10⁶-10⁷ bits — for tasks like chess | **Green** — 1947 LMS lecture (seminarTEXT pp. 12-13). Verified. |
| ACE mercury-delay-line storage capacity | "about 200,000 binary digits" total Hg-delay-line storage; "probably comparable with the memory capacity of a minnow." Each 5-foot mercury tube stored 1024 binary digits. | **Green** — 1947 LMS lecture (seminarTEXT p. 6). Verified by `pdftotext` (Claude 2026-04-28). |
| Turing's 1950 prediction of machine storage adequate for the game | "about 10⁹" binary digits | **Green** — Mind 1950 §6 opening, p. 442. Doubly verified — `pdftotext` + Saygin 2000 cross-citation. |
| Turing's 1950 estimate of human-brain storage range | "from 10¹⁰ to 10¹⁵ binary digits"; Turing inclines to the lower values; "most of it is probably used for the retention of visual impressions" | **Green** — Mind 1950 §7, p. 455. Verified. |
| Turing's 1950 lower bound for satisfactory blind-machine play | "I should be surprised if more than 10⁹ was required for satisfactory playing of the imitation game, at any rate against a blind man" | **Green** — Mind 1950 §7, p. 455. Verified. Note the qualifier "against a blind man." |
| 1950 reference point | "(Note: The capacity of the *Encyclopaedia Britannica*, 11th edition, is 2 × 10⁹)" | **Green** — Mind 1950 §7, p. 455. Verified — direct parenthetical. |
| Turing's 1950 estimate of practicable storage by 1950 standards | "A storage capacity of 10⁷ would be a very practicable possibility even by present techniques." | **Green** — Mind 1950 §7, p. 455. Verified. |
| Turing's 1950 estimate of programming labour to build the imitation player | "At my present rate of working I produce about a thousand digits of programme a day, so that about sixty workers, working steadily through the fifty years might accomplish the job, if nothing went into the wastepaper basket. Some more expeditious method seems desirable." | **Green** — Mind 1950 §7, pp. 455-456. Verified. Useful for showing that Turing thought of the test as a multi-decade engineering problem, not a near-term demo. |

## Computing Substrate Available to Turing 1947-1952

| Machine | Status during the chapter window | Verification |
|---|---|---|
| ACE (Automatic Computing Engine), NPL | Designed by Turing 1945-1947; Pilot ACE not operational until May 1950. The 1947 LMS lecture is *about the ACE design*, not about a running machine. | **Green** for the 1947 lecture being ACE-focused — verified via the lecture text. The May 1950 Pilot ACE first-run date is widely standard but not directly verified by Claude. |
| Manchester Mark 1 / Manchester Baby | The Manchester Baby ran its first program 21 June 1948 (out of scope, Ch9 territory); the Manchester Mark 1 was operational by 1949. Turing was at Manchester from late 1948. The 1950 *Mind* paper references "the Manchester machine" by storage capacity in §5: 2560 wheels with 1280-digit capacity each... | **Green** — Mind 1950 §5 references the Manchester machine's storage parameters, p. ~441. Verified. |
| Newell-Simon Logic Theorist | Did not exist during this chapter's window — first appeared in 1955-1956 (Ch11/Ch12 territory). | Out of scope. |
| Universal-machine model | Theoretical reference frame the chapter inherits from Ch2; the 1948 NPL report and the 1950 *Mind* §3-§5 both rely on it. | **Green** for textual references in NPL 1948 and Mind 1950; theoretical territory (Ch2). |

## The Test as Operational Specification — What It Demands and What It Allows

These are the infrastructure constraints the chapter should foreground when explaining the Imitation Game's design choices:

- **No video, no audio, no haptic.** The teleprinter constraint is the test's load-bearing operational decision. It is *what* makes the test about symbolic-linguistic intelligence rather than about humanoid mimicry. (Mind §1 p. 433; §2 p. 434.)
- **Three-room separation.** C is in a different room from A and B; A is in a different room from B. The original gender game already has this structure; the machine-substituted game inherits it. (Mind §1 p. 433.)
- **Time-limited interrogation.** "Five minutes of questioning" is Turing's named bound in the §6 prediction. He does not specify five minutes as the test's general time bound — only as the bound at which his year-2000 prediction kicks in. (Mind §6 p. 442.)
- **Quantitative threshold, not binary verdict.** The 70% / five-minute threshold is a frequency claim about a population of average interrogators, not a single-trial pass/fail. The chapter must not present "the Turing Test" as a single-trial binary test — that is a popular reading, not Turing's. (Mind §6 p. 442.)
- **No real-time machine demo required for Turing's argument.** The 1950 paper is explicitly an *argument*, not a demonstration. Turing names the sixty-workers-fifty-years estimate (§7 p. 455-456) precisely to acknowledge that adequate machines did not yet exist. The Imitation Game is a test the future would administer; Turing's contribution is the protocol, not its execution.
- **Backward compatibility with the 1948 chess experiment.** The two-room chess proto-imitation experiment (NPL 1948 inner p. [13]) is operationally a degenerate case of the 1950 game — A=human, B=paper machine, C=observer guessing which is which. The 1948 setup uses domain-specific play (chess) as the test medium; the 1950 setup generalises to free conversation via teleprinter. The continuity is operational, not just rhetorical.

## Operational Limits Worth Naming in Prose

- **No 1950-vintage machine could play the game.** Mind §7 pp. 454-456 acknowledges the storage and programming-labour gap explicitly. The chapter must not gloss over this — it is part of why Turing offered the test as an *evaluation protocol* rather than a *working demonstration*.
- **The ACE was a paper design at the 1947 lecture.** Turing was lecturing on a machine that did not yet exist as built hardware. (The Pilot ACE first ran in May 1950.) This is part of the lecture's intellectual force — Turing was reasoning about what machines *of this kind* would and would not be able to do, not what any specific running machine had done.
- **No shared programming language for AI in 1947-1952.** LISP did not exist until 1958. Each researcher worked in their own conventions — Turing's "instruction tables" in 1947 LMS, paper-machine simulations in the 1948 NPL chess experiment. There was no medium for the kind of collaborative test-bed development the §7 child-machine programme would have required.

## Notes

- Several "infrastructure facts" frequently repeated in tertiary sources (e.g., "Turing predicted 125 megabytes of memory by 2000" or "Turing said the test takes five minutes") collapse into the *more specific* §6 prediction, where 10⁹ bits and five minutes are coupled to the year-2000 timeframe and to a 70% interrogator-error rate. Infrastructure-log claims should stay narrowly accurate — the test, as Turing wrote it, is a four-parameter operational specification, not a one-line slogan.
- The 1948 chess proto-experiment's specific test parameters (number of games, length of each game, criteria for declaring C confused) are not given in the NPL report. The chapter should not invent values.
