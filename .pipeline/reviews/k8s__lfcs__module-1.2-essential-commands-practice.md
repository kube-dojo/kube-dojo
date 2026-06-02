# Review Audit: k8s/lfcs/module-1.2-essential-commands-practice

**Path**: `src/content/docs/k8s/lfcs/module-1.2-essential-commands-practice.md`
**Current phase**: review

---

## 2026-06-02T22:41:28Z — `REVIEW` — `APPROVE`
Tool-certs wave-2 LFCS cross-family R1 (session 95). Reviewer: opus-4.8 (4/5, NEEDS_CHANGES). Fixed + ground-checked: P1 glob correctness (\*.log does NOT match .log — \* skips a leading dot); awk -F':' added to /etc/passwd example (matched its correct twin); tar -C absolute-path explanation corrected (KC#4 taught a wrong mental model); history date POSIX-1984 -> ustar standardized in POSIX.1 / IEEE Std 1003.1-1988; 3 'preserved' authoring-leak words removed. opus verified redirection ordering, find traps, mv/cp, links, tar flags, sed all correct. Fixed via PR #1759. Verifier T3 on body_words_floor (~43w pre-existing gap) + sources_all_reachable (local-prober network-block FP) ONLY — both non-blocking; finalized on the review axis.
