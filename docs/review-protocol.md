# Review Protocol

## Prompt Context

PROJECT CONTEXT:
KubeDojo is a free, open-source Kubernetes curriculum with 700+ modules:
- Certification tracks: CKA, CKAD, CKS, KCNA, KCSA (exam-aligned, K8s 1.35)
- Platform Engineering: SRE, GitOps, DevSecOps, MLOps
- On-Premises Kubernetes, Cloud, Linux, and AI tracks
- Quality standard: learning outcomes, inline prompts, scenario-based quizzes

REVIEW RULES:
1. DIFF vs FILE: a diff only shows what changed. Lines absent from the diff may still exist in the file.
   Before claiming something is missing, verify absence in the actual branch file, not just the diff.
2. Mandatory format for every must-fix finding:
   FINDING: <one-line summary>
   FILE:LINE: <path>:<N>
   CURRENT CODE:
     <verbatim quote from the branch>
   WHY: <specific failure mode>
   FIX: <concrete change>
3. "Missing" claims require proof of absence. If you cannot quote the file or show a search proving absence, delete the finding or demote it to a question.
4. Do not invent line numbers. Every cited line must exist on the reviewed branch.
5. Self-check before submit: if the code might exist outside the diff, read/search the file before reporting.

OUTPUT:
1. Verdict: APPROVE / NEEDS CHANGES / REJECT
2. Must-Fix findings in the mandatory format
3. Nits in the same format when useful
4. Concise focus on what needs changing

## Universal Review Loop

Any orchestrator can run the review loop the same way:

1. Run the reviewer with this protocol prepended to the task.
2. Verify the review text with `.venv/bin/python scripts/verify_review.py --pr <N> --branch <ref>` or pass `--from-pr` to fetch the latest PR comment directly.
3. Treat `quote_missing` as hallucinated evidence. Treat `line_mismatch` as a citation accuracy problem. `verified` means the quoted code exists at the cited location.
4. Optionally post the verifier summary with `--post-comment`.
5. Decide manually. The verifier is passive evidence-checking only; it warns, but it does not block merge automatically.
