# Gap Analysis: Chapter 27 - The Convolutional Breakthrough

Source: Gemini gap analysis on PR #410, recorded 2026-04-27.

## Current Verdict

Research contract approved, and the first review follow-up has removed the largest prose-readiness blocker. Fukushima 1980, LeCun et al. 1989, LeCun et al. 1990, and LeCun et al. 1998 now have exact page anchors for architecture, datasets, preprocessing, training/hardware, throughput, and document-pipeline claims. The chapter is close to prose-ready, with remaining decisions about source-access provenance, Denker/Bell Labs lineage, and scope control.

## Claim Readiness After Follow-Up

| Claim Area | Status | Why |
|---|---|---|
| Fukushima as architectural prehistory | Green | Anchored to Fukushima 1980 pp.193-194 and pp.197-199 for hierarchy, S/C cells, shift tolerance, and cascade behavior. |
| USPS dataset details | Green | Anchored to LeCun et al. 1989 p.542 and LeCun et al. 1990 pp.397-398; later MNIST construction anchored separately to LeCun et al. 1998 pp.2286-2287. |
| LeNet-5 production pipeline | Green | Anchored to LeCun et al. 1998 pp.2278-2279, 2296-2298, and 2304-2305 for document/check systems, GTNs, segmentation, and replicated recognizers. |
| Architecture reducing search space | Green | Supported by LeCun et al. 1989 pp.541, 544-546 and LeCun et al. 1998 pp.2283-2284, 2291-2292; still phrase as interpretation grounded in parameter reduction and prior knowledge. |
| Check-volume numbers, hardware, deployment timeline | Green/Yellow | Green for specific anchors: 1989/1990 DSP and SUN/SPARC context, 1998 check-system scale. Yellow only for broader Bell Labs deployment chronology beyond the cited papers. |
| "First CNN" language | Red | Avoid unless a strongly qualified source supports it; current safer framing is lineage plus breakthrough. |

## Required Anchors Before Prose Readiness

- Confirm LeCun et al. 1989 page anchors against an access-approved copy if the team wants to avoid relying on a mirrored MIT PDF for extraction.
- Decide whether Denker et al. 1988/1989 should be added for Bell Labs lineage, or left as optional context.
- Decide how much of the LeCun et al. 1998 GTN/check-system material belongs in the final chapter without over-expanding beyond convolutional architecture.

## Scene Strength

| Scene | Strength | Notes |
|---|---|---|
| Pixels With Structure | Strong | Architecture, local receptive fields, feature maps, weight sharing, subsampling, and parameter-reduction anchors found. |
| From Neocognitron to Backprop | Strong | Fukushima hierarchy and shift-tolerance anchors found; LeCun 1990/1998 give the contrast with supervised backpropagation. |
| The Postal Code Laboratory | Strong | USPS/Buffalo data, train/test split, preprocessing, performance, training, and DSP details anchored. |
| Checks, Throughput, and Engineering | Strong | 1998 production, GTN, segmentation, NCR, and check-volume anchors found; needs scope discipline. |
| Why It Waited | Medium to strong | Compute/training context in 1998 pp.2291-2292 strengthens this scene; later retrospectives can remain secondary. |

## Word Count Assessment

- Core range now: 4,000-5,000 words.
- Stretch range with Denker lineage or archival color: 5,000-6,500 words.

The chapter can now responsibly grow as a system story: visual-architecture lineage, USPS data, constrained backpropagation, hardware/throughput, and document/check pipelines. It still should not grow by adding a generic modern CNN tutorial.

## Responsible Expansion Path

To reach 4,000-7,000 words without bloat:

- Use Fukushima 1980 as lineage, not as a claim of modern CNN invention.
- Keep USPS/Buffalo digit recognition, later MNIST construction, and 1998 bank-check systems in separate chronological lanes.
- Use hardware/throughput details as constraints that explain why architecture mattered.
- Use GTN/check-pipeline details to show the network inside a production document system, not to turn the chapter into a GTN chapter.
- Add optional Bell Labs archival demo/video material only as color after the anchored claims carry the chapter.

## Handoff Requests

- Ask Gemini to review the newly extracted anchors and decide whether Ch27 can move from `gap_analysis_received` to prose-ready after the LeCun 1989 access-provenance note is accepted.
- If Gemini wants more lineage, add Denker et al. 1988/1989 as a small supporting source set rather than expanding the chapter's core claim.
- If Gemini approves without Denker, proceed to prose outline/draft after other assigned chapters reach the same review standard.
