# Sources: Chapter 22 - The Lisp Machine Bubble

## Source Table

| Source | Type | Anchor | Use | Status |
|---|---|---|---|---|
| Lisp Machine Group, [*"LISP Machine Progress Report"*](https://bitsavers.org/pdf/mit/ai/aim/AIM-444.pdf), MIT AI Memo 444, August 1977 | Primary technical memo / scanned PDF OCR | pp.1-5, 7-8, 26-29 | Time-sharing problem, personal-computer design, PDP-10 address-space limits, CONS hardware, all-Lisp I/O/editor, LUNAR/Macsyma status, plan for more machines | Green |
| Thomas F. Knight Jr., David A. Moon, Jack Holloway, Guy L. Steele Jr., [*"CADR"*](https://bitsavers.org/pdf/mit/ai/aim/AIM-528.pdf), MIT AI Memo 528, May 1979 | Primary technical memo / scanned PDF OCR | pp.1-4 | CADR processor design, relationship between CADR and Lisp machine, writable microcode, stack support, virtual memory, 24-bit virtual address mapping | Green |
| Daniel Weinreb and David Moon, [*Lisp Machine Manual, Fourth Edition*](https://bitsavers.org/pdf/mit/cadr/chinual_4thEd_Jul81.pdf), MIT AI Lab, July 1981 | Primary system manual / scanned PDF OCR | front matter, pp.1-2 | Zetalisp, "operating system"-like environment, all-system-programs-in-Lisp, personal computation, Maclisp compatibility, MIT AI Lab software culture | Green |
| Symbolics, Inc., [*Symbolics 3600 Technical Summary*](https://bitsavers.org/pdf/symbolics/3600_series/3600_TechnicalSummary_Feb83.pdf), February 1983 | Vendor technical summary / scanned PDF OCR | pp.2-18, 31-46 | Productized 3600 pitch, MIT-to-Symbolics history, LM-2, 3600 design, tagged architecture, system software, networking, graphics, Zmacs, applications, Common Lisp compatibility | Green |
| Richard P. Gabriel and Guy L. Steele Jr., [*"The Evolution of Lisp" (HOPL II uncut version)*](https://www.dreamsongs.com/Files/HOPL2-Uncut.pdf), 1993/1996 | Later participant-history paper / author-hosted PDF | pp.22-31, 36-44 | PDP-10/VAX context, Lisp-machine wave, MIT commercialization, LMI/Symbolics split, Common Lisp meeting, portability, later stock-hardware pressure | Green |
| Daniel Weinreb, ["What happened to Symbolics?"](https://danluu.com/symbolics-lisp-machines/) archived by Dan Luu | Participant retrospective / archived web page | Not yet parsed in local evidence set | Potential stretch source for failure causes; must be labeled participant memory and checked before prose | Red |
| Richard Stallman, ["My Lisp Experiences and the Development of GNU Emacs"](https://www.gnu.org/gnu/rms-lisp.html) | Participant retrospective / partisan conflict source | Not yet parsed in local evidence set | Possible context for Symbolics/LMI conflict and software-sharing dispute; do not use as neutral chronology without balancing sources | Red |
| Wikipedia, ["Lisp machine"](https://en.wikipedia.org/wiki/Lisp_machine) | Tertiary discovery source | Discovery only | Useful for names, dates, and source discovery; not a prose anchor | Red |

## Claim Matrix

| Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|
| MIT's Lisp Machine Group framed the machine as a high-performance, economical implementation of Lisp, motivated by AI's heavy use of Lisp and the mismatch between large interactive Lisp programs and time-shared PDP-10 systems. | Time-Sharing Wall | AIM-444 pp.1-3 | Green | Use as opening frame; avoid making this only a hardware story. |
| Maclisp and InterLisp had grown around the PDP-10, but the AI Lisp community was hitting architectural limits that language modifications could no longer hide. | Time-Sharing Wall | AIM-444 pp.2-3 | Green | Useful for why a new machine seemed rational. |
| Highly interactive AI programs, editors, debuggers, MACSYMA, and programming assistants stressed throughput, response time, swapping, and memory competition on time-shared systems. | Time-Sharing Wall | AIM-444 pp.3-4 | Green | This is the human-facing pain: response time and thrashing. |
| The Lisp Machine design gave each user a personal processor and memory, with shared network resources, rather than time-division-multiplexing processor and memory among logged-in users. | Personal Computing for AI | AIM-444 pp.3-5; Manual pp.1-2 | Green | Core contrast with Project MAC/time-sharing. |
| The project explicitly valued service to the interactive user over system-wide efficiency, giving each user full processor and disk throughput and avoiding other users' swapping behavior. | Personal Computing for AI | AIM-444 pp.4-5 | Green | Good sentence for the infrastructure philosophy. |
| PDP-10 address-space limits caused trouble for MACSYMA and Woods's LUNAR; AIM-444 described future intelligent systems as possibly needing five to ten times the PDP-10 address space. | Time-Sharing Wall | AIM-444 pp.4-5 | Green | Anchor for address-space pressure; do not overgeneralize to all AI. |
| The Lisp Machine used a 24-bit virtual address space and compact instruction set to make larger Lisp systems practical. | CONS to CADR | AIM-444 pp.4-5; AIM-528 pp.2-3 | Green | Good bridge from software pain to hardware answer. |
| CONS was the prototype processor designed by Tom Knight; by early 1977 the prototype had memory, disk, terminal, paging, keyboard, mouse, TV, and PDP-10 file I/O working. | CONS to CADR | AIM-444 pp.5, 27-29 | Green | Keep "prototype" and dates precise. |
| By August 1977 LUNAR had been converted and ran about three times faster than Maclisp on a KA-10, while LUNAR and Macsyma could reside together with room left on the Lisp Machine. | CONS to CADR | AIM-444 pp.28-29 | Green | Strong capacity scene; avoid turning into universal benchmark. |
| The CADR memo defines CADR as the processor and the Lisp machine as CADR plus microcode interpreting the Lisp machine order code. | CONS to CADR | AIM-528 pp.2-3 | Green | Important terminology guardrail. |
| CADR was a 32-bit microprogrammable processor with writable microcode, stack-oriented support, 16K microprogram memory, and virtual paging from 24-bit virtual to 22-bit physical addresses. | CONS to CADR | AIM-528 pp.2-4 | Green | Technical texture; use sparingly. |
| CADR was influenced by Lisp but avoided wiring in a single Lisp instruction format; its efficiency came from writable microcode and features useful for stack and pointer manipulation. | CONS to CADR | AIM-528 pp.3-4 | Green | Helps avoid "single-purpose toy" framing. |
| AIM-444 says Lisp Machine I/O software was essentially all written in Lisp, with only timing-critical read/write operations in microcode. | Operating System in Lisp | AIM-444 pp.7-8 | Green | Strong all-Lisp system claim. |
| AIM-444 describes an advanced real-time display editor written completely in Lisp, drawing on EMACS, using high-speed display, self-documentation, user-extensible commands, and mouse interaction. | Operating System in Lisp | AIM-444 pp.26-28 | Green | Use for lived environment scene. |
| AIM-444 notes that sophisticated display interaction reduced device independence: the Lisp Machine could not be used remotely over the ARPANET as an ordinary terminal system. | Operating System in Lisp | AIM-444 p.8 | Green | Nuance: integration had tradeoffs. |
| The 1981 Lisp Machine Manual describes both the language and operating-system-like parts of the Lisp Machine, with Zetalisp as a Maclisp-related dialect and system programs written in Lisp. | Operating System in Lisp | Manual front matter, pp.1-2 | Green | Good evidence for language/environment fusion. |
| The Symbolics 3600 Technical Summary presents the 3600 as a 36-bit single-user computer for high-productivity software development and large symbolic programs, combining supermini power with a dedicated workstation. | 3600 Bet | Symbolics 3600 pp.2-3 | Green | Vendor source; use as product pitch, not independent market proof. |
| Symbolics claimed more than half a million lines of accessible system code, object-oriented techniques throughout, and an integrated environment without the usual operating-system/language division. | 3600 Bet / Operating System in Lisp | Symbolics 3600 p.2 | Green | Vendor source but technically specific. |
| Symbolics listed applications including AI, CAD, expert systems, simulation, signal processing, education, physics, animation, VLSI, speech, vision, and natural-language understanding. | 3600 Bet | Symbolics 3600 pp.2-3 | Green | Shows broad market ambition; do not imply adoption. |
| Symbolics traced the Lisp Machine concept to hardware economics and software demands that made personal networked computers more attractive than timeshared systems; it said the MIT project began in 1974. | Commercializing the Lab | Symbolics 3600 p.4 | Green | Vendor history; consistent with MIT sources. |
| Symbolics states CONS ran in 1976, CADR was introduced in 1978, Symbolics formed in 1980, LM-2 was introduced in 1981, and the 3600 was developed from 1979 to 1982 as a fourth-generation Lisp Machine. | Commercializing the Lab | Symbolics 3600 p.4 | Green | Use for product-line chronology. |
| The 3600 environment included Zetalisp, Flavors, macros, packages, streams, incremental compilers, dynamic loading, display debugger, condition system, Ethernet, Interlisp compatibility, FORTRAN 77 toolkit, and MACSYMA. | 3600 Bet | Symbolics 3600 pp.5-7, 13-21, 31-46 | Green | Choose representative examples; avoid list padding. |
| Symbolics described 10-Mbit Ethernet networking, generic file-system access, remote login, email, interactive messages, and resource sharing with 3600s, LM-2s, UNIX/VAX/VMS systems. | 3600 Bet | Symbolics 3600 p.7 | Green | Shows networked personal workstation, not isolated box. |
| The 3600 hardware included 32 data bits plus 4 tag bits, demand-paged virtual memory, 1150-by-900 display, MC68000 console, disk, Ethernet, mouse, and audio. | 3600 Bet | Symbolics 3600 pp.7-10 | Green | Good product concreteness. |
| Symbolics framed the network as combining timesharing's communication/shared-resource benefits with single-user response, memory, customization, and crash isolation. | 3600 Bet | Symbolics 3600 pp.8-9 | Green | Nice synthesis of Ch20 and Ch22. |
| Zmacs used real-time display editing, Lisp syntax awareness, mouse interaction, online documentation, customization, and EMACS command-set compatibility. | Operating System in Lisp | Symbolics 3600 pp.13-18 | Green | Shows continuity from MIT editor culture to product. |
| Gabriel and Steele state that by the late 1970s PDP-10 address-space limits and VAX performance problems made hardware look bleak for Lisp, so Lisp machines appeared to be the wave of the future. | Time-Sharing Wall / Bubble Logic | Gabriel/Steele pp.22-24 | Green | Later participant history; supports plausibility. |
| Gabriel and Steele describe Lisp machines as general-purpose computers with special support for tagging, function calling, garbage collection, stack frames, and incremental GC, not as mere appliances. | CONS to CADR | Gabriel/Steele pp.25-26 | Green | Use to counter caricature. |
| Gabriel and Steele describe CONS, CADR, dozens of CADRs, commercialization as sensible, and disagreements leading to LMI and Symbolics, with both initially making CADR clones. | Commercializing the Lab | Gabriel/Steele p.27 | Green | Keep split non-partisan unless more sources are added. |
| Gabriel and Steele state that Lisp-machine companies expanded implementations with graphics, windowing, and mouse support, but late-1980s general-purpose hardware and stock Lisp implementations competed effectively. | Bubble Logic | Gabriel/Steele pp.30-31 | Green | Core close; no business numbers. |
| Gabriel and Steele identify the 1981 ARPA Lisp Community Meeting and four diverging Lisp communities as context for Common Lisp's formation. | Portability Arrives | Gabriel/Steele pp.36-38 | Green | Bridge to portability. |
| LMI and Symbolics joined the Common Lisp effort even though Lisp-machine vendors initially viewed the action as being on the machines, not portable dialects. | Portability Arrives | Gabriel/Steele pp.36-39 | Green | Good tension. |
| Common Lisp excluded features not easily implemented across broad computers, including hardware/microcode-specific features, graphics, window systems, Flavors, locatives, and multiprocessing/multitasking. | Portability Arrives | Gabriel/Steele pp.39-43 | Green | Use as portability boundary, not language tutorial. |
| Critics argued Common Lisp had assumed a large Lisp-machine-like world and ignored some costs of microcoding/type-dispatch expectations. | Portability Arrives / Bubble Logic | Gabriel/Steele p.44 | Green | Good closing warning, but attribute as critique. |

## Citation Bar

Minimum sources before prose:

- AIM-444 pp.1-5 for the time-sharing, address-space, and personal-computer
  rationale.
- AIM-444 pp.7-8, 26-29 for all-Lisp I/O, editor, mouse/display interaction,
  LUNAR/Macsyma status, and prototype/current status.
- AIM-528 pp.1-4 for CADR terminology, microcode, stack, pointer, and virtual
  memory details.
- Lisp Machine Manual front matter and pp.1-2 for Zetalisp and the
  operating-system-like all-Lisp environment.
- Symbolics 3600 pp.2-18 and 31-46 for mature product pitch, applications, history,
  hardware, network, display, and development environment.
- Gabriel/Steele pp.22-31 and 36-44 for later historical synthesis,
  commercialization, Common Lisp, and stock-hardware pressure.

## Source Discipline Notes

- AIM-444, AIM-528, the Lisp Machine Manual, and the Symbolics 3600 Technical
  Summary are scanned PDFs. Local extraction used `pdftoppm` plus `tesseract`.
  Verify any direct quotation against page images before final prose.
- Page anchors above use document page numbers visible in the source or logical
  article pages, not raw OCR line numbers. OCR evidence was stored in a
  temporary extraction workspace and should be treated as a working aid, not a
  permanent citation.
- The Symbolics source is a vendor technical summary. It is Green for product
  specifications and company self-description, but not for independent proof of
  market success, customer count, financial performance, or failure causes.
- Gabriel and Steele is a later participant-history paper. It is Green for
  broad Lisp-history synthesis and attribution, but should be attributed where
  it interprets motives or relative importance.
- Wikipedia is acceptable for discovery, date sanity checks, and finding
  sources. It is not a prose anchor for this chapter.
- Do not upgrade Dan Weinreb or Stallman participant retrospectives until they
  are fetched, parsed, and framed as memory/conflict sources rather than neutral
  primary documentation.
