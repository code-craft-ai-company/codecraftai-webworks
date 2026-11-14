"""
    data.py

    Catalog entries for the 'Data & Display' component group.

    Each entry describes and demonstrates one data-oriented component:
    mj-table, mj-data-table, mj-tree-grid, mj-list, mj-virtual-list,
    mj-kanban, mj-calendar, mj-master-detail, mj-column-picker,
    mj-bulk-action-bar, mj-sort-control and mj-row-selector.

    Every page is a sandbox: a gallery of examples (the first one, ``basic``,
    is the one the functional tests in ``tests/test_func_data.py`` load), typed
    attribute controls and complete reference tables. The reference content is
    taken from the component sources under
    ``static/javascript/components/mj<name>.js``.
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


# ===========================================================================
# mj-table
# ===========================================================================

_TABLE = ComponentDoc(
    tag="mj-table",
    title="Table",
    group="data",
    summary="Static, read-only tabular data with native &lt;table&gt; semantics.",
    description=(
        "<p><code>&lt;mj-table&gt;</code> renders read-only tabular data as a real "
        "<code>&lt;table&gt;</code> in its shadow root: a caption, a header row of "
        "<code>&lt;th scope=\"col\"&gt;</code> cells, and body rows whose first column is the "
        "row header (<code>&lt;th scope=\"row\"&gt;</code>). It offers striped, bordered and "
        "compact variants, a sticky header that stays in place while the table scrolls "
        "inside a bounded box, a loading state, and three responsive strategies: "
        "<em>scroll</em> (default; the table scrolls sideways and becomes a focusable, "
        "labelled region only while it overflows), <em>stack</em> (each row becomes a card "
        "of label / value lines at or below <code>--mj-table-stack-breakpoint</code>, 480px "
        "by default) and <em>priority</em> (columns with the highest <code>priority</code> "
        "number are hidden first until the table fits).</p>"
        "<p>Data comes from the <code>columns</code> / <code>rows</code> properties, or from a "
        "light-DOM <code>&lt;table&gt;</code> child that is read once into columns and rows, "
        "so the page still shows a plain table when scripting is unavailable. It is not "
        "interactive: for sorting, filtering, selection or editing use "
        "<code>&lt;mj-data-table&gt;</code>.</p>"
    ),
    how_to_use=(
        "<p>Set <code>columns</code> to an array of <code>{ key, label, width?, rowHeader?, "
        "priority?, render?, cellClass?, cellAttrs? }</code> and <code>rows</code> to plain "
        "objects whose fields match the column keys. The first column is the row header "
        "unless it sets <code>rowHeader: false</code>; any other column may opt in with "
        "<code>rowHeader: true</code>. <code>render(row, col, index)</code> may return a "
        "string, a Node, an array of Nodes or a fragment; <code>cellAttrs</code> / "
        "<code>rowAttrs</code> stamp attributes on cells and rows (a <code>part</code> value "
        "makes them styleable from the page with <code>::part()</code>, as in the "
        "<em>Custom cells</em> example). Classes added by <code>rowClass</code> / "
        "<code>cellClass</code> live in the shadow root and cannot be targeted by page CSS.</p>"
        "<p>Alternatively write a normal <code>&lt;table&gt;</code> inside the element: its "
        "header row becomes the columns (keys <code>col0</code>, <code>col1</code>, ...) and "
        "its caption the <code>caption</code> attribute. Use the <code>caption</code> slot for "
        "rich caption content, <code>footer</code> for a summary row and <code>empty</code> "
        "for the no-rows message. <code>col-widths</code> takes comma-separated CSS widths "
        "for the <code>&lt;col&gt;</code> elements (lengths or percentages; <code>fr</code> "
        "units are not valid there). <code>summary</code> is helper text for assistive "
        "technology: it is visually hidden and linked with <code>aria-describedby</code>.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A striped table filled from the <code>columns</code> and <code>rows</code> "
                "properties. The first column renders as the row header. Try the "
                "<code>variant</code>, <code>sticky-header</code> and <code>loading</code> "
                "controls.</p>"
            ),
            html=r"""<mj-table id="demo-table" caption="Top fruits" variant="striped"></mj-table>""",
            script=r"""const table = document.getElementById("demo-table")
table.columns = [
  { key: "name", label: "Fruit" },
  { key: "color", label: "Colour" },
  { key: "calories", label: "kcal / 100 g" },
  { key: "origin", label: "Main producer" }
]
table.rows = [
  { name: "Apple", color: "Red", calories: 52, origin: "China" },
  { name: "Banana", color: "Yellow", calories: 89, origin: "India" },
  { name: "Mango", color: "Orange", calories: 60, origin: "India" },
  { name: "Kiwi", color: "Green", calories: 61, origin: "China" },
  { name: "Blueberry", color: "Blue", calories: 57, origin: "United States" }
]
""",
        ),
        ComponentExample(
            key="variants",
            title="Variants",
            description=(
                "<p>The same data as <code>bordered</code>, <code>compact</code> and the default "
                "look. The controls drive the first table.</p>"
            ),
            html=r"""<div class="variants">
  <mj-table id="bordered" caption="variant=&quot;bordered&quot;" variant="bordered"></mj-table>
  <mj-table id="compact" caption="variant=&quot;compact&quot;" variant="compact"></mj-table>
  <mj-table id="plain" caption="No variant"></mj-table>
</div>""",
            css=r""".variants {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: var(--mj-space-5);
  padding: var(--mj-space-3);
}""",
            script=r"""const columns = [
  { key: "city", label: "City" },
  { key: "country", label: "Country" },
  { key: "population", label: "Population (M)" }
]
const rows = [
  { city: "Tokyo", country: "Japan", population: 37.1 },
  { city: "Delhi", country: "India", population: 33.8 },
  { city: "Shanghai", country: "China", population: 29.9 },
  { city: "Sao Paulo", country: "Brazil", population: 22.8 }
]
for (const id of ["bordered", "compact", "plain"]) {
  const table = document.getElementById(id)
  table.columns = columns
  table.rows = rows
}
""",
        ),
        ComponentExample(
            key="declarative",
            title="Light-DOM table and slots",
            description=(
                "<p>No script: the element reads the <code>&lt;table&gt;</code> written inside it "
                "(its caption becomes the <code>caption</code> attribute). The "
                "<code>footer</code> slot adds a summary row, <code>summary</code> describes "
                "the table to screen readers and <code>col-widths</code> sizes the columns. "
                "Toggle the slots in the Slots panel.</p>"
            ),
            html=r"""<mj-table id="planets" variant="striped" col-widths="40%,30%,30%"
          summary="Average distance from the Sun in astronomical units, and the number of known moons.">
  <table>
    <caption>Inner planets</caption>
    <thead>
      <tr><th>Planet</th><th>Distance (AU)</th><th>Moons</th></tr>
    </thead>
    <tbody>
      <tr><td>Mercury</td><td>0.39</td><td>0</td></tr>
      <tr><td>Venus</td><td>0.72</td><td>0</td></tr>
      <tr><td>Earth</td><td>1.00</td><td>1</td></tr>
      <tr><td>Mars</td><td>1.52</td><td>2</td></tr>
    </tbody>
  </table>
  <span slot="footer">4 planets &middot; 3 moons in total</span>
</mj-table>""",
        ),
        ComponentExample(
            key="responsive",
            title="Responsive strategies",
            description=(
                "<p>Drag the corner of each dashed box to resize it. The first table uses "
                "<code>responsive=\"stack\"</code> and turns into cards at 480px or less; the "
                "second uses <code>responsive=\"priority\"</code> and drops the columns with "
                "the highest <code>priority</code> number first; the third scrolls and "
                "becomes a focusable region (use the arrow keys) while it overflows. Each "
                "<code>mj-table-overflow</code> change is logged with the table id.</p>"
            ),
            html=r"""<div class="box" id="box-stack">
  <mj-table id="orders" responsive="stack" caption="Orders (stack)"></mj-table>
</div>
<div class="box" id="box-priority">
  <mj-table id="servers" responsive="priority" caption="Servers (priority)"></mj-table>
</div>
<div class="box" id="box-scroll">
  <mj-table id="metrics" caption="Metrics (scroll)"></mj-table>
</div>""",
            css=r""".box {
  resize: horizontal;
  overflow: auto;
  inline-size: 640px;
  max-inline-size: 100%;
  min-inline-size: 220px;
  padding: var(--mj-space-2);
  margin: var(--mj-space-3);
  border: 1px dashed var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
}""",
            script=r"""const orders = document.getElementById("orders")
orders.columns = [
  { key: "id", label: "Order" },
  { key: "customer", label: "Customer" },
  { key: "total", label: "Total" },
  { key: "status", label: "Status" }
]
orders.rows = [
  { id: "SO-1042", customer: "Northwind Traders", total: "$1,280.00", status: "Shipped" },
  { id: "SO-1043", customer: "Contoso Ltd", total: "$312.50", status: "Packing" },
  { id: "SO-1044", customer: "Fabrikam Inc", total: "$89.90", status: "New" }
]

const servers = document.getElementById("servers")
servers.columns = [
  { key: "host", label: "Host" },
  { key: "region", label: "Region", priority: 2 },
  { key: "cpu", label: "CPU" },
  { key: "memory", label: "Memory", priority: 1 },
  { key: "uptime", label: "Uptime", priority: 3 },
  { key: "version", label: "Version", priority: 4 }
]
servers.rows = [
  { host: "web-01", region: "eu-west", cpu: "42%", memory: "6.1 GB", uptime: "41 days", version: "2.8.1" },
  { host: "web-02", region: "eu-west", cpu: "37%", memory: "5.8 GB", uptime: "41 days", version: "2.8.1" },
  { host: "db-01", region: "us-east", cpu: "71%", memory: "28.4 GB", uptime: "12 days", version: "15.4" }
]

const metrics = document.getElementById("metrics")
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
metrics.columns = [{ key: "metric", label: "Metric" }].concat(months.map((m) => ({ key: m, label: m })))
metrics.rows = ["Visitors", "Sign-ups", "Orders"].map((metric, i) => {
  const row = { metric: metric }
  months.forEach((m, mi) => { row[m] = String((i + 1) * 1000 + mi * 137) })
  return row
})

for (const table of [orders, servers, metrics]) {
  table.addEventListener("mj-table-overflow", (event) => {
    mjSandbox.log(table.id + " overflow", event.detail)
  })
}
""",
        ),
        ComponentExample(
            key="long-content",
            title="Sticky header and loading",
            description=(
                "<p>200 rows in a box bounded by <code>--mj-table-max-height</code> (260px here): "
                "with <code>sticky-header</code> the header stays in place while the body "
                "scrolls. The button toggles <code>loading</code>, which dims the table, sets "
                "<code>aria-busy</code> and announces the load.</p>"
            ),
            html=r"""<mj-table id="build-log" caption="Build log" variant="compact" sticky-header></mj-table>
<p><button type="button" id="toggle-loading">Toggle loading</button></p>""",
            css=r"""#build-log { --mj-table-max-height: 260px; }
p { margin: var(--mj-space-3); }""",
            script=r"""const table = document.getElementById("build-log")
const steps = ["checkout", "install", "lint", "test", "package", "publish"]
const results = ["passed", "passed", "passed", "failed", "skipped"]
table.columns = [
  { key: "build", label: "Build" },
  { key: "step", label: "Step" },
  { key: "result", label: "Result" },
  { key: "duration", label: "Duration" }
]
table.rows = Array.from({ length: 200 }, (_, i) => ({
  build: "#" + (4800 + Math.floor(i / steps.length)),
  step: steps[i % steps.length],
  result: results[(i * 7) % results.length],
  duration: ((i * 13) % 90 + 5) + " s"
}))
document.getElementById("toggle-loading").addEventListener("click", () => {
  table.loading = !table.loading
  mjSandbox.log("loading", { loading: table.loading })
})
""",
        ),
        ComponentExample(
            key="custom-cells",
            title="Custom cells and empty state",
            description=(
                "<p><code>render</code> returns Nodes (a status pill, a link), "
                "<code>rowHeader</code> moves the row header to the Title column, and "
                "<code>rowAttrs</code> / <code>cellAttrs</code> add <code>part</code> names "
                "(<code>tr-blocked</code>, <code>num</code>) that page CSS styles with "
                "<code>::part()</code>. The second table has no rows and shows its "
                "<code>empty</code> slot.</p>"
            ),
            html=r"""<mj-table id="tasks" caption="Sprint 42 tasks"></mj-table>
<mj-table id="archived" caption="Archived tasks">
  <span slot="empty">Nothing has been archived this sprint.</span>
</mj-table>""",
            css=r"""mj-table { margin-block-end: var(--mj-space-5); }
#tasks::part(tr-blocked) { background: var(--mj-color-warning-surface); }
#tasks::part(num) { text-align: end; font-variant-numeric: tabular-nums; }""",
            script=r"""const statusColours = {
  done: "var(--mj-color-success-surface)",
  doing: "var(--mj-color-info-surface)",
  blocked: "var(--mj-color-warning-surface)",
  todo: "var(--mj-bg-muted)"
}
function pill(status) {
  const span = document.createElement("span")
  span.textContent = status
  span.style.cssText = "padding: 0 var(--mj-space-2); border-radius: var(--mj-radius-pill);" +
    "background: " + statusColours[status] + "; font-size: var(--mj-font-size-xs);"
  return span
}
function link(row) {
  const a = document.createElement("a")
  a.href = "#task-" + row.id
  a.textContent = "Open"
  return a
}
const table = document.getElementById("tasks")
table.columns = [
  { key: "id", label: "ID", rowHeader: false, width: "4rem" },
  { key: "title", label: "Title", rowHeader: true },
  { key: "status", label: "Status", render: (row) => pill(row.status) },
  { key: "points", label: "Points", cellAttrs: () => ({ part: "td num" }) },
  { key: "open", label: "Actions", labelHidden: true, render: (row) => link(row) }
]
table.rowAttrs = (row) => ({
  "data-task-id": row.id,
  part: row.status === "blocked" ? "tr tr-blocked" : "tr"
})
table.rows = [
  { id: 101, title: "Design the export dialog", status: "done", points: 3 },
  { id: 102, title: "Write the CSV encoder", status: "doing", points: 5 },
  { id: 103, title: "Wait for the API key", status: "blocked", points: 2 },
  { id: 104, title: "Document the export format", status: "todo", points: 1 }
]

const archived = document.getElementById("archived")
archived.columns = table.columns.slice(0, 4)
archived.rows = []
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="caption",
            description="Visible caption that also names the table. Slotted `caption` content is shown instead when present.",
            kind="string",
            values=["Top fruits", "Quarterly sales"],
        ),
        AttributeDoc(
            name="summary",
            description="Helper text for assistive technology: rendered visually hidden and referenced by `aria-describedby`.",
            kind="string",
        ),
        AttributeDoc(
            name="variant",
            description="Visual style; one value at a time.",
            kind="enum",
            values=["striped", "bordered", "compact"],
        ),
        AttributeDoc(
            name="responsive",
            description=(
                "Narrow-width strategy: `scroll` scrolls sideways, `stack` turns rows into cards at or below "
                "`--mj-table-stack-breakpoint`, `priority` hides the columns with the highest `priority` number first."
            ),
            kind="enum",
            values=["scroll", "stack", "priority"],
            default="scroll",
        ),
        AttributeDoc(
            name="sticky-header",
            description="Bounds the table to `--mj-table-max-height` (24rem) and keeps the header row in place while it scrolls.",
            kind="boolean",
        ),
        AttributeDoc(
            name="loading",
            description="Dims the table, blocks pointer input, sets `aria-busy` and announces the load.",
            kind="boolean",
        ),
        AttributeDoc(
            name="col-widths",
            description="Comma-separated CSS widths for the `<col>` elements, in column order (lengths or percentages).",
            kind="string",
            values=["40%,30%,30%", "160px,120px,auto"],
        ),
        AttributeDoc(
            name="aria-label",
            description="Accessible name used when there is no caption (default: a generic table label).",
            kind="string",
        ),
    ],
    events=[
        (
            "mj-table-overflow",
            "The table started or stopped overflowing its box horizontally (also fires once after the first render).",
            "{ overflowing: boolean }",
        ),
    ],
    slots=[
        ("caption", "Rich caption content; replaces the `caption` attribute text.", "<strong>Fruit, ranked by sales</strong>"),
        ("footer", "Content of a full-width row in `<tfoot>`, shown below the body.", "<span>5 fruits listed</span>"),
        ("empty", "Message shown in the body while `rows` is empty (default: a generic no-data text).", "<span>No fruit in stock today.</span>"),
    ],
    properties=[
        ("columns", "object[]. Column definitions `{ key, label?, width?, rowHeader?, priority?, render?, cellClass?, cellAttrs? }`. Assigning replaces data read from a light-DOM table."),
        ("rows", "object[]. Row objects keyed by column `key`."),
        ("rowClass", "string | string[] | (row, index) => string | string[]. Classes added to each body `<tr>` (inside the shadow root)."),
        ("rowAttrs", "(row, index) => object. Attributes stamped on each body `<tr>`; `true` sets an empty attribute, `false` / `null` removes it."),
        ("loading", "boolean. Reflects the `loading` attribute."),
    ],
    parts=[
        ("scroll-wrapper", "The scrolling box around the table (a focusable region while it overflows)."),
        ("table", "The `<table>` element."),
        ("caption", "The `<caption>` element."),
        ("colgroup", "The `<colgroup>` holding one `<col>` per column."),
        ("thead", "The header section."),
        ("tbody", "The body section."),
        ("tfoot", "The footer section that holds the `footer` slot."),
        ("th", "Every header cell: column headers and row-header cells."),
        ("tr", "Every body row (extend with `rowAttrs` returning a `part`)."),
        ("td", "Every data cell (extend with `cellAttrs` returning a `part`)."),
    ],
    css_properties=[
        ("--mj-table-max-height", "Height of the scrolling box with `sticky-header` (default 24rem)."),
        ("--mj-table-stack-breakpoint", "Width in px at or below which `responsive=\"stack\"` shows cards (default 480)."),
        ("--mj-table-cell-padding-y", "Block padding of cells (default 10px; compact uses 4px)."),
        ("--mj-table-cell-padding-x", "Inline padding of cells (default 12px)."),
        ("--mj-table-border-color", "Row and cell border colour (default `--mj-border`)."),
        ("--mj-table-header-bg", "Header row background (default `--mj-bg-subtle`)."),
        ("--mj-table-stripe-bg", "Background of odd rows with `variant=\"striped\"` (default `--mj-bg-subtle`)."),
        ("--mj-table-row-header-weight", "Font weight of row-header cells (default `--mj-font-weight-medium`)."),
    ],
)


# ===========================================================================
# mj-data-table
# ===========================================================================

_DATA_TABLE = ComponentDoc(
    tag="mj-data-table",
    title="Data Table",
    group="data",
    summary="Interactive grid with sorting, filtering, selection, cell editing and virtualized rows.",
    description=(
        "<p><code>&lt;mj-data-table&gt;</code> is an interactive grid (<code>role=\"grid\"</code>) "
        "with a single roving tab stop over header and data cells. Only the visible rows "
        "(plus a small overscan) are in the DOM, so tens of thousands of rows stay fast. It "
        "sorts by clicking (or Enter / Space on) a sortable header, cycling ascending, "
        "descending and unsorted, with type- and locale-aware ordering and missing values "
        "last; it filters through an optional filter row (one text input per column) and a "
        "<code>globalFilter</code> that matches values in every column; it selects rows "
        "(<code>single</code> or <code>multi-row</code> with Shift range and Ctrl+A); it edits "
        "cells in place (double-click, Enter or F2; Enter commits, Escape cancels); and it "
        "resizes columns by dragging a header handle.</p>"
        "<p>Without an explicit height the body grows with its rows up to "
        "<code>--mj-dt-body-max-height</code> (400px) and then scrolls; a height set on the "
        "element wins. Data comes either from <code>rows</code> (sorted and filtered in the "
        "browser) or from a <code>dataSource</code> (an array, a fetcher function or an "
        "adapter object) that is queried page by page for the visible window with the "
        "current sort and filters.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>columns</code> (<code>{ key, label?, width?, sortable?, filterable?, "
        "editable?, resizable?, type?, compare?, render?, cellClass?, cellAttrs? }</code>; "
        "a number width is pixels, default 160px) and then <code>rows</code>. Give rows a "
        "stable identity with <code>row-key</code> (the field holding a unique id); without "
        "it a row's <code>__key</code> is used, else an id tied to the row object, so "
        "selection and edits follow the record through sorting and filtering. "
        "<code>selectedRows</code> holds those keys as strings.</p>"
        "<p>Add <code>sortable</code>, <code>filterable</code>, <code>resizable</code> and "
        "<code>selection</code> as needed; a column can opt out with "
        "<code>sortable: false</code> / <code>filterable: false</code> / "
        "<code>editable: false</code>. Cells are editable unless <code>mode=\"view\"</code>, "
        "the column sets <code>editable: false</code> or it has a <code>render</code> "
        "function; <code>mj-cell-edit-commit</code> is cancelable so you can validate, and "
        "numeric cells stay numbers. For server data set <code>dataSource</code> to "
        "<code>(query) =&gt; Promise&lt;{ items, total }&gt;</code> or an object with "
        "<code>query(query)</code> / <code>fetch(query)</code>; the query carries "
        "<code>offset</code>, <code>limit</code> (<code>page-size</code>), "
        "<code>sort</code>, <code>filter</code> (global text), <code>filters</code> (per "
        "column) and <code>filterKeys</code>. Slot a toolbar (search box, column picker) into "
        "<code>toolbar</code>, replace the row count with <code>footer</code>, and the "
        "no-results text with <code>empty</code>.</p>"
        "<p>Keyboard: arrow keys, Home / End, Ctrl+Home / Ctrl+End and PageUp / PageDown move "
        "between cells; Enter or Space on a sortable header sorts; Space toggles the row "
        "(Shift+Space extends a range); Ctrl+A selects all in <code>multi-row</code> mode; "
        "Enter or F2 edits the cell.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A sortable grid with single-row selection. Click a header to sort, click a "
                "row to select it, double-click a cell to edit it. Try the "
                "<code>selection</code>, <code>filterable</code> and <code>mode</code> "
                "controls.</p>"
            ),
            html=r"""<mj-data-table id="demo-dt" sortable selection="single" label="Team members"></mj-data-table>""",
            script=r"""const grid = document.getElementById("demo-dt")
grid.columns = [
  { key: "id", label: "ID", width: 70, editable: false },
  { key: "name", label: "Name", width: 170 },
  { key: "role", label: "Role", width: 150 },
  { key: "location", label: "Location", width: 150 },
  { key: "projects", label: "Projects", width: 100 }
]
grid.rows = [
  { id: 1, name: "Alice Martin", role: "Engineer", location: "Lisbon", projects: 4 },
  { id: 2, name: "Bob Chen", role: "Designer", location: "Toronto", projects: 2 },
  { id: 3, name: "Chiara Rossi", role: "Manager", location: "Milan", projects: 7 },
  { id: 4, name: "Dev Patel", role: "QA", location: "Pune", projects: 3 },
  { id: 5, name: "Eva Novak", role: "Engineer", location: "Prague", projects: 5 },
  { id: 6, name: "Femi Adeyemi", role: "Support", location: "Lagos", projects: 1 }
]
""",
        ),
        ComponentExample(
            key="large-data",
            title="10,000 rows",
            description=(
                "<p>10,000 generated rows with <code>row-key=\"id\"</code>, sorting, the filter "
                "row, resizable columns and multi-row selection (Shift-click for a range, "
                "Ctrl+A for all). Only the visible rows are rendered; the search box sets "
                "<code>globalFilter</code>. The line below the grid shows the match count and "
                "how many rows are in the DOM.</p>"
            ),
            html=r"""<div class="bar">
  <input type="search" id="global-search" placeholder="Search every column" aria-label="Search every column">
  <span id="status" aria-live="polite"></span>
</div>
<mj-data-table id="people" row-key="id" sortable filterable resizable selection="multi-row"
               label="Employees" style="height: 420px"></mj-data-table>""",
            css=r""".bar {
  display: flex;
  gap: var(--mj-space-3);
  align-items: center;
  margin-block-end: var(--mj-space-2);
}
#global-search { padding: var(--mj-space-1) var(--mj-space-2); min-inline-size: 16rem; }
#status { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }""",
            script=r"""const first = ["Ada", "Grace", "Alan", "Edsger", "Barbara", "Donald", "Frances", "Ken",
  "Margaret", "Niklaus", "Radia", "Tim", "Vint", "Whitfield", "Yukihiro", "Guido"]
const last = ["Lovelace", "Hopper", "Turing", "Dijkstra", "Liskov", "Knuth", "Allen", "Thompson",
  "Hamilton", "Wirth", "Perlman", "Lee", "Cerf", "Diffie", "Matsumoto", "Rossum"]
const departments = ["Engineering", "Design", "Sales", "Support", "Finance", "Operations"]
const cities = ["Berlin", "Lagos", "Lima", "Osaka", "Oslo", "Austin", "Pune", "Quebec", "Seoul"]
const rows = []
for (let i = 0; i < 10000; i += 1) {
  rows.push({
    id: i + 1,
    name: first[i % first.length] + " " + last[(i * 7 + Math.floor(i / 16)) % last.length],
    department: departments[(i * 5) % departments.length],
    city: cities[(i * 11) % cities.length],
    salary: 40000 + ((i * 7919) % 90000),
    started: (2005 + (i % 20)) + "-" + String((i % 12) + 1).padStart(2, "0") + "-" + String((i % 28) + 1).padStart(2, "0")
  })
}
const grid = document.getElementById("people")
grid.columns = [
  { key: "id", label: "ID", width: 80, editable: false },
  { key: "name", label: "Name", width: 190 },
  { key: "department", label: "Department", width: 150 },
  { key: "city", label: "City", width: 120 },
  { key: "salary", label: "Salary", width: 110, type: "number" },
  { key: "started", label: "Started", width: 120 }
]
grid.rows = rows

const status = document.getElementById("status")
function showStatus() {
  const rendered = grid.shadowRoot.querySelectorAll(".row").length
  status.textContent = grid.rowCount.toLocaleString() + " matching rows, " +
    grid.selectedRows.size + " selected, " + rendered + " row elements in the DOM"
}
document.getElementById("global-search").addEventListener("input", (event) => {
  grid.globalFilter = event.target.value
  showStatus()
})
for (const name of ["mj-sort-change", "mj-filter-change", "mj-selection-change"]) {
  grid.addEventListener(name, () => { requestAnimationFrame(showStatus) })
}
grid.shadowRoot.querySelector(".body-scroll").addEventListener("scroll", () => { requestAnimationFrame(showStatus) })
showStatus()
""",
        ),
        ComponentExample(
            key="editing",
            title="Editing and validation",
            description=(
                "<p>Double-click a cell, or focus it and press Enter or F2, to edit it. The "
                "script cancels <code>mj-cell-edit-commit</code> when Stock would become "
                "negative or not a number, and logs every edit. ID is "
                "<code>editable: false</code> and the Status column has a <code>render</code> "
                "function, so neither can be edited. Set <code>mode</code> to "
                "<code>view</code> to make the whole grid read-only.</p>"
            ),
            html=r"""<mj-data-table id="inventory" row-key="sku" sortable label="Inventory"></mj-data-table>
<p id="message" role="status"></p>""",
            css=r"""#message { margin: var(--mj-space-2) 0; color: var(--mj-text-muted); min-block-size: 1.5em; }""",
            script=r"""const grid = document.getElementById("inventory")
const message = document.getElementById("message")
grid.columns = [
  { key: "sku", label: "SKU", width: 110, editable: false },
  { key: "product", label: "Product", width: 200 },
  { key: "stock", label: "Stock", width: 90 },
  { key: "price", label: "Price", width: 90 },
  {
    key: "status", label: "Status", width: 120,
    render: (row) => row.stock === 0 ? "Sold out" : (row.stock < 10 ? "Low" : "In stock")
  }
]
grid.rows = [
  { sku: "KB-001", product: "Mechanical keyboard", stock: 42, price: 89 },
  { sku: "MS-014", product: "Wireless mouse", stock: 7, price: 29 },
  { sku: "HD-220", product: "USB-C hub", stock: 0, price: 45 },
  { sku: "MN-270", product: "27-inch monitor", stock: 15, price: 249 }
]
grid.addEventListener("mj-cell-edit-start", (event) => {
  message.textContent = "Editing " + event.detail.colKey + " of " + event.detail.rowKey
})
grid.addEventListener("mj-cell-edit-commit", (event) => {
  const detail = event.detail
  if (detail.colKey === "stock" && (typeof detail.newValue !== "number" || detail.newValue < 0)) {
    event.preventDefault()
    message.textContent = "Rejected: stock must be a number of zero or more."
    return
  }
  message.textContent = "Saved " + detail.colKey + " of " + detail.rowKey + ": " + detail.oldValue + " -> " + detail.newValue
  /* The Status column is derived from Stock: re-assign rows to refresh it. */
  requestAnimationFrame(() => { grid.rows = grid.rows.slice() })
})
""",
        ),
        ComponentExample(
            key="data-source",
            title="Remote data source",
            description=(
                "<p>A <code>dataSource</code> adapter whose <code>query()</code> waits 400ms "
                "and then sorts, filters and pages 10,000 rows, as a server would. The grid "
                "asks for the pages that cover the visible window (<code>page-size=\"50\"</code>; "
                "watch <code>mj-load-more</code> in Events while scrolling) and sends the sort "
                "and the filters with each query. Tick the box to make requests fail and see "
                "<code>mj-load-error</code>.</p>"
            ),
            html=r"""<label class="fail"><input type="checkbox" id="fail"> Make requests fail</label>
<mj-data-table id="remote" row-key="id" sortable filterable page-size="50" label="Orders"
               style="height: 360px"></mj-data-table>""",
            css=r""".fail { display: inline-flex; gap: var(--mj-space-2); margin-block-end: var(--mj-space-2); }""",
            script=r"""import { DataSource } from "/static/javascript/core/collection.js"

const customers = ["Northwind", "Contoso", "Fabrikam", "Tailspin", "Wingtip", "Litware", "Adventure Works"]
const states = ["New", "Paid", "Shipped", "Returned"]
const all = Array.from({ length: 10000 }, (_, i) => ({
  id: 50000 + i,
  customer: customers[(i * 3) % customers.length],
  state: states[(i * 7) % states.length],
  amount: Math.round(((i * 7919) % 100000) / 10) / 10
}))
const server = new DataSource(all)
const failBox = document.getElementById("fail")

const grid = document.getElementById("remote")
grid.columns = [
  { key: "id", label: "Order", width: 100 },
  { key: "customer", label: "Customer", width: 180 },
  { key: "state", label: "State", width: 120 },
  { key: "amount", label: "Amount", width: 110, type: "number" }
]
grid.dataSource = {
  query: async (query) => {
    mjSandbox.log("query", { offset: query.offset, limit: query.limit, sort: query.sort, filters: query.filters })
    await new Promise((resolve) => setTimeout(resolve, 400))
    if (failBox.checked === true) {
      throw new Error("Service unavailable")
    }
    return server.query(query)
  }
}
""",
        ),
        ComponentExample(
            key="slots-and-states",
            title="Slots, empty and loading",
            description=(
                "<p>The <code>toolbar</code> slot holds a title and a search box, the "
                "<code>footer</code> slot replaces the built-in row count, and the "
                "<code>empty</code> slot shows when the search matches nothing (type "
                "<em>zzz</em>). The second grid has <code>loading</code> set: the body is "
                "dimmed and <code>aria-busy</code> is true.</p>"
            ),
            html=r"""<mj-data-table id="books" sortable label="Books">
  <div slot="toolbar" class="toolbar">
    <strong>Library</strong>
    <input type="search" id="book-search" placeholder="Filter books" aria-label="Filter books">
  </div>
  <span slot="footer" id="book-footer"></span>
  <div slot="empty" class="empty">No book matches that search.</div>
</mj-data-table>
<mj-data-table id="busy" loading label="Loading example"></mj-data-table>""",
            css=r""".toolbar { display: flex; gap: var(--mj-space-3); align-items: center; justify-content: space-between; }
.empty { padding: var(--mj-space-5); text-align: center; color: var(--mj-text-muted); }
#busy { margin-block-start: var(--mj-space-4); }""",
            script=r"""const books = document.getElementById("books")
const footer = document.getElementById("book-footer")
books.columns = [
  { key: "title", label: "Title", width: 240 },
  { key: "author", label: "Author", width: 180 },
  { key: "year", label: "Year", width: 80 }
]
books.rows = [
  { title: "The Pragmatic Programmer", author: "Hunt and Thomas", year: 1999 },
  { title: "Structure and Interpretation of Computer Programs", author: "Abelson and Sussman", year: 1985 },
  { title: "Designing Data-Intensive Applications", author: "Martin Kleppmann", year: 2017 },
  { title: "Refactoring", author: "Martin Fowler", year: 1999 }
]
function updateFooter() {
  footer.textContent = books.rowCount + " of " + books.rows.length + " books shown"
}
document.getElementById("book-search").addEventListener("input", (event) => {
  books.globalFilter = event.target.value
  updateFooter()
})
updateFooter()

const busy = document.getElementById("busy")
busy.columns = books.columns
busy.rows = books.rows.slice(0, 2)
""",
        ),
        ComponentExample(
            key="events",
            title="Events and API",
            description=(
                "<p>The script drives the grid through its API and its UI: it sorts by Score "
                "with a header click, selects rows with <code>selectRow()</code> and clicks, "
                "filters with <code>filterState</code>, and finally clears the selection. Every "
                "step is in the Events panel.</p>"
            ),
            html=r"""<mj-data-table id="scores" row-key="player" sortable filterable selection="multi-row" label="Scores"></mj-data-table>""",
            script=r"""const grid = document.getElementById("scores")
grid.columns = [
  { key: "player", label: "Player", width: 160 },
  { key: "team", label: "Team", width: 120 },
  { key: "score", label: "Score", width: 100 }
]
grid.rows = [
  { player: "Mia", team: "Red", score: 87 },
  { player: "Noah", team: "Blue", score: 92 },
  { player: "Olga", team: "Red", score: 78 },
  { player: "Pavel", team: "Blue", score: 95 },
  { player: "Quinn", team: "Green", score: 81 }
]
const pause = () => new Promise((resolve) => setTimeout(resolve, 500))
const sr = grid.shadowRoot

await pause()
sr.querySelector('.header-cell[data-col-key="score"]').click()
await pause()
sr.querySelector('.header-cell[data-col-key="score"]').click()
await pause()
sr.querySelector('.row[data-row-key="Mia"] .cell').click()
sr.querySelector('.row[data-row-key="Olga"] .cell').click()
await pause()
grid.selectRow("Quinn")
mjSandbox.log("selectedRows after selectRow()", Array.from(grid.selectedRows))
await pause()
grid.filterState = { team: "Red" }
mjSandbox.log("rowCount with filterState team=Red", grid.rowCount)
await pause()
grid.filterState = {}
grid.clearSelection()
mjSandbox.log("selectedRows after clearSelection()", Array.from(grid.selectedRows))
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="selection",
            description="Row selection: `single` keeps one row, `multi-row` toggles rows (Shift range, Ctrl+A all).",
            kind="enum",
            values=["none", "single", "multi-row"],
            default="none",
        ),
        AttributeDoc(
            name="sortable",
            description="Every column sorts unless it sets `sortable: false` (a column can also opt in alone with `sortable: true`).",
            kind="boolean",
        ),
        AttributeDoc(
            name="filterable",
            description="Adds a filter row with one text input per column (except `filterable: false`); filters apply after 300 ms.",
            kind="boolean",
        ),
        AttributeDoc(
            name="resizable",
            description="Adds a pointer drag handle to every header (or per column with `resizable: true`); minimum width 60px.",
            kind="boolean",
        ),
        AttributeDoc(
            name="mode",
            description="`view` makes every cell read-only; `grid` allows editing of editable columns.",
            kind="enum",
            values=["grid", "view"],
            default="grid",
        ),
        AttributeDoc(
            name="row-key",
            description="Name of the row field holding a unique id; used for selection, edits and `selectedRows`.",
            kind="string",
            values=["id"],
        ),
        AttributeDoc(
            name="row-height",
            description="Row height in pixels (rows are virtualized at this fixed height).",
            kind="number",
            default="40",
        ),
        AttributeDoc(
            name="page-size",
            description="Rows per `dataSource` request.",
            kind="number",
            default="100",
        ),
        AttributeDoc(
            name="loading",
            description="Dims the body, blocks pointer input and sets `aria-busy`.",
            kind="boolean",
        ),
        AttributeDoc(
            name="empty-label",
            description="Text shown when there are no rows to show (fallback of the `empty` slot).",
            kind="string",
            values=["No results", "Nothing matches the filters"],
            default="No results",
        ),
        AttributeDoc(
            name="label",
            description="Accessible name of the grid (`aria-label` is used when it is absent).",
            kind="string",
            values=["Team members"],
        ),
    ],
    events=[
        ("mj-sort-change", "A header changed the sort (click, Enter or Space).", "{ key: string, direction: 'asc' | 'desc' | null }"),
        ("mj-filter-change", "A filter input changed (after the 300 ms delay).", "{ key: string, value: string, filterState: object }"),
        ("mj-selection-change", "The user changed the selection (not fired by `selectRow()` / `clearSelection()`).", "{ selectedRows: string[], rows: object[], selectedCell: null }"),
        ("mj-cell-edit-start", "Cancelable; a cell is about to enter edit mode.", "{ rowKey: string, colKey: string, value: any }"),
        ("mj-cell-edit-commit", "Cancelable; an edited value is about to be written to the row object.", "{ rowKey: string, colKey: string, oldValue: any, newValue: any }"),
        ("mj-column-resize", "A column resize drag ended.", "{ key: string, width: number }"),
        ("mj-load-more", "A `dataSource` page is being requested.", "{ offset: number, pageSize: number }"),
        ("mj-load-error", "A `dataSource` request failed; the footer shows an error message.", "{ error: any, offset: number }"),
    ],
    slots=[
        ("toolbar", "Content above the grid (title, search box, column picker).", '<div style="display:flex;justify-content:space-between"><strong>Team</strong><button type="button">Export</button></div>'),
        ("footer", "Replaces the built-in row count and load-error line below the grid.", "<span>Footer content</span>"),
        ("empty", "Shown in the body while there are no rows (fallback: `empty-label`).", "<span>No team members yet.</span>"),
    ],
    properties=[
        ("columns", "object[]. Column definitions `{ key, label?, width?, sortable?, filterable?, editable?, resizable?, type?, compare?, render?, cellClass?, cellAttrs? }`."),
        ("rows", "object[]. Client-side data; edits are written back to these objects."),
        ("dataSource", "array | (query) => Promise<{ items, total }> | { query(query) } | { fetch(query) } | null. Remote data, fetched page by page; null returns to `rows`."),
        ("sortState", "{ key, direction } | null. The current sort; assigning it sorts without an event."),
        ("filterState", "object. Column key to filter text; assigning it filters without an event."),
        ("globalFilter", "string. Text matched against the values of every column."),
        ("rowCount", "number (read-only). Rows after filtering (the reported total in remote mode)."),
        ("selectedRows", "Set<string> (read-only). Keys of the selected rows."),
        ("rowClass", "string | string[] | (row, index) => string | string[]. Classes added to each row element (inside the shadow root)."),
        ("rowAttrs", "(row, index) => object. Attributes stamped on each row element."),
        ("loading", "boolean. Reflects the `loading` attribute."),
    ],
    methods=[
        ("selectRow(key)", "Selects the row with that key (replacing the selection in `single` mode). No event."),
        ("selectAll()", "Selects every row of the current view (the loaded rows in remote mode). No event."),
        ("clearSelection()", "Deselects every row. No event."),
        ("focus(options)", "Moves focus to the cell that is the grid's tab stop."),
    ],
    parts=[
        ("toolbar", "Container of the `toolbar` slot."),
        ("grid-root", "The `role=grid` element."),
        ("header-row", "The column header row."),
        ("header-cell", "Each column header."),
        ("resize-handle", "The drag handle of a resizable column."),
        ("filter-row", "The filter row (with `filterable`)."),
        ("filter-input", "Each column filter input."),
        ("body", "The scrolling body."),
        ("body-inner", "The full-height inner box the rows are positioned in."),
        ("row", "Each rendered row."),
        ("cell", "Each data cell."),
        ("empty-state", "Container of the `empty` slot."),
        ("footer", "Container of the `footer` slot (row count by default)."),
    ],
    css_properties=[
        ("--mj-dt-body-max-height", "Height the body grows to before it scrolls when the element has no height (default 400px)."),
        ("--mj-dt-header-bg", "Header background (default `--mj-bg-subtle`)."),
        ("--mj-dt-selected-row-bg", "Selected row background (default a 10% accent tint)."),
    ],
)


# ===========================================================================
# mj-tree-grid
# ===========================================================================

_TREE_GRID = ComponentDoc(
    tag="mj-tree-grid",
    title="Tree Grid",
    group="data",
    summary="Hierarchical data grid following the WAI-ARIA treegrid pattern.",
    description=(
        "<p><code>&lt;mj-tree-grid&gt;</code> shows tree-structured rows in columns "
        "(<code>role=\"treegrid\"</code>): parent rows expand and collapse in place, child "
        "rows are indented, and only the visible rows of the flattened tree are rendered, so "
        "large trees stay fast. The first column holds the expander button and the row label; "
        "the other columns show values. Rows can be selected (<code>single</code> or multiple), "
        "<code>sortable</code> sorts the siblings of every level by the clicked column, and "
        "lazy parents (<code>hasChildren: true</code> without <code>children</code>) let you "
        "load children on demand with <code>setChildren()</code>.</p>"
        "<p>Rows are the roving tab stop. ArrowDown / ArrowUp move between rows, ArrowRight "
        "expands a collapsed parent or moves to its first child, ArrowLeft collapses or moves "
        "to the parent, Home / End go to the first / last row, Enter toggles expansion and "
        "Space toggles selection. Sortable headers are focusable and sort on Enter / Space. "
        "Without an explicit height the body grows up to <code>--mj-tg-body-max-height</code> "
        "(400px) and then scrolls.</p>"
    ),
    how_to_use=(
        "<p>Set <code>columns</code> (<code>{ key, label?, width?, sortable? }</code>; the first "
        "column defaults to 160px, the others to 120px) and <code>rows</code>: an array of "
        "<code>{ key, data?, children?, hasChildren? }</code> nodes with unique keys, whose "
        "values live in <code>data</code> or on the node itself. <code>expand-depth</code> "
        "expands that many levels on the first non-empty assignment; later assignments keep "
        "the expansion state, and <code>expandedKeys</code> takes it over completely. "
        "<code>mj-row-expand</code> / <code>mj-row-collapse</code> are cancelable.</p>"
        "<p>For lazy loading give a node <code>hasChildren: true</code>, listen for "
        "<code>mj-row-expand</code>, fetch, then call <code>setChildren(key, rows)</code>. "
        "<code>mode=\"view\"</code> makes the grid read-only (no selection). The "
        "<code>toolbar</code> and <code>footer</code> slots frame the grid and "
        "<code>empty-label</code> (or the <code>empty</code> slot) replaces the no-rows "
        "text.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A file tree with the top level expanded (<code>expand-depth=\"1\"</code>) "
                "and single-row selection. Click the triangles or use the arrow keys; Space "
                "selects the focused row.</p>"
            ),
            html=r"""<mj-tree-grid id="demo-tg" expand-depth="1" selection="single" label="Files"></mj-tree-grid>""",
            script=r"""const tree = document.getElementById("demo-tg")
tree.columns = [
  { key: "name", label: "Name", width: 240 },
  { key: "size", label: "Size", width: 100 },
  { key: "modified", label: "Modified", width: 130 }
]
tree.rows = [
  { key: "docs", data: { name: "Documents", size: "-", modified: "2026-10-02" }, children: [
    { key: "cv", data: { name: "CV.pdf", size: "120 KB", modified: "2026-09-12" } },
    { key: "cover", data: { name: "Cover letter.docx", size: "45 KB", modified: "2026-09-14" } },
    { key: "taxes", data: { name: "Taxes", size: "-", modified: "2026-04-30" }, children: [
      { key: "t2025", data: { name: "2025 return.pdf", size: "310 KB", modified: "2026-04-30" } }
    ] }
  ] },
  { key: "imgs", data: { name: "Images", size: "-", modified: "2026-10-20" }, children: [
    { key: "logo", data: { name: "logo.png", size: "32 KB", modified: "2026-10-20" } },
    { key: "banner", data: { name: "banner.svg", size: "8 KB", modified: "2026-10-19" } }
  ] },
  { key: "notes", data: { name: "notes.txt", size: "2 KB", modified: "2026-11-01" } }
]
""",
        ),
        ComponentExample(
            key="selection-and-sorting",
            title="Multi-select and sorting",
            description=(
                "<p>A budget tree with <code>sortable</code> headers (siblings are sorted on "
                "every level; click again for descending, a third time to clear) and "
                "multiple selection (<code>selection=\"multi-row\"</code>). The selected keys "
                "are listed under the grid.</p>"
            ),
            html=r"""<mj-tree-grid id="budget" sortable selection="multi-row" expand-depth="2" label="Budget"></mj-tree-grid>
<p id="picked">Selected: none</p>""",
            css=r"""#picked { margin: var(--mj-space-2) 0; color: var(--mj-text-muted); }""",
            script=r"""const tree = document.getElementById("budget")
tree.columns = [
  { key: "item", label: "Item", width: 220 },
  { key: "planned", label: "Planned", width: 110 },
  { key: "spent", label: "Spent", width: 110 }
]
tree.rows = [
  { key: "eng", item: "Engineering", planned: 420000, spent: 380500, children: [
    { key: "eng-cloud", item: "Cloud hosting", planned: 120000, spent: 131200 },
    { key: "eng-tools", item: "Tooling", planned: 40000, spent: 22100 },
    { key: "eng-hire", item: "Hiring", planned: 260000, spent: 227200 }
  ] },
  { key: "mkt", item: "Marketing", planned: 180000, spent: 96000, children: [
    { key: "mkt-events", item: "Events", planned: 90000, spent: 51000 },
    { key: "mkt-ads", item: "Online ads", planned: 90000, spent: 45000 }
  ] },
  { key: "ops", item: "Operations", planned: 75000, spent: 80250 }
]
tree.addEventListener("mj-selection-change", (event) => {
  const keys = event.detail.selectedRows
  document.getElementById("picked").textContent = "Selected: " + (keys.length > 0 ? keys.join(", ") : "none")
})
""",
        ),
        ComponentExample(
            key="lazy-children",
            title="Lazy children",
            description=(
                "<p>Each region has <code>hasChildren: true</code> but no children. Expanding "
                "one fires <code>mj-row-expand</code>; the script sets <code>loading</code>, "
                "waits 600ms as if calling a server, and supplies the rows with "
                "<code>setChildren()</code> (<code>mj-children-load</code> follows). Offices "
                "are lazy too, one level deeper.</p>"
            ),
            html=r"""<mj-tree-grid id="regions" expand-depth="0" label="Offices"></mj-tree-grid>""",
            script=r"""const tree = document.getElementById("regions")
tree.columns = [
  { key: "name", label: "Region / office", width: 240 },
  { key: "staff", label: "Staff", width: 90 }
]
tree.rows = [
  { key: "emea", data: { name: "EMEA", staff: 410 }, hasChildren: true },
  { key: "amer", data: { name: "Americas", staff: 655 }, hasChildren: true },
  { key: "apac", data: { name: "Asia Pacific", staff: 380 }, hasChildren: true }
]
const offices = {
  emea: ["London", "Berlin", "Nairobi"],
  amer: ["New York", "Austin", "Sao Paulo"],
  apac: ["Singapore", "Sydney", "Tokyo"]
}
const loaded = new Set()
tree.addEventListener("mj-row-expand", async (event) => {
  const key = event.detail.key
  if (loaded.has(key) === true) {
    return
  }
  loaded.add(key)
  tree.loading = true
  await new Promise((resolve) => setTimeout(resolve, 600))
  let children = []
  if (offices[key] !== undefined) {
    children = offices[key].map((city, i) => ({
      key: key + "-" + i, data: { name: city, staff: 40 + i * 17 }, hasChildren: true
    }))
  } else {
    children = ["Engineering", "Sales"].map((team, i) => ({
      key: key + "-" + i, data: { name: team, staff: 10 + i * 6 }
    }))
  }
  tree.setChildren(key, children)
  tree.loading = false
})
""",
        ),
        ComponentExample(
            key="large-data",
            title="Large tree and expandedKeys",
            description=(
                "<p>An organisation of about 3,000 rows (5 levels). The buttons assign "
                "<code>expandedKeys</code> to expand or collapse everything at once; only the "
                "visible rows are rendered.</p>"
            ),
            html=r"""<div class="bar">
  <button type="button" id="expand-all">Expand all</button>
  <button type="button" id="collapse-all">Collapse all</button>
  <span id="count"></span>
</div>
<mj-tree-grid id="org" expand-depth="1" selection="single" label="Organisation" style="height: 380px"></mj-tree-grid>""",
            css=r""".bar { display: flex; gap: var(--mj-space-2); align-items: center; margin-block-end: var(--mj-space-2); }
#count { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }""",
            script=r"""const tree = document.getElementById("org")
const allKeys = []
let total = 0
function build(prefix, level, max) {
  const count = level === 0 ? 4 : 6
  const nodes = []
  for (let i = 0; i < count; i += 1) {
    const key = prefix + "." + (i + 1)
    total += 1
    const node = { key: key, data: { unit: "Unit " + key.slice(1), level: level + 1, headcount: (level + 1) * 3 + i } }
    if (level < max) {
      allKeys.push(key)
      node.children = build(key, level + 1, max)
    }
    nodes.push(node)
  }
  return nodes
}
tree.columns = [
  { key: "unit", label: "Unit", width: 260 },
  { key: "level", label: "Level", width: 80 },
  { key: "headcount", label: "Headcount", width: 110 }
]
tree.rows = build("", 0, 4)
document.getElementById("count").textContent = total.toLocaleString() + " rows in the tree"
document.getElementById("expand-all").addEventListener("click", () => { tree.expandedKeys = allKeys })
document.getElementById("collapse-all").addEventListener("click", () => { tree.expandedKeys = [] })
""",
        ),
        ComponentExample(
            key="slots-and-states",
            title="Slots, view mode and empty",
            description=(
                "<p>The <code>toolbar</code> and <code>footer</code> slots frame a read-only "
                "grid (<code>mode=\"view\"</code> ignores <code>selection</code>). The second "
                "grid has no rows and shows <code>empty-label</code>.</p>"
            ),
            html=r"""<mj-tree-grid id="menu" mode="view" selection="single" expand-depth="1" label="Menu">
  <div slot="toolbar"><strong>Site menu</strong> (read-only)</div>
  <div slot="footer" class="footer">3 sections, 7 pages</div>
</mj-tree-grid>
<mj-tree-grid id="nothing" empty-label="No folders shared with you yet." label="Shared folders"></mj-tree-grid>""",
            css=r""".footer { padding: var(--mj-space-2); color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
#nothing { margin-block-start: var(--mj-space-4); }""",
            script=r"""const menu = document.getElementById("menu")
menu.columns = [{ key: "title", label: "Page", width: 220 }, { key: "path", label: "Path", width: 180 }]
menu.rows = [
  { key: "home", title: "Home", path: "/" },
  { key: "products", title: "Products", path: "/products", children: [
    { key: "p1", title: "Widgets", path: "/products/widgets" },
    { key: "p2", title: "Gadgets", path: "/products/gadgets" }
  ] },
  { key: "about", title: "About", path: "/about", children: [
    { key: "a1", title: "Team", path: "/about/team" },
    { key: "a2", title: "Careers", path: "/about/careers" },
    { key: "a3", title: "Contact", path: "/about/contact" }
  ] }
]
const nothing = document.getElementById("nothing")
nothing.columns = menu.columns
nothing.rows = []
""",
        ),
        ComponentExample(
            key="events",
            title="Keyboard and events",
            description=(
                "<p>The script focuses the grid and sends keys: ArrowRight expands "
                "<em>src</em>, ArrowRight moves into it, Space selects, ArrowLeft returns to "
                "the parent and Enter collapses it. A cancelable <code>mj-row-collapse</code> "
                "handler keeps the <em>locked</em> folder open. Watch the Events panel.</p>"
            ),
            html=r"""<mj-tree-grid id="repo" expand-depth="0" selection="single" label="Repository"></mj-tree-grid>""",
            script=r"""const tree = document.getElementById("repo")
tree.columns = [{ key: "name", label: "Path", width: 220 }, { key: "lines", label: "Lines", width: 90 }]
tree.rows = [
  { key: "src", name: "src", lines: 5120, children: [
    { key: "src/app.js", name: "app.js", lines: 840 },
    { key: "src/util.js", name: "util.js", lines: 210 }
  ] },
  { key: "locked", name: "locked (cannot collapse)", lines: 64, children: [
    { key: "locked/a", name: "keep-open.md", lines: 64 }
  ] }
]
tree.expandedKeys = ["locked"]
tree.addEventListener("mj-row-collapse", (event) => {
  if (event.detail.key === "locked") {
    event.preventDefault()
    mjSandbox.log("collapse prevented", event.detail)
  }
})
const pause = () => new Promise((resolve) => setTimeout(resolve, 450))
const press = (key) => tree.shadowRoot.activeElement.dispatchEvent(
  new KeyboardEvent("keydown", { key: key, bubbles: true, composed: true, cancelable: true }))
tree.focus()
for (const key of ["ArrowRight", "ArrowRight", " ", "ArrowLeft", "Enter"]) {
  await pause()
  press(key)
  mjSandbox.log("pressed " + (key === " " ? "Space" : key), { focused: tree.shadowRoot.activeElement.getAttribute("data-key") })
}
await pause()
tree.shadowRoot.querySelector('.row[data-key="locked"] .expander-btn').click()
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="expand-depth",
            description="Levels expanded on the first non-empty `rows` assignment; changing it later resets the expansion to that depth.",
            kind="number",
            default="1",
        ),
        AttributeDoc(
            name="selection",
            description="Row selection; any value other than `none` / `single` allows several rows (`multi-row`).",
            kind="enum",
            values=["none", "single", "multi-row"],
            default="none",
        ),
        AttributeDoc(
            name="sortable",
            description="Every column sorts the siblings on each level (unless `sortable: false`); removing it clears the sort.",
            kind="boolean",
        ),
        AttributeDoc(
            name="mode",
            description="`view` makes the grid read-only: rows cannot be selected.",
            kind="enum",
            values=["view"],
        ),
        AttributeDoc(
            name="loading",
            description="Dims the body, blocks pointer input and sets `aria-busy`.",
            kind="boolean",
        ),
        AttributeDoc(
            name="row-height",
            description="Row height in pixels (rows are virtualized at this fixed height).",
            kind="number",
            default="40",
        ),
        AttributeDoc(
            name="empty-label",
            description="Text shown when there are no rows (fallback of the `empty` slot).",
            kind="string",
            values=["No rows"],
        ),
        AttributeDoc(
            name="label",
            description="Accessible name of the treegrid (`aria-label` is used when it is absent).",
            kind="string",
            values=["Files"],
        ),
    ],
    events=[
        ("mj-row-expand", "Cancelable; a parent row is about to expand (also for lazy parents).", "{ key: any, level: number }"),
        ("mj-row-collapse", "Cancelable; a parent row is about to collapse.", "{ key: any, level: number }"),
        ("mj-selection-change", "The user changed the selection.", "{ selectedRows: any[] }"),
        ("mj-sort-change", "A sortable header changed the sort.", "{ key: string, direction: 'asc' | 'desc' | null }"),
        ("mj-children-load", "`setChildren()` supplied the rows of a parent.", "{ parentKey: any, rows: object[] }"),
    ],
    slots=[
        ("toolbar", "Content above the grid.", "<div><strong>Files</strong></div>"),
        ("footer", "Content below the grid.", "<div>Footer content</div>"),
        ("empty", "Shown while there are no rows (fallback: `empty-label`).", "<span>No files here yet.</span>"),
    ],
    properties=[
        ("columns", "object[]. Column definitions `{ key, label?, width?, sortable? }`; the first column holds the expander and row label."),
        ("rows", "object[]. Tree nodes `{ key, data?, children?, hasChildren? }`; re-assigning keeps the expansion state."),
        ("expandedKeys", "Set<any>. Keys of the expanded rows; assigning a Set or an array replaces the expansion (no events)."),
        ("selectedRows", "Set<any> (read-only). Keys of the selected rows."),
        ("sortState", "{ key, direction } | null. The current sort; assigning it sorts without an event."),
        ("loading", "boolean. Reflects the `loading` attribute."),
    ],
    methods=[
        ("setChildren(parentKey, rows)", "Supplies the children of a (lazy) parent; the parent keeps its expansion state. Emits `mj-children-load`."),
        ("focus(options)", "Moves focus to the row that is the grid's tab stop."),
    ],
    parts=[
        ("toolbar", "Container of the `toolbar` slot."),
        ("grid-root", "The `role=treegrid` element."),
        ("header-row", "The column header row."),
        ("header-cell", "Each column header."),
        ("body", "The scrolling body."),
        ("row", "Each rendered row (`row row-expanded` while expanded)."),
        ("row-expanded", "Added to expanded parent rows."),
        ("expander-cell", "The first cell (expander and label)."),
        ("expander-button", "The expand / collapse button (hidden on leaves)."),
        ("cell", "Each value cell after the first column."),
        ("empty-state", "Container of the `empty` slot."),
        ("footer", "Container of the `footer` slot."),
    ],
    css_properties=[
        ("--mj-tg-body-max-height", "Height the body grows to before it scrolls when the element has no height (default 400px)."),
        ("--mj-tg-hover-bg", "Row hover background (default `--mj-bg-muted`)."),
        ("--mj-tg-selected-bg", "Selected row background (default a 10% accent tint)."),
        ("--mj-tg-expander-size", "Size of the expander button (default 20px)."),
    ],
)


# ===========================================================================
# mj-list
# ===========================================================================

_LIST = ComponentDoc(
    tag="mj-list",
    title="List",
    group="data",
    summary="Semantic unordered, ordered or description list with nesting, dividers and densities.",
    description=(
        "<p><code>&lt;mj-list&gt;</code> renders a <code>&lt;ul&gt;</code>, <code>&lt;ol&gt;</code> "
        "or <code>&lt;dl&gt;</code> in its shadow root depending on <code>type</code>. Items "
        "come from the <code>items</code> property or from static <code>&lt;li&gt;</code> "
        "children in the default slot (shown while <code>items</code> is empty). A data item "
        "is plain text, a link (<code>href</code>) or a button (<code>action</code>), may carry "
        "a leading <code>icon</code> and may nest a list of <code>children</code>; in a "
        "description list each item is a term with one or more definitions.</p>"
        "<p>Markers follow the list type (bullets for unordered, decimal numbers for ordered) "
        "unless <code>marker</code> picks another style; <code>marker=\"none\"</code> keeps list "
        "semantics with <code>role=\"list\"</code>. <code>dividers</code> draws a border "
        "between items, <code>density</code> tightens or loosens the spacing, and nested lists "
        "inherit <code>marker</code>, <code>density</code> and <code>dividers</code>. Link "
        "<code>href</code>s pass through <code>safeUrl</code>, so <code>javascript:</code> "
        "URLs become <code>#</code>.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>items</code>: <code>{ label, href?, action?, icon?, description?, "
        "children? }</code>. <code>description</code> is used with "
        "<code>type=\"description\"</code> and may be a string or an array of strings (one "
        "<code>&lt;dd&gt;</code> each). Listen for <code>mj-item-click</code> to handle link and "
        "button items: the detail carries the item <code>index</code> and <code>label</code> "
        "(and <code>href</code> for links), not the <code>action</code> value, so look the item "
        "up with <code>list.items[event.detail.index]</code>. Link items still navigate.</p>"
        "<p>For static content write <code>&lt;li&gt;</code> children (or "
        "<code>&lt;dt&gt;</code> / <code>&lt;dd&gt;</code> for a description list) inside the "
        "element; markers and dividers apply to them too. <code>start</code> and "
        "<code>reversed</code> work like the native <code>&lt;ol&gt;</code> attributes.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>An unordered list of links from the <code>items</code> property. Try the "
                "<code>type</code>, <code>marker</code>, <code>density</code> and "
                "<code>dividers</code> controls.</p>"
            ),
            html=r"""<mj-list id="demo-list" marker="disc" density="spacious"></mj-list>""",
            script=r"""document.getElementById("demo-list").items = [
  { label: "Design tokens", href: "#tokens" },
  { label: "Components", href: "#components" },
  { label: "Patterns", href: "#patterns" },
  { label: "Accessibility", href: "#accessibility" }
]
""",
        ),
        ComponentExample(
            key="ordered",
            title="Ordered lists",
            description=(
                "<p><code>type=\"ordered\"</code> numbers items with decimal markers by default. "
                "The second list uses <code>marker=\"alpha\"</code> with <code>start=\"3\"</code>, "
                "the third <code>marker=\"roman\"</code> with <code>reversed</code>.</p>"
            ),
            html=r"""<div class="columns">
  <mj-list id="steps" type="ordered"></mj-list>
  <mj-list id="alpha" type="ordered" marker="alpha" start="3"></mj-list>
  <mj-list id="countdown" type="ordered" marker="roman" reversed></mj-list>
</div>""",
            css=r""".columns { display: flex; flex-wrap: wrap; gap: var(--mj-space-6); padding: var(--mj-space-3); }""",
            script=r"""const steps = [
  { label: "Install the package" },
  { label: "Import the components" },
  { label: "Add an element to the page" },
  { label: "Set its properties" }
]
for (const id of ["steps", "alpha", "countdown"]) {
  document.getElementById(id).items = steps
}
""",
        ),
        ComponentExample(
            key="description",
            title="Description list",
            description=(
                "<p><code>type=\"description\"</code> renders a <code>&lt;dl&gt;</code>: each item's "
                "<code>label</code> is a term and its <code>description</code> one or more "
                "definitions (an array gives several <code>&lt;dd&gt;</code>).</p>"
            ),
            html=r"""<mj-list id="glossary" type="description" dividers></mj-list>""",
            script=r"""document.getElementById("glossary").items = [
  { label: "Token", description: "A named design value such as a colour, a spacing step or a radius." },
  { label: "Slot", description: ["A placeholder in a component's shadow root.", "Light-DOM children are shown in it."] },
  { label: "Part", description: "An element inside the shadow root that page CSS can style with ::part()." }
]
""",
        ),
        ComponentExample(
            key="nested",
            title="Nesting, icons and dividers",
            description=(
                "<p>Items with <code>children</code> render a nested <code>&lt;mj-list&gt;</code> "
                "that inherits <code>marker</code>, <code>density</code> and "
                "<code>dividers</code> (change them with the controls). Items may carry a text "
                "<code>icon</code>.</p>"
            ),
            html=r"""<mj-list id="outline" marker="circle" density="compact" dividers></mj-list>""",
            script=r"""document.getElementById("outline").items = [
  { label: "Getting started", icon: "\u{1F680}", children: [
    { label: "Installation" },
    { label: "First component" }
  ] },
  { label: "Guides", icon: "\u{1F4D8}", children: [
    { label: "Theming", children: [{ label: "Tokens" }, { label: "Dark mode" }] },
    { label: "Forms" }
  ] },
  { label: "Changelog", icon: "\u{1F4DD}" }
]
""",
        ),
        ComponentExample(
            key="slotted-items",
            title="Static items (default slot)",
            description=(
                "<p>No script: the <code>&lt;li&gt;</code> children are slotted into the list and "
                "get its markers and dividers. The second list uses <code>marker=\"none\"</code>, "
                "which keeps list semantics through <code>role=\"list\"</code>.</p>"
            ),
            html=r"""<mj-list id="packing" marker="square" dividers>
  <li>Passport</li>
  <li>Charger and adapter</li>
  <li>Rain jacket</li>
</mj-list>
<mj-list id="plain" marker="none">
  <li><a href="#privacy">Privacy</a></li>
  <li><a href="#terms">Terms</a></li>
  <li><a href="#contact">Contact</a></li>
</mj-list>""",
            css=r"""mj-list { margin: var(--mj-space-3); }""",
        ),
        ComponentExample(
            key="events",
            title="Action items and events",
            description=(
                "<p>Items with an <code>action</code> render as buttons. The handler looks the "
                "item up by <code>event.detail.index</code> to get its action; the script "
                "clicks two of them so <code>mj-item-click</code> shows in Events.</p>"
            ),
            html=r"""<mj-list id="actions" marker="none" density="spacious"></mj-list>
<p id="last-action">No action yet.</p>""",
            css=r"""#last-action { margin: var(--mj-space-3); color: var(--mj-text-muted); }""",
            script=r"""const list = document.getElementById("actions")
list.items = [
  { label: "Rename file", action: "rename", icon: "✎" },
  { label: "Duplicate file", action: "duplicate", icon: "⎘" },
  { label: "Move to trash", action: "trash", icon: "\u{1F5D1}" }
]
list.addEventListener("mj-item-click", (event) => {
  const item = list.items[event.detail.index]
  document.getElementById("last-action").textContent = "Last action: " + item.action
  mjSandbox.log("action", { action: item.action, index: event.detail.index })
})
const buttons = list.shadowRoot.querySelectorAll("button")
buttons[0].click()
await new Promise((resolve) => setTimeout(resolve, 400))
buttons[2].click()
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="type",
            description="List element: `<ul>`, `<ol>` or `<dl>`.",
            kind="enum",
            values=["unordered", "ordered", "description"],
            default="unordered",
        ),
        AttributeDoc(
            name="marker",
            description=(
                "Marker style. Unordered lists take bullet / disc / circle / square, ordered lists decimal / alpha / roman; "
                "`none` hides markers. Default: bullet for unordered, decimal for ordered."
            ),
            kind="enum",
            values=["bullet", "disc", "circle", "square", "decimal", "alpha", "roman", "none"],
        ),
        AttributeDoc(
            name="density",
            description="Spacing between items (2px compact, 6px normal, 12px spacious).",
            kind="enum",
            values=["compact", "spacious"],
        ),
        AttributeDoc(
            name="dividers",
            description="Draws a border between items.",
            kind="boolean",
        ),
        AttributeDoc(
            name="nested",
            description="Indents the list; set automatically on the lists created for item `children`.",
            kind="boolean",
        ),
        AttributeDoc(
            name="start",
            description="First number of an ordered list.",
            kind="number",
        ),
        AttributeDoc(
            name="reversed",
            description="Numbers an ordered list downwards.",
            kind="boolean",
        ),
    ],
    events=[
        ("mj-item-click", "A link or button item was activated (links still navigate).", "{ index: number, label: string, href?: string }"),
    ],
    slots=[
        ("", "Static `<li>` items (or `<dt>` / `<dd>` with `type=\"description\"`), shown while `items` is empty.",
         "<li>First static item</li><li>Second static item</li>"),
    ],
    properties=[
        ("items", "object[]. Data items `{ label, href?, action?, icon?, description?, children? }`; an empty array shows the slotted items again."),
    ],
    parts=[
        ("list", "The `<ul>`, `<ol>` or `<dl>` element."),
        ("item", "Each `<li>` rendered from `items`."),
        ("item-icon", "The icon of an item."),
        ("term", "Each `<dt>` of a description list."),
        ("definition", "Each `<dd>` of a description list."),
    ],
    css_properties=[
        ("--mj-list-gap", "Space between items (default 6px)."),
        ("--mj-list-gap-compact", "Space between items with `density=\"compact\"` (default 2px)."),
        ("--mj-list-gap-spacious", "Space between items with `density=\"spacious\"` (default 12px)."),
        ("--mj-list-indent", "Marker indent, nested-list indent and definition indent (default 20px)."),
        ("--mj-list-divider-color", "Divider colour (default `--mj-border`)."),
        ("--mj-list-term-weight", "Font weight of description terms (default 600)."),
    ],
)


# ===========================================================================
# mj-virtual-list
# ===========================================================================

_VIRTUAL_LIST = ComponentDoc(
    tag="mj-virtual-list",
    title="Virtual List",
    group="data",
    summary="Virtualized one-dimensional list (WAI-ARIA feed) for very large or endless item sets.",
    description=(
        "<p><code>&lt;mj-virtual-list&gt;</code> keeps only the visible items plus an "
        "<code>overscan</code> buffer in the DOM, at a fixed <code>item-height</code>, so the "
        "DOM stays small whether the list holds fifty or a hundred thousand items. It follows "
        "the WAI-ARIA feed pattern: the box the items are positioned in is <code>role=\"feed\"</code> "
        "(it owns only the items; the Load more button, status regions and empty state sit outside "
        "it in the scroller), each item an <code>article</code> in a roving tab order. PageDown / PageUp (and ArrowDown / "
        "ArrowUp) move between items, Home / End go to the first / last loaded item, and "
        "Enter / Space activate the focused item.</p>"
        "<p>More items can be loaded in two ways. Host-driven: the list emits "
        "<code>mj-load-more</code> (from its Load more button, and with the default "
        "<code>load-strategy=\"intersection\"</code> also when the bottom of the list scrolls "
        "into view); the host fetches, calls <code>appendItems()</code> and sets "
        "<code>end-of-list</code> when done. Or through a <code>dataSource</code> (array, "
        "fetcher function or adapter object) that the list pages through itself, managing "
        "<code>loading</code>, <code>error</code> and <code>end-of-list</code>; when the source "
        "reports a <code>total</code> the scroller is sized for it and only the pages that "
        "cover the visible range are fetched.</p>"
    ),
    how_to_use=(
        "<p>Give the element a height (the default is <code>--mj-vl-container-height</code>, "
        "400px) and set <code>items</code>. Without <code>renderItem</code> an item shows its "
        "<code>label</code> (or its JSON). <code>renderItem(item, index)</code> may return a "
        "Node, the result of the <code>html</code> tag from <code>core/html.js</code>, or a "
        "string, which is inserted <em>as markup</em>: escape interpolated data with "
        "<code>escapeHtml</code> or build a Node with <code>textContent</code>. Items render "
        "inside the shadow root, so style them inline or with tokens. "
        "<code>keyExtractor(item, index)</code> supplies the <code>key</code> of "
        "<code>mj-item-click</code>.</p>"
        "<p>A list offers more items (the Load more button, and with the intersection strategy "
        "the sentinel that emits <code>mj-load-more</code>) until it is complete: "
        "<code>end-of-list</code> is set, or it holds <code>total</code> items. So give a list "
        "that never grows its <code>total</code> (or <code>end-of-list</code>); until then its "
        "<code>aria-setsize</code> is <code>total</code> or -1 (unknown). A <code>dataSource</code> is "
        "<code>({ offset, limit }) =&gt; Promise&lt;{ items, total? }&gt;</code>, an object with "
        "<code>query()</code> / <code>fetch()</code>, or an array. The <code>loading</code>, "
        "<code>error</code>, <code>end</code> and <code>empty</code> slots label those states.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A message list loaded 50 at a time with "
                "<code>load-strategy=\"manual\"</code>: the Load more button emits "
                "<code>mj-load-more</code>, the host sets <code>loading</code>, appends the page "
                "with <code>appendItems()</code> and sets <code>end-of-list</code> after 250 "
                "messages. Scroll, or click an item.</p>"
            ),
            html=r"""<mj-virtual-list id="demo-vl" item-height="44" load-strategy="manual" page-size="50"
                 style="height: 220px">
  <span slot="loading">Loading 50 more messages...</span>
  <span slot="end">That is everything: 250 messages.</span>
</mj-virtual-list>""",
            script=r"""const list = document.getElementById("demo-vl")
const senders = ["Ana", "Bram", "Chloe", "Dmitri", "Esi", "Farid"]
const subjects = ["Lunch on Friday?", "Build is green", "Design review notes", "Invoice 2026-114", "Travel plans"]
function message(i) {
  return { id: "m" + i, label: (i + 1) + ". " + senders[i % senders.length] + ": " + subjects[i % subjects.length] }
}
list.renderItem = (item) => {
  const row = document.createElement("div")
  row.textContent = item.label
  row.style.cssText = "padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border);"
  return row
}
list.keyExtractor = (item) => item.id
list.items = Array.from({ length: 50 }, (_, i) => message(i))
list.addEventListener("mj-load-more", async (event) => {
  list.loading = true
  await new Promise((resolve) => setTimeout(resolve, 500))
  const offset = event.detail.offset
  list.appendItems(Array.from({ length: event.detail.pageSize }, (_, i) => message(offset + i)))
  list.loading = false
  if (list.items.length >= 250) {
    list.setAttribute("end-of-list", "")
  }
})
""",
        ),
        ComponentExample(
            key="large-data",
            title="10,000 items",
            description=(
                "<p>10,000 generated items in a static list (<code>end-of-list</code> and "
                "<code>total=\"10000\"</code> mark it complete). <code>renderItem</code> returns "
                "escaped markup. The line above the list follows <code>mj-items-rendered</code>: "
                "however far you scroll, only a dozen item elements exist.</p>"
            ),
            html=r"""<p id="window-info">-</p>
<mj-virtual-list id="contacts" item-height="56" overscan="4" end-of-list total="10000"
                 style="height: 340px"></mj-virtual-list>""",
            css=r"""#window-info { margin: 0 0 var(--mj-space-2); color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }""",
            script=r"""import { escapeHtml } from "/static/javascript/core/html.js"

const first = ["Ada", "Bea", "Cyrus", "Dalia", "Emil", "Fumiko", "Goran", "Hana", "Ines", "Jonas"]
const last = ["Okafor", "Lindqvist", "Moreau", "Tanaka", "Silva", "Novak", "Haddad", "Kowalski"]
const items = Array.from({ length: 10000 }, (_, i) => {
  const name = first[i % first.length] + " " + last[(i * 3) % last.length]
  return { id: i + 1, name: name, email: name.toLowerCase().replace(" ", ".") + (i + 1) + "@example.test" }
})
const list = document.getElementById("contacts")
list.renderItem = (item) =>
  '<div style="padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border)">' +
  "<strong>" + escapeHtml(item.name) + '</strong> <span style="color: var(--mj-text-muted)">#' + item.id + "</span><br>" +
  '<small style="color: var(--mj-text-muted)">' + escapeHtml(item.email) + "</small></div>"
list.keyExtractor = (item) => String(item.id)
const info = document.getElementById("window-info")
list.addEventListener("mj-items-rendered", (event) => {
  const count = list.shadowRoot.querySelectorAll(".vl-item").length
  info.textContent = "Showing items " + (event.detail.startIndex + 1) + "-" + event.detail.endIndex +
    " of " + event.detail.total.toLocaleString() + " (" + count + " item elements in the DOM)"
})
list.items = items
""",
        ),
        ComponentExample(
            key="infinite-scroll",
            title="Infinite scroll with a data source",
            description=(
                "<p>A <code>dataSource</code> fetcher that returns 25 posts per call after "
                "600ms and no <code>total</code>. With the default intersection strategy the "
                "next page loads as the end of the list scrolls into view; the list manages "
                "<code>loading</code> and sets <code>end-of-list</code> when a short page "
                "arrives (after 120 posts).</p>"
            ),
            html=r"""<mj-virtual-list id="feed" item-height="64" page-size="25" style="height: 320px">
  <span slot="loading">Loading more posts...</span>
  <span slot="end">You are all caught up.</span>
</mj-virtual-list>""",
            script=r"""const authors = ["@river", "@sol", "@kai", "@noor", "@ivy"]
const topics = ["shipped a new release", "wrote about caching", "asked about testing", "shared a design sketch"]
const posts = Array.from({ length: 120 }, (_, i) => ({
  label: authors[i % authors.length] + " " + topics[(i * 3) % topics.length] + " (post " + (i + 1) + ")"
}))
const feed = document.getElementById("feed")
feed.renderItem = (item) => {
  const card = document.createElement("div")
  card.textContent = item.label
  card.style.cssText = "padding: var(--mj-space-3); border-block-end: 1px solid var(--mj-border);"
  return card
}
feed.dataSource = async ({ offset, limit }) => {
  await new Promise((resolve) => setTimeout(resolve, 600))
  return { items: posts.slice(offset, offset + limit) }
}
""",
        ),
        ComponentExample(
            key="remote-total",
            title="Remote data with a known total",
            description=(
                "<p>The fetcher reports <code>total: 50000</code>, so the scroller is sized for "
                "all items at once. Drag the scrollbar anywhere: only the page under the "
                "visible range is fetched (watch <code>mj-load-more</code> offsets in "
                "Events), and items appear when it arrives.</p>"
            ),
            html=r"""<mj-virtual-list id="ledger" item-height="40" page-size="100" style="height: 300px">
  <span slot="loading">Fetching rows...</span>
</mj-virtual-list>""",
            script=r"""const ledger = document.getElementById("ledger")
ledger.renderItem = (item) => {
  const row = document.createElement("div")
  row.textContent = "Entry " + item.n.toLocaleString() + " - balance " + item.balance.toFixed(2)
  row.style.cssText = "padding: var(--mj-space-2) var(--mj-space-3); font-variant-numeric: tabular-nums;"
  return row
}
ledger.dataSource = {
  query: async ({ offset, limit }) => {
    await new Promise((resolve) => setTimeout(resolve, 350))
    const items = Array.from({ length: limit }, (_, i) => ({ n: offset + i + 1, balance: ((offset + i) * 37.13) % 10000 }))
    return { items: items, total: 50000 }
  }
}
""",
        ),
        ComponentExample(
            key="states",
            title="Empty, loading and error",
            description=(
                "<p>Three lists: an empty one (<code>end-of-list</code>, so it does not offer "
                "to load more) showing its <code>empty</code> slot; one with "
                "<code>loading</code> set; and one whose data source fails, showing the "
                "<code>error</code> slot with a Retry button that succeeds.</p>"
            ),
            html=r"""<div class="states">
  <mj-virtual-list id="empty-list" end-of-list>
    <span slot="empty">No notifications.</span>
  </mj-virtual-list>
  <mj-virtual-list id="loading-list" loading>
    <span slot="loading">Loading notifications...</span>
  </mj-virtual-list>
  <mj-virtual-list id="error-list">
    <span slot="error">Could not load notifications. <button type="button" id="retry">Retry</button></span>
  </mj-virtual-list>
</div>""",
            css=r""".states { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: var(--mj-space-4); }
.states mj-virtual-list { --mj-vl-container-height: 180px; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }""",
            script=r"""const list = document.getElementById("error-list")
let attempts = 0
const source = async ({ offset, limit }) => {
  attempts += 1
  await new Promise((resolve) => setTimeout(resolve, 300))
  if (attempts === 1) {
    throw new Error("Network error")
  }
  return { items: Array.from({ length: 8 }, (_, i) => ({ label: "Notification " + (offset + i + 1) })), total: 8 }
}
list.dataSource = source
document.getElementById("retry").addEventListener("click", () => {
  list.dataSource = source
})
""",
        ),
        ComponentExample(
            key="events",
            title="Keyboard and events",
            description=(
                "<p>The script focuses the list and presses PageDown three times, Enter "
                "(<code>mj-item-click</code> with the <code>keyExtractor</code> key) and End. "
                "Scrolling to the bottom also fires <code>mj-scroll-end</code>.</p>"
            ),
            html=r"""<mj-virtual-list id="keys" item-height="40" end-of-list total="40" style="height: 200px"></mj-virtual-list>""",
            script=r"""const list = document.getElementById("keys")
list.keyExtractor = (item) => item.sku
list.items = Array.from({ length: 40 }, (_, i) => ({ sku: "SKU-" + (1000 + i), label: "Product " + (i + 1) }))
const pause = () => new Promise((resolve) => setTimeout(resolve, 400))
const press = (key) => list.shadowRoot.activeElement.dispatchEvent(
  new KeyboardEvent("keydown", { key: key, bubbles: true, composed: true, cancelable: true }))
list.focus()
for (const key of ["PageDown", "PageDown", "PageDown", "Enter", "End"]) {
  await pause()
  press(key)
  mjSandbox.log("pressed " + key, { focused: list.shadowRoot.activeElement.getAttribute("data-index") })
}
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="item-height",
            description="Height of every item in pixels (items are positioned at this fixed height).",
            kind="number",
            default="48",
        ),
        AttributeDoc(
            name="overscan",
            description="Extra items rendered above and below the visible range.",
            kind="number",
            default="3",
        ),
        AttributeDoc(
            name="page-size",
            description="Items per `dataSource` request, and the `pageSize` of `mj-load-more`.",
            kind="number",
            default="50",
        ),
        AttributeDoc(
            name="total",
            description="Known item count for host-loaded lists, announced as `aria-setsize` on every item; once the list holds that many items it is complete (as with `end-of-list`). A `dataSource` reports its own total.",
            kind="number",
        ),
        AttributeDoc(
            name="load-strategy",
            description="`intersection` also requests more items when the end of the list scrolls into view; `manual` only from the Load more button.",
            kind="enum",
            values=["intersection", "manual"],
            default="intersection",
        ),
        AttributeDoc(
            name="loading",
            description="Shows the loading region (spinner and `loading` slot), disables Load more and holds back further requests. Managed automatically with a `dataSource`.",
            kind="boolean",
        ),
        AttributeDoc(
            name="error",
            description="Shows the error region (`error` slot). Set automatically when a `dataSource` request fails.",
            kind="boolean",
        ),
        AttributeDoc(
            name="end-of-list",
            description="Everything is loaded: hides Load more, stops requests and shows the `end` slot (also implied once a host-loaded list holds `total` items).",
            kind="boolean",
        ),
        AttributeDoc(
            name="load-more-label",
            description="Text of the Load more button.",
            kind="string",
            values=["Load more", "Show older messages"],
            default="Load more",
        ),
        AttributeDoc(
            name="empty-label",
            description="Text shown while the list has no items (fallback of the `empty` slot).",
            kind="string",
            values=["No items"],
            default="No items",
        ),
    ],
    events=[
        ("mj-load-more", "More items are wanted (host-driven), or a `dataSource` page is being fetched.", "{ offset: number, pageSize: number }"),
        ("mj-load-error", "A `dataSource` request failed.", "{ error: any, offset: number }"),
        ("mj-item-click", "An item was clicked, or activated with Enter / Space.", "{ index: number, key: string, item: any }"),
        ("mj-items-rendered", "The rendered window changed (after every render).", "{ startIndex: number, endIndex: number, total: number }"),
        ("mj-scroll-end", "The user scrolled to within 50px of the end.", "{ scrollTop: number }"),
    ],
    slots=[
        ("loading", "Text next to the spinner while `loading` is set.", "<span>Loading more items...</span>"),
        ("error", "Shown while `error` is set (for example with a retry button).", '<span>Could not load. <button type="button">Retry</button></span>'),
        ("end", "Shown below the items once `end-of-list` is set.", "<span>No more items.</span>"),
        ("empty", "Shown while there are no items and nothing is loading (fallback: `empty-label`).", "<span>Nothing here yet.</span>"),
    ],
    properties=[
        ("items", "any[]. The loaded items (with a `dataSource`, sparse until pages arrive)."),
        ("dataSource", "array | ({ offset, limit }) => Promise<{ items, total? }> | { query() } | { fetch() } | null. Assigning resets the list and loads the first page."),
        ("renderItem", "(item, index) => Node | html`` result | string | null. A string is inserted as markup: escape interpolated data."),
        ("keyExtractor", "(item, index) => string. The `key` reported by `mj-item-click` (default: the index)."),
        ("loading", "boolean. Reflects the `loading` attribute."),
    ],
    methods=[
        ("appendItems(items)", "Appends items to the end of the list (host-driven loading)."),
        ("focus(options)", "Focuses the item that is the roving tab stop."),
    ],
    parts=[
        ("container", "The scroller around the feed, the load-more area and the empty state."),
        ("inner", "The full-height `role=feed` box the items are positioned in (no role while it holds no item and is not loading)."),
        ("item", "Each rendered item (`role=article`)."),
        ("sentinel", "The 1px marker at the end used by the intersection strategy."),
        ("load-more-button", "The Load more button."),
        ("loading-state", "The loading region."),
        ("error-state", "The error region."),
        ("end-state", "The end-of-list region."),
        ("empty-state", "The empty placeholder."),
        ("status-region", "The visually hidden live region announcing loaded pages."),
    ],
    css_properties=[
        ("--mj-vl-container-height", "Height of the element when no height is set on it (default 400px)."),
    ],
)


# ===========================================================================
# mj-kanban
# ===========================================================================

_KANBAN = ComponentDoc(
    tag="mj-kanban",
    title="Kanban Board",
    group="data",
    summary="Board of columns and cards with drag-and-drop, a keyboard move mode and WIP limits.",
    description=(
        "<p><code>&lt;mj-kanban&gt;</code> renders a board of columns, each holding a stack of "
        "cards. Cards move by dragging their handle (HTML5 drag for the mouse, pointer events for "
        "touch and pen) to any position in any column, or with the keyboard: Enter / Space on a "
        "handle starts move mode, ArrowLeft / ArrowRight pick the column, ArrowUp / ArrowDown the "
        "position, Enter or Space drops the card and Escape cancels; focus stays on the moved "
        "card's handle. Enter / Space on a card itself emits <code>mj-card-click</code>.</p>"
        "<p>With <code>wip-limits</code> each column that sets <code>wipLimit</code> shows a "
        "<code>count/limit</code> badge styled as at-limit (count equals the limit) or exceeded "
        "(count above it), and <code>mj-col-wip-exceeded</code> fires when a move pushes a column "
        "over its limit. Moves are announced in a live region. The board is a labelled "
        "<code>region</code>, columns are groups and the body of a column that holds cards is a "
        "list (an empty column shows its <code>empty-[id]</code> slot in a plain container, "
        "since a list may own only list items).</p>"
    ),
    how_to_use=(
        "<p>Set <code>columns</code> to <code>[{ id, label, wipLimit?, cards: [{ id, title, ... }] }]</code>. "
        "The board updates this array in place when cards move, so it is always the current "
        "state. <code>mj-card-move-start</code> and <code>mj-card-move</code> are cancelable "
        "(prevent a move into a column, for example); <code>toIndex</code> counts the target "
        "column's cards without the moved card. <code>renderCard(card)</code> may return a Node "
        "or markup (escape interpolated data with <code>core/html.js</code>).</p>"
        "<p>Per column the board provides the slots <code>column-header-[id]</code> (extra header "
        "content), <code>add-card-[id]</code> (a footer, typically an add button) and "
        "<code>empty-[id]</code> (shown while the column has no cards), plus "
        "<code>loading</code>. For a backend set <code>dataSource</code> to an object with "
        "<code>fetchBoard()</code> (resolving the columns) and <code>moveCard(cardId, toColId, "
        "toIndex)</code>; a rejected <code>moveCard</code> moves the card back and fires "
        "<code>mj-card-move-error</code>. <code>mode=\"readonly\"</code> removes the handles.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Four columns with WIP badges (<code>wip-limits</code>; In Progress allows two "
                "cards) and an empty Review column showing its <code>empty-review</code> slot. "
                "Drag a card by its handle, or focus the handle and use Enter, the arrow keys "
                "and Enter.</p>"
            ),
            html=r"""<mj-kanban id="demo-kb" wip-limits label="Sprint board">
  <span slot="empty-review" class="empty">Nothing waiting for review</span>
</mj-kanban>""",
            css=r""".empty { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); padding: var(--mj-space-2); }""",
            script=r"""document.getElementById("demo-kb").columns = [
  { id: "todo", label: "To Do", cards: [
    { id: "c1", title: "Write tests" },
    { id: "c2", title: "Update README" }
  ] },
  { id: "wip", label: "In Progress", wipLimit: 2, cards: [
    { id: "c3", title: "Refactor API" }
  ] },
  { id: "review", label: "Review", cards: [] },
  { id: "done", label: "Done", cards: [
    { id: "c4", title: "Deploy v1.0" }
  ] }
]
""",
        ),
        ComponentExample(
            key="wip-limits",
            title="WIP limits",
            description=(
                "<p>Doing is at its limit (badge <em>2/2</em>), Testing already exceeds it. "
                "Move one more card into Doing to get <code>mj-col-wip-exceeded</code>; the "
                "handler shows a warning. Remove <code>wip-limits</code> with the control to "
                "hide the badges.</p>"
            ),
            html=r"""<mj-kanban id="flow" wip-limits label="Delivery flow"></mj-kanban>
<p id="warning" role="status"></p>""",
            css=r"""#warning { margin: var(--mj-space-2) var(--mj-space-3); color: var(--mj-color-warning); min-block-size: 1.5em; }""",
            script=r"""const board = document.getElementById("flow")
board.columns = [
  { id: "ready", label: "Ready", cards: [{ id: "r1", title: "Export to CSV" }, { id: "r2", title: "Dark mode" }] },
  { id: "doing", label: "Doing", wipLimit: 2, cards: [{ id: "d1", title: "Login rate limit" }, { id: "d2", title: "Audit log" }] },
  { id: "testing", label: "Testing", wipLimit: 1, cards: [{ id: "t1", title: "Search filters" }, { id: "t2", title: "Billing page" }] }
]
board.addEventListener("mj-col-wip-exceeded", (event) => {
  const { colId, count, limit } = event.detail
  document.getElementById("warning").textContent = colId + " now holds " + count + " cards; its limit is " + limit + "."
})
""",
        ),
        ComponentExample(
            key="custom-cards",
            title="Custom cards and layout",
            description=(
                "<p><code>renderCard</code> builds each card from its data (assignee, tags, due "
                "date). <code>col-width=\"220\"</code> narrows the columns and "
                "<code>layout=\"fluid\"</code> wraps them onto new rows instead of scrolling "
                "sideways. Clicking a card fires <code>mj-card-click</code>.</p>"
            ),
            html=r"""<mj-kanban id="team" col-width="220" layout="fluid" label="Team board"></mj-kanban>""",
            script=r"""const board = document.getElementById("team")
board.renderCard = (card) => {
  const box = document.createElement("div")
  const title = document.createElement("div")
  title.textContent = card.title
  title.style.fontWeight = "var(--mj-font-weight-medium)"
  const meta = document.createElement("div")
  meta.style.cssText = "display: flex; gap: var(--mj-space-1); flex-wrap: wrap; margin-block-start: var(--mj-space-1); font-size: var(--mj-font-size-xs); color: var(--mj-text-muted);"
  const who = document.createElement("span")
  who.textContent = card.assignee
  who.style.cssText = "padding: 0 var(--mj-space-1); border-radius: var(--mj-radius-pill); background: var(--mj-bg-muted);"
  meta.append(who)
  for (const tag of card.tags) {
    const chip = document.createElement("span")
    chip.textContent = "#" + tag
    meta.append(chip)
  }
  const due = document.createElement("span")
  due.textContent = "due " + card.due
  meta.append(due)
  box.append(title, meta)
  return box
}
board.columns = [
  { id: "backlog", label: "Backlog", cards: [
    { id: "k1", title: "Offline mode", assignee: "Lee", tags: ["mobile"], due: "Dec 2" },
    { id: "k2", title: "Usage report", assignee: "Ama", tags: ["data", "pm"], due: "Dec 9" }
  ] },
  { id: "design", label: "Design", cards: [
    { id: "k3", title: "Onboarding flow", assignee: "Sam", tags: ["ux"], due: "Nov 21" }
  ] },
  { id: "build", label: "Build", cards: [
    { id: "k4", title: "Payment retries", assignee: "Ira", tags: ["api"], due: "Nov 18" }
  ] },
  { id: "ship", label: "Ship", cards: [] }
]
board.addEventListener("mj-card-click", (event) => {
  mjSandbox.log("opened card", event.detail)
})
""",
        ),
        ComponentExample(
            key="slots",
            title="Column slots",
            description=(
                "<p>Every column gets a <code>column-header-[id]</code> slot (here a card count "
                "menu button), an <code>add-card-[id]</code> slot (an Add card button that "
                "appends a card to <code>columns</code>) and an <code>empty-[id]</code> slot. "
                "Add cards to the empty Ideas column to see its empty slot disappear.</p>"
            ),
            html=r"""<mj-kanban id="slotted" label="Content plan">
  <button type="button" slot="column-header-ideas" class="menu" aria-label="Ideas options">&#8943;</button>
  <span slot="empty-ideas" class="empty">No ideas yet: add the first one.</span>
  <button type="button" slot="add-card-ideas" class="add" data-col="ideas">+ Add card</button>
  <button type="button" slot="add-card-writing" class="add" data-col="writing">+ Add card</button>
  <button type="button" slot="add-card-published" class="add" data-col="published">+ Add card</button>
</mj-kanban>""",
            css=r""".add { inline-size: 100%; padding: var(--mj-space-1); border: 1px dashed var(--mj-border-strong); background: transparent; color: var(--mj-text-muted); border-radius: var(--mj-radius-sm); cursor: pointer; }
.menu { margin-inline-start: auto; border: none; background: transparent; color: var(--mj-text-muted); cursor: pointer; }
.empty { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); padding: var(--mj-space-2); }""",
            script=r"""const board = document.getElementById("slotted")
board.columns = [
  { id: "ideas", label: "Ideas", cards: [] },
  { id: "writing", label: "Writing", cards: [{ id: "w1", title: "Release notes 3.2" }] },
  { id: "published", label: "Published", cards: [{ id: "p1", title: "Migration guide" }] }
]
let next = 1
board.addEventListener("click", (event) => {
  const button = event.target.closest(".add")
  if (button === null) {
    return
  }
  const column = board.columns.find((col) => col.id === button.dataset.col)
  column.cards.push({ id: "new-" + next, title: "New card " + next })
  next += 1
  board.columns = board.columns
  mjSandbox.log("added card", { column: column.id, cards: column.cards.length })
})
""",
        ),
        ComponentExample(
            key="data-source",
            title="Data source, loading and move errors",
            description=(
                "<p>A <code>dataSource</code> whose <code>fetchBoard()</code> resolves after a "
                "second (the <code>loading</code> slot shows meanwhile) and whose "
                "<code>moveCard()</code> rejects every move into Archived: the card snaps back "
                "and <code>mj-card-move-error</code> is logged. Other moves complete with "
                "<code>mj-card-move-complete</code>.</p>"
            ),
            html=r"""<mj-kanban id="remote-board" label="Support tickets">
  <span slot="loading" class="loading">Loading the board...</span>
</mj-kanban>""",
            css=r""".loading { display: block; padding: var(--mj-space-3); color: var(--mj-text-muted); }""",
            script=r"""const board = document.getElementById("remote-board")
board.dataSource = {
  fetchBoard: async () => {
    await new Promise((resolve) => setTimeout(resolve, 1000))
    return [
      { id: "open", label: "Open", cards: [{ id: "T-101", title: "Cannot reset password" }, { id: "T-102", title: "Invoice missing" }] },
      { id: "pending", label: "Pending", cards: [{ id: "T-099", title: "Feature request: SSO" }] },
      { id: "archived", label: "Archived (rejects moves)", cards: [] }
    ]
  },
  moveCard: async (cardId, toColId, toIndex) => {
    await new Promise((resolve) => setTimeout(resolve, 300))
    if (toColId === "archived") {
      throw new Error("Archiving is not allowed for " + cardId)
    }
    return true
  }
}
""",
        ),
        ComponentExample(
            key="events",
            title="Keyboard move and events",
            description=(
                "<p>The script moves <em>Write copy</em> with the keyboard (Enter on its handle, "
                "ArrowRight, Enter), then tries to move a card out of Done, which the "
                "cancelable <code>mj-card-move</code> handler refuses. Follow the sequence in "
                "Events.</p>"
            ),
            html=r"""<mj-kanban id="keyboard-board" label="Launch checklist"></mj-kanban>""",
            script=r"""const board = document.getElementById("keyboard-board")
board.columns = [
  { id: "todo", label: "To Do", cards: [{ id: "a", title: "Write copy" }, { id: "b", title: "Pick a date" }] },
  { id: "doing", label: "Doing", cards: [{ id: "c", title: "Record demo" }] },
  { id: "done", label: "Done (locked)", cards: [{ id: "d", title: "Book venue" }] }
]
board.addEventListener("mj-card-move", (event) => {
  if (event.detail.fromColId === "done") {
    event.preventDefault()
    mjSandbox.log("move refused: Done is locked", event.detail)
  }
})
const pause = () => new Promise((resolve) => setTimeout(resolve, 450))
const press = (key) => board.shadowRoot.activeElement.dispatchEvent(
  new KeyboardEvent("keydown", { key: key, bubbles: true, composed: true, cancelable: true }))

board.shadowRoot.querySelector('.card[data-card-id="a"] .card-handle').focus()
for (const key of ["Enter", "ArrowRight", "Enter"]) {
  await pause()
  press(key)
}
await pause()
board.shadowRoot.querySelector('.card[data-card-id="d"] .card-handle').focus()
for (const key of ["Enter", "ArrowLeft", "Enter"]) {
  await pause()
  press(key)
}
mjSandbox.log("columns now", board.columns.map((col) => col.id + ": " + col.cards.map((card) => card.id).join(",")))
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="mode",
            description="`readonly` removes the drag handles, so cards cannot be moved (they stay clickable).",
            kind="enum",
            values=["interactive", "readonly"],
            default="interactive",
        ),
        AttributeDoc(
            name="wip-limits",
            description="Shows `count/limit` badges for columns with `wipLimit` and enables `mj-col-wip-exceeded`.",
            kind="boolean",
        ),
        AttributeDoc(
            name="layout",
            description="`fluid` wraps columns onto new rows instead of scrolling the board sideways.",
            kind="enum",
            values=["fluid"],
        ),
        AttributeDoc(
            name="col-width",
            description="Column width: a number of pixels or any CSS length (sets `--mj-kanban-col-width`).",
            kind="string",
            values=["220", "18rem", "320px"],
            default="280px",
        ),
        AttributeDoc(
            name="loading",
            description="Shows the `loading` slot above the board and sets `aria-busy`. Managed automatically by `dataSource.fetchBoard()`.",
            kind="boolean",
        ),
        AttributeDoc(
            name="label",
            description="Accessible name of the board region (`aria-label` is used when it is absent).",
            kind="string",
            values=["Sprint board"],
        ),
    ],
    events=[
        ("mj-card-click", "A card was clicked, or Enter / Space was pressed on it.", "{ cardId: string, colId: string }"),
        ("mj-card-move-start", "Cancelable; a drag or keyboard move is starting.", "{ cardId: string, fromColId: string, fromIndex: number }"),
        ("mj-card-move", "Cancelable; a card is about to be dropped at a new position.", "{ cardId: string, fromColId: string, toColId: string, toIndex: number }"),
        ("mj-card-move-complete", "A move finished (after `dataSource.moveCard()` resolved, when there is one).", "{ cardId: string, fromColId: string, toColId: string, toIndex: number }"),
        ("mj-card-move-error", "`dataSource.moveCard()` rejected; the card was moved back.", "{ cardId: string, error: any }"),
        ("mj-col-wip-exceeded", "A move put more cards in a column than its `wipLimit` (with `wip-limits`).", "{ colId: string, count: number, limit: number }"),
        ("mj-board-error", "`dataSource.fetchBoard()` rejected.", "{ error: any }"),
    ],
    slots=[
        ("column-header-todo", "Extra header content of one column; the name is `column-header-[column id]` (here the To Do column).",
         '<button type="button" aria-label="To Do options">&#8943;</button>'),
        ("add-card-todo", "Footer of one column, typically an add button; the name is `add-card-[column id]`.",
         '<button type="button">+ Add card</button>'),
        ("empty-review", "Shown while one column has no cards; the name is `empty-[column id]` (here the Review column).",
         "<span>Nothing waiting for review</span>"),
        ("loading", "Shown above the board while `loading` is set.", "<span>Loading the board...</span>"),
    ],
    properties=[
        ("columns", "object[]. `[{ id, label, wipLimit?, cards: [{ id, title, ... }] }]`; updated in place when cards move."),
        ("dataSource", "{ fetchBoard(): Promise<columns>, moveCard?(cardId, toColId, toIndex): Promise } | null. Assigning loads the board."),
        ("renderCard", "(card) => Node | string | html`` result | null. Custom card content; a string is inserted as markup."),
        ("loading", "boolean. Reflects the `loading` attribute."),
    ],
    parts=[
        ("board", "The board region holding the columns."),
        ("column", "Each column."),
        ("column-header", "A column's header row (title, slot, badge)."),
        ("wip-indicator", "The `count/limit` badge."),
        ("column-body", "The list of cards of a column."),
        ("column-footer", "Container of the `add-card-[id]` slot."),
        ("card", "Each card."),
        ("card-handle", "The drag / keyboard-move handle of a card."),
        ("drop-zone", "The insertion marker shown while dragging or moving."),
        ("loading", "Container of the `loading` slot."),
    ],
    css_properties=[
        ("--mj-kanban-col-width", "Column width (default 280px; set by `col-width`)."),
        ("--mj-kanban-col-gap", "Space between columns (default 12px)."),
        ("--mj-kanban-col-bg", "Column background (default `--mj-bg-subtle`)."),
        ("--mj-kanban-card-gap", "Space between cards (default 8px)."),
        ("--mj-kanban-card-bg", "Card background (default `--mj-surface`)."),
        ("--mj-kanban-card-radius", "Card corner radius (default `--mj-radius-md`)."),
        ("--mj-kanban-wip-ok-color", "Badge colour at the limit (default `--mj-text`)."),
        ("--mj-kanban-wip-exceeded-color", "Badge colour above the limit (default `--mj-color-warning`)."),
        ("--mj-kanban-drag-opacity", "Opacity of the card being dragged (default 0.5)."),
        ("--mj-kanban-drop-zone-color", "Colour of the active drop marker (default `--mj-accent`)."),
    ],
)


# ===========================================================================
# mj-calendar
# ===========================================================================

_CALENDAR = ComponentDoc(
    tag="mj-calendar",
    title="Calendar",
    group="data",
    summary="Calendar in month, week, day or agenda view with event chips; form-associated.",
    description=(
        "<p><code>&lt;mj-calendar&gt;</code> shows a period with a toolbar (previous / next "
        "buttons, the period label and a view switcher) and the events that fall into it. "
        "<em>Month</em> is a grid of weeks with up to <code>event-overflow</code> chips per day "
        "and a <em>+N more</em> button that expands the day in place; <em>week</em> and "
        "<em>day</em> list the period's days with all their events (there is no hourly time "
        "grid yet); <em>agenda</em> lists the displayed month's events grouped by day. "
        "Weekday names, the period label and dates are formatted for <code>locale</code> (or "
        "the library locale), and the week starts on the locale's first day unless "
        "<code>first-day-of-week</code> says otherwise.</p>"
        "<p>All dates are local calendar days: <code>value</code>, <code>min</code>, "
        "<code>max</code> and event dates written as <code>YYYY-MM-DD</code> are never parsed as "
        "UTC, and every date the component reports is the local <code>YYYY-MM-DD</code>. The "
        "element is form-associated: with a <code>name</code> it submits the selected day, "
        "<code>required</code> makes it invalid until a day is selected, and a form reset clears "
        "the selection. One day cell is the tab stop: arrow keys move by day and week, Home / "
        "End to the start / end of the week, PageUp / PageDown by month (with Shift by year), "
        "crossing into other periods as needed, and Enter / Space select the focused day.</p>"
    ),
    how_to_use=(
        "<p>Set <code>events</code> to <code>[{ id, title, start, end?, color? }]</code> where "
        "<code>start</code> / <code>end</code> are <code>Date</code> objects, ISO strings or "
        "<code>YYYY-MM-DD</code> local days (an event that ends at midnight does not cover that "
        "day); <code>color</code> is any CSS colour: the chip shows it as a start stripe and a light "
        "tint behind the text, which stays <code>--mj-text</code>, so every colour keeps its contrast "
        "in both themes. "
        "<code>view</code> picks the view and <code>value</code> the displayed date; "
        "<code>value</code> follows navigation (the attribute is updated) and stays the displayed "
        "date even when a day is selected (read <code>selectedDate</code> for that). "
        "<code>min</code> / <code>max</code> disable the days outside the range.</p>"
        "<p>For events per period set <code>dataSource</code> to an object with "
        "<code>fetchEvents(start, end)</code> (two <code>Date</code>s) returning a Promise of "
        "events; it is called for every new period while <code>loading</code> is set. Listen "
        "for <code>mj-date-select</code>, <code>mj-event-click</code>, "
        "<code>mj-period-change</code> and <code>mj-view-change</code>; "
        "in an editable calendar a click / Enter / Space on a day first emits the cancelable "
        "<code>mj-event-create</code> (a host can open a new-event form); its default action is "
        "the selection, so <code>preventDefault()</code> keeps the previous selection and no "
        "<code>mj-date-select</code> follows. <code>readonly</code> selects without asking. "
        "Put extra toolbar content in "
        "<code>toolbar-start</code> / <code>toolbar-end</code>.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>The current month with a few events. Click a day (<code>mj-date-select</code>) "
                "or a chip (<code>mj-event-click</code>), navigate with the arrows, switch views "
                "with the toolbar buttons or the <code>view</code> control.</p>"
            ),
            html=r"""<mj-calendar id="demo-cal" view="month"></mj-calendar>""",
            script=r"""const today = new Date()
const y = today.getFullYear()
const m = today.getMonth()
document.getElementById("demo-cal").events = [
  { id: "e1", title: "Team standup", start: new Date(y, m, 3, 9, 0), end: new Date(y, m, 3, 9, 30) },
  { id: "e2", title: "Design review", start: new Date(y, m, 10, 14, 0), end: new Date(y, m, 10, 15, 0),
    color: "var(--mj-chart-series-2)" },
  { id: "e3", title: "Release 3.2", start: new Date(y, m, 20, 11, 0), end: new Date(y, m, 20, 12, 0),
    color: "var(--mj-chart-series-3)" },
  { id: "e4", title: "Conference", start: new Date(y, m, 24), end: new Date(y, m, 27) },
  { id: "e5", title: "Lunch with Sam", start: new Date(y, m, today.getDate(), 12, 30), end: new Date(y, m, today.getDate(), 13, 30) }
]
""",
        ),
        ComponentExample(
            key="views",
            title="Week and agenda views",
            description=(
                "<p><code>view=\"week\"</code> lists the seven days of the current week with all "
                "their events; the second calendar uses <code>view=\"agenda\"</code>, the month's "
                "events grouped by day. Use the toolbar to switch views "
                "(<code>mj-view-change</code>).</p>"
            ),
            html=r"""<mj-calendar id="week" view="week"></mj-calendar>
<mj-calendar id="agenda" view="agenda"></mj-calendar>""",
            css=r"""#agenda { margin-block-start: var(--mj-space-4); }""",
            script=r"""const now = new Date()
const at = (dayOffset, hour, minutes) =>
  new Date(now.getFullYear(), now.getMonth(), now.getDate() + dayOffset, hour, minutes || 0)
const events = [
  { id: "w1", title: "Planning", start: at(0, 9), end: at(0, 10) },
  { id: "w2", title: "Customer call", start: at(1, 15), end: at(1, 15, 45), color: "var(--mj-chart-series-4)" },
  { id: "w3", title: "Code review", start: at(1, 11), end: at(1, 12) },
  { id: "w4", title: "Offsite", start: at(2, 8), end: at(3, 18), color: "var(--mj-chart-series-2)" },
  { id: "w5", title: "Retro", start: at(-1, 16), end: at(-1, 17) }
]
document.getElementById("week").events = events
document.getElementById("agenda").events = events
""",
        ),
        ComponentExample(
            key="limits-and-locale",
            title="Locale, week start and date limits",
            description=(
                "<p><code>locale=\"de-DE\"</code> formats the labels and weekday names in German, "
                "<code>first-day-of-week=\"1\"</code> starts weeks on Monday, and "
                "<code>min</code> / <code>max</code> (set by the script to the 5th and the 25th "
                "of this month) disable the other days. <code>readonly</code> keeps "
                "<code>mj-event-create</code> from firing. Try another <code>locale</code> in the "
                "controls.</p>"
            ),
            html=r"""<mj-calendar id="limited" locale="de-DE" first-day-of-week="1" readonly></mj-calendar>""",
            script=r"""const calendar = document.getElementById("limited")
const now = new Date()
const key = (day) => now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0") + "-" + String(day).padStart(2, "0")
calendar.setAttribute("min", key(5))
calendar.setAttribute("max", key(25))
calendar.events = [
  { id: "l1", title: "Sprint start", start: key(6) },
  { id: "l2", title: "Sprint end", start: key(19), color: "var(--mj-chart-series-5)" }
]
""",
        ),
        ComponentExample(
            key="overflow",
            title="Busy days (+N more)",
            description=(
                "<p>With <code>event-overflow=\"2\"</code> a day shows two chips and a "
                "<em>+N more</em> button that expands the day in place (and <em>Show less</em> "
                "collapses it). The 12th has six events.</p>"
            ),
            html=r"""<mj-calendar id="busy" event-overflow="2"></mj-calendar>""",
            script=r"""const now = new Date()
const y = now.getFullYear()
const m = now.getMonth()
const titles = ["Standup", "1:1 with Ana", "Budget review", "Hiring panel", "Vendor demo", "Board prep"]
const events = titles.map((title, i) => ({
  id: "b" + i, title: title, start: new Date(y, m, 12, 9 + i), end: new Date(y, m, 12, 10 + i),
  color: i % 2 === 0 ? undefined : "var(--mj-chart-series-" + (i % 6 + 1) + ")"
}))
events.push({ id: "b9", title: "Dentist", start: new Date(y, m, 13, 8), end: new Date(y, m, 13, 9) })
document.getElementById("busy").events = events
""",
        ),
        ComponentExample(
            key="form",
            title="Form field",
            description=(
                "<p>A named, <code>required</code> calendar inside a form. Submitting without "
                "picking a day reports it as invalid; after a click the form submits the "
                "selected local day (<code>FormData</code> is shown below). Reset clears the "
                "selection while <code>value</code> keeps the displayed month.</p>"
            ),
            html=r"""<form id="booking">
  <mj-calendar id="appointment" name="appointment" required></mj-calendar>
  <div class="actions">
    <button type="submit">Book</button>
    <button type="reset">Reset</button>
  </div>
  <output id="result">Pick a day, then book.</output>
</form>""",
            css=r""".actions { display: flex; gap: var(--mj-space-2); margin-block: var(--mj-space-3); }
output { color: var(--mj-text-muted); }""",
            script=r"""const form = document.getElementById("booking")
const calendar = document.getElementById("appointment")
const result = document.getElementById("result")
form.addEventListener("submit", (event) => {
  event.preventDefault()
  if (calendar.checkValidity() === false) {
    result.textContent = "Invalid: " + (calendar.validationMessage || "a day is required")
    return
  }
  const data = Object.fromEntries(new FormData(form).entries())
  result.textContent = "Submitted " + JSON.stringify(data)
  mjSandbox.log("submitted", data)
})
form.addEventListener("reset", () => {
  setTimeout(() => {
    result.textContent = "Reset: selectedDate is " + calendar.selectedDate + ", value is " + calendar.value
  }, 0)
})
""",
        ),
        ComponentExample(
            key="data-source",
            title="Data source and events",
            description=(
                "<p>A <code>dataSource</code> whose <code>fetchEvents(start, end)</code> invents "
                "three events for whatever period is shown, after 500ms (<code>loading</code> is "
                "set meanwhile). The <code>toolbar-end</code> slot adds a Today button. The script "
                "then clicks next, switches to week view and goes back, so "
                "<code>mj-period-change</code> and <code>mj-view-change</code> appear in "
                "Events.</p>"
            ),
            html=r"""<mj-calendar id="remote-cal">
  <button type="button" slot="toolbar-end" id="today">Today</button>
</mj-calendar>""",
            script=r"""const calendar = document.getElementById("remote-cal")
calendar.dataSource = {
  fetchEvents: async (start, end) => {
    mjSandbox.log("fetchEvents", { start: start.toDateString(), end: end.toDateString() })
    await new Promise((resolve) => setTimeout(resolve, 500))
    const span = Math.max(1, Math.round((end - start) / 86400000))
    return [1, 2, 3].map((n) => {
      const day = new Date(start.getFullYear(), start.getMonth(), start.getDate() + Math.floor(span * n / 4))
      return { id: start.toDateString() + n, title: "Shift " + n, start: new Date(day.getTime() + 9 * 3600000), end: new Date(day.getTime() + 17 * 3600000) }
    })
  }
}
document.getElementById("today").addEventListener("click", () => {
  const now = new Date()
  calendar.value = new Date(now.getFullYear(), now.getMonth(), now.getDate())
})
const pause = () => new Promise((resolve) => setTimeout(resolve, 800))
const sr = calendar.shadowRoot
await pause()
sr.querySelector('[part="next-button"]').click()
await pause()
sr.querySelector('.view-btn[data-view="week"]').click()
await pause()
sr.querySelector('[part="prev-button"]').click()
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="view",
            description="The view shown (week and day list the days with their events; no hourly grid).",
            kind="enum",
            values=["month", "week", "day", "agenda"],
            default="month",
        ),
        AttributeDoc(
            name="value",
            description="Displayed date as local `YYYY-MM-DD`; updated as the user navigates (not the selection).",
            kind="string",
            values=["2026-11-10", "2025-06-01"],
        ),
        AttributeDoc(
            name="min",
            description="First selectable day (`YYYY-MM-DD`); earlier days are disabled.",
            kind="string",
        ),
        AttributeDoc(
            name="max",
            description="Last selectable day (`YYYY-MM-DD`); later days are disabled.",
            kind="string",
        ),
        AttributeDoc(
            name="first-day-of-week",
            description="First weekday column, 0 (Sunday) to 6 (Saturday). Default: the locale's week start.",
            kind="enum",
            values=["0", "1", "2", "3", "4", "5", "6"],
        ),
        AttributeDoc(
            name="locale",
            description="BCP 47 locale for labels, weekday names and the default week start; invalid tags fall back to the library locale.",
            kind="string",
            values=["en-US", "en-GB", "de-DE", "fr-FR", "ja-JP", "ar-EG"],
        ),
        AttributeDoc(
            name="event-overflow",
            description="Chips shown per day in month view before a `+N more` button.",
            kind="number",
            default="3",
        ),
        AttributeDoc(
            name="readonly",
            description="Days are selected without the cancelable `mj-event-create` first.",
            kind="boolean",
        ),
        AttributeDoc(
            name="loading",
            description="Sets `aria-busy`; managed automatically while `dataSource.fetchEvents()` runs.",
            kind="boolean",
        ),
        AttributeDoc(
            name="name",
            description="Form field name; the form submits the selected day (`YYYY-MM-DD`), nothing while none is selected.",
            kind="string",
            values=["appointment"],
        ),
        AttributeDoc(
            name="required",
            description="With a `name`, the calendar is invalid until a day is selected.",
            kind="boolean",
        ),
        AttributeDoc(
            name="disabled",
            description="Days can no longer be selected; like every disabled mj-* host it also ignores pointer input.",
            kind="boolean",
        ),
    ],
    events=[
        ("mj-date-select", "A day was selected by click, Enter or Space (after `mj-event-create`, unless that was cancelled).", "{ date: string }  (local YYYY-MM-DD)"),
        ("mj-event-create", "Cancelable; emitted when a day is activated, before it is selected (not when `readonly`). `preventDefault()` keeps the previous selection and suppresses `mj-date-select`.", "{ date: string }"),
        ("mj-event-click", "An event chip or agenda entry was activated.", "{ eventId: any, event: object }"),
        ("mj-period-change", "The displayed period changed (navigation, view or `value`).", "{ start: string, end: string, view: string }"),
        ("mj-view-change", "The user switched the view with the toolbar.", "{ view: 'month' | 'week' | 'day' | 'agenda' }"),
        ("mj-load-error", "`dataSource.fetchEvents()` rejected.", "{ error: any }"),
    ],
    slots=[
        ("toolbar-start", "Content at the start of the toolbar, before the previous button.", '<button type="button">Calendars</button>'),
        ("toolbar-end", "Content at the end of the toolbar, after the view switcher.", '<button type="button">Today</button>'),
    ],
    properties=[
        ("value", "string. Displayed date as `YYYY-MM-DD`; assigning a Date or string navigates there."),
        ("events", "object[]. `[{ id, title, start, end?, color? }]`."),
        ("dataSource", "{ fetchEvents(start: Date, end: Date): Promise<events> } | null. Called for every displayed period."),
        ("selectedDate", "string | null (read-only). The selected day as `YYYY-MM-DD`."),
        ("displayedPeriod", "{ start: Date, end: Date } (read-only). The first and last day shown."),
        ("form", "HTMLFormElement | null (read-only). The owning form."),
        ("validity", "ValidityState (read-only). `valueMissing` while required and nothing is selected."),
        ("validationMessage", "string (read-only). The current validation message."),
        ("loading", "boolean. Reflects the `loading` attribute."),
    ],
    methods=[
        ("checkValidity() -> boolean", "Returns the validity and fires `invalid` when it fails."),
        ("reportValidity() -> boolean", "Like `checkValidity()` and shows the problem to the user."),
    ],
    parts=[
        ("header", "The toolbar row."),
        ("prev-button", "The previous-period button."),
        ("next-button", "The next-period button."),
        ("view-switcher", "The group of view buttons."),
        ("grid", "The grid / list area of the current view."),
        ("week-row", "Each row of days."),
        ("day-cell", "Each day cell (plus `day-cell-today` and `day-cell-other-month`)."),
        ("day-cell-today", "The cell of today."),
        ("day-cell-other-month", "Cells of days outside the displayed month."),
        ("day-number", "The day number in a cell."),
        ("event-chip", "Each event chip."),
        ("event-overflow", "The `+N more` / Show less button."),
    ],
    css_properties=[
        ("--mj-cal-cell-min-height", "Minimum height of day cells and week rows (default 80px)."),
        ("--mj-cal-period-min-height", "Minimum height of the single row in day view (default 240px)."),
        ("--mj-cal-today-bg", "Background of today's cell (default a 10% accent tint)."),
        ("--mj-cal-other-month-opacity", "Opacity of other-month and disabled days (default 0.4)."),
        ("--mj-cal-event-radius", "Corner radius of event chips (default `--mj-radius-sm`)."),
        ("--mj-cal-event-color", "Colour of events without their own `color`: the chip's start stripe and an 18% tint "
         "behind its text (default var(--mj-accent)). Each event's `color` is written here on its chip."),
    ],
)


# ===========================================================================
# mj-master-detail
# ===========================================================================

_MASTER_DETAIL = ComponentDoc(
    tag="mj-master-detail",
    title="Master Detail",
    group="data",
    summary="Responsive split view: a selectable master list beside a detail panel.",
    description=(
        "<p><code>&lt;mj-master-detail&gt;</code> shows a master list (a "
        "<code>listbox</code> with one tab stop: ArrowUp / ArrowDown / Home / End move, Enter / "
        "Space select) next to a detail panel. The panels follow the inline direction, so the "
        "master is on the right in right-to-left pages. With <code>layout=\"auto\"</code> the "
        "panels sit side by side and stack when the element is narrower than "
        "<code>breakpoint</code> (640px by default), and they return to side by side when it "
        "widens again; in the stacked layout only one panel is visible at a time and the detail "
        "panel has a Back button. The <code>layout</code> attribute is never rewritten: read "
        "<code>resolvedLayout</code> or listen for <code>mj-layout-change</code>.</p>"
        "<p>The detail panel shows exactly one of four states: empty (nothing selected, the "
        "<code>detail-empty</code> slot), loading (the <code>detail-loading</code> slot and a "
        "spinner), error (the <code>detail-error</code> slot) and data (the <code>detail</code> "
        "slot). With <code>resizable</code> the divider is a focusable separator you can drag or "
        "move with the arrow keys (8px steps; Home for the minimum, End for 60%).</p>"
    ),
    how_to_use=(
        "<p>Set <code>items</code> to <code>[{ key, label, meta? }]</code> and put your detail "
        "markup in the <code>detail</code> slot; update it from <code>mj-item-select</code> "
        "(cancelable; the detail carries the item). To load details asynchronously assign "
        "<code>detailDataSource = (key, { signal }) =&gt; Promise</code>: the panel shows its "
        "loading state, a newer selection aborts the signal and ignores the stale result, and "
        "the outcome arrives as <code>mj-detail-load</code> (also stored in "
        "<code>detailData</code>) or <code>mj-detail-error</code>.</p>"
        "<p><code>selected-key</code> selects an item from markup or script (it is updated when "
        "the user selects), <code>master-width</code> sets the master panel width, and "
        "<code>loading-detail</code> forces the loading state while you fetch on your own. Give "
        "the element a height: it fills its container (<code>height: 100%</code>).</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Countries in the master list; selecting one fills the <code>detail</code> "
                "slot from <code>mj-item-select</code>. Before a selection the "
                "<code>detail-empty</code> slot shows. The divider is draggable because "
                "<code>resizable</code> is set.</p>"
            ),
            html=r"""<mj-master-detail id="demo-md" master-label="Countries" detail-label="Country" resizable>
  <p slot="detail-empty" class="hint">Select a country to see its details.</p>
  <div slot="detail" class="detail">
    <h3 id="md-title"></h3>
    <p id="md-text"></p>
  </div>
</mj-master-detail>""",
            css=r"""#demo-md { height: 320px; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
.hint, .detail { padding: var(--mj-space-4); }
.hint { color: var(--mj-text-muted); }
.detail h3 { margin: 0 0 var(--mj-space-2); }""",
            script=r"""const facts = {
  fr: "Capital Paris. Population about 68 million. Currency euro.",
  jp: "Capital Tokyo. Population about 124 million. Currency yen.",
  br: "Capital Brasilia. Population about 216 million. Currency real.",
  ke: "Capital Nairobi. Population about 55 million. Currency shilling.",
  ca: "Capital Ottawa. Population about 40 million. Currency Canadian dollar."
}
const view = document.getElementById("demo-md")
view.items = [
  { key: "fr", label: "France", meta: "Europe" },
  { key: "jp", label: "Japan", meta: "Asia" },
  { key: "br", label: "Brazil", meta: "Americas" },
  { key: "ke", label: "Kenya", meta: "Africa" },
  { key: "ca", label: "Canada", meta: "Americas" }
]
view.addEventListener("mj-item-select", (event) => {
  document.getElementById("md-title").textContent = event.detail.item.label
  document.getElementById("md-text").textContent = facts[event.detail.key] || ("Region: " + (event.detail.item.meta || "unknown"))
})
""",
        ),
        ComponentExample(
            key="detail-data-source",
            title="Async detail: loading and error",
            description=(
                "<p><code>detailDataSource</code> fetches each contact after 700ms; the "
                "<code>detail-loading</code> slot shows meanwhile. <em>Broken record</em> rejects "
                "and shows the <code>detail-error</code> slot. Select quickly in a row: the "
                "<code>signal</code> aborts earlier requests and only the last result is "
                "shown.</p>"
            ),
            html=r"""<mj-master-detail id="contacts-md" master-label="Contacts">
  <p slot="detail-empty" class="pad muted">Pick a contact.</p>
  <span slot="detail-loading">Loading contact...</span>
  <p slot="detail-error" class="pad">This contact could not be loaded.</p>
  <dl slot="detail" id="contact-card" class="pad"></dl>
</mj-master-detail>""",
            css=r"""#contacts-md { height: 300px; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
.pad { padding: var(--mj-space-4); margin: 0; }
.muted { color: var(--mj-text-muted); }
#contact-card dt { font-weight: var(--mj-font-weight-medium); }
#contact-card dd { margin: 0 0 var(--mj-space-2); }""",
            script=r"""const people = {
  1: { name: "Maya Brooks", email: "maya@example.test", phone: "+1 555 0101" },
  2: { name: "Kenji Sato", email: "kenji@example.test", phone: "+81 3 5555 0102" },
  3: { name: "Lena Fischer", email: "lena@example.test", phone: "+49 30 5555 0103" }
}
const view = document.getElementById("contacts-md")
view.items = [
  { key: 1, label: "Maya Brooks", meta: "Sales" },
  { key: 2, label: "Kenji Sato", meta: "Engineering" },
  { key: 3, label: "Lena Fischer", meta: "Support" },
  { key: 4, label: "Broken record", meta: "Fails to load" }
]
view.detailDataSource = (key, { signal }) => new Promise((resolve, reject) => {
  const timer = setTimeout(() => {
    if (people[key] === undefined) {
      reject(new Error("Contact " + key + " not found"))
    } else {
      resolve(people[key])
    }
  }, 700)
  signal.addEventListener("abort", () => {
    clearTimeout(timer)
    mjSandbox.log("aborted request", { key: key })
  })
})
view.addEventListener("mj-detail-load", (event) => {
  const card = document.getElementById("contact-card")
  card.replaceChildren()
  for (const [label, value] of [["Name", event.detail.data.name], ["Email", event.detail.data.email], ["Phone", event.detail.data.phone]]) {
    const dt = document.createElement("dt")
    dt.textContent = label
    const dd = document.createElement("dd")
    dd.textContent = value
    card.append(dt, dd)
  }
})
""",
        ),
        ComponentExample(
            key="stacked",
            title="Stacked layout and breakpoint",
            description=(
                "<p>The first view is pinned to <code>layout=\"stacked\"</code>: selecting a "
                "message opens the detail with a Back button (<code>mj-back</code>). The second "
                "uses <code>layout=\"auto\"</code> with <code>breakpoint=\"520\"</code> in a box "
                "you can resize by its corner; crossing 520px switches the layout and fires "
                "<code>mj-layout-change</code>.</p>"
            ),
            html=r"""<mj-master-detail id="inbox" layout="stacked" master-label="Inbox" back-label="All messages">
  <article slot="detail" class="pad" id="inbox-detail"></article>
</mj-master-detail>
<div class="box">
  <mj-master-detail id="auto" breakpoint="520" master-label="Settings" master-width="180">
    <p slot="detail" class="pad">Settings page content.</p>
  </mj-master-detail>
</div>""",
            css=r"""#inbox { height: 240px; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
.box {
  resize: horizontal; overflow: auto; inline-size: 620px; max-inline-size: 100%; min-inline-size: 260px;
  height: 220px; margin-block-start: var(--mj-space-4); border: 1px dashed var(--mj-border-strong);
}
.pad { padding: var(--mj-space-4); margin: 0; }""",
            script=r"""const inbox = document.getElementById("inbox")
inbox.items = [
  { key: "m1", label: "Quarterly report", meta: "Finance - 09:12" },
  { key: "m2", label: "Welcome aboard", meta: "People team - Mon" },
  { key: "m3", label: "Your invoice", meta: "Billing - Sun" }
]
inbox.addEventListener("mj-item-select", (event) => {
  document.getElementById("inbox-detail").textContent = "Message: " + event.detail.item.label
})
const auto = document.getElementById("auto")
auto.items = [{ key: "profile", label: "Profile" }, { key: "privacy", label: "Privacy" }, { key: "billing", label: "Billing" }]
auto.addEventListener("mj-layout-change", (event) => {
  mjSandbox.log("auto layout", { layout: event.detail.layout, resolvedLayout: auto.resolvedLayout })
})
""",
        ),
        ComponentExample(
            key="custom-styling",
            title="Master width and custom properties",
            description=(
                "<p><code>master-width=\"220\"</code> sets the starting width; the divider is "
                "styled with <code>--mj-md-divider-width</code> / <code>--mj-md-divider-color</code> "
                "and the selection with <code>--mj-md-selected-item-bg</code>. Drag the divider, or "
                "focus it and use the arrow keys, Home and End: <code>mj-panel-resize</code> "
                "reports the new width.</p>"
            ),
            html=r"""<mj-master-detail id="styled" master-width="220" resizable selected-key="tokens" master-label="Topics">
  <div slot="detail" class="pad" id="styled-detail">Design tokens are named design values.</div>
</mj-master-detail>""",
            css=r"""#styled {
  height: 260px;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  --mj-md-divider-width: 6px;
  --mj-md-divider-color: var(--mj-border-strong);
  --mj-md-selected-item-bg: color-mix(in srgb, var(--mj-accent) 22%, var(--mj-surface));
  --mj-md-detail-bg: var(--mj-bg-subtle);
}
.pad { padding: var(--mj-space-4); }""",
            script=r"""const view = document.getElementById("styled")
const text = {
  tokens: "Design tokens are named design values.",
  slots: "Slots let a page place its own content inside a component.",
  parts: "Parts expose shadow elements to page CSS."
}
view.items = [{ key: "tokens", label: "Tokens" }, { key: "slots", label: "Slots" }, { key: "parts", label: "Parts" }]
view.addEventListener("mj-item-select", (event) => {
  document.getElementById("styled-detail").textContent = text[event.detail.key]
})
""",
        ),
        ComponentExample(
            key="events",
            title="Keyboard, selected-key and events",
            description=(
                "<p>The script selects an item through <code>selected-key</code>, then focuses "
                "the list and presses ArrowDown, Enter, End and Space. A cancelable "
                "<code>mj-item-select</code> handler refuses the <em>Locked</em> item.</p>"
            ),
            html=r"""<mj-master-detail id="keys-md" master-label="Projects">
  <p slot="detail" class="pad" id="keys-detail"></p>
</mj-master-detail>""",
            css=r"""#keys-md { height: 260px; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
.pad { padding: var(--mj-space-4); margin: 0; }""",
            script=r"""const view = document.getElementById("keys-md")
view.items = [
  { key: "alpha", label: "Alpha", meta: "Active" },
  { key: "beta", label: "Beta", meta: "Active" },
  { key: "gamma", label: "Gamma", meta: "Paused" },
  { key: "locked", label: "Locked", meta: "Cannot be opened" }
]
view.addEventListener("mj-item-select", (event) => {
  if (event.detail.key === "locked") {
    event.preventDefault()
    mjSandbox.log("selection refused", event.detail)
    return
  }
  document.getElementById("keys-detail").textContent = "Project " + event.detail.item.label
})
const pause = () => new Promise((resolve) => setTimeout(resolve, 450))
view.setAttribute("selected-key", "alpha")
document.getElementById("keys-detail").textContent = "Project Alpha"
const sr = view.shadowRoot
sr.querySelector('.master-item[tabindex="0"]').focus()
const press = (key) => sr.activeElement.dispatchEvent(
  new KeyboardEvent("keydown", { key: key, bubbles: true, composed: true, cancelable: true }))
for (const key of ["ArrowDown", "Enter", "End", " "]) {
  await pause()
  press(key)
  mjSandbox.log("pressed " + (key === " " ? "Space" : key), { focused: sr.activeElement.getAttribute("data-key"), selected: view.getAttribute("selected-key") })
}
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="layout",
            description="`auto` stacks below `breakpoint` and returns side by side above it; the other values pin the layout.",
            kind="enum",
            values=["auto", "side-by-side", "stacked"],
            default="auto",
        ),
        AttributeDoc(
            name="breakpoint",
            description="Element width in px below which `layout=\"auto\"` stacks the panels.",
            kind="number",
            default="640",
        ),
        AttributeDoc(
            name="master-width",
            description="Master panel width: a number of pixels or any CSS length (default `--mj-md-master-width`, 320px).",
            kind="string",
            values=["220", "30%", "18rem"],
        ),
        AttributeDoc(
            name="resizable",
            description="Makes the divider a focusable separator that can be dragged or moved with the arrow keys (`resizable=\"false\"` also turns it off).",
            kind="boolean",
        ),
        AttributeDoc(
            name="selected-key",
            description="Key of the selected item; selecting from markup or script loads its detail, and user selections update it.",
            kind="string",
        ),
        AttributeDoc(
            name="loading-detail",
            description="Forces the detail panel into its loading state (spinner and `detail-loading` slot).",
            kind="boolean",
        ),
        AttributeDoc(
            name="master-label",
            description="Accessible name of the master list.",
            kind="string",
            values=["Countries"],
            default="List",
        ),
        AttributeDoc(
            name="detail-label",
            description="Accessible name of the detail panel (the selected item's label is appended).",
            kind="string",
            values=["Detail"],
            default="Detail",
        ),
        AttributeDoc(
            name="back-label",
            description="Text of the Back button in the stacked layout.",
            kind="string",
            values=["Back", "All messages"],
            default="Back",
        ),
    ],
    events=[
        ("mj-item-select", "Cancelable; the user is selecting a master item (click, Enter or Space).", "{ key: any, item: object }"),
        ("mj-detail-load", "`detailDataSource` resolved for the current selection.", "{ key: any, data: any }"),
        ("mj-detail-error", "`detailDataSource` rejected for the current selection.", "{ key: any, error: any }"),
        ("mj-layout-change", "The layout in effect changed (auto layout crossing the breakpoint, or a new `layout`).", "{ layout: 'side-by-side' | 'stacked' }"),
        ("mj-panel-resize", "The divider was released after a drag, or moved with the keyboard.", "{ masterWidth: number }"),
        ("mj-back", "The Back button was pressed in the stacked layout.", "{}"),
    ],
    slots=[
        ("detail", "Detail content, shown once an item is selected (and its detail loaded).", "<div style=\"padding: 16px\">Detail content</div>"),
        ("detail-empty", "Shown while nothing is selected.", "<p style=\"padding: 16px\">Select an item.</p>"),
        ("detail-loading", "Text next to the spinner while the detail loads.", "<span>Loading...</span>"),
        ("detail-error", "Shown when `detailDataSource` rejected.", "<p style=\"padding: 16px\">Could not load this item.</p>"),
        ("master", "Extra content below the master list (for example a footer link).", "<p style=\"padding: 8px\">5 countries</p>"),
    ],
    properties=[
        ("items", "object[]. Master items `[{ key, label, meta? }]`."),
        ("detailDataSource", "(key, { signal }) => Promise<any> | null. Loads the detail of a selection; the signal aborts when a newer selection starts."),
        ("detailData", "any (read-only). What the last successful `detailDataSource` call resolved."),
        ("resolvedLayout", "'side-by-side' | 'stacked' (read-only). The layout in effect."),
        ("columns", "object[]. Stored for a future table master (`master-type=\"table\"`); not used yet."),
        ("dataSource", "any. Stored for a future table master; not used yet."),
    ],
    parts=[
        ("root", "The container of both panels (`data-layout` shows the layout in effect)."),
        ("master-panel", "The master panel."),
        ("master-item", "Each master list option."),
        ("divider", "The separator between the panels."),
        ("detail-panel", "The detail panel."),
        ("back-button", "The Back button (stacked layout)."),
        ("detail-empty", "Container of the `detail-empty` slot."),
        ("detail-loading", "Container of the spinner and the `detail-loading` slot."),
        ("detail-error", "Container of the `detail-error` slot."),
    ],
    css_properties=[
        ("--mj-md-master-width", "Master panel width (default 320px; `master-width` overrides it)."),
        ("--mj-md-master-min-width", "Minimum master width (default 200px)."),
        ("--mj-md-master-max-width", "Maximum master width (default 60%)."),
        ("--mj-md-divider-width", "Divider thickness (default 4px)."),
        ("--mj-md-divider-color", "Divider colour (default `--mj-border`)."),
        ("--mj-md-detail-bg", "Detail panel background (default `--mj-surface`)."),
        ("--mj-md-selected-item-bg", "Selected master item background (default a 10% accent tint)."),
    ],
)


# ===========================================================================
# mj-column-picker
# ===========================================================================

_COLUMN_PICKER = ComponentDoc(
    tag="mj-column-picker",
    title="Column Picker",
    group="data",
    summary="Trigger button and popover for showing, hiding and reordering the columns of a table.",
    description=(
        "<p><code>&lt;mj-column-picker&gt;</code> is a trigger button that opens a non-modal "
        "popover (positioned by the overlay engine, so it flips and shifts to stay in the "
        "viewport) with one checkbox per column. It does not change a table itself: it keeps "
        "its own copy of the column list and reports changes, and the host applies them to "
        "<code>&lt;mj-data-table&gt;</code>, <code>&lt;mj-table&gt;</code> or a tree grid (every "
        "example here does). Locked columns keep their visibility and position, and "
        "<code>min-visible</code> stops the last columns from being hidden.</p>"
        "<p>Columns can be reordered by dragging a handle with the pointer, or with the keyboard: "
        "focus a handle, press Space to grab, ArrowUp / ArrowDown to move, Enter or Space to "
        "drop and Escape to put the column back. With <code>apply-mode=\"immediate\"</code> "
        "(default) every change is reported as it happens; with <code>deferred</code> changes "
        "collect in a pending copy that Apply commits and closing discards. Reset restores "
        "<code>defaultColumns</code>, or the first <code>columns</code> assignment when "
        "defaults were never set. Escape or a click outside closes the panel.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>columns</code> (<code>[{ key, label, visible?, locked? }]</code>; "
        "<code>visible</code> defaults to true) using the same keys as your table, and apply "
        "the reported list to the table: in immediate mode on "
        "<code>mj-column-visibility-change</code>, <code>mj-column-reorder</code> and "
        "<code>mj-columns-reset</code>; in deferred mode on <code>mj-columns-apply</code> and "
        "<code>mj-columns-reset</code>. Each detail carries the full <code>columns</code> list "
        "in display order; show the entries whose <code>visible</code> is not false. The picker "
        "clones what you assign, so read <code>picker.columns</code> for its current state.</p>"
        "<p>Put the picker in a table toolbar (the <code>toolbar</code> slot of "
        "<code>&lt;mj-data-table&gt;</code> works well). The <code>panel-header</code> slot "
        "replaces the panel title and <code>panel-footer</code> adds controls between Reset and "
        "Apply. <code>reorderable=\"false\"</code> hides the drag handles.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage (wired to a data table)",
            description=(
                "<p>The picker sits in the data table's <code>toolbar</code> slot. Each "
                "<code>mj-column-visibility-change</code>, <code>mj-column-reorder</code> and "
                "<code>mj-columns-reset</code> rebuilds the table's <code>columns</code>, so "
                "hiding Email or dragging Role up changes the table at once. Name is locked; "
                "Department starts hidden.</p>"
            ),
            html=r"""<mj-data-table id="cp-table" sortable label="Employees">
  <div slot="toolbar" class="toolbar">
    <strong>Employees</strong>
    <mj-column-picker id="demo-cp" label="Columns"></mj-column-picker>
  </div>
</mj-data-table>""",
            css=r""".toolbar { display: flex; align-items: center; justify-content: space-between; }""",
            script=r"""const table = document.getElementById("cp-table")
const picker = document.getElementById("demo-cp")
const definitions = {
  name: { key: "name", label: "Name", width: 160 },
  email: { key: "email", label: "Email", width: 220 },
  role: { key: "role", label: "Role", width: 130 },
  dept: { key: "dept", label: "Department", width: 140 },
  city: { key: "city", label: "City", width: 120 }
}
function applyColumns(columns) {
  table.columns = columns
    .filter((col) => col.visible !== false && definitions[col.key] !== undefined)
    .map((col) => definitions[col.key])
}
picker.columns = [
  { key: "name", label: "Name", locked: true },
  { key: "email", label: "Email" },
  { key: "role", label: "Role" },
  { key: "dept", label: "Department", visible: false },
  { key: "city", label: "City" }
]
for (const name of ["mj-column-visibility-change", "mj-column-reorder", "mj-columns-reset", "mj-columns-apply"]) {
  picker.addEventListener(name, (event) => applyColumns(event.detail.columns))
}
applyColumns(picker.columns)
table.rows = [
  { name: "Alice Martin", email: "alice@example.test", role: "Engineer", dept: "Platform", city: "Lisbon" },
  { name: "Bob Chen", email: "bob@example.test", role: "Designer", dept: "Product", city: "Toronto" },
  { name: "Chiara Rossi", email: "chiara@example.test", role: "Manager", dept: "Platform", city: "Milan" },
  { name: "Dev Patel", email: "dev@example.test", role: "QA", dept: "Quality", city: "Pune" }
]
""",
            height=420,
        ),
        ComponentExample(
            key="deferred",
            title="Deferred apply",
            description=(
                "<p>With <code>apply-mode=\"deferred\"</code> toggles and moves stay in a pending "
                "copy: the table changes only when you press Apply (<code>mj-columns-apply</code>). "
                "Close the panel with Escape or a click outside to discard the changes.</p>"
            ),
            html=r"""<div class="bar"><mj-column-picker id="deferred-cp" apply-mode="deferred" label="Edit columns"></mj-column-picker></div>
<mj-table id="deferred-table" caption="Monthly invoices" variant="striped"></mj-table>""",
            css=r""".bar { display: flex; justify-content: flex-end; margin-block-end: var(--mj-space-2); }""",
            script=r"""const picker = document.getElementById("deferred-cp")
const table = document.getElementById("deferred-table")
const labels = { number: "Invoice", client: "Client", issued: "Issued", due: "Due", amount: "Amount", status: "Status" }
picker.columns = Object.keys(labels).map((key) => ({ key: key, label: labels[key], visible: key !== "issued" }))
function applyColumns(columns) {
  table.columns = columns.filter((col) => col.visible !== false).map((col) => ({ key: col.key, label: col.label }))
}
picker.addEventListener("mj-columns-apply", (event) => applyColumns(event.detail.columns))
picker.addEventListener("mj-columns-reset", (event) => applyColumns(event.detail.columns))
applyColumns(picker.columns)
table.rows = [
  { number: "INV-2041", client: "Northwind", issued: "2026-10-01", due: "2026-10-31", amount: "$4,200", status: "Paid" },
  { number: "INV-2042", client: "Contoso", issued: "2026-10-03", due: "2026-11-02", amount: "$980", status: "Open" },
  { number: "INV-2043", client: "Fabrikam", issued: "2026-10-09", due: "2026-11-08", amount: "$12,450", status: "Overdue" }
]
""",
            height=420,
        ),
        ComponentExample(
            key="constraints",
            title="Locked columns and min-visible",
            description=(
                "<p>Order and Total are <code>locked</code>, <code>min-visible=\"3\"</code> refuses "
                "to hide a third-to-last column (the live region says why), and "
                "<code>reorderable=\"false\"</code> removes the drag handles. The table follows "
                "every accepted change.</p>"
            ),
            html=r"""<div class="bar"><mj-column-picker id="strict-cp" min-visible="3" reorderable="false" open></mj-column-picker></div>
<mj-table id="strict-table" caption="Orders"></mj-table>""",
            css=r""".bar { margin-block-end: var(--mj-space-2); }""",
            script=r"""const picker = document.getElementById("strict-cp")
const table = document.getElementById("strict-table")
picker.columns = [
  { key: "order", label: "Order", locked: true },
  { key: "customer", label: "Customer" },
  { key: "items", label: "Items" },
  { key: "total", label: "Total", locked: true }
]
function applyColumns(columns) {
  table.columns = columns.filter((col) => col.visible !== false).map((col) => ({ key: col.key, label: col.label }))
}
picker.addEventListener("mj-column-visibility-change", (event) => applyColumns(event.detail.columns))
picker.addEventListener("mj-columns-reset", (event) => applyColumns(event.detail.columns))
applyColumns(picker.columns)
table.rows = [
  { order: "SO-77", customer: "Ana Lima", items: 3, total: "$59.00" },
  { order: "SO-78", customer: "Jon Berg", items: 1, total: "$12.50" }
]
""",
            height=420,
        ),
        ComponentExample(
            key="slots",
            title="Panel header and footer slots",
            description=(
                "<p>The <code>panel-header</code> slot replaces the title with a heading and a "
                "hint; the <code>panel-footer</code> slot adds a Show all button that makes every "
                "column visible by assigning <code>columns</code> and updates the table.</p>"
            ),
            html=r"""<div class="bar">
  <mj-column-picker id="slotted-cp" open>
    <div slot="panel-header" class="head"><strong>Visible columns</strong><br><small>Drag to reorder</small></div>
    <button type="button" slot="panel-footer" id="show-all">Show all</button>
  </mj-column-picker>
</div>
<mj-table id="slotted-table" caption="Servers" variant="compact"></mj-table>""",
            css=r""".bar { margin-block-end: var(--mj-space-2); }
.head small { color: var(--mj-text-muted); }""",
            script=r"""const picker = document.getElementById("slotted-cp")
const table = document.getElementById("slotted-table")
picker.columns = [
  { key: "host", label: "Host", locked: true },
  { key: "ip", label: "IP address", visible: false },
  { key: "os", label: "OS", visible: false },
  { key: "cpu", label: "CPU" },
  { key: "memory", label: "Memory" }
]
function applyColumns(columns) {
  table.columns = columns.filter((col) => col.visible !== false).map((col) => ({ key: col.key, label: col.label }))
}
for (const name of ["mj-column-visibility-change", "mj-column-reorder", "mj-columns-reset"]) {
  picker.addEventListener(name, (event) => applyColumns(event.detail.columns))
}
document.getElementById("show-all").addEventListener("click", () => {
  picker.columns = picker.columns.map((col) => Object.assign({}, col, { visible: true }))
  applyColumns(picker.columns)
  mjSandbox.log("show all", picker.columns.map((col) => col.key))
})
applyColumns(picker.columns)
table.rows = [
  { host: "web-01", ip: "10.0.0.11", os: "Debian 12", cpu: "34%", memory: "4.2 GB" },
  { host: "db-01", ip: "10.0.0.21", os: "Ubuntu 24.04", cpu: "71%", memory: "28 GB" }
]
""",
            height=420,
        ),
        ComponentExample(
            key="events",
            title="Keyboard reorder and events",
            description=(
                "<p>The script opens the panel, hides Phone, moves Email to the top with the "
                "keyboard (grab its handle, ArrowUp twice, drop; the script clicks the handle, "
                "which is what Space and Enter do on that button), resets, and closes with "
                "Escape. "
                "The table follows each step; the Events panel shows the sequence.</p>"
            ),
            html=r"""<div class="bar"><mj-column-picker id="events-cp"></mj-column-picker></div>
<mj-table id="events-table" caption="Contacts"></mj-table>""",
            css=r""".bar { margin-block-end: var(--mj-space-2); }""",
            script=r"""const picker = document.getElementById("events-cp")
const table = document.getElementById("events-table")
picker.columns = [
  { key: "name", label: "Name" },
  { key: "phone", label: "Phone" },
  { key: "email", label: "Email" }
]
function applyColumns(columns) {
  table.columns = columns.filter((col) => col.visible !== false).map((col) => ({ key: col.key, label: col.label }))
}
for (const name of ["mj-column-visibility-change", "mj-column-reorder", "mj-columns-reset"]) {
  picker.addEventListener(name, (event) => applyColumns(event.detail.columns))
}
applyColumns(picker.columns)
table.rows = [{ name: "Ivo", phone: "+386 1 555 0100", email: "ivo@example.test" }]

const sr = picker.shadowRoot
const pause = () => new Promise((resolve) => setTimeout(resolve, 600))
const key = (target, name) => target.dispatchEvent(new KeyboardEvent("keydown", { key: name, bubbles: true, composed: true, cancelable: true }))
await pause()
picker.open = true
await pause()
sr.querySelector('.column-item[data-col-key="phone"] .col-checkbox').click()
await pause()
const handle = sr.querySelector('.column-item[data-col-key="email"] .drag-handle')
handle.focus()
handle.click()
key(sr.activeElement, "ArrowUp")
key(sr.activeElement, "ArrowUp")
handle.click()
await pause()
sr.querySelector('[part="reset-button"]').click()
await pause()
key(document, "Escape")
""",
            height=420,
        ),
    ],
    attributes=[
        AttributeDoc(
            name="label",
            description="Trigger text, its accessible name and the panel title.",
            kind="string",
            values=["Columns", "Edit columns"],
            default="Columns",
        ),
        AttributeDoc(
            name="apply-mode",
            description="`immediate` reports each change; `deferred` collects them until Apply (closing discards them).",
            kind="enum",
            values=["immediate", "deferred"],
            default="immediate",
        ),
        AttributeDoc(
            name="reorderable",
            description="Drag handles for reordering; `reorderable=\"false\"` removes them.",
            kind="boolean",
            default="true",
        ),
        AttributeDoc(
            name="min-visible",
            description="Fewest columns that must stay visible; hiding one more is refused with a live-region message.",
            kind="number",
            default="1",
        ),
        AttributeDoc(
            name="open",
            description="Opens the panel (also when present at first render); removed when the panel closes.",
            kind="boolean",
        ),
        AttributeDoc(
            name="disabled",
            description="Disables the trigger and closes an open panel.",
            kind="boolean",
        ),
    ],
    events=[
        ("mj-picker-open", "The panel opened.", "{}"),
        ("mj-picker-close", "The panel closed.", "{}"),
        ("mj-column-visibility-change", "Immediate mode: a column was shown or hidden.", "{ key: string, visible: boolean, columns: object[] }"),
        ("mj-column-reorder", "Immediate mode: a grabbed or dragged column was dropped at a new index.", "{ key: string, from: number, to: number, columns: object[] }"),
        ("mj-columns-apply", "Apply was pressed (deferred mode); the pending copy is now `columns`.", "{ columns: object[] }"),
        ("mj-columns-reset", "Reset restored the default columns.", "{ columns: object[] }"),
    ],
    slots=[
        ("panel-header", "Replaces the panel title (the `label` text).", "<strong>Choose columns</strong>"),
        ("panel-footer", "Extra controls in the footer, between Reset and Apply.", '<button type="button">Show all</button>'),
    ],
    properties=[
        ("columns", "object[]. `[{ key, label, visible?, locked? }]` in display order; assigning clones the list (the first assignment is the Reset default unless `defaultColumns` is set)."),
        ("defaultColumns", "object[]. What Reset restores."),
        ("open", "boolean. Reflects the `open` attribute."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    parts=[
        ("trigger-button", "The button that opens the panel."),
        ("panel", "The popover panel (`role=dialog`)."),
        ("panel-header", "Container of the title / `panel-header` slot."),
        ("column-list", "The list of columns."),
        ("column-item", "Each column row."),
        ("column-drag-handle", "The drag / keyboard-grab handle of a row."),
        ("column-checkbox", "The visibility checkbox of a row."),
        ("column-label", "The label of a row."),
        ("panel-footer", "The footer with Reset, the `panel-footer` slot and Apply."),
        ("reset-button", "The Reset button."),
        ("apply-button", "The Apply button (deferred mode only)."),
    ],
    css_properties=[
        ("--mj-cp-panel-width", "Panel width (default 240px)."),
        ("--mj-cp-panel-max-height", "Panel maximum height before it scrolls (default 360px)."),
        ("--mj-cp-item-height", "Height of each column row (default 36px)."),
        ("--mj-cp-drag-handle-color", "Handle colour (default `--mj-text-muted`)."),
        ("--mj-cp-checked-color", "Checkbox accent colour (default `--mj-accent`)."),
    ],
)


# ===========================================================================
# mj-bulk-action-bar
# ===========================================================================

_BULK_ACTION_BAR = ComponentDoc(
    tag="mj-bulk-action-bar",
    title="Bulk Action Bar",
    group="data",
    summary="Contextual toolbar for a selection: tri-state select-all, count, actions and clear.",
    description=(
        "<p><code>&lt;mj-bulk-action-bar&gt;</code> is the toolbar that appears while rows are "
        "selected in a table, tree grid or list. It shows a tri-state select-all checkbox "
        "(checked when <code>selected-count</code> reaches <code>total-count</code>, mixed when "
        "some rows are selected), a live count label, the action buttons built from "
        "<code>actions</code> (plus any slotted controls), and a clear (&times;) button. The "
        "action buttons are one roving tab stop moved with the arrow keys; Escape inside the bar "
        "clears the selection. The count is announced once per change while the bar is "
        "shown.</p>"
        "<p>The bar does not track a selection itself: the host keeps <code>selected-count</code>, "
        "<code>total-count</code> and <code>selectedKeys</code> in sync and reacts to its events. "
        "It sets <code>visible</code> itself when the count rises above zero and removes it when "
        "the count drops back to zero; the host may also set or remove <code>visible</code> at "
        "any time. Actions that do not fit wrap onto further lines (there is no overflow menu). "
        "<code>position=\"floating\"</code> makes the bar sticky at the bottom of the nearest "
        "scrolling container.</p>"
    ),
    how_to_use=(
        "<p>Set <code>actions</code> to <code>[{ key, label, icon?, destructive?, disabled? }]</code> "
        "(<code>icon</code> is text such as an emoji, hidden from assistive technology). On every "
        "selection change update <code>selectedCount</code>, <code>totalCount</code> and "
        "<code>selectedKeys</code>; <code>mj-action</code> then reports the action key with the "
        "selected keys. Handle <code>mj-select-all</code> (its <code>selectAll</code> flag says "
        "whether to select or clear everything) and <code>mj-clear-selection</code>, and update "
        "the counts afterwards; the checkbox re-syncs to the counts, so ignoring the event is "
        "safe.</p>"
        "<p><code>count-label</code> is a template with <code>{n}</code> for the number. Set "
        "<code>returnFocusTo</code> to the grid so focus goes back there when the bar hides "
        "while focused. Extra controls (a <code>&lt;select&gt;</code>, a menu button) go in the "
        "<code>actions</code> slot.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage (wired to a data table)",
            description=(
                "<p>A multi-row <code>&lt;mj-data-table&gt;</code> drives the bar: every "
                "<code>mj-selection-change</code> updates <code>selectedCount</code> and "
                "<code>selectedKeys</code>. The select-all checkbox calls <code>selectAll()</code> / "
                "<code>clearSelection()</code>, &times; and Escape clear, and Delete removes the "
                "selected rows. Three rows start selected; click rows to change the "
                "selection.</p>"
            ),
            html=r"""<mj-bulk-action-bar id="demo-bab" total-count="8"></mj-bulk-action-bar>
<mj-data-table id="bab-table" row-key="id" selection="multi-row" sortable label="Files"></mj-data-table>
<p id="bab-output" role="status"></p>""",
            css=r"""#demo-bab { margin-block-end: var(--mj-space-2); min-block-size: 48px; }
#bab-output { color: var(--mj-text-muted); margin: var(--mj-space-2) 0; }""",
            script=r"""const bar = document.getElementById("demo-bab")
const table = document.getElementById("bab-table")
const output = document.getElementById("bab-output")
table.columns = [
  { key: "name", label: "Name", width: 220 },
  { key: "type", label: "Type", width: 110 },
  { key: "size", label: "Size", width: 100 }
]
table.rows = [
  { id: "f1", name: "budget-2026.xlsx", type: "Spreadsheet", size: "84 KB" },
  { id: "f2", name: "roadmap.pdf", type: "PDF", size: "1.2 MB" },
  { id: "f3", name: "logo.svg", type: "Image", size: "6 KB" },
  { id: "f4", name: "notes.md", type: "Text", size: "3 KB" },
  { id: "f5", name: "demo.mp4", type: "Video", size: "48 MB" },
  { id: "f6", name: "contract.docx", type: "Document", size: "220 KB" },
  { id: "f7", name: "data.csv", type: "Spreadsheet", size: "910 KB" },
  { id: "f8", name: "photo.jpg", type: "Image", size: "2.4 MB" }
]
bar.actions = [
  { key: "download", label: "Download", icon: "⬇" },
  { key: "share", label: "Share", icon: "↗" },
  { key: "delete", label: "Delete", icon: "\u{1F5D1}", destructive: true }
]
bar.returnFocusTo = table

function sync() {
  bar.selectedKeys = table.selectedRows
  bar.totalCount = table.rows.length
  bar.selectedCount = table.selectedRows.size
}
table.addEventListener("mj-selection-change", sync)
bar.addEventListener("mj-select-all", (event) => {
  if (event.detail.selectAll === true) {
    table.selectAll()
  } else {
    table.clearSelection()
  }
  sync()
})
bar.addEventListener("mj-clear-selection", () => {
  table.clearSelection()
  sync()
})
bar.addEventListener("mj-action", (event) => {
  const keys = event.detail.selectedKeys
  output.textContent = event.detail.actionKey + ": " + keys.join(", ")
  if (event.detail.actionKey === "delete") {
    table.rows = table.rows.filter((row) => keys.indexOf(row.id) < 0)
    table.clearSelection()
    sync()
  }
})
for (const key of ["f1", "f3", "f4"]) {
  table.selectRow(key)
}
sync()
""",
        ),
        ComponentExample(
            key="floating",
            title="Floating bar with row selectors",
            description=(
                "<p>A 40-row <code>&lt;mj-table&gt;</code> renders an "
                "<code>&lt;mj-row-selector&gt;</code> in its first column and the header "
                "select-all is the bar's checkbox. With <code>position=\"floating\"</code> the bar "
                "sticks to the bottom of the scrolling box while you scroll.</p>"
            ),
            html=r"""<div class="scroller">
  <mj-table id="float-table" caption="Inbox"></mj-table>
  <mj-bulk-action-bar id="float-bar" position="floating" total-count="40"></mj-bulk-action-bar>
</div>""",
            css=r""".scroller { block-size: 320px; overflow: auto; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); padding: var(--mj-space-2); }""",
            script=r"""const table = document.getElementById("float-table")
const bar = document.getElementById("float-bar")
const selected = new Set()
const rows = Array.from({ length: 40 }, (_, i) => ({ id: "msg-" + (i + 1), subject: "Message " + (i + 1), from: ["Ana", "Ben", "Cai", "Dee"][i % 4] }))
table.columns = [
  {
    key: "pick", label: "Select", labelHidden: true, rowHeader: false, width: "3rem",
    render: (row) => {
      const selector = document.createElement("mj-row-selector")
      selector.value = row.id
      selector.setAttribute("label", "Select " + row.subject)
      selector.selected = selected.has(row.id)
      return selector
    }
  },
  { key: "subject", label: "Subject", rowHeader: true },
  { key: "from", label: "From" }
]
table.rows = rows
bar.actions = [{ key: "archive", label: "Archive" }, { key: "read", label: "Mark as read" }]
function sync() {
  bar.selectedKeys = selected
  bar.selectedCount = selected.size
}
table.addEventListener("mj-row-select-change", (event) => {
  if (event.detail.selected === true) {
    selected.add(event.detail.value)
  } else {
    selected.delete(event.detail.value)
  }
  sync()
})
function setAll(on) {
  selected.clear()
  if (on === true) {
    rows.forEach((row) => selected.add(row.id))
  }
  table.rows = rows
  sync()
}
bar.addEventListener("mj-select-all", (event) => setAll(event.detail.selectAll))
bar.addEventListener("mj-clear-selection", () => setAll(false))
selected.add("msg-2")
selected.add("msg-5")
table.rows = rows
sync()
""",
        ),
        ComponentExample(
            key="custom-actions",
            title="Labels, disabled actions and the actions slot",
            description=(
                "<p><code>count-label=\"{n} of 40 files\"</code> replaces the count text and "
                "<code>select-all-label</code> / <code>clear-label</code> rename the controls. "
                "Rename is disabled (<code>disabled: true</code>) because more than one file is "
                "selected, and the <code>actions</code> slot adds a Move to... select after the "
                "built-in buttons.</p>"
            ),
            html=r"""<mj-bulk-action-bar id="custom-bab" selected-count="4" total-count="40"
                    count-label="{n} of 40 files" select-all-label="Select every file" clear-label="Deselect files">
  <label slot="actions" class="move">Move to
    <select id="move-target">
      <option>Archive</option>
      <option>Shared</option>
      <option>Trash</option>
    </select>
  </label>
</mj-bulk-action-bar>""",
            css=r""".move { display: inline-flex; gap: var(--mj-space-1); align-items: center; font-size: var(--mj-font-size-sm); }""",
            script=r"""const bar = document.getElementById("custom-bab")
bar.selectedKeys = ["a.txt", "b.txt", "c.txt", "d.txt"]
bar.actions = [
  { key: "rename", label: "Rename", disabled: true },
  { key: "copy", label: "Copy link" },
  { key: "delete", label: "Delete", destructive: true }
]
document.getElementById("move-target").addEventListener("change", (event) => {
  mjSandbox.log("move", { to: event.target.value, keys: Array.from(bar.selectedKeys) })
})
""",
        ),
        ComponentExample(
            key="states",
            title="States",
            description=(
                "<p>All selected (the checkbox is checked because <code>selected-count</code> "
                "equals <code>total-count</code>), part selected (mixed), and "
                "<code>disabled</code> (every control is disabled and the slotted actions are "
                "inert).</p>"
            ),
            html=r"""<div class="stack">
  <mj-bulk-action-bar id="all-bab" selected-count="12" total-count="12"></mj-bulk-action-bar>
  <mj-bulk-action-bar id="some-bab" selected-count="5" total-count="12"></mj-bulk-action-bar>
  <mj-bulk-action-bar id="disabled-bab" selected-count="5" total-count="12" disabled>
    <button type="button" slot="actions">Slotted action</button>
  </mj-bulk-action-bar>
</div>""",
            css=r""".stack { display: grid; gap: var(--mj-space-3); }""",
            script=r"""for (const id of ["all-bab", "some-bab", "disabled-bab"]) {
  document.getElementById(id).actions = [{ key: "export", label: "Export" }, { key: "delete", label: "Delete", destructive: true }]
}
""",
        ),
        ComponentExample(
            key="events",
            title="Events and keyboard",
            description=(
                "<p>The script clicks Export (<code>mj-action</code> with the selected keys), "
                "toggles the select-all checkbox (<code>mj-select-all</code>; the handler applies "
                "it), and presses Escape inside the bar (<code>mj-clear-selection</code>), which "
                "hides the bar. Set <code>selected-count</code> above zero to show it again.</p>"
            ),
            html=r"""<mj-bulk-action-bar id="events-bab" selected-count="2" total-count="6"></mj-bulk-action-bar>""",
            script=r"""const bar = document.getElementById("events-bab")
const all = ["r1", "r2", "r3", "r4", "r5", "r6"]
bar.selectedKeys = ["r2", "r5"]
bar.actions = [{ key: "export", label: "Export" }, { key: "tag", label: "Tag" }]
bar.addEventListener("mj-select-all", (event) => {
  bar.selectedKeys = event.detail.selectAll === true ? all : []
  bar.selectedCount = event.detail.selectAll === true ? all.length : 0
})
bar.addEventListener("mj-clear-selection", () => {
  bar.selectedKeys = []
  bar.selectedCount = 0
})
const sr = bar.shadowRoot
const pause = () => new Promise((resolve) => setTimeout(resolve, 600))
await pause()
sr.querySelector('.action-btn[data-action-key="export"]').click()
await pause()
sr.querySelector(".select-all-cb").click()
mjSandbox.log("after select all", { selectedCount: bar.selectedCount })
await pause()
sr.querySelector(".action-btn").focus()
sr.activeElement.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, composed: true }))
mjSandbox.log("after Escape", { visible: bar.visible, selectedCount: bar.selectedCount })
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="selected-count",
            description="Number of selected rows; drives the count label and the checkbox, and shows / hides the bar when it crosses zero.",
            kind="number",
            default="0",
        ),
        AttributeDoc(
            name="total-count",
            description="Number of selectable rows; the checkbox is checked when `selected-count` reaches it.",
            kind="number",
            default="0",
        ),
        AttributeDoc(
            name="visible",
            description="Shows the bar. Set automatically when the count rises above zero and removed when it drops to zero.",
            kind="boolean",
        ),
        AttributeDoc(
            name="disabled",
            description="Disables the checkbox, the clear button and every action; slotted actions become inert.",
            kind="boolean",
        ),
        AttributeDoc(
            name="position",
            description="`floating` makes the bar sticky at the bottom of its scrolling container, with a shadow.",
            kind="enum",
            values=["inline", "floating"],
            default="inline",
        ),
        AttributeDoc(
            name="count-label",
            description="Template of the count text; `{n}` is replaced by the formatted count.",
            kind="string",
            values=["{n} selected", "{n} of 40 files"],
            default="{n} selected",
        ),
        AttributeDoc(
            name="select-all-label",
            description="Accessible name of the select-all checkbox.",
            kind="string",
            default="Select all",
        ),
        AttributeDoc(
            name="clear-label",
            description="Accessible name and tooltip of the clear button.",
            kind="string",
            default="Clear selection",
        ),
    ],
    events=[
        ("mj-action", "An action button was activated.", "{ actionKey: string, selectedKeys: any[] }"),
        ("mj-select-all", "Cancelable; the select-all checkbox was toggled (true: select everything, false: clear).", "{ selectAll: boolean }"),
        ("mj-clear-selection", "The clear button was pressed or Escape was pressed inside the bar; the bar hides.", "{}"),
    ],
    slots=[
        ("actions", "Extra controls after the built-in action buttons.", '<button type="button">More...</button>'),
    ],
    properties=[
        ("actions", "object[]. `[{ key, label, icon?, destructive?, disabled? }]` rendered as buttons."),
        ("selectedKeys", "Set<any>. The selected keys reported by `mj-action`; an array is converted to a Set."),
        ("selectedCount", "number. Reflects `selected-count`."),
        ("totalCount", "number. Reflects `total-count`."),
        ("visible", "boolean. Reflects `visible`."),
        ("disabled", "boolean. Reflects `disabled`."),
        ("returnFocusTo", "Element | null. Receives focus when the bar hides while focus is inside it."),
    ],
    parts=[
        ("bar", "The toolbar (`role=toolbar`)."),
        ("select-all-checkbox", "The tri-state checkbox."),
        ("count-label", "The count text."),
        ("action-group", "The group of action buttons and the `actions` slot."),
        ("action-button", "Each built-in action button."),
        ("clear-button", "The clear (x) button."),
    ],
    css_properties=[
        ("--mj-bab-height", "Minimum bar height (default 48px)."),
        ("--mj-bab-bg", "Bar background (default an 8% accent tint of `--mj-surface`)."),
        ("--mj-bab-action-gap", "Space between items (default 8px)."),
        ("--mj-bab-count-color", "Count text colour (default `--mj-accent`)."),
        ("--mj-bab-z-index", "Stacking level of the floating bar (default `--mj-layer-sticky`)."),
        ("--mj-bab-shadow", "Shadow of the floating bar (default `--mj-elevation-2`)."),
        ("--mj-bab-border-radius", "Corner radius of the floating bar (default `--mj-radius-md`)."),
    ],
)


# ===========================================================================
# mj-sort-control
# ===========================================================================

_SORT_CONTROL = ComponentDoc(
    tag="mj-sort-control",
    title="Sort Control",
    group="data",
    summary="Sort button and direction indicator that cycles none, ascending and descending.",
    description=(
        "<p><code>&lt;mj-sort-control&gt;</code> is a standalone sort button for one field: put "
        "it in a column header, a toolbar or anywhere else. Activating it (click, Enter or Space "
        "on its native button) steps the direction through its <code>cycle</code> (by default "
        "none, ascending, descending, none), updates the indicator and "
        "<code>aria-pressed</code>, and emits <code>mj-sort-change</code> so the host re-sorts "
        "its data. The control never sorts anything itself.</p>"
        "<p>Controls that share a <code>group</code> in the same document or shadow root sort one "
        "dataset: activating one resets the others to none (silently), so the host does not need "
        "single-sort bookkeeping. The accessible name says the field, the current direction and "
        "what the next activation does; <code>label-none</code>, <code>label-asc</code> and "
        "<code>label-desc</code> replace those texts (with <code>{label}</code> for the field "
        "label) for other languages.</p>"
    ),
    how_to_use=(
        "<p>Set <code>field</code> to the key the host sorts on and put the visible label "
        "between the tags. Listen for <code>mj-sort-change</code> (it bubbles and crosses shadow "
        "boundaries, so one listener on the table works) and sort by <code>field</code> and "
        "<code>direction</code>. Use <code>group</code> for single-column sorting, "
        "<code>cycle</code> to change the steps (for example <code>asc-desc</code> to skip the "
        "unsorted state, or <code>desc-asc-none</code> to start descending), and "
        "<code>reset()</code> or the <code>direction</code> property to set the state without an "
        "event.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage (sorting a table)",
            description=(
                "<p>Sort controls in the header cells of a plain <code>&lt;table&gt;</code>, all in "
                "<code>group=\"people\"</code>: one <code>mj-sort-change</code> listener on the "
                "table re-sorts the rows, and activating one control resets the others. Updated "
                "starts sorted descending.</p>"
            ),
            html=r"""<table id="people-table">
  <thead>
    <tr>
      <th><mj-sort-control field="name" group="people">Name</mj-sort-control></th>
      <th><mj-sort-control field="team" group="people">Team</mj-sort-control></th>
      <th><mj-sort-control field="updated" group="people" direction="desc">Updated</mj-sort-control></th>
    </tr>
  </thead>
  <tbody></tbody>
</table>""",
            css=r"""#people-table { border-collapse: collapse; inline-size: 100%; font-size: var(--mj-font-size-sm); }
#people-table th, #people-table td { text-align: start; padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }
#people-table th { background: var(--mj-bg-subtle); }""",
            script=r"""const people = [
  { name: "Noor", team: "Design", updated: "2026-11-02" },
  { name: "Arjun", team: "Platform", updated: "2026-10-28" },
  { name: "Lucia", team: "Design", updated: "2026-11-07" },
  { name: "Tomas", team: "Support", updated: "2026-09-30" },
  { name: "Beatriz", team: "Platform", updated: "2026-11-05" }
]
const table = document.getElementById("people-table")
function render(field, direction) {
  let rows = people.slice()
  if (direction !== "none") {
    rows.sort((a, b) => String(a[field]).localeCompare(String(b[field])))
    if (direction === "desc") {
      rows.reverse()
    }
  }
  table.tBodies[0].replaceChildren(...rows.map((person) => {
    const tr = document.createElement("tr")
    for (const key of ["name", "team", "updated"]) {
      const td = document.createElement("td")
      td.textContent = person[key]
      tr.append(td)
    }
    return tr
  }))
}
table.addEventListener("mj-sort-change", (event) => render(event.detail.field, event.detail.direction))
render("updated", "desc")
""",
        ),
        ComponentExample(
            key="with-mj-table",
            title="Driving an mj-table",
            description=(
                "<p>A toolbar of sort controls above an <code>&lt;mj-table&gt;</code>: the "
                "handler assigns the sorted <code>rows</code>. Price uses "
                "<code>cycle=\"asc-desc\"</code> (never unsorted) and Rating "
                "<code>cycle=\"desc-asc-none\"</code> (highest first).</p>"
            ),
            html=r"""<div class="sort-bar" id="sort-bar">
  <span>Sort by</span>
  <mj-sort-control field="name" group="products">Name</mj-sort-control>
  <mj-sort-control field="price" group="products" cycle="asc-desc">Price</mj-sort-control>
  <mj-sort-control field="rating" group="products" cycle="desc-asc-none">Rating</mj-sort-control>
</div>
<mj-table id="products" caption="Headphones"></mj-table>""",
            css=r""".sort-bar { display: flex; gap: var(--mj-space-2); align-items: center; margin-block-end: var(--mj-space-2); color: var(--mj-text-muted); }""",
            script=r"""const products = [
  { name: "Aria", price: 129, rating: 4.4 },
  { name: "Bolt", price: 59, rating: 3.9 },
  { name: "Coda", price: 249, rating: 4.8 },
  { name: "Drift", price: 89, rating: 4.1 }
]
const table = document.getElementById("products")
table.columns = [{ key: "name", label: "Model" }, { key: "price", label: "Price ($)" }, { key: "rating", label: "Rating" }]
table.rows = products
document.getElementById("sort-bar").addEventListener("mj-sort-change", (event) => {
  const { field, direction } = event.detail
  if (direction === "none") {
    table.rows = products
    return
  }
  const sorted = products.slice().sort((a, b) => (a[field] > b[field] ? 1 : (a[field] < b[field] ? -1 : 0)))
  table.rows = direction === "desc" ? sorted.reverse() : sorted
})
""",
        ),
        ComponentExample(
            key="states",
            title="Directions, disabled and labels",
            description=(
                "<p>The three directions, a <code>disabled</code> control, and one with German "
                "accessible-name templates (<code>label-none</code>, <code>label-asc</code>, "
                "<code>label-desc</code>; inspect its button's <code>aria-label</code>). The "
                "styled one sets <code>--mj-sort-control-*</code> properties.</p>"
            ),
            html=r"""<div class="row">
  <mj-sort-control field="a">Not sorted</mj-sort-control>
  <mj-sort-control field="b" direction="asc">Ascending</mj-sort-control>
  <mj-sort-control field="c" direction="desc">Descending</mj-sort-control>
  <mj-sort-control field="d" disabled>Disabled</mj-sort-control>
  <mj-sort-control field="e" label="Preis"
                   label-none="{label}: nicht sortiert" label-asc="{label}: aufsteigend" label-desc="{label}: absteigend">Preis</mj-sort-control>
  <mj-sort-control field="f" direction="asc" class="styled">Styled</mj-sort-control>
</div>""",
            css=r""".row { display: flex; flex-wrap: wrap; gap: var(--mj-space-3); padding: var(--mj-space-3); }
.styled {
  --mj-sort-control-border-color: var(--mj-border-strong);
  --mj-sort-control-bg-active: var(--mj-color-accent-100);
  --mj-sort-control-color-active: var(--mj-color-accent-700);
  --mj-sort-control-border-radius: var(--mj-radius-pill);
  --mj-sort-control-icon-size: 1rem;
}""",
        ),
        ComponentExample(
            key="events",
            title="Events, group and reset()",
            description=(
                "<p>The script clicks Size three times (none, ascending, descending, none), then "
                "Date, which resets Size through the shared <code>group</code>, and finally calls "
                "<code>reset()</code> on Date (no event). Every <code>mj-sort-change</code> shows "
                "<code>previousDirection</code>.</p>"
            ),
            html=r"""<div class="row">
  <mj-sort-control id="by-size" field="size" group="files">Size</mj-sort-control>
  <mj-sort-control id="by-date" field="date" group="files">Date</mj-sort-control>
</div>""",
            css=r""".row { display: flex; gap: var(--mj-space-3); padding: var(--mj-space-3); }""",
            script=r"""const size = document.getElementById("by-size")
const date = document.getElementById("by-date")
const pause = () => new Promise((resolve) => setTimeout(resolve, 500))
const click = (control) => control.shadowRoot.querySelector("button").click()
for (let i = 0; i < 3; i += 1) {
  await pause()
  click(size)
}
await pause()
click(size)
await pause()
click(date)
mjSandbox.log("after Date click", { size: size.direction, date: date.direction })
await pause()
date.reset()
mjSandbox.log("after reset()", { date: date.direction })
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="field",
            description="The data key the host sorts on; reported in `mj-sort-change`.",
            kind="string",
            values=["name", "updated"],
        ),
        AttributeDoc(
            name="direction",
            description="Current direction; set to `none` on first render when absent. Unknown values read as `none`.",
            kind="enum",
            values=["none", "asc", "desc"],
            default="none",
        ),
        AttributeDoc(
            name="cycle",
            description="Dash-separated steps in order (at least two of none / asc / desc), e.g. `asc-desc` or `desc-asc-none`.",
            kind="string",
            values=["none-asc-desc", "asc-desc", "desc-asc-none", "desc-asc"],
            default="none-asc-desc",
        ),
        AttributeDoc(
            name="group",
            description="Controls with the same group in one document or shadow root share one sort: activating one resets the others to none.",
            kind="string",
            values=["people"],
        ),
        AttributeDoc(
            name="label",
            description="Field label used in the accessible name (default: the slotted text, else `field`).",
            kind="string",
        ),
        AttributeDoc(
            name="label-none",
            description="Accessible-name template while unsorted; `{label}` is the field label.",
            kind="string",
        ),
        AttributeDoc(
            name="label-asc",
            description="Accessible-name template while sorted ascending.",
            kind="string",
        ),
        AttributeDoc(
            name="label-desc",
            description="Accessible-name template while sorted descending.",
            kind="string",
        ),
        AttributeDoc(
            name="disabled",
            description="Disables the button; activation does nothing.",
            kind="boolean",
        ),
    ],
    events=[
        ("mj-sort-change", "The user changed the direction (bubbles, composed). Not fired by `reset()`, `direction` or group resets.",
         "{ field: string, direction: 'none' | 'asc' | 'desc', previousDirection: string }"),
    ],
    slots=[
        ("", "The visible label; also used in the accessible name.", "Name"),
    ],
    properties=[
        ("field", "string. Reflects `field`."),
        ("direction", "'none' | 'asc' | 'desc'. Reflects `direction`; setting it does not emit an event."),
        ("disabled", "boolean. Reflects `disabled`."),
    ],
    methods=[
        ("reset()", "Sets the direction to `none` without an event (after a controlled change by the host)."),
    ],
    parts=[
        ("button", "The native button."),
        ("label", "Container of the slotted label."),
        ("indicator", "The direction icon."),
    ],
    css_properties=[
        ("--mj-sort-control-color", "Text colour (default `--mj-text`)."),
        ("--mj-sort-control-color-active", "Text colour while sorted (default `--mj-accent`)."),
        ("--mj-sort-control-bg", "Background (default transparent)."),
        ("--mj-sort-control-bg-hover", "Hover background (default `--mj-bg-muted`)."),
        ("--mj-sort-control-bg-active", "Background while sorted (default `--mj-bg-muted`)."),
        ("--mj-sort-control-border-color", "Border colour (default transparent)."),
        ("--mj-sort-control-border-radius", "Corner radius (default `--mj-radius-sm`)."),
        ("--mj-sort-control-height", "Minimum height (default `--mj-control-height-sm`)."),
        ("--mj-sort-control-font-weight", "Font weight (default `--mj-font-weight-medium`)."),
        ("--mj-sort-control-icon-size", "Indicator size (default 0.875rem)."),
        ("--mj-sort-control-indicator-color", "Indicator colour (default currentColor)."),
        ("--mj-sort-control-focus-ring-color", "Focus ring colour (default `--mj-focus-ring`)."),
    ],
)


# ===========================================================================
# mj-row-selector
# ===========================================================================

_ROW_SELECTOR = ComponentDoc(
    tag="mj-row-selector",
    title="Row Selector",
    group="data",
    summary="Form-associated row checkbox with a select-all mode and an indeterminate state.",
    description=(
        "<p><code>&lt;mj-row-selector&gt;</code> is the checkbox that selects a row in a table, "
        "list or tree grid. In <code>mode=\"row\"</code> (default) it carries the row's "
        "<code>value</code>; in <code>mode=\"all\"</code> it is the header select-all checkbox, "
        "with an optional <code>count</code> shown in parentheses. Either mode supports "
        "<code>indeterminate</code> (the mixed state); activating an indeterminate control clears "
        "it and selects the control. Every change emits <code>mj-row-select-change</code> with the "
        "new state and whether Shift was held (for range selection), and a click on the control "
        "never reaches the row it sits in, also while it is disabled, so it does not trigger row "
        "navigation or row selection.</p>"
        "<p>It is form-associated: with a <code>name</code> a selected control submits its "
        "<code>value</code> (or <code>on</code>), a form reset restores the authored "
        "<code>selected</code> state, and a disabled <code>&lt;fieldset&gt;</code> disables (and "
        "dims) it. It has no constraint validation (no <code>required</code>). The selection model "
        "belongs to the host, which listens for the events and keeps the select-all state in line "
        "with the rows.</p>"
    ),
    how_to_use=(
        "<p>Give each row a selector with <code>value</code> set to the row id and a "
        "<code>label</code> naming the row (the preferred accessible name; slotted text is used "
        "when visible, else a generic \"Select row\", also for an icon without text). Put a "
        "<code>mode=\"all\"</code> selector "
        "in the header and, after every change, set its <code>selected</code> (all rows "
        "selected) and <code>indeterminate</code> (some selected) properties and its "
        "<code>count</code>. Use <code>event.detail.shiftKey</code> to select a range. Setting "
        "<code>selected</code> / <code>indeterminate</code> from script does not emit an "
        "event.</p>"
    ),
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage (select-all wired to rows)",
            description=(
                "<p>A plain table with a <code>mode=\"all\"</code> selector in the header and one "
                "selector per row. One listener keeps them in sync: the header shows "
                "<code>indeterminate</code> and a <code>count</code> while some rows are "
                "selected, selected rows are highlighted, and Shift-click selects a range.</p>"
            ),
            html=r"""<table id="tasks-table">
  <thead>
    <tr>
      <th><mj-row-selector id="select-all" mode="all" label="Select all tasks"></mj-row-selector></th>
      <th>Task</th>
      <th>Owner</th>
    </tr>
  </thead>
  <tbody></tbody>
</table>""",
            css=r"""#tasks-table { border-collapse: collapse; inline-size: 100%; font-size: var(--mj-font-size-sm); }
#tasks-table th, #tasks-table td { text-align: start; padding: var(--mj-space-1) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }
#tasks-table th { background: var(--mj-bg-subtle); }
#tasks-table th:first-child { inline-size: 7rem; }
#tasks-table tr[aria-selected="true"] td { background: color-mix(in srgb, var(--mj-accent) 10%, transparent); }""",
            script=r"""const tasks = [
  { id: "t1", task: "Draft the announcement", owner: "Rosa" },
  { id: "t2", task: "Review the pricing page", owner: "Ken" },
  { id: "t3", task: "Record the demo video", owner: "Ama" },
  { id: "t4", task: "Update the changelog", owner: "Ken" },
  { id: "t5", task: "Schedule the webinar", owner: "Rosa" }
]
const table = document.getElementById("tasks-table")
const header = document.getElementById("select-all")
const body = table.tBodies[0]
for (const item of tasks) {
  const tr = document.createElement("tr")
  tr.dataset.id = item.id
  const cell = document.createElement("td")
  const selector = document.createElement("mj-row-selector")
  selector.value = item.id
  selector.setAttribute("label", "Select " + item.task)
  cell.append(selector)
  const name = document.createElement("td")
  name.textContent = item.task
  const owner = document.createElement("td")
  owner.textContent = item.owner
  tr.append(cell, name, owner)
  body.append(tr)
}
const rowSelectors = () => Array.from(body.querySelectorAll("mj-row-selector"))
let anchor = -1
function syncHeader() {
  const count = rowSelectors().filter((s) => s.selected).length
  header.selected = count === tasks.length
  header.indeterminate = count > 0 && count < tasks.length
  header.setAttribute("count", count + " of " + tasks.length)
  for (const selector of rowSelectors()) {
    selector.closest("tr").setAttribute("aria-selected", selector.selected ? "true" : "false")
  }
}
table.addEventListener("mj-row-select-change", (event) => {
  const selectors = rowSelectors()
  if (event.detail.mode === "all") {
    selectors.forEach((s) => { s.selected = event.detail.selected })
  } else {
    const index = selectors.findIndex((s) => s.value === event.detail.value)
    if (event.detail.shiftKey === true && anchor >= 0) {
      const [from, to] = [Math.min(anchor, index), Math.max(anchor, index)]
      for (let i = from; i <= to; i += 1) {
        selectors[i].selected = event.detail.selected
      }
    }
    anchor = index
  }
  syncHeader()
})
rowSelectors()[1].selected = true
syncHeader()
""",
        ),
        ComponentExample(
            key="in-mj-table",
            title="Inside an mj-table",
            description=(
                "<p>An <code>&lt;mj-table&gt;</code> column <code>render</code>s a selector per row. "
                "<code>mj-row-select-change</code> is composed, so it reaches a listener on the "
                "table from inside its shadow root; the summary below lists the selected "
                "values.</p>"
            ),
            html=r"""<mj-table id="servers-rs" caption="Servers to restart"></mj-table>
<p id="rs-summary">Nothing selected.</p>""",
            css=r"""#rs-summary { margin: var(--mj-space-2) 0; color: var(--mj-text-muted); }""",
            script=r"""const table = document.getElementById("servers-rs")
const chosen = new Set(["db-02"])
table.columns = [
  {
    key: "select", label: "Restart", labelHidden: true, rowHeader: false, width: "3rem",
    render: (row) => {
      const selector = document.createElement("mj-row-selector")
      selector.value = row.host
      selector.selected = chosen.has(row.host)
      selector.setAttribute("label", "Restart " + row.host)
      return selector
    }
  },
  { key: "host", label: "Host", rowHeader: true },
  { key: "uptime", label: "Uptime" }
]
table.rows = [
  { host: "web-01", uptime: "41 days" },
  { host: "web-02", uptime: "41 days" },
  { host: "db-02", uptime: "3 days" }
]
const summary = document.getElementById("rs-summary")
function show() {
  summary.textContent = chosen.size > 0 ? "Will restart: " + Array.from(chosen).join(", ") : "Nothing selected."
}
table.addEventListener("mj-row-select-change", (event) => {
  if (event.detail.selected === true) {
    chosen.add(event.detail.value)
  } else {
    chosen.delete(event.detail.value)
  }
  show()
})
show()
""",
        ),
        ComponentExample(
            key="form",
            title="Form participation",
            description=(
                "<p>Named selectors inside a form: Submit shows the <code>FormData</code> (each "
                "selected control submits its <code>value</code>), Reset restores the authored "
                "<code>selected</code> state, and the checkbox disables the "
                "<code>&lt;fieldset&gt;</code>, which disables every selector.</p>"
            ),
            html=r"""<form id="export-form">
  <fieldset id="export-fields">
    <legend>Export these reports</legend>
    <mj-row-selector name="report" value="sales" selected>Sales</mj-row-selector>
    <mj-row-selector name="report" value="traffic">Traffic</mj-row-selector>
    <mj-row-selector name="report" value="churn" selected>Churn</mj-row-selector>
  </fieldset>
  <label><input type="checkbox" id="lock"> Disable the fieldset</label>
  <div class="actions">
    <button type="submit">Export</button>
    <button type="reset">Reset</button>
  </div>
  <output id="export-result"></output>
</form>""",
            css=r"""fieldset { display: grid; gap: var(--mj-space-1); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
.actions { display: flex; gap: var(--mj-space-2); margin-block: var(--mj-space-3); }
output { color: var(--mj-text-muted); }""",
            script=r"""const form = document.getElementById("export-form")
const result = document.getElementById("export-result")
form.addEventListener("submit", (event) => {
  event.preventDefault()
  const reports = new FormData(form).getAll("report")
  result.textContent = "report = " + JSON.stringify(reports)
  mjSandbox.log("submitted", { report: reports })
})
document.getElementById("lock").addEventListener("change", (event) => {
  document.getElementById("export-fields").disabled = event.target.checked
})
""",
        ),
        ComponentExample(
            key="states",
            title="States and styling",
            description=(
                "<p>Unchecked, <code>selected</code>, <code>indeterminate</code>, "
                "<code>disabled</code>, a <code>mode=\"all\"</code> control with a "
                "<code>count</code>, one without visible text (named by <code>label</code>), one "
                "with only an icon (no text, so it gets the generated name \"Select row\"), and "
                "one styled with <code>--mj-row-selector-*</code> properties.</p>"
            ),
            html=r"""<div class="grid">
  <mj-row-selector value="1">Unchecked</mj-row-selector>
  <mj-row-selector value="2" selected>Selected</mj-row-selector>
  <mj-row-selector value="3" indeterminate>Indeterminate</mj-row-selector>
  <mj-row-selector value="4" disabled>Disabled</mj-row-selector>
  <mj-row-selector mode="all" indeterminate count="3 of 12">Select all</mj-row-selector>
  <mj-row-selector value="6" label="Select invoice 1042"></mj-row-selector>
  <mj-row-selector value="8"><svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M8 1.5l2 4.2 4.6.6-3.4 3.2.9 4.5L8 11.8 3.9 14l.9-4.5L1.4 6.3 6 5.7z" fill="currentColor"/></svg></mj-row-selector>
  <mj-row-selector value="7" selected class="styled">Styled</mj-row-selector>
</div>""",
            css=r""".grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr)); gap: var(--mj-space-2); padding: var(--mj-space-3); }
.styled {
  --mj-row-selector-size: 1.25rem;
  --mj-row-selector-accent: var(--mj-color-success);
  --mj-row-selector-bg-hover: var(--mj-color-success-surface);
  --mj-row-selector-border-radius: var(--mj-radius-pill);
}""",
        ),
        ComponentExample(
            key="events",
            title="Events",
            description=(
                "<p>The script clicks the row selector, Shift-clicks it, and clicks the "
                "indeterminate select-all (which clears the mixed state and selects). Each "
                "<code>mj-row-select-change</code> shows <code>mode</code>, <code>value</code> and "
                "<code>shiftKey</code>; the outer row's click counter stays at zero because the "
                "control stops its clicks.</p>"
            ),
            html=r"""<div id="row-box" class="box">
  <mj-row-selector id="one" value="order-17">Order 17</mj-row-selector>
  <mj-row-selector id="all" mode="all" indeterminate count="1 of 4">All orders</mj-row-selector>
  <span id="row-clicks">Row clicks: 0</span>
</div>""",
            css=r""".box { display: flex; gap: var(--mj-space-4); align-items: center; padding: var(--mj-space-3); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
#row-clicks { color: var(--mj-text-muted); }""",
            script=r"""let rowClicks = 0
document.getElementById("row-box").addEventListener("click", () => {
  rowClicks += 1
  document.getElementById("row-clicks").textContent = "Row clicks: " + rowClicks
})
const one = document.getElementById("one")
const all = document.getElementById("all")
const pause = () => new Promise((resolve) => setTimeout(resolve, 500))
const box = (selector) => selector.shadowRoot.querySelector("input")
await pause()
box(one).click()
await pause()
box(one).dispatchEvent(new MouseEvent("click", { bubbles: true, composed: true, shiftKey: true }))
await pause()
box(all).click()
mjSandbox.log("state", { one: one.selected, all: all.selected, allIndeterminate: all.indeterminate, rowClicks: rowClicks })
""",
        ),
    ],
    attributes=[
        AttributeDoc(
            name="mode",
            description="`row` selects one row; `all` is the header select-all (shows `count`).",
            kind="enum",
            values=["row", "all"],
            default="row",
        ),
        AttributeDoc(
            name="selected",
            description="The checked state; also the state a form reset returns to (as authored).",
            kind="boolean",
        ),
        AttributeDoc(
            name="indeterminate",
            description="Mixed state, in either mode; activation clears it and selects the control.",
            kind="boolean",
        ),
        AttributeDoc(
            name="value",
            description="Row identifier reported in the event and submitted with the form (`on` when empty).",
            kind="string",
            values=["row-42"],
        ),
        AttributeDoc(
            name="name",
            description="Form field name; a selected control submits `value` under it.",
            kind="string",
        ),
        AttributeDoc(
            name="label",
            description="Accessible name of the checkbox (preferred; otherwise the slotted text, else a generic name).",
            kind="string",
            values=["Select row 42"],
        ),
        AttributeDoc(
            name="count",
            description="Tally shown in parentheses after the label in `mode=\"all\"`, e.g. `3 of 12`.",
            kind="string",
            values=["3 of 12"],
        ),
        AttributeDoc(
            name="disabled",
            description="Disables and dims the checkbox; clicks on it still do not reach the row.",
            kind="boolean",
        ),
    ],
    events=[
        ("mj-row-select-change", "The user toggled the checkbox (bubbles, composed).",
         "{ selected: boolean, indeterminate: false, mode: 'row' | 'all', value: string, shiftKey: boolean }"),
    ],
    slots=[
        ("", "Visible label next to the checkbox; names it when it has text and no `label` is set (an icon alone does not: the generated name is used).", "Row 42"),
    ],
    properties=[
        ("mode", "'row' | 'all'. Reflects `mode`."),
        ("selected", "boolean. Reflects `selected`; setting it does not emit an event."),
        ("indeterminate", "boolean. Reflects `indeterminate`; setting it does not emit an event."),
        ("value", "string. Reflects `value`."),
        ("name", "string. Reflects `name`."),
        ("disabled", "boolean. Reflects `disabled`."),
    ],
    parts=[
        ("wrap", "The `<label>` around checkbox, text and count."),
        ("checkbox", "The native checkbox."),
        ("label", "Container of the slotted label (hidden when empty)."),
        ("count", "The count in `mode=\"all\"`."),
    ],
    css_properties=[
        ("--mj-row-selector-size", "Checkbox size (default 1rem)."),
        ("--mj-row-selector-accent", "Checkbox accent colour (default `--mj-accent`)."),
        ("--mj-row-selector-color", "Text colour (default `--mj-text`)."),
        ("--mj-row-selector-height", "Minimum height of the control (default `--mj-target-min`)."),
        ("--mj-row-selector-padding", "Padding of the control (default `--mj-space-1`)."),
        ("--mj-row-selector-border-radius", "Corner radius of the hover area (default `--mj-radius-sm`)."),
        ("--mj-row-selector-bg-hover", "Hover background (default `--mj-bg-muted`)."),
        ("--mj-row-selector-focus-ring-color", "Focus ring colour (default `--mj-focus-ring`)."),
        ("--mj-row-selector-label-font-size", "Label font size (default inherit)."),
        ("--mj-row-selector-count-color", "Count colour (default `--mj-text-muted`)."),
    ],
)


COMPONENTS = [
    _TABLE,
    _DATA_TABLE,
    _TREE_GRID,
    _LIST,
    _VIRTUAL_LIST,
    _KANBAN,
    _CALENDAR,
    _MASTER_DETAIL,
    _COLUMN_PICKER,
    _BULK_ACTION_BAR,
    _SORT_CONTROL,
    _ROW_SELECTOR,
]
