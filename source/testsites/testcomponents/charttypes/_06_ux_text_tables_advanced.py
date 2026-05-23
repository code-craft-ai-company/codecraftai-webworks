"""
    06_ux_text_tables_advanced.py

    ChartTypeDoc catalog entries for:
      - UX / Product / Business charts (gauge, kpi, cohort, retention,
        user-journey, session-flow)
      - Text / Categorical charts (word-cloud, venn, euler, upset, matrix)
      - Tables with Visual Encoding (heatmap-table, bar-in-cell,
        conditional-format-table, icon-array, waffle-pictograph, scorecard)
      - Less Common / Advanced charts (calendar-heatmap, voronoi, spiral,
        pixel, glyph, faceted)
"""

from testcomponents.charttypes.charttypedoc import ChartTypeDoc


CHART_TYPES = [

    # ── UX / PRODUCT / BUSINESS ─────────────────────────────────────────────

    ChartTypeDoc(
        type_key="gauge",
        title="Gauge",
        category="ux-product-business",
        summary="Arc dial showing a single value against a min/max range with threshold colour bands.",
        example=(
            '<mj-chart type="gauge" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"gauge": {'
            '"value": 72,'
            '"min": 0,'
            '"max": 100,'
            '"unit": "%",'
            '"thresholds": ['
            '{"value": 40, "label": "Fair", "color": "--mj-color-warning"},'
            '{"value": 70, "label": "Good", "color": "--mj-color-success"}'
            '],'
            '"needle": true'
            '}'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Renders a speedometer-style arc gauge.  The gauge.thresholds array "
            "defines colour-band breakpoints; each threshold carries a value, an "
            "optional label, and an optional CSS custom-property colour token.  "
            "start_angle and sweep_angle control the arc geometry."
        ),
    ),

    ChartTypeDoc(
        type_key="kpi",
        title="KPI Card",
        category="ux-product-business",
        summary="Big-number metric card with optional delta badge and sparkline.",
        example=(
            '<mj-chart type="kpi" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"kpi": {'
            '"value": 48320,'
            '"label": "Monthly Active Users",'
            '"comparison": {"value": 41500, "label": "vs last month"},'
            '"spark": [31200, 34800, 38100, 41500, 43900, 46200, 48320]'
            '}'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Displays a prominent headline value with a sub-label, a delta/trend "
            "badge computed from kpi.comparison, and an optional sparkline drawn "
            "at the bottom of the card.  Trend direction (up/down/flat) can be "
            "overridden with kpi.trend."
        ),
    ),

    ChartTypeDoc(
        type_key="cohort",
        title="Cohort Retention Grid",
        category="ux-product-business",
        summary="Heat-coloured retention grid showing how cohorts shrink over time.",
        example=(
            '<mj-chart type="cohort" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"cohorts": ['
            '{"label": "Jan", "size": 1200, "periods": [1.0, 0.72, 0.55, 0.41, 0.33, 0.28]},'
            '{"label": "Feb", "size": 980,  "periods": [1.0, 0.68, 0.50, 0.38, 0.30]},'
            '{"label": "Mar", "size": 1350, "periods": [1.0, 0.75, 0.58, 0.44]},'
            '{"label": "Apr", "size": 1100, "periods": [1.0, 0.70, 0.53]},'
            '{"label": "May", "size": 1450, "periods": [1.0, 0.74]}'
            '],'
            '"period_labels": ["Week 0", "Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],'
            '"mode": "rate"'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Each row is a user cohort; each column is a retention period.  "
            "mode=\"rate\" expects 0–1 fractions and displays percentages; "
            "mode=\"count\" expects absolute user counts.  Cells that do not yet "
            "have data (cohort too young) are greyed out automatically.  "
            "Also registered as type=\"retention\"."
        ),
    ),

    ChartTypeDoc(
        type_key="retention",
        title="Retention Grid (alias)",
        category="ux-product-business",
        summary="Alias for cohort — identical renderer, different type key.",
        example=(
            '<mj-chart type="retention" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"cohorts": ['
            '{"label": "2024-Q1", "size": 5000, "periods": [1.0, 0.60, 0.42, 0.31, 0.24]},'
            '{"label": "2024-Q2", "size": 4800, "periods": [1.0, 0.63, 0.45, 0.34]},'
            '{"label": "2024-Q3", "size": 5200, "periods": [1.0, 0.58, 0.40]},'
            '{"label": "2024-Q4", "size": 6100, "periods": [1.0, 0.65]}'
            '],'
            '"period_labels": ["Month 0", "Month 1", "Month 2", "Month 3", "Month 4"],'
            '"mode": "rate"'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Registered as an alias for the cohort renderer.  Accepts the same "
            "JSON shape: cohorts[], period_labels[], and mode."
        ),
    ),

    ChartTypeDoc(
        type_key="user-journey",
        title="User Journey Map",
        category="ux-product-business",
        summary="Emotion-score line chart across journey steps with touchpoint and pain-point markers.",
        example=(
            '<mj-chart type="user-journey" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"steps": ['
            '{"label": "Awareness", "score": 3.5, "touchpoints": ["Ad", "Blog"], "pain_points": []},'
            '{"label": "Consideration", "score": 2.8, "touchpoints": ["Website"], "pain_points": ["Slow load"]},'
            '{"label": "Purchase", "score": 3.9, "touchpoints": ["Checkout"], "pain_points": []},'
            '{"label": "Onboarding", "score": 2.2, "touchpoints": ["Email"], "pain_points": ["Confusing setup"]},'
            '{"label": "Retention", "score": 4.1, "touchpoints": ["App", "Support"], "pain_points": []}'
            '],'
            '"score_range": [1, 5]'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Draws a satisfaction/emotion score curve across ordered journey steps.  "
            "Each step node is sized by the number of touchpoints; a red dot marks "
            "steps that have pain_points.  Multi-persona layout is supported via "
            "raw.personas (array of step arrays)."
        ),
    ),

    ChartTypeDoc(
        type_key="session-flow",
        title="Session Flow",
        category="ux-product-business",
        summary="Sankey-style navigation flow with nodes and weighted links.",
        example=(
            '<mj-chart type="session-flow" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"nodes": ['
            '{"id": "home",     "label": "Home"},'
            '{"id": "catalog",  "label": "Catalog"},'
            '{"id": "product",  "label": "Product"},'
            '{"id": "cart",     "label": "Cart"},'
            '{"id": "checkout", "label": "Checkout"},'
            '{"id": "exit",     "label": "Exit"}'
            '],'
            '"links": ['
            '{"source": "home",    "target": "catalog",  "value": 820},'
            '{"source": "home",    "target": "exit",     "value": 180},'
            '{"source": "catalog", "target": "product",  "value": 610},'
            '{"source": "catalog", "target": "exit",     "value": 210},'
            '{"source": "product", "target": "cart",     "value": 390},'
            '{"source": "product", "target": "exit",     "value": 220},'
            '{"source": "cart",    "target": "checkout", "value": 270},'
            '{"source": "cart",    "target": "exit",     "value": 120}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Dispatched by the journey.js renderer when the JSON root contains "
            "nodes[] and links[].  Nodes are auto-levelled by in-degree (BFS); "
            "link thickness encodes flow volume.  The same file registers both "
            "user-journey and session-flow."
        ),
    ),

    # ── TEXT / CATEGORICAL ───────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="word-cloud",
        title="Word Cloud",
        category="text-categorical",
        summary="Tag cloud where font size encodes word frequency via a sqrt scale.",
        example=(
            '<mj-chart type="word-cloud" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"words": ['
            '{"text": "Python",      "value": 320},'
            '{"text": "JavaScript",  "value": 280},'
            '{"text": "TypeScript",  "value": 240},'
            '{"text": "Rust",        "value": 190},'
            '{"text": "Go",          "value": 175},'
            '{"text": "SQL",         "value": 160},'
            '{"text": "Docker",      "value": 145},'
            '{"text": "Kubernetes",  "value": 130},'
            '{"text": "GraphQL",     "value": 110},'
            '{"text": "React",       "value": 210},'
            '{"text": "FastAPI",     "value": 95},'
            '{"text": "Postgres",    "value": 88},'
            '{"text": "Redis",       "value": 75},'
            '{"text": "Kafka",       "value": 68},'
            '{"text": "Terraform",   "value": 60}'
            '],'
            '"max_words": 60,'
            '"rotation": "mixed"'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Lays out word tokens on an Archimedean spiral; font size follows a "
            "sqrt scale so visual area (font-size²) is proportional to value.  "
            "rotation=\"mixed\" allows every fourth word to be rotated 90°."
        ),
    ),

    ChartTypeDoc(
        type_key="venn",
        title="Venn Diagram",
        category="text-categorical",
        summary="Overlapping circles showing set membership and intersection sizes (2–3 sets).",
        example=(
            '<mj-chart type="venn" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"sets": ['
            '{"name": "Backend",  "size": 420},'
            '{"name": "Frontend", "size": 380},'
            '{"name": "DevOps",   "size": 210}'
            '],'
            '"intersections": ['
            '{"sets": ["Backend", "Frontend"], "size": 95},'
            '{"sets": ["Backend", "DevOps"],   "size": 78},'
            '{"sets": ["Frontend", "DevOps"],  "size": 42},'
            '{"sets": ["Backend", "Frontend", "DevOps"], "size": 30}'
            '],'
            '"proportional": false'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Supports 2 or 3 sets; for ≥ 4 sets the renderer emits an error and "
            "recommends type=\"upset\".  When proportional=true, circle centres are "
            "nudged so the actual geometric overlap area approximates the declared "
            "intersection size."
        ),
    ),

    ChartTypeDoc(
        type_key="euler",
        title="Euler Diagram",
        category="text-categorical",
        summary="Proportional variant of the Venn diagram where overlap area encodes intersection size.",
        example=(
            '<mj-chart type="euler" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"sets": ['
            '{"name": "Subscribers", "size": 8000},'
            '{"name": "Paid",        "size": 3200}'
            '],'
            '"intersections": ['
            '{"sets": ["Subscribers", "Paid"], "size": 3200}'
            '],'
            '"proportional": true'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Registered as an alias for the venn renderer with proportional=true "
            "as the conventional default.  The renderer uses binary search on the "
            "circle-intersection-area formula to find the centre distance that "
            "matches the declared overlap size."
        ),
    ),

    ChartTypeDoc(
        type_key="upset",
        title="UpSet Plot",
        category="text-categorical",
        summary="Set-intersection bar chart with a dot-matrix membership grid for 4+ sets.",
        example=(
            '<mj-chart type="upset" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"sets": ['
            '{"name": "Email",   "size": 5200},'
            '{"name": "Push",    "size": 3800},'
            '{"name": "SMS",     "size": 2100},'
            '{"name": "In-App",  "size": 4400}'
            '],'
            '"intersections": ['
            '{"sets": ["Email"],                   "size": 1800},'
            '{"sets": ["Push"],                    "size": 1200},'
            '{"sets": ["In-App"],                  "size": 1400},'
            '{"sets": ["Email", "Push"],           "size": 980},'
            '{"sets": ["Email", "In-App"],         "size": 870},'
            '{"sets": ["Push", "In-App"],          "size": 640},'
            '{"sets": ["Email", "Push", "In-App"], "size": 420},'
            '{"sets": ["SMS"],                     "size": 520},'
            '{"sets": ["Email", "SMS"],            "size": 310}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Three visual regions: (1) top — vertical bars for each intersection "
            "sorted by size desc; (2) bottom-centre — dot matrix showing which sets "
            "participate in each intersection, connected by a vertical line; "
            "(3) bottom-left — horizontal bars for individual set sizes."
        ),
    ),

    ChartTypeDoc(
        type_key="matrix",
        title="Matrix Chart",
        category="text-categorical",
        summary="Categorical row × column grid with circle (bubble) or square colour marks.",
        example=(
            '<mj-chart type="matrix" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"x_categories": ["Q1", "Q2", "Q3", "Q4"],'
            '"y_categories": ["APAC", "EMEA", "LATAM", "NA"],'
            '"cells": ['
            '{"x": "Q1", "y": "APAC",  "value": 42},'
            '{"x": "Q1", "y": "EMEA",  "value": 78},'
            '{"x": "Q1", "y": "LATAM", "value": 31},'
            '{"x": "Q1", "y": "NA",    "value": 95},'
            '{"x": "Q2", "y": "APAC",  "value": 55},'
            '{"x": "Q2", "y": "EMEA",  "value": 82},'
            '{"x": "Q2", "y": "LATAM", "value": 40},'
            '{"x": "Q2", "y": "NA",    "value": 110},'
            '{"x": "Q3", "y": "APAC",  "value": 68},'
            '{"x": "Q3", "y": "EMEA",  "value": 74},'
            '{"x": "Q3", "y": "LATAM", "value": 52},'
            '{"x": "Q3", "y": "NA",    "value": 98},'
            '{"x": "Q4", "y": "APAC",  "value": 80},'
            '{"x": "Q4", "y": "EMEA",  "value": 91},'
            '{"x": "Q4", "y": "LATAM", "value": 63},'
            '{"x": "Q4", "y": "NA",    "value": 125}'
            '],'
            '"mark": "circle"'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "mark=\"circle\" sizes bubbles by sqrt scale so area encodes value.  "
            "mark=\"square\" fills cells with a sequential colour scale and overlays "
            "the value as text.  Cells with value ≤ 0 are skipped."
        ),
    ),

    # ── TABLES WITH VISUAL ENCODING ──────────────────────────────────────────

    ChartTypeDoc(
        type_key="heatmap-table",
        title="Heatmap Table",
        category="tables-visual-encoding",
        summary="Data table where numeric cells are filled with sequential or diverging intensity.",
        example=(
            '<mj-chart type="heatmap-table" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"columns": ['
            '{"key": "region",  "label": "Region",  "type": "string"},'
            '{"key": "jan",     "label": "Jan",      "type": "number"},'
            '{"key": "feb",     "label": "Feb",      "type": "number"},'
            '{"key": "mar",     "label": "Mar",      "type": "number"},'
            '{"key": "apr",     "label": "Apr",      "type": "number"}'
            '],'
            '"rows": ['
            '{"region": "North",  "jan": 82, "feb": 76, "mar": 91, "apr": 88},'
            '{"region": "South",  "jan": 55, "feb": 61, "mar": 70, "apr": 74},'
            '{"region": "East",   "jan": 93, "feb": 88, "mar": 95, "apr": 99},'
            '{"region": "West",   "jan": 47, "feb": 52, "mar": 60, "apr": 65},'
            '{"region": "Central","jan": 68, "feb": 71, "mar": 78, "apr": 83}'
            '],'
            '"colorScale": "sequential"'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "The shared envelope (columns, rows) is also used by bar-in-cell and "
            "conditional-format-table.  colorScale accepts \"sequential\" (white → "
            "accent-700) or \"diverging\" (danger → white → success).  domain can "
            "be set explicitly as [min, max]; otherwise auto-computed across all "
            "numeric cells."
        ),
    ),

    ChartTypeDoc(
        type_key="bar-in-cell",
        title="Bar-in-Cell Table",
        category="tables-visual-encoding",
        summary="Table with miniature horizontal bars drawn inside numeric cells.",
        example=(
            '<mj-chart type="bar-in-cell" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"columns": ['
            '{"key": "product",  "label": "Product",  "type": "string"},'
            '{"key": "revenue",  "label": "Revenue",  "type": "number", "render": "bar"},'
            '{"key": "units",    "label": "Units",    "type": "number", "render": "bar"},'
            '{"key": "margin",   "label": "Margin %", "type": "number"}'
            '],'
            '"rows": ['
            '{"product": "Widget A", "revenue": 128000, "units": 3200, "margin": 38},'
            '{"product": "Widget B", "revenue":  94000, "units": 2400, "margin": 42},'
            '{"product": "Gadget X", "revenue": 210000, "units": 5100, "margin": 29},'
            '{"product": "Gadget Y", "revenue":  67000, "units": 1800, "margin": 51},'
            '{"product": "Module Z", "revenue": 155000, "units": 3900, "margin": 35}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Columns with render=\"bar\" draw a filled accent-coloured horizontal "
            "bar proportional to value within that column's min–max domain.  "
            "Columns without render=\"bar\" display plain text.  Per-column domain "
            "can be overridden with a domain:[min, max] field on the column object."
        ),
    ),

    ChartTypeDoc(
        type_key="conditional-format-table",
        title="Conditional Format Table",
        category="tables-visual-encoding",
        summary="Table with rules-based cell highlight fills and icon glyphs.",
        example=(
            '<mj-chart type="conditional-format-table" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"columns": ['
            '{"key": "metric",  "label": "Metric",    "type": "string"},'
            '{"key": "current", "label": "Current",   "type": "number"},'
            '{"key": "target",  "label": "Target",    "type": "number"},'
            '{"key": "status",  "label": "vs Target", "type": "number"}'
            '],'
            '"rows": ['
            '{"metric": "Uptime %",    "current": 99.8, "target": 99.9, "status": -0.1},'
            '{"metric": "Error Rate",  "current":  1.4, "target":  2.0, "status":  0.6},'
            '{"metric": "P95 Latency", "current": 320,  "target": 300,  "status": -20},'
            '{"metric": "Throughput",  "current": 4800, "target": 4000, "status": 800},'
            '{"metric": "MTTR (min)",  "current":  18,  "target":  15,  "status":  -3}'
            '],'
            '"rules": ['
            '{"column": "status", "op": "lt",  "value": 0,   "style": {"fill": "var(--mj-color-danger-subtle, #fee2e2)",  "icon": "warning"}},'
            '{"column": "status", "op": "gte", "value": 0,   "style": {"fill": "var(--mj-color-success-subtle, #dcfce7)", "icon": "check"}}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Rules are evaluated in order; the first matching rule wins.  "
            "Supported ops: lt, lte, gt, gte, eq, neq.  Style.fill accepts any "
            "CSS colour; style.icon accepts \"warning\", \"check\", \"info\", or "
            "\"cross\"."
        ),
    ),

    ChartTypeDoc(
        type_key="icon-array",
        title="Icon Array",
        category="tables-visual-encoding",
        summary="Grid of countable unit icons (circle/person/square) coloured by proportion.",
        example=(
            '<mj-chart type="icon-array" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"total": 100,'
            '"series": ['
            '{"name": "Treated",   "count": 63, "icon": "person"},'
            '{"name": "Placebo",   "count": 27, "icon": "person"},'
            '{"name": "Untreated", "count": 10, "icon": "person"}'
            '],'
            '"grid": {"cols": 10}'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Icons are placed left-to-right, top-to-bottom in declaration order.  "
            "icon supports \"circle\" (default), \"square\", or \"person\".  "
            "total controls the grid size; series counts should sum to ≤ total.  "
            "A legend with percentage labels is rendered below the grid."
        ),
    ),

    ChartTypeDoc(
        type_key="waffle-pictograph",
        title="Waffle Pictograph",
        category="tables-visual-encoding",
        summary="Square-icon proportion grid (waffle chart variant of icon-array).",
        example=(
            '<mj-chart type="waffle-pictograph" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"total": 100,'
            '"series": ['
            '{"name": "Completed", "count": 74, "icon": "square"},'
            '{"name": "In Progress","count": 18, "icon": "square"},'
            '{"name": "Blocked",   "count":  8, "icon": "square"}'
            '],'
            '"grid": {"cols": 10}'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Registered as an alias of the icon-array renderer.  Default icon is "
            "\"square\" by convention for waffle charts, but any icon type from the "
            "series entries or the icon attribute is accepted."
        ),
    ),

    ChartTypeDoc(
        type_key="scorecard",
        title="Scorecard",
        category="tables-visual-encoding",
        summary="Row of KPI tiles each showing value, delta, trend arrow, progress bar, and sparkline.",
        example=(
            '<mj-chart type="scorecard" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"metrics": ['
            '{'
            '"label": "Revenue", "value": 2480000, "target": 3000000,'
            '"delta": 0.12, "trend": "up",'
            '"sparkline": [1900000, 2050000, 2120000, 2300000, 2380000, 2480000]'
            '},'
            '{'
            '"label": "Churn Rate", "value": 3.2, "target": 4.0,'
            '"delta": -0.08, "trend": "down",'
            '"sparkline": [4.1, 3.9, 3.7, 3.5, 3.3, 3.2]'
            '},'
            '{'
            '"label": "NPS", "value": 62, "target": 70,'
            '"delta": 0.05, "trend": "up",'
            '"sparkline": [48, 51, 55, 57, 60, 62]'
            '}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Tiles are laid out horizontally by default (orientation=\"horizontal\") "
            "or stacked vertically.  delta is a fractional change (0.12 = +12%).  "
            "A progress bar appears when both target and value are present.  "
            "mode=\"compact\" omits delta, progress bar, and sparkline."
        ),
    ),

    # ── LESS COMMON / ADVANCED ───────────────────────────────────────────────

    ChartTypeDoc(
        type_key="calendar-heatmap",
        title="Calendar Heatmap",
        category="advanced",
        summary="GitHub-style year-view heat grid mapping daily values across 53 week columns.",
        example=(
            '<mj-chart type="calendar-heatmap" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"years": [2025],'
            '"data": ['
            '{"date": "2025-01-06", "value": 12},'
            '{"date": "2025-01-07", "value": 5},'
            '{"date": "2025-01-13", "value": 28},'
            '{"date": "2025-01-20", "value": 18},'
            '{"date": "2025-02-03", "value": 42},'
            '{"date": "2025-02-17", "value": 37},'
            '{"date": "2025-03-10", "value": 55},'
            '{"date": "2025-03-24", "value": 61},'
            '{"date": "2025-04-07", "value": 48},'
            '{"date": "2025-04-21", "value": 73},'
            '{"date": "2025-05-05", "value": 88},'
            '{"date": "2025-05-19", "value": 94},'
            '{"date": "2025-06-02", "value": 102},'
            '{"date": "2025-06-16", "value": 115},'
            '{"date": "2025-07-04", "value": 78},'
            '{"date": "2025-07-14", "value": 65},'
            '{"date": "2025-08-11", "value": 50},'
            '{"date": "2025-09-01", "value": 88},'
            '{"date": "2025-10-13", "value": 120},'
            '{"date": "2025-11-03", "value": 95},'
            '{"date": "2025-12-25", "value": 30}'
            '],'
            '"colorScale": "sequential"'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Dates are \"YYYY-MM-DD\" strings.  The grid starts on the Monday on or "
            "before January 1 so columns align on week boundaries.  Multiple years "
            "can be stacked by listing them in raw.years.  domain can be set "
            "explicitly; otherwise auto-computed from the data values."
        ),
    ),

    ChartTypeDoc(
        type_key="voronoi",
        title="Voronoi Diagram",
        category="advanced",
        summary="2-D nearest-neighbour region partition computed via half-plane clipping.",
        example=(
            '<mj-chart type="voronoi" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"series": ['
            '{'
            '"name": "Cluster A",'
            '"points": ['
            '{"x": 1.2, "y": 2.8, "label": "P1"},'
            '{"x": 2.0, "y": 4.1, "label": "P2"},'
            '{"x": 3.1, "y": 1.5, "label": "P3"}'
            ']'
            '},'
            '{'
            '"name": "Cluster B",'
            '"points": ['
            '{"x": 5.5, "y": 3.2, "label": "P4"},'
            '{"x": 6.8, "y": 5.0, "label": "P5"},'
            '{"x": 7.2, "y": 1.8, "label": "P6"}'
            ']'
            '},'
            '{'
            '"name": "Cluster C",'
            '"points": ['
            '{"x": 4.0, "y": 7.5, "label": "P7"},'
            '{"x": 5.2, "y": 8.8, "label": "P8"}'
            ']'
            '}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Each point in series[].points becomes a Voronoi cell seed.  The "
            "renderer uses iterative half-plane clipping (Sutherland-Hodgman on "
            "perpendicular bisectors) — no external library.  Series colour is "
            "applied to all cells belonging to that series.  mode attr: "
            "\"filled\" (default) | \"overlay\" (outlines only)."
        ),
    ),

    ChartTypeDoc(
        type_key="spiral",
        title="Spiral Chart",
        category="advanced",
        summary="Archimedean spiral mapping time-series data so repeating cycles align radially.",
        example=(
            '<mj-chart type="spiral" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"cycle": "week",'
            '"series": ['
            '{'
            '"name": "Page Views",'
            '"points": ['
            '{"t": "2025-01-06", "value": 4200},'
            '{"t": "2025-01-07", "value": 3800},'
            '{"t": "2025-01-08", "value": 6100},'
            '{"t": "2025-01-09", "value": 5900},'
            '{"t": "2025-01-10", "value": 5400},'
            '{"t": "2025-01-11", "value": 2100},'
            '{"t": "2025-01-12", "value": 1800},'
            '{"t": "2025-01-13", "value": 4500},'
            '{"t": "2025-01-14", "value": 4100},'
            '{"t": "2025-01-15", "value": 6400},'
            '{"t": "2025-01-16", "value": 6000},'
            '{"t": "2025-01-17", "value": 5600},'
            '{"t": "2025-01-18", "value": 2300},'
            '{"t": "2025-01-19", "value": 1900}'
            ']'
            '}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "cycle controls the radial period: \"week\" (default, Mon–Sun labels), "
            "\"year\" (Jan–Dec labels), or \"day\" (hourly labels).  Each spiral arm "
            "represents one full cycle; patterns that repeat weekly stack on top of "
            "each other radially.  mode attr: \"line\" (default) | \"bar\"."
        ),
    ),

    ChartTypeDoc(
        type_key="pixel",
        title="Pixel Chart",
        category="advanced",
        summary="Dense 2-D discrete grid where each cell encodes one observation via colour.",
        example=(
            '<mj-chart type="pixel" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"xDimension": "Hour of Day",'
            '"yDimension": "Day of Week",'
            '"valueMeasure": "Incidents",'
            '"colorScale": "sequential",'
            '"bins": ['
            '{"x": 0, "y": 0, "value": 2},  {"x": 1, "y": 0, "value": 1},'
            '{"x": 2, "y": 0, "value": 0},  {"x": 3, "y": 0, "value": 3},'
            '{"x": 4, "y": 0, "value": 5},  {"x": 5, "y": 0, "value": 8},'
            '{"x": 6, "y": 0, "value": 12}, {"x": 7, "y": 0, "value": 18},'
            '{"x": 8, "y": 0, "value": 22}, {"x": 9, "y": 0, "value": 19},'
            '{"x": 10,"y": 0, "value": 15}, {"x": 11,"y": 0, "value": 11},'
            '{"x": 0, "y": 1, "value": 1},  {"x": 1, "y": 1, "value": 0},'
            '{"x": 2, "y": 1, "value": 0},  {"x": 3, "y": 1, "value": 2},'
            '{"x": 4, "y": 1, "value": 4},  {"x": 5, "y": 1, "value": 7},'
            '{"x": 6, "y": 1, "value": 10}, {"x": 7, "y": 1, "value": 16},'
            '{"x": 8, "y": 1, "value": 20}, {"x": 9, "y": 1, "value": 17},'
            '{"x": 10,"y": 1, "value": 13}, {"x": 11,"y": 1, "value": 9},'
            '{"x": 0, "y": 2, "value": 0},  {"x": 5, "y": 2, "value": 3},'
            '{"x": 6, "y": 2, "value": 6},  {"x": 7, "y": 2, "value": 9},'
            '{"x": 8, "y": 2, "value": 14}, {"x": 9, "y": 2, "value": 11},'
            '{"x": 10,"y": 2, "value": 8},  {"x": 11,"y": 2, "value": 5}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "x and y in each bin are 0-based integer indices; the grid dimensions "
            "are inferred as max(x)+1 × max(y)+1.  Colour follows the same "
            "color-mix sequential/diverging helpers as heatmaptable.js and "
            "calendarheatmap.js.  domain can be provided explicitly."
        ),
    ),

    ChartTypeDoc(
        type_key="glyph",
        title="Glyph Chart",
        category="advanced",
        summary="Tiled star/radar/bar-glyph polygons — one miniature glyph per observation.",
        example=(
            '<mj-chart type="glyph" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"axes": ["Speed", "Accuracy", "Reliability", "Cost", "Scalability"],'
            '"glyphType": "radar",'
            '"grid": {"cols": 4},'
            '"series": ['
            '{"name": "Service A", "values": [0.9, 0.7, 0.8, 0.5, 0.85]},'
            '{"name": "Service B", "values": [0.6, 0.95, 0.9, 0.7, 0.65]},'
            '{"name": "Service C", "values": [0.75, 0.6, 0.7, 0.9, 0.8]},'
            '{"name": "Service D", "values": [0.5, 0.8, 0.6, 0.4, 0.95]},'
            '{"name": "Service E", "values": [0.85, 0.75, 0.65, 0.6, 0.7]},'
            '{"name": "Service F", "values": [0.4, 0.5, 0.85, 0.95, 0.55]},'
            '{"name": "Service G", "values": [0.95, 0.65, 0.55, 0.35, 0.9]},'
            '{"name": "Service H", "values": [0.7, 0.85, 0.8, 0.65, 0.6]}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "values are normalised per-axis (0–1) across all series so the glyph "
            "spans the full radius for the best performer on each axis.  Raw values "
            "outside [0, 1] are also accepted — per-axis linear scales are applied "
            "automatically.  glyphType: \"star\" (outline only), \"radar\" (filled), "
            "\"bar-glyph\" (radial bars)."
        ),
    ),

    ChartTypeDoc(
        type_key="faceted",
        title="Faceted (Small Multiples)",
        category="advanced",
        summary="Tiles the same inner chart type across data groups in a responsive SVG grid.",
        example=(
            '<mj-chart type="faceted" style="height:260px">'
            '<script type="application/json">'
            '{'
            '"childType": "bar",'
            '"categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],'
            '"grid": {"cols": 2, "colGap": 12, "rowGap": 12},'
            '"sharedScales": true,'
            '"panels": ['
            '{'
            '"label": "North",'
            '"series": [{"name": "Revenue", "values": [42, 55, 61, 58, 70, 75]}]'
            '},'
            '{'
            '"label": "South",'
            '"series": [{"name": "Revenue", "values": [28, 32, 38, 45, 51, 49]}]'
            '},'
            '{'
            '"label": "East",'
            '"series": [{"name": "Revenue", "values": [65, 70, 78, 82, 90, 95]}]'
            '},'
            '{'
            '"label": "West",'
            '"series": [{"name": "Revenue", "values": [38, 42, 48, 53, 60, 58]}]'
            '}'
            ']'
            '}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "childType (or the facet-type HTML attribute) names any registered "
            "renderer — bar, line, area, scatter, etc.  Each panel receives a "
            "sub-context sized to its grid cell.  sharedScales=true computes the "
            "union domain across all panels so y-axes are comparable.  The faceted "
            "renderer does not spawn child <mj-chart> elements."
        ),
    ),

]
