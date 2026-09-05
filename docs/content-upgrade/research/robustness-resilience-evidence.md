# Robustness and resilience terminology — #2403

Scope: section4.1 and Q4 of `platform/foundations/systems-thinking/module-1.4-complexity-and-emergent-behavior.md` at `71e2573854c6ae9104bb2c4d4c287d78e386d12d`. Research only; Q3/Q8 and the lab are separate packets.

## Source and access

David D. Woods, “Four concepts for resilience and the implications for the future of resilience engineering,” DOI10.1016/j.ress.2015.03.018. The [publisher record](https://www.sciencedirect.com/science/article/pii/S0951832015000848) identifies *Reliability Engineering & System Safety*141, September2015, pp.5–9. Publisher metadata is not the inspected full-text edition.

The [ResearchGate author upload](https://www.researchgate.net/publication/276139783_Four_concepts_for_resilience_and_the_implications_for_the_future_of_resilience_engineering) provided readable article HTML; its PDF download returned429. A [third-party mirror of that manuscript](https://maritimesafetyinnovationlab.org/wp-content/uploads/2021/06/4sensesofresiliencepublic.pdf) provided241,772bytes, SHA256 `434a9e61432520ff58db5aa636ce4e0be092bc5a4915847c3daba2027674860a`. The six-page file contains a ResearchGate cover identifying an author upload on21September2018, followed by a manuscript with numbered pages and a2015 DOI citation footer. The cover's April2015 label, upload date, mirror path and final issue date are distinct; none establishes first availability. The manuscript's pagination is not the final issue's pp.5–9.

Lead inspected text extracted from PDFpages1–4, including the article opening and sections2.1–2.3. Relevant HTML and PDF terminology agree; byte identity with the unavailable ResearchGate download was not established. No successful visual layout check or examination of every cited underlying study is claimed. The mirror hosts a copy of the primary author's paper; it is not publisher-hosted evidence.

## Claim map

| Module claim | Inspected span | Disposition |
|---|---|---|
| Robustness and resilience are an exhaustive fortress/reed pair. | Manuscript opening, PDFpage2; section2.2, PDFpages3–4 (printed2–3). Woods distinguishes four uses of resilience and critiques conflation with robustness. | Replace the binary taxonomy with explicitly attributed terminology. It is one author's conceptual analysis, not an agreed universal classification. |
| Robustness can be assigned to an entire system without naming a property or disturbance. | Section2.2, PDFpage3, paragraph beginning “An increase in robustness”; the paragraph attributes property/perturbation specificity to Alderson and Doyle. | State the operating conditions and required performance. Cite Woods's account; do not claim direct inspection of Alderson and Doyle. |
| A frontend crash after a designed timeout establishes a robust system. | Section2.2 discusses effective responses within a disturbance set and failure at its boundary; section2.3, PDFpage4, paragraphs2–3, discusses performance near boundaries. | Reject the inference. The vignette specifies a failure outcome, not demonstrated robustness of a named property over a range of conditions. |
| A cached fallback establishes resilience to unexpected stress. | Section2.3, PDFpage4, paragraph beginning “Attempts to expand the base envelope,” distinguishes graceful extensibility from degradation. | Narrow to the stipulated fallback behavior. A planned response to database delay does not by itself demonstrate adaptation beyond the system's prepared capabilities. |
| Resilient systems keep working under unknown stress; the best design always combines both. | Section2.3, PDFpage4, acknowledges finite resources, uncertain boundaries and the risk of collapse; section2.2 continues onto that page with trade-offs. | Remove guarantees and universal design rankings. An illustration must not imply unlimited adaptability. |

## Prose direction and acceptance boundary

Use a brief attributed comparison of performance within specified conditions and adaptation when conditions challenge prepared responses. Replace the fortress/reed outcome diagrams with questions about boundaries or clearly qualified illustrations. Q4 should ask what the stated timeout responses establish and what remains unknown, including whether stale data satisfies the operation's requirements. Those API examples and investigation questions are teaching applications, not Woods's examples or empirical results.

This packet does not validate the other quiz questions, prove a software architecture superior, or establish safe stale-price behavior. It does not replace Hollnagel's separately sourced four abilities with Woods's four concepts. Independent SOURCE acceptance is required before prose changes; later PROSE review, build, CI and live checks remain separate. No whole-module or Ukrainian acceptance is claimed.
