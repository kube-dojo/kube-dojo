# Sources: Chapter 21 - The Rule-Based Fortune

## Source Table

| Source | Type | Anchor | Use | Status |
|---|---|---|---|---|
| John McDermott, [*"R1: A Rule-Based Configurer of Computer Systems"*](https://web.cs.wpi.edu/Research/aidg/CS540/papers/McDermott-R1-XCON.pdf), *Artificial Intelligence* 19, 1982, pp.39-88 | Primary technical paper / scanned PDF OCR | pp.39-40, 41-42, 45-46, 58, 64-66, 68-70 | Core technical description of R1, VAX configuration task, production rules, Match, rule counts, development history, validation, manufacturing integration | Green |
| John McDermott and Barbara Steele, [*"Extending a Knowledge-Based System to Deal with Ad Hoc Constraints"*](https://www.ijcai.org/Proceedings/81-2/Papers/047.pdf), IJCAI 1981, pp.824-828 | Primary conference paper | pp.824-828 | XSEL/R1 relationship, customer-specific constraints, OPS5, 850 rules, "almost all VAX-11 systems shipped," 15-person maintenance group, 20 commands, 87 command-recognition rules | Green |
| John McDermott and Judith Bachant, [*"R1 Revisited: Four Years in the Trenches"*](https://studylib.net/doc/13831835/ri--revisited--judith--bachant-john--mcdermott), *AI Magazine* 5(3), Fall 1984, pp.21-32 | Primary deployment/maintenance retrospective; AI Magazine PDF mirror locally extracted | pp.21-32 | Four-year production use, rule/data-base growth, DEC organization, testing/release process, performance data, 80,000 orders, maintenance conclusions | Green |
| Reid G. Smith, [*"On the Development of Commercial Expert Systems"*](https://ngds.egi.utah.edu/files/GL01352/GL01352.pdf), *AI Magazine* 5(3), Fall 1984, pp.61-73 | Primary/in-period commercial expert-system reflection; scanned PDF compilation | pp.61-73 | Broader commercial expert-system context: real problem vs demo, domain experts, knowledge engineering, rapid prototyping, technology transfer, progressive releases | Green |
| Reid G. Smith, [personal bibliography entry for "On the Development of Commercial Expert Systems"](https://www.reidgsmith.com/) | Author bibliography / source-discovery check | 1984 section | Confirms bibliographic metadata for Smith 1984 article | Yellow |
| AAAI AI Magazine bibliography, [Volume 5, Issue 3 listing](https://auld.aaai.org/Magazine/bibliography.php) | Publisher bibliography / source-discovery check | Fall 1984 issue listing | Confirms McDermott/Bachant and Smith AI Magazine issue placement and page ranges | Yellow |
| John McDermott, [*"R1 ('XCON') at Age 12: Lessons from an Elementary School Achiever"*](https://doi.org/10.1016/0004-3702(93)90192-E), *Artificial Intelligence* 59(1-2), 1993, pp.241-247 | Later retrospective | DOI/metadata only; full text not extracted | Potential stretch unlock for later XCON lessons; do not use for factual prose until full text is available and parsed | Red |

## Claim Matrix

| Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|
| R1 configured VAX-11/780 systems from customer orders, added missing components when needed, and produced diagrams used for physical assembly. | Factory Problem | McDermott 1982 pp.39-40 | Green | Keep "VAX-11/780" precise for the 1982 paper. |
| In 1982 R1 was in regular use by DEC manufacturing and implemented as a production system using Match, with enough domain knowledge to recognize what to do with little search. | Rules That Recognize | McDermott 1982 p.39 | Green | Avoid turning this into general intelligence. |
| VAX configuration was nontrivial because the architecture permitted many system variations and peripheral combinations. | Knowledge as Constraints | McDermott 1982 p.41 | Green | Use to justify why configuration deserved expert-system treatment. |
| A VAX configurer needed about eight properties for each of roughly 420 supported components, yielding over 3300 pieces of component information. | Knowledge as Constraints | McDermott 1982 p.41 | Green | Exact figures from OCR; article page 41. |
| McDermott extracted 480 rules from experts: 96 for initiating subtasks and 384 for extending partial configurations. | Knowledge as Constraints | McDermott 1982 p.42 | Green | Good concrete anchor for "knowledge engineering." |
| Many configuration constraints had an ad hoc flavor and were not easily derived from general knowledge. | Knowledge as Constraints | McDermott 1982 p.42 | Green | This is a key anti-hype sentence. |
| R1 was implemented in OPS4; productions consisted of conditions and actions operating over working memory in a recognize-act cycle. | Rules That Recognize | McDermott 1982 p.45 | Green | Technical exposition should stay readable. |
| R1's domain-specific knowledge, including control knowledge, was in productions; each rule embodied a piece of constraint knowledge. | Rules That Recognize | McDermott 1982 p.45 | Green | Explains why rules are not just if/then trivia. |
| OPS4 interpreting R1 had an average cycle time of about 150 milliseconds, and R1 had 772 rules in the 1982 account. | Rules That Recognize | McDermott 1982 p.46 | Green | Use only if runtime texture helps. |
| Of R1's 772 rules, 480 were directly configuration-related and 292 were more general; domain rules covered context generation, prerequisites, association, retrieval, and computation. | Rules That Recognize | McDermott 1982 p.58 | Green | Good for source-backed taxonomy, but avoid list padding. |
| In 20 sample runs, only about 40-50 percent of available knowledge was required on a particular order, with average configuration runtime about 1.76 CPU minutes excluding output. | Rules That Recognize / Deployment | McDermott 1982 pp.64-66 | Green | Useful for explaining sparse rule use and practical runtime. |
| R1 development began in December 1978; after five or six days of tutoring and manuals, an initial version under 200 domain rules handled simple orders but failed on complex ones. | Knowledge Engineering | McDermott 1982 p.68 | Green | Strong narrative scene. |
| The second development stage used expert examination of output; R1's domain knowledge almost tripled, and exceptional cases proved hard for experts to produce on demand. | Knowledge Engineering | McDermott 1982 pp.68-69 | Green | Explains the knowledge-acquisition bottleneck in industrial form. |
| Rule splitting/context spawning made refinement relatively straightforward, with negative side effects usually confined to related contexts. | Knowledge Engineering | McDermott 1982 p.69 | Green | Balance with later maintenance burden. |
| Formal validation in October-November 1979 used 50 orders and six experts spending one to two hours per order; 12 pieces of errorful knowledge were found and fixed. | Knowledge Engineering / Deployment | McDermott 1982 pp.69-70 | Green | Avoid saying "perfect"; it passed a validation process. |
| After validation R1 was integrated into manufacturing, used to produce configuration descriptions before assembly, and began same-day screening at regional field offices. | Into DEC Manufacturing | McDermott 1982 p.70 | Green | This is the deployment bridge. |
| McDermott and Steele state that since January 1980 R1 had been used by DEC manufacturing to configure almost all VAX-11 systems shipped, and DEC had 15 people maintaining/extending it. | Into DEC Manufacturing | McDermott/Steele 1981 p.824 | Green | Use carefully: "VAX-11 systems" in that paper, not all DEC systems. |
| XSEL was under development as a sales assistant; it selected a skeletal order and passed it to R1 for fleshing out and configuration. | Advice, Customers | McDermott/Steele 1981 pp.824-825 | Green | Keep XSEL separate from R1/XCON. |
| R1 was not initially designed for customer-specific constraints, but the authors added a relatively small set of rules rather than redesigning the system. | Advice, Customers | McDermott/Steele 1981 p.825 | Green | Good example of extension vs redesign. |
| R1 understood 20 XSEL commands; 87 rules recognized XSEL commands, and about 20 ordinary rules were changed in adding the capability. | Advice, Customers | McDermott/Steele 1981 pp.826-827 | Green | Use as concrete capacity, not as a detour. |
| The ad-hoc constraints extension made R1 more flexible within the configuration task, not beyond it. | Advice, Customers / Close | McDermott/Steele 1981 p.828 | Green | Important scope guardrail. |
| By 1984 R1/XCON had been used in DEC manufacturing since January 1980 and configured systems made of roughly 50-150 components. | Into DEC Manufacturing | Bachant/McDermott 1984 p.21 | Green | Complements 1982 paper with four-year perspective. |
| The authors expected R1 might eventually enter maintenance mode, but by 1984 found it hard to believe R1 would ever be done. | System Keeps Growing | Bachant/McDermott 1984 p.21 | Green | Core maintenance thesis. |
| Early performance expectations were wrong: 90-95 percent perfect configurations took three years to reach, and the system was useful before that because humans did not demand more than they demanded of predecessors. | Deployment Discipline | Bachant/McDermott 1984 p.22 | Green | Avoid sloppy "success from day one." |
| DEC's Intelligent Systems Technologies group grew from five people with no AI background to 77 people responsible for eight knowledge-based systems, one of which was R1. | System Keeps Growing | Bachant/McDermott 1984 p.22 | Green | Useful for "fortune" and organizational growth. |
| The R1 technical group remained about eight people, with less distinction over time between knowledge collection and knowledge encoding. | System Keeps Growing | Bachant/McDermott 1984 p.22 | Green | Shows ongoing labor. |
| Over four years, work devoted to adding R1 knowledge stayed around four worker-years per year. | System Keeps Growing | Bachant/McDermott 1984 p.23 | Green | Strong maintenance metric. |
| By November 1983 R1 had about 3300 rules and around 5500 component descriptions, and work would continue to extend and deepen expertise. | System Keeps Growing | Bachant/McDermott 1984 p.23 | Green | Source-backed growth number. |
| As DEC depended more on R1, planned releases were preceded by extensive testing. | System Keeps Growing | Bachant/McDermott 1984 p.23 | Green | Shows commercial engineering discipline. |
| About 65 percent of the 2526 rules added since 1980 extended general configuration capabilities, while at least 15 percent of those corrected/refined known subtasks. | System Keeps Growing | Bachant/McDermott 1984 pp.24-25 | Green | Use if prose needs growth analysis. |
| Bachant/McDermott conclude that R1's development would never be finished because its domain kept changing and users kept asking it to do more. | System Keeps Growing | Bachant/McDermott 1984 pp.27-28 | Green | Do not make this sound like failure; it is success pressure. |
| R1 began as a technical editor with mentors; every order it configured was examined more or less closely, and problems were reported to developers. | Deployment Discipline | Bachant/McDermott 1984 p.28 | Green | Human-in-the-loop deployment scene. |
| R1 had configured more than 80,000 orders by 1984, but still had seen only a fraction of possible situations. | Deployment Discipline | Bachant/McDermott 1984 p.29 | Green | Key scale plus humility anchor. |
| By 1984 fewer than one in a thousand orders was misconfigured because of rule problems. | Deployment Discipline | Bachant/McDermott 1984 p.29 | Green | Exact claim from performance discussion; keep category precise. |
| Missing part descriptions were a persistent problem because R1 knew about about 5500 of more than 100,000 possible parts that could appear on an order. | Deployment Discipline | Bachant/McDermott 1984 p.29 | Green | Shows data maintenance, not only rules. |
| The authors warn that near-perfection during the first few years of production use is unrealistic and that waiting for complete knowledge before production use is a poor strategy. | Deployment Discipline / Close | Bachant/McDermott 1984 pp.31-32 | Green | Good closing lesson. |
| Smith argues commercial expert systems solve real problems rather than test architectures, so developers should avoid a demonstration mentality. | Commercial Reality | Smith 1984 pp.66-67 | Green | Generalize from R1 with care. |
| Smith identifies domain expertise, knowledge engineering, expert-system tool design, and programming support as typical commercial expert-system development skills. | Commercial Reality | Smith 1984 p.67 | Green | Useful for "team" and organization. |
| Smith argues rapid prototyping and successive refinement help but complicate technology transfer because systems stay in flux. | Commercial Reality | Smith 1984 pp.67-69 | Green | Supports broader commercial-engineering frame. |
| Smith says incremental development is accepted, but commercial settings are reluctant to throw away Mark-I code; progressive releases are likelier. | Commercial Reality | Smith 1984 p.69 | Green | Use as bridge from demo to product. |

## Citation Bar

Minimum sources before prose:

- McDermott 1982 pp.39-42 for task, components, constraints, and early rule extraction.
- McDermott 1982 pp.45-46, 58, 64-66 for production-system architecture, rule counts, and runtime/knowledge-use data.
- McDermott 1982 pp.68-70 for development history, exceptional cases, validation, and manufacturing integration.
- McDermott/Steele 1981 pp.824-828 for XSEL, ad-hoc constraints, 15-person DEC maintenance group, and "almost all VAX-11 systems shipped."
- Bachant/McDermott 1984 pp.21-32 for four-year deployment, growth, performance, 80,000 orders, and maintenance conclusions.
- Smith 1984 pp.61-73 for broader commercial expert-system development and technology-transfer context.

## Source Discipline Notes

- The R1 1982 PDF is scanned; local extraction used `pdftoppm` plus
  `tesseract`. Verify any quoted sentence against page images before final
  prose. Page mapping is `[[page-01.txt]] = article p.39`.
- The R1 Revisited AAAI/OJS download route returned an empty stream during
  extraction. The Studylib mirror was downloaded as a PDF and its metadata
  identifies *R1 Revisited: Four Years in the Trenches*, AI Magazine Volume 5
  Number 3. Treat it as Green for anchored research, but a reviewer should
  prefer an AAAI-hosted PDF if one becomes retrievable.
- The Smith 1984 file is a scanned compilation that includes several articles;
  local text extraction places "On the Development of Commercial Expert
  Systems" at the AI Magazine article pages. Use article page numbers, not PDF
  page numbers.
- Wikipedia may be useful for discovery and date sanity checks, but do not use
  it as a prose anchor for this chapter.
- Do not upgrade the 1993 "R1/XCON at age 12" retrospective until the full text
  is fetched and parsed. Metadata alone is not an anchor.
- Do not cite unverified savings numbers, "first commercial expert system"
  absolutes, or exact market-size claims without a parsed source.
