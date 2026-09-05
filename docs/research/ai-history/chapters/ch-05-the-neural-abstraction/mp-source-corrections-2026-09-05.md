# McCulloch–Pitts 1943 source corrections (2026-09-05)

Research-only record for #2373. It records source and locator evidence for review.

## Retrieval record

- CMU requested URL: <https://www.cs.cmu.edu/~./epxing/Class/10715/reading/McCulloch.and.Pitts.pdf>; final URL after redirect: <https://www.cs.cmu.edu/~epxing/Class/10715/reading/McCulloch.and.Pitts.pdf>. Retrieved 2026-09-05 06:45:14 GMT, HTTP 200, 1,272,966 bytes, SHA-256 `6506f2cdcef8d4701bdf238a0f2fa9a40c11f6c0701a6c65e2582a88b7db43d0`.
- The CMU file is a 17-page 1990 *Bulletin of Mathematical Biology* reprint. Visible page labels run 99-115; the scan is not an original 1943-pagination facsimile. Layout extraction SHA-256: `0f27e0334637e82a1d52d803bf199bc37b34e6f1fb1f1885ccdbc0af3345bc5c`.
- Comparison copy: <https://jontalle.web.engr.illinois.edu/uploads/410-NS.F22/McCulloch-Pitts-1943-neural-networks.pdf>. Retrieved 2026-09-05 06:46:03 GMT, HTTP 200, 890,301 bytes, SHA-256 `d9ec459b95fad84f348c63d6a2d964ce8c9a65ae4afd1cebf0195ad86c764d0a`. Its 21 pages are a 2008 seminar retypeset with `-1-` style labels, not an original-pagination facsimile; it cannot establish original locators.

## Pagination disposition

The CMU footer says “Reprinted from” volume 5, pages 115-133, while the visible reprint labels are 99-115. Those facts do not establish an original-page locator, and the difference in page counts alone does not prove that original text was omitted or reflowed. Original 1943 pagination remains unverified in this packet.

The directly inspected visible map is PDF page 1 → reprint 99, 3 → 101, 4 → 102, 6 → 104, 7 → 105, 10 → 108, and 17 → 115. Do not call the old ledger's original-page labels verified from this copy; reviewers should use this record's visible locators. Earlier dated records remain historical.

## Technical evidence corrections

- Visible reprint 99 prints axon velocities `< 1 m s−1` and `> 150 m s−1`, and latent addition `< 0.25 ms`; visible 100 prints synaptic delay `> 0.5 ms` and some inhibitions `< 1 ms`. These are source-visible inequalities, not reconstructed values.
- Visible 101 contains the five physical assumptions. Visible 102 supports the upright `E` existential operator, the implication arrow, and `N_i(t)` measured in synaptic delays. Neither observation supplies an original 1943 page number.
- Visible 104-105 presents a **conjoined negation** construction, not an unqualified bare NOT gate: `N3(t) ≡ N1(t−1) · ¬N2(t−1)`. The negated input is conjoined with an excitatory input and evaluated at one synaptic time-step, so teaching text must retain both conditions.
- The realizability discussion states that the following theorems use the extended sense and that sharper narrow-sense results may be available. Theorems 2-3 therefore need their stated TPE/truth-table conditions; they do not support an unqualified claim about every logical form.
- Visible 104, after the Theorem 2 construction, explicitly allows an indefinite number of topologically different nets realizing a TPE. The chapter's claim that a formula produces one specific net should not imply uniqueness of realization.
- Visible 108 states Theorem 7, “Alterable synapses can be replaced by circles.” The paper also describes equivalent fixed-connection nets as a formal representation and explicitly does not present that equivalence as a biological explanation. This is not a learning algorithm or evidence that biological learning works by the paper's construction.
- The visible literature entry at 115 prints Hilbert and Ackermann as 1927, while the Theorem 3 discussion at 104 cites them as 1938. Independent edition metadata verified elsewhere gives a 1928 edition. Preserve these as citation-specific source discrepancies; this packet does not establish which edition the authors used or silently undo the existing #2213 treatment.

## Access limits

No independently verified original-pagination facsimile was obtained. The CMU and Illinois copies support the visible reprint/retypeset observations above, but not original page conversion. Any prose using original page numbers, claims about omitted pages, or stronger biological interpretation needs a separately verified source.
