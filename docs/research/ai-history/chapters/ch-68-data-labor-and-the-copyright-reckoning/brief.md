# Brief: Chapter 68 - Data Labor and the Copyright Reckoning

## Thesis
The modern AI race was not powered only by GPUs, scaling laws, and model
architecture. It also depended on human labor that made model behavior usable
and on contested data pipelines that converted the web, books, images, captions,
and news archives into training material. Ch68 explains how data stopped looking
like an ambient public resource and became a labor, rights, licensing, and court
fight. The chapter does not decide the legal merits. It shows the historical
turn: first the work was hidden in labeling queues and scraped corpora; then
workers, artists, authors, publishers, courts, robots.txt files, and licensing
deals made the hidden supply chain visible.

## Scope
- IN SCOPE: RLHF labeler work already introduced in Ch57; safety/content
  labeling labor; Sama/Kenya reporting with careful attribution; GPT-3-style
  Common Crawl/books mixtures; The Pile and Books3; LAION and Stable Diffusion;
  Getty v. Stability as an image-rights flashpoint; New York Times v.
  OpenAI/Microsoft as a news-rights flashpoint; Bartz v. Anthropic as the
  clearest 2025 book-corpus court record; crawler opt-outs; publisher/platform
  licensing deals; data access as strategic infrastructure.
- OUT OF SCOPE: comprehensive legal survey; predictions about case outcomes;
  treating complaint allegations as adjudicated facts; all AI copyright suits;
  full social-media content-moderation history; technical synthetic-data and
  data-exhaustion strategies covered in Ch69; physical datacenter limits covered
  in Ch70 and Ch72.

## Required Scenes

1. **The Human Filter:** Ouyang et al. show the respectable research version of
   human-feedback labor: demonstrations, rankings, reward models, PPO, and about
   40 contractors. TIME's Sama reporting shows a harsher safety-labeling layer:
   outsourced workers handling toxic or explicit material under contested
   conditions. Keep the two evidence types separate.
2. **The Scraped Corpus:** GPT-3, The Pile, Common Crawl, and Books3 show the
   normal research language of "datasets" and "corpora." The prose should show
   how this language made web pages and books look like input material before
   rights holders had a stable response.
3. **The Image Dataset Flashpoint:** LAION-5B and the Stable Diffusion model
   card make image-caption training concrete; Getty's statement and complaint
   show how image owners translated dataset use into copyright, trademark,
   metadata, and watermark claims.
4. **The Newspaper And Book Reckoning:** The NYT complaint, OpenAI response,
   2025 motion-to-dismiss opinion, and Bartz/Anthropic fair-use order show the
   courtroom phase. Allegations, company defenses, and court rulings must be
   lexically separated.
5. **From Commons To Enclosure:** GPTBot/OAI-SearchBot rules, Reddit's Data API
   partnership, and publisher deals with Axel Springer, the Financial Times, and
   News Corp show the endpoint: data access becomes negotiated, blocked,
   attributed, licensed, or priced.

## Prose Capacity Plan

Target range: 4,500-5,500 words after source verification.

- 500-650 words: bridge from Ch67's platform gates to the less visible data
  gate: the model stack needs people and rights-cleared material, not just
  compute.
- 850-1,000 words: the human filter. Use Ch57/Ouyang for the research pipeline
  and TIME for Sama/Kenya reporting. Do not turn anonymous workers into scenery.
- 800-950 words: the scraped corpus. Explain Common Crawl, GPT-3's training
  mixture, The Pile's 825 GiB/22-subset design, and Books3 as a named book
  component that later becomes legally salient.
- 800-1,000 words: the image flashpoint. LAION-5B, Stable Diffusion v1-4, Getty's
  claim of copied images/captions/metadata, and watermark/trademark allegations.
- 900-1,100 words: the news/book courtroom phase. NYT allegations, OpenAI's fair
  use/opt-out/regurgitation framing, the 2025 NYT motion-to-dismiss narrowing,
  and the Bartz/Anthropic order's split between training copies, purchased
  scanning, and pirated library copies.
- 600-800 words: enclosure close. Robots.txt/crawler controls, publisher
  licensing, Reddit Data API, and handoff to Ch69's question: what happens when
  high-quality human data becomes scarce, expensive, or legally fenced?

## Guardrails

- Do not make legal conclusions the sources do not support.
- Do not conflate labor conditions across vendors or countries without evidence.
- Do not treat all scraping as legally identical.
- Do not say "training is legal" or "training is illegal" as a general rule.
  The 2025 Bartz/Anthropic order is one district-court order with a narrow
  posture and a split result.
- Do not imply OpenAI, Stability, Anthropic, Meta, or any other lab used a
  dataset unless a primary source, court record, model card, or company
  statement supports that specific claim.
- Do not let this become the technical synthetic-data chapter; that is Chapter
  69.
- Date all legal status statements. As of April 28, 2026, several AI copyright
  disputes remain active or settlement-finality-sensitive.
