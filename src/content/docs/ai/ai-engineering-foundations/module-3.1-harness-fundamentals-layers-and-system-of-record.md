---
title: "Harness Fundamentals — Layers and System of Record"
slug: ai/ai-engineering-foundations/module-3.1-harness-fundamentals-layers-and-system-of-record
sidebar:
  order: 31
---

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: ~50 minutes
>
> **Prerequisites**: [Module 2.4 Dynamic Context Orchestration](../module-2.4-dynamic-context-orchestration/), or equivalent comfort with session-level context management, tool-output budget decisions, and context-rot detection in multi-turn agent workflows.

---

## Learning Outcomes

By the end of this module, you will be able to:

- **Design** a three-tier harness classification for a multi-repository team and justify why each rule belongs in its assigned tier rather than one level up or down.
- **Evaluate** whether a team's current instruction regime is operating as a System of Record or as an ungoverned advice surface, using concrete evidence from the repository layout and agent failure traces.
- **Compare** AGENTS.md and CLAUDE.md as control artifacts against prompt-level instruction files, naming the operational guarantees that control artifacts provide and prompt files cannot.
- **Diagnose** a semantic-ambiguity failure in an agent task loop and redesign the anchor path so the first 30 seconds of agent boot resolve to a deterministic policy source.

## Why This Module Matters

Hypothetical scenario: a platform team of twelve engineers operates across six repositories with a shared agent gateway. Every repository has an AGENTS.md file, a CLAUDE.md file, a docs directory, and a growing collection of prompt templates that individual engineers wrote after frustrating agent sessions. The team estimates they spend six engineer-hours per week debugging agent behavior that looks correct in the first five turns and then drifts — the agent edits generated files, ignores a recently added branch restriction, or applies a retired review checklist from a stale prompt template. Nobody disputes that the rules exist somewhere. The problem is that no single artifact can answer the question "which rule governs this task class and what happens when the rule is violated?"

This module is about making that question answerable. The tools you need are not new programming languages or orchestration frameworks. They are a three-tier classification scheme that assigns every rule to a platform, advisory, or enforcement layer, a System of Record discipline that keeps policy in one canonical location per domain, and a set of control-artifact conventions that reduce the time from agent boot to correct policy resolution to under 30 seconds. When these foundations are in place, the team's debugging time shifts from "find the right document" to "verify the right document was consulted," which is the difference between a reactive support queue and an engineered control surface.

The prompt layer taught you to define instruction interfaces that survive model upgrades and team handoffs. The context layer taught you to manage what an agent sees on each turn, how the repository speaks to the agent, and when session state becomes stale. The harness layer builds on both by making those interfaces enforceable. A prompt can tell an agent to follow a branch convention, but only a harness can prove that the convention was checked before the branch was pushed. A context layout can point the agent to the right policy file, but only a harness can detect when that file became stale and refuse to proceed until it is refreshed. This module is where good individual sessions become repeatable team systems, and where the engineering discipline shifts from persuasion to proof.

## The Three-Tier Harness Model in Operation

Module 2.1 introduced the three-tier classification — platform defaults, project advisory, project enforcement — as a taxonomy for assigning every governance rule to a layer with explicit ownership. This module deepens that classification by examining what each layer does during an agent session, not just what it contains.

When an agent boots into a fresh session, the platform runtime layer is already active before any repository file is loaded. The agent's model family, sandboxing mode, network access grants, and timeout envelope are set by the gateway operator, not by any instruction in the repository. The agent cannot read a platform rule, decide it is inconvenient, and ignore it, because the rule is not expressed as prose — it is a capability boundary enforced by the execution environment. If the sandbox mode is read-only, no AGENTS.md instruction can grant write access. If the network is firewalled to internal services only, no policy file can open an outbound connection. Platform rules are the only tier where compliance is guaranteed by the runtime rather than asserted by the repository.

Project advisory rules operate differently. They live in the repository as discoverable files, and every agent session can read them, but when a session violates an advisory rule, nothing mechanical stops the workflow. The agent moves forward, the commit lands, the PR opens, and the violation becomes visible only if a human reviewer notices it during code review. Advisory rules succeed when they reduce the cognitive overhead of repeated style decisions — the agent does not need to decide whether to use snake_case or camelCase because the advisory document already answered the question. They fail when the team relies on an advisory rule to prevent a class of error that demands mechanical enforcement, such as secret leakage or branch protection, and then treats the agent as if it violated a hard constraint when no constraint existed.

The most expensive failure mode in the three-tier model is the misclassified boundary: a rule written as advisory prose that the team treats as enforceable, or a rule enforced by a pre-commit hook that produces a generic error without a remediation path. In the first case, the team experiences repeated violations and blames the agent for ignoring a rule that had no mechanical teeth. In the second, the agent hits a gate, cannot determine how to satisfy it, and either deadlocks or takes destructive actions to clear the block. Both failures are misclassification failures, not agent failures — the rule was placed in the wrong tier or implemented with the wrong failure contract.

The diagnostic pattern for auditing an existing repository is to evaluate each rule against three questions: where is this rule written, what happens when it is violated, and who is responsible for noticing the violation. A rule written in a CONTRIBUTING.md file with no CI enforcement and no owner assigned for violation detection is operating in an ambiguous advisory tier — it cost time to write but delivers none of the benefits of either advisory (low overhead) or enforcement (mechanical certainty). A rule enforced by a CI gate that runs only on pull requests against main but not on every push leaves a gap that an agent working on a long-running feature branch can exploit unintentionally.

The three-tier classification is valuable not because it demands that every rule graduate to enforcement, but because it forces the team to make the placement decision consciously and revisit it when the operational environment changes.

**Pause and predict:** Your team maintains a rule that every pull request must include a test for the changed behavior. Today this rule lives in a CONTRIBUTING.md file, and the CI pipeline does not enforce it. Three of the last ten merged PRs skipped tests, and the team spends Thursday afternoons writing retroactive coverage. Before reading further, decide: does this rule belong in advisory or enforcement, and what single script would you add to make the transition?

## The Repository as System of Record: Enforcement Mechanisms

Module 2.1 established the principle: the repository is the single authoritative source for every policy that governs agent behavior, and every other surface is either a cached copy or an unofficial interpretation. This module adds the enforcement mechanisms that make that principle mechanically verifiable.

The operational question is not "where should policy live?" but "how does the system prove that the agent read the correct policy before it acted?" Three mechanisms answer this question in sequence. First, the AGENTS.md pointer graph provides a single entry path to every policy file. When an agent follows a pointer from AGENTS.md to `docs/harness/policy/deploy.md`, the traversal produces an audit trail that a reviewer can replay: the agent read AGENTS.md, resolved the deploy task class to its policy file, and loaded the policy file before executing deployment commands. This guarantee is filesystem-level, not natural-language — the agent either opened the file at the declared path or it did not, and the session log records which path was resolved.

Second, enforcement scripts close the loop between policy declaration and policy verification. A policy file that says "every deployment must declare the target environment" is an advisory statement. The same policy with a `deploy-guard.sh` script that greps the commit message for `env: staging` or `env: production` and exits non-zero when neither appears is an enforcement mechanism. The script transforms the policy from a document that the agent might read into a gate that the agent must pass, and the pass/fail output becomes part of the session log that a reviewer can inspect.

Third, pre-commit hooks and CI gates extend enforcement to the code-integration boundary. A policy that lives only in a markdown file can be bypassed by an agent that never reads the file, or by a human who edits directly on the platform. A policy enforced by a pre-commit hook blocks the commit before it enters the repository's history, and a policy enforced by a CI gate blocks the merge before it reaches the protected branch. These mechanisms are not add-ons to the System of Record discipline — they are what convert the discipline from a documentation convention into an operational guarantee.

The SoR discipline also changes how teams update policy. In the pre-SoR model, policy changes propagate through chat messages, wiki edits, and standup announcements, reaching different team members at different times and leaving agents with no single source to consult at boot. In the SoR model, policy changes land through pull requests against the repository, which means they are reviewed, versioned, revertible, and automatically discoverable by every subsequent agent session. The overhead is higher for small changes — opening a PR takes longer than sending a message — but the reliability gain compounds across sessions, because every session reads the same policy from the same canonical path rather than reconstructing it from scattered, conflicting, or outdated signals.

This principle belongs in the harness layer rather than the context layer because it is an enforcement concern. Module 2.2 taught you how to structure a repository so agents can discover context quickly and avoid stale guidance. That was about the format and discoverability of instruction surfaces. The System of Record concept taught here is about the authority of those surfaces: when an agent loads a policy from the repository, the system can now assert that this policy is the canonical version, that no other policy file contradicts it, and that any deviation from this policy is a violation that the enforcement tier can detect. The SoR is what turns a well-structured repository into a governed repository.

**Pause and predict:** Your team's deployment checklist lives in three places: a Notion page, a pinned Slack message, and docs/runbooks/deploy.md. The Notion page was last updated in March, the Slack message links to an older version of the Notion page, and docs/runbooks/deploy.md was updated last week but nobody announced it. An agent is about to execute a deployment. If the agent discovers all three sources, which one should it trust, and what single change to the repository would prevent this ambiguity from recurring?

## AGENTS.md and CLAUDE.md as Control Artifacts

Module 2.2 introduced AGENTS.md and CLAUDE.md as paired contract layers for repository engineering. It explained how AGENTS.md serves as a table of contents and entry point while CLAUDE.md provides scoped behavioral rules. That framing is correct for context engineering, where the goal is to help an agent discover and load the right instruction surface. The harness layer adds a second, higher-stakes question: what operational guarantees do these files provide that a plain prompt file cannot?

A control artifact differs from a prose instruction file in three ways. First, a control artifact is machine-parsed as part of the agent's boot sequence, not loaded as free-text context after the agent has already begun exploring the repository. This means the agent's first action is to read the control artifact and establish its policy surface, rather than to start exploring files and discovering policy opportunistically. Second, a control artifact declares rule provenance — it tells the agent not just what the rules are, but where each rule lives in the repository and what tier it belongs to. Third, a control artifact can be validated by a pre-flight check before any task work begins. If the artifact references a policy file that doesn't exist, the agent can abort before wasting turns on a broken map.

Consider a concrete difference. A prose instruction file might say: "Always run tests before opening a PR, and never commit to main directly." An agent reads this instruction, understands it, and may follow it most of the time. But when the task is urgent, when the context window is full, or when the agent encounters an unfamiliar code path, the instruction competes for attention with every other sentence in the context window and may be overridden by a more recently loaded or more emphatically worded instruction. A control artifact, by contrast, encodes the same rule as a pointer: "Test requirement: enforced by scripts/pre-commit-tests.sh, documented in docs/harness/policy/tests.md." The agent doesn't need to remember the rule from a prose paragraph. It invokes the script, reads the deterministic pass/fail output, and either proceeds or stops with a specific remediation link. The instruction is no longer a string in the context window. It is a gate in the execution path.

This shift from prose to pointer is what makes a control artifact different from a conventional documentation file. AGENTS.md and CLAUDE.md are not reference manuals that the agent reads cover to cover and then tries to apply from memory during the task. They are launch-time resolvers: the agent reads them first, follows the pointer graph to the specific policy files relevant to the current task class, and then executes against those files while the rest of the documentation tree stays unloaded. This keeps the context window lean — the agent carries the policy surface it needs rather than the entire repository's governance handbook — and it makes policy violations traceable because the reviewer can see exactly which pointer path the agent followed.

The pointer graph benefits from a deliberately boring format. Rather than rich formatting, embedded diagrams, or natural-language persuasion, a control artifact benefits from a simple key-value or section-header layout where each rule maps to a file path, an enforcement tier, and a failure remediation link. The agent does not need to be persuaded to follow the rule. It needs to be shown where the rule lives and what to do when the rule blocks progress. The file format that best supports this pattern is static Markdown with section anchors, because every agent runtime can resolve a Markdown link, every CI system can validate that a Markdown file exists at the referenced path, and every human reviewer can read the same artifact without specialized tooling.

```text
+-----------------------------+
| AGENTS.md (control artifact)|
+-----------------------------+
| ## Task Classes             |
| - bug-fix -> docs/harness/  |
|   policy/bug-fix.md         |
| - deploy  -> docs/harness/  |
|   policy/deploy.md          |
| - feature -> docs/harness/  |
|   policy/feature.md         |
+-----------------------------+
            |
            v
+-----------------------------+
| docs/harness/policy/        |
|   bug-fix.md                |
+-----------------------------+
| ## Pre-flight checks        |
| - scripts/pre-commit-tests  |
| - scripts/branch-guard.sh   |
| ## Enforcement tier         |
| Both checks are enforcement |
| ## Remediation              |
| See docs/runbooks/tests.md  |
+-----------------------------+
            |
            v
+-----------------------------+
| scripts/pre-commit-tests.sh |
| (deterministic pass/fail)   |
+-----------------------------+
```

This architecture is not a new invention. It is the same pattern that build systems, package managers, and configuration management tools have used for decades — a root manifest that declares what exists, where it lives, and what depends on what — applied to the domain of agent governance. The pattern works because it is boring enough to be mechanically verifiable, and the mechanical verifiability is what makes it enforceable across hundreds of agent sessions without human oversight.

## Progressive Disclosure and Anchored Path Resolution

Module 2.2 covered progressive disclosure as a repository engineering technique: structure documentation so that agents encounter the most important information first, and drill into detail only when the task requires it. That framing emphasizes the "disclosure" side of the pattern — what the agent sees and when. The harness layer adds the "progressive" side — how the agent resolves ambiguity at each step, and how the resolution path is anchored to prevent drift.

Anchored path resolution means that every level of the disclosure tree resolves to a file path, not to a topic description. A topic description says "see the deployment policy" — an instruction that requires the agent to search for a file matching that description, interpret multiple candidate files, and decide which one is authoritative. A file path says "see docs/harness/policy/deploy.md" — an instruction that resolves in one filesystem operation and produces exactly one result. The difference in latency is small for a human reading documentation, but it compounds across agent sessions because every unresolved topic description adds a search step, and every search step adds an opportunity for the agent to load the wrong file, interpret the wrong section, or miss a recently added policy that the search index hasn't indexed yet.

The anchor chain for a task class follows a predictable shape. The root AGENTS.md declares the task class and its policy file. The policy file declares the enforcement checks, the advisory guidelines, and the remediation documents. The enforcement scripts produce pass/fail output with a specific exit code. The remediation documents describe the fix path when enforcement fails. At no point in this chain does the agent need to search the repository, because every step resolves to a file path that was declared at the previous step. The chain can be verified mechanically: a simple script can walk the anchor graph from AGENTS.md through every referenced policy file and enforcement script, confirm that every referenced file exists, and report any broken links before an agent ever tries to follow them.

Progressive disclosure in a harness context also means that policy files should be structured so the agent reads the enforcement rules first — because those are the rules that can block progress — and the advisory guidelines second. This ordering is the opposite of most human-facing documentation, which typically starts with context and principles before getting to concrete rules. The reversal is justified because an agent's task loop is more like a compiler pass than a human reading experience. The agent needs to know what will cause a build failure before it starts building, just as a compiler checks syntax before it generates code. If the enforcement rules are buried at the bottom of a long policy file, the agent may begin work, make commits, and only then discover that a pre-commit hook blocks the path — wasting turns and context window budget on work that the policy file could have prevented.

The simplest anchored path is a three-level tree that any CI system can validate. Level one is the AGENTS.md task-class map. Level two is the per-task-class policy files that reference enforcement scripts by path. Level three is the enforcement scripts themselves, which exit zero on pass and non-zero on fail with a stderr message that includes the remediation document path. This tree is flat enough that agents never need to traverse more than three hops to reach a deterministic gate, and structured enough that any broken reference produces a CI failure before the agent session begins.

```text
AGENTS.md
  |
  +---> docs/harness/policy/bug-fix.md
  |       |
  |       +---> scripts/pre-commit-tests.sh     (enforcement)
  |       +---> scripts/branch-guard.sh         (enforcement)
  |       +---> docs/harness/advisory/style.md  (advisory)
  |
  +---> docs/harness/policy/deploy.md
  |       |
  |       +---> scripts/deploy-guard.sh         (enforcement)
  |       +---> scripts/canary-approval.sh      (enforcement)
  |
  +---> docs/harness/policy/feature.md
          |
          +---> scripts/feature-branch-naming.sh (enforcement)
          +---> docs/harness/advisory/review.md  (advisory)
```

This three-level anchored tree is the practical implementation of the "map, not manual" principle that the original harness-engineering guidance recommends. The map is the AGENTS.md task-class index. The manual — if it exists at all — is the set of advisory documents that agents load only after the enforcement path has been satisfied. The distinction matters because a map works in the first 30 seconds of agent boot, while a manual requires the agent to read, interpret, and prioritize potentially hundreds of paragraphs before it can take any action.

## Limitations of Prompt-Level Instructions Across Fleets

A fleet of agents — multiple independent agent sessions running against the same repository, either concurrently or in sequence — exposes a failure mode that single-session workflows rarely encounter. When each agent receives its instructions through a prompt template, every session carries its own copy of the rules. If the rules change between sessions, the copies diverge. If one agent's prompt template is edited without updating the others, the fleet operates under different assumptions. If the prompt template is versioned in a separate system from the repository, the version mapping becomes another failure point that nobody owns.

Prompt-level instructions are not inherently wrong. A prompt can express a task contract, a reasoning pattern, and an output schema with precision, as the prompt layer modules demonstrated. The limitation appears when the instruction is not the task contract but the governance contract — the set of rules that should apply uniformly to every session regardless of which engineer initiated it, which model variant is running, or which task class is in scope. Governance contracts need to be read from a single source at run time, not baked into a prompt that was authored days or weeks earlier and may have missed a policy update that landed yesterday.

The operational difference is easiest to see at scale. When a team of twelve engineers maintains prompt templates across six repositories, and each template includes a copy of the branch-naming convention, the test-coverage threshold, and the secret-scanning policy, a policy change requires editing six templates and hoping that no engineer misses one. When the same policy lives in a single repository file referenced by AGENTS.md, a policy change requires one edit, and every subsequent agent session — running any prompt template, on any task class, initiated by any engineer — reads the updated policy before it begins work. The difference is not philosophical. It is the difference between a policy update that takes one pull request and one review cycle, and a policy update that takes six pull requests, six review cycles, and an unknown number of stale sessions running against the old policy until the templates are all updated.

This scaling problem also affects review quality. When a reviewer examines an agent's output and needs to verify that the agent followed the deployment policy, the reviewer should be able to check a single source — the policy file in the repository — rather than reconstruct which prompt template the agent received and whether that template contained a current or stale copy of the policy. The System of Record discipline from the previous section addresses this directly: if the policy is in the repository and the agent's task log shows that it read the policy file, the reviewer has a complete audit trail. If the policy was baked into a prompt, the reviewer cannot distinguish between an agent that followed an outdated policy and an agent that ignored the current policy.

The remedy is not to eliminate prompt templates. Task-specific instructions — what to build, how to approach the problem, what output format to return — still belong in prompts because they vary by task class. The remedy is to separate the governance surface from the task surface. The governance surface lives in the repository's harness layer and is loaded by every agent session before any task-specific prompt is evaluated. The task surface lives in the prompt template or the issue description and varies by task. The separation creates a clean contract: the platform runtime loads the governance surface from the repository's System of Record, the agent applies the governance rules to the task surface, and the enforcement tier verifies the result. No policy is ever duplicated between the governance surface and the task surface, which means no policy update can be missed because it was buried in a template that nobody remembered to edit.

```text
+---------------------------+       +---------------------------+
| GOVERNANCE SURFACE        |       | TASK SURFACE              |
| (loaded at agent boot)    |       | (varies by issue/task)    |
+---------------------------+       +---------------------------+
| AGENTS.md                 |       | Issue description          |
| docs/harness/policy/*.md  |       | Prompt template            |
| scripts/*.sh (enforcement)|       | WORKFLOW.md spec          |
+---------------------------+       +---------------------------+
| Source: repository SoR    |       | Source: issue tracker or   |
| Authoritative, versioned  |       | prompt library             |
| Same for every session    |       | Varies by task class       |
+---------------------------+       +---------------------------+
            |                               |
            +---------------+---------------+
                            |
                            v
              +---------------------------+
              | AGENT RUNTIME             |
              | Governance loaded first,  |
              | then task context applied |
              +---------------------------+
```

## Boring-Tech Bias and Reducing Semantic Ambiguity

The engineering instinct when designing a harness is to build something sophisticated: a policy engine with a DSL, a rule database with a query interface, a plugin architecture for custom enforcement hooks, a dashboard for rule-compliance metrics. The instinct is understandable because sophisticated systems are interesting to build and rewarding to demonstrate. The instinct is also wrong for harness engineering, at least in the first iteration, because sophistication introduces semantic ambiguity — the gap between what a rule says and what an agent interprets — and every layer of abstraction widens that gap.

Boring-tech bias is the deliberate choice to implement harness controls using the simplest available tools: static Markdown files for policy declarations, shell scripts for enforcement gates, and filesystem paths for the resolution graph. These tools are boring in the best sense: they have well-defined semantics that every agent runtime understands, they produce deterministic output, they can be verified by CI systems without custom plugins, and they do not require the agent to learn a new DSL or interpret a novel configuration format.

When a shell script exits with code 1 and prints a message to stderr, every agent runtime — whether it is Claude Code, Codex CLI, Aider, or a custom Python wrapper — can parse the result and decide whether to proceed or remediate. When a Markdown file declares a policy with a link to an enforcement script, every agent runtime can follow the link and execute the script. The tools are boring enough to be interoperable, and interoperability across agent runtimes is what makes a harness valuable to a team that may switch models, tools, or platforms over the lifetime of the repository.

The semantic ambiguity problem is most acute in the first 30 seconds of an agent task loop. When an agent boots and begins exploring the repository, it must answer several questions before it can do useful work: what task class is this, which policy files govern this task class, which enforcement gates apply, and what is the order of operations for satisfying those gates. If the answers to these questions require interpreting natural-language descriptions, searching the file tree, or guessing which of several similar-looking policy files is authoritative, the agent spends its first turns building a mental model of the repository rather than executing the task. Worse, the mental model it builds may differ from the mental model that another agent built for the same repository four hours earlier, which means the fleet operates under inconsistent assumptions even though every agent read the same files.

Anchored path resolution, the three-tier model, and the pointer-graph architecture all serve the same goal: to reduce the semantic ambiguity of those first 30 seconds to zero, or as close to zero as a deterministic filesystem can provide. When an agent reads AGENTS.md and finds a task-class table that maps "bug-fix" to "docs/harness/policy/bug-fix.md," there is no ambiguity about which file to load. When the policy file lists enforcement scripts by path, there is no ambiguity about which script to run. When the script exits with a specific code and a specific remediation link, there is no ambiguity about what to do next. The agent's decision tree becomes a series of filesystem operations that produce deterministic results, and the human reviewer's audit trail becomes a series of "read this file, ran this script, got this result" entries that can be replayed and verified.

Boring-tech bias does not mean the harness must stay simple forever. A team that has operated a three-tier harness with static Markdown and shell scripts for several months may find that their enforcement checks have grown complex enough to justify a more structured format — a YAML-based rule registry, a policy-as-code framework, or a custom validation service with a REST API. The bias is about the starting point, not the ceiling. Start with tools that are boring enough to be mechanically verifiable by a curl call and a grep invocation. Graduate to more sophisticated tools only when the boring tools demonstrably cannot handle the complexity, and the sophistication buys a measurable reduction in failure rate or recovery time. Most teams will find that the boring tools handle 80 percent of their enforcement needs, and the remaining 20 percent can be addressed with a small number of purpose-built scripts rather than a general-purpose policy framework.

The graduation path from boring to sophisticated should be triggered by concrete evidence, not by engineering curiosity. Three signals justify moving a rule from a shell-script enforcement gate to a more structured implementation.

First, the rule's enforcement script has grown past 200 lines and the team can no longer reason about its correctness by reading the source. Second, the rule is enforced across more than five repositories and maintaining identical copies of the script in each repository has caused a drift incident where one repository ran a stale version. Third, the rule requires data from an external system — a ticketing API, a secrets manager, a compliance database — that a shell script cannot access reliably without complex credential management.

Any one of these signals is a reasonable trigger to evaluate a more structured implementation. Absent these signals, the boring implementation is the correct default, and the team's energy is better spent on improving the accuracy of the enforcement logic than on upgrading the tooling that runs it.

> **Active learning prompt:** Open a terminal in a repository you work with regularly. Time how long it takes you to answer the question "what are the branch-naming rules for this repository, and what happens if I break them?" If the answer took more than 30 seconds, or if you are not certain that your answer is correct, the repository does not yet have an anchored path for this governance question. Describe what single file you would add to reduce that time to under 10 seconds.

## Patterns and Anti-Patterns

### Patterns

| Pattern | When to Use | Why It Works |
|---|---|---|
| Three-tier classification | When a team has more than five rules that agents should follow | Assigns every rule an operational tier with explicit ownership, so the team knows which rules are enforceable, which are advisory, and which are out of their control |
| Pointer-graph architecture | When policy changes frequently or spans multiple domains | AGENTS.md becomes a launch-time resolver that loads only the policy files relevant to the current task, keeping the context window lean and the audit trail explicit |
| Separated governance and task surfaces | When a fleet of agents runs against the same repository concurrently | Governance rules load from one canonical location at agent boot, while task-specific instructions stay in the prompt, preventing policy drift across sessions |
| Pre-flight anchor validation | When a repository has three or more linked policy files | A CI script validates that every pointer in AGENTS.md resolves to an existing file before any agent session begins, catching broken references at merge time rather than at run time |
| Enforcement before advisory | When policy files contain both blocking and non-blocking rules | Loading enforcement rules first lets the agent discover what will block progress before it begins work, saving context budget and turn count |

### Anti-Patterns

| Anti-Pattern | Why Teams Fall Into It | Better Alternative |
|---|---|---|
| The policy monolith: all rules in one long AGENTS.md | AGENTS.md is the file every agent reads first, so teams add more to it until it becomes a 4,000-line instruction dump | Reserve AGENTS.md for the task-class map and pointer graph; move policy detail into per-domain files under docs/harness/policy/ |
| The advisory-only trap: every rule is advisory, nothing is enforced | Writing enforcement scripts is more work than writing prose rules, and teams defer the work until an incident forces it | Identify the three rules that would cause the most damage if violated, automate them first, and treat the rest as a backlog |
| Duplicated policy in prompt templates | Copying the branch convention into every prompt template feels like a quick win during the first week of agent adoption | Govern from the repository and task from the prompt; never duplicate a governance rule between surfaces |
| Semantic search for policy resolution | Relying on the agent to grep or vector-search for policy files creates non-deterministic resolution paths | Use anchored file paths in AGENTS.md so every policy reference resolves to exactly one file |
| Platform rules in repository files | Teams write AGENTS.md instructions like "agent must run in danger mode," which the platform runtime may override | Document platform rules in the platform's own configuration; keep repository files focused on what the repository controls |
| Stale advisory rules without expiry | A style rule written six months ago stays in the advisory tier even though the team no longer follows it | Add a reviewed-date field to every policy file and a CI check that flags files unreviewed for more than 90 days |

## Decision Framework

When you encounter a new rule that should govern agent behavior in your repository, use this framework to assign it to the correct tier and choose the correct implementation approach.

```text
                        New governance rule
                              |
                              v
              +-------------------------------+
              | Is this rule about the agent's |
              | execution environment?         |
              | (model, sandbox, network,      |
              |  tool access, timeouts)         |
              +-------------------------------+
                     |                |
                    Yes              No
                     |                |
                     v                v
              PLATFORM RUNTIME   +-------------------------------+
              Configure in the   | Does violating this rule      |
              platform, not the  | cause immediate and           |
              repository         | measurable harm?              |
                                 | (secrets leak, broken build,  |
                                 |  compliance violation,         |
                                 |  unreviewable change)          |
                                 +-------------------------------+
                                        |                |
                                       Yes              No
                                        |                |
                                        v                v
                                 PROJECT            PROJECT
                                 ENFORCEMENT        ADVISORY
                                        |                |
                                        v                v
                                 Implement as:     Document as:
                                 - pre-commit      - style guide
                                   hook            - recommended
                                 - CI gate           practice
                                 - deterministic   - team convention
                                   script          - review checklist
                                        |
                                        v
                                 +-------------------------------+
                                 | Add remediation doc path to  |
                                 | enforcement script's stderr  |
                                 | output and to AGENTS.md      |
                                 | pointer graph                |
                                 +-------------------------------+
```

The framework is deliberately coarse because most governance decisions do not require fine-grained analysis. The platform-runtime question is usually answered by the team running the agent gateway, not the team contributing to the repository. The harm question is the only binary that matters for the advisory-versus-enforcement split, and the answer is almost always clear: if you can name a specific damage that occurs when the rule is broken, and that damage is severe enough that you would want the workflow to stop rather than proceed, the rule belongs in enforcement.

A smaller set of rules sits on the boundary. A commit-message format convention, for example, might seem harmless to violate in a single commit, but the accumulated inconsistency across hundreds of commits makes changelog generation unreliable and release automation fragile. In cases like this, the rule can start in advisory — document the convention, ask agents to follow it — and graduate to enforcement after the team observes that advisory isn't working. The pattern to follow: measure the violation rate over a defined period (two weeks of agent sessions is a reasonable window), compare it to the team's tolerance, and promote to enforcement if the rate exceeds the tolerance. This data-driven promotion path prevents the most common harness failure mode, which is adding enforcement gates for rules that nobody was actually violating, creating friction that benefits nobody.

## Did You Know?

- Did You Know: OpenAI published its harness-engineering guidance in February 2026, and through 2026 the AGENTS.md convention — initially a community-driven pattern — was adopted as a first-class control surface across Codex CLI and a range of agent tools (Cursor, Amp, and others) and is now stewarded as an open, cross-tool format. Claude Code, by contrast, reads its own `CLAUDE.md` file rather than `AGENTS.md` natively (native AGENTS.md support remains an open community request) — so the two ecosystems converge on the same *idea* (a checked-in, machine-readable rules file) even where the filename and loader differ.

- Did You Know: Claude Code's `@` syntax is a file-import mechanism: writing `@.claude/rules/branches.md` inside a CLAUDE.md file inlines the entire contents of the referenced file into the CLAUDE.md context at agent boot time. The agent does not navigate to the referenced file at run time — it receives the inlined content as part of CLAUDE.md itself, which means the import chain is explicit, auditable, and version-controlled through the file that declares it. The `.claude/rules/` directory convention is a project-level organizational pattern (adopted by repositories including KubeDojo) where scoped rule files are imported by the project's CLAUDE.md through explicit `@` directives, rather than auto-loaded by the runtime.

- Did You Know: OpenAI's Model Spec (published September 2025, updated regularly) defines a formal hierarchy for instruction authority — platform instructions override developer instructions, and developer instructions override user instructions — a design that maps directly to the three-tier harness model described in this module, where platform rules sit above repository rules and repository enforcement rules sit above task-specific instructions.

- Did You Know: A recurring, hard-to-debug failure mode in multi-agent setups is *not* model variance or tool failure but ambiguity over which policy file governs a given task class — two rule files disagree, or no single artifact says which one wins, so the agent's behavior drifts unpredictably between runs. The anchored-path-resolution approach taught in this module exists to remove exactly that ambiguity: one task-class table, one resolution order, one place to look.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Writing a long AGENTS.md that mixes task-class routing, policy detail, and style guidance in one file | AGENTS.md is the first file agents read, so every team member adds their rule to it until it becomes unreadable | Reserve AGENTS.md for the task-class pointer map; move policy detail into per-domain files that AGENTS.md references by path |
| Treating all rules as equally enforceable without distinguishing advisory from enforcement | The team has not explicitly discussed which rules are hard constraints and which are preferences | Run a one-hour governance workshop: list every rule, vote on which tier it belongs to, and assign an owner to each enforcement rule |
| Copying the same policy into multiple prompt templates instead of referencing a single source | The team started with one prompt template, then cloned it for different task classes, and the policy text came along for the ride | Extract governance rules into repository files, remove them from all prompt templates, and add a single AGENTS.md pointer to each governance file |
| Adding enforcement gates without providing a remediation path | The team automated the check but not the recovery, leaving agents blocked without a clear next step | Every enforcement script must print a stderr message that includes the path to the remediation document before exiting non-zero |
| Letting policy files go stale without a review cadence | Policy files are rarely the most urgent item in a sprint, so review gets deferred indefinitely | Add a reviewed-date field to every policy file and a CI check that fails if any policy file is older than 90 days |
| Relying on the agent to discover the correct policy file through tree search | The team has not built a pointer graph, so the only way an agent can find policy is by searching | Create an AGENTS.md task-class table that maps each task class to a specific policy file path, and validate those paths in CI |
| Placing rules in the platform tier that the repository should control | The platform team and the repository team have not agreed on who owns which tier of policy | Document the platform's fixed rules in a PLATFORM.md file at the repo root, reference it from AGENTS.md, and keep repository policy files focused on repository-controlled rules |
| Treating AGENTS.md as a one-time setup task rather than a maintained control surface | The team wrote AGENTS.md during agent onboarding and never updated it as policies changed | Add an AGENTS.md review step to the pull request template for any PR that changes a policy file, so the pointer graph stays in sync |

## Quiz

Test your understanding with these scenario-based questions.

<details><summary>1. A team's AGENTS.md file is 3,800 lines long and includes branch conventions, commit templates, review checklists, deployment steps, runbook links, and coding style guides. The team reports that agents frequently violate the branch convention despite the rule appearing prominently in AGENTS.md. What is the most likely root cause?</summary>

The most likely root cause is that the branch convention is buried in a monolithic AGENTS.md where it competes for attention with thousands of lines of other guidance. In a 3,800-line file, the agent's attention mechanism — like a human reading a long document — dilutes the signal of any single rule. The fix is not to make the rule louder or to reformat the file. The fix is to split AGENTS.md into a task-class pointer map and a set of per-domain policy files, then move the branch convention into a dedicated file (docs/harness/policy/branches.md) and enforce it with a pre-push hook. The agent then follows the pointer to the policy file, reads a short focused document, and encounters the enforcement gate before the branch is pushed — a mechanical path that does not depend on attention-budget competition.</details>

<details><summary>2. Your team maintains the same deployment checklist in three places: a Notion wiki, a Slack canvas, and docs/runbooks/deploy.md. An agent is about to execute a deployment and discovers all three sources through separate search operations. Which source should the agent trust, and what single repository change would prevent this ambiguity from recurring?</summary>

The agent should trust docs/runbooks/deploy.md because it is the repository-resident source and is therefore versioned, reviewable, and discoverable by CI validation. The Notion wiki and Slack canvas are ephemeral communication surfaces that may be stale, unversioned, or missing recent updates. The single repository change to prevent recurrence is to deprecate the Notion and Slack copies, replace them with links that point to the repository file, and add the deploy.md path to the AGENTS.md pointer graph so every agent boots into the correct source without searching. The team should also add a CI check that confirms deploy.md exists and references valid enforcement scripts, so the pointer chain is validated on every pull request.</details>

<details><summary>3. A team adds a secret-scanning pre-commit hook to their repository. The hook correctly detects a test API key in a configuration file and blocks the commit, but the agent responds by removing the configuration file entirely rather than rotating the key. What tier classification error caused this behavior?</summary>

The team correctly classified secret scanning as an enforcement rule and implemented the mechanical gate. The error is that they did not provide a remediation path — the enforcement script blocked progress without telling the agent what to do next. An enforcement rule that says "stop" without saying "and here is how to recover" converts a resolvable failure into a dead end, and agents confronted with a dead end will often take destructive actions to clear the block. The fix is to ensure the enforcement script's stderr output includes a link to a remediation document (docs/runbooks/secret-rotation.md) that describes how to rotate the key, replace the committed value with a placeholder, and re-stage the file. The three-tier model requires not just the gate but the path through the gate.</details>

<details><summary>4. Your team copied the full set of repository governance rules into six different prompt templates for six different task classes. The branch-naming convention changes, and you update five of the six templates. Two weeks later, an agent running on the sixth template creates a branch with the old naming pattern. Where does this failure belong in the three-tier model, and what is the correct long-term fix?</summary>

This failure does not fit cleanly into any tier because the rules were never in a tier — they were duplicated across prompt surfaces rather than governed from a single source. The immediate fix is to update the sixth template, but the long-term fix is to remove governance rules from all prompt templates, place them in a single repository policy file (docs/harness/policy/branches.md), reference that file from AGENTS.md, and enforce the convention with a branch-naming hook that reads the policy file. The task surface (prompt templates) should contain only task-specific instructions, and the governance surface (harness layer) should be the single source of truth that every session loads at boot. This separation prevents the duplication problem permanently because there is only one copy of the rule to update.</details>

<details><summary>5. A repository has an enforcement rule that blocks commits when test coverage drops below 80 percent, enforced by a CI gate. An agent working on a bug fix adds a single-line change to a legacy module that has no existing tests. The CI gate blocks the merge, and the agent spends twelve turns trying to write tests for the entire legacy module before giving up. What is wrong with the enforcement rule, and how should it be adjusted?</summary>

The enforcement rule is correct in principle — test coverage thresholds prevent regression — but it applies too broadly. The rule should distinguish between new code (which should meet the 80 percent threshold) and existing uncovered code (which an agent should not be expected to retroactively cover as part of a bug fix). The fix is to modify the enforcement script to measure coverage only on changed lines or changed files rather than on the entire codebase, using a tool like diff-cover or a custom script that compares coverage reports against the git diff. This keeps the enforcement tier's benefit — preventing untested changes — while removing the unintended burden of requiring agents to fix pre-existing coverage gaps that are unrelated to the current task.</details>

<details><summary>6. Your team is evaluating whether to move the commit-message format convention from advisory to enforcement. What operational evidence would justify the move, and what specific metric would you track during a two-week trial period?</summary>

The operational evidence that justifies promoting a rule to enforcement is a measurable violation rate that exceeds the team's tolerance. For a commit-message format convention, the team should track the percentage of agent-authored commits that violate the convention over a two-week window. If the violation rate is below 5 percent, advisory is working and enforcement would add friction without benefit. If the violation rate is above 20 percent, advisory has demonstrably failed and enforcement is justified. The trial period should measure not just the violation rate but also the false-positive rate — commits that the enforcement script rejects but the team would have accepted — because a high false-positive rate indicates that the convention is not well-defined enough to automate. The team should also measure the remediation time: how long does it take an agent to fix a rejected commit message and re-push, compared to how long it currently takes a human reviewer to request the fix.</details>

<details><summary>7. An agent session begins, reads AGENTS.md, follows a pointer to docs/harness/policy/bug-fix.md, and executes the enforcement scripts listed there. One script fails with exit code 1 and prints "Branch name must match pattern: ^(feature|bugfix|hotfix)/[A-Z]+-[0-9]+. See docs/runbooks/branch-naming.md." The agent opens docs/runbooks/branch-naming.md and finds it empty except for the title. What single CI check would have prevented this situation?</summary>

A pre-flight anchor validation check would have prevented this situation. The check walks the AGENTS.md pointer graph, follows every reference to a policy file, reads every enforcement script path from each policy file, and confirms that every remediation document referenced in the enforcement scripts' output strings exists and contains more than a minimum number of words. This validation runs in CI on every pull request that touches the harness layer, so a broken remediation link is caught at merge time rather than at agent run time. The check can be implemented as a simple shell script that greps for "See docs/" patterns in enforcement script stderr output, verifies that each referenced path exists, and fails the CI run with a specific error message if any path is missing or empty.</details>

<details><summary>8. A team adopts the three-tier harness model and classifies all their rules correctly. Six months later, an incident reveals that the platform runtime's timeout envelope was set to 300 seconds, while several enforcement scripts take 240-280 seconds to run. During peak load, these scripts occasionally hit the timeout and fail, which agents interpret as a policy violation rather than an infrastructure failure. What tier-classification error does this reveal?</summary>

This reveals a misalignment between the platform tier and the enforcement tier. The platform's timeout envelope is a platform runtime rule that the repository cannot override, but the enforcement scripts' execution time was not constrained to stay within that envelope. The platform tier and the enforcement tier must be designed together: an enforcement script that can exceed the platform's timeout is not a reliable gate because it can fail for infrastructure reasons that are unrelated to policy compliance. The fix is either to raise the platform timeout (if the platform team agrees), reduce the enforcement scripts' execution time to stay comfortably under the timeout with a safety margin, or split long-running enforcement checks into a fast pre-check that validates preconditions and a slow full check that runs asynchronously after the commit is pushed. The general principle is that no enforcement gate should have a runtime that approaches the platform's outer timeout bound.</details>

## Hands-On Exercise

In this exercise, you will design a mock repository layout with a three-tier harness, build an AGENTS.md pointer graph, create interconnected policy files and enforcement scripts, and simulate an agent traversal that resolves a specific deployment failure using only grep, cat, and shell scripts.

**Setup:** Create a temporary directory and populate it with the repository scaffold described below. Use only standard command-line tools (bash, grep, cat, mkdir, echo).

### Task 1: Build the scaffold

Create the following directory structure and files:

```
harness-lab/
  AGENTS.md
  CLAUDE.md
  docs/
    harness/
      policy/
        branches.md
        tests.md
        deploy.md
      advisory/
        style.md
      runbooks/
        branch-naming.md
        test-failure.md
        deploy-rollback.md
  scripts/
    branch-guard.sh
    pre-commit-tests.sh
    deploy-guard.sh
  PLATFORM.md
```

<details><summary>Solution</summary>

```bash
mkdir -p harness-lab/{docs/harness/{policy,advisory,runbooks},scripts}
touch harness-lab/{AGENTS.md,CLAUDE.md,PLATFORM.md}
touch harness-lab/docs/harness/policy/{branches.md,tests.md,deploy.md}
touch harness-lab/docs/harness/advisory/style.md
touch harness-lab/docs/harness/runbooks/{branch-naming.md,test-failure.md,deploy-rollback.md}
touch harness-lab/scripts/{branch-guard.sh,pre-commit-tests.sh,deploy-guard.sh}
chmod +x harness-lab/scripts/*.sh
```

</details>

### Task 2: Write the AGENTS.md task-class map

Write an AGENTS.md that maps three task classes to their policy files using explicit file paths. Each entry should include the task class name, the policy file path, and a one-line description of the enforcement gates that apply.

<details><summary>Solution</summary>

```markdown
# AGENTS.md

## Task Classes

| Task Class | Policy File | Enforcement Gates |
|---|---|---|
| bug-fix | docs/harness/policy/branches.md | scripts/branch-guard.sh, scripts/pre-commit-tests.sh |
| deploy | docs/harness/policy/deploy.md | scripts/deploy-guard.sh |
| feature | docs/harness/policy/branches.md | scripts/branch-guard.sh, scripts/pre-commit-tests.sh |

## Platform Overrides

See PLATFORM.md for platform-level rules that this repository cannot modify.

## Advisory Rules

See docs/harness/advisory/style.md for code style and review conventions.
```

</details>

### Task 3: Write an enforcement script and its policy file

Write `scripts/deploy-guard.sh` to enforce a deployment precondition: the target environment must be explicitly declared as either "staging" or "production" in the commit message, or the deploy is blocked. The script should fail with exit code 1 and print a remediation link. Then write `docs/harness/policy/deploy.md` to reference the script.

<details><summary>Solution</summary>

`docs/harness/policy/deploy.md`:

```markdown
# Deployment Policy

## Enforcement

- scripts/deploy-guard.sh: blocks deploy unless the commit message includes `env: staging` or `env: production`

## Remediation

See docs/harness/runbooks/deploy-rollback.md for rollback procedures if a deploy fails after guard check passes.
```

`scripts/deploy-guard.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

COMMIT_MSG="${1:-$(git log -1 --pretty=%B 2>/dev/null || echo '')}"

if echo "$COMMIT_MSG" | grep -qE 'env: (staging|production)'; then
    echo "Deploy guard passed: environment declared."
    exit 0
fi

echo "ERROR: deploy blocked. Commit message must include 'env: staging' or 'env: production'." >&2
echo "Remediation: docs/harness/runbooks/deploy-rollback.md" >&2
exit 1
```

</details>

### Task 4: Simulate an agent traversal

Simulate how an agent would resolve a deployment request using only command-line tools. Start from AGENTS.md, follow the pointer to the deploy policy, run the enforcement script, and observe the pass or fail outcome. Test both a passing case (commit message includes the environment) and a failing case (commit message does not).

<details><summary>Solution</summary>

```bash
cd harness-lab

# Step 1: Agent reads AGENTS.md and finds the deploy policy path
POLICY=$(grep '^| deploy ' AGENTS.md | grep -oE 'docs/harness/policy/[^ |]+')
echo "Resolved policy file: $POLICY"

# Step 2: Agent reads the policy file and finds the enforcement script
SCRIPT=$(grep -o 'scripts/[^ ]*\.sh' "$POLICY" | head -1)
echo "Resolved enforcement script: $SCRIPT"

# Step 3: Run the enforcement script with a passing commit message
echo "env: staging" | xargs -I{} bash "$SCRIPT" "{}" && echo "PASS: deploy allowed" || echo "FAIL"

# Step 4: Run the enforcement script with a failing commit message (no env declaration)
bash "$SCRIPT" "Fix typo in config" && echo "PASS" || echo "FAIL: deploy blocked as expected"
```

Expected output shows that the script passes when `env: staging` is in the commit message and fails with the remediation link when it is absent.

</details>

### Task 5: Add a pre-flight validation check

Write a shell script `scripts/validate-anchors.sh` that walks the AGENTS.md policy table, extracts every referenced file path, and verifies that each file exists. Run it to confirm that your new harness scaffold is internally consistent.

<details><summary>Solution</summary>

```bash
#!/usr/bin/env bash
set -euo pipefail

errors=0
echo "=== Anchor validation ==="

# Extract all paths from AGENTS.md policy table (skip header and separator)
while read -r path; do
    if [ -f "$path" ]; then
        echo "OK: $path"
    else
        echo "BROKEN: $path does not exist"
        errors=$((errors + 1))
    fi
done < <(grep -oP 'docs/[^ ]+' AGENTS.md | sort -u)

# Also validate enforcement script references inside policy files
for policy in docs/harness/policy/*.md; do
    while read -r script_path; do
        if [ -f "$script_path" ] && [ -x "$script_path" ]; then
            echo "OK: $script_path (referenced from $policy)"
        else
            echo "BROKEN: $script_path referenced from $policy but missing or not executable"
            errors=$((errors + 1))
        fi
    done < <(grep -oP 'scripts/[^ ]+\.sh' "$policy" 2>/dev/null)
done

if [ "$errors" -gt 0 ]; then
    echo "=== $errors broken anchors found ==="
    exit 1
fi

echo "=== All anchors valid ==="
```

</details>

### Success Checklist

- [ ] Repository scaffold created with AGENTS.md, policy files, advisory files, runbooks, and enforcement scripts
- [ ] AGENTS.md contains a task-class table with explicit file paths, not prose descriptions
- [ ] At least one enforcement script produces deterministic pass/fail output with exit codes
- [ ] Every enforcement script prints a remediation link to stderr on failure
- [ ] Agent traversal simulation resolves from AGENTS.md to enforcement script in under 3 steps
- [ ] Pre-flight anchor validation script confirms all referenced paths exist

## Sources

- https://openai.com/index/harness-engineering/ — OpenAI's canonical post on harness engineering as a discipline (February 2026)
- https://developers.openai.com/codex/guides/agents-md — OpenAI Codex CLI documentation on AGENTS.md as a control surface
- https://docs.anthropic.com/en/docs/claude-code/memory — Anthropic documentation on CLAUDE.md and scoped rules for Claude Code
- https://agents.md/ — Community-driven AGENTS.md specification and conventions
- https://model-spec.openai.com/2025-09-12.html — OpenAI Model Spec defining the hierarchy of instruction authority (platform, developer, user)
- https://modelcontextprotocol.io/docs/concepts/architecture — MCP architecture specification describing client-server resource discovery patterns
- https://github.com/openai/symphony — Symphony OSS repository demonstrating issue-as-control-plane orchestration with WORKFLOW.md contracts
- https://raw.githubusercontent.com/openai/symphony/main/SPEC.md — Symphony specification defining lifecycle hooks and state-machine semantics for agent orchestration
- https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions — GitHub Actions documentation on secret handling (referenced in enforcement-tier secret scanning patterns)
- https://aider.chat/docs/repomap.html — Aider documentation on repository map generation and progressive disclosure patterns for coding agents
- https://github.com/features/codespaces — GitHub Codespaces documentation on repository-as-environment patterns
- https://containers.dev/ — Development Containers specification defining standardized repository environment contracts

## Next Module

[Module 3.2: Guardrails, Gates, and Agent-Legible Apps](../module-3.2-guardrails-gates-and-agent-legible-apps/) — extends the three-tier model into concrete mechanical guardrails: hooks, lints, tests, errors-as-remediation, observability surfaces, and devtools wiring that make agent behavior legible to the humans who own the outcomes.
