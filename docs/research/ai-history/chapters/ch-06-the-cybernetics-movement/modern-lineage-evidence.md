# Modern feedback: connection is not a genealogy

Research packet for #2405 cluster5, parent #2289/#2290, epic #2272. Audited published chapter at `19b66cdf0f2d2a0544b43d593c62559b3b8d0580`. No published prose change; source acceptance and subsequent editorial review are separate gates.

## Inspected evidence

### A. The 1943 paper's own engineering context

Arturo Rosenblueth, Norbert Wiener and Julian Bigelow, “Behavior, Purpose and Teleology,” *Philosophy of Science* 10(1), January1943, pp.18–24. [University-hosted original scan](https://home.csulb.edu/~cwallis/382/readings/482/wiener.behavior.purpose.teleology.1943.pdf):664132bytes, SHA256 `4369ef758fe4d8055a2a39db8d3595d92fab73118de91e6b1b040c467f73cca9`. Primary conceptual paper; eight PDF pages including the cover. Lead visually inspected printed19, PDF3, on September5,2026. Printed23–24 were separately inspected in `teleology-determinism-evidence.md`.

Exact locator: printed19, paragraph beginning “Purposeful active behavior,” and the preceding discussion of machines and servomechanisms. The authors describe two senses in which engineers use feedback, distinguish energy returned as input from control by error relative to a goal, and select the second sense for their argument. They describe servomechanisms as an existing term. This is direct evidence that they were working with engineering terminology already in use; it is not a priority history of feedback or an experimental comparison of controllers.

### B. A documented digital flight-control example

Jim Skeen, NASA Armstrong Public Affairs Specialist, [“Flying with NASA – Digital-Fly-By-Wire”](https://www.nasa.gov/centers-and-facilities/armstrong/flying-with-nasa-digital-fly-by-wire/), June6,2023; page last updated September5,2023. NASA institutional retrospective, not a contemporary flight-test report. Lead read the article body on September5,2026. Cached HTML307289bytes, SHA256 `92ab3e89a6c9689bb3d034a2030ea9e9c47bee5c29294937943bc92cf7a89b84`; page navigation may change independently of the article.

Exact locator: paragraph beginning “Shortly after the historic 1969 Moon landing,” following the second F-8 photograph. NASA describes an aircraft digital fly-by-wire development program using the Apollo digital computer and inertial sensing as its core, with a first flight on May25,1972, piloted by Gary Krier. The next paragraph after Krier's quotation describes replacement of the original Apollo system with a triple-redundant digital system. The opening article explanation identifies flight controls as the application. These passages support a bounded example of digital computing used for physical flight control.

Do not import all neighboring assertions: this packet does not verify general cost/reliability advantages, particular signal media in the1972 aircraft, global first-ever priority, measured latency, or the program's influence on every later aircraft. Do not turn the quotation into reconstructed cockpit dialogue. The article does not attribute this program to the1943 paper.

## Claim map and disposition

| Published claim in “Why this still matters today” | What the inspected evidence establishes | Disposition for the next prose packet |
| --- | --- | --- |
| Thermostats, autopilots, PID, robotic arms, error-correcting codes, telemetry and reinforcement-learning reward signals are all heirs of the1943 paper | Source A explicitly uses existing engineering terminology. Neither A nor B establishes those individual lines of influence. | Remove the universal ancestry assertion. Explain the paper's particular classification of purposeful behavior, with A, without claiming it invented feedback. Any specific later intellectual influence needs separate historical evidence. |
| Reprogrammable tasks run on stored-program digital hardware while all continuous, fast physical control uses dedicated loops whose structure is built into the substrate | B documents an Apollo digital computer in an aircraft flight-control program. Digital computation and physical control are not mutually exclusive categories. | Replace the exclusive hardware contrast with this attributed historical example. Do not assert a measured timing capability, general hardware taxonomy, or that digital controllers lack specialized components. |

The second disposition is a limited inference from the program example, not a claim about all controllers. The first is an evidence boundary, not proof that none of the listed technologies was influenced by cybernetics. Avoid replacing “all are heirs” with an equally unsupported “none are heirs.”

## Reader value and remaining limits

The revised note can connect two concrete questions: what does the1943 classification tell us about behavior, and what does the1972 aircraft tell us about implementation? Give the documented example directly; an artificial reveal or invented flight scene adds no evidence. Similarity of a feedback diagram alone cannot establish historical transmission. This preserves an engaging connection while distinguishing conceptual description, implementation and genealogy.

Grok's bounded scout found additional leads, but external body retrieval failed. Minorsky1922, Black1934, Hamming1950 and Sutton1988 remain unaccepted leads here; Sutton's HTTP200 HEAD response is not a reading. NASA NTRS records19720056394 and19750010175 returned403 to lead browsing, so their report bodies are not part of the accepted evidence. The NASA retrospective is explicitly the basis of B.

This packet does not settle the Ashby priority, Macy synthesis/format, analog-program causality, predictor-performance activity or Ukrainian fidelity findings. No whole-chapter acceptance. Independent source review must assess the map and access limits before a separate published revision and Google editorial review.
