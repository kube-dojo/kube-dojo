Targeted structural fix (NOT a full expansion) of:
src/content/docs/cloud/azure-essentials/module-3.13-application-gateway.md

This module is already at the word floor (body_words 5003) and the content is good.
It fails ONLY two structure gates in `scripts/quality/verify_module.py`:
  - `structure_quiz_6_8_with_details`: it has 4 quiz questions; the gate needs 6-8.
  - `outcomes_aligned`: the **Design** learning outcome ("Design a regional ingress
    pattern that uses the right boundary: Application Gateway vs Front Door vs ...")
    is not covered by any quiz question.

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DO EXACTLY THIS — minimal, surgical:
1. ADD 3 NEW quiz questions (bringing the total to 7, inside the 6-8 band), each in
   `<details><summary>...</summary>...</details>` form with a 3-5 sentence answer
   that explains WHY. At least ONE new question MUST be a scenario that assesses the
   **Design** outcome — i.e. choosing the correct regional-ingress boundary
   (Application Gateway vs Azure Front Door vs Load Balancer vs API Management) for a
   described requirement. Make >=2 of the new questions scenario-based.
2. RAISE the learning-outcomes list to 5 testable outcomes if it currently has fewer
   (it has 3) — add outcomes that the EXISTING content already teaches (do not invent
   uncovered topics); each new outcome must map to a section AND be assessed by a quiz
   question. Keep them as `**Verb** ...` Bloom-style outcomes.
3. Do NOT pad body words, do NOT delete or restructure existing content, do NOT add a
   source `# H1`. Preserve DYK=4 and Common-Mistakes 6-8 exactly.

### VERIFY before committing:
Run `scripts/quality/verify_module.py` on the file and confirm
`structure_quiz_6_8_with_details: true`, `outcomes_aligned: true`, and the module
stays T0 (passed: true). Report the final tier + the two gate values.

Web-verify any new Azure fact in a new quiz answer against learn.microsoft.com.
Commit: `chore(content): fix 3.13 application-gateway quiz/outcomes alignment (cloud Azure wave)`.
