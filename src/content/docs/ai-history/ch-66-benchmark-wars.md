---
title: "Chapter 66: Benchmark Wars"
description: "How AI evaluation moved from shared scientific tasks into product claims, public leaderboards, procurement signals, contamination disputes, and political power."
sidebar:
  order: 66
---

Benchmarks began as instruments of humility.

A shared task is supposed to make a field less vague. Instead of arguing about which system "understands" language, recognizes images, translates text, or solves software problems, researchers agree on a task, a dataset, a metric, and a submission rule. The agreement is never perfect. The dataset is always partial. The metric always loses something. But the shared frame lets a community compare systems without relying entirely on rhetoric.

That older culture mattered. Speech recognition, machine translation, information retrieval, computer vision, and many other AI subfields became more empirical because common tasks made progress visible. Chapter 32 described the DARPA evaluation style that pushed research toward measured performance. Chapter 43 described ImageNet as a public scoreboard for vision. Those scoreboards did not make the science pure, but they did discipline it. A laboratory could still tell a story about its method, but the story had to meet a test.

In the foundation-model era, that tradition mutated.

The benchmark table moved out of the paper appendix and into the product launch. It became investor evidence, procurement shorthand, public-relations ammunition, regulatory language, and community sport. A new model did not only need to work. It needed to beat something, top something, close a gap, set a record, or appear in a chart that made general capability look legible.

This was not a simple corruption of science by marketing. Benchmarks remained necessary. Without evaluation, the field would drown in demonstrations, cherry-picked prompts, and theatrical screenshots. But once scores became central to reputation, they also became targets. The metric was no longer just observing the system. It was shaping the system.

That is the benchmark war: the struggle over which tests count, who controls them, how they are scored, how easily they can be gamed, whether the test data leaked into training, and whether a number can represent the messy social fact people actually care about. Is the model useful? Is it safe? Is it reliable under pressure? Is it better than the alternatives? Is it worth paying for? Is it good enough to regulate around, procure, deploy, or trust?

No single benchmark can answer those questions. But in the product shock after 2022, benchmarks became one of the main languages people used to ask them.

Open weights made the pressure worse. Chapter 65 ended with downloadable models, adapters, quantization, hosting platforms, and community fine-tunes. Once many actors could produce plausible alternatives to closed systems, comparison became a market ritual. A model with no benchmark result looked invisible. A model with a strong result looked serious. A model that climbed a public leaderboard could become news before many users had tested it carefully.

The evaluation layer became infrastructure.

It was not only a scoreboard. It was a trust layer, a marketing layer, a research layer, and a governance layer at once.

MMLU made broad model comparison feel concrete.

In 2020, Dan Hendrycks and collaborators introduced Measuring Massive Multitask Language Understanding as a benchmark across 57 academic and professional subjects. The list mattered because it made the claim feel broad: mathematics, computer science, history, law, medicine, ethics, and other domains were brought under one evaluation roof. The benchmark was not asking whether a model could complete a single language task. It was asking whether a model could answer questions across a wide slice of learned human knowledge.

The original MMLU paper was not a victory parade. It reported that the largest GPT-3 model reached 43.9 percent accuracy and remained far below expert-level performance. That historical detail is important because MMLU did not begin as a trophy for frontier labs. It began as a way to expose the gap between impressive language modeling and broad reliable knowledge. A model could generate fluent text and still fail many questions that a trained person would answer.

The benchmark's design also carried a story about generality. Earlier NLP benchmarks often focused on narrower skills: sentiment, entailment, question answering, translation, reading comprehension, or specific reasoning formats. MMLU compressed many domains into a single visible table. That made it powerful. It also made it dangerous. Once a broad benchmark becomes a single score, readers can forget that the score is an average across many tasks, prompts, subject areas, and failure modes.

The seduction is obvious. A one-line number is easy to compare. It fits in a release table. It travels across social media. It can be plotted over time. It can be placed next to a competitor. A buyer can ask for it. A policymaker can cite it. A model card can include it. A technical report can use it to claim progress.

But the number is not the model. It is a measurement under a particular test setup.

The setup includes the dataset, the prompt format, the number of examples shown to the model, the scoring rule, the handling of invalid answers, and the time at which the test was still fresh. When readers ignore the setup, the benchmark becomes a symbol instead of an instrument.

The prompt format deserves special attention because language models do not simply "take a test" in the way a person does. A benchmark run may be zero-shot, few-shot, chain-of-thought prompted, instruction wrapped, or routed through a harness that normalizes answers. A multiple-choice benchmark may require the model to output a letter. A coding benchmark may require exact code. A preference benchmark may compare two long-form answers. Small changes in framing can move results, especially when the model is sensitive to examples or output format.

That does not make the result meaningless. It means the result is a system result. The measured artifact is not just the base model in the abstract. It is the model plus prompt, decoding settings, answer parser, evaluation script, and sometimes safety or tool layers. In older machine-learning settings, this was already true: preprocessing, validation splits, and metric definitions mattered. With chat models, the surface became more visible because the interface itself is language.

This is one reason benchmark tables became contested in public. Two groups could evaluate what looked like the same model and get different results because they used different prompts, different harness versions, different few-shot examples, or different model endpoints. A release table might be accurate under the provider's setup while still being hard for outsiders to reproduce exactly. Independent evaluation became valuable not because first-party results were automatically false, but because the full evaluation setup needed external pressure.

BIG-bench pushed in the opposite direction: if one score was too narrow, make the test world bigger.

In 2022, Beyond the Imitation Game, usually called BIG-bench, gathered 204 tasks from 450 authors across 132 institutions. That scale was itself a statement. Language models were no longer being evaluated by a small handful of canonical academic datasets. A large community was trying to probe many kinds of behavior: reasoning, math, linguistic skill, commonsense, bias, social reasoning, software development, science, and stranger tasks that did not fit neatly into older categories.

BIG-bench also made a quieter point about benchmark mortality. The authors discussed the restricted scope and short useful lifespans of benchmarks. A benchmark is most useful when it is hard enough to reveal differences and clean enough to trust. If models saturate it, or if the field trains too directly against it, the benchmark loses resolution. It can still have historical value, but it stops being a sharp instrument.

That short lifespan is one reason the benchmark war never ends. Every successful metric creates the conditions for its own erosion. If a benchmark becomes important, researchers and companies study it. They tune prompts for it. They report it. They build datasets around similar skills. They use it as a target. The more valuable the score becomes, the less innocent the score remains.

HELM tried to answer this by refusing the idea that a single accuracy number was enough.

Also in 2022, the Stanford Center for Research on Foundation Models introduced Holistic Evaluation of Language Models as a response to fragmented, incomplete, and accuracy-centered evaluation. HELM organized scenarios and metrics, evaluated prominent models across many scenarios, and emphasized that accuracy should not be the only dimension of judgment. Calibration, robustness, fairness, bias, toxicity, and efficiency were part of the frame.

This mattered because it treated evaluation as a multidimensional governance problem. A model can be accurate but poorly calibrated. It can perform well on average but fail under distribution shift. It can be strong on one demographic slice and harmful on another. It can be useful but expensive. It can be safe in one prompt format and brittle in another. If a field only rewards the headline score, it trains itself to ignore the rest.

HELM did not make evaluation simple. It made the opposite argument: responsible comparison is expensive because reality is multidimensional. That was an important counterweight to leaderboard culture. The problem was that the market still loved simple rankings. Users and buyers wanted to know what was best. Labs wanted a clean claim. Journalists wanted a headline. Open communities wanted proof that a smaller or cheaper model could compete. The richer the evaluation, the harder it was to compress into public reputation.

Then GPT-4 showed how benchmark tables could become launch evidence at frontier scale.

In March 2023, OpenAI's GPT-4 Technical Report presented a model that, in the company's framing, reached human-level performance on many professional and academic benchmarks. The report included exams, MMLU, coding benchmarks, contamination checks, safety evaluations, and comparisons to earlier systems. It reported, among other results, strong MMLU performance and a simulated bar exam result in the top decile.

Those claims should be read precisely. They are OpenAI's first-party technical-report claims, not neutral metaphysical proof that the system "understands" in the human sense. But their historical role is clear. The benchmark table became a central part of how a frontier model announced itself to the world.

This was a different kind of model launch than earlier academic release culture. A paper could still describe architecture, data, training, and limitations, but many readers went straight to the table. The table answered the public question: how good is it? It compared the new system to past systems and to human test performance. It made a diffuse capability claim look measurable.

The GPT-4 report also showed that evaluation had become operational infrastructure. OpenAI described Evals as a framework for creating and running benchmarks and tracking model performance, including deployed models. That sentence matters. Evaluation was no longer only a paper-time activity. It was becoming part of the lifecycle of model deployment.

Once models are deployed into products, evaluation cannot stop at release. A provider may change a model, add a safety layer, alter a system prompt, modify a tool interface, route queries differently, or introduce a cheaper variant. Users experience a service, not a static paper artifact. Evaluation tools become a way to track that service over time.

This also made benchmarks political. If a company can claim its model passes important tests, that affects trust. If a regulator asks for evidence of safety, evaluation becomes part of compliance. If an enterprise buyer compares vendors, benchmark tables become procurement language. If an open-weight model closes the gap on a widely cited benchmark, it can challenge the story that only closed frontier labs matter.

The same table can be science, sales, and governance.

It can also be a translation device between technical and nontechnical audiences. A model architecture diagram means little to a procurement officer. Training-token counts may not help a school administrator decide whether a system is reliable. But a table of exam performance, safety evaluations, coding results, and comparison benchmarks offers a familiar shape: tests passed, scores achieved, gaps closed. That familiarity is useful and risky at the same time. It allows broader participation in the conversation, but it can smuggle in the assumption that benchmark success is equivalent to readiness.

Professional exams are especially seductive in this way. A bar exam or medical exam has social meaning outside AI. If a model performs well on a simulated exam, the result travels farther than a technical metric because the audience already knows the exam is hard. But the analogy has limits. A human who passes an exam is embedded in training, accountability, professional norms, and a body that can act in the world. A model's exam score does not carry those institutions with it. The score shows something real about pattern use and knowledge access under a test condition; it does not license the model as a professional.

That distinction is easy to lose in a launch cycle. The stronger the table, the stronger the temptation to let the table stand in for the system. Careful reports add caveats, contamination checks, safety sections, and limitations. Public reception often compresses those details back into a headline.

That is why contamination became such a serious issue.

Modern models are trained on enormous mixtures of web text, books, code, papers, forums, documentation, and other data. Benchmarks are often public. Test questions may appear in papers, GitHub repositories, tutorials, copied datasets, blog posts, or discussion threads. If a model has seen the answers during training, a test result may look like reasoning while partly reflecting memorization or leakage.

This does not mean every strong result is fraudulent. It means the burden of evaluation changed. Large-scale pretraining made clean separation harder. Benchmark designers and model developers had to think not only about task difficulty but also about data provenance, time splits, repository overlap, and contamination checks.

The GPT-4 report included contamination checks and disclosed an issue with GSM-8K training-set inclusion. BIG-bench discussed leakage concerns, noting that direct leakage was impossible for the reported models because of timing, while indirect leakage could not be ruled out in the same simple way. SWE-bench would later design around repository overlap by separating training data repositories from evaluation repositories. These are not gossip points. They show that serious evaluation work had to treat leakage as a design problem.

Contamination is only one part of the Goodhart problem.

Goodhart's law is often summarized as: when a measure becomes a target, it ceases to be a good measure. David Manheim and Scott Garrabrant categorized variants of this failure: regressional, extremal, causal, and adversarial. The exact taxonomy is less important here than the basic institutional warning. If a score becomes valuable, actors optimize against it. That optimization can weaken the connection between the score and the underlying goal.

In AI evaluation, the underlying goal is rarely "perform well on this dataset." The real goal might be useful reasoning, reliable coding assistance, safe medical triage, honest uncertainty, good instruction following, or trustworthy operation inside a business process. The benchmark is a proxy. It can be a good proxy for a while. But once the proxy becomes the target, the system adapts.

That adaptation can be benign. Researchers build better models because benchmarks reveal weaknesses. A hard test encourages progress. A public leaderboard pushes teams to share results. A standardized harness reduces ambiguity. Without these pressures, the field would be worse.

But adaptation can also become benchmark-specific. Teams can tune prompts, choose favorable few-shot examples, filter data, train on benchmark-like tasks, select checkpoints, report only successful variants, or design systems around quirks of the scoring rule. Even without bad intent, the result can be overfitting to the public ritual of evaluation.

This is why the benchmark war is not merely about cheating. It is about incentives.

A company does not need to lie for benchmark culture to distort development. If customers, investors, media, and internal leadership all watch the same numbers, teams will naturally optimize for those numbers. The metric becomes part of the product environment. It changes what gets funded, celebrated, and shipped.

That pressure also affects open communities. An open-weight model may live or die by leaderboard position. A small model with impressive benchmark results can attract users, contributors, fine-tunes, and hosting support. A model with weaker public numbers may be ignored even if it is useful in specific domains. The same public comparison machinery that democratizes evaluation can also narrow attention.

Then came the arena.

In June 2023, MT-Bench and Chatbot Arena, introduced by Lianmin Zheng and collaborators, addressed a weakness of static benchmarks: many users cared less about multiple-choice test accuracy than about open-ended interaction. Could the model answer naturally? Follow an instruction over multiple turns? Write helpful code? Explain a concept? Refuse appropriately? Be concise without being useless? Handle ambiguity?

Static test items struggled to capture those preferences. Human evaluation was expensive. Pairwise comparison offered a different route. Show a user two anonymous model answers, ask which is better, aggregate many votes, and produce a public ranking. Chatbot Arena made model comparison feel like a courtroom where the crowd could judge.

The method was powerful because it matched the product experience. People do not use chatbots by reading benchmark tables. They ask questions and compare answers. A preference arena turned that behavior into data. It could update as new models appeared. It could include open and closed models. It could surface surprising strengths and weaknesses that static tests missed.

MT-Bench added another layer: LLM-as-judge. Instead of relying only on human raters, a strong model such as GPT-4 could evaluate answers at scale. The MT-Bench and Chatbot Arena paper reported that GPT-4 judge agreement with humans was over 80 percent, roughly comparable to human-human agreement in their setting. That made automated preference evaluation look plausible.

It also made evaluation stranger. A model could judge other models. In some cases, it might even judge versions of itself or systems built around similar training distributions. Evaluation became cheaper and more scalable, but also more dependent on the biases of the judge.

The authors documented those biases. Position bias matters: a judge may prefer the first or second answer. Verbosity bias matters: a longer answer may look more helpful even when it is padded. Self-enhancement bias matters: a model may favor outputs resembling its own style. Math and reasoning failures matter: a judge can be fluent and wrong when the question requires exactness.

These caveats did not make arenas useless. They made them institutions. An arena has rules, judges, incentives, blind spots, and legitimacy problems. Its leaderboard is not a timeless map of model quality. It is a dated public artifact produced by a particular evaluation process.

That process still had force. Public preference rankings shaped perception because they translated the messy experience of chatting with models into a visible order. A model could be "good" because users liked its answers. A model could be "frontier" because it performed well in anonymous pairwise comparisons. A smaller open model could win attention by appearing close to closed systems. A closed lab could use arena position as external validation.

The arena format also redistributed authority. Traditional benchmark creators decide the dataset and metric in advance. In a public preference arena, users partly decide what matters through their votes. If users prefer a warmer tone, that preference enters the ranking. If they reward detailed explanations, detail gains value. If they punish refusals, models that refuse less may look better. The benchmark does not merely reveal a neutral property called "quality." It aggregates a social preference under a particular interface.

That social character is not a defect to be eliminated. Chatbots are social products. User preference matters. A model that people find confusing, evasive, or brittle may be worse in practice than a model with a stronger static score. The danger is forgetting that public preference is not the same as truth, safety, or reliability. People may prefer confidence over accuracy, fluency over calibration, or agreement over correction. A good evaluation ecosystem needs both: controlled tests that expose exact failures and preference data that reflects real interaction.

The arena also changed what "capability" meant. It was no longer only a question of answering known test questions. It was style, helpfulness, refusal behavior, instruction following, conversational coherence, and user satisfaction. Some of those are real virtues. Some are easy to confuse with depth. A verbose but shallow answer can win. A cautious answer can look worse than a confident one. A model that flatters the user's premise can be preferred over one that corrects it.

The benchmark war therefore moved from the lab into the crowd.

The next turn was to make benchmarks harder and more work-like.

In October 2023, SWE-bench tried to evaluate software engineering through real GitHub issues and pull requests. The benchmark asked models to modify codebases and pass tests, using 2,294 problems from 12 Python repositories. The initial results were intentionally humbling. In the original setup, Claude 2 solved 1.96 percent of tasks.

That low number is historically useful. It shows a benchmark doing what a good benchmark should do at release: revealing a gap. If every strong model immediately saturates a benchmark, the benchmark may still be interesting, but it cannot guide progress for long. SWE-bench began as a hard test because it moved closer to real work.

A software issue is not just a prompt. It is a repository, a bug report, files, tests, dependencies, context, and an edit. The model has to understand not only language but also code structure, execution, and consequences. The evaluation can be partly automated because tests can pass or fail. That gives the benchmark a more grounded target than a preference score alone.

But SWE-bench also shows why harder evaluations are expensive. Work-like benchmarks require infrastructure. Repositories must be selected. Tasks must be filtered. Environments must run. Patches must be applied. Tests must execute. Contamination must be managed. The benchmark is no longer a spreadsheet of questions. It is a miniature production system.

That expense is the price of realism.

As models moved from chat demonstrations into agents, coding assistants, tool users, and enterprise workflows, static question answering could not carry the whole evaluation burden. Real work has state. It has side effects. It has hidden constraints. It has brittle environments. It requires planning, repair, and iteration. A model that answers a coding question correctly may still fail when asked to patch a repository.

SWE-bench therefore points forward without belonging entirely to agent history. Chapter 60 owns the agent turn: tools, retrieval, orchestration, and looped workflows. Ch66's concern is evaluation. SWE-bench matters here because it shows the benchmark arms race following capability into the workplace. When models become software actors, the tests must become closer to software work.

The same Goodhart cycle will follow. If SWE-bench becomes valuable, systems will adapt to it. They will improve repository navigation, patch generation, test selection, environment setup, and benchmark-specific workflows. That is not a scandal. It is progress and overfitting living next to each other. A benchmark can drive real improvements while gradually losing its ability to distinguish general capability from targeted adaptation.

This is the recurring pattern of evaluation in AI.

A field identifies a gap. It builds a benchmark. The benchmark creates discipline. Scores improve. Public attention gathers. The metric becomes a target. The community debates contamination, saturation, prompt sensitivity, and fairness. A new benchmark appears, harder or broader or more realistic. The cycle begins again.

The foundation-model era compressed that cycle because product competition moved faster than academic consensus. A benchmark could become famous in months. A leaderboard could shift weekly. A model card could cite scores that users discussed immediately. Open communities could fine-tune around public tests. Closed labs could publish selective tables. Evaluation did not have the slow rhythm of traditional scientific infrastructure. It had the tempo of product launches.

That speed made benchmark literacy essential.

A careful reader has to ask: Who created the benchmark? What does it measure? What does it leave out? When was the result produced? Was the model prompted in a comparable way? Was the test public before training? Is the score averaged across tasks that should not be averaged? Is the benchmark saturated? Does the metric reward verbosity, caution, speed, exactness, creativity, or something else? Is the score from a first-party report, an independent harness, a public arena, or a reproduction?

Those questions are not pedantry. They are the difference between evaluation and myth.

They also matter for governance. As AI systems entered schools, offices, hospitals, codebases, customer support channels, and government discussions, evaluation became a way to decide what was acceptable. A benchmark can shape whether a system is considered safe enough, useful enough, cheap enough, or advanced enough to deploy. A safety evaluation can become part of a release gate. A model comparison can influence procurement. A public leaderboard can affect market confidence. A regulatory debate can borrow the language of capability thresholds.

This does not mean benchmarks control society. It means they supply a vocabulary for decisions that would otherwise be even more opaque.

Safety evaluation sharpened that point. Once models could produce persuasive text, write code, plan steps, analyze images, and call tools, the question was not only which model was more capable. It was which capabilities should be released, limited, monitored, or delayed. Evaluation became part of the argument about deployment gates. A dangerous-capability test, a jailbreak rate, a refusal metric, or a red-team result could influence whether a model shipped broadly or with restrictions.

Those safety measurements are even harder to treat as simple scores. Refusal behavior can be too weak or too strong. A model that refuses many requests may look safer while being less useful. A model that answers broadly may be more helpful while creating more risk. Red-team prompts evolve as users discover new attack patterns. Policy categories change. Tool access changes the harm surface. The evaluation target moves because the product and the adversary both move.

That is why evaluation became governance infrastructure rather than mere reporting. A serious lab, platform, or buyer needs repeatable tests, version tracking, escalation rules, and a way to notice regressions. The benchmark table is the public artifact. The evaluation pipeline behind it is the operational control surface.

That vocabulary can empower outsiders. HELM-style transparency can expose differences that model providers might prefer to summarize. Public arenas can let users compare systems without waiting for official claims. Open evaluation harnesses can help researchers reproduce or challenge release narratives. SWE-bench-style tasks can show that a polished assistant still fails at real work.

But the same vocabulary can hide power. A company with the resources to run many evaluations can choose the most flattering table. A lab with access to private data can tune against public expectations. A leaderboard operator can define the rules of recognition. A procurement process can reduce complex risk to a score. A public debate can confuse exam performance with social readiness.

The benchmark war is therefore a fight over institutions, not just numbers.

It is also a fight over time. A benchmark result is dated. It belongs to a model version, a prompt method, an evaluation harness, a data cutoff, and a moment in a rapidly moving field. Treating a score as timeless is one of the easiest ways to misunderstand modern AI. A result that once demonstrated frontier performance may later become table stakes. A benchmark that once exposed weakness may later become saturated. A leaderboard position that looked decisive in one month may be irrelevant in the next.

This is why Ch66 sits between open weights and the next chapters on platforms, data, and the physical economy of frontier AI. Evaluation does not float above those fights. It connects them.

Open weights need benchmarks to prove they matter. Closed labs need benchmarks to justify premium access. Copyright disputes affect what data can be used and therefore what models can learn. Data exhaustion changes the value of synthetic data and harder evaluations. Inference economics determines whether a model that scores well can be served cheaply. Chip geopolitics shapes who can train and run the systems that compete on the scoreboard.

Benchmarks make capability visible, but visibility is never neutral.

The healthiest view is neither naive nor cynical. Benchmarks are indispensable. They are how a field disciplines claims, finds weaknesses, compares systems, and notices progress. Without them, the loudest demo wins. With them, at least some claims have to meet a common test.

But benchmarks are not reality. They are negotiated instruments inside an incentive system. They measure what their designers could formalize. They miss what was too expensive, ambiguous, political, or new to measure. They invite optimization. They decay. They create winners, and winners learn to speak their language.

The score is not the system.

The war over benchmarks is the war over who gets to say what the system is.
