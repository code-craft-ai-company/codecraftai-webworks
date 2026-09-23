"""
    productivity.py

    Catalog entries for the 'Productivity' component group.

    Covers toolbar, menubar, status bar, app shell, search results, filter
    panel, query builder, dropzone, file browser, activity feed, comments,
    mention input, chat composer, and chat message.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-toolbar",
        title="Toolbar",
        group="productivity",
        summary="Horizontal (or vertical) strip of grouped controls with roving tabindex and overflow handling.",
        description=(
            "<p><code>&lt;mj-toolbar&gt;</code> implements the WAI-ARIA APG "
            "Toolbar pattern. It wraps any focusable children — buttons, "
            "selects, toggle buttons — and manages keyboard navigation with "
            "a roving tabindex. When the strip overflows its container a "
            "&ldquo;More actions&rdquo; button appears automatically. A "
            "<code>ribbon</code> variant adds a tablist for office-style "
            "ribbon bars, and an <code>action-bar</code> variant floats "
            "above content.</p>"
        ),
        how_to_use=(
            "<p>Place any controls as direct children. Set "
            "<code>label</code> or <code>labelledby</code> for the "
            "accessible toolbar name. Use <code>orientation=\"vertical\"</code> "
            "to flip to a column layout. Apply <code>variant=\"ribbon\"</code> "
            "for a ribbon or <code>variant=\"action-bar\"</code> with the "
            "<code>active</code> attribute to show a floating contextual bar. "
            "Listen for <code>mj-toolbar-overflow-change</code> to handle "
            "items pushed into the overflow menu.</p>"
        ),
        example=(
            '<mj-toolbar label="Text formatting">\n'
            '  <mj-button variant="secondary" size="sm">Bold</mj-button>\n'
            '  <mj-button variant="secondary" size="sm">Italic</mj-button>\n'
            '  <mj-button variant="secondary" size="sm">Underline</mj-button>\n'
            '</mj-toolbar>'
        ),
        attributes=[
            ("label", "Accessible label for the toolbar region."),
            ("labelledby", "Id of an element that labels the toolbar."),
            ("orientation", "horizontal (default) | vertical layout."),
            ("variant", "toolbar (default) | ribbon | action-bar."),
            ("active", "Boolean; shows the action-bar variant."),
            ("disabled", "Boolean; dims the toolbar and blocks interaction."),
        ],
        events=[
            ("mj-toolbar-overflow-change", "Fired when items overflow; detail includes overflowItems."),
        ],
    ),
    ComponentDoc(
        tag="mj-menubar",
        title="Menubar",
        group="productivity",
        summary="Application-level menubar with dropdown menus and keyboard navigation.",
        description=(
            "<p><code>&lt;mj-menubar&gt;</code> implements the WAI-ARIA APG "
            "Menubar pattern. Each slotted child element becomes a top-level "
            "menu; nested <code>[data-menu-item]</code> or "
            "<code>role=\"menuitem\"</code> elements become dropdown entries. "
            "Roving tabindex navigates the bar; Arrow keys open dropdowns; "
            "hovering switches open menus; Escape closes.</p>"
        ),
        how_to_use=(
            "<p>Slot one element per top-level menu. Give each a "
            "<code>label</code> attribute for the button text. Add children "
            "with <code>data-menu-item</code> and a <code>value</code> "
            "attribute to populate the dropdown. Listen for "
            "<code>mj-menubar-select</code> to act on item clicks. Set "
            "<code>disabled</code> to block the whole bar.</p>"
        ),
        example=(
            '<mj-menubar label="Application menu">\n'
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
            '</mj-menubar>'
        ),
        attributes=[
            ("label", "Accessible label for the menubar region."),
            ("compact", "Boolean; reduces padding on menu items."),
            ("disabled", "Boolean; dims the bar and blocks interaction."),
            ("active-item", "Value of the currently active top-level item."),
        ],
        events=[
            ("mj-menubar-open", "Fired when a dropdown opens; detail includes item and menuId."),
            ("mj-menubar-close", "Fired when a dropdown closes; detail includes item and menuId."),
            ("mj-menubar-select", "Fired when an item is chosen; detail includes value and path."),
        ],
    ),
    ComponentDoc(
        tag="mj-status-bar",
        title="Status Bar",
        group="productivity",
        summary="Persistent footer strip with start, center, and end sections and a live region.",
        description=(
            "<p><code>&lt;mj-status-bar&gt;</code> is the application-wide "
            "status strip typically pinned to the bottom of the viewport. "
            "It uses a three-slot layout (<code>start</code>, default centre, "
            "<code>end</code>) and contains an ARIA live region so that "
            "messages announced via the <code>announce()</code> method are "
            "picked up by screen readers. Slotted children with the "
            "<code>interactive</code> attribute become clickable items.</p>"
        ),
        how_to_use=(
            "<p>Slot content into <code>slot=\"start\"</code>, the default "
            "slot (centre), or <code>slot=\"end\"</code>. Mark clickable "
            "items with the <code>interactive</code> attribute and give them "
            "a <code>value</code> attribute; the bar fires "
            "<code>mj-status-item-click</code> for those. Call "
            "<code>announce(message)</code> on the element to push messages "
            "to assistive technology. Use <code>variant=\"minimal\"</code> "
            "to hide the centre and end sections.</p>"
        ),
        example=(
            '<mj-status-bar label="Application status">\n'
            '  <span slot="start">Ln 12, Col 8</span>\n'
            '  <span>Ready</span>\n'
            '  <span slot="end" severity="success">Saved</span>\n'
            '</mj-status-bar>'
        ),
        attributes=[
            ("label", "Accessible label for the status bar footer."),
            ("variant", "minimal hides the centre and end sections."),
        ],
        events=[
            ("mj-status-item-click", "Fired when an interactive item is clicked; detail includes itemId and value."),
        ],
    ),
    ComponentDoc(
        tag="mj-app-shell",
        title="App Shell",
        group="productivity",
        summary="Full-page layout frame composing app bar, side nav, main content, inspector, and status bar.",
        description=(
            "<p><code>&lt;mj-app-shell&gt;</code> is the outermost layout "
            "component that assembles the canonical five-zone application "
            "chrome: app bar, icon dock, collapsible side navigation, main "
            "content area, inspector panel, and status bar. It manages "
            "responsive collapse (an overlay drawer, closed by default, "
            "below <code>--mj-shell-breakpoint-nav</code>, 768 px unless "
            "set), panel size persistence in <code>localStorage</code>, focus "
            "cycling with <kbd>F6</kbd>, and an accessible overlay drawer "
            "that traps focus and closes on <kbd>Escape</kbd>. It adds a "
            "main or navigation landmark only where the slotted content "
            "does not bring one, and leaves empty regions out.</p>"
        ),
        how_to_use=(
            "<p>Assign content to named slots: <code>app-bar</code>, "
            "<code>dock</code>, <code>nav</code>, <code>main</code> "
            "(or the default slot), <code>inspector</code>, and "
            "<code>status-bar</code>. Set <code>nav-open</code> to show "
            "the navigation panel and <code>inspector-open</code> for the "
            "inspector. Use <code>nav-mode</code> to choose "
            "<code>static</code>, <code>collapsible</code>, or "
            "<code>overlay</code> behaviour. Provide a <code>storage-key</code> "
            "to namespace persisted sizes.</p>"
        ),
        example=(
            '<mj-app-shell nav-open style="height:300px;">\n'
            '  <div slot="app-bar" style="padding:8px;background:var(--mj-surface);border-bottom:1px solid var(--mj-border);">App Bar</div>\n'
            '  <nav slot="nav" style="padding:12px;">Navigation</nav>\n'
            '  <main slot="main" style="padding:16px;">Main content area</main>\n'
            '  <div slot="status-bar" style="padding:2px 8px;font-size:0.75rem;">Ready</div>\n'
            '</mj-app-shell>'
        ),
        attributes=[
            ("nav-open", "Boolean; opens the side navigation panel."),
            ("nav-mode", "static | collapsible | overlay behaviour."),
            ("inspector-open", "Boolean; opens the inspector panel."),
            ("nav-label", "Accessible label for the nav landmark."),
            ("inspector-label", "Accessible label for the inspector aside."),
            ("storage-key", "localStorage key prefix for persisted panel sizes."),
            ("split", "Boolean; enables draggable panel resize handles."),
        ],
        events=[
            ("mj-shell-nav-toggle", "Fired when the nav panel opens or closes; detail includes open."),
            ("mj-shell-inspector-toggle", "Fired when the inspector opens or closes; detail includes open."),
        ],
    ),
    ComponentDoc(
        tag="mj-search-results",
        title="Search Results",
        group="productivity",
        summary="Ranked list of search results with count bar, skeletons, highlights, and pagination.",
        description=(
            "<p><code>&lt;mj-search-results&gt;</code> renders an accessible "
            "ranked result list. It shows a live count, supports shimmer "
            "skeleton loading, highlights query terms with "
            "<code>&lt;mark&gt;</code>, and offers three pagination strategies: "
            "<code>paginate</code> (prev/next), <code>button</code> (load more), "
            "and <code>infinite</code> (IntersectionObserver). Results are set "
            "via the <code>results</code> JS property or a <code>dataSource</code> "
            "object.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>results</code> property to an array of objects "
            "with <code>{id, title, url, snippet, date}</code> fields and "
            "<code>total-count</code> to the full match count. Use "
            "<code>loading</code> to show skeletons during a fetch. Set "
            "<code>highlight-term</code> to highlight words in snippets. "
            "Choose a <code>load-mode</code> and listen for "
            "<code>mj-page-change</code>, <code>mj-load-more</code>, or "
            "<code>mj-result-select</code>.</p>"
        ),
        example=(
            '<mj-search-results\n'
            '  total-count="3"\n'
            '  highlight-term="component"\n'
            '  load-mode="paginate">\n'
            '</mj-search-results>\n'
            '<script>\n'
            '  const sr = document.querySelector("mj-search-results");\n'
            '  sr.results = [\n'
            '    { id: "1", title: "Button component", url: "/docs/button",\n'
            '      snippet: "The button component triggers actions." },\n'
            '    { id: "2", title: "Card component", url: "/docs/card",\n'
            '      snippet: "The card component groups related content." },\n'
            '    { id: "3", title: "Dialog component", url: "/docs/dialog",\n'
            '      snippet: "The dialog component presents modal content." }\n'
            '  ];\n'
            '</script>'
        ),
        attributes=[
            ("total-count", "Total number of matching results (may exceed visible count)."),
            ("loading", "Boolean; shows shimmer skeleton rows."),
            ("load-mode", "paginate | button | infinite pagination strategy."),
            ("page", "Current page number (1-based)."),
            ("page-size", "Results per page (default 10)."),
            ("highlight-term", "Space-separated terms to highlight in snippets."),
            ("empty-message", "Message shown when results array is empty."),
            ("compact", "Boolean; reduces vertical spacing between items."),
        ],
        events=[
            ("mj-result-select", "Fired when a result link is clicked; detail includes result and index."),
            ("mj-page-change", "Fired when the page changes; detail includes page and pageSize."),
            ("mj-load-more", "Fired when load-more is triggered; detail includes page and pageSize."),
        ],
    ),
    ComponentDoc(
        tag="mj-filter-panel",
        title="Filter Panel",
        group="productivity",
        summary="Faceted filter sidebar with applied-filter chips, sort control, and collapsible groups.",
        description=(
            "<p><code>&lt;mj-filter-panel&gt;</code> provides a full-featured "
            "faceted filter UI. Filter groups are defined via the "
            "<code>filterConfig</code> property and render as collapsible "
            "accordion sections of checkboxes or radio buttons. Selected "
            "values appear as dismissible chips at the top with a "
            "&ldquo;Clear all&rdquo; shortcut. A sort control with direction "
            "toggle is built in. The component fires a rich "
            "<code>mj-filter-change</code> event on every change.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>filterConfig</code> JS property to an array of "
            "group objects: <code>{id, label, type, options: [{value, label}]}</code>. "
            "Use <code>type: \"radio\"</code> for single-select groups. Read "
            "the <code>value</code> property for the current filter and sort "
            "state. The <code>layout</code> attribute switches between "
            "<code>sidebar</code> and <code>inline</code> rendering. Slot "
            "content into <code>header</code> and <code>footer</code> for "
            "custom additions.</p>"
        ),
        example=(
            '<mj-filter-panel label="Filters" layout="sidebar"\n'
            '                 total-count="42" style="width:280px;">\n'
            '</mj-filter-panel>\n'
            '<script>\n'
            '  const fp = document.querySelector("mj-filter-panel");\n'
            '  fp.filterConfig = [\n'
            '    { id: "status", label: "Status", type: "checkbox",\n'
            '      options: [{value:"active",label:"Active"},{value:"archived",label:"Archived"}] },\n'
            '    { id: "type", label: "Type", type: "radio",\n'
            '      options: [{value:"doc",label:"Document"},{value:"img",label:"Image"}] }\n'
            '  ];\n'
            '</script>'
        ),
        attributes=[
            ("label", "Accessible label for the filter region."),
            ("layout", "sidebar (default) | inline rendering."),
            ("collapsible", "Boolean; adds a toggle button to collapse the whole panel."),
            ("open", "Boolean; expanded state when collapsible."),
            ("total-count", "Shows a result count footer when set."),
            ("sort-label", "Label for the sort-by control."),
        ],
        events=[
            ("mj-filter-change", "Fired on any filter or sort change; detail includes value and changedGroup."),
            ("mj-chip-remove", "Fired when an applied-filter chip is dismissed; detail includes groupId and value."),
            ("mj-filter-clear", "Fired when all filters are cleared."),
            ("mj-panel-toggle", "Fired when the collapsible panel opens or closes; detail includes open."),
        ],
    ),
    ComponentDoc(
        tag="mj-query-builder",
        title="Query Builder",
        group="productivity",
        summary="Visual editor for compound boolean filter expressions with AND/OR combinators and nesting.",
        description=(
            "<p><code>&lt;mj-query-builder&gt;</code> lets users build "
            "arbitrarily nested boolean queries through a visual UI. Each "
            "condition row provides field, operator, and value selectors "
            "drawn from the <code>fieldSchema</code> property. Groups can "
            "be nested up to <code>max-depth</code> levels. The component "
            "emits its structured <code>QueryGroup</code> JSON on every "
            "change and optionally shows a live JSON preview.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>fieldSchema</code> JS property to an array of "
            "<code>{id, label, type}</code> objects where type is one of "
            "<code>string</code>, <code>number</code>, <code>date</code>, "
            "<code>boolean</code>, or <code>select</code>. Optionally provide "
            "a custom <code>operatorMap</code>. Read or set <code>value</code> "
            "to get or restore a query. Enable <code>show-preview</code> to "
            "render the JSON tree below the editor. Set <code>readonly</code> "
            "to prevent changes.</p>"
        ),
        example=(
            '<mj-query-builder label="Filter query" show-preview>\n'
            '</mj-query-builder>\n'
            '<script>\n'
            '  const qb = document.querySelector("mj-query-builder");\n'
            '  qb.fieldSchema = [\n'
            '    { id: "name",   label: "Name",   type: "string" },\n'
            '    { id: "age",    label: "Age",    type: "number" },\n'
            '    { id: "status", label: "Status", type: "select" }\n'
            '  ];\n'
            '</script>'
        ),
        attributes=[
            ("label", "Accessible label for the query builder region."),
            ("readonly", "Boolean; disables all editing controls."),
            ("max-depth", "Maximum nesting depth for condition groups (default 3)."),
            ("show-preview", "Boolean; shows a JSON preview panel below the editor."),
            ("add-rule-label", "Label for the Add condition button."),
            ("add-group-label", "Label for the Add group button."),
        ],
        events=[
            ("mj-query-change", "Fired on every edit; detail includes the value QueryGroup tree."),
            ("mj-query-valid", "Fired alongside mj-query-change; detail includes valid and errors."),
        ],
    ),
    ComponentDoc(
        tag="mj-dropzone",
        title="Drop Zone",
        group="productivity",
        summary="Drag-and-drop file upload zone with click-to-browse, type and size validation, and progress.",
        description=(
            "<p><code>&lt;mj-dropzone&gt;</code> is a form-associated file "
            "input that accepts files by drag-and-drop or by clicking the "
            "Browse button. It validates MIME types against <code>accept</code> "
            "and enforces <code>max-size</code> and <code>max-files</code> "
            "limits, firing <code>mj-files-rejected</code> for violations. "
            "Accepted files appear in a removable list with per-file progress "
            "bars when updated via <code>updateFile()</code>.</p>"
        ),
        how_to_use=(
            "<p>Set <code>accept</code> to a comma-separated MIME or extension "
            "list, <code>max-size</code> in bytes, and <code>max-files</code>. "
            "Remove <code>multiple</code> (or set it to <code>false</code>) "
            "for single-file mode. Customise the icon and instructions with "
            "the <code>icon</code> and <code>instructions</code> slots. "
            "Listen for <code>mj-files-added</code> then call "
            "<code>updateFile(id, {status, progress})</code> to drive "
            "per-file upload feedback.</p>"
        ),
        example=(
            '<mj-dropzone\n'
            '  label="Upload documents"\n'
            '  accept=".pdf,.docx"\n'
            '  multiple\n'
            '  max-size="10485760"\n'
            '  show-list="true">\n'
            '</mj-dropzone>'
        ),
        attributes=[
            ("accept", "Comma-separated MIME types or file extensions."),
            ("multiple", "Boolean; allow multiple files (default true)."),
            ("max-size", "Maximum bytes per file; rejected files fire mj-files-rejected."),
            ("max-files", "Maximum total file count."),
            ("disabled", "Boolean; blocks interaction."),
            ("compact", "Boolean; renders as a compact horizontal strip."),
            ("show-list", "Boolean; shows the accepted-file list (default true)."),
            ("label", "Accessible label for the drop region."),
            ("browse-label", "Label for the Browse files button."),
            ("drag-label", "Instruction text shown inside the zone."),
        ],
        events=[
            ("mj-files-added", "Fired when valid files are accepted; detail includes files entries."),
            ("mj-files-rejected", "Fired when files fail validation; detail includes rejectedFiles."),
            ("mj-file-remove", "Fired when a file is removed from the list; detail includes fileId and file."),
            ("mj-drag-enter", "Fired when a drag enters the zone."),
            ("mj-drag-leave", "Fired when a drag leaves the zone."),
        ],
    ),
    ComponentDoc(
        tag="mj-file-browser",
        title="File Browser",
        group="productivity",
        summary="Three-pane file system navigator with folder tree, file grid/list, and optional preview.",
        description=(
            "<p><code>&lt;mj-file-browser&gt;</code> is a self-contained "
            "file manager widget. The left pane shows a folder tree, the "
            "centre pane renders files in grid or list view, and an optional "
            "right pane previews the selected file. Breadcrumb navigation, "
            "multi-select with Ctrl/Meta+click, and <kbd>F6</kbd> focus "
            "cycling between panes are all built in. Data is loaded "
            "asynchronously via a <code>dataSource</code> object.</p>"
        ),
        how_to_use=(
            "<p>Assign a <code>dataSource</code> object with a "
            "<code>listDir(path)</code> method that returns a promise of "
            "file-item arrays. Each item should have "
            "<code>{name, type, path, size?, modified?}</code>. Set "
            "<code>view</code> to <code>grid</code> or <code>list</code>, "
            "<code>selection-mode</code> to <code>single</code> or "
            "<code>multi</code>, and <code>preview-open</code> to reveal "
            "the preview pane. Listen for <code>mj-selection-change</code> "
            "and <code>mj-file-open</code>.</p>"
        ),
        example=(
            '<mj-file-browser\n'
            '  label="Project files"\n'
            '  view="list"\n'
            '  style="height:320px;">\n'
            '</mj-file-browser>\n'
            '<script>\n'
            '  const fb = document.querySelector("mj-file-browser");\n'
            '  fb.dataSource = {\n'
            '    listDir(path) {\n'
            '      return Promise.resolve([\n'
            '        { name: "docs", type: "folder", path: "/docs" },\n'
            '        { name: "readme.md", type: "text/markdown", path: "/readme.md", size: "2 KB" },\n'
            '        { name: "logo.png", type: "image/png", path: "/logo.png", size: "48 KB" }\n'
            '      ]);\n'
            '    }\n'
            '  };\n'
            '</script>'
        ),
        attributes=[
            ("view", "list (default) | grid file display."),
            ("preview", "none | auto — controls preview pane visibility."),
            ("preview-open", "Boolean; shows the preview pane."),
            ("tree-open", "true (default) | false — controls folder tree visibility."),
            ("selection-mode", "single | multi file selection."),
            ("show-hidden", "Boolean; includes dot-files."),
            ("label", "Accessible label for the browser application region."),
        ],
        events=[
            ("mj-folder-navigate", "Fired when the current directory changes; detail includes path."),
            ("mj-selection-change", "Fired when the selection changes; detail includes selectedFiles."),
            ("mj-file-open", "Fired on double-click / Enter on a non-folder file; detail includes file."),
            ("mj-view-change", "Fired when the view mode toggles; detail includes view."),
        ],
    ),
    ComponentDoc(
        tag="mj-activity-feed",
        title="Activity Feed",
        group="productivity",
        summary="Chronological stream of activity events with real-time prepend, grouping, and load-older.",
        description=(
            "<p><code>&lt;mj-activity-feed&gt;</code> renders a timeline of "
            "activity events using the APG Feed pattern "
            "(<code>role=\"feed\"</code>). Events are set via the "
            "<code>items</code> property or a <code>dataSource</code>. "
            "New items prepended while the user is scrolled down show a "
            "sticky &ldquo;N new events&rdquo; banner when "
            "<code>realtime</code> is set. Relative timestamps refresh "
            "every minute automatically. Items can be grouped by date.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>items</code> property to an array of objects "
            "with <code>{id, actor: {name, avatarUrl?}, action, body?, timestamp}</code> "
            "fields. Add <code>realtime</code> to enable the new-items "
            "banner. Choose <code>load-mode</code> for how older items are "
            "fetched. Call <code>addItem(item)</code> to prepend a single "
            "new event at runtime. Use <code>group-by=\"date\"</code> to "
            "insert date dividers.</p>"
        ),
        example=(
            '<mj-activity-feed label="Recent activity" load-mode="button">\n'
            '</mj-activity-feed>\n'
            '<script>\n'
            '  const feed = document.querySelector("mj-activity-feed");\n'
            '  const now = new Date().toISOString();\n'
            '  feed.items = [\n'
            '    { id: "1", actor: { name: "Alice Martin" }, action: "created document",\n'
            '      body: "Q4 Planning Notes", timestamp: now },\n'
            '    { id: "2", actor: { name: "Bob Lee" }, action: "commented",\n'
            '      body: "Looks good to me!", timestamp: now }\n'
            '  ];\n'
            '</script>'
        ),
        attributes=[
            ("label", "Accessible label for the feed region."),
            ("compact", "Boolean; reduces item spacing."),
            ("group-by", "date — inserts date divider headings between items."),
            ("load-mode", "button (default) | infinite — how older items are loaded."),
            ("realtime", "Boolean; shows a sticky banner when new items are prepended."),
            ("empty-message", "Message shown when the items list is empty."),
            ("timestamp-format", "relative (default) | absolute timestamp display."),
        ],
        events=[
            ("mj-load-older", "Fired when the user requests older items; detail includes cursor."),
            ("mj-new-items-viewed", "Fired when the new-items banner is dismissed; detail includes count."),
        ],
    ),
    ComponentDoc(
        tag="mj-comments",
        title="Comments",
        group="productivity",
        summary="Threaded comment section with replies, inline editing, emoji reactions, and load-older.",
        description=(
            "<p><code>&lt;mj-comments&gt;</code> renders a full-featured "
            "comment thread using the APG Feed pattern. Top-level comments "
            "and their replies are displayed with avatars and relative "
            "timestamps that refresh automatically. Authenticated users can "
            "reply, edit their own comments, delete them, and react with "
            "emoji. The composer can sit above or below the thread. "
            "Pagination is supported via a <code>dataSource</code> or by "
            "directly setting the <code>comments</code> property.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>comments</code> property to an array of "
            "comment objects: "
            "<code>{id, authorId, authorName, authorAvatar?, body, createdAt, "
            "replies?: [], reactions?: []}</code>. "
            "Supply <code>current-user-id</code> to enable edit/delete on "
            "owned comments. Set <code>readonly</code> to hide the composer. "
            "Provide <code>max-depth</code> to cap nesting. "
            "Listen for <code>mj-comment-post</code> to persist new comments "
            "then call <code>addComment()</code> to update the UI.</p>"
        ),
        example=(
            '<mj-comments\n'
            '  label="Discussion"\n'
            '  current-user-id="u1"\n'
            '  allow-reactions="true">\n'
            '</mj-comments>\n'
            '<script>\n'
            '  const c = document.querySelector("mj-comments");\n'
            '  c.comments = [\n'
            '    { id: "c1", authorId: "u2", authorName: "Alice",\n'
            '      body: "Great feature!", createdAt: new Date().toISOString(),\n'
            '      reactions: [{ emoji: "&#128077;", count: 3, userIds: [] }],\n'
            '      replies: [] }\n'
            '  ];\n'
            '</script>'
        ),
        attributes=[
            ("label", "Accessible label for the comments feed region."),
            ("current-user-id", "Id of the signed-in user; enables edit and delete on own comments."),
            ("readonly", "Boolean; hides the composer and action buttons."),
            ("max-depth", "Maximum reply nesting depth (default 3)."),
            ("max-visible-replies", "Replies shown before Show more button appears (default 3)."),
            ("allow-reactions", "Boolean; enables emoji reaction chips (default true)."),
            ("composer-position", "top | bottom (default) placement of the top-level composer."),
            ("empty-message", "Message shown when the comment list is empty."),
        ],
        events=[
            ("mj-comment-post", "Fired when a new comment is submitted; detail includes body, parentId, mentions."),
            ("mj-comment-edit", "Fired when an edit is saved; detail includes commentId and body."),
            ("mj-comment-delete", "Fired when a comment is deleted; detail includes commentId."),
            ("mj-comment-react", "Fired when a reaction chip is toggled; detail includes commentId, emoji, active."),
            ("mj-load-replies", "Fired when Show more replies is clicked; detail includes commentId and cursor."),
            ("mj-load-older", "Fired when Load earlier comments is clicked; detail includes cursor."),
        ],
    ),
    ComponentDoc(
        tag="mj-mention-input",
        title="Mention Input",
        group="productivity",
        summary="Contenteditable text field with @ and # trigger detection, suggestion popup, and inline tokens.",
        description=(
            "<p><code>&lt;mj-mention-input&gt;</code> is a form-associated "
            "rich text field that detects configurable trigger characters "
            "(<code>@</code>, <code>#</code>, or custom) as the user types. "
            "After detection it queries a <code>mentionSource</code> object "
            "and displays a suggestion popup. Choosing a suggestion inserts "
            "an inline token chip that is rendered as a styled, "
            "non-editable element and can be removed with Backspace. "
            "An optional character counter enforces <code>max-length</code>.</p>"
        ),
        how_to_use=(
            "<p>Assign a <code>mentionSource</code> object with a "
            "<code>suggest(trigger, query)</code> method that returns a "
            "promise of suggestion objects: "
            "<code>{id, displayName, subtitle?, avatarUrl?, type?}</code>. "
            "Set <code>placeholder</code>, <code>triggers</code> "
            "(default <code>@#</code>), <code>multiline</code>, and "
            "<code>max-length</code>. Listen for <code>mj-input</code> "
            "for live value/mentions, <code>mj-submit</code> on Enter, "
            "and <code>mj-change</code> on blur.</p>"
        ),
        example=(
            '<mj-mention-input\n'
            '  label="Message"\n'
            '  placeholder="Type @ to mention someone…"\n'
            '  multiline="false"\n'
            '  triggers="@">\n'
            '</mj-mention-input>\n'
            '<script>\n'
            '  const mi = document.querySelector("mj-mention-input");\n'
            '  mi.mentionSource = {\n'
            '    suggest(trigger, query) {\n'
            '      const users = [\n'
            '        { id: "u1", displayName: "Alice Martin", subtitle: "Engineering" },\n'
            '        { id: "u2", displayName: "Bob Lee", subtitle: "Design" }\n'
            '      ];\n'
            '      return Promise.resolve(\n'
            '        users.filter(u => u.displayName.toLowerCase().includes(query.toLowerCase()))\n'
            '      );\n'
            '    }\n'
            '  };\n'
            '</script>'
        ),
        attributes=[
            ("label", "Visible and accessible label for the field."),
            ("placeholder", "Placeholder text shown when the field is empty."),
            ("triggers", "Characters that open the suggestion popup (default @#)."),
            ("multiline", "Boolean (default true); allows newlines in the field."),
            ("max-length", "Maximum character count; shows a counter when set."),
            ("disabled", "Boolean; blocks interaction."),
            ("readonly", "Boolean; prevents editing."),
            ("required", "Boolean; marks the field as required."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke; detail includes value and mentions."),
            ("mj-change", "Fired on blur if the value changed; detail includes value and mentions."),
            ("mj-submit", "Cancelable; fired on Enter (when multiline is false); detail includes value and mentions."),
            ("mj-mention-select", "Fired when a suggestion is accepted; detail includes trigger and suggestion."),
            ("mj-mention-cancel", "Fired when the popup is dismissed without selection; detail includes trigger."),
        ],
    ),
    ComponentDoc(
        tag="mj-chat-composer",
        title="Chat Composer",
        group="productivity",
        summary="Message-entry bar with attach, emoji, reply preview, attachment chips, and send button.",
        description=(
            "<p><code>&lt;mj-chat-composer&gt;</code> is the input bar at the "
            "bottom of a chat thread. It combines a growing textarea, an "
            "optional attachment button, an emoji button, a send button with "
            "loading spinner, and an attachment chip list. A reply preview "
            "banner appears when <code>replyTo</code> is set. "
            "The send key is configurable between <code>enter</code> and "
            "<code>ctrl+enter</code>.</p>"
        ),
        how_to_use=(
            "<p>Set <code>placeholder</code> and optionally "
            "<code>max-length</code>. To disable attachments set "
            "<code>allow-attachments=\"false\"</code>; to disable the emoji "
            "button set <code>allow-emoji=\"false\"</code>. "
            "Assign a <code>replyTo</code> property to show the reply preview "
            "strip. Set <code>loading</code> while a message is being sent. "
            "Listen for <code>mj-send</code> (cancelable) to handle "
            "submission; the composer clears itself automatically unless "
            "<code>mj-send</code> is cancelled. Use the "
            "<code>toolbar-start</code> and <code>toolbar-end</code> slots "
            "for extra toolbar buttons.</p>"
        ),
        example=(
            '<mj-chat-composer\n'
            '  placeholder="Type a message…"\n'
            '  send-key="enter"\n'
            '  allow-attachments="true"\n'
            '  allow-emoji="true">\n'
            '</mj-chat-composer>'
        ),
        attributes=[
            ("placeholder", "Placeholder text for the textarea."),
            ("label", "Accessible label for the composer form region."),
            ("max-length", "Maximum character count; shows a counter when set."),
            ("send-key", "enter (default) | ctrl+enter send trigger."),
            ("allow-attachments", "Boolean (default true); shows the attach button."),
            ("allow-emoji", "Boolean (default true); shows the emoji button."),
            ("disabled", "Boolean; blocks all interaction."),
            ("loading", "Boolean; shows a spinner on the send button and disables input."),
            ("accept", "Accepted file types for the file input (passed to accept attribute)."),
        ],
        events=[
            ("mj-send", "Cancelable; fired on send; detail includes value, mentions, attachments, replyTo."),
            ("mj-input", "Fired on every keystroke; detail includes value and mentions."),
            ("mj-attachment-add", "Fired when files are attached; detail includes files entries."),
            ("mj-attachment-remove", "Fired when an attachment chip is dismissed; detail includes fileId."),
            ("mj-reply-cancel", "Fired when the reply preview is dismissed."),
        ],
    ),
    ComponentDoc(
        tag="mj-chat-message",
        title="Chat Message",
        group="productivity",
        summary="Single chat message bubble with incoming/outgoing/system variants, reactions, and action menu.",
        description=(
            "<p><code>&lt;mj-chat-message&gt;</code> renders one bubble in a "
            "chat thread. The <code>variant</code> attribute controls layout: "
            "<code>incoming</code> shows an avatar on the left, "
            "<code>outgoing</code> reverses to the right with a delivery "
            "status indicator, and <code>system</code> centres a pill "
            "notification. The <code>consecutive</code> attribute hides the "
            "avatar and header for messages in the same group. Emoji "
            "reactions, a reply preview strip, and a context menu with "
            "Reply / Copy / Edit / Delete actions are all built in.</p>"
        ),
        how_to_use=(
            "<p>Set attributes for <code>variant</code>, "
            "<code>author-name</code>, <code>author-avatar</code>, "
            "<code>timestamp</code>, <code>message-id</code>, and "
            "<code>status</code>. Provide body content via the "
            "<code>body</code> slot or by assigning the <code>bodyHtml</code> "
            "JS property (HTML is sanitized). To show reactions assign the "
            "<code>reactions</code> property and set "
            "<code>current-user-id</code>. For reply threads set the "
            "<code>replyTo</code> property. Add "
            "<code>allow-actions</code> to show the context menu trigger. "
            "Place multiple messages inside a "
            "<code>role=\"feed\"</code> container.</p>"
        ),
        example=(
            '<div role="feed" aria-label="Chat" style="padding:8px;">\n'
            '  <mj-chat-message\n'
            '    variant="incoming"\n'
            '    author-name="Alice"\n'
            '    timestamp="2026-05-22T09:00:00Z"\n'
            '    message-id="m1"\n'
            '    allow-reactions\n'
            '    allow-actions>\n'
            '    <span slot="body">Hey, how is the project going?</span>\n'
            '  </mj-chat-message>\n'
            '  <mj-chat-message\n'
            '    variant="outgoing"\n'
            '    author-name="You"\n'
            '    timestamp="2026-05-22T09:01:00Z"\n'
            '    message-id="m2"\n'
            '    status="read">\n'
            '    <span slot="body">Going great &mdash; almost done!</span>\n'
            '  </mj-chat-message>\n'
            '  <mj-chat-message\n'
            '    variant="system"\n'
            '    message-id="m3">\n'
            '    <span slot="body">Alice added Bob to the conversation.</span>\n'
            '  </mj-chat-message>\n'
            '</div>'
        ),
        attributes=[
            ("variant", "incoming (default) | outgoing | system layout."),
            ("consecutive", "Boolean; hides avatar and header for follow-up bubbles from the same sender."),
            ("author-name", "Display name of the message author."),
            ("author-id", "Id of the message author."),
            ("author-avatar", "URL of the author avatar image."),
            ("timestamp", "ISO 8601 datetime string; displayed as relative time."),
            ("status", "sent | delivered | read | failed delivery status (outgoing only)."),
            ("message-id", "Unique identifier for the message."),
            ("allow-reactions", "Boolean; enables the emoji reaction bar."),
            ("allow-actions", "Boolean; shows the context-menu trigger button on hover."),
        ],
        events=[
            ("mj-message-reply", "Fired when Reply is chosen from the context menu; detail includes messageId."),
            ("mj-message-action", "Fired for copy/edit/delete actions; detail includes messageId and action."),
            ("mj-message-react", "Fired when a reaction chip is toggled; detail includes messageId, emoji, active."),
            ("mj-message-link-click", "Cancelable; fired when a link inside bodyHtml is clicked; detail includes href and messageId."),
        ],
    ),
]
