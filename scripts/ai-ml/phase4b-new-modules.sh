#!/usr/bin/env bash
#
# Phase 4b — write 8 new modernization modules (#199)
#
# Order: highest impact first per docs/ai-ml-modernization-plan.md.
# Each module:
#   1. Creates a stub file (idempotent — re-running skips existing).
#   2. Runs the v1 pipeline. Stub scores < 28 → triggers REWRITE mode →
#      Gemini Pro writes the full module from scratch.
#
# Sequential by design — never parallelize Gemini calls.
# Resumable: if a module fails, fix and re-run; completed ones are skipped
# by the pipeline state machine.
#
# Usage:
#   bash scripts/ai-ml/phase4b-new-modules.sh           # all 8
#   bash scripts/ai-ml/phase4b-new-modules.sh 1 2 3     # only the first 3
#

source "$(dirname "$0")/_lib.sh"

# Module spec arrays — index aligned across all four arrays.
PHASE=(  2  4  3  4  4  6  7  8 )
SEQ=(    6  8  5  9 10  3  9  4 )
DIR=(
  "generative-ai"
  "frameworks-agents"
  "vector-rag"
  "frameworks-agents"
  "frameworks-agents"
  "ai-infrastructure"
  "advanced-genai"
  "multimodal-ai"
)
STEM=(
  "reasoning-models"
  "model-context-protocol"
  "long-context-prompt-caching"
  "computer-use-agents"
  "next-gen-agentic-frameworks"
  "vllm-sglang-inference"
  "modern-peft-dora-pissa"
  "multimodal-first-design"
)
TITLE=(
  "Reasoning Models: System 2 Thinking"
  "Model Context Protocol (MCP) for Agents"
  "Long-Context LLMs and Prompt Caching"
  "Computer Use and Browser Automation Agents"
  "Next-Gen Agentic Frameworks"
  "High-Performance LLM Inference: vLLM and sglang"
  "Modern PEFT: DoRA and PiSSA"
  "Multimodal-First AI Design"
)
TOPIC=(
  "Reasoning models (System 2 thinking): OpenAI o3, DeepSeek R1, Claude reasoning. Test-time compute scaling, RL-R training, chain-of-thought verification, when to use reasoning models vs standard LLMs, distinct cost/latency tradeoffs, prompting paradigm shift (goal-orientation over micromanagement)."
  "Model Context Protocol (MCP): the standardized protocol for connecting AI agents to tools, databases, APIs and filesystems. Building MCP servers, consuming with Claude Code / Cursor / LangGraph, auth, transport, schemas. Replaces fragmented custom JSON tool schemas. Anti-pattern: bespoke per-model tool wiring."
  "1M+ token context windows and prompt caching. Claude 4.6, Gemini 3.5 Pro. Needle-in-haystack retrieval limits, prefix caching cost model, KV cache reuse, latency wins. When massive context replaces RAG. Cost optimization patterns."
  "Computer Use and browser automation agents. Anthropic Computer Use API, OpenAI Operator. Coordinate-based visual grounding, DOM navigation, headless browser security boundaries, screenshot loops, sandbox isolation. Universal task execution beyond text APIs."
  "Next-gen agentic frameworks: Letta (formerly MemGPT), AutoGen 0.4+, CrewAI 0.5+. Stateful event-driven multi-agent systems, OS-like persistent memory, supervisor/worker patterns, concurrent orchestration, comparison with LangGraph."
  "High-performance LLM inference: vLLM 0.6+ and sglang. Continuous batching, paged KV cache management, prefix caching, speculative decoding, chunked prefill. Self-hosting Llama 4 / DeepSeek V3 / Qwen 3 at scale on GPUs. Throughput vs latency tradeoffs."
  "Modern PEFT beyond standard LoRA: Weight-Decomposed Low-Rank Adaptation (DoRA) and PiSSA. Near full-parameter performance with minimal compute. Practical fine-tuning workflows, when to choose each, integration with PEFT/Hugging Face, comparison with LoRA and full fine-tuning."
  "Multimodal-first AI design. Native multimodal models (Gemini 3, GPT-5) processing text, audio, image, video in the same latent space without bolt-on STT/TTS encoders. Real-time streaming, voice agents, near-zero latency, end-of-pipeline-multimodal era."
)

run_one() {
  local i="$1"
  local p="${PHASE[$i]}" s="${SEQ[$i]}" d="${DIR[$i]}" st="${STEM[$i]}"
  local t="${TITLE[$i]}" tp="${TOPIC[$i]}"
  local key="ai-ml-engineering/${d}/module-${p}.${s}-${st}"

  log "==== Module $((i+1))/8: ${key} ===="
  write_stub "$p" "$s" "$d" "$st" "$t" "$tp"
  run_pipeline "$key"
}

# Pick which to run
if (( $# > 0 )); then
  for n in "$@"; do
    run_one $((n - 1))
  done
else
  for i in "${!STEM[@]}"; do
    run_one "$i"
  done
fi

log "Phase 4b complete. Run 'npm run build' before committing."
