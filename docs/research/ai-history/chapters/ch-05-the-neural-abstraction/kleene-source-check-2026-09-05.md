# Kleene source check — 2026-09-05

Research-only record for the McCulloch–Pitts / finite-automata relationship.
This does not accept Chapter 5 or resolve its other historical claims.

## Source provenance and access

The full text was retrieved from the University of Alicante copy:
<https://www.dlsi.ua.es/~mlf/nnafmc/papers/kleene56representation.pdf>
(HTTP 200, retrieved `2026-09-05T06:46:45Z`, SHA-256
`81bf002582db2b3b6dc0324f4b2ff370db3a5ea56657165388dbd8bd4e02ba3c`). A
second copy is hosted by the Slovak University of Technology:
<https://www2.fiit.stuba.sk/~kvasnicka/CognitiveScience/2.prednaska/kleene56representation%5B1%5D.pdf>
(HTTP 200, retrieved `2026-09-05T06:47:03Z`, SHA-256
`acca19f8843427d8ea33a0ea4d4384ea6e3268e51d896fb3c6dd31f72fa94d43`).

Both are 44-page standalone PDF reproductions with the same visible pagination
and substantive transcription. Their hashes differ, but matching layout,
pagination, and typographic/custom-font behavior indicate copies of the same
underlying reproduction; they are **not independent textual confirmations**.
The clean A4-like typography and modern PDF metadata do not establish that
either is a facsimile scan of the 1956 book. They may be retypeset or
reformatted reproductions. I therefore treat the visible page images as a
reproduction of the primary text, while leaving its production history
unknown.

Publisher metadata was checked at <https://doi.org/10.1515/9781400882618-002>
and the JSTOR record at <https://www.jstor.org/stable/j.ctt1bgzb3s> (both
checked 2026-09-05). They identify Kleene’s chapter in *Automata Studies*
(AM-34, 1956); De Gruyter gives chapter pages 3–42. The publisher preview
<https://api.pageplace.de/preview/DT0400.9781400882618_A26693444/preview-9781400882618_A26693444.pdf>
(HTTP 200, retrieved `2026-09-05T06:44:02Z`, SHA-256
`9ae6331e1aa3142ba7b0bd0f03205df248e04f0970fb2ddaf76a6c4a0bbb9c95`) exposes
only the opening portion. Its printed p. 3 (preview PDF p. 14) says the article
is drawn from RAND RM-704 (15 December 1951).

The standalone PDFs show visible pages 1–44; the locators below use those
visible numbers plus section/theorem names. The preview establishes an early
book-page correspondence (book p. 3 at preview PDF p. 14), but no later book
offset is inferred. The 1956 citation block itself says pp. 3–41, while
publisher metadata says pp. 3–42; this pagination discrepancy remains open.

## Verified page-level relationship

Page references are to the standalone reproduction’s visible printed numbers.

* **pp. 1–3, §§1–2:** Kleene names McCulloch and Pitts’s 1943 paper and
  treats an M–P nerve net as his chosen example of a finite automaton. He calls
  the M–P assumptions an abstraction from neurophysiology, not an exact
  biological account, and notes that alternative assumptions can yield the
  same behavior. Nothing here establishes a causal or priority story.
* **p. 31, §7.3, Theorem 3:** every regular event has a nerve-net
  representation, with suitable initial inner-neuron states.
* **p. 35, end §7.4 / Part II:** Kleene states that an M–P nerve net can
  represent every event representable by another finite digital automaton,
  explicitly limiting “finite digital automaton” to the definitions developed
  in Section 8.
* **p. 36, §§8.1–8.2:** an M–P nerve net is a particular finite automaton;
  Kleene’s finite automata have finitely many cells and states. This is a
  model-class inclusion, not an identity between every automaton and an M–P
  net.
* **p. 37, §9, Theorem 5:** an event represented by a given state of any
  finite automaton, “in particular” an M–P net, started at time 1 in a
  specified internal state `b1`, is regular. Together with Theorem 3, this
  gives the two directions for a qualified same-event-class statement.
* **pp. 38–39:** Theorem 5’s proof uses the finite state/transition relation;
  it is not a theorem about unrestricted computation or physical circuits.
* **p. 40, §9 discussion and Appendix §10; p. 42, §11:** finite cells/states and
  initial-state conditions matter. A Turing machine with its unbounded tape as
  part of the machine is not a finite automaton; Theorems 6 and 7 address
  infinite-past and arbitrary-initial-state cases. Theorem 8 at p. 42, §12
  separately concerns primitive recursiveness of regular events.

## Conservative disposition

Safe wording is: “Kleene’s 1956 treatment placed McCulloch–Pitts nerve nets
inside a finite-state automaton framework. Under his finite-state definitions
and stated initial-state conditions, Theorems 3 and 5 connect the same regular
event class to nerve-net and finite-automaton representations.” This supports a
formal relationship, not “M–P directly led to finite automata,” historical
inevitability, priority, biological fidelity, or equivalence with arbitrary
computation. The chapter’s other claims remain outside this packet.

The 1951 RAND predecessor is separately identified at
<https://www.rand.org/content/dam/rand/pubs/research_memoranda/2008/RM704.pdf>
(original host returned HTTP 403 on 2026-09-05); a mirror copy exists at
<https://gwern.net/doc/ai/nn/1951-kleene.pdf>. Its page references must not be
silently presented as 1956 pagination or as independent confirmation.
