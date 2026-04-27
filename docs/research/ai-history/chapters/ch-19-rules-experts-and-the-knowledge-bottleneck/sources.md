# Sources: Chapter 19 - Rules, Experts, and the Knowledge Bottleneck

## Source Table

| Source | Type | Anchor | Use | Status |
|---|---|---|---|---|
| Bruce G. Buchanan and Edward H. Shortliffe, eds., [*Rule-Based Expert Systems: The MYCIN Experiments of the Stanford Heuristic Programming Project*](https://people.dbmi.columbia.edu/~ehs7001/Buchanan-Shortliffe-1984/MYCIN%20Book.htm), Addison-Wesley, 1984 | Primary retrospective / edited project record | landing page and Contents; Ch1, Ch2, Ch4, Ch5, Ch7, Ch9, Ch11, Ch15, Ch17, Ch31, Ch36 | Central MYCIN archive: system context, rules, knowledge engineering, certainty factors, evaluation, and limits | Green |
| Buchanan and Shortliffe 1984, Chapter 1, "The Context of the MYCIN Experiments" | Primary retrospective | pp.3-10 | Expert-system definition, knowledge base/inference engine split, backward chaining, knowledge engineering definition, MYCIN origins and 1973 grant goals | Green |
| Randall Davis and Jonathan J. King, Chapter 2, "The Origin of Rule-Based Systems in AI" | Primary retrospective | pp.20-30 | Production systems, performance-oriented expert systems, rules as accessible/modifiable knowledge, strengths and awkward domains | Green |
| William van Melle, Chapter 4, "The Structure of the MYCIN System" | Primary retrospective / reprinted article | pp.67-72 | Three subprograms, consultation flow, contexts/clinical parameters, CF triples, 500 rules, goal-directed backward chaining, rule modularity | Green |
| Edward H. Shortliffe, Chapter 5, "Details of the Consultation System" | Primary retrospective / dissertation condensation | pp.78-132 | Rule syntax and implementation details; use only for exact rule mechanics if prose needs them | Yellow |
| Chapter 7, "Knowledge Engineering" | Primary retrospective | pp.149-152 | Knowledge acquisition bottleneck, iterative construction, transparency, handcrafting risks, knowledge engineer/expert workflow | Green |
| Randall Davis, Chapter 9, "Interactive Transfer of Expertise" | Primary retrospective / reprinted article | pp.171-174 | TEIRESIAS, explanation as prerequisite for knowledge acquisition, interactive transfer of expertise, debugging/teaching model | Green |
| Edward H. Shortliffe and Bruce G. Buchanan, Chapter 11, "A Model of Inexact Reasoning in Medicine" | Primary retrospective / reprinted 1975 paper | pp.233-237 | Why full Bayes was hard in medicine, judgmental knowledge, certainty-factor motivation, approximate evidence accumulation | Green |
| William van Melle, Edward H. Shortliffe, and Bruce G. Buchanan, Chapter 15, "EMYCIN" | Primary retrospective / reprinted 1981 paper | pp.302-305 | MYCIN shell generalization, domain-independent framework, limits of broad generality, narrow-domain knowledge-based systems | Green |
| Chapter 17, "Explanation as a Topic of AI Research" | Primary retrospective | pp.331-335 | WHY/HOW history, explanation as transparency, debugging, acceptance, and knowledge-acquisition support | Green |
| Yu et al., Chapter 31, "An Evaluation of MYCIN's Advice" | Primary retrospective / reprinted JAMA 1979 article | pp.589-594 | Blinded meningitis evaluation, 10 cases, eight outside evaluators, MYCIN ratings, explicit small-case limitation | Green |
| Chapter 36, "Major Lessons from This Work" | Primary retrospective | pp.669-676 | Flexibility/modularity, shallow/causal limits, not ward-deployed, knowledge base laid to rest in 1978, evidence-gathering/closed-world fit | Green |
| Edward A. Feigenbaum, ["The Art of Artificial Intelligence: Themes and Case Studies of Knowledge Engineering"](https://www.ijcai.org/Proceedings/77-2/Papers/092.pdf), IJCAI 1977, pp.1014-1029 | Primary/in-period invited paper | pp.1014-1015, 1027-1028 | Knowledge engineer definition, PUFF/MYCIN example, expert-rule extraction, explanation as engineering issue, shortage of trained knowledge engineers | Green |
| Edward H. Shortliffe, ["Feature Interview: Edward H. Shortliffe on the MYCIN Expert System"](https://www.researchgate.net/publication/334376827_Feature_Interview_Edward_H_Shortliffe_on_the_MYCIN_Expert_System), *Computer Compacts* 1(6), 1983 | Primary interview | pp.283-289 | Direct contemporary retrospective on origin, clinical non-use, liability ambiguity, workflow/cost constraints, collaborator loss, and EMYCIN/PUFF reuse | Green |

## Claim Matrix

| Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|
| MYCIN's authors defined an expert system as one designed to provide expert-level solutions, be understandable, and accommodate new knowledge easily. | Consultant in Terminal | Ch1 pp.3-4 | Green | Good opening definition. |
| MYCIN separated knowledge base and inference engine, with additional user/explanation/building subsystems. | Rules as Frozen Expertise | Ch1 pp.3-6; Ch4 pp.67-68 | Green | Core architecture. |
| MYCIN represented knowledge mostly as conditional IF/THEN rules. | Rules as Frozen Expertise | Ch1 pp.4-5; Ch4 pp.70-71 | Green | Avoid over-formalizing as all knowledge. |
| MYCIN primarily used backward chaining / goal-directed inference and behaved as an evidence-gathering program. | Rules as Frozen Expertise | Ch1 p.5; Ch4 p.71 | Green | Link to consultation ergonomics. |
| MYCIN was born from a Stanford infectious-disease consultation concept after a monitoring system seemed to require expert antimicrobial knowledge. | Consultant in Terminal | Ch1 pp.8-10 | Green | Use this as origin scene. |
| The 1973 grant goals included consultation, interactive explanation, and acquisition of judgmental knowledge from experts. | Consultant in Terminal | Ch1 pp.10-11 | Green | Strong source for chapter structure. |
| Rule modularity supported rapid feedback from experts and incremental modification. | Rules as Frozen Expertise | Ch1 pp.9-10; Ch4 p.72; Ch2 pp.26-27 | Green | Core "why rules" claim. |
| MYCIN used certainty factors between -1 and 1 attached to facts/hypotheses. | Uncertainty | Ch4 pp.70-71 | Green | State as MYCIN model, not probability theory. |
| Shortliffe/Buchanan argued full Bayesian analysis was often impractical in medicine because good conditional data and interrelationship data were unavailable. | Uncertainty | Ch11 pp.233-237 | Green | Important anti-overclaim: not "Bayes wrong," but data unavailable. |
| The authors described knowledge acquisition as a bottleneck from DENDRAL onward. | Bottleneck Appears | Ch7 p.149 | Green | Exact bottleneck anchor. |
| Knowledge acquisition is transfer and transformation of problem-solving expertise from sources such as experts, textbooks, databases, or experience into a program. | Bottleneck Appears | Ch7 pp.149-151 | Green | Definition anchor. |
| Complex expert systems could not safely rely on handcrafting when programmer and specialist differ; building/debugging large judgmental knowledge programs is slow and consistency is hard. | Bottleneck Appears | Ch7 p.151 | Green | Supports bottleneck consequences. |
| TEIRESIAS treated explanation as prerequisite to knowledge transfer: expert must see what the program knows and how it used it before modifying the knowledge base. | Bottleneck Appears | Ch9 pp.171-174 | Green | Good scene for debugging loop. |
| Feigenbaum framed knowledge engineering as applying AI tools to difficult applications requiring expert knowledge and listed acquiring/representing/using knowledge as core design issues. | After General Methods | Feigenbaum 1977 p.1014 | Green | In-period movement thesis. |
| Feigenbaum's PUFF example says 55 IF/THEN rules encoded partly public, partly private expert knowledge extracted by engineers working with an expert. | After General Methods | Feigenbaum 1977 pp.1014-1015 | Green | Useful short comparative scene, not central narrative. |
| Feigenbaum treated explanation as an engineering requirement for acceptance and knowledge acquisition/debugging. | Bottleneck Appears | Feigenbaum 1977 pp.1027-1028 | Green | Reinforces Ch17/TEIRESIAS. |
| The blinded meningitis evaluation compared MYCIN and human prescribers on 10 cases, with eight outside specialists rating prescriptions without knowing one was a computer program. | Power and Fragility | Ch31 pp.589-591 | Green | Keep narrow. |
| In the evaluation, 65% of MYCIN prescriptions were rated acceptable; MYCIN received majority-acceptable ratings in 70% of cases, and its prescriptions received acceptable ratings more often than those of any of the nine human prescribers on the stated criterion. | Power and Fragility | Ch31 pp.592-593 | Green | Do not generalize beyond study. |
| The evaluation's primary limitation was small case count. | Power and Fragility | Ch31 p.594 | Green | Must appear near evaluation discussion. |
| The MYCIN authors later said ward implementation/testing was intended but never undertaken; the infectious-disease knowledge base was laid to rest in 1978. | Power and Fragility | Ch36 p.673 | Green | Critical anti-hype anchor. |
| In 1983, Shortliffe described MYCIN as an experimental system that no hospital could install, said it had never been used clinically, and named practical reasons including collaborator loss, research-machine constraints, slow consultations, and cost-effective hardware limits. | Power and Fragility | Shortliffe 1983 pp.286-287 | Green | Use to explain non-deployment without inventing a single-cause story. |
| Shortliffe treated legal responsibility for computer-assisted diagnosis as unsettled, while still emphasizing physician decision authority rather than "computer medicine." | Power and Fragility | Shortliffe 1983 pp.285-286 | Green | Keep as ambiguity, not proof that liability alone blocked deployment. |
| EMYCIN reused MYCIN's domain-independent core to construct rule-based consultants but remained suitable only for certain application types. | Power and Fragility | Ch15 pp.302-305; Ch36 pp.673-675 | Green | Handoff to shells/commercialization. |

## Citation Bar

Minimum sources before prose:

- Buchanan/Shortliffe 1984 Ch1 pp.3-10.
- Ch4 pp.67-72.
- Ch7 pp.149-152.
- Ch9 pp.171-174.
- Ch11 pp.233-237.
- Ch31 pp.589-594.
- Ch36 pp.669-676.
- Feigenbaum 1977 pp.1014-1015 and pp.1027-1028.
- Shortliffe 1983 pp.286-287 for non-deployment causes if prose expands the
  clinical-practice limit.

## Source Discipline Notes

- Wikipedia may be used only for discovery and title/date sanity checks. It is
  not a prose claim anchor.
- Treat the 1984 book as a primary retrospective from the project, not as a
  neutral outside history.
- Do not quote long rule examples verbatim in prose; paraphrase and cite the
  source pages.
- The evaluation claim is Green only in its narrow study frame. Do not claim
  "MYCIN was better than doctors" without the meningitis-task/evaluator limits.
