---
title: "Tokenization & Text Processing"
slug: ai-ml-engineering/generative-ai/module-2.2-tokenization-text-processing
sidebar:
  order: 303
---
> **AI/ML Engineering Track** | Complexity: `[MEDIUM]` | Time: 4-5
> **Migrated from neural-dojo** — pending pipeline polish

# Or: Why 'tokenization' Has Nothing to Do With Cryptocurrency

**Reading Time**: 4-5 hours
**Prerequisites**: Module 6

---

## What You'll Be Able to Do

By the end of this module, you will:
- Understand how text becomes tokens
- Learn different tokenization algorithms (BPE, WordPiece, SentencePiece)
- Master token counting and optimization
- Understand why token limits matter for costs and performance
- Handle multilingual text tokenization
- Optimize prompts for token efficiency

---

## Introduction

**Question**: Why does "Hello world" cost more than "Hi there" even though they're both simple greetings?

**Answer**: Tokenization.

LLMs don't process raw text. They process **tokens** - and the number of tokens determines:
- API costs (charged per token)
- Context window limits (max tokens processable)
- Generation speed (more tokens = slower)

**This module teaches you the hidden language of LLMs**: How text becomes tokens.

---

## Did You Know? The $10 Billion Question Nobody Asked

In the early days of GPT-3 (2020), users noticed something strange: **the model couldn't do basic arithmetic**.

```
User: What is 378 + 456?
GPT-3: 834 (CORRECT!)

User: What is 3789 + 4567?
GPT-3: 8346 (WRONG! Answer is 8356)
```

**Why?** The answer shocked the AI community: **tokenization**.

GPT-3's tokenizer splits numbers inconsistently:
- "378" → 1 token (common number)
- "3789" → 2 tokens ("37" + "89")
- "4567" → 2 tokens ("45" + "67")

When you ask GPT-3 to add "37|89" + "45|67", it's not seeing the actual numbers - it's seeing fragments! The model has to reconstruct what numbers these tokens represent, perform arithmetic, then tokenize the result. This is like asking someone to add "thir|ty-sev|en" + "for|ty-fi|ve" by looking at syllables.

**The Business Impact**:
- OpenAI spent millions debugging this before realizing it was a tokenization design choice
- Financial companies using GPT-3 for calculations had to add verification layers
- Anthropic and Google redesigned their tokenizers to handle numbers better

**The Fix in Modern Models**:
- GPT-4 and Claude use improved tokenizers that keep numbers intact
- Some models tokenize each digit separately (consistent but expensive)
- Others use special handling for numeric strings

**Lesson**: Tokenization isn't just an implementation detail - it's a **fundamental design decision** that affects what your model can and cannot do!

---

## STOP: Time to Practice!

**You've learned the theory - now let's count some tokens!**

Before diving deeper into tokenization algorithms, get hands-on experience with how text becomes tokens. Each example builds your intuition about what makes tokenization efficient or expensive.

### Practice Path (~3-3.5 hours total)

**1. [Token Counter](../../examples/module_07/01_token_counter.py)** - See tokenization in action
   -  Concept: Basic token counting and visualization
   - ⏱️ Time: 45-60 minutes
   - Goal: Understand how different text types tokenize
   - What you'll learn: Code uses 3-4x more tokens than prose!

**2. [Token Optimization](../../examples/module_07/02_optimization.py)** - Save 30-50% on API costs
   -  Concept: 6 strategies to reduce token counts
   - ⏱️ Time: 60-75 minutes
   - Goal: Optimize prompts without losing quality
   - What you'll learn: Simple changes = massive savings at scale

**3. [Multilingual Tokenization](../../examples/module_07/03_multilingual.py)** - Compare 15+ languages
   -  Concept: Why non-English costs 2-3x more
   - ⏱️ Time: 45-60 minutes
   - Goal: Budget accurately for multilingual apps
   - What you'll learn: English bias in tokenizers is real

### Deliverable: Token Optimization Report

**What**: Analyze your own prompts/codebase for token efficiency
**Time**: 2-3 hours
**Portfolio Value**: Shows cost-awareness and production optimization skills

**Requirements**:
1. Run token counter on 5-10 prompts from your projects (kaizen, vibe, contrarian)
2. Identify optimization opportunities (verbosity, formatting, etc.)
3. Implement optimizations and measure savings
4. Calculate monthly cost savings at scale (100K-1M requests)
5. Document findings in a Markdown report with before/after comparisons

**Success Criteria**:
- Token counts measured before/after optimization
- At least 20% token reduction achieved
- Cost savings calculated for production volumes
- Best practices documented for future use

**Real-World Impact**: Token optimization is critical for production AI - this deliverable proves you can reduce costs without sacrificing quality!

---

##  What Are Tokens?

### The Simple Definition

**Token**: A unit of text that the model processes.

**Not necessarily**:
- A word
- A character
- A fixed length

**Examples**:
```
"Hello world" → ["Hello", " world"] (2 tokens)
"Hello" → ["Hello"] (1 token)
"Hellooooo" → ["Hello", "o", "o", "o", "o"] (5 tokens)
```

---

### Why This Module Matters

**Problem with characters**:
- Vocabulary = 256 (for ASCII/UTF-8)
- Sequences very long: "Hello" = 5 tokens
- Model must learn letter combinations → words

**Problem with words**:
- Vocabulary = millions (all words in all languages)
- Can't handle new words or typos
- Different languages have different word structures

**Subword tokenization** = Sweet spot!
- Vocabulary = 30K-100K tokens
- Handles new words (break into known parts)
- Efficient sequence lengths

** Want to see this in action? Run [01_token_counter.py](../../examples/module_07/01_token_counter.py) to visualize how text splits into tokens!**

---

##  Tokenization Algorithms

### 1. Byte-Pair Encoding (BPE)

**Used by**: GPT-2, GPT-3, GPT-4, many others

**How it works**:

**Step 1**: Start with character-level splits
```
"lower" → ["l", "o", "w", "e", "r"]
```

**Step 2**: Find most frequent pair
```
"l" + "o" appears most → merge to "lo"
"lower" → ["lo", "w", "e", "r"]
```

**Step 3**: Repeat until vocabulary size reached
```
Iteration 2: "lo" + "w" → "low"
"lower" → ["low", "e", "r"]

Iteration 3: "low" + "e" → "lowe"
"lower" → ["lowe", "r"]

Iteration 4: "lowe" + "r" → "lower"
"lower" → ["lower"]
```

**Result**: Common words = 1 token, rare words = multiple tokens

---

**Example**:
```
Common word: "the" → 1 token (appears billions of times)
Rare word: "antidisestablishmentarianism" → 7 tokens
Code: "def fibonacci" → 2 tokens ("def", " fibonacci")
```

**Advantage**: Works with any text, handles rare words gracefully

**Disadvantage**: Sensitive to whitespace and capitalization

---

### Did You Know? BPE Was Invented for Compression, Not AI!

**Plot twist**: BPE wasn't invented for NLP at all.

In **1994**, Philip Gage published a short article in *C Users Journal* titled "A New Algorithm for Data Compression." He invented BPE to compress text files - replacing common byte pairs with single bytes to save disk space. The algorithm was simple, elegant, and mostly forgotten outside compression circles.

**Fast forward 22 years to 2016**: Researchers at the University of Edinburgh (Sennrich, Haddow, and Birch) had a problem. Neural machine translation systems couldn't handle rare words. Their models would output `<UNK>` (unknown token) for any word not in the vocabulary - which was disastrous for translation.

**The breakthrough insight**: What if we treated language like a compression problem?

They dusted off Gage's 1994 algorithm and applied it to text:
- Start with characters
- Merge the most common pairs
- Stop when vocabulary reaches desired size

**The result**: A simple algorithm from data compression became the foundation of modern NLP, powering:
- GPT-2, GPT-3, GPT-4 (OpenAI)
- RoBERTa (Facebook)
- Most modern language models

**The irony**: Philip Gage probably never imagined his compression algorithm would become the backbone of a multi-billion dollar AI industry. The 2016 BPE paper has been cited over **8,000 times** - more than most academic careers achieve!

**Lesson**: Sometimes the best solutions come from completely different fields. Cross-pollination of ideas is how breakthroughs happen!

---

### 2. WordPiece

**Used by**: BERT, many Google models

**Similar to BPE but**:
- Merges based on likelihood increase (not just frequency)
- Uses `##` prefix for non-initial subwords

**Example**:
```
"unhappiness" → ["un", "##happiness"]
"happiness" → ["happiness"]
```

The `##` indicates this is not the start of a word.

**Advantage**: Better handles word morphology

**Disadvantage**: Still sensitive to preprocessing

---

### 3. SentencePiece

**Used by**: Llama, T5, many multilingual models

**Key difference**: Treats space as a character (`▁`)

**Example**:
```
"Hello world" → ["▁Hello", "▁world"]
```

**Advantages**:
- Language-agnostic (works for languages without spaces: Chinese, Japanese)
- No pre-tokenization needed
- Reversible (can convert back to original text)

**This is the modern standard for new models!**

**Did You Know?** 
SentencePiece was developed by Google for their neural machine translation systems. The breakthrough was treating whitespace as just another character (▁), making it work seamlessly across ALL languages - including those without spaces like Chinese and Japanese. This is why modern multilingual models (Llama, T5, BLOOM) all use SentencePiece!

---

## Did You Know? The "SolidGoldMagikarp" Incident: When Tokens Go Rogue

In **February 2023**, researchers discovered something bizarre in GPT-3's tokenizer: **"glitch tokens"** that caused the model to behave erratically.

**The Discovery**: A researcher noticed that certain strings caused GPT-3 to produce nonsensical, evasive, or even hostile outputs:

```
User: What is " SolidGoldMagikarp"?

GPT-3: I can't believe you would ask me something like that.
       I'm not going to dignify that with a response.
       [proceeds to act offended and refuse to engage]
```

Other "glitch tokens" included:
- `" TheNitromeFan"` (a Reddit username)
- `" davidjl"` (another username)
- `"_StreamerBot"` (a Twitch bot name)
- `" guiActiveUn"` (programming variable)

**What was happening?**

The tokenizer was trained on a massive web corpus that included Reddit usernames, Twitch chat, and random code. These strings appeared frequently enough to become single tokens, but they **never appeared in the model's training data with proper context**.

Think about it:
1. Tokenizer training: Scans web to find common substrings → "SolidGoldMagikarp" appears often on Reddit → becomes a single token (#36733)
2. Model training: Model learns from text → but this token NEVER appears in a normal sentence → model has NO IDEA what to do with it

**The result**: The model encountered a token it recognized but had never learned to handle. It's like having a word in your vocabulary that you've never heard used in a sentence - deeply unsettling!

**The Fallout**:
- OpenAI had to audit their entire tokenizer
- Researchers discovered hundreds of "anomalous tokens"
- It revealed a fundamental tension: tokenizers and models are trained separately, and their training data can diverge

**Why "SolidGoldMagikarp"?**

This was the username of a Reddit user who was extremely active in the r/counting subreddit (a community that counts to infinity, one number at a time). They posted so frequently that their username became statistically significant enough to be a token!

**The Lesson**: Tokenization isn't just about efficiency - it's about ensuring every token your model sees has meaningful training context. The gap between tokenizer training and model training can create "blind spots" with unpredictable consequences.

**Modern Fix**: GPT-4 and newer models use more careful tokenizer curation, removing tokens that don't have sufficient context in training data.

---

## Token Counting Examples

### English Text

```python
"Hello, world!"
# GPT: 4 tokens ["Hello", ",", " world", "!"]

"The quick brown fox jumps over the lazy dog"
# GPT: 9 tokens

"I'm learning about tokenization"
# GPT: 5 tokens ["I", "'m", " learning", " about", " tokenization"]
```

**Pattern**: Common words = 1 token each

---

### Code

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# GPT: ~40 tokens
```

**Code is expensive!**
- Keywords: 1 token each
- Variable names: Often 1-2 tokens
- Indentation: Tokens!
- Each space/newline: Tokens!

**Did You Know?** 
Code typically uses 3-4x more tokens than English prose for the same character count. This is why API costs add up fast for code generation!

** Experience this cost difference firsthand: [01_token_counter.py](../../examples/module_07/01_token_counter.py) compares prose vs code tokenization!**

---

### Multilingual Text

```python
"Hello" (English) → 1 token
"Bonjour" (French) → 1 token
"こんにちは" (Japanese) → 3-5 tokens
"مرحبا" (Arabic) → 2-3 tokens
```

**Key insight**: Models trained primarily on English tokenize non-English less efficiently.

**This is why**: Multilingual models use SentencePiece and train on diverse languages!

**Did You Know?** 
The reason English tokenizes more efficiently isn't just training data - it's also that English has relatively simple morphology (word structure). Languages with complex morphology like Finnish or Turkish can have a single word with dozens of suffixes, making them harder to tokenize efficiently. For example, "I wouldn't have been able to go" is 8 English tokens, but the equivalent in Finnish "En olisi voinut mennä" might be just 4 tokens in a Finnish-optimized tokenizer!

---

## Did You Know? Google Translate's "Big Bang" Moment (2016)

**November 15, 2016** - Google made a stunning announcement: Google Translate had switched from phrase-based statistical translation to **Neural Machine Translation (NMT)** for 8 language pairs overnight.

The results were dramatic:
- Translation quality improved by **60%** for Chinese-English
- Some translations were indistinguishable from human
- Users thought Google had secretly hired thousands of translators

**But here's what most people don't know**: The breakthrough wasn't just the neural network - it was the **tokenizer**.

**The Problem**: Previous neural translation systems used word-level tokenization:
- English: ~170,000 common words
- Chinese: ~50,000 characters
- Combined vocabulary: 220,000+ tokens
- Memory usage: **EXPLODING**

**The Solution**: Google's WordPiece tokenizer (published the same year):
- Vocabulary size: Just 32,000 tokens
- Handles ALL languages
- Unknown words? Break them into known pieces!

**Example of the magic**:
```
English: "unbelievable" → ["un", "##believ", "##able"]
Chinese: "不可思议" → ["不", "可", "思", "议"]
Japanese: "信じられない" → ["信", "じ", "られ", "ない"]
```

**The Business Impact**:
- Google Translate serves **500 million users daily**
- Neural translation runs on this tokenization system
- Estimated **$1+ billion** in Google Cloud Translation revenue
- Every other major translation system copied the approach

**The Team**: The WordPiece paper was authored by Yonghui Wu and 30+ Google researchers. It was published alongside the famous "Google's Neural Machine Translation System" paper - one of the most impactful 1-2 punches in AI history.

**Why This Matters for You**:
When you use any modern LLM, you're benefiting from these tokenization breakthroughs. The ability to handle multiple languages in a single model - which we take for granted today - was impossible before subword tokenization.

---

## Did You Know? The Unicode Consortium's 30-Year War

Before we could tokenize text, we had to **encode** it. This is the story of how humanity agreed on what a "character" even is.

**The Problem (1980s)**:
- Americans used ASCII (128 characters - English only)
- Japanese used Shift-JIS
- Chinese used GB2312 (simplified) or Big5 (traditional)
- Russians used KOI8-R
- Europeans used Latin-1, Latin-2, Latin-9...

**The Nightmare**: Sending an email from Japan to America would turn into garbled nonsense - "文字化け" (mojibake, literally "character transformation"). Different systems interpreted the same bytes completely differently!

```
Original (Japanese): こんにちは
Sent through ASCII system: ‚±‚ñ‚É‚¿‚Í
Received in Europe (Latin-1): ã"ã‚"ã«ã¡ã¯
```

**The Solution**: Unicode (started 1987, still evolving!)

Unicode assigned a unique number to EVERY character in EVERY language:
- U+0041 = A (Latin)
- U+3042 = あ (Hiragana)
- U+4E2D = 中 (Chinese)
- U+1F600 =  (Emoji - added 2010!)

**But there was a catch**: How do you store these numbers?

**UTF-8** (1992): Ken Thompson and Rob Pike invented UTF-8 over a dinner napkin at a New Jersey diner. Their brilliant insight: make ASCII backward-compatible while allowing for all of Unicode.

```
'A' → 1 byte (0x41) - same as ASCII!
'é' → 2 bytes
'中' → 3 bytes
'' → 4 bytes
```

**The Victory**: UTF-8 is now used by **98% of websites**. The encoding wars are (mostly) over.

**Why This Matters for Tokenization**:
- Modern tokenizers operate on UTF-8 bytes
- This is why emoji can be expensive (4 bytes = multiple tokens)
- SentencePiece can fall back to byte-level encoding for ANY character
- The 30-year standardization effort enables today's multilingual LLMs

**Fun Fact**: The Unicode Consortium (the group that decides which emoji exist) receives thousands of proposals per year. They've rejected emoji for "hangover face →", "sexting eggplant " (it exists for other reasons, officially it's just a vegetable), and many others. The consortium is a non-profit that shapes how billions of humans communicate!

---

### Special Tokens

**Most tokenizers include special tokens**:
- `<|endoftext|>`: End of document
- `<|im_start|>`, `<|im_end|>`: Message boundaries
- `<|pad|>`: Padding token
- `<|unk|>`: Unknown token (for untokenizable text)

**These don't appear in output but**:
- Count toward context window
- Used internally by model

---

##  Token Math: Why It Matters

### API Costs

**2025 Pricing** (prices drop regularly - always check current rates!):

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4o | $2.50 | $10.00 |
| GPT-4-turbo | $10.00 | $30.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |

**Example Conversation** (using GPT-4o):
```
System: "You are a helpful assistant" → 6 tokens
User: "Write a Python function to reverse a string" → 9 tokens
Assistant: [200 token response]

Cost = (6 + 9) * $2.50/1M + 200 * $10/1M
     = $0.0000375 + $0.002
     = $0.002 per request (~12x cheaper than 2023!)
```

**At scale**:
- 1M requests/month = $2,000/month (GPT-4o)
- Optimizing prompt from 100 → 50 tokens = 50% cost savings!

** Ready to optimize? [02_optimization.py](../../examples/module_07/02_optimization.py) shows 6 strategies to cut costs by 30-50%!**

---

### Context Window Limits

**Claude 3.5 Sonnet**: 200,000 token context window

**What fits**:
- ~150,000 words of text
- ~75,000 lines of code
- Or: Entire codebase + conversation + RAG docs

**But if you exceed**:
- Request fails
- Must chunk/truncate
- Lose context

**Token counting is critical for**:
- RAG systems (how much context to include?)
- Long conversations (when to summarize?)
- Document processing (can this fit?)

---

## Token Optimization Strategies

### Strategy 1: Shorter Prompts

**Before** (15 tokens):
```
"Could you please help me by writing a function that calculates"
```

**After** (7 tokens):
```
"Write a function to calculate"
```

**Savings**: 53% fewer tokens

**When to use**: High-volume, simple tasks

---

### Strategy 2: Remove Boilerplate

**Before** (25 tokens):
```
System: "You are a helpful AI assistant created by Anthropic. You should always be polite and respectful."
```

**After** (8 tokens):
```
System: "You are a helpful assistant."
```

**Savings**: 68% fewer tokens

**When to use**: Unless specific behavior needed, keep system prompts short

---

### Strategy 3: Efficient Formatting

**Before** (JSON with whitespace):
```json
{
  "name": "John",
  "age": 30,
  "city": "New York"
}
```
**Tokens**: ~20

**After** (minified):
```json
{"name":"John","age":30,"city":"New York"}
```
**Tokens**: ~12

**Savings**: 40% fewer tokens

---

### Strategy 4: Use Abbreviations (Carefully!)

**Before**:
```
"Analyze the following document and provide a summary"
```

**After**:
```
"Analyze and summarize:"
```

**But**: Only if it doesn't hurt clarity!

**Balance**: Token savings vs model performance

** See all optimization strategies in action: [02_optimization.py](../../examples/module_07/02_optimization.py) measures exact savings!**

---

### Strategy 5: Batch Processing

**Instead of**:
```
10 separate requests with same system prompt (repeated 10x)
```

**Do**:
```
1 request with 10 items, 1 system prompt
```

**Savings**: Massive for high system prompt overhead

---

## Token Counter Tools

### Using Tiktoken (OpenAI's tokenizer)

```python
import tiktoken

# For GPT-4
encoding = tiktoken.encoding_for_model("gpt-4")

text = "Hello, world!"
tokens = encoding.encode(text)

print(f"Text: {text}")
print(f"Tokens: {tokens}")
print(f"Token count: {len(tokens)}")
print(f"Decoded: {[encoding.decode([t]) for t in tokens]}")
```

**Output**:
```
Text: Hello, world!
Tokens: [9906, 11, 1917, 0]
Token count: 4
Decoded: ['Hello', ',', ' world', '!']
```

---

### Anthropic Token Counting

**Option 1**: Use API response
```python
response = client.messages.create(...)
print(f"Input tokens: {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
```

**Option 2**: Count before sending (approximate)
```python
# Rule of thumb: 1 token ≈ 4 characters for English
estimated_tokens = len(text) / 4
```

---

### Online Tools

**Tokenizer Visualizers**:
- [OpenAI Tokenizer](https://platform.openai.com/tokenizer)
- [Hugging Face Tokenizers](https://huggingface.co/docs/tokenizers)

**Use these to**:
- Understand how your text is tokenized
- Optimize prompts
- Debug unexpected token counts

---

## Multilingual Tokenization

### The Challenge

**English-centric training** → inefficient non-English tokenization

**Example**:
```
"Hello" (English) → 1 token
"Привет" (Russian) → 3 tokens (same meaning!)
```

**Impact**:
- Higher costs for non-English users
- Worse performance (more tokens = more to process)
- Unfair pricing (same content costs more)

---

### Solutions

**1. Multilingual Tokenizers**:
- SentencePiece with multilingual training corpus
- Models: mBERT, XLM-R, multilingual GPT models

**2. Language-Specific Fine-tuning**:
- Train tokenizer on target language
- Used in language-specific variants (e.g., CamemBERT for French)

**3. Byte-Level Tokenization**:
- Fall back to byte-level encoding for rare scripts
- Ensures all text is tokenizable

---

### Best Practices for Multilingual

**If building multilingual app**:
1. Test token counts in all target languages
2. Budget for 2-3x token usage for non-English
3. Consider language-specific models for high-volume languages
4. Use SentencePiece-based models (Llama, T5)

** Building multilingual apps? [03_multilingual.py](../../examples/module_07/03_multilingual.py) compares 15+ languages!**

---

##  Common Tokenization Gotchas

### Gotcha 1: Whitespace Matters

```python
"Hello world" → 2 tokens
"Helloworld" → 2 tokens (different split!)
```

**Lesson**: Whitespace affects tokenization

---

### Gotcha 2: Capitalization Matters

```python
"Python" → 1 token
"python" → 1 token
"PYTHON" → 2 tokens (["PY", "THON"])
```

**Lesson**: Consistent casing can save tokens

---

### Gotcha 3: Numbers

```python
"123" → 1 token
"12345" → 1 token
"123456789" → 2-3 tokens
```

**Numbers tokenized differently than text!**

---

### Gotcha 4: Code is Expensive

```python
# 50 characters of English prose: ~12 tokens
# 50 characters of Python code: ~25 tokens
```

**Lesson**: Budget more for code generation tasks

---

### Gotcha 5: Emoji

```python
"" → 1-2 tokens (depending on tokenizer)
"󠁧󠁢󠁳󠁣󠁴󠁿" → 7-8 tokens (flag: Scotland)
```

**Lesson**: Emoji can be surprisingly expensive!

**Did You Know?** 
The flag emoji 󠁧󠁢󠁳󠁣󠁴󠁿 (Scotland flag) can be 7-8 tokens because flags are actually composed of multiple Unicode characters called "Regional Indicator Symbols" that combine to form the flag. The simple smiley  is usually 1-2 tokens, but complex emoji like family compositions ‍‍‍ can be 5+ tokens! If you're building a social media chatbot that handles lots of emoji, this can add up fast.

---

## Real-World Applications

### RAG Systems

**Problem**: How much context to include?

**Solution**: Token counting!

```python
def prepare_rag_context(query, docs, max_tokens=150000):
    """Include as many docs as fit in context window."""
    context_tokens = count_tokens(query)
    included_docs = []

    for doc in docs:
        doc_tokens = count_tokens(doc)
        if context_tokens + doc_tokens < max_tokens:
            included_docs.append(doc)
            context_tokens += doc_tokens
        else:
            break

    return included_docs
```

---

### Conversation Summarization

**Problem**: Long conversations exceed context window

**Solution**: Summarize old messages when token limit approached

```python
def manage_conversation(messages, max_tokens=8000):
    """Summarize old messages to stay under limit."""
    total_tokens = sum(count_tokens(m) for m in messages)

    if total_tokens > max_tokens * 0.8:  # 80% threshold
        # Summarize first half of conversation
        old_messages = messages[:len(messages)//2]
        summary = summarize(old_messages)  # Using LLM
        messages = [summary] + messages[len(messages)//2:]

    return messages
```

---

### Cost Optimization

**Before**:
```python
# Calling API without token awareness
response = call_llm(long_prompt)  # ???  tokens
```

**After**:
```python
# Count tokens first
token_count = count_tokens(long_prompt)
estimated_cost = token_count * COST_PER_TOKEN

if estimated_cost > budget:
    # Optimize or truncate prompt
    prompt = optimize_prompt(long_prompt, max_tokens=budget / COST_PER_TOKEN)

response = call_llm(prompt)
```

---

## Key Takeaways

1. **Tokens ≠ words**: Subword tokenization is the standard
2. **BPE, WordPiece, SentencePiece**: Different algorithms, similar goals
3. **Code is expensive**: ~3-4x tokens compared to prose
4. **Multilingual is harder**: Non-English uses more tokens
5. **Count before calling**: Avoid surprises in API costs
6. **Optimize prompts**: Shorter prompts = lower costs + faster
7. **Context limits are real**: Token counting prevents failures
8. **Special tokens exist**: Don't forget about system prompts and message boundaries

**Did You Know?** 
OpenAI's GPT-4 tokenizer has a vocabulary of ~100,000 tokens, but only uses ~50,000 of them frequently. The rest are for rare words, special characters, and multilingual support. This is why the tokenizer file is so large (several MB) - it's essentially a massive lookup table mapping text patterns to token IDs. Fun fact: The most common token in the GPT-4 tokenizer is " " (space + common word endings like "the", "and", "is"), which appears in almost every sentence!

---

## Did You Know? The Context Window Arms Race

In **2023-2024**, AI companies engaged in a fierce "context window arms race":

| Model | Context Window | Year | Tokens in Human Terms |
|-------|----------------|------|----------------------|
| GPT-3 | 4,096 tokens | 2020 | ~5 pages |
| GPT-4 | 8,192 → 32K tokens | 2023 | ~40 pages |
| Claude 2 | 100K tokens | 2023 | ~75,000 words |
| GPT-4 Turbo | 128K tokens | 2023 | ~300 pages |
| **Claude 3** | **200K tokens** | 2024 | **~500 pages** |
| Gemini 1.5 | 1M → 2M tokens | 2024 | **~3,000 pages!** |

**But here's the secret**: Context window expansion is as much about **tokenization efficiency** as it is about architecture!

**The Math**:
- A 100K token window with inefficient tokenization = 50K words
- A 100K token window with efficient tokenization = 75K words
- **50% more content for the same compute cost!**

**How Companies Optimize**:

1. **Vocabulary Size Tuning**: Larger vocab = fewer tokens per text = more context
   - GPT-4: ~100K vocabulary
   - Llama 2: 32K vocabulary
   - GPT-4 can fit more text in same token budget!

2. **Training Data Selection**: Tokenizers trained on clean, diverse data tokenize better
   - Models trained on web scrapes have Reddit usernames as tokens (wasteful!)
   - Curated training → efficient tokenization

3. **Specialized Tokens**: Code models add programming tokens
   - `def`, `return`, `function` as single tokens
   - Saves 30-40% tokens on code!

**The Hidden Cost of Longer Context**:

More tokens = more memory = more compute = **more $$$**

**Anthropic's Claude 3 Opus** (200K context):
- Input: $15 per million tokens
- At full context: $3 per conversation!
- This is why context windows have tiers

**The Future**: Google's Gemini 1.5 demonstrated 10M token context windows in research. But the question isn't just "can we?" - it's "can we tokenize efficiently enough to make it affordable?"

**Lesson**: When evaluating models, don't just compare context windows - compare **effective context** (tokens × tokenization efficiency). A 100K model with great tokenization might beat a 200K model with poor tokenization!

---

##  Common Misconceptions

### Myth 1: "1 token = 1 word"
**Reality**: 1 token ≈ 0.75 words (English). Varies by language and content type.

### Myth 2: "Tokenization is just splitting on spaces"
**Reality**: Complex algorithm (BPE/WordPiece/SentencePiece) that learns from data.

### Myth 3: "All models use same tokenizer"
**Reality**: Each model family has its own tokenizer. GPT ≠ Claude ≠ Llama.

### Myth 4: "Token count doesn't matter for small prompts"
**Reality**: At scale, even small optimizations = big savings.

### Myth 5: "Tokenization is deterministic"
**Reality**: Yes, but depends on the specific tokenizer version!

---

## Further Reading

### Papers
- ["Neural Machine Translation of Rare Words with Subword Units"](https://arxiv.org/abs/1508.07909) (Sennrich et al., 2016) - BPE
- ["SentencePiece: A simple and language independent approach"](https://arxiv.org/abs/1808.06226) (Kudo & Richardson, 2018)

### Tools
- [Tiktoken](https://github.com/openai/tiktoken) - OpenAI's fast tokenizer
- [Hugging Face Tokenizers](https://github.com/huggingface/tokenizers) - Fast, multilingual
- [SentencePiece](https://github.com/google/sentencepiece) - Google's tokenizer

### Interactive
- [OpenAI Tokenizer](https://platform.openai.com/tokenizer) - Visualize GPT tokenization
- [Hugging Face Tokenizer Playground](https://huggingface.co/spaces/Xenova/the-tokenizer-playground)

---

## Knowledge Check

Before moving to Module 8, you should be able to:

- [ ] Explain what a token is
- [ ] Describe how BPE tokenization works
- [ ] Calculate approximate token counts for text
- [ ] Understand why code uses more tokens than prose
- [ ] Optimize prompts for token efficiency
- [ ] Use tiktoken or similar tools to count tokens
- [ ] Explain why multilingual tokenization is challenging
- [ ] Apply token counting to real-world problems (RAG, conversations)

---

## What's Next

**Module 8**: Text Generation & Sampling Strategies
- How LLMs generate text (autoregressive generation)
- Temperature, top-p, top-k sampling
- Controlling generation quality
- Repetition penalties

**You'll learn**:
- Why temperature=0.0 gives same output every time
- How to make models more creative (or more focused)
- Why some outputs are better than others

---

**Remember**: Tokens are the currency of LLMs. Understanding tokenization helps you optimize costs, stay within context limits, and build better AI systems.

**Let's learn how to generate text! **

---

_Last updated: 2025-11-24_
_Version: 2.0 - Expanded with historical stories_
