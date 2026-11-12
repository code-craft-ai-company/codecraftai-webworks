"""
    .. module:: testcomponents.tests.test_func_media

    Functional Playwright tests for the 'media' component group.

    Covers: mj-image, mj-avatar, mj-media-player, mj-chart, mj-map,
    mj-gauge, mj-sparkline, mj-diagram.

    Each test navigates to the component playground, acquires the preview
    iframe, waits for the custom element to be registered, and then
    exercises the component's documented attributes, properties, and events
    using real implementation details from the component JS source.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_preview(page, base_url: str, group: str, tag: str):
    """
        Navigate to a component playground and return the preview iframe Frame.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
        :param group: The component group key (e.g. 'media').
        :param tag: The component custom-element tag name.

        :returns: The Playwright Frame inside the playground preview iframe.
    """

    page.goto(base_url + f"/components/{group}/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


def _fill_and_run(page, html: str):
    """
        Replace the playground editor content and press Run.

        :param page: The Playwright page object.
        :param html: The HTML markup to insert into the editor.

        :returns: The newly re-acquired preview Frame after Run.
    """

    page.get_by_test_id("playground-editor").fill(html)
    page.get_by_test_id("playground-run").click()
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    return frame


def _wait_for_element(frame, tag: str, timeout: int = 15000):
    """
        Wait for a custom element to be registered and present in the frame.

        :param frame: The Playwright Frame object.
        :param tag: The custom-element tag to wait for.
        :param timeout: Maximum milliseconds to wait.

        :returns: None
    """

    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=timeout,
    )
    return


# ---------------------------------------------------------------------------
# mj-image
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_renders_with_alt_and_caption(page, base_url):
    """
        mj-image renders a figure with an img whose alt attribute matches
        and the caption is shown when the caption attribute is set.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-image")
    el = frame.locator("mj-image").first
    expect(el).to_be_attached(timeout=10000)

    # The component renders a shadow root with a figure element.
    has_figure = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('figure') !== null;
        }"""
    )
    assert has_figure is True

    # The inner img carries the alt text set on the host element.
    alt_value = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            if (el === null || el.shadowRoot === null) { return null; }
            const img = el.shadowRoot.querySelector('img.img');
            return img !== null ? img.getAttribute('alt') : null;
        }"""
    )
    assert alt_value is not None

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_eager_loading_sets_src(page, base_url):
    """
        When loading='eager' the component sets the src on the inner img
        immediately without waiting for IntersectionObserver.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-image")

    html = (
        '<mj-image '
        '  src="https://picsum.photos/seed/test/200/100" '
        '  alt="eager test image" '
        '  loading="eager" '
        '  style="max-width:200px">'
        '</mj-image>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-image")

    img_src = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            if (el === null || el.shadowRoot === null) { return null; }
            const img = el.shadowRoot.querySelector('img.img');
            return img !== null ? img.getAttribute('src') : null;
        }"""
    )
    assert img_src == "https://picsum.photos/seed/test/200/100"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_caption_attribute_renders_figcaption(page, base_url):
    """
        The caption attribute causes a figcaption to appear in the shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-image")

    html = (
        '<mj-image '
        '  src="https://picsum.photos/seed/cap/200/100" '
        '  alt="captioned image" '
        '  caption="My test caption" '
        '  loading="eager">'
        '</mj-image>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-image")

    caption_text = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            if (el === null || el.shadowRoot === null) { return null; }
            const fc = el.shadowRoot.querySelector('figcaption.caption');
            return fc !== null ? fc.textContent : null;
        }"""
    )
    assert caption_text == "My test caption"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_placeholder_visible_before_load(page, base_url):
    """
        Before the image loads the placeholder div is present in the shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-image")
    el = frame.locator("mj-image").first
    expect(el).to_be_attached(timeout=10000)

    has_placeholder = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('.placeholder') !== null;
        }"""
    )
    assert has_placeholder is True

    return


# A 1x1 PNG, so image tests do not depend on the network.
_PIXEL_PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_caption_sits_below_the_ratio_box(page, base_url):
    """
        With aspect-ratio set, the figcaption is laid out below the clipped
        ratio box and inside the host, so it is visible rather than cut off.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-image")

    html = (
        f'<mj-image src="{_PIXEL_PNG}" alt="Pixel" loading="eager" '
        'aspect-ratio="16/9" caption="Visible caption" style="width:240px"></mj-image>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-image")

    geometry = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            const box = el.shadowRoot.querySelector('.container').getBoundingClientRect();
            const caption = el.shadowRoot.querySelector('figcaption.caption').getBoundingClientRect();
            const host = el.getBoundingClientRect();
            return {
                boxHeight: box.height,
                captionHeight: caption.height,
                captionBelowBox: caption.top >= box.bottom - 0.5,
                captionInsideHost: caption.bottom <= host.bottom + 0.5
            };
        }"""
    )
    assert abs(geometry["boxHeight"] - 135) < 1.5
    assert geometry["captionHeight"] > 0
    assert geometry["captionBelowBox"] is True
    assert geometry["captionInsideHost"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_caption_slot_is_displayed(page, base_url):
    """
        Content in the caption slot unhides the figcaption and replaces the
        caption attribute text; the slot element survives the attribute.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-image")

    html = (
        f'<mj-image src="{_PIXEL_PNG}" alt="Pixel" loading="eager" caption="Attribute text">'
        '<span slot="caption">Rich <b>slotted</b> caption</span></mj-image>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-image")

    state = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            const caption = el.shadowRoot.querySelector('figcaption.caption');
            return {
                hidden: caption.hidden,
                hasSlot: caption.querySelector('slot[name="caption"]') !== null,
                attributeTextHidden: caption.querySelector('.caption-text').hidden,
                height: caption.getBoundingClientRect().height
            };
        }"""
    )
    assert state["hidden"] is False
    assert state["hasSlot"] is True
    assert state["attributeTextHidden"] is True
    assert state["height"] > 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_failed_load_shows_error_state_with_alt(page, base_url):
    """
        A failed image reveals the error state, which shows the alt text, and
        the container stops being busy.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-image")

    html = (
        '<mj-image src="/static/does-not-exist.png" alt="Team photo" loading="eager" '
        'aspect-ratio="16/9" style="width:240px"></mj-image>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-image")

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-image');
            if (el === null || el.shadowRoot === null) { return false; }
            const error = el.shadowRoot.querySelector('.error');
            return error !== null && error.hidden === false;
        }""",
        timeout=10000,
    )

    state = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            const root = el.shadowRoot;
            return {
                text: root.querySelector('.error-text').textContent,
                busy: root.querySelector('.container').getAttribute('aria-busy'),
                errorHeight: root.querySelector('.error').getBoundingClientRect().height
            };
        }"""
    )
    assert state["text"] == "Team photo"
    assert state["busy"] is None
    assert state["errorHeight"] > 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_image_attribute_changes_after_load(page, base_url):
    """
        Changing alt after the image loaded does not mark it busy again, and
        removing caption / aspect-ratio takes them off the shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-image")

    html = (
        f'<mj-image src="{_PIXEL_PNG}" alt="Pixel" loading="eager" '
        'aspect-ratio="4/3" caption="Going away" style="width:120px"></mj-image>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-image")

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-image');
            if (el === null || el.shadowRoot === null) { return false; }
            const img = el.shadowRoot.querySelector('img.img');
            return img !== null && img.classList.contains('loaded');
        }""",
        timeout=10000,
    )

    state = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-image');
            const root = el.shadowRoot;
            el.setAttribute('alt', 'Changed');
            el.removeAttribute('caption');
            el.removeAttribute('aspect-ratio');
            return {
                busy: root.querySelector('.container').getAttribute('aria-busy'),
                alt: root.querySelector('img.img').getAttribute('alt'),
                captionHidden: root.querySelector('figcaption.caption').hidden,
                ratio: root.querySelector('.container').style.aspectRatio
            };
        }"""
    )
    assert state["busy"] is None
    assert state["alt"] == "Changed"
    assert state["captionHidden"] is True
    assert state["ratio"] == ""

    return


# ---------------------------------------------------------------------------
# mj-avatar
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_avatar_shows_initials_from_name(page, base_url):
    """
        When no src is provided, mj-avatar derives initials from the name
        attribute and shows them in the .initials span.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-avatar")

    html = '<mj-avatar name="Alice Martin" size="lg"></mj-avatar>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-avatar")

    initials_text = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-avatar');
            if (el === null || el.shadowRoot === null) { return null; }
            const span = el.shadowRoot.querySelector('.initials');
            return span !== null ? span.textContent : null;
        }"""
    )
    assert initials_text == "AM"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_avatar_explicit_initials_override_name(page, base_url):
    """
        When the initials attribute is set it takes precedence over name-derived
        initials.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-avatar")

    html = '<mj-avatar initials="XY" size="lg" shape="square"></mj-avatar>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-avatar")

    initials_text = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-avatar');
            if (el === null || el.shadowRoot === null) { return null; }
            const span = el.shadowRoot.querySelector('.initials');
            return span !== null ? span.textContent : null;
        }"""
    )
    assert initials_text == "XY"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_avatar_presence_dot_is_shown(page, base_url):
    """
        When the presence attribute is set the .presence dot becomes visible
        and gets an aria-label matching the presence state.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-avatar")

    html = '<mj-avatar name="Bob Chen" size="lg" presence="online"></mj-avatar>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-avatar")

    presence_label = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-avatar');
            if (el === null || el.shadowRoot === null) { return null; }
            const dot = el.shadowRoot.querySelector('.presence');
            return dot !== null ? dot.getAttribute('aria-label') : null;
        }"""
    )
    assert presence_label == "Online"

    # Children of a role="img" element are presentational, so the dot must
    # be a sibling of the named container for its label to be reachable.
    placement = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-avatar');
            const root = el.shadowRoot;
            const container = root.querySelector('.container');
            const dot = root.querySelector('.presence');
            return {
                containerRole: container.getAttribute('role'),
                dotRole: dot.getAttribute('role'),
                dotInsideContainer: container.contains(dot),
                dotVisible: dot.getBoundingClientRect().width > 0
            };
        }"""
    )
    assert placement["containerRole"] == "img"
    assert placement["dotRole"] == "img"
    assert placement["dotInsideContainer"] is False
    assert placement["dotVisible"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_avatar_removing_src_returns_to_initials(page, base_url):
    """
        After src is removed the photo is no longer shown or referenced and
        the initials fallback is back; a presence change does not reload it.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-avatar")

    html = f'<mj-avatar src="{_PIXEL_PNG}" name="Dana Evans" size="lg"></mj-avatar>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-avatar")

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-avatar');
            if (el === null || el.shadowRoot === null) { return false; }
            const img = el.shadowRoot.querySelector('.img');
            return img !== null && img.classList.contains('visible');
        }""",
        timeout=10000,
    )

    state = frame.evaluate(
        """async () => {
            const el = document.querySelector('mj-avatar');
            const root = el.shadowRoot;
            let loads = 0;
            el.addEventListener('mj-avatar-image-load', () => { loads = loads + 1; });
            el.setAttribute('presence', 'busy');
            el.setAttribute('size', 'md');
            await new Promise((resolve) => setTimeout(resolve, 300));
            const reloads = loads;
            el.removeAttribute('src');
            return {
                reloads: reloads,
                imgVisible: root.querySelector('.img').classList.contains('visible'),
                imgHasSrc: root.querySelector('.img').hasAttribute('src'),
                initialsVisible: root.querySelector('.initials').classList.contains('visible'),
                initials: root.querySelector('.initials').textContent
            };
        }"""
    )
    assert state["reloads"] == 0
    assert state["imgVisible"] is False
    assert state["imgHasSrc"] is False
    assert state["initialsVisible"] is True
    assert state["initials"] == "DE"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_avatar_host_custom_properties_override_size_and_background(page, base_url):
    """
        --mj-avatar-size and --mj-avatar-bg set on the host win over the size
        attribute and the name-derived colour.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-avatar")

    html = (
        '<mj-avatar name="Erin Frost" size="sm" '
        'style="--mj-avatar-size:80px;--mj-avatar-bg:rgb(1, 2, 3)"></mj-avatar>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-avatar")

    rendered = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-avatar');
            const container = el.shadowRoot.querySelector('.container');
            return {
                width: container.getBoundingClientRect().width,
                background: getComputedStyle(container).backgroundColor
            };
        }"""
    )
    assert abs(rendered["width"] - 80) < 0.5
    assert rendered["background"] == "rgb(1, 2, 3)"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_avatar_no_src_shows_icon_fallback(page, base_url):
    """
        When no src and no name/initials are given the icon fallback becomes
        visible.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-avatar")

    html = '<mj-avatar size="md"></mj-avatar>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-avatar")

    icon_visible = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-avatar');
            if (el === null || el.shadowRoot === null) { return false; }
            const icon = el.shadowRoot.querySelector('.icon');
            return icon !== null && icon.classList.contains('visible');
        }"""
    )
    assert icon_visible is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_avatar_container_has_aria_label(page, base_url):
    """
        The .container element carries an aria-label derived from the name.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-avatar")

    html = '<mj-avatar name="Carol Davis" size="md"></mj-avatar>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-avatar")

    container_label = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-avatar');
            if (el === null || el.shadowRoot === null) { return null; }
            const container = el.shadowRoot.querySelector('.container');
            return container !== null ? container.getAttribute('aria-label') : null;
        }"""
    )
    assert container_label == "Carol Davis"

    return


# ---------------------------------------------------------------------------
# mj-media-player
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_renders_controls(page, base_url):
    """
        mj-media-player renders a play button, seek range, and volume control
        in its shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-media-player")
    el = frame.locator("mj-media-player").first
    expect(el).to_be_attached(timeout=10000)

    has_controls = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            if (el === null || el.shadowRoot === null) { return false; }
            const sr = el.shadowRoot;
            const play = sr.querySelector('[part="play-btn"]');
            const seek = sr.querySelector('.seek');
            const volume = sr.querySelector('.volume-range');
            return play !== null && seek !== null && volume !== null;
        }"""
    )
    assert has_controls is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_controls_stay_on_video_with_transcript(page, base_url):
    """
        With show-transcript the video's control bar overlays the bottom of
        the picture and the transcript sits below it (the bar used to be
        pinned to the bottom of the whole player, on top of the transcript,
        where the cue buttons covered the CC button).

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")
    frame = _fill_and_run(page, (
        '<mj-media-player id="p" label="Tour" show-transcript style="max-inline-size: 480px">'
        '<track kind="captions" srclang="en" label="English" '
        'src="data:text/vtt,WEBVTT%0A%0A00:00.000%20--%3E%2000:02.000%0AHello%0A%0A'
        '00:02.000%20--%3E%2000:04.000%0AWorld%0A">'
        '</mj-media-player>'
    ))
    _wait_for_element(frame, "mj-media-player")
    frame.wait_for_function(
        "() => document.getElementById('p').shadowRoot.querySelectorAll('.cue').length === 2"
    )

    geometry = frame.evaluate(
        """() => {
            const root = document.getElementById('p').shadowRoot;
            const box = (selector) => root.querySelector(selector).getBoundingClientRect();
            const media = box('.media-container');
            const controls = box('.controls');
            const transcript = box('.transcript');
            const cc = box('.captions-btn');
            const hit = root.elementFromPoint(cc.x + cc.width / 2, cc.y + cc.height / 2);
            return {
                controlsBottom: Math.round(controls.bottom),
                controlsTop: Math.round(controls.top),
                mediaBottom: Math.round(media.bottom),
                mediaTop: Math.round(media.top),
                transcriptTop: Math.round(transcript.top),
                ccOnTop: hit !== null && hit.classList.contains('captions-btn'),
            };
        }"""
    )
    assert geometry["controlsBottom"] == geometry["mediaBottom"], geometry
    assert geometry["controlsTop"] > geometry["mediaTop"], geometry
    assert geometry["transcriptTop"] >= geometry["mediaBottom"], geometry
    assert geometry["ccOnTop"] is True, geometry

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_video_type_renders_video_element(page, base_url):
    """
        When type='video' the component creates a native <video> element
        inside the shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-media-player")
    el = frame.locator("mj-media-player").first
    expect(el).to_be_attached(timeout=10000)

    has_video = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('video') !== null;
        }"""
    )
    assert has_video is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_audio_type_renders_audio_element(page, base_url):
    """
        When type='audio' the component creates a native <audio> element.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")

    html = (
        '<mj-media-player '
        '  type="audio" '
        '  src="https://www.w3schools.com/html/horse.ogg" '
        '  label="Test audio player">'
        '</mj-media-player>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-media-player")

    has_audio = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('audio') !== null;
        }"""
    )
    assert has_audio is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_accessible_label(page, base_url):
    """
        The player section element carries the aria-label from the label
        attribute.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")

    html = (
        '<mj-media-player '
        '  type="video" '
        '  src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4" '
        '  label="Accessibility label test">'
        '</mj-media-player>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-media-player")

    section_label = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            if (el === null || el.shadowRoot === null) { return null; }
            const section = el.shadowRoot.querySelector('section');
            return section !== null ? section.getAttribute('aria-label') : null;
        }"""
    )
    assert section_label == "Accessibility label test"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_speed_select_has_options(page, base_url):
    """
        The speed select element contains the default playback rate options.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-media-player")
    el = frame.locator("mj-media-player").first
    expect(el).to_be_attached(timeout=10000)

    speed_options = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            if (el === null || el.shadowRoot === null) { return []; }
            const select = el.shadowRoot.querySelector('.speed-select');
            if (select === null) { return []; }
            return Array.from(select.options).map(o => o.value);
        }"""
    )
    assert "1" in speed_options
    assert len(speed_options) >= 4

    return


# JavaScript that defines window.__mjMakeWav(seconds): a blob URL for a silent
# WAV file, so playback tests do not depend on the network or on codecs.
_DEFINE_MAKE_WAV = """() => {
    window.__mjMakeWav = (seconds) => {
        const rate = 8000;
        const count = rate * seconds;
        const buffer = new ArrayBuffer(44 + count);
        const view = new DataView(buffer);
        const text = (offset, value) => {
            for (let i = 0; i < value.length; i = i + 1) {
                view.setUint8(offset + i, value.charCodeAt(i));
            }
        };
        text(0, 'RIFF'); view.setUint32(4, 36 + count, true); text(8, 'WAVE');
        text(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
        view.setUint16(22, 1, true); view.setUint32(24, rate, true);
        view.setUint32(28, rate, true); view.setUint16(32, 1, true);
        view.setUint16(34, 8, true); text(36, 'data'); view.setUint32(40, count, true);
        for (let i = 0; i < count; i = i + 1) { view.setUint8(44 + i, 128); }
        return URL.createObjectURL(new Blob([buffer], { type: 'audio/wav' }));
    };
}"""


def _start_playback(frame, media_tag: str):
    """
        Give the player a generated WAV source, press its play button with a
        real click and wait until the native media element is playing.

        :param frame: The Playwright Frame containing one mj-media-player.
        :param media_tag: 'audio' or 'video', the native element to wait on.

        :returns: None
    """

    frame.evaluate(_DEFINE_MAKE_WAV)
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            el.setAttribute('src', window.__mjMakeWav(30));
        }"""
    )
    frame.wait_for_function(
        """(tag) => {
            const el = document.querySelector('mj-media-player');
            const media = el.shadowRoot.querySelector(tag);
            return media !== null && media.readyState >= 1;
        }""",
        arg=media_tag,
        timeout=10000,
    )
    frame.locator("mj-media-player .play-btn").click()
    frame.wait_for_function(
        """(tag) => {
            const el = document.querySelector('mj-media-player');
            const media = el.shadowRoot.querySelector(tag);
            return media !== null && media.paused === false;
        }""",
        arg=media_tag,
        timeout=10000,
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_audio_controls_stay_visible_while_playing(page, base_url):
    """
        The audio control bar never auto-hides: well past the three second
        hide delay it is still opaque and the pause button still works.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")

    html = '<mj-media-player type="audio" label="Audio auto-hide test"></mj-media-player>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-media-player")

    _start_playback(frame, "audio")
    page.wait_for_timeout(3600)

    controls = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            const bar = el.shadowRoot.querySelector('.controls');
            const style = getComputedStyle(bar);
            return {
                hiddenClass: bar.classList.contains('hidden'),
                opacity: style.opacity,
                pointerEvents: style.pointerEvents,
                playLabel: el.shadowRoot.querySelector('.play-btn').getAttribute('aria-label')
            };
        }"""
    )
    assert controls["hiddenClass"] is False
    assert controls["opacity"] == "1"
    assert controls["pointerEvents"] != "none"
    assert controls["playLabel"] == "Pause"

    frame.locator("mj-media-player .play-btn").click()
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-media-player');
            return el.shadowRoot.querySelector('audio').paused === true;
        }""",
        timeout=10000,
    )

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_video_controls_return_on_focus(page, base_url):
    """
        Video controls fade out during playback, come back as soon as focus
        enters the control bar, and stay while focus is inside it.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")

    html = '<mj-media-player label="Video auto-hide test" style="max-width:320px"></mj-media-player>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-media-player")

    _start_playback(frame, "video")

    # Take focus and the pointer away so nothing counts as activity.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            const active = el.shadowRoot.activeElement;
            if (active !== null) { active.blur(); }
        }"""
    )
    page.mouse.move(0, 0)

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-media-player');
            return el.shadowRoot.querySelector('.controls').classList.contains('hidden');
        }""",
        timeout=10000,
    )

    shown_on_focus = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            el.shadowRoot.querySelector('.mute-btn').focus();
            return el.shadowRoot.querySelector('.controls').classList.contains('hidden') === false;
        }"""
    )
    assert shown_on_focus is True

    page.wait_for_timeout(3600)
    still_shown = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            return el.shadowRoot.querySelector('.controls').classList.contains('hidden') === false;
        }"""
    )
    assert still_shown is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_mirrors_source_and_track_children(page, base_url):
    """
        <source> and <track> children of the host are mirrored into the native
        media element: the media loads from the source, the caption track is
        available, the captions button appears and toggles the track.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")

    html = '<mj-media-player label="Slotted sources test" style="max-width:320px"></mj-media-player>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-media-player")

    frame.evaluate(_DEFINE_MAKE_WAV)
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            const vtt = URL.createObjectURL(new Blob(
                ['WEBVTT\\n\\n00:00.000 --> 00:05.000\\nFirst cue\\n\\n00:05.000 --> 00:10.000\\nSecond cue\\n'],
                { type: 'text/vtt' }
            ));
            const source = document.createElement('source');
            source.setAttribute('src', window.__mjMakeWav(12));
            source.setAttribute('type', 'audio/wav');
            const track = document.createElement('track');
            track.setAttribute('kind', 'captions');
            track.setAttribute('src', vtt);
            track.setAttribute('srclang', 'en');
            track.setAttribute('label', 'English');
            el.appendChild(source);
            el.appendChild(track);
            el.setAttribute('show-transcript', '');
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-media-player');
            const media = el.shadowRoot.querySelector('video');
            return media.readyState >= 1 && media.textTracks.length === 1 &&
                el.shadowRoot.querySelectorAll('.cue').length === 2;
        }""",
        timeout=10000,
    )

    state = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            const root = el.shadowRoot;
            const media = root.querySelector('video');
            const button = root.querySelector('.captions-btn');
            const before = { hidden: button.hidden, pressed: button.getAttribute('aria-pressed') };
            const changes = [];
            el.addEventListener('mj-captions-change', (event) => { changes.push(event.detail.track); });
            button.click();
            return {
                duration: Math.round(media.duration),
                mirroredSources: media.querySelectorAll('source').length,
                lightChildrenKept: el.querySelectorAll('source, track').length,
                before: before,
                pressedAfter: button.getAttribute('aria-pressed'),
                mode: media.textTracks[0].mode,
                changes: changes,
                cues: Array.from(root.querySelectorAll('.cue')).map((cue) => cue.textContent)
            };
        }"""
    )
    assert state["duration"] == 12
    assert state["mirroredSources"] == 1
    assert state["lightChildrenKept"] == 2
    assert state["before"] == {"hidden": False, "pressed": "false"}
    assert state["pressedAfter"] == "true"
    assert state["mode"] == "showing"
    assert state["changes"] == ["English"]
    assert state["cues"] == ["First cue", "Second cue"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_shortcuts_leave_focused_controls_their_keys(page, base_url):
    """
        Player shortcuts do not take Space from a button, digits or arrows
        from the speed select, arrows from the volume slider, or any key
        pressed with Ctrl; letters still work from a focused button.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")

    html = '<mj-media-player type="audio" label="Shortcut test"></mj-media-player>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-media-player")

    frame.evaluate(_DEFINE_MAKE_WAV)
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            el.setAttribute('src', window.__mjMakeWav(30));
        }"""
    )
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-media-player');
            return el.shadowRoot.querySelector('audio').readyState >= 1;
        }""",
        timeout=10000,
    )

    result = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            const root = el.shadowRoot;
            const media = root.querySelector('audio');
            const press = (target, key, extra) => {
                const event = new KeyboardEvent('keydown', Object.assign(
                    { key: key, bubbles: true, composed: true, cancelable: true }, extra || {}
                ));
                target.dispatchEvent(event);
                return event.defaultPrevented;
            };
            const mute = root.querySelector('.mute-btn');
            const select = root.querySelector('.speed-select');
            const volume = root.querySelector('.volume-range');
            const seek = root.querySelector('.seek');
            const out = {};
            out.spaceOnButton = press(mute, ' ');
            out.pausedAfterSpace = media.paused;
            out.ctrlC = press(mute, 'c', { ctrlKey: true });
            out.digitOnSelect = press(select, '5');
            out.arrowOnSelect = press(select, 'ArrowDown');
            out.arrowOnVolume = press(volume, 'ArrowLeft');
            out.timeUntouched = media.currentTime;
            out.letterOnButton = press(mute, 'm');
            out.mutedAfterLetter = media.muted;
            out.arrowOnSeek = press(seek, 'ArrowRight');
            out.timeAfterSeek = media.currentTime;
            return out;
        }"""
    )
    assert result["spaceOnButton"] is False
    assert result["pausedAfterSpace"] is True
    assert result["ctrlC"] is False
    assert result["digitOnSelect"] is False
    assert result["arrowOnSelect"] is False
    assert result["arrowOnVolume"] is False
    assert result["timeUntouched"] == 0
    assert result["letterOnButton"] is True
    assert result["mutedAfterLetter"] is True
    assert result["arrowOnSeek"] is True
    assert result["timeAfterSeek"] == 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_media_player_attribute_changes_apply_after_render(page, base_url):
    """
        loop, muted, preload, controls and type changes made after the first
        render reach the native media element and the control bar.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-media-player")

    html = '<mj-media-player label="Attribute test" style="max-width:320px"></mj-media-player>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-media-player")

    state = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-media-player');
            const root = el.shadowRoot;
            el.setAttribute('loop', '');
            el.setAttribute('muted', '');
            el.setAttribute('preload', 'none');
            el.setAttribute('controls', 'minimal');
            const video = root.querySelector('video');
            const out = {
                loop: video.loop,
                muted: video.muted,
                preload: video.getAttribute('preload'),
                muteLabel: root.querySelector('.mute-btn').getAttribute('aria-label'),
                minimalHidesMute: getComputedStyle(root.querySelector('.mute-btn')).display,
                minimalKeepsSeek: getComputedStyle(root.querySelector('.seek')).display
            };
            el.setAttribute('controls', 'none');
            out.noneHidesBar = getComputedStyle(root.querySelector('.controls')).display;
            el.removeAttribute('controls');
            el.setAttribute('type', 'audio');
            out.audioAfterTypeChange = root.querySelector('audio') !== null && root.querySelector('video') === null;
            out.loopCarriedOver = root.querySelector('audio').loop;
            return out;
        }"""
    )
    assert state["loop"] is True
    assert state["muted"] is True
    assert state["preload"] == "none"
    assert state["muteLabel"] == "Unmute"
    assert state["minimalHidesMute"] == "none"
    assert state["minimalKeepsSeek"] != "none"
    assert state["noneHidesBar"] == "none"
    assert state["audioAfterTypeChange"] is True
    assert state["loopCarriedOver"] is True

    return


# ---------------------------------------------------------------------------
# mj-chart
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_accessible_table_is_present(page, base_url):
    """
        The chart always renders an accessible data table (possibly hidden)
        with thead and tbody populated from the data.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")
    el = frame.locator("mj-chart").first
    expect(el).to_be_attached(timeout=10000)

    # Delete the own data property set by the example script so that assigning
    # goes through the prototype setter which calls _draw() to build the table.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-chart');
            if (el === null) { return; }
            delete el.data;
            el.data = {
                labels: ['Q1', 'Q2', 'Q3'],
                series: [{ name: 'Revenue', values: [100, 200, 150] }]
            };
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-chart');
            if (el === null || el.shadowRoot === null) { return false; }
            const tbody = el.shadowRoot.querySelector('table tbody');
            return tbody !== null && tbody.querySelectorAll('tr').length > 0;
        }""",
        timeout=10000,
    )

    table_info = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-chart');
            if (el === null || el.shadowRoot === null) { return null; }
            const table = el.shadowRoot.querySelector('table');
            if (table === null) { return null; }
            const thead = table.querySelector('thead');
            const tbody = table.querySelector('tbody');
            return {
                hasTable: true,
                headRows: thead !== null ? thead.querySelectorAll('tr').length : 0,
                bodyRows: tbody !== null ? tbody.querySelectorAll('tr').length : 0
            };
        }"""
    )
    assert table_info is not None
    assert table_info["hasTable"] is True
    assert table_info["headRows"] >= 1
    assert table_info["bodyRows"] >= 1

    return


def _mount_chart_markup(frame, markup: str, ready: str = "mj-chart"):
    """
        Replace the preview body with chart markup and wait until every
        <mj-chart> in it has settled (rendered, empty or errored).

        :param frame: The preview Frame (the chart library is loaded).
        :param markup: The HTML to place in the body.
        :param ready: Selector of the charts that must settle.

        :returns: None
    """

    frame.evaluate("markup => { document.body.innerHTML = markup; }", markup)
    frame.wait_for_function(
        """selector => {
            const charts = Array.from(document.querySelectorAll(selector));
            return charts.length > 0 && charts.every((chart) => {
                const state = chart.chartState;
                return state === 'ready' || state === 'empty' || state === 'error';
            });
        }""",
        arg=ready,
        timeout=10000,
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_category_indices_get_distinct_colours(page, base_url):
    """
        A pie chart colours its slices through colorFor(sliceIndex); every
        slice gets its own palette colour instead of the first one.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")
    _mount_chart_markup(frame, (
        '<mj-chart type="pie" style="height:240px">'
        '<script type="application/json">'
        '{"categories":["A","B","C","D","E"],'
        '"series":[{"name":"Share","values":[30,25,20,15,10]}]}'
        '</script></mj-chart>'
    ))

    fills = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            const paths = chart.shadowRoot.querySelectorAll('svg path');
            const colours = new Set();
            paths.forEach((path) => {
                const fill = path.getAttribute('fill');
                if (fill !== null && fill.indexOf('--mj-chart-series') >= 0) {
                    colours.add(window.getComputedStyle(path).fill);
                }
            });
            return Array.from(colours);
        }"""
    )
    assert len(fills) == 5, f"expected 5 distinct slice colours, got {fills}"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_figure_is_named_and_marks_are_one_tab_stop(page, base_url):
    """
        The chart is a labelled figure, its drawing is not aria-hidden, the
        focusable marks form a single tab stop, and arrow keys move focus
        from mark to mark. The fallback table is not a live region.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")
    _mount_chart_markup(frame, (
        '<mj-chart type="bar" label="Quarterly revenue" style="height:240px">'
        '<script type="application/json">'
        '{"categories":["Q1","Q2","Q3"],'
        '"series":[{"name":"2025","values":[10,20,15]}]}'
        '</script></mj-chart>'
    ))

    info = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            const root = chart.shadowRoot;
            const svg = root.querySelector('svg');
            const marks = Array.from(svg.querySelectorAll('[tabindex]'));
            marks[0].focus();
            marks[0].dispatchEvent(new KeyboardEvent('keydown', {
                key: 'ArrowRight', bubbles: true, composed: true, cancelable: true
            }));
            return {
                role: chart.getAttribute('role'),
                label: chart.getAttribute('aria-label'),
                svgHidden: svg.getAttribute('aria-hidden'),
                marks: marks.length,
                tabStops: marks.filter((mark) => mark.getAttribute('tabindex') === '0').length,
                focusedIndex: marks.indexOf(root.activeElement),
                live: root.querySelector('[data-chart-table]').getAttribute('aria-live'),
                caption: root.querySelector('[data-chart-table] caption').textContent
            };
        }"""
    )
    assert info["role"] == "figure"
    assert info["label"] == "Quarterly revenue"
    assert info["svgHidden"] is None
    assert info["marks"] == 3
    assert info["tabStops"] == 1
    assert info["focusedIndex"] == 1
    assert info["live"] is None
    assert info["caption"] == "Quarterly revenue"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_legend_toggle_hides_the_series(page, base_url):
    """
        Pressing a legend entry hides that series in the chart (its bars
        disappear), reports the state through aria-pressed (true = shown)
        and emits mj-chart-series-toggle; pressing again shows it.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")
    _mount_chart_markup(frame, (
        '<mj-chart id="toggled" type="bar" style="height:240px">'
        '<script type="application/json">'
        '{"categories":["Q1","Q2"],'
        '"series":[{"name":"North","values":[1,2]},{"name":"South","values":[3,4]}]}'
        '</script></mj-chart>'
        '<mj-chart-legend chart="toggled"></mj-chart-legend>'
    ))

    result = frame.evaluate(
        """() => {
            const chart = document.getElementById('toggled');
            const legend = document.querySelector('mj-chart-legend');
            const events = [];
            chart.addEventListener('mj-chart-series-toggle', (event) => {
                events.push(event.detail);
            });
            const bars = () => Array.from(chart.shadowRoot.querySelectorAll('svg rect[part="bar"]'))
                .map((bar) => bar.getAttribute('aria-label'));
            const button = legend.shadowRoot.querySelector('button');
            const before = bars();
            button.click();
            const hidden = { bars: bars(), pressed: button.getAttribute('aria-pressed') };
            button.click();
            return {
                before: before.length,
                hidden: hidden,
                after: bars().length,
                pressedAfter: button.getAttribute('aria-pressed'),
                events: events
            };
        }"""
    )
    assert result["before"] == 4
    assert len(result["hidden"]["bars"]) == 2
    assert all(label.startswith("South") for label in result["hidden"]["bars"])
    assert result["hidden"]["pressed"] == "false"
    assert result["after"] == 4
    assert result["pressedAfter"] == "true"
    assert result["events"][0]["series"] == "North"
    assert result["events"][0]["seriesIndex"] == 0
    assert result["events"][0]["visible"] is False
    assert result["events"][1]["visible"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_src_is_fetched_once_and_stale_responses_are_dropped(page, base_url):
    """
        A `src` payload is fetched once and reused when the chart resizes or
        an option changes, and a slow response for a previous `src` never
        replaces the data of the current one.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const bodies = {
                '/chart-src/slow.json': { delay: 400, name: 'SLOW' },
                '/chart-src/fast.json': { delay: 20, name: 'FAST' }
            };
            const requested = [];
            const realFetch = window.fetch.bind(window);
            window.fetch = (url, init) => {
                const entry = bodies[String(url)];
                if (entry === undefined) { return realFetch(url, init); }
                requested.push(String(url));
                const body = JSON.stringify({ categories: ['a'], series: [{ name: entry.name, values: [1] }] });
                return new Promise((resolve) => {
                    setTimeout(() => {
                        resolve(new Response(body, { headers: { 'Content-Type': 'application/json' } }));
                    }, entry.delay);
                });
            };

            document.body.innerHTML =
                '<div id="box" style="inline-size:600px"><mj-chart type="bar" src="/chart-src/slow.json" style="height:200px"></mj-chart></div>';
            const chart = document.querySelector('mj-chart');
            await wait(80);
            chart.setAttribute('src', '/chart-src/fast.json');
            await wait(700);
            const shown = chart.chartModel.series.map((entry) => entry.name);

            const before = requested.length;
            const box = document.getElementById('box');
            for (const width of [520, 440, 360]) {
                box.style.inlineSize = width + 'px';
                await wait(80);
            }
            chart.setAttribute('orientation', 'horizontal');
            await wait(80);
            return {
                shown: shown,
                extraRequests: requested.length - before,
                viewBox: chart.shadowRoot.querySelector('svg').getAttribute('viewBox')
            };
        }"""
    )
    assert result["shown"] == ["FAST"]
    assert result["extraRequests"] == 0
    assert result["viewBox"].startswith("0 0 360 ")

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_labels_are_plain_text_and_not_injectable(page, base_url):
    """
        Labels are shown exactly as written ("FP&A", not "FP&amp;A"), and a
        markup payload in the data or the label attribute stays text.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")
    payload = "x'\"><img src=\"data:,x\" onerror=\"top.__hits=(top.__hits||0)+1\">"
    frame.evaluate(
        """payload => {
            document.body.innerHTML = '';
            const chart = document.createElement('mj-chart');
            chart.setAttribute('type', 'bar');
            chart.setAttribute('label', payload);
            chart.style.height = '220px';
            chart.data = {
                meta: { title: payload, description: payload },
                categories: ['FP&A', payload],
                series: [{ name: payload, values: [3, 4] }]
            };
            document.body.appendChild(chart);
        }""",
        payload,
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-chart').chartState === 'ready'",
        timeout=10000,
    )
    page.wait_for_timeout(300)

    result = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            const texts = Array.from(root.querySelectorAll('svg text')).map((node) => node.textContent);
            return {
                texts: texts,
                images: root.querySelectorAll('img').length,
                hits: top.__hits === undefined ? null : top.__hits
            };
        }"""
    )
    assert "FP&A" in result["texts"]
    assert all("&amp;" not in text for text in result["texts"])
    assert result["images"] == 0
    assert result["hits"] is None

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_tree_render_completes_and_tables_the_nodes(page, base_url):
    """
        A tree chart finishes its render (mj-chart-render fires) and its
        fallback table lists one row per node, although the tree renderer
        links nodes to their parents.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")

    result = frame.evaluate(
        """async () => {
            document.body.innerHTML = '';
            const chart = document.createElement('mj-chart');
            chart.setAttribute('type', 'tree');
            chart.style.height = '260px';
            const rendered = new Promise((resolve) => {
                chart.addEventListener('mj-chart-render', (event) => { resolve(event.detail.type); });
                setTimeout(() => { resolve(null); }, 4000);
            });
            const errors = [];
            chart.addEventListener('mj-chart-error', (event) => { errors.push(event.detail.message); });
            chart.data = { root: { name: 'CEO', children: [
                { name: 'CTO', children: [{ name: 'Dev' }, { name: 'Ops' }] },
                { name: 'CFO' }
            ] } };
            document.body.appendChild(chart);
            const type = await rendered;
            const rows = chart.shadowRoot.querySelectorAll('[data-chart-table] tbody tr').length;
            return { type: type, rows: rows, errors: errors, state: chart.chartState };
        }"""
    )
    assert result["type"] == "tree", f"mj-chart-render did not fire: {result}"
    assert result["errors"] == []
    assert result["state"] == "ready"
    assert result["rows"] == 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chart_empty_payloads_and_explicit_height(page, base_url):
    """
        Empty collections show the empty state (mj-chart-empty), raw-data
        payloads such as a gauge value do not, nulls stay null in the model,
        and an explicit host height smaller than the default is honoured.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-chart")
    _mount_chart_markup(frame, (
        '<mj-chart id="empty" type="sankey" style="height:200px">'
        '<script type="application/json">{"nodes":[],"links":[]}</script></mj-chart>'
        '<mj-chart id="gauge" type="gauge" style="height:200px">'
        '<script type="application/json">{"value":72,"min":0,"max":100}</script></mj-chart>'
        '<mj-chart id="small" type="sparkline" style="height:60px;width:200px">'
        '<script type="application/json">'
        '{"series":[{"name":"Trend","values":[3,null,5,4]}]}</script></mj-chart>'
    ))

    result = frame.evaluate(
        """() => {
            const empty = document.getElementById('empty');
            const gauge = document.getElementById('gauge');
            const small = document.getElementById('small');
            return {
                emptyState: empty.chartState,
                emptyText: empty.shadowRoot.querySelector('.message').textContent,
                gaugeState: gauge.chartState,
                nullValue: small.chartModel.series[0].values[1],
                smallHeight: Math.round(small.getBoundingClientRect().height)
            };
        }"""
    )
    assert result["emptyState"] == "empty"
    assert result["emptyText"] == "No chart data supplied."
    assert result["gaugeState"] == "ready"
    assert result["nullValue"] is None
    assert result["smallHeight"] == 60

    return


# ---------------------------------------------------------------------------
# mj-map
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_renders_accessible_marker_list(page, base_url):
    """
        After setting .markers the accessible list is populated with <li>
        elements for each marker.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")
    el = frame.locator("mj-map").first
    expect(el).to_be_attached(timeout=10000)

    # The inline example script may have set markers as a plain own property before
    # the custom element upgraded. Delete it first so the prototype setter runs.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null) { return; }
            delete el.markers;
            el.markers = [
                { id: 'm1', label: 'Marker One', lat: 51.5014, lng: -0.1419,
                  description: 'First test marker' },
                { id: 'm2', label: 'Marker Two', lat: 51.5081, lng: -0.0759,
                  description: 'Second test marker' }
            ];
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null || el.shadowRoot === null) { return false; }
            const ul = el.shadowRoot.querySelector('.marker-list');
            return ul !== null && ul.querySelectorAll('li').length >= 2;
        }""",
        timeout=10000,
    )

    list_item_count = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null || el.shadowRoot === null) { return 0; }
            const ul = el.shadowRoot.querySelector('.marker-list');
            return ul !== null ? ul.querySelectorAll('li').length : 0;
        }"""
    )
    assert list_item_count >= 2

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_show_list_makes_list_visible(page, base_url):
    """
        When show-list is present the .marker-list element has the 'visible'
        CSS class.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")
    el = frame.locator("mj-map").first
    expect(el).to_be_attached(timeout=10000)

    # The example in catalog/media.py includes show-list.
    list_visible = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null || el.shadowRoot === null) { return false; }
            const ul = el.shadowRoot.querySelector('.marker-list');
            return ul !== null && ul.classList.contains('visible');
        }"""
    )
    assert list_visible is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_has_zoom_controls(page, base_url):
    """
        The map renders zoom-in and zoom-out control buttons in its shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")
    el = frame.locator("mj-map").first
    expect(el).to_be_attached(timeout=10000)

    has_zoom_controls = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null || el.shadowRoot === null) { return false; }
            const sr = el.shadowRoot;
            const zoomIn = sr.querySelector('[part="zoom-in"]');
            const zoomOut = sr.querySelector('[part="zoom-out"]');
            return zoomIn !== null && zoomOut !== null;
        }"""
    )
    assert has_zoom_controls is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_region_label_from_attribute(page, base_url):
    """
        The section element carries an aria-label derived from the label
        attribute.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")
    el = frame.locator("mj-map").first
    expect(el).to_be_attached(timeout=10000)

    section_label = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null || el.shadowRoot === null) { return null; }
            const section = el.shadowRoot.querySelector('section');
            return section !== null ? section.getAttribute('aria-label') : null;
        }"""
    )
    assert section_label is not None
    assert len(section_label) > 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_marker_click_opens_popup(page, base_url):
    """
        Clicking a marker link in the accessible list opens the popup panel
        and shows the marker label as the popup title.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")
    el = frame.locator("mj-map").first
    expect(el).to_be_attached(timeout=10000)

    # Delete own property first so the prototype setter runs and the marker list
    # is rebuilt with new items that have click handlers.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null) { return; }
            delete el.markers;
            el.markers = [
                { id: 'bk', label: 'Buckingham Palace', lat: 51.5014, lng: -0.1419,
                  description: 'Official London residence' }
            ];
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('.marker-list a') !== null;
        }""",
        timeout=10000,
    )

    popup_title = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-map');
            if (el === null || el.shadowRoot === null) { return null; }
            const sr = el.shadowRoot;
            const firstLink = sr.querySelector('.marker-list a');
            if (firstLink === null) { return null; }
            firstLink.click();
            const popup = sr.querySelector('.popup');
            if (popup === null) { return null; }
            const title = popup.querySelector('.popup-title');
            return title !== null ? title.textContent : null;
        }"""
    )
    assert popup_title is not None
    assert popup_title == "Buckingham Palace"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_markers_set_before_connection(page, base_url):
    """
        Assigning markers (and a selection) to an mj-map that is not yet in
        the document does not throw; the list, the built-in markers and the
        popup appear once it is connected.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")

    state = frame.evaluate(
        """async () => {
            const map = document.createElement('mj-map');
            map.setAttribute('label', 'Detached map');
            map.style.height = '240px';
            let error = null;
            try {
                map.markers = [
                    { id: 'a', label: 'Alpha', lat: 51.50, lng: -0.10 },
                    { id: 'b', label: 'Beta', lat: 51.60, lng: -0.20 }
                ];
                map.selectedMarkerId = 'b';
            } catch (caught) {
                error = String(caught);
            }
            document.body.appendChild(map);
            await new Promise((resolve) => setTimeout(resolve, 200));
            const root = map.shadowRoot;
            return {
                error: error,
                listItems: root.querySelectorAll('.marker-list li').length,
                svgMarkers: root.querySelectorAll('.svg-map-marker').length,
                popupOpen: root.querySelector('.popup').classList.contains('open'),
                popupTitle: root.querySelector('.popup-title').textContent
            };
        }"""
    )
    assert state["error"] is None
    assert state["listItems"] == 2
    assert state["svgMarkers"] == 2
    assert state["popupOpen"] is True
    assert state["popupTitle"] == "Beta"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_builtin_plot_spreads_city_markers(page, base_url):
    """
        Markers within one city spread over the built-in plot (the minimum
        extent used to be half a degree, which piled city-scale markers up in
        the middle of the drawing with overlapping labels), and a single
        marker is still drawn in the middle.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")

    state = frame.evaluate(
        """async () => {
            document.body.innerHTML =
                '<mj-map id="city" label="City" style="height:300px;width:600px;display:block"></mj-map>' +
                '<mj-map id="single" label="Single" style="height:300px;width:600px;display:block"></mj-map>';
            await customElements.whenDefined('mj-map');
            const city = document.getElementById('city');
            city.markers = [
                { id: 'a', label: 'Buckingham Palace', lat: 51.5014, lng: -0.1419 },
                { id: 'b', label: 'Tower of London', lat: 51.5081, lng: -0.0759 },
                { id: 'c', label: 'British Museum', lat: 51.5194, lng: -0.127 }
            ];
            const single = document.getElementById('single');
            single.markers = [{ id: 'x', label: 'Only', lat: 48.85, lng: 2.35 }];
            await new Promise((resolve) => setTimeout(resolve, 300));
            const centres = (map) => Array.from(map.shadowRoot.querySelectorAll('.svg-map-marker circle'))
                .map((circle) => { const box = circle.getBoundingClientRect(); return [box.x + box.width / 2, box.y + box.height / 2]; });
            const area = (map) => map.shadowRoot.querySelector('[part=map-target]').getBoundingClientRect();
            const cityPoints = centres(city);
            const xs = cityPoints.map((point) => point[0]);
            const ys = cityPoints.map((point) => point[1]);
            const singlePoint = centres(single)[0];
            const singleArea = area(single);
            return {
                widthShare: (Math.max(...xs) - Math.min(...xs)) / area(city).width,
                heightShare: (Math.max(...ys) - Math.min(...ys)) / area(city).height,
                singleOffsetX: Math.abs(singlePoint[0] - (singleArea.x + singleArea.width / 2)),
                singleOffsetY: Math.abs(singlePoint[1] - (singleArea.y + singleArea.height / 2))
            };
        }"""
    )
    # The markers' own extent fills half of each dimension (margin and padding take the rest).
    assert state["widthShare"] > 0.4, state
    assert state["heightShare"] > 0.4, state
    assert state["singleOffsetX"] < 2, state
    assert state["singleOffsetY"] < 2, state

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_visible_list_fits_inside_host_height(page, base_url):
    """
        The host is the sizing box: with show-list the map area and the
        visible marker list share the host height and the list is not clipped.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-map")

    geometry = frame.evaluate(
        """async () => {
            const map = document.querySelector('mj-map');
            delete map.markers;
            map.markers = [
                { id: 'a', label: 'Alpha', lat: 51.50, lng: -0.10 },
                { id: 'b', label: 'Beta', lat: 51.60, lng: -0.20 }
            ];
            await new Promise((resolve) => setTimeout(resolve, 200));
            const root = map.shadowRoot;
            const host = map.getBoundingClientRect();
            const container = root.querySelector('.container').getBoundingClientRect();
            const area = root.querySelector('.map-area').getBoundingClientRect();
            const list = root.querySelector('.marker-list').getBoundingClientRect();
            return {
                hostHeight: host.height,
                containerHeight: container.height,
                listBelowArea: list.top >= area.bottom - 0.5,
                listInsideHost: list.bottom <= host.bottom + 0.5,
                listHeight: list.height
            };
        }"""
    )
    # The catalog example sets style="height:360px".
    assert abs(geometry["hostHeight"] - 360) < 0.5
    assert abs(geometry["containerHeight"] - 360) < 0.5
    assert geometry["listBelowArea"] is True
    assert geometry["listInsideHost"] is True
    assert geometry["listHeight"] > 20

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_escape_in_popup_closes_and_returns_focus(page, base_url):
    """
        Escape pressed on the popup's close button closes the popup and puts
        focus back on the marker that opened it; the built-in SVG is exposed
        to assistive technology while its markers are buttons.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-map")

    html = '<mj-map id="esc-map" label="Escape test" style="height:300px"></mj-map>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-map")

    state = frame.evaluate(
        """async () => {
            const map = document.querySelector('mj-map');
            map.markers = [
                { id: 'a', label: 'Alpha', lat: 51.50, lng: -0.10 },
                { id: 'b', label: 'Beta', lat: 51.60, lng: -0.20 }
            ];
            await new Promise((resolve) => setTimeout(resolve, 100));
            const root = map.shadowRoot;
            const marker = root.querySelectorAll('.svg-map-marker')[1];
            marker.focus();
            marker.dispatchEvent(new KeyboardEvent('keydown',
                { key: 'Enter', bubbles: true, composed: true, cancelable: true }));
            const close = root.querySelector('.popup-close');
            const openState = {
                open: root.querySelector('.popup').classList.contains('open'),
                focusOnClose: root.activeElement === close
            };
            close.dispatchEvent(new KeyboardEvent('keydown',
                { key: 'Escape', bubbles: true, composed: true, cancelable: true }));
            return {
                opened: openState,
                openAfterEscape: root.querySelector('.popup').classList.contains('open'),
                focusBackOnMarker: root.activeElement === root.querySelectorAll('.svg-map-marker')[1],
                svgAriaHidden: root.querySelector('svg.svg-map').getAttribute('aria-hidden'),
                hiddenListLinkTabindex: root.querySelector('.marker-list a').getAttribute('tabindex')
            };
        }"""
    )
    assert state["opened"] == {"open": True, "focusOnClose": True}
    assert state["openAfterEscape"] is False
    assert state["focusBackOnMarker"] is True
    assert state["svgAriaHidden"] is None
    assert state["hiddenListLinkTabindex"] == "-1"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_map_adapter_receives_markers_and_attribute_changes(page, base_url):
    """
        Markers set before the adapter are handed to it on init, lat/lng
        changes are forwarded, and the adapter's reported position is what
        mj-map-move carries.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-map")

    html = '<mj-map label="Adapter test" lat="10" lng="20" zoom="5" style="height:200px"></mj-map>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-map")

    state = frame.evaluate(
        """async () => {
            const map = document.querySelector('mj-map');
            const calls = [];
            const handlers = {};
            map.markers = [{ id: 'a', label: 'Alpha', lat: 1, lng: 2 }];
            map.adapter = {
                init(target, options) { calls.push(`init:${options.lat},${options.lng},${options.zoom}`); },
                destroy() { calls.push('destroy'); },
                panTo(lat, lng) { calls.push(`panTo:${lat},${lng}`); },
                setZoom(zoom) { calls.push(`setZoom:${zoom}`); },
                addMarker(marker) { calls.push(`add:${marker.id}`); return marker.id; },
                removeMarker(handle) { calls.push(`remove:${handle}`); },
                on(name, handler) { handlers[name] = handler; }
            };
            map.setAttribute('lat', '11');
            const moves = [];
            map.addEventListener('mj-map-move', (event) => { moves.push(event.detail); });
            handlers.move({ lat: 33, lng: 44, zoom: 6 });
            await new Promise((resolve) => setTimeout(resolve, 350));
            return { calls: calls, moves: moves, center: map.center, zoom: map.currentZoom };
        }"""
    )
    assert state["calls"] == ["init:10,20,5", "add:a", "panTo:11,20"]
    assert state["moves"] == [{"lat": 33, "lng": 44, "zoom": 6}]
    assert state["center"] == {"lat": 33, "lng": 44}
    assert state["zoom"] == 6

    return


# ---------------------------------------------------------------------------
# mj-gauge
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_arc_renders_svg(page, base_url):
    """
        The default arc gauge renders an SVG element in its shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-gauge")
    el = frame.locator("mj-gauge").first
    expect(el).to_be_attached(timeout=10000)

    has_svg = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('svg.gauge-svg') !== null;
        }"""
    )
    assert has_svg is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_value_label_reflects_value(page, base_url):
    """
        The .value-label element displays the formatted numeric value.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = (
        '<mj-gauge id="g1" value="72" min="0" max="100" '
        'title="CPU Usage" unit="%"></mj-gauge>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    value_text = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            if (el === null || el.shadowRoot === null) { return null; }
            const label = el.shadowRoot.querySelector('.value-label');
            return label !== null ? label.textContent : null;
        }"""
    )
    assert value_text is not None
    assert "72" in value_text

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_linear_shape_renders_fill_bar(page, base_url):
    """
        When shape='linear' the component renders a .linear-fill bar instead
        of an SVG arc.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = (
        '<mj-gauge value="45" min="0" max="100" '
        'title="Memory" unit="%" shape="linear" show-min-max></mj-gauge>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    fill_width = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            if (el === null || el.shadowRoot === null) { return null; }
            const fill = el.shadowRoot.querySelector('.linear-fill');
            return fill !== null ? fill.style.width : null;
        }"""
    )
    assert fill_width is not None
    assert "45" in fill_width

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_native_meter_provides_semantics(page, base_url):
    """
        The shadow DOM contains a native <meter> element that holds the
        accessible value, min, and max.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = (
        '<mj-gauge value="60" min="0" max="100" title="Test Gauge"></mj-gauge>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    meter_attrs = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            if (el === null || el.shadowRoot === null) { return null; }
            const meter = el.shadowRoot.querySelector('meter.sr-meter');
            if (meter === null) { return null; }
            return {
                value: meter.getAttribute('value'),
                min: meter.getAttribute('min'),
                max: meter.getAttribute('max')
            };
        }"""
    )
    assert meter_attrs is not None
    assert meter_attrs["value"] == "60"
    assert meter_attrs["min"] == "0"
    assert meter_attrs["max"] == "100"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_title_attribute_renders_label(page, base_url):
    """
        The title attribute text is rendered in the .title div.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = '<mj-gauge value="50" title="My Gauge Label"></mj-gauge>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    title_text = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            if (el === null || el.shadowRoot === null) { return null; }
            const title = el.shadowRoot.querySelector('.title');
            return title !== null ? title.textContent : null;
        }"""
    )
    assert title_text == "My Gauge Label"

    return


_INJECTION_PAYLOAD = """x'"><img src="data:,x" onerror="top.__hits=(top.__hits||0)+1">"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_unit_and_threshold_colors_are_not_markup(page, base_url):
    """
        A unit and threshold colours / labels carrying markup are rendered as
        text or rejected as colours; no element is created from them.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = (
        '<mj-gauge id="g-linear" value="40" shape="linear" title="Linear"></mj-gauge>'
        '<mj-gauge id="g-arc" value="40" title="Arc"></mj-gauge>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    state = frame.evaluate(
        """async (payload) => {
            const gauges = [document.getElementById('g-linear'), document.getElementById('g-arc')];
            for (const gauge of gauges) {
                gauge.setAttribute('unit', payload);
                gauge.setAttribute('title', payload);
                gauge.thresholds = [
                    { value: 0, color: 'red"><img src="data:,x" onerror="top.__hits=1">', label: payload },
                    { value: 30, color: 'blue', label: 'Blue' }
                ];
            }
            await new Promise((resolve) => setTimeout(resolve, 300));
            return {
                hits: top.__hits === undefined ? null : top.__hits,
                images: gauges.map((gauge) => gauge.shadowRoot.querySelectorAll('img').length),
                minLabel: gauges[0].shadowRoot.querySelector('[part="min-label"]').textContent,
                valueLabel: gauges[1].shadowRoot.querySelector('.value-label').textContent
            };
        }""",
        _INJECTION_PAYLOAD,
    )
    assert state["hits"] is None
    assert state["images"] == [0, 0]
    assert state["minLabel"] == "0" + _INJECTION_PAYLOAD
    assert state["valueLabel"] == "40" + _INJECTION_PAYLOAD

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_arc_opening_faces_down(page, base_url):
    """
        The default 240 degree arc starts lower-left and ends lower-right
        (opening at the bottom), 180 degrees draws a dome, and 360 degrees
        draws a full ring.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = (
        '<mj-gauge id="g240" value="50"></mj-gauge>'
        '<mj-gauge id="g180" value="50" arc-degrees="180"></mj-gauge>'
        '<mj-gauge id="g360" value="50" arc-degrees="360"></mj-gauge>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    tracks = frame.evaluate(
        """() => {
            const bounds = (id) => {
                const path = document.getElementById(id).shadowRoot.querySelector('.arc-track');
                const box = path.getBBox();
                const start = path.getPointAtLength(0);
                const end = path.getPointAtLength(path.getTotalLength());
                return {
                    start: [start.x, start.y], end: [end.x, end.y],
                    box: [box.x, box.y, box.width, box.height]
                };
            };
            return { g240: bounds('g240'), g180: bounds('g180'), g360: bounds('g360') };
        }"""
    )
    centre = 60
    # 240: both ends below the centre, symmetric left/right.
    assert tracks["g240"]["start"][0] < centre and tracks["g240"]["start"][1] > centre
    assert tracks["g240"]["end"][0] > centre and tracks["g240"]["end"][1] > centre
    assert abs(tracks["g240"]["start"][1] - tracks["g240"]["end"][1]) < 0.1
    # 180: a dome over the centre line, as wide as the circle.
    assert abs(tracks["g180"]["start"][1] - centre) < 0.1
    assert tracks["g180"]["start"][0] < tracks["g180"]["end"][0]
    assert tracks["g180"]["box"][1] < centre - 40
    assert tracks["g180"]["box"][1] + tracks["g180"]["box"][3] <= centre + 0.5
    # 360: a full ring has the full diameter in both directions.
    assert abs(tracks["g360"]["box"][2] - 96) < 1
    assert abs(tracks["g360"]["box"][3] - 96) < 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_value_change_reports_previous_value_and_keeps_fill(page, base_url):
    """
        mj-gauge-value-change carries the value that was shown before the
        change, and the fill element is updated in place (so it can animate).

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = '<mj-gauge value="20" title="Previous value"></mj-gauge>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    state = frame.evaluate(
        """() => {
            const gauge = document.querySelector('mj-gauge');
            const events = [];
            gauge.addEventListener('mj-gauge-value-change', (event) => { events.push(event.detail); });
            const fillBefore = gauge.shadowRoot.querySelector('.arc-fill');
            gauge.setAttribute('value', '65');
            gauge.setAttribute('value', '65');
            return {
                events: events,
                sameFill: fillBefore === gauge.shadowRoot.querySelector('.arc-fill')
            };
        }"""
    )
    assert state["events"] == [{"value": 65, "previousValue": 20, "threshold": None}]
    assert state["sameFill"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_min_max_labels_locale_and_bands(page, base_url):
    """
        Min/max labels show by default and hide with show-min-max="false",
        `locale` formats the value, and thresholds draw patterned bands.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-gauge")

    html = (
        '<mj-gauge id="g-default" value="10" shape="linear"></mj-gauge>'
        '<mj-gauge id="g-off" value="10" shape="linear" show-min-max="false"></mj-gauge>'
        '<mj-gauge id="g-locale" value="1234.5" max="2000" precision="1" locale="de-DE"></mj-gauge>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-gauge")

    state = frame.evaluate(
        """() => {
            const root = (id) => document.getElementById(id).shadowRoot;
            const arc = document.getElementById('g-locale');
            arc.thresholds = [
                { value: 0, color: '#047857', label: 'Normal' },
                { value: 1500, color: '#b91c1c', label: 'High' }
            ];
            const linear = document.getElementById('g-default');
            linear.thresholds = [
                { value: 0, color: '#047857', label: 'Normal' },
                { value: 60, color: '#b91c1c', label: 'High' }
            ];
            return {
                defaultMinMax: root('g-default').querySelector('.minmax') !== null,
                offMinMax: root('g-off').querySelector('.minmax') !== null,
                arcMinMax: root('g-locale').querySelector('[part="min-label"]') !== null,
                localeLabel: root('g-locale').querySelector('.value-label').textContent,
                arcBandPatterns: root('g-locale').querySelectorAll('pattern').length,
                linearBands: Array.from(root('g-default').querySelectorAll('.linear-band'))
                    .map((band) => band.getAttribute('data-pattern'))
            };
        }"""
    )
    assert state["defaultMinMax"] is True
    assert state["offMinMax"] is False
    assert state["arcMinMax"] is True
    assert state["localeLabel"] == "1.234,5"
    assert state["arcBandPatterns"] >= 2
    assert state["linearBands"] == ["stripes", "dots"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_gauge_thresholds_set_before_connection(page, base_url):
    """
        Assigning thresholds to an mj-gauge that is not yet connected does
        not throw, and the bands are drawn once it connects.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-gauge")

    state = frame.evaluate(
        """() => {
            const gauge = document.createElement('mj-gauge');
            gauge.setAttribute('value', '50');
            let error = null;
            try {
                gauge.thresholds = [{ value: 0, color: '#047857', label: 'Normal' }];
            } catch (caught) {
                error = String(caught);
            }
            document.body.appendChild(gauge);
            return {
                error: error,
                bands: gauge.shadowRoot.querySelectorAll('.arc-band').length
            };
        }"""
    )
    assert state["error"] is None
    assert state["bands"] > 0

    return


# ---------------------------------------------------------------------------
# mj-sparkline
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_renders_svg(page, base_url):
    """
        mj-sparkline renders an SVG element inside its shadow DOM.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-sparkline")
    el = frame.locator("mj-sparkline").first
    expect(el).to_be_attached(timeout=10000)

    has_svg = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('svg') !== null;
        }"""
    )
    assert has_svg is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_line_type_draws_path(page, base_url):
    """
        For type='line' the SVG contains a <path> element with class 'line'.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline values="10,20,15,25,18,30" '
        'type="line" width="120" height="32">'
        '</mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    has_path = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            if (el === null || el.shadowRoot === null) { return false; }
            const svg = el.shadowRoot.querySelector('svg');
            return svg !== null && svg.querySelector('path.line') !== null;
        }"""
    )
    assert has_path is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_area_type_draws_area_path(page, base_url):
    """
        For type='area' the SVG contains a <path> element with class 'area'.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline values="12,18,15,22,19,28,25,32" '
        'type="area" width="120" height="32" show-end-dot>'
        '</mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    has_area = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            if (el === null || el.shadowRoot === null) { return false; }
            const svg = el.shadowRoot.querySelector('svg');
            return svg !== null && svg.querySelector('path.area') !== null;
        }"""
    )
    assert has_area is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_bar_type_draws_rect_elements(page, base_url):
    """
        For type='bar' the SVG contains <rect> elements with class 'bar-pos'
        or 'bar-neg'.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline values="5,10,8,12,7,15" '
        'type="bar" width="120" height="32">'
        '</mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    has_bars = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            if (el === null || el.shadowRoot === null) { return false; }
            const svg = el.shadowRoot.querySelector('svg');
            return svg !== null && svg.querySelector('rect.bar-pos') !== null;
        }"""
    )
    assert has_bars is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_label_sets_accessible_role(page, base_url):
    """
        When the label attribute is set the SVG gets role='img' and the
        aria-label matches.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline values="1,-1,1,1,-1,1,-1,1,1,1" '
        'type="win-loss" width="80" height="28" '
        'label="Win/loss record: 7 wins, 3 losses">'
        '</mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    svg_attrs = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            if (el === null || el.shadowRoot === null) { return null; }
            const svg = el.shadowRoot.querySelector('svg');
            if (svg === null) { return null; }
            return {
                role: svg.getAttribute('role'),
                ariaLabel: svg.getAttribute('aria-label')
            };
        }"""
    )
    assert svg_attrs is not None
    assert svg_attrs["role"] == "img"
    assert svg_attrs["ariaLabel"] == "Win/loss record: 7 wins, 3 losses"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_svg_dimensions_match_attributes(page, base_url):
    """
        The rendered SVG width and height attributes match the component's
        width and height attributes.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline values="10,20,30" '
        'type="line" width="150" height="40">'
        '</mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    svg_size = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            if (el === null || el.shadowRoot === null) { return null; }
            const svg = el.shadowRoot.querySelector('svg');
            if (svg === null) { return null; }
            return {
                width: svg.getAttribute('width'),
                height: svg.getAttribute('height')
            };
        }"""
    )
    assert svg_size is not None
    assert svg_size["width"] == "150"
    assert svg_size["height"] == "40"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_bars_and_area_stay_inside_the_box(page, base_url):
    """
        Without reference-value, bars grow up from the bottom (zero) baseline
        and the area closes to the bottom; every bar sits inside the SVG box.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline id="bars" type="bar" values="3,5,4,8" width="80" height="24"></mj-sparkline>'
        '<mj-sparkline id="area" type="area" values="3,5,4,8" width="80" height="24"></mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    state = frame.evaluate(
        """() => {
            const bars = Array.from(document.getElementById('bars').shadowRoot.querySelectorAll('rect[part=bar]'))
                .map((rect) => ({
                    x: parseFloat(rect.getAttribute('x')),
                    y: parseFloat(rect.getAttribute('y')),
                    width: parseFloat(rect.getAttribute('width')),
                    height: parseFloat(rect.getAttribute('height'))
                }));
            const area = document.getElementById('area').shadowRoot.querySelector('path.area');
            const box = area.getBBox();
            return { bars: bars, areaBottom: box.y + box.height };
        }"""
    )
    bottoms = [round(bar["y"] + bar["height"], 1) for bar in state["bars"]]
    assert len(set(bottoms)) == 1
    assert bottoms[0] == 22.0
    for bar in state["bars"]:
        assert bar["x"] >= 0
        assert bar["x"] + bar["width"] <= 80
        assert bar["y"] >= 0
    heights = [bar["height"] for bar in state["bars"]]
    assert heights[3] > heights[1] > heights[2] > heights[0]
    assert abs(state["areaBottom"] - 22.0) < 0.2

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_reference_value_and_gaps(page, base_url):
    """
        A reference value outside the data is pulled into the Y domain, a gap
        closes each area segment on its own, a single value draws a dot and
        zero is neutral in win-loss mode.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline id="ref" values="3,9,5,6" reference-value="0" width="80" height="24"></mj-sparkline>'
        '<mj-sparkline id="gap" type="area" values="3,5,x,4,8,6" width="100" height="24"></mj-sparkline>'
        '<mj-sparkline id="one" values="5"></mj-sparkline>'
        '<mj-sparkline id="wl" type="win-loss" values="1,0,-1"></mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    state = frame.evaluate(
        """() => {
            const root = (id) => document.getElementById(id).shadowRoot;
            const reference = root('ref').querySelector('.reference-line');
            const area = root('gap').querySelector('path.area').getAttribute('d');
            return {
                referenceY: parseFloat(reference.getAttribute('y1')),
                areaSubpaths: area.split('M').length - 1,
                areaClosures: area.split('Z').length - 1,
                singleDot: root('one').querySelectorAll('circle.point').length,
                winLoss: Array.from(root('wl').querySelectorAll('rect')).map((rect) => rect.getAttribute('class'))
            };
        }"""
    )
    assert 0 <= state["referenceY"] <= 24
    assert state["areaSubpaths"] == 2
    assert state["areaClosures"] == 2
    assert state["singleDot"] == 1
    assert state["winLoss"] == ["bar-pos mark", "bar-zero mark", "bar-neg mark"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_sparkline_interactive_marks_are_keyboard_buttons(page, base_url):
    """
        With `interactive` the marks are focusable labelled buttons and
        Enter / Space emit mj-sparkline-click; a monotone curve uses cubic
        segments.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-sparkline")

    html = (
        '<mj-sparkline id="click" type="bar" values="3,9,5" interactive label="Sales"></mj-sparkline>'
        '<mj-sparkline id="curve" curve="monotone" values="1,8,3,9" width="100"></mj-sparkline>'
    )
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-sparkline")

    state = frame.evaluate(
        """() => {
            const el = document.getElementById('click');
            const marks = el.shadowRoot.querySelectorAll('rect[part=bar]');
            const clicks = [];
            el.addEventListener('mj-sparkline-click', (event) => { clicks.push(event.detail); });
            marks[1].dispatchEvent(new KeyboardEvent('keydown',
                { key: 'Enter', bubbles: true, composed: true, cancelable: true }));
            return {
                role: marks[0].getAttribute('role'),
                tabindex: marks[0].getAttribute('tabindex'),
                label: marks[1].getAttribute('aria-label'),
                clicks: clicks,
                curve: document.getElementById('curve').shadowRoot.querySelector('path.line').getAttribute('d')
            };
        }"""
    )
    assert state["role"] == "button"
    assert state["tabindex"] == "0"
    assert state["label"] == "2: 9"
    assert state["clicks"] == [{"index": 1, "value": 9}]
    assert "C" in state["curve"]

    return


# ---------------------------------------------------------------------------
# mj-diagram
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_renders_accessible_node_list(page, base_url):
    """
        After .graph is set the node list is populated with <li> elements
        containing buttons for each node.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-diagram")
    el = frame.locator("mj-diagram").first
    expect(el).to_be_attached(timeout=10000)

    # Delete any own graph property set before upgrade so prototype setter runs.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null) { return; }
            delete el.graph;
            el.graph = {
                nodes: [
                    { id: 'ui', label: 'UI Layer', description: 'Browser components' },
                    { id: 'api', label: 'API Gateway', description: 'Auth and routing' }
                ],
                edges: [
                    { id: 'e1', source: 'ui', target: 'api', label: 'HTTP/REST' }
                ]
            };
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            const ul = el.shadowRoot.querySelector('.node-list');
            return ul !== null && ul.querySelectorAll('.node-btn').length >= 2;
        }""",
        timeout=10000,
    )

    node_button_count = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return 0; }
            const ul = el.shadowRoot.querySelector('.node-list');
            return ul !== null ? ul.querySelectorAll('.node-btn').length : 0;
        }"""
    )
    assert node_button_count >= 2

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_show_list_makes_node_list_visible(page, base_url):
    """
        When show-list is present the .node-list element has the 'visible'
        CSS class.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-diagram")
    el = frame.locator("mj-diagram").first
    expect(el).to_be_attached(timeout=10000)

    # The catalog example includes show-list.
    list_visible = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            const ul = el.shadowRoot.querySelector('.node-list');
            return ul !== null && ul.classList.contains('visible');
        }"""
    )
    assert list_visible is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_node_labels_in_list(page, base_url):
    """
        The node list buttons contain the node labels from the graph data.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-diagram")
    el = frame.locator("mj-diagram").first
    expect(el).to_be_attached(timeout=10000)

    # Delete any own graph property set before upgrade so prototype setter runs.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null) { return; }
            delete el.graph;
            el.graph = {
                nodes: [
                    { id: 'n1', label: 'UI Layer' },
                    { id: 'n2', label: 'API Gateway' },
                    { id: 'n3', label: 'Database' }
                ],
                edges: []
            };
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            const btns = el.shadowRoot.querySelectorAll('.node-btn');
            return btns.length >= 3;
        }""",
        timeout=10000,
    )

    node_labels = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return []; }
            const btns = el.shadowRoot.querySelectorAll('.node-btn');
            return Array.from(btns).map(b => b.textContent.trim());
        }"""
    )
    assert len(node_labels) >= 3
    assert "UI Layer" in node_labels
    assert "API Gateway" in node_labels
    assert "Database" in node_labels

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_has_zoom_controls(page, base_url):
    """
        The diagram renders zoom-in, zoom-out, and fit-to-view buttons.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-diagram")
    el = frame.locator("mj-diagram").first
    expect(el).to_be_attached(timeout=10000)

    has_zoom_controls = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            const sr = el.shadowRoot;
            const zoomIn = sr.querySelector('[part="zoom-in"]');
            const zoomOut = sr.querySelector('[part="zoom-out"]');
            const fitBtn = sr.querySelector('[part="fit-btn"]');
            return zoomIn !== null && zoomOut !== null && fitBtn !== null;
        }"""
    )
    assert has_zoom_controls is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_region_label_from_attribute(page, base_url):
    """
        The section element carries an aria-label derived from the label
        attribute.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-diagram")
    el = frame.locator("mj-diagram").first
    expect(el).to_be_attached(timeout=10000)

    section_label = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return null; }
            const section = el.shadowRoot.querySelector('section');
            return section !== null ? section.getAttribute('aria-label') : null;
        }"""
    )
    assert section_label is not None
    assert len(section_label) > 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_node_button_click_emits_select_event(page, base_url):
    """
        Clicking a node button in the list emits the mj-diagram-node-select
        custom event.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-diagram")
    el = frame.locator("mj-diagram").first
    expect(el).to_be_attached(timeout=10000)

    # Delete any own graph property set before upgrade so prototype setter runs.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null) { return; }
            delete el.graph;
            el.graph = {
                nodes: [{ id: 'n1', label: 'Test Node' }],
                edges: []
            };
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelector('.node-btn') !== null;
        }""",
        timeout=10000,
    )

    event_received = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            let received = false;
            el.addEventListener('mj-diagram-node-select', () => { received = true; });
            const btn = el.shadowRoot.querySelector('.node-btn');
            if (btn === null) { return false; }
            btn.click();
            return received;
        }"""
    )
    assert event_received is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_cyclic_graph_lays_out(page, base_url):
    """
        A graph with a cycle (a -> b -> c -> b) and a self-loop lays out in
        finite time: one node per layer along the chain, nothing thrown.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-diagram")

    html = '<mj-diagram label="Cycle test" style="height:260px"></mj-diagram>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-diagram")

    state = frame.evaluate(
        """async () => {
            const diagram = document.querySelector('mj-diagram');
            let error = null;
            try {
                diagram.graph = {
                    nodes: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' },
                        { id: 'c', label: 'C' }, { id: 's', label: 'Self' }],
                    edges: [{ source: 'a', target: 'b' }, { source: 'b', target: 'c' },
                        { source: 'c', target: 'b' }, { source: 's', target: 's' }]
                };
            } catch (caught) {
                error = String(caught);
            }
            await new Promise((resolve) => setTimeout(resolve, 200));
            const root = diagram.shadowRoot;
            const columnOf = (id) => root.querySelector(`.diagram-node[data-node-id="${id}"] rect`).getAttribute('x');
            return {
                error: error,
                nodes: root.querySelectorAll('.diagram-node').length,
                columns: [columnOf('a'), columnOf('b'), columnOf('c'), columnOf('s')]
            };
        }"""
    )
    assert state["error"] is None
    assert state["nodes"] == 4
    assert state["columns"] == ["80", "300", "520", "80"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_graph_set_before_connection(page, base_url):
    """
        Assigning graph and selectedNodeId to an mj-diagram that is not yet in
        the document does not throw; nodes and selection show once connected.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    frame = _open_preview(page, base_url, "media", "mj-diagram")

    state = frame.evaluate(
        """async () => {
            const diagram = document.createElement('mj-diagram');
            diagram.setAttribute('label', 'Detached diagram');
            diagram.style.height = '220px';
            let error = null;
            try {
                diagram.graph = {
                    nodes: [{ id: 'x', label: 'X' }, { id: 'y', label: 'Y' }],
                    edges: [{ source: 'x', target: 'y' }]
                };
                diagram.selectedNodeId = 'y';
            } catch (caught) {
                error = String(caught);
            }
            document.body.appendChild(diagram);
            await new Promise((resolve) => setTimeout(resolve, 200));
            const root = diagram.shadowRoot;
            const selected = root.querySelector('.node-btn.selected');
            return {
                error: error,
                buttons: root.querySelectorAll('.node-btn').length,
                svgNodes: root.querySelectorAll('.diagram-node').length,
                selected: selected !== null ? selected.textContent : null
            };
        }"""
    )
    assert state["error"] is None
    assert state["buttons"] == 2
    assert state["svgNodes"] == 2
    assert state["selected"] == "Y"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_zoom_steps_from_fitted_scale_and_wheel_needs_focus(page, base_url):
    """
        The zoom-in button steps from the scale on screen (after the fit),
        about the viewport centre, and reflects it to `zoom`; repeated graph
        assignments do not stack wheel listeners, and an unfocused diagram
        lets the wheel scroll the page.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-diagram")

    html = '<mj-diagram label="Zoom test" style="height:260px"></mj-diagram>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-diagram")

    state = frame.evaluate(
        """async () => {
            const diagram = document.querySelector('mj-diagram');
            const nodes = [];
            const edges = [];
            for (let i = 0; i < 6; i = i + 1) {
                nodes.push({ id: `n${i}`, label: `Node ${i}` });
                if (i > 0) { edges.push({ source: `n${i - 1}`, target: `n${i}` }); }
            }
            const graph = { nodes: nodes, edges: edges };
            diagram.graph = graph;
            diagram.graph = graph;
            diagram.graph = graph;
            await new Promise((resolve) => setTimeout(resolve, 200));
            const root = diagram.shadowRoot;
            const target = root.querySelector('.render-target');
            const group = () => {
                const match = root.querySelector('svg g.diagram-content').getAttribute('transform')
                    .match(/translate\\(([-\\d.e]+),([-\\d.e]+)\\) scale\\(([-\\d.e]+)\\)/);
                return { tx: parseFloat(match[1]), ty: parseFloat(match[2]), scale: parseFloat(match[3]) };
            };
            const fitted = group();

            const unfocusedWheel = new WheelEvent('wheel', { deltaY: -100, bubbles: true, cancelable: true });
            target.dispatchEvent(unfocusedWheel);
            const afterUnfocusedWheel = group().scale;

            target.focus();
            const focusedWheel = new WheelEvent('wheel', { deltaY: -100, bubbles: true, cancelable: true });
            target.dispatchEvent(focusedWheel);
            const afterOneWheel = group().scale;

            root.querySelector('[part="fit-btn"]').click();
            const refit = group();
            root.querySelector('[part="zoom-in"]').click();
            const zoomed = group();
            const centreX = target.clientWidth / 2;
            return {
                fittedScale: fitted.scale,
                unfocusedPrevented: unfocusedWheel.defaultPrevented,
                unfocusedChanged: afterUnfocusedWheel !== fitted.scale,
                focusedPrevented: focusedWheel.defaultPrevented,
                wheelStep: Math.round((afterOneWheel - fitted.scale) * 1000) / 1000,
                zoomStep: Math.round((zoomed.scale - refit.scale) * 1000) / 1000,
                zoomAttribute: parseFloat(diagram.getAttribute('zoom')),
                zoomedScale: zoomed.scale,
                centreDrift: Math.abs((centreX - zoomed.tx) / zoomed.scale - (centreX - refit.tx) / refit.scale)
            };
        }"""
    )
    assert state["fittedScale"] < 1
    assert state["unfocusedPrevented"] is False
    assert state["unfocusedChanged"] is False
    assert state["focusedPrevented"] is True
    assert state["wheelStep"] == 0.1
    assert state["zoomStep"] == 0.25
    assert abs(state["zoomAttribute"] - state["zoomedScale"]) < 0.001
    assert state["centreDrift"] < 0.01

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_selection_panel_escape_clears_highlight(page, base_url):
    """
        Activating an SVG node with Enter opens a non-modal panel with the
        node's details; Escape inside the panel closes it, clears the
        highlight and returns focus to the node. Nodes are reachable buttons.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-diagram")

    html = '<mj-diagram label="Panel test" show-selection-panel style="height:280px"></mj-diagram>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-diagram")

    state = frame.evaluate(
        """async () => {
            const diagram = document.querySelector('mj-diagram');
            diagram.graph = {
                nodes: [{ id: 'ui', label: 'UI Layer' }, { id: 'api', label: 'API Gateway', description: 'Auth' }],
                edges: [{ source: 'ui', target: 'api', label: 'HTTP' }]
            };
            await new Promise((resolve) => setTimeout(resolve, 200));
            const root = diagram.shadowRoot;
            const node = () => root.querySelector('.diagram-node[data-node-id="api"]');
            const panel = root.querySelector('.selection-panel');
            const press = (target, key) => target.dispatchEvent(new KeyboardEvent('keydown',
                { key: key, bubbles: true, composed: true, cancelable: true }));
            node().focus();
            press(node(), 'Enter');
            const opened = {
                open: panel.classList.contains('open'),
                modal: panel.getAttribute('aria-modal'),
                title: panel.querySelector('.selection-title').textContent,
                description: panel.querySelector('.selection-desc').textContent,
                focusInPanel: root.activeElement === panel,
                highlighted: node().classList.contains('selected')
            };
            press(panel, 'Escape');
            return {
                opened: opened,
                groupAriaHidden: root.querySelector('svg g.diagram-content').getAttribute('aria-hidden'),
                nodeRole: node().getAttribute('role'),
                openAfterEscape: panel.classList.contains('open'),
                highlightedAfter: root.querySelectorAll('.selected').length,
                focusBackOnNode: root.activeElement === node(),
                selectedNodeId: diagram.selectedNodeId
            };
        }"""
    )
    assert state["opened"] == {
        "open": True, "modal": "false", "title": "API Gateway", "description": "Auth",
        "focusInPanel": True, "highlighted": True
    }
    assert state["groupAriaHidden"] is None
    assert state["nodeRole"] == "button"
    assert state["openAfterEscape"] is False
    assert state["highlightedAfter"] == 0
    assert state["focusBackOnNode"] is True
    assert state["selectedNodeId"] is None

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_diagram_empty_graph_and_interactive_false(page, base_url):
    """
        An empty graph removes the previous drawing and shows the empty state;
        interactive="false" stops zoom and selection; directed="false" drops
        the arrowheads.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
    """

    _open_preview(page, base_url, "media", "mj-diagram")

    html = '<mj-diagram label="Static test" style="height:240px"></mj-diagram>'
    frame = _fill_and_run(page, html)
    _wait_for_element(frame, "mj-diagram")

    state = frame.evaluate(
        """async () => {
            const diagram = document.querySelector('mj-diagram');
            const root = diagram.shadowRoot;
            const graph = {
                nodes: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
                edges: [{ source: 'a', target: 'b' }]
            };
            diagram.graph = graph;
            await new Promise((resolve) => setTimeout(resolve, 150));
            const markersDirected = root.querySelectorAll('marker').length;
            diagram.setAttribute('directed', 'false');
            const markersUndirected = root.querySelectorAll('marker').length;
            diagram.setAttribute('interactive', 'false');
            const scaleBefore = root.querySelector('svg g.diagram-content').getAttribute('transform');
            root.querySelector('[part="zoom-in"]').click();
            root.querySelector('.diagram-node').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            const staticState = {
                transformUnchanged: root.querySelector('svg g.diagram-content').getAttribute('transform') === scaleBefore,
                nodeFocusable: root.querySelector('.diagram-node').hasAttribute('tabindex'),
                listDisabled: root.querySelector('.node-btn').disabled,
                selected: diagram.selectedNodeId
            };
            diagram.graph = { nodes: [], edges: [] };
            return {
                markersDirected: markersDirected,
                markersUndirected: markersUndirected,
                staticState: staticState,
                svgAfterEmpty: root.querySelector('svg') !== null,
                emptyVisible: root.querySelector('.empty').classList.contains('visible')
            };
        }"""
    )
    assert state["markersDirected"] == 1
    assert state["markersUndirected"] == 0
    assert state["staticState"] == {
        "transformUnchanged": True, "nodeFocusable": False, "listDisabled": True, "selected": None
    }
    assert state["svgAfterEmpty"] is False
    assert state["emptyVisible"] is True

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
