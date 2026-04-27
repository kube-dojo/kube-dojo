# Infrastructure Log: Chapter 50

## Technical Metrics & Constraints
- **Parallelization:**
  - Architectural Shift: RNNs are $O(n)$ sequential. Transformers process sequences simultaneously, allowing O(1) sequential operations, which maxes out GPU/TPU utilization.
