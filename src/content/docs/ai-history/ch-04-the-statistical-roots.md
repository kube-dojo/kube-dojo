---
title: "Chapter 4: The Statistical Roots"
description: "How Andrey Markov's analysis of a Russian poem laid the distant statistical groundwork for predicting text."
sidebar:
  order: 4
---

# Chapter 4: The Statistical Roots

Decades before Turing or Shannon began their work, an entirely different mathematical lineage was already at play in Russia. It was not concerned with binary switches, absolute truths, or universal machines. Instead, it was concerned with the messy, unpredictable nature of human language and probability.

This alternate path would remain largely disconnected from the hardware of the era for decades. Yet, the mathematical concept born from it—the Markov Chain—would eventually become the statistical ancestor of predictive text and modern Large Language Models. To understand how machines generate language today, we must look back to the early 20th century, when a Russian mathematician decided to mathematically prove the laws of probability against theological objections.

## The Theological Dispute

Andrey Markov was a brilliant and combative mathematician at St. Petersburg University. He was deeply invested in probability theory, specifically the Law of Large Numbers. This law states that as an experiment (like flipping a coin) is repeated many times, the average of the results will eventually converge on the expected value.

In the early 20th century, probability theory was not just a mathematical discipline; it was a philosophical and theological battleground. Markov’s primary rival was Pavel Nekrasov, a mathematician who had become a theologian. 

As detailed in their original, heated correspondence, Nekrasov argued that the Law of Large Numbers only applied to entirely independent events—like a coin flip, where the previous flip has no influence on the next. Nekrasov claimed that human actions, because they were an expression of free will, were dependent and connected, and therefore could only be predicted or understood through divine intervention, not pure mathematics.

Markov was incensed by this mystical interpretation. He wanted to mathematically prove Nekrasov wrong. He needed to demonstrate that the Law of Large Numbers still applied even when events were strictly dependent on one another—when the next action was directly influenced by the previous one. 

## The 1906 Proof

Markov attacked the problem with pure mathematics. In a foundational 1906 paper titled *Extension of the Law of Large Numbers to Dependent Variables*, he developed a rigorous mathematical framework. 

He proved that a sequence of dependent events—where the probability of a future state depends explicitly on the current state—still adheres to strict probabilistic limits. The "Markov Chain" was born. The mathematics proved unequivocally that the concept of "free will" and dependent actions did not grant immunity from the unfeeling, calculable laws of statistics.

He had won the mathematical debate, but he needed a public-facing, undeniable demonstration to illustrate his proof. He needed a real-world dataset of dependent events, and he chose human language. In any language, the probability of the next letter is not an independent coin flip; it is highly dependent on the letter that just preceded it. 

## Counting Pushkin

In 1913, serving as the applied illustration of his 1906 proof, Markov sat down with a copy of Alexander Pushkin’s classic novel in verse, *Eugene Onegin*. 

He did not read it for its poetry. He read it as a dataset. Markov stripped away the meaning, the grammar, and the emotion of the text. He ignored the punctuation and the spaces. He reduced Pushkin’s masterpiece to a continuous, uninterrupted sequence of letters.

Markov then manually categorized every single letter as either a vowel or a consonant. He counted 20,000 letters by hand, meticulously tracking the transitions between them. He wanted to know: if you are currently looking at a consonant, what is the exact mathematical probability that the very next letter will be a vowel? 

He discovered that in *Eugene Onegin*, if the current letter is a consonant, there is a 66% chance the next letter will be a vowel. If the current letter is a vowel, there is an 87% chance the next letter will be a consonant. 

But Markov did not stop at simple one-step transitions. In the same 1913 paper, he explored "2-step" (second-order) chains. He calculated the probabilities based not just on the immediate preceding letter, but on the preceding *two* letters, deepening the statistical context of the prediction.

> [!note] Pedagogical Insight: The Chain of Probability
> This is the essence of a Markov Chain. It is a mathematical system that transitions from one state to another, where the probability of the next state depends *only* on a strictly defined local history. In a first-order chain, you only need to know where you are right now. In a second-order (2-step) chain, you look at the current two-symbol window. Markov proved that you do not need to understand the entire history of a sequence (or the deep grammatical rules of a language) to make a statistically accurate prediction about what comes next.

## The Ancestry of Generation

Markov had successfully proved his point against Nekrasov: probability mathematics applied perfectly to dependent sequences. But in doing so, he had inadvertently planted a theoretical seed that would heavily influence information theory and AI.

Three decades later, in 1948, Claude Shannon would explicitly cite Markov’s n-gram statistics in his legendary formulation of Information Theory. Shannon recognized that Markov’s chains of probability were the key to modeling English text mechanically.

Markov’s 1913 study offered the mathematical foundation for an entirely different paradigm. Decades later, statistical language models would build on this same local-transition idea, demonstrating that language generation did not necessarily require a machine to "understand" grammar, syntax, or meaning. It only required the ability to calculate the statistical likelihood of the next token based on the current one.

Markov's manual counting of 20,000 characters was the absolute physical limit of his era. The math of predictive sequences was proven, but without massive digital memory and processing infrastructure to scale it, it could not be applied to entire words, sentences, or billions of documents. The concept would lay waiting for the computational power and the massive datasets of the digital age to finally catch up to the mathematics.

## Sources

### Primary
- **Markov, Andrey. "Extension of the Law of Large Numbers to Dependent Variables." *Izvestiya Fiz.-Mat. Obsch. Pri Kazansk. Univ.*, 1906.**
- **Markov, Andrey. "An Example of Statistical Investigation of the Text Eugene Onegin." (1913).**
- **Shannon, Claude E. "A Mathematical Theory of Communication." *Bell System Technical Journal* 27 (1948).**

### Secondary
- **Sheynin, Oscar. *Russian Papers on the History of Probability and Statistics*. Berlin, 2004.**
- **Hayes, Brian. "First Links in the Markov Chain." *American Scientist*, 2013.**
- **Gleick, James. *The Information: A History, a Theory, a Flood*. Pantheon, 2011.**
