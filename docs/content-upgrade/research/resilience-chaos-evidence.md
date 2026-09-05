# Resilience abilities and chaos guidance — #2403

Research-only claim map for the complexity module sections4.2–4.3 and its absolute testing claim, audited at `9dc3ed7f54a3ad4f6ec9379cb25965690601c464`. No experiments were executed.

## Inspected sources and access

- Erik Hollnagel, *How Resilient Is Your Organisation? An Introduction to the Resilience Analysis Grid (RAG)*, April2010 author draft, HAL record hal-00613986: https://hal.science/hal-00613986/document redirects to https://minesparis-psl.hal.science/hal-00613986/document. Retrieved266167bytes; SHA256 `30da2b11366db804c0ba3c3801fda3aa99f828b8e621a271f06477f511da2830`; seven PDF pages including repository cover. Lead visually inspected PDF3–5, printed2–4. The body footer says3Apr10. This is not the2015 technical note: that author's old URL returned404. ResearchGate's author-uploaded full text corroborates the2010 title/draft and HAL identifier; its2015 upload date is not the work's date.
- *Principles of Chaos Engineering*, https://principlesofchaos.org/, full public HTML inspected; header says last update March2019. This is practitioner guidance, not an empirical guarantee of outcomes.

## Dispositions

1. **Four abilities: attribute and qualify.** Hollnagel printed2–3 names respond, monitor, anticipate and learn. Printed3–4 treats assessment as a profile with questions tailored to the organization. Replace the module's telemetry-oriented maturity assertion with an attributed assessment framework. Circuit breakers, game days and specific dashboards are author applications, not examples established by these inspected spans.
2. **Monitoring and learning: remove guarantees.** Printed2 requires valid precursors and warns against spurious indicator associations; a named metric is not automatically a leading indicator. Printed3 discusses learning that changes behavior, including learning from successful activity. It does not establish the module's guaranteed incident-repetition assertion. Use conditional applications rather than importing unsupported certainty.
3. **Chaos definition: broaden.** “Chaos in Practice,” steps1–4, describes a measurable steady state, a hypothesis, real-world variables and an attempt to disprove the hypothesis. “Vary Real-world Events” includes traffic spikes and scaling as well as faults. Do not define the discipline solely as failure injection or random termination.
4. **Production: state preference, not universal necessity.** “Run Experiments in Production” strongly prefers production traffic because environments differ. It does not say every exercise must run there. Retain the distinction between representative traffic and preproduction evidence without claiming staging is useless or production is mandatory for every learner.
5. **Continuous experiments: bound the advice.** Automation and continuous execution appear under “Advanced Principles”; “Minimize Blast Radius” explicitly requires containing fallout. Attribute this guidance and retain operational prerequisites; do not promise automatic detection of all drift or guaranteed resilient design.
6. **Testing absolute: remove.** These sources do not establish that tests cannot reveal emergent behavior. Explain coverage limits and the particular hypothesis being examined; do not make chaos a replacement for other tests or a universal requirement. The module's30%-pods/200ms example is hypothetical, not a measured result.

## Remaining limits

This packet does not establish a universal robustness/resilience dichotomy, validate the listed experiment tools, or accept edge-of-chaos claims. No2015 RAG body or generic Safety-II page is accepted by substituting the2010 draft. Any retained source-specific assertion must use the inspected edition. Independent source review precedes separate prose review, build/render/CI and live checks. Ukrainian parity and other module findings remain open.
