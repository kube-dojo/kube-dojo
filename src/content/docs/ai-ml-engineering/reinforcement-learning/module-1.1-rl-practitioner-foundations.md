---
title: "RL Practitioner Foundations"
description: "Decide when reinforcement learning is the right tool, choose between PPO/DQN/SAC, design rewards that resist hacking, and evaluate runs honestly with multi-seed protocols."
slug: ai-ml-engineering/reinforcement-learning/module-1.1-rl-practitioner-foundations
sidebar:
  order: 1
---

> Track: AI/ML Engineering | Complexity: Intermediate | Time: 75-90 minutes
> Prerequisites: [Module 1.1: Scikit-learn API & Pipelines](../../machine-learning/module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../../machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.5: Decision Trees & Random Forests](../../machine-learning/module-1.5-decision-trees-and-random-forests/), and [Module 1.11: Hyperparameter Optimization](../../machine-learning/module-1.11-hyperparameter-optimization/).

Reinforcement learning rarely fails in a dramatic way first.
It usually fails quietly.
A run looks healthy because reward is climbing,
GPU utilization is steady,
and a single seed produced one promising checkpoint.
Then the policy meets a slightly different episode,
finds a loophole in the proxy you wrote,
or collapses when the next retraining job uses another seed.
That is why a practitioner mindset matters more than algorithm trivia.
You need to decide whether RL should be used at all,
whether PPO, DQN, or SAC matches the action space,
whether the reward says what you think it says,
and whether your evaluation protocol is honest enough to survive review.

## Learning Outcomes

- **Decide** when reinforcement learning is the right tool versus supervised learning, given a problem description, available data, and an interaction budget.
- **Choose** between PPO, DQN, and SAC for a candidate problem and **justify** the choice from action-space type, observation modality, and sample-efficiency tradeoffs.
- **Design** a reward function that resists reward hacking by inspecting the dominant failure modes (sparse signal, proxy gaming, unintended optimization) before training begins.
- **Evaluate** an RL training run honestly using a multi-seed protocol that separates mean-and-variance reporting from single-seed cherry-picking.
- **Debug** a stalled or diverging RL run by triaging environment definition, reward shape, hyperparameter range, and seed variance against published Stable-Baselines3 guidance.

## Why This Module Matters

Stable-Baselines3 says the quiet part out loud: RL is unstable, sample-inefficient, and unusually sensitive to reward design and evaluation procedure. That warning is not a footnote. It is the operating manual.
https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html

Gymnasium is equally direct about the environment contract. An environment defines what the agent observes, what actions exist, when an episode is truly over, and what reward gets logged at every step. If that contract is wrong, your training curve can look disciplined while teaching the wrong behavior.
https://gymnasium.farama.org/api/env/

That becomes painful when a team treats one overnight run as evidence. A policy appears to improve. The mean reward from a single seed looks higher than last week. The demo clip is smooth. No one notices that another seed plateaus early, or that the shaping term taught the agent to orbit the proxy instead of solving the task.

Nothing in that workflow feels obviously reckless when you are close to it. The logs are real. The checkpoint loads. The curve points up. But the system is still lying to you, because you have not yet separated training progress from decision-grade evidence.

The reproducibility critique in deep RL makes this problem concrete. Small implementation choices, seed choices, and evaluation habits can change which method appears to win.
https://arxiv.org/abs/1709.06560

That is why this module matters. RL is not just another model family. It is a loop in which data collection, policy updates, reward specification, and evaluation all shape one another. If any one of those pieces is weak, the rest become a faster way to become confident in the wrong result.

## Section 1: What RL is, and what it isn't

Reinforcement learning is the part of machine learning where an agent learns by acting, observing consequences, and adjusting behavior to maximize return over time. The phrase "over time" is the hinge.

If your problem is really a one-step prediction problem, RL is usually the wrong tool. If you already have labeled examples of the correct action for each state, supervised learning will usually be cheaper, faster, easier to debug, and easier to evaluate honestly.

That matters because many first RL projects are disguised classification tasks. A team has logged examples, clear labels, and no safe way to explore in production, yet still reaches for RL because the control loop feels more modern. That is usually a mistake.

RL becomes worth considering when actions change future states, when delayed consequences matter, and when interaction is part of the learning process rather than just the deployment process. A thermostat, a robot arm, a game-playing agent, or an online control policy can fit that shape. A static fraud classifier usually does not. The practical test is whether you need to learn from consequences you can only observe by trying actions, not whether the product vocabulary includes the word "agent."

The first practitioner question is therefore not, "Which algorithm should we use." It is, "What kind of evidence do we actually have." Do you have logged labels. Do you have a simulator. Can you explore safely. Does the action now affect the observations later. Can the environment reset repeatedly without harming real users or systems. Answering those questions honestly prevents months of tuning the wrong learning paradigm and saves you from impressive-looking curves that answer the wrong problem.

If supervised learning works, use supervised learning. The modules on [Module 1.1: Scikit-learn API & Pipelines](../../machine-learning/module-1.1-scikit-learn-api-and-pipelines/), [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../../machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration/), and [Module 1.5: Decision Trees & Random Forests](../../machine-learning/module-1.5-decision-trees-and-random-forests/) give you stronger defaults for that world. RL earns its complexity only when interaction and long-horizon credit assignment are the real problem.

| Problem question | If the answer is yes | Practitioner reading |
|---|---|---|
| Do you already know the correct action for each example | Prefer supervised learning | RL would add variance without adding information |
| Can the model learn safely only from logged data | Prefer offline RL or imitation later | Online exploration is not available |
| Does one action change the next observation distribution | RL becomes more plausible | Sequential effects are real |
| Is the environment expensive to reset or dangerous to probe | Be skeptical of online RL | The interaction budget may be too small |
| Can a hand-built rule solve the task cheaply | Start with the rule | RL should beat a strong trivial baseline before it earns trust |

The practical failure mode here is conceptual overreach. Teams choose RL because the system "acts" in the vague everyday sense. But many systems act without needing RL. Recommendation ranking, tabular risk scoring, or next-best-action prediction can often be framed more cleanly as supervised learning, ranking, or bandits.

That is the first pitfall of this module. RL is the wrong tool when supervised learning already answers the question with less risk.

## Section 2: The MDP frame, briefly and operationally

Most RL texts organize the problem as a Markov decision process, or MDP. You do not need heavy notation to use that frame well. You need operational questions.

The state is what the agent gets to observe before acting. The action is what the agent is allowed to do. The reward is the scalar signal you log after the action. The transition is how the next state changes. The episode boundary defines when a rollout starts over.

That sounds abstract until you make it concrete. In `CartPole-v1`, the state is a small vector describing cart and pole motion. The action is left or right. The reward is a stepwise signal for keeping the pole upright. The transition is the physics. Termination happens when the pole falls or the cart leaves the allowed range.

The operational value of the MDP frame is not symbolism. It is forcing clarity about interfaces and blame. If training stalls, was the observation incomplete. Was the action space mismatched. Was the reward sparse. Did the episode end too early. Was the transition stochastic enough that one seed looked great by luck.

| MDP piece | Operational question |
|---|---|
| State | What exact variables are visible to the policy at decision time |
| Action | Is the choice discrete or continuous, and is every action actually valid |
| Reward | What proxy is the optimizer really maximizing step by step |
| Transition | What dynamics or simulator quirks shape the learning signal |
| Episode boundary | What counts as success, failure, timeout, or reset |
| Return | What long-run behavior does repeated reward accumulation favor |

This frame also clarifies why RL feels different from the earlier machine-learning modules. In supervised learning, the dataset is mostly fixed before optimization begins. In RL, the policy helps generate the future data distribution. Better policies visit different states. Worse policies may never visit useful ones.

That feedback loop is why environment definition and reward definition matter so much. You are not only fitting a model to data. You are shaping which data the model will see next.

The agent–environment loop is the durable spine underneath every library in this module. At each discrete time step `t`, the agent observes state `s_t`, chooses action `a_t`, receives scalar reward `r_t`, and lands in next state `s_{t+1}`. An episode ends when a termination or truncation condition fires. Return is the discounted sum of future rewards: `G_t = r_t + γ r_{t+1} + γ² r_{t+2} + …`, where discount factor `γ` in `(0, 1]` controls how far ahead the agent plans. A `γ` near zero makes the agent myopic; a `γ` near one makes distant consequences matter, which is powerful but harder to learn when rewards are sparse.

```
  ┌─────────┐  action a_t   ┌──────────────┐
  │  Agent  │──────────────▶│ Environment  │
  │ (policy)│◀──────────────│ (dynamics)   │
  └─────────┘  obs s_t,     └──────────────┘
               reward r_t
```

The Markov property, when it holds, says the future depends on history only through the current state. Real deployments often violate that cleanly: a dashboard snapshot may omit hidden inventory, and a partially observed process may need memory or state estimation. The MDP frame still helps because it forces you to name what the policy actually sees at decision time, not what you wish it could see.

Exploration versus exploitation sits on top of that loop. Exploitation means choosing the action that looks best from current estimates. Exploration means trying actions that might be suboptimal now but could reveal better long-run behavior. A policy that never explores may never discover a high-reward region; a policy that explores too aggressively wastes interaction budget on noise. There is no universal dial that solves this once. Sparse rewards, stochastic transitions, and deceptive local optima all change the balance. That is one reason algorithm families differ: some encourage stochastic policies explicitly, some rely on ε-greedy action noise, and some depend on environment resets to keep visitation broad.

## Section 3: Three algorithm families

For this module, the first family choice is simpler than the literature makes it sound. Start from the action space, then ask how much data reuse you need, then ask how much instability you are willing to manage.

PPO is the general-purpose workhorse for many online RL projects. It is on-policy, which means it learns from data generated by the current policy. That usually makes it more stable to reason about, but less sample-efficient because old experience becomes stale quickly.

DQN is the classic discrete-control family in this module. It learns a value estimate for each discrete action and uses a replay buffer to reuse old transitions. That makes it more sample-efficient than an on-policy method in many small discrete settings, but it does not solve continuous action problems directly.

SAC is the continuous-control family here. It is off-policy, so it also reuses past transitions, and it adds an entropy-driven exploration objective that often makes it strong for continuous `Box` action spaces. The tradeoff is that it usually asks more of your stabilization and debugging discipline.

| Family | Typical action space | Data reuse | Default story | Main caution |
|---|---|---|---|---|
| PPO | Discrete or continuous | Low | Stable first baseline | Sample efficiency is weaker |
| DQN | Discrete only | High | Replay-based value learning | Wrong fit for continuous actions |
| SAC | Continuous `Box` | High | Efficient continuous control | Stabilization is less forgiving |

Observation modality matters too, but in a more boring way at this level. If your observations are low-dimensional vectors and a standard multilayer perceptron policy is enough, algorithm family choice is mostly about action space and data reuse. If you need complex visual encoders, partially observed memory, or multi-agent behavior, the problem grows beyond this foundation module quickly.

A common beginner mistake is to choose from names first and interfaces second. Do the opposite. Inspect `env.action_space` and `env.observation_space` before you argue about algorithms. That single check eliminates many bad starts.

Before naming PPO, DQN, or SAC, it helps to know what object each family is trying to learn. Value-based methods estimate how good states or state–action pairs are, then derive behavior by picking high-value actions. Policy-based methods learn a mapping from state to action directly and optimize that mapping with gradient signals from rollouts. Actor–critic methods keep both: a policy actor proposes actions, and a critic estimates value to reduce variance in the policy update. DQN is the canonical value-based discrete-control story in this module. PPO is policy-based with a value baseline attached. SAC is actor–critic with entropy regularization for continuous control.

On-policy versus off-policy is a separate axis from that taxonomy. On-policy learning updates from data collected by the policy you are currently improving; old rollouts become stale quickly when the policy changes. Off-policy learning reuses transitions gathered under older behavior, which can improve sample efficiency but introduces mismatch between the data distribution and the policy you want. PPO is on-policy in spirit. DQN and SAC are off-policy and use replay. The durable lesson is not memorizing acronyms but knowing whether your update is allowed to trust old experience and whether your critic is being queried on actions the data never supported.

> **Landscape snapshot — as of 2026-06**
>
> Gymnasium exposes the loop through `reset()` → `step(action)` with `observation_space` and `action_space` metadata. Stable-Baselines3 wraps algorithms behind a common `learn()` / `predict()` API. Verify constructor names, space types, and evaluator helpers against the pinned docs in **Sources** before relying on them in production; both projects ship breaking changes between minor releases.

## Section 4: PPO — the workhorse

PPO is the algorithm many practitioners should try first, not because it is always best, but because it is a solid baseline across many tasks and tends to fail in ways you can inspect. Its central practical tradeoff is straightforward: PPO is on-policy, which means the rollout data used for updates should come from the current policy rather than a large pool of older behavior. The upside is conceptual simplicity and often smoother training; the downside is weaker sample efficiency when every environment step is expensive.

That tradeoff becomes important on real budgets. If environment interaction is cheap, PPO can be a very sensible default. If every environment step is expensive, on-policy waste becomes painful, and that is where off-policy methods often earn their extra complexity. Exploration versus exploitation also matters here more than many newcomers expect: a PPO run can look stable while still under-exploring because the reward is too uninformative or because the agent settles into a locally decent behavior too early, and in those cases switching algorithms is often less useful than fixing the task signal.

The SB3 interface makes a first PPO baseline simple enough that you should use it early. The point of the first baseline is not to win; it is to expose whether the environment and reward are even learnable.

```python
env = make_vec_env("CartPole-v1", n_envs=4, seed=0)
model = PPO("MlpPolicy", env, verbose=1, seed=0)
model.learn(total_timesteps=10000)

eval_env = gym.make("CartPole-v1")
mean_reward, std_reward = evaluate_policy(
    model,
    eval_env,
    n_eval_episodes=10,
)
print(f"mean={mean_reward:.2f}, std={std_reward:.2f}")
```

This example works because the environment is cheap,
the action space is discrete,
and the observation is a small vector.
It is exactly the kind of environment where a first PPO run tells you something useful quickly.

> **Pause and decide** — You have a simulator that resets cheaply, a small vector observation, and a policy that must emit one of two safe actions each step. Would you start with PPO for stability, or jump to a replay-based method first, and what assumption about interaction cost drives your choice?

Practitioners sometimes confuse PPO's popularity with algorithmic invincibility, which is a mistake. PPO is often a good first answer, not a magical final answer, and if learning plateaus you still have to inspect the environment, the reward, the budget, and the seed variance. The sample-efficiency versus wall-clock tradeoff is the main thing to remember: vectorized rollouts can improve wall-clock speed on one machine, but they do not change the fact that PPO discards much of what older off-policy methods can reuse, and that is the price of its stable workhorse reputation.

## Section 5: DQN — discrete action spaces and replay buffers

DQN fits problems where the action space is discrete and not too large. Instead of learning a direct continuous control policy, it learns action values and improves behavior by preferring actions with larger estimated return. The replay buffer is the important operational feature: transitions collected earlier can be sampled again later, which usually helps sample efficiency, but you pay for that efficiency with a different kind of debugging burden because old experience can reinforce biases in the policy's state visitation and exploration quality matters a lot.

This is why DQN is often attractive in small discrete control tasks and game-like environments, but not the right default for torque control, continuous robotics, or other `Box` action settings. If your action is a real-valued vector, DQN is answering the wrong question.

```python
env = gym.make("CartPole-v1")
model = DQN("MlpPolicy", env, verbose=1, seed=0)
model.learn(total_timesteps=10000)

eval_env = gym.make("CartPole-v1")
mean_reward, std_reward = evaluate_policy(
    model,
    eval_env,
    n_eval_episodes=10,
)
print(f"mean={mean_reward:.2f}, std={std_reward:.2f}")
```

The temptation with DQN is to over-credit the algorithm when the real issue is exploration. A replay buffer cannot rescue a task the agent rarely discovers, and if the initial behavior almost never reaches useful states the buffer mostly stores unhelpful transitions more efficiently. That is why exploration versus exploitation tuning often matters more than the algorithm label: a mediocre reward with decent state coverage can outperform a theoretically stronger method whose experience never includes the crucial states. DQN also teaches a healthy discipline about action spaces, so before you run it check that the environment's action space is actually discrete, because that one line of due diligence prevents a category error that no amount of hyperparameter tuning can fix.

## Section 6: SAC — continuous control with entropy

SAC is the family to keep in mind when the action space is continuous and data reuse matters. Its defining idea at practitioner level is simple: learn from replayed transitions while encouraging sufficiently stochastic behavior to keep exploration alive. That entropy term is not decoration; it is one reason SAC can explore continuous spaces more effectively than a purely greedy control update, and in tasks where action values are smooth and interaction is expensive that can make SAC a strong choice. The tradeoff is that SAC asks for more judgment: it is often sample-efficient, but it can be less forgiving than a first PPO baseline if the reward is badly scaled, the environment is poorly specified, or your evaluation protocol is sloppy.

```python
env = gym.make("Pendulum-v1")
model = SAC("MlpPolicy", env, verbose=1, seed=0)
model.learn(total_timesteps=10000)

eval_env = gym.make("Pendulum-v1")
mean_reward, std_reward = evaluate_policy(
    model,
    eval_env,
    n_eval_episodes=10,
)
print(f"mean={mean_reward:.2f}, std={std_reward:.2f}")
```

The algorithm choice here is driven by the interface. `Pendulum-v1` uses a continuous `Box` action space, so DQN is out before discussion starts. PPO remains viable, but SAC becomes attractive when interaction cost makes replay-based reuse valuable. This is the second place where sample efficiency versus wall-clock must be separated: a slower-feeling method per update can still be the better engineering choice if every new environment interaction is expensive, whereas if you can cheaply parallelize simulation on one machine PPO may still be easier to get moving. SAC does not repeal the rule that reward design dominates algorithm choice; if the reward is exploitable, SAC will exploit it efficiently, because off-policy efficiency is a force multiplier that helps when the objective is sound and hurts when it is not.

## Section 7: Stable-Baselines3 in practice

Stable-Baselines3 is valuable because it narrows the gap between RL theory and a practical first experiment. It gives you consistent APIs, documented algorithm support, and guidance about when a result should be treated as suspicious rather than exciting. In practice, the library should shape your workflow in three ways: start from one documented algorithm-environment pair that clearly fits the action space, use a small budget that can finish quickly enough to support iteration, and separate training, evaluation, and serialization so checkpoints are testable artifacts rather than disposable side effects.

```python
train_env = DummyVecEnv([lambda: gym.make("CartPole-v1")])
model = PPO("MlpPolicy", train_env, verbose=1, seed=0)
model.learn(total_timesteps=10000)
model.save("ppo_cartpole")

loaded_model = PPO.load("ppo_cartpole", env=train_env)
eval_env = gym.make("CartPole-v1")
mean_reward, std_reward = evaluate_policy(
    loaded_model,
    eval_env,
    n_eval_episodes=10,
)
print(f"mean={mean_reward:.2f}, std={std_reward:.2f}")
```

Saving and reloading matters more than it looks, because a checkpoint you cannot reload and evaluate cleanly is not an experiment result but a transient process state. SB3's documentation also encourages a useful cultural habit: treat the first implementation as a baseline, not as proof, which sounds obvious but is one of the easiest disciplines to lose when RL curves start moving. The common failure mode in this section is premature complexity, where people reach for distributed training, custom wrappers, and large sweeps before confirming that the smallest documented setup can learn at all; do not scale confusion, scale a working baseline.

## Section 8: Gymnasium — the environment interface

Gymnasium is the boundary object between your algorithm and the task, and if that boundary is misunderstood everything upstream becomes harder to interpret. The modern API matters: `reset` returns both observation and info, and `step` returns observation, reward, termination flag, truncation flag, and info, so the distinction between termination and truncation is operationally important. Termination means the task ended according to task logic, while truncation usually means a time limit or external episode cutoff, and if you collapse those carelessly you can misread learning progress or compute returns in a misleading way.

```python
env = gym.make("CartPole-v1")
obs, info = env.reset(seed=0)
print(env.observation_space)
print(env.action_space)

for _ in range(3):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(reward, terminated, truncated)
    if terminated or truncated:
        obs, info = env.reset(seed=0)
```

Two quick checks fall out of this example. `env.action_space` tells you whether DQN or SAC even belongs in the conversation, and `env.observation_space` tells you what the policy must ingest. This is also the right place to remember that environment bugs can mimic algorithm bugs: a wrong reward sign, a hidden state leak, or an inconsistent reset can produce learning curves that look random, unstable, or deceptively good, so before you blame PPO inspect the environment. Gymnasium environments are not just datasets with a fancy loop; they are executable task definitions, which makes interface hygiene part of model quality rather than separate from it. Mapping the durable MDP pieces onto Gymnasium is straightforward once you treat the API as a contract checklist rather than boilerplate: state is the observation returned by `reset` and `step`, action is whatever `action_space.sample()` would admit, reward is the scalar from `step`, transition is whatever your simulator or wrapper implements behind those calls, and the episode boundary is the combination of `terminated` and `truncated`.

## Section 9: Reward design — the hardest part of RL

Reward design dominates algorithm choice more often than practitioners want to admit.
If the reward is sparse,
misaligned,
or easy to game,
the algorithm will spend its intelligence on the wrong problem.

There are three classic failure modes to look for before training begins.
The first is sparse signal:
the agent almost never sees meaningful positive feedback,
so learning drifts or stalls.
The second is proxy gaming:
the reward captures a shortcut rather than the intended behavior.
The third is unintended optimization:
the agent discovers behavior that satisfies the scalar reward while violating the human objective.

Shaping can help, but shaping is not free. A shaping term changes the optimum unless it is designed very carefully, which is why the question is never just "Can I make reward denser" but "What new loophole did I introduce by making it denser." Classic reward-shaping pitfalls include potential-based shortcuts that look correct on paper but change the optimal policy, per-step bonuses that dominate sparse terminal rewards and teach the agent to stall, and proxy terms copied from a different task that correlate with success in training but not in deployment. Potential-based shaping theory exists to preserve optimal policies under certain conditions, but practitioner implementations often skip the formal checks and add hand-tuned bonuses anyway.

The role of the reward signal is not to narrate your intent; it is to define the optimization target. If two behaviors tie on your scalar but differ on safety, latency, or user trust, the agent will not split the difference politely. It will pick whichever behavior maximizes the number you logged. Reward hacking is therefore a specification bug, not a mysterious failure of deep learning. Before training, list the behaviors that would score well while failing the real objective, then design evaluations that would catch them. After training, inspect rollouts for those failure modes even when mean reward looks healthy.

```python
class PositionBonus(gym.RewardWrapper):
    def reward(self, reward):
        position = self.env.unwrapped.state[0]
        return reward + 0.05 * float(position)

env = PositionBonus(gym.make("MountainCar-v0"))
obs, info = env.reset(seed=0)
print(obs)
```

This wrapper makes the signal denser by slightly rewarding forward position.
That may help learning.
It may also teach a side behavior,
such as favoring local motion patterns that harvest the bonus without reaching the real objective as reliably as you hoped.

> **Pause and predict** — You add a shaping term that rewards a control system for staying near a safe-looking intermediate state, and training suddenly becomes faster. What evidence would you need before deciding you improved the real task instead of teaching the agent to orbit the proxy?

The honest reward-design habit is to write down failure hypotheses before the first run.
How could the policy game this signal.
What behavior would look good on reward but bad in reality.
Which side effects would a reviewer look for immediately.

That habit sounds slow.
It is usually faster than retraining a month of reward mistakes.

If you remember one thing from this section,
remember this:
reward design is usually the hardest part of RL because the optimizer is literal.
It does not understand your intent.
It only understands the scalar you handed it.

When debugging reward issues, compare rollouts side by side with the unshaped environment when possible. Watch for agents that maximize a shaping term while ignoring terminal success, agents that oscillate to harvest dense bonuses, and agents that exploit simulator quirks that do not exist in production. The durable fix is usually to tighten the objective or add evaluation criteria the optimizer does not see, not to chase a more exotic algorithm.

## Section 10: Evaluation discipline — multi-seed or it doesn't count

A training curve is not a result.
A checkpoint from one seed is not a result.
A demo clip is definitely not a result.

Deep RL is noisy enough that single-seed claims are not trustworthy evidence on their own.
Variance from initialization,
environment stochasticity,
and training dynamics can change the story dramatically.
https://arxiv.org/abs/1709.06560

That is why a minimum honest protocol includes repeated runs across multiple seeds under the same environment,
same code,
same horizon,
and same evaluation policy.
You then report the mean and spread across seeds,
not just the prettiest run.

There is another subtlety here.
`evaluate_policy` returns a mean and standard deviation across episodes for one trained policy.
That is useful,
but it is not the same as spread across training seeds.
You need both levels of variation in your head.

```python
seed_scores = []

for seed in [0, 1, 2, 3, 4]:
    train_env = make_vec_env("CartPole-v1", n_envs=4, seed=seed)
    model = PPO("MlpPolicy", train_env, verbose=1, seed=seed)
    model.learn(total_timesteps=10000)

    eval_env = gym.make("CartPole-v1")
    mean_reward, std_reward = evaluate_policy(
        model,
        eval_env,
        n_eval_episodes=10,
    )
    print(f"seed={seed} mean={mean_reward:.2f} episode_std={std_reward:.2f}")
    seed_scores.append(mean_reward)

print(f"across-seed mean={np.mean(seed_scores):.2f}")
print(f"across-seed std={np.std(seed_scores):.2f}")
```

This is also where hyperparameter optimization in RL becomes more expensive than
people expect.
If one trial equals one seed,
the sweep mostly learns which random initialization got lucky.
To make tuning honest,
important trials need multiple seeds per candidate,
which should remind you of the evidence discipline from
[Module 1.11: Hyperparameter Optimization](../../machine-learning/module-1.11-hyperparameter-optimization/).

The reproducibility crisis in RL is not an excuse for cynicism.
It is a request for better experimental hygiene.
Keep environment versions fixed.
Keep evaluation budgets fixed.
Keep wrapper choices fixed.
Report variance.
Refuse to celebrate a single cherry-picked line.

Treat every checkpoint as a hypothesis about behavior, not a trophy. Save the config, seed list, library versions, and evaluation script alongside the model weights so a colleague can reproduce the claim without guessing which informal tweaks produced the curve you are showing.

> **Pause and decide** — One PPO configuration averages slightly lower reward than another across one favorite seed, but it has much tighter results across five seeds and fewer collapses. Which run is more credible for deployment review, and what would you write in the summary to make that case honestly?

Multi-seed reporting also changes how you debug stalled or diverging runs. If all seeds fail, suspect environment definition, reward quality, or a wildly bad hyperparameter range before you blame the algorithm family. If one seed succeeds and four fail, suspect brittleness and under-reported variance before you declare victory. When curves diverge mid-training, triage in this order: confirm `terminated` versus `truncation` handling, inspect reward scale and wrapper side effects, compare against a trivial random or heuristic policy, then revisit learning rate and batch size against Stable-Baselines3 guidance. Debugging RL is mostly debugging the loop you defined, not swapping acronyms.

That is the third pitfall of this module. Single-seed results are not real results.

## Section 11: Ray RLlib — when one machine is not enough

Stable-Baselines3 is enough for many foundation experiments.
Ray RLlib enters the picture when the question itself becomes distributed.

That can happen because you need many parallel environment workers,
because simulation is expensive and cluster throughput matters,
because you are running population-style experiments,
or because one process can no longer collect and update fast enough for the research loop you want.
https://docs.ray.io/en/latest/rllib/index.html

The temptation at that point is to think scale will solve uncertainty.
Usually it only scales uncertainty faster unless the evaluation contract is already sound.
A hundred single-seed distributed trials are still a hundred single-seed trials.

RLlib therefore belongs after,
not before,
the small-scale discipline in this module.
Know that the environment learns at all.
Know that the reward is not obviously gameable.
Know that your evaluation harness reports across-seed variance.
Then distribute the workload.

This is also where search discipline gets expensive.
If you use distributed infrastructure for hyperparameter optimization,
budget for repeated seeds per candidate and not just more candidates.
Otherwise the cluster mainly purchases faster self-deception.
The mindset should feel familiar from
[Module 1.11: Hyperparameter Optimization](../../machine-learning/module-1.11-hyperparameter-optimization/):
selection pressure amplifies noise unless you design the protocol to absorb it.

If one laptop and one vectorized baseline can answer the current question,
stay there.
Reach for RLlib when the bottleneck is truly system scale,
not because the smaller setup feels insufficiently impressive.

Distributed training changes throughput, not truth. The same MDP questions apply at cluster scale: does the environment contract hold across workers, are rewards aggregated consistently, and does the evaluation harness still report across-seed variance rather than surfacing the best of many lucky single-seed trials. RLlib is a scaling tool once the scientific protocol is sound, not a substitute for the discipline earlier in this module.

## Section 12: Where RL is the wrong tool

RL is the wrong tool more often than many first-time teams expect.
That is not a criticism of RL.
It is a reminder to choose the smallest honest method that matches the problem.

If the task is one-step prediction from labeled examples,
use supervised learning.
If exploration is unsafe,
online RL may be disqualified before training starts.
If a crisp rule or search procedure already solves the control logic cheaply,
do not wrap it in policy optimization just to modernize the vocabulary.

If you only have logged behavior and cannot interact online,
you are already moving toward the next module's problem family:
[Module 2.1: Offline RL & Imitation Learning](../module-2.1-offline-rl-and-imitation-learning/).
That is a different setup from free online exploration and deserves its own treatment.

This section is also where it helps to separate standard control RL from RLHF.
Language-model alignment workflows involve preference data,
reward models,
KL control,
and very different engineering constraints.
They are related in lineage,
but not interchangeable in practice.
If that is your target domain,
read [Module 1.4: RLHF Alignment](../../advanced-genai/module-1.4-rlhf-alignment/) as a different beast,
not as a minor variant of `CartPole-v1`.

The same warning applies to static business workflows.
If you cannot define meaningful episodic interaction,
if actions do not change future state in the sense that matters,
or if the best policy can be learned from labeled examples directly,
RL is adding moving parts faster than it adds value.

That is the final core pitfall. RL is the wrong tool when a simpler supervised, bandit, search, or rule-based framing already answers the operational question.

## Section 13: Connecting back

This module sits downstream of earlier machine-learning discipline, not outside it. [Module 1.1: Scikit-learn API & Pipelines](../../machine-learning/module-1.1-scikit-learn-api-and-pipelines/) taught you to respect interfaces, and Gymnasium environments are another interface contract with the same stakes: if the contract is wrong, the optimizer learns the wrong problem.

[Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../../machine-learning/module-1.3-model-evaluation-validation-leakage-and-calibration/) taught you that evidence can be contaminated by bad protocol. RL inherits that lesson and adds seed variance, interaction effects, and proxy optimization on top, which means a leaky evaluation harness can look like algorithmic success until deployment proves otherwise.

[Module 1.5: Decision Trees & Random Forests](../../machine-learning/module-1.5-decision-trees-and-random-forests/) showed the value of strong baselines, and that lesson survives unchanged here. A hand-built rule, a heuristic controller, or a supervised imitation baseline often deserves to exist before the first RL claim, because if you cannot beat a simple baseline you may not have an RL problem yet.

[Module 1.11: Hyperparameter Optimization](../../machine-learning/module-1.11-hyperparameter-optimization/) showed that selection pressure can turn noise into apparent certainty. RL makes that easier, not harder, because every seed can generate a different training story and every sweep can amplify lucky rollouts unless you budget seeds per candidate honestly.

Finally, do not forget the deployment side. Once an RL policy is live, you still need observability, drift awareness, and behavior review. The production habits from [Module 1.10: ML Monitoring](../../mlops/module-1.10-ml-monitoring/) still apply, even if the failure signal looks like degraded sequential behavior rather than plain classifier drift. The durable spine you practiced here—MDP clarity, reward skepticism, multi-seed evaluation, and library APIs as contracts—carries forward whether your next project stays online or moves to logged-data settings.

The next module moves to the setting many practitioners actually face first: learning from logged or demonstrated behavior when free online exploration is not available.

## Did You Know?

- Stable-Baselines3 publishes an [algorithm support table](https://stable-baselines3.readthedocs.io/en/master/guide/algos.html) that makes action-space compatibility explicit before you ever start training.
- Gymnasium's current API [separates `terminated` from `truncated`](https://gymnasium.farama.org/introduction/basic_usage/), which prevents a subtle but common evaluation mistake when time limits and task success are not the same event.
- Stable-Baselines3's [PPO page](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html) presents PPO as a broad baseline across common action-space types, which is one reason practitioners often start there.
- Henderson and coauthors [argued](https://arxiv.org/abs/1709.06560) that deep RL results often vary enough across seeds and implementation details that reporting norms matter as much as algorithm choice.

## Common Mistakes

| Mistake | Why it bites | Fix |
|---|---|---|
| Using RL for a one-step labeled task | You add instability where supervised learning already has the answer | Start with a supervised or heuristic baseline and justify why sequential interaction is truly required |
| Choosing an algorithm before checking `action_space` | DQN and SAC solve different interface problems | Inspect `env.action_space` and rule out incompatible families immediately |
| Treating reward as the same thing as the real objective | The agent optimizes the proxy literally and may game it | Write down likely loopholes before training and test for them explicitly |
| Reporting one good seed as the result | Variance can reverse the story on the next run | Use a multi-seed protocol and report across-seed spread |
| Comparing runs with different wrappers or episode limits | You stop comparing policies and start comparing task definitions | Freeze wrappers, horizons, and evaluation settings before algorithm comparison |
| Ignoring `terminated` versus `truncated` | Timeouts can masquerade as solved or failed episodes | Respect Gymnasium's API and track both flags |
| Launching distributed sweeps before the local baseline learns | You scale confusion and spend compute on noise | Make one-machine SB3 baselines work first, then scale with RLlib if the question demands it |

## Quiz

1. A team has a large logged dataset of states and the correct human action for each case, but it cannot safely explore new actions in production. Someone proposes PPO because "the system is sequential." What would you recommend first, and why?
<details><summary>Answer</summary>
Start with supervised learning or prepare for offline RL or imitation learning rather than online PPO.
The key facts are that the labels already exist and safe exploration is unavailable.
RL only earns its complexity when interactive data collection and long-horizon consequences are the real problem.
If online exploration is not possible, the problem has already shifted toward the setting in [Module 2.1: Offline RL & Imitation Learning](../module-2.1-offline-rl-and-imitation-learning/).
</details>

2. You are controlling a simulator with four discrete actions, cheap resets, and low-dimensional observations. Interaction is abundant, but the reward is sparse. Which family would you try first between PPO, DQN, and SAC, and what is the first non-algorithm question you would ask?
<details><summary>Answer</summary>
PPO or DQN are both defensible because the action space is discrete, while SAC is not the natural fit.
The first non-algorithm question is about the reward and exploration signal.
If the agent rarely discovers meaningful states, replay alone may not rescue the task.
You would inspect whether the sparse reward needs safer shaping or a clearer task definition before expecting the algorithm name to solve it.
</details>

3. A continuous-control task uses a real-valued torque vector and every simulator step is expensive. A colleague wants DQN because it worked on a previous game project. What is the flaw in that reasoning?
<details><summary>Answer</summary>
DQN is built for discrete action spaces, so it is mismatched before training starts.
For a continuous `Box` action space with expensive interaction, SAC is often the more relevant family because it reuses experience and is designed for continuous control.
The main flaw is reusing an algorithm label from a different interface rather than checking the current environment contract.
</details>

4. You add a shaping reward to make learning faster, and the curve improves immediately. During manual inspection, the agent seems to prefer a stable intermediate behavior rather than completing the actual task consistently. What happened, and what should you do next?
<details><summary>Answer</summary>
You likely changed the optimization target in a way that made the proxy easier to maximize than the real objective.
That is classic reward hacking or unintended optimization.
The next step is to compare the shaped behavior against the task you actually care about, revise the shaping term, and inspect whether the shortcut is structurally encouraged by the wrapper.
</details>

5. Two PPO experiments differ only by seed. One run reaches a very high reward, while four others plateau much earlier. A status update drafts the best run as the headline result. Why is that unacceptable, and how should the result be rewritten?
<details><summary>Answer</summary>
It is unacceptable because one favorable seed is not reliable evidence of typical behavior.
The result should be rewritten as an across-seed summary that reports the mean and spread over the repeated runs.
If most seeds plateau, the honest interpretation is that the configuration is brittle or unstable, not solved.
</details>

6. A team parallelizes one hundred RLlib trials and selects the best checkpoint from the whole cluster. Every trial uses a single seed because repeating seeds "wastes compute." What is the methodological error?
<details><summary>Answer</summary>
The team has built a large selection machine that mostly amplifies variance rather than measuring robust performance.
Without repeated seeds per candidate, the cluster is rewarding lucky initializations as if they were strong configurations.
Distributed infrastructure does not remove the need for honest repeated evaluation.
</details>

7. An engineer says that training a policy for a robotic arm and aligning a chat model with preference data are basically the same problem because both are "RL." What important difference should you point out?
<details><summary>Answer</summary>
You should point out that RLHF has a different data pipeline, objective structure, and systems profile.
It often uses preference data, reward models, KL regularization, and large-scale language-model infrastructure rather than the simpler online control loop used in small Gymnasium tasks.
They are related historically, but they are not interchangeable project templates.
</details>

## Hands-On Exercise

- [ ] Install the core libraries first. `CartPole-v1`, `MountainCar-v0`, and `Pendulum-v1` work with a basic install. `LunarLander-v3` needs the Box2D extras.

```bash
pip install stable-baselines3 gymnasium
pip install "gymnasium[box2d]"
```

- [ ] Create a short PPO baseline on `CartPole-v1` and confirm that you can finish a small run on a laptop.

```python
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO, DQN, SAC
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.env_util import make_vec_env

train_env = make_vec_env("CartPole-v1", n_envs=4, seed=0)
model = PPO("MlpPolicy", train_env, verbose=1, seed=0)
model.learn(total_timesteps=10000)

eval_env = gym.make("CartPole-v1")
mean_reward, std_reward = evaluate_policy(
    model,
    eval_env,
    n_eval_episodes=10,
)
print(f"single-seed mean={mean_reward:.2f} +- {std_reward:.2f}")
```

- [ ] Save the trained policy and reload it so the checkpoint becomes a real artifact instead of a one-off process state.

```python
train_env = DummyVecEnv([lambda: gym.make("CartPole-v1")])
model = PPO("MlpPolicy", train_env, verbose=1, seed=0)
model.learn(total_timesteps=10000)
model.save("ppo_cartpole_demo")

loaded_model = PPO.load("ppo_cartpole_demo", env=train_env)
eval_env = gym.make("CartPole-v1")
mean_reward, std_reward = evaluate_policy(
    loaded_model,
    eval_env,
    n_eval_episodes=10,
)
print(f"reloaded mean={mean_reward:.2f} +- {std_reward:.2f}")
```

- [ ] Repeat the same PPO training for five seeds and report the across-seed mean and standard deviation. Do not stop at the per-episode standard deviation from a single run.

```python
seed_scores = []

for seed in [0, 1, 2, 3, 4]:
    train_env = make_vec_env("CartPole-v1", n_envs=4, seed=seed)
    model = PPO("MlpPolicy", train_env, verbose=1, seed=seed)
    model.learn(total_timesteps=10000)

    eval_env = gym.make("CartPole-v1")
    mean_reward, std_reward = evaluate_policy(
        model,
        eval_env,
        n_eval_episodes=10,
    )
    print(f"seed={seed} mean={mean_reward:.2f} episode_std={std_reward:.2f}")
    seed_scores.append(mean_reward)

print(f"across-seed mean={np.mean(seed_scores):.2f}")
print(f"across-seed std={np.std(seed_scores):.2f}")
```

- [ ] Run a reward-shaping experiment on `MountainCar-v0`. Watch the training logs and compare the evaluation result to the unshaped environment. Write down whether shaping accelerated learning, changed the agent's style, or introduced a suspicious shortcut.

```python
class PositionBonus(gym.RewardWrapper):
    def reward(self, reward):
        position = self.env.unwrapped.state[0]
        return reward + 0.05 * float(position)

base_env = gym.make("MountainCar-v0")
shaped_env = PositionBonus(gym.make("MountainCar-v0"))

base_model = PPO("MlpPolicy", base_env, verbose=1, seed=0)
base_model.learn(total_timesteps=10000)

shaped_model = PPO("MlpPolicy", shaped_env, verbose=1, seed=0)
shaped_model.learn(total_timesteps=10000)

base_eval_env = gym.make("MountainCar-v0")
shaped_eval_env = PositionBonus(gym.make("MountainCar-v0"))

base_mean, base_std = evaluate_policy(
    base_model,
    base_eval_env,
    n_eval_episodes=10,
)
shaped_mean, shaped_std = evaluate_policy(
    shaped_model,
    shaped_eval_env,
    n_eval_episodes=10,
)

print(f"base mean={base_mean:.2f} +- {base_std:.2f}")
print(f"shaped mean={shaped_mean:.2f} +- {shaped_std:.2f}")
```

- [ ] Inspect the environment interface directly once, so you can see what the agent actually receives and returns at runtime.

```python
env = gym.make("CartPole-v1")
obs, info = env.reset(seed=0)
print("obs shape:", np.shape(obs))
print("action space:", env.action_space)

action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
print("reward:", reward)
print("terminated:", terminated)
print("truncated:", truncated)
```

- [ ] Completion check: confirm you ran multi-seed eval and reported standard deviation across seeds, not just mean.
- [ ] Completion check: confirm you noticed at least one reward-shaping side effect or at least one suspicious change in behavior after shaping.
- [ ] Completion check: name one situation where you would NOT use RL for this problem class.

## Sources

- https://stable-baselines3.readthedocs.io/en/master/
- https://stable-baselines3.readthedocs.io/en/master/guide/algos.html
- https://stable-baselines3.readthedocs.io/en/master/guide/quickstart.html
- https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html
- https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
- https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html
- https://stable-baselines3.readthedocs.io/en/master/modules/sac.html
- https://gymnasium.farama.org/
- https://gymnasium.farama.org/introduction/basic_usage/
- https://gymnasium.farama.org/api/env/
- https://gymnasium.farama.org/api/spaces/
- https://docs.ray.io/en/latest/rllib/index.html
- https://docs.ray.io/en/latest/rllib/rllib-algorithms.html
- https://arxiv.org/abs/1801.01290
- https://arxiv.org/abs/1709.06560

## Next Module

Continue to [Module 2.1: Offline RL & Imitation Learning](../module-2.1-offline-rl-and-imitation-learning/).
