# Infrastructure Log: Chapter 2 — The Universal Machine

Technical and institutional metrics relevant to the chapter's infrastructure-history thesis. Each row is what made the 1936 results *operationally* possible — and what their operational limits were. The chapter's infrastructure story is unusual: there were no machines. The "infrastructure" is publication venues, journal turnaround times, postal-mail communications between Princeton and Cambridge, and the institutional weight that allowed two unknown mathematicians to publish results in flagship journals within months of each other.

## The Mathematical Infrastructure (1928-1936)

| Item | Value | Verification |
|---|---|---|
| Hilbert's textbook venue | *Grundzüge der theoretischen Logik*, 1st ed. (Berlin: Springer, 1928), with a 1931 second printing of the 1st edition | Yellow — primary book not retrieved this session; attestation via Turing 1936 §11 p.259 footnote citing "(Berlin, 1931), chapter 3" |
| Hilbert's address venue | "Probleme der Grundlegung der Mathematik," delivered Bologna ICM Sept 3-10, 1928, published *Mathematische Annalen* 102 (1930), pp. 1-9 | Yellow — secondary attestation; out of chapter's load-bearing scope |
| Gödel's announcement | Announced to the Vienna Academy of Sciences in 1930 (Königsberg conference 7 October 1930 is the standard secondary date) | **Green** — Braithwaite intro to Meltzer 1962 ed. p.vii; verified by Claude `pdftotext` 2026-04-28. The Königsberg-vs-Vienna distinction is a Yellow upgrade. |
| Gödel's publication | *Monatshefte für Mathematik und Physik* 38 (Leipzig, 1931), pp. 173-198 | **Green** — Braithwaite intro to Meltzer 1962 ed. p.vii; verified by Claude `pdftotext` 2026-04-28. |
| Gödel's paper length | ~25 pages (pp. 173-198 = 26 pages including title) | **Green** — Braithwaite intro to Meltzer 1962 ed. p.vii ("the 25 pages of the *Monatshefte für Mathematik und Physik*"). Verified by Claude `pdftotext` 2026-04-28. |

## Church's Publication Infrastructure (1933-1937)

| Item | Value | Verification |
|---|---|---|
| Stepping-stone publication venue | *Annals of Mathematics* 34 (1933), p. 863; *American Journal of Mathematics* 57 (1935), pp. 153-173, 219-244 (Kleene) | Yellow — attestation via Church 1936 footnote pp.345-346; specific stepping-stone papers not retrieved this session |
| Presentation venue | American Mathematical Society, April 19, 1935 | **Green** — Church 1936 p.345 footnote; verified by Claude `pdftotext` 2026-04-28 |
| Primary publication venue | *American Journal of Mathematics* 58, no. 2 (April 1936), pp. 345-363 | **Green** — Church 1936 cover page; verified by Claude `pdftotext` 2026-04-28 |
| Companion publication | *Journal of Symbolic Logic* 1, no. 1 (March 1936), pp. 40-41 ("A Note on the Entscheidungsproblem") | Yellow — Cambridge Core direct fetch returned interstitial 2026-04-28; volume/page numbers attested via Turing 1936 p.231 footnote ‡ |
| JSL correction | *Journal of Symbolic Logic* 1, no. 3 (September 1936), pp. 101-102 | Yellow — secondary attestation; not retrieved this session |
| Review of Turing | *Journal of Symbolic Logic* 2, no. 1 (March 1937), pp. 42-43 | Yellow — Stanford Encyclopedia attestation; specific volume not retrieved this session |
| Presentation-to-publication gap | Church 1936: 12 months (presented April 1935; published April 1936). Turing 1936: 8 months between manuscript receipt (28 May 1936) and read date (12 November 1936); 17 months between receipt and publication (1937, Vol 42 of LMS Proc.) | **Green** — verified against the explicit dates on Church 1936 p.345 and Turing 1936 p.230 |

## Turing's Publication Infrastructure (1936-1937)

| Item | Value | Verification |
|---|---|---|
| Manuscript composition site | King's College, Cambridge, 1935-spring 1936 (specific composition timeline pending Hodges 1983) | Yellow |
| Receipt by LMS | 28 May 1936 | **Green** — Turing 1936 cover-page header p.230. Verified by Claude `pdftotext` 2026-04-28 |
| Appendix dated | 28 August 1936 | **Green** — Turing 1936 p.263. Verified by Claude `pdftotext` 2026-04-28 |
| Appendix return address | "The Graduate College, Princeton University, New Jersey, U.S.A." | **Green** — Turing 1936 p.265. Verified by Claude `pdftotext` 2026-04-28 |
| Read at LMS | 12 November 1936 | **Green** — Turing 1936 cover-page header p.230. Verified by Claude `pdftotext` 2026-04-28 |
| Published | *Proceedings of the London Mathematical Society*, Series 2, Vol. 42 (1937), pp. 230-265 | **Green** — Turing 1936 cover page; verified by Claude `pdftotext` 2026-04-28. The journal's part-publication structure (the "VOL. 42. NO. 2144." marker between pp.241-242) attests publication in two installments. |
| Length | 36 pages (pp. 230-265), plus 3-page correction in Vol. 43 (1937), pp. 544-546 | **Green** for the 230-265 main paper; Yellow for the correction (not retrieved this session) |
| Footnote attestation of Church | Turing 1936 §1 p.231 footnote † (Church 1936 *Am. J. Math.*) and ‡ (Church 1936 *JSL* note) | **Green** — verified by Claude `pdftotext` 2026-04-28 |

## Computational Infrastructure: There Was None

The chapter's structurally interesting infrastructure point: in 1936, when both papers proved their negative results about computation, no general-purpose programmable digital computer existed anywhere. The closest extant computational substrates were:

| System | Status circa 1936 | Why it does not appear in the chapter's load-bearing claims |
|---|---|---|
| Mechanical calculators (Burroughs, Marchant, Friden) | Mature commercial product | Not programmable; not Turing-complete; out of scope |
| Differential analyzers (Vannevar Bush at MIT, 1931) | Operational but analog | Cross-link to Ch7 (the analog bottleneck); not relevant to Ch2's *mathematical* claims |
| Relay-based devices (Stibitz at Bell Labs, 1937) | Just begun | Post-dates Turing 1936; cross-link to Ch7/Ch8 |
| Konrad Zuse's Z1 (Berlin, 1936) | Mechanical, programmable, in development | Independent of the Turing/Church work; out of chapter scope |
| IBM tabulators | Mature commercial product | Not programmable in the Turing sense; out of scope |

The chapter's stance: **the universal computing machine was a mathematical object, not a physical one.** Turing 1936 §6 describes it; nothing in 1936 ran it. The connection between the §6 universal machine and the post-1945 stored-program computers belongs to Ch8.

## Communication Infrastructure (1935-1936)

The story's "infrastructure" is partly the *postal mail* between Cambridge and Princeton. The chapter should foreground:

| Item | What we know | Verification |
|---|---|---|
| Mail crossing time, Cambridge ↔ Princeton, 1936 | ~7-10 days each way via transatlantic liner | Yellow — standard for the period; specific anchor not searched this session |
| Likely route by which Turing learned of Church | The April 1936 *Am. J. Math.* issue and/or the March 1936 *JSL* note arriving in Cambridge in spring/summer 1936; possibly a copy sent personally between mathematicians; possibly Newman noticing Church's paper and bringing it to Turing's attention | Yellow — secondary; specific route not anchored. Stanford Encyclopedia (Copeland) confirms only the *fact* that Turing learned mid-process. |
| Princeton-as-destination | Newman wrote to Church recommending Turing for Princeton; standard secondary attestation; specific Newman-to-Church correspondence pending Hodges page anchor | Yellow |
| Turing's transatlantic crossing | Standard secondary attestation: Turing sailed for the US in late September 1936 on the *Berengaria* (or similar — Hodges 1983 has the specific ship). The August 28 appendix dated from Princeton predates this typical secondary timing, suggesting either a date discrepancy or that Turing arrived earlier than secondary literature usually says | Yellow — flagged as conflict-noted in `sources.md` Conflict Notes |

## Operational Limits Worth Naming in Prose

These are the infrastructure constraints the chapter should foreground when explaining the 1936 moment:

- **No machines.** The universal computing machine was described mathematically; no physical instance existed. This is structurally similar to Ch1's framing (Boole's algebra "trapped on paper") and is what the chapter must close with: the bridge from theory to engineering had not been crossed.
- **Two journals carrying the news.** The April 1936 *Am. J. Math.* and the November 1936 / 1937 *Proc. LMS* are the two publication venues that carried the chapter's central results. Both are pre-arXiv-era flagship venues with multi-month publication lags.
- **Slow mail.** Transatlantic correspondence between Cambridge and Princeton, even at first-class postal speed, ran 1-2 weeks each way. Turing learned of Church's work *via* this mail infrastructure; the appendix-after-receipt structure of his paper is what his postal infrastructure permitted.
- **Print-only equivalence proof.** Turing's appendix proves λ-definability ↔ computability without any computational verification — the "running the proof" idiom is post-1945. In 1936, mathematical proofs were checked by other mathematicians reading them, full stop.
- **No proceedings beyond the journal.** Unlike the Dartmouth conference of Ch11, there is no "summer conference" gathering the principals. Church and Turing met in person only after Turing arrived at Princeton in autumn 1936. The pre-meeting correspondence was via letters and journal articles.

## Notes

- The chapter's *infrastructure* claim is unusual: it is a chapter about computing in which no computer appears. The infrastructure is mathematical journals, university institutions (Princeton, Cambridge, Göttingen, Vienna), and the international mathematical community's mail-and-print communication channels. The chapter should foreground this.
- The §6 universal computing machine is itself an *infrastructure description* — it is the architectural specification of a machine that does not yet exist. The chapter should treat the §6 description with the same rigor it treats real infrastructure in later chapters (e.g., the JOHNNIAC at RAND in Ch11).
- "How many copies of *Proc. LMS* Vol. 42 were printed" / "how many people read Turing 1936 in 1937" / "how many Princeton seminars discussed it" — these are infrastructure questions the chapter should *not* try to answer without primary anchors. Hodges 1983 may have figures; do not invent.
