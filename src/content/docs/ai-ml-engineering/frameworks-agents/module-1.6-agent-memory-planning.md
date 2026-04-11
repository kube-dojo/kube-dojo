---
title: "Agent Memory & Planning"
slug: ai-ml-engineering/frameworks-agents/module-4.6-agent-memory-planning
sidebar:
  order: 507
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6
---
**Reading Time**: 8-9 hours
**Prerequisites**: Module 19
**Heureka Moment**: Agents with memory and planning solve problems they couldn't before
---

Stanford University. March 2023. 2:47 AM. PhD student Joon Sung Park sat in his dimly lit office, watching something extraordinary unfold on his screen. Twenty-five AI characters were living their lives in a simulated town called Smallville—and they had started doing things he never programmed them to do.

Klaus, one of the AI characters, had been quietly writing a poem about Maria, another resident. When Klaus heard through the social network that Maria was single, he made a decision: he would ask her on a date. No human told him to. No code specified romantic interactions. Klaus simply *remembered* his feelings about Maria and *decided* to act on them.

Meanwhile, Isabella was planning a Valentine's Day party. Not because the simulation required festivities, but because she *reflected* on the calendar, *remembered* that people enjoy parties, and *chose* to organize one.

By morning, the AI town had social cliques, spreading gossip, and budding relationships—all emergent behavior from one simple addition: memory.

"We didn't program any of this," Park later told reporters, still amazed. "The characters developed it themselves, just by remembering and reflecting. Memory turned simple chatbots into something that felt... alive."

The resulting paper, "Generative Agents: Interactive Simulacra of Human Behavior," has been cited over 2,000 times. It proved something fundamental that every AI engineer should understand: **memory is what transforms a chatbot into an agent.**

This module teaches you how to build that memory—and much more. You'll learn the architectures that make agents remember, plan, collaborate, and improve themselves. By the end, you'll understand why a $10/month API subscription can now do what million-dollar enterprise software couldn't do five years ago.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Master agent memory systems (short-term, long-term, episodic, summary)
- Implement planning algorithms (ReWOO, Plan-and-Execute, Tree of Thought)
- Build multi-agent collaborative systems
- Design agent architectures (supervisor, swarm, hierarchical)
- Implement self-improvement patterns (reflection, self-correction)
- Understand when and how agents create their own tools

---

## The Evolution of AI Agents: A Brief History

Before we dive into implementation, understanding how we got here helps you avoid reinventing failed approaches and appreciate why modern architectures work.

### The Symbolic AI Era (1950s-1980s): Rules and Logic

The first "agents" were rule-based expert systems. Think of them like extremely detailed instruction manuals—thousands of if-then rules crafted by human experts.

**MYCIN** (1976) at Stanford could diagnose bacterial infections. It had 600 hand-coded rules like: "If the infection is bacterial AND the patient has a compromised immune system, THEN consider Pseudomonas." MYCIN performed as well as specialists in blind tests—but took 10 years and thousands of person-hours to build.

The problem? Rules don't scale. Every new disease required new rules. Every edge case required explicit handling. And when rules conflicted, resolving them required more rules.

> **Did You Know?** The famous Cyc project, started in 1984 by Doug Lenat, attempted to encode all human common-sense knowledge in logical rules. After 40 years and estimated $100M+ in funding, it contains over 25 million hand-entered assertions. Despite this massive effort, it still struggles with questions a 5-year-old could answer because common sense is contextual, not rule-based.

### The Statistical Learning Era (1990s-2010s): Data-Driven Intelligence

Machine learning shifted the paradigm: instead of encoding rules, learn patterns from data. Agents became statistical models—less brittle, but still limited in reasoning.

**IBM's Watson** (2011) beat human champions at Jeopardy using a pipeline of statistical NLP models. It was impressive, but under the hood was a fragile Rube Goldberg machine of 100+ specialized algorithms. Adding new capabilities meant adding new algorithms—a different kind of scaling problem.

The agents of this era were narrow: excellent at one task, useless at others. A spam filter couldn't summarize emails. A recommendation engine couldn't explain its choices. Each capability required its own model, its own data, its own engineering team.

### The Transformer Era (2017-2022): General-Purpose Reasoning

The 2017 "Attention Is All You Need" paper introduced transformers, and everything changed. By 2020, GPT-3 showed that a single model could write essays, translate languages, answer questions, and generate code—capabilities that previously required dozens of specialized systems.

But these early LLMs were still stateless. Ask GPT-3 a question, get an answer. No memory. No planning. No tool use. They were incredibly capable but fundamentally limited: brilliant goldfish that forgot everything between prompts.

### The Agentic Era (2022-Present): Memory, Tools, and Autonomy

**ReAct** (Yao et al., October 2022) was the breakthrough. Researchers at Princeton showed that interleaving reasoning ("I need to find the capital of France") with actions ("Search: capital of France") dramatically improved LLM performance on complex tasks. The paper has over 2,500 citations.

Then came the explosion:
- **Toolformer** (Meta, February 2023): LLMs that learn to use tools
- **Generative Agents** (Stanford, April 2023): The Smallville paper showing emergent social behavior from memory
- **AutoGPT** (March 2023): The viral experiment showing autonomous task execution
- **gpt-5 with function calling** (June 2023): Native tool use built into a commercial LLM
- **LangGraph** (2024): Production-grade stateful agent framework

We're now in an era where agents can:
- Remember context across sessions
- Plan multi-step solutions
- Use external tools (search, code execution, APIs)
- Reflect on and improve their own outputs
- Collaborate with other agents

The rest of this module teaches you how to build these systems.

### The Key Insight from History

Every era improved by making agents more *modular*. Symbolic AI failed because every capability was hard-coded. Statistical learning improved by separating data from logic. LLMs improved by separating training from inference. Modern agents improve by separating memory from reasoning from action.

Think of it like building with LEGO vs carving from stone. Early agents were monolithic sculptures—beautiful but inflexible. Modern agents are LEGO constructions—you can swap out the memory system, change the planner, upgrade the tools, all without rebuilding from scratch.

---

## Why Agents, Why Now?

Three things converged in 2022-2023 to make practical AI agents possible:

### 1. LLMs Became Good Enough

Pre-2022 language models could write coherent paragraphs but struggled with reasoning. gpt-5 crossed a critical threshold: it could follow complex instructions, reason through multi-step problems, and recover from mistakes. Below that threshold, agents were frustratingly stupid. Above it, they became surprisingly capable.

Think of it like self-driving cars. You can build all the planning and perception systems you want, but if the underlying AI can't reliably distinguish a pedestrian from a shadow, the system fails. LLMs needed to reach "reliable enough" before agent architectures became practical.

### 2. Context Windows Expanded

GPT-3 had 4,096 tokens. gpt-5 Turbo has 128,000. Claude can handle 200,000. This expansion is transformative for agents because they need context for:
- Recent conversation history
- Retrieved memories
- Current plan
- Tool results
- Task instructions

With 4K context, agents had to summarize aggressively, losing information. With 128K+, agents can maintain rich working memory without constant compression.

### 3. Tool Use Became Native

Early LLM tool use was hacky: parse JSON from text, hope the model formatted it correctly, retry on failures. Function calling changed this. When gpt-5 gained native tool support in June 2023, tool use became:
- Reliable: Structured outputs, not text parsing
- Efficient: Single API call for tool selection
- Natural: Models trained specifically for tool use

This made the "act" part of ReAct practical at scale.

---

## The Heureka Moment

**Agents with memory and planning can solve problems they couldn't before!**

Think about the difference between:
1. A calculator (stateless, single operation)
2. A spreadsheet (state, but human-driven planning)
3. A human accountant (memory, planning, collaboration, self-correction)

We've built systems like #1 and #2. This module teaches you to build #3.

---

## Part 1: Agent Memory Systems

### The Memory Problem

Think of an AI agent without memory like a brilliant amnesiac doctor. They can diagnose any condition brilliantly in the moment, but if you come back tomorrow, they'll have no idea who you are, what they diagnosed, or what treatment they recommended. You'd have to explain your entire medical history from scratch every visit. Memory systems fix this by giving agents the equivalent of medical records, notes, and institutional knowledge.

Consider this conversation:

```
User: My name is Alex and I work at TechCorp.
Agent: Nice to meet you, Alex from TechCorp!

[1000 messages later...]

User: Where do I work again?
Agent: I'm sorry, I don't have information about where you work.
```

Without memory, agents are goldfish - brilliant in the moment, but unable to build relationships or learn from experience.

### Did You Know?

In 2023, researchers at Stanford created "Generative Agents" - 25 AI characters living in a Sims-like world. Each agent had three memory types: a "memory stream" of observations, a "reflection" system for synthesizing insights, and a "plan" for daily activities. The agents spontaneously organized a Valentine's Day party, spread gossip about each other, and formed social cliques - all emergent behavior from the memory architecture!

The paper "Generative Agents: Interactive Simulacra of Human Behavior" has been cited 2,000+ times since April 2023.

### Memory Types

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT MEMORY ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  SHORT-TERM  │  │   LONG-TERM  │  │   EPISODIC   │          │
│  │   (Buffer)   │  │   (Vector)   │  │  (Specific)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └────────────┬────┴────────────┬────┘                   │
│                      │                 │                        │
│              ┌───────▼───────┐ ┌───────▼───────┐               │
│              │    SUMMARY    │ │   SEMANTIC    │               │
│              │  (Compressed) │ │   (Indexed)   │               │
│              └───────────────┘ └───────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 1. Short-Term Memory (Conversation Buffer)

The simplest form - keep recent messages in context.

```python
from typing import List
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationBuffer:
    """Short-term memory: recent conversation history."""
    messages: List[Message] = field(default_factory=list)
    max_messages: int = 20  # Keep last N messages

    def add(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))
        # Trim to max size
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_context(self) -> str:
        """Format messages for LLM context."""
        return "\n".join([
            f"{m.role}: {m.content}"
            for m in self.messages
        ])

    def clear(self):
        self.messages = []
```

**Limitations**:
- Fixed window size
- Loses information outside window
- No semantic understanding of what's important

#### 2. Long-Term Memory (Vector Store)

Store experiences as embeddings, retrieve relevant ones when needed.

```python
from dataclasses import dataclass, field
from typing import List, Optional
import json

@dataclass
class MemoryEntry:
    """A single memory with embedding."""
    content: str
    embedding: List[float]
    metadata: dict = field(default_factory=dict)
    timestamp: str = ""
    importance: float = 1.0  # How significant is this memory?

class VectorMemory:
    """Long-term memory using vector similarity."""

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.memories: List[MemoryEntry] = []

    def store(self, content: str, metadata: dict = None):
        """Store a new memory."""
        embedding = self.embedding_model.embed(content)
        importance = self._calculate_importance(content)

        memory = MemoryEntry(
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            timestamp=datetime.now().isoformat(),
            importance=importance
        )
        self.memories.append(memory)

    def retrieve(self, query: str, k: int = 5) -> List[MemoryEntry]:
        """Retrieve k most relevant memories."""
        query_embedding = self.embedding_model.embed(query)

        # Calculate similarity scores
        scored = []
        for memory in self.memories:
            similarity = self._cosine_similarity(
                query_embedding,
                memory.embedding
            )
            # Weight by importance and recency
            score = similarity * memory.importance
            scored.append((score, memory))

        # Return top k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]

    def _calculate_importance(self, content: str) -> float:
        """Estimate importance of a memory."""
        # Simple heuristics - could use LLM for better scoring
        importance = 1.0

        # Questions are often important
        if "?" in content:
            importance += 0.2

        # Personal information
        personal_keywords = ["my name", "i work", "i live", "my email"]
        for kw in personal_keywords:
            if kw in content.lower():
                importance += 0.3

        # Preferences and decisions
        if any(w in content.lower() for w in ["prefer", "want", "decided", "chose"]):
            importance += 0.2

        return min(importance, 2.0)  # Cap at 2x

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
```

#### 3. Episodic Memory (Specific Experiences)

Remember specific interactions as coherent episodes, not just isolated facts.

```python
@dataclass
class Episode:
    """A complete interaction episode."""
    episode_id: str
    title: str
    summary: str
    messages: List[Message]
    outcome: str  # What was achieved?
    lessons: List[str]  # What was learned?
    created_at: datetime
    embedding: List[float] = field(default_factory=list)

class EpisodicMemory:
    """Stores complete interaction episodes."""

    def __init__(self, llm, embedding_model):
        self.llm = llm
        self.embedding_model = embedding_model
        self.episodes: List[Episode] = []

    def create_episode(self, messages: List[Message]) -> Episode:
        """Create an episode from a conversation."""
        # Use LLM to summarize and extract lessons
        conversation = "\n".join([
            f"{m.role}: {m.content}" for m in messages
        ])

        analysis_prompt = f"""Analyze this conversation and extract:
1. A short title (5-10 words)
2. A one-paragraph summary
3. The outcome (what was achieved)
4. Key lessons learned (bullet points)

Conversation:
{conversation}

Respond in JSON format:
{{
    "title": "...",
    "summary": "...",
    "outcome": "...",
    "lessons": ["...", "..."]
}}"""

        response = self.llm.generate(analysis_prompt)
        analysis = json.loads(response)

        episode = Episode(
            episode_id=f"ep_{len(self.episodes)}",
            title=analysis["title"],
            summary=analysis["summary"],
            messages=messages,
            outcome=analysis["outcome"],
            lessons=analysis["lessons"],
            created_at=datetime.now(),
            embedding=self.embedding_model.embed(analysis["summary"])
        )

        self.episodes.append(episode)
        return episode

    def recall_similar(self, situation: str, k: int = 3) -> List[Episode]:
        """Recall episodes similar to current situation."""
        query_embedding = self.embedding_model.embed(situation)

        scored = []
        for episode in self.episodes:
            similarity = self._cosine_similarity(
                query_embedding,
                episode.embedding
            )
            scored.append((similarity, episode))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:k]]
```

#### 4. Summary Memory (Compressed History)

As conversations grow, compress older history into summaries.

```python
class SummaryMemory:
    """Progressive summarization of conversation history."""

    def __init__(self, llm, summary_interval: int = 10):
        self.llm = llm
        self.summary_interval = summary_interval
        self.summaries: List[str] = []
        self.current_buffer: List[Message] = []

    def add_message(self, message: Message):
        """Add message, summarize if needed."""
        self.current_buffer.append(message)

        if len(self.current_buffer) >= self.summary_interval:
            self._summarize_buffer()

    def _summarize_buffer(self):
        """Summarize current buffer and clear it."""
        conversation = "\n".join([
            f"{m.role}: {m.content}"
            for m in self.current_buffer
        ])

        prompt = f"""Summarize this conversation segment concisely.
Focus on:
- Key information exchanged
- Decisions made
- Action items or tasks
- Important context for future reference

Conversation:
{conversation}

Summary:"""

        summary = self.llm.generate(prompt)
        self.summaries.append(summary)
        self.current_buffer = []

    def get_context(self) -> str:
        """Get full context: summaries + current buffer."""
        context_parts = []

        if self.summaries:
            context_parts.append("Previous conversation summary:")
            context_parts.extend(self.summaries)
            context_parts.append("\nRecent messages:")

        for msg in self.current_buffer:
            context_parts.append(f"{msg.role}: {msg.content}")

        return "\n".join(context_parts)
```

### Combining Memory Systems

The most capable agents combine multiple memory types:

```python
class HybridMemory:
    """Combined memory system for agents."""

    def __init__(self, llm, embedding_model):
        self.short_term = ConversationBuffer(max_messages=20)
        self.long_term = VectorMemory(embedding_model)
        self.episodic = EpisodicMemory(llm, embedding_model)
        self.summary = SummaryMemory(llm, summary_interval=15)

    def add_interaction(self, role: str, content: str):
        """Record an interaction across all memory systems."""
        message = Message(role=role, content=content)

        # Short-term: always add
        self.short_term.add(role, content)

        # Summary: track for periodic summarization
        self.summary.add_message(message)

        # Long-term: store important memories
        if self._is_important(content):
            self.long_term.store(
                content,
                metadata={"role": role}
            )

    def get_relevant_context(self, query: str) -> str:
        """Build context from all memory systems."""
        context_parts = []

        # Summaries of older conversations
        summary_context = self.summary.get_context()
        if summary_context:
            context_parts.append(f"History Summary:\n{summary_context}")

        # Relevant long-term memories
        memories = self.long_term.retrieve(query, k=5)
        if memories:
            memory_text = "\n".join([m.content for m in memories])
            context_parts.append(f"Relevant Memories:\n{memory_text}")

        # Similar past episodes
        episodes = self.episodic.recall_similar(query, k=2)
        if episodes:
            episode_text = "\n".join([
                f"- {ep.title}: {ep.summary}"
                for ep in episodes
            ])
            context_parts.append(f"Similar Past Situations:\n{episode_text}")

        # Recent conversation
        recent = self.short_term.get_context()
        context_parts.append(f"Recent Conversation:\n{recent}")

        return "\n\n".join(context_parts)

    def _is_important(self, content: str) -> bool:
        """Determine if content should go to long-term memory."""
        # Store user messages with personal info or explicit facts
        important_patterns = [
            "my name", "i am", "i work", "i live",
            "remember", "don't forget", "important",
            "always", "never", "prefer"
        ]
        content_lower = content.lower()
        return any(p in content_lower for p in important_patterns)
```

### Did You Know?

The concept of working memory in AI agents was inspired by cognitive psychology. Alan Baddeley's model of human working memory (1974) proposed a "phonological loop" for verbal information, a "visuospatial sketchpad" for visual information, and a "central executive" that coordinates them.

Modern AI agents mirror this: short-term buffers, long-term vector stores, and an LLM "executive" that decides what to remember and retrieve!

---

## Part 2: Planning Algorithms

### Why Agents Need Planning

Without planning, agents operate reactively - responding to each input without considering future steps. This leads to:

- Inefficient tool use (calling the same API repeatedly)
- Incomplete task execution (forgetting steps)
- Poor handling of dependencies (doing things out of order)

Planning transforms agents from reactive responders to proactive problem-solvers.

### Did You Know?

The Plan-and-Execute pattern was popularized by BabyAGI in April 2023 - a 140-line Python script that went viral on Twitter. Created by Yohei Nakajima (a VC!), it used gpt-5 to create a task list, execute tasks, and generate new tasks based on results. Within a week, it had 15,000 GitHub stars and spawned dozens of "autonomous agent" projects.

The key insight: separating planning from execution lets you use different models for each - a larger model for planning, smaller for execution.

### Planning Pattern 1: Plan-and-Execute

Create a plan first, then execute each step.

```
┌──────────────────────────────────────────────────────────────┐
│                    PLAN-AND-EXECUTE FLOW                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   Task   │───▶│  Planner │───▶│   Plan   │              │
│  └──────────┘    └──────────┘    └────┬─────┘              │
│                                       │                     │
│        ┌──────────────────────────────┘                     │
│        ▼                                                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Step 1  │───▶│  Step 2  │───▶│  Step 3  │───▶ Result   │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  [Execute]       [Execute]       [Execute]                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

```python
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from enum import Enum

class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PlanStep:
    """A single step in the plan."""
    step_id: int
    description: str
    tool: Optional[str] = None
    tool_input: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    depends_on: List[int] = field(default_factory=list)

@dataclass
class Plan:
    """A complete execution plan."""
    goal: str
    steps: List[PlanStep]
    current_step: int = 0

class PlanAndExecuteAgent:
    """Agent that plans before executing."""

    def __init__(self, llm, tools: Dict[str, Callable]):
        self.llm = llm
        self.tools = tools

    def create_plan(self, task: str) -> Plan:
        """Create a plan for the given task."""
        tools_description = "\n".join([
            f"- {name}: {func.__doc__}"
            for name, func in self.tools.items()
        ])

        prompt = f"""Create a step-by-step plan to accomplish this task.

Task: {task}

Available tools:
{tools_description}

For each step, specify:
1. What to do
2. Which tool to use (if any)
3. What input to give the tool

Respond in JSON format:
{{
    "steps": [
        {{
            "description": "Step description",
            "tool": "tool_name or null",
            "tool_input": "input string or null",
            "depends_on": []  // list of step indices this depends on
        }}
    ]
}}"""

        response = self.llm.generate(prompt)
        data = json.loads(response)

        steps = [
            PlanStep(
                step_id=i,
                description=s["description"],
                tool=s.get("tool"),
                tool_input=s.get("tool_input"),
                depends_on=s.get("depends_on", [])
            )
            for i, s in enumerate(data["steps"])
        ]

        return Plan(goal=task, steps=steps)

    def execute_plan(self, plan: Plan) -> str:
        """Execute a plan step by step."""
        results = []

        for step in plan.steps:
            # Check dependencies
            for dep_id in step.depends_on:
                dep_step = plan.steps[dep_id]
                if dep_step.status != StepStatus.COMPLETED:
                    step.status = StepStatus.FAILED
                    step.result = f"Dependency {dep_id} not completed"
                    continue

            step.status = StepStatus.IN_PROGRESS
            print(f"Executing: {step.description}")

            try:
                if step.tool and step.tool in self.tools:
                    # Execute tool
                    result = self.tools[step.tool](step.tool_input)
                else:
                    # Use LLM for reasoning step
                    result = self.llm.generate(
                        f"Complete this step: {step.description}\n"
                        f"Context from previous steps: {results}"
                    )

                step.result = result
                step.status = StepStatus.COMPLETED
                results.append(f"Step {step.step_id}: {result}")

            except Exception as e:
                step.status = StepStatus.FAILED
                step.result = str(e)
                results.append(f"Step {step.step_id} failed: {e}")

        # Summarize results
        return self._summarize_execution(plan, results)

    def _summarize_execution(self, plan: Plan, results: List[str]) -> str:
        """Summarize the execution results."""
        prompt = f"""Summarize the results of executing this plan.

Original goal: {plan.goal}

Execution results:
{chr(10).join(results)}

Provide a concise summary of what was accomplished and any issues."""

        return self.llm.generate(prompt)

    def run(self, task: str) -> str:
        """Plan and execute a task."""
        print(f"Creating plan for: {task}")
        plan = self.create_plan(task)

        print(f"Plan created with {len(plan.steps)} steps:")
        for step in plan.steps:
            print(f"  {step.step_id}. {step.description}")

        print("\nExecuting plan...")
        result = self.execute_plan(plan)

        return result
```

### Planning Pattern 2: ReWOO (Reason Without Observation)

Traditional ReAct interleaves reasoning and observation. ReWOO separates them:
1. **Plan all tool calls upfront** (without seeing results)
2. **Execute all tools**
3. **Solve using all results**

This reduces LLM calls dramatically!

```
┌────────────────────────────────────────────────────────────────┐
│                         ReWOO PATTERN                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Traditional ReAct (5 LLM calls):                              │
│  Think → Act → Observe → Think → Act → Observe → Think → ...   │
│                                                                │
│  ReWOO (2 LLM calls):                                          │
│  Plan [Tool1, Tool2, Tool3] → Execute All → Solve              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class ReWOOPlan:
    """A ReWOO-style plan with evidence variables."""
    steps: List[Dict[str, str]]  # {plan, tool, input, evidence_var}

class ReWOOAgent:
    """ReWOO: Reason Without Observation.

    Plans all tool calls upfront, executes them,
    then solves using all evidence.
    """

    def __init__(self, llm, tools: Dict[str, Callable]):
        self.llm = llm
        self.tools = tools

    def plan(self, task: str) -> ReWOOPlan:
        """Create a plan with evidence variables."""
        tools_desc = "\n".join([
            f"- {name}: {func.__doc__}"
            for name, func in self.tools.items()
        ])

        prompt = f"""Plan how to solve this task using the available tools.
Use #E[n] as placeholder for evidence from step n.

Task: {task}

Available tools:
{tools_desc}

Create a plan where each step has:
- Plan: What to do and why
- Tool: Which tool to use
- Input: Input for the tool (can reference #E[n])
- Evidence: #E[n] where n is step number

Example format:
Step 1:
Plan: Search for information about X
Tool: web_search
Input: "query about X"
Evidence: #E1

Step 2:
Plan: Analyze the search results from #E1
Tool: analyze
Input: #E1
Evidence: #E2

Create your plan:"""

        response = self.llm.generate(prompt)
        return self._parse_plan(response)

    def _parse_plan(self, response: str) -> ReWOOPlan:
        """Parse the planner output into structured steps."""
        steps = []
        current_step = {}

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("Step"):
                if current_step:
                    steps.append(current_step)
                current_step = {}
            elif line.startswith("Plan:"):
                current_step["plan"] = line[5:].strip()
            elif line.startswith("Tool:"):
                current_step["tool"] = line[5:].strip()
            elif line.startswith("Input:"):
                current_step["input"] = line[6:].strip()
            elif line.startswith("Evidence:"):
                current_step["evidence_var"] = line[9:].strip()

        if current_step:
            steps.append(current_step)

        return ReWOOPlan(steps=steps)

    def execute(self, plan: ReWOOPlan) -> Dict[str, str]:
        """Execute all planned tool calls, collecting evidence."""
        evidence = {}

        for i, step in enumerate(plan.steps, 1):
            tool_name = step.get("tool")
            tool_input = step.get("input", "")
            evidence_var = step.get("evidence_var", f"#E{i}")

            # Substitute previous evidence into input
            for var, value in evidence.items():
                tool_input = tool_input.replace(var, value)

            # Execute tool
            if tool_name and tool_name in self.tools:
                try:
                    result = self.tools[tool_name](tool_input)
                    evidence[evidence_var] = str(result)
                except Exception as e:
                    evidence[evidence_var] = f"Error: {e}"
            else:
                evidence[evidence_var] = f"Unknown tool: {tool_name}"

        return evidence

    def solve(self, task: str, plan: ReWOOPlan, evidence: Dict[str, str]) -> str:
        """Solve the task using collected evidence."""
        plan_text = "\n".join([
            f"Step {i}: {s['plan']}"
            for i, s in enumerate(plan.steps, 1)
        ])

        evidence_text = "\n".join([
            f"{var}: {value[:500]}..."  # Truncate long evidence
            for var, value in evidence.items()
        ])

        prompt = f"""Solve this task using the evidence collected.

Task: {task}

Plan executed:
{plan_text}

Evidence collected:
{evidence_text}

Based on this evidence, provide your final answer:"""

        return self.llm.generate(prompt)

    def run(self, task: str) -> str:
        """Full ReWOO execution: Plan → Execute → Solve."""
        print("Planning...")
        plan = self.plan(task)

        print(f"Executing {len(plan.steps)} tool calls...")
        evidence = self.execute(plan)

        print("Solving...")
        result = self.solve(task, plan, evidence)

        return result
```

### Planning Pattern 3: Tree of Thought (ToT)

Explore multiple reasoning paths, evaluate each, and select the best.

```
┌───────────────────────────────────────────────────────────────────┐
│                      TREE OF THOUGHT                              │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│                        [Problem]                                  │
│                            │                                      │
│              ┌─────────────┼─────────────┐                        │
│              ▼             ▼             ▼                        │
│         [Path A]      [Path B]      [Path C]                      │
│         score:0.7     score:0.9     score:0.4                     │
│              │             │             │                        │
│              │      ┌──────┴──────┐      X (pruned)               │
│              │      ▼             ▼                               │
│              │  [Path B1]    [Path B2]                            │
│              │  score:0.95   score:0.85                           │
│              │      │                                             │
│              │      ▼                                             │
│              │  [Solution] ← SELECTED                             │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

```python
from dataclasses import dataclass, field
from typing import List, Optional
import heapq

@dataclass
class ThoughtNode:
    """A node in the thought tree."""
    thought: str
    score: float
    parent: Optional['ThoughtNode'] = None
    children: List['ThoughtNode'] = field(default_factory=list)
    depth: int = 0

    def __lt__(self, other):
        # For heap comparison (higher score = better)
        return self.score > other.score

class TreeOfThoughtAgent:
    """Explores multiple reasoning paths."""

    def __init__(self, llm, branching_factor: int = 3, max_depth: int = 3):
        self.llm = llm
        self.branching_factor = branching_factor
        self.max_depth = max_depth

    def generate_thoughts(self, problem: str, current_path: List[str]) -> List[str]:
        """Generate possible next thoughts."""
        path_text = " → ".join(current_path) if current_path else "Starting fresh"

        prompt = f"""Problem: {problem}

Current reasoning path: {path_text}

Generate {self.branching_factor} different next steps or approaches.
Each should be a distinct way to continue solving this problem.
Be creative and consider different angles.

Format each as a separate paragraph."""

        response = self.llm.generate(prompt)

        # Split into separate thoughts
        thoughts = [t.strip() for t in response.split("\n\n") if t.strip()]
        return thoughts[:self.branching_factor]

    def evaluate_thought(self, problem: str, path: List[str]) -> float:
        """Score how promising a thought path is (0-1)."""
        path_text = " → ".join(path)

        prompt = f"""Problem: {problem}

Reasoning path so far: {path_text}

Rate this reasoning path on a scale of 0-10:
- 10: Excellent progress toward solution
- 7-9: Good progress, promising direction
- 4-6: Some progress, but uncertain
- 1-3: Poor direction, likely wrong
- 0: Dead end

Consider:
1. Does this make logical sense?
2. Is it making progress toward the goal?
3. Are there any errors or contradictions?

Respond with just a number (0-10):"""

        response = self.llm.generate(prompt)
        try:
            score = float(response.strip()) / 10.0
            return min(max(score, 0.0), 1.0)
        except:
            return 0.5

    def solve(self, problem: str) -> str:
        """Solve using tree of thought exploration."""
        # Initialize with root node
        root = ThoughtNode(thought="Start", score=1.0, depth=0)

        # Priority queue for best-first search
        frontier = [root]
        best_path = []
        best_score = 0.0

        while frontier:
            current = heapq.heappop(frontier)

            # Build current path
            path = []
            node = current
            while node.parent:
                path.append(node.thought)
                node = node.parent
            path.reverse()

            # Check if we've reached max depth
            if current.depth >= self.max_depth:
                if current.score > best_score:
                    best_score = current.score
                    best_path = path
                continue

            # Generate and evaluate children
            thoughts = self.generate_thoughts(problem, path)

            for thought in thoughts:
                child_path = path + [thought]
                score = self.evaluate_thought(problem, child_path)

                child = ThoughtNode(
                    thought=thought,
                    score=score,
                    parent=current,
                    depth=current.depth + 1
                )
                current.children.append(child)

                # Only explore promising paths
                if score > 0.3:
                    heapq.heappush(frontier, child)

                # Track best
                if score > best_score:
                    best_score = score
                    best_path = child_path

        # Generate final answer from best path
        return self._synthesize_answer(problem, best_path)

    def _synthesize_answer(self, problem: str, path: List[str]) -> str:
        """Synthesize final answer from the best reasoning path."""
        path_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(path)])

        prompt = f"""Problem: {problem}

Best reasoning path found:
{path_text}

Based on this reasoning, provide the final answer:"""

        return self.llm.generate(prompt)
```

### Did You Know?

The Tree of Thoughts paper (Yao et al., 2023) showed that gpt-5 with ToT solved 74% of "Game of 24" puzzles (make 24 from 4 numbers), compared to just 4% with standard prompting! The key was allowing the model to explore multiple paths and backtrack from dead ends - something humans do naturally but standard LLM prompting prevents.

---

## Part 3: Multi-Agent Architectures

### Why This Module Matters

Single agents have limitations:
- **Context limits**: One agent can't hold all relevant information
- **Specialization**: Different tasks need different "personalities"
- **Verification**: Self-checking is less effective than peer review
- **Parallelism**: Some tasks can be done simultaneously

### Did You Know?

In 2023, researchers at Microsoft Research created AutoGen, where agents could automatically create other agents! In one experiment, an "AgentBuilder" agent created specialized agents for different subtasks, assembled them into a team, and coordinated their work - all autonomously.

The paper noted that multi-agent debate improved factual accuracy by 15-20% over single-agent responses, because agents caught each other's mistakes.

### Architecture 1: Supervisor Pattern

One agent manages a team of specialized workers.

```
┌───────────────────────────────────────────────────────────────────┐
│                      SUPERVISOR PATTERN                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│                      ┌──────────────┐                             │
│                      │  SUPERVISOR  │                             │
│                      │  (Manager)   │                             │
│                      └──────┬───────┘                             │
│                             │                                     │
│           ┌─────────────────┼─────────────────┐                   │
│           │                 │                 │                   │
│           ▼                 ▼                 ▼                   │
│    ┌────────────┐   ┌────────────┐   ┌────────────┐              │
│    │ RESEARCHER │   │   WRITER   │   │   CRITIC   │              │
│    │  (Worker)  │   │  (Worker)  │   │  (Worker)  │              │
│    └────────────┘   └────────────┘   └────────────┘              │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

class AgentRole(Enum):
    SUPERVISOR = "supervisor"
    RESEARCHER = "researcher"
    WRITER = "writer"
    CRITIC = "critic"
    CODER = "coder"

@dataclass
class AgentMessage:
    """Message between agents."""
    sender: str
    recipient: str
    content: str
    message_type: str = "task"  # task, result, feedback

@dataclass
class WorkerAgent:
    """A specialized worker agent."""
    name: str
    role: AgentRole
    system_prompt: str
    llm: Any
    tools: Dict[str, Callable] = field(default_factory=dict)

    def process(self, task: str, context: str = "") -> str:
        """Process a task and return result."""
        prompt = f"""{self.system_prompt}

Context: {context}

Task: {task}

Your response:"""

        return self.llm.generate(prompt)

class SupervisorAgent:
    """Supervisor that coordinates worker agents."""

    def __init__(self, llm, workers: List[WorkerAgent]):
        self.llm = llm
        self.workers = {w.name: w for w in workers}
        self.message_history: List[AgentMessage] = []

    def delegate(self, task: str) -> str:
        """Delegate a task to appropriate workers."""
        # Determine which workers to use
        worker_descriptions = "\n".join([
            f"- {name} ({w.role.value}): {w.system_prompt[:100]}..."
            for name, w in self.workers.items()
        ])

        planning_prompt = f"""You are a supervisor coordinating a team.

Available workers:
{worker_descriptions}

Task to complete: {task}

Create a plan specifying:
1. Which workers to use (in order)
2. What task to give each worker
3. How to combine their outputs

Respond in JSON:
{{
    "plan": [
        {{"worker": "worker_name", "task": "specific task"}},
        ...
    ],
    "synthesis_instructions": "how to combine outputs"
}}"""

        response = self.llm.generate(planning_prompt)
        plan = json.loads(response)

        # Execute the plan
        results = {}
        context = f"Original task: {task}\n\n"

        for step in plan["plan"]:
            worker_name = step["worker"]
            worker_task = step["task"]

            if worker_name not in self.workers:
                continue

            worker = self.workers[worker_name]

            # Include previous results as context
            if results:
                context += "Previous results:\n"
                for name, result in results.items():
                    context += f"{name}: {result[:500]}...\n"

            # Get worker's output
            result = worker.process(worker_task, context)
            results[worker_name] = result

            # Track message
            self.message_history.append(AgentMessage(
                sender="supervisor",
                recipient=worker_name,
                content=worker_task,
                message_type="task"
            ))
            self.message_history.append(AgentMessage(
                sender=worker_name,
                recipient="supervisor",
                content=result,
                message_type="result"
            ))

        # Synthesize final output
        synthesis_prompt = f"""Synthesize these worker outputs into a final response.

Instructions: {plan["synthesis_instructions"]}

Worker outputs:
{json.dumps(results, indent=2)}

Final synthesized response:"""

        return self.llm.generate(synthesis_prompt)

# Example usage
def create_content_team(llm) -> SupervisorAgent:
    """Create a content creation team."""
    workers = [
        WorkerAgent(
            name="researcher",
            role=AgentRole.RESEARCHER,
            system_prompt="""You are a thorough researcher.
            Find relevant facts, statistics, and examples.
            Always cite your sources.""",
            llm=llm
        ),
        WorkerAgent(
            name="writer",
            role=AgentRole.WRITER,
            system_prompt="""You are a skilled writer.
            Transform research into engaging, clear content.
            Use vivid examples and clear explanations.""",
            llm=llm
        ),
        WorkerAgent(
            name="critic",
            role=AgentRole.CRITIC,
            system_prompt="""You are a critical reviewer.
            Check for errors, unclear explanations, and missing information.
            Suggest specific improvements.""",
            llm=llm
        )
    ]

    return SupervisorAgent(llm, workers)
```

### Architecture 2: Peer-to-Peer (Swarm)

Agents collaborate as equals, passing work between each other.

```
┌───────────────────────────────────────────────────────────────────┐
│                       SWARM PATTERN                               │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│         ┌────────────┐          ┌────────────┐                   │
│         │  Agent A   │◄────────▶│  Agent B   │                   │
│         └─────┬──────┘          └──────┬─────┘                   │
│               │                        │                          │
│               │    ┌────────────┐      │                          │
│               └───▶│  Agent C   │◄─────┘                          │
│                    └────────────┘                                 │
│                                                                   │
│  Each agent can hand off to any other agent based on the task.   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

```python
@dataclass
class SwarmAgent:
    """An agent in a swarm that can hand off to others."""
    name: str
    role: str
    description: str
    system_prompt: str
    llm: Any

    def should_handle(self, task: str) -> float:
        """Return confidence (0-1) that this agent should handle the task."""
        prompt = f"""You are {self.name}, a {self.role}.
Your specialty: {self.description}

Task: {task}

On a scale of 0-10, how well-suited are you to handle this task?
Consider your expertise and the task requirements.
Respond with just a number."""

        response = self.llm.generate(prompt)
        try:
            return float(response.strip()) / 10.0
        except:
            return 0.5

    def process(self, task: str, context: str = "") -> tuple[str, Optional[str]]:
        """Process task. Returns (response, handoff_to) or (response, None)."""
        prompt = f"""{self.system_prompt}

Context: {context}

Task: {task}

Complete this task. If you need to hand off part of the work to a
specialist, end your response with "HANDOFF: [specialist_type]"

Your response:"""

        response = self.llm.generate(prompt)

        # Check for handoff
        if "HANDOFF:" in response:
            parts = response.split("HANDOFF:")
            result = parts[0].strip()
            handoff = parts[1].strip()
            return result, handoff

        return response, None

class SwarmCoordinator:
    """Coordinates a swarm of peer agents."""

    def __init__(self, agents: List[SwarmAgent], max_handoffs: int = 5):
        self.agents = {a.name: a for a in agents}
        self.max_handoffs = max_handoffs

    def find_best_agent(self, task: str, exclude: List[str] = None) -> SwarmAgent:
        """Find the best agent for a task."""
        exclude = exclude or []
        candidates = [a for a in self.agents.values() if a.name not in exclude]

        if not candidates:
            # Return any agent if all excluded
            return list(self.agents.values())[0]

        scores = [(a.should_handle(task), a) for a in candidates]
        scores.sort(key=lambda x: x[0], reverse=True)

        return scores[0][1]

    def run(self, task: str) -> str:
        """Run the swarm to complete a task."""
        context = f"Original task: {task}\n\n"
        results = []
        handoffs = 0
        excluded = []

        current_task = task

        while handoffs < self.max_handoffs:
            # Find best agent
            agent = self.find_best_agent(current_task, excluded)

            print(f"Agent '{agent.name}' handling task...")

            # Process
            result, handoff = agent.process(current_task, context)
            results.append(f"{agent.name}: {result}")
            context += f"{agent.name}'s work:\n{result}\n\n"

            if handoff:
                # Find agent matching handoff description
                current_task = f"Continue from {agent.name}'s work: {handoff}"
                excluded.append(agent.name)
                handoffs += 1
            else:
                break

        # Combine results
        return "\n\n---\n\n".join(results)
```

### Architecture 3: Hierarchical Teams

Nested teams with supervisors at each level.

```
┌───────────────────────────────────────────────────────────────────┐
│                    HIERARCHICAL PATTERN                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│                    ┌──────────────┐                               │
│                    │   EXECUTIVE  │                               │
│                    │  (Top-level) │                               │
│                    └──────┬───────┘                               │
│                           │                                       │
│            ┌──────────────┼──────────────┐                        │
│            ▼              ▼              ▼                        │
│     ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│     │  RESEARCH  │ │  WRITING   │ │    QA      │                 │
│     │   LEAD     │ │   LEAD     │ │   LEAD     │                 │
│     └─────┬──────┘ └─────┬──────┘ └─────┬──────┘                 │
│           │              │              │                         │
│      ┌────┼────┐    ┌────┼────┐    ┌────┼────┐                   │
│      ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼                   │
│     [W1] [W2] [W3] [W4] [W5] [W6] [W7] [W8] [W9]                 │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Architecture 4: Debate

Agents argue different positions to find the truth.

```python
@dataclass
class DebateAgent:
    """An agent that argues a position."""
    name: str
    position: str  # "for" or "against" or "neutral"
    llm: Any

    def make_argument(self, topic: str, opponent_args: List[str] = None) -> str:
        """Make an argument for the position."""
        opponent_text = ""
        if opponent_args:
            opponent_text = f"\n\nOpponent's arguments:\n" + "\n".join(opponent_args)

        prompt = f"""You are arguing {self.position} the following topic.

Topic: {topic}
{opponent_text}

Make your strongest argument. Be persuasive and use evidence.
If responding to opponent's arguments, address their points directly."""

        return self.llm.generate(prompt)

class DebateArena:
    """Facilitates debates between agents."""

    def __init__(self, llm, rounds: int = 3):
        self.llm = llm
        self.rounds = rounds

    def debate(self, topic: str) -> str:
        """Run a debate on a topic."""
        for_agent = DebateAgent("Proponent", "FOR", self.llm)
        against_agent = DebateAgent("Opponent", "AGAINST", self.llm)

        for_args = []
        against_args = []

        for round_num in range(self.rounds):
            print(f"\n=== Round {round_num + 1} ===")

            # For side argues
            for_arg = for_agent.make_argument(topic, against_args)
            for_args.append(for_arg)
            print(f"\nFOR: {for_arg[:200]}...")

            # Against side responds
            against_arg = against_agent.make_argument(topic, for_args)
            against_args.append(against_arg)
            print(f"\nAGAINST: {against_arg[:200]}...")

        # Judge decides
        return self._judge(topic, for_args, against_args)

    def _judge(self, topic: str, for_args: List[str], against_args: List[str]) -> str:
        """Neutral judge evaluates the debate."""
        prompt = f"""You are a neutral judge evaluating this debate.

Topic: {topic}

Arguments FOR:
{chr(10).join(for_args)}

Arguments AGAINST:
{chr(10).join(against_args)}

Evaluate the debate and provide:
1. The stronger arguments from each side
2. Weaknesses in each side's reasoning
3. Your balanced conclusion on the topic
4. What additional information would help resolve this

Your verdict:"""

        return self.llm.generate(prompt)
```

### Did You Know?

Google DeepMind's Gemini team found that using three agents to verify each other's work reduced hallucinations by 40%! The pattern: one agent generates, second agent critiques, third agent synthesizes. They called it "Constitutional AI meets Multi-Agent Debate."

---

## Part 4: Self-Improvement Patterns

### Reflection: Agents That Evaluate Themselves

```python
class ReflectiveAgent:
    """Agent that reflects on and improves its own outputs."""

    def __init__(self, llm, max_iterations: int = 3):
        self.llm = llm
        self.max_iterations = max_iterations

    def generate_with_reflection(self, task: str) -> str:
        """Generate output with self-reflection loop."""

        # Initial generation
        output = self._generate(task)

        for i in range(self.max_iterations):
            # Reflect on output
            critique = self._reflect(task, output)

            # Check if good enough
            if self._is_satisfactory(critique):
                print(f"Satisfied after {i+1} iterations")
                break

            # Improve based on reflection
            output = self._improve(task, output, critique)

        return output

    def _generate(self, task: str) -> str:
        """Generate initial output."""
        return self.llm.generate(f"Complete this task:\n{task}")

    def _reflect(self, task: str, output: str) -> str:
        """Reflect on the output quality."""
        prompt = f"""Critically evaluate this output for the given task.

Task: {task}

Output:
{output}

Provide specific feedback on:
1. Correctness: Are there any errors or mistakes?
2. Completeness: Is anything missing?
3. Clarity: Is it clear and well-organized?
4. Quality: How could it be improved?

Be specific and constructive:"""

        return self.llm.generate(prompt)

    def _is_satisfactory(self, critique: str) -> bool:
        """Determine if the output is good enough."""
        prompt = f"""Based on this critique, is the output satisfactory?

Critique:
{critique}

Answer YES if the output is good enough with only minor issues.
Answer NO if there are significant problems that need fixing.

Answer (YES/NO):"""

        response = self.llm.generate(prompt)
        return "YES" in response.upper()

    def _improve(self, task: str, output: str, critique: str) -> str:
        """Improve output based on reflection."""
        prompt = f"""Improve this output based on the critique.

Original task: {task}

Current output:
{output}

Critique:
{critique}

Provide an improved version that addresses the critique:"""

        return self.llm.generate(prompt)
```

### Self-Correction: Fixing Mistakes Iteratively

```python
class SelfCorrectingAgent:
    """Agent that detects and corrects its own mistakes."""

    def __init__(self, llm, tools: Dict[str, Callable]):
        self.llm = llm
        self.tools = tools

    def execute_with_verification(self, task: str) -> str:
        """Execute task with self-verification."""

        # Generate solution
        solution = self._solve(task)

        # Verify the solution
        verification = self._verify(task, solution)

        if verification["is_correct"]:
            return solution

        # Self-correct based on errors found
        corrected = self._correct(task, solution, verification["errors"])

        # Verify again (could loop, but limiting to one correction)
        return corrected

    def _solve(self, task: str) -> str:
        """Generate a solution."""
        return self.llm.generate(f"Solve this task:\n{task}")

    def _verify(self, task: str, solution: str) -> dict:
        """Verify the solution for errors."""
        prompt = f"""Verify this solution for correctness.

Task: {task}

Solution:
{solution}

Check for:
1. Logical errors
2. Factual mistakes
3. Missing steps
4. Inconsistencies

Respond in JSON:
{{
    "is_correct": true/false,
    "errors": ["error1", "error2", ...],
    "confidence": 0.0-1.0
}}"""

        response = self.llm.generate(prompt)
        return json.loads(response)

    def _correct(self, task: str, solution: str, errors: List[str]) -> str:
        """Correct the solution based on identified errors."""
        prompt = f"""Fix these errors in the solution.

Task: {task}

Current solution:
{solution}

Errors to fix:
{chr(10).join(f"- {e}" for e in errors)}

Provide a corrected solution:"""

        return self.llm.generate(prompt)
```

### Tool Creation: Agents That Build Tools

The most advanced pattern: agents that create new tools when needed!

```python
class ToolCreatingAgent:
    """Agent that can create new tools."""

    def __init__(self, llm):
        self.llm = llm
        self.tools: Dict[str, Callable] = {}
        self.tool_code: Dict[str, str] = {}

    def needs_new_tool(self, task: str) -> tuple[bool, str]:
        """Determine if a new tool is needed."""
        tools_desc = "\n".join([
            f"- {name}: {func.__doc__}"
            for name, func in self.tools.items()
        ]) or "No tools available"

        prompt = f"""Do you need a new tool to complete this task?

Task: {task}

Available tools:
{tools_desc}

If existing tools are sufficient, respond: NO

If a new tool is needed, respond:
YES: [description of tool needed]"""

        response = self.llm.generate(prompt)

        if response.startswith("YES:"):
            return True, response[4:].strip()
        return False, ""

    def create_tool(self, description: str) -> str:
        """Create a new tool based on description."""
        prompt = f"""Create a Python function for this tool.

Tool description: {description}

Requirements:
1. Single function with clear docstring
2. Use only standard library
3. Handle errors gracefully
4. Return a string result

```python
def tool_name(input_str: str) -> str:
    '''Tool description'''
    # Implementation
    return result
```

Provide the function code:"""

        response = self.llm.generate(prompt)

        # Extract code from response
        code = self._extract_code(response)

        # Safely execute to define the function
        tool_name = self._execute_and_register(code)

        return tool_name

    def _extract_code(self, response: str) -> str:
        """Extract Python code from response."""
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            return response[start:end].strip()
        return response.strip()

    def _execute_and_register(self, code: str) -> str:
        """Execute code and register the tool."""
        # Create a restricted namespace
        namespace = {"__builtins__": __builtins__}

        try:
            exec(code, namespace)

            # Find the function that was defined
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith("_"):
                    self.tools[name] = obj
                    self.tool_code[name] = code
                    return name
        except Exception as e:
            print(f"Error creating tool: {e}")

        return ""

    def run(self, task: str) -> str:
        """Run task, creating tools if needed."""
        # Check if new tool needed
        needs_tool, tool_desc = self.needs_new_tool(task)

        if needs_tool:
            print(f"Creating new tool: {tool_desc}")
            tool_name = self.create_tool(tool_desc)
            if tool_name:
                print(f"Created tool: {tool_name}")

        # Now solve the task with available tools
        tools_desc = "\n".join([
            f"- {name}: {func.__doc__}"
            for name, func in self.tools.items()
        ])

        prompt = f"""Solve this task using available tools.

Task: {task}

Available tools:
{tools_desc}

To use a tool, write: USE_TOOL(tool_name, "input")

Your solution:"""

        response = self.llm.generate(prompt)

        # Execute any tool calls
        return self._execute_tool_calls(response)

    def _execute_tool_calls(self, response: str) -> str:
        """Execute tool calls in the response."""
        import re

        pattern = r'USE_TOOL\((\w+),\s*"([^"]*)"\)'

        def replace_call(match):
            tool_name = match.group(1)
            tool_input = match.group(2)

            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](tool_input)
                    return f"[{tool_name} result: {result}]"
                except Exception as e:
                    return f"[{tool_name} error: {e}]"
            return f"[Unknown tool: {tool_name}]"

        return re.sub(pattern, replace_call, response)
```

### Did You Know?

In early 2024, researchers demonstrated "Voyager" - a Minecraft agent that could write its own skill code! When it needed to mine diamonds but didn't know how, it:
1. Explored the world to understand the problem
2. Wrote Python code for a mining skill
3. Tested the skill and debugged failures
4. Saved the skill to a library for future use

By the end, Voyager had created a library of 70+ reusable skills, all self-written!

---

## Part 5: Putting It All Together

### The Complete Autonomous Agent

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import json

@dataclass
class AutonomousAgentConfig:
    """Configuration for the autonomous agent."""
    max_iterations: int = 10
    enable_reflection: bool = True
    enable_tool_creation: bool = False
    memory_type: str = "hybrid"  # simple, vector, hybrid

class AutonomousAgent:
    """
    A complete autonomous agent with:
    - Hybrid memory (short-term, long-term, episodic)
    - Planning (Plan-and-Execute)
    - Self-reflection and correction
    - Tool creation (optional)
    """

    def __init__(
        self,
        llm,
        embedding_model,
        tools: Dict[str, Callable] = None,
        config: AutonomousAgentConfig = None
    ):
        self.llm = llm
        self.embedding_model = embedding_model
        self.tools = tools or {}
        self.config = config or AutonomousAgentConfig()

        # Initialize memory
        self.memory = HybridMemory(llm, embedding_model)

        # Initialize sub-systems
        self.planner = PlanAndExecuteAgent(llm, self.tools)
        self.reflector = ReflectiveAgent(llm) if config.enable_reflection else None
        self.tool_creator = ToolCreatingAgent(llm) if config.enable_tool_creation else None

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        print(f"\n{'='*60}")
        print(f"TASK: {task}")
        print(f"{'='*60}\n")

        # Step 1: Retrieve relevant context from memory
        context = self.memory.get_relevant_context(task)
        print(f"Retrieved {len(context)} characters of context")

        # Step 2: Check if we need new tools
        if self.tool_creator:
            needs_tool, tool_desc = self.tool_creator.needs_new_tool(task)
            if needs_tool:
                print(f"Creating new tool: {tool_desc}")
                tool_name = self.tool_creator.create_tool(tool_desc)
                if tool_name:
                    self.tools[tool_name] = self.tool_creator.tools[tool_name]

        # Step 3: Create and execute plan
        print("\nCreating plan...")
        plan = self.planner.create_plan(f"{context}\n\nTask: {task}")

        print(f"Plan has {len(plan.steps)} steps:")
        for step in plan.steps:
            print(f"  - {step.description}")

        print("\nExecuting plan...")
        result = self.planner.execute_plan(plan)

        # Step 4: Self-reflect and improve if enabled
        if self.reflector:
            print("\nReflecting on output...")
            result = self.reflector.generate_with_reflection(
                f"Task: {task}\n\nInitial result: {result}"
            )

        # Step 5: Store interaction in memory
        self.memory.add_interaction("user", task)
        self.memory.add_interaction("assistant", result)

        print(f"\n{'='*60}")
        print("COMPLETED")
        print(f"{'='*60}\n")

        return result

    def chat(self, message: str) -> str:
        """Chat interface for interactive use."""
        # Add to memory
        self.memory.add_interaction("user", message)

        # Get context
        context = self.memory.get_relevant_context(message)

        # Generate response
        prompt = f"""You are a helpful assistant with memory and planning capabilities.

{context}

User: {message}
Assistant:"""

        response = self.llm.generate(prompt)

        # Store response
        self.memory.add_interaction("assistant", response)

        return response
```

---

## The Economics of AI Agents

Before you deploy agents to production, you need to understand their economic reality. Agents are fundamentally different from traditional software in how they consume resources—and how they fail.

### The Token Multiplication Problem

A simple question like "What's the weather?" might cost 500 tokens with a regular chatbot. But give that same question to an agent with memory, planning, and tool use:

```
Query processing:        100 tokens
Memory retrieval:        300 tokens (embedding + search context)
Planning:                500 tokens (generating a plan)
Tool call #1 (search):   400 tokens (formatting + response parsing)
Tool call #2 (API):      300 tokens (weather API call)
Response synthesis:      400 tokens (combining results)
Memory storage:          200 tokens (summarizing for long-term)
────────────────────────────────────
Total:                 2,200 tokens (4.4x simple chatbot!)
```

At gpt-5 prices ($30/1M tokens), that's $0.066 per complex query vs $0.015 for a simple one. Scale to 100,000 queries/day, and the difference is **$5,100/day**.

> **Did You Know?** A 2024 analysis of enterprise agent deployments found that 73% of teams underestimated their token consumption by at least 3x in initial projections. The most common culprits: reflection loops (45%), verbose tool responses (30%), and redundant memory retrievals (25%). One fintech company's "simple" trading agent consumed $47,000 in API costs during its first month—they had budgeted $8,000.

### The Latency Tax

Agents are slow. Not because LLMs are slow, but because agents make multiple sequential LLM calls:

| Agent Action | Typical Latency |
|--------------|-----------------|
| Plan generation | 2-5 seconds |
| Each tool call | 1-3 seconds |
| Memory retrieval | 0.5-1 second |
| Reflection | 2-4 seconds |
| Response synthesis | 1-2 seconds |

A simple 3-step agent might take 10-20 seconds to respond. Users accustomed to sub-second chatbot responses will perceive this as broken.

**Solutions**:
1. **Streaming**: Show the agent's thinking process in real-time
2. **Async UX**: "I'm working on this, I'll notify you when done"
3. **Caching**: Pre-compute common tool calls and memory retrievals
4. **Parallel execution**: Run independent tool calls simultaneously

### When Agents Are Worth the Cost

Not every problem needs an agent. Here's a decision framework:

| Use Case | Agent ROI | Why |
|----------|-----------|-----|
| Complex research tasks | High | Saves hours of human time |
| Multi-step workflows | High | Replaces expensive human labor |
| Simple Q&A | Low | Regular chatbot is 4x cheaper |
| Real-time applications | Very Low | Latency makes it impractical |
| High-volume, simple tasks | Very Low | Costs explode without proportional value |

**The golden rule**: Agents should save more human time than they cost in compute. A $10 agent task that saves 30 minutes of developer time ($25+) is a win. A $10 agent task that a $0.50 chatbot query could handle is waste.

---

## Production Agent Horror Stories

Learning from others' failures is cheaper than making your own. Here are real production agent disasters and what they teach us.

### Horror Story 1: The Infinite Planner

**Company**: A Silicon Valley legal tech startup
**Agent**: Contract analysis with planning capabilities
**The Problem**: The agent was asked to analyze a complex merger agreement. It started planning:

```
Plan v1: Analyze 47 sections of the agreement
  → But wait, some sections reference other documents
Plan v2: First identify all referenced documents
  → But wait, I should understand the merger context first
Plan v3: Research the companies involved before analyzing
  → But wait, I need the financial context too
Plan v4: Start with SEC filings for both companies
  → But wait...
```

The agent spent 3 hours "planning" before a human noticed. Cost: $340 in API calls. Work done: zero.

**The Fix**: Implemented a "planning budget"—max 30 seconds of planning time, max 5 plan iterations. If still not ready, execute the simplest viable plan.

```python
class BudgetedPlanner:
    def __init__(self, max_time: float = 30.0, max_iterations: int = 5):
        self.max_time = max_time
        self.max_iterations = max_iterations

    def plan(self, task: str) -> Plan:
        start_time = time.time()
        iterations = 0

        while iterations < self.max_iterations:
            elapsed = time.time() - start_time
            if elapsed > self.max_time:
                # Time's up - use simplest plan
                return self._simple_plan(task)

            plan = self._generate_plan(task, iteration=iterations)
            if plan.is_executable():
                return plan

            iterations += 1

        # Max iterations - use what we have
        return self._simple_plan(task)
```

### Horror Story 2: The Memory Hoarder

**Company**: An e-commerce customer service platform
**Agent**: Personal shopping assistant with long-term memory
**The Problem**: The agent stored *everything* users said. After 6 months:

- Average memory size: 50,000+ entries per user
- Retrieval latency: 15+ seconds
- Memory costs: $0.50 per query just for retrieval
- Relevance: Terrible (too much noise)

One user had mentioned they were "looking for a birthday gift for mom" 200+ times over 6 months. The memory was full of duplicate near-identical entries.

**The Fix**: Implemented memory hygiene:

```python
class HygienicMemory:
    def store(self, content: str):
        # Check for duplicates
        if self._is_duplicate(content):
            return

        # Check importance threshold
        importance = self._calculate_importance(content)
        if importance < 0.3:
            return  # Not worth storing

        # Age out old memories
        self._decay_old_memories()

        # Store with TTL based on importance
        ttl = self._calculate_ttl(importance)
        self._store_with_ttl(content, ttl)

    def _is_duplicate(self, content: str) -> bool:
        # Check if similar content exists
        similar = self.retrieve(content, k=1)
        if similar and self._similarity(content, similar[0]) > 0.9:
            return True
        return False
```

### Horror Story 3: The Runaway Reflecter

**Company**: A code review automation startup
**Agent**: Code reviewer with self-correction capabilities
**The Problem**: The agent would review code, find issues, suggest fixes, then review its own suggestions, find issues with those, suggest meta-fixes, then review *those*...

One 50-line pull request generated:
- 847 tokens of original review
- 12,400 tokens of self-reflection
- 23 rounds of "improving" its feedback
- Final output: Incomprehensible meta-commentary about the nature of code quality

Cost: $2.30 for a review that should have cost $0.08.

**The Fix**: Reflection limits with diminishing returns detection:

```python
class ReflectionController:
    def __init__(self, max_rounds: int = 3, improvement_threshold: float = 0.1):
        self.max_rounds = max_rounds
        self.improvement_threshold = improvement_threshold

    def should_continue_reflecting(
        self,
        current_round: int,
        scores: List[float]
    ) -> bool:
        # Hard limit
        if current_round >= self.max_rounds:
            return False

        # Check for improvement
        if len(scores) >= 2:
            improvement = scores[-1] - scores[-2]
            if improvement < self.improvement_threshold:
                # Diminishing returns - stop reflecting
                return False

        return True
```

### Horror Story 4: The Tool Proliferation

**Company**: A DevOps automation platform
**Agent**: Infrastructure manager that could create its own tools
**The Problem**: The agent decided the best tool for monitoring CPU usage was a custom script. Then it needed a tool to parse the output. Then a tool to aggregate results. Then a tool to format alerts...

After 2 weeks:
- 147 custom tools created
- 89 were redundant or broken
- 23 conflicted with each other
- The agent spent 60% of its time managing its own tools

**The Fix**: Tool creation governance:

```python
class ToolGovernor:
    def __init__(self, existing_tools: List[Tool]):
        self.existing_tools = existing_tools
        self.created_tools = []

    def approve_tool_creation(self, proposed_tool: ToolSpec) -> bool:
        # Check if existing tool does the job
        for tool in self.existing_tools + self.created_tools:
            if self._tools_overlap(tool, proposed_tool) > 0.7:
                # Reject - use existing tool
                return False

        # Check tool count limit
        if len(self.created_tools) >= 10:
            # Force cleanup before creating more
            self._cleanup_unused_tools()

        # Check tool quality
        if not self._validate_tool_spec(proposed_tool):
            return False

        return True
```

---

## Measuring Agent Success

How do you know if your agent is actually working? Traditional software metrics don't capture agent-specific failure modes.

### The Agent Quality Framework

| Metric | What It Measures | Target |
|--------|------------------|--------|
| Task Completion Rate | % of tasks successfully finished | > 85% |
| First-Try Success | % completed without retries | > 70% |
| Token Efficiency | Tokens per successful task | < 3000 |
| Latency P50/P95 | Response time distribution | < 10s / < 30s |
| Hallucination Rate | % responses with false claims | < 5% |
| User Satisfaction | Post-task rating | > 4.0/5.0 |

### Failure Mode Analysis

Track *why* agents fail, not just *that* they fail:

```python
class AgentMetrics:
    def __init__(self):
        self.failures = {
            "planning_timeout": 0,
            "tool_error": 0,
            "memory_miss": 0,
            "context_overflow": 0,
            "hallucination": 0,
            "user_abort": 0,
            "unknown": 0,
        }

    def record_failure(self, task_id: str, failure_type: str, details: dict):
        self.failures[failure_type] += 1
        # Log for analysis
        self._log_failure(task_id, failure_type, details)

    def get_failure_distribution(self) -> dict:
        total = sum(self.failures.values())
        return {
            k: v / total if total > 0 else 0
            for k, v in self.failures.items()
        }
```

> **Did You Know?** OpenAI's internal agent evaluation framework tracks 37 different failure modes. Their research found that 68% of agent failures fall into just 5 categories: tool selection errors, context management failures, planning loops, output formatting issues, and hallucinated tool capabilities. Focusing improvement efforts on these 5 areas yields the highest ROI.

---

## Agents in the Wild: Production Case Studies

Let's examine how major companies deploy agents in production. These aren't hypotheticals—they're real systems processing millions of queries.

### Case Study 1: GitHub Copilot's Agent Mode

GitHub Copilot evolved from autocomplete to full agent capabilities in 2024. Here's how their architecture works:

**The Challenge**: Help developers with complex multi-file changes without losing context of the codebase.

**The Solution**: A hierarchical memory system:
1. **Immediate context**: Current file being edited (short-term)
2. **Project context**: File tree, imports, function signatures (structured memory)
3. **Semantic context**: Vector embeddings of similar code patterns (long-term)
4. **User context**: Previous interactions, coding style preferences (personalization)

The agent uses a **plan-act-observe** loop:
- **Plan**: "I need to add error handling to this function"
- **Act**: Generate code, find related files, check types
- **Observe**: Did the code compile? Did tests pass? User feedback?
- **Replan**: If observation shows issues, revise approach

**Key metrics**:
- 46% acceptance rate on multi-line suggestions
- 55% of developers report finishing tasks faster
- Average agent interaction: 4-6 tool calls

**Lesson**: Copilot succeeds because it focuses on augmentation, not replacement. The agent handles tedious multi-file coordination while the human makes decisions.

### Case Study 2: Intercom's Customer Service Fin

Intercom's Fin agent handles millions of customer service conversations monthly. It's one of the largest production agent deployments.

**The Challenge**: Answer customer questions accurately while maintaining brand voice across thousands of different businesses.

**The Solution**: RAG-first with behavioral fine-tuning
- **Knowledge**: Retrieves from each customer's help center (RAG)
- **Behavior**: Fine-tuned base model for customer service tone
- **Guardrails**: Extensive safety filters for sensitive topics

**Architecture pattern** (Supervisor):
```
User Message → Router → {
  "factual_question": RAG Pipeline,
  "complaint": Escalation Handler,
  "sales_inquiry": Sales Flow,
  "unclear": Clarification Agent
}
```

**Key metrics**:
- 50%+ of conversations fully resolved without human
- Average resolution time: 3 minutes (vs 12 minutes with human)
- Customer satisfaction within 5% of human agents

**Lesson**: Fin works because it knows when NOT to be an agent. Simple questions get simple answers (no planning overhead). Complex issues escalate to humans. The router is the hero.

### Case Study 3: Replit's Code Generation Agent

Replit Ghostwriter evolved into an agent that can build entire projects autonomously.

**The Challenge**: Generate, test, and iterate on code without human intervention.

**The Solution**: Tool-centric architecture with aggressive evaluation
- **Code generation**: LLM produces code
- **Execution**: Run code in sandboxed environment
- **Testing**: Automated test suite evaluation
- **Iteration**: Self-correction based on errors

**Innovation**: "Spec-driven development"
1. User provides high-level spec: "Build a todo app with React"
2. Agent generates detailed technical spec
3. Agent executes spec step-by-step
4. Each step is verified before proceeding

**Key metrics**:
- Can complete simple full-stack apps in ~10 minutes
- ~40% of generated code runs without modification
- 3-5 iteration cycles for typical project

**Lesson**: Replit's success comes from tight feedback loops. The agent doesn't just generate—it executes, observes, and corrects. Execution is verification.

### Case Study 4: Anthropic's Claude Code (Yes, Me!)

I can share insights about my own architecture as an agent:

**The Challenge**: Help developers with complex software engineering tasks while being trustworthy and safe.

**The Architecture**:
- **Memory**: Full conversation context (no explicit long-term storage)
- **Tools**: File read/write, bash commands, search, web access
- **Planning**: Implicit in reasoning (no formal plan data structure)
- **Reflection**: Continuous evaluation of approach

**Key design decisions**:
1. **Transparency**: Show thinking process, not just results
2. **Human-in-loop**: Always ask before destructive operations
3. **Confidence calibration**: Express uncertainty explicitly
4. **Task decomposition**: Break complex tasks into checkpoints

**What works**:
- Long context enables rich multi-file reasoning
- Tool confirmation prevents accidental damage
- Streaming responses feel interactive despite latency

**What's hard**:
- Very long conversations can lose focus
- Complex debugging requires human insight
- Novel problems without training examples struggle

**Lesson**: The most effective agent pattern might be "transparent co-pilot"—show your work, ask for confirmation, be honest about limits.

---

## The Future of Agents: What's Coming

Based on current research and trends, here's what advanced agents will look like in 2025-2026:

### Persistent Memory at Scale

Current limitation: Most agents forget between sessions.
Coming solution: Integrated long-term memory with automatic importance scoring, summarization, and retrieval. Your agent will remember that you prefer tabs over spaces, that your production servers run Ubuntu 22.04, and that you had a bug in the authentication module last month.

### Multi-Modal Agents

Current limitation: Most agents work with text only.
Coming solution: Agents that can see your screen, hear your voice, and interact with visual interfaces. "Look at this error message" will work by sharing your screen, not copying text.

### Specialized Agent Networks

Current limitation: Single agents trying to do everything.
Coming solution: Networks of specialized agents that hand off tasks. A coding agent might delegate documentation to a writing agent, testing to a QA agent, and deployment to a DevOps agent.

### Self-Improvement Pipelines

Current limitation: Agents don't learn from their mistakes (at inference time).
Coming solution: Agents that track success/failure patterns and adapt their strategies. If Tool A fails 80% of the time for a certain task type, the agent learns to prefer Tool B.

### Formal Verification Integration

Current limitation: No guarantees about agent behavior.
Coming solution: Integration with formal methods to verify agent actions before execution. "This database query will not delete production data" becomes provable, not hopeful.

The meta-trend: **Agents are becoming infrastructure**. Just as we don't think about TCP/IP when browsing the web, we'll stop thinking about "agents" and just have AI systems that remember, plan, and act. The abstractions will become invisible.

---

## Common Pitfalls

Understanding common failure modes helps you build more robust agents. Each pitfall includes real-world examples, detection strategies, and fixes.

### 1. Memory Overload

**Problem**: Storing too much in memory leads to slow retrieval and irrelevant context.

Think of it like a filing cabinet that's never cleaned. At first, you can find anything. But after 10 years of dumping every document into it, even finding your own birth certificate takes an hour of digging through expired coupons and old grocery lists.

**Real-world example**: A personal finance agent stored every transaction the user mentioned. After 18 months, its memory had 47,000 entries, retrieval took 8+ seconds, and 95% of retrieved "relevant" memories were noise like "I bought coffee."

**Detection**:
```python
def check_memory_health(memory):
    if memory.size() > 10000:
        print("WARNING: Memory size exceeds healthy threshold")
    if memory.average_retrieval_time() > 2.0:
        print("WARNING: Retrieval latency degraded")
    if memory.duplicate_ratio() > 0.3:
        print("WARNING: Too many duplicate memories")
```

**Solution**: Use importance scoring, TTL (time-to-live), and periodic cleanup. Set hard limits: "If memory exceeds 5,000 entries, compress oldest 1,000 into summaries."

### 2. Planning Paralysis

**Problem**: Agent spends too long planning, never executing.

Imagine asking someone to make you a sandwich, and they spend 2 hours researching bread varieties, optimal condiment ratios, and the structural engineering of sandwich stacking—without ever touching food. Planning paralysis happens when agents treat every task as requiring deep analysis.

**Detection signs**:
- Planning phase consistently takes longer than execution
- Plans keep growing in complexity without execution starting
- Agent generates "meta-plans" (plans about how to plan)

**Solution**: Set max planning time, use simpler plans for simple tasks. Implement "planning budgets" based on task complexity.

### 3. Infinite Reflection Loops

**Problem**: Agent keeps finding issues and never stops improving.

Self-improvement sounds great until your agent enters an infinite loop of "let me improve that improvement." This is perfectionism at scale—and it's expensive.

**Why it happens**: Reflection is genuinely useful, so agents (and their designers) tend to over-apply it. But each reflection round costs tokens, adds latency, and often shows diminishing returns after 2-3 iterations.

**Solution**: Set max iterations, use confidence thresholds. Track improvement delta—if the last three rounds improved quality by less than 5%, stop reflecting.

### 4. Tool Explosion

**Problem**: Agent creates too many tools, many redundant.

When agents can create their own tools, they often go overboard. "I need a tool to check if a number is even." "Now I need a tool to check if it's odd." "Now I need a tool to check if it's divisible by 3."

**Why it happens**: Tool creation feels productive. The agent gets positive feedback ("I successfully created a tool!") without evaluating whether the tool was necessary.

**Solution**: Check for similar tools before creating, implement tool cleanup. Set hard limits: "Maximum 20 custom tools. Creating a new one requires retiring an existing one."

### 5. Context Window Exhaustion

**Problem**: Memory + plan + conversation exceeds context limit.

This is the silent killer of agent sessions. Everything seems fine until—suddenly—the agent starts forgetting the beginning of the conversation, losing track of the plan, or hallucinating tool results it never received.

**Solution**: Aggressive summarization, hierarchical context loading. Monitor context usage and proactively compress when you hit 70% capacity.

---

## Testing Agents: A Practical Guide

Traditional software testing doesn't work for agents. You can't just write unit tests because agent behavior is non-deterministic and context-dependent. Here's how to actually test agents.

### The Three Levels of Agent Testing

**Level 1: Component Testing**
Test individual capabilities in isolation:
- Does the memory store and retrieve correctly?
- Do tools execute properly?
- Does the planner generate valid plans?

```python
def test_memory_retrieval():
    memory = VectorMemory(embedding_model)
    memory.store("User's name is Alice")
    memory.store("User works at TechCorp")
    memory.store("Today's weather is sunny")

    results = memory.retrieve("What is the user's name?", k=1)
    assert "Alice" in results[0].content

def test_tool_execution():
    calc_tool = CalculatorTool()
    result = calc_tool.execute("2 + 2")
    assert result == 4
```

**Level 2: Integration Testing**
Test how components work together:
- Does the agent use memory appropriately in context?
- Does it select the right tool for the job?
- Does planning integrate correctly with execution?

```python
def test_agent_uses_memory():
    agent = Agent(memory, tools, llm)

    agent.process("My name is Bob")
    response = agent.process("What's my name?")

    assert "Bob" in response

def test_agent_selects_correct_tool():
    agent = Agent(memory, [calculator, search, calendar], llm)

    response = agent.process("What is 47 * 23?")

    assert agent.last_tool_used == "calculator"
```

**Level 3: End-to-End Scenario Testing**
Test complete user scenarios:

```python
def test_research_agent_scenario():
    agent = ResearchAgent()

    # Multi-turn interaction
    agent.process("I'm researching quantum computing")
    agent.process("Find recent breakthroughs in error correction")
    response = agent.process("Summarize what you found")

    # Check quality metrics
    assert len(response) > 500  # Substantive response
    assert "error correction" in response.lower()
    assert agent.tools_used_count() >= 2  # Used search tools
```

### Evaluation Metrics for Agents

| Metric | How to Measure | Target |
|--------|----------------|--------|
| Task Completion | % tasks that reach successful end state | > 85% |
| Accuracy | Human evaluation of factual correctness | > 90% |
| Relevance | Are retrieved memories/tools appropriate? | > 80% |
| Efficiency | Tokens per successful task | < 5000 |
| Safety | % responses passing safety filters | 100% |
| Latency | Time from query to response | < 30s p95 |

### Regression Testing for Agents

The hardest part: ensuring improvements don't break existing functionality.

**Golden Dataset Approach**:
1. Create 100+ test scenarios with expected outcomes
2. Run all scenarios before every deployment
3. Any regression below 95% match rate blocks deployment

```python
def run_regression_suite(agent, golden_dataset):
    results = []
    for scenario in golden_dataset:
        response = agent.process(scenario.query)
        match_score = evaluate_similarity(response, scenario.expected)
        results.append({
            "scenario": scenario.id,
            "score": match_score,
            "passed": match_score > 0.8
        })

    pass_rate = sum(r["passed"] for r in results) / len(results)
    if pass_rate < 0.95:
        raise RegressionError(f"Pass rate {pass_rate} below threshold")
    return results
```

> **Did You Know?** Anthropic runs over 10,000 automated evaluations on Claude before each release. These tests range from simple fact-checking to complex multi-turn scenarios. The evaluation suite takes 4+ hours to run and catches ~30% of potential issues that human testers miss.

---

## Best Practices

These practices come from teams that have deployed agents at scale. Each lesson was learned through costly mistakes.

### Memory Design

**1. Start simple, add complexity only when needed**

Don't build a complex vector-episodic-summary memory system on day one. Start with a conversation buffer. When you see specific failures ("the agent forgot the user's name"), add targeted solutions. Complexity without purpose is just bugs waiting to happen.

**2. Importance scoring is essential at scale**

Not all information deserves long-term storage. "I bought coffee" shouldn't have the same weight as "I'm allergic to peanuts." Implement importance scoring from the start—retrofitting it is painful.

**3. Periodic consolidation prevents bloat**

Every week (or every 1000 memories), consolidate:
- Merge similar memories into summaries
- Delete low-importance items
- Refresh embeddings if your model upgraded

**4. Test retrieval quality regularly**

The best memory architecture is useless if retrieval fails. Run weekly tests: "Given these memories, does the agent retrieve the right ones for these queries?" Retrieval precision should stay above 80%.

### Planning

**1. Match planning complexity to task complexity**

A simple question shouldn't trigger a 5-step plan. Use heuristics: "If task is < 50 tokens, skip planning entirely." Reserve Tree of Thought for genuinely complex problems.

**2. Monitor which plans succeed vs fail**

Track plan outcomes. If "research → summarize → format" succeeds 90% but "format → research → summarize" fails 60%, learn from that. Over time, you'll discover patterns that work for your domain.

**3. Plans should be flexible, not contracts**

Allow replanning when execution reveals new information. If Step 2 fails, the agent shouldn't stubbornly retry—it should reconsider whether the plan itself was wrong.

**4. Limit planning depth for most tasks**

Plans deeper than 5 steps are usually wrong. Deep plans accumulate uncertainty: if each step has 90% success probability, a 10-step plan only succeeds 35% of the time (0.9^10). Keep it shallow.

### Multi-Agent Systems

**1. Each agent should have a distinct, narrow specialty**

"General-purpose agent" is a contradiction. Specialization enables excellence: a coding agent that only codes will outperform a "do-everything" agent at coding.

**2. Make agent handoffs explicit and traceable**

When Agent A passes work to Agent B, log: why, what context was transferred, what Agent B's mandate is. Invisible handoffs are debugging nightmares.

**3. Prevent infinite delegation loops**

Set hard limits: "Maximum 3 agent-to-agent transfers." Better yet, design architectures where loops are impossible (e.g., acyclic graphs).

**4. Log all inter-agent communication**

When something goes wrong in a multi-agent system, you'll need to trace exactly what happened. Log every message, every tool call, every decision. Storage is cheap; debugging time isn't.

### Self-Improvement

**1. Define "good enough" before you start**

Without quality thresholds, reflection never stops. "Accuracy > 85% AND confidence > 0.8" gives the agent clear termination criteria.

**2. Set hard limits on iterations**

Even with quality thresholds, set max iterations (3-5 for most tasks). Infinite loops are expensive.

**3. Save successful patterns for reuse**

If reflection discovers a better approach, store it. "For task type X, strategy Y works better than Z" becomes institutional knowledge the agent can use for future tasks.

**4. Keep humans in the loop for critical decisions**

Self-improvement is powerful but imperfect. For high-stakes outputs (financial advice, medical information, legal documents), require human review before finalizing.

---

## Further Reading

The field of AI agents is evolving rapidly. These resources represent the current state of the art, but check for newer papers and updates regularly.

### Foundational Papers

1. **"Generative Agents: Interactive Simulacra of Human Behavior"** (Park et al., Stanford, April 2023)
   - The Smallville paper that proved memory makes agents feel alive
   - Key contribution: Reflection and memory stream architecture
   - 2,000+ citations, foundational for modern agent design

2. **"Tree of Thoughts: Deliberate Problem Solving with Large Language Models"** (Yao et al., May 2023)
   - Structured reasoning through explicit tree search
   - Key contribution: Thought evaluation and backtracking
   - Essential reading for planning architectures

3. **"ReWOO: Decoupling Reasoning from Observations"** (Xu et al., 2023)
   - Separates planning from execution for efficiency
   - Key contribution: Reduced token usage by 60-80%
   - Important for cost-conscious agent design

4. **"AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"** (Microsoft, October 2023)
   - Framework for multi-agent collaboration
   - Key contribution: Conversation-based agent coordination
   - Production-tested at Microsoft scale

5. **"Voyager: An Open-Ended Embodied Agent"** (NVIDIA, May 2023)
   - Self-improving agent that learns new skills
   - Key contribution: Skill library and curriculum learning
   - Demonstration of truly autonomous learning

### Documentation and Frameworks

- **LangGraph**: The production-grade framework for stateful agents (https://langchain-ai.github.io/langgraph/)
- **AutoGen**: Microsoft's multi-agent conversation framework (https://microsoft.github.io/autogen/)
- **CrewAI**: Role-based agent collaboration (https://docs.crewai.com/)
- **Semantic Kernel**: Microsoft's agent orchestration for enterprise (https://learn.microsoft.com/semantic-kernel/)

### Recommended Tutorials

- Building agents with memory: LangChain official documentation
- Multi-agent orchestration: AutoGen example gallery
- Planning algorithms: LangGraph step-by-step tutorials
- Production deployment: Real-world case studies on agent observability

---

## Hands-On Exercises

These exercises progressively build your agent implementation skills. Each builds on concepts from the previous one.

### Exercise 1: Build a Hybrid Memory System

**Goal**: Create a memory system that combines short-term conversation buffer with long-term vector storage.

**What you'll build**:
- A conversation buffer that keeps the last 20 messages
- A vector store for facts extracted from conversations
- An importance scoring function that decides what to store long-term
- A retrieval function that combines recent context with relevant memories

**Steps**:
1. Implement the `ConversationBuffer` class from Part 1
2. Add the `VectorMemory` class with embedding storage
3. Create an `extract_facts()` function using an LLM to identify important information
4. Build a `get_context()` function that combines both memory types

**Success criteria**:
- Agent remembers user's name across conversation resets
- Agent retrieves relevant past context (not just recent messages)
- Memory doesn't grow unboundedly (importance filtering works)

**Estimated time**: 2-3 hours

### Exercise 2: Implement Plan-and-Execute Agent

**Goal**: Build an agent that decomposes complex tasks into executable plans.

**What you'll build**:
- A planning module that generates multi-step plans
- An execution module that runs each step with appropriate tools
- A replanning module that adjusts when steps fail

**Steps**:
1. Define 3-4 simple tools (calculator, web search, file reader)
2. Implement a `Planner` class that takes a task and outputs steps
3. Implement an `Executor` class that runs each step
4. Add failure handling: if a step fails, generate a new plan

**Success criteria**:
- Agent can complete: "Find the current weather in NYC and convert the temperature from F to C"
- Agent recovers when a tool fails (e.g., search returns no results)
- Plan steps are logged for debugging

**Estimated time**: 3-4 hours

### Exercise 3: Create a Multi-Agent Research Team

**Goal**: Build a team of specialized agents that collaborate on research tasks.

**What you'll build**:
- **Researcher Agent**: Takes a topic, searches for information, returns findings
- **Writer Agent**: Takes findings, produces a structured summary
- **Critic Agent**: Reviews the summary, suggests improvements
- **Supervisor**: Coordinates the team, handles handoffs

**Steps**:
1. Define clear responsibilities for each agent
2. Implement the supervisor's routing logic
3. Create handoff protocols (what context is passed between agents)
4. Add iteration limits to prevent infinite loops

**Success criteria**:
- Given "Research recent advances in battery technology", the team produces a well-structured summary
- Each agent's contribution is visible in logs
- The process completes in < 10 iterations

**Estimated time**: 4-5 hours

### Exercise 4: Add Self-Reflection and Improvement

**Goal**: Extend your agents with reflection capabilities that improve output quality.

**What you'll build**:
- A quality evaluation function that scores agent outputs
- A reflection module that identifies weaknesses
- An improvement loop that iterates until quality threshold is met
- Diminishing returns detection to prevent over-iteration

**Steps**:
1. Define quality metrics for your task (accuracy, completeness, clarity)
2. Implement `evaluate_output()` that returns a score
3. Implement `reflect_and_improve()` that takes feedback and produces better output
4. Add stopping conditions: max iterations AND improvement threshold

**Success criteria**:
- Initial output improves measurably after reflection
- Agent stops reflecting when quality is "good enough"
- Agent stops reflecting when improvements become marginal (< 5%)

**Estimated time**: 2-3 hours

### Bonus Challenge: Production-Ready Agent

Combine all four exercises into a production-grade agent system:
- Hybrid memory (Exercise 1)
- Plan-and-execute architecture (Exercise 2)
- Multi-agent collaboration (Exercise 3)
- Self-reflection (Exercise 4)
- Add: Logging, metrics, error recovery, cost tracking

**This is your capstone project for the module.**

**Estimated time**: 8-12 hours

---

## Deliverables

- [ ] **Agent Memory Demo**: Working hybrid memory system
- [ ] **Planning Agent**: Plan-and-execute implementation
- [ ] **Multi-Agent Team**: Supervisor + workers pattern
- [ ] **Autonomous Agent Framework**: Complete agent with all features

**Success Criteria**:
- Memory correctly retrieves relevant context
- Plans execute successfully
- Multi-agent collaboration produces better output than single agent
- Self-reflection improves output quality

---

## Next Steps

Move on to **Module 21: AI Agents in Production** to learn:
- Deploying agents to production
- Safety guardrails
- Monitoring and observability
- Cost control
- Failure handling

---

**You've discovered the Heureka Moment: Agents with memory and planning can solve problems they couldn't before!**

This is the foundation for building truly autonomous AI systems. In Module 21, you'll learn how to deploy these agents safely and reliably.

---

_Last updated: 2025-11-25_
_Status: Complete_
_Module 20: Advanced Agentic AI_
