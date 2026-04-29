# Open Questions: Chapter 44 — The Latent Space

## Yellow Claims To Resolve

- **Public word2vec release date and archive details.** Need a stable Google Code archive page, release note, or repository snapshot before saying July 2013 or describing the package history. Current status: Yellow.
- **Google News corpus composition.** The paper anchors "Google News corpus" and 6B tokens, but not the corpus composition. Do not add details about source mix, time range, or cleaning until anchored. Current status: Yellow.
- **Adoption speed.** The contract does not yet prove that Word2Vec became the default baseline "within months." A prose draft can call it influential only through textbook synthesis unless citation-history or contemporaneous workshop evidence is added. Current status: Yellow.
- **Successor lineage.** GloVe, FastText, ELMo, and BERT are real follow-ons, but the chapter should not present a tidy linear chain without primary anchors for each. Current status: Yellow and mostly out of scope.
- **Deerwester/LSA deeper details.** The p.391 abstract is enough for a compact lineage paragraph. A longer LSA scene needs full-page extraction from the article. Current status: Green for abstract-level claim, Yellow for deeper experiments.

## Red Claims To Keep Out

- **A Google "eureka moment" for King-Man+Woman=Queen.** No source found. Do not draft.
- **Vector arithmetic perfectly mirrors semantic relationships.** Primary sources and secondary synthesis both support caveats. Do not draft.
- **GPU-dependent Word2Vec training.** No extracted source supports GPU reliance; the sources emphasize CPUs, DistBelief, and optimized single-machine implementations. Do not draft.

## Archival Or Source Access That Would Help

- Google Code Archive page for `word2vec`, including initial release metadata and license.
- Contemporary blog posts, mailing-list posts, or conference slides from 2013 showing how researchers first adopted Word2Vec.
- Full Deerwester et al. 1990 article pages for LSA examples and limits.
- Interviews with Mikolov, Corrado, Dean, or Yih that discuss why the analogy benchmarks were chosen. Use only if page/time anchors are real.

## Scope Decision

The current evidence is sufficient for `capacity_plan_anchored` and a `3k-5k likely` chapter. It is not sufficient for a long personality-driven lab narrative. If the prose team wants 5k+, the missing adoption/release/interview anchors should be sourced before drafting.
