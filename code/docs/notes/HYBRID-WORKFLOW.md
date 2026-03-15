# Hybrid Workflow Notes

Date: 2026-03-14

## Why this note exists

Ygg should not merely be a deterministic command wrapper.
It should become a practical **human/machine hybrid workflow surface**.

## Core tension

The machine benefits from:

- explicit command structure
- deterministic execution
- inspectable state
- reliable repetition
- bounded contracts

The human benefits from:

- natural language
- fluid exploration
- ambiguous but meaningful intent
- creative reframing
- adaptive interpretation

The design problem is not to pick one side.
It is to let each side contribute what it is better at.

## Working hypothesis

A good Ygg interface should let the human speak naturally while preserving a deterministic command substrate underneath.

This suggests a split architecture:

1. **Intent layer**
   - conversational
   - approximate
   - context-sensitive
   - good for planning and reframing

2. **Command layer**
   - explicit verbs
   - inspectable arguments
   - reproducible outcomes
   - safe to automate

3. **Promotion layer**
   - decides what becomes durable
   - prevents meaningful outcomes from vanishing silently

## Near-term interface ideas

### 1. Suggested-next-command cards
After a meaningful Ygg response, show a short list of likely next commands.
This lowers memory burden without removing explicit structure.

### 2. Explainable translation
Allow the system to say:

- "Given what you asked, the likely Ygg action is..."
- "Here are 2-3 candidate commands"
- "Here is why I chose this one"

Concrete first implementation:

- `ygg suggest "<natural language>"`

This command should interpret intent and produce explicit candidate Ygg commands without executing them.


### 3. Verb help from inside the CLI
Examples:

```bash
ygg help branch
ygg explain promote
```

### 4. Optional TUI/GUI later
A richer interface may help eventually, but it should remain optional.
The deeper value is the workflow architecture, not the ornament of the interface.

## Design principle

The interface should be poetic in topology and consequence, but operationally clear.

## Failure condition

This direction is failing if:

- the system becomes so conversational that it loses inspectability,
- the human cannot tell what deterministic action is actually being taken,
- or the explicit command layer becomes too cumbersome to be worth using.

## Short version

The goal is not pure automation and not pure conversation.
The goal is a trustworthy oscillation between:

- natural language,
- explicit commands,
- and durable traces.
