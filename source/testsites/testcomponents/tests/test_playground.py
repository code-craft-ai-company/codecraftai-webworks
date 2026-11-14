"""
    .. module:: testcomponents.tests.test_playground
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Every component works through its live sandbox, and the sandbox works.

    Two kinds of tests:

    The sweep over all 143 components verifies that:

      - the mj-* library loads inside the isolated preview iframe and
        registers the component's custom element,
      - the preview renders the element, it upgrades (gains a shadow root and
        renders content) and the preview reports no uncaught error,
      - editing the source and pressing Run re-renders the preview,
      - pressing Reset restores the original example.

    The sandbox tests exercise each panel of the page once: the example
    gallery and deep links, the JS pane and held inline scripts running after
    upgrade, the controls (attributes set live, HTML pane kept in sync), the
    event log, the slot inspector, the error panel, theme and direction
    switches applied without Run, the preview growing with its content, width
    presets and the drag handle, open in new tab, copy, and the chart data
    presets. They use the chart-part pages, whose docs belong to this site
    and use every field, and plain markup typed into the editors.

    The cases of the sweep are defined as individual module-level tests named
    ``<check>__<group>_<tag>`` so a broken component is reported by name.
"""

import json

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.catalogs import all_components
from testcomponents.harness.catalogs import identifier_for
from testcomponents.harness.factories import create_page
from testcomponents.harness.generation import define_page_tests


# One case per component: (identifier, (group, tag, title)).
_CASES = [
    (identifier_for(group, tag), (group, tag, title))
    for group, tag, title in all_components()
]

_READY_TIMEOUT = 20000

# True once the preview of the page's current run reported ready (library
# loaded, elements upgraded, example scripts run).
_PREVIEW_READY_JS = """() => {
    const frame = document.getElementById('pg-frame');
    const page = window.mjSandboxPage;
    return frame !== null && page !== undefined
        && frame.getAttribute('data-ready-run') === String(page.state.run);
}"""


def _preview_frame(page):
    """
        Resolve the Frame object for the playground preview iframe.

        :param page: The Playwright page.

        :returns: The Frame inside the preview iframe.
    """

    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    return frame


def _ready_preview(page):
    """
        Wait until the preview of the current run is ready and return its frame.

        :param page: The Playwright page.

        :returns: The preview Frame.
    """

    page.wait_for_function(_PREVIEW_READY_JS, timeout=_READY_TIMEOUT)
    frame = _preview_frame(page)
    return frame


def _open_component(page, base_url, group, tag):
    """
        Open a component page and wait for the library to register the
        custom element inside the preview iframe.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param group: The component group key.
        :param tag: The component tag.

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


def _run_markup(page, html, css="", script=""):
    """
        Replace the editors' content, press Run and wait for the new preview.

        :param page: The Playwright page (already on a sandbox page).
        :param html: The HTML pane content.
        :param css: The CSS pane content.
        :param script: The JS pane content.

        :returns: The ready preview Frame.
    """

    page.get_by_test_id("playground-editor").fill(html)
    page.get_by_test_id("playground-style-editor").fill(css)
    page.get_by_test_id("playground-script-editor").fill(script)
    page.get_by_test_id("playground-run").click()
    frame = _ready_preview(page)
    return frame


def _sandbox_errors(page):
    """
        Read the messages the error panel holds.

        :param page: The Playwright page.

        :returns: The list of error messages.
    """

    messages = page.evaluate("() => window.mjSandboxPage.state.errors.map(error => error.message)")
    return messages


# ---------------------------------------------------------------------------
# The sweep over every component
# ---------------------------------------------------------------------------

def _check_component_is_registered(page, base_url, group, tag, title):
    """
        The component's custom element is registered by the library.

        :param group: The component group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    frame = _open_component(page, base_url, group, tag)

    is_defined = frame.evaluate("tag => customElements.get(tag) !== undefined", tag)
    assert is_defined is True

    return


def _check_playground_renders_component(page, base_url, group, tag, title):
    """
        The playground preview renders the component, it upgrades to a live
        custom element with a populated shadow root, and the example raises no
        uncaught error or unhandled rejection.

        :param group: The component group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")
    frame = _ready_preview(page)

    instance = frame.locator(tag).first
    expect(instance).to_be_attached(timeout=10000)

    # The element upgraded: it has a shadow root with rendered content.
    upgraded = frame.evaluate(
        """tag => {
            const el = document.querySelector(tag);
            if (el === null) { return false; }
            return el.shadowRoot !== null
                && el.shadowRoot.childNodes.length > 0;
        }""",
        tag,
    )
    assert upgraded is True

    # Late errors (timers, first frames) get a moment to arrive.
    page.wait_for_timeout(300)
    errors = _sandbox_errors(page)
    assert errors == [], "The {} example reported errors: {}".format(tag, errors)

    return


def _check_playground_run_and_reset(page, base_url, group, tag, title):
    """
        Editing the playground source and pressing Run re-renders the
        preview; pressing Reset restores the original example.

        :param group: The component group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    _open_component(page, base_url, group, tag)

    editor = page.get_by_test_id("playground-editor")
    original = editor.input_value()
    assert tag in original

    marker = f"<p data-mark='pg-marker'>edited {tag}</p>"
    editor.fill(marker)
    page.get_by_test_id("playground-run").click()

    frame = _preview_frame(page)
    frame.wait_for_selector("[data-mark=pg-marker]", timeout=10000)

    page.get_by_test_id("playground-reset").click()
    assert editor.input_value() == original

    frame = _preview_frame(page)
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )

    return


define_page_tests(globals(), "test_component_is_registered",
                  _check_component_is_registered, _CASES)
define_page_tests(globals(), "test_playground_renders_component",
                  _check_playground_renders_component, _CASES)
define_page_tests(globals(), "test_playground_run_and_reset",
                  _check_playground_run_and_reset, _CASES)


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_gallery_switches_example(page, base_url):
    """
        Selecting a gallery example loads its HTML, CSS and JS into the
        editors, runs it in the preview and records it in the URL.
    """

    page.goto(base_url + "/chart-part/mj-chart-legend")
    _ready_preview(page)

    first = page.get_by_test_id("example-item-basic")
    expect(first).to_have_attribute("aria-pressed", "true")

    page.get_by_test_id("example-item-vertical").click()
    expect(page.get_by_test_id("example-item-vertical")).to_have_attribute("aria-pressed", "true")
    expect(first).to_have_attribute("aria-pressed", "false")
    expect(page).to_have_url(base_url + "/chart-part/mj-chart-legend?example=vertical")

    editor_text = page.get_by_test_id("playground-editor").input_value()
    assert 'orientation="vertical"' in editor_text
    assert ".row" in page.get_by_test_id("playground-style-editor").input_value()
    expect(page.get_by_test_id("example-description")).to_contain_text("vertical legend")

    frame = _ready_preview(page)
    orientation = frame.evaluate("() => document.querySelector('mj-chart-legend').getAttribute('orientation')")
    assert orientation == "vertical"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_gallery_deep_link_opens_example(page, base_url):
    """
        ``?example=<key>`` opens the page with that example selected; an
        unknown key falls back to the first example.
    """

    page.goto(base_url + "/chart-part/mj-chart-legend?example=color-key")
    frame = _ready_preview(page)

    expect(page.get_by_test_id("example-item-color-key")).to_have_attribute("aria-pressed", "true")
    assert 'type="pie"' in page.get_by_test_id("playground-editor").input_value()
    chart_type = frame.evaluate("() => document.querySelector('mj-chart').getAttribute('type')")
    assert chart_type == "pie"

    page.goto(base_url + "/chart-part/mj-chart-legend?example=no-such-example")
    _ready_preview(page)
    expect(page.get_by_test_id("example-item-basic")).to_have_attribute("aria-pressed", "true")

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_examples_tab_builds_its_preview_lazily(page, base_url):
    """
        The Examples tab's preview is not built until the tab is shown; its
        cards view an example there or open it in Play.
    """

    page.goto(base_url + "/chart-part/mj-chart-title")
    _ready_preview(page)

    built = page.get_by_test_id("example-frame").evaluate("frame => frame.hasAttribute('srcdoc')")
    assert built is False

    page.get_by_test_id("tab-example").click()
    expect(page.get_by_test_id("example-frame")).to_be_visible()
    built = page.get_by_test_id("example-frame").evaluate("frame => frame.hasAttribute('srcdoc')")
    assert built is True

    page.get_by_test_id("example-view-meta-title").click()
    expect(page.get_by_test_id("example-card-meta-title")).to_have_class("example-card viewing")

    page.get_by_test_id("example-open-custom-styling").click()
    expect(page.get_by_test_id("tab-play")).to_have_attribute("aria-selected", "true")
    expect(page.get_by_test_id("example-item-custom-styling")).to_have_attribute("aria-pressed", "true")
    assert "--mj-chart-title-color" in page.get_by_test_id("playground-style-editor").input_value()

    return


# ---------------------------------------------------------------------------
# Scripts run after upgrade
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_scripts_run_after_the_elements_upgrade(page, base_url):
    """
        An inline <script> in the HTML pane and the JS pane both run after the
        library has defined the elements, so methods and properties work.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    _ready_preview(page)

    html = (
        '<mj-button id="b">Save</mj-button>\n'
        "<script>document.body.dataset.inline = String("
        "document.getElementById('b') instanceof customElements.get('mj-button'))</script>"
    )
    script = (
        'const button = document.getElementById("b")\n'
        'document.body.dataset.module = String(button.shadowRoot !== null && '
        'button instanceof customElements.get("mj-button"))\n'
    )
    frame = _run_markup(page, html, script=script)

    frame.wait_for_function("() => document.body.dataset.module !== undefined", timeout=10000)
    result = frame.evaluate("() => [document.body.dataset.inline, document.body.dataset.module]")
    assert result == ["true", "true"], result
    assert _sandbox_errors(page) == []

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_scripts_do_not_wait_for_data_only_child_tags(page, base_url):
    """
        Data-only child tags the library never registers (mj-option, mj-radio,
        mj-checkbox, mj-tree-item) do not hold the scripts back: the preview
        waits only for tags the library registers, so the scripts run as soon
        as the library has loaded instead of after the 5 s define timeout.
    """

    page.goto(base_url + "/components/selection/mj-select")
    _ready_preview(page)

    html = (
        '<mj-select id="fruit" label="Fruit"><mj-option value="a">Apple</mj-option></mj-select>\n'
        '<mj-radio-group label="Size"><mj-radio value="s">Small</mj-radio></mj-radio-group>\n'
        '<mj-checkbox-group label="Extras"><mj-checkbox value="x">Extra</mj-checkbox></mj-checkbox-group>\n'
        '<mj-tree-nav label="Tree"><mj-tree-item label="Root"></mj-tree-item></mj-tree-nav>\n'
        '<mj-not-a-library-tag></mj-not-a-library-tag>'
    )
    script = 'document.body.dataset.ran = String(document.getElementById("fruit").shadowRoot !== null)\n'
    frame = _run_markup(page, html, script=script)

    assert frame.evaluate("() => document.body.dataset.ran") == "true"
    timing = frame.evaluate("() => window.mjSandbox.timing")
    held_back = timing["scripts"] - timing["library"]
    assert held_back < 1500, "The scripts waited {:.0f} ms after the library loaded.".format(held_back)
    unregistered = frame.evaluate("() => customElements.get('mj-option') === undefined")
    assert unregistered is True
    assert _sandbox_errors(page) == []

    return


# ---------------------------------------------------------------------------
# Navigation guard
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_links_and_forms_do_not_navigate_the_preview(page, base_url):
    """
        The preview is an srcdoc document that resolves URLs against the
        catalog page. A fragment link goes to the fragment inside the preview;
        any other link (also target="_top" and a link in a shadow root) and a
        form submission are cancelled and logged instead of loading a page.
    """

    page.goto(base_url + "/components/navigation/mj-link")
    _ready_preview(page)
    sandbox_url = page.url

    html = (
        '<p id="top">Top</p>\n'
        '<a id="to-section" href="#section">To the section</a>\n'
        '<a id="away" href="/charts">Away</a>\n'
        '<a id="up" href="/" target="_top">Up</a>\n'
        '<mj-link id="library-link" href="/charts">Library link</mj-link>\n'
        '<form id="search"><input name="q" value="term" aria-label="Query"><button id="go">Go</button></form>\n'
        '<form method="dialog"><button id="dialog-submit">Dialog</button></form>\n'
        '<div style="height:900px"></div>\n'
        '<h2 id="section">Section</h2>'
    )
    frame = _run_markup(page, html)
    frame.evaluate("() => { window.__sameDocument = true }")

    frame.locator("#to-section").click()
    frame.wait_for_function("() => location.hash === '#section'", timeout=5000)

    for selector in ("#away", "#up", "#library-link", "#go", "#dialog-submit"):
        frame.locator(selector).click()
    page.wait_for_timeout(300)

    assert frame.evaluate("() => window.__sameDocument") is True
    assert frame.evaluate("() => document.getElementById('section') !== null") is True
    assert page.url == sandbox_url, page.url

    page.get_by_test_id("inspector-tab-events").click()
    log = page.get_by_test_id("event-log")
    expect(log.locator('[data-event="link navigation blocked"]')).to_have_count(3)
    expect(log.locator('[data-event="form submission blocked"]')).to_have_count(1)
    expect(log.locator('[data-event="form submission blocked"]')).to_contain_text('"q":"term"')
    assert _sandbox_errors(page) == []

    return


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_controls_set_attributes_live_and_sync_the_html(page, base_url):
    """
        Changing a control sets the attribute on the first instance in the
        preview without Run and rewrites the HTML pane; clearing it removes
        the attribute from both.
    """

    page.goto(base_url + "/chart-part/mj-chart-legend")
    frame = _ready_preview(page)

    control = page.get_by_test_id("control-orientation")
    expect(control).to_be_enabled()
    control.select_option("vertical")

    orientation = frame.evaluate("() => document.querySelector('mj-chart-legend').getAttribute('orientation')")
    assert orientation == "vertical"
    editor = page.get_by_test_id("playground-editor")
    assert '<mj-chart-legend orientation="vertical">' in editor.input_value()

    page.get_by_test_id("control-orientation-clear").click()
    has_attribute = frame.evaluate("() => document.querySelector('mj-chart-legend').hasAttribute('orientation')")
    assert has_attribute is False
    assert "orientation=" not in editor.input_value()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_controls_follow_the_component(page, base_url):
    """
        The controls show the first instance's attributes after load, and
        follow an attribute the page changes itself.
    """

    page.goto(base_url + "/chart-part/mj-chart-title")
    frame = _ready_preview(page)

    expect(page.get_by_test_id("control-level")).to_have_value("2")
    expect(page.get_by_test_id("control-subtitle")).to_have_value("Thousands of euros")

    frame.evaluate("() => document.querySelector('mj-chart-title').setAttribute('level', '4')")
    expect(page.get_by_test_id("control-level")).to_have_value("4")

    page.get_by_test_id("control-text").fill("Typed title")
    text = frame.evaluate("() => document.querySelector('mj-chart-title').getAttribute('text')")
    assert text == "Typed title"
    assert 'text="Typed title"' in page.get_by_test_id("playground-editor").input_value()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_colour_control_shows_and_keeps_alpha(page, base_url):
    """
        A colour control shows the exact value next to the swatch (here a
        #rrggbbaa value the native picker cannot hold), a colour picked on the
        swatch keeps that alpha, and any CSS colour can be typed.
    """

    page.goto(base_url + "/components/feedback/mj-badge")
    _ready_preview(page)
    frame = _run_markup(page, '<mj-badge color="#0ea5e9cc">New</mj-badge>')

    text = page.get_by_test_id("control-color-text")
    swatch = page.get_by_test_id("control-color")
    expect(text).to_have_value("#0ea5e9cc")
    expect(swatch).to_have_value("#0ea5e9")

    swatch.fill("#ff0000")
    color = frame.evaluate("() => document.querySelector('mj-badge').getAttribute('color')")
    assert color == "#ff0000cc", color
    expect(text).to_have_value("#ff0000cc")

    text.fill("rebeccapurple")
    color = frame.evaluate("() => document.querySelector('mj-badge').getAttribute('color')")
    assert color == "rebeccapurple", color
    expect(swatch).to_have_value("#663399")
    assert 'color="rebeccapurple"' in page.get_by_test_id("playground-editor").input_value()

    page.get_by_test_id("control-color-clear").click()
    has_color = frame.evaluate("() => document.querySelector('mj-badge').hasAttribute('color')")
    assert has_color is False
    expect(text).to_have_value("")

    return


# ---------------------------------------------------------------------------
# Event log
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_event_log_records_events(page, base_url):
    """
        mj-* events fired in the preview are listed with their target and
        detail; mjSandbox.log adds entries; Clear empties the log.
    """

    page.goto(base_url + "/chart-part/mj-chart-legend?example=events")
    frame = _ready_preview(page)

    page.get_by_test_id("inspector-tab-events").click()
    log = page.get_by_test_id("event-log")
    expect(log.locator('[data-event="mj-chart-render"]').first).to_be_visible()

    frame.locator("mj-chart-legend").locator("button.item").first.click()

    toggle = log.locator('[data-event="mj-chart-legend-toggle"]').first
    expect(toggle).to_be_visible()
    expect(toggle).to_contain_text("mj-chart-legend#reactive-legend")
    expect(toggle).to_contain_text('"seriesIndex":0')
    expect(log.locator('[data-event="hidden series"]').first).to_contain_text("Product A")

    count_text = page.get_by_test_id("event-log-count").inner_text()
    assert count_text != "0 events"

    page.get_by_test_id("event-log-filter").fill("legend-toggle")
    expect(log.locator('[data-event="mj-chart-render"]').first).to_be_hidden()
    expect(toggle).to_be_visible()

    page.get_by_test_id("event-log-clear").click()
    expect(log.locator("[data-testid=event-log-entry]")).to_have_count(0)
    expect(page.get_by_test_id("event-log-count")).to_have_text("0 events")

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_event_log_records_bridged_change_and_input(page, base_url):
    """
        change / input events, native or dispatched by a component, are
        logged next to the mj-* events.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    _ready_preview(page)

    html = '<input id="field" aria-label="Field">\n<mj-button id="b">B</mj-button>'
    script = (
        'const button = document.getElementById("b")\n'
        'button.dispatchEvent(new CustomEvent("change", { bubbles: true, detail: { value: 7 } }))\n'
        'button.dispatchEvent(new CustomEvent("mj-custom", { detail: { ok: true } }))\n'
    )
    frame = _run_markup(page, html, script=script)
    frame.locator("#field").fill("x")

    page.get_by_test_id("inspector-tab-events").click()
    log = page.get_by_test_id("event-log")
    expect(log.locator('[data-event="change"]', has_text='"value":7')).to_have_count(1)
    expect(log.locator('[data-event="mj-custom"]').first).to_contain_text("mj-button#b")
    expect(log.locator('[data-event="input"]').first).to_contain_text("input#field")

    return


# ---------------------------------------------------------------------------
# Slot inspector
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_slot_toggle_removes_and_adds_content(page, base_url):
    """
        A slot toggle reflects whether the first instance has content for the
        slot; switching it off detaches the content, on restores it, and on
        an empty instance inserts the documented sample.
    """

    page.goto(base_url + "/chart-part/mj-chart-title")
    frame = _ready_preview(page)

    page.get_by_test_id("inspector-tab-slots").click()
    toggle = page.get_by_test_id("slot-toggle-default")
    expect(toggle).to_be_checked()

    toggle.uncheck()
    text = frame.evaluate("() => document.querySelector('mj-chart-title').textContent.trim()")
    assert text == ""

    toggle.check()
    text = frame.evaluate("() => document.querySelector('mj-chart-title').textContent.trim()")
    assert text == "Quarterly revenue by product"

    page.get_by_test_id("example-item-meta-title").click()
    _ready_preview(page)
    page.get_by_test_id("inspector-tab-slots").click()
    expect(toggle).not_to_be_checked()
    toggle.check()
    frame = _preview_frame(page)
    text = frame.evaluate("() => document.querySelector('mj-chart-title').textContent.trim()")
    assert text == "Quarterly revenue by product"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_slot_toggle_counts_component_assigned_slots_as_default_content(page, base_url):
    """
        Children a component moved to a slot of its own (mj-breadcrumb puts
        each crumb in slot="mj-crumb-N") are still default-slot content: the
        toggle shows on, switching it off detaches them, on restores them.
    """

    page.goto(base_url + "/components/navigation/mj-breadcrumb")
    _ready_preview(page)
    html = (
        '<mj-breadcrumb label="Trail"><a href="#home">Home</a>'
        '<a href="#docs">Docs</a><span>Page</span></mj-breadcrumb>'
    )
    frame = _run_markup(page, html)

    crumb_texts = """() => Array.from(document.querySelector('mj-breadcrumb').children)
        .map((child) => child.textContent.trim()).filter((text) => text !== '')"""
    slots = frame.evaluate(
        "() => Array.from(document.querySelector('mj-breadcrumb').children).map((child) => child.getAttribute('slot'))")
    assert any(slot is not None and slot.startswith("mj-crumb") for slot in slots), slots

    page.get_by_test_id("inspector-tab-slots").click()
    toggle = page.get_by_test_id("slot-toggle-default")
    expect(toggle).to_be_checked()

    toggle.uncheck()
    assert "Home" not in frame.evaluate(crumb_texts)

    toggle.check()
    assert frame.evaluate(crumb_texts)[:3] == ["Home", "Docs", "Page"]
    expect(toggle).to_be_checked()

    return


# ---------------------------------------------------------------------------
# Error panel
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_error_panel_shows_uncaught_errors_and_rejections(page, base_url):
    """
        An uncaught error and an unhandled rejection in the preview are listed
        in the error panel and counted on its tab; Run starts it empty.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    _ready_preview(page)

    script = (
        'Promise.reject(new Error("sandbox rejection"))\n'
        'setTimeout(() => { throw new Error("sandbox boom") }, 0)\n'
    )
    _run_markup(page, "<mj-button>B</mj-button>", script=script)

    page.get_by_test_id("inspector-tab-errors").click()
    entries = page.get_by_test_id("error-list").locator("[data-testid=error-entry]")
    expect(entries).to_have_count(2)
    expect(page.get_by_test_id("error-list")).to_contain_text("sandbox boom")
    expect(page.get_by_test_id("error-list")).to_contain_text("sandbox rejection")
    expect(page.get_by_test_id("inspector-tab-errors").locator(".badge")).to_have_text("2")

    _run_markup(page, "<mj-button>B</mj-button>")
    expect(entries).to_have_count(0)

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_transient_library_fetch_failure_is_retried_once(page, base_url):
    """
        When a library module fails to fetch (a transient network failure under
        load), the sandbox builds the preview again once instead of reporting
        "The component library failed to load"; the retry is noted in the
        Events panel. A failure that persists is reported after the one retry.
    """

    aborted = []

    def abort_first(route):
        if len(aborted) == 0:
            aborted.append(route.request.url)
            route.abort()
        else:
            route.continue_()

    page.route("**/static/javascript/core/registry.js", abort_first)
    page.goto(base_url + "/components/buttons/mj-button")
    frame = _ready_preview(page)

    assert len(aborted) == 1, aborted
    assert frame.evaluate("() => customElements.get('mj-button') !== undefined") is True
    assert _sandbox_errors(page) == []
    page.get_by_test_id("inspector-tab-events").click()
    expect(page.get_by_test_id("event-log").locator('[data-event="library load retried"]')).to_have_count(1)

    page.unroute("**/static/javascript/core/registry.js")
    page.route("**/static/javascript/core/registry.js", lambda route: route.abort())
    page.get_by_test_id("playground-run").click()
    _ready_preview(page)
    page.wait_for_function("() => window.mjSandboxPage.state.errors.length > 0", timeout=_READY_TIMEOUT)
    errors = _sandbox_errors(page)
    assert len(errors) == 1, errors
    assert "The component library failed to load" in errors[0], errors

    return


# ---------------------------------------------------------------------------
# Preview: theme, direction, size
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_theme_and_direction_apply_without_run(page, base_url):
    """
        The preview theme and direction switches, and the header theme
        toggle, change the preview document at once.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    frame = _ready_preview(page)
    root = frame.locator("html")

    expect(root).to_have_attribute("data-theme", "light")
    page.get_by_test_id("preview-theme-dark").click()
    expect(root).to_have_attribute("data-theme", "dark")
    page.get_by_test_id("preview-theme-os").click()
    has_theme = frame.evaluate("() => document.documentElement.hasAttribute('data-theme')")
    assert has_theme is False

    page.get_by_test_id("theme-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(root).to_have_attribute("data-theme", "dark")
    expect(page.get_by_test_id("preview-theme-dark")).to_have_attribute("aria-pressed", "true")

    page.get_by_test_id("preview-dir-rtl").click()
    expect(root).to_have_attribute("dir", "rtl")
    page.get_by_test_id("preview-dir-ltr").click()
    expect(root).to_have_attribute("dir", "ltr")

    # The choice also holds for the next run.
    page.get_by_test_id("preview-dir-rtl").click()
    page.get_by_test_id("playground-run").click()
    frame = _ready_preview(page)
    expect(frame.locator("html")).to_have_attribute("dir", "rtl")
    expect(frame.locator("html")).to_have_attribute("data-theme", "dark")

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_preview_grows_and_shrinks_with_its_content(page, base_url):
    """
        The preview takes the height of its content instead of a fixed size.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    _ready_preview(page)

    _run_markup(page, '<div id="tall" style="height:900px">tall</div>')
    page.wait_for_function(
        "() => document.getElementById('pg-frame').getBoundingClientRect().height >= 900",
        timeout=10000,
    )

    frame = _preview_frame(page)
    frame.evaluate("() => { document.getElementById('tall').style.height = '1300px' }")
    page.wait_for_function(
        "() => document.getElementById('pg-frame').getBoundingClientRect().height >= 1300",
        timeout=10000,
    )

    _run_markup(page, '<div style="height:200px">short</div>')
    page.wait_for_function(
        "() => { const h = document.getElementById('pg-frame').getBoundingClientRect().height;"
        " return h >= 200 && h < 400 }",
        timeout=10000,
    )

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_preview_grows_for_an_open_modal_dialog(page, base_url):
    """
        A modal dialog in the top layer takes no space in the document; the
        preview still grows so the whole dialog shows.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    _ready_preview(page)

    html = (
        '<dialog id="d"><div style="height:420px">A tall modal dialog</div></dialog>\n'
        '<p>Behind the dialog</p>'
    )
    _run_markup(page, html, script='document.getElementById("d").showModal()\n')
    page.wait_for_function(
        "() => document.getElementById('pg-frame').getBoundingClientRect().height >= 440",
        timeout=10000,
    )

    return


_FRAME_HEIGHT_JS = "() => document.getElementById('pg-frame').getBoundingClientRect().height"


@testbase.attach.parameter(create_page, identifier="page")
def test_preview_ignores_hidden_and_parked_fixed_panels(page, base_url):
    """
        A fixed panel hidden with visibility, or parked below the viewport by a
        transform (a closed bottom sheet), does not grow the preview; a bottom
        sheet that slides in grows it to the sheet's height and no further,
        and the preview shrinks again when the sheet slides out.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    _ready_preview(page)

    # The preview measures mj-* elements and shadow-root children for overlays,
    # so the sheets are (unregistered) mj-* elements.
    css = (
        ".sheet { display: block; position: fixed; inset-inline: 0; inset-block-end: 0; block-size: 180px;\n"
        "  background: var(--mj-surface, #fff); transform: translateY(110%); transition: transform 0.4s; }\n"
        ".sheet.open { transform: none; }\n"
        "#hidden-sheet { visibility: hidden; transform: none; }\n"
    )
    html = (
        '<p>Content behind the sheets</p>\n'
        '<mj-test-sheet class="sheet" id="hidden-sheet"></mj-test-sheet>\n'
        '<mj-test-sheet class="sheet" id="sliding-sheet"></mj-test-sheet>'
    )
    frame = _run_markup(page, html, css=css)
    page.wait_for_timeout(600)
    closed_height = page.evaluate(_FRAME_HEIGHT_JS)
    assert closed_height < 180, closed_height

    frame.evaluate("() => document.getElementById('sliding-sheet').classList.add('open')")
    page.wait_for_function("() => document.getElementById('pg-frame').getBoundingClientRect().height >= 180",
                           timeout=5000)
    page.wait_for_timeout(800)
    open_height = page.evaluate(_FRAME_HEIGHT_JS)
    assert 180 <= open_height < 400, open_height

    frame.evaluate("() => document.getElementById('sliding-sheet').classList.remove('open')")
    page.wait_for_function("() => document.getElementById('pg-frame').getBoundingClientRect().height < 180",
                           timeout=5000)

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_preview_width_presets_and_drag_handle(page, base_url):
    """
        The width presets size the preview; the drag handle resizes it.
    """

    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(base_url + "/components/buttons/mj-button")
    frame = _ready_preview(page)
    inner_width = "() => window.innerWidth"

    # A preset is the width of the preview's own viewport.
    for preset in [320, 768]:
        page.get_by_test_id(f"preview-width-{preset}").click()
        expect(page.get_by_test_id(f"preview-width-{preset}")).to_have_attribute("aria-pressed", "true")
        frame.wait_for_function(f"() => window.innerWidth === {preset}", timeout=5000)
        expect(page.get_by_test_id("preview-size")).to_contain_text(f"{preset} ×")

    page.get_by_test_id("preview-width-full").click()
    frame.wait_for_function("() => window.innerWidth > 600", timeout=5000)
    full = frame.evaluate(inner_width)

    handle = page.get_by_test_id("preview-resize-handle")
    handle_box = handle.bounding_box()
    start_x = handle_box["x"] + handle_box["width"] / 2
    start_y = handle_box["y"] + handle_box["height"] / 2
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(start_x - 200, start_y, steps=5)
    page.mouse.up()
    frame.wait_for_function(f"() => Math.abs(window.innerWidth - {full - 200}) <= 2", timeout=5000)
    expect(page.get_by_test_id("preview-width-full")).to_have_attribute("aria-pressed", "false")

    return


# ---------------------------------------------------------------------------
# Open in new tab, copy
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_open_in_new_tab_shows_the_full_page(page, base_url):
    """
        "Open in new tab" opens the current editors' content as a full page
        that loads the library and runs the example.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    _ready_preview(page)
    page.get_by_test_id("playground-editor").fill('<mj-button id="solo">Solo</mj-button>')

    with page.expect_popup() as popup_info:
        page.get_by_test_id("playground-open").click()
    popup = popup_info.value
    popup.wait_for_function("() => window.mjSandbox !== undefined && window.mjSandbox.ready === true",
                            timeout=_READY_TIMEOUT)
    upgraded = popup.evaluate(
        "() => { const b = document.getElementById('solo');"
        " return b !== null && b.shadowRoot !== null && b.shadowRoot.childNodes.length > 0 }"
    )
    assert upgraded is True
    popup.close()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_copy_puts_the_snippet_on_the_clipboard(page, base_url):
    """
        Copy puts the CSS, HTML and JS on the clipboard as one snippet.
    """

    page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=base_url)
    page.goto(base_url + "/chart-part/mj-chart-title?example=custom-styling")
    _ready_preview(page)

    page.get_by_test_id("playground-copy").click()
    expect(page.get_by_test_id("playground-copy")).to_have_attribute("data-copied", "true")
    copied = page.evaluate("() => navigator.clipboard.readText()")
    assert copied.startswith("<style>"), copied
    assert "--mj-chart-title-font-size" in copied
    assert '<mj-chart id="styled"' in copied

    return


# ---------------------------------------------------------------------------
# Chart pages
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_chart_data_presets_change_the_live_chart(page, base_url):
    """
        The data presets replace the chart's data without Run: 1,000 points,
        a single point, negative values, empty, and back to the original.
    """

    page.goto(base_url + "/chart-part/mj-chart-data-table")
    frame = _ready_preview(page)

    read_shape = (
        "() => { const c = document.querySelector('mj-chart'); const d = c.data;"
        " if (d === null || d === undefined) { return null }"
        " return [d.categories.length, d.series[0].values.length,"
        " Math.min(...d.series[0].values.filter(v => typeof v === 'number'))] }"
    )

    page.get_by_test_id("chart-preset-large").click()
    shape = frame.evaluate(read_shape)
    assert shape[0] == 1000 and shape[1] == 1000, shape
    frame.wait_for_function("() => document.querySelector('mj-chart').shadowRoot.querySelector('svg') !== null")

    page.get_by_test_id("chart-preset-single").click()
    assert frame.evaluate(read_shape)[0:2] == [1, 1]

    page.get_by_test_id("chart-preset-negative").click()
    assert frame.evaluate(read_shape)[2] < 0

    page.get_by_test_id("chart-preset-empty").click()
    assert frame.evaluate(read_shape)[0:2] == [0, 0]

    page.get_by_test_id("chart-preset-original").click()
    assert frame.evaluate(read_shape) is None
    assert _sandbox_errors(page) == []

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_type_page_shows_description_and_controls(page, base_url):
    """
        A chart-type page shows the type's description and offers controls
        that set attributes on the first <mj-chart>.
    """

    from testcomponents.charttypes import chart_type_for

    doc = chart_type_for("bar")
    page.goto(base_url + "/chart-type/bar")
    frame = _ready_preview(page)

    description = page.get_by_test_id("chart-type-description")
    expect(description).to_be_visible()
    expect(description).to_contain_text(doc.description[:40])

    page.get_by_test_id("control-label").fill("Relabelled chart")
    label = frame.evaluate("() => document.querySelector('mj-chart').getAttribute('label')")
    assert label == "Relabelled chart"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_page_data_is_safe_json(page, base_url):
    """
        The page data the sandbox reads parses back to the examples, even
        though example markup contains script tags.
    """

    page.goto(base_url + "/chart-part/mj-chart-data-table")
    _ready_preview(page)

    data = page.evaluate("() => JSON.parse(document.getElementById('sandbox-data').textContent)")
    keys = [example["key"] for example in data["examples"]]
    assert keys == ["basic", "nested", "live-data"], json.dumps(keys)
    assert "<script" in data["examples"][0]["html"]

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
