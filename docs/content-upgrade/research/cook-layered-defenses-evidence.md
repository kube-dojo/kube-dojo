# Cook, Reason, and operational applications — #2403

Scope: Part 3 of `src/content/docs/platform/foundations/systems-thinking/module-1.4-complexity-and-emergent-behavior.md`, audited at `86dcb695c5f8b69f0b1822a90342612a0802b2aa`. Research only; no published prose acceptance.

## Inspected sources

- Richard I. Cook, *How Complex Systems Fail*, Revision D (00.04.21): https://www.adaptivecapacitylabs.com/HowComplexSystemsFail.pdf. Retrieved 35,566 bytes, SHA256 `7e3f303c2e2a7bca1707bc64e832b1adbb4f116b75e770b962ac4f48ff4aea57`; PDF metadata reports five pages. Text extraction was compared with the numbered HTML presentation at https://how.complexsystems.fail/, which links the original PDF. Local page renders had missing body glyphs: body evidence here is text, not successful visual verification.
- James Reason, “Human error: models and management,” *Western Journal of Medicine* 172(6), June 2000, pp.393–396, DOI10.1136/ewjm.172.6.393: https://pmc.ncbi.nlm.nih.gov/articles/PMC1070929/. The inspected HTML identifies the author and states that the article originally appeared in *BMJ* 2000;320:768–770. Direct BMJ retrieval failed; this note cites the inspected republication, not an inspected BMJ layout or Reason's books.

## Claim dispositions

1. **Cook principles1–5: retain attribution, narrow applications.** PDF page1/HTML numbered principles cover hazards, multiple defenses, combinations of failures, latent flaws, and degraded operation. Technical and human defenses are explicitly included. Monitoring, retries, capacity cliffs and Kubernetes mechanisms in the module need labels as author applications, not Cook quotations or enumerated source examples. Avoid presenting these principles as measured failure probabilities for every software service.
2. **Cook principles6–8: qualify the synthesis.** PDF page2/HTML principles6–8 discuss persistent catastrophic potential, objections to isolated root-cause attribution, and hindsight bias. The module's shipping-pressure explanation is an additional interpretation, not the wording of principle6. Keep distinctions between a contributing fault and a complete accident explanation.
3. **Length claim: replace.** The retrieved artifact has five PDF pages; “three pages” is not a reliable description of this edition. Use “short treatise” without a page-count claim. Page count does not establish a first-publication date.
4. **Swiss Cheese: attribute separately to Reason's account.** The republication's section “THE ‘SWISS CHEESE’ MODEL OF SYSTEM ACCIDENTS,” opening two paragraphs, describes defensive layers with changing weaknesses and accident opportunities passing through them. Its Figure1 caption names the model. A teaching diagram can be attributed as an illustration after Reason; do not present it as Cook's figure. No claim about the model's first invention or earliest publication is established here.
5. **Operational diagram and questions: label illustrations.** The module's “Mostly Working”/“Barely Working” diagram and platform questions are teaching constructions. Remove unsupported frequency labels such as “Most of the time” and “Rarely,” or source their intended population. A quiet dashboard alone does not prove which latent failures are present.

## Acceptance boundary

Independent source review must precede prose. Later changes need separate prose review, build/render checks, CI and live verification. This note neither validates all Part3 examples nor accepts the resilience, edge-of-chaos or Ukrainian sections. Reason's figure image was not visually inspected; the proposed attribution rests on his accessible text and caption. No medical recommendations are derived from either source.
