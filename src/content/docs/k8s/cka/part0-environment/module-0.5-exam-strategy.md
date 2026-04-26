---
title: "Module 0.5: Exam Strategy - Three-Pass Method"
slug: k8s/cka/part0-environment/module-0.5-exam-strategy
sidebar:
  order: 5
lab:
  id: cka-0.5-exam-strategy
  url: https://killercoda.com/kubedojo/scenario/cka-0.5-exam-strategy
  duration: "15 min"
  difficulty: beginner
  environment: ubuntu
---

> **Complexity**: `[QUICK]` - Strategy, timing discipline, and exam execution habits
>
> **Time to Complete**: 20-30 minutes to learn, repeated practice to internalize
>
> **Prerequisites**: Modules 0.1-0.4, a working shell, and basic comfort running `kubectl` commands
>
> **Kubernetes Version Target**: 1.35+

---

## Learning Outcomes

After this module, you will be able to:

- **Apply** the Three-Pass Method to prioritize CKA tasks by score, complexity, and remaining time.
- **Triage** exam questions into quick, medium, and complex work before committing to a solution path.
- **Evaluate** point-per-minute tradeoffs when multiple unfinished questions compete for limited time.
- **Design** a repeatable question-start routine that protects against wrong-context and wrong-namespace mistakes.
- **Recover** from stuck troubleshooting tasks by preserving partial credit and moving to higher-confidence work.

---

## Why This Module Matters

A candidate sits down for the CKA with months of practice behind them. They can create Deployments, debug Services, explain kubelet behavior, and write NetworkPolicies from the official documentation. Ninety minutes later, they are still trapped in a low-value troubleshooting task while several straightforward questions remain untouched, and the problem is no longer Kubernetes knowledge. The problem is execution strategy under pressure.

The CKA is a performance exam, so every minute must produce visible cluster state that a grader can inspect. Knowing the correct command is only half the skill; choosing when to run that command is the other half. A candidate who solves questions in the order presented can accidentally let one ambiguous task consume the time needed for three predictable tasks. The exam rewards working systems, not heroic struggle.

The Three-Pass Method turns the exam from a linear obstacle course into a controlled triage exercise. First, secure tasks that are fast and familiar. Next, complete standard multi-step work that may require YAML or documentation. Finally, spend remaining time on troubleshooting and complex cluster work, where uncertainty is highest but partial progress still matters. This is the same pattern senior operators use during incidents: stabilize what can be stabilized quickly, investigate what is likely to pay off, and reserve deep diagnosis for the problems that remain.

---

## Part 1: The Real Problem Is Not the Clock

The clock is visible, but the hidden threat is decision fatigue. In a two-hour performance exam, you repeatedly decide which cluster context to use, whether a question is worth continuing, when to consult documentation, and whether a partial solution is enough. Each decision happens while a terminal is open and a timer is running. Strategy exists so those decisions are mostly pre-made before the stress starts.

A linear exam path looks fair because it feels disciplined. You read Question 1, solve Question 1, then move to Question 2. That works only when every question has similar difficulty and similar point value. CKA tasks are not like that. A simple label command, a moderate RBAC setup, and a broken control-plane component can sit next to each other, yet they do not deserve equal attention at the same moment.

```ascii
+----------------------+------------------------+-------------------------+
| Linear Exam Thinking | What Actually Happens  | Strategic Correction    |
+----------------------+------------------------+-------------------------+
| Start at Question 1  | Early hard task stalls | Scan all questions      |
| Finish before moving | One bug eats minutes   | Time-box aggressively   |
| Treat tasks equally  | Points are uneven      | Compare point return    |
| Perfect each answer  | Optional polish grows  | Meet requirements only  |
| Review at the end    | No time remains        | Verify during each task |
+----------------------+------------------------+-------------------------+
```

The Three-Pass Method is not about rushing. It is about protecting high-confidence points from low-confidence uncertainty. If a question asks you to create a namespace and a ConfigMap, that is a predictable task with a short feedback loop. If another question says a cluster network is broken, the first five minutes may only reveal the next diagnostic step. Both tasks matter, but the predictable task should usually be banked first.

> **Active learning prompt**: Imagine the first question is a node troubleshooting problem worth 6 points, and the second question is a Service creation task worth 5 points. Before reading further, decide which one you would attempt first and explain your reasoning in one sentence. The strongest answer considers uncertainty, not only point value.

The exam passing score is 66%, which means the winning strategy is not perfection. The winning strategy is enough correct work across enough questions. A candidate who completes every predictable task, earns partial credit on several hard tasks, and avoids wrong-context mistakes is in a far stronger position than a candidate who fully solves one impressive task while leaving routine work untouched.

---

## Part 2: Build a Triage Model Before You Need It

Triage begins by estimating three things: how long the task should take, how predictable the work is, and how easy it is to verify. A quick task is not merely short; it is short because the command shape is familiar and the expected output is obvious. A complex task is not merely long; it is long because diagnosis may branch into several possible causes. Medium tasks sit between those extremes, usually involving documented resource definitions and a few validation commands.

The labels `[QUICK]`, `[MEDIUM]`, and `[COMPLEX]` are not moral judgments about your skill. They are planning categories. A strong candidate may complete a NetworkPolicy in four minutes, while another candidate needs the documentation every time. Your personal triage model should reflect your own speed, but the exam strategy remains the same: do not let uncertain work block predictable work.

| Category | Typical Time | Common Signals | Verification Shape |
|----------|--------------|----------------|--------------------|
| `[QUICK]` | 1-3 minutes | Create, scale, label, annotate, expose a familiar object | One `kubectl get` or `kubectl describe` confirms the result |
| `[MEDIUM]` | 4-6 minutes | RBAC, PVC, NetworkPolicy, ConfigMap usage, simple scheduling rule | Manifest plus object inspection confirms the result |
| `[COMPLEX]` | 8-15 minutes | Troubleshoot, repair, debug, investigate, node or control-plane issue | Several diagnostic commands narrow the failure before a fix works |

A quick task usually has a direct imperative command. Examples include creating a Pod, scaling a Deployment, labeling an object, exposing a Deployment, or writing command output to a file. These tasks are high-value during Pass 1 because the feedback loop is short. You can complete the task, verify it, and leave it behind with confidence.

A medium task usually has multiple resources or a YAML shape that must be correct. RBAC requires the relationship between subject, Role, and RoleBinding to line up. A NetworkPolicy requires labels, selectors, policy type, and ports to agree. A PVC requires storage requests and access modes. These tasks are manageable, but they deserve a time box because a small YAML mistake can send you into slow debugging.

A complex task usually starts with symptoms rather than instructions. The question might say that Pods are stuck, a node is `NotReady`, DNS resolution is failing, or an application cannot reach a Service. You must gather evidence, form a hypothesis, test a fix, and verify the result. The uncertainty is why these tasks move to Pass 3 unless the point value and your confidence clearly justify earlier work.

```ascii
+-------------------+       +----------------------+       +--------------------+
| Read Question     | ----> | Estimate Work Type   | ----> | Choose Pass        |
+-------------------+       +----------------------+       +--------------------+
        |                              |                              |
        v                              v                              v
+-------------------+       +----------------------+       +--------------------+
| Context Required  |       | Predictable Command  |       | Pass 1: Quick      |
| Namespace Needed  |       | Documented Manifest  |       | Pass 2: Medium     |
| Output File Path  |       | Diagnostic Unknown   |       | Pass 3: Complex    |
+-------------------+       +----------------------+       +--------------------+
```

> **Pause and predict**: Categorize these before reading the answer: create a Secret and mount it into a Pod, fix a kubelet that will not start, and write all Pod names with label `tier=frontend` into a file. The Secret task is usually medium because it combines object creation with Pod configuration. The kubelet task is complex because the cause is unknown. The Pod-name output task is quick because it is a direct query and redirection.

A senior-level move is to update the category when new evidence appears. A task that looked quick can become medium if the namespace is missing, the target object has unexpected labels, or the requested output format is precise. That does not mean you misjudged badly. It means you noticed reality early enough to protect the rest of the exam.

---

## Part 3: Pass 1 Secures Predictable Points

Pass 1 starts with a full exam scan. You do not solve during the scan unless the interface design makes scanning impractical; the goal is to build a mental map. For each question, identify the context, namespace, resource type, point value if shown, and likely category. This scan is not wasted time. It prevents the worst failure mode: discovering easy questions only after hard questions consumed the clock.

A good Pass 1 question has a short command path and a simple verification path. The question might ask for a namespace, Pod, Deployment scale change, label, annotation, ConfigMap, Secret, or Service exposure. You should be able to complete most of these with imperative commands and only generate YAML when the requested fields require it.

```bash
# Run this once in your practice shell if the alias is not already configured.
alias k=kubectl

# Quick example: create a namespace, then verify it exists.
k create namespace production
k get namespace production
```

From this point forward, the module uses `k` as the standard alias for `kubectl`. The exam environment may already provide aliases, but you should be comfortable creating or using one without hesitation. The alias is not a trick; it simply reduces typing during repetitive work.

```bash
# Quick example: create a Pod in a specified namespace, then verify readiness.
k run web --image=nginx:1.25 -n production
k get pod web -n production
```

```bash
# Quick example: scale a Deployment and confirm the desired replica count.
k scale deployment api --replicas=3 -n production
k get deployment api -n production
```

```bash
# Quick example: expose a Deployment and inspect the Service object.
k expose deployment api --port=8080 --target-port=8080 -n production
k get service api -n production
```

The verification command is part of the answer, not an optional afterthought. If the grader expects a running Pod and your command created it in the wrong namespace, a fast `k get` catches the mistake while the question is still in your working memory. Verification also prevents over-review later, because you can trust the state you already checked.

| Pass 1 Habit | Why It Matters | Example Verification |
|--------------|----------------|----------------------|
| Switch context before every question | A correct solution in the wrong cluster earns no credit for the intended task | `k config current-context` |
| Confirm namespace before creating resources | Many exam tasks are namespace-scoped and silently differ by location | `k get ns target-ns` |
| Prefer imperative commands for simple objects | Imperative commands reduce YAML typing and syntax risk | `k get pod web -n production` |
| Verify immediately after each change | Immediate checks catch mistakes while they are still cheap | `k describe deployment api -n production` |

Pass 1 should feel almost mechanical. Read the task, switch context, run the direct command, verify, and move. If a supposedly quick task reaches the point where you are reading multiple documentation pages or debugging unexpected object state, it is no longer a Pass 1 task. Flag it mentally and continue.

---

## Part 4: Pass 2 Handles Standard Multi-Step Work

Pass 2 is where documented Kubernetes mechanics matter most. These tasks are not mysterious, but they contain enough fields that typing from memory can be risky. You may create a Role and RoleBinding, mount a Secret, write a PVC, apply a NetworkPolicy, configure a simple probe, or use a ConfigMap inside a Pod. The strategy is to use reliable patterns, verify relationships, and leave when the requirements are satisfied.

A strong Pass 2 workflow begins by generating or copying a small starting point. For example, RBAC is easier when you create the ServiceAccount, Role, and RoleBinding with commands instead of hand-writing every field. NetworkPolicy and PVC resources are often easier from a compact manifest because their nested fields are precise. Choose the path that reduces error for the specific object.

```bash
# Worked example setup: create a namespace and a service account for an RBAC task.
k create namespace secure
k create serviceaccount app-sa -n secure
```

```bash
# Worked example: create a Role and bind it to the ServiceAccount.
k create role pod-reader --verb=get,list,watch --resource=pods -n secure
k create rolebinding app-sa-pod-reader --role=pod-reader --serviceaccount=secure:app-sa -n secure
```

```bash
# Worked example verification: prove the binding grants the intended access.
k auth can-i list pods --as=system:serviceaccount:secure:app-sa -n secure
k get role,rolebinding,serviceaccount -n secure
```

This is a worked example because it demonstrates the full cycle: create the objects, connect the subject to the permission, and verify the authorization result. In the exam, you should not stop after applying YAML merely because the API accepted it. An accepted manifest can still bind the wrong subject, use the wrong namespace, or grant the wrong verb.

NetworkPolicy is a classic Pass 2 topic because the fields are easy to mix up. The policy selects the destination Pods with `spec.podSelector`, then defines which source Pods may connect under `ingress.from`. If you reverse those selectors, the YAML still applies, but the behavior is wrong. This is why Pass 2 requires careful reading rather than blind speed.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: web
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

```bash
# Apply and inspect the NetworkPolicy after saving it as netpol.yaml.
k create namespace web
k apply -f netpol.yaml
k describe networkpolicy allow-frontend-to-backend -n web
```

> **Active learning prompt**: Before applying the NetworkPolicy above, identify which Pods are being protected and which Pods are allowed to initiate traffic. If your answer mentions only one side of the traffic relationship, reread the `podSelector` and `ingress.from` blocks until both sides are clear.

A Pass 2 time box is usually stricter than learners expect. If you are five or six minutes into an RBAC task and still arguing with YAML indentation, you should ask whether the same points could be earned elsewhere first. The goal is not to abandon every imperfect task. The goal is to stop medium tasks from quietly becoming complex tasks without an explicit decision.

---

## Part 5: Pass 3 Converts Uncertainty Into Partial Credit

Pass 3 is where troubleshooting belongs. By this point, quick and medium tasks should already be banked, so the remaining time can be spent on problems with uncertain diagnosis. This changes the psychology of troubleshooting. You are no longer worried that every minute spent on a broken node is stealing time from a simple scaling task, because the simple work is already done.

Good troubleshooting follows a loop: observe, hypothesize, change one thing, verify, and repeat. The loop matters because random fixes create new symptoms and waste time. A candidate who immediately edits a Deployment without checking events may miss an image pull error, a missing Secret, or a failed scheduling constraint. Evidence is faster than guessing when the problem space is broad.

```ascii
+-------------------+      +-------------------+      +-------------------+
| Observe Symptoms  | ---> | Form Hypothesis   | ---> | Make Small Change |
+-------------------+      +-------------------+      +-------------------+
         ^                                                   |
         |                                                   v
+-------------------+      +-------------------+      +-------------------+
| Decide Next Step  | <--- | Verify Result     | <--- | Inspect New State |
+-------------------+      +-------------------+      +-------------------+
```

Consider a Deployment whose Pods are in `ImagePullBackOff`. A novice might delete Pods repeatedly, hoping the state changes. A practiced candidate checks the Pod events, identifies the failing image, updates the Deployment image, and verifies the rollout. The difference is not memorizing every failure mode. The difference is having a repeatable diagnostic loop.

```bash
# Worked troubleshooting example: inspect the Deployment, Pod state, and recent events.
k get deployment critical-app -n production
k get pods -l app=critical-app -n production
k describe pod -l app=critical-app -n production
k get events -n production --sort-by='.lastTimestamp'
```

```bash
# If events show a bad image reference, update the image and watch the rollout.
k set image deployment/critical-app critical-app=nginx:1.25 -n production
k rollout status deployment/critical-app -n production
k get pods -l app=critical-app -n production
```

Partial credit is not a license to be sloppy; it is a reason to make visible progress. If a question asks you to fix a broken workload and add resource limits, fixing the bad image but missing the limits may still be worth something. If you spend all remaining time trying to craft perfect resource limits while the Pod never starts, the visible state may be less valuable. The exam rewards cluster state, so make the most important state true first.

A senior operator also knows when to stop diagnosing. If a node issue could be caused by kubelet configuration, container runtime state, disk pressure, or networking, you cannot explore every branch equally with six minutes left. Pick the most likely branch based on the evidence, make one reversible fix if appropriate, verify, and then move if higher-confidence points remain elsewhere.

---

## Part 6: Context, Namespace, And Output Files Are Part Of The Strategy

Wrong-context work is especially painful because it can look perfect in your terminal. You create the right object, verify it successfully, and move on, yet the grader checks another cluster context and awards nothing for that question. This is why context switching must be part of the first action for every question, not a cleanup step at the end.

The safest question-start routine is short and repeatable. Read the required context. Switch context. Confirm the current context. Identify the namespace. Confirm or create the namespace only if the task requires creation. Then solve the actual problem. This routine may feel slow during practice, but it costs seconds and protects entire questions.

```bash
# Question-start routine: replace the context and namespace with the values from the task.
k config use-context exam-cluster-a
k config current-context
k get namespace production
```

```ascii
+------------------------+
| Every Question Starts  |
+------------------------+
| 1. Read context        |
| 2. Switch context      |
| 3. Confirm context     |
| 4. Check namespace     |
| 5. Solve requirement   |
| 6. Verify result       |
+------------------------+
```

Namespaces deserve the same discipline. Many Kubernetes objects are namespace-scoped, and the default namespace is rarely a safe assumption in the exam. A Pod named `web` in `default` does not satisfy a task that asked for `web` in `production`. If you create an object in the wrong namespace, recreate it correctly and delete the wrong one only if cleanup will not consume valuable time or remove evidence needed for another question.

Output-file questions look easy, but they are easy to lose through small mistakes. If the task asks for a file path, create exactly that file path. If the task asks for names only, avoid headers. If the task asks for sorted output, sort it. These questions are often quick wins because verification is simple: print the file and confirm the content matches the requested shape.

```bash
# Example: output Pod names with a label selector to an exact file path.
k get pods -l tier=frontend -o custom-columns=NAME:.metadata.name --no-headers > /tmp/frontend-pods.txt
cat /tmp/frontend-pods.txt
```

The best exam routine is boring because it removes improvisation. You do not need a new plan for every question start. You need the same small ritual repeated until it becomes automatic: context, namespace, solve, verify. That habit is not only for exams; it is the same habit that prevents production changes from landing in the wrong cluster.

---

## Part 7: Point-Per-Minute Thinking

Point value matters, but raw point value is not enough. A 10-point task that might take the rest of the exam can be worse than two smaller tasks that are nearly certain. The useful question is not "Which task is worth the most?" The useful question is "Which task is likely to produce the most verified credit per minute from here?"

| Situation | Weak Decision | Stronger Decision |
|-----------|---------------|-------------------|
| One complex task and two medium tasks remain | Start the complex task because it has the highest point value | Bank the medium tasks first if their combined value and certainty are higher |
| A quick task becomes unexpectedly confusing | Keep forcing it because quick tasks should be easy | Reclassify it, flag it, and return after predictable work is complete |
| Ten minutes remain and one hard task is half-solved | Chase an uncertain complete fix until time expires | Preserve current progress, then secure any small unfinished task |
| A completed answer probably works | Rebuild it for elegance | Verify the requirement and move on |

Point-per-minute thinking also helps when you are emotionally attached to a task. The hardest task can feel like a personal challenge, especially when you are close to solving it. The exam does not care whether a task is interesting. It cares whether enough required state exists across the cluster. If another question can produce certain points faster, your strategy should beat your curiosity.

A practical rule is to set a decision checkpoint before starting medium or complex work. For a medium task, ask after about five minutes whether the remaining work is obvious. For a complex task, ask after each diagnostic loop whether the next step is evidence-driven or guess-driven. If the next step is mostly guessing and other questions remain, move on.

```ascii
+------------------+----------------------+-----------------------------+
| Time Remaining   | Best Use             | Usually Avoid               |
+------------------+----------------------+-----------------------------+
| 90+ minutes      | Finish quick tasks   | Deep troubleshooting first   |
| 45-90 minutes    | Medium tasks         | Optional polish             |
| 15-45 minutes    | Complex or leftovers | Starting vague rabbit holes  |
| 0-15 minutes     | Verify and quick fix | New multi-branch diagnosis   |
+------------------+----------------------+-----------------------------+
```

> **Stop and decide**: You have 18 minutes left, one 9-point troubleshooting task untouched, one 5-point PVC task untouched, and one 4-point output-file task untouched. Write your order before reading the answer. A strong order is output file, PVC, then troubleshooting, because the first two tasks are highly verifiable and together match the point value of the uncertain task.

The Three-Pass Method does not remove judgment. It gives judgment a structure. You can still choose a high-value complex task earlier if you are unusually confident and the remaining tasks are low value. The important point is that the choice should be deliberate, not a side effect of question order.

---

## Part 8: Good Enough Means Requirement-Complete

"Good enough" does not mean careless. It means the solution satisfies the stated requirements and has been verified. In production engineering, you may add labels, comments, resource defaults, dashboards, and policy checks because long-term maintainability matters. In the exam, adding unstated improvements can consume time and sometimes introduce errors. Requirement-complete is the target.

A common perfectionist trap is overbuilding manifests. If the task asks for a Deployment with three replicas and a specific image, you do not need to add probes, resource limits, affinity, annotations, and comments unless the task asks for them. Optional best practices are valuable in real systems, but exam answers are graded against requested state. Extra fields do not compensate for missing required fields.

```bash
# Requirement-complete answer: create a Deployment with three replicas using the requested image.
k create deployment web --image=nginx:1.25
k scale deployment web --replicas=3
k rollout status deployment/web
```

```bash
# Verification focuses on the stated requirement, not on cosmetic YAML quality.
k get deployment web -o jsonpath='{.spec.replicas}{"\n"}'
k get deployment web -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

Good enough also means accepting partial credit when full completion is no longer realistic. If a multi-part question asks for a ServiceAccount, Role, RoleBinding, and Pod using that ServiceAccount, create and verify as many pieces as possible in the correct namespace. Leaving a partially correct object graph is usually better than deleting everything because the final Pod did not start.

This mindset translates directly to senior incident response. During an outage, stabilizing traffic may matter more than finding the deepest root cause in the first ten minutes. After the system is stable, the team can investigate the underlying defect. The exam compresses that pattern into a timed lab: secure what works, reduce uncertainty, and spend remaining time where it can still change the score.

---

## Part 9: A Complete Worked Mini-Triage

Now combine the strategy into a miniature exam plan. Suppose you have four questions and 20 minutes. The tasks are: create a Pod, create a PVC, create a NetworkPolicy, and fix a Deployment whose Pods will not start. A linear candidate starts at Question 1 and may still do well if the order is friendly. A strategic candidate scans all four, categorizes them, and deliberately chooses the fastest path to verified state.

```ascii
+------------+----------------------------------------------+------------+----------------+
| Question   | Requirement                                  | Category   | Planned Pass   |
+------------+----------------------------------------------+------------+----------------+
| Q1         | Create Pod q1-pod running nginx               | QUICK      | Pass 1         |
| Q2         | Create NetworkPolicy for backend traffic      | MEDIUM     | Pass 2         |
| Q3         | Create PVC requesting 5Gi ReadWriteOnce       | MEDIUM     | Pass 2         |
| Q4         | Debug broken Deployment q4-broken             | COMPLEX    | Pass 3         |
+------------+----------------------------------------------+------------+----------------+
```

Pass 1 handles Q1 because it is a direct command. The verification is simple, and there is no reason to postpone it. Notice that the point value might not be the highest, but the confidence and speed are excellent. A verified quick answer also warms up the terminal and reduces early anxiety.

```bash
k run q1-pod --image=nginx:1.25
k get pod q1-pod
```

Pass 2 handles Q3 and Q2. The PVC is shorter than the NetworkPolicy, so many candidates should do the PVC first. The NetworkPolicy follows once the namespace and selectors are clear. This order protects the easier medium task before the more selector-heavy one.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: q3-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

```bash
k apply -f q3-pvc.yaml
k get pvc q3-pvc
```

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: q2-netpol
  namespace: web
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

```bash
k create namespace web
k apply -f q2-netpol.yaml
k describe networkpolicy q2-netpol -n web
```

Pass 3 handles Q4. The diagnostic path begins with object state and events, not guesses. If the Deployment uses a bad image, the fix is direct. If the failure is something else, the same observation loop still gives you the next evidence-driven step.

```bash
k get deployment q4-broken
k get pods -l app=q4-broken
k describe pod -l app=q4-broken
k get events --sort-by='.lastTimestamp'
```

```bash
k set image deployment/q4-broken nginx=nginx:1.25
k rollout status deployment/q4-broken
k get pods -l app=q4-broken
```

This worked mini-triage demonstrates constructive alignment across the module. The learning outcome is to apply triage, the teaching activity shows categorization and ordering, and the assessment later asks you to make the same kind of decision under different constraints. That is the pattern you should use in your own practice: strategy first, commands second, verification always.

---

## Part 10: Exam-Day Routine And Practice Rhythm

Your exam-day routine should be simple enough to follow while nervous. Before the exam starts, prepare your physical environment, confirm identity requirements, and settle your workspace. When the exam begins, spend the opening minutes scanning tasks and identifying categories. After that, work the passes with discipline. During the final minutes, stop starting broad investigations and focus on verification, small fixes, and visible partial credit.

A useful rhythm is scan, pass, checkpoint, pass, checkpoint, finish. The checkpoints prevent drift. If you expected Pass 1 to take about 25 minutes and it has taken much longer, you need to skip more aggressively. If Pass 2 is turning into a series of debugging sessions, you need to move unfinished items to Pass 3. The plan is only useful if it changes your behavior when the clock disagrees with your expectations.

| Time Elapsed | Expected State | Decision If Behind |
|--------------|----------------|--------------------|
| 5 minutes | Questions scanned and rough categories identified | Stop solving during scan and finish the map quickly |
| 25-30 minutes | Most quick wins completed and verified | Lower the threshold for skipping anything uncertain |
| 75-85 minutes | Many medium tasks completed or partially completed | Move unresolved YAML-heavy tasks to the end |
| 105-115 minutes | Complex tasks underway and partial credit preserved | Stop broad diagnosis and look for small verified wins |
| Final minutes | Critical answers checked and files verified | Do not start a new multi-branch troubleshooting task |

Practice should mirror this rhythm rather than only drilling isolated commands. Command fluency matters, but strategy is learned through timed decisions. Use small mock exams where some tasks are intentionally easy, some are YAML-heavy, and some are broken. The point is to practice leaving a task before you are emotionally ready to leave it.

The final habit is post-practice review. After a timed drill, write down which tasks you miscategorized, where you lost time, and which verification steps caught mistakes. This converts practice from repetition into calibration. Over time, your personal categories become more accurate, and the Three-Pass Method feels less like a rule and more like professional judgment.

---

## Did You Know?

- **The CKA is performance-based**: You are graded on the state you create in live Kubernetes environments, so verified cluster state matters more than explanations in your notes.
- **A 66% passing score changes the strategy**: You do not need perfect coverage; you need enough correct and partially correct work across the exam.
- **Troubleshooting carries high weight**: The CKA emphasizes diagnostic skill, which is why complex tasks deserve focused time after predictable work is protected.
- **The exam environment can change over time**: Always verify current allowed resources, Kubernetes version, and exam rules before your scheduled attempt.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Move |
|---------|--------------|-------------|
| Starting immediately on the first question | The first question may be slow, ambiguous, or lower value than later tasks | Scan all questions first and build a pass order |
| Treating every task as equal | A two-minute task and a fifteen-minute task can compete for the same clock | Compare predictability, point value, and verification cost |
| Forgetting to switch context | Correct work in the wrong cluster does not satisfy the intended question | Make context switching the first action of every question |
| Ignoring namespaces | Namespace-scoped objects can be correct in one namespace and invisible to the grader in another | Read the namespace from the task and verify with `k get` |
| Overbuilding manifests | Extra best-practice fields consume time and can introduce mistakes | Implement only the requested state, then verify it |
| Staying stuck without a checkpoint | One uncertain task can quietly consume time needed for several predictable tasks | Reclassify stuck work and return after higher-confidence tasks |
| Skipping verification | Small mistakes survive until scoring if you never inspect the result | Verify immediately with the simplest command that proves the requirement |
| Leaving partial work invisible | A half-solved task may earn less if the useful state was never created | Apply working pieces as you go and preserve visible progress |

---

## Quiz

1. **You begin the exam and Question 1 asks you to troubleshoot a node that is `NotReady`, while Question 2 asks you to create a namespace and ConfigMap worth slightly fewer points. What should you do first, and why?**

   <details>
   <summary>Answer</summary>

   Scan the remaining questions first, then handle the namespace and ConfigMap during Pass 1 if they are as straightforward as they appear. The `NotReady` node may require several diagnostic branches, while the namespace and ConfigMap are predictable and easy to verify. The point difference does not justify letting an uncertain task block a fast completed answer.

   </details>

2. **You are six minutes into a NetworkPolicy question and the YAML applies, but traffic still does not behave as expected. You have several untouched medium tasks. How should you decide whether to continue?**

   <details>
   <summary>Answer</summary>

   Check whether your next step is evidence-driven and likely to finish quickly. If you can inspect labels and immediately see a selector mismatch, fix it and verify. If you are guessing at policy behavior without clear evidence, mark the task for Pass 3 and move to other medium tasks. A medium task has effectively become complex once it starts consuming troubleshooting time.

   </details>

3. **You completed an RBAC task, but your verification command shows the ServiceAccount cannot list Pods. The Role exists, and the RoleBinding exists. What should you inspect before rewriting everything?**

   <details>
   <summary>Answer</summary>

   Inspect the RoleBinding subject, namespace, and role reference. The common failure is binding the wrong ServiceAccount namespace, using the wrong Role name, or creating the binding in a different namespace from the Role. Rewriting everything wastes time; targeted inspection follows the diagnostic loop and preserves work that is already correct.

   </details>

4. **You have 14 minutes left. One untouched question asks for an etcd-style recovery procedure worth high points, and another asks for command output to a specified file plus a simple Deployment scale change. What is the stronger order?**

   <details>
   <summary>Answer</summary>

   Complete the output-file and scale-change tasks first, then spend remaining time on the recovery task. The smaller tasks have short verification paths and high certainty. The recovery task may be valuable, but it is multi-step and carries higher risk. The point-per-minute and risk-adjusted return favors banking the predictable work before the final complex attempt.

   </details>

5. **You realize that you solved a Service question in the wrong context. The YAML file is still available in your shell history and five minutes remain. What should you do?**

   <details>
   <summary>Answer</summary>

   Switch to the required context immediately, confirm it, and reapply or rerun the required commands in the correct cluster. Verify the Service in the correct namespace. If time remains and cleanup is safe, remove the accidental object from the wrong context, but the priority is creating verified state where the grader expects it.

   </details>

6. **A task asks for a Deployment with three replicas and a specific image. You are tempted to add probes and resource limits because they are best practice. How should exam strategy guide your choice?**

   <details>
   <summary>Answer</summary>

   Create the requested Deployment with the specified image and replica count, verify those requirements, and move on unless probes or resource limits were explicitly requested. In the exam, optional polish can consume time and introduce errors without improving the score. Good enough means requirement-complete and verified, not minimal in a careless sense.

   </details>

7. **During Pass 3, a broken workload question asks you to fix both an image error and missing resource limits. You have three minutes left and events clearly show the image is invalid. What is the best partial-credit move?**

   <details>
   <summary>Answer</summary>

   Fix the invalid image first, verify that Pods start or the rollout progresses, and then add resource limits only if time remains. A running workload is a major visible improvement, while resource limits on a still-broken Deployment may not satisfy the core troubleshooting requirement. The best partial-credit move creates the most important correct state quickly.

   </details>

---

## Hands-On Exercise

**Task**: Practice the Three-Pass Method against a small timed exam, then review your triage decisions. This exercise is designed to train prioritization, not only command syntax, so keep a timer visible and write down when you decide to skip.

### Setup

Create a practice namespace and a deliberately broken Deployment. These commands are safe in a disposable local cluster. If you are using a shared cluster, choose a unique namespace name and clean it up when finished.

```bash
k create namespace exam-strategy-practice
k create deployment q4-broken --image=nginx:doesnotexist -n exam-strategy-practice
```

### Mock Exam Questions

1. Create a Pod named `q1-pod` running `nginx:1.25` in namespace `exam-strategy-practice`.
2. Create a ConfigMap named `q2-config` with key `LOG_LEVEL=debug` in namespace `exam-strategy-practice`.
3. Create a PVC named `q3-pvc` requesting `5Gi` with `ReadWriteOnce` access mode in namespace `exam-strategy-practice`.
4. Troubleshoot the Deployment `q4-broken` in namespace `exam-strategy-practice` so its Pods can start.
5. Write the names of all Pods in namespace `exam-strategy-practice` to `/tmp/exam-strategy-pods.txt` with no header line.
6. Create a Role named `pod-reader` that can `get`, `list`, and `watch` Pods, then bind it to a ServiceAccount named `app-sa` in namespace `exam-strategy-practice`.

### Step 1: Scan And Categorize

Before running any solution command, scan all six tasks and write each one as `[QUICK]`, `[MEDIUM]`, or `[COMPLEX]`. Your categorization should reflect your current skill, not someone else's. If RBAC is automatic for you, it may be medium; if you always need documentation, still treat it as medium but give it a stricter checkpoint.

- [ ] I scanned all questions before solving.
- [ ] I identified the namespace for every task.
- [ ] I chose a Pass 1, Pass 2, and Pass 3 order before typing solution commands.
- [ ] I wrote down at least one task I would skip if it exceeded its time box.

### Step 2: Pass 1 Quick Wins

Complete only the quick tasks first. For many learners, Q1, Q2, and Q5 are quick. Do not start the broken Deployment yet, even if it looks tempting, because the purpose is to protect predictable points.

```bash
k run q1-pod --image=nginx:1.25 -n exam-strategy-practice
k create configmap q2-config --from-literal=LOG_LEVEL=debug -n exam-strategy-practice
k get pods -n exam-strategy-practice -o custom-columns=NAME:.metadata.name --no-headers > /tmp/exam-strategy-pods.txt
```

```bash
k get pod q1-pod -n exam-strategy-practice
k get configmap q2-config -n exam-strategy-practice
cat /tmp/exam-strategy-pods.txt
```

- [ ] I completed the quick tasks before starting troubleshooting.
- [ ] I verified each quick task immediately after creating the required state.
- [ ] I did not add optional fields or spend time polishing completed answers.

### Step 3: Pass 2 Medium Tasks

Complete the PVC and RBAC tasks next. Use YAML for the PVC because the object shape is compact and precise. Use imperative commands for RBAC because they reduce typing and make the subject relationship explicit.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: q3-pvc
  namespace: exam-strategy-practice
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

```bash
k apply -f q3-pvc.yaml
k create serviceaccount app-sa -n exam-strategy-practice
k create role pod-reader --verb=get,list,watch --resource=pods -n exam-strategy-practice
k create rolebinding app-sa-pod-reader --role=pod-reader --serviceaccount=exam-strategy-practice:app-sa -n exam-strategy-practice
```

```bash
k get pvc q3-pvc -n exam-strategy-practice
k auth can-i list pods --as=system:serviceaccount:exam-strategy-practice:app-sa -n exam-strategy-practice
```

- [ ] I used a manifest or command pattern that matched the task instead of relying on memory alone.
- [ ] I verified the PVC object and the RBAC permission separately.
- [ ] I stopped adding fields once the stated requirements were satisfied.

### Step 4: Pass 3 Complex Troubleshooting

Now troubleshoot the broken Deployment. Start by observing the state, then use events to identify the likely cause. Make one focused change and verify the rollout.

```bash
k get deployment q4-broken -n exam-strategy-practice
k get pods -l app=q4-broken -n exam-strategy-practice
k describe pod -l app=q4-broken -n exam-strategy-practice
k get events -n exam-strategy-practice --sort-by='.lastTimestamp'
```

```bash
k set image deployment/q4-broken nginx=nginx:1.25 -n exam-strategy-practice
k rollout status deployment/q4-broken -n exam-strategy-practice
k get pods -l app=q4-broken -n exam-strategy-practice
```

- [ ] I gathered evidence before changing the Deployment.
- [ ] I made one targeted fix based on the observed failure.
- [ ] I verified that the rollout completed or made visible progress.
- [ ] I preserved partial credit instead of deleting useful work when time was tight.

### Step 5: Review Your Strategy

After the timer stops, review the decisions rather than only the commands. Strategy improves when you identify where your estimates were wrong. If a quick task took too long, ask whether the command was unfamiliar or the requirement was more complex than it looked. If a medium task became troubleshooting, ask what evidence would have told you to skip earlier.

- [ ] I recorded which task took longer than expected and why.
- [ ] I identified one command or manifest pattern to practice before the next mock exam.
- [ ] I identified one moment where I should have skipped earlier or stayed longer.
- [ ] I cleaned up the practice namespace after finishing the review.

```bash
k delete namespace exam-strategy-practice
rm -f /tmp/exam-strategy-pods.txt
```

---

## Next Module

Next: [Part 1: Cluster Architecture, Installation & Configuration](/k8s/cka/part1-cluster-architecture/)
