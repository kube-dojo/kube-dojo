# July 8, 2015 outage opener: evidence boundary

Issue #2381; parent #2282; epic #2272. Research draft checked 2026-09-05, not independently reviewed or approved for publication. The current module is `src/content/docs/platform/foundations/systems-thinking/module-1.4-complexity-and-emergent-behavior.md`, opening section. This packet addresses that opening only.

## Retrieved primary evidence

1. [CSIS event record](https://www.csis.org/events/statesmens-forum-dhs-secretary-jeh-johnson), July 8, 2015, 1–2 p.m. EDT; [hosted transcript](https://csis-website-prod.s3.amazonaws.com/s3fs-public/event/150708_Statesmens_Forum_DHS_Johnson_Transcript.pdf#page=3), PDF page 3, first substantive paragraph of Jeh Johnson's remarks. He acknowledged the three organizations' malfunctions, gave a preliminary non-malicious assessment for United and NYSE, and explicitly had less information about WSJ. This is evidence of his contemporaneous assessment, not three completed investigations or proof of causal independence.
2. [SEC staff analysis of the NYSE suspension](https://www.sec.gov/file/corporate-stock-trading-volume-spreads-and-depth-during-and-after-nyse-trading-suspension-july), PDF page 1, “What Happened”: NYSE suspended trading on its exchange from 11:32 a.m. to 3:10 p.m., a 3h38m interval. PDF page 4 discusses migration to other exchanges. This distinguishes an exchange outage from cessation of all trading in its listed stocks. It does not establish United's or WSJ's technical cause.

CSIS PDF retrieval: HTTP200 at 2026-09-05 08:12:37 UTC, 220873 bytes, SHA256 `264c2190459dee0a950f6c89be6d256c550b58201eded73c3eed2d4a6b44f9ea`. Sixteen PDF pages. Page 3 was rendered locally and visually inspected; no printed page number was visible, so use PDF page 3 rather than inventing pagination. Cache and receipt are local under `.agent/sources/` in the research worktree; exclude them from a PR.

SEC evidence was read through the web tool's PDF extraction (23 pages). Direct local download returned HTTP403; no local bytes, hash, or visual validation are claimed. Web screenshot attempts failed. The CSIS event page also returned403 through the web tool, but direct public retrieval exposed the hosted transcript link and the PDF fetched successfully. These are access limitations, not evidence that the documents do not exist.

## Claims the current opener must not retain without more evidence

| Current claim | Disposition |
|---|---|
| Each organization subsequently reported an independent cause with no shared dependency | Not established by the retrieved primary sources. Do not turn a preliminary assessment about attackers into a dependency analysis. |
| United's problem was specifically router configuration | A secondary report carries a company statement about a router issue; this packet has not retrieved a primary configuration postmortem. Do not silently strengthen “issue” to “configuration.” |
| WSJ's own delivery stack caused its disruption | Not established. The contemporary primary transcript explicitly limits knowledge about WSJ. |
| Engineers at all three had mostly healthy dashboards, ambiguous component symptoms and pressure to name one villain | No supporting operational records retrieved. These scene details must be removed or sourced, not narrated as witnessed facts. |
| Coincident outages demonstrate emergence or make safety efforts futile | An editorial leap, not a result established by these incidents. Teach uncertainty, scope and evidence rather than inevitability. |

Secondary news results were useful discovery leads, not accepted technical-cause evidence. No direct company postmortem for all three was located in this bounded pass; this is not a claim that none exists.

## Proposed editorial direction

Use the actual uncertainty as the learning problem. Present the time and scope of the NYSE disruption from SEC evidence; explain what the contemporaneous official statement did and did not establish. Ask the reader which observations would discriminate between shared and separate failures. Avoid reconstructing dashboards, operator thoughts, root dependencies or a conspiracy narrative.

Suggested question: “Before choosing a common-cause explanation, what timestamps, affected services and dependency evidence would you request? Which of those do these two sources actually provide?” A reveal can distinguish observed events, attributed preliminary assessment and still-missing cause evidence. Label that diagnostic question as a reader exercise, not an account of what the incident teams did.

This is a replacement plan for unsupported prose, not acceptance of the rest of the module. Before publication: independent source review, scoped prose revision and Google review, normal published-content tests/build/render/CI, then live smoke. Do not close #2381 on this research draft alone.
