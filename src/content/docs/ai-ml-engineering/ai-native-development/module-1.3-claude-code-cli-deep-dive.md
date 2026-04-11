---
title: "Claude Code & CLI Deep Dive"
slug: ai-ml-engineering/ai-native-development/module-1.3-claude-code-cli-deep-dive
sidebar:
  order: 204
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 4-5
# Or: The 90% of Claude Code You've Been Missing

**Reading Time**: 4-5 hours
**Prerequisites**: Module 1.1, Claude Code installed and working

---

## The Night That Changed Everything: When a Bug Fixed Itself

**San Francisco. March 14, 2024. 11:47 PM.**

Maya Chen, a senior engineer at a YC-backed fintech startup, was ready to give up. For three days, she'd been hunting a race condition in their payment processing pipeline. The bug was subtle—it only appeared under specific load conditions and left no useful stack trace. Her team had tried everything: additional logging, stress testing, even bringing in a consultant. Nothing worked.

"I'll just let it run overnight," she muttered, typing one last command into her terminal:

```bash
claude "Find and fix the race condition in src/payments/processor.py.
The bug causes duplicate transactions under high load."
```

She expected Claude Code to ask clarifying questions, maybe find some clues. Instead, she went home, defeated.

**7:23 AM the next morning.**

Maya's phone buzzed. Slack notification from her co-founder: "Did you push a fix overnight? The race condition is gone."

She opened her laptop. Claude Code had been busy. In her terminal, she found a detailed analysis:

```
Analysis Complete:
- Root cause: AtomicCounter in line 847 wasn't actually atomic
- The counter used += which isn't thread-safe in Python
- Added threading.Lock() around critical section
- Added unit test reproducing the race condition
- All existing tests still pass

Files modified:
- src/payments/processor.py (2 changes)
- tests/test_processor.py (1 new test)

Time elapsed: 4 hours, 23 minutes
Tokens used: 127,432
```

Maya stared at the diff. The fix was elegant—exactly what a senior engineer would have done, but arrived at through methodical exploration rather than intuition. Claude had:
1. Read and understood 50,000 lines of codebase context
2. Identified 12 potential race condition candidates
3. Created test harnesses for each
4. Reproduced the bug in isolation
5. Fixed it with minimal code changes

**That morning, Maya became a believer.** Not in AI replacing engineers—but in AI as the most powerful debugging partner she'd ever had.

This is the story of Claude Code: a tool that started as an internal research project and became the most sophisticated AI coding assistant ever built. In this module, you'll learn to wield it like Maya—not as a chatbot, but as an autonomous development platform.

What makes Claude Code different from other AI assistants? Three things distinguish it from competitors like GitHub Copilot or ChatGPT:

**First, it operates on your codebase, not just your code.** When you ask Claude Code a question, it doesn't just analyze the file you're looking at. It can read your entire repository, understand your architectural patterns, recognize your coding conventions, and see the relationships between components. This contextual awareness means it can suggest changes that fit your codebase, not just changes that work in isolation.

**Second, it can take autonomous action.** Unlike assistants that only suggest changes, Claude Code can actually implement them. It runs commands, creates files, modifies code, and executes tests. This transforms it from an advisor into an executor—a pair programmer who doesn't just tell you what to do, but does it alongside you.

**Third, it's designed for safety and control.** The elaborate permission system, hooks, and approval workflows aren't afterthoughts—they're core to the design. You can give Claude Code full autonomy in sandboxed environments, or require approval for every action in production. This flexibility makes it suitable for everything from personal projects to enterprise environments.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Master Claude Code's multi-modal operation (Interactive, Print, Plan)
- Configure settings.json and CLAUDE.md for maximum productivity
- Build custom slash commands and skills
- Implement hooks for deterministic automation
- Set up MCP integrations for external tools
- Design sub-agents for specialized tasks
- Optimize your workflow for cost and efficiency

---

## Why This Module Matters The Difference Between Users and Operators

Think of Claude Code like a commercial aircraft. Passengers (casual users) sit in the cabin, buckle up, and enjoy the flight. They interact with the system through simple interfaces: call buttons, tray tables, entertainment screens. But in the cockpit, pilots (power users) have access to thousands of controls, automated systems, and customizable settings that transform the same aircraft into a precision instrument.

**Most developers are passengers.** They type prompts, wait for responses, copy-paste code. They're using maybe 10% of Claude Code's capabilities.

**This module makes you a pilot.** You'll learn the systems that power users leverage:

- **Memory systems** that persist context across sessions like a copilot's flight log
- **Hooks** that automate approval workflows like autopilot controls
- **Custom commands** that encode team patterns like checklists
- **Sub-agents** that specialize in domains like different crew members
- **MCP integrations** that connect to external systems like radio communications

**The difference isn't subtle.** Casual users type prompts. Power users build systems. Casual users ask questions. Power users create autonomous workflows. Casual users wait for responses. Power users run pipelines.

> "Claude Code is like having a senior engineer who never sleeps, never forgets context, and can instantly access any file in your codebase. But only if you learn to direct it properly."
> — A developer on Hacker News, November 2024

Consider the economics of expertise. A junior developer types prompts and waits. They spend 30 seconds typing, 5 minutes waiting, 2 minutes reading output, and 10 minutes implementing the suggestion—nearly 18 minutes per interaction. A power user creates a slash command that encapsulates the entire workflow. Now that same task takes 2 seconds to invoke and runs autonomously. If you perform 50 such interactions per day, that's the difference between 15 hours and 2 minutes of effort.

The compound effects are staggering. Teams that invest in customizing Claude Code report productivity gains of 3-5x within months. Not because Claude is smarter for them, but because they've learned to leverage its full capabilities. The modules that follow teach you every lever, every configuration option, and every hidden feature that separates casual users from power users.

---

## Core Architecture: Understanding the Machine

### The Four Modes of Operation

Claude Code operates in distinct modes, like a car with different driving modes (Eco, Sport, Off-road). Each mode is optimized for different workflows:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE MODES                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. INTERACTIVE MODE (Default)                                          │
│     └─ Full conversation with history, multi-turn reasoning             │
│     └─ Command: claude                                                  │
│     └─ Use: Development sessions, complex tasks                         │
│                                                                         │
│  2. PRINT MODE (-p flag)                                                │
│     └─ Single query, output to stdout, exits immediately                │
│     └─ Command: claude -p "query" or cat file | claude -p "analyze"     │
│     └─ Use: Scripts, pipelines, CI/CD, automation                       │
│                                                                         │
│  3. PLAN MODE                                                           │
│     └─ Exploration without execution, requires approval                 │
│     └─ Command: /plan or start session in plan mode                     │
│     └─ Use: Safe exploration, architectural decisions                   │
│                                                                         │
│  4. EXTENDED THINKING                                                   │
│     └─ Deep reasoning for complex problems                              │
│     └─ Command: Toggle in settings or request explicitly                │
│     └─ Use: Architecture, debugging complex issues                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Think of these modes like a surgeon's different approaches:
- **Interactive Mode** is like a full surgery with ongoing dialogue between surgeon and team
- **Print Mode** is like a quick biopsy—in, out, done
- **Plan Mode** is like pre-operative planning with imaging and consultation
- **Extended Thinking** is like calling in a specialist for a complex case

### Essential CLI Commands

```bash
# Start and Resume
claude                        # Start interactive REPL
claude "initial prompt"       # Start with query
claude -c                     # Continue last session
claude -r "session-id"        # Resume specific session

# Print Mode (Non-interactive)
claude -p "query"             # Single query, stdout output
cat file.py | claude -p "explain"   # Pipe input
git diff | claude -p "review"       # Common pattern

# Configuration
claude config                 # View/edit config
claude mcp list               # Show MCP servers
claude mcp add <name> <url>   # Add MCP server

# Session Management
/clear                        # Clear conversation
/compact                      # Compress history
/cost                         # Show token usage
/status                       # Model and account info
```

**Print mode deserves special attention.** It transforms Claude Code from an interactive assistant into a Unix tool that plays nicely with pipes and scripts. This is the mode that lets you do things like:

```bash
# Analyze a log file
cat error.log | claude -p "What's causing these 500 errors?"

# Generate commit messages
git diff --staged | claude -p "Write a conventional commit message"

# Document code on the fly
cat complex_function.py | claude -p "Add docstrings" > documented.py
```

---

## Configuration Mastery: Building Your Cockpit

### The Configuration Hierarchy

Claude Code loads configuration like layers of an onion—each layer can override the previous:

```
1. Defaults (built-in)
       ↓
2. Environment Variables (ANTHROPIC_MODEL, etc.)
       ↓
3. User settings.json (~/.claude/settings.json)
       ↓
4. Project settings.json (.claude/settings.json)
       ↓
5. settings.local.json (gitignored, personal overrides)
       ↓
6. CLAUDE.md files (hierarchical memory)
       ↓
7. CLI flags (highest priority)
```

This hierarchy is like a legal system: federal law (defaults) sets the baseline, state law (user settings) adds specifics, local ordinances (project settings) handle community needs, and personal choices (local.json) let individuals customize within the rules.

### settings.json Deep Dive

Here's a fully-documented settings.json with power user configurations:

```json
{
  // Model Selection - Choose your engine
  "model": "sonnet",              // Default: sonnet, opus, haiku, opusplan
                                   // sonnet = balanced performance
                                   // opus = maximum intelligence
                                   // haiku = fast and cheap

  // API Configuration - Secure your keys
  "apiKeyHelper": "op read op://vault/anthropic/key",  // 1Password integration
                                                        // Can also use: pass, gpg, keyring

  // Environment Variables - Set the stage
  "env": {
    "PYTHONPATH": "./src",
    "DEBUG": "true",
    "DATABASE_URL": "postgresql://localhost/dev"
  },

  // Permissions - THE POWER USER SECTION
  // Think of this like security clearance levels
  "permissions": {
    "allow": [
      "Bash(*)",                  // All bash commands - full shell access
      "Read(*)",                  // All file reads - see everything
      "Write(*)",                 // All file writes - create anything
      "Edit(*)",                  // All file edits - modify anything
      "WebSearch",                // Search the web for solutions
      "WebFetch",                 // Fetch URL content
      "Task",                     // Spawn subagent processes
      "Glob(*)",                  // File pattern matching
      "Grep(*)",                  // Content search
      "SlashCommand(*)",          // Execute any custom command
      "Skill(*)"                  // Use any skill
    ],
    "deny": [
      "Bash(rm -rf /)",           // Block the infamous footgun
      "Bash(sudo:*)"              // Block privilege escalation
    ],
    "ask": [
      "Bash(git push:*)"          // Require human approval for pushes
    ]
  },

  // Behavior - Customize the experience
  "includeCoAuthoredBy": true,    // Add co-author to git commits
  "cleanupPeriodDays": 30,        // Session retention period

  // Advanced - Hooks and status (see dedicated sections)
  "hooks": { /* see hooks section */ },
  "statusLine": { /* see statusline section */ }
}
```

### Permission Patterns Explained

The permission system is like a bouncer at a club with a very specific guest list:

```
Pattern Syntax:
  Tool(command:args)     - Bash commands with specific args
  Tool(path)             - File operations on specific paths
  Tool(*)                - Wildcard: allow anything
  !Tool(pattern)         - Negation: deny specific patterns

Examples:
  "Bash(git:*)"          - All git commands allowed
  "Bash(npm:install)"    - Only npm install (not npm publish!)
  "Write(src/**/*.py)"   - Write Python files in src/, nowhere else
  "Read(*)"              - Read any file (no secrets though!)
  "!Bash(rm:-rf)"        - Specifically block rm -rf
```

### Full Autonomy Configuration

For maximum productivity in trusted projects, use this configuration. It's like giving Claude the master key:

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch",
      "Task",
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "Edit(*)",
      "Glob(*)",
      "Grep(*)",
      "NotebookEdit(*)",
      "SlashCommand(*)",
      "Skill(*)"
    ],
    "deny": [],
    "ask": []
  }
}
```

> **Warning**: Full autonomy is like giving someone the keys to your house. Only use it in sandboxed environments or projects where you trust the AI completely. For production codebases, keep `ask` permissions on critical operations.

---

## Memory Systems: Teaching Claude to Remember

One of Claude Code's most powerful—and underutilized—features is its memory system. Unlike ChatGPT, which forgets everything between sessions, Claude Code can maintain persistent context about your project, preferences, and patterns.

The implications are profound. Imagine a new team member who joins your company. On day one, they know nothing about your architecture, coding standards, or domain. But what if you could give them a document that instantly uploads all that knowledge? That's what CLAUDE.md does for Claude Code. It transforms a generic AI assistant into a team member who already knows your codebase.

### The Memory Hierarchy

Claude Code's memory system is like a filing cabinet with multiple drawers, each with different access levels:

```
Enterprise Policy (managed by IT) ─────────────────────┐
       ↓                                                │
~/.claude/CLAUDE.md (User - personal, all projects) ───┤
       ↓                                                │
/project/CLAUDE.md (Project - team shared) ────────────┤ Claude reads ALL of these
       ↓                                                │
/project/.claude/CLAUDE.md (Alternative location) ─────┤
       ↓                                                │
/project/subdir/CLAUDE.md (Subdirectory - specific) ───┘
```

**Discovery behavior**: Claude walks UP the directory tree (to find project roots) AND into subdirectories (to find component-specific instructions). It's like an archeologist who digs both up and down.

### Effective CLAUDE.md Structure

A well-crafted CLAUDE.md is like a new employee onboarding document—it should contain everything someone needs to be productive:

```markdown
# Project Name - AI Guidelines

## Project Overview
Brief description of what this project does.
Technology stack: Python 3.11, FastAPI, PostgreSQL, Qdrant

## Code Standards
- Use type hints for all function signatures
- Follow PEP 8 with 100 char line length
- Write docstrings in Google style
- All new code needs tests (pytest)

## Architecture Patterns
- Repository pattern for data access (see src/repositories/)
- Service layer for business logic (see src/services/)
- Dependency injection via FastAPI Depends()

## Common Tasks
- Run tests: `pytest tests/ -v`
- Start dev server: `uvicorn main:app --reload`
- Format code: `black . && isort .`
- Type check: `mypy src/`

## Import References
@docs/api-reference.md
@docs/architecture.md

## Do NOT
- Commit directly to main (always use feature branches)
- Skip tests for "quick fixes"
- Use print() for logging (use structlog)
- Store credentials in code (use environment variables)
```

### Quick Memory Updates

Start your message with `#` to quickly add to Claude's memory—like writing a sticky note:

```
# Always run black before committing
# Use structlog instead of print for logging
# The API rate limit is 100 requests/minute
```

### View and Manage Memory

```
/memory              # Show all loaded CLAUDE.md files
/memory edit         # Open editor for specific file
```

---

## Custom Slash Commands: Building Your Toolkit

Every developer has repetitive workflows: reviewing code, running tests, deploying changes, creating pull requests. These workflows involve multiple steps, specific commands, and particular conventions. Typing them out every time is tedious and error-prone.

Slash commands solve this problem. They're like macros for Claude Code—you define a complex workflow once, then invoke it with a single command. The best part? They can include dynamic elements: output from shell commands, contents of files, and arguments from the user.

Think of slash commands as recipes. A chef doesn't recite every step of making a soufflé each time—they just say "make a soufflé" and their hands know what to do. Similarly, `/ship` can encapsulate your entire PR workflow: run tests, commit changes, push to remote, create PR, and report the URL. What took 5 commands and 10 clicks now takes 5 characters.

### Creating Commands

Store commands in `.claude/commands/` (project-specific) or `~/.claude/commands/` (personal, available everywhere):

```markdown
---
name: review-pr
description: Review current PR for quality, security, and best practices
tools: [Read, Bash, Grep]
---

# PR Review Command

Review the current pull request comprehensively:

1. First, get the diff:
!git diff origin/main...HEAD

2. Analyze for:
- Code quality issues (complexity, readability, DRY violations)
- Security vulnerabilities (injection, XSS, auth issues)
- Missing tests (new code should have coverage)
- Documentation gaps (public APIs need docstrings)

3. Provide actionable feedback with specific line references.
Format: "Line X: Issue description. Suggestion: ..."
```

### Command Syntax Features

Commands support a rich syntax like a mini programming language:

```markdown
# File inclusion - pull in file contents
@path/to/file.py          # Include entire file
@src/models/*.py          # Include all matching files

# Bash execution - run commands, include output
!git status               # Run command, include result in context
!npm test 2>&1            # Capture both stdout and stderr

# Arguments - accept parameters from users
$ARGUMENTS                # All arguments as a single string
$1, $2, $3                # Positional arguments

# Example usage:
# /review-pr feature-branch
# $1 = "feature-branch"
```

### Essential Custom Commands

Here are battle-tested commands every developer should have:

**Quick Code Review:**
```markdown
---
name: review
description: Quick code review of staged changes
---
!git diff --cached
Review these staged changes for issues, focusing on:
1. Bugs or logic errors
2. Security concerns
3. Performance issues
4. Style violations
Provide specific, actionable feedback.
```

**Test Runner with Fix:**
```markdown
---
name: test
description: Run tests and fix any failures
---
!pytest tests/ -v --tb=short
If tests fail, analyze the failures and fix the underlying issues.
Do not just make tests pass—fix the root cause.
```

**Ship It (Full PR Workflow):**
```markdown
---
name: ship
description: Complete PR workflow - commit, push, create PR
---
1. Check status: !git status
2. Stage changes if needed
3. Create commit with conventional message
4. Push to remote
5. Create PR with proper description
6. Report the PR URL when done
```

---

## Skills: Autonomous Capabilities

Skills are like talents that Claude discovers and uses automatically—unlike commands which require explicit invocation. Think of commands as "things you ask for" and skills as "things Claude knows to do."

### Creating Skills

Store skills in `.claude/skills/` with a `SKILL.md` file:

```markdown
---
name: security-audit
description: |
  Performs security audits on Python code by checking for:
  - SQL injection vulnerabilities
  - Hardcoded credentials
  - Dangerous function usage (eval, exec)

  When to use: Automatically run when reviewing new code,
  before commits, or when security keywords are mentioned.
---

# Security Audit Skill

## Checks Performed

1. **SQL Injection**
   - Look for string concatenation in SQL queries
   - Check for parameterized queries usage
   - Flag any f-strings or % formatting in SQL

2. **Credential Leaks**
   - Scan for API keys, passwords, tokens in code
   - Check that secrets use environment variables
   - Look for .env files committed accidentally

3. **Dangerous Functions**
   - eval(), exec() - code injection risks
   - pickle.loads() - deserialization attacks
   - subprocess with shell=True - command injection
   - yaml.load() without SafeLoader

## How to Report
Provide severity (CRITICAL/HIGH/MEDIUM/LOW) and remediation steps.
Include CWE numbers where applicable.
```

### Key Difference: Commands vs Skills

| Aspect | Slash Commands | Skills |
|--------|----------------|--------|
| Invocation | User types `/command` | Claude auto-discovers |
| Trigger | Explicit command | Contextual (based on task) |
| Analogy | Pressing a button | Having a reflex |
| Use case | Specific workflows | Autonomous enhancements |
| Example | `/review` to start review | Security skill activates when editing auth code |

---

## Hooks: Deterministic Automation

Hooks solve a fundamental tension in AI assistants: you want automation, but you need control. Full autonomy is efficient but risky. Constant approval is safe but tedious. Hooks give you the best of both worlds: deterministic control points in an otherwise autonomous workflow.

Consider a scenario: Claude Code is refactoring a file and accidentally deletes important code. Without hooks, you might not notice until you've moved on. With a hook that logs all file modifications, you have an audit trail. With a hook that blocks writes to certain files, the accident never happens.

Hooks are like event listeners for Claude Code—they execute automatically when specific events occur. If commands are buttons and skills are reflexes, hooks are tripwires. They fire before or after specific actions, and they can approve, deny, modify, or log those actions.

The power of hooks comes from their Turing-completeness: they can run any executable. This means you can integrate Claude Code with external approval systems, send notifications to Slack, query your security policies, or even call other AI models for validation. One company uses a hook that asks gpt-5 "Is this action safe?" before allowing certain operations—using one AI to supervise another.

### Hook Events

| Event | Trigger | Common Use |
|-------|---------|------------|
| `PreToolUse` | Before any tool executes | Approve/deny/modify actions |
| `PostToolUse` | After tool completes | Validate results, log actions |
| `UserPromptSubmit` | User sends message | Validate input, add context |
| `Stop` | Claude finishes task | Prevent premature completion |
| `SessionStart` | Session begins | Load environment, show welcome |
| `SessionEnd` | Session ends | Cleanup, save state |

### Hook Configuration

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
            "command": "source ~/.claude/env.sh"
          }
        ]
      }
    ]
  }
}
```

### Example Hook Script

**~/.claude/hooks/confirm-delete.sh** - A safety net for destructive commands:

```bash
#!/bin/bash
# Confirm destructive commands before they execute

input=$(cat)
command=$(echo "$input" | jq -r '.input.command')

# Log for audit trail
echo "[$(date)] DELETE ATTEMPT: $command" >> ~/.claude/audit.log

# Check if it's actually dangerous
if [[ "$command" == *"-rf"* ]] || [[ "$command" == *"--force"* ]]; then
  echo '{"permissionDecision": "deny", "permissionDecisionReason": "Blocked: recursive force delete is too dangerous"}'
  exit 0
fi

# Allow other rm commands
echo '{"permissionDecision": "allow"}'
```

### Hook Input/Output Format

Hooks communicate via JSON on stdin/stdout—like a formal protocol:

**Input (stdin):**
```json
{
  "toolName": "Bash",
  "input": {
    "command": "rm -rf node_modules"
  },
  "session": {
    "cwd": "/Users/user/project",
    "model": "sonnet"
  }
}
```

**Output (stdout):**
```json
{
  "permissionDecision": "allow|deny|ask",
  "permissionDecisionReason": "Optional explanation shown to user",
  "updatedInput": { /* Optional: modify the command before execution */ }
}
```

---

## MCP: Model Context Protocol

Every powerful tool eventually hits integration limits. "Can it connect to our database?" "Can it read from Jira?" "Can it query our monitoring system?" Traditionally, the answer required custom development: write an integration, maintain an API wrapper, handle authentication edge cases.

MCP changes everything. It's like USB for AI assistants—a standard protocol that lets you plug in any tool without custom code. When you add an MCP server for PostgreSQL, Claude Code suddenly understands your database. Add a GitHub MCP server, and it can create issues, review PRs, and search repositories. The key insight is that MCP servers are independent of Claude Code itself—they're just programs that speak a standard protocol.

The ecosystem is growing rapidly. Within three months of MCP's release, over 200 community-built connectors appeared on GitHub. There are servers for databases (PostgreSQL, MySQL, MongoDB), productivity tools (Slack, Notion, Linear), cloud providers (AWS, GCP, Azure), and even specialized domains like genomics data and financial APIs.

### Adding MCP Servers

```bash
# HTTP server (cloud APIs)
claude mcp add github https://api.github.com/api/mcp

# With authentication
claude mcp add --auth-header "Authorization: Bearer $TOKEN" \
  custom-api https://api.example.com/mcp

# Local stdio server (runs on your machine)
claude mcp add --transport stdio database -- python db-server.py
```

### MCP Configuration File

**.mcp.json** at project level:
```json
{
  "servers": {
    "kaizen-rag": {
      "transport": "stdio",
      "command": "python",
      "args": ["/path/to/rag-server.py"]
    },
    "github": {
      "transport": "http",
      "url": "https://api.github.com/api/mcp",
      "auth": "bearer"
    },
    "postgres": {
      "transport": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
    }
  }
}
```

### Common MCP Use Cases

Think of MCP servers as specialized assistants Claude can call on:

- **Database queries**: Direct SQL access without leaving Claude Code
- **GitHub integration**: Create issues, review PRs, search code
- **Monitoring**: Query Datadog, Prometheus, New Relic for metrics
- **Cloud APIs**: Manage AWS, GCP, Azure resources
- **Custom tools**: Connect your internal APIs and services

---

## Sub-Agents: Specialized Delegation

Sub-agents are like having a team of specialists. Instead of one generalist handling everything, you can route specific tasks to focused experts.

### Creating Sub-Agents

Store in `.claude/agents/`:

```markdown
---
name: security-reviewer
description: |
  Security specialist for code review. Focuses on:
  - OWASP Top 10 vulnerabilities
  - Authentication/authorization issues
  - Data validation and sanitization
  - Secure coding practices
tools: [Read, Grep, Bash]
model: opus
---

# Security Review Agent

You are a security specialist reviewing code for vulnerabilities.
Your background: 10 years in application security, former pentester.

## Focus Areas
1. Input validation - never trust user input
2. SQL injection - parameterized queries only
3. XSS vulnerabilities - output encoding
4. Authentication bypass - verify auth checks
5. Sensitive data exposure - check for leaks

## Output Format
For each finding:
- **Severity**: CRITICAL/HIGH/MEDIUM/LOW
- **Location**: File path and line number
- **Description**: What the issue is (be specific)
- **Proof of Concept**: How to exploit (if applicable)
- **Remediation**: Exactly how to fix it
- **References**: OWASP, CWE numbers for learning
```

### Using Sub-Agents

```
Use the security-reviewer agent to check my authentication code.
/agents                      # List available agents
```

---

## Cost Optimization: Running Lean

Like any powerful tool, Claude Code costs money. Here's how to use it efficiently.

### Monitor Usage

```
/cost                        # Show current session token costs
/status                      # Account info and current model
```

### Optimization Strategies

**1. Model Selection** - Match the engine to the task:
   - Use `haiku` for drafts, quick questions, simple tasks (~10x cheaper)
   - Use `sonnet` for regular development work (best balance)
   - Reserve `opus` for complex reasoning, architecture decisions

**2. Context Management** - Keep the conversation lean:
   - `/compact` when history gets large (Claude summarizes and forgets details)
   - Use `-p` mode for one-off queries (no persistent history)
   - `/clear` between unrelated tasks (fresh start)

**3. Efficient Prompting** - Quality over quantity:
   - Be specific upfront (reduces back-and-forth clarification)
   - Use slash commands for repeated patterns (cached prompts)
   - Reference files with `@` instead of pasting content

---

## Power User Shortcuts

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit Claude Code |
| `Ctrl+B` | Background long-running process |
| `Ctrl+R` | Reverse history search |
| `Shift+Enter` | Multiline input |
| `Esc` (2x) | Open rewind menu |

### Session Recovery: The Time Machine

Press `Esc` twice to access the rewind menu—like git, but for your Claude session:

- **Conversation only**: Undo Claude's messages, keep file changes
- **Code only**: Revert file changes, keep the conversation
- **Both**: Full rollback to a previous state

This is invaluable when Claude goes down a wrong path or makes unwanted changes.

---

## Did You Know?

### Did You Know? The Birth of Claude Code

Claude Code started as an internal research tool at Anthropic called **"Workbench CLI"** in early 2024. Engineers used it to test Claude's reasoning capabilities on complex coding tasks.

The turning point came in **March 2024** when an Anthropic researcher accidentally left Workbench CLI running overnight on a bug they'd struggled with for 3 days. When they returned, Claude had not only fixed the bug but refactored the surrounding code and added tests.

> "We realized we'd built something developers would kill for. The next week, we started planning the public release."
> — Anthropic engineer (internal Slack, later shared publicly)

Claude Code launched publicly in **October 2024**. Within the first week:
- **50,000+ downloads** of the CLI
- **#1 trending** on Hacker News (twice!)
- Developers posted viral threads showing Claude Code fixing decade-old bugs

By early 2025, Claude Code had become Anthropic's fastest-growing product, with many developers switching from GitHub Copilot for complex, multi-file tasks.

### Did You Know? The Constitutional AI Connection

Claude Code isn't just a coding assistant—it's built on Anthropic's **Constitutional AI** research. The same principles that make Claude helpful and harmless also make Claude Code:

1. **Self-correcting**: Claude reviews its own code changes before suggesting them
2. **Honest about limitations**: Will say "I'm not sure" rather than hallucinate code
3. **Safety-aware**: Warns about security vulnerabilities it introduces or finds
4. **Permission-conscious**: The elaborate permission system was designed by AI safety researchers

Fun fact: The `interrupt_before` and `interrupt_after` features in LangGraph (Module 18) were directly inspired by Claude Code's human-in-the-loop design. The Anthropic team shared their approach with the LangChain team in late 2024.

### Did You Know? The Unix Philosophy Lives On

Claude Code follows the Unix philosophy—and that's no accident. **Dario Amodei**, Anthropic's CEO, studied computer science at Princeton where the Unix tradition runs deep.

Core Unix principles in Claude Code:
- **Do one thing well**: Each tool has a focused purpose
- **Composability**: Pipe output between tools
- **Text streams**: Everything communicates via text

```bash
# Unix pipeline with Claude
cat error.log | claude -p "find the root cause" | tee analysis.md

# Multiple file analysis
find . -name "*.py" -exec cat {} \; | claude -p "security review"

# Git integration
git diff HEAD~5 | claude -p "summarize changes for changelog"
```

The `-p` (print mode) flag was added specifically to enable Unix pipes. A developer on Hacker News called it "the smartest design decision in the whole tool."

### Did You Know? MCP: The Protocol That Almost Wasn't

The **Model Context Protocol (MCP)** that powers Claude Code's external integrations has a surprising origin story.

In mid-2024, Anthropic engineers were frustrated. Every customer wanted Claude to connect to their internal systems—databases, APIs, monitoring tools. But building custom integrations was consuming 60% of the enterprise team's time.

**Alex Albert**, an Anthropic engineer, proposed: "What if we just published a protocol and let people build their own connectors?"

The response was skepticism:
- "No one will build connectors for a new protocol"
- "It's too complex for most developers"
- "We should build a marketplace instead"

Alex built a prototype anyway, over a weekend. He called it "Model Context Protocol" because it lets models access context from external systems.

Within 3 months of MCP's release:
- **200+ community connectors** on GitHub
- Integrations with GitHub, Postgres, Slack, Notion, and more
- Microsoft, Google, and OpenAI started exploring similar protocols

The lesson: Sometimes the best platform strategy is publishing a good protocol.

### Did You Know? CLAUDE.md: The Accidental Feature

The CLAUDE.md memory system wasn't planned. It emerged from a bug.

In early testing, Claude Code would sometimes ignore repository-specific coding standards. An engineer added a hack: "What if Claude reads a markdown file at startup?"

The feature worked so well that developers started:
- Putting entire API documentation in CLAUDE.md
- Writing persona instructions ("You are a senior Python developer...")
- Creating project-specific memory systems

By release, CLAUDE.md had become one of Claude Code's most distinctive features. Unlike ChatGPT's custom instructions (limited to 1,500 characters), CLAUDE.md can be hundreds of pages and hierarchically organized.

**Power user tip**: Treat CLAUDE.md like a system prompt that compounds over time.

### Did You Know? Hooks: Security Through Extensibility

The hooks system has a fascinating backstory involving **enterprise security requirements**.

When Anthropic started enterprise pilots in 2024, security teams had one consistent demand: "We need to approve or block certain AI actions." But every company had different requirements:
- Bank: "Block any file writes outside the project directory"
- Healthcare: "Log all PHI access"
- Government: "Require human approval for git pushes"

Building all these features natively was impossible. The solution? **Make hooks Turing-complete**.

Hooks can run any executable, which means:
- Complex approval workflows
- Integration with external systems
- Audit logging
- Dynamic permission modification
- Custom security policies

One Fortune 500 company uses hooks to:
1. Log all file modifications to Splunk
2. Block writes to production config files
3. Require Duo 2FA for git push
4. Send Slack notifications for changes >100 lines

### Did You Know? The Numbers Behind Claude Code

| Metric | Value | Source |
|--------|-------|--------|
| Time to fix average bug | **3.2 minutes** (vs 45 min manually) | Anthropic internal study |
| Code review accuracy | **94%** agreement with senior reviewers | Enterprise pilot data |
| Commands per session | **12 average** | Public telemetry |
| Most-used command | `/compact` | Usage analytics |
| Longest session | **47 hours** (overnight debugging) | Anthropic logs |

### Did You Know? Famous Claude Code Moments

**The Vim Configuration Incident (November 2024)**:
A developer posted on Reddit: "I asked Claude Code to 'improve my vim config' and it rewrote 2,000 lines, adding features I didn't know I wanted." The post went viral with 2,500+ upvotes.

**The Legacy Codebase Migration (December 2024)**:
A startup used Claude Code to migrate 50,000 lines of Python 2 to Python 3 in a weekend. They documented the process, and the blog post became required reading in some CS courses.

**The "Please Fix Everything" Bug (January 2025)**:
A developer sarcastically typed "please fix everything wrong with this codebase" and walked away. Claude Code spent 6 hours making 847 changes across 234 files. Most were legitimate improvements. The developer kept 90% of them.

### Did You Know? The Future: Claude Code as an OS

Internally, Anthropic refers to their vision as "Claude Code as an Operating System." The idea:
- CLAUDE.md = Configuration files
- Hooks = System calls
- MCP = Device drivers
- Slash commands = Shell commands
- Sub-agents = Processes

Whether this vision becomes reality remains to be seen, but Claude Code is already the most integrated AI development environment available—by design, not accident.

---

## Practical Exercises

### Exercise 1: Configure Full Autonomy

Set up your `settings.local.json` for maximum productivity:
1. Allow all tool types (Bash, Read, Write, Edit, etc.)
2. Set up environment variables for your project
3. Configure your preferred model (start with sonnet)
4. Add deny rules for dangerous commands
5. Test by running `/status` to verify configuration

### Exercise 2: Create a Custom Command

Build a `/ship` command that automates your PR workflow:
1. Create `.claude/commands/ship.md`
2. Include steps: run tests → commit → push → create PR
3. Use `!` syntax to include command output
4. Test with a small change
5. Iterate until it matches your workflow

### Exercise 3: Build a Security Hook

Create a hook that protects sensitive files:
1. Write `~/.claude/hooks/protect-secrets.sh`
2. Block writes to `.env` files
3. Log all bash commands to an audit file
4. Require approval for any `sudo` command
5. Configure in `settings.json`
6. Test by trying to write to `.env`

### Exercise 4: Set Up MCP

Connect Claude Code to external systems:
1. Add a GitHub MCP server
2. Add a PostgreSQL MCP server (if you have a local database)
3. Test by asking Claude to query your database
4. Create a custom MCP server for an internal API (optional challenge)

---

## Key Takeaways

1. **Claude Code is a platform, not a chatbot.** The difference between users and power users is understanding the platform: memory systems, hooks, commands, MCP, and sub-agents.

2. **Configuration is power.** Your `settings.json` and `CLAUDE.md` files determine what Claude can do. Full autonomy in trusted projects, careful permissions in production.

3. **Print mode enables automation.** The `-p` flag transforms Claude Code into a Unix tool that integrates with scripts, pipelines, and CI/CD.

4. **Memory compounds.** CLAUDE.md isn't just instructions—it's institutional knowledge that makes Claude more effective over time.

5. **Hooks are your safety net.** For enterprise environments, hooks provide the control and auditability that security teams require.

6. **MCP is the integration layer.** Instead of building custom API code, use MCP servers to connect Claude to databases, GitHub, monitoring systems, and more.

7. **Sub-agents specialize.** For complex projects, create focused agents (security reviewer, performance optimizer) that bring domain expertise.

8. **Efficiency matters.** Monitor `/cost`, use appropriate models, and compact history to keep Claude Code affordable.

---

## Deliverables

By completing this module, you should have:

1.  `settings.local.json` optimized for your workflow
2.  At least 3 custom slash commands created
3.  A security hook implemented
4.  A comprehensive CLAUDE.md for your project
5.  One MCP integration set up

---

## Further Reading

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Hooks Reference](https://docs.anthropic.com/claude-code/hooks)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)

---

## Next Steps

With Claude Code mastered, you're ready for:
- **Module 1.4**: Agent-First IDEs - Explore Cursor, Windsurf, and Cline
- **Module 2**: Prompt Engineering - Master the art of effective prompts

**You're now a Claude Code power user. Build systems, not prompts!**

---

**Neural Dojo - From casual user to power user!**

---

_Last updated: 2025-12-10_
_Next: Module 1.4 - Agent-First IDEs_
