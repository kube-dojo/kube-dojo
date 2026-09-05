# EDVAC citation: direct evidence and limits

Scope: #2373, research only. This record separates the presence of a citation from claims about uniqueness, priority and subsequent influence. Independent source review is pending.

## Inspected source

John von Neumann, *First Draft of a Report on the EDVAC*, [Internet Archive scan](https://archive.org/download/firstdraftofrepo00vonn/firstdraftofrepo00vonn.pdf), retrieved 2026-09-05. HTTP200, application/pdf,7,234,506bytes; SHA256 `3e229fb12656f92841bbfaf811c40899253ba27748360d6d795b513022404fe9`. PDF metadata reports216pages. That is a scan-page count, not the report's numbered-page count.

Local page images were rendered and inspected:

- PDF page3: title page names von Neumann, the Moore School and June30,1945.
- PDF page35, printed12: §4.2 discusses an all-or-none neuron analogy, excitatory/inhibitory synapses and synaptic delay, then explicitly cites Pitts and McCulloch's1943 paper.
- PDF page37, printed13: the citation's sentence continues with aspects of neuron functioning omitted by the simplification. The next paragraph says these simplified functions can be imitated with telegraph relays or vacuum tubes. §4.3 then discusses vacuum-tube elements.

Use the printed-page and PDF-page locators together. The citation spans printed12–13; it is not all on the twelfth PDF page. PDF page213 was also inspected, but that image does not establish a visible final page number; no complete pagination audit is claimed.

## Reassessment of the earlier Green record

The April record in `sources.md` treated an OCR search for `Vol.` and `Bull.` as proof that this was the sole journal citation. That search cannot rule out differently formatted references, OCR omissions or non-journal sources. Its reported outcome is retained as historical evidence of a search, not accepted as a comprehensive citation census. The uniqueness claim remains unverified; this reassessment does not assert that another journal citation exists.

The inspected passage supports explicit citation and a connection between simplified neuron functions and proposed computing elements. It does not by itself establish sole authorship of stored-program architecture, priority, the entire subsequent influence chain, or the chapter's fixed two-and-a-half-year interval. Such claims require separate evidence. A future prose correction should use the direct design connection without those additions.

Local `pdftotext` was unavailable (exit127); web extraction contained OCR noise and the web find calls returned errors. Page images, not a reconstructed text search, supplied this turn's evidence. Cache: `.agent/sources/edvac.pdf` and `edvac-{3,35,37,213}.png`; excluded from commits. The MIT and Computer History Museum copies were located but not independently page-verified here.
