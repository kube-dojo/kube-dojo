---
title: "Local Models for AI Coding"
slug: ai-ml-engineering/ai-native-development/module-1.2-local-models-for-ai-coding
sidebar:
  order: 203
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 3-4
# Or: How to Stop Paying OpenAI and Start Loving Your GPU

**Reading Time**: 3-4 hours
**Prerequisites**: Module 1.1 complete, 16GB+ RAM recommended (8GB minimum)

---

## The $600/Year Mistake That Changed Everything

**Austin, Texas. March 15, 2024. 8:43 PM.**

Marcus stared at his credit card statement in disbelief. Three hundred and twelve dollars. In a single month. All from OpenAI.

He'd been working on a side project—a code analysis tool—and had been iterating rapidly with gpt-5. Every experiment, every prompt tweak, every debugging session had added up. The tokens had accumulated silently while he was in the flow of coding.

"There has to be another way," he muttered, opening a new browser tab.

That night, Marcus discovered Ollama. By midnight, he had DeepSeek Coder running on his MacBook. The responses were slower, sure, but the quality was surprisingly good. And the cost? Zero. He ran the same prompts that had cost him fifty dollars the day before—completely free.

Two months later, Marcus's approach had evolved. He used local models for 80% of his work: code completion, test generation, documentation, routine refactoring. For the hard problems—complex architecture decisions, tricky bugs—he'd spend a few dollars on Claude. His monthly API bill dropped from $300 to $15.

> "Local models aren't a replacement for gpt-5 or Claude. They're more like a capable junior developer who handles the routine work so your expensive senior developer can focus on what matters. Once you think about it that way, the hybrid approach becomes obvious."
> — Marcus Chen, at PyCon 2025

That $600/year in savings? It funded Marcus's new GPU, which made his local models even faster. The cycle of value continued.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Understand the local vs API trade-offs for AI coding
- Install and run Ollama with coding-focused models
- Use local models with Aider for terminal-based AI coding
- Configure Continue.dev to use local models in VS Code
- Implement cost-optimization strategies (local + API hybrid)
- Know which local models excel at which coding tasks
- Troubleshoot common local model issues

**Why this matters**: Running models locally means **$0/month** AI coding, complete privacy, and offline capability. Perfect for learning, experimentation, and cost-conscious development.

---

## The Local Models Revolution: Why This Changes Everything

### The Problem Everyone Faces

**Without local models** (API-only approach):

```
Week 1: Sign up for Claude API
Week 2: $10 in API costs (moderate coding)
Week 3: $15 (got ambitious with refactoring)
Week 4: $25 (trying different models, debugging)

Monthly total: $50-100 in API costs
Annual: $600-1,200

Plus:
- Need internet connection always
- Code sent to external servers
- Rate limits during heavy use
- Billing surprises
```

**With local models** (hybrid approach):

```
Week 1: Install Ollama (free), download DeepSeek Coder (free)
Week 2: Use local for 80% of tasks, API for complex 20%
Week 3: API costs: $3 (only used for hard problems)
Week 4: API costs: $2

Monthly total: $5-10 in API costs
Annual: $60-120 (10× cheaper!)

Plus:
- Works offline
- Code stays on your machine
- No rate limits
- Predictable costs
```

**The difference**: $600-1,200/year vs $60-120/year. **10× cost reduction!**

---

## Did You Know? The Open Source AI Boom

**2023**: OpenAI dominates, local models struggle to compete

**2024**: Meta releases Llama 4 - changes everything
- Open source models catch up dramatically
- DeepSeek Coder beats GPT-3.5 on coding tasks
- Qwen 2.5-Coder rivals commercial models

**2025**: Local models are now **viable alternatives**
- DeepSeek R1 competes with o1 on reasoning
- Qwen 2.5-Coder:32B rivals gpt-5 on code
- Can run 7B models on MacBook Air!

**The trend**: Gap between local and API models shrinking fast. By 2026, local models may match gpt-5 quality.

---

## Introduction: Understanding Local Models

### What Are Local Models?

**The Personality**: Local models are **self-sufficient coding assistants** - they live on your machine, not in the cloud.

Think of local models like having a reference library in your home versus using the public library downtown. The public library (API models) has more books, expert librarians, and the latest publications—but you have to drive there, pay parking, and work within their hours. Your home library (local models) has fewer books, but it's always available, completely private, and costs nothing after the initial purchase.

**Three types of AI model deployment**:

```
1. API Models (ChatGPT, Claude, Gemini)
   ├─ Run on company servers
   ├─ Access via internet
   ├─ Pay per request
   └─ Example: claude-4.6-sonnet-20241022

2. Local Models (Qwen, DeepSeek, Llama)
   ├─ Downloaded to your machine
   ├─ Run on your CPU/GPU
   ├─ One-time download cost
   └─ Example: qwen2.5-coder:7b

3. Hybrid (Mix of both)
   ├─ Local for simple/repetitive tasks
   ├─ API for complex reasoning
   └─ Best of both worlds
```

**Scale analogy**:
- API models = Cloud computing (AWS, Google Cloud)
- Local models = Your own server
- Hybrid = Edge computing + cloud

**Process analogy**:
- API models = Calling a consultant (pay per hour, expert knowledge)
- Local models = Hiring an intern (one-time training, available 24/7)
- Hybrid = Small team with occasional expert advice

---

##  Local vs API: When to Use Each

### Use Local Models When:

**1. Cost is a concern** ($0/month vs $50-100/month)
```python
# Scenario: Learning Python, writing 100+ functions/week
# API cost: $20-40/month (Claude/gpt-5)
# Local cost: $0/month (after download)
# Annual savings: $240-480
```

**2. Privacy matters** (proprietary code)
```python
# Scenario: Working on closed-source company project
# API: Code sent to Anthropic/OpenAI servers 
# Local: Code never leaves your machine 
```

**3. Offline work needed**
```python
# Scenario: Coding on airplane, no WiFi
# API: Cannot work 
# Local: Full functionality 
```

**4. Repetitive tasks** (boilerplate, tests, docs)
```python
# Scenario: Generating 50 unit tests
# API: $2-5 in costs
# Local: Free, unlimited
```

**5. Learning and experimentation**
```python
# Scenario: Trying different prompts, models
# API: Costs add up with experimentation
# Local: Experiment freely
```

---

### Use API Models When:

**1. Maximum quality needed**
```python
# Scenario: Complex algorithm design, architecture decisions
# API: Claude Opus 4, gpt-5 (best reasoning)
# Local: Good, but not as strong
```

**2. Latest capabilities required**
```python
# Scenario: Using newest features (vision, long context, etc.)
# API: Always cutting-edge
# Local: Lags behind by 6-12 months
```

**3. Very large context windows**
```python
# Scenario: Analyzing entire 50K line codebase
# API: Claude (200K tokens), Gemini (2M tokens)
# Local: Most models max at 8-32K tokens
```

**4. Zero setup time**
```python
# Scenario: Need to start coding NOW
# API: Sign up, get key, start (5 minutes)
# Local: Download (30min-2hrs depending on model size)
```

---

### The Decision Matrix

| Factor | Local Models | API Models | Winner |
|--------|-------------|------------|--------|
| **Cost** | $0/month | $20-100/month |  Local |
| **Privacy** | Code stays local | Sent to servers |  Local |
| **Offline** | Works offline | Needs internet |  Local |
| **Quality** | Good | Excellent |  API |
| **Speed** | Slower (CPU) | Very fast |  API |
| **Context** | 8-32K tokens | 200K-2M tokens |  API |
| **Latest features** | 6-12mo lag | Cutting-edge |  API |
| **Setup** | 30min-2hrs | 5 minutes |  API |

**Verdict**: **Use both!** Local for most work, API for complex tasks.

Think of the hybrid approach like a restaurant kitchen. You don't fly in a Michelin-starred chef (expensive API model) to chop onions and wash dishes—that's what your reliable prep cooks (local models) are for. But when it's time to create the signature dish that brings customers back, you want the master chef's expertise. The kitchen runs best when everyone works together, each handling what they do best.

---

##  The Local Model Landscape (2025)

### Category 1: **Best for Coding Quality** ⭐⭐⭐

#### **DeepSeek Coder V2** (China - DeepSeek AI)

**What it is**: Specialized coding model that rivals gpt-5 on benchmarks

**The Good**:
- **Best code quality** among local models
- Supports 338 programming languages
- Strong at debugging and refactoring
- Reasoning capabilities (R1 model)
- 16B version runs on 16GB RAM

**The Not-So-Good**:
- ️ Newer, less community support
- ️ 236B version needs GPU
- ️ Less documentation than Llama

**Sizes available**:
```bash
ollama pull deepseek-coder-v2:16b   # Recommended
ollama pull deepseek-coder-v2:236b  # Needs GPU
ollama pull deepseek-r1:7b          # Reasoning model
ollama pull deepseek-r1:14b
```

**Best for**: Complex algorithms, code review, refactoring
**Benchmarks**: Beats GPT-3.5-Turbo, rivals gpt-5 on HumanEval

> ** Did You Know? The DeepSeek Story**
>
> DeepSeek is a Chinese AI company that shocked Silicon Valley in 2024-2025. While American AI labs spent billions on massive GPU clusters, DeepSeek's small team in Hangzhou achieved comparable results with a fraction of the compute budget.
>
> Their secret? **Engineering efficiency over brute force**. DeepSeek R1 (their reasoning model) was trained with novel techniques that reduced compute costs by 90% compared to OpenAI's o1.
>
> The result: A model you can run locally that competes with $200/month API subscriptions. DeepSeek proved that AI progress isn't just about throwing money at problems - clever engineering matters more.
>
> **Fun fact**: When DeepSeek R1 was released in January 2025, Nvidia's stock dropped 17% ($600B in market cap) in one day. Investors realized the AI hardware arms race might be less important than they thought.

---

#### **Qwen 2.5-Coder** (China - Alibaba)

**What it is**: Latest coding model from Alibaba, excellent quality

**The Good**:
- **Top-tier code generation**
- Fast inference
- Great at multiple languages (especially Asian languages)
- Strong reasoning (QwQ model)
- 7B version very efficient

**The Not-So-Good**:
- ️ Less known in Western dev community
- ️ Some English docs still being translated

**Sizes available**:
```bash
ollama pull qwen2.5-coder:7b    # Best balance
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:32b   # High quality
ollama pull qwq:32b             # Reasoning
```

**Best for**: Code generation, multi-language projects, daily coding
**Benchmarks**: Often beats CodeLlama, competitive with GPT-3.5

---

### Category 2: **Most Popular & Mature** ⭐

#### **CodeLlama** (USA - Meta)

**What it is**: Meta's specialized coding version of Llama 4

**The Good**:
- Huge community, best documentation
- Well-tested and stable
- Great Python support
- Multiple size options
- Excellent code completion

**The Not-So-Good**:
- ️ Being overtaken by newer models (DeepSeek, Qwen)
- ️ Not as strong at reasoning

**Sizes available**:
```bash
ollama pull codellama:7b
ollama pull codellama:13b
ollama pull codellama:34b
```

**Best for**: Beginners, Python development, stable choice
**Benchmarks**: Solid, but DeepSeek and Qwen now beat it

---

### Category 3: **Fastest Inference** 

#### **Codestral** (France - Mistral AI)

**What it is**: Mistral's coding-specialized model

**The Good**:
- **Very fast** inference
- 22B params, good quality
- Excellent for autocomplete
- Strong European backing

**The Not-So-Good**:
- ️ 22B size needs more RAM
- ️ Not as widely used as Llama

**Sizes available**:
```bash
ollama pull codestral:22b
```

**Best for**: Real-time autocomplete, fast iteration
**Benchmarks**: Competitive with CodeLlama 34B

---

### Category 4: **Smallest & Most Efficient** 

#### **Phi-3.5** (USA - Microsoft)

**What it is**: Microsoft's tiny but capable model

**The Good**:
- **Only 3.8B params** - runs anywhere!
- Surprisingly good for size
- Great for learning
- Fast on CPU

**The Not-So-Good**:
- ️ Limited capabilities vs larger models
- ️ Small context window
- ️ Not suitable for complex tasks

**Sizes available**:
```bash
ollama pull phi3:3.8b
ollama pull phi3.5:3.8b
```

**Best for**: Low-resource machines, learning, quick tasks
**Benchmarks**: Punches above its weight class

---

### Category 5: **Google's Offering**

#### **CodeGemma** (USA - Google)

**What it is**: Google's open-source coding model

**The Good**:
- Google quality
- Good Python support
- Active development

**The Not-So-Good**:
- ️ Less popular than Llama/Qwen
- ️ Smaller community

**Sizes available**:
```bash
ollama pull codegemma:7b
ollama pull gemma2:9b
ollama pull gemma2:27b
```

**Best for**: Google ecosystem, Python-focused work

---

## Comparison Table: Which Model Should You Use?

| Model | Size | RAM Needed | Code Quality | Speed | Best Use Case |
|-------|------|------------|--------------|-------|---------------|
| **DeepSeek Coder V2** | 16B | 16GB | ⭐⭐⭐⭐⭐ | Medium | Complex coding, refactoring |
| **Qwen 2.5-Coder** | 7B | 8GB | ⭐⭐⭐⭐⭐ | Fast | Daily driver, general coding |
| **Qwen 2.5-Coder** | 32B | 32GB | ⭐⭐⭐⭐⭐ | Medium | High-quality code gen |
| **CodeLlama** | 13B | 16GB | ⭐⭐⭐⭐ | Fast | Python, stable choice |
| **Codestral** | 22B | 24GB | ⭐⭐⭐⭐ | Very Fast | Autocomplete, real-time |
| **CodeGemma** | 7B | 8GB | ⭐⭐⭐ | Fast | Python-focused |
| **Phi-3.5** | 3.8B | 4GB | ⭐⭐⭐ | Very Fast | Learning, low-resource |

---

## Recommendations by Your Situation

### **You Have: MacBook with 16GB RAM** (Most Common)
```bash
# Your best setup:
ollama pull qwen2.5-coder:7b          # Daily driver (uses ~6GB)
ollama pull deepseek-coder-v2:16b     # Heavy lifting (uses ~14GB)
```
**Why**: Qwen 7B for fast tasks, DeepSeek 16B when you need quality

---

### **You Have: MacBook with 8GB RAM**
```bash
# Your best setup:
ollama pull qwen2.5-coder:7b          # Main model
ollama pull phi3.5:3.8b               # Quick tasks
```
**Why**: Stay under 8GB, both are excellent for their size

---

### **You Have: Desktop with 32GB+ RAM (or GPU)**
```bash
# Go big!
ollama pull qwen2.5-coder:32b         # Highest quality
ollama pull deepseek-coder-v2:236b    # If you have GPU
```
**Why**: Use the full power available

---

### **You Have: Budget Laptop (4GB RAM)**
```bash
# Lightweight only:
ollama pull phi3.5:3.8b
```
**Why**: Only model that will run smoothly on 4GB

---

## Did You Know? The Apple Silicon Revolution

### Why Your MacBook Can Run AI Now

Before 2020, running AI models locally was painful. You needed expensive Nvidia GPUs, separate RAM for graphics, and complex CUDA drivers. Most developers couldn't do it.

Then Apple released the **M1 chip** in November 2020. Everything changed.

**The breakthrough**: Apple's "Unified Memory Architecture" means the CPU and GPU share the same fast memory. For AI inference, this is perfect - no copying data back and forth between CPU and GPU RAM.

**The numbers**:
- M1 MacBook Air (8GB): Can run 7B parameter models
- M1 Pro (16GB): Can run 14B parameter models comfortably
- M1 Max (32GB): Can run 32B+ parameter models
- M1 Ultra (64-128GB): Can run models that normally need datacenter GPUs

**The surprise**: A $999 MacBook Air can now run models that would have cost $10,000+ in GPU hardware just 3 years ago.

**Why this matters for you**: If you have any Mac with M-series chip (M1, M2, M3, M4), you can run production-quality AI models locally. No cloud costs, complete privacy, works offline. This was science fiction in 2019.

---

## ️ Hands-On: Installing Ollama

### What is Ollama?

**The Personality**: Ollama is your **model manager** - like Docker for AI models.

Think of Ollama like a video game console for AI models. Just like how a PlayStation lets you download, manage, and play games without worrying about hardware compatibility or installation headaches, Ollama handles all the complexity of running AI models. You just say "I want this model," and Ollama figures out the memory management, optimization, and APIs automatically.

**What it does**:
- Downloads and manages models
- Runs models locally
- Provides simple API
- Works with coding tools (Aider, Continue.dev)

> ** Did You Know?**
>
> Ollama was created by Jeffrey Morgan and Michael Chiang in 2023. They were frustrated that running local AI models required deep knowledge of CUDA drivers, quantization formats, and memory optimization. Their goal was simple: make local models as easy as `docker run`. Within a year, Ollama had over 500,000 users and became the de facto standard for running local models. The name "Ollama" is a playful take on "llama" (Meta's model family) combined with the idea of models being "portable" (O-llama, like a friendly llama you can carry around).

---

### Installation (macOS)

```bash
# Method 1: Homebrew (recommended)
brew install ollama

# Method 2: Official installer
# Download from https://ollama.com/download

# Verify installation
ollama --version
# Output: ollama version 0.x.x
```

---

### Installation (Linux)

```bash
# Single command install
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version

# Start service (if needed)
sudo systemctl start ollama
sudo systemctl enable ollama
```

---

### Installation (Windows)

```powershell
# Download installer from https://ollama.com/download
# Run OllamaSetup.exe

# Verify in PowerShell
ollama --version
```

---

### Your First Model

```bash
# Pull a small model to test
ollama pull qwen2.5-coder:7b

# This downloads ~4GB, takes 5-15 minutes depending on connection
# Output:
# pulling manifest
# pulling 8934d96d3f08... 100% ▕████████████▏ 4.7 GB
# pulling 8c17c2ebb0ea... 100% ▕████████████▏ 7.0 KB
# pulling 590d74a5569b... 100% ▕████████████▏ 6.0 KB
# pulling 56bb8bd477a5... 100% ▕████████████▏  96 B
# pulling 1d21db061cdd... 100% ▕████████████▏ 485 B
# success
```

---

### Test Your Model

```bash
# Interactive mode
ollama run qwen2.5-coder:7b

# You'll see a prompt:
# >>>

# Try it:
>>> Write a Python function to reverse a string

# Model generates code!
# Exit with: /bye
```

---

### List Your Models

```bash
# See what models you have
ollama list

# Output:
# NAME                    ID              SIZE      MODIFIED
# qwen2.5-coder:7b        abc123          4.7 GB    2 minutes ago
```

---

### Remove Models (Free Up Space)

```bash
# Remove a model
ollama rm codellama:13b

# Check space saved
ollama list
```

---

## Hands-On: Using Local Models with Aider

### What is Aider?

**Aider** = AI pair programmer in your terminal
- Edits multiple files
- Git integration
- Works with any LLM (API or local!)

---

### Installing Aider

```bash
# Install via pip
pip install aider-chat

# Or in your venv
source venv/bin/activate
pip install aider-chat

# Verify
aider --version
```

---

### Using Aider with Local Models

```bash
# Basic usage with Qwen
aider --model ollama/qwen2.5-coder:7b

# With specific files
aider --model ollama/qwen2.5-coder:7b myfile.py

# With DeepSeek for complex work
aider --model ollama/deepseek-coder-v2:16b
```

---

### Example Session

```bash
# Start Aider with local model
aider --model ollama/qwen2.5-coder:7b test.py

# Aider opens, you see:
# Aider v0.x.x
# Model: ollama/qwen2.5-coder:7b
# Git repo: /path/to/project
# Added test.py to the chat

# Now ask it to code:
> Create a Python function to calculate fibonacci numbers with memoization

# Aider generates code:
# Applied edit to test.py
# Commit changes? (Y)es/(N)o/(D)on't ask again [Yes]: y
# Commit message: Add fibonacci function with memoization

# Success! Code written, tests added, committed to git
```

---

### Aider Configuration File

Create `~/.aider.conf.yml`:

```yaml
# Use local model by default
model: ollama/qwen2.5-coder:7b

# Auto-commit changes
auto-commits: true

# Show diffs
show-diffs: true

# Prettier output
pretty: true
```

Now just run:
```bash
aider  # Uses config automatically
```

---

### Cost Comparison: Aider Local vs API

**Scenario**: Refactor 10 files (500 lines each)

**With Claude API**:
```
Input: ~100K tokens
Output: ~50K tokens
Cost: ~$5-8 per refactoring session
Monthly (4 sessions): $20-32
```

**With Local Qwen**:
```
Input: Unlimited
Output: Unlimited
Cost: $0
Monthly (unlimited sessions): $0
```

**Savings**: $20-32/month = $240-384/year!

---

## Hands-On: Using Local Models with Continue.dev

### What is Continue.dev?

**Continue.dev** = VS Code extension for AI coding
- Like Copilot, but works with ANY model
- Supports local models!
- Open source

---

### Installing Continue.dev

1. Open VS Code
2. Extensions (Cmd/Ctrl+Shift+X)
3. Search "Continue"
4. Install "Continue - Codestral, Claude, and more"

---

### Configuring for Local Models

1. Open Continue settings (Cmd/Ctrl+Shift+J)
2. Click gear icon ️
3. Edit `config.json`:

```json
{
  "models": [
    {
      "title": "Qwen 2.5 Coder (Local)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "DeepSeek Coder (Local)",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen Autocomplete",
    "provider": "ollama",
    "model": "qwen2.5-coder:7b"
  }
}
```

4. Save and reload VS Code

---

### Using Continue with Local Models

**Tab Autocomplete**:
- Start typing code
- Continue suggests completions
- Press Tab to accept
- All running locally!

**Chat**:
- Open Continue sidebar (Cmd/Ctrl+Shift+J)
- Select "Qwen 2.5 Coder (Local)"
- Ask questions:
  ```
  You: Refactor this function to use async/await

  Qwen: [Generates refactored code]
  ```

**Inline Editing**:
- Highlight code
- Cmd/Ctrl+I
- Describe change: "Add error handling"
- Continue edits inline!

---

### Multi-Model Setup (Best Practice)

Use different models for different tasks:

```json
{
  "models": [
    {
      "title": "Quick (Phi-3.5)",
      "provider": "ollama",
      "model": "phi3.5:3.8b",
      "description": "Fast for simple tasks"
    },
    {
      "title": "Balanced (Qwen)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "description": "Daily driver"
    },
    {
      "title": "Quality (DeepSeek)",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "description": "Complex refactoring"
    },
    {
      "title": "API (Claude)",
      "provider": "anthropic",
      "model": "claude-4.6-sonnet-20241022",
      "apiKey": "YOUR_KEY",
      "description": "When you need the best"
    }
  ]
}
```

Switch models based on task complexity!

---

##  Cost Optimization: Hybrid Strategy

### The 80/20 Rule

**80% of tasks**: Simple, use local models (FREE)
- Code completion
- Boilerplate generation
- Unit tests
- Documentation
- Simple refactoring

**20% of tasks**: Complex, use API (PAY)
- Architecture design
- Complex algorithms
- Debugging subtle bugs
- Code review of large changes

**Result**: 80% cost reduction!

---

### Your Hybrid Setup (Recommended)

**For daily coding**:
```bash
# VS Code + Continue.dev
# Autocomplete: Qwen 2.5-Coder:7b (local)
# Chat: Mix of local (simple) + Gemini Flash (complex, your free tier)
```

**For terminal work**:
```bash
# Aider with local
aider --model ollama/qwen2.5-coder:7b

# When stuck, switch to API
aider --model gemini/gemini-2.5-flash
```

**Monthly cost**:
- Local models: $0
- Gemini Flash (free tier): $0
- Overflow to paid API: $3-5/month

**Total**: ~$5/month vs $50-100 API-only!

---

## Performance Benchmarks

### Code Generation Quality

**HumanEval Benchmark** (Python coding tasks):

| Model | Score | Cost/1M tokens | Speed |
|-------|-------|----------------|-------|
| gpt-5 | 67% | $30 | Fast |
| Claude 3.5 Sonnet | 64% | $15 | Fast |
| DeepSeek Coder V2 16B | 62% | **$0** | Medium |
| Qwen 2.5-Coder 32B | 61% | **$0** | Medium |
| CodeLlama 34B | 54% | **$0** | Medium |
| Gemini Flash 2.5 | 71% | **$0** (free tier) | Very Fast |

**Insight**: Local models are 90-95% as good as API, at 0% of the cost!

---

### Speed Comparison (MacBook Pro 16GB)

**Task**: Generate 100-line Python function

| Model | Time | Quality |
|-------|------|---------|
| gpt-5 (API) | 2-3 sec | ⭐⭐⭐⭐⭐ |
| Qwen 2.5-Coder:7b (local) | 8-12 sec | ⭐⭐⭐⭐ |
| DeepSeek V2:16b (local) | 15-20 sec | ⭐⭐⭐⭐⭐ |
| Phi-3.5:3.8b (local) | 5-8 sec | ⭐⭐⭐ |

**Trade-off**: Local is 3-6× slower, but free and private!

---

## Common Mistakes: Learn From Others' Pain

### Mistake #1: "Downloaded 236B Model, My Mac is Frozen"

**Symptom**: Downloaded DeepSeek 236B on 16GB MacBook, system unresponsive

**Why It's Bad**:
- 236B model needs 200+ GB RAM or GPU
- CPU-only inference would take minutes per response
- System swaps to disk, grinds to halt

**The Fix**:
```bash
# Remove the huge model
ollama rm deepseek-coder-v2:236b

# Use appropriately-sized model
ollama pull deepseek-coder-v2:16b  # Much better!
```

**Rule**: Match model size to your RAM (model params × 2 = GB needed)

---

### Mistake #2: "Local Model Gives Worse Code Than I Expected"

**Symptom**: Qwen 7B generates buggy code, frustrated

**Why It's Bad**:
- Used 7B model for complex architecture task
- 7B models are good, but not great at complex reasoning

**The Fix**:
```bash
# For complex tasks, use bigger model OR API
aider --model ollama/deepseek-coder-v2:16b  # Better
# or
aider --model gemini/gemini-2.5-flash       # Your free tier
```

**Rule**: Match model capability to task complexity!

---

### Mistake #3: "Ollama Using 100% CPU, Laptop is Hot"

**Symptom**: Fan running loud, laptop hot during code generation

**Why It's Normal**:
- Local models use CPU/GPU intensively
- This is expected behavior
- Not harmful unless sustained for hours

**The Fix** (if bothered):
```bash
# Use smaller model for less intensive work
ollama pull phi3.5:3.8b

# Or use API for complex stuff
# Save local for offline/simple tasks
```

**Rule**: Local models trade electricity for cost savings!

---

### Mistake #4: "Continue.dev Not Finding My Local Model"

**Symptom**: Set up Ollama, but Continue.dev says "model not found"

**Diagnosis**:
```bash
# Check Ollama is running
ollama list

# If empty or error, Ollama service isn't running
```

**The Fix**:
```bash
# Start Ollama service (macOS/Linux)
ollama serve

# Or on Linux:
sudo systemctl start ollama

# Then in Continue config:
# Make sure apiBase is: http://localhost:11434
```

**Prevention**: Always verify `ollama list` works before configuring tools!

---

## Best Practices for Local Models

### 1. **Start Small, Scale Up**

**Why**: Don't download every model at once

```bash
# BAD (downloading everything)
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:32b
ollama pull deepseek-coder-v2:16b
ollama pull codellama:34b
# (Uses 80+ GB disk space!)

# GOOD (start with one)
ollama pull qwen2.5-coder:7b
# Test it for a week
# If you need more quality, then add:
ollama pull deepseek-coder-v2:16b
```

**Benefit**: Save disk space, learn what works for you

---

### 2. **Use Local for Iteration, API for Innovation**

**Pattern**:
```python
# Scenario: Building new feature

# Step 1: Architecture (use API - needs reasoning)
aider --model gemini/gemini-2.5-flash
> "Design class structure for user authentication system"

# Step 2: Implementation (use local - repetitive)
aider --model ollama/qwen2.5-coder:7b
> "Implement the User class with methods we designed"

# Step 3: Tests (use local - boilerplate)
> "Generate unit tests for all User methods"

# Step 4: Refactoring (use API if complex, local if simple)
aider --model ollama/deepseek-coder-v2:16b
> "Refactor for better error handling"
```

**Benefit**: Best quality where it matters, zero cost where it doesn't

---

### 3. **Create Model Aliases for Workflows**

**Setup** (in `~/.bashrc` or `~/.zshrc`):
```bash
# Quick coding tasks
alias aider-quick="aider --model ollama/phi3.5:3.8b"

# Daily driver
alias aider-local="aider --model ollama/qwen2.5-coder:7b"

# High quality
alias aider-quality="aider --model ollama/deepseek-coder-v2:16b"

# API fallback (your Gemini free tier)
alias aider-api="aider --model gemini/gemini-2.5-flash"
```

**Usage**:
```bash
# Simple task
aider-quick add_tests.py

# Normal coding
aider-local main.py

# Complex refactoring
aider-quality --architect
```

**Benefit**: Fast workflow switching!

---

### 4. **Monitor Your Costs (Even $0 Has Opportunity Cost)**

**Track usage**:
```bash
# Create usage log
echo "$(date): Used DeepSeek 16B for refactoring - 5 min CPU time" >> ~/ai_usage.log

# Weekly review
cat ~/ai_usage.log | grep "$(date +%Y-%m)"
```

**Calculate savings**:
```python
# If you used API instead
api_cost_per_1m_tokens = 3  # Claude Haiku
estimated_tokens = 50_000   # Your usage
monthly_savings = (estimated_tokens / 1_000_000) * api_cost_per_1m_tokens * 30
print(f"Saved ${monthly_savings:.2f} this month by using local models")
```

**Benefit**: Quantify your cost optimization!

---

## Deep Dive (Optional): How Local Models Work

**For the curious**: What happens when you run `ollama run qwen2.5-coder:7b`?

### The Technical Stack

**1. Model Download**:
```
Ollama downloads:
├─ Model weights (4.7 GB) - the "brain"
├─ Tokenizer (7 KB) - converts text to numbers
├─ Config (6 KB) - model parameters
└─ Prompt template (485 B) - how to format inputs
```

**2. Loading into RAM**:
```
7B model × 2 bytes/param = 14 GB quantized
Actually uses: 4-6 GB (thanks to quantization!)
```

**3. Inference**:
```
Your prompt → Tokenizer → Model → Detokenizer → Code output

Example:
"Write Python function" → [1234, 5678, 9012] → Transformer layers → [4567, 8901, 2345] → "def fibonacci(n):"
```

**4. Quantization Magic**:
```
Full precision: 16-bit floats = 14 GB
Quantized (Q4): 4-bit ints = 3.5 GB
Quantized (Q8): 8-bit ints = 7 GB

Ollama uses Q4 by default - 4× memory reduction!
```

**5. CPU vs GPU**:
```
CPU inference: Uses all cores, ~10-20 tokens/sec
GPU inference (CUDA): Uses GPU, ~50-100 tokens/sec
Apple Silicon (Metal): Uses GPU, ~30-60 tokens/sec
```

---

## Try This: Interactive Challenges

### Challenge 1: The Model Comparison Test

**Goal**: See which model is best for YOUR coding style

**Task**: Generate the same function with 3 different models, compare

```bash
# Create test file
cat > compare_models.md << 'EOF'
# Model Comparison
Task: Write a Python function to find prime numbers up to N using Sieve of Eratosthenes

## Model 1: Qwen 2.5-Coder:7b
[Paste output here]

## Model 2: DeepSeek Coder V2:16b
[Paste output here]

## Model 3: CodeLlama:13b
[Paste output here]

## Winner: [Your choice]
Why: [Your reasoning]
EOF

# Test each model
ollama run qwen2.5-coder:7b "Write Python function for Sieve of Eratosthenes"
ollama run deepseek-coder-v2:16b "Write Python function for Sieve of Eratosthenes"
ollama run codellama:13b "Write Python function for Sieve of Eratosthenes"
```

<details>
<summary>Expected Results</summary>

**Likely winner**: DeepSeek V2:16b (most optimized, best comments)
**Runner-up**: Qwen 2.5-Coder:7b (fast, correct, good enough)
**Lesson**: Bigger models produce slightly better code, but 7B is often sufficient!
</details>

---

### Challenge 2: Cost Savings Calculator

**Goal**: Calculate your actual savings from using local models

**Task**: Track one week of coding, calculate what it would cost with API

```python
# Create savings_calculator.py
def calculate_savings():
    # Your actual usage this week
    coding_sessions = 15  # How many times you used Aider/Continue
    avg_tokens_per_session = 5000  # Rough estimate

    total_tokens = coding_sessions * avg_tokens_per_session

    # API costs
    claude_sonnet_cost = (total_tokens / 1_000_000) * 3  # $3/M input
    gemini_flash_cost = 0  # Your free tier

    # Local cost
    local_cost = 0

    weekly_savings = claude_sonnet_cost
    monthly_savings = weekly_savings * 4
    annual_savings = monthly_savings * 12

    print(f" Your Cost Savings Report")
    print(f"   Weekly:  ${weekly_savings:.2f}")
    print(f"   Monthly: ${monthly_savings:.2f}")
    print(f"   Annual:  ${annual_savings:.2f}")
    print(f"\n    You saved enough for: [insert fun comparison]")

calculate_savings()
```

**Run it**:
```bash
python savings_calculator.py
```

<details>
<summary>Expected Output</summary>

```
 Your Cost Savings Report
   Weekly:  $0.23
   Monthly: $0.90
   Annual:  $10.80

    You saved enough for: 1 month of Spotify Premium!
```

Note: Actual savings depend on usage. Heavy users save $200-500/year!
</details>

---

## Real Project Tie-Ins

How Module 1.2 skills apply to your actual projects:

### For kaizen (Lean DevOps Platform)

**What you just learned applies to**:
- Using local models for RAG pipeline development (privacy!)
- Cost optimization (iterate locally, deploy with API)
- Offline development of LangChain code

**Specific example**:
```bash
# Develop RAG pipeline locally with DeepSeek
aider --model ollama/deepseek-coder-v2:16b

> "Create a RAG pipeline using LangChain that:
  - Loads documents from /docs
  - Splits into chunks
  - Generates embeddings
  - Stores in Qdrant
  - Retrieves with similarity search"

# Model generates entire pipeline
# Test locally before deploying
# Deploy to production with Claude API for quality
```

**Savings**: $50-100/month during development!

---

### For vibe (Teaching Platform)

**What you just learned applies to**:
- Generating course content locally (cost-effective)
- Testing content generation prompts
- Privacy for unpublished content

**Specific example**:
```bash
# Generate programming exercises locally
aider --model ollama/qwen2.5-coder:7b

> "Generate 10 Python exercises for beginners:
  - Topic: Functions and loops
  - Difficulty: Easy to medium
  - Include solutions and test cases"

# Free, instant, iterate unlimited times
```

---

### For contrarian (Stock Analysis)

**What you just learned applies to**:
- Developing ML pipelines locally
- Code generation for data analysis
- Exploratory data analysis scripts

**Specific example**:
```bash
# Create sentiment analysis pipeline locally
aider --model ollama/deepseek-coder-v2:16b

> "Build sentiment analyzer for stock news:
  - Fetch from RSS feeds
  - Analyze sentiment with transformers
  - Store results with timestamps
  - Generate buy/sell signals"

# Iterate on strategy, all local, private
```

---

## Module 1.2 Complete Checklist

Use this to verify you're ready for Module 2:

### Setup 
- [ ] Ollama installed and working (`ollama --version`)
- [ ] At least one coding model downloaded (Qwen or DeepSeek)
- [ ] Tested model in terminal (`ollama run qwen2.5-coder:7b`)
- [ ] Aider installed (`aider --version`)
- [ ] Continue.dev extension installed in VS Code

### Practice 
- [ ] Generated code with local model (any task)
- [ ] Used Aider with local model
- [ ] Configured Continue.dev to use local model
- [ ] Tried at least 2 different models, compared results
- [ ] Set up hybrid workflow (local + Gemini Flash)

### Understanding 
- [ ] Can explain local vs API trade-offs
- [ ] Know which model to use for which task
- [ ] Understand cost savings (calculated your own)
- [ ] Know when to use local vs when to switch to API

### Reflection 
- [ ] Identified 3 tasks you'll do with local models
- [ ] Calculated potential monthly savings
- [ ] Planned your hybrid workflow (80% local, 20% API)

**All checked?**  **You're ready for Module 2: Prompt Engineering!**

---

## Further Reading

### Essential Resources

**Ollama Documentation**:
- Official docs: https://github.com/ollama/ollama
- Model library: https://ollama.com/library
- Community models: https://ollama.com/search

**Model Benchmarks**:
- HumanEval: https://github.com/openai/human-eval
- LiveCodeBench: https://livecodebench.github.io/
- BigCodeBench: https://bigcode-bench.github.io/

**Tools Integration**:
- Aider docs: https://aider.chat/docs/
- Continue.dev docs: https://continue.dev/docs

---

## ️ Next Steps

**Congratulations!** You now have cost-effective AI coding with local models!

**You've learned**:
- How to install and run Ollama
- The best local models for coding (DeepSeek, Qwen, etc.)
- Using local models with Aider
- Configuring Continue.dev for local models
- Hybrid optimization strategies (local + API)
- Real cost savings ($200-500/year potential!)

**Next Module**: **Module 2: Prompt Engineering Fundamentals** 

In Module 2, you'll learn:
- The art and science of prompt engineering
- How to structure prompts for best results
- Few-shot learning techniques
- Chain-of-thought prompting
- Works with BOTH local AND API models!

**Why Module 2 is critical**: Master prompting → Get 3-5× better results from ANY model (local or API)!

---

**Ready? Let's master prompt engineering in Module 2!** 

---

_Last updated: 2025-11-22_
_Module status:  Complete_
_Cost impact: $200-500/year savings potential_
_Tools: Ollama, Aider, Continue.dev_
