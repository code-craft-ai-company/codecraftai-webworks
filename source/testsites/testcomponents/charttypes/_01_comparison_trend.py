"""
    01_comparison_trend.py

    ChartTypeDoc catalog entries for the Comparison and Trend chart families.
    Each entry documents one <mj-chart type="..."> variant and provides a
    self-contained HTML example with realistic inline JSON data shaped exactly
    as the corresponding renderer expects.
"""

from testcomponents.charttypes.charttypedoc import ChartTypeDoc


CHART_TYPES = [

    # ------------------------------------------------------------------
    # COMPARISON
    # ------------------------------------------------------------------

    ChartTypeDoc(
        type_key="bar",
        title="Bar Chart",
        category="comparison",
        summary="Horizontal bars comparing values across categories.",
        example=(
            '<mj-chart type="bar" orientation="horizontal" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["North","South","East","West","Central"],'
            '"series":['
            '{"name":"2023","values":[142,98,175,110,63]},'
            '{"name":"2024","values":[158,115,190,128,87]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Horizontal bar chart rendered by bar.js (orientation=horizontal). "
            "Two clustered series make regional differences easy to read. "
            "Use group=\"stack\" for stacked bars or group=\"stack100\" for "
            "100 percent stacked bars."
        ),
    ),

    ChartTypeDoc(
        type_key="column",
        title="Column Chart",
        category="comparison",
        summary="Vertical columns comparing values across categories.",
        example=(
            '<mj-chart type="column" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["Q1","Q2","Q3","Q4"],'
            '"series":['
            '{"name":"Product A","values":[320,410,375,490]},'
            '{"name":"Product B","values":[210,275,340,420]},'
            '{"name":"Product C","values":[140,195,215,260]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Vertical column chart rendered by the shared bar.js renderer "
            "(default orientation=vertical). Three clustered series show "
            "quarterly performance across product lines."
        ),
    ),

    ChartTypeDoc(
        type_key="lollipop",
        title="Lollipop Chart",
        category="comparison",
        summary="Stem-and-dot alternative to bar charts with less ink.",
        example=(
            '<mj-chart type="lollipop" orientation="horizontal" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["Accessibility","Performance","SEO","Best Practices","Security"],'
            '"series":['
            '{"name":"Score","values":[92,78,88,95,84]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Each category is represented by a thin stem from the baseline to a "
            "filled circle head at the data value. Lower ink than a bar chart; "
            "especially effective for ordered ranking or audit-style scorecards."
        ),
    ),

    ChartTypeDoc(
        type_key="dotplot",
        title="Dot Plot",
        category="comparison",
        summary="Cleveland dot plot comparing two periods or groups per category.",
        example=(
            '<mj-chart type="dotplot" orientation="horizontal"'
            ' show-connectors="true" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["Marketing","Engineering","Sales","Support","Operations"],'
            '"series":['
            '{"name":"2022","values":[62,91,74,55,68]},'
            '{"name":"2024","values":[71,96,80,63,75]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Uses a point scale (not a band) so dots land precisely at category "
            "midpoints. When show-connectors is true and two series are present "
            "the renderer draws a dumbbell connector between paired dots, "
            "emphasising change between the two groups."
        ),
    ),

    ChartTypeDoc(
        type_key="bullet",
        title="Bullet Chart",
        category="comparison",
        summary="Compact KPI gauge with qualitative ranges and a target marker.",
        example=(
            '<mj-chart type="bullet" style="height:260px">'
            '<script type="application/json">'
            '{"categories":[],'
            '"series":['
            '{"name":"Revenue","value":275,"target":300,"ranges":[200,250,350],'
            '"rangeLabels":["Poor","Satisfactory","Good"]},'
            '{"name":"Margin","value":42,"target":50,"ranges":[30,45,60],'
            '"rangeLabels":["Poor","Satisfactory","Good"]},'
            '{"name":"NPS","value":38,"target":45,"ranges":[20,35,55],'
            '"rangeLabels":["Poor","Satisfactory","Good"]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Each series entry describes one bullet: a performance bar "
            "(value), a target tick marker (target), and up to three "
            "qualitative range bands (ranges / rangeLabels). Multiple bullets "
            "stack vertically in horizontal layout (the default)."
        ),
    ),

    ChartTypeDoc(
        type_key="slope",
        title="Slope Chart",
        category="comparison",
        summary="Shows direction and magnitude of change between two time points.",
        example=(
            '<mj-chart type="slope" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["2020","2024"],'
            '"series":['
            '{"name":"Europe","values":[42,58]},'
            '{"name":"Asia","values":[55,74]},'
            '{"name":"Americas","values":[38,46]},'
            '{"name":"Africa","values":[22,35]},'
            '{"name":"Oceania","values":[48,52]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Exactly two categories define the left and right column headers. "
            "Each series entry provides two values: left column and right column. "
            "Endpoint labels are auto-nudged to avoid overlap. Slope direction "
            "immediately reveals which entities rose or fell."
        ),
    ),

    ChartTypeDoc(
        type_key="radar",
        title="Radar Chart",
        category="comparison",
        summary="Spider chart comparing entities across multiple dimensions.",
        example=(
            '<mj-chart type="radar" fill="true" grid-shape="polygon" style="height:300px">'
            '<script type="application/json">'
            '{"categories":["Speed","Reliability","Scalability","Security","Usability","Cost"],'
            '"series":['
            '{"name":"Platform A","values":[80,92,75,88,70,60]},'
            '{"name":"Platform B","values":[65,78,90,72,85,74]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Categories define the spokes; each series draws a filled polygon "
            "overlay. Per-spoke scales are derived from the maximum value across "
            "all series on that spoke. The fill and grid-shape attributes "
            "control the visual style."
        ),
    ),

    ChartTypeDoc(
        type_key="parallel",
        title="Parallel Coordinates",
        category="comparison",
        summary="Multi-dimensional comparison with one vertical axis per dimension.",
        example=(
            '<mj-chart type="parallel" curved="true" style="height:280px">'
            '<script type="application/json">'
            '{"dimensions":['
            '{"name":"Height","domain":[150,200],"unit":"cm"},'
            '{"name":"Weight","domain":[50,120],"unit":"kg"},'
            '{"name":"Age","domain":[18,65],"unit":"yr"},'
            '{"name":"Score","domain":[0,100],"unit":"pts"}'
            '],'
            '"series":['
            '{"name":"Group A","observations":['
            '[172,68,34,82],[165,55,29,91],[180,90,45,74],[158,60,52,88],'
            '[175,75,38,65],[168,72,41,79]'
            ']},'
            '{"name":"Group B","observations":['
            '[160,58,28,95],[170,80,35,70],[185,95,50,60],[162,65,44,85],'
            '[177,85,40,72],[155,52,30,90]'
            ']}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "The parallel renderer reads ctx.raw directly (not ctx.model). "
            "Each dimension entry specifies its name, domain [min, max], and "
            "optional unit suffix. Series carry an observations array where each "
            "element is a numeric array aligned with dimensions. Setting "
            "curved=true draws smooth bezier polylines."
        ),
    ),

    # ------------------------------------------------------------------
    # TREND
    # ------------------------------------------------------------------

    ChartTypeDoc(
        type_key="line",
        title="Line Chart",
        category="trend",
        summary="Single-series line showing values over time.",
        example=(
            '<mj-chart type="line" show-points="true" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"],'
            '"series":['
            '{"name":"Revenue","values":[410,385,442,468,510,488,530,572]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Rendered by line.js. Series data can use either values (index-aligned "
            "with categories) or points ([{x, y}]). show-points=true adds "
            "circular markers at each data position. The curve attribute accepts "
            "linear (default) or monotone for smooth interpolation."
        ),
    ),

    ChartTypeDoc(
        type_key="multiline",
        title="Multi-line Chart",
        category="trend",
        summary="Multiple series on a shared time axis for trend comparison.",
        example=(
            '<mj-chart type="multiline" curve="monotone" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"],'
            '"series":['
            '{"name":"Desktop","values":[520,490,545,580,610,598,640,675]},'
            '{"name":"Mobile","values":[310,340,385,420,445,470,510,548]},'
            '{"name":"Tablet","values":[120,115,130,140,135,142,155,160]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "multiline is an alias for line registered in line.js. Any number "
            "of series are drawn on the shared axis. curve=monotone smooths "
            "transitions between data points while preserving monotonicity."
        ),
    ),

    ChartTypeDoc(
        type_key="area",
        title="Area Chart",
        category="trend",
        summary="Filled area chart showing volume beneath a trend line.",
        example=(
            '<mj-chart type="area" curve="monotone" fill-opacity="0.4" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"],'
            '"series":['
            '{"name":"Sessions","values":[12400,13100,11800,14200,15600,14900,16300,17800]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "A plain (unstacked) area chart closes each series to the baseline "
            "at y=0. fill-opacity controls the translucency of the fill. For "
            "multiple series use stack=stack or stack=stack100 to compose them."
        ),
    ),

    ChartTypeDoc(
        type_key="stacked-area",
        title="Stacked Area",
        category="trend",
        summary="Area chart with series stacked to reveal part-to-whole trends.",
        example=(
            '<mj-chart type="stacked-area" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["2018","2019","2020","2021","2022","2023","2024"],'
            '"series":['
            '{"name":"Cloud","values":[120,185,240,310,380,450,530]},'
            '{"name":"On-Prem","values":[480,420,350,290,230,180,140]},'
            '{"name":"Hybrid","values":[80,120,170,220,260,300,330]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "stacked-area is an alias registered in area.js that automatically "
            "sets stack=stack. Series areas are composited bottom-up so the "
            "total height at any x represents the aggregate of all series."
        ),
    ),

    ChartTypeDoc(
        type_key="area100",
        title="100% Stacked Area",
        category="trend",
        summary="Stacked area normalised to 100% to show share over time.",
        example=(
            '<mj-chart type="area100" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["2019","2020","2021","2022","2023","2024"],'
            '"series":['
            '{"name":"Chrome","values":[64,66,65,66,65,66]},'
            '{"name":"Safari","values":[19,17,19,20,19,20]},'
            '{"name":"Firefox","values":[9,8,8,7,6,5]},'
            '{"name":"Other","values":[8,9,8,7,10,9]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "area100 is an alias registered in area.js that automatically sets "
            "stack=stack100. Each x position is normalised so all series sum to "
            "100 percent, making market-share or composition trends readable."
        ),
    ),

    ChartTypeDoc(
        type_key="step",
        title="Step Chart",
        category="trend",
        summary="Step-line chart for discrete state changes over time.",
        example=(
            '<mj-chart type="step" step-position="after" fill="true" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],'
            '"series":['
            '{"name":"Active Users","values":[1400,1620,1580,1750,1880,980,860]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "The step-position attribute controls where the vertical jump "
            "occurs: after (default) jumps at the next x, before jumps before "
            "the current x, middle splits the difference. fill=true shades the "
            "area beneath the step path."
        ),
    ),

    ChartTypeDoc(
        type_key="sparkline",
        title="Sparkline",
        category="trend",
        summary="Compact, axes-free inline trend indicator.",
        example=(
            '<mj-chart type="sparkline" sparkline-variant="line"'
            ' show-markers="true" show-last-value="true" style="height:60px;width:200px">'
            '<script type="application/json">'
            '{"categories":["W1","W2","W3","W4","W5","W6","W7","W8","W9","W10","W11","W12"],'
            '"series":['
            '{"name":"Revenue","values":[88,92,85,97,104,99,111,108,120,115,128,135]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Sparklines render without any axes, gridlines, or legend — only the "
            "trend shape. show-markers=true highlights first, last, min, and max "
            "dots. show-last-value=true appends a text label at the final point. "
            "sparkline-variant=bar switches to a miniature bar style."
        ),
    ),

    ChartTypeDoc(
        type_key="horizon",
        title="Horizon Chart",
        category="trend",
        summary="Banded folded area chart for dense multi-series time data.",
        example=(
            '<mj-chart type="horizon" horizon-bands="3" row-height="40" style="height:200px">'
            '<script type="application/json">'
            '{"categories":["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],'
            '"series":['
            '{"name":"CPU","values":[45,52,48,61,70,66,78,82,74,65,58,50]},'
            '{"name":"Memory","values":[60,63,65,68,72,75,80,84,82,78,70,65]},'
            '{"name":"Network","values":[30,38,35,42,55,50,62,68,60,48,40,35]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "Each series occupies a fixed-height row (row-height px). Values are "
            "divided into magnitude bands; higher bands are rendered darker and "
            "overlap lower ones, folding the area into a compact display. "
            "Set diverging=true to show negative values in a contrasting hue."
        ),
    ),

    ChartTypeDoc(
        type_key="streamgraph",
        title="Streamgraph",
        category="trend",
        summary="Flowing symmetric stacked area emphasising rhythm and volume.",
        example=(
            '<mj-chart type="streamgraph" baseline="wiggle" curve="monotone" style="height:260px">'
            '<script type="application/json">'
            '{"categories":["2016","2017","2018","2019","2020","2021","2022","2023","2024"],'
            '"series":['
            '{"name":"Jazz","values":[42,45,38,50,35,40,48,52,55]},'
            '{"name":"Rock","values":[88,82,76,70,65,62,60,58,55]},'
            '{"name":"Pop","values":[110,118,125,130,120,135,142,148,155]},'
            '{"name":"Electronic","values":[30,38,50,65,80,95,108,120,132]},'
            '{"name":"Classical","values":[25,22,24,20,18,20,22,24,26]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "The baseline attribute controls vertical centering: wiggle "
            "(ThemeRiver, minimises weighted slope), silhouette (centred at "
            "y=0), or zero (bottom-aligned like a stacked area). curve=monotone "
            "smooths the stream contours."
        ),
    ),

    ChartTypeDoc(
        type_key="bump",
        title="Bump Chart",
        category="trend",
        summary="Rank-over-time chart using S-curve connectors between positions.",
        example=(
            '<mj-chart type="bump" style="height:280px">'
            '<script type="application/json">'
            '{"categories":["2020","2021","2022","2023","2024"],'
            '"series":['
            '{"name":"Alpha","values":[3,2,1,2,1]},'
            '{"name":"Beta","values":[1,3,4,3,4]},'
            '{"name":"Gamma","values":[2,1,2,1,2]},'
            '{"name":"Delta","values":[5,4,3,4,3]},'
            '{"name":"Epsilon","values":[4,5,5,5,5]}'
            ']}'
            '</script>'
            '</mj-chart>'
        ),
        description=(
            "The y-axis is inverted so rank 1 appears at the top. Each series "
            "records an integer rank at each time point (1 = best). Consecutive "
            "rank positions are joined with horizontal-monotone cubic Bezier "
            "S-curves. End-of-line labels are nudged to avoid overlap."
        ),
    ),

]
