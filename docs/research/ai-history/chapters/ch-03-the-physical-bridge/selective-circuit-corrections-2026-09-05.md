# Selective Circuit correction record

This is a bounded research record for the Section V *Selective Circuit*
example. It does not edit published prose and is not a Chapter 3 acceptance
decision.

## Primary-source binding

- Claude E. Shannon, *A Symbolic Analysis of Relay and Switching Circuits*,
  MIT master's thesis, signed August 10, 1937.
- MIT record: <https://dspace.mit.edu/handle/1721.1/11173>.
- PDF endpoint: <https://dspace.mit.edu/bitstream/handle/1721.1/11173/34541425-MIT.pdf?sequence=1>.
- Checked 2026-09-05 against the unchanged local facsimile at
  `../content-book-ch03-context-research/.agent/shannon-1937-source-cached.pdf`;
  3,153,192 bytes, SHA-256
  `4a7c64ce7a11c186568c36963dff77a958bd73ea56fe165a346e20fba9fc48d4`.
  The endpoint was not reopened in this packet; the existing cache receipt
  records HTTP 429 on 2026-09-05 UTC.

## Verified facts

- Section V begins on printed p. 51 (PDF p. 54). The selective example on
  printed p. 52 (PDF p. 55) says relay `A` operates when any one, any three,
  or all four of `w, x, y, z` operate. It labels the following expression the
  “hinderance function for A” and visibly prints seven product terms:

  ```text
  A = wxyz + w'x'yz + w'xy'z + w'xyz' + wx'y'z
      + wx'yz' + wxy'z'
  ```

- Shannon defines hindrance `0` as a closed circuit and `1` as an open circuit
  (printed pp. 4–5, PDF pp. 7–8). Under that convention the seven minterms are
  the states where `A` remains hindered: zero operated relays (one state) or
  two operated relays (six states). They are not seven desired operating
  combinations. The desired operation weights 1, 3, and 4 contain
  `C(4,1)+C(4,3)+C(4,4) = 9` of the 16 input states.

- Shannon's symmetric-function definition says the `a`-numbers count variables
  equal to zero (printed p. 40, PDF p. 43; the level-count explanation is on
  printed p. 43, PDF p. 46). Thus `A = S₄(1,3,4)` on printed p. 52 is
  consistent with the nine desired operation states when “weight” means the
  number of operated, zero-hindrance relays. The complement `A' = S₄(0,2)`
  appears on printed p. 53 (PDF p. 56).

- The source reports Fig. 30 “requires 20 elements” (printed p. 52/PDF p. 55),
  then says the symmetric-function circuit contains 15 elements (printed p.
  53/PDF p. 56), followed by a 14-element result in the same p. 53–54/PDF
  p. 56–57 sequence. Printed p. 14 (PDF p. 17) explains that expression
  letters represent make/break relay contacts or switch-blade-and-contact
  elements. These are network-element/contact counts, not Boolean states or
  counts of the four relay names.

## Deterministic check and bounded correction

The prior visual/source check retains rendered pages and the trace under
`../content-book-ch03-context-research/.agent/shannon-selective-pages/` and
`../content-book-ch03-context-research/.agent/shannon-selective-count.py`.
The trace evaluates all 16 hindrance
tuples against the seven printed terms: 9 desired-operation states, 7
hindrance states, and zero mismatches.

The chapter phrase “a sum of seven product terms enumerating each operating
combination” should therefore be narrowed to the seven-term *hindrance*
expression, covering the seven non-operation states (weights 0 and 2), while
the desired operation covers weights 1, 3, and 4. Define Shannon's
zero-hindrance convention near the notation.

## Figure-attribution uncertainty and limits

The 15-element statement follows Fig. 31 on printed p. 53. The text then
introduces `A'`, Fig. 32, dualization, and Fig. 33; the “14 elements” sentence
lands at the p. 53 bottom while Fig. 33 begins on p. 54. The 14 count and the
source's “probably the most economical circuit of any sort” wording are
verified as a sequence, but this record does not assign the count to one
figure without resolving that page-break referent. It does not independently
recount every drawn contact or accept any other Chapter 3 claim.
