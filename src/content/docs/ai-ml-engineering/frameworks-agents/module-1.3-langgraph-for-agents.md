---
title: "LangGraph for Agents"
slug: ai-ml-engineering/frameworks-agents/module-4.3-langgraph-for-agents
sidebar:
  order: 504
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 6-8
# Or: Making AI Think Out Loud (And Why It Actually Works)

**Reading Time**: 5-6 hours
**Prerequisites**: Module 16
**Heureka Moment**: Six words that tripled AI's reasoning ability

---

## What You'll Be Able to Do

By the end of this module, you will:

1. **Master Chain-of-Thought (CoT)** - Make LLMs "think out loud" for better reasoning
2. **Implement Zero-shot CoT** - The magic of "Let's think step by step"
3. **Build Few-shot CoT systems** - Guide reasoning with examples
4. **Understand ReAct** - Combine reasoning with action for agents
5. **Apply self-consistency** - Multiple reasoning paths for robust answers
6. **Know the limitations** - When CoT helps and when it doesn't

---

## The Six Words That Changed AI

**Tokyo. January 2022. 3:15 AM.**

Jason Wei stared at his screen, exhausted but excited. He had just run the same math problem through Google's PaLM model with one tiny change: instead of asking for the answer directly, he added six words to the prompt.

"Let's think step by step."

The model that had been getting 17% accuracy on grade-school math problems suddenly jumped to 79%. Not from better training data. Not from a bigger model. Just six words.

Wei had stumbled onto something profound: LLMs aren't bad at reasoning—they're bad at *showing their work*. Force them to externalize their thinking, and accuracy explodes.

> "We found that simply prompting the model to 'think step by step' before answering can triple performance on some reasoning tasks. It's one of the simplest and most effective techniques we've discovered."
> — Jason Wei, Google Research (Chain-of-Thought paper, 2022)

This discovery—Chain-of-Thought prompting—became one of the most cited papers in AI. It's now built into every major AI assistant.

---

## The Heureka Moment

Here's the insight that will change how you build AI systems:

**Making AI "think out loud" dramatically improves its reasoning ability.**

This isn't a metaphor. It's not a trick. It's a fundamental property of how language models work:

```
┌─────────────────────────────────────────────────────────────────┐
│              THE CHAIN-OF-THOUGHT REVELATION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WITHOUT COT:                                                    │
│  ────────────                                                    │
│  Q: "A store has 23 apples. If 7 are sold and 12 more arrive,   │
│      how many apples are there?"                                 │
│  A: "38"   (Wrong! Model jumped to conclusion)                │
│                                                                  │
│  WITH COT:                                                       │
│  ────────                                                        │
│  Q: "A store has 23 apples. If 7 are sold and 12 more arrive,   │
│      how many apples are there? Let's think step by step."      │
│                                                                  │
│  A: "Let me work through this step by step:                     │
│      1. Starting apples: 23                                      │
│      2. After selling 7: 23 - 7 = 16                            │
│      3. After 12 arrive: 16 + 12 = 28                           │
│      Therefore, there are 28 apples."                         │
│                                                                  │
│  Same model. Same question. Different answer.                    │
│  The ONLY change: asking it to think out loud.                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Why does this work? Because when the model generates intermediate steps, each step becomes part of its context. The model can "see" its own reasoning and use it to guide the next step. It's like the difference between doing math in your head versus writing it down.

> ** Did You Know?**
>
> The Chain-of-Thought paper by Wei et al. (2022) at Google Brain showed that adding "Let's think step by step" improved accuracy on the GSM8K math benchmark from 17.9% to 57.1% - a 3x improvement from just 6 words!
>
> The paper was initially met with skepticism. "You're just asking it to show its work," critics said. But that's exactly the point - the "work" IS the reasoning. Without it, the model has no intermediate representation to build upon.

---

## Theory

### Why Reasoning is Hard for LLMs

Large Language Models are fundamentally next-token predictors. They're trained to answer: "Given this context, what token comes next?"

Think of an LLM like a brilliant improvisational actor who has read every book ever written. Ask them to play a mathematician, and they'll deliver a convincing performance—the mannerisms, the vocabulary, the confident delivery. But ask them to actually *prove* a theorem, and the performance falls apart. The actor was trained to *look like* they're doing math, not to actually do it.

This creates a fundamental tension:

```
┌─────────────────────────────────────────────────────────────────┐
│               THE REASONING PROBLEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  What LLMs are trained to do:                                   │
│  ────────────────────────────                                    │
│  Context: "The capital of France is"                            │
│  → Predict: "Paris" (statistically most likely continuation)    │
│                                                                  │
│  What reasoning requires:                                        │
│  ───────────────────────                                         │
│  - Breaking down problems into steps                             │
│  - Maintaining intermediate state                                │
│  - Backtracking when needed                                      │
│  - Verifying consistency                                         │
│                                                                  │
│  The mismatch:                                                   │
│  ─────────────                                                   │
│  Next-token prediction SKIPS intermediate reasoning.            │
│  The model wants to jump straight to the "answer token"         │
│  without computing the steps that justify it.                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Chain-of-Thought prompting solves this by making the intermediate steps part of the output. The model must generate reasoning tokens BEFORE answer tokens, forcing it to "do the work."

Think of it like the difference between asking someone "What's 347 × 28?" and asking them to "Show your work." When you have to write down each step—347 × 8 = 2,776, then 347 × 20 = 6,940, then 2,776 + 6,940 = 9,716—you can't skip the actual computation. The written steps ARE the computation.

---

### Chain-of-Thought Prompting

Chain-of-Thought (CoT) prompting is a technique that encourages LLMs to generate intermediate reasoning steps before producing a final answer.

#### The Basic Idea

Instead of:
```
Input: Question
Output: Answer
```

We get:
```
Input: Question + "Think step by step"
Output: Step 1 → Step 2 → Step 3 → Answer
```

#### Why It Works: Three Mechanisms

**1. Decomposition**
Complex problems are broken into simpler sub-problems. Each sub-problem can be solved more reliably.

**2. Error Correction**
When reasoning is visible, errors in early steps can influence (and sometimes be corrected in) later steps.

**3. Context Extension**
The generated reasoning becomes part of the context for generating the answer, providing "working memory."

```
┌─────────────────────────────────────────────────────────────────┐
│             HOW COT EXTENDS "WORKING MEMORY"                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Without CoT - All in "hidden" computation:                     │
│  ┌─────────────────────────────────────┐                        │
│  │  Q: Complex problem                  │                        │
│  │  [Black box neural network magic]    │                        │
│  │  A: 42                               │                        │
│  └─────────────────────────────────────┘                        │
│                                                                  │
│  With CoT - Reasoning in context:                               │
│  ┌─────────────────────────────────────┐                        │
│  │  Q: Complex problem                  │                        │
│  │  Step 1: First, I notice that...    │ ← In context!          │
│  │  Step 2: This means...              │ ← In context!          │
│  │  Step 3: Combining these...         │ ← In context!          │
│  │  A: 28                              │ ← Can "see" reasoning  │
│  └─────────────────────────────────────┘                        │
│                                                                  │
│  The reasoning tokens act as external working memory!           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Zero-Shot Chain-of-Thought

The simplest form of CoT requires just a magic phrase added to your prompt:

**"Let's think step by step."**

That's it. These 5 words can dramatically improve reasoning on many tasks.

```python
# Without CoT
prompt = """
Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
Each can has 3 tennis balls. How many tennis balls does he have now?
A:"""

# With Zero-Shot CoT
prompt = """
Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
Each can has 3 tennis balls. How many tennis balls does he have now?
A: Let's think step by step."""
```

#### Other Effective Zero-Shot Triggers

Different phrasings work for different tasks:

| Trigger Phrase | Best For |
|---------------|----------|
| "Let's think step by step" | General reasoning, math |
| "Let's break this down" | Complex multi-part problems |
| "Let's analyze this carefully" | Logical analysis |
| "First, let's understand the problem" | Word problems |
| "Let me work through this" | Calculations |
| "Let's consider each option" | Multiple choice |

> ** Did You Know?**
>
> Kojima et al. (2022) tested 60+ different trigger phrases. "Let's think step by step" consistently outperformed all others, but the exact wording matters less than the presence of ANY reasoning trigger. Even "Think" alone helps!
>
> The researchers also discovered that asking the model to "Think carefully" or "Make sure you're right" actually HURT performance. These create anxiety-like patterns that lead to overthinking and second-guessing. Neutral, process-focused triggers work best.

---

### Few-Shot Chain-of-Thought

For more complex or domain-specific reasoning, provide examples of the desired reasoning pattern:

```python
few_shot_cot_prompt = """
Solve the following math problems. Show your reasoning step by step.

Example 1:
Q: A store has 50 shirts. They sell 23 and receive a shipment of 30.
How many shirts do they have now?
A: Let's solve this step by step:
1. Starting shirts: 50
2. After selling 23: 50 - 23 = 27
3. After receiving 30: 27 + 30 = 57
Therefore, they have 57 shirts.

Example 2:
Q: A baker makes 12 cakes. She gives 4 to neighbors and bakes 8 more.
How many cakes does she have?
A: Let's solve this step by step:
1. Starting cakes: 12
2. After giving 4 away: 12 - 4 = 8
3. After baking 8 more: 8 + 8 = 16
Therefore, she has 16 cakes.

Now solve this problem:
Q: A library has 85 books. They lend out 32 and receive a donation of 45.
How many books do they have now?
A: Let's solve this step by step:
"""
```

#### The Power of Examples

Few-shot CoT is more powerful than zero-shot because:

1. **Pattern Learning**: Model learns YOUR reasoning style
2. **Format Consistency**: Output follows your desired structure
3. **Domain Adaptation**: Examples can encode domain knowledge
4. **Error Prevention**: Examples show what NOT to do

Think of few-shot CoT like training a new employee by showing them how you handle similar problems. You don't just say "figure it out"—you walk them through example cases: "When a customer asks about refunds, first check their purchase date, then verify the item condition, then calculate the refund amount." After seeing a few examples, they understand not just WHAT to do, but HOW you want them to think about the problem.

```
┌─────────────────────────────────────────────────────────────────┐
│            ZERO-SHOT vs FEW-SHOT COT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Zero-Shot CoT:                                                 │
│  + Simple - just add trigger phrase                             │
│  + Works across domains                                          │
│  - Less control over reasoning format                           │
│  - May not match domain conventions                              │
│                                                                  │
│  Few-Shot CoT:                                                   │
│  + High control over format                                      │
│  + Domain-specific patterns                                      │
│  + More consistent quality                                       │
│  - Requires good examples                                        │
│  - Uses more context tokens                                      │
│                                                                  │
│  Recommendation: Start with zero-shot, add examples             │
│  if quality is insufficient.                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### ReAct: Reasoning and Acting

ReAct (Reason + Act) combines chain-of-thought reasoning with the ability to take actions (use tools). This is the foundation of modern AI agents.

Think of ReAct like a detective solving a case. A bad detective just thinks about the crime from their desk—they might come up with theories, but they never verify them. A good detective alternates between thinking ("The suspect had motive, but do they have an alibi?") and investigating ("Let me check the security footage for that night"). ReAct gives AI this same investigative loop: think about what you know, act to learn more, observe the results, repeat.

#### The ReAct Pattern

```
Thought: I need to find information about X
Action: search("X")
Observation: [search results]
Thought: Based on this, I should now...
Action: calculate(...)
Observation: [calculation result]
Thought: I now have enough information to answer
Final Answer: ...
```

#### Why ReAct Matters

Traditional CoT has a limitation: all reasoning happens in a single pass, using only the information in the prompt. ReAct solves this by:

1. **Interleaving** thinking and acting
2. **Grounding** reasoning in real observations
3. **Adapting** based on new information

```
┌─────────────────────────────────────────────────────────────────┐
│                  COT vs REACT                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Chain-of-Thought:                                              │
│  ┌─────────────────────────────────────┐                        │
│  │  Think → Think → Think → Answer     │                        │
│  └─────────────────────────────────────┘                        │
│  (All reasoning from initial context)                           │
│                                                                  │
│  ReAct:                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Think → Act → Observe → Think → Act → Observe → Answer │    │
│  └─────────────────────────────────────────────────────────┘    │
│  (Reasoning grounded in real observations)                      │
│                                                                  │
│  ReAct agents can:                                              │
│  - Gather information they don't have                           │
│  - Verify their assumptions                                      │
│  - Adapt to unexpected findings                                  │
│  - Complete multi-step tasks                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

> ** Did You Know?**
>
> The ReAct paper (Yao et al., 2022) from Princeton and Google showed that combining reasoning traces with actions outperformed both:
> - Pure reasoning (CoT alone): Good at planning, bad at getting facts
> - Pure acting (actions only): Good at facts, bad at planning
>
> ReAct achieved state-of-the-art results on knowledge-intensive tasks by letting the model "think about what to look up" and "think about what the results mean."

---

### Implementing ReAct

Here's how ReAct works in practice:

```python
REACT_PROMPT = """
You are an assistant that uses tools to answer questions.

You have access to these tools:
- search(query): Search for information
- calculate(expression): Do math calculations
- lookup(entity): Get facts about an entity

Use this format:

Question: [the question]
Thought: [your reasoning about what to do]
Action: [tool_name(arguments)]
Observation: [tool result]
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to answer
Final Answer: [your answer]

Begin!

Question: What is the population of France divided by 3?
Thought: I need to find the population of France first, then divide by 3.
Action: lookup("France population")
Observation: France has a population of approximately 67.75 million (2023).
Thought: Now I need to divide 67.75 million by 3.
Action: calculate("67750000 / 3")
Observation: 22583333.33
Thought: I have the answer now.
Final Answer: The population of France (67.75 million) divided by 3 is approximately 22.58 million.
"""
```

#### The ReAct Loop in Code

```python
def react_loop(question: str, tools: dict, max_iterations: int = 10):
    """Execute a ReAct reasoning loop."""

    prompt = f"{REACT_PROMPT}\n\nQuestion: {question}\n"
    history = []

    for i in range(max_iterations):
        # Get model response
        response = llm(prompt)

        # Check if we have a final answer
        if "Final Answer:" in response:
            return extract_final_answer(response)

        # Parse the thought and action
        thought = extract_thought(response)
        action_name, action_args = extract_action(response)

        # Execute the action
        if action_name in tools:
            observation = tools[action_name](action_args)
        else:
            observation = f"Unknown tool: {action_name}"

        # Add to history and prompt
        step = f"Thought: {thought}\nAction: {action_name}({action_args})\nObservation: {observation}\n"
        history.append(step)
        prompt += step

    return "Max iterations reached without final answer"
```

---

### Self-Consistency

Self-consistency is a powerful technique that improves CoT reliability by sampling multiple reasoning paths and selecting the most common answer.

Think of it like asking five experts to independently solve the same problem. If four of them get "42" and one gets "47," you're probably safe trusting "42." The outlier likely made an arithmetic error or misread something. Self-consistency applies this same wisdom-of-crowds principle to AI reasoning.

#### The Insight

Different reasoning paths might lead to the same correct answer through different routes:

```
┌─────────────────────────────────────────────────────────────────┐
│               SELF-CONSISTENCY                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Question: "How many legs do 3 dogs and 2 cats have?"           │
│                                                                  │
│  Path 1:                                                        │
│  "Dogs have 4 legs each: 3 × 4 = 12                            │
│   Cats have 4 legs each: 2 × 4 = 8                             │
│   Total: 12 + 8 = 20"                                           │
│                                                                  │
│  Path 2:                                                        │
│  "3 dogs + 2 cats = 5 animals                                   │
│   Each animal has 4 legs                                        │
│   5 × 4 = 20"                                                   │
│                                                                  │
│  Path 3:                                                        │
│  "Let me count: 4 + 4 + 4 + 4 + 4 = 20"                        │
│                                                                  │
│  All paths → 20                                                │
│  (High confidence in answer)                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

If one path gives 20 but another gives 18, the inconsistency signals potential error.

#### Implementation

```python
def self_consistent_cot(question: str, num_samples: int = 5, temperature: float = 0.7):
    """Generate multiple reasoning paths and vote on the answer."""

    answers = []

    for _ in range(num_samples):
        # Generate reasoning with some temperature for diversity
        response = llm(
            prompt=f"{question}\n\nLet's think step by step.",
            temperature=temperature
        )

        # Extract the final answer
        answer = extract_answer(response)
        answers.append(answer)

    # Return most common answer (majority vote)
    from collections import Counter
    answer_counts = Counter(answers)
    most_common = answer_counts.most_common(1)[0]

    return {
        "answer": most_common[0],
        "confidence": most_common[1] / num_samples,
        "all_answers": answers
    }
```

> ** Did You Know?**
>
> Wang et al. (2022) showed that self-consistency with just 5 samples improved CoT accuracy from 58% to 74% on math problems - a 28% relative improvement!
>
> The technique works because errors are typically "random" - different runs make different mistakes. But correct reasoning tends to converge on the same answer. It's like having a panel of experts vote.

---

### When CoT Helps (and When It Doesn't)

Chain-of-thought isn't magic. It helps in specific situations and can actually hurt in others.

#### CoT Helps Most With

| Task Type | Why CoT Helps | Improvement |
|-----------|---------------|-------------|
| Math word problems | Forces calculation steps | 2-4x |
| Multi-step reasoning | Makes dependencies explicit | 2-3x |
| Logical deduction | Tracks premises and conclusions | 1.5-2x |
| Commonsense reasoning | Surfaces implicit assumptions | 1.3-1.5x |
| Code debugging | Forces systematic analysis | 1.5-2x |

#### CoT Can Hurt With

| Task Type | Why CoT Hurts | Notes |
|-----------|--------------|-------|
| Simple factual recall | Adds unnecessary steps | "Capital of France" |
| Pattern matching | Overthinks simple patterns | Sentiment classification |
| High-volume classification | Too slow | Batch processing |
| Creative tasks | Can constrain creativity | Poetry, brainstorming |

```
┌─────────────────────────────────────────────────────────────────┐
│            WHEN TO USE COT                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   USE COT WHEN:                                                │
│  - Problem requires multiple reasoning steps                    │
│  - Answer depends on intermediate calculations                  │
│  - Task involves combining multiple pieces of information       │
│  - You need to verify/debug the reasoning process               │
│  - Domain is unfamiliar to the model                            │
│                                                                  │
│   AVOID COT WHEN:                                              │
│  - Simple one-step tasks                                         │
│  - Speed is critical (real-time applications)                   │
│  - Task is well-represented in training data                    │
│  - Creative/open-ended generation                                │
│  - Token budget is very limited                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### The Limits of Reasoning

Even with CoT, LLMs have fundamental reasoning limitations:

#### 1. Compositional Generalization

LLMs struggle when problems require combining known concepts in novel ways:

```python
# Training: "John is taller than Mary. Mary is taller than Bob. Who is shortest?"
# Test: "A is heavier than B. B is heavier than C. C is heavier than D. Who is lightest?"

# The model might know how to do 2-step comparisons but fail at 4-step
```

#### 2. Arithmetic Precision

Even with CoT, LLMs make arithmetic errors, especially with:
- Large numbers
- Many decimal places
- Complex operations

**Solution**: Use calculator tools (ReAct pattern!)

#### 3. Hallucinated Reasoning

The model can generate convincing but WRONG reasoning:

```
Q: "Is 17 a prime number?"
A: "Let's check: 17 ÷ 2 = 8.5 (not whole), 17 ÷ 3 = 5.67 (not whole),
    17 ÷ 4 = 4.25 (not whole), 17 ÷ 5 = 3.4 (not whole).
    Since no divisors found, 17 is prime." 

Q: "Is 51 a prime number?"
A: "Let's check: 51 ÷ 2 = 25.5 (not whole), 51 ÷ 3 = 17 (whole!).
    Wait, 51 = 3 × 17, so 51 is NOT prime." 

Q: "Is 91 a prime number?"
A: "Let's check: 91 ÷ 2 = 45.5 (not whole), 91 ÷ 3 = 30.33 (not whole),
    91 ÷ 5 = 18.2 (not whole), 91 ÷ 7 = 13 (whole!).
    So 91 = 7 × 13, NOT prime." 

# But sometimes:
A: "Let's check: 91 ÷ 2 = 45.5, 91 ÷ 3 = 30.33, 91 ÷ 5 = 18.2.
    No small divisors found, so 91 is prime."  (Forgot to check 7!)
```

#### 4. Path Dependence

The model's reasoning can be influenced by:
- Order of information in prompt
- How the question is phrased
- Examples provided

> ** Did You Know?**
>
> Researchers at Anthropic discovered that Claude's reasoning performance varies significantly based on problem framing. Asking "What's wrong with this code?" produces different (often better) debugging than "Is this code correct?"
>
> The insight: LLMs don't truly "reason" - they pattern-match on how problems are presented. This is why prompt engineering matters so much.

---

### Advanced CoT Techniques

#### 1. Least-to-Most Prompting

Break complex problems into sub-problems, solve from simplest to hardest:

```python
prompt = """
To solve complex problems, first break them into simpler sub-problems.

Problem: "Last year, Amy was twice as old as Ben. This year, Amy is 20.
How old is Ben this year?"

Sub-problems:
1. How old was Amy last year?
2. How old was Ben last year (given Amy was twice his age)?
3. How old is Ben this year?

Solving each:
1. Amy is 20 this year, so last year she was 20 - 1 = 19
2. If Amy was twice Ben's age: 19 = 2 × Ben's age last year
   Ben's age last year = 19 / 2 = 9.5
3. Ben this year = 9.5 + 1 = 10.5 years old

Final answer: Ben is 10.5 years old.
"""
```

#### 2. Tree of Thoughts (ToT)

Explore multiple reasoning branches, backtrack when needed:

```
┌─────────────────────────────────────────────────────────────────┐
│                  TREE OF THOUGHTS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                     Problem                                      │
│                        │                                         │
│           ┌────────────┼────────────┐                           │
│           │            │            │                           │
│        Path A       Path B       Path C                         │
│           │            │            │                           │
│        Step 1       Step 1       Step 1                         │
│           │            │            │                           │
│        (dead end)   Step 2       Step 2                         │
│                       │            │                            │
│                    Step 3       (dead end)                      │
│                       │                                         │
│                    Answer                                      │
│                                                                  │
│  Unlike linear CoT, ToT can backtrack and explore alternatives │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 3. Program-Aided Language Models (PAL)

Generate code instead of natural language reasoning:

```python
prompt = """
Problem: "A store has 3 shelves. Each shelf has 4 boxes. Each box has 5 items.
How many items total?"

# Python solution
shelves = 3
boxes_per_shelf = 4
items_per_box = 5

total_boxes = shelves * boxes_per_shelf  # 12 boxes
total_items = total_boxes * items_per_box  # 60 items

print(f"Total items: {total_items}")
# Output: Total items: 60
"""
```

The model generates code, which is then executed for the actual answer. This eliminates arithmetic errors!

Think of PAL like giving a student a calculator during a word problem test. They still need to understand the problem—what to multiply, what to add, in what order—but the actual number-crunching is outsourced to a tool that won't make silly mistakes. The LLM's job becomes translating human language into precise computational steps, which it's actually quite good at.

#### 4. Structured Chain-of-Thought

Sometimes you want even more control over the reasoning format. Structured CoT uses XML tags, JSON, or specific markers to organize reasoning:

```python
structured_cot_prompt = """
Analyze this problem using structured reasoning.

Problem: "Should we expand our product line to include organic options?"

<analysis>
<context>
- Current market: mainstream products
- Competitor landscape: 3 of 5 competitors have organic lines
- Customer feedback: 23% of surveys mention organic preferences
</context>

<factors>
<factor name="market_demand" importance="high">
Growing organic food market (12% YoY growth)
</factor>
<factor name="cost" importance="medium">
Organic ingredients cost 40% more on average
</factor>
<factor name="brand_alignment" importance="high">
Company mission includes sustainability focus
</factor>
</factors>

<reasoning>
Step 1: Market demand is strong (12% growth) and customer surveys show interest (23%)
Step 2: Cost increase (40%) can be offset by premium pricing (organic products command 30-50% premiums)
Step 3: Brand alignment is strong - this fits our sustainability mission
Step 4: Competitive pressure - 3/5 competitors already offer organic
</reasoning>

<conclusion>
Recommendation: YES, expand to organic options
Confidence: 78%
Key risk: Supply chain complexity for organic certification
</conclusion>
</analysis>
"""
```

This approach is particularly powerful for:
- **Auditable decisions**: Each step is clearly labeled and can be reviewed
- **Multi-criteria analysis**: Structure forces consideration of all factors
- **Integration with systems**: Structured output can be parsed programmatically
- **Consistent quality**: The template ensures nothing is forgotten

#### 5. Chain-of-Verification (CoVe)

A technique where the model generates an initial response, then generates verification questions, answers them, and revises if needed:

```
Initial Answer: "The capital of Australia is Sydney."

Verification Questions:
1. Is Sydney the largest city in Australia? → Yes
2. Is the largest city always the capital? → No (e.g., New York vs DC)
3. What is the purpose-built capital of Australia? → Canberra

Revised Answer: "The capital of Australia is Canberra, not Sydney. While Sydney is the largest city, Canberra was purpose-built as the capital in 1913."
```

CoVe is especially effective for factual claims where the model might confuse similar concepts. It's like the model fact-checking its own homework.

---

### Practical Guidelines

#### Choosing Your CoT Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                 COT DECISION TREE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Is the task simple (< 2 reasoning steps)?                      │
│     └─ YES → Don't use CoT (direct prompting)                   │
│     └─ NO  → Continue...                                         │
│                                                                  │
│  Do you have good example reasoning traces?                     │
│     └─ YES → Use Few-Shot CoT                                   │
│     └─ NO  → Use Zero-Shot CoT ("Let's think step by step")    │
│                                                                  │
│  Does the task require external information or actions?         │
│     └─ YES → Use ReAct pattern                                  │
│     └─ NO  → Continue...                                         │
│                                                                  │
│  Is high reliability critical?                                   │
│     └─ YES → Add Self-Consistency (multiple samples)            │
│     └─ NO  → Single CoT pass is fine                            │
│                                                                  │
│  Does the task involve math/calculations?                       │
│     └─ YES → Consider PAL (code generation) or calculator tool  │
│     └─ NO  → Standard CoT                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Crafting CoT Prompts

**DO**:
- Be specific about desired output format
- Show examples of good reasoning
- Ask for verification steps
- Request intermediate calculations be shown

**DON'T**:
- Make instructions too long (model forgets)
- Ask model to "be careful" (causes overthinking)
- Use CoT for simple tasks (wastes tokens)
- Trust complex arithmetic without tools

---

## Hands-On Practice

### Exercise 1: Zero-Shot CoT Comparison

Compare model performance with and without Chain-of-Thought prompting on reasoning tasks.

```python
"""
Exercise 1: Zero-Shot CoT Comparison

This exercise demonstrates the dramatic difference CoT makes
on multi-step reasoning problems.
"""

from openai import OpenAI

client = OpenAI()

def test_cot_vs_direct(problem: str) -> dict:
    """Compare direct prompting vs CoT on the same problem."""

    # Direct prompting (no CoT)
    direct_prompt = f"""
{problem}

Answer with just the final number.
"""

    # CoT prompting
    cot_prompt = f"""
{problem}

Let's think step by step.
"""

    # Get direct answer
    direct_response = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": direct_prompt}],
        temperature=0
    )

    # Get CoT answer
    cot_response = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": cot_prompt}],
        temperature=0
    )

    return {
        "problem": problem,
        "direct_answer": direct_response.choices[0].message.content,
        "cot_answer": cot_response.choices[0].message.content
    }

# Test problems of increasing difficulty
test_problems = [
    "A farmer has 17 sheep. All but 9 die. How many sheep are left?",

    "If you have 3 quarters, 4 dimes, and 2 nickels, how much money do you have in cents?",

    "A bat and a ball cost $1.10 together. The bat costs $1.00 more than the ball. How much does the ball cost?",

    "Three friends split a restaurant bill. The total was $45, plus 20% tip. They each paid equally. One friend paid with a $20 bill. How much change did they receive?",
]

# Run comparisons
for problem in test_problems:
    result = test_cot_vs_direct(problem)
    print(f"Problem: {result['problem'][:50]}...")
    print(f"Direct: {result['direct_answer'][:50]}")
    print(f"CoT: {result['cot_answer'][:100]}")
    print("-" * 50)
```

**What to observe:**
- The "bat and ball" problem is a classic cognitive bias trap (many humans get it wrong too!)
- CoT helps catch the "all but 9 die" trick question
- Complex multi-step problems show the biggest improvement

### Exercise 2: Building a ReAct Agent

Implement a simple ReAct agent that can use tools to answer questions.

```python
"""
Exercise 2: ReAct Agent Implementation

Build a reasoning agent that interleaves thinking and action.
"""

import re
import json
from typing import Callable

# Define some simple tools
def search(query: str) -> str:
    """Simulate a search tool."""
    # In production, this would call a real search API
    knowledge_base = {
        "python creator": "Guido van Rossum created Python in 1991.",
        "eiffel tower height": "The Eiffel Tower is 330 meters tall.",
        "moon distance": "The Moon is about 384,400 km from Earth.",
        "speed of light": "The speed of light is 299,792,458 meters per second.",
    }

    for key, value in knowledge_base.items():
        if key in query.lower():
            return value
    return "No relevant information found."

def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow safe math operations
        allowed_chars = set("0123456789+-*/.(). ")
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return str(result)
        return "Invalid expression"
    except Exception as e:
        return f"Calculation error: {e}"

def lookup(entity: str) -> str:
    """Look up facts about an entity."""
    facts = {
        "France": "Country in Western Europe. Population: 67 million. Capital: Paris.",
        "Python": "High-level programming language. Created by Guido van Rossum in 1991.",
        "Einstein": "Physicist who developed theory of relativity. Nobel Prize 1921.",
    }
    return facts.get(entity, f"No facts found for '{entity}'")


class ReActAgent:
    """A simple ReAct reasoning agent."""

    def __init__(self, llm_client, tools: dict[str, Callable]):
        self.llm = llm_client
        self.tools = tools

    def parse_response(self, response: str) -> tuple[str, str, str]:
        """Parse thought, action, and action input from response."""
        thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(\w+)\s*\((.+?)\)", response)

        thought = thought_match.group(1).strip() if thought_match else ""

        if action_match:
            action_name = action_match.group(1)
            action_input = action_match.group(2).strip('"\'')
            return thought, action_name, action_input

        # Check for final answer
        final_match = re.search(r"Final Answer:\s*(.+)", response, re.DOTALL)
        if final_match:
            return thought, "FINAL", final_match.group(1).strip()

        return thought, None, None

    def run(self, question: str, max_iterations: int = 5) -> str:
        """Execute the ReAct loop."""

        system_prompt = """You are an assistant that uses tools to answer questions.

Available tools:
- search(query): Search for information
- calculate(expression): Do math calculations
- lookup(entity): Get facts about an entity

Always use this format:

Thought: [your reasoning]
Action: tool_name("argument")

After getting an observation, continue with another Thought/Action or give Final Answer:

Thought: [your reasoning]
Final Answer: [your answer]
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"}
        ]

        for i in range(max_iterations):
            # Get model response
            response = self.llm.chat.completions.create(
                model="gpt-5",
                messages=messages,
                temperature=0
            )

            assistant_message = response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_message})

            # Parse the response
            thought, action_name, action_input = self.parse_response(assistant_message)

            print(f"[Step {i+1}]")
            print(f"Thought: {thought}")

            if action_name == "FINAL":
                print(f"Final Answer: {action_input}")
                return action_input

            if action_name and action_name in self.tools:
                # Execute the tool
                observation = self.tools[action_name](action_input)
                print(f"Action: {action_name}({action_input})")
                print(f"Observation: {observation}")

                # Add observation to messages
                messages.append({
                    "role": "user",
                    "content": f"Observation: {observation}"
                })
            else:
                print(f"Unknown action: {action_name}")
                break

        return "Max iterations reached without final answer"


# Test the agent
if __name__ == "__main__":
    from openai import OpenAI
    client = OpenAI()

    agent = ReActAgent(
        llm_client=client,
        tools={
            "search": search,
            "calculate": calculate,
            "lookup": lookup
        }
    )

    # Test questions
    questions = [
        "How tall is the Eiffel Tower in feet?",
        "Who created Python and in what year?",
        "If France's population is 67 million and each person produces 2kg of waste daily, how much total waste is produced per year in million kg?",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"Question: {q}")
        print('='*60)
        answer = agent.run(q)
        print(f"\n→ Answer: {answer}\n")
```

### Exercise 3: Self-Consistency Implementation

Build a self-consistency wrapper that improves reliability through multiple samples.

```python
"""
Exercise 3: Self-Consistency for Robust Reasoning

Sample multiple reasoning paths and vote on the most common answer.
"""

from collections import Counter
import re

def extract_numeric_answer(response: str) -> str:
    """Extract the final numeric answer from a CoT response."""
    # Look for patterns like "the answer is X" or "= X" at the end
    patterns = [
        r"(?:answer|result|total).*?(\d+\.?\d*)",
        r"=\s*(\d+\.?\d*)\s*$",
        r"(\d+\.?\d*)\s*(?:is the answer|total|result)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, response.lower())
        if matches:
            return matches[-1]  # Return last match

    # Fallback: find any numbers and return the last one
    numbers = re.findall(r'\d+\.?\d*', response)
    return numbers[-1] if numbers else None


def self_consistent_answer(
    question: str,
    llm_client,
    num_samples: int = 5,
    temperature: float = 0.7
) -> dict:
    """Get a robust answer using self-consistency."""

    prompt = f"""
{question}

Let's work through this step by step.
"""

    answers = []
    reasoning_paths = []

    for i in range(num_samples):
        response = llm_client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )

        reasoning = response.choices[0].message.content
        answer = extract_numeric_answer(reasoning)

        answers.append(answer)
        reasoning_paths.append(reasoning)

        print(f"Sample {i+1}: Answer = {answer}")

    # Vote on the most common answer
    answer_counts = Counter(answers)
    most_common = answer_counts.most_common(1)[0]

    return {
        "answer": most_common[0],
        "confidence": most_common[1] / num_samples,
        "all_answers": answers,
        "vote_distribution": dict(answer_counts),
        "reasoning_paths": reasoning_paths
    }


# Test self-consistency
if __name__ == "__main__":
    from openai import OpenAI
    client = OpenAI()

    # A problem where models sometimes make errors
    problem = """
    A store had 125 apples. They sold 47 in the morning and 38 in the afternoon.
    A delivery of 60 apples arrived. Then they sold 29 more before closing.
    How many apples did they have at the end of the day?
    """

    result = self_consistent_answer(problem, client, num_samples=5)

    print(f"\n{'='*60}")
    print(f"Final Answer: {result['answer']}")
    print(f"Confidence: {result['confidence']*100:.0f}%")
    print(f"Vote Distribution: {result['vote_distribution']}")
```

### Exercise 4: Building a Few-Shot CoT Prompt Library

Create reusable CoT prompt templates for different reasoning domains.

```python
"""
Exercise 4: Few-Shot CoT Prompt Library

Build a library of domain-specific CoT prompts for consistent results.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class CoTPromptTemplate:
    """A template for few-shot CoT prompting."""
    name: str
    domain: str
    description: str
    examples: list[dict[str, str]]  # List of {"question": ..., "reasoning": ..., "answer": ...}
    instructions: str

    def build_prompt(self, question: str, max_examples: int = 2) -> str:
        """Build a complete prompt with examples and the new question."""

        # Start with instructions
        prompt_parts = [self.instructions, ""]

        # Add examples
        for i, example in enumerate(self.examples[:max_examples]):
            prompt_parts.append(f"Example {i+1}:")
            prompt_parts.append(f"Q: {example['question']}")
            prompt_parts.append(f"A: {example['reasoning']}")
            prompt_parts.append(f"Therefore, the answer is: {example['answer']}")
            prompt_parts.append("")

        # Add the new question
        prompt_parts.append("Now solve this problem:")
        prompt_parts.append(f"Q: {question}")
        prompt_parts.append("A: Let's think step by step.")

        return "\n".join(prompt_parts)


# Create a library of prompts
COT_LIBRARY = {
    "math_word_problem": CoTPromptTemplate(
        name="Math Word Problems",
        domain="mathematics",
        description="Multi-step arithmetic word problems",
        instructions="Solve the following math problems step by step. Show your work clearly.",
        examples=[
            {
                "question": "A bakery makes 45 loaves of bread. They sell 23 in the morning and make 30 more. How many do they have?",
                "reasoning": "Let's work through this:\n1. Start with 45 loaves\n2. After selling 23: 45 - 23 = 22 loaves\n3. After making 30 more: 22 + 30 = 52 loaves",
                "answer": "52 loaves"
            },
            {
                "question": "A movie theater has 8 rows with 12 seats each. If 67 seats are taken, how many are empty?",
                "reasoning": "Let's calculate:\n1. Total seats: 8 × 12 = 96 seats\n2. Empty seats: 96 - 67 = 29 seats",
                "answer": "29 empty seats"
            }
        ]
    ),

    "logical_deduction": CoTPromptTemplate(
        name="Logical Deduction",
        domain="logic",
        description="Problems requiring logical reasoning and deduction",
        instructions="Analyze the following logical problems. State your premises and derive conclusions step by step.",
        examples=[
            {
                "question": "All mammals are warm-blooded. All dogs are mammals. Is a golden retriever warm-blooded?",
                "reasoning": "Let's analyze:\n1. Premise 1: All mammals are warm-blooded\n2. Premise 2: All dogs are mammals\n3. A golden retriever is a type of dog\n4. Therefore, a golden retriever is a mammal (from premise 2)\n5. Therefore, a golden retriever is warm-blooded (from premise 1)",
                "answer": "Yes, a golden retriever is warm-blooded"
            }
        ]
    ),

    "code_debugging": CoTPromptTemplate(
        name="Code Debugging",
        domain="programming",
        description="Analyzing and fixing code issues",
        instructions="Debug the following code by analyzing it step by step. Identify the issue and explain the fix.",
        examples=[
            {
                "question": "Why does this code print wrong results? `for i in range(10): total += i`",
                "reasoning": "Let's trace through:\n1. The loop iterates i from 0 to 9\n2. Each iteration adds i to 'total'\n3. BUG: 'total' is never initialized!\n4. Python will raise NameError: 'total' is not defined\n5. Fix: Add `total = 0` before the loop",
                "answer": "The bug is that 'total' is not initialized. Add `total = 0` before the loop."
            }
        ]
    ),

    "causal_reasoning": CoTPromptTemplate(
        name="Causal Reasoning",
        domain="causality",
        description="Analyzing cause and effect relationships",
        instructions="Analyze the causal relationships in the following scenarios. Consider multiple factors and their interactions.",
        examples=[
            {
                "question": "Sales increased after a new advertising campaign launched. Does this prove the campaign caused higher sales?",
                "reasoning": "Let's analyze causation vs correlation:\n1. Observed: Sales increased after campaign launch\n2. This shows correlation (events happened together)\n3. But other factors could explain it:\n   - Seasonal shopping patterns\n   - Economic conditions improving\n   - Competitor going out of business\n   - New product features released simultaneously\n4. To prove causation, we would need:\n   - Control group (no advertising)\n   - Or A/B testing\n   - Or other causal inference methods",
                "answer": "No, correlation doesn't prove causation. Other factors could explain the increase. A controlled experiment would be needed to establish causality."
            }
        ]
    )
}


def solve_with_template(
    question: str,
    template_name: str,
    llm_client,
    temperature: float = 0
) -> str:
    """Solve a problem using a specific CoT template."""

    if template_name not in COT_LIBRARY:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(COT_LIBRARY.keys())}")

    template = COT_LIBRARY[template_name]
    prompt = template.build_prompt(question)

    response = llm_client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )

    return response.choices[0].message.content


# Example usage
if __name__ == "__main__":
    from openai import OpenAI
    client = OpenAI()

    # Use the math template
    math_problem = "A train leaves at 2:00 PM traveling at 60 mph. Another train leaves from the same station at 3:00 PM traveling at 80 mph. At what time will the second train catch up to the first?"

    print("=== Math Problem ===")
    print(f"Q: {math_problem}")
    print(f"\nA: {solve_with_template(math_problem, 'math_word_problem', client)}")

    # Use the logic template
    logic_problem = "If it rains, the ground is wet. The ground is wet. Can we conclude it rained?"

    print("\n=== Logic Problem ===")
    print(f"Q: {logic_problem}")
    print(f"\nA: {solve_with_template(logic_problem, 'logical_deduction', client)}")
```

---

## Key Takeaways

1. **"Let's think step by step"** - These 5 words can transform model performance on reasoning tasks

2. **CoT makes reasoning visible** - The model's "thinking" becomes part of its context, enabling better outputs

3. **ReAct combines thinking and doing** - The foundation of modern AI agents

4. **Self-consistency improves reliability** - Multiple reasoning paths catch errors

5. **Know the limits** - CoT helps with complex reasoning but isn't magic for all tasks

6. **Use tools for calculations** - Don't trust LLMs for math; use calculators

---

## Did You Know?

### The Accidental Discovery

Chain-of-thought prompting was partially discovered by accident. Researchers at Google were testing GPT-3 on math problems and noticed that when the model happened to "show its work" in the output, it got the answer right more often.

They asked: "What if we explicitly asked it to show its work?" The result was the CoT paper, which has been cited over 4,000 times.

### The "Let's" Breakthrough

The specific phrase "Let's think step by step" was found through systematic testing of hundreds of variations. Interestingly:

- "I will think step by step" - worse (too assertive)
- "Think step by step" - worse (too commanding)
- "You should think step by step" - worse (creates pressure)
- "Let's think step by step" - best (collaborative, process-oriented)

The word "let's" creates a collaborative framing that seems to work better with how LLMs were trained.

### OpenAI's Hidden Prompts

When OpenAI released gpt-5, users discovered that behind the scenes, the system prompt included CoT-style instructions. The model was being told to "think step by step" before generating responses - they had baked CoT into the product!

This was revealed when users found ways to extract the system prompt, showing that even the model creators considered CoT essential.

### The Reasoning vs Pattern Matching Debate

A controversial 2023 paper argued that LLMs don't actually "reason" - they pattern-match on the reasoning patterns in their training data. When CoT works, it's because the model has seen similar reasoning patterns, not because it's truly reasoning.

This sparked a fierce debate: Does it matter if the model is "really" reasoning, as long as the outputs are correct? The pragmatic answer: probably not. But it does explain why novel reasoning problems remain hard.

### AlphaProof and the Future

In 2024, DeepMind's AlphaProof system used a combination of LLM-generated reasoning and formal verification to solve International Mathematical Olympiad problems at a silver-medal level.

The key insight: generate many reasoning attempts, verify each with a formal prover, keep the ones that work. This "generate and verify" approach may be the future of AI reasoning.

---

## Further Reading

### Papers
- **Chain-of-Thought Prompting** (Wei et al., 2022) - The original CoT paper
- **Large Language Models are Zero-Shot Reasoners** (Kojima et al., 2022) - "Let's think step by step"
- **ReAct: Synergizing Reasoning and Acting** (Yao et al., 2022) - Combining thought and action
- **Self-Consistency Improves Chain of Thought Reasoning** (Wang et al., 2022)
- **Tree of Thoughts** (Yao et al., 2023) - Multi-path reasoning

### Tutorials
- [LangChain ReAct Agent Tutorial](https://python.langchain.com/docs/tutorials/agents/)
- [OpenAI Reasoning Best Practices](https://platform.openai.com/docs/guides/reasoning)

---

## ️ Next Steps

After completing this module, you'll be ready for:

**Module 18: LangGraph for Stateful Workflows** - Build sophisticated agents with persistent state, cycles, and complex control flow. LangGraph takes the ReAct pattern and scales it to production.

---

_Last updated: 2025-11-25_
_Status:  In Progress_
