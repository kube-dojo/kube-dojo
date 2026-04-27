# Gap Analysis: Chapter 19 - Rules, Experts, and the Knowledge Bottleneck

## Current Verdict

`NEEDS_REVIEW`, likely close to `READY_TO_DRAFT_WITH_CAP`.

The chapter has enough anchored evidence for a 4,000-4,800 word draft if prose
keeps MYCIN as the central case and treats EMYCIN/PUFF as supporting examples.
The natural expansion path is technical and procedural: system architecture,
rule mechanics, uncertainty, explanation, knowledge-acquisition workflow,
evaluation, and non-deployment. The unsafe expansion path is importing XCON's
commercial story or making broad claims about clinical AI.

Word Count Discipline label: `4k-4.8k confirmed; 4.8k-5.5k requires stretch unlocks`

## Green Scenes

- **General-methods handoff:** Feigenbaum 1977 and EMYCIN Ch15 support the pivot
  from general problem-solving methods to task-specific knowledge.
- **MYCIN origin:** Ch1 pp.8-10 supports the antimicrobial-consultant origin
  and the 1973 project goals.
- **Rule architecture:** Ch1, Ch2, and Ch4 support a detailed explanation of
  knowledge base, inference engine, backward chaining, and modular rules.
- **Uncertainty:** Ch4 and Ch11 support a careful certainty-factor discussion.
- **Knowledge bottleneck:** Ch7 supports exact "bottleneck" and knowledge
  acquisition definitions.
- **TEIRESIAS/explanation:** Ch9 and Ch17 support explanation as transparency,
  debugging, and expertise-transfer infrastructure.
- **Evaluation:** Ch31 supports the blinded meningitis evaluation and its
  limits.
- **Non-deployment and lessons:** Ch36 supports the ward-testing caveat, 1978
  retirement, flexibility/modularity lessons, and closed-world constraints.
- **Clinical-practice caveats:** Shortliffe 1983 supports the experimental
  status, no hospital access, never-used-clinically statement, liability
  ambiguity, collaborator loss, research-machine limits, slow consultation time,
  and cost-effective hardware constraints.

## Yellow / Thin Areas

- **Outside historian perspective:** Most anchors are Stanford-authored
  retrospective or in-period Stanford sources. An outside history could improve
  the chapter's field-level balance.
- **Legal/ethical deployment reasons:** Shortliffe 1983 supports legal
  ambiguity, but does not prove that liability was the decisive deployment
  blocker.
- **Shortliffe 1976 dissertation/book:** The 1984 reprints cite it and include
  condensed material, and the 1983 interview adds contemporary retrospective
  context. Add the direct 1976 source only as stretch hardening if prose needs
  exact origin/detail support.
- **Reception beyond Stanford:** Feigenbaum gives in-period movement framing,
  but an outside review or SIGART/AI Magazine source would help if prose wants
  a broader field-response paragraph.

## Red / Excluded Claims

- "MYCIN was a deployed clinical product."
- "MYCIN outperformed doctors in general."
- "Expert systems solved the first winter."
- "Rules captured all medical reasoning."
- "Knowledge acquisition became easy once TEIRESIAS existed."
- "MYCIN's certainty factors were formal probabilities."
- "XCON's business success is the climax of Ch19."

## Word Count Readiness

Natural supported range: 4,000-4,800 words.

Path to 4,000 without bloat:

- Open with the knowledge-engineering pivot from Ch18's critique.
- Use the origin scene to humanize the clinical problem.
- Spend serious explanatory space on rules, backward chaining, and certainty
  factors.
- Turn knowledge acquisition into a narrative loop rather than a definition.
- Use the evaluation as evidence of real performance and the non-deployment
  note as the honest limit.
- End with EMYCIN and the shell idea as the handoff to commercialization.

Path to 4,800-5,500 without bloat:

- Add one outside historical/reception source.
- Add the direct Shortliffe 1976 source if the draft needs exact origin/detail
  hardening.
- Add one source on clinical deployment/legal/ethical constraints.

## Reviewer Questions

1. Is the Stanford-heavy source base sufficient if the prose makes that bias
   explicit and avoids broad field claims?
2. Is the Ch31 evaluation enough to support a strong "real performance" scene
   if the 10-case limit is included immediately?
3. Is the direct Shortliffe 1976 source worth adding as stretch hardening after
   drafting, or is the 1984 retrospective/reprint plus the 1983 interview
   sufficient?
4. Should PUFF remain a short Feigenbaum example, or be used as a second scene
   showing reusable shells after MYCIN?
