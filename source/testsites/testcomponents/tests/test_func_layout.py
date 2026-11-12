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


def _wait_for_upgrade(frame, selector, inner_selector):
    """
        Wait until the element matching ``selector`` in the preview frame has
        been upgraded and rendered ``inner_selector`` into its shadow root.
        The light-DOM markup is visible before the library module has run, so
        a test that reads component state must wait for this first.

        :param frame: The preview Frame.
        :param selector: Selector of the component element.
        :param inner_selector: Selector of an element inside its shadow root.
    """

    frame.wait_for_function(
        """([selector, innerSelector]) => {
            const element = document.querySelector(selector);
            return element !== null && element.shadowRoot !== null &&
                element.shadowRoot.querySelector(innerSelector) !== null;
        }""",
        arg=[selector, inner_selector],
        timeout=15000,
    )
    return


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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_card_heading_attribute_is_rendered_as_text(page, base_url):
    """
        mj-card renders markup in the heading and subheading attributes as
        literal text; no element is created from it and no handler runs.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = "<mj-card id=\"hx\" heading=\"placeholder\"><p>body</p></mj-card>"
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-card", html=html
    )
    _wait_for_upgrade(frame, "#hx", ".heading")

    result = frame.evaluate(
        """() => {
            const payload = 'x\\'"><img src="data:,x" onerror="top.__hits=(top.__hits||0)+1">';
            const card = document.querySelector('#hx');
            card.setAttribute('heading', payload);
            card.setAttribute('subheading', payload);
            return new Promise((resolve) => {
                setTimeout(() => {
                    const heading = card.shadowRoot.querySelector('.heading');
                    resolve({
                        hits: String(top.__hits),
                        images: card.shadowRoot.querySelectorAll('img').length,
                        headingText: heading !== null ? heading.textContent === payload : false
                    });
                }, 300);
            });
        }"""
    )
    assert result["hits"] == "undefined"
    assert result["images"] == 0
    assert result["headingText"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_card_link_does_not_block_footer_actions(page, base_url):
    """
        A clickable card (href) keeps its footer buttons clickable with the
        pointer, while the body area belongs to the card link, which is named
        from the heading.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-card id="lc" heading="Mountain Hike" href="#hike" style="width:20rem">'
        '<p id="lc-body">A trek through alpine meadows.</p>'
        '<div slot="footer"><button id="lc-book">Book</button></div>'
        "</mj-card>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-card", html=html
    )
    _wait_for_upgrade(frame, "#lc", ".card-link")
    expect(frame.locator("#lc-book")).to_be_visible(timeout=10000)

    frame.evaluate(
        """() => {
            window.__mjbookclicks = 0;
            document.querySelector('#lc-book').addEventListener('click', () => {
                window.__mjbookclicks += 1;
            });
        }"""
    )
    frame.locator("#lc-book").click()
    clicks = frame.evaluate("() => window.__mjbookclicks")
    assert clicks == 1

    link = frame.evaluate(
        """() => {
            const card = document.querySelector('#lc');
            const link = card.shadowRoot.querySelector('.card-link');
            const body = document.querySelector('#lc-body').getBoundingClientRect();
            const hit = card.shadowRoot.elementFromPoint(body.left + 5, body.top + 5);
            const labelId = link.getAttribute('aria-labelledby');
            const label = labelId !== null ? card.shadowRoot.getElementById(labelId) : null;
            return {
                bodyHitsLink: hit === link,
                name: label !== null ? label.textContent : ''
            };
        }"""
    )
    assert link["bodyHitsLink"] is True
    assert link["name"] == "Mountain Hike"

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_surface_nested_does_not_inherit_attributes(page, base_url):
    """
        A surface nested in a raised, padded, rounded surface keeps its own
        defaults: the custom properties the outer attributes write on the
        host are not inherited (FP-019).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-surface id="outer" elevation="raised" padding="lg" radius="full">'
        '<mj-surface id="inner">Inner</mj-surface>'
        "</mj-surface>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-surface", html=html
    )
    _wait_for_upgrade(frame, "#inner", ".root")

    styles = frame.evaluate(
        """() => {
            const read = (id) => getComputedStyle(document.getElementById(id).shadowRoot.querySelector('.root'));
            const outer = read('outer');
            const inner = read('inner');
            return {
                outerShadow: outer.boxShadow, outerPadding: outer.paddingTop,
                innerShadow: inner.boxShadow, innerPadding: inner.paddingTop,
                innerRadius: inner.borderTopLeftRadius
            };
        }"""
    )
    assert styles["outerShadow"] != "none", styles
    assert styles["outerPadding"] == "24px", styles
    assert styles["innerShadow"] == "none", styles
    assert styles["innerPadding"] == "16px", styles
    assert styles["innerRadius"] == "8px", styles

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_grid_fixed_columns_fit_narrow_container(page, base_url):
    """
        A fixed-column mj-grid in a container narrower than its content does
        not overflow: the column tracks shrink to fit.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<div id="narrow" style="width:150px">'
        '<mj-grid id="ng" columns="3" gap="sm">'
        "<div>Alpha_long_unbreakable_word</div><div>Beta</div><div>Gamma</div>"
        "</mj-grid></div>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-grid", html=html
    )
    _wait_for_upgrade(frame, "#ng", ".root")

    result = frame.evaluate(
        """() => {
            const grid = document.querySelector('#ng');
            const root = grid.shadowRoot.querySelector('.root');
            const style = getComputedStyle(root);
            const tracks = style.gridTemplateColumns.split(' ').map(parseFloat);
            const gap = parseFloat(style.columnGap);
            let used = gap * (tracks.length - 1);
            for (const track of tracks) { used = used + track; }
            return { columns: tracks.length, usedWidth: used, hostWidth: grid.clientWidth };
        }"""
    )
    assert result["columns"] == 3
    assert result["usedWidth"] <= result["hostWidth"] + 0.5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_grid_nested_does_not_inherit_columns(page, base_url):
    """
        A grid in a cell of a three-column grid with a large gap lays out with
        its own defaults (FP-019): the outer track list, gap and alignment do
        not reach it.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-grid id="outer" columns="3" gap="xl" align-items="center">'
        '<div><mj-grid id="inner"><div>A</div><div>B</div></mj-grid></div>'
        "<div>2</div><div>3</div>"
        "</mj-grid>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-grid", html=html
    )
    _wait_for_upgrade(frame, "#inner", ".root")

    layout = frame.evaluate(
        """() => {
            const read = (id) => getComputedStyle(document.getElementById(id).shadowRoot.querySelector('.root'));
            const outer = read('outer');
            const inner = read('inner');
            return {
                outerColumns: outer.gridTemplateColumns.split(' ').length,
                innerColumns: inner.gridTemplateColumns.split(' ').length,
                innerGap: inner.columnGap,
                innerAlign: inner.alignItems
            };
        }"""
    )
    assert layout["outerColumns"] == 3, layout
    assert layout["innerColumns"] == 1, layout
    assert layout["innerGap"] == "16px", layout
    assert layout["innerAlign"] == "stretch", layout

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_stack_nested_does_not_inherit_layout(page, base_url):
    """
        A stack nested in a horizontal, centred, wrapping stack is a vertical,
        stretched stack unless it says otherwise (FP-019). The layout
        properties apply to the element they are set on: an author rule on
        the element applies, one on an ancestor does not.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        "<style>.themed { --mj-stack-gap: 40px; } mj-stack.own { --mj-stack-gap: 24px; }</style>"
        '<mj-stack id="outer" direction="horizontal" align="center" justify="end" wrap gap="lg">'
        '<mj-stack id="inner" gap="none"><b>A</b><small>B</small></mj-stack>'
        "</mj-stack>"
        '<div class="themed"><mj-stack id="ancestor-themed"><span>a</span><span>b</span></mj-stack></div>'
        '<mj-stack id="own-rule" class="own"><span>a</span><span>b</span></mj-stack>'
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-stack", html=html
    )
    _wait_for_upgrade(frame, "#own-rule", ".root")

    layout = frame.evaluate(
        """() => {
            const read = (id) => getComputedStyle(document.getElementById(id).shadowRoot.querySelector('.root'));
            const outer = read('outer');
            const inner = read('inner');
            return {
                outerDirection: outer.flexDirection,
                innerDirection: inner.flexDirection,
                innerAlign: inner.alignItems,
                innerWrap: inner.flexWrap,
                innerGap: inner.rowGap,
                ancestorThemedGap: read('ancestor-themed').rowGap,
                ownRuleGap: read('own-rule').rowGap
            };
        }"""
    )
    assert layout["outerDirection"] == "row", layout
    assert layout["innerDirection"] == "column", layout
    assert layout["innerAlign"] == "stretch", layout
    assert layout["innerWrap"] == "nowrap", layout
    assert layout["innerGap"] == "0px", layout
    assert layout["ancestorThemedGap"] == "16px", layout
    assert layout["ownRuleGap"] == "24px", layout

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_stack_align_does_not_align_text(page, base_url):
    """
        `align` is also the legacy HTML presentational attribute; it aligns the
        children of the stack but does not centre the text inside (FP-020).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-stack id="aligned" align="center"><p id="para">Some text</p></mj-stack>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-stack", html=html
    )
    _wait_for_upgrade(frame, "#aligned", ".root")

    result = frame.evaluate(
        """() => ({
            hostTextAlign: getComputedStyle(document.getElementById('aligned')).textAlign,
            paraTextAlign: getComputedStyle(document.getElementById('para')).textAlign,
            alignItems: getComputedStyle(document.getElementById('aligned').shadowRoot.querySelector('.root')).alignItems
        })"""
    )
    assert result["alignItems"] == "center", result
    assert result["hostTextAlign"] == "start", result
    assert result["paraTextAlign"] == "start", result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_disclosure_collapsed_content_not_focusable(page, base_url):
    """
        The content of a collapsed mj-disclosure is out of the tab order and
        not rendered; it becomes reachable once the panel is opened.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-disclosure id="cd" heading="Details" animated="false">'
        '<a id="cd-link" href="#more">More</a>'
        "</mj-disclosure>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-disclosure", html=html
    )
    expect(frame.locator("#cd button.trigger")).to_be_visible(timeout=10000)

    collapsed = frame.evaluate(
        """() => {
            const link = document.querySelector('#cd-link');
            link.focus();
            return { focused: document.activeElement === link, rendered: link.getClientRects().length > 0 };
        }"""
    )
    assert collapsed["focused"] is False
    assert collapsed["rendered"] is False

    frame.locator("#cd button.trigger").click()

    expanded = frame.evaluate(
        """() => {
            const link = document.querySelector('#cd-link');
            link.focus();
            return { focused: document.activeElement === link, rendered: link.getClientRects().length > 0 };
        }"""
    )
    assert expanded["focused"] is True
    assert expanded["rendered"] is True

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


_ACCORDION_KEYBOARD_HTML = (
    "<mj-accordion>"
    '<mj-disclosure id="k1" heading="One" open animated="false">'
    '<input id="k1-input" value="text">'
    '<mj-disclosure id="k1-nested" heading="Nested" animated="false"><p>Inner</p></mj-disclosure>'
    "</mj-disclosure>"
    '<mj-disclosure id="k2" heading="Two" animated="false"><p>Two</p></mj-disclosure>'
    '<mj-disclosure id="k3" heading="Three" animated="false"><p>Three</p></mj-disclosure>'
    "</mj-accordion>"
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_accordion_arrow_keys_move_between_headers(page, base_url):
    """
        ArrowDown / ArrowUp / End / Home on an accordion header move focus to
        the next / previous / last / first header of that accordion.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-accordion",
        html=_ACCORDION_KEYBOARD_HTML
    )
    # "#k1 button.trigger" would also match the trigger of the disclosure
    # nested in panel k1, so the panel's own trigger is reached through it.
    expect(frame.locator("#k2 button.trigger")).to_be_visible(timeout=10000)

    focused_panel = """() => {
        const active = document.activeElement;
        const inTrigger = active !== null && active.shadowRoot !== null &&
            active.shadowRoot.activeElement !== null &&
            active.shadowRoot.activeElement.classList.contains('trigger');
        return inTrigger ? active.id : '';
    }"""

    frame.evaluate("() => { document.querySelector('#k1').focus(); }")
    assert frame.evaluate(focused_panel) == "k1"
    page.keyboard.press("ArrowDown")
    assert frame.evaluate(focused_panel) == "k2"
    page.keyboard.press("ArrowDown")
    assert frame.evaluate(focused_panel) == "k3"
    page.keyboard.press("ArrowDown")
    assert frame.evaluate(focused_panel) == "k1"
    page.keyboard.press("ArrowUp")
    assert frame.evaluate(focused_panel) == "k3"
    page.keyboard.press("Home")
    assert frame.evaluate(focused_panel) == "k1"
    page.keyboard.press("End")
    assert frame.evaluate(focused_panel) == "k3"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_accordion_keys_in_panel_content_not_hijacked(page, base_url):
    """
        Arrow keys pressed in a form control inside an accordion panel keep
        their normal meaning: focus stays in the control.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-accordion",
        html=_ACCORDION_KEYBOARD_HTML
    )
    field = frame.locator("#k1-input")
    expect(frame.locator("#k2 button.trigger")).to_be_visible(timeout=10000)
    expect(field).to_be_visible(timeout=10000)

    field.focus()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Home")

    focused = frame.evaluate("() => document.activeElement.id")
    assert focused == "k1-input"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_accordion_nested_disclosure_keeps_parent_open(page, base_url):
    """
        Opening a disclosure nested inside an accordion panel does not close
        that panel (the single-open rule applies to direct panels only).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-accordion",
        html=_ACCORDION_KEYBOARD_HTML
    )
    nested_trigger = frame.locator("#k1-nested button.trigger")
    expect(nested_trigger).to_be_visible(timeout=10000)

    nested_trigger.click()

    state = frame.evaluate(
        """() => ({
            parent: document.querySelector('#k1').hasAttribute('open'),
            nested: document.querySelector('#k1-nested').hasAttribute('open')
        })"""
    )
    assert state["parent"] is True
    assert state["nested"] is True

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


_SPLIT_GEOMETRY_SCRIPT = """() => {
    const split = document.querySelector('mj-split-pane');
    const box = (element) => {
        const rect = element.getBoundingClientRect();
        return { left: rect.left, right: rect.right, width: rect.width };
    };
    return {
        host: box(split),
        start: box(split.shadowRoot.querySelector('[part=start-pane]')),
        separator: box(split.shadowRoot.querySelector('[part=separator]')),
        ratio: split.ratio
    };
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_pane_keeps_ratio_when_container_shrinks(page, base_url):
    """
        After a resize, mj-split-pane keeps the split as a proportion of the
        container: when the container shrinks the start pane shrinks with it
        and the separator stays inside the container.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-split-pane initial-size="50%" min="40px" style="height:8rem;width:600px">'
        '<div slot="start">Left</div><div slot="end">Right</div>'
        "</mj-split-pane>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-split-pane", html=html
    )
    expect(frame.locator("mj-split-pane [role=separator]")).to_be_visible(timeout=10000)

    frame.evaluate("() => { document.querySelector('mj-split-pane').size = 450; }")
    before = frame.evaluate(_SPLIT_GEOMETRY_SCRIPT)
    assert abs(before["start"]["width"] - 450) < 1

    frame.evaluate("() => { document.querySelector('mj-split-pane').style.width = '200px'; }")
    frame.wait_for_function(
        """() => {
            const split = document.querySelector('mj-split-pane');
            const start = split.shadowRoot.querySelector('[part=start-pane]');
            return start.getBoundingClientRect().width < 200;
        }""",
        timeout=5000,
    )
    after = frame.evaluate(_SPLIT_GEOMETRY_SCRIPT)

    assert abs(after["start"]["width"] - 150) < 2
    assert after["separator"]["right"] <= after["host"]["right"] + 0.5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_pane_pointer_drag_rtl(page, base_url):
    """
        In a right-to-left split the start pane is on the right; dragging the
        separator to the left makes the start pane larger.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-split-pane dir="rtl" initial-size="50%" style="height:8rem;width:600px">'
        '<div slot="start">Start</div><div slot="end">End</div>'
        "</mj-split-pane>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-split-pane", html=html
    )
    separator = frame.locator("mj-split-pane [role=separator]")
    expect(separator).to_be_visible(timeout=10000)

    before = frame.evaluate(_SPLIT_GEOMETRY_SCRIPT)
    assert before["start"]["left"] > before["separator"]["left"]

    box = separator.bounding_box()
    center_x = box["x"] + box["width"] / 2
    center_y = box["y"] + box["height"] / 2
    page.mouse.move(center_x, center_y)
    page.mouse.down()
    page.mouse.move(center_x - 60, center_y, steps=4)
    page.mouse.up()

    after = frame.evaluate(_SPLIT_GEOMETRY_SCRIPT)
    assert abs(after["start"]["width"] - (before["start"]["width"] + 60)) < 2

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
        The catalog example of mj-carousel has several slides (any element
        children; the example uses plain figure elements) and shows the first
        one by default.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    frame = _open_component(page, base_url, group="layout", tag="mj-carousel")

    instance = frame.locator("mj-carousel").first
    expect(instance).to_be_attached(timeout=10000)
    _wait_for_upgrade(frame, "mj-carousel", ".slides-container")

    result = frame.evaluate(
        """() => {
            const carousel = document.querySelector('mj-carousel');
            const slides = carousel.slides;
            return {
                count: slides.length,
                firstHidden: slides.length > 0 ? slides[0].getAttribute('aria-hidden') : null
            };
        }"""
    )
    assert result["count"] >= 2
    assert result["firstHidden"] == "false"

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_carousel_plain_children_are_slides(page, base_url):
    """
        mj-carousel treats plain element children as slides: each one is a
        labelled group sized to the full carousel width, only the current one
        is visible, and the picker tabs move focus with the arrow keys.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-carousel id="pc" label="Plain slides" transition="none" style="width:24rem">'
        '<div id="ps0"><p>First</p></div>'
        '<article id="ps1"><p>Second</p></article>'
        '<div id="ps2"><p>Third</p></div>'
        "</mj-carousel>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-carousel", html=html
    )
    _wait_for_upgrade(frame, "#pc", "[part=picker-item]")

    initial = frame.evaluate(
        """() => {
            const carousel = document.querySelector('mj-carousel');
            const first = document.querySelector('#ps0');
            const second = document.querySelector('#ps1');
            return {
                role: first.getAttribute('role'),
                label: first.getAttribute('aria-label'),
                firstHidden: first.getAttribute('aria-hidden'),
                secondHidden: second.getAttribute('aria-hidden'),
                secondVisibility: getComputedStyle(second).visibility,
                fullWidth: Math.abs(first.getBoundingClientRect().width - carousel.getBoundingClientRect().width) < 1
            };
        }"""
    )
    assert initial["role"] == "group"
    assert initial["label"] == "Slide 1 of 3"
    assert initial["firstHidden"] == "false"
    assert initial["secondHidden"] == "true"
    assert initial["secondVisibility"] == "hidden"
    assert initial["fullWidth"] is True

    frame.locator("mj-carousel [part=picker-item]").first.focus()
    page.keyboard.press("ArrowRight")

    after = frame.evaluate(
        """() => {
            const carousel = document.querySelector('mj-carousel');
            const tabs = Array.from(carousel.shadowRoot.querySelectorAll('[part=picker-item]'));
            return {
                index: carousel.getAttribute('current-index'),
                focusedTab: tabs.indexOf(carousel.shadowRoot.activeElement),
                tabStops: tabs.map((tab) => tab.getAttribute('tabindex')),
                secondHidden: document.querySelector('#ps1').getAttribute('aria-hidden')
            };
        }"""
    )
    assert after["index"] == "1"
    assert after["focusedTab"] == 1
    assert after["tabStops"] == ["-1", "0", "-1"]
    assert after["secondHidden"] == "false"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_carousel_rtl_chevrons_are_not_flipped(page, base_url):
    """
        In RTL the previous / next chevrons are not transformed: the glyphs
        are Bidi_Mirrored, so the text engine already points them outwards
        and a scaleX(-1) flip would turn them inwards again (FP-021).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    page.goto(base_url + "/components/layout/mj-carousel?example=rtl")
    frame = _preview_frame(page)
    _wait_for_upgrade(frame, "mj-carousel", ".prev-btn")

    result = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-carousel').shadowRoot;
            const prev = root.querySelector('.prev-btn');
            const next = root.querySelector('.next-btn');
            return {
                direction: getComputedStyle(prev).direction,
                prevOnRight: prev.getBoundingClientRect().left > next.getBoundingClientRect().left,
                transforms: Array.from(root.querySelectorAll('.chevron')).map((chevron) => getComputedStyle(chevron).transform)
            };
        }"""
    )
    assert result["direction"] == "rtl", result
    assert result["prevOnRight"] is True, result
    assert result["transforms"] == ["none", "none"], result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_feed_plain_children_are_articles(page, base_url):
    """
        mj-feed gives plain element children article semantics at first
        render (role, position, name from the item heading, a roving tab
        stop) and Page Down moves focus to the next article.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-feed id="pf" has-more="false">'
        '<article id="pa1"><h3>Alice</h3><p>First post</p></article>'
        '<div id="pa2"><h3>Bob</h3><p>Second post</p></div>'
        '<div slot="empty" id="pa-empty">Nothing</div>'
        "</mj-feed>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-feed", html=html
    )
    _wait_for_upgrade(frame, "#pf", "[role=feed]")
    expect(frame.locator("#pa1")).to_be_visible(timeout=10000)

    items = frame.evaluate(
        """() => {
            const describe = (id) => {
                const item = document.querySelector(id);
                const labelId = item.getAttribute('aria-labelledby');
                const label = labelId !== null ? document.getElementById(labelId) : null;
                return {
                    role: item.getAttribute('role'),
                    posinset: item.getAttribute('aria-posinset'),
                    setsize: item.getAttribute('aria-setsize'),
                    tabindex: item.getAttribute('tabindex'),
                    name: label !== null ? label.textContent : ''
                };
            };
            return { first: describe('#pa1'), second: describe('#pa2'),
                     emptyRole: document.querySelector('#pa-empty').getAttribute('role') };
        }"""
    )
    assert items["first"] == {"role": "article", "posinset": "1", "setsize": "2", "tabindex": "0", "name": "Alice"}
    assert items["second"] == {"role": "article", "posinset": "2", "setsize": "2", "tabindex": "-1", "name": "Bob"}
    assert items["emptyRole"] is None

    frame.locator("#pa1").focus()
    page.keyboard.press("PageDown")

    focused = frame.evaluate("() => document.activeElement.id")
    assert focused == "pa2"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_feed_role_owns_only_articles(page, base_url):
    """
        The role="feed" element of mj-feed owns only the articles (axe
        aria-required-children): the Load more button, loading indicator,
        live region, sentinel and empty state are outside it, and it carries
        aria-busy while loading. An empty feed that is not loading has no
        feed role (its empty state shows); the role returns with the first
        item. Page Down still moves between the articles.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-feed id="lf" load-mode="button">'
        '<article id="la1"><h3>One</h3><p>First</p></article>'
        '<article id="la2"><h3>Two</h3><p>Second</p></article>'
        "</mj-feed>"
        '<mj-feed id="ef" has-more="false"><p slot="empty">Nothing yet</p></mj-feed>'
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-feed", html=html
    )
    _wait_for_upgrade(frame, "#lf", "[role=feed]")
    _wait_for_upgrade(frame, "#ef", "[part=empty]")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const full = document.getElementById("lf").shadowRoot;
            const feed = full.querySelector("[role=feed]");
            const slot = feed.querySelector("slot");
            const state = {
                feedChildren: Array.from(feed.children).map((child) => child.localName),
                itemRoles: slot.assignedElements().map((item) => item.getAttribute("role")),
                foreignInside: feed.querySelectorAll(
                    "button, [aria-live], [part=empty], [part=loading-indicator], .sentinel").length,
                buttonOutside: full.querySelector("[part=load-more-button]") !== null
            };
            document.getElementById("lf").setAttribute("loading", "");
            await wait(50);
            state.busy = feed.getAttribute("aria-busy");
            document.getElementById("lf").removeAttribute("loading");

            const emptyFeed = document.getElementById("ef");
            state.emptyRole = emptyFeed.shadowRoot.querySelector("[role=feed]") !== null;
            state.emptyShown = emptyFeed.shadowRoot.querySelector("[part=empty]").hidden === false;
            const article = document.createElement("article");
            article.innerHTML = "<h3>First post</h3>";
            emptyFeed.appendChild(article);
            await wait(50);
            state.filledRole = emptyFeed.shadowRoot.querySelector("[role=feed]") !== null;
            state.filledEmptyShown = emptyFeed.shadowRoot.querySelector("[part=empty]").hidden === false;
            return state;
        }"""
    )

    assert result["feedChildren"] == ["slot"], result
    assert result["itemRoles"] == ["article", "article"], result
    assert result["foreignInside"] == 0, result
    assert result["buttonOutside"] is True, result
    assert result["busy"] == "true", result
    assert result["emptyRole"] is False and result["emptyShown"] is True, result
    assert result["filledRole"] is True and result["filledEmptyShown"] is False, result

    frame.locator("#la1").focus()
    page.keyboard.press("PageDown")
    focused = frame.evaluate("() => document.activeElement.id")
    assert focused == "la2"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_feed_takes_its_name_from_the_host(page, base_url):
    """
        The role="feed" element inside the shadow root is named by the host:
        ``aria-label`` is copied onto it, ``aria-labelledby`` is resolved in the
        host's tree and copied as text, and the name follows later changes.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-feed id="nf" aria-label="Team updates">'
        '<article><h3>One</h3></article>'
        "</mj-feed>"
        '<h2 id="nf2-title">Release notes</h2>'
        '<mj-feed id="nf2" aria-labelledby="nf2-title">'
        '<article><h3>Two</h3></article>'
        "</mj-feed>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-feed", html=html
    )
    _wait_for_upgrade(frame, "#nf", "[role=feed]")
    _wait_for_upgrade(frame, "#nf2", "[role=feed]")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const nameOf = (id) => document.getElementById(id).shadowRoot
                .querySelector("[role=feed]").getAttribute("aria-label");
            const state = { label: nameOf("nf"), labelledBy: nameOf("nf2") };
            document.getElementById("nf").setAttribute("aria-label", "All updates");
            await wait(50);
            state.changed = nameOf("nf");
            document.getElementById("nf").removeAttribute("aria-label");
            await wait(50);
            state.removed = nameOf("nf");
            return state;
        }"""
    )

    assert result["label"] == "Team updates", result
    assert result["labelledBy"] == "Release notes", result
    assert result["changed"] == "All updates", result
    assert result["removed"] is None, result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_media_object_align_does_not_align_text(page, base_url):
    """
        `align="center"` centres the media and the content on the cross axis
        but leaves the text alignment to the page (FP-020), and a nested media
        object does not inherit the outer gap, alignment or media size
        (FP-019).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-media-object id="outer" align="center" gap="xl" media-size="8rem">'
        '<span slot="media">M</span>'
        '<p id="text">Build #2481 failed on main.</p>'
        '<mj-media-object id="reply"><span slot="media">R</span>Reply</mj-media-object>'
        "</mj-media-object>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-media-object", html=html
    )
    _wait_for_upgrade(frame, "#reply", ".root")

    result = frame.evaluate(
        """() => {
            const root = (id) => document.getElementById(id).shadowRoot;
            return {
                outerAlign: getComputedStyle(root('outer').querySelector('.root')).alignItems,
                hostTextAlign: getComputedStyle(document.getElementById('outer')).textAlign,
                textAlign: getComputedStyle(document.getElementById('text')).textAlign,
                replyGap: getComputedStyle(root('reply').querySelector('.root')).columnGap,
                replyAlign: getComputedStyle(root('reply').querySelector('.root')).alignItems,
                replyMediaWidth: getComputedStyle(root('reply').querySelector('.media')).width
            };
        }"""
    )
    assert result["outerAlign"] == "center", result
    assert result["hostTextAlign"] == "start", result
    assert result["textAlign"] == "start", result
    assert result["replyGap"] == "16px", result
    assert result["replyAlign"] in ("flex-start", "flow-start", "start"), result
    assert result["replyMediaWidth"] == "48px", result

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


# Contrast helpers evaluated in the preview frame (WCAG 2 relative luminance).
# `textContrast(element)` composites the backgrounds of the element and its
# flat-tree ancestors (slots and shadow hosts included) until an opaque one,
# and returns the ratio of the element's text colour against that.
_A11Y_CONTRAST_JS = r"""
    const parseColor = (text) => {
        let match = text.match(/^rgba?\(([^)]+)\)$/);
        let channels = null;
        if (match !== null) {
            const parts = match[1].split(/[\s,\/]+/).filter((part) => part.length > 0).map(Number);
            channels = [parts[0] / 255, parts[1] / 255, parts[2] / 255, parts.length > 3 ? parts[3] : 1];
        } else {
            match = text.match(/^color\(srgb ([^)]+)\)$/);
            if (match !== null) {
                const parts = match[1].split(/[\s\/]+/).filter((part) => part.length > 0).map(Number);
                channels = [parts[0], parts[1], parts[2], parts.length > 3 ? parts[3] : 1];
            }
        }
        return channels;
    };
    const flatParent = (node) => {
        let parent = null;
        if (node.assignedSlot !== null && node.assignedSlot !== undefined) {
            parent = node.assignedSlot;
        } else if (node.parentElement !== null) {
            parent = node.parentElement;
        } else if (node.getRootNode() instanceof ShadowRoot) {
            parent = node.getRootNode().host;
        }
        return parent;
    };
    const effectiveBackground = (element) => {
        const layers = [];
        let node = element;
        while (node !== null) {
            const color = parseColor(getComputedStyle(node).backgroundColor);
            if (color !== null && color[3] > 0) {
                layers.push(color);
                if (color[3] >= 1) { break; }
            }
            node = flatParent(node);
        }
        let result = [1, 1, 1];
        for (let index = layers.length - 1; index >= 0; index = index - 1) {
            const layer = layers[index];
            result = [0, 1, 2].map((c) => layer[c] * layer[3] + result[c] * (1 - layer[3]));
        }
        return result;
    };
    const luminance = (rgb) => {
        const linear = (c) => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        return 0.2126 * linear(rgb[0]) + 0.7152 * linear(rgb[1]) + 0.0722 * linear(rgb[2]);
    };
    const contrastRatio = (first, second) => {
        const a = luminance(first);
        const b = luminance(second);
        return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    };
    const textContrast = (element) => {
        const foreground = parseColor(getComputedStyle(element).color);
        return Math.round(contrastRatio(foreground, effectiveBackground(element)) * 100) / 100;
    };
"""

# A 1x1 PNG: a background image that loads.
_HERO_PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_hero_basic_example_text_keeps_contrast_on_the_accent(page, base_url):
    """
        In the basic example the heading and the tertiary "See examples"
        button (its label set to --mj-text-on-accent through
        --mj-button-color) keep 4.5:1 on the accent background in the light
        and the dark theme (axe color-contrast).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    page.goto(base_url + "/components/layout/mj-hero?example=basic")
    frame = _preview_frame(page)
    _wait_for_upgrade(frame, "mj-hero", ".root")
    _wait_for_upgrade(frame, "mj-button.on-accent", ".label")

    result = frame.evaluate(
        """async () => {
            """ + _A11Y_CONTRAST_JS + """
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const label = document.querySelector("mj-button.on-accent").shadowRoot.querySelector(".label");
            const heading = document.querySelector("mj-hero").shadowRoot.querySelector(".heading-el");
            const measure = async (theme) => {
                document.documentElement.setAttribute("data-theme", theme);
                await wait(50);
                return { label: textContrast(label), heading: textContrast(heading) };
            };
            const light = await measure("light");
            const dark = await measure("dark");
            document.documentElement.setAttribute("data-theme", "light");
            return { light: light, dark: dark };
        }"""
    )

    for theme in ("light", "dark"):
        assert result[theme]["label"] >= 4.5, result
        assert result[theme]["heading"] >= 4.5, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_hero_text_is_light_over_the_scrim_and_scrim_goes_with_a_failed_image(page, base_url):
    """
        While the scrim shows over a background image the heading is light
        (--mj-color-neutral-0) in both themes, not --mj-text-on-accent (dark
        in the dark theme). When the image fails to load the scrim is
        removed with it: the plain colour shows and the text is
        --mj-text-on-accent again.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-hero id="photo" heading="Photo" min-height="8rem" bg-src="' + _HERO_PIXEL + '"></mj-hero>'
        '<mj-hero id="broken" heading="Broken" min-height="8rem" bg-src="/static/media/missing-hero-test.jpg"></mj-hero>'
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-hero", html=html
    )
    _wait_for_upgrade(frame, "#photo", ".root")
    _wait_for_upgrade(frame, "#broken", ".root")
    frame.wait_for_function(
        "() => document.getElementById('broken').shadowRoot.querySelector('.overlay').hidden === true",
        timeout=10000,
    )

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const describe = (id) => {
                const root = document.getElementById(id).shadowRoot;
                return {
                    scrim: root.querySelector(".overlay").hidden === false,
                    marked: root.querySelector(".root").hasAttribute("data-scrim"),
                    heading: getComputedStyle(root.querySelector(".heading-el")).color
                };
            };
            document.documentElement.setAttribute("data-theme", "dark");
            await wait(50);
            const dark = { photo: describe("photo"), broken: describe("broken") };
            document.documentElement.setAttribute("data-theme", "light");
            await wait(50);
            const light = { photo: describe("photo"), broken: describe("broken") };
            return { dark: dark, light: light };
        }"""
    )

    for theme in ("light", "dark"):
        assert result[theme]["photo"] == {"scrim": True, "marked": True, "heading": "rgb(255, 255, 255)"}, result
        assert result[theme]["broken"]["scrim"] is False and result[theme]["broken"]["marked"] is False, result
    assert result["dark"]["broken"]["heading"] == "rgb(20, 24, 31)", result
    assert result["light"]["broken"]["heading"] == "rgb(255, 255, 255)", result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_hero_video_error_reports_a_changed_source(page, base_url):
    """
        The background video element is reused when `bg-video` changes: a
        failure of the new source still fires mj-hero-bg-error with that
        source and removes the scrim.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = '<mj-hero id="clip" heading="Clip" min-height="8rem" bg-video="/static/media/missing-clip-a.mp4"></mj-hero>'
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-hero", html=html
    )
    _wait_for_upgrade(frame, "#clip", ".root")
    frame.wait_for_function(
        "() => document.getElementById('clip').shadowRoot.querySelector('.overlay').hidden === true",
        timeout=10000,
    )

    frame.evaluate(
        """() => {
            window.__heroErrors = [];
            const hero = document.getElementById("clip");
            hero.addEventListener("mj-hero-bg-error", (event) => window.__heroErrors.push(event.detail.src));
            hero.setAttribute("bg-video", "/static/media/missing-clip-b.mp4");
        }"""
    )
    frame.wait_for_function("() => window.__heroErrors.length >= 1", timeout=10000)
    result = frame.evaluate(
        """() => ({
            errors: window.__heroErrors,
            scrim: document.getElementById("clip").shadowRoot.querySelector(".overlay").hidden === false
        })"""
    )
    assert result == {"errors": ["/static/media/missing-clip-b.mp4"], "scrim": False}, result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_empty_state_description_region_removed_when_empty(page, base_url):
    """
        Without slot="description" the description region takes no room, so
        the heading and the actions are one gap apart (FP-022); slotting a
        description brings the region back.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-empty-state id="es" heading="No projects yet">'
        '<button slot="actions" type="button">Create project</button>'
        "</mj-empty-state>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-empty-state", html=html
    )
    _wait_for_upgrade(frame, "#es", ".description")

    measure = """() => {
        const root = document.getElementById('es').shadowRoot;
        const container = getComputedStyle(root.querySelector('.root'));
        const heading = root.querySelector('.heading-el').getBoundingClientRect();
        const actions = root.querySelector('.actions').getBoundingClientRect();
        return {
            descriptionDisplay: getComputedStyle(root.querySelector('.description')).display,
            gap: parseFloat(container.rowGap),
            space: Math.round(actions.top - heading.bottom)
        };
    }"""
    without = frame.evaluate(measure)
    assert without["descriptionDisplay"] == "none", without
    assert abs(without["space"] - without["gap"]) <= 1, without

    frame.evaluate(
        """() => {
            const description = document.createElement('p');
            description.slot = 'description';
            description.textContent = 'Create one to get started.';
            document.getElementById('es').appendChild(description);
        }"""
    )
    frame.wait_for_function(
        """() => getComputedStyle(document.getElementById('es').shadowRoot.querySelector('.description')).display !== 'none'""",
        timeout=5000,
    )

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


_DOCK_GEOMETRY_SCRIPT = """(ids) => {
    const result = {};
    for (const id of ids) {
        const element = document.getElementById(id);
        const rect = element.getBoundingClientRect();
        result[id] = {
            left: Math.round(rect.left), top: Math.round(rect.top),
            width: Math.round(rect.width), height: Math.round(rect.height)
        };
    }
    return result;
}"""


def _wait_for_dock_pass(frame):
    """
        Wait four animation frames: enough for the observers to notice a
        change and for the layout pass they schedule (one frame later) to run.

        :param frame: The preview Frame.
    """

    frame.evaluate(
        """() => new Promise((resolve) => {
            let frames = 0;
            const tick = () => {
                frames = frames + 1;
                if (frames >= 4) { resolve(true); } else { requestAnimationFrame(tick); }
            };
            requestAnimationFrame(tick);
        })"""
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_keeps_author_band_sizes(page, base_url):
    """
        Docked bands keep the size their author gave them (an inline height
        on a top band, an inline width on a start band) and the fill child is
        sized on both axes to exactly the rectangle that is left.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout id="ab" style="width:600px;height:240px">'
        '<div id="ab-top" dock="top" style="height:40px">top</div>'
        '<div id="ab-bottom" dock="bottom" style="height:32px">bottom</div>'
        '<div id="ab-start" dock="start" style="width:140px">start</div>'
        '<div id="ab-fill" dock="fill">fill</div>'
        "</mj-dock-layout>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    frame.wait_for_function(
        "() => document.querySelector('#ab-fill').style.position === 'absolute'",
        timeout=5000,
    )

    box = frame.evaluate(_DOCK_GEOMETRY_SCRIPT, ["ab", "ab-top", "ab-bottom", "ab-start", "ab-fill"])
    assert box["ab-top"]["height"] == 40
    assert box["ab-top"]["width"] == 600
    assert box["ab-bottom"]["height"] == 32
    assert box["ab-start"]["width"] == 140
    assert box["ab-start"]["height"] == 240 - 40 - 32
    assert box["ab-fill"]["left"] == box["ab"]["left"] + 140
    assert box["ab-fill"]["top"] == box["ab"]["top"] + 40
    assert box["ab-fill"]["width"] == 600 - 140
    assert box["ab-fill"]["height"] == 240 - 40 - 32

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_relayouts_on_child_changes(page, base_url):
    """
        The layout re-runs when a docked child changes size, when one is
        hidden, and when the dock attribute of a plain element changes; a
        child that loses its dock attribute returns to normal flow with its
        own inline styles intact.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout id="rc" style="width:500px;height:300px">'
        '<nav id="rc-nav" dock="start" style="width:150px">nav</nav>'
        '<aside id="rc-aside" dock="end" style="width:100px">aside</aside>'
        '<main id="rc-main" dock="fill">main</main>'
        "</mj-dock-layout>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    frame.wait_for_function(
        "() => document.querySelector('#rc-main').style.position === 'absolute'",
        timeout=5000,
    )
    ids = ["rc", "rc-nav", "rc-main"]

    frame.evaluate("() => { document.querySelector('#rc-nav').style.width = '60px'; }")
    _wait_for_dock_pass(frame)
    box = frame.evaluate(_DOCK_GEOMETRY_SCRIPT, ids)
    assert box["rc-main"]["left"] == box["rc"]["left"] + 60
    assert box["rc-main"]["width"] == 500 - 60 - 100

    frame.evaluate("() => { document.querySelector('#rc-aside').hidden = true; }")
    _wait_for_dock_pass(frame)
    box = frame.evaluate(_DOCK_GEOMETRY_SCRIPT, ids)
    assert box["rc-main"]["width"] == 500 - 60

    frame.evaluate("() => { document.querySelector('#rc-nav').setAttribute('dock', 'top'); }")
    _wait_for_dock_pass(frame)
    box = frame.evaluate(_DOCK_GEOMETRY_SCRIPT, ids)
    assert box["rc-nav"]["width"] == 500
    assert box["rc-main"]["top"] == box["rc"]["top"] + box["rc-nav"]["height"]

    frame.evaluate("() => { document.querySelector('#rc-nav').removeAttribute('dock'); }")
    _wait_for_dock_pass(frame)
    undocked = frame.evaluate(
        "() => document.querySelector('#rc-nav').getAttribute('style')"
    )
    assert undocked == "width: 60px;"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_nested_fill_gets_remaining_height(page, base_url):
    """
        A nested mj-dock-layout docked as fill under a toolbar gets exactly
        the remaining height, so its own bottom band stays inside the outer
        layout; a split pane docked as fill inside it fills what is left.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout id="nl" style="width:500px;height:300px">'
        '<div id="nl-toolbar" dock="top" style="height:48px">toolbar</div>'
        '<mj-dock-layout id="nl-inner" dock="fill">'
        '<div id="nl-status" dock="bottom" style="height:24px">status</div>'
        '<mj-split-pane id="nl-split" dock="fill">'
        '<div slot="start">A</div><div slot="end">B</div>'
        "</mj-split-pane>"
        "</mj-dock-layout>"
        "</mj-dock-layout>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    frame.wait_for_function(
        "() => document.querySelector('#nl-split').style.position === 'absolute'",
        timeout=5000,
    )
    _wait_for_dock_pass(frame)

    box = frame.evaluate(_DOCK_GEOMETRY_SCRIPT, ["nl", "nl-inner", "nl-status", "nl-split"])
    outer_bottom = box["nl"]["top"] + box["nl"]["height"]
    assert box["nl-inner"]["height"] == 300 - 48
    assert box["nl-status"]["top"] + box["nl-status"]["height"] == outer_bottom
    assert box["nl-split"]["height"] == 300 - 48 - 24

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_register_dock_child_reaches_layout(page, base_url):
    """
        MjElement's registerDockChild / unregisterDockChild reach the layout
        that docks the child: for a direct child (whose assigned slot is the
        layout's own shadow slot) and for content slotted into a component
        whose shadow root holds the layout with a <slot> child.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout id="rd" style="width:300px;height:160px">'
        '<mj-button id="rd-top" dock="top">Top</mj-button>'
        '<div dock="fill">fill</div>'
        "</mj-dock-layout>"
        '<x-dock-shell id="shell"><mj-button id="rd-slotted" dock="top">Slotted</mj-button></x-dock-shell>'
        '<div id="rd-loose"><mj-button id="rd-none" dock="top">Not docked by a layout</mj-button></div>'
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    _wait_for_upgrade(frame, "#rd", "slot")

    result = frame.evaluate(
        """async () => {
            if (customElements.get('x-dock-shell') === undefined) {
                customElements.define('x-dock-shell', class extends HTMLElement {
                    constructor() {
                        super();
                        this.attachShadow({ mode: 'open' }).innerHTML =
                            '<mj-dock-layout style="width:300px;height:120px"><slot></slot></mj-dock-layout>';
                    }
                });
            }
            await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            const anchoring = await import('/static/javascript/core/anchoring.js');
            const spy = (layout) => {
                const counter = { count: 0 };
                const original = layout.requestLayout.bind(layout);
                layout.requestLayout = () => { counter.count = counter.count + 1; original(); };
                return counter;
            };
            const outer = spy(document.getElementById('rd'));
            const inner = spy(document.getElementById('shell').shadowRoot.querySelector('mj-dock-layout'));
            anchoring.registerDockChild(document.getElementById('rd-top'));
            anchoring.unregisterDockChild(document.getElementById('rd-top'));
            anchoring.registerDockChild(document.getElementById('rd-slotted'));
            anchoring.registerDockChild(document.getElementById('rd-none'));
            return { outer: outer.count, inner: inner.count };
        }"""
    )
    assert result == {"outer": 2, "inner": 1}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_no_mj_layout_when_not_rendered(page, base_url):
    """
        A layout pass requested while the layout is not rendered (inside
        display:none) changes nothing and emits no mj-layout; showing the
        layout runs a pass that does.

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<div id="nr-wrap" style="display:none">'
        '<mj-dock-layout id="nr" style="width:300px;height:160px">'
        '<div id="nr-top" dock="top" style="height:30px">top</div>'
        "</mj-dock-layout>"
        "</div>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    _wait_for_upgrade(frame, "#nr", "slot")

    frame.evaluate(
        """() => {
            window.__nrEvents = 0;
            const layout = document.getElementById('nr');
            layout.addEventListener('mj-layout', () => { window.__nrEvents = window.__nrEvents + 1; });
            layout.requestLayout();
        }"""
    )
    _wait_for_dock_pass(frame)
    hidden = frame.evaluate(
        "() => ({ events: window.__nrEvents, position: document.getElementById('nr-top').style.position })"
    )
    assert hidden == {"events": 0, "position": ""}

    frame.evaluate("() => { document.getElementById('nr-wrap').style.display = 'block'; }")
    frame.wait_for_function("() => window.__nrEvents > 0", timeout=5000)
    position = frame.evaluate("() => document.getElementById('nr-top').style.position")
    assert position == "absolute"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dock_layout_disabled_keeps_pointer_for_content(page, base_url):
    """
        disabled has no meaning for the layout: its content still receives
        pointer input (the base control rule is overridden).

        :param page: The Playwright page fixture.
        :param base_url: The site base URL fixture.
    """

    html = (
        '<mj-dock-layout id="dd" disabled style="width:300px;height:120px">'
        '<button id="dd-button" dock="fill" type="button">Press</button>'
        "</mj-dock-layout>"
    )
    frame = _render_custom_html(
        page, base_url, group="layout", anchor_tag="mj-dock-layout", html=html
    )
    _wait_for_upgrade(frame, "#dd", "slot")
    frame.wait_for_function(
        "() => document.getElementById('dd-button').style.position === 'absolute'",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__ddClicks = 0;
            document.getElementById('dd-button').addEventListener('click', () => { window.__ddClicks = window.__ddClicks + 1; });
        }"""
    )

    frame.locator("#dd-button").click(timeout=5000)
    state = frame.evaluate(
        "() => ({ clicks: window.__ddClicks, pointer: getComputedStyle(document.getElementById('dd')).pointerEvents })"
    )
    assert state == {"clicks": 1, "pointer": "auto"}

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
