# Infrastructure Log: Chapter 17 - The Perceptron's Fall

## Hardware

- Mark I had a 20x20 photocell sensory unit, 512 association units, and eight
  response units, according to the ONR Digital Computer Newsletter pp.2-3.
- The machine was electromechanical and explicitly research-purpose, not a
  deployable application system.
- Scaling from Mark I to useful machines was a named open engineering problem:
  the ONR source says considerable R&D remained before applications and that
  economics were not demonstrated.

## Computation

- Minsky/Papert's critique is fundamentally about locality, order, and scaling.
  The issue is not merely that a perceptron cannot compute a toy Boolean
  function; the issue is that some predicates require association units whose
  support grows with the whole input retina.
- The connectedness examples are a computational-infrastructure story: local
  parallel summation stops being cheap if the partial predicates become global.
- Prior structure is the chapter's technical hinge. Minsky/Papert allow that
  learning can work when partial functions are matched to the task; they reject
  quasi-universal randomly generated perceptrons for high-order tasks.

## Funding / Institutions

- ONR and RADC sponsored Mark I work, but Olazaran's account says ONR funding
  was much smaller than ARPA's potential funding scale.
- Olazaran reports ARPA backing symbolic AI and explicitly not funding
  neural-net research; treat this as a historiographic/interview-based anchor,
  not a sole documentary budget table.

## Prose Guardrails

- Do not present hardware limits as the only cause of decline.
- Do not present theorem limits as the only cause of decline.
- The chapter should show the interaction between theorem, hardware, and
  institutional interpretation.
