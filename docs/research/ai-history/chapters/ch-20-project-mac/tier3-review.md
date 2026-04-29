# Tier 3 adversarial review - Codex

Direct user dispatch in `/Users/krisztiankoos/projects/kubedojo/.claude/worktrees/agent-af2d97a78fdeb3bd9`. Task: cross-family adversarial review of Claude-authored Tier 3 proposal for AI History Chapter 20, "Project MAC." Codex verified the proposed Fano pull-quote against R. M. Fano, "The Computer Utility and the Community" at `https://multicians.org/fano1967.html`, and checked the skipped Progress Report II mission candidate against the Bitsavers PDF text for *Project MAC Progress Report II, July 1964-July 1965*.

---

## Codex's verdicts (verbatim)

> **Element 8: APPROVE-SKIP.** Universal skip per `READER_AIDS.md`: the tooltip component does not exist yet, and inline `<abbr>` would modify prose lines.
>
> **Candidate A - Fano 1967 mission/social-utility pull-quote: REVISE.** The proposed wording is not verbatim and should not land: Fano does not write, "A time-sharing system is more than a facility for sharing computing resources. It is a community resource whose technical features shape the intellectual life of the community that uses it." The Green primary source does contain a nearby sentence that supports the same point: "A time-sharing system can quickly become a major community resource, somewhat analogous to a library, and its evolution and growth depend on the inherent capabilities of the system as well as on the interests and goals of the members of the community." The following sentence also contains the "intellectual life" phrasing, but combining them would exceed the pull-quote cap and make the callout too heavy. Use the verified first sentence only.
>
> **Candidate A adjacent-repetition check: PASS WITH REVISED ANCHOR.** The chapter paraphrases Fano's community-resource point in the "The important word is 'community'" paragraph but does not quote the sentence verbatim. The pull-quote should land immediately after that paragraph, not after the next AI-extrapolation paragraph, because the quoted Fano sentence comes from the community-resource discussion.
>
> **Candidate B - Project MAC Progress Report II founding mission: APPROVE-SKIP.** The skip is correct. Progress Report II's actual wording is: "The broad goal of Project MAC is the experimental investigation of new ways in which on-line use of computers can aid people in their individual intellectual work..." and then "the evolutionary development of a large, multiple-access computer system..." The proposal's quoted fragment is a compressed paraphrase, not a verbatim candidate. More importantly, the chapter already plain-reads this material in "A Project, Not A Lab," especially the dual Machine-Aided Cognition / Multiple-Access Computer framing. A pull-quote here would repeat the prose and lose to the Fano community hinge under the one-quote cap.
>
> **Candidate C - CTSS operating details plain-reading aside: APPROVE-SKIP.** Correct skip. The CTSS paragraph is concrete prose, not symbolic density. The next paragraph already explains the meaning of passwords, files, links, online manuals, and user commands in plain language, so a `Plain reading` callout would duplicate the surrounding text.
>
> **Candidate D - Multics vs. ITS contrast plain-reading aside: APPROVE-SKIP.** Correct skip. The contrast is narrative/institutional, not mathematical or abstract-definition-stacked. The prose already states the governing distinction directly: Multics as dependable shared service, ITS as intimate research control.
>
> **Candidate E - MACSYMA resource-hunger plain-reading aside: APPROVE-SKIP.** Correct skip. The paragraph is conceptually important but not symbolically dense under `READER_AIDS.md`. Progress Report X supports the resource-pressure claim, including that 256K of primary memory was insufficient for more than one MACSYMA user with reasonable response time, but the chapter already explains the operational lesson plainly.
>
> **Missed primary-source sentence: No separate missed candidate.** The missed issue is inside Candidate A: the proposal supplied a synthetic sentence instead of Fano's actual quotable sentence. Progress Report II's "intimate collaboration between man and computer system" sentence and Fano's editing/compiling/debugging sentence are plausible primary-source lines, but neither beats the revised Fano community-resource sentence for this chapter's hinge.
>
> **Final Tier 3 count:** 1 APPROVED VIA REVISION, 4 SKIPPED.

---

## Decisions and rationale

| # | Element | Codex verdict | Action taken | Why |
|---|---|---|---|---|
| 8 | Inline tooltip | APPROVE-SKIP | **SKIP** | Universal default until a non-destructive tooltip component exists. |
| 9 / Cand A | Fano 1967 pull-quote | REVISE | **APPLY REVISED** | Proposed wording is not verbatim. Fano's Green primary text instead says the time-sharing system can become "a major community resource"; this sentence is verified and not already quoted in prose. |
| 9 / Cand B | Progress Report II founding mission | APPROVE-SKIP | **SKIP** | The proposal's quoted fragment is compressed, and the chapter already explains the dual mission clearly. Cap is one; Fano is stronger. |
| 10 / Cand C | CTSS operating details plain-reading | APPROVE-SKIP | **SKIP** | Concrete narrative prose, followed by its own plain explanation; not symbolically dense. |
| 10 / Cand D | Multics / ITS contrast plain-reading | APPROVE-SKIP | **SKIP** | Narrative contrast; already plain-read by the prose. |
| 10 / Cand E | MACSYMA resource-hunger plain-reading | APPROVE-SKIP | **SKIP** | Important infrastructure point but not formula- or definition-stacked symbolic density. |
| - | Missed candidate | None separate | - | The only additional quote-worthy correction is the verified Fano wording replacing Candidate A's synthetic sentence. |

---

## Final landed elements

1. `:::note[Fano's community claim]` pull-quote callout immediately after the "The important word is 'community'" paragraph in `## The Utility Dream`.

Exact paragraph anchor:

> The machine could remember a working culture, not just execute isolated jobs.

Exact text to insert:

```markdown
:::note[Fano's community claim]
> "A time-sharing system can quickly become a major community resource, somewhat analogous to a library, and its evolution and growth depend on the inherent capabilities of the system as well as on the interests and goals of the members of the community."

Fano's 1967 point was social: system design steers what a research community can become.
:::
```

**Tally: 1 APPROVED, 4 SKIPPED of 5 total candidates.**

