"""
    media.py

    Catalog entries for the 'Media & Visualization' component group.

    Every component in this group handles rich media display or data
    visualization: images, avatars, audio/video playback, charts, maps,
    gauges, sparklines, and node/edge diagrams.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-image",
        title="Image",
        group="media",
        summary="Lazy-loaded, responsive image with aspect-ratio reservation and optional caption.",
        description=(
            "<p><code>&lt;mj-image&gt;</code> wraps a native <code>&lt;img&gt;</code> "
            "with IntersectionObserver-driven lazy loading, <code>srcset</code>/<code>sizes</code> "
            "support, a placeholder shown while the image loads, and an optional "
            "<code>figcaption</code>. Use the <code>thumbnail</code> variant for small "
            "fixed-size previews, or the default block variant for hero and inline figures. "
            "An <code>overlay</code> slot lets you add badges or play buttons over the image.</p>"
        ),
        how_to_use=(
            "<p>Set <code>src</code> and always provide an <code>alt</code> description "
            "(use <code>alt=\"\"</code> for purely decorative images). Supply "
            "<code>width</code> and <code>height</code> or <code>aspect-ratio</code> to "
            "reserve space before the image loads and eliminate layout shift. Use "
            "<code>loading=\"eager\"</code> for above-the-fold images; the default "
            "<code>lazy</code> defers loading until the image nears the viewport. "
            "Set <code>fit</code> to control <code>object-fit</code> behaviour. "
            "Add a <code>caption</code> attribute for a visible figure caption. "
            "Listen for <code>mj-image-load</code> or <code>mj-image-error</code> "
            "to react to load outcomes.</p>"
        ),
        example=(
            '<mj-image\n'
            '  src="https://picsum.photos/seed/webworks/800/450"\n'
            '  alt="A sample landscape photograph"\n'
            '  aspect-ratio="16/9"\n'
            '  caption="Sample image loaded lazily"\n'
            '  style="max-width:480px">\n'
            '</mj-image>'
        ),
        attributes=[
            ("src", "URL of the image to load."),
            ("srcset", "Responsive image candidate list passed to the native img srcset."),
            ("sizes", "Media-condition/width descriptor pairs for srcset selection."),
            ("alt", "Accessible alternative text. Required; use empty string for decorative images."),
            ("width", "Intrinsic pixel width; used for aspect-ratio reservation."),
            ("height", "Intrinsic pixel height; used for aspect-ratio reservation."),
            ("aspect-ratio", "CSS aspect-ratio value (e.g. 16/9) for the container."),
            ("loading", "eager | lazy (default). Controls when the image is fetched."),
            ("fit", "CSS object-fit value applied to the image (default: cover)."),
            ("variant", "thumbnail — fixed square thumbnail mode."),
            ("caption", "Text rendered in a figcaption below the image."),
            ("placeholder-color", "Background color of the placeholder shown before load."),
            ("crossorigin", "CORS setting forwarded to the native img element."),
            ("decoding", "Image decoding hint forwarded to the native img (default: async)."),
        ],
        events=[
            ("mj-image-visible", "Fired when the image enters the viewport and loading begins."),
            ("mj-image-load", "Fired after the image loads successfully; includes src, naturalWidth, naturalHeight."),
            ("mj-image-error", "Fired when the image fails to load; includes src."),
        ],
    ),
    ComponentDoc(
        tag="mj-avatar",
        title="Avatar",
        group="media",
        summary="User or entity avatar with photo, initials, and icon fallback chain.",
        description=(
            "<p><code>&lt;mj-avatar&gt;</code> displays a user or entity identity "
            "image with a graceful three-level fallback: photo &rarr; derived initials "
            "&rarr; generic person icon. Background color is deterministically derived "
            "from the <code>name</code> so the same person always gets the same hue "
            "across sessions. An optional presence dot (online / away / busy / offline) "
            "can be overlaid on the avatar. Use <code>shape=\"square\"</code> for "
            "entity or brand avatars.</p>"
        ),
        how_to_use=(
            "<p>Provide <code>src</code> for a photo. If the image fails to load "
            "or is omitted, the component falls back to <code>initials</code> (explicit) "
            "or initials derived from <code>name</code>, then to a silhouette icon. "
            "Set <code>size</code> to xs / sm / md / lg / xl. Add "
            "<code>presence</code> to show an availability indicator. "
            "Use <code>color</code> to override the auto-generated background.</p>"
        ),
        example=(
            '<mj-avatar name="Alice Martin" size="lg" presence="online"></mj-avatar>\n'
            '<mj-avatar\n'
            '  src="https://i.pravatar.cc/80?img=3"\n'
            '  name="Bob Chen"\n'
            '  size="lg"\n'
            '  presence="away">\n'
            '</mj-avatar>\n'
            '<mj-avatar initials="XY" size="lg" shape="square"></mj-avatar>'
        ),
        attributes=[
            ("src", "URL of the avatar photo."),
            ("name", "Full name used to derive initials and background color."),
            ("initials", "Explicit initials (up to 2 characters) overriding name-derived initials."),
            ("size", "xs | sm | md (default) | lg | xl."),
            ("shape", "circle (default) | square."),
            ("presence", "online | away | busy | offline — shows a colored presence dot."),
            ("color", "Explicit background color overriding the auto-derived color."),
            ("crossorigin", "CORS setting forwarded to the native img element."),
        ],
        events=[
            ("mj-avatar-image-load", "Fired when the avatar photo loads successfully; includes src."),
            ("mj-avatar-image-error", "Fired when the avatar photo fails to load; falls back to initials/icon."),
        ],
    ),
    ComponentDoc(
        tag="mj-media-player",
        title="Media Player",
        group="media",
        summary="Accessible video and audio player with full keyboard control and transcript support.",
        description=(
            "<p><code>&lt;mj-media-player&gt;</code> is a fully accessible "
            "video or audio player built on the native media element. It provides "
            "play/pause, seek, volume, mute, playback-speed selection, captions "
            "toggle, and fullscreen (video). All controls are keyboard-operable "
            "with standard shortcuts (Space/K to play, arrow keys to seek/volume, "
            "M to mute, F for fullscreen, C for captions, 0&ndash;9 for percentage "
            "jumps). A buffering spinner and error banner are shown automatically. "
            "An optional transcript panel can be shown below the player.</p>"
        ),
        how_to_use=(
            "<p>Set <code>type</code> to <code>video</code> (default) or "
            "<code>audio</code>. Provide <code>src</code> for the media file. "
            "Add <code>poster</code> for a video thumbnail. Use "
            "<code>aspect-ratio</code> to control the video frame ratio. "
            "Set <code>label</code> for an accessible region name. "
            "Add <code>show-transcript</code> to reveal a transcript slot. "
            "Listen for <code>mj-play</code>, <code>mj-pause</code>, "
            "<code>mj-ended</code>, and other events to integrate with "
            "analytics or UI state.</p>"
        ),
        example=(
            '<mj-media-player\n'
            '  type="video"\n'
            '  src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"\n'
            '  poster="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/BigBuckBunny.jpg"\n'
            '  label="Big Buck Bunny preview"\n'
            '  aspect-ratio="16/9"\n'
            '  style="max-width:560px">\n'
            '</mj-media-player>'
        ),
        attributes=[
            ("type", "video (default) | audio."),
            ("src", "URL of the media resource."),
            ("poster", "Poster image URL shown before video playback begins (video only)."),
            ("label", "Accessible label for the player region."),
            ("aspect-ratio", "CSS aspect-ratio of the video frame (default: 16/9)."),
            ("autoplay", "Boolean; starts playback on load (suppressed under prefers-reduced-motion)."),
            ("loop", "Boolean; loops the media."),
            ("muted", "Boolean; starts muted."),
            ("preload", "none | metadata (default) | auto — native preload hint."),
            ("show-transcript", "Boolean; reveals the transcript slot below the player."),
            ("crossorigin", "CORS setting forwarded to the native media element."),
            ("playback-rates", "Space-separated speed options (default: 0.5 0.75 1 1.25 1.5 2)."),
        ],
        events=[
            ("mj-play", "Fired when playback starts; includes currentTime."),
            ("mj-pause", "Fired when playback pauses; includes currentTime."),
            ("mj-ended", "Fired when the media finishes playing."),
            ("mj-seek", "Fired when the user seeks; includes currentTime and previousTime."),
            ("mj-volume-change", "Fired on volume or mute change; includes volume and muted."),
            ("mj-rate-change", "Fired on playback speed change; includes playbackRate."),
            ("mj-captions-change", "Fired when captions are toggled; includes track label or null."),
            ("mj-error", "Fired on media error; includes code and message."),
        ],
    ),
    ComponentDoc(
        tag="mj-chart",
        title="Chart",
        group="media",
        summary="The chart controller — 139 chart types selected by the type attribute, drawn as SVG from JSON.",
        description=(
            "<p><code>&lt;mj-chart&gt;</code> is the controller of the "
            "codecraftai-webworks chart library. A single component covers "
            "every chart type &mdash; bar, line, area, pie, donut, scatter, "
            "Sankey, treemap, gauge, OHLC, network, and ~130 more &mdash; "
            "selected by the <code>type</code> attribute. Data is supplied "
            "as JSON via the <code>data</code> JavaScript property, the "
            "<code>src</code> URL attribute, or an inline "
            "<code>&lt;script type=&quot;application/json&quot;&gt;</code> "
            "child. Visit <a href=\"/charts\">/charts</a> to browse all "
            "the chart types this controller can render.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>type</code> attribute to choose the chart "
            "kind (e.g. <code>bar</code>, <code>line</code>, <code>pie</code>, "
            "<code>sankey</code>). Supply data as JSON shaped per the "
            "chart family (categories + series for Cartesian, nodes + "
            "links for flows, a root tree for hierarchical, etc.). The "
            "controller re-renders whenever <code>data</code> or "
            "<code>type</code> change. Coordinated parts "
            "<code>&lt;mj-chart-title&gt;</code>, "
            "<code>&lt;mj-chart-legend&gt;</code> and "
            "<code>&lt;mj-chart-data-table&gt;</code> may be placed "
            "anywhere and bound by the chart's <code>id</code>.</p>"
        ),
        example=(
            '<mj-chart type="bar" style="height:260px">\n'
            '  <script type="application/json">\n'
            '  {\n'
            '    "categories": ["Q1","Q2","Q3","Q4"],\n'
            '    "series": [\n'
            '      {"name":"2024","values":[42,58,35,71]},\n'
            '      {"name":"2025","values":[55,49,68,80]}\n'
            '    ]\n'
            '  }\n'
            '  </script>\n'
            '</mj-chart>'
        ),
        attributes=[
            ("type", "Chart kind: bar/column/line/area/pie/donut/scatter/sankey/treemap and ~130 more — see /charts."),
            ("src", "URL to a JSON document; the controller fetches and parses it as the data."),
            ("orientation", "vertical | horizontal — default orientation for Cartesian renderers."),
        ],
        events=[
            ("mj-chart-render", "Fired after each successful draw; includes the resolved type."),
            ("mj-chart-error", "Fired on a data-source or renderer error; includes a message."),
            ("mj-chart-bar-click", "Renderer-specific: fired when a bar is activated (other renderers emit their own marker-click events)."),
        ],
    ),
    ComponentDoc(
        tag="mj-map",
        title="Map",
        group="media",
        summary="Accessible geographic map with pluggable provider adapter, keyboard pan/zoom, and marker list.",
        description=(
            "<p><code>&lt;mj-map&gt;</code> is an accessible geographic map container. "
            "No tile engine is bundled &mdash; a provider adapter (e.g. Leaflet, "
            "Google Maps) must be supplied via the <code>adapter</code> JavaScript "
            "property. The component adds keyboard pan/zoom, a visible zoom-in/zoom-out "
            "control overlay, and a screen-reader-friendly accessible marker list. "
            "Clicking a marker opens an inline popup panel. A <code>controls</code> "
            "slot allows additional overlay controls to be injected.</p>"
        ),
        how_to_use=(
            "<p>Set <code>lat</code>, <code>lng</code>, and <code>zoom</code> to "
            "position the initial view. Supply a map adapter via the <code>.adapter</code> "
            "JavaScript property. Populate markers via the <code>.markers</code> property "
            "using the shape <code>[{ id, label, lat, lng, description?, href? }]</code>. "
            "Set <code>label</code> (required) for the accessible region name. "
            "Add <code>show-list</code> to make the marker list visible to sighted users. "
            "Use <code>min-zoom</code> and <code>max-zoom</code> to constrain the zoom range.</p>"
        ),
        example=(
            '<mj-map id="demo-map"\n'
            '  label="World map centered on London"\n'
            '  lat="51.505" lng="-0.09" zoom="10"\n'
            '  show-list\n'
            '  style="height:360px">\n'
            '</mj-map>\n'
            '<script>\n'
            '  document.getElementById("demo-map").markers = [\n'
            '    { id: "bkng", label: "Buckingham Palace",\n'
            '      lat: 51.5014, lng: -0.1419,\n'
            '      description: "Official London residence of the UK monarch" },\n'
            '    { id: "tow",  label: "Tower of London",\n'
            '      lat: 51.5081, lng: -0.0759,\n'
            '      description: "Historic castle on the north bank of the Thames" }\n'
            '  ];\n'
            '</script>'
        ),
        attributes=[
            ("lat", "Initial map center latitude."),
            ("lng", "Initial map center longitude."),
            ("zoom", "Initial zoom level (default: 10)."),
            ("min-zoom", "Minimum allowed zoom level (default: 1)."),
            ("max-zoom", "Maximum allowed zoom level (default: 20)."),
            ("map-type", "Hint passed to the adapter; e.g. road | satellite (default: road)."),
            ("interactive", "Boolean; controls whether pan/zoom are enabled (adapter-dependent)."),
            ("show-list", "Boolean; makes the accessible marker list visible to sighted users."),
            ("label", "Accessible region label. Required."),
            ("loading", "Boolean; shows a loading overlay."),
        ],
        events=[
            ("mj-map-ready", "Fired when the adapter initialises successfully."),
            ("mj-map-zoom-change", "Fired (debounced) after a zoom change; includes zoom."),
            ("mj-map-move", "Fired when the map is panned via keyboard; includes lat, lng, zoom."),
            ("mj-map-marker-select", "Fired when a marker is selected; includes marker object."),
            ("mj-map-marker-deselect", "Fired when the marker popup is closed."),
            ("mj-map-error", "Fired when the adapter throws; includes message."),
        ],
    ),
    ComponentDoc(
        tag="mj-gauge",
        title="Gauge",
        group="media",
        summary="Single-value arc or linear meter with threshold bands, animated fill, and native meter semantics.",
        description=(
            "<p><code>&lt;mj-gauge&gt;</code> displays a single numeric value as "
            "an animated arc gauge or a horizontal linear progress bar. Color "
            "thresholds (supplied via the <code>.thresholds</code> JavaScript "
            "property) change the fill color as the value crosses boundaries, "
            "giving instant visual feedback for status indicators such as CPU "
            "usage, battery level, or NPS scores. A visually-hidden "
            "<code>&lt;meter&gt;</code> element provides native accessibility "
            "semantics. Values are formatted with <code>Intl.NumberFormat</code> "
            "and support a <code>unit</code> suffix.</p>"
        ),
        how_to_use=(
            "<p>Set <code>value</code>, <code>min</code>, and <code>max</code>. "
            "Use <code>shape=\"arc\"</code> (default) for a semicircular gauge or "
            "<code>shape=\"linear\"</code> for a progress bar. Provide "
            "<code>title</code> for a visible label and accessible name. "
            "Set <code>low</code>, <code>high</code>, and <code>optimum</code> "
            "to drive the native meter semantics. Supply threshold objects via the "
            "<code>.thresholds</code> property to colorize ranges: "
            "<code>[{ value, color, label }]</code>.</p>"
        ),
        example=(
            '<div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:flex-start">\n'
            '  <mj-gauge id="gauge-arc"\n'
            '    value="72" min="0" max="100"\n'
            '    title="CPU Usage" unit="%"\n'
            '    show-needle>\n'
            '  </mj-gauge>\n'
            '  <mj-gauge id="gauge-linear"\n'
            '    value="45" min="0" max="100"\n'
            '    title="Memory" unit="%" shape="linear"\n'
            '    show-min-max>\n'
            '  </mj-gauge>\n'
            '</div>\n'
            '<script>\n'
            '  document.getElementById("gauge-arc").thresholds = [\n'
            '    { value: 0,  color: "#059669", label: "Normal" },\n'
            '    { value: 70, color: "#d97706", label: "Warning" },\n'
            '    { value: 90, color: "#dc2626", label: "Critical" }\n'
            '  ];\n'
            '  document.getElementById("gauge-linear").thresholds = [\n'
            '    { value: 0,  color: "#2563eb", label: "Low" },\n'
            '    { value: 60, color: "#d97706", label: "High" }\n'
            '  ];\n'
            '</script>'
        ),
        attributes=[
            ("value", "Current numeric value to display."),
            ("min", "Minimum of the range (default: 0)."),
            ("max", "Maximum of the range (default: 100)."),
            ("low", "Low threshold forwarded to the native meter element."),
            ("high", "High threshold forwarded to the native meter element."),
            ("optimum", "Optimum value forwarded to the native meter element."),
            ("title", "Visible label shown above the gauge; also used as the accessible meter label."),
            ("unit", "Unit suffix appended to the formatted value label (e.g. %)."),
            ("shape", "arc (default) | linear."),
            ("arc-degrees", "Sweep angle of the arc in degrees (default: 240, range 90–360)."),
            ("show-needle", "Boolean (arc only); draws a pointer needle."),
            ("show-min-max", "Boolean (linear only); shows min and max labels."),
            ("precision", "Decimal places for the value label (default: 0)."),
            ("locale", "BCP 47 locale tag for Intl.NumberFormat."),
            ("animated", "Boolean; enables animated fill transition (respects prefers-reduced-motion)."),
        ],
        events=[
            ("mj-gauge-value-change", "Fired when the value attribute changes; includes value, previousValue, and threshold label."),
        ],
    ),
    ComponentDoc(
        tag="mj-sparkline",
        title="Sparkline",
        group="media",
        summary="Compact inline SVG trend chart supporting line, area, bar, and win/loss types.",
        description=(
            "<p><code>&lt;mj-sparkline&gt;</code> is a small inline data trend "
            "chart that fits naturally beside text or inside table cells. It "
            "supports four rendering modes: <code>line</code>, <code>area</code>, "
            "<code>bar</code>, and <code>win-loss</code>. All values are supplied "
            "as a comma-separated <code>values</code> attribute, making sparklines "
            "easy to generate server-side. An optional end-dot highlights the most "
            "recent value, and a reference line can mark a baseline. The SVG is "
            "<code>aria-hidden</code> unless a <code>label</code> attribute is "
            "supplied for screen readers.</p>"
        ),
        how_to_use=(
            "<p>Set <code>values</code> to a comma-separated list of numbers. "
            "Choose a <code>type</code> (line, area, bar, win-loss). "
            "Adjust <code>width</code> and <code>height</code> to size the SVG. "
            "Add <code>show-end-dot</code> to mark the final value. "
            "Set <code>reference-value</code> to draw a baseline reference line. "
            "Provide a <code>label</code> for an accessible SVG description. "
            "Add <code>animated</code> to animate the line draw-in on first render.</p>"
        ),
        example=(
            '<p>Revenue trend:\n'
            '  <mj-sparkline values="12,18,15,22,19,28,25,32"\n'
            '    type="area" width="120" height="32"\n'
            '    show-end-dot>\n'
            '  </mj-sparkline>\n'
            '</p>\n'
            '<p>Win/loss:\n'
            '  <mj-sparkline values="1,-1,1,1,-1,1,-1,1,1,1"\n'
            '    type="win-loss" width="80" height="28"\n'
            '    label="Win/loss record: 7 wins, 3 losses">\n'
            '  </mj-sparkline>\n'
            '</p>'
        ),
        attributes=[
            ("values", "Comma-separated list of numeric data points."),
            ("type", "line (default) | area | bar | win-loss."),
            ("width", "SVG width in pixels (default: 80)."),
            ("height", "SVG height in pixels (default: 24)."),
            ("show-end-dot", "Boolean; draws a dot on the last valid data point."),
            ("reference-value", "Numeric baseline; draws a dashed reference line at this value."),
            ("curve", "Reserved for future smooth-curve support."),
            ("label", "Accessible SVG aria-label; marks the SVG as role=img when set."),
            ("animated", "Boolean; animates the line draw-in (respects prefers-reduced-motion)."),
        ],
        events=[
            ("mj-sparkline-render", "Fired after the sparkline is drawn; includes type and pointCount."),
        ],
    ),
    ComponentDoc(
        tag="mj-diagram",
        title="Diagram",
        group="media",
        summary="Accessible node/edge graph diagram with pluggable layout adapter, keyboard navigation, and selection panel.",
        description=(
            "<p><code>&lt;mj-diagram&gt;</code> renders interactive node/edge "
            "graph diagrams. No layout engine is bundled &mdash; a layout adapter "
            "must be supplied via the <code>.adapter</code> JavaScript property. "
            "Graph data is supplied via the <code>.graph</code> property using the "
            "shape <code>{ nodes: [{ id, label, description? }], "
            "edges: [{ id, source, target, label? }] }</code>. "
            "The component provides keyboard pan/zoom, a fit-to-view button, "
            "an accessible node list (always rendered for screen readers), and "
            "an optional selection panel that opens when a node is activated.</p>"
        ),
        how_to_use=(
            "<p>Set <code>label</code> (required) for the accessible region name. "
            "Supply a layout adapter via the <code>.adapter</code> property, then "
            "set the <code>.graph</code> property. Use <code>directed</code> to "
            "indicate edge direction. Add <code>show-list</code> to make the node "
            "list visible to sighted users. Enable <code>show-selection-panel</code> "
            "to open a details panel on node click. Use <code>fit-on-load</code> "
            "(default true) to auto-fit the graph after data is set. "
            "Listen for <code>mj-diagram-node-select</code> to respond to selection.</p>"
        ),
        example=(
            '<mj-diagram id="demo-diagram"\n'
            '  label="Software architecture diagram"\n'
            '  show-list\n'
            '  style="height:400px">\n'
            '</mj-diagram>\n'
            '<script>\n'
            '  document.getElementById("demo-diagram").graph = {\n'
            '    nodes: [\n'
            '      { id: "ui",  label: "UI Layer",\n'
            '        description: "Browser-side web components" },\n'
            '      { id: "api", label: "API Gateway",\n'
            '        description: "Handles auth and routing" },\n'
            '      { id: "db",  label: "Database",\n'
            '        description: "PostgreSQL persistent store" }\n'
            '    ],\n'
            '    edges: [\n'
            '      { id: "e1", source: "ui",  target: "api", label: "HTTP/REST" },\n'
            '      { id: "e2", source: "api", target: "db",  label: "SQL" }\n'
            '    ]\n'
            '  };\n'
            '</script>'
        ),
        attributes=[
            ("label", "Accessible region label for the diagram canvas. Required."),
            ("directed", "Boolean (default true); indicates edges have direction."),
            ("interactive", "Boolean; controls pan/zoom interactivity (adapter-dependent)."),
            ("show-list", "Boolean; makes the accessible node list visible to sighted users."),
            ("show-selection-panel", "Boolean; opens a details side-panel when a node is activated."),
            ("fit-on-load", "Boolean (default true); calls adapter.fit() after graph data is loaded."),
            ("zoom", "Current zoom level; also accepted as initial zoom hint."),
            ("min-zoom", "Minimum zoom level (default: 0.25)."),
            ("max-zoom", "Maximum zoom level (default: 4)."),
            ("loading", "Boolean; shows a loading overlay."),
        ],
        events=[
            ("mj-diagram-ready", "Fired when the adapter initialises successfully."),
            ("mj-diagram-node-select", "Fired when a node is selected; includes node object."),
            ("mj-diagram-node-deselect", "Fired when the selection panel is closed."),
            ("mj-diagram-edge-select", "Fired when an edge is selected by the adapter; includes edge object."),
            ("mj-diagram-zoom-change", "Fired (debounced) after a zoom change; includes zoom."),
            ("mj-diagram-pan", "Fired (debounced) after a pan; includes x and y."),
            ("mj-diagram-error", "Fired when the adapter throws; includes message."),
        ],
    ),
]
