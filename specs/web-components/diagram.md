# Diagram Spec

- **Tag:** `<mj-diagram>`
- **Class / file:** `MjDiagram` / `mjdiagram.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Graph viewer, Node/edge diagram
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-diagram>` renders a node/edge graph diagram using a pluggable layout adapter
(e.g. Cytoscape.js, Dagre, ELK). The component owns the accessible surface —
keyboard pan/zoom, selectable nodes with accessible names, an accessible list-of-
nodes-and-edges text alternative — while delegating all graph layout and pixel
rendering to the adapter. It is reused by BranchGraph, Dependency graph, and
Workflow diagram components in §5.11.

## 2. When to use / when not to use

**Use** for node/edge visualizations: dependency graphs, workflow diagrams, state
machines, network topologies, and org charts.

**Do not use** for geographic maps (use `<mj-map>`), for timeline/Gantt charts
(use `<mj-chart>` or the P3 chart variants), for simple list relationships
(use a nested `<ul>` instead). Do not use without a layout adapter.

## 3. Anatomy

- **Container** (`::part(container)`) — outermost element with overflow hidden;
  holds the render target and overlay controls.
- **Render target** (`::part(render-target)`) — the `<div>` or `<canvas>` passed
  to the layout adapter for graph drawing.
- **Controls bar** (`::part(controls)`) — overlaid panel with zoom in/out and
  fit-to-view buttons.
- **Zoom in button** (`::part(zoom-in)`) — increments zoom.
- **Zoom out button** (`::part(zoom-out)`) — decrements zoom.
- **Fit button** (`::part(fit-btn)`) — resets pan/zoom to fit all nodes in view.
- **Selection panel** (`::part(selection-panel)`) — optional side panel or popup
  showing details of the selected node or edge.
- **Node list** (`::part(node-list)`) — visually hidden (or `show-list`-visible)
  `<ul>` listing all nodes with their labels and relationships as text, providing
  the accessible structural alternative.
- **Loading** (`::part(loading)`) — shown while adapter initializes.
- **Error** (`::part(error)`) — shown when adapter or data fails.
- **Empty** (`::part(empty)`) — shown when the graph has zero nodes.

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Default directed | `directed="true"` (default) | Edges have directional arrows |
| Undirected | `directed="false"` | Edges are bidirectional/unordered |
| List visible | `show-list` (boolean) | Node list rendered visibly below the diagram |
| Readonly | `interactive="false"` | Pan/zoom disabled; node selection disabled |
| With selection panel | `show-selection-panel` (boolean) | Selection details shown in a side panel |
| Fit on load | `fit-on-load` (boolean, default true) | Auto-fits view to all nodes after first render |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `directed` | `boolean` | `true` | Yes | Whether edges have direction/arrows |
| `interactive` | `boolean` | `true` | Yes | Enable pan, zoom, and node selection |
| `show-list` | `boolean` | `false` | Yes | Render node/edge list visibly as a structural fallback |
| `show-selection-panel` | `boolean` | `false` | Yes | Show details panel for selected node/edge |
| `fit-on-load` | `boolean` | `true` | Yes | Auto-fit view after first render |
| `zoom` | `number` | `1` | Yes | Current zoom level; read/write; setting it calls `adapter.setZoom()` |
| `min-zoom` | `number` | `0.25` | Yes | Minimum zoom level |
| `max-zoom` | `number` | `4` | Yes | Maximum zoom level |
| `label` | `string` | `""` | Yes | Accessible label for the diagram region |
| `loading` | `boolean` | `false` | Yes | Shows the loading state |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `adapter` | `DiagramAdapter` | Pluggable layout adapter; must implement `{ init(target, options): void, destroy(): void, setData(graph): void, setZoom(level): void, fit(): void, selectNode(id): void, deselectAll(): void, on(event, handler): void }` |
| `adapterOptions` | `object` | Adapter-specific config passed verbatim to `adapter.init()` |
| `graph` | `DiagramGraph` | `{ nodes: DiagramNode[], edges: DiagramEdge[] }` where `DiagramNode = { id: string, label: string, description?: string, type?: string, data?: object }` and `DiagramEdge = { id: string, source: string, target: string, label?: string, type?: string }` |
| `selectedNodeId` | `string \| null` | Currently selected node id; setting it calls `adapter.selectNode()` |
| `selectedEdgeId` | `string \| null` | Currently selected edge id |

## 7. Slots

| Slot | Description |
|------|-------------|
| `selection-panel` | Custom detail content for the selected node/edge; receives selection data via a `detail` property |
| `empty` | Content shown when `graph.nodes` is empty |
| `controls` | Additional buttons appended to the controls bar |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-diagram-ready` | `{}` | Yes | No | Fired after adapter has rendered the initial graph |
| `mj-diagram-node-select` | `{ node: DiagramNode }` | Yes | No | Fired when a node is selected |
| `mj-diagram-node-deselect` | `{}` | Yes | No | Fired when node selection is cleared |
| `mj-diagram-edge-select` | `{ edge: DiagramEdge }` | Yes | No | Fired when an edge is selected |
| `mj-diagram-zoom-change` | `{ zoom: number }` | Yes | No | Fired after zoom changes (debounced 200ms) |
| `mj-diagram-pan` | `{ x: number, y: number }` | Yes | No | Fired after panning completes (debounced 200ms) |
| `mj-diagram-error` | `{ message: string }` | Yes | No | Fired when adapter fails |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)`, `::part(render-target)`, `::part(controls)`
- `::part(zoom-in)`, `::part(zoom-out)`, `::part(fit-btn)`
- `::part(selection-panel)`, `::part(node-list)`
- `::part(loading)`, `::part(error)`, `::part(empty)`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-diagram-height` | `480px` | Default diagram container height |
| `--mj-diagram-bg` | `var(--mj-color-surface-1)` | Render target background |
| `--mj-diagram-radius` | `var(--mj-radius-md)` | Container corner radius |
| `--mj-diagram-controls-bg` | `var(--mj-color-surface-1)` | Controls panel background |
| `--mj-diagram-controls-shadow` | `var(--mj-elevation-2)` | Controls panel shadow |
| `--mj-diagram-selection-panel-width` | `16rem` | Width of the selection detail panel |
| `--mj-diagram-focus-ring` | `var(--mj-focus-ring)` | Focus ring on the render target |
| `--mj-diagram-node-selected-color` | `var(--mj-color-primary)` | Token passed to adapter for selected node highlight |
| `--mj-diagram-edge-color` | `var(--mj-color-border)` | Token passed to adapter for edge color |

## 10. States

- **loading** — adapter initializing; spinner shown; `aria-busy="true"`.
- **ready** — graph rendered; nodes navigable.
- **empty** — `graph.nodes` is empty or `graph` not set.
- **error** — adapter threw; error part shown; `mj-diagram-error` fired.
- **node-selected** — a node is highlighted; selection panel populated (if enabled).
- **edge-selected** — an edge is highlighted.
- **panning** — user is dragging the render target; cursor changes to `grabbing`.
- **zoomed-min** — zoom at `min-zoom`; zoom-out button `aria-disabled="true"`.
- **zoomed-max** — zoom at `max-zoom`; zoom-in button `aria-disabled="true"`.

## 11. Behavior & interactions

On `connectedCallback` the component calls `adapter.init(target, adapterOptions)`,
then calls `adapter.setData(graph)` if `graph` is already set. It listens to
adapter events for node/edge clicks and selection changes, translating them to
`mj-diagram-*` custom events.

When `graph` property changes, the component calls `adapter.setData(graph)`,
rebuilds the node list, and (if `fit-on-load`) calls `adapter.fit()`.

Keyboard pan: when the render target has focus, arrow keys pan by a step
proportional to `100 / currentZoom` pixels. `+`/`-` adjust zoom by 0.25 steps.

Node navigation via node list: the node list `<ul>` items are `<a>` elements or
`<button>` elements. When activated, they call `adapter.selectNode(id)` and
`adapter.panTo(node)` to bring the node into view. This provides full keyboard
navigation of the graph without requiring pointer interaction.

When a node is selected, the selection panel (if `show-selection-panel`) receives
the `DiagramNode` data and opens. Focus moves into the panel. Esc closes the panel
and returns focus to the node list item corresponding to the selected node.

Pan/zoom announcements are debounced at 200ms to avoid flooding the live region.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus into the diagram; first stop is the node list or render target |
| `↑` / `↓` / `←` / `→` | Pan the diagram in the corresponding direction (when render target is focused) |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `F` | Fit all nodes in view |
| `Tab` (within node list) | Move between node list items |
| `Enter` / `Space` (on node list item) | Select node; pan to it; open selection panel |
| `Escape` | Close selection panel; return focus to the triggering node list item |
| `Tab` (within selection panel) | Navigate interactive elements in the detail panel |

## 13. Accessibility

- The component renders as a `<section role="application">` with `aria-label` from
  the `label` attribute (required; warns if absent).
- The render target `<div>` has `tabindex="0"` and `aria-label` set to a
  localized "Diagram canvas" string; it is the entry point for keyboard pan/zoom.
- The node list (`<ul>`) is always present in the shadow DOM. Each item uses a
  `<button>` with `aria-label` equal to the node's `label` and `aria-describedby`
  pointing to a visually-hidden span with the node's `description`.
- Edges are listed in the node list as `<li>` sub-items within each node item:
  "Connected to: [target label]".
- The selection panel has `role="dialog"` with `aria-label` equal to the selected
  node's label; focus is trapped within it while open.
- Node types and edge types are never differentiated by color alone; they must
  also use distinct shapes or dash patterns (communicated to the adapter via
  node/edge `type` string and corresponding token or adapter option).
- Zoom controls carry `aria-label` and `aria-disabled` at min/max zoom.
- Zoom/pan changes are announced via `role="status"` live region (debounced).

## 14. Form participation

N/A — `<mj-diagram>` is a display/interaction component with no form value.

## 15. Internationalization & RTL

- All UI strings (button labels, live region messages, node list structure) are
  overridable via the localization hook (§3.8).
- In RTL mode the controls panel docks to the start edge; arrow key pan directions
  remain absolute (left arrow = pan canvas left, regardless of text direction).
- Node labels in the adapter rendering use the `label` string from `DiagramNode`;
  localization of those strings is the host's responsibility.

## 16. Progressive enhancement / SSR

The server renders the node list as a visible `<ul>` inside `<mj-diagram>`. Without
scripting the list is immediately usable as a structured text description of the
graph. On upgrade the component promotes the list into the shadow DOM structure
(hidden unless `show-list`) and initializes the adapter.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection.
- **Design-token stylesheet** (§6) — color, elevation, and motion tokens.
- **Overlay/positioning engine** (§6) — selection panel positioning.
- **Focus utilities** (§6) — selection panel focus trap and restore.
- **Live-region service** (§6) — zoom, pan, and selection announcements.
- **Localization hook** (§6) — all user-facing strings.
- **Pluggable layout adapter** — supplied by the host application; not bundled.

## 18. Edge cases & error handling

- `adapter` not set: renders node list only; logs a console error.
- `adapter.init()` or `adapter.setData()` throws: error state shown; `mj-diagram-error`
  fired; node list remains functional.
- `graph.nodes` is empty: empty state shown; adapter not called with empty data.
- Circular references in edges (cycle): adapter is responsible for cycle detection;
  the component passes data verbatim and documents this in the adapter contract.
- Node `id` not unique: first occurrence is used; a console error is logged for
  the duplicate; the node list deduplicates by id.
- Container resized to zero: `ResizeObserver` skips adapter resize; resumes on
  non-zero size.
- `selectedNodeId` set to an id not present in `graph.nodes`: clears selection;
  logs a console warning.

## 19. Acceptance criteria

- [ ] Adapter `init()` called on `connectedCallback`; `setData()` called when `graph` is set.
- [ ] Node list is always in the shadow DOM with one `<button>` per node.
- [ ] Node list items pan to the node and select it on activation.
- [ ] Arrow keys pan the diagram when render target is focused.
- [ ] `+`/`-` keys change zoom; `F` fits all nodes.
- [ ] `mj-diagram-node-select` fires with the correct node when selected.
- [ ] Selection panel opens on selection (when `show-selection-panel`); Esc closes it.
- [ ] Zoom buttons have correct `aria-disabled` at min/max zoom.
- [ ] `role="application"` + `aria-label` present on the section element.
- [ ] `show-list` renders the node list visibly.
- [ ] No-adapter fallback shows node list with a console error.
- [ ] RTL mode docks controls to the start edge.
- [ ] Adapter error fires `mj-diagram-error` and shows the error state.
- [ ] Automated accessibility checks pass with no violations.

## 20. Open questions

- Should `<mj-diagram>` expose a `layout` attribute (e.g. `"dagre"`, `"elk-layered"`,
  `"force-directed"`) so a multi-algorithm adapter can switch algorithms, or is
  that entirely the adapter's concern?
- Should the selection panel be a separate `<mj-diagram-panel>` component that
  hosts compose, or always an internal part of `<mj-diagram>`?
- Should the node list expose edge traversal controls (e.g. "follow edge to [target]")
  to enable graph walking entirely via keyboard through the list?
