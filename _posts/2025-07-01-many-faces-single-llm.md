---
layout: distillPost
title: LLM with a Thousand Faces
date: 2025-07-15
description: A reflection on the structure and behavior of LLM-based agents, and what lies beneath the surface.
_styles: >
  h3, h2, h1 {
    padding-top: 0!important;
  }
distill: true
mathjax: true
bibliography: llm.bib
---

We've come a long way, from single-task LLMs (like translation or classification) to general-purpose models capable of performing a wide range of tasks. 
Giving these models the ability to **call tools** has elevated them to the status of "agents", systems with the apparent capacity to act on their environment.

"AI agents" is now a term you hear everywhere. 
But the mental image people form when they hear "agent" can vary dramatically. Some imagine superintelligent machines capable of transforming the society, while others imagine nefarious systems plotting to overthrow humanity.

Sometimes, I find myself so caught up in this narrative that I forget to zoom out and remember what's really going on under the hood: how these systems are actually constructed.

This post is a reflection and a reminder: **what is behind these agents**.

## Enriching Context

At the core, each "agent" is just a call to an LLM with a structured input, often referred to as a **prompt** or **context**. It typically consists of:

* **Instructions**: How the LLM should behave or reason (“You are an expert physicist”).
* **Task**: The goal or problem to solve (“Explain the theory of relativity”).
* **Contextual Support**: Supporting information, such as examples, prior conversation turns, tool outputs, or formatting guidance.

Whether a task is handled by a single LLM or given to others, it's all about crafting the right context to elicit the best possible response.
Even in multi-agent systems, where tasks are handed off, these "other agents" are often just the same LLM being prompted differently.

## Human-AI Collaboration: Who is the tool?

Although I understood how LLMs work, I was so immersed in chatting with ChatGPT that I momentarily forgot it's just an LLM under the hood, reprocessing the same base input over and over, each time with a slightly richer context.

Here's what that might look like in a simple session:

* **Instruction:** You are an expert physicist.
* **Task:** Explain the theory of relativity.
* **Context:** (starts empty)

The first output might be too dense. So I say:

> "Break it down for a novice."

Now that instruction becomes part of the new context, and the LLM tries again. The conversation continues, with each turn enriching the context to move closer to the desired outcome.

<div style="display: flex; flex-direction: column; align-items: center; margin: 0.5em; margin-bottom:0.25em;">
  <img
    class="img-fluid rounded z-depth-1"
    src="/images/blog/2025-07-01-many-faces-single-llm/human-as-tool.png"
    alt="Human as Tool Illustration"
    style="width: 75%; height: auto; border: 2px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); display: block; margin: 0 auto;">
</div>
<div style="font-style: italic; color: #666; font-size: 1.05em; text-align: center; margin-bottom: 0.5em;">
  Feedback from humans enhances the context, guiding the LLM to produce improved outputs.
</div>


### Deciding to enrich its own context

What if I had given no instruction at all, just the task:

> Explain the theory of relativity. You're free to take on any persona to make the explanation effective.

The LLM might respond:

> "Let me take on the persona of Richard Feynman..."

And I say:

> "Yes, go ahead."

Now the updated context includes:

> *"I am Richard Feynman, and here's how I explain the theory of relativity..."*

In this case, the LLM is **writing to its own contextual support** to improve its performance. This mirrors how agents delegate tasks to specialized sub-agents; essentially, **same LLM, different prompts**. This might as well be referred to as **Agent Calling**,  unless you explicitly model the workflow.

> "other agents" are just creative reuses of the LLM with new instructions and context.


## Tool Calling

Now imagine the input also mentions external tools. The LLM might decide it's best to call a calculator, a search engine, or a code interpreter.
So we call these tools. This **tool use** enriches the context with new information, like equations, results, or facts, which is then fed back into the next LLM call.

Again, it's all about context enrichment.

<div style="display: flex; flex-direction: column; align-items: center; margin: 0.5em; margin-bottom:0.25em;">
  <img
    class="img-fluid rounded z-depth-1"
    src="/images/blog/2025-07-01-many-faces-single-llm/tool-call.png"
    alt="Tool Calling Illustration"
    style="width: 75%; height: auto; border: 2px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); display: block; margin: 0 auto;">
</div>
<div style="font-style: italic; color: #666; font-size: 1.05em; text-align: center; margin-bottom: 0.5em;">
  Tool calling enriches the context for LLMs to give desired results.
</div>


## Agent Calling


When other agents and their functionalities are available as callable options, I tend to think of this as **agent calling**, or simply using **more intelligent tools**. While I haven't yet seen work where new agents are entirely *programmed* by a previous LLM (i.e., constructed from scratch), that too should be possible in principle.

In many cases, these agents aren't fundamentally different entities; they're just **LLMs used as intelligent tools**. Some are initialized with predefined prompts like *"You are a physicist,"* while others are dynamically created at runtime, taking on whatever instructions the current LLM chooses to provide.

> Other tools may be simple deterministic functions. But **agent-tools** are LLMs themselves, capable not just of retrieving knowledge, but of **generating it**.


<div style="display: flex; flex-direction: column; align-items: center; margin: 0.5em; margin-bottom:0.25em;">
  <img
    class="img-fluid rounded z-depth-1"
    src="/images/blog/2025-07-01-many-faces-single-llm/img.png"
    alt="Agentic Systems Illustration"
    style="width: 75%; height: auto; border: 2px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); display: block; margin: 0 auto;">
</div>
<div style="font-style: italic; color: #666; font-size: 1.05em; text-align: center; margin-bottom: 0.5em;">
  In a multi-agent system, tasks are achieved through the processes of tool-calling and agent-calling. This approach enriches the context for a single agent or transfers information to another agent to enhance their context.
</div>