---
title: "Configuring an Agentic Harness"
slug: ai-ml-engineering/ai-native-development/module-1.3-claude-code-cli-deep-dive
sidebar:
  order: 204
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 4-5 hours

**Prerequisites**: Module 1.1, basic Git workflow, comfort reading Markdown and JSON, and a safe sandbox repository where an agent can make test changes without touching production credentials.

> **Go deeper:** For the tool-family map and the AI Coding Harness Rosetta Stone, start with [Module 1.1: AI Coding Tools Landscape](/ai-ml-engineering/ai-native-development/module-1.1-ai-coding-tools-landscape/). For lower-level SDK and runtime design, continue later to [Module 1.10: Agent SDK and Runtime Patterns](/ai-ml-engineering/ai-native-development/module-1.10-anthropic-agent-sdk-and-runtime-patterns/).

---

## Introduction: The Harness Is The Scaffold

An agentic harness is the software layer that wraps a model and turns it into a working development partner. The model predicts and reasons, but the harness decides what repository context gets loaded, which files can be edited, which commands can run, which tools are reachable, which instructions persist across sessions, and when a human must approve an action. The durable skill is learning how a harness turns instructions, tool access, hooks, memory, permissions, and delegation into an auditable workflow.

That distinction matters because the model behind a harness can change without changing the operational problem. A terminal agent may use one frontier model this month and another next month, while the team still needs the same project instructions, test commands, secret boundaries, approval rules, and rollback habits. Treating "the model" and "the harness" as the same thing leads to brittle vendor habits. Treating them separately lets you move between Codex, Cursor, Claude Code, Aider, opencode, Windsurf, Gemini CLI, GitHub Copilot, Goose, or future tools without relearning the core control surface.

Hypothetical scenario: a platform team allows an agent to help with dependency updates. In the first repository, the agent reads a generic README, upgrades a package, and breaks a generated client because the code generation step was documented only in a teammate's memory. In the second repository, the agent reads a nearby `AGENTS.md`, sees the exact generation command, runs the targeted tests, and stops before pushing because the permission profile requires human approval for remote Git operations. The model could be identical in both cases; the difference is the harness configuration around it.

This module sits in the Extensibility layer of the AI-native development track. We will use concrete products as worked examples because configuration is easiest to learn from real files, but the subject is not any single vendor. The subject is the recurring pattern: persistent instructions, portable tool protocols, deterministic hooks, specialized sub-agents, explicit permissions, memory hygiene, and cost-aware operating habits.

## What You'll Be Able To Do

- Explain the difference between a model, an agentic harness, and an agent runtime without tying the explanation to one vendor.
- Design a rules-file strategy using `AGENTS.md`, `CLAUDE.md`, or another project instruction file without duplicating stale guidance.
- Add MCP as a vendor-neutral context and tool layer while keeping server permissions narrow and auditable.
- Use lifecycle hooks, wrapper scripts, or CI gates to add deterministic checks around probabilistic agent behavior.
- Create specialized sub-agents or equivalent delegated roles with clear scope, tool budgets, and reporting formats.

## Why This Module Matters

The difference between casual agent use and operationally reliable agent use is configuration discipline. A casual user asks for a fix and reads the answer. An operator designs the environment that answer must pass through: what the agent knows before it starts, what evidence it must produce, what it is forbidden to touch, and which external systems it may query. The operator is not trying to make the assistant sound smarter. The operator is making the assistant's work easier to constrain, reproduce, and review.

Think of the harness like a workshop bench rather than a magic engineer. The bench has labeled drawers, power tools, safety guards, measurement jigs, task cards, and cleanup rules. A skilled worker can do more with a well-arranged bench, and a distracted worker can do less damage when sharp tools have guards. The model is the worker's reasoning engine; the harness is the bench that decides which tools are within reach and how the work is checked before it leaves the room.

This framing also lowers the temperature around vendor debates. One team may prefer a terminal-first harness for automation, another may prefer an IDE-first harness for fast diff review, and another may choose a local-first harness for data-control reasons. Those choices matter, but the same configuration questions keep appearing. Where do persistent instructions live? How are external tools exposed? Which actions require approval? How do specialized workers share context? What audit trail proves that the agent did not simply claim success?

The practical outcome is leverage with boundaries. A well-configured harness can run the same test command every time it changes a file, load repository-specific rules before planning, use an MCP server to read a ticket instead of relying on pasted context, and hand a security review to a specialized sub-agent. A poorly configured harness can make broad edits from incomplete context, leak a secret into a tool call, or silently weaken a test because no gate told it that behavior was unacceptable.

## Did You Know?

This is the only "Did You Know?" section in the module, and it is limited to sourced infrastructure facts rather than origin lore, invented metrics, or personality stories. The purpose is to anchor the durable patterns in public governance and documentation milestones, not to imply that any one product owns the agentic development category.

- **AGENTS.md is now under neutral stewardship**: OpenAI announced on December 9, 2025 that it was contributing AGENTS.md to the Agentic AI Foundation under the Linux Foundation.
- **The AGENTS.md convention is plain Markdown**: The public AGENTS.md site describes it as a simple, open format with nested files and closest-file precedence for subprojects.
- **MCP started as an open integration standard**: Anthropic introduced the Model Context Protocol on November 25, 2024 as an open standard for connecting AI assistants to external systems.
- **MCP moved to the Agentic AI Foundation**: Anthropic announced on December 9, 2025 that it was donating MCP to AAIF, and the MCP project blog reported a first-year snapshot of 97 million monthly SDK downloads and 10,000 active servers.

## Common Mistakes

Most harness failures are not dramatic model failures. They are mundane configuration failures that make a capable assistant operate with stale instructions, excessive authority, missing evidence, or unsafe context. The table below is written as a review checklist: if a team sees one of these patterns in a repository, the fix is usually a small configuration change before the next prompt is written.

| Mistake | Problem | Better Approach |
|---|---|---|
| Treating the model and harness as one thing | Teams argue about model names while ignoring permissions, context, and checks | Evaluate the harness control surface separately from the model provider |
| Duplicating rules across tool-specific files | `AGENTS.md`, `CLAUDE.md`, and IDE rules drift apart over time | Keep one canonical shared file and use thin per-tool adapters |
| Granting broad shell access too early | The agent can mutate dependencies, delete files, or touch unrelated state | Allow only the commands needed for the next evidence-producing loop |
| Connecting MCP servers without ownership | External data and tool calls become invisible workflow authority | Assign owners, scopes, credentials, and audit expectations to each server |
| Using sub-agents without output contracts | Specialist reports become vague opinions that cannot be ground-checked | Require scope, file references, evidence, remediation, and verification notes |
| Hiding critical knowledge in session memory | Future runs depend on private summaries that teammates cannot inspect | Move durable rules into repository or organization-controlled instruction files |
| Automating release steps before review habits are stable | A bad manual process becomes a faster bad automated process | Package workflows only after the human process is repeatable and observable |

The most subtle mistake is using configuration as a way to avoid judgment. A permission profile, MCP server, hook, or sub-agent is not proof that the work is safe. It is a way to make the work easier to inspect. Humans still decide whether the evidence is sufficient, whether the scope is appropriate, and whether the remaining risk is acceptable for the repository.

## The Configuration Surface

Every agentic harness exposes a configuration surface, even when the names differ. The durable surfaces are instruction files, context connectors, lifecycle automation, delegation, permissions, and memory. Some products place these in JSON settings, some in TOML, some in Markdown, some in IDE settings, and some in command-line flags. The names will change faster than the underlying engineering needs.

```
Human intent
    |
    v
Rules file / project memory ----> model prompt context
    |
    v
Permission profile -------------> allowed actions
    |
    v
MCP / connectors ---------------> external tools and data
    |
    v
Hooks / CI / wrappers ----------> deterministic checks
    |
    v
Sub-agents / skills ------------> specialized delegated work
    |
    v
Evidence: diff, tests, logs, review notes
```

The harness is independent of the model that powers it. A rules file does not become less important because the model improves. A hook that blocks accidental writes to `.env` files still matters when the model is stronger. A permission profile that requires approval before `git push` still matters when the model has better planning. Better models reduce some error rates, but they do not remove the need for explicit authority boundaries.

The configuration surface should be treated as source-controlled infrastructure. Shared rules belong in the repository when they affect everyone. Personal overrides belong in ignored local files when they affect only one developer. Organization policy belongs in managed settings or centrally deployed templates when the boundary is compliance or security. The worst place for a critical instruction is an untracked chat habit that only one engineer remembers to paste.

A mature harness configuration also separates design-time and run-time authority. Design-time authority decides what the agent may know before it proposes a change: rules files, indexed docs, MCP resources, issue text, and previous review notes. Run-time authority decides what the agent may do after it starts acting: edit paths, shell commands, external tool calls, and delegated sub-agent work. Teams get into trouble when they grant run-time authority to compensate for missing design-time context. If the agent does not know the test command, the answer is to document the test command, not to allow every shell command and hope it discovers the right one.

This is why the most useful harness review is a configuration review, not only a transcript review. Open the rules file, inspect the connector list, read the permission profile, check the hook scripts, and verify where local memory is stored. Then compare those settings against the task the agent is being asked to perform. If the task is a read-only architecture explanation, broad write access is unnecessary. If the task is a migration, a narrow edit scope plus targeted test commands is usually enough. If the task requires external systems, the connector should be explicit, scoped, and visible in the final evidence.

## Rules Files And Agent Instructions

Rules files are the simplest durable pattern in agentic development: put project-specific instructions in a predictable Markdown file so the harness can load them before it acts. The file should explain setup, tests, coding standards, risky areas, review expectations, and commands that prove success. It should not become a second README full of marketing copy; it should be closer to what you would tell a new teammate during their first repository walkthrough.

As of 2026-06, `AGENTS.md` is the broad cross-tool convention. The public AGENTS.md project describes it as a simple, open Markdown format for guiding coding agents, with nested files for subprojects and closest-file precedence when instructions conflict. OpenAI contributed AGENTS.md to the Agentic AI Foundation under the Linux Foundation in December 2025, and OpenAI's announcement described adoption by more than 60,000 open-source projects and agent frameworks including Amp, Codex, Cursor, Devin, Factory, Gemini CLI, GitHub Copilot, Jules, and VS Code among others. Verify the current support matrix before depending on any one tool's loading behavior.

The key behavior to internalize is hierarchy. A repository-level `AGENTS.md` gives broad guidance, and a deeper `services/payments/AGENTS.md` can add payment-specific rules. In nearest-file-wins systems, the closer file should sharpen the instruction rather than contradict the repository baseline. If the root file says "run unit tests before finishing" and the service file says "for payments, also run the idempotency test," the hierarchy helps. If one file says "never push" and another says "push automatically," the harness cannot rescue you from a governance problem.

Claude Code uses `CLAUDE.md` as its native project memory file rather than reading `AGENTS.md` directly. As of 2026-06, Anthropic's Claude Code memory documentation states that Claude Code reads `CLAUDE.md`, not `AGENTS.md`, and recommends importing `AGENTS.md` from `CLAUDE.md` or using a symlink when a repository already has cross-tool instructions. That is an important honesty point: do not claim Claude Code natively reads `AGENTS.md` until the current documentation says it does.

Equivalent in other harnesses: Codex uses layered `AGENTS.md` guidance, many IDE and CLI agents have their own project-rule files, and Module 1.1's Rosetta Stone is the place to compare current names across tools.

Here is a realistic `CLAUDE.md` pattern that keeps the shared policy in `AGENTS.md` while adding a small Claude-specific note. The example headings are intentionally inside the fenced block; they are example file contents, not headings in this module.

```markdown
@AGENTS.md

# Claude Code Notes

## Project Overview
This repository contains a FastAPI service, a React dashboard, and background jobs that process billing events.

## Code Standards
- Use type hints for all Python function signatures.
- Keep API response shapes backward compatible unless the issue says otherwise.
- Prefer small patches that can be reviewed with `git diff --stat` and targeted tests.

## Architecture Patterns
- API routes live under `src/api/`.
- Database access goes through repository objects in `src/repositories/`.
- Background jobs must be idempotent because queue retries are expected.

## Common Tasks
- Install dependencies: `.venv/bin/python -m pip install -r requirements.txt`
- Run unit tests: `.venv/bin/pytest tests/unit -q`
- Run billing tests: `.venv/bin/pytest tests/billing -q`
- Run lint: `.venv/bin/ruff check src tests`

## Import References
@docs/architecture.md
@docs/billing-invariants.md

## Do NOT
- Do not commit generated migration files unless the task explicitly asks for a schema change.
- Do not read `.env`, `.env.*`, or files under `secrets/`.
- Do not push branches or open pull requests without explicit human instruction.
```

A strong rules file is short enough to load repeatedly and specific enough to change behavior. Avoid long lists of generic advice such as "write clean code" or "be careful." Replace them with commands, invariants, and boundaries: "run `.venv/bin/pytest tests/billing -q` after billing edits," "never change `public_api.py` without updating contract tests," and "ask before adding a production dependency." The agent does not need motivational text; it needs operational facts.

There are two common anti-patterns. The first is stuffing an entire engineering handbook into the agent file, which burns context and hides the rules that actually matter. The second is leaving the file stale, which is worse than having no file because the harness will confidently follow obsolete commands. Treat agent instructions as living documentation: update them when a review catches a repeated mistake, when a build command changes, or when a team discovers a new unsafe path.

For multi-tool repositories, make `AGENTS.md` the shared source when possible and bridge vendor-specific files to it. A `CLAUDE.md` can import `AGENTS.md`; a Codex setup can use global and project `AGENTS.md`; other tools may read `.cursorrules`, `copilot-instructions.md`, `.windsurfrules`, or configurable fallback filenames. The exact filenames are volatile, so the durable policy is simple: one shared canonical instruction file, thin per-tool adapters, and explicit dated notes when a product cannot read the shared file directly.

## MCP: Portable Tool And Context Access

MCP, the Model Context Protocol, is the durable integration story behind many current harnesses. Anthropic introduced MCP on November 25, 2024 as an open standard for connecting AI assistants to systems where data lives, including content repositories, business tools, and development environments. Anthropic donated MCP to the Agentic AI Foundation under the Linux Foundation on December 9, 2025, and the MCP project blog reported more than 97 million monthly SDK downloads, 10,000 active servers, and first-class client support across major AI platforms in its first year. Verify current adoption and security guidance before connecting new servers.

MCP is not "Claude's protocol" in the way a proprietary plugin system would be. It began at Anthropic, but its value is that a server can expose tools and resources through a common protocol while multiple clients decide how to call them. The harness becomes an MCP client; the database connector, GitHub connector, docs connector, or internal API wrapper becomes an MCP server. That separation is why MCP matters for durable learning: you are learning how to expose controlled context and actions, not merely memorizing one CLI command.

The simplest mental model is "context with an interface." A raw paste into chat is unstructured context. A file path is repository context. An MCP resource can be live documentation, a ticket, a schema, or a monitoring query that the harness can request when needed. An MCP tool can be a constrained action such as "create issue," "query read-only database," or "fetch deployment status." The security question is whether that server exposes only the capability the task needs.

As of 2026-06, Claude Code's MCP documentation shows remote HTTP servers and local stdio servers as common installation patterns. The exact flags and JSON schema are product skin, so verify current docs before copying commands into a production setup.

```bash
# Remote HTTP server
claude mcp add --transport http docs https://docs.example.com/mcp

# Remote HTTP server with an explicit header
claude mcp add --transport http internal-api https://api.example.com/mcp \
  --header "Authorization: Bearer $TOKEN"

# Local stdio server
claude mcp add --transport stdio local-search -- node ./tools/local-search-mcp.js
```

Equivalent in other harnesses: Codex, Cursor, VS Code integrations, Gemini-oriented tools, and other MCP-capable clients may expose different setup commands, but the durable pattern is still client plus server plus least-privilege tool access; compare current tool names in Module 1.1.

Project-level MCP configuration is useful when a repository depends on a repeatable connector set. Keep secrets out of the file, prefer read-only scopes when possible, and document who owns the server. A server that can query production billing data is not just a convenience; it is a new data path that needs review.

```json
{
  "servers": {
    "engineering-docs": {
      "transport": "http",
      "url": "https://docs.example.com/mcp"
    },
    "local-repo-search": {
      "transport": "stdio",
      "command": "node",
      "args": ["./tools/local-repo-search-mcp.js"]
    },
    "read-only-postgres": {
      "transport": "stdio",
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-postgres",
        "postgresql://readonly_user@localhost/app"
      ]
    }
  }
}
```

MCP is powerful because it reduces copy-paste context loss, but it also expands the blast radius of a prompt. If a malicious issue description reaches the harness through a ticket connector, the agent may see instructions written by an attacker. If a docs connector can read sensitive pages, the agent may summarize information into the wrong place. If a tool can mutate state, an ambiguous prompt can become an external action. The safe default is read-only servers, scoped credentials, server allowlists, and audit logs for every tool call that matters.

The best first MCP server is usually boring. Connect internal documentation, a local search index, or a read-only test database before connecting systems that send messages, deploy code, or change money-facing records. When the agent uses the server successfully, capture the exact use case in the rules file: "Use `engineering-docs` for architecture decisions, but do not use it for secrets or customer data." A connected harness should become more grounded, not more mysterious.

## Hooks: Deterministic Automation Around Probabilistic Work

Hooks are lifecycle automation points around an agent's work. They exist because language-model behavior is probabilistic, while many engineering checks must be deterministic. A hook can block a risky command, log a tool call, append context at session start, run a formatter after an edit, require approval for a specific path, or prevent a session from ending before tests have been reported. The durable idea is not the hook brand; it is adding machine-checkable rules at moments where trust alone is too weak.

Claude Code is a useful worked example because its hook system has named lifecycle events. As of 2026-06, the documented events include pre-tool and post-tool hooks, prompt-submission hooks, session-start hooks, stop hooks, and related lifecycle controls. The exact event list and JSON fields are volatile product details, so verify current docs before relying on a specific field in a security-sensitive workflow.

| Lifecycle point | Durable purpose | Example use |
|---|---|---|
| Before tool use | Decide whether an action is allowed | Block writes to secrets or destructive shell commands |
| After tool use | Validate or record what happened | Run a formatter or append an audit log |
| Prompt submission | Add context or reject unsafe prompts | Warn when a task asks for production credentials |
| Session start | Load environment facts | Print branch, issue, or sandbox status |
| Stop or completion | Require evidence before ending | Refuse completion until tests are reported |

Equivalent in other harnesses: if a tool does not have native hooks, use Git hooks, `pre-commit`, wrapper scripts, CI jobs, shell aliases, or a repository-specific command runner to create the same deterministic checkpoints.

Here is a small Claude Code settings example. It blocks a narrow destructive pattern before tool execution and loads a session banner at startup. The point is not that every team should copy this exact JSON; the point is that policy becomes executable rather than remembered.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(rm:*)",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/confirm-delete.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/session-banner.sh"
          }
        ]
      }
    ]
  }
}
```

The hook script should be boring, small, and testable. Avoid turning a hook into another agent unless you have a clear reason, because now your safety system depends on another probabilistic decision. A shell script that rejects recursive force deletes is less glamorous than an AI reviewer, but it is predictable, cheap, and easy to audit.

```bash
#!/usr/bin/env bash
set -euo pipefail

payload="$(cat)"
command="$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')"

printf '[%s] command=%s\n' "$(date -Iseconds)" "$command" >> "$HOME/.agent-audit.log"

if [[ "$command" == *"rm -rf"* ]] || [[ "$command" == *"--force"* ]]; then
  jq -n \
    --arg reason "Blocked destructive delete; ask a human to perform this manually." \
    '{permissionDecision: "deny", permissionDecisionReason: $reason}'
  exit 0
fi

jq -n '{permissionDecision: "allow"}'
```

Hooks should be designed around failure modes you have actually seen or can reasonably predict. Useful early hooks include blocking writes to `.env` and `secrets/`, logging every command that touches deployment files, requiring approval for dependency lockfile changes, and reminding the agent to run a project-specific test command after editing a risky subsystem. Less useful hooks print motivational messages, rewrite every prompt, or run expensive checks after every tiny edit.

The most important design choice is where to enforce the rule. A formatting hook is fine after an edit. A secret-access rule belongs before a read or write. A deployment gate belongs in CI or an external release system, not only inside a local harness that a developer can bypass. Hooks are one layer in a defense-in-depth workflow; they do not replace Git review, CI, branch protection, or human accountability.

## Sub-Agents And Specialized Delegation

Sub-agents are specialized workers inside or alongside a harness. The core pattern is simple: give a delegated agent a narrower role, a narrower tool set, a narrower memory window, and a clearer output format than the primary agent. Instead of asking one general assistant to implement a feature, audit security, optimize performance, and write release notes in a single context window, you can split the work into focused passes that are easier to review.

The label changes by product. One harness may call them sub-agents, another workers, another skills, another background agents, and another simply separate invocations with different prompts. The durable design is the same: specialization should reduce cognitive load and blast radius. A security reviewer should not need write access by default. A test-failure fixer may need shell access but not cloud credentials. A docs drafter may need file reads and writes but not package installation authority.

As of 2026-06, Claude Code supports file-based sub-agents in `.claude/agents/` and session-defined sub-agents through CLI JSON. The precise fields are product details, but the useful structure is frontmatter plus a role prompt plus tool constraints. The example headings below remain inside the fenced file content.

```markdown
---
name: security-reviewer
description: Review code changes for security-sensitive defects before a pull request.
tools: [Read, Grep, Glob, Bash]
model: sonnet
---

# Security Review Agent

You are a security reviewer. Review only the current diff unless the user asks for broader context.
Do not edit files. Report findings with file paths and concrete remediation steps.

## Focus Areas
1. Input validation and output encoding
2. Authentication and authorization checks
3. Secret handling and accidental credential exposure
4. Dangerous shell, deserialization, or template usage
5. Dependency or configuration changes that widen attack surface

## Output Format
For each finding, include:
- Severity: CRITICAL, HIGH, MEDIUM, or LOW
- Location: file path and line number when available
- Evidence: the code or behavior that proves the risk
- Fix: the smallest concrete remediation
- Verification: the test, linter, or manual check that should prove the fix
```

Equivalent in other harnesses: Codex-style workflows can use bounded subagent dispatches, Cursor-style workflows can use specialized rules or chat contexts, and open tools can run separate prompts with different model providers; Module 1.1 is the current map for naming differences.

A good sub-agent contract has three limits. First, define scope: "review the diff" is safer than "review the whole application." Second, define authority: "read-only" is different from "may edit tests." Third, define evidence: "give file and line references" is easier to ground-check than "tell me if it looks good." Without those limits, sub-agents become another source of confident but hard-to-audit prose.

Delegation is not a substitute for integration. The primary agent or human still owns the final diff, resolves conflicts between specialists, and decides what to ship. If a performance sub-agent recommends caching and a security sub-agent warns that the cache may expose tenant data, someone must reconcile the tradeoff. Specialized agents can improve coverage, but they also create more outputs to evaluate.

## Permissions And Autonomy

Permissions are the harness control surface for autonomy. Module 1.1 introduces the L0-L5 autonomy ladder; this module focuses on the configuration that makes a chosen level real. A tool is not at L3 because a vendor says it is agentic. It is at L3 only if it can take multi-step action under bounded authority and return evidence. It is not at L5 because a user typed "be autonomous." It is at a higher autonomy level only when permissions, tools, rollback, and review process support that level safely.

The most useful permission categories are allow, deny, and ask. Allow grants routine authority. Deny blocks actions that should not happen in the harness. Ask creates a human checkpoint for operations that may be acceptable in some contexts but not without review. This pattern appears in different forms across tools, even when the syntax changes.

As of 2026-06, Claude Code settings support permissions in JSON with allow and deny lists, and documented examples include environment variables and tool-specific permission patterns. Treat the following as a teaching example, not a universal production template.

```json
{
  "permissions": {
    "allow": [
      "Read(src/**)",
      "Read(tests/**)",
      "Edit(src/**)",
      "Edit(tests/**)",
      "Bash(.venv/bin/pytest tests/unit -q)",
      "Bash(.venv/bin/ruff check src tests)"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(secrets/**)",
      "Bash(sudo:*)",
      "Bash(rm -rf:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(npm install:*)",
      "Write(pyproject.toml)",
      "Write(package-lock.json)"
    ]
  }
}
```

Equivalent in other harnesses: some tools expose sandbox modes, approval prompts, filesystem scopes, or Git-worktree boundaries instead of this exact JSON; the durable task is mapping each permission to the autonomy level you intend.

Full autonomy is a configuration, not a personality trait. It means the harness can act without asking for each step inside a defined sandbox. That can be appropriate for throwaway experiments, generated test fixtures, or a disposable worktree where secrets are absent and rollback is cheap. It is not appropriate for a primary checkout with production credentials, a repository with unrelated user work, or a task where the verification command is unknown.

Use a simple rule: grant the minimum authority needed for the next evidence-producing loop. If the agent only needs to inspect a bug, read-only is enough. If it needs to edit one package, write scope can be limited to that package. If it needs to run tests, allow the test command rather than every shell command. If it needs to push a branch, make that a human-approved step until your team has a documented reason to automate it.

Permission design should also account for directionality. Reading a file, writing a file, running a command, calling a network service, and changing remote state are different risk classes even when the harness displays them as one "tool use" stream. A read-only docs query may be acceptable during planning, while a write to a lockfile or a push to a remote branch deserves a separate checkpoint. If your chosen harness exposes only coarse permissions, compensate with Git worktrees, clean sandboxes, CI checks, and explicit human review before remote side effects.

The autonomy ladder becomes useful when you can point to actual controls. L1 may mean suggestion-only work inside an editor. L2 may allow scoped edits but no command execution. L3 may allow edits plus targeted test commands inside a worktree. L4 may allow multi-step issue work with preapproved commands and hooks. L5 should be rare because it implies broad, sustained action with minimal human interruption. Those levels are not badges; they are operating modes that should be documented in the repository's instructions.

## Memory, Cost, And Power-User Operations

Memory is the long-term context a harness carries across sessions or loads from project files. Rules files are one form of memory, but products may also offer user memories, enterprise policies, session summaries, skills, command libraries, and local caches. Memory should make the agent less repetitive and more grounded. It should not become a private shadow process that changes behavior without the team understanding why.

The safest memory pattern is layered and explicit. Organization policy states non-negotiable boundaries. Repository instructions state project workflow. Subdirectory instructions state local exceptions. Personal local files state individual preferences and should not override shared safety rules. Session summaries can help continuity, but they should never be the only place a critical build command or security invariant exists.

Cost management is part of harness configuration because context, tool calls, and delegated agents all consume budget. A harness that loads every documentation file, spawns three specialists, and runs a long conversation for a one-line typo fix is badly configured even if it produces correct code. Match the model and context window to the task, compact or clear stale sessions, prefer one-shot non-interactive mode for simple transformations, and stop the loop when evidence is sufficient.

Memory and cost interact more than many teams expect. A large rules file, a broad MCP result, a long session summary, and three sub-agent reports can all enter the same context budget. When that happens, the model may spend more effort navigating the workspace you created than solving the actual task. The answer is not to starve the agent of context; it is to make context intentional. Load the invariant rules every time, retrieve external context only when the task needs it, and archive long-running work into human-readable notes rather than relying on hidden session state.

There is also a review-cost dimension. A harness that changes one file and reports one test command is cheap for a human to review. A harness that changes twelve files, summarizes three MCP calls, invokes two specialists, and reports no final diff is expensive even if the token bill looks modest. Configure workflows so review artifacts are compact: changed files, commands run, sources consulted, unresolved assumptions, and any remaining failures. The human bottleneck is often attention, not API cost.

As of 2026-06, Claude Code exposes interactive usage and a `-p` print mode for one-shot command-line workflows, while other harnesses expose their own non-interactive or headless modes. The vendor-specific flags are volatile, but the durable pattern is stable: use conversational mode for exploration, one-shot mode for scripts, plan mode for risky proposals, and sandboxed execution for autonomous loops.

```bash
# One-shot review pattern in a CLI harness
git diff --staged | claude -p "Review this diff for correctness and security issues."

# The same durable pattern in another harness may use a different command name:
git diff --staged | codex exec "Review this diff for correctness and security issues."
```

Equivalent in other harnesses: one-shot mode, background mode, headless mode, and CI mode all serve the same purpose when they turn an agent into a scriptable step with visible input and output.

Power-user workflow packaging sits on top of memory and permissions. Claude Code has slash commands and skills; Codex and other tools have prompt files, task recipes, or dispatch wrappers; IDE agents may have reusable instructions or saved workflows. Package a workflow only after it is stable enough to repeat. A brittle manual process becomes a brittle automated process when wrapped in a command.

```markdown
---
name: review-staged
description: Review staged changes before commit.
---

Read the staged diff and report only actionable issues.

Use this evidence:
!git diff --cached

Check for:
1. Logic bugs or missing edge cases
2. Security-sensitive changes
3. Tests that were weakened instead of fixed
4. Files outside the stated task scope

Do not edit files. Return findings with file paths and suggested fixes.
```

The operating habit is to make the harness produce evidence in the same place a human reviewer expects it. A good agent session ends with a diff, commands run, failures remaining, and unresolved assumptions. A poor session ends with "done" and no way to tell what happened. Configuration should keep pushing the workflow toward the first outcome.

## Key Takeaways

- An agentic harness is the scaffold around a model: instructions, tools, hooks, memory, permissions, delegation, and evidence.
- Harness configuration is independent of the model provider, so learn the durable control surface rather than one product's current labels.
- `AGENTS.md` is the broad cross-tool Markdown convention, while `CLAUDE.md` remains Claude Code's native memory file as of 2026-06.
- MCP is vendor-neutral integration infrastructure; connect servers with least privilege and treat every connector as a new data path.
- Hooks and CI gates make probabilistic work safer by enforcing deterministic checks at lifecycle boundaries.
- Sub-agents are useful only when they narrow scope, authority, and output format enough to make review easier.
- Permission profiles should match the intended autonomy level, with full autonomy reserved for controlled sandboxes.
- Memory and cost discipline keep agentic work grounded, repeatable, and affordable.

Read these takeaways as an operating checklist rather than a summary. If your harness has no shared rules file, no scoped connector story, no deterministic checkpoint, no delegation contract, and no final evidence habit, the next improvement should be configuration work before a stronger model is added.

## Learner Check

Earlier in this module, the core principle was stated this way:

> The durable skill is learning how a harness turns instructions, tool access, hooks, memory, permissions, and delegation into an auditable workflow.

Before moving on, apply that sentence to your own tooling. Name one instruction file, one permission boundary, one deterministic check, and one evidence command that would make your current AI coding workflow more auditable. If you cannot name all four, your next improvement is probably configuration, not prompting.

## Quiz

**Q1.** A team switches from one model provider to another but keeps the same terminal agent, rules files, MCP servers, and permission profile. What changed, and what stayed the same?

<details>
<summary>Answer</summary>

The model changed, but the harness configuration stayed the same. The durable operational controls are the rules files, connectors, hooks, permissions, memory, and evidence loop. A stronger or different model may improve reasoning, but it does not remove the need for explicit harness boundaries.

</details>

**Q2.** Your repository already has `AGENTS.md`, and you want Claude Code to use the same shared instructions. What is the honest configuration pattern as of 2026-06?

<details>
<summary>Answer</summary>

Do not claim that Claude Code natively reads `AGENTS.md`. Create a `CLAUDE.md` that imports `@AGENTS.md`, or use a symlink if that fits your environment. Add only Claude-specific notes below the import so the shared policy remains canonical.

</details>

**Q3.** Why is a read-only MCP documentation server usually a better first connector than a server that can deploy or mutate tickets?

<details>
<summary>Answer</summary>

It grounds the harness in useful external context while keeping the blast radius small. A mutating connector turns a prompt into an external action path, so it needs stronger approval, audit, and rollback controls. Start with low-risk context before granting workflow authority.

</details>

**Q4.** A harness does not support native hooks. Does that mean the team cannot add deterministic safety checks around agent work?

<details>
<summary>Answer</summary>

No. The durable pattern can be implemented with Git hooks, `pre-commit`, CI jobs, wrapper scripts, command runners, or sandbox policies. Native hooks are convenient, but the engineering need is deterministic enforcement at the right lifecycle boundary.

</details>

**Q5.** A security sub-agent reports "looks safe" but provides no file paths, evidence, or verification command. What is wrong with that output?

<details>
<summary>Answer</summary>

It is not auditable. Specialized agents should narrow scope and produce reviewable evidence: file paths, concrete findings, remediation steps, and verification suggestions. A vague approval increases confidence without improving safety.

</details>

**Q6.** When is full autonomy reasonable, and when is it a bad default?

<details>
<summary>Answer</summary>

Full autonomy is reasonable in a sandbox or disposable worktree with no secrets, clear scope, and cheap rollback. It is a bad default in primary checkouts, production-connected environments, repositories with unrelated user work, or tasks where the evidence command is unknown.

</details>

**Q7.** A team says its agent is operating at L4 autonomy because it can edit files and run commands. What configuration evidence would you ask for before accepting that claim?

<details>
<summary>Answer</summary>

Ask for the actual permission profile, filesystem scope, allowed commands, approval checkpoints, rollback boundary, and required evidence commands. Autonomy level is not proven by the agent's confidence or by a broad marketing label; it is proven by the control surface that defines what the harness can do without interrupting a human.

</details>

**Q8.** Your harness is becoming expensive and hard to review because every task loads long rules, broad MCP results, multiple sub-agent reports, and a long conversation history. What configuration changes should you make first?

<details>
<summary>Answer</summary>

Keep invariant project rules loaded, but retrieve external context only when the task needs it, compact or clear stale sessions, use one-shot mode for simple work, and require compact final evidence such as changed files, commands run, sources consulted, and unresolved assumptions. The goal is not less context at all costs; the goal is intentional context that produces reviewable work.

</details>

## Hands-On Exercises

These exercises are designed for a disposable repository or a throwaway branch. Do not connect production credentials, customer data, or deployment systems while practicing. The goal is to build configuration muscle memory, not to prove that an agent can be trusted with broad authority on the first attempt. Treat each exercise as a short operating drill: configure one surface, run one observable test, inspect the evidence, and write down what changed.

### Exercise 1: Build A Shared Rules File

Create an `AGENTS.md` at the root of a sandbox repository, then add a thin `CLAUDE.md` adapter that imports it if you use Claude Code. Include setup commands, test commands, code style rules, risky paths, and a short "do not" section. Then run your harness from the repository root and ask it to summarize the active instructions before making any edits.

**Success criteria:**
- [ ] The shared instructions live in `AGENTS.md`.
- [ ] Any tool-specific file is a thin adapter, not a duplicate policy source.
- [ ] The harness can report the setup command, test command, and at least two forbidden actions.
- [ ] No secret files or production credentials are referenced in the instructions.

### Exercise 2: Add A Read-Only Context Connector

Add a low-risk MCP server or equivalent connector that exposes documentation, local search, or a read-only test data source. Ask the harness to answer a question that requires the connector, then inspect the transcript or tool log to confirm it used the connector rather than inventing context. If your chosen harness does not support MCP, simulate the same pattern with a read-only wrapper script and document the limitation.

**Success criteria:**
- [ ] The connector is read-only or scoped to harmless sample data.
- [ ] The configuration does not commit tokens, passwords, or machine-specific absolute paths.
- [ ] The rules file explains when the connector should and should not be used.
- [ ] The answer includes enough evidence to show which external context informed it.

### Exercise 3: Create A Deterministic Safety Check

Implement a hook, Git hook, `pre-commit` check, or wrapper script that blocks one dangerous action before it happens. Good beginner targets are reads from `.env`, writes under `secrets/`, recursive force deletes, or dependency changes without human approval. Test the check with a harmless command that should pass and a simulated command that should be blocked.

**Success criteria:**
- [ ] The check is deterministic and does not depend on another language model.
- [ ] The block message explains what happened and how a human can proceed safely.
- [ ] The check writes a small audit record for blocked actions.
- [ ] You can show both a passing case and a blocked case.

### Exercise 4: Design A Specialized Reviewer

Create a read-only sub-agent, saved prompt, skill, or second harness profile for one narrow review role such as security, test quality, documentation clarity, or performance. Give it a clear scope, tool list, and output format. Run it against a small diff and compare the result with your own review, then revise the prompt so it reports fewer vague opinions and more evidence.

**Success criteria:**
- [ ] The specialized reviewer has read-only authority by default.
- [ ] The output format requires file paths, evidence, and concrete fixes.
- [ ] The reviewer does not claim approval when it cannot verify the code.
- [ ] The primary human or agent still owns the final decision.

## Sources

- [AGENTS.md](https://agents.md/) - The public AGENTS.md site describes the Markdown convention, nested files, closest-file precedence, broad tool compatibility, and 60,000+ open-source project adoption.
- [Custom instructions with AGENTS.md - OpenAI Codex](https://developers.openai.com/codex/guides/agents-md) - OpenAI's Codex guide documents how Codex discovers global and project `AGENTS.md` files and layers guidance.
- [OpenAI co-founds the Agentic AI Foundation under the Linux Foundation](https://openai.com/index/agentic-ai-foundation/) - OpenAI's December 9, 2025 announcement says it contributed AGENTS.md to AAIF and describes adoption across agent frameworks.
- [Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) - Anthropic's November 25, 2024 announcement introduces MCP as an open standard for connecting AI assistants to external systems.
- [Donating the Model Context Protocol and establishing the Agentic AI Foundation](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation) - Anthropic's December 9, 2025 announcement covers donating MCP to AAIF under the Linux Foundation and lists major platform adoption.
- [MCP joins the Agentic AI Foundation](https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/) - The MCP project blog reports the 97 million monthly SDK downloads, 10,000 active servers, and major client support snapshot.
- [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings) - Anthropic's settings documentation covers settings precedence and permission configuration.
- [How Claude remembers your project](https://docs.anthropic.com/en/docs/claude-code/memory) - Anthropic's memory documentation covers `CLAUDE.md`, its load order, and the current relationship to `AGENTS.md`.
- [Claude Code hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks) - Anthropic's hooks documentation covers lifecycle events and JSON input/output patterns.
- [Claude Code sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) - Anthropic's sub-agent documentation covers file-based and CLI-defined sub-agent configuration.
- [Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp) - Anthropic's MCP documentation covers connecting Claude Code to MCP servers and the current command examples.

## Next Module

Continue to [Module 1.4: Agent-First IDEs](/ai-ml-engineering/ai-native-development/module-1.4-agent-first-ides/) to compare IDE harnesses as a form factor, then return to terminal and headless patterns in [Module 1.5: CLI AI Coding Agents](/ai-ml-engineering/ai-native-development/module-1.5-cli-ai-coding-agents/). When you are ready to build harnesses rather than configure them, use [Module 1.10](/ai-ml-engineering/ai-native-development/module-1.10-anthropic-agent-sdk-and-runtime-patterns/) as the runtime layer.
