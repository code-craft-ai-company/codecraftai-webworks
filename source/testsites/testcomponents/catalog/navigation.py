"""
    navigation.py

    Catalog entries for the 'Navigation' component group.

    Every navigation component exposed by the mj-* library is described here
    as a ComponentDoc instance.  The module-level ``COMPONENTS`` list is
    consumed by the testcomponents site to build the live component catalog.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-link",
        title="Link",
        group="navigation",
        summary="A styled navigation hyperlink with variant, external-link, and disabled support.",
        description=(
            "<p><code>&lt;mj-link&gt;</code> wraps a real <code>&lt;a&gt;</code> "
            "element and adds styling variants, safe external-link handling "
            "(automatic <code>noopener noreferrer</code>), and a disabled state "
            "that blocks navigation while keeping the element in the tab order. "
            "Use it anywhere a styled hyperlink is needed in prose or standalone "
            "call-to-action contexts.</p>"
        ),
        how_to_use=(
            "<p>Set <code>href</code> and place link text between the tags. "
            "Choose a <code>variant</code> (<code>default</code>, "
            "<code>subtle</code>, or <code>standalone</code>) to match the "
            "surrounding context. Add <code>external</code> to render an "
            "external-link icon and open in a new tab. Use the "
            "<code>prefix</code> slot for a leading icon. Listen for "
            "<code>mj-link-click</code> to intercept navigation; the event is "
            "cancelable.</p>"
        ),
        example=(
            '<mj-link href="https://example.com">Default link</mj-link>\n'
            '<mj-link href="https://example.com" variant="subtle">Subtle link</mj-link>\n'
            '<mj-link href="https://example.com" variant="standalone">Standalone link</mj-link>\n'
            '<mj-link href="https://example.com" external>Opens externally</mj-link>\n'
            "<mj-link disabled>Disabled link</mj-link>"
        ),
        attributes=[
            ("href", "The destination URL."),
            ("variant", "default | subtle | standalone visual style."),
            ("external", "Boolean; opens in a new tab with noopener noreferrer."),
            ("target", "Forwarded to the underlying <a> element."),
            ("rel", "Forwarded to the underlying <a> element."),
            ("download", "Forwarded to the underlying <a> element."),
            ("disabled", "Boolean; blocks navigation and marks aria-disabled."),
            ("visited-cue", "Boolean; shows a distinct color for visited links."),
        ],
        events=[
            ("mj-link-click", "Cancelable; fired on activation with href and external detail."),
        ],
    ),
    ComponentDoc(
        tag="mj-app-bar",
        title="App Bar",
        group="navigation",
        summary="Top-of-page branding and navigation bar with responsive mobile drawer.",
        description=(
            "<p><code>&lt;mj-app-bar&gt;</code> renders a "
            "<code>&lt;header role=\"banner\"&gt;</code> landmark containing "
            "brand, navigation, and actions slots. On narrow viewports the "
            "navigation collapses into a slide-in drawer toggled by a hamburger "
            "button. When <code>transparent</code> is set the bar becomes opaque "
            "once the page is scrolled past the configured threshold.</p>"
        ),
        how_to_use=(
            "<p>Place brand content in the <code>brand</code> slot, navigation "
            "links in the <code>navigation</code> slot, and icon buttons in the "
            "<code>actions</code> slot. Add <code>sticky</code> to pin the bar "
            "to the top of the viewport. Use <code>mobile-navigation</code> to "
            "provide a different set of links for the drawer. Listen for "
            "<code>mj-app-bar-open</code> and <code>mj-app-bar-close</code> to "
            "react to drawer state changes.</p>"
        ),
        example=(
            '<mj-app-bar sticky>\n'
            '  <span slot="brand"><strong>MyApp</strong></span>\n'
            '  <a slot="navigation" href="#">Home</a>\n'
            '  <a slot="navigation" href="#">Docs</a>\n'
            '  <a slot="navigation" href="#">Blog</a>\n'
            '  <button slot="actions" aria-label="Search">&#128269;</button>\n'
            "</mj-app-bar>"
        ),
        attributes=[
            ("sticky", "Boolean; pins the bar to the top of the viewport."),
            ("open", "Boolean; opens the mobile navigation drawer."),
            ("transparent", "Boolean; starts transparent and gains a shadow on scroll."),
            ("scrolled", "Boolean; set automatically when the page is scrolled past the threshold."),
            ("nav-label", "Accessible label for the inner <nav> element."),
            ("scroll-threshold", "Scroll distance in pixels before scrolled is set (default 16)."),
        ],
        events=[
            ("mj-app-bar-open", "Cancelable; fired when the mobile drawer is about to open."),
            ("mj-app-bar-close", "Cancelable; fired when the mobile drawer is about to close."),
            ("mj-app-bar-scroll", "Fired when the scrolled state changes; detail includes scrolled and scrollY."),
        ],
    ),
    ComponentDoc(
        tag="mj-side-nav",
        title="Side Nav",
        group="navigation",
        summary="Side navigation panel with static, collapsible, and overlay-drawer modes.",
        description=(
            "<p><code>&lt;mj-side-nav&gt;</code> is a <code>&lt;nav&gt;</code> "
            "landmark for persistent or dismissible side navigation. Three "
            "modes cover common layouts: <code>static</code> (always visible), "
            "<code>collapsible</code> (slides closed with a built-in toggle "
            "button, optionally persisting its open/closed state in "
            "<code>localStorage</code>), and <code>overlay-drawer</code> "
            "(slides in over content with a scrim backdrop). Roving tabindex "
            "manages keyboard focus across slotted items.</p>"
        ),
        how_to_use=(
            "<p>Set <code>mode</code> to the desired layout. Place links or "
            "buttons directly in the default slot; mark the active item with "
            "<code>aria-current=\"page\"</code>. Use the <code>header</code> "
            "and <code>footer</code> named slots for logo or utility content. "
            "For overlay-drawer mode, toggle the <code>open</code> attribute "
            "from an external trigger. Set <code>persist-state</code> on "
            "collapsible mode to remember the panel width across page loads.</p>"
        ),
        example=(
            '<mj-side-nav mode="static" style="height:200px">\n'
            '  <a href="#" aria-current="page">Dashboard</a>\n'
            '  <a href="#">Reports</a>\n'
            '  <a href="#">Settings</a>\n'
            "</mj-side-nav>"
        ),
        attributes=[
            ("mode", "static | collapsible | overlay-drawer layout mode."),
            ("open", "Boolean; controls the open state for collapsible and overlay-drawer modes."),
            ("edge", "start | end; which edge the overlay-drawer slides from."),
            ("nav-label", "Accessible label for the <nav> landmark."),
            ("persist-state", "Boolean; saves open/closed state in localStorage (collapsible mode)."),
            ("persist-key", "localStorage key used when persist-state is enabled."),
        ],
        events=[
            ("mj-side-nav-open", "Cancelable; fired when the panel is about to open."),
            ("mj-side-nav-close", "Cancelable; fired when the panel is about to close."),
        ],
    ),
    ComponentDoc(
        tag="mj-breadcrumb",
        title="Breadcrumb",
        group="navigation",
        summary="An ordered hierarchy trail with automatic current-page marking and ellipsis collapse.",
        description=(
            "<p><code>&lt;mj-breadcrumb&gt;</code> wraps slotted anchor elements "
            "in a <code>&lt;nav aria-label&gt;</code> landmark and an ordered "
            "list. The last item automatically receives "
            "<code>aria-current=\"page\"</code>. When the breadcrumb path is "
            "deeper than <code>max-visible</code> allows, intermediate items "
            "are hidden behind an expandable ellipsis button.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;a&gt;</code> elements in the default slot — one "
            "per level of hierarchy. The rightmost item is automatically marked "
            "as current, or set the <code>current</code> attribute on any item "
            "to override. Set <code>max-visible</code> to enable ellipsis "
            "collapse and <code>separator</code> to customise the divider "
            "character.</p>"
        ),
        example=(
            "<mj-breadcrumb>\n"
            '  <a href="/">Home</a>\n'
            '  <a href="/products">Products</a>\n'
            '  <a href="/products/widgets">Widgets</a>\n'
            '  <a href="/products/widgets/blue">Blue Widget</a>\n'
            "</mj-breadcrumb>"
        ),
        attributes=[
            ("separator", "Divider character rendered between items (default /)."),
            ("max-visible", "Maximum number of items shown before collapsing to an ellipsis."),
            ("always-show-last", "Number of trailing items always kept visible when collapsed (default 1)."),
            ("nav-label", "Accessible label for the <nav> landmark."),
        ],
        events=[
            ("mj-breadcrumb-expand", "Cancelable; fired when the ellipsis expand button is clicked."),
        ],
    ),
    ComponentDoc(
        tag="mj-tabs",
        title="Tabs",
        group="navigation",
        summary="WAI-ARIA tablist/tab/tabpanel composite with automatic or manual activation.",
        description=(
            "<p><code>&lt;mj-tabs&gt;</code> implements the ARIA tabs pattern "
            "with roving tabindex on the tab strip and linked tab panels. "
            "Tabs and panels are associated by index. Supports "
            "<code>horizontal</code> and <code>vertical</code> orientation, "
            "<code>automatic</code> and <code>manual</code> activation, and "
            "<code>default</code>, <code>pills</code>, and <code>enclosed</code> "
            "visual variants. An animated indicator bar tracks the selected "
            "tab.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;button slot=\"tab\"&gt;</code> elements for each "
            "tab label, then add the corresponding panel content as direct "
            "children (no slot name). The component pairs them by position. "
            "Set <code>selected</code> to the id of the tab to pre-select. "
            "Use <code>activation=\"manual\"</code> if you need the user to "
            "press Enter/Space to confirm a tab change.</p>"
        ),
        example=(
            "<mj-tabs>\n"
            '  <button slot="tab">Overview</button>\n'
            '  <button slot="tab">Details</button>\n'
            '  <button slot="tab">Reviews</button>\n'
            "  <div><p>Overview panel content.</p></div>\n"
            "  <div><p>Details panel content.</p></div>\n"
            "  <div><p>Reviews panel content.</p></div>\n"
            "</mj-tabs>"
        ),
        attributes=[
            ("selected", "Id of the initially selected tab."),
            ("variant", "default | pills | enclosed visual style."),
            ("orientation", "horizontal | vertical tab strip layout."),
            ("activation", "automatic | manual keyboard activation mode."),
            ("tablist-label", "Accessible label for the tablist role element."),
        ],
        events=[
            ("mj-tabs-change", "Fired when the selected tab changes; detail includes selectedId, previousId, selectedTab, and selectedPanel."),
        ],
    ),
    ComponentDoc(
        tag="mj-nav-stepper",
        title="Nav Stepper",
        group="navigation",
        summary="An ordered step-indicator strip for multi-step flows with complete/error/upcoming states.",
        description=(
            "<p><code>&lt;mj-nav-stepper&gt;</code> renders an ordered list of "
            "step indicators. Each step button shows its number, a check mark "
            "when complete, or an error icon when in error state. The "
            "<code>current</code> attribute drives which step is active; steps "
            "before it are automatically marked complete. In "
            "<code>linear</code> mode (the default) upcoming steps are "
            "disabled. In non-linear mode any step can be reached directly.</p>"
        ),
        how_to_use=(
            "<p>Place one element per step in the default slot — the text "
            "content becomes the step label. Set <code>current</code> to the "
            "zero-based index of the active step. Override individual step "
            "status with a <code>status</code> attribute on the slotted "
            "element. Set <code>orientation</code> to "
            "<code>vertical</code> for a column layout. Add "
            "<code>compact</code> to hide labels and show only the indicator "
            "circles.</p>"
        ),
        example=(
            '<mj-nav-stepper current="1">\n'
            "  <span>Account</span>\n"
            "  <span>Profile</span>\n"
            "  <span>Payment</span>\n"
            "  <span>Review</span>\n"
            "</mj-nav-stepper>"
        ),
        attributes=[
            ("current", "Zero-based index of the current step."),
            ("orientation", "horizontal | vertical layout."),
            ("linear", "Boolean; when true (default) upcoming steps are disabled."),
            ("compact", "Boolean; hides step labels, showing only indicator circles."),
            ("label", "Accessible label for the ordered list."),
        ],
        events=[
            ("mj-nav-stepper-change", "Cancelable; fired when a step is clicked; detail includes index, previousIndex, and step element."),
        ],
    ),
    ComponentDoc(
        tag="mj-wizard",
        title="Wizard",
        group="navigation",
        summary="A multi-step guided flow with built-in Back/Next/Submit navigation and form validation.",
        description=(
            "<p><code>&lt;mj-wizard&gt;</code> composes "
            "<code>&lt;mj-nav-stepper&gt;</code> with a content panel and a "
            "navigation bar to produce a complete wizard shell. One step is "
            "visible at a time. In <code>linear</code> mode (default) "
            "<code>checkValidity()</code> is called on all forms in the current "
            "step before advancing. A live region announces the current step "
            "for screen readers. Focus is moved into each step on entry.</p>"
        ),
        how_to_use=(
            "<p>Place one element per step in the default slot, giving each a "
            "<code>label</code> attribute for the stepper and announcement. "
            "Set <code>stepper-position</code> to <code>top</code> (default), "
            "<code>side</code>, or <code>none</code>. Override button labels "
            "with <code>next-label</code>, <code>back-label</code>, and "
            "<code>submit-label</code>. Handle <code>mj-wizard-submit</code> to "
            "receive the aggregated <code>FormData</code> and call your save "
            "logic.</p>"
        ),
        example=(
            '<mj-wizard label="Sign up">\n'
            '  <section label="Account">\n'
            "    <h3>Create account</h3>\n"
            '    <p><label>Email <input type="email" required></label></p>\n'
            "  </section>\n"
            '  <section label="Profile">\n'
            "    <h3>Your profile</h3>\n"
            '    <p><label>Name <input type="text" required></label></p>\n'
            "  </section>\n"
            '  <section label="Done">\n'
            "    <h3>All set!</h3>\n"
            "    <p>Review and submit your details.</p>\n"
            "  </section>\n"
            "</mj-wizard>"
        ),
        attributes=[
            ("current", "Zero-based index of the current step."),
            ("linear", "Boolean; validates the current step's forms before advancing (default true)."),
            ("stepper-position", "top | side | none position of the nav stepper."),
            ("label", "Accessible label for the wizard group."),
            ("next-label", "Label for the Next button."),
            ("back-label", "Label for the Back button."),
            ("submit-label", "Label for the Submit button shown on the last step."),
        ],
        events=[
            ("mj-wizard-before-change", "Cancelable; fired before navigating between steps; detail includes from, to, and direction."),
            ("mj-wizard-step-leave", "Fired when leaving a step; detail includes index and step element."),
            ("mj-wizard-step-enter", "Fired when entering a step; detail includes index and step element."),
            ("mj-wizard-change", "Fired after a step transition completes; detail includes from, to, and direction."),
            ("mj-wizard-submit", "Cancelable; fired on Submit click; detail includes aggregated FormData."),
            ("mj-wizard-complete", "Fired after mj-wizard-submit when not cancelled."),
        ],
    ),
    ComponentDoc(
        tag="mj-pagination",
        title="Pagination",
        group="navigation",
        summary="Page navigation with numbered buttons, ellipsis, Previous/Next, and optional summary.",
        description=(
            "<p><code>&lt;mj-pagination&gt;</code> renders a "
            "<code>&lt;nav&gt;</code> landmark with Previous/Next controls and "
            "an optional numbered page list. Large page counts are collapsed "
            "with ellipsis using configurable boundary and sibling counts. "
            "Three variants are available: <code>full</code> (numbered list), "
            "<code>compact</code> (Page X of Y label), and "
            "<code>simple</code> (Previous/Next only). An optional results "
            "summary shows the record range for the current page.</p>"
        ),
        how_to_use=(
            "<p>Set <code>page</code> (1-based) and <code>total-pages</code>. "
            "Listen for <code>mj-pagination-change</code> and update "
            "<code>page</code> in the handler. Add <code>show-summary</code> "
            "along with <code>total-items</code> and <code>page-size</code> "
            "to display a &ldquo;Showing X&ndash;Y of Z&rdquo; summary. "
            "Use <code>variant=\"compact\"</code> for narrow containers.</p>"
        ),
        example=(
            '<mj-pagination page="3" total-pages="10" show-summary\n'
            '               total-items="97" page-size="10">\n'
            "</mj-pagination>"
        ),
        attributes=[
            ("page", "Current page number (1-based)."),
            ("total-pages", "Total number of pages."),
            ("total-items", "Total record count used for the summary."),
            ("page-size", "Records per page used for the summary."),
            ("sibling-count", "Number of page buttons shown on each side of the current page (default 1)."),
            ("boundary-count", "Number of page buttons always shown at each end (default 1)."),
            ("variant", "full | compact | simple layout."),
            ("show-summary", "Boolean; shows a results-range summary."),
            ("nav-label", "Accessible label for the <nav> landmark."),
            ("disabled", "Boolean; disables all controls."),
        ],
        events=[
            ("mj-pagination-change", "Cancelable; fired on page navigation; detail includes page, previousPage, and pageSize."),
        ],
    ),
    ComponentDoc(
        tag="mj-toc",
        title="Table of Contents",
        group="navigation",
        summary="An in-page table of contents with IntersectionObserver scroll-spy and dynamic content support.",
        description=(
            "<p><code>&lt;mj-toc&gt;</code> scans the headings inside a "
            "target element and builds a linked list of section anchors. "
            "As the user scrolls, an IntersectionObserver highlights the "
            "active section with <code>aria-current=\"true\"</code>. A "
            "MutationObserver automatically rebuilds the list when the "
            "target&rsquo;s DOM changes. Headings without ids receive "
            "slugified ids automatically.</p>"
        ),
        how_to_use=(
            "<p>Set <code>target</code> to a CSS selector pointing at the "
            "article or main element that contains the headings. Use "
            "<code>depth</code> to control how many heading levels are "
            "included (default 2, meaning h2 and h3). Add <code>sticky</code> "
            "to pin the TOC while scrolling. Set <code>title</code> to render "
            "a visible heading above the link list. Override "
            "<code>offset</code> to compensate for a sticky app bar.</p>"
        ),
        example=(
            '<div id="article">\n'
            "  <h2>Introduction</h2>\n"
            "  <p>Some text about the introduction.</p>\n"
            "  <h2>Getting Started</h2>\n"
            "  <p>Setup instructions go here.</p>\n"
            "  <h3>Installation</h3>\n"
            "  <p>Install details.</p>\n"
            "  <h2>API Reference</h2>\n"
            "  <p>API details go here.</p>\n"
            "</div>\n"
            '<mj-toc target="#article" title="On this page"></mj-toc>'
        ),
        attributes=[
            ("target", "CSS selector of the element whose headings are scanned."),
            ("depth", "Number of heading levels to include starting from h2 (default 2)."),
            ("heading-selector", "Custom CSS selector overriding the auto-generated heading selector."),
            ("title", "Optional visible title rendered above the link list."),
            ("sticky", "Boolean; positions the TOC as sticky."),
            ("nav-label", "Accessible label for the <nav> landmark."),
            ("offset", "Pixel offset applied to IntersectionObserver rootMargin to account for sticky headers."),
        ],
        events=[
            ("mj-toc-active-change", "Fired when the active section changes; detail includes id, element, and previousId."),
            ("mj-toc-navigate", "Cancelable; fired when a TOC link is clicked; detail includes id, element, and originalEvent."),
        ],
    ),
    ComponentDoc(
        tag="mj-skip-link",
        title="Skip Link",
        group="navigation",
        summary="A visually hidden skip-to-content link that satisfies WCAG 2.4.1 Bypass Blocks.",
        description=(
            "<p><code>&lt;mj-skip-link&gt;</code> renders a native "
            "<code>&lt;a&gt;</code> that is clipped off-screen until it "
            "receives keyboard focus, at which point it appears at the top of "
            "the page. Activating it moves focus to the element identified by "
            "<code>target</code>, temporarily making non-focusable landmarks "
            "focusable and cleaning up afterwards. It should be the first "
            "focusable element on the page.</p>"
        ),
        how_to_use=(
            "<p>Place the component as the very first child of "
            "<code>&lt;body&gt;</code>. Set <code>target</code> to the id of "
            "the main content landmark (e.g. <code>#main</code>). Override the "
            "visible label via the <code>label</code> attribute or by slotting "
            "text. Use <code>variant=\"inline\"</code> to keep the link always "
            "visible, which is useful for testing.</p>"
        ),
        example=(
            '<mj-skip-link target="#main-content"></mj-skip-link>\n'
            '<main id="main-content">\n'
            "  <h1>Page heading</h1>\n"
            "  <p>Main content begins here.</p>\n"
            "</main>"
        ),
        attributes=[
            ("target", "CSS selector or id of the element to focus (default #main)."),
            ("label", "Visible label of the link; defaults to Skip to main content."),
            ("variant", "default (visually hidden until focused) | inline (always visible)."),
        ],
        events=[
            ("mj-skip-link-activate", "Cancelable; fired on activation; detail includes target and originalEvent."),
        ],
    ),
    ComponentDoc(
        tag="mj-footer-nav",
        title="Footer Nav",
        group="navigation",
        summary="A site-wide footer with grouped navigation columns, brand slot, social area, and legal bar.",
        description=(
            "<p><code>&lt;mj-footer-nav&gt;</code> renders a "
            "<code>&lt;footer role=\"contentinfo\"&gt;</code> landmark with a "
            "responsive multi-column grid of navigation groups. Slotted group "
            "elements are distributed across the columns; the number of columns "
            "can be fixed with the <code>columns</code> attribute. Optional "
            "slots handle brand identity, social links, and the legal / "
            "copyright bar.</p>"
        ),
        how_to_use=(
            "<p>Place navigation group elements (e.g. <code>&lt;nav&gt;</code> "
            "or <code>&lt;ul&gt;</code> with links) in the default slot. Use "
            "the <code>brand</code>, <code>social</code>, and "
            "<code>legal</code> named slots for the corresponding areas. Set "
            "<code>copyright</code> to a company name — the component "
            "prepends the current year automatically. Listen for "
            "<code>mj-footer-nav-navigate</code> to track link clicks "
            "across all groups.</p>"
        ),
        example=(
            '<mj-footer-nav copyright="Acme Corp" columns="3">\n'
            '  <span slot="brand"><strong>Acme</strong></span>\n'
            "  <nav>\n"
            "    <strong>Product</strong>\n"
            '    <ul><li><a href="#">Features</a></li><li><a href="#">Pricing</a></li></ul>\n'
            "  </nav>\n"
            "  <nav>\n"
            "    <strong>Company</strong>\n"
            '    <ul><li><a href="#">About</a></li><li><a href="#">Blog</a></li></ul>\n'
            "  </nav>\n"
            "  <nav>\n"
            "    <strong>Legal</strong>\n"
            '    <ul><li><a href="#">Privacy</a></li><li><a href="#">Terms</a></li></ul>\n'
            "  </nav>\n"
            "</mj-footer-nav>"
        ),
        attributes=[
            ("variant", "minimal | centered layout variant."),
            ("columns", "Fixed column count for the navigation grid."),
            ("copyright", "Company name; the year is prepended automatically."),
            ("nav-label", "Accessible label for the footer landmark."),
            ("heading-level", "Heading level used for group titles."),
        ],
        events=[
            ("mj-footer-nav-navigate", "Cancelable; fired on any footer link click; detail includes href and group label."),
        ],
    ),
    ComponentDoc(
        tag="mj-menu",
        title="Menu",
        group="navigation",
        summary="A WAI-ARIA menu popup with keyboard navigation, typeahead, and dropdown/context variants.",
        description=(
            "<p><code>&lt;mj-menu&gt;</code> implements the ARIA menu pattern "
            "with <code>role=\"menu\"</code> and "
            "<code>aria-activedescendant</code> for keyboard focus management. "
            "It supports <code>menuitem</code>, "
            "<code>menuitemcheckbox</code>, and <code>menuitemradio</code> "
            "roles, typeahead search, and auto-positioning relative to a "
            "trigger element. Four variants are available: "
            "<code>dropdown</code>, <code>flyout</code>, "
            "<code>mega</code>, and <code>context</code>.</p>"
        ),
        how_to_use=(
            "<p>Assign an id to the trigger element and pass it to "
            "<code>anchor</code>. Toggle the <code>open</code> attribute on "
            "the menu from the trigger&rsquo;s click handler. Slot "
            "<code>role=\"menuitem\"</code> elements as direct children; add "
            "<code>data-menu-item</code> to any element that should behave as "
            "an item. Listen for <code>mj-menu-select</code> to handle item "
            "activation. The menu closes automatically on Escape, click "
            "outside, or Tab.</p>"
        ),
        example=(
            '<button id="menu-trigger"\n'
            '        aria-haspopup="menu"\n'
            '        onclick="this.nextElementSibling.setAttribute(\'open\', \'\')">\n'
            "  Options\n"
            "</button>\n"
            '<mj-menu anchor="menu-trigger" close-on-select>\n'
            '  <div role="menuitem">Edit</div>\n'
            '  <div role="menuitem">Duplicate</div>\n'
            '  <div role="menuitem">Archive</div>\n'
            '  <div role="menuitem" aria-disabled="true">Delete</div>\n'
            "</mj-menu>"
        ),
        attributes=[
            ("open", "Boolean; shows the menu popup."),
            ("anchor", "CSS selector or id of the trigger element used for positioning."),
            ("placement", "Preferred placement relative to the anchor (default bottom-start)."),
            ("variant", "dropdown | flyout | mega | context visual variant."),
            ("label", "Accessible label for the menu role element."),
            ("close-on-select", "Boolean; closes the menu after an item is selected (default true)."),
        ],
        events=[
            ("mj-menu-open", "Cancelable; fired when the menu is about to open."),
            ("mj-menu-close", "Cancelable; fired when the menu is about to close; detail includes reason."),
            ("mj-menu-select", "Cancelable; fired when a menu item is activated; detail includes item, value, and checked."),
            ("mj-menu-item-focus", "Fired when the virtual focus moves to an item."),
        ],
    ),
    ComponentDoc(
        tag="mj-tree-nav",
        title="Tree Nav",
        group="navigation",
        summary="A hierarchical navigation tree with expand/collapse, aria-activedescendant, and persist-state.",
        description=(
            "<p><code>&lt;mj-tree-nav&gt;</code> implements the WAI-ARIA tree "
            "pattern inside a <code>&lt;nav&gt;</code> landmark. It uses "
            "<code>aria-activedescendant</code> on the tree root so a single "
            "tab stop manages the entire tree. Features include keyboard "
            "expand/collapse, typeahead search, auto-expansion of the current "
            "item&rsquo;s ancestors, and optional "
            "<code>sessionStorage</code>-backed persist of expanded state "
            "across page loads.</p>"
        ),
        how_to_use=(
            "<p>Nest <code>&lt;li&gt;</code> elements directly in the "
            "component; add a <code>&lt;ul&gt;</code> inside any "
            "<code>&lt;li&gt;</code> to create a subtree. The component "
            "automatically wires ARIA roles, levels, and expand/collapse "
            "buttons. Set <code>current</code> to the id or href of the active "
            "item; the component marks it with "
            "<code>aria-current=\"page\"</code> and expands its ancestors. "
            "Enable <code>persist-state</code> to remember expanded branches "
            "in sessionStorage.</p>"
        ),
        example=(
            '<mj-tree-nav nav-label="Site navigation">\n'
            "  <li><a href=\"#\">Home</a></li>\n"
            "  <li>\n"
            "    <a href=\"#\">Products</a>\n"
            "    <ul>\n"
            "      <li><a href=\"#\">Widgets</a></li>\n"
            "      <li><a href=\"#\">Gadgets</a></li>\n"
            "    </ul>\n"
            "  </li>\n"
            "  <li><a href=\"#\">About</a></li>\n"
            "</mj-tree-nav>"
        ),
        attributes=[
            ("nav-label", "Accessible label for the <nav> landmark."),
            ("current", "Id or href of the currently active tree item."),
            ("auto-expand", "Boolean; automatically expands ancestors of the current item (default true)."),
            ("compact", "Boolean; reduces item row height."),
            ("persist-state", "Boolean; saves expanded state to sessionStorage."),
            ("persist-key", "sessionStorage key used when persist-state is enabled."),
        ],
        events=[
            ("mj-tree-nav-navigate", "Cancelable; fired when a tree item link is clicked; detail includes item and href."),
            ("mj-tree-nav-expand", "Cancelable; fired when a branch is about to expand; detail includes item and id."),
            ("mj-tree-nav-collapse", "Cancelable; fired when a branch is about to collapse; detail includes item and id."),
            ("mj-tree-nav-focus", "Fired when virtual focus moves to a tree item."),
        ],
    ),
]
