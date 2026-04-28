---
title: "Chapter 10: The Imitation Game"
description: "Between 1947 and 1952, Alan Turing built a behavioural test for machine intelligence on three deliberate moves, substituting an empirical imitation game for the unanswerable question of whether machines can think."
sidebar:
  order: 10
---

The historical importance of Alan Turing's 1950 paper in *Mind* is not its prediction of a machine fooling an interrogator by the year 2000. It is an epistemic move. Between 1947 and 1952, Turing dismantled the definitional debate over the word "intelligence" and replaced it with a behavioural protocol. By routing interaction through a teleprinter and stripping away the physical body, Turing established the empirical baseline against which the progress of artificial intelligence would be measured.

## The Precursors

Turing's pivot toward an empirical test of machine intelligence was not an abrupt arrival in 1950. The philosophical groundwork and the operational shape of the test were laid out in the preceding three years.

On 20 February 1947, Turing addressed the London Mathematical Society. Speaking on the design of the Automatic Computing Engine (ACE) at the National Physical Laboratory (NPL), Turing confronted the assumption that a machine must be flawless to be considered intelligent. In his view, "if a machine is expected to be infallible, it cannot also be intelligent." The demand for absolute precision was a trap, holding the machine to a standard that human intelligence did not meet. He concluded that "fair play must be given to the machine," proposing that true intelligence resided in the learning loop, and that "what we want is a machine that can learn from experience."

During the same lecture, Turing estimated the memory capacity of the human brain to be "about ten thousand million binary digits"—roughly $10^{10}$ bits. By contrast, the total storage capacity of the ACE's mercury delay lines was "about 200,000 binary digits," which Turing wryly noted was "probably comparable with the memory capacity of a minnow." Nevertheless, he argued that a more modest storage of "a few million digits" might suffice for limited demonstrations of intelligence, such as playing a game of chess.

In 1948, Turing drafted an unpublished NPL report titled *Intelligent Machinery*. The opening pages systematically listed five common objections to machine intelligence—human pride, Promethean religious feeling, the limitations of recent machinery, Gödel-style mathematical theorems, and the idea that intelligence is merely a "reflection" of the creator—and provided a "Refutation of Some Objections" for each.

More critically, the 1948 report introduced the concept of "unorganized machines." These were discrete-state random networks constructed from simple logical units, representing one of the earliest examples of connectionist models. Turing proposed the human infant cortex as a biological analogue to such an unorganized network. The challenge was how to organize it. Turing framed the education of machinery through a system of rewards and punishments: "events which shortly preceded the occurrence of a punishment signal are unlikely to be repeated, whereas a reward signal increased the probability of repetition of the events which led up to it." He distinguished between "screwdriver interference"—physically rewiring the machine—and "paper interference," the communication of instructions. Education, he noted, was largely a matter of paper interference.

At the very end of the *Intelligent Machinery* report, in a section titled "Intelligence as an Emotional Concept," Turing outlined a two-room chess experiment that served as a proto-imitation game. He imagined three participants: a poor chess player (A), a mathematician operating a paper machine (B), and another poor chess player acting as an observer (C). The observer plays one game against A and one against the paper machine, with moves communicated between two separate rooms. "C may find it quite difficult to tell which he is playing," Turing wrote. He added a revealing note about this setup: "This is a rather idealized form of an experiment I have actually done." Two years before the publication of his famous paper, the operational shape of the test—the separated rooms, the hidden machine, the human observer trying to tell them apart—was already taking form.

## The Parlour Game

In October 1950, Turing published "Computing Machinery and Intelligence" in the philosophy journal *Mind* (volume 59). The paper begins with a deliberate subversion: "I propose to consider the question, 'Can machines think?'" 

Having posed the question, Turing immediately rejects the method of finding an answer by surveying the common usage of the words "machine" and "think." He dismisses the definitional debate as an "absurd" exercise akin to a Gallup poll. Instead, he writes, "such a definition I shall replace the question by another, which is closely related to it and is expressed in relatively unambiguous words."

This new question is the Imitation Game. In its original form, the game is a Victorian parlour amusement played with three people: a man (A), a woman (B), and an interrogator (C) who may be of either sex. The interrogator stays in a separate room from A and B, knowing them only by the labels X and Y. The interrogator's task is to determine which is the man and which is the woman. The game is asymmetric: A's object is to make the interrogator identify wrongly, while B's object is to help the interrogator decide correctly.

To ensure the game tests only intellectual capacity, the interface must be severely constrained. "In order that tones of voice may not help the interrogator," Turing specifies, "the answers should be written, or better still, typewritten. The ideal arrangement is to have a teleprinter communicating between the two rooms." Alternatively, an intermediary may relay questions and answers.

Having established this gender-disambiguation game as the baseline of human deception and detection, Turing makes his crucial pivot: "We now ask the question, 'What will happen when a machine takes the part of A in this game?' Will the interrogator decide wrongly as often when the game is played like this as he does when the game is played between a man and a woman? These questions replace our original, 'Can machines think?'"

The gender structure of the 1950 setup establishes the control group. The machine does not have to achieve absolute deception. It only has to fool the interrogator as often as a man playing the same game would fool the interrogator. The human baseline of deception is the metric against which the machine's performance is substituted and judged.

## The Argumentative Spine

The middle sections of the *Mind* paper form an argumentative spine designed to defend the Imitation Game from theoretical attacks. In Section 2, Turing provides a "Critique of the New Problem," defending the decision to decouple intelligence from physical embodiment. "No engineer or chemist claims to be able to produce a material which is indistinguishable from the human skin," he observes. And even if such a synthetic skin could be invented, "we should feel there was little point in trying to make a 'thinking machine' more human by dressing it up in such artificial flesh." The teleprinter constraint operationalises this decoupling: it prevents the interrogator from seeing, touching, or hearing the competitors, ensuring the test measures purely symbolic and linguistic behaviour.

Sections 3 through 5 reframe the problem around digital computers. Turing advances a universality argument: any single discrete-state machine equipped with adequate storage and speed can mimic the behaviour of any other. To ground this theoretical point in contemporary reality, he references the storage parameters of the Manchester machine, noting its 2560 wheels and its 1280-digit capacity per wheel.

Section 6, "Contrary Views on the Main Question," catalogues nine distinct objections to the idea of thinking machines, ranging from Theological and Mathematical arguments to Arguments from Extra-Sensory Perception. By systematically rebutting each, Turing demonstrates that his behavioural test is robust against the era's prevailing skepticisms. 

One of the rebuttals Turing engages most fully is the objection attributed to Lady Ada Lovelace, who wrote that the Analytical Engine "has no pretensions to originate anything." The core of the Lovelace objection is that machines can only do whatever we know how to order them to perform; they cannot surprise us. Turing counters this by observing that machines take him by surprise frequently. He pushes further, questioning whether a mind can be "supercritical" in the sense of an atomic pile: "An idea presented to such a mind that may give rise to a whole 'theory' consisting of secondary, tertiary and more remote ideas." The implication is that a sufficiently complex machine, capable of learning, might achieve this supercritical state and originate new concepts.

Turing also addresses the "Argument from Consciousness," which asserts that a machine must feel emotions and be aware of its own thoughts to be considered intelligent. This view was prominently championed at the time by Geoffrey Jefferson, whose 1949 Lister Oration, "The Mind of Mechanical Man," had attacked machine-intelligence claims on biological grounds. Turing deflects the demand for inner experience by pointing out its solipsism: the only way to be certain that a machine thinks is to be the machine. Since we routinely grant that other humans think based purely on their outward behaviour, fair play demands we extend the same behavioural courtesy to the machine.

## The Prediction and the Child Machine

The most frequently quoted passage of the *Mind* paper occurs at the opening of Section 6, where Turing offers a specific, quantitative forecast.

"I believe that in about fifty years' time it will be possible, to programme computers, with a storage capacity of about $10^9$, to make them play the imitation game so well that an average interrogator will not have more than 70 per cent chance of making the right identification after five minutes of questioning."

This is not a binary finish line for artificial intelligence. It is a frequency claim about a population of average interrogators, bounded by a five-minute time limit, set against an estimated storage capacity. Immediately following this, Turing makes a companion claim about cultural reception rather than engineering: "I believe that at the end of the century the use of words and general educated opinion will have altered so much that one will be able to speak of machines thinking without expecting to be contradicted."

Turing was well aware that no 1950-vintage machine could play the game. He estimated that a human programmer could write about a thousand digits of code a day, meaning it would take sixty workers fifty years of flawless work to programme the imitation player by hand. "Some more expeditious method seems desirable," he noted. 

This leads to Section 7, "Learning Machines," which reorients the entire engineering problem. Rather than attempting to programme an adult mind from scratch, Turing proposes programming a child mind and subjecting it to "an appropriate course of education."

Turing divides the mind into three components: "(a) The initial state of the mind, say at birth, (b) The education to which it has been subjected, (c) Other experience, not to be described as education, to which it has been subjected." He returns to the system of rewards and punishments he had outlined in 1948, remarking modestly that he had done "some experiments with one such child machine, and succeeded in teaching it a few things, but the teaching method was too unorthodox for the experiment to be considered really successful." To demonstrate that education does not strictly require conventional sensory embodiment, he cites the example of Helen Keller, noting that communication in both directions is sufficient.

Turing draws an explicit analogy between this educational design loop and biological evolution. The structure of the child machine corresponds to hereditary material; changes made to the child machine are mutations; and the judgment of the experimenter takes the role of natural selection. 

As the paper concludes, Turing identifies two possible paths forward. One approach would focus on highly abstract activities, such as chess. The alternative would be to provide the machine "with the best sense organs that money can buy," and teach it to understand and speak English. Refusing to declare a winner between the symbolic and the embodied approaches, he writes: "Again I do not know what the right answer is, but I think both approaches should be tried."

The final sentence of the *Mind* paper reads: "We can only see a short distance ahead, but we can see plenty there that needs to be done."

## Aftermath: BBC and Reframing

Turing defended his empirical framing in public after the paper's publication. On 14 January 1952, the BBC Third Programme broadcast a four-way conversation titled "Can Automatic Calculating Machines Be Said To Think?" The panel included Turing, his Manchester colleague Max Newman, the Cambridge philosopher R. B. Braithwaite, and Geoffrey Jefferson. 

The broadcast brought the theoretical debates of the *Mind* paper into real-time collision. Jefferson reportedly advanced biological objections, continuing the argument that thinking required a nervous-system substrate, while Turing defended the behavioural-test framing against these demands for inner experience. The presence of a mathematician, a neurosurgeon, a philosopher, and the test's author established the cross-disciplinary register that would characterize debates over artificial intelligence in the decades to follow.

Over the next fifty years, the reception of Turing's paper shifted through various disciplines, as surveyed by researchers Ayse Pinar Saygin, Ilyas Cicekli, and Varol Akman. In the 1960s and 1970s, the literature was dominated by philosophical responses. By the 1980s, the focus moved toward computational critiques, and in the 1990s, the debate turned toward anthropomorphism and the specific mechanics of the game.

During this half-century, the "Imitation Game" underwent a gradual rebrand. Later commentators universally adopted the term "Turing Test." Along with the name change came a subtle structural shift. The original 1950 setup—where the machine takes the part of a man trying to imitate a woman—was frequently simplified into a straightforward human-versus-machine test. 

Whether this abstraction was faithful to Turing's intent remains a subject of active debate. The philosopher Diane Proudfoot has argued that subsequent commentary actively stripped out the gender-disambiguation structure upon which Turing built the test. In her reading, the "abstracted" Turing Test, where the interrogator merely tries to distinguish human from machine, is a fundamentally different test from what Turing proposed. Other commentators have treated the gender axis as a vestigial quirk that was meant to be abstracted away. 

Regardless of whether the gender structure was load-bearing, Turing's core epistemic move survived. By substituting an empirical, teleprinter-bound imitation game for the unanswerable question of whether machines can think, Turing set an operational baseline for the field.
