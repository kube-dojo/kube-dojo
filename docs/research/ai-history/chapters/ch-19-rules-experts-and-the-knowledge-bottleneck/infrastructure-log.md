# Infrastructure Log: Chapter 19
# Infrastructure Log: Chapter 19 - Rules, Experts, and the Knowledge Bottleneck

## System Architecture

- MYCIN's core architecture separates knowledge base from inference engine.
  This is the chapter's central infrastructure move: expertise becomes data-like
  material that can be edited, inspected, explained, and reused.
- MYCIN's visible system includes a consultation program, explanation program,
  and knowledge-acquisition program. Do not reduce it to "a pile of rules."
- The inference style is primarily backward chaining: the system starts from a
  clinical parameter/goal and asks for evidence needed to support or reject it.

## Knowledge Representation

- Rules are modular chunks of medical knowledge, often represented as stylized
  IF/THEN conditions with certainty factors.
- The rule format made explanation possible because the system could display or
  translate the rule behind a question or conclusion.
- The format also imposed limits: Chapter 36 notes that MYCIN's rules often did
  not separate causal links from heuristics and that expanded rule sets create
  knowledge-engineering maintenance problems.

## Hardware / Software

- MYCIN was written in the LISP ecosystem; the Ch1 retrospective explicitly
  says LISP helped separate medical rules from inference procedures and allowed
  rules to be treated as data.
- EMYCIN turned the MYCIN core into a reusable shell for rule-based
  consultants, but its power depended on the specificity of the representation
  and backward-chaining inference structure.

## Prose Guardrails

- Make the bottleneck visible as labor, not just an abstract phrase. The chapter
  should show expert interviews, prototype feedback, debugging cases, and tool
  support.
- Keep clinical deployment separate from evaluation. MYCIN performed well in a
  blinded study, but it was not tested on hospital wards.
- Keep XCON and the commercial expert-system boom as the handoff, not the body
  of Ch19.
