"""
    overlays.py

    Catalog entries for the 'Overlays' component group.

    This module exposes a module-level ``COMPONENTS`` list of ComponentDoc
    instances describing and demonstrating every overlay and contextual-layer
    component in the mj-* library.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-dialog",
        title="Dialog",
        group="overlays",
        summary="Modal and non-modal dialog built on the native &lt;dialog&gt; element.",
        description=(
            "<p><code>&lt;mj-dialog&gt;</code> renders a panel on top of page "
            "content for tasks that require user attention or input. It supports "
            "four <code>variant</code> modes: plain <code>dialog</code>, "
            "<code>alertdialog</code>, <code>confirmation</code> (adds Cancel / "
            "Confirm buttons), and <code>prompt</code> (adds a text field). Modal "
            "dialogs trap focus and display an <code>&lt;mj-overlay&gt;</code> "
            "backdrop; non-modal dialogs can be shown alongside page content.</p>"
        ),
        how_to_use=(
            "<p>Place content between the tags. Use the <code>title</code> slot "
            "for the heading and the <code>footer</code> slot for custom action "
            "buttons. Call <code>showModal()</code> or set the <code>open</code> "
            "attribute to open as a modal; call <code>show()</code> or add "
            "<code>modal=\"false\"</code> with <code>open</code> for a non-modal "
            "dialog. Call <code>close()</code> or remove the <code>open</code> "
            "attribute to dismiss. Set <code>close-on-backdrop=\"false\"</code> to "
            "prevent backdrop-click dismissal. The <code>no-close-button</code> "
            "attribute hides the built-in &times; button.</p>"
        ),
        example=(
            '<mj-dialog open variant="dialog" label="Example dialog">\n'
            '  <span slot="title">Confirm action</span>\n'
            "  <p>Are you sure you want to proceed with this action? "
            "This cannot be undone.</p>\n"
            '  <div slot="footer">\n'
            '    <button onclick="this.closest(\'mj-dialog\').close()">Cancel</button>\n'
            '    <button onclick="this.closest(\'mj-dialog\').close()">Confirm</button>\n'
            "  </div>\n"
            "</mj-dialog>"
        ),
        attributes=[
            ("open", "Boolean; opens the dialog."),
            ("variant", "dialog | alertdialog | confirmation | prompt."),
            ("modal", "Boolean (default true); false for a non-modal dialog."),
            ("label", "aria-label override when no visible title is slotted."),
            ("close-label", "Accessible label for the close button (default 'Close dialog')."),
            ("confirm-label", "Label for the confirm button in confirmation/prompt variants."),
            ("cancel-label", "Label for the cancel button in confirmation/prompt variants."),
            ("close-on-backdrop", "Boolean (default true); dismiss when the backdrop is clicked."),
            ("no-close-button", "Boolean; hides the built-in close button."),
        ],
        events=[
            ("mj-dialog-open", "Fired when the dialog finishes opening."),
            ("mj-dialog-before-close", "Cancelable; fired before the dialog closes."),
            ("mj-dialog-close", "Fired when the dialog finishes closing; detail includes reason."),
            ("mj-dialog-confirm", "Fired when the confirm button is activated; detail includes value."),
            ("mj-dialog-cancel", "Fired when the cancel button is activated."),
        ],
    ),
    ComponentDoc(
        tag="mj-popover",
        title="Popover",
        group="overlays",
        summary="Anchored, non-modal overlay for rich contextual content.",
        description=(
            "<p><code>&lt;mj-popover&gt;</code> displays a floating panel "
            "anchored to a trigger element. It supports two <code>variant</code> "
            "modes: <code>popover</code> (click/keyboard-activated) and "
            "<code>hovercard</code> (hover-activated with configurable delays). "
            "The positioning engine keeps the panel inside the viewport and "
            "light-dismiss closes it when the user clicks outside.</p>"
        ),
        how_to_use=(
            "<p>Place the trigger element in the <code>trigger</code> slot, or "
            "point <code>trigger-id</code> at an element elsewhere in the DOM. "
            "Default body content goes between the tags; use the <code>header</code> "
            "and <code>footer</code> slots for structured layout. Control placement "
            "with <code>placement</code> (e.g. <code>bottom</code>, <code>top</code>, "
            "<code>end</code>) and <code>offset</code>. Call <code>show()</code> or "
            "set the <code>open</code> attribute to open programmatically; call "
            "<code>close()</code> to dismiss. Set <code>light-dismiss=\"false\"</code> "
            "to prevent outside-click dismissal.</p>"
        ),
        example=(
            '<mj-popover placement="bottom" open>\n'
            '  <button slot="trigger">Show popover</button>\n'
            '  <span slot="header">More information</span>\n'
            "  <p>This popover panel contains contextual details about the "
            "adjacent control.</p>\n"
            "</mj-popover>"
        ),
        attributes=[
            ("open", "Boolean; shows the popover."),
            ("variant", "popover (default) | hovercard."),
            ("placement", "Preferred placement: top | bottom | start | end (default bottom)."),
            ("offset", "Gap in pixels between anchor and popover (default 8)."),
            ("trigger-id", "Id of an external trigger element."),
            ("light-dismiss", "Boolean (default true); close on outside pointer-down."),
            ("hover-delay", "Milliseconds before opening on hover in hovercard mode (default 200)."),
            ("hover-out-delay", "Milliseconds before closing after pointer leaves in hovercard mode (default 300)."),
            ("no-close-button", "Boolean; hides the built-in close button."),
            ("close-label", "Accessible label for the close button (default 'Close')."),
        ],
        events=[
            ("mj-popover-before-open", "Cancelable; fired before the popover opens."),
            ("mj-popover-open", "Fired when the popover opens; detail includes placement."),
            ("mj-popover-before-close", "Cancelable; fired before the popover closes."),
            ("mj-popover-close", "Fired when the popover closes; detail includes reason."),
        ],
    ),
    ComponentDoc(
        tag="mj-drawer",
        title="Drawer",
        group="overlays",
        summary="Edge-anchored sliding panel for navigation, filters, or detail views.",
        description=(
            "<p><code>&lt;mj-drawer&gt;</code> slides in from any viewport edge "
            "(<code>start</code>, <code>end</code>, <code>top</code>, or "
            "<code>bottom</code>). In modal mode it traps focus and shows a "
            "backdrop; set <code>modal=\"false\"</code> for a sidebar that "
            "coexists with page content. The <code>bottom</code> edge variant "
            "renders a drag handle and supports swipe-to-dismiss on touch "
            "devices.</p>"
        ),
        how_to_use=(
            "<p>Place content between the tags. The <code>title</code> slot "
            "provides a heading; the <code>header</code> slot replaces the "
            "entire header region; the <code>footer</code> slot adds a pinned "
            "footer. Set the <code>edge</code> attribute to choose which side "
            "slides in. Call <code>show()</code> or set <code>open</code> to "
            "open the drawer; call <code>close()</code> or remove <code>open</code> "
            "to dismiss. Set <code>close-on-backdrop=\"false\"</code> to prevent "
            "backdrop-click dismissal.</p>"
        ),
        example=(
            '<mj-drawer open edge="end" label="Navigation">\n'
            '  <span slot="title">Site Navigation</span>\n'
            "  <nav>\n"
            "    <ul>\n"
            "      <li><a href=\"#\">Home</a></li>\n"
            "      <li><a href=\"#\">About</a></li>\n"
            "      <li><a href=\"#\">Contact</a></li>\n"
            "    </ul>\n"
            "  </nav>\n"
            "</mj-drawer>"
        ),
        attributes=[
            ("open", "Boolean; slides the panel into view."),
            ("edge", "start | end (default) | top | bottom."),
            ("modal", "Boolean (default true); false for a non-modal sidebar."),
            ("label", "aria-label for the panel when no visible title is provided."),
            ("close-label", "Accessible label for the close button (default 'Close')."),
            ("close-on-backdrop", "Boolean (default true); dismiss when the backdrop is clicked."),
            ("no-close-button", "Boolean; hides the built-in close button."),
            ("swipe-to-dismiss", "Boolean (default true); enables swipe-down to close on bottom edge."),
        ],
        events=[
            ("mj-drawer-open", "Fired when the drawer opens; detail includes edge."),
            ("mj-drawer-before-close", "Cancelable; fired before the drawer closes."),
            ("mj-drawer-close", "Fired when the drawer closes; detail includes edge and reason."),
            ("mj-drawer-swipe", "Fired during a swipe gesture; detail includes progress (0&ndash;1)."),
        ],
    ),
    ComponentDoc(
        tag="mj-lightbox",
        title="Lightbox",
        group="overlays",
        summary="Full-screen modal media viewer with navigation and zoom.",
        description=(
            "<p><code>&lt;mj-lightbox&gt;</code> presents images (and other "
            "media) in a full-viewport overlay with previous/next navigation, "
            "pinch/button zoom, captions, and a counter. Items are set via the "
            "<code>items</code> JavaScript property as an array of "
            "<code>{ src, alt, caption }</code> objects. Keyboard arrows "
            "navigate between items; <kbd>+</kbd>/<kbd>&minus;</kbd> zoom; "
            "<kbd>0</kbd> resets zoom; <kbd>Escape</kbd> closes.</p>"
        ),
        how_to_use=(
            "<p>Add the element to the page and assign the <code>items</code> "
            "array in script. Call <code>show(index)</code> to open at a "
            "specific item, or set the <code>open</code> attribute. Call "
            "<code>close()</code> to dismiss. Use <code>show-caption</code> "
            "to display per-item captions and <code>loop</code> to enable "
            "wrap-around navigation. The <code>current-index</code> attribute "
            "reflects and controls the displayed item.</p>"
        ),
        example=(
            '<mj-lightbox id="lb1" open show-caption loop></mj-lightbox>\n'
            "<script>\n"
            "  const lb = document.getElementById('lb1');\n"
            "  lb.items = [\n"
            "    { src: 'https://picsum.photos/seed/a/800/500', alt: 'Sample image 1', caption: 'Caption one' },\n"
            "    { src: 'https://picsum.photos/seed/b/800/500', alt: 'Sample image 2', caption: 'Caption two' }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("open", "Boolean; shows the lightbox."),
            ("current-index", "Zero-based index of the currently displayed item."),
            ("loop", "Boolean (default true); wrap-around navigation."),
            ("show-caption", "Boolean; display the caption bar."),
            ("show-counter", "Boolean; display the item counter in the toolbar."),
            ("zoom-enabled", "Boolean; enable zoom controls."),
            ("label", "Accessible label for the dialog (default 'Media viewer')."),
            ("counter-format", "Counter template; use {current} and {total} (default '{current} of {total}')."),
        ],
        events=[
            ("mj-lightbox-open", "Fired when the lightbox opens; detail includes index and item."),
            ("mj-lightbox-close", "Fired when the lightbox closes; detail includes reason."),
            ("mj-lightbox-change", "Fired on navigation; detail includes index, previousIndex, and item."),
            ("mj-lightbox-zoom", "Fired when the zoom level changes; detail includes level."),
        ],
    ),
    ComponentDoc(
        tag="mj-overlay",
        title="Overlay",
        group="overlays",
        summary="Dimming/blocking backdrop primitive used internally by modal components.",
        description=(
            "<p><code>&lt;mj-overlay&gt;</code> is a low-level backdrop "
            "primitive. It renders a fixed-position scrim, manages a "
            "reference-counted scroll lock on <code>&lt;body&gt;</code>, and "
            "applies the <code>inert</code> attribute to background elements. "
            "It is composed automatically by <code>&lt;mj-dialog&gt;</code>, "
            "<code>&lt;mj-drawer&gt;</code>, <code>&lt;mj-lightbox&gt;</code>, "
            "and other modal components; application code rarely needs to use "
            "it directly.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>visible</code> attribute to show the backdrop. "
            "Use <code>variant</code> to choose between a dimmed scrim "
            "(<code>dim</code>, the default), a transparent click-blocker "
            "(<code>block</code>), or a fully transparent surface "
            "(<code>transparent</code>). Point <code>inert-target</code> at a "
            "CSS selector to apply <code>inert</code> to those elements. Call "
            "<code>show()</code> / <code>hide()</code> from script. Listen "
            "for <code>mj-overlay-click</code> to implement light-dismiss in "
            "custom overlays.</p>"
        ),
        example=(
            '<mj-overlay visible id="demo-overlay"></mj-overlay>\n'
            "<script>\n"
            "  document.getElementById('demo-overlay')\n"
            "    .addEventListener('mj-overlay-click', () => {\n"
            "      document.getElementById('demo-overlay').removeAttribute('visible');\n"
            "    });\n"
            "</script>"
        ),
        attributes=[
            ("visible", "Boolean; activates the backdrop."),
            ("variant", "dim (default) | block | transparent."),
            ("scroll-lock", "Boolean (default true); lock body scroll while visible."),
            ("inert-target", "CSS selector for elements to mark inert while visible."),
        ],
        events=[
            ("mj-overlay-click", "Cancelable; fired when the backdrop is clicked."),
            ("mj-overlay-visible", "Fired when the overlay activates."),
            ("mj-overlay-hidden", "Fired when the overlay deactivates."),
        ],
    ),
    ComponentDoc(
        tag="mj-toast-region",
        title="Toast Region",
        group="overlays",
        summary="Fixed-position manager for transient notification toasts.",
        description=(
            "<p><code>&lt;mj-toast-region&gt;</code> is a singleton placement "
            "and queuing manager for toast notifications. It controls a "
            "fixed-position live region, enforces a configurable "
            "<code>max-visible</code> limit, auto-dismisses toasts after a "
            "per-severity timeout, and pauses timers while the pointer or "
            "keyboard focus is inside the region. Queued toasts appear "
            "automatically as visible slots become free.</p>"
        ),
        how_to_use=(
            "<p>Place one <code>&lt;mj-toast-region&gt;</code> in the page "
            "(usually near <code>&lt;/body&gt;</code>). Add toasts by calling "
            "<code>add({ message, severity, duration })</code> on the element. "
            "<code>severity</code> is one of <code>info</code>, "
            "<code>success</code>, <code>warning</code>, or <code>error</code>. "
            "Set <code>duration</code> to <code>0</code> for a persistent toast. "
            "Call <code>dismissAll()</code> to clear all visible and queued "
            "toasts. Use <code>placement</code> to control the screen corner.</p>"
        ),
        example=(
            '<mj-toast-region id="toasts" placement="bottom-end"></mj-toast-region>\n'
            "<script>\n"
            "  const region = document.getElementById('toasts');\n"
            "  region.add({ message: 'File saved successfully.', severity: 'success' });\n"
            "  region.add({ message: 'Connection lost &mdash; retrying.', severity: 'warning' });\n"
            "  region.add({ message: 'Profile updated.', severity: 'info' });\n"
            "</script>"
        ),
        attributes=[
            ("placement", (
                "bottom-end (default) | bottom-start | bottom-center | "
                "top-end | top-start | top-center."
            )),
            ("max-visible", "Maximum number of toasts shown simultaneously (default 3)."),
            ("region-label", "aria-label for the live region (default 'Notifications')."),
            ("polite", "Boolean; force aria-live='polite' even for errors and warnings."),
        ],
        events=[
            ("mj-toast-add", "Fired when a toast is queued; detail includes id and descriptor."),
            ("mj-toast-show", "Fired when a toast becomes visible; detail includes id."),
            ("mj-toast-dismiss", "Fired when a toast is removed; detail includes id and reason."),
            ("mj-toast-queue-empty", "Fired when all toasts have been dismissed and the queue is empty."),
        ],
    ),
    ComponentDoc(
        tag="mj-notification-center",
        title="Notification Center",
        group="overlays",
        summary="Persistent notification history panel with read/unread tracking.",
        description=(
            "<p><code>&lt;mj-notification-center&gt;</code> maintains a "
            "scrollable list of persistent notifications with unread badges, "
            "date-based or category-based grouping, roving-tabindex keyboard "
            "navigation, and bulk actions (Mark all read, Clear all). Items "
            "are added via <code>addItem(descriptor)</code> and managed "
            "through the <code>items</code> property. The component is "
            "typically shown inside a popover or drawer rather than inline.</p>"
        ),
        how_to_use=(
            "<p>Place the element where it should render (e.g. inside an "
            "<code>&lt;mj-popover&gt;</code> or <code>&lt;mj-drawer&gt;</code>). "
            "Call <code>addItem({ id, title, body, timestamp, category })</code> "
            "to push new notifications; items default to <code>read: false</code>. "
            "Assign the <code>items</code> property directly to restore a saved "
            "list. Use <code>group-by=\"date\"</code> (default) or "
            "<code>group-by=\"category\"</code> or <code>group-by=\"none\"</code>. "
            "Set <code>show-mark-all-read=\"false\"</code> and "
            "<code>show-clear-all=\"false\"</code> to hide those action buttons.</p>"
        ),
        example=(
            '<mj-notification-center id="nc1"></mj-notification-center>\n'
            "<script>\n"
            "  const nc = document.getElementById('nc1');\n"
            "  nc.addItem({\n"
            "    id: 'n1', title: 'Deployment succeeded',\n"
            "    body: 'Production deploy v2.4.1 completed.',\n"
            "    timestamp: new Date().toISOString()\n"
            "  });\n"
            "  nc.addItem({\n"
            "    id: 'n2', title: 'New comment',\n"
            "    body: 'Alice commented on your pull request.',\n"
            "    timestamp: new Date().toISOString()\n"
            "  });\n"
            "</script>"
        ),
        attributes=[
            ("label", "Panel heading and aria-label for the list (default 'Notifications')."),
            ("group-by", "date (default) | category | none."),
            ("empty-message", "Message shown when the list is empty (default 'No notifications')."),
            ("max-items", "Maximum items retained before evicting oldest read item (default 100)."),
            ("loading", "Boolean; show a loading state."),
            ("show-mark-all-read", "Boolean (default true); show the Mark all read button."),
            ("show-clear-all", "Boolean (default true); show the Clear all button."),
        ],
        events=[
            ("mj-notification-select", "Fired when an item is clicked; detail includes item."),
            ("mj-notification-read", "Fired when an item is marked read; detail includes item."),
            ("mj-notification-dismiss", "Cancelable; fired when an item is dismissed; detail includes item."),
            ("mj-notification-mark-all-read", "Fired after all items are marked read; detail includes count."),
            ("mj-notification-clear-all", "Cancelable; fired before all items are cleared; detail includes count."),
        ],
    ),
    ComponentDoc(
        tag="mj-context-menu",
        title="Context Menu",
        group="overlays",
        summary="Pointer- or keyboard-invoked actions menu at cursor position.",
        description=(
            "<p><code>&lt;mj-context-menu&gt;</code> opens at the cursor "
            "position on right-click or the <kbd>ContextMenu</kbd> key over a "
            "target element. Items are supplied via the <code>items</code> "
            "JavaScript property as an array of descriptors supporting plain "
            "actions, <code>checkbox</code> items, <code>separator</code> "
            "lines, and <code>group</code> labels. Full keyboard navigation "
            "and type-ahead search are built in.</p>"
        ),
        how_to_use=(
            "<p>Wrap the target element in the default slot, or use "
            "<code>target-id</code> to reference an element elsewhere. Assign "
            "<code>items</code> in script; each item is "
            "<code>{ id, label, type?, disabled?, checked?, submenu? }</code>. "
            "Listen for <code>mj-context-menu-select</code> to handle "
            "activation. Call <code>show(x, y)</code> to open "
            "programmatically at specific coordinates; call <code>close()</code> "
            "to dismiss.</p>"
        ),
        example=(
            '<mj-context-menu id="ctx1">\n'
            '  <div style="padding:2rem;border:2px dashed #888;user-select:none;">'
            "Right-click here</div>\n"
            "</mj-context-menu>\n"
            "<script>\n"
            "  const ctx = document.getElementById('ctx1');\n"
            "  ctx.items = [\n"
            "    { id: 'copy',   label: 'Copy' },\n"
            "    { id: 'cut',    label: 'Cut' },\n"
            "    { id: 'paste',  label: 'Paste' },\n"
            "    { type: 'separator' },\n"
            "    { id: 'delete', label: 'Delete', disabled: true }\n"
            "  ];\n"
            "  ctx.addEventListener('mj-context-menu-select', e => {\n"
            "    console.log('Selected:', e.detail.item.id);\n"
            "  });\n"
            "</script>"
        ),
        attributes=[
            ("open", "Boolean; shows the menu (set automatically on right-click)."),
            ("target-id", "Id of an external element to listen for contextmenu events on."),
            ("label", "aria-label for the menu (default 'Actions')."),
            ("variant", "Reserved for future variants."),
        ],
        events=[
            ("mj-context-menu-before-open", "Cancelable; fired before the menu opens; detail includes x and y."),
            ("mj-context-menu-open", "Fired when the menu opens; detail includes x, y, and targetEl."),
            ("mj-context-menu-select", "Fired when an item is activated; detail includes item and optional checked."),
            ("mj-context-menu-close", "Fired when the menu closes; detail includes reason."),
        ],
    ),
    ComponentDoc(
        tag="mj-command-palette",
        title="Command Palette",
        group="overlays",
        summary="Keyboard-first, searchable command launcher with fuzzy matching.",
        description=(
            "<p><code>&lt;mj-command-palette&gt;</code> is a modal search "
            "interface for launching commands. It opens via a configurable "
            "global keyboard shortcut (default <kbd>Ctrl/Cmd+K</kbd>), "
            "performs fuzzy scoring against the <code>commands</code> array, "
            "persists recently used commands in <code>localStorage</code>, "
            "and supports per-command icons and keyboard shortcuts displayed "
            "in results.</p>"
        ),
        how_to_use=(
            "<p>Place the element anywhere in the page. Assign a "
            "<code>commands</code> array where each entry is "
            "<code>{ id, label, icon?, shortcut?, keywords?, disabled?, "
            "action?, href? }</code>. The global shortcut defaults to "
            "<code>Meta+k,Ctrl+k</code>; override with "
            "<code>global-shortcut</code>. Call <code>show()</code> to open "
            "programmatically; call <code>close()</code> to dismiss. Listen "
            "for <code>mj-command-palette-select</code> to handle command "
            "execution when no <code>action</code> function is provided.</p>"
        ),
        example=(
            '<mj-command-palette id="cp1" open placeholder="Search commands&hellip;">'
            "</mj-command-palette>\n"
            "<script>\n"
            "  const cp = document.getElementById('cp1');\n"
            "  cp.commands = [\n"
            "    { id: 'new-file',    label: 'New File',    icon: '&#x1F4C4;', shortcut: 'Ctrl+N' },\n"
            "    { id: 'open-file',   label: 'Open File',   icon: '&#x1F4C2;', shortcut: 'Ctrl+O' },\n"
            "    { id: 'save',        label: 'Save',         icon: '&#x1F4BE;', shortcut: 'Ctrl+S' },\n"
            "    { id: 'preferences', label: 'Preferences',  icon: '&#x2699;' }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("open", "Boolean; shows the command palette."),
            ("placeholder", "Input placeholder text (default 'Type a command…')."),
            ("global-shortcut", "Comma-separated shortcut combos that open the palette (default 'Meta+k,Ctrl+k')."),
            ("empty-message", "Message shown when no commands match (default 'No matching commands')."),
            ("max-results", "Maximum number of filtered results shown (default 20)."),
            ("max-recent", "Maximum recently used commands remembered (default 5)."),
            ("debounce", "Input debounce delay in milliseconds (default 120)."),
            ("label", "aria-label for the dialog (default 'Command palette')."),
        ],
        events=[
            ("mj-command-palette-open", "Fired when the palette opens."),
            ("mj-command-palette-close", "Fired when the palette closes; detail includes reason."),
            ("mj-command-palette-query", "Fired on each (debounced) input change; detail includes query."),
            ("mj-command-palette-results", "Fired after filtering; detail includes results array and query."),
            ("mj-command-palette-select", "Cancelable; fired when a command is activated; detail includes command."),
        ],
    ),
    ComponentDoc(
        tag="mj-tour",
        title="Tour",
        group="overlays",
        summary="Multi-step coach-mark tour that spotlights page elements.",
        description=(
            "<p><code>&lt;mj-tour&gt;</code> guides users through a feature or "
            "onboarding flow by displaying a sequence of anchored coach-mark "
            "cards. Each step spotlights a target element with a full-viewport "
            "overlay cutout, animates the card into position, and updates "
            "progress dots and a step counter. Navigation is possible with "
            "Back / Next buttons or keyboard arrow keys; <kbd>Escape</kbd> "
            "skips the tour. Completion and dismissal state can be persisted "
            "to <code>localStorage</code> via <code>storage-key</code>.</p>"
        ),
        how_to_use=(
            "<p>Add the element to the page and assign a <code>steps</code> "
            "array where each entry is "
            "<code>{ title, body, targetId?, placement? }</code>. "
            "<code>placement</code> accepts <code>bottom</code>, "
            "<code>top</code>, <code>end</code>, or <code>start</code>. "
            "Call <code>start()</code> or set the <code>active</code> "
            "attribute to begin. Call <code>skip()</code> to dismiss early "
            "or <code>reset()</code> to clear persisted state. Use "
            "<code>next()</code> and <code>back()</code> to navigate "
            "programmatically.</p>"
        ),
        example=(
            '<button id="start-tour-btn" onclick="document.getElementById(\'tour1\').start();">'
            "Start tour</button>\n"
            '<p id="feature-a" style="margin-top:2rem;padding:1rem;border:1px solid #ccc;">'
            "Feature A</p>\n"
            '<p id="feature-b" style="margin-top:1rem;padding:1rem;border:1px solid #ccc;">'
            "Feature B</p>\n"
            '<mj-tour id="tour1"></mj-tour>\n'
            "<script>\n"
            "  const tour = document.getElementById('tour1');\n"
            "  tour.steps = [\n"
            "    { title: 'Welcome', body: 'This tour walks you through the key features.' },\n"
            "    { title: 'Feature A', body: 'Use Feature A to accomplish your goal.', "
            "targetId: 'feature-a', placement: 'bottom' },\n"
            "    { title: 'Feature B', body: 'Feature B helps you do even more.', "
            "targetId: 'feature-b', placement: 'top' }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("active", "Boolean; starts/shows the tour."),
            ("current-step", "Zero-based index of the current step."),
            ("show-progress-dots", "Boolean (default true); display progress dots in the card."),
            ("show-counter", "Boolean (default true); display step counter text."),
            ("counter-format", "Counter template; use {current} and {total} (default 'Step {current} of {total}')."),
            ("skip-label", "Accessible label for the skip button (default 'Skip tour')."),
            ("back-label", "Label for the back button (default 'Back')."),
            ("next-label", "Label for the next button (default 'Next')."),
            ("done-label", "Label for the next button on the final step (default 'Done')."),
            ("storage-key", "localStorage key for persisting dismissed/completed state."),
            ("spotlight-padding", "Padding in pixels around the spotlight cutout (default 8)."),
        ],
        events=[
            ("mj-tour-start", "Fired when the tour begins; detail includes totalSteps."),
            ("mj-tour-step", "Cancelable; fired before each step is shown; detail includes step, totalSteps, and stepDef."),
            ("mj-tour-next", "Fired when advancing to the next step; detail includes step and totalSteps."),
            ("mj-tour-back", "Fired when returning to the previous step; detail includes step and totalSteps."),
            ("mj-tour-skip", "Fired when the user skips the tour; detail includes step."),
            ("mj-tour-complete", "Fired when the last step is finished; detail includes totalSteps."),
        ],
    ),
]
