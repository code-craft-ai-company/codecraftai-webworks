"""
    05_scientific_geographic.py

    ChartTypeDoc catalog entries for the Scientific and Geographic chart families.

    Scientific types come from:
        polar.js        -> polar, wind-rose, nightingale, coxcomb
        contour.js      -> surface   (the contour type is documented in _02)
        vectorfield.js  -> vector-field (alias vectorfield), streamline
        spectrogram.js  -> spectrogram
        ternary.js      -> ternary
        phase.js        -> phase-diagram (alias phase)
        freqresponse.js -> nyquist, bode
        smith.js        -> smith
        loglog.js       -> log-log, semi-log

    Geographic types come from:
        geomap.js       -> choropleth, symbol-map, bubble-map,
                           proportional-symbol-map, hex-map, tile-grid-map
        flowmap.js      -> flow-map, route-map, geo-heatmap, isoline, cartogram

    Example data is kept as Python dictionaries and written into each example's
    markup as inline JSON (``<script type="application/json">``) by the shared
    builders of :mod:`testcomponents.charttypes.examplemarkup`, so the
    chart-type page's data presets can read it.
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.charttypes.charttypedoc import ChartTypeDoc
from testcomponents.charttypes.examplemarkup import boolean_option
from testcomponents.charttypes.examplemarkup import chart_example
from testcomponents.charttypes.examplemarkup import events_example
from testcomponents.charttypes.examplemarkup import true_false_option
from testcomponents.charttypes.examplemarkup import with_changes


# ---------------------------------------------------------------------------
# Shared option docs
# ---------------------------------------------------------------------------

_SCALE_VALUES = ["log", "linear"]

_PROJECTION_OPTION = AttributeDoc(
    name="projection",
    description=(
        "Map projection; overrides `meta.projection`. equirectangular scales longitudes by the "
        "cosine of the mid latitude; equal-area is Equal Earth. The central meridian is chosen "
        "so data that crosses the antimeridian stays together."
    ),
    kind="enum",
    values=["equirectangular", "mercator", "equal-area", "natural-earth"],
    default="equirectangular",
)

_FEATURE_KEY_OPTION = AttributeDoc(
    name="feature-key",
    description=(
        "Feature property that holds each feature's id (overrides `featureKey` in the data); "
        "without it the id is `feature.id`, else `properties.id`."
    ),
    kind="string",
    values=["id", "name", "iso_a3"],
)

_SHOW_LABELS_OPTION = boolean_option(
    "show-labels", "Writes each point's `label` next to its mark (otherwise labels are only in "
    "tooltips and the table).")

_MIN_RADIUS_OPTION = AttributeDoc(
    name="min-radius", description="Smallest radius in px of a sized symbol with a positive value.",
    kind="number", default="2")

_MAX_RADIUS_OPTION = AttributeDoc(
    name="max-radius", description="Radius in px of the largest value; others get max-radius x sqrt(value / largest).",
    kind="number", default="28")


# A simplified outline of the contiguous United States, used as a base map.
_US_OUTLINE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "usa",
            "properties": {"name": "United States (simplified)"},
            "geometry": {"type": "Polygon", "coordinates": [[
                [-124.7, 48.4], [-124.2, 42.0], [-120.6, 34.6], [-117.1, 32.5], [-111.0, 31.3],
                [-106.5, 31.8], [-97.4, 25.9], [-94.0, 29.7], [-89.0, 30.2], [-84.9, 29.7],
                [-82.6, 27.5], [-80.1, 25.2], [-80.6, 28.4], [-81.4, 30.7], [-75.5, 35.2],
                [-76.0, 38.9], [-74.0, 40.5], [-70.0, 41.7], [-70.7, 43.1], [-67.0, 44.8],
                [-69.2, 47.4], [-71.5, 45.0], [-75.0, 45.0], [-79.0, 43.3], [-82.5, 41.7],
                [-83.1, 46.3], [-89.0, 48.0], [-95.2, 49.0], [-123.0, 49.0], [-124.7, 48.4],
            ]]},
        },
    ],
}


# ---------------------------------------------------------------------------
# Example data (the basic example of each type first)
# ---------------------------------------------------------------------------

_POLAR_DATA = {
    "thetaUnit": "degrees",
    "fill": True,
    "series": [
        {
            "name": "Signal A",
            "points": [
                {"theta": 0, "r": 3.0},
                {"theta": 45, "r": 5.5},
                {"theta": 90, "r": 7.2},
                {"theta": 135, "r": 4.8},
                {"theta": 180, "r": 2.1},
                {"theta": 225, "r": 3.7},
                {"theta": 270, "r": 6.3},
                {"theta": 315, "r": 4.0},
            ],
        },
        {
            "name": "Signal B",
            "points": [
                {"theta": 0, "r": 6.0},
                {"theta": 45, "r": 3.2},
                {"theta": 90, "r": 5.0},
                {"theta": 135, "r": 7.8},
                {"theta": 180, "r": 5.5},
                {"theta": 225, "r": 2.0},
                {"theta": 270, "r": 4.4},
                {"theta": 315, "r": 6.9},
            ],
        },
    ],
}


_WIND_ROSE_DATA = {
    "directions": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
    "series": [
        {"name": "0-3 m/s", "values": [8, 4, 6, 3, 5, 7, 9, 6]},
        {"name": "3-6 m/s", "values": [12, 7, 5, 4, 6, 10, 14, 11]},
        {"name": "6+ m/s", "values": [5, 2, 1, 1, 2, 4, 8, 6]},
    ],
}


_NIGHTINGALE_DATA = {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "series": [
        {
            "name": "Disease",
            "values": [310, 270, 240, 180, 150, 120, 110, 130, 170, 220, 260, 300],
        },
        {"name": "Wounds", "values": [60, 75, 90, 110, 140, 160, 150, 130, 100, 80, 70, 60]},
        {"name": "Other", "values": [40, 45, 50, 60, 70, 80, 85, 80, 65, 55, 45, 40]},
    ],
}


_COXCOMB_DATA = {
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
        {"name": "Revenue", "values": [4200, 5800, 7100, 6300]},
        {"name": "Cost", "values": [2100, 2800, 3200, 2900]},
    ],
}


_SURFACE_DATA = {
    "meta": {"xLabel": "x", "yLabel": "y", "zLabel": "z"},
    "projection": "isometric",
    "style": "both",
    "grid": {
        "x": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "y": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "z": [
            [0.03, 0.28, 0.55, 0.75, 0.78, 0.59, 0.27, -0.05, -0.27],
            [0.09, 0.49, 1.02, 1.53, 1.7, 1.37, 0.74, 0.16, -0.21],
            [0.21, 0.88, 1.92, 3.01, 3.44, 2.85, 1.64, 0.55, -0.09],
            [0.35, 1.33, 2.94, 4.7, 5.44, 4.54, 2.66, 0.99, 0.05],
            [0.42, 1.53, 3.42, 5.48, 6.36, 5.32, 3.14, 1.2, 0.11],
            [0.35, 1.33, 2.94, 4.7, 5.44, 4.54, 2.66, 0.99, 0.05],
            [0.21, 0.88, 1.92, 3.01, 3.44, 2.85, 1.64, 0.55, -0.09],
            [0.09, 0.49, 1.02, 1.53, 1.7, 1.37, 0.74, 0.16, -0.21],
            [0.03, 0.28, 0.55, 0.75, 0.78, 0.59, 0.27, -0.05, -0.27],
        ],
    },
}


_VECTOR_FIELD_DATA = {
    "meta": {"xLabel": "x", "yLabel": "y"},
    "vectors": [
        {"x": -2, "y": -2, "u": 1.9, "v": -1.6},
        {"x": -1, "y": -2, "u": 1.9, "v": -0.8},
        {"x": 0, "y": -2, "u": 1.9, "v": 0.0},
        {"x": 1, "y": -2, "u": 1.9, "v": 0.8},
        {"x": 2, "y": -2, "u": 1.9, "v": 1.6},
        {"x": -2, "y": -1, "u": 1.1, "v": -1.6},
        {"x": -1, "y": -1, "u": 1.1, "v": -0.8},
        {"x": 0, "y": -1, "u": 1.1, "v": 0.0},
        {"x": 1, "y": -1, "u": 1.1, "v": 0.8},
        {"x": 2, "y": -1, "u": 1.1, "v": 1.6},
        {"x": -2, "y": 0, "u": 0.3, "v": -1.6},
        {"x": -1, "y": 0, "u": 0.3, "v": -0.8},
        {"x": 0, "y": 0, "u": 0.3, "v": 0.0},
        {"x": 1, "y": 0, "u": 0.3, "v": 0.8},
        {"x": 2, "y": 0, "u": 0.3, "v": 1.6},
        {"x": -2, "y": 1, "u": -0.5, "v": -1.6},
        {"x": -1, "y": 1, "u": -0.5, "v": -0.8},
        {"x": 0, "y": 1, "u": -0.5, "v": 0.0},
        {"x": 1, "y": 1, "u": -0.5, "v": 0.8},
        {"x": 2, "y": 1, "u": -0.5, "v": 1.6},
        {"x": -2, "y": 2, "u": -1.3, "v": -1.6},
        {"x": -1, "y": 2, "u": -1.3, "v": -0.8},
        {"x": 0, "y": 2, "u": -1.3, "v": 0.0},
        {"x": 1, "y": 2, "u": -1.3, "v": 0.8},
        {"x": 2, "y": 2, "u": -1.3, "v": 1.6},
    ],
}


_STREAMLINE_DATA = {
    "meta": {"xLabel": "x", "yLabel": "y"},
    "grid": {
        "x": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
        "y": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
        "u": [
            [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
            [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            [-0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0],
            [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5],
            [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0],
            [-1.5, -1.5, -1.5, -1.5, -1.5, -1.5, -1.5, -1.5, -1.5],
            [-2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0],
        ],
        "v": [
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
            [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
        ],
    },
    "seeds": [[2, 2.4], [2, 2.9], [2, 3.4], [2, 3.9]],
}


_SPECTROGRAM_DATA = {
    "scale": "log",
    "timeAxis": {"start": 0.0, "end": 1.0, "bins": 8},
    "freqAxis": {"start": 0, "end": 4000, "bins": 6},
    "power": [
        [0.01, 0.02, 0.05, 0.1, 0.08, 0.03, 0.02, 0.01],
        [0.05, 0.3, 0.8, 0.95, 0.7, 0.2, 0.08, 0.04],
        [0.2, 0.75, 0.99, 0.85, 0.6, 0.4, 0.25, 0.15],
        [0.4, 0.6, 0.8, 0.7, 0.5, 0.55, 0.6, 0.45],
        [0.1, 0.25, 0.4, 0.35, 0.2, 0.3, 0.45, 0.35],
        [0.02, 0.05, 0.08, 0.06, 0.04, 0.07, 0.1, 0.08],
    ],
    "meta": {"xLabel": "Time (s)", "yLabel": "Frequency (Hz)"},
}


_TERNARY_DATA = {
    "meta": {"aLabel": "SiO₂", "bLabel": "Al₂O₃", "cLabel": "MgO"},
    "regions": [
        {
            "name": "Cordierite field",
            "vertices": [
                {"a": 60, "b": 30, "c": 10},
                {"a": 45, "b": 45, "c": 10},
                {"a": 40, "b": 40, "c": 20},
                {"a": 55, "b": 25, "c": 20},
            ],
        },
    ],
    "series": [
        {
            "name": "Samples",
            "points": [
                {"a": 52, "b": 37, "c": 11},
                {"a": 48, "b": 39, "c": 13},
                {"a": 60, "b": 25, "c": 15},
                {"a": 70, "b": 20, "c": 10},
                {"a": 40, "b": 45, "c": 15},
                {"a": 35, "b": 25, "c": 40},
            ],
        },
    ],
}


_PHASE_DIAGRAM_DATA = {
    "meta": {"xLabel": "Temperature (K)", "yLabel": "Pressure (atm)"},
    "yScale": "log",
    "regions": [
        {
            "name": "Solid",
            "path": [[150, 0.0001], [150, 1000], [273.2, 1000], [273.16, 0.006], [200, 0.0002]],
        },
        {
            "name": "Liquid",
            "path": [
                [273.16, 0.006],
                [273.2, 1000],
                [700, 1000],
                [700, 218],
                [647, 218],
                [573, 84.5],
                [473, 15.3],
                [373, 1],
            ],
        },
        {
            "name": "Gas",
            "path": [
                [150, 0.0001],
                [200, 0.0002],
                [273.16, 0.006],
                [373, 1],
                [473, 15.3],
                [573, 84.5],
                [647, 218],
                [700, 218],
                [700, 0.0001],
            ],
        },
    ],
    "boundaries": [
        {"name": "Melting curve", "points": [[273.16, 0.006], [273.2, 1000]]},
        {
            "name": "Vaporisation curve",
            "points": [[273.16, 0.006], [373, 1], [473, 15.3], [573, 84.5], [647, 218]],
        },
        {
            "name": "Sublimation curve",
            "style": "dashed",
            "points": [[150, 0.0001], [200, 0.0002], [273.16, 0.006]],
        },
    ],
    "specialPoints": [
        {"name": "Triple point", "x": 273.16, "y": 0.006},
        {"name": "Critical point", "x": 647, "y": 218},
    ],
}


_NYQUIST_DATA = {
    "criticalPoint": {"re": -1, "im": 0},
    "showUnitCircle": True,
    "series": [
        {
            "name": "G(jω) = 2/(jω+1)³",
            "mirror": True,
            "points": [
                {"omega": 0, "re": 2.0, "im": -0.0},
                {"omega": 0.2, "re": 1.565, "im": -1.053},
                {"omega": 0.4, "re": 0.666, "im": -1.456},
                {"omega": 0.6, "re": -0.064, "im": -1.259},
                {"omega": 0.8, "re": -0.417, "im": -0.856},
                {"omega": 1.0, "re": -0.5, "im": -0.5},
                {"omega": 1.2, "re": -0.457, "im": -0.258},
                {"omega": 1.5, "re": -0.335, "im": -0.066},
                {"omega": 2, "re": -0.176, "im": 0.032},
                {"omega": 3, "re": -0.052, "im": 0.036},
                {"omega": 5, "re": -0.008, "im": 0.013},
            ],
        },
    ],
}


_BODE_DATA = {
    "asymptotes": True,
    "series": [
        {
            "name": "2nd-order low-pass (ζ = 0.5)",
            "points": [
                {"omega": 0.1, "magnitude_db": 0.04, "phase_deg": -5.8},
                {"omega": 0.2, "magnitude_db": 0.17, "phase_deg": -11.8},
                {"omega": 0.5, "magnitude_db": 0.9, "phase_deg": -33.7},
                {"omega": 0.8, "magnitude_db": 1.14, "phase_deg": -65.8},
                {"omega": 1.0, "magnitude_db": 0.0, "phase_deg": -90.0},
                {"omega": 1.25, "magnitude_db": -2.74, "phase_deg": -114.2},
                {"omega": 2, "magnitude_db": -11.14, "phase_deg": -146.3},
                {"omega": 5, "magnitude_db": -27.79, "phase_deg": -168.2},
                {"omega": 10, "magnitude_db": -39.96, "phase_deg": -174.2},
                {"omega": 20, "magnitude_db": -52.03, "phase_deg": -177.1},
                {"omega": 50, "magnitude_db": -67.96, "phase_deg": -178.9},
                {"omega": 100, "magnitude_db": -80.0, "phase_deg": -179.4},
            ],
        },
    ],
}


_SMITH_DATA = {
    "mode": "impedance",
    "grid": {"rLines": [0, 0.2, 0.5, 1.0, 2.0, 5.0], "xLines": [0.2, 0.5, 1.0, 2.0, 5.0]},
    "series": [
        {
            "name": "Antenna input",
            "points": [
                {"freq_hz": 100000000.0, "r": 0.2, "x": 0.8},
                {"freq_hz": 200000000.0, "r": 0.4, "x": 0.5},
                {"freq_hz": 300000000.0, "r": 0.7, "x": 0.2},
                {"freq_hz": 400000000.0, "r": 1.0, "x": 0.0},
                {"freq_hz": 500000000.0, "r": 1.2, "x": -0.3},
                {"freq_hz": 600000000.0, "r": 0.9, "x": -0.6},
                {"freq_hz": 700000000.0, "r": 0.5, "x": -0.9},
            ],
        },
    ],
}


_LOG_LOG_DATA = {
    "series": [
        {
            "name": "y = x²",
            "points": [
                {"x": 1, "y": 1},
                {"x": 2, "y": 4},
                {"x": 5, "y": 25},
                {"x": 10, "y": 100},
                {"x": 20, "y": 400},
                {"x": 50, "y": 2500},
                {"x": 100, "y": 10000},
            ],
        },
        {
            "name": "y = x³",
            "points": [
                {"x": 1, "y": 1},
                {"x": 2, "y": 8},
                {"x": 5, "y": 125},
                {"x": 10, "y": 1000},
                {"x": 20, "y": 8000},
                {"x": 50, "y": 125000},
                {"x": 100, "y": 1000000},
            ],
        },
    ],
    "meta": {"xLabel": "x", "yLabel": "y"},
}


_SEMI_LOG_DATA = {
    "series": [
        {
            "name": "Bacterial count",
            "points": [
                {"x": 0, "y": 100},
                {"x": 1, "y": 200},
                {"x": 2, "y": 400},
                {"x": 3, "y": 800},
                {"x": 4, "y": 1600},
                {"x": 5, "y": 3200},
                {"x": 6, "y": 6400},
                {"x": 7, "y": 12800},
                {"x": 8, "y": 25600},
                {"x": 9, "y": 51200},
                {"x": 10, "y": 102400},
            ],
        },
    ],
    "meta": {"xLabel": "Time (h)", "yLabel": "CFU / mL"},
}


_CHOROPLETH_DATA = {
    "geojson": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "A", "name": "Region A"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-10, 40], [0, 40], [0, 50], [-10, 50], [-10, 40]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "B", "name": "Region B"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 40], [10, 40], [10, 50], [0, 50], [0, 40]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "C", "name": "Region C"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[10, 40], [20, 40], [20, 50], [10, 50], [10, 40]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "D", "name": "Region D"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-10, 30], [5, 30], [5, 40], [-10, 40], [-10, 30]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "E", "name": "Region E"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[5, 30], [20, 30], [20, 40], [5, 40], [5, 30]]],
                },
            },
        ],
    },
    "regions": [
        {"id": "A", "value": 42, "label": "Region A"},
        {"id": "B", "value": 78, "label": "Region B"},
        {"id": "C", "value": 55, "label": "Region C"},
        {"id": "D", "value": 91, "label": "Region D"},
        {"id": "E", "value": 30, "label": "Region E"},
    ],
}


_SYMBOL_MAP_DATA = {
    "markers": [
        {"lat": 48.85, "lng": 2.35, "label": "Paris"},
        {"lat": 51.51, "lng": -0.13, "label": "London"},
        {"lat": 52.52, "lng": 13.4, "label": "Berlin"},
        {"lat": 41.9, "lng": 12.5, "label": "Rome"},
        {"lat": 40.41, "lng": -3.7, "label": "Madrid"},
        {"lat": 47.38, "lng": 8.54, "label": "Zurich"},
        {"lat": 50.85, "lng": 4.35, "label": "Brussels"},
    ],
}


_BUBBLE_MAP_DATA = {
    "markers": [
        {"lat": 40.71, "lng": -74.01, "label": "New York", "value": 8336817},
        {"lat": 34.05, "lng": -118.24, "label": "Los Angeles", "value": 3979576},
        {"lat": 41.88, "lng": -87.63, "label": "Chicago", "value": 2693976},
        {"lat": 29.76, "lng": -95.37, "label": "Houston", "value": 2304580},
        {"lat": 33.45, "lng": -112.07, "label": "Phoenix", "value": 1608139},
        {"lat": 39.95, "lng": -75.17, "label": "Philadelphia", "value": 1584064},
        {"lat": 29.42, "lng": -98.49, "label": "San Antonio", "value": 1434625},
    ],
}


_PROPORTIONAL_SYMBOL_MAP_DATA = {
    "series": [
        {
            "name": "GDP (USD bn)",
            "symbol": "diamond",
            "points": [
                {"lat": 35.68, "lon": 139.69, "label": "Tokyo", "size": 1900},
                {"lat": 37.57, "lon": 126.98, "label": "Seoul", "size": 700},
                {"lat": 31.23, "lon": 121.47, "label": "Shanghai", "size": 660},
                {"lat": 22.4, "lon": 114.11, "label": "HK", "size": 360},
                {"lat": 13.75, "lon": 100.52, "label": "Bangkok", "size": 270},
                {"lat": 1.35, "lon": 103.82, "label": "Singapore", "size": 400},
                {"lat": 14.6, "lon": 121.0, "label": "Manila", "size": 200},
            ],
        },
    ],
}


_HEX_MAP_DATA = {
    "regions": [
        {"id": "NW", "value": 42, "label": "NW"},
        {"id": "N", "value": 68, "label": "N"},
        {"id": "NE", "value": 55, "label": "NE"},
        {"id": "W", "value": 30, "label": "W"},
        {"id": "C", "value": 91, "label": "C"},
        {"id": "E", "value": 75, "label": "E"},
        {"id": "S", "value": 48, "label": "S"},
    ],
    "layout": {
        "NW": {"q": 0, "r": 0},
        "N": {"q": 1, "r": 0},
        "NE": {"q": 2, "r": 0},
        "W": {"q": 0, "r": 1},
        "C": {"q": 1, "r": 1},
        "E": {"q": 2, "r": 1},
        "S": {"q": 1, "r": 2},
    },
}


_TILE_GRID_MAP_DATA = {
    "regions": [
        {"id": "ME", "value": 14, "label": "ME"},
        {"id": "VT", "value": 21, "label": "VT"},
        {"id": "NH", "value": 18, "label": "NH"},
        {"id": "MA", "value": 68, "label": "MA"},
        {"id": "RI", "value": 35, "label": "RI"},
        {"id": "CT", "value": 48, "label": "CT"},
        {"id": "NY", "value": 91, "label": "NY"},
    ],
    "layout": {
        "ME": {"q": 3, "r": 0},
        "VT": {"q": 2, "r": 1},
        "NH": {"q": 3, "r": 1},
        "NY": {"q": 1, "r": 2},
        "MA": {"q": 2, "r": 2},
        "RI": {"q": 3, "r": 2},
        "CT": {"q": 2, "r": 3},
    },
}


_FLOW_MAP_DATA = {
    "nodes": [
        {"id": "NYC", "lon": -74.01, "lat": 40.71, "label": "New York"},
        {"id": "LAX", "lon": -118.24, "lat": 34.05, "label": "Los Angeles"},
        {"id": "CHI", "lon": -87.63, "lat": 41.88, "label": "Chicago"},
        {"id": "MIA", "lon": -80.19, "lat": 25.77, "label": "Miami"},
        {"id": "SEA", "lon": -122.33, "lat": 47.61, "label": "Seattle"},
    ],
    "links": [
        {"source": "NYC", "target": "LAX", "value": 5200},
        {"source": "NYC", "target": "CHI", "value": 3800},
        {"source": "LAX", "target": "SEA", "value": 2100},
        {"source": "CHI", "target": "MIA", "value": 1700},
        {"source": "MIA", "target": "NYC", "value": 2900},
        {"source": "SEA", "target": "CHI", "value": 1400},
    ],
}


_ROUTE_MAP_DATA = {
    "series": [
        {
            "name": "Trans-Atlantic",
            "routes": [
                {
                    "id": "JFK-LHR",
                    "waypoints": [
                        {"lon": -73.78, "lat": 40.64, "label": "JFK"},
                        {"lon": -53.0, "lat": 47.0},
                        {"lon": -30.0, "lat": 52.0},
                        {"lon": -0.46, "lat": 51.48, "label": "LHR"},
                    ],
                },
            ],
        },
        {
            "name": "Pacific Rim",
            "routes": [
                {
                    "id": "LAX-NRT",
                    "waypoints": [
                        {"lon": -118.41, "lat": 33.94, "label": "LAX"},
                        {"lon": -160.0, "lat": 52.0},
                        {"lon": 139.78, "lat": 35.55, "label": "NRT"},
                    ],
                },
            ],
        },
    ],
}


_GEO_HEATMAP_DATA = {
    "series": [
        {
            "name": "Incident density",
            "points": [
                {"lon": 2.35, "lat": 48.85, "weight": 3.0},
                {"lon": 2.4, "lat": 48.88, "weight": 2.5},
                {"lon": 2.3, "lat": 48.82, "weight": 2.0},
                {"lon": 2.33, "lat": 48.87, "weight": 4.0},
                {"lon": 2.38, "lat": 48.84, "weight": 3.5},
                {"lon": 13.4, "lat": 52.52, "weight": 2.0},
                {"lon": 13.45, "lat": 52.5, "weight": 1.8},
                {"lon": 13.38, "lat": 52.54, "weight": 2.2},
                {"lon": -0.13, "lat": 51.51, "weight": 1.5},
                {"lon": -0.1, "lat": 51.54, "weight": 1.2},
            ],
        },
    ],
}


_ISOLINE_DATA = {
    "series": [
        {
            "name": "Temperature (°C)",
            "levels": [10, 15, 20, 25, 30],
            "grid": {
                "lon-min": -10,
                "lon-max": 30,
                "lat-min": 35,
                "lat-max": 60,
                "cols": 5,
                "rows": 4,
                "values": [10, 12, 15, 18, 20, 14, 18, 22, 25, 26, 16, 20, 26, 30, 28, 12, 16, 20, 24, 22],
            },
        },
    ],
}


_CARTOGRAM_DATA = {
    "geojson": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "A", "name": "Region A"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-10, 45], [0, 45], [0, 55], [-10, 55], [-10, 45]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "B", "name": "Region B"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 45], [10, 45], [10, 55], [0, 55], [0, 45]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "C", "name": "Region C"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[10, 45], [20, 45], [20, 55], [10, 55], [10, 45]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "D", "name": "Region D"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-5, 35], [5, 35], [5, 45], [-5, 45], [-5, 35]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"id": "E", "name": "Region E"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[5, 35], [15, 35], [15, 45], [5, 45], [5, 35]]],
                },
            },
        ],
    },
    "regions": [
        {"id": "A", "value": 120},
        {"id": "B", "value": 380},
        {"id": "C", "value": 250},
        {"id": "D", "value": 600},
        {"id": "E", "value": 90},
    ],
}


_POLAR_LINE_DATA = {
    "thetaUnit": "radians",
    "series": [
        {
            "name": "Antenna gain (dBi)",
            "points": [
                {"theta": 0, "r": 9.5}, {"theta": 0.785, "r": 7.1}, {"theta": 1.571, "r": 3.2},
                {"theta": 2.356, "r": None}, {"theta": 3.142, "r": 1.4}, {"theta": 3.927, "r": 2.2},
                {"theta": 4.712, "r": 3.0}, {"theta": 5.498, "r": 7.4},
            ],
        },
    ],
}


_POLAR_RANGE_DATA = {
    "rMin": 2,
    "rMax": 10,
    "series": [
        {
            "name": "Noise level (dB)",
            "points": [
                {"theta": 0, "r": 6.5}, {"theta": 60, "r": 8.2}, {"theta": 120, "r": 1.2},
                {"theta": 180, "r": 4.4}, {"theta": 240, "r": 9.1}, {"theta": 300, "r": 5.0},
            ],
        },
    ],
}


_WIND_ROSE_16_DATA = {
    "directions": [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ],
    "series": [
        {"name": "All speeds", "values": [7, 5, 4, 3, 3, 2, 3, 4, 6, 8, 11, 12, 10, 8, 7, 7]},
    ],
}


_WIND_ROSE_GAPS_DATA = {
    "directions": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
    "series": [
        {"name": "Calm (0-2 m/s)", "values": [4, None, 3, 2, None, 5, 6, 4]},
        {"name": "Breeze (2-8 m/s)", "values": [9, 6, None, 3, 5, 9, 12, 10]},
    ],
}


_NIGHTINGALE_SINGLE_DATA = {
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "series": [{"name": "Support tickets", "values": [140, 118, 126, 131, 109, 42, 35]}],
}


_NIGHTINGALE_GAPS_DATA = {
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
        {"name": "Product A", "values": [120, None, 180, 150]},
        {"name": "Product B", "values": [60, 90, None, 110]},
    ],
}


_COXCOMB_SEASONS_DATA = {
    "categories": ["Winter", "Spring", "Summer", "Autumn"],
    "series": [
        {"name": "Rain (mm)", "values": [210, 160, 90, 230]},
        {"name": "Snow (mm)", "values": [80, 15, 0, 10]},
        {"name": "Hail (mm)", "values": [5, 12, 18, 6]},
    ],
}


_SURFACE_SADDLE_DATA = {
    "meta": {"xLabel": "x", "yLabel": "y", "zLabel": "z = x² − y²"},
    "projection": "oblique",
    "grid": {
        "x": [-2, -1, 0, 1, 2],
        "y": [-2, -1, 0, 1, 2],
        "z": [
            [0, -3, -4, -3, 0],
            [3, 0, -1, 0, 3],
            [4, 1, None, 1, 4],
            [3, 0, -1, 0, 3],
            [0, -3, -4, -3, 0],
        ],
    },
}


_VECTOR_GRID_DATA = {
    "meta": {"xLabel": "x (m)", "yLabel": "y (m)"},
    "grid": {
        "x": [-2, -1, 0, 1, 2],
        "y": [-2, -1, 0, 1, 2],
        "u": [
            [2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0],
            [-1, -1, -1, -1, -1],
            [-2, -2, -2, -2, -2],
        ],
        "v": [
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
        ],
    },
}


_STREAMLINE_VORTEX_DATA = {
    "meta": {"xLabel": "x", "yLabel": "y"},
    "maxSteps": 120,
    "grid": {
        "x": [-2, -1, 0, 1, 2],
        "y": [-2, -1, 0, 1, 2],
        "u": [
            [2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0],
            [-1, -1, -1, -1, -1],
            [-2, -2, -2, -2, -2],
        ],
        "v": [
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
            [-2, -1, 0, 1, 2],
        ],
    },
}


_STREAMLINE_LINES_DATA = {
    "meta": {"xLabel": "Distance (km)", "yLabel": "Height (km)"},
    "lines": [
        [[0, 1.0], [1, 1.1], [2, 1.5], [3, 2.1], [4, 2.2], [5, 1.8], [6, 1.2]],
        [[0, 2.0], [1, 2.1], [2, 2.4], [3, 2.9], [4, 3.0], [5, 2.7], [6, 2.2]],
        [[0, 3.0], [1, 3.0], [2, 3.2], [3, 3.5], [4, 3.6], [5, 3.4], [6, 3.1]],
    ],
}


_SPECTROGRAM_LINEAR_DATA = {
    "scale": "linear",
    "colormap": "grayscale",
    "range": [0, 1],
    "timeAxis": {"start": 0, "end": 2, "bins": 8},
    "freqAxis": {"start": 50, "end": 8000, "bins": 5, "logScale": True},
    "power": [
        [0.9, 0.8, 0.7, 0.6, 0.6, 0.5, 0.4, 0.3],
        [0.2, 0.6, 0.9, None, None, 0.7, 0.5, 0.2],
        [0.1, 0.3, 0.5, 0.8, 0.9, 0.6, 0.3, 0.1],
        [0.0, 0.1, 0.2, 0.4, 0.5, 0.3, 0.1, 0.0],
        [0.0, 0.0, 0.1, 0.1, 0.2, 0.1, 0.0, 0.0],
    ],
    "meta": {"xLabel": "Time (s)", "yLabel": "Frequency (Hz)"},
}


_TERNARY_CONNECTED_DATA = {
    "meta": {"aLabel": "Sand", "bLabel": "Silt", "cLabel": "Clay"},
    "connect": True,
    "series": [
        {
            "name": "Core A (by depth)",
            "points": [
                {"a": 70, "b": 20, "c": 10}, {"a": 55, "b": 30, "c": 15},
                {"a": 40, "b": 38, "c": 22}, {"a": 28, "b": 42, "c": 30},
            ],
        },
        {
            "name": "Core B (by depth)",
            "points": [
                {"a": 20, "b": 65, "c": 15}, {"a": 18, "b": 52, "c": 30},
                {"a": 15, "b": 40, "c": 45}, {"a": 10, "b": 30, "c": 60},
            ],
        },
    ],
}


_TERNARY_EDGE_DATA = {
    "meta": {"aLabel": "Oil", "bLabel": "Water", "cLabel": "Surfactant"},
    "series": [
        {
            "name": "Mixtures (mL)",
            "points": [
                {"a": 2, "b": 6, "c": 2},
                {"a": 30, "b": 30, "c": 40},
                {"a": 0, "b": 0, "c": 0},
                {"a": -5, "b": 50, "c": 55},
                {"a": 10, "b": None, "c": 5},
                {"a": 100, "b": 0, "c": 0},
            ],
        },
    ],
}


_PHASE_LINEAR_DATA = {
    "meta": {"xLabel": "Load (%)", "yLabel": "Inlet temperature (°C)"},
    "regions": [
        {"name": "Safe", "path": [[0, 0], [0, 35], [60, 35], [80, 20], [100, 0]]},
        {"name": "Throttled", "path": [[0, 35], [0, 45], [100, 45], [100, 0], [80, 20], [60, 35]]},
        {"name": "Shutdown", "path": [[0, 45], [0, 60], [100, 60], [100, 45]]},
    ],
    "boundaries": [
        {"name": "Throttle line", "style": "dashed", "points": [[0, 35], [60, 35], [80, 20], [100, 0]]},
        {"name": "Trip line", "style": "dotted", "points": [[0, 45], [100, 45]]},
    ],
    "specialPoints": [{"name": "Design point", "x": 50, "y": 25}],
}


_NYQUIST_FIRST_ORDER_DATA = {
    "criticalPoint": {"re": -0.5, "im": 0},
    "meta": {"xLabel": "Re L(jω)", "yLabel": "Im L(jω)"},
    "series": [
        {
            "name": "L(jω) = 1/(jω+1)",
            "points": [
                {"omega": 0, "re": 1.0, "im": 0.0}, {"omega": 0.25, "re": 0.941, "im": -0.235},
                {"omega": 0.5, "re": 0.8, "im": -0.4}, {"omega": 1, "re": 0.5, "im": -0.5},
                {"omega": 2, "re": 0.2, "im": -0.4}, {"omega": 4, "re": 0.059, "im": -0.235},
                {"omega": 10, "re": 0.01, "im": -0.099},
            ],
        },
        {
            "name": "L(jω) = 2/(jω+1)²",
            "points": [
                {"omega": 0, "re": 2.0, "im": 0.0}, {"omega": 0.25, "re": 1.661, "im": -0.886},
                {"omega": 0.5, "re": 0.96, "im": -1.28}, {"omega": 1, "re": 0.0, "im": -1.0},
                {"omega": 2, "re": -0.24, "im": -0.32}, {"omega": 4, "re": -0.104, "im": -0.055},
                {"omega": 10, "re": -0.019, "im": -0.004},
            ],
        },
    ],
}


_BODE_RE_IM_DATA = {
    "asymptotes": True,
    "meta": {"xLabel": "ω (rad/s)"},
    "series": [
        {
            "name": "H(jω) = 10/(jω+10)",
            "points": [
                {"omega": 0.1, "re": 1.0, "im": -0.01}, {"omega": 1, "re": 0.990, "im": -0.099},
                {"omega": 3, "re": 0.917, "im": -0.275}, {"omega": 10, "re": 0.5, "im": -0.5},
                {"omega": 30, "re": 0.1, "im": -0.3}, {"omega": 100, "re": 0.0099, "im": -0.099},
                {"omega": 1000, "re": 0.0001, "im": -0.01},
            ],
        },
    ],
}


_BODE_TWO_DATA = {
    "series": [
        {
            "name": "Low-pass (linear magnitude)",
            "points": [
                {"omega": 0.1, "magnitude": 1.0, "phase_deg": -0.6},
                {"omega": 1, "magnitude": 0.995, "phase_deg": -5.7},
                {"omega": 10, "magnitude": 0.707, "phase_deg": -45},
                {"omega": 100, "magnitude": 0.0995, "phase_deg": -84.3},
                {"omega": 1000, "magnitude": 0.01, "phase_deg": -89.4},
            ],
        },
        {
            "name": "High-pass (dB)",
            "points": [
                {"omega": 0.1, "magnitude_db": -40.0, "phase_deg": 89.4},
                {"omega": 1, "magnitude_db": -20.0, "phase_deg": 84.3},
                {"omega": 10, "magnitude_db": -3.0, "phase_deg": 45},
                {"omega": 100, "magnitude_db": -0.04, "phase_deg": 5.7},
                {"omega": 1000, "magnitude_db": 0.0, "phase_deg": 0.6},
            ],
        },
    ],
}


_SMITH_OHMS_DATA = {
    "meta": {"z0": 50},
    "mode": "both",
    "series": [
        {
            "name": "Matching network (Ω)",
            "points": [
                {"freq_hz": 900000000.0, "R": 25, "X": 30},
                {"freq_hz": 1800000000.0, "R": 40, "X": 10},
                {"freq_hz": 2400000000.0, "R": 50, "X": 0},
                {"freq_hz": 3500000000.0, "R": 75, "X": -25},
            ],
        },
    ],
}


_SMITH_GAMMA_DATA = {
    "grid": {"rLines": [0, 0.5, 1, 2], "xLines": [0.5, 1, 2]},
    "series": [
        {
            "name": "S11 port 1",
            "points": [
                {"freq_hz": 1000000000.0, "gamma_re": 0.6, "gamma_im": 0.3},
                {"freq_hz": 2000000000.0, "gamma_re": 0.2, "gamma_im": 0.4},
                {"freq_hz": 3000000000.0, "gamma_re": -0.1, "gamma_im": 0.2},
                {"freq_hz": 4000000000.0, "gamma_re": -0.2, "gamma_im": -0.1},
            ],
        },
        {
            "name": "S22 port 2",
            "points": [
                {"freq_hz": 1000000000.0, "g": 0.5, "b": 0.5},
                {"freq_hz": 2000000000.0, "g": 1.0, "b": 0.2},
                {"freq_hz": 3000000000.0, "g": 1.5, "b": -0.4},
            ],
        },
    ],
}


_LOG_LOG_DROPPED_DATA = {
    "meta": {"xLabel": "Frequency (Hz)", "yLabel": "Power spectral density"},
    "series": [
        {
            "name": "1/f noise",
            "points": [
                {"x": 0, "y": 5}, {"x": 1, "y": 1.0}, {"x": 10, "y": 0.1}, {"x": 100, "y": 0.01},
                {"x": 300, "y": None}, {"x": 1000, "y": 0.001}, {"x": 5000, "y": -0.0002},
                {"x": 10000, "y": 0.0001},
            ],
        },
    ],
}


_SEMI_LOG_LOG_X_DATA = {
    "meta": {"xLabel": "Dose (mg)", "yLabel": "Response (%)"},
    "series": [
        {
            "name": "Drug A",
            "points": [
                {"x": 0.1, "y": 3}, {"x": 0.3, "y": 9}, {"x": 1, "y": 24}, {"x": 3, "y": 50},
                {"x": 10, "y": 76}, {"x": 30, "y": 91}, {"x": 100, "y": 97},
            ],
        },
        {
            "name": "Drug B",
            "points": [
                {"x": 0.1, "y": 1}, {"x": 0.3, "y": 2}, {"x": 1, "y": 7}, {"x": 3, "y": 18},
                {"x": 10, "y": 42}, {"x": 30, "y": 70}, {"x": 100, "y": 88},
            ],
        },
    ],
}


_SEMI_LOG_DECAY_DATA = {
    "meta": {"xLabel": "Time (days)", "yLabel": "Activity (MBq)"},
    "series": [
        {
            "name": "Iodine-131",
            "points": [
                {"x": 0, "y": 1000}, {"x": 8, "y": 500}, {"x": 16, "y": 250}, {"x": 24, "y": 125},
                {"x": 32, "y": 62.5}, {"x": 40, "y": 31.3},
            ],
        },
        {
            "name": "Technetium-99m",
            "points": [
                {"x": 0, "y": 1000}, {"x": 1, "y": 63}, {"x": 2, "y": 4}, {"x": 3, "y": 0.25},
            ],
        },
    ],
}

_CHOROPLETH_DIVERGING_DATA = with_changes(
    _CHOROPLETH_DATA,
    scheme="diverging",
    midpoint=0,
    classes=4,
    regions=[
        {"id": "A", "value": -12, "label": "Region A"},
        {"id": "B", "value": 4, "label": "Region B"},
        {"id": "C", "value": 9, "label": "Region C"},
        {"id": "D", "value": -3, "label": "Region D"},
        {"id": "E", "value": 15, "label": "Region E"},
    ],
)


_CHOROPLETH_BY_NAME_DATA = {
    "meta": {"projection": "mercator"},
    "geojson": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Northland"},
                "geometry": {"type": "Polygon", "coordinates": [[[4, 58], [12, 58], [12, 64], [4, 64], [4, 58]]]},
            },
            {
                "type": "Feature",
                "properties": {"name": "Westmark"},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 52], [6, 52], [6, 58], [0, 58], [0, 52]]]},
            },
            {
                "type": "Feature",
                "properties": {"name": "Eastvale"},
                "geometry": {"type": "Polygon", "coordinates": [[[6, 52], [14, 52], [14, 58], [6, 58], [6, 52]]]},
            },
            {
                "type": "Feature",
                "properties": {"name": "River Line"},
                "geometry": {"type": "LineString", "coordinates": [[2, 50], [7, 54], [13, 56]]},
            },
        ],
    },
    "regions": [
        {"id": "Northland", "value": 18.2},
        {"id": "Eastvale", "value": 7.5},
        {"id": "River Line", "value": 12.0},
    ],
}


_SYMBOL_SERIES_DATA = {
    "series": [
        {
            "name": "Airports",
            "symbol": "square",
            "points": [
                {"id": "CDG", "label": "Paris CDG", "lat": 49.01, "lon": 2.55},
                {"id": "FRA", "label": "Frankfurt", "lat": 50.04, "lon": 8.56},
                {"id": "MAD", "label": "Madrid", "lat": 40.49, "lon": -3.57},
            ],
        },
        {
            "name": "Rail hubs",
            "symbol": "triangle",
            "points": [
                {"id": "ZRH", "label": "Zurich HB", "lat": 47.38, "lon": 8.54},
                {"id": "MIL", "label": "Milano C.", "lat": 45.49, "lon": 9.2},
                {"id": "BRU", "label": "Brussels", "lat": 50.85, "lon": 4.35},
            ],
        },
    ],
}


_SYMBOL_SIZED_DATA = {
    "markers": [
        {"lat": 48.85, "lng": 2.35, "label": "Paris", "value": 2.1},
        {"lat": 51.51, "lng": -0.13, "label": "London", "value": 8.9},
        {"lat": 52.52, "lng": 13.4, "label": "Berlin", "value": 3.7},
        {"lat": 41.9, "lng": 12.5, "label": "Rome", "value": 2.8},
        {"lat": 40.41, "lng": -3.7, "label": "Madrid", "value": 3.3},
    ],
}


_BUBBLE_BASE_MAP_DATA = with_changes(_BUBBLE_MAP_DATA, geojson=_US_OUTLINE)


_PROPORTIONAL_SHAPES_DATA = {
    "series": [
        {
            "name": "Solar (MW)",
            "symbol": "square",
            "points": [
                {"label": "Seville", "lat": 37.39, "lon": -5.98, "size": 1200},
                {"label": "Lisbon", "lat": 38.72, "lon": -9.14, "size": 640},
                {"label": "Marseille", "lat": 43.3, "lon": 5.37, "size": 410},
            ],
        },
        {
            "name": "Wind (MW)",
            "symbol": "triangle",
            "points": [
                {"label": "Aberdeen", "lat": 57.15, "lon": -2.09, "size": 1500},
                {"label": "Esbjerg", "lat": 55.47, "lon": 8.45, "size": 2100},
                {"label": "Rotterdam", "lat": 51.92, "lon": 4.48, "size": 760},
            ],
        },
    ],
}


_TILE_GRID_GAPS_DATA = {
    "regions": [
        {"id": "WA", "value": 62, "label": "WA"},
        {"id": "OR", "value": 48, "label": "OR"},
        {"id": "ID", "value": None, "label": "ID"},
        {"id": "CA", "value": 91, "label": "CA"},
        {"id": "NV", "value": 35, "label": "NV"},
        {"id": "AK", "value": 22, "label": "AK"},
        {"id": "HI", "value": 40, "label": "HI"},
    ],
    "layout": {
        "WA": {"q": 0, "r": 0},
        "ID": {"q": 1, "r": 0},
        "OR": {"q": 0, "r": 1},
        "NV": {"q": 1, "r": 1},
        "CA": {"q": 0, "r": 2},
    },
}


_FLOW_MAP_BASE_DATA = with_changes(_FLOW_MAP_DATA, geojson=_US_OUTLINE)


_ROUTE_MAP_BASE_DATA = {
    "geojson": _US_OUTLINE,
    "series": [
        {
            "name": "Freight",
            "routes": [
                {
                    "id": "I-80 corridor",
                    "waypoints": [
                        {"lon": -122.27, "lat": 37.8, "label": "Oakland"},
                        {"lon": -111.89, "lat": 40.76, "label": "Salt Lake City"},
                        {"lon": -95.94, "lat": 41.26, "label": "Omaha"},
                        {"lon": -87.63, "lat": 41.88, "label": "Chicago"},
                        {"lon": -74.17, "lat": 40.74, "label": "Newark"},
                    ],
                },
            ],
        },
        {
            "name": "Coastal",
            "routes": [
                {
                    "id": "I-95 corridor",
                    "waypoints": [
                        {"lon": -80.19, "lat": 25.77, "label": "Miami"},
                        {"lon": -81.66, "lat": 30.33, "label": "Jacksonville"},
                        {"lon": -77.44, "lat": 37.54, "label": "Richmond"},
                        {"lon": -71.06, "lat": 42.36, "label": "Boston"},
                    ],
                },
            ],
        },
    ],
}


_GEO_HEATMAP_US_DATA = {
    "geojson": _US_OUTLINE,
    "series": [
        {
            "name": "Store visits",
            "points": [
                {"lon": -74.0, "lat": 40.7, "weight": 5}, {"lon": -73.8, "lat": 40.9, "weight": 3},
                {"lon": -87.6, "lat": 41.9, "weight": 4}, {"lon": -87.9, "lat": 42.0, "weight": 2},
                {"lon": -118.2, "lat": 34.1, "weight": 5}, {"lon": -117.9, "lat": 33.8, "weight": 3},
                {"lon": -95.4, "lat": 29.8, "weight": 3}, {"lon": -84.4, "lat": 33.7, "weight": 2},
                {"lon": -122.4, "lat": 37.8, "weight": 4}, {"lon": -104.9, "lat": 39.7, "weight": 1},
            ],
        },
    ],
}


_ISOLINE_AUTO_DATA = {
    "series": [
        {
            "name": "Rainfall (mm)",
            "grid": {
                "lon-min": 0, "lon-max": 12,
                "lat-min": 44, "lat-max": 52,
                "cols": 6, "rows": 5,
                "values": [
                    40, 55, 70, 80, 75, 60,
                    50, 75, 95, 110, 90, 70,
                    55, 85, 120, 140, 105, 75,
                    45, 70, 95, 100, 85, 65,
                    35, 50, 60, 65, 60, 50,
                ],
            },
        },
    ],
}


_ISOLINE_HOLES_DATA = {
    "series": [
        {
            "name": "Sea depth (m)",
            "levels": [50, 100, 150],
            "grid": {
                "lon-min": -6, "lon-max": 4,
                "lat-min": 47, "lat-max": 52,
                "cols": 6, "rows": 5,
                "values": [
                    20, 45, 80, 110, 140, 160,
                    30, 60, 95, 125, 150, 170,
                    35, 70, None, 130, 155, 175,
                    30, 65, 100, 135, 150, 165,
                    25, 55, 90, 120, 145, 155,
                ],
            },
        },
    ],
}


# ---------------------------------------------------------------------------
# Scientific
# ---------------------------------------------------------------------------

_POLAR_FAMILY_NOTE = (
    "<p>Angles run clockwise from the top (0° is north). Null or non-numeric values are "
    "gaps (no wedge, a broken line), never zero. The legend hides and shows series.</p>"
)

_SCIENTIFIC = [

    # ── polar ──────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="polar",
        title="Polar",
        category="scientific",
        summary="Line or filled area of (theta, r) points on a circular grid, 0° at the top, clockwise.",
        description=(
            "Each series supplies points with an angle theta (degrees by default, radians with "
            "thetaUnit) and a radius r. Line mode draws an open path that closes only when the "
            "points span a full turn; area mode (fill: true in the data, or fill=\"true\") draws "
            "a closed, filled region. The radial axis runs from rMin (default the smaller of 0 "
            "and the data minimum) to rMax; values below rMin sit at the centre. Null r values "
            "are gaps. Points are focusable and emit mj-chart-polar-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  thetaUnit?: \"degrees\" | \"radians\",   // default \"degrees\"\n"
            "  fill?: boolean,                       // area mode (the fill attribute wins)\n"
            "  rMin?: number, rMax?: number,         // radial domain\n"
            "  series: [{ name: string, color?: string,\n"
            "             points: [{ theta: number, r: number | null }] }]\n"
            "}</code></pre>" + _POLAR_FAMILY_NOTE
        ),
        options=[
            true_false_option("fill", "`true` (or a bare `fill`) fills each series as a closed area, "
                              "`false` draws open lines; absent, the data's `fill` decides.", None),
        ],
        examples=[
            chart_example(
                "basic", "Filled areas",
                "<p>Two filled series in degrees with a legend; hover a point for its value, "
                "toggle a series in the legend.</p>",
                "polar", _POLAR_DATA, legend=True),
            chart_example(
                "line-gaps", "Line in radians with a gap",
                "<p>Line mode with <code>thetaUnit: \"radians\"</code>: the path stays open "
                "because the points do not span a full turn, and the null at 135° breaks it. "
                "Set <em>fill</em> to <code>true</code> in Controls to close it.</p>",
                "polar", _POLAR_LINE_DATA),
            chart_example(
                "radial-range", "Fixed radial range",
                "<p><code>rMin: 2</code> and <code>rMax: 10</code> fix the rings; the 1.2 dB "
                "reading lies below <code>rMin</code> and is drawn at the centre. The "
                "<code>fill=\"true\"</code> attribute turns on area mode.</p>",
                "polar", _POLAR_RANGE_DATA, attributes={"fill": "true"}),
            events_example(
                "polar", _POLAR_DATA, ["mj-chart-polar-click"],
                "<p>Every point emits <code>mj-chart-polar-click</code> "
                "<code>{ series, theta, r }</code> on click or Enter; the script shows the "
                "detail under the chart and clicks the first point once drawn.</p>",
                legend=True),
        ],
    ),

    # ── wind-rose ──────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="wind-rose",
        title="Wind Rose",
        category="scientific",
        summary="Directional frequency chart: stacked petals per compass direction, north at the top.",
        description=(
            "directions lists the compass sectors clockwise from north and every series gives "
            "one value per direction; each series is a speed bin stacked outward, so petal "
            "LENGTH is the stacked total. Null values are skipped. Each petal is focusable and "
            "emits mj-chart-windrose-click; the legend names and toggles the bins."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  directions: string[],                 // clockwise from north\n"
            "  series: [{ name: string, color?: string,\n"
            "             values: (number | null)[] }] // one per direction\n"
            "}</code></pre>" + _POLAR_FAMILY_NOTE
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Three speed bins",
                "<p>Eight directions and three stacked speed bins with a legend.</p>",
                "wind-rose", _WIND_ROSE_DATA, legend=True),
            chart_example(
                "sixteen-points", "16 directions, one bin",
                "<p>A single series over the 16-point compass: petal length is the "
                "frequency.</p>",
                "wind-rose", _WIND_ROSE_16_DATA, height=300),
            chart_example(
                "gaps", "Missing readings",
                "<p>Null values draw no wedge for that bin; the other bin still stacks from "
                "the centre.</p>",
                "wind-rose", _WIND_ROSE_GAPS_DATA, legend=True),
            events_example(
                "wind-rose", _WIND_ROSE_DATA, ["mj-chart-windrose-click"],
                "<p>Petals emit <code>mj-chart-windrose-click</code> "
                "<code>{ series, value, direction }</code>.</p>",
                legend=True),
        ],
    ),

    # ── nightingale ────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="nightingale",
        title="Nightingale Rose",
        category="scientific",
        summary="Polar area chart: equal-angle sectors per category whose AREA encodes the value.",
        description=(
            "Each category gets an equal sector, starting at the top and running clockwise; "
            "series stack outward on a square-root radius scale, so sector area (not radius) "
            "is proportional to the value. Supply categories and series values aligned to them. "
            "Null values are skipped. Sectors emit mj-chart-nightingale-click. The type key "
            "coxcomb is the same chart."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  categories: string[],                 // one sector each, clockwise from the top\n"
            "  series: [{ name: string, color?: string,\n"
            "             values: (number | null)[] }]\n"
            "}</code></pre>" + _POLAR_FAMILY_NOTE
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Twelve months, three causes",
                "<p>Monthly causes stacked per sector, in the style of Nightingale's "
                "diagram.</p>",
                "nightingale", _NIGHTINGALE_DATA, legend=True, height=300),
            chart_example(
                "single-series", "One series",
                "<p>One value per weekday; compare Monday (140) with Sunday (35): the area, "
                "not the radius, is four times larger.</p>",
                "nightingale", _NIGHTINGALE_SINGLE_DATA),
            chart_example(
                "gaps", "Null values",
                "<p>Q2 of Product A and Q3 of Product B are null and draw no sector.</p>",
                "nightingale", _NIGHTINGALE_GAPS_DATA, legend=True),
            events_example(
                "nightingale", _NIGHTINGALE_DATA, ["mj-chart-nightingale-click"],
                "<p>Sectors emit <code>mj-chart-nightingale-click</code> "
                "<code>{ series, value, category }</code>.</p>",
                legend=True, height=300),
        ],
    ),

    # ── coxcomb ────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="coxcomb",
        title="Coxcomb",
        category="scientific",
        summary="Alias of the Nightingale rose: equal-angle sectors whose area encodes the value.",
        description=(
            "Same renderer, data and events as nightingale: categories with series values "
            "stacked in equal-angle sectors on a square-root radius scale. Sectors emit "
            "mj-chart-nightingale-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  categories: string[],\n"
            "  series: [{ name: string, color?: string, values: (number | null)[] }]\n"
            "}</code></pre>" + _POLAR_FAMILY_NOTE
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Quarterly revenue and cost",
                "<p>Four quarters, two stacked series.</p>",
                "coxcomb", _COXCOMB_DATA, legend=True),
            chart_example(
                "seasons", "Seasonal precipitation",
                "<p>Three stacked series; a zero (summer snow) adds no wedge.</p>",
                "coxcomb", _COXCOMB_SEASONS_DATA, legend=True),
            events_example(
                "coxcomb", _COXCOMB_DATA, ["mj-chart-nightingale-click"],
                "<p>Sectors emit <code>mj-chart-nightingale-click</code> "
                "<code>{ series, value, category }</code>.</p>",
                legend=True),
        ],
    ),

    # ── surface ────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="surface",
        title="Surface",
        category="scientific",
        summary="Shaded 3-D projection of a z = f(x, y) height field with floor axes and a colour bar.",
        description=(
            "grid.z[row][col] is the height at (grid.x[col], grid.y[row]); a cell that is not a "
            "finite number is a hole and the faces touching it are not drawn. The projection "
            "(isometric or oblique) and the drawing style (shaded, wireframe or both) come from "
            "the projection and variant attributes, else the data. Faces are painted far to "
            "near, the drawing is fitted to the chart, the floor axes carry ticks and "
            "meta.xLabel / yLabel / zLabel, and a colour bar explains the heights. Each face "
            "emits mj-chart-surface-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  grid: { x: number[], y: number[],\n"
            "          z: (number | null)[][] },      // z[row][col] at (x[col], y[row])\n"
            "  projection?: \"isometric\" | \"oblique\",   // the projection attribute wins\n"
            "  style?: \"shaded\" | \"wireframe\" | \"both\", // the variant attribute wins\n"
            "  meta?: { xLabel?, yLabel?, zLabel? }\n"
            "}</code></pre>"
            "<p>x and y need at least two values each. Defaults: isometric, shaded.</p>"
        ),
        options=[
            AttributeDoc(name="variant", description="Drawing style; overrides the data's `style`.",
                         kind="enum", values=["shaded", "wireframe", "both"], default="shaded"),
            AttributeDoc(name="projection", description="Projection; overrides the data's `projection`.",
                         kind="enum", values=["isometric", "oblique"], default="isometric"),
        ],
        examples=[
            chart_example(
                "basic", "Shaded with wire grid",
                "<p>A Gaussian hill drawn isometric with <code>style: \"both\"</code>; hover a "
                "face for its corner heights.</p>",
                "surface", _SURFACE_DATA, height=300),
            chart_example(
                "wireframe", "Wireframe variant",
                "<p><code>variant=\"wireframe\"</code> overrides the data's style: grid lines "
                "only.</p>",
                "surface", _SURFACE_DATA, attributes={"variant": "wireframe"}, height=300),
            chart_example(
                "oblique-hole", "Oblique saddle with a hole",
                "<p>An oblique projection of z = x² − y²; the null centre cell leaves a hole of "
                "four missing faces.</p>",
                "surface", _SURFACE_SADDLE_DATA, height=300),
            events_example(
                "surface", _SURFACE_DATA, ["mj-chart-surface-click"],
                "<p>Faces emit <code>mj-chart-surface-click</code> <code>{ row, col, x0, x1, "
                "y0, y1, corners, zAvg }</code>.</p>",
                height=300),
        ],
    ),

    # ── vector-field ───────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="vector-field",
        title="Vector Field",
        category="scientific",
        summary="Quiver plot: arrows showing a 2-D field's direction and magnitude at sample points.",
        description=(
            "Supply vectors with a position (x, y) and components (u along x, v along y; the y "
            "axis points up), or the structured grid form with u[row][col] and v[row][col]. "
            "Arrow length and colour encode the magnitude (square-root colour scale, colour bar "
            "on the right); normalize: true draws equal-length arrows and scale multiplies the "
            "length. Arrows emit mj-chart-vector-click. The type key vectorfield is an alias."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  vectors: [{ x: number, y: number, u: number, v: number }]\n"
            "  // or: grid: { x: number[], y: number[], u: number[][], v: number[][] }\n"
            "  normalize?: boolean,                  // equal-length arrows\n"
            "  scale?: number,                       // length factor (default 1)\n"
            "  meta?: { xLabel?, yLabel? }\n"
            "}</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Sampled vectors",
                "<p>Twenty-five arrows of a shear flow; colour and length both show the "
                "magnitude.</p>",
                "vector-field", _VECTOR_FIELD_DATA, height=300),
            chart_example(
                "grid", "Structured grid",
                "<p>The same kind of field given as <code>grid.u</code> / <code>grid.v</code> "
                "matrices (a rotating, vortex-like flow); the centre vector is zero.</p>",
                "vector-field", _VECTOR_GRID_DATA, height=300),
            chart_example(
                "normalized", "Normalised arrows",
                "<p><code>normalize: true</code> with <code>scale: 0.8</code>: every arrow has "
                "the same length, so only colour shows the magnitude.</p>",
                "vector-field", with_changes(_VECTOR_GRID_DATA, normalize=True, scale=0.8), height=300),
            events_example(
                "vector-field", _VECTOR_FIELD_DATA, ["mj-chart-vector-click"],
                "<p>Arrows emit <code>mj-chart-vector-click</code> <code>{ x, y, u, v, "
                "magnitude }</code>.</p>",
                height=300),
        ],
    ),

    # ── streamline ─────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="streamline",
        title="Streamline",
        category="scientific",
        summary="Flow lines traced through a 2-D vector field (RK4, both directions from each seed).",
        description=(
            "Give a grid with u and v matrices, optionally with seeds; each line is integrated "
            "with RK4 in both directions from its seed, stepSize data units per step (default "
            "a fifth of the smallest grid cell) for up to maxSteps steps each way (default "
            "200). Without seeds the domain is seeded on a regular lattice. Lines with a grid "
            "are coloured by mean speed and the axes cover the grid. Pre-computed polylines can "
            "be given as lines instead. Lines emit mj-chart-streamline-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  grid: { x: number[], y: number[], u: number[][], v: number[][] },\n"
            "  seeds?: [[x, y], ...],                // default: a regular lattice\n"
            "  stepSize?: number, maxSteps?: number, // max 5000\n"
            "  meta?: { xLabel?, yLabel? }\n"
            "}\n"
            "// or pre-computed lines:\n"
            "{ lines: [[[x, y] | { x, y }, ...], ...] }</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Seeded lines",
                "<p>Four seeds in a shear field, each traced both ways and coloured by mean "
                "speed.</p>",
                "streamline", _STREAMLINE_DATA, height=300),
            chart_example(
                "auto-seeds", "Automatic seeds",
                "<p>No <code>seeds</code>: the renderer seeds a regular lattice over a vortex; "
                "the lines circle the centre and <code>maxSteps: 120</code> limits each "
                "line.</p>",
                "streamline", _STREAMLINE_VORTEX_DATA, height=300),
            chart_example(
                "lines", "Pre-computed lines",
                "<p>Three polylines given as <code>lines</code> (no field, one colour).</p>",
                "streamline", _STREAMLINE_LINES_DATA, height=300),
            events_example(
                "streamline", _STREAMLINE_DATA, ["mj-chart-streamline-click"],
                "<p>Lines emit <code>mj-chart-streamline-click</code> <code>{ index, seed, "
                "points, meanSpeed }</code>.</p>",
                height=300),
        ],
    ),

    # ── spectrogram ────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="spectrogram",
        title="Spectrogram",
        category="scientific",
        summary="Time vs frequency intensity grid with a sequential or greyscale colour map.",
        description=(
            "power[freqBin][timeBin] holds the intensity, row 0 being the lowest frequency; "
            "timeAxis and freqAxis give start, end and bin counts (freqAxis.logScale spaces "
            "the rows logarithmically). scale: \"log\" colours 10 log10(power) in dB (cells <= 0 "
            "sit at the floor and do not stretch the scale); range fixes the colour range in "
            "the displayed unit and colormap picks sequential or grayscale. Null cells are "
            "gaps. The grid is one focusable mark: the pointer or the arrow keys pick a cell "
            "and click or Enter emits mj-chart-spectrogram-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  power: (number | null)[][],           // power[freqBin][timeBin]\n"
            "  timeAxis?: { start?, end?, bins? },   // default 0 .. bins\n"
            "  freqAxis?: { start?, end?, bins?, logScale?: boolean },\n"
            "  scale?: \"linear\" | \"log\",            // log: 10 log10(power) dB\n"
            "  colormap?: \"sequential\" | \"grayscale\",\n"
            "  range?: [min, max],                   // colour range, displayed unit\n"
            "  meta?: { xLabel?, yLabel? }\n"
            "}</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Power in dB",
                "<p>Six frequency bins over one second with <code>scale: \"log\"</code>; hover "
                "the grid to read a cell.</p>",
                "spectrogram", _SPECTROGRAM_DATA),
            chart_example(
                "grayscale-gaps", "Greyscale, log frequency, gaps",
                "<p><code>colormap: \"grayscale\"</code>, a fixed <code>range</code>, "
                "logarithmic frequency rows and two null cells (gaps).</p>",
                "spectrogram", _SPECTROGRAM_LINEAR_DATA),
            events_example(
                "spectrogram", _SPECTROGRAM_DATA, ["mj-chart-spectrogram-click"],
                "<p>Click a cell, or focus the grid, move with the arrow keys and press Enter: "
                "<code>mj-chart-spectrogram-click</code> <code>{ timeBin, freqBin, time, "
                "frequency, power, value }</code> (value in the displayed unit).</p>"),
        ],
    ),

    # ── ternary ────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="ternary",
        title="Ternary",
        category="scientific",
        summary="Three-component composition diagram on a triangle (a + b + c = 100%).",
        description=(
            "Each point has a, b and c; the components are normalised by their total, and a "
            "point with a negative or missing component or a zero total is skipped. A is the "
            "bottom-left vertex (read on the left edge), B bottom-right (bottom edge) and C the "
            "top (right edge). meta.aLabel / bLabel / cLabel name the components, regions "
            "shade named fields and connect: true (or connect=\"true\") joins each series' "
            "points in order. Points emit mj-chart-ternary-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  meta?: { aLabel?, bLabel?, cLabel? },  // default \"A\", \"B\", \"C\"\n"
            "  series: [{ name, color?, points: [{ a, b, c }] }],\n"
            "  regions?: [{ name, color?, vertices: [{ a, b, c }] }],\n"
            "  connect?: boolean                     // the connect attribute wins\n"
            "}</code></pre>"
        ),
        options=[
            true_false_option("connect", "`true` (or a bare `connect`) joins each series' points in "
                              "order; absent, the data's `connect` decides.", None),
        ],
        examples=[
            chart_example(
                "basic", "Samples and a field",
                "<p>Oxide compositions with a shaded stability field.</p>",
                "ternary", _TERNARY_DATA, height=300),
            chart_example(
                "connected", "Connected trajectories",
                "<p>Two soil cores sampled by depth, joined in order "
                "(<code>connect: true</code>), with a legend.</p>",
                "ternary", _TERNARY_CONNECTED_DATA, height=300, legend=True),
            chart_example(
                "edge-data", "Raw amounts and invalid points",
                "<p>Components in millilitres are normalised (2 : 6 : 2 becomes 20 : 60 : 20); "
                "the all-zero, negative and null rows are skipped, so three points are "
                "drawn.</p>",
                "ternary", _TERNARY_EDGE_DATA, height=300),
            events_example(
                "ternary", _TERNARY_DATA, ["mj-chart-ternary-click"],
                "<p>Points emit <code>mj-chart-ternary-click</code> <code>{ series, a, b, c "
                "}</code> with the values as given.</p>",
                height=300),
        ],
    ),

    # ── phase-diagram ──────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="phase-diagram",
        title="Phase Diagram",
        category="scientific",
        summary="Regime map with named filled regions, boundary curves and special points.",
        description=(
            "regions are polygons drawn back to front in array order (a region without a "
            "colour gets its own palette colour and a legend entry); boundaries are polylines "
            "with a solid, dashed or dotted style (curve: \"monotone-x\" smooths them); "
            "specialPoints are labelled dots. xScale / yScale (or the scale-x / scale-y "
            "attributes) choose linear or log axes; on a log axis a coordinate <= 0 is drawn "
            "at the floor. The domain covers every region, boundary and point. Regions, "
            "boundaries and points each emit their own click event. The type key phase is an "
            "alias."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  meta?: { xLabel?, yLabel? },\n"
            "  xScale?: \"linear\" | \"log\", yScale?: \"linear\" | \"log\",\n"
            "  regions?: [{ name, color?, path: [[x, y], ...] }],\n"
            "  boundaries?: [{ name, style?: \"solid\" | \"dashed\" | \"dotted\",\n"
            "                  curve?: \"monotone-x\", points: [[x, y], ...] }],\n"
            "  specialPoints?: [{ name, x, y }]\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="scale-x", description="x axis scale; overrides the data's `xScale`.",
                         kind="enum", values=_SCALE_VALUES, default="linear"),
            AttributeDoc(name="scale-y", description="y axis scale; overrides the data's `yScale`.",
                         kind="enum", values=_SCALE_VALUES, default="linear"),
        ],
        examples=[
            chart_example(
                "basic", "Water (log pressure)",
                "<p>Solid, liquid and gas regions of water on a log pressure axis, with the "
                "triple and critical points and a legend of regions.</p>",
                "phase-diagram", _PHASE_DIAGRAM_DATA, height=300, legend=True),
            chart_example(
                "linear", "Operating envelope",
                "<p>Linear axes, dashed and dotted boundaries and a design point: a "
                "machine's safe, throttled and shutdown regimes. Try <em>scale-y</em> = "
                "<code>log</code> in Controls.</p>",
                "phase-diagram", _PHASE_LINEAR_DATA, height=300, legend=True),
            events_example(
                "phase-diagram", _PHASE_DIAGRAM_DATA,
                ["mj-chart-phase-region-click", "mj-chart-phase-boundary-click", "mj-chart-phase-point-click"],
                "<p>Regions emit <code>mj-chart-phase-region-click</code> <code>{ name, index "
                "}</code>, boundaries <code>mj-chart-phase-boundary-click</code> <code>{ name "
                "}</code> and special points <code>mj-chart-phase-point-click</code> "
                "<code>{ name, x, y }</code>.</p>",
                height=300, legend=True),
        ],
    ),

    # ── nyquist ────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="nyquist",
        title="Nyquist",
        category="scientific",
        summary="Complex-plane frequency-response locus (Re vs Im) with the critical point.",
        description=(
            "Each series lists points with omega, re and im. Re and Im share one pixels-per-"
            "unit factor, so circles stay round and angles are true. mirror: true adds the "
            "negative-frequency locus (dashed); criticalPoint (default -1+0j) is marked and "
            "labelled; showUnitCircle: true (or showUnitCircle=\"true\") adds the unit circle. "
            "Arrows point toward rising omega. Points emit mj-chart-nyquist-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name, color?, mirror?: boolean,\n"
            "             points: [{ omega?, re: number, im: number }] }],\n"
            "  criticalPoint?: { re, im },           // default { re: -1, im: 0 }\n"
            "  showUnitCircle?: boolean,             // the attribute wins\n"
            "  meta?: { xLabel?, yLabel? }           // default \"Re(H)\", \"Im(H)\"\n"
            "}</code></pre>"
        ),
        options=[
            true_false_option("showUnitCircle", "`true` (or a bare `showUnitCircle`) draws the unit "
                              "circle; absent, the data's `showUnitCircle` decides.", None),
        ],
        examples=[
            chart_example(
                "basic", "Third-order loop",
                "<p>One locus with its mirror, the unit circle and the -1 point.</p>",
                "nyquist", _NYQUIST_DATA, height=300),
            chart_example(
                "two-loops", "Two loops, custom critical point",
                "<p>Two open-loop responses without mirrors (the Im range is not made "
                "symmetric), a legend, axis labels and the critical point moved to "
                "-0.5.</p>",
                "nyquist", _NYQUIST_FIRST_ORDER_DATA, height=300, legend=True),
            events_example(
                "nyquist", _NYQUIST_DATA, ["mj-chart-nyquist-click"],
                "<p>Points emit <code>mj-chart-nyquist-click</code> <code>{ series, omega, re, "
                "im }</code>.</p>",
                height=300),
        ],
    ),

    # ── bode ───────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="bode",
        title="Bode",
        category="scientific",
        summary="Stacked magnitude (dB) and phase (degrees) panels over a log frequency axis.",
        description=(
            "Each point gives omega and the magnitude as magnitude_db, as a linear magnitude "
            "(converted with 20 log10) or as re / im, and the phase as phase_deg (or from re / "
            "im). The frequency axis is logarithmic over whole decades and the phase is "
            "unwrapped. asymptotes: true draws the low- and high-frequency asymptotes with "
            "slopes rounded to multiples of 20 dB/decade meeting at the corner frequency. "
            "Magnitude and phase points emit mj-chart-bode-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name, color?, points: [{\n"
            "    omega: number,\n"
            "    magnitude_db? | magnitude? | re? + im?,\n"
            "    phase_deg?                           // else from re / im\n"
            "  }] }],\n"
            "  asymptotes?: boolean,\n"
            "  meta?: { xLabel? }                    // default \"Frequency (rad/s)\"\n"
            "}</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Second-order low-pass",
                "<p>Magnitude and phase in dB / degrees with the asymptotes.</p>",
                "bode", _BODE_DATA, height=300),
            chart_example(
                "from-re-im", "From the complex response",
                "<p>Points given as <code>re</code> / <code>im</code>: magnitude and phase are "
                "computed; the asymptotes meet at the 10 rad/s corner.</p>",
                "bode", _BODE_RE_IM_DATA, height=300),
            chart_example(
                "two-filters", "Two filters with a legend",
                "<p>One series with a linear <code>magnitude</code>, one with "
                "<code>magnitude_db</code>; toggle either in the legend.</p>",
                "bode", _BODE_TWO_DATA, height=300, legend=True),
            events_example(
                "bode", _BODE_DATA, ["mj-chart-bode-click"],
                "<p>Points on both panels emit <code>mj-chart-bode-click</code> <code>{ series, "
                "omega, magnitude_db, phase_deg }</code>.</p>",
                height=300),
        ],
    ),

    # ── smith ──────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="smith",
        title="Smith Chart",
        category="scientific",
        summary="RF impedance chart: constant-resistance circles and constant-reactance arcs.",
        description=(
            "Points give a normalised impedance (r, x), an impedance in ohms (R, X, normalised "
            "by meta.z0, default 50), a normalised admittance (g, b) or a reflection "
            "coefficient (gamma_re, gamma_im), plus an optional freq_hz; every point is placed "
            "at its reflection coefficient. grid.rLines and grid.xLines choose the grid. mode "
            "\"admittance\" draws the admittance grid (the impedance grid rotated by 180°) and "
            "\"both\" overlays the two. Points emit mj-chart-smith-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  meta?: { z0?: number },               // ohms, default 50\n"
            "  mode?: \"impedance\" | \"admittance\" | \"both\",\n"
            "  grid?: { rLines?: number[], xLines?: number[] },\n"
            "  series: [{ name, color?, points: [\n"
            "    { r, x } | { R, X } | { g, b } | { gamma_re, gamma_im }  // + freq_hz?\n"
            "  ] }]\n"
            "}</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Antenna sweep",
                "<p>Normalised impedances of an antenna from 100 to 700 MHz.</p>",
                "smith", _SMITH_DATA, height=300),
            chart_example(
                "ohms-both", "Ohms on both grids",
                "<p>Impedances in ohms (<code>R</code>, <code>X</code>) normalised by "
                "<code>z0</code>, drawn over the impedance and admittance grids "
                "(<code>mode: \"both\"</code>).</p>",
                "smith", _SMITH_OHMS_DATA, height=300),
            chart_example(
                "gamma", "Reflection coefficients",
                "<p>S11 as reflection coefficients and S22 as admittances, on a sparse custom "
                "grid with a legend.</p>",
                "smith", _SMITH_GAMMA_DATA, height=300, legend=True),
            events_example(
                "smith", _SMITH_DATA, ["mj-chart-smith-click"],
                "<p>Points emit <code>mj-chart-smith-click</code> <code>{ series, freq_hz, r, "
                "x, gamma_re, gamma_im }</code>.</p>",
                height=300),
        ],
    ),

    # ── log-log ────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="log-log",
        title="Log-Log",
        category="scientific",
        summary="Line and point chart with both axes logarithmic, for power-law relationships.",
        description=(
            "Series give x / y points. Both axes are logarithmic over whole decades; the "
            "scale-x / scale-y attributes switch an axis to linear. A point that a log axis "
            "cannot show (<= 0) or a null breaks the line, and the dropped count is reported "
            "once per render as an mj-chart-error with severity \"warning\". Points emit "
            "mj-chart-loglog-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name, color?, points: [{ x: number, y: number | null }] }],\n"
            "  meta?: { xLabel?, yLabel? }\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="scale-x", description="x axis scale.", kind="enum",
                         values=_SCALE_VALUES, default="log"),
            AttributeDoc(name="scale-y", description="y axis scale.", kind="enum",
                         values=_SCALE_VALUES, default="log"),
        ],
        examples=[
            chart_example(
                "basic", "Power laws",
                "<p>y = x² and y = x³ are straight lines with slopes 2 and 3.</p>",
                "log-log", _LOG_LOG_DATA, legend=True),
            chart_example(
                "dropped-points", "Non-positive and null values",
                "<p>x = 0 and a negative y cannot be drawn on a log axis and the null is a gap: "
                "the line breaks there and an <code>mj-chart-error</code> warning (see "
                "Events) reports two dropped points.</p>",
                "log-log", _LOG_LOG_DROPPED_DATA),
            chart_example(
                "linear-y", "Linear y axis",
                "<p><code>scale-y=\"linear\"</code> turns the y axis linear: the power laws "
                "curve upward.</p>",
                "log-log", _LOG_LOG_DATA, attributes={"scale-y": "linear"}, legend=True),
            events_example(
                "log-log", _LOG_LOG_DROPPED_DATA, ["mj-chart-loglog-click", "mj-chart-error"],
                "<p>Points emit <code>mj-chart-loglog-click</code> <code>{ series, x, y }</code>; "
                "dropped points are reported as <code>mj-chart-error</code> <code>{ message, "
                "severity: \"warning\", dropped }</code>.</p>"),
        ],
    ),

    # ── semi-log ───────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="semi-log",
        title="Semi-Log",
        category="scientific",
        summary="One logarithmic axis, one linear: exponential growth and decay become straight lines.",
        description=(
            "By default x is linear and y logarithmic. Setting only one of scale-x / scale-y "
            "makes the other axis the opposite kind (scale-x=\"log\" alone gives a log x and a "
            "linear y); set both to choose freely. Points <= 0 on the log axis and nulls are "
            "gaps, reported as an mj-chart-error warning. Points emit mj-chart-loglog-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name, color?, points: [{ x: number, y: number | null }] }],\n"
            "  meta?: { xLabel?, yLabel? }\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="scale-x", description="x axis scale; set alone, y becomes the opposite kind.",
                         kind="enum", values=_SCALE_VALUES, default="linear"),
            AttributeDoc(name="scale-y", description="y axis scale; set alone, x becomes the opposite kind.",
                         kind="enum", values=_SCALE_VALUES, default="log"),
        ],
        examples=[
            chart_example(
                "basic", "Exponential growth",
                "<p>A doubling count is a straight line on the log y axis.</p>",
                "semi-log", _SEMI_LOG_DATA),
            chart_example(
                "decay", "Radioactive decay",
                "<p>Two isotopes with different half-lives: two straight lines of different "
                "slope, with a legend.</p>",
                "semi-log", _SEMI_LOG_DECAY_DATA, legend=True),
            chart_example(
                "log-x", "Log x axis (dose response)",
                "<p><code>scale-x=\"log\"</code> alone gives a log x axis and a linear y axis: "
                "the classic sigmoid dose-response plot.</p>",
                "semi-log", _SEMI_LOG_LOG_X_DATA, attributes={"scale-x": "log"}, legend=True),
            events_example(
                "semi-log", _SEMI_LOG_DATA, ["mj-chart-loglog-click"],
                "<p>Points emit <code>mj-chart-loglog-click</code> <code>{ series, x, y }</code>.</p>"),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Geographic
# ---------------------------------------------------------------------------

_GEOMETRY_NOTE = (
    "<p>Geometry is inline: <code>geojson</code> (a FeatureCollection, Feature or geometry) or "
    "<code>topology</code> (TopoJSON; <code>topologyObject</code> names the object, default "
    "the first). Polygon, MultiPolygon, LineString, MultiLineString, Point and MultiPoint "
    "features are drawn. A feature's id is <code>properties[featureKey]</code> when a key is "
    "given, else <code>feature.id</code>, else <code>properties.id</code>. The page's data is "
    "never changed; a URL string in <code>geojson</code> / <code>topology</code> is fetched by "
    "the chart before drawing.</p>"
)

_SYMBOL_SHAPE = (
    "<pre><code>{\n"
    "  series: [{ name, color?, symbol?: \"circle\" | \"square\" | \"triangle\" | \"diamond\",\n"
    "             points: [{ id?, label?, lat: number, lon | lng: number, size?: number }] }]\n"
    "  // or one layer: markers: [{ lat, lng | lon, label?, id?, value? | size? }],\n"
    "  //               symbol?: string\n"
    "  geojson? | topology?,                 // optional base map\n"
    "  meta?: { projection? }\n"
    "}</code></pre>"
    "<p>Series points are sized by <code>size</code>; markers by <code>size</code>, else "
    "<code>value</code>. With size scaling, radius = max-radius x sqrt(size / largest), "
    "at least min-radius; a size &lt;= 0 draws no symbol, and a size legend is drawn. Non-circle "
    "symbols keep the circle's area.</p>"
)

_TILE_SHAPE = (
    "<pre><code>{\n"
    "  regions: [{ id: string, value: number | null, label? }],\n"
    "  layout: { [id]: { q: number, r: number } }\n"
    "}</code></pre>"
    "<p>Hex tiles use axial coordinates (q, r); square tiles put q in columns and r in rows. "
    "Regions without a layout entry are placed in rows below the grid. Tiles are coloured by "
    "value class (legend) and a null value gets the no-data colour; labels turn light on dark "
    "tiles.</p>"
)

_SYMBOL_OPTIONS_SIZED = [
    AttributeDoc(name="size-scale", description="`sqrt` sizes symbols by area; `none` draws one size.",
                 kind="enum", values=["sqrt", "none"], default="sqrt"),
    _MIN_RADIUS_OPTION,
    _MAX_RADIUS_OPTION,
    _SHOW_LABELS_OPTION,
    _PROJECTION_OPTION,
    _FEATURE_KEY_OPTION,
]

_TILE_OPTIONS = [
    AttributeDoc(name="hex-orientation", description="Hexagon orientation (hex tiles).",
                 kind="enum", values=["flat", "pointy"], default="flat"),
]

_SELECT_EVENT = "mj-chart-select"

_GEOGRAPHIC = [

    # ── choropleth ─────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="choropleth",
        title="Choropleth",
        category="geographic",
        summary="Filled region map coloured by value class.",
        description=(
            "Regions from inline GeoJSON or TopoJSON are coloured by the value of the matching "
            "regions entry: values fall into equal-interval classes (classes, 2 to 9, default "
            "5) shown in the legend, and scheme: \"diverging\" centres a two-hue ramp on "
            "midpoint (default 0). Features without a value use the no-data colour; line "
            "features are coloured as strokes. Without geometry, regions that carry lat / lon "
            "are drawn as dots. Regions emit mj-chart-select."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  geojson | topology,                   // see below\n"
            "  regions: [{ id: string, value: number | null, label?,\n"
            "              lat?, lon? }],            // lat / lon: dots when there is no geometry\n"
            "  featureKey?: string,                  // the feature-key attribute wins\n"
            "  classes?: number,                     // 2..9, default 5\n"
            "  scheme?: \"diverging\", midpoint?: number,\n"
            "  meta?: { projection? }\n"
            "}</code></pre>" + _GEOMETRY_NOTE
        ),
        options=[_PROJECTION_OPTION, _FEATURE_KEY_OPTION],
        examples=[
            chart_example(
                "basic", "Five regions",
                "<p>Five polygons coloured into value classes, with the class legend.</p>",
                "choropleth", _CHOROPLETH_DATA),
            chart_example(
                "diverging", "Diverging classes",
                "<p>Signed changes with <code>scheme: \"diverging\"</code>, "
                "<code>midpoint: 0</code> and four classes.</p>",
                "choropleth", _CHOROPLETH_DIVERGING_DATA),
            chart_example(
                "feature-key", "Join by name, no-data, lines",
                "<p><code>feature-key=\"name\"</code> joins regions to "
                "<code>properties.name</code>; Westmark has no value (no-data colour), the "
                "river is a line feature and <code>meta.projection</code> is mercator.</p>",
                "choropleth", _CHOROPLETH_BY_NAME_DATA, attributes={"feature-key": "name"}),
            events_example(
                "choropleth", _CHOROPLETH_DATA, [_SELECT_EVENT],
                "<p>Regions emit <code>mj-chart-select</code> <code>{ id, label, value }</code> "
                "(value null without data).</p>"),
        ],
    ),

    # ── symbol-map ─────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="symbol-map",
        title="Symbol Map",
        category="geographic",
        summary="Point symbols at geographic coordinates, one size unless size scaling is on.",
        description=(
            "Supply markers (one layer) or series with points and a per-series symbol (circle, "
            "square, triangle or diamond). Symbols have one size unless size-scale=\"sqrt\" is "
            "set; show-labels writes the labels next to the symbols. An optional "
            "geojson / topology base map is drawn underneath. Symbols emit mj-chart-select and "
            "the legend lists the series."
        ),
        data_shape=_SYMBOL_SHAPE + _GEOMETRY_NOTE,
        options=[
            AttributeDoc(name="size-scale", description="`sqrt` sizes symbols by area; `none` draws one size.",
                         kind="enum", values=["sqrt", "none"], default="none"),
            _MIN_RADIUS_OPTION,
            _MAX_RADIUS_OPTION,
            _SHOW_LABELS_OPTION,
            _PROJECTION_OPTION,
            _FEATURE_KEY_OPTION,
        ],
        examples=[
            chart_example(
                "basic", "Labelled markers",
                "<p>Seven cities as markers; the bare <code>show-labels</code> attribute writes "
                "their names (any boolean option is on when present).</p>",
                "symbol-map", _SYMBOL_MAP_DATA, attributes={"show-labels": ""}),
            chart_example(
                "series-symbols", "Series with symbols",
                "<p>Two series drawn as squares and triangles, with a legend; labels are in the "
                "tooltips (try <em>show-labels</em> in Controls).</p>",
                "symbol-map", _SYMBOL_SERIES_DATA, legend=True),
            chart_example(
                "sized", "Sized by value",
                "<p><code>size-scale=\"sqrt\"</code> sizes the markers by population (area "
                "proportional to value) and adds a size legend.</p>",
                "symbol-map", _SYMBOL_SIZED_DATA, attributes={"size-scale": "sqrt", "show-labels": "true"}),
            events_example(
                "symbol-map", _SYMBOL_SERIES_DATA, [_SELECT_EVENT],
                "<p>Symbols emit <code>mj-chart-select</code> <code>{ id, label, lon, lat, "
                "value, series }</code>.</p>",
                legend=True),
        ],
    ),

    # ── bubble-map ─────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="bubble-map",
        title="Bubble Map",
        category="geographic",
        summary="Circles at geographic coordinates whose area is proportional to the value.",
        description=(
            "The symbol map with size scaling on by default: radius = max-radius x sqrt(value / "
            "largest value), at least min-radius, so circle AREA is proportional to the value; "
            "values <= 0 draw no circle. A size legend shows reference values and "
            "show-labels=\"true\" names the places. size-scale=\"none\" turns the sizing off. "
            "Bubbles emit mj-chart-select."
        ),
        data_shape=_SYMBOL_SHAPE + _GEOMETRY_NOTE,
        options=_SYMBOL_OPTIONS_SIZED,
        examples=[
            chart_example(
                "basic", "City populations",
                "<p>The seven largest US cities sized by population.</p>",
                "bubble-map", _BUBBLE_MAP_DATA, attributes={"show-labels": "true"}),
            chart_example(
                "base-map", "Over a base map",
                "<p>The same bubbles over a simplified outline given as <code>geojson</code>, "
                "with <code>min-radius=\"4\"</code> and <code>max-radius=\"20\"</code>.</p>",
                "bubble-map", _BUBBLE_BASE_MAP_DATA,
                attributes={"min-radius": "4", "max-radius": "20", "show-labels": "true"}),
            events_example(
                "bubble-map", _BUBBLE_MAP_DATA, [_SELECT_EVENT],
                "<p>Bubbles emit <code>mj-chart-select</code> <code>{ id, label, lon, lat, "
                "value, series }</code>; markers take their id from <code>label</code> when "
                "they have no <code>id</code>.</p>"),
        ],
    ),

    # ── proportional-symbol-map ────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="proportional-symbol-map",
        title="Proportional Symbol Map",
        category="geographic",
        summary="Squares, triangles or diamonds at geographic coordinates, sized by value.",
        description=(
            "The bubble-map sizing (symbol area proportional to size, size-scale \"sqrt\" by "
            "default) with the per-series symbol shape: diamond, square, triangle or circle. "
            "Supply series with points carrying lat, lon (or lng), size and label. Symbols "
            "emit mj-chart-select; the legend lists the series."
        ),
        data_shape=_SYMBOL_SHAPE + _GEOMETRY_NOTE,
        options=_SYMBOL_OPTIONS_SIZED,
        examples=[
            chart_example(
                "basic", "Diamonds by GDP",
                "<p>One series of diamonds sized by city GDP.</p>",
                "proportional-symbol-map", _PROPORTIONAL_SYMBOL_MAP_DATA, attributes={"show-labels": "true"}),
            chart_example(
                "shapes", "Two shapes, one scale",
                "<p>Solar sites as squares and wind sites as triangles share one size scale; "
                "toggle a series in the legend.</p>",
                "proportional-symbol-map", _PROPORTIONAL_SHAPES_DATA,
                attributes={"show-labels": "true"}, legend=True),
            events_example(
                "proportional-symbol-map", _PROPORTIONAL_SHAPES_DATA, [_SELECT_EVENT],
                "<p>Symbols emit <code>mj-chart-select</code> <code>{ id, label, lon, lat, "
                "value, series }</code> (a point without an <code>id</code> reports its label as the id).</p>",
                legend=True),
        ],
    ),

    # ── hex-map ────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="hex-map",
        title="Hex Map",
        category="geographic",
        summary="Equal-area hexagonal tile map with each region coloured by value class.",
        description=(
            "Supply regions and a layout of axial hex coordinates (q, r); the hexagons "
            "tessellate, flat-topped by default (hex-orientation=\"pointy\" for pointy tops). "
            "shape=\"square\" draws the same data as square tiles. Tiles are coloured by value "
            "class with a legend, labels switch to a light colour on dark tiles, and regions "
            "without a layout entry are placed below the grid. Tiles emit mj-chart-select."
        ),
        data_shape=_TILE_SHAPE,
        options=_TILE_OPTIONS + [
            AttributeDoc(name="shape", description="Tile shape; overrides the type's shape.",
                         kind="enum", values=["hex", "square"], default="hex"),
        ],
        examples=[
            chart_example(
                "basic", "Seven regions",
                "<p>A compass-shaped hex layout of seven regions.</p>",
                "hex-map", _HEX_MAP_DATA),
            chart_example(
                "pointy", "Pointy-topped hexagons",
                "<p><code>hex-orientation=\"pointy\"</code> rotates the hexagons by 30°.</p>",
                "hex-map", _HEX_MAP_DATA, attributes={"hex-orientation": "pointy"}),
            chart_example(
                "missing-layout", "Missing layout and values",
                "<p>Alaska and Hawaii have no layout entry and are placed below the grid; Idaho "
                "has no value (no-data colour).</p>",
                "hex-map", _TILE_GRID_GAPS_DATA),
            events_example(
                "hex-map", _HEX_MAP_DATA, [_SELECT_EVENT],
                "<p>Tiles emit <code>mj-chart-select</code> <code>{ id, label, value }</code>.</p>"),
        ],
    ),

    # ── tile-grid-map ──────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="tile-grid-map",
        title="Tile Grid Map",
        category="geographic",
        summary="Equal-area square tile map on a plain column / row grid (same data as hex-map).",
        description=(
            "Same data as hex-map, drawn as square tiles: layout puts q in columns and r in "
            "rows, so tiles line up and never overlap. shape=\"hex\" draws hexagons instead. "
            "Tiles are coloured by value class with a legend; regions without a layout entry "
            "go below the grid. Tiles emit mj-chart-select."
        ),
        data_shape=_TILE_SHAPE,
        options=[
            AttributeDoc(name="shape", description="Tile shape; overrides the type's shape.",
                         kind="enum", values=["square", "hex"], default="square"),
        ] + _TILE_OPTIONS,
        examples=[
            chart_example(
                "basic", "New England",
                "<p>Seven north-eastern states on a square tile grid.</p>",
                "tile-grid-map", _TILE_GRID_MAP_DATA),
            chart_example(
                "missing-layout", "Missing layout and values",
                "<p>AK and HI have no layout entry and are placed below; ID has no value.</p>",
                "tile-grid-map", _TILE_GRID_GAPS_DATA),
            chart_example(
                "hex-shape", "As hexagons",
                "<p><code>shape=\"hex\"</code> draws the same layout as hexagons.</p>",
                "tile-grid-map", _TILE_GRID_MAP_DATA, attributes={"shape": "hex"}),
            events_example(
                "tile-grid-map", _TILE_GRID_MAP_DATA, [_SELECT_EVENT],
                "<p>Tiles emit <code>mj-chart-select</code> <code>{ id, label, value }</code>.</p>"),
        ],
    ),

    # ── flow-map ───────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="flow-map",
        title="Flow Map",
        category="geographic",
        summary="Directed curved flows between geographic nodes, width proportional to value.",
        description=(
            "nodes give positions and links give source, target and value. Stroke width is "
            "proportional to the value from zero (a width legend explains it; taper=\"false\" "
            "draws equal widths); A to B and B to A bend to opposite sides and the arrowheads "
            "follow the curve and stop at the node marker. arc=\"straight\" draws straight "
            "flows and show-labels=\"true\" names the nodes. Flows and nodes emit "
            "mj-chart-select."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  nodes: [{ id: string, lon | lng: number, lat: number, label? }],\n"
            "  links: [{ source: id, target: id, value?: number }],\n"
            "  geojson? | topology?,                 // optional base map\n"
            "  meta?: { projection? }\n"
            "}</code></pre>" + _GEOMETRY_NOTE
        ),
        options=[
            boolean_option("taper", "Flow width proportional to value; `taper=\"false\"` draws every "
                           "flow with the same width.", True),
            AttributeDoc(name="arc", description="Flow shape.", kind="enum",
                         values=["curve", "straight"], default="curve"),
            _SHOW_LABELS_OPTION,
            _PROJECTION_OPTION,
            _FEATURE_KEY_OPTION,
        ],
        examples=[
            chart_example(
                "basic", "Passenger flows",
                "<p>Six flows between five cities, widths proportional to passengers.</p>",
                "flow-map", _FLOW_MAP_DATA, attributes={"show-labels": "true"}),
            chart_example(
                "straight", "Straight, equal widths, base map",
                "<p><code>arc=\"straight\"</code> and <code>taper=\"false\"</code> over a "
                "simplified base map.</p>",
                "flow-map", _FLOW_MAP_BASE_DATA,
                attributes={"arc": "straight", "taper": "false", "show-labels": "true"}),
            events_example(
                "flow-map", _FLOW_MAP_DATA, [_SELECT_EVENT],
                "<p>Flows emit <code>mj-chart-select</code> <code>{ source, target, value }</code> "
                "and nodes <code>{ id, label }</code>.</p>",
                attributes={"show-labels": "true"}),
        ],
    ),

    # ── route-map ──────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="route-map",
        title="Route Map",
        category="geographic",
        summary="Routes drawn as polylines along waypoint sequences, optionally over a base map.",
        description=(
            "Each series holds routes, each with an id and waypoints; routes take the short way "
            "across the antimeridian. variant=\"great-circle\" follows the geodesic between "
            "waypoints, show-stops=\"true\" marks and labels each waypoint, and an optional "
            "geojson / topology base map is drawn underneath. Routes (and stops) emit "
            "mj-chart-select; the legend lists the series."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name, color?, routes: [{ id: string,\n"
            "             waypoints: [{ lon: number, lat: number, label? }] }] }],\n"
            "  geojson? | topology?,                 // optional base map\n"
            "  meta?: { projection? }\n"
            "}</code></pre>" + _GEOMETRY_NOTE
        ),
        options=[
            AttributeDoc(name="variant", description="Line between waypoints.", kind="enum",
                         values=["polyline", "great-circle"], default="polyline"),
            boolean_option("show-stops", "Marks and labels every waypoint (each stop is then "
                           "focusable)."),
            _PROJECTION_OPTION,
            _FEATURE_KEY_OPTION,
        ],
        examples=[
            chart_example(
                "basic", "Great-circle flights",
                "<p>Two flights with <code>variant=\"great-circle\"</code> and stops; the "
                "Pacific route crosses the antimeridian the short way.</p>",
                "route-map", _ROUTE_MAP_DATA,
                attributes={"variant": "great-circle", "show-stops": "true"}, legend=True),
            chart_example(
                "base-map", "Corridors over a base map",
                "<p>Polylines (the default variant) over a simplified outline; switch "
                "<em>show-stops</em> on in Controls to name the cities.</p>",
                "route-map", _ROUTE_MAP_BASE_DATA, legend=True),
            events_example(
                "route-map", _ROUTE_MAP_DATA, [_SELECT_EVENT],
                "<p>Routes emit <code>mj-chart-select</code> <code>{ id, series }</code>; with "
                "stops shown, stops emit <code>{ routeId, waypointIndex, label }</code>.</p>",
                attributes={"variant": "great-circle", "show-stops": "true"}, legend=True),
        ],
    ),

    # ── geo-heatmap ────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="geo-heatmap",
        title="Geo Heatmap",
        category="geographic",
        summary="Gaussian kernel-density surface of weighted points, over an optional base map.",
        description=(
            "Points with lon, lat and an optional weight (default 1) are smoothed with a "
            "Gaussian kernel (bandwidth = sigma in px, default 30, reaching 3 sigma) and "
            "painted as one raster colour layer above an optional base map, with a low-to-high "
            "key. The surface is one focusable mark with a summary label. A click emits "
            "mj-chart-select { id, label, series, lon, lat, weight, density, distance } for the "
            "data point nearest the pointer (density: the surface there relative to the peak, "
            "0-1; distance in px); Enter or Space reports the hottest spot."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name, points: [{ lon: number, lat: number, weight?: number,\n"
            "                              id?: string, label?: string }] }],\n"
            "  geojson? | topology?,                 // optional base map\n"
            "  meta?: { projection? }\n"
            "}</code></pre>"
            "<p>The raster image's pixels arrive a moment after the render (its href is set "
            "asynchronously).</p>" + _GEOMETRY_NOTE
        ),
        options=[
            AttributeDoc(name="bandwidth", description="Kernel sigma in px.", kind="number", default="30"),
            _PROJECTION_OPTION,
            _FEATURE_KEY_OPTION,
        ],
        examples=[
            chart_example(
                "basic", "Three hot spots",
                "<p>Weighted incidents around Paris, Berlin and London.</p>",
                "geo-heatmap", _GEO_HEATMAP_DATA),
            chart_example(
                "bandwidth", "Narrow kernel over a base map",
                "<p><code>bandwidth=\"12\"</code> keeps the spots tight; the outline is a "
                "<code>geojson</code> base map.</p>",
                "geo-heatmap", _GEO_HEATMAP_US_DATA, attributes={"bandwidth": "12"}),
            events_example(
                "geo-heatmap", _GEO_HEATMAP_US_DATA, ["mj-chart-select"],
                "<p>Click the surface: <code>mj-chart-select</code> reports the data point nearest "
                "the pointer and the relative <code>density</code> there (0-1). Focus the surface "
                "and press Enter for the hottest spot.</p>"),
        ],
    ),

    # ── isoline ────────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="isoline",
        title="Isoline",
        category="geographic",
        summary="Contour lines, or filled bands between levels, from a lon / lat scalar grid.",
        description=(
            "Each series has a grid over a lon / lat box with cols x rows values (row-major, "
            "row 0 at lat-min) and optional levels (default: nice levels from the data). Each "
            "level is one labelled path; variant=\"filled\" fills the bands between levels. A "
            "non-numeric value is a hole. Level paths emit mj-chart-isoline-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name, levels?: number[],\n"
            "             grid: { \"lon-min\", \"lon-max\", \"lat-min\", \"lat-max\",\n"
            "                     cols: number, rows: number,\n"
            "                     values: (number | null)[] } }],   // cols x rows, row 0 at lat-min\n"
            "  geojson? | topology?,                 // optional base map\n"
            "  meta?: { projection? }\n"
            "}</code></pre>" + _GEOMETRY_NOTE
        ),
        options=[
            AttributeDoc(name="variant", description="Lines only, or filled bands between levels.",
                         kind="enum", values=["lines", "filled"], default="lines"),
            _PROJECTION_OPTION,
            _FEATURE_KEY_OPTION,
        ],
        examples=[
            chart_example(
                "basic", "Filled temperature bands",
                "<p>Five temperature levels with <code>variant=\"filled\"</code>.</p>",
                "isoline", _ISOLINE_DATA, attributes={"variant": "filled"}),
            chart_example(
                "auto-levels", "Lines with automatic levels",
                "<p>No <code>levels</code>: nice levels are derived from the rainfall grid and "
                "drawn as labelled lines (the default variant).</p>",
                "isoline", _ISOLINE_AUTO_DATA),
            chart_example(
                "holes", "Holes in the grid",
                "<p>One null value (no sounding) is a hole: the cells around it are left out, so the "
                "100 m contour has a gap there.</p>",
                "isoline", _ISOLINE_HOLES_DATA),
            events_example(
                "isoline", _ISOLINE_AUTO_DATA, ["mj-chart-isoline-click"],
                "<p>Level paths emit <code>mj-chart-isoline-click</code> <code>{ series, level "
                "}</code>.</p>"),
        ],
    ),

    # ── cartogram ──────────────────────────────────────────────────────────────

    ChartTypeDoc(
        type_key="cartogram",
        title="Cartogram",
        category="geographic",
        summary="Value-scaled region map: region (or circle) area proportional to the value.",
        description=(
            "Needs polygon geometry and regions with values. By default (area) each region "
            "shrinks about its centroid until its AREA is proportional to its value; the "
            "densest region keeps its size and dashed outlines show the original map (a "
            "non-contiguous cartogram). variant=\"dorling\" draws circles with area "
            "proportional to value, separated by a collision pass, with a size legend; "
            "regions[].color colours a circle. Regions emit mj-chart-select."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  geojson | topology,                   // polygons\n"
            "  regions: [{ id: string, value: number, label?, color? }],\n"
            "  featureKey?: string,\n"
            "  classes?, scheme?, midpoint?,         // area mode colours, as choropleth\n"
            "  meta?: { projection? }\n"
            "}</code></pre>" + _GEOMETRY_NOTE
        ),
        options=[
            AttributeDoc(name="variant", description="Scaled regions or Dorling circles.", kind="enum",
                         values=["area", "dorling"], default="area"),
            _PROJECTION_OPTION,
            _FEATURE_KEY_OPTION,
        ],
        examples=[
            chart_example(
                "basic", "Scaled regions",
                "<p>Five equal squares shrunk to areas proportional to their values; Region D "
                "(600) keeps its size.</p>",
                "cartogram", _CARTOGRAM_DATA),
            chart_example(
                "dorling", "Dorling circles",
                "<p><code>variant=\"dorling\"</code>: one circle per region, area proportional "
                "to value, pushed apart so they do not overlap.</p>",
                "cartogram", _CARTOGRAM_DATA, attributes={"variant": "dorling"}),
            events_example(
                "cartogram", _CARTOGRAM_DATA, [_SELECT_EVENT],
                "<p>Regions emit <code>mj-chart-select</code> <code>{ id, label, value }</code>.</p>"),
        ],
    ),
]


CHART_TYPES = _SCIENTIFIC + _GEOGRAPHIC
