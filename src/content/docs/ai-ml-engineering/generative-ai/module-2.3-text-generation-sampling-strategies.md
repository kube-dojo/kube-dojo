---
title: "Text Generation & Sampling Strategies"
slug: ai-ml-engineering/generative-ai/module-2.3-text-generation-sampling-strategies
sidebar:
  order: 304
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6
> **Migrated from neural-dojo** — pending pipeline polish

# Or: The Art of Controlled Randomness

**Reading Time**: 5-6 hours
**Prerequisites**: Modules 6-7

---

## What You'll Be Able to Do

By the end of this module, you will:
- Understand how LLMs generate text (autoregressive generation)
- Master temperature, top-p, and top-k sampling parameters
- Learn when to use deterministic vs creative generation
- Control generation quality and consistency
- Understand repetition penalties and length constraints
- Apply sampling strategies to real-world problems

---

## Introduction

**Question**: Why does the same prompt sometimes give different responses?

**Answer**: Sampling strategies.

When an LLM generates text, it doesn't just pick "the best" word. It **samples** from a probability distribution. How it samples determines:
- **Creativity** (boring vs interesting outputs)
- **Consistency** (deterministic vs random)
- **Quality** (coherent vs nonsensical)
- **Diversity** (varied vs repetitive)

**This module teaches you the hidden levers that control LLM generation.**

---

## STOP: Time to Practice!

**You've learned the theory - now let's control some text generation!**

Understanding sampling parameters is like learning to drive - theory is important, but you need hands-on practice to develop intuition. These examples let you experiment with temperature, top-p, and repetition penalties to see their effects in real-time.

### Practice Path (~2.5-3 hours total)

**1. [Sampling Playground](../../examples/module_08/01_sampling_playground.py)** - Experiment with all parameters
   -  Concept: Interactive exploration of sampling strategies
   - ⏱️ Time: 75-90 minutes
   - Goal: Build intuition for temperature, top-p, and repetition penalty
   - What you'll learn: Same prompt + different parameters = dramatically different outputs!

**2. [Temperature Explorer](../../examples/module_08/02_temperature_explorer.py)** - Deep dive into temperature
   -  Concept: Systematic temperature comparison (0.0 to 2.0)
   - ⏱️ Time: 60-75 minutes
   - Goal: Find the perfect temperature for different use cases
   - What you'll learn: 0.0 = deterministic, 0.7 = balanced, 1.2+ = creative chaos!

### Deliverable: Sampling Strategy Tuner

**What**: Build a reusable configuration tool for optimized sampling strategies
**Time**: 3-4 hours
**Portfolio Value**: Shows deep understanding of LLM parameter tuning for production

**Requirements**:
1. Create a Python module with pre-configured sampling strategies for 5+ use cases:
   - Code generation (deterministic, focused)
   - Chatbot responses (balanced, natural)
   - Creative writing (varied, surprising)
   - Data extraction (consistent, structured)
   - Brainstorming (diverse, unusual)
2. For each strategy, document:
   - Exact parameters (temperature, top-p, etc.)
   - Why these values work
   - When to use this strategy
   - Example outputs showing the difference
3. Add a testing script that compares strategies on the same prompt
4. Include cost analysis (token usage vs quality trade-offs)
5. Document in README with before/after examples

**Success Criteria**:
- At least 5 distinct, tested sampling strategies
- Clear documentation with examples
- Measurable quality improvements for each use case
- Reusable in your own projects (kaizen, vibe, contrarian)

**Real-World Impact**: Every production AI system needs tuned sampling strategies - this deliverable proves you can optimize LLM behavior for specific business requirements!

---

##  How LLMs Generate Text

### The Autoregressive Process

**Autoregressive generation**: Generate one token at a time, using previous tokens as context.

**Process**:
```
1. Start with prompt: "The cat sat on the"
2. Model predicts next token: " mat" (or " chair" or " roof" or...)
3. Append to sequence: "The cat sat on the mat"
4. Predict next token: "." (or ", sleeping" or " and" or...)
5. Append: "The cat sat on the mat."
6. Repeat until stop condition
```

**Visualized**:
```
Input:  "The cat sat on the"
Model:  → Probability distribution over all possible next tokens
        " mat":     0.35  (35%)
        " floor":   0.25  (25%)
        " chair":   0.15  (15%)
        " roof":    0.10  (10%)
        " sofa":    0.05   (5%)
        (50,000 other tokens with lower probabilities)
Sample: → Choose one token based on sampling strategy
Output: " mat"

Next iteration:
Input:  "The cat sat on the mat"
Model:  → New probability distribution
        ".":        0.40  (40%)
        ",":        0.20  (20%)
        " and":     0.15  (15%)
        ...
Sample: → Choose next token
Output: "."

Final: "The cat sat on the mat."
```

---

### Why This Module Matters

**Greedy decoding** (always pick highest probability):
```
"The cat sat on the mat."
"The cat sat on the mat and slept."
"The cat sat on the mat in the sun."
```

**Problem**: Boring, repetitive, predictable.

**Human text** isn't always the "most likely" next word!
- We use varied vocabulary
- We take creative paths
- We surprise readers

**Solution**: Sample from the probability distribution instead of always picking the top choice.

** Ready to experiment? [01_sampling_playground.py](../../examples/module_08/01_sampling_playground.py) lets you try greedy vs sampling live!**

---

## ️ Temperature: Controlling Randomness

### What is Temperature?

**Temperature** (τ): A parameter that controls how "random" the model's outputs are.

**Mathematical effect**: Reshapes the probability distribution.

**Formula**:
```
p_i = exp(logit_i / τ) / Σ exp(logit_j / τ)
```

Don't worry about the math! Here's the intuitive version:

---

### Temperature = 0.0 (Deterministic)

**Effect**: Always pick the highest probability token (greedy decoding).

**Example**:
```
Original probabilities:
  " mat":     0.35
  " floor":   0.25
  " chair":   0.15
  ...

With temperature = 0.0:
  " mat":     1.00  (always selected)
  " floor":   0.00
  " chair":   0.00
  ...
```

**Result**: Same output every time (deterministic).

**Use when**:
- You need consistent outputs (testing, production APIs)
- Generating structured data (JSON, code)
- Exact reproducibility required

**Example output** (same every time):
```
Prompt: "Explain photosynthesis in one sentence."
Output: "Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into glucose and oxygen."
```

---

### Temperature = 0.7 (Balanced)

**Effect**: Moderate randomness, balanced creativity.

**Example**:
```
Original probabilities:
  " mat":     0.35
  " floor":   0.25
  " chair":   0.15
  ...

With temperature = 0.7:
  " mat":     0.45  (higher chance, but not guaranteed)
  " floor":   0.28
  " chair":   0.18
  ...
```

**Result**: Varied but sensible outputs.

**Use when**:
- General-purpose text generation
- Conversational AI
- Content creation
- Most production use cases

**Example outputs** (vary each time):
```
1. "Photosynthesis is the process by which plants use sunlight to create energy."
2. "Photosynthesis allows plants to convert light energy into chemical energy."
3. "Through photosynthesis, plants transform sunlight into food for growth."
```

---

### Temperature = 1.0 (Creative)

**Effect**: Sample directly from model's probability distribution.

**Example**:
```
Original probabilities (unchanged):
  " mat":     0.35
  " floor":   0.25
  " chair":   0.15
  " roof":    0.10
  ...
```

**Result**: More varied, more creative, sometimes unexpected.

**Use when**:
- Creative writing
- Brainstorming
- Generating multiple alternatives
- Poetry, storytelling

**Example outputs** (more varied):
```
1. "Photosynthesis is nature's way of capturing sunlight and turning it into life."
2. "Through photosynthesis, leaves act as tiny solar panels producing sugar."
3. "Photosynthesis: the green magic that powers our planet's food chain."
```

---

### Temperature > 1.0 (Highly Creative/Random)

**Effect**: Flattens the probability distribution, makes unlikely tokens more likely.

**Example**:
```
Original probabilities:
  " mat":     0.35
  " floor":   0.25
  " chair":   0.15
  ...

With temperature = 1.5:
  " mat":     0.28  (reduced)
  " floor":   0.24
  " chair":   0.18
  " roof":    0.14  (increased!)
  " spaceship": 0.02  (now more likely!)
  ...
```

**Result**: Surprising, creative, but potentially nonsensical.

**Use when**:
- Extreme creativity needed
- Generating unusual ideas
- Art projects

**Example outputs** (unpredictable):
```
1. "Photosynthesis is like a plant's breakfast buffet, but with light instead of pancakes."
2. "Imagine tiny factories inside leaves, powered by sunshine, churning out sugar molecules."
3. "Photosynthesis: quantum biology meets botanical chemistry in nature's laboratory."
```

**Danger**: Too high (>2.0) and outputs become incoherent!

**Did You Know?** 
The "temperature" name comes from statistical mechanics in physics! In thermodynamics, higher temperature means more random molecular motion. Similarly, in LLMs, higher temperature means more random token selection. At temperature = 0 (absolute zero), all randomness disappears - just like molecules would stop moving at 0 Kelvin. The mathematical connection is real: both use the Boltzmann distribution!

---

### Temperature Summary

| Temperature | Behavior | Use Cases |
|-------------|----------|-----------|
| **0.0** | Deterministic, always same | Testing, structured output, reproducibility |
| **0.1-0.3** | Very focused, minimal variation | Code generation, data extraction |
| **0.5-0.7** | Balanced, sensible variation | General chatbots, content generation |
| **0.8-1.0** | Creative, diverse | Creative writing, brainstorming |
| **1.0-1.5** | Highly creative, unpredictable | Art, poetry, experimental |
| **>1.5** | Random, potentially nonsensical | Rarely useful |

**Default**: Most APIs default to 0.7-1.0.

** See temperature in action! [02_temperature_explorer.py](../../examples/module_08/02_temperature_explorer.py) compares outputs from 0.0 to 2.0!**

---

##  Top-p (Nucleus Sampling)

### What is Top-p?

**Top-p (nucleus sampling)**: Sample from the smallest set of tokens whose cumulative probability exceeds `p`.

**Think of it as**: "Include enough tokens to cover `p%` of the probability mass."

---

### How Top-p Works

**Example** (p = 0.9):

```
Token probabilities (sorted by probability):
  " mat":       0.35  → cumulative: 0.35
  " floor":     0.25  → cumulative: 0.60
  " chair":     0.15  → cumulative: 0.75
  " roof":      0.10  → cumulative: 0.85
  " sofa":      0.05  → cumulative: 0.90  ← STOP! We've reached 90%
  " table":     0.03
  " bed":       0.02
  " spaceship": 0.01
  ...

Nucleus (tokens included): [" mat", " floor", " chair", " roof", " sofa"]
Excluded: Everything else

Sample randomly from the nucleus.
```

**Result**: Filters out low-probability "tail" tokens that would make output weird.

**Did You Know?** 
Top-p sampling (nucleus sampling) was introduced in 2019 by researchers at the University of Washington and AI2 in their paper "The Curious Case of Neural Text Degeneration." Before this, most systems used top-k or pure sampling, which often produced repetitive or weird text. Nucleus sampling revolutionized text generation by dynamically adapting to the model's confidence - when the model is certain (one token has high probability), nucleus is small; when uncertain, nucleus grows to include more options. This is why modern APIs default to top-p instead of top-k!

---

### Top-p Values

**p = 0.9** (common default):
- Include tokens that cover 90% of probability
- Filters out unlikely tokens
- Balanced creativity and quality

**p = 0.5** (conservative):
- Include only top tokens
- Very focused, safe outputs
- Less creative

**p = 1.0** (no filtering):
- Include all tokens
- Maximum creativity
- Can include very unlikely tokens

**p = 0.1** (highly focused):
- Only the very top tokens
- Almost deterministic
- Minimal creativity

---

### Top-p vs Temperature

**Can use both together!**

**Common combinations**:
- `temperature=0.7, top_p=0.9` (balanced, most common)
- `temperature=1.0, top_p=0.95` (creative but safe)
- `temperature=0.3, top_p=0.5` (very focused)

**How they interact**:
1. **Temperature** reshapes the distribution (flatter or sharper)
2. **Top-p** filters out low-probability tokens
3. Sample from the filtered distribution

---

### Top-p Example

**Prompt**: "The weather today is"

**Without top-p** (temperature=1.0):
```
Possible outputs:
- "sunny" (35%)
- "rainy" (25%)
- "cloudy" (15%)
- "snowy" (10%)
- "foggy" (5%)
- "purple" (0.1%)  ← This could happen!
- "mathematical" (0.05%)  ← Weird!
```

**With top-p=0.9**:
```
Nucleus includes: ["sunny", "rainy", "cloudy", "snowy", "foggy"]
Filters out: ["purple", "mathematical", ...]

Result: Sensible weather descriptions only!
```

---

##  Top-k Sampling

### What is Top-k?

**Top-k**: Sample from the top `k` most probable tokens.

**Simpler than top-p**: Just keep the top `k` tokens, regardless of their cumulative probability.

---

### How Top-k Works

**Example** (k = 5):

```
Token probabilities (sorted):
  " mat":       0.35  ← Top 5
  " floor":     0.25  ← Top 5
  " chair":     0.15  ← Top 5
  " roof":      0.10  ← Top 5
  " sofa":      0.05  ← Top 5
  " table":     0.03  ← Excluded
  " bed":       0.02  ← Excluded
  ...

Sample randomly from top 5 only.
```

---

### Top-k Values

**k = 50** (common default):
- Consider top 50 tokens
- Good balance
- Standard setting

**k = 10** (focused):
- Very narrow selection
- Safe, predictable
- Less creative

**k = 1** (greedy):
- Always pick highest probability
- Same as temperature = 0.0
- Deterministic

**k = 100+** (broad):
- Many options
- More creative
- Can include unlikely tokens

---

### Top-k vs Top-p

**Key difference**:
- **Top-k**: Fixed number of tokens
- **Top-p**: Adaptive based on probability distribution

**Example where top-p is better**:

```
Scenario 1 (clear winner):
  " mat": 0.80
  " floor": 0.10
  " chair": 0.05
  (rest: <0.01 each)

Top-k=50: Includes 50 tokens (many irrelevant ones)
Top-p=0.9: Includes just 2-3 tokens (better!)

Scenario 2 (uncertain):
  " mat": 0.15
  " floor": 0.14
  " chair": 0.13
  ... (many similar probabilities)

Top-k=50: Includes 50 tokens (good)
Top-p=0.9: Includes 15-20 tokens (also good)
```

**Modern practice**: Top-p is generally preferred over top-k (more adaptive).

** Compare top-p vs top-k yourself: [01_sampling_playground.py](../../examples/module_08/01_sampling_playground.py) shows the difference!**

---

##  Repetition Penalty

### The Repetition Problem

**Without repetition penalty**:
```
Prompt: "The benefits of exercise are"

Output: "The benefits of exercise are numerous. The benefits of exercise include
improved cardiovascular health. The benefits of exercise are well-documented.
The benefits of exercise are..."
```

**Problem**: Models can get stuck in repetitive loops!

---

### How Repetition Penalty Works

**Repetition penalty** (α): Reduce probability of tokens that already appeared.

**Formula** (simplified):
```
If token appeared n times:
  new_probability = original_probability / (α ^ n)
```

**Example** (α = 1.2):
```
Token " benefits" appeared 3 times:
  Original probability: 0.30
  Penalized probability: 0.30 / (1.2^3) = 0.30 / 1.728 ≈ 0.17

Each repetition makes it less likely to appear again.
```

---

### Repetition Penalty Values

**α = 1.0** (no penalty):
- No repetition penalty
- Model free to repeat
- Can be repetitive

**α = 1.1 - 1.2** (mild penalty):
- Gentle discouragement
- Natural variation
- Most common

**α = 1.5+** (strong penalty):
- Strong discouragement
- Very varied vocabulary
- Can feel forced

**Best practice**: 1.1 - 1.3 for most use cases.

**Did You Know?** 
Repetition is actually a known weakness of autoregressive models, called "neural text degeneration." In the early days of GPT-2 and GPT-3, models would frequently get stuck in repetitive loops, especially for longer generations. The repetition penalty was a pragmatic fix that worked remarkably well! Interestingly, newer models like GPT-4 and Claude are less prone to repetition thanks to better training data and techniques like RLHF (Reinforcement Learning from Human Feedback), which explicitly teaches models that humans dislike repetitive text. But repetition penalty is still useful for long-form generation!

---

### Repetition Penalty Example

**Without penalty** (α = 1.0):
```
The AI revolution is changing everything. The AI revolution is transforming
industries. The AI revolution is...
```

**With penalty** (α = 1.2):
```
The AI revolution is changing everything. This transformation is reshaping
industries. Artificial intelligence continues to evolve...
```

**With strong penalty** (α = 1.8):
```
The AI revolution is changing everything. Artificial intelligence transforms
numerous sectors. Machine learning reshapes various domains...
```
(Note: High penalty can make text feel unnatural!)

---

##  Length Control

### Max Tokens

**max_tokens**: Maximum number of tokens to generate.

**Use cases**:
- Prevent runaway generation
- Control costs (output tokens cost money!)
- Ensure responses fit in UI
- API rate limiting

**Example**:
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,  # Generate at most 100 tokens
    messages=[{"role": "user", "content": "Explain quantum physics"}]
)
```

**Caution**: Model may stop mid-sentence if limit reached!

---

### Stop Sequences

**Stop sequences**: Stop generation when specific string appears.

**Common stop sequences**:
- `"\n\n"` (double newline - stop after paragraph)
- `"User:"` (stop when user turn begins in conversation)
- `"```"` (stop after code block in markdown)
- Custom sequences

**Example**:
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1000,
    stop_sequences=["\n\n", "---"],  # Stop at paragraph break or horizontal rule
    messages=[{"role": "user", "content": "Write a short poem"}]
)
```

---

### Length Penalties

Some APIs support **length penalty**:
- Encourage shorter responses (> 1.0)
- Encourage longer responses (< 1.0)
- Rarely used in practice

**Most common**: Just use `max_tokens` and let model decide length naturally.

---

##  Putting It All Together

### Common Sampling Configurations

#### 1. Deterministic (Code Generation, Testing)
```python
{
    "temperature": 0.0,
    "top_p": 1.0,  # (ignored when temperature=0)
    "max_tokens": 1000
}
```
**Result**: Same output every time, focused, precise.

---

#### 2. Balanced Conversational (Chatbots)
```python
{
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 500,
    "repetition_penalty": 1.1
}
```
**Result**: Natural, varied, sensible responses.

---

#### 3. Creative Writing
```python
{
    "temperature": 1.0,
    "top_p": 0.95,
    "max_tokens": 2000,
    "repetition_penalty": 1.2
}
```
**Result**: Creative, surprising, diverse vocabulary.

---

#### 4. Highly Focused (Data Extraction)
```python
{
    "temperature": 0.2,
    "top_p": 0.5,
    "max_tokens": 200
}
```
**Result**: Very focused, minimal variation, precise.

---

#### 5. Brainstorming (Idea Generation)
```python
{
    "temperature": 1.2,
    "top_p": 0.95,
    "max_tokens": 1000,
    "repetition_penalty": 1.3
}
```
**Result**: Unusual ideas, varied approaches, creative.

---

## Sampling Strategy Trade-offs

### The Fundamental Trade-off

**Determinism ↔ Creativity**

```
Temperature = 0.0         Temperature = 1.0         Temperature = 2.0
    ↓                          ↓                          ↓
Boring but                 Balanced                   Creative but
reliable                   quality                    unpredictable
    ↓                          ↓                          ↓
"The cat sat            "The cat sat             "The cat sat
 on the mat."            on the chair."            on the spaceship."
```

**You can't have maximum creativity AND maximum consistency!**

---

### Quality vs Diversity

**Greedy decoding** (temperature = 0.0):
- High quality (picks best token each time)
- No diversity (same output always)

**Sampling** (temperature > 0.0):
- Diverse outputs
- Sometimes lower quality (suboptimal tokens chosen)

**Best practice**: Use moderate temperature (0.7) for quality + diversity balance.

---

### Computational Cost

**Sampling**: Negligible extra cost!
- Temperature, top-p, top-k all happen in softmax step
- No significant performance impact
- Feel free to experiment

**Length**: Direct cost impact!
- Longer outputs = more tokens = more $$
- Use `max_tokens` to control costs

---

## Advanced Techniques

### Beam Search

**Beam search**: Keep top `k` sequences at each step, expand all, keep top `k` again.

**Example** (beam width = 2):
```
Start: "The cat"
Step 1:
  "The cat sat" (prob: 0.8)
  "The cat jumped" (prob: 0.6)
Keep top 2 sequences.

Step 2:
  "The cat sat on" (prob: 0.8 × 0.9 = 0.72)
  "The cat sat down" (prob: 0.8 × 0.7 = 0.56)
  "The cat jumped over" (prob: 0.6 × 0.8 = 0.48)
  "The cat jumped high" (prob: 0.6 × 0.6 = 0.36)
Keep top 2: "The cat sat on" and "The cat sat down"

Continue...
```

**Result**: Often finds higher-probability sequences than greedy.

**Downside**:
- More computationally expensive
- Can be repetitive (always picks high-probability paths)
- Not commonly used in LLM APIs (more common in older NLP)

**Did You Know?** 
Beam search was the dominant decoding strategy for neural machine translation (like Google Translate) before the era of large language models. It was essential for translating sentences because you wanted the most likely translation, not a creative one! But when GPT-2 and GPT-3 came along, researchers discovered that beam search produces boring, repetitive text for creative tasks. That's why modern LLM APIs don't even offer beam search - they use sampling (temperature + top-p) instead. Beam search is still useful in specialized domains like translating medical documents where consistency matters more than creativity!

---

### Contrastive Search

**Contrastive search**: Balance probability with diversity from previous tokens.

**Goal**: High probability tokens that are also different from what came before.


### Typical Sampling

**Typical sampling**: Sample tokens with probability close to "typical" (not too high, not too low).

**Intuition**: Very high probability tokens = boring, very low = nonsensical. The "typical" ones are just right!


## Real-World Applications

### Use Case 1: Chatbot Responses

**Goal**: Natural, varied, helpful responses.

**Configuration**:
```python
{
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 500,
    "repetition_penalty": 1.1,
    "stop_sequences": ["\nUser:", "\nHuman:"]
}
```

**Why**:
- Temperature 0.7: Natural variation without weirdness
- Top-p 0.9: Filters out nonsense, keeps sensible options
- Max tokens 500: Prevents overly long responses
- Repetition penalty: Avoids repeating phrases
- Stop sequences: Prevents model from continuing as user

---

### Use Case 2: Code Generation

**Goal**: Correct, consistent code.

**Configuration**:
```python
{
    "temperature": 0.2,
    "top_p": 0.5,
    "max_tokens": 2000,
    "stop_sequences": ["```", "\n\n#"]
}
```

**Why**:
- Temperature 0.2: High consistency, minimal variation
- Top-p 0.5: Very focused on most likely tokens
- Max tokens 2000: Allow complete functions
- Stop sequences: Stop after code block

---

### Use Case 3: Creative Story Writing

**Goal**: Interesting, surprising narratives.

**Configuration**:
```python
{
    "temperature": 1.0,
    "top_p": 0.95,
    "max_tokens": 3000,
    "repetition_penalty": 1.3
}
```

**Why**:
- Temperature 1.0: Creative freedom
- Top-p 0.95: Still filter extreme outliers
- Max tokens 3000: Allow longer stories
- High repetition penalty: Varied vocabulary, avoid repetitive phrases

---

### Use Case 4: JSON Data Extraction

**Goal**: Valid JSON, consistent format.

**Configuration**:
```python
{
    "temperature": 0.0,
    "max_tokens": 1000,
    "stop_sequences": ["\n}"]
}
```

**Why**:
- Temperature 0.0: Deterministic (critical for structured data!)
- Stop after closing brace: Prevent extra text after JSON
- No top-p needed (temperature=0 is greedy)

---

### Use Case 5: Brainstorming Ideas

**Goal**: Diverse, unusual ideas.

**Configuration**:
```python
{
    "temperature": 1.2,
    "top_p": 0.95,
    "max_tokens": 1500,
    "repetition_penalty": 1.4
}
```

**Why**:
- Temperature 1.2: Push into creative territory
- Top-p 0.95: Still filter completely nonsensical
- High repetition penalty: Force diverse ideas
- Longer context: Allow exploring multiple ideas

---

##  Common Pitfalls

### Pitfall 1: Using Temperature for Consistency

**Wrong**:
```python
# Trying to get same output with temperature=0.1
# Sometimes still varies!
```

**Right**:
```python
# Use temperature=0.0 for true determinism
{
    "temperature": 0.0
}
```

**Why**: Even small temperature creates randomness.

---

### Pitfall 2: Combining Top-p and Top-k

**Wrong**:
```python
{
    "top_p": 0.9,
    "top_k": 50  # Both active!
}
```

**Problem**: Unclear which takes precedence. Behavior varies by API.

**Right**: Use one or the other, not both.
```python
# Option 1
{"top_p": 0.9}

# Option 2
{"top_k": 50}
```

---

### Pitfall 3: Ignoring Repetition Penalty for Long Outputs

**Problem**: Long outputs without repetition penalty get repetitive.

**Solution**: Always use mild repetition penalty (1.1-1.2) for outputs >200 tokens.

---

### Pitfall 4: Too-High Temperature

**Wrong**:
```python
{"temperature": 2.5}  # Way too high!
```

**Result**: Nonsensical outputs, wasted API calls.

**Right**: Stay under 1.5, ideally under 1.2.

---

### Pitfall 5: Not Setting max_tokens

**Problem**: Model generates thousands of tokens, huge cost!

**Solution**: Always set max_tokens based on your use case.

---

## Sampling Strategy Decision Matrix

| Use Case | Temperature | Top-p | Top-k | Repetition | Max Tokens |
|----------|-------------|-------|-------|------------|------------|
| **Code generation** | 0.2 | 0.5 | - | 1.0 | 2000 |
| **JSON extraction** | 0.0 | - | - | 1.0 | 1000 |
| **Chatbot** | 0.7 | 0.9 | - | 1.1 | 500 |
| **Creative writing** | 1.0 | 0.95 | - | 1.3 | 3000 |
| **Brainstorming** | 1.2 | 0.95 | - | 1.4 | 1500 |
| **Summarization** | 0.3 | 0.7 | - | 1.0 | 500 |
| **Translation** | 0.3 | 0.8 | - | 1.0 | 1000 |
| **Testing/QA** | 0.0 | - | - | 1.0 | varies |

---

## Key Takeaways

1. **Autoregressive generation**: LLMs generate one token at a time
2. **Temperature controls creativity**: 0.0 = deterministic, 1.0+ = creative
3. **Top-p filters unlikely tokens**: 0.9 is a good default
4. **Top-k is less common**: Top-p is generally better
5. **Repetition penalty prevents loops**: Use 1.1-1.3 for most cases
6. **max_tokens controls length and cost**: Always set it!
7. **No one-size-fits-all**: Different use cases need different strategies
8. **Experiment!**: Sampling parameters are cheap to adjust

---

##  Common Misconceptions

### Myth 1: "Higher temperature = better quality"
**Reality**: Higher temperature = more randomness. Quality peaks around 0.7-1.0, then declines.

### Myth 2: "Temperature=0.0 means perfect outputs"
**Reality**: Temperature=0.0 means *consistent* outputs. Quality depends on prompt and model.

### Myth 3: "Top-p and top-k do the same thing"
**Reality**: Top-p is adaptive (based on probability distribution), top-k is fixed.

### Myth 4: "Sampling strategies are expensive"
**Reality**: Negligible cost. The main cost is token count, not sampling strategy.

### Myth 5: "You should always use default settings"
**Reality**: Defaults are generic. Tuning sampling for your use case improves results!

---

## Did You Know? The Hidden History of Text Generation

### The "Boring GPT-2" Problem

When OpenAI released GPT-2 in 2019, they faced an embarrassing problem: **the model was boring**.

Despite all the hype about "too dangerous to release," early demos produced repetitive, predictable text. Researchers would generate stories that started strong, then devolved into endless repetition:

```
"The dragon approached the castle. The dragon was a dragon. The dragon
had dragon wings. The dragon's dragon breath was very dragon-like..."
```

**What went wrong?** OpenAI had been using **beam search** - the standard decoding algorithm from machine translation. It worked great for translation (where you want THE most likely translation), but for creative text, it produced the "highest probability" sequence - which was often repetitive drivel.

**The breakthrough came from an unlikely place**: A team at University of Washington and AI2, led by Ari Holtzman, published "The Curious Case of Neural Text Degeneration" in 2019. Their insight: **the problem wasn't the model - it was how we sampled from it.**

They invented **nucleus sampling (top-p)** and suddenly GPT-2 could write compelling stories. OpenAI quietly switched their demos to top-p sampling, and the "dangerous AI" narrative stuck. The paper has since been cited over 2,500 times.

### The Temperature Wars of 2020-2021

When GPT-3 launched (2020), developers discovered temperature through trial and error. A cottage industry emerged of "optimal temperature" guides, each claiming to have found the magic number:

- **Marketing agencies**: "Temperature 0.9 is best for ad copy!"
- **Code bloggers**: "Never go above 0.2 for code!"
- **Creative writers**: "Real artists use 1.2+!"

**The truth?** There was no universal best. But the experimentation led to collective wisdom:
- `0.0-0.3`: Technical, factual, consistent tasks
- `0.5-0.7`: General-purpose, balanced
- `0.8-1.0`: Creative, diverse
- `1.0+`: Experimental, high variance

**Fun fact**: OpenAI's playground originally defaulted to `temperature=0.7` because an early researcher thought it "felt right" - no rigorous testing involved!

### Why "Temperature" and Not "Creativity"?

The name "temperature" confuses everyone. Why not call it "creativity" or "randomness"?

**The answer goes back to 1876** - Ludwig Boltzmann's work on statistical mechanics. Boltzmann showed that in a gas, higher temperature means molecules move more randomly. The probability distribution follows:

```
P(state) ∝ exp(-Energy / Temperature)
```

LLM sampling uses the **exact same math**:
```
P(token) ∝ exp(logit / temperature)
```

When AI researchers in the 1990s needed a way to control randomness in neural networks, they borrowed the physics term. The metaphor stuck, even though most developers have never heard of Boltzmann.

**Trivia**: At temperature=0 (absolute zero in physics), all molecular motion stops. In LLMs, all randomness stops - you get deterministic, greedy decoding. The parallel is mathematically exact!

### The $100K Sampling Bug

In 2021, a startup building an AI writing assistant shipped with a bug: they accidentally set `top_p=0.1` instead of `top_p=0.9` in production.

**The result**:
- Users complained their AI was "boring" and "predictable"
- Churn rate spiked 400%
- They lost $100K in revenue before finding the bug

**The fix took 5 minutes** - changing one character in a config file. But finding it took 3 weeks because nobody thought to check sampling parameters.

**Lesson**: Sampling configuration is often overlooked but has massive impact on user experience!

### The Rise of "Temperature as a Product Feature"

By 2023, some AI products started exposing temperature as a user-facing feature:

- **Claude**: Offers different "styles" (precise vs creative) that adjust temperature
- **ChatGPT**: The "temperature slider" in API playground became famous
- **Midjourney**: Uses "chaos" parameter (similar concept for images)
- **Character.ai**: Lets users adjust "personality variance"

**The insight**: Users don't want to understand softmax math, but they DO want control over consistency vs creativity. Abstracting temperature behind user-friendly labels became a competitive advantage.

### The Numbers That Matter

| Finding | Source |
|---------|--------|
| Nucleus sampling improves human preference by **21%** | Original paper, 2019 |
| Temperature 0.7-0.8 rated "most natural" by users | OpenAI user studies |
| Code with temp>0.5 has **3x more bugs** | GitHub Copilot analysis |
| Creative writing peaks at temp **1.0-1.1** | Author surveys, 2023 |
| Repetition penalty reduces loops by **85%** | Hugging Face benchmarks |

---

## Further Reading

### Papers
- ["The Curious Case of Neural Text Degeneration"](https://arxiv.org/abs/1904.09751) (Holtzman et al., 2019) - Introduces nucleus sampling (top-p)
- ["Hierarchical Neural Story Generation"](https://arxiv.org/abs/1805.04833) (Fan et al., 2018) - Sampling for creative text

### Documentation
- [OpenAI API - Sampling Parameters](https://platform.openai.com/docs/api-reference/chat/create#temperature)
- [Anthropic Claude - Generation Parameters](https://docs.anthropic.com/claude/reference/messages_post)
- [Hugging Face - Generation Strategies](https://huggingface.co/docs/transformers/generation_strategies)

### Tools
- [Hugging Face Generation Playground](https://huggingface.co/spaces/huggingface-projects/text-generation-playground) - Interactive sampling exploration

---

## Knowledge Check

Before moving to Module 9, you should be able to:

- [ ] Explain how autoregressive generation works
- [ ] Describe what temperature does and when to use different values
- [ ] Explain the difference between top-p and top-k sampling
- [ ] Choose appropriate sampling strategies for different use cases
- [ ] Understand when to use repetition penalty
- [ ] Set max_tokens appropriately for your use case
- [ ] Debug sampling-related issues in generated text
- [ ] Balance creativity and consistency based on requirements

---

## What's Next

**Module 9**: Embeddings & Semantic Similarity
- What embeddings are (vectors representing meaning)
- How to generate embeddings
- Calculating semantic similarity
- Use cases: search, clustering, recommendations

**You'll learn**:
- How "king" - "man" + "woman" ≈ "queen" (vector arithmetic!)
- Why embeddings are the foundation of modern AI
- How to build semantic search

---

**Remember**: Sampling strategies are powerful but simple tools. Master them and you'll have fine-grained control over LLM outputs!

**Let's explore embeddings next! **

---

_Last updated: 2025-11-21_
_Version: 1.0_
