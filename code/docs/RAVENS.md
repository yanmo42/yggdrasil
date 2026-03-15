# Ravens

Purpose: define a flexible signal-and-return subsystem inside Yggdrasil.

This is intentionally a little loose for now.
It should feel more like a living metaphor with operational value than a fully frozen taxonomy.
Like wings in the wind.

---

## Core image

Odin's ravens fly out into the world, gather signal, and return it back.

That maps unusually well onto what Yggdrasil needs:
- something leaves the spine,
- encounters the world,
- gathers signal,
- interprets what matters,
- and returns meaningful consequence back to the center.

The ravens are not the tree.
They are not the root.
They are not canonical memory.
They are the roaming layer.

---

## Role in Yggdrasil

### Yggdrasil
The tree remains the larger architecture:
- root,
- spine,
- branches,
- promotion,
- continuity,
- durable memory.

### The Ravens
The ravens are a subsystem of motion and return.

They are for:
- scouting,
- noticing,
- reminding,
- summarizing,
- probing,
- reporting,
- and carrying signal between the world and the spine.

If Yggdrasil is the structured organism, the ravens are its roaming cognition.

---

## Initial split

The classic pairing is too useful to ignore.

### Huginn
Usually glossed as **thought** / **mind**.

Operationally, Huginn can represent:
- active interpretation,
- scouting,
- search,
- pattern noticing,
- planning pressure,
- next-move suggestion,
- curiosity directed outward.

Huginn is the raven that goes looking.

### Muninn
Usually glossed as **memory** / **remembering**.

Operationally, Muninn can represent:
- recall,
- compaction,
- summary,
- cue-setting,
- promotion,
- continuity recovery,
- carrying things back in a form the spine can keep.

Muninn is the raven that makes return meaningful.

---

## Important caution

This split should remain helpful, not dogmatic.

In practice:
- one subsystem may do both jobs,
- one pass may contain both Huginn and Muninn behavior,
- and future implementations may blur them intentionally.

The names are meant to sharpen intuition, not trap design.

---

## Raven flight (v0 lifecycle)

A useful first model:

1. **Launch**
   - a question, need, trigger, schedule, or curiosity sends a raven outward

2. **Encounter**
   - it touches some surface:
     - Discord
     - web search
     - transcripts
     - files
     - voice input
     - external sensors or tools later

3. **Gather**
   - raw signal is collected
   - most of it is noisy or low-value

4. **Interpret**
   - signal is filtered into:
     - actionable next move
     - summary
     - warning
     - reminder
     - memory candidate
     - or explicit no-promote

5. **Return**
   - the raven comes back to the spine
   - result is routed into:
     - human prompt
     - machine trace
     - cycle update
     - daily note
     - durable memory
     - or discard

6. **Disposition**
   - nothing meaningful remains unclassified

That last step matters.
A raven that never returns, or returns without consequence, is just noise.

---

## Where the ravens fit today

### Defensible now
The ravens map cleanly onto:
- Discord cadence pings
- cron-based reminders
- web search and retrieval
- session/transcript recall
- summary + promotion loops

### Plausible next
They could also cover:
- voice command intake
- push-to-talk prompting
- spoken summaries / TTS returns
- ambient monitoring of project state
- lightweight multi-surface nudges

### Speculative later
They might eventually become:
- persistent roaming agents
- multimodal scouts
- AR/VR or spatialized signal carriers
- a more explicit cognition layer over the tree

---

## Discord interpretation

Discord is a strong early raven surface because it is:
- socially natural,
- low-friction,
- asynchronous,
- legible to both human and machine.

In that framing:
- `claw-20-cycle` is a natural raven perch
- cadence pings are raven returns
- acknowledgements (`done`, `blocked`, `snooze 2h`) are signals sent back to the spine

This makes Discord less like “the whole app” and more like one useful branch surface for raven traffic.

---

## Relationship to Sandy Chaos

For now, I would **not** force a rename.

Sandy Chaos still feels larger and deeper than a raven subsystem.
It points more toward:
- research engine,
- conceptual space,
- theory pressure,
- and the broader questions of lawful growth under constraint.

The ravens feel more like:
- movement,
- signal,
- contact,
- and return.

So the most stable structure right now is:
- **Yggdrasil** = architecture / tree / spine
- **Ravens** = roaming signal-and-return subsystem
- **Sandy Chaos** = deeper research/conceptual engine

That may change later.
But it is a good boundary for now.

---

## Invariants

1. The ravens are not a second canonical root.
2. Meaningful signal must return to the spine somehow.
3. Raven flights should improve reality contact, not hallucinated motion.
4. More scouting is not automatically better.
5. A raven system that generates chatter without consequence is failing.
6. Memory, summary, and next-move suggestion should remain distinct enough to inspect.

---

## Failure conditions

This subsystem is failing if:
- raven language becomes purely decorative,
- scouting generates noise without improving decisions,
- Discord/message traffic grows without improving throughput,
- the ravens become a vague aesthetic excuse for overcomplication,
- or they begin replacing the spine instead of serving it.

It is also failing if:
- every signal is treated as equally important,
- or nothing gets returned in compact, durable form.

---

## Good design question

Before building a new raven behavior, ask:

**What is leaving the spine, what signal is it gathering, and how does that signal return with consequence?**

If that is unclear, the raven probably has not been defined well enough yet.

---

## Naming direction (loose)

Some promising possibilities:

- **Ravens** — umbrella subsystem
- **Huginn** — outward thought/scout pass
- **Muninn** — memory/return/promote pass

Optional later possibilities:
- **Ratatoskr** — relay / message-bus / trunk-runner role
- **Odin's birds** or a custom mythos variant if strict Norse framing becomes too constraining

No need to overcommit yet.
The important thing is that the naming clarifies function.

---

## Short version

The ravens are a subsystem of Yggdrasil.
They leave the spine, gather signal, and return it in useful form.

- Huginn leans toward thought, search, interpretation, outward motion.
- Muninn leans toward memory, summary, compaction, and meaningful return.

The tree remains the architecture.
The ravens help it stay in touch with the world.
