# Chapter 4 model-analogy corrections — research record

**Checked:** 2026-09-05

This unpublished record addresses only the Markov/current-language-model
analogy. It does not edit or accept Chapter 4 prose, settle ideology/quotation
claims, or verify the historical hardware assertions.

## Fresh primary-source receipts

- Vaswani et al., “Attention Is All You Need,”
  <https://arxiv.org/pdf/1706.03762>, retrieved 2026-09-05. PDF SHA-256:
  `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`.
  The abstract directly describes the Transformer as based solely on attention.
  Printed p. 2, §3, directly describes an autoregressive decoder consuming
  previously generated symbols; printed p. 3, §3.1, directly describes the
  causal masking that prevents a position from attending to subsequent
  positions.
- Brown et al., “Language Models are Few-Shot Learners,”
  <https://arxiv.org/pdf/2005.14165>, retrieved 2026-09-05. PDF SHA-256:
  `97fd272f1fdfc18677462d0292f5fbf26ca86b4d1b485c2dba03269b643a0e83`.
  The abstract directly identifies GPT-3 as a 175-billion-parameter
  autoregressive language model. §1 describes in-context completion as
  predicting what comes next; §2 describes a finite context window.

These papers are representative primary evidence, not a survey of every modern
language model or architecture.

Preserved retrieval PDFs, full text, and page excerpts are in the ignored
`.agent/ch04-model-retrieval/` directory; the command and hash receipt is
`.agent/ch04-model-retrieval-receipt.md`.

## Inherited historical evidence

The Markov and Shannon locators below are inherited from the existing Chapter 4
source ledger, not freshly rechecked in this packet:

- Markov, 1913 English translation, pp. 591–598:
  <https://alpha60.de/research/markov/DavidLink_AnExampleOfStatistical_MarkovTrans_2007.pdf>
  — hand-counted conditional vowel statistics.
- Shannon, 1948, §§3–4:
  <https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf>
  — Markoff-process text approximations and the indirect Fréchet route.

## Claim dispositions

- **Glossary “N-grams ... direct descendant”:** Shannon §3 and Markov's
  counts support a related conditioning pattern. “Direct descendant” is an
  inference and conflicts with the documented indirect Markov–Fréchet–Shannon
  route. Prefer “conceptual descendant” or “a finite-order predictive model
  with a related conditioning pattern.”
- **Manual-work comparison:** Shannon §3 directly supports random-number books,
  frequency tables, and labor becoming enormous; Markov pp. 591–598 support
  manual tables. This comparison is safe for those examples only and does not
  date the arrival of general computing infrastructure.
- **Autoregressive models / next token:** Brown and Vaswani support the
  representative GPT-3/Transformer case. Scope prose to “autoregressive
  transformer language models such as GPT-3”; do not say every language model
  predicts the next token.
- **“Attention violates the Markov property”:** the papers directly support
  causal attention over available earlier positions. They do not state that
  formal verdict. Safe wording: “causal self-attention can consult multiple
  earlier positions in its context, rather than being restricted to the
  immediately preceding token.” This avoids an unsupported taxonomy claim while
  distinguishing it from the chapter's first-order chain.
- **“Not Markov chains in any technically meaningful sense”:** overbroad.
  Say only that the models discussed are not the two-state, first-order process
  analyzed by Markov and are not restricted to its one-step condition.
- **“Every modern language model” / “same task”:** unsupported universal and
  misleading equivalence. A safe replacement is: “An autoregressive transformer
  language model estimates a distribution for the next token from available
  prior context. That echoes Markov's count-and-condition pattern, while
  Markov's experiment measured vowel transition statistics rather than modern
  text generation.”
- **“Entire context window”:** qualify as available earlier positions within a
  finite context window; Vaswani's causal mask excludes subsequent positions.

## Explicit gap

The chapter's “no digital storage,” “first practical late-1950s storage,” and
“only a computer can answer” claims have no fresh hardware source here. Keep
them out of this model-analogy disposition; a separate hardware-history packet
must source or narrow them. No whole-chapter acceptance follows.
