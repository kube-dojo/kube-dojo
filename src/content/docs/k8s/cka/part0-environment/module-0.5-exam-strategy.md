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
> **Complexity**: `[QUICK]` - Strategy, not technical skills
>
> **Time to Complete**: 15-20 minutes to read, lifetime to master
>
> **Prerequisites**: Modules 0.1-0.4

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Apply** the Three-Pass Method to maximize your score under time pressure
- **Triage** exam questions by difficulty and time estimate (quick wins first, hard ones last)
- **Manage** exam time using the 2-minute rule (if stuck for 2 minutes, flag and move on)
- **Avoid** the #1 exam failure mode: spending 15 minutes on a 4-point question while skipping three 7-point questions

---

## Why This Module Matters

You can know Kubernetes perfectly and still fail the CKA.

How? Time.

16 questions. 120 minutes. That's 7.5 minutes average per question. But questions aren't equal—some take 2 minutes, others take 15. If you spend 15 minutes on a hard question first and don't finish the easy ones, you've thrown away points.

The **Three-Pass Method** is a strategy that maximizes your score regardless of question difficulty.

---

## The Problem: Linear Thinking

Most people approach exams linearly:

```
Question 1 → Question 2 → Question 3 → ... → Question 16
```

This fails when:
- Question 3 is a 15-minute troubleshooting nightmare
- You spend 20 minutes on it (perfectionism)
- You rush through Questions 14-16
- You miss easy points you could have gotten

> **War Story: The 4-Point Black Hole**
> A candidate taking the CKA encountered a question worth 4 points asking them to fix a crashing CoreDNS pod. They spent 22 minutes digging through logs, editing ConfigMaps, and restarting deployments. They eventually fixed it, but they only had 5 minutes left for the last three questions—two of which were simple 7-point JSONPath and scaling tasks. They lost 14 easy points to gain 4 hard points, failing the exam by a 3% margin.

The CKA passing score is **66%**. You don't need perfect—you need efficient.

---

> **Think about it**: The exam has 16 questions worth different points. A 4-point question and a 7-point question both take "about 10 minutes" if you get stuck. But the 7-point question is worth 75% more. If you only have time for one, which do you pick? This is why strategy matters as much as knowledge.

## The Solution: Three-Pass Method

Instead of linear, work in passes:

```
┌─────────────────────────────────────────────────────────────────┐
│                     THE THREE-PASS METHOD                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PASS 1: QUICK WINS (1-3 minutes each)                          │
│  ├── Scan ALL 16 questions first                                │
│  ├── Do every task you can complete quickly                     │
│  ├── Skip anything that looks complex                           │
│  └── Goal: Secure easy points, bank time                        │
│                                                                  │
│  PASS 2: MEDIUM TASKS (4-6 minutes each)                        │
│  ├── Return to skipped questions                                │
│  ├── Do tasks requiring moderate effort                         │
│  ├── Skip if stuck after 5-6 minutes                            │
│  └── Goal: Steady progress                                      │
│                                                                  │
│  PASS 3: COMPLEX TASKS (remaining time)                         │
│  ├── Tackle the hardest questions last                          │
│  ├── Use ALL remaining time                                     │
│  ├── Partial solutions get partial credit                       │
│  └── Goal: Maximize remaining points                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Recognizing Task Complexity

Before you can use the three-pass method, you need to instantly categorize questions.

### Quick Wins (1-3 minutes)

**Indicators**:
- "Create a Pod/Deployment/Service"
- "Add a label to..."
- "Scale deployment to..."
- "Expose service on port..."
- Single-step operations
- Resources you create often

**Examples**:
- Create an nginx pod
- Add label `env=prod` to all pods in namespace
- Scale deployment `web` to 5 replicas
- Create a NodePort service for deployment `api`

### Medium Tasks (4-6 minutes)

**Indicators**:
- "Configure RBAC..."
- "Create a NetworkPolicy..."
- "Set up a PersistentVolumeClaim..."
- "Configure a ConfigMap and use it in..."
- Multi-step but straightforward
- Requires looking up syntax

**Examples**:
- Create Role and RoleBinding for user to list pods
- Create NetworkPolicy allowing only frontend pods to reach backend
- Create PVC and mount it in a pod
- Create ConfigMap and inject as environment variables

### Complex Tasks (8-15 minutes)

**Indicators**:
- "Troubleshoot why..."
- "Fix the broken..."
- "The cluster is not..."
- "Debug and resolve..."
- Multi-cluster or multi-step
- Requires investigation

**Examples**:
- Troubleshoot why pods are not scheduling
- Fix the broken deployment (something is wrong, figure it out)
- Node is NotReady, find and fix the issue
- Application cannot connect to database, resolve

> **Pause and predict**: Before moving to Pass 1, test your gut reaction. How would you categorize these three tasks?
> 1. "Fix a kubelet that fails to start on worker-node-2."
> 2. "Create a Secret and mount it as a volume in a new Pod."
> 3. "Output the names of all Pods with label `tier=front` to a file."
>
> *Answers: 1 is Complex (troubleshooting, unpredictable time). 2 is Medium (multi-step YAML, relies on docs). 3 is Quick (single imperative command).*

---

## Part 2: Pass 1 - Quick Wins

### What To Do

1. **Start of exam**: Read through ALL 16 questions quickly (5 minutes)
2. **Identify quick wins**: Mark them mentally or on scratch paper
3. **Execute quick wins**: Do all easy questions first
4. **Don't get distracted**: If anything takes longer than expected, skip

### Time Budget

- Scan all questions: 5 minutes
- Quick wins (assume 4-6 questions): 15-20 minutes
- **Pass 1 total**: ~25 minutes

### Example Quick Wins

```yaml
# Question: Create a pod named 'web' running nginx in namespace 'production'
# Time: <1 minute

kubectl run web --image=nginx -n production

# Done. Next question.
```

```yaml
# Question: Scale deployment 'api' to 3 replicas
# Time: <30 seconds

kubectl scale deploy api --replicas=3

# Done. Next question.
```

```yaml
# Question: Create a ClusterIP service for deployment 'backend' on port 8080
# Time: <1 minute

kubectl expose deploy backend --port=8080

# Done. Next question.
```

### The Psychology

Quick wins build confidence. After Pass 1, you've already answered 4-6 questions correctly. That's potentially 25-35% of the exam done in 25 minutes. The pressure is off.

---

## Part 3: Pass 2 - Medium Tasks

### What To Do

1. **Return to skipped questions**: Start with the least complex
2. **Use documentation**: This is where kubernetes.io helps
3. **Time-box yourself**: If stuck after 5-6 minutes, move on
4. **Accept "good enough"**: Partial solutions > nothing

### Time Budget

- Medium tasks (assume 6-8 questions): 50-60 minutes
- **Pass 2 total**: ~55 minutes
- **Cumulative**: ~80 minutes (40 minutes remaining)

### Example Medium Tasks

```yaml
# Question: Create a NetworkPolicy that allows pods with label 'role=frontend'
#           to access pods with label 'role=backend' on port 3306

# Time: 4-5 minutes
# Strategy: Look up NetworkPolicy template, modify

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      role: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - port: 3306
```

```yaml
# Question: Create a ServiceAccount 'app-sa', a Role that can list pods,
#           and bind them together

# Time: 5-6 minutes
# Strategy: kubectl create commands + YAML for binding

kubectl create serviceaccount app-sa
kubectl create role pod-reader --verb=get,list,watch --resource=pods
kubectl create rolebinding app-sa-binding --role=pod-reader --serviceaccount=default:app-sa
```

> **Stop and think**: Pause and plan your own time budget. If you know you are naturally slow at writing YAML but very fast at kubectl imperative commands, how might you adjust the 55 minutes for Pass 2? Sketch out your personalized time limits before reading further.

---

## Part 4: Pass 3 - Complex Tasks

### What To Do

1. **Use ALL remaining time**: No need to rush now
2. **Methodical troubleshooting**: Gather info → hypothesize → test
3. **Partial credit**: Fixing SOME of the issue is better than nothing
4. **Don't panic**: You've already secured most of your points

### Time Budget

- Complex tasks (assume 2-4 questions): 40 minutes
- **Pass 3 total**: ~40 minutes
- **Buffer**: 0 minutes (you've used all time strategically)

### Example Complex Task

```
Question: The deployment 'critical-app' in namespace 'production' is not
working correctly. Pods are in CrashLoopBackOff. Troubleshoot and fix.
```

**Troubleshooting Approach**:

```bash
# Step 1: Gather information (2 minutes)
kubectl get pods -n production
kubectl describe pod critical-app-xxx -n production
kubectl logs critical-app-xxx -n production
kubectl get events -n production --sort-by='.lastTimestamp'

# Step 2: Identify issue (from logs/events)
# Example: ConfigMap 'app-config' not found

# Step 3: Fix
kubectl get cm -n production  # Confirm it's missing
kubectl create configmap app-config --from-literal=KEY=value -n production

# Step 4: Verify
kubectl get pods -n production -w  # Watch until Running
```

### Partial Credit Strategy

If you can't fully solve a complex task:

1. **Fix what you can**: If 3 things are broken, fix 2
2. **Document your progress**: The grader may see partial work
3. **Don't leave it blank**: Any progress is better than none

---

## Part 5: Context Switching Discipline

Every CKA question specifies a cluster context. **This is critical.**

### The #1 Exam Mistake

Solving a problem on the wrong cluster. You do everything right, but on the wrong context. Zero points.

> **War Story: The Perfect Zero**
> A candidate flawlessly executed a complex ETCD backup and restore procedure worth 11 points. It took them 12 minutes, and they verified the snapshot perfectly. When they got their exam results, they scored 0 on that question. Why? They performed the backup on the `k8s-master` context instead of the required `wk8s-cluster` context. The grading script checked `wk8s-cluster`, found no backup file, and awarded zero points.

### The Rule

**EVERY question, FIRST action**: Switch context.

```bash
# At the start of EVERY question
kubectl config use-context <context-from-question>
```

Make it muscle memory. Read question → switch context → then solve.

### Verification

After switching:
```bash
kubectl config current-context
```

This takes 2 seconds. It can save 7 minutes of wasted work.

> **Stop and think**: You just perfectly solved a 7-point NetworkPolicy question, but as you review your work, you realize you forgot to switch context at the start. What do you do?
>
> *Answer: Do not panic. Switch to the correct context immediately. Re-apply your YAML file or commands in the correct cluster. Finally, switch back to the wrong context and delete the resources you accidentally created to avoid unintended side effects.*

---

## Part 6: The "Good Enough" Mindset

Perfectionists fail the CKA. Here's why.

### Perfectionism Trap

```
Question: Create a deployment with 3 replicas, resource limits,
          health checks, and a ConfigMap volume

Perfectionist:
- Spends 10 minutes crafting perfect YAML
- Double-checks every field
- Adds optional best practices
- Runs out of time on other questions
```

### Good Enough Approach

```
Good Enough:
- Creates working deployment (3 minutes)
- Adds required fields only
- Verifies it works
- Moves on

Result: Same points, 7 minutes saved
```

### The 80% Rule

If your solution works and meets the requirements, it's done. Don't:
- Add "nice to have" features
- Refactor for cleanliness
- Add comments explaining your logic
- Double-check already-working solutions

---

## Part 7: Time Checkpoints

Set mental checkpoints during the exam:

| Time Elapsed | Checkpoint | Status Check |
|--------------|------------|--------------|
| 30 minutes | End of Pass 1 | Should have 4-6 questions done |
| 80 minutes | End of Pass 2 | Should have 10-12 questions done |
| 110 minutes | Pass 3 in progress | Working on complex tasks |
| 120 minutes | Exam ends | Submit |

If you're behind at a checkpoint, speed up. Skip more aggressively.

> **Success Story: From Failed to 89%**
>
> A candidate failed their first CKA attempt with 58%. They'd spent 18 minutes on a troubleshooting question in the first pass, then rushed through everything else. On their second attempt, they used the three-pass method religiously. Pass 1: 6 questions in 22 minutes. Pass 2: 7 questions in 50 minutes. Pass 3: 3 complex questions with 48 minutes remaining. Final score: 89%. Same knowledge, different strategy, completely different outcome.

---

### When Three-Pass Doesn't Work

The Three-Pass method isn't flawless. Be aware of these edge cases:
- **Misjudging Complexity**: You might tag a task as "Quick," but realize 3 minutes in that there's a trick (e.g., a missing namespace or a broken API). *Adjustment*: Be ruthless. If a Quick task hits the 4-minute mark, downgrade it to Medium/Complex and walk away.
- **The "All Medium" Exam**: Sometimes, you won't get any 1-minute tasks. If every question seems to require YAML and 5 minutes of work, Pass 1 might only yield 2 completed questions. *Adjustment*: Don't panic. Combine Pass 1 and Pass 2, maintaining a strict 6-minute cap per question.

---

## Part 8: Pre-Exam Routine

### 5 Minutes Before

1. **Environment ready**: Water, quiet space, ID
2. **Mental state**: Calm, focused, confident
3. **Remember**: Three-pass method. Quick wins first.

### First 5 Minutes of Exam

1. **Read ALL questions**: Don't start solving yet
2. **Categorize mentally**: Quick / Medium / Complex
3. **Plan your passes**: Know which questions you'll hit first
4. **Set up aliases**: If not pre-configured

### Last 5 Minutes of Exam

1. **Don't start new complex tasks**: Not enough time
2. **Verify critical answers**: Quick sanity checks
3. **Submit any partial work**: Something > nothing
4. **Breathe**: You did your best

---

## Beyond the Exam: Triage as a Site Reliability Engineer (SRE)

> **Real-World Connection**: The Three-Pass method isn't just an exam trick; it's incident response training. When an outage hits a production cluster, you will face dozens of firing alerts. You can't fix them linearly. You triage:
> 1. **Quick Wins (Mitigation)**: Can I scale up the deployment or rollback to stabilize the system in 2 minutes?
> 2. **Medium Tasks (Investigation)**: Let's pull the logs and check the database connection limits.
> 3. **Complex Tasks (Root Cause)**: We need to analyze the memory leak in the application code.
> Mastering exam triage directly translates to keeping your cool during a Sev-1 outage.

---

## Did You Know?

- **66% is passing**. That means you can get 5-6 questions completely wrong and still pass. The three-pass method ensures you don't leave easy points on the table.

- **Partial credit exists**. If a question is worth 7 points and you get 4 things right, you might get 4 points. Always attempt something.

- **The exam is designed to be hard**. The Linux Foundation expects many people to run out of time. Your strategy matters as much as your knowledge.

- **Second attempts are allowed**. If you fail, you get one free retake with your exam purchase. This isn't the end of the world.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Starting with Question 1 | Might be hard | Scan all first, pick easy ones |
| Perfectionism | Time waste | "Good enough" mindset |
| Wrong context | Zero points | Always switch context first |
| Stuck on hard question | Time drain | Skip after 5-6 minutes, return later |
| Not using remaining time | Leaving points | Use ALL time on complex tasks |
| Panicking | Poor decisions | Trust your preparation |

---

## Quiz

1. **Question Categorization**: You read the following task: "Upgrade the kubeadm cluster on the master node to version 1.28.x." How do you categorize this, and why?
   <details>
   <summary>Answer</summary>
   Complex (Pass 3). While the steps are well-documented, a cluster upgrade involves multiple commands like draining nodes, upgrading kubeadm, applying upgrades, upgrading the kubelet, and uncordoning. It takes significant time and carries a high risk of getting stuck if a node does not drain properly due to restrictive PodDisruptionBudgets or local data. Because of this unpredictability and the high volume of steps, you should save it for Pass 3 to ensure it does not consume time meant for quicker wins.
   </details>

2. **Scenario-Based Triage**: You have 45 minutes remaining in the exam. You have three questions left:
   - Question 12 (12 points): Troubleshoot a broken cluster network (Complex).
   - Question 14 (4 points): Create a CronJob (Medium).
   - Question 15 (8 points): Create a NetworkPolicy and expose a Pod (Medium).
   What is your optimal execution order and why?
   <details>
   <summary>Answer</summary>
   Your optimal order is Question 15, then Question 14, and finally Question 12. You must secure predictable points first, and the two medium tasks are standard operations that will reliably yield a combined 12 points in about 15 minutes. Question 12 is a troubleshooting task that could easily consume your entire remaining 45 minutes if you go down a rabbit hole. By banking the 12 easy and medium points first, you ensure you do not fail because you ran out of time, and you can comfortably dedicate the remaining 30 minutes to diagnosing the broken network.
   </details>

3. **Calculate the Tradeoff**: You have 15 minutes left. You can either attempt a 9-point ETCD restore (Complex, estimated 12 minutes) OR two separate questions: a 4-point RBAC task (estimated 5 minutes) and a 5-point Service/Ingress task (estimated 6 minutes). Which option gives you the better point-per-minute return, and which should you choose?
   <details>
   <summary>Answer</summary>
   Attempting the two smaller tasks gives you a better point-per-minute return (0.81 points per minute vs 0.75 points per minute) and is the strategically correct choice. You should choose the RBAC and Service/Ingress tasks because they yield a better return on your limited time. More importantly, this approach diversifies your risk across two separate grading rubrics. If you make a fatal mistake on the ETCD restore, you lose all 9 points, but if you mess up the RBAC task, you can still secure 5 points from the Ingress task.
   </details>

4. **Full Triage Planning**: You have 5 minutes left in the exam. You are working on a 7-point troubleshooting question, but you are completely stuck. You remember skipping a 2-point question to "output the CPU usage of nodes to a file." What is your exact plan of action for the last 5 minutes?
   <details>
   <summary>Answer</summary>
   You should immediately stop troubleshooting the 7-point question and switch to the 2-point question. Your chances of successfully identifying and fixing a complex bug in 5 minutes while under severe exam pressure are near zero. Instead, switch your context to the 2-point question, run the quick imperative command to output the CPU usage, and verify the file. If you have a minute left afterward, switch back to the context of the 7-point question and leave whatever partial configuration you managed to create, as you might receive partial credit for the steps you completed.
   </details>

---

## Hands-On Exercise

**Task**: Practice categorizing questions and timing yourself.

### Exercise 1: Question Categorization

Categorize these sample CKA questions as `[QUICK]`, `[MEDIUM]`, or `[COMPLEX]`:

1. Create a pod named `nginx` running the `nginx:1.25` image
2. The deployment `web-app` is not starting. Pods show `CrashLoopBackOff`. Find and fix the issue.
3. Scale the deployment `api` to 5 replicas
4. Create a NetworkPolicy that allows pods with label `role=frontend` to access pods with label `role=db` on port 3306
5. Create a ClusterRole that allows listing and getting pods, and bind it to user `developer`
6. Node `worker-02` is in `NotReady` state. Troubleshoot and fix.
7. Add the label `env=production` to all pods in namespace `app`
8. Create a PersistentVolumeClaim requesting 5Gi storage with `ReadWriteOnce` access mode

<details>
<summary>Answers</summary>

1. `[QUICK]` - Single kubectl command
2. `[COMPLEX]` - Requires investigation
3. `[QUICK]` - Single kubectl command
4. `[MEDIUM]` - Requires YAML, but straightforward
5. `[MEDIUM]` - Multi-step but documented
6. `[COMPLEX]` - Troubleshooting required
7. `[QUICK]` - Single kubectl command with selector
8. `[MEDIUM]` - Requires YAML template

</details>

### Exercise 2: Timed Practice

Set a timer and practice:

1. **2 minutes**: Create a deployment with 3 replicas and expose it
2. **5 minutes**: Create a complete RBAC setup (Role, RoleBinding, ServiceAccount)
3. **3 minutes**: Create a NetworkPolicy from documentation

**Success Criteria**:
- [ ] Can categorize question complexity in <10 seconds
- [ ] Understand which pass each question belongs to
- [ ] Can execute quick wins without hesitation

---

## Practice Drills

### Drill 1: Question Categorization Speed Test (Target: 2 minutes)

Categorize all 10 questions as QUICK / MEDIUM / COMPLEX. Time yourself.

1. Create namespace `production`
2. Troubleshoot why deployment `api` pods are CrashLoopBackOff
3. Create a ConfigMap named `app-config` with key `LOG_LEVEL=debug`
4. Scale StatefulSet `database` to 5 replicas
5. Create NetworkPolicy allowing frontend pods to reach backend on port 443
6. Node `worker-03` shows NotReady. Find and fix the issue.
7. Create ClusterRole allowing get/list on secrets, bind to user `auditor`
8. Add annotation `owner=team-a` to deployment `web`
9. Create PVC with 10Gi storage, ReadWriteOnce, StorageClass `fast`
10. Debug: Service `api-svc` not routing traffic to pods. Fix it.

<details>
<summary>Answers</summary>

1. QUICK - single command
2. COMPLEX - requires investigation
3. QUICK - single command
4. QUICK - single command
5. MEDIUM - requires YAML
6. COMPLEX - troubleshooting
7. MEDIUM - multi-step but documented
8. QUICK - single command
9. MEDIUM - requires YAML
10. COMPLEX - troubleshooting

</details>

### Drill 2: Mock Exam - Pass 1 Only (Target: 15 minutes)

Do ONLY the quick wins from Drill 1. Skip all MEDIUM and COMPLEX.

```bash
# Start timer

# 1. Create namespace
kubectl create ns production

# 3. Create ConfigMap
kubectl create cm app-config --from-literal=LOG_LEVEL=debug

# 4. Scale StatefulSet
kubectl scale sts database --replicas=5

# 8. Add annotation
kubectl annotate deploy web owner=team-a

# Stop timer. Target: <5 minutes for 4 questions
# You just secured ~25% of points in <5 minutes
```

### Drill 3: Context Switching Under Pressure (Target: 3 minutes)

Simulate exam context switching. Create test contexts and practice:

```bash
# Setup
kubectl config set-context exam-cluster-1 --cluster=kubernetes --user=kubernetes-admin
kubectl config set-context exam-cluster-2 --cluster=kubernetes --user=kubernetes-admin
kubectl config set-context exam-cluster-3 --cluster=kubernetes --user=kubernetes-admin

# DRILL: Read the question, switch context, verify, then solve
# Timer starts NOW

# Question 1: On cluster exam-cluster-1, create pod nginx
kubectl config use-context exam-cluster-1
kubectl config current-context  # Verify!
kubectl run nginx --image=nginx

# Question 2: On cluster exam-cluster-2, create namespace dev
kubectl config use-context exam-cluster-2
kubectl config current-context  # Verify!
kubectl create ns dev

# Question 3: On cluster exam-cluster-3, scale deploy web to 3
kubectl config use-context exam-cluster-3
kubectl config current-context  # Verify!
kubectl scale deploy web --replicas=3 2>/dev/null || echo "deploy not found - expected in drill"

# Timer stop. Did you verify context EVERY time?
```

### Drill 4: Time Pressure Simulation (Target: 7 minutes)

Simulate a medium-complexity question under time pressure:

```bash
# START TIMER: You have exactly 7 minutes

# QUESTION:
# Create a ServiceAccount named 'app-sa' in namespace 'secure'
# Create a Role named 'secret-reader' that can get and list secrets
# Bind the role to the service account
# Create a pod 'test-pod' using this service account

# GO!

kubectl create ns secure
kubectl create sa app-sa -n secure
kubectl create role secret-reader --verb=get,list --resource=secrets -n secure
kubectl create rolebinding app-sa-binding --role=secret-reader --serviceaccount=secure:app-sa -n secure
kubectl run test-pod --image=nginx --serviceaccount=app-sa -n secure

# VERIFY
kubectl get sa,role,rolebinding,pod -n secure

# STOP TIMER
# <5 min: Excellent
# 5-7 min: Good
# >7 min: Practice more

# Cleanup
kubectl delete ns secure
```

### Drill 5: Partial Credit Practice

**Scenario**: You're stuck on a complex question with 3 minutes left. Practice getting partial credit.

```bash
# QUESTION: The deployment 'web-app' is not working. Pods are in
# ImagePullBackOff. Troubleshoot and fix. Also ensure the deployment
# has resource limits set.

# You have 3 minutes. You won't finish everything. Get partial credit.

# Step 1: Diagnose (30 seconds)
kubectl describe pod -l app=web-app | grep -A5 "Events"
# See: Failed to pull image "nginx:nonexistent"

# Step 2: Fix the obvious issue (30 seconds)
kubectl set image deploy web-app web-app=nginx:1.25

# Step 3: Check if working now (30 seconds)
kubectl get pods -l app=web-app
# Running? Good!

# Time's up! You didn't add resource limits, but you got partial credit
# for fixing the image issue.
```

### Drill 6: Full Mini-Exam (Target: 20 minutes)

Complete this 4-question mini-exam using the three-pass method:

**Question 1** (3%): Create a pod `q1-pod` running `nginx`

**Question 2** (7%): Create a NetworkPolicy `q2-netpol` in namespace `web` that:
- Applies to pods with label `app=backend`
- Allows ingress only from pods with label `app=frontend`
- Allows ingress only on port 8080

**Question 3** (5%): Create a PVC `q3-pvc` requesting 5Gi with ReadWriteOnce

**Question 4** (10%): Debug: The deployment `q4-broken` exists but pods won't start. Fix it.

```bash
# Setup for Q4
kubectl create deploy q4-broken --image=nginx:doesnotexist
```

**Instructions**:
1. Read all 4 questions (1 minute)
2. Pass 1: Quick wins only
3. Pass 2: Medium tasks
4. Pass 3: Complex (Q4)

<details>
<summary>Solutions</summary>

```bash
# Pass 1: Quick wins
# Q1 (QUICK)
kubectl run q1-pod --image=nginx

# Pass 2: Medium
# Q3 (MEDIUM)
cat << 'EOF' | kubectl apply -f -
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
EOF

# Q2 (MEDIUM)
kubectl create ns web
cat << 'EOF' | kubectl apply -f -
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
    - port: 8080
EOF

# Pass 3: Complex
# Q4 (COMPLEX)
kubectl describe deploy q4-broken
kubectl get pods | grep q4-broken
kubectl describe pod q4-broken-xxx | grep -A5 Events
# Image doesn't exist - fix:
kubectl set image deploy q4-broken nginx=nginx:1.25

# Verify all
kubectl get pod q1-pod
kubectl get netpol -n web
kubectl get pvc q3-pvc
kubectl get pods | grep q4-broken
```

</details>

### Drill 7: Challenge - 30-Minute Intensive

Set aside 30 uninterrupted minutes. Complete as many tasks as possible:

1. Create namespace `exam-practice`
2. Create ConfigMap `cm-1` with 3 key-value pairs
3. Create Secret `secret-1` with username and password
4. Create Deployment `web` with 3 replicas using nginx
5. Expose deployment `web` on NodePort 30080
6. Create PVC `data-pvc` with 1Gi storage
7. Create Pod `data-pod` using the PVC at `/data`
8. Create ServiceAccount `app-sa`
9. Create Role `pod-reader` (get, list, watch pods)
10. Bind Role to ServiceAccount
11. Create NetworkPolicy allowing only port 80 ingress
12. Scale deployment `web` to 5 replicas
13. Create HPA for `web` (min 2, max 10, CPU 80%)
14. Create Job `batch-job` that runs `echo "done"` and exits
15. Create CronJob `cron-job` running every 5 minutes

All in namespace `exam-practice`. Track your score:
- 15/15: Exam ready
- 12-14: Almost there
- 9-11: Keep practicing
- <9: Review modules 0.1-0.4

```bash
# Cleanup
kubectl delete ns exam-practice
```

---

## Summary: Three-Pass Reference Card

```
╔═══════════════════════════════════════════════════════════════╗
║               THREE-PASS EXAM STRATEGY                         ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  BEFORE SOLVING: Read ALL 16 questions (5 min)                 ║
║                                                                ║
║  PASS 1: QUICK WINS                                            ║
║  • 1-3 min tasks                                               ║
║  • Create, scale, label, expose                                ║
║  • Target: ~25 min for 4-6 questions                           ║
║                                                                ║
║  PASS 2: MEDIUM TASKS                                          ║
║  • 4-6 min tasks                                               ║
║  • RBAC, NetworkPolicy, PVC, ConfigMap                         ║
║  • Target: ~55 min for 6-8 questions                           ║
║                                                                ║
║  PASS 3: COMPLEX TASKS                                         ║
║  • 8-15 min tasks                                              ║
║  • Troubleshooting, multi-step, debugging                      ║
║  • Target: ~40 min for remaining questions                     ║
║                                                                ║
║  ALWAYS: Switch context first. Good enough > perfect.          ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Next Steps

Congratulations! You've completed **Part 0: Environment & Exam Technique**.

You now have:
- ✅ A working multi-node Kubernetes cluster
- ✅ Optimized shell with aliases and autocomplete
- ✅ Vim configured for YAML editing
- ✅ Knowledge of where to find documentation fast
- ✅ A strategy to maximize your exam score

**Next**: [Part 1: Cluster Architecture, Installation & Configuration](../part1-cluster-architecture/)

This is where the real Kubernetes learning begins.