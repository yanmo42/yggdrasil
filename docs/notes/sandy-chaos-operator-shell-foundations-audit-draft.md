# Sandy Chaos operator-shell foundations audit v0

Status: parked draft design artifact
Audience: Ian + Ygg
Scope: define the first high-value audit schema and command surface for using Ygg in service of Sandy Chaos research

Note: this is a parked exploratory draft, not an active Ygg contract or committed roadmap item. It lives under `docs/notes/` intentionally so it does not read like canonical repo guidance.

---

## 1. Why this exists

Ygg should help Sandy Chaos move **more rigorously**, not merely **more continuously**.

Right now, the likely bottleneck is not idea generation. It is legibility around:

- which frontiers are active,
- which claims depend on which foundations,
- which assumptions are load-bearing,
- which baselines/nulls are required,
- which evidence artifacts exist,
- and where proof debt remains.

So the first operator-shell move should not be topology visualization or richer UX.
It should be a **foundations/frontier audit surface**.

That surface should let Ian or Ygg ask questions like:

- What is the current frontier actually trying to establish?
- What mathematical / physical / modeling assumptions does it rest on?
- Which of those assumptions are explicitly documented versus merely implied?
- What benchmark harnesses exist already?
- What null models are required?
- What evidence is attached?
- What is the next highest-leverage move?

---

## 2. Boundary: Sandy Chaos vs Ygg

### Sandy Chaos owns
- canonical theory docs
- mathematical derivations
- physical postulates
- benchmark definitions
- theory-implementation matrix rows
- concept spine / pressure / promotion records
- advisor-facing research truth-claims

### Ygg owns
- continuity across sessions/lanes
- operational legibility
- frontier selection support
- audit/report surfaces
- evidence routing and gap surfacing
- next-step pressure / proof-debt visibility

### Operator-shell principle
Ygg does **not** decide what is true.
Ygg helps expose:
- what is assumed,
- what is evidenced,
- what is missing,
- and what should happen next.

---

## 3. Design goals

The first audit surface should be:

1. **Read-first**
   - no mutation required for useful first value
2. **Source-explicit**
   - every field should distinguish authoritative vs inferred values
3. **Claim-tier disciplined**
   - defensible now / plausible but unproven / speculative
4. **Failure-legible**
   - every major audit should surface missing nulls, missing evidence, and blocking gaps
5. **Composable**
   - the same schema should support both a single concept audit and a whole frontier audit
6. **Unix-legible**
   - text-first CLI output, JSON available for machine use

---

## 4. Core concept: audit target

An audit target is any Sandy Chaos surface whose foundation/evidence posture matters.

Initial target classes:

- **frontier** — an active research frontier or near-term lane
- **concept** — a spine concept or conceptual lane
- **matrix-row** — a theory-implementation matrix row
- **doc** — a canonical Sandy Chaos document
- **benchmark** — a validation task or benchmark family

Example target ids:

- `frontier:symbolic-maps-discriminating-benchmark`
- `concept:SC-CONCEPT-0006`
- `concept:SC-CONCEPT-0008`
- `matrix:T-014`
- `doc:docs/16_temporal_predictive_processing.md`
- `benchmark:null-vs-coupled-transport`

---

## 5. Audit schema v0

The audit schema should be usable both as:
- a human-readable report shape
- a machine-readable JSON payload

### 5.1 Top-level shape

```json
{
  "schemaVersion": 1,
  "generatedAt": "ISO-8601",
  "generator": "ygg frontier audit | ygg roots show",
  "target": {},
  "summary": {},
  "foundations": {},
  "evidence": {},
  "gaps": {},
  "dependencies": {},
  "promotion": {},
  "nextMove": {},
  "sources": []
}
```

---

### 5.2 `target`

Describes what is being audited.

```json
{
  "kind": "frontier|concept|matrix-row|doc|benchmark",
  "id": "string",
  "title": "string",
  "status": "active|partial|stalled|planned|speculative|implemented",
  "claimTier": "defensible-now|plausible-but-unproven|speculative",
  "ownerSurface": "sandy-chaos|ygg-bridge|mixed",
  "authoritativeSource": "path or object ref"
}
```

Notes:
- `ownerSurface` is important. It prevents Ygg from pretending to own SC canon.
- `claimTier` should come from authoritative sources when possible; inferred only when necessary.

---

### 5.3 `summary`

Compact readout for operator use.

```json
{
  "objective": "What this target is trying to establish or build",
  "whyNow": "Why this target matters currently",
  "loadBearing": true,
  "auditVerdict": "grounded|mixed|under-founded|blocked|unclear",
  "operatorReading": "Short plain-language readout"
}
```

Suggested meaning of `auditVerdict`:
- `grounded` — foundations/evidence are reasonably explicit for the current tier
- `mixed` — some support exists, but important pieces are partial or implicit
- `under-founded` — major dependencies or nulls are missing
- `blocked` — progress is materially blocked by missing base/supporting machinery
- `unclear` — the target itself is underspecified

---

### 5.4 `foundations`

This is the heart of the schema.

```json
{
  "mathematical": [
    {
      "name": "string",
      "status": "explicit|implicit|missing|contested",
      "role": "axiom|derived-structure|formalism-choice|dependency",
      "source": "path/ref",
      "notes": "string"
    }
  ],
  "physical": [
    {
      "name": "string",
      "status": "explicit|implicit|missing|contested",
      "role": "postulate|constraint|regime-assumption|dependency",
      "source": "path/ref",
      "notes": "string"
    }
  ],
  "modeling": [
    {
      "name": "string",
      "status": "explicit|implicit|missing|contested",
      "role": "sc-choice|operationalization|abstraction|heuristic",
      "source": "path/ref",
      "notes": "string"
    }
  ]
}
```

This split is important.
It prevents these from collapsing together:
- what math permits,
- what physics asserts,
- what Sandy Chaos chooses to model.

---

### 5.5 `evidence`

```json
{
  "docs": ["path"],
  "artifacts": ["path"],
  "tests": ["path or command"],
  "benchmarks": ["id or path"],
  "matrixRows": ["T-xxx"],
  "spineConcepts": ["SC-CONCEPT-xxxx"],
  "pressureEvents": ["SC-PRESSURE-..."],
  "quality": {
    "documentation": "strong|partial|weak|none",
    "implementation": "strong|partial|weak|none",
    "validation": "strong|partial|weak|none",
    "traceability": "strong|partial|weak|none"
  }
}
```

`quality` is an operator compression layer, not canonical truth.
It should be marked as inferred unless directly encoded somewhere.

---

### 5.6 `gaps`

```json
{
  "missingAssumptions": ["string"],
  "missingNullModels": ["string"],
  "missingBenchmarks": ["string"],
  "missingArtifacts": ["string"],
  "ambiguities": ["string"],
  "contradictionRisks": ["string"],
  "blockingGaps": ["string"]
}
```

This section should be blunt.
If the audit is useful, it must be able to say:
- what is not defined,
- what is not benchmarked,
- what is rhetorically present but operationally absent.

---

### 5.7 `dependencies`

```json
{
  "upstream": [
    {
      "kind": "doc|concept|matrix-row|benchmark|artifact",
      "id": "string",
      "role": "required|supporting|calibration|governance",
      "status": "healthy|partial|missing|stale"
    }
  ],
  "downstream": [
    {
      "kind": "doc|concept|matrix-row|benchmark|artifact",
      "id": "string",
      "role": "feeds|constrains|promotes-into|blocks",
      "status": "active|partial|planned|speculative"
    }
  ]
}
```

This is what lets Ygg expose proof debt instead of just file lists.

---

### 5.8 `promotion`

```json
{
  "readiness": "not-ready|evidence-needed|reviewable|promotion-candidate",
  "dispositionHint": "LOG_ONLY|TODO_PROMOTE|DOC_PROMOTE|POLICY_PROMOTE|ESCALATE|DROP_LOCAL",
  "why": "string"
}
```

This is advisory.
Ygg may suggest promotion posture, but SC canon still decides what gets promoted.

---

### 5.9 `nextMove`

```json
{
  "type": "define-foundation|write-null|build-benchmark|collect-evidence|resolve-ambiguity|promote|defer",
  "action": "string",
  "why": "string",
  "expectedGain": "string"
}
```

This section is critical for operator usefulness.
The audit should not merely diagnose.
It should produce the **highest-leverage next move**.

---

### 5.10 `sources`

```json
[
  {
    "path": "string",
    "kind": "doc|json|jsonl|test|artifact|inferred",
    "authority": "canonical|bridge|derived",
    "usedFor": ["target", "foundations", "evidence", "dependencies"]
  }
]
```

This keeps the audit honest.

---

## 6. Output rule: authoritative vs inferred

Every audit field should be treated as one of:

- **authoritative** — stated directly in canonical SC or Ygg source
- **derived** — deterministically extracted from canonical source
- **inferred** — operator interpretation by Ygg

This distinction should be visible in JSON and, when relevant, in text output.

If this distinction is not preserved, the audit surface will drift into overclaiming.

---

## 7. First command-family proposal

The first command family should be small.
Not a sprawling CLI tree.

## 7.1 `ygg roots`

Purpose: expose foundational support beneath an SC target.

Why `roots`:
- mythically coherent
- operationally legible
- directly about foundational support

### Proposed subcommands

#### `ygg roots show <target>`
Return the full foundations audit for one target.

Examples:
```bash
ygg roots show frontier:symbolic-maps-discriminating-benchmark
ygg roots show concept:SC-CONCEPT-0006
ygg roots show matrix:T-014
ygg roots show doc:docs/16_temporal_predictive_processing.md
```

#### `ygg roots gaps [<target>]`
Return only the most important missing assumptions / nulls / benchmarks.

Examples:
```bash
ygg roots gaps
ygg roots gaps frontier:symbolic-maps-discriminating-benchmark
```

#### `ygg roots deps <target>`
Return upstream/downstream dependency readout.

#### `ygg roots nulls <target>`
Return required null models and baseline comparisons.

---

## 7.2 `ygg frontier`

Purpose: expose the active research frontier and audit it.

### Proposed subcommands

#### `ygg frontier current`
Show the currently active SC-relevant frontier.

#### `ygg frontier list`
Show ranked/open frontiers.

#### `ygg frontier audit [<target>]`
If no target is provided, audit the current frontier using the schema above.

This is probably the single most useful first operator-shell command.

Example:
```bash
ygg frontier audit
```

Desired output sections:
- target summary
- claim tier
- audit verdict
- foundations split
- evidence quality
- blocking gaps
- next best move

---

## 7.3 `ygg evidence`

Purpose: show supporting artifacts and missing evidence.

### Proposed subcommands

#### `ygg evidence show <target>`
Show current supporting docs/tests/artifacts.

#### `ygg evidence missing [<target>]`
Show missing artifacts/benchmarks/traceability links.

This should likely be implemented after `roots` and `frontier audit`, since those already include evidence sections.

---

## 8. Recommended implementation order

### Step 1 — schema + static mapping
Define the audit schema and a small target-resolution layer.

Inputs may initially come from:
- explicit small mapping file(s)
- known SC docs
- theory-implementation matrix refs
- spine concept refs
- a manually curated frontier index

This is acceptable for v0.
Do not wait for perfect automation.

### Step 2 — `ygg frontier audit`
Implement one strong audit command using the schema.

Why first:
- aligns with active work selection
- highest immediate value
- gives Ygg a concrete operator-shell identity

### Step 3 — `ygg roots show`
Make the underlying foundations-focused command explicit.

### Step 4 — `ygg roots gaps`
Add compressed proof-debt surfacing.

### Step 5 — only then broaden
Consider evidence/topology views after the audit surface proves useful.

---

## 9. Suggested initial target set

The first audit targets should stay small and high-value.

Recommended initial set:

1. the current active Sandy Chaos frontier from `plans/today_frontier_*.md`
2. `SC-CONCEPT-0006` symbolic maps / narrative invariants
3. `SC-CONCEPT-0008` proof-path frontier governance
4. `docs/16_temporal_predictive_processing.md`
5. `docs/11_geodesic_hydrology_contracts.md`
6. `T-014`
7. `T-015`

This is enough to validate the shell without pretending to cover the whole repo.

---

## 10. Claim-tier read on this proposal

### Defensible now
- Ygg can add real value to Sandy Chaos by exposing proof debt, dependency structure, and frontier readiness.
- A read-first foundations/frontier audit surface is a better first move than topology UI or voice features.
- The math / physics / modeling split is necessary if the shell is to help with rigor rather than blur it.

### Plausible but unproven
- A compact `roots` / `frontier audit` command family could become the main operator shell for SC-facing work.
- The audit schema may become a useful bridge between SC canon and Ygg continuity.

### Speculative
- This audit surface could eventually become the basis for richer topology, pressure mapping, or semi-automated promotion support across SC.

---

## 11. Failure conditions

This design should be considered to have failed if:

1. Ygg begins asserting canonical SC truth instead of citing/deriving from SC sources.
2. The audit outputs feel impressive but are not source-traceable.
3. The schema collapses math, physics, and modeling into one undifferentiated assumption list.
4. The command surface becomes larger than its actual evidence quality supports.
5. The system cannot produce a concrete next move from an audit.

---

## 12. Immediate next action

Build the first implementation target around:

```bash
ygg frontier audit
```

with a small manually curated target-resolution layer and the audit schema above.

That should be the first command that proves Ygg can help Sandy Chaos become more rigorous, not just more organized.
