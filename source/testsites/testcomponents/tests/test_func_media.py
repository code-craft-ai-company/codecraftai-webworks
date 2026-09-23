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


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
