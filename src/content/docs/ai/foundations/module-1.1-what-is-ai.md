---
title: "What Is AI?"
slug: ai/foundations/module-1.1-what-is-ai
sidebar:
  order: 1
revision_pending: false
---

> **Complexity**: `[QUICK]`
>
> **Time to Complete**: 60-75 min
>
> **Prerequisites**: Curiosity, basic computer use, and a willingness to check answers instead of accepting them automatically

---

## Learning Outcomes

By the end of this module, you should be able to:

- Explain in plain language what AI means and how it differs from ordinary rule-following software.
- Tell the difference between rule-based systems, machine learning, generative AI, and agentic assistants using everyday examples.
- Identify what an AI tool can see, what it can change, and where a human approval boundary belongs.
- Check an AI answer by separating confident wording from evidence you can verify yourself.

## Why This Module Matters

Hypothetical scenario: you are planning a weekend trip with friends, and everyone is busy. You ask an AI travel assistant to compare dates, suggest hotels, and draft a shared plan. The assistant writes a confident answer that sounds helpful: it recommends a hotel near the station, says the museum is open late, and offers to book the cheapest non-refundable room. You almost click confirm before noticing that the hotel is in a different city with a similar name.

That mistake does not mean AI is useless, and it does not mean you did anything foolish. It means the tool sounded more certain than its evidence deserved. A beginner can be impressed by the smooth writing, the quick comparison, and the polite tone, while missing the more important question: how did the system reach that answer? This module gives you a simple map for asking that question before the answer affects your time, money, privacy, or decisions.

This track is for people starting from zero AI background, so we will not begin with servers, model training, or advanced system-building. We will begin with familiar experiences: email spam filters, photo apps that group pictures, streaming recommendations, chatbots that draft text, and assistants that can use tools. These examples are ordinary enough to understand, but serious enough to show why AI literacy is a real skill rather than a collection of slogans.

The goal is not to make AI mysterious or magical. The goal is to make it legible. Once you can tell whether a system is following rules, learning from examples, generating new content, or using tools to take actions, you can choose a sensible level of trust. You do not need to know advanced math to start; you need a clear vocabulary, a few reliable questions, and the habit of checking important outputs.

## AI in Plain Language

Artificial intelligence is a broad name for computer systems that appear to perform tasks we normally associate with judgment, pattern recognition, language, planning, or decision support. That does not mean the computer understands the world the way a person does. It means the system receives input, transforms it using rules or learned patterns, and produces an output such as a label, recommendation, prediction, piece of content, or next action.

In a simplified paraphrase of the OECD definition, an AI system uses the input it receives to work out an output that serves a stated or implicit objective. The result might be a prediction, recommendation, decision, or generated content that affects the physical world or a digital environment. Systems differ in how independently they operate and how much they can adapt after they enter use. For a beginner, the useful idea is the flow: something goes in, the system works out an output, and that output may affect what people see or do next.

In everyday language, AI is easiest to understand as software that handles ambiguity. A calculator does not need AI to add two numbers, because the rule is exact. A photo app that groups pictures of the same person faces a messier task, because faces vary with lighting, angle, age, expression, camera quality, and background. The value of AI often appears where the input is too varied for a simple rule to cover comfortably.

That flexibility is powerful, but it comes with a tradeoff. The more a system relies on learned patterns or generated language, the less you should expect it to behave like a simple calculator. It may be useful without being fully reliable, confident without being correct, and fluent without having evidence. Good AI use begins when you can hold both ideas at once: the tool can save time, and the tool can still be wrong.

Think of AI literacy like learning to read a nutrition label. You do not need to become a chemist before buying food, but you do need to know the difference between calories, ingredients, serving size, and marketing language. In the same way, you do not need to become a machine learning engineer before using AI, but you do need to know the difference between a rule, a learned pattern, a generated answer, and an action taken on your behalf.

## Ordinary Software vs AI

Ordinary software often follows instructions that people wrote directly. If you set an alarm for 7:00 AM, the app does not infer your sleep goals or guess whether tomorrow is important. It checks the time, follows a rule, and plays a sound. That kind of software can still be complex, but its decision path is usually easier to explain because the important conditions were written in advance by humans.

A simple rule-based email filter works the same way. If the sender is on your blocked list, move the message to junk. If the subject contains a phrase you personally blocked, hide it. The computer is not learning what spam means in a broad sense; it is applying instructions someone supplied. When the result is wrong, you can often point to the exact rule that caused the mistake.

```text
if sender_is_blocked:
    move_message_to_junk()
else if subject_contains_blocked_phrase:
    move_message_to_junk()
else:
    keep_message_in_inbox()
```

Many AI systems work differently because they use patterns learned from examples. A modern spam filter may look at many signals: wording, sender reputation, link patterns, previous user reports, formatting, and similarities to messages seen before. No person writes one explicit rule for every possible spam message. The system learns a pattern from data and then applies that pattern to new messages it has never seen.

That shift changes how you check the system. With ordinary software, you ask what rule ran and whether the rule was written correctly. With a learned system, you also ask what examples shaped it, whether the current situation resembles those examples, and how costly a mistake would be. A learned spam filter can catch tricks that a simple rule misses, but it can also hide an important message because the message resembles spam.

Generative AI adds another twist because it creates new text, images, audio, code, or plans instead of only sorting existing items. A chatbot can write a polite email, summarize a long article, suggest quiz questions, or explain a concept in several styles. That feels conversational, which is why beginners sometimes treat it like a person who knows things. Underneath, it is still a system producing likely output from input and context.

Agentic assistants add one more layer: they can use tools. Instead of only saying "Here is a possible trip plan," an assistant might search calendars, compare prices, fill a booking form, send an email, or make a purchase if you give it access. The important beginner question changes from "Is the answer correct?" to "What is this tool allowed to do if it is wrong?" A wrong suggestion is annoying; a wrong purchase may cost money.

The useful analogy is a kitchen. A rule-based timer rings when the minutes run out. A learned recommendation system notices that you often cook vegetarian meals and suggests similar recipes. A generative assistant drafts a shopping list and rewrites the instructions for beginners. An agentic assistant orders the groceries. Each can help, but each deserves a different level of checking because each can affect your life in a different way.

## The Four Categories You Will Actually Meet

The word "AI" is too broad to be useful by itself. It appears on search boxes, writing tools, phones, cameras, learning apps, customer support chats, design tools, and office software. If you treat every AI label as the same thing, you will either trust too much or reject too much. A better habit is to ask what mechanism is doing the work and what kind of output or action follows.

```text
Everyday AI map

Rule-based system
  -> follows explicit human-written rules

Machine learning system
  -> learns patterns from examples

Generative AI system
  -> creates new text, images, audio, code, or plans

Agentic assistant
  -> uses tools across steps and may take actions
```

Rule-based systems are the easiest starting point because they behave like checklists. A thermostat may turn heat on below a chosen temperature and turn it off above another temperature. A banking app may warn you when a password is too short. A form may reject an invalid date. These systems can be frustrating when the rule is too rigid, but their main advantage is that the rule can usually be inspected, tested, and explained.

The main failure of rule-based systems is brittleness. They work well when the situation matches the rule writer's expectations, and they work poorly when reality comes in a shape the rule did not anticipate. A blocked-phrase email filter might hide a harmless newsletter because it contains a suspicious word. A shopping-site rule might reject a valid address because the address format is unusual. The system is not confused; it is simply narrow.

Machine learning systems learn patterns from examples instead of relying only on rules written one by one. A photo app can learn to group pictures with similar faces. A music service can recommend songs because people with similar listening patterns liked them. A bank can flag unusual card activity because it differs from your normal behavior. These systems are useful when the pattern is real but hard to describe with a tidy rule.

The main failure of machine learning is pattern mismatch. The system can learn from examples that are incomplete, outdated, biased, or unlike the current situation. A recommendation system may keep suggesting baby products long after a gift purchase because it learned the wrong meaning from your shopping history. A photo app may group different people together because lighting and angle made them look similar to the model. The output may be statistical rather than certain.

Generative AI systems create new content. A large language model can write a study guide, rewrite a confusing paragraph, propose a packing list, draft a message to a landlord, or explain a technical term in simpler language. Image generators, music generators, and video generators belong to the same broad family of systems that produce new artifacts. They are especially attractive because they can meet you in ordinary language instead of requiring a special interface.

The main failure of generative AI is plausible invention. The answer may be grammatical, polished, and organized while still containing details that are wrong, missing, or made up. A chatbot can invent a book title, misstate a policy, summarize an article it did not actually read, or give outdated advice with calm confidence. Fluency is a writing quality, not proof. The more important the output is, the more you need a way to verify it.

Agentic assistants combine AI with tools, memory, steps, and permissions. A travel assistant might ask clarifying questions, search flights, compare hotels, draft an itinerary, and wait for your approval before booking. A study assistant might gather sources, make flashcards, schedule practice, and quiz you later. A work assistant might read a document, draft an email, and create a calendar invite. The defining feature is not only conversation; it is action across multiple steps.

The main failure of agentic assistants is that a mistaken conclusion can become a real action. If a chatbot gives you a bad restaurant recommendation, you can ignore it. If an agent books the restaurant, sends invitations, and charges a deposit before you review the details, the mistake has already moved into the world. Agentic systems need clear permission boundaries because usefulness and risk grow together when a tool can act.

Real products often combine categories. A shopping app may use rules to block invalid coupons, machine learning to rank products, generative AI to summarize reviews, and an agentic assistant to place an order. The safe question is not "Is this AI?" The safe question is "Which part is rule-based, which part learned from examples, which part generated content, and which part can take action?"

Here is a compact comparison you can reuse whenever you meet a new tool:

| Category | Everyday Example | What It Does Well | What To Check |
|---|---|---|---|
| Rule-based system | A password rule that requires a minimum length | Applies clear instructions consistently | Whether the rule fits the situation |
| Machine learning system | A photo app that groups pictures by person | Finds patterns across many examples | Whether the pattern could be wrong or biased |
| Generative AI system | A chatbot that drafts a thank-you email | Creates useful first drafts quickly | Whether the facts, tone, and assumptions are correct |
| Agentic assistant | A travel helper that can book a hotel | Carries work across several steps | What it can see, what it can change, and who approves |

Use the table as a beginner's safety map rather than a strict academic definition. Some systems blur boundaries, and the labels may change as products evolve. The point is to slow down the moment an AI badge appears and ask what kind of mechanism is behind it. That habit keeps you from trusting a generated answer like a verified fact or letting a tool take action before you understand its permission.

## Worked Example: Planning A Trip

Imagine you are organizing a short trip for four people. You want a city that is reachable by train, a hotel near the station, one museum visit, and a restaurant that can handle a vegetarian guest. This is a familiar task with enough moving parts to show why AI can be useful. It also contains real risks because a wrong date, location, cancellation policy, or dietary assumption can create stress or cost money.

A rule-based tool could help with the parts that are exact. It might reject a hotel check-in date that comes after the check-out date, warn when a password is too short, or show only trains that leave after 8:00 AM because you selected that filter. The tool does not need to understand travel; it needs to follow explicit conditions. If the filter is wrong, the fix is usually to change the rule or selection.

A machine learning tool could help with the parts that involve patterns. It might recommend hotels similar to places travelers liked before, rank restaurants based on many reviews, or suggest destinations that match your past choices. This is useful because the system can compare many signals quickly. It is also risky because "people like you liked this" is not the same as "this matches your exact trip, budget, accessibility needs, and values."

A generative AI tool could draft the plan in ordinary language. It might turn scattered notes into a clean itinerary, explain the difference between two neighborhoods, rewrite the plan for a friend who hates long schedules, or create a packing list. This is where AI can feel most impressive because it makes messy information readable. The weak point is that the readable plan may include assumptions the system did not verify.

An agentic assistant could go further by using tools. It might check calendars, search hotel sites, compare prices, put the museum into a shared schedule, draft messages to the group, and prepare a booking. At that point, the assistant is no longer only giving you words. It is moving through a workflow. The same capability that saves time also means you need approval gates before anything irreversible happens.

The first approval boundary is information access. Does the assistant need to see your full calendar, all emails, payment details, passport number, or location history to perform this task? Usually it does not. A beginner-friendly boundary is to share the smallest useful amount of information. For travel planning, that might mean dates, city preferences, budget range, and accessibility needs, but not unrelated private messages or saved payment credentials.

The second approval boundary is action. It is usually fine for an assistant to draft an itinerary, summarize options, or prepare a booking form for review. It is much more serious for the assistant to purchase a ticket, reserve a non-refundable hotel, send an email to everyone, or share personal information with a third-party site. When an action costs money, reveals private data, or affects other people, the human should approve it.

The third approval boundary is evidence. If the assistant says the museum is open late on Saturday, you should ask where that claim comes from before building the trip around it. A link to the museum's official hours is stronger evidence than the assistant's memory. A current booking page is stronger evidence than a general travel blog. The more specific the claim, the more specific the check should be.

The trip example teaches the whole taxonomy without requiring technical background. Rules are good for exact filters, machine learning is good for patterns, generative AI is good for drafts and explanations, and agentic assistants are useful when work spans steps. The same example also shows the basic safety habit: read the output as a proposal, verify important claims, and keep final approval over actions that matter.

## Trust Boundaries For Everyday AI Use

A trust boundary is a line that says what a tool may do without asking you again. Beginners sometimes hear "trust boundary" and assume it belongs only to engineers, but the idea is ordinary. You already use trust boundaries when you let a maps app suggest a route but not drive your car, let a banking app show a balance but not send money without confirmation, or let a store remember your address but not choose gifts for your friends.

The simplest boundary question is "What can it see?" An AI tool may ask for a prompt, a document, a photo, a contact list, a calendar, or a browser session. Each extra source of information can improve the answer, but it also increases privacy risk. Before sharing, ask whether the information is necessary for the task and whether a smaller excerpt would work. You can often get useful help without handing over the whole context.

The second boundary question is "What can it change?" A chatbot that only answers questions is different from an assistant that can send messages, edit files, submit forms, place orders, or delete content. Change is where mistakes become harder to undo. If a tool can alter something, the boundary should be tighter: preview first, approve before sending, confirm before payment, and keep a record of what changed.

The third boundary question is "Who approves?" Human approval is not a decorative button. A useful approval step shows the proposed action, the evidence behind it, the cost or consequence, and the way to undo it if possible. If an assistant asks "Confirm booking?" but hides the hotel city, cancellation policy, and total price, the approval is weak. A good approval step makes the decision understandable before you click.

You can sort everyday AI tasks into low, medium, and high stakes. Low-stakes tasks include brainstorming birthday party themes, rewriting a casual note, or suggesting practice questions for a topic you are learning. Medium-stakes tasks include drafting a work message for your review or organizing information before a decision. Summarizing a lease or comparing health insurance terms can become consequential when you rely on the summary to act. High-stakes tasks include medical, legal, financial, safety, or irreversible decisions. The consequences and your reliance on the output determine how much outside evidence and human review you need.

The boundary should also match your own expertise. If you ask AI to explain a topic you understand well, you can spot many mistakes. If you ask it about a topic you barely know, you may not recognize false confidence. That does not mean you cannot use it for unfamiliar topics. It means you should ask for sources, compare multiple references, and avoid acting on the answer until a more authoritative source confirms it.

A useful beginner rule is "draft freely, decide carefully." Let AI help you explore ideas, organize messy notes, compare options, and create first drafts. Slow down when the output claims facts, affects people, spends money, shares private data, changes a record, or tells you what to do in a serious situation. This rule keeps AI useful while making sure responsibility stays with the person who understands the real-world consequences.

NIST's voluntary AI Risk Management Framework (AI RMF) 1.0, released in 2023, organizes AI risk work through the functions Govern, Map, Measure, and Manage. You do not need the full framework in this first module, but the beginner version is already visible: know who is responsible, map what the tool can see and do, measure whether the answer is reliable enough, and keep managing risk as the system is designed, used, and evaluated. Serious AI literacy starts with those habits.

## Reading AI Answers

An AI answer is a claim, not a conclusion delivered from authority. This is especially important with generative AI because the answer often arrives in polished paragraphs that feel complete. A smooth paragraph can make weak evidence feel stronger than it is. Instead of asking "Does this sound smart?" ask "What would prove or disprove this?" That question turns the output into something you can inspect.

Start by separating wording from evidence. Wording is the style, confidence, and organization of the answer. Evidence is the support behind the claim: a source, a calculation, a current document, an official page, a direct observation, or a test you can repeat. AI is often strong at wording and uneven at evidence. A beginner should enjoy the wording while refusing to treat it as proof.

Next, separate general advice from specific claims. "Pack layers because spring weather can change" is a general suggestion that may be reasonable without deep research. "The 9:30 train is the cheapest option this Saturday" is a specific claim that needs a current source. "This article argues that privacy depends on data minimization" needs a link or quotation from the article. Specific claims deserve specific checks.

Then look for missing assumptions. If an assistant recommends a restaurant, did it consider distance, price, dietary needs, accessibility, noise level, or whether the place is open that day? If it summarizes a document, did it see the whole document or only a pasted excerpt? If it explains a law, policy, or health topic, is it using current authoritative information? AI answers often sound complete because they omit the uncertainty.

For generated writing, review tone and ownership. An assistant may write an apology that is grammatically correct but too cold for the relationship. It may draft a student paragraph that sounds polished but does not reflect what the learner actually understands. It may produce a work message that is efficient but more aggressive than intended. Correctness is not the only standard; suitability matters too.

For generated explanations, ask the tool to show the reasoning in simple steps, then check the steps. This does not mean every hidden model process becomes visible. It means you can ask for an explanation that exposes assumptions, definitions, examples, and source needs. If the answer cannot be broken into checkable parts, treat it as a starting point for learning rather than something to rely on.

For agentic assistants, read the proposed action as carefully as the answer. The assistant may summarize why a hotel looks good, but the action might book the wrong dates. It may draft an email well, but the recipient list might include someone unintended. It may prepare a form correctly, but submit it before you review the privacy implications. In agentic workflows, the final action often matters more than the explanation.

The practical review habit is simple: underline the claims, circle the actions, and mark the evidence. Claims are things the answer says are true. Actions are things the tool wants to do or wants you to do. Evidence is what supports the claims or justifies the actions. If an answer has many claims and few evidence marks, it may still be useful for brainstorming, but it is not ready for important decisions.

## When To Use AI And When Not To

Use rule-based tools when the condition is clear and repeatability matters. A calendar reminder, password rule, form validation, budget limit, or email filter can be simple and reliable precisely because it does not guess. Beginners sometimes assume newer AI is always better, but boring software is often the right answer when the task is exact. If a rule solves the problem cleanly, adding AI may only add uncertainty.

Use machine learning when examples and patterns matter more than hand-written rules. Recommendations, spam detection, photo grouping, speech recognition, and fraud alerts can benefit from learned patterns because the input varies so much. The key question is whether the pattern learned from past examples still fits the current case. If your situation is unusual, new, or underrepresented, the system may be less reliable than it appears.

Use generative AI when you need drafting, summarizing, rephrasing, translation help, idea generation, or an explanation at a different level of detail. It is especially useful when you can review the output yourself or compare it with a trusted source. It is weakest when you ask it for facts you cannot check, citations it does not actually have, or decisions where a confident mistake would cause harm.

Use agentic assistants when the task genuinely needs several steps and tools, and when you can keep approval over important actions. A good early use is asking the assistant to gather options, prepare a draft, or build a checklist for your review. A risky use is letting it spend money, contact people, submit forms, or alter records without a clear preview. Autonomy should grow only after reliability and boundaries are proven.

Do not use AI as a substitute for professional accountability. Medical, legal, financial, safety, and employment decisions can be supported by AI for organization or preparation, but the output should not become the final authority. People and organizations retain decision roles, with responsibilities assigned according to the role and context. That is why verification, source checking, and human judgment belong at the center of serious AI use.

## A Beginner's First AI Conversation

The safest way to begin is to choose a low-stakes topic where you can recognize whether the answer helped. Ask for something like a study plan for learning basic spreadsheet formulas, a clearer version of a paragraph you already wrote, or a comparison of two phone settings you can check in the app itself. Low-stakes practice lets you notice the tool's strengths and weaknesses without putting money, privacy, or another person at risk.

Start the conversation with context, not a command. Instead of writing "explain AI," write "I am a beginner with no AI background, and I want a plain-language explanation with two everyday examples and one thing to watch out for." That prompt does not require special skill, but it gives the tool a job, an audience, a format, and a safety expectation. Better input usually produces easier output to review.

After the first answer, do not immediately ask for more content. Ask a checking question. You might write, "Which parts of your answer are definitions, which parts are examples, and which parts would need an outside source?" This forces the conversation away from smooth performance and toward evidence. It also trains you to see that an AI answer has parts, and different parts deserve different levels of trust.

Then ask for a simpler version. If the tool cannot explain the idea without jargon, the explanation may not be serving you yet. A useful assistant should be able to restate a concept for a beginner without losing the main point. When it introduces terms such as model, training, prompt, inference, context, or hallucination, ask for one sentence and one everyday example for each term before moving on.

Next, ask for a mistake check. A strong beginner prompt is "What are three ways someone could misuse this answer?" This works because the tool may be good at listing limitations even when it is not perfect at judging itself. You still need your own review, but the question changes the mode from confident delivery to cautious inspection. That is a healthier relationship with the tool.

When the output includes a claim you might repeat to someone else, ask for sources or a way to verify it. Do not ask only "Are you sure?" because a generative system can answer confidently again. Ask "What source should I check?" or "What exact phrase should I search on an official page?" The goal is to move from the model's wording to something outside the model that can support or correct the claim.

When the output includes a recommendation, ask what would change the recommendation. If an assistant recommends a study schedule, ask how the plan changes for someone with only twenty minutes a day. If it recommends a hotel, ask how the answer changes for a wheelchair user, a strict budget, or a refundable booking requirement. This reveals assumptions that may have been hidden inside a polished first answer.

When the output includes an action, pause. Drafting a message is different from sending it. Preparing a form is different from submitting it. Listing hotels is different from booking one. A beginner's strongest habit is to keep AI on the drafting side until the proposed action is visible, reversible where possible, and approved by the person who owns the consequence. That habit matters long before you learn any advanced AI vocabulary.

Keep a small notebook of misses as well as wins. Write down when the tool saved time, when it confused you, when it made an unsupported claim, and when your prompt was too vague. This is not busywork. It builds judgment. Over time, you will notice which tasks are good fits, which tasks need stronger checking, and which tasks should stay outside AI assistance entirely.

Also notice how the tool behaves when you say no. If it changes the answer gracefully, asks a clarifying question, or narrows the scope, that is useful behavior. If it keeps pushing the same recommendation, invents new confidence, or ignores a constraint you clearly stated, that is a warning sign. You are not only evaluating the first answer. You are evaluating the conversation pattern, because real AI use often involves correction, disagreement, and meaningful revision before the output is good enough.

The point of a first AI conversation is not to get the perfect answer. The point is to practice the loop that makes later AI use safer: give context, inspect the output, separate claims from evidence, ask about assumptions, and keep approval over actions. Once that loop feels natural on everyday tasks, the later modules on language models, prompting, verification, privacy, and AI-supported work will have somewhere solid to land.

## Did You Know?

- [The OECD revised its AI system definition in 2023 to emphasize machine-based systems that infer from input and generate outputs such as predictions, content, recommendations, or decisions.](https://oecd.ai/en/wonk/definition-)
- [The NIST AI RMF Playbook describes the voluntary AI RMF 1.0, released on January 26, 2023, and organizes work around Govern, Map, Measure, and Manage.](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook)
- The same product can combine several mechanisms, so one "AI assistant" may include rules, learned rankings, generated text, and tool-using steps in a single workflow.
- A beginner can often reduce risk by asking three plain questions before using a tool: what can it see, what can it change, and what evidence supports the answer?

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating every AI label as the same kind of system | Product names hide whether the tool follows rules, learns patterns, generates content, or takes actions. | Ask which mechanism is doing the work before deciding how much to trust the output. |
| Assuming a fluent answer is a verified answer | Generative systems are good at producing smooth language, and smooth language feels like confidence. | Separate wording from evidence, then check important claims against sources you trust. |
| Sharing more private context than the task requires | The tool asks for context, and it is tempting to paste the whole message, document, or thread. | Share the smallest useful excerpt, remove sensitive details, and check the tool's data settings. |
| Letting an assistant act before reviewing the action | Multi-step tools feel efficient, especially when they prepare forms, messages, bookings, or purchases. | Keep preview and approval steps before spending money, sending messages, or changing records. |
| Using AI where a simple rule would be clearer | Newer tools can make ordinary filters, reminders, and checks feel outdated even when they work well. | Prefer rule-based tools when the condition is exact and the cost of ambiguity is unnecessary. |
| Trusting AI most on topics you know least | Beginners may not notice when an answer skips assumptions, invents details, or uses outdated information. | Ask for sources, compare with authoritative references, and avoid acting until you understand the evidence. |
| Rejecting all AI because some tools make mistakes | Bad marketing and visible errors can make every AI feature look equally unreliable. | Separate useful drafting and pattern-finding from high-stakes decisions that require stronger verification. |

## Quiz

<details>
<summary>1. A website rejects passwords shorter than twelve characters. Which category best describes this behavior, and why?</summary>

This is a rule-based system because the site is applying an explicit condition written in advance. The password is either shorter than twelve characters or it is not, and the software does not need to learn from examples to make that decision. The behavior can still annoy users if the rule is poorly designed, but the mechanism is straightforward. This is different from machine learning, which would infer patterns from data, and different from generative AI, which would create new content.

</details>

<details>
<summary>2. A photo app groups pictures that appear to show the same person. Which category is most likely involved, and what should you remember about mistakes?</summary>

This is most likely a machine learning system because the app recognizes patterns across many visual examples instead of relying on a simple hand-written rule for every face. The useful caution is that pattern recognition can be wrong. Lighting, age, angle, camera quality, and similar-looking faces can confuse the system. You can use the grouping as a helpful convenience while still checking it before relying on it for anything important.

</details>

<details>
<summary>3. A chatbot writes a polished school presentation outline about a historical event. What should you check before using it?</summary>

You should check the factual claims, dates, names, and sources instead of assuming polish means accuracy. This is a generative AI system because it creates new text from your prompt and context. The outline can be useful as a draft, but it may omit important context or invent details. A good next step is to compare its claims with a textbook, teacher-provided material, library source, or official reference before presenting it as your own understanding.

</details>

<details>
<summary>4. A travel assistant can search hotels, fill a booking form, and click purchase after you approve. What boundary matters most?</summary>

The important boundary is the action approval boundary. The assistant may be useful for searching and preparing options, but booking a hotel spends money and creates a real commitment. Before approval, you should see the city, dates, total price, cancellation policy, room details, and payment method. This is an agentic assistant because it uses tools across steps, so its permissions matter as much as the wording of its recommendation.

</details>

<details>
<summary>5. Why is "what can it see, what can it change, and who approves?" a useful beginner checklist?</summary>

The checklist turns vague trust into specific boundaries. "What can it see?" helps you control privacy and context. "What can it change?" helps you notice when a tool can affect money, messages, files, or records. "Who approves?" keeps important actions under human review. This checklist works across rule-based tools, machine learning systems, generative AI, and agentic assistants because it focuses on evidence and consequences.

</details>

<details>
<summary>6. An AI answer sounds confident but gives no source for a specific claim. What should you do with that claim?</summary>

Treat the claim as unverified until you can check it somewhere reliable. Confidence and clear writing are not the same as evidence. If the claim is low-stakes, you may use it as a clue for further research. If the claim affects money, safety, health, law, work, or another person, you should find an authoritative source before acting. The answer may still be useful, but it has not earned trust for that specific claim.

</details>

<details>
<summary>7. When is ordinary rule-following software better than AI?</summary>

Ordinary rule-following software is often better when the condition is clear, stable, and easy to test. A reminder time, a spending limit, a required form field, or a password length rule does not need a model to guess. Adding AI to an exact task can create uncertainty without adding value. AI becomes more useful when inputs are ambiguous, varied, language-heavy, or difficult to describe with simple rules.

</details>

## Hands-On Exercise

In this exercise, you will classify everyday tools and set simple boundaries for each one. Choose three tools you already understand: one email or messaging feature, one photo or media feature, and one assistant or chatbot feature. If you do not use one of those categories, imagine a common example such as a spam filter, a photo-tagging app, and a travel-planning assistant.

For each tool, write a short note in your own words. Do not try to sound technical. The goal is to practice seeing the mechanism behind the label and the consequence behind the output. A strong answer might say that a spam filter uses rules and learned patterns, that a photo app uses pattern recognition, and that a travel assistant becomes higher risk when it can book or send information without review.

### Tasks

- [ ] Name the tool and classify it as rule-based, machine learning, generative AI, agentic, or a combination.
- [ ] Write one sentence explaining what input the tool uses and what output it produces.
- [ ] Write one sentence identifying the main thing that could go wrong if the output is wrong.
- [ ] Decide what the tool should be allowed to see for this task and what information should stay private.
- [ ] Decide what the tool should be allowed to change automatically and what should require human approval.
- [ ] List one piece of evidence you would want before trusting an important claim from the tool.

<details>
<summary>Suggested solution</summary>

A spam filter may combine rules and machine learning because it can block messages from known senders while also learning patterns from many examples of unwanted mail. The main risk is hiding an important message, so you might keep a junk folder review habit and avoid deleting messages automatically. A photo-tagging app is mainly a machine learning system because it groups images by visual patterns. The main risk is misidentifying people, so you should check names before sharing albums. A travel-planning assistant may be generative when it drafts an itinerary and agentic when it can search sites or prepare bookings. The main risk is turning a wrong assumption into a purchase, so it should show current sources and require your approval before booking.

</details>

### Success Criteria

- [ ] You classified at least three everyday tools using the four-category map from this module.
- [ ] You explained each tool using ordinary language rather than vendor marketing language.
- [ ] You identified what each tool can see and what private information should stay outside the task.
- [ ] You identified what each tool can change and which actions need human approval.
- [ ] You named at least one external evidence check for an important AI-generated claim.
- [ ] You can explain why fluency, recommendations, and tool access require different levels of trust.

## Next Module

Continue to [What Are LLMs?](./module-1.2-what-are-llms/) to learn why modern chatbots can respond in natural language and why that ability is useful but not the same as guaranteed understanding.

## Sources

- [OECD.AI: What is AI? Can you make a clear distinction between AI and non-AI systems?](https://oecd.ai/en/wonk/definition-)
- [OECD AI Principles](https://oecd.ai/en/ai-principles)
- [NIST AI Risk Management Framework Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST AI Risk Management Framework: Generative Artificial Intelligence Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)
- [NIST Trustworthy and Responsible AI](https://www.nist.gov/trustworthy-and-responsible-ai)
- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
- [Google People + AI Guidebook](https://pair.withgoogle.com/guidebook)
- [Stanford AI Index Report](https://aiindex.stanford.edu/report/)
- [IBM: What is machine learning?](https://www.ibm.com/topics/machine-learning)
