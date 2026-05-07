# Aura Architecture — Figma Re-Style Instructions

Companion to `aura_architecture.mmd`. Mermaid is the structural source of truth; Figma is the styled artefact. Mermaid's default treatment (rounded corners, curved arrows, default fonts, default greys) violates every deck_spec.md §0 lock and is rejected on sight.

These are the steps a designer (or Shaurya) runs once, after exporting SVG from https://mermaid.live, to bring the diagram into the deck's locked visual system.

---

## 0. Locks recap

| Lock | Value |
|---|---|
| Background | #FAF8F5 warm off-white |
| Ink | #0E0E0E ink black |
| Accent | #FF5B2E sunset orange — load-bearing only |
| Display serif | Fraunces |
| Body sans | Inter Tight |
| Mono | JetBrains Mono |
| Canvas | 1700 × 720 px (slide 4 hero region cols 1–9) |
| Banned | gradients, glows, drop shadows, glassmorphism, neon, blue tech-gradient, light-bulb metaphors, robot icons, isometric phones, neuron motifs |

---

## 1. Import

1. Open `aura_architecture.mmd` at https://mermaid.live.
2. Render. Click **Actions → SVG**. Save as `s4_architecture_raw.svg`.
3. Open the raw SVG in Figma. Detach all groups once so every node, edge, and label is independently selectable.

---

## 2. Frame and grid

1. Create a Figma frame named `s4_architecture` at exactly **1700 × 720 px**.
2. Background fill: `#FAF8F5` solid. No grain texture in the frame itself — grain lives at deck composition level.
3. Add three vertical lanes with **equal 540 px width** each, separated by **1 px `#0E0E0E` hairlines** that span full frame height. Lane order, left to right: SENSE, INTELLIGENCE, EXPERIENCE.
4. Lane kicker labels at the top of each lane in **Inter Tight 14 pt tracked +40**, set in `#FF5B2E` sunset orange — the only place on the diagram where a label is orange. Labels read exactly: `SENSE`, `INTELLIGENCE`, `EXPERIENCE`. 24 px from frame top.

---

## 3. Node treatment — square corners, stroke only

Mermaid ships rounded fills. Replace all of them with the locked treatment.

**Sense layer nodes** (S1–S7):
- Shape: rectangle, **corner radius 4 px max** (square corners — 0 px preferred). No curves.
- Fill: none (transparent).
- Stroke: 1 px `#0E0E0E`.
- Size: 220 × 56 px each.
- Internal label: **JetBrains Mono 14 pt** in `#0E0E0E`, centred. The API names are code identifiers, so they live in mono.
- Stack vertically with 16 px gap between nodes. 24 px lane padding.

**Intelligence layer nodes**:
- Four agent nodes (`COMMS`, `CAL`, `FIN`, `WELL`): rectangles, square corners, 1 px `#0E0E0E` stroke, no fill, 240 × 96 px each. Position at the four corners of the lane. Inside each node:
  - Tier title (agent name) in **Fraunces 18 pt regular** `#0E0E0E` — top line.
  - Component name (model + LoRA) in **Inter Tight 14 pt** at 60% ink — second line.
  - Where applicable, a JetBrains Mono 12 pt API tag — third line.
- Orchestrator node (`ORCH`): rectangle, square corners, **320 × 120 px**, dead-centre vertically in the lane. Fill: none. Stroke: 1 px `#0E0E0E` on three sides; **left edge replaced with a 4 px `#FF5B2E` sunset-orange stroke** that runs full node height. This is the single most important style cue in the diagram.
  - Title "Orchestrator" in **Fraunces 22 pt regular** — top line.
  - Component name "Phi-3-mini · LangGraph" in **Inter Tight 14 pt** at 60% ink — second line.
  - State list "Idle · Listening · Deliberating · AwaitingConfirm · Executing · LoggingTrace · Cooldown" in **JetBrains Mono 11 pt** at 60% ink, wrapped onto two lines — bottom block.
- Memory node (`MEM`): rectangle, square corners, 240 × 72 px, centred at lane bottom. 1 px `#0E0E0E` stroke. Title "Memory Graph" in Fraunces 18 pt. Component "sqlite-vss · Keystore · Merkle audit" in Inter Tight 14 pt at 60% ink.
- Reasoning Trace node (`TRACE`): a **slim parallelogram-replaced-by-rectangle** at 240 × 56 px adjacent to the orchestrator on its right side, square corners, 1 px `#0E0E0E` stroke. Title "Reasoning Trace" in Fraunces 16 pt. Subtitle "typed JSON · local-only" in JetBrains Mono 12 pt at 60% ink.

**Experience layer nodes**:
- Four surface nodes stacked vertically: phone, watch, earbuds, tablet.
- Same rectangle, square corners, 1 px `#0E0E0E` stroke treatment. 240 × 80 px each.
- Surface name in Fraunces 18 pt regular — top line.
- Surface affordances ("Brief · Action · Trace · Memory" etc.) in Inter Tight 14 pt at 60% ink — second line.

Universal node rule: **at least 24 px clear space around every node**. The diagram should still read at 1280 × 720 fallback.

---

## 4. Arrow treatment — orthogonal only, never curved

Mermaid renders curved bezier arrows by default. **Delete all curved paths.**

Replace with:
- **Stroke**: 1.5 px `#0E0E0E`.
- **Geometry**: orthogonal segments only — right-angle bends, never curved beziers, never diagonal except where the diagram strictly requires it (none, in this graph).
- **Heads**: simple triangular arrow head, 6 px wide, ink-black fill, no stroke. No diamond heads, no open arrowheads.
- **Anchor points**: arrows attach to node edge midpoints, never to corners. Use Figma's snap-to-edge.

**Arrow labels**:
- Font: **JetBrains Mono 12 pt italic**. (API names live in mono. Italic distinguishes the label from a node title at a glance.)
- Colour: `#0E0E0E`.
- Placement: on the horizontal segment of the arrow, with a 4 px solid `#FAF8F5` halo behind the text for legibility against any underlying hairline.
- Sense → agent arrows are **unlabelled** (signal flow assumed; labels would clutter).
- Agent → orchestrator arrows are labelled with the typed-JSON tool name verbatim from `aura_architecture.mmd` — `classify() / draft_reply()`, `detect_conflicts() / suggest_slots()`, `parse_sms() / anomaly_flag()`, `compute_load_score() / intervention_select()`.
- Orchestrator → surface arrows are labelled with the action type — `brief`, `action_card + confirm`, `trace_drawer (glass box)`, `watch_haptic`, `tts_whisper`, `pull_tab`.
- Orchestrator ↔ Memory: bidirectional, two parallel orthogonal paths 8 px apart, each with its own arrowhead.

---

## 5. The single sunset-orange element (besides the orchestrator edge)

The orchestrator → Phone → "trace_drawer (glass box)" arrow is rendered in **`#FF5B2E` sunset orange, 1.5 px stroke**, with a **`#FF5B2E` triangular arrowhead**. The label on this arrow reads `trace_drawer (glass box)` set in **JetBrains Mono 12 pt italic** in `#FF5B2E`.

That arrow plus the orchestrator's left-edge accent are the only two orange elements in the entire architecture diagram. Lane kickers are also orange (per §2) but at 14 pt tracked sans they read as identity, not as a load-bearing element. If the deck needs a tighter accent budget, drop the kicker orange and keep only the orchestrator edge + the one trace arrow — that is the §0 single-accent rule's strictest reading.

---

## 6. Type system — strict three-tier hierarchy

| Element | Font | Size | Weight | Colour |
|---|---|---|---|---|
| Lane kicker | Inter Tight | 14 pt tracked +40 | Regular | `#FF5B2E` |
| Tier title (agent / orchestrator / memory / surface name) | Fraunces | 16–22 pt | Regular | `#0E0E0E` |
| Component name (model, runtime, store) | Inter Tight | 14 pt | Regular | `#0E0E0E` at 60% opacity |
| API name / state list / tool call / arrow label | JetBrains Mono | 11–14 pt | Regular (italic on arrow labels) | `#0E0E0E` |
| The single orange arrow label | JetBrains Mono | 12 pt | Italic | `#FF5B2E` |

The three tiers are deliberate: **Fraunces says "this is a thing"; Inter Tight says "this is what it is"; JetBrains Mono says "this is its API"**. The reader's eye is trained by the deck's other slides on the same hierarchy.

---

## 7. Layer dividers and frame edges

- Inter-lane vertical hairlines: 1 px `#0E0E0E` at 100% opacity, full frame height.
- No frame border around the diagram. No drop shadow. No background fill change between lanes.
- 80 px outer margin from frame edge to nearest node, on all four sides.

---

## 8. Export

1. Select the `s4_architecture` frame.
2. Export as **SVG** at 1× — file `s4_architecture.svg`. Save to `aura/design/architecture/`.
3. Also export a 2× **PNG** for the deck — file `s4_architecture@2x.png`, 3400 × 1440 px, transparent background. Save to `aura/design/architecture/`.
4. Drop both into `deck/phase1_blueprint/source_assets/` for slide 4.

---

## 9. Anti-cliché checklist before commit

Run these six against the styled diagram. Any "no" blocks the commit.

- [ ] Zero gradients, zero glows, zero drop shadows.
- [ ] Zero curved arrows. All arrows orthogonal.
- [ ] Zero rounded-corner nodes (max 4 px, ideally 0 px).
- [ ] Sunset orange appears in **at most three** elements: orchestrator left edge, the trace arrow + its label, and lane kickers. If the kickers feel decorative, demote them to ink black and drop to two orange elements.
- [ ] No light-bulb, robot, brain, neuron, or device-frame illustration anywhere in the diagram.
- [ ] All API and tool labels are in JetBrains Mono. All component names are in Inter Tight. All tier titles are in Fraunces. No off-system fonts.

If all six pass, commit. Otherwise, revise and re-check.
