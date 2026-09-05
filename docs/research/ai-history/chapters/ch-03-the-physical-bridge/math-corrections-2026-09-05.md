# Chapter 3: Shannon's worked reduction

Research correction for #2339 and #2289. This record does not accept the whole
chapter or its other circuit examples. Published prose and a reader exercise
require separate review.

## Primary evidence and access

Claude E. Shannon, *A Symbolic Analysis of Relay and Switching Circuits*, MIT
thesis, signed August 10, 1937:

- [MIT record](https://dspace.mit.edu/handle/1721.1/11173).
- [PDF endpoint](https://dspace.mit.edu/bitstream/handle/1721.1/11173/34541425-MIT.pdf?sequence=1).
- The fresh endpoint returned HTTP 429 on September 5, 2026. Inspection used
  the unchanged existing cache: 3,153,192 bytes, SHA-256
  `4a7c64ce7a11c186568c36963dff77a958bd73ea56fe165a346e20fba9fc48d4`.
- Printed pp. 14–16 (PDF pp. 17–19) were visually inspected: theorem list,
  Figure 5 and its displayed algebra, then Figure 6 and its final expression.
  This is a primary-source facsimile, not a fresh successful download.

## Theorems: correct the identification

Printed p. 14 gives theorem 15a as `X + XY = X`, the absorption identity.
Theorem 17b on that page is `X + f(X) = X + f(0)`. The source applies 17b
successively to W, X, and Y in the reduction on pp. 15–16. The chapter must
not label absorption as theorem 17b.

The 17b identity can be checked by its two cases: if X is 0, both sides are
f(0); if X is 1, the OR with X makes both sides 1. This explanation is a
modern teaching derivation, not a quotation or a reconstruction of Shannon's
thought process.

## Expressions and contact counts

Printed p. 15 gives the Figure 5 hindrance expression:

`W + W'(X+Y) + (X+Z)(S+W'+Z)(Z'+Y+S'V)`

The displayed intermediate and final forms on pp. 15–16 are:

`W + X + Y + Z(Z' + S'V)`

`W + X + Y + ZS'V`

The first expression has 13 variable/contact occurrences; the last has six.
Figure 6 visibly shows W, X, Y and the three parallel contacts Z, S', V.
The source describes a reduction in elements; it does not print a 13-to-5
count. The chapter's five-contact claim is incorrect, as is the initial
instruction in #2339 to preserve that allegedly source-backed count.

These are contact occurrences in this example, not a verified count of
physical relays. Six distinct Boolean variables occur in both expressions;
that fact alone does not establish hardware inventory, cost, performance, or
an unchanged physical relay count. Do not assert global minimality without
a separate proof.

## Independent mathematical check

Using Shannon's hindrance convention, 0 means closed and 1 means open.
Addition is Boolean OR of hindrances and represents a series connection;
juxtaposition is Boolean AND and represents a parallel connection.

A dependency-free local trace enumerated all 64 assignments of W, X, Y, Z,
S, V. It checked the original, the W substitution, constant elimination,
X/Y substitutions, distributive expansion, and final form. Every adjacent
pair had zero mismatches; every form evaluated to 1 on 57 assignments.
Token counts were derived from the two transcribed expression strings,
yielding 13 and six. Visual inspection binds those strings to the source;
the truth table alone cannot prove historical transcription accuracy.

The unpublished trace is retained locally as
`.agent/verify_shannon_fig5.py` in the context-research worktree. Before
publishing an exercise, include its reproducible check with the exercise
packet; a local execution receipt is not a permanent learner resource.

## Editorial boundary

Correct the count and theorem identification; remove unsupported claims
about physical relay counts or later popularizations unless sourced.
An optional prediction/reveal exercise may use the displayed reduction and
all-assignment check, explicitly as a modern algebra exercise. No invented
discovery scene, historical experiment, dialogue, or performance result.
The later selective-circuit example and modern-chip analogy remain outside
this record and require their own verification.
