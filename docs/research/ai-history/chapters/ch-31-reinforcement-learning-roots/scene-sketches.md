# Scene Sketches: Chapter 31 - Reinforcement Learning Roots

## Scene 1: The Problem Supervision Could Not See

Start with the missing teacher. A supervised learner can be corrected at the point of error; an RL agent may receive only a delayed scalar reward. Use Tesauro's temporal credit assignment explanation and Kaelbling/Littman/Moore's problem definition to set the stakes.

## Scene 2: Bellman and Samuel Give the Shape

Move from Bellman's recurrence to Samuel's checkers machine. The prose should make the lineage precise: Bellman supplies the recursive decision mathematics; Samuel supplies an early AI demonstration that evaluation can improve through play.

## Scene 3: The Pole-Balancing Critic

Introduce the cart-pole as a concrete control problem: the learner does not get the equations of motion and only gets sparse evaluative feedback when failure occurs. ASE/ACE gives the chapter a vivid actor-critic root without overclaiming modern actor-critic identity.

## Scene 4: Temporal Difference as a Credit-Assignment Machine

Use Sutton's weather-prediction style explanation and random-walk example: learning from changes in successive predictions lets credit move before the final outcome arrives. This is the conceptual center of the chapter.

## Scene 5: Delayed Rewards Become Q Values

Watkins gives the delayed-reward frame and exploration-exploitation dilemma; Watkins/Dayan turn the history into a theorem-bound algorithm. Explain action values as a practical answer to "what should I do here if future rewards matter?"

## Scene 6: Self-Play Shows the Ambition and the Limit

End with TD-Gammon. It is not AlphaGo yet. It is a 1990s signal that TD learning plus self-play plus function approximation could exceed expectations in a structured stochastic game, while leaving open whether the same recipe generalized.
