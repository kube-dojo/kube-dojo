"""Prompt building for Gemini and Claude interactions."""


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

TOOLS YOU MUST USE (not simulate):
- run_shell_command: scripts/audit_module.sh, .venv/bin/python scripts/*.py, grep, wc
- read_file / write_file: Read content, apply fixes directly

SILENCE PROTOCOL (CRITICAL):
- DO NOT narrate. DO NOT say "I will..." or "Let me..." or "First, I need to..."
- DO NOT describe what you are about to do. Just invoke the tool.
- Between tool calls, emit ZERO text. No commentary. No summaries. No reasoning.
- {delimiter_instruction}
- Every word you write that is NOT a tool call or the final delimited output is a WASTED TOKEN that risks timeout.

PRIVATE SCRATCHPAD (allowed):
- If you need to reason through complex logic (case endings, dates, IPA), use XML comments: <!-- thinking: your reasoning here -->
- Scratchpad comments do NOT count as narration — they are your private workspace.
- Keep scratchpad brief. Do NOT use it for narration or status updates.

RULES:
1. NO MESSAGES. Never use send_message, message broker, or any communication tool.
2. NO EXPLORATION. Do not check GitHub, inbox, or broker. Stay on task.
3. NO DELEGATION. Never say "Claude should..." or request skills/commands.
4. NO SIMULATION. You MUST run_shell_command for every check. Never "remember" file contents — always read from disk. If you skip a bash command and guess the result, the review is INVALID.
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
        output_instruction = """1. OUTPUT ONLY TEXT. Your ONLY job is to read input files and produce text output between delimiters.
2. DO NOT WRITE OR EDIT ANY FILES. You must not use any tool that creates, modifies, or deletes files."""
        success_instruction = """- Read the task content provided below
- Think about the content
- Output your result as plain text between the delimiters specified in the task
- That's it. Nothing else. Just text output."""

    prompt = f"""ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.

ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:

{output_instruction}
3. DO NOT SEND MESSAGES. Do not use send_message, message broker, MCP tools, or any communication tool.
4. DO NOT RUN SHELL COMMANDS that modify state. You may read files (cat, head) but NEVER run commands that write, move, delete, or execute scripts (no sed -i, no python scripts, no git, no audit_module.sh).
5. DO NOT TAKE INITIATIVE. Do not explore the codebase beyond what the task requires. Do not check GitHub issues, status files, inbox, or broker messages. Do not make strategic decisions.
6. DO NOT DELEGATE. Do not say "Claude should...", "please run...", or request any skills/commands.

HOW TO SUCCEED:
{success_instruction}

IF YOU ARE TEMPTED TO DO ANYTHING OTHER THAN WHAT'S DESCRIBED ABOVE: DON'T. Complete the task and stop.

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
    prompt = f"""You are Gemini, participating in a collaboration with Claude.
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
- Do NOT invent examples that are not in the files. Only critique what actually exists.
- Before critiquing a vocabulary list, activity list, or similar: list ALL items you found in the file first, THEN review each one.
- If a file has 25 vocabulary entries, your review must reference the actual 25 entries, not imagined ones.

Please respond appropriately. If this is a request, fulfill it.
If Claude asked for feedback, provide your honest assessment.
Format your response clearly.
"""
    return prompt


def build_claude_prompt(msg: dict) -> str:
    """Build prompt for Claude invocation."""
    prompt = f"""You are Claude, receiving a message from {msg['from'].title()} via the message broker.

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
