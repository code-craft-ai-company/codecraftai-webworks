"""
    layout.py

    Catalog entries for the 'Layout' component group.

    Every component that arranges, contains, or spaces other components
    belongs here: surfaces, grids, stacks, disclosure panels, split views,
    scroll areas, feeds, and dock-based app shells.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-card",
        title="Card",
        group="layout",
        summary="A contained content surface grouping media, header, body, and footer.",
        description=(
            "<p><code>&lt;mj-card&gt;</code> wraps an article of content into a "
            "visually distinct elevated box. It supports an optional hero image "
            "(<code>media</code> slot), a badge overlay, an attribute-driven "
            "heading/subheading pair, a default body slot, and a footer slot for "
            "actions. Set <code>elevation</code> to control shadow versus outlined "
            "appearance, <code>orientation</code> to switch between vertical and "
            "horizontal image placement, and <code>href</code> to make the whole "
            "card a clickable link without extra markup.</p>"
        ),
        how_to_use=(
            "<p>Place body content between the tags for the default slot. Use the "
            "<code>heading</code> and <code>subheading</code> attributes to render "
            "a built-in header, or supply a <code>slot=\"header\"</code> element "
            "for full control. Add <code>slot=\"media\"</code> to an "
            "<code>&lt;img&gt;</code> for a hero image. Use <code>slot=\"footer\"</code> "
            "for action buttons. Set <code>loading</code> to show a shimmer "
            "animation while content is fetching. Use the <code>headingLevel</code> "
            "property (not an attribute) to override the generated heading element "
            "level (default h3).</p>"
        ),
        example=(
            '<mj-card heading="Mountain Hike" subheading="July 2025" elevation="raised" style="max-width:22rem">\n'
            '  <img slot="media" src="https://picsum.photos/seed/hike/400/200" alt="Mountain trail" />\n'
            "  <p>A beautiful trek through alpine meadows with panoramic views.</p>\n"
            '  <div slot="footer">\n'
            '    <mj-button variant="primary" size="sm">Book now</mj-button>\n'
            '    <mj-button variant="secondary" size="sm">Learn more</mj-button>\n'
            "  </div>\n"
            "</mj-card>"
        ),
        attributes=[
            ("heading", "Card heading text rendered as an h3 (or the level set via headingLevel)."),
            ("subheading", "Secondary text beneath the heading."),
            ("elevation", "raised (default) | flat | outlined controls shadow and border."),
            ("orientation", "vertical (default) | horizontal places the media slot on the side."),
            ("href", "Makes the entire card a clickable link to this URL."),
            ("loading", "Boolean; shows a shimmer overlay and marks aria-busy."),
            ("disabled", "Boolean; disables the card link when href is set."),
            ("aspect-ratio", "Aspect-ratio token applied to the media region."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-surface",
        title="Surface",
        group="layout",
        summary="A generic content wrapper providing elevation, padding, and radius.",
        description=(
            "<p><code>&lt;mj-surface&gt;</code> is the fundamental container "
            "primitive of the library. It unifies Panel, Section, and Container "
            "patterns into a single element configured entirely through attributes. "
            "Use it whenever you need a padded, optionally elevated region that "
            "is not semantically a card, dialog, or other named construct.</p>"
        ),
        how_to_use=(
            "<p>Wrap any content between the tags. Set <code>elevation</code> to "
            "<code>outlined</code>, <code>raised</code>, or <code>overlay</code>; "
            "use <code>padding</code> to pick a spacing step; and <code>radius</code> "
            "for corner rounding. Set <code>role-hint=\"section\"</code> to emit a "
            "<code>&lt;section&gt;</code> element instead of a <code>&lt;div&gt;</code>. "
            "Use <code>max-width</code> plus <code>full-bleed</code> to build "
            "content-width containers that bleed their background to the edges.</p>"
        ),
        example=(
            '<mj-surface elevation="outlined" padding="lg" radius="md">\n'
            "  <h3>Settings</h3>\n"
            "  <p>Configure your preferences here.</p>\n"
            "</mj-surface>"
        ),
        attributes=[
            ("elevation", "flat (default) | outlined | raised | overlay."),
            ("padding", "none | sm | md (default) | lg | xl spacing inside the surface."),
            ("radius", "none | sm | md (default) | lg | full corner rounding."),
            ("role-hint", "generic (default) | section; switches the root tag between div and section."),
            ("max-width", "CSS width value; constrains the surface and centres it."),
            ("full-bleed", "Boolean; removes padding and radius for edge-to-edge treatment."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-grid",
        title="Grid",
        group="layout",
        summary="A responsive CSS Grid primitive with auto-fill and fixed column modes.",
        description=(
            "<p><code>&lt;mj-grid&gt;</code> is a declarative CSS Grid wrapper. "
            "By default it uses <code>auto-fill</code> with a minimum column width "
            "so the grid reflows naturally as the container narrows. Set "
            "<code>columns</code> to a positive integer for an exact column count. "
            "A <code>mj-grid-layout</code> event fires on every resize so parent "
            "code can react to the current column count.</p>"
        ),
        how_to_use=(
            "<p>Place child elements directly inside <code>&lt;mj-grid&gt;</code>; "
            "each child fills one cell. Use <code>columns</code> for a fixed layout "
            "or <code>min-col-width</code> for a fluid one. Tune spacing with "
            "<code>gap</code>, or use <code>col-gap</code> and <code>row-gap</code> "
            "independently. Add <code>dense</code> to enable CSS grid auto-placement "
            "dense packing for irregular item sizes.</p>"
        ),
        example=(
            '<mj-grid columns="3" gap="md">\n'
            '  <mj-card heading="Item A" elevation="outlined"><p>First card</p></mj-card>\n'
            '  <mj-card heading="Item B" elevation="outlined"><p>Second card</p></mj-card>\n'
            '  <mj-card heading="Item C" elevation="outlined"><p>Third card</p></mj-card>\n'
            '  <mj-card heading="Item D" elevation="outlined"><p>Fourth card</p></mj-card>\n'
            '  <mj-card heading="Item E" elevation="outlined"><p>Fifth card</p></mj-card>\n'
            '  <mj-card heading="Item F" elevation="outlined"><p>Sixth card</p></mj-card>\n'
            "</mj-grid>"
        ),
        attributes=[
            ("columns", "Positive integer for a fixed column count; omit for auto-fill."),
            ("min-col-width", "Minimum column width used with auto-fill (default 16rem)."),
            ("gap", "none | xs | sm | md (default) | lg | xl uniform track gap."),
            ("col-gap", "Independent column gap token; overrides gap for columns only."),
            ("row-gap", "Independent row gap token; overrides gap for rows only."),
            ("dense", "Boolean; enables grid-auto-flow: dense packing."),
            ("align-items", "CSS align-items value for cell alignment (default stretch)."),
        ],
        events=[
            ("mj-grid-layout", "Fires on resize with {columns, masonry} describing the current layout."),
        ],
    ),
    ComponentDoc(
        tag="mj-stack",
        title="Stack",
        group="layout",
        summary="A one-dimensional flexbox primitive for vertical or horizontal stacks.",
        description=(
            "<p><code>&lt;mj-stack&gt;</code> is a thin flex-container wrapper "
            "that arranges its slotted children along a single axis with uniform "
            "gap spacing. It covers the most common layout need&mdash;stacking "
            "blocks vertically or lining them up horizontally&mdash;without "
            "requiring custom CSS. Use it inside cards, forms, toolbars, and "
            "any region that needs consistent spacing between children.</p>"
        ),
        how_to_use=(
            "<p>Set <code>direction</code> to <code>horizontal</code> or leave it "
            "as the default <code>vertical</code>. Pick a <code>gap</code> token. "
            "Use <code>align</code> and <code>justify</code> for cross-axis and "
            "main-axis alignment. Add <code>wrap</code> to let children reflow, "
            "and <code>reverse</code> to flip the order. Add the <code>inline</code> "
            "attribute when the stack must be inline-block rather than block.</p>"
        ),
        example=(
            '<mj-stack direction="horizontal" gap="sm" align="center">\n'
            '  <mj-button variant="primary">Save</mj-button>\n'
            '  <mj-button variant="secondary">Cancel</mj-button>\n'
            "  <mj-spacer></mj-spacer>\n"
            '  <mj-button variant="tertiary">Help</mj-button>\n'
            "</mj-stack>"
        ),
        attributes=[
            ("direction", "vertical (default) | horizontal main axis."),
            ("gap", "none | xs | sm | md (default) | lg | xl spacing between children."),
            ("align", "cross-axis alignment: stretch (default) | start | center | end | baseline."),
            ("justify", "main-axis distribution: start (default) | center | end | between | around | evenly."),
            ("wrap", "Boolean; allows children to wrap onto multiple lines."),
            ("reverse", "Boolean; reverses the child order on the main axis."),
            ("inline", "Boolean; makes the host inline-block instead of block."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-spacer",
        title="Spacer",
        group="layout",
        summary="A blank space that fills available flex/grid room or occupies a fixed size.",
        description=(
            "<p><code>&lt;mj-spacer&gt;</code> is a zero-content element used "
            "inside flex or grid containers to add breathing room between siblings. "
            "Without a <code>size</code> attribute it grows to fill all available "
            "space on the main axis, pushing siblings to opposite ends. With a "
            "<code>size</code> token it becomes a fixed-dimension inert block.</p>"
        ),
        how_to_use=(
            "<p>Drop <code>&lt;mj-spacer&gt;</code> between two siblings inside "
            "<code>&lt;mj-stack&gt;</code> or any flex container to push them "
            "apart. Set <code>size</code> to a token for a fixed gap instead of "
            "a flexible one. Use <code>axis</code> to constrain whether the size "
            "applies to the inline or block dimension.</p>"
        ),
        example=(
            '<mj-stack direction="horizontal" align="center" style="background:var(--mj-bg-muted);padding:0.5rem">\n'
            "  <span>Logo</span>\n"
            "  <mj-spacer></mj-spacer>\n"
            "  <span>Nav item</span>\n"
            "  <mj-spacer size=\"sm\"></mj-spacer>\n"
            "  <span>Nav item</span>\n"
            "  <mj-spacer size=\"sm\"></mj-spacer>\n"
            "  <span>Profile</span>\n"
            "</mj-stack>"
        ),
        attributes=[
            ("size", "xs | sm | md | lg | xl | 2xl or any CSS length for a fixed size; omit to flex-grow."),
            ("axis", "both (default) | horizontal | vertical; which dimension the fixed size applies to."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-aspect-ratio",
        title="Aspect Ratio Box",
        group="layout",
        summary="Constrains slotted content to a fixed aspect ratio to prevent layout shift.",
        description=(
            "<p><code>&lt;mj-aspect-ratio&gt;</code> wraps an image, video, "
            "iframe, or any other media element and enforces a fixed width-to-height "
            "ratio using the CSS <code>aspect-ratio</code> property. It eliminates "
            "cumulative layout shift (CLS) for media whose intrinsic dimensions "
            "are not yet known. Built-in keyword aliases cover the most common "
            "ratios; arbitrary fractions and decimal values are also accepted.</p>"
        ),
        how_to_use=(
            "<p>Place an <code>&lt;img&gt;</code>, <code>&lt;video&gt;</code>, "
            "or <code>&lt;iframe&gt;</code> between the tags. Set <code>ratio</code> "
            "to a keyword alias (<code>16x9</code>, <code>4x3</code>, "
            "<code>1x1</code>, <code>3x2</code>, <code>9x16</code>), a CSS "
            "<code>width/height</code> fraction, or a single decimal. Control "
            "how the media fills the box with <code>fit</code> and centre the "
            "focal point with <code>position</code>.</p>"
        ),
        example=(
            '<mj-aspect-ratio ratio="16x9" fit="cover" style="max-width:32rem">\n'
            '  <img src="https://picsum.photos/seed/landscape/800/450" alt="Landscape" />\n'
            "</mj-aspect-ratio>"
        ),
        attributes=[
            ("ratio", "16x9 (default) | 4x3 | 1x1 | 3x2 | 9x16 | W/H fraction | decimal number."),
            ("fit", "CSS object-fit value applied to slotted img/video (default cover)."),
            ("position", "CSS object-position value for focal point (default center)."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-accordion",
        title="Accordion",
        group="layout",
        summary="Groups multiple disclosure panels and coordinates their open/closed state.",
        description=(
            "<p><code>&lt;mj-accordion&gt;</code> wraps two or more "
            "<code>&lt;mj-disclosure&gt;</code> elements and manages which ones "
            "are open. In the default mode only one panel may be open at a time; "
            "set <code>allow-multiple</code> to let any number be open "
            "simultaneously. Full WAI-ARIA Accordion keyboard navigation "
            "(Arrow keys, Home, End) is built in.</p>"
        ),
        how_to_use=(
            "<p>Nest <code>&lt;mj-disclosure&gt;</code> children directly inside "
            "<code>&lt;mj-accordion&gt;</code>. Add <code>bordered</code> for a "
            "unified card-style border around all panels. Use <code>allow-multiple</code> "
            "when independent section visibility is preferred. The "
            "<code>disabled</code> attribute disables every panel at once. "
            "Listen for <code>mj-accordion-close</code> to react when a panel "
            "is automatically closed by the single-open rule.</p>"
        ),
        example=(
            "<mj-accordion bordered>\n"
            '  <mj-disclosure heading="What is CodeCraftAI WebWorks?">\n'
            "    <p>A library of accessible, themeable web components built on native "
            "custom elements.</p>\n"
            "  </mj-disclosure>\n"
            '  <mj-disclosure heading="How do I install it?">\n'
            "    <p>Run <code>npm install codecraftai-webworks</code> and import the "
            "components you need.</p>\n"
            "  </mj-disclosure>\n"
            '  <mj-disclosure heading="Is it accessible?" open>\n'
            "    <p>Yes. Every component is built to WCAG 2.2 AA and the WAI-ARIA "
            "authoring practices guide.</p>\n"
            "  </mj-disclosure>\n"
            "</mj-accordion>"
        ),
        attributes=[
            ("allow-multiple", "Boolean; permits more than one panel to be open simultaneously."),
            ("bordered", "Boolean; draws a shared border and overflow:hidden around all panels."),
            ("flush", "Boolean; removes gaps between panels."),
            ("disabled", "Boolean; propagates disabled to every child mj-disclosure."),
        ],
        events=[
            ("mj-accordion-close", "Fires when a panel is closed by the single-open rule; detail includes {panel, index}."),
        ],
    ),
    ComponentDoc(
        tag="mj-disclosure",
        title="Disclosure",
        group="layout",
        summary="A single show/hide region with a trigger button and animated panel.",
        description=(
            "<p><code>&lt;mj-disclosure&gt;</code> implements the ARIA button + "
            "region disclosure pattern. A trigger button controls a collapsible "
            "content panel with an animated height transition. The "
            "<code>summary</code> slot fills the button label; a plain "
            "<code>heading</code> attribute can be used instead. The component "
            "manages <code>aria-expanded</code> and <code>aria-controls</code> "
            "automatically.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>heading</code> attribute for the button text, or "
            "slot content into <code>slot=\"summary\"</code> for rich labels. "
            "Place the body content in the default slot. Add <code>open</code> "
            "for an initially expanded state. Set <code>disabled</code> to "
            "prevent toggling. The <code>mj-disclosure-toggle</code> event is "
            "cancelable&mdash;returning <code>false</code> from a handler vetoes "
            "the state change. Use <code>indicator-position=\"start\"</code> to "
            "move the chevron before the label.</p>"
        ),
        example=(
            '<mj-disclosure heading="What is included?" open>\n'
            "  <p>Access to all components, themes, and documentation for one "
            "year from the purchase date.</p>\n"
            "</mj-disclosure>\n"
            '<mj-disclosure heading="Can I use it commercially?">\n'
            "  <p>Yes. The license covers unlimited commercial projects.</p>\n"
            "</mj-disclosure>"
        ),
        attributes=[
            ("heading", "Trigger button text when no summary slot is provided."),
            ("open", "Boolean; the expanded/collapsed state."),
            ("disabled", "Boolean; blocks toggling and dimms the trigger."),
            ("animated", "Set to false to disable the height transition."),
            ("indicator-position", "end (default) | start position of the chevron icon."),
            ("heading-level", "Heading level hint (not rendered; reserved for future use)."),
        ],
        events=[
            ("mj-disclosure-toggle", "Cancelable; fires before the state changes; detail includes {open}."),
            ("mj-disclosure-open", "Fires after the panel finishes opening."),
            ("mj-disclosure-close", "Fires after the panel finishes closing."),
        ],
    ),
    ComponentDoc(
        tag="mj-split-pane",
        title="Split Pane",
        group="layout",
        summary="Divides a container into two resizable regions separated by a draggable handle.",
        description=(
            "<p><code>&lt;mj-split-pane&gt;</code> renders a start pane and an "
            "end pane separated by a keyboard-operable drag handle. Either "
            "horizontal (side-by-side) or vertical (top/bottom) orientations are "
            "supported. The separator is a proper ARIA separator with live "
            "aria-valuenow feedback. Size boundaries are enforced by "
            "<code>min</code> and <code>max</code> attributes, and the settled "
            "size can be persisted to <code>localStorage</code> via "
            "<code>persist-key</code>.</p>"
        ),
        how_to_use=(
            "<p>Put the primary region in <code>slot=\"start\"</code> and the "
            "secondary region in <code>slot=\"end\"</code>. Set "
            "<code>initial-size</code> to any CSS length or percentage for the "
            "start pane. Set <code>orientation=\"vertical\"</code> for a "
            "top/bottom split. Drag or use Arrow keys on the separator to resize; "
            "double-click to collapse/restore when <code>collapsible</code> is "
            "set. Listen for <code>mj-split-resize-end</code> for settled sizes.</p>"
        ),
        example=(
            '<mj-split-pane initial-size="40%" style="height:14rem;border:1px solid var(--mj-border)">\n'
            '  <div slot="start" style="padding:1rem;background:var(--mj-bg-muted)">\n'
            "    <strong>File tree</strong>\n"
            "    <p>src/</p><p>tests/</p>\n"
            "  </div>\n"
            '  <div slot="end" style="padding:1rem">\n'
            "    <strong>Editor</strong>\n"
            "    <p>Select a file to edit.</p>\n"
            "  </div>\n"
            "</mj-split-pane>"
        ),
        attributes=[
            ("orientation", "horizontal (default) | vertical axis of the split."),
            ("initial-size", "CSS length or % for the start pane initial size (default 50%)."),
            ("min", "Minimum pixel size of the start pane (default 80px)."),
            ("max", "Maximum pixel size of the start pane; defaults to total minus min."),
            ("disabled", "Boolean; locks the separator so it cannot be dragged."),
            ("collapsible", "none (default) | start | end; enables double-click collapse."),
            ("persist-key", "localStorage key under which the settled size is saved."),
            ("separator-label", "Accessible label for the separator (default Resize)."),
        ],
        events=[
            ("mj-split-resize", "Fires continuously while dragging; detail includes {size, ratio}."),
            ("mj-split-resize-end", "Fires when a drag or keyboard resize settles; detail includes {size, ratio}."),
            ("mj-split-collapse", "Fires when a pane is collapsed by double-click; detail includes {pane}."),
            ("mj-split-expand", "Fires when a collapsed pane is restored by double-click; detail includes {pane}."),
        ],
    ),
    ComponentDoc(
        tag="mj-scroll-area",
        title="Scroll Area",
        group="layout",
        summary="A scrollable region with consistent, theme-aware scrollbars.",
        description=(
            "<p><code>&lt;mj-scroll-area&gt;</code> wraps any overflowing content "
            "in a viewport whose scrollbars match the design token palette using "
            "the CSS <code>scrollbar-color</code> and <code>scrollbar-width</code> "
            "properties. Native scroll behavior and keyboard scrollability are "
            "fully preserved. Throttled <code>mj-scroll</code> events (one per "
            "animation frame) and a debounced <code>mj-scroll-end</code> event "
            "are emitted for consumer code.</p>"
        ),
        how_to_use=(
            "<p>Wrap long content between the tags. Give the host a fixed block "
            "size (height) so overflow can occur. Set <code>overflow-x</code> and "
            "<code>overflow-y</code> independently; the defaults are "
            "<code>hidden</code> / <code>auto</code>. Set "
            "<code>aria-label</code> to name the region for screen readers. "
            "Use <code>scroll-padding</code> to add padding around scroll-snap "
            "targets.</p>"
        ),
        example=(
            '<mj-scroll-area style="height:10rem;border:1px solid var(--mj-border)" '
            'aria-label="Recent activity">\n'
            "  <ul style=\"list-style:none;margin:0;padding:0.5rem\">\n"
            "    <li>Commit: fix layout bug</li>\n"
            "    <li>Commit: add skeleton component</li>\n"
            "    <li>Commit: update theme tokens</li>\n"
            "    <li>Commit: carousel keyboard nav</li>\n"
            "    <li>Commit: scroll area events</li>\n"
            "    <li>Commit: split pane persist</li>\n"
            "    <li>Commit: dock layout anchoring</li>\n"
            "    <li>Commit: hero bg video support</li>\n"
            "  </ul>\n"
            "</mj-scroll-area>"
        ),
        attributes=[
            ("overflow-x", "CSS overflow value for the horizontal axis (default hidden)."),
            ("overflow-y", "CSS overflow value for the vertical axis (default auto)."),
            ("scroll-padding", "CSS scroll-padding applied to the viewport."),
            ("tabindex", "Tabindex on the viewport element (default 0)."),
            ("aria-label", "Accessible name for the scroll region."),
        ],
        events=[
            ("mj-scroll", "Throttled (rAF); fires while scrolling with {scrollTop, scrollLeft, scrollHeight, scrollWidth}."),
            ("mj-scroll-end", "Debounced; fires when scrolling stops with {scrollTop, scrollLeft}."),
        ],
    ),
    ComponentDoc(
        tag="mj-carousel",
        title="Carousel",
        group="layout",
        summary="A slide sequence with prev/next controls, picker dots, and optional autoplay.",
        description=(
            "<p><code>&lt;mj-carousel&gt;</code> presents a set of "
            "<code>&lt;mj-carousel-slide&gt;</code> children one at a time with "
            "previous/next buttons and picker dots for direct slide access. It "
            "follows the WAI-ARIA APG carousel pattern with an "
            "<code>aria-roledescription=\"carousel\"</code> region, live region "
            "announcements on user interaction, and full keyboard navigation "
            "(Arrow keys, Home, End). Autoplay pauses on hover and focus.</p>"
        ),
        how_to_use=(
            "<p>Wrap each slide in an <code>&lt;mj-carousel-slide&gt;</code> and "
            "nest those inside <code>&lt;mj-carousel&gt;</code>. Set "
            "<code>label</code> for the accessible region name. Enable "
            "<code>loop</code> to wrap around at the ends. Add "
            "<code>autoplay</code> for timer-driven rotation and "
            "<code>autoplay-interval</code> to set the delay in milliseconds. "
            "Set <code>show-controls=\"false\"</code> or "
            "<code>show-picker=\"false\"</code> to hide navigation UI.</p>"
        ),
        example=(
            '<mj-carousel label="Feature highlights" loop style="max-width:32rem">\n'
            "  <mj-carousel-slide>\n"
            '    <mj-surface elevation="outlined" padding="lg">\n'
            "      <h3>Fast</h3><p>Built on native custom elements with no framework dependency.</p>\n"
            "    </mj-surface>\n"
            "  </mj-carousel-slide>\n"
            "  <mj-carousel-slide>\n"
            '    <mj-surface elevation="outlined" padding="lg">\n'
            "      <h3>Accessible</h3><p>Every component meets WCAG 2.2 AA out of the box.</p>\n"
            "    </mj-surface>\n"
            "  </mj-carousel-slide>\n"
            "  <mj-carousel-slide>\n"
            '    <mj-surface elevation="outlined" padding="lg">\n'
            "      <h3>Themeable</h3><p>Design tokens control every visual property.</p>\n"
            "    </mj-surface>\n"
            "  </mj-carousel-slide>\n"
            "</mj-carousel>"
        ),
        attributes=[
            ("current-index", "Zero-based index of the active slide (default 0)."),
            ("loop", "Boolean; wraps navigation past the first and last slides."),
            ("autoplay", "Boolean; enables timer-driven slide rotation."),
            ("autoplay-interval", "Milliseconds between automatic advances (default 5000, min 1000)."),
            ("show-controls", "Set to false to hide the prev/next buttons."),
            ("show-picker", "Set to false to hide the picker dots."),
            ("label", "Accessible label for the carousel region (default Carousel)."),
            ("transition", "slide (default) | fade | none visual transition style."),
        ],
        events=[
            ("mj-carousel-change", "Cancelable; fires before a slide change; detail includes {index, previousIndex, trigger}."),
            ("mj-carousel-changed", "Fires after the active slide updates; detail includes {index, previousIndex}."),
            ("mj-carousel-play", "Fires when autoplay starts."),
            ("mj-carousel-pause", "Fires when autoplay stops."),
        ],
    ),
    ComponentDoc(
        tag="mj-feed",
        title="Feed",
        group="layout",
        summary="An ARIA feed region with infinite scroll and button-triggered loading.",
        description=(
            "<p><code>&lt;mj-feed&gt;</code> implements the WAI-ARIA feed role "
            "for a dynamically updated list of articles. It manages "
            "<code>aria-posinset</code> and <code>aria-setsize</code> on each "
            "<code>&lt;mj-feed-item&gt;</code> child, announces new items via a "
            "live region, and triggers load requests either by scroll-intersection "
            "(infinite scroll) or a visible Load More button. Page Up/Down "
            "keyboard navigation moves focus between feed items per the APG "
            "feed pattern.</p>"
        ),
        how_to_use=(
            "<p>Wrap <code>&lt;mj-feed-item&gt;</code> children inside "
            "<code>&lt;mj-feed&gt;</code>. Set <code>load-mode=\"button\"</code> "
            "to show a Load More button instead of auto-triggering on scroll. "
            "Set <code>loading</code> while fetching to block double requests. "
            "Set <code>has-more=\"false\"</code> when all data is loaded to hide "
            "the trigger. Supply a <code>slot=\"empty\"</code> element for the "
            "no-content state. Listen for <code>mj-feed-load-more</code> and "
            "append new <code>&lt;mj-feed-item&gt;</code> elements.</p>"
        ),
        example=(
            '<mj-feed has-more="false">\n'
            "  <mj-feed-item>\n"
            '    <mj-media-object gap="md">\n'
            '      <img slot="media" src="https://i.pravatar.cc/48?img=1" alt="Alice" '
            'style="border-radius:50%;width:48px;height:48px" />\n'
            "      <div><strong>Alice</strong><p>Just shipped the new carousel component!</p></div>\n"
            "    </mj-media-object>\n"
            "  </mj-feed-item>\n"
            "  <mj-feed-item>\n"
            '    <mj-media-object gap="md">\n'
            '      <img slot="media" src="https://i.pravatar.cc/48?img=2" alt="Bob" '
            'style="border-radius:50%;width:48px;height:48px" />\n'
            "      <div><strong>Bob</strong><p>Reviewed the accessibility audit.</p></div>\n"
            "    </mj-media-object>\n"
            "  </mj-feed-item>\n"
            '  <div slot="empty"><mj-empty-state heading="Nothing yet" '
            'show-illustration="false"></mj-empty-state></div>\n'
            "</mj-feed>"
        ),
        attributes=[
            ("load-mode", "scroll (default) | button controls how more items are requested."),
            ("loading", "Boolean; marks aria-busy and disables the Load More button."),
            ("has-more", "true (default) | false; set to false when all items are loaded."),
            ("reversed", "Boolean; stacks items bottom-up using column-reverse."),
            ("load-more-label", "Text for the Load More button (default Load more)."),
            ("loading-label", "Text shown in the loading indicator (default Loading)."),
        ],
        events=[
            ("mj-feed-load-more", "Fires when the sentinel enters the viewport or the button is clicked; detail includes {itemCount}."),
            ("mj-feed-item-focus", "Fires on keyboard Page Up/Down navigation; detail includes {item, index}."),
        ],
    ),
    ComponentDoc(
        tag="mj-media-object",
        title="Media Object",
        group="layout",
        summary="Places a fixed-size media element beside a variable-width text block.",
        description=(
            "<p><code>&lt;mj-media-object&gt;</code> is the foundational pattern "
            "for rows that pair a thumbnail or avatar with a text body: comment "
            "rows, notification items, list rows with icons, and settings rows. "
            "The media element is shrink-proof and sized by <code>media-size</code>; "
            "the content area grows to fill the remainder.</p>"
        ),
        how_to_use=(
            "<p>Place the thumbnail, avatar, or icon in <code>slot=\"media\"</code> "
            "and text content in the default slot. Set <code>media-size</code> to "
            "a CSS length to override the 3 rem default. Use <code>align</code> "
            "to align the media vertically within the row. Set "
            "<code>media-position=\"end\"</code> to move the media to the "
            "trailing side.</p>"
        ),
        example=(
            '<mj-media-object gap="md" align="start">\n'
            '  <img slot="media" src="https://i.pravatar.cc/48?img=5" alt="Carol" '
            'style="border-radius:50%;width:48px;height:48px" />\n'
            "  <div>\n"
            "    <strong>Carol</strong>\n"
            "    <p style=\"margin:0.25rem 0 0\">Left a comment on your pull request.</p>\n"
            "    <small style=\"color:var(--mj-text-muted)\">2 minutes ago</small>\n"
            "  </div>\n"
            "</mj-media-object>"
        ),
        attributes=[
            ("media-position", "start (default) | end side for the media element."),
            ("gap", "none | xs | sm | md (default) | lg | xl spacing between media and content."),
            ("align", "start (default) | center | end | stretch vertical alignment."),
            ("media-size", "CSS inline-size of the media element (default 3rem)."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-hero",
        title="Hero Section",
        group="layout",
        summary="A full-width introductory banner with background, heading, body, and actions.",
        description=(
            "<p><code>&lt;mj-hero&gt;</code> is a large, visually prominent "
            "introductory section for landing pages and feature announcements. "
            "It supports a CSS background color, a background image "
            "(<code>bg-src</code>), or a background video (<code>bg-video</code>) "
            "with a semi-transparent overlay. The content area is centered and "
            "max-width constrained, and four named slots&mdash;heading, body, "
            "actions, and media&mdash;give full control over the content "
            "hierarchy.</p>"
        ),
        how_to_use=(
            "<p>Set <code>heading</code> for the main text or supply "
            "<code>slot=\"heading\"</code>. Use <code>slot=\"body\"</code> for "
            "supporting copy, <code>slot=\"actions\"</code> for CTA buttons, and "
            "<code>slot=\"media\"</code> for an illustration or screenshot below "
            "the copy. Control alignment with <code>align</code> "
            "(<code>start</code> | <code>center</code> | <code>end</code>). "
            "Set <code>overlay-opacity</code> (0&ndash;1) to tune the background "
            "overlay. Add <code>full-height</code> to make the section fill the "
            "full viewport.</p>"
        ),
        example=(
            '<mj-hero heading="Build faster with WebWorks" bg-color="#1a1a2e" align="center">\n'
            '  <p slot="body" style="max-width:40ch;margin-inline:auto">\n'
            "    Accessible, themeable web components built on native custom elements.\n"
            "  </p>\n"
            '  <div slot="actions">\n'
            '    <mj-button variant="primary">Get started</mj-button>\n'
            '    <mj-button variant="secondary">View docs</mj-button>\n'
            "  </div>\n"
            "</mj-hero>"
        ),
        attributes=[
            ("heading", "Heading text; also available via slot=\"heading\" for rich content."),
            ("heading-level", "HTML heading level for the generated heading element (default 1)."),
            ("bg-src", "URL of a background image."),
            ("bg-video", "URL of a background video (muted, looped, autoplayed)."),
            ("bg-color", "CSS color for the background when no image or video is set."),
            ("overlay-opacity", "Opacity of the dark overlay over the background (default 0.4)."),
            ("align", "center (default) | start | end content alignment."),
            ("min-height", "CSS value for the minimum section height (default 40vh)."),
            ("full-height", "Boolean; sets minimum height to 100dvh."),
        ],
        events=[
            ("mj-hero-bg-error", "Fires when the background image or video fails to load; detail includes {src}."),
        ],
    ),
    ComponentDoc(
        tag="mj-empty-state",
        title="Empty State",
        group="layout",
        summary="A meaningful no-content message with illustration, heading, and actions.",
        description=(
            "<p><code>&lt;mj-empty-state&gt;</code> gives zero-result views a "
            "consistent, helpful structure: an optional illustration slot, a "
            "heading, a description paragraph, and action buttons. It is typically "
            "rendered inside a feed, table, or search results area to guide users "
            "when there is nothing to show yet. A <code>compact</code> mode "
            "reduces padding and icon size for use in smaller containers.</p>"
        ),
        how_to_use=(
            "<p>Set <code>heading</code> for the main message, or use "
            "<code>slot=\"heading\"</code> for rich content. Put supporting text "
            "in <code>slot=\"description\"</code> and recovery actions in "
            "<code>slot=\"actions\"</code>. Place an SVG or image in "
            "<code>slot=\"illustration\"</code>. Set "
            "<code>show-illustration=\"false\"</code> to hide the illustration "
            "area when no art is available. Add <code>compact</code> to reduce "
            "the layout density.</p>"
        ),
        example=(
            '<mj-empty-state heading="No results found">\n'
            '  <svg slot="illustration" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
            'fill="none" stroke="currentColor" stroke-width="2" '
            'style="width:5rem;height:5rem;opacity:0.4">\n'
            '    <circle cx="32" cy="32" r="28"/>\n'
            '    <line x1="20" y1="20" x2="44" y2="44"/>\n'
            "  </svg>\n"
            '  <p slot="description">Try adjusting your search terms or clearing the filters.</p>\n'
            '  <div slot="actions">\n'
            '    <mj-button variant="secondary">Clear filters</mj-button>\n'
            "  </div>\n"
            "</mj-empty-state>"
        ),
        attributes=[
            ("heading", "Primary message text; also settable via slot=\"heading\"."),
            ("heading-level", "Heading element level (default 3)."),
            ("compact", "Boolean; reduces padding and illustration size."),
            ("show-illustration", "Set to false to hide the illustration area entirely."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-skeleton",
        title="Skeleton Loader",
        group="layout",
        summary="A shimmering loading placeholder shaped like the content it will replace.",
        description=(
            "<p><code>&lt;mj-skeleton&gt;</code> renders a shimmer animation in "
            "the shape of content that has not yet loaded. Three variants are "
            "available: <code>rectangle</code> (the default, useful for images "
            "and blocks), <code>circle</code> (for avatars), and <code>text</code> "
            "(multi-line text rows where the last line is narrower). The host is "
            "<code>aria-hidden</code>; a visually-hidden live region announces "
            "the loading state to screen readers.</p>"
        ),
        how_to_use=(
            "<p>Drop an <code>&lt;mj-skeleton&gt;</code> wherever content is "
            "loading. Use <code>width</code> and <code>height</code> to match "
            "the expected content dimensions. For avatar placeholders set "
            "<code>variant=\"circle\"</code> and a square <code>width</code>. "
            "For text blocks set <code>variant=\"text\"</code> and "
            "<code>lines</code> to the expected line count. Set "
            "<code>animated=\"false\"</code> to disable the shimmer when the "
            "platform already conveys loading state another way.</p>"
        ),
        example=(
            '<mj-stack gap="md" style="max-width:24rem">\n'
            '  <mj-stack direction="horizontal" gap="sm" align="center">\n'
            '    <mj-skeleton variant="circle" width="3rem"></mj-skeleton>\n'
            '    <mj-stack gap="xs" style="flex:1">\n'
            '      <mj-skeleton variant="text" width="60%" height="1rem"></mj-skeleton>\n'
            '      <mj-skeleton variant="text" width="40%" height="0.75rem"></mj-skeleton>\n'
            "    </mj-stack>\n"
            "  </mj-stack>\n"
            '  <mj-skeleton variant="rectangle" width="100%" height="8rem"></mj-skeleton>\n'
            '  <mj-skeleton variant="text" lines="3"></mj-skeleton>\n'
            "</mj-stack>"
        ),
        attributes=[
            ("variant", "rectangle (default) | circle | text shape of the placeholder."),
            ("width", "CSS inline-size of the skeleton (default 100%)."),
            ("height", "CSS block-size of the skeleton (default 1rem; ignored for text variant)."),
            ("lines", "Number of text lines when variant is text (default 1)."),
            ("animated", "Set to false to disable the shimmer animation."),
            ("radius", "CSS border-radius override for the rectangle variant."),
            ("loading-label", "Text announced by the live region to screen readers (default Loading)."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-divider",
        title="Divider",
        group="layout",
        summary="A visual or semantic separator between adjacent content regions.",
        description=(
            "<p><code>&lt;mj-divider&gt;</code> renders a horizontal or vertical "
            "line between sibling elements. By default it is a semantic "
            "<code>&lt;hr&gt;</code> (role separator); set <code>decorative</code> "
            "to render it as a purely visual element. An optional "
            "<code>label</code> attribute (or <code>slot=\"label\"</code>) wraps "
            "a short text label in the center of the line, useful for "
            "&ldquo;or&rdquo; dividers in forms.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;mj-divider&gt;</code> between sibling elements. "
            "For a vertical divider inside a flex row set "
            "<code>orientation=\"vertical\"</code>. Add <code>decorative</code> "
            "when the line is purely aesthetic and should not be announced by "
            "screen readers. Use <code>variant</code> to switch between solid, "
            "dashed, and dotted lines. Adjust the surrounding whitespace with "
            "<code>spacing</code> and the line weight with <code>thickness</code>.</p>"
        ),
        example=(
            "<p>Section A</p>\n"
            '<mj-divider spacing="md"></mj-divider>\n'
            "<p>Section B</p>\n"
            '<mj-divider label="or" spacing="md"></mj-divider>\n'
            "<p>Section C</p>\n"
            '<mj-divider variant="dashed" thickness="thin" decorative></mj-divider>\n'
            "<p>Section D</p>"
        ),
        attributes=[
            ("orientation", "horizontal (default) | vertical."),
            ("decorative", "Boolean; renders the divider as role=\"none\" aria-hidden=\"true\"."),
            ("label", "Short text centered on the line; also accepts slot=\"label\"."),
            ("variant", "solid (default) | dashed | dotted line style."),
            ("thickness", "thin (default, 1px) | medium (2px) | thick (4px)."),
            ("spacing", "none | xs | sm | md (default) | lg block margin around the divider."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-dock-layout",
        title="Dock Layout",
        group="layout",
        summary="An app-shell container that positions children by dock edge (top/bottom/start/end/fill).",
        description=(
            "<p><code>&lt;mj-dock-layout&gt;</code> is a positioning host that "
            "arranges its direct children according to their <code>dock</code> "
            "attribute. Each child with <code>dock=\"top\"</code>, "
            "<code>dock=\"bottom\"</code>, <code>dock=\"start\"</code>, or "
            "<code>dock=\"end\"</code> consumes a band of the container's "
            "remaining space in DOM order&mdash;similar to WPF DockPanel. "
            "Children with <code>dock=\"fill\"</code> share the leftover "
            "rectangle and are typically the main content area. Children "
            "without a <code>dock</code> attribute are left in normal flow, "
            "so anchored pop-up elements (which position relative to this "
            "container as the established positioning context) work naturally "
            "alongside docked children.</p>"
            "<p>The layout re-runs on every resize (ResizeObserver) and on "
            "any child mutation that changes a <code>dock</code> attribute, "
            "emitting a non-bubbling <code>mj-layout</code> event after each "
            "pass.</p>"
        ),
        how_to_use=(
            "<p>Give <code>&lt;mj-dock-layout&gt;</code> a fixed or percentage "
            "height so the fill area has space to occupy. Add children with "
            "appropriate <code>dock</code> attributes in the desired consumption "
            "order&mdash;typically top toolbar first, then bottom status bar, "
            "then start sidebar, then end sidebar, then the fill content pane. "
            "DOM order determines which edge is consumed first when multiple "
            "children share the same axis. Children that need to float above "
            "the layout (dropdowns, tooltips) should have no <code>dock</code> "
            "attribute and use absolute positioning against this container.</p>"
        ),
        example=(
            '<mj-dock-layout style="height:18rem;border:1px solid var(--mj-border)">\n'
            '  <header dock="top" style="background:var(--mj-accent);color:var(--mj-text-on-accent);'
            'padding:0.5rem 1rem;display:flex;align-items:center;gap:0.5rem">\n'
            "    <strong>My App</strong>\n"
            "    <mj-spacer></mj-spacer>\n"
            "    <span>User menu</span>\n"
            "  </header>\n"
            '  <nav dock="start" style="background:var(--mj-bg-muted);padding:0.75rem;'
            'min-width:10rem">\n'
            "    <p>Dashboard</p><p>Reports</p><p>Settings</p>\n"
            "  </nav>\n"
            '  <footer dock="bottom" style="background:var(--mj-bg-muted);padding:0.25rem 1rem;'
            'font-size:0.75rem;color:var(--mj-text-muted)">\n'
            "    Status: Ready\n"
            "  </footer>\n"
            '  <main dock="fill" style="padding:1rem;overflow:auto">\n'
            "    <h2>Welcome</h2>\n"
            "    <p>Main content fills the remaining space.</p>\n"
            "  </main>\n"
            "</mj-dock-layout>"
        ),
        attributes=[
            ("dock", "(on children) top | bottom | start | end | fill &mdash; edge or fill region the child occupies."),
        ],
        events=[
            ("mj-layout", "Non-bubbling; fires after each layout pass; detail includes {container}."),
        ],
    ),
]
