---
revision_pending: false
title: "CNPE Full Mock Exam"
slug: k8s/cnpe/module-1.5-full-mock-exam
sidebar:
  order: 105
---

# CNPE Full Mock Exam

- **CNPE Track**: Complexity `[COMPLEX]`
- **Time to Complete**: 90-120 min
- **Prerequisites**: CNPE Exam Strategy and Environment, GitOps and Delivery Lab, Platform APIs and Self-Service Lab, Observability Security and Operations Lab

## Learning Outcomes

After this module, you will be able to:

- Diagnose GitOps delivery drift by comparing repository intent, controller status, and live Kubernetes 1.35+ objects.
- Evaluate platform API self-service claims by reading CRD contracts, status conditions, and reconciliation evidence.
- Debug observability or security failures without weakening policy guardrails or losing operational evidence.
- Design an exam pacing workflow that parks stuck work, verifies every task, and preserves final review time.
- Implement an examiner-style debrief that converts misses into concrete practice changes.

## Why This Module Matters

Hypothetical scenario: Your exam environment opens with three partially broken platform tasks, a ticking timer, and no friendly hint about which layer is wrong. One application is out of sync with its GitOps source, one self-service resource is stuck because its contract and claim disagree, and one workload looks like a security problem until the evidence points toward a rollout mistake. None of those tasks is individually mysterious, but the combined pressure makes ordinary habits visible in a way that a quiet lab never does.

A full mock exam is valuable because it tests the workflow between skills, not just the skills themselves. Reading another theory page can make you feel prepared while leaving your sequencing untested, your verification loop soft, and your scratchpad scattered across too many half-finished ideas. A rehearsal forces you to decide what to inspect first, when to stop digging, which layer owns the fix, and how much proof is enough before moving to the next task.

This module is meant to be used like a flight simulation, not consumed like a reference page. The earlier CNPE modules trained the individual instruments: GitOps delivery, platform APIs, observability, security, and operational follow-up. Here you practice taking off, handling turbulence, landing cleanly, and then reviewing the run like an examiner who cares about evidence more than confidence.

## Reading the Exam Like a Platform Operator

The first skill in a CNPE-style mock exam is not typing faster; it is reading the environment as a system with layers. A platform task may mention an application symptom, but the cause might live in repository intent, a controller condition, a CRD schema, a namespace policy, or a missing operational signal. If you begin by editing the first object that looks suspicious, you can accidentally make the system less explainable while still failing to address the task the examiner intended you to solve.

The most reliable starting move is to classify the work before you repair it. Delivery tasks ask whether desired state and live state converge. Platform API tasks ask whether a self-service contract is clear enough for a user and a controller to agree. Observability and security tasks ask whether you can prove a cause using evidence without weakening the guardrails that make the platform safe. Operations follow-up tasks ask whether the next operator will have enough signal to understand the fix after you leave.

Pause and predict: if an application is unhealthy after a Git commit, what evidence would tell you whether the problem is repository intent, controller reconciliation, or the live Kubernetes object? A useful answer names at least two sources of truth before it names a fix. In a GitOps system, the repository is the declared intent, the controller status tells you whether reconciliation is blocked, and the cluster objects show the current result. When those three disagree, the job is to identify the boundary where the disagreement starts.

Think of the exam as a set of inspection lanes in a workshop. You do not disassemble the engine because the dashboard light is on; you check the signal, confirm the system, and isolate the layer with the cheapest trustworthy evidence. In Kubernetes 1.35+ environments, that evidence often comes from resource status, events, controller conditions, and narrow command output. The platform operator habit is to move from broad signal to specific cause without turning the investigation into a scavenger hunt.

The original practice module summarized the sample exam flow in four tasks: GitOps delivery, platform API self-service, observability or security incident response, and operations follow-up. That sequence still works as the backbone of the mock exam, but the deeper lesson is that each task has a different success definition. A delivery fix is not complete because a manifest was edited; it is complete when the intended environment converges. A platform API fix is not complete because a claim was accepted; it is complete when the contract is valid, status is meaningful, and reconciliation reaches the expected state.

In a realistic rehearsal, the task text may deliberately include tempting details. A namespace name, a failed pod, or an angry event is useful evidence, but it is not automatically the root cause. Good exam work turns each clue into a question: which system produced this clue, what does that system own, and what would change if my hypothesis were true? That habit keeps you from confusing implementation noise with platform intent, especially when a task spans GitOps, APIs, and runtime behavior.

## Running the Mock Exam Under Real Pressure

The rules of the rehearsal are simple because the complexity should come from the work, not from ceremony. Set a timer and do not pause it. Keep a small scratchpad of task state. Verify every change before moving on. Do not optimize for perfect elegance when a smaller correct fix exists. If a task stalls, park it and return later with a fresh hypothesis. These rules preserve the original module's purpose: build pressure tolerance and sequencing skill rather than produce a polished design document.

Timer discipline matters because platform engineers often lose time in respectable ways. You can spend ten minutes making a solution prettier, five minutes collecting evidence you already have, and another stretch rereading documentation while easier points wait untouched. The mock exam exposes those habits because the clock keeps moving. A stable pacing workflow protects you from the false comfort of effort, which is when you are busy but not improving the score.

Use a scratchpad, but keep it intentionally plain. The scratchpad should record task status, current hypothesis, next check, and verification result. It should not become a second source of truth, a personal runbook, or a transcript of every command. The practical goal is to preserve context when you switch tasks, especially after you park a stuck issue and return later. If you cannot understand your own note in a few seconds, the note is too elaborate for exam conditions.

Exercise scenario: You have a 90-minute practice window and four tasks. The delivery task looks straightforward, the platform API task has unfamiliar CRD fields, the incident task produces noisy events, and the operations task asks for a runbook improvement. The strong move is usually to collect the delivery and operations points early, timebox the unfamiliar contract investigation, and leave final review time intact. The weak move is to treat the most confusing task as a personal challenge and let it absorb the whole session.

Before running this, what output do you expect from your final verification pass, and what would make you stop trusting that pass? Strong candidates answer in terms of signals, not vibes. They expect a clean Git state or intentional file diff, current events that no longer show the failing symptom, and workload state that matches the repaired namespace. They stop trusting the pass if the command checks the wrong namespace, if the resource name is stale, or if the verification proves only that a command ran.

The original module used a dress rehearsal analogy, and it is still a useful mental model. A real performance does not test whether you can memorize the score; it tests whether you can keep tempo, recover from mistakes, and finish strongly. CNPE works the same way. The best rehearsal outcome is not a perfect first run, but a repeatable read-act-verify loop that survives distraction and leaves behind enough evidence for an examiner to follow.

## Working Each Domain Without Losing the Thread

GitOps delivery tasks begin with intent. You inspect the repository change, identify the environment boundary, and compare that desired state with the controller's view and the live Kubernetes result. The highest-value question is not, "Which command fixes this?" but, "Which source of truth is wrong or blocked?" If the repository is wrong, repair the manifest or overlay. If the controller is blocked, inspect sync status, health, or diff behavior. If live state was manually changed, restore convergence rather than normalize drift.

Platform API self-service tasks begin with the contract. A claim, composite resource, CRD, or platform-specific abstraction is not just another YAML object; it is a promise between the platform team and its users. The learner has to read required fields, validation behavior, defaulting assumptions, status conditions, and controller ownership. When the contract is unclear, users guess. When status is vague, operators guess. The mock exam rewards the habit of making both sides observable.

Observability and security tasks begin with evidence. A failing request may show up as a pod restart, an authorization denial, a network symptom, or a missing trace, but each signal has a scope. Logs tell you what a process said. Events tell you what Kubernetes observed. Metrics tell you how behavior changed over time. Traces connect request paths. Policies explain what the platform rejected. A good answer combines signals until the cause is narrow enough to fix safely.

Operations follow-up tasks begin with the next person. After an incident or repair, the platform should be easier to operate than it was before. That may mean adding a missing alert, improving a runbook clue, clarifying a status message, or documenting the verification signal that proved the fix. The follow-up should not be theatrical. It should reduce ambiguity for the operator who sees the same class of symptom later and needs to know where to look first.

The sample exam flow from the original module remains a practical map. Task one is GitOps delivery: inspect repository intent, repair the environment-specific change, restore sync or correct rollout, and verify that live state matches desired state. Task two is platform API self-service: read the CRD or claim, identify contract fields, repair validation, status, or reconciliation issues, and confirm that the object reaches the expected healthy state. Task three is observability or security: narrow the cause with metrics, logs, traces, or events, apply the smallest safe fix, preserve guardrails, and verify that the symptom is gone. Task four is operations follow-up: confirm the right alert or runbook signal exists, document the operational clue, and keep the platform explainable.

The difference between a strong and weak run is often visible in the verbs. Strong runs inspect, compare, narrow, repair, verify, and record. Weak runs poke, hope, broaden, rewrite, and move on. That contrast is not about personality; it is about observability and control. Under pressure, precise verbs help you notice whether you are moving toward proof or merely creating more changes to reason about.

The original scoring rubric is worth keeping because it mirrors the platform layers you must integrate during the rehearsal.

| Area | Full Credit | Partial Credit |
|------|-------------|----------------|
| Delivery | Sync or rollout converges with correct environment boundaries | Change works but promotion or verification is weak |
| Platform API | Contract is understood and the resource reconciles | Resource is created but status or contract reasoning is unclear |
| Operations | Root cause is identified and fixed safely | Symptom is improved but evidence is incomplete |
| Security | Guardrails stay intact while the issue is fixed | Fix works but weakens controls unnecessarily |
| Time Management | Tasks are sequenced and stuck work is parked | One task absorbs too much of the session |

Use that rubric immediately after the run, not hours later when memory has softened the edges. The rubric is not a grade-school scorecard; it is a diagnostic instrument. If delivery converged but verification was weak, the next practice target is not more GitOps theory. It is building a stronger proof habit. If a platform object reconciled but the status reasoning was unclear, the next target is contract reading and condition interpretation. The point is to turn every miss into a specific practice change.

## Verification as the Exam's Control Loop

Verification is the exam's control loop because it turns action into evidence. Without verification, a task can feel finished simply because you edited the plausible file, restarted the plausible workload, or saw one command return a reassuring line. That is not enough in a platform exam. The examiner is not asking whether you performed activity; the examiner is asking whether the system reached the requested state for the right reason.

The smallest useful verification checks the layer you changed and the symptom the task described. If you changed GitOps intent, compare the repository change, controller status, and live object. If you changed a platform claim, inspect the claim, status conditions, composed resources, and any events that explain reconciliation. If you changed an operational signal, confirm that the runbook, alert, or query would guide a future operator. Verification should be boring, scoped, and repeatable.

Which approach would you choose here and why: a broad command that lists everything in the cluster, or a narrow command that proves the exact namespace and resource the task mentioned? Broad commands are useful for orientation, but they become expensive when repeated. Narrow commands are better for proof because they reduce noise and make it clear which object satisfies the task. A strong exam run usually starts broad enough to avoid tunnel vision, then narrows quickly and stays narrow until the fix is proven.

There is also a social dimension to verification, even in a solo exam. The command output is the explanation you leave for your future self during the final review pass. If your verification is only "it looks better," the final pass has nothing to audit. If your verification names the resource, namespace, condition, and expected transition, the final pass can quickly confirm that the work still holds. That distinction matters because late corrections are expensive and often happen under fatigue.

Keep the original module's simple verification block as the end-of-run baseline. It is deliberately small: check Git state, inspect recent events, and list the workload state in the relevant namespace. In a real mock exam you should add task-specific proof around it, but this baseline catches a surprising number of avoidable mistakes. It also reinforces the habit that verification belongs in the workflow, not as an optional ceremony after the timer has already expired.

## Debriefing Like an Examiner

The debrief is where a mock exam becomes training instead of merely a stressful hour. A poor debrief says, "I need to get faster," which is too vague to guide practice. A useful debrief names the task, the decision point, the evidence you missed, and the next behavior you will rehearse. The goal is to make the next run measurably different, not emotionally satisfying.

Start by reconstructing the timeline from your scratchpad. Which task did you open first, when did you switch, where did you park work, and how much time remained for review? Then examine the layer choices. Did you patch an implementation detail when the intent was wrong? Did you treat a policy denial as a workload failure? Did you keep digging after the evidence was already enough? These questions are uncomfortable in exactly the way good practice should be.

The original module's debrief questions still work because they force cause and consequence into the same conversation. Which task consumed the most time, and why? Did you move too early on any hard task? Where did verification save you from a bad assumption? Which platform layer was easiest to reason about under pressure? Answer each question with evidence from the run, not with a general feeling about your readiness.

An examiner-style debrief should produce a small set of concrete practice changes. For example, you might decide to rehearse CRD contract reading for twenty minutes before the next mock, write a tighter verification checklist for GitOps tasks, or practice parking an incident after a fixed timebox. Those are useful changes because they are observable. During the next run, you can tell whether you actually did them.

Be careful not to turn the debrief into self-punishment. The exam does not require a perfect operator; it requires a reliable one. Reliability grows when you can identify a weak signal, build a better habit, and test that habit in the next rehearsal. That is why this module asks you to implement a debrief, not just think about one. The debrief is part of the platform engineering workflow because platforms improve through feedback loops.

## Building a Repeatable Practice Set

A single mock exam can reveal weak habits, but repeatable practice turns those habits into measurable improvement. Build a small rotation of tasks instead of replaying the same exact scenario until memory replaces judgment. One week might emphasize delivery drift and platform API status conditions, while the next emphasizes security denials and operational follow-up. The goal is to keep the workflow stable while changing the symptoms enough that you still have to reason from evidence.

Good practice sets are deliberately mixed. If every task is a GitOps task, you will get faster at delivery while leaving platform contracts and incident evidence undertrained. If every task is a dramatic runtime failure, you will practice urgency while neglecting quiet operations work. A CNPE-style rehearsal should make you switch mental models: repository intent, API contract, controller reconciliation, runtime behavior, and human-operable documentation. Switching is part of the skill being examined.

When you assemble the practice set, write task prompts that describe outcomes rather than commands. "Restore the staging workload so GitOps and live state agree" is better than "change this field in this manifest" because it leaves room for diagnosis. "Make the database claim ready without bypassing the platform API" is better than "patch the claim" because it forces contract reasoning. Outcome-style prompts make the rehearsal feel closer to platform work, where the system rarely announces the correct command.

Vary the evidence available in each run. Sometimes provide clear controller status and noisy pod logs. Sometimes provide a helpful event and incomplete metrics. Sometimes make the runbook clue stale so the operations task tests whether the learner can improve it. This variation matters because exam readiness is not the ability to recognize one familiar failure. It is the ability to choose the next trustworthy signal when the surface symptom changes.

Keep practice data realistic but harmless. Use non-production namespaces, sample applications, and disposable claims. Avoid invented secrets, realistic tokens, or external systems that could make the rehearsal unsafe. The mock exam should create cognitive pressure, not operational risk. A learner should be able to reset the environment, rerun the task, and compare results without worrying that a practice mistake damaged shared infrastructure.

After each rehearsal, update the practice set with one small improvement. If the GitOps task was too obvious, add an environment boundary that must be checked. If the platform API task was too vague, improve the status condition so the learner can practice reading it. If the security task encouraged bypassing policy, rewrite the prompt so preserving guardrails is explicit. Practice material should evolve from evidence just like platform systems do.

There is a useful balance between novelty and repetition. Too much novelty turns every rehearsal into exploration, which hides whether core workflow habits are improving. Too much repetition turns the exam into recall, which hides whether the learner can transfer judgment to new symptoms. A practical rotation repeats the same domain mix while changing names, namespaces, failure surfaces, and verification signals. That keeps the pacing workflow familiar while the diagnosis remains real.

The best practice set also includes intentionally boring tasks. A small runbook correction, a missing alert label, or a straightforward GitOps overlay mismatch may not feel exciting, but those tasks test professional reliability. Platform engineering is full of small repairs that matter because they protect the next operator. If your mock exams contain only spectacular failures, you will undertrain the quiet work that often decides whether a platform stays understandable.

Before each new rehearsal, read the previous debrief and choose one behavior to test. Do not try to fix every habit at once. If the last run showed weak verification, make the next run about writing task-specific proof before moving on. If the last run showed poor parking discipline, make the next run about recording return conditions. Focused practice makes improvement visible, and visible improvement keeps the mock exam from becoming a vague endurance exercise.

Finally, keep the practice set connected to the Kubernetes and platform versions you expect to use. This module assumes Kubernetes 1.35+ behavior, modern controller status patterns, and cloud-native tooling where GitOps, custom resources, metrics, logs, traces, and policy signals are routine. Version awareness does not mean memorizing every release note. It means avoiding stale habits that no longer match the APIs, defaults, or operational signals learners will see in current environments.

## Scoring Strategy and Evidence Quality

The easiest way to improve a mock exam score is to separate task completion from task confidence. Completion means the requested outcome has been reached and verified. Confidence is the feeling that the answer is probably right. Under pressure, confidence often arrives before completion because a familiar command produced familiar output. Evidence quality keeps those two ideas separate by asking whether the proof directly matches the requested outcome, the layer you changed, and the symptom the task originally described.

High-quality evidence is specific enough that another operator could repeat the check. For a delivery task, "the app is fixed" is weak, while "the repository overlay now matches staging, the GitOps controller reports synced and healthy, and the Deployment in the namespace has the expected image" is strong. For a platform API task, "the claim works" is weak, while "the claim shows the ready condition, the composed resource exists, and no reconciliation errors remain in events" is strong. Specific proof reduces ambiguity during the final review pass.

Evidence also has to be proportional. You do not need a forensic report for a small manifest typo, but you do need enough signal to rule out the most likely wrong layer. A proportional check is narrow, relevant, and cheap to repeat. If the check requires several unrelated commands, the task may not be sufficiently isolated. If the check proves only that a pod exists, it may not prove delivery convergence, API readiness, or policy compliance. The art is choosing proof that is neither theatrical nor flimsy.

Score strategy begins with recognizing which tasks are point-rich and low-risk. A straightforward GitOps drift task with a clear overlay mismatch should usually be collected early because it can be verified quickly. A platform API task with unfamiliar schema may be valuable, but it deserves a timebox because contract reading can expand without warning. An operations follow-up task may look small, yet it often provides durable points because the expected result is a concise runbook or alerting improvement. Treat the exam as a portfolio of evidence, not a single heroic investigation.

The final review pass should be planned before the timer starts. If you decide at the end whether review matters, fatigue will argue for skipping it. Instead, assume the final review is part of the exam contract and protect it from the beginning. The review pass is where you catch namespace mistakes, uncommitted file changes, stale assumptions, and verification gaps. It is also where you decide whether a parked task is worth reopening or whether the better answer is to document the remaining hypothesis clearly.

When you grade yourself, be honest about partial credit. A fix that restores a workload but bypasses GitOps intent should not receive full delivery credit. A platform API object that exists but has unclear status reasoning should not receive full platform credit. A security repair that works by widening permissions should not receive full security credit. This honesty is not harsh; it is how the rehearsal remains useful. Inflated scores hide exactly the weaknesses the mock exam is supposed to reveal.

Evidence quality can improve even when the first run feels messy. After the debrief, pick one proof pattern and reuse it deliberately. For delivery, that might be intent, controller, live object. For platform API, that might be claim, contract, condition, composed resource. For incident work, that might be symptom, signal, smallest fix, symptom gone. Reusable proof patterns reduce cognitive load because you are not inventing a verification method from scratch while the timer is running.

The strongest candidates eventually make the mock exam feel calm because their workflow is boring in the right way. They still see unfamiliar symptoms, but they do not invent a new process for each one. They classify the layer, gather evidence, make the smallest safe change, verify the result, and leave a note that supports review. That repeatability is the real target of this module. Passing the mock exam is not about never being surprised; it is about having a workflow that remains useful when you are.

## Patterns & Anti-Patterns

The strongest pattern is the read-act-verify loop. Read the task and classify the layer, act with the smallest change that addresses the evidence, and verify both the changed layer and the original symptom. This pattern works because it keeps the loop tight enough to recover from mistakes. It scales to larger exams because each task leaves behind a short proof trail, so you do not need to rebuild context during the final review pass.

Another useful pattern is parking stuck work with a named return condition. Parking does not mean abandoning a task; it means recording the current hypothesis, the next check, and the reason you are stopping. This protects time management without losing the thread. It also prevents the common failure where a confusing platform API task consumes the whole rehearsal while easier delivery or operations points remain untouched.

A third pattern is layer ownership. Before changing anything, ask which layer owns the failing behavior: Git intent, controller reconciliation, platform API contract, policy guardrail, workload runtime, or operational signal. This pattern works because platform systems are built from contracts. If you repair the wrong layer, the symptom may briefly disappear while the underlying contract remains broken, which is exactly the sort of weak answer a full mock exam is designed to expose.

The original module identified several common failure patterns, and they remain useful because they describe habits rather than tool-specific mistakes.

| Failure Pattern | What It Looks Like | Better Habit |
|-----------------|--------------------|--------------|
| Starting with a complex incident | The first task consumes your attention | Collect quick wins first |
| Confusing intent and implementation | You patch the wrong layer | Identify the contract before editing |
| Verifying too late | The exam ends before you discover the mistake | Verify after each change |
| Over-logging | Notes become a second project | Keep the scratchpad minimal |
| Overcorrecting | You solve one issue by creating another | Make the smallest safe fix |

The anti-pattern behind all of those rows is treating motion as progress. Starting with the hardest incident can feel responsible because it tackles risk first, but the exam rewards finished, verified work across domains. Over-logging can feel disciplined, but it steals attention from the system. Overcorrecting can feel thorough, but it expands the blast radius. The better habit in each case is to keep the loop small enough that evidence can guide the next move.

## Decision Framework

Use the decision framework as a pacing guide during the mock exam. Start with the task text and identify the requested outcome, then classify the platform layer, choose the cheapest evidence, apply the smallest safe repair, verify the original symptom, and record the result. If the chosen evidence does not change your confidence, switch evidence rather than repeat the same command. If the repair would weaken guardrails or rewrite unrelated behavior, stop and revisit the layer classification.

The decision point that saves the most time is often "continue or park." Continue when you have a fresh hypothesis, a cheap next check, and enough remaining time that the task can still pay off. Park when you are repeating checks, broadening the scope without evidence, or about to make a risky change just to feel unblocked. A parked task should have a return condition such as "recheck controller condition after delivery task" or "inspect claim schema if final review leaves time."

| Decision | Choose This When | Tradeoff |
|----------|------------------|----------|
| Fix GitOps intent first | Repository desired state disagrees with the requested environment | Fast convergence if the controller is healthy, but weak if live drift is the real cause |
| Fix platform API contract first | Claim fields, validation, or status conditions explain the failure | Produces durable self-service behavior, but requires careful reading under time pressure |
| Fix runtime symptom first | Evidence proves the workload or namespace state is the immediate blocker | Can restore service quickly, but must not bypass GitOps or policy ownership |
| Park and return | You are repeating checks without new evidence | Protects score across domains, but requires a clear note so context is recoverable |
| Spend final review time | You have finished tasks with narrow verification evidence | Catches small mistakes, but only works if earlier notes are concise |

Treat this table as a set of guardrails rather than a script. Real platform work rarely follows a perfectly linear path, and exam tasks may deliberately mix symptoms from different layers. The value of the framework is that it keeps every choice attached to a reason. When you can explain why you continued, parked, or changed layers, your work becomes easier to grade and easier to improve.

## Did You Know?

- Kubernetes API extension through CustomResourceDefinitions became stable in the `apiextensions.k8s.io/v1` API, which is why modern platform API exams expect you to read schema and status as first-class operational evidence.
- Argo CD treats Git as the desired state source and continuously compares it with live cluster state, so a delivery task is incomplete until you can explain both sync and health signals.
- Prometheus graduated from the CNCF in 2018, and its query model is still central to cloud-native incident work because platform operators need time-series evidence rather than isolated snapshots.
- Kubernetes 1.35+ still rewards careful use of events, conditions, and controller status because those signals explain reconciliation decisions that raw pod listings often hide.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating the mock exam as another reading assignment | The learner expects the module to provide comfort instead of pressure | Run the rehearsal with a real timer, a short scratchpad, and no pauses |
| Editing live objects before checking GitOps intent | The visible symptom is in the cluster, so the repository feels indirect | Compare repository intent, controller status, and live objects before choosing the layer |
| Repairing a platform claim without reading the CRD contract | Self-service resources look like ordinary YAML under stress | Inspect required fields, defaults, status conditions, and reconciliation ownership before changing values |
| Weakening a policy to clear a security symptom | A denial can look like an obstacle rather than useful evidence | Preserve guardrails and identify the allowed change that satisfies the workload requirement |
| Letting one hard task consume the session | The learner wants closure and keeps chasing one more clue | Park the task with a named return condition and collect verified points elsewhere |
| Saving verification for the final minutes | Verification feels slower than making more changes | Verify after each task so the final review confirms work rather than discovering basic failures |
| Writing debrief notes that are too vague to practice | "Get faster" feels true but does not name a behavior | Convert each miss into a concrete next rehearsal target with an observable success signal |

## Quiz

### Question 1

Hypothetical scenario: A GitOps-managed application is unhealthy after a recent repository change. The task asks you to restore the environment without bypassing the delivery process. What is the best first move?

- A. Edit the live Deployment directly because the pod is the visible failure.

- B. Compare repository intent, controller status, and live Kubernetes objects to locate the drift boundary.

- C. Delete the namespace so the GitOps controller recreates everything from scratch.

- D. Disable automated sync until the exam ends so the workload stops changing.

<details>
<summary>Answer</summary>

B is correct because delivery drift must be diagnosed across intent, reconciliation, and live state before a safe fix is chosen. A is wrong because a direct live edit may fight GitOps and hide the real source of truth. C is wrong because deleting the namespace expands risk and may destroy unrelated state. D is wrong because disabling sync avoids the platform contract instead of restoring convergence.

</details>

### Question 2

Exercise scenario: A self-service database claim is accepted by the API server, but it never reaches a ready condition. Which investigation path best evaluates the platform API contract?

- A. Read the claim, the CRD schema, status conditions, events, and composed resources before editing fields.

- B. Replace the claim with a hand-written Secret because the application only needs credentials.

- C. Ignore status because successful object creation proves the claim is valid.

- D. Patch the controller deployment image tag before checking the resource contract.

<details>
<summary>Answer</summary>

A is correct because platform API work depends on the contract between user input, validation, reconciliation, and status evidence. B is wrong because bypassing the claim breaks the self-service model and may leave the controller unaware of the desired state. C is wrong because creation only proves admission, not successful reconciliation. D is wrong because changing the controller first skips the cheaper evidence available in the claim and CRD.

</details>

### Question 3

Hypothetical scenario: A workload is failing after a policy denial appears in events. The task says to restore service while keeping platform guardrails intact. What should you do?

- A. Remove the policy because service restoration is always more important than guardrails.

- B. Use events, workload configuration, and policy requirements to find the smallest compliant fix.

- C. Add broad privileges to the service account and move on.

- D. Ignore the denial and restart pods until one becomes ready.

<details>
<summary>Answer</summary>

B is correct because security failures must be debugged with evidence while preserving the policy boundary. A is wrong because removing the policy weakens the platform rather than satisfying the workload safely. C is wrong because broad privileges create an avoidable security regression and may not address the actual denial. D is wrong because restarts do not change the violated requirement and waste exam time.

</details>

### Question 4

Exercise scenario: You have spent several minutes on an unfamiliar CRD and are repeating the same inspection commands without new evidence. Two easier tasks remain untouched. What pacing decision best protects the overall mock exam score?

- A. Keep digging because abandoning a hard task always loses more points.

- B. Park the task with the current hypothesis, next check, and return condition, then collect verified points elsewhere.

- C. Delete the custom resource so the controller has a clean start.

- D. Stop taking notes because the scratchpad is slowing you down.

<details>
<summary>Answer</summary>

B is correct because an exam pacing workflow must protect time across domains while preserving enough context to return safely. A is wrong because effort on one task can starve easier verified work. C is wrong because deleting the resource is a risky action unrelated to the pacing problem. D is wrong because the scratchpad should be concise, not absent; it carries the hypothesis needed for a later return.

</details>

### Question 5

Hypothetical scenario: The final review pass finds that your delivery fix works, but your notes do not show how you verified the original symptom. What is the examiner-style improvement for the next rehearsal?

- A. Write a longer narrative about everything you tried so no detail is missing.

- B. Add a concrete verification line to each task that names the resource, namespace, condition, and expected result.

- C. Skip final review next time because it only creates anxiety.

- D. Focus only on command speed because documentation is not part of platform work.

<details>
<summary>Answer</summary>

B is correct because the debrief should convert a miss into an observable practice change. A is wrong because longer notes can become a second project without proving the symptom. C is wrong because final review is where small mistakes are caught before time expires. D is wrong because platform work includes evidence that another operator or examiner can follow.

</details>

### Question 6

Exercise scenario: A service has elevated latency, a recent rollout, and incomplete traces. Metrics show the latency began after a configuration change, while events show no policy denials. Which answer best reflects disciplined debugging?

- A. Start with the metric time window, rollout diff, and available logs, then decide whether trace gaps are causal or incidental.

- B. Assume tracing is broken and spend the session rebuilding observability.

- C. Disable the deployment strategy because rollouts are always the cause of latency.

- D. Treat missing policy denials as proof that the service is healthy.

<details>
<summary>Answer</summary>

A is correct because observability debugging should combine signals and let timing guide the next check. B is wrong because rebuilding observability is too broad unless evidence shows instrumentation is the blocking issue. C is wrong because the rollout is a hypothesis, not a conclusion. D is wrong because the absence of policy denials only narrows one class of cause; it does not prove healthy behavior.

</details>

### Question 7

Hypothetical scenario: Your operations follow-up task asks for a runbook improvement after you fixed a platform API reconciliation issue. Which update best supports the next operator?

- A. Add the exact status condition, likely cause, and verification signal that indicate the contract mismatch.

- B. Add a generic reminder to "check Kubernetes" because all failures eventually involve the cluster.

- C. Remove the runbook section so operators learn by investigating from scratch.

- D. Document only the final command you ran, without explaining the evidence it proved.

<details>
<summary>Answer</summary>

A is correct because operations follow-up should make future diagnosis faster and more reliable. B is wrong because generic advice does not identify the platform layer or signal. C is wrong because removing guidance throws away operational learning. D is wrong because a command without its evidence relationship is difficult to audit and easy to misuse.

</details>

## Hands-On Exercise

Exercise scenario: Run a full CNPE rehearsal using one delivery task, one platform API task, one observability or security task, and one operations follow-up from the CNPE track. Use a real timer, keep your notes short, and grade the run with the preserved rubric in this module. The point is not to invent a perfect exam; the point is to create a repeatable pressure test that exposes how you diagnose GitOps delivery drift, evaluate platform API claims, debug guarded runtime failures, manage pacing, and implement a debrief.

Task one is setup. Pick the four tasks, write a one-line expected outcome for each, and set a timer that you will not pause. Your setup is complete when you can point to the exact evidence that would prove each task finished. Do not start solving yet; the first practice move is to define success before pressure narrows your attention.

<details>
<summary>Suggested setup approach</summary>

Choose one task from each domain and write the success signal before touching the cluster or repository. For delivery, name the desired GitOps state and the live object that should converge. For platform API work, name the claim or CRD condition that should become healthy. For observability or security, name the symptom and the evidence that would show it disappeared. For operations follow-up, name the alert, runbook clue, or documentation change that would help the next operator.

</details>

Task two is execution. Solve the tasks in the order that gives you the most verified points fastest, not in the order that feels most interesting. When a task stalls, park it with a current hypothesis, next check, and return condition. Every time you make a change, verify the changed layer and the original symptom before moving to another task.

<details>
<summary>Suggested execution approach</summary>

Start with the task that has the clearest success signal and lowest blast radius. Use the read-act-verify loop for each change, and keep the scratchpad limited to status, hypothesis, next check, and verification result. If you notice repeated commands without new evidence, park the task and move to a different domain. The parked note should be short enough that you can resume it during final review without rereading the whole task.

</details>

Task three is review. Reserve the final minutes to audit the work instead of opening new investigations. Confirm that the repository, cluster, platform API objects, and operational notes tell the same story. If something is incomplete, prefer a clear note and a narrow correction over a broad risky change.

<details>
<summary>Suggested review approach</summary>

Review each task against the success signal you wrote at setup. For GitOps delivery, check intent, controller status, and live state. For the platform API task, check schema assumptions, status conditions, and reconciliation evidence. For observability or security, check that the original symptom is gone without weakening policy. For operations follow-up, check that the next operator would know what signal matters.

</details>

Task four is debrief. Grade yourself using the original rubric, then answer the debrief questions with evidence from your run. Convert at least two misses into concrete practice changes for the next rehearsal. A useful practice change describes the behavior, the context where you will use it, and the signal that proves you did it.

<details>
<summary>Suggested debrief approach</summary>

Avoid vague conclusions such as needing to be faster. Write observations like "I spent too long on the CRD without reading status conditions" or "I verified the pod but not the GitOps controller." Then define the next practice move, such as rehearsing claim-condition reading or adding a verification line before every task switch. The debrief is successful when the next mock exam has a behavior you can deliberately test.

</details>

**Success Criteria**:

- [ ] You diagnose GitOps delivery drift with repository intent, controller status, and live Kubernetes object evidence.
- [ ] You evaluate the platform API self-service claim by reading its contract, status conditions, and reconciliation signal.
- [ ] You debug the observability or security task without weakening policy guardrails or losing operational evidence.
- [ ] You manage exam pacing by parking stuck work with a return condition and preserving final review time.
- [ ] You implement an examiner-style debrief with at least two concrete practice changes.
- [ ] You can explain one decision you would change on the next run and the evidence that revealed it.

**Verification**:

```bash
git status --short
kubectl get events -A --sort-by=.lastTimestamp | tail -n 20
kubectl get all -n <namespace>
```

## Sources

- [Kubernetes overview](https://kubernetes.io/docs/concepts/overview/)
- [Kubernetes custom resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Kubernetes kubectl reference](https://kubernetes.io/docs/reference/kubectl/)
- [Kubernetes debugging running pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [Kubernetes logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes pod security standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes service accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [Argo CD sync options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/)
- [Argo CD diffing customization](https://argo-cd.readthedocs.io/en/stable/user-guide/diffing/)
- [Crossplane managed resources](https://docs.crossplane.io/latest/concepts/managed-resources/)
- [Prometheus querying basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [OpenTelemetry observability primer](https://opentelemetry.io/docs/concepts/observability-primer/)

## Next Module

Return to the [CNPE hub](/k8s/cnpe/) and run another full rehearsal with different tasks so the workflow becomes repeatable under pressure.
