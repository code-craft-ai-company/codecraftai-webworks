# Flow & Process Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Each entry uses this format:

### <Chart name>  *(synonyms / alternate names)*
- **Renderer / `type`:** `<key>` — **Primary renderer** | **Variant of `<key>`**
- **Controller:** `<mj-chart type="<key>" ...>`
- **Purpose:** one line — what this chart is best for.
- **Decomposition:** the part components it uses.
- **JSON shape:** the concrete data shape this chart consumes.
- **SVG primitives:** the SVG elements the renderer emits.
- **Orientation:** `horizontal` / `vertical` support, or `n/a`.
- **Variants / modes:** related catalog names satisfied by an attribute mode.
- **Phase:** P0–P5 per the plan's phasing.
- **Notes:** anything implementation-relevant.

---

### Sankey Diagram  *(energy-flow diagram, flow map)*

- **Renderer / `type`:** `sankey` — **Primary renderer**
- **Controller:** `<mj-chart type="sankey" ...>`
- **Purpose:** Visualise the magnitude of flow between stages or categories, with link widths proportional to flow volume.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Flow / network family (plan §3.4):
  ```json
  {
    "meta": { "title": "Energy Flow" },
    "nodes": [
      { "id": "coal" },
      { "id": "electricity" },
      { "id": "residential" }
    ],
    "links": [
      { "source": "coal", "target": "electricity", "value": 120 },
      { "source": "electricity", "target": "residential", "value": 80 }
    ]
  }
  ```
- **SVG primitives:** `<path>` (cubic-bezier bands for links, proportional to `value`), `<rect>` (node bars), `<text>` (node labels), `<g>` (grouping per node/link)
- **Orientation:** `horizontal` (left-to-right default) / `vertical` (top-to-bottom); swaps the primary axis along which stages are laid out.
- **Variants / modes:**
  - `alluvial` — Variant of `sankey`; see Alluvial Diagram entry below.
- **Phase:** P4
- **Notes:** Layout engine iterates node ranks using a force-relaxation or iterative positioning algorithm; node `y` positions are resolved to avoid overlap. Link paths are cubic Bézier curves whose stroke-width encodes `value`. Uses `band` scale for node positioning and `linear` scale for link widths. Accessibility: data-table lists source → target → value rows.

---

### Alluvial Diagram  *(parallel sets, flow-over-time)*

- **Renderer / `type`:** `sankey` — **Variant of `sankey`**
- **Controller:** `<mj-chart type="sankey" mode="alluvial" ...>`
- **Purpose:** Show how a categorical population redistributes across multiple time points or classification dimensions.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Same `nodes` / `links` envelope as `sankey`, with nodes grouped by a `group` or `time` field to define parallel column positions:
  ```json
  {
    "meta": { "title": "Customer Journey" },
    "nodes": [
      { "id": "2023-new",   "group": "2023", "label": "New" },
      { "id": "2023-loyal", "group": "2023", "label": "Loyal" },
      { "id": "2024-new",   "group": "2024", "label": "New" },
      { "id": "2024-loyal", "group": "2024", "label": "Loyal" }
    ],
    "links": [
      { "source": "2023-new",   "target": "2024-loyal", "value": 42 },
      { "source": "2023-loyal", "target": "2024-loyal", "value": 71 }
    ]
  }
  ```
- **SVG primitives:** `<path>` (smooth ribbon bands), `<rect>` (column blocks), `<text>` (group / node labels), `<g>`
- **Orientation:** `horizontal` (columns left-to-right) / `vertical` (columns top-to-bottom).
- **Variants / modes:** None beyond the `sankey` primary.
- **Phase:** P4
- **Notes:** Rendered by the `sankey` renderer with `mode="alluvial"`; the renderer pins nodes into explicit columns derived from the `group` field instead of computing ranks from topology. Coloring follows group or series color ramp from design tokens.

---

### Chord Diagram  *(circos, relationship wheel)*

- **Renderer / `type`:** `chord` — **Primary renderer**
- **Controller:** `<mj-chart type="chord" ...>`
- **Purpose:** Show bidirectional or symmetric flows and relationships between groups arranged on a circle.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:** Flow / network family; a symmetric matrix expressed as `nodes` + `links` (both directions may be listed, or only the upper triangle; renderer symmetrises):
  ```json
  {
    "meta": { "title": "Trade Flows" },
    "nodes": [
      { "id": "USA" },
      { "id": "EU" },
      { "id": "China" }
    ],
    "links": [
      { "source": "USA",   "target": "EU",    "value": 300 },
      { "source": "USA",   "target": "China",  "value": 200 },
      { "source": "EU",    "target": "China",  "value": 150 }
    ]
  }
  ```
- **SVG primitives:** `<path>` (arc segments on the ring, cubic-Bézier chord ribbons), `<text>` (group labels), `<g>`
- **Orientation:** `n/a` — radial layout has no meaningful horizontal/vertical orientation.
- **Variants / modes:** None.
- **Phase:** P4
- **Notes:** Arc positions derived from summed link values per node; chord ribbons are quadratic or cubic Bézier paths whose two anchors lie on the ring. Uses `linear` scale to map cumulative value to angle in `[0, 2π]`. Accessibility: data-table lists pairwise flow values. Marks are `role="img"` with generated `aria-label`.

---

### Flowchart  *(process diagram, workflow diagram)*

- **Renderer / `type`:** `flowchart` — **Primary renderer**
- **Controller:** `<mj-chart type="flowchart" ...>`
- **Purpose:** Depict a sequence of process steps, decision branches, and control flow between them.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Flow / network family; nodes carry a `shape` field; links carry an optional `label` for decision branches:
  ```json
  {
    "meta": { "title": "Order Processing" },
    "nodes": [
      { "id": "start",    "label": "Start",          "shape": "oval" },
      { "id": "receive",  "label": "Receive order",   "shape": "rect" },
      { "id": "instock",  "label": "In stock?",       "shape": "diamond" },
      { "id": "ship",     "label": "Ship order",      "shape": "rect" },
      { "id": "reorder",  "label": "Reorder item",    "shape": "rect" },
      { "id": "end",      "label": "End",             "shape": "oval" }
    ],
    "links": [
      { "source": "start",   "target": "receive",  "value": 1 },
      { "source": "receive", "target": "instock",  "value": 1 },
      { "source": "instock", "target": "ship",     "value": 1, "label": "Yes" },
      { "source": "instock", "target": "reorder",  "value": 1, "label": "No" },
      { "source": "ship",    "target": "end",      "value": 1 },
      { "source": "reorder", "target": "receive",  "value": 1 }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (process boxes), `<path>` (diamond decisions, ovals, arrows/connectors), `<line>` (straight connector segments), `<polygon>` (arrowheads), `<text>` (node and edge labels), `<g>`
- **Orientation:** `horizontal` (left-to-right flow) / `vertical` (top-to-bottom flow); controls the primary layout direction of the auto-routing algorithm.
- **Variants / modes:** None in this file; see Dependency Graph and Decision Tree for specialisations.
- **Phase:** P4
- **Notes:** Auto-layout via layered (Sugiyama-style) graph layout: assign ranks, sort within ranks to minimise crossings, route edges with orthogonal or curved connectors. Cycle detection required (back-edges from `reorder` to `receive` in example). Node `shape` controls which SVG primitive is used per node.

---

### Funnel Chart  *(pipeline chart, conversion funnel)*

- **Renderer / `type`:** `funnel` — **Primary renderer**
- **Controller:** `<mj-chart type="funnel" ...>`
- **Purpose:** Show progressive reduction of a quantity through sequential stages, such as a sales or conversion pipeline.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Common envelope; `categories` name the stages and `series[0].values` give the counts or rates:
  ```json
  {
    "meta": { "title": "Sales Funnel" },
    "categories": ["Leads", "Qualified", "Proposals", "Closed"],
    "series": [
      { "name": "2025", "values": [10000, 4200, 1500, 420] }
    ]
  }
  ```
- **SVG primitives:** `<polygon>` or `<path>` (trapezoid / truncated triangle segments per stage), `<text>` (stage labels and value labels), `<g>`
- **Orientation:** `vertical` (stages flow top-to-bottom, widths narrow downward, default) / `horizontal` (stages flow left-to-right).
- **Variants / modes:**
  - Pyramid chart — same renderer with `mode="pyramid"` (widths increase toward the last stage instead of narrowing).
- **Phase:** P2
- **Notes:** Width of each stage segment is proportional to its value relative to the first (largest) stage. The `linear` scale maps value → half-width. Gap between stages is configurable via a design token or attribute. Drop-off percentage between adjacent stages may be annotated via `mj-chart-value-labels`.

---

### Waterfall Chart  *(bridge chart, cascade chart)*

- **Renderer / `type`:** `waterfall` — **Primary renderer**
- **Controller:** `<mj-chart type="waterfall" ...>`
- **Purpose:** Show how an initial value increases or decreases through a sequence of positive and negative contributions to reach a final total.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` ×2, `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Common envelope; each `series[0].values` entry represents a step; a special `type` field on each value marks it as `"total"` or `"subtotal"` so the renderer can anchor it at zero:
  ```json
  {
    "meta": { "title": "2025 P&L Bridge" },
    "categories": ["Start", "Revenue", "COGS", "OpEx", "Tax", "Net"],
    "series": [
      {
        "name": "P&L",
        "values": [
          { "v": 500,  "kind": "total" },
          { "v": 200,  "kind": "add" },
          { "v": -80,  "kind": "subtract" },
          { "v": -60,  "kind": "subtract" },
          { "v": -20,  "kind": "subtract" },
          { "v": 540,  "kind": "total" }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (floating bars for incremental steps, grounded bars for totals), `<line>` (connector lines between bars), `<text>` (value labels, category labels), `<g>`
- **Orientation:** `vertical` (bars rise/fall on the value axis, categories on the x-axis, default) / `horizontal` (rotated; categories on the y-axis).
- **Variants / modes:** None.
- **Phase:** P2
- **Notes:** Each `<rect>` is positioned by computing a running cumulative baseline; `linear` scale maps value domain → pixel range. `total`/`subtotal` steps always start at zero baseline. Connector `<line>` elements link the top of one bar to the base of the next. Color distinguishes positive, negative, and total steps using design tokens (`--mj-color-positive`, `--mj-color-negative`, `--mj-color-neutral` or equivalent).

---

### Dependency Graph  *(module graph, package graph, task network)*

- **Renderer / `type`:** `dependency-graph` — **Variant of `network`** (`charts/core/renderers/network.js`, layered layout by default). (An earlier draft of this entry named the type `depgraph`; the shipped key is `dependency-graph`.)
- **Controller:** `<mj-chart type="dependency-graph" ...>`; `<mj-dependency-graph>` is a convenience wrapper for this type with the work-item data shape (see `../web-components/dependencygraph.md`, WW-1498).
- **Purpose:** Visualise directed dependency relationships among software components, packages, or work items, with the critical path and cycles called out.
- **Decomposition:** drawn by the renderer inside `<mj-chart>`; `mj-chart-legend` (one entry per node group, when nodes have groups), `mj-chart-title` and `mj-chart-data-table` bind as parts.
- **JSON shape:** Flow / network family; directed links from `source` to `target`:
  ```json
  {
    "meta": { "title": "Package Dependencies" },
    "nodes": [
      { "id": "app",    "label": "app",    "group": "ui" },
      { "id": "core",   "label": "core",   "status": "done" },
      { "id": "utils",  "label": "utils",  "status": "in-progress" },
      { "id": "lodash", "label": "lodash", "status": "blocked" }
    ],
    "links": [
      { "source": "app",  "target": "core",   "value": 1 },
      { "source": "app",  "target": "utils",  "value": 1 },
      { "source": "core", "target": "lodash", "value": 1 }
    ],
    "criticalPath": ["app", "core", "lodash"]
  }
  ```
  `nodes[]`: `id` (required; a repeated id keeps its first node), `label` (else the id), `group`, `status` (`todo`, `planned`, `in-progress`, `done`, `completed`, `blocked`, or any text shown as given), `value`. `links[]`: `source`, `target` (links naming an unknown node are skipped), `value`, `label`. `criticalPath`: an ordered list of node ids.
- **Drawing (changed from the earlier circle drawing):** each node is a **labelled box** — the name, and when the node has a `status` a second line with a status dot and the status text — whose border shows the status (todo / planned `--mj-text-muted`, in-progress `--mj-accent`, done / completed `--mj-color-success`, blocked `--mj-color-danger`), else the node's group colour, else a neutral border. Boxes are 64–160 px wide to fit the columns (30 px tall without statuses, 40 px with). Nodes are placed in longest-path columns (Sugiyama-style ranks with barycentre ordering); links are straight arrows from box edge to box edge, curved where a straight line would cross another box. Nodes in `criticalPath` get a thicker amber (`--mj-color-warning`) border on a warning-surface fill, and every link joining two consecutive path entries is amber and thicker. The link that closes a cycle (found by a DFS) is left out of the ranking and drawn as a dashed red (`--mj-color-danger`) curve; self-links are small loops on the box's corner; nodes on a cycle get a ⚠ badge.
- **SVG primitives:** `<g>` per node (the focusable mark) with `<rect>`, `<text>` and a status `<circle>`; `<g>` per link with `<path>` and an arrowhead `<polygon>`; `<text>` badges.
- **Orientation:** `horizontal` (registered default; ranks left to right) / `vertical` (ranks top to bottom).
- **Options:**
  | Option | Default | Effect |
  |---|---|---|
  | `layout` | `layered` | `force`, `arc`, `bundled`, `static` use the network drawing (circles) instead of the boxes |
  | `orientation` | `horizontal` | direction of the ranks |
  | `show-critical-path` | on | `"false"` draws critical-path nodes and links like the others |
- **Height:** the renderer asks for the height its busiest column needs (`ctx.setContentHeight`), so a chart without a fixed height grows with it; the width is shared by the columns.
- **Events:**
  | Event | `detail` |
  |---|---|
  | `mj-chart-node-click` | `{ id, label, group, index }` |
  | `mj-chart-edge-click` | `{ source, target, value, label }` |
  | `mj-chart-cycle-detect` | `{ cycles: [[nodeId, ...]] }` — one array per link that closes a cycle; emitted once per data object, not on every redraw |
- **Parts:** `plot`, `node` (`node critical-path-node` on the path), `edge` (`edge critical-path-edge`; a cycle link carries `data-cycle-edge`), `cycle-badge`; nodes carry `data-mark="node:<index>"`.
- **Accessibility:** each node's accessible name gives its label, group, value, link count, status, "on the critical path" and "in a cycle". The accessible table lists every node: Node, Group, Value, Status, Critical path (each when present), Links to, Linked from; the caption counts nodes, links and cycles.
- **Phase:** P4 — implemented.
- **Notes:** Cycles never break the layout and never raise `mj-chart-error`. With `layout="force"` (or any non-layered layout) the type draws like `network` (value-sized circles), so the boxes, the critical-path highlighting and the cycle event apply to the layered layout only (the table's Critical path column is filled in every layout).

---

### Network Graph  *(node-link diagram, graph diagram)*

- **Renderer / `type`:** `network` — **Primary renderer**
- **Controller:** `<mj-chart type="network" ...>`
- **Purpose:** Show connections and relationships between a set of entities without implying directional flow or hierarchy.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`, `mj-chart-brush`
- **JSON shape:** Flow / network family; nodes may carry a `group` or `category` for coloring; links carry optional `value` for line weight:
  ```json
  {
    "meta": { "title": "Social Network" },
    "nodes": [
      { "id": "alice", "label": "Alice", "group": "team-a" },
      { "id": "bob",   "label": "Bob",   "group": "team-b" },
      { "id": "carol", "label": "Carol", "group": "team-a" }
    ],
    "links": [
      { "source": "alice", "target": "bob",   "value": 5 },
      { "source": "alice", "target": "carol", "value": 3 }
    ]
  }
  ```
- **SVG primitives:** `<circle>` (nodes, radius from `sqrt` scale on optional `nodes[].value`), `<line>` or `<path>` (edges, stroke-width from `value`), `<text>` (node labels), `<g>`
- **Orientation:** `n/a` — force-directed layout is orientation-independent.
- **Variants / modes:**
  - Arc diagram — `layout="arc"` places nodes on a single axis and draws edges as arcs above/below.
- **Phase:** P4
- **Notes:** Default layout is force-directed (iterative spring-repulsion, fully in-renderer, no external library). The `mj-chart-brush` part enables lasso selection of nodes. Node `group` drives the categorical color ramp (`ordinal-color` scale). `mj-chart-brush` reports selected node ids via `mj-chart-select`. Zoom/pan handled by updating the SVG `viewBox` on pointer events. Compare with Dependency Graph (`dependency-graph`) which uses a directed layered layout of labelled boxes.

---

### Tree Diagram  *(hierarchy diagram)*

- **Renderer / `type`:** `tree` — **Primary renderer**
- **Controller:** `<mj-chart type="tree" ...>`
- **Purpose:** Display a hierarchical parent-child structure as a node-link tree with explicit branch connections.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Hierarchical family (plan §3.4); `root` is a recursive structure:
  ```json
  {
    "meta": { "title": "File System" },
    "root": {
      "name": "src",
      "value": null,
      "children": [
        {
          "name": "core",
          "value": null,
          "children": [
            { "name": "scales.js", "value": 12 },
            { "name": "svgdraw.js", "value": 18 }
          ]
        },
        { "name": "index.js", "value": 3 }
      ]
    }
  }
  ```
- **SVG primitives:** `<circle>` or `<rect>` (nodes), `<path>` (curved or straight connectors between parent and child nodes), `<text>` (node labels), `<g>`
- **Orientation:** `horizontal` (root at left, leaves at right) / `vertical` (root at top, leaves at bottom).
- **Variants / modes:**
  - Radial tree — `layout="radial"` arranges the tree in polar coordinates (root at center).
  - Dendrogram — see `specs/chart-components/09-hierarchical.md`; the `tree` renderer with `mode="dendrogram"` clusters leaves by similarity.
- **Phase:** P4
- **Notes:** Layout uses a Reingold-Tilford (tidy tree) algorithm to assign x/y positions with minimal crossings and balanced subtrees. Edge connectors are cubic Bézier paths or elbow connectors based on an attribute (`edge-style="curve|elbow"`). This chart also appears in `09-hierarchical.md`; both files reference the same `tree` renderer. See that file for the dendrogram variant and cross-reference.

---

### Decision Tree  *(classification tree, regression tree)*

- **Renderer / `type`:** `tree` — **Variant of `tree`**
- **Controller:** `<mj-chart type="tree" mode="decision" ...>`
- **Purpose:** Show branching decisions or classification splits, with edge labels carrying conditions and leaf nodes carrying outcomes.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Hierarchical family; leaf nodes carry an `outcome` or `label`; edges (encoded as `children[].edgeLabel`) carry the split condition:
  ```json
  {
    "meta": { "title": "Loan Decision" },
    "root": {
      "name": "Income > 50k?",
      "value": null,
      "children": [
        {
          "name": "Credit > 700?",
          "edgeLabel": "Yes",
          "value": null,
          "children": [
            { "name": "Approve",  "edgeLabel": "Yes", "value": 1 },
            { "name": "Review",   "edgeLabel": "No",  "value": 0.5 }
          ]
        },
        { "name": "Deny", "edgeLabel": "No", "value": 0 }
      ]
    }
  }
  ```
- **SVG primitives:** `<rect>` (decision and leaf nodes), `<path>` (connectors), `<text>` (node question labels, edge condition labels, outcome labels), `<g>`
- **Orientation:** `vertical` (root at top, decisions downward, default) / `horizontal`.
- **Variants / modes:** None beyond the `tree` primary.
- **Phase:** P4
- **Notes:** Reuses the `tree` renderer layout engine; `mode="decision"` activates edge-label rendering via `mj-chart-annotation`-style text along connectors, and rectangular node shapes instead of circles. Node coloring can encode class purity or a probability value via the `linear` scale mapped to a diverging color ramp from design tokens.
