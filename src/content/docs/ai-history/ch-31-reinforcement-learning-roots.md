---
title: "Chapter 31: Reinforcement Learning Roots"
description: "How delayed reward, temporal differences, action values, and self-play turned learning from consequences into a mathematical program."
slug: ai-history/ch-31-reinforcement-learning-roots
sidebar:
  order: 31
---

# Chapter 31: Reinforcement Learning Roots

Reinforcement learning begins with a different kind of silence.

In supervised learning, the teacher can often correct the learner immediately.
This image is a seven. This sentence has this label. This output should have
been closer to that target. The lesson may still be difficult, but the feedback
arrives in a familiar form: here is the answer you should have produced.

Delayed reward is harsher. A move in a game may matter only after a long chain
of later moves. A control signal may look harmless until the system drifts
toward failure. A decision may make exploration possible now and pay off only
much later. The learner receives not a full explanation, but a consequence. The
hard question is how to assign credit backward through time.

That problem gave artificial intelligence a different mathematical root. It
joined dynamic programming, game-playing programs, adaptive control,
psychology-inspired language, temporal-difference prediction, and Markov
decision processes. Its researchers did not merely ask how to fit a function to
examples. They asked how an agent should act when the value of an action is
known only through future experience.

The roots were scattered before they became a field. Richard Bellman supplied
sequential-decision mathematics. Arthur Samuel showed that a game-playing
machine could improve an evaluation function through play. Andrew Barto,
Richard Sutton, and Charles Anderson used adaptive elements to learn a
pole-balancing control task from sparse evaluative feedback. Sutton turned
successive predictions into a learning signal. Christopher Watkins framed
delayed rewards through Markov decision processes and action values. Watkins
and Peter Dayan then gave Q-learning a convergence result in a restricted but
powerful setting.

The result was not general intelligence. It was a grammar for learning from
consequences.

> [!note] Pedagogical Insight: Reward Is Not a Label
> A label tells the learner what the right answer was. A reward says only that
> some outcome was good or bad. Reinforcement learning became difficult and
> historically important because it had to connect delayed consequences back to
> earlier actions.

## The Problem Supervision Could Not See

The central reinforcement-learning problem is easy to state and hard to solve:
an agent must learn behavior through trial-and-error interaction with a dynamic
environment. It observes a state, chooses an action, receives some feedback,
and faces the next state. The feedback may be immediate, delayed, noisy, sparse,
or misleading. The agent's task is not just to predict. It must act.

That makes the problem different from the pattern-recognition stories in the
previous chapters. Backpropagation made it plausible to train hidden
representations from examples. Universal approximation made multilayer
networks mathematically credible as function families. Convolutional networks
would show how architecture could exploit structure in images. Support vector
machines would discipline classification through margins and kernels. Statistical
speech recognition would make uncertainty operational through decoding.

Reinforcement learning entered through a different door. It asked what happens
when the learner's own action changes the data it will see next. A classifier
does not usually decide which future examples exist. An agent does. If it
explores, it may discover a better policy. If it exploits too soon, it may
settle for a mediocre one. If it explores recklessly, it may waste opportunities
or fail. The problem is not simply representation. It is behavior under
uncertainty.

The computer-science field borrowed the word "reinforcement" from a much older
behavioral vocabulary, but the meaning was not identical. The later survey by
Kaelbling, Littman, and Moore is careful on this point: the work resembles
psychology, but differs in details and in the use of the word. In AI, the
phrase became a problem class. A learner interacts with an environment, receives
reinforcement, and must improve behavior over time.

Tesauro's TD-Gammon article gives a compact version of the same problem. The
agent sees an input, produces an action or control signal, and receives a
scalar reward from the environment. When that reward comes at the end of a long
sequence, the learner faces temporal credit assignment: how much of the final
success or failure should be blamed on each earlier state and action?

That credit-assignment problem is the thread through the history. It links
checkers, pole balancing, temporal-difference learning, Q-learning, and
self-play. Each stage asks the same question in a different setting: how can a
machine learn from consequences that arrive late?

## Bellman and Samuel Give the Shape

Bellman's contribution sits at the mathematical edge of the story. In 1957, he
published "A Markovian Decision Process," a paper built around nonlinear
recurrence relations arising from a dynamic-programming process. The full
recurrence belongs to mathematics, but its historical role is enough here:
sequential decision problems could be written recursively. A current choice
could be evaluated in relation to future value.

That was the ancestry, not the whole field. Bellman did not write the later
machine-learning story by himself. Reinforcement learning would also need
experiments, games, control problems, and algorithms that learned from
experience rather than solving a fully known model. Arthur Samuel supplied an
early AI version of that sensibility.

Samuel's 1959 checkers paper is one of the great early uses of the phrase
"machine learning." The setting was concrete: a program played checkers, used
lookahead search, evaluated board positions, and adjusted its evaluation. The
abstract made the claim boldly enough. A computer could be programmed so that
it learned to play a better game than the person who wrote the program, and it
could do so in a short period of machine-playing time when given the rules, a
sense of direction, and an incomplete list of parameters.

The game mattered because exhaustive search was hopeless. Samuel described the
enormous branching of possible checkers games. A program needed a way to stop
looking ahead and score positions. That scoring function was not a decorative
feature. It was the machine's compressed judgment about future prospects. If
the evaluation improved, the play improved.

Samuel's work was not modern Q-learning. It did not contain the later
convergence theorem, the same Markov decision formalism, or the vocabulary of
state-action values that would become standard. Its importance is more basic.
It showed that a machine could improve behavior in a game by using experience
to reshape evaluation. It tied learning to play, judgment, search, and future
outcome.

The paper also showed how quickly the problem became practical. There were
board-position records, memory limits, lookahead depth, evaluation terms,
weights, and self-play arrangements. The learner did not receive a clean label
for every board position. It had to relate present positions to later results.
That is the historical bridge to reinforcement learning: not a direct identity,
but a recurring shape.

Samuel's Alpha and Beta setup sharpened that bridge. The program could use one
version of its evaluation function to play and another to compare against it.
After play, the coefficients attached to board features could be changed. Some
features were discarded and replaced. The system was not simply replaying a
fixed expert table. It was testing an evaluation of the game against experience
and changing the evaluation when experience exposed weakness.

Checkers therefore belongs in the reinforcement-learning ancestry even though it
was not yet modern reinforcement learning. A later RL textbook would use
different notation, but the practical outline was already visible. Search had to
stop before the end of the game. A value estimate had to stand in for the
future. The value estimate could be improved by play. The improvement was not a
label attached by a human teacher to every position; it was a judgment revised
through consequences.

A machine faces a position. It cannot search forever. It estimates value. It
acts. Later evidence changes the estimate.

## The Pole-Balancing Critic

The next root was not a board game. It was a control problem.

In 1983, Barto, Sutton, and Anderson published a paper on neuronlike adaptive
elements that could solve a difficult learning control problem. The task was
cart-pole balancing: apply forces to a cart so that a hinged pole stays upright.
The learner was not given the equations of motion. The only feedback evaluating
performance was a failure signal when the pole fell too far from vertical or
the cart reached the end of the track.

That sparse feedback matters. A full teacher could say which force should have
been applied at every moment. The pole-balancing learner did not have that
teacher. It had to learn a control behavior from consequences. The signal came
late and crudely: still balanced, still balanced, still balanced, failure.
Learning from such feedback required an internal way to make the failure
informative before the final moment arrived.

The paper's abstract names two components: an associative search element and an
adaptive critic element. The associative search element selected actions under
reinforcement feedback. The adaptive critic constructed a more informative
evaluation function than reinforcement feedback alone could provide. That is
the important actor-critic root. One part chooses behavior; another part learns
to evaluate situations so the behavior can improve.

This historical claim is focused: the 1983 paper establishes the cart-pole
task, sparse failure signal, unknown-equations assumption, and ASE/ACE
structure. The central point is not the specific implementation, but how the
system converted sparse failure feedback into an internal evaluative signal for
control.

Even at that level of detail, the historical point is strong. The
pole-balancing system made delayed reinforcement tangible. It was not a theorem
floating above practice. It was a machine-learning control problem where the
learner had to act repeatedly before knowing whether its policy was good. The
critic did not remove delayed reward. It made delayed reward usable.

That idea would echo through later reinforcement learning. If reward arrives
too late, the learner can try to learn predictions of future reward. Those
predictions become intermediate teaching signals. Instead of waiting until the
end of an episode to learn anything, the system can change its estimates along
the way.

The path from that insight to modern reinforcement learning was not automatic,
but the direction was clear. Learning to act required learning to predict value.
Learning to predict value required a way to update predictions before the
final outcome arrived.

## Temporal Difference

Sutton's 1988 paper gave that update idea a name and a clean formulation:
temporal-difference learning.

The paper introduced incremental procedures specialized for prediction in
incompletely known systems. The distinction from conventional prediction
learning was the key. A conventional method can compare a prediction with the
actual final outcome. A temporal-difference method compares one prediction with
a later prediction. Learning occurs when predictions change over time.

Sutton's weather example makes the idea intuitive. Suppose a forecaster
predicts on Monday whether it will rain on Saturday. A conventional method can
wait until Saturday and compare the earlier predictions with the outcome. A TD
method can compare Monday's prediction with Tuesday's prediction, Tuesday's
with Wednesday's, and so on. If the forecast changes as new evidence arrives,
the change itself becomes information.

That sounds modest until the delayed-reward problem is in view. If a learner
has to wait until the end of every sequence, credit moves slowly. A late
outcome must be propagated backward through many earlier states. Temporal
differences let estimates bootstrap from other estimates. A current prediction
can be improved by looking at the next prediction, not only by waiting for the
final truth.

Sutton's paper was careful about its target. It focused on prediction, not on
the full control problem. It also distinguished the work from the wave of
multilayer supervised networks. The issue was not only how complex an
input-output mapping could be learned. The issue was how predictions about
future outcomes could be improved incrementally from experience.

The random-walk examples in the paper made the idea measurable. A sequence
moves through states before terminating at an outcome. Different values of the
TD parameter change how credit moves across the sequence. The mathematical
formalism matters, but the historical lesson is simpler: TD methods gave
learning systems a way to revise earlier predictions from later predictions
without storing and replaying every complete history in the most expensive
way.

That incremental character was part of the appeal. A learner could adjust an
estimate while a sequence unfolded. The change did not have to wait for a
complete supervised training set. The same experience that generated the next
prediction also supplied a learning signal for the current one. This is why TD
methods fit the reinforcement-learning imagination so well. They treated time
not as a nuisance around the training example, but as the structure of the
training problem.

The TD parameter also gave the idea a useful continuum. At one end, learning
leans toward immediate bootstrapping from the next prediction. At the other, it
leans toward using longer returns. The historical importance is not the symbol
itself. It is the way the method made credit assignment adjustable across time.
Delayed reward no longer had to be all-or-nothing: either wait for the final
outcome or invent a full teacher. There was a middle path.

This is where reinforcement learning began to acquire its distinctive shape.
The learner is not merely fitting a label. It is estimating value through time.
The value estimate is not passive. In control settings, it helps choose future
actions. A better prediction of future consequence can become a better policy.

Sutton also contrasted TD credit assignment with Holland's bucket brigade. The
bucket brigade assigned credit through rules that caused other rules to become
active. TD assigned credit through temporal succession. That difference helped
separate two kinds of credit problem: structural credit among components and
temporal credit across time. Reinforcement learning would need both in various
forms, but the temporal one became central.

The phrase "temporal difference" therefore marks more than an algorithmic
family. It marks a conceptual compromise between waiting for the end and
pretending the end is already known. The learner updates from the next estimate
because the next estimate is closer to the future than the current one.

## Delayed Rewards Become Q Values

Watkins's 1989 thesis carried the delayed-reward problem into the language that
would become central for Q-learning. The thesis title was blunt: *Learning from
Delayed Rewards*. Its summary begins from a biological and behavioral question:
dynamic programming can calculate optimal policies, but how might animals
learn efficient behavior from experience?

The answer did not require animals to run conventional dynamic-programming
calculations. Watkins argued that Markov decision processes could serve as a
general formal model for behavioral choices in an environment, while also
noting that full dynamic-programming calculations were not plausible as animal
computation. The alternative was to reorganize the calculation into incremental
learning methods.

One of the important thesis claims, presented in the opening summary, was that
action values could be learned directly without requiring the learner to model
the environment. That is the historical bridge to model-free reinforcement
learning. Instead of first learning the transition structure and then solving
the model, the agent can learn estimates of how good actions are in states.

The thesis also made the exploration-exploitation dilemma explicit. The
two-armed bandit problem is the simplest version: try the known good option, or
sample the uncertain option that might be better. Watkins treated this as a
central dilemma in instrumental learning. Too much exploration wastes time that
could have been spent exploiting what is already known. Too little exploration
can trap the learner in a mediocre strategy.

That dilemma is not a side issue. It is one reason reinforcement learning is
harder than ordinary prediction. The data are partly a consequence of the
learner's own policy. An agent that never tries an action cannot learn its
value. An agent that tries everything indiscriminately may fail to use what it
has learned. The learning problem and the behavior problem are entangled.

Watkins and Dayan's 1992 paper then gave Q-learning a compact public form. The
abstract describes Q-learning as a simple way for agents to learn how to act
optimally in controlled Markovian domains. It is incremental, related to
dynamic programming, and based on improving estimates of the quality of
particular actions at particular states.

That last phrase is the key. A value function over states can say how good a
situation is. An action-value function says how good it is to take a particular
action in a particular state and then continue well afterward. If an agent can
learn those action values, it can choose actions by comparing them. The policy
is no longer hidden inside a large symbolic rule system. It is implicit in the
table or function of estimated future returns.

Watkins and Dayan described experience as a sequence of stages or episodes. At
each stage, the agent observes the current state, selects and performs an
action, observes the subsequent state, receives reinforcement, and updates its
action-value estimate. That cycle is small, but it captures the heart of the
field. The learner is not merely collecting a static data set. It is producing
experience through action and then using that experience to alter later action.

The action-value view also made the planning connection visible without
requiring a complete model. Dynamic programming computes value when the model is
available. Q-learning uses samples of experience to improve action-value
estimates. It therefore preserves a Bellman-like structure while loosening one
of Bellman's practical assumptions: the agent does not need to know the full
transition model before learning useful preferences over actions.

The convergence result mattered because it put a boundary around optimism. The
paper states that Q-learning converges to optimum action values with
probability one under conditions such as repeated sampling of all actions in
all states, discrete representation, bounded rewards, and suitable learning
rates. Those conditions are not a footnote to skip. They are the reason the
claim is meaningful. The result was powerful because it was bounded.

The theorem did not say Q-learning would solve every real environment. It did
not say exploration would be cheap. It did not say function approximation would
always behave. It did not say a finite learner in a messy partially observable
world would get the same guarantee. It said that, in a controlled finite
Markovian setting with the right sampling and update conditions, the action
values converge.

That is exactly the kind of disciplined claim the post-winter AI landscape
needed. The field had seen enough broad promises. Q-learning offered something
more useful: a small algorithmic idea with a precise setting, a clear
interpretation, and a theorem.

## Self-Play and the Warning Label

TD-Gammon showed how far the delayed-reward idea could travel when joined to
self-play and function approximation.

Gerald Tesauro's 1995 article presented TD-Gammon as a neural-network
backgammon program that learned by playing against itself and learning from the
outcome. The setting was ideal for a dramatic demonstration. Backgammon has
long sequences of decisions, stochastic dice rolls, and a final outcome that
arrives after many moves. It is a natural laboratory for temporal credit
assignment.

Tesauro framed the reinforcement-learning paradigm in the same basic terms:
the learner observes an input, produces an output or action, and receives a
scalar reward signal. If the reward is delayed until the end of a long
sequence, the learner has to solve temporal credit assignment. TD-Gammon used
temporal-difference learning to train a neural network evaluation function from
self-play.

The contrast with Neurogammon was historically useful. Neurogammon had been
trained with backpropagation on expert game data and used hand-crafted
features. TD-Gammon explored a different route: learn from the results of play
itself. Early raw-board experiments were knowledge-free in the sense that they
did not use precomputed expert features. Later versions did add hand-crafted
features, and those versions became stronger. This distinction matters for an
accurate historical account: TD-Gammon was not pure magic. It combined an
algorithm, a game environment, a neural network, self-play, stochastic
variation, and eventually feature engineering.

The results were still striking. Tesauro reports comparisons with
Neurogammon and expert players, and the article describes TD-Gammon as
surpassing previous computer programs. More important for AI history, the
program changed what researchers thought temporal-difference learning might do.
It was not merely a clean idea in small Markov examples. It could produce
strong behavior in a complex game.

The article also helped explain why the result was possible without pretending
that every estimate was numerically perfect. Move decisions depend on comparing
candidate positions, and errors in similar candidate positions can be
correlated. A program can make useful relative choices even if its absolute
equity estimates are imperfect. That distinction matters because it keeps
TD-Gammon from becoming a fairy tale about flawless value prediction. The
system was useful because its learned judgments ranked many choices well
enough for play.

Backgammon's dice mattered too. Randomness kept the game from following a
single narrow script. Self-play generated variation, and variation gave the
learner more situations from which to learn. That does not mean randomness
solves exploration in general. It means the structure of this game helped this
method. A deterministic domain with poor exploration could behave very
differently.

The later survey by Kaelbling, Littman, and Moore keeps the warning label
attached. TD-Gammon was impressive, but its success did not automatically
generalize to every domain. The stochastic nature of backgammon helped
exploration. Self-play can also narrow experience if it explores only the
states created by the current policy. Function approximation can help
generalization, but it can also break simple guarantees.

That is the balanced historical conclusion. Reinforcement learning did not
arrive as a complete recipe for intelligence. It arrived as a way to make
delayed consequence mathematically and computationally usable. Bellman supplied
recursive value. Samuel showed evaluation improving through play. The
pole-balancing work made sparse feedback concrete. Sutton turned successive
predictions into a learning signal. Watkins and Dayan made action values and
Q-learning precise. TD-Gammon showed the ambition.

The roots were not enough for modern AI by themselves. They did not contain
deep reinforcement learning, AlphaGo, or large-scale robotic autonomy. But
they changed the question. A machine did not need a label for every decision.
It could act, observe consequences, update value, and act again.

That loop would become one of AI's most durable ideas.

## Sources

### Primary

- Richard Bellman, ["A Markovian Decision
  Process"](https://iumj.org/article/1116/), *Journal of Mathematics and
  Mechanics* 6(5), 679-684 (1957): limited background anchor for dynamic
  programming recurrence and sequential-decision ancestry.
- Arthur L. Samuel, ["Some Studies in Machine Learning Using the Game of
  Checkers"](https://www.cs.virginia.edu/~evans/greatworks/samuel1959.pdf),
  *IBM Journal of Research and Development* 3(3) (1959): early game-learning
  anchor for checkers, lookahead, evaluation functions, machine-playing time,
  and self-improving play.
- Andrew G. Barto, Richard S. Sutton, and Charles W. Anderson, ["Neuronlike
  Adaptive Elements That Can Solve Difficult Learning Control
  Problems"](https://www.derongliu.org/adp/adp-cdrom/Barto1983.pdf), *IEEE
  Transactions on Systems, Man, and Cybernetics* SMC-13(5), 834-846 (1983):
  p.834 anchor for the cart-pole task, sparse failure signal, unknown
  equations, and ASE/ACE actor-critic structure.
- Richard S. Sutton, ["Learning to Predict by the Methods of Temporal
  Differences"](http://incompleteideas.net/papers/sutton-88-with-erratum.pdf),
  *Machine Learning* 3, 9-44 (1988): core anchor for temporal-difference
  prediction, successive-prediction errors, random-walk examples, and temporal
  credit assignment.
- Christopher J. C. H. Watkins, ["Learning from Delayed
  Rewards"](http://www.cs.rhul.ac.uk/~chrisw/new_thesis.pdf), PhD thesis,
  King's College, Cambridge (1989): thesis-level anchor for title, summary,
  Markov-decision-process framing, action-value learning from experience, and
  exploration-exploitation discussion.
- Christopher J. C. H. Watkins and Peter Dayan,
  ["Q-learning"](https://www.gatsby.ucl.ac.uk/~dayan/papers/cjch.pdf),
  *Machine Learning* 8, 279-292 (1992): core anchor for Q-learning,
  model-free action-value learning, and bounded convergence conditions.
- Gerald Tesauro, ["Temporal Difference Learning and
  TD-Gammon"](https://www.csd.uwo.ca/~xling/cs346a/extra/tdgammon.pdf),
  *Communications of the ACM* 38(3) (1995): anchor for TD-Gammon, delayed
  reward, temporal credit assignment, self-play, and limits of the result.

### Secondary

- Leslie Pack Kaelbling, Michael L. Littman, and Andrew W. Moore,
  ["Reinforcement Learning: A
  Survey"](https://www.ri.cmu.edu/pub_files/pub1/kaelbling_l_p_1996_1/kaelbling_l_p_1996_1.pdf),
  *Journal of Artificial Intelligence Research* 4, 237-285 (1996): near-primary
  survey anchor for field definition, history, Markov decision framing,
  exploration versus exploitation, delayed reinforcement, generalization, and
  TD-Gammon limits.

> [!note] Honesty Over Output
> This chapter treats reinforcement learning as a bounded mathematical and
> engineering lineage, not as a single invention or a solved theory of
> intelligence. Bellman is used only as ancestry, Barto/Sutton/Anderson only at
> abstract-level p.834 claims, Watkins 1989 only within the thesis summary and
> early framing, and Q-learning only under the convergence conditions stated by
> Watkins and Dayan.
