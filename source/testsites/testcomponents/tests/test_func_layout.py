"""
    .. module:: testcomponents.tests.test_func_layout

    Functional Playwright tests for the 'layout' component group.

    Covers all 18 components in catalog/layout.py:
      mj-card, mj-surface, mj-grid, mj-stack, mj-spacer, mj-aspect-ratio,
      mj-accordion, mj-disclosure, mj-split-pane, mj-scroll-area,
      mj-carousel, mj-feed, mj-media-object, mj-hero, mj-empty-state,
      mj-skeleton, mj-divider, mj-dock-layout.

    Interactive components (accordion, disclosure, split-pane, carousel,
    scroll-area, feed) receive real interaction tests.  Presentational
    components receive lighter render / attribute / structure tests.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _preview_frame(page):
    """
        Resolve the Frame object for the playground preview iframe.

        :param page: The Playwright page.

        :returns: The Frame inside the preview iframe.
    """

    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    return frame


def _open_component(page, base_url, group, tag):
    """
        Open a component playground page and wait for the custom element to
        be registered inside the preview iframe.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param group: The component group key.
        :param tag: The HTML custom-element tag name.

        :returns: The preview Frame with the library loaded.
    """

    page.goto(base_url + f"/components/{group}/{tag}")
    frame = _preview_frame(page)
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


def _render_custom_html(page, base_url, group, anchor_tag, html):
    """
        Replace the playground editor content with ``html``, press Run, and
        re-acquire the preview frame.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param group: The component group key.
        :param anchor_tag: A tag expected to already be registered in the frame.
        :param html: The HTML snippet to render in the playground.

        :returns: The re-acquired preview Frame.
    """

    page.goto(base_url + f"/components/{group}/{anchor_tag}")
    frame = _preview_frame(page)
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=anchor_tag,
        timeout=15000,
    )

    editor = page.get_by_test_id("playground-editor")
    editor.fill(html)
    page.get_by_test_id("playground-run").click()

    frame = _preview_frame(page)
    return frame


# ---------------------------------------------------------------------------
# mj-card
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_card_renders(page, base_url):
    """
        mj-card renders in the preview iframe and upgrades to a live custom
        element with a shadow root.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-card")

    instance = frame.locator("mj-card").first
    expect(instance).to_be_attached(timeout=10000)

    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-card').shadowRoot !== null"
    )
    assert has_shadow is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_card_heading_attribute(page, base_url):
    """
        mj-card reflects the heading attribute into its shadow DOM heading
        element.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-card heading="Test Heading" elevation="raised"><p>body</p></mj-card>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-card", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-card') !== undefined",
        timeout=15000,
    )

    instance = frame.locator("mj-card").first
    expect(instance).to_be_attached(timeout=10000)

    heading_text = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-card');
            if (el === null || el.shadowRoot === null) { return ''; }
            const h = el.shadowRoot.querySelector('.heading');
            return h !== null ? h.textContent.trim() : '';
        }"""
    )
    assert heading_text == "Test Heading"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_card_elevation_attribute_reflected(page, base_url):
    """
        mj-card reflects the elevation attribute on the host element.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-card heading="Flat Card" elevation="flat"><p>content</p></mj-card>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-card", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-card') !== undefined",
        timeout=15000,
    )

    elevation_val = frame.evaluate(
        "() => document.querySelector('mj-card').getAttribute('elevation')"
    )
    assert elevation_val == "flat"

    return


# ---------------------------------------------------------------------------
# mj-surface
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_surface_renders(page, base_url):
    """
        mj-surface renders with a shadow root in the preview iframe.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-surface")

    instance = frame.locator("mj-surface").first
    expect(instance).to_be_attached(timeout=10000)

    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-surface').shadowRoot !== null"
    )
    assert has_shadow is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_surface_slotted_content_visible(page, base_url):
    """
        mj-surface passes slotted content through to the page.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-surface elevation="outlined" padding="lg">'
        '<p id="inner-text">Hello surface</p>'
        "</mj-surface>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-surface", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-surface') !== undefined",
        timeout=15000,
    )

    inner = frame.locator("#inner-text")
    expect(inner).to_be_visible(timeout=10000)
    expect(inner).to_contain_text("Hello surface")

    return


# ---------------------------------------------------------------------------
# mj-grid
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_grid_renders_children(page, base_url):
    """
        mj-grid renders and its slotted children are visible.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-grid columns="2" gap="md">'
        '<div id="cell-a">Cell A</div>'
        '<div id="cell-b">Cell B</div>'
        "</mj-grid>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-grid", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-grid') !== undefined",
        timeout=15000,
    )

    expect(frame.locator("#cell-a")).to_be_visible(timeout=10000)
    expect(frame.locator("#cell-b")).to_be_visible(timeout=10000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_grid_columns_attribute_reflected(page, base_url):
    """
        mj-grid reflects the columns attribute on its host element.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-grid columns="3" gap="sm"><div>A</div></mj-grid>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-grid", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-grid') !== undefined",
        timeout=15000,
    )

    cols = frame.evaluate(
        "() => document.querySelector('mj-grid').getAttribute('columns')"
    )
    assert cols == "3"

    return


# ---------------------------------------------------------------------------
# mj-stack
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_stack_renders_slotted_children(page, base_url):
    """
        mj-stack renders slotted children in a flex container.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-stack direction="horizontal" gap="sm">'
        '<span id="item-1">One</span>'
        '<span id="item-2">Two</span>'
        "</mj-stack>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-stack", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-stack') !== undefined",
        timeout=15000,
    )

    expect(frame.locator("#item-1")).to_be_visible(timeout=10000)
    expect(frame.locator("#item-2")).to_be_visible(timeout=10000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_stack_direction_attribute_reflected(page, base_url):
    """
        mj-stack reflects the direction attribute on its host element.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-stack direction="horizontal" gap="md"><span>A</span></mj-stack>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-stack", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-stack') !== undefined",
        timeout=15000,
    )

    direction = frame.evaluate(
        "() => document.querySelector('mj-stack').getAttribute('direction')"
    )
    assert direction == "horizontal"

    return


# ---------------------------------------------------------------------------
# mj-spacer
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_spacer_renders(page, base_url):
    """
        mj-spacer renders in the preview iframe as a custom element.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-spacer")

    instance = frame.locator("mj-spacer").first
    expect(instance).to_be_attached(timeout=10000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_spacer_size_attribute_reflected(page, base_url):
    """
        mj-spacer reflects the size attribute on the host element.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-stack direction="horizontal">'
        '<span>left</span>'
        '<mj-spacer size="md"></mj-spacer>'
        '<span>right</span>'
        "</mj-stack>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-spacer", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-spacer') !== undefined",
        timeout=15000,
    )

    size_val = frame.evaluate(
        "() => document.querySelector('mj-spacer').getAttribute('size')"
    )
    assert size_val == "md"

    return


# ---------------------------------------------------------------------------
# mj-aspect-ratio
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_aspect_ratio_renders(page, base_url):
    """
        mj-aspect-ratio renders with a shadow root in the preview iframe.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-aspect-ratio")

    instance = frame.locator("mj-aspect-ratio").first
    expect(instance).to_be_attached(timeout=10000)

    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-aspect-ratio').shadowRoot !== null"
    )
    assert has_shadow is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_aspect_ratio_attribute_reflected(page, base_url):
    """
        mj-aspect-ratio reflects the ratio attribute on the host element.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-aspect-ratio ratio="4x3" style="max-width:20rem">'
        '<img src="https://picsum.photos/400/300" alt="test" />'
        "</mj-aspect-ratio>"
    )
    frame = _render_custom_html(
        page,
        base_url,
        group="layout",
        anchor_tag="mj-aspect-ratio",
        html=html,
    )
    frame.wait_for_function(
        "() => customElements.get('mj-aspect-ratio') !== undefined",
        timeout=15000,
    )

    ratio_val = frame.evaluate(
        "() => document.querySelector('mj-aspect-ratio').getAttribute('ratio')"
    )
    assert ratio_val == "4x3"

    return


# ---------------------------------------------------------------------------
# mj-disclosure
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_disclosure_renders_and_is_collapsed_by_default(page, base_url):
    """
        mj-disclosure renders with the trigger button visible and the panel
        collapsed (aria-expanded="false") by default.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-disclosure heading="Details">'
        "<p>Hidden content</p>"
        "</mj-disclosure>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-disclosure", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-disclosure') !== undefined",
        timeout=15000,
    )

    trigger = frame.locator("mj-disclosure").locator("button.trigger")
    expect(trigger).to_be_visible(timeout=10000)

    aria_expanded = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-disclosure');
            if (el === null || el.shadowRoot === null) { return ''; }
            const btn = el.shadowRoot.querySelector('button');
            return btn !== null ? btn.getAttribute('aria-expanded') : '';
        }"""
    )
    assert aria_expanded == "false"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_disclosure_expands_on_click(page, base_url):
    """
        Clicking the trigger button opens the disclosure panel and sets
        aria-expanded to "true".

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-disclosure heading="Expand Me" animated="false">'
        '<p id="panel-content">Now visible</p>'
        "</mj-disclosure>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-disclosure", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-disclosure') !== undefined",
        timeout=15000,
    )

    trigger = frame.locator("mj-disclosure button.trigger")
    expect(trigger).to_be_visible(timeout=10000)
    trigger.click()

    aria_expanded = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-disclosure');
            if (el === null || el.shadowRoot === null) { return ''; }
            const btn = el.shadowRoot.querySelector('button');
            return btn !== null ? btn.getAttribute('aria-expanded') : '';
        }"""
    )
    assert aria_expanded == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_disclosure_open_attribute_starts_expanded(page, base_url):
    """
        mj-disclosure with the open attribute renders with aria-expanded="true"
        without any user interaction.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-disclosure heading="Already Open" open>'
        "<p>Visible from the start</p>"
        "</mj-disclosure>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-disclosure", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-disclosure') !== undefined",
        timeout=15000,
    )

    aria_expanded = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-disclosure');
            if (el === null || el.shadowRoot === null) { return ''; }
            const btn = el.shadowRoot.querySelector('button');
            return btn !== null ? btn.getAttribute('aria-expanded') : '';
        }"""
    )
    assert aria_expanded == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_disclosure_toggle_event_fires(page, base_url):
    """
        Clicking the trigger emits the mj-disclosure-toggle event.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-disclosure heading="Event Test" animated="false">'
        "<p>Content</p>"
        "</mj-disclosure>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-disclosure", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-disclosure') !== undefined",
        timeout=15000,
    )

    frame.evaluate(
        """() => {
            window.__mjdiscevents = [];
            document.querySelector('mj-disclosure').addEventListener(
                'mj-disclosure-toggle',
                e => window.__mjdiscevents.push(e.type)
            );
        }"""
    )

    trigger = frame.locator("mj-disclosure button.trigger")
    trigger.click()

    events = frame.evaluate("() => window.__mjdiscevents")
    assert "mj-disclosure-toggle" in events

    return


# ---------------------------------------------------------------------------
# mj-accordion
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_accordion_renders_panels(page, base_url):
    """
        mj-accordion renders with multiple mj-disclosure children visible.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-accordion")

    panels = frame.locator("mj-disclosure")
    count = panels.count()
    assert count >= 2

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_accordion_single_open_mode(page, base_url):
    """
        In default (single-open) mode, opening a second disclosure closes the
        first one.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        "<mj-accordion>"
        '<mj-disclosure id="panel-1" heading="First" animated="false">'
        "<p>Content 1</p>"
        "</mj-disclosure>"
        '<mj-disclosure id="panel-2" heading="Second" animated="false">'
        "<p>Content 2</p>"
        "</mj-disclosure>"
        "</mj-accordion>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-accordion", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-accordion') !== undefined",
        timeout=15000,
    )

    # Open the first panel.
    first_trigger = frame.locator("#panel-1").locator("button.trigger")
    first_trigger.click()

    first_expanded = frame.evaluate(
        """() => {
            const el = document.querySelector('#panel-1');
            return el !== null ? el.hasAttribute('open') : false;
        }"""
    )
    assert first_expanded is True

    # Open the second panel; the first should close automatically.
    second_trigger = frame.locator("#panel-2").locator("button.trigger")
    second_trigger.click()

    second_expanded = frame.evaluate(
        """() => {
            const el = document.querySelector('#panel-2');
            return el !== null ? el.hasAttribute('open') : false;
        }"""
    )
    assert second_expanded is True

    first_still_open = frame.evaluate(
        """() => {
            const el = document.querySelector('#panel-1');
            return el !== null ? el.hasAttribute('open') : true;
        }"""
    )
    assert first_still_open is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_accordion_allow_multiple(page, base_url):
    """
        With allow-multiple set, both panels can be open simultaneously.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        "<mj-accordion allow-multiple>"
        '<mj-disclosure id="m1" heading="One" animated="false">'
        "<p>Content 1</p>"
        "</mj-disclosure>"
        '<mj-disclosure id="m2" heading="Two" animated="false">'
        "<p>Content 2</p>"
        "</mj-disclosure>"
        "</mj-accordion>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-accordion", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-accordion') !== undefined",
        timeout=15000,
    )

    frame.locator("#m1").locator("button.trigger").click()
    frame.locator("#m2").locator("button.trigger").click()

    both_open = frame.evaluate(
        """() => {
            const m1 = document.querySelector('#m1');
            const m2 = document.querySelector('#m2');
            return m1.hasAttribute('open') && m2.hasAttribute('open');
        }"""
    )
    assert both_open is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_accordion_close_event_fires(page, base_url):
    """
        mj-accordion emits mj-accordion-close when single-open mode forces a
        panel to close.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        "<mj-accordion>"
        '<mj-disclosure id="ac1" heading="Alpha" animated="false">'
        "<p>A</p>"
        "</mj-disclosure>"
        '<mj-disclosure id="ac2" heading="Beta" animated="false">'
        "<p>B</p>"
        "</mj-disclosure>"
        "</mj-accordion>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-accordion", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-accordion') !== undefined",
        timeout=15000,
    )

    frame.evaluate(
        """() => {
            window.__mjaccevents = [];
            document.querySelector('mj-accordion').addEventListener(
                'mj-accordion-close',
                e => window.__mjaccevents.push(e.type)
            );
        }"""
    )

    frame.locator("#ac1").locator("button.trigger").click()
    frame.locator("#ac2").locator("button.trigger").click()

    events = frame.evaluate("() => window.__mjaccevents")
    assert "mj-accordion-close" in events

    return


# ---------------------------------------------------------------------------
# mj-split-pane
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_pane_renders_both_panes(page, base_url):
    """
        mj-split-pane renders slotted content in both the start and end panes.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-split-pane initial-size="40%" style="height:10rem">'
        '<div slot="start" id="start-pane">Start</div>'
        '<div slot="end" id="end-pane">End</div>'
        "</mj-split-pane>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-split-pane", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-split-pane') !== undefined",
        timeout=15000,
    )

    expect(frame.locator("#start-pane")).to_be_visible(timeout=10000)
    expect(frame.locator("#end-pane")).to_be_visible(timeout=10000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_pane_separator_has_correct_role(page, base_url):
    """
        mj-split-pane renders a separator element with role="separator".

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-split-pane initial-size="50%" style="height:10rem">'
        '<div slot="start">Left</div>'
        '<div slot="end">Right</div>'
        "</mj-split-pane>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-split-pane", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-split-pane') !== undefined",
        timeout=15000,
    )

    separator_role = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-split-pane');
            if (el === null || el.shadowRoot === null) { return ''; }
            const sep = el.shadowRoot.querySelector('[role=separator]');
            return sep !== null ? sep.getAttribute('role') : '';
        }"""
    )
    assert separator_role == "separator"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_pane_keyboard_resize(page, base_url):
    """
        Pressing ArrowRight on the separator emits mj-split-resize-end and
        updates the start pane size.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-split-pane initial-size="50%" style="height:10rem;width:400px">'
        '<div slot="start">Left</div>'
        '<div slot="end">Right</div>'
        "</mj-split-pane>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-split-pane", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-split-pane') !== undefined",
        timeout=15000,
    )

    frame.evaluate(
        """() => {
            window.__mjsplitevents = [];
            document.querySelector('mj-split-pane').addEventListener(
                'mj-split-resize-end',
                e => window.__mjsplitevents.push(e.type)
            );
        }"""
    )

    separator = frame.locator("mj-split-pane").locator("[role=separator]")
    separator.focus()
    separator.press("ArrowRight")

    events = frame.evaluate("() => window.__mjsplitevents")
    assert "mj-split-resize-end" in events

    return


# ---------------------------------------------------------------------------
# mj-scroll-area
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_scroll_area_renders_viewport(page, base_url):
    """
        mj-scroll-area renders a viewport element with role="region" inside
        its shadow root.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-scroll-area style="height:6rem" aria-label="Test scroll">'
        "<p>Line 1</p><p>Line 2</p><p>Line 3</p><p>Line 4</p>"
        "<p>Line 5</p><p>Line 6</p>"
        "</mj-scroll-area>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-scroll-area", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-scroll-area') !== undefined",
        timeout=15000,
    )

    viewport_role = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-scroll-area');
            if (el === null || el.shadowRoot === null) { return ''; }
            const vp = el.shadowRoot.querySelector('.viewport');
            return vp !== null ? vp.getAttribute('role') : '';
        }"""
    )
    assert viewport_role == "region"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_scroll_area_scroll_event_fires(page, base_url):
    """
        Programmatically scrolling the viewport emits the mj-scroll event.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-scroll-area style="height:4rem" aria-label="Scroll test">'
        + "".join(f"<p>Item {i}</p>" for i in range(20))
        + "</mj-scroll-area>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-scroll-area", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-scroll-area') !== undefined",
        timeout=15000,
    )

    frame.evaluate(
        """() => {
            window.__mjscrollevents = [];
            document.querySelector('mj-scroll-area').addEventListener(
                'mj-scroll',
                e => window.__mjscrollevents.push(e.type)
            );
        }"""
    )

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-scroll-area');
            const vp = el.shadowRoot.querySelector('.viewport');
            vp.scrollTop = 50;
            vp.dispatchEvent(new Event('scroll'));
        }"""
    )

    frame.wait_for_function(
        "() => window.__mjscrollevents.length > 0",
        timeout=5000,
    )

    events = frame.evaluate("() => window.__mjscrollevents")
    assert "mj-scroll" in events

    return


# ---------------------------------------------------------------------------
# mj-carousel
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_carousel_renders_slides(page, base_url):
    """
        mj-carousel renders mj-carousel-slide children and shows the first
        slide by default.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-carousel")

    instance = frame.locator("mj-carousel").first
    expect(instance).to_be_attached(timeout=10000)

    slides = frame.locator("mj-carousel-slide")
    count = slides.count()
    assert count >= 2

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_carousel_first_slide_visible(page, base_url):
    """
        The first mj-carousel-slide has aria-hidden="false" on initial render.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-carousel label="Test carousel">'
        '<mj-carousel-slide id="slide-0"><p>Slide 0</p></mj-carousel-slide>'
        '<mj-carousel-slide id="slide-1"><p>Slide 1</p></mj-carousel-slide>'
        "</mj-carousel>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-carousel", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-carousel') !== undefined",
        timeout=15000,
    )

    first_hidden = frame.evaluate(
        "() => document.querySelector('#slide-0').getAttribute('aria-hidden')"
    )
    assert first_hidden == "false"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_carousel_next_button_advances_slide(page, base_url):
    """
        Clicking the next-slide button advances to slide index 1 and sets
        aria-hidden="false" on the second slide.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-carousel label="Nav carousel" transition="none">'
        '<mj-carousel-slide id="s0"><p>First</p></mj-carousel-slide>'
        '<mj-carousel-slide id="s1"><p>Second</p></mj-carousel-slide>'
        '<mj-carousel-slide id="s2"><p>Third</p></mj-carousel-slide>'
        "</mj-carousel>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-carousel", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-carousel') !== undefined",
        timeout=15000,
    )

    next_btn = frame.locator("mj-carousel").locator("[part=next-button]")
    expect(next_btn).to_be_visible(timeout=10000)
    next_btn.click()

    frame.wait_for_function(
        "() => document.querySelector('#s1').getAttribute('aria-hidden') === 'false'",
        timeout=5000,
    )

    second_visible = frame.evaluate(
        "() => document.querySelector('#s1').getAttribute('aria-hidden')"
    )
    assert second_visible == "false"

    first_hidden = frame.evaluate(
        "() => document.querySelector('#s0').getAttribute('aria-hidden')"
    )
    assert first_hidden == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_carousel_picker_dots_render(page, base_url):
    """
        mj-carousel renders picker-item buttons matching the number of slides.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-carousel label="Dots carousel">'
        '<mj-carousel-slide><p>A</p></mj-carousel-slide>'
        '<mj-carousel-slide><p>B</p></mj-carousel-slide>'
        '<mj-carousel-slide><p>C</p></mj-carousel-slide>'
        "</mj-carousel>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-carousel", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-carousel') !== undefined",
        timeout=15000,
    )

    dot_count = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-carousel');
            if (el === null || el.shadowRoot === null) { return 0; }
            return el.shadowRoot.querySelectorAll('.picker-item').length;
        }"""
    )
    assert dot_count == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_carousel_change_event_fires(page, base_url):
    """
        Clicking next emits the mj-carousel-change event.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-carousel label="Event carousel" transition="none">'
        '<mj-carousel-slide><p>1</p></mj-carousel-slide>'
        '<mj-carousel-slide><p>2</p></mj-carousel-slide>'
        "</mj-carousel>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-carousel", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-carousel') !== undefined",
        timeout=15000,
    )

    frame.evaluate(
        """() => {
            window.__mjcarouselevents = [];
            document.querySelector('mj-carousel').addEventListener(
                'mj-carousel-change',
                e => window.__mjcarouselevents.push(e.type)
            );
        }"""
    )

    next_btn = frame.locator("mj-carousel").locator("[part=next-button]")
    next_btn.click()

    frame.wait_for_function(
        "() => window.__mjcarouselevents.length > 0",
        timeout=5000,
    )

    events = frame.evaluate("() => window.__mjcarouselevents")
    assert "mj-carousel-change" in events

    return


# ---------------------------------------------------------------------------
# mj-feed
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_feed_renders_items(page, base_url):
    """
        mj-feed renders mj-feed-item children.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-feed has-more="false">'
        '<mj-feed-item id="fi-1"><p>Item 1</p></mj-feed-item>'
        '<mj-feed-item id="fi-2"><p>Item 2</p></mj-feed-item>'
        "</mj-feed>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-feed", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-feed') !== undefined",
        timeout=15000,
    )

    expect(frame.locator("#fi-1")).to_be_visible(timeout=10000)
    expect(frame.locator("#fi-2")).to_be_visible(timeout=10000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_feed_has_feed_role(page, base_url):
    """
        mj-feed shadow root contains an element with role="feed".

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-feed has-more="false">'
        "<mj-feed-item><p>Item</p></mj-feed-item>"
        "</mj-feed>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-feed", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-feed') !== undefined",
        timeout=15000,
    )

    feed_role = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-feed');
            if (el === null || el.shadowRoot === null) { return ''; }
            const root = el.shadowRoot.querySelector('[role=feed]');
            return root !== null ? root.getAttribute('role') : '';
        }"""
    )
    assert feed_role == "feed"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_feed_load_more_button_visible(page, base_url):
    """
        When load-mode is "button" and has-more is not false, the Load More
        button is visible.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-feed load-mode="button" has-more="true">'
        "<mj-feed-item><p>Item</p></mj-feed-item>"
        "</mj-feed>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-feed", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-feed') !== undefined",
        timeout=15000,
    )

    load_more_visible = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-feed');
            if (el === null || el.shadowRoot === null) { return false; }
            const btn = el.shadowRoot.querySelector('.load-more-btn');
            if (btn === null) { return false; }
            const style = window.getComputedStyle(btn);
            return style.display !== 'none';
        }"""
    )
    assert load_more_visible is True

    return


# ---------------------------------------------------------------------------
# mj-media-object
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_media_object_renders(page, base_url):
    """
        mj-media-object renders with a shadow root.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-media-object")

    instance = frame.locator("mj-media-object").first
    expect(instance).to_be_attached(timeout=10000)

    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-media-object').shadowRoot !== null"
    )
    assert has_shadow is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_media_object_slotted_content_visible(page, base_url):
    """
        mj-media-object makes both the media slot and default slot content
        visible.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-media-object gap="md">'
        '<span slot="media" id="mo-media">Avatar</span>'
        '<span id="mo-body">Body text</span>'
        "</mj-media-object>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-media-object", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-media-object') !== undefined",
        timeout=15000,
    )

    expect(frame.locator("#mo-media")).to_be_visible(timeout=10000)
    expect(frame.locator("#mo-body")).to_be_visible(timeout=10000)

    return


# ---------------------------------------------------------------------------
# mj-hero
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_hero_renders(page, base_url):
    """
        mj-hero renders with a shadow root in the preview iframe.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-hero")

    instance = frame.locator("mj-hero").first
    expect(instance).to_be_attached(timeout=10000)

    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-hero').shadowRoot !== null"
    )
    assert has_shadow is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_hero_heading_attribute_reflected(page, base_url):
    """
        mj-hero reflects the heading attribute and renders it in the shadow DOM.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-hero heading="Welcome Hero" bg-color="#1a1a2e"></mj-hero>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-hero", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-hero') !== undefined",
        timeout=15000,
    )

    heading_val = frame.evaluate(
        "() => document.querySelector('mj-hero').getAttribute('heading')"
    )
    assert heading_val == "Welcome Hero"

    return


# ---------------------------------------------------------------------------
# mj-empty-state
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_empty_state_renders(page, base_url):
    """
        mj-empty-state renders with a shadow root.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-empty-state")

    instance = frame.locator("mj-empty-state").first
    expect(instance).to_be_attached(timeout=10000)

    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-empty-state').shadowRoot !== null"
    )
    assert has_shadow is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_empty_state_heading_in_shadow_dom(page, base_url):
    """
        mj-empty-state renders the heading attribute in its shadow DOM.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-empty-state heading="Nothing here" show-illustration="false">'
        "</mj-empty-state>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-empty-state", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-empty-state') !== undefined",
        timeout=15000,
    )

    heading_text = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-empty-state');
            if (el === null || el.shadowRoot === null) { return ''; }
            const h = el.shadowRoot.querySelector('.heading-el');
            return h !== null ? h.textContent.trim() : '';
        }"""
    )
    assert heading_text == "Nothing here"

    return


# ---------------------------------------------------------------------------
# mj-skeleton
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_skeleton_renders_rectangle_variant(page, base_url):
    """
        mj-skeleton rectangle variant renders and is attached to the DOM.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-skeleton variant="rectangle" width="100%" height="4rem"></mj-skeleton>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-skeleton", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-skeleton') !== undefined",
        timeout=15000,
    )

    instance = frame.locator("mj-skeleton").first
    expect(instance).to_be_attached(timeout=10000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_skeleton_circle_variant_reflected(page, base_url):
    """
        mj-skeleton reflects the variant="circle" attribute on the host.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-skeleton variant="circle" width="3rem"></mj-skeleton>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-skeleton", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-skeleton') !== undefined",
        timeout=15000,
    )

    variant_val = frame.evaluate(
        "() => document.querySelector('mj-skeleton').getAttribute('variant')"
    )
    assert variant_val == "circle"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_skeleton_root_div_is_aria_hidden(page, base_url):
    """
        mj-skeleton renders its inner root div with aria-hidden="true" to
        exclude the shimmer from the accessibility tree, while a visually
        hidden live status region announces the loading state.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-skeleton variant="text" lines="3"></mj-skeleton>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-skeleton", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-skeleton') !== undefined",
        timeout=15000,
    )

    root_aria_hidden = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-skeleton');
            if (el === null || el.shadowRoot === null) { return ''; }
            const root = el.shadowRoot.querySelector('.root');
            return root !== null ? root.getAttribute('aria-hidden') : '';
        }"""
    )
    assert root_aria_hidden == "true"

    status_role = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-skeleton');
            if (el === null || el.shadowRoot === null) { return ''; }
            const status = el.shadowRoot.querySelector('.status');
            return status !== null ? status.getAttribute('role') : '';
        }"""
    )
    assert status_role == "status"

    return


# ---------------------------------------------------------------------------
# mj-divider
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_divider_renders_with_separator_role(page, base_url):
    """
        mj-divider shadow DOM contains an element with role="separator" by
        default (non-decorative).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-divider spacing="md"></mj-divider>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-divider", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-divider') !== undefined",
        timeout=15000,
    )

    instance = frame.locator("mj-divider").first
    expect(instance).to_be_attached(timeout=10000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_divider_label_attribute(page, base_url):
    """
        mj-divider with a label attribute reflects that attribute on the host.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-divider label="or" spacing="md"></mj-divider>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-divider", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-divider') !== undefined",
        timeout=15000,
    )

    label_val = frame.evaluate(
        "() => document.querySelector('mj-divider').getAttribute('label')"
    )
    assert label_val == "or"

    return


# ---------------------------------------------------------------------------
# mj-dock-layout
# ---------------------------------------------------------------------------


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_renders(page, base_url):
    """
        mj-dock-layout renders with a shadow root and is attached to the DOM.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-dock-layout")

    instance = frame.locator("mj-dock-layout").first
    expect(instance).to_be_attached(timeout=10000)

    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-dock-layout').shadowRoot !== null"
    )
    assert has_shadow is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_positions_top_child(page, base_url):
    """
        mj-dock-layout sets position:absolute on a child with dock="top" after
        the layout pass runs.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout style="height:20rem;width:40rem">'
        '<header id="top-bar" dock="top" style="height:3rem;background:#aaa">'
        "Header"
        "</header>"
        '<main id="fill-area" dock="fill" style="background:#eee">'
        "Content"
        "</main>"
        "</mj-dock-layout>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-dock-layout') !== undefined",
        timeout=15000,
    )

    frame.wait_for_function(
        "() => document.querySelector('#top-bar').style.position === 'absolute'",
        timeout=5000,
    )

    top_bar_position = frame.evaluate(
        "() => document.querySelector('#top-bar').style.position"
    )
    assert top_bar_position == "absolute"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_fill_child_positioned(page, base_url):
    """
        mj-dock-layout sets position:absolute on the dock="fill" child and
        positions it below the top bar.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout style="height:20rem;width:40rem">'
        '<header id="dl-header" dock="top" style="height:2rem;background:#ccc">'
        "Top"
        "</header>"
        '<main id="dl-fill" dock="fill" style="background:#f0f">'
        "Main"
        "</main>"
        "</mj-dock-layout>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-dock-layout') !== undefined",
        timeout=15000,
    )

    frame.wait_for_function(
        "() => document.querySelector('#dl-fill').style.position === 'absolute'",
        timeout=5000,
    )

    fill_position = frame.evaluate(
        "() => document.querySelector('#dl-fill').style.position"
    )
    assert fill_position == "absolute"

    fill_top = frame.evaluate(
        "() => document.querySelector('#dl-fill').style.top"
    )
    # The fill child top should be non-zero (below the header).
    assert fill_top != "" and fill_top != "0px"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_emits_mj_layout_event(page, base_url):
    """
        mj-dock-layout emits a mj-layout event after each layout pass.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout style="height:10rem;width:20rem">'
        '<div dock="top" style="height:2rem">Top</div>'
        '<div dock="fill">Fill</div>'
        "</mj-dock-layout>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    frame.wait_for_function(
        "() => customElements.get('mj-dock-layout') !== undefined",
        timeout=15000,
    )

    # Attach the listener, then explicitly request a relayout so the event
    # fires deterministically after the listener is in place (the initial
    # layout pass may complete before this evaluate runs).
    frame.evaluate(
        """() => {
            window.__mjlayoutevents = [];
            const layout = document.querySelector('mj-dock-layout');
            layout.addEventListener(
                'mj-layout',
                e => window.__mjlayoutevents.push(e.type)
            );
            layout.requestLayout();
        }"""
    )

    frame.wait_for_function(
        "() => window.__mjlayoutevents.length > 0",
        timeout=10000,
    )

    events = frame.evaluate("() => window.__mjlayoutevents")
    assert "mj-layout" in events

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
