"""
    layout.py

    Catalog entries for the 'Layout' component group.

    Every component that arranges, contains, or spaces other components
    belongs here: surfaces, grids, stacks, disclosure panels, split views,
    scroll areas, feeds, and dock-based app shells.

    The examples are sandboxes: each one uses realistic slotted content
    (mostly other mj-* components), and the layout examples say which
    preview width preset (320 / 768 / 1024 / Full) and which direction
    (LTR / RTL) shows their responsive behaviour. Images are inline SVG
    data URIs so the pages work offline.

    The first example of a component is also the page the functional tests
    open, and a test that types its own markup into the playground keeps the
    first example's CSS and script. The first examples therefore scope their
    CSS to classes / ids and their scripts check that the element they
    drive exists.
"""

import base64
import math
import struct
import zlib

from textwrap import dedent
from urllib.parse import quote

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


def _code(text: str) -> str:
    """
        Dedent a triple-quoted markup, CSS or script block and trim the blank
        first and last lines.

        :param text: The indented source text.

        :returns: The dedented text.
    """

    result = dedent(text).strip("\n")
    return result


def _svg_uri(svg: str) -> str:
    """
        Turn an SVG document into a ``data:`` URI usable in ``src`` and in CSS
        ``url("...")``.

        :param svg: The SVG markup (single-quoted attributes).

        :returns: The data URI.
    """

    uri = "data:image/svg+xml," + quote(svg, safe=" /:=,;'()!*+")
    return uri


def _scene(width: int, height: int, sky: str, hills: str, sun: str, caption: str = "") -> str:
    """
        A simple landscape picture (sky, sun, two hill ranges) with an
        intrinsic size of ``width`` x ``height``.

        :param width: Intrinsic width in px.
        :param height: Intrinsic height in px.
        :param sky: Sky colour.
        :param hills: Hill colour.
        :param sun: Sun colour.
        :param caption: Optional text drawn in the lower start corner.

        :returns: A data URI.
    """

    text = ""
    if len(caption) > 0:
        size = max(14, int(height * 0.07))
        text = (
            f"<text x='{int(width * 0.04)}' y='{int(height * 0.93)}' font-family='sans-serif' "
            f"font-size='{size}' font-weight='700' fill='#ffffff'>{caption}</text>"
        )

    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        f"viewBox='0 0 {width} {height}'>"
        f"<rect width='{width}' height='{height}' fill='{sky}'/>"
        f"<circle cx='{int(width * 0.74)}' cy='{int(height * 0.3)}' r='{int(min(width, height) * 0.11)}' fill='{sun}'/>"
        f"<polygon points='0,{height} 0,{int(height * 0.62)} {int(width * 0.28)},{int(height * 0.42)} "
        f"{int(width * 0.52)},{int(height * 0.66)} {int(width * 0.78)},{int(height * 0.48)} "
        f"{width},{int(height * 0.6)} {width},{height}' fill='{hills}' opacity='0.65'/>"
        f"<polygon points='0,{height} 0,{int(height * 0.8)} {int(width * 0.35)},{int(height * 0.68)} "
        f"{int(width * 0.7)},{int(height * 0.84)} {width},{int(height * 0.74)} {width},{height}' fill='{hills}'/>"
        f"{text}</svg>"
    )
    uri = _svg_uri(svg)
    return uri


def _bands(width: int, height: int) -> str:
    """
        A tall picture made of three labelled bands (Top / Middle / Bottom),
        used to show what `fit` and `position` keep visible.

        :param width: Intrinsic width in px.
        :param height: Intrinsic height in px.

        :returns: A data URI.
    """

    band = height // 3
    size = int(width * 0.14)
    parts = []
    labels = [("Top", "#264653"), ("Middle", "#2a9d8f"), ("Bottom", "#e76f51")]
    for index, (label, colour) in enumerate(labels):
        top = band * index
        parts.append(f"<rect y='{top}' width='{width}' height='{band}' fill='{colour}'/>")
        parts.append(
            f"<text x='{width // 2}' y='{top + band // 2 + size // 3}' text-anchor='middle' "
            f"font-family='sans-serif' font-size='{size}' font-weight='700' fill='#ffffff'>{label}</text>"
        )
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        f"viewBox='0 0 {width} {height}' preserveAspectRatio='none'>" + "".join(parts) + "</svg>"
    )
    uri = _svg_uri(svg)
    return uri


def _png_landscape(width: int, height: int) -> str:
    """
        A small landscape picture as a PNG data URI (sky gradient, sun, two
        hill ranges). Used where only raster data URIs are accepted, such as
        the `bg-src` of mj-hero (SVG data URIs are rejected there).

        :param width: Width in px.
        :param height: Height in px.

        :returns: A ``data:image/png;base64,...`` URI.
    """

    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            mix = y / height
            red, green, blue = int(38 + 60 * mix), int(70 + 90 * mix), int(83 + 70 * mix)
            sun_dx, sun_dy = x - width * 0.72, y - height * 0.32
            if sun_dx * sun_dx + sun_dy * sun_dy < (height * 0.12) ** 2:
                red, green, blue = 233, 196, 106
            far = height * (0.62 - 0.18 * math.sin(x / width * math.pi * 2.2))
            near = height * (0.8 - 0.08 * math.sin(x / width * math.pi * 1.4 + 1.0))
            if y > far:
                red, green, blue = 42, 157, 143
            if y > near:
                red, green, blue = 29, 110, 100
            row.extend((red, green, blue))
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        packed = struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        return packed

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")
    uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    return uri


def _screenshot() -> str:
    """
        A small mock application window, used as hero media.

        :returns: A data URI.
    """

    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='640' height='400' viewBox='0 0 640 400'>"
        "<rect width='640' height='400' rx='14' fill='#f8fafc'/>"
        "<rect width='640' height='40' rx='14' fill='#1e293b'/>"
        "<rect y='26' width='640' height='14' fill='#1e293b'/>"
        "<circle cx='24' cy='20' r='6' fill='#f87171'/><circle cx='44' cy='20' r='6' fill='#fbbf24'/>"
        "<circle cx='64' cy='20' r='6' fill='#34d399'/>"
        "<rect x='0' y='40' width='150' height='360' fill='#e2e8f0'/>"
        "<rect x='20' y='64' width='100' height='12' rx='6' fill='#94a3b8'/>"
        "<rect x='20' y='92' width='80' height='12' rx='6' fill='#cbd5e1'/>"
        "<rect x='20' y='120' width='90' height='12' rx='6' fill='#cbd5e1'/>"
        "<rect x='180' y='64' width='200' height='16' rx='8' fill='#334155'/>"
        "<rect x='180' y='100' width='130' height='90' rx='10' fill='#6366f1'/>"
        "<rect x='325' y='100' width='130' height='90' rx='10' fill='#22c55e'/>"
        "<rect x='470' y='100' width='130' height='90' rx='10' fill='#f59e0b'/>"
        "<polyline points='180,330 240,290 300,310 360,250 420,270 480,220 540,240 600,200' "
        "fill='none' stroke='#6366f1' stroke-width='6' stroke-linecap='round'/>"
        "</svg>"
    )
    uri = _svg_uri(svg)
    return uri


IMG_TRAIL = _scene(640, 360, "#8ecae6", "#2d6a4f", "#ffb703")
IMG_LAKE = _scene(800, 600, "#a2d2ff", "#3d5a80", "#ffd166")
IMG_DUNES = _scene(600, 400, "#ffd6a5", "#bc6c25", "#fb8500")
IMG_FOREST = _scene(640, 480, "#cdeac0", "#1b4332", "#f4a261")
IMG_COAST = _scene(720, 360, "#bde0fe", "#0077b6", "#ffafcc")
IMG_SQUARE = _scene(400, 400, "#e9d8fd", "#553c9a", "#f6ad55")
IMG_HERO = _png_landscape(192, 108)
IMG_TALL = _bands(300, 600)
IMG_APP = _screenshot()

ICON_SEARCH = (
    '<svg slot="illustration" viewBox="0 0 64 64" width="64" height="64" fill="none" '
    'stroke="currentColor" stroke-width="3" stroke-linecap="round" aria-hidden="true">'
    '<circle cx="28" cy="28" r="18"/><line x1="41" y1="41" x2="56" y2="56"/></svg>'
)

ICON_FOLDER = (
    '<svg slot="illustration" viewBox="0 0 64 64" width="64" height="64" fill="none" '
    'stroke="currentColor" stroke-width="3" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M6 16h18l6 6h28v30H6z"/><line x1="24" y1="38" x2="40" y2="38"/>'
    '<line x1="32" y1="30" x2="32" y2="46"/></svg>'
)


# ---------------------------------------------------------------------------
# mj-card
# ---------------------------------------------------------------------------

CARD = ComponentDoc(
    tag="mj-card",
    title="Card",
    group="layout",
    summary="A contained content surface grouping media, header, body, and footer.",
    description=(
        "<p><code>&lt;mj-card&gt;</code> wraps one piece of content into a visually distinct box: "
        "optional media (<code>slot=\"media\"</code>) with a badge corner, a header built from the "
        "<code>heading</code> / <code>subheading</code> attributes or taken from "
        "<code>slot=\"header\"</code>, the body (default slot) and a footer for actions.</p>"
        "<p>The host is a column flex container and the card fills it, so cards stretched by a grid "
        "row or a flex parent are painted to the full height and their footers line up along the "
        "bottom edge even when the bodies differ in length. The media region is hidden while nothing "
        "is slotted into it; <code>aspect-ratio</code> gives it a fixed shape, and slotted media is "
        "cropped to fill it (<code>object-fit: cover</code>).</p>"
        "<p><code>orientation=\"horizontal\"</code> places the media beside the content. The row "
        "wraps: when the card is narrower than the media plus the content's minimum width "
        "(<code>--mj-card-content-min-width</code>, 12rem) the content drops below the media and the "
        "card reads as a vertical one.</p>"
        "<p><code>href</code> makes the card clickable: a link is stretched over the card and named "
        "from the heading (or the host's <code>aria-label</code>, the header slot text, or the start "
        "of the card's text). The footer, and interactive elements slotted directly into the header "
        "or body (links, buttons, form controls, elements with a tabindex, <code>mj-button</code>, "
        "<code>mj-link</code>), sit above the link and keep working; interactive content nested deeper "
        "inside the body needs <code>position: relative; z-index: 2</code>. Activating the link fires "
        "<code>mj-card-click</code>; <code>disabled</code> (or <code>loading</code>) switches the link "
        "off without blocking the footer.</p>"
        "<p><code>loading</code> covers the card with a shimmer, makes the regions underneath inert, "
        "sets <code>aria-busy</code> and announces Loading / Loaded through a status region.</p>"
    ),
    how_to_use=(
        "<p>Put body content between the tags. Use the <code>heading</code> and <code>subheading</code> "
        "attributes for a built-in header (an <code>h3</code>; set the <code>headingLevel</code> "
        "property for another level), or supply <code>slot=\"header\"</code> for full control. Add an "
        "<code>&lt;img slot=\"media\"&gt;</code> for a hero image and <code>aspect-ratio=\"16/9\"</code> "
        "so a row of cards gets media of equal height. Put actions in <code>slot=\"footer\"</code> and "
        "a status chip in <code>slot=\"badge\"</code> (it is positioned in the top end corner of the "
        "media). Place cards in an <code>&lt;mj-grid&gt;</code> for a responsive gallery.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="heading", description="Heading text of the built-in header (rendered as text, never as markup).",
                     kind="string"),
        AttributeDoc(name="subheading", description="Secondary line under the heading.", kind="string"),
        AttributeDoc(name="elevation", description="Shadow or border treatment.", kind="enum",
                     values=["raised", "flat", "outlined"], default="raised"),
        AttributeDoc(name="orientation", description="`horizontal` puts the media beside the content; the card stacks again when it is too narrow.",
                     kind="enum", values=["vertical", "horizontal"], default="vertical"),
        AttributeDoc(name="aspect-ratio", description="CSS aspect-ratio of the media region, e.g. `16/9`; an unusable value is ignored.",
                     kind="string", values=["16/9", "4/3", "1", "2/1"]),
        AttributeDoc(name="href", description="Makes the whole card a link; footer and slotted controls stay clickable. Script URLs are neutralised.",
                     kind="string", values=["#details", "/components/layout/mj-grid"]),
        AttributeDoc(name="disabled", description="Switches the card link off (aria-disabled, not focusable); content and footer stay usable.",
                     kind="boolean"),
        AttributeDoc(name="loading", description="Shows the shimmer, makes the content inert, sets aria-busy and announces the state.",
                     kind="boolean"),
        AttributeDoc(name="aria-label", description="Accessible name of the card link when the heading should not be used.",
                     kind="string"),
    ],
    events=[
        ("mj-card-click", "The card link was activated (not fired while disabled or loading). Bubbles; cancel the original event to stop navigation.",
         "{ originalEvent: MouseEvent }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A card with media, the attribute header, a body and footer actions. Use the controls to "
                "switch <code>elevation</code>, try <code>orientation=horizontal</code>, or set "
                "<code>loading</code>.</p>"
            ),
            html=_code(f"""
                <mj-card class="demo-card" heading="Mountain hike" subheading="Saturday, 7:30 am &middot; 14 km"
                  elevation="raised" aspect-ratio="16/9">
                  <img slot="media" src="{IMG_TRAIL}" alt="Trail winding up through alpine meadows" />
                  <p>A full-day trek through alpine meadows to the Seven Lakes viewpoint. Moderate climb,
                    packed lunch provided.</p>
                  <div slot="footer" class="demo-card-actions">
                    <mj-button variant="primary" size="sm">Book a seat</mj-button>
                    <mj-button variant="secondary" size="sm">Route details</mj-button>
                  </div>
                </mj-card>
            """),
            css=_code("""
                .demo-card { max-inline-size: 22rem; margin: var(--mj-space-4); }
                .demo-card-actions { display: flex; flex-wrap: wrap; gap: var(--mj-space-2); }
            """),
        ),
        ComponentExample(
            key="grid",
            title="Cards in a grid",
            description=(
                "<p>Six cards with unequal content in an auto-fill <code>mj-grid</code>. Every card is "
                "stretched to the row height and the footers line up. <code>aspect-ratio</code> gives "
                "media of different shapes the same height; the last card has no media, so its media "
                "region is removed. Try the <b>320</b>, <b>768</b> and <b>Full</b> width presets: the "
                "grid goes from one to two to three or more columns.</p>"
            ),
            html=_code(f"""
                <mj-grid min-col-width="15rem" gap="md" class="card-gallery">
                  <mj-card heading="Alpine trail" subheading="14 km &middot; hard" aspect-ratio="16/9">
                    <img slot="media" src="{IMG_TRAIL}" alt="Alpine trail" />
                    <p>Steep switchbacks to the ridge, then an easy walk past seven glacier lakes.</p>
                    <div slot="footer"><mj-button size="sm" variant="primary">Book</mj-button></div>
                  </mj-card>
                  <mj-card heading="Lake loop" subheading="6 km &middot; easy" aspect-ratio="16/9">
                    <img slot="media" src="{IMG_LAKE}" alt="Lake with hills" />
                    <p>Flat gravel path.</p>
                    <div slot="footer"><mj-button size="sm" variant="primary">Book</mj-button></div>
                  </mj-card>
                  <mj-card heading="Dune walk" subheading="9 km &middot; moderate" aspect-ratio="16/9">
                    <img slot="media" src="{IMG_DUNES}" alt="Sand dunes at sunset" />
                    <p>Soft sand most of the way. Bring sun protection and at least two litres of water;
                      there is no shade and no refill point until the beach kiosk at the turning point.</p>
                    <div slot="footer"><mj-button size="sm" variant="primary">Book</mj-button></div>
                  </mj-card>
                  <mj-card heading="Forest path" subheading="11 km &middot; moderate" aspect-ratio="16/9">
                    <img slot="media" src="{IMG_FOREST}" alt="Path through a forest" />
                    <span slot="badge" class="badge">New</span>
                    <p>Shaded all day; muddy after rain.</p>
                    <div slot="footer"><mj-button size="sm" variant="primary">Book</mj-button></div>
                  </mj-card>
                  <mj-card heading="Coast road" subheading="18 km &middot; cycling" aspect-ratio="16/9">
                    <img slot="media" src="{IMG_COAST}" alt="Road along the sea" />
                    <p>Rolling road along the cliffs with three cafe stops.</p>
                    <div slot="footer"><mj-button size="sm" variant="primary">Book</mj-button></div>
                  </mj-card>
                  <mj-card heading="Guide training" subheading="Weekend course" elevation="outlined">
                    <p>No media: the media region is removed. Learn route planning, first aid and group
                      management in two days.</p>
                    <div slot="footer"><mj-button size="sm" variant="secondary">Join waitlist</mj-button></div>
                  </mj-card>
                </mj-grid>
            """),
            css=_code("""
                .card-gallery { padding: var(--mj-space-4); }
                .badge {
                  padding: var(--mj-space-1) var(--mj-space-2);
                  border-radius: var(--mj-radius-pill);
                  background: var(--mj-accent);
                  color: var(--mj-text-on-accent);
                  font-size: var(--mj-font-size-xs);
                  font-weight: var(--mj-font-weight-bold);
                }
            """),
        ),
        ComponentExample(
            key="horizontal",
            title="Horizontal cards",
            description=(
                "<p><code>orientation=\"horizontal\"</code> puts the media beside the content. At the "
                "<b>320</b> preset the card is narrower than media plus 12rem of content, so the content "
                "wraps under the media. Switch <b>Dir</b> to <b>RTL</b>: the media moves to the right. The "
                "second card uses <code>slot=\"header\"</code> instead of the attributes.</p>"
            ),
            html=_code(f"""
                <mj-card orientation="horizontal" heading="Lake loop" subheading="6 km &middot; easy"
                  elevation="outlined" class="row-card">
                  <img slot="media" src="{IMG_LAKE}" alt="Lake with hills" />
                  <p>A flat gravel loop around the reservoir, suitable for strollers. Toilets at the
                    car park and halfway.</p>
                  <div slot="footer"><mj-button size="sm" variant="primary">Book</mj-button></div>
                </mj-card>
                <mj-card orientation="horizontal" elevation="outlined" class="row-card">
                  <img slot="media" src="{IMG_SQUARE}" alt="Summit at dusk" />
                  <div slot="header" class="custom-header">
                    <mj-avatar name="Rita Okafor" size="sm"></mj-avatar>
                    <div><strong>Summit sunrise</strong><br><small>Guided by Rita Okafor</small></div>
                  </div>
                  <p>Start at 4 am with head torches; breakfast on the summit.</p>
                </mj-card>
            """),
            css=_code("""
                .row-card { max-inline-size: 36rem; margin: var(--mj-space-4); }
                .custom-header { display: flex; align-items: center; gap: var(--mj-space-2); }
                .custom-header small { color: var(--mj-text-muted); }
            """),
        ),
        ComponentExample(
            key="events",
            title="Clickable card",
            description=(
                "<p><code>href</code> stretches a link over the card. Clicking the body or media fires "
                "<code>mj-card-click</code> (the script cancels navigation and logs it); the footer "
                "buttons are above the link and log their own clicks. The script clicks the link once on "
                "load. Toggle <code>disabled</code>: the link stops working but the footer still does.</p>"
            ),
            html=_code(f"""
                <mj-card id="demo-link-card" href="#trail-42" heading="Forest path" subheading="11 km &middot; moderate"
                  aspect-ratio="2/1" class="link-card">
                  <img slot="media" src="{IMG_FOREST}" alt="Path through a forest" />
                  <span slot="badge" class="badge">3 seats left</span>
                  <p>Click anywhere on the card to open the route.</p>
                  <div slot="footer" class="link-card-actions">
                    <mj-button id="save-route" size="sm" variant="secondary">Save</mj-button>
                    <mj-button id="share-route" size="sm" variant="tertiary">Share</mj-button>
                  </div>
                </mj-card>
            """),
            css=_code("""
                .link-card { max-inline-size: 22rem; margin: var(--mj-space-4); }
                .link-card-actions { display: flex; gap: var(--mj-space-2); }
                .badge {
                  padding: var(--mj-space-1) var(--mj-space-2);
                  border-radius: var(--mj-radius-pill);
                  background: var(--mj-surface);
                  color: var(--mj-text);
                  font-size: var(--mj-font-size-xs);
                  box-shadow: var(--mj-elevation-1);
                }
            """),
            script=_code("""
                const card = document.getElementById("demo-link-card")
                card.addEventListener("mj-card-click", (event) => {
                  event.detail.originalEvent.preventDefault()
                  mjSandbox.log("navigate to", { href: card.getAttribute("href") })
                })
                for (const id of ["save-route", "share-route"]) {
                  document.getElementById(id).addEventListener("click", () => mjSandbox.log("footer action", { id: id }))
                }
                card.linkElement.click()
            """),
        ),
        ComponentExample(
            key="states",
            title="Elevation and states",
            description=(
                "<p>The three elevations side by side, then a loading card and a disabled clickable card. "
                "<b>Toggle loading</b> switches the shimmer on and off; the status region announces "
                "Loading / Loaded.</p>"
            ),
            html=_code("""
                <mj-grid min-col-width="12rem" gap="md" class="states">
                  <mj-card id="loading-card" heading="Raised" subheading="default" elevation="raised" loading>
                    <p>Shadow, no border.</p>
                  </mj-card>
                  <mj-card heading="Flat" subheading="elevation=flat" elevation="flat">
                    <p>No shadow, no border; sits on a tinted page.</p>
                  </mj-card>
                  <mj-card heading="Outlined" subheading="elevation=outlined" elevation="outlined">
                    <p>A 1px border instead of the shadow.</p>
                  </mj-card>
                  <mj-card heading="Disabled link" subheading="href + disabled" href="#nowhere" disabled
                    elevation="outlined">
                    <p>The card link is off; the footer still works.</p>
                    <div slot="footer"><mj-button size="sm" variant="secondary">Still clickable</mj-button></div>
                  </mj-card>
                </mj-grid>
                <mj-button id="toggle-loading" variant="secondary" class="toggle">Toggle loading</mj-button>
            """),
            css=_code("""
                .states { padding: var(--mj-space-4); background: var(--mj-bg-muted); }
                .toggle { margin: var(--mj-space-4); }
            """),
            script=_code("""
                const card = document.getElementById("loading-card")
                document.getElementById("toggle-loading").addEventListener("click", () => {
                  card.toggleAttribute("loading")
                  mjSandbox.log("loading", { loading: card.hasAttribute("loading") })
                })
            """),
        ),
    ],
    slots=[
        ("", "Body content.", "<p>Body text supplied by the slot inspector.</p>"),
        ("media", "Hero image or video; cropped to fill the media region. The region is hidden while empty.",
         f'<img src="{IMG_COAST}" alt="Coast road" />'),
        ("header", "Replaces the attribute-driven heading and subheading.",
         "<div><strong>Custom header</strong><br><small>From slot=header</small></div>"),
        ("footer", "Action row; stays clickable on a clickable card.",
         '<div><mj-button size="sm" variant="primary">Primary</mj-button> <mj-button size="sm" variant="secondary">Secondary</mj-button></div>'),
        ("badge", "Positioned in the top end corner of the media region.", "<span>New</span>"),
        ("badge-inner", "Fallback badge slot nested inside `badge` (used when nothing is slotted into `badge`).",
         "<span>Inner</span>"),
    ],
    properties=[
        ("headingLevel", "number. Level (1-6) of the generated heading element; default 3."),
        ("linkElement", "HTMLAnchorElement | null. The stretched card link while `href` is set (read-only)."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    parts=[
        ("root", "The article box."),
        ("media", "Media region (also holds the badge)."),
        ("badge", "Badge corner inside the media region."),
        ("header", "Header region."),
        ("header-attr", "The attribute-driven heading/subheading block."),
        ("body", "Body region (default slot)."),
        ("footer", "Footer region."),
        ("link", "The stretched link, present while `href` is set."),
    ],
    css_properties=[
        ("--mj-card-bg", "Card background (default var(--mj-surface))."),
        ("--mj-card-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-card-shadow", "Shadow; written by `elevation` when that attribute is set (default var(--mj-elevation-2))."),
        ("--mj-card-border-width", "Border width; written by `elevation` when set (default 0)."),
        ("--mj-card-border", "Border colour (default var(--mj-border))."),
        ("--mj-card-padding", "Padding of header, body and footer (default var(--mj-space-4))."),
        ("--mj-card-gap", "Gap between header, body and footer (default var(--mj-space-2))."),
        ("--mj-card-media-ratio", "Aspect ratio of the media region; written by `aspect-ratio` (default auto)."),
        ("--mj-card-content-min-width", "Minimum content width of a horizontal card before it stacks (default 12rem)."),
        ("--mj-card-shimmer-duration", "Duration of one loading shimmer sweep (default 1.5s)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-surface
# ---------------------------------------------------------------------------

SURFACE = ComponentDoc(
    tag="mj-surface",
    title="Surface",
    group="layout",
    summary="A generic content wrapper providing elevation, padding, radius and content-width containers.",
    description=(
        "<p><code>&lt;mj-surface&gt;</code> is the basic container primitive: Panel, Section and "
        "Container in one element configured by attributes. Use it for any padded, optionally elevated "
        "region that is not semantically a card, dialog or other named construct.</p>"
        "<p>The host is a column flex container and the painted box grows to fill it, so a surface with "
        "an explicit height, or one stretched by a grid row, flex parent or dock layout, is painted over "
        "its whole box.</p>"
        "<p><code>max-width</code> constrains and centres the painted box. Together with "
        "<code>full-bleed</code> the background runs edge to edge and only the <em>content</em> is "
        "constrained and centred (the inline padding absorbs the extra width), which is the usual "
        "page-band pattern. A custom property is written only for attributes that are present, so "
        "stylesheet rules such as <code>mj-surface { --mj-surface-padding: 2rem }</code> apply when "
        "the attribute is absent. Those attribute-driven properties belong to one surface: a nested "
        "surface does not inherit the padding, radius, elevation or max-width of the one around it. "
        "The colours (<code>--mj-surface-bg</code>, <code>--mj-surface-border</code>) inherit like "
        "theme tokens.</p>"
    ),
    how_to_use=(
        "<p>Wrap any content between the tags. Set <code>elevation</code> to <code>outlined</code>, "
        "<code>raised</code> or <code>overlay</code>; pick a <code>padding</code> step and a "
        "<code>radius</code>. Set <code>role-hint=\"section\"</code> to render a "
        "<code>&lt;section&gt;</code> instead of a <code>&lt;div&gt;</code> (give it an accessible name "
        "with <code>aria-labelledby</code> on the host if it should be a region). Use "
        "<code>max-width</code> plus <code>full-bleed</code> for content-width bands whose background "
        "spans the page. Colour the surface with <code>--mj-surface-bg</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="elevation", description="Shadow / border treatment.", kind="enum",
                     values=["flat", "outlined", "raised", "overlay"], default="flat"),
        AttributeDoc(name="padding", description="Inner padding step.", kind="enum",
                     values=["none", "sm", "md", "lg", "xl"], default="md"),
        AttributeDoc(name="radius", description="Corner rounding.", kind="enum",
                     values=["none", "sm", "md", "lg", "full"], default="md"),
        AttributeDoc(name="role-hint", description="`section` renders the root as a <section> element.", kind="enum",
                     values=["generic", "section"], default="generic"),
        AttributeDoc(name="max-width", description="CSS length; constrains and centres the painted box (the content only, with `full-bleed`).",
                     kind="string", values=["40rem", "60ch", "720px"]),
        AttributeDoc(name="full-bleed", description="Removes padding and radius; with `max-width` the background spans the full width.",
                     kind="boolean"),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>An outlined settings panel. Use the controls to try the other elevations, padding steps "
                "and radii.</p>"
            ),
            html=_code("""
                <mj-surface class="demo-surface" elevation="outlined" padding="lg" radius="md">
                  <h3 class="surface-title">Notifications</h3>
                  <p class="surface-text">Choose how you hear about new comments and mentions.</p>
                  <mj-stack direction="horizontal" gap="sm" wrap>
                    <mj-toggle-button pressed>Email</mj-toggle-button>
                    <mj-toggle-button>Push notification</mj-toggle-button>
                    <mj-toggle-button>Weekly digest</mj-toggle-button>
                  </mj-stack>
                </mj-surface>
            """),
            css=_code("""
                .demo-surface { max-inline-size: 28rem; margin: var(--mj-space-4); }
                .surface-title { margin: 0 0 var(--mj-space-2); }
                .surface-text { margin: 0 0 var(--mj-space-3); color: var(--mj-text-muted); }
            """),
        ),
        ComponentExample(
            key="variants",
            title="Elevations",
            description=(
                "<p>The four elevations on a tinted background, placed in a grid. The grid stretches each "
                "surface to the row height and the painted box fills it, although the texts differ in "
                "length. Try the <b>320</b> preset: one column.</p>"
            ),
            html=_code("""
                <mj-grid min-col-width="11rem" gap="md" class="elevations">
                  <mj-surface elevation="flat"><strong>flat</strong><p>Default. No shadow or border.</p></mj-surface>
                  <mj-surface elevation="outlined"><strong>outlined</strong><p>1px border.</p></mj-surface>
                  <mj-surface elevation="raised"><strong>raised</strong><p>Card-level shadow for content that
                    sits above the page, such as a summary panel.</p></mj-surface>
                  <mj-surface elevation="overlay"><strong>overlay</strong><p>The strongest shadow, for
                    floating panels.</p></mj-surface>
                </mj-grid>
            """),
            css=_code("""
                .elevations { padding: var(--mj-space-5); background: var(--mj-bg-muted); }
                .elevations p { margin: var(--mj-space-2) 0 0; }
            """),
        ),
        ComponentExample(
            key="container",
            title="Content-width bands",
            description=(
                "<p>Page bands built from <code>full-bleed</code> + <code>max-width=\"36rem\"</code>: the "
                "background spans the full width of the container while the text column stays 36rem wide and centred. The middle "
                "surface has <code>max-width</code> only, so the painted box itself is constrained. Compare "
                "the <b>Full</b>, <b>1024</b> and <b>320</b> presets.</p>"
            ),
            html=_code("""
                <mj-surface full-bleed max-width="36rem" class="band band-accent" role-hint="section">
                  <h2>Release 4.2</h2>
                  <p>Dock layouts now keep the sizes you give their bands, and split panes remember their
                    ratio when the window is resized.</p>
                </mj-surface>
                <mj-surface max-width="36rem" elevation="raised" padding="lg" class="band-gap">
                  <strong>Constrained box</strong>
                  <p>max-width without full-bleed: the painted box is 36rem wide and centred.</p>
                </mj-surface>
                <mj-surface full-bleed max-width="36rem" class="band band-muted">
                  <p>Footer band: same column width as the band above, background edge to edge.</p>
                </mj-surface>
            """),
            css=_code("""
                .band { --mj-surface-bg: var(--mj-bg-muted); }
                .band::part(root) { padding-block: var(--mj-space-5); }
                .band-accent { --mj-surface-bg: var(--mj-accent); color: var(--mj-text-on-accent); }
                .band h2 { margin: 0 0 var(--mj-space-2); }
                .band-gap { margin-block: var(--mj-space-5); }
            """),
        ),
        ComponentExample(
            key="nested",
            title="Nested surfaces",
            description=(
                "<p>A raised dashboard section (<code>role-hint=\"section\"</code>, "
                "<code>padding=\"lg\"</code>) holding nested surfaces in a stack and a grid: three outlined "
                "stat tiles with <code>radius=\"lg\"</code> and a note that only sets "
                "<code>padding=\"sm\"</code> -- it stays flat, because a nested surface never inherits "
                "the elevation of the one around it. Try <b>768</b> and <b>320</b>: the tiles reflow.</p>"
            ),
            html=_code("""
                <mj-surface role-hint="section" elevation="raised" padding="lg" aria-labelledby="usage-title"
                  class="dashboard">
                  <mj-stack gap="md">
                    <mj-stack direction="horizontal" align="center" wrap gap="sm">
                      <h3 id="usage-title" class="no-margin">Usage this month</h3>
                      <mj-spacer></mj-spacer>
                      <mj-button size="sm" variant="secondary">Export</mj-button>
                    </mj-stack>
                    <mj-grid columns="3" min-col-width="9rem" gap="sm">
                      <mj-surface elevation="outlined" radius="lg" padding="md"><small>Builds</small><div class="stat">1,284</div></mj-surface>
                      <mj-surface elevation="outlined" radius="lg" padding="md"><small>Minutes</small><div class="stat">9,410</div></mj-surface>
                      <mj-surface elevation="outlined" radius="lg" padding="md"><small>Storage</small><div class="stat">38 GB</div></mj-surface>
                    </mj-grid>
                    <mj-surface padding="sm" class="note">Quota resets on the 1st. Nested surface with padding=sm.</mj-surface>
                  </mj-stack>
                </mj-surface>
            """),
            css=_code("""
                .dashboard { margin: var(--mj-space-4); }
                .no-margin { margin: 0; }
                .stat { font-size: var(--mj-font-size-xl); font-weight: var(--mj-font-weight-bold); }
                .note { --mj-surface-bg: var(--mj-bg-muted); color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
            """),
        ),
    ],
    slots=[
        ("", "Surface content.", "<p>Content supplied by the slot inspector.</p>"),
    ],
    properties=[
        ("contentElement", "HTMLElement. The painted root element (div or section) that holds the slot (read-only)."),
    ],
    parts=[
        ("root", "The painted box (a div, or a section with role-hint=section)."),
    ],
    css_properties=[
        ("--mj-surface-bg", "Background (default var(--mj-surface))."),
        ("--mj-surface-padding", "Padding; written by `padding` (default var(--mj-space-4)). Per element: not inherited by nested surfaces."),
        ("--mj-surface-radius", "Corner radius; written by `radius` (default var(--mj-radius-md)). Per element."),
        ("--mj-surface-shadow", "Shadow; written by `elevation` (default none). Per element."),
        ("--mj-surface-border-width", "Border width; written by `elevation` (default 0). Per element."),
        ("--mj-surface-border", "Border colour (default var(--mj-border))."),
        ("--mj-surface-max-width", "Maximum inline size; written by `max-width` (default none). Per element."),
    ],
)


# ---------------------------------------------------------------------------
# mj-grid
# ---------------------------------------------------------------------------

GRID = ComponentDoc(
    tag="mj-grid",
    title="Grid",
    group="layout",
    summary="A responsive CSS Grid primitive with auto-fill, capped, fixed and masonry column modes.",
    description=(
        "<p><code>&lt;mj-grid&gt;</code> is a declarative CSS Grid wrapper. Every element child is one "
        "cell. Column modes:</p>"
        "<ul>"
        "<li><b>auto</b> (default): as many columns of at least <code>min-col-width</code> (16rem) as "
        "fit; the grid reflows as the container narrows.</li>"
        "<li><code>columns=\"N\"</code>: exactly N equal columns. The tracks may shrink to any width, so "
        "the grid never overflows a narrow container.</li>"
        "<li><code>columns=\"N\"</code> plus <code>min-col-width</code>: <em>at most</em> N columns, "
        "each at least <code>min-col-width</code>; the count drops on narrow containers.</li>"
        "<li><code>layout=\"masonry\"</code>: items flow into balanced columns of their own height (CSS "
        "multi-column, using the same <code>columns</code> / <code>min-col-width</code>). Items keep "
        "DOM order top to bottom within a column; native CSS masonry is not used "
        "(<code>masonrySupported</code> is false).</li>"
        "</ul>"
        "<p>A child spans tracks with ordinary CSS on the child (<code>grid-column: span 2</code>, "
        "<code>grid-row: span 2</code>); <code>dense</code> back-fills the holes that spanning leaves. "
        "A non-bubbling <code>mj-grid-layout</code> event reports the column count after every resize "
        "and after attribute changes.</p>"
    ),
    how_to_use=(
        "<p>Place children directly inside <code>&lt;mj-grid&gt;</code>. For a responsive gallery set "
        "only <code>min-col-width</code>; for a form or dashboard with a maximum column count add "
        "<code>columns</code>. Tune spacing with <code>gap</code>, or <code>col-gap</code> / "
        "<code>row-gap</code> separately. <code>align-items</code> controls vertical alignment inside "
        "a row; the default <code>stretch</code> gives cards of equal height. A grid nested in a "
        "cell is laid out by its own attributes only: the <code>--mj-grid-*</code> properties are "
        "per element and are not inherited.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="columns", description="Column count: `auto` (default) or a positive integer. With `min-col-width` it is a maximum.",
                     kind="string", values=["auto", "2", "3", "4", "6"], default="auto"),
        AttributeDoc(name="min-col-width", description="Minimum column width (a CSS length); an unusable value warns and falls back.",
                     kind="string", values=["10rem", "12rem", "16rem", "240px"], default="16rem"),
        AttributeDoc(name="gap", description="Gap between rows and columns.", kind="enum",
                     values=["none", "xs", "sm", "md", "lg", "xl"], default="md"),
        AttributeDoc(name="col-gap", description="Column gap; overrides `gap` for columns.", kind="enum",
                     values=["none", "xs", "sm", "md", "lg", "xl"]),
        AttributeDoc(name="row-gap", description="Row gap; overrides `gap` for rows.", kind="enum",
                     values=["none", "xs", "sm", "md", "lg", "xl"]),
        AttributeDoc(name="layout", description="`masonry` flows items into balanced columns (CSS multi-column).",
                     kind="enum", values=["masonry"]),
        AttributeDoc(name="dense", description="grid-auto-flow: dense; back-fills holes left by spanning items.", kind="boolean"),
        AttributeDoc(name="align-items", description="Alignment of items inside their row.", kind="enum",
                     values=["stretch", "start", "center", "end", "baseline"], default="stretch"),
    ],
    events=[
        ("mj-grid-layout", "Non-bubbling. Fires after a resize or an attribute change with the current column count.",
         "{ columns: number, masonry: boolean }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Responsive card grid",
            description=(
                "<p>The default auto-fill mode with <code>min-col-width=\"14rem\"</code> and cards of "
                "unequal content: each row is as tall as its tallest card. Try the <b>320</b>, <b>768</b> "
                "and <b>Full</b> presets and watch <code>mj-grid-layout</code> in Events report the new "
                "column count.</p>"
            ),
            html=_code("""
                <mj-grid class="demo-grid" min-col-width="14rem" gap="md">
                  <mj-card heading="Build pipeline" subheading="Passing" elevation="outlined">
                    <p>All 312 checks passed in 6 minutes.</p>
                  </mj-card>
                  <mj-card heading="Deploy to staging" subheading="Waiting for approval" elevation="outlined">
                    <p>Release 4.2.0 is ready. Two reviewers must approve before the change set is promoted
                      to the staging cluster.</p>
                    <div slot="footer"><mj-button size="sm" variant="primary">Approve</mj-button></div>
                  </mj-card>
                  <mj-card heading="Open incidents" subheading="None" elevation="outlined">
                    <p>Quiet week.</p>
                  </mj-card>
                  <mj-card heading="Error budget" subheading="72% left" elevation="outlined">
                    <mj-progress value="72" label="Error budget remaining" show-value></mj-progress>
                  </mj-card>
                  <mj-card heading="On call" subheading="This week" elevation="outlined">
                    <mj-media-object align="center" gap="sm" media-size="auto">
                      <mj-avatar slot="media" name="Priya Natarajan" size="sm"></mj-avatar>
                      Priya Natarajan
                    </mj-media-object>
                  </mj-card>
                </mj-grid>
            """),
            css=".demo-grid { padding: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="columns",
            title="Fixed and capped columns",
            description=(
                "<p>Top: <code>columns=\"3\" min-col-width=\"16rem\"</code> means <em>at most</em> three "
                "columns of at least 16rem: <b>Full</b> shows three, the <b>768</b> preset two and <b>320</b> one. "
                "Bottom: <code>columns=\"4\"</code> alone keeps four columns at every width; the tracks "
                "shrink instead of overflowing (try <b>320</b>).</p>"
            ),
            html=_code("""
                <section class="mode">
                  <h4>columns="3" min-col-width="16rem"</h4>
                  <mj-grid columns="3" min-col-width="16rem" gap="sm">
                    <mj-text-field label="First name" name="first" value="Ada"></mj-text-field>
                    <mj-text-field label="Last name" name="last" value="Lovelace"></mj-text-field>
                    <mj-text-field label="Email" name="email" type="email" value="ada@example.com"></mj-text-field>
                    <mj-text-field label="Role" name="role" value="Administrator"></mj-text-field>
                    <mj-text-field label="Team" name="team" value="Platform"></mj-text-field>
                    <mj-text-field label="Location" name="location" value="London"></mj-text-field>
                  </mj-grid>
                </section>
                <section class="mode">
                  <h4>columns="4"</h4>
                  <mj-grid columns="4" gap="sm">
                    <div class="cell">Q1<br><b>$1.2M</b></div>
                    <div class="cell">Q2<br><b>$1.4M</b></div>
                    <div class="cell">Q3<br><b>$1.1M</b></div>
                    <div class="cell">Q4<br><b>$1.9M</b></div>
                  </mj-grid>
                </section>
            """),
            css=_code("""
                .mode { padding: var(--mj-space-4); }
                .mode h4 { margin: 0 0 var(--mj-space-2); font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); }
                .cell { padding: var(--mj-space-3); background: var(--mj-bg-muted); border-radius: var(--mj-radius-sm); overflow-wrap: anywhere; }
            """),
        ),
        ComponentExample(
            key="spanning",
            title="Spanning and dense packing",
            description=(
                "<p>A dashboard: the chart cell spans two columns and two rows, the wide note spans two "
                "columns (plain CSS <code>grid-column</code> / <code>grid-row</code> on the children). "
                "<code>dense</code> fills the holes with later small tiles; toggle it in Controls to see "
                "the gaps return. <code>col-gap=\"lg\"</code> and <code>row-gap=\"sm\"</code> differ.</p>"
            ),
            html=_code("""
                <mj-grid columns="4" min-col-width="8rem" col-gap="lg" row-gap="sm" dense class="dash">
                  <mj-surface elevation="outlined" class="tile wide">Wide note: release freeze starts Friday.</mj-surface>
                  <mj-surface elevation="outlined" class="tile big">
                    <strong>Requests per minute</strong>
                    <mj-sparkline values="[12,18,15,22,30,26,34,40,37,45]" width="220" height="64" label="Requests per minute" class="spark"></mj-sparkline>
                  </mj-surface>
                  <mj-surface elevation="outlined" class="tile">CPU 41%</mj-surface>
                  <mj-surface elevation="outlined" class="tile">Memory 63%</mj-surface>
                  <mj-surface elevation="outlined" class="tile">Disk 18%</mj-surface>
                  <mj-surface elevation="outlined" class="tile">Errors 0.2%</mj-surface>
                  <mj-surface elevation="outlined" class="tile">Queue 12</mj-surface>
                </mj-grid>
            """),
            css=_code("""
                .dash { padding: var(--mj-space-4); }
                .tile { min-block-size: 4rem; }
                .wide { grid-column: span 2; }
                .big { grid-column: span 2; grid-row: span 2; }
                .spark { display: block; margin-block-start: var(--mj-space-3); }
            """),
        ),
        ComponentExample(
            key="masonry",
            title="Masonry",
            description=(
                "<p><code>layout=\"masonry\"</code> with <code>min-col-width=\"12rem\"</code>: notes of "
                "very different heights flow into balanced columns without row gaps. Try <b>768</b> and "
                "<b>320</b>.</p>"
            ),
            html=_code("""
                <mj-grid layout="masonry" min-col-width="12rem" gap="sm" class="notes">
                  <mj-surface elevation="raised"><b>Standup</b><p>Ship the dock fixes.</p></mj-surface>
                  <mj-surface elevation="raised"><b>Retro notes</b><p>Release went smoothly. The staging
                    environment was slow on Tuesday; the cache warm-up job now runs before tests. Next time
                    announce the freeze earlier.</p></mj-surface>
                  <mj-surface elevation="raised"><b>Idea</b><p>Dark-mode screenshots in the docs.</p></mj-surface>
                  <mj-surface elevation="raised"><b>Groceries</b><p>Coffee, oat milk, bread, apples,
                    lemons.</p></mj-surface>
                  <mj-surface elevation="raised"><b>Reading</b><p>The WAI-ARIA feed pattern.</p></mj-surface>
                  <mj-surface elevation="raised"><b>Travel</b><p>Train to Lyon on the 14th, 08:12 from Gare
                    de Lyon, coach 7.</p></mj-surface>
                  <mj-surface elevation="raised"><b>Reminder</b><p>Renew certificate.</p></mj-surface>
                </mj-grid>
            """),
            css=_code("""
                .notes { padding: var(--mj-space-4); background: var(--mj-bg-muted); }
                .notes p { margin: var(--mj-space-1) 0 0; }
            """),
        ),
        ComponentExample(
            key="events",
            title="Layout events",
            description=(
                "<p>The buttons set <code>columns</code>; each change, and each width preset, fires "
                "<code>mj-grid-layout</code> with the resulting column count (see Events; the script also "
                "logs it). The script switches to two columns on load.</p>"
            ),
            html=_code("""
                <mj-stack direction="horizontal" gap="sm" wrap class="bar">
                  <mj-button data-columns="auto" size="sm" variant="secondary">auto</mj-button>
                  <mj-button data-columns="2" size="sm" variant="secondary">2</mj-button>
                  <mj-button data-columns="3" size="sm" variant="secondary">3</mj-button>
                  <mj-button data-columns="6" size="sm" variant="secondary">6</mj-button>
                  <output id="column-readout" class="readout"></output>
                </mj-stack>
                <mj-grid id="demo-events-grid" min-col-width="8rem" gap="sm" class="tiles">
                  <div>1</div><div>2</div><div>3</div><div>4</div><div>5</div><div>6</div>
                </mj-grid>
            """),
            css=_code("""
                .bar { padding: var(--mj-space-4) var(--mj-space-4) 0; align-items: center; }
                .readout { color: var(--mj-text-muted); }
                .tiles { padding: var(--mj-space-4); }
                .tiles > div { padding: var(--mj-space-4); text-align: center; background: var(--mj-bg-muted); border-radius: var(--mj-radius-sm); }
            """),
            script=_code("""
                const grid = document.getElementById("demo-events-grid")
                const readout = document.getElementById("column-readout")
                grid.addEventListener("mj-grid-layout", (event) => {
                  readout.textContent = event.detail.columns + " columns"
                  mjSandbox.log("columns now", event.detail)
                })
                for (const button of document.querySelectorAll("[data-columns]")) {
                  button.addEventListener("click", () => grid.setAttribute("columns", button.dataset.columns))
                }
                grid.setAttribute("columns", "2")
            """),
        ),
    ],
    slots=[
        ("", "Grid cells: every element child is one cell.",
         "<div>New cell</div>"),
    ],
    properties=[
        ("masonrySupported", "boolean. Whether masonry is laid out natively; always false (multi-column is used)."),
    ],
    parts=[
        ("root", "The CSS grid (or multi-column box with layout=masonry)."),
    ],
    css_properties=[
        ("--mj-grid-template-columns", "Track list; written by `columns` (default repeat(auto-fill, minmax(min(var(--mj-grid-min-col), 100%), 1fr)))."),
        ("--mj-grid-min-col", "Minimum column width; written by `min-col-width` (default 16rem)."),
        ("--mj-grid-gap", "Gap; written by `gap` (default var(--mj-space-4))."),
        ("--mj-grid-col-gap", "Column gap; written by `col-gap` (default the gap)."),
        ("--mj-grid-row-gap", "Row gap; written by `row-gap` (default the gap)."),
        ("--mj-grid-align", "align-items; written by `align-items` (default stretch)."),
        ("--mj-grid-column-count", "Column count used by the masonry layout; written by `columns`."),
    ],
)


# ---------------------------------------------------------------------------
# mj-stack
# ---------------------------------------------------------------------------

STACK = ComponentDoc(
    tag="mj-stack",
    title="Stack",
    group="layout",
    summary="A one-dimensional flexbox primitive for vertical or horizontal stacks.",
    description=(
        "<p><code>&lt;mj-stack&gt;</code> arranges its children along one axis with a uniform gap: "
        "blocks stacked vertically (the default) or lined up horizontally, with optional wrapping, "
        "reversed order and main/cross-axis alignment. Use it inside cards, forms and toolbars, and "
        "nest stacks for rows inside columns.</p>"
        "<p>The host is a column flex container whose only item, the stack, grows to fill it. A stack "
        "with a fixed height, or one stretched by a grid, flex or dock parent, therefore has the full "
        "height available for <code>justify</code>, flexible <code>mj-spacer</code>s and "
        "<code>align</code>. Horizontal stacks follow the text direction (they mirror in RTL). A custom "
        "property is written only for attributes that are present.</p>"
        "<p>Every stack is laid out by its own attributes: a stack nested in a horizontal, centred "
        "stack is still a vertical, stretched stack with the default gap unless it says otherwise. "
        "The <code>--mj-stack-*</code> properties apply to the element they are set on and are not "
        "inherited by nested stacks.</p>"
    ),
    how_to_use=(
        "<p>Set <code>direction=\"horizontal\"</code> for a row; leave it out for a column. Pick a "
        "<code>gap</code> token. Use <code>align</code> (cross axis) and <code>justify</code> (main "
        "axis), add <code>wrap</code> so a row reflows on narrow screens, <code>reverse</code> to flip "
        "the visual order (DOM and tab order stay the same) and <code>inline</code> for an inline-flex "
        "host. Put an <code>&lt;mj-spacer&gt;</code> between children to push them apart. To restyle "
        "stacks from a stylesheet, set the <code>--mj-stack-*</code> properties on the stacks "
        "themselves (<code>.toolbar &gt; mj-stack { --mj-stack-gap: 2rem }</code>).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="direction", description="Main axis.", kind="enum",
                     values=["vertical", "horizontal"], default="vertical"),
        AttributeDoc(name="gap", description="Space between children.", kind="enum",
                     values=["none", "xs", "sm", "md", "lg", "xl"], default="md"),
        AttributeDoc(name="align", description="Cross-axis alignment (CSS align-items). Aligns the children only; the text inside keeps the alignment of the page.", kind="enum",
                     values=["stretch", "start", "center", "end", "baseline"], default="stretch"),
        AttributeDoc(name="justify", description="Main-axis distribution; needs free space (a fixed size or a stretched host) to show.",
                     kind="enum", values=["start", "center", "end", "between", "around", "evenly"], default="start"),
        AttributeDoc(name="wrap", description="Lets children wrap onto further lines.", kind="boolean"),
        AttributeDoc(name="reverse", description="Reverses the visual order on the main axis.", kind="boolean"),
        AttributeDoc(name="inline", description="Makes the host inline-flex instead of a block-level flex box.", kind="boolean"),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="Form column",
            description=(
                "<p>A vertical stack of form fields with a nested horizontal stack of actions. Use the "
                "controls on the outer stack: <code>gap</code>, <code>align=center</code>, "
                "<code>reverse</code>.</p>"
            ),
            html=_code("""
                <mj-stack class="demo-stack" gap="md">
                  <mj-text-field label="Project name" name="project" value="Atlas"></mj-text-field>
                  <mj-textarea label="Description" name="description" rows="3"></mj-textarea>
                  <mj-number-field label="Team size" name="size" min="1" max="50" value="6"></mj-number-field>
                  <mj-stack direction="horizontal" gap="sm" justify="end">
                    <mj-button variant="secondary">Cancel</mj-button>
                    <mj-button variant="primary">Create project</mj-button>
                  </mj-stack>
                </mj-stack>
            """),
            css=".demo-stack { max-inline-size: 26rem; margin: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="toolbar",
            title="Wrapping toolbar row",
            description=(
                "<p>A horizontal stack with <code>wrap</code> and <code>align=\"center\"</code>; a "
                "flexible <code>mj-spacer</code> pushes the last group to the end. At the <b>320</b> "
                "preset the row wraps instead of overflowing. Switch <b>Dir</b> to <b>RTL</b>: the order "
                "mirrors.</p>"
            ),
            html=_code("""
                <mj-stack direction="horizontal" gap="sm" align="center" wrap class="row">
                  <mj-search-input label="Search issues" placeholder="Search issues"></mj-search-input>
                  <mj-chip mode="selectable" selected>Open</mj-chip>
                  <mj-chip mode="selectable">Assigned to me</mj-chip>
                  <mj-spacer></mj-spacer>
                  <mj-button variant="secondary" size="sm">Export</mj-button>
                  <mj-button variant="primary" size="sm">New issue</mj-button>
                </mj-stack>
            """),
            css=".row { padding: var(--mj-space-3); margin: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }",
        ),
        ComponentExample(
            key="justify",
            title="Justify in a fixed height",
            description=(
                "<p>Three vertical stacks of the same fixed height with <code>justify</code> "
                "<code>start</code>, <code>between</code> and <code>end</code>, and a horizontal stack "
                "with <code>justify=\"evenly\"</code>. justify only shows when the stack has free space: "
                "here a height on the host, which the stack fills.</p>"
            ),
            html=_code("""
                <mj-grid columns="3" gap="sm" class="cols">
                  <mj-stack justify="start" gap="xs" class="tall"><b>start</b><span>One</span><span>Two</span></mj-stack>
                  <mj-stack justify="between" gap="xs" class="tall"><b>between</b><span>One</span><span>Two</span></mj-stack>
                  <mj-stack justify="end" gap="xs" class="tall"><b>end</b><span>One</span><span>Two</span></mj-stack>
                </mj-grid>
                <mj-stack direction="horizontal" justify="evenly" class="evenly">
                  <span>Draft</span><span>Review</span><span>Approved</span><span>Live</span>
                </mj-stack>
            """),
            css=_code("""
                .cols { padding: var(--mj-space-4); }
                .tall { block-size: 10rem; padding: var(--mj-space-2); background: var(--mj-bg-muted); border-radius: var(--mj-radius-sm); }
                .evenly { margin: 0 var(--mj-space-4) var(--mj-space-4); padding: var(--mj-space-2); border: 1px dashed var(--mj-border-strong); }
            """),
        ),
        ComponentExample(
            key="nested",
            title="Nested stacks and inline",
            description=(
                "<p>A settings list: an outer vertical stack of rows, each row a horizontal stack with "
                "<code>align=\"center\"</code> holding a text stack, a spacer and a control. The text "
                "stacks only set <code>gap=\"none\"</code>: they stay vertical and left-aligned inside "
                "the centred rows because a stack never inherits the layout of the stack around it. The "
                "last line uses <code>inline</code> stacks inside a sentence, and one row is "
                "<code>reverse</code>d.</p>"
            ),
            html=_code("""
                <mj-stack gap="none" class="settings">
                  <mj-stack direction="horizontal" align="center" gap="md" class="setting">
                    <mj-stack gap="none"><b>Two-factor authentication</b><small>Required for admins</small></mj-stack>
                    <mj-spacer></mj-spacer>
                    <mj-toggle-button pressed>On</mj-toggle-button>
                  </mj-stack>
                  <mj-stack direction="horizontal" align="center" gap="md" class="setting">
                    <mj-stack gap="none"><b>Session timeout</b><small>Sign out after inactivity</small></mj-stack>
                    <mj-spacer></mj-spacer>
                    <mj-number-field label="Minutes" min="5" max="120" value="30" class="narrow"></mj-number-field>
                  </mj-stack>
                  <mj-stack direction="horizontal" align="center" gap="md" reverse class="setting">
                    <mj-button size="sm" variant="secondary">Download</mj-button>
                    <mj-spacer></mj-spacer>
                    <mj-stack gap="none"><b>Audit log (reverse)</b><small>The button comes first in the DOM</small></mj-stack>
                  </mj-stack>
                </mj-stack>
                <p class="inline-demo">Status:
                  <mj-stack inline direction="horizontal" gap="xs" align="center"><mj-badge variant="status" status="online"></mj-badge> Online</mj-stack>
                  &middot; region
                  <mj-stack inline direction="horizontal" gap="xs"><b>eu-west-1</b></mj-stack>
                </p>
            """),
            css=_code("""
                .settings { margin: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .setting { padding: var(--mj-space-3) var(--mj-space-4); border-block-end: 1px solid var(--mj-border); }
                .setting:last-child { border-block-end: none; }
                .setting small { color: var(--mj-text-muted); }
                .narrow { inline-size: 8rem; }
                .inline-demo { margin: var(--mj-space-4); }
            """),
        ),
    ],
    slots=[
        ("", "The stacked children.", "<span>New item</span>"),
    ],
    properties=[
        ("childCount", "number. Number of element children assigned to the stack (read-only)."),
    ],
    parts=[
        ("root", "The flex container."),
    ],
    css_properties=[
        ("--mj-stack-direction", "flex-direction; written by `direction` / `reverse` (default column). Per element: not inherited by nested stacks."),
        ("--mj-stack-gap", "Gap; written by `gap` (default var(--mj-space-4)). Per element."),
        ("--mj-stack-align", "align-items; written by `align` (default stretch). Per element."),
        ("--mj-stack-justify", "justify-content; written by `justify` (default flex-start). Per element."),
        ("--mj-stack-wrap", "flex-wrap; written by `wrap` (default nowrap). Per element."),
    ],
)


# ---------------------------------------------------------------------------
# mj-spacer
# ---------------------------------------------------------------------------

SPACER = ComponentDoc(
    tag="mj-spacer",
    title="Spacer",
    group="layout",
    summary="A blank space that fills the free room in a flex container or occupies a fixed size.",
    description=(
        "<p><code>&lt;mj-spacer&gt;</code> is an empty, hidden-from-assistive-technology element for "
        "flex and grid containers. Without <code>size</code> it is flexible (<code>flex: 1 1 0</code>) "
        "and takes all free space on the main axis, pushing its siblings to opposite ends; several "
        "flexible spacers share the space equally. With <code>size</code> (a token or any CSS length) "
        "it is a fixed block that does not grow or shrink. <code>axis</code> limits the fixed size to "
        "the inline or the block dimension.</p>"
    ),
    how_to_use=(
        "<p>Drop <code>&lt;mj-spacer&gt;</code> between two children of an <code>&lt;mj-stack&gt;</code> "
        "(or any flex container) to push them apart; in a vertical stack with a height it pushes the "
        "following children to the bottom. Set <code>size</code> for a fixed gap in addition to the "
        "container's own gap. Weight flexible spacers with "
        "<code>mj-spacer { --mj-spacer-flex: 2 1 0 }</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="size", description="Token (xs-2xl) or a CSS length for a fixed spacer; omit for a flexible one.",
                     kind="string", values=["xs", "sm", "md", "lg", "xl", "2xl", "3rem", "48px"]),
        AttributeDoc(name="axis", description="Which dimension a fixed `size` applies to.", kind="enum",
                     values=["both", "horizontal", "vertical"], default="both"),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="Header with spacers",
            description=(
                "<p>An app header in a horizontal stack with <code>gap=\"none\"</code>, so only the "
                "spacers make room (they are drawn striped here). The flexible spacer pushes the account "
                "menu to the end; the fixed <code>size=\"md\"</code> spacers separate the links. Give the "
                "first spacer a <code>size</code> in Controls and it stops growing.</p>"
            ),
            html=_code("""
                <mj-stack class="demo-header" direction="horizontal" gap="none" align="center">
                  <strong class="brand">Acme Cloud</strong>
                  <mj-spacer></mj-spacer>
                  <a href="#docs">Docs</a>
                  <mj-spacer size="md"></mj-spacer>
                  <a href="#pricing">Pricing</a>
                  <mj-spacer size="md"></mj-spacer>
                  <mj-avatar name="Sam Lee" size="sm"></mj-avatar>
                </mj-stack>
            """),
            css=_code("""
                .demo-header {
                  margin: var(--mj-space-4);
                  padding: var(--mj-space-2) var(--mj-space-3);
                  background: var(--mj-bg-muted);
                  border-radius: var(--mj-radius-md);
                }
                .demo-header mj-spacer {
                  align-self: stretch;
                  background: repeating-linear-gradient(45deg, transparent 0 4px, var(--mj-border-strong) 4px 5px);
                }
            """),
        ),
        ComponentExample(
            key="vertical",
            title="Vertical spacers",
            description=(
                "<p>A fixed-height sidebar column: a flexible spacer pushes the account block to the "
                "bottom, and <code>size=\"xl\" axis=\"vertical\"</code> adds a fixed gap after the "
                "header.</p>"
            ),
            html=_code("""
                <mj-stack gap="xs" class="sidebar">
                  <strong>Workspace</strong>
                  <mj-spacer size="xl" axis="vertical"></mj-spacer>
                  <a href="#inbox">Inbox</a>
                  <a href="#projects">Projects</a>
                  <a href="#reports">Reports</a>
                  <mj-spacer></mj-spacer>
                  <mj-media-object align="center" gap="sm" media-size="auto">
                    <mj-avatar slot="media" name="Jo Park" size="sm"></mj-avatar>
                    Jo Park
                  </mj-media-object>
                </mj-stack>
            """),
            css=".sidebar { block-size: 18rem; inline-size: 14rem; margin: var(--mj-space-4); padding: var(--mj-space-3); background: var(--mj-bg-muted); border-radius: var(--mj-radius-md); }",
        ),
        ComponentExample(
            key="sizes",
            title="Sizes",
            description=(
                "<p>Every token and a CSS length, as fixed spacers between markers in rows with no gap. "
                "The last row has two flexible spacers, the second weighted with "
                "<code>--mj-spacer-flex: 3 1 0</code>.</p>"
            ),
            html=_code("""
                <div class="rows">
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer size="xs"></mj-spacer><i></i><code>xs</code></mj-stack>
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer size="sm"></mj-spacer><i></i><code>sm</code></mj-stack>
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer size="md"></mj-spacer><i></i><code>md</code></mj-stack>
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer size="lg"></mj-spacer><i></i><code>lg</code></mj-stack>
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer size="xl"></mj-spacer><i></i><code>xl</code></mj-stack>
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer size="2xl"></mj-spacer><i></i><code>2xl</code></mj-stack>
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer size="5rem"></mj-spacer><i></i><code>5rem</code></mj-stack>
                  <mj-stack direction="horizontal" gap="none" align="center"><i></i><mj-spacer></mj-spacer><i></i><mj-spacer class="heavy"></mj-spacer><i></i></mj-stack>
                </div>
            """),
            css=_code("""
                .rows { display: grid; gap: var(--mj-space-2); padding: var(--mj-space-4); }
                .rows i { inline-size: 0.75rem; block-size: 1.5rem; background: var(--mj-accent); border-radius: var(--mj-radius-sm); }
                .rows code { margin-inline-start: var(--mj-space-3); }
                .rows mj-spacer { block-size: 0.25rem; background: var(--mj-border-strong); }
                .heavy { --mj-spacer-flex: 3 1 0; }
            """),
        ),
    ],
    slots=[],
    properties=[
        ("flex", "boolean. True while the spacer is flexible (no `size`), read-only."),
    ],
    parts=[
        ("root", "The empty inner span."),
    ],
    css_properties=[
        ("--mj-spacer-flex", "flex shorthand of the host; written as `0 0 auto` while `size` is set (default 1 1 0)."),
        ("--mj-spacer-inline-size", "Inline size; written by `size` (default auto)."),
        ("--mj-spacer-block-size", "Block size; written by `size` (default auto)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-aspect-ratio
# ---------------------------------------------------------------------------

ASPECT_RATIO = ComponentDoc(
    tag="mj-aspect-ratio",
    title="Aspect Ratio Box",
    group="layout",
    summary="Keeps slotted content at a fixed width-to-height ratio to prevent layout shift.",
    description=(
        "<p><code>&lt;mj-aspect-ratio&gt;</code> reserves a box of a fixed ratio with the CSS "
        "<code>aspect-ratio</code> property and stretches <em>every</em> slotted child over it: an "
        "image, video, iframe, canvas or a plain container alike. The space is reserved before media "
        "loads, so nothing shifts. An empty box shows a muted background.</p>"
        "<p><code>ratio</code> accepts <code>16x9</code>, <code>16/9</code>, <code>16 / 9</code>, "
        "<code>16:9</code> or a single decimal such as <code>1.5</code>. A zero side is clamped to 1/1 "
        "and an unreadable value falls back to 16/9; both warn once in the console. "
        "<code>fit</code> and <code>position</code> (object-fit / object-position) apply to "
        "<code>img</code> and <code>video</code> only.</p>"
    ),
    how_to_use=(
        "<p>Give the box a width (it fills its container by default) and put the media between the "
        "tags. Use <code>fit=\"contain\"</code> for logos or diagrams that must not be cropped, and "
        "<code>position</code> to keep the important part of a cropped photo in view.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="ratio", description="Width / height as WxH, W/H, W:H or a decimal.", kind="string",
                     values=["16x9", "4x3", "1x1", "3x2", "9x16", "21 / 9", "16:9", "1.5"], default="16x9"),
        AttributeDoc(name="fit", description="object-fit of slotted img / video.", kind="enum",
                     values=["cover", "contain", "fill", "none", "scale-down"], default="cover"),
        AttributeDoc(name="position", description="object-position of slotted img / video (the focal point).", kind="string",
                     values=["center", "top", "bottom", "left", "right", "50% 20%"], default="center"),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A 4:3 photo in a 16x9 box, cropped with <code>fit=\"cover\"</code>. Change "
                "<code>ratio</code>, <code>fit</code> (try <code>contain</code>) and "
                "<code>position</code> (try <code>top</code>) in Controls.</p>"
            ),
            html=_code(f"""
                <mj-aspect-ratio class="demo-ratio" ratio="16x9" fit="cover">
                  <img src="{IMG_LAKE}" alt="Lake below rolling hills" />
                </mj-aspect-ratio>
            """),
            css=".demo-ratio { max-inline-size: 32rem; margin: var(--mj-space-4); border-radius: var(--mj-radius-md); }",
        ),
        ComponentExample(
            key="ratios",
            title="Ratios and non-media content",
            description=(
                "<p>Six spellings of a ratio, each box holding a plain <code>div</code> that is stretched "
                "over it. Try the <b>768</b> and <b>320</b> presets: the boxes keep their shape as the "
                "grid reflows.</p>"
            ),
            html=_code("""
                <mj-grid min-col-width="9rem" gap="sm" class="ratios" align-items="start">
                  <mj-aspect-ratio ratio="1x1"><div class="face">1x1</div></mj-aspect-ratio>
                  <mj-aspect-ratio ratio="4/3"><div class="face">4/3</div></mj-aspect-ratio>
                  <mj-aspect-ratio ratio="3:2"><div class="face">3:2</div></mj-aspect-ratio>
                  <mj-aspect-ratio ratio="16 / 9"><div class="face">16 / 9</div></mj-aspect-ratio>
                  <mj-aspect-ratio ratio="2.35"><div class="face">2.35</div></mj-aspect-ratio>
                  <mj-aspect-ratio ratio="9x16"><div class="face">9x16</div></mj-aspect-ratio>
                </mj-grid>
            """),
            css=_code("""
                .ratios { padding: var(--mj-space-4); }
                .face { display: grid; place-items: center; background: var(--mj-accent); color: var(--mj-text-on-accent); font-family: var(--mj-font-mono); }
            """),
        ),
        ComponentExample(
            key="fit",
            title="Fit and focal point",
            description=(
                "<p>The same tall picture (Top / Middle / Bottom bands) in square boxes: "
                "<code>cover</code> with <code>position</code> top, center and bottom, then "
                "<code>contain</code> (letterboxed) and <code>fill</code> (distorted).</p>"
            ),
            html=_code(f"""
                <mj-grid min-col-width="8rem" gap="sm" class="fits" align-items="start">
                  <figure><mj-aspect-ratio ratio="1x1" position="top"><img src="{IMG_TALL}" alt="Three bands" /></mj-aspect-ratio><figcaption>cover, top</figcaption></figure>
                  <figure><mj-aspect-ratio ratio="1x1"><img src="{IMG_TALL}" alt="Three bands" /></mj-aspect-ratio><figcaption>cover, center</figcaption></figure>
                  <figure><mj-aspect-ratio ratio="1x1" position="bottom"><img src="{IMG_TALL}" alt="Three bands" /></mj-aspect-ratio><figcaption>cover, bottom</figcaption></figure>
                  <figure><mj-aspect-ratio ratio="1x1" fit="contain"><img src="{IMG_TALL}" alt="Three bands" /></mj-aspect-ratio><figcaption>contain</figcaption></figure>
                  <figure><mj-aspect-ratio ratio="1x1" fit="fill"><img src="{IMG_TALL}" alt="Three bands" /></mj-aspect-ratio><figcaption>fill</figcaption></figure>
                </mj-grid>
            """),
            css=_code("""
                .fits { padding: var(--mj-space-4); }
                .fits figure { margin: 0; }
                .fits figcaption { margin-block-start: var(--mj-space-1); font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); text-align: center; }
            """),
        ),
        ComponentExample(
            key="embed",
            title="Canvas and embedded frame",
            description=(
                "<p>A <code>canvas</code> and an <code>iframe</code> (local <code>srcdoc</code>) are both "
                "stretched over their 21:9 / 4:3 boxes. The script redraws the canvas chart at the box "
                "size whenever it changes; try the <b>320</b> preset.</p>"
            ),
            html=_code("""
                <mj-aspect-ratio ratio="21/9" class="embed">
                  <canvas id="ratio-canvas" aria-label="Weekly visitors chart" role="img"></canvas>
                </mj-aspect-ratio>
                <mj-aspect-ratio ratio="4x3" class="embed small">
                  <iframe title="Embedded status page" srcdoc="&lt;body style='font:16px sans-serif;margin:0;display:grid;place-items:center;height:100vh;background:#e0f2fe'&gt;&lt;p&gt;All systems operational&lt;/p&gt;&lt;/body&gt;"></iframe>
                </mj-aspect-ratio>
            """),
            css=_code("""
                .embed { margin: var(--mj-space-4); border-radius: var(--mj-radius-md); }
                .small { max-inline-size: 18rem; }
            """),
            script=_code("""
                const canvas = document.getElementById("ratio-canvas")
                const values = [32, 41, 38, 55, 61, 48, 70]
                function draw() {
                  const width = canvas.clientWidth
                  const height = canvas.clientHeight
                  canvas.width = width
                  canvas.height = height
                  const context = canvas.getContext("2d")
                  const style = getComputedStyle(document.documentElement)
                  context.fillStyle = style.getPropertyValue("--mj-accent").trim() || "#4f46e5"
                  const step = width / values.length
                  values.forEach((value, index) => {
                    const barHeight = (value / 80) * (height - 16)
                    context.fillRect(index * step + 8, height - barHeight, step - 16, barHeight)
                  })
                }
                new ResizeObserver(draw).observe(canvas)
                draw()
            """),
        ),
    ],
    slots=[
        ("", "The content to constrain; every child is stretched over the box.",
         f'<img src="{IMG_COAST}" alt="Coast road" />'),
    ],
    properties=[
        ("resolvedRatio", "string. The CSS aspect-ratio value in effect, e.g. `16/9` (read-only)."),
    ],
    parts=[
        ("inner", "The absolutely positioned box the slot fills (also exposed as `root`)."),
        ("root", "Alias of `inner`."),
    ],
    css_properties=[
        ("--mj-ar-ratio", "aspect-ratio; written by `ratio` (default 16/9)."),
        ("--mj-ar-fit", "object-fit of img / video; written by `fit` (default cover)."),
        ("--mj-ar-position", "object-position of img / video; written by `position` (default center)."),
        ("--mj-ar-bg", "Background shown while the box is empty or letterboxed (default var(--mj-bg-muted))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-accordion
# ---------------------------------------------------------------------------

ACCORDION = ComponentDoc(
    tag="mj-accordion",
    title="Accordion",
    group="layout",
    summary="Groups disclosure panels and coordinates their open state.",
    description=(
        "<p><code>&lt;mj-accordion&gt;</code> wraps <code>&lt;mj-disclosure&gt;</code> panels and "
        "manages which ones are open. Only <em>direct</em> mj-disclosure children are panels; a "
        "disclosure or accordion nested inside a panel is independent. By default one panel is open at "
        "a time: opening a panel (by click, by script or with the <code>open</code> attribute) closes "
        "the others, and when several are marked open in the markup the first wins. "
        "<code>allow-multiple</code> lifts the rule. A toggle cancelled by a "
        "<code>mj-disclosure-toggle</code> listener closes nothing.</p>"
        "<p>Each panel trigger is a level-3 heading (the panel's <code>heading-level</code> "
        "overrides it). Arrow Up / Down move focus between the panel headers and wrap, Home / End jump "
        "to the first / last; the keys are handled only while a header has focus, so text fields, "
        "sliders and nested accordions inside a panel keep their own keys. Disabled panels are "
        "skipped.</p>"
        "<p><code>disabled</code> disables every panel trigger (panels that were disabled on their own "
        "stay so when it is removed); the content of open panels stays readable and clickable. "
        "<code>bordered</code> draws one border around the group; <code>flush</code> removes the outer "
        "border, radius, gaps and the inline padding of the panels so the accordion lines up with "
        "surrounding text.</p>"
    ),
    how_to_use=(
        "<p>Nest <code>&lt;mj-disclosure heading=\"...\"&gt;</code> children directly inside "
        "<code>&lt;mj-accordion&gt;</code>; mark one <code>open</code> to start with it expanded. Put "
        "any content in a panel, including form controls. Listen for <code>mj-accordion-open</code> / "
        "<code>mj-accordion-close</code> (detail <code>{ panel, index }</code>) to react to panel "
        "changes; the panels' own <code>mj-disclosure-*</code> events bubble through as well.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="allow-multiple", description="Lets any number of panels be open at once.", kind="boolean"),
        AttributeDoc(name="bordered", description="One shared border around all panels.", kind="boolean"),
        AttributeDoc(name="flush", description="No outer border, radius, gaps or inline panel padding.", kind="boolean"),
        AttributeDoc(name="disabled", description="Disables every panel trigger; open content stays usable.", kind="boolean"),
    ],
    events=[
        ("mj-accordion-open", "A direct panel finished opening.", "{ panel: MjDisclosure, index: number }"),
        ("mj-accordion-close", "A direct panel finished closing (by the user, script or the single-open rule).",
         "{ panel: MjDisclosure, index: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="FAQ",
            description=(
                "<p>A bordered FAQ with the last panel open. Open another panel and the open one closes. "
                "Focus a header and use Arrow Up / Down, Home and End. Toggle "
                "<code>allow-multiple</code>, <code>flush</code> or <code>disabled</code> in Controls.</p>"
            ),
            html=_code("""
                <mj-accordion class="demo-accordion" bordered>
                  <mj-disclosure heading="What does the Team plan include?">
                    <p>Unlimited projects, 50 GB of storage per member, single sign-on and priority support
                      with a four-hour response time on business days.</p>
                  </mj-disclosure>
                  <mj-disclosure heading="Can I change plans later?">
                    <p>Yes. Upgrades apply immediately and are prorated; downgrades take effect at the end of
                      the billing period.</p>
                  </mj-disclosure>
                  <mj-disclosure heading="How do refunds work?" open>
                    <p>Annual plans can be refunded in full within 30 days. After that, unused months are
                      credited to your account.</p>
                  </mj-disclosure>
                </mj-accordion>
            """),
            css=".demo-accordion { max-inline-size: 36rem; margin: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="form",
            title="Form in panels",
            description=(
                "<p>A settings form split into panels (<code>allow-multiple</code>) with text fields, a "
                "select, a slider, a radio group and a nested <code>mj-disclosure</code> for advanced "
                "options. Type in a field and press Arrow keys: they move the caret, not the focus. "
                "<b>Save</b> logs the submitted form data, including fields in closed panels. Try the "
                "<b>320</b> preset: the two-column field grid stacks.</p>"
            ),
            html=_code("""
                <form id="profile-form" class="settings-form">
                  <mj-accordion allow-multiple bordered>
                    <mj-disclosure heading="Profile" open>
                      <mj-grid columns="2" min-col-width="12rem" gap="sm">
                        <mj-text-field label="Display name" name="name" value="Ada Lovelace" required></mj-text-field>
                        <mj-text-field label="Email" name="email" type="email" value="ada@example.com"></mj-text-field>
                        <label class="field">Language
                          <mj-select name="language" value="en">
                            <mj-option value="en">English</mj-option>
                            <mj-option value="fr">Fran&ccedil;ais</mj-option>
                            <mj-option value="ar">&#1575;&#1604;&#1593;&#1585;&#1576;&#1610;&#1577;</mj-option>
                          </mj-select>
                        </label>
                        <mj-text-field label="Time zone" name="tz" value="Europe/London"></mj-text-field>
                      </mj-grid>
                    </mj-disclosure>
                    <mj-disclosure heading="Notifications">
                      <mj-radio-group name="digest" value="daily">
                        <span slot="label">Email digest</span>
                        <mj-radio value="off">Off</mj-radio>
                        <mj-radio value="daily">Daily</mj-radio>
                        <mj-radio value="weekly">Weekly</mj-radio>
                      </mj-radio-group>
                      <mj-slider label="Quiet hours start" name="quiet" min="18" max="24" value="22" show-value-label></mj-slider>
                      <mj-disclosure heading="Advanced" indicator-position="start" class="nested">
                        <mj-checkbox-group name="advanced" value="mentions">
                          <span slot="label">Also notify me about</span>
                          <mj-checkbox value="mentions">Mentions in code review</mj-checkbox>
                          <mj-checkbox value="deploys">Deployments I started</mj-checkbox>
                        </mj-checkbox-group>
                      </mj-disclosure>
                    </mj-disclosure>
                    <mj-disclosure heading="Danger zone">
                      <p>Deleting your account removes all personal projects.</p>
                      <mj-button variant="secondary" size="sm">Delete account</mj-button>
                    </mj-disclosure>
                  </mj-accordion>
                  <mj-button type="submit" variant="primary" class="save">Save</mj-button>
                </form>
            """),
            css=_code("""
                .settings-form { max-inline-size: 40rem; margin: var(--mj-space-4); }
                .settings-form mj-radio-group, .settings-form mj-slider { margin-block-end: var(--mj-space-4); }
                .nested { border: 1px solid var(--mj-border); border-radius: var(--mj-radius-sm); }
                .field { display: grid; gap: var(--mj-space-1); font-size: var(--mj-font-size-sm); }
                .save { margin-block-start: var(--mj-space-4); }
            """),
            script=_code("""
                const form = document.getElementById("profile-form")
                form.addEventListener("submit", (event) => {
                  event.preventDefault()
                  mjSandbox.log("submitted", Object.fromEntries(new FormData(form)))
                })
            """),
        ),
        ComponentExample(
            key="flush",
            title="Flush, inside a card",
            description=(
                "<p>A <code>flush</code> accordion inside an <code>mj-card</code>: no outer border and no "
                "inline padding, so the headers line up with the card text. Switch <b>Dir</b> to "
                "<b>RTL</b>: the chevrons move to the left.</p>"
            ),
            html=_code("""
                <mj-card heading="Order #10482" subheading="Shipped 12 March" elevation="outlined" class="order">
                  <mj-accordion flush>
                    <mj-disclosure heading="Items (3)" open>
                      <mj-stack gap="xs">
                        <span>Trail running shoes &times; 1</span>
                        <span>Merino socks &times; 2</span>
                      </mj-stack>
                    </mj-disclosure>
                    <mj-disclosure heading="Delivery address">
                      <p>12 Harbour Street, Leith, Edinburgh EH6 6QW</p>
                    </mj-disclosure>
                    <mj-disclosure heading="Payment">
                      <p>Visa ending 4242, charged &pound;148.00</p>
                    </mj-disclosure>
                  </mj-accordion>
                </mj-card>
            """),
            css=".order { max-inline-size: 26rem; margin: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="disabled",
            title="Disabled",
            description=(
                "<p>The first accordion is <code>disabled</code>: the headers do not toggle, but the open "
                "panel's link and button still work. In the second, only the middle panel carries its own "
                "<code>disabled</code>; arrow-key navigation skips it.</p>"
            ),
            html=_code("""
                <mj-accordion disabled bordered class="block">
                  <mj-disclosure heading="Billing (locked by your administrator)" open>
                    <p>Contact <a href="#admin">your administrator</a> to change billing details.</p>
                    <mj-button size="sm" variant="secondary">Download invoice</mj-button>
                  </mj-disclosure>
                  <mj-disclosure heading="Tax information"><p>VAT number GB123456789.</p></mj-disclosure>
                </mj-accordion>
                <mj-accordion bordered class="block">
                  <mj-disclosure heading="Step 1: Connect repository" open><p>Connected to github.com/acme/atlas.</p></mj-disclosure>
                  <mj-disclosure heading="Step 2: Configure build (waiting for step 1)" disabled><p>Build settings.</p></mj-disclosure>
                  <mj-disclosure heading="Step 3: Invite team"><p>Invite people by email.</p></mj-disclosure>
                </mj-accordion>
            """),
            css=".block { max-inline-size: 34rem; margin: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="events",
            title="Events and script control",
            description=(
                "<p>The script opens panel 2 and then panel 3 by setting their <code>open</code> "
                "property; Events shows <code>mj-accordion-open</code> for each and "
                "<code>mj-accordion-close</code> for the panels the single-open rule closed. The buttons "
                "drive the panels through the <code>panels</code> property.</p>"
            ),
            html=_code("""
                <mj-stack direction="horizontal" gap="sm" class="bar">
                  <mj-button id="open-first" size="sm" variant="secondary">Open first</mj-button>
                  <mj-button id="open-last" size="sm" variant="secondary">Open last</mj-button>
                  <mj-button id="close-all" size="sm" variant="secondary">Close all</mj-button>
                </mj-stack>
                <mj-accordion id="demo-events-accordion" bordered class="block">
                  <mj-disclosure heading="Overview" open><p>Project health at a glance.</p></mj-disclosure>
                  <mj-disclosure heading="Milestones"><p>Beta on 1 May, general availability on 1 July.</p></mj-disclosure>
                  <mj-disclosure heading="Risks"><p>Two open risks; both have owners.</p></mj-disclosure>
                </mj-accordion>
            """),
            css=_code("""
                .bar { margin: var(--mj-space-4) var(--mj-space-4) 0; }
                .block { max-inline-size: 34rem; margin: var(--mj-space-4); }
            """),
            script=_code("""
                const accordion = document.getElementById("demo-events-accordion")
                accordion.addEventListener("mj-accordion-open", (event) => mjSandbox.log("opened panel", { index: event.detail.index }))
                accordion.addEventListener("mj-accordion-close", (event) => mjSandbox.log("closed panel", { index: event.detail.index }))
                document.getElementById("open-first").addEventListener("click", () => { accordion.panels[0].open = true })
                document.getElementById("open-last").addEventListener("click", () => { accordion.panels[accordion.panels.length - 1].open = true })
                document.getElementById("close-all").addEventListener("click", () => {
                  for (const panel of accordion.openPanels) { panel.open = false }
                })
                const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
                accordion.panels[1].open = true
                await wait(600)
                accordion.panels[2].open = true
            """),
        ),
    ],
    slots=[
        ("", "The panels: direct mj-disclosure children.",
         '<mj-disclosure heading="Added panel"><p>Content of the added panel.</p></mj-disclosure>'),
    ],
    properties=[
        ("panels", "MjDisclosure[]. The direct mj-disclosure children, in order (read-only)."),
        ("openPanels", "MjDisclosure[]. The panels that are currently open (read-only)."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    parts=[
        ("root", "The container of the panels (carries the border with `bordered`)."),
    ],
    css_properties=[
        ("--mj-accordion-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-accordion-border", "Border colour with `bordered` (default var(--mj-border))."),
        ("--mj-accordion-gap", "Gap between panels when not bordered (default 0)."),
        ("--mj-disclosure-trigger-padding", "Set by `flush` on the panels (var(--mj-space-3) 0); can be set on the accordion for all panels."),
        ("--mj-disclosure-panel-padding", "Set by `flush` on the panels (var(--mj-space-4) 0); can be set on the accordion for all panels."),
    ],
)


# ---------------------------------------------------------------------------
# mj-disclosure
# ---------------------------------------------------------------------------

DISCLOSURE = ComponentDoc(
    tag="mj-disclosure",
    title="Disclosure",
    group="layout",
    summary="A single show/hide region with a trigger button and an animated panel.",
    description=(
        "<p><code>&lt;mj-disclosure&gt;</code> implements the ARIA disclosure pattern: a button with "
        "<code>aria-expanded</code> / <code>aria-controls</code> and a labelled region. The "
        "<code>open</code> attribute is the state. Opening and closing animate the panel height (unless "
        "<code>animated=\"false\"</code> or the user prefers reduced motion); a change during the "
        "animation reverses it from the height reached. A closed panel is <code>display: none</code>, "
        "so its content is neither focusable nor read.</p>"
        "<p>The trigger label is the <code>heading</code> attribute or rich content in "
        "<code>slot=\"summary\"</code> (the slot wins). <code>heading-level</code> (1-6) wraps the "
        "trigger in a heading (<code>role=heading</code> + <code>aria-level</code>); a disclosure that "
        "is a panel of an <code>mj-accordion</code> is a level-3 heading unless it sets its own.</p>"
        "<p>A click fires the cancelable <code>mj-disclosure-toggle</code> first; only "
        "<code>event.preventDefault()</code> vetoes the change (returning false from a listener does "
        "not). <code>mj-disclosure-open</code> / <code>-close</code> follow when the panel has finished "
        "animating, also for changes made by script. <code>disabled</code> blocks the trigger only: "
        "the content of an open panel stays usable.</p>"
    ),
    how_to_use=(
        "<p>Set <code>heading</code> for the trigger text, or slot rich content into "
        "<code>slot=\"summary\"</code>. Put the body in the default slot and add <code>open</code> to "
        "start expanded. Toggle from script with the <code>open</code> property. Use "
        "<code>indicator-position=\"start\"</code> to put the chevron before the label (tree-like "
        "lists). Group several disclosures in an <code>&lt;mj-accordion&gt;</code> for single-open "
        "behaviour and arrow-key navigation.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="heading", description="Trigger text when no `summary` slot content is given.", kind="string"),
        AttributeDoc(name="open", description="Expanded state; toggled by the trigger.", kind="boolean"),
        AttributeDoc(name="disabled", description="Blocks the trigger (aria-disabled, not focusable); open content stays usable.",
                     kind="boolean"),
        AttributeDoc(name="animated", description="`false` switches the height animation off.", kind="boolean", default="true"),
        AttributeDoc(name="indicator-position", description="Side of the chevron.", kind="enum",
                     values=["end", "start"], default="end"),
        AttributeDoc(name="heading-level", description="Wraps the trigger in a heading of this level; inside mj-accordion the default is 3.",
                     kind="enum", values=["1", "2", "3", "4", "5", "6"]),
    ],
    events=[
        ("mj-disclosure-toggle", "Cancelable; fires on a trigger click before the state changes. preventDefault() vetoes it.",
         "{ open: boolean }"),
        ("mj-disclosure-open", "The panel finished opening (click or script).", "{}"),
        ("mj-disclosure-close", "The panel finished closing (click or script).", "{}"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Two independent disclosures; the first starts open. Toggle <code>open</code>, "
                "<code>animated</code> and <code>indicator-position</code> on the first one in "
                "Controls.</p>"
            ),
            html=_code("""
                <div class="demo-disclosures">
                  <mj-disclosure heading="What is included in the trial?" open>
                    <p>All features of the Team plan for 14 days, with up to five members. No card required.</p>
                  </mj-disclosure>
                  <mj-disclosure heading="What happens when the trial ends?">
                    <p>Your projects become read-only until you choose a plan. Nothing is deleted.</p>
                  </mj-disclosure>
                </div>
            """),
            css=".demo-disclosures { max-inline-size: 34rem; margin: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="slots",
            title="Rich summary",
            description=(
                "<p>The <code>summary</code> slot holds an icon, a title, a status chip and a count; "
                "<code>indicator-position=\"start\"</code> puts the chevron first and "
                "<code>heading-level=\"3\"</code> exposes the trigger as a heading. Switch the summary "
                "slot off in Slots to fall back to the <code>heading</code> attribute.</p>"
            ),
            html=_code("""
                <mj-disclosure heading="Build #2481" indicator-position="start" heading-level="3" open class="build">
                  <span slot="summary" class="summary">
                    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="currentColor"/></svg>
                    <span class="title">Build #2481 &middot; main</span>
                    <mj-chip>Failed</mj-chip>
                    <small>2 of 312 checks</small>
                  </span>
                  <ul class="checks">
                    <li><b>test_dock_layout</b> &mdash; expected 240, got 238</li>
                    <li><b>lint</b> &mdash; unused import in rendering.py</li>
                  </ul>
                  <mj-button size="sm" variant="secondary">Re-run failed checks</mj-button>
                </mj-disclosure>
            """),
            css=_code("""
                .build { max-inline-size: 36rem; margin: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .summary { display: flex; flex-wrap: wrap; align-items: center; gap: var(--mj-space-2); }
                .summary svg { color: var(--mj-color-danger); }
                .summary small { color: var(--mj-text-muted); }
                .checks { margin-block-start: 0; }
            """),
        ),
        ComponentExample(
            key="nested",
            title="Nested disclosures",
            description=(
                "<p>A file-browser style outline: disclosures nested three deep with the chevron at the "
                "start, a form control inside, and <code>animated=\"false\"</code> on the innermost one. "
                "Collapsed levels take their content out of the tab order.</p>"
            ),
            html=_code("""
                <div class="outline">
                  <mj-disclosure heading="src" indicator-position="start" open>
                    <mj-disclosure heading="components" indicator-position="start" open>
                      <mj-disclosure heading="layout (animated=false)" indicator-position="start" animated="false">
                        <p>mjdocklayout.js, mjsplitpane.js, mjgrid.js</p>
                      </mj-disclosure>
                      <mj-disclosure heading="forms" indicator-position="start">
                        <mj-text-field label="Filter files" placeholder="e.g. textfield"></mj-text-field>
                      </mj-disclosure>
                    </mj-disclosure>
                    <mj-disclosure heading="core" indicator-position="start"><p>mjelement.js, anchoring.js</p></mj-disclosure>
                  </mj-disclosure>
                </div>
            """),
            css=_code("""
                .outline { max-inline-size: 30rem; margin: var(--mj-space-4); --mj-disclosure-panel-padding: 0 0 0 var(--mj-space-5); }
                .outline p { margin: var(--mj-space-2) var(--mj-space-4); }
                .outline mj-text-field { margin: var(--mj-space-2) var(--mj-space-4); }
            """),
        ),
        ComponentExample(
            key="events",
            title="Vetoing a toggle",
            description=(
                "<p>The terms panel cannot be closed until the checkbox is checked: the script calls "
                "<code>preventDefault()</code> on <code>mj-disclosure-toggle</code>. The second panel is "
                "opened by script after load (<code>open = true</code>), which fires "
                "<code>mj-disclosure-open</code> without a toggle event. Watch Events.</p>"
            ),
            html=_code("""
                <div class="events-demo">
                  <mj-disclosure id="terms" heading="Terms of service (read before closing)" open>
                    <p>By creating an account you agree to the acceptable use policy and the data
                      processing terms.</p>
                    <label><input type="checkbox" id="terms-read"> I have read the terms</label>
                  </mj-disclosure>
                  <mj-disclosure id="privacy" heading="Privacy summary">
                    <p>We store your email and the projects you create; nothing is sold to third parties.</p>
                  </mj-disclosure>
                </div>
            """),
            css=".events-demo { max-inline-size: 34rem; margin: var(--mj-space-4); }",
            script=_code("""
                const terms = document.getElementById("terms")
                const read = document.getElementById("terms-read")
                terms.addEventListener("mj-disclosure-toggle", (event) => {
                  if (event.detail.open === false && read.checked === false) {
                    event.preventDefault()
                    mjSandbox.log("toggle vetoed", { reason: "terms not read" })
                  }
                })
                setTimeout(() => { document.getElementById("privacy").open = true }, 400)
            """),
        ),
        ComponentExample(
            key="disabled",
            title="Disabled",
            description=(
                "<p>A disabled, open disclosure: the trigger is dimmed and does not toggle, but the link "
                "and button in the panel still work. The second one is disabled and closed.</p>"
            ),
            html=_code("""
                <div class="disabled-demo">
                  <mj-disclosure heading="Billing (managed by your organisation)" open disabled>
                    <p>Billing is handled by <a href="#org">Acme Corp</a>.</p>
                    <mj-button size="sm" variant="secondary">Request change</mj-button>
                  </mj-disclosure>
                  <mj-disclosure heading="API keys (requires owner role)" disabled>
                    <p>Hidden.</p>
                  </mj-disclosure>
                </div>
            """),
            css=".disabled-demo { max-inline-size: 34rem; margin: var(--mj-space-4); }",
        ),
    ],
    slots=[
        ("", "Panel content.", "<p>Panel content supplied by the slot inspector.</p>"),
        ("summary", "Rich trigger label; replaces the `heading` text.",
         "<span><b>Rich summary</b> <small>with extra text</small></span>"),
    ],
    properties=[
        ("open", "boolean. Reflects `open`; setting it opens or closes (fires open/close, not toggle)."),
        ("disabled", "boolean. Reflects `disabled`."),
        ("panelElement", "HTMLElement. The panel region in the shadow root (read-only)."),
        ("triggerElement", "HTMLButtonElement. The trigger button (read-only)."),
    ],
    methods=[
        ("focus(options)", "Moves focus to the trigger button."),
    ],
    parts=[
        ("trigger", "The trigger button."),
        ("indicator", "The chevron icon."),
        ("panel", "The collapsible region."),
    ],
    css_properties=[
        ("--mj-disclosure-trigger-padding", "Trigger padding (default var(--mj-space-3) var(--mj-space-4))."),
        ("--mj-disclosure-trigger-bg", "Trigger background (default transparent)."),
        ("--mj-disclosure-trigger-color", "Trigger text colour (default var(--mj-text))."),
        ("--mj-disclosure-border", "Line under the trigger (default var(--mj-border))."),
        ("--mj-disclosure-indicator-size", "Chevron size (default 1.25rem)."),
        ("--mj-disclosure-duration", "Height animation duration (default var(--mj-motion-medium))."),
        ("--mj-disclosure-panel-padding", "Panel padding (default var(--mj-space-4))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-split-pane
# ---------------------------------------------------------------------------

SPLIT_PANE = ComponentDoc(
    tag="mj-split-pane",
    title="Split Pane",
    group="layout",
    summary="Divides a container into two resizable panes separated by a draggable, keyboard-operable separator.",
    description=(
        "<p><code>&lt;mj-split-pane&gt;</code> renders a start pane and an end pane separated by an "
        "ARIA <code>separator</code> (focusable, with <code>aria-valuenow</code> / min / max in pixels "
        "of the start pane). The host fills its container (<code>block-size: 100%</code>), so give it "
        "or its parent a height. Each pane scrolls on its own.</p>"
        "<p>Until the user resizes it the start pane has the <code>initial-size</code> (any CSS length "
        "or percentage, default 50%). Once resized (drag, keyboard or the <code>size</code> property) "
        "the split is kept as a <em>ratio</em> and re-applied when the container changes size, so the "
        "panes stay in proportion and the separator never leaves the view. <code>min</code> and "
        "<code>max</code> bound the start pane (px, %, rem or em; default min 80px, which also protects "
        "the end pane when no max is set); when the container is too small for both the panes meet in "
        "the middle.</p>"
        "<p>Keyboard on the separator: Arrow keys move it by 8px (Left/Right follow the text direction; "
        "Up/Down for vertical splits), Home / End jump to min / max, Enter collapses or restores "
        "(Shift+Enter collapses the end pane with <code>collapsible=\"both\"</code>); double-click does "
        "the same with the pointer. A collapsed pane gets size 0 and is hidden, the host reflects "
        "<code>collapsed=\"start|end\"</code>, and expanding returns to the previous split.</p>"
        "<p><code>persist-key</code> stores <code>{ ratio, collapsed }</code> as JSON in "
        "localStorage after every settled resize and restores it on load (an older pixel value is "
        "still read). <code>disabled</code> locks the separator only; both panes stay interactive.</p>"
    ),
    how_to_use=(
        "<p>Put the primary region in <code>slot=\"start\"</code> and the secondary one in "
        "<code>slot=\"end\"</code>, and give the split a height (or put it in a dock layout fill, a "
        "grid row or a flex column). Slotted panes are not stretched by default: give them "
        "<code>min-block-size: 100%</code> when their background must fill the pane. Nest split panes "
        "for three or more regions. Listen for <code>mj-split-resize-end</code> to save sizes "
        "yourself, or set <code>persist-key</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="orientation", description="`horizontal`: side by side; `vertical`: top / bottom.", kind="enum",
                     values=["horizontal", "vertical"], default="horizontal"),
        AttributeDoc(name="initial-size", description="Start pane size before the first resize (CSS length or %). Changing it resets the split.",
                     kind="string", values=["30%", "50%", "240px", "16rem"], default="50%"),
        AttributeDoc(name="min", description="Minimum start pane size (px, %, rem, em).", kind="string",
                     values=["80px", "20%", "10rem"], default="80px"),
        AttributeDoc(name="max", description="Maximum start pane size (px, %, rem, em); default leaves `min` for the end pane.",
                     kind="string", values=["80%", "400px", "30rem"]),
        AttributeDoc(name="collapsible", description="Which pane Enter / double-click collapses.", kind="enum",
                     values=["none", "start", "end", "both"], default="none"),
        AttributeDoc(name="disabled", description="Locks the separator; the panes stay interactive.", kind="boolean"),
        AttributeDoc(name="persist-key", description="localStorage key for the settled { ratio, collapsed } state.", kind="string",
                     values=["layout.sidebar"]),
        AttributeDoc(name="separator-label", description="Accessible name of the separator.", kind="string", default="Resize"),
    ],
    events=[
        ("mj-split-resize", "While dragging, after each move that changed the size.", "{ size: number, ratio: number }"),
        ("mj-split-resize-end", "A drag, key press, collapse/expand or size change settled.", "{ size: number, ratio: number }"),
        ("mj-split-collapse", "A pane was collapsed.", "{ pane: 'start' | 'end' }"),
        ("mj-split-expand", "A collapsed pane was restored (by expand(), Enter, double-click or a resize).", "{ pane: 'start' | 'end' }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="File explorer",
            description=(
                "<p>A tree in the start pane (30%, <code>collapsible=\"start\"</code>) and a document in "
                "the end pane; both scroll on their own. Drag the separator, or focus it and use the "
                "Arrow keys, Home / End, and Enter to collapse. Try the <b>320</b> preset: the split keeps "
                "its ratio and <code>min</code> protects both panes. Switch <b>Dir</b> to <b>RTL</b>: the "
                "tree moves to the right and Arrow keys follow.</p>"
            ),
            html=_code("""
                <mj-split-pane class="demo-split" initial-size="30%" min="8rem" collapsible="start" separator-label="Resize file tree">
                  <mj-tree-nav slot="start" nav-label="Project files" current="#render" class="pane">
                    <li><a href="#src">src</a>
                      <ul>
                        <li><a href="#app">app.py</a></li>
                        <li><a href="#render">rendering.py</a></li>
                        <li><a href="#catalog">catalog</a></li>
                      </ul>
                    </li>
                    <li><a href="#tests">tests</a></li>
                    <li><a href="#readme">README.md</a></li>
                  </mj-tree-nav>
                  <article slot="end" class="pane doc">
                    <h3>rendering.py</h3>
                    <p>Builds the component pages: the example gallery, the attribute controls, the event log
                      and the reference tables.</p>
                    <pre>def render_component_page(doc):
                    sections = [gallery(doc), controls(doc)]
                    return join(sections)</pre>
                    <p>Every example runs in its own preview frame with the component library loaded.</p>
                  </article>
                </mj-split-pane>
            """),
            css=_code("""
                .demo-split { block-size: 20rem; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .demo-split .pane { box-sizing: border-box; min-block-size: 100%; padding: var(--mj-space-3); }
                .demo-split mj-tree-nav { background: var(--mj-bg-muted); }
                .doc h3 { margin-block-start: 0; }
                .doc pre { overflow-x: auto; padding: var(--mj-space-2); background: var(--mj-bg-muted); border-radius: var(--mj-radius-sm); }
            """),
        ),
        ComponentExample(
            key="nested",
            title="Three panes (nested)",
            description=(
                "<p>An editor workbench: a horizontal split whose end pane is a vertical split (editor "
                "over terminal). Each separator works on its own. Try <b>768</b> and <b>320</b>: the "
                "panes keep their proportions; the vertical split's <code>min=\"20%\"</code> / "
                "<code>max=\"80%\"</code> hold.</p>"
            ),
            html=_code("""
                <mj-split-pane initial-size="14rem" min="10rem" max="50%" class="workbench">
                  <nav slot="start" class="pane side" aria-label="Outline">
                    <strong>Outline</strong>
                    <ol><li>Imports</li><li>STYLES</li><li>class MjSplitPane</li><li>render()</li><li>_applyLayout()</li></ol>
                  </nav>
                  <mj-split-pane slot="end" orientation="vertical" initial-size="65%" min="20%" max="80%" separator-label="Resize terminal">
                    <div slot="start" class="pane editor">
                      <mj-tabs>
                        <button slot="tab">mjsplitpane.js</button>
                        <button slot="tab">mjdocklayout.js</button>
                        <div><pre>_applyLayout() {
                  const total = this._totalSize()
                  const limits = this._limits(total)
                }</pre></div>
                        <div><pre>requestLayout() { ... }</pre></div>
                      </mj-tabs>
                    </div>
                    <div slot="end" class="pane terminal" role="log" aria-label="Terminal">
                      <code>$ npm test</code><br><code>312 passed, 0 failed (6.1 s)</code>
                    </div>
                  </mj-split-pane>
                </mj-split-pane>
            """),
            css=_code("""
                .workbench { block-size: 26rem; border: 1px solid var(--mj-border); }
                .workbench .pane { box-sizing: border-box; min-block-size: 100%; padding: var(--mj-space-3); }
                .side { background: var(--mj-bg-muted); }
                .side ol { padding-inline-start: var(--mj-space-5); }
                .terminal { background: var(--mj-color-neutral-900); color: var(--mj-color-neutral-100); font-family: var(--mj-font-mono); }
            """),
        ),
        ComponentExample(
            key="vertical",
            title="Vertical with limits",
            description=(
                "<p><code>orientation=\"vertical\"</code> with <code>min=\"25%\"</code> and "
                "<code>max=\"75%\"</code>: a mail list over the reading pane. Arrow Up / Down move the "
                "separator; Home / End jump to the limits.</p>"
            ),
            html=_code("""
                <mj-split-pane orientation="vertical" initial-size="40%" min="25%" max="75%" class="mail">
                  <mj-scroll-area slot="start" aria-label="Messages" class="fill">
                    <mj-list id="mail-list"></mj-list>
                  </mj-scroll-area>
                  <article slot="end" class="reading">
                    <h3>Quarterly planning</h3>
                    <p>Hi team, the planning session moves to Thursday at 10:00. Please add your topics to
                      the shared agenda before Wednesday evening.</p>
                  </article>
                </mj-split-pane>
            """),
            css=_code("""
                .mail { block-size: 22rem; border: 1px solid var(--mj-border); }
                .fill { block-size: 100%; }
                .reading { padding: var(--mj-space-3) var(--mj-space-4); }
                .reading h3 { margin-block-start: 0; }
            """),
            script=_code("""
                const subjects = ["Quarterly planning", "Build failed on main", "Lunch on Friday?", "New hire onboarding",
                  "Invoice 2024-03", "Security review notes", "Design critique", "Release 4.2 checklist"]
                document.getElementById("mail-list").items = subjects.map((subject) => ({ label: subject }))
            """),
        ),
        ComponentExample(
            key="events",
            title="Collapse, persist and events",
            description=(
                "<p><code>collapsible=\"both\"</code> with <code>persist-key</code>: the buttons call "
                "<code>collapse(\"start\")</code>, <code>collapse(\"end\")</code>, <code>expand()</code> "
                "and set <code>size</code>. Events shows <code>mj-split-collapse</code>, "
                "<code>-expand</code> and <code>-resize-end</code> (the script collapses and restores "
                "once on load). Reload the page after a drag: the split is restored from "
                "localStorage.</p>"
            ),
            html=_code("""
                <mj-stack direction="horizontal" gap="sm" wrap class="bar">
                  <mj-button id="collapse-start" size="sm" variant="secondary">Collapse start</mj-button>
                  <mj-button id="collapse-end" size="sm" variant="secondary">Collapse end</mj-button>
                  <mj-button id="expand" size="sm" variant="secondary">Expand</mj-button>
                  <mj-button id="size-200" size="sm" variant="secondary">size = 200</mj-button>
                  <output id="split-readout" class="readout"></output>
                </mj-stack>
                <mj-split-pane id="demo-events-split" collapsible="both" persist-key="mj-catalog.split-demo" class="split">
                  <div slot="start" class="pane a">Navigation</div>
                  <div slot="end" class="pane b">Inspector</div>
                </mj-split-pane>
            """),
            css=_code("""
                .bar { margin: var(--mj-space-4); align-items: center; }
                .readout { color: var(--mj-text-muted); font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); }
                .split { block-size: 12rem; margin: 0 var(--mj-space-4) var(--mj-space-4); border: 1px solid var(--mj-border); }
                .pane { box-sizing: border-box; min-block-size: 100%; padding: var(--mj-space-3); }
                .a { background: var(--mj-bg-muted); }
            """),
            script=_code("""
                const split = document.getElementById("demo-events-split")
                const readout = document.getElementById("split-readout")
                const show = () => { readout.textContent = "size " + Math.round(split.size) + "px, ratio " + split.ratio.toFixed(2) + ", collapsed " + split.collapsed }
                split.addEventListener("mj-split-resize-end", show)
                split.addEventListener("mj-split-collapse", (event) => { mjSandbox.log("collapsed", event.detail); show() })
                split.addEventListener("mj-split-expand", (event) => { mjSandbox.log("expanded", event.detail); show() })
                document.getElementById("collapse-start").addEventListener("click", () => split.collapse("start"))
                document.getElementById("collapse-end").addEventListener("click", () => split.collapse("end"))
                document.getElementById("expand").addEventListener("click", () => split.expand())
                document.getElementById("size-200").addEventListener("click", () => { split.size = 200 })
                await new Promise((resolve) => requestAnimationFrame(resolve))
                split.collapse("start")
                split.expand()
                show()
            """),
        ),
        ComponentExample(
            key="disabled",
            title="Disabled separator",
            description=(
                "<p><code>disabled</code> locks the separator (not focusable, no drag), while the form "
                "in the end pane stays fully usable.</p>"
            ),
            html=_code("""
                <mj-split-pane disabled initial-size="35%" class="locked">
                  <div slot="start" class="pane menu"><strong>Settings</strong><p>General</p><p>Members</p></div>
                  <div slot="end" class="pane">
                    <mj-text-field label="Workspace name" value="Acme"></mj-text-field>
                    <mj-button size="sm" variant="primary" class="save">Save</mj-button>
                  </div>
                </mj-split-pane>
            """),
            css=_code("""
                .locked { block-size: 12rem; margin: var(--mj-space-4); border: 1px solid var(--mj-border); }
                .locked .pane { box-sizing: border-box; min-block-size: 100%; padding: var(--mj-space-3); }
                .menu { background: var(--mj-bg-muted); }
                .save { margin-block-start: var(--mj-space-3); }
            """),
        ),
    ],
    slots=[
        ("start", "Start pane content (left in LTR, top when vertical).",
         '<div style="padding:1rem">Start pane from the slot inspector</div>'),
        ("end", "End pane content.", '<div style="padding:1rem">End pane from the slot inspector</div>'),
    ],
    properties=[
        ("size", "number. Start pane size in px; setting it resizes (clamped) and fires mj-split-resize-end."),
        ("ratio", "number. Start pane size as a fraction 0-1 of the container (read-only)."),
        ("collapsed", "'start' | 'end' | null. The collapsed pane (read-only; also reflected as the `collapsed` host attribute)."),
        ("disabled", "boolean. Reflects `disabled`."),
    ],
    methods=[
        ("collapse(pane)", "Collapses the 'start' (default) or 'end' pane to zero; the split is kept for expand()."),
        ("expand()", "Restores the collapsed pane to the previous split."),
    ],
    parts=[
        ("start-pane", "The start pane container."),
        ("separator", "The separator (role=separator)."),
        ("separator-handle", "The grip drawn on the separator."),
        ("end-pane", "The end pane container."),
    ],
    css_properties=[
        ("--mj-split-separator-size", "Thickness of the separator bar (default 4px)."),
        ("--mj-split-separator-color", "Separator colour (default var(--mj-border))."),
        ("--mj-split-separator-hover-color", "Separator colour on hover / focus (default var(--mj-accent))."),
        ("--mj-split-separator-hit-slop", "Extra pointer target on each side of the bar (default 6px)."),
        ("--mj-split-handle-size", "Length of the grip (default 24px)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-scroll-area
# ---------------------------------------------------------------------------

def _activity_items(count: int) -> str:
    """
        Markup for a list of activity entries.

        :param count: Number of entries.

        :returns: The ``<li>`` elements, one per line.
    """

    events = [
        ("Priya", "merged", "Fix dock band sizes"),
        ("Tom", "commented on", "Split pane persist format"),
        ("Ada", "opened", "Carousel fade transition"),
        ("Sam", "approved", "Scroll area keyboard access"),
        ("Rita", "closed", "Feed item roles"),
        ("Jo", "pushed to", "release/4.2"),
    ]
    lines = []
    for index in range(count):
        who, verb, what = events[index % len(events)]
        lines.append(f"    <li><b>{who}</b> {verb} <a href=\"#pr-{120 + index}\">{what}</a> <small>{index + 2} min ago</small></li>")
    text = "\n".join(lines)
    return text


SCROLL_AREA = ComponentDoc(
    tag="mj-scroll-area",
    title="Scroll Area",
    group="layout",
    summary="A scrollable region with theme-aware native scrollbars and scroll events.",
    description=(
        "<p><code>&lt;mj-scroll-area&gt;</code> wraps overflowing content in a viewport whose "
        "scrollbars are the browser's own, styled with <code>scrollbar-color</code> / "
        "<code>scrollbar-width</code> from the design tokens. Native scrolling, momentum and keyboard "
        "scrolling are preserved. The host is a column flex container and the viewport fills it, so the "
        "area scrolls with a fixed <code>height</code>, with only a <code>max-height</code> (the "
        "viewport grows with its content up to the limit), or as the stretched child of a flex column "
        "or dock layout.</p>"
        "<p><code>scrollbar-visibility</code>: <code>auto</code> shows the scrollbar when the content "
        "overflows, <code>always</code> reserves the track, <code>hover</code> draws the thumb only "
        "while the pointer is over the area or focus is inside it. <code>native</code> leaves the "
        "platform styling untouched.</p>"
        "<p>The viewport is a <code>region</code> named from the host's <code>aria-label</code> (or "
        "the text of the elements <code>aria-labelledby</code> points to). It is a tab stop only while "
        "its content overflows, so keyboard users can scroll it; a <code>tabindex</code> on the host "
        "is moved to the viewport and then always applies. <code>mj-scroll</code> fires at most once "
        "per animation frame while scrolling; <code>mj-scroll-end</code> fires once when scrolling "
        "stops (native <code>scrollend</code>, or 150ms of quiet where that event is not "
        "supported).</p>"
    ),
    how_to_use=(
        "<p>Wrap long content and give the host a height or max-height. Set <code>overflow-x</code> / "
        "<code>overflow-y</code> for horizontal or two-axis scrolling, <code>aria-label</code> to name "
        "the region, and <code>scroll-padding</code> to keep scroll-snap targets clear of an edge. "
        "Scroll-snap itself is set on the viewport part: "
        "<code>mj-scroll-area::part(viewport) { scroll-snap-type: x mandatory }</code>. Read or set "
        "<code>scrollTop</code> / <code>scrollLeft</code> on the host.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="overflow-x", description="Horizontal overflow of the viewport.", kind="enum",
                     values=["hidden", "auto", "scroll", "visible"], default="hidden"),
        AttributeDoc(name="overflow-y", description="Vertical overflow of the viewport.", kind="enum",
                     values=["auto", "hidden", "scroll", "visible"], default="auto"),
        AttributeDoc(name="scrollbar-visibility", description="When the styled scrollbar is shown.", kind="enum",
                     values=["auto", "always", "hover"], default="auto"),
        AttributeDoc(name="native", description="Use the platform's default scrollbar styling.", kind="boolean"),
        AttributeDoc(name="scroll-padding", description="CSS scroll-padding of the viewport (for snap targets).", kind="string",
                     values=["0", "1rem", "0 2rem"]),
        AttributeDoc(name="aria-label", description="Accessible name of the scroll region.", kind="string"),
        AttributeDoc(name="aria-labelledby", description="Ids of elements whose text names the region.", kind="string"),
        AttributeDoc(name="tabindex", description="Moved to the viewport; makes it focusable even without overflow.", kind="number"),
    ],
    events=[
        ("mj-scroll", "While scrolling, at most once per animation frame.",
         "{ scrollTop: number, scrollLeft: number, scrollHeight: number, scrollWidth: number }"),
        ("mj-scroll-end", "Scrolling stopped (once per scroll).", "{ scrollTop: number, scrollLeft: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Activity list",
            description=(
                "<p>A 14rem tall activity list. The viewport is a tab stop because the list overflows: "
                "press Tab into it and scroll with the Arrow keys. Try "
                "<code>scrollbar-visibility</code> and <code>native</code> in Controls.</p>"
            ),
            html=(
                '<mj-scroll-area class="demo-scroll" aria-label="Recent activity">\n'
                '  <ul class="activity">\n'
                + _activity_items(14)
                + "\n  </ul>\n</mj-scroll-area>"
            ),
            css=_code("""
                .demo-scroll { block-size: 14rem; max-inline-size: 30rem; margin: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .activity { list-style: none; margin: 0; padding: 0; }
                .activity li { padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }
                .activity small { color: var(--mj-text-muted); }
            """),
        ),
        ComponentExample(
            key="horizontal",
            title="Horizontal with snap",
            description=(
                "<p><code>overflow-x=\"auto\" overflow-y=\"hidden\"</code> with cards in a row, "
                "scroll-snap set on <code>::part(viewport)</code> and "
                "<code>scroll-padding=\"0 1rem\"</code>. Scroll sideways: each card snaps to the start "
                "edge. Switch <b>Dir</b> to <b>RTL</b>: the row starts on the right.</p>"
            ),
            html=_code(f"""
                <mj-scroll-area overflow-x="auto" overflow-y="hidden" scroll-padding="0 1rem" aria-label="Featured routes" class="rail">
                  <div class="track">
                    <mj-card heading="Alpine trail" aspect-ratio="16/9"><img slot="media" src="{IMG_TRAIL}" alt="Alpine trail" /><p>14 km</p></mj-card>
                    <mj-card heading="Lake loop" aspect-ratio="16/9"><img slot="media" src="{IMG_LAKE}" alt="Lake" /><p>6 km</p></mj-card>
                    <mj-card heading="Dune walk" aspect-ratio="16/9"><img slot="media" src="{IMG_DUNES}" alt="Dunes" /><p>9 km</p></mj-card>
                    <mj-card heading="Forest path" aspect-ratio="16/9"><img slot="media" src="{IMG_FOREST}" alt="Forest" /><p>11 km</p></mj-card>
                    <mj-card heading="Coast road" aspect-ratio="16/9"><img slot="media" src="{IMG_COAST}" alt="Coast" /><p>18 km</p></mj-card>
                  </div>
                </mj-scroll-area>
            """),
            css=_code("""
                .rail { margin: var(--mj-space-4); }
                .rail::part(viewport) { scroll-snap-type: x mandatory; }
                .track { display: flex; gap: var(--mj-space-3); padding: var(--mj-space-2) var(--mj-space-4) var(--mj-space-3); inline-size: max-content; }
                .track mj-card { inline-size: 14rem; scroll-snap-align: start; }
            """),
        ),
        ComponentExample(
            key="max-height",
            title="max-height and flex column",
            description=(
                "<p>Left: only <code>max-height: 12rem</code>; the area grows with its content until the "
                "limit, then scrolls. <b>Add comment</b> appends items: once it overflows the viewport "
                "becomes a tab stop. Right: a panel that is a flex column; the scroll area is its "
                "<code>flex: 1</code> middle child between a fixed header and footer.</p>"
            ),
            html=_code("""
                <mj-grid columns="2" min-col-width="15rem" gap="md" class="two">
                  <div>
                    <mj-scroll-area id="grow-area" aria-label="Comments" class="grow">
                      <ul id="comments" class="comments"><li>First!</li></ul>
                    </mj-scroll-area>
                    <mj-button id="add-comment" size="sm" variant="secondary" class="add">Add comment</mj-button>
                  </div>
                  <section class="panel" aria-label="Chat">
                    <header class="panel-head">Team chat</header>
                    <mj-scroll-area aria-label="Chat messages" class="panel-body">
                      <p>Morning! Standup in 5.</p><p>Can someone review the dock PR?</p><p>On it.</p>
                      <p>Staging is green again.</p><p>Lunch?</p><p>12:30 works.</p><p>See you there.</p>
                    </mj-scroll-area>
                    <footer class="panel-foot"><mj-text-field label="Message" placeholder="Write a message"></mj-text-field></footer>
                  </section>
                </mj-grid>
            """),
            css=_code("""
                .two { padding: var(--mj-space-4); }
                .grow { max-block-size: 12rem; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .comments { margin: 0; padding: var(--mj-space-2) var(--mj-space-5); }
                .add { margin-block-start: var(--mj-space-2); }
                .panel { display: flex; flex-direction: column; block-size: 18rem; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .panel-head, .panel-foot { padding: var(--mj-space-2) var(--mj-space-3); background: var(--mj-bg-muted); }
                .panel-body { flex: 1 1 auto; min-block-size: 0; padding-inline: var(--mj-space-3); }
            """),
            script=_code("""
                const list = document.getElementById("comments")
                let count = 1
                document.getElementById("add-comment").addEventListener("click", () => {
                  count = count + 1
                  const item = document.createElement("li")
                  item.textContent = "Comment number " + count
                  list.append(item)
                })
            """),
        ),
        ComponentExample(
            key="events",
            title="Scroll events",
            description=(
                "<p>The script scrolls the log to the bottom on load and the buttons scroll through the "
                "<code>scrollTop</code> property; Events shows the throttled <code>mj-scroll</code> "
                "stream and one <code>mj-scroll-end</code> per scroll. Two-axis overflow: the table is "
                "wider than the area.</p>"
            ),
            html=_code("""
                <mj-stack direction="horizontal" gap="sm" class="bar">
                  <mj-button id="to-top" size="sm" variant="secondary">Top</mj-button>
                  <mj-button id="to-bottom" size="sm" variant="secondary">Bottom</mj-button>
                  <output id="scroll-readout" class="readout"></output>
                </mj-stack>
                <mj-scroll-area id="demo-events-scroll" overflow-x="auto" overflow-y="auto" aria-label="Deployment log" class="log-area">
                  <table id="log-table" class="log"></table>
                </mj-scroll-area>
            """),
            css=_code("""
                .bar { margin: var(--mj-space-4) var(--mj-space-4) 0; align-items: center; }
                .readout { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
                .log-area { block-size: 12rem; margin: var(--mj-space-4); border: 1px solid var(--mj-border); }
                .log { border-collapse: collapse; white-space: nowrap; font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); }
                .log td { padding: var(--mj-space-1) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }
            """),
            script=_code("""
                const area = document.getElementById("demo-events-scroll")
                const table = document.getElementById("log-table")
                const readout = document.getElementById("scroll-readout")
                for (let index = 1; index <= 40; index = index + 1) {
                  const row = table.insertRow()
                  row.insertCell().textContent = "10:" + String(index).padStart(2, "0") + ":00"
                  row.insertCell().textContent = "deploy"
                  row.insertCell().textContent = "step " + index + " of 40: rolling out pod web-" + index + " in region eu-west-1 (healthy)"
                }
                area.addEventListener("mj-scroll-end", (event) => {
                  readout.textContent = "scrollTop " + Math.round(event.detail.scrollTop)
                  mjSandbox.log("scroll settled", event.detail)
                })
                document.getElementById("to-top").addEventListener("click", () => { area.scrollTop = 0 })
                document.getElementById("to-bottom").addEventListener("click", () => { area.scrollTop = area.scrollHeight })
                await new Promise((resolve) => requestAnimationFrame(resolve))
                area.scrollTop = area.scrollHeight
            """),
        ),
    ],
    slots=[
        ("", "The scrollable content.", "<p>Content supplied by the slot inspector.</p>"),
    ],
    properties=[
        ("scrollTop", "number. Vertical scroll position of the viewport; settable."),
        ("scrollLeft", "number. Horizontal scroll position of the viewport; settable."),
        ("scrollHeight", "number. Scroll height of the viewport content (read-only)."),
        ("scrollWidth", "number. Scroll width of the viewport content (read-only)."),
    ],
    parts=[
        ("viewport", "The scrolling element (role=region); target scroll-snap rules here."),
    ],
    css_properties=[
        ("--mj-scroll-thumb-color", "Scrollbar thumb colour (default var(--mj-border-strong))."),
        ("--mj-scroll-track-color", "Scrollbar track colour (default transparent)."),
        ("--mj-scroll-scrollbar-width", "scrollbar-width (default thin)."),
        ("--mj-scroll-overflow-x", "overflow-x; written by `overflow-x` (default hidden)."),
        ("--mj-scroll-overflow-y", "overflow-y; written by `overflow-y` (default auto)."),
        ("--mj-scroll-padding", "scroll-padding; written by `scroll-padding` (default 0)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-carousel
# ---------------------------------------------------------------------------

def _slide(image: str, title: str, text: str) -> str:
    """
        Markup of one picture slide (a figure with a caption).

        :param image: Image data URI.
        :param title: Caption title.
        :param text: Caption text.

        :returns: The ``<figure>`` markup.
    """

    markup = (
        f'  <figure class="slide">\n'
        f'    <img src="{image}" alt="{title}" />\n'
        f"    <figcaption><b>{title}</b> {text}</figcaption>\n"
        f"  </figure>"
    )
    return markup


SLIDE_CSS = _code("""
    .slide { margin: 0; }
    .slide img { display: block; inline-size: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: var(--mj-radius-md); }
    .slide figcaption { padding-block-start: var(--mj-space-2); color: var(--mj-text-muted); }
    .slide figcaption b { color: var(--mj-text); }
""")


CAROUSEL = ComponentDoc(
    tag="mj-carousel",
    title="Carousel",
    group="layout",
    summary="A slide sequence with previous / next buttons, picker tabs and optional auto-rotation.",
    description=(
        "<p><code>&lt;mj-carousel&gt;</code> shows one slide at a time, following the WAI-ARIA APG "
        "carousel pattern: a labelled region with <code>aria-roledescription=\"carousel\"</code>, "
        "previous / next buttons, a tab list of picker dots and a polite live region that announces "
        "slide changes made by the user (not those of the rotation timer).</p>"
        "<p>Slides are the element children that are not in a named slot: any element works (a "
        "<code>figure</code>, an <code>article</code>, an <code>mj-card</code>; the conventional "
        "<code>mj-carousel-slide</code> tag is a plain element, not a component). Every slide is sized "
        "to the full width; the carousel gives it <code>role=group</code>, "
        "<code>aria-roledescription=\"slide\"</code> and an \"n of total\" label unless the author set "
        "them, and <code>aria-hidden</code> plus <code>visibility: hidden</code> on the slides out of "
        "view so their content is not focusable.</p>"
        "<p><code>transition</code>: <code>slide</code> moves the track (mirrored in RTL), "
        "<code>fade</code> cross-fades, <code>none</code> switches at once; reduced motion turns "
        "animation off. Arrow Left / Right, Home and End work on the picker tabs only (focus follows "
        "the selection); elsewhere the keys keep their normal meaning.</p>"
        "<p><code>autoplay</code> adds a pause / play button and starts rotating, except for users who "
        "prefer reduced motion (they get the button and start it themselves). Hovering or focusing "
        "the carousel suspends the timer without changing the playing state; "
        "<code>mj-carousel-play</code> / <code>-pause</code> fire only when that state changes. "
        "Without <code>loop</code> the buttons are disabled at the ends and rotation stops at the last "
        "slide.</p>"
    ),
    how_to_use=(
        "<p>Put one element per slide inside <code>&lt;mj-carousel&gt;</code> and set "
        "<code>label</code>. Add <code>loop</code> to wrap around, <code>autoplay</code> and "
        "<code>autoplay-interval</code> (ms, at least 1000) for rotation. Hide navigation with "
        "<code>show-controls=\"false\"</code> or <code>show-picker=\"false\"</code>. Listen for the "
        "cancelable <code>mj-carousel-change</code> to veto a move and "
        "<code>mj-carousel-changed</code> to react after it; set <code>current-index</code> to jump "
        "without events.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="current-index", description="Zero-based index of the slide on display; kept inside the slide range.",
                     kind="number", default="0"),
        AttributeDoc(name="loop", description="Wrap past the first and last slides.", kind="boolean"),
        AttributeDoc(name="autoplay", description="Adds the pause / play control and starts rotating (not under reduced motion).",
                     kind="boolean"),
        AttributeDoc(name="autoplay-interval", description="Milliseconds between advances (minimum 1000).", kind="number",
                     default="5000"),
        AttributeDoc(name="transition", description="Slide change animation.", kind="enum",
                     values=["slide", "fade", "none"], default="slide"),
        AttributeDoc(name="show-controls", description="`false` hides the previous / next buttons.", kind="boolean", default="true"),
        AttributeDoc(name="show-picker", description="`false` hides the picker dots.", kind="boolean", default="true"),
        AttributeDoc(name="label", description="Accessible name of the carousel region.", kind="string", default="Carousel"),
        AttributeDoc(name="prev-label", description="Accessible name of the previous button.", kind="string", default="Previous slide"),
        AttributeDoc(name="next-label", description="Accessible name of the next button.", kind="string", default="Next slide"),
    ],
    events=[
        ("mj-carousel-change", "Cancelable; fires before a user or timer move. preventDefault() keeps the current slide.",
         "{ index: number, previousIndex: number, trigger: 'user' | 'auto' }"),
        ("mj-carousel-changed", "The new slide is on display.", "{ index: number, previousIndex: number }"),
        ("mj-carousel-play", "Auto-rotation was switched on.", "{}"),
        ("mj-carousel-pause", "Auto-rotation was switched off (button, `playing = false`, or the end of a non-looping carousel).", "{}"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Photo carousel",
            description=(
                "<p>Four picture slides (plain <code>figure</code> elements) with <code>loop</code>. Use "
                "the arrow buttons or the dots; focus a dot and press Arrow Left / Right. Switch "
                "<b>Dir</b> to <b>RTL</b>: the track and the buttons mirror (previous on the right).</p>"
            ),
            html=(
                '<mj-carousel class="demo-carousel" label="Featured routes" loop>\n'
                + _slide(IMG_TRAIL, "Alpine trail.", "Fourteen kilometres past seven glacier lakes.") + "\n"
                + _slide(IMG_LAKE, "Lake loop.", "A flat, family-friendly walk around the reservoir.") + "\n"
                + _slide(IMG_DUNES, "Dune walk.", "Soft sand and big skies; best at sunset.") + "\n"
                + _slide(IMG_COAST, "Coast road.", "A rolling ride along the cliffs.") + "\n"
                + "</mj-carousel>"
            ),
            css=".demo-carousel { max-inline-size: 34rem; margin: var(--mj-space-4); }\n" + SLIDE_CSS,
        ),
        ComponentExample(
            key="autoplay",
            title="Auto-rotation with fade",
            description=(
                "<p><code>autoplay autoplay-interval=\"2500\" transition=\"fade\" loop</code>. Watch "
                "<code>mj-carousel-change</code> (trigger <code>auto</code>) and "
                "<code>-changed</code> in Events; hover the carousel to suspend the timer, or press the "
                "pause button (fires <code>mj-carousel-pause</code>).</p>"
            ),
            html=(
                '<mj-carousel label="Announcements" autoplay autoplay-interval="2500" transition="fade" loop class="banner">\n'
                '  <mj-alert severity="info"><b>New:</b> dock layouts keep the band sizes you give them.</mj-alert>\n'
                '  <mj-alert severity="success"><b>Done:</b> the 4.2 release is live in every region.</mj-alert>\n'
                '  <mj-alert severity="warning"><b>Heads up:</b> maintenance window on Sunday 02:00-03:00 UTC.</mj-alert>\n'
                "</mj-carousel>"
            ),
            css=".banner { max-inline-size: 40rem; margin: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="cards",
            title="Card groups per slide",
            description=(
                "<p>Each slide is an <code>mj-grid</code> of three <code>mj-card</code>s; no "
                "<code>loop</code>, so the previous button is disabled on the first slide and next on "
                "the last. <code>show-picker=\"false\"</code> hides the dots. Try the <b>320</b> preset: "
                "the cards inside a slide stack.</p>"
            ),
            html=_code("""
                <mj-carousel label="Plans" show-picker="false" class="plans">
                  <mj-grid columns="3" min-col-width="10rem" gap="sm" aria-label="Personal plans">
                    <mj-card heading="Free" subheading="$0" elevation="outlined"><p>One project.</p></mj-card>
                    <mj-card heading="Pro" subheading="$12 / month" elevation="outlined"><p>Unlimited projects and 20 GB of storage.</p></mj-card>
                    <mj-card heading="Pro+" subheading="$20 / month" elevation="outlined"><p>Everything in Pro plus priority support.</p></mj-card>
                  </mj-grid>
                  <mj-grid columns="3" min-col-width="10rem" gap="sm" aria-label="Team plans">
                    <mj-card heading="Team" subheading="$9 / seat" elevation="outlined"><p>Shared workspaces.</p></mj-card>
                    <mj-card heading="Business" subheading="$19 / seat" elevation="outlined"><p>SSO and audit log.</p></mj-card>
                    <mj-card heading="Enterprise" subheading="Contact us" elevation="outlined"><p>Dedicated region and SLA.</p></mj-card>
                  </mj-grid>
                </mj-carousel>
            """),
            css=_code("""
                .plans { max-inline-size: 44rem; margin: var(--mj-space-4); }
                .plans mj-grid { padding: var(--mj-space-1); }
            """),
        ),
        ComponentExample(
            key="events",
            title="Vetoing a change",
            description=(
                "<p>The script cancels <code>mj-carousel-change</code> to slide 3 until the checkbox is "
                "checked, and logs every <code>mj-carousel-changed</code>. On load it presses the next "
                "button once. <b>Jump to last</b> sets <code>current-index</code>, which changes the slide "
                "without events.</p>"
            ),
            html=(
                '<mj-carousel id="demo-events-carousel" label="Onboarding" class="steps">\n'
                '  <section class="step"><h3>1. Create a workspace</h3><p>Pick a name and a region.</p></section>\n'
                '  <section class="step"><h3>2. Invite your team</h3><p>Send invites by email or share a link.</p></section>\n'
                '  <section class="step"><h3>3. Connect a repository</h3><p>Requires the checkbox below.</p></section>\n'
                '  <section class="step"><h3>4. Ship</h3><p>Your first deploy is one click away.</p></section>\n'
                "</mj-carousel>\n"
                '<label class="gate"><input type="checkbox" id="allow-step-3"> I have admin rights on the repository</label>\n'
                '<mj-button id="jump-last" size="sm" variant="secondary" class="gate">Jump to last</mj-button>'
            ),
            css=_code("""
                .steps { max-inline-size: 30rem; margin: var(--mj-space-4); }
                .step { padding: var(--mj-space-5); background: var(--mj-bg-muted); border-radius: var(--mj-radius-md); }
                .step h3 { margin-block-start: 0; }
                .gate { display: inline-block; margin: 0 var(--mj-space-4) var(--mj-space-4); }
            """),
            script=_code("""
                const carousel = document.getElementById("demo-events-carousel")
                const allow = document.getElementById("allow-step-3")
                carousel.addEventListener("mj-carousel-change", (event) => {
                  if (event.detail.index === 2 && allow.checked === false) {
                    event.preventDefault()
                    mjSandbox.log("change vetoed", event.detail)
                  }
                })
                carousel.addEventListener("mj-carousel-changed", (event) => mjSandbox.log("now on slide", { index: event.detail.index }))
                document.getElementById("jump-last").addEventListener("click", () => {
                  carousel.setAttribute("current-index", String(carousel.slides.length - 1))
                })
                carousel.shadowRoot.querySelector("[part='next-button']").click()
            """),
        ),
        ComponentExample(
            key="rtl",
            title="Right-to-left",
            description=(
                "<p>A carousel inside <code>dir=\"rtl\"</code> with Arabic button labels "
                "(<code>prev-label</code> / <code>next-label</code>) and <code>transition=\"none\"</code>. "
                "The first slide is on the right, the previous button is on the right with its chevron "
                "pointing right (outwards), the next button on the left points left, and Arrow Right on a "
                "dot moves to the previous slide.</p>"
            ),
            html=(
                '<div dir="rtl" lang="ar" class="rtl-wrap">\n'
                '<mj-carousel label="&#1605;&#1587;&#1575;&#1585;&#1575;&#1578;" prev-label="&#1575;&#1604;&#1588;&#1585;&#1610;&#1581;&#1577; &#1575;&#1604;&#1587;&#1575;&#1576;&#1602;&#1577;" '
                'next-label="&#1575;&#1604;&#1588;&#1585;&#1610;&#1581;&#1577; &#1575;&#1604;&#1578;&#1575;&#1604;&#1610;&#1577;" transition="none">\n'
                + _slide(IMG_FOREST, "1.", "&#1605;&#1587;&#1575;&#1585; &#1575;&#1604;&#1594;&#1575;&#1576;&#1577;") + "\n"
                + _slide(IMG_SQUARE, "2.", "&#1575;&#1604;&#1602;&#1605;&#1577;") + "\n"
                + _slide(IMG_LAKE, "3.", "&#1575;&#1604;&#1576;&#1581;&#1610;&#1585;&#1577;") + "\n"
                + "</mj-carousel>\n</div>"
            ),
            css=".rtl-wrap { max-inline-size: 30rem; margin: var(--mj-space-4); }\n" + SLIDE_CSS,
        ),
    ],
    slots=[
        ("", "The slides: every element child not assigned to a named slot.",
         '<section style="padding:2rem;background:var(--mj-bg-muted)"><h3>New slide</h3><p>Added by the slot inspector.</p></section>'),
    ],
    properties=[
        ("slides", "Element[]. The slide elements (read-only)."),
        ("currentIndex", "number. Index of the slide on display (read-only; set `current-index` to change it)."),
        ("playing", "boolean. Whether auto-rotation is on (it may be suspended by hover or focus); setting it starts or stops rotation."),
    ],
    parts=[
        ("root", "The carousel region."),
        ("slides-container", "The track holding the slides."),
        ("controls", "The row with the buttons and the picker."),
        ("prev-button", "Previous button."),
        ("next-button", "Next button."),
        ("picker", "The tab list of dots."),
        ("picker-item", "One picker dot (a tab)."),
        ("autoplay-button", "The pause / play button (shown with `autoplay`)."),
    ],
    css_properties=[
        ("--mj-carousel-slide-duration", "Slide / fade duration (default var(--mj-motion-medium))."),
        ("--mj-carousel-control-size", "Size of the round buttons (default 2.5rem)."),
        ("--mj-carousel-control-bg", "Button background (default var(--mj-surface))."),
        ("--mj-carousel-picker-size", "Dot size (default 0.5rem; the target is at least 1.5rem)."),
        ("--mj-carousel-picker-gap", "Gap between dots (default var(--mj-space-2))."),
        ("--mj-carousel-picker-active-color", "Colour of the current dot (default var(--mj-accent))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-feed
# ---------------------------------------------------------------------------

FEED_POSTS = [
    ("Alice Martin", "Shipped the new carousel fade transition.", "2 min"),
    ("Bob Chen", "Reviewed the accessibility audit; three findings left.", "14 min"),
    ("Chioma Eze", "Staging is green again after the cache fix.", "40 min"),
    ("Diego Alvarez", "Draft of the 4.3 roadmap is up for comments.", "1 h"),
    ("Emma Novak", "Pairing session on split pane persistence at 3 pm.", "2 h"),
]


def _post(name: str, text: str, age: str) -> str:
    """
        Markup of one feed article: a heading and an mj-media-object row.

        :param name: Author name.
        :param text: Post text.
        :param age: Relative time.

        :returns: The ``<article>`` markup.
    """

    markup = (
        f'  <article class="post">\n'
        f'    <mj-media-object gap="sm" media-size="auto">\n'
        f'      <mj-avatar slot="media" name="{name}" size="md"></mj-avatar>\n'
        f'      <h3 class="post-title">{name} <small>{age} ago</small></h3>\n'
        f"      <p>{text}</p>\n"
        f"    </mj-media-object>\n"
        f"  </article>"
    )
    return markup


POST_CSS = _code("""
    .post { padding: var(--mj-space-3); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); background: var(--mj-surface); }
    .post-title { margin: 0; font-size: var(--mj-font-size-md); }
    .post-title small { font-weight: var(--mj-font-weight-regular); color: var(--mj-text-muted); }
    .post p { margin: var(--mj-space-1) 0 0; }
""")

POST_SCRIPT_HELPERS = _code("""
    const names = ["Farah Haddad", "Gus Walker", "Hana Sato", "Ivan Petrov", "Julia Rossi", "Kofi Mensah"]
    let made = 0
    function makePost() {
      made = made + 1
      const name = names[made % names.length]
      const article = document.createElement("article")
      article.className = "post"
      article.innerHTML = '<mj-media-object gap="sm" media-size="auto"><mj-avatar slot="media" size="md"></mj-avatar>' +
        '<h3 class="post-title"></h3><p></p></mj-media-object>'
      article.querySelector("mj-avatar").setAttribute("name", name)
      article.querySelector("h3").textContent = name + " "
      const age = document.createElement("small")
      age.textContent = (made * 3) + " h ago"
      article.querySelector("h3").append(age)
      article.querySelector("p").textContent = "Older update number " + made + "."
      return article
    }
""")


FEED = ComponentDoc(
    tag="mj-feed",
    title="Feed",
    group="layout",
    summary="An ARIA feed of articles with infinite scroll or a Load more button.",
    description=(
        "<p><code>&lt;mj-feed&gt;</code> implements the WAI-ARIA <code>feed</code> pattern for a list "
        "of articles that grows as the user reads. Items are the element children not in a named slot "
        "(an <code>article</code>, a <code>div</code>, an <code>mj-card</code>; the conventional "
        "<code>mj-feed-item</code> tag is a plain element). On every item the feed manages "
        "<code>role=\"article\"</code> (unless the item has a role), "
        "<code>aria-posinset</code> / <code>aria-setsize</code> (the size is -1 while more items can "
        "be loaded), <code>aria-labelledby</code> pointing at the item's first heading, and a roving "
        "tabindex: one item is a tab stop, Page Down / Page Up move focus to the next / previous item "
        "and Ctrl+End / Ctrl+Home to the last / first.</p>"
        "<p>Loading: with <code>load-mode=\"scroll\"</code> (default) an invisible sentinel after the "
        "last item fires <code>mj-feed-load-more</code> when it comes within 200px of view (also inside "
        "a scroll container) and again when loading ends while it is still visible; with "
        "<code>button</code> a Load more button does; with <code>none</code> nothing is requested. "
        "While <code>loading</code> is set the feed is <code>aria-busy</code>, the button is disabled "
        "and a loading line is shown; <code>has-more=\"false\"</code> removes the trigger. Items added "
        "after load are announced (\"3 new items added\"). <code>slot=\"empty\"</code> content shows "
        "while there are no items and nothing is loading. <code>reversed</code> stacks items bottom-up "
        "(chat style) with the trigger on top.</p>"
    ),
    how_to_use=(
        "<p>Put one element per article inside <code>&lt;mj-feed&gt;</code>, each with a heading. "
        "Listen for <code>mj-feed-load-more</code>: set <code>loading</code>, append the new elements, "
        "remove <code>loading</code>, and set <code>has-more=\"false\"</code> when everything is "
        "loaded. For infinite scroll inside a panel, wrap the feed in an "
        "<code>&lt;mj-scroll-area&gt;</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="load-mode", description="How more items are requested.", kind="enum",
                     values=["scroll", "button", "none"], default="scroll"),
        AttributeDoc(name="loading", description="Marks the feed busy, disables the button and shows the loading line.", kind="boolean"),
        AttributeDoc(name="has-more", description="`false` when everything is loaded: hides the trigger and sets the real set size.",
                     kind="boolean", default="true"),
        AttributeDoc(name="reversed", description="Stacks items bottom-up with the trigger at the top.", kind="boolean"),
        AttributeDoc(name="load-more-label", description="Text of the Load more button.", kind="string", default="Load more"),
        AttributeDoc(name="loading-label", description="Text of the loading line.", kind="string", default="Loading"),
    ],
    events=[
        ("mj-feed-load-more", "The sentinel came into view or the button was pressed.", "{ itemCount: number }"),
        ("mj-feed-item-focus", "Page Up / Down or Ctrl+Home / End moved focus to an item.", "{ item: Element, index: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Load more button",
            description=(
                "<p>A team feed with <code>load-mode=\"button\"</code>. <b>Load more</b> fires "
                "<code>mj-feed-load-more</code>; the script sets <code>loading</code>, appends two posts "
                "after 600ms and sets <code>has-more=\"false\"</code> after the third page. Click a post "
                "and press Page Down / Page Up to move between articles.</p>"
            ),
            html=(
                '<mj-feed id="demo-feed" class="demo-feed" load-mode="button" aria-label="Team updates">\n'
                + "\n".join(_post(name, text, age) for name, text, age in FEED_POSTS[:3])
                + "\n</mj-feed>"
            ),
            css=".demo-feed { max-inline-size: 34rem; margin: var(--mj-space-4); }\n" + POST_CSS,
            script=POST_SCRIPT_HELPERS + "\n" + _code("""
                const feed = document.getElementById("demo-feed")
                let pages = 0
                if (feed !== null) {
                  feed.addEventListener("mj-feed-load-more", () => {
                    feed.setAttribute("loading", "")
                    setTimeout(() => {
                      feed.append(makePost(), makePost())
                      feed.removeAttribute("loading")
                      pages = pages + 1
                      if (pages >= 3) { feed.setAttribute("has-more", "false") }
                    }, 600)
                  })
                }
            """),
        ),
        ComponentExample(
            key="infinite",
            title="Infinite scroll in a panel",
            description=(
                "<p>The default <code>load-mode=\"scroll\"</code> inside a 20rem <code>mj-scroll-area</code>. "
                "Scroll down: near the end the feed fires <code>mj-feed-load-more</code>, the loading line "
                "shows while the script fetches (three posts per request), and once there are 15 or more "
                "posts <code>has-more</code> becomes false.</p>"
            ),
            html=(
                '<mj-scroll-area aria-label="Activity" class="panel">\n'
                '<mj-feed id="infinite-feed" aria-label="Activity" loading-label="Fetching older posts">\n'
                + "\n".join(_post(name, text, age) for name, text, age in FEED_POSTS)
                + "\n</mj-feed>\n</mj-scroll-area>"
            ),
            css=_code("""
                .panel { block-size: 20rem; max-inline-size: 34rem; margin: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                #infinite-feed { padding: var(--mj-space-3); }
            """) + "\n" + POST_CSS,
            script=POST_SCRIPT_HELPERS + "\n" + _code("""
                const feed = document.getElementById("infinite-feed")
                feed.addEventListener("mj-feed-load-more", (event) => {
                  if (feed.hasAttribute("loading")) { return }
                  feed.setAttribute("loading", "")
                  setTimeout(() => {
                    feed.append(makePost(), makePost(), makePost())
                    feed.removeAttribute("loading")
                    if (feed.itemCount >= 15) { feed.setAttribute("has-more", "false") }
                  }, 700)
                })
            """),
        ),
        ComponentExample(
            key="empty",
            title="Empty state",
            description=(
                "<p>A feed with no items and <code>has-more=\"false\"</code> shows its "
                "<code>slot=\"empty\"</code> content, an <code>mj-empty-state</code>. <b>Post an "
                "update</b> appends an article: the empty state disappears and the new item is "
                "announced.</p>"
            ),
            html=_code(f"""
                <mj-feed id="empty-feed" has-more="false" aria-label="Announcements" class="feed">
                  <mj-empty-state slot="empty" heading="No announcements yet" compact>
                    {ICON_FOLDER}
                    <p slot="description">Updates from your team will appear here.</p>
                    <mj-button slot="actions" id="post-update" size="sm" variant="primary">Post an update</mj-button>
                  </mj-empty-state>
                </mj-feed>
            """),
            css=".feed { max-inline-size: 34rem; margin: var(--mj-space-4); }\n" + POST_CSS,
            script=POST_SCRIPT_HELPERS + "\n" + _code("""
                const feed = document.getElementById("empty-feed")
                document.getElementById("post-update").addEventListener("click", () => {
                  feed.append(makePost())
                  mjSandbox.log("items", { itemCount: feed.itemCount })
                })
            """),
        ),
        ComponentExample(
            key="reversed",
            title="Reversed (chat)",
            description=(
                "<p><code>reversed</code> with <code>load-mode=\"button\"</code> and "
                "<code>load-more-label=\"Load older messages\"</code>: items are in newest-first DOM order "
                "and shown bottom-up, so the newest message is at the bottom and the button at the top. The "
                "script appends older messages, which appear above.</p>"
            ),
            html=_code("""
                <mj-feed id="chat-feed" reversed load-mode="button" load-more-label="Load older messages" aria-label="Chat" class="chat">
                  <article class="msg"><h3>Sam</h3><p>No problem, we start with the release.</p></article>
                  <article class="msg"><h3>Priya</h3><p>Joining from the train.</p></article>
                  <article class="msg"><h3>Sam</h3><p>Morning! Standup in five minutes.</p></article>
                </mj-feed>
            """),
            css=_code("""
                .chat { max-inline-size: 30rem; margin: var(--mj-space-4); --mj-feed-gap: var(--mj-space-2); }
                .msg { padding: var(--mj-space-2) var(--mj-space-3); background: var(--mj-bg-muted); border-radius: var(--mj-radius-md); }
                .msg h3 { margin: 0; font-size: var(--mj-font-size-sm); }
                .msg p { margin: 0; }
            """),
            script=_code("""
                const feed = document.getElementById("chat-feed")
                let older = 0
                feed.addEventListener("mj-feed-load-more", () => {
                  for (let index = 0; index < 2; index = index + 1) {
                    older = older + 1
                    const message = document.createElement("article")
                    message.className = "msg"
                    message.innerHTML = "<h3></h3><p></p>"
                    message.querySelector("h3").textContent = "Yesterday"
                    message.querySelector("p").textContent = "Older message " + older
                    feed.append(message)
                  }
                  if (older >= 6) { feed.setAttribute("has-more", "false") }
                })
            """),
        ),
    ],
    slots=[
        ("", "The feed items: element children not in a named slot.",
         "<article><h3>New post</h3><p>Added by the slot inspector.</p></article>"),
        ("empty", "Shown while there are no items and the feed is not loading.",
         '<mj-empty-state heading="Nothing here yet" compact></mj-empty-state>'),
    ],
    properties=[
        ("items", "Element[]. The feed items (read-only)."),
        ("itemCount", "number. Number of items (read-only)."),
    ],
    parts=[
        ("root", "The wrapper around the feed, its load-more controls and the empty state."),
        ("items-container", "The role=feed column holding only the items (the trigger, loading line, "
         "live region and empty state are outside it; it has no role while the feed is empty and "
         "not loading)."),
        ("load-more-button", "The Load more button (load-mode=button)."),
        ("loading-indicator", "The loading line (while `loading`)."),
        ("empty", "Container of the empty slot."),
    ],
    css_properties=[
        ("--mj-feed-gap", "Gap between items (default var(--mj-space-4))."),
        ("--mj-feed-max-width", "Maximum inline size of the item column (default none)."),
        ("--mj-feed-padding", "Padding of the item column (default 0)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-media-object
# ---------------------------------------------------------------------------

MEDIA_OBJECT = ComponentDoc(
    tag="mj-media-object",
    title="Media Object",
    group="layout",
    summary="Places a fixed-size media element beside a flexible text block.",
    description=(
        "<p><code>&lt;mj-media-object&gt;</code> is the row pattern behind comments, notifications, "
        "list rows with icons and settings rows: media in <code>slot=\"media\"</code>, text in the "
        "default slot. The media region is <code>media-size</code> wide (3rem by default) and never "
        "shrinks; a slotted <code>img</code>, <code>video</code>, <code>canvas</code> or "
        "<code>svg</code> is scaled to that width, while any other element (an "
        "<code>mj-avatar</code>, an icon button) keeps its own size and the region grows to hold it (but does not shrink below "
        "<code>media-size</code>; use <code>media-size=\"auto\"</code> to fit the region to a small avatar). "
        "The content takes the remaining width and wraps.</p>"
        "<p>The media region (and its gap) is removed while nothing is slotted into it. "
        "<code>media-position=\"end\"</code> moves the media to the trailing side (mirrored in RTL). "
        "With <code>stack-at</code> (a px, rem or em length) the media stacks above the content "
        "whenever the component is narrower than that length; <code>stacked</code> reports it.</p>"
    ),
    how_to_use=(
        "<p>Put an avatar, thumbnail or icon in <code>slot=\"media\"</code> and the text in the default "
        "slot. Use <code>align=\"center\"</code> for single-line rows, <code>media-size</code> for "
        "larger thumbnails, and <code>stack-at</code> for rows that must stack on phones. Nest media "
        "objects for threaded replies: each one is laid out by its own attributes (the "
        "<code>--mj-media-object-*</code> properties are per element and not inherited).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="media-position", description="Side of the media region.", kind="enum",
                     values=["start", "end"], default="start"),
        AttributeDoc(name="gap", description="Space between media and content.", kind="enum",
                     values=["none", "xs", "sm", "md", "lg", "xl"], default="md"),
        AttributeDoc(name="align", description="Cross-axis alignment of media and content. The text inside keeps the alignment of the page.", kind="enum",
                     values=["start", "center", "end", "stretch", "baseline"], default="start"),
        AttributeDoc(name="media-size", description="Width of the media region; replaced media scales to it. `auto` fits the region to an avatar or icon.", kind="string",
                     values=["auto", "2rem", "3rem", "4rem", "8rem", "96px"], default="3rem"),
        AttributeDoc(name="stack-at", description="Stack the media above the content when the component is narrower than this (px, rem, em).",
                     kind="string", values=["20rem", "28rem", "480px"]),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="Comment",
            description=(
                "<p>An avatar beside a comment with a name line, text and actions. Try "
                "<code>media-position=end</code>, <code>align=center</code> and <code>gap</code> in "
                "Controls, and <b>Dir</b> = <b>RTL</b>.</p>"
            ),
            html=_code("""
                <mj-media-object class="demo-media" gap="md" media-size="auto">
                  <mj-avatar slot="media" name="Carol Diaz" size="md" presence="online"></mj-avatar>
                  <div>
                    <b>Carol Diaz</b> <small class="muted">2 minutes ago</small>
                    <p class="comment">The dock layout now keeps my 3rem toolbar height. Could we also document
                      how the fill child is sized? That tripped me up last week.</p>
                    <mj-stack direction="horizontal" gap="sm">
                      <mj-button size="sm" variant="tertiary">Reply</mj-button>
                      <mj-button size="sm" variant="tertiary">Resolve</mj-button>
                    </mj-stack>
                  </div>
                </mj-media-object>
            """),
            css=_code("""
                .demo-media { max-inline-size: 36rem; margin: var(--mj-space-4); }
                .muted { color: var(--mj-text-muted); }
                .comment { margin: var(--mj-space-1) 0 var(--mj-space-2); }
            """),
        ),
        ComponentExample(
            key="list",
            title="Notification and settings rows",
            description=(
                "<p>Repeated rows: notifications with <code>align=\"center\"</code> and an svg icon, a long "
                "wrapping message, a row without media (the region collapses), and settings rows with the "
                "control as <code>media-position=\"end\"</code> media.</p>"
            ),
            html=_code("""
                <mj-stack gap="none" class="rows">
                  <mj-media-object align="center" gap="sm" class="row">
                    <svg slot="media" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="currentColor"/></svg>
                    Build #2481 failed on <b>main</b>.
                  </mj-media-object>
                  <mj-media-object align="center" gap="sm" class="row">
                    <svg slot="media" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="4" fill="currentColor"/></svg>
                    Priya requested your review on <b>Fix dock band sizes</b>, which changes 14 files across the
                    layout engine, the dock layout component and its functional tests.
                  </mj-media-object>
                  <mj-media-object align="center" class="row">
                    No media slotted: the media region and its gap are removed.
                  </mj-media-object>
                  <mj-media-object media-position="end" align="center" class="row">
                    <mj-toggle-button slot="media" pressed>On</mj-toggle-button>
                    <b>Email notifications</b><br><small class="muted">Daily digest at 08:00</small>
                  </mj-media-object>
                  <mj-media-object media-position="end" align="center" class="row">
                    <mj-button slot="media" size="sm" variant="secondary">Change</mj-button>
                    <b>Password</b><br><small class="muted">Last changed 3 months ago</small>
                  </mj-media-object>
                </mj-stack>
            """),
            css=_code("""
                .rows { max-inline-size: 34rem; margin: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .row { padding: var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }
                .row:last-child { border-block-end: none; }
                .row svg { color: var(--mj-accent); }
                .muted { color: var(--mj-text-muted); }
            """),
        ),
        ComponentExample(
            key="stack-at",
            title="Stacking on narrow widths",
            description=(
                "<p>Product rows with <code>media-size=\"8rem\"</code> and <code>stack-at=\"26rem\"</code>. "
                "At <b>Full</b> and <b>768</b> the picture sits beside the text; at the <b>320</b> preset "
                "the component is narrower than 26rem and the picture stacks on top.</p>"
            ),
            html=_code(f"""
                <mj-stack gap="md" class="products">
                  <mj-media-object media-size="8rem" stack-at="26rem">
                    <img slot="media" src="{IMG_TRAIL}" alt="Alpine trail" class="thumb" />
                    <h3 class="title">Alpine trail guide</h3>
                    <p>Printed route booklet with elevation profiles, water points and emergency exits for all
                      seven stages.</p>
                    <mj-button size="sm" variant="primary">Add to basket</mj-button>
                  </mj-media-object>
                  <mj-media-object media-size="8rem" stack-at="26rem">
                    <img slot="media" src="{IMG_COAST}" alt="Coast road" class="thumb" />
                    <h3 class="title">Coast road map</h3>
                    <p>Waterproof 1:50,000 map.</p>
                    <mj-button size="sm" variant="primary">Add to basket</mj-button>
                  </mj-media-object>
                </mj-stack>
            """),
            css=_code("""
                .products { max-inline-size: 40rem; margin: var(--mj-space-4); }
                .thumb { border-radius: var(--mj-radius-md); }
                .title { margin: 0 0 var(--mj-space-1); font-size: var(--mj-font-size-md); }
                .products p { margin: 0 0 var(--mj-space-2); }
            """),
        ),
        ComponentExample(
            key="nested",
            title="Threaded replies",
            description=(
                "<p>Media objects nested in the content of another for a reply thread. The thread "
                "keeps the default <code>md</code> gap while the replies set <code>gap=\"sm\"</code> for "
                "their small avatars; nested media objects never inherit the outer one's settings.</p>"
            ),
            html=_code("""
                <mj-media-object class="thread" media-size="auto">
                  <mj-avatar slot="media" name="Tom Becker" size="md"></mj-avatar>
                  <b>Tom Becker</b>
                  <p class="text">Should the split pane store pixels or a ratio?</p>
                  <mj-media-object gap="sm" class="reply" media-size="auto">
                    <mj-avatar slot="media" name="Ada Lovelace" size="sm"></mj-avatar>
                    <b>Ada Lovelace</b>
                    <p class="text">A ratio, so it survives window resizes.</p>
                    <mj-media-object gap="sm" class="reply" media-size="auto">
                      <mj-avatar slot="media" name="Tom Becker" size="sm"></mj-avatar>
                      <b>Tom Becker</b>
                      <p class="text">Agreed, and keep reading the old pixel value.</p>
                    </mj-media-object>
                  </mj-media-object>
                </mj-media-object>
            """),
            css=_code("""
                .thread { max-inline-size: 36rem; margin: var(--mj-space-4); }
                .text { margin: var(--mj-space-1) 0 var(--mj-space-3); }
                .reply { padding-inline-start: var(--mj-space-2); border-inline-start: 2px solid var(--mj-border); }
            """),
        ),
    ],
    slots=[
        ("", "The text content.", "<p>Text supplied by the slot inspector.</p>"),
        ("media", "Avatar, thumbnail or icon; the region is removed while empty.",
         '<mj-avatar name="Slot Sample" size="md"></mj-avatar>'),
    ],
    properties=[
        ("stacked", "boolean. True while the media is stacked above the content because of `stack-at` (read-only)."),
        ("contentElement", "HTMLElement. The content region in the shadow root (read-only)."),
    ],
    parts=[
        ("root", "The flex row."),
        ("media", "The media region."),
        ("content", "The content region."),
    ],
    css_properties=[
        ("--mj-media-object-gap", "Gap; written by `gap` (default var(--mj-space-4)). Per element: not inherited by nested media objects."),
        ("--mj-media-object-align", "align-items; written by `align` (default flex-start). Per element."),
        ("--mj-media-object-media-size", "Media region width; written by `media-size` (default 3rem). Per element."),
        ("--mj-media-object-direction", "flex-direction of the row (default row)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-hero
# ---------------------------------------------------------------------------

HERO = ComponentDoc(
    tag="mj-hero",
    title="Hero Section",
    group="layout",
    summary="A full-width introductory banner with background, heading, body, actions and media.",
    description=(
        "<p><code>&lt;mj-hero&gt;</code> is the large introductory section of a landing or feature "
        "page. Background layers, bottom to top: <code>bg-color</code> (default the accent colour), "
        "the <code>bg-src</code> image or <code>bg-video</code> video, a dark scrim for contrast "
        "(<code>overlay-opacity</code>, 0-1, default 0.4; only over an image or video), then the "
        "content. If the image or video fails to load, <code>mj-hero-bg-error</code> fires, the scrim "
        "is removed and the colour shows.</p>"
        "<p>Text colour: <code>--mj-text-on-accent</code> on the default accent background; white "
        "(<code>--mj-color-neutral-0</code>) in both themes while the scrim shows. A custom "
        "<code>bg-color</code> does not change the text colour: set <code>--mj-hero-heading-color</code> "
        "and <code>--mj-hero-body-color</code> to keep the contrast (a fixed dark colour needs light text "
        "in the dark theme too).</p>"
        "<p>A background video is muted, looped and inline; it autoplays unless the user prefers "
        "reduced motion, and a pause / play button (part <code>video-toggle</code>) lets the user stop "
        "it. <code>video-poster</code> is shown until it plays.</p>"
        "<p>The heading comes from the <code>heading</code> attribute or <code>slot=\"heading\"</code> "
        "and is an <code>h1</code> by default (<code>heading-level</code> 1-6); with neither no heading "
        "is exposed and the section is not labelled. The content column is centred and at most 72rem "
        "wide; <code>align</code> moves text and actions to the start or end. "
        "<code>min-height</code> defaults to 40vh (in the preview frame vh is the frame height, so the "
        "examples set it in rem); <code>full-height</code> uses 100dvh.</p>"
    ),
    how_to_use=(
        "<p>Set <code>heading</code> (or use the heading slot for rich text), put supporting copy in "
        "<code>slot=\"body\"</code>, buttons in <code>slot=\"actions\"</code> and an illustration or "
        "screenshot in <code>slot=\"media\"</code> (shown below the copy). Use <code>bg-src</code> with "
        "<code>overlay-opacity</code> for photos so the text keeps its contrast, and "
        "<code>heading-level=\"2\"</code> when the page already has an h1.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="heading", description="Heading text (fallback content of the heading slot).", kind="string"),
        AttributeDoc(name="heading-level", description="Level of the heading element.", kind="enum",
                     values=["1", "2", "3", "4", "5", "6"], default="1"),
        AttributeDoc(name="bg-color", description="Background colour (under any image or video).", kind="color"),
        AttributeDoc(name="bg-src", description="Background image URL. Script URLs are rejected, and data: URLs are accepted only for raster images (png, gif, jpeg, webp, avif, bmp), not SVG.",
                     kind="string"),
        AttributeDoc(name="bg-video", description="Background video URL; muted, looped, autoplays unless reduced motion.",
                     kind="string"),
        AttributeDoc(name="video-poster", description="Poster image of the background video.", kind="string"),
        AttributeDoc(name="overlay-opacity", description="Opacity 0-1 of the scrim over an image or video.", kind="number",
                     default="0.4"),
        AttributeDoc(name="align", description="Horizontal alignment of the content.", kind="enum",
                     values=["center", "start", "end"], default="center"),
        AttributeDoc(name="min-height", description="Minimum block size of the section (any CSS length).", kind="string",
                     values=["16rem", "24rem", "40vh"], default="40vh"),
        AttributeDoc(name="full-height", description="Minimum height of 100dvh (the frame height in this preview).", kind="boolean"),
    ],
    events=[
        ("mj-hero-bg-error", "The background image or video failed to load; the colour shows instead.", "{ src: string }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A centred hero on the default accent background with body copy and two actions. The "
                "tertiary button is transparent, so its text is set to <code>--mj-text-on-accent</code> "
                "through <code>--mj-button-color</code> (a plain <code>color</code> on the host does not "
                "reach the button's label). Try <code>align</code>, <code>bg-color</code> and "
                "<code>heading-level</code> in Controls, and the <b>320</b> preset: the actions wrap.</p>"
            ),
            html=_code("""
                <mj-hero heading="Build internal tools in days, not months" min-height="18rem">
                  <p slot="body" class="hero-copy">Accessible, themeable web components on native custom elements,
                    with layouts, data tables and charts included.</p>
                  <mj-button slot="actions" variant="secondary">Read the guide</mj-button>
                  <mj-button slot="actions" variant="tertiary" class="on-accent">See examples</mj-button>
                </mj-hero>
            """),
            css=_code("""
                .hero-copy { max-inline-size: 42ch; margin: 0 auto; font-size: var(--mj-font-size-lg); }
                .on-accent { --mj-button-color: var(--mj-text-on-accent); --mj-button-bg: transparent; }
                .on-accent:hover { --mj-button-bg: color-mix(in srgb, var(--mj-text-on-accent) 16%, transparent); }
            """),
        ),
        ComponentExample(
            key="image",
            title="Background image and media",
            description=(
                "<p><code>bg-src</code> with <code>overlay-opacity=\"0.55\"</code>, <code>align=\"start\"</code>, "
                "<code>heading-level=\"2\"</code>, a rich heading slot and a screenshot in the media slot. "
                "Change <code>overlay-opacity</code> to see the scrim. Try the <b>320</b> preset.</p>"
            ),
            html=_code(f"""
                <mj-hero bg-src="{IMG_HERO}" overlay-opacity="0.55" align="start" heading-level="2" min-height="24rem">
                  <span slot="heading">Plan routes <em class="hl">together</em></span>
                  <p slot="body" class="copy">Share trails with your club, vote on the next outing and download offline maps.</p>
                  <mj-button slot="actions" variant="primary">Start free</mj-button>
                  <img slot="media" src="{IMG_APP}" alt="Route planner screenshot" class="shot" />
                </mj-hero>
            """),
            css=_code("""
                .copy { max-inline-size: 40ch; margin: 0; font-size: var(--mj-font-size-lg); }
                .hl { font-style: normal; text-decoration: underline; text-decoration-thickness: 0.15em; }
                .shot { display: block; inline-size: min(100%, 28rem); border-radius: var(--mj-radius-md); box-shadow: var(--mj-elevation-3); }
            """),
        ),
        ComponentExample(
            key="error",
            title="Missing background (events)",
            description=(
                "<p>The first hero's <code>bg-video</code> and the second hero's <code>bg-src</code> point "
                "at files that do not exist: each fires <code>mj-hero-bg-error</code> (see Events) and "
                "falls back to its <code>bg-color</code> without the scrim. The video hero still shows the "
                "pause / play button. Both colours are dark in either theme, so the text is set light with "
                "<code>--mj-hero-heading-color</code> / <code>--mj-hero-body-color</code>.</p>"
            ),
            html=_code("""
                <mj-hero id="video-hero" heading="Product tour" bg-video="/static/media/missing-tour.mp4"
                  bg-color="#1e3a5f" min-height="12rem" heading-level="2">
                  <p slot="body" class="copy">The video could not be loaded, so the colour shows.</p>
                </mj-hero>
                <mj-hero id="image-hero" heading="Summer meetup" bg-src="/static/media/missing-banner.jpg"
                  bg-color="#5b2a86" min-height="10rem" heading-level="2" align="end">
                </mj-hero>
            """),
            css=_code("""
                #video-hero, #image-hero {
                  --mj-hero-heading-color: var(--mj-color-neutral-0);
                  --mj-hero-body-color: var(--mj-color-neutral-0);
                }
                .copy { margin: 0; }
                #image-hero { margin-block-start: var(--mj-space-4); }
            """),
            script=_code("""
                for (const id of ["video-hero", "image-hero"]) {
                  document.getElementById(id).addEventListener("mj-hero-bg-error", (event) => {
                    mjSandbox.log("background failed", { hero: id, src: event.detail.src })
                  })
                }
                // The first attempt may have failed before this script ran: setting the
                // attribute again retries the load, so the listener sees the error.
                const imageHero = document.getElementById("image-hero")
                imageHero.setAttribute("bg-src", imageHero.getAttribute("bg-src"))
            """),
        ),
        ComponentExample(
            key="in-page",
            title="Hero in a page layout",
            description=(
                "<p>The hero as the first band of a page built from <code>mj-surface</code> and "
                "<code>mj-grid</code>: a full-width hero, then a centred feature grid under its own "
                "<code>h2</code>. The dark green <code>bg-color</code> is the same in both themes, so the "
                "text is set light with <code>--mj-hero-heading-color</code> / "
                "<code>--mj-hero-body-color</code>. Try <b>1024</b>, <b>768</b> and <b>320</b>.</p>"
            ),
            html=_code("""
                <mj-hero heading="Everything your team needs" min-height="16rem" bg-color="#14532d" class="brand-hero">
                  <p slot="body" class="copy">One workspace for planning, building and shipping.</p>
                  <mj-button slot="actions" variant="secondary">Get started</mj-button>
                </mj-hero>
                <mj-surface max-width="60rem" padding="lg" class="features">
                  <h2 class="features-title">From plan to production</h2>
                  <mj-grid columns="3" min-col-width="13rem" gap="md">
                    <mj-card heading="Plan" elevation="outlined"><p>Roadmaps and milestones.</p></mj-card>
                    <mj-card heading="Build" elevation="outlined"><p>Pipelines with fast feedback.</p></mj-card>
                    <mj-card heading="Ship" elevation="outlined"><p>Promotions with approvals.</p></mj-card>
                  </mj-grid>
                </mj-surface>
            """),
            css=_code("""
                .brand-hero {
                  --mj-hero-heading-color: var(--mj-color-neutral-0);
                  --mj-hero-body-color: var(--mj-color-neutral-0);
                }
                .copy { margin: 0; font-size: var(--mj-font-size-lg); }
                .features-title { margin: 0 0 var(--mj-space-4); font-size: var(--mj-font-size-xl); }
            """),
        ),
    ],
    slots=[
        ("heading", "Rich heading content; replaces the `heading` attribute text.", "<span>Slotted <em>heading</em></span>"),
        ("body", "Supporting copy under the heading.", "<p>Body copy supplied by the slot inspector.</p>"),
        ("actions", "Call-to-action buttons (a wrapping row).",
         '<mj-button variant="secondary">Primary action</mj-button>'),
        ("media", "Illustration or screenshot below the copy.",
         f'<img src="{IMG_APP}" alt="Screenshot" style="max-inline-size:20rem;border-radius:8px" />'),
    ],
    properties=[
        ("videoElement", "HTMLVideoElement | null. The background video while `bg-video` is set (read-only)."),
    ],
    parts=[
        ("root", "The section."),
        ("background", "The image / video layer."),
        ("overlay", "The scrim (only over an image or video)."),
        ("content", "The centred content column."),
        ("heading", "The heading element."),
        ("body", "Body region."),
        ("actions", "Actions row."),
        ("media", "Media region."),
        ("video-toggle", "The pause / play button of a background video."),
    ],
    css_properties=[
        ("--mj-hero-bg-color", "Background colour; written by `bg-color` (default var(--mj-accent))."),
        ("--mj-hero-min-height", "Minimum height; written by `min-height` (default 40vh)."),
        ("--mj-hero-overlay-color", "Scrim colour (default #000000)."),
        ("--mj-hero-overlay-opacity", "Scrim opacity; written by `overlay-opacity` (default 0.4)."),
        ("--mj-hero-content-max-width", "Maximum width of the content column (default 72rem)."),
        ("--mj-hero-padding-block", "Block padding of the content (default var(--mj-space-8))."),
        ("--mj-hero-heading-color", "Heading colour (default var(--mj-text-on-accent); var(--mj-color-neutral-0) over the scrim of an image or video)."),
        ("--mj-hero-body-color", "Body colour (default var(--mj-text-on-accent); var(--mj-color-neutral-0) over the scrim of an image or video)."),
        ("--mj-hero-actions-gap", "Gap between actions (default var(--mj-space-3))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-empty-state
# ---------------------------------------------------------------------------

EMPTY_STATE = ComponentDoc(
    tag="mj-empty-state",
    title="Empty State",
    group="layout",
    summary="A no-content message with an illustration, heading, description and actions.",
    description=(
        "<p><code>&lt;mj-empty-state&gt;</code> gives zero-result views a consistent structure: an "
        "illustration, a heading, a description and recovery actions, centred in a column at most "
        "24rem wide. Each region is shown only when it has content: the illustration when something is "
        "slotted (and <code>show-illustration</code> is not \"false\"), the heading when the "
        "<code>heading</code> attribute or slot provides text, the description and the actions when "
        "something is slotted into them; an empty region takes no room, so the spacing between the "
        "regions stays even. The heading is an <code>h3</code> by default (<code>heading-level</code> 1-6). "
        "<code>compact</code> reduces padding, gap, illustration and heading size for small "
        "containers such as side panels, table bodies and feeds.</p>"
    ),
    how_to_use=(
        "<p>Place it where the content would be: inside the table, list, feed (its "
        "<code>slot=\"empty\"</code>) or search results area. Set <code>heading</code>, put a short "
        "explanation in <code>slot=\"description\"</code> and one or two actions in "
        "<code>slot=\"actions\"</code>; add an SVG to <code>slot=\"illustration\"</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="heading", description="Main message (fallback of the heading slot).", kind="string"),
        AttributeDoc(name="heading-level", description="Level of the heading element.", kind="enum",
                     values=["1", "2", "3", "4", "5", "6"], default="3"),
        AttributeDoc(name="compact", description="Smaller padding, gap, illustration and heading.", kind="boolean"),
        AttributeDoc(name="show-illustration", description="`false` hides the illustration region.", kind="boolean", default="true"),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="No search results",
            description=(
                "<p>Illustration, heading, description and two actions. Toggle <code>compact</code> and "
                "<code>show-illustration</code>, or switch slots off in Slots: each region disappears "
                "with its content.</p>"
            ),
            html=_code(f"""
                <mj-empty-state heading="No results for &ldquo;dock layot&rdquo;">
                  {ICON_SEARCH}
                  <p slot="description">Check the spelling or try a broader term. Filters for status and owner
                    are still applied.</p>
                  <mj-button slot="actions" variant="secondary">Clear filters</mj-button>
                  <mj-button slot="actions" variant="tertiary">Search all projects</mj-button>
                </mj-empty-state>
            """),
            css="mj-empty-state svg { color: var(--mj-text-muted); }",
        ),
        ComponentExample(
            key="in-context",
            title="Inside a panel and a table",
            description=(
                "<p>Where it belongs: a compact empty state in a dashboard panel next to a populated one "
                "(try the <b>320</b> preset), and one inside an empty table body.</p>"
            ),
            html=_code(f"""
                <mj-grid columns="2" min-col-width="15rem" gap="md" class="panels">
                  <mj-card heading="Open incidents" elevation="outlined">
                    <mj-empty-state heading="All clear" compact>
                      <p slot="description">No incidents in the last 7 days.</p>
                    </mj-empty-state>
                  </mj-card>
                  <mj-card heading="Deploys" elevation="outlined">
                    <ul class="deploys"><li>web 4.2.0 &middot; 10:42</li><li>api 2.8.1 &middot; 09:15</li></ul>
                  </mj-card>
                </mj-grid>
                <table class="tbl">
                  <thead><tr><th>Name</th><th>Owner</th><th>Updated</th></tr></thead>
                  <tbody><tr><td colspan="3">
                    <mj-empty-state heading="No projects yet" compact>
                      {ICON_FOLDER}
                      <mj-button slot="actions" size="sm" variant="primary">Create project</mj-button>
                    </mj-empty-state>
                  </td></tr></tbody>
                </table>
            """),
            css=_code("""
                .panels { padding: var(--mj-space-4); }
                .deploys { margin: 0; padding-inline-start: var(--mj-space-5); }
                .tbl { inline-size: calc(100% - 2 * var(--mj-space-4)); margin: 0 var(--mj-space-4) var(--mj-space-4); border-collapse: collapse; }
                .tbl th { text-align: start; padding: var(--mj-space-2); border-block-end: 2px solid var(--mj-border); }
                .tbl svg { color: var(--mj-text-muted); }
            """),
        ),
        ComponentExample(
            key="slots",
            title="Heading slot and recovery",
            description=(
                "<p>A rich heading in <code>slot=\"heading\"</code> with <code>heading-level=\"2\"</code>. "
                "<b>Create project</b> replaces the empty state with a list, and <b>Reset</b> brings it "
                "back; the script logs <code>hasActions</code>.</p>"
            ),
            html=_code(f"""
                <div id="projects" class="area">
                  <mj-empty-state id="no-projects" heading-level="2">
                    {ICON_FOLDER}
                    <span slot="heading">Start your <em>first</em> project</span>
                    <p slot="description">Projects group repositories, pipelines and environments.</p>
                    <mj-button slot="actions" id="create" variant="primary">Create project</mj-button>
                  </mj-empty-state>
                </div>
                <mj-button id="reset" size="sm" variant="secondary" class="reset">Reset</mj-button>
            """),
            css=_code("""
                .area { margin: var(--mj-space-4); border: 1px dashed var(--mj-border-strong); border-radius: var(--mj-radius-md); }
                .area svg { color: var(--mj-accent); }
                .reset { margin: 0 var(--mj-space-4) var(--mj-space-4); }
            """),
            script=_code("""
                const area = document.getElementById("projects")
                const empty = document.getElementById("no-projects")
                mjSandbox.log("empty state", { hasActions: empty.hasActions })
                document.getElementById("create").addEventListener("click", () => {
                  const list = document.createElement("ul")
                  list.innerHTML = "<li>Atlas (just now)</li>"
                  empty.replaceWith(list)
                  mjSandbox.log("created", { project: "Atlas" })
                })
                document.getElementById("reset").addEventListener("click", () => {
                  area.replaceChildren(empty)
                })
            """),
        ),
    ],
    slots=[
        ("illustration", "Icon or illustration above the heading.",
         '<svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true"><circle cx="32" cy="32" r="26" fill="currentColor"/></svg>'),
        ("heading", "Rich heading content; replaces the `heading` attribute.", "<span>Slotted heading</span>"),
        ("description", "Explanation under the heading.", "<p>Description supplied by the slot inspector.</p>"),
        ("actions", "Recovery actions.", '<mj-button variant="secondary">Try again</mj-button>'),
    ],
    properties=[
        ("hasActions", "boolean. Whether anything is slotted into `actions` (read-only)."),
    ],
    parts=[
        ("root", "The centred column."),
        ("illustration", "Illustration region."),
        ("heading", "The heading element."),
        ("description", "Description region."),
        ("actions", "Actions row."),
    ],
    css_properties=[
        ("--mj-empty-state-padding", "Padding (default var(--mj-space-8))."),
        ("--mj-empty-state-gap", "Gap between regions (default var(--mj-space-4))."),
        ("--mj-empty-state-max-width", "Maximum width of the column (default 24rem)."),
        ("--mj-empty-state-illustration-size", "Illustration box size (default 5rem)."),
        ("--mj-empty-state-heading-color", "Heading colour (default var(--mj-text))."),
        ("--mj-empty-state-description-color", "Description colour (default var(--mj-text-muted))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-skeleton
# ---------------------------------------------------------------------------

SKELETON = ComponentDoc(
    tag="mj-skeleton",
    title="Skeleton Loader",
    group="layout",
    summary="A shimmering placeholder shaped like the content that is loading.",
    description=(
        "<p><code>&lt;mj-skeleton&gt;</code> draws a placeholder in the shape of content that has not "
        "loaded yet: <code>rectangle</code> (default; images, blocks), <code>circle</code> (avatars; as "
        "tall as it is wide, whatever unit the width uses) and <code>text</code> (<code>lines</code> "
        "rows, the last one shorter; <code>height</code> does not apply, the line height follows the "
        "font size). A shimmer sweeps across unless <code>animated=\"false\"</code> or the user prefers "
        "reduced motion.</p>"
        "<p>The shapes are hidden from assistive technology (the host itself is not). A placeholder is "
        "usually built from several skeletons, so only <em>one</em> connected skeleton (the first one "
        "without <code>announce=\"false\"</code>) carries a polite status region with the "
        "<code>loading-label</code>; when it goes away the next one takes over.</p>"
    ),
    how_to_use=(
        "<p>Compose skeletons in the layout of the real content (a stack, a media object, a card) and "
        "replace them when the data arrives. Match <code>width</code> / <code>height</code> to the "
        "expected content; set <code>loading-label</code> on the first one to say what is loading.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="variant", description="Shape of the placeholder.", kind="enum",
                     values=["rectangle", "circle", "text"], default="rectangle"),
        AttributeDoc(name="width", description="Inline size (CSS length).", kind="string",
                     values=["100%", "60%", "3rem", "12rem"], default="100%"),
        AttributeDoc(name="height", description="Block size (CSS length); ignored by circle and text.", kind="string",
                     values=["1rem", "4rem", "8rem"], default="1rem"),
        AttributeDoc(name="lines", description="Number of rows of the text variant (1-50).", kind="number", default="1"),
        AttributeDoc(name="radius", description="Corner radius (CSS length).", kind="string",
                     values=["0", "4px", "var(--mj-radius-lg)"]),
        AttributeDoc(name="animated", description="`false` switches the shimmer off.", kind="boolean", default="true"),
        AttributeDoc(name="loading-label", description="Text of the status announcement (announcing skeleton only).",
                     kind="string", default="Loading"),
        AttributeDoc(name="announce", description="`false` keeps this skeleton from carrying the announcement.",
                     kind="boolean", default="true"),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="Profile placeholder",
            description=(
                "<p>A circle, two text lines and a picture block composed like the profile they stand in "
                "for. Only the first skeleton announces \"Loading profile\". Change the first skeleton's "
                "<code>variant</code>, <code>width</code> or <code>animated</code> in Controls.</p>"
            ),
            html=_code("""
                <mj-stack class="demo-skeletons" gap="md">
                  <mj-stack direction="horizontal" gap="sm" align="center">
                    <mj-skeleton variant="circle" width="3rem" loading-label="Loading profile"></mj-skeleton>
                    <mj-stack gap="xs" class="grow">
                      <mj-skeleton variant="text" width="60%"></mj-skeleton>
                      <mj-skeleton variant="text" width="35%"></mj-skeleton>
                    </mj-stack>
                  </mj-stack>
                  <mj-skeleton height="8rem" radius="var(--mj-radius-md)"></mj-skeleton>
                  <mj-skeleton variant="text" lines="3"></mj-skeleton>
                </mj-stack>
            """),
            css=_code("""
                .demo-skeletons { max-inline-size: 24rem; margin: var(--mj-space-4); }
                .grow { flex: 1 1 auto; }
            """),
        ),
        ComponentExample(
            key="variants",
            title="Variants and sizes",
            description=(
                "<p>Rectangles of different heights and radii, circles in rem and percent widths, and "
                "text blocks of one to four lines (the text size follows the font size).</p>"
            ),
            html=_code("""
                <mj-grid columns="3" min-col-width="12rem" gap="lg" class="variants" align-items="start">
                  <mj-stack gap="sm">
                    <b>rectangle</b>
                    <mj-skeleton height="1rem"></mj-skeleton>
                    <mj-skeleton height="3rem" radius="0"></mj-skeleton>
                    <mj-skeleton height="5rem" radius="var(--mj-radius-lg)"></mj-skeleton>
                  </mj-stack>
                  <mj-stack gap="sm">
                    <b>circle</b>
                    <mj-stack direction="horizontal" gap="sm" align="center">
                      <mj-skeleton variant="circle" width="1.5rem"></mj-skeleton>
                      <mj-skeleton variant="circle" width="2.5rem"></mj-skeleton>
                      <mj-skeleton variant="circle" width="4rem"></mj-skeleton>
                      <mj-skeleton variant="circle" width="20%"></mj-skeleton>
                    </mj-stack>
                  </mj-stack>
                  <mj-stack gap="sm">
                    <b>text</b>
                    <mj-skeleton variant="text"></mj-skeleton>
                    <mj-skeleton variant="text" lines="2"></mj-skeleton>
                    <mj-skeleton variant="text" lines="4" class="large"></mj-skeleton>
                  </mj-stack>
                </mj-grid>
            """),
            css=".variants { padding: var(--mj-space-4); }\n.large { font-size: var(--mj-font-size-lg); }",
        ),
        ComponentExample(
            key="loading",
            title="Swap in real content",
            description=(
                "<p>A card grid shows skeleton cards for 1.5 seconds, then the script replaces them with "
                "real cards. <b>Reload</b> repeats it. Try the <b>320</b> preset: the placeholders reflow "
                "like the cards.</p>"
            ),
            html=_code("""
                <mj-button id="reload" size="sm" variant="secondary" class="reload">Reload</mj-button>
                <mj-grid id="team-grid" columns="3" min-col-width="12rem" gap="md" class="team"></mj-grid>
            """),
            css=_code("""
                .reload { margin: var(--mj-space-4) var(--mj-space-4) 0; }
                .team { padding: var(--mj-space-4); }
                .ph { display: flex; flex-direction: column; gap: var(--mj-space-2); padding: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
            """),
            script=_code("""
                const grid = document.getElementById("team-grid")
                const people = [["Ada Lovelace", "Platform"], ["Grace Hopper", "Compilers"], ["Alan Turing", "Research"]]
                function showPlaceholders() {
                  grid.replaceChildren()
                  for (let index = 0; index < people.length; index = index + 1) {
                    const holder = document.createElement("div")
                    holder.className = "ph"
                    holder.innerHTML = '<mj-skeleton variant="circle" width="2.5rem"></mj-skeleton>' +
                      '<mj-skeleton variant="text" width="70%"></mj-skeleton><mj-skeleton variant="text" lines="2"></mj-skeleton>'
                    if (index === 0) { holder.firstElementChild.setAttribute("loading-label", "Loading team") }
                    grid.append(holder)
                  }
                  mjSandbox.log("loading", { placeholders: people.length })
                  setTimeout(showPeople, 1500)
                }
                function showPeople() {
                  grid.replaceChildren()
                  for (const [name, team] of people) {
                    const card = document.createElement("mj-card")
                    card.setAttribute("heading", name)
                    card.setAttribute("subheading", team)
                    card.setAttribute("elevation", "outlined")
                    const avatar = document.createElement("mj-avatar")
                    avatar.setAttribute("name", name)
                    card.append(avatar)
                    grid.append(card)
                  }
                  mjSandbox.log("loaded", { cards: people.length })
                }
                document.getElementById("reload").addEventListener("click", showPlaceholders)
                showPlaceholders()
            """),
        ),
        ComponentExample(
            key="custom-styling",
            title="Static and custom colours",
            description=(
                "<p><code>animated=\"false\"</code> placeholders (for platforms that show loading another "
                "way) and themed ones using <code>--mj-skeleton-bg</code>, "
                "<code>--mj-skeleton-shimmer-color</code> and <code>--mj-skeleton-duration</code>. The "
                "second group uses <code>announce=\"false\"</code>.</p>"
            ),
            html=_code("""
                <mj-stack gap="sm" class="group">
                  <mj-skeleton animated="false" height="2rem"></mj-skeleton>
                  <mj-skeleton animated="false" variant="text" lines="2"></mj-skeleton>
                </mj-stack>
                <mj-stack gap="sm" class="group themed">
                  <mj-skeleton announce="false" height="2rem"></mj-skeleton>
                  <mj-skeleton announce="false" variant="text" lines="2"></mj-skeleton>
                </mj-stack>
            """),
            css=_code("""
                .group { max-inline-size: 22rem; margin: var(--mj-space-4); }
                .themed { --mj-skeleton-bg: var(--mj-color-accent-100); --mj-skeleton-shimmer-color: var(--mj-color-accent-300); --mj-skeleton-duration: 0.8s; }
            """),
        ),
    ],
    slots=[],
    properties=[
        ("announcing", "boolean. True for the one skeleton that carries the loading announcement (read-only)."),
        ("animating", "boolean. Whether the shimmer runs (false with animated=false or reduced motion; read-only)."),
    ],
    parts=[
        ("root", "The shape container (aria-hidden)."),
        ("shimmer", "The moving highlight (one per text line)."),
    ],
    css_properties=[
        ("--mj-skeleton-width", "Inline size; written by `width` (default 100%)."),
        ("--mj-skeleton-height", "Block size; written by `height` (default 1rem)."),
        ("--mj-skeleton-radius", "Corner radius; written by `radius` (default var(--mj-radius-sm))."),
        ("--mj-skeleton-bg", "Placeholder colour (default var(--mj-bg-muted))."),
        ("--mj-skeleton-shimmer-color", "Highlight colour (default var(--mj-bg-subtle))."),
        ("--mj-skeleton-duration", "One shimmer sweep (default 1.5s)."),
        ("--mj-skeleton-line-height", "Height of a text line (default 1em)."),
        ("--mj-skeleton-line-gap", "Gap between text lines (default 0.5em)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-divider
# ---------------------------------------------------------------------------

DIVIDER = ComponentDoc(
    tag="mj-divider",
    title="Divider",
    group="layout",
    summary="A visual or semantic separator between adjacent content regions.",
    description=(
        "<p><code>&lt;mj-divider&gt;</code> draws a horizontal or vertical line. By default it is a "
        "semantic separator (<code>role=separator</code> with <code>aria-orientation</code>, named by "
        "its label); <code>decorative</code> makes it purely visual (hidden from assistive "
        "technology).</p>"
        "<p>A label comes from the <code>label</code> attribute or from <code>slot=\"label\"</code> "
        "content (the slot wins; the text is never parsed as HTML); with a label the line is drawn on "
        "both sides of it, in either orientation. A vertical divider fills the height of a stretching "
        "flex or grid row and is at least one line tall elsewhere.</p>"
    ),
    how_to_use=(
        "<p>Place <code>&lt;mj-divider&gt;</code> between siblings. In a horizontal flex row (a toolbar, "
        "an <code>mj-stack direction=\"horizontal\"</code>) use <code>orientation=\"vertical\"</code>. "
        "Use a label for \"or\" separators in sign-in forms and for date separators in lists. Pick "
        "<code>variant</code>, <code>thickness</code> and <code>spacing</code> (block margin, or inline "
        "margin when vertical).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="orientation", description="Direction of the line.", kind="enum",
                     values=["horizontal", "vertical"], default="horizontal"),
        AttributeDoc(name="label", description="Short text on the line (the label slot takes precedence).", kind="string",
                     values=["or", "Today", "Older"]),
        AttributeDoc(name="decorative", description="Purely visual: role=none, aria-hidden.", kind="boolean"),
        AttributeDoc(name="variant", description="Line style.", kind="enum",
                     values=["solid", "dashed", "dotted", "double"], default="solid"),
        AttributeDoc(name="thickness", description="Line weight: 1px, 2px or 4px.", kind="enum",
                     values=["thin", "medium", "thick"], default="thin"),
        AttributeDoc(name="spacing", description="Margin around the line (block axis; inline axis when vertical).", kind="enum",
                     values=["none", "xs", "sm", "md", "lg"], default="md"),
    ],
    events=[],
    examples=[
        ComponentExample(
            key="basic",
            title="Sign-in form",
            description=(
                "<p>A labelled \"or\" divider between two sign-in methods, and a plain divider above the "
                "footer. Change the first divider's <code>variant</code>, <code>thickness</code>, "
                "<code>spacing</code> and <code>label</code> in Controls.</p>"
            ),
            html=_code("""
                <mj-stack class="demo-signin" gap="sm">
                  <mj-button variant="secondary">Continue with single sign-on</mj-button>
                  <mj-divider label="or" spacing="md"></mj-divider>
                  <mj-text-field label="Email" type="email" placeholder="you@example.com"></mj-text-field>
                  <mj-password-field label="Password"></mj-password-field>
                  <mj-button variant="primary">Sign in</mj-button>
                  <mj-divider spacing="sm"></mj-divider>
                  <small>No account? <a href="#signup">Create one</a></small>
                </mj-stack>
            """),
            css=".demo-signin { max-inline-size: 22rem; margin: var(--mj-space-4); }",
        ),
        ComponentExample(
            key="vertical",
            title="Vertical in a toolbar",
            description=(
                "<p><code>orientation=\"vertical\"</code> dividers between button groups of a toolbar row; "
                "they stretch to the row height. The second row has a labelled vertical divider. Try the "
                "<b>320</b> preset: the row wraps.</p>"
            ),
            html=_code("""
                <mj-stack direction="horizontal" gap="xs" align="stretch" wrap class="tools">
                  <mj-toggle-button>Bold</mj-toggle-button>
                  <mj-toggle-button>Italic</mj-toggle-button>
                  <mj-divider orientation="vertical" spacing="xs" decorative></mj-divider>
                  <mj-button size="sm" variant="tertiary">Bullets</mj-button>
                  <mj-button size="sm" variant="tertiary">Numbers</mj-button>
                  <mj-divider orientation="vertical" spacing="xs" decorative></mj-divider>
                  <mj-button size="sm" variant="tertiary">Link</mj-button>
                </mj-stack>
                <mj-stack direction="horizontal" gap="none" align="stretch" class="compare">
                  <div class="side">Monthly<br><b>$12</b></div>
                  <mj-divider orientation="vertical" label="vs"></mj-divider>
                  <div class="side">Yearly<br><b>$120</b></div>
                </mj-stack>
            """),
            css=_code("""
                .tools { margin: var(--mj-space-4); padding: var(--mj-space-1); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .compare { margin: var(--mj-space-4); block-size: 8rem; }
                .side { flex: 1 1 0; display: grid; place-content: center; text-align: center; }
            """),
        ),
        ComponentExample(
            key="variants",
            title="Variants, thickness, spacing",
            description=(
                "<p>All line styles and weights, and the spacing steps from <code>none</code> to "
                "<code>lg</code> between grey bars.</p>"
            ),
            html=_code("""
                <div class="list">
                  <mj-divider label="solid, thin"></mj-divider>
                  <mj-divider variant="dashed" thickness="medium" label="dashed, medium"></mj-divider>
                  <mj-divider variant="dotted" thickness="thick" label="dotted, thick"></mj-divider>
                  <mj-divider variant="double" thickness="thick" label="double, thick"></mj-divider>
                  <div class="bar"></div><mj-divider spacing="none" decorative></mj-divider><div class="bar"></div>
                  <mj-divider spacing="xs" decorative></mj-divider><div class="bar"></div>
                  <mj-divider spacing="sm" decorative></mj-divider><div class="bar"></div>
                  <mj-divider spacing="lg" decorative></mj-divider><div class="bar"></div>
                </div>
            """),
            css=_code("""
                .list { max-inline-size: 30rem; margin: var(--mj-space-4); }
                .bar { block-size: 0.5rem; background: var(--mj-bg-muted); border-radius: var(--mj-radius-sm); }
            """),
        ),
        ComponentExample(
            key="slots",
            title="Label slot",
            description=(
                "<p>Date separators in an activity list using <code>slot=\"label\"</code> with an icon "
                "and text; the slotted text also names the separator. Switch the slot off in Slots: the "
                "line runs the full width.</p>"
            ),
            html=_code("""
                <div class="activity">
                  <mj-divider>
                    <span slot="label" class="label"><svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="currentColor"/></svg> Today</span>
                  </mj-divider>
                  <p>Priya merged <b>Fix dock band sizes</b>.</p>
                  <mj-divider label="Yesterday"></mj-divider>
                  <p>Tom opened <b>Split pane persist format</b>.</p>
                </div>
            """),
            css=_code("""
                .activity { max-inline-size: 30rem; margin: var(--mj-space-4); }
                .label { display: inline-flex; align-items: center; gap: var(--mj-space-1); color: var(--mj-accent); }
            """),
        ),
    ],
    slots=[
        ("label", "Rich label content; replaces the `label` attribute.", "<span>Slotted label</span>"),
    ],
    properties=[
        ("isDecorative", "boolean. Whether `decorative` is set (read-only)."),
    ],
    parts=[
        ("root", "The separator element."),
        ("line-start", "The line before the label (the whole line when unlabelled)."),
        ("label", "The label container."),
        ("line-end", "The line after the label."),
    ],
    css_properties=[
        ("--mj-divider-color", "Line colour (default var(--mj-border))."),
        ("--mj-divider-thickness", "Line weight; written by `thickness` (default 1px)."),
        ("--mj-divider-variant", "Line style; written by `variant` (default solid)."),
        ("--mj-divider-spacing", "Margin; written by `spacing` (default var(--mj-space-4))."),
        ("--mj-divider-label-gap", "Gap between label and lines (default var(--mj-space-3))."),
        ("--mj-divider-label-color", "Label colour (default var(--mj-text-muted))."),
        ("--mj-divider-label-bg", "Label background (default transparent)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-dock-layout
# ---------------------------------------------------------------------------

DOCK_LAYOUT = ComponentDoc(
    tag="mj-dock-layout",
    title="Dock Layout",
    group="layout",
    summary="An app-shell container that docks its children to its edges (top, bottom, start, end) and fills the rest.",
    description=(
        "<p><code>&lt;mj-dock-layout&gt;</code> arranges its children by their <code>dock</code> "
        "attribute, like a WPF DockPanel. In DOM order, each child with <code>dock=\"top\"</code>, "
        "<code>bottom</code>, <code>start</code> or <code>end</code> takes a band along that edge of the "
        "space that is still free; <code>dock=\"fill\"</code> children share the rectangle that is left, "
        "side by side. <code>start</code> / <code>end</code> follow the text direction (they swap in "
        "RTL). Any element can be docked: mj-* components (toolbar, side nav, status bar, split pane, "
        "scroll area, another dock layout) and plain elements alike.</p>"
        "<p><b>Sizing contract.</b> A band keeps the size its author gave it along the axis it consumes "
        "(<code>height</code> for top / bottom, <code>width</code> for start / end, inline or from a "
        "stylesheet), or the size of its content; the layout stretches it across the other axis. A fill "
        "child is sized on both axes to the remaining rectangle, so a nested "
        "<code>&lt;mj-dock-layout dock=\"fill\"&gt;</code> or <code>&lt;mj-split-pane "
        "dock=\"fill\"&gt;</code> gets exactly that space. Child margins are honoured, padding on the "
        "layout insets every band, and the <code>gap</code> attribute (or the CSS <code>gap</code> "
        "property) separates the bands. A child that is <code>hidden</code> / "
        "<code>display: none</code> takes no space. The inline styles the engine writes are recorded and "
        "restored when a child is undocked.</p>"
        "<p>The layout re-runs when the container or a docked child changes size, when a child is "
        "added, removed, hidden or shown, and when the <code>dock</code> attribute of any child changes; "
        "after each pass that lays the children out a non-bubbling <code>mj-layout</code> event fires "
        "(a pass that finds the layout not rendered, 0 &times; 0 inside <code>display: none</code>, "
        "changes nothing and fires nothing). The host fills its container (<code>100%</code> on both "
        "axes) and clips overflow, so give it, or its parent, a height. <code>disabled</code> has no "
        "meaning for the layout and does not block pointer input to its content.</p>"
        "<p><b>Anchoring.</b> Children <em>without</em> <code>dock</code> stay in normal flow under the "
        "bands; the layout is a positioning context, so mj-* children with the universal "
        "<code>anchor</code> attribute (top-start, top, top-end, start, center, end, bottom-start, "
        "bottom, bottom-end, stretch) are pinned to its corners or edges, inset by "
        "<code>--mj-anchor-inset</code>, above the bands (<code>--mj-layer-docked</code>).</p>"
    ),
    how_to_use=(
        "<p>Give <code>&lt;mj-dock-layout&gt;</code> a height. Add the bands in the order they should "
        "claim space (usually the top bar, then the status bar, then the side panels) and the content "
        "last with <code>dock=\"fill\"</code>. Size bands with ordinary CSS width / height. Make the "
        "fill child a scroll container (an <code>mj-scroll-area</code>) or a nested layout. Change a "
        "child's <code>dock</code> at run time to re-dock it (for example on narrow screens), and call "
        "<code>requestLayout()</code> after changes the layout cannot observe.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="gap", description="Space between the bands and the fill area (or set the CSS gap / --mj-dock-gap).",
                     kind="enum", values=["none", "xs", "sm", "md", "lg", "xl"], default="none"),
        AttributeDoc(name="dock", description="Set on CHILDREN: the edge the child consumes or `fill`. On the layout itself it docks the layout into an outer dock layout.",
                     kind="string", values=["top", "bottom", "start", "end", "fill"]),
        AttributeDoc(name="anchor", description="Universal mj-* attribute for undocked children: pins the child to a corner or edge of the layout.",
                     kind="string", values=["top-start", "top", "top-end", "start", "center", "end", "bottom-start", "bottom", "bottom-end", "stretch"]),
    ],
    events=[
        ("mj-layout", "Non-bubbling; fires after every layout pass that laid the children out (not while the layout is not rendered, 0 x 0).", "{ container: MjDockLayout }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="App shell",
            description=(
                "<p>Docked mj-* components: an <code>mj-toolbar</code> on top, an "
                "<code>mj-status-bar</code> at the bottom, an <code>mj-side-nav</code> at the start (its "
                "own 13rem width is kept) and an <code>mj-scroll-area</code> as the fill that scrolls on "
                "its own. Try the <b>768</b> and <b>320</b> presets: the bands keep their sizes and the "
                "fill shrinks (see the Responsive example for re-docking). Switch <b>Dir</b> to "
                "<b>RTL</b>: the navigation moves to the right.</p>"
            ),
            html=_code("""
                <mj-dock-layout class="demo-shell">
                  <mj-toolbar dock="top" label="Main actions" class="shell-top">
                    <mj-button size="sm" variant="primary">New report</mj-button>
                    <mj-button size="sm" variant="secondary">Import</mj-button>
                    <mj-button size="sm" variant="secondary">Share</mj-button>
                  </mj-toolbar>
                  <mj-status-bar dock="bottom" label="Workspace status">
                    <span slot="start">eu-west-1</span>
                    <span>All changes saved</span>
                    <span slot="end">v4.2.0</span>
                  </mj-status-bar>
                  <mj-side-nav dock="start" mode="static" nav-label="Sections" class="shell-nav">
                    <a href="#dashboard" aria-current="page">Dashboard</a>
                    <a href="#reports">Reports</a>
                    <a href="#customers">Customers</a>
                    <a href="#settings">Settings</a>
                  </mj-side-nav>
                  <mj-scroll-area dock="fill" aria-label="Dashboard" class="shell-main">
                    <h2>Dashboard</h2>
                    <p>The fill child gets the rectangle the bands leave, on both axes, and scrolls inside it.</p>
                    <mj-grid min-col-width="10rem" gap="sm">
                      <mj-surface elevation="outlined"><small>Revenue</small><br><b>$48.2k</b></mj-surface>
                      <mj-surface elevation="outlined"><small>Orders</small><br><b>1,204</b></mj-surface>
                      <mj-surface elevation="outlined"><small>Refunds</small><br><b>12</b></mj-surface>
                    </mj-grid>
                    <p>Recent activity, notes and reports follow below the tiles. Scroll this area: the
                      toolbar, navigation and status bar stay where they are.</p>
                    <p>Last import finished at 09:12 with 4,180 rows.</p>
                    <p>Next scheduled export: tonight at 23:00.</p>
                  </mj-scroll-area>
                </mj-dock-layout>
            """),
            css=_code("""
                .demo-shell { block-size: 26rem; border: 1px solid var(--mj-border); }
                .demo-shell .shell-top { padding: var(--mj-space-2); background: var(--mj-surface); }
                .demo-shell .shell-nav { --mj-side-nav-width: 13rem; border-inline-end: 1px solid var(--mj-border); }
                .demo-shell .shell-main { padding-inline: var(--mj-space-4); }
            """),
        ),
        ComponentExample(
            key="nested",
            title="Workbench: split pane and grid",
            description=(
                "<p>Nesting: the outer layout docks an <code>mj-app-bar</code> on top and an "
                "<code>mj-split-pane</code> as fill. The split pane's start pane is an "
                "<code>mj-tree-nav</code>; its end pane is a nested <code>mj-dock-layout</code> with a "
                "breadcrumb band, a property panel docked at the end and an <code>mj-scroll-area</code> fill "
                "holding an <code>mj-grid</code> of cards. Drag the separator: the inner layout re-runs "
                "and the grid reflows. Try <b>1024</b>, <b>768</b> and <b>320</b>: at 320 the app bar "
                "collapses to its menu button and a media query hides the property panel "
                "(<code>display: none</code>), which the layout gives no space.</p>"
            ),
            html=_code("""
                <mj-dock-layout class="workbench">
                  <mj-app-bar dock="top" collapse-breakpoint="sm" class="bench-bar">
                    <strong slot="brand">Atlas</strong>
                    <a slot="navigation" href="#files" aria-current="page">Files</a>
                    <a slot="navigation" href="#runs">Runs</a>
                    <mj-button slot="actions" size="sm" variant="secondary">Deploy</mj-button>
                  </mj-app-bar>
                  <mj-split-pane dock="fill" initial-size="13rem" min="8rem" max="50%" collapsible="start" separator-label="Resize project tree">
                    <mj-tree-nav slot="start" nav-label="Project" current="#reports" class="bench-tree">
                      <li><a href="#assets">assets</a>
                        <ul><li><a href="#logo">logo.svg</a></li><li><a href="#hero">hero.png</a></li></ul>
                      </li>
                      <li><a href="#reports">reports</a></li>
                      <li><a href="#config">config.toml</a></li>
                    </mj-tree-nav>
                    <mj-dock-layout slot="end" gap="sm" class="bench-inner">
                      <mj-breadcrumb dock="top" class="bench-crumbs">
                        <a href="#atlas">atlas</a>
                        <a href="#reports">reports</a>
                      </mj-breadcrumb>
                      <mj-surface dock="end" elevation="outlined" padding="sm" class="bench-props">
                        <b>Properties</b>
                        <p>8 files<br>2.4 MB<br>Updated today</p>
                      </mj-surface>
                      <mj-scroll-area dock="fill" aria-label="Reports" class="bench-main">
                        <mj-grid min-col-width="9rem" gap="sm">
                          <mj-card heading="Q1 revenue" elevation="outlined"><p>PDF &middot; 340 KB</p></mj-card>
                          <mj-card heading="Q2 revenue" elevation="outlined"><p>PDF &middot; 360 KB</p></mj-card>
                          <mj-card heading="Churn analysis" elevation="outlined"><p>Notebook with cohort charts and the retention model.</p></mj-card>
                          <mj-card heading="Roadmap" elevation="outlined"><p>Slides</p></mj-card>
                          <mj-card heading="Hiring plan" elevation="outlined"><p>Sheet</p></mj-card>
                          <mj-card heading="Budget" elevation="outlined"><p>Sheet</p></mj-card>
                        </mj-grid>
                      </mj-scroll-area>
                    </mj-dock-layout>
                  </mj-split-pane>
                </mj-dock-layout>
            """),
            css=_code("""
                .workbench { block-size: 30rem; border: 1px solid var(--mj-border); }
                .bench-tree { box-sizing: border-box; min-block-size: 100%; padding: var(--mj-space-2); background: var(--mj-bg-muted); }
                .bench-inner { padding: var(--mj-space-2); }
                .bench-props { inline-size: 9rem; }
                /* Narrow frames: drop the property panel; a display:none band takes no space. */
                @media (max-width: 600px) { .bench-props { display: none; } }
                .bench-props p { margin: var(--mj-space-1) 0 0; font-size: var(--mj-font-size-sm); }
            """),
        ),
        ComponentExample(
            key="responsive",
            title="Responsive re-docking",
            description=(
                "<p>The script watches the layout width. At <b>Full</b> / <b>1024</b> the navigation is "
                "docked at the start and the inspector at the end; below 800px (the <b>768</b> and <b>320</b> "
                "presets) the inspector is hidden; below 480px (<b>320</b>) the navigation "
                "re-docks as a top band (<code>dock</code> changes from <code>start</code> to "
                "<code>top</code>). Each change logs and triggers <code>mj-layout</code>.</p>"
            ),
            html=_code("""
                <mj-dock-layout id="responsive-shell" class="resp">
                  <mj-toolbar dock="top" label="Editor actions" class="resp-top">
                    <mj-button size="sm" variant="primary">Publish</mj-button>
                    <mj-button size="sm" variant="secondary">Preview</mj-button>
                  </mj-toolbar>
                  <nav id="resp-nav" dock="start" class="resp-nav" aria-label="Pages">
                    <a href="#home">Home</a><a href="#pricing">Pricing</a><a href="#blog">Blog</a><a href="#about">About</a>
                  </nav>
                  <mj-surface id="resp-inspector" dock="end" elevation="flat" padding="sm" class="resp-inspector">
                    <b>Inspector</b>
                    <mj-text-field label="Page title" value="Pricing"></mj-text-field>
                  </mj-surface>
                  <mj-scroll-area dock="fill" aria-label="Page editor" class="resp-main">
                    <h3>Pricing</h3>
                    <p>Simple plans for teams of every size. Start free and upgrade when you need more.</p>
                    <mj-grid min-col-width="9rem" gap="sm">
                      <mj-card heading="Free" elevation="outlined"><p>$0</p></mj-card>
                      <mj-card heading="Team" elevation="outlined"><p>$9 / seat</p></mj-card>
                      <mj-card heading="Business" elevation="outlined"><p>$19 / seat</p></mj-card>
                    </mj-grid>
                  </mj-scroll-area>
                </mj-dock-layout>
            """),
            css=_code("""
                .resp { block-size: 24rem; border: 1px solid var(--mj-border); }
                .resp-top { padding: var(--mj-space-2); border-block-end: 1px solid var(--mj-border); }
                .resp-nav { display: flex; flex-direction: column; gap: var(--mj-space-2); inline-size: 9rem; padding: var(--mj-space-3); background: var(--mj-bg-muted); }
                .resp-nav[dock="top"] { flex-direction: row; flex-wrap: wrap; inline-size: auto; }
                .resp-inspector { inline-size: 12rem; --mj-surface-bg: var(--mj-bg-muted); }
                .resp-main { padding-inline: var(--mj-space-4); }
            """),
            script=_code("""
                const shell = document.getElementById("responsive-shell")
                const nav = document.getElementById("resp-nav")
                const inspector = document.getElementById("resp-inspector")
                function adapt() {
                  const width = shell.clientWidth
                  const navEdge = width < 480 ? "top" : "start"
                  const hideInspector = width < 800
                  if (nav.getAttribute("dock") !== navEdge) {
                    nav.setAttribute("dock", navEdge)
                    mjSandbox.log("navigation docked", { edge: navEdge, width: width })
                  }
                  if (inspector.hidden !== hideInspector) {
                    inspector.hidden = hideInspector
                    mjSandbox.log("inspector", { hidden: hideInspector, width: width })
                  }
                }
                new ResizeObserver(adapt).observe(shell)
                adapt()
            """),
            height=420,
        ),
        ComponentExample(
            key="anchor",
            title="Anchored children",
            description=(
                "<p>Undocked mj-* children with the <code>anchor</code> attribute are pinned to the "
                "layout over the bands: an <code>mj-button</code> at <code>bottom-end</code> (a floating "
                "action, inset by <code>--mj-anchor-inset</code>), an <code>mj-chip</code> at "
                "<code>top-end</code> and an <code>mj-alert</code> at <code>top</code>. Anchors are relative "
                "to the whole layout box, not to the free area, so the alert uses a 3.25rem inset to clear "
                "the header band. Switch <b>Dir</b> to <b>RTL</b>: start / end corners swap.</p>"
            ),
            html=_code("""
                <mj-dock-layout class="map-shell">
                  <header dock="top" class="map-top">Field map &middot; Sector 7</header>
                  <aside dock="start" class="map-legend" aria-label="Legend"><b>Legend</b><br>Trail<br>Hut<br>Water</aside>
                  <div dock="fill" class="map-canvas" role="img" aria-label="Map"></div>
                  <mj-chip anchor="top-end" class="map-chip">Live</mj-chip>
                  <mj-alert anchor="top" severity="info" class="map-alert">Offline map downloaded</mj-alert>
                  <mj-button anchor="bottom-end" variant="primary" class="map-fab">+ Waypoint</mj-button>
                </mj-dock-layout>
            """),
            css=_code("""
                .map-shell { block-size: 22rem; border: 1px solid var(--mj-border); }
                .map-top { block-size: 2.5rem; padding-inline: var(--mj-space-3); display: flex; align-items: center; background: var(--mj-surface); border-block-end: 1px solid var(--mj-border); }
                .map-legend { inline-size: 8rem; padding: var(--mj-space-3); background: var(--mj-surface); border-inline-end: 1px solid var(--mj-border); }
                .map-canvas { background: repeating-linear-gradient(0deg, var(--mj-bg-muted) 0 1px, transparent 1px 24px), repeating-linear-gradient(90deg, var(--mj-bg-muted) 0 1px, transparent 1px 24px), var(--mj-bg-subtle); }
                .map-chip { --mj-anchor-inset: var(--mj-space-2); }
                .map-fab { --mj-anchor-inset: var(--mj-space-4); }
                .map-alert { --mj-anchor-inset: 3.25rem; max-inline-size: 60%; }
            """),
        ),
        ComponentExample(
            key="events",
            title="Runtime changes and events",
            description=(
                "<p>Every button changes the layout at run time and Events shows the resulting "
                "<code>mj-layout</code> pass: hide the bottom panel, widen the sidebar (an inline width "
                "change on a plain element is observed), move the sidebar to the end, and step the "
                "<code>gap</code>. The script toggles the panel once on load. Plain elements are docked "
                "here; padding on the layout insets every band.</p>"
            ),
            html=_code("""
                <mj-stack direction="horizontal" gap="sm" wrap class="bar">
                  <mj-button id="toggle-panel" size="sm" variant="secondary">Toggle panel</mj-button>
                  <mj-button id="widen" size="sm" variant="secondary">Widen sidebar</mj-button>
                  <mj-button id="flip" size="sm" variant="secondary">Sidebar start / end</mj-button>
                  <mj-button id="gap" size="sm" variant="secondary">Next gap</mj-button>
                </mj-stack>
                <mj-dock-layout id="demo-events-dock" gap="sm" class="runtime">
                  <div dock="top" class="band">Top band (height 2.5rem)</div>
                  <div id="bottom-panel" dock="bottom" class="band panel">Problems panel (height 5rem)</div>
                  <div id="sidebar" dock="start" class="band side" style="width: 8rem">Sidebar</div>
                  <div dock="fill" class="band fill">Fill</div>
                </mj-dock-layout>
            """),
            css=_code("""
                .bar { margin: var(--mj-space-4); }
                .runtime { block-size: 20rem; margin: 0 var(--mj-space-4) var(--mj-space-4); padding: var(--mj-space-2); box-sizing: border-box; border: 1px solid var(--mj-border); }
                .band { display: grid; place-items: center; padding: var(--mj-space-2); border-radius: var(--mj-radius-sm); background: var(--mj-bg-muted); }
                .runtime > [dock="top"] { block-size: 2.5rem; }
                .panel { block-size: 5rem; }
                .fill { background: var(--mj-bg-subtle); border: 1px dashed var(--mj-border-strong); }
            """),
            script=_code("""
                const dock = document.getElementById("demo-events-dock")
                const panel = document.getElementById("bottom-panel")
                const sidebar = document.getElementById("sidebar")
                const gaps = ["none", "xs", "sm", "md", "lg", "xl"]
                dock.addEventListener("mj-layout", () => {
                  mjSandbox.log("layout pass", { sidebar: sidebar.getAttribute("dock"), width: sidebar.style.width, gap: dock.getAttribute("gap") })
                })
                document.getElementById("toggle-panel").addEventListener("click", () => { panel.hidden = !panel.hidden })
                document.getElementById("widen").addEventListener("click", () => {
                  const width = parseFloat(sidebar.style.width) >= 14 ? 8 : parseFloat(sidebar.style.width) + 3
                  sidebar.style.width = width + "rem"
                })
                document.getElementById("flip").addEventListener("click", () => {
                  sidebar.setAttribute("dock", sidebar.getAttribute("dock") === "start" ? "end" : "start")
                })
                document.getElementById("gap").addEventListener("click", () => {
                  const next = gaps[(gaps.indexOf(dock.getAttribute("gap")) + 1) % gaps.length]
                  dock.setAttribute("gap", next)
                })
                panel.hidden = true
                setTimeout(() => { panel.hidden = false }, 500)
            """),
        ),
    ],
    slots=[
        ("", "The children: bands with dock=top|bottom|start|end, content with dock=fill, anchored or plain children.",
         '<div dock="bottom" style="height:2rem;padding:0.25rem 1rem;background:var(--mj-bg-muted)">Added bottom band</div>'),
    ],
    properties=[],
    methods=[
        ("requestLayout()", "Schedules a layout pass on the next animation frame (coalesced); use after changes the layout cannot observe."),
    ],
    parts=[],
    css_properties=[
        ("--mj-dock-gap", "Gap between bands; overrides the `gap` token (default 0)."),
        ("--mj-anchor-inset", "On an anchored child: distance from the layout edge (default 0)."),
    ],
)


COMPONENTS = [
    CARD,
    SURFACE,
    GRID,
    STACK,
    SPACER,
    ASPECT_RATIO,
    ACCORDION,
    DISCLOSURE,
    SPLIT_PANE,
    SCROLL_AREA,
    CAROUSEL,
    FEED,
    MEDIA_OBJECT,
    HERO,
    EMPTY_STATE,
    SKELETON,
    DIVIDER,
    DOCK_LAYOUT,
]
