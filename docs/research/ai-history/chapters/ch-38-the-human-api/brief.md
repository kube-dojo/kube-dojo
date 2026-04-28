# Brief: Chapter 38 - The Human API

## Thesis

Amazon Mechanical Turk mattered to AI history less as a clever crowdsourcing website than as a new infrastructure shape: human judgment packaged behind a web-service interface. Amazon's public 2005 announcement described a reversed human-computer relationship in which a computer program could ask people to perform tasks and return results; the underlying patent language made the same move in engineering terms, decomposing tasks into subtasks, dispatching them to human-operated nodes, and exposing the arrangement through an API. Once that abstraction existed, machine-learning researchers could buy annotation as an elastic service. Snow et al. showed in 2008 that small groups of non-expert MTurk workers could produce useful NLP labels cheaply, and ImageNet showed in 2009 how crowd labor could become part of the operating system for large visual datasets. The chapter's claim is not that MTurk invented human computation, crowdsourcing, or annotation, but that it made paid, distributed human cognition look callable, meterable, and scalable at exactly the moment supervised learning needed labels.

## Scope

- IN SCOPE: Amazon's internal duplicate-catalog problem as a secondary-source origin story; Harinarayan/Rajaraman/Ranganathan's "hybrid machine/human computing arrangement" patent; Amazon's November 2, 2005 public MTurk announcement; Bezos's 2006 "hidden Amazon" developer-services framing; the phrase "Artificial Artificial Intelligence"; MTurk's HIT/requester/worker/API mechanics; Snow et al. 2008 as an early NLP validation case; ImageNet 2009 as the chapter's computer-vision scale case; the labor abstraction and wage caveat needed to keep the "human API" metaphor honest.
- OUT OF SCOPE: full labor-history treatment of crowdwork; global gig-economy regulation; content moderation; reinforcement learning from human feedback; Scale AI, Sama, Appen, Figure Eight/CrowdFlower, and later data-labeling firms except as sparse forward pointers; AlexNet and ImageNet competition consequences (see Ch39); foundation-model RLHF pipelines (see later chapters).

## Boundary Contract

This chapter must not say MTurk "created" crowdsourcing, human computation, or data annotation. Von Ahn and Dabbish's ESP Game and Open Mind-style volunteer annotation predate MTurk, and conventional expert/graduate-student annotation predates both. The chapter also must not present Amazon's catalog origin as primary-sourced unless a Bezos transcript, internal memo, or patent/application file explicitly ties the patent to duplicate product pages. That origin is usable as an anchored secondary claim via IEEE Spectrum and Pew, not as an archival fact.

The chapter must not claim that MTurk directly caused deep learning's later breakthroughs. It can say ImageNet's 2009 construction used AMT for image verification and that ImageNet later became central to Ch39's story. It must not anticipate Ch39's argument about ImageNet, GPUs, AlexNet, or benchmark culture beyond a short pointer.

The chapter must also keep labor claims narrow. The wage and invisibility material is necessary because "API" is an abstraction over people, but a full political economy of microwork belongs elsewhere. Use Hara et al. 2018 to mark the cost of abstraction; do not turn the chapter into a comprehensive worker-rights survey.

## Scenes Outline

1. **The Catalog Problem.** Amazon's product catalog accumulates duplicate entries; secondary sources report that ordinary software could not reliably resolve the image/text similarity problem. The patent gives the engineering abstraction: split tasks into human-performable subtasks and collect results through a coordinating server.
2. **Artificial Artificial Intelligence.** Amazon launches MTurk publicly on November 2, 2005 as a web-services API that lets programs ask people to do tasks computers handle poorly. The name deliberately echoes the 18th-century Mechanical Turk illusion.
3. **Hidden Amazon, Exposed as Service.** Bezos presents MTurk beside S3 and EC2 at MIT in 2006 as part of developer-facing AWS. The important shift is not only outsourcing work, but making Amazon's internal operational machinery available as pay-by-use infrastructure.
4. **Cheap and Fast - But Is It Good?** Snow, O'Connor, Jurafsky, and Ng test MTurk on five NLP annotation tasks and report that aggregated non-expert labels can approach expert labels at much lower cost, while also needing task design, redundancy, and bias correction.
5. **ImageNet and the Cost of the Abstraction.** Deng et al. use AMT to verify millions of candidate images for ImageNet, relying on multiple human votes and confidence thresholds. The closing turn shows what the API metaphor hides: workers, piece rates, unpaid search time, and wage distributions measured later by Hara et al.

## Prose Capacity Plan

This chapter supports a medium-length narrative if it spends words where the anchors are strongest:

- 650-900 words: **The Amazon catalog problem and the patentable abstraction** - set up why duplicate catalog cleaning was hard for conventional software, then pivot to the patent's "hybrid machine/human computing arrangement": task decomposition, subtasks, human-operated nodes, central server, API, accuracy/cost/time parameters. Anchored to: `sources.md` Green claims G1-G5 (US7197459B1 Info and Summary/Description anchors; IEEE Spectrum "Mechanical Turk Revisited" section, lines 97-106). Scene: 1.
- 650-900 words: **The public launch of Artificial Artificial Intelligence** - Amazon's November 2, 2005 announcement, the reversal of the normal human-computer request direction, and the claim that MTurk supplied a web-services API for integrating "Artificial Artificial Intelligence" into processing. Explain the name with Pew's historical note on the original Mechanical Turk, without overloading the chess-automaton backstory. Anchored to: `sources.md` Green claims G6-G9 and G29 (AWS announcement title/date/body, lines 27-32; Pew "What is Mechanical Turk?", lines 145-148). Scene: 2.
- 550-800 words: **AWS as the delivery vehicle** - Bezos's September 27, 2006 MIT "hidden Amazon" keynote as reported by Computerworld; MTurk grouped with S3 and EC2; 200,000 registered developers across 10 web services; the "pay-by-drink" and internal-tools-exposed-as-services framing. Anchored to: `sources.md` Green claims G10-G12 (Computerworld lines 228-242). Scene: 3.
- 850-1,200 words: **MTurk becomes research annotation infrastructure** - Snow et al.'s NLP validation: five tasks, HIT mechanics, non-expert aggregation, 10 labels per item, $2 for 7,000 affect labels, roughly 3,500 labels per dollar, and conclusion that many tasks need only a small number of non-expert labels to match expert-level quality. Anchored to: `sources.md` Green claims G13-G17 (Snow et al. 2008 pp. 254-263, especially pp. 254-257 and p. 262). Scene: 4.
- 900-1,300 words: **ImageNet scale and the hidden worker close** - Deng et al.'s 2009 ImageNet paper: 12 subtrees, 5,247 synsets, 3.2 million images, WordNet goal, AMT cleaning pipeline, multiple independent workers, confidence thresholds, and reported precision. Close with Hara et al.'s later wage data as a boundary warning: the API made annotation look frictionless to requesters while workers bore search time, rejection risk, and low median hourly wages. Anchored to: `sources.md` Green claims G19-G26 (ImageNet 2009 pp. 248-252; Hara et al. 2018 pp. 1-4). Scene: 5.

Total: **3,600-5,100 words**. Label: `3k-5k likely` - the launch, patent, Snow, and ImageNet anchors are strong enough for a substantial chapter, but the Amazon internal-origin scene and Bezos/Pontin details remain partly secondary or inaccessible, so the upper end should not be forced.

If the verified evidence runs out, cap the chapter.

## Citation Bar

- Minimum primary/near-primary anchors before prose: AWS Nov. 2, 2005 announcement; US7197459B1 patent; Computerworld's Sept. 27, 2006 MIT keynote report; Snow et al. 2008 ACL PDF; Deng et al. 2009 ImageNet PDF.
- Minimum secondary/context anchors before prose: IEEE Spectrum 2019 "Mechanical Turk Revisited"; Pew Research Center 2016 explainer; Hara et al. 2018 CHI wage analysis.
- Do not quote Pontin/New York Times directly unless the article text is accessed through a legitimate archive or database.

## Conflict Notes

- **Who "invented" MTurk?** Pew credits Bezos with the website idea; IEEE Spectrum foregrounds Venky Harinarayan and the patent; the patent lists Harinarayan, Anand Rajaraman, and Anand Ranganathan as inventors and Amazon Technologies as original assignee. Treat invention as organizational and avoid a single-hero claim.
- **Amazon catalog origin.** IEEE Spectrum and Fair Crowd Work report the duplicate-product origin, but the public patent is more general and does not by itself prove the duplicate-product use case. Keep the catalog scene anchored as secondary until an internal Amazon source or Bezos transcript is found.
- **Launch date nuance.** AWS's public announcement is November 2, 2005. The patent priority date is March 19, 2001, filing date October 12, 2001, and publication/grant date March 27, 2007. Do not collapse these into a single origin date.
- **"Cheap" for whom?** Snow et al. legitimately show low requester cost and useful labels in specific NLP tasks. Hara et al. later show low worker earnings. The prose must hold both truths at once.

## Honest Prose-Capacity Estimate

Current anchored estimate: **3,600-5,100 words**. The chapter can reach the lower-to-middle range from verified sources without padding. Reaching a 6,000+ word chapter would require legitimate access to the New York Times/Pontin article text, Bezos's 2006 MIT transcript or video, Amazon internal launch materials, or interviews with MTurk builders. Without those, keep the chapter compact and evidence-driven.
