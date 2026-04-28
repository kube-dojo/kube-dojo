# Infrastructure Log: Chapter 66 - Benchmark Wars

## Systems To Track

- **Static benchmark suites:** MMLU, BIG-bench, HELM, HumanEval, TruthfulQA, and
  other table entries become common release-report grammar.
- **Human preference arenas:** MT-Bench and Chatbot Arena collect pairwise human
  votes and/or use strong LLMs as scalable judges.
- **Evaluation harnesses:** OpenAI Evals and benchmark APIs turn evaluation into
  reusable tooling, not one-off paper scripts.
- **Prompt and adaptation settings:** few-shot prompts, validation choices,
  benchmark-specific tuning, and held-out tests become part of the result.
- **Contamination checks:** GPT-4 report, BIG-bench, and SWE-bench show that data
  overlap must be managed explicitly.
- **Execution-based tests:** SWE-bench uses code patches and repository tests,
  making evaluation closer to work but more expensive and infrastructure-heavy.
- **Leaderboards:** public rankings become dated social artifacts; prose should
  avoid freezing any leaderboard as timeless truth.

## Metrics To Verify

- MMLU: 57 subjects; 15,908 questions; largest GPT-3 at 43.9% in the original
  paper; expert-level gap.
- BIG-bench: 204 tasks; 450 authors; 132 institutions; 24-task BIG-bench Lite;
  direct leakage impossible for reported models but indirect leakage possible.
- HELM: 7 metric categories; 16 core scenarios; 42 total scenarios; 30 models;
  prior average scenario coverage 17.9%, improved to 96.0%.
- GPT-4 report: simulated bar exam top 10%; MMLU 86.4%; contamination checks;
  GSM-8K training-set inclusion disclosure; Evals framework.
- MT-Bench / Arena: 80 MT-Bench questions; over 80% GPT-4/human agreement;
  bias/failure caveats. Re-verify any exact vote/conversation counts before
  surfacing them in prose because public Arena figures evolved quickly.
- SWE-bench: 2,294 tasks from 12 Python repositories; Claude 2 1.96% initial
  solve rate; about 90,000 PRs filtered to benchmark instances.

## Boundary

This chapter is about evaluation as power. Specific product launches remain in Chapter 59, and open-weight politics continue in Chapter 65.
