# Infrastructure Log: Chapter 1

## Technical Metrics & Constraints

### The Pre-Silicon Era (Theoretical Infrastructure)
- **The Turing Machine (1936):**
  - Architecture: A theoretical infinite paper tape divided into discrete squares, a read/write head, and a finite table of instructions (state transitions).
  - Constraint: It existed entirely on paper and in the mind. It possessed infinite memory (the tape) but operated at the speed of human thought. The infrastructural challenge was how to build one in the real world.

### The Physical Bridge
- **Electrical Relay Circuits (1930s):**
  - Components: Electro-mechanical switches (relays) used primarily in the telephone routing networks of the Bell System and in early analog calculating machines like the MIT Differential Analyzer.
  - Constraint: Before Shannon (1937), these circuits were designed using intuition, trial-and-error, and "plumber's engineering." They were messy and inefficient to scale.
  - Breakthrough: Shannon proved that the state of a relay (open/closed) was mathematically identical to Boolean logic (1/0, True/False). This meant logic could now be designed and optimized *algebraically* before being built physically, allowing computation to scale out of the theoretical realm and into the industrial realm.
