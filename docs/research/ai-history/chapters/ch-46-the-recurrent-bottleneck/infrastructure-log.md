# Infrastructure Log: Chapter 46

## Technical Metrics & Constraints
- **Sequential Compute:**
  - Constraint: To calculate the hidden state for word *t*, the GPU must first finish calculating the hidden state for word *t-1*. This O(N) sequential dependency leaves thousands of GPU cores idle.
