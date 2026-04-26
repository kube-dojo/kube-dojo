# Chapter 4: Rules, Experts, and the Knowledge Bottleneck

## Thesis
The "Expert Systems" boom of the 1980s was an attempt to scale symbolic AI through specialized, incredibly expensive infrastructure—LISP machines. The era ultimately collapsed not because the logic failed, but because of the "knowledge acquisition bottleneck": extracting human expertise and hand-coding it into rules proved completely unscalable without automated data pipelines.

## Scope
- IN SCOPE: The rise of expert systems (MYCIN, XCON/R1), the creation of specialized hardware (LISP machines like Symbolics and LMI), the Japanese Fifth Generation Computer Systems project, and the eventual collapse (the second AI Winter) due to maintenance complexity.
- OUT OF SCOPE: Statistical machine learning and HMMs (belongs to Chapter 5).

## Scenes Outline
1. **The Rule-Based Fortune:** DEC implements XCON (R1) to configure VAX computer orders, saving millions of dollars. The realization that specialized, narrow domains can be encoded into IF-THEN rules. The AI industry pivots from general intelligence to enterprise software.
2. **The LISP Machine Bubble:** Standard microprocessors are too slow to run massive LISP programs efficiently. Companies like Symbolics and LMI spin out of MIT to build custom LISP machines—expensive, specialized workstations designed entirely around symbolic processing infrastructure.
3. **The Knowledge Bottleneck:** As expert systems scale from 1,000 rules to 10,000 rules, they become impossible to maintain. The "knowledge acquisition bottleneck" becomes apparent: human experts cannot articulate every edge case, and hand-coding rules is infinitely slower than the emerging statistical methods. The LISP machine market collapses as standard PCs follow Moore's Law, triggering the second AI Winter.