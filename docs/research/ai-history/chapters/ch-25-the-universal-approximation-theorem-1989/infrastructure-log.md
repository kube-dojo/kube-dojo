# Infrastructure Log: Chapter 25
# Infrastructure Log: Chapter 25 - The Universal Approximation Theorem (1989)

## Hardware and Compute

- The theorem itself is mathematical infrastructure: it changes what researchers believe networks can represent, but it does not supply compute, data, or a training recipe.
- Narrative should contrast low-cost proof with high-cost realization: approximating a function may require many hidden units, many parameters, and enough computation to search weight space.
- Do not attach specific machines to Cybenko/Hornik/Funahashi unless primary sources identify them. This chapter likely needs less lab-machine detail than Ch24 or Ch27.

## Data and Benchmarks

- Universal approximation is not benchmark performance. Keep the proof domain separate from practical datasets.
- If examples are needed, use simple continuous-function approximation as pedagogy, not invented lab scenes.
- Link forward to Ch27: convolutional networks succeed partly because architecture restricts the search space; universal approximation alone is too unconstrained to explain practical vision systems.

## Mathematical Infrastructure

- Key infrastructure is the move from "single-layer perceptrons have sharp limits" to "nonlinear hidden-layer networks are rich function classes."
- The theorem turns hidden units into a representational resource, but leaves open how many are needed and how to fit them.
- The chapter should emphasize density/approximation rather than exact symbolic representation.

## Economic and Institutional Context

- Late-1980s neural-network enthusiasm needed legitimacy after prior disappointment. A formal theorem helped researchers argue that multilayer networks were not mathematically dead ends.
- Avoid treating theorem publication as direct commercial infrastructure. Its role is intellectual confidence, not immediate deployment.

## Claims Not Yet Safe

- "The theorem caused industry adoption" is Red without stronger evidence.
- "The theorem showed deep networks were necessary" is false/misleading; the classic result often concerns shallow networks with enough units.
- "The theorem solved generalization" is false.
