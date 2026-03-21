"""Prompt building for Gemini and Claude interactions — KubeDojo edition."""


def build_gemini_prompt(msg: dict, stdout_only: bool, output_path: str | None,
                        allow_write: bool, delimiters: str | None) -> str:
    """Build the prompt string for a Gemini invocation.

    Selects one of three modes:
    - FULL-EXECUTION (allow_write): Gemini has bash + write access
    - ORCHESTRATED (stdout_only or output_path): Ultra-restrictive, text-only
    - STANDARD: Collaborative prompt for general communication
    """
    if allow_write:
        return _build_full_execution_prompt(msg, delimiters)
    elif stdout_only or output_path:
        return _build_orchestrated_prompt(msg, output_path)
    else:
        return _build_standard_prompt(msg)


def _build_full_execution_prompt(msg: dict, delimiters: str | None) -> str:
    """Build FULL-EXECUTION prompt: Gemini has bash + write access."""
    if delimiters:
        tag_list = [t.strip() for t in delimiters.split(",")]
        delimiter_lines = "\n".join(
            f"  - ==={tag}_START=== ... ==={tag}_END===" for tag in tag_list
        )
        delimiter_instruction = f"Your ONLY text output must be between these exact delimiters:\n{delimiter_lines}"
    else:
        delimiter_instruction = "Your ONLY text output must be between the ===TAG_START=== / ===TAG_END=== delimiters defined in your task."

    return f"""ROLE: You are a SILENT EXECUTION AGENT with FULL read-write access.

CONTEXT: KubeDojo is a free, open-source Kubernetes curriculum (311+ modules covering
CKA, CKAD, CKS, KCNA, KCSA certifications + Platform Engineering, Linux, IaC tracks).
Modules live in docs/ and follow strict quality standards (see CLAUDE.md).

TOOLS YOU MUST USE (not simulate):
- run_shell_command: grep, cat, wc, git commands
- read_file / write_file: Read content, apply fixes directly

SILENCE PROTOCOL (CRITICAL):
- DO NOT narrate. DO NOT say "I will..." or "Let me..." or "First, I need to..."
- DO NOT describe what you are about to do. Just invoke the tool.
- Between tool calls, emit ZERO text. No commentary. No summaries.
- {delimiter_instruction}
- Every word you write that is NOT a tool call or the final delimited output is a WASTED TOKEN.

RULES:
1. NO MESSAGES. Never use send_message, message broker, or any communication tool.
2. NO EXPLORATION beyond what the task requires.
3. NO DELEGATION. Never say "Claude should..." or request skills/commands.
4. NO SIMULATION. You MUST run_shell_command for every check. Never guess file contents.
5. ALWAYS FINISH. Always produce output between the required delimiters, even on errors.

TASK:
{msg['content']}
"""


def _build_orchestrated_prompt(msg: dict, output_path: str | None) -> str:
    """Build ORCHESTRATED prompt: ultra-restrictive, text/file output only."""
    if output_path:
        output_instruction = f"""1. WRITE OUTPUT TO EXACTLY ONE FILE: {output_path}
   Write your COMPLETE output to this file. This is the ONLY file you may create or modify.
   Do NOT write to any other file. Do NOT edit any existing file."""
        success_instruction = f"""- Read the task content provided below
- Think about the content
- Write your COMPLETE output to: {output_path}
- That's it. Nothing else."""
    else:
        output_instruction = """1. OUTPUT ONLY TEXT. Your ONLY job is to read input files and produce text output.
2. DO NOT WRITE OR EDIT ANY FILES."""
        success_instruction = """- Read the task content provided below
- Think about the content
- Output your result as plain text
- That's it. Nothing else. Just text output."""

    prompt = f"""ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.

ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:

{output_instruction}
3. DO NOT SEND MESSAGES. Do not use send_message, message broker, MCP tools, or any communication tool.
4. DO NOT RUN SHELL COMMANDS that modify state. You may read files (cat, head) but NEVER write, move, delete, or execute scripts.
5. DO NOT TAKE INITIATIVE. Do not explore beyond what the task requires.
6. DO NOT DELEGATE. Do not say "Claude should..." or request any skills/commands.

HOW TO SUCCEED:
{success_instruction}

TASK:
{msg['content']}
"""
    if msg['data']:
        prompt += f"""
ATTACHED DATA:
{msg['data']}
"""
    return prompt


def _build_standard_prompt(msg: dict) -> str:
    """Build STANDARD collaborative prompt for general communication."""
    prompt = f"""You are Gemini, collaborating with Claude on the KubeDojo project.

PROJECT CONTEXT:
KubeDojo is a free, open-source Kubernetes curriculum with 311+ modules:
- Certification tracks: CKA, CKAD, CKS, KCNA, KCSA (exam-aligned, K8s 1.35+)
- Platform Engineering: SRE, GitOps, DevSecOps, MLOps (102 modules)
- Deep Dives: Linux (28 modules), IaC (12 modules)
- Quality standard: Every module has theory, hands-on exercises, quizzes, "Did You Know?" facts

This is a message from Claude to you:

---
{msg['content']}
"""
    if msg['data']:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """
---

REVIEW PROTOCOL (mandatory for all review requests):
- You MUST read every referenced file COMPLETELY before writing your review. Use read_file or cat — do not skim.
- For EVERY issue you report, cite the exact content from the file (quote the line, value, or field).
- If you cannot cite evidence from the actual file, do NOT report the issue — you may be hallucinating.

KUBEDOJO-SPECIFIC REVIEW CRITERIA:
- Technical accuracy: Are K8s commands correct and runnable? Are version numbers accurate?
- Exam alignment: Does the content match the current CNCF exam curriculum?
- Completeness: Are acceptance criteria thorough? Any edge cases missed?
- Scope: Is the change appropriately sized? Not too broad, not too narrow?
- Dependencies: Are cross-module or cross-track impacts identified?
- Junior-friendly: Would a beginner understand this? Is the "why" explained, not just the "what"?

Please respond with:
1. A clear verdict (APPROVE / NEEDS CHANGES / REJECT)
2. Specific, actionable feedback for any issues found
3. Keep it concise — focus on what needs changing, not what's already good

Format your response clearly with markdown.
"""
    return prompt


def build_claude_prompt(msg: dict) -> str:
    """Build prompt for Claude invocation."""
    prompt = f"""You are Claude, receiving a message from {msg['from'].title()} via the message broker.

PROJECT: KubeDojo — free, open-source Kubernetes curriculum (311+ modules).

---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
From: {msg['from']}

{msg['content']}
"""
    if msg['data']:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """
---

Respond directly to this message. Be concise and helpful.
Your response will be automatically sent back to the sender via the message broker.
Do NOT use MCP tools to send your response - just output your response directly.
"""
    return prompt
