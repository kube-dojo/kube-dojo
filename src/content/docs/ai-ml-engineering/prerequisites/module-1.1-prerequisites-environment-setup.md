---
title: "Prerequisites & Environment Setup"
slug: ai-ml-engineering/prerequisites/module-0.0-prerequisites-environment-setup
sidebar:
  order: 101
---
> **AI/ML Engineering Track** | Complexity: `[QUICK]` | Time: 2-3
---
**Reading Time**: 2-3 hours
**Prerequisites**: A computer, internet access, and the willingness to type commands into a terminal
---

San Francisco. January 15, 2024. 11:32 PM. Alex Chen, a developer at a San Francisco startup, stared at his terminal, exhausted and confused. He was supposed to be learning prompt engineering—his company had given him two weeks to prototype an AI feature. Instead, he'd spent the last eight hours debugging why his Python installation couldn't find the `anthropic` module. "Which Python is this even using?" he muttered, watching his third attempt fail with yet another cryptic error message.

## The 8-Hour Nightmare That Inspired This Module

Alex was supposed to be learning prompt engineering. Instead, he'd spent the last eight hours debugging why his Python installation couldn't find the `anthropic` module. He'd installed it. At least, he thought he had.

"Which Python is this even using?" he muttered, staring at three different Python versions installed on his Mac. The terminal showed Python 3.8, his IDE said 3.11, and pip was installing to... somewhere else entirely.

He'd tried everything. Reinstalling pip. Upgrading Python. Reading Stack Overflow threads from 2019 that recommended commands that no longer worked. Each "solution" seemed to create two new problems. His browser had forty-seven tabs open, each promising to fix the issue once and for all.

At 2 AM, he finally gave up and went to bed, having learned zero about AI and everything about dependency hell.

The next morning, his mentor—a senior ML engineer who'd seen this exact scenario play out a hundred times—sent him a single checklist. "Follow this exactly," she wrote. "Don't skip steps. Don't improvise." Thirty minutes later, Alex had a clean virtual environment, properly installed packages, and his first working API call.

> "I wasted an entire night because nobody told me the basics. Now I make every new developer go through this setup guide before they write a single line of AI code. The time spent here saves weeks of frustration later."
> — Alex Chen, ML Engineer (and co-author of this module)

That eight-hour nightmare? It's now a 30-minute checklist. Every step exists because someone suffered so you don't have to.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Verify you have the required prerequisites (Python, git, command line)
- Set up your development environment with confidence
- Configure API keys securely (and understand why it matters!)
- Make your first LLM API call
- **Master Python AI best practices** from day one
- Understand what can go wrong (and how to fix it fast)

**Why this matters**: A properly configured environment is like a sharp knife - it makes every task easier and prevents frustration. Do this right once, benefit for the entire curriculum.

---

## The Setup Challenge: Why This Module Exists

### The Problem Everyone Faces

**Without proper setup** (the horror story):

```
Day 1: "Let me just start coding..."
Hour 1: ImportError: No module named 'anthropic'
Hour 2: "Wait, which Python am I running?" (system Python vs venv chaos)
Hour 3: "Why is my API key not working?!" (committed to git, oops!)
Hour 4: "Different error on my laptop vs desktop"
Hour 5: Gives up, frustrated
```

**With proper setup** (the smooth experience):

```
Day 1: Following Module 0 step-by-step
Hour 1: Python 3.12 + venv created 
Hour 2: API keys configured securely 
Hour 3: First LLM call successful 
Remaining time: Actually learning AI instead of fighting tools!
```

**The difference**: 5 hours of frustration vs 2 hours of foundation-building.

---

## Did You Know? The Hidden Cost of Bad Setup

**Real data from bootcamp students**:
- **70% of "bugs"** in Week 1 are actually environment issues, not code bugs
- **Average time lost**: 8-12 hours debugging setup problems
- **#1 reason students quit**: Frustration with tooling before they even start learning

**Good news**: This module prevents all of that. Every minute invested here saves 10 minutes later.

> **Did You Know?** The term "dependency hell" was coined in the late 1990s to describe the nightmare of managing software libraries. In 2019, a study by researchers at the University of Zurich found that **23% of all build failures** in open-source projects were caused by dependency issues—not actual code bugs. Python's virtual environment system, while sometimes confusing for beginners, has reduced this problem significantly. Before venvs became standard, teams would spend an average of 4-6 hours per developer per month resolving environment conflicts. That's nearly a full workday lost to tooling problems!

---

## Prerequisites Check

### The Self-Assessment Test

Before starting Neural Dojo, you should have basic programming knowledge. But what does "basic" actually mean?

**Answer these honestly**:

```python
# Test 1: Can you read and understand this code?
def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}! Welcome to Neural Dojo."

# Test 2: Can you explain what happens here?
users = ["Alice", "Bob", "Charlie"]
greetings = [greet(user) for user in users]

# Test 3: Can you spot the bug?
def calculate_total(prices: list[float]) -> float:
    total = 0
    for price in prices:
        total += price
    return total

items = ["10.50", "20.00", "5.75"]  # Bug: strings, not floats!
total = calculate_total(items)
```

#### If you could:
- Read and understand Test 1 → You're ready
- Explain Test 2 (list comprehension) → Great!
- Spot Test 3 bug (type mismatch) → Even better!

#### If you couldn't:
- **Recommendation**: Take a Python basics course first
- **Options**: [Python for Everybody](https://www.py4e.com/) or [Automate the Boring Stuff](https://automatetheboringstuff.com/)
- **Time needed**: 20-40 hours to get comfortable

**No shame in starting with basics!** Everyone starts somewhere. A solid foundation makes AI learning 10× easier.

---

## Required Software: The Minimal Toolbox
### (Or: What You Actually Need to Install Before We Can Have Fun)

Think of your development environment like a kitchen. You can technically cook with just a pan and a knife, but having the right tools—sharp knives, good pots, proper measuring cups—makes everything faster and more enjoyable. This section gives you the minimal kitchen setup; later modules will add specialized equipment as needed.

### What You Actually Need

**The essentials** (can't proceed without these):
1. **Python 3.12+** - The programming language (we require modern Python for performance and features)
2. **pip** - Package installer (comes with Python)
3. **Terminal/Command Prompt** - Access to command line
4. **Text editor or IDE** - Any code editor works

**Recommended** (makes life easier):
5. **Git** - Version control (helpful but optional for this curriculum)
6. **VS Code or Cursor** - Modern AI-friendly editors

**Not required** (but nice to have):
- Docker (we'll install later if needed)
- Jupyter Notebook (modules work as .py files)
- Database tools (not needed until Module 11+)

---

## Development Environment Setup
### (The Part Where We Actually Set Things Up)

### The Setup Journey: A Visual Roadmap

```
┌─────────────────────────────────────────────────────┐
│ Your System (macOS/Windows/Linux)                   │
│                                                      │
│  Step 1: Verify Python 3.12+                        │
│           ↓                                          │
│  Step 2: Choose Editor (VS Code/Cursor/PyCharm)     │
│           ↓                                          │
│  Step 3: Clone neural-dojo repo                     │
│           ↓                                          │
│  Step 4: Create virtual environment (venv)          │
│           ↓                                          │
│  Step 5: Install dependencies                       │
│           ↓                                          │
│  Step 6: Configure API keys (.env file)             │
│           ↓                                          │
│  Step 7: Run test scripts (verify everything)       │
│           ↓                                          │
│      READY TO START MODULE 1!                     │
└─────────────────────────────────────────────────────┘
```

**Total time**: 1-2 hours (first time), 15 minutes (if you repeat on another machine)

---

### Step 1: Verify Python Installation

**The Personality**: Python is your **universal translator** - it speaks to AI models, processes data, and builds applications.

**Why Python 3.12+?**

We're not being picky for fun here. Python 3.12 brings real improvements that matter for AI work:

- **5-10% faster** than 3.11 - sounds small, but when you're training models for hours, it adds up
- **Better error messages** - the new error messages actually tell you what went wrong instead of cryptic tracebacks
- **Improved type system** - your IDE becomes dramatically more helpful
- **Per-interpreter GIL** - experimental, but useful for parallel ML workloads
- **Full library support** - PyTorch, TensorFlow, Transformers all work perfectly
- **Future-proof** - this curriculum will stay relevant for years

Think of it like this: you could build a house with hand tools from 1950, but why would you when power tools exist?

```bash
# Check Python version (must be 3.12 or higher)
python --version
# or on macOS/Linux:
python3 --version

# Check pip is installed
pip --version
# or:
pip3 --version
```

**Expected Output**:
```
Python 3.12.x or 3.13.x (3.12+ required)
pip 24.x.x (or higher)
```

#### Common Mistakes 

Think of Python versions like phone numbers. If you dial the wrong number, you reach the wrong person—even if you dial perfectly. Similarly, running code with the wrong Python version gives wrong results, even if your code is perfect. The mistakes below are like having multiple phone numbers written down and accidentally calling your ex instead of your boss.

**Mistake #1: Using system Python (macOS/Linux)**
```bash
# DON'T DO THIS
which python
# Output: /usr/bin/python (system Python, often old!)

# DO THIS INSTEAD
which python3
# Output: /usr/local/bin/python3 or /opt/homebrew/bin/python3
```

**Why it matters**: System Python is often outdated (3.9 on macOS, 3.8 on some Linux) and shouldn't be modified. Always use `python3`.

**Mistake #2: Multiple Python versions causing confusion**
```bash
# Check all Python installations
ls -la /usr/bin/python*
ls -la /usr/local/bin/python*
ls -la /opt/homebrew/bin/python*  # macOS with Apple Silicon

# If you see python, python3, python3.9, python3.12, python3.13...
# Use version 3.12+ explicitly
python3.12 --version
# or
python3.13 --version
```

**Fix**: Use `python3.12` or `python3.13` throughout the curriculum.

#### Troubleshooting

**macOS**:
- **Default macOS Python is 3.9** (Monterey/Ventura/Sonoma)
- ️ Too old for this curriculum! We need 3.12+
- **Install Python 3.12+**:
  ```bash
  # Using Homebrew (recommended)
  brew install python@3.12

  # Verify installation
  python3.12 --version

  # Make it the default (optional)
  echo 'alias python3=python3.12' >> ~/.zshrc
  echo 'alias pip3=pip3.12' >> ~/.zshrc
  source ~/.zshrc
  ```
- Alternative: Download from https://python.org/downloads/
- Use `python3.12` and `pip3.12` commands explicitly

**Windows**:
- Download **Python 3.12+** from https://python.org/downloads/
- **CRITICAL**:  CHECK "Add Python to PATH" during installation
- Restart terminal after installing
- Verify: `python --version` (should show 3.12+)

**Linux**:
- Ubuntu/Debian:
  ```bash
  sudo apt update
  sudo apt install python3.12 python3.12-venv python3-pip
  python3.12 --version
  ```
- Fedora:
  ```bash
  sudo dnf install python3.12
  python3.12 --version
  ```
- If 3.12 not available in repos, use deadsnakes PPA (Ubuntu):
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update
  sudo apt install python3.12 python3.12-venv
  ```

---

### Step 2: Choose Your Text Editor/IDE

**The Personality**: Your editor is your **workshop** - where you craft code, debug, and bring ideas to life.

**Decision Matrix**: Which editor matches your style?

| Editor | Best For | Pros | Cons | AI Features |
|--------|----------|------|------|-------------|
| **VS Code** | Beginners, general use | Free, lightweight, huge extension ecosystem | Can be overwhelming | Claude Code extension, Copilot |
| **Cursor** | AI-first developers | Built-in AI, VS Code fork | Newer, some bugs | Native AI chat, inline editing |
| **PyCharm** | Python experts, large projects | Best Python tooling, refactoring | Heavy, slower startup | AI Assistant plugin |
| **Vim/Emacs** | Terminal lovers | Ultra fast, everywhere | Steep learning curve | Copilot.vim, codeium |

**Recommendation by Profile**

**"I'm new to programming"** → Go with **VS Code**. It's the Toyota Corolla of editors - reliable, well-documented, and everyone can help you when you're stuck. The Python extension works out of the box, and there's a tutorial for literally everything. Download: https://code.visualstudio.com/

**"I want AI to write my code"** → Try **Cursor**. It's VS Code with AI superpowers baked in. You'll be using AI assistants heavily in Module 1 anyway, so you might as well start with the tool built for it. The learning curve is almost zero if you know VS Code. Download: https://cursor.sh/

**"I'm a Python pro who hates slow tools"** → You want **PyCharm**. Yes, it's heavier than VS Code. Yes, startup takes a few seconds. But the refactoring tools will save you hours, and the debugger is genuinely the best in the business. Download: https://www.jetbrains.com/pycharm/download/ (Community Edition is free)

**"I live in the terminal and judge people who use GUIs"** → You already know what you're doing. Vim/Neovim with Copilot.vim or codeium. We respect you. We also can't help you debug your .vimrc.

**After installing**, add the recommended extensions:
- **VS Code**: Python, Pylance, Claude Code
- **Cursor**: Built-in AI (no additional setup needed)
- **PyCharm**: Python plugin is included

---

### Step 3: Create Project Directory

```bash
# Navigate to where you keep code projects
cd ~/projects  # or C:\Users\YourName\projects on Windows

# Clone neural-dojo (if you haven't already)
git clone https://github.com/krisztiankoos/neural-dojo.git
cd neural-dojo

# Or if you already have it:
cd ~/projects/neural-dojo
```

**Pro tip**: Keep all your projects in ONE parent directory (like `~/projects`). Makes them easy to find and back up.

---

### Step 4: Create Virtual Environment

**The Personality**: Virtual environments are **isolation chambers** - each project gets its own clean Python universe.

Think of virtual environments like a scientist's clean room laboratory. When manufacturing computer chips, you can't have dust from one batch contaminating another—each project needs its own pristine, isolated workspace. Similarly, a virtual environment gives each Python project its own sealed bubble where packages can't interfere with each other.

#### Why This Module Matters The Real Reason

**Without venv** (dependency hell):
```
Project A needs: pandas 1.5.0
Project B needs: pandas 2.0.0
System Python has: pandas 1.3.0

Result: Nothing works. Everything breaks. Chaos.
```

**With venv** (harmony):
```
Project A (venv_a): pandas 1.5.0 
Project B (venv_b): pandas 2.0.0 
System Python: pandas 1.3.0 

Result: All projects work independently!
```

**Real-world analogy**: Venvs are like separate kitchens for each recipe. Project A's kitchen has metric measuring cups, Project B's has imperial. No conflicts!

> ** Did You Know?**
>
> Virtual environments were inspired by a concept from the Python community called "dependency isolation." Before venvs became standard, developers used tools like `virtualenv` (created in 2007 by Ian Bicking) and later `pipenv`. The `venv` module was added to Python's standard library in version 3.3 (2012), making virtual environments accessible without installing extra packages. Today, over 90% of professional Python projects use some form of virtual environment—it's considered malpractice to install packages to your system Python.

#### Create It

```bash
# Create virtual environment named 'venv'
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your prompt:
(venv) $
```

**Verify activation**:
```bash
which python
# Should show: /path/to/neural-dojo/venv/bin/python
# NOT /usr/bin/python or /usr/local/bin/python3

pip list
# Should show minimal packages (pip, setuptools)
# If you see 100+ packages, you're NOT in the venv!
```

#### Common Mistakes 

**Mistake #1: Forgetting to activate venv**
```bash
# You'll know if you forgot because:
which python
# Shows: /usr/bin/python (WRONG!)

# Instead of:
# Shows: /Users/you/projects/neural-dojo/venv/bin/python (RIGHT!)
```

**Fix**: Always run `source venv/bin/activate` when starting work.

**Mistake #2: Installing packages globally**
```bash
# DON'T DO THIS (installing without venv active)
pip install anthropic  # Goes to system Python!

# DO THIS (venv active)
(venv) $ pip install anthropic  # Goes to venv 
```

**Mistake #3: Committing venv to git**
- venv folders are HUGE (100-500MB)
- They're system-specific (won't work on other machines)
- `.gitignore` already excludes `venv/` - don't override this!

---

### Step 5: Install Initial Dependencies

```bash
# FIRST: Activate venv (if not already)
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Upgrade pip (old pip has bugs)
pip install --upgrade pip

# Install development tools
pip install pytest pytest-cov black isort flake8 mypy

# Verify installation
pytest --version
black --version
```

**Expected Output**:
```
pytest 7.4.x or higher
black, 23.x.x or higher
```

#### What Each Tool Does

| Tool | Purpose | Why You Need It |
|------|---------|-----------------|
| **pytest** | Testing framework | Write and run tests for your code |
| **pytest-cov** | Code coverage | See what code is tested (aim for 80%+) |
| **black** | Code formatter | Auto-format code (PEP 8 style) |
| **isort** | Import sorter | Organize imports alphabetically |
| **flake8** | Linter | Find code smells and bugs |
| **mypy** | Type checker | Catch type errors before runtime |

** Did You Know?**
Black is called the "uncompromising code formatter" because it has almost no configuration options. The Python community agreed on ONE style, and Black enforces it. No more arguing about formatting in code reviews!

---

## API Keys Setup: Your Passport to AI
### (The Most Important Section You'll Skim and Regret Later)

**The Personality**: API keys are **security badges** - they prove you're authorized to access AI services (and track your usage for billing).

### ️ Critical: Subscriptions ≠ API Access

**This confuses 90% of beginners**, so read carefully:

| What You Have | What It Gives You | Can You Use It for This Curriculum? |
|---------------|-------------------|-------------------------------------|
| **ChatGPT Plus** ($20/month) | Unlimited ChatGPT web access |  NO - Different from API |
| **Claude Pro** ($20/month) | Unlimited Claude web access |  NO - Different from API |
| **OpenAI API Account** (pay-per-use) | Programmatic GPT access |  YES - This is what you need |
| **Anthropic API Account** (pay-per-use) | Programmatic Claude access |  YES - This is what you need |

**The difference**:
- **Subscriptions**: You click buttons in a web browser, unlimited use
- **API Access**: Your **code** sends requests, you pay per request (pennies)

**Can I have both?**
Yes! Many people have ChatGPT Plus for daily use AND an API account for coding. They're separate billing.

---

### Cost Reality Check: How Much Will This Actually Cost?

**Full Neural Dojo curriculum estimate**:
- **Claude API**: $3-5 total (most modules)
- **OpenAI API**: $5-10 total (if using gpt-5)
- **Optional local models**: $0 (free, but needs GPU)

**Why so cheap?**
Most requests are small (100-500 tokens). Even expensive models like gpt-5 cost ~$0.01 per request for typical curriculum use.

**Example calculation**:
```
Module 2 (Prompt Engineering): 50 API calls
Average tokens per call: 200 input + 300 output = 500 total
Claude Sonnet cost: $3 per 1M input tokens, $15 per 1M output tokens

Cost = (50 * 200 / 1M * $3) + (50 * 300 / 1M * $15)
     = $0.03 + $0.225
     = $0.26 for entire module!
```

**Entire curriculum**: 40 modules × $0.10 average = ~$4 total

---

### Option 1: Anthropic Claude API (Recommended)

**Why recommended**:
- Claude Sonnet 4.5 is excellent for code
- 200K token context window (huge!)
- Often includes $5-10 free credits for new accounts
- Straightforward pricing
- Great documentation

**Setup**:
1. Create account: https://console.anthropic.com/
2. Go to Settings → API Keys
3. Click "Create Key"
4. Copy the key (starts with `sk-ant-`)
5. **IMPORTANT**: Save it now - you can't see it again!

**Pricing** (as of 2025):
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens
- For curriculum: ~$3-5 total

---

### Option 2: OpenAI API

**When to use**:
- You already have OpenAI credits
- You want to compare Claude vs GPT
- Specific modules require GPT features

**Setup**:
1. Create account: https://platform.openai.com/
2. Go to API Keys
3. Create new secret key
4. Copy the key (starts with `sk-`)

**Pricing** (gpt-5-mini recommended for learning):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- For curriculum: ~$2-3 total

**Note**: New accounts may have rate limits. If you get rate limit errors, wait 24 hours or upgrade to paid tier.

> **Did You Know?** OpenAI's API pricing has dropped dramatically over time. When GPT-3 launched in 2020, it cost $0.06 per 1,000 tokens—making a single conversation cost several dollars. By 2023, GPT-3.5-turbo had dropped to $0.002 per 1,000 tokens—a **30x reduction**. Today's gpt-5-mini is even cheaper at $0.00015 per 1,000 input tokens. This exponential cost reduction follows a pattern similar to Moore's Law for computing. Researchers at Stanford estimated that the cost of AI inference is dropping approximately **70% per year**. What costs $10 today will cost $3 next year and less than $1 the year after. This is why now is the perfect time to learn AI development—the economics are becoming accessible to everyone.

---

### Option 3: Free Alternatives (Good for Experimentation)

If you want to try before committing to paid API:

1. **Groq** (FREE tier)
   - https://console.groq.com/
   - Ultra-fast inference
   - Free: 30 requests/minute
   - Models: Llama 4, Mixtral
   - **Perfect for**: Initial testing, learning prompting

2. **Together AI** ($25 free credits)
   - https://www.together.ai/
   - Many open-source models
   - Free trial lasts weeks
   - **Perfect for**: Full curriculum if on budget

3. **Hugging Face Inference API** (Free tier)
   - https://huggingface.co/inference-api
   - Access to 1000s of models
   - Rate limited but functional
   - **Perfect for**: Experimenting with different models

**Recommendation**: Start with Claude or OpenAI API ($3-5 investment) for best learning experience. Fall back to free alternatives if budget is tight.

---

### Storing API Keys Securely: The Right Way

**The WRONG way** (please don't do this):
```python
# main.py
api_key = "sk-ant-your-actual-key-here"  # TERRIBLE IDEA!

# Then you commit to GitHub and everyone has your key
# You get a $500 bill because someone used your key
# True story - happens weekly to developers
```

**The RIGHT way** (environment variables):
```python
# main.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file
api_key = os.getenv("ANTHROPIC_API_KEY")  # Safe!

# .env file is in .gitignore - never committed
```

#### Step-by-Step Secure Setup

**1. Create `.env` file**:
```bash
# In neural-dojo directory
touch .env

# Verify it's in .gitignore (should already be there)
cat .gitignore | grep .env
# Should show: .env
```

**2. Add your keys to `.env`**:
```bash
# Open .env in your editor and add:
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
OPENAI_API_KEY=sk-your-openai-key-here

# Optional: Set default model
DEFAULT_MODEL=claude-sonnet-4-5-20250929
```

**3. Install python-dotenv**:
```bash
pip install python-dotenv
```

**4. Test it works**:
```python
# test_env.py
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    print(f" API key loaded: {api_key[:10]}...")  # Show first 10 chars only
else:
    print(" API key not found")
```

#### Common Mistakes 

**Mistake #1: Spaces around `=`**
```bash
# WRONG
ANTHROPIC_API_KEY = sk-ant-key  # Spaces break it!

# RIGHT
ANTHROPIC_API_KEY=sk-ant-key  # No spaces!
```

**Mistake #2: Forgetting to call `load_dotenv()`**
```python
# WRONG
import os
api_key = os.getenv("ANTHROPIC_API_KEY")  # Returns None!

# RIGHT
import os
from dotenv import load_dotenv
load_dotenv()  # Must call this first!
api_key = os.getenv("ANTHROPIC_API_KEY")  # Now it works
```

**Mistake #3: Committing `.env` to git**
```bash
# Check what would be committed
git status

# If you see .env listed:
git rm --cached .env  # Remove from git
echo ".env" >> .gitignore  # Make sure it's ignored
```

---

## Verification: Your First LLM Call
### (The Moment of Truth)

**The moment of truth!** Let's verify everything works.

### Test 1: Environment Check

Run this test to verify Python setup:

```bash
cd examples/module_00
python test_environment.py
```

**What it checks**:
- Python 3.12+
- pip works
- python-dotenv installed

**Expected output**:
```
 Testing environment setup...

 Python 3.12.0
 pip works: pip 23.3.1
 python-dotenv installed

 Environment setup complete!
```

**If it fails**: Check the error message, fix the issue, run again.

---

### Test 2: Claude API Call

**The exciting part** - talking to Claude for the first time!

```bash
python test_claude_api.py
```

**What happens behind the scenes**:
1. Loads API key from `.env`
2. Imports `anthropic` package
3. Creates client
4. Sends request to Claude API
5. Receives response
6. Shows token usage

**Expected output**:
```
 Testing Claude API...

Installing anthropic package...
 API key found
 anthropic package imported

 Making API call to Claude...

 Claude says: Hello from Neural Dojo!

 Token usage:
   Input tokens: 15
   Output tokens: 6

 Claude API working! You're ready to start Module 1.
```

** Understanding Token Usage**:
- **Input tokens**: Your prompt (15 tokens for "Say 'Hello from Neural Dojo!' and nothing else.")
- **Output tokens**: Claude's response (6 tokens for "Hello from Neural Dojo!")
- **Cost**: (15 * $3 / 1M) + (6 * $15 / 1M) = $0.000045 + $0.00009 = **$0.000135** (basically free!)

**If it fails**: Check these in order:
1. Is API key in `.env` file? (`cat .env`)
2. Is key correct? (Copy-paste from Anthropic console again)
3. Do you have credits? (Check console.anthropic.com)
4. Is `anthropic` package installed? (`pip list | grep anthropic`)

---

### Test 3: OpenAI API (Optional)

If you also set up OpenAI:

```bash
python test_openai_api.py
```

**Note**: This is completely optional. Claude is sufficient for the entire curriculum.

---

## Module 0 Complete Checklist

Use this to verify you're 100% ready:

### Environment Setup
- [ ] Python 3.12+ installed and verified (`python3 --version`)
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Virtual environment activated (see `(venv)` in prompt)
- [ ] pip upgraded (`pip install --upgrade pip`)
- [ ] Development tools installed (pytest, black, etc.)

### Editor Setup
- [ ] Text editor/IDE chosen and installed
- [ ] Python extensions/plugins installed (if using VS Code/PyCharm)
- [ ] Editor can open and edit Python files

### Project Setup
- [ ] neural-dojo repository cloned/accessed
- [ ] Can navigate to project in terminal
- [ ] `.env` file created
- [ ] API key(s) added to `.env`
- [ ] `.env` is in `.gitignore` (verify!)

### Verification
- [ ] `test_environment.py` passes 
- [ ] `test_claude_api.py` passes  (or `test_openai_api.py`)
- [ ] Can see token usage in API test output

### Skills Verification
- [ ] Comfortable with command line (cd, ls, running scripts)
- [ ] Understand basic Python (functions, loops, classes)
- [ ] Know how to activate venv
- [ ] Can install packages with pip

**All checked?**  **You're ready for Module 1!**

---

## Understanding LLM APIs: What Actually Happens When You Call Claude
### (The Foundation You'll Build On)

Before we dive into best practices, let's understand what's really happening when your code talks to an AI. This mental model will save you countless debugging hours.

### The Journey of a Prompt

Think of an LLM API call like sending a letter through the postal system. You write your message (the prompt), put it in an envelope (HTTP request), address it correctly (API endpoint + headers), and send it off. Somewhere far away, the post office (Anthropic's servers) processes your letter, writes a response, and sends it back.

```
Your Code                    Internet                    Anthropic's Servers
   │                            │                              │
   │  1. Create prompt         │                              │
   │  2. Build request         │                              │
   ├────────────────────────────>                              │
   │        HTTP POST with                                     │
   │        - Headers (API key)                                │
   │        - Body (prompt, model, params)                     │
   │                            │                              │
   │                            ├──────────────────────────────>
   │                            │      3. Validate API key     │
   │                            │      4. Queue request        │
   │                            │      5. Run model            │
   │                            │      6. Generate tokens      │
   │                            <──────────────────────────────┤
   │                            │                              │
   <────────────────────────────┤                              │
   │        HTTP Response                                      │
   │        - Status (200, 429, etc.)                          │
   │        - Body (response text, usage stats)                │
   │                            │                              │
   │  7. Parse response        │                              │
   │  8. Use result            │                              │
```

### Why This Matters

Understanding this flow explains many common issues:

| Issue | What's Actually Happening |
|-------|--------------------------|
| "API key not found" | Step 2 failed - key missing from headers |
| "Rate limited" | Step 4 - too many requests queued |
| "Timeout error" | Steps 5-6 took too long (big prompt, complex response) |
| "Invalid model" | Step 3 - the model name you specified doesn't exist |
| "Context length exceeded" | Step 5 - prompt + expected response exceeds model's limit |

### The Anatomy of an API Request

Every LLM API call has the same basic structure:

```python
# This is what anthropic.messages.create() does under the hood
response = requests.post(
    "https://api.anthropic.com/v1/messages",  # Endpoint
    headers={
        "x-api-key": api_key,           # Authentication
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"  # API version
    },
    json={
        "model": "claude-sonnet-4-5-20250929",  # Which model
        "max_tokens": 1000,                     # Response limit
        "messages": [                           # The conversation
            {"role": "user", "content": "Hello!"}
        ]
    }
)
```

The `anthropic` Python package wraps this complexity in a clean interface:

```python
# Same thing, but nicer
from anthropic import Anthropic
client = Anthropic(api_key=api_key)
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Token Economics: Why Every Token Matters

LLM APIs charge by **tokens**, not characters or words. Understanding tokens is crucial for managing costs.

**What's a token?**

Think of tokens like syllables for AI. Common words ("the", "and", "is") are single tokens. Uncommon words get split up. Code has its own tokenization patterns.

```
"Hello, world!" → ["Hello", ",", " world", "!"] → 4 tokens
"anthropic" → ["anthrop", "ic"] → 2 tokens
"def hello():" → ["def", " hello", "():", "\n"] → 4 tokens
```

**The 4:1 Rule of Thumb**: English text averages ~4 characters per token. A 1000-word document is roughly 750-1000 tokens.

**Why it matters for costs**:
```
Your prompt (input tokens)        → You pay for this
+ Claude's response (output tokens) → You pay MORE for this

Claude Sonnet pricing:
Input:  $3 per 1M tokens  = $0.000003 per token
Output: $15 per 1M tokens = $0.000015 per token

A typical conversation:
- Your prompt: 200 tokens × $0.000003 = $0.0006
- Claude's response: 500 tokens × $0.000015 = $0.0075
- Total: ~$0.0081 per exchange (less than a cent!)
```

### Streaming vs. Non-Streaming Responses

When Claude generates a response, you have two options:

**Non-streaming** (default): Wait for the complete response
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Write a haiku"}]
)
print(response.content[0].text)  # Prints all at once
```

**Streaming**: Get tokens as they're generated
```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Write a haiku"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)  # Prints word by word
```

Think of it like a restaurant: non-streaming is getting your entire meal delivered at once (might wait a while but get everything together), while streaming is getting courses as they're ready (faster first bite, but takes same total time).

**When to use each**:
- **Non-streaming**: Processing responses programmatically, batch operations
- **Streaming**: User-facing chat interfaces (feels faster and more responsive)

> ** Did You Know?**
>
> The concept of tokens in NLP dates back to the 1960s, but modern "subword tokenization" (like BPE, the method Claude uses) was popularized by a 2015 paper by Rico Sennrich and colleagues. They discovered that breaking words into smaller pieces solved the "rare word problem"—models no longer needed to memorize every possible word, just common pieces they could combine. This single innovation made modern language models possible. GPT-2, GPT-3, gpt-5, and Claude all use variations of this approach, handling vocabulary of 50,000-100,000 tokens instead of millions of individual words.

---

## Python AI Best Practices
### (Start Strong, Save Hours Later)

Since you're here to learn AI development, let's establish **best practices from day one**:

### 1. **Always Use Type Hints**

**Why**: AI models (and humans!) understand your code better with types.

```python
# BAD (no type hints)
def generate_text(prompt, max_tokens):
    # What types are these? Who knows!
    pass

# GOOD (explicit types)
def generate_text(prompt: str, max_tokens: int) -> str:
    """Generate text using LLM."""
    pass
```

**AI coding assistants** (Copilot, Claude Code) give MUCH better suggestions with type hints!

---

### 2. **Use Pydantic for API Responses**

**Why**: LLM responses need validation - they sometimes hallucinate invalid JSON.

```python
# BAD (raw dict, no validation)
response = api_call()
name = response["name"]  # KeyError if missing!

# GOOD (Pydantic validates)
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

response_data = api_call()
user = User(**response_data)  # Validates or raises clear error
print(user.name)  # Safe!
```

---

### 3. **Handle API Errors Gracefully**

**Why**: APIs fail (rate limits, network issues, invalid keys). Plan for it.

```python
# BAD (crashes on error)
response = client.messages.create(...)

# GOOD (handles errors)
try:
    response = client.messages.create(...)
except anthropic.RateLimitError as e:
    print(f"Rate limited. Wait {e.retry_after} seconds.")
except anthropic.APIError as e:
    print(f"API error: {e}")
    # Fall back to cached response or retry
```

---

### 4. **Set Max Tokens to Prevent Runaway Costs**

**Why**: Without limits, a single bug can cost $50+ in API calls.

```python
# BAD (no limit, could generate 100K tokens!)
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": prompt}]
)

# GOOD (capped at 1000 tokens)
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1000,  # Safety limit
    messages=[{"role": "user", "content": prompt}]
)
```

---

### 5. **Use Structured Logging, Not Print**

**Why**: In production, you need searchable, filterable logs.

```python
# BAD (print statements)
print(f"Calling API with prompt: {prompt}")
print(f"Got response: {response}")

# GOOD (structured logging)
import logging

logger = logging.getLogger(__name__)

logger.info("api_call", extra={
    "prompt_length": len(prompt),
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 1000
})
logger.debug("api_response", extra={
    "response_tokens": response.usage.output_tokens
})
```

---

### 6. **Version Lock Your Dependencies**

**Why**: `pip install anthropic` today ≠ `pip install anthropic` in 6 months. Lock versions!

```bash
# BAD (in requirements.txt)
anthropic
openai

# GOOD (exact versions)
anthropic==0.25.0
openai==1.10.0

# HOW TO CREATE
pip freeze > requirements.txt
```

---

### 7. **Separate Prompts from Code**

**Why**: Prompts are data, not code. Easier to iterate when separate.

```python
# BAD (hardcoded prompt)
def analyze_sentiment(text: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"Classify sentiment of: {text}"
        }]
    )
    return response.content[0].text

# GOOD (prompt in separate file or constant)
SENTIMENT_PROMPT = """
Classify the sentiment of the following text as positive, negative, or neutral.

Text: {text}

Sentiment:"""

def analyze_sentiment(text: str) -> str:
    prompt = SENTIMENT_PROMPT.format(text=text)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

---

### 8. **Test AI Outputs (They're Non-Deterministic!)**

**Why**: LLMs with temperature > 0 are random. Test behaviors, not exact text.

```python
# BAD (brittle test)
def test_sentiment():
    result = analyze_sentiment("I love this!")
    assert result == "positive"  # Might be "Positive" or "positive sentiment"

# GOOD (flexible test)
def test_sentiment():
    result = analyze_sentiment("I love this!")
    assert "positive" in result.lower()
    assert len(result) < 20  # Reasonable length
```

---

## Common Mistakes: Learn From Others' Pain
### (So You Don't Have to Make Them Yourself)

### Mistake #1: "I Installed Packages Without Activating Venv"

**Symptom**:
```bash
$ pip list
# Shows 200 packages (you only installed 10?)
```

**Diagnosis**: You installed to system Python, not venv.

**Fix**:
```bash
# Delete venv and start over
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Prevention**: ALWAYS see `(venv)` before running `pip install`!

---

### Mistake #2: "My API Key Stopped Working After I Committed to GitHub"

**Symptom**: API calls fail with "Invalid API key" after you pushed code.

**Diagnosis**: You committed your key to GitHub. Someone found it and used/reported it. Anthropic/OpenAI automatically revoked it.

**Fix**:
1. **Immediately** revoke the key in API console
2. Generate new key
3. Add to `.env` file
4. Verify `.env` is in `.gitignore`
5. Remove key from git history:
```bash
git filter-branch --tree-filter 'rm -f .env' HEAD
git push --force
```

**Prevention**: NEVER commit `.env`. Triple-check before pushing!

---

### Mistake #3: "I'm Getting 'ModuleNotFoundError' But I Installed It!"

**Symptom**:
```python
import anthropic  # ModuleNotFoundError!
```

**Diagnosis**: Multiple Python installations. You installed with one, running with another.

**Fix**:
```bash
# Find which Python is being used
which python
# Output: /usr/bin/python (WRONG! System Python)

# Activate venv
source venv/bin/activate

# Now check again
which python
# Output: /path/to/neural-dojo/venv/bin/python (RIGHT!)
```

**Prevention**: Always activate venv before running Python code!

---

### Mistake #4: "My Code Works Locally But Not on Another Machine"

**Symptom**: Code runs fine on your laptop, crashes on your desktop.

**Diagnosis**: Different Python versions, missing dependencies, hard-coded paths.

**Fix**:
```bash
# On working machine
python --version  # Note the version
pip freeze > requirements.txt  # Lock dependencies

# On broken machine
python3 --version  # Must match!
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Install exact versions
```

**Prevention**: Use `requirements.txt` and document Python version in README!

---

## Hands-On Exercises

### Exercise 1: Debug the Setup

I've intentionally broken this code. Can you fix it?

```python
# broken_setup.py
import os

# Bug 1: Missing import
api_key = os.getenv("ANTHROPIC_API_KEY")

# Bug 2: Using wrong client
client = OpenAI(api_key=api_key)

# Bug 3: Wrong model name
response = client.messages.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.content)
```

<details>
<summary>Click for solution</summary>

```python
# fixed_setup.py
import os
from dotenv import load_dotenv
from anthropic import Anthropic  # Fix: Correct import

load_dotenv()  # Fix: Actually load .env
api_key = os.getenv("ANTHROPIC_API_KEY")

client = Anthropic(api_key=api_key)  # Fix: Correct client

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",  # Fix: Correct model
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.content[0].text)  # Fix: Access text correctly
```
</details>

---

### Exercise 2: Cost Calculator

Write a function to estimate API costs:

```python
def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-sonnet-4-5"
) -> float:
    """
    Calculate estimated cost for API call.

    Pricing (as of 2025):
    Claude Sonnet: $3/1M input, $15/1M output
    gpt-5-mini: $0.15/1M input, $0.60/1M output
    """
    # Your code here!
    pass

# Test it
cost = estimate_cost(input_tokens=500, output_tokens=300)
print(f"Estimated cost: ${cost:.4f}")  # Should print ~$0.0060
```

<details>
<summary>Click for solution</summary>

```python
def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-sonnet-4-5"
) -> float:
    pricing = {
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "gpt-5-mini": {"input": 0.15, "output": 0.60}
    }

    if model not in pricing:
        raise ValueError(f"Unknown model: {model}")

    input_cost = (input_tokens / 1_000_000) * pricing[model]["input"]
    output_cost = (output_tokens / 1_000_000) * pricing[model]["output"]

    return input_cost + output_cost
```
</details>

---

### Exercise 3: What Happens If...?

Predict the output, then run to verify:

```python
# Scenario 1: Venv not activated
# Run: pip list
# Prediction: ?

# Scenario 2: .env exists but load_dotenv() not called
import os
api_key = os.getenv("ANTHROPIC_API_KEY")
# Prediction: api_key is ___?

# Scenario 3: Temperature=0 vs Temperature=1
# Run same prompt twice with temp=0
# Run same prompt twice with temp=1
# Prediction: Which gives identical outputs?
```

---

## Deep Dive (Optional): How Virtual Environments Really Work
### (For the Curious)

**For the curious**: What actually happens when you create a venv?

### Under the Hood

```bash
python3 -m venv venv

# This creates:
venv/
├── bin/              # Executables
│   ├── python       # Symlink to python3.12
│   ├── pip          # Pip for this venv
│   └── activate     # Activation script
├── include/          # C headers
├── lib/              # Installed packages
│   └── python3.12/
│       └── site-packages/  # Package installation directory
└── pyvenv.cfg        # Configuration
```

**When you activate**:
```bash
source venv/bin/activate

# This modifies your shell:
export PATH="/path/to/venv/bin:$PATH"
export VIRTUAL_ENV="/path/to/venv"

# Now `python` resolves to venv/bin/python
# And `pip install` goes to venv/lib/python3.12/site-packages/
```

**When you deactivate**:
```bash
deactivate

# This restores original PATH
# `python` now resolves to system Python again
```

### Why Symlinks Matter

```bash
ls -la venv/bin/python
# Output: python -> python3.12

# This is a symlink (symbolic link)
# Points to the actual Python binary
# Allows multiple names (python, python3) to use same executable
```

### The Magic of site-packages

```bash
# Where packages actually live
ls venv/lib/python3.12/site-packages/

# When you `import anthropic`, Python searches:
# 1. Current directory
# 2. PYTHONPATH environment variable
# 3. site-packages directories (venv first, then system)
```

**Pro tip**: Want to see import resolution?
```python
import sys
print(sys.path)
# Shows all directories Python searches for imports
# First one should be your venv/lib/python3.12/site-packages
```

---

## Real Project Tie-Ins

This setup directly enables your real projects:

### For kaizen (Lean DevOps Platform)
**What you just learned applies to**:
- Setting up kaizen's RAG backend environment
- Managing dependencies for LangChain, Qdrant, FastAPI
- Securing Anthropic API keys for production
- Testing RAG pipelines with pytest

**Next steps in kaizen**: Module 11+ (Vector DBs, RAG systems)

---

### For vibe (Teaching Platform)
**What you just learned applies to**:
- AI content generation backend setup
- Managing OpenAI/Claude dependencies
- Environment isolation for dev vs production
- Handling API costs at scale

**Next steps in vibe**: Module 26-29 (Generative AI, multimodal models)

---

### For contrarian (Stock Analysis)
**What you just learned applies to**:
- Setting up ML pipeline environment
- Managing PyTorch, transformers dependencies
- Isolating analysis environment from other projects
- Testing sentiment analysis models

**Next steps in contrarian**: Module 19-25 (Deep Learning, time series)

---

## Did You Know? More Fascinating Facts

### The .env Pattern's Origin

The `.env` file pattern comes from the **Twelve-Factor App** methodology, created by Heroku engineers in 2012. They observed that successful cloud apps separated config from code. Now it's an industry standard!

**Fun fact**: GitHub scans every commit for API keys and automatically notifies providers if it finds one. They catch ~1,000 leaked keys per day!

> **Did You Know?** The Twelve-Factor App methodology was written by Adam Wiggins and other Heroku engineers after observing patterns across thousands of deployed applications. Factor number three—"Config: Store config in the environment"—specifically recommends using environment variables because they're language-agnostic, can't be accidentally committed to version control, and are easy to change between deployments. The methodology has been adopted by companies like Netflix, Spotify, and Airbnb for their microservices architectures. When you create a `.env` file, you're following the same practices that power applications serving billions of users.

---

### Python's Virtual Environment Evolution

- **2008**: `virtualenv` created as third-party tool
- **2012**: `virtualenv` becomes most popular Python tool
- **2014**: `venv` added to Python 3.3+ standard library (built-in!)
- **2020**: `virtualenv` still popular but `venv` is preferred
- **Today**: 95% of Python projects use venv or virtualenv

**Why built-in matters**: No extra installation needed. Works everywhere Python works.

---

### API Key Security Statistics

**Real data from GitHub leaked secrets**:
- **80%** of leaked keys are found within 24 hours by bots
- **Average cost** of leaked key before detection: $500-2,000
- **#1 cause**: Committing `.env` file to public repo
- **#2 cause**: Hardcoding keys in code then pushing

**Protection**: `.gitignore` + environment variables = 99.9% effective

> **Did You Know?** In 2023, GitGuardian detected over **12.8 million hardcoded secrets** in public GitHub commits—a 28% increase from the previous year. The most commonly exposed secrets were API keys, followed by database credentials and private encryption keys. One infamous case involved a developer at Uber who accidentally committed AWS credentials to a public repository in 2016, leading to a data breach affecting 57 million users. The incident cost Uber $148 million in settlements and led to stricter security practices across the industry. Today, tools like GitHub's secret scanning, GitGuardian, and pre-commit hooks can catch most leaks before they happen—but only if you use them.

---

## Advanced Troubleshooting

### Issue: "SSL Certificate Verification Failed"

**Symptom**:
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Common on**: macOS with Python from python.org

**Fix**:
```bash
# Run the certificate install script
cd "/Applications/Python 3.12"
./Install\ Certificates.command
```

---

### Issue: "Permission Denied When Creating Venv"

**Symptom**:
```bash
python3 -m venv venv
# PermissionError: [Errno 13] Permission denied
```

**Fix**:
```bash
# Don't use sudo! Instead, check directory permissions
ls -la  # Check if you own the directory

# If not, change to a directory you own
cd ~/projects
mkdir neural-dojo-test
cd neural-dojo-test
python3 -m venv venv  # Should work now
```

---

### Issue: "ImportError After Installing Package"

**Symptom**:
```bash
pip install anthropic
# Successfully installed

python -c "import anthropic"
# ImportError: No module named 'anthropic'
```

**Diagnosis**: Package installed to different Python than you're running.

**Fix**:
```bash
# Use Python module invocation for pip
python -m pip install anthropic

# This ensures same Python for both pip and import
```

---

## Module 0 Completion Badge

** Congratulations!** If you've checked all items and tests pass, you've earned:

```
╔════════════════════════════════════════╗
║    NEURAL DOJO: MODULE 0 COMPLETE     ║
║                                        ║
║    Environment Setup Master          ║
║    API Configuration Expert          ║
║    Best Practices Advocate           ║
║                                        ║
║   Ready for Module 1: AI-Driven Dev   ║
╚════════════════════════════════════════╝
```

**Skills acquired**:
- Python environment management (venv, pip)
- Secure API key handling
- First LLM API call
- Troubleshooting setup issues
- Python AI best practices
- Cost estimation and management
- Understanding token economics
- Debugging common setup problems
- Following industry-standard security practices

---

## Next Steps

**You're now ready for Module 1: Foundations of AI-Driven Development**

In Module 1, you'll learn:
- The AI development landscape (11 AI coding tools compared!)
- How to use AI assistants effectively (Claude Code, Cursor, Copilot)
- The mental model of AI pair programming
- When to use AI vs traditional coding
- Building your first project with AI assistance

The environment you've just configured is your launchpad. Every AI application you build—from simple chatbots to sophisticated RAG systems—will rely on these fundamentals. The time you invested here will pay dividends throughout the entire curriculum and beyond.

**The foundation is set. Let's build!** 

---

_Last updated: 2025-11-22 (Enhanced with Quality Patterns)_
_Module status:  Complete_
