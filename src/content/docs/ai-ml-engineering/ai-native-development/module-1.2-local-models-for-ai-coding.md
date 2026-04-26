---
title: "Local Models for AI Coding"
slug: ai-ml-engineering/ai-native-development/module-1.2-local-models-for-ai-coding
sidebar:
  order: 203
---

> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 3-4 hours

# Local Models for AI Coding

**Reading Time**: 3-4 hours

**Prerequisites**: Module 1.1 complete, comfort using a terminal, basic Git workflow, and at least 8 GB RAM. A 16 GB machine is strongly recommended for the examples in this module.

---

## Learning Outcomes

By the end of this module, you will be able to:

1. **Compare** local, API, and hybrid AI coding workflows against cost, privacy, latency, quality, and operational constraints.

2. **Design** a local-model setup using Ollama, Aider, and Continue.dev that matches a developer workstation's memory and workflow needs.

3. **Evaluate** when a coding task should stay local and when it should be escalated to a stronger API model.

4. **Debug** common local-model failures such as missing Ollama services, oversized model downloads, slow inference, and tool configuration errors.

5. **Implement** a repeatable hybrid workflow that uses local models for routine coding and API models for high-reasoning tasks.

---

## Why This Module Matters

Marcus was not trying to become an AI infrastructure engineer when his monthly API bill crossed three hundred dollars. He was trying to build an internal code analysis tool after work, and the cost grew quietly because every small experiment felt harmless. A prompt to generate tests became another prompt to revise the tests, which became another prompt to explain a failing edge case, which became another prompt to refactor the helper function.

By the time he looked at the credit card statement, the problem was no longer a single expensive request. The problem was that he had built a workflow where every tiny coding thought required a paid round trip to somebody else's server. His code left his machine, his work stopped when the network was unstable, and his budget depended on how often he experimented.

Local models changed the shape of that workflow. Marcus did not replace every API call, and that distinction matters. He started using local models for boilerplate, tests, documentation, small refactors, and exploratory prompts where speed and privacy mattered more than peak reasoning. He still used strong hosted models for architecture decisions and subtle debugging, but those calls became deliberate instead of automatic.

That is the senior-level lesson in this module. Local models are not magic, and they are not automatically better than hosted models. They are another execution environment for AI coding work, with different economics and constraints. A strong practitioner knows how to place the right task in the right environment, just as they know when to run a service locally, deploy it to staging, or hand it to a managed cloud service.

---

## 1. Build The Mental Model First

A local model is an AI model that runs on your machine instead of a provider's servers. The model weights are downloaded to disk, loaded into memory, and executed by your CPU, GPU, or Apple Silicon accelerator. Tools such as Ollama hide much of that complexity, but the basic trade-off remains: you exchange cloud cost and network dependency for local resource usage and setup responsibility.

API models are the opposite deployment shape. You send prompts and context to a provider, the provider runs inference on their infrastructure, and you receive the response over the network. This is usually faster to start, often stronger for complex reasoning, and easier to use across machines, but it introduces recurring cost, external data handling, rate limits, and dependency on internet access.

Hybrid workflows combine both. They use local models for high-volume, lower-risk, repetitive work and reserve API models for the smaller number of tasks where quality matters more than cost. This is the pattern most professional teams eventually land on because it treats AI coding like any other engineering resource: cheap capacity handles routine throughput, while expensive capacity is saved for decisions where quality changes the outcome.

```ascii
+-------------------------+       +---------------------------+
| Developer workstation   |       | Hosted model provider     |
|                         |       |                           |
|  Editor                 |       |  Large model runtime      |
|  Terminal               |       |  Managed GPUs             |
|  Git repository         |       |  Billing and rate limits  |
|                         |       |                           |
|  +-------------------+  |       |  +---------------------+  |
|  | Ollama            |  |       |  | API endpoint         |  |
|  | local model       |  |       |  | hosted model         |  |
|  +-------------------+  |       |  +---------------------+  |
|                         |       |                           |
+-----------+-------------+       +-------------+-------------+
            |                                   |
            | local requests                    | network calls
            v                                   v
+-------------------------------------------------------------+
| Hybrid workflow: choose local or API based on task risk      |
+-------------------------------------------------------------+
```

The important question is not "Are local models good enough?" That question is too broad to answer usefully. A better question is "Good enough for which task, on which machine, with which failure cost?" A local seven-billion-parameter coding model may be excellent for writing straightforward unit tests and poor for designing a security-sensitive authentication architecture. A hosted frontier model may be excellent for architecture but wasteful for converting a block of repeated assertions into a table-driven test.

**Stop and think:** If your team currently uses AI coding tools, which three tasks happen most often: generating tests, explaining code, refactoring files, designing architecture, debugging incidents, or writing documentation? Mark which of those tasks would still be acceptable if the answer were a little slower but free and private.

A useful analogy is the difference between a local development database and a managed production database. You do not expect SQLite on your laptop to behave like a globally replicated managed database, but you still use it constantly because it is fast to access, cheap, private, and enough for many development tasks. Local models occupy a similar role in AI coding. They are not the whole platform, but they can absorb a large amount of daily work.

The deployment model also changes behavior. When every prompt costs money, learners often under-experiment and accept the first answer that seems plausible. When local iteration is free, they can ask the model to produce alternatives, critique its own patch, generate tests, and compare designs without worrying about a meter running. That experimentation is valuable, but it must be paired with engineering judgment because a free wrong answer is still wrong.

| Deployment type | Where the model runs | Main advantage | Main risk | Best fit |
|---|---|---|---|---|
| Local | Your workstation | Privacy and predictable cost | Hardware limits and slower inference | Tests, docs, boilerplate, small refactors |
| API | Provider infrastructure | Strong quality and large context | Cost, network dependency, data handling | Architecture, subtle bugs, large analysis |
| Hybrid | Both local and API | Balanced cost and quality | Requires deliberate routing | Professional daily workflow |

The table shows why "local versus API" is a false binary for serious work. The real skill is task routing. You want a mental habit where you quickly classify a request before choosing a model. Routine, low-risk, repetitive, and privacy-sensitive tasks usually start local. High-risk, ambiguous, cross-system, or large-context tasks usually deserve an API model or at least a second pass from one.

---

## 2. Choose Models By Constraint, Not Hype

Most beginners choose local models by reputation, download size, or benchmark screenshots. That is understandable, but it leads to predictable problems. A model that looks impressive on a leaderboard may be unusable on an 8 GB laptop, and a model that fits comfortably may be weak for the task you are assigning it. The first practical constraint is memory, not marketing.

The model name often includes a size such as `7b`, `14b`, `16b`, or `32b`. The `b` means billions of parameters. More parameters can improve capability, but they also require more memory and usually run more slowly. Quantization reduces memory use by storing parameters in fewer bits, which is why a `7b` model can often fit in several gigabytes instead of requiring the full memory implied by raw sixteen-bit weights.

```ascii
+----------------------+----------------------+----------------------+
| Model size           | Typical workstation  | Practical expectation|
+----------------------+----------------------+----------------------+
| 3B to 4B             | 4 GB to 8 GB RAM     | Fast, limited depth  |
| 7B                   | 8 GB to 16 GB RAM    | Good daily driver    |
| 14B to 16B           | 16 GB to 24 GB RAM   | Better refactoring   |
| 22B to 32B           | 32 GB+ RAM or GPU    | Stronger, slower     |
| Very large models    | High-end GPU setup   | Not laptop-friendly  |
+----------------------+----------------------+----------------------+
```

Treat these numbers as operational estimates, not guarantees. The exact memory footprint depends on quantization, context length, runtime settings, and what else is running on your machine. A developer with 16 GB RAM may run a `16b` model acceptably when the editor and browser are modest, then experience heavy swapping when a container stack and many browser tabs are also open.

For this module, start with `qwen2.5-coder:7b` because it is a practical default for many learners. It is small enough to run on common developer machines while still being useful for coding tasks. If you have 16 GB RAM or more, add `deepseek-coder-v2:16b` as a higher-quality option for more difficult refactors. If your machine is constrained, use a smaller model and route complex work to an API.

| Situation | Recommended local model | Why this choice works | When to escalate |
|---|---|---|---|
| 8 GB laptop | `qwen2.5-coder:7b` or smaller | Fits common machines and handles routine coding | Architecture, large context, subtle bugs |
| 16 GB laptop | `qwen2.5-coder:7b` plus `deepseek-coder-v2:16b` | Balances speed and quality | Security design or complex debugging |
| 32 GB workstation | `qwen2.5-coder:32b` or similar larger model | Better output for heavier code tasks | Whole-repo reasoning or high-stakes decisions |
| Low-resource machine | `phi3.5:3.8b` or another small model | Fast enough for simple prompts | Most production-quality coding decisions |

A senior practitioner also considers context size. A local model may answer well when you give it one function, but degrade when you paste several files and ask for a design decision. Hosted models often support larger context windows and stronger retrieval workflows. If the task depends on understanding many modules, a local model might still help summarize individual files, but the final integration decision may belong to a stronger model or a human review.

**Stop and think:** Suppose a local model generates a correct-looking patch for a billing calculation. The patch is small, the tests pass, and the model explains itself confidently. What extra evidence would you require before merging if the code affects real customer invoices? Your answer should include more than "use a bigger model."

The answer is engineering evidence: focused tests, edge-case analysis, code review, and comparison against the business rule. Model choice is only one layer of quality control. Local models lower the cost of producing candidate changes, but they do not lower the standard for accepting those changes.

---

## 3. Install Ollama And Run A First Coding Model

Ollama is a local model runtime and model manager. It downloads model artifacts, runs an inference server, exposes a local API, and provides a command-line interface. You can think of it as the part of the system that turns "run this model" into an actual process listening on your machine.

On macOS, Homebrew is the simplest installation path for many developers. On Linux, the official install script is common, and systemd may manage the service after installation. On Windows, the installer provides the same command-line interface through PowerShell. Use the installation method that matches your operating system and verify with `ollama --version` before moving on.

```bash
# macOS with Homebrew
brew install ollama

# Verify the CLI is available
ollama --version
```

```bash
# Linux installation
curl -fsSL https://ollama.com/install.sh | sh

# Verify the CLI is available
ollama --version

# Start the service if your installation did not start it automatically
sudo systemctl start ollama
```

```powershell
# Windows verification after installing Ollama
ollama --version
```

After the CLI is available, pull a coding model. The first download can take several minutes because model files are large. Choose one model first, test it, and only then add more. Downloading five models before you know which one fits your workflow wastes disk space and makes troubleshooting harder.

```bash
# Pull a practical coding model for daily work
ollama pull qwen2.5-coder:7b

# Confirm the model is installed
ollama list
```

A successful `ollama list` output should show the model name, an ID, a size, and the modification time. If the command fails, solve that before configuring editor tools. Aider and Continue.dev depend on the Ollama service, so debugging the editor first wastes time when the runtime itself is not healthy.

```bash
# Run the model interactively
ollama run qwen2.5-coder:7b

# At the prompt, ask for a small coding task
# Write a Python function named is_palindrome that ignores spaces and case.
```

Here is a worked example of how to evaluate the first response. Do not only ask "Did it produce code?" Ask whether the code matches the requirement, whether it handles edge cases, and whether it is simple enough to maintain. Local models can produce useful code, but you should train yourself to inspect outputs immediately.

```python
def is_palindrome(text: str) -> bool:
    normalized = "".join(char.lower() for char in text if not char.isspace())
    return normalized == normalized[::-1]
```

This answer handles spaces and case, but it does not ignore punctuation. That is acceptable only if the requirement truly says spaces and case, not all non-alphanumeric characters. A careful reviewer might add tests before accepting it. The important habit is to treat the model output as a candidate implementation, not as proof.

```bash
# Create a quick test file to validate the behavior
cat > test_palindrome.py <<'EOF'
from palindrome import is_palindrome

def test_ignores_spaces_and_case():
    assert is_palindrome("Never odd or even")

def test_detects_non_palindrome():
    assert not is_palindrome("local model")
EOF
```

The command above writes a small test file, but in a real project you would use the repository's existing test framework and style. The goal is not to create isolated toy files forever. The goal is to connect the model's output to verification as quickly as possible.

**Stop and think:** Before you run a local model on a real repository, what files would you add to the prompt and what files would you leave out? Consider whether the model needs implementation files, tests, configuration, logs, or secrets, and justify each choice.

Local execution improves privacy because prompts do not leave your machine through a model provider API. It does not remove every privacy risk. If you paste secrets into terminal history, commit generated files containing credentials, or use plugins that call external services, you can still leak sensitive data. Local models are one part of a privacy posture, not a complete security program.

---

## 4. Connect Local Models To Coding Tools

Running `ollama run` proves that the model works, but most coding value appears when the model is connected to tools that understand files, diffs, and editor context. Two common tools are Aider for terminal-based pair programming and Continue.dev for editor-integrated assistance. They solve different workflow problems, so many developers use both.

Aider is useful when you want the model to edit files directly in a Git repository. It can read selected files, propose patches, apply changes, and create commits. This makes it powerful, but also means you should use it inside a clean repository state whenever possible. If your working tree already has unrelated changes, review them before inviting an AI tool to edit nearby files.

```bash
# Install Aider in your normal Python tool environment
pip install aider-chat

# Verify the command is available
aider --version
```

```bash
# Start Aider with a local Ollama model
aider --model ollama/qwen2.5-coder:7b

# Start Aider with a specific file in context
aider --model ollama/qwen2.5-coder:7b src/example.py
```

A useful first Aider task is narrow and testable. Instead of asking "Improve this project," ask for one function, one bug, or one test gap. Local models perform better when the prompt is concrete, the context is small, and the acceptance criteria are explicit.

```text
Add table-driven tests for parse_duration in src/time_utils.py.
Cover seconds, minutes, hours, and invalid input.
Do not change production code unless a test exposes a bug.
```

That prompt gives the model a role, a target file, coverage expectations, and a constraint. If the model changes production code unnecessarily, you have a clear reason to reject or revise the patch. Good prompts are not long because they are verbose; they are long enough to define the engineering contract.

Aider can also use a configuration file so you do not repeat the model flag on every command. The exact options evolve across Aider versions, so treat this as a starting point and confirm against the installed version if an option fails. The key idea is to make the local path easy enough that you use it by default for routine tasks.

```yaml
# ~/.aider.conf.yml
model: ollama/qwen2.5-coder:7b
auto-commits: true
show-diffs: true
pretty: true
```

Continue.dev solves a different problem by bringing local models into VS Code and compatible editor workflows. It can provide chat, inline editing, and autocomplete-style assistance depending on configuration. The main failure mode is assuming Continue is broken when Ollama is not running or the configured model name does not match `ollama list`.

```json
{
  "models": [
    {
      "title": "Qwen 2.5 Coder Local",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "apiBase": "http://127.0.0.1:11434"
    },
    {
      "title": "DeepSeek Coder Local",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "apiBase": "http://127.0.0.1:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen Autocomplete",
    "provider": "ollama",
    "model": "qwen2.5-coder:7b",
    "apiBase": "http://127.0.0.1:11434"
  }
}
```

The `apiBase` value points to the local Ollama server. Using `127.0.0.1` makes the local network boundary explicit, which is helpful when teaching and debugging. If your tool documentation shows `localhost`, the intent is the same for most developer machines, but consistency makes configuration easier to reason about.

```ascii
+----------------------+       +---------------------+
| VS Code / Continue   |       | Terminal / Aider    |
|                      |       |                     |
| Chat with file ctx   |       | Patch files in Git  |
| Inline edits         |       | Show diffs          |
| Autocomplete         |       | Commit changes      |
+----------+-----------+       +----------+----------+
           |                              |
           | HTTP to local runtime        | HTTP to local runtime
           v                              v
+----------------------------------------------------+
| Ollama server on 127.0.0.1:11434                   |
|                                                    |
| Loaded model: qwen2.5-coder:7b                     |
| Optional model: deepseek-coder-v2:16b              |
+----------------------------------------------------+
```

**Stop and think:** Which interface should you use for a change that touches four files and must be reviewed as a Git diff: editor chat, inline editing, or Aider? Which interface should you use for quickly asking what a selected function does? Explain the workflow reason, not just the tool name.

The practical split is straightforward. Use Continue when you are reading, asking questions, applying small inline edits, or using editor context. Use Aider when you want a deliberate patch across files and expect Git integration. Use raw `ollama run` when you are testing a model, experimenting with prompts, or isolating whether the runtime works before blaming another tool.

---

## 5. Route Tasks With A Hybrid Strategy

A local model is most valuable when it becomes part of a routing strategy. Without routing, teams swing between two bad habits. They either send every task to the most expensive model because it feels safest, or they force every task through a local model because it feels cheapest. Both habits waste something important.

A good hybrid strategy starts by classifying the task. Ask whether the work is routine or novel, low-risk or high-risk, small-context or large-context, private or shareable, and reversible or hard to undo. This classification is faster than it sounds once the team practices it. It becomes a short design reflex before choosing the model.

| Task type | Start with local? | Escalate to API when | Verification required |
|---|---|---|---|
| Generate unit tests | Yes | Test logic is domain-heavy or security-sensitive | Run tests and inspect assertions |
| Write boilerplate | Yes | Framework behavior is unfamiliar or production-critical | Compile, lint, and review diff |
| Explain one function | Yes | Explanation affects incident response or compliance | Compare with code and logs |
| Refactor one module | Usually | Behavior is subtle or many callers are involved | Tests, diff review, possibly API second pass |
| Design architecture | Usually no | Local may draft alternatives, but final needs stronger reasoning | Human design review and constraints check |
| Debug production issue | Sometimes | Impact is high, context is broad, or time pressure is severe | Logs, reproduction, rollback plan |

The phrase "start with local" does not mean "trust local." It means local is allowed to produce the first draft. For low-risk tasks, that first draft may be enough after tests and review. For high-risk tasks, the local draft can still be useful as a sketch, but the final decision needs stronger evidence.

A common pattern is "local for iteration, API for judgment." For example, a developer might ask a local model to generate three possible test structures for a parser, then choose one and refine it manually. Later, if the parser handles a complex production format and failures are expensive, the developer might ask a stronger API model to review the final test strategy for missing classes of input.

```bash
# Local model for routine implementation
aider --model ollama/qwen2.5-coder:7b src/user_profile.py tests/test_user_profile.py

# Higher-quality local model for a more difficult refactor
aider --model ollama/deepseek-coder-v2:16b src/billing_rules.py tests/test_billing_rules.py

# API model only when the task needs stronger reasoning or broad context
aider --model gemini/gemini-2.5-flash src/auth_design.md src/auth_service.py
```

Cost control is not only about reducing the bill. It is about making experimentation cheap enough that developers can ask better questions. If a local model can generate ten variants for no token cost, the developer can compare approaches, find edge cases, and sharpen the final prompt before using a paid model. That often improves the paid model's answer because the expensive request becomes more specific.

```python
def estimate_monthly_api_savings(
    local_sessions_per_week: int,
    average_tokens_per_session: int,
    api_cost_per_million_tokens: float,
) -> float:
    weekly_tokens = local_sessions_per_week * average_tokens_per_session
    monthly_tokens = weekly_tokens * 4
    return (monthly_tokens / 1_000_000) * api_cost_per_million_tokens


if __name__ == "__main__":
    savings = estimate_monthly_api_savings(
        local_sessions_per_week=25,
        average_tokens_per_session=8_000,
        api_cost_per_million_tokens=3.0,
    )
    print(f"Estimated monthly API cost avoided: ${savings:.2f}")
```

This calculator is intentionally simple. Real pricing distinguishes input tokens, output tokens, cache hits, and model tiers. The purpose is not perfect accounting; the purpose is to make the hidden cost of frequent experimentation visible. Once you can estimate the cost, you can choose deliberately instead of reacting to a surprise invoice.

**Stop and think:** A local model proposes a refactor that reduces duplicate code but changes the order of validation errors returned by an API. Is this a local-model problem, a prompt problem, or a review problem? Decide what you would do before reading the next paragraph.

It is primarily a review problem. The model may have followed a reasonable refactoring instinct while missing an externally observable behavior. A better prompt could have said "preserve error order," and a stronger model might have noticed the contract, but the team's acceptance process must catch this. Hybrid AI coding does not remove the need to define compatibility constraints before refactoring.

---

## 6. Debug And Operate The Local Workflow

Local AI coding introduces a small operational surface area. You now have a runtime service, downloaded model artifacts, editor configuration, terminal tools, memory pressure, and sometimes GPU acceleration. The upside is control; the cost is that you must debug the stack when something breaks.

Start every diagnosis at the bottom of the stack. If Continue.dev cannot find a model, first verify Ollama. If Aider is slow, first check whether the model is too large for available memory. If responses are low quality, first check whether the task is too complex for the selected model before assuming local models are useless.

```bash
# Confirm Ollama is installed
ollama --version

# Confirm the service responds and models are available
ollama list

# Pull a missing model if needed
ollama pull qwen2.5-coder:7b

# Run a direct test outside editor tools
ollama run qwen2.5-coder:7b "Write a Python function that adds two integers."
```

The direct test matters because it separates runtime problems from integration problems. If `ollama run` fails, Continue and Aider are not the right place to debug. If `ollama run` works but Continue fails, check the model name, provider, and `apiBase`. If Continue works but autocomplete is slow, try a smaller model for tab completion and keep the larger model for chat.

```ascii
+-----------------------------+
| Tool reports model failure  |
+--------------+--------------+
               |
               v
+-----------------------------+
| Does ollama list work?      |
+-------+---------------------+
        | yes
        v
+-----------------------------+
| Does ollama run model work? |
+-------+---------------------+
        | yes
        v
+-----------------------------+
| Check tool config:          |
| provider, model, apiBase    |
+-----------------------------+

If any earlier check fails, fix Ollama before editing tool settings.
```

Memory pressure has a distinct feel. The machine becomes sluggish, fans increase, responses take much longer than expected, and other applications pause because the operating system is swapping memory to disk. The fix is usually not a clever prompt. The fix is to use a smaller model, reduce context size, close memory-heavy applications, or move the task to an API model.

```bash
# Remove a model that is too large for your machine
ollama rm deepseek-coder-v2:236b

# Keep a practical daily model instead
ollama pull qwen2.5-coder:7b
```

Quality problems require a different diagnosis. Ask whether the prompt included enough context, whether the model was asked to perform reasoning beyond its capability, whether the task needs tests, and whether the output was evaluated against the real acceptance criteria. Many "bad model" experiences are actually context failures, vague prompts, or attempts to use a small model for senior-level design.

A useful escalation rule is to switch models when the failure mode repeats after one good prompt revision. If the first answer is weak because your prompt was vague, improve the prompt and try again. If the second answer is still weak on a well-scoped task, change the model or route the task to an API. Repeating the same weak request wastes time even when tokens are free.

```bash
# Smaller, faster model for quick tasks
aider --model ollama/qwen2.5-coder:7b tests/test_parser.py

# Stronger local model for more demanding refactoring
aider --model ollama/deepseek-coder-v2:16b src/parser.py tests/test_parser.py

# API fallback when the reasoning risk is higher than the local model can handle
aider --model gemini/gemini-2.5-flash src/parser.py tests/test_parser.py docs/parser-contract.md
```

The senior move is to make these decisions visible to the team. Document which local model is the daily default, which one is the heavier local option, which API model is approved for escalation, and what kinds of code must not be sent to external providers. Without that shared agreement, each developer invents their own policy, and the team's privacy and cost posture becomes accidental.

---

## Did You Know?

1. Ollama exposes a local HTTP API by default, which is why editor tools can talk to it without each tool implementing its own model runtime.

2. Quantization is the reason many local models fit on ordinary developer machines; it stores model weights with fewer bits while accepting some quality trade-off.

3. Local execution can improve code privacy, but it does not protect secrets from terminal history, editor plugins, logs, screenshots, or accidental commits.

4. The best hybrid workflows often reduce paid model usage by making the expensive prompt more specific after local experimentation has clarified the problem.

---

## Common Mistakes

| Mistake | What it looks like | Why it causes trouble | Better practice |
|---|---|---|---|
| Downloading the largest model first | A developer pulls a huge model onto a laptop and the machine becomes unresponsive | Model size must match memory, or the operating system starts swapping heavily | Start with `qwen2.5-coder:7b`, then add larger models only after measuring performance |
| Treating local output as automatically safe | A local model writes plausible code and the developer merges without tests | Local privacy does not equal correctness, and generated code can still break contracts | Run tests, inspect diffs, and review behavior against acceptance criteria |
| Using a small model for architecture decisions | A team asks a 7B model to design authentication, authorization, and audit logging | Small models can miss cross-system constraints and security implications | Use local models for drafts, then escalate high-risk design decisions |
| Debugging the editor before the runtime | Continue.dev says a model is missing, so the developer repeatedly edits JSON config | If Ollama is not running or the model was not pulled, editor settings cannot fix it | Verify `ollama list` and `ollama run` before changing tool configuration |
| Sending too much context | The prompt includes entire files, logs, and unrelated documentation | Local models have limited context and may focus on irrelevant details | Provide the smallest set of files needed for the decision |
| Never escalating to API models | The team insists on local-only even when results are repeatedly weak | Free iteration becomes expensive in developer time and review risk | Escalate after a good prompt revision still fails |
| Ignoring operational cost | A laptop runs hot for long sessions during every coding task | Local inference uses electricity, memory, and developer time even when token cost is zero | Use smaller models for frequent tasks and reserve heavier models for harder work |
| Forgetting team policy | Each developer chooses different tools, models, and data-sharing habits | Cost, privacy, and review expectations become inconsistent | Document approved local models, API fallback rules, and data restrictions |

---

## Quiz

**Q1.** Your team works on proprietary payment code and wants AI help generating unit tests. The tests are repetitive, the repository is private, and developers will run the normal test suite afterward. Which model routing decision should you make, and what verification still remains necessary?

<details>
<summary>Answer</summary>

Start with a local model because the task is repetitive, privacy-sensitive, and easy to verify with tests. The remaining verification is still essential: inspect the generated assertions, run the project's test suite, and confirm the tests check meaningful behavior rather than simply mirroring the implementation. Local execution reduces data exposure and token cost, but it does not prove the generated tests are useful.

</details>

**Q2.** A developer with an 8 GB laptop pulls a large model because a benchmark says it performs well. After starting the model, the editor freezes, the terminal lags, and responses take a very long time. What is the most likely root cause, and how should the developer recover?

<details>
<summary>Answer</summary>

The most likely cause is memory pressure from running a model that is too large for the machine. The developer should stop using that model, remove it if necessary with `ollama rm`, and switch to a smaller daily model such as `qwen2.5-coder:7b` or another model that fits comfortably. For complex tasks that exceed the laptop's local capacity, they should escalate to an API model instead of forcing the local machine to swap.

</details>

**Q3.** Continue.dev reports that `qwen2.5-coder:7b` cannot be found, but the configuration looks correct at first glance. What diagnostic sequence should you follow before changing more editor settings?

<details>
<summary>Answer</summary>

First run `ollama list` to verify that Ollama is installed, running, and aware of the model. Then run `ollama run qwen2.5-coder:7b` with a tiny prompt to confirm the model works outside the editor. Only after those checks pass should you inspect Continue.dev configuration for provider, exact model name, and `apiBase`. This sequence isolates the runtime from the editor integration.

</details>

**Q4.** A local model writes a refactor that removes duplicate code but changes the order of validation errors returned by a public API. The test suite still passes because no test checks error ordering. How should the team respond?

<details>
<summary>Answer</summary>

The team should treat this as a review and test-coverage issue, not merely a model issue. They should decide whether error ordering is part of the API contract, add or update tests to capture the expected behavior, and revise or reject the refactor if it breaks compatibility. A stronger model might have noticed the risk, but the acceptance process must define and verify externally visible behavior.

</details>

**Q5.** Your team needs help designing a new authorization model, implementing straightforward data classes, generating unit tests, and writing documentation. How should you split the work between local and API models?

<details>
<summary>Answer</summary>

Use an API model or a strong reviewed design process for the authorization model because it is high-risk and reasoning-heavy. Use local models for the straightforward data classes, unit test drafts, and documentation because those tasks are more repetitive and easier to verify. The key is not local-only or API-only; it is routing each task based on risk, context size, and verification cost.

</details>

**Q6.** A teammate says local models are useless because a 7B model produced poor advice for a large cross-repository migration. What question should you ask before accepting that conclusion, and what routing change might you recommend?

<details>
<summary>Answer</summary>

Ask whether the task was appropriate for the selected model and context window. A large cross-repository migration requires broad context, careful sequencing, and higher-level reasoning, so a small local model may be the wrong tool. The teammate could still use local models to summarize individual files or draft mechanical changes, but the migration plan should be reviewed by a stronger API model and humans familiar with the system.

</details>

**Q7.** A developer uses a local model to generate tests for a parser and then asks an API model to review the final test strategy. Why can this be better than sending the whole task to the API immediately?

<details>
<summary>Answer</summary>

Local iteration lets the developer explore test cases, clarify edge conditions, and produce a concrete draft without paying for every experiment. The later API review can focus on a sharper question: whether the drafted strategy misses important input classes or behavioral risks. This often reduces cost while improving the quality of the expensive request because the prompt is more specific and evidence-rich.

</details>

**Q8.** During a flight, a developer needs AI assistance for code explanation and small refactors, but cannot access the internet. The same repository contains sensitive internal logic. What setup would have prevented the interruption, and what limits should the developer still remember?

<details>
<summary>Answer</summary>

A local Ollama setup with a suitable coding model, connected to Aider or Continue.dev, would allow code explanation and small refactors without internet access and without sending prompts to a hosted model provider. The developer should still remember local models have limited context and capability compared with stronger API models, and generated changes still require tests and review before being trusted.

</details>

---

## Hands-On Exercise

In this exercise, you will build a small local-model workflow and make a routing decision the way a professional team would. You do not need a production repository; a small Git repository with one or two source files is enough. The goal is to practice setup, verification, task routing, and review rather than to produce a large application.

### Scenario

Your team maintains a small Python utility library. You want to use AI assistance to add tests and improve one function, but the repository is private and the team wants to avoid unnecessary API usage. You will start with a local model, verify the runtime, use a coding tool, and then decide whether escalation is justified.

### Step 1: Verify The Runtime

Run the following commands and record what each one proves. If a command fails, fix that layer before continuing to the next step. Do not configure editor tooling until the model works directly.

```bash
ollama --version
ollama list
ollama pull qwen2.5-coder:7b
ollama run qwen2.5-coder:7b "Write a Python function that validates an email-like string."
```

Success criteria:

- [ ] You can explain whether Ollama is installed, running, and able to execute the selected model.

- [ ] You can identify the exact model name shown by `ollama list`.

- [ ] You have confirmed the model can answer a direct coding prompt outside any editor integration.

### Step 2: Create A Small Test Target

Create or choose a small function with behavior that can be tested. The example below is intentionally simple, but it includes enough edge cases to make test generation meaningful.

```python
# src/durations.py
def parse_duration_seconds(value: str) -> int:
    text = value.strip().lower()

    if text.endswith("ms"):
        return int(text[:-2]) // 1000

    if text.endswith("s"):
        return int(text[:-1])

    if text.endswith("m"):
        return int(text[:-1]) * 60

    if text.endswith("h"):
        return int(text[:-1]) * 3600

    raise ValueError(f"Unsupported duration: {value}")
```

Success criteria:

- [ ] You have a function with at least four valid input categories and one invalid category.

- [ ] You can describe one edge case the current implementation handles poorly or ambiguously.

- [ ] You have initialized a Git repository or are working inside an existing one where diffs can be reviewed.

### Step 3: Ask A Local Model For Tests

Use Aider or your editor integration to ask for tests. Your prompt should include constraints, not just a general request. For example, ask for table-driven tests, invalid input coverage, and no production-code changes unless a test reveals a bug.

```text
Add pytest tests for parse_duration_seconds.
Cover milliseconds, seconds, minutes, hours, whitespace, uppercase suffixes, and invalid input.
Do not change production code unless a test exposes behavior that contradicts the intended contract.
Show the diff before committing.
```

Success criteria:

- [ ] The model produced tests rather than only explaining what tests could exist.

- [ ] You inspected the generated assertions and removed or revised any weak tests.

- [ ] You ran the tests with your project's normal test command.

- [ ] You can explain whether any production-code change was necessary.

### Step 4: Make A Routing Decision

Now classify the task. Decide whether the local model was sufficient or whether escalation to an API model is justified. Your answer should refer to task risk, context size, model output quality, and verification evidence.

Use this structure:

```text
Task:
Local model used:
Evidence collected:
Risk level:
Decision:
Reason:
```

Success criteria:

- [ ] Your routing decision is based on evidence, not preference.

- [ ] You identify at least one situation that would cause you to escalate the same task.

- [ ] You identify at least one situation where staying local is clearly the better choice.

### Step 5: Document A Team Workflow

Write a short team policy for local AI coding. Keep it practical enough that another developer could follow it without attending a meeting.

Your policy should include:

- [ ] Default local model for routine tasks.

- [ ] Heavier local model or API fallback for complex tasks.

- [ ] Examples of tasks that must not be sent to external APIs.

- [ ] Required verification before accepting generated code.

- [ ] Troubleshooting sequence for "model not found" or slow inference.

### Completion Checklist

You are ready for the next module when the following are true:

- [ ] You can run a local coding model through Ollama.

- [ ] You can connect at least one coding tool to that local model.

- [ ] You can choose between local, API, and hybrid routing for a realistic coding task.

- [ ] You can debug the first three layers of failure: runtime, model availability, and tool configuration.

- [ ] You can explain why local models reduce cost and improve privacy without making generated code automatically correct.

---

## Next Module

Next: **Module 1.3: Prompt Engineering Fundamentals**

In the next module, you will learn how to write prompts that produce better code, better tests, and better reviews across both local and API models. The workflow from this module gives you the execution environment; prompt engineering gives you the control surface for using that environment well.

---

## Sources

- [Ollama README](https://github.com/ollama/ollama) — Primary upstream entry point for installing Ollama and understanding how local model runtimes work.
- [Aider README](https://github.com/Aider-AI/aider) — Primary upstream reference for using Aider with cloud and local models.
- [DeepSeek-R1 model card](https://huggingface.co/deepseek-ai/DeepSeek-R1) — Useful primary source for current open reasoning-model capabilities and distilled local variants.
