"""
    02_distribution_relationship.py

    ChartTypeDoc catalog entries for the DISTRIBUTION and RELATIONSHIP chart
    categories supported by the <mj-chart> controller.

    Data shapes verified against the renderer source files in
    charts/core/renderers/.
"""

from testcomponents.charttypes.charttypedoc import ChartTypeDoc


# ---------------------------------------------------------------------------
# DISTRIBUTION
# ---------------------------------------------------------------------------

_HISTOGRAM = ChartTypeDoc(
    type_key="histogram",
    title="Histogram",
    category="DISTRIBUTION",
    summary="Divides a continuous variable into bins and counts observations per bin.",
    example="""<mj-chart type="histogram" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Reaction Time (ms)",
          "samples": [210, 225, 230, 235, 240, 242, 245, 248, 250, 252,
                      255, 258, 260, 263, 265, 268, 270, 273, 275, 278,
                      280, 285, 290, 295, 300, 308, 315, 325, 340, 360]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Accepts either a raw samples array (renderer bins with Sturges rule) "
        "or pre-computed bins as {x0, x1, count} objects. "
        "Use the bin-count attr to override the number of bins, "
        "group='stack' to stack multiple series, "
        "and normalize='density' to show probability density on the y-axis."
    ),
)

_DENSITY = ChartTypeDoc(
    type_key="density",
    title="Density Plot",
    category="DISTRIBUTION",
    summary="Smoothed kernel density estimate of a continuous variable.",
    example="""<mj-chart type="density" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Group A",
          "samples": [48, 51, 53, 55, 56, 57, 58, 59, 60, 61,
                      62, 63, 64, 65, 66, 67, 68, 70, 72, 75]
        },
        {
          "name": "Group B",
          "samples": [55, 60, 63, 65, 66, 67, 68, 69, 70, 71,
                      72, 73, 74, 75, 76, 77, 78, 80, 83, 88]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Uses a Gaussian KDE with Silverman's rule-of-thumb bandwidth. "
        "Rendered as a filled area curve. "
        "Set fill='none' to show line only, or bandwidth=<number> to override "
        "the automatic bandwidth selection."
    ),
)

_FREQUENCY_POLYGON = ChartTypeDoc(
    type_key="frequency-polygon",
    title="Frequency Polygon",
    category="DISTRIBUTION",
    summary="Line graph connecting bin midpoints — a continuous alternative to the histogram.",
    example="""<mj-chart type="frequency-polygon" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Score",
          "bins": [
            {"x0": 0,  "x1": 10, "count": 3},
            {"x0": 10, "x1": 20, "count": 8},
            {"x0": 20, "x1": 30, "count": 15},
            {"x0": 30, "x1": 40, "count": 22},
            {"x0": 40, "x1": 50, "count": 18},
            {"x0": 50, "x1": 60, "count": 11},
            {"x0": 60, "x1": 70, "count": 6},
            {"x0": 70, "x1": 80, "count": 2}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Draws a line through the midpoint of each bin and dots at each midpoint. "
        "Accepts the same samples or pre-binned data as histogram. "
        "Set fill='none' to suppress the shaded area beneath the line."
    ),
)

_BOXPLOT = ChartTypeDoc(
    type_key="boxplot",
    title="Box Plot",
    category="DISTRIBUTION",
    summary="Five-number summary (min, Q1, median, Q3, max) with outlier dots.",
    example="""<mj-chart type="boxplot" style="height:260px">
  <script type="application/json">
    {
      "categories": ["Control", "Treatment A", "Treatment B"],
      "series": [
        {
          "name": "Yield (kg)",
          "groups": [
            {"category": "Control",     "min": 12, "q1": 15, "median": 18, "q3": 22, "max": 28, "outliers": [8]},
            {"category": "Treatment A", "min": 18, "q1": 22, "median": 26, "q3": 31, "max": 38},
            {"category": "Treatment B", "min": 20, "q1": 25, "median": 30, "q3": 36, "max": 44, "outliers": [50]}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Each group can supply either a raw samples array or pre-computed "
        "{min, q1, median, q3, max, outliers} stats. "
        "Multiple series render side-by-side within each category band. "
        "Set notched='true' for notched boxes, or iqr-mult to change the whisker fence."
    ),
)

_VIOLIN = ChartTypeDoc(
    type_key="violin",
    title="Violin Plot",
    category="DISTRIBUTION",
    summary="Mirrored kernel density estimate showing the full distribution shape per group.",
    example="""<mj-chart type="violin" show-box="true" style="height:260px">
  <script type="application/json">
    {
      "categories": ["Setosa", "Versicolor", "Virginica"],
      "series": [
        {
          "name": "Petal Length (cm)",
          "groups": [
            {"category": "Setosa",     "samples": [1.4,1.4,1.3,1.5,1.4,1.7,1.4,1.5,1.4,1.5,1.5,1.6,1.4,1.1,1.2,1.5,1.3,1.4,1.7,1.5]},
            {"category": "Versicolor", "samples": [4.7,4.5,4.9,4.0,4.6,4.5,4.7,3.3,4.6,3.9,3.5,4.2,4.0,4.7,3.6,4.4,4.5,4.1,4.5,3.9]},
            {"category": "Virginica",  "samples": [6.0,5.1,5.9,5.6,5.8,6.6,4.5,6.3,5.8,6.1,5.1,5.3,5.5,5.0,5.1,5.3,5.5,6.7,6.9,5.0]}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Requires at least two samples per group for KDE. "
        "Set show-box='true' to overlay a miniature box plot, "
        "show-points='true' to scatter raw observations, "
        "and half='true' for a half-violin (rain-cloud style)."
    ),
)

_STRIP = ChartTypeDoc(
    type_key="strip",
    title="Strip Plot",
    category="DISTRIBUTION",
    summary="Individual observations scattered with random jitter along a category axis.",
    example="""<mj-chart type="strip" style="height:260px">
  <script type="application/json">
    {
      "categories": ["Q1", "Q2", "Q3", "Q4"],
      "series": [
        {
          "name": "Revenue ($k)",
          "groups": [
            {"category": "Q1", "samples": [42, 45, 38, 50, 44, 47, 41, 49, 43, 46]},
            {"category": "Q2", "samples": [55, 58, 52, 60, 57, 54, 59, 56, 61, 53]},
            {"category": "Q3", "samples": [48, 51, 45, 55, 50, 47, 53, 49, 52, 46]},
            {"category": "Q4", "samples": [65, 70, 62, 75, 68, 72, 66, 71, 64, 69]}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Data shape mirrors boxplot: series[].groups[].{category, samples}. "
        "Set jitter='none' for aligned ticks, jitter='swarm' for collision-avoiding "
        "beeswarm-style placement, or r=<px> to change the dot radius."
    ),
)

_SWARM = ChartTypeDoc(
    type_key="swarm",
    title="Swarm Plot",
    category="DISTRIBUTION",
    summary="Non-overlapping dot layout along a category axis — beeswarm style.",
    example="""<mj-chart type="swarm" style="height:260px">
  <script type="application/json">
    {
      "categories": ["Low", "Medium", "High"],
      "series": [
        {
          "name": "Score",
          "groups": [
            {"category": "Low",    "samples": [22,25,28,24,21,27,23,26,29,20]},
            {"category": "Medium", "samples": [45,48,42,50,46,44,49,47,43,51]},
            {"category": "High",   "samples": [70,74,68,76,72,71,75,69,73,77]}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Uses the same renderer as strip but defaults jitter='swarm'. "
        "Points are placed with a greedy collision-avoidance algorithm so no "
        "two dots overlap. Useful when n < ~200 per group."
    ),
)

_RUG = ChartTypeDoc(
    type_key="rug",
    title="Rug Plot",
    category="DISTRIBUTION",
    summary="Tick marks along an axis showing the exact position of each observation.",
    example="""<mj-chart type="rug" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Group A",
          "samples": [12,15,18,20,22,23,25,27,28,30,31,33,35,38,40,43,45,48,50,55]
        },
        {
          "name": "Group B",
          "samples": [25,28,30,32,34,35,37,38,40,41,43,44,46,48,50,52,55,58,60,65]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Each series renders in its own row offset so they do not overlap. "
        "Tick opacity auto-scales with density (denser data → lower opacity). "
        "Set tick-height=<px> or opacity=<0-1> to override defaults."
    ),
)

_DOT_HISTOGRAM = ChartTypeDoc(
    type_key="dot-histogram",
    title="Dot Histogram",
    category="DISTRIBUTION",
    summary="Wilkinson dot plot — stacked dots instead of bars to show individual counts.",
    example="""<mj-chart type="dot-histogram" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Errors",
          "samples": [1,1,2,2,2,3,3,3,3,4,4,4,4,4,5,5,5,5,6,6,6,7,7,8,9]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Auto-switches from stacked dots to bars when total dot count exceeds "
        "dot-limit (default 200). Set bin-count to control bin width. "
        "Multiple series are placed side-by-side within each bin by default; "
        "set group='overlay' for overlaid semi-transparent bars."
    ),
)

_RIDGELINE = ChartTypeDoc(
    type_key="ridgeline",
    title="Ridgeline Plot",
    category="DISTRIBUTION",
    summary="Vertically offset density curves — one per group — revealing distribution shifts.",
    example="""<mj-chart type="ridgeline" style="height:260px">
  <script type="application/json">
    {
      "categories": ["2020", "2021", "2022", "2023", "2024"],
      "series": [
        {
          "name": "Daily High Temp (°F)",
          "groups": [
            {"category": "2020", "samples": [62,65,68,70,72,73,74,75,76,77,78,79,80,81,82,83,85,87,90,94]},
            {"category": "2021", "samples": [60,63,66,68,70,72,73,74,75,76,77,78,79,81,83,85,88,91,95,98]},
            {"category": "2022", "samples": [64,67,70,72,74,75,76,77,78,79,80,81,82,83,85,87,89,92,96,99]},
            {"category": "2023", "samples": [66,69,72,74,76,77,78,79,80,81,82,83,84,85,87,89,91,94,97,100]},
            {"category": "2024", "samples": [68,71,74,76,78,79,80,81,82,83,84,85,86,87,89,91,93,96,99,102]}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "The categories list controls display order (top to bottom). "
        "Set overlap=<0-1> to control how much rows overlap (default 0.5). "
        "Set mode='histogram' for stepped histogram ridges instead of KDE curves."
    ),
)

_QQ = ChartTypeDoc(
    type_key="qq",
    title="Q-Q Plot",
    category="DISTRIBUTION",
    summary="Quantile-quantile plot comparing sample quantiles to a theoretical distribution.",
    example="""<mj-chart type="qq" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Residuals",
          "samples": [-2.1,-1.5,-1.2,-0.9,-0.7,-0.5,-0.4,-0.2,-0.1, 0.0,
                       0.1, 0.2, 0.3, 0.5, 0.6, 0.8, 1.0, 1.3, 1.7, 2.3]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Single series plots observed quantiles against a theoretical distribution "
        "(default 'normal'; set theoretical='uniform'|'exponential'|'lognormal'). "
        "Supply two series for an empirical Q-Q comparison. "
        "A 45° reference line indicates perfect agreement."
    ),
)

_CDF = ChartTypeDoc(
    type_key="cdf",
    title="CDF",
    category="DISTRIBUTION",
    summary="Empirical cumulative distribution function — proportion of data at or below each value.",
    example="""<mj-chart type="cdf" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Before",
          "samples": [10,14,17,20,22,24,26,28,30,32,34,36,38,41,45,49,54,60,68,80]
        },
        {
          "name": "After",
          "samples": [20,24,27,30,32,34,36,38,40,42,44,46,48,51,55,59,64,70,78,90]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Renders as a step function by default. "
        "Set smooth='true' for a spline curve. "
        "Set direction='descending' to display a survival function (1 - CDF). "
        "Pre-computed points can be supplied as series[].points=[{x, y}, ...] "
        "where y is the cumulative probability [0, 1]."
    ),
)


# ---------------------------------------------------------------------------
# RELATIONSHIP
# ---------------------------------------------------------------------------

_SCATTER = ChartTypeDoc(
    type_key="scatter",
    title="Scatter Plot",
    category="RELATIONSHIP",
    summary="Individual observations plotted at (x, y) coordinates to reveal correlations.",
    example="""<mj-chart type="scatter" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "City A",
          "points": [
            {"x": 1.2, "y": 3.4}, {"x": 2.0, "y": 5.1}, {"x": 2.8, "y": 4.7},
            {"x": 3.5, "y": 6.2}, {"x": 4.1, "y": 7.0}, {"x": 4.8, "y": 6.8},
            {"x": 5.5, "y": 8.3}, {"x": 6.2, "y": 9.1}, {"x": 7.0, "y": 8.9},
            {"x": 7.8, "y": 10.2}
          ]
        },
        {
          "name": "City B",
          "points": [
            {"x": 1.5, "y": 2.1}, {"x": 2.3, "y": 3.8}, {"x": 3.0, "y": 4.2},
            {"x": 3.8, "y": 5.5}, {"x": 4.5, "y": 5.9}, {"x": 5.2, "y": 7.1},
            {"x": 6.0, "y": 7.8}, {"x": 6.7, "y": 8.5}, {"x": 7.5, "y": 9.0},
            {"x": 8.2, "y": 9.8}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Each series provides an array of {x, y} point objects. "
        "Set the series shape field to 'square', 'triangle', or 'diamond' "
        "to vary point marks by series."
    ),
)

_BUBBLE = ChartTypeDoc(
    type_key="bubble",
    title="Bubble Chart",
    category="RELATIONSHIP",
    summary="Scatter plot with a third dimension encoded as circle area.",
    example="""<mj-chart type="bubble" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Countries",
          "points": [
            {"x": 8.2,  "y": 72, "size": 1400, "label": "China"},
            {"x": 10.5, "y": 74, "size": 1200, "label": "India"},
            {"x": 62.0, "y": 78, "size": 330,  "label": "USA"},
            {"x": 45.0, "y": 82, "size": 128,  "label": "Japan"},
            {"x": 48.0, "y": 81, "size": 83,   "label": "Germany"},
            {"x": 28.0, "y": 76, "size": 215,  "label": "Brazil"},
            {"x": 18.0, "y": 70, "size": 180,  "label": "Pakistan"},
            {"x": 55.0, "y": 80, "size": 68,   "label": "France"}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Each point must include a size field; the renderer maps sizes to radii "
        "on a square-root scale. Set min-radius and max-radius attrs to control "
        "the pixel range. Labels appear next to each bubble."
    ),
)

_CONNECTED_SCATTER = ChartTypeDoc(
    type_key="connected-scatter",
    title="Connected Scatter",
    category="RELATIONSHIP",
    summary="Scatter points joined by lines in data order — useful for time-path trajectories.",
    example="""<mj-chart type="connected-scatter" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Lifecycle",
          "points": [
            {"x": 5,  "y": 12, "label": "2018"},
            {"x": 12, "y": 22, "label": "2019"},
            {"x": 20, "y": 35, "label": "2020"},
            {"x": 18, "y": 30, "label": "2021"},
            {"x": 25, "y": 42, "label": "2022"},
            {"x": 32, "y": 55, "label": "2023"},
            {"x": 38, "y": 61, "label": "2024"}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Uses the same data shape as scatter (series[].points[].{x, y, label?}). "
        "Points are connected in the order they appear in the array. "
        "Labels are drawn next to each point."
    ),
)

_RESIDUAL = ChartTypeDoc(
    type_key="residual",
    title="Residual Plot",
    category="RELATIONSHIP",
    summary="Scatter with a y=0 reference line for visualizing model residuals.",
    example="""<mj-chart type="residual" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Residuals",
          "points": [
            {"x": 10, "y":  0.8}, {"x": 15, "y": -0.3}, {"x": 20, "y":  1.1},
            {"x": 25, "y": -0.7}, {"x": 30, "y":  0.4}, {"x": 35, "y": -1.2},
            {"x": 40, "y":  0.2}, {"x": 45, "y":  0.9}, {"x": 50, "y": -0.5},
            {"x": 55, "y":  1.4}, {"x": 60, "y": -0.8}, {"x": 65, "y":  0.3}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Identical data shape to scatter. "
        "A dashed zero-reference line is always drawn. "
        "Patterns in residuals (trends, fan shapes) indicate model mis-specification."
    ),
)

_HEATMAP = ChartTypeDoc(
    type_key="heatmap",
    title="Heatmap",
    category="RELATIONSHIP",
    summary="Grid of colored cells encoding a numeric value at each (row, column) intersection.",
    example="""<mj-chart type="heatmap" show-labels="true" style="height:260px">
  <script type="application/json">
    {
      "categories": ["Mon", "Tue", "Wed", "Thu", "Fri"],
      "series": [
        {"name": "Morning",   "values": [42, 55, 38, 60, 72]},
        {"name": "Afternoon", "values": [78, 85, 70, 90, 95]},
        {"name": "Evening",   "values": [55, 62, 48, 68, 80]},
        {"name": "Night",     "values": [20, 18, 22, 15, 25]}
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "categories defines column labels; each series is a row. "
        "series[i].values must have one entry per category. "
        "Set show-labels='true' to print values inside cells, "
        "gap=<px> to control cell spacing, and scale='diverging' for a red-white-blue ramp."
    ),
)

_CORRELATION_MATRIX = ChartTypeDoc(
    type_key="correlation-matrix",
    title="Correlation Matrix",
    category="RELATIONSHIP",
    summary="Symmetric heatmap of pairwise correlation coefficients on a diverging scale.",
    example="""<mj-chart type="correlation-matrix" show-labels="true" style="height:260px">
  <script type="application/json">
    {
      "categories": ["Height", "Weight", "Age", "Income"],
      "series": [
        {"name": "Height", "values": [ 1.00,  0.82,  0.15,  0.31]},
        {"name": "Weight", "values": [ 0.82,  1.00,  0.22,  0.28]},
        {"name": "Age",    "values": [ 0.15,  0.22,  1.00,  0.55]},
        {"name": "Income", "values": [ 0.31,  0.28,  0.55,  1.00]}
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "Values should be in [-1, 1]. The renderer automatically applies a "
        "diverging color scale (red = negative, white = zero, blue = positive). "
        "Set triangle='upper' or 'lower' to show only half the matrix."
    ),
)

_DENSITY_2D = ChartTypeDoc(
    type_key="density-2d",
    title="2D Density",
    category="RELATIONSHIP",
    summary="2D kernel density estimate visualized as a filled heat-surface.",
    example="""<mj-chart type="density-2d" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Observations",
          "points": [
            {"x": 1.1, "y": 2.3}, {"x": 1.4, "y": 2.8}, {"x": 1.8, "y": 3.1},
            {"x": 2.0, "y": 3.5}, {"x": 2.2, "y": 3.2}, {"x": 2.5, "y": 3.8},
            {"x": 2.7, "y": 4.1}, {"x": 3.0, "y": 4.4}, {"x": 3.2, "y": 4.0},
            {"x": 3.5, "y": 4.7}, {"x": 3.8, "y": 5.0}, {"x": 4.0, "y": 4.8},
            {"x": 4.2, "y": 5.3}, {"x": 2.3, "y": 3.0}, {"x": 2.8, "y": 3.6},
            {"x": 3.1, "y": 4.2}, {"x": 1.6, "y": 2.6}, {"x": 2.1, "y": 3.4},
            {"x": 3.4, "y": 4.6}, {"x": 3.9, "y": 4.9}
          ]
        }
      ],
      "density": {"style": "fill", "resolution": 24}
    }
  </script>
</mj-chart>""",
    description=(
        "Accepts model.series[].points=[{x,y}] for KDE computation, or a "
        "pre-computed grid via raw.grid={x:[...], y:[...], z:[[...],...]}. "
        "Control resolution (grid cells), bandwidth, and style via the "
        "raw.density object. style='both' overlays contour lines on the fill."
    ),
)

_CONTOUR = ChartTypeDoc(
    type_key="contour",
    title="Contour Plot",
    category="RELATIONSHIP",
    summary="Iso-contour lines tracing equal-density levels of a 2D distribution.",
    example="""<mj-chart type="contour" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Samples",
          "points": [
            {"x": 0.5, "y": 0.8}, {"x": 1.0, "y": 1.5}, {"x": 1.5, "y": 2.0},
            {"x": 2.0, "y": 2.5}, {"x": 2.5, "y": 3.0}, {"x": 3.0, "y": 3.2},
            {"x": 1.2, "y": 1.8}, {"x": 1.8, "y": 2.3}, {"x": 2.3, "y": 2.8},
            {"x": 2.8, "y": 3.1}, {"x": 0.8, "y": 1.1}, {"x": 1.6, "y": 2.1},
            {"x": 2.1, "y": 2.6}, {"x": 2.6, "y": 3.0}, {"x": 3.2, "y": 3.4},
            {"x": 1.3, "y": 1.9}, {"x": 1.9, "y": 2.4}, {"x": 2.4, "y": 2.9},
            {"x": 0.7, "y": 1.0}, {"x": 3.5, "y": 3.6}
          ]
        }
      ],
      "density": {"style": "contour", "levels": 8, "resolution": 24}
    }
  </script>
</mj-chart>""",
    description=(
        "Uses marching squares to trace iso-contour lines from the KDE grid. "
        "Set density.levels to control the number of contour lines. "
        "Set density.style='both' to combine filled surface with contour lines. "
        "A pre-computed z grid can be supplied via raw.grid."
    ),
)

_HEXBIN = ChartTypeDoc(
    type_key="hexbin",
    title="Hexbin",
    category="RELATIONSHIP",
    summary="Aggregates dense scatter data into hexagonal bins colored by count.",
    example="""<mj-chart type="hexbin" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Observations",
          "points": [
            {"x": 1.0, "y": 2.0}, {"x": 1.2, "y": 2.3}, {"x": 1.1, "y": 1.9},
            {"x": 2.0, "y": 3.5}, {"x": 2.1, "y": 3.4}, {"x": 2.2, "y": 3.6},
            {"x": 3.5, "y": 5.0}, {"x": 3.4, "y": 4.9}, {"x": 3.6, "y": 5.1},
            {"x": 4.0, "y": 6.0}, {"x": 4.1, "y": 6.1}, {"x": 3.9, "y": 5.9},
            {"x": 5.0, "y": 7.5}, {"x": 5.1, "y": 7.4}, {"x": 4.9, "y": 7.6},
            {"x": 1.5, "y": 2.5}, {"x": 2.5, "y": 4.0}, {"x": 3.0, "y": 4.5},
            {"x": 4.5, "y": 6.5}, {"x": 5.5, "y": 8.0}
          ]
        }
      ],
      "hexbin": {"radius": 28, "stat": "count"}
    }
  </script>
</mj-chart>""",
    description=(
        "Points from all series are merged and assigned to hexagonal grid cells. "
        "raw.hexbin.stat controls the per-bin statistic: 'count' (default), 'sum', or 'mean'. "
        "For 'sum' and 'mean' each point must carry a value field. "
        "Set encoding='size' to encode the statistic as hexagon radius instead of fill color."
    ),
)

_SPLOM = ChartTypeDoc(
    type_key="splom",
    title="Scatter Plot Matrix",
    category="RELATIONSHIP",
    summary="N×N grid of scatter sub-plots for every pair of numeric variables.",
    example="""<mj-chart type="splom" style="height:260px">
  <script type="application/json">
    {
      "variables": ["SepalLen", "SepalWid", "PetalLen"],
      "series": [
        {
          "name": "Setosa",
          "points": [
            {"SepalLen": 5.1, "SepalWid": 3.5, "PetalLen": 1.4},
            {"SepalLen": 4.9, "SepalWid": 3.0, "PetalLen": 1.4},
            {"SepalLen": 4.7, "SepalWid": 3.2, "PetalLen": 1.3},
            {"SepalLen": 5.0, "SepalWid": 3.4, "PetalLen": 1.5},
            {"SepalLen": 5.4, "SepalWid": 3.9, "PetalLen": 1.7}
          ]
        },
        {
          "name": "Versicolor",
          "points": [
            {"SepalLen": 7.0, "SepalWid": 3.2, "PetalLen": 4.7},
            {"SepalLen": 6.4, "SepalWid": 3.2, "PetalLen": 4.5},
            {"SepalLen": 6.9, "SepalWid": 3.1, "PetalLen": 4.9},
            {"SepalLen": 6.5, "SepalWid": 2.8, "PetalLen": 4.6},
            {"SepalLen": 5.7, "SepalWid": 2.8, "PetalLen": 4.5}
          ]
        }
      ]
    }
  </script>
</mj-chart>""",
    description=(
        "raw.variables is required: an ordered list of field names present on "
        "each point object. Each series is one group (e.g. species). "
        "Diagonal cells show the variable name; set diagonal='histogram' to add "
        "a marginal histogram. Set triangle='lower' or 'upper' to show half the matrix."
    ),
)

_BEESWARM = ChartTypeDoc(
    type_key="beeswarm",
    title="Beeswarm",
    category="RELATIONSHIP",
    summary="Non-overlapping dot layout along a single continuous axis.",
    example="""<mj-chart type="beeswarm" style="height:260px">
  <script type="application/json">
    {
      "series": [
        {
          "name": "Group A",
          "points": [
            {"x": 12}, {"x": 15}, {"x": 18}, {"x": 20}, {"x": 22},
            {"x": 23}, {"x": 25}, {"x": 27}, {"x": 28}, {"x": 30}
          ]
        },
        {
          "name": "Group B",
          "points": [
            {"x": 30}, {"x": 33}, {"x": 35}, {"x": 37}, {"x": 38},
            {"x": 40}, {"x": 42}, {"x": 45}, {"x": 48}, {"x": 52}
          ]
        }
      ],
      "radius": 5,
      "padding": 1
    }
  </script>
</mj-chart>""",
    description=(
        "Data lives in raw.series (not model.series) as [{name, points:[{x?,y?,label?}]}]. "
        "Use the x field for horizontal orientation (default) or y for vertical. "
        "raw.radius and raw.padding control dot size and gap. "
        "A dashed median line is drawn automatically."
    ),
)


# ---------------------------------------------------------------------------
# Exported catalog
# ---------------------------------------------------------------------------

CHART_TYPES = [
    _HISTOGRAM,
    _DENSITY,
    _FREQUENCY_POLYGON,
    _BOXPLOT,
    _VIOLIN,
    _STRIP,
    _SWARM,
    _RUG,
    _DOT_HISTOGRAM,
    _RIDGELINE,
    _QQ,
    _CDF,
    _SCATTER,
    _BUBBLE,
    _CONNECTED_SCATTER,
    _RESIDUAL,
    _HEATMAP,
    _CORRELATION_MATRIX,
    _DENSITY_2D,
    _CONTOUR,
    _HEXBIN,
    _SPLOM,
    _BEESWARM,
]
