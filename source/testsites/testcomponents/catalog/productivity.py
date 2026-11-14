"""
    productivity.py

    Catalog entries for the 'Productivity' component group.

    Covers toolbar, menubar, status bar, app shell, search results, filter
    panel, query builder, dropzone, file browser, activity feed, comments,
    mention input, chat composer, and chat message.

    Each entry is a sandbox page: an example gallery (the first example is the
    one the functional tests in tests/test_func_productivity.py load), typed
    attribute controls, and reference tables taken from the component code.
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


# ---------------------------------------------------------------------------
# mj-toolbar
# ---------------------------------------------------------------------------

TOOLBAR = ComponentDoc(
    tag="mj-toolbar",
    title="Toolbar",
    group="productivity",
    summary="A strip of controls with one tab stop, arrow-key navigation and a More actions popup for items that do not fit.",
    description=(
        "<p><code>&lt;mj-toolbar&gt;</code> implements the WAI-ARIA toolbar pattern "
        "(<code>role=\"toolbar\"</code>). The controls among its children form a roving set "
        "with a single tab stop: native <code>button</code>, <code>a[href]</code>, "
        "<code>input</code>, <code>select</code>, <code>textarea</code>, elements with a "
        "<code>tabindex</code> or <code>data-toolbar-item</code>, and the library's button, "
        "select and field elements (<code>mj-button</code>, <code>mj-toggle-button</code>, "
        "<code>mj-menu-button</code>, <code>mj-select</code>, <code>mj-search-input</code> "
        "&hellip;). For those the tab stop is the inner control, never the host. Disabled and "
        "hidden items are skipped.</p>"
        "<p>A horizontal toolbar that is narrower than its content moves the trailing "
        "children into a popup opened by a &ldquo;More actions&rdquo; button (they get "
        "<code>slot=\"mj-toolbar-overflow\"</code> while there and stay fully operable), and "
        "moves them back when room returns; <code>mj-toolbar-overflow-change</code> reports "
        "the change. <code>variant=\"action-bar\"</code> floats a contextual bar that is shown "
        "only while <code>active</code> is set; <code>variant=\"ribbon\"</code> is accepted and "
        "renders as the plain toolbar. <code>disabled</code> makes the whole toolbar "
        "<code>inert</code> (no pointer or keyboard interaction).</p>"
    ),
    how_to_use=(
        "<p>Put the controls (optionally grouped in wrapper elements) directly inside. Name the "
        "toolbar with <code>label</code>, or with <code>labelledby</code> set to the id of a "
        "visible heading in the same document (its text is copied). Keys: "
        "<kbd>ArrowLeft</kbd>/<kbd>ArrowRight</kbd> (or <kbd>ArrowUp</kbd>/<kbd>ArrowDown</kbd> "
        "with <code>orientation=\"vertical\"</code>), <kbd>Home</kbd>, <kbd>End</kbd>; text "
        "fields and selects keep the keys they need (the caret moves inside a field until it "
        "reaches the edge; with <kbd>Shift</kbd> the keys always stay in the field and extend "
        "its selection). <kbd>ArrowDown</kbd> on the More actions button opens the popup, "
        "<kbd>Escape</kbd> closes it. Mark a custom focusable element with "
        "<code>data-toolbar-item</code> to add it to the set.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the toolbar.", kind="string",
                     values=["Text formatting", "Editor tools"]),
        AttributeDoc(name="labelledby", description="Id of an element in the same document whose text names the toolbar (wins over `label`).",
                     kind="string"),
        AttributeDoc(name="orientation", description="Layout and arrow keys; a vertical toolbar never overflows.",
                     kind="enum", values=["horizontal", "vertical"], default="horizontal"),
        AttributeDoc(name="variant", description="`action-bar` floats a contextual bar shown while `active`; `ribbon` renders as the plain toolbar.",
                     kind="enum", values=["action-bar", "ribbon"]),
        AttributeDoc(name="active", description="Shows an `action-bar` toolbar (no effect on other variants).",
                     kind="boolean"),
        AttributeDoc(name="overflow-button-label", description="Accessible name of the More actions button and its popup.",
                     kind="string", default="More actions"),
        AttributeDoc(name="disabled", description="Dims the toolbar and makes it inert: no item can be focused or clicked.",
                     kind="boolean"),
    ],
    events=[
        ("mj-toolbar-overflow-change", "The set of items in the More actions popup changed (resize or content change).",
         "{ overflowCount: number, overflowItems: Element[] }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Three <code>mj-button</code> items with one tab stop. Tab into the toolbar, then "
                "use <kbd>ArrowLeft</kbd>/<kbd>ArrowRight</kbd>, <kbd>Home</kbd> and <kbd>End</kbd>.</p>"
            ),
            html=(
                '<mj-toolbar label="Text formatting">\n'
                '  <mj-button variant="secondary" size="sm">Bold</mj-button>\n'
                '  <mj-button variant="secondary" size="sm">Italic</mj-button>\n'
                '  <mj-button variant="secondary" size="sm">Underline</mj-button>\n'
                '</mj-toolbar>'
            ),
            css="mj-toolbar { margin: var(--mj-space-4); }\n",
        ),
        ComponentExample(
            key="mixed-controls",
            title="Groups and mixed controls",
            description=(
                "<p>Toggle buttons, a select and a search field in groups. In the field the arrows "
                "move the caret and leave the field only at its edges; the select keeps "
                "<kbd>ArrowUp</kbd>/<kbd>ArrowDown</kbd>. The script reports the pressed styles.</p>"
            ),
            html=(
                '<mj-toolbar id="editor-tools" label="Editor tools">\n'
                '  <div class="group" role="group" aria-label="Style">\n'
                '    <mj-toggle-button size="sm" value="bold">Bold</mj-toggle-button>\n'
                '    <mj-toggle-button size="sm" value="italic">Italic</mj-toggle-button>\n'
                '    <mj-toggle-button size="sm" value="code">Code</mj-toggle-button>\n'
                '  </div>\n'
                '  <div class="group">\n'
                '    <select aria-label="Block type">\n'
                '      <option>Paragraph</option><option>Heading 1</option><option>Heading 2</option><option>Quote</option>\n'
                '    </select>\n'
                '  </div>\n'
                '  <div class="group">\n'
                '    <input type="search" aria-label="Find in document" placeholder="Find&hellip;" value="roadmap">\n'
                '    <button type="button">Replace</button>\n'
                '  </div>\n'
                '</mj-toolbar>'
            ),
            css=(
                "mj-toolbar { margin: var(--mj-space-4); }\n"
                ".group { display: flex; gap: var(--mj-space-1); align-items: center; }\n"
                ".group + .group { padding-inline-start: var(--mj-space-3); border-inline-start: 1px solid var(--mj-border); }\n"
            ),
            script=(
                'const tools = document.getElementById("editor-tools")\n'
                'tools.addEventListener("click", () => {\n'
                '  const pressed = Array.from(tools.querySelectorAll("mj-toggle-button[pressed]")).map((b) => b.getAttribute("value"))\n'
                '  mjSandbox.log("pressed styles", { pressed: pressed })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="overflow",
            title="Overflow into More actions",
            description=(
                "<p>The toolbar sits in a container you can resize by dragging its corner (or use "
                "the 320 / 768 preview widths). Items that do not fit move into the popup behind "
                "the custom <code>overflow-icon</code>; <code>mj-toolbar-overflow-change</code> "
                "appears in Events each time the set changes.</p>"
            ),
            html=(
                '<div class="resizable">\n'
                '  <mj-toolbar id="formatting" label="Formatting" overflow-button-label="More formatting">\n'
                '    <button type="button">Bold</button>\n'
                '    <button type="button">Italic</button>\n'
                '    <button type="button">Underline</button>\n'
                '    <button type="button">Strikethrough</button>\n'
                '    <button type="button">Highlight</button>\n'
                '    <button type="button">Link</button>\n'
                '    <button type="button">Bulleted list</button>\n'
                '    <button type="button">Numbered list</button>\n'
                '    <button type="button">Clear formatting</button>\n'
                '    <span slot="overflow-icon" aria-hidden="true">&#9662; More</span>\n'
                '  </mj-toolbar>\n'
                '</div>'
            ),
            css=(
                ".resizable {\n"
                "  inline-size: 360px;\n"
                "  max-inline-size: 100%;\n"
                "  margin: var(--mj-space-4);\n"
                "  padding: var(--mj-space-2);\n"
                "  overflow: hidden;\n"
                "  resize: horizontal;\n"
                "  border: 1px dashed var(--mj-border-strong);\n"
                "}\n"
            ),
            script=(
                'const formatting = document.getElementById("formatting")\n'
                'mjSandbox.log("initial overflow", { items: formatting.overflowItems.map((item) => item.textContent) })\n'
            ),
            height=260,
        ),
        ComponentExample(
            key="vertical",
            title="Vertical, named by a heading",
            description=(
                "<p><code>orientation=\"vertical\"</code> stacks the items and uses "
                "<kbd>ArrowUp</kbd>/<kbd>ArrowDown</kbd>; <code>labelledby</code> takes the name "
                "from the visible heading.</p>"
            ),
            html=(
                '<div class="side">\n'
                '  <h3 id="draw-tools">Drawing tools</h3>\n'
                '  <mj-toolbar orientation="vertical" labelledby="draw-tools">\n'
                '    <mj-toggle-button size="sm" pressed>Select</mj-toggle-button>\n'
                '    <mj-toggle-button size="sm">Pen</mj-toggle-button>\n'
                '    <mj-toggle-button size="sm">Shape</mj-toggle-button>\n'
                '    <mj-toggle-button size="sm">Text</mj-toggle-button>\n'
                '    <mj-button size="sm" variant="tertiary">Undo</mj-button>\n'
                '  </mj-toolbar>\n'
                '</div>'
            ),
            css=(
                ".side { display: inline-grid; gap: var(--mj-space-2); margin: var(--mj-space-4); }\n"
                ".side h3 { margin: 0; font-size: var(--mj-font-size-sm); }\n"
            ),
        ),
        ComponentExample(
            key="action-bar",
            title="Contextual action bar",
            description=(
                "<p><code>variant=\"action-bar\"</code> floats above the list and is shown only "
                "while <code>active</code> is set: the script sets it while at least one row is "
                "ticked and the bar acts on the selection.</p>"
            ),
            html=(
                '<div class="files">\n'
                '  <div class="bar-area">\n'
                '    <mj-toolbar id="selection-bar" variant="action-bar" label="Selected files">\n'
                '      <span id="selected-count" class="count">0 selected</span>\n'
                '      <button type="button" data-action="download">Download</button>\n'
                '      <button type="button" data-action="move">Move</button>\n'
                '      <button type="button" data-action="delete">Delete</button>\n'
                '    </mj-toolbar>\n'
                '  </div>\n'
                '  <ul class="rows">\n'
                '    <li><label><input type="checkbox"> Q4 roadmap.pdf</label></li>\n'
                '    <li><label><input type="checkbox"> Brand guidelines.pdf</label></li>\n'
                '    <li><label><input type="checkbox"> Launch banner.png</label></li>\n'
                '    <li><label><input type="checkbox"> Budget 2027.xlsx</label></li>\n'
                '  </ul>\n'
                '</div>'
            ),
            css=(
                ".files { min-block-size: 220px; margin: var(--mj-space-4);\n"
                "         border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }\n"
                ".rows { list-style: none; margin: 0; padding: 0 var(--mj-space-3); }\n"
                ".rows li { padding-block: var(--mj-space-2); border-block-end: 1px solid var(--mj-border); }\n"
                ".count { font-weight: var(--mj-font-weight-medium); }\n"
                ".bar-area { position: relative; block-size: 56px; padding-block-start: var(--mj-space-2); }\n"
            ),
            script=(
                'const bar = document.getElementById("selection-bar")\n'
                'const boxes = Array.from(document.querySelectorAll(".rows input"))\n'
                'function sync() {\n'
                '  const count = boxes.filter((box) => box.checked).length\n'
                '  bar.toggleAttribute("active", count > 0)\n'
                '  document.getElementById("selected-count").textContent = count + " selected"\n'
                '}\n'
                'boxes.forEach((box) => box.addEventListener("change", sync))\n'
                'bar.addEventListener("click", (event) => {\n'
                '  const button = event.target.closest("button[data-action]")\n'
                '  if (button) {\n'
                '    mjSandbox.log("action", { action: button.dataset.action, files: boxes.filter((b) => b.checked).length })\n'
                '  }\n'
                '})\n'
                'boxes[0].checked = true\n'
                'boxes[2].checked = true\n'
                'sync()\n'
            ),
        ),
        ComponentExample(
            key="disabled",
            title="Disabled",
            description="<p><code>disabled</code> dims the toolbar and makes it inert: its items cannot be focused or clicked. Toggle it in Controls.</p>",
            html=(
                '<mj-toolbar label="Review actions" disabled>\n'
                '  <mj-button size="sm" variant="primary">Approve</mj-button>\n'
                '  <mj-button size="sm" variant="secondary">Request changes</mj-button>\n'
                '  <mj-button size="sm" variant="tertiary">Comment</mj-button>\n'
                '</mj-toolbar>'
            ),
            css="mj-toolbar { margin: var(--mj-space-4); }\n",
        ),
    ],
    slots=[
        ("", "The toolbar controls; direct children are the units that move into the overflow popup.",
         '<button type="button">Bold</button><button type="button">Italic</button>'),
        ("overflow-icon", "Content of the More actions button (default a horizontal ellipsis).",
         '<span aria-hidden="true">&#9662; More</span>'),
    ],
    properties=[
        ("items", "Element[], read-only. The items the arrow keys reach right now, in order (popup items only while it is open)."),
        ("overflowItems", "Element[], read-only. The items currently moved into the More actions popup."),
    ],
    methods=[],
    parts=[
        ("root", "The `role=\"toolbar\"` strip."),
        ("overflow-button", "The More actions button."),
        ("overflow-menu", "The popup holding the overflowed items."),
    ],
    css_properties=[
        ("--mj-toolbar-height", "Minimum height of the strip (default `--mj-control-height-md`)."),
        ("--mj-toolbar-group-gap", "Gap between children of the strip (default `--mj-space-3`)."),
        ("--mj-toolbar-gap", "Gap between items in the overflow popup (default `--mj-space-1`)."),
        ("--mj-toolbar-bg", "Background (default `--mj-surface`)."),
        ("--mj-toolbar-border", "Border colour (default `--mj-border`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-menubar
# ---------------------------------------------------------------------------

MENUBAR = ComponentDoc(
    tag="mj-menubar",
    title="Menubar",
    group="productivity",
    summary="Application menubar built from a hidden definition, with dropdown menus and the full APG keyboard model.",
    description=(
        "<p><code>&lt;mj-menubar&gt;</code> implements the WAI-ARIA menubar pattern. Its "
        "children are a <em>definition</em> that is never displayed: each child element is a "
        "top-level menu, named by its <code>label</code> attribute (or, without one, by its own "
        "text outside its entries), and its descendants matching <code>[data-menu-item]</code>, "
        "<code>[role=\"menuitem\"]</code> or <code>li</code> become the menu's entries (flat, "
        "in document order; no submenus). An entry's text is its label and its "
        "<code>value</code> attribute (default: the label) is reported when it is chosen. "
        "<code>hr</code>, <code>[role=\"separator\"]</code> and "
        "<code>[data-menu-separator]</code> elements become separators (also on an "
        "<code>li</code>). A "
        "<code>disabled</code> attribute on a menu or an entry disables it. Changes to the "
        "definition rebuild the bar.</p>"
        "<p>Keyboard: on the bar, <kbd>ArrowLeft</kbd>/<kbd>ArrowRight</kbd>, <kbd>Home</kbd>, "
        "<kbd>End</kbd> and a letter move between menus; <kbd>ArrowDown</kbd>, <kbd>Enter</kbd> "
        "or <kbd>Space</kbd> open a menu on its first entry and <kbd>ArrowUp</kbd> on its last. "
        "In an open menu <kbd>ArrowUp</kbd>/<kbd>ArrowDown</kbd>, <kbd>Home</kbd>, "
        "<kbd>End</kbd> and letters move, <kbd>ArrowLeft</kbd>/<kbd>ArrowRight</kbd> switch to "
        "the neighbouring menu, <kbd>Enter</kbd>/<kbd>Space</kbd> choose and <kbd>Escape</kbd> "
        "closes. With a menu open, hovering another top-level item opens that one. While a menu "
        "is open the host's <code>active-item</code> attribute names it.</p>"
    ),
    how_to_use=(
        "<p>Write one element per menu with a <code>label</code>, and entries inside it with "
        "<code>data-menu-item</code> (or <code>li</code> / <code>role=\"menuitem\"</code>) and a "
        "<code>value</code>. Listen for <code>mj-menubar-select</code>: its detail carries the "
        "entry's <code>value</code>, the definition elements (<code>item</code> for the menu, "
        "<code>menuItem</code> for the entry) and <code>path</code> = <code>[menu label, entry "
        "label]</code>. Set <code>active-item</code> to a menu's id, value or label to open it "
        "from script, remove it to close. Inside list markup a separator is an "
        "<code>&lt;li role=\"separator\"&gt;</code> or <code>&lt;li data-menu-separator&gt;</code> "
        "(or an <code>hr</code>).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the menubar.", kind="string",
                     default="Application menu"),
        AttributeDoc(name="active-item", description="Key (id, value or label) of the open menu; set it to open a menu, remove it to close. Written by the component.",
                     kind="string", values=["File", "Edit"]),
        AttributeDoc(name="compact", description="Smaller bar height and item padding.", kind="boolean"),
        AttributeDoc(name="disabled", description="Disables every top-level item: the bar leaves the tab order and ignores clicks and keys.",
                     kind="boolean"),
    ],
    events=[
        ("mj-menubar-open", "A dropdown opened.", "{ item: Element, menuId: string }"),
        ("mj-menubar-close", "A dropdown closed.", "{ item: Element, menuId: string }"),
        ("mj-menubar-select", "An entry was chosen; the menu closes and focus returns to the bar.",
         "{ item: Element, menuItem: Element, value: string, path: [menuLabel, entryLabel] }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>File and Edit menus from a hidden definition. Click or use the keyboard "
                "(<kbd>ArrowDown</kbd> opens, <kbd>ArrowRight</kbd> switches menus); the line "
                "below shows the last <code>mj-menubar-select</code>.</p>"
            ),
            html=(
                '<mj-menubar id="app-menu" label="Application menu">\n'
                '  <div label="File">\n'
                '    <span data-menu-item value="new">New</span>\n'
                '    <span data-menu-item value="open">Open</span>\n'
                '    <span data-menu-item value="save">Save</span>\n'
                '  </div>\n'
                '  <div label="Edit">\n'
                '    <span data-menu-item value="cut">Cut</span>\n'
                '    <span data-menu-item value="copy">Copy</span>\n'
                '    <span data-menu-item value="paste">Paste</span>\n'
                '  </div>\n'
                '</mj-menubar>\n'
                '<p class="last">Last command: <output id="last-command">none</output></p>'
            ),
            css=".last { margin: var(--mj-space-4); color: var(--mj-text-muted); }\n",
            script=(
                'document.getElementById("app-menu").addEventListener("mj-menubar-select", (event) => {\n'
                '  document.getElementById("last-command").textContent =\n'
                '    event.detail.path.join(" › ") + " (value " + event.detail.value + ")"\n'
                '})\n'
            ),
            height=240,
        ),
        ComponentExample(
            key="full-menus",
            title="Separators, disabled items, list markup",
            description=(
                "<p>Four menus written three ways (<code>data-menu-item</code>, <code>ul</code> / "
                "<code>li</code>, <code>role=\"menuitem\"</code>), with <code>hr</code> and "
                "<code>data-menu-separator</code> separators, disabled entries and a disabled Help "
                "menu that never opens.</p>"
            ),
            html=(
                '<mj-menubar label="Document editor">\n'
                '  <div label="File">\n'
                '    <span data-menu-item value="new">New document</span>\n'
                '    <span data-menu-item value="open">Open&hellip;</span>\n'
                '    <span data-menu-separator></span>\n'
                '    <span data-menu-item value="export-pdf">Export as PDF</span>\n'
                '    <span data-menu-item value="print" disabled>Print</span>\n'
                '  </div>\n'
                '  <ul label="Edit">\n'
                '    <li value="undo">Undo</li>\n'
                '    <li value="redo" disabled>Redo</li>\n'
                '    <hr>\n'
                '    <li value="find">Find and replace</li>\n'
                '  </ul>\n'
                '  <div label="View">\n'
                '    <span role="menuitem" value="outline">Show outline</span>\n'
                '    <span role="menuitem" value="ruler">Show ruler</span>\n'
                '    <span role="separator"></span>\n'
                '    <span role="menuitem" value="full-screen">Full screen</span>\n'
                '  </div>\n'
                '  <div label="Help" disabled>\n'
                '    <span data-menu-item value="docs">Documentation</span>\n'
                '  </div>\n'
                '</mj-menubar>'
            ),
            css="mj-menubar { margin: var(--mj-space-4); }\n",
            script=(
                'document.querySelector("mj-menubar").addEventListener("mj-menubar-select", (event) => {\n'
                '  mjSandbox.log("chosen", { path: event.detail.path, value: event.detail.value,\n'
                '                            entry: event.detail.menuItem.localName })\n'
                '})\n'
            ),
            height=280,
        ),
        ComponentExample(
            key="active-item",
            title="Opening from script, compact",
            description=(
                "<p>The buttons set and remove <code>active-item</code> to open and close a menu "
                "(focus stays on the button). The bar is <code>compact</code>.</p>"
            ),
            html=(
                '<div class="buttons">\n'
                '  <button type="button" data-open="view">Open View</button>\n'
                '  <button type="button" data-open="tools">Open Tools</button>\n'
                '  <button type="button" data-open="">Close</button>\n'
                '</div>\n'
                '<mj-menubar id="compact-menu" compact label="Workspace menu">\n'
                '  <div id="view" label="View">\n'
                '    <span data-menu-item value="zoom-in">Zoom in</span>\n'
                '    <span data-menu-item value="zoom-out">Zoom out</span>\n'
                '  </div>\n'
                '  <div id="tools" label="Tools">\n'
                '    <span data-menu-item value="spelling">Spelling</span>\n'
                '    <span data-menu-item value="word-count">Word count</span>\n'
                '  </div>\n'
                '</mj-menubar>'
            ),
            css=(
                ".buttons { display: flex; gap: var(--mj-space-2); margin: var(--mj-space-4); }\n"
                "mj-menubar { margin-inline: var(--mj-space-4); }\n"
            ),
            script=(
                'const menu = document.getElementById("compact-menu")\n'
                'document.querySelector(".buttons").addEventListener("click", (event) => {\n'
                '  const key = event.target.dataset.open\n'
                '  if (key === undefined) { return }\n'
                '  if (key === "") { menu.removeAttribute("active-item") } else { menu.setAttribute("active-item", key) }\n'
                '})\n'
            ),
            height=260,
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>Custom properties set the bar height, colours and item padding; <code>::part(menu)</code> styles the dropdowns.</p>",
            html=(
                '<mj-menubar label="Styled menu">\n'
                '  <div label="Project">\n'
                '    <span data-menu-item value="settings">Settings</span>\n'
                '    <span data-menu-item value="members">Members</span>\n'
                '  </div>\n'
                '  <div label="Share">\n'
                '    <span data-menu-item value="link">Copy link</span>\n'
                '    <span data-menu-item value="invite">Invite people</span>\n'
                '  </div>\n'
                '</mj-menubar>'
            ),
            css=(
                "mj-menubar {\n"
                "  margin: var(--mj-space-4);\n"
                "  --mj-menubar-height: 44px;\n"
                "  --mj-menubar-bg: var(--mj-bg-subtle);\n"
                "  --mj-menubar-border: var(--mj-accent);\n"
                "  --mj-menubar-item-padding: 0 var(--mj-space-4);\n"
                "  --mj-menubar-item-hover-bg: var(--mj-bg-muted);\n"
                "}\n"
                "mj-menubar::part(menu) { border-radius: var(--mj-radius-lg); }\n"
            ),
            height=220,
        ),
    ],
    slots=[
        ("", "The hidden menu definition: one element per top-level menu with a `label`, entries inside.",
         '<div label="Help"><span data-menu-item value="docs">Documentation</span>'
         '<span data-menu-item value="about">About</span></div>'),
    ],
    properties=[
        ("items", "Element[], read-only. The top-level definition elements."),
        ("openMenu", "HTMLElement | null, read-only. The open dropdown (`role=\"menu\"`) in the shadow root."),
    ],
    methods=[],
    parts=[
        ("root", "The `role=\"menubar\"` bar."),
        ("item", "Each top-level menu button."),
        ("menu", "Each dropdown list."),
    ],
    css_properties=[
        ("--mj-menubar-height", "Bar height (default `--mj-control-height-md`; `--mj-control-height-sm` when compact)."),
        ("--mj-menubar-bg", "Bar background (default `--mj-surface`)."),
        ("--mj-menubar-border", "Bar border colour (default `--mj-border`)."),
        ("--mj-menubar-item-padding", "Top-level item padding (default `0 var(--mj-space-3)`)."),
        ("--mj-menubar-item-hover-bg", "Hovered top-level item background (default `--mj-bg-muted`)."),
        ("--mj-menubar-item-active-bg", "Background of the item whose menu is open (default `--mj-bg-muted`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-status-bar
# ---------------------------------------------------------------------------

STATUS_BAR = ComponentDoc(
    tag="mj-status-bar",
    title="Status Bar",
    group="productivity",
    summary="Sticky bottom strip with start, centre and end sections, clickable items, severity tints and a polite announcer.",
    description=(
        "<p><code>&lt;mj-status-bar&gt;</code> lays out short status items in three sections: "
        "<code>slot=\"start\"</code>, the default slot (centre, which grows) and "
        "<code>slot=\"end\"</code>. It is <code>position: sticky</code> at the bottom of its "
        "scroll container. The bar is a labelled <code>role=\"group\"</code>, deliberately not "
        "a live region, so changing an item's text is not read out; call "
        "<code>announce()</code> for messages that should be spoken (polite ones through the "
        "bar's hidden status region, assertive ones through the page announcer).</p>"
        "<p>Items with the <code>interactive</code> attribute fire "
        "<code>mj-status-item-click</code>; a non-button element also gets "
        "<code>role=\"button\"</code>, a tab stop and <kbd>Enter</kbd>/<kbd>Space</kbd> "
        "activation. Items with <code>severity</code> (<code>info</code>, "
        "<code>success</code>, <code>warning</code>, <code>error</code>) get a tinted "
        "background. Inside <code>mj-app-shell</code> the shell provides the "
        "<code>contentinfo</code> landmark around it.</p>"
    ),
    how_to_use=(
        "<p>Slot short items into the three sections. Add <code>interactive</code> and a "
        "<code>value</code> (default: the item's text) to items that act, and listen for "
        "<code>mj-status-item-click</code>; its <code>itemId</code> is the item's id. Use "
        "<code>severity</code> for state. <code>variant=\"minimal\"</code> keeps only the start "
        "section. Call <code>announce(message, \"polite\" | \"assertive\")</code> to speak a "
        "message; repeated messages are spoken again.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the bar's group.", kind="string",
                     default="Status bar"),
        AttributeDoc(name="variant", description="`minimal` hides the centre and end sections.", kind="enum",
                     values=["minimal"]),
        AttributeDoc(name="hidden", description="Hides the bar (announcements are then not heard).", kind="boolean"),
    ],
    events=[
        ("mj-status-item-click", "An interactive item was clicked or activated with Enter / Space.",
         "{ itemId: string, value: string }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>An editor status bar: cursor position at the start, state in the centre, and a success-tinted save state at the end.</p>",
            html=(
                '<mj-status-bar label="Application status">\n'
                '  <span slot="start">Ln 12, Col 8</span>\n'
                '  <span>Ready</span>\n'
                '  <span slot="end" severity="success">Saved</span>\n'
                '</mj-status-bar>'
            ),
        ),
        ComponentExample(
            key="interactive",
            title="Interactive items",
            description=(
                "<p>The branch, indentation and encoding items are <code>interactive</code>: "
                "click them or Tab to them and press <kbd>Enter</kbd>. The script cycles the "
                "indentation and updates the item text.</p>"
            ),
            html=(
                '<mj-status-bar id="editor-status" label="Editor status">\n'
                '  <span slot="start" id="branch" interactive value="main">&#9095; main</span>\n'
                '  <span slot="start">0 problems</span>\n'
                '  <span>Ln 48, Col 2</span>\n'
                '  <span slot="end" id="indent" interactive value="2">Spaces: 2</span>\n'
                '  <button slot="end" type="button" id="encoding" interactive value="utf-8">UTF-8</button>\n'
                '</mj-status-bar>'
            ),
            script=(
                'const bar = document.getElementById("editor-status")\n'
                'const sizes = ["2", "4", "8"]\n'
                'bar.addEventListener("mj-status-item-click", (event) => {\n'
                '  if (event.detail.itemId === "indent") {\n'
                '    const item = document.getElementById("indent")\n'
                '    const next = sizes[(sizes.indexOf(item.getAttribute("value")) + 1) % sizes.length]\n'
                '    item.setAttribute("value", next)\n'
                '    item.textContent = "Spaces: " + next\n'
                '    bar.announce("Indentation set to " + next + " spaces")\n'
                '  }\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="severity",
            title="Severity and minimal",
            description=(
                "<p>Each <code>severity</code> tint, then a <code>variant=\"minimal\"</code> bar that "
                "shows only its start section.</p>"
            ),
            html=(
                '<mj-status-bar label="Build status">\n'
                '  <span slot="start" severity="info">Indexing 1,204 files</span>\n'
                '  <span severity="warning">3 warnings</span>\n'
                '  <span severity="error">1 test failed</span>\n'
                '  <span slot="end" severity="success">Deployed 4.2.0</span>\n'
                '</mj-status-bar>\n'
                '<mj-status-bar variant="minimal" label="Sync status">\n'
                '  <span slot="start">Synced 2 minutes ago</span>\n'
                '  <span>Hidden in minimal</span>\n'
                '  <span slot="end">Hidden in minimal</span>\n'
                '</mj-status-bar>'
            ),
            css="mj-status-bar + mj-status-bar { margin-block-start: var(--mj-space-4); }\n",
        ),
        ComponentExample(
            key="announce",
            title="Announcements",
            description=(
                "<p>The buttons change the save item and call <code>announce()</code>: a polite "
                "message after saving, an assertive one when saving fails. The item text changes "
                "alone are never read out.</p>"
            ),
            html=(
                '<div class="page">\n'
                '  <div class="actions">\n'
                '    <button type="button" id="save">Save</button>\n'
                '    <button type="button" id="fail">Save (fails)</button>\n'
                '  </div>\n'
                '  <mj-status-bar id="doc-status" label="Document status">\n'
                '    <span slot="start">Quarterly report.docx</span>\n'
                '    <span id="words">2,418 words</span>\n'
                '    <span slot="end" id="save-state" severity="warning">Unsaved changes</span>\n'
                '  </mj-status-bar>\n'
                '</div>'
            ),
            css=".actions { display: flex; gap: var(--mj-space-2); padding: var(--mj-space-4); }\n",
            script=(
                'const bar = document.getElementById("doc-status")\n'
                'const state = document.getElementById("save-state")\n'
                'document.getElementById("save").addEventListener("click", () => {\n'
                '  state.setAttribute("severity", "success")\n'
                '  state.textContent = "Saved at " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })\n'
                '  bar.announce("Document saved", "polite")\n'
                '  mjSandbox.log("announce", { message: "Document saved", politeness: "polite" })\n'
                '})\n'
                'document.getElementById("fail").addEventListener("click", () => {\n'
                '  state.setAttribute("severity", "error")\n'
                '  state.textContent = "Save failed"\n'
                '  bar.announce("Saving failed: you are offline", "assertive")\n'
                '  mjSandbox.log("announce", { message: "Saving failed: you are offline", politeness: "assertive" })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>A taller, accent-coloured bar through the custom properties; <code>::part(section-end)</code> adds a divider.</p>",
            html=(
                '<mj-status-bar label="Player status">\n'
                '  <span slot="start">Now playing: Episode 12</span>\n'
                '  <span>12:40 / 48:05</span>\n'
                '  <span slot="end">1.5&times;</span>\n'
                '</mj-status-bar>'
            ),
            css=(
                "mj-status-bar {\n"
                "  --mj-statusbar-height: 32px;\n"
                "  --mj-statusbar-bg: var(--mj-accent);\n"
                "  --mj-statusbar-color: var(--mj-text-on-accent);\n"
                "  --mj-statusbar-border: transparent;\n"
                "  --mj-statusbar-font-size: var(--mj-font-size-sm);\n"
                "  --mj-statusbar-item-padding: 0 var(--mj-space-3);\n"
                "}\n"
                "mj-status-bar::part(section-end) { border-inline-start: 1px solid currentColor; }\n"
            ),
        ),
    ],
    slots=[
        ("start", "Items at the inline start. Item attributes: `interactive` (clickable; role=button and a tab stop for non-buttons), `value` (reported on click, default its text), `severity` (info | success | warning | error tint).",
         '<span interactive value="main">main</span>'),
        ("", "Centre items (the section grows); same item attributes.", "<span>Ready</span>"),
        ("end", "Items pushed to the inline end; same item attributes.", '<span severity="success">Saved</span>'),
    ],
    properties=[
        ("items", "Element[], read-only. The slotted items of the start, centre and end sections, in that order."),
    ],
    methods=[
        ("announce(message, politeness)", "Speaks `message`; `politeness` is `polite` (default, through the bar's status region) or `assertive` (through the page announcer)."),
    ],
    parts=[
        ("root", "The bar (`role=\"group\"`)."),
        ("section-start", "The start section."),
        ("section-center", "The centre section."),
        ("section-end", "The end section."),
        ("live-region", "The visually hidden polite status region."),
    ],
    css_properties=[
        ("--mj-statusbar-height", "Bar height (default 22px)."),
        ("--mj-statusbar-bg", "Background (default `--mj-bg-subtle`)."),
        ("--mj-statusbar-border", "Top border colour (default `--mj-border`)."),
        ("--mj-statusbar-font-size", "Font size (default `--mj-font-size-xs`)."),
        ("--mj-statusbar-color", "Text colour (default `--mj-text-muted`)."),
        ("--mj-statusbar-item-padding", "Padding of each item (default `0 var(--mj-space-2)`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-app-shell
# ---------------------------------------------------------------------------

_SHELL_CSS = (
    "mj-app-shell { --mj-shell-height: 520px; border: 1px solid var(--mj-border); }\n"
    ".brand { font-weight: var(--mj-font-weight-bold); }\n"
    ".content { padding: var(--mj-space-4) var(--mj-space-5); }\n"
    ".content h1 { margin-block-start: 0; font-size: var(--mj-font-size-xl); }\n"
    ".tasks { list-style: none; margin: var(--mj-space-3) 0 0; padding: 0; }\n"
    ".tasks li { display: flex; gap: var(--mj-space-2); align-items: center; padding: var(--mj-space-2) var(--mj-space-1);\n"
    "            border-block-end: 1px solid var(--mj-border); }\n"
    ".details { padding: var(--mj-space-4); }\n"
    ".details h2 { margin-block-start: 0; font-size: var(--mj-font-size-md); }\n"
    ".details dl { display: grid; grid-template-columns: auto 1fr; gap: var(--mj-space-1) var(--mj-space-3); margin: 0; }\n"
    ".details dt { color: var(--mj-text-muted); }\n"
    ".details dd { margin: 0; }\n"
    ".hint { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
)

APP_SHELL = ComponentDoc(
    tag="mj-app-shell",
    title="App Shell",
    group="productivity",
    summary="Page-level application frame: app bar, dock, resizable navigation, main area (optionally split), inspector and status bar, with responsive drawers and F6 region cycling.",
    description=(
        "<p><code>&lt;mj-app-shell&gt;</code> is the outermost layout of an application. It "
        "places its slotted regions in a grid: <code>app-bar</code> across the top, an icon "
        "<code>dock</code> column, the navigation region (<code>workspace</code> and "
        "<code>nav</code> slots), the main region (<code>main</code> or the default slot, "
        "scrolling on its own), an optional second pane (<code>split</code> with the "
        "<code>split-secondary</code> slot), the <code>inspector</code>, and the "
        "<code>status-bar</code> along the bottom. Empty regions are left out. Each region gets "
        "its landmark (banner, navigation, main, complementary, contentinfo) unless the "
        "slotted content already is one, so a slotted <code>&lt;nav&gt;</code>, "
        "<code>&lt;main&gt;</code>, <code>&lt;aside&gt;</code>, <code>mj-app-bar</code> or "
        "<code>mj-side-nav</code> is not wrapped twice. The resize handles sit inside the main "
        "landmark the shell supplies; slot plain content into <code>main</code> to keep them "
        "there (a slotted <code>&lt;main&gt;</code> keeps its own landmark, and the handles are "
        "then outside every landmark). The host is "
        "<code>--mj-shell-height</code> tall (default <code>100dvh</code>).</p>"
        "<p>What the shell does for you:</p>"
        "<ul>"
        "<li><strong>Resizing.</strong> The navigation, the inspector and the split view have "
        "<code>role=\"separator\"</code> handles: drag them, or focus one and use "
        "<kbd>ArrowLeft</kbd>/<kbd>ArrowRight</kbd> (steps of <code>--mj-shell-split-step</code>, "
        "16px), <kbd>Home</kbd> and <kbd>End</kbd>. Navigation is 160-480px, the inspector "
        "200-640px, neither more than half the shell; the split ratio is 0.1-0.9. After a "
        "resize the size is stored in <code>localStorage</code> under "
        "<code>&lt;storage-key&gt;-nav-size</code>, <code>-inspector-size</code> and "
        "<code>-split-ratio</code> and restored on the next load, and "
        "<code>mj-shell-nav-resize</code> / <code>-inspector-resize</code> / "
        "<code>-split-resize</code> fire.</li>"
        "<li><strong>F6 cycling.</strong> <kbd>F6</kbd> and <kbd>Shift</kbd>+<kbd>F6</kbd> move "
        "focus between the visible regions (app bar, navigation, main, second pane, inspector, "
        "status bar) and announce the region; from the dock or a resize handle they move to the "
        "region beyond it.</li>"
        "<li><strong>Responsive drawers.</strong> When the shell itself is narrower than "
        "<code>--mj-shell-breakpoint-nav</code> (768px) it reflects <code>narrow</code>, closes "
        "the navigation and inspector, and shows them as modal drawers: focus moves in and is "
        "trapped, the rest is inert, <kbd>Escape</kbd> or the backdrop closes them and focus "
        "returns to the opener; a link clicked in the nav drawer closes it. Only one drawer is "
        "open at a time. Widening restores the wide-layout state. <code>nav-mode</code> is never "
        "rewritten.</li>"
        "<li><strong>Built-in nav toggle and skip link.</strong> A toggle button "
        "(<code>part=\"nav-toggle-button\"</code>, <code>aria-expanded</code>, "
        "<code>aria-controls</code>) appears at the start of the app bar whenever the "
        "navigation can be opened and closed: in the narrow layout and in the "
        "<code>collapsible</code> and <code>overlay</code> modes. A &ldquo;Skip to main "
        "content&rdquo; link is the first tab stop; it moves focus to the main region (the "
        "region is in the shadow root, so the link has no fragment URL). A link slotted into "
        "<code>skip-link</code> does the same unless its <code>href</code> names an element "
        "outside the main content.</li>"
        "</ul>"
        "<p>An earlier version of this page (finding WW-1093) documented resize handles, "
        "persisted panel sizes and F6 cycling that the shell did not implement. The shell now "
        "implements all three as described above, plus the split view, the built-in toggle and "
        "the skip link.</p>"
    ),
    how_to_use=(
        "<p>Make the shell the page's top-level element (or give it "
        "<code>--mj-shell-height</code> when embedded) and slot real components into the "
        "regions: an <code>mj-app-bar</code> in <code>app-bar</code>, an "
        "<code>mj-side-nav</code> or <code>&lt;nav&gt;</code> in <code>nav</code>, your page in "
        "<code>main</code>, details in <code>inspector</code> and an "
        "<code>mj-status-bar</code> in <code>status-bar</code>. Set <code>nav-open</code> and "
        "<code>inspector-open</code> for the wide-layout state (absent means closed), or call "
        "<code>toggleNav()</code> / <code>toggleInspector()</code> and listen for "
        "<code>mj-shell-nav-toggle</code> / <code>mj-shell-inspector-toggle</code>. "
        "<code>nav-mode=\"collapsible\"</code> keeps a 48px rail when the navigation is closed; "
        "<code>overlay</code> always uses the drawer. An <code>mj-app-bar</code> inside a shell "
        "that has navigation hands its own menu button to the shell; set "
        "<code>hide-nav-toggle</code> if you provide your own toggle. Initial sizes come from "
        "<code>nav-size</code> / <code>inspector-size</code> (plain pixel numbers) or the "
        "custom properties; a size the user stored under <code>storage-key</code> wins over the "
        "attribute at load, and a later change of the attribute applies. To see the narrow "
        "layout here, choose the 768 or 320 preview width.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="nav-open", description="Navigation open (wide layout); absent means closed. Updated by the toggle, drawers and breakpoint changes.",
                     kind="boolean"),
        AttributeDoc(name="inspector-open", description="Inspector open; absent means closed. Opening it in the narrow layout closes the nav drawer.",
                     kind="boolean"),
        AttributeDoc(name="nav-mode", description="`static`: a closed nav takes no space; `collapsible`: a closed nav is a 48px rail and the toggle is shown; `overlay`: the nav is always a modal drawer.",
                     kind="enum", values=["static", "collapsible", "overlay"], default="static"),
        AttributeDoc(name="nav-size", description="Initial navigation width in px (plain number, 160-480).", kind="number"),
        AttributeDoc(name="inspector-size", description="Initial inspector width in px (plain number, 200-640).", kind="number"),
        AttributeDoc(name="split", description="Splits the main region into two panes with a resize handle; the second shows the `split-secondary` slot.",
                     kind="boolean"),
        AttributeDoc(name="split-ratio", description="Share of the first pane, 0.1-0.9.", kind="number", default="0.5"),
        AttributeDoc(name="storage-key", description="Prefix of the localStorage keys for sizes; changing it switches to the sizes stored under the new prefix.",
                     kind="string", default="mj-app-shell"),
        AttributeDoc(name="nav-label", description="Name of the navigation landmark (when the shell provides it) and of the region in F6 announcements.",
                     kind="string", default="Primary navigation"),
        AttributeDoc(name="inspector-label", description="Name of the inspector landmark and region.", kind="string",
                     default="Inspector"),
        AttributeDoc(name="status-bar-label", description="Name of the status-bar landmark and region.", kind="string",
                     default="Status bar"),
        AttributeDoc(name="hide-nav-toggle", description="Hides the built-in nav toggle (when the page provides its own).",
                     kind="boolean"),
    ],
    events=[
        ("mj-shell-nav-toggle", "The navigation opened or closed, for any reason (toggle, drawer, breakpoint).",
         "{ open: boolean }"),
        ("mj-shell-inspector-toggle", "The inspector opened or closed.", "{ open: boolean }"),
        ("mj-shell-nav-resize", "A user resize of the navigation settled (200 ms); the size was stored.",
         "{ size: number }"),
        ("mj-shell-inspector-resize", "A user resize of the inspector settled; the size was stored.",
         "{ size: number }"),
        ("mj-shell-split-resize", "A user resize of the split view settled; the ratio was stored.",
         "{ ratio: number }"),
        ("mj-shell-main-scroll", "The main region scrolled (at most once per frame).",
         "{ scrollTop: number, scrollLeft: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Complete application shell",
            description=(
                "<p>An <code>mj-app-bar</code> (the banner), an <code>mj-side-nav</code>, a task list in "
                "<code>main</code> (a plain container: the shell supplies the main landmark, which "
                "also holds the resize handles), task details in the inspector and an "
                "<code>mj-status-bar</code>. Try: drag or arrow-key the handles beside the "
                "navigation and the inspector (sizes persist across reloads and the status bar "
                "shows them); press <kbd>F6</kbd> / <kbd>Shift</kbd>+<kbd>F6</kbd> to move between "
                "regions; use the menu button to collapse the navigation to a rail and "
                "&ldquo;Details&rdquo; to toggle the inspector. Choose the <strong>768</strong> or "
                "<strong>320</strong> preview width to see the narrow layout: both panels become "
                "drawers opened by the same buttons.</p>"
            ),
            html=(
                '<mj-app-shell id="shell" nav-open inspector-open nav-mode="collapsible"\n'
                '              storage-key="demo-projects" nav-label="Projects">\n'
                '  <mj-app-bar slot="app-bar">\n'
                '    <span slot="brand" class="brand">Acme Projects</span>\n'
                '    <mj-button slot="actions" id="details-toggle" variant="tertiary" size="sm">Details</mj-button>\n'
                '  </mj-app-bar>\n'
                '  <mj-side-nav slot="nav" mode="static" nav-label="Projects">\n'
                '    <a href="#launch" aria-current="page">Q4 launch</a>\n'
                '    <a href="#website">Website refresh</a>\n'
                '    <a href="#mobile">Mobile app 2.0</a>\n'
                '    <a href="#hiring">Hiring plan</a>\n'
                '  </mj-side-nav>\n'
                '  <div slot="main" class="content">\n'
                '    <h1 id="project-title">Q4 launch</h1>\n'
                '    <mj-toolbar label="Task actions">\n'
                '      <mj-button size="sm" variant="primary">New task</mj-button>\n'
                '      <mj-button size="sm" variant="secondary">Assign</mj-button>\n'
                '      <mj-button size="sm" variant="secondary">Archive</mj-button>\n'
                '    </mj-toolbar>\n'
                '    <ul class="tasks">\n'
                '      <li><input type="checkbox" aria-label="Done"> Finalise the changelog</li>\n'
                '      <li><input type="checkbox" aria-label="Done" checked> Book the launch webinar</li>\n'
                '      <li><input type="checkbox" aria-label="Done"> Update pricing page</li>\n'
                '      <li><input type="checkbox" aria-label="Done"> Brief customer support</li>\n'
                '    </ul>\n'
                '    <p class="hint">Press F6 to move between regions.</p>\n'
                '  </div>\n'
                '  <aside slot="inspector" class="details" aria-label="Task details">\n'
                '    <h2>Finalise the changelog</h2>\n'
                '    <dl>\n'
                '      <dt>Owner</dt><dd>Priya Natarajan</dd>\n'
                '      <dt>Due</dt><dd>14 November</dd>\n'
                '      <dt>Status</dt><dd><mj-chip size="sm">In review</mj-chip></dd>\n'
                '    </dl>\n'
                '  </aside>\n'
                '  <mj-status-bar slot="status-bar" label="Workspace status">\n'
                '    <span slot="start" severity="success">Synced</span>\n'
                '    <span id="sizes">Drag a handle to resize</span>\n'
                '    <span slot="end" id="layout-state">Wide layout</span>\n'
                '  </mj-status-bar>\n'
                '</mj-app-shell>'
            ),
            css=_SHELL_CSS + "#shell { --mj-shell-nav-width: 200px; --mj-shell-inspector-width: 260px; }\n",
            script=(
                'const shell = document.getElementById("shell")\n'
                'const sizes = document.getElementById("sizes")\n'
                'const layout = document.getElementById("layout-state")\n'
                'document.getElementById("details-toggle").addEventListener("click", () => shell.toggleInspector())\n'
                '\n'
                '/* Navigation: mark the chosen project and show it in main. */\n'
                'shell.querySelector("mj-side-nav").addEventListener("click", (event) => {\n'
                '  const link = event.target.closest("a")\n'
                '  if (link === null) { return }\n'
                '  event.preventDefault()\n'
                '  shell.querySelectorAll("mj-side-nav a").forEach((a) => a.removeAttribute("aria-current"))\n'
                '  link.setAttribute("aria-current", "page")\n'
                '  document.getElementById("project-title").textContent = link.textContent\n'
                '})\n'
                '\n'
                'shell.addEventListener("mj-shell-nav-resize", (event) => { sizes.textContent = "Navigation " + event.detail.size + "px" })\n'
                'shell.addEventListener("mj-shell-inspector-resize", (event) => { sizes.textContent = "Inspector " + event.detail.size + "px" })\n'
                'function showLayout() { layout.textContent = shell.narrow ? "Narrow layout (drawers)" : "Wide layout" }\n'
                'new ResizeObserver(showLayout).observe(shell)\n'
                'showLayout()\n'
            ),
            height=540,
        ),
        ComponentExample(
            key="split-dock",
            title="Dock, workspace and split view",
            description=(
                "<p>An icon <code>dock</code>, a <code>workspace</code> switcher above the "
                "navigation, and <code>split</code> with <code>split-ratio=\"0.55\"</code>: the "
                "main region shows a document and <code>split-secondary</code> its preview. Drag "
                "the handle between the panes (or arrow-key it); <code>mj-shell-split-resize</code> "
                "reports the ratio. The main content is unwrapped default-slot content, so the "
                "shell supplies the <code>main</code> landmark (holding the resize handles), and "
                "the file list is a plain container, so the shell supplies one navigation landmark "
                "(named by <code>nav-label</code>) around both the workspace switcher and the "
                "files.</p>"
            ),
            html=(
                '<mj-app-shell id="editor-shell" nav-open split split-ratio="0.55" nav-size="200"\n'
                '              storage-key="demo-editor" nav-label="Files">\n'
                '  <header slot="app-bar" class="bar"><span class="brand">Docs editor</span></header>\n'
                '  <nav slot="dock" class="dock" aria-label="Tools">\n'
                '    <button type="button" aria-label="Files" aria-pressed="true">&#128196;</button>\n'
                '    <button type="button" aria-label="Search">&#128269;</button>\n'
                '    <button type="button" aria-label="Settings">&#9881;</button>\n'
                '  </nav>\n'
                '  <div slot="workspace" class="workspace">\n'
                '    <label>Workspace <select><option>Product docs</option><option>Internal wiki</option></select></label>\n'
                '  </div>\n'
                '  <div slot="nav" class="files">\n'
                '    <a href="#intro" aria-current="page">introduction.md</a>\n'
                '    <a href="#install">installation.md</a>\n'
                '    <a href="#faq">faq.md</a>\n'
                '  </div>\n'
                '  <div class="content">\n'
                '    <h1>introduction.md</h1>\n'
                '    <textarea aria-label="Markdown source" rows="10"># Welcome\n\nThis guide explains **how to install** the toolkit.</textarea>\n'
                '  </div>\n'
                '  <div slot="split-secondary" class="content">\n'
                '    <h1>Welcome</h1>\n'
                '    <p>This guide explains <strong>how to install</strong> the toolkit.</p>\n'
                '  </div>\n'
                '  <mj-status-bar slot="status-bar" label="Editor status">\n'
                '    <span slot="start">Markdown</span>\n'
                '    <span id="ratio">Split 55%</span>\n'
                '  </mj-status-bar>\n'
                '</mj-app-shell>'
            ),
            css=(
                _SHELL_CSS
                + ".bar { display: flex; align-items: center; min-block-size: 48px; padding-inline: var(--mj-space-3); }\n"
                ".dock { display: grid; align-content: start; gap: var(--mj-space-1); padding: var(--mj-space-1); }\n"
                ".dock button { inline-size: 40px; block-size: 40px; }\n"
                ".workspace { padding: var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }\n"
                ".files { display: grid; padding: var(--mj-space-2); }\n"
                ".files a { padding: var(--mj-space-1) var(--mj-space-2); }\n"
                ".content textarea { inline-size: 100%; font-family: var(--mj-font-mono, monospace); }\n"
            ),
            script=(
                'const shell = document.getElementById("editor-shell")\n'
                'shell.addEventListener("mj-shell-split-resize", (event) => {\n'
                '  document.getElementById("ratio").textContent = "Split " + Math.round(event.detail.ratio * 100) + "%"\n'
                '})\n'
                'shell.querySelector(".files").addEventListener("click", (event) => event.preventDefault())\n'
            ),
            height=540,
        ),
        ComponentExample(
            key="overlay",
            title="Overlay navigation, own toggle",
            description=(
                "<p><code>nav-mode=\"overlay\"</code> shows the navigation as a modal drawer at every "
                "width. The page hides the built-in toggle (<code>hide-nav-toggle</code>) and opens "
                "it from its own &ldquo;Menu&rdquo; button with <code>toggleNav()</code>; focus "
                "moves into the drawer, <kbd>Escape</kbd> closes it and returns focus to the "
                "button. A custom <code>skip-link</code> is the first tab stop: it points at the "
                "slotted <code>&lt;main id=\"article\"&gt;</code>, and the shell moves focus to "
                "the main region when it is activated (press <kbd>Tab</kbd>, then <kbd>Enter</kbd>).</p>"
            ),
            html=(
                '<mj-app-shell id="overlay-shell" nav-mode="overlay" hide-nav-toggle nav-label="Main menu">\n'
                '  <a slot="skip-link" href="#article" id="skip">Skip to the article</a>\n'
                '  <header slot="app-bar" class="bar">\n'
                '    <button type="button" id="menu">&#9776; Menu</button>\n'
                '    <span class="brand">Field notes</span>\n'
                '  </header>\n'
                '  <nav slot="nav" class="menu" aria-label="Main menu">\n'
                '    <a href="#latest">Latest notes</a>\n'
                '    <a href="#topics">Topics</a>\n'
                '    <a href="#archive">Archive</a>\n'
                '    <a href="#about">About</a>\n'
                '  </nav>\n'
                '  <main slot="main" class="content" id="article">\n'
                '    <h1>Notes from the field</h1>\n'
                '    <p>The menu opens as a drawer over this article at every width.</p>\n'
                '  </main>\n'
                '</mj-app-shell>'
            ),
            css=(
                _SHELL_CSS
                + ".bar { display: flex; align-items: center; gap: var(--mj-space-3); min-block-size: 48px; padding-inline: var(--mj-space-3); }\n"
                ".menu { display: grid; gap: var(--mj-space-1); padding: var(--mj-space-3); }\n"
                "#skip { position: absolute; inset-inline-start: -9999px; }\n"
                "#skip:focus { inset-inline-start: var(--mj-space-2); inset-block-start: var(--mj-space-2); z-index: 10; }\n"
            ),
            script=(
                'const shell = document.getElementById("overlay-shell")\n'
                'const menu = document.getElementById("menu")\n'
                'menu.addEventListener("click", () => shell.toggleNav())\n'
                'shell.addEventListener("mj-shell-nav-toggle", (event) => menu.setAttribute("aria-expanded", String(event.detail.open)))\n'
                'menu.setAttribute("aria-expanded", "false")\n'
                'shell.querySelector(".menu").addEventListener("click", (event) => event.preventDefault())\n'
            ),
            height=420,
        ),
        ComponentExample(
            key="breakpoint",
            title="Narrow layout via the breakpoint",
            description=(
                "<p><code>--mj-shell-breakpoint-nav: 1400px</code> puts this shell in the narrow "
                "layout at any preview width: <code>narrow</code> is reflected, both panels start "
                "closed even though the markup sets <code>nav-open</code> and "
                "<code>inspector-open</code>, and the built-in toggle opens the navigation drawer. "
                "&ldquo;Filters&rdquo; opens the inspector as a drawer from the end (which closes "
                "the navigation drawer).</p>"
            ),
            html=(
                '<mj-app-shell id="narrow-shell" nav-open inspector-open inspector-label="Filters">\n'
                '  <mj-app-bar slot="app-bar">\n'
                '    <span slot="brand" class="brand">Inventory</span>\n'
                '    <mj-button slot="actions" id="filters" size="sm" variant="secondary">Filters</mj-button>\n'
                '  </mj-app-bar>\n'
                '  <mj-side-nav slot="nav" mode="static" nav-label="Sections">\n'
                '    <a href="#stock" aria-current="page">Stock</a>\n'
                '    <a href="#orders">Orders</a>\n'
                '    <a href="#suppliers">Suppliers</a>\n'
                '  </mj-side-nav>\n'
                '  <main slot="main" class="content">\n'
                '    <h1>Stock</h1>\n'
                '    <p>1,204 items in 3 warehouses.</p>\n'
                '  </main>\n'
                '  <div slot="inspector" class="details">\n'
                '    <h2>Filters</h2>\n'
                '    <label><input type="checkbox" checked> In stock</label><br>\n'
                '    <label><input type="checkbox"> Low stock</label>\n'
                '    <p><button type="button" id="apply">Apply</button></p>\n'
                '  </div>\n'
                '  <mj-status-bar slot="status-bar" label="Inventory status"><span slot="start">Narrow layout</span></mj-status-bar>\n'
                '</mj-app-shell>'
            ),
            css=_SHELL_CSS + "#narrow-shell { --mj-shell-breakpoint-nav: 1400px; }\n",
            script=(
                'const shell = document.getElementById("narrow-shell")\n'
                'document.getElementById("filters").addEventListener("click", () => shell.toggleInspector())\n'
                'document.getElementById("apply").addEventListener("click", () => { shell.inspectorOpen = false })\n'
                'shell.querySelector("mj-side-nav").addEventListener("click", (event) => event.preventDefault())\n'
                'mjSandbox.log("state", { narrow: shell.narrow, navOpen: shell.navOpen, inspectorOpen: shell.inspectorOpen })\n'
            ),
            height=460,
        ),
    ],
    slots=[
        ("app-bar", "Top bar, e.g. an `mj-app-bar` (gets the banner landmark unless it is one).",
         '<header><strong>My application</strong></header>'),
        ("dock", "Narrow icon column at the inline start.",
         '<nav aria-label="Tools"><button type="button" aria-label="Files">&#128196;</button></nav>'),
        ("workspace", "Content above the navigation in the nav region (workspace switcher)."),
        ("nav", "Navigation, e.g. an `mj-side-nav` or `<nav>`.",
         '<nav aria-label="Sections"><a href="#one">One</a> <a href="#two">Two</a></nav>'),
        ("", "Main content when no `main` slot is used (the shell supplies the main landmark).",
         "<p>Main content supplied by the slot inspector.</p>"),
        ("main", "Main content. Plain content gets the shell's main landmark, which also holds the resize handles; a slotted `<main>` is used as the landmark instead (the handles are then outside every landmark).",
         "<main><h1>Overview</h1><p>Main content.</p></main>"),
        ("split-secondary", "Second pane of the main region (shown with `split`).",
         "<div><h2>Preview</h2><p>Second pane.</p></div>"),
        ("inspector", "Details panel at the inline end.",
         '<aside aria-label="Details"><h2>Details</h2><p>Selected item.</p></aside>'),
        ("status-bar", "Bottom strip, e.g. an `mj-status-bar` (gets the contentinfo landmark).",
         '<mj-status-bar><span slot="start">Ready</span></mj-status-bar>'),
        ("skip-link", "Replaces the built-in \"Skip to main content\" link. The shell moves focus to the main region when it is activated, unless its `href` names an element outside the main content (or another page) or a listener called `preventDefault()`.",
         '<a href="#">Skip to content</a>'),
        ("nav-toggle-icon", "Icon of the built-in nav toggle (default a hamburger).",
         '<span aria-hidden="true">&#9776;</span>'),
    ],
    properties=[
        ("navOpen", "boolean. Reflects `nav-open`; set `true` / `false` to open or close."),
        ("inspectorOpen", "boolean. Reflects `inspector-open`."),
        ("narrow", "boolean, read-only. True while the narrow (drawer) layout is active; the shell also reflects it as the `narrow` attribute (for styling, do not set it)."),
        ("navToggleable", "boolean, read-only. True when the shell has navigation that can be opened and closed right now (narrow layout, or `nav-mode` overlay / collapsible): where the built-in toggle is offered."),
        ("mainRegion", "HTMLElement, read-only. The scrolling main region in the shadow root."),
        ("navPanel", "Element | null, read-only. The first element slotted into `nav`."),
        ("inspectorPanel", "Element | null, read-only. The first element slotted into `inspector`."),
    ],
    methods=[
        ("toggleNav()", "Opens or closes the navigation (a drawer in the narrow and overlay layouts)."),
        ("toggleInspector()", "Opens or closes the inspector."),
        ("focusMain()", "Moves focus to the main region."),
    ],
    parts=[
        ("skip-link", "The built-in skip link."),
        ("app-bar", "The app-bar region."),
        ("nav-toggle-button", "The built-in navigation toggle."),
        ("dock", "The dock column."),
        ("nav", "The navigation region."),
        ("main", "The main region."),
        ("split-secondary", "The second pane."),
        ("split-handle", "Each resize separator (navigation, panes, inspector)."),
        ("inspector", "The inspector region."),
        ("status-bar", "The status-bar region."),
        ("backdrop", "The backdrop behind an open drawer."),
    ],
    css_properties=[
        ("--mj-shell-height", "Height of the shell (default 100dvh)."),
        ("--mj-shell-breakpoint-nav", "Shell width below which the narrow drawer layout is used (default 768px; px, rem or em)."),
        ("--mj-shell-nav-width", "Navigation width when no size is set or stored (default 240px)."),
        ("--mj-shell-inspector-width", "Inspector width when no size is set or stored (default 320px)."),
        ("--mj-shell-dock-width", "Dock and collapsed-rail width (default 48px)."),
        ("--mj-shell-split-step", "Arrow-key step of the resize handles (default 16px)."),
        ("--mj-shell-split-handle-size", "Half the hit area of a resize handle (default 4px)."),
        ("--mj-shell-bg", "Shell background (default `--mj-bg`)."),
        ("--mj-shell-appbar-bg", "App-bar region background (default `--mj-surface`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-search-results
# ---------------------------------------------------------------------------

_SEARCH_DOCS_SCRIPT = r'''const DOCS = [
  { id: "button", title: "Button component", url: "/docs/components/button", category: "Components", date: "2026-10-02",
    snippet: "The button component triggers an action. Use the primary variant for the main action of a view." },
  { id: "card", title: "Card component", url: "/docs/components/card", category: "Components", date: "2026-09-18",
    snippet: "A card component groups related content and actions about a single subject." },
  { id: "dialog", title: "Dialog component", url: "/docs/components/dialog", category: "Overlays", date: "2026-08-30",
    snippet: "The dialog component presents modal content above the page and traps focus until it closes." },
  { id: "tokens", title: "Design tokens", url: "/docs/foundations/tokens", category: "Foundations", date: "2026-07-11",
    snippet: "Tokens name every colour, space and radius so each component follows the theme." },
  { id: "forms", title: "Building forms", url: "/docs/guides/forms", category: "Guides", date: "2026-06-24",
    snippet: "Form-associated components submit their value with the form and take part in validation." },
  { id: "a11y", title: "Accessibility checklist", url: "/docs/guides/accessibility", category: "Guides", date: "2026-05-02",
    snippet: "Every component exposes a role, an accessible name and a keyboard model; this checklist covers the rest." }
]
const MORE = Array.from({ length: 17 }, (_, index) => ({
  id: "release-" + (index + 1),
  title: "Release notes 4." + (17 - index),
  url: "/docs/releases/4-" + (17 - index),
  category: "Releases",
  date: new Date(2026, 9 - Math.floor(index / 2), 28 - index).toISOString().slice(0, 10),
  snippet: "Component fixes and new features shipped in release 4." + (17 - index) + "."
}))
const ALL = DOCS.concat(MORE)

/* Keep the preview on this page: a result link is reported, not followed. */
function stayOnPage(element) {
  element.addEventListener("click", (event) => {
    const link = event.composedPath().find((node) => node.classList && node.classList.contains("result-title"))
    if (link) {
      event.preventDefault()
    }
  })
}
'''

SEARCH_RESULTS = ComponentDoc(
    tag="mj-search-results",
    title="Search Results",
    group="productivity",
    summary="Ranked result list with a live count, term highlighting, skeletons, an empty state and three paging modes.",
    description=(
        "<p><code>&lt;mj-search-results&gt;</code> renders the items of its <code>results</code> "
        "array as a list of links: title, URL, snippet and a meta line "
        "(<code>category &middot; date</code>). A <code>role=\"status\"</code> count bar reads "
        "&ldquo;N results&rdquo; from <code>total-count</code> (never from the array length). "
        "Every field is shown as text; only the snippet is highlighted, with each word of "
        "<code>highlight-term</code> wrapped in <code>&lt;mark&gt;</code> (case-insensitive, "
        "longest match first). <code>loading</code> replaces the rows with three skeletons "
        "(while more results load in the <code>button</code> / <code>infinite</code> modes the "
        "rows stay and one skeleton row is added below them), "
        "and an empty list shows <code>empty-message</code>, <code>empty-suggestion</code> or "
        "the <code>empty</code> slot.</p>"
        "<p>The component never slices <code>results</code>; it shows every item it is given. "
        "Paging is either driven by the page or by a <code>dataSource</code>:</p>"
        "<ul>"
        "<li><code>load-mode=\"paginate\"</code> (default) shows Previous / Page X of Y / Next "
        "when <code>total-count</code> exceeds <code>page-size</code>; a click writes "
        "<code>page</code>, moves focus to the list and fires <code>mj-page-change</code>.</li>"
        "<li><code>load-mode=\"button\"</code> shows Load more while fewer than "
        "<code>total-count</code> results are present and fires <code>mj-load-more</code> "
        "(with the next page number); it hides after the last page.</li>"
        "<li><code>load-mode=\"infinite\"</code> fires <code>mj-load-more</code> when a sentinel "
        "after the last row scrolls into the viewport; set <code>loading</code> while fetching.</li>"
        "</ul>"
        "<p>With a <code>dataSource</code> the component fetches the page itself on first "
        "render, when <code>page</code> or <code>page-size</code> change and on Load more "
        "(appending; the Load more button stays in place, inert, until the batch arrives), sets "
        "<code>loading</code> during the request, writes <code>total-count</code> from the "
        "response, and fires <code>mj-results-error</code> (and shows an alert) when the request "
        "fails. A response without <code>total</code> is read as &ldquo;at least this "
        "many&rdquo;: a full page keeps Load more / Next available and the count shows "
        "&ldquo;N+ results&rdquo;; a short page ends paging.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>results</code> an array of <code>{ id, title, url, snippet, category?, "
        "date? }</code> and set <code>total-count</code>. A <code>date</code> may be a "
        "<code>YYYY-MM-DD</code> string (shown as that local day), a <code>Date</code> or any "
        "parseable date. Reassign the array to update it (<code>push()</code> does not "
        "re-render). Without a data source, answer <code>mj-page-change</code> by assigning "
        "that page's items, and <code>mj-load-more</code> by appending. Or assign "
        "<code>dataSource = { query({ offset, limit, page, pageSize }) }</code> returning "
        "(a promise of) <code>{ items, total? }</code>. Links navigate normally; to handle "
        "them in the page, call <code>preventDefault()</code> in a click listener on the host "
        "when the composed path contains the <code>.result-title</code> link "
        "(<code>mj-result-select</code> is not cancelable).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="total-count", description="Total number of matches: drives the count bar, the page count and Load more. Written by the component after each data-source response.",
                     kind="number", default="0"),
        AttributeDoc(name="highlight-term", description="Whitespace-separated words highlighted in each snippet.",
                     kind="string", values=["component", "button dialog"]),
        AttributeDoc(name="load-mode", description="How further results are requested.",
                     kind="enum", values=["paginate", "button", "infinite"], default="paginate"),
        AttributeDoc(name="page", description="Current page (1-based); written by Previous / Next.",
                     kind="number", default="1"),
        AttributeDoc(name="page-size", description="Results per page.", kind="number", default="10"),
        AttributeDoc(name="loading", description="Shows three skeleton rows instead of the results and disables paging. Set by the component during data-source requests.",
                     kind="boolean"),
        AttributeDoc(name="empty-message", description="Empty-state text.", kind="string", default="No results found."),
        AttributeDoc(name="empty-suggestion", description="Second line of the empty state, e.g. a hint to broaden the search.",
                     kind="string"),
        AttributeDoc(name="compact", description="Hides the snippet and meta lines and tightens the spacing.",
                     kind="boolean"),
    ],
    events=[
        ("mj-result-select", "A result title was clicked (not cancelable; the link still navigates).",
         "{ result: object, index: number }"),
        ("mj-page-change", "Previous or Next was activated; `page` is already updated.",
         "{ page: number, pageSize: number }"),
        ("mj-load-more", "Load more was clicked or the infinite sentinel became visible.",
         "{ page: number, pageSize: number }"),
        ("mj-results-error", "The data source rejected or threw; an alert is shown.", "{ error: any }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Six results with categories and dates; <code>highlight-term</code> marks "
                "&ldquo;component&rdquo; in the snippets. Clicking a title is reported as "
                "<code>mj-result-select</code> and kept on the page by the script.</p>"
            ),
            html='<mj-search-results id="results" total-count="6" highlight-term="component"></mj-search-results>',
            css="mj-search-results { max-inline-size: 44rem; margin: var(--mj-space-4); }\n",
            script=(
                _SEARCH_DOCS_SCRIPT
                + 'const results = document.getElementById("results")\n'
                'stayOnPage(results)\n'
                'results.results = DOCS\n'
            ),
        ),
        ComponentExample(
            key="paginate",
            title="Pages from a data source",
            description=(
                "<p>A <code>dataSource</code> serves 23 results, four per page, after a short delay: "
                "the component shows skeletons, fetches each page on Next / Previous and writes "
                "<code>total-count</code>. Tick &ldquo;Fail the next request&rdquo; to see the error "
                "state and <code>mj-results-error</code>.</p>"
            ),
            html=(
                '<label class="fail"><input type="checkbox" id="fail"> Fail the next request</label>\n'
                '<mj-search-results id="paged" page-size="4" highlight-term="release component"></mj-search-results>'
            ),
            css=(
                "mj-search-results { max-inline-size: 44rem; margin: var(--mj-space-4); }\n"
                ".fail { display: block; margin: var(--mj-space-4) var(--mj-space-4) 0; }\n"
            ),
            script=(
                _SEARCH_DOCS_SCRIPT
                + 'const paged = document.getElementById("paged")\n'
                'const fail = document.getElementById("fail")\n'
                'stayOnPage(paged)\n'
                'paged.dataSource = {\n'
                '  query({ offset, limit, page }) {\n'
                '    mjSandbox.log("query", { offset, limit, page })\n'
                '    return new Promise((resolve, reject) => setTimeout(() => {\n'
                '      if (fail.checked) {\n'
                '        fail.checked = false\n'
                '        reject(new Error("The search service is unavailable"))\n'
                '      } else {\n'
                '        resolve({ items: ALL.slice(offset, offset + limit), total: ALL.length })\n'
                '      }\n'
                '    }, 500))\n'
                '  }\n'
                '}\n'
            ),
        ),
        ComponentExample(
            key="load-more",
            title="Load more",
            description=(
                "<p><code>load-mode=\"button\"</code> without a data source: the script answers "
                "each <code>mj-load-more</code> by appending the next five results. The button "
                "disappears once all 23 are shown.</p>"
            ),
            html='<mj-search-results id="more" load-mode="button" page-size="5" total-count="23"></mj-search-results>',
            css="mj-search-results { max-inline-size: 44rem; margin: var(--mj-space-4); }\n",
            script=(
                _SEARCH_DOCS_SCRIPT
                + 'const more = document.getElementById("more")\n'
                'stayOnPage(more)\n'
                'more.results = ALL.slice(0, 5)\n'
                'more.addEventListener("mj-load-more", (event) => {\n'
                '  const start = more.results.length\n'
                '  more.results = more.results.concat(ALL.slice(start, start + event.detail.pageSize))\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="states",
            title="Loading, empty and compact",
            description=(
                "<p>Top: <code>loading</code> skeletons. Middle: the empty state from "
                "<code>empty-message</code> and <code>empty-suggestion</code>. Bottom: "
                "<code>compact</code> rows without snippet and meta, and a custom "
                "<code>empty</code> slot below it.</p>"
            ),
            html=(
                '<mj-search-results id="loading" loading total-count="12"></mj-search-results>\n'
                '<mj-search-results empty-message="No results for &ldquo;quarterly roadmap&rdquo;"\n'
                '                   empty-suggestion="Check the spelling or search all spaces."></mj-search-results>\n'
                '<mj-search-results id="compact" compact total-count="4"></mj-search-results>\n'
                '<mj-search-results>\n'
                '  <div slot="empty" class="empty">\n'
                '    <strong>Nothing matched.</strong>\n'
                '    <button type="button">Search the archive</button>\n'
                '  </div>\n'
                '</mj-search-results>'
            ),
            css=(
                "mj-search-results { display: block; max-inline-size: 44rem; margin: var(--mj-space-4); }\n"
                ".empty { display: flex; gap: var(--mj-space-3); align-items: center; }\n"
            ),
            script=(
                _SEARCH_DOCS_SCRIPT
                + 'const compact = document.getElementById("compact")\n'
                'stayOnPage(compact)\n'
                'compact.results = DOCS.slice(0, 4)\n'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>Custom properties recolour titles, URLs and highlights and widen the gap; <code>::part(result-item)</code> adds a card look.</p>",
            html='<mj-search-results id="styled" total-count="3" highlight-term="component tokens"></mj-search-results>',
            css=(
                "mj-search-results {\n"
                "  max-inline-size: 44rem;\n"
                "  margin: var(--mj-space-4);\n"
                "  --mj-results-gap: var(--mj-space-3);\n"
                "  --mj-results-title-color: var(--mj-text);\n"
                "  --mj-results-url-color: var(--mj-accent);\n"
                "  --mj-results-highlight-bg: var(--mj-accent);\n"
                "  --mj-results-highlight-color: var(--mj-text-on-accent);\n"
                "  --mj-results-count-size: var(--mj-font-size-xs);\n"
                "}\n"
                "mj-search-results::part(result-item) {\n"
                "  padding: var(--mj-space-3);\n"
                "  border: 1px solid var(--mj-border);\n"
                "  border-radius: var(--mj-radius-md);\n"
                "}\n"
            ),
            script=(
                _SEARCH_DOCS_SCRIPT
                + 'const styled = document.getElementById("styled")\n'
                'stayOnPage(styled)\n'
                'styled.results = [DOCS[0], DOCS[1], DOCS[3]]\n'
            ),
        ),
    ],
    slots=[
        ("empty", "Replaces the empty-state text when there are no results.",
         '<div><strong>Nothing matched.</strong> <button type="button">Search the archive</button></div>'),
    ],
    properties=[
        ("results", "object[]. The rows to show: `{ id, title, url, snippet, category?, date? }`. Setting re-renders and clears the error state; the getter returns the live array."),
        ("dataSource", "{ query({ offset, limit, page, pageSize }) } | null. Returns (a promise of) `{ items, total? }` (without `total`, a full page means more may follow); setting it fetches the current page."),
    ],
    methods=[],
    parts=[
        ("count-bar", "The live result count."),
        ("result-list", "The list of results."),
        ("result-item", "One result row."),
        ("result-title", "The title link."),
        ("result-url", "The URL line."),
        ("result-snippet", "The snippet (with `<mark>` highlights)."),
        ("result-meta", "The category and date line."),
        ("empty-state", "The empty-state row (holds the `empty` slot)."),
        ("error-state", "The alert shown when the data source fails."),
        ("pagination", "The Previous / Page X of Y / Next navigation."),
        ("load-more", "The Load more button."),
    ],
    css_properties=[
        ("--mj-results-gap", "Space between results (default `--mj-space-4`; `--mj-space-2` when compact)."),
        ("--mj-results-title-color", "Title link colour (default `--mj-accent`)."),
        ("--mj-results-url-color", "URL line colour (default `--mj-text-muted`)."),
        ("--mj-results-highlight-bg", "Highlight background (default `--mj-color-warning-surface`)."),
        ("--mj-results-highlight-color", "Highlight text colour (default `--mj-text`)."),
        ("--mj-results-count-size", "Count bar font size (default `--mj-font-size-sm`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-filter-panel
# ---------------------------------------------------------------------------

_FILTER_DATA_SCRIPT = r'''const DOCUMENTS = [
  { name: "Q4 roadmap.pdf", status: "active", type: "doc", owner: "alice", updated: 9 },
  { name: "Brand guidelines.pdf", status: "active", type: "doc", owner: "bob", updated: 30 },
  { name: "Launch banner.png", status: "draft", type: "img", owner: "bob", updated: 2 },
  { name: "Team offsite.jpg", status: "archived", type: "img", owner: "carmen", updated: 120 },
  { name: "Budget 2027.xlsx", status: "draft", type: "sheet", owner: "alice", updated: 1 },
  { name: "Hiring plan.xlsx", status: "active", type: "sheet", owner: "carmen", updated: 14 },
  { name: "Release notes 4.2.md", status: "active", type: "doc", owner: "dmitri", updated: 0 },
  { name: "Old logo.png", status: "archived", type: "img", owner: "dmitri", updated: 400 }
]
const count = (field, value) => DOCUMENTS.filter((doc) => doc[field] === value).length
const FILTER_CONFIG = [
  { id: "status", label: "Status", type: "checkbox", options: [
    { value: "active", label: "Active", count: count("status", "active") },
    { value: "draft", label: "Draft", count: count("status", "draft") },
    { value: "archived", label: "Archived", count: count("status", "archived") }
  ] },
  { id: "type", label: "Type", type: "radio", options: [
    { value: "doc", label: "Document", count: count("type", "doc") },
    { value: "img", label: "Image", count: count("type", "img") },
    { value: "sheet", label: "Spreadsheet", count: count("type", "sheet") }
  ] },
  { id: "owner", label: "Owner", type: "checkbox", options: [
    { value: "alice", label: "Alice Martin" }, { value: "bob", label: "Bob Lee" },
    { value: "carmen", label: "Carmen Ortiz" }, { value: "dmitri", label: "Dmitri Volkov" }
  ] }
]
const SORT_OPTIONS = [{ value: "updated", label: "Last updated" }, { value: "name", label: "Name" }]

/* Apply a filter-panel value to the documents. */
function matching(value) {
  const filters = value.filters || {}
  let rows = DOCUMENTS.filter((doc) => {
    const status = filters.status || []
    const owner = filters.owner || []
    return (status.length === 0 || status.includes(doc.status)) &&
           (owner.length === 0 || owner.includes(doc.owner)) &&
           (filters.type === undefined || filters.type === null || filters.type === doc.type)
  })
  const sort = value.sort || {}
  if (sort.field === "name") {
    rows = rows.slice().sort((a, b) => a.name.localeCompare(b.name))
  } else if (sort.field === "updated") {
    rows = rows.slice().sort((a, b) => a.updated - b.updated)
  }
  if (sort.direction === "desc") {
    rows = rows.reverse()
  }
  return rows
}
'''

FILTER_PANEL = ComponentDoc(
    tag="mj-filter-panel",
    title="Filter Panel",
    group="productivity",
    summary="Faceted filters with collapsible checkbox and radio groups, applied-filter chips, an optional sort control and a result count.",
    description=(
        "<p><code>&lt;mj-filter-panel&gt;</code> renders the groups of its "
        "<code>filterConfig</code>: each group has a header button (collapses the group, shows "
        "a &ldquo;N selected&rdquo; badge) and a list of checkboxes, or radio buttons for "
        "<code>type: \"radio\"</code>, with optional option counts. Every selection appears as "
        "a removable chip (&ldquo;Group: Option&rdquo;) above the groups, with a Clear all "
        "button. When <code>sortOptions</code> is not empty a sort select (always starting "
        "with &ldquo;Default&rdquo;) and an ascending / descending toggle appear. "
        "<code>total-count</code> adds a &ldquo;Showing N results&rdquo; status line.</p>"
        "<p><code>layout=\"sidebar\"</code> gives a fixed-width column "
        "(<code>--mj-filter-panel-width</code>); <code>layout=\"inline\"</code> lays the groups "
        "out side by side in a wrapping row (<code>role=\"group\"</code> instead of "
        "<code>complementary</code>). With <code>collapsible</code> a toggle button collapses "
        "the whole panel; it starts collapsed unless <code>open</code> is present. The panel "
        "is not form-associated: read <code>value</code> or listen for "
        "<code>mj-filter-change</code>.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>filterConfig = [{ id, label, type: \"checkbox\" | \"radio\", options: "
        "[{ value, label, count? }] }]</code> and, for sorting, <code>sortOptions = [{ value, "
        "label }]</code>. The state is <code>value = { sort: { field, direction: \"asc\" | "
        "\"desc\" }, filters: { [groupId]: array (checkbox) | scalar or null (radio) } }</code>; "
        "set it to restore a saved state (no event is fired). Option values keep their type "
        "and are matched by their string form. Every user change fires "
        "<code>mj-filter-change</code> with the whole value and the group that changed "
        "(<code>\"sort\"</code> or <code>\"clear\"</code> for those controls); keep "
        "<code>total-count</code> in step with your results. Clear all clears the filters "
        "but keeps the sort.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the panel and text of the collapse toggle.",
                     kind="string", default="Filters"),
        AttributeDoc(name="layout", description="`sidebar`: fixed-width column; `inline`: groups side by side. Absent: stacked full width.",
                     kind="enum", values=["sidebar", "inline"]),
        AttributeDoc(name="collapsible", description="Shows a toggle button that collapses the whole panel.",
                     kind="boolean"),
        AttributeDoc(name="open", description="Expanded state of a collapsible panel; written by the toggle. Without it a collapsible panel starts collapsed.",
                     kind="boolean"),
        AttributeDoc(name="total-count", description="Shows \"Showing N results\" at the bottom; remove it to hide the line.",
                     kind="number"),
        AttributeDoc(name="sort-label", description="Label of the sort select.", kind="string", default="Sort by"),
    ],
    events=[
        ("mj-filter-change", "Any user change: an option, the sort field or direction, a chip removal or Clear all.",
         "{ value: { sort: { field, direction }, filters: object }, changedGroup: string }"),
        ("mj-chip-remove", "An applied-filter chip was removed (fired before mj-filter-change).",
         "{ groupId: string, value: any }"),
        ("mj-filter-clear", "Clear all was activated (fired before mj-filter-change).", "{}"),
        ("mj-panel-toggle", "The collapsible panel was opened or closed.", "{ open: boolean }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Filtering a list",
            description=(
                "<p>A sidebar panel filters the document list next to it. Tick options, remove "
                "chips, choose a sort field and flip the direction; the script applies "
                "<code>event.detail.value</code> and updates <code>total-count</code>.</p>"
            ),
            html=(
                '<div class="layout">\n'
                '  <mj-filter-panel id="filters" label="Filters" layout="sidebar" total-count="8"></mj-filter-panel>\n'
                '  <ul id="documents" class="documents" aria-label="Documents"></ul>\n'
                '</div>'
            ),
            css=(
                ".layout { display: flex; gap: var(--mj-space-4); align-items: flex-start; padding: var(--mj-space-3); }\n"
                ".documents { flex: 1; margin: 0; padding: 0; list-style: none; }\n"
                ".documents li { padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }\n"
                ".documents small { color: var(--mj-text-muted); margin-inline-start: var(--mj-space-2); }\n"
            ),
            script=(
                _FILTER_DATA_SCRIPT
                + 'const panel = document.getElementById("filters")\n'
                'const list = document.getElementById("documents")\n'
                'function show(value) {\n'
                '  const rows = matching(value)\n'
                '  list.replaceChildren(...rows.map((doc) => {\n'
                '    const item = document.createElement("li")\n'
                '    const meta = document.createElement("small")\n'
                '    item.textContent = doc.name\n'
                '    meta.textContent = doc.status + ", updated " + doc.updated + " days ago"\n'
                '    item.append(meta)\n'
                '    return item\n'
                '  }))\n'
                '  panel.setAttribute("total-count", String(rows.length))\n'
                '}\n'
                'panel.filterConfig = FILTER_CONFIG\n'
                'panel.sortOptions = SORT_OPTIONS\n'
                'panel.addEventListener("mj-filter-change", (event) => show(event.detail.value))\n'
                'show(panel.value)\n'
            ),
        ),
        ComponentExample(
            key="inline",
            title="Inline layout",
            description="<p><code>layout=\"inline\"</code> places the groups side by side above content; resize the preview to see them wrap.</p>",
            html='<mj-filter-panel id="inline" layout="inline" label="Refine results" sort-label="Order by"></mj-filter-panel>',
            css="mj-filter-panel { margin: var(--mj-space-3); }\n",
            script=(
                _FILTER_DATA_SCRIPT
                + 'const panel = document.getElementById("inline")\n'
                'panel.filterConfig = FILTER_CONFIG\n'
                'panel.sortOptions = SORT_OPTIONS\n'
            ),
        ),
        ComponentExample(
            key="collapsible",
            title="Collapsible, preset value, slots",
            description=(
                "<p><code>collapsible open</code> with a restored <code>value</code> (two chips "
                "and a sort), a <code>header</code> slot and a <code>footer</code> slot whose "
                "button logs the current <code>value</code> and <code>appliedFilters</code>.</p>"
            ),
            html=(
                '<mj-filter-panel id="saved" label="Saved view filters" layout="sidebar" collapsible open total-count="3">\n'
                '  <p slot="header" class="hint">Saved view: <strong>My active work</strong></p>\n'
                '  <div slot="footer" class="footer">\n'
                '    <button type="button" id="apply">Apply filters</button>\n'
                '  </div>\n'
                '</mj-filter-panel>'
            ),
            css=(
                "mj-filter-panel { margin: var(--mj-space-3); }\n"
                ".hint { margin: 0 0 var(--mj-space-2); color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ".footer { padding-block-start: var(--mj-space-2); }\n"
            ),
            script=(
                _FILTER_DATA_SCRIPT
                + 'const panel = document.getElementById("saved")\n'
                'panel.filterConfig = FILTER_CONFIG\n'
                'panel.sortOptions = SORT_OPTIONS\n'
                'panel.value = { sort: { field: "updated", direction: "desc" }, filters: { status: ["active"], owner: ["alice"] } }\n'
                'document.getElementById("apply").addEventListener("click", () => {\n'
                '  mjSandbox.log("apply", { value: panel.value, applied: panel.appliedFilters.map((chip) => chip.label) })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>A narrower panel with wider group spacing and an accent count badge, set through the custom properties and parts.</p>",
            html='<mj-filter-panel id="styled" layout="sidebar" label="Filters"></mj-filter-panel>',
            css=(
                "mj-filter-panel {\n"
                "  margin: var(--mj-space-3);\n"
                "  --mj-filter-panel-width: 220px;\n"
                "  --mj-filter-group-gap: var(--mj-space-4);\n"
                "  --mj-filter-chips-gap: var(--mj-space-2);\n"
                "  --mj-filter-count-badge-bg: var(--mj-accent);\n"
                "}\n"
                "mj-filter-panel::part(group-header) { font-weight: var(--mj-font-weight-bold); }\n"
            ),
            script=(
                _FILTER_DATA_SCRIPT
                + 'const panel = document.getElementById("styled")\n'
                'panel.filterConfig = FILTER_CONFIG\n'
                'panel.value = { filters: { status: ["active", "draft"] } }\n'
            ),
        ),
    ],
    slots=[
        ("header", "Content above the panel toggle and the groups; stays visible when collapsed.",
         '<p>Saved view: <strong>My active work</strong></p>'),
        ("footer", "Content after the groups, e.g. an Apply button; stays visible when collapsed.",
         '<div><button type="button">Apply filters</button></div>'),
    ],
    properties=[
        ("filterConfig", "object[]. Groups `{ id, label, type: \"checkbox\" | \"radio\", options: [{ value, label, count? }] }`; any other type is a checkbox group. Setting does not reset `value`."),
        ("sortOptions", "object[]. `[{ value, label }]` for the sort select; while empty the sort control is hidden."),
        ("value", "object. `{ sort: { field, direction }, filters: { [groupId]: array | scalar | null } }`. Setting restores a state without an event; the getter returns the live state."),
        ("appliedFilters", "object[], read-only. One entry per chip: `{ groupId, label: \"Group: Option\", value }`."),
    ],
    methods=[],
    parts=[
        ("root", "The panel container."),
        ("panel-toggle", "The collapse toggle (shown with `collapsible`)."),
        ("chips-bar", "The applied-filter chips."),
        ("clear-all", "The Clear all button."),
        ("sort-control", "The sort row."),
        ("sort-select", "The sort field select."),
        ("sort-direction", "The ascending / descending toggle."),
        ("groups", "The container of all groups."),
        ("group", "One filter group."),
        ("group-header", "A group's header button."),
        ("group-body", "A group's option list."),
        ("result-count", "The \"Showing N results\" line."),
    ],
    css_properties=[
        ("--mj-filter-panel-width", "Width of the sidebar layout (default 280px)."),
        ("--mj-filter-group-gap", "Space between groups (default `--mj-space-2`)."),
        ("--mj-filter-chips-gap", "Space between chips (default `--mj-space-1`)."),
        ("--mj-filter-count-badge-bg", "Background of the \"N selected\" badge (default `--mj-bg-muted`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-query-builder
# ---------------------------------------------------------------------------

_QUERY_SCHEMA_SCRIPT = r'''const FIELDS = [
  { id: "name", label: "Customer name", type: "string" },
  { id: "orders", label: "Orders", type: "number" },
  { id: "signup", label: "Signed up", type: "date" },
  { id: "vip", label: "VIP", type: "boolean" },
  { id: "region", label: "Region", type: "select",
    options: [{ value: "emea", label: "Europe, Middle East, Africa" }, { value: "amer", label: "Americas" },
              { value: "apac", label: "Asia Pacific" }] }
]
'''

QUERY_BUILDER = ComponentDoc(
    tag="mj-query-builder",
    title="Query Builder",
    group="productivity",
    summary="Visual, form-associated editor for nested AND / OR condition groups with typed value editors.",
    description=(
        "<p><code>&lt;mj-query-builder&gt;</code> edits a tree of condition groups. Each group "
        "has an AND / OR toggle, its conditions and subgroups, and Add condition / Add group "
        "buttons (Add group only while the group is shallower than <code>max-depth</code>). "
        "Each condition picks a field from <code>fieldSchema</code>, an operator for that "
        "field's type, and a value in an editor that fits the type and the operator's arity: "
        "none (<em>is empty</em>, <em>is true</em>), a text, number or date input, a select or "
        "multi-select for fields with <code>options</code>, two inputs for <em>is between</em>, "
        "or a comma-separated list. <code>show-preview</code> adds the JSON of the tree.</p>"
        "<p>Default operators: string &mdash; equals, contains, starts with, ends with, is "
        "empty, is not empty; number &mdash; =, !=, &gt;, &lt;, &gt;=, &lt;=, is between, is "
        "empty; date &mdash; is, is before, is after, is between; boolean &mdash; is true, is "
        "false; select &mdash; is, is not, is any of. A field's own <code>operators</code> or "
        "an <code>operatorMap</code> replace them.</p>"
        "<p>The element is form-associated: under <code>name</code> it submits the tree as "
        "JSON. It is invalid while a condition is incomplete, and with <code>required</code> "
        "while the root has no condition. Incomplete conditions are marked only after the user "
        "edits them (or after <code>reportValidity()</code>). <code>readonly</code> and "
        "<code>disabled</code> disable every control.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>fieldSchema = [{ id, label, type, options?, operators? }]</code> with "
        "<code>type</code> one of <code>string</code>, <code>number</code>, <code>date</code>, "
        "<code>boolean</code>, <code>select</code> (or a custom type found in "
        "<code>operatorMap</code>); <code>options</code> are <code>[{ value, label }]</code>. "
        "Read or restore the tree through <code>value</code>: a group is <code>{ combinator: "
        "\"AND\" | \"OR\", rules: [...] }</code> and a condition <code>{ id, field, operator, "
        "value }</code>. <code>value</code> and the event details are copies, so changing them "
        "does not change the builder. <code>operatorMap</code> maps a type to entries that are "
        "operator strings or <code>{ id, label, arity }</code> with arity <code>0</code>, "
        "<code>1</code>, <code>2</code> or <code>\"list\"</code>. Listen for "
        "<code>mj-query-change</code> and <code>mj-query-valid</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the builder region.", kind="string",
                     default="Query builder"),
        AttributeDoc(name="show-preview", description="Shows the tree as formatted JSON below the editor.",
                     kind="boolean"),
        AttributeDoc(name="max-depth", description="Deepest subgroup level that can be added (root is 0; `0` allows no subgroups).",
                     kind="number", default="3"),
        AttributeDoc(name="add-rule-label", description="Text of the Add condition buttons.", kind="string",
                     default="Add condition"),
        AttributeDoc(name="add-group-label", description="Text of the Add group buttons.", kind="string",
                     default="Add group"),
        AttributeDoc(name="readonly", description="Disables every control; the tree stays visible.", kind="boolean"),
        AttributeDoc(name="disabled", description="Disables every control (a disabled fieldset does the same).",
                     kind="boolean"),
        AttributeDoc(name="name", description="Form field name; the tree is submitted as JSON.", kind="string"),
        AttributeDoc(name="required", description="Invalid until the root group has at least one condition.",
                     kind="boolean"),
    ],
    events=[
        ("mj-query-change", "A user edit changed the tree (combinator, add / remove, field, operator or value).",
         "{ value: QueryGroup }"),
        ("mj-query-valid", "Fired right after each mj-query-change.",
         "{ valid: boolean, errors: [{ ruleId: string, message: string }] }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Five field types with a starting condition and the JSON preview. Add "
                "conditions and a group, switch AND / OR, and watch <code>mj-query-change</code> "
                "and <code>mj-query-valid</code> in Events.</p>"
            ),
            html='<mj-query-builder id="query" label="Customer segment" show-preview></mj-query-builder>',
            css="mj-query-builder { margin: var(--mj-space-3); }\n",
            script=(
                _QUERY_SCHEMA_SCRIPT
                + 'const query = document.getElementById("query")\n'
                'query.fieldSchema = FIELDS\n'
                'query.value = { combinator: "AND", rules: [{ field: "orders", operator: ">", value: 5 }] }\n'
            ),
        ),
        ComponentExample(
            key="nested",
            title="Nested groups",
            description=(
                "<p>A restored two-level tree with a list operator and a between range. "
                "<code>max-depth=\"2\"</code> hides Add group inside the second level.</p>"
            ),
            html='<mj-query-builder id="nested" max-depth="2" show-preview></mj-query-builder>',
            css="mj-query-builder { margin: var(--mj-space-3); }\n",
            script=(
                _QUERY_SCHEMA_SCRIPT
                + 'const nested = document.getElementById("nested")\n'
                'nested.fieldSchema = FIELDS\n'
                'nested.value = {\n'
                '  combinator: "AND",\n'
                '  rules: [\n'
                '    { field: "region", operator: "is any of", value: ["emea", "apac"] },\n'
                '    { combinator: "OR", rules: [\n'
                '      { field: "vip", operator: "is true", value: null },\n'
                '      { field: "signup", operator: "is between", value: ["2026-01-01", "2026-06-30"] }\n'
                '    ] }\n'
                '  ]\n'
                '}\n'
            ),
        ),
        ComponentExample(
            key="form",
            title="In a form",
            description=(
                "<p><code>name=\"segment\" required</code> inside a form. Submit with no condition, "
                "or with an incomplete one, to see the validation; a valid submit shows the JSON "
                "the form receives.</p>"
            ),
            html=(
                '<form id="segment-form" class="segment-form">\n'
                '  <mj-query-builder name="segment" required label="Segment rules"></mj-query-builder>\n'
                '  <div class="row"><button type="submit">Save segment</button> <button type="reset">Reset</button></div>\n'
                '  <output id="payload"></output>\n'
                '</form>'
            ),
            css=(
                ".segment-form { display: grid; gap: var(--mj-space-3); margin: var(--mj-space-3); }\n"
                "output { font-family: var(--mj-font-mono, monospace); font-size: var(--mj-font-size-sm); overflow-wrap: anywhere; }\n"
            ),
            script=(
                _QUERY_SCHEMA_SCRIPT
                + 'const form = document.getElementById("segment-form")\n'
                'form.querySelector("mj-query-builder").fieldSchema = FIELDS\n'
                'form.addEventListener("submit", (event) => {\n'
                '  event.preventDefault()\n'
                '  const json = new FormData(form).get("segment")\n'
                '  document.getElementById("payload").textContent = json\n'
                '  mjSandbox.log("submitted", JSON.parse(json))\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="custom-operators",
            title="Custom operators and labels",
            description=(
                "<p>An <code>operatorMap</code> with labelled entries and arities, a field with its "
                "own <code>operators</code>, and renamed add buttons.</p>"
            ),
            html='<mj-query-builder id="custom" add-rule-label="Add rule" add-group-label="Add rule set" show-preview></mj-query-builder>',
            css="mj-query-builder { margin: var(--mj-space-3); }\n",
            script=(
                'const custom = document.getElementById("custom")\n'
                'custom.operatorMap = {\n'
                '  string: [{ id: "eq", label: "is exactly", arity: 1 }, { id: "like", label: "looks like", arity: 1 },\n'
                '           { id: "blank", label: "is blank", arity: 0 }],\n'
                '  number: [{ id: "lt", label: "is under", arity: 1 }, { id: "range", label: "is within", arity: 2 }]\n'
                '}\n'
                'custom.fieldSchema = [\n'
                '  { id: "title", label: "Ticket title", type: "string" },\n'
                '  { id: "age", label: "Age in days", type: "number" },\n'
                '  { id: "tags", label: "Tags", type: "string", operators: ["in", "not in"] }\n'
                ']\n'
                'custom.value = { combinator: "OR", rules: [\n'
                '  { field: "age", operator: "range", value: [3, 14] },\n'
                '  { field: "tags", operator: "in", value: ["billing", "outage"] }\n'
                '] }\n'
            ),
        ),
        ComponentExample(
            key="readonly",
            title="Read-only",
            description="<p><code>readonly</code> shows a saved query with every control disabled.</p>",
            html='<mj-query-builder id="locked" readonly label="Saved segment"></mj-query-builder>',
            css="mj-query-builder { margin: var(--mj-space-3); }\n",
            script=(
                _QUERY_SCHEMA_SCRIPT
                + 'const locked = document.getElementById("locked")\n'
                'locked.fieldSchema = FIELDS\n'
                'locked.value = { combinator: "AND", rules: [\n'
                '  { field: "name", operator: "starts with", value: "Acme" },\n'
                '  { field: "orders", operator: ">=", value: 10 }\n'
                '] }\n'
            ),
        ),
    ],
    slots=[],
    properties=[
        ("value", "QueryGroup. `{ combinator: \"AND\" | \"OR\", rules: [rule | group] }`, rule = `{ id, field, operator, value }`. The getter returns a copy; setting copies and normalises and fires no event."),
        ("fieldSchema", "object[]. `{ id, label?, type?, options?, operators? }`; type defaults to `string`."),
        ("operatorMap", "object | null. `{ [type]: (string | { id, label?, arity? })[] }`; replaces the default operators (missing types use `string`); `null` restores them. Reading it returns a copy: changing that copy changes nothing until it is assigned back."),
        ("form", "HTMLFormElement | null, read-only. The owning form."),
        ("validity", "ValidityState, read-only. `customError` while a condition is incomplete; `valueMissing` while a `required` builder has no condition."),
        ("validationMessage", "string, read-only. The current validation message."),
    ],
    methods=[
        ("checkValidity() -> boolean", "Runs constraint validation."),
        ("reportValidity() -> boolean", "Validates and marks every incomplete condition as invalid."),
    ],
    parts=[
        ("root", "The builder region."),
        ("group", "A condition group."),
        ("group-header", "A group's header row."),
        ("combinator", "The AND / OR toggle."),
        ("rule-row", "One condition row."),
        ("field-select", "The field select of a condition."),
        ("operator-select", "The operator select of a condition."),
        ("value-input", "A value editor (input or select)."),
        ("remove-rule", "A condition's remove button."),
        ("add-rule", "An Add condition button."),
        ("add-group", "An Add group button."),
        ("remove-group", "A subgroup's remove button."),
        ("preview", "The JSON preview (with `show-preview`)."),
    ],
    css_properties=[
        ("--mj-qb-group-border", "Group border colour (default `--mj-border`)."),
        ("--mj-qb-group-bg", "Group background (default `--mj-surface`)."),
        ("--mj-qb-rule-gap", "Space between the controls of a condition (default `--mj-space-2`)."),
        ("--mj-qb-row-gap", "Space between conditions (default `--mj-space-2`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-dropzone
# ---------------------------------------------------------------------------

_DROPZONE_ADD_SCRIPT = r'''/* Queue files as if the user had picked them in the file dialog. */
function pick(dropzone, files) {
  const transfer = new DataTransfer()
  files.forEach((file) => transfer.items.add(file))
  const input = dropzone.shadowRoot.querySelector("input[type=file]")
  input.files = transfer.files
  input.dispatchEvent(new Event("change"))
}
const sized = (name, type, bytes) => new File([new Uint8Array(bytes)], name, { type: type })
'''

DROPZONE = ComponentDoc(
    tag="mj-dropzone",
    title="Drop Zone",
    group="productivity",
    summary="Form-associated file drop target with a browse button, type, size and count checks, a file list and upload progress rows.",
    description=(
        "<p><code>&lt;mj-dropzone&gt;</code> accepts files dropped on its target (folders are "
        "expanded) or picked with the Browse button; the target itself is not a button. "
        "Each file is checked against <code>accept</code>, <code>max-size</code> and "
        "<code>max-files</code>. Accepted files are listed with name, size and a remove button; "
        "rejected ones appear in a separate list with the reason (&ldquo;File type not "
        "allowed&rdquo;, &ldquo;File too large&rdquo;, &ldquo;Maximum file count "
        "exceeded&rdquo;, &ldquo;Only one file can be selected&rdquo;) and a dismiss button. "
        "While files are dragged over it the host has the <code>drag-over</code> attribute, "
        "and <code>drag-invalid</code> when their MIME type is not accepted.</p>"
        "<p>The component queues files; uploading is up to the page. Report progress with "
        "<code>updateFile(id, { status, progress, error })</code>: <code>uploading</code> shows "
        "a progress bar, <code>done</code> a check mark and <code>error</code> the message. "
        "It is form-associated: the form receives every queued <code>File</code> under "
        "<code>name</code>, <code>required</code> needs at least one file, and a form reset "
        "empties it. <code>disabled</code> (or a disabled fieldset) disables browsing, drops "
        "and removal.</p>"
    ),
    how_to_use=(
        "<p>Set <code>accept</code> (MIME types, <code>type/*</code> groups or extensions), "
        "<code>max-size</code> in bytes and <code>max-files</code>. Files are allowed in any "
        "number unless <code>multiple=\"false\"</code>: then each new file replaces the "
        "current one. <code>show-list=\"false\"</code> hides the accepted list (rejections "
        "still show). Listen for <code>mj-files-added</code> and start uploads with the ids in "
        "<code>detail.files</code>; remove entries with <code>removeFile(id)</code> or "
        "<code>clear()</code>. Replace the icon and text with the <code>icon</code> and "
        "<code>instructions</code> slots. Removing works with the remove buttons and "
        "<kbd>Delete</kbd> / <kbd>Backspace</kbd> on them.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="accept", description="Comma-separated MIME types, `type/*` groups or extensions; shown in the constraint line.",
                     kind="string", values=[".pdf,.docx", "image/*", "image/png,image/jpeg"]),
        AttributeDoc(name="multiple", description="`false` keeps a single file (a new one replaces it); any other value or absent allows several.",
                     kind="boolean", default="true"),
        AttributeDoc(name="max-size", description="Maximum bytes per file; larger files are rejected.", kind="number"),
        AttributeDoc(name="max-files", description="Maximum number of queued files.", kind="number"),
        AttributeDoc(name="show-list", description="`false` hides the accepted-file list.", kind="boolean", default="true"),
        AttributeDoc(name="compact", description="A single-row layout for tight spaces.", kind="boolean"),
        AttributeDoc(name="disabled", description="Disables browsing, dropping and removing (a disabled fieldset does the same).",
                     kind="boolean"),
        AttributeDoc(name="label", description="Accessible name of the drop region.", kind="string", default="File upload"),
        AttributeDoc(name="browse-label", description="Text of the browse button.", kind="string", default="Browse files"),
        AttributeDoc(name="drag-label", description="Instruction text (fallback of the `instructions` slot).",
                     kind="string", default="Drag and drop files here, or"),
        AttributeDoc(name="name", description="Form field name; each queued File is appended under it.", kind="string"),
        AttributeDoc(name="required", description="Invalid (`valueMissing`) until a file is queued.", kind="boolean"),
        AttributeDoc(name="required-message", description="Validation message when required and empty.",
                     kind="string", default="Please select a file."),
    ],
    events=[
        ("mj-files-added", "Files passed the checks and were queued.",
         "{ files: [{ id, file: File, status, progress, error }] }"),
        ("mj-files-rejected", "Files failed a check (this batch only).",
         "{ rejectedFiles: [{ id, file: File, reason: string }] }"),
        ("mj-file-remove", "A file left the queue (remove button, removeFile() or replacement in single mode).",
         "{ fileId: string, file: File }"),
        ("mj-drag-enter", "Files were dragged onto the zone.", ""),
        ("mj-drag-leave", "The drag left the zone without dropping.", ""),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Accepts PDF and Word files up to 10&nbsp;MB. Drop files on the zone or use "
                "Browse; a file of another type or size is listed as rejected. Events appear in "
                "the Events panel.</p>"
            ),
            html=(
                '<mj-dropzone id="upload" label="Upload documents" accept=".pdf,.docx" max-size="10485760"></mj-dropzone>'
            ),
            css="mj-dropzone { max-inline-size: 36rem; margin: var(--mj-space-4); }\n",
        ),
        ComponentExample(
            key="upload-progress",
            title="Upload progress",
            description=(
                "<p>The script queues three files and a 12&nbsp;MB video (rejected by "
                "<code>max-size</code>), then drives <code>updateFile()</code>: one upload "
                "completes, one fails with a message, one keeps going.</p>"
            ),
            html='<mj-dropzone id="progress" label="Release assets" max-size="5242880"></mj-dropzone>',
            css="mj-dropzone { max-inline-size: 36rem; margin: var(--mj-space-4); }\n",
            script=(
                _DROPZONE_ADD_SCRIPT
                + 'const zone = document.getElementById("progress")\n'
                'zone.addEventListener("mj-files-added", (event) => {\n'
                '  const [first, second, third] = event.detail.files\n'
                '  let percent = 0\n'
                '  const timer = setInterval(() => {\n'
                '    percent = percent + 10\n'
                '    zone.updateFile(first.id, { status: percent >= 100 ? "done" : "uploading", progress: percent })\n'
                '    zone.updateFile(third.id, { status: "uploading", progress: Math.min(percent / 2, 95) })\n'
                '    if (percent === 40) {\n'
                '      zone.updateFile(second.id, { status: "error", error: "Upload failed: the server closed the connection" })\n'
                '    }\n'
                '    if (percent >= 100) {\n'
                '      clearInterval(timer)\n'
                '    }\n'
                '  }, 300)\n'
                '})\n'
                'pick(zone, [\n'
                '  sized("changelog-4.2.pdf", "application/pdf", 182000),\n'
                '  sized("screenshots.zip", "application/zip", 3400000),\n'
                '  sized("installer-4.2.dmg", "application/x-apple-diskimage", 4900000),\n'
                '  sized("walkthrough.mp4", "video/mp4", 12582912)\n'
                '])\n'
            ),
        ),
        ComponentExample(
            key="single-compact",
            title="Single file, limits, compact",
            description=(
                "<p>Top: <code>multiple=\"false\" compact accept=\"image/*\"</code> for an avatar; a "
                "second pick replaces the file. Bottom: <code>max-files=\"2\"</code> with the list "
                "hidden by <code>show-list=\"false\"</code>, and a <code>disabled</code> zone.</p>"
            ),
            html=(
                '<mj-dropzone id="avatar" label="Profile picture" multiple="false" compact accept="image/*"\n'
                '             browse-label="Choose image" drag-label="Drop an image, or"></mj-dropzone>\n'
                '<mj-dropzone label="Two files at most" max-files="2" show-list="false"></mj-dropzone>\n'
                '<mj-dropzone label="Uploads paused" disabled drag-label="Uploads are paused during maintenance"></mj-dropzone>'
            ),
            css="mj-dropzone { display: block; max-inline-size: 36rem; margin: var(--mj-space-4); }\n",
        ),
        ComponentExample(
            key="form",
            title="In a form",
            description=(
                "<p><code>name=\"attachments\" required</code>: submitting while empty shows the "
                "validation message; a valid submit lists the <code>File</code> entries the form "
                "receives. Reset empties the zone.</p>"
            ),
            html=(
                '<form id="ticket" class="ticket">\n'
                '  <label>Summary <input name="summary" value="Export fails for large reports"></label>\n'
                '  <mj-dropzone name="attachments" required label="Attachments" compact></mj-dropzone>\n'
                '  <div class="row"><button type="submit">Submit ticket</button> <button type="reset">Reset</button></div>\n'
                '  <output id="entries"></output>\n'
                '</form>'
            ),
            css=(
                ".ticket { display: grid; gap: var(--mj-space-3); max-inline-size: 36rem; margin: var(--mj-space-4); }\n"
                ".ticket label { display: grid; gap: var(--mj-space-1); }\n"
            ),
            script=(
                'const form = document.getElementById("ticket")\n'
                'form.addEventListener("submit", (event) => {\n'
                '  event.preventDefault()\n'
                '  const files = new FormData(form).getAll("attachments").map((file) => file.name + " (" + file.size + " bytes)")\n'
                '  document.getElementById("entries").textContent = "attachments: " + files.join(", ")\n'
                '  mjSandbox.log("submitted", { files: files })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="slots",
            title="Slots and styling",
            description="<p>Custom <code>icon</code> and <code>instructions</code> slots with the custom properties for size, border and background.</p>",
            html=(
                '<mj-dropzone id="styled" label="Import contacts" accept=".csv,.vcf">\n'
                '  <svg slot="icon" viewBox="0 0 24 24" width="32" height="32" aria-hidden="true">\n'
                '    <path fill="currentColor" d="M12 3a4 4 0 1 1 0 8 4 4 0 0 1 0-8Zm-7 17a7 7 0 0 1 14 0v1H5Z"/>\n'
                '  </svg>\n'
                '  <span slot="instructions">Drop a CSV or vCard export here, or</span>\n'
                '</mj-dropzone>'
            ),
            css=(
                "mj-dropzone {\n"
                "  max-inline-size: 36rem;\n"
                "  margin: var(--mj-space-4);\n"
                "  --mj-dropzone-min-height: 140px;\n"
                "  --mj-dropzone-radius: var(--mj-radius-lg);\n"
                "  --mj-dropzone-border: 2px solid var(--mj-border);\n"
                "  --mj-dropzone-bg: var(--mj-surface);\n"
                "  --mj-dropzone-border-dragover: 2px solid var(--mj-accent);\n"
                "}\n"
                "mj-dropzone::part(icon) { color: var(--mj-accent); }\n"
            ),
        ),
    ],
    slots=[
        ("icon", "Icon above the instructions (default a cloud).",
         '<svg viewBox="0 0 24 24" width="32" height="32" aria-hidden="true"><path fill="currentColor" d="M5 20h14v-2H5Zm7-16-5 5h3v6h4V9h3Z"/></svg>'),
        ("instructions", "Instruction text before the browse button (default `drag-label`).",
         "<span>Drop your files here, or</span>"),
    ],
    properties=[
        ("files", "object[], read-only. Queued entries `{ id, file: File, status, progress, error }`."),
        ("rejectedFiles", "object[], read-only. Rejections `{ id, file: File, reason }`, kept until dismissed or cleared."),
        ("value", "string. The first queued file's name, or \"\". Setting \"\" or null clears the zone without events."),
        ("form", "HTMLFormElement | null, read-only. The owning form."),
        ("validity", "ValidityState, read-only. `valueMissing` when required and empty."),
    ],
    methods=[
        ("updateFile(fileId, { status, progress, error })", "Updates one row: `uploading` shows a progress bar (0-100), `done` a check mark, `error` the message (default \"Error\")."),
        ("removeFile(fileId) -> boolean", "Removes a queued file and fires `mj-file-remove`."),
        ("clear()", "Empties the queue and the rejected list without events."),
        ("checkValidity() -> boolean", "Runs constraint validation."),
        ("reportValidity() -> boolean", "Validates and shows the browser message."),
    ],
    parts=[
        ("drop-target", "The drop region."),
        ("icon", "The icon container."),
        ("instructions", "The instruction text."),
        ("browse-button", "The browse button."),
        ("constraint-text", "The accepted types and size limit line."),
        ("file-list", "The list of queued files."),
        ("file-item", "One queued file row."),
        ("file-name", "A file's name."),
        ("file-size", "A file's size."),
        ("file-progress", "A file's progress bar."),
        ("file-remove", "A file's remove button."),
        ("file-error", "The error text of a failed upload, in a queued file's row."),
        ("error-list", "The list of rejected files."),
        ("error-item", "A rejected-file row."),
        ("error-name", "A rejected file's name."),
        ("error-reason", "Why the file was rejected."),
        ("error-dismiss", "A rejected file's dismiss button (disabled while the zone is disabled)."),
    ],
    css_properties=[
        ("--mj-dropzone-min-height", "Minimum height of the drop region (default 180px)."),
        ("--mj-dropzone-border", "Border shorthand (default `2px dashed var(--mj-border-strong)`)."),
        ("--mj-dropzone-radius", "Corner radius (default `--mj-radius-md`)."),
        ("--mj-dropzone-bg", "Background (default `--mj-bg-subtle`)."),
        ("--mj-dropzone-border-dragover", "Border while files are dragged over (default `2px dashed var(--mj-accent)`)."),
        ("--mj-dropzone-bg-dragover", "Background while files are dragged over (default 8% accent)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-file-browser
# ---------------------------------------------------------------------------

_FILES_SCRIPT = r'''/* A small in-memory file system, served with a short delay like a real API. */
const TREE = {
  "/": [
    { name: "docs", type: "folder", path: "/docs" },
    { name: "images", type: "folder", path: "/images" },
    { name: "archive", type: "folder", path: "/archive" },
    { name: "restricted", type: "folder", path: "/restricted" },
    { name: ".env", type: "text/plain", path: "/.env", size: "120 B", modified: "2026-11-02 09:14" },
    { name: "README.md", type: "text/markdown", path: "/README.md", size: "2 KB", modified: "2026-11-08 16:40" },
    { name: "package.json", type: "application/json", path: "/package.json", size: "1 KB", modified: "2026-11-07 11:02" }
  ],
  "/docs": [
    { name: "guides", type: "folder", path: "/docs/guides" },
    { name: "changelog.md", type: "text/markdown", path: "/docs/changelog.md", size: "18 KB", modified: "2026-11-09 08:30" },
    { name: "roadmap.pdf", type: "application/pdf", path: "/docs/roadmap.pdf", size: "412 KB", modified: "2026-10-28 14:05" }
  ],
  "/docs/guides": [
    { name: "install.md", type: "text/markdown", path: "/docs/guides/install.md", size: "6 KB", modified: "2026-09-12 10:00" },
    { name: "theming.md", type: "text/markdown", path: "/docs/guides/theming.md", size: "9 KB", modified: "2026-10-01 15:20" }
  ],
  "/images": [
    { name: "logo.png", type: "image/png", path: "/images/logo.png", size: "48 KB", modified: "2026-08-19 12:00" },
    { name: "hero.jpg", type: "image/jpeg", path: "/images/hero.jpg", size: "1.2 MB", modified: "2026-10-30 17:45" },
    { name: "demo.mp4", type: "video/mp4", path: "/images/demo.mp4", size: "24 MB", modified: "2026-11-01 09:10" }
  ],
  "/archive": []
}
const fileSystem = {
  listDir(path) {
    return new Promise((resolve, reject) => setTimeout(() => {
      if (path === "/restricted") {
        reject(new Error("Permission denied"))
      } else {
        resolve(TREE[path] || [])
      }
    }, 150))
  }
}
'''

FILE_BROWSER = ComponentDoc(
    tag="mj-file-browser",
    title="File Browser",
    group="productivity",
    summary="File manager with breadcrumb, folder tree, list or grid view, keyboard selection, a details pane and a context menu, fed by a dataSource.",
    description=(
        "<p><code>&lt;mj-file-browser&gt;</code> shows the folder at <code>currentPath</code> "
        "from its <code>dataSource</code>. A breadcrumb and a toolbar (list / grid buttons and "
        "the <code>toolbar-actions</code> slot) sit on top; below are a folder tree "
        "(<code>role=\"tree\"</code>, built from the folders of every listing, expanding "
        "folders loads them), the file pane (a <code>role=\"grid\"</code> table in list view, a "
        "<code>role=\"listbox\"</code> in grid view) and a details pane, with a status line "
        "&ldquo;N items &middot; N selected&rdquo;. A listing that fails shows an alert with "
        "Retry; an empty folder shows the <code>empty</code> slot.</p>"
        "<p>A single click selects (folders too), <kbd>Ctrl</kbd>/<kbd>Cmd</kbd>+click toggles "
        "and <kbd>Shift</kbd>+click selects a range; a double-click or <kbd>Enter</kbd> opens: a "
        "folder is entered (<code>mj-folder-navigate</code>), a file fires "
        "<code>mj-file-open</code>. In the file pane the arrows move focus and selection "
        "(<kbd>Shift</kbd> extends, <kbd>Ctrl</kbd> moves focus only, "
        "<kbd>ArrowLeft</kbd>/<kbd>ArrowRight</kbd> in grid view), <kbd>Space</kbd> toggles, "
        "<kbd>Home</kbd>/<kbd>End</kbd> jump and <kbd>Ctrl</kbd>+<kbd>A</kbd> selects all. "
        "<kbd>F6</kbd> / <kbd>Shift</kbd>+<kbd>F6</kbd> cycle tree, files and details (from "
        "elsewhere in the browser they start at the first / last pane). Entering a folder "
        "clears the file pane and shows Loading until its listing arrives. The details pane opens while something "
        "is selected and lists name, type, size and modified date (there is no content "
        "preview). Right-click, <kbd>Shift</kbd>+<kbd>F10</kbd> or the Menu key open the "
        "<code>contextMenuItems</code> menu, and a choice fires "
        "<code>mj-context-action</code> with the selected files.</p>"
    ),
    how_to_use=(
        "<p>Give the element a height and assign <code>dataSource = { listDir(path) }</code> "
        "returning (a promise of) items <code>{ name, type, path?, size?, modified? }</code>. "
        "Only <code>type: \"folder\"</code> items are folders; other types pick the icon "
        "(<code>image/*</code>, <code>video/*</code>, <code>audio/*</code>, PDF). "
        "<code>size</code> and <code>modified</code> are shown as given, so format them first. "
        "<code>path</code> defaults to the current folder plus the name; the root is "
        "<code>/</code>. Set <code>currentPath</code> to navigate from script. Names starting "
        "with a dot are hidden unless <code>show-hidden</code> is present; removing it also "
        "removes hidden items from the selection.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the browser.", kind="string", default="File browser"),
        AttributeDoc(name="view", description="File pane layout; the toolbar buttons write it.", kind="enum",
                     values=["list", "grid"], default="list"),
        AttributeDoc(name="selection-mode", description="`single` keeps one selected item; otherwise several can be selected.",
                     kind="enum", values=["single", "multi"], default="multi"),
        AttributeDoc(name="preview", description="`none` never shows the details pane.", kind="enum", values=["none", "auto"],
                     default="auto"),
        AttributeDoc(name="preview-open", description="Present: the details pane is always shown; `false`: never shown; absent: shown while something is selected.",
                     kind="enum", values=["true", "false"]),
        AttributeDoc(name="tree-open", description="`false` hides the folder tree.", kind="boolean", default="true"),
        AttributeDoc(name="show-hidden", description="Also lists names that start with a dot.", kind="boolean"),
    ],
    events=[
        ("mj-folder-navigate", "The current folder changed (breadcrumb, tree, opening a folder, or setting currentPath).",
         "{ path: string }"),
        ("mj-file-open", "A file (not a folder) was opened with a double-click or Enter.", "{ file: object }"),
        ("mj-selection-change", "The selection changed.", "{ selectedFiles: object[] }"),
        ("mj-view-change", "A view button was clicked.", "{ view: 'list' | 'grid' }"),
        ("mj-context-action", "A context-menu item was chosen.",
         "{ action: any, item: object, files: object[] }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A project folder from an in-memory <code>dataSource</code>. Click to select "
                "(the details pane opens), double-click or press <kbd>Enter</kbd> to open, expand "
                "folders in the tree, switch list / grid. <em>archive</em> is empty and "
                "<em>restricted</em> fails to load (try Retry). Opened files are logged.</p>"
            ),
            html='<mj-file-browser id="files" label="Project files" style="height:380px"></mj-file-browser>',
            script=(
                _FILES_SCRIPT
                + 'const browser = document.getElementById("files")\n'
                'browser.dataSource = fileSystem\n'
                'browser.addEventListener("mj-file-open", (event) => mjSandbox.log("open", { path: event.detail.file.path }))\n'
            ),
        ),
        ComponentExample(
            key="grid-single",
            title="Grid view, single selection",
            description=(
                "<p><code>view=\"grid\"</code> with <code>selection-mode=\"single\"</code> and "
                "<code>preview-open</code> (the details pane stays open). The script starts in "
                "<code>/images</code> by setting <code>currentPath</code>; arrow keys move in two "
                "directions in the grid.</p>"
            ),
            html='<mj-file-browser id="gallery" label="Images" view="grid" selection-mode="single" preview-open style="height:360px"></mj-file-browser>',
            script=(
                _FILES_SCRIPT
                + 'const gallery = document.getElementById("gallery")\n'
                'gallery.dataSource = fileSystem\n'
                'gallery.currentPath = "/images"\n'
            ),
        ),
        ComponentExample(
            key="context-menu",
            title="Context menu, toolbar actions, hidden files",
            description=(
                "<p>Right-click a file (or press <kbd>Shift</kbd>+<kbd>F10</kbd>) for the "
                "<code>contextMenuItems</code> menu; <code>mj-context-action</code> carries the "
                "selected files. The <code>toolbar-actions</code> slot adds buttons that act on the "
                "selection, and <code>show-hidden</code> lists <code>.env</code>.</p>"
            ),
            html=(
                '<mj-file-browser id="manager" label="Repository" show-hidden style="height:380px">\n'
                '  <button slot="toolbar-actions" type="button" id="download">Download</button>\n'
                '  <button slot="toolbar-actions" type="button" id="share">Share</button>\n'
                '</mj-file-browser>'
            ),
            script=(
                _FILES_SCRIPT
                + 'const manager = document.getElementById("manager")\n'
                'manager.dataSource = fileSystem\n'
                'manager.contextMenuItems = [\n'
                '  { label: "Open", value: "open" },\n'
                '  { label: "Rename", value: "rename" },\n'
                '  { label: "Duplicate", value: "duplicate" },\n'
                '  { separator: true },\n'
                '  { label: "Delete", value: "delete" }\n'
                ']\n'
                'manager.addEventListener("mj-context-action", (event) => {\n'
                '  mjSandbox.log("context action", { action: event.detail.action, files: event.detail.files.map((f) => f.name) })\n'
                '})\n'
                'for (const id of ["download", "share"]) {\n'
                '  document.getElementById(id).addEventListener("click", () => {\n'
                '    mjSandbox.log(id, { files: manager.selectedFiles.map((f) => f.name) })\n'
                '  })\n'
                '}\n'
            ),
        ),
        ComponentExample(
            key="empty",
            title="Empty folder, no tree",
            description=(
                "<p><code>tree-open=\"false\"</code> and <code>preview=\"none\"</code> leave only the "
                "file pane; the script opens the empty <code>/archive</code> folder, which shows "
                "the custom <code>empty</code> slot. Use the breadcrumb to go back up.</p>"
            ),
            html=(
                '<mj-file-browser id="archive" label="Archive" tree-open="false" preview="none" style="height:300px">\n'
                '  <div slot="empty" class="empty">\n'
                '    <strong>This folder is empty.</strong>\n'
                '    <span>Archived projects appear here after 90 days.</span>\n'
                '  </div>\n'
                '</mj-file-browser>'
            ),
            css=".empty { display: grid; gap: var(--mj-space-1); padding: var(--mj-space-4); text-align: center; }\n",
            script=(
                _FILES_SCRIPT
                + 'const archive = document.getElementById("archive")\n'
                'archive.dataSource = fileSystem\n'
                'archive.currentPath = "/archive"\n'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>Custom properties for the pane widths, grid tile size and colours.</p>",
            html='<mj-file-browser id="styled" view="grid" label="Styled files" style="height:340px"></mj-file-browser>',
            css=(
                "mj-file-browser {\n"
                "  --mj-fb-tree-width: 170px;\n"
                "  --mj-fb-preview-width: 220px;\n"
                "  --mj-fb-grid-item-size: 120px;\n"
                "  --mj-fb-grid-gap: var(--mj-space-4);\n"
                "  --mj-fb-bg: var(--mj-bg-subtle);\n"
                "  --mj-fb-border: var(--mj-accent);\n"
                "}\n"
            ),
            script=(
                _FILES_SCRIPT
                + 'const styled = document.getElementById("styled")\n'
                'styled.dataSource = fileSystem\n'
                'styled.currentPath = "/docs"\n'
            ),
        ),
    ],
    slots=[
        ("toolbar-actions", "Extra toolbar content after the view buttons.",
         '<button type="button">Upload</button>'),
        ("empty", "Shown when the current folder has no items.",
         "<div><strong>This folder is empty.</strong></div>"),
    ],
    properties=[
        ("dataSource", "{ listDir(path) } | null. Returns (a promise of) the items of `path`; setting it reloads the current folder."),
        ("currentPath", "string. The folder shown (`/` for the root); setting it navigates and fires mj-folder-navigate."),
        ("selectedFiles", "object[], read-only. The selected items."),
        ("contextMenuItems", "object[]. Context-menu entries `{ label, value, disabled? }` or `{ separator: true }`."),
    ],
    methods=[],
    parts=[
        ("root", "The browser container."),
        ("breadcrumb", "The path breadcrumb."),
        ("toolbar", "The toolbar with the view buttons and the `toolbar-actions` slot."),
        ("panes", "The row of tree, file and details panes."),
        ("tree-pane", "The folder tree pane."),
        ("file-pane", "The file list or grid pane."),
        ("file-grid", "The grid (grid view)."),
        ("file-item", "One file row (list) or tile (grid)."),
        ("file-icon", "A file's icon."),
        ("file-name", "A file's name."),
        ("preview-pane", "The details pane."),
        ("status-strip", "The item and selection counts."),
    ],
    css_properties=[
        ("--mj-fb-bg", "Background (default `--mj-bg`)."),
        ("--mj-fb-border", "Border colour (default `--mj-border`)."),
        ("--mj-fb-tree-width", "Tree pane width (default 220px)."),
        ("--mj-fb-preview-width", "Details pane width (default 300px)."),
        ("--mj-fb-grid-item-size", "Grid tile size (default 96px)."),
        ("--mj-fb-grid-gap", "Gap between grid tiles (default `--mj-space-3`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-activity-feed
# ---------------------------------------------------------------------------

_ACTIVITY_SCRIPT = r'''const minutes = (count) => new Date(Date.now() - count * 60000).toISOString()
const RECENT = [
  { id: "a1", actor: { name: "Alice Martin" }, action: "created the document", body: "Q4 planning notes", timestamp: minutes(3) },
  { id: "a2", actor: { name: "Bob Lee" }, action: "commented on", body: "Looks good to me. Can we move the launch to Tuesday so support has a full day to prepare?", timestamp: minutes(26) },
  { id: "a3", actor: { name: "Carmen Ortiz" }, action: "uploaded budget-2027.xlsx", timestamp: minutes(140) },
  { id: "a4", actor: { name: "Dmitri Volkov" }, action: "closed issue #482", body: "Export fails for reports with more than 10,000 rows", timestamp: minutes(60 * 26) }
]
const OLDER = [
  [
    { id: "a5", actor: { name: "Alice Martin" }, action: "renamed the project to Q4 launch", timestamp: minutes(60 * 50) },
    { id: "a6", actor: { name: "Bob Lee" }, action: "invited Carmen Ortiz", timestamp: minutes(60 * 75) }
  ],
  [
    { id: "a7", actor: {}, action: "Project created from the Launch template", timestamp: minutes(60 * 24 * 6) }
  ]
]
'''

ACTIVITY_FEED = ComponentDoc(
    tag="mj-activity-feed",
    title="Activity Feed",
    group="productivity",
    summary="Chronological activity stream with relative times, date grouping, item actions, realtime additions and load-older paging.",
    description=(
        "<p><code>&lt;mj-activity-feed&gt;</code> renders its <code>items</code> as articles in "
        "a <code>role=\"feed\"</code> list: avatar (image or initials), actor name, action "
        "text, an optional body (plain text, clamped to four lines with Show more), item "
        "action buttons and a timestamp. Timestamps are relative (&ldquo;5 minutes "
        "ago&rdquo;, refreshed every minute), absolute or both; text that is not a date is "
        "shown as given. <code>group-by=\"date\"</code> inserts a heading whenever the day "
        "changes between consecutive items (the order is yours); the feed itself holds only "
        "articles, so the heading is hidden from assistive technology and describes the first "
        "article of its day instead, and the empty state is shown outside the feed.</p>"
        "<p>Below the list a &ldquo;Load older activity&rdquo; button (or, with "
        "<code>load-mode=\"infinite\"</code>, a sentinel) fires <code>mj-load-older</code> while "
        "<code>hasMore</code> is true; without a data source the feed then waits (busy, the "
        "button inert) until the page assigns <code>items</code> or <code>hasMore</code>, so it "
        "never asks twice. With a <code>dataSource</code> the feed loads its first "
        "page and the older pages itself and shows an error with Retry when a request fails. "
        "<code>addItem()</code> prepends an item; with <code>realtime</code>, items added while "
        "the top of the feed is scrolled out of view are counted in a sticky &ldquo;N new "
        "events&rdquo; banner that scrolls back up. Articles are focusable: "
        "<kbd>PageDown</kbd>/<kbd>PageUp</kbd> move between them, <kbd>Home</kbd>/<kbd>End</kbd> "
        "to the first and last. <code>compact</code> shows one line per item.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>items</code> = <code>[{ id, actor: { name, avatarUrl? }, action, "
        "body?, timestamp, actions?: [{ action, label }] }]</code>, newest first. Without a data "
        "source <code>hasMore</code> starts <code>false</code>: set it to <code>true</code> to "
        "offer older items, answer <code>mj-load-older</code> by appending "
        "(<code>feed.items = feed.items.concat(older)</code>) and set <code>hasMore = "
        "false</code> at the end. With <code>dataSource = { query({ cursor }) }</code> (or "
        "<code>fetch</code>) returning <code>{ items, cursor, hasMore? }</code> the feed pages "
        "itself; a <code>null</code> cursor ends paging. Item action buttons fire "
        "<code>mj-item-action</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the feed.", kind="string", default="Activity feed"),
        AttributeDoc(name="timestamp-format", description="How times are shown (relative ones have the absolute time as tooltip).",
                     kind="enum", values=["relative", "absolute", "both"], default="relative"),
        AttributeDoc(name="group-by", description="`date` inserts a day heading when the day changes.", kind="enum",
                     values=["date"]),
        AttributeDoc(name="load-mode", description="`button`: a Load older button; `infinite`: loads when the end scrolls into view.",
                     kind="enum", values=["button", "infinite"], default="button"),
        AttributeDoc(name="realtime", description="Counts items added with addItem() while the top is out of view in a \"N new events\" banner.",
                     kind="boolean"),
        AttributeDoc(name="compact", description="One line per item: smaller avatar, no body or actions.", kind="boolean"),
        AttributeDoc(name="empty-message", description="Text shown when there are no items (fallback of the `empty` slot).",
                     kind="string", default="No activity yet."),
    ],
    events=[
        ("mj-load-older", "Load older was activated (button or sentinel) while hasMore is true and no earlier request is pending; also fired with a data source, before it fetches.",
         "{ cursor: any }"),
        ("mj-item-action", "An item action button was clicked.", "{ itemId: any, action: string, item: object }"),
        ("mj-new-items-viewed", "The new-items banner was clicked, or the top came back into view with new items counted.",
         "{ count: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Four recent items with relative times and a long body (Show more). The script sets "
                "<code>hasMore = true</code>, so &ldquo;Load older activity&rdquo; is offered; it "
                "fires <code>mj-load-older</code>, the script appends two older pages and then "
                "sets <code>hasMore = false</code>. Focus an item and press "
                "<kbd>PageDown</kbd>.</p>"
            ),
            html='<mj-activity-feed id="feed" label="Recent activity" load-mode="button"></mj-activity-feed>',
            css="mj-activity-feed { max-inline-size: 40rem; margin: var(--mj-space-4); }\n",
            script=(
                _ACTIVITY_SCRIPT
                + 'const feed = document.getElementById("feed")\n'
                'let page = 0\n'
                'feed.items = RECENT.slice()\n'
                'feed.hasMore = true\n'
                'feed.addEventListener("mj-load-older", () => {\n'
                '  if (page >= OLDER.length) { return }\n'
                '  feed.items = feed.items.concat(OLDER[page])\n'
                '  page = page + 1\n'
                '  feed.hasMore = page < OLDER.length\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="realtime",
            title="Realtime additions",
            description=(
                "<p>A scrolling feed with <code>realtime</code>. The script scrolls it down and adds "
                "an item every few seconds with <code>addItem()</code>; they are counted in the "
                "sticky banner, which scrolls back to the top when clicked "
                "(<code>mj-new-items-viewed</code>). &ldquo;Add activity&rdquo; adds one now.</p>"
            ),
            html=(
                '<button type="button" id="add">Add activity</button>\n'
                '<div class="scroller">\n'
                '  <mj-activity-feed id="live" realtime label="Live activity"></mj-activity-feed>\n'
                '</div>'
            ),
            css=(
                "#add { margin: var(--mj-space-3) var(--mj-space-4) 0; }\n"
                ".scroller { block-size: 300px; overflow-y: auto; margin: var(--mj-space-3) var(--mj-space-4);\n"
                "            border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }\n"
            ),
            script=(
                _ACTIVITY_SCRIPT
                + 'const live = document.getElementById("live")\n'
                'const scroller = document.querySelector(".scroller")\n'
                'live.items = RECENT.concat(OLDER[0], OLDER[1])\n'
                'live.hasMore = false\n'
                'const people = ["Alice Martin", "Bob Lee", "Carmen Ortiz", "Dmitri Volkov"]\n'
                'let next = 100\n'
                'function addOne() {\n'
                '  next = next + 1\n'
                '  live.addItem({ id: "live-" + next, actor: { name: people[next % people.length] },\n'
                '                 action: "updated task #" + next, timestamp: new Date().toISOString() })\n'
                '}\n'
                'document.getElementById("add").addEventListener("click", addOne)\n'
                'scroller.scrollTop = scroller.scrollHeight\n'
                'addOne()\n'
                'let added = 0\n'
                'const timer = setInterval(() => { addOne(); added = added + 1; if (added >= 3) { clearInterval(timer) } }, 3000)\n'
            ),
        ),
        ComponentExample(
            key="data-source",
            title="Data source, date groups, actions",
            description=(
                "<p>A <code>dataSource</code> serves three pages by cursor; <code>group-by=\"date\"</code> "
                "adds day headings and <code>timestamp-format=\"both\"</code> shows relative and "
                "absolute time. Avatars are PNG data URLs drawn by the script. Review items have "
                "action buttons (<code>mj-item-action</code>). The last page fails once to show "
                "the error and Retry.</p>"
            ),
            html='<mj-activity-feed id="paged" label="Project history" group-by="date" timestamp-format="both"></mj-activity-feed>',
            css="mj-activity-feed { max-inline-size: 40rem; margin: var(--mj-space-4); }\n",
            script=(
                'function avatar(initials, hue) {\n'
                '  const canvas = document.createElement("canvas")\n'
                '  canvas.width = 64\n'
                '  canvas.height = 64\n'
                '  const context = canvas.getContext("2d")\n'
                '  context.fillStyle = "hsl(" + hue + " 55% 45%)"\n'
                '  context.fillRect(0, 0, 64, 64)\n'
                '  context.fillStyle = "white"\n'
                '  context.font = "bold 26px sans-serif"\n'
                '  context.textAlign = "center"\n'
                '  context.textBaseline = "middle"\n'
                '  context.fillText(initials, 32, 34)\n'
                '  return canvas.toDataURL("image/png")\n'
                '}\n'
                'const alice = { name: "Alice Martin", avatarUrl: avatar("AM", 210) }\n'
                'const bob = { name: "Bob Lee", avatarUrl: avatar("BL", 20) }\n'
                'const hoursAgo = (hours) => new Date(Date.now() - hours * 3600000).toISOString()\n'
                'const review = [{ action: "approve", label: "Approve" }, { action: "reject", label: "Request changes" }]\n'
                'const PAGES = {\n'
                '  start: { items: [\n'
                '    { id: 1, actor: alice, action: "requested a review of the pricing page", timestamp: hoursAgo(0.2), actions: review },\n'
                '    { id: 2, actor: bob, action: "pushed 3 commits to release/4.2", timestamp: hoursAgo(1.5) },\n'
                '    { id: 3, actor: alice, action: "merged pull request #311", timestamp: hoursAgo(20) }\n'
                '  ], cursor: "p2" },\n'
                '  p2: { items: [\n'
                '    { id: 4, actor: bob, action: "opened pull request #312", timestamp: hoursAgo(50), actions: review },\n'
                '    { id: 5, actor: alice, action: "created branch release/4.2", timestamp: hoursAgo(74) }\n'
                '  ], cursor: "p3" },\n'
                '  p3: { items: [{ id: 6, actor: bob, action: "joined the project", timestamp: hoursAgo(220) }], cursor: null }\n'
                '}\n'
                'let failedOnce = false\n'
                'const paged = document.getElementById("paged")\n'
                'paged.dataSource = {\n'
                '  query({ cursor }) {\n'
                '    mjSandbox.log("query", { cursor })\n'
                '    return new Promise((resolve, reject) => setTimeout(() => {\n'
                '      if (cursor === "p3" && failedOnce === false) {\n'
                '        failedOnce = true\n'
                '        reject(new Error("Network error"))\n'
                '      } else {\n'
                '        resolve(PAGES[cursor === null ? "start" : cursor])\n'
                '      }\n'
                '    }, 400))\n'
                '  }\n'
                '}\n'
            ),
        ),
        ComponentExample(
            key="compact-empty",
            title="Compact and empty",
            description=(
                "<p>Top: <code>compact</code> with <code>timestamp-format=\"absolute\"</code>, one "
                "line per item. Bottom: an empty feed with a custom <code>empty</code> slot.</p>"
            ),
            html=(
                '<mj-activity-feed id="compact" compact timestamp-format="absolute" label="Audit log"></mj-activity-feed>\n'
                '<mj-activity-feed label="Mentions">\n'
                '  <div slot="empty" class="empty">No mentions yet. When someone @mentions you, it shows up here.</div>\n'
                '</mj-activity-feed>'
            ),
            css=(
                "mj-activity-feed { display: block; max-inline-size: 40rem; margin: var(--mj-space-4); }\n"
                ".empty { padding: var(--mj-space-4); color: var(--mj-text-muted); text-align: center; }\n"
            ),
            script=(
                _ACTIVITY_SCRIPT
                + 'const compact = document.getElementById("compact")\n'
                'compact.items = RECENT.concat(OLDER[0])\n'
                'compact.hasMore = false\n'
                'document.querySelectorAll("mj-activity-feed")[1].hasMore = false\n'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>Larger avatars, an accent timeline line and wider spacing through the custom properties.</p>",
            html='<mj-activity-feed id="styled" label="Styled feed"></mj-activity-feed>',
            css=(
                "mj-activity-feed {\n"
                "  max-inline-size: 40rem;\n"
                "  margin: var(--mj-space-4);\n"
                "  --mj-feed-avatar-size: 40px;\n"
                "  --mj-feed-gap: var(--mj-space-5);\n"
                "  --mj-feed-line-width: 3px;\n"
                "  --mj-feed-line-color: var(--mj-accent);\n"
                "  --mj-feed-timestamp-color: var(--mj-accent);\n"
                "}\n"
            ),
            script=(
                _ACTIVITY_SCRIPT
                + 'const styled = document.getElementById("styled")\n'
                'styled.items = RECENT\n'
                'styled.hasMore = false\n'
            ),
        ),
    ],
    slots=[
        ("empty", "Shown when there are no items (default `empty-message`).",
         "<div>No activity yet. Changes to this project appear here.</div>"),
    ],
    properties=[
        ("items", "object[]. `{ id, actor: { name, avatarUrl? }, action, body?, timestamp, actions? }`, newest first; the live array (addItem() prepends to it)."),
        ("hasMore", "boolean. Whether Load older is offered. Without a data source it starts `false`: set `true` to offer older items, `false` at the end; assigning it (or `items`) also ends the busy state after `mj-load-older`. A data source maintains it from its cursor."),
        ("dataSource", "{ query({ cursor }) } | { fetch({ cursor }) } | null. Returns (a promise of) `{ items, cursor, hasMore? }`; setting it loads the first page (cursor `null`)."),
        ("newItemCount", "number, read-only. Items counted by the realtime banner."),
    ],
    methods=[
        ("addItem(item)", "Prepends an item (an item whose id is already present is ignored); counted by the banner with `realtime` when the top is out of view."),
    ],
    parts=[
        ("root", "The feed container."),
        ("new-banner", "The \"N new events\" banner."),
        ("feed-list", "The `role=\"feed\"` list."),
        ("group-heading", "A day heading (`group-by=\"date\"`); hidden from assistive technology, it describes the first article of its day."),
        ("item", "One activity article."),
        ("item-avatar", "An item's avatar."),
        ("item-header", "An item's header line."),
        ("item-actor", "The actor name."),
        ("item-action-text", "The action text."),
        ("item-timestamp", "The time."),
        ("item-body", "The body text."),
        ("item-actions", "The item action buttons."),
        ("load-more", "The Load older activity button."),
        ("empty-state", "The empty state (outside the feed list)."),
    ],
    css_properties=[
        ("--mj-feed-gap", "Space between items (default `--mj-space-4`; `--mj-space-2` when compact)."),
        ("--mj-feed-avatar-size", "Avatar size (default 32px; 20px when compact)."),
        ("--mj-feed-line-width", "Width of the timeline line (default 2px)."),
        ("--mj-feed-line-color", "Colour of the timeline line (default `--mj-border`)."),
        ("--mj-feed-timestamp-color", "Timestamp colour (default `--mj-text-muted`)."),
        ("--mj-feed-new-banner-bg", "New-items banner background (default `--mj-bg-muted`)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-comments
# ---------------------------------------------------------------------------

_COMMENTS_SCRIPT = r'''const minutes = (count) => new Date(Date.now() - count * 60000).toISOString()
const reply = (id, authorId, authorName, body, ago) => ({ id, authorId, authorName, body, createdAt: minutes(ago) })
const THREAD = [
  { id: "c1", authorId: "u2", authorName: "Alice Martin", createdAt: minutes(180),
    body: "The new onboarding flow cut sign-up time in half in the test group.\nShall we roll it out to everyone next week?",
    reactions: [{ emoji: "\u{1F44D}", count: 3, userIds: ["u3", "u4", "u5"] }, { emoji: "\u{1F389}", count: 1, userIds: ["u1"] }],
    replies: [
      reply("c1-r1", "u3", "Bob Lee", "Yes, support is ready.", 170),
      reply("c1-r2", "u4", "Carmen Ortiz", "Can we keep the old flow behind a flag for a week?", 150),
      reply("c1-r3", "u1", "You", "Good idea, I will add the flag.", 140),
      reply("c1-r4", "u5", "Dmitri Volkov", "QA signed off on both flows.", 90)
    ] },
  { id: "c2", authorId: "u1", authorName: "You", createdAt: minutes(45),
    body: "I posted the rollout checklist in the project wiki." },
  { id: "c3", authorId: "u3", authorName: "Bob Lee", createdAt: minutes(30), deleted: true, body: "" }
]
let sequence = 0
function newComment(body) {
  sequence = sequence + 1
  return { id: "new-" + sequence, authorId: "u1", authorName: "You", body: body, createdAt: new Date().toISOString() }
}
/* The component never changes reaction counts; the page does. */
function applyReaction(comments, detail, userId) {
  const visit = (list) => list.forEach((comment) => {
    if (comment.id === detail.commentId) {
      comment.reactions = comment.reactions || []
      let reaction = comment.reactions.find((r) => r.emoji === detail.emoji)
      if (reaction === undefined) {
        reaction = { emoji: detail.emoji, count: 0, userIds: [] }
        comment.reactions.push(reaction)
      }
      const mine = reaction.userIds.includes(userId)
      if (detail.active && !mine) { reaction.userIds.push(userId); reaction.count = reaction.count + 1 }
      if (!detail.active && mine) { reaction.userIds = reaction.userIds.filter((id) => id !== userId); reaction.count = reaction.count - 1 }
      comment.reactions = comment.reactions.filter((r) => r.count > 0)
    }
    visit(comment.replies || [])
  })
  visit(comments)
}
'''

COMMENTS = ComponentDoc(
    tag="mj-comments",
    title="Comments",
    group="productivity",
    summary="Threaded discussion with a composer, replies, editing and deleting your own comments, emoji reactions and paging.",
    description=(
        "<p><code>&lt;mj-comments&gt;</code> renders a count heading, its <code>comments</code> "
        "as articles in a <code>role=\"feed\"</code> list, and a composer above or below the list. "
        "The feed holds the top-level comments only: a comment's replies are a group of articles "
        "inside the comment's own article (nested up to <code>max-depth</code>; deeper replies are "
        "shown in the deepest thread). Each comment shows "
        "avatar, author, a relative time (refreshed every minute) and its body as plain text "
        "with line breaks kept. Comments whose <code>authorId</code> matches "
        "<code>current-user-id</code> get Edit and Delete; Delete asks for confirmation in an "
        "<code>mj-dialog</code>, then leaves a &ldquo;[Comment deleted]&rdquo; tombstone (a "
        "<code>deleted: true</code> comment). Only the first "
        "<code>max-visible-replies</code> replies show; &ldquo;Show N more replies&rdquo; reveals "
        "the rest, or fires <code>mj-load-replies</code> when <code>replyCount</code> says more "
        "exist than are loaded. Reaction chips toggle, and a &ldquo;+&rdquo; picker offers six "
        "emoji. A &ldquo;Load earlier comments&rdquo; button shows while <code>cursor</code> is "
        "not null.</p>"
        "<p>In the composers <kbd>Enter</kbd> posts and <kbd>Shift</kbd>+<kbd>Enter</kbd> adds "
        "a line; <kbd>Escape</kbd> cancels a reply or edit. <kbd>PageDown</kbd>/<kbd>PageUp</kbd> "
        "move between top-level comments (from a reply, to the comment after or before the one it "
        "belongs to). Every post fires <code>mj-comment-post</code>. "
        "Without a <code>dataSource</code> the composer clears at once and the page adds the "
        "comment with <code>addComment()</code>; with <code>dataSource.post</code> the composer "
        "waits, inserts the returned comment, and keeps the text with an error message when the "
        "post fails. The component updates the body on edit and the tombstone on delete itself, "
        "but never reaction counts: update <code>reactions</code> and reassign "
        "<code>comments</code>.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>comments</code> = <code>[{ id, authorId, authorName, authorAvatar?, "
        "body, createdAt, reactions?: [{ emoji, count, userIds }], replies?: [...], replyCount?, "
        "repliesCursor?, deleted? }]</code> (<code>author: { name, avatarUrl }</code> and "
        "<code>timestamp</code> are accepted too). Set <code>current-user-id</code> for "
        "ownership and pressed reactions. Handle <code>mj-comment-post</code> with "
        "<code>addComment(comment, detail.parentId)</code>, or set <code>dataSource = { "
        "fetch({ cursor }), post({ body, parentId }) }</code>: <code>fetch</code> (or "
        "<code>query</code>) returns an array or <code>{ items, cursor }</code>. Without a data "
        "source, answer <code>mj-load-older</code> by adding older comments and setting "
        "<code>cursor</code>. <code>mentionSource</code> is stored but not used yet and "
        "<code>mentions</code> in the post detail is always empty.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the comment feed.", kind="string", default="Comments"),
        AttributeDoc(name="current-user-id", description="Id of the signed-in user: their comments get Edit and Delete, their reactions show pressed.",
                     kind="string", values=["u1"]),
        AttributeDoc(name="readonly", description="Hides the composer and the Reply, Edit and Delete actions; reactions are shown as counts only (no toggling, no picker, no `mj-comment-react`).", kind="boolean"),
        AttributeDoc(name="composer-position", description="Where the top-level composer sits; new comments are added next to it.",
                     kind="enum", values=["top", "bottom"], default="bottom"),
        AttributeDoc(name="max-depth", description="Deepest nesting level (top level is 0); deeper replies are shown in the deepest thread, after the reply they answer, and cannot be replied to.", kind="number",
                     default="3"),
        AttributeDoc(name="max-visible-replies", description="Replies shown before \"Show N more replies\".", kind="number",
                     default="3"),
        AttributeDoc(name="allow-reactions", description="`false` hides reaction chips and the picker.", kind="boolean",
                     default="true"),
        AttributeDoc(name="empty-message", description="Text shown when there are no comments.", kind="string",
                     default="Be the first to comment."),
    ],
    events=[
        ("mj-comment-post", "A comment or reply was submitted (before any dataSource.post).",
         "{ body: string, parentId: string | null, mentions: [] }"),
        ("mj-comment-edit", "An edit was saved (the component already updated the body).",
         "{ commentId: string, body: string }"),
        ("mj-comment-delete", "A deletion was confirmed (the comment is now a tombstone).", "{ commentId: string }"),
        ("mj-comment-react", "A reaction chip was toggled or an emoji picked.",
         "{ commentId: string, emoji: string, active: boolean }"),
        ("mj-load-replies", "Show more replies was clicked for replies that are not loaded yet.",
         "{ commentId: string, cursor: any }"),
        ("mj-load-older", "Load earlier comments was clicked.", "{ cursor: any }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>You are <code>u1</code>: your comments have Edit and Delete (with a confirmation "
                "dialog). Post a comment or reply (<kbd>Enter</kbd>); the script adds it with "
                "<code>addComment()</code>. Toggle reactions or pick one with &ldquo;+&rdquo;; the "
                "script updates the counts. &ldquo;Show 1 more reply&rdquo; reveals the fourth "
                "reply; the third comment is a tombstone.</p>"
            ),
            html='<main>\n  <mj-comments id="discussion" label="Discussion" current-user-id="u1"></mj-comments>\n</main>',
            css="mj-comments { max-inline-size: 44rem; margin: var(--mj-space-4); }\n",
            script=(
                _COMMENTS_SCRIPT
                + 'const discussion = document.getElementById("discussion")\n'
                'discussion.comments = THREAD\n'
                'discussion.addEventListener("mj-comment-post", (event) => {\n'
                '  discussion.addComment(newComment(event.detail.body), event.detail.parentId)\n'
                '})\n'
                'discussion.addEventListener("mj-comment-react", (event) => {\n'
                '  applyReaction(discussion.comments, event.detail, "u1")\n'
                '  discussion.comments = discussion.comments\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="data-source",
            title="Data source, composer on top",
            description=(
                "<p>A <code>dataSource</code> loads the newest comments and, on &ldquo;Load earlier "
                "comments&rdquo;, the older page. Posting waits for <code>post()</code> (600&nbsp;ms); "
                "tick &ldquo;Fail the next post&rdquo; to see the error, with the text kept. "
                "<code>composer-position=\"top\"</code> and a <code>composer-header</code> slot.</p>"
            ),
            html=(
                '<main>\n'
                '  <label class="fail"><input type="checkbox" id="fail-post"> Fail the next post</label>\n'
                '  <mj-comments id="remote" label="Release discussion" current-user-id="u1" composer-position="top">\n'
                '    <p slot="composer-header" class="composer-note">Commenting as <strong>You</strong> in #release-4-2</p>\n'
                '  </mj-comments>\n'
                '</main>'
            ),
            css=(
                "mj-comments { max-inline-size: 44rem; margin: var(--mj-space-4); }\n"
                ".fail { display: block; margin: var(--mj-space-4) var(--mj-space-4) 0; }\n"
                ".composer-note { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }\n"
            ),
            script=(
                _COMMENTS_SCRIPT
                + 'const remote = document.getElementById("remote")\n'
                'const fail = document.getElementById("fail-post")\n'
                'const PAGES = {\n'
                '  newest: { items: [THREAD[1], { id: "c4", authorId: "u4", authorName: "Carmen Ortiz", body: "Release notes are translated.", createdAt: minutes(20) }], cursor: "older" },\n'
                '  older: { items: [{ id: "c0", authorId: "u5", authorName: "Dmitri Volkov", body: "Kick-off: release 4.2 planning starts today.", createdAt: minutes(60 * 30) }], cursor: null }\n'
                '}\n'
                'remote.dataSource = {\n'
                '  fetch({ cursor }) {\n'
                '    mjSandbox.log("fetch", { cursor })\n'
                '    return new Promise((resolve) => setTimeout(() => resolve(PAGES[cursor === null ? "newest" : cursor]), 300))\n'
                '  },\n'
                '  post({ body, parentId }) {\n'
                '    return new Promise((resolve, reject) => setTimeout(() => {\n'
                '      if (fail.checked) { fail.checked = false; reject(new Error("offline")) } else { resolve(newComment(body)) }\n'
                '    }, 600))\n'
                '  }\n'
                '}\n'
            ),
        ),
        ComponentExample(
            key="threads",
            title="Deep threads, replies on demand",
            description=(
                "<p><code>max-depth=\"2\"</code> stops replying below the second level and "
                "<code>max-visible-replies=\"1\"</code> collapses replies. The first comment has "
                "<code>replyCount: 3</code> but only one reply loaded: &ldquo;Show more&rdquo; fires "
                "<code>mj-load-replies</code> and the script adds the missing replies.</p>"
            ),
            html='<main>\n  <mj-comments id="threads" label="Design review" current-user-id="u1" max-depth="2" max-visible-replies="1"></mj-comments>\n</main>',
            css="mj-comments { max-inline-size: 44rem; margin: var(--mj-space-4); }\n",
            script=(
                _COMMENTS_SCRIPT
                + 'const threads = document.getElementById("threads")\n'
                'threads.comments = [\n'
                '  { id: "t1", authorId: "u2", authorName: "Alice Martin", body: "Should the checkout button be full width on mobile?",\n'
                '    createdAt: minutes(300), replyCount: 3, repliesCursor: "t1-more",\n'
                '    replies: [{ ...reply("t1-r1", "u3", "Bob Lee", "Yes, it is easier to tap.", 280),\n'
                '                replies: [reply("t1-r1-a", "u2", "Alice Martin", "Agreed. Any objections?", 270)] }] }\n'
                ']\n'
                'threads.addEventListener("mj-load-replies", (event) => {\n'
                '  mjSandbox.log("loading replies", event.detail)\n'
                '  setTimeout(() => {\n'
                '    threads.addComment(reply("t1-r2", "u4", "Carmen Ortiz", "Full width below 480px, please.", 200), event.detail.commentId)\n'
                '    threads.addComment(reply("t1-r3", "u5", "Dmitri Volkov", "Tested on three phones: works.", 120), event.detail.commentId)\n'
                '  }, 300)\n'
                '})\n'
                'threads.addEventListener("mj-comment-post", (event) => threads.addComment(newComment(event.detail.body), event.detail.parentId))\n'
            ),
        ),
        ComponentExample(
            key="readonly-empty",
            title="Read-only and empty",
            description=(
                "<p>Top: an archived thread with <code>readonly</code> (no composer, no Reply / Edit / "
                "Delete; reactions would show as plain counts) and <code>allow-reactions=\"false\"</code>. Bottom: an empty thread with a "
                "custom <code>empty</code> slot.</p>"
            ),
            html=(
                '<main>\n'
                '  <mj-comments id="archived" label="Archived discussion" readonly allow-reactions="false"></mj-comments>\n'
                '  <mj-comments label="New discussion">\n'
                '    <p slot="empty" class="empty">No comments yet. Start the discussion below.</p>\n'
                '  </mj-comments>\n'
                '</main>'
            ),
            css=(
                "mj-comments { display: block; max-inline-size: 44rem; margin: var(--mj-space-4); }\n"
                ".empty { color: var(--mj-text-muted); }\n"
            ),
            script=(
                _COMMENTS_SCRIPT
                + 'document.getElementById("archived").comments = THREAD.slice(0, 2)\n'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>Wider indent, an accent thread line, larger avatars and a tinted composer through the custom properties.</p>",
            html='<main>\n  <mj-comments id="styled" label="Styled discussion" current-user-id="u1"></mj-comments>\n</main>',
            css=(
                "mj-comments {\n"
                "  max-inline-size: 44rem;\n"
                "  margin: var(--mj-space-4);\n"
                "  --mj-comments-gap: var(--mj-space-4);\n"
                "  --mj-comments-avatar-size: 40px;\n"
                "  --mj-comments-reply-indent: 3.5rem;\n"
                "  --mj-comments-thread-line: 3px solid var(--mj-accent);\n"
                "  --mj-comments-composer-bg: var(--mj-surface);\n"
                "}\n"
            ),
            script=(
                _COMMENTS_SCRIPT
                + 'const styled = document.getElementById("styled")\n'
                'styled.comments = THREAD.slice(0, 2)\n'
                'styled.addEventListener("mj-comment-post", (event) => styled.addComment(newComment(event.detail.body), event.detail.parentId))\n'
            ),
        ),
    ],
    slots=[
        ("composer-header", "Content above the top-level composer's text area.",
         "<p>Commenting as <strong>You</strong></p>"),
        ("empty", "Shown when there are no comments (default `empty-message`).",
         "<p>No comments yet. Start the discussion below.</p>"),
    ],
    properties=[
        ("comments", "object[]. The thread (see How to use); the live array. Reassign it to re-render after changing comment objects."),
        ("dataSource", "{ fetch({ cursor }) | query({ cursor }), post?({ body, parentId }) } | null. Setting it loads the first page."),
        ("cursor", "any. Cursor of the earlier page; Load earlier comments shows while it is not null."),
        ("mentionSource", "object | null. Stored for future mention support; currently unused."),
    ],
    methods=[
        ("addComment(comment, parentId)", "Adds a comment: as a reply of `parentId` (or `comment.parentId`, the thread expands), else at the top level next to the composer. A comment whose id is already in the thread is ignored."),
    ],
    parts=[
        ("root", "The component container."),
        ("count-heading", "The \"N comments\" heading."),
        ("feed-list", "The `role=\"feed\"` list."),
        ("comment", "One comment article."),
        ("comment-header", "A comment's header (author and time)."),
        ("comment-author", "The author name."),
        ("comment-time", "The time."),
        ("comment-body", "The body text."),
        ("comment-actions", "Reply, Edit and Delete."),
        ("reaction-bar", "Reaction chips and the picker button."),
        ("reply-thread", "The group of a comment's replies, inside the comment's article."),
        ("reply-composer", "The inline reply composer."),
        ("load-more-replies", "The Show more replies button."),
        ("top-composer", "The top-level composer."),
        ("load-older", "The Load earlier comments button."),
        ("empty-state", "The empty state."),
    ],
    css_properties=[
        ("--mj-comments-gap", "Space between comments (default `--mj-space-5`)."),
        ("--mj-comments-avatar-size", "Avatar size (default 32px)."),
        ("--mj-comments-reply-indent", "Indent of a reply thread (default 2.5rem)."),
        ("--mj-comments-thread-line", "Border shorthand of the reply-thread line (default `2px solid var(--mj-border)`)."),
        ("--mj-comments-composer-bg", "Composer background (default `--mj-bg-subtle`)."),
    ],
)

# ---------------------------------------------------------------------------
# Chat: a small working conversation shared by mj-chat-composer and
# mj-chat-message. The composer's mj-send appends an outgoing message, walks
# it through sent -> delivered -> read, and a teammate answers.
# ---------------------------------------------------------------------------

_CHAT_HTML = (
    '<section class="chat" aria-label="Release planning chat">\n'
    '  <div id="thread" class="thread" role="feed" aria-label="Messages">\n'
    '    <mj-chat-message variant="system" message-id="m1">Priya added you to #release-planning</mj-chat-message>\n'
    '    <mj-chat-message variant="incoming" message-id="m2" author-name="Priya Natarajan" allow-actions\n'
    '                     timestamp="2026-11-10T09:02:00Z">Morning! Is the 4.2 changelog ready for review?</mj-chat-message>\n'
    '    <mj-chat-message variant="incoming" message-id="m3" author-name="Priya Natarajan" consecutive allow-actions\n'
    '                     timestamp="2026-11-10T09:03:00Z">I would like to send it to QA before lunch.</mj-chat-message>\n'
    '  </div>\n'
    '  <mj-chat-composer id="composer" placeholder="Reply to Priya&hellip;" max-length="500"></mj-chat-composer>\n'
    '</section>'
)

_CHAT_CSS = (
    ".chat {\n"
    "  display: flex;\n"
    "  flex-direction: column;\n"
    "  gap: var(--mj-space-2);\n"
    "  max-inline-size: 40rem;\n"
    "  margin: var(--mj-space-3) auto;\n"
    "}\n"
    ".thread {\n"
    "  block-size: 300px;\n"
    "  overflow-y: auto;\n"
    "  padding-block: var(--mj-space-2);\n"
    "  border: 1px solid var(--mj-border);\n"
    "  border-radius: var(--mj-radius-lg);\n"
    "  background: var(--mj-bg-subtle);\n"
    "}\n"
)

_CHAT_SCRIPT = r'''const thread = document.getElementById("thread")
const composer = document.getElementById("composer")
const CURRENT_USER = "u-you"
let sequence = thread.children.length
const ANSWERS = ["Thanks! I will take a look now.", "Perfect, sending it to QA.", "Got it \u{1F44D}"]
let answered = 0

/* Recent timestamps so the relative times read naturally. */
const minutesAgo = [12, 9, 8]
Array.from(thread.children).forEach((message, index) => {
  if (message.hasAttribute("timestamp")) {
    message.setAttribute("timestamp", new Date(Date.now() - minutesAgo[index] * 60000).toISOString())
  }
})

function addMessage(options) {
  sequence = sequence + 1
  const message = document.createElement("mj-chat-message")
  const previous = thread.lastElementChild
  message.setAttribute("variant", options.variant)
  message.setAttribute("message-id", "m" + sequence)
  message.setAttribute("author-name", options.author)
  message.setAttribute("timestamp", new Date().toISOString())
  message.setAttribute("allow-actions", "")
  if (options.status) {
    message.setAttribute("status", options.status)
  }
  if (previous && previous.getAttribute("variant") === options.variant &&
      previous.getAttribute("author-name") === options.author) {
    message.setAttribute("consecutive", "")
  }
  message.textContent = options.text
  thread.appendChild(message)
  message.currentUserId = CURRENT_USER
  if (options.replyTo) {
    message.replyTo = options.replyTo
  }
  if (options.attachments && options.attachments.length > 0) {
    message.attachments = options.attachments
  }
  thread.scrollTop = thread.scrollHeight
  return message
}

/* Reply in the thread: the composer shows what is being answered. */
thread.addEventListener("mj-message-reply", (event) => {
  const original = thread.querySelector(`[message-id="${event.detail.messageId}"]`)
  composer.replyTo = { messageId: event.detail.messageId, preview: original.textContent.trim() }
  composer.focus()
})

composer.addEventListener("mj-send", (event) => {
  const detail = event.detail
  const replied = detail.replyTo ? thread.querySelector(`[message-id="${detail.replyTo}"]`) : null
  const attachments = detail.attachments.map((entry) => ({
    name: entry.file.name,
    size: entry.file.size,
    mimeType: entry.file.type,
    thumbnailUrl: entry.file.type.startsWith("image/") ? URL.createObjectURL(entry.file) : undefined
  }))
  const sent = addMessage({
    variant: "outgoing", author: "You", status: "sent", text: detail.value, attachments: attachments,
    replyTo: replied ? { messageId: detail.replyTo, authorName: replied.getAttribute("author-name"),
                         preview: replied.textContent.trim() } : null
  })
  mjSandbox.log("sent", { value: detail.value, attachments: attachments.length, replyTo: detail.replyTo })
  setTimeout(() => sent.setAttribute("status", "delivered"), 700)
  setTimeout(() => sent.setAttribute("status", "read"), 1500)
  const answer = ANSWERS[answered % ANSWERS.length]
  answered = answered + 1
  setTimeout(() => addMessage({ variant: "incoming", author: "Priya Natarajan", text: answer }), 2200)
})
'''


_PEOPLE_SCRIPT = r'''const people = [
  { id: "u1", displayName: "Alice Martin", subtitle: "Engineering" },
  { id: "u2", displayName: "Bob Lee", subtitle: "Design" },
  { id: "u3", displayName: "Carmen Ortiz", subtitle: "Product" },
  { id: "u4", displayName: "Dmitri Volkov", subtitle: "Quality assurance" }
]
const channels = [
  { id: "c1", displayName: "release-planning", subtitle: "12 members", type: "channel" },
  { id: "c2", displayName: "design-reviews", subtitle: "8 members", type: "channel" },
  { id: "c3", displayName: "incidents", subtitle: "31 members", type: "channel" }
]
const mentionSource = {
  suggest(trigger, query) {
    const pool = trigger === "#" ? channels : people
    const needle = query.toLowerCase()
    return Promise.resolve(pool.filter((entry) => entry.displayName.toLowerCase().includes(needle)))
  }
}
'''


MENTION_INPUT = ComponentDoc(
    tag="mj-mention-input",
    title="Mention Input",
    group="productivity",
    summary="Form-associated text field that turns @people and #channels into inline mention tokens.",
    description=(
        "<p><code>&lt;mj-mention-input&gt;</code> is a plain-text, content-editable field "
        "(<code>contenteditable=\"plaintext-only\"</code> where supported) with "
        "<code>role=\"textbox\"</code>. When a trigger character (default <code>@</code> and "
        "<code>#</code>) starts a word and is followed by at least "
        "<code>min-trigger-length</code> characters, it asks the <code>mentionSource</code> "
        "for suggestions (debounced by 200&nbsp;ms) and shows them in a listbox under the "
        "field with the first one highlighted. Choosing one replaces the typed "
        "<code>@query</code> with a non-editable token followed by a space. Backspace or "
        "Delete next to a token removes it whole. A trigger inside a word "
        "(<code>a@b.com</code>) is ignored.</p>"
        "<p>The element is form-associated: under <code>name</code> it submits "
        "<code>value</code>, the plain text with each token written as its visible text "
        "(<code>@Alice Martin</code>) and line breaks as <code>\\n</code>; mention ids are "
        "not submitted, read them from <code>mentions</code>. <code>required</code> and "
        "<code>max-length</code> take part in constraint validation; typing and pasting "
        "beyond <code>max-length</code> is refused and a counter is shown. "
        "<code>disabled</code> (or a disabled fieldset) makes the field non-editable and "
        "non-focusable; <code>readonly</code> keeps it focusable for reading and copying.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>mentionSource</code> an object with "
        "<code>suggest(trigger, query)</code> returning (a promise of) suggestions "
        "<code>{ id, displayName, subtitle?, avatarUrl?, type? }</code>; an empty array shows "
        "&ldquo;No matches&rdquo;. Use <kbd>ArrowUp</kbd>/<kbd>ArrowDown</kbd> to move the "
        "highlight, <kbd>Enter</kbd> or a click to insert, <kbd>Escape</kbd> or "
        "<kbd>Tab</kbd> to dismiss. Without the popup, <kbd>Enter</kbd> fires the "
        "cancelable <code>mj-submit</code>; in a multiline field <kbd>Shift</kbd>+"
        "<kbd>Enter</kbd> inserts a line break (a single-line field, "
        "<code>multiline=\"false\"</code>, never takes one). <code>mj-input</code> reports "
        "every change, <code>mj-change</code> the value on blur. Set "
        "<code>min-trigger-length=\"0\"</code> to open the popup on the bare trigger.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", description="Visible label above the field; also its accessible name.",
                     kind="string", values=["Message", "Comment"]),
        AttributeDoc(name="placeholder", description="Placeholder shown while empty (the accessible name when there is no label).",
                     kind="string"),
        AttributeDoc(name="triggers", description="Characters that start a mention, as one string.",
                     kind="string", values=["@#", "@", "#"], default="@#"),
        AttributeDoc(name="min-trigger-length",
                     description="Characters needed after the trigger before suggestions are requested; read on each keystroke.",
                     kind="number", default="1"),
        AttributeDoc(name="multiline", description="`false` makes a single-line field: Enter always submits and pasted line breaks become spaces.",
                     kind="boolean", default="true"),
        AttributeDoc(name="max-length", description="Maximum characters (tokens count as their text); shows an `n / max` counter and refuses longer input.",
                     kind="number"),
        AttributeDoc(name="name", description="Form field name; the plain-text value is submitted under it.", kind="string"),
        AttributeDoc(name="value", description="Initial plain-text content, also restored by a form reset. Read at first render.",
                     kind="string"),
        AttributeDoc(name="required", description="The field is invalid (`valueMissing`) while empty.", kind="boolean"),
        AttributeDoc(name="required-message", description="Validation message used instead of the default when required and empty.",
                     kind="string"),
        AttributeDoc(name="disabled", description="Not editable and not focusable; `aria-disabled`. A disabled fieldset has the same effect.",
                     kind="boolean"),
        AttributeDoc(name="readonly", description="Not editable but still focusable; `aria-readonly`.", kind="boolean"),
    ],
    events=[
        ("mj-input", "The content changed (typing, a token inserted or removed).",
         "{ value: string, mentions: Mention[] }"),
        ("mj-change", "Focus left the field and the value differs from the last committed one.",
         "{ value: string, mentions: Mention[] }"),
        ("mj-submit", "Enter was pressed with no suggestion highlighted (cancelable).",
         "{ value: string, mentions: Mention[] }"),
        ("mj-mention-trigger", "A trigger plus query was detected (before suggestions are fetched).",
         "{ trigger: string, query: string }"),
        ("mj-mention-select", "A suggestion was chosen; the token is inserted right after.",
         "{ trigger: string, suggestion: object }"),
        ("mj-mention-cancel", "The suggestions were dismissed without a choice (Escape, Tab, blur).",
         "{ trigger: string }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="People and channels",
            description=(
                "<p>Type <kbd>@</kbd> for a person or <kbd>#</kbd> for a channel (the popup opens "
                "on the bare trigger here because <code>min-trigger-length=\"0\"</code>). Pick with "
                "the arrows and <kbd>Enter</kbd>; press <kbd>Enter</kbd> again to submit. The line "
                "below echoes <code>value</code> and <code>mentions</code>.</p>"
            ),
            html=(
                '<mj-mention-input id="message" label="Message" min-trigger-length="0"\n'
                '                  placeholder="Type @ to mention someone or # for a channel"></mj-mention-input>\n'
                '<p class="echo">value: <code id="echo-value">""</code><br>mentions: <code id="echo-mentions">[]</code></p>'
            ),
            css=(
                "mj-mention-input { max-inline-size: 32rem; margin: var(--mj-space-4); }\n"
                ".echo { margin-inline: var(--mj-space-4); color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
            ),
            script=(
                _PEOPLE_SCRIPT
                + 'const field = document.getElementById("message")\n'
                'field.mentionSource = mentionSource\n'
                'field.addEventListener("mj-input", (event) => {\n'
                '  document.getElementById("echo-value").textContent = JSON.stringify(event.detail.value)\n'
                '  document.getElementById("echo-mentions").textContent =\n'
                '    JSON.stringify(event.detail.mentions.map((m) => m.trigger + m.id))\n'
                '})\n'
                'field.addEventListener("mj-submit", (event) => {\n'
                '  mjSandbox.log("submitted", { value: event.detail.value, mentions: event.detail.mentions.length })\n'
                '  field.value = ""\n'
                '})\n'
            ),
            height=320,
        ),
        ComponentExample(
            key="form",
            title="In a form",
            description=(
                "<p>A single-line, <code>required</code> field with <code>max-length=\"60\"</code> "
                "inside a <code>&lt;form&gt;</code>. Submit while empty to see the validation; "
                "a valid submit shows the <code>FormData</code> entry (plain text, no ids). "
                "Reset restores the <code>value</code> attribute.</p>"
            ),
            html=(
                '<form id="task-form" class="task-form">\n'
                '  <mj-mention-input name="task" label="Task title" multiline="false" required max-length="60"\n'
                '                    value="Review the changelog with " placeholder="Assign with @"></mj-mention-input>\n'
                '  <div class="row">\n'
                '    <button type="submit">Create task</button>\n'
                '    <button type="reset">Reset</button>\n'
                '  </div>\n'
                '  <output id="submitted"></output>\n'
                '</form>'
            ),
            css=(
                ".task-form { display: grid; gap: var(--mj-space-2); max-inline-size: 32rem; margin: var(--mj-space-4); }\n"
                ".row { display: flex; gap: var(--mj-space-2); }\n"
                "output { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
            ),
            script=(
                _PEOPLE_SCRIPT
                + 'const form = document.getElementById("task-form")\n'
                'form.querySelector("mj-mention-input").mentionSource = mentionSource\n'
                'form.addEventListener("submit", (event) => {\n'
                '  event.preventDefault()\n'
                '  const task = new FormData(form).get("task")\n'
                '  document.getElementById("submitted").textContent = "Submitted task = " + JSON.stringify(task)\n'
                '  mjSandbox.log("form submit", { task: task })\n'
                '})\n'
            ),
            height=300,
        ),
        ComponentExample(
            key="states",
            title="Disabled and read-only",
            description=(
                "<p><code>disabled</code> cannot be focused or edited; <code>readonly</code> can be "
                "focused and its text selected but not changed. The third field counts toward "
                "<code>max-length=\"40\"</code>.</p>"
            ),
            html=(
                '<div class="stack">\n'
                '  <mj-mention-input label="Disabled" disabled value="Waiting for approval"></mj-mention-input>\n'
                '  <mj-mention-input label="Read-only" readonly value="Shipped in release 4.1"></mj-mention-input>\n'
                '  <mj-mention-input label="Short note" max-length="40" placeholder="At most 40 characters"></mj-mention-input>\n'
                '</div>'
            ),
            css=".stack { display: grid; gap: var(--mj-space-4); max-inline-size: 32rem; margin: var(--mj-space-4); }\n",
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description=(
                "<p>The custom properties and <code>::part(token)</code> restyle the field and its "
                "tokens; the field starts with a token inserted by the script through the popup.</p>"
            ),
            html=(
                '<mj-mention-input id="styled" label="Hand-off note" min-trigger-length="0"\n'
                '                  placeholder="Mention a teammate"></mj-mention-input>'
            ),
            css=(
                "mj-mention-input {\n"
                "  max-inline-size: 32rem;\n"
                "  margin: var(--mj-space-4);\n"
                "  --mj-mention-border: var(--mj-accent);\n"
                "  --mj-mention-min-height: 5rem;\n"
                "  --mj-mention-token-bg: var(--mj-color-success-subtle, var(--mj-bg-muted));\n"
                "  --mj-mention-token-color: var(--mj-text);\n"
                "  --mj-mention-token-radius: var(--mj-radius-pill);\n"
                "}\n"
                "mj-mention-input::part(token) { padding-inline: var(--mj-space-2); font-weight: var(--mj-font-weight-medium); }\n"
                "mj-mention-input::part(label) { text-transform: uppercase; letter-spacing: 0.05em; }\n"
            ),
            script=(
                _PEOPLE_SCRIPT
                + 'const field = document.getElementById("styled")\n'
                'field.mentionSource = mentionSource\n'
            ),
            height=280,
        ),
    ],
    slots=[],
    properties=[
        ("value", "string. Plain text; tokens as their visible text (`@Alice Martin`), line breaks as `\\n`. Setting it replaces the content with plain text (tokens are dropped) and emits no event."),
        ("mentions", "Mention[], read-only. `{ trigger, id, displayName, type }` for every token in the field, in order (`type` defaults to `user`)."),
        ("mentionSource", "{ suggest(trigger, query) } | null. Supplies suggestions; without it no popup opens."),
        ("form", "HTMLFormElement | null, read-only. The owning form."),
        ("validity", "ValidityState, read-only. `valueMissing` (required) or `customError` (over max-length)."),
        ("validationMessage", "string, read-only. The current validation message."),
    ],
    methods=[
        ("focus(options)", "Focuses the editable field."),
        ("checkValidity() -> boolean", "Runs constraint validation (fires `invalid` when it fails)."),
        ("reportValidity() -> boolean", "Like checkValidity() and shows the browser message."),
    ],
    parts=[
        ("label", "The visible label (hidden when `label` is empty)."),
        ("editable", "The content-editable textbox."),
        ("token", "Each inserted mention token."),
        ("counter", "The `n / max` counter (shown with `max-length`)."),
        ("suggestion-popup", "The suggestions listbox."),
        ("suggestion-item", "One suggestion option."),
    ],
    css_properties=[
        ("--mj-mention-border", "Field border colour (default `--mj-border-strong`)."),
        ("--mj-mention-focus-ring", "Border colour while focused (default `--mj-focus-ring`)."),
        ("--mj-mention-min-height", "Minimum field height (default `--mj-control-height-md`)."),
        ("--mj-mention-max-height", "Height after which the field scrolls (default 200px)."),
        ("--mj-mention-token-bg", "Token background (default 12% accent)."),
        ("--mj-mention-token-color", "Token text colour (default `--mj-accent`)."),
        ("--mj-mention-token-radius", "Token corner radius (default `--mj-radius-sm`)."),
    ],
)


CHAT_COMPOSER = ComponentDoc(
    tag="mj-chat-composer",
    title="Chat Composer",
    group="productivity",
    summary="Message-entry bar with a growing text area, attachments, a built-in emoji panel, a reply strip and a send button with a loading state.",
    description=(
        "<p><code>&lt;mj-chat-composer&gt;</code> is the input bar under a chat thread "
        "(<code>role=\"form\"</code>). The text area grows with its content up to "
        "<code>--mj-composer-max-height</code>. <kbd>Enter</kbd> sends and "
        "<kbd>Shift</kbd>+<kbd>Enter</kbd> adds a line, or with "
        "<code>send-key=\"ctrl+enter\"</code> <kbd>Ctrl</kbd>/<kbd>Cmd</kbd>+<kbd>Enter</kbd> "
        "sends and <kbd>Enter</kbd> adds a line. The Send button is "
        "<code>aria-disabled</code> until there is text or an attachment. Sending fires the "
        "cancelable <code>mj-send</code>; unless it is cancelled the composer clears itself "
        "(text, attachments and reply strip).</p>"
        "<p>Files come from the attach button (one file per pick), a paste or a drop on the "
        "composer and appear as chips (image thumbnails for images) with a remove button; "
        "files that fail <code>accept</code> or <code>max-attachment-size</code> are shown as "
        "error chips and reported with <code>mj-attachment-reject</code>. "
        "<code>updateAttachment()</code> shows upload progress or an error on a chip. The emoji "
        "button fires the cancelable <code>mj-emoji-request</code>; unless cancelled it opens "
        "a built-in panel of twelve emoji that inserts at the caret "
        "(<kbd>ArrowLeft</kbd>/<kbd>ArrowRight</kbd>, <kbd>Escape</kbd>). Setting "
        "<code>replyTo</code> shows a &ldquo;Replying to&hellip;&rdquo; strip; its close button "
        "or <kbd>Escape</kbd> cancels it. <code>max-length</code> limits typing and shows a "
        "counter. <code>loading</code> makes the text read-only and shows a spinner; "
        "<code>disabled</code> disables the whole bar. Mention tokens are not produced yet: "
        "<code>mentions</code> is always empty.</p>"
    ),
    how_to_use=(
        "<p>Listen for <code>mj-send</code>: its detail has the <code>value</code>, the "
        "<code>attachments</code> entries (<code>{ id, file: File, status, progress }</code>) "
        "and <code>replyTo</code> (the replied message id or <code>null</code>). Append the "
        "message to your thread; call <code>event.preventDefault()</code> to keep the text "
        "(for example to send asynchronously: set <code>loading</code>, then "
        "<code>clear()</code> when done). To reply to a message set <code>replyTo = { "
        "messageId, preview }</code>. Insert canned text with <code>insertText()</code>. Put "
        "extra buttons in the <code>toolbar-start</code> and <code>toolbar-end</code> slots. "
        "<code>allow-attachments=\"false\"</code> and <code>allow-emoji=\"false\"</code> hide "
        "those buttons.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="placeholder", description="Placeholder of the text area.", kind="string",
                     default="Type a message…"),
        AttributeDoc(name="label", description="Accessible name of the composer and its text area.", kind="string",
                     default="Message composer"),
        AttributeDoc(name="send-key", description="`enter`: Enter sends (Shift+Enter new line); `ctrl+enter`: Ctrl/Cmd+Enter sends.",
                     kind="enum", values=["enter", "ctrl+enter"], default="enter"),
        AttributeDoc(name="max-length", description="Maximum characters; typing stops there and a `n / max` counter is shown.",
                     kind="number"),
        AttributeDoc(name="allow-attachments", description="`false` hides the attach button and ignores pasted or dropped files.",
                     kind="boolean", default="true"),
        AttributeDoc(name="allow-emoji", description="`false` hides the emoji button.", kind="boolean", default="true"),
        AttributeDoc(name="accept", description="Accepted attachment types (MIME types, `type/*` groups or extensions).",
                     kind="string", values=["image/*", ".pdf,.docx", "image/*,application/pdf"]),
        AttributeDoc(name="max-attachment-size", description="Maximum bytes per attachment; larger files become error chips.",
                     kind="number"),
        AttributeDoc(name="loading", description="Sending in progress: spinner on Send, text read-only, sending blocked.",
                     kind="boolean"),
        AttributeDoc(name="disabled", description="Disables the text area and every button.", kind="boolean"),
    ],
    events=[
        ("mj-send", "Send was activated with content (cancelable: cancel to keep the text).",
         "{ value: string, mentions: [], attachments: [{ id, file, status, progress, error }], replyTo: string | null }"),
        ("mj-input", "The text changed (typing, insertText(), an emoji).", "{ value: string, mentions: [] }"),
        ("mj-emoji-request", "The emoji button was pressed (cancelable: cancel to show your own picker).", "{}"),
        ("mj-attachment-add", "Files were attached.", "{ files: [{ id, file, status, progress, error, previewUrl }] }"),
        ("mj-attachment-reject", "Files failed `accept` or `max-attachment-size`.",
         "{ rejectedFiles: [{ id, file, reason }] }"),
        ("mj-attachment-remove", "An attachment chip was removed.", "{ fileId: string }"),
        ("mj-reply-cancel", "The reply strip was dismissed.", "{}"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="A working conversation",
            description=(
                "<p>Type and press <kbd>Enter</kbd>: the script turns each <code>mj-send</code> into "
                "an outgoing <code>mj-chat-message</code> (sent, then delivered, then read) and "
                "Priya answers. Attach a file or pick an emoji before sending. Open a message's "
                "&hellip; menu and choose Reply to quote it in the composer.</p>"
            ),
            html=_CHAT_HTML,
            css=_CHAT_CSS,
            script=_CHAT_SCRIPT,
        ),
        ComponentExample(
            key="attachments",
            title="Attachments and upload progress",
            description=(
                "<p>The script drops three files on the composer: an image (thumbnail chip), a PDF "
                "that uploads with progress through <code>updateAttachment()</code>, and a video "
                "over <code>max-attachment-size=\"5000000\"</code> that becomes an error chip. A "
                "reply strip is set through <code>replyTo</code>.</p>"
            ),
            html='<mj-chat-composer id="uploads" max-attachment-size="5000000" placeholder="Add a caption&hellip;"></mj-chat-composer>',
            css="mj-chat-composer { max-inline-size: 40rem; margin: var(--mj-space-4); }\n",
            script=(
                'const composer = document.getElementById("uploads")\n'
                'function pixel() {\n'
                '  const canvas = document.createElement("canvas")\n'
                '  canvas.width = 48\n'
                '  canvas.height = 48\n'
                '  const context = canvas.getContext("2d")\n'
                '  context.fillStyle = "#3b82f6"\n'
                '  context.fillRect(0, 0, 48, 48)\n'
                '  return new Promise((resolve) => canvas.toBlob(resolve, "image/png"))\n'
                '}\n'
                'const image = new File([await pixel()], "whiteboard.png", { type: "image/png" })\n'
                'const pdf = new File([new Uint8Array(240000)], "minutes.pdf", { type: "application/pdf" })\n'
                'const video = new File([new Uint8Array(6000000)], "recording.mp4", { type: "video/mp4" })\n'
                'composer.addEventListener("mj-attachment-add", (event) => {\n'
                '  const entry = event.detail.files.find((item) => item.file.name === "minutes.pdf")\n'
                '  if (entry === undefined) { return }\n'
                '  let progress = 0\n'
                '  const timer = setInterval(() => {\n'
                '    progress = progress + 20\n'
                '    composer.updateAttachment(entry.id, { status: progress >= 100 ? "done" : "uploading", progress: progress })\n'
                '    if (progress >= 100) { clearInterval(timer) }\n'
                '  }, 400)\n'
                '})\n'
                '/* Simulate the user dropping the files on the composer. */\n'
                'const transfer = new DataTransfer()\n'
                ';[image, pdf, video].forEach((file) => transfer.items.add(file))\n'
                'composer.shadowRoot.querySelector("[part=root]").dispatchEvent(\n'
                '  new DragEvent("drop", { dataTransfer: transfer, bubbles: true, cancelable: true }))\n'
                'composer.replyTo = { messageId: "m42", preview: "Can you share the whiteboard from the retro?" }\n'
            ),
        ),
        ComponentExample(
            key="states",
            title="Send key, limits and states",
            description=(
                "<p>First: <code>send-key=\"ctrl+enter\"</code> (<kbd>Enter</kbd> adds a line) with "
                "<code>max-length=\"120\"</code> and no attach or emoji buttons. Second: "
                "<code>loading</code> while a message is sent. Third: <code>disabled</code>.</p>"
            ),
            html=(
                '<div class="stack">\n'
                '  <mj-chat-composer id="ctrl-enter" send-key="ctrl+enter" max-length="120" allow-attachments="false"\n'
                '                    allow-emoji="false" placeholder="Ctrl+Enter to send"></mj-chat-composer>\n'
                '  <mj-chat-composer id="busy" loading placeholder="Sending&hellip;"></mj-chat-composer>\n'
                '  <mj-chat-composer disabled placeholder="This conversation is archived"></mj-chat-composer>\n'
                '</div>'
            ),
            css=".stack { display: grid; gap: var(--mj-space-4); max-inline-size: 40rem; margin: var(--mj-space-4); }\n",
            script=(
                'document.getElementById("busy").value = "Uploading the build logs now"\n'
                'document.getElementById("ctrl-enter").addEventListener("mj-send", (event) => {\n'
                '  mjSandbox.log("sent with Ctrl+Enter", { value: event.detail.value })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="toolbar-slots",
            title="Toolbar slots and a custom picker",
            description=(
                "<p>The <code>toolbar-start</code> slot holds canned replies that call "
                "<code>insertText()</code>; <code>toolbar-end</code> a button that sends "
                "asynchronously: it cancels <code>mj-send</code>, shows <code>loading</code> for a "
                "second and then calls <code>clear()</code>. The script cancels "
                "<code>mj-emoji-request</code> and shows its own reaction row instead of the "
                "built-in panel.</p>"
            ),
            html=(
                '<mj-chat-composer id="support" placeholder="Reply to the customer&hellip;">\n'
                '  <button slot="toolbar-start" type="button" class="canned" data-text="Thanks for reaching out! ">Greeting</button>\n'
                '  <button slot="toolbar-start" type="button" class="canned" data-text="Could you send a screenshot of the error? ">Ask for screenshot</button>\n'
                '  <button slot="toolbar-end" type="button" id="internal">Send as internal note</button>\n'
                '</mj-chat-composer>\n'
                '<div id="picker" class="picker" hidden>\n'
                '  <button type="button">&#x2705;</button> <button type="button">&#x1F64C;</button> <button type="button">&#x1F680;</button>\n'
                '</div>'
            ),
            css=(
                "mj-chat-composer { max-inline-size: 40rem; margin: var(--mj-space-4); }\n"
                ".canned, #internal { font-size: var(--mj-font-size-xs); }\n"
                ".picker { display: flex; gap: var(--mj-space-1); margin-inline: var(--mj-space-4); }\n"
                ".picker[hidden] { display: none; }\n"
            ),
            script=(
                'const composer = document.getElementById("support")\n'
                'const picker = document.getElementById("picker")\n'
                'let internal = false\n'
                'composer.querySelectorAll(".canned").forEach((button) => {\n'
                '  button.addEventListener("click", () => { composer.insertText(button.dataset.text); composer.focus() })\n'
                '})\n'
                'document.getElementById("internal").addEventListener("click", () => {\n'
                '  internal = true\n'
                '  composer.shadowRoot.querySelector("[part=send-button]").click()\n'
                '})\n'
                'composer.addEventListener("mj-send", (event) => {\n'
                '  event.preventDefault()\n'
                '  composer.setAttribute("loading", "")\n'
                '  mjSandbox.log(internal ? "internal note" : "reply", { value: event.detail.value })\n'
                '  internal = false\n'
                '  setTimeout(() => { composer.removeAttribute("loading"); composer.clear() }, 1000)\n'
                '})\n'
                'composer.addEventListener("mj-emoji-request", (event) => {\n'
                '  event.preventDefault()\n'
                '  picker.hidden = !picker.hidden\n'
                '})\n'
                'picker.addEventListener("click", (event) => {\n'
                '  if (event.target.localName === "button") { composer.insertText(event.target.textContent); picker.hidden = true }\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>Rounded, taller composer with its own background and border through the custom properties.</p>",
            html='<mj-chat-composer placeholder="Write something nice&hellip;"></mj-chat-composer>',
            css=(
                "mj-chat-composer {\n"
                "  max-inline-size: 40rem;\n"
                "  margin: var(--mj-space-4);\n"
                "  --mj-composer-bg: var(--mj-bg-subtle);\n"
                "  --mj-composer-border: var(--mj-accent);\n"
                "  --mj-composer-radius: var(--mj-radius-pill, 999px);\n"
                "  --mj-composer-min-height: 48px;\n"
                "  --mj-composer-toolbar-gap: var(--mj-space-2);\n"
                "}\n"
                "mj-chat-composer::part(send-button) { border-radius: var(--mj-radius-pill, 999px); }\n"
            ),
        ),
    ],
    slots=[
        ("toolbar-start", "Buttons before the attach and emoji buttons.",
         '<button type="button">Greeting</button>'),
        ("toolbar-end", "Buttons after the attach and emoji buttons.",
         '<button type="button">Schedule</button>'),
    ],
    properties=[
        ("value", "string. The text; setting it replaces the text without an event."),
        ("attachments", "object[], read-only. Attached entries `{ id, file: File, status, progress, error, previewUrl }`."),
        ("replyTo", "{ messageId, preview } | null. Shows the reply strip; `mj-send` reports its messageId."),
        ("mentions", "[], read-only. Always empty (mention tokens are not produced yet)."),
        ("mentionSource", "object | null. Stored for future mention support; currently unused."),
    ],
    methods=[
        ("insertText(text)", "Inserts text at the caret (cut at `max-length`) and fires mj-input."),
        ("updateAttachment(id, { status, progress, error })", "Shows `uploading` progress (0-100), clears it for `done`, or shows `error` on a chip."),
        ("clear()", "Empties the text, attachments, error chips and reply strip."),
        ("focus(options)", "Focuses the text area."),
    ],
    parts=[
        ("root", "The composer (`role=\"form\"`)."),
        ("reply-preview", "The reply strip."),
        ("reply-preview-text", "The reply strip text."),
        ("reply-cancel", "The reply strip close button."),
        ("attachment-bar", "The attachment chips."),
        ("attachment-item", "One attachment or error chip."),
        ("attachment-remove", "A chip's remove button."),
        ("input", "The text area."),
        ("counter", "The `n / max` counter."),
        ("toolbar", "The button row."),
        ("attach-button", "The attach button."),
        ("emoji-button", "The emoji button."),
        ("send-button", "The Send button."),
    ],
    css_properties=[
        ("--mj-composer-bg", "Background (default `--mj-surface`)."),
        ("--mj-composer-border", "Border colour (default `--mj-border`)."),
        ("--mj-composer-radius", "Corner radius (default `--mj-radius-lg`)."),
        ("--mj-composer-min-height", "Minimum text-area height (default `--mj-control-height-md`)."),
        ("--mj-composer-max-height", "Height at which the text area stops growing and scrolls (default 200px)."),
        ("--mj-composer-toolbar-gap", "Gap between toolbar buttons (default `--mj-space-1`)."),
        ("--mj-composer-attachment-size", "Image thumbnail size (default 56px)."),
        ("--mj-composer-attachment-max-width", "Maximum chip width (default 240px)."),
    ],
)


CHAT_MESSAGE = ComponentDoc(
    tag="mj-chat-message",
    title="Chat Message",
    group="productivity",
    summary="One chat bubble: incoming, outgoing with delivery status, or system; with reply quote, attachments, reactions and an actions menu.",
    description=(
        "<p><code>&lt;mj-chat-message&gt;</code> renders a single message as an "
        "<code>&lt;article&gt;</code>. <code>incoming</code> (default) shows an avatar (image "
        "from <code>author-avatar</code>, else initials) and a header with author and time; "
        "<code>outgoing</code> is aligned to the inline end in the accent colour with a "
        "delivery indicator (<code>sent</code> &#10003;, <code>delivered</code> and "
        "<code>read</code> &#10003;&#10003;, <code>failed</code> &#9888;); <code>system</code> is "
        "a centred pill. <code>consecutive</code> hides the avatar and header for follow-ups "
        "from the same author. The timestamp is shown relative (refreshed every minute, the full "
        "date as tooltip); text that is not a date is shown as given. Attribute changes after "
        "render are applied.</p>"
        "<p>The body is the <code>body</code> slot or, when it is empty, the default slot. "
        "Assigning <code>bodyHtml</code> replaces it with sanitized HTML: only <code>b</code>, "
        "<code>i</code>, <code>em</code>, <code>strong</code>, <code>a</code> "
        "(<code>href</code>, <code>title</code>; script, <code>data:</code> and "
        "<code>blob:</code> links dropped; <code>rel=\"noopener noreferrer\"</code> forced), "
        "<code>br</code>, <code>p</code>, <code>span</code>, <code>mark</code>, "
        "<code>code</code> and <code>pre</code> survive, without any other attribute; other "
        "wrappers are unwrapped. Link clicks fire the cancelable "
        "<code>mj-message-link-click</code>. <code>replyTo</code> shows a quote above the body, "
        "<code>attachments</code> shows image thumbnails or file links with sizes, and "
        "<code>reactions</code> shows chips (pressed when <code>currentUserId</code> is among "
        "the <code>userIds</code>; clicking toggles the pressed state and fires "
        "<code>mj-message-react</code>, the page updates the counts).</p>"
        "<p>With <code>allow-actions</code> an &hellip; button (visible on hover or focus) opens "
        "a menu: Reply and Copy text, plus Edit and Delete for outgoing messages and Retry "
        "for a failed one. The menu only reports the choice (<code>mj-message-reply</code> or "
        "<code>mj-message-action</code>); it supports <kbd>ArrowUp</kbd>/<kbd>ArrowDown</kbd>, "
        "<kbd>Home</kbd>, <kbd>End</kbd> and <kbd>Escape</kbd> (focus returns to the "
        "button).</p>"
    ),
    how_to_use=(
        "<p>Put messages in a <code>role=\"feed\"</code> (or <code>role=\"log\"</code>) "
        "container. Create one per message with <code>variant</code>, "
        "<code>message-id</code>, <code>author-name</code>, <code>timestamp</code> (ISO 8601) "
        "and, for your own messages, <code>status</code>; put plain text in it (default slot) "
        "or assign <code>bodyHtml</code> for formatted text. The properties "
        "<code>replyTo</code> (<code>{ messageId, authorName, preview }</code>), "
        "<code>attachments</code> (<code>[{ name, url?, mimeType?, size?, thumbnailUrl? "
        "}]</code>), <code>reactions</code> (<code>[{ emoji, count, userIds }]</code>) and "
        "<code>currentUserId</code> can be set before or after the element is connected. "
        "Reactions are on unless <code>allow-reactions=\"false\"</code>. Handle the menu "
        "events yourself (copy to the clipboard, edit, delete, resend).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="variant", description="Layout: incoming (avatar at the start), outgoing (end, with status) or system (centred pill).",
                     kind="enum", values=["incoming", "outgoing", "system"], default="incoming"),
        AttributeDoc(name="author-name", description="Author shown in the header; also the source of the avatar initials.",
                     kind="string"),
        AttributeDoc(name="author-avatar", description="Avatar image URL (http(s), relative, or a data:image PNG/JPEG/GIF/WebP); else initials.",
                     kind="string"),
        AttributeDoc(name="timestamp", description="When the message was sent (ISO 8601 or YYYY-MM-DD); shown relative.",
                     kind="string"),
        AttributeDoc(name="status", description="Delivery state of an outgoing message (unknown values show as sent).",
                     kind="enum", values=["sent", "delivered", "read", "failed"], default="sent"),
        AttributeDoc(name="message-id", description="Id reported in every event of this message.", kind="string"),
        AttributeDoc(name="author-id", description="Id of the author, reported as `authorId` in every event of this message (nothing is rendered from it).",
                     kind="string"),
        AttributeDoc(name="consecutive", description="Hides avatar and header for a follow-up from the same author.",
                     kind="boolean"),
        AttributeDoc(name="allow-actions", description="Shows the actions button and its menu (`false` hides it).",
                     kind="boolean"),
        AttributeDoc(name="allow-reactions", description="`false` hides the reaction chips.", kind="boolean", default="true"),
    ],
    events=[
        ("mj-message-reply", "Reply was chosen in the actions menu.", "{ messageId: string, authorId: string }"),
        ("mj-message-action", "Copy text, Edit, Delete or Retry was chosen.",
         "{ messageId: string, authorId: string, action: 'copy' | 'edit' | 'delete' | 'retry' }"),
        ("mj-message-react", "A reaction chip was toggled (counts are not changed).",
         "{ messageId: string, authorId: string, emoji: string, active: boolean }"),
        ("mj-message-link-click", "A link in the bodyHtml was clicked (cancelable: cancel to stop navigation).",
         "{ href: string, messageId: string, authorId: string }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Incoming, outgoing and system messages in a feed. The first message has "
                "reactions and an actions menu (hover or focus it, then &hellip;); the second is a "
                "<code>consecutive</code> follow-up; the outgoing one shows <code>status=\"read\"</code>. "
                "Clicking a reaction logs <code>mj-message-react</code> (with the message's "
                "<code>author-id</code> as <code>authorId</code>) and the script updates the "
                "count.</p>"
            ),
            html=(
                '<div class="thread" role="feed" aria-label="Chat with Alice">\n'
                '  <mj-chat-message variant="incoming" author-name="Alice Martin" author-id="u2" message-id="m1"\n'
                '                   timestamp="2026-11-10T09:00:00Z" allow-reactions allow-actions>\n'
                '    <span slot="body">Hey, how is the project going?</span>\n'
                '  </mj-chat-message>\n'
                '  <mj-chat-message variant="incoming" author-name="Alice Martin" message-id="m2"\n'
                '                   timestamp="2026-11-10T09:00:30Z" consecutive>The demo is on Thursday.</mj-chat-message>\n'
                '  <mj-chat-message variant="outgoing" author-name="You" message-id="m3"\n'
                '                   timestamp="2026-11-10T09:01:00Z" status="read" allow-actions>Going great &mdash; almost done!</mj-chat-message>\n'
                '  <mj-chat-message variant="system" message-id="m4">Alice added Bob to the conversation.</mj-chat-message>\n'
                '</div>'
            ),
            css=".thread { max-inline-size: 40rem; margin: var(--mj-space-3) auto; }\n",
            script=(
                'const messages = Array.from(document.querySelectorAll("mj-chat-message"))\n'
                '/* Recent timestamps so the relative times read naturally. */\n'
                'const minutesAgo = [6, 5, 4]\n'
                'messages.slice(0, 3).forEach((message, index) => {\n'
                '  message.setAttribute("timestamp", new Date(Date.now() - minutesAgo[index] * 60000).toISOString())\n'
                '})\n'
                'const first = messages[0]\n'
                'first.currentUserId = "u-you"\n'
                'first.reactions = [{ emoji: "\\u{1F44D}", count: 2, userIds: ["u-bob", "u-carmen"] },\n'
                '                   { emoji: "\\u{1F389}", count: 1, userIds: ["u-you"] }]\n'
                'first.addEventListener("mj-message-react", (event) => {\n'
                '  first.reactions = first.reactions.map((reaction) => {\n'
                '    if (reaction.emoji !== event.detail.emoji) { return reaction }\n'
                '    const userIds = event.detail.active ? reaction.userIds.concat("u-you") : reaction.userIds.filter((id) => id !== "u-you")\n'
                '    return { emoji: reaction.emoji, count: userIds.length, userIds: userIds }\n'
                '  })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="status",
            title="Delivery status and Retry",
            description=(
                "<p>Outgoing messages in each <code>status</code>. The failed one's actions menu "
                "adds Retry; the script answers it by setting <code>status</code> back to "
                "<code>sent</code> and then <code>delivered</code>.</p>"
            ),
            html=(
                '<div class="thread" role="feed" aria-label="Delivery states">\n'
                '  <mj-chat-message variant="outgoing" message-id="s1" timestamp="2026-11-10T08:00:00Z" status="sent">Sent</mj-chat-message>\n'
                '  <mj-chat-message variant="outgoing" message-id="s2" timestamp="2026-11-10T08:01:00Z" status="delivered" consecutive>Delivered</mj-chat-message>\n'
                '  <mj-chat-message variant="outgoing" message-id="s3" timestamp="2026-11-10T08:02:00Z" status="read" consecutive>Read</mj-chat-message>\n'
                '  <mj-chat-message id="failed" variant="outgoing" message-id="s4" timestamp="2026-11-10T08:03:00Z"\n'
                '                   status="failed" allow-actions consecutive>This one failed &mdash; open &hellip; and choose Retry</mj-chat-message>\n'
                '</div>'
            ),
            css=".thread { max-inline-size: 40rem; margin: var(--mj-space-3) auto; }\n",
            script=(
                'document.querySelectorAll("mj-chat-message").forEach((message, index) => {\n'
                '  message.setAttribute("timestamp", new Date(Date.now() - (8 - index * 2) * 60000).toISOString())\n'
                '})\n'
                'const failed = document.getElementById("failed")\n'
                'failed.addEventListener("mj-message-action", (event) => {\n'
                '  if (event.detail.action !== "retry") { return }\n'
                '  failed.setAttribute("status", "sent")\n'
                '  setTimeout(() => failed.setAttribute("status", "delivered"), 800)\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="rich-body",
            title="Formatted body, quote and attachments",
            description=(
                "<p><code>bodyHtml</code> with emphasis, code and a link (the script cancels "
                "<code>mj-message-link-click</code> and logs it; a <code>style</code> attribute and "
                "an <code>onclick</code> in the input are dropped), a <code>replyTo</code> quote, "
                "and <code>attachments</code>: an image thumbnail and a file with its size.</p>"
            ),
            html=(
                '<div class="thread" role="feed" aria-label="Release notes thread">\n'
                '  <mj-chat-message id="rich" variant="incoming" author-name="Bob Lee" message-id="r1" allow-actions></mj-chat-message>\n'
                '</div>'
            ),
            css=".thread { max-inline-size: 40rem; margin: var(--mj-space-3) auto; }\n",
            script=(
                'const rich = document.getElementById("rich")\n'
                'rich.setAttribute("timestamp", new Date(Date.now() - 2 * 60000).toISOString())\n'
                'rich.replyTo = { messageId: "r0", authorName: "You", preview: "Where are the 4.2 release notes?" }\n'
                'rich.bodyHtml = \'Here they are: <a href="https://example.com/releases/4.2" onclick="alert(1)">release notes</a>. \' +\n'
                '  \'The <strong>breaking change</strong> is in <code>mj-toolbar</code>, see <mark style="color:red">overflow</mark>.\'\n'
                'function thumbnail() {\n'
                '  const canvas = document.createElement("canvas")\n'
                '  canvas.width = 160\n'
                '  canvas.height = 100\n'
                '  const context = canvas.getContext("2d")\n'
                '  context.fillStyle = "#0ea5e9"\n'
                '  context.fillRect(0, 0, 160, 100)\n'
                '  context.fillStyle = "white"\n'
                '  context.font = "bold 18px sans-serif"\n'
                '  context.fillText("4.2", 64, 56)\n'
                '  return canvas.toDataURL("image/png")\n'
                '}\n'
                'rich.attachments = [\n'
                '  { name: "release-banner.png", mimeType: "image/png", thumbnailUrl: thumbnail() },\n'
                '  { name: "release-notes-4.2.pdf", mimeType: "application/pdf", size: 182344, url: "/static/release-notes-4.2.pdf" }\n'
                ']\n'
                'rich.addEventListener("mj-message-link-click", (event) => {\n'
                '  event.preventDefault()\n'
                '  mjSandbox.log("link kept in the page", { href: event.detail.href })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="conversation",
            title="With a composer",
            description=(
                "<p>Messages are created by script from an <code>mj-chat-composer</code>: send a "
                "message and watch its status go from sent to read before the answer arrives. Use "
                "a message's Reply action to quote it.</p>"
            ),
            html=_CHAT_HTML,
            css=_CHAT_CSS,
            script=_CHAT_SCRIPT,
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>Bubble colours, radius, width and avatar size through the custom properties; an avatar from <code>author-avatar</code>.</p>",
            html=(
                '<div class="thread" role="feed" aria-label="Styled messages">\n'
                '  <mj-chat-message id="styled-in" variant="incoming" author-name="Carmen Ortiz" message-id="x1">Lunch at noon?</mj-chat-message>\n'
                '  <mj-chat-message variant="outgoing" author-name="You" message-id="x2" status="delivered">Sounds good!</mj-chat-message>\n'
                '</div>'
            ),
            css=(
                ".thread {\n"
                "  max-inline-size: 40rem;\n"
                "  margin: var(--mj-space-3) auto;\n"
                "  --mj-msg-avatar-size: 40px;\n"
                "  --mj-msg-max-width: 60%;\n"
                "  --mj-msg-bubble-radius: var(--mj-radius-sm);\n"
                "  --mj-msg-bubble-bg-incoming: var(--mj-bg-muted);\n"
                "  --mj-msg-bubble-bg-outgoing: var(--mj-color-success, var(--mj-accent));\n"
                "  --mj-msg-bubble-color-outgoing: var(--mj-text-on-accent);\n"
                "  --mj-msg-timestamp-color: var(--mj-accent);\n"
                "}\n"
            ),
            script=(
                'function avatar() {\n'
                '  const canvas = document.createElement("canvas")\n'
                '  canvas.width = 80\n'
                '  canvas.height = 80\n'
                '  const context = canvas.getContext("2d")\n'
                '  context.fillStyle = "#a855f7"\n'
                '  context.fillRect(0, 0, 80, 80)\n'
                '  context.fillStyle = "white"\n'
                '  context.font = "bold 32px sans-serif"\n'
                '  context.textAlign = "center"\n'
                '  context.textBaseline = "middle"\n'
                '  context.fillText("CO", 40, 42)\n'
                '  return canvas.toDataURL("image/png")\n'
                '}\n'
                'document.getElementById("styled-in").setAttribute("author-avatar", avatar())\n'
                'document.querySelectorAll("mj-chat-message").forEach((message) => {\n'
                '  message.setAttribute("timestamp", new Date(Date.now() - 60000).toISOString())\n'
                '})\n'
            ),
        ),
    ],
    slots=[
        ("body", "The message body (wins over the default slot).", "<span>Body text from the body slot.</span>"),
        ("", "The message body when the `body` slot is empty (plain text children).", "Plain text body."),
    ],
    properties=[
        ("bodyHtml", "string | null. Sanitized HTML body that replaces the slotted body; `null` restores it."),
        ("replyTo", "{ messageId, authorName, preview } | null. The quoted message shown above the body."),
        ("attachments", "object[]. `{ name, url?, mimeType?, size?, thumbnailUrl? }`: images with a usable URL show a thumbnail, others a file link with size (data: and blob: links are not linked)."),
        ("reactions", "object[]. `{ emoji, count, userIds }` chips."),
        ("currentUserId", "string. Viewer id; reactions whose `userIds` contain it show pressed."),
        ("authorId", "string. Reflects `author-id` (\"\" when absent)."),
    ],
    methods=[
        ("focus(options)", "Focuses the message article (for keyboard navigation in a feed)."),
    ],
    parts=[
        ("root", "The message article."),
        ("avatar", "The avatar."),
        ("header", "The author and time header."),
        ("author-name", "The author name."),
        ("timestamp", "The time."),
        ("bubble", "The bubble."),
        ("reply-preview", "The reply quote."),
        ("body", "The body container."),
        ("attachments", "The attachment list."),
        ("reaction-bar", "The reaction chips."),
        ("status", "The delivery indicator (outgoing only)."),
        ("actions-trigger", "The actions button."),
        ("context-menu", "The actions menu."),
    ],
    css_properties=[
        ("--mj-msg-avatar-size", "Avatar size (default 32px)."),
        ("--mj-msg-max-width", "Maximum bubble width (default 70%)."),
        ("--mj-msg-bubble-radius", "Bubble corner radius (default `--mj-radius-lg`)."),
        ("--mj-msg-bubble-bg-incoming", "Incoming bubble background (default `--mj-surface`)."),
        ("--mj-msg-bubble-bg-outgoing", "Outgoing bubble background (default `--mj-accent`)."),
        ("--mj-msg-bubble-color-outgoing", "Outgoing bubble text colour (default `--mj-text-on-accent`)."),
        ("--mj-msg-timestamp-color", "Timestamp colour (default `--mj-text-muted`)."),
        ("--mj-msg-attachment-size", "Maximum image thumbnail size (default 160px)."),
        ("--mj-msg-reply-bg", "Reply quote background (default the bubble's text colour at 8%, so it shows on light, dark and accent bubbles)."),
        ("--mj-msg-status-color-read", "Colour of the read indicator (default `--mj-accent`)."),
    ],
)


COMPONENTS = [
    TOOLBAR,
    MENUBAR,
    STATUS_BAR,
    APP_SHELL,
    SEARCH_RESULTS,
    FILTER_PANEL,
    QUERY_BUILDER,
    DROPZONE,
    FILE_BROWSER,
    ACTIVITY_FEED,
    COMMENTS,
    MENTION_INPUT,
    CHAT_COMPOSER,
    CHAT_MESSAGE,
]
