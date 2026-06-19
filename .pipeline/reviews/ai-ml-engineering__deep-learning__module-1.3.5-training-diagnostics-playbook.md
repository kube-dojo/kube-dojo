## 2026-06-19T20:20:20Z — `REVIEW` — `APPROVE`
#2037 cross-family review (s168). Reviewer: deepseek-v4-pro. P2 (orchestrator-confirmed): label smoothing was listed as a cause of below-`log(C)` init loss — incorrect (uniform predictions give CE=log(C) regardless; smoothing raises the floor). Fixed: replaced with leaked-labels + added clarifying note. Re-verified T0 PASS.
