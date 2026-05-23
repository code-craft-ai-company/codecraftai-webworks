# Workflow Diagram Spec

- **Tag:** `<mj-workflow-diagram>`
- **Class / file:** `WorkflowDiagram` / `workflowdiagram.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Workflow diagram, State diagram, Swimlane diagram,
  Process flow diagram
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-workflow-diagram>` renders a state-machine or cross-actor process flow as
a directed graph. In swimlane mode, nodes are grouped into horizontal or vertical
rows representing actors (people, teams, systems); edges represent transitions or
handoffs. The current-state highlight marks the live position in the workflow.
It reuses the §5.9 Diagram/Graph viewer rendering adapter.

## 2. When to use / when not to use

**Use** to document approval flows, JIRA workflow configurations, CI/CD process
steps divided by actor, or software state machines. **Do not use** for pipeline
execution status (use `<mj-pipeline-chart>`) or for dependency blocking graphs
(use `<mj-dependency-graph>`). Nearest alternative: `<mj-pipeline-chart>` for
linear CI flows.

## 3. Anatomy

- **Canvas / viewport** — pannable/zoomable area.
- **Swimlane rows** (optional) — horizontal or vertical bands, one per actor;
  labeled on the edge.
- **State nodes** — rounded boxes for states/steps; shapes vary by type
  (start: filled circle, end: double circle, decision: diamond, state: rectangle).
- **Transition edges** — directed arrows labeled with trigger conditions or
  guard expressions.
- **Current-state highlight** — the active state node has a pulsing ring or
  bold border; `aria-current="step"` on the node element.
- **Detail panel** — shows state/transition metadata on selection.
- **Accessible adjacency list** — `<dl>` of states with their outgoing
  transitions.
- **Legend** — node shape and color guide.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| State machine | `diagram-type="state"` (default) | No swimlanes; nodes are states |
| Swimlane | `diagram-type="swimlane"` | Nodes grouped into actor swim-lanes |
| Horizontal swimlanes | `swimlane-direction="horizontal"` (default) | Actors stacked top to bottom |
| Vertical swimlanes | `swimlane-direction="vertical"` | Actors arranged left to right |
| Read-only | `readonly` (boolean, default) | No editing; current-state can be set |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"jira"`, `"github"` |
| `diagram-type` | `"state"` \| `"swimlane"` | `"state"` | yes | Structural layout |
| `swimlane-direction` | `"horizontal"` \| `"vertical"` | `"horizontal"` | yes | Swimlane orientation |
| `current-state` | string | `""` | yes | ID of the currently active state node |
| `readonly` | boolean | `false` | yes | Disables editing actions |
| `layout` | `"dagre"` \| `"elk"` | `"dagre"` | yes | Layout algorithm |
| `show-labels` | boolean | `true` | yes | Show transition edge labels |
| `locale` | string | `""` | yes | BCP 47 locale for any numeric labels |
| `label-loading` | string | `"Loading diagram…"` | yes | Loading message |
| `label-empty` | string | `"No workflow data."` | yes | Empty message |
| `label-error` | string | `"Failed to load diagram."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `WorkflowData` | `{ states: StateNode[], transitions: Transition[], actors: Actor[] }` |
| `selectedNode` | `StateNode \| null` | Currently selected state node |
| `selectedTransition` | `Transition \| null` | Currently selected transition edge |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<dl>` rendered before upgrade |
| `node-detail` | Custom detail panel for selected state node |
| `transition-detail` | Custom detail panel for selected transition |
| `empty` | Shown when no workflow data |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-node-select` | `{ node: StateNode }` | yes | no | State node activated |
| `mj-node-deselect` | `{}` | yes | no | Selection cleared |
| `mj-transition-select` | `{ transition: Transition }` | yes | no | Transition edge activated |
| `mj-state-change` | `{ from: string, to: string }` | yes | no | `current-state` attribute changed |
| `mj-zoom-change` | `{ zoom: number }` | yes | no | Zoom changed |
| `mj-data-load` | `{ states: number, transitions: number, actors: number }` | yes | no | Data loaded |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(canvas)` — pannable/zoomable area
- `::part(swimlane)` — individual actor swimlane band
- `::part(swimlane-label)` — actor label on a swimlane
- `::part(state-node)` — state/step box
- `::part(state-node-current)` — current-state node accent
- `::part(start-node)` — start circle node
- `::part(end-node)` — end double-circle node
- `::part(decision-node)` — diamond decision node
- `::part(transition-edge)` — directed arrow
- `::part(transition-label)` — label on a transition arrow
- `::part(detail-panel)` — selected node/transition detail overlay
- `::part(legend)` — legend container

**Custom properties:**
- `--mj-node-bg` — default state node background
- `--mj-node-border` — default state node border color
- `--mj-node-radius` — state node corner radius (default `6px`)
- `--mj-current-state-color` — current-state highlight ring color
- `--mj-current-state-pulse` — pulse animation duration (default `1.5s`)
- `--mj-transition-color` — edge arrow stroke color
- `--mj-swimlane-bg` — alternating swimlane background
- `--mj-swimlane-label-width` — width of the actor label column (default `120px`)

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown.
- **node-selected** — node highlighted; detail panel open.
- **transition-selected** — edge highlighted; transition detail panel open.
- **current-state** — the `current-state` node has a pulsing ring; `aria-current="step"`.
- **reduced-motion** — pulse animation disabled; current-state shown by bold border only.

## 11. Behavior & interactions

On load the adapter returns `WorkflowData`. The rendering adapter lays out nodes
using the `layout` algorithm, respecting swimlane boundaries when
`diagram-type="swimlane"`. Start and end node shapes are rendered by the adapter
based on `StateNode.type` values (`"start"`, `"end"`, `"decision"`, `"state"`).
Setting the `current-state` attribute highlights the corresponding node and fires
`mj-state-change` if the value differs from the previous. Transition edge labels
are positioned mid-arc by the rendering adapter. Selecting a transition (click or
Enter/Space when edge-button focused) fires `mj-transition-select` and opens the
transition detail panel.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between state nodes, then transition edges (as buttons), then toolbar |
| `Arrow Up` / `Arrow Down` / `Arrow Left` / `Arrow Right` | Pan the canvas |
| `Enter` / `Space` | Select focused node or transition edge |
| `Escape` | Deselect; close detail panel |
| `+` / `-` | Zoom in / zoom out |
| `0` | Reset zoom to fit |
| `C` | Jump focus to the `current-state` node |
| `Home` / `End` | Focus start / end node |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Workflow diagram: {n} states,
  {m} transitions{, {k} actors}".
- State nodes: `role="button"` with `aria-label` = "{name}, type: {type},
  {current state|not current}"; `aria-current="step"` when active.
- Transition edges: `role="button"` with `aria-label` = "Transition from {from}
  to {to}{: {label}}".
- Swimlane bands: `role="group"` with `aria-label` = "Actor: {actor name}".
- Start node: `aria-label` = "Start state".
- End node: `aria-label` = "End state".
- Decision node: `aria-label` = "{name}, decision node".
- Accessible adjacency list: `<dl>` with each state as `<dt>` and its outgoing
  transitions as `<dd>` entries.
- Current state change announced via live-region: "Current state: {name}".

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Transition labels are rendered verbatim.
- All UI strings overridable: `label-loading`, `label-empty`, `label-error`,
  `label-zoom-in`, `label-zoom-out`, `label-reset-zoom`, `label-show-list`,
  `label-current-state`.
- RTL: canvas layout re-applied with RTL hint; swimlane labels mirror to the
  right; edge arrows reverse; actor-label column moves to the right.

## 16. Progressive enhancement / SSR

Server renders a `<dl>` of states and transitions inside the default slot. On
upgrade the component hides the list visually (toggle re-accessible) and draws
the diagram without layout shift.

## 17. Dependencies

- §6 data-source adapter interface (adapter keys: `static`, `jira`, `github`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 overlay/positioning engine (detail panels)
- §6 live-region/announcement service (current-state changes)
- §6 localization/formatting hook
- §5.9 Diagram/Graph viewer pluggable rendering adapter (layout: dagre/elk)

## 18. Edge cases & error handling

- **No transitions** — isolated nodes rendered; no edges.
- **Multiple start nodes** — all rendered with start-node styling; no error.
- **Cycles in transitions** — allowed in state machines; no cycle warning
  (unlike dependency graphs, cycles are expected here).
- **`current-state` ID not found in nodes** — attribute silently ignored;
  console warning logged.
- **Adapter failure** — error slot shown; stale data retained.
- **Long transition labels** — truncated to 40 chars on edge; full label in
  detail panel.
- **Very large diagrams (>100 nodes)** — minimap recommended; warning emitted
  if `show-minimap` is false.

## 19. Acceptance criteria

- [ ] State nodes render with correct shapes by `StateNode.type`.
- [ ] Transition edges render with labels when `show-labels` is true.
- [ ] Swimlane bands group nodes by actor when `diagram-type="swimlane"`.
- [ ] `current-state` attribute highlights the correct node with pulsing ring.
- [ ] Setting `current-state` fires `mj-state-change` with from/to IDs.
- [ ] Selecting a node fires `mj-node-select` and opens detail panel.
- [ ] Selecting a transition fires `mj-transition-select`.
- [ ] Keyboard navigation per §12 covers nodes, transitions, and canvas pan.
- [ ] `aria-current="step"` appears on the current-state node.
- [ ] Accessible adjacency list present in DOM.
- [ ] `prefers-reduced-motion` disables pulse animation.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should transition edges themselves be focusable as interactive elements, or
  is the adjacency list sufficient for keyboard users to understand transitions?
- Is a "trace mode" (animate a token moving through states like a Petri net
  simulation) in scope for P3?
- Should `diagram-type="swimlane"` support nested actors (sub-swimlanes)?
