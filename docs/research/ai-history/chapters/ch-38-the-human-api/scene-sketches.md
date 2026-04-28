# Scene Sketches: Chapter 38 - The Human API

## Scene 1: The Catalog Problem

Amazon's storefront is no longer a tidy bookseller's shelf. It is a swelling catalog fed by many product sources, and duplicate listings begin to fracture search and shopping. The old software instinct is to write a better detector, but the task sits in an awkward zone: easy for a person comparing pictures and text, hard for the computer systems of the period. The scene should stay disciplined: IEEE Spectrum reports the duplicate-product origin and calls the problem "insurmountable" for Amazon engineers; the patent provides the verified engineering language.

The prose should then move from anecdote to architecture. US7197459B1 is not a colorful scene; it is the chapter's blueprint. A task server decomposes work into subtasks. A coordinating server dispatches those subtasks to human-operated nodes. The API describes input data, expected accuracy, time, security, and cost. That is the chapter's first turn: not "humans help computers" in the abstract, but human judgment made addressable by software.

Anchors: `sources.md` G1-G5, G27-G28.

## Scene 2: Artificial Artificial Intelligence

Open on the November 2, 2005 AWS announcement. The language is almost a miniature manifesto: humans still outperform powerful computers at tasks like identifying objects in photographs; what if the normal request flow were reversed; what if a computer program could ask a human to do the work and return the result? The public product name supplies the irony. "Mechanical Turk" points back to a machine that appeared autonomous because a human was hidden inside it, and AWS calls the new service "Artificial Artificial Intelligence."

The scene should explain the joke without letting it become an antique chess-machine detour. The important point is interface design. MTurk is presented as a web-services API, not as a staffing agency brochure. A requester no longer needs to hire a room of annotators directly; software can create tasks, set rewards, collect answers, and fold human outputs back into a larger computation.

Anchors: `sources.md` G6-G9, G29.

## Scene 3: Hidden Amazon, Exposed as Service

At MIT in September 2006, Bezos is reported as showing the "hidden Amazon": the operational machinery behind the retailer turned outward as developer services. MTurk appears in the same breath as S3 and EC2. That juxtaposition is the scene's center. Storage, compute, and human judgment are being introduced to developers as metered services.

Computerworld gives enough texture for a compact scene: about 200,000 developers registered across 10 Amazon web services; Bezos describes "pay-by-drink" experimentation; the services are things Amazon already had to do internally. Do not overstate MTurk's business success or worker scale. The scene's job is to show how the API metaphor got credibility from the broader AWS platform moment.

Anchors: `sources.md` G10-G12.

## Scene 4: Cheap and Fast - But Is It Good?

Move from Amazon's platform pitch to a researcher's bottleneck. Snow et al. open by saying human linguistic annotation is crucial but expensive and time-consuming. They choose five NLP tasks, post them through AMT, and compare non-expert labels to expert gold labels. This is the moment the "human API" becomes research method.

The prose should preserve the mechanics. AMT is an online labor market of requesters, HITs, rewards, qualifications, approvals, workers, and Amazon-mediated transactions. Snow et al. do not claim a single anonymous click is equivalent to expertise. They use redundancy, task design, aggregation, and bias correction. The strongest narrative numbers are the affect experiment's $2 for 7,000 labels and the conclusion that a small number of non-expert labels can match expert-level performance for many tasks.

Anchors: `sources.md` G13-G18.

## Scene 5: ImageNet and the Cost of the Abstraction

ImageNet lets the chapter widen from sentence labels to visual scale. Deng et al. want a database built on WordNet, eventually tens of millions of clean images, and in 2009 they already report 12 subtrees, 5,247 synsets, and 3.2 million images. The paper says traditional data collection is no longer enough. The missing machine is a crowd of humans verifying whether candidate images contain the target synset.

This scene should be technical rather than triumphant. Workers see candidate images and definitions; multiple users independently vote; categories differ in difficulty; the system uses confidence thresholds and more votes for harder distinctions. Then the chapter closes by re-opening the abstraction. To the requester, MTurk made judgment look callable. To workers, Hara et al. later show, the work involved low median hourly wages, unpaid search time, rejected tasks, and other frictions that the API hid. End with a sparse forward pointer: ImageNet's later consequences belong to Ch39.

Anchors: `sources.md` G19-G26.
