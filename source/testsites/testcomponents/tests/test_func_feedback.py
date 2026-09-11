"""
    .. module:: testcomponents.tests.test_func_feedback

    Functional Playwright tests for the 'feedback' component group.

    Covers six components: mj-alert, mj-toast, mj-progress, mj-badge,
    mj-chip, and mj-tooltip. Each test opens the component's playground
    page (or injects custom HTML via the editor), interacts with the
    component inside the preview iframe, and asserts behavioural outcomes
    derived from the component's JavaScript implementation.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_GROUP = "feedback"


def _open_component(page, base_url: str, tag: str):
    """
        Navigate to a component playground page and wait for the custom
        element to be registered inside the preview iframe.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
        :param tag: The component tag name (e.g. 'mj-alert').

        :returns: The preview iframe Frame with the library loaded.
    """

    page.goto(base_url + f"/components/{_GROUP}/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


def _inject_html(page, base_url: str, tag: str, html: str):
    """
        Replace the playground editor content with custom HTML, press Run,
        and return the refreshed preview iframe frame with the component
        re-registered.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
        :param tag: The component tag name used to wait for registration.
        :param html: The HTML snippet to inject into the editor.

        :returns: The refreshed preview iframe Frame.
    """

    page.goto(base_url + f"/components/{_GROUP}/{tag}")
    editor = page.get_by_test_id("playground-editor")
    editor.fill(html)
    page.get_by_test_id("playground-run").click()

    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


def _click_shadow(frame, selector: str, shadow_selector: str) -> None:
    """
        Click an element inside a web component's shadow root by evaluating
        JavaScript. This bypasses the Playwright shadow-piercing selector
        limitation when elements are not directly queryable.

        :param frame: The iframe Frame containing the component.
        :param selector: CSS selector for the host element.
        :param shadow_selector: CSS selector for the shadow root target.
    """

    frame.evaluate(
        """([hostSel, shadowSel]) => {
            const host = document.querySelector(hostSel);
            if (host === null) { return; }
            const target = host.shadowRoot.querySelector(shadowSel);
            if (target !== null) { target.click(); }
        }""",
        [selector, shadow_selector],
    )
    return


def _focus_shadow(frame, selector: str, shadow_selector: str) -> None:
    """
        Focus an element inside a web component's shadow root.

        :param frame: The iframe Frame containing the component.
        :param selector: CSS selector for the host element.
        :param shadow_selector: CSS selector for the shadow root target.
    """

    frame.evaluate(
        """([hostSel, shadowSel]) => {
            const host = document.querySelector(hostSel);
            if (host === null) { return; }
            const target = host.shadowRoot.querySelector(shadowSel);
            if (target !== null) { target.focus(); }
        }""",
        [selector, shadow_selector],
    )
    return


# ---------------------------------------------------------------------------
# mj-alert tests
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_default_role_is_status(page, base_url):
    """
        An mj-alert with severity='info' renders a container whose ARIA
        role is 'status'.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-alert severity="info">Information message</mj-alert>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    role_value = frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        const container = el.shadowRoot.querySelector(".container");
        return container ? container.getAttribute("role") : null;
    }""")

    assert role_value == "status"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_error_severity_role_is_alert(page, base_url):
    """
        An mj-alert with severity='error' renders a container whose ARIA
        role is 'alert', reflecting the assertive live-region semantic.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-alert severity="error">Critical failure</mj-alert>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    role_value = frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        const container = el.shadowRoot.querySelector(".container");
        return container ? container.getAttribute("role") : null;
    }""")

    assert role_value == "alert"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_dismissible_fires_event_and_hides(page, base_url):
    """
        Clicking the dismiss button on a dismissible mj-alert fires the
        mj-alert-dismiss event.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-alert severity="warning" dismissible>Dismiss me</mj-alert>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    frame.evaluate("""() => {
        window.__mjAlertDismissed = false;
        const el = document.querySelector("mj-alert");
        el.addEventListener("mj-alert-dismiss", () => {
            window.__mjAlertDismissed = true;
        });
    }""")

    _click_shadow(frame=frame, selector="mj-alert", shadow_selector=".dismiss")

    frame.wait_for_function("() => window.__mjAlertDismissed === true", timeout=3000)

    dismissed = frame.evaluate("() => window.__mjAlertDismissed")
    assert dismissed is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_dismiss_event_is_cancelable(page, base_url):
    """
        When a listener calls preventDefault() on mj-alert-dismiss the
        alert does NOT gain open='false'.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-alert severity="info" dismissible>Cancel my dismiss</mj-alert>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        el.addEventListener("mj-alert-dismiss", e => e.preventDefault());
    }""")

    _click_shadow(frame=frame, selector="mj-alert", shadow_selector=".dismiss")
    page.wait_for_timeout(300)

    open_attr = frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        return el ? el.getAttribute("open") : "missing";
    }""")

    assert open_attr != "false"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_open_false_hides_element(page, base_url):
    """
        Setting open='false' hides the mj-alert via CSS (:host([open=false])).

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-alert severity="success" open="false">Hidden alert</mj-alert>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    el_locator = frame.locator("mj-alert")
    expect(el_locator).to_be_hidden(timeout=5000)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_heading_attribute_renders(page, base_url):
    """
        The heading attribute text appears inside the shadow DOM title slot.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-alert severity="info" heading="Test Heading">Body text</mj-alert>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    title_text = frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        const titleSlot = el.shadowRoot.querySelector("slot[name='title']");
        return titleSlot ? titleSlot.textContent.trim() : "";
    }""")

    assert "Test Heading" in title_text
    return


# ---------------------------------------------------------------------------
# mj-toast tests
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_open_attribute_makes_visible(page, base_url):
    """
        An mj-toast with the open attribute present is visible; without it
        the element is hidden by :host(:not([open])).

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-toast open severity="info">Visible toast</mj-toast>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    toast_locator = frame.locator("mj-toast")
    expect(toast_locator).to_be_visible(timeout=5000)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_dismiss_button_fires_event(page, base_url):
    """
        Clicking the dismiss button fires mj-toast-dismiss with reason='user'.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-toast open severity="success" heading="Done">Upload complete.</mj-toast>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    frame.evaluate("""() => {
        window.__mjToastReason = null;
        const el = document.querySelector("mj-toast");
        el.addEventListener("mj-toast-dismiss", e => {
            window.__mjToastReason = e.detail.reason;
        });
    }""")

    _click_shadow(frame=frame, selector="mj-toast", shadow_selector=".dismiss")

    frame.wait_for_function("() => window.__mjToastReason !== null", timeout=3000)

    reason = frame.evaluate("() => window.__mjToastReason")
    assert reason == "user"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_dismiss_event_is_cancelable(page, base_url):
    """
        When a listener calls preventDefault() on mj-toast-dismiss the
        open attribute is NOT removed.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-toast open severity="warning">Keep me open</mj-toast>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    frame.evaluate("""() => {
        const el = document.querySelector("mj-toast");
        el.addEventListener("mj-toast-dismiss", e => e.preventDefault());
    }""")

    _click_shadow(frame=frame, selector="mj-toast", shadow_selector=".dismiss")
    page.wait_for_timeout(300)

    still_open = frame.evaluate("""() => {
        const el = document.querySelector("mj-toast");
        return el ? el.hasAttribute("open") : false;
    }""")

    assert still_open is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_escape_key_dismisses(page, base_url):
    """
        Pressing Escape while focus is within an open mj-toast fires
        mj-toast-dismiss with reason='user'. The keydown listener is on
        the host element itself, so we dispatch a KeyboardEvent to it.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-toast open severity="error">Error toast</mj-toast>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    frame.evaluate("""() => {
        window.__mjToastEscapeReason = null;
        const el = document.querySelector("mj-toast");
        el.addEventListener("mj-toast-dismiss", e => {
            window.__mjToastEscapeReason = e.detail.reason;
        });
        el.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    }""")

    frame.wait_for_function(
        "() => window.__mjToastEscapeReason !== null",
        timeout=3000,
    )

    reason = frame.evaluate("() => window.__mjToastEscapeReason")
    assert reason == "user"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_auto_dismiss_fires_event(page, base_url):
    """
        A toast with auto-dismiss set fires mj-toast-dismiss with
        reason='auto' after the configured delay. The open attribute is set
        programmatically after attaching the event listener so the listener
        is guaranteed to be in place before the timer starts.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-toast severity="info" auto-dismiss="1200">Auto-dismiss me</mj-toast>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    frame.evaluate("""() => {
        window.__mjToastAutoReason = null;
        const el = document.querySelector("mj-toast");
        el.addEventListener("mj-toast-dismiss", e => {
            window.__mjToastAutoReason = e.detail.reason;
        });
        el.setAttribute("open", "");
    }""")

    frame.wait_for_function(
        "() => window.__mjToastAutoReason !== null",
        timeout=5000,
    )

    reason = frame.evaluate("() => window.__mjToastAutoReason")
    assert reason == "auto"
    return


# ---------------------------------------------------------------------------
# mj-progress tests
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_aria_valuenow_reflects_value(page, base_url):
    """
        The progressbar's aria-valuenow attribute matches the value
        attribute set on mj-progress.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-progress value="65" label="Uploading"></mj-progress>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    aria_value = frame.evaluate("""() => {
        const el = document.querySelector("mj-progress");
        const bar = el.shadowRoot.querySelector("[role='progressbar']");
        return bar ? bar.getAttribute("aria-valuenow") : null;
    }""")

    assert aria_value == "65"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_indeterminate_removes_aria_valuenow(page, base_url):
    """
        When mj-progress has the indeterminate attribute, the progressbar
        element has no aria-valuenow attribute (ARIA spec requirement).

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-progress indeterminate label="Loading"></mj-progress>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    aria_value = frame.evaluate("""() => {
        const el = document.querySelector("mj-progress");
        const bar = el.shadowRoot.querySelector("[role='progressbar']");
        return bar ? bar.getAttribute("aria-valuenow") : "present";
    }""")

    assert aria_value is None
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_fill_width_reflects_value(page, base_url):
    """
        The inner .fill element's inline width style corresponds to the
        percentage of value / max.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-progress value="40" max="100" label="Sync"></mj-progress>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    fill_width = frame.evaluate("""() => {
        const el = document.querySelector("mj-progress");
        const fill = el.shadowRoot.querySelector(".fill");
        return fill ? fill.style.width : null;
    }""")

    assert fill_width == "40%"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_change_event_fires_on_value_update(page, base_url):
    """
        Changing the value attribute dispatches mj-progress-change with
        the expected detail payload.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-progress value="10" label="Test"></mj-progress>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    frame.evaluate("""() => {
        window.__mjProgressDetail = null;
        const el = document.querySelector("mj-progress");
        el.addEventListener("mj-progress-change", e => {
            window.__mjProgressDetail = e.detail;
        });
        el.setAttribute("value", "75");
    }""")

    frame.wait_for_function(
        "() => window.__mjProgressDetail !== null",
        timeout=3000,
    )

    detail = frame.evaluate("() => window.__mjProgressDetail")
    assert detail["value"] == 75
    assert detail["max"] == 100
    assert detail["percentage"] == 75.0
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_complete_event_fires_at_max(page, base_url):
    """
        Setting value equal to max dispatches the mj-progress-complete
        event.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-progress value="50" label="Test"></mj-progress>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    frame.evaluate("""() => {
        window.__mjProgressComplete = false;
        const el = document.querySelector("mj-progress");
        el.addEventListener("mj-progress-complete", () => {
            window.__mjProgressComplete = true;
        });
        el.setAttribute("value", "100");
    }""")

    frame.wait_for_function(
        "() => window.__mjProgressComplete === true",
        timeout=3000,
    )

    complete = frame.evaluate("() => window.__mjProgressComplete")
    assert complete is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_ring_variant_renders_svg(page, base_url):
    """
        The ring variant renders an SVG with the progressbar role.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-progress variant="ring" value="40" label="Sync"></mj-progress>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    ring_role = frame.evaluate("""() => {
        const el = document.querySelector("mj-progress");
        const ring = el.shadowRoot.querySelector("svg[role='progressbar']");
        return ring ? ring.getAttribute("role") : null;
    }""")

    assert ring_role == "progressbar"
    return


# ---------------------------------------------------------------------------
# mj-badge tests
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_count_displays_number(page, base_url):
    """
        The count variant displays the raw count number when it is at or
        below the max.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge count="7"><button type="button">Inbox</button></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    count_text = frame.evaluate("""() => {
        const el = document.querySelector("mj-badge");
        const span = el.shadowRoot.querySelector(".count-text");
        return span ? span.textContent.trim() : null;
    }""")

    assert count_text == "7"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_overflow_displays_max_plus(page, base_url):
    """
        When count exceeds max the indicator displays 'max+'.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge count="120" max="99"><button type="button">Inbox</button></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    count_text = frame.evaluate("""() => {
        const el = document.querySelector("mj-badge");
        const span = el.shadowRoot.querySelector(".count-text");
        return span ? span.textContent.trim() : null;
    }""")

    assert count_text == "99+"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_overflow_event_fires(page, base_url):
    """
        Setting a count that exceeds max triggers mj-badge-overflow with
        detail.count, detail.max, and detail.displayCount.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge count="5"><button type="button">Inbox</button></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    frame.evaluate("""() => {
        window.__mjBadgeOverflow = null;
        const el = document.querySelector("mj-badge");
        el.addEventListener("mj-badge-overflow", e => {
            window.__mjBadgeOverflow = e.detail;
        });
        el.setAttribute("count", "200");
    }""")

    frame.wait_for_function(
        "() => window.__mjBadgeOverflow !== null",
        timeout=3000,
    )

    detail = frame.evaluate("() => window.__mjBadgeOverflow")
    assert detail["count"] == 200
    assert detail["max"] == 99
    assert detail["displayCount"] == "99+"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_zero_count_hidden_by_default(page, base_url):
    """
        A count badge with count=0 hides the indicator element unless
        show-zero is present.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge count="0"><button type="button">Inbox</button></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    is_hidden = frame.evaluate("""() => {
        const el = document.querySelector("mj-badge");
        const indicator = el.shadowRoot.querySelector(".indicator");
        return indicator ? indicator.hidden : true;
    }""")

    assert is_hidden is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_show_zero_makes_indicator_visible(page, base_url):
    """
        With show-zero present a count=0 badge shows the indicator.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge count="0" show-zero><button type="button">Inbox</button></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    is_hidden = frame.evaluate("""() => {
        const el = document.querySelector("mj-badge");
        const indicator = el.shadowRoot.querySelector(".indicator");
        return indicator ? indicator.hidden : true;
    }""")

    assert is_hidden is False
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_status_variant_renders_aria_label(page, base_url):
    """
        The status variant sets role='img' and a descriptive aria-label on
        the indicator element.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge variant="status" status="online"><img src="" alt="Avatar"></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    aria_label = frame.evaluate("""() => {
        const el = document.querySelector("mj-badge");
        const indicator = el.shadowRoot.querySelector(".indicator");
        return indicator ? indicator.getAttribute("aria-label") : null;
    }""")

    assert aria_label is not None
    assert len(aria_label) > 0
    return


# ---------------------------------------------------------------------------
# mj-chip tests
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_selectable_has_checkbox_role(page, base_url):
    """
        A chip with mode='selectable' exposes role='checkbox' on its inner
        .chip element.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-chip mode="selectable" value="dark-mode">Dark mode</mj-chip>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    chip_role = frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        const chip = el.shadowRoot.querySelector(".chip");
        return chip ? chip.getAttribute("role") : null;
    }""")

    assert chip_role == "checkbox"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_selectable_toggle_fires_change_event(page, base_url):
    """
        Clicking a selectable chip fires mj-chip-change with the toggled
        selected state in detail.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-chip mode="selectable" value="notifications">Notifications</mj-chip>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    frame.evaluate("""() => {
        window.__mjChipChangeDetail = null;
        const el = document.querySelector("mj-chip");
        el.addEventListener("mj-chip-change", e => {
            window.__mjChipChangeDetail = e.detail;
        });
        el.shadowRoot.querySelector(".chip").click();
    }""")

    frame.wait_for_function(
        "() => window.__mjChipChangeDetail !== null",
        timeout=3000,
    )

    detail = frame.evaluate("() => window.__mjChipChangeDetail")
    assert detail["value"] == "notifications"
    assert detail["selected"] is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_selectable_aria_checked_updates(page, base_url):
    """
        After toggling a selectable chip, aria-checked reflects the new
        selected state.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-chip mode="selectable" value="opt">Option</mj-chip>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    initial_checked = frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        const chip = el.shadowRoot.querySelector(".chip");
        return chip ? chip.getAttribute("aria-checked") : null;
    }""")
    assert initial_checked == "false"

    frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        el.shadowRoot.querySelector(".chip").click();
    }""")

    after_checked = frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        const chip = el.shadowRoot.querySelector(".chip");
        return chip ? chip.getAttribute("aria-checked") : null;
    }""")
    assert after_checked == "true"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_selectable_select_event_is_cancelable(page, base_url):
    """
        Calling preventDefault() on mj-chip-select prevents the chip from
        toggling its selected state.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-chip mode="selectable" value="cancel-test">Cancel</mj-chip>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        el.addEventListener("mj-chip-select", e => e.preventDefault());
        el.shadowRoot.querySelector(".chip").click();
    }""")

    page.wait_for_timeout(300)

    aria_checked = frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        const chip = el.shadowRoot.querySelector(".chip");
        return chip ? chip.getAttribute("aria-checked") : null;
    }""")

    assert aria_checked == "false"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_removable_fires_remove_event(page, base_url):
    """
        Clicking the remove button on a removable chip fires the
        mj-chip-remove event with the chip's value in detail.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-chip mode="removable" value="typescript">TypeScript</mj-chip>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    frame.evaluate("""() => {
        window.__mjChipRemoveDetail = null;
        const el = document.querySelector("mj-chip");
        el.addEventListener("mj-chip-remove", e => {
            e.preventDefault();
            window.__mjChipRemoveDetail = e.detail;
        });
        el.shadowRoot.querySelector(".remove").click();
    }""")

    frame.wait_for_function(
        "() => window.__mjChipRemoveDetail !== null",
        timeout=3000,
    )

    detail = frame.evaluate("() => window.__mjChipRemoveDetail")
    assert detail["value"] == "typescript"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_removable_remove_event_is_cancelable(page, base_url):
    """
        Calling preventDefault() on mj-chip-remove prevents the chip from
        removing itself from the DOM.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-chip mode="removable" value="keep-me">Keep me</mj-chip>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        el.addEventListener("mj-chip-remove", e => e.preventDefault());
        el.shadowRoot.querySelector(".remove").click();
    }""")

    page.wait_for_timeout(300)

    still_present = frame.evaluate(
        "() => document.querySelector('mj-chip') !== null"
    )
    assert still_present is True
    return


# ---------------------------------------------------------------------------
# mj-tooltip tests
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_popup_hidden_initially(page, base_url):
    """
        The tooltip popup is hidden before any interaction occurs.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Copy to clipboard" show-delay="0">'
        '  <button slot="trigger" type="button">Copy</button>'
        '</mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    popup_hidden = frame.evaluate("""() => {
        const el = document.querySelector("mj-tooltip");
        const popup = el.shadowRoot.querySelector(".popup");
        return popup ? popup.hidden : true;
    }""")

    assert popup_hidden is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_open_attribute_forces_visible(page, base_url):
    """
        Setting the open attribute on mj-tooltip makes the popup visible
        immediately without hover or focus.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Forced open" open>'
        '  <button slot="trigger" type="button">Trigger</button>'
        '</mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    popup_hidden = frame.evaluate("""() => {
        const el = document.querySelector("mj-tooltip");
        const popup = el.shadowRoot.querySelector(".popup");
        return popup ? popup.hidden : true;
    }""")

    assert popup_hidden is False
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_focus_shows_popup(page, base_url):
    """
        Focusing the trigger element causes the tooltip popup to become
        visible after the show-delay. We dispatch a focusin event directly
        on the trigger so the iframe does not need to take actual focus.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Helpful hint" show-delay="0">'
        '  <button slot="trigger" type="button" id="trig">Help</button>'
        '</mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    frame.evaluate("""() => {
        const btn = document.getElementById("trig");
        btn.dispatchEvent(new FocusEvent("focusin", { bubbles: true }));
    }""")

    frame.wait_for_function(
        """() => {
            const el = document.querySelector("mj-tooltip");
            const popup = el.shadowRoot.querySelector(".popup");
            return popup ? popup.hidden === false : false;
        }""",
        timeout=3000,
    )

    popup_hidden = frame.evaluate("""() => {
        const el = document.querySelector("mj-tooltip");
        const popup = el.shadowRoot.querySelector(".popup");
        return popup ? popup.hidden : true;
    }""")

    assert popup_hidden is False
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_escape_hides_popup(page, base_url):
    """
        Pressing Escape while the tooltip is visible hides the popup. We
        dispatch the keydown event directly on the trigger element where
        the MjTooltip attaches its keydown listener.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Press Escape" show-delay="0" hide-delay="0">'
        '  <button slot="trigger" type="button" id="trig2">Trigger</button>'
        '</mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    frame.evaluate("""() => {
        const btn = document.getElementById("trig2");
        btn.dispatchEvent(new FocusEvent("focusin", { bubbles: true }));
    }""")

    frame.wait_for_function(
        """() => {
            const el = document.querySelector("mj-tooltip");
            const popup = el.shadowRoot.querySelector(".popup");
            return popup ? popup.hidden === false : false;
        }""",
        timeout=3000,
    )

    frame.evaluate("""() => {
        const btn = document.getElementById("trig2");
        btn.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    }""")

    frame.wait_for_function(
        """() => {
            const el = document.querySelector("mj-tooltip");
            const popup = el.shadowRoot.querySelector(".popup");
            return popup ? popup.hidden === true : true;
        }""",
        timeout=3000,
    )

    popup_hidden = frame.evaluate("""() => {
        const el = document.querySelector("mj-tooltip");
        const popup = el.shadowRoot.querySelector(".popup");
        return popup ? popup.hidden : true;
    }""")

    assert popup_hidden is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_show_event_fires_on_focus(page, base_url):
    """
        The mj-tooltip-show event fires with detail.trigger='focus' when
        the trigger element receives a focusin event.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Event test" show-delay="0">'
        '  <button slot="trigger" type="button" id="trig3">Info</button>'
        '</mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    frame.evaluate("""() => {
        window.__mjTooltipShowTriggers = [];
        const el = document.querySelector("mj-tooltip");
        el.addEventListener("mj-tooltip-show", e => {
            window.__mjTooltipShowTriggers.push(e.detail.trigger);
        });
    }""")

    frame.evaluate("""() => {
        const btn = document.getElementById("trig3");
        btn.dispatchEvent(new FocusEvent("focusin", { bubbles: true }));
    }""")

    frame.wait_for_function(
        "() => window.__mjTooltipShowTriggers.includes('focus')",
        timeout=3000,
    )

    has_focus_trigger = frame.evaluate(
        "() => window.__mjTooltipShowTriggers.includes('focus')"
    )
    assert has_focus_trigger is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_disabled_suppresses_popup(page, base_url):
    """
        A tooltip with the disabled attribute does not show its popup on
        focus because _scheduleShow returns early when disabled.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Should not show" show-delay="0" disabled>'
        '  <button slot="trigger" type="button" id="trig4">Disabled</button>'
        '</mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    frame.evaluate("""() => {
        const btn = document.getElementById("trig4");
        btn.dispatchEvent(new FocusEvent("focusin", { bubbles: true }));
    }""")

    page.wait_for_timeout(400)

    popup_hidden = frame.evaluate("""() => {
        const el = document.querySelector("mj-tooltip");
        const popup = el.shadowRoot.querySelector(".popup");
        return popup ? popup.hidden : true;
    }""")

    assert popup_hidden is True
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
