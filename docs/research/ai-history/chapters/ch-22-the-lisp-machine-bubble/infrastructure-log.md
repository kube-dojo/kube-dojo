# Infrastructure Log: Chapter 22 - The Lisp Machine Bubble

## Machines and Runtime Stack

- **PDP-10 time-sharing:** The inherited AI Lisp environment. It supported
  Maclisp, editors, debuggers, MACSYMA, LUNAR, and interactive research, but
  AIM-444 frames it as increasingly constrained by response time, swapping,
  memory competition, and address space.
- **CONS:** MIT's prototype Lisp Machine processor, designed by Tom Knight.
  AIM-444 describes 32-bit data paths, 24-bit address paths, writable
  microcode, a PDL buffer, keyboard/mouse/TV interaction, disk paging, and file
  I/O through the PDP-10.
- **CADR:** The revised processor documented in AIM-528. It was a general
  32-bit microprogrammable processor optimized for stack and pointer
  manipulation. Use the memo's distinction: CADR is the processor; the Lisp
  machine is CADR plus Lisp microcode and system software.
- **Zetalisp / Lisp Machine Lisp:** The system language and Lisp dialect
  documented in the 1981 manual. It was related to Maclisp and used for both
  user programs and system software.
- **All-Lisp operating environment:** AIM-444 and the manual support the claim
  that most system programs, I/O software, editor, compiler, and interactive
  environment were written in Lisp rather than split across a conventional OS
  and application layer.
- **Display/mouse/editor stack:** The Lisp Machine editor drew on EMACS but
  used the machine's high-speed bitmapped display, mouse, and self-documenting
  command environment. Later Symbolics Zmacs continued that lineage.
- **Symbolics LM-2:** Symbolics described the LM-2 as a CADR repackaged for
  reliability and servicing. It belongs in the commercialization bridge, not as
  the mature product scene.
- **Symbolics 3600:** Mature product expression: 36-bit single-user machine,
  32 data bits plus 4 tag bits, demand-paged virtual memory, high-resolution
  display, MC68000 console, disk, Ethernet, mouse, audio, tagged architecture,
  incremental development environment, and extensive system code.
- **Ethernet/networked personal computing:** Symbolics framed networking as the
  way to regain timesharing's communication and resource-sharing benefits while
  keeping single-user response and isolation.
- **Common Lisp:** Portability infrastructure. Use it as the route by which
  Lisp-machine ideas moved off special machines and onto broad classes of
  hardware.

## Infrastructure Lesson

The Lisp machine was infrastructure integration pushed to an extreme: language,
hardware, memory model, editor, debugger, graphics, network, and user culture
were co-designed. That is why it worked so well for its native users and why it
became risky as a market proposition. A tightly integrated stack has to keep
outperforming looser, cheaper, more portable stacks by enough to justify the
specialization.
