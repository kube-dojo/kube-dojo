# Infrastructure Log: Chapter 1

## Technical Metrics & Constraints

### Analog Constraints (pre-1955)
- **W. Grey Walter's Tortoises (1948-1953):**
  - Compute: 2 vacuum tubes per tortoise.
  - Sensors: 1 photo-electric cell, 1 bump sensor.
  - Constraint: Behavior was hard-wired; no memory or symbolic representation possible.

### Digital Capabilities (The IBM Shift)
- **IBM 701 (1952):**
  - Memory: Williams tubes (electrostatic), 2048 words of 36 bits.
  - Speed: ~16,000 additions per second.
- **IBM 704 (1954/1956) - *The Target Infrastructure*:**
  - Memory: Magnetic core memory (crucial for reliability), up to 32,768 words.
  - Speed: ~40,000 instructions per second; hardware floating-point math (up to 12,000 floating-point additions per second).
  - Significance: It was the only machine powerful enough with enough reliable memory to support early list processing and symbolic manipulation, leading McCarthy to develop LISP on it.