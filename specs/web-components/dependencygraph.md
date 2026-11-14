# Dependency Graph Spec

- **Tag:** `<mj-dependency-graph>`
- **Class / file:** `MjDependencyGraph` / `components/mjdependencygraph.js` (base: `components/pmchartwrapper.js`)
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Variant — a convenience wrapper for `<mj-chart type="dependency-graph">`
- **Synonyms covered:** Dependency graph, Task network, Module dependencies
- **Status:** Implemented (wrapper since WW-1498)

> `<mj-dependency-graph>` is `<mj-chart type="dependency-graph">` with the type
> fixed and the work-item data shape of this component family. Drawing (labelled
> boxes in longest-path columns, status colours, the critical path, dashed cycle
> edges and badges), keyboard support, the data table and data loading are the
> chart's: see [chart.md](chart.md) (§21) and the `dependency-graph` chart-type
> page. This spec records only what differs.

## 1. Purpose and when to use

Work items or modules and the order they depend on each other, with the critical
path and cycles called out. Use `<mj-chart type="network">` for undirected
relationship graphs and `<mj-workflow-diagram>` for state machines.

## 2. Data shape (mapped onto the chart type)

```
{ nodes: [{ id, name, status, estimate }], edges: [{ from, to }], criticalPath: [nodeId, ...] }
```

| Wrapper field | Chart type field |
|---|---|
| `node.id` (else `name`, else `node-N`) | `id` |
| `node.name` (else the id) | `label` |
| `node.status` (missing = todo) | `status` |
| `node.estimate` | — (shown in the detail panel) |
| `edges: [{ from, to }]` (prerequisite -> dependent) | `links: [{ source, target }]` |
| `criticalPath` | same |

Edges naming an unknown node are ignored.

## 3. Attributes

| Attribute | Chart type option |
|---|---|
| `show-critical-path` | same (default on) |
| `src` | as on `<mj-chart>` |

## 4. Properties

| Property | Description |
|---|---|
| `data` | The data above; assigning draws at once, clears the selection, emits `mj-data-load` (and `mj-cycle-detected`) |
| `selectedNode` | The selected node object, or null |
| `cycles` | `string[][]`: every cycle of the current data as node ids (one per edge that closes a cycle) |
| `zoom` | Always 1 |

## 5. Events

| Event | `detail` | From |
|---|---|---|
| `mj-node-select` | `{ node }` | `mj-chart-node-click`; opens the inline detail panel |
| `mj-node-deselect` | `{}` | the detail panel closed |
| `mj-data-load` | `{ nodes, edges, hasCycles }` | first draw of each data object |
| `mj-cycle-detected` | `{ cycles }` | after `mj-data-load`, when the data has cycles (`mj-chart-cycle-detect`) |
| `mj-error` | `{ message }` | `mj-chart-error` |

## 6. Slots and parts

- Slots: `node-detail` (extra detail-panel content), `empty`.
- Parts: `toolbar`, `cycle-banner` (a `role="alert"` banner naming the cycles,
  e.g. "B → C → B"), `detail-panel`, the chart's `surface`, `svg`, `message`,
  `table data-table`, and the renderer's `node` (`node critical-path-node` on the
  path), `edge` (`edge critical-path-edge`; cycle edges carry `data-cycle-edge`),
  `cycle-badge`.

## 7. Migration (behaviour changes from the standalone implementation)

- The graph fits its width: boxes are 64-160 px wide depending on the number of
  columns (were a fixed 160 px with sideways scrolling); it grows in height with
  its busiest column.
- Edges are straight or gently curved lines with arrowheads (were orthogonal
  routes between the boxes); the edge that closes a cycle is a dashed red curve
  (was routed above the nodes).
- The status is a coloured dot and text in the box and the box border's colour
  (text was in the status colour); critical nodes have an amber border on a
  warning-surface fill as before.
- The dependency list (`dl`, part `a11y-list`) is replaced by the chart's data
  table (Node / Status / Critical path / Links to / Linked from), disclosed by the
  toolbar button. Parts `wrapper`, `canvas`, `a11y-list` and `empty-state` are
  gone; a node on the critical path now carries both `node` and
  `critical-path-node`. Error texts are the chart's generic messages (detail in
  `mj-error`); the default-slot fallback is not shown.
