# Infrastructure Log: Chapter 21 - The Rule-Based Fortune

## Technical Substrate

- **VAX-11 systems:** The configured product family. The task involved CPUs,
  memory, MASSBUS/UNIBUS interfaces, peripheral devices, cabinets, boxes,
  backplanes, cables, floor layout, and customer-specific constraints.
- **Production systems:** R1 represented constraint knowledge as productions:
  condition/action rules over working memory, executed through a recognize-act
  cycle.
- **OPS4 / OPS5:** R1 was originally implemented in OPS4 and later rewritten in
  OPS5. The language substrate matters because R1's maintainability argument is
  partly about production rules being easy to split, specialize, and extend.
- **Match method:** R1 avoided broad search by ordering decisions dynamically so
  that enough information was available before each action. This only works in
  domains with the right local structure.
- **Component database:** R1 used a database of component descriptions. By 1984
  it had about 5500 descriptions, but DEC had more than 100,000 possible parts
  that might appear on an order.
- **Output diagrams/configuration descriptions:** R1's output was operational:
  technicians used it before physically assembling systems.

## Operational Infrastructure

- **Manufacturing process:** R1 was not merely consulted by researchers; it was
  integrated into the workflow that checked orders and prepared assembly
  descriptions.
- **Regional field-office screening:** McDermott 1982 reports R1 beginning to
  configure orders on the day they were booked at several regional offices.
- **Mentor/review process:** Bachant/McDermott 1984 report that people who had
  been technical editors watched R1's configurations and reported problems.
- **Release/testing process:** As DEC depended more on R1, planned release dates
  were preceded by extensive testing.
- **Maintenance labor:** R1 required continuing knowledge collection, rule
  encoding, component-description work, and problem reporting; this is the core
  infrastructure of the "fortune."

## Implementation Guardrails

- Do not describe R1 as a neural system, statistical learner, or automated
  optimizer. It is a rule-based production system.
- Do not imply R1 learned automatically from orders. Humans extracted,
  represented, tested, and corrected knowledge.
- Do not treat the component database as passive trivia. Missing or incomplete
  part descriptions were a major operational problem.
