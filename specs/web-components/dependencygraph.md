# Dependency Graph Spec

- **Tag:** `<mj-dependency-graph>`
- **Class / file:** `DependencyGraph` / `dependencygraph.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Dependency graph, Critical path chart, PERT chart,
  Module dependency graph
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-dependency-graph>` renders a directed node/edge graph of work items,
modules, or services and their dependencies. It highlights the critical path
(the longest chain of dependent tasks), detects cycles, and makes individual
nodes selectable with full accessible detail. It reuses the §5.9 Diagram/Graph
viewer pluggable rendering adapter rather than implementing its own layout engine.

## 2. When to use / when not to use

**Use** to visualize blocking dependencies between work items, package dependency
trees, or PERT-style effort estimates. **Do not use** for pipeline stage flows
(use `<mj-pipeline-chart>`) or for branching history (use `<mj-branch-graph>`).
Nearest alternative: `<mj-workflow-diagram>` for state-machine flows.

## 3. Anatomy

- **Canvas / viewport** — pannable and zoomable area managed by the rendering
  adapter.
- **Nodes** — boxes or circles representing work items or modules; carry label,
  status, and optional estimate.
- **Edges** — directed arrows representing "depends on" relationships.
- **Critical-path highlight** — nodes and edges on the longest path rendered
  with a distinct stroke and fill pattern.
- **Cycle-detection indicator** — nodes involved in a cycle carry a warning badge.
- **Detail panel** — appears on node selection; shows full metadata.
- **Minimap** — optional thumbnail overview with viewport rectangle (large graphs).
- **Accessible adjacency list** — visually hidden `<dl>` of node names with
  their dependencies listed.
- **Legend** — maps node status colors/patterns and edge types to labels.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Work items | `graph-type="work"` (default) | Nodes are tasks/epics; edges are blocking dependencies |
| Module/package | `graph-type="module"` | Nodes are packages; edges are import/runtime dependencies |
| PERT | `graph-type="pert"` | Nodes show EST/LST/EFT/LFT; critical path uses float=0 calculation |
| Read-only | `readonly` (boolean, default) | No node interaction beyond selection |
| Minimap | `show-minimap` (boolean) | Renders a minimap thumbnail overlay |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"jira"`, `"linear"`, `"npm"`, `"github"` |
| `graph-type` | `"work"` \| `"module"` \| `"pert"` | `"work"` | yes | Node/edge semantic model |
| `show-critical-path` | boolean | `true` | yes | Highlight the critical path |
| `show-minimap` | boolean | `false` | yes | Render minimap overlay |
| `readonly` | boolean | `false` | yes | Disables editing actions |
| `layout` | `"dagre"` \| `"elk"` \| `"force"` | `"dagre"` | yes | Layout algorithm hint passed to the rendering adapter |
| `locale` | string | `""` | yes | BCP 47 locale for numeric estimates |
| `label-loading` | string | `"Loading graph…"` | yes | Loading message |
| `label-empty` | string | `"No dependencies."` | yes | Empty message |
| `label-error` | string | `"Failed to load graph."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `DependencyGraphData` | `{ nodes: Node[], edges: Edge[], criticalPath: string[] }` |
| `selectedNode` | `Node \| null` | Currently selected node |
| `cycles` | `string[][]` | Detected cycles; each is an array of node IDs forming the cycle |
| `zoom` | `number` | Current zoom level (1 = 100%) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<dl>` of nodes and dependencies rendered before upgrade |
| `node-detail` | Custom detail panel template for a selected node |
| `empty` | Shown when `data.nodes` is empty |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-node-select` | `{ node: Node }` | yes | no | Node activated |
| `mj-node-deselect` | `{}` | yes | no | Selection cleared |
| `mj-cycle-detected` | `{ cycles: string[][] }` | yes | no | Fired after data load when cycles are present |
| `mj-zoom-change` | `{ zoom: number }` | yes | no | Zoom level changed |
| `mj-data-load` | `{ nodes: number, edges: number, hasCycles: boolean }` | yes | no | Data loaded |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(canvas)` — pannable/zoomable graph container
- `::part(node)` — individual node element
- `::part(node-label)` — text label inside a node
- `::part(edge)` — directed arrow between nodes
- `::part(critical-path-node)` — node on the critical path
- `::part(critical-path-edge)` — edge on the critical path
- `::part(cycle-badge)` — warning badge on a node in a cycle
- `::part(detail-panel)` — node detail overlay
- `::part(minimap)` — minimap thumbnail container
- `::part(legend)` — legend

**Custom properties:**
- `--mj-node-width` — default node width (default `160px`)
- `--mj-node-height` — default node height (default `48px`)
- `--mj-node-radius` — node corner radius (default `4px`)
- `--mj-critical-path-color` — critical-path stroke/fill accent
- `--mj-cycle-badge-color` — cycle warning badge color
- `--mj-edge-color` — default edge arrow stroke color
- `--mj-edge-critical-color` — critical path edge stroke color
- `--mj-minimap-size` — minimap thumbnail dimension (default `160px`)

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown.
- **node-selected** — node highlighted; detail panel open.
- **critical-path-highlighted** — nodes and edges on the critical path carry
  the accent color and a `data-critical="true"` attribute.
- **cycle-detected** — affected nodes carry cycle-badge and `data-cycle="true"`;
  `mj-cycle-detected` fired; warning banner shown above the graph.
- **zoomed-out** — minimap visible and useful; zoom-reset control active.

## 11. Behavior & interactions

On load the adapter returns `DependencyGraphData`. The component passes nodes and
edges to the rendering adapter which applies the requested layout algorithm. The
critical path is computed from the `criticalPath` array in data (pre-computed by
the adapter) or, when `graph-type="pert"`, calculated client-side using float=0.
Cycle detection runs client-side via DFS on every data load; cycles are stored in
`this.cycles` and announced via `mj-cycle-detected`. Pan is pointer-drag or
Arrow keys; zoom is scroll wheel, pinch, or ± buttons. Clicking or pressing
Enter/Space on a node fires `mj-node-select` and opens the detail panel.
Edges are SVG paths and are not themselves focusable (relationship conveyed via
the adjacency list).

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between nodes in topological order; toolbar controls; minimap |
| `Arrow Up` / `Arrow Down` / `Arrow Left` / `Arrow Right` | Pan the viewport |
| `Enter` / `Space` | Select focused node; open detail panel |
| `Escape` | Deselect node; close detail panel |
| `+` / `-` | Zoom in / zoom out |
| `0` | Reset zoom to fit all nodes |
| `Home` | Focus the first node (start of topological order) |
| `End` | Focus the last node |
| `F` | Focus the first critical-path node |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Dependency graph: {n} nodes, {m}
  edges{, critical path: {k} nodes}".
- Nodes: `role="button"` with `aria-label` = "{name}, status: {status},
  {estimate if pert}, {on critical path|in cycle if applicable}".
- Edges: `aria-hidden="true"` (relationships conveyed by adjacency list).
- Cycle warning banner: `role="alert"` with text listing cycle node names.
- Critical-path nodes: supplemented by both color accent and a thicker stroke
  pattern; `data-critical="true"` for CSS targeting.
- Accessible adjacency list: `<dl>` with `<dt>` = node name, `<dd>` = "depends
  on: {comma-separated prerequisites}".
- Detail panel: `role="dialog"` `aria-modal="false"` with `aria-labelledby`
  pointing to the node name heading.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Numeric estimates in PERT mode use `Intl.NumberFormat` with `locale`.
- All UI strings overridable: `label-loading`, `label-empty`, `label-error`,
  `label-critical-path`, `label-cycle-warning`, `label-zoom-in`,
  `label-zoom-out`, `label-reset-zoom`, `label-show-list`.
- RTL: edge arrows reverse direction; layout re-applied with RTL hint to the
  rendering adapter.

## 16. Progressive enhancement / SSR

Server renders a `<dl>` inside the default slot listing each node and its
dependencies as plain text. On upgrade the component hides the list visually
(re-accessible via toggle) and draws the graph.

## 17. Dependencies

- §6 data-source adapter interface (adapter keys: `static`, `jira`, `linear`,
  `npm`, `github`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 overlay/positioning engine (detail panel)
- §6 live-region/announcement service (cycle detection alert)
- §6 localization/formatting hook
- §5.9 Diagram/Graph viewer pluggable rendering adapter (layout: dagre/elk/force)

## 18. Edge cases & error handling

- **Single node, no edges** — node rendered centered; no critical path computed.
- **Cycles in data** — cycle-detection badge and alert; critical path still
  computed for the acyclic subgraph.
- **Disconnected subgraphs** — multiple independent clusters laid out side by
  side.
- **Adapter failure** — error slot shown; stale data retained.
- **Very large graphs (>200 nodes)** — minimap forced on; node labels hidden
  until zoom > 0.5; warning logged recommending filtering.
- **Node label overflow** — truncated with tooltip.

## 19. Acceptance criteria

- [ ] Nodes and edges render from static `data` property.
- [ ] Critical-path nodes and edges carry accent color and thick stroke.
- [ ] Cycle detection fires `mj-cycle-detected` and shows warning banner.
- [ ] Selecting a node fires `mj-node-select` and opens detail panel.
- [ ] Keyboard navigation per §12 moves through nodes.
- [ ] Accessible adjacency list present in DOM.
- [ ] `layout` attribute change re-renders with the new algorithm.
- [ ] PERT mode shows EST/LST/float on each node.
- [ ] Minimap renders when `show-minimap` is true.
- [ ] RTL layout re-applies layout with RTL hint.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should cycle detection warn only (display badge) or hard-block rendering?
  Hard-blocking may be confusing for legacy dependency data with known cycles.
- Is the `npm` adapter fetching `package.json` dependency trees from the registry
  API or from a local manifest file via `src`?
- Should the PERT float calculation happen in the adapter or client-side, and
  what is the contract if `criticalPath` is pre-populated by the adapter?
