# Hierarchical Charts

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

### Tree Diagram  *(hierarchy diagram, node-link tree)*

- **Renderer / `type`:** `tree` — **Primary renderer**
- **Controller:** `<mj-chart type="tree" ...>`
- **Purpose:** Display parent-child relationships as a node-link tree with explicit branch connectors between every level.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Hierarchical family (plan §3.4); `root` is a recursive structure:
  ```json
  {
    "meta": { "title": "Org Structure" },
    "root": {
      "name": "CEO",
      "value": null,
      "children": [
        {
          "name": "CTO",
          "value": null,
          "children": [
            { "name": "Eng Lead", "value": null, "children": [] },
            { "name": "QA Lead",  "value": null, "children": [] }
          ]
        },
        { "name": "CFO", "value": null, "children": [] }
      ]
    }
  }
  ```
- **SVG primitives:** `<circle>` or `<rect>` (nodes), `<path>` (curved or elbow connectors between parent and child), `<text>` (node labels), `<g>`
- **Orientation:** `horizontal` (root left, leaves right) / `vertical` (root top, leaves bottom).
- **Variants / modes:**
  - Radial tree — `layout="radial"` arranges nodes in polar coordinates (root at center, leaves on the outer ring).
  - Dendrogram — `mode="dendrogram"`; see Dendrogram entry below.
- **Phase:** P4
- **Notes:** This chart also appears in `08-flow-process.md` (where it is described as a flow/process topology). Both files reference the same `tree` renderer in `charts/core/renderers/tree.js`. Layout uses a Reingold-Tilford (tidy tree) algorithm. Edge style is configurable via `edge-style="curve|elbow"`. Compare with Org Chart (`tree` with `mode="org"`) and Dendrogram entries in this file.

---

### Treemap  *(squarified treemap, tiled treemap)*

- **Renderer / `type`:** `hierlayout` — **Primary renderer**
- **Controller:** `<mj-chart type="hierlayout" layout="treemap" ...>`
- **Purpose:** Represent nested part-to-whole data as a space-filling arrangement of proportionally-sized rectangles, one per leaf node.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Hierarchical family; `root.value` is the aggregate and `children[].value` drive tile sizes:
  ```json
  {
    "meta": { "title": "Budget Allocation" },
    "root": {
      "name": "Total",
      "value": 1000,
      "children": [
        {
          "name": "Engineering",
          "value": 450,
          "children": [
            { "name": "Salaries",   "value": 350, "children": [] },
            { "name": "Tools",      "value": 100, "children": [] }
          ]
        },
        { "name": "Marketing", "value": 300, "children": [] },
        { "name": "Operations","value": 250, "children": [] }
      ]
    }
  }
  ```
- **SVG primitives:** `<rect>` (tiles), `<text>` (node name and value labels clipped to tile bounds), `<g>` (per depth level), `<clipPath>` (label clipping inside tile)
- **Orientation:** `n/a` — squarified layout fills the available rectangle without a fixed axis.
- **Variants / modes:**
  - Icicle chart — `layout="icicle"`; same `hierlayout` renderer. See Icicle entry.
  - Sunburst chart — `layout="sunburst"`; same `hierlayout` renderer. See Sunburst entry.
  - Circle packing — `layout="pack"`; same `hierlayout` renderer. See Circle Packing entry.
- **Phase:** P2
- **Notes:** Shares the `hierlayout` renderer with Icicle, Sunburst, and Circle Packing — all four differ only in how hierarchy levels are mapped to SVG primitives and coordinate systems. The renderer dispatches on `layout`. Squarified treemap algorithm (Bruls et al.) minimises tile aspect ratios. Depth-based coloring uses the categorical color ramp; leaf value label is suppressed if the tile is narrower than a threshold (configurable via design token `--mj-chart-label-min-width`).

---

### Sunburst Chart  *(radial treemap, multilevel pie)*

- **Renderer / `type`:** `hierlayout` — **Variant of `hierlayout`**
- **Controller:** `<mj-chart type="hierlayout" layout="sunburst" ...>`
- **Purpose:** Display a radial hierarchy where each ring represents a depth level and arc widths are proportional to value, revealing both structure and proportion.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Same hierarchical `root` / `children` shape as Treemap.
  ```json
  {
    "meta": { "title": "Disk Usage" },
    "root": {
      "name": "/",
      "value": 500,
      "children": [
        {
          "name": "home",
          "value": 300,
          "children": [
            { "name": "documents", "value": 180, "children": [] },
            { "name": "downloads", "value": 120, "children": [] }
          ]
        },
        { "name": "usr", "value": 200, "children": [] }
      ]
    }
  }
  ```
- **SVG primitives:** `<path>` (annular arc segments per node, computed with arc commands), `<text>` (rotated or horizontal labels), `<g>` (per depth ring)
- **Orientation:** `n/a` — radial layout; orientation attribute is ignored.
- **Variants / modes:** See Treemap entry for the full list of `hierlayout` modes.
- **Phase:** P4
- **Notes:** Arc angles computed by partitioning `[0, 2π]` proportionally to node value within each ring. Uses `linear` scale for angle, `band` scale for ring radii. Clicking an arc zooms to that subtree (re-partitions the full angle range to the selected node's descendants). Breadcrumb trail annotation supported via `mj-chart-annotation`. Compare with Icicle for the rectangular equivalent.

---

### Icicle Chart  *(partition chart, flame graph inverted)*

- **Renderer / `type`:** `hierlayout` — **Variant of `hierlayout`**
- **Controller:** `<mj-chart type="hierlayout" layout="icicle" ...>`
- **Purpose:** Show a rectangular hierarchical partition where depth is mapped to one axis and breadth (proportional to value) to the other — the rectangular counterpart of Sunburst.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Same hierarchical `root` / `children` shape as Treemap.
  ```json
  {
    "meta": { "title": "Call Stack" },
    "root": {
      "name": "main",
      "value": 100,
      "children": [
        {
          "name": "render",
          "value": 60,
          "children": [
            { "name": "draw",    "value": 40, "children": [] },
            { "name": "layout",  "value": 20, "children": [] }
          ]
        },
        { "name": "parse", "value": 40, "children": [] }
      ]
    }
  }
  ```
- **SVG primitives:** `<rect>` (one per node; width proportional to value, height equal per depth level), `<text>` (label clipped within rect), `<g>` (per depth level), `<clipPath>`
- **Orientation:** `vertical` (root at top, children grow downward, default) / `horizontal` (root at left, children grow rightward — flame graph style).
- **Variants / modes:** See Treemap entry for the full list of `hierlayout` modes.
- **Phase:** P4
- **Notes:** The `hierlayout` renderer in `icicle` mode partitions the plot width/height proportionally to node value, then steps down one band per depth level. `linear` scale maps cumulative value to pixel offset; `band` scale maps depth to band height/width. Effectively identical to Sunburst but in Cartesian space. `orientation="horizontal"` produces a flame graph.

---

### Dendrogram  *(cluster tree, hierarchical clustering tree)*

- **Renderer / `type`:** `tree` — **Variant of `tree`**
- **Controller:** `<mj-chart type="tree" mode="dendrogram" ...>`
- **Purpose:** Display the results of hierarchical clustering, emphasising the similarity distance between groups by the height at which branches merge.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (distance/height axis), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Hierarchical family; internal nodes carry a `distance` or `height` value representing the merge distance; leaf nodes represent observations:
  ```json
  {
    "meta": { "title": "Gene Expression Clusters" },
    "root": {
      "name": "root",
      "value": 1.0,
      "children": [
        {
          "name": "cluster-A",
          "value": 0.6,
          "children": [
            { "name": "Gene1", "value": 0.0, "children": [] },
            { "name": "Gene2", "value": 0.0, "children": [] }
          ]
        },
        {
          "name": "cluster-B",
          "value": 0.4,
          "children": [
            { "name": "Gene3", "value": 0.0, "children": [] }
          ]
        }
      ]
    }
  }
  ```
- **SVG primitives:** `<line>` or `<path>` (stepped connectors; branch height encodes merge distance), `<circle>` (leaf nodes, optional), `<text>` (leaf labels), `<g>`
- **Orientation:** `horizontal` (leaves at left, root at right, distance axis horizontal, default) / `vertical` (leaves at top, root at bottom — cladogram style).
- **Variants / modes:** None beyond the `tree` primary.
- **Phase:** P4
- **Notes:** Reuses the `tree` renderer layout engine; `mode="dendrogram"` replaces tidy-tree x-position assignment with a `linear` scale mapping node `value` (merge distance/height) to the distance axis. Connectors are elbow paths (horizontal + vertical segments). A `mj-chart-axis` with `kind="value"` renders the distance axis. Leaf spacing is equidistant (`band` scale on the leaf axis). Cross-reference: Tree Diagram entry above for the base `tree` renderer.

---

### Circle Packing Chart  *(bubble hierarchy, packed circles)*

- **Renderer / `type`:** `hierlayout` — **Variant of `hierlayout`**
- **Controller:** `<mj-chart type="hierlayout" layout="pack" ...>`
- **Purpose:** Display nested groups using circles whose areas are proportional to their values, revealing hierarchical structure through containment.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Same hierarchical `root` / `children` shape as Treemap.
  ```json
  {
    "meta": { "title": "Language Popularity" },
    "root": {
      "name": "languages",
      "value": null,
      "children": [
        {
          "name": "Web",
          "value": null,
          "children": [
            { "name": "JavaScript", "value": 320, "children": [] },
            { "name": "TypeScript", "value": 210, "children": [] }
          ]
        },
        {
          "name": "Systems",
          "value": null,
          "children": [
            { "name": "Rust", "value": 150, "children": [] },
            { "name": "C++",  "value": 180, "children": [] }
          ]
        }
      ]
    }
  }
  ```
- **SVG primitives:** `<circle>` (one per node; radius from `sqrt` scale on aggregated leaf values), `<text>` (label inside circle, suppressed when circle is too small), `<g>` (per depth level)
- **Orientation:** `n/a` — packing algorithm fills an elliptical/circular bounding region; orientation attribute is ignored.
- **Variants / modes:** See Treemap entry for the full list of `hierlayout` modes.
- **Phase:** P4
- **Notes:** Uses the `hierlayout` renderer with `layout="pack"`. Internal node `value` is computed as the sum of descendant leaf values when `null`. Radius is derived from leaf `value` via a `sqrt` scale (area proportional to value). Packing algorithm places sibling circles to minimise enclosing circle radius (Wang-Bhatt packed-circles heuristic). Depth-based stroke color distinguishes hierarchy levels; fill color uses categorical color ramp from design tokens.

---

### Org Chart  *(organisation chart, reporting hierarchy)*

- **Renderer / `type`:** `tree` — **Variant of `tree`**
- **Controller:** `<mj-chart type="tree" mode="org" ...>`
- **Purpose:** Render an organisational reporting hierarchy with styled node cards showing roles, names, and optional metadata.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`, `mj-chart-brush`
- **JSON shape:** Hierarchical family; leaf and internal nodes carry `role` and `name` fields as well as optional `avatar` (URL), `department`, and other metadata displayed in the node card:
  ```json
  {
    "meta": { "title": "Engineering Org" },
    "root": {
      "name": "Sarah Chen",
      "value": null,
      "role": "VP Engineering",
      "department": "Engineering",
      "children": [
        {
          "name": "James Park",
          "value": null,
          "role": "Engineering Manager",
          "department": "Platform",
          "children": [
            { "name": "Priya Nair",   "value": null, "role": "Senior Engineer", "department": "Platform", "children": [] },
            { "name": "Luis Torres",  "value": null, "role": "Engineer",        "department": "Platform", "children": [] }
          ]
        }
      ]
    }
  }
  ```
- **SVG primitives:** `<rect>` (node card backgrounds with rounded corners via `rx`/`ry`), `<line>` or `<path>` (elbow connectors), `<text>` (name, role, department lines within card), `<image>` (optional avatar), `<g>` (per node card)
- **Orientation:** `vertical` (root at top, reports below, default) / `horizontal` (root at left, reports to the right).
- **Variants / modes:** None beyond the `tree` primary.
- **Phase:** P4
- **Notes:** Reuses the `tree` renderer with `mode="org"`, which replaces bare circle/circle nodes with multi-line rectangular cards. Card dimensions are fixed or driven by a design token (`--mj-chart-org-card-width`, `--mj-chart-org-card-height`). The tidy-tree layout algorithm is used with additional inter-node spacing to accommodate card sizes. `mj-chart-brush` enables selection of subtrees (highlights the selected node and all its descendants). Cross-reference: Tree Diagram entry above for the base `tree` renderer.

---

### Mind Map  *(concept map, idea map)*

- **Renderer / `type`:** `tree` — **Variant of `tree`**
- **Controller:** `<mj-chart type="tree" mode="mindmap" ...>`
- **Purpose:** Display a conceptual hierarchy radiating from a central idea, with branches and sub-branches representing related topics.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:** Hierarchical family; nodes carry `name` and optionally `color` or `icon` metadata:
  ```json
  {
    "meta": { "title": "Project Planning" },
    "root": {
      "name": "Product Launch",
      "value": null,
      "children": [
        {
          "name": "Marketing",
          "value": null,
          "children": [
            { "name": "Social media", "value": null, "children": [] },
            { "name": "Press release", "value": null, "children": [] }
          ]
        },
        {
          "name": "Engineering",
          "value": null,
          "children": [
            { "name": "Feature freeze", "value": null, "children": [] },
            { "name": "QA sign-off",    "value": null, "children": [] }
          ]
        }
      ]
    }
  }
  ```
- **SVG primitives:** `<rect>` (rounded label bubbles), `<path>` (curved branch connectors, tapering toward leaves), `<text>` (node labels), `<g>` (per branch/subtree)
- **Orientation:** `n/a` — root is centered; first-level branches are distributed around the root in all directions (radial placement). Attribute is ignored.
- **Variants / modes:** None beyond the `tree` primary.
- **Phase:** P4
- **Notes:** Reuses the `tree` renderer with `mode="mindmap"`. First-level children are placed radially around the root at equal angular intervals; deeper children follow the same pattern relative to their parent, but constrained to a half-plane away from the root direction to avoid overlap. Branch color is assigned from the categorical color ramp at depth 1 and inherited by all descendants of that branch. Connector paths taper in stroke-width from root to leaf using a `linear` scale. Cross-reference: Tree Diagram entry above for the base `tree` renderer.
