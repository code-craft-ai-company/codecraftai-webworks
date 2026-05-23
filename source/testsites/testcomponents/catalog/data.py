"""
    data.py

    Catalog entries for the 'Data & Display' component group.

    Each entry describes and demonstrates one data-oriented component:
    mj-table, mj-data-table, mj-tree-grid, mj-list, mj-virtual-list,
    mj-kanban, mj-calendar, mj-master-detail, mj-column-picker, and
    mj-bulk-action-bar.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-table",
        title="Table",
        group="data",
        summary="Static, read-only tabular data with native table semantics.",
        description=(
            "<p><code>&lt;mj-table&gt;</code> renders structured tabular data "
            "using native <code>&lt;table&gt;</code> semantics. It supports "
            "striped, bordered, and compact visual variants, optional sticky "
            "headers, a configurable caption, and three responsive strategies: "
            "<em>scroll</em> (default), priority column hiding, and "
            "<em>stack</em> (card layout at small widths). Data is supplied "
            "entirely through the <code>columns</code> and <code>rows</code> "
            "JavaScript properties; no server round-trip is needed.</p>"
        ),
        how_to_use=(
            "<p>Place the element in your HTML, then set the "
            "<code>columns</code> and <code>rows</code> properties in a "
            "<code>&lt;script&gt;</code> block. Each column object requires a "
            "<code>key</code> string and an optional <code>label</code>; each "
            "row is a plain object whose keys match the column keys. Use the "
            "<code>variant</code> attribute to choose the visual style, "
            "<code>caption</code> for an accessible title, and "
            "<code>responsive</code> to control narrow-viewport behaviour. "
            "Add <code>loading</code> to dim the table during data fetches.</p>"
        ),
        example=(
            '<mj-table id="demo-table" caption="Top Fruits" variant="striped"></mj-table>\n'
            "<script>\n"
            "  const t = document.getElementById('demo-table');\n"
            "  t.columns = [\n"
            "    { key: 'name',     label: 'Fruit'    },\n"
            "    { key: 'color',    label: 'Color'    },\n"
            "    { key: 'calories', label: 'Cal/100g' }\n"
            "  ];\n"
            "  t.rows = [\n"
            "    { name: 'Apple',  color: 'Red',    calories: 52 },\n"
            "    { name: 'Banana', color: 'Yellow', calories: 89 },\n"
            "    { name: 'Mango',  color: 'Orange', calories: 60 }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("caption", "Visible caption and accessible label for the table."),
            ("variant", "striped | bordered | compact visual style."),
            ("responsive", "scroll (default) | stack — narrow-viewport strategy."),
            ("sticky-header", "Boolean; fixes the header row during vertical scroll."),
            ("loading", "Boolean; dims the table and sets aria-busy while data loads."),
            ("col-widths", "Comma-separated widths applied to <col> elements (e.g. '120px,1fr')."),
        ],
        events=[
            ("mj-table-overflow", "Fired when horizontal overflow state changes; detail: { overflowing }."),
        ],
    ),
    ComponentDoc(
        tag="mj-data-table",
        title="Data Table",
        group="data",
        summary="Interactive data grid with sorting, filtering, selection, and cell editing.",
        description=(
            "<p><code>&lt;mj-data-table&gt;</code> is a full-featured "
            "interactive grid following the WAI-ARIA <em>grid</em> pattern. "
            "It virtualises rows for performance, supports click-to-sort on "
            "sortable columns, row selection (single or multi-row), "
            "double-click cell editing, and optional column resize handles. "
            "Data can be provided as a static <code>rows</code> array or "
            "through a <code>dataSource</code> adapter that handles "
            "server-side sorting and filtering.</p>"
        ),
        how_to_use=(
            "<p>Set <code>columns</code> (array of column descriptors with "
            "<code>key</code>, <code>label</code>, optional <code>width</code>, "
            "<code>sortable</code>, and <code>editable</code>) and "
            "<code>rows</code> (array of row objects) in script. Add the "
            "<code>sortable</code> attribute to enable column-header sorting, "
            "<code>resizable</code> for drag-resize handles, and "
            "<code>selection</code> (<code>single</code> or "
            "<code>multi-row</code>) for row selection. The "
            "<code>mode</code> attribute (<code>view</code> | <code>grid</code>) "
            "disables editing when set to <code>view</code>.</p>"
        ),
        example=(
            '<mj-data-table id="demo-dt" sortable selection="single"\n'
            '               style="height:260px"></mj-data-table>\n'
            "<script>\n"
            "  const dt = document.getElementById('demo-dt');\n"
            "  dt.columns = [\n"
            "    { key: 'id',   label: 'ID',   width: '60px'  },\n"
            "    { key: 'name', label: 'Name', width: '160px' },\n"
            "    { key: 'role', label: 'Role', width: '140px' }\n"
            "  ];\n"
            "  dt.rows = [\n"
            "    { id: 1, name: 'Alice',   role: 'Engineer'  },\n"
            "    { id: 2, name: 'Bob',     role: 'Designer'  },\n"
            "    { id: 3, name: 'Charlie', role: 'Manager'   },\n"
            "    { id: 4, name: 'Diana',   role: 'QA'        }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("mode", "view | grid — disables cell editing when set to view."),
            ("selection", "none (default) | single | multi-row row selection mode."),
            ("sortable", "Boolean; enables click-to-sort on all sortable columns."),
            ("filterable", "Boolean; enables per-column filter inputs in the toolbar."),
            ("resizable", "Boolean; shows drag handles on column borders."),
            ("row-height", "Row height in pixels (default 40)."),
            ("loading", "Boolean; dims the body and sets aria-busy."),
            ("empty-label", "Text shown when no rows match the current filter."),
        ],
        events=[
            ("mj-sort-change", "Fired on column sort; detail: { key, direction }."),
            ("mj-selection-change", "Fired on row selection; detail: { selectedRows }."),
            ("mj-cell-edit-start", "Cancelable; fired when a cell enters edit mode."),
            ("mj-cell-edit-commit", "Cancelable; fired when an edited value is committed."),
            ("mj-column-resize", "Fired after a column is resized; detail: { key, width }."),
        ],
    ),
    ComponentDoc(
        tag="mj-tree-grid",
        title="Tree Grid",
        group="data",
        summary="Hierarchical data grid following the WAI-ARIA treegrid pattern.",
        description=(
            "<p><code>&lt;mj-tree-grid&gt;</code> displays tree-structured "
            "tabular data — parent rows with collapsible children — using the "
            "WAI-ARIA <em>treegrid</em> role. Visible rows are maintained in a "
            "flattened list and rendered through a virtual window for "
            "performance. Expansion is in-place; keyboard navigation follows "
            "the ARIA treegrid specification (Arrow keys expand / collapse / "
            "move focus, Space selects).</p>"
        ),
        how_to_use=(
            "<p>Set <code>columns</code> (column descriptors with "
            "<code>key</code> and <code>label</code>) and <code>rows</code> "
            "(hierarchical array where each node may have a <code>children</code> "
            "array and must have a unique <code>key</code>; data values live in "
            "a <code>data</code> sub-object or directly on the node). Use "
            "<code>expand-depth</code> to pre-expand levels on load and "
            "<code>selection</code> to enable row selection.</p>"
        ),
        example=(
            '<mj-tree-grid id="demo-tg" expand-depth="1"\n'
            '              style="height:280px"></mj-tree-grid>\n'
            "<script>\n"
            "  const tg = document.getElementById('demo-tg');\n"
            "  tg.columns = [\n"
            "    { key: 'name', label: 'Name',  width: '200px' },\n"
            "    { key: 'size', label: 'Size',  width: '100px' }\n"
            "  ];\n"
            "  tg.rows = [\n"
            "    { key: 'docs',  data: { name: 'Documents', size: '—' }, children: [\n"
            "      { key: 'cv',    data: { name: 'CV.pdf',       size: '120 KB' } },\n"
            "      { key: 'cover', data: { name: 'Cover.docx',   size: '45 KB'  } }\n"
            "    ]},\n"
            "    { key: 'imgs',  data: { name: 'Images',    size: '—' }, children: [\n"
            "      { key: 'logo',  data: { name: 'logo.png',     size: '32 KB'  } }\n"
            "    ]}\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("mode", "view — disables interaction; future editing modes."),
            ("selection", "none (default) | single | multi-row."),
            ("sortable", "Boolean; enables sortable column headers."),
            ("loading", "Boolean; sets aria-busy on the grid root."),
            ("expand-depth", "Number of levels to auto-expand on initial render (default 1)."),
            ("row-height", "Row height in pixels (default 40)."),
        ],
        events=[
            ("mj-row-expand", "Cancelable; fired when a row is about to expand; detail: { key, level }."),
            ("mj-row-collapse", "Cancelable; fired when a row is about to collapse; detail: { key, level }."),
            ("mj-selection-change", "Fired on row selection change; detail: { selectedRows }."),
        ],
    ),
    ComponentDoc(
        tag="mj-list",
        title="List",
        group="data",
        summary="Semantic ordered, unordered, or description list with optional nesting and dividers.",
        description=(
            "<p><code>&lt;mj-list&gt;</code> renders a <code>&lt;ul&gt;</code>, "
            "<code>&lt;ol&gt;</code>, or <code>&lt;dl&gt;</code> depending on "
            "the <code>type</code> attribute. Items can be plain text, links, "
            "or action buttons, and may contain nested <code>&lt;mj-list&gt;</code> "
            "children. Optional dividers and three density presets "
            "(<code>compact</code>, default, <code>spacious</code>) make it "
            "easy to fit the component into any design context.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>items</code> property in script. Each item "
            "must have a <code>label</code> string and may include "
            "<code>href</code> (renders an anchor), <code>action</code> "
            "(renders a button), <code>description</code> (used for "
            "<code>dl</code> type), and a <code>children</code> array for "
            "nested lists. Use the <code>type</code>, <code>marker</code>, "
            "and <code>density</code> attributes to control appearance. "
            "Alternatively, place static <code>&lt;li&gt;</code> elements "
            "in the default slot.</p>"
        ),
        example=(
            '<mj-list id="demo-list" type="unordered" marker="disc"\n'
            '          density="spacious"></mj-list>\n'
            "<script>\n"
            "  document.getElementById('demo-list').items = [\n"
            "    { label: 'Design tokens',  href: '#tokens'  },\n"
            "    { label: 'Components',     href: '#comps'   },\n"
            "    { label: 'Patterns',       href: '#patterns' },\n"
            "    { label: 'Accessibility',  href: '#a11y'    }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("type", "unordered (default) | ordered | description."),
            ("marker", "bullet | disc | circle | square | decimal | alpha | roman | none."),
            ("density", "compact | (default) | spacious — controls gap between items."),
            ("dividers", "Boolean; inserts <hr> separators between items."),
            ("nested", "Boolean; adds indent; set automatically on nested lists."),
            ("start", "Starting number for ordered lists."),
            ("reversed", "Boolean; reverses the count of an ordered list."),
        ],
        events=[
            ("mj-item-click", "Fired when a link or button item is activated; detail: { index, label, href? }."),
        ],
    ),
    ComponentDoc(
        tag="mj-virtual-list",
        title="Virtual List",
        group="data",
        summary="Virtualized one-dimensional list for arbitrarily large datasets.",
        description=(
            "<p><code>&lt;mj-virtual-list&gt;</code> renders only the visible "
            "slice of a large item set plus a configurable overscan buffer, "
            "keeping DOM size constant regardless of total record count. It "
            "supports three loading strategies: <em>intersection</em> "
            "(auto-load when the sentinel enters the viewport), "
            "<em>manual</em> (a Load&nbsp;More button), or pre-loaded "
            "static arrays. A custom <code>renderItem</code> function lets "
            "you produce any HTML per item.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>items</code> property to a pre-loaded array, "
            "or assign a <code>dataSource</code> adapter that implements "
            "<code>query({ offset, limit })</code> returning "
            "<code>{ items, total }</code>. Assign a <code>renderItem</code> "
            "function to control per-item HTML — it receives <code>(item, index)</code> "
            "and must return a string or <code>HTMLElement</code>. Use "
            "<code>item-height</code> (pixels) and <code>page-size</code> to "
            "tune virtualisation. Listen for <code>mj-load-more</code> to "
            "append data manually.</p>"
        ),
        example=(
            '<mj-virtual-list id="demo-vl" item-height="44"\n'
            '                 load-strategy="manual"\n'
            '                 style="height:220px"></mj-virtual-list>\n'
            "<script>\n"
            "  const vl = document.getElementById('demo-vl');\n"
            "  vl.renderItem = (item) => `<div style='padding:8px 12px'>${item.label}</div>`;\n"
            "  const base = Array.from({ length: 40 }, (_, i) =>\n"
            "    ({ label: `Item ${i + 1}` }));\n"
            "  vl.items = base;\n"
            "</script>"
        ),
        attributes=[
            ("item-height", "Height of each list item in pixels (default 48)."),
            ("overscan", "Number of extra items to render above and below the viewport (default 3)."),
            ("page-size", "Number of items requested per page when using a dataSource (default 50)."),
            ("total", "Known total item count; used for aria-setsize."),
            ("loading", "Boolean; shows aria-busy on the container."),
            ("end-of-list", "Boolean; hides the Load More button when all items are loaded."),
            ("load-strategy", "intersection (default) | manual — controls how more items are triggered."),
            ("load-more-label", "Label for the Load More button (default 'Load more')."),
            ("empty-label", "Text shown when the list is empty (default 'No items')."),
        ],
        events=[
            ("mj-load-more", "Fired when more data should be fetched; detail: { offset, pageSize }."),
            ("mj-item-click", "Fired when an item is clicked; detail: { index, key, item }."),
            ("mj-items-rendered", "Fired after each virtual render; detail: { startIndex, endIndex, total }."),
            ("mj-scroll-end", "Fired when the user scrolls near the bottom; detail: { scrollTop }."),
        ],
    ),
    ComponentDoc(
        tag="mj-kanban",
        title="Kanban Board",
        group="data",
        summary="Multi-column card board for workflow visualisation with drag-and-drop.",
        description=(
            "<p><code>&lt;mj-kanban&gt;</code> renders a board of named "
            "columns (swim lanes) each holding a stack of cards. Cards can be "
            "moved between columns by pointer drag-and-drop or by a full "
            "keyboard move interface (press the card handle, navigate with "
            "Arrow keys, confirm with Enter, cancel with Escape). WIP limits "
            "per column are shown as a badge and fire an event when exceeded. "
            "A custom <code>renderCard</code> function controls card HTML.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>columns</code> property to an array of column "
            "descriptors. Each descriptor needs an <code>id</code>, a "
            "<code>label</code>, and a <code>cards</code> array. Each card "
            "needs an <code>id</code> and a <code>title</code>. Optionally "
            "add <code>wipLimit</code> to a column to enforce WIP constraints. "
            "Assign a <code>renderCard</code> function to customise card "
            "appearance. Add <code>mode=\"readonly\"</code> to disable "
            "drag handles. Listen for <code>mj-card-move</code> "
            "(cancelable) to persist moves.</p>"
        ),
        example=(
            '<mj-kanban id="demo-kb"></mj-kanban>\n'
            "<script>\n"
            "  document.getElementById('demo-kb').columns = [\n"
            "    { id: 'todo',  label: 'To Do',      cards: [\n"
            "      { id: 'c1', title: 'Write tests'   },\n"
            "      { id: 'c2', title: 'Update README'  }\n"
            "    ]},\n"
            "    { id: 'wip',   label: 'In Progress', wipLimit: 2, cards: [\n"
            "      { id: 'c3', title: 'Refactor API'   }\n"
            "    ]},\n"
            "    { id: 'done',  label: 'Done',         cards: [\n"
            "      { id: 'c4', title: 'Deploy v1.0'    }\n"
            "    ]}\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("mode", "interactive (default) | readonly — hides drag handles when readonly."),
            ("layout", "fluid — allows columns to wrap on narrow viewports."),
            ("wip-limits", "Boolean; show WIP limit badges and fire exceeded events."),
            ("loading", "Boolean; sets aria-busy on the board."),
        ],
        events=[
            ("mj-card-click", "Fired when a card body is clicked; detail: { cardId, colId }."),
            ("mj-card-move-start", "Fired when a drag begins; detail: { cardId, fromColId, fromIndex }."),
            ("mj-card-move", "Cancelable; fired before a card moves; detail: { cardId, fromColId, toColId, toIndex }."),
            ("mj-card-move-complete", "Fired after a successful move."),
            ("mj-card-move-error", "Fired when a dataSource moveCard call fails."),
            ("mj-col-wip-exceeded", "Fired when a column's WIP limit is exceeded after a move."),
        ],
    ),
    ComponentDoc(
        tag="mj-calendar",
        title="Calendar",
        group="data",
        summary="Calendar grid in month, week, day, or agenda view with event chips.",
        description=(
            "<p><code>&lt;mj-calendar&gt;</code> renders a locale-aware "
            "calendar in four switchable views: <em>month</em>, <em>week</em>, "
            "<em>day</em>, and <em>agenda</em>. Event objects are supplied "
            "through the <code>events</code> property or a "
            "<code>dataSource</code> adapter and appear as coloured chips "
            "within day cells. The built-in toolbar provides Previous/Next "
            "navigation and a view switcher. Keyboard navigation follows the "
            "WAI-ARIA grid pattern; the grid is navigable by arrow keys and "
            "Page Up / Page Down moves between periods.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>events</code> property to an array of event "
            "objects. Each event needs an <code>id</code>, a <code>title</code> "
            "string, and <code>start</code> / <code>end</code> values "
            "(<code>Date</code> objects or ISO 8601 strings). Optionally add "
            "<code>color</code> (CSS colour) for per-event chip colouring. "
            "Use the <code>view</code> attribute to set the initial view and "
            "<code>value</code> to set the initial date. Provide "
            "<code>min</code> / <code>max</code> to restrict selectable dates. "
            "Listen for <code>mj-date-select</code> and "
            "<code>mj-event-click</code>.</p>"
        ),
        example=(
            '<mj-calendar id="demo-cal" view="month"></mj-calendar>\n'
            "<script>\n"
            "  const today = new Date();\n"
            "  const y = today.getFullYear();\n"
            "  const m = today.getMonth();\n"
            "  document.getElementById('demo-cal').events = [\n"
            "    { id: 'e1', title: 'Team standup',\n"
            "      start: new Date(y, m, 3, 9, 0),\n"
            "      end:   new Date(y, m, 3, 9, 30) },\n"
            "    { id: 'e2', title: 'Design review',\n"
            "      start: new Date(y, m, 10, 14, 0),\n"
            "      end:   new Date(y, m, 10, 15, 0),\n"
            "      color: '#6366f1' },\n"
            "    { id: 'e3', title: 'Release',\n"
            "      start: new Date(y, m, 20, 11, 0),\n"
            "      end:   new Date(y, m, 20, 12, 0),\n"
            "      color: '#22c55e' }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("view", "month (default) | week | day | agenda."),
            ("value", "ISO 8601 date string for the initially displayed period."),
            ("min", "ISO 8601 minimum selectable date."),
            ("max", "ISO 8601 maximum selectable date."),
            ("first-day-of-week", "0 (Sunday, default) through 6 (Saturday)."),
            ("event-overflow", "Maximum event chips shown per cell before a '+N more' button (default 3)."),
            ("loading", "Boolean; sets aria-busy on the grid."),
            ("readonly", "Boolean; suppresses mj-event-create on cell click."),
        ],
        events=[
            ("mj-date-select", "Fired when a day cell is clicked; detail: { date } (ISO string)."),
            ("mj-event-click", "Fired when an event chip is clicked; detail: { eventId, event }."),
            ("mj-period-change", "Fired when the user navigates to a new period; detail: { start, end, view }."),
            ("mj-view-change", "Fired when the active view is switched; detail: { view }."),
            ("mj-event-create", "Cancelable; fired on blank day-cell click when not readonly."),
        ],
    ),
    ComponentDoc(
        tag="mj-master-detail",
        title="Master Detail",
        group="data",
        summary="Responsive split-panel layout — master list beside a contextual detail view.",
        description=(
            "<p><code>&lt;mj-master-detail&gt;</code> renders two panels "
            "side-by-side on wide viewports: a scrollable master list on the "
            "left and a detail view on the right. Below the configurable "
            "breakpoint (640&nbsp;px by default) the layout switches to "
            "stacked mode, hiding the inactive panel and showing a Back "
            "button in the detail panel. The divider between panels is "
            "draggable and keyboard-resizable. Selecting an item fires "
            "<code>mj-item-select</code> and optionally loads detail content "
            "through a <code>detailDataSource</code> function.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>items</code> property to an array of item "
            "descriptors, each with a <code>key</code> string, a "
            "<code>label</code>, and an optional <code>meta</code> secondary "
            "line. Place your detail markup in the <code>detail</code> named "
            "slot and update it in response to <code>mj-detail-load</code> "
            "or <code>mj-item-select</code>. Assign a "
            "<code>detailDataSource</code> function (receives the selected "
            "<code>key</code>, returns a Promise) to trigger automatic loading "
            "with the built-in loading / error states. Use "
            "<code>layout</code> to pin the layout instead of letting it "
            "auto-detect.</p>"
        ),
        example=(
            '<mj-master-detail id="demo-md"\n'
            '  master-label="Countries" detail-label="Detail"\n'
            '  style="height:300px; border:1px solid var(--mj-border)">\n'
            '  <div slot="detail" id="md-detail"\n'
            '    style="padding:16px; color:var(--mj-text-muted)">\n'
            "    Select a country to see details.\n"
            "  </div>\n"
            "</mj-master-detail>\n"
            "<script>\n"
            "  const md = document.getElementById('demo-md');\n"
            "  md.items = [\n"
            "    { key: 'fr', label: 'France',  meta: 'Europe'   },\n"
            "    { key: 'jp', label: 'Japan',   meta: 'Asia'     },\n"
            "    { key: 'br', label: 'Brazil',  meta: 'Americas' }\n"
            "  ];\n"
            "  md.addEventListener('mj-item-select', (e) => {\n"
            "    document.getElementById('md-detail').textContent =\n"
            "      'Selected: ' + e.detail.item.label;\n"
            "  });\n"
            "</script>"
        ),
        attributes=[
            ("layout", "auto (default) | side-by-side | stacked."),
            ("selected-key", "Key of the initially or programmatically selected item."),
            ("resizable", "Boolean; enables pointer and keyboard resize of the divider."),
            ("master-label", "Accessible label for the master panel (default 'List')."),
            ("detail-label", "Accessible label for the detail panel (default 'Detail')."),
            ("back-label", "Label for the Back button in stacked mode (default 'Back')."),
            ("loading-detail", "Boolean; shows the built-in loading spinner in the detail panel."),
        ],
        events=[
            ("mj-item-select", "Cancelable; fired when a master item is clicked; detail: { key, item }."),
            ("mj-detail-load", "Fired when detailDataSource resolves; detail: { key, data }."),
            ("mj-detail-error", "Fired when detailDataSource rejects; detail: { key, error }."),
            ("mj-layout-change", "Fired when auto layout switches; detail: { layout }."),
            ("mj-panel-resize", "Fired after the divider is released; detail: { masterWidth }."),
            ("mj-back", "Fired when the Back button is pressed in stacked mode."),
        ],
    ),
    ComponentDoc(
        tag="mj-column-picker",
        title="Column Picker",
        group="data",
        summary="Popover panel for toggling column visibility and reordering columns.",
        description=(
            "<p><code>&lt;mj-column-picker&gt;</code> is a trigger button "
            "that opens a dialog panel listing all columns with checkboxes to "
            "show or hide them. Columns can optionally be reordered by "
            "keyboard drag (Space to grab, Arrow keys to move, Enter to "
            "confirm, Escape to cancel). Changes can be applied immediately "
            "as each checkbox is toggled, or deferred until an Apply button "
            "is clicked. A Reset button restores the original column set.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>columns</code> property to the same column "
            "descriptor array used by the associated table or grid. Each "
            "descriptor should have <code>key</code>, <code>label</code>, "
            "optional <code>visible</code> (boolean, default <code>true</code>), "
            "optional <code>locked</code> (boolean, prevents hide/reorder), "
            "and optional <code>reorderable</code>. Also set "
            "<code>defaultColumns</code> to enable the Reset function. "
            "Use <code>apply-mode=\"deferred\"</code> to show an Apply "
            "button. Listen for <code>mj-column-visibility-change</code> "
            "and <code>mj-column-reorder</code> to update the table.</p>"
        ),
        example=(
            '<mj-column-picker id="demo-cp" label="Columns"\n'
            '                  apply-mode="immediate"\n'
            '                  reorderable="true"></mj-column-picker>\n'
            "<script>\n"
            "  const cols = [\n"
            "    { key: 'name',  label: 'Name',   visible: true,  locked: true  },\n"
            "    { key: 'email', label: 'Email',  visible: true  },\n"
            "    { key: 'role',  label: 'Role',   visible: true  },\n"
            "    { key: 'dept',  label: 'Dept',   visible: false }\n"
            "  ];\n"
            "  const cp = document.getElementById('demo-cp');\n"
            "  cp.columns = cols;\n"
            "  cp.defaultColumns = cols;\n"
            "  cp.addEventListener('mj-column-visibility-change', (e) => {\n"
            "    console.log('columns updated', e.detail.columns);\n"
            "  });\n"
            "</script>"
        ),
        attributes=[
            ("label", "Button label and panel heading (default 'Columns')."),
            ("apply-mode", "immediate (default) | deferred — when visibility changes are applied."),
            ("reorderable", "Boolean (default true); enables drag-reorder handles."),
            ("min-visible", "Minimum number of columns that must remain visible (default 1)."),
            ("open", "Boolean; controls panel open state."),
            ("disabled", "Boolean; disables the trigger button."),
        ],
        events=[
            ("mj-picker-open", "Fired when the panel opens."),
            ("mj-picker-close", "Fired when the panel closes."),
            ("mj-column-visibility-change", "Fired (immediate mode) when a column is shown/hidden; detail: { key, visible, columns }."),
            ("mj-column-reorder", "Fired after a column is reordered; detail: { key, from, to, columns }."),
            ("mj-columns-apply", "Fired (deferred mode) when Apply is clicked; detail: { columns }."),
            ("mj-columns-reset", "Fired when Reset is clicked; detail: { columns }."),
        ],
    ),
    ComponentDoc(
        tag="mj-bulk-action-bar",
        title="Bulk Action Bar",
        group="data",
        summary="Contextual toolbar shown when rows are selected, with select-all and action buttons.",
        description=(
            "<p><code>&lt;mj-bulk-action-bar&gt;</code> is a toolbar "
            "displayed when one or more rows are selected in a table, grid, "
            "or list. It shows a tri-state select-all checkbox, a live count "
            "label, action buttons rendered from the <code>actions</code> "
            "property, and a clear-selection (×) button. The bar is "
            "automatically hidden when <code>selected-count</code> drops to "
            "zero and shown when it rises above zero. It can be positioned "
            "as an inline or floating sticky element. Escape clears the "
            "selection via <code>mj-clear-selection</code>.</p>"
        ),
        how_to_use=(
            "<p>Set <code>selected-count</code> and <code>total-count</code> "
            "attributes (or properties) to the number of currently selected "
            "and total rows. Set the <code>actions</code> property to an "
            "array of action descriptors — each with <code>key</code>, "
            "<code>label</code>, optional <code>icon</code> (text/emoji), "
            "optional <code>destructive</code> (boolean), and optional "
            "<code>disabled</code>. The bar shows automatically when "
            "<code>selected-count &gt; 0</code>. Listen for "
            "<code>mj-action</code> to handle button clicks and "
            "<code>mj-select-all</code> (cancelable) for the checkbox. "
            "Use <code>position=\"floating\"</code> for a sticky bottom bar.</p>"
        ),
        example=(
            '<mj-bulk-action-bar id="demo-bab"\n'
            '  selected-count="3" total-count="20"\n'
            '  visible></mj-bulk-action-bar>\n'
            "<script>\n"
            "  const bab = document.getElementById('demo-bab');\n"
            "  bab.actions = [\n"
            "    { key: 'export',  label: 'Export',  icon: '⬇' },\n"
            "    { key: 'tag',     label: 'Tag',     icon: '🏷' },\n"
            "    { key: 'delete',  label: 'Delete',  icon: '🗑', destructive: true }\n"
            "  ];\n"
            "  bab.addEventListener('mj-action', (e) => {\n"
            "    alert('Action: ' + e.detail.actionKey +\n"
            "          ' on ' + e.detail.selectedKeys.length + ' items');\n"
            "  });\n"
            "  bab.addEventListener('mj-clear-selection', () => {\n"
            "    bab.selectedCount = 0;\n"
            "  });\n"
            "</script>"
        ),
        attributes=[
            ("selected-count", "Number of currently selected rows (drives the count label and checkbox state)."),
            ("total-count", "Total number of rows in the list (used to determine checked vs indeterminate state)."),
            ("visible", "Boolean; forces the bar to show regardless of selected-count."),
            ("disabled", "Boolean; disables all action buttons and the select-all checkbox."),
            ("position", "inline (default) | floating — floating makes the bar sticky at the bottom."),
            ("select-all-label", "Accessible label for the select-all checkbox (default 'Select all')."),
            ("clear-label", "Accessible label for the clear button (default 'Clear selection')."),
            ("count-label", "Template for the count label; use {n} as the placeholder (default '{n} selected')."),
        ],
        events=[
            ("mj-action", "Fired when an action button is clicked; detail: { actionKey, selectedKeys }."),
            ("mj-select-all", "Cancelable; fired when the select-all checkbox is toggled; detail: { selectAll }."),
            ("mj-clear-selection", "Fired when the × button is clicked or Escape is pressed."),
        ],
    ),
    ComponentDoc(
        tag="mj-sort-control",
        title="Sort Control",
        group="data",
        summary="Sort header indicator that cycles none -> asc -> desc on activation.",
        description=(
            "<p><code>&lt;mj-sort-control&gt;</code> is the standalone "
            "Sort control companion for DataTable / List / treegrid hosts "
            "(plan 5.8). It can live in a column header or anywhere else "
            "in the DOM; click or keyboard activation cycles the sort "
            "direction through <code>none -&gt; asc -&gt; desc -&gt; "
            "none</code> for the named field and emits "
            "<code>mj-sort-change</code> on every transition.</p>"
        ),
        how_to_use=(
            "<p>Set <code>field</code> to the dataset key the host will "
            "sort on. Slot the visible column label as the control's "
            "child text. Listen for <code>mj-sort-change</code> and "
            "re-sort the dataset.</p>"
        ),
        example=(
            '<mj-sort-control field="name">Name</mj-sort-control>\n'
            '<mj-sort-control field="updated" direction="desc">Updated</mj-sort-control>'
        ),
        attributes=[
            ("field", "Field identifier used by the host to sort the dataset."),
            ("direction", "none | asc | desc; the active sort direction."),
            ("label", "Override accessible label (defaults to slotted text)."),
            ("disabled", "Boolean; blocks activation."),
        ],
        events=[
            ("mj-sort-change", "Fired on every direction change with { field, direction, previousDirection }."),
        ],
    ),
    ComponentDoc(
        tag="mj-row-selector",
        title="Row Selector",
        group="data",
        summary="Checkbox row-selector with select-all + indeterminate modes.",
        description=(
            "<p><code>&lt;mj-row-selector&gt;</code> is the DataTable / "
            "List row-selection companion (plan 5.8). In "
            "<code>mode=\"row\"</code> it carries a per-row value; in "
            "<code>mode=\"all\"</code> it acts as the header select-all "
            "checkbox with <code>indeterminate</code> support. Form-"
            "associated via ElementInternals so the control reports its "
            "checkbox state on form submit.</p>"
        ),
        how_to_use=(
            "<p>For per-row use, set <code>value</code> to the row's "
            "identifier and listen for <code>mj-row-select-change</code>. "
            "For the header, set <code>mode=\"all\"</code>, drive "
            "<code>selected</code> + <code>indeterminate</code> from the "
            "selected-count, and optionally provide <code>count</code> for "
            "an inline tally.</p>"
        ),
        example=(
            '<mj-row-selector mode="all" indeterminate count="3 of 12">'
            "Select all</mj-row-selector>\n"
            '<mj-row-selector value="row-42">Row 42</mj-row-selector>'
        ),
        attributes=[
            ("mode", "row (default) | all."),
            ("selected", "Boolean; the checked state."),
            ("indeterminate", "Boolean; only meaningful in mode=all."),
            ("value", "Row identifier carried in the form value and the change event."),
            ("name", "Form-field name when used inside <form>."),
            ("count", "Optional inline count string (mode=all only, e.g. '3 of 12')."),
            ("label", "Override accessible label."),
            ("disabled", "Boolean; blocks activation."),
        ],
        events=[
            ("mj-row-select-change", "Fired with { selected, indeterminate, mode, value }."),
        ],
    ),
]
