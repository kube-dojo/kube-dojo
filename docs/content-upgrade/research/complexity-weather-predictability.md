# Weather analogy: prediction and its limits

Research packet for #2403, parent #2282, epic #2272. Scope: the weather analogy in `module-1.4-complexity-and-emergent-behavior.md`. Checked 2026-09-05; independent source review pending. No published prose changes in this packet.

## Inspected evidence

- [ECMWF, Quantifying forecast uncertainty](https://www.ecmwf.int/en/research/modelling-and-prediction/quantifying-forecast-uncertainty), opening explanation and its two error-source bullets: uncertainty in initial conditions and numerical-model approximations both contribute to errors that grow with time. ECMWF also explains why the two sources are not independent. This is the forecasting institution's explanation of its methods. This packet does not rely on the page's operational ensemble counts or model-version details.
- [Lorenz, The predictability of a flow which possesses many scales of motion (1969), MIT-hosted scan](https://wind.mit.edu/~emanuel/Lorenz/EdLorenz/Predictability_Flow_Which_Possesses_1969.pdf#page=1), PDF page 1, abstract and introduction: the study concerns a simplified model and conditional, scale-dependent predictability. Its introduction distinguishes exact-state/exact-equation/exact-solution prediction in a deterministic isolated system from practical observation. This does not support a universal ten-day horizon under perfect knowledge.
- [Same scan, PDF page 18](https://wind.mit.edu/~emanuel/Lorenz/EdLorenz/Predictability_Flow_Which_Possesses_1969.pdf#page=18), Summary: the conjecture concerns reducing observational error to a positive value, not eliminating it. Lorenz explicitly qualifies the statistical assumptions and applicability to real fluids. The preceding discussion questions applying the model to a single localized wing disturbance. Do not turn this into evidence for a particular butterfly causing a particular tornado.

The Lorenz file has 19 PDF pages, 1,745,835 bytes, SHA-256 `1770809242f1dc7e6cfe008b23e8fb0db2eb58d7a61ae5f22289b2280754249c`. Direct public download succeeded; PDF pages 1 and 18 were rendered and visually inspected. The scan has proof markings and a visible `018` label; this packet uses PDF locators and does not claim final-journal page equivalence. Other pages were not inspected. Local cache: `.agent/sources/lorenz1969.pdf`, `lorenz-page1.png`, `lorenz-page18.png`; exclude from PR.

## Claim dispositions

| Existing wording | Required disposition |
|---|---|
| Perfect modelling of every molecule still prevents forecasts beyond about ten days | Replace. It conflates an exact-knowledge idealization with practical errors and supplies an unqualified numerical horizon. Do not substitute another universal number. |
| A butterfly in Brazil might cause a tornado in Texas | Remove the literal causal example from this packet. The inspected evidence does not establish such an event or prove this specific scenario. |
| This is not a measurement problem | Replace: initial-condition uncertainty is explicitly relevant in the inspected explanation. Avoid claiming it is the only source of uncertainty. |
| A distributed system is the same | Label a limited teaching analogy. These meteorological sources establish no theorem about all distributed systems. |

## Proposed teaching use

Explain how uncertainty in starting conditions and a model can limit a prediction. Ask readers to name what they do and do not know before making an operational forecast; distinguish missing measurements from approximations. This is an editorial transfer question, not a claim that platforms obey the atmospheric model. Keep the practical lesson about stating assumptions without claiming that testing or observation is futile.

Before publication: independent source review, separate scoped prose review, required tests/build/render/CI and live checks. This packet leaves the other four #2403 claim clusters, the existing chaos exercise and Ukrainian parity open.
