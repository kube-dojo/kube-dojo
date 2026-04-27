# Scene Sketches: Chapter 22 - The Lisp Machine Bubble

## Scene 1 - The Lab Machine That Keeps Swapping

Open with the physical rhythm of a time-shared PDP-10 AI lab: multiple logged-in
users, large Lisp jobs, editor buffers, debuggers, MACSYMA, LUNAR, and the
machine struggling to keep everyone interactive. The point is not nostalgia; it
is to make response time and address space feel like research constraints. The
Lisp Machine begins as relief from this environment.

Evidence: AIM-444 pp.1-5; Gabriel/Steele pp.22-24.

## Scene 2 - One Processor Per Programmer

Show the design inversion. Instead of making one central system fair to many
users, MIT gives each user a personal processor and memory, while shared disks,
file servers, and networked resources keep the lab connected. Explain why "less
efficient" at the aggregate level could be more effective for a human trying to
debug an interactive symbolic system.

Evidence: AIM-444 pp.3-5; Lisp Machine Manual pp.1-2.

## Scene 3 - CADR Is the Processor, the Lisp Machine Is the Stack

Use CADR to keep hardware concrete without drowning the chapter in bits:
writable microcode, 32-bit paths, stack and pointer manipulation, virtual
memory, and Lisp order-code interpretation. State the CADR/Lisp-machine
terminology clearly because later product names can blur it.

Evidence: AIM-528 pp.1-4.

## Scene 4 - The Operating System Is Also Lisp

Make the machine's soul visible through the editor and I/O stack. A user edits
on a bitmapped display, points with a mouse, asks for help, extends commands in
Lisp, and lives inside an environment whose system code is inspectable and
modifiable. Include the tradeoff that rich display interaction made ordinary
remote-terminal use less central.

Evidence: AIM-444 pp.7-8, 26-28; Manual front matter and pp.1-2; Symbolics 3600
pp.30-34.

## Scene 5 - From Lab Artifact to Product Company

Move carefully from MIT prototypes to companies. CONS works, CADR improves it,
dozens are built, commercialization seems sensible, and disagreements produce
LMI and Symbolics. Avoid assigning blame without stronger sources. The scene
should feel like a lab invention becoming a market bet.

Evidence: Gabriel/Steele p.27; Symbolics 3600 p.4.

## Scene 6 - The Symbolics 3600 Sales Pitch

Let the vendor source speak as a vendor source: a 36-bit single-user symbolic
workstation, tags, half-million-line system, graphics, networking, Zmacs,
debugger, Flavors, Common Lisp plans, MACSYMA, and a long application list from
AI to CAD to expert systems. The point is ambition, integration, and cost
structure, not independent proof of adoption.

Evidence: Symbolics 3600 pp.2-18 and 31-46.

## Scene 7 - Common Lisp Makes Portability Real

ARPA gathers a fragmented Lisp world. The Lisp-machine companies join the
Common Lisp effort even though their commercial energy is still in special
hardware. The standard drops or excludes features too tied to machine-specific
microcode, windows, graphics, Flavors, locatives, and multiprocessing. That
success carries a hidden message: maybe Lisp's future cannot require a Lisp
machine.

Evidence: Gabriel/Steele pp.36-44.

## Scene 8 - The Bubble Was a Timing Problem

Close without sneering. Lisp machines were technically rich and historically
important. The market risk was that they needed special hardware to remain far
enough ahead while general-purpose workstations, compilers, and portable Lisp
implementations improved. The winning idea was not the vendor box; it was the
interactive, networked, high-level development environment that later machines
absorbed.

Evidence: Gabriel/Steele pp.30-31, p.44; Symbolics 3600 pp.8-18.
