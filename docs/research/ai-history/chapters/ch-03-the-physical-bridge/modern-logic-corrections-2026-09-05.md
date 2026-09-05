# Chapter 3 modern logic: bounded research correction

**Date:** 2026-09-05
**Chapter source binding:** `src/content/docs/ai-history/ch-03-the-physical-bridge.md`

This is an unpublished evidence record for a separate research review. It
does not edit the chapter, certify the sources, or claim an executed synthesis
artifact.

## Claim boundary

The current modern-logic paragraph presents every CPU, GPU, MCU, and FPGA as
a series-parallel two-state network and says synthesis produces minimal
gate-level networks. The evidence below supports a narrower, tool-specific
example of RTL lowering, functional-preservation goals, and target mapping.
It does not establish universal chip-class coverage, physical-layer identity,
or global circuit minimality.

## Source bindings

### Current official tool manual

YosysHQ, *Yosys 0.68-dev manual*, current official tool documentation:
[PDF](https://yosyshq.readthedocs.io/_/downloads/yosys/en/latest/pdf/).
Retrieved 2026-09-05 UTC; 3,434,314 bytes; SHA-256
`c36bf12d15b365640ae70562b14b4026f6a769255b3a6a1facc1eec1eaef3667`;
`pdfinfo` reports 691 physical PDF pages. The URL is rolling; this hash pins
the reviewed bytes.

Locators distinguish printed manual pages from physical PDF pages (the web
extractor labels those pages from zero): printed p.44 = physical PDF p.50
(web P49), and printed p.50 = physical PDF p.56 (web P55). Printed p.53 =
physical PDF p.59 (web P58) documents memory-library mapping, functional
equivalence, and fallback to DFFs/address decoders. Printed pp.71-72 =
physical PDF pp.77-78 (web P76-77) document target-cell mapping, coarse-grain
resources, register mapping, and combinational mapping.

### Historical primary conference paper

Wolf and Glaser, “Yosys – A Free Verilog Synthesis Suite,” *Austrochip 2013*:
[PDF](https://yosyshq.net/yosys/files/yosys-austrochip2013.pdf).
This is a historical primary paper describing the 2013 release, not current
tool documentation. Retrieved 2026-09-05 UTC; 150,619 bytes; SHA-256
`9798c6623cf9c9da22896e9ee6a6b660d4232e0d4e1c63b01d9007e9c5935f9f`;
`pdfinfo` reports 6 physical PDF pages. PDF p.1 gives the HDL-to-circuit
context; pp.2-3 describe logically equivalent-netlist goals and ASIC/FPGA
mapping flows; p.2 records the paper's 2013 timing/STA/constraints scope; p.5
reports equivalence checks for small modules and real designs including CPUs;
p.6 records feature and future-work boundaries.

## Proposed bounded wording

> The habit of transforming a symbolic description also appears in modern logic synthesis. Yosys documentation describes turning a Verilog design’s behavior, including clocked state and memory accesses, into an internal network, transforming that network while aiming to preserve its function, and mapping it to cells or memory resources for a chosen target library. The resulting network depends on target technology and synthesis choices.

This wording records a documented flow and functional goal, not an unexecuted
equivalence result. It provides no timing, power, area, placement, routing, or
fabrication result. Keep Shannon’s historical relay and series-parallel
discussion separate from this modern tool example.
