"""
    media.py

    Catalog entries for the 'Media & Visualization' component group.

    Every component in this group handles rich media display or data
    visualization: images, avatars, audio/video playback, charts, maps,
    gauges, sparklines, and node/edge diagrams.

    The examples never reach the network: pictures are inline SVG (or a small
    generated PNG) data: URIs, the media player's sound is synthesised in the
    example script as a WAV blob, and caption tracks are WebVTT data: URIs.
"""

import base64
import struct
import zlib

from urllib.parse import quote

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


# ---------------------------------------------------------------------------
# Generated media (no network access in any example)
# ---------------------------------------------------------------------------

def _svg_uri(svg: str) -> str:
    """
        Turn SVG markup into a data: URI usable in an ``src`` attribute.

        :param svg: SVG markup written with single-quoted attributes.

        :returns: A ``data:image/svg+xml,...`` URI, percent-encoded so it can sit
            inside a double-quoted HTML attribute.
    """

    encoded = quote(svg, safe="=:/;,'()")
    uri = "data:image/svg+xml," + encoded
    return uri


def _scene(width: int, height: int, sky_top: str, sky_bottom: str, far: str, near: str, caption: str = "") -> str:
    """
        Build a small landscape picture (sky, sun, two mountain ranges, water).

        :param width: Picture width in SVG user units.
        :param height: Picture height in SVG user units.
        :param sky_top: Colour at the top of the sky gradient.
        :param sky_bottom: Colour at the horizon.
        :param far: Colour of the far mountain range.
        :param near: Colour of the near mountain range.
        :param caption: Optional text drawn in the lower left corner.

        :returns: A data: URI of the picture.
    """

    w = width
    h = height
    far_path = (
        f"M0 {h * 0.72:.0f} L{w * 0.18:.0f} {h * 0.42:.0f} L{w * 0.33:.0f} {h * 0.62:.0f} "
        f"L{w * 0.5:.0f} {h * 0.33:.0f} L{w * 0.7:.0f} {h * 0.66:.0f} L{w * 0.85:.0f} {h * 0.5:.0f} "
        f"L{w} {h * 0.64:.0f} V{h} H0Z"
    )
    near_path = (
        f"M0 {h * 0.84:.0f} L{w * 0.15:.0f} {h * 0.67:.0f} L{w * 0.3:.0f} {h * 0.8:.0f} "
        f"L{w * 0.48:.0f} {h * 0.6:.0f} L{w * 0.65:.0f} {h * 0.8:.0f} L{w * 0.82:.0f} {h * 0.69:.0f} "
        f"L{w} {h * 0.82:.0f} V{h} H0Z"
    )
    label = ""
    if caption != "":
        label = (
            f"<text x='{w * 0.04:.0f}' y='{h * 0.95:.0f}' font-family='sans-serif' "
            f"font-size='{max(12, round(h * 0.07))}' font-weight='bold' fill='white'>{caption}</text>"
        )
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}'>"
        "<defs><linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0' stop-color='{sky_top}'/><stop offset='1' stop-color='{sky_bottom}'/>"
        "</linearGradient></defs>"
        f"<rect width='{w}' height='{h}' fill='url(#sky)'/>"
        f"<circle cx='{w * 0.76:.0f}' cy='{h * 0.28:.0f}' r='{min(w, h) * 0.11:.0f}' fill='#ffd36b'/>"
        f"<path d='{far_path}' fill='{far}'/>"
        f"<path d='{near_path}' fill='{near}'/>"
        f"<rect y='{h * 0.9:.0f}' width='{w}' height='{h * 0.1:.0f}' fill='{near}' opacity='0.7'/>"
        f"{label}</svg>"
    )
    uri = _svg_uri(svg)
    return uri


def _tower(width: int, height: int) -> str:
    """
        Build a tall (portrait) picture of a lighthouse, used to show `fit`.

        :param width: Picture width in SVG user units.
        :param height: Picture height in SVG user units.

        :returns: A data: URI of the picture.
    """

    w = width
    h = height
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}'>"
        f"<rect width='{w}' height='{h}' fill='#9fd3f2'/>"
        f"<rect y='{h * 0.8:.0f}' width='{w}' height='{h * 0.2:.0f}' fill='#2f6f8f'/>"
        f"<path d='M{w * 0.38:.0f} {h * 0.8:.0f} L{w * 0.43:.0f} {h * 0.22:.0f} "
        f"L{w * 0.57:.0f} {h * 0.22:.0f} L{w * 0.62:.0f} {h * 0.8:.0f}Z' fill='#f4f4f4'/>"
        f"<rect x='{w * 0.4:.0f}' y='{h * 0.4:.0f}' width='{w * 0.2:.0f}' height='{h * 0.06:.0f}' fill='#d9433f'/>"
        f"<rect x='{w * 0.39:.0f}' y='{h * 0.6:.0f}' width='{w * 0.22:.0f}' height='{h * 0.06:.0f}' fill='#d9433f'/>"
        f"<rect x='{w * 0.42:.0f}' y='{h * 0.13:.0f}' width='{w * 0.16:.0f}' height='{h * 0.09:.0f}' fill='#ffd36b'/>"
        f"<path d='M{w * 0.4:.0f} {h * 0.13:.0f} L{w * 0.5:.0f} {h * 0.06:.0f} L{w * 0.6:.0f} {h * 0.13:.0f}Z' fill='#d9433f'/>"
        "</svg>"
    )
    uri = _svg_uri(svg)
    return uri


def _portrait(background: str, skin: str, hair: str, shirt: str) -> str:
    """
        Build a square head-and-shoulders illustration used as an avatar photo.

        :param background: Background colour.
        :param skin: Face colour.
        :param hair: Hair colour.
        :param shirt: Shirt colour.

        :returns: A data: URI of the picture.
    """

    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80' width='80' height='80'>"
        f"<rect width='80' height='80' fill='{background}'/>"
        f"<path d='M12 80c2-18 14-26 28-26s26 8 28 26z' fill='{shirt}'/>"
        f"<circle cx='40' cy='33' r='15' fill='{skin}'/>"
        f"<path d='M24 32c0-12 7-19 16-19s16 7 16 19c-3-7-9-9-16-9s-13 2-16 9z' fill='{hair}'/>"
        "</svg>"
    )
    uri = _svg_uri(svg)
    return uri


def _png_poster(width: int, height: int) -> str:
    """
        Encode a small dusk-gradient PNG (with a sun) as a data: URI.

        The media player's `poster` attribute accepts raster data: URIs only
        (PNG, JPEG, GIF, WebP, AVIF, BMP), so the poster example needs a real
        PNG. It is generated here with zlib and struct.

        :param width: Image width in pixels.
        :param height: Image height in pixels.

        :returns: A ``data:image/png;base64,...`` URI.
    """

    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            mix = y / max(1, height - 1)
            red = round(40 + 200 * mix)
            green = round(50 + 90 * mix)
            blue = round(120 - 40 * mix)
            dx = x - width * 0.7
            dy = y - height * 0.55
            if dx * dx + dy * dy < (height * 0.18) ** 2:
                red, green, blue = 255, 214, 110
            if y > height * 0.75:
                red, green, blue = 30, 40, 70
            rows.extend((red, green, blue))

    def chunk(tag: bytes, data: bytes) -> bytes:
        checksum = zlib.crc32(tag + data) & 0xFFFFFFFF
        block = struct.pack(">I", len(data)) + tag + data + struct.pack(">I", checksum)
        return block

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")
    uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    return uri


def _vtt_uri(cues: list) -> str:
    """
        Build a WebVTT caption track as a data: URI.

        :param cues: ``(start, end, text)`` tuples, times as ``mm:ss.mmm``.

        :returns: A ``data:text/vtt,...`` URI.
    """

    lines = ["WEBVTT", ""]
    for start, end, text in cues:
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    uri = "data:text/vtt," + quote("\n".join(lines), safe="")
    return uri


_LAKE = _scene(800, 450, "#5aa9e6", "#fde2b8", "#5b7a99", "#33566f")
_DUSK = _scene(800, 450, "#3b2f6b", "#f59e6b", "#6b4f7a", "#3a2d4f")
_MEADOW = _scene(600, 400, "#8fd0f5", "#e8f6d4", "#6f9f5a", "#3f7a3a")
_LIGHTHOUSE = _tower(300, 450)
_SMALL_400 = _scene(400, 225, "#5aa9e6", "#fde2b8", "#5b7a99", "#33566f", "400w candidate")
_LARGE_800 = _scene(800, 450, "#5aa9e6", "#fde2b8", "#5b7a99", "#33566f", "800w candidate")
_THUMBS = [
    _scene(160, 160, "#5aa9e6", "#fde2b8", "#5b7a99", "#33566f"),
    _scene(160, 160, "#3b2f6b", "#f59e6b", "#6b4f7a", "#3a2d4f"),
    _scene(160, 160, "#8fd0f5", "#e8f6d4", "#6f9f5a", "#3f7a3a"),
    _scene(160, 160, "#1f2a44", "#4f6d9a", "#2d3e5e", "#141c2e"),
]

_PHOTO_BOB = _portrait("#cfe3f7", "#e8b98f", "#3b2a20", "#2563eb")
_PHOTO_CARA = _portrait("#f7e1cf", "#a8724c", "#1b1b1b", "#be185d")
_PHOTO_DEV = _portrait("#e2f2df", "#f1c9a5", "#c2702d", "#047857")

_POSTER_PNG = _png_poster(64, 36)

_MISSING_IMAGE = "/static/media/missing-photo.jpg"

_CAPTIONS_EN = _vtt_uri([
    ("00:00.000", "00:03.000", "Welcome to the product tour."),
    ("00:03.000", "00:06.000", "First, open the dashboard from the menu."),
    ("00:06.000", "00:09.000", "Then pick a report and press Share."),
    ("00:09.000", "00:12.000", "That is all it takes. Thanks for watching!"),
])

_CAPTIONS_DE = _vtt_uri([
    ("00:00.000", "00:03.000", "Willkommen zur Produkttour."),
    ("00:03.000", "00:06.000", "Öffnen Sie zuerst das Dashboard im Menü."),
    ("00:06.000", "00:09.000", "Wählen Sie dann einen Bericht und drücken Sie Teilen."),
    ("00:09.000", "00:12.000", "Das ist alles. Danke fürs Zuschauen!"),
])


# A script prelude that synthesises a short chime as a WAV blob URL, so the
# media player examples can play, seek and loop without any media file.
_WAV_HELPER = """\
// No media file ships with this site: synthesise a gentle 12 second chime
// (8 kHz, 8-bit mono WAV) and hand the player a blob: URL for it.
function makeChime(seconds) {
  const rate = 8000
  const count = rate * seconds
  const view = new DataView(new ArrayBuffer(44 + count))
  const text = (offset, value) => {
    for (let i = 0; i < value.length; i += 1) { view.setUint8(offset + i, value.charCodeAt(i)) }
  }
  text(0, "RIFF"); view.setUint32(4, 36 + count, true); text(8, "WAVE")
  text(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true)
  view.setUint16(22, 1, true); view.setUint32(24, rate, true); view.setUint32(28, rate, true)
  view.setUint16(32, 1, true); view.setUint16(34, 8, true)
  text(36, "data"); view.setUint32(40, count, true)
  const notes = [523.25, 659.25, 783.99, 1046.5]
  for (let i = 0; i < count; i += 1) {
    const time = i / rate
    const note = notes[Math.floor(time) % notes.length]
    const decay = Math.exp(-3 * (time % 1))
    view.setUint8(44 + i, 128 + Math.round(40 * decay * Math.sin(2 * Math.PI * note * time)))
  }
  return URL.createObjectURL(new Blob([view.buffer], { type: "audio/wav" }))
}
"""


# ---------------------------------------------------------------------------
# mj-image
# ---------------------------------------------------------------------------

_IMAGE = ComponentDoc(
    tag="mj-image",
    title="Image",
    group="media",
    summary="Lazy-loaded, responsive image with aspect-ratio reservation, placeholder, error state and caption.",
    description=(
        "<p><code>&lt;mj-image&gt;</code> wraps a native <code>&lt;img&gt;</code> in a "
        "<code>&lt;figure&gt;</code>. The image sits in a ratio box (<code>part=\"container\"</code>) "
        "that reserves its space before the file arrives, shows a placeholder while it loads and "
        "clips the image, the placeholder, the error state and the overlay. The "
        "<code>&lt;figcaption&gt;</code> is a sibling below the ratio box, so a caption is never "
        "clipped.</p>"
        "<p>Loading is lazy by default: the source is handed to the inner image when the element "
        "comes within 200px of the viewport (IntersectionObserver), or at once with "
        "<code>loading=\"eager\"</code>. <code>srcset</code> and <code>sizes</code> are passed through "
        "for responsive selection. When the file cannot be loaded the ratio box shows an error state: "
        "a broken-image icon with the <code>alt</code> text (or a generic \"could not be loaded\" "
        "message), while the inner image keeps carrying the alt text for assistive technology.</p>"
        "<p>The <code>thumbnail</code> variant is a small fixed square for lists and previews. The "
        "<code>overlay</code> slot places badges or buttons over the picture.</p>"
    ),
    how_to_use=(
        "<p>Set <code>src</code> and always set <code>alt</code> (use <code>alt=\"\"</code> for a "
        "decorative image; a missing <code>alt</code> logs a console warning). Reserve the space with "
        "<code>aspect-ratio</code> (for example <code>16/9</code>) or with <code>width</code> plus "
        "<code>height</code>, which only give the ratio: the element is a block that fills its "
        "container, so size it with CSS (<code>max-inline-size</code>). Pick the crop with "
        "<code>fit</code>. Use <code>loading=\"eager\"</code> for above-the-fold pictures.</p>"
        "<p>Give a caption with the <code>caption</code> attribute, or rich caption content in the "
        "<code>caption</code> slot (it replaces the attribute text). Put a spinner or blurred preview "
        "in the <code>placeholder</code> slot and colour the empty box with "
        "<code>placeholder-color</code>. Listen for <code>mj-image-load</code> and "
        "<code>mj-image-error</code>; the read-only <code>failed</code>, <code>complete</code>, "
        "<code>naturalWidth</code>, <code>naturalHeight</code> and <code>currentSrc</code> properties "
        "report the outcome. Changing <code>src</code>, <code>srcset</code> or <code>sizes</code> "
        "starts a new load; switching <code>loading</code> to <code>eager</code> starts a lazy image "
        "that has not loaded yet.</p>"
    ),
    attributes=[
        AttributeDoc(name="src", description="URL of the image (http(s), relative or a data: URI).",
                     kind="string"),
        AttributeDoc(name="alt", description="Alternative text; also shown in the error state. Use `alt=\"\"` for a decorative image.",
                     kind="string", values=["Mountain lake at sunrise", ""]),
        AttributeDoc(name="aspect-ratio", description="CSS aspect ratio of the ratio box; wins over width/height.",
                     kind="string", values=["16/9", "4/3", "3/2", "1/1", "21/9"]),
        AttributeDoc(name="width", description="Intrinsic width; with `height` it sets the box ratio (not its size).",
                     kind="number"),
        AttributeDoc(name="height", description="Intrinsic height; with `width` it sets the box ratio.",
                     kind="number"),
        AttributeDoc(name="fit", description="`object-fit` of the image inside the box.", kind="enum",
                     values=["cover", "contain", "fill", "none", "scale-down"], default="cover"),
        AttributeDoc(name="loading", description="`lazy` waits until the element nears the viewport; `eager` loads at once.",
                     kind="enum", values=["lazy", "eager"], default="lazy"),
        AttributeDoc(name="variant", description="`thumbnail` makes a small fixed square (`--mj-image-thumbnail-size`).",
                     kind="enum", values=["thumbnail"]),
        AttributeDoc(name="caption", description="Caption text shown below the ratio box; the `caption` slot replaces it.",
                     kind="string"),
        AttributeDoc(name="placeholder-color", description="Background of the placeholder and error state.",
                     kind="color"),
        AttributeDoc(name="srcset", description="Responsive candidates, passed to the inner img.", kind="string"),
        AttributeDoc(name="sizes", description="Slot sizes for `srcset` selection, e.g. `(max-width: 600px) 100vw, 480px`.",
                     kind="string"),
        AttributeDoc(name="crossorigin", description="CORS mode forwarded to the inner img.", kind="enum",
                     values=["anonymous", "use-credentials"]),
        AttributeDoc(name="decoding", description="Decoding hint forwarded to the inner img.", kind="enum",
                     values=["async", "sync", "auto"], default="async"),
    ],
    events=[
        ("mj-image-visible", "A lazy image came within 200px of the viewport and starts loading.",
         "{ ratio: number }"),
        ("mj-image-load", "The image loaded and is shown.",
         "{ src: string, naturalWidth: number, naturalHeight: number }"),
        ("mj-image-error", "The image could not be loaded; the error state is shown.", "{ src: string }"),
    ],
    slots=[
        ("placeholder", "Content shown centred in the box while the image loads (spinner, initials, blurred preview).",
         '<span style="font: var(--mj-font-size-sm) var(--mj-font-sans); color: var(--mj-text-muted)">Loading…</span>'),
        ("overlay", "Content laid over the picture (badges, a play button); it stays clickable.",
         '<span style="position:absolute; inset-block-start:8px; inset-inline-start:8px; padding:2px 8px; '
         'border-radius:999px; background:var(--mj-surface); color:var(--mj-text); '
         'font:600 12px var(--mj-font-sans)">New</span>'),
        ("caption", "Rich caption content; replaces the `caption` attribute text.",
         "<span>Photo: <strong>Lake Bled</strong>, Slovenia</span>"),
    ],
    properties=[
        ("failed", "boolean, read-only. True when the last load attempt failed."),
        ("complete", "boolean, read-only. The inner image finished loading (or failed)."),
        ("naturalWidth", "number, read-only. Intrinsic width of the loaded image, 0 before load."),
        ("naturalHeight", "number, read-only. Intrinsic height of the loaded image, 0 before load."),
        ("currentSrc", "string, read-only. The candidate the browser picked from `src` / `srcset`."),
    ],
    parts=[
        ("figure", "The outer figure (ratio box plus caption)."),
        ("container", "The clipped ratio box."),
        ("img", "The native img."),
        ("placeholder", "The layer shown while loading."),
        ("error", "The error state (icon and alt text)."),
        ("overlay", "The layer holding the overlay slot."),
        ("caption", "The figcaption below the box."),
    ],
    css_properties=[
        ("--mj-image-radius", "Corner radius of the ratio box (default `--mj-radius-md`)."),
        ("--mj-image-placeholder-color", "Placeholder background (default `--mj-bg-muted`); the attribute wins."),
        ("--mj-image-thumbnail-size", "Edge of the thumbnail variant (default 3rem)."),
        ("--mj-image-transition-duration", "Fade-in duration (default `--mj-motion-medium`)."),
        ("--mj-image-caption-font-size", "Caption font size (default `--mj-font-size-sm`)."),
        ("--mj-image-caption-color", "Caption colour (default `--mj-text-muted`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A 16:9 figure with alt text and a caption below the ratio box. Change "
                "<code>fit</code>, <code>aspect-ratio</code> or <code>caption</code> in Controls.</p>"
            ),
            html=(
                '<mj-image\n'
                '  src="' + _LAKE + '"\n'
                '  alt="Mountain lake under a clear morning sky"\n'
                '  aspect-ratio="16/9"\n'
                '  caption="Morning at the lake (generated SVG)"\n'
                '  style="max-inline-size: 480px">\n'
                '</mj-image>'
            ),
        ),
        ComponentExample(
            key="fit",
            title="Fit modes",
            description=(
                "<p>The same portrait picture in square boxes with each <code>fit</code> value: "
                "<code>cover</code> crops, <code>contain</code> letterboxes, <code>fill</code> "
                "stretches, <code>scale-down</code> never enlarges.</p>"
            ),
            html=(
                '<div class="fit-row">\n'
                '  <mj-image src="' + _LIGHTHOUSE + '" alt="Lighthouse, cover" aspect-ratio="1/1" fit="cover" caption="cover"></mj-image>\n'
                '  <mj-image src="' + _LIGHTHOUSE + '" alt="Lighthouse, contain" aspect-ratio="1/1" fit="contain" caption="contain"></mj-image>\n'
                '  <mj-image src="' + _LIGHTHOUSE + '" alt="Lighthouse, fill" aspect-ratio="1/1" fit="fill" caption="fill"></mj-image>\n'
                '  <mj-image src="' + _LIGHTHOUSE + '" alt="Lighthouse, scale-down" aspect-ratio="1/1" fit="scale-down" caption="scale-down"></mj-image>\n'
                '</div>'
            ),
            css=(
                ".fit-row {\n"
                "  display: grid;\n"
                "  grid-template-columns: repeat(auto-fill, minmax(8rem, 1fr));\n"
                "  gap: var(--mj-space-4);\n"
                "  max-inline-size: 40rem;\n"
                "}\n"
            ),
        ),
        ComponentExample(
            key="thumbnails",
            title="Thumbnails and overlay",
            description=(
                "<p><code>variant=\"thumbnail\"</code> gives small fixed squares (resized here with "
                "<code>--mj-image-thumbnail-size</code>). The large picture uses the "
                "<code>overlay</code> slot for a badge and a play button.</p>"
            ),
            html=(
                '<mj-image src="' + _DUSK + '" alt="Dusk over the hills, video still" aspect-ratio="16/9" style="max-inline-size: 360px">\n'
                '  <span slot="overlay" class="badge">4K</span>\n'
                '  <button slot="overlay" type="button" class="play" aria-label="Play video">&#9654;</button>\n'
                '</mj-image>\n'
                '<div class="thumbs">\n'
                '  <mj-image variant="thumbnail" loading="eager" src="' + _THUMBS[0] + '" alt="Lake"></mj-image>\n'
                '  <mj-image variant="thumbnail" loading="eager" src="' + _THUMBS[1] + '" alt="Dusk"></mj-image>\n'
                '  <mj-image variant="thumbnail" loading="eager" src="' + _THUMBS[2] + '" alt="Meadow"></mj-image>\n'
                '  <mj-image variant="thumbnail" loading="eager" src="' + _THUMBS[3] + '" alt="Night"></mj-image>\n'
                '</div>'
            ),
            css=(
                ".thumbs { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n"
                ".thumbs mj-image { --mj-image-thumbnail-size: 4rem; --mj-image-radius: var(--mj-radius-sm); }\n"
                ".badge {\n"
                "  position: absolute; inset-block-start: var(--mj-space-2); inset-inline-end: var(--mj-space-2);\n"
                "  padding: 0 var(--mj-space-2); border-radius: var(--mj-radius-pill);\n"
                "  background: var(--mj-surface); color: var(--mj-text);\n"
                "  font: var(--mj-font-weight-bold) var(--mj-font-size-xs) var(--mj-font-sans); line-height: 1.6;\n"
                "}\n"
                ".play {\n"
                "  position: absolute; inset: 0; margin: auto; inline-size: 3rem; block-size: 3rem;\n"
                "  border: none; border-radius: 50%; background: var(--mj-surface); color: var(--mj-text);\n"
                "  font-size: 1.1rem; line-height: 1; cursor: pointer;\n"
                "}\n"
            ),
            script=(
                'document.querySelector(".play").addEventListener("click", () => {\n'
                '  mjSandbox.log("overlay button clicked", { action: "play" })\n'
                '})\n'
            ),
        ),
        ComponentExample(
            key="responsive",
            title="srcset, sizes and lazy loading",
            description=(
                "<p>The first figure offers a 400w and an 800w candidate through <code>srcset</code>; "
                "the picture says which one the browser chose (resize the preview to compare). The "
                "second figure reserves its box with <code>width</code>/<code>height</code> and sits "
                "below a tall spacer: scroll the preview to it and watch <code>mj-image-visible</code> "
                "then <code>mj-image-load</code> in Events.</p>"
            ),
            html=(
                '<mj-image\n'
                '  src="' + _LARGE_800 + '"\n'
                '  srcset="' + _SMALL_400 + ' 400w, ' + _LARGE_800 + ' 800w"\n'
                '  sizes="(max-width: 500px) 100vw, 480px"\n'
                '  alt="Mountain lake; the picture names the chosen candidate"\n'
                '  aspect-ratio="16/9"\n'
                '  loading="eager"\n'
                '  style="max-inline-size: 480px">\n'
                '</mj-image>\n'
                '<p class="spacer">Scroll down: the next image loads lazily.</p>\n'
                '<mj-image id="lazy-image" src="' + _MEADOW + '" alt="Green meadow below blue sky"\n'
                '  width="600" height="400" caption="Loaded when it came into view" style="max-inline-size: 360px">\n'
                '</mj-image>'
            ),
            css=(
                ".spacer {\n"
                "  block-size: 600px; margin: var(--mj-space-4) 0; padding: var(--mj-space-3);\n"
                "  border: 1px dashed var(--mj-border); color: var(--mj-text-muted);\n"
                "}\n"
            ),
            script=(
                'const lazy = document.getElementById("lazy-image")\n'
                'lazy.addEventListener("mj-image-load", (event) => {\n'
                '  mjSandbox.log("lazy image loaded", { naturalWidth: event.detail.naturalWidth, complete: lazy.complete })\n'
                '})\n'
                'const chosen = document.querySelector("mj-image")\n'
                'chosen.addEventListener("mj-image-load", () => {\n'
                '  mjSandbox.log("srcset candidate", { naturalWidth: chosen.naturalWidth })\n'
                '})\n'
            ),
            height=420,
        ),
        ComponentExample(
            key="states",
            title="Placeholder, error and decorative",
            description=(
                "<p>Left: no <code>src</code> yet, so the <code>placeholder</code> slot and "
                "<code>placeholder-color</code> show. Middle: the file does not exist, so the error "
                "state shows the alt text and <code>mj-image-error</code> appears in Events. Right: "
                "a decorative image with <code>alt=\"\"</code>.</p>"
            ),
            html=(
                '<div class="states">\n'
                '  <mj-image alt="Product photo, waiting for upload" aspect-ratio="4/3" placeholder-color="var(--mj-color-info-surface)"\n'
                '    caption="Waiting for src">\n'
                '    <span slot="placeholder" class="hint">Upload a photo</span>\n'
                '  </mj-image>\n'
                '  <mj-image src="' + _MISSING_IMAGE + '" alt="Team photo from the 2025 offsite" aspect-ratio="4/3"\n'
                '    loading="eager" caption="Missing file"></mj-image>\n'
                '  <mj-image src="' + _THUMBS[2] + '" alt="" aspect-ratio="4/3" caption="Decorative (alt=&quot;&quot;)"></mj-image>\n'
                '</div>'
            ),
            css=(
                ".states { display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: var(--mj-space-4); }\n"
                ".hint { font: var(--mj-font-size-sm) var(--mj-font-sans); color: var(--mj-color-info); }\n"
            ),
        ),
        ComponentExample(
            key="events",
            title="Swapping sources",
            description=(
                "<p>The buttons change <code>src</code> at run time: each change starts a new load and "
                "the event log shows <code>mj-image-load</code> or <code>mj-image-error</code>. The "
                "caption comes from the <code>caption</code> slot.</p>"
            ),
            html=(
                '<mj-image id="swap-image" src="' + _LAKE + '" alt="Landscape picture" aspect-ratio="16/9"\n'
                '  loading="eager" style="max-inline-size: 420px">\n'
                '  <span slot="caption">Showing: <strong id="swap-name">lake</strong></span>\n'
                '</mj-image>\n'
                '<div class="buttons">\n'
                '  <button type="button" data-name="lake">Lake</button>\n'
                '  <button type="button" data-name="dusk">Dusk</button>\n'
                '  <button type="button" data-name="meadow">Meadow</button>\n'
                '  <button type="button" data-name="missing">Missing file</button>\n'
                '</div>'
            ),
            css=".buttons { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n",
            script=(
                'const sources = {\n'
                '  lake: "' + _LAKE + '",\n'
                '  dusk: "' + _DUSK + '",\n'
                '  meadow: "' + _MEADOW + '",\n'
                '  missing: "' + _MISSING_IMAGE + '"\n'
                '}\n'
                'const image = document.getElementById("swap-image")\n'
                'for (const button of document.querySelectorAll("[data-name]")) {\n'
                '  button.addEventListener("click", () => {\n'
                '    const name = button.getAttribute("data-name")\n'
                '    document.getElementById("swap-name").textContent = name\n'
                '    image.setAttribute("src", sources[name])\n'
                '  })\n'
                '}\n'
                'image.addEventListener("mj-image-error", () => {\n'
                '  mjSandbox.log("failed", { failed: image.failed })\n'
                '})\n'
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# mj-avatar
# ---------------------------------------------------------------------------

_AVATAR = ComponentDoc(
    tag="mj-avatar",
    title="Avatar",
    group="media",
    summary="User or entity avatar with photo, initials and icon fallback, sizes, shapes and a presence dot.",
    description=(
        "<p><code>&lt;mj-avatar&gt;</code> shows who someone is with a three-step fallback: the "
        "photo from <code>src</code>, else initials (explicit <code>initials</code>, or the first "
        "letters of the first and last word of <code>name</code>), else a person icon. The fallback "
        "is shown while the photo loads and again if it fails. The background is picked "
        "deterministically from the name (eight palette colours, each with at least 4.5:1 contrast "
        "against the white initials), so a person keeps their colour everywhere.</p>"
        "<p>The element is named for assistive technology by <code>name</code> (\"Unknown user\" "
        "without one). An optional presence dot (online, away, busy, offline) sits outside the "
        "clipped circle and has its own text alternative. A slotted <code>&lt;img&gt;</code> or "
        "<code>&lt;picture&gt;</code> replaces the photo and the fallback; the <code>icon</code> "
        "slot replaces the default person icon.</p>"
    ),
    how_to_use=(
        "<p>Always set <code>name</code>; add <code>src</code> for a photo. Choose "
        "<code>size</code> (xs, sm, md, lg, xl) or any size with <code>--mj-avatar-size</code>, and "
        "<code>shape=\"square\"</code> for teams, bots or brands. <code>presence</code> adds the "
        "status dot. <code>color</code> overrides the name-derived background (an invalid colour "
        "is ignored with a console warning); <code>--mj-avatar-bg</code> and "
        "<code>--mj-avatar-color-1</code> ... <code>-8</code> restyle it from CSS.</p>"
        "<p>Listen for <code>mj-avatar-image-load</code> / <code>mj-avatar-image-error</code>. "
        "Removing <code>src</code> returns to the initials. Read <code>computedInitials</code>, "
        "<code>imageLoaded</code> and <code>resolvedColor</code> from script.</p>"
    ),
    attributes=[
        AttributeDoc(name="name", description="Full name: accessible name, initials and colour source.",
                     kind="string", values=["Alice Martin", "Bob Chen", "Cara Diaz"]),
        AttributeDoc(name="src", description="Photo URL; the fallback shows until it loads and if it fails.",
                     kind="string"),
        AttributeDoc(name="initials", description="Explicit initials (first two characters used); wins over `name`.",
                     kind="string"),
        AttributeDoc(name="size", description="Preset size.", kind="enum",
                     values=["xs", "sm", "md", "lg", "xl"], default="md"),
        AttributeDoc(name="shape", description="Circle or rounded square.", kind="enum",
                     values=["circle", "square"], default="circle"),
        AttributeDoc(name="presence", description="Shows a status dot; other values draw the offline colour with the value as label.",
                     kind="enum", values=["online", "away", "busy", "offline"]),
        AttributeDoc(name="color", description="Background colour; wins over the palette and `--mj-avatar-bg`.",
                     kind="color"),
        AttributeDoc(name="crossorigin", description="CORS mode forwarded to the inner img.", kind="enum",
                     values=["anonymous", "use-credentials"]),
    ],
    events=[
        ("mj-avatar-image-load", "The photo loaded and replaced the fallback.", "{ src: string }"),
        ("mj-avatar-image-error", "The photo failed; initials or the icon stay.", "{ src: string }"),
    ],
    slots=[
        ("", "A custom `<img>` or `<picture>` that replaces the photo and the fallback.",
         '<img alt="" src="' + _PHOTO_DEV + '">'),
        ("icon", "Replaces the person icon shown when there is no name and no photo.",
         '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l3 7h7l-5.5 4.5 2 7.5-6.5-4.5-6.5 4.5 2-7.5L2 9h7z"/></svg>'),
    ],
    properties=[
        ("computedInitials", "string, read-only. The initials shown in the fallback (\"\" when there is no name)."),
        ("imageLoaded", "boolean, read-only. True once the photo has loaded."),
        ("resolvedColor", "string, read-only. The `color` attribute or the palette entry the name hashes to."),
    ],
    parts=[
        ("frame", "Sizing box holding the avatar and the presence dot."),
        ("container", "The clipped circle/square (role img, named by `name`)."),
        ("img", "The photo."),
        ("initials", "The initials text."),
        ("icon", "The fallback icon."),
        ("presence", "The presence dot."),
    ],
    css_properties=[
        ("--mj-avatar-size", "Edge length; wins over `size` (default 2.25rem for md)."),
        ("--mj-avatar-bg", "Background; wins over the name palette, loses to the `color` attribute."),
        ("--mj-avatar-color-1 ... --mj-avatar-color-8", "The name-hash palette (#2563eb, #7c3aed, #be185d, #b91c1c, #b45309, #047857, #0e7490, #4f46e5). The same in both themes: each keeps 4.5:1 against the white initials."),
        ("--mj-avatar-fg", "Initials and icon colour (default #ffffff)."),
        ("--mj-avatar-font-size", "Initials size (default 40% of the avatar size)."),
        ("--mj-avatar-border-width", "Ring width (default 0px)."),
        ("--mj-avatar-border-color", "Ring colour (default `--mj-border`)."),
        ("--mj-avatar-presence-size", "Dot size (default 28% of the avatar size)."),
        ("--mj-avatar-presence-border", "Dot outline (default `2px solid var(--mj-surface)`)."),
        ("--mj-avatar-presence-online", "Online colour (default `--mj-color-success`)."),
        ("--mj-avatar-presence-away", "Away colour (default `--mj-color-warning`)."),
        ("--mj-avatar-presence-busy", "Busy colour (default `--mj-color-danger`)."),
        ("--mj-avatar-presence-offline", "Offline colour (default `--mj-text-muted`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Initials derived from a name with a presence dot, a photo, and explicit initials "
                "on a square avatar. Controls drive the first avatar.</p>"
            ),
            html=(
                '<div class="row">\n'
                '  <mj-avatar name="Alice Martin" size="lg" presence="online"></mj-avatar>\n'
                '  <mj-avatar name="Bob Chen" src="' + _PHOTO_BOB + '" size="lg" presence="away"></mj-avatar>\n'
                '  <mj-avatar name="Design team" initials="DT" size="lg" shape="square"></mj-avatar>\n'
                '</div>'
            ),
            css=".row { display: flex; gap: var(--mj-space-3); align-items: center; }\n",
        ),
        ComponentExample(
            key="sizes",
            title="Sizes and shapes",
            description=(
                "<p>The five preset sizes as circles and squares, plus a custom 5rem avatar set with "
                "<code>--mj-avatar-size</code>.</p>"
            ),
            html=(
                '<div class="row">\n'
                '  <mj-avatar name="Priya Shah" size="xs"></mj-avatar>\n'
                '  <mj-avatar name="Priya Shah" size="sm"></mj-avatar>\n'
                '  <mj-avatar name="Priya Shah" size="md"></mj-avatar>\n'
                '  <mj-avatar name="Priya Shah" size="lg"></mj-avatar>\n'
                '  <mj-avatar name="Priya Shah" size="xl"></mj-avatar>\n'
                '  <mj-avatar name="Priya Shah" class="huge"></mj-avatar>\n'
                '</div>\n'
                '<div class="row">\n'
                '  <mj-avatar name="Build bot" shape="square" size="xs"></mj-avatar>\n'
                '  <mj-avatar name="Build bot" shape="square" size="sm"></mj-avatar>\n'
                '  <mj-avatar name="Build bot" shape="square" size="md"></mj-avatar>\n'
                '  <mj-avatar name="Build bot" shape="square" size="lg"></mj-avatar>\n'
                '  <mj-avatar name="Build bot" shape="square" size="xl"></mj-avatar>\n'
                '</div>'
            ),
            css=(
                ".row { display: flex; gap: var(--mj-space-3); align-items: center; margin-block-end: var(--mj-space-3); }\n"
                ".huge { --mj-avatar-size: 5rem; }\n"
            ),
        ),
        ComponentExample(
            key="fallbacks",
            title="Fallback chain and slots",
            description=(
                "<p>Left to right: a photo; a broken photo that falls back to initials; no name and no "
                "photo, so the person icon; a custom icon in the <code>icon</code> slot; a slotted "
                "<code>&lt;img&gt;</code> that replaces everything. Watch "
                "<code>mj-avatar-image-error</code> in Events.</p>"
            ),
            html=(
                '<div class="row">\n'
                '  <mj-avatar name="Cara Diaz" src="' + _PHOTO_CARA + '" size="xl"></mj-avatar>\n'
                '  <mj-avatar name="Dana Ortiz" src="' + _MISSING_IMAGE + '" size="xl"></mj-avatar>\n'
                '  <mj-avatar size="xl"></mj-avatar>\n'
                '  <mj-avatar size="xl" shape="square" color="#0e7490">\n'
                '    <svg slot="icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">\n'
                '      <path d="M4 7h16v11H4zM9 3h6v4H9z"/>\n'
                '    </svg>\n'
                '  </mj-avatar>\n'
                '  <mj-avatar name="Devon Reed" size="xl">\n'
                '    <img alt="" src="' + _PHOTO_DEV + '">\n'
                '  </mj-avatar>\n'
                '</div>'
            ),
            css=".row { display: flex; gap: var(--mj-space-3); align-items: center; }\n",
        ),
        ComponentExample(
            key="presence",
            title="Presence states",
            description=(
                "<p>The four presence states; each dot has its own text alternative (\"Online\", "
                "\"Away\" ...). The dot sits outside the clipping circle so it is never cut off.</p>"
            ),
            html=(
                '<ul class="people">\n'
                '  <li><mj-avatar name="Alice Martin" presence="online"></mj-avatar> Alice Martin <small>online</small></li>\n'
                '  <li><mj-avatar name="Bob Chen" src="' + _PHOTO_BOB + '" presence="away"></mj-avatar> Bob Chen <small>away</small></li>\n'
                '  <li><mj-avatar name="Cara Diaz" presence="busy"></mj-avatar> Cara Diaz <small>busy</small></li>\n'
                '  <li><mj-avatar name="Dana Ortiz" presence="offline"></mj-avatar> Dana Ortiz <small>offline</small></li>\n'
                '</ul>'
            ),
            css=(
                ".people { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--mj-space-2); }\n"
                ".people li { display: flex; align-items: center; gap: var(--mj-space-2); }\n"
                ".people small { color: var(--mj-text-muted); }\n"
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Colours and custom properties",
            description=(
                "<p>The <code>color</code> attribute, <code>--mj-avatar-bg</code>, a ring from "
                "<code>--mj-avatar-border-*</code>, and a palette override with "
                "<code>--mj-avatar-color-N</code> applied to a whole stack.</p>"
            ),
            html=(
                '<div class="row">\n'
                '  <mj-avatar name="Ellis Park" size="lg" color="#7c3aed"></mj-avatar>\n'
                '  <mj-avatar name="Fran Liu" size="lg" class="brand"></mj-avatar>\n'
                '  <mj-avatar name="Gus Novak" size="lg" class="ring"></mj-avatar>\n'
                '</div>\n'
                '<div class="stack">\n'
                '  <mj-avatar name="Hana Ito" size="md"></mj-avatar>\n'
                '  <mj-avatar name="Ivan Petrov" size="md"></mj-avatar>\n'
                '  <mj-avatar name="Jo Kim" size="md"></mj-avatar>\n'
                '  <mj-avatar name="Kai Moana" size="md"></mj-avatar>\n'
                '</div>'
            ),
            css=(
                ".row { display: flex; gap: var(--mj-space-3); align-items: center; margin-block-end: var(--mj-space-4); }\n"
                ".brand { --mj-avatar-bg: var(--mj-color-neutral-800, #1f2937); }\n"
                ".ring { --mj-avatar-border-width: 3px; --mj-avatar-border-color: var(--mj-accent); }\n"
                ".stack { display: flex; }\n"
                ".stack mj-avatar {\n"
                "  margin-inline-start: -0.5rem;\n"
                "  --mj-avatar-border-width: 2px; --mj-avatar-border-color: var(--mj-surface);\n"
                "  --mj-avatar-color-1: #334155; --mj-avatar-color-2: #334155; --mj-avatar-color-3: #475569;\n"
                "  --mj-avatar-color-4: #475569; --mj-avatar-color-5: #334155; --mj-avatar-color-6: #475569;\n"
                "  --mj-avatar-color-7: #334155; --mj-avatar-color-8: #475569;\n"
                "}\n"
                ".stack mj-avatar:first-child { margin-inline-start: 0; }\n"
            ),
        ),
        ComponentExample(
            key="events",
            title="Changing the photo",
            description=(
                "<p>The buttons set a working photo, a broken one, or remove <code>src</code>. The log "
                "shows the load/error events and the read-only properties after each change.</p>"
            ),
            html=(
                '<mj-avatar id="live-avatar" name="Cara Diaz" size="xl" presence="busy"></mj-avatar>\n'
                '<div class="buttons">\n'
                '  <button type="button" id="photo-ok">Set photo</button>\n'
                '  <button type="button" id="photo-broken">Broken photo</button>\n'
                '  <button type="button" id="photo-none">Remove src</button>\n'
                '</div>'
            ),
            css=".buttons { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n",
            script=(
                'const avatar = document.getElementById("live-avatar")\n'
                'const report = (label) => mjSandbox.log(label, {\n'
                '  computedInitials: avatar.computedInitials,\n'
                '  imageLoaded: avatar.imageLoaded,\n'
                '  resolvedColor: avatar.resolvedColor\n'
                '})\n'
                'document.getElementById("photo-ok").addEventListener("click", () => {\n'
                '  avatar.setAttribute("src", "' + _PHOTO_CARA + '")\n'
                '})\n'
                'document.getElementById("photo-broken").addEventListener("click", () => {\n'
                '  avatar.setAttribute("src", "' + _MISSING_IMAGE + '")\n'
                '})\n'
                'document.getElementById("photo-none").addEventListener("click", () => {\n'
                '  avatar.removeAttribute("src")\n'
                '  report("src removed")\n'
                '})\n'
                'avatar.addEventListener("mj-avatar-image-load", () => report("after load"))\n'
                'avatar.addEventListener("mj-avatar-image-error", () => report("after error"))\n'
                'report("initial state")\n'
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# mj-media-player
# ---------------------------------------------------------------------------

_POSTER_SVG = (
    '<svg slot="poster" viewBox="0 0 160 90" preserveAspectRatio="xMidYMid slice" aria-hidden="true">\n'
    '    <defs><linearGradient id="poster-sky" x1="0" y1="0" x2="0" y2="1">\n'
    '      <stop offset="0" stop-color="#1e3a8a"/><stop offset="1" stop-color="#f59e6b"/>\n'
    '    </linearGradient></defs>\n'
    '    <rect width="160" height="90" fill="url(#poster-sky)"/>\n'
    '    <circle cx="118" cy="40" r="12" fill="#ffd36b"/>\n'
    '    <path d="M0 70 L40 45 L70 62 L105 38 L160 66 V90 H0Z" fill="#1f2a44"/>\n'
    '    <text x="12" y="22" fill="#ffffff" font-family="sans-serif" font-size="9" font-weight="bold">Product tour</text>\n'
    '  </svg>'
)

_PLAYER_BASIC_SCRIPT = _WAV_HELPER + """
const player = document.getElementById("demo-player")
if (player !== null) {
  player.setAttribute("src", makeChime(12))
}
"""

_PLAYER_CAPTIONS_SCRIPT = _WAV_HELPER + """
const player = document.getElementById("captioned-player")
player.setAttribute("src", makeChime(12))
player.addEventListener("mj-captions-change", (event) => {
  mjSandbox.log("captions now", { track: event.detail.track })
})
"""

_PLAYER_AUDIO_SCRIPT = _WAV_HELPER + """
const player = document.getElementById("audio-player")
player.setAttribute("src", makeChime(8))
"""

_PLAYER_CONTROLS_SCRIPT = _WAV_HELPER + """
const chime = makeChime(12)
for (const player of document.querySelectorAll("mj-media-player")) {
  player.setAttribute("src", chime)
}
document.getElementById("share-btn").addEventListener("click", () => {
  const player = document.getElementById("full-player")
  mjSandbox.log("share at", { currentTime: Math.round(player.currentTime * 10) / 10 })
})
"""

_PLAYER_EVENTS_SCRIPT = _WAV_HELPER + """
const player = document.getElementById("events-player")
player.setAttribute("src", makeChime(12))
const media = player.mediaElement

document.getElementById("btn-play").addEventListener("click", () => {
  // Starting playback from script needs a user gesture unless the media is muted.
  media.play()
})
document.getElementById("btn-pause").addEventListener("click", () => media.pause())
document.getElementById("btn-mute").addEventListener("click", () => { player.muted = !player.muted })
document.getElementById("btn-jump").addEventListener("click", () => {
  // Setting currentTime moves the playhead without an mj-seek event (that is for user seeks).
  player.currentTime = 6
  mjSandbox.log("currentTime set", { currentTime: player.currentTime })
})
document.getElementById("btn-rate").addEventListener("click", () => {
  player.playbackRate = player.playbackRate === 1 ? 1.5 : 1
  mjSandbox.log("playbackRate set", { playbackRate: player.playbackRate })
})

media.addEventListener("loadedmetadata", () => {
  mjSandbox.log("loaded", { duration: player.duration, paused: player.paused })
})
"""

_MEDIA_PLAYER = ComponentDoc(
    tag="mj-media-player",
    title="Media Player",
    group="media",
    summary="Accessible video and audio player with keyboard shortcuts, captions, transcript and fullscreen.",
    description=(
        "<p><code>&lt;mj-media-player&gt;</code> wraps a native <code>&lt;video&gt;</code> or "
        "<code>&lt;audio&gt;</code> element (<code>type</code>) in an accessible control bar: "
        "play/pause, a seek slider with elapsed/total time, mute and volume, a playback-speed menu, "
        "a captions button (shown when the media has a captions or subtitles track) and fullscreen "
        "(video; the whole player goes fullscreen so the controls come along). A buffering spinner "
        "and an error banner appear automatically.</p>"
        "<p>Alternate sources and caption tracks are written as light-DOM "
        "<code>&lt;source&gt;</code> and <code>&lt;track&gt;</code> children; the player mirrors them "
        "into its native element and keeps them in sync. With <code>show-transcript</code> a panel "
        "below the player lists the cues of the active caption track as buttons that seek to their "
        "start, highlighting the current cue; content in the <code>transcript</code> slot replaces "
        "the generated list.</p>"
        "<p>Keyboard shortcuts work while focus is anywhere in the player: Space or K play/pause, "
        "Left/Right seek 5 s, Up/Down change the volume, M mutes, F toggles fullscreen, C cycles "
        "captions, Home/End jump to the start/end and 0-9 jump to 0-90%. A focused control keeps the "
        "keys it needs (Space/Enter on buttons, everything in the speed menu, arrows on the volume "
        "slider, all keys in slotted content), and keys pressed with Ctrl, Alt or Meta are left "
        "alone. Video controls fade out after 3 s of playback without activity and return on "
        "pointer movement, a key press or focus; audio controls never hide.</p>"
        "<p>The examples here have no media file to play (the site works offline), so their "
        "scripts synthesise a short chime as a WAV blob and set it as <code>src</code>; a video "
        "player playing it shows its poster, then a black frame. Supply your own file in "
        "<code>src</code> or <code>&lt;source&gt;</code> children.</p>"
    ),
    how_to_use=(
        "<p>Set <code>label</code> (the region name), then <code>src</code> or one "
        "<code>&lt;source src type&gt;</code> child per format, and "
        "<code>&lt;track kind=\"captions\" src srclang label&gt;</code> children for captions. "
        "<code>poster</code> takes an http(s), relative or raster data: URL (SVG data: URLs are "
        "refused); for artwork in markup use the <code>poster</code> slot. "
        "<code>type=\"audio\"</code> drops the picture and keeps the bar. "
        "<code>controls=\"minimal\"</code> keeps only play and seek, <code>controls=\"none\"</code> "
        "hides the bar (keyboard shortcuts still work). <code>playback-rates</code> sets the speed "
        "menu. Every attribute can change after the first render; changing <code>type</code> "
        "rebuilds the media element.</p>"
        "<p>Script the native element through <code>mediaElement</code> (for example "
        "<code>player.mediaElement.play()</code>) or the <code>currentTime</code>, "
        "<code>volume</code>, <code>muted</code> and <code>playbackRate</code> properties. "
        "<code>mj-seek</code> and <code>mj-rate-change</code> report user actions only; "
        "<code>mj-play</code>, <code>mj-pause</code>, <code>mj-ended</code> and "
        "<code>mj-volume-change</code> follow the media whatever caused the change.</p>"
    ),
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the player region.", kind="string",
                     values=["Product tour", "Podcast episode 12"]),
        AttributeDoc(name="type", description="Native element to use; a change rebuilds it.", kind="enum",
                     values=["video", "audio"], default="video"),
        AttributeDoc(name="src", description="Media URL (http(s), relative, blob: or an audio/video data: URL).",
                     kind="string"),
        AttributeDoc(name="poster", description="Poster image URL (video). Raster data: URLs only; use the poster slot for SVG.",
                     kind="string"),
        AttributeDoc(name="controls", description="`minimal` keeps play and seek; `none` hides the bar.", kind="enum",
                     values=["full", "minimal", "none"], default="full"),
        AttributeDoc(name="aspect-ratio", description="Frame ratio of a video player.", kind="string",
                     values=["16/9", "4/3", "21/9", "1/1"], default="16/9"),
        AttributeDoc(name="playback-rates", description="Space-separated speeds offered in the speed menu.",
                     kind="string", values=["0.5 0.75 1 1.25 1.5 2", "1 1.5 2 3"], default="0.5 0.75 1 1.25 1.5 2"),
        AttributeDoc(name="show-transcript", description="Shows the transcript panel below the player.",
                     kind="boolean"),
        AttributeDoc(name="autoplay", description="Starts playing when possible; suppressed under prefers-reduced-motion and by browser autoplay rules unless muted.",
                     kind="boolean"),
        AttributeDoc(name="muted", description="Starts muted.", kind="boolean"),
        AttributeDoc(name="loop", description="Restarts at the end.", kind="boolean"),
        AttributeDoc(name="preload", description="Native preload hint.", kind="enum",
                     values=["none", "metadata", "auto"], default="metadata"),
        AttributeDoc(name="crossorigin", description="CORS mode forwarded to the native element.", kind="enum",
                     values=["anonymous", "use-credentials"]),
    ],
    events=[
        ("mj-play", "Playback started.", "{ currentTime: number }"),
        ("mj-pause", "Playback paused.", "{ currentTime: number }"),
        ("mj-ended", "The media reached its end (the play button becomes Replay).", "{}"),
        ("mj-seek", "The user moved the playhead (slider, keys or a transcript cue).",
         "{ currentTime: number, previousTime: number }"),
        ("mj-volume-change", "Volume or mute changed.", "{ volume: number, muted: boolean }"),
        ("mj-rate-change", "A speed was picked in the speed menu.", "{ playbackRate: number }"),
        ("mj-captions-change", "The captions button switched tracks; `track` is null when captions are off.",
         "{ track: string | null }"),
        ("mj-transcript-toggle", "`show-transcript` was added or removed.", "{ open: boolean }"),
        ("mj-error", "The media could not be loaded or decoded.", "{ code: number, message: string }"),
    ],
    slots=[
        ("poster", "Artwork shown over the video until playback starts (any markup, e.g. an inline SVG).",
         '<svg viewBox="0 0 160 90" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
         '<rect width="160" height="90" fill="#1e3a8a"/><circle cx="118" cy="40" r="12" fill="#ffd36b"/>'
         '<text x="12" y="22" fill="#fff" font-family="sans-serif" font-size="9">Poster slot</text></svg>'),
        ("controls-end", "Extra controls at the end of the control bar; they keep all their keys.",
         '<button type="button" style="background:none;border:1px solid currentColor;color:inherit;'
         'border-radius:4px;padding:2px 8px;cursor:pointer">Share</button>'),
        ("transcript", "Custom transcript content; replaces the cue list built from the caption track. Shown while `show-transcript` is set.",
         '<div><p><strong>Host:</strong> Welcome to the product tour.</p>'
         '<p><strong>Host:</strong> First, open the dashboard from the menu.</p></div>'),
    ],
    properties=[
        ("mediaElement", "HTMLMediaElement, read-only. The native video/audio element (rebuilt when `type` changes)."),
        ("currentTime", "number. Playhead in seconds; setting it seeks without `mj-seek`."),
        ("duration", "number, read-only. Media length in seconds (NaN before metadata, Infinity for live)."),
        ("paused", "boolean, read-only. True while not playing."),
        ("volume", "number. Volume 0-1; changes emit `mj-volume-change`."),
        ("muted", "boolean. Mute state; changes emit `mj-volume-change`."),
        ("playbackRate", "number. Playback speed; setting it does not emit `mj-rate-change`."),
        ("textTracks", "TextTrackList, read-only. The tracks mirrored from `<track>` children."),
    ],
    parts=[
        ("player", "The outer region (section)."),
        ("media-container", "Box holding the native element, poster, spinner and error."),
        ("media", "The native video/audio element."),
        ("poster", "The layer holding the poster slot."),
        ("loading", "The buffering spinner."),
        ("error", "The error banner."),
        ("controls", "The control bar."),
        ("play-btn", "Play / pause / replay button."),
        ("seek", "The seek slider."),
        ("time", "Elapsed / total time."),
        ("volume", "The mute button."),
        ("speed", "The playback-speed select."),
        ("captions-btn", "The captions toggle (hidden without a caption track)."),
        ("fullscreen-btn", "The fullscreen toggle (video only)."),
        ("transcript", "The transcript panel."),
    ],
    css_properties=[
        ("--mj-player-radius", "Corner radius of the player (default `--mj-radius-md`)."),
        ("--mj-player-bg", "Background behind the picture and of the audio player (default #000). The player stays dark in both themes; these properties retheme it."),
        ("--mj-player-controls-bg", "Control bar background (default rgba(0, 0, 0, 0.75))."),
        ("--mj-player-controls-color", "Control bar text and icon colour (default #fff)."),
        ("--mj-player-track-bg", "Unfilled track of the seek and volume sliders (default rgba(255, 255, 255, 0.3))."),
        ("--mj-player-loading-bg", "Loading overlay over the picture (default rgba(0, 0, 0, 0.4))."),
        ("--mj-player-error-bg", "Error overlay over the picture (default rgba(0, 0, 0, 0.6))."),
        ("--mj-player-overlay-color", "Spinner and error message colour (default #fff)."),
        ("--mj-player-seek-color", "Accent of the seek and volume sliders (default `--mj-accent`)."),
        ("--mj-player-seek-height", "Seek slider thickness (default 4px)."),
        ("--mj-player-transcript-height", "Maximum transcript panel height (default 12rem)."),
        ("--mj-player-transcript-bg", "Transcript panel background (default `--mj-surface`)."),
        ("--mj-player-active-cue-color", "Colour of the current cue (default `--mj-accent`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A video player with artwork in the <code>poster</code> slot. The script gives it a "
                "synthesised 12 second chime as <code>src</code> (no media file ships with the site), so "
                "play, seek, volume and speed all work; the picture turns black once it plays. Try "
                "Space, the arrow keys and M with focus in the player.</p>"
            ),
            html=(
                '<mj-media-player id="demo-player" label="Product tour" aspect-ratio="16/9" style="max-inline-size: 560px">\n'
                '  ' + _POSTER_SVG + '\n'
                '</mj-media-player>'
            ),
            script=_PLAYER_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="captions",
            title="Captions and transcript",
            description=(
                "<p>Two <code>&lt;track&gt;</code> children (English, German) as WebVTT data: URLs make "
                "the CC button appear; press it (or C) to cycle English, German, off. "
                "<code>show-transcript</code> lists the cues: click one to seek there.</p>"
            ),
            html=(
                '<mj-media-player id="captioned-player" label="Product tour with captions" show-transcript\n'
                '  poster="' + _POSTER_PNG + '" style="max-inline-size: 560px">\n'
                '  <track kind="captions" srclang="en" label="English" src="' + _CAPTIONS_EN + '">\n'
                '  <track kind="subtitles" srclang="de" label="Deutsch" src="' + _CAPTIONS_DE + '">\n'
                '</mj-media-player>'
            ),
            script=_PLAYER_CAPTIONS_SCRIPT,
        ),
        ComponentExample(
            key="audio",
            title="Audio player",
            description=(
                "<p><code>type=\"audio\"</code> keeps only the control bar, which never auto-hides. "
                "<code>loop</code> restarts the chime and <code>playback-rates</code> offers 1x to 3x.</p>"
            ),
            html=(
                '<mj-media-player id="audio-player" type="audio" label="Notification chime" loop\n'
                '  playback-rates="1 1.5 2 3" style="max-inline-size: 480px">\n'
                '</mj-media-player>'
            ),
            script=_PLAYER_AUDIO_SCRIPT,
        ),
        ComponentExample(
            key="controls",
            title="Control modes and extra controls",
            description=(
                "<p>The full bar with a Share button in the <code>controls-end</code> slot, "
                "<code>controls=\"minimal\"</code> (play and seek only) and <code>controls=\"none\"</code> "
                "(no bar; focus the player and use the keyboard).</p>"
            ),
            html=(
                '<div class="players">\n'
                '  <mj-media-player id="full-player" label="Full controls">\n'
                '    ' + _POSTER_SVG.replace('poster-sky', 'poster-sky-a') + '\n'
                '    <button slot="controls-end" type="button" id="share-btn" class="share">Share</button>\n'
                '  </mj-media-player>\n'
                '  <mj-media-player label="Minimal controls" controls="minimal"></mj-media-player>\n'
                '  <mj-media-player label="No controls" controls="none"></mj-media-player>\n'
                '</div>'
            ),
            css=(
                ".players { display: grid; grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr)); gap: var(--mj-space-4); }\n"
                ".share {\n"
                "  background: none; color: inherit; border: 1px solid currentColor;\n"
                "  border-radius: var(--mj-radius-sm); padding: 0 var(--mj-space-2); cursor: pointer;\n"
                "}\n"
            ),
            script=_PLAYER_CONTROLS_SCRIPT,
        ),
        ComponentExample(
            key="error",
            title="Error state",
            description=(
                "<p>The <code>src</code> points at a file that does not exist: the player shows the "
                "error banner and <code>mj-error</code> appears in Events.</p>"
            ),
            html=(
                '<mj-media-player label="Missing recording" src="/static/media/missing-recording.mp4"\n'
                '  style="max-inline-size: 480px">\n'
                '</mj-media-player>'
            ),
        ),
        ComponentExample(
            key="events",
            title="Scripting the player",
            description=(
                "<p>Buttons drive the player through <code>mediaElement</code>, <code>muted</code>, "
                "<code>currentTime</code> and <code>playbackRate</code>. Compare the log: script changes "
                "emit <code>mj-play</code>/<code>mj-pause</code>/<code>mj-volume-change</code>, while "
                "<code>mj-seek</code> and <code>mj-rate-change</code> appear only when you use the "
                "player's own slider and speed menu.</p>"
            ),
            html=(
                '<mj-media-player id="events-player" type="audio" label="Scripted chime" style="max-inline-size: 480px">\n'
                '</mj-media-player>\n'
                '<div class="buttons">\n'
                '  <button type="button" id="btn-play">Play</button>\n'
                '  <button type="button" id="btn-pause">Pause</button>\n'
                '  <button type="button" id="btn-mute">Toggle mute</button>\n'
                '  <button type="button" id="btn-jump">currentTime = 6</button>\n'
                '  <button type="button" id="btn-rate">Toggle 1.5x</button>\n'
                '</div>'
            ),
            css=".buttons { display: flex; flex-wrap: wrap; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n",
            script=_PLAYER_EVENTS_SCRIPT,
        ),
    ],
)


# ---------------------------------------------------------------------------
# mj-chart
# ---------------------------------------------------------------------------

_REGIONS = (
    '{"categories":["Q1","Q2","Q3","Q4"],'
    '"series":['
    '{"name":"North","values":[42,58,35,71]},'
    '{"name":"South","values":[55,49,68,80]},'
    '{"name":"West","values":[30,36,44,52]}'
    ']}'
)

_CHANNELS = (
    '{"meta":{"title":"Orders by channel"},'
    '"categories":["Web","Mobile app","Marketplace","Phone","Store"],'
    '"series":['
    '{"name":"2024","values":[120,95,60,25,40]},'
    '{"name":"2025","values":[150,130,70,20,35]}'
    ']}'
)

_TRAFFIC = (
    '{"categories":["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],'
    '"series":['
    '{"name":"Visitors","values":[820,932,901,934,1290,1330,1320]},'
    '{"name":"Sign-ups","values":[120,182,191,234,290,330,310]}'
    ']}'
)

_CHART_DATA_SCRIPT = """\
const chart = document.getElementById("live-chart")
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
let seed = 7
function next() {
  seed = (seed * 9301 + 49297) % 233280
  return 20 + Math.round((seed / 233280) * 80)
}
function freshData() {
  return {
    meta: { title: "Active users" },
    categories: months,
    series: [
      { name: "Free", values: months.map(next) },
      { name: "Pro", values: months.map(next) }
    ]
  }
}

// The data property wins over src and inline JSON.
chart.data = freshData()

document.getElementById("new-data").addEventListener("click", () => {
  chart.data = freshData()
})
document.getElementById("edit-in-place").addEventListener("click", async () => {
  // Mutating the object does not re-render by itself: call redraw() (it returns a Promise).
  chart.data.series[0].values[5] = chart.data.series[0].values[5] + 25
  await chart.redraw()
  mjSandbox.log("redrawn", { june: chart.data.series[0].values[5], state: chart.chartState })
})
document.getElementById("type-select").addEventListener("change", (event) => {
  chart.setAttribute("type", event.target.value)
})
"""

_CHART_EVENTS_SCRIPT = """\
const chart = document.getElementById("event-chart")

chart.addEventListener("mj-chart-render", (event) => {
  mjSandbox.log("rendered", { type: event.detail.type, ms: Math.round(event.detail.duration * 10) / 10 })
})
chart.addEventListener("mj-chart-bar-click", (event) => {
  document.getElementById("picked").textContent =
    event.detail.series + ", " + event.detail.category + ": " + event.detail.value
})

document.getElementById("hide-north").addEventListener("click", () => {
  const changed = chart.hideSeries("North")
  mjSandbox.log("hideSeries('North')", { changed: changed, hiddenSeries: chart.hiddenSeries })
})
document.getElementById("toggle-west").addEventListener("click", () => {
  const visible = chart.toggleSeries("West")
  mjSandbox.log("toggleSeries('West')", { visibleAfter: visible })
})
document.getElementById("show-all").addEventListener("click", () => chart.showAllSeries())
"""

_CHART = ComponentDoc(
    tag="mj-chart",
    title="Chart",
    group="media",
    summary="The chart controller: 139 chart types selected by `type`, drawn as accessible SVG from JSON.",
    description=(
        "<p><code>&lt;mj-chart&gt;</code> is the controller of the chart library. One element covers "
        "every chart type (bar, line, area, pie, scatter, Sankey, treemap, gauge, OHLC, network and "
        "about 130 more), chosen with <code>type</code>; see <a href=\"/charts\">/charts</a> for each "
        "type's data shape and options. It reads JSON from, in priority order, the <code>data</code> "
        "property, the <code>src</code> URL (fetched once per URL and reused; a stale response never "
        "paints) or an inline <code>&lt;script type=\"application/json\"&gt;</code> child (edits to it "
        "re-render), normalises it into a model and draws it as SVG.</p>"
        "<p>It re-renders when the data, <code>type</code>, <code>orientation</code>, any renderer "
        "option attribute (such as <code>group</code> or <code>sort</code> for bars), the set of hidden "
        "series or its size changes. Empty data shows \"No chart data supplied.\" and fires "
        "<code>mj-chart-empty</code>; a fetch failure or malformed JSON shows a generic message and "
        "fires <code>mj-chart-error</code> with the details.</p>"
        "<p>Accessibility: the host is a <code>figure</code> named by <code>label</code> (else a bound "
        "<code>&lt;mj-chart-title&gt;</code>, <code>meta.title</code>, then \"&lt;type&gt; chart\"), "
        "described by <code>description</code>. The focusable marks are one tab stop with Arrow, Home "
        "and End to move between them, and a visually hidden data table follows the drawing.</p>"
        "<p>Three chart parts coordinate with it: <code>&lt;mj-chart-title&gt;</code>, "
        "<code>&lt;mj-chart-legend&gt;</code> (its series entries hide and show series) and "
        "<code>&lt;mj-chart-data-table&gt;</code>. Nest them in the chart or bind them anywhere with "
        "<code>chart=\"&lt;chart id&gt;\"</code>; see their own pages under "
        "<a href=\"/charts\">Chart parts</a>.</p>"
    ),
    how_to_use=(
        "<p>Pick a <code>type</code>, give the chart a height (inline style, a class or a grid cell; "
        "without one it uses <code>--mj-chart-min-height</code> or the type's default, 280px for most) "
        "and supply data shaped for the type: <code>{ categories, series: [{ name, values }] }</code> "
        "for Cartesian charts, <code>{ nodes, links }</code> for flows, <code>{ root }</code> for trees. "
        "Set <code>label</code> for the accessible name.</p>"
        "<p>From script, assign <code>data</code> to replace the data; after mutating the same object "
        "call <code>redraw()</code>; call <code>reload()</code> to fetch <code>src</code> again. Hide "
        "series with <code>hideSeries()</code>, <code>showSeries()</code>, "
        "<code>toggleSeries()</code> and <code>showAllSeries()</code> (a nested legend does the "
        "same). Renderers also emit interaction events such as <code>mj-chart-bar-click</code>, "
        "<code>mj-chart-point-click</code> or <code>mj-chart-node-click</code>; each chart-type page "
        "lists its own.</p>"
    ),
    attributes=[
        AttributeDoc(name="type", description="Chart type key; any of the 139 types listed on /charts.",
                     kind="string", default="bar",
                     values=["bar", "column", "line", "area", "pie", "donut", "scatter", "sankey",
                             "treemap", "gauge", "heatmap", "radar", "funnel", "waterfall"]),
        AttributeDoc(name="label", description="Accessible name of the figure; also the table caption.",
                     kind="string", values=["Revenue by region"]),
        AttributeDoc(name="description", description="Longer text alternative read with the chart.", kind="string"),
        AttributeDoc(name="orientation", description="Cartesian orientation; default `meta.orientation`, then the type's own (vertical for most).",
                     kind="enum", values=["vertical", "horizontal"]),
        AttributeDoc(name="src", description="URL of the JSON data; fetched once per URL.", kind="string"),
        AttributeDoc(name="variant", description="Drawing variant for types that have one, e.g. `candlestick` / `ohlc` for ohlc, `butterfly` for tornado.",
                     kind="string", values=["candlestick", "ohlc", "butterfly", "diverging"]),
        AttributeDoc(name="group", description="Bar/column option: side by side, stacked or 100% stacked.",
                     kind="enum", values=["cluster", "stack", "stack100"], default="cluster"),
        AttributeDoc(name="sort", description="Bar/column option: order categories by their total.",
                     kind="enum", values=["none", "asc", "desc"], default="none"),
    ],
    events=[
        ("mj-chart-render", "A render finished.", "{ type: string, duration: number }"),
        ("mj-chart-empty", "The data holds nothing to draw; the empty message is shown.", "{ type: string }"),
        ("mj-chart-error", "Loading, parsing or drawing failed; the chart shows a generic message.",
         "{ message: string }"),
        ("mj-chart-series-toggle", "A series was hidden or shown (API or legend).",
         "{ series: string, seriesIndex: number, visible: boolean, hidden: boolean, hiddenSeries: string[] }"),
        ("mj-chart-bar-click", "Bar/column renderer: a bar was clicked or activated with Enter/Space.",
         "{ series: string, category: string, value: number }"),
        ("mj-chart-connect", "The controller connected or its id changed (chart parts bind on it).", "{}"),
    ],
    slots=[
        ("", "Chart parts (`mj-chart-title` is drawn above the plot, `mj-chart-legend` and `mj-chart-data-table` below) and the inline JSON script; anything else is hidden.",
         "<mj-chart-legend></mj-chart-legend>"),
    ],
    properties=[
        ("data", "object | null. The chart data; assigning it re-renders and wins over `src` and inline JSON."),
        ("chartState", "string, read-only. `idle`, `loading`, `ready`, `empty`, `error` or `deferred`."),
        ("chartModel", "object | null, read-only. The normalised model `{ meta, categories, series, allSeries, raw }`."),
        ("chartContext", "object | null, read-only. Context of the last render (type, width, height, orientation, colorFor, legend, table...)."),
        ("chartTable", "object | null, read-only. The accessible table `{ columns, rows, caption }` of the last render."),
        ("chartLabel", "string, read-only. The accessible name currently in use."),
        ("hiddenSeries", "string[], read-only. Names of the hidden series (a copy)."),
    ],
    methods=[
        ("redraw() -> Promise", "Renders now; call it after mutating `data` in place."),
        ("reload() -> Promise", "Fetches `src` again (or re-reads the inline JSON) and renders."),
        ("hideSeries(name) -> boolean", "Hides a series; true when it was visible."),
        ("showSeries(name) -> boolean", "Shows a hidden series; true when it was hidden."),
        ("toggleSeries(name) -> boolean", "Flips a series; returns whether it is visible afterwards."),
        ("showAllSeries()", "Shows every hidden series."),
        ("isSeriesHidden(name) -> boolean", "Whether a series is hidden."),
        ("refreshLabel()", "Re-reads the accessible name (a bound title calls it)."),
    ],
    parts=[
        ("surface", "The drawing box holding the SVG and messages."),
        ("description", "The visually hidden description paragraph."),
        ("table", "The visually hidden data table."),
        ("plot", "Renderer group holding the marks (inside the SVG)."),
        ("bar", "Bar/column renderer: each bar."),
    ],
    css_properties=[
        ("--mj-chart-min-height", "Height when the host has none (default: the type's default, 280px for most)."),
        ("--mj-chart-series-1 ... --mj-chart-series-8", "The 8-hue series palette (light and dark values in tokens.css)."),
        ("--mj-chart-series-secondary", "Secondary mark colour used by some renderers."),
        ("--mj-chart-geo-land", "Land fill of the geographic renderers."),
        ("--mj-chart-geo-no-data", "Fill of regions without data (geographic renderers)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A column chart from inline JSON with a nested <code>&lt;mj-chart-legend&gt;</code> "
                "that explains the colours; press an entry to hide that series. Try <code>type</code>, "
                "<code>orientation</code>, <code>group</code> and <code>sort</code> in Controls.</p>"
            ),
            html=(
                '<mj-chart id="quarterly" type="column" label="Revenue by region and quarter" style="height:280px">\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _REGIONS + '</script>\n'
                '</mj-chart>'
            ),
        ),
        ComponentExample(
            key="parts",
            title="Title, legend and data table",
            description=(
                "<p>The three chart parts bound by <code>chart=\"regions\"</code> from outside the "
                "chart: a heading title, a vertical legend beside the plot and a visible data table "
                "below. Hide a series in the legend: the bars and the table column go together.</p>"
            ),
            html=(
                '<mj-chart-title chart="regions" level="2" text="Revenue by region" subtitle="Thousands of euros, 2025"></mj-chart-title>\n'
                '<div class="chart-row">\n'
                '  <mj-chart id="regions" type="column" style="height:240px">\n'
                '    <script type="application/json">' + _REGIONS + '</script>\n'
                '  </mj-chart>\n'
                '  <mj-chart-legend chart="regions" orientation="vertical"></mj-chart-legend>\n'
                '</div>\n'
                '<mj-chart-data-table chart="regions" caption="Revenue per region and quarter"></mj-chart-data-table>'
            ),
            css=(
                ".chart-row { display: flex; gap: var(--mj-space-4); align-items: center; }\n"
                ".chart-row mj-chart { flex: 1; min-inline-size: 0; }\n"
                "mj-chart-data-table { margin-block-start: var(--mj-space-3); }\n"
            ),
        ),
        ComponentExample(
            key="data-property",
            title="Data from script",
            description=(
                "<p>The script assigns <code>data</code>. \"New data\" assigns a fresh object; "
                "\"Edit in place\" mutates the current one and calls <code>redraw()</code>; the select "
                "switches <code>type</code> at run time. The nested title reads <code>meta.title</code>.</p>"
            ),
            html=(
                '<mj-chart id="live-chart" type="line" label="Active users per month" style="height:260px">\n'
                '  <mj-chart-title></mj-chart-title>\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '</mj-chart>\n'
                '<div class="buttons">\n'
                '  <button type="button" id="new-data">New data</button>\n'
                '  <button type="button" id="edit-in-place">Edit in place + redraw()</button>\n'
                '  <label>Type\n'
                '    <select id="type-select">\n'
                '      <option>line</option><option>area</option><option>column</option><option>bar</option>\n'
                '    </select>\n'
                '  </label>\n'
                '</div>'
            ),
            css=".buttons { display: flex; flex-wrap: wrap; gap: var(--mj-space-2); align-items: center; margin-block-start: var(--mj-space-3); }\n",
            script=_CHART_DATA_SCRIPT,
        ),
        ComponentExample(
            key="options",
            title="Renderer options",
            description=(
                "<p>Options are plain attributes read by the renderer: a horizontal, stacked, sorted "
                "bar chart (<code>orientation</code>, <code>group=\"stack\"</code>, "
                "<code>sort=\"desc\"</code>) and a line chart with <code>curve=\"monotone\"</code> and "
                "<code>show-points</code>. Changing one re-renders the chart.</p>"
            ),
            html=(
                '<mj-chart type="bar" orientation="horizontal" group="stack" sort="desc" label="Orders by channel" style="height:260px">\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _CHANNELS + '</script>\n'
                '</mj-chart>\n'
                '<mj-chart type="line" curve="monotone" show-points label="Weekly traffic" style="height:240px">\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _TRAFFIC + '</script>\n'
                '</mj-chart>'
            ),
            css="mj-chart + mj-chart { margin-block-start: var(--mj-space-5); }\n",
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>Empty collections show the empty message (<code>mj-chart-empty</code>); malformed "
                "inline JSON and a <code>src</code> that cannot be fetched show a generic message while "
                "<code>mj-chart-error</code> in Events carries the details.</p>"
            ),
            html=(
                '<div class="grid">\n'
                '  <mj-chart type="column" label="Empty chart" style="height:160px">\n'
                '    <script type="application/json">{"categories":[],"series":[]}</script>\n'
                '  </mj-chart>\n'
                '  <mj-chart type="column" label="Malformed JSON" style="height:160px">\n'
                '    <script type="application/json">{"categories": ["Q1", "Q2"], "series": [</script>\n'
                '  </mj-chart>\n'
                '  <mj-chart type="line" label="Missing data file" src="/static/data/missing-chart.json" style="height:160px"></mj-chart>\n'
                '</div>'
            ),
            css=(
                ".grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr)); gap: var(--mj-space-4); }\n"
                ".grid mj-chart { border: 1px dashed var(--mj-border); border-radius: var(--mj-radius-md); }\n"
            ),
        ),
        ComponentExample(
            key="events",
            title="Series API and events",
            description=(
                "<p>The buttons call <code>hideSeries()</code>, <code>toggleSeries()</code> and "
                "<code>showAllSeries()</code>; the legend follows. Click a bar (or focus the chart, move "
                "with the arrow keys and press Enter) to see <code>mj-chart-bar-click</code>.</p>"
            ),
            html=(
                '<mj-chart id="event-chart" type="column" label="Revenue by region" style="height:260px">\n'
                '  <mj-chart-legend></mj-chart-legend>\n'
                '  <script type="application/json">' + _REGIONS + '</script>\n'
                '</mj-chart>\n'
                '<div class="buttons">\n'
                '  <button type="button" id="hide-north">hideSeries("North")</button>\n'
                '  <button type="button" id="toggle-west">toggleSeries("West")</button>\n'
                '  <button type="button" id="show-all">showAllSeries()</button>\n'
                '</div>\n'
                '<p>Last bar: <output id="picked">none yet</output></p>'
            ),
            css=".buttons { display: flex; flex-wrap: wrap; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n",
            script=_CHART_EVENTS_SCRIPT,
        ),
    ],
)


# ---------------------------------------------------------------------------
# mj-map
# ---------------------------------------------------------------------------

_MAP_BASIC_SCRIPT = """\
const map = document.getElementById("demo-map")
if (map !== null) {
  map.markers = [
    { id: "bkng", label: "Buckingham Palace", lat: 51.5014, lng: -0.1419,
      description: "Official London residence of the UK monarch" },
    { id: "tow", label: "Tower of London", lat: 51.5081, lng: -0.0759,
      description: "Historic castle on the north bank of the Thames" },
    { id: "eye", label: "London Eye", lat: 51.5033, lng: -0.1196,
      description: "Cantilevered observation wheel on the South Bank" },
    { id: "bm", label: "British Museum", lat: 51.5194, lng: -0.127,
      description: "Museum of human history, art and culture" }
  ]
}
"""

_MAP_ADAPTER_SCRIPT = """\
// A tiny provider adapter: an equirectangular SVG "map" with a graticule.
// A real application wraps Leaflet, MapLibre or Google Maps the same way.
const SVG_NS = "http://www.w3.org/2000/svg"
function svgAdapter() {
  const handlers = {}
  const markers = new Map()
  let svg = null
  let view = { lat: 0, lng: 0, zoom: 4 }
  let drag = null
  const scale = () => (256 * Math.pow(2, view.zoom)) / 360
  const project = (lat, lng) => ({
    x: svg.clientWidth / 2 + (lng - view.lng) * scale(),
    y: svg.clientHeight / 2 - (lat - view.lat) * scale()
  })
  const element = (name, attributes) => {
    const node = document.createElementNS(SVG_NS, name)
    for (const key of Object.keys(attributes)) { node.setAttribute(key, attributes[key]) }
    return node
  }
  function draw() {
    if (svg === null) { return }
    svg.textContent = ""
    svg.appendChild(element("rect", { width: "100%", height: "100%", fill: "var(--mj-color-info-surface, #e0f2fe)" }))
    const step = view.zoom >= 6 ? 1 : 5
    for (let lat = -80; lat <= 80; lat += step) {
      const y = project(lat, 0).y
      svg.appendChild(element("line", { x1: 0, x2: "100%", y1: y, y2: y, stroke: "var(--mj-border)" }))
    }
    for (let lng = -180; lng <= 180; lng += step) {
      const x = project(0, lng).x
      svg.appendChild(element("line", { y1: 0, y2: "100%", x1: x, x2: x, stroke: "var(--mj-border)" }))
    }
    for (const marker of markers.values()) {
      const point = project(marker.lat, marker.lng)
      const dot = element("circle", { cx: point.x, cy: point.y, r: 8, fill: "var(--mj-accent)", stroke: "var(--mj-surface)", "stroke-width": 2 })
      dot.style.cursor = "pointer"
      dot.addEventListener("click", () => { if (handlers.markerClick) { handlers.markerClick(marker.id) } })
      const text = element("text", { x: point.x + 12, y: point.y + 4, "font-size": 12, fill: "var(--mj-text)" })
      text.textContent = marker.label
      svg.append(dot, text)
    }
  }
  const moved = () => { draw(); if (handlers.move) { handlers.move({ lat: view.lat, lng: view.lng, zoom: view.zoom }) } }
  return {
    init(target, options) {
      view = { lat: options.lat, lng: options.lng, zoom: options.zoom }
      svg = element("svg", { width: "100%", height: "100%" })
      svg.style.display = "block"
      svg.addEventListener("pointerdown", (event) => { drag = { x: event.clientX, y: event.clientY } })
      svg.addEventListener("pointerup", () => { drag = null })
      svg.addEventListener("pointerleave", () => { drag = null })
      svg.addEventListener("pointermove", (event) => {
        if (drag === null || options.interactive === false) { return }
        this.panBy(drag.x - event.clientX, drag.y - event.clientY)
        drag = { x: event.clientX, y: event.clientY }
      })
      target.appendChild(svg)
      requestAnimationFrame(draw)
    },
    destroy() { if (svg !== null) { svg.remove() } svg = null },
    panTo(lat, lng) { view.lat = lat; view.lng = lng; moved() },
    panBy(dx, dy) { view.lng += dx / scale(); view.lat -= dy / scale(); moved() },
    setZoom(level) { view.zoom = level; draw(); if (handlers.zoom) { handlers.zoom(level) } },
    getCenter() { return { lat: view.lat, lng: view.lng } },
    addMarker(marker) { markers.set(marker.id, marker); draw(); return marker.id },
    removeMarker(handle) { markers.delete(handle); draw() },
    resize() { draw() },
    on(name, handler) { handlers[name] = handler }
  }
}

const map = document.getElementById("adapter-map")
map.markers = [
  { id: "ams", label: "Amsterdam", lat: 52.37, lng: 4.9, description: "Capital of the Netherlands" },
  { id: "bru", label: "Brussels", lat: 50.85, lng: 4.35, description: "Seat of the EU institutions" },
  { id: "par", label: "Paris", lat: 48.86, lng: 2.35, description: "Capital of France" },
  { id: "lux", label: "Luxembourg", lat: 49.61, lng: 6.13, description: "Capital of Luxembourg" }
]
map.addEventListener("mj-map-ready", () => mjSandbox.log("adapter ready", { center: map.center, zoom: map.currentZoom }))
map.adapter = svgAdapter()
"""

_MAP_SLOTS_SCRIPT = """\
const map = document.getElementById("slot-map")
map.markers = [
  { id: "cafe", label: "Harbour Cafe", lat: 59.9075, lng: 10.7372, description: "Open 08:00-18:00" },
  { id: "museum", label: "Maritime Museum", lat: 59.9029, lng: 10.6977, description: "Ships and sea history" },
  { id: "park", label: "Vigeland Park", lat: 59.927, lng: 10.7009, description: "Sculpture park" }
]
// Selecting from script opens the popup (and its slotted content) for that marker.
map.selectedMarkerId = "cafe"

document.getElementById("directions").addEventListener("click", () => {
  mjSandbox.log("directions requested", { marker: map.selectedMarkerId })
})
document.getElementById("reset-view").addEventListener("click", () => {
  map.setAttribute("zoom", "10")
  map.selectedMarkerId = null
})
"""

_MAP_BUBBLES_SCRIPT = """\
// The built-in plot sizes a marker by its `size` (or `value`) field, 6-24 px.
document.getElementById("bubble-map").markers = [
  { id: "ber", label: "Berlin", lat: 52.52, lng: 13.405, size: 22, description: "3.7 million people" },
  { id: "ham", label: "Hamburg", lat: 53.551, lng: 9.993, size: 16, description: "1.9 million people" },
  { id: "muc", label: "Munich", lat: 48.137, lng: 11.575, size: 14, description: "1.5 million people" },
  { id: "cgn", label: "Cologne", lat: 50.937, lng: 6.96, size: 11, description: "1.1 million people" },
  { id: "fra", label: "Frankfurt", lat: 50.11, lng: 8.682, size: 9, description: "0.8 million people" }
]
"""

_MAP_STATES_SCRIPT = """\
const places = [
  { id: "a", label: "Depot", lat: 40.71, lng: -74.0 },
  { id: "b", label: "Warehouse", lat: 40.76, lng: -73.98 }
]
for (const map of document.querySelectorAll("mj-map")) {
  map.markers = places
}

// An adapter whose init throws: the error overlay and mj-map-error appear.
document.getElementById("failing-map").adapter = {
  init() { throw new Error("Map provider key is missing.") },
  destroy() {}, panTo() {}, setZoom() {}, addMarker() {}, removeMarker() {}
}

document.getElementById("toggle-loading").addEventListener("click", () => {
  document.getElementById("loading-map").toggleAttribute("loading")
})
"""

_MAP = ComponentDoc(
    tag="mj-map",
    title="Map",
    group="media",
    summary="Accessible map container with a pluggable provider adapter, built-in marker plot, marker list and popup.",
    description=(
        "<p><code>&lt;mj-map&gt;</code> is an accessible map shell. It does not bundle a tile "
        "engine: a provider adapter (Leaflet, MapLibre, Google Maps ...) supplied through the "
        "<code>adapter</code> property draws the map. Without an adapter it draws a built-in SVG plot "
        "of the markers on a plain grid (no geography): positions are relative to each other, "
        "<code>zoom</code> only scales the marker layer, and a marker's <code>size</code> or "
        "<code>value</code> field sets its radius.</p>"
        "<p>Around the map it adds zoom buttons (and a <code>controls</code> slot for more), an "
        "accessible marker list (visually hidden unless <code>show-list</code>, then shown below the "
        "map area), a popup for the selected marker (with a <code>popup</code> slot), loading and "
        "error overlays and a live region that announces zoom changes. The host is the sizing box: "
        "its height comes from an inline/CSS height or <code>--mj-map-height</code> (400px).</p>"
        "<p>Adapter contract. Required: <code>init(target, options)</code>, <code>destroy()</code>, "
        "<code>panTo(lat, lng)</code>, <code>setZoom(level)</code>, "
        "<code>addMarker(marker) -&gt; handle</code>, <code>removeMarker(handle)</code>. Optional: "
        "<code>resize()</code>, <code>panBy(dx, dy)</code>, <code>getCenter()</code>, "
        "<code>setMapType(type)</code>, <code>setInteractive(flag)</code> and "
        "<code>on(name, handler)</code> for <code>\"move\"</code> ({ lat, lng, zoom? }), "
        "<code>\"zoom\"</code> (level) and <code>\"markerClick\"</code> (marker or id). "
        "<code>init</code> receives <code>{ lat, lng, zoom, minZoom, maxZoom, mapType, interactive, "
        "...adapterOptions }</code>; without <code>setMapType</code>/<code>setInteractive</code> the "
        "adapter is re-initialised when those attributes change.</p>"
        "<p>Keyboard (focus the map): arrow keys pan (adapter with <code>panBy</code>), + / = and - "
        "zoom, Enter or Space on a built-in marker opens its popup, Escape closes the popup and "
        "returns focus to the marker or list link that opened it.</p>"
    ),
    how_to_use=(
        "<p>Always set <code>label</code> (a missing label logs a warning). Set "
        "<code>lat</code>/<code>lng</code>/<code>zoom</code> for the initial view and give the "
        "element a height. Assign <code>markers</code> as "
        "<code>[{ id, label, lat, lng, description?, href?, size? }]</code>, then the "
        "<code>adapter</code> (markers set before it are handed over on init). Read the view with "
        "<code>center</code> and <code>currentZoom</code>; open or clear a popup with "
        "<code>selectedMarkerId</code>.</p>"
        "<p><code>interactive=\"false\"</code> disables zooming and panning, "
        "<code>loading</code> shows the loading overlay, <code>min-zoom</code>/<code>max-zoom</code> "
        "clamp the zoom (the buttons disable at the limits). <code>mj-map-move</code> carries the "
        "centre the adapter reports.</p>"
    ),
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the map region. Required.", kind="string",
                     values=["Central London landmarks"]),
        AttributeDoc(name="lat", description="Centre latitude; changes are forwarded to the adapter.", kind="number",
                     default="0"),
        AttributeDoc(name="lng", description="Centre longitude; changes are forwarded to the adapter.", kind="number",
                     default="0"),
        AttributeDoc(name="zoom", description="Zoom level, clamped to min-zoom..max-zoom; reflects button zooms.",
                     kind="number", default="10"),
        AttributeDoc(name="min-zoom", description="Lowest zoom level.", kind="number", default="1"),
        AttributeDoc(name="max-zoom", description="Highest zoom level.", kind="number", default="20"),
        AttributeDoc(name="show-list", description="Shows the marker list below the map area.", kind="boolean"),
        AttributeDoc(name="interactive", description="`false` disables zoom and pan (buttons, keys, adapter).",
                     kind="boolean", default="true"),
        AttributeDoc(name="loading", description="Shows the loading overlay (`loading=\"false\"` hides it).",
                     kind="boolean"),
        AttributeDoc(name="map-type", description="Passed to the adapter (`setMapType`, or a re-init).", kind="string",
                     values=["road", "satellite", "terrain", "hybrid"], default="road"),
    ],
    events=[
        ("mj-map-ready", "The adapter initialised.", "{}"),
        ("mj-map-marker-select", "A marker was selected (plot, list or adapter); its popup opened.",
         "{ marker: object }"),
        ("mj-map-marker-deselect", "The popup was closed by the user.", "{}"),
        ("mj-map-zoom-change", "The zoom changed (debounced 200 ms).", "{ zoom: number }"),
        ("mj-map-move", "The view moved (debounced 200 ms); the centre is the one the adapter reports.",
         "{ lat: number, lng: number, zoom: number }"),
        ("mj-map-error", "The adapter's init threw; the error overlay shows the message.", "{ message: string }"),
    ],
    slots=[
        ("controls", "Extra buttons in the control overlay, below the zoom buttons.",
         '<button type="button" aria-label="Locate me" style="inline-size:2rem;block-size:2rem;border:none;'
         'background:transparent;cursor:pointer;color:var(--mj-text)">&#9678;</button>'),
        ("popup", "Extra content in the marker popup, below its title and description. Shown while a marker is selected.",
         '<p style="margin:8px 0 0"><a href="#directions">Get directions</a></p>'),
    ],
    properties=[
        ("markers", "object[]. Markers `{ id, label, lat, lng, description?, href?, size?, value? }`; assigning redraws."),
        ("adapter", "object | null. The provider adapter; assigning destroys the old one and initialises the new one."),
        ("adapterOptions", "object. Extra options merged into the adapter's init options."),
        ("center", "{ lat, lng }. The adapter-reported centre, else lat/lng; setting it writes the attributes."),
        ("currentZoom", "number, read-only. The zoom on screen."),
        ("selectedMarkerId", "string | null. Opens the popup for that marker; null closes it silently."),
    ],
    parts=[
        ("container", "The outer region."),
        ("map-area", "The clipped area holding the map, controls and popup."),
        ("map-target", "The element the adapter (or the built-in plot) draws into."),
        ("controls", "The control overlay."),
        ("zoom-in", "Zoom-in button."),
        ("zoom-out", "Zoom-out button."),
        ("popup", "The marker popup."),
        ("loading", "The loading overlay."),
        ("error", "The error overlay."),
        ("marker-list", "The accessible marker list."),
    ],
    css_properties=[
        ("--mj-map-height", "Host height when none is set (default 400px)."),
        ("--mj-map-radius", "Corner radius (default `--mj-radius-md`)."),
        ("--mj-map-surface", "Background of the built-in plot (default `--mj-bg-subtle`)."),
        ("--mj-map-controls-bg", "Control overlay background (default `--mj-surface`)."),
        ("--mj-map-controls-radius", "Control overlay radius (default `--mj-radius-sm`)."),
        ("--mj-map-controls-shadow", "Control overlay shadow (default `--mj-elevation-2`)."),
        ("--mj-map-popup-bg", "Popup background (default `--mj-surface`)."),
        ("--mj-map-popup-width", "Popup width (default 16rem)."),
        ("--mj-map-focus-ring", "Focus ring of the map area (default `--mj-focus-ring`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>No adapter, so the built-in plot places four London landmarks relative to each "
                "other on a grid; <code>show-list</code> shows the marker list below the map. Click a "
                "marker or a list link to open its popup; Escape closes it.</p>"
            ),
            html=(
                '<mj-map id="demo-map"\n'
                '  label="Central London landmarks"\n'
                '  lat="51.505" lng="-0.12" zoom="10"\n'
                '  show-list\n'
                '  style="height:360px">\n'
                '</mj-map>'
            ),
            script=_MAP_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="adapter",
            title="Custom adapter",
            description=(
                "<p>The script implements the adapter contract with a small SVG map (graticule, "
                "markers, drag to pan) and assigns it. Focus the map and use the arrow keys or + / -, "
                "or drag: <code>mj-map-move</code> and <code>mj-map-zoom-change</code> appear in "
                "Events with the adapter's centre.</p>"
            ),
            html=(
                '<mj-map id="adapter-map" label="Benelux capitals" lat="50.8" lng="4.4" zoom="6" min-zoom="3" max-zoom="9"\n'
                '  style="height:340px">\n'
                '</mj-map>'
            ),
            script=_MAP_ADAPTER_SCRIPT,
        ),
        ComponentExample(
            key="slots",
            title="Popup and controls slots",
            description=(
                "<p>A Directions button in the <code>popup</code> slot and a reset button in the "
                "<code>controls</code> slot. The script opens the cafe's popup with "
                "<code>selectedMarkerId</code>; <code>min-zoom</code>/<code>max-zoom</code> stop the "
                "zoom buttons at 8 and 12.</p>"
            ),
            html=(
                '<mj-map id="slot-map" label="Oslo waterfront" lat="59.91" lng="10.72" zoom="10" min-zoom="8" max-zoom="12"\n'
                '  style="height:320px">\n'
                '  <button slot="controls" type="button" id="reset-view" class="map-ctrl" aria-label="Reset view">&#8634;</button>\n'
                '  <p slot="popup" class="popup-actions"><button type="button" id="directions">Directions</button></p>\n'
                '</mj-map>'
            ),
            css=(
                ".map-ctrl {\n"
                "  inline-size: 2rem; block-size: 2rem; border: none; background: transparent;\n"
                "  border-radius: var(--mj-radius-sm); color: var(--mj-text); font-size: 1.1rem; cursor: pointer;\n"
                "}\n"
                ".popup-actions { margin: var(--mj-space-2) 0 0; }\n"
            ),
            script=_MAP_SLOTS_SCRIPT,
        ),
        ComponentExample(
            key="bubbles",
            title="Sized markers",
            description=(
                "<p>Data-driven markers: the built-in plot sizes each city by its <code>size</code> "
                "field. The height comes from <code>--mj-map-height</code> instead of an inline style.</p>"
            ),
            html='<mj-map id="bubble-map" label="Largest German cities" class="short"></mj-map>',
            css=".short { --mj-map-height: 300px; --mj-map-surface: var(--mj-color-info-surface, var(--mj-bg-subtle)); }\n",
            script=_MAP_BUBBLES_SCRIPT,
        ),
        ComponentExample(
            key="states",
            title="Loading, error and static",
            description=(
                "<p>Left: <code>loading</code> shows the overlay (the button toggles it). Middle: an "
                "adapter whose <code>init</code> throws shows the error overlay and fires "
                "<code>mj-map-error</code>. Right: <code>interactive=\"false\"</code> disables the zoom "
                "buttons and keys.</p>"
            ),
            html=(
                '<div class="maps">\n'
                '  <mj-map id="loading-map" label="Loading map" loading style="height:220px"></mj-map>\n'
                '  <mj-map id="failing-map" label="Map with a failing provider" style="height:220px"></mj-map>\n'
                '  <mj-map label="Static map" interactive="false" style="height:220px"></mj-map>\n'
                '</div>\n'
                '<button type="button" id="toggle-loading">Toggle loading</button>'
            ),
            css=(
                ".maps { display: grid; grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr)); gap: var(--mj-space-4);\n"
                "  margin-block-end: var(--mj-space-3); }\n"
            ),
            script=_MAP_STATES_SCRIPT,
        ),
    ],
)


# ---------------------------------------------------------------------------
# mj-gauge
# ---------------------------------------------------------------------------

_GAUGE_BASIC_SCRIPT = """\
const gauge = document.getElementById("gauge-arc")
if (gauge !== null) {
  gauge.thresholds = [
    { value: 0, color: "var(--mj-color-success)", label: "Normal" },
    { value: 70, color: "var(--mj-color-warning)", label: "Warning" },
    { value: 90, color: "var(--mj-color-danger)", label: "Critical" }
  ]
}
"""

_GAUGE_SHAPES_SCRIPT = """\
const bands = [
  { value: 0, color: "var(--mj-color-success)", label: "Good" },
  { value: 60, color: "var(--mj-color-warning)", label: "Fair" },
  { value: 85, color: "var(--mj-color-danger)", label: "Poor" }
]
for (const gauge of document.querySelectorAll("mj-gauge")) {
  gauge.thresholds = bands
}
"""

_GAUGE_THRESHOLDS_SCRIPT = """\
document.getElementById("battery").thresholds = [
  { value: 0, color: "var(--mj-color-danger)", label: "Low", pattern: "crosshatch" },
  { value: 20, color: "var(--mj-color-warning)", label: "Medium", pattern: "dots" },
  { value: 50, color: "var(--mj-color-success)", label: "Full", pattern: "solid" }
]
document.getElementById("nps").thresholds = [
  { value: -100, color: "var(--mj-color-danger)", label: "Detractors" },
  { value: 0, color: "var(--mj-color-warning)", label: "Passive" },
  { value: 50, color: "var(--mj-color-success)", label: "Promoters" }
]
document.getElementById("disk").thresholds = [
  { value: 0, color: "var(--mj-color-info)", label: "OK", pattern: "stripes" },
  { value: 80, color: "var(--mj-color-danger)", label: "Almost full", pattern: "stripes-reverse" }
]
"""

_GAUGE_EVENTS_SCRIPT = """\
const gauge = document.getElementById("live-gauge")
const slider = document.getElementById("value-slider")
gauge.thresholds = [
  { value: 0, color: "var(--mj-color-success)", label: "Normal" },
  { value: 70, color: "var(--mj-color-warning)", label: "Warning" },
  { value: 90, color: "var(--mj-color-danger)", label: "Critical" }
]
slider.addEventListener("input", () => {
  gauge.setAttribute("value", slider.value)
})
document.getElementById("motion").addEventListener("change", (event) => {
  gauge.setAttribute("animated", event.target.checked ? "true" : "false")
})
gauge.addEventListener("mj-gauge-value-change", (event) => {
  document.getElementById("gauge-status").textContent =
    gauge.formattedValue + " (" + (event.detail.threshold || "no band") + ")"
})
"""

_GAUGE = ComponentDoc(
    tag="mj-gauge",
    title="Gauge",
    group="media",
    summary="Single-value arc or linear meter with threshold bands (colour and pattern), needle, animated fill and native meter semantics.",
    description=(
        "<p><code>&lt;mj-gauge&gt;</code> shows one number against a range: as an arc (240 degrees by "
        "default, opening downwards; 180 is a half dial and 360 a ring) or as a horizontal bar "
        "(<code>shape=\"linear\"</code>). Min and max labels are shown by default.</p>"
        "<p>Threshold bands come from the <code>thresholds</code> property: "
        "<code>[{ value, color, label, pattern? }]</code>, where each band starts at its "
        "<code>value</code> and runs to the next one (or <code>max</code>). Bands are drawn along the "
        "track in their colour and a pattern (stripes, dots, crosshatch, stripes-reverse or solid; "
        "bands without one cycle through the first four), so they do not rely on colour alone. The "
        "fill takes the colour and pattern of the band the value falls in, and that band's label is "
        "added to the value text for assistive technology. Colours may be CSS variables such as "
        "<code>var(--mj-color-warning)</code>.</p>"
        "<p>A visually hidden native <code>&lt;meter&gt;</code> carries the semantics (min, max, "
        "value, <code>low</code>/<code>high</code>/<code>optimum</code>, named by "
        "<code>title</code>). The value is formatted with <code>Intl.NumberFormat</code> in "
        "<code>locale</code> with <code>precision</code> decimals and the <code>unit</code> suffix. "
        "Value changes update the existing fill so it animates (unless "
        "<code>animated=\"false\"</code> or prefers-reduced-motion).</p>"
    ),
    how_to_use=(
        "<p>Set <code>value</code>, <code>min</code> and <code>max</code> (values outside are "
        "clamped on the track; the label shows the real value). Give a <code>title</code> for the "
        "visible label and accessible name (as a global attribute it also shows a native tooltip), "
        "or rich content in the <code>title</code> slot; the <code>value-label</code> slot replaces "
        "the formatted value. Assign <code>thresholds</code> for bands. <code>low</code>, "
        "<code>high</code> and <code>optimum</code> only reach the native meter; they do not change "
        "the drawing.</p>"
        "<p>Hide the min/max labels with <code>show-min-max=\"false\"</code>. Listen for "
        "<code>mj-gauge-value-change</code> (with the previous value and the band label) and "
        "<code>mj-gauge-click</code>. Size the gauge with <code>--mj-gauge-size</code>.</p>"
    ),
    attributes=[
        AttributeDoc(name="value", description="The value shown.", kind="number", default="0"),
        AttributeDoc(name="min", description="Start of the range.", kind="number", default="0"),
        AttributeDoc(name="max", description="End of the range; must be greater than `min`.", kind="number",
                     default="100"),
        AttributeDoc(name="title", description="Visible label and accessible name of the meter.", kind="string",
                     values=["CPU usage", "Battery"]),
        AttributeDoc(name="unit", description="Suffix appended to the value and the min/max labels.", kind="string",
                     values=["%", " °C", " ms", " kWh"]),
        AttributeDoc(name="shape", description="Arc dial or horizontal bar.", kind="enum",
                     values=["arc", "linear"], default="arc"),
        AttributeDoc(name="arc-degrees", description="Sweep of the arc, clamped to 90-360 (opening faces down).",
                     kind="number", default="240"),
        AttributeDoc(name="show-needle", description="Draws a needle on the arc.", kind="boolean"),
        AttributeDoc(name="show-min-max", description="Min and max labels; `false` hides them.", kind="boolean",
                     default="true"),
        AttributeDoc(name="precision", description="Decimals of the value label (0-20).", kind="number", default="0"),
        AttributeDoc(name="locale", description="BCP 47 locale for number formatting; default the page locale.",
                     kind="string", values=["en-US", "de-DE", "fr-FR", "hi-IN"]),
        AttributeDoc(name="animated", description="`false` turns off the fill transition.", kind="boolean",
                     default="true"),
        AttributeDoc(name="low", description="Native meter `low` (semantics only).", kind="number"),
        AttributeDoc(name="high", description="Native meter `high` (semantics only).", kind="number"),
        AttributeDoc(name="optimum", description="Native meter `optimum` (semantics only).", kind="number"),
    ],
    events=[
        ("mj-gauge-value-change", "The `value` attribute changed the number shown.",
         "{ value: number, previousValue: number, threshold: string | null }"),
        ("mj-gauge-click", "The gauge was clicked.",
         "{ value: number, min: number, max: number, threshold: string | null }"),
    ],
    slots=[
        ("title", "Rich title content; replaces the `title` text (the meter keeps `title` as its name).",
         "<span>CPU <small>(4 cores)</small></span>"),
        ("value-label", "Replaces the formatted value under the gauge.", "<strong>72% busy</strong>"),
    ],
    properties=[
        ("thresholds", "object[]. Bands `{ value, color, label?, pattern? }`; assigning redraws."),
        ("formattedValue", "string, read-only. The value as displayed (locale, precision, unit)."),
    ],
    parts=[
        ("container", "The outer column."),
        ("title", "The title row."),
        ("track", "The empty track (arc path or bar)."),
        ("threshold-markers", "The band group (arc) or each band (linear)."),
        ("fill", "The value fill."),
        ("needle", "The needle (arc with show-needle)."),
        ("value-label", "The value text."),
        ("min-max", "The min/max row."),
        ("min-label", "The min label."),
        ("max-label", "The max label."),
    ],
    css_properties=[
        ("--mj-gauge-size", "Arc diameter (default 7.5rem); minimum width of a linear gauge (default 10rem)."),
        ("--mj-gauge-fill-color", "Fill colour without thresholds (default `--mj-accent`)."),
        ("--mj-gauge-track-color", "Track colour (default `--mj-bg-muted`)."),
        ("--mj-gauge-track-width", "Linear track thickness (default 0.75rem)."),
        ("--mj-gauge-needle-color", "Needle colour (default `--mj-text`)."),
        ("--mj-gauge-title-font-size", "Title size (default `--mj-font-size-sm`)."),
        ("--mj-gauge-title-color", "Title colour (default `--mj-text-muted`)."),
        ("--mj-gauge-value-font-size", "Value size (default `--mj-font-size-xl`)."),
        ("--mj-gauge-transition-duration", "Fill animation duration (default `--mj-motion-medium`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A 240 degree arc with a needle and three threshold bands; the fill takes the "
                "warning colour and pattern because 72 is in the 70-90 band. Change <code>value</code> "
                "in Controls to watch the fill animate.</p>"
            ),
            html=(
                '<mj-gauge id="gauge-arc"\n'
                '  value="72" min="0" max="100"\n'
                '  title="CPU usage" unit="%"\n'
                '  show-needle>\n'
                '</mj-gauge>'
            ),
            script=_GAUGE_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="shapes",
            title="Arc sweeps and linear",
            description=(
                "<p><code>arc-degrees</code> 180, 240 (default) and 360, and <code>shape=\"linear\"</code>, "
                "all with the same bands.</p>"
            ),
            html=(
                '<div class="row">\n'
                '  <mj-gauge value="64" title="180 degrees" unit="%" arc-degrees="180" show-needle></mj-gauge>\n'
                '  <mj-gauge value="64" title="240 degrees" unit="%"></mj-gauge>\n'
                '  <mj-gauge value="64" title="360 degrees" unit="%" arc-degrees="360"></mj-gauge>\n'
                '  <mj-gauge value="64" title="Linear" unit="%" shape="linear"></mj-gauge>\n'
                '</div>'
            ),
            css=".row { display: flex; flex-wrap: wrap; gap: var(--mj-space-6); align-items: flex-start; }\n",
            script=_GAUGE_SHAPES_SCRIPT,
        ),
        ComponentExample(
            key="thresholds",
            title="Bands, patterns and ranges",
            description=(
                "<p>Explicit band patterns (crosshatch, dots, solid), a range below zero (NPS -100 to "
                "100) with <code>low</code>/<code>high</code>/<code>optimum</code> for the native meter, "
                "and a value above <code>max</code> that is clamped on the track.</p>"
            ),
            html=(
                '<div class="row">\n'
                '  <mj-gauge id="battery" value="15" title="Battery" unit="%" low="20" high="80" optimum="100"></mj-gauge>\n'
                '  <mj-gauge id="nps" value="38" min="-100" max="100" title="Net promoter score" show-needle></mj-gauge>\n'
                '  <mj-gauge id="disk" value="112" max="100" title="Disk (over quota)" unit="%" shape="linear"></mj-gauge>\n'
                '</div>'
            ),
            css=".row { display: flex; flex-wrap: wrap; gap: var(--mj-space-6); align-items: flex-start; }\n",
            script=_GAUGE_THRESHOLDS_SCRIPT,
        ),
        ComponentExample(
            key="formatting",
            title="Locale, precision and slots",
            description=(
                "<p><code>locale=\"de-DE\"</code> with <code>precision=\"1\"</code> and a unit; the "
                "<code>title</code> slot holds rich content and the <code>value-label</code> slot "
                "replaces the number on the second gauge; the third hides the min/max labels.</p>"
            ),
            html=(
                '<div class="row">\n'
                '  <mj-gauge value="1234.56" max="2000" locale="de-DE" precision="1" unit=" kWh" title="Energy this month"></mj-gauge>\n'
                '  <mj-gauge value="38.2" min="35" max="42" precision="1" unit=" °C" title="Body temperature">\n'
                '    <span slot="title">Temperature <small>(oral)</small></span>\n'
                '    <strong slot="value-label">38.2 °C, mild fever</strong>\n'
                '  </mj-gauge>\n'
                '  <mj-gauge value="420" max="1000" unit=" ms" title="Response time" show-min-max="false"></mj-gauge>\n'
                '</div>'
            ),
            css=".row { display: flex; flex-wrap: wrap; gap: var(--mj-space-6); align-items: flex-start; }\n",
        ),
        ComponentExample(
            key="events",
            title="Live value",
            description=(
                "<p>Drag the slider: each change sets <code>value</code>, the fill animates and "
                "<code>mj-gauge-value-change</code> reports the previous value and band. Untick the box "
                "to set <code>animated=\"false\"</code>. Clicking the gauge emits "
                "<code>mj-gauge-click</code>.</p>"
            ),
            html=(
                '<mj-gauge id="live-gauge" value="40" title="Server load" unit="%" show-needle></mj-gauge>\n'
                '<div class="controls">\n'
                '  <label>Value <input type="range" id="value-slider" min="0" max="100" value="40"></label>\n'
                '  <label><input type="checkbox" id="motion" checked> Animated</label>\n'
                '  <output id="gauge-status">40% (Normal)</output>\n'
                '</div>'
            ),
            css=".controls { display: flex; flex-wrap: wrap; gap: var(--mj-space-4); align-items: center; margin-block-start: var(--mj-space-3); }\n",
            script=_GAUGE_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>The <code>--mj-gauge-*</code> custom properties make a large dial and a thick bar.</p>",
            html=(
                '<div class="row">\n'
                '  <mj-gauge class="big" value="58" title="Throughput" unit=" MB/s" max="120" show-needle></mj-gauge>\n'
                '  <mj-gauge class="thick" value="33" title="Upload" unit="%" shape="linear"></mj-gauge>\n'
                '</div>'
            ),
            css=(
                ".row { display: flex; flex-wrap: wrap; gap: var(--mj-space-6); align-items: flex-start; }\n"
                ".big {\n"
                "  --mj-gauge-size: 12rem; --mj-gauge-fill-color: var(--mj-color-info);\n"
                "  --mj-gauge-needle-color: var(--mj-color-danger); --mj-gauge-value-font-size: 2rem;\n"
                "}\n"
                ".thick {\n"
                "  --mj-gauge-size: 16rem; --mj-gauge-track-width: 1.5rem;\n"
                "  --mj-gauge-fill-color: var(--mj-color-success); --mj-gauge-title-color: var(--mj-text);\n"
                "}\n"
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# mj-sparkline
# ---------------------------------------------------------------------------

_SPARKLINE_EVENTS_SCRIPT = """\
const spark = document.getElementById("clickable-spark")
spark.addEventListener("mj-sparkline-click", (event) => {
  document.getElementById("spark-pick").textContent =
    "Week " + (event.detail.index + 1) + ": " + event.detail.value + " orders"
})
document.getElementById("spark-update").addEventListener("click", () => {
  // Appending a value re-renders the sparkline (watch mj-sparkline-render).
  const values = spark.parsedValues
  values.push(Math.round(values[values.length - 1] * 1.1))
  spark.setAttribute("values", values.slice(-10).join(","))
  mjSandbox.log("stats", { min: spark.min, max: spark.max, last: spark.last })
})
"""

_SPARKLINE = ComponentDoc(
    tag="mj-sparkline",
    title="Sparkline",
    group="media",
    summary="Compact inline SVG trend: line, area, bar and win/loss, with reference line, end dot and optional interactive marks.",
    description=(
        "<p><code>&lt;mj-sparkline&gt;</code> is a word-sized chart for text and table cells. Values "
        "come from a comma-separated <code>values</code> attribute, so it is easy to render on the "
        "server. Four types: <code>line</code> (default), <code>area</code> (filled down to zero or the "
        "reference value), <code>bar</code> (positive bars up, negative bars down from the baseline, in "
        "the negative colour) and <code>win-loss</code> (equal columns up for positive, down for "
        "negative, neutral for zero). Bars and columns use one band per value, so nothing spills out of "
        "the box.</p>"
        "<p>An empty or non-numeric entry is a gap. <code>reference-value</code> draws a dashed line "
        "and becomes the baseline of area and bar types. <code>show-end-dot</code> marks the last value "
        "(line and area). <code>curve=\"monotone\"</code> smooths the line without overshooting.</p>"
        "<p>Accessibility: with <code>label</code> the SVG is an image with that name; without it the "
        "SVG is hidden and the element's text content (visually hidden) is the alternative. With "
        "<code>interactive</code> the marks become focusable buttons (\"Point 3: 15\") that respond to "
        "Enter and Space as well as clicks.</p>"
    ),
    how_to_use=(
        "<p>Set <code>values</code> and a <code>type</code>; size it with <code>width</code> and "
        "<code>height</code> (pixels). Always give a text alternative: a <code>label</code> or text "
        "between the tags. Add <code>interactive</code> only when you handle "
        "<code>mj-sparkline-click</code> (clicks emit it either way). <code>animated</code> draws the "
        "line in on each render (skipped under prefers-reduced-motion). <code>locale</code> formats the "
        "numbers in the interactive marks' labels. Read <code>parsedValues</code>, <code>min</code>, "
        "<code>max</code> and <code>last</code> from script.</p>"
    ),
    attributes=[
        AttributeDoc(name="values", description="Comma-separated numbers; empty or non-numeric entries are gaps.",
                     kind="string", values=["12,18,15,22,19,28,25,32", "3,-2,5,0,-4,6", "1,-1,1,1,-1,1"]),
        AttributeDoc(name="type", description="Chart type.", kind="enum",
                     values=["line", "area", "bar", "win-loss"], default="line"),
        AttributeDoc(name="width", description="Width in pixels.", kind="number", default="80"),
        AttributeDoc(name="height", description="Height in pixels.", kind="number", default="24"),
        AttributeDoc(name="label", description="Accessible name; makes the SVG an image.", kind="string"),
        AttributeDoc(name="show-end-dot", description="Dot on the last valid value (line and area).", kind="boolean"),
        AttributeDoc(name="reference-value", description="Dashed reference line; baseline of area and bar types.",
                     kind="number"),
        AttributeDoc(name="curve", description="Line interpolation.", kind="enum",
                     values=["linear", "monotone"], default="linear"),
        AttributeDoc(name="interactive", description="Marks become focusable buttons (Enter/Space emit `mj-sparkline-click`).",
                     kind="boolean"),
        AttributeDoc(name="animated", description="Draws the line in on render.", kind="boolean"),
        AttributeDoc(name="locale", description="Locale of the numbers in the interactive marks' labels.",
                     kind="string", values=["en-US", "de-DE", "fr-FR"]),
    ],
    events=[
        ("mj-sparkline-render", "The sparkline was drawn.", "{ type: string, pointCount: number }"),
        ("mj-sparkline-click", "A bar, win/loss column or the end dot was clicked (or activated with Enter/Space when interactive).",
         "{ index: number, value: number }"),
    ],
    slots=[
        ("", "Text alternative used when there is no `label` (visually hidden).",
         "Revenue rose from 12 to 32 over eight weeks"),
    ],
    properties=[
        ("parsedValues", "number[], read-only. The values as numbers (NaN for gaps)."),
        ("min", "number, read-only. Smallest valid value."),
        ("max", "number, read-only. Largest valid value."),
        ("last", "number, read-only. Last valid value."),
    ],
    parts=[
        ("container", "The wrapper."),
        ("svg", "The SVG."),
        ("line", "The line path (and the dot of a single point)."),
        ("area", "The filled area (area type)."),
        ("bar", "Each bar (bar type)."),
        ("win-loss-col", "Each column (win-loss type)."),
        ("end-dot", "The end dot."),
        ("reference-line", "The dashed reference line."),
    ],
    css_properties=[
        ("--mj-sparkline-color", "Line, area, positive bar and dot colour (default `--mj-accent`)."),
        ("--mj-sparkline-negative-color", "Negative bars and losses (default `--mj-color-danger`)."),
        ("--mj-sparkline-neutral-color", "Zero columns in win-loss (default `--mj-text-muted`)."),
        ("--mj-sparkline-stroke-width", "Line width (default 1.5px)."),
        ("--mj-sparkline-area-opacity", "Area fill opacity (default 0.2)."),
        ("--mj-sparkline-reference-color", "Reference line colour (default `--mj-border`)."),
        ("--mj-sparkline-reference-dash", "Reference line dash pattern (default `3 2`)."),
        ("--mj-sparkline-end-dot-radius", "End dot radius (default 3)."),
        ("--mj-sparkline-transition", "Draw-in duration with `animated` (default `--mj-motion-medium`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A line sparkline inline in a sentence, with an end dot and a <code>label</code> as "
                "its accessible name. Switch <code>type</code> in Controls.</p>"
            ),
            html=(
                '<p>Weekly revenue\n'
                '  <mj-sparkline values="12,18,15,22,19,28,25,32" width="120" height="32" show-end-dot\n'
                '    label="Weekly revenue, rising from 12 to 32 thousand">\n'
                '  </mj-sparkline>\n'
                '  <strong>32k</strong>\n'
                '</p>'
            ),
        ),
        ComponentExample(
            key="types",
            title="Types",
            description=(
                "<p>The same data as line, area and bar (negatives go down in the negative colour), and a "
                "win/loss record where zero is a neutral draw. The text between the tags is the text "
                "alternative.</p>"
            ),
            html=(
                '<dl class="types">\n'
                '  <dt>line</dt><dd><mj-sparkline values="4,7,3,-2,5,8,-1,6" width="140" height="32">Mixed results, ending at 6</mj-sparkline></dd>\n'
                '  <dt>area</dt><dd><mj-sparkline type="area" values="4,7,3,-2,5,8,-1,6" width="140" height="32">Mixed results, ending at 6</mj-sparkline></dd>\n'
                '  <dt>bar</dt><dd><mj-sparkline type="bar" values="4,7,3,-2,5,8,-1,6" width="140" height="32">Mixed results, ending at 6</mj-sparkline></dd>\n'
                '  <dt>win-loss</dt><dd><mj-sparkline type="win-loss" values="1,1,-1,0,1,-1,1,1,1,-1" width="140" height="24">6 wins, 3 losses, 1 draw</mj-sparkline></dd>\n'
                '</dl>'
            ),
            css=(
                ".types { display: grid; grid-template-columns: max-content max-content; gap: var(--mj-space-2) var(--mj-space-4);\n"
                "  align-items: center; margin: 0; }\n"
                ".types dt { color: var(--mj-text-muted); font-family: var(--mj-font-mono, monospace); }\n"
                ".types dd { margin: 0; }\n"
            ),
        ),
        ComponentExample(
            key="table",
            title="In a table, with reference and gaps",
            description=(
                "<p>Sparklines in table cells. The latency row has a <code>reference-value</code> (the "
                "SLA) and a gap (an empty entry); the budget row is a bar type around a reference of "
                "100.</p>"
            ),
            html=(
                '<table class="metrics">\n'
                '  <thead><tr><th scope="col">Metric</th><th scope="col">Last 12 weeks</th><th scope="col">Now</th></tr></thead>\n'
                '  <tbody>\n'
                '    <tr><th scope="row">Sign-ups</th>\n'
                '      <td><mj-sparkline type="area" values="30,32,35,33,40,44,43,50,52,55,61,64" width="120" height="24" show-end-dot>Sign-ups up from 30 to 64</mj-sparkline></td><td>64</td></tr>\n'
                '    <tr><th scope="row">Latency (ms)</th>\n'
                '      <td><mj-sparkline values="180,175,190,,210,260,240,205,190,185,170,165" reference-value="200" width="120" height="24">Latency mostly under the 200 ms SLA, one missing week</mj-sparkline></td><td>165</td></tr>\n'
                '    <tr><th scope="row">Budget (%)</th>\n'
                '      <td><mj-sparkline type="bar" values="92,98,104,110,97,95,101,99,108,96,94,90" reference-value="100" width="120" height="24">Budget around 100 percent</mj-sparkline></td><td>90</td></tr>\n'
                '  </tbody>\n'
                '</table>'
            ),
            css=(
                ".metrics { border-collapse: collapse; }\n"
                ".metrics th, .metrics td { padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border);\n"
                "  text-align: start; }\n"
                ".metrics td:last-child { font-variant-numeric: tabular-nums; }\n"
            ),
        ),
        ComponentExample(
            key="events",
            title="Interactive marks",
            description=(
                "<p><code>interactive</code> bars are buttons: click one, or Tab to it and press Enter, "
                "to see <code>mj-sparkline-click</code>. \"Add week\" appends a value and logs "
                "<code>min</code>, <code>max</code> and <code>last</code>.</p>"
            ),
            html=(
                '<p>Orders per week\n'
                '  <mj-sparkline id="clickable-spark" type="bar" interactive values="14,22,18,25,31,27,35,40"\n'
                '    width="200" height="40" label="Orders per week">\n'
                '  </mj-sparkline>\n'
                '</p>\n'
                '<p><output id="spark-pick">Pick a bar</output></p>\n'
                '<button type="button" id="spark-update">Add week</button>'
            ),
            script=_SPARKLINE_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="options",
            title="Curve and animation",
            description=(
                "<p><code>curve=\"linear\"</code> versus <code>curve=\"monotone\"</code>, and "
                "<code>animated</code> drawing the line in (press Run to replay).</p>"
            ),
            html=(
                '<p>linear <mj-sparkline values="5,20,8,24,6,22,10,26" width="160" height="36" label="Linear curve"></mj-sparkline></p>\n'
                '<p>monotone <mj-sparkline values="5,20,8,24,6,22,10,26" width="160" height="36" curve="monotone" label="Monotone curve"></mj-sparkline></p>\n'
                '<p>animated <mj-sparkline values="5,20,8,24,6,22,10,26" width="160" height="36" curve="monotone" animated show-end-dot label="Animated monotone curve"></mj-sparkline></p>'
            ),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>The <code>--mj-sparkline-*</code> custom properties restyle the line, area, bars and reference line.</p>",
            html=(
                '<p class="green">Uptime <mj-sparkline type="area" values="97,98,99,99,98,100,99,100" width="140" height="32" show-end-dot label="Uptime near 100 percent"></mj-sparkline></p>\n'
                '<p class="warm">P&amp;L <mj-sparkline type="bar" values="5,-3,8,-6,4,9,-2,7" reference-value="0" width="140" height="32" label="Profit and loss by month"></mj-sparkline></p>'
            ),
            css=(
                ".green mj-sparkline {\n"
                "  --mj-sparkline-color: var(--mj-color-success); --mj-sparkline-area-opacity: 0.35;\n"
                "  --mj-sparkline-stroke-width: 2.5px; --mj-sparkline-end-dot-radius: 4;\n"
                "}\n"
                ".warm mj-sparkline {\n"
                "  --mj-sparkline-color: var(--mj-color-info); --mj-sparkline-negative-color: var(--mj-color-warning);\n"
                "  --mj-sparkline-reference-color: var(--mj-text-muted); --mj-sparkline-reference-dash: 1 1;\n"
                "}\n"
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# mj-diagram
# ---------------------------------------------------------------------------

_DIAGRAM_BASIC_SCRIPT = """\
const diagram = document.getElementById("demo-diagram")
if (diagram !== null) {
  diagram.graph = {
    nodes: [
      { id: "ui", label: "UI Layer", description: "Browser-side web components" },
      { id: "api", label: "API Gateway", description: "Handles auth and routing" },
      { id: "db", label: "Database", description: "PostgreSQL persistent store" }
    ],
    edges: [
      { id: "e1", source: "ui", target: "api", label: "HTTP/REST" },
      { id: "e2", source: "api", target: "db", label: "SQL" }
    ]
  }
}
"""

_DIAGRAM_PANEL_SCRIPT = """\
const diagram = document.getElementById("panel-diagram")
diagram.graph = {
  nodes: [
    { id: "web", label: "Web app", description: "React front end", owner: "Team Atlas", uptime: "99.95%" },
    { id: "auth", label: "Auth service", description: "OAuth2 and sessions", owner: "Team Keys", uptime: "99.99%" },
    { id: "orders", label: "Orders", description: "Order lifecycle", owner: "Team Cart", uptime: "99.9%" },
    { id: "pay", label: "Payments", description: "Card and wallet payments", owner: "Team Coin", uptime: "99.97%" },
    { id: "mail", label: "Notifications", description: "E-mail and push", owner: "Team Ping", uptime: "99.5%" }
  ],
  edges: [
    { id: "e1", source: "web", target: "auth", label: "login" },
    { id: "e2", source: "web", target: "orders", label: "REST" },
    { id: "e3", source: "orders", target: "pay", label: "charge" },
    { id: "e4", source: "orders", target: "mail", label: "events" },
    { id: "e5", source: "pay", target: "mail", label: "receipts" }
  ]
}

// Slotted panel content gets a `detail` property ({ node }) when a node is selected;
// fill it from the select event.
const card = document.getElementById("service-card")
diagram.addEventListener("mj-diagram-node-select", (event) => {
  const node = event.detail.node
  card.querySelector("h3").textContent = node.label
  card.querySelector(".owner").textContent = node.owner
  card.querySelector(".uptime").textContent = node.uptime
})
"""

_DIAGRAM_WORKFLOW_SCRIPT = """\
const diagram = document.getElementById("workflow-diagram")
// A pipeline with a retry loop (a cycle) and a self-loop: the built-in layout is cycle-safe.
diagram.graph = {
  nodes: [
    { id: "push", label: "Push" },
    { id: "build", label: "Build" },
    { id: "test", label: "Test" },
    { id: "lint", label: "Lint" },
    { id: "review", label: "Review" },
    { id: "deploy", label: "Deploy" },
    { id: "watch", label: "Monitor" }
  ],
  edges: [
    { source: "push", target: "build" },
    { source: "build", target: "test" },
    { source: "build", target: "lint" },
    { source: "test", target: "review" },
    { source: "lint", target: "review" },
    { source: "review", target: "build", label: "changes requested" },
    { source: "review", target: "deploy", label: "approved" },
    { source: "deploy", target: "watch" },
    { source: "watch", target: "watch", label: "every 5 min" }
  ]
}
document.getElementById("toggle-direction").addEventListener("click", () => {
  const directed = diagram.getAttribute("directed") !== "false"
  diagram.setAttribute("directed", directed ? "false" : "true")
})
"""

_DIAGRAM_STATES_SCRIPT = """\
const small = {
  nodes: [{ id: "a", label: "Draft" }, { id: "b", label: "Published" }],
  edges: [{ source: "a", target: "b", label: "publish" }]
}
document.getElementById("empty-diagram").graph = { nodes: [], edges: [] }
document.getElementById("loading-diagram").graph = small
document.getElementById("static-diagram").graph = small
"""

_DIAGRAM_ADAPTER_SCRIPT = """\
// A minimal layout adapter: nodes on a circle, drawn as SVG. A real application
// wraps Cytoscape, ELK or dagre the same way.
const SVG_NS = "http://www.w3.org/2000/svg"
function circleAdapter() {
  const handlers = {}
  let svg = null
  let graph = null
  let selected = null
  let zoom = 1
  const pan = { x: 0, y: 0 }
  const element = (name, attributes) => {
    const node = document.createElementNS(SVG_NS, name)
    for (const key of Object.keys(attributes)) { node.setAttribute(key, attributes[key]) }
    return node
  }
  function draw() {
    if (svg === null) { return }
    svg.textContent = ""
    if (graph === null) { return }
    const width = svg.clientWidth || 600
    const height = svg.clientHeight || 320
    const radius = Math.min(width, height) / 2 - 40
    const group = element("g", {
      transform: `translate(${width / 2 + pan.x} ${height / 2 + pan.y}) scale(${zoom})`
    })
    const position = new Map()
    graph.nodes.forEach((node, index) => {
      const angle = (index / graph.nodes.length) * 2 * Math.PI - Math.PI / 2
      position.set(node.id, { x: radius * Math.cos(angle), y: radius * Math.sin(angle) })
    })
    for (const edge of graph.edges) {
      const a = position.get(edge.source)
      const b = position.get(edge.target)
      const line = element("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y,
        stroke: "var(--mj-text-muted)", "stroke-width": 6, "stroke-opacity": 0.35 })
      line.style.cursor = "pointer"
      line.addEventListener("click", () => { if (handlers.edgeSelect) { handlers.edgeSelect(edge) } })
      group.appendChild(line)
    }
    for (const node of graph.nodes) {
      const point = position.get(node.id)
      const circle = element("circle", { cx: point.x, cy: point.y, r: 26,
        fill: node.id === selected ? "var(--mj-accent)" : "var(--mj-bg-subtle)",
        stroke: "var(--mj-border-strong)", "stroke-width": 2 })
      circle.style.cursor = "pointer"
      circle.addEventListener("click", () => { if (handlers.nodeSelect) { handlers.nodeSelect(node) } })
      const label = element("text", { x: point.x, y: point.y + 4, "text-anchor": "middle", "font-size": 11,
        fill: node.id === selected ? "var(--mj-text-on-accent)" : "var(--mj-text)", "pointer-events": "none" })
      label.textContent = node.label
      group.append(circle, label)
    }
    svg.appendChild(group)
  }
  return {
    init(target) {
      svg = element("svg", { width: "100%", height: "100%" })
      svg.style.display = "block"
      target.appendChild(svg)
    },
    destroy() { if (svg !== null) { svg.remove() } svg = null },
    setData(next) { graph = next; requestAnimationFrame(draw) },
    setZoom(level) { zoom = level; draw() },
    fit() { zoom = 1; pan.x = 0; pan.y = 0; draw(); if (handlers.zoom) { handlers.zoom(1) } },
    selectNode(id) { selected = id; draw() },
    deselectAll() { selected = null; draw() },
    panBy(dx, dy) { pan.x -= dx; pan.y -= dy; draw(); if (handlers.pan) { handlers.pan({ x: pan.x, y: pan.y }) } },
    resize() { draw() },
    clear() { graph = null; draw() },
    on(name, handler) { handlers[name] = handler }
  }
}

const diagram = document.getElementById("adapter-diagram")
diagram.graph = {
  nodes: [
    { id: "plan", label: "Plan" }, { id: "code", label: "Code" }, { id: "build", label: "Build" },
    { id: "test", label: "Test" }, { id: "release", label: "Release" }, { id: "operate", label: "Operate" }
  ],
  edges: [
    { id: "e1", source: "plan", target: "code", label: "tickets" },
    { id: "e2", source: "code", target: "build" },
    { id: "e3", source: "build", target: "test" },
    { id: "e4", source: "test", target: "release" },
    { id: "e5", source: "release", target: "operate" },
    { id: "e6", source: "operate", target: "plan", label: "feedback" }
  ]
}
diagram.addEventListener("mj-diagram-edge-select", (event) => {
  mjSandbox.log("edge", { id: event.detail.edge.id, from: event.detail.edge.source, to: event.detail.edge.target })
})
diagram.adapter = circleAdapter()
"""

_DIAGRAM = ComponentDoc(
    tag="mj-diagram",
    title="Diagram",
    group="media",
    summary="Accessible node/edge diagram with a built-in layered renderer, pluggable layout adapter, pan/zoom and selection panel.",
    description=(
        "<p><code>&lt;mj-diagram&gt;</code> draws a graph of nodes and edges from its "
        "<code>graph</code> property, <code>{ nodes: [{ id, label?, description? }], edges: [{ id?, "
        "source, target, label? }] }</code>. Without an adapter a built-in renderer lays the graph out "
        "in layers from left to right as SVG. The layout is cycle-safe: back edges and self-loops are "
        "left out of the layering, so any graph lays out in linear time. A layout adapter (Cytoscape, "
        "ELK, dagre ...) assigned to <code>adapter</code> replaces the built-in renderer.</p>"
        "<p>The component adds zoom-in, zoom-out and fit buttons (and a <code>controls</code> slot), an "
        "accessible node list that names each node and its relations (visually hidden unless "
        "<code>show-list</code>), a non-modal selection panel (<code>show-selection-panel</code>) with "
        "the node's label, description and relations by default, loading, error and empty states "
        "(<code>empty</code> slot) and a live region that announces the zoom.</p>"
        "<p>Interaction with the built-in renderer: drag with mouse, pen or touch to pan, pinch with two "
        "fingers to zoom, and use the wheel to zoom while the diagram has focus or Ctrl/Meta is held "
        "(so the page still scrolls across it). Keyboard on the focused diagram: arrow keys pan, + / = "
        "and - zoom, F fits, Enter or Space on a node selects it, Escape clears the selection and "
        "returns focus. One zoom state is reflected to the <code>zoom</code> attribute.</p>"
        "<p>Adapter contract. Required: <code>init(target, options)</code>, <code>destroy()</code>, "
        "<code>setData(graph)</code>, <code>setZoom(level)</code>, <code>fit()</code>, "
        "<code>selectNode(id)</code>, <code>deselectAll()</code>. Optional: <code>resize()</code>, "
        "<code>panBy(dx, dy)</code>, <code>clear()</code> (asked instead of <code>setData</code> for an "
        "empty graph) and <code>on(name, handler)</code> for <code>\"nodeSelect\"</code> (node), "
        "<code>\"edgeSelect\"</code> (edge), <code>\"zoom\"</code> (level) and <code>\"pan\"</code> "
        "({ x, y }). <code>init</code> receives <code>{ directed, interactive, minZoom, maxZoom, "
        "...adapterOptions }</code>; changing <code>directed</code> or <code>interactive</code> "
        "re-initialises it.</p>"
    ),
    how_to_use=(
        "<p>Set <code>label</code> (a missing label logs a warning) and give the element a height "
        "(it fills its container's height, at least <code>--mj-diagram-min-height</code>, 280px). "
        "Assign <code>graph</code>; assign <code>adapter</code> only to use your own layout engine. "
        "<code>directed=\"false\"</code> drops the arrowheads and uses neutral relation text, "
        "<code>interactive=\"false\"</code> turns pan, zoom and selection off. Set "
        "<code>zoom</code> to zoom from outside (no events), <code>selectedNodeId</code> to select "
        "from script (no event), and listen for <code>mj-diagram-node-select</code>.</p>"
        "<p>Content in the <code>selection-panel</code> slot replaces the default details; each "
        "slotted element gets a <code>detail</code> property (<code>{ node }</code>) when a node is "
        "selected.</p>"
    ),
    attributes=[
        AttributeDoc(name="label", description="Accessible name of the diagram region. Required.", kind="string",
                     values=["Software architecture"]),
        AttributeDoc(name="show-list", description="Shows the node list beside the drawing.", kind="boolean"),
        AttributeDoc(name="show-selection-panel", description="Opens the details panel when a node is selected.",
                     kind="boolean"),
        AttributeDoc(name="directed", description="`false` draws edges without arrowheads.", kind="boolean",
                     default="true"),
        AttributeDoc(name="interactive", description="`false` disables pan, zoom and selection.", kind="boolean",
                     default="true"),
        AttributeDoc(name="zoom", description="Zoom scale; reflects the current zoom, setting it zooms without events.",
                     kind="number", default="1"),
        AttributeDoc(name="min-zoom", description="Lowest zoom scale.", kind="number", default="0.25"),
        AttributeDoc(name="max-zoom", description="Highest zoom scale.", kind="number", default="4"),
        AttributeDoc(name="fit-on-load", description="`false` skips fitting new data to the view: the built-in renderer applies `zoom` from the top-start corner instead, and an adapter's `fit()` is not called.",
                     kind="boolean", default="true"),
        AttributeDoc(name="loading", description="Shows the loading overlay (`loading=\"false\"` hides it).",
                     kind="boolean"),
    ],
    events=[
        ("mj-diagram-node-select", "A node was selected (drawing, list or adapter).", "{ node: object }"),
        ("mj-diagram-node-deselect", "The user cleared the selection (close button or Escape).", "{}"),
        ("mj-diagram-edge-select", "The adapter reported an edge selection.", "{ edge: object }"),
        ("mj-diagram-zoom-change", "The user zoomed (debounced 200 ms).", "{ zoom: number }"),
        ("mj-diagram-pan", "The user panned (debounced 200 ms).", "{ x: number, y: number }"),
        ("mj-diagram-ready", "The adapter initialised.", "{}"),
        ("mj-diagram-error", "The adapter threw; the error overlay shows the message.", "{ message: string }"),
    ],
    slots=[
        ("controls", "Extra buttons below the zoom and fit buttons.",
         '<button type="button" aria-label="Export" style="inline-size:2rem;block-size:2rem;border:none;'
         'background:transparent;cursor:pointer;color:var(--mj-text)">&#8681;</button>'),
        ("selection-panel", "Replaces the default node details in the selection panel (shown with `show-selection-panel` while a node is selected); slotted elements receive `.detail = { node }`.",
         '<div><h3 style="margin:0 0 8px">Custom panel</h3><p style="margin:0">Select a node.</p></div>'),
        ("empty", "Shown when the graph has no nodes.",
         '<p style="margin:0">No services yet. <a href="#add">Add the first one</a>.</p>'),
    ],
    properties=[
        ("graph", "object | null. `{ nodes, edges }`; assigning redraws."),
        ("adapter", "object | null. Layout adapter; assigning destroys the old one and initialises the new one."),
        ("adapterOptions", "object. Extra options merged into the adapter's init options."),
        ("selectedNodeId", "string | null. Selects (or clears) a node without an event."),
        ("selectedEdgeId", "string | null. The last edge the adapter reported."),
    ],
    parts=[
        ("container", "The outer region."),
        ("render-target", "The focusable drawing area (built-in SVG or adapter)."),
        ("controls", "The control overlay."),
        ("zoom-in", "Zoom-in button."),
        ("zoom-out", "Zoom-out button."),
        ("fit-btn", "Fit-to-view button."),
        ("node-list", "The accessible node list."),
        ("selection-panel", "The details panel."),
        ("loading", "The loading overlay."),
        ("error", "The error overlay."),
        ("empty", "The empty state."),
    ],
    css_properties=[
        ("--mj-diagram-min-height", "Minimum host height (default 280px)."),
        ("--mj-diagram-height", "Height of the inner container (default 100%)."),
        ("--mj-diagram-radius", "Corner radius (default `--mj-radius-md`)."),
        ("--mj-diagram-bg", "Background (default `--mj-surface`)."),
        ("--mj-diagram-node-bg", "Node fill (default `--mj-bg-subtle`)."),
        ("--mj-diagram-node-border", "Node outline (default `--mj-border-strong`)."),
        ("--mj-diagram-node-text", "Node label colour (default `--mj-text`)."),
        ("--mj-diagram-node-selected-bg", "Selected node fill (default `--mj-accent`)."),
        ("--mj-diagram-node-selected-border", "Selected node outline (default `--mj-text`)."),
        ("--mj-diagram-node-selected-text", "Selected node label (default `--mj-text-on-accent`)."),
        ("--mj-diagram-edge", "Edge and arrowhead colour (default `--mj-text-muted`)."),
        ("--mj-diagram-controls-bg", "Control overlay background (default `--mj-surface`)."),
        ("--mj-diagram-controls-shadow", "Control overlay shadow (default `--mj-elevation-2`)."),
        ("--mj-diagram-selection-panel-width", "Width of the panel and the visible node list (default 16rem)."),
        ("--mj-diagram-focus-ring", "Focus ring colour (default `--mj-focus-ring`)."),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Three layers drawn by the built-in renderer, with the node list shown "
                "(<code>show-list</code>). Drag to pan, focus the diagram and use + / - / F, click a "
                "node to select it.</p>"
            ),
            html=(
                '<mj-diagram id="demo-diagram"\n'
                '  label="Software architecture"\n'
                '  show-list\n'
                '  style="height:400px">\n'
                '</mj-diagram>'
            ),
            script=_DIAGRAM_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="selection-panel",
            title="Selection panel",
            description=(
                "<p><code>show-selection-panel</code> with custom content in the "
                "<code>selection-panel</code> slot, filled from <code>mj-diagram-node-select</code>. "
                "Switch the slot off in Slots to see the default details (label, description, "
                "relations). Escape or the close button deselects.</p>"
            ),
            html=(
                '<mj-diagram id="panel-diagram" label="Service map" show-selection-panel style="height:380px">\n'
                '  <div slot="selection-panel" id="service-card">\n'
                '    <h3>Select a service</h3>\n'
                '    <p>Owner: <span class="owner">-</span></p>\n'
                '    <p>Uptime: <span class="uptime">-</span></p>\n'
                '  </div>\n'
                '</mj-diagram>'
            ),
            css="#service-card h3 { margin: 0 0 var(--mj-space-2); }\n#service-card p { margin: 0 0 var(--mj-space-1); }\n",
            script=_DIAGRAM_PANEL_SCRIPT,
        ),
        ComponentExample(
            key="workflow",
            title="Branches and cycles",
            description=(
                "<p>A CI pipeline with parallel branches, a review loop back to Build and a self-loop. "
                "A button in the <code>controls</code> slot toggles <code>directed</code> (arrowheads and "
                "relation arrows).</p>"
            ),
            html=(
                '<mj-diagram id="workflow-diagram" label="Delivery pipeline" style="height:380px">\n'
                '  <button slot="controls" type="button" id="toggle-direction" class="diagram-ctrl"\n'
                '    aria-label="Toggle arrowheads">&#8644;</button>\n'
                '</mj-diagram>'
            ),
            css=(
                ".diagram-ctrl {\n"
                "  inline-size: 2rem; block-size: 2rem; border: none; background: transparent;\n"
                "  border-radius: var(--mj-radius-sm); color: var(--mj-text); cursor: pointer;\n"
                "}\n"
            ),
            script=_DIAGRAM_WORKFLOW_SCRIPT,
        ),
        ComponentExample(
            key="states",
            title="Empty, loading and static",
            description=(
                "<p>An empty graph shows the <code>empty</code> slot; <code>loading</code> shows the "
                "overlay; <code>interactive=\"false\"</code> disables pan, zoom and selection (the list "
                "buttons are disabled too).</p>"
            ),
            html=(
                '<div class="diagrams">\n'
                '  <mj-diagram id="empty-diagram" label="Empty service map" style="height:220px">\n'
                '    <p slot="empty">No services yet. Add one to start the map.</p>\n'
                '  </mj-diagram>\n'
                '  <mj-diagram id="loading-diagram" label="Loading diagram" loading style="height:220px"></mj-diagram>\n'
                '  <mj-diagram id="static-diagram" label="Static diagram" interactive="false" show-list style="height:220px"></mj-diagram>\n'
                '</div>'
            ),
            css=".diagrams { display: grid; grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr)); gap: var(--mj-space-4); }\n",
            script=_DIAGRAM_STATES_SCRIPT,
        ),
        ComponentExample(
            key="adapter",
            title="Custom layout adapter",
            description=(
                "<p>The script implements the adapter contract with a circular SVG layout. Click a node "
                "(<code>mj-diagram-node-select</code>) or an edge (<code>mj-diagram-edge-select</code>, "
                "which the built-in renderer does not emit); arrow keys call <code>panBy</code> and "
                "+ / - call <code>setZoom</code>.</p>"
            ),
            html='<mj-diagram id="adapter-diagram" label="DevOps cycle" show-list style="height:380px"></mj-diagram>',
            script=_DIAGRAM_ADAPTER_SCRIPT,
        ),
    ],
)


COMPONENTS = [
    _IMAGE,
    _AVATAR,
    _MEDIA_PLAYER,
    _CHART,
    _MAP,
    _GAUGE,
    _SPARKLINE,
    _DIAGRAM,
]
