# Open Questions: Chapter 39 - The Vision Wall

## Yellow Claims To Resolve

- **VOC plateau curve:** Extract Everingham et al. 2015 PDF figures/tables. The chapter can currently say that top 2010 PASCAL methods were not statistically distinguishable per Torralba-Efros's citation, but not that "accuracy plateaued around 2010" across most classes.
- **Workshop-level sentiment:** Find VOC workshop papers, invited talks, or participant retrospectives that describe incremental gains or frustration. Without these, do not write conference-room drama.
- **ImageNet motivation:** Leave Fei-Fei Li, Jia Deng, and ImageNet project motivation mostly to Ch40 unless page anchors from memoir/interviews/ImageNet papers are added here.
- **Causal split between algorithms, data, and compute:** Ch39 can document hand-designed features plus dataset-bias/scale pressure. It cannot prove a monocausal "data was the only bottleneck" thesis.

## Red Claims Not To Draft

- Exact annual VOC leaderboard plateau without the Everingham figure/table.
- Private conversations or motives behind ImageNet's creation.
- Claims that PASCAL-trained systems failed catastrophically in the real world; use measured cross-dataset generalization instead.

## Archival or Access Requests

- Network-enabled shell access to fetch `everingham15.pdf` or Edinburgh's accepted manuscript and run `pdftotext`.
- Physical or ebook access to Fei-Fei Li, *The Worlds I See*, for page anchors if Ch39 needs a one-paragraph handoff.
- Any preserved VOC workshop proceedings/slides from 2008-2012 that discuss plateau, benchmark overfitting, or participants' method descriptions.
- Direct HAL PDF extraction for Dalal-Triggs 2005, to replace browser-indexed abstract anchoring with local text extraction.

## Drafting Guidance

- Keep the chapter's rhetoric balanced: VOC is successful infrastructure that exposed limits.
- Use "dataset bias," "cross-dataset generalization," "negative-set bias," and "sample value" because those are anchored terms in Torralba-Efros.
- Avoid "starved for variance" unless immediately tied to G19-G21 and framed as an interpretation of their data-value and negative-set analysis.
