# KubeDojo content review and expansion plan

Review date: 2026-09-04. Baseline: `8dd9bbd4cccffdef62b426cf987a0e4c5a8c92cb`.

This is the initial sampled audit. The user's subsequent whole-site mandate is implemented by the [complete upgrade program](content-upgrade/README.md) and GitHub epic #2272; initial pilot suggestions here do not limit that program or impose mystery/gamification as a writing style.

## Editorial judgment

KubeDojo has enough breadth to be a substantial learning library. Its next improvement should make that library easier to enter, practice with, and remember. More pages alone will not solve the largest observed problems. Expand learner experiences selectively; edit repetition and expose a manageable core route through the existing depth.

The history book has a distinctive infrastructure-centered premise. Preserve that identity, its mathematical explanations, and its care around historical evidence. Give it stronger narrative pacing and optional experiments rather than converting every chapter into a curriculum template.

## Scope and limits

This is a planning audit: whole-tree file inventory, live local API inspection, implementation inspection of quality/progress signals, existing-plan reconciliation, and representative content reads by the lead and three bounded scouts. It is not a full technical certification audit, a fact check of every historical claim, a lab execution pass, or verification of the deployed website. Files in the Astro source tree establish content presence, not deployment or historical correctness. No curriculum or book prose was changed.

### Inventory

Counts use `.md`/`.mdx` files in `src/content/docs`; module counts use `module-*.md`; book chapters use `ai-history/ch-*.md`. Ukrainian counterparts mean an existing file at the exact mirrored path, not verified translation quality or freshness.

| Track | EN modules / chapters | Exact UK counterparts | Approximate median words |
|---|---:|---:|---:|
| Prerequisites | 44 | 44 | 7,544 |
| Linux | 37 | 37 | 7,485 |
| Kubernetes | 195 | 195 | 7,522 |
| Cloud | 92 | 78 | 9,064 |
| Platform | 242 | 3 | 7,533 |
| On-premises | 57 | 0 | 8,040 |
| AI literacy / workflows | 37 | 37 | 7,590 |
| AI/ML Engineering | 124 | 0 | 7,373 |
| AI history book | 73 | 10 | 4,831 |

Total: 1,639 Markdown/MDX files including hubs and translations; 828 English curriculum modules. Word estimates remove frontmatter and triple-backtick blocks, then split on whitespace. They still include tables, sources, and markup; use them to flag workload, not as reading-time measurements.

## Highest-confidence findings

### 1. The quality score has exhausted its usefulness for prioritization

The live `/api/quality/scores` returned 828/828 modules at 5.0. Its implementation (`scripts/local_api.py:2512`) rewards line count, title, quiz/exercise headings, and a diagram signal that also accepts `<details>`. A linked Sources section removes the citation penalty; the function does not verify claim support. This is a structural heuristic, not evidence that every lesson is excellent.

The separate readiness endpoint reported 176/828 cleared (21.3%). Its definition (`scripts/local_api.py:4011`) checks `revision_pending` and `citations_verified` frontmatter. The remaining 652 are not proven bad lessons: their clearance metadata does not meet that definition.

Action: label structural compliance, source verification, editorial review, runnable-lab validation, and learner performance separately. Keep existing gates; add a small manually reviewed calibration set that reveals actual differences. Do not mass-rewrite 652 modules based on metadata alone.

### 2. Entry-level lessons ask too much before the learner gets a small win

`src/content/docs/prerequisites/zero-to-terminal/module-0.1-what-is-a-computer.md:8` promises QUICK / 35 minutes while containing approximately 7,660 words excluding code and frontmatter. Its kitchen analogy and diagnostic framing are useful; the volume is the problem to test. Across the corpus, long median lengths make workload a systemic concern, although length alone cannot establish poor pedagogy.

Action: pilot a clearly marked essential route, first practical success early in the lesson, and optional deeper sections. Measure actual read-and-do time with beginners. Preserve advanced explanation rather than merely deleting it or mechanically splitting files. If editorial findings require changes to established word-floor policy, propose that policy revision separately; do not quietly weaken gates.

The verifier defaults to a 5,000-word minimum unless a module budget overrides it (`scripts/quality/verify_module.py:596`). That creates an incentive toward volume and deserves explicit evaluation for introductory lessons. It does not prove that the observed prose was padded, but editorial quality and minimum length should not be treated as interchangeable.

### 3. Several previously proposed improvements already exist

`docs/curriculum-route-action-plan.md` proposes persona routes and certification-prep completion. The platform hub already has SRE, DevEx, and architect entry routes (`src/content/docs/platform/index.md:35`). LFCS/CNPE mock-exam files and CNPA/CGOA exam-strategy files exist. Presence does not prove sufficient exam coverage, but these cannot be reported as absent without deeper inspection.

Action: reconcile the old backlog before opening new work. Improve the continuity and outcomes of existing routes rather than creating parallel hubs that compete with them.

### 4. Ukrainian learners encounter a substantial advanced-track discontinuity

Exact-path parity is complete for prerequisite, Linux, Kubernetes, and AI module files, but AI/ML Engineering has 0/124, Platform 3/242, and On-premises 0/57. This is a concrete coverage gap. It does not establish whether present translations are current or readable.

Action: translate a complete useful route first, after its English pilot stabilizes. Include setup instructions, quiz explanations, diagrams, and capstone assets. Track source revision and terminology review. Avoid translating prose that is immediately due for substantial restructuring.

There is also a verified fidelity problem in present material: `uk/ai/foundations/module-1.1-what-is-ai.md:22` requires scripting and infrastructure terminology and teaches infrastructure automation; the English counterpart's outcomes and introduction (`ai/foundations/module-1.1-what-is-ai.md:17`) target everyday beginners. Both paths are under `src/content/docs/`. Repair this audience drift before claiming the introductory route has translation parity. The Ukrainian AI hub also points toward a missing Ukrainian AI/ML directory; verify route resolution and provide an explicitly labeled English fallback until a translated route exists.

### 5. The book's operational map needs reconciliation

The public-source book index describes 73 chapters; `docs/research/ai-history/README.md` and the comprehensive roadmap still describe 72 and contain older drafting-status statements. Separate chapter presence, accepted editorial state, evidence readiness, and deployment. Reconcile chapter contracts and review records before expanding or changing a chapter's acceptance status.

In Chapter 15, useful explanations of the different gradient-method lineages are repeated in the introduction and closing sections. The section heading “The Modern Reinterpretation, and Where Ch15 Stops” (`src/content/docs/ai-history/ch-15-the-gradient-descent-concept.md:151`) exposes editorial boundary language to readers. This is a candidate for tightening, not a factual verdict on the chapter.

The book scout read Chapters 1, 36, 72, and 73 and inspected the chapter structures and research statuses. The lead independently reproduced three important counts: only 12/73 chapters have a `## Sources` heading; 36/73 have no level-two narrative headings; there are 72 research status files and no Ch73 contract directory. Missing Sources headings do not establish that every claim is unsourced, but reader-visible provenance is inconsistent. The absence of headings is a strong scanability concern for long chapters, not proof of weak reasoning.

The scout found 40 research statuses marked `accepted`, 11 `prose_ready`, and 21 `capacity_plan_anchored`. These are recorded states, not fresh review verdicts. For example, Ch39's status combines `capacity_plan_anchored` with `prose_state: published_on_main`. Ch73 is already linked as the final chapter; the practical default is to bring its evidence contract and review tracking into alignment, not remove it. Do not silently promote the other chapter statuses to accepted.

Book priorities ahead of expansion: expose checked source references for the 61 chapters without a Sources heading; section the 36 long unsectioned chapters according to their narrative beats; reconcile Ch73's research contract; and audit dated claims in Ch59–73. Reuse verified contract anchors, but do not mechanically turn an unverified source list into a claim of verification. The sampled Ch36 causal structure and Ch72 distinctions between announcements and operational capacity are strengths worth preserving. Ch73's learning aids are promising, while its editorial language and repeated thesis need a dedicated prose pass.

### 6. Several sampled exercises under-test their promised outcomes

The general curriculum scout fully read seven modules. These are source-review findings; commands were not executed.

| Sample | Observed gap | Specific improvement |
|---|---|---|
| Kubernetes Basics, Deployments (`src/content/docs/prerequisites/kubernetes-basics/module-1.4-deployments.md:455`) | Lab updates to a valid image and rolls back; the comment says “simulate problem” without introducing one. | Add a broken-image or readiness failure and require the learner to use events to choose repair or rollback. |
| Cloud Native 101, What Is Kubernetes (`src/content/docs/prerequisites/cloud-native-101/module-1.3-what-is-kubernetes.md:450`) | Lab inspects a cluster and creates/deletes a Pod, while outcomes promise diagnosis and architectural judgment. | Add one bounded failure diagnosis and a justified deployment choice. |
| Linux troubleshooting (`src/content/docs/linux/operations/troubleshooting/module-6.1-systematic-troubleshooting.md:549`) | Exercise reveals the injected cause and expected diagnosis. | Present symptoms first; keep the cause in a separate fixture or collapsed solution and require supporting evidence. |
| AWS VPC (`src/content/docs/cloud/aws-essentials/module-1.2-vpc.md:490`) | The substantial provisioning lab introduces its cost warning late, depends on an optional IAM setup for flow logs, and lacks a minimal traffic test. | Move cost/setup requirements before provisioning; supply the IAM prerequisite and cleanup; test actual traffic, not just object existence. Verify current provider documentation before revising or running it. |
| Systems Thinking (`src/content/docs/platform/foundations/systems-thinking/module-1.1-what-is-systems-thinking.md:443`) | Toy simulation and substantially solved scenario offer limited transfer evidence. | Provide an unfamiliar evidence packet and competing interventions; require the learner to defend a boundary and trade-off. |

The AI scout read three hubs and three complete modules. Preserve the decision ladder in Tools, Retrieval, and Boundaries and the cumulative numerical work in Neural Network Math Warm-Up. Its heading scans flagged candidate assessment and metadata inconsistencies, but alternate section names can produce false positives: manually verify these before making a missing-section backlog. Do not fill heading quotas merely to improve a structural score. Clearly labeled hypothetical teaching scenarios are legitimate; they do not need invented historical citations.

## What to build next

### Curriculum: a continuing project with varied challenges

Choose one explicitly fictional teaching service—such as a small community events application—and let it recur through a bounded route. Label simulated incidents as simulations. Keep real historical incidents sourced.

1. Run it locally and observe files, processes, ports, and logs.
2. Put it in a container and deploy it to a local cluster.
3. Diagnose one failure from symptoms, with progressive hints and a clean reset.
4. Add a reliability objective and defend a monitoring decision.
5. Add a small retrieval feature and evaluate it against a fixed test set.

Reuse relevant modules and labs; add only the missing transitions and artifacts. Make each milestone independently useful so a beginner does not need the entire platform track to finish something.

Alternate activity types: predict an output before running it; find the misleading graph; choose between two plausible fixes; repair a broken manifest; explain a result to a teammate; compare a working baseline with a more elaborate model. “Fun” should come from discovery and increasing competence, with occasional light humor grounded in the task.

Existing `src/components/LabProgress.ts` and `LabBanner.astro` already support local progress and user-marked completion. Extend this experience only after the pilot demonstrates a need. A completion click is distinct from demonstrated mastery; offer a small transfer challenge and a later recall prompt without requiring accounts or a new gamification platform.

### Book: strengthen the reading experience before adding more chapters

Offer curated entry routes through the existing book: a short essential arc, the full chronology, and thematic routes for mathematics, machines, or people and institutions. Name exact chapter destinations and prerequisite concepts. The current “quick” orientation is itself described as roughly 13,000 words, so add a genuinely brief orientation rather than sending time-constrained readers to another long assignment.

For selected chapters, use: a documented problem or puzzle; the people facing it; the constraints on their choices; the key idea; an accessible demonstration; what changed and what remained unresolved. Vary chapter form to suit the evidence. Do not impose seven identical boxes on all 73 chapters.

Pilot companion activities outside the main narrative:

- Perceptron: move points and discover which arrangements one boundary cannot separate.
- Gradient descent: choose a step size and predict the next move on a simple curve before revealing it.
- Evaluation: compare two systems on a deliberately limited test set, then change the test distribution.

These are proposed teaching activities, not claims that historical actors performed them. Each must have a text/table fallback, keyboard access if interactive, a learning objective, and a clear explanation of the model's limitations.

Audit continuity for classical statistics, causal reasoning, robotics/control, non-US research, and data labor across the existing chapter map. These are coverage questions, not established missing topics: the modern matrix already explicitly routes data labor, evaluation, agents, and geopolitical constraints. Prefer stronger connections or a sidebar when an existing chapter can carry the explanation; add a chapter only after documenting a real structural gap.

## Delivery sequence and acceptance criteria

| Priority | Bounded packet | Output | Acceptance |
|---|---|---|---|
| P0 | Reconcile inventory, old plans, and book status | One current backlog with evidence and explicit unknowns | No absent-content claim based solely on an old plan; no status upgrade without review evidence |
| P0 | Calibrate review signals | Small stratified editorial sample plus separately labeled structural/source/lab signals | Review distinguishes strong and weak examples; every finding cites text or learner behavior |
| P0 | Repair the clearest route/lab mismatches | Ukrainian introductory fidelity fix, deliberate language fallback, AWS VPC preflight and behavioral test plan | Audience matches EN; routes resolve intentionally; cloud lab requirements and costs are visible before provisioning |
| P1 | Beginner pilot: first three zero-to-terminal lessons | Essential route, early practical win, optional depth, honest timings | New learner completes setup and an unseen small task; confusion and actual duration recorded |
| P1 | Book pilot: Ch14–15 and their transition | Tightened narrative, optional demonstration, source-preserving edit | Independent source-fidelity and prose review; reader can explain the key distinction without notes |
| P1 | AI builder pilot | One short path ending in an evaluated working artifact | Runs from a clean environment; learner can explain one failure and the evaluation result |
| P2 | Cross-track capstone | Reusable service, fault fixtures, hints, checks, reset/cleanup | Success verified from outputs; another learner reproduces setup and teardown |
| P2 | Ukrainian route parity | One complete stabilized route with all companion material | EN-to-UK fidelity and natural-language review; revision freshness recorded |
| P3 | Broader expansion | Small batches based on pilot evidence | Retain only patterns that improve completion, understanding, or transfer |

Treat this as a sequence of experiments, not a promised calendar. Start with a few representative readers for qualitative observation; do not infer statistical effect sizes from that small group. Record time to first success, setup failure, hint use, ability to solve an unfamiliar variant, and delayed explanation/recall. Ask where readers became bored or confused. Page views and completion clicks alone cannot answer those questions.

For execution, keep one lead and at most three disjoint packets active: curriculum pilot, book pilot, and validation/reader feedback. Use the live available worker catalog and quotas. Cross-family review remains required before shipping; the scouts in this audit are all OpenAI-family and do not constitute cross-family clearance. No mass rewrite, PR posting, merge, or deployment is part of this planning deliverable.

## Learning-design evidence

The practice and feedback recommendations follow [Carnegie Mellon's learning principles](https://www.cmu.edu/teaching/principles/learning.html). Short recall checks and revisiting earlier material follow [CMU's retrieval-practice guidance](https://www.cmu.edu/teaching/resources/instructionalstrategies/activelearningstrategies/retrievalpractice/index.html) and the [Australian Education Research Organisation's spacing and retrieval guide](https://www.edresearch.edu.au/guides-resources/practice-guides/spacing-and-retrieval-practice-guide-full-publication). Their application to KubeDojo is a proposed design to test with learners, not an established result for this site.
