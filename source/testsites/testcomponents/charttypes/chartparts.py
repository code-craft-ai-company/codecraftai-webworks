"""
    chartparts.py

    ComponentDoc entries for the coordinated chart PART components --
    <mj-chart-title>, <mj-chart-legend> and <mj-chart-data-table>. Each part
    binds to an <mj-chart> controller (its `chart` attribute names the
    controller's id, else the nearest ancestor controller) and draws from
    the controller's model, so every example pairs the part with a chart.

    The parts are served at /chart-part/<tag> and listed in the "Chart parts"
    section of the Charts landing page; they are not part of the component
    catalog's 143 pages.
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


#: The group key the chart part docs carry.
CHART_PARTS_GROUP = "chart-parts"


_QUARTERS = (
    '{"categories":["Q1","Q2","Q3","Q4"],'
    '"series":['
    '{"name":"Product A","values":[320,410,375,490]},'
    '{"name":"Product B","values":[210,275,340,420]},'
    '{"name":"Product C","values":[140,195,215,260]}'
    ']}'
)

_VISITORS = (
    '{"meta":{"title":"Visitors (from meta.title)","subtitle":"Last six months"},'
    '"categories":["May","Jun","Jul","Aug","Sep","Oct"],'
    '"series":[{"name":"Visitors","values":[1200,1350,1280,1520,1610,1740]}]}'
)

_SHARE = (
    '{"categories":["Direct","Search","Social","Referral"],'
    '"series":[{"name":"Share","values":[38,32,18,12]}]}'
)


_TITLE = ComponentDoc(
    tag="mj-chart-title",
    title="Chart Title",
    group=CHART_PARTS_GROUP,
    summary="Title and subtitle of a chart, bound to its &lt;mj-chart&gt;.",
    description=(
        "<p><code>&lt;mj-chart-title&gt;</code> shows the title (and an optional "
        "subtitle) of a chart. It binds to the <code>&lt;mj-chart&gt;</code> named "
        "by its <code>chart</code> attribute, or to the chart it is nested in, and "
        "can be placed anywhere in the page. The bound chart takes the title as its "
        "accessible name when it has no <code>label</code>.</p>"
    ),
    how_to_use=(
        "<p>Nest it inside the chart (it is drawn above the plot) or place it "
        "elsewhere with <code>chart=\"&lt;chart id&gt;\"</code>. The text is, in "
        "order: the <code>text</code> attribute, the element's own content, then the "
        "data's <code>meta.title</code>. Content is shown as written: text, rich "
        "markup, an icon or an image; the chart takes its text alternative (the "
        "text, an image's <code>alt</code>, an element's <code>aria-label</code>) as "
        "its name. <code>subtitle</code> falls back to <code>meta.subtitle</code>. Set "
        "<code>level</code> (1-6) to expose the title as a heading.</p>"
    ),
    attributes=[
        AttributeDoc(name="chart", description="Id of the `mj-chart` to bind to; default: the enclosing chart.",
                     kind="string"),
        AttributeDoc(name="text", description="Title text; wins over the content and `meta.title`.",
                     kind="string"),
        AttributeDoc(name="subtitle", description="Subtitle; default `meta.subtitle`.", kind="string"),
        AttributeDoc(name="level", description="Exposes the title as a heading of this level.",
                     kind="enum", values=["1", "2", "3", "4", "5", "6"]),
    ],
    slots=[
        ("", "The title content, shown as written: text, rich markup, an icon or an image. "
             "Its text alternative (text, `alt`, `aria-label`) is the title text.",
         "Quarterly revenue by product"),
    ],
    properties=[
        ("chartLabel", "string, read-only. The title text currently shown: the `text` value, the content's "
                       "text alternative, or `meta.title`; the bound chart uses it as its name."),
        ("controller", "MjChart | null, read-only. The chart the title is bound to."),
    ],
    parts=[
        ("title", "The title line."),
        ("subtitle", "The subtitle line (hidden when there is none)."),
    ],
    css_properties=[
        ("--mj-chart-title-font-size", "Title font size (default `--mj-font-size-lg`)."),
        ("--mj-chart-title-color", "Title colour (default `--mj-text`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Nested in the chart",
            description="<p>The title is drawn above the plot and names the chart.</p>",
            html=(
                '<mj-chart id="revenue" type="column" style="height:260px">\n'
                '  <mj-chart-title level="2" subtitle="Thousands of euros">Quarterly revenue by product</mj-chart-title>\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _QUARTERS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="bound-by-id",
            title="Placed elsewhere",
            description="<p>The title sits outside the chart and binds with <code>chart=\"trend\"</code>.</p>",
            html=(
                '<mj-chart-title chart="trend" text="Weekly sign-ups" subtitle="Bound with chart=&quot;trend&quot;"></mj-chart-title>\n'
                '<mj-chart id="trend" type="line" style="height:220px">\n'
                '  <script type="application/json">' + _VISITORS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="meta-title",
            title="From the data",
            description="<p>No text and no content: the title and subtitle come from <code>meta</code>.</p>",
            html=(
                '<mj-chart id="meta" type="area" style="height:220px">\n'
                '  <mj-chart-title></mj-chart-title>\n'
                '  <script type="application/json">' + _VISITORS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="image-title",
            title="Image as the title",
            description=(
                "<p>The content is only an image: it is shown, and its <code>alt</code> "
                "text names the chart (see the chart's <code>aria-label</code>).</p>"
            ),
            html=(
                '<mj-chart id="logo" type="column" style="height:240px">\n'
                '  <mj-chart-title level="2">'
                '<img alt="Acme revenue" width="180" height="28" src="data:image/svg+xml,'
                '%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27180%27 height=%2728%27%3E'
                '%3Crect width=%2728%27 height=%2728%27 rx=%276%27 fill=%27%232563eb%27/%3E'
                '%3Ctext x=%2738%27 y=%2720%27 font-family=%27sans-serif%27 font-size=%2716%27 '
                'fill=%27%232563eb%27%3EAcme revenue%3C/text%3E%3C/svg%3E">'
                '</mj-chart-title>\n'
                '  <script type="application/json">' + _QUARTERS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>The custom properties and <code>::part(subtitle)</code> restyle the title.</p>",
            html=(
                '<mj-chart id="styled" type="bar" orientation="horizontal" style="height:220px">\n'
                '  <mj-chart-title subtitle="Styled with custom properties">Traffic share</mj-chart-title>\n'
                '  <script type="application/json">' + _SHARE + '</script>\n'
                '</mj-chart>'
            ),
            css=(
                "mj-chart-title {\n"
                "  --mj-chart-title-font-size: 1.5rem;\n"
                "  --mj-chart-title-color: var(--mj-accent);\n"
                "}\n"
                "mj-chart-title::part(subtitle) { font-style: italic; }\n"
            ),
        ),
    ],
)


_LEGEND = ComponentDoc(
    tag="mj-chart-legend",
    title="Chart Legend",
    group=CHART_PARTS_GROUP,
    summary="What a chart's colours stand for; series entries toggle the series.",
    description=(
        "<p><code>&lt;mj-chart-legend&gt;</code> lists the entries the chart "
        "publishes: one per series, or what the renderer reports for its type "
        "(slices, nodes). A series entry is a toggle button: pressing it hides or "
        "shows that series in the chart, and <code>aria-pressed=\"true\"</code> means "
        "the series is shown. An entry that only explains a colour is plain text.</p>"
    ),
    how_to_use=(
        "<p>Nest it in the chart (drawn below the plot) or bind it with "
        "<code>chart=\"&lt;chart id&gt;\"</code> anywhere on the page. "
        "<code>orientation=\"vertical\"</code> stacks the entries. Listen for "
        "<code>mj-chart-legend-toggle</code> on the legend, or "
        "<code>mj-chart-series-toggle</code> on the chart. <code>disabled</code> "
        "turns the toggles off for pointer and keyboard alike.</p>"
    ),
    attributes=[
        AttributeDoc(name="chart", description="Id of the `mj-chart` to bind to; default: the enclosing chart.",
                     kind="string"),
        AttributeDoc(name="orientation", description="Lays the entries out in a row or a column.",
                     kind="enum", values=["horizontal", "vertical"], default="horizontal"),
        AttributeDoc(name="disabled",
                     description="Disables the series toggles: they take neither focus nor clicks, so the "
                                 "series cannot be hidden or shown from this legend (the chart's API still works).",
                     kind="boolean"),
    ],
    events=[
        ("mj-chart-legend-toggle", "A series entry was pressed; the chart hides or shows that series.",
         "{ series: string, seriesIndex: number, visible: boolean, hidden: boolean }"),
    ],
    properties=[
        ("controller", "MjChart | null, read-only. The chart the legend is bound to."),
        ("disabled", "boolean. Reads and sets the `disabled` attribute."),
    ],
    parts=[
        ("legend", "The list of entries (`ul`)."),
        ("entry", "Each list item (`li`)."),
        ("item", "The toggle `button` of a series entry, or the `span` of a colour-key entry."),
        ("swatch", "The colour square of each entry; hollow while its series is hidden."),
    ],
    css_properties=[
        ("--mj-chart-legend-swatch", "Swatch fill and border colour (default `--mj-accent`). The legend sets it "
                                     "on each swatch from the entry colour, so an outside value only shows for "
                                     "an entry without a colour; restyle swatches through `::part(swatch)`."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Toggle series",
            description="<p>Press an entry to hide a series; watch <code>mj-chart-legend-toggle</code> in Events.</p>",
            html=(
                '<mj-chart id="quarters" type="column" style="height:260px">\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _QUARTERS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="vertical",
            title="Vertical, beside the chart",
            description="<p>A vertical legend bound by id, laid out next to the chart.</p>",
            html=(
                '<div class="row">\n'
                '  <mj-chart id="side" type="line" style="height:240px">\n'
                '    <script type="application/json">' + _QUARTERS + '</script>\n'
                '  </mj-chart>\n'
                '  <mj-chart-legend chart="side" orientation="vertical"></mj-chart-legend>\n'
                '</div>'
            ),
            css=(
                ".row { display: flex; gap: var(--mj-space-4, 1rem); align-items: center; }\n"
                ".row mj-chart { flex: 1; min-width: 0; }\n"
            ),
        ),
        ComponentExample(
            key="color-key",
            title="Colour key (pie)",
            description="<p>For a pie the entries explain slice colours and are not toggles.</p>",
            html=(
                '<mj-chart id="share" type="pie" style="height:260px">\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _SHARE + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="disabled",
            title="Disabled",
            description=(
                "<p>A disabled legend still explains the colours, but its entries are "
                "neither clickable nor reachable with Tab.</p>"
            ),
            html=(
                '<mj-chart id="locked" type="column" style="height:240px">\n'
                '  <mj-chart-legend disabled></mj-chart-legend>\n'
                '  <script type="application/json">' + _QUARTERS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="events",
            title="Reacting to toggles",
            description=(
                "<p>A script lists the hidden series under the chart from the chart's "
                "<code>mj-chart-series-toggle</code> event.</p>"
            ),
            html=(
                '<mj-chart id="reactive" type="column" style="height:240px">\n'
                '  <mj-chart-legend id="reactive-legend"></mj-chart-legend>\n'
                '  <script type="application/json">' + _QUARTERS + '</script>\n'
                '</mj-chart>\n'
                '<p id="hidden-series">Hidden: none</p>'
            ),
            script=(
                'const chart = document.getElementById("reactive")\n'
                'const output = document.getElementById("hidden-series")\n'
                'chart.addEventListener("mj-chart-series-toggle", (event) => {\n'
                '  const hidden = event.detail.hiddenSeries\n'
                '  output.textContent = "Hidden: " + (hidden.length > 0 ? hidden.join(", ") : "none")\n'
                '  mjSandbox.log("hidden series", hidden)\n'
                '})\n'
            ),
        ),
    ],
)


_DATA_TABLE = ComponentDoc(
    tag="mj-chart-data-table",
    title="Chart Data Table",
    group=CHART_PARTS_GROUP,
    summary="The chart's data as a real, visible table.",
    description=(
        "<p><code>&lt;mj-chart-data-table&gt;</code> renders the data of the chart "
        "it is bound to as a <code>&lt;table&gt;</code>: the renderer's own table "
        "for its chart type when it publishes one, else a generic table of the "
        "data. Hidden series are left out (with every series hidden a short note "
        "takes the table's place), and long tables are cut after 500 rows with a "
        "note. It is both an accessible alternative to the drawing and a data "
        "inspector.</p>"
    ),
    how_to_use=(
        "<p>Place it near the chart with <code>chart=\"&lt;chart id&gt;\"</code>, or "
        "nest it in the chart. <code>caption</code> overrides the caption, which "
        "defaults to the caption the chart type gives its table, else the chart's "
        "accessible name (its <code>label</code>, a bound "
        "<code>&lt;mj-chart-title&gt;</code>, <code>meta.title</code>, else "
        "\"&lt;type&gt; chart\"). Try the data presets in Controls: the table "
        "follows every redraw.</p>"
    ),
    attributes=[
        AttributeDoc(name="chart", description="Id of the `mj-chart` to bind to; default: the enclosing chart.",
                     kind="string"),
        AttributeDoc(name="caption",
                     description="Table caption; blank counts as absent. Default: the caption the chart type gives "
                                 "its table, else the chart's accessible name (`label`, `title`, a bound "
                                 "`mj-chart-title`, `meta.title`, else \"<type> chart\").",
                     kind="string"),
    ],
    properties=[
        ("controller", "MjChart | null, read-only. The chart the table is bound to."),
    ],
    parts=[
        ("container", "The element holding the table (empty while the chart has no data)."),
        ("table", "The `table` element: caption, column headers, rows and the truncation note."),
        ("empty", "The note shown instead of the table while every series is hidden."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Bound by id",
            description="<p>The table under the chart shows the same data.</p>",
            html=(
                '<mj-chart-data-table chart="sales" caption="Revenue per quarter"></mj-chart-data-table>\n'
                '<mj-chart id="sales" type="column" style="height:220px">\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _QUARTERS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="nested",
            title="Nested in the chart",
            description=(
                "<p>A nested table is drawn below the plot and takes its caption from the "
                "title; hide a series in the legend and its column goes, hide them all and "
                "a note replaces the table. The chart sets only a minimum plot height, so "
                "the parts add to it instead of squeezing the drawing.</p>"
            ),
            html=(
                '<mj-chart id="nested" type="line" style="--mj-chart-min-height:200px">\n'
                '  <mj-chart-title>Quarterly revenue by product</mj-chart-title>\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <mj-chart-data-table></mj-chart-data-table>\n'
                '  <script type="application/json">' + _QUARTERS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="live-data",
            title="Live data",
            description="<p>The script replaces the chart data every two seconds; the table follows.</p>",
            html=(
                '<mj-chart-data-table chart="live"></mj-chart-data-table>\n'
                '<mj-chart id="live" type="bar" style="height:200px"></mj-chart>'
            ),
            script=(
                'const chart = document.getElementById("live")\n'
                'let tick = 0\n'
                'function update() {\n'
                '  tick += 1\n'
                '  chart.data = {\n'
                '    meta: { title: "Live update " + tick },\n'
                '    categories: ["North", "South", "East"],\n'
                '    series: [{ name: "Orders", values: [3 + (tick % 5), 6 - (tick % 4), 2 + (tick % 3)] }]\n'
                '  }\n'
                '}\n'
                'update()\n'
                'setInterval(update, 2000)\n'
            ),
        ),
    ],
)


#: The chart part docs, in display order.
CHART_PARTS = [_TITLE, _LEGEND, _DATA_TABLE]
