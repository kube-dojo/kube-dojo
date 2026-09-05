# Chapter 2 remaining research: chronology, machines, and modern limits

Checked 2026-09-05 against `src/content/docs/ai-history/ch-02-the-universal-machine.md` at
revision `7a9d5c52664aaa452402c9c76cfeee3d6206a5ab`, and the reviewed mathematical record
`mathematical-corrections-2026-09-05.md`. Research record only: no prose acceptance or
lifecycle decision. The chapter file was not edited in this packet.

## Gödel chronology

- The affected paragraph begins “The first two pillars...” and says that Gödel announced
  the result “in October 1930” to the Vienna Academy, then published the detailed proof
  the following year. The Oxford critical-edition note, [Feferman et al., *Gödel
  Collected Works I*, pp. 126–139](https://academic.oup.com/book/55022/chapter/422805314),
  abstract lines 79–81, literally labels the items **1990b** and **1991** and states that
  the first was presented by **Hans Hahn on 23 October 1930**, while the full text of the
  second was received by *Monatshefte* on **17 November 1930**. The page does not expose
  enough bibliography to determine whether those labels are editorial identifiers or a
  rendering error; do not silently normalize them to 1930b/1931. The historical dates
  support the month and the 1931 publication framing, but not Gödel personally making an
  in-person announcement.
- The Oxford page exposes the abstract and bibliography but reports that the chapter is
  access-restricted (line 90); an original scan of the 1930 notice and full 1931 article
  was not inspected here. Conservative correction: identify the 23 October presentation
  as Hahn presenting Gödel’s short abstract, and separate the November receipt from the
  1931 publication. Do not infer more of the notice’s contents from the abstract alone.

## Physical-machine claim

- The affected passage begins “The year 1936 was not the year the computer was
  invented” and says “No physical machine was built, no wires were soldered, and no
  vacuum tubes were illuminated.” The [Konrad Zuse Internet Archive, Z1](https://zuse.zib.de/z1),
  lines 242–256, records a mechanical computer designed 1935–36 and **built 1936–38**,
  with punched-tape instructions, memory, control, arithmetic and I/O; it says the only
  electrical unit was a motor and that the machine had no relays (lines 247–252).
- The [Deutsches Technikmuseum Berlin computer history page](https://technikmuseum.berlin/en/exhibitions/permanent-exhibition/computers/),
  lines 90–101 and 116–126, independently dates the Z1’s construction to 1936–38 and
  calls it mechanical and freely programmable, while reserving “first fully functioning”
  for the relay-based Z3 presented in 1941. Raúl Rojas’s academic reconstruction at
  [Freie Universität Berlin](https://www.mi.fu-berlin.de/inf/groups/ag-ki/publications/Z1-Architecture/index.html),
  lines 8–14, dates the Z1 to 1936–38, notes punched-tape instructions and **no
  conditional branching**, and says its description is reconstructed from blueprints,
  letters and notebooks.
- These institutional/academic sources support physical construction work spanning 1936–38
  and a limited programmable machine completed in 1938, but do **not** establish that Z1
  implemented Turing’s universal machine, was reliable, or was a stored-program universal
  computer. The broad sentence is
  therefore materially misleading unless scoped explicitly to a physical implementation
  of Turing’s U specification. The nearby “no ... electromechanical contraption ...
  answered to the universal machine’s specification” claim remains unresolved: Z1’s
  existence does not prove that it met that specification, and no source reviewed here
  proves the negative. Recommended boundary: distinguish Turing’s mathematical U from
  contemporaneous physical programmable machines and avoid “no physical machine” as an
  unqualified statement.

## Modern epilogue claims

- The note says **every** production computer reads instructions and data from the same
  memory. That universal is unsupported and conflicts with a current production MCU
  family’s own documentation: [Microchip tinyAVR 1-series architecture](https://onlinedocs.microchip.com/oxy/GUID-B990D80E-52D0-4869-8631-E8A045F89631-en-US-4/GUID-F9B6741C-7F50-477E-81A8-5423F10CD41A.html), §9.3 lines 128–142, specifies Harvard architecture with separate program/data buses and spaces. The Arm M7 TRM was also opened, but separate I/D caches alone do not establish a separate address-space counterexample and are not relied on here. Proposed scope: “many general-purpose stored-program systems are usefully modeled in a Turing-style way.”
- Turing’s primary text, [*On Computable Numbers*](https://www.cs.virginia.edu/~robins/Turing_Paper_1936.pdf), §8 PDF pp.17–18 (lines 706–776), proves no general machine decides circle-freeness or whether an arbitrary machine prints a symbol; §11 PDF p.29 (lines 1158–1181) applies this to provability. This supports an undecidability analogy, not the exact modern words “static analyser,” “antivirus,” or “formal verification.”
- [Rice, “Classes of Recursively Enumerable Sets and Their Decision Problems,” AMS PDF](https://www.ams.org/journals/tran/1953-074-02/S0002-9947-1953-0053041-6/S0002-9947-1953-0053041-6.pdf), pp.358–366 (PDF access returned an error here), and the [SEP exposition](https://plato.stanford.edu/entries/recursive-functions/), Theorem 3.4 lines 743–760, support undecidability of non-trivial semantic program properties, including total output/correct computation. The [academic program-analysis chapter](https://link.springer.com/chapter/10.1007/978-3-319-96142-2_8), lines 245–253, applies the limitation to sound, nontrivial precise verification. This supports “no sound-and-complete automatic decision procedure for every nontrivial semantic property,” not “formal verification stops at proof-decidable subsets.”
- [NIST SP 800-83](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-83.pdf) was published in **November 2005** and **withdrawn on July 22, 2013**, superseded by SP 800-83 Rev. 1, according to the [NIST publication record](https://csrc.nist.gov/pubs/sp/800/83/final) (publication date and withdrawal notice, checked 2026-09-05). Its §3.4.1.1 PDF pp.32–33 / lines 1266–1287 documents signatures, heuristics, false positives and false negatives; §3.4.1.3 PDF p.35 / lines 1361–1385 says antivirus cannot stop all incidents. This is historical operational evidence, not a current capability statement or formal theorem that every binary cannot be classified. Recommended correction boundary: call the antivirus example an inference from undecidability plus observed heuristic limits, and replace the formal-verification absolute with the narrower automatic-verification claim above.

Access receipts (2026-09-05): Oxford abstract lines 79–81 were visible but full chapter access was denied at line 90; ZIB, Technikmuseum, FU Berlin, Microchip, Turing, SEP, Springer and NIST text/locators opened; the AMS Rice PDF URL returned an internal retrieval error, so its scope is retained only as bibliographic/locator context and SEP carries the usable theorem text.

Remaining gaps: no primary scan of Gödel’s October notice was available in this check; no evidence here settles whether any 1936 physical machine satisfied Turing’s exact U specification; no source was found proving the chapter’s literal “every computer” architecture universal. Broader chronology, lineage and modern-technology review remain open under #2329.
