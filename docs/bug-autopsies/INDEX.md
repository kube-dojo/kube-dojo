# Bug Autopsies

| Date | Category | Summary | Detail |
|------|----------|---------|--------|
| 2026-05-22 | calibration | content-review 0.5-collapse — binary-AND substring gates → ratio gates (PR for #1441) | [calibration-scorer-brittleness.md](calibration-scorer-brittleness.md) |
| 2026-05-22 | calibration | fact-check parse fragility — prose-prefixed JSON not extracted (PR for #1441) | [calibration-scorer-brittleness.md](calibration-scorer-brittleness.md) |
| 2026-06-04 | ci/build | invalid `lab.difficulty: medium` (Astro Zod enum) broke main's build; PR CI runs no full `astro build` so it slipped through (commit b52f9fce → fixed session 103) | [ci-no-full-build-gate.md](ci-no-full-build-gate.md) |
