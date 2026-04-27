# Sources: Chapter 12 - Logic Theorist and GPS

## Verification Key

- Green: claim has a primary source with verified page or section anchor, plus independent confirmation or a second primary/context source.
- Yellow: claim has one strong source, archive access is blocked, or the wording has unresolved attribution nuance.
- Red: claim should not be drafted yet.

Note: local shell `curl` was attempted from this worktree on 2026-04-27 and failed with DNS resolution errors under the current sandbox. Page anchors below were verified from browser-accessible PDF text extraction and local repository inspection, not from fabricated memory. Claims that could not be page-verified remain Yellow or Red.

## Primary Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| `P-868` | Allen Newell and Herbert A. Simon, "The Logic Theory Machine: A Complex Information Processing System," RAND P-868 / IRE Transactions on Information Theory IT-2(3), 1956. CMU PDF: https://iiif.library.cmu.edu/file/Simon_box00006_fld00406_bdl0001_doc0001/Simon_box00006_fld00406_bdl0001_doc0001.pdf | Core LT specification, symbolic representation, hand-simulation boundary, specification vs. realization distinction. | Green. Verified PDF anchors: p. 1 summary says LT discovers proofs in symbolic logic, is a formal pseudo-code specification, and is "not" yet the computer realization; p. 1 credits J. C. Shaw for realization work to be reported later; p. 3 says LT is small enough to be hand simulated "barely"; pp. 5-6 explain realization, digital computers, memory/speed limits, and a similar language being coded; pp. 7-16 define IPS/IPP, symbols, expressions, theorem/problem lists, working/storage memories, instructions, and routines. |
| `NSS57` | Allen Newell, J. C. Shaw, Herbert A. Simon, "Empirical Explorations of the Logic Theory Machine: A Case Study in Heuristic," Proceedings of the 1957 Western Joint Computer Conference, pp. 218-230. DOI: `10.1145/1455567.1455605`. | Needed for empirical theorem-count claims, JOHNNIAC run details, LT performance, Theorem 2.85, and stronger evidence for "programming by computer." | Yellow. Bibliographic and abstract metadata verified through ACM/CoLab/dblp pages, but full page text was not extracted in this sandbox. Do not mark "38 of 52" Green until this paper is obtained and searched. |
| `P-1584` | Allen Newell, J. C. Shaw, Herbert A. Simon, "A General Problem-Solving Program for a Computer," International Conference on Information Processing, Paris, 1959. CMU PDF: https://iiif.library.cmu.edu/file/Newell_box00039_fld03042_doc0001/Newell_box00039_fld03042_doc0001.pdf | GPS-I architecture, means-ends analysis, planning, task-environment separation, limits. | Green. Verified PDF anchors: p. 1 describes General Problem Solver I as a digital-computer program and states the synthetic method; p. 1 defines problem, heuristics, and empirical validity; p. 3 casts chess, theorem proving, integration, and programming as objects/operators problems; pp. 5-6 show planning abstraction; p. 6 explicitly says GPS has little task-environment information, needs special heuristics, and that realizing GPS-like programs is a major programming-language task involving IPL. |
| `GPS61` | Allen Newell and Herbert A. Simon, "GPS, A Program that Simulates Human Thought," in Heinz Billing, ed., *Lernende Automaten*, 1961; reprinted in *Computers and Thought*, 1963. CMU PDF: https://iiif.library.cmu.edu/file/Simon_box00064_fld04907_bdl0001_doc0001/Simon_box00064_fld04907_bdl0001_doc0001.pdf | GPS as psychological simulation, protocol method, recursive goal/subgoal structure, three goal types. | Green. Verified PDF anchors: p. 109 states GPS is a computer program developed from protocol data and used as a theory of human problem solving; p. 109 names General Problem Solver and its dual AI/psychology role; pp. 111-113 show the experimental symbolic-logic problem, rules, solution trace, and protocol; pp. 114-117 define the GPS task environment, objects, operators, differences, three goal types, recursive subgoals, feasibility tests, and table of connections. |
| `CBI91` | Arthur L. Norberg, oral history interview with Allen Newell, Charles Babbage Institute, 10-12 June 1991. PDF: https://conservancy.umn.edu/bitstreams/af365416-3c8c-400b-8411-d738275fa44a/download | Newell retrospective on RAND, Shaw, non-numerical computing, Selfridge trigger, Dartmouth, LT reception. | Green/Yellow. Green for Newell's retrospective statements: pp. 3-6 discuss RAND organizational simulations, Cliff Shaw, JOHNNIAC not yet available at the earliest phase, and non-numerical computing; p. 9 dates Selfridge conversion to mid-November 1954 and links it to arbitrary information/symbolic/adaptive processing; pp. 10-12 discuss Dartmouth, the field still unnamed before the conference, contacts with McCarthy/Minsky/Shannon, and the 1956-1957 reception of LT. Yellow for autobiographical memory as sole source for exact chronology. |
| `IPL-V` | Allen Newell et al., *Information Processing Language V Manual*, RAND P-1897, 1960. CMU PDF visible in search result: https://iiif.library.cmu.edu/file/Newell_box00003_fld00180_doc0001/Newell_box00003_fld00180_doc0001.pdf | List-processing infrastructure and later IPL context. | Yellow. Search-result PDF snippet verifies the manual and bibliography, but detailed page anchors were not extracted. Treat as tractable follow-up, not Green. |
| `Programming-LT` | Allen Newell and J. C. Shaw, "Programming the Logic Theory Machine," 1957 Western Joint Computer Conference, pp. 230-240. | Computer realization and IPL/list-processing mechanics for LT. | Yellow. Bibliographic metadata verified through dblp and `P-1584` references; full text not extracted. Needed before a rich JOHNNIAC/IPL scene is drafted. |
| `Simon-Models` | Herbert A. Simon, *Models of My Life*, BasicBooks, 1991. | Autobiographical account of hand simulation, Theorem 2.01, Theorem 2.85, JSL rejection, and GPS collaboration. | Yellow. Likely high-value but archive/physical-copy blocked in this sandbox. No page anchors verified. |
| `P-671` | Allen Newell, "The Chess Machine: An Example of Dealing with a Complex Task by Adaptation," RAND P-671, March 1955 (presented at WJCC 1955). | Intellectual bridge from RAND organizational simulations to symbolic search; primes the LT trajectory before the Selfridge trigger. Per Gemini gap audit 2026-04-27, the absence of P-671 makes the Selfridge moment look like an isolated epiphany rather than a turn within already-active conceptual work. | Yellow. RAND P-series PDF likely available; not extracted in this sandbox pass. Tractable follow-up. |
| `IPL-I/II/III` | Newell, Shaw, Simon, early Information Processing Language manuals (IPL-I drafted 1956; IPL-II implemented on JOHNNIAC 1956-57; IPL-III as the LT-era successor). | Correct IPL-version anchor for the actual LT JOHNNIAC implementation, distinct from the later IPL-V (1960) manual. Per Gemini gap audit 2026-04-27, citing only `IPL-V` for the 1956-57 LT runtime is a technical anachronism. | Yellow. Bibliographic metadata via secondary sources; primary RAND P-series PDFs not yet extracted. |

## Secondary Sources

| Source | Use | Verification |
|---|---|---|
| Computer History Museum timeline entry "Logic Theorist," 1955. URL: https://www.computerhistory.org/timeline/1955/ | Independent confirmation that Newell, Simon, and Shaw began work on LT and that it eventually proved 38 theorems from *Principia Mathematica*; also lists heuristics, list processing, and reasoning as search. | Yellow/Green split. Green only for CHM as institutional secondary context; Yellow for theorem-count drafting because the primary `NSS57` page anchor is still pending. |
| AITopics / AAAI "Computers and Thought" metadata. URL: https://aitopics.org/doc/classics%3AF433B66A | Confirms the *Computers and Thought* table of contents includes LT and GPS chapters and page ranges in the classic anthology. | Green for bibliographic context only; not a load-bearing claim source. |
| Pamela McCorduck, *Machines Who Think* (1979 / 2004). | Narrative detail on Newell-Simon-Shaw, hand simulation, Dartmouth reaction, and attribution conflicts. | Yellow. Physical/page access blocked. Use only after pages are pulled. |
| Daniel Crevier, *AI: The Tumultuous History of the Search for Artificial Intelligence* (1993). | Secondary cross-check for LT, GPS, and first-AI-program boundary claims. | Yellow. Physical/page access blocked. |
| Nils J. Nilsson, *The Quest for Artificial Intelligence* (2010). | Academic history of early symbolic AI, LT, and GPS limits. | Yellow. Page anchors pending. |
| Hubert Dreyfus, *What Computers Can't Do* (1972). | Later critique of GPS-style claims and symbolic generality. | Yellow. Use only for conflict framing after exact pages are obtained. |
| Roger Schank commentary on GPS limits. | Possible conflict source on GPS generality and cognitive realism. | Red until a specific source is identified. |
| Edward Feigenbaum, "The Simulation of Verbal Learning Behavior" (EPAM), 1959/1961. | Direct descendant of the Newell-Simon-Shaw symbolic architecture extended to perception/memory; evidence the symbolic approach was not just for logic. Per Gemini gap audit 2026-04-27. | Yellow. Tractable Should-add for the chapter's "Information Processing Psychology breadth" beat. |
| Robert Lindsay, "Inferential Memory as the Basis of Machines Which Understand Natural Language" (SAD-SAM), 1958. | Competing 1958 symbolic-AI claim applying list-processing to natural language; challenges the uniqueness of the Carnegie/RAND trajectory. Per Gemini gap audit. | Yellow. Tractable Should-add for field context around the GPS Paris presentation. |
| Philip Stone et al., *The General Inquirer*, 1960s. | Contemporary non-AI symbolic system; clarifies what made GPS's means-ends analysis distinct from general list-processing utilities. Per Gemini gap audit. | Yellow. Tractable Should-add for the "Generality Ceiling" scene. |
| STRIPS / Project MAC GPS-derivative planning systems (Fikes & Nilsson 1971+). | Migration of GPS architecture out of Carnegie/RAND ecosystem; forward-link for the Generality Ceiling scene. Per Gemini gap audit. | Yellow. Belongs more in Ch20 (Project MAC) but a brief forward-link strengthens this chapter's close. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| `P-868` specifies a system called the Logic Theory Machine capable of discovering proofs in symbolic logic. | 1, 2 | `P-868`, p. 1 | CHM timeline; AITopics metadata | Green | Safe core claim. |
| The 1956 LT paper is explicitly a specification paper and not yet the report of computer realization. | 1 | `P-868`, p. 1 | `CBI91`, pp. 9-12 | Green | Important boundary against premature machine-room prose. |
| J. C. Shaw is credited in `P-868` for undertaking the computer realization work to be reported later. | 1 | `P-868`, p. 1 | `P-1584`, references to LT programming work | Green | Supports Shaw as infrastructure figure, not a footnote. |
| LT was small enough to be hand simulated, but only barely. | 1 | `P-868`, p. 3 | `CBI91`, pp. 9-10 for Newell's process context | Green | Typewriter/Theorem 2.01 details remain Yellow. |
| The LT representation uses symbols, expressions, working memories, storage memories, theorem/problem lists, instructions, and routines. | 2 | `P-868`, pp. 7-16 | `P-1584`, p. 1 for later description of LT as symbolic proof discovery | Green | Strong enough for a pedagogical scene. |
| LT relied on heuristic methods rather than a fixed algorithmic proof procedure. | 2 | `P-868`, pp. 2-3 | `P-1584`, p. 1 | Green | Avoid overclaiming mathematical power; this is a heuristic-search claim. |
| The high-speed digital computer mattered as realization infrastructure, with limits in speed and memory rather than the complexity of processes it could realize. | 1, 5 | `P-868`, pp. 5-6 | `CBI91`, pp. 5-6 | Green | Good bridge to JOHNNIAC/IPL, but exact machine run remains Yellow. |
| Newell's pathway into LT came through RAND, organizational simulations, non-numerical computing, Shaw, and a Selfridge-triggered turn toward symbolic/adaptive processing. | 1 | `CBI91`, pp. 3-9 | `P-868`, pp. 5-6 | Green | Autobiographical; use as retrospective, not omniscient narration. |
| Before Dartmouth, the community did not yet have a settled field label; Newell later recalled that "AI" became the name at Dartmouth. | 3 | `CBI91`, pp. 10-12 | Ch11 sources | Green/Yellow | Green for Newell's recollection; Yellow for broader naming history, handled in Ch11. |
| GPS-I is described in 1959 as a digital-computer program for investigating intelligent, adaptive, and creative behavior by synthesis. | 4 | `P-1584`, p. 1 | `GPS61`, p. 109 | Green | Safe GPS opening. |
| GPS frames problem solving around imperfect knowledge, heuristics, and empirical rather than infallible guidance. | 4 | `P-1584`, p. 1 | `GPS61`, pp. 114-117 | Green | Useful for explaining why GPS was not an algorithmic guarantee. |
| GPS formalizes task environments in terms of objects, operators, differences, goals, subgoals, and recursive methods. | 4 | `GPS61`, pp. 114-117 | `P-1584`, pp. 3-6 | Green | Core means-ends-analysis anchor. |
| GPS separates problem-solving method from task content more than LT did, but still requires task-specific representations and correlative definitions. | 4, 5 | `P-1584`, pp. 3-6; `GPS61`, pp. 114-117 | `P-1584`, p. 6 | Green | This is the architecture-vs.-generality boundary. |
| GPS's practical limits include special heuristics, evaluation, information handling, and programming-language infrastructure. | 5 | `P-1584`, p. 6 | `GPS61`, pp. 114-117 | Green | Strong anti-hype close. |
| LT proved 38 of the first 52 theorems in Chapter 2 of *Principia Mathematica*. | 2 | `NSS57` pending | CHM timeline; McCorduck/Crevier/Nilsson likely | Yellow | Do not draft as Green until `NSS57` page anchor is extracted. |
| LT's proof of Theorem 2.85 was cleaner than Whitehead and Russell's and the JSL paper was rejected. | 2 | `Simon-Models` or `NSS57` pending | McCorduck/Crevier likely | **Red** (demoted from Yellow per Gemini gap audit 2026-04-27) | Folklore-prone; the "JSL rejection as Luddite establishment" narrative is contested — historical accounts suggest the rejection was for technical not ideological reasons. Drafting this without the exact text of the rejection or a primary citation risks perpetuating a biased narrative. Demoted to Red until a primary anchor is found; do not draft a load-bearing scene. |
| The first successful hand proof was Theorem 2.01 and was typewriter-driven. | 1 | `Simon-Models` pending | `P-868`, p. 3 only supports hand simulation generally | Yellow | Include only as a worklist item, not a scene detail yet. |
| LT ran on JOHNNIAC in mid-1956 in IPL. | 1, 5 | `Programming-LT` / `NSS57` pending | CHM and secondary sources likely | Yellow | `P-868` says realization work was later; exact run date and machine need primary page anchor. |
| LT was the first AI program, full stop. | 3 | None | Conflicts with McCulloch-Pitts/Samuel/Strachey boundary | Red | Forbidden framing. Use "first running symbolic-AI program" only with care. |
| GPS was a working general intelligence. | 5 | None | `P-1584`, p. 6 undercuts this | Red | Forbidden framing. |
| Dartmouth attendees saw LT execute live on a Dartmouth computer. | 3 | None | Ch11 infrastructure notes say no shared computer | Red | Do not draft. Describe demonstration/discussion unless primary evidence says otherwise. |

## Conflict Notes

- **First-AI-program claim:** The safest wording is "first running symbolic-AI program," not "first AI program." The latter collides with neural, game-playing, and simulation histories.
- **Hand trace vs. computer run:** `P-868` is explicit that the June/September 1956 paper reports the specification, not the computer realization. Any JOHNNIAC/IPL machine-run scene needs `NSS57` or `Programming-LT`.
- **Theorem counts:** The familiar "38 of 52" claim is plausible and secondarily confirmed, but this contract does not mark it Green because the primary page anchor was not extracted.
- **Theorem 2.85 and JSL rejection:** Treat as a vivid but currently Yellow story. It should not become the chapter's centerpiece until exact page evidence is found.
- **GPS generality:** GPS's name invites overclaiming. `P-1584` and `GPS61` both show the architecture was general only through supplied vocabularies, operator definitions, methods, evaluation, and task-specific representations.

## Page Anchor Worklist

### Done

- `P-868`: Done for title/date, specification vs. realization, Shaw credit, hand-simulation boundary, symbolic-representation machinery, memory/list structures, theorem/problem lists, and digital-computer realization constraints.
- `P-1584`: Done for GPS-I as a digital-computer program, heuristics, objects/operators framing, planning, task-content separation, and programming-language/information-handling limits.
- `GPS61`: Done for GPS as human-problem-solving simulation, protocol method, three goal types, recursive subgoals, and means-ends methods.
- `CBI91`: Done for Newell's retrospective on RAND, Shaw, non-numerical computing, Selfridge, Dartmouth contacts, and LT reception.
- Ch11 cross-link: Done at contract level; Ch11 Scene 3 already carries the Dartmouth/LT bridge as Yellow.

### Tractable

- `NSS57`: Obtain full text and extract theorem-count, Theorem 2.85, empirical performance, and JOHNNIAC/IPL details.
- `Programming-LT`: Obtain full text and extract IPL/list-processing implementation mechanics.
- `IPL-V`: Extract pages on list structures and RAND/JOHNNIAC implementation context.
- AITopics *Computers and Thought* PDF: If accessible outside the quick-check gate, extract anthology pages for LT and GPS reprint context.

### Archive-blocked

- `Simon-Models`: Physical/scan access needed for Theorem 2.01, Theorem 2.85, and JSL rejection.
- McCorduck, Crevier, Nilsson: physical or library scans needed for secondary page anchors.
- RAND/CMU archival correspondence: needed for exact hand-demo, Dartmouth, and JOHNNIAC chronology.
