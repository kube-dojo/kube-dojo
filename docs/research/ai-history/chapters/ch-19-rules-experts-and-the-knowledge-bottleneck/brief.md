# Brief: Chapter 19 - Rules, Experts, and the Knowledge Bottleneck

## Thesis

Expert systems became a pragmatic answer in the first-winter era: if general
intelligence would not scale, encode narrow expertise explicitly. MYCIN showed
the bargain clearly. Separating a knowledge base from an inference engine made
medical rules inspectable, editable, explainable, and strong enough to rival
specialists in a bounded evaluation. But the same architecture exposed the
bottleneck that would haunt the field: knowledge had to be extracted,
formalized, debugged, and maintained through labor-intensive collaboration
between experts and knowledge engineers.

## Scope

This chapter should bridge Ch18's Lighthill critique to Ch20/Ch21's
infrastructure and commercialization arc. It should focus on the Stanford
Heuristic Programming Project, DENDRAL-to-MYCIN lineage, rule-based
representation, certainty factors, explanation facilities, knowledge
acquisition, and the limits of clinical deployment. The chapter should use
MYCIN as the central case and EMYCIN/PUFF as evidence that the MYCIN core became
a reusable expert-system shell, while leaving DEC/XCON commercialization to
Ch21.

## Boundary Contract

- Do not say MYCIN was broadly deployed in hospitals. The 1984 retrospective
  says ward testing was intended but never undertaken, and the infectious-disease
  knowledge base was laid to rest in 1978 despite strong decision-performance
  studies.
- Do not present MYCIN as a reaction to Lighthill or the first winter. MYCIN's
  architecture and 1973 grant goals predate the winter's effects; frame expert
  systems as a parallel current that the winter made newly attractive, not as a
  post-Lighthill invention.
- Do not turn the blinded meningitis evaluation into general medical supremacy.
  It used 10 challenging cases, eight independent outside evaluators, and a
  narrow antimicrobial-selection task.
- Do not summarize the evaluation as "MYCIN scored higher than nine doctors."
  Say that MYCIN's prescriptions received acceptable ratings more often than
  those of any of the nine human prescribers, on that study's stated criterion.
- Do not imply rule-based systems solved general intelligence. EMYCIN's own
  retrospective says good applications are bounded classification/evidence
  problems with a reasonably small closed-world vocabulary.
- Do not make the knowledge-acquisition bottleneck a later hindsight invention.
  Buchanan/Shortliffe Chapter 7 explicitly calls putting domain-specific
  knowledge into programs a bottleneck and defines knowledge acquisition as the
  transfer/transformation of expertise.
- Do not make certainty factors rigorous probability. The MYCIN authors present
  them as a practical approximation for judgmental, incomplete medical
  reasoning where exhaustive Bayesian data were unavailable.
- Do not duplicate Ch21's XCON/DEC business story. Ch19 may end by showing why
  shells and domain-specific rules were commercially tempting, but not narrate
  the DEC fortune.

## Narrative Spine

1. **After General Methods:** move from Lighthill's critique to the Stanford
   knowledge principle: performance comes from task-specific knowledge.
2. **The Consultant in the Terminal:** MYCIN begins as an infectious-disease
   consultation program modeled on expert clinical advice, not as a universal
   doctor.
3. **Rules as Frozen Expertise:** production rules turn informal clinical
   judgments into modular IF/THEN chunks that can be chained, edited, and
   explained.
4. **Uncertainty Without Full Probability:** certainty factors encode practical
   evidential strength when clean statistical data and full conditional
   probabilities are unavailable.
5. **The Bottleneck Appears:** building the knowledge base requires iterative
   expert interviews, prototype feedback, debugging, and tools like TEIRESIAS.
6. **Power and Fragility:** MYCIN's blinded evaluation was strong, but the
   system was narrow, not ward-deployed, and difficult to maintain.
7. **Handoff to the Boom:** the reusable-shell idea points toward Ch20/Ch21:
   domain rules, expert interviews, and packaged inference engines become
   economically tempting, but the DEC/XCON business story stays out of Ch19.

## Prose Capacity Plan

Word Count Discipline label: `4k-4.8k confirmed; 4.8k-5.5k requires stretch unlocks`

Core range: 4,000-4,800 words supported by current verified anchors. Stretch
range: 4,800-5,500 words only if one more strong source is added on early
expert-system reception outside Stanford. Shortliffe's 1983 interview now
supports a fuller clinical non-deployment paragraph without making liability
or hardware the single cause.

- 550-700 words: Ch18 handoff and DENDRAL-to-MYCIN shift from general methods
  to domain-specific knowledge, anchored by Feigenbaum 1977 pp.1014-1029,
  Buchanan/Shortliffe Ch1 pp.3-10, and Ch15 pp.302-305.
- 650-800 words: MYCIN origin as a consultation program for infectious-disease
  therapy, anchored by Ch1 pp.8-10 and the 1973 grant-goal excerpt.
- 700-850 words: knowledge base/inference engine, rules, backward chaining,
  explanation subsystem, and rule modularity, anchored by Ch1 pp.3-6, Ch4
  pp.67-72, and Ch2 pp.26-30.
- 500-650 words: certainty factors and inexact medical reasoning, anchored by
  Ch4 pp.70-71 and Ch11 pp.233-237.
- 750-950 words: knowledge engineering and the bottleneck: iterative transfer,
  handcrafting risks, TEIRESIAS, and expert-program feedback loops, anchored by
  Ch7 pp.149-152 and Ch9 pp.171-174.
- 650-850 words: evaluation, limits, and non-deployment, anchored by Ch31
  pp.589-594, Ch36 pp.669-676, and Shortliffe 1983 pp.286-287.
- 350-500 words: handoff to Ch20/Ch21: EMYCIN shells and reusable rule-based
  consultants, anchored by Ch15 pp.302-305 and Ch36 pp.673-675.

Honesty close: If the prose cannot reach 4,000 words without repeating MYCIN
implementation details or borrowing XCON's business arc, stop near the lower
bound and flag the missing external-reception source.
