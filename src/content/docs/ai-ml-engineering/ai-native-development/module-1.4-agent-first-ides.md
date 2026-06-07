---
title: "Agent-First IDEs"
slug: ai-ml-engineering/ai-native-development/module-1.4-agent-first-ides
sidebar:
  order: 205
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 4-6 hours

---

**Prerequisites**: [Module 1.1: AI Coding Tools Landscape](/ai-ml-engineering/ai-native-development/module-1.1-ai-coding-tools-landscape/) and Modules 1.2–1.3 complete

> **Go deeper:** For how applications package context and how harness layers record agent work, see [Context Engineering Fundamentals](/ai/ai-engineering-foundations/module-2.1-context-fundamentals/) and [Harness Fundamentals — Layers and System of Record](/ai/ai-engineering-foundations/module-3.1-harness-fundamentals-layers-and-system-of-record/).

---

## What You'll Be Able to Do

By the end of this module, you will:

- Map IDE tool modes to autonomy levels L0–L5 and explain how agent-first delegation differs from autocomplete-first editing inside the editor.
- Separate harness design (permissions, artifacts, billing, data path) from raw model capability when evaluating IDE-integrated tools.
- Compare GitHub Copilot, Cursor, Google Antigravity, Windsurf, and Cline as peer illustrations using fit-based reasoning rather than brand rankings.
- Decide when the IDE form factor fits a task versus when a CLI or headless agent is the better match, including cross-reference to Module 1.5.
- Apply task scoping, artifact review, and approval policies that reduce over-delegation and security risk in shared repositories.

---

## Why This Module Matters

Hypothetical scenario: two engineers on the same team both say they "use AI in the IDE." One accepts inline completions while typing; the other delegates a three-file refactor to an agent panel and reviews a batch of diffs at the end of the session. They are using the same form factor — an editor with AI — but granting very different authority to the tool, which means their risk profile, review burden, and recovery options diverge even though the user interface looks similar.

That gap matters because IDE-integrated agents can change production code, run shell commands, open browsers, and create files you did not anticipate. The comfortable editing surface does not make those actions low-risk. Teams that treat every IDE assistant as "just smarter autocomplete" often discover the difference when an agent widens scope beyond the ticket, skips edge cases that tests never cover, or adds a credential file that never appeared in the diff they skimmed before merge.

This module teaches the durable concepts behind IDE-integrated agents: how autocomplete-first and agent-first modes differ, how harness design shapes safety, and how major products illustrate those concepts as peers rather than ranked winners. Product names, model lineups, and pricing change quarterly; the form-factor tradeoffs — editor as system of record, diff review, artifacts, permission gates — last longer. For the cross-tool Rosetta Stone on authority, evaluation worksheets, and vendor-claim testing, see [Module 1.1](/ai-ml-engineering/ai-native-development/module-1.1-ai-coding-tools-landscape/). For the contrasting CLI and headless form factor, see [Module 1.5: CLI AI Coding Agents](/ai-ml-engineering/ai-native-development/module-1.5-cli-ai-coding-agents/).

---

## The IDE-Integrated Form Factor

An IDE-integrated AI coding tool keeps the agent inside the editor you already use. The editor remains the system of record: you open files, read diffs, run tests from the terminal panel, and commit through Git. The agent does not replace that surface; it operates within it, which is why IDE agents feel familiar to developers who already live in VS Code, JetBrains, or a forked editor while still expanding what the assistant is allowed to do on your behalf.

What this form factor buys you is a tight loop between intent, action, and review. Inline L0 autocomplete offers ghost-text suggestions as you type with minimal context switching. In-context multi-file edits let the agent propose patches across several files while you review diff-by-diff before accepting anything into the branch. Artifacts and checkpoints — plans, checklists, screenshots, command logs — document what the agent did without forcing you to read every line on the first pass. Configurable autonomy through approval gates for terminal commands, browser actions, and file creation lets teams match tool authority to repository sensitivity instead of accepting vendor defaults.

This is materially different from browser chat, which has no direct edit path into your tree, and from headless CLI agents, which prioritize composability and log streams over inline visual diffs. Module 1.1 maps the full tool landscape by authority — what each tool can read, edit, and execute. This module zooms in on one layer of that map: tools where the editor is home base and the human reviewer is expected to stay in the loop for most production work.

**The workshop analogy:** a browser chat is like calling a consultant on the phone — useful advice, but you still carry every change back to the bench yourself. An IDE-integrated agent is like a skilled assistant standing beside you at the workbench: they can hand you parts, mark up your blueprint, and run the test jig while you watch. You still own the final assembly; the difference is how much of the loop happens in one place without switching applications.

---

## Landscape Snapshot (Volatile Details)

Product facts below are a point-in-time snapshot. Verify pricing, models, and feature names on official documentation before adopting them in production or writing team policy around them.

> **As of 2026-06** — the IDE agent landscape moves fast; confirm details before relying on them.

| Topic | Snapshot |
|-------|----------|
| **Google Antigravity** | Google's agent-first platform: multi-agent manager surface, editor view, CLI, and SDK; Gemini-powered. Google announced sunsetting the Gemini CLI and Code Assist *individual* tier on **June 18, 2026**, folding individual-tier workflows into Antigravity; enterprise Code Assist is retained. |
| **Cursor** | VS Code–forked IDE; inline completion, Composer-style multi-file agent, background agents; BYO API key and frontier model picker. |
| **Windsurf** | VS Code–forked IDE; Cascade agent with Flows session memory; browser and terminal integration. |
| **Cline** | Open-source VS Code extension; BYO cloud APIs and local models (for example via Ollama); human-in-the-loop approvals. |
| **GitHub Copilot** | Editor extension and Copilot Chat; frontier model picker in supported configurations; no local-model path in the standard product — cloud-hosted models only. |

---

## What Makes an IDE "Agent-First"?

### Autocomplete-First vs Agent-First

Think of the evolution inside the editor as increasing delegation surface, not just smarter next-token prediction. Autocomplete-first tools keep the buffer primary: you write, the model suggests the next line or block, and you accept or reject each suggestion without handing over a multi-step goal. Agent-first tools elevate a task panel or manager surface so you describe outcomes in natural language, the harness plans and acts within permission boundaries, and you review artifacts and diffs before the work lands on main. The diagrams below contrast autocomplete-first (editor-primary) and agent-first (delegation co-primary) layouts.

**Autocomplete-first (editor-primary):**

```
┌─────────────────────────────────────────┐
│  Editor (primary)                       │
│  ┌─────────────────────────────────┐   │
│  │ Your code here...               │   │
│  │ AI suggests: next line ████     │   │
│  └─────────────────────────────────┘   │
│  [AI Chat Panel - secondary]            │
└─────────────────────────────────────────┘
You write → AI assists → You accept/reject each suggestion
```

**Agent-first (delegation co-primary):**

```
┌─────────────────────────────────────────┐
│  Agent panel / manager (co-primary)     │
│  ┌─────────────────────────────────┐   │
│  │ Task: "Fix auth bug"     [████░░]│   │
│  │ Task: "Add tests"        [██████]│   │
│  └─────────────────────────────────┘   │
│  [Editor - diffs, review, manual edits] │
└─────────────────────────────────────────┘
You delegate → Agent plans and acts → You review artifacts and diffs
```

The shift is not merely that AI appeared in the IDE; autocomplete has been there for years. The shift is that the default interaction can become task delegation — natural-language goals, multi-step plans, tool use, and evidence artifacts — while the editor stays the place you approve or reject outcomes.

### Autonomy Levels in the IDE (L0–L5)

Module 1.1 describes tool classes by authority. Inside the IDE form factor, map common modes to an autonomy ladder. Vendors mix levels in one product; the labels are pedagogical, not rigid product tiers.

| Level | Mode | Typical IDE behavior | Review burden |
|-------|------|----------------------|---------------|
| **L0** | Inline completion | Ghost text at cursor; single-line or block suggestions | Low — local accept/reject |
| **L1** | Editor chat | Explain selection, draft snippets, no file writes | Low — nothing commits without you |
| **L2** | Scoped multi-file edit | Agent proposes patches across named files; diff review | Medium — read each hunk |
| **L3** | Tool-using agent | Terminal commands, test runs, browser steps with approval gates | Medium–high — commands plus diffs |
| **L4** | Parallel / background agents | Multiple tasks or agents concurrently; async completion | High — track several artifact streams |
| **L5** | Sustained headless autonomy | Long-running loops with minimal UI (often CLI — see Module 1.5) | Highest — needs strong harness plus CI |

The IDE form factor is the natural home for L0 through L3 and increasingly L4 as background agents mature. L5 workflows — scripted pipelines, bastion-host repair, CI-integrated agents — usually fit the CLI form factor better because they prioritize composability and stdout evidence over inline diffs.

> **Did You Know?** The term "vibe coding" describes stating intent in natural language and letting AI generate much of the implementation. Reported productivity effects vary widely by task type, and many teams note that review time rises when agents edit more files per turn.

### Harness ⟂ Model

A common mistake is conflating the IDE harness — permissions, UI, indexing, artifact format, billing — with the model behind it. They are independent axes that you evaluate separately before standardizing on a stack.

| Product | Harness notes | Model flexibility |
|---------|---------------|-------------------|
| **Cursor** | Full IDE fork; Composer, agents, codebase index | BYO API key plus frontier model picker |
| **GitHub Copilot** | Extension inside VS Code and other hosts | Frontier model picker; **no local models** |
| **Cline** | VS Code extension; MCP tools; per-action approval | BYO cloud providers and local (Ollama, etc.) |
| **Google Antigravity** | Manager surface plus editor plus CLI/SDK | Gemini-powered; lineup tied to Google stack |
| **Windsurf** | Cascade agent; Flows memory | Vendor-managed models plus selectable hosted options |

Choosing an IDE form factor is therefore two decisions: whether the editing and review loop fits your task, and whether the model and data path fit your security and cost constraints. A flexible harness with a weaker model may lose on hard reasoning; a strong model behind a harness that cannot run your tests may lose on verification even when the prose looks confident.

---

## Peer Tour: Five IDE-Integrated Illustrations

The sections below describe durable capabilities each product illustrates. Names and feature labels change; compare current documentation when evaluating. For the cross-tool view of authority and evaluation methodology, see [Module 1.1](/ai-ml-engineering/ai-native-development/module-1.1-ai-coding-tools-landscape/). Illustrative examples rotate which tool leads each concept; they are not endorsements.

### GitHub Copilot — Inline-First with Agent Chat

GitHub Copilot established the mainstream pattern of L0 inline completion inside widely used editors. Copilot Chat and agent-style features extend the same harness with conversational and multi-step edits while keeping the developer in VS Code, Visual Studio, JetBrains IDEs, or other supported hosts, which matters for enterprises that cannot mandate a forked IDE.

Copilot illustrates low-friction L0 entry where completions trigger from typing with context from the open file and nearby symbols. It also shows how chat can stay inside the editor for explanations and patch proposals without a separate browser tab. Enterprise governance surfaces — organizational policies, seat billing, data-handling options — are part of the harness story and are distinct from consumer chat products even when the vendor name matches.

In fit terms, Copilot suits teams that want IDE-native assistance with a mature extension ecosystem and are satisfied with cloud-hosted frontier models, while deep parallel-agent orchestration or open-source harness auditability may point you toward other peers from Module 1.1.

### Cursor — Diff-Centric Multi-File Agent

Cursor is a VS Code–forked IDE that popularized Composer-style multi-file editing: you attach files to context, describe a change, and review unified diffs before applying. Its durable lesson is that codebase indexing plus diff-first review can outperform raw autonomy on established repositories where consistency matters more than speed.

Cursor illustrates L2–L3 agent loops where you plan, patch, and iterate in a side panel with terminal integration and configurable auto-run policies. Background agents (L4) continue work asynchronously while you edit elsewhere, converging back to reviewable diffs rather than silent commits. Model flexibility through subscription plus BYO API keys lets teams separate harness choice from model choice when policy allows.

Cursor's inline-edit and diff-first model fits established codebases where pattern consistency and reviewability dominate, and it is a weaker fit when the primary need is a mission-control view of many concurrent autonomous agents because that pattern is what Antigravity's manager surface targets explicitly.

### Google Antigravity — Multi-Agent Manager Surface

Antigravity is Google's agent-first IDE with a prominent manager surface: multiple agents can run tasks in parallel while you monitor status, artifacts, and outcomes from one cockpit-style view rather than serial chat threads.

Antigravity illustrates L4 parallel delegation where backend, frontend, tests, and documentation can progress concurrently with separate artifact streams. Rich artifacts — plans, checklists, diffs, screenshots, recordings — address the trust gap when agents touch many files. Browser integration lets agents drive Chrome for web testing or flow validation behind URL allowlists. Security controls include terminal execution policies, command allow/deny lists, and browser restrictions that teams should treat as part of the harness contract, not optional advanced settings.

**Illustrative workflow:** describe a task in natural language; the agent produces a plan whose depth depends on mode; the agent executes within permission settings; you review artifacts before accepting; you reject or request revision if evidence fails. Antigravity fits parallel independent workstreams in one session and workflows that benefit from browser-led verification, while it is a weaker fit when you require local-only models, minimal Google-stack coupling, or the lightest extension inside stock VS Code.

### Windsurf — Cascade and Flows Session Memory

Windsurf ships a VS Code–forked IDE built around Cascade, an agentic engine with Flows — persistent session memory across turns, terminal output, and corrections. Its durable lesson is that multi-step debugging fails when each turn forgets what you already tried.

Cascade separates context indexing, planning, and execution across files, terminal, and browser. Flows contrasts with stateless chat: when you say "that fix failed," a Flows-aware agent can reference the prior patch, terminal error, and rejected approach instead of asking you to restate the entire debugging narrative. Inline commands bridge L0 and L2 for quick edits without leaving the buffer.

Windsurf fits multi-step debugging and iterative refactors where session continuity reduces repeated explanation, and Cascade's memory model fits long single-thread sessions more than a manager UI optimized for unrelated parallel agents, so compare against Antigravity when parallelization is the main goal.

### Cline — Open Extension, BYO and Local Models

Cline runs as a VS Code extension, illustrating how to add agent capabilities inside an editor your organization already standardized on without migrating to a new application shell.

Cline illustrates harness portability on stock VS Code, model agnosticism across Anthropic, OpenAI, OpenRouter, and Ollama-local endpoints, human-in-the-loop approval for file edits and shell commands by default, and MCP integration for custom tools such as internal APIs or ticket systems. The approval UI pattern — view diff, approve, reject, or edit before run — is the harness expressing conservative defaults that teams can relax only after they have evidence.

Cline fits organizations that mandate stock VS Code, need auditable open-source harness code, or want local models for air-gapped or cost-predictable work, with the tradeoff that per-action approval is safer but slower than more autonomous defaults on greenfield tasks.

### Rotating Illustrations: Same Task, Different Peers

To internalize peer neutrality, take one bounded task — add a `/health` route with a JSON body and a single integration test — and imagine how each peer would likely frame the work. Copilot might accelerate L0 typing inside the handler you write yourself. Cursor might attach `routes.ts` and `tests/health.test.ts` to a Composer session and return a diff for review. Antigravity might schedule the route, test, and a browser screenshot of the response as separate streams on a manager surface. Windsurf might keep your failed first attempt in Flows memory when the test assertion expects a different content-type. Cline might ask you to approve each file write and `curl` command explicitly. None of these stories makes a universal winner; they show how harness shape changes the loop even when the model family is similar.

---

## Fit-Based Comparison

Use this matrix to match capabilities to constraints, not to crown a winner. Empty cells mean "not a primary design center today," not "missing forever."

| Capability | Copilot | Cursor | Antigravity | Windsurf | Cline |
|------------|---------|--------|-------------|----------|-------|
| **L0 inline completion** | Primary | Yes | Yes | Yes | Via editor |
| **L2 multi-file diffs** | Chat/agent features | Primary | Yes | Yes | Yes |
| **L4 parallel agents** | Limited | Background agents | Primary | Secondary | No |
| **Session memory (Flows-style)** | Partial | Partial | Artifacts | Primary | Partial |
| **Browser automation** | Varies | Varies | Primary | Yes | Yes |
| **Open-source harness** | No | No | No | No | Yes |
| **Local models** | No | Via config | No | No | Yes |
| **Frontier model picker** | Yes | Yes | Google stack | Hosted options | BYO |
| **Rich artifacts** | Varies | Diffs plus logs | Primary | Varies | Partial |

Products in this space borrow from one another: IDE forks add background agents, extensions add memory, manager UIs add stricter approval modes. End every comparison with a fit statement — "Tool X fits constraint Y; Tool Z fits constraint W" — and prefer the peer whose data path and harness defaults match governance rules when two tools fit the same task.

---

## IDE Form Factor vs CLI Form Factor

Prefer IDE-integrated workflows when you need visual diff review on every change, the team already lives in VS Code or a forked IDE, tasks sit at L0–L4 with frequent human steering, UI screenshots and inline breakpoints matter for verification, or you are onboarding developers who learn by reading patches in context. Prefer CLI and headless workflows — detailed in [Module 1.5](/ai-ml-engineering/ai-native-development/module-1.5-cli-ai-coding-agents/) — when you work on remote servers, containers, or CI workers; when you want Unix-style composability through pipes, scripts, and logs; when sessions are long, non-interactive, or automation-driven; when the autonomy target is L5 with evidence in stdout and exit codes; or when IDE installation is impractical or policy-blocked.

The form factors are complements. Many engineers use Copilot or Cursor for daily edits and a terminal agent for SSH sessions or batch refactors. The mistake is assuming one surface covers every authority level Module 1.1 describes.

---

## Configuring Permission Gates in IDE Agents

IDE harnesses expose permission gates that are easy to overlook because the editor still feels like a familiar typing environment. In practice you are approving a bundle of capabilities: read access to workspace files, write access to paths inside or outside the repo, shell execution with or without prompts, network access for package installs or API calls, and browser control for localhost or arbitrary URLs. Mature teams document which gate settings are allowed on shared repositories versus disposable branches, because the same model behind two different policies produces radically different risk.

Start with terminal execution policy. Review mode means the agent proposes commands and waits for human approval — slower but appropriate for unfamiliar codebases, production-adjacent services, and onboarding exercises where the learner must see each command. More automatic modes can be acceptable on throwaway clones when the worst case is deleting a local folder, but they are a poor default when the workspace contains deployment keys, customer data fixtures, or monorepo siblings the agent was never asked to touch. Pair execution policy with explicit allow and deny lists: allow routine test and build commands your stack uses daily, deny destructive patterns and privilege escalation, and treat package-manager installs as a separate approval class because dependency changes outlive the chat session.

Browser gates deserve the same discipline. Agents that can open arbitrary URLs are vulnerable to prompt-injection via malicious pages and to accidental exfiltration if the page content becomes model context. Restricting automation to `localhost` and known staging hosts is a common pattern for login-flow exercises and UI smoke tests. File-creation gates matter because agents solve problems creatively: a missing credential for a local test can become a new `.env` file that never appears in the diff panel you focused on. Review `git status` after every agent session and treat new paths with the same suspicion as modified hunks.

Indexing and context scope are permission decisions too. A harness that indexes the entire monorepo may retrieve irrelevant or sensitive modules when you asked for a one-file fix. Naming directories and files in the task contract — the same discipline Module 1.1 recommends — reduces retrieval noise and prevents the agent from "helpfully" refactoring cousins of the module you cared about. If your harness supports rules files or project instructions, keep them under version control so the team shares boundaries instead of each developer improvising prompts.

Finally, separate **who pays** from **what runs**. A BYO API key in Cursor or Cline routes billing and data-policy questions to your cloud account; a Copilot seat routes them to GitHub's enterprise terms; Antigravity ties you to Google's stack and announced transition timelines. None of that is a quality judgment — it is a fit question. The harness you choose should make those boundaries visible before you grant L3 or L4 authority on a shared branch.

---

## Team Governance Without Tool Sprawl

Teams adopt IDE agents faster than they adopt shared rules, which creates invisible automation: each developer picks a fork or extension, uses a personal API key, and merges agent-generated patches that reviewers cannot distinguish from hand-written code. Governance does not require banning agents; it requires making their use legible in code review and incident response.

A lightweight policy can fit on one page. Name approved harness classes for each repository tier: autocomplete-only on regulated services, IDE agents with review-mode terminals on product repos, parallel agents only on feature branches or prototypes. Require a task contract in the ticket or PR description — scope files, forbidden changes, success command — so reviewers can tell whether the agent stayed inside bounds. Store evaluation notes when pilots finish, using the three-pass read-only, narrow-edit, and recovery-test sequence from Module 1.1.

Reviewers should ask agent-specific questions during pull request review: Does this patch match the stated contract? Are tests asserting real behavior or encoding the agent's guess? Did any new files appear? Does the transcript or artifact explain a design choice that looks unusual? Teaching reviews — where a senior engineer walks through an agent-generated change with the author — reduce understanding debt without pretending agents are forbidden.

Cost governance belongs in the same conversation. IDE subscriptions, API metered usage, and parallel background agents can spike when developers delegate large refactors without scoping. Track spend by workflow type, not by moral panic: a team that spends credits fixing tests with evidence may be healthier than a team that saves credits but merges unreviewed megadiffs. Rotate a boring benchmark task quarterly and re-run it after major harness upgrades; model and permission defaults change behavior even when the product name stays the same.

---

## Artifacts, Checkpoints, and the Trust Gap

When agents edit one file, diff review scales. When agents edit twenty files, run commands, and browse localhost, diff-only review breaks down. IDE harnesses therefore export artifacts: implementation plans, task checklists, patch summaries, terminal transcripts, screenshots, and verification notes. Treat these as first-class review inputs alongside `git diff`.

A practical artifact review order: read the plan and confirm scope matches your ticket; scan the file list for paths you did not expect; read the diff or patch summary for risky areas such as auth, payments, and schema migrations; run the verification commands the agent recorded or your own targeted tests; run `git status` for new files the diff view might not highlight. Skipping artifacts is how credential files and test fixtures slip into commits while the developer only reviewed the "main" code hunks.

---

## Worked Example: Fit-Based IDE Choice

Hypothetical scenario: you must add a profile endpoint to an existing TypeScript API with strict style conventions, no new dependencies, and a mandatory integration test. Parallel agents are unnecessary; reviewability and pattern matching matter most.

**Contract:** edit only `src/routes/users.ts`, `src/services/profile.ts`, and `tests/profile.test.ts`; preserve error response shapes; success is `npm test -- profile.test.ts`. **Copilot** fits L0–L2 assistance if you drive the edits. **Cursor** fits L2–L3 if you want indexed context and diff review in one fork. **Antigravity** is heavier than needed unless you also want browser screenshots of a local demo. **Cline** fits if policy requires stock VS Code with per-command approval. **Windsurf** fits if you expect several iterative test failures and want session memory across attempts. End with a fit statement, not a universal winner.

---

## The History of AI-Powered Development Environments

Early smart environments were compilers and analyzers: syntax highlighting, symbol navigation, and refactor tools on parsed ASTs rather than neural networks. Microsoft's IntelliSense (1996) established the expectation that editors should predict what you might type next from structure. Research on the naturalness of code ([Hindle et al., 2012](https://cacm.acm.org/research/on-the-naturalness-of-software/)) motivated statistical and neural completion through the 2010s.

[GitHub Copilot](https://github.com/features/copilot) (2021) brought neural completion to mainstream editors at scale but remained reactive — suggestions followed your cursor without planning loops or tool use. Integrations such as Cursor and Copilot Chat (2023–2024) moved L1 conversation beside the buffer, but shallow session memory and limited execution evidence remained bottlenecks. Current IDE agents add planning, tool use, memory, multi-file edits, and artifacts — shifting from "predict the next line" to "execute a bounded engineering task and show evidence," still reviewed in the editor.

The history lesson for practitioners is conservative: every wave reused the previous editor shell while changing authority. IntelliSense did not replace typing; it assisted it. Copilot did not replace IntelliSense; it added probabilistic generation. Agent panels do not replace diffs; they add delegation with artifacts. Teams that align review habits with the current authority level adopt new tools without surprise incidents, while teams that stay mentally at L0 while operating at L3 accumulate understanding debt and security debt in equal measure.

---

## Connecting to Module 1.1 and Module 1.5

Module 1.1 gives you the Rosetta Stone for authority across autocomplete, chat, IDE agents, terminal agents, and connected tools. This module is not a duplicate of that map — it is a magnifying glass on the IDE column. When you evaluate Copilot versus Cursor versus Antigravity, you are still answering Module 1.1 questions: what can it read, what can it write, what can it execute, what evidence does it return, and who pays for the data path. The IDE form factor simply makes those questions feel more comfortable because the violations show up as diffs in a familiar buffer.

Module 1.5 covers the CLI and headless column where L5 autonomy, log streams, and composability dominate. Many production incidents happen where GUIs are absent, which is why the curriculum treats IDE and CLI form factors as partners. Choose IDE-integrated agents when visual review and tight edit loops are the bottleneck; choose CLI agents when the environment is remote, non-interactive, or script-driven. Returning to Module 1.1 after trying both form factors helps you articulate a starter stack instead of a pile of subscriptions.

---

## Hypothetical Scenario: Failure Modes in IDE Agents

> **Hypothetical scenario** — composite illustration of real failure patterns; not a specific company or incident.

A developer asks an IDE agent to "add OAuth login." The agent modifies several files and reports success. The developer reviews the code diff in the editor but does not notice a new `.env.local` the agent created for testing. The file is not covered by an ignore rule; credentials are committed. Failure modes: over-delegation from vague scope; artifact blind spot from reviewing only highlighted diffs; permission defaults that auto-approved file creation. Mitigations: name files and boundaries in the task contract; review `git status` and new paths; use review-mode execution policies; treat artifact bundles as mandatory review inputs.

---

## Evaluating IDE Agents on Your Repository

Before standardizing on any IDE-integrated harness, run the same three-pass evaluation Module 1.1 describes, adapted to the editor context. Pass one is read-only grounding: ask the tool to locate where a specific invariant is enforced — authorization on one route, retry limits in a config file, or the fixture that creates a disabled test account — and require file paths in the answer. Pass two is a narrow edit with a written contract naming allowed files, forbidden files, and the single success command. Pass three is recovery: introduce or use an existing failing test, let the agent attempt a fix, and observe whether it interprets stderr without widening scope to unrelated modules.

Record results in engineering language, not enthusiasm. "Composer produced a three-file diff that passed `npm test -- users` but invented a helper not used elsewhere" is actionable. "Felt smart" is not. Note whether the harness respected review mode for terminal commands, whether artifacts matched the final diff, and whether session memory helped on pass three or the agent repeated a rejected approach. If a product passes pass one and two on a toy repo but fails pass three on your real tree, approve it for explanation and boilerplate only until recovery improves.

Pay attention to data path during evaluation. Indexing that uploads embeddings to a vendor cloud may be acceptable on public samples and unacceptable on private monorepos. BYO-key extensions route prompts to whichever account you configure — which can be a feature for billing control or an accident if the key is personal while the code is employer-owned. Copilot seats route through GitHub's policies; Antigravity routes through Google's announced stack transitions. Fit is constraint satisfaction, not a scoreboard.

Finally, rehearse rollback. IDE agents make editing feel reversible because Git is right there, yet agents can run commands that mutate state outside Git — databases, local caches, global package installs, browser sessions with cookies. Your evaluation should include whether the harness logs commands clearly enough to undo side effects. A tool that excels at diffs but obscures shell history fails the evidence loop Module 1.1 emphasizes even if the model is strong.

When the evaluation finishes, write two fit statements: one task this harness may handle next sprint, and one task it may not handle yet. Share those notes with reviewers so pull requests carry expectations about how the branch was produced. That single habit prevents the common failure mode where reviewers treat agent-generated patches as if they were typed line-by-line and apply the wrong review depth.

### Editor as System of Record: What Stays Human-Owned

Even in agent-first workflows, certain artifacts remain human-owned because they encode judgment rather than implementation. Architecture diagrams that commit to coupling boundaries, threat models for auth flows, naming conventions for public APIs, and rollback plans for migrations are poor candidates for full delegation regardless of how polished the IDE panel looks. Agents excel at filling in implementations once those boundaries exist; they are weaker at deciding which boundaries should exist in the first place. Teams that confuse fast implementation with fast architecture often pay interest during the next incident, when nobody can explain why the agent chose a pattern that contradicts the rest of the service.

The editor reinforces human ownership when you keep using it the way senior reviewers expect: blame-aware Git history, meaningful commit messages that describe intent, and PR descriptions that link to tickets. If the agent wrote eighty percent of the lines but you approved the plan and the scope, your name on the merge still means you vouch for the change. IDE integrations that hide command output or squash every intermediate commit can make that accountability harder, so prefer harness settings that preserve inspectable steps unless you have another audit trail.

Finally, treat the IDE as a teaching surface for junior engineers even when agents are available. Reading diffs, stepping through tests, and comparing the agent's plan to the ticket are skills that remain valuable when the model vendor changes next quarter. The form factor lasts because editing is still how most software teams reconcile intent with reality — agents just moved the frontier of what "editing" can mean from keystrokes to delegation, artifacts, and review.

Pause and predict: if your team disabled all agent panels tomorrow but kept Git, tests, and code review, which parts of your delivery would slow down first — typing speed, multi-file refactors, or architectural decisions? Teams that answer "typing speed" are good candidates for stronger autocomplete; teams that answer "multi-file refactors with evidence" are asking for IDE agents with tight harnesses; teams that answer "architecture" need human-led design before any delegation tier. Write your answer in one sentence and compare it with Module 1.1's authority worksheet — the overlap tells you which IDE or CLI form factor to pilot first on your repository.

---

## Key Takeaways

1. IDE-integrated agents keep the editor as system of record while expanding authority from L0 completion through L4 parallel work.
2. Harness ⟂ model — evaluate permissions, artifacts, and data paths separately from model intelligence.
3. Peers, not rankings — Copilot, Cursor, Antigravity, Windsurf, and Cline illustrate different fits; end comparisons with constraint-based fit statements.
4. Artifacts exist for trust — review plans and file lists, not only the final diff.
5. IDE vs CLI — visual review and daily editing favor the IDE; automation, remote hosts, and L5 loops favor CLI (Module 1.5).
6. Scope tasks like tickets — vague delegation produces vague, risky code.
7. Security follows the harness — execution policies and new-file review matter as much as model choice.
8. Volatile details expire — snapshot product facts and re-verify on official docs.

---

## Did You Know?

- IDE agents expose adjustable autonomy — approval per command, per session, or per risk class — because unrestricted tool use in a shared repo fails quickly in practice.
- Artifacts (plans, recordings, checklists) exist because diff-only review does not scale when agents touch dozens of files; the harness exports narrative evidence on purpose.
- Open-source extensions like Cline prove that the IDE form factor does not require a proprietary fork — only a host editor, a panel, and disciplined permissions.
- Background and parallel agents (L4) reintroduce coordination cost: someone must merge concurrent changes and resolve conflicts humans did not see being introduced.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating IDE agents as autocomplete | The UI feels familiar so authority creep goes unnoticed | Map each session to an L0–L5 level and match review depth to that level |
| Choosing by model name only | Marketing emphasizes models, not harness permissions | Evaluate context scope, execution policy, and artifacts on a benchmark task |
| Over-delegating with vague prompts | Natural language feels fast | Write contracts with files, forbidden changes, and success commands |
| Reviewing diffs but not new files | Diff UIs highlight edits, not always creates | Run `git status` and scan artifact file lists before merge |
| Ignoring artifacts | Developers want to ship quickly | Review plan, verification output, and command logs first |
| Setting fully automatic terminal policy on sensitive repos | Speed is tempting on trusted-looking code | Use review mode with allow/deny lists until the harness earns trust |
| Ranking peers instead of fitting tasks | Blog posts declare winners | End with fit statements tied to constraints from Module 1.1 |

## Quiz

**Q1.** Your team needs three independent pieces this afternoon: a small API backend, a frontend shell, and integration tests — ideally monitored from one IDE session with parallel progress. Which capability pattern fits best, and which peer primarily illustrates it?

<details>
<summary>Answer</summary>
L4 parallel or manager-surface delegation fits best. Google Antigravity primarily illustrates multi-agent orchestration with a manager-style UI and rich artifacts. Cursor background agents can approach this pattern with different UX; Cline does not center parallel agents. State fit in terms of capability, not brand loyalty.
</details>

**Q2.** An agent returns OAuth-related changes across several files. Your lead wants the fastest trust check before deep code review. What should you open first?

<details>
<summary>Answer</summary>
Review artifacts first when available: implementation_plan.md, task checklist, code_diff or per-file diffs, test or verification reports, and screenshots. Also run `git status` for new files the diff view might not highlight.
</details>

**Q3.** During debugging you say "that fix failed" and want the assistant to recall terminal errors and prior attempts. Which durable concept matters most, and which peer emphasizes it?

<details>
<summary>Answer</summary>
Session memory beyond raw chat text — structured recall of attempts, terminal output, and rejections. Windsurf Flows emphasizes this in Cascade. Match the tool to continuity requirements rather than assuming all chat panels are equal.
</details>

**Q4.** Policy requires stock VS Code, open-source harness, optional local models, and per-action approval. Which peer fits, and what is the tradeoff?

<details>
<summary>Answer</summary>
Cline fits: VS Code extension, Apache-licensed harness, BYO and Ollama-local providers, explicit approve/reject on edits and commands. Tradeoff: slower iteration on greenfield work than more autonomous defaults.
</details>

**Q5.** On a large codebase you need small incremental changes with strong pattern matching and readable diffs — not five autonomous agents. Which peer's design center aligns, and why?

<details>
<summary>Answer</summary>
Cursor centers diff-centric, codebase-indexed multi-file edits with review in the IDE fork. That fits established repos where consistency and reviewability dominate. Antigravity's manager surface fits better when parallelization is the primary goal.
</details>

**Q6.** An engineer enables fully automatic terminal execution on a sensitive repo. What safer configuration reduces risk, and what failures does it target?

<details>
<summary>Answer</summary>
Use review-mode execution with explicit allow/deny lists (block destructive commands and unrestricted browser access). This reduces unreviewed credential file creation, destructive shell commands, and prompt-injection via browsed content.
</details>

**Q7.** Hypothetical: a developer ships a feature quickly with an IDE agent but struggles for days debugging session logic they never internalized. What concept does this illustrate, and what practice helps?

<details>
<summary>Answer</summary>
Understanding debt — output outran comprehension. Mitigations: smaller scoped tasks, mandatory self-explanation before merge, senior walkthrough of agent-generated patches, and keeping security-critical paths human-authored.
</details>

**Q8.** Inline ghost-text at the cursor is autocomplete-first behavior at which autonomy level (L0–L5), and a manager surface running three concurrent agents is agent-first behavior closest to which level? Why must review depth differ? A teammate says the newest frontier model makes IDE agents safe — which harness ⟂ model controls matter more?

<details>
<summary>Answer</summary>
Autocomplete-first inline ghost-text is L0; agent-first parallel manager surfaces are L4. Review depth must scale: L0 needs local accept/reject, while L4 needs artifact streams, merge coordination, and new-file checks. Harness ⟂ model refutes model-only safety — terminal review mode with deny lists and mandatory artifact plus `git status` review matter more than model vintage.
</details>

## Hands-On Exercises

These exercises teach form-factor skills that transfer across products. Use whichever IDE-integrated tool you have access to; substitute peers with equivalent capabilities where noted.

### Exercise 1: Parallel Task Delegation (Antigravity or equivalent)

*Illustrative lead tool: Google Antigravity — any product with parallel agent or background-task support can substitute.*

Build a minimal task-manager slice with three independent workstreams (backend API, frontend shell, integration tests) using parallel agents or background tasks. Launch three concurrent agent tasks, observe how the tool surfaces status per stream, collect artifacts from each (plans, diffs, test output), and merge into one runnable project locally only after you have reviewed every artifact stream.

- [ ] All three streams produce reviewable artifacts before merge
- [ ] Application runs locally with create/list working
- [ ] You can explain one change you rejected and why

### Exercise 2: Local Model via Cline (or BYO extension)

Run an IDE agent offline on a small change to experience harness ⟂ model separation: install Ollama or your org-approved local runtime, pull a coding model with `ollama pull deepseek-coder:6.7b`, configure Cline or another BYO-capable extension to use the local endpoint, and task the agent to add input validation to a toy form component while approving each action explicitly.

- [ ] No cloud API calls during the session if policy requires offline work
- [ ] Agent proposes a diff; you approve explicitly
- [ ] You record latency and quality tradeoffs versus a hosted frontier model

### Exercise 3: Browser Automation Comparison

Compare how IDE peers handle the same login smoke test on localhost by running a trivial login flow, executing the test in two or three tools with browser control (for example Antigravity, Cline, Windsurf), and documenting setup steps, selector reliability, and screenshot quality using fit statements rather than a ranked winner.

- [ ] Written comparison ending in fit statements per tool
- [ ] Notes on URL allowlisting and credential handling
- [ ] At least one failure mode observed and explained

---

## Learner check

Before moving on, confirm you can explain the IDE form factor in your own words. The core idea:

> The IDE-integrated form factor keeps the editor as the system of record while the agent proposes multi-file changes, runs tools under permission gates, and leaves artifacts you review before anything ships.

---

## Next Module

Continue to [Module 1.5: CLI AI Coding Agents](/ai-ml-engineering/ai-native-development/module-1.5-cli-ai-coding-agents/) for terminal-based agents — the complement to IDE-integrated work when you need scriptable, headless, or remote-server autonomy.

---

_Last updated: 2026-06-07_

## Sources

- [An important update: Transitioning Gemini CLI to Antigravity CLI](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/) — Google's announcement on sunsetting individual-tier Gemini CLI / Code Assist and folding workflows into Antigravity (June 18, 2026).
- [Getting started with Google Antigravity codelab](https://codelabs.developers.google.com/getting-started-google-antigravity) — Official onboarding for Antigravity's manager surface, editor, and agent workflows.
- [Cursor documentation](https://docs.cursor.com) — Composer, agents, indexing, and model configuration.
- [Windsurf documentation](https://docs.codeium.com/windsurf) — Cascade, Flows, and agent features.
- [Cline GitHub repository](https://github.com/cline/cline) — Licensing, provider support, MCP, browser use, and approval model.
- [Cline documentation](https://docs.cline.bot/home) — Setup, configuration, and feature reference for the VS Code extension.
- [GitHub Copilot documentation](https://docs.github.com/en/copilot) — Editor integration, chat/agent features, and model options.
- [Visual Studio Code Copilot overview](https://code.visualstudio.com/docs/copilot/overview) — How Copilot integrates with the VS Code editing surface.
- [Responsible use of GitHub Copilot features](https://docs.github.com/en/copilot/responsible-use-of-github-copilot-features) — Governance and limitation guidance from GitHub.
- [Model Context Protocol introduction](https://modelcontextprotocol.io/docs/getting-started/intro) — Protocol background for Cline-style tool connectors.
- [On the Naturalness of Software](https://cacm.acm.org/research/on-the-naturalness-of-software/) — Hindle et al. (2012); background for statistical code completion research cited in the history section.
