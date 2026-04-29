# Tier 3 adversarial review — Codex (gpt-5.5)

Direct `codex exec -m gpt-5.5 -c model_reasoning_effort=high` dispatch. Task `394-ch14-tier3-codex-review`. Codex visually verified the *NYT* 1958 scan via the Blackmon-page link (resolving attribution: the "walk, talk…" rhetoric is newspaper/UPI voice attributing expectation to the Navy, not Rosenblatt's technical voice) and consulted the Internet Archive `POND61` scan for the alternate candidate.

---

## Codex's verdicts (verbatim)

> **Element 8 — APPROVE-SKIP.** Universal skip still applies until non-destructive tooltip support exists.
>
> **Element 9 — REVISE / LAND B, NOT A.** I could visually verify the NYT scan enough to resolve attribution direction: the "walk, talk…" language is newspaper/UPI voice attributing expectation to the Navy, not Rosenblatt's technical voice. But do **not** use it as the pull-quote. The prose already quotes the core phrase nearby, and the contract still treats `NYT58` as reception/hype material. It would amplify the spectacle the chapter is trying to discipline.
>
> Use Rosenblatt's `POND61` preface instead, anchored after the paragraph at `src/content/docs/ai-history/ch-14-the-perceptron.md:142`:
>
> ```markdown
> :::note
> > "A perceptron is first and foremost a brain model, not an invention for pattern recognition."
>
> Rosenblatt's preface makes the anti-hype argument in his own voice: neurodynamic theory first, engineering application second.
> :::
> ```
>
> **Element 10 — APPROVE-SKIP C/D/E.**
> C: convergence theorem skip approved. The section already explains scope and boundedness in plain prose.
> D: linear separability skip approved. The "boundary / straight edge / many dimensions" explanation already is the reader aid.
> E: S/A/R architecture skip approved. The paragraph is definitional, not symbolically dense.
>
> **Missed candidate:** one alternate `POND61` sentence about "perceptron" as a generic name for theoretical nerve nets is paraphrased but not quoted. I would not land it. It is useful but narrower than the selected brain-model quote, which does stronger thesis work.
>
> Sources checked: `READER_AIDS.md`, Ch14 contract/source files, Ch14 prose, Internet Archive `POND61`, and the NYT scan linked from the Blackmon page.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default. |
| 9 / Cand A | NYT 1958 press rhetoric | REJECT — *not* the right pull-quote | **DECLINED** | Codex visually verified the NYT scan and resolved that the famous "walk, talk…" rhetoric is newspaper/UPI voice attributing expectation to the Navy, not Rosenblatt's technical voice. Even with attribution clarified, Codex correctly judged that landing it as a pull-quote would *amplify* the spectacle the chapter is trying to discipline. The chapter's prose handles the press rhetoric in its critical context already. |
| 9 / Cand B | POND61 preface (anti-hype) | APPLY with Codex's exact verbatim and annotation | **APPLY** | Rosenblatt's own anti-hype voice. Codex pulled the verbatim from the Internet Archive POND61 scan and proposed insertion in the "Experiments and limits without failure framing" section, after the paragraph that walks through Rosenblatt's own discussion of limits — the right rhetorical place for the brain-model framing. |
| 10 / Cand C | Convergence theorem plain-reading | APPROVE-SKIP | **SKIP** | Both reviewers agree the section already plain-reads scope and boundedness. |
| 10 / Cand D | Linear separability plain-reading | APPROVE-SKIP | **SKIP** | Both reviewers agree the geometric "boundary / straight edge / many dimensions" framing in the prose IS the plain-reading. |
| 10 / Cand E | S/A/R architecture plain-reading | APPROVE-SKIP | **SKIP** | Both reviewers agree the paragraph is definitional, not symbolically dense. |
| — | Missed alternate POND61 sentence | Codex flagged but recommended not landing | **DECLINED** | Brain-model quote already does the thesis work better. Cap is one. |

---

## Final landed elements

1. `:::note[Rosenblatt's own framing]` pull-quote callout in the "Experiments and limits without failure framing" section, after the paragraph "The difference is important because later histories often reverse the order…", with verbatim POND61 wording (Codex-verified) and Codex's tighter annotation framing the move as Rosenblatt's anti-hype voice.

**Tally: 1 of 5 candidates landed.** Calibration consistent with Ch10/Ch11/Ch12/Ch13.

The author's PROPOSED Candidate A (NYT press rhetoric) was actively rejected on chapter-thesis grounds even though the verbatim could be source-verified — exactly the kind of editorial judgment-call Codex is expected to make. The chapter's discipline is *to* discipline the press spectacle, not to elevate it; landing it as a typographic event would have undermined the chapter's argument.
