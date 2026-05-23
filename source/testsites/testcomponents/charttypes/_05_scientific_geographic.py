"""
    05_scientific_geographic.py

    ChartTypeDoc catalog entries for the Scientific and Geographic chart families.

    Scientific types come from:
        polar.js        -> polar, wind-rose, nightingale, coxcomb
        contour.js      -> contour, surface
        vectorfield.js  -> vector-field, streamline
        spectrogram.js  -> spectrogram
        ternary.js      -> ternary
        phase.js        -> phase-diagram
        freqresponse.js -> nyquist, bode
        smith.js        -> smith
        loglog.js       -> log-log, semi-log

    Geographic types come from:
        geomap.js       -> choropleth, symbol-map, bubble-map,
                           proportional-symbol-map, hex-map, tile-grid-map
        flowmap.js      -> flow-map, route-map, geo-heatmap, isoline, cartogram
"""

from testcomponents.charttypes.charttypedoc import ChartTypeDoc


CHART_TYPES = [

    # ── Scientific: polar ──────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="polar",
        title="Polar",
        category="scientific",
        summary="Continuous line/area chart plotted on a circular radial grid.",
        description=(
            "Plots (theta, r) data points on a polar grid.  "
            "Each series supplies a list of {theta, r} objects where theta is "
            "in degrees (default) or radians.  Multiple series are supported."
        ),
        example=(
            '<mj-chart type="polar" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "thetaUnit": "degrees",\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Signal A",\n'
            '        "points": [\n'
            '          {"theta":   0, "r": 3.0},\n'
            '          {"theta":  45, "r": 5.5},\n'
            '          {"theta":  90, "r": 7.2},\n'
            '          {"theta": 135, "r": 4.8},\n'
            '          {"theta": 180, "r": 2.1},\n'
            '          {"theta": 225, "r": 3.7},\n'
            '          {"theta": 270, "r": 6.3},\n'
            '          {"theta": 315, "r": 4.0}\n'
            '        ]\n'
            '      },\n'
            '      {\n'
            '        "name": "Signal B",\n'
            '        "points": [\n'
            '          {"theta":   0, "r": 6.0},\n'
            '          {"theta":  45, "r": 3.2},\n'
            '          {"theta":  90, "r": 5.0},\n'
            '          {"theta": 135, "r": 7.8},\n'
            '          {"theta": 180, "r": 5.5},\n'
            '          {"theta": 225, "r": 2.0},\n'
            '          {"theta": 270, "r": 4.4},\n'
            '          {"theta": 315, "r": 6.9}\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: wind-rose ──────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="wind-rose",
        title="Wind Rose",
        category="scientific",
        summary="Directional frequency chart with stacked wedge petals.",
        description=(
            "Displays directional data (e.g. wind speed frequency by compass "
            "direction) as stacked wedge petals radiating from a centre.  "
            "Supply directions[] (compass labels) and series[].values[] aligned "
            "to those directions."
        ),
        example=(
            '<mj-chart type="wind-rose" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "directions": ["N","NE","E","SE","S","SW","W","NW"],\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "0-3 m/s",\n'
            '        "values": [8, 4, 6, 3, 5, 7, 9, 6]\n'
            '      },\n'
            '      {\n'
            '        "name": "3-6 m/s",\n'
            '        "values": [12, 7, 5, 4, 6, 10, 14, 11]\n'
            '      },\n'
            '      {\n'
            '        "name": "6+ m/s",\n'
            '        "values": [5, 2, 1, 1, 2, 4, 8, 6]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: nightingale ────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="nightingale",
        title="Nightingale Rose",
        category="scientific",
        summary="Polar area (coxcomb) chart where sector area encodes value.",
        description=(
            "Each category occupies an equal angular slice; area (via sqrt scale) "
            "encodes value.  Supply categories[] and series[].values[] aligned to "
            "those categories.  The 'coxcomb' type is an alias."
        ),
        example=(
            '<mj-chart type="nightingale" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "categories": ["Jan","Feb","Mar","Apr","May","Jun",\n'
            '                   "Jul","Aug","Sep","Oct","Nov","Dec"],\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Wounds",\n'
            '        "values": [830,740,830,860,830,800,900,910,800,760,720,690]\n'
            '      },\n'
            '      {\n'
            '        "name": "Disease",\n'
            '        "values": [460,210,160,150,140,130,120,135,160,180,220,350]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: coxcomb ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="coxcomb",
        title="Coxcomb",
        category="scientific",
        summary="Alias for nightingale rose — polar area chart.",
        description=(
            "Identical to the nightingale renderer.  Accepts the same "
            "categories[] / series[].values[] data shape."
        ),
        example=(
            '<mj-chart type="coxcomb" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "categories": ["Q1","Q2","Q3","Q4"],\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Revenue",\n'
            '        "values": [4200, 5800, 7100, 6300]\n'
            '      },\n'
            '      {\n'
            '        "name": "Cost",\n'
            '        "values": [2100, 2800, 3200, 2900]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: contour ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="contour",
        title="Contour",
        category="scientific",
        summary="Iso-value contour lines or filled contour bands over a 2-D grid.",
        description=(
            "Requires grid.x (x-axis values), grid.y (y-axis values), and "
            "grid.z (2-D array [rows][cols] of scalar values).  Optional "
            "levels[] overrides the auto-computed isoline set.  Set fill:true "
            "for filled contour bands."
        ),
        example=(
            '<mj-chart type="contour" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "fill": true,\n'
            '    "grid": {\n'
            '      "x": [-2, -1, 0, 1, 2],\n'
            '      "y": [-2, -1, 0, 1, 2],\n'
            '      "z": [\n'
            '        [8.00, 5.00, 4.00, 5.00, 8.00],\n'
            '        [5.00, 2.00, 1.00, 2.00, 5.00],\n'
            '        [4.00, 1.00, 0.00, 1.00, 4.00],\n'
            '        [5.00, 2.00, 1.00, 2.00, 5.00],\n'
            '        [8.00, 5.00, 4.00, 5.00, 8.00]\n'
            '      ]\n'
            '    },\n'
            '    "meta": {"xLabel": "x", "yLabel": "y"}\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: surface ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="surface",
        title="Surface",
        category="scientific",
        summary="Shaded 2-D projection of a z=f(x,y) surface.",
        description=(
            "Uses the same grid.x / grid.y / grid.z shape as contour.  "
            "The projection attribute selects 'isometric' (default) or 'oblique'. "
            "The style attribute selects 'shaded', 'wireframe', or 'both'."
        ),
        example=(
            '<mj-chart type="surface" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "projection": "isometric",\n'
            '    "style": "shaded",\n'
            '    "grid": {\n'
            '      "x": [0, 1, 2, 3, 4],\n'
            '      "y": [0, 1, 2, 3, 4],\n'
            '      "z": [\n'
            '        [0.0, 0.5, 1.0, 0.5, 0.0],\n'
            '        [0.5, 2.0, 3.5, 2.0, 0.5],\n'
            '        [1.0, 3.5, 6.0, 3.5, 1.0],\n'
            '        [0.5, 2.0, 3.5, 2.0, 0.5],\n'
            '        [0.0, 0.5, 1.0, 0.5, 0.0]\n'
            '      ]\n'
            '    }\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: vector-field ───────────────────────────────────────────────

    ChartTypeDoc(
        type_key="vector-field",
        title="Vector Field",
        category="scientific",
        summary="Quiver plot: arrows showing direction and magnitude at grid points.",
        description=(
            "Supply vectors[] where each entry has x, y (position) and "
            "u, v (velocity/gradient components).  "
            "Set normalize:true to make all arrows the same length, "
            "or scale (number) to adjust arrow size."
        ),
        example=(
            '<mj-chart type="vector-field" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "normalize": false,\n'
            '    "scale": 1.0,\n'
            '    "vectors": [\n'
            '      {"x": 0, "y": 0, "u":  1.0, "v":  0.2},\n'
            '      {"x": 1, "y": 0, "u":  0.8, "v":  0.6},\n'
            '      {"x": 2, "y": 0, "u":  0.3, "v":  1.0},\n'
            '      {"x": 0, "y": 1, "u": -0.4, "v":  0.9},\n'
            '      {"x": 1, "y": 1, "u": -0.9, "v":  0.4},\n'
            '      {"x": 2, "y": 1, "u": -1.0, "v": -0.2},\n'
            '      {"x": 0, "y": 2, "u": -0.6, "v": -0.8},\n'
            '      {"x": 1, "y": 2, "u":  0.2, "v": -1.0},\n'
            '      {"x": 2, "y": 2, "u":  0.8, "v": -0.6}\n'
            '    ],\n'
            '    "meta": {"xLabel": "x", "yLabel": "y"}\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: streamline ─────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="streamline",
        title="Streamline",
        category="scientific",
        summary="Flow-lines traced through a 2-D vector field using RK4 integration.",
        description=(
            "Accepts either pre-computed lines[] (array of [[x,y],...] polylines) "
            "or a grid {x[], y[], u[][], v[][]} plus seeds [[x0,y0],...] from "
            "which the renderer integrates streamlines.  maxSteps and stepSize "
            "control the integrator."
        ),
        example=(
            '<mj-chart type="streamline" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "maxSteps": 300,\n'
            '    "stepSize": 0.04,\n'
            '    "grid": {\n'
            '      "x": [0.0, 0.5, 1.0, 1.5, 2.0],\n'
            '      "y": [0.0, 0.5, 1.0, 1.5, 2.0],\n'
            '      "u": [\n'
            '        [ 0.5,  0.8,  1.0,  0.8,  0.5],\n'
            '        [ 0.3,  0.6,  1.0,  0.6,  0.3],\n'
            '        [ 0.0,  0.0,  0.0,  0.0,  0.0],\n'
            '        [-0.3, -0.6, -1.0, -0.6, -0.3],\n'
            '        [-0.5, -0.8, -1.0, -0.8, -0.5]\n'
            '      ],\n'
            '      "v": [\n'
            '        [-0.5, -0.3,  0.0,  0.3,  0.5],\n'
            '        [-0.8, -0.6,  0.0,  0.6,  0.8],\n'
            '        [-1.0, -1.0,  0.0,  1.0,  1.0],\n'
            '        [-0.8, -0.6,  0.0,  0.6,  0.8],\n'
            '        [-0.5, -0.3,  0.0,  0.3,  0.5]\n'
            '      ]\n'
            '    },\n'
            '    "seeds": [\n'
            '      [0.1, 0.1], [0.1, 1.0], [0.1, 1.9],\n'
            '      [1.0, 0.1], [1.9, 0.1], [1.9, 1.9]\n'
            '    ],\n'
            '    "meta": {"xLabel": "x", "yLabel": "y"}\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: spectrogram ────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="spectrogram",
        title="Spectrogram",
        category="scientific",
        summary="Time vs. frequency intensity grid with a sequential color palette.",
        description=(
            "Requires timeAxis {start, end, bins}, freqAxis {start, end, bins}, "
            "and power (2-D array [freqBins][timeBins] of linear power values). "
            "Set scale:'log' to map power through 10*log10 before coloring."
        ),
        example=(
            '<mj-chart type="spectrogram" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "scale": "log",\n'
            '    "timeAxis": {"start": 0.0, "end": 1.0, "bins": 8},\n'
            '    "freqAxis": {"start": 0, "end": 4000, "bins": 6},\n'
            '    "power": [\n'
            '      [0.01, 0.02, 0.05, 0.10, 0.08, 0.03, 0.02, 0.01],\n'
            '      [0.05, 0.30, 0.80, 0.95, 0.70, 0.20, 0.08, 0.04],\n'
            '      [0.20, 0.75, 0.99, 0.85, 0.60, 0.40, 0.25, 0.15],\n'
            '      [0.40, 0.60, 0.80, 0.70, 0.50, 0.55, 0.60, 0.45],\n'
            '      [0.10, 0.25, 0.40, 0.35, 0.20, 0.30, 0.45, 0.35],\n'
            '      [0.02, 0.05, 0.08, 0.06, 0.04, 0.07, 0.10, 0.08]\n'
            '    ],\n'
            '    "meta": {"xLabel": "Time (s)", "yLabel": "Frequency (Hz)"}\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: ternary ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="ternary",
        title="Ternary",
        category="scientific",
        summary="Three-axis triangular composition diagram where a+b+c = 100.",
        description=(
            "Each data point has {a, b, c} values (need not sum to exactly 100; "
            "the renderer normalises them).  Supply meta.aLabel/bLabel/cLabel for "
            "vertex labels.  Optional regions[] define filled phase fields with "
            "vertices [{a,b,c}] and a color."
        ),
        example=(
            '<mj-chart type="ternary" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "meta": {\n'
            '      "aLabel": "SiO\\u2082",\n'
            '      "bLabel": "Al\\u2082O\\u2083",\n'
            '      "cLabel": "MgO"\n'
            '    },\n'
            '    "regions": [\n'
            '      {\n'
            '        "name": "Cordierite",\n'
            '        "color": "#60a5fa",\n'
            '        "vertices": [\n'
            '          {"a": 55, "b": 35, "c": 10},\n'
            '          {"a": 50, "b": 40, "c": 10},\n'
            '          {"a": 45, "b": 40, "c": 15},\n'
            '          {"a": 50, "b": 35, "c": 15}\n'
            '        ]\n'
            '      }\n'
            '    ],\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Samples",\n'
            '        "points": [\n'
            '          {"a": 52, "b": 37, "c": 11},\n'
            '          {"a": 48, "b": 39, "c": 13},\n'
            '          {"a": 60, "b": 30, "c": 10},\n'
            '          {"a": 70, "b": 20, "c": 10},\n'
            '          {"a": 40, "b": 50, "c": 10}\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: phase-diagram ──────────────────────────────────────────────

    ChartTypeDoc(
        type_key="phase-diagram",
        title="Phase Diagram",
        category="scientific",
        summary="Stability/regime diagram with named filled regions and boundary curves.",
        description=(
            "regions[] each have a name, color, and path (array of [x, y] points). "
            "boundaries[] each have a name, style ('solid'|'dashed'|'dotted'), "
            "and points (array of [x, y]).  "
            "specialPoints[] mark triple/critical points with {name, x, y}."
        ),
        example=(
            '<mj-chart type="phase-diagram" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "meta": {"xLabel": "Temperature (K)", "yLabel": "Pressure (atm)"},\n'
            '    "regions": [\n'
            '      {\n'
            '        "name": "Solid",\n'
            '        "color": "#93c5fd",\n'
            '        "path": [\n'
            '          [0, 0], [0, 600], [273, 600], [273, 0]\n'
            '        ]\n'
            '      },\n'
            '      {\n'
            '        "name": "Liquid",\n'
            '        "color": "#86efac",\n'
            '        "path": [\n'
            '          [273, 0.006], [273, 600],\n'
            '          [647, 218], [647, 0.006]\n'
            '        ]\n'
            '      },\n'
            '      {\n'
            '        "name": "Gas",\n'
            '        "color": "#fde68a",\n'
            '        "path": [\n'
            '          [273, 0], [647, 0], [700, 0], [700, 0.006], [273, 0.006]\n'
            '        ]\n'
            '      }\n'
            '    ],\n'
            '    "boundaries": [\n'
            '      {\n'
            '        "name": "Melting curve",\n'
            '        "style": "solid",\n'
            '        "points": [[273, 0], [273, 600]]\n'
            '      },\n'
            '      {\n'
            '        "name": "Vapour curve",\n'
            '        "style": "solid",\n'
            '        "points": [\n'
            '          [273, 0.006], [373, 1.0], [473, 15.3],\n'
            '          [573, 84.5], [647, 218]\n'
            '        ]\n'
            '      },\n'
            '      {\n'
            '        "name": "Sublimation curve",\n'
            '        "style": "dashed",\n'
            '        "points": [[100, 0.0001], [200, 0.003], [273, 0.006]]\n'
            '      }\n'
            '    ],\n'
            '    "specialPoints": [\n'
            '      {"name": "Triple point",   "x": 273, "y": 0.006},\n'
            '      {"name": "Critical point", "x": 647, "y": 218}\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: nyquist ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="nyquist",
        title="Nyquist",
        category="scientific",
        summary="Complex-plane frequency-response locus (Re vs Im).",
        description=(
            "series[].points each contain {omega, re, im}.  "
            "Set mirror:true on a series to draw the conjugate (negative-frequency) "
            "mirror locus as a dashed line.  "
            "criticalPoint {re, im} marks the stability reference (default -1+0j)."
        ),
        example=(
            '<mj-chart type="nyquist" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "criticalPoint": {"re": -1, "im": 0},\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "G(j\\u03c9)",\n'
            '        "mirror": true,\n'
            '        "points": [\n'
            '          {"omega": 0.10, "re":  1.960, "im": -0.392},\n'
            '          {"omega": 0.20, "re":  1.724, "im": -0.690},\n'
            '          {"omega": 0.50, "re":  0.800, "im": -0.960},\n'
            '          {"omega": 1.00, "re":  0.000, "im": -1.000},\n'
            '          {"omega": 2.00, "re": -0.400, "im": -0.800},\n'
            '          {"omega": 5.00, "re": -0.385, "im": -0.385},\n'
            '          {"omega":10.00, "re": -0.198, "im": -0.198}\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: bode ───────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="bode",
        title="Bode",
        category="scientific",
        summary="Stacked magnitude (dB) and phase (deg) frequency-response panels.",
        description=(
            "series[].points each contain {omega, magnitude_db, phase_deg}.  "
            "The x-axis uses a log scale for frequency.  "
            "Set asymptotes:true to draw a straight-line Bode approximation overlay."
        ),
        example=(
            '<mj-chart type="bode" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "asymptotes": true,\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "2nd-order system",\n'
            '        "points": [\n'
            '          {"omega": 0.1,  "magnitude_db":  0.04, "phase_deg":   -1.1},\n'
            '          {"omega": 0.3,  "magnitude_db":  0.39, "phase_deg":   -3.4},\n'
            '          {"omega": 1.0,  "magnitude_db":  0.00, "phase_deg":  -90.0},\n'
            '          {"omega": 2.0,  "magnitude_db": -6.02, "phase_deg": -116.6},\n'
            '          {"omega": 5.0,  "magnitude_db":-20.00, "phase_deg": -146.3},\n'
            '          {"omega":10.0,  "magnitude_db":-34.02, "phase_deg": -158.2},\n'
            '          {"omega":50.0,  "magnitude_db":-60.00, "phase_deg": -171.9},\n'
            '          {"omega":100.0, "magnitude_db":-72.04, "phase_deg": -174.3}\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: smith ──────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="smith",
        title="Smith Chart",
        category="scientific",
        summary="RF impedance chart with constant-resistance and constant-reactance grid circles.",
        description=(
            "series[].points each contain normalised impedance {r, x} and "
            "optionally freq_hz.  "
            "grid.rLines and grid.xLines set the constant-r and constant-x circle values. "
            "Set mode:'admittance' for a Y-Smith chart."
        ),
        example=(
            '<mj-chart type="smith" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "mode": "impedance",\n'
            '    "grid": {\n'
            '      "rLines": [0, 0.2, 0.5, 1.0, 2.0, 5.0],\n'
            '      "xLines": [0.2, 0.5, 1.0, 2.0, 5.0]\n'
            '    },\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Antenna input",\n'
            '        "points": [\n'
            '          {"freq_hz": 100e6, "r": 0.20, "x":  0.80},\n'
            '          {"freq_hz": 200e6, "r": 0.40, "x":  0.50},\n'
            '          {"freq_hz": 300e6, "r": 0.70, "x":  0.20},\n'
            '          {"freq_hz": 400e6, "r": 1.00, "x":  0.00},\n'
            '          {"freq_hz": 500e6, "r": 1.20, "x": -0.30},\n'
            '          {"freq_hz": 600e6, "r": 0.90, "x": -0.60},\n'
            '          {"freq_hz": 700e6, "r": 0.50, "x": -0.90}\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: log-log ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="log-log",
        title="Log-Log",
        category="scientific",
        summary="Both axes logarithmic — ideal for power-law relationships.",
        description=(
            "series[].points contain {x, y} values.  All values must be positive "
            "on log axes.  The scale-x and scale-y controller attributes can "
            "override each axis independently ('log' or 'linear')."
        ),
        example=(
            '<mj-chart type="log-log" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "y = x\\u00b2",\n'
            '        "points": [\n'
            '          {"x": 1,    "y": 1},\n'
            '          {"x": 2,    "y": 4},\n'
            '          {"x": 5,    "y": 25},\n'
            '          {"x": 10,   "y": 100},\n'
            '          {"x": 20,   "y": 400},\n'
            '          {"x": 50,   "y": 2500},\n'
            '          {"x": 100,  "y": 10000}\n'
            '        ]\n'
            '      },\n'
            '      {\n'
            '        "name": "y = x\\u00b3",\n'
            '        "points": [\n'
            '          {"x": 1,   "y": 1},\n'
            '          {"x": 2,   "y": 8},\n'
            '          {"x": 5,   "y": 125},\n'
            '          {"x": 10,  "y": 1000},\n'
            '          {"x": 20,  "y": 8000},\n'
            '          {"x": 50,  "y": 125000},\n'
            '          {"x": 100, "y": 1000000}\n'
            '        ]\n'
            '      }\n'
            '    ],\n'
            '    "meta": {"xLabel": "x", "yLabel": "y"}\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Scientific: semi-log ───────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="semi-log",
        title="Semi-Log",
        category="scientific",
        summary="One logarithmic axis — ideal for exponential growth/decay.",
        description=(
            "By default the y-axis is logarithmic and the x-axis is linear "
            "(exponential growth pattern).  Override with controller attributes "
            "scale-x='log' / scale-y='linear' to swap."
        ),
        example=(
            '<mj-chart type="semi-log" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Bacterial count",\n'
            '        "points": [\n'
            '          {"x":  0, "y":     100},\n'
            '          {"x":  1, "y":     200},\n'
            '          {"x":  2, "y":     400},\n'
            '          {"x":  3, "y":     800},\n'
            '          {"x":  4, "y":    1600},\n'
            '          {"x":  5, "y":    3200},\n'
            '          {"x":  6, "y":    6400},\n'
            '          {"x":  7, "y":   12800},\n'
            '          {"x":  8, "y":   25600},\n'
            '          {"x":  9, "y":   51200},\n'
            '          {"x": 10, "y":  102400}\n'
            '        ]\n'
            '      }\n'
            '    ],\n'
            '    "meta": {"xLabel": "Time (h)", "yLabel": "CFU / mL"}\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: choropleth ─────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="choropleth",
        title="Choropleth",
        category="geographic",
        summary="Filled region map coloured by a sequential value ramp.",
        description=(
            "Requires geojson (a GeoJSON FeatureCollection) and regions[] "
            "[{id, value, label?}].  The feature id is matched against "
            "feature.properties.id.  Regions without a matching value are "
            "rendered in a no-data grey."
        ),
        example=(
            '<mj-chart type="choropleth" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "geojson": {\n'
            '      "type": "FeatureCollection",\n'
            '      "features": [\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "A", "name": "Region A"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [-10, 40], [0, 40], [0, 50], [-10, 50], [-10, 40]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "B", "name": "Region B"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [0, 40], [10, 40], [10, 50], [0, 50], [0, 40]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "C", "name": "Region C"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [10, 40], [20, 40], [20, 50], [10, 50], [10, 40]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "D", "name": "Region D"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [-10, 30], [5, 30], [5, 40], [-10, 40], [-10, 30]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "E", "name": "Region E"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [5, 30], [20, 30], [20, 40], [5, 40], [5, 30]\n'
            '          ]]}\n'
            '        }\n'
            '      ]\n'
            '    },\n'
            '    "regions": [\n'
            '      {"id": "A", "value": 42,  "label": "Region A"},\n'
            '      {"id": "B", "value": 78,  "label": "Region B"},\n'
            '      {"id": "C", "value": 55,  "label": "Region C"},\n'
            '      {"id": "D", "value": 91,  "label": "Region D"},\n'
            '      {"id": "E", "value": 30,  "label": "Region E"}\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: symbol-map ─────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="symbol-map",
        title="Symbol Map",
        category="geographic",
        summary="Point symbols positioned at geographic coordinates.",
        description=(
            "Supply markers[] (flat array) or series[].points.  "
            "Each marker needs at least lat and lng (or lon).  "
            "An optional label field labels the point.  "
            "The symbol attribute on a series selects 'circle', 'square', "
            "'triangle', or 'diamond'."
        ),
        example=(
            '<mj-chart type="symbol-map" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "markers": [\n'
            '      {"lat": 48.85, "lng":  2.35, "label": "Paris"},\n'
            '      {"lat": 51.51, "lng": -0.13, "label": "London"},\n'
            '      {"lat": 52.52, "lng": 13.40, "label": "Berlin"},\n'
            '      {"lat": 41.90, "lng": 12.50, "label": "Rome"},\n'
            '      {"lat": 40.41, "lng": -3.70, "label": "Madrid"},\n'
            '      {"lat": 47.38, "lng":  8.54, "label": "Zurich"},\n'
            '      {"lat": 50.85, "lng":  4.35, "label": "Brussels"}\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: bubble-map ─────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="bubble-map",
        title="Bubble Map",
        category="geographic",
        summary="Proportional circles at geographic coordinates sized by value.",
        description=(
            "Uses a sqrt size scale activated automatically for bubble-map.  "
            "Each marker needs lat, lng, and value.  "
            "The controller attributes min-radius and max-radius control the "
            "pixel size range."
        ),
        example=(
            '<mj-chart type="bubble-map" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "markers": [\n'
            '      {"lat": 40.71, "lng": -74.01, "label": "New York",    "value": 8336817},\n'
            '      {"lat": 34.05, "lng":-118.24, "label": "Los Angeles", "value": 3979576},\n'
            '      {"lat": 41.88, "lng": -87.63, "label": "Chicago",     "value": 2693976},\n'
            '      {"lat": 29.76, "lng": -95.37, "label": "Houston",     "value": 2304580},\n'
            '      {"lat": 33.45, "lng":-112.07, "label": "Phoenix",     "value": 1608139},\n'
            '      {"lat": 39.95, "lng": -75.17, "label": "Philadelphia","value": 1584064},\n'
            '      {"lat": 29.42, "lng": -98.49, "label": "San Antonio", "value": 1434625}\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: proportional-symbol-map ───────────────────────────────────

    ChartTypeDoc(
        type_key="proportional-symbol-map",
        title="Proportional Symbol Map",
        category="geographic",
        summary="Non-circle symbols (diamond/square) sized proportionally to value.",
        description=(
            "Identical pipeline to bubble-map but the symbol shape defaults to "
            "the per-series symbol attribute.  "
            "Supply series[].points with lat, lng (or lon), size, and label."
        ),
        example=(
            '<mj-chart type="proportional-symbol-map" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "GDP (USD bn)",\n'
            '        "symbol": "diamond",\n'
            '        "points": [\n'
            '          {"lat": 35.68, "lon": 139.69, "label": "Tokyo",    "size": 1900},\n'
            '          {"lat": 37.57, "lon": 126.98, "label": "Seoul",    "size": 700},\n'
            '          {"lat": 31.23, "lon": 121.47, "label": "Shanghai", "size": 660},\n'
            '          {"lat": 22.40, "lon": 114.11, "label": "HK",       "size": 360},\n'
            '          {"lat": 13.75, "lon": 100.52, "label": "Bangkok",  "size": 270},\n'
            '          {"lat":  1.35, "lon": 103.82, "label": "Singapore","size": 400},\n'
            '          {"lat": 14.60, "lon": 121.00, "label": "Manila",   "size": 200}\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: hex-map ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="hex-map",
        title="Hex Map",
        category="geographic",
        summary="Equal-area hexagonal tile map with each region coloured by value.",
        description=(
            "Supply regions[] [{id, value, label?}] and layout {id: {q, r}} "
            "where q/r are axial hex-grid coordinates.  "
            "The controller attribute hex-orientation selects 'flat' (default) "
            "or 'pointy'."
        ),
        example=(
            '<mj-chart type="hex-map" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "regions": [\n'
            '      {"id": "NW", "value": 42,  "label": "NW"},\n'
            '      {"id": "N",  "value": 68,  "label": "N"},\n'
            '      {"id": "NE", "value": 55,  "label": "NE"},\n'
            '      {"id": "W",  "value": 30,  "label": "W"},\n'
            '      {"id": "C",  "value": 91,  "label": "C"},\n'
            '      {"id": "E",  "value": 75,  "label": "E"},\n'
            '      {"id": "S",  "value": 48,  "label": "S"}\n'
            '    ],\n'
            '    "layout": {\n'
            '      "NW": {"q": 0, "r": 0},\n'
            '      "N":  {"q": 1, "r": 0},\n'
            '      "NE": {"q": 2, "r": 0},\n'
            '      "W":  {"q": 0, "r": 1},\n'
            '      "C":  {"q": 1, "r": 1},\n'
            '      "E":  {"q": 2, "r": 1},\n'
            '      "S":  {"q": 1, "r": 2}\n'
            '    }\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: tile-grid-map ──────────────────────────────────────────────

    ChartTypeDoc(
        type_key="tile-grid-map",
        title="Tile Grid Map",
        category="geographic",
        summary="Equal-area square tile map — same data shape as hex-map.",
        description=(
            "Identical to hex-map but renders square tiles (shape='square' "
            "is the effective default when the type is tile-grid-map).  "
            "The layout {id: {q, r}} positions each tile on a q/r integer grid."
        ),
        example=(
            '<mj-chart type="tile-grid-map" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "regions": [\n'
            '      {"id": "ME", "value": 14,  "label": "ME"},\n'
            '      {"id": "VT", "value": 21,  "label": "VT"},\n'
            '      {"id": "NH", "value": 18,  "label": "NH"},\n'
            '      {"id": "MA", "value": 68,  "label": "MA"},\n'
            '      {"id": "RI", "value": 35,  "label": "RI"},\n'
            '      {"id": "CT", "value": 48,  "label": "CT"},\n'
            '      {"id": "NY", "value": 91,  "label": "NY"}\n'
            '    ],\n'
            '    "layout": {\n'
            '      "ME": {"q": 3, "r": 0},\n'
            '      "VT": {"q": 2, "r": 1},\n'
            '      "NH": {"q": 3, "r": 1},\n'
            '      "NY": {"q": 1, "r": 2},\n'
            '      "MA": {"q": 2, "r": 2},\n'
            '      "RI": {"q": 3, "r": 2},\n'
            '      "CT": {"q": 2, "r": 3}\n'
            '    }\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: flow-map ───────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="flow-map",
        title="Flow Map",
        category="geographic",
        summary="Directed curved arcs between geographic node pairs, scaled by value.",
        description=(
            "Requires nodes[] [{id, lon, lat, label?}] and links[] "
            "[{source, target, value?}].  "
            "Arc stroke width tapers with value.  "
            "An optional geojson base map is rendered underneath."
        ),
        example=(
            '<mj-chart type="flow-map" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "nodes": [\n'
            '      {"id": "NYC", "lon": -74.01, "lat": 40.71, "label": "New York"},\n'
            '      {"id": "LAX", "lon":-118.24, "lat": 34.05, "label": "Los Angeles"},\n'
            '      {"id": "CHI", "lon": -87.63, "lat": 41.88, "label": "Chicago"},\n'
            '      {"id": "MIA", "lon": -80.19, "lat": 25.77, "label": "Miami"},\n'
            '      {"id": "SEA", "lon":-122.33, "lat": 47.61, "label": "Seattle"}\n'
            '    ],\n'
            '    "links": [\n'
            '      {"source": "NYC", "target": "LAX", "value": 5200},\n'
            '      {"source": "NYC", "target": "CHI", "value": 3800},\n'
            '      {"source": "LAX", "target": "SEA", "value": 2100},\n'
            '      {"source": "CHI", "target": "MIA", "value": 1700},\n'
            '      {"source": "MIA", "target": "NYC", "value": 2900},\n'
            '      {"source": "SEA", "target": "CHI", "value": 1400}\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: route-map ──────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="route-map",
        title="Route Map",
        category="geographic",
        summary="Fixed-path polylines drawn over a geographic base map.",
        description=(
            "series[].routes[] each have an id and waypoints [{lon, lat, label?}].  "
            "Set the controller attribute style='great-circle' to interpolate "
            "each segment through intermediate latitudes.  "
            "show-stops='true' places a circle at each waypoint."
        ),
        example=(
            '<mj-chart type="route-map" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Trans-Atlantic",\n'
            '        "routes": [\n'
            '          {\n'
            '            "id": "JFK-LHR",\n'
            '            "waypoints": [\n'
            '              {"lon": -73.78, "lat": 40.64, "label": "JFK"},\n'
            '              {"lon": -53.00, "lat": 47.00},\n'
            '              {"lon": -30.00, "lat": 52.00},\n'
            '              {"lon":  -0.46, "lat": 51.48, "label": "LHR"}\n'
            '            ]\n'
            '          }\n'
            '        ]\n'
            '      },\n'
            '      {\n'
            '        "name": "Pacific Rim",\n'
            '        "routes": [\n'
            '          {\n'
            '            "id": "LAX-NRT",\n'
            '            "waypoints": [\n'
            '              {"lon":-118.41, "lat": 33.94, "label": "LAX"},\n'
            '              {"lon":-160.00, "lat": 52.00},\n'
            '              {"lon": 139.78, "lat": 35.55, "label": "NRT"}\n'
            '            ]\n'
            '          }\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: geo-heatmap ────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="geo-heatmap",
        title="Geo Heatmap",
        category="geographic",
        summary="Kernel-density heatmap coloured over a geographic base.",
        description=(
            "series[].points[] each have lon, lat, and an optional weight "
            "(default 1).  The renderer computes a Gaussian KDE on a pixel grid "
            "and draws coloured cells.  "
            "The bandwidth controller attribute (pixels) controls kernel width."
        ),
        example=(
            '<mj-chart type="geo-heatmap" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Incident density",\n'
            '        "points": [\n'
            '          {"lon":  2.35, "lat": 48.85, "weight": 3.0},\n'
            '          {"lon":  2.40, "lat": 48.88, "weight": 2.5},\n'
            '          {"lon":  2.30, "lat": 48.82, "weight": 2.0},\n'
            '          {"lon":  2.33, "lat": 48.87, "weight": 4.0},\n'
            '          {"lon":  2.38, "lat": 48.84, "weight": 3.5},\n'
            '          {"lon": 13.40, "lat": 52.52, "weight": 2.0},\n'
            '          {"lon": 13.45, "lat": 52.50, "weight": 1.8},\n'
            '          {"lon": 13.38, "lat": 52.54, "weight": 2.2},\n'
            '          {"lon": -0.13, "lat": 51.51, "weight": 1.5},\n'
            '          {"lon": -0.10, "lat": 51.54, "weight": 1.2}\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: isoline ────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="isoline",
        title="Isoline",
        category="geographic",
        summary="Contour lines or filled contour bands from a lon/lat scalar grid.",
        description=(
            "series[].grid defines the scalar field: lon-min, lon-max, lat-min, "
            "lat-max, cols, rows, and values[] (flat row-major array of length "
            "cols*rows).  series[].levels[] sets the iso-values to trace.  "
            "Set style='filled' on the controller for filled bands."
        ),
        example=(
            '<mj-chart type="isoline" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "series": [\n'
            '      {\n'
            '        "name": "Temperature (\\u00b0C)",\n'
            '        "levels": [10, 15, 20, 25, 30],\n'
            '        "grid": {\n'
            '          "lon-min": -10, "lon-max": 30,\n'
            '          "lat-min":  35, "lat-max": 60,\n'
            '          "cols": 5, "rows": 4,\n'
            '          "values": [\n'
            '            10, 12, 15, 18, 20,\n'
            '            14, 18, 22, 25, 26,\n'
            '            16, 20, 26, 30, 28,\n'
            '            12, 16, 20, 24, 22\n'
            '          ]\n'
            '        }\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

    # ── Geographic: cartogram ──────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="cartogram",
        title="Cartogram",
        category="geographic",
        summary="Value-distorted region map scaling polygon area to data.",
        description=(
            "Requires geojson (FeatureCollection) and regions[] [{id, value, color?}]. "
            "The default style scales each polygon area proportionally to value. "
            "Set the controller attribute style='dorling' for non-overlapping "
            "sqrt-scaled circles at feature centroids."
        ),
        example=(
            '<mj-chart type="cartogram" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "geojson": {\n'
            '      "type": "FeatureCollection",\n'
            '      "features": [\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "A", "name": "Region A"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [-10, 45], [0, 45], [0, 55], [-10, 55], [-10, 45]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "B", "name": "Region B"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [0, 45], [10, 45], [10, 55], [0, 55], [0, 45]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "C", "name": "Region C"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [10, 45], [20, 45], [20, 55], [10, 55], [10, 45]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "D", "name": "Region D"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [-5, 35], [5, 35], [5, 45], [-5, 45], [-5, 35]\n'
            '          ]]}\n'
            '        },\n'
            '        {\n'
            '          "type": "Feature",\n'
            '          "properties": {"id": "E", "name": "Region E"},\n'
            '          "geometry": {"type": "Polygon", "coordinates": [[\n'
            '            [5, 35], [15, 35], [15, 45], [5, 45], [5, 35]\n'
            '          ]]}\n'
            '        }\n'
            '      ]\n'
            '    },\n'
            '    "regions": [\n'
            '      {"id": "A", "value": 120},\n'
            '      {"id": "B", "value": 380},\n'
            '      {"id": "C", "value": 250},\n'
            '      {"id": "D", "value": 600},\n'
            '      {"id": "E", "value": 90}\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
    ),

]
