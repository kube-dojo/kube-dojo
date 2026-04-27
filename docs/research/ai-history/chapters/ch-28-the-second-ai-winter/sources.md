# Sources: Chapter 28 - The Second AI Winter

## Verification Legend

- Green: source is strong enough for drafting the stated claim with recorded page anchors.
- Yellow: source is relevant but needs another anchor, access check, or cautious wording.
- Red: claim should remain out of prose until sourced.

## Primary and Near-Primary Sources

| Source | Use | Verification |
|---|---|---|
| Navaratna S. Rajaram, ["Tools and Technologies for Expert Systems: A Human Factors Perspective"](https://ntrs.nasa.gov/citations/19880005500), NASA/JSC Summer Faculty Program final report, 1987. | Period NASA view of expert systems as promising but not mature; knowledge-acquisition bottleneck and technology-transfer problem. | Green. Abstract on report p.26-2 says expert systems can help knowledge-intensive organizations but are new technologies with transfer problems; report p.26-14 calls expert systems a "technology in transition" and defines the knowledge-acquisition bottleneck as the gap between AI technologists and domain specialists. |
| Gerald L. Atkinson, ["Technology Transfer Using Automated Knowledge-Acquisition Tools"](https://cdn.aaai.org/IAAI/1990/IAAI90-013.pdf), *IAAI-90 Proceedings*, AAAI, 1990, pp.159-176. | Period applied-AI account showing expert systems in defense technology transfer while admitting acquisition bottlenecks. | Green. pp.159-160 set up defense hardening as a scarce-expertise transfer problem; p.161 says first-generation expert systems depended on discourse between knowledge engineer and expert, that tacit heuristics are hard to verbalize, and that knowledge acquisition remained the major stumbling block during the 1980s. |
| Bernd Neumann, ["Configuration Expert Systems: A Case Study and Tutorial"](https://kogs-www.informatik.uni-hamburg.de/publikationen/pub-neumann/Neumann88.pdf), in Horst Bunke, ed., *Artificial Intelligence in Manufacturing, Assembly and Robotics*, Oldenbourg, 1988, pp.27-68. | XCON as both success and maintenance warning; large rule-base complexity and rule-order/intelligibility problems. | Green. p.27 summary says configuration systems suggested knowledge-based architectures different from conventional rule-based systems; pp.34-35 describe XCON configuring DEC orders; p.34 says it contained more than 6,200 rules over ~20,000 parts and about half the rules were expected to change each year; pp.36-37 say developers found it increasingly difficult to ensure rule firing order and that rule-language control mismatch became significant in large systems. |
| Alex Roland and Philip Shiman, [*Strategic Computing: DARPA and the Quest for Machine Intelligence, 1983-1993*](https://gwern.net/doc/cs/hardware/2002-roland-strategiccomputing-darpaandthequestformachineintelligence19831993.pdf), MIT Press, 2002. | DARPA Strategic Computing expectation correction, FGCS as Western trigger, program cuts, shift from AI toward architectures/HPC. | Green as a commissioned historical study with extensive primary interviews/records. p.5 says Japan's Fifth Generation program fueled U.S. concerns over computer/defense technology competitiveness; p.37 says MITI's 1981 Fifth Generation announcement promised machines capable of human intelligence and raised alarms about U.S. leadership; pp.56-57 say Japan was the spending rationale, DeLauer was exercised by FGCS, and Congress gave the proposal a warm reception but wanted a clear sellable plan. pp.274-276 describe Schwartz's view that AI was promising but not ripe, algorithms did not scale, and AI/robotics budgets fell from $47M in 1987 to under $31M by 1989; p.276 records expert-system funding cut from $5.2M in 1988 to $3M by 1990; pp.279-281 describe congressional pressure for products and SC2's maturity/producer-consumer strategy; p.285 says SC vanished as a DARPA line item in 1993 and was transmuted into HPC, leaving behind the failed promise of AI. |
| Institute for New Generation Computer Technology (ICOT), ed., [*Fifth Generation Computer Systems 1992: Proceedings of FGCS'92, Volume 1*](https://www.bitsavers.org/pdf/icot/Fifth_Generation_Computer_Systems_1992_Volume_1.pdf), Ohmsha/IOS Press, 1992. | Japanese FGCS final context: goals, knowledge processing, parallel inference machines, international expectation and evaluation. | Green/Yellow. Foreword pp.iii-iv says FGCS began in 1982 to build knowledge-processing computers for the 1990s, developed KL1 and PIM, and presented final ten-year results at FGCS'92; MITI foreword p.v says formal evaluation would follow and claims spectacular research results in parallel inference hardware/software. Use for stated goals/final-results context, not as independent proof of impact. |
| James Bates, ["Symbolics Lays Off 90 at Plant in Chatsworth"](https://www.latimes.com/archives/la-xpm-1988-05-24-fi-3053-story.html), *Los Angeles Times*, May 24, 1988. | Business-press anchor for the specialized AI hardware market correction. | Green for Symbolics scene. Article reports Symbolics laid off 225 of 640 workers nationwide, expected $15M annual savings, had dropped from more than 1,000 employees to slightly more than 400, was hurt by less expensive Sun/Apollo workstations, lost $4.9M in the quarter ending April 3, 1988, and lost $24.8M over nine months on $65.2M revenue. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| James Hendler, ["Avoiding Another AI Winter"](https://doi.org/10.1109/MIS.2008.20), *IEEE Intelligent Systems* 23(2), 2-4, 2008. | Retrospective "perfect storm" framing: earlier funding cuts, expert-system commercialization consuming older research, research-community disavowal, and commodity machines killing the Lisp-machine market. | Yellow. Use as retrospective synthesis only. Source is stable via IEEE DOI; local PDF extraction was not completed in this pass. |
| Pamela McCorduck, *Machines Who Think*, 2nd ed., A.K. Peters, 2004. | Narrative context for public expectations around expert systems and AI winters. | Yellow. Useful for color and cross-checking, not primary claim support unless page anchors are added. |
| Daniel Crevier, *AI: The Tumultuous History of the Search for Artificial Intelligence*, Basic Books, 1993. | Contemporary narrative of the 1980s boom and early-1990s contraction. | Yellow. Add page anchors before using in prose. |

## Scene-Level Claim Table

| Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|
| XCON was a successful but maintenance-heavy expert system, not a fake achievement. | Successful Warning Sign | Neumann 1988 pp.34-37 | Green | Use the 6,200 rules, ~20,000 parts, annual half-rule churn, and rule-order difficulty as the central concrete example. |
| Knowledge acquisition, not just inference speed, became a bottleneck for expert systems. | Knowledge Acquisition Bottleneck | Rajaram 1987 p.26-14; Atkinson 1990 p.161 | Green | Frame as tacit heuristics and communication gap between domain expert and knowledge engineer. |
| DARPA's late-1980s AI retreat came from scaling skepticism and demand for measurable transition, not a blanket belief that AI was impossible. | Demonstration Trap | Roland/Shiman pp.274-276, 279-281 | Green | Preserve nuance: Schwartz believed AI was possible but not ripe; speech/NavLab/neural modeling saw selective support. |
| Strategic Computing disappeared into high-performance computing by 1993. | Winter as Reallocation | Roland/Shiman p.285 | Green | Useful transition to infrastructure thesis: winter reallocates resources rather than freezing all compute. |
| FGCS amplified U.S./Western expectations and helped sell Strategic Computing as a response to Japanese competition. | Fifth Generation Shadow | Roland/Shiman pp.5, 37, 56-57 | Green | This fixes the external-trigger gap: use Roland/Shiman, not ICOT, for U.S. concern and political leverage. |
| FGCS's own final proceedings frame the project as research/prototype achievements in knowledge processing and parallel inference. | Fifth Generation Shadow | FGCS 1992 pp.iii-v | Green/Yellow | Use only for official stated goals and final-results context; do not claim "FGCS failed" from ICOT proceedings alone. |
| Specialized AI hardware economics visibly deteriorated in 1988. | Hardware Economics | Bates 1988, LA Times | Green | Use Symbolics as one concrete business scene; do not generalize every vendor's bankruptcy timeline from it. |
| The broader Lisp-machine market collapse was a key economic factor in the second winter. | Hardware Economics | Hendler 2008; Bates 1988 | Yellow/Green | Green for Symbolics; Yellow for whole-market claims unless another source is added. Phrase as Symbolics-specific plus broader secondary context. |

## Conflict Notes

- Do not claim expert systems were useless; the strongest examples were valuable in bounded domains.
- Do not claim hype alone caused the winter; funding priorities, maintenance economics, hardware commoditization, and lack of scalable concepts all mattered.
- Do not transfer XCON's numbers to all expert systems.
- Do not treat FGCS as an outright failure unless a source specifically supports the claim and defines the metric.
- Do not rely on ICOT alone for Western reaction to FGCS; use Roland/Shiman for U.S. concern and political leverage.
- Do not overstate the winter as an end of AI research; Roland/Shiman show selective DARPA movement toward speech, neural modeling, machine learning, benchmarks, architectures, and HPC.

## Page Anchor Worklist

- Add a second business source for the broader Lisp-machine market only if prose wants to generalize beyond Symbolics.
- Add page anchors from Crevier or McCorduck only if used for narrative color.
- Gemini gap analysis approved the contract after requesting a Symbolics hardware-economics anchor; the LA Times anchor now covers that gap.
- Claude requested an external FGCS trigger anchor; Roland/Shiman pp.5, 37, and 56-57 now cover that gap.
