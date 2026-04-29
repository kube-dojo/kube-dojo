# Open Questions: Chapter 47 - The Depths of Vision

## Yellow Claims

- **Y1 - Exact ResNet ImageNet hardware and training time.** The ResNet paper anchors dataset scale, optimization recipe, FLOPs, and mini-batch size, but not GPU model/count or wall-clock duration for the 152-layer ImageNet runs. Do not import AlexNet's two GTX 580s or VGG's four Titan Blacks into ResNet.
- **Y2 - Highway Networks influence.** The ResNet paper mentions Highway Networks as concurrent related work, but this contract does not anchor a causal influence claim. A page anchor from the Highway paper plus an interview/source connecting the teams would be needed before saying more.
- **Y3 - Official pure-classification table for ILSVRC 2015.** The ResNet paper itself anchors the 3.57% test-server result and classification win. The fetched official ImageNet page anchors detection/localization standings, but the pure-classification table was not visible in the extracted text.

## Red Claims

- **R1 - Internal invention sequence.** No source here says which ResNet author first proposed the residual block or how the idea moved through Microsoft Research. Requires interviews, talks, oral histories, or lab records.
- **R2 - "Human-level" framing.** The legacy chapter hinted at human-level error. This contract does not anchor that comparison for ResNet. Use the verified 3.57% top-5 test error instead.
- **R3 - Lab drama and naming anecdotes.** No verified source supports late-night training scenes, deadline pressure, whiteboard dialogue, or the origin of the name "ResNet."

## Archival / Source Leads

- Kaiming He talks or interviews from 2016-2017 may clarify hardware and development sequence.
- Microsoft Research blog or archived project pages may contain non-paper infrastructure details, but must be page-anchored before use.
- Highway Networks original paper can support a careful related-work paragraph if exact page anchors are extracted.
- Batch Normalization and PReLU papers can support a short "human-level" or normalization-context note only if the prose genuinely needs it.

## Drafting Guidance

- The chapter is draftable without resolving the Red claims because the primary paper carries the technical narrative.
- The prose should hedge all Yellow claims and omit all Red claims.
- If the chapter feels thin, expand technical explanation of the anchored ResNet paper rather than inventing human scenes.
