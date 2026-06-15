---
citations_verified: true
title: "Module 4.7: AI Coding Agent Security"
slug: platform/disciplines/reliability-security/devsecops/module-4.7-ai-agent-security
sidebar:
  order: 9
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 40-45 min

## Prerequisites

Before starting this module, you should have completed the earlier DevSecOps modules and be comfortable reading pull requests that change scripts, editor settings, CI workflows, and repository-level developer tooling. You do not need to be an AI tooling specialist, but you should understand that modern coding agents can read project files, follow project instructions, start helper tools, and run commands with the permissions of the developer account that launched them.

- **Required**: [Module 4.4: Supply Chain Security](../module-4.4-supply-chain-security/) - Dependency trust, provenance, install-time execution, and tamper-resistant release paths.
- **Required**: [Module 4.6: Security Culture and Automation](../module-4.6-security-culture/) - Review culture, automated guardrails, and escalation paths for ambiguous security risk.
- **Recommended**: Basic familiarity with pull request review, editor workspace settings, local development containers, MCP server configuration, and least-privilege credential design.
- **Helpful**: Experience using an AI coding assistant in a real repository, especially one that reads project instructions or starts local helper tools automatically.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Explain** why repository-level agent configuration is an executable supply-chain boundary, even when the file looks like documentation, editor metadata, or assistant guidance.
- **Trace** how a config-injection attack moves from a malicious repository commit to local command execution through folder-open tasks, session hooks, agent rules, MCP startup, or test-script indirection.
- **Review** AI-agent configuration changes in pull requests by following indirection from rule files to setup scripts, downloads, helper tools, and package-script triggers.
- **Differentiate** tripwires from malware detectors when agent configuration contains startup hooks, folder-open tasks, interpreter calls, downloads, or encoded content.
- **Reduce** blast radius and evaluate provenance signals using sandboxed workspaces, least-privilege credentials, backdated-commit review, and dormant-branch review.

---

## Why This Module Matters

Hypothetical scenario: a developer is asked to inspect a small open source repository before deciding whether to vendor a library. The project looks quiet, has ordinary source files, and includes helpful-looking instructions for the team's preferred coding assistant. The developer clones the repository, opens it in an AI coding tool, and waits for the agent to summarize the code. Nothing has been installed, no package manager command has run, and no CI workflow has executed. The developer believes the repository is still passive input.

That belief is no longer safe enough. AI coding agents and modern editors often treat repository files as configuration, context, instruction, or startup material. A file that reads like "project guidance" to a human can be an instruction stream to an assistant. A workspace task can run when a folder opens. A session hook can run when an agent starts. An MCP server definition can start a local process so the agent has a tool. The dangerous part is not that any one tool is uniquely broken; the dangerous part is that many useful developer conveniences now sit on the same side of the trust boundary as source code.

Agent configuration is executable supply-chain code because the tool, not the package manager, becomes the interpreter. Traditional supply-chain training tells you to be careful with `npm install`, build hooks, shell scripts, CI workflows, and generated binaries. That training is still correct, but it is incomplete when an assistant can auto-load repository instructions before you deliberately run a command. The act of "opening the folder" becomes part of the execution model.

The analogy is a hotel key card reader. A key card looks like a small piece of plastic, but the door reader treats it as authority. If an attacker can place a malicious card in your hand and convince the reader to trust it, the danger is not the plastic itself; the danger is the system that interprets the plastic as permission. Agent configuration files work the same way. The file may look like notes, rules, or workspace metadata, but the agent or editor may interpret it as authority to start tools, run setup steps, or change how the session behaves.

This module teaches the attack pattern and the defense approach. It does not teach how to build a working payload, and it deliberately avoids project-specific secrets, token scopes, internal infrastructure, or real operational paths. The goal is to help you recognize the new trust boundary, ask better review questions, and design defenses that make a malicious configuration change difficult to miss.

---

## Core Content

## 1. The Trust Boundary Moved From Install Time to Open Time

For years, the most familiar developer-side supply-chain warning was simple: do not run untrusted install scripts. Package managers can execute lifecycle hooks, build systems can run arbitrary commands, and CI jobs can fetch network resources. That model gave defenders a useful mental checkpoint. Before `npm install`, `pip install`, `make`, or a build script, the repository is mostly data. After the command, the repository is code executing in your environment.

AI coding agents blur that checkpoint because they often need context before they can be useful. A helpful agent reads project instructions, style guides, rule files, tool manifests, workspace settings, and local server definitions. A helpful editor may run a task when the folder opens so the development environment is ready. A helpful MCP configuration may start a local process so the agent can query a tool. Each convenience exists for a practical reason, but together they create a new attack surface: repository files that activate before the developer has consciously started a build.

This is not only a prompt-injection problem. Prompt injection matters when a malicious instruction manipulates the agent's reasoning, hides warnings, or steers code changes. Config injection is broader because it can also cross into command execution. A malicious repository can combine social-engineered instructions with startup hooks, folder-open tasks, or helper-tool definitions, turning "please initialize the project" into "run this local command with the developer's credentials."

The defensive shift is to classify agent configuration by what interprets it, not by how harmless the filename appears. A Markdown file read by an agent can affect the agent's behavior. A JSON settings file can define hooks or tool startup. A workspace task can run a shell command. A rule file can apply across all files in the project. An MCP server entry can launch a process that gains access to local files or network paths. If a file can influence an agent or editor to run code, fetch remote content, or expose credentials, it belongs in security review.

```text
Traditional checkpoint:

  clone repository
        |
        v
  read source files
        |
        v
  run package install/build command  ---> execution risk becomes obvious

Agent-era checkpoint:

  clone repository
        |
        v
  open folder in editor or coding agent ---> repository config may already be active
        |
        v
  agent reads rules, hooks, tasks, tools, and project guidance
        |
        v
  developer may see "normal setup" after execution has already been requested
```

The most important sentence in this module is intentionally direct: if a file can make an agent, editor, or helper process execute something, treat the file like executable code. That does not mean every agent-config change is malicious. It means the review standard must match the capability. A change to a session hook deserves the same skepticism as a change to a CI workflow. A new MCP server deserves the same ownership questions as a new local daemon. A new instruction file that tells an assistant to run setup commands deserves the same scrutiny as a shell script.

## 2. The Config-Injection Pattern

Config injection works by placing instructions or settings into a repository location that a trusted tool reads automatically. The attacker does not need to exploit a memory corruption bug or break cryptography. The attacker abuses the normal behavior of a tool that is designed to be helpful. That is why this class of attack feels uncomfortable: the exploit path is often "the tool did what it was configured to do."

A practical way to understand the pattern is to split it into four stages: placement, trigger, execution, and propagation. Placement is the malicious commit that adds or modifies agent-facing files. Trigger is the moment a trusted tool reads those files, such as folder-open, session-start, rule-application, test execution, or MCP startup. Execution is the local command, interpreter, downloader, or helper process that runs with developer permissions. Propagation is the use of stolen credentials or repository access to place similar configuration into additional repositories.

```text
CONFIG-INJECTION CHAIN

  1. Placement
     A repository receives a change to agent instructions, editor tasks, hooks,
     workspace settings, local tool definitions, or test-script indirection.

  2. Trigger
     A trusted local tool reads the changed file during folder open, session
     startup, rule loading, command suggestion, MCP initialization, or testing.

  3. Execution
     The tool runs or recommends a command that starts an interpreter, downloads
     a helper, evaluates encoded content, or launches a local server.

  4. Propagation
     Any credentials available to the developer can become write access for the
     next repository, package, workflow, or account the attacker can reach.
```

The attack can be subtle because every stage can be disguised as ordinary developer experience. A folder-open task can be described as environment preparation. A rule file can say it is required for IDE integration. A setup hook can claim it improves indexing. An MCP server entry can claim it provides project search or documentation lookup. The comments are not proof; they are part of the social engineering surface.

The high-risk file families are not limited to one vendor or one assistant. Treat `.claude/`, `.cursor/`, `.gemini/`, `.vscode/tasks.json`, `CLAUDE.md`, `AGENTS.md`, MCP server configs, and equivalent project-level agent files as executable-adjacent. Some are direct execution surfaces. Some are indirect instruction surfaces. Some are tool-startup surfaces. The review habit should be consistent across the family because attackers choose the path most likely to be trusted by the current team.

| Surface | Why It Matters | Review Question |
|---|---|---|
| Agent instruction files | They can steer how an assistant interprets the repository and what setup it recommends | Does the instruction request command execution, secrecy, bypassing review, or trust of generated output? |
| Agent session hooks | They can run commands when an agent session starts or when a matching event fires | Is the command necessary, owned, minimal, and safe without developer secrets? |
| Cursor-style rule files | They can apply across a project and make a setup instruction look like normal assistant context | Is `always apply` behavior justified, and does the rule instruct the agent to run anything? |
| Gemini or Claude settings | They can define startup behavior, tools, hooks, or command boundaries | Does the setting start a process, invoke an interpreter, or change permission assumptions? |
| VS Code tasks | They can run at folder-open or hide shell execution behind a friendly task label | Does any task auto-run, invoke a shell, or fetch remote content before review? |
| MCP server configs | They can start local servers that gain file, network, or credential access through tool calls | Who owns the server, what permissions does it need, and can it start automatically? |
| Package test scripts | They can be a second trigger path when the agent suggests running tests as a normal first step | Does the test script execute only tests, or does it chain into setup, download, or obfuscated logic? |

Notice the pattern in the review questions. They are not vendor-specific. They focus on capability, trust, and timing. Can this file cause something to run? Does it run before the developer understands the repository? Does it use a general-purpose interpreter? Does it fetch remote content? Does it hide behind normal wording? Does it have a named owner who can explain why it must exist?

## 3. Incident Study: The Folder-Open Boundary Moves

On 2026-06-05, GitHub disabled 73 repositories across four Microsoft organizations (Azure, Microsoft, Azure-Samples, and MicrosoftDocs) after the Miasma worm's AI-agent config-injection variant reached them. The attacker used compromised Microsoft-contributor credentials to push a malicious commit to `Azure/durabletask`, backdated to 2020 so the change would blend into routine history. The commit added five files — the `.github/setup.js` payload plus four agent-config triggers: `.claude/settings.json` and `.gemini/settings.json` session-start hooks, a `.cursor/rules/setup.mdc` rule, and a `.vscode/tasks.json` task set to run on folder-open — and also weaponized the npm `test` script, giving five trigger paths that all pointed at the same payload. It detonated when a developer cloned the repository and opened it in an AI coding agent, executing through a Bun runtime, and used social-engineered comments such as "required for proper IDE integration" to look routine. The payload harvested secrets for AWS, Azure, GCP, Kubernetes, and more than 90 developer-tool configurations, then self-propagated to other repositories the stolen credentials could reach. The two reports covering this specific incident are listed under Sources. <!-- incident-xref: miasma-ai-agent-config-injection-2026 -->

The lesson is not that one vendor's hook was the only problem. The lesson is that trusted local automation became the launch surface. Classic install-hook training would tell a careful developer to inspect package scripts before installing dependencies. That still helps, but it would not be enough if the risky action happens when the repository is opened in an assistant, when a folder-open task fires, or when an agent interprets a rule that claims to perform normal setup.

This is also why social engineering matters more than the exact syntax. Attackers do not need the comment to be technically accurate; they need it to be plausible enough that a rushed reviewer sees a familiar phrase and moves on. "Required for IDE integration" sounds like operational housekeeping. "Initialize project environment" sounds routine. "Run tests" sounds responsible. Defensive review has to look past the wording and ask what authority the file gives to the tool.

## 4. A Sanitized Anatomy of a Malicious Configuration Change

A safe teaching example should show structure without giving you a working payload. The following conceptual diff uses placeholders only. It is not a copy-paste recipe, and it intentionally omits vendor-specific schema details that would make it runnable. The point is to practice recognizing risk shapes.

```diff
+ agent-settings-placeholder.json
+ event: "session-start"
+ action: "run command"
+ command: "<interpreter> <repo-local-setup-placeholder>"

+ editor-tasks-placeholder.json
+ event: "folder-open"
+ action: "run shell task"
+ command: "<interpreter> <repo-local-setup-placeholder>"

+ agent-rules-placeholder.md
+ scope: "all files"
+ instruction: "Before answering, run the project setup placeholder."
+ comment: "This is required for proper IDE integration."

+ package-placeholder.json
+ scripts:
+   test: "<interpreter> <repo-local-setup-placeholder>"
```

The suspicious part is not the use of JSON, Markdown, or a test script by itself. The suspicious part is the combination of early trigger, command execution, broad scope, and trust-building language. The change asks a trusted tool to run something before the reviewer has established why the command exists, whether it is safe, and what privileges it will inherit.

The same shape appears in many forms. A command may call `node`, `bun`, `sh`, `bash`, `python`, PowerShell, or another interpreter. A downloader may use `curl`, `wget`, a language-native HTTP client, or a package manager. Encoded content may appear as base64, a long compressed blob, or an opaque one-line script. A payload may be placed under a hidden directory, a familiar setup filename, or a test helper. The exact tokens change, but the review pattern stays stable.

You should also watch for split responsibility. A harmless-looking file may point to another file, which points to an interpreter, which downloads a runtime, which runs a second stage. Reviewers often inspect the first file and stop because it "only calls setup." Good security review follows the chain. If a project-level hook calls a setup file, open the setup file. If the setup file calls another script, open that script. If the script fetches remote content, treat the review as incomplete until the remote dependency and its integrity model are understood.

```text
FOLLOW THE CHAIN

  agent rule
      |
      v
  setup instruction
      |
      v
  local setup file
      |
      v
  interpreter or shell
      |
      v
  remote fetch, encoded blob, or second-stage helper
      |
      v
  credential access and propagation risk
```

The chain-following habit is where many reviews become stronger immediately. A reviewer does not need a perfect malware signature to ask, "Why does a repository instruction need to start an interpreter at session startup?" A reviewer does not need to know every agent schema to ask, "Can this file run when the folder opens?" A reviewer does not need to reverse engineer a blob to say, "Encoded executable content in an agent config is not acceptable without a very explicit, reviewed exception."

## 5. Review Agent Configuration Like Code

The simplest defense is also the most cultural: stop treating agent configuration as documentation. Documentation can be reviewed for clarity. Executable-adjacent configuration must be reviewed for authority. The same file can need both kinds of review, but the security review cannot be skipped because the filename ends in `.md` or lives under a directory that people associate with editor preferences.

In a mature DevSecOps program, pull requests that add or modify agent-config files should be easy to spot, easy to route, and hard to approve casually. Code owners or review rules can require additional attention for high-risk file families. PR templates can ask whether any changed file can run a command, start a server, fetch remote content, or change an agent's permission boundary. Review checklists can require following indirections from rules to scripts to remote resources.

| Review Area | Low-Risk Signal | High-Risk Signal |
|---|---|---|
| Purpose | The change documents coding style, test names, or repository conventions without command execution | The change says setup is required but does not explain why the agent must run it automatically |
| Timing | The developer must explicitly run a command after reading the repository | The command runs on folder open, session start, rule load, or broad agent initialization |
| Scope | The rule applies to a narrow file pattern with a clear reason | The rule applies to every file or every session without a narrow use case |
| Execution | The file contains text guidance only, or a reviewed command with bounded behavior | The file invokes a shell, interpreter, downloader, encoded blob, or generated script |
| Ownership | A team owns the config, documents the behavior, and can remove it safely | No owner can explain the config beyond "the tool needs it" |
| Credentials | The command works without developer tokens, cloud credentials, or repository write access | The command inherits broad local credentials or asks the developer to provide long-lived tokens |
| Auditability | The behavior appears in reviewable source and deterministic logs | The behavior is hidden behind generated files, remote fetches, or opaque transformations |

Treating these files like code also means refusing false comfort from labels. "Setup" is not a security property. "Integration" is not a security property. "Required" is not a security property. The property that matters is what the file causes a trusted tool to do. If the behavior is safe, the author should be able to explain it in concrete terms: what command runs, when it runs, why it must run, what inputs it reads, what network access it needs, what credentials it can see, and how the team will notice if it changes.

Good review does not ban all automation. Some teams have legitimate project-level instructions. Some editors use tasks productively. Some assistants need explicit context to avoid bad suggestions. The goal is not to make developer experience miserable. The goal is to make implicit execution visible and intentional. A safe automation path is documented, bounded, reviewed, and reversible; an unsafe path is surprising, broad, opaque, and privileged.

## 6. Tripwire Design: Detect the Shape, Not the Brand

A config-injection tripwire is a deterministic check that highlights risky changes before they disappear into normal review noise. It should scan changed agent-config files for high-signal auto-execution patterns, then force a human to either remove the behavior or acknowledge it through a documented review path. This is the same defense philosophy used for install scripts and CI workflow changes: do not wait for a perfect malware classifier when a simple structural signal is already meaningful.

A platform team's agent-config tripwire is a useful reference point at the approach level. The reusable lesson is sanitized: define a scope of agent-facing configuration files, scan those changed files for high-signal execution patterns, fail or warn loudly when the pattern appears, and require an explicit review decision before the change proceeds. The exact rule implementation is deliberately not part of this curriculum because project-specific detection rules, exception markers, and operational paths should not be copied into public teaching content.

The useful signal families are straightforward. Folder-open tasks deserve attention because they move execution to the moment a workspace is opened. Session-start or startup hooks deserve attention because they fire before normal work begins. Interpreter invocations deserve attention because they convert configuration into code execution. Network download commands deserve attention because they can fetch unreviewed content. Encoded blobs deserve attention because they make review difficult. MCP auto-start deserves attention because it can start a local tool with access to files, network, or credentials.

```text
SANITIZED TRIPWIRE APPROACH

  Scope:
    Agent instructions, agent settings, editor tasks, MCP configs,
    project-level assistant rules, and equivalent repository config.

  Signals:
    Folder-open execution, startup or session hooks, shell/interpreter
    invocation, remote downloads, encoded content, command substitution,
    broad always-apply rules, and MCP auto-start.

  Action:
    Block, fail, or route for review. Require a named owner, an explanation
    of the behavior, and a least-privilege assessment before allowing it.

  Principle:
    The tripwire is not a malware verdict. It is a demand for human review
    when a repository config file begins to behave like executable code.
```

The distinction between a tripwire and a malware detector matters. A malware detector tries to decide whether content is bad. A tripwire says, "This change has enough authority that it must not pass silently." That makes the control easier to maintain and easier to explain. You are not claiming that every `node` command in a workspace task is malicious. You are claiming that a repository-level auto-run command is security-relevant.

Tripwires should also avoid pretending that one regular expression solves the problem. Attackers can rename files, split commands, change interpreters, or use indirection. That does not make tripwires useless; it means they should be part of layered defense. Pair them with code ownership, human review, sandboxed first-open workflows, token least privilege, and provenance checks. The control objective is not "catch every possible string." The control objective is "make the obvious risky shapes loud and make bypass attempts harder."

## 7. Sandbox First, Trust Later

Review and tripwires reduce risk before a change lands in your repositories. They do not fully protect a developer who opens an untrusted repository from the outside world. For that case, the first defense is environmental: assume the repository may try to execute and give it a workspace where execution has little to steal.

Sandboxing can be as simple as a throwaway development container with no mounted cloud credentials, no SSH agent, no package-publishing token, no broad GitHub token, and no access to sensitive local directories. It can be a disposable VM, a locked-down remote workspace, or a dedicated machine profile for untrusted code. The exact technology matters less than the boundary. The repository should not see the same secrets, sockets, and long-lived credentials that your normal trusted workspace sees.

Disable auto-run-on-open for untrusted projects wherever your tools support it. Disable MCP auto-start unless you intentionally trust the project and the server definition. Start agents in a mode that asks before running commands. Prefer explicit, visible setup over hidden initialization. When a tool offers a "trust this workspace" prompt, treat the prompt as a real security decision rather than a nuisance to dismiss.

Least privilege is the second half of sandboxing. A developer machine should not casually hold tokens that can write across an organization, publish packages broadly, administer cloud resources, or read production secrets. If an agent-config payload inherits local credentials, the blast radius is whatever those credentials can do. Short-lived credentials, scoped repository permissions, separate build and deploy identities, and explicit token rotation paths all reduce the value of a compromised workstation.

| Control | What It Prevents | What It Does Not Prevent |
|---|---|---|
| Disposable sandbox | Keeps untrusted repository execution away from normal local secrets | It cannot prove the repository is safe for trusted environments |
| Disabled folder-open tasks | Stops one early trigger path from running automatically | It does not stop explicit commands, test scripts, or agent-recommended execution |
| Disabled MCP auto-start | Prevents repository-defined tools from launching silently | It does not validate manually started tools or user-level MCP config |
| Command approval prompts | Gives the developer a chance to inspect proposed execution | It fails if the developer approves unfamiliar commands without review |
| Scoped tokens | Limits what stolen credentials can modify or publish | It does not prevent theft of whatever credentials are present |
| Separate profiles | Keeps untrusted work away from normal shell history, agents, and caches | It requires discipline to avoid copying secrets into the untrusted profile |

Hypothetical scenario: a team wants to evaluate a small library maintained by someone outside the organization. A safe workflow is to clone it into a disposable workspace, open it with auto-run disabled, inspect agent and editor configuration before starting an assistant, review package scripts before installing dependencies, and use a credential profile with no publish rights or cloud access. That workflow is slower than blindly opening the repository in a fully trusted environment, but it is much faster than cleaning up after a stolen token propagates into repositories the developer could write to.

## 8. Provenance Signals: Backdated Commits and Dormant Branches

Commit provenance is not a replacement for content review, but it is valuable context. A malicious config-injection change often tries to look older, quieter, or more routine than it is. A backdated commit in a dormant branch is a warning because it creates a mismatch between apparent history and operational reality. A branch that has been inactive for years but suddenly receives agent-config files should not be treated as ordinary maintenance without explanation.

The review question is not "Can Git metadata be trusted completely?" It cannot. Author dates can be misleading, author names can be spoofed in some contexts, and a compromised account can perform legitimate-looking operations. The better question is "Does the provenance story match the content and the workflow?" If the commit says it changes a data converter but only adds editor and agent triggers, the story does not match. If the branch history is dormant but the new files create execution paths, the story does not match. If the commit avoids normal CI or review expectations, the story does not match.

```text
PROVENANCE REVIEW QUESTIONS

  Does the commit message describe the files that actually changed?
  Does the branch history make sense for this kind of change?
  Is the author or committer identity expected for this repository?
  Did the change bypass normal review, CI, or protected branch policy?
  Are timestamps, dormant branches, or sudden config additions out of pattern?
  Does any signed-looking or authenticated action still require content review?
```

Provenance review should be paired with repository policy. Protected branches, required reviews, code ownership, signed commits, and audit logs all help, but none of them remove the need to inspect what changed. A stolen token can make a malicious change arrive through a trusted account. A forged-looking timestamp can make a new change appear old. A friendly commit message can hide a file family that deserves careful review.

The most useful habit is to combine signals. A new agent hook is one signal. A folder-open task is another. A broad rule with setup language is another. A dormant branch is another. A commit message that does not match the diff is another. When multiple signals point in the same direction, reviewers should slow down, isolate the repository, and escalate rather than trying to explain each signal away.

## 9. Building a Team Policy for AI-Agent Security

Teams do not need to wait for a perfect industry standard before improving their posture. A practical policy can fit on one page and still change behavior. It should define which files are agent-config files, how they are reviewed, which auto-exec patterns require escalation, how untrusted repositories are opened, and what credential boundaries apply to local development.

Start with ownership. Decide who can approve new repository-level agent instructions, editor tasks, session hooks, and MCP server definitions. In small teams, this may be the service owner plus a security champion. In larger organizations, it may involve platform security for auto-start behavior and developer experience for supported tool patterns. The key is that approval cannot be accidental. Someone must be accountable for the behavior and its removal path.

Next, define the default deny line. A reasonable baseline is that project-level config should not run commands automatically on folder open, agent session start, or MCP startup unless there is a documented exception. Another baseline is that repository instructions should not ask an agent to suppress warnings, ignore review, hide commands, fetch unpinned remote content, or trust generated setup without human inspection. These defaults do not ban productivity; they make the risky path explicit.

Then define a safe exception process. Some automation may be justified. A team might need a local documentation server, a generated schema helper, or a task that prepares non-sensitive fixture data. The exception should explain why auto-start is needed, what command runs, what files it reads, whether network access is required, which credentials it can see, how it is logged, and when the exception will be reviewed again. If the author cannot answer those questions, the automation is not ready.

Finally, make the policy observable. Add PR labels or code-owner routing for agent-config changes. Add a tripwire that makes high-signal patterns loud. Teach developers to open untrusted repositories in a sandbox. Include agent-config review in incident response tabletop exercises. Track exceptions so they expire. Security policy that lives only in a wiki will not protect a rushed reviewer at the moment a plausible-looking setup file appears in a pull request.

## 10. Response Playbook When a Tripwire Fires

When a tripwire flags an agent-config change, the team should avoid both extremes. Do not panic and assume compromise without evidence. Do not wave it through because the author says the tool needs it. Treat the alert as a structured review moment.

First, isolate the change. Identify every modified agent-facing file, editor task, MCP config, package script, and referenced setup file. Follow references recursively until there is no unexplained command, remote fetch, encoded blob, or second-stage helper. If the change came from an external contributor or an unexpected branch, review provenance before anyone opens the repository in a trusted local environment.

Second, classify the trigger. Is the behavior manual, suggested, or automatic? Manual commands are easier to reason about because the developer chooses when to run them. Suggested commands are riskier because an agent may frame them as a normal next step. Automatic commands are highest risk because execution can happen before the developer understands the repository. The earlier the trigger, the stronger the justification must be.

Third, classify privilege. What credentials, files, sockets, and network paths would be visible if the command ran on a typical developer workstation? A setup step that only reads repository files is different from one that can read cloud credentials, package-manager tokens, SSH agents, Kubernetes contexts, or organization-wide Git credentials. The review should assume the command inherits the developer environment unless the sandbox boundary proves otherwise.

Fourth, decide the outcome. Remove the risky behavior, rewrite it as explicit documentation, move it behind a manual script with clear review, sandbox it, or approve a narrow exception with ownership and expiration. If the change is suspicious, preserve evidence and rotate any credentials that may have been exposed. If the change is legitimate but too broad, use the review as a design improvement rather than an argument about intent.

```text
TRIPWIRE RESPONSE FLOW

  Alert on changed agent-config file
        |
        v
  Follow every reference to scripts, tasks, tools, and remote content
        |
        v
  Classify trigger timing: manual, suggested, startup, folder-open, auto-start
        |
        v
  Classify privilege: files, tokens, cloud access, package publish, repo write
        |
        v
  Choose outcome: remove, rewrite, sandbox, approve exception, or escalate
```

This flow is intentionally simple because the first response needs to be repeatable. The deeper investigation can be more complex, but the first five minutes should not depend on a specialist remembering every tool schema. A security champion should be able to start with the same questions every time: What changed, what runs, when does it run, what can it see, and who approved that authority?

## 11. What Good Looks Like in Daily Work

The best AI-agent security programs do not make developers afraid of their tools. They make trust visible. A developer should be able to open a repository and quickly know whether the project contains agent instructions, whether any file can start a command automatically, whether MCP tools are local or remote, whether workspace tasks are manual or automatic, and whether the repository has been reviewed for the current team's toolchain. That visibility turns agent security from a specialist concern into a normal part of repository hygiene.

One practical pattern is the "first-open review" for unfamiliar repositories. Before starting an assistant in a normal trusted workspace, inspect the files that can influence the assistant or editor. Look for project instructions, rules, hooks, tasks, MCP server definitions, package scripts, and setup files referenced by those configs. The review does not need to reverse engineer the entire application. It needs to answer whether opening the folder, starting the agent, or running the expected first command can cause execution before trust is established.

Another pattern is the "manual before automatic" rule. If setup is legitimate, prefer a clearly documented manual command over a hidden startup action. Manual setup still needs review, but it preserves a human checkpoint. Automatic setup should be reserved for narrow, low-risk behavior with a named owner, clear logs, bounded inputs, and no sensitive credential dependency. When a team cannot justify why a command must run at startup, it usually does not need to run at startup.

Teams should also keep user-level agent configuration separate from repository-level configuration. User-level configuration is not automatically safe, but it is at least owned by the developer or organization rather than by every repository the developer opens. Repository-level configuration is more dangerous because it travels with the code and can be changed by anyone who can influence the repository. When repository configuration starts local tools, the review should ask why that behavior belongs in the repository instead of in a documented, organization-managed developer profile.

Good defaults should make the safe path convenient. Provide a disposable workspace template for unfamiliar repositories. Publish a short list of file families reviewers must inspect. Add code-owner routing for agent and editor configuration. Keep local credentials short-lived and scoped. Teach developers that workspace trust prompts are security decisions. Add a tripwire that flags high-signal execution shapes. None of these controls is dramatic on its own, but together they change the default from "open first, investigate later" to "inspect first, then grant trust deliberately."

```text
DAILY WORKFLOW MODEL

  Familiar repository with reviewed agent config:
    Open normally, keep command approval visible, and review config diffs in PRs.

  Unfamiliar repository from outside your trust boundary:
    Open in a disposable workspace, disable auto-run behavior, inspect configs,
    then decide whether to start an agent or run setup.

  Repository with new auto-exec config:
    Route for security review, require ownership and justification, and prefer
    manual setup unless automatic behavior is clearly necessary.
```

The maturity test is whether a rushed developer can still make the right choice. If the only safe workflow requires remembering a long security lecture, the system will fail under deadline pressure. If risky config changes are labeled, routed, blocked, and explained at the point of review, the team can keep using powerful AI tooling while reducing the chance that the tool becomes an unobserved execution path.

---

## Did You Know?

- **Agent-readable does not mean human-only**: a file can be documentation for a person, instruction for an AI assistant, and startup configuration for a local tool, all at the same time.
- **Auto-run timing changes severity**: the same setup command is materially riskier when it runs during folder open or session start than when it is documented as a manual command.
- **A tripwire is a review trigger, not a verdict**: the purpose is to make risky execution shapes visible before they become normalized, not to prove every flagged change is malicious.
- **Manual setup preserves a checkpoint**: forcing a developer to choose a reviewed command deliberately is safer than asking an assistant or editor to run setup before trust is established.

---

## Common Mistakes

| Mistake | Why It Is Dangerous | Better Approach |
|---|---|---|
| Treating `CLAUDE.md`, `AGENTS.md`, or rule files as harmless prose | Agent-readable instructions can change tool behavior, recommend commands, or hide risky setup behind ordinary wording | Review agent instruction files as authority-bearing configuration whenever they affect tool behavior |
| Approving folder-open tasks because they are "just developer convenience" | Folder-open execution can happen before the developer understands the repository or disables risky behavior | Require explicit justification, ownership, and sandbox-safe behavior for any auto-run task |
| Reviewing only the first config file in a chain | A visible rule may call a setup file, which calls another interpreter, which fetches unreviewed content | Follow every reference until the execution chain is fully understood |
| Relying on comments such as "required for IDE integration" | Social-engineered comments make malicious behavior look routine without proving necessity | Ask what command runs, why it must run automatically, and what happens if it is removed |
| Opening untrusted repos in a fully privileged daily workspace | Any auto-exec path can inherit local tokens, cloud credentials, SSH agents, and repository access | Use disposable sandboxes or devcontainers with no sensitive credentials for first inspection |
| Assuming provenance replaces review | A compromised account, dormant branch, or misleading timestamp can still produce a trusted-looking commit | Combine provenance checks with content review, branch policy, and high-signal tripwires |

---

## Quiz: Apply the Concepts

### Question 1

A pull request adds an AI assistant rule file that applies to every file in the repository and says the agent should run a project setup command before answering questions. The author says this is only documentation for the assistant. What is the security review issue?

<details>
<summary>Answer</summary>

The issue is that the file is not merely documentation if the assistant treats it as instruction. A broad always-apply rule that tells an agent to run setup creates an execution-adjacent path. The reviewer should ask what command runs, when it runs, why automatic execution is required, what the command can access, and whether the behavior can be replaced with explicit manual documentation.
</details>

### Question 2

Why is folder-open execution more concerning than a documented setup command that a developer runs manually after inspection?

<details>
<summary>Answer</summary>

Folder-open execution can occur before the developer has read the repository, reviewed agent configuration, checked package scripts, or decided to trust the workspace. A manual setup command creates a deliberate checkpoint. The same command may still need review, but the timing gives the developer a chance to inspect the behavior first.
</details>

### Question 3

A tripwire flags a new MCP server config in a repository. The config starts a local helper process, but the helper's source is not included in the pull request. What should the reviewer do?

<details>
<summary>Answer</summary>

The reviewer should treat the review as incomplete. An MCP server can become a tool execution and data-access boundary for the agent. The reviewer needs to know what process starts, where it comes from, what permissions it has, what files or network paths it can access, and who owns it. If the helper is fetched remotely or not reviewable, the safer outcome is to remove the auto-start behavior or require a narrow, documented exception.
</details>

### Question 4

What is the difference between a malware detector and a config-injection tripwire?

<details>
<summary>Answer</summary>

A malware detector tries to decide whether content is malicious. A config-injection tripwire identifies high-risk shapes, such as startup hooks, folder-open tasks, interpreter invocations, remote downloads, encoded blobs, or MCP auto-start in agent-config files. The tripwire does not need to prove malicious intent; it forces review when configuration begins to behave like executable code.
</details>

### Question 5

Why does least privilege matter on developer machines in this attack class?

<details>
<summary>Answer</summary>

If a malicious agent-config path executes locally, it can inherit whatever credentials are available to the developer environment. Broad GitHub tokens, package publish tokens, cloud credentials, Kubernetes contexts, and SSH agents all increase blast radius. Least privilege ensures that even if execution occurs, the stolen credential set cannot write broadly, publish widely, or reach sensitive systems unnecessarily.
</details>

### Question 6

A commit message claims to refactor application code, but the diff only adds editor tasks and agent hooks on a backdated commit in a branch that has been dormant for years. Why is that a provenance signal?

<details>
<summary>Answer</summary>

The story does not match the evidence. A mismatch between commit message, changed files, branch history, and execution capability suggests the change may be disguised. The reviewer should slow down, inspect the content, verify author and branch context, avoid opening the repository in a trusted environment, and escalate if the change cannot be explained by a legitimate owner.
</details>

---

## Learner check

Find the quoted sentence earlier in this module, then explain in your own words why the sentence changes how you review repository files that used to feel like harmless tool preferences.

> Agent configuration is executable supply-chain code because the tool, not the package manager, becomes the interpreter.

Your explanation should mention at least two trigger paths from the module and one defense that reduces blast radius if a trigger is missed.

---

## Hands-On Exercise: Review a Conceptual Agent-Config Change

This is a light conceptual exercise, not a runnable lab. Do not create a working payload, do not run unfamiliar setup commands, and do not test with real credentials. The goal is to practice review judgment using sanitized placeholders.

### Hypothetical scenario: PR summary

A teammate opens a pull request titled "Improve AI assistant onboarding for the repository." The PR adds a project instruction file, a workspace task, and an MCP server entry. The instruction file says the assistant should initialize the environment before answering questions. The workspace task is configured for folder-open timing. The MCP server entry starts a local helper through a package-manager command. The PR description says these changes are "required for proper IDE integration" and does not name an owner for the helper.

### Part 1: Classify the changed files

Create a short review note that classifies each changed file as text guidance, execution-adjacent configuration, direct execution, or tool-startup configuration. For each file, write one sentence explaining what trusted tool interprets it and whether the behavior is manual, suggested, or automatic.

### Part 2: Follow the execution chain

Write the chain you would inspect before approving the PR. Start with the instruction file, follow references to setup commands, then follow references to any helper process, remote content, interpreter, or package-manager invocation. If the chain leaves reviewable source, mark the review as incomplete and explain what evidence is missing.

### Part 3: Apply the tripwire approach

List which sanitized tripwire signals would fire: folder-open timing, startup or session behavior, interpreter or shell invocation, remote download, encoded content, broad always-apply rule, MCP auto-start, or package script indirection. For each signal, write whether it should block the PR, route for security review, or require a documented exception.

### Part 4: Decide the safer design

Rewrite the PR outcome in safer terms. You might replace automatic setup with manual documentation, move a helper behind an explicit developer command, require a devcontainer with no sensitive credentials, remove the MCP auto-start, or ask the author to provide a reviewed local script with a named owner and expiration date for any exception.

### Success Criteria

- [ ] You identified at least three execution-adjacent surfaces and explained which trusted tool interprets each one.
- [ ] You followed references beyond the first config file instead of stopping at a friendly setup label.
- [ ] You separated intent from capability by reviewing what the files can cause, not what the comments claim.
- [ ] You proposed a safer design that preserves developer experience without silent folder-open or agent-start execution.
- [ ] You included a least-privilege note describing which credentials should not be present when evaluating untrusted repositories.

---

## Sources

- [StepSecurity: Miasma worm hits Microsoft repositories](https://www.stepsecurity.io/blog/miasma-worm-hits-microsoft-again-azure-functions-action-and-72-other-repositories-disabled-after-supply-chain-attack-targeting-ai-coding-agents) - Primary report for the Microsoft Miasma incident in the case study (73 repositories across four organizations, the `Azure/durabletask` backdated commit, and the five trigger paths).
- [The Next Web: Miasma worm, Microsoft, and the GitHub supply chain](https://thenextweb.com/news/miasma-worm-microsoft-github-supply-chain) - News report corroborating the Microsoft Miasma incident (the Bun-based worm and clone-and-open execution).
- [SafeDep: Red Hat hit by mini-Shai-Hulud npm worm](https://safedep.io/redhat-cloud-services-hit-by-mini-shai-hulud-npm-worm/) - A separate but related campaign documenting the same AI-agent and editor config-injection pattern (`.claude/settings.json` SessionStart, `.vscode/tasks.json`); context for the attack class, not the Microsoft incident.
- [VS Code Workspace Trust](https://code.visualstudio.com/docs/editing/workspaces/workspace-trust) - Reference for editor workspace trust decisions and untrusted folder handling.
- [VS Code Tasks](https://code.visualstudio.com/docs/editor/tasks) - Reference for reviewing workspace task behavior and task-trigger configuration.
- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks) - Reference for understanding hook lifecycle concepts before approving hook-based project behavior.
- [Cursor Rules documentation](https://docs.cursor.com/context/rules) - Reference for project rule files and how assistant instructions are scoped.
- [Gemini CLI settings documentation](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/settings.md) - Reference for settings-file review in Gemini CLI workflows.
- [Model Context Protocol introduction](https://modelcontextprotocol.io/docs/getting-started/intro) - Reference for understanding why local tool-server configuration is part of the agent trust boundary.
- [GitHub CODEOWNERS documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) - Reference for routing sensitive configuration changes to the right reviewers.
- [GitHub personal access token management](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) - Reference for least-privilege and rotation practices around developer credentials.
- **Agent-config tripwire concept (defense pattern)** - The reusable idea, not any specific implementation: changed agent-config files should be scanned for high-signal auto-exec patterns and routed for deliberate review.

---

## Next Module

You have completed the DevSecOps discipline sequence. Continue by exploring the [Security Tools toolkit](../../../toolkits/security-quality/security-tools/) or return to the [DevSecOps index](../) to review earlier modules.
