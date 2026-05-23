# Scientific & Technical Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Charts in this category visualize quantitative, physical, and engineering data
that require specialized coordinate systems, derived scales, or domain-specific
drawing conventions.

---

### Contour plot  *(isoline plot, level-set plot)*
- **Renderer / `type`:** `contour` — **Primary renderer**
- **Controller:** `<mj-chart type="contour" ...>`
- **Purpose:** Represent a scalar field `z = f(x, y)` in 2-D by drawing iso-value curves (contours), making a 3-D surface readable on a flat plane.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2 (x and y, both `kind="value"`), `mj-chart-grid`, `mj-chart-legend` (color-band legend for the z scale), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Pressure field", "xLabel": "X (m)", "yLabel": "Y (m)", "zLabel": "Pa" },
    "grid": {
      "x": [0, 1, 2, 3],
      "y": [0, 1, 2, 3],
      "z": [[0.1, 0.4, 0.9], [0.2, 0.5, 1.0], [0.3, 0.6, 1.1]]
    },
    "levels": [0.2, 0.4, 0.6, 0.8, 1.0],
    "fill": true
  }
  ```
  `grid.z` is a row-major 2-D array where `z[row][col]` maps to `(x[col], y[row])`. `levels` overrides automatic level count. `fill: true` requests filled contour bands between levels.
- **SVG primitives:** `<path>` (marching-squares iso-contour paths), `<rect>` (filled bands as colored closed paths), `<text>` (contour labels), `<g>` (per-level groups), `<line>` (axis ticks).
- **Orientation:** `n/a` — x maps to horizontal, y to vertical by convention.
- **Variants / modes:**
  - `fill: false` — line-only contour (isolines without color fill).
  - `fill: true` — filled contour / heatmap-style color bands.
- **Phase:** P4
- **Notes:** The renderer implements the marching-squares algorithm to trace iso-contour `<path>` strings from the grid. Scales are `linear` for x, y, and z. The z scale maps to the categorical color ramp (or a sequential ramp from design tokens). Also cross-referenced from category 4 (Relationship & correlation) where contour density plots appear. When used as a density/hexbin overlay, the same renderer is invoked with a pre-computed kernel-density `grid` produced by `chartmodel.js`.

---

### Surface plot  *(3-D surface, wireframe, mesh plot)*
- **Renderer / `type`:** `surface` — **Primary renderer**
- **Controller:** `<mj-chart type="surface" ...>`
- **Purpose:** Show the shape of a 3-D function `z = f(x, y)` as a shaded or wireframe mesh projected onto 2-D SVG using a parallel-oblique or isometric projection.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 3 (x, y, z axes rendered as angled SVG lines), `mj-chart-legend` (z color legend), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Potential energy surface", "xLabel": "x", "yLabel": "y", "zLabel": "E (eV)" },
    "grid": {
      "x": [0, 0.5, 1.0],
      "y": [0, 0.5, 1.0],
      "z": [[0.0, 0.25, 1.0], [0.25, 0.5, 1.25], [1.0, 1.25, 2.0]]
    },
    "projection": "isometric",
    "style": "shaded"
  }
  ```
  `projection` is `"isometric"` | `"oblique"`. `style` is `"shaded"` | `"wireframe"` | `"both"`.
- **SVG primitives:** `<polygon>` (quadrilateral face patches, painter's algorithm back-to-front sort), `<path>` (wireframe grid lines), `<line>` (projected axis lines), `<text>` (axis labels), `<g>` (per-row groups).
- **Orientation:** `n/a` — 3-D axes are fixed by the projection.
- **Variants / modes:**
  - `style: "wireframe"` — mesh lines only, no fill.
  - `style: "shaded"` — filled polygon faces colored by z value.
  - `style: "both"` — shaded faces with wireframe overlay.
- **Phase:** P4
- **Notes:** Rendered entirely as a 2-D SVG projection; no WebGL. The projection transform (isometric or oblique) is computed in `svgdraw.js`. Faces are sorted by painter's algorithm (furthest-center-y first) before emitting `<polygon>` elements so nearer faces paint over farther ones. The z scale maps to the sequential color ramp from design tokens. The three projected axis legs are drawn as `<line>` elements by `mj-chart-axis` in a special `kind="projected"` mode unique to this renderer.

---

### Phase diagram  *(stability diagram, regime map, state diagram)*
- **Renderer / `type`:** `phase` — **Primary renderer**
- **Controller:** `<mj-chart type="phase" ...>`
- **Purpose:** Delineate regions (phases, states, stability regimes) in a 2-D parameter space, typically with boundary curves separating named regions.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2 (both `kind="value"`), `mj-chart-grid`, `mj-chart-legend` (region labels), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Water phase diagram", "xLabel": "Temperature (°C)", "yLabel": "Pressure (atm)" },
    "regions": [
      { "name": "Solid", "color": "#aec6e8", "path": [[0,1],[0,10],[5,10],[5,1]] },
      { "name": "Liquid", "color": "#b5d9b5", "path": [[5,1],[5,10],[100,10],[100,1]] },
      { "name": "Gas", "color": "#f7e6b0", "path": [[0,0],[200,0],[200,1],[0,1]] }
    ],
    "boundaries": [
      { "name": "Melting curve", "points": [[0,1],[5,10]], "style": "solid" },
      { "name": "Boiling curve", "points": [[100,1],[100,10]], "style": "dashed" }
    ]
  }
  ```
  `regions[].path` is an array of `[x, y]` vertices defining a closed polygon for that phase region. `boundaries[].style` is `"solid"` | `"dashed"` | `"dotted"`.
- **SVG primitives:** `<polygon>` or `<path>` (filled region areas), `<path>` (boundary curves), `<text>` (region labels, phase-transition labels), `<circle>` (triple-point or critical-point markers), `<g>` (per-region groups).
- **Orientation:** `n/a` — x and y parameter axes are fixed by convention.
- **Variants / modes:** None; boundary styles cover common sub-types.
- **Phase:** P4
- **Notes:** Regions are drawn back-to-front by array order. Boundary paths support both straight-line segments and spline curves (pass `"curve": "monotone-x"` on a boundary to enable cubic interpolation via `svgdraw.js`). Scales are `linear` or `log` independently per axis — the `scale` attribute on each `mj-chart-axis` drives this. Accessibility: each region polygon carries `aria-label` set to the region name.

---

### Vector field plot  *(quiver plot, arrow plot)*
- **Renderer / `type`:** `vectorfield` — **Primary renderer**
- **Controller:** `<mj-chart type="vectorfield" ...>`
- **Purpose:** Display the direction and magnitude of a 2-D vector field `(u, v) = F(x, y)` as a regular or irregular grid of arrows.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2 (both `kind="value"`), `mj-chart-grid`, `mj-chart-legend` (magnitude color scale), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Wind velocity field", "xLabel": "Longitude", "yLabel": "Latitude" },
    "vectors": [
      { "x": 0.0, "y": 0.0, "u": 1.2, "v": -0.5 },
      { "x": 1.0, "y": 0.0, "u": 0.8, "v":  0.3 }
    ],
    "normalize": false,
    "scale": 1.0
  }
  ```
  `u` and `v` are the x and y components of the vector. `normalize: true` draws all arrows the same length (direction only). `scale` multiplies rendered arrow length.
- **SVG primitives:** `<line>` (arrow shaft), `<polygon>` (arrowhead triangle), `<g>` (per-vector group), `<text>` (magnitude labels, optional).
- **Orientation:** `n/a` — x/y axes are fixed by the field domain.
- **Variants / modes:**
  - `normalize: true` — unit-length arrows (direction-only quiver plot).
  - Color-mapped magnitude — arrows colored by `sqrt(u²+v²)` via the `sqrt` scale.
- **Phase:** P4
- **Notes:** Arrow length in pixels = `sqrt(u²+v²) * scale * cellSize`, clamped to avoid overlap. The `sqrt` scale from `scales.js` maps magnitude to the color ramp and optionally to arrow width. Arrowhead size is fixed in design tokens (`--mj-chart-arrow-head-size`). For grid-sampled data `chartmodel.js` accepts a structured-grid shorthand analogous to `contour`'s `grid` object.

---

### Streamline plot  *(flow lines, particle trace, integral curves)*
- **Renderer / `type`:** `streamline` — **Primary renderer**
- **Controller:** `<mj-chart type="streamline" ...>`
- **Purpose:** Show the paths that massless particles would follow in a 2-D vector field, revealing overall flow structure (sources, sinks, vortices).
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2 (both `kind="value"`), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Fluid streamlines", "xLabel": "x", "yLabel": "y" },
    "grid": {
      "x": [0, 0.5, 1.0],
      "y": [0, 0.5, 1.0],
      "u": [[1.0, 0.8, 0.5], [0.9, 0.7, 0.4], [0.6, 0.5, 0.3]],
      "v": [[0.0, 0.1, 0.2], [0.1, 0.2, 0.3], [0.2, 0.3, 0.4]]
    },
    "seeds": [[0.0, 0.25], [0.0, 0.5], [0.0, 0.75]],
    "maxSteps": 200,
    "stepSize": 0.01
  }
  ```
  `seeds` is a list of `[x, y]` starting points. The renderer integrates the vector field from each seed using RK4. Pre-computed streamline paths may also be supplied directly as `lines: [[[x,y],…],…]`.
- **SVG primitives:** `<path>` (one open path per streamline, drawn with `svgdraw.js` monotone spline), `<polygon>` (direction arrow tick marks along each path), `<g>` (per-line group).
- **Orientation:** `n/a`.
- **Variants / modes:**
  - Color-mapped speed — path stroke colored by local `sqrt(u²+v²)`.
  - Pre-computed paths — skip integration, render supplied `lines` directly.
- **Phase:** P4
- **Notes:** The RK4 integrator runs in `chartmodel.js` at model-build time; the renderer receives ready-to-draw polylines. Bilinear interpolation of the `(u, v)` grid is done inside the integrator. Integration stops at `maxSteps`, on leaving the domain, or when speed drops below a tolerance. Streamlines share the vector-field grid format; when both `type="streamline"` and a quiver overlay are desired, a second `mj-chart-plot` referencing the same controller with `type="vectorfield"` can be layered.

---

### Spectrogram  *(time-frequency plot, short-time Fourier transform display)*
- **Renderer / `type`:** `spectrogram` — **Primary renderer**
- **Controller:** `<mj-chart type="spectrogram" ...>`
- **Purpose:** Display signal energy as a function of both time (x) and frequency (y), using color intensity to encode amplitude or power.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2 (`kind="time"` on x, `kind="value"` on y for frequency), `mj-chart-legend` (color/amplitude scale), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Audio spectrogram", "xLabel": "Time (s)", "yLabel": "Frequency (Hz)" },
    "timeAxis": { "start": 0.0, "end": 5.0, "bins": 256 },
    "freqAxis": { "start": 0.0, "end": 8000.0, "bins": 128 },
    "power": [[0.01, 0.05, 0.12], [0.02, 0.08, 0.20]],
    "scale": "log",
    "colormap": "sequential"
  }
  ```
  `power` is a 2-D array `[freqBin][timeBin]` of power values. `scale: "log"` applies a logarithmic color mapping (dB scale). `colormap` selects the design-token sequential ramp.
- **SVG primitives:** `<rect>` (one per time-frequency cell, fill color from color scale; cells are merged into fewer wider rects when adjacent cells share the same quantized color for performance), `<text>` (axis labels), `<g>` (row groups).
- **Orientation:** `n/a` — time on x, frequency on y by convention.
- **Variants / modes:**
  - `scale: "linear"` — linear power mapping.
  - `scale: "log"` — dB (logarithmic) color mapping via the `log` scale in `scales.js`.
- **Phase:** P4
- **Notes:** For large spectrograms the renderer quantizes colors to a palette of 64 shades and merges adjacent same-color cells into a single wider `<rect>` to bound SVG element count. The `log` scale from `scales.js` drives the y-axis frequency when `freqAxis.logScale: true` is set. Pre-windowed FFT output is accepted directly; `chartmodel.js` does not perform the FFT itself.

---

### Polar chart  *(radar chart — circular, rose plot — single series, angle-radius plot)*
- **Renderer / `type`:** `polar` — **Primary renderer**
- **Controller:** `<mj-chart type="polar" ...>`
- **Purpose:** Plot data in a circular coordinate system where angle encodes one variable and radius encodes another — suited to circular or angular data such as directional measurements and periodic phenomena.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (radial, `kind="value"` for the r axis), `mj-chart-axis` (angular, `kind="angular"` for the θ axis — ring of labels), `mj-chart-grid` (concentric-ring and spoke gridlines), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Signal amplitude vs angle", "rLabel": "Amplitude", "thetaLabel": "Angle (°)" },
    "series": [
      {
        "name": "Antenna pattern",
        "points": [
          { "theta": 0,   "r": 1.0 },
          { "theta": 45,  "r": 0.7 },
          { "theta": 90,  "r": 0.3 },
          { "theta": 135, "r": 0.1 },
          { "theta": 180, "r": 0.05 }
        ]
      }
    ],
    "thetaUnit": "degrees",
    "rMin": 0
  }
  ```
  `theta` values in degrees or radians (controlled by `thetaUnit`). `rMin` sets inner radius for the r scale (useful to show near-zero variation).
- **SVG primitives:** `<path>` (closed or open polar curve, built with `svgdraw.js` polar path builder), `<circle>` (concentric grid rings), `<line>` (spoke gridlines from center), `<text>` (angular labels around the ring, radial tick values), `<g>` (per-series groups).
- **Orientation:** `n/a` — circular.
- **Variants / modes:**
  - Line mode (default) — open polar path connecting data points.
  - Area mode (`fill: true`) — closed filled polar region.
  - Wind rose / Nightingale — use `wind-rose` entry below (same renderer, petal layout).
- **Phase:** P4
- **Notes:** The θ scale is always circular; the r scale is `linear` by default and can be `log`. Angular labels are placed at the perimeter using `svgdraw.js` polar text positioning (labels rotate to stay readable). Multiple series are drawn as overlaid polar paths. The `polar` renderer is shared by wind-rose and Nightingale-rose (see those entries).

---

### Wind rose  *(directional rose, compass rose, wind direction frequency chart)*
- **Renderer / `type`:** `wind-rose` — **Variant of `polar`**
- **Controller:** `<mj-chart type="wind-rose" ...>`
- **Purpose:** Show the frequency and intensity distribution of wind (or any directional measurement) across compass directions using variable-length petals or wedge bars.
- **Decomposition:** Same as `polar`: `mj-chart-plot`, `mj-chart-axis` (radial and angular), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Wind rose — Station A", "rLabel": "Frequency (%)", "thetaLabel": "Direction" },
    "directions": ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"],
    "series": [
      { "name": "0–5 m/s",  "values": [2,1,3,2,1,1,2,3,4,3,2,1,2,3,4,2] },
      { "name": "5–10 m/s", "values": [1,2,4,3,2,1,1,2,3,4,5,3,2,1,2,3] }
    ]
  }
  ```
  `directions` maps to equally-spaced angular bins. `series` are stacked radially (wind speed bins). The petal width equals the bin's angular span; the petal length equals the stacked sum of the series values for that direction.
- **SVG primitives:** `<path>` (wedge/petal shapes — one closed `arc` path per direction per series), `<circle>` (concentric frequency grid rings), `<line>` (compass-direction spokes), `<text>` (direction labels, frequency tick values), `<g>` (per-direction groups).
- **Orientation:** `n/a` — circular; north is always at top (0° = up).
- **Variants / modes:**
  - Filled wedges (default) — opaque stacked petals per direction.
  - Line rose — just the perimeter of the total-frequency polygon (single series, no fill).
- **Phase:** P4
- **Notes:** Implemented as the `polar` renderer in `petal` layout mode, triggered by `type="wind-rose"`. The controller internally re-maps the `directions` + `values` structure to `theta/r` point arrays. The `band` scale is used for angular bin width. North-up convention is enforced by setting θ-origin to −90° in the SVG arc calculation.

---

### Nightingale rose chart  *(coxcomb chart, polar area chart)*
- **Renderer / `type`:** `nightingale` — **Variant of `polar`**
- **Controller:** `<mj-chart type="nightingale" ...>`
- **Purpose:** Display part-to-whole proportions across categorical sectors arranged in a circle, where sector area (radius) encodes value — as invented by Florence Nightingale.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (radial value axis), `mj-chart-grid` (concentric rings), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Causes of mortality", "rLabel": "Deaths" },
    "categories": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
    "series": [
      { "name": "Preventable disease", "values": [830,422,361,333,220,145,128,133,139,159,182,257] },
      { "name": "Wounds",              "values": [32,19,17,14,12,12,14,15,12,13,15,20] },
      { "name": "Other",               "values": [72,36,29,25,22,22,24,25,23,24,26,31] }
    ]
  }
  ```
  Each category maps to an equal-angle sector. Series within a sector are stacked radially. Sector radius is proportional to value (area encoding requires `r = sqrt(value)` which the renderer applies automatically via the `sqrt` scale).
- **SVG primitives:** `<path>` (arc-wedge per category per series), `<circle>` (concentric grid rings), `<line>` (sector-boundary spokes), `<text>` (category and value labels), `<g>` (per-sector groups).
- **Orientation:** `n/a`.
- **Variants / modes:** None beyond standard Nightingale area encoding.
- **Phase:** P4
- **Notes:** Shares the `polar` renderer's angular-layout engine. The `sqrt` scale from `scales.js` maps value to radius so that area (not radius) is proportional to value, matching Nightingale's original intent. Sectors use the `band` scale for equal angular widths. Distinguished from wind-rose by area (not length) encoding and by the categorical (not directional) nature of the sectors.

---

### Ternary plot  *(ternary diagram, trilinear plot, simplex plot)*
- **Renderer / `type`:** `ternary` — **Primary renderer**
- **Controller:** `<mj-chart type="ternary" ...>`
- **Purpose:** Display three-component compositional data (where components sum to 100%) inside an equilateral triangle, with each vertex representing 100% of one component.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 3 (one per edge, `kind="ternary-axis"`), `mj-chart-grid` (ternary gridlines parallel to each side), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Soil texture triangle", "aLabel": "Sand (%)", "bLabel": "Silt (%)", "cLabel": "Clay (%)" },
    "series": [
      {
        "name": "Sample set A",
        "points": [
          { "a": 60, "b": 30, "c": 10 },
          { "a": 50, "b": 35, "c": 15 },
          { "a": 40, "b": 40, "c": 20 }
        ]
      }
    ],
    "regions": [
      { "name": "Sandy loam", "vertices": [{"a":80,"b":15,"c":5},{"a":70,"b":20,"c":10},{"a":60,"b":25,"c":15}], "color": "#f0d080" }
    ]
  }
  ```
  Each point has three compositional components `a`, `b`, `c` that must sum to 100. `regions` defines named zones within the triangle as closed ternary polygons.
- **SVG primitives:** `<polygon>` (outer triangle frame, region zones), `<circle>` (data point markers), `<path>` (connecting lines for series paths), `<line>` (ternary axis ticks, gridlines parallel to triangle sides), `<text>` (axis labels at vertices, tick percentage labels), `<g>` (per-series groups).
- **Orientation:** `n/a` — the equilateral triangle is fixed.
- **Variants / modes:**
  - Scatter mode (default) — individual point markers.
  - Path mode — `connect: true` draws lines between points in series order.
  - Region overlay — named zones drawn as filled polygons from the `regions` array.
- **Phase:** P4
- **Notes:** The ternary-to-Cartesian transform (`x = b + c/2`, `y = c * sqrt(3)/2`, normalized to the triangle height) lives in `svgdraw.js`. The three `mj-chart-axis` elements use `kind="ternary-axis"` and render tick marks and labels along the three edges. Gridlines are lines parallel to each side, spaced at equal-percentage intervals. Region polygons are converted to SVG pixel coordinates the same way as data points.

---

### Log-log plot  *(power-law plot, log-log graph)*
- **Renderer / `type`:** `line` — **Variant of `line`** (scale-mode variant)
- **Controller:** `<mj-chart type="line" scale-x="log" scale-y="log" ...>`
- **Purpose:** Reveal power-law relationships `y = ax^b` as straight lines by plotting both axes on logarithmic scales; the slope equals the exponent `b`.
- **Decomposition:** Identical to `line`: `mj-chart-plot`, `mj-chart-axis` × 2 (both with `scale="log"`), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Particle size distribution", "xLabel": "Diameter (μm)", "yLabel": "Frequency" },
    "series": [
      {
        "name": "Sample 1",
        "points": [
          { "x": 0.1, "y": 1000 },
          { "x": 1.0, "y": 100 },
          { "x": 10.0, "y": 10 }
        ]
      }
    ]
  }
  ```
  Standard XY points envelope; the `scale-x="log"` and `scale-y="log"` attributes on the controller activate the `log` scale from `scales.js` for both axes.
- **SVG primitives:** Same as `line` renderer — `<path>` (line series), `<circle>` (point markers), `<line>` (axis ticks), `<text>` (tick labels formatted as powers of 10), `<g>`.
- **Orientation:** `vertical` (x horizontal, y vertical) only; swapping to `horizontal` on log-log is rarely meaningful.
- **Variants / modes:**
  - `scale-x="log" scale-y="linear"` — semi-log X (see Semi-log plot).
  - `scale-x="linear" scale-y="log"` — semi-log Y (see Semi-log plot).
- **Phase:** P4 (scale support added to `line` renderer; the `log` scale is in `scales.js` from Phase 0)
- **Notes:** No new renderer; the `log` scale from `scales.js` is simply set on the axis. Tick labels are formatted as `10^n` or as the actual value (configurable via `tickFormat` on the axis). Zero and negative values are excluded from the domain before scale construction; `chartmodel.js` warns via `mj-chart-error` if any data point has `x ≤ 0` or `y ≤ 0`.

---

### Semi-log plot  *(log-linear plot, exponential plot, log scale chart)*
- **Renderer / `type`:** `line` — **Variant of `line`** (scale-mode variant)
- **Controller:** `<mj-chart type="line" scale-y="log" ...>` (or `scale-x="log"` for semi-log X)
- **Purpose:** Expose exponential growth or decay as a straight line by applying a logarithmic scale to one axis while keeping the other linear.
- **Decomposition:** Identical to `line`: `mj-chart-plot`, `mj-chart-axis` × 2 (one with `scale="log"`, one with `scale="linear"`), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Bacterial growth", "xLabel": "Time (h)", "yLabel": "Cell count" },
    "series": [
      {
        "name": "E. coli",
        "points": [
          { "x": 0, "y": 100 },
          { "x": 1, "y": 320 },
          { "x": 2, "y": 1024 },
          { "x": 3, "y": 3277 }
        ]
      }
    ]
  }
  ```
  Same XY envelope as `line`. The `scale-y="log"` attribute activates the `log` scale on the y axis.
- **SVG primitives:** Same as `line`.
- **Orientation:** `vertical` | `horizontal` (supported by the `line` renderer).
- **Variants / modes:**
  - Semi-log Y (`scale-y="log"`) — exponential y data; linear x (time, frequency).
  - Semi-log X (`scale-x="log"`) — logarithmic x data (e.g. frequency response on log-frequency axis).
- **Phase:** P4 (scale support; see Log-log note)
- **Notes:** Same implementation path as log-log. The `scatter` renderer also supports `scale-x="log"` / `scale-y="log"` by the same attribute mechanism, giving log-scale scatter plots without a separate renderer.

---

### Nyquist plot  *(Nyquist diagram, polar frequency response plot)*
- **Renderer / `type`:** `nyquist` — **Primary renderer**
- **Controller:** `<mj-chart type="nyquist" ...>`
- **Purpose:** Display the frequency response of a linear system in the complex plane by plotting `Re(H(jω))` vs `Im(H(jω))` as frequency `ω` sweeps from 0 to ∞, used to assess gain and phase margin.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2 (`kind="value"` — Re on x, Im on y), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Open-loop Nyquist", "xLabel": "Re(H)", "yLabel": "Im(H)" },
    "series": [
      {
        "name": "G(s)H(s)",
        "points": [
          { "omega": 0.1, "re":  0.98, "im": -0.20 },
          { "omega": 1.0, "re":  0.50, "im": -0.86 },
          { "omega": 10,  "re": -0.10, "im": -0.10 }
        ],
        "mirror": true
      }
    ],
    "criticalPoint": { "re": -1, "im": 0 }
  }
  ```
  `omega` is stored for tooltip display and is not plotted directly. `mirror: true` instructs the renderer to also draw the complex conjugate (negative-frequency) locus as a dashed path. `criticalPoint` places the `−1 + 0j` marker.
- **SVG primitives:** `<path>` (Nyquist locus curve, dashed mirror), `<circle>` (critical point marker at −1+0j, unit-circle guide if requested), `<line>` (Re and Im axis lines through origin), `<text>` (axis labels, frequency annotations on the curve), `<g>`.
- **Orientation:** `n/a` — complex plane is fixed.
- **Variants / modes:**
  - `mirror: true` — shows both positive- and negative-frequency loci.
  - Unit-circle overlay — `showUnitCircle: true` adds a `<circle r="…">` at the origin.
- **Phase:** P4
- **Notes:** The `scatter` renderer's XY curve drawing is reused for the locus path; `nyquist` is a thin wrapper that pre-processes `(re, im)` as `(x, y)` and adds the domain-specific annotations (critical point, encirclement direction arrows). Encirclement arrows (small `<polygon>` arrowheads placed along the curve) indicate the direction of increasing ω. Both axes use `linear` scale centered at 0; the controller auto-ranges to include the critical point.

---

### Bode plot  *(Bode diagram, frequency response chart)*
- **Renderer / `type`:** `bode` — **Primary renderer**
- **Controller:** `<mj-chart type="bode" ...>`
- **Purpose:** Display a linear system's frequency response as two vertically-stacked sub-charts: magnitude (dB) vs log-frequency and phase (degrees) vs log-frequency.
- **Decomposition:** Two linked `mj-chart-plot` elements (magnitude and phase panels) sharing one `mj-chart` controller; `mj-chart-axis` × 3 (shared log-frequency x axis, dB y axis, degrees y axis); `mj-chart-grid` (shared vertical log-frequency gridlines); `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Second-order low-pass filter", "xLabel": "Frequency (rad/s)" },
    "series": [
      {
        "name": "G(s)",
        "points": [
          { "omega": 0.1, "magnitude_db": -0.04, "phase_deg": -1.1 },
          { "omega": 1.0, "magnitude_db": -3.01, "phase_deg": -45.0 },
          { "omega": 10,  "magnitude_db": -20.0, "phase_deg": -84.3 }
        ]
      }
    ],
    "asymptotes": true
  }
  ```
  `magnitude_db` and `phase_deg` are the pre-computed Bode values. `asymptotes: true` overlays straight-line asymptote segments (dashed) for each series.
- **SVG primitives:** `<path>` (magnitude curve, phase curve, asymptote dashes), `<line>` (0 dB reference line, −180° reference line, axis ticks), `<text>` (frequency tick labels as powers of 10, dB and degree labels), `<rect>` (panel background bands if styled), `<g>` (magnitude-panel group, phase-panel group).
- **Orientation:** `n/a` — two stacked panels with shared log-frequency x axis.
- **Variants / modes:**
  - `asymptotes: true` — piecewise-linear Bode asymptotes overlaid.
  - Gain/phase margin markers — `<circle>` at the gain crossover and phase crossover frequencies.
- **Phase:** P4
- **Notes:** The Bode renderer manages two distinct SVG drawing areas within one `mj-chart-plot` (each panel is a `<g>` with its own y-scale). The x axis uses the `log` scale from `scales.js`, with tick labels formatted as powers of 10. Gain and phase margin can be annotated automatically when `showMargins: true` is set; the renderer computes the crossover frequencies from the data and places `mj-chart-annotation` markers. The two panels share the x-axis pixel range — the plot's reported box width drives both y-scales consistently.

---

### Smith chart  *(normalized impedance chart, reflection-coefficient chart)*
- **Renderer / `type`:** `smith` — **Primary renderer**
- **Controller:** `<mj-chart type="smith" ...>`
- **Purpose:** Plot complex impedances normalized to a reference impedance (typically 50 Ω) in the reflection-coefficient plane, used for RF matching network and transmission-line analysis.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-legend`, `mj-chart-data-table`, `mj-chart-annotation`. (No standard `mj-chart-axis`; the Smith chart's grid is its own specialized circular coordinate system.)
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Amplifier input impedance", "z0": 50 },
    "series": [
      {
        "name": "S11 locus",
        "points": [
          { "freq_hz": 1e9, "r": 0.5, "x":  0.5 },
          { "freq_hz": 2e9, "r": 1.0, "x":  0.0 },
          { "freq_hz": 3e9, "r": 0.5, "x": -0.5 }
        ]
      }
    ],
    "grid": { "rLines": [0, 0.2, 0.5, 1, 2, 5], "xLines": [0, ±0.2, ±0.5, ±1, ±2] }
  }
  ```
  `r` and `x` are the normalized resistance and reactance. The renderer converts `(r, x)` to reflection-coefficient `Γ = (Z/Z0 − 1)/(Z/Z0 + 1)` and maps `Γ` to pixel coordinates within the unit circle.
- **SVG primitives:** `<circle>` (outer unit-circle boundary, constant-resistance circles, constant-reactance arc circles), `<path>` (curved reactance arc segments clipped to the unit disk, data series locus), `<line>` (center crosshair, real-axis line), `<text>` (impedance labels on grid circles), `<g>` (grid group, series group).
- **Orientation:** `n/a` — the Smith chart is a fixed circular projection.
- **Variants / modes:**
  - Admittance (Y) chart — rotated 180° within the unit circle, toggled via `mode: "admittance"`.
  - Combined Z+Y overlay — `mode: "both"` overlays the admittance chart in a contrasting color.
- **Phase:** P4
- **Notes:** The constant-resistance circles `(center = (r/(r+1), 0), radius = 1/(r+1))` and constant-reactance arcs `(center = (1, 1/x), radius = 1/|x|)` are computed analytically in `svgdraw.js` and drawn as SVG `<circle>` elements (resistance circles are complete circles; reactance arcs are clipped by the unit-circle boundary using `<clipPath>`). There are no standard linear scales; all coordinate transforms are custom Smith-chart geometry. This is one of the most geometrically complex renderers in the library.

---

### Phylogenetic tree  *(cladogram, dendrogram — evolutionary, evolutionary tree)*
- **Renderer / `type`:** `phylo` — **Primary renderer**
- **Controller:** `<mj-chart type="phylo" ...>`
- **Purpose:** Show evolutionary relationships among organisms (or entities) as a branching tree where branch lengths encode evolutionary distance or time.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (optional time/distance axis, `kind="value"`, drawn along the root-to-tip dimension), `mj-chart-legend` (clade color coding), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Mammal phylogeny", "branchLengthLabel": "Mya" },
    "root": {
      "name": "Amniota",
      "length": 0,
      "children": [
        {
          "name": "Mammalia",
          "length": 50,
          "children": [
            { "name": "Primates", "length": 30, "children": [
                { "name": "Homo sapiens", "length": 6 },
                { "name": "Pan troglodytes", "length": 6 }
            ]},
            { "name": "Rodentia", "length": 30, "children": [
                { "name": "Mus musculus", "length": 25 }
            ]}
          ]
        }
      ]
    },
    "layout": "rectangular",
    "branchLengths": true
  }
  ```
  Uses the hierarchical data envelope (`root` with recursive `children`). `length` is the branch length (distance from parent). `layout` is `"rectangular"` | `"circular"` | `"diagonal"`. `branchLengths: false` produces a cladogram (equal branch lengths).
- **SVG primitives:** `<line>` (horizontal branch segments, vertical connector lines between sibling branches in rectangular layout), `<path>` (diagonal or curved branches in diagonal/circular layout), `<circle>` (internal node markers, leaf tip markers), `<text>` (leaf taxon labels, node labels, branch-length annotations), `<g>` (per-clade groups).
- **Orientation:** `vertical` (root at top, tips at bottom) | `horizontal` (root at left, tips at right).
- **Variants / modes:**
  - `layout: "rectangular"` — right-angle branches (standard phylogram/cladogram).
  - `layout: "diagonal"` — angled straight branches.
  - `layout: "circular"` — radial tree (root at center, tips around the circumference); orientation is `n/a` in this sub-mode.
  - `branchLengths: false` — equal-length branches (cladogram, topology only).
- **Phase:** P4
- **Notes:** Shares the hierarchical layout engine from the dendrogram renderer (category 9, hierarchical charts) with a `kind="phylo"` parameter that enables branch-length scaling along the root-to-tip axis. The y (vertical layout) or x (horizontal layout) position of each leaf is computed by the same even-spacing algorithm used in dendrogram. The root-to-tip axis uses a `linear` scale when `branchLengths: true`; the scale is omitted for cladograms. The circular layout reuses the `polar` renderer's radial positioning utilities from `svgdraw.js`. Branch-support values (bootstrap or posterior probability) may be added as `{ "support": 95 }` on internal nodes and are rendered as small `<text>` labels near the node `<circle>`.
