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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_custom_properties_override_severity_colours(page, base_url):
    """
        --mj-alert-bg / -border-color / -icon-color set on the host override
        the severity colours (they used to be reassigned on the inner
        container, so a host-level value never applied), and an alert
        without them keeps its severity colours.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-alert id="custom" severity="warning" variant="callout" '
        'style="--mj-alert-bg: rgb(1, 2, 3); --mj-alert-border-color: rgb(4, 5, 6); '
        '--mj-alert-icon-color: rgb(7, 8, 9)">Custom colours</mj-alert>'
        '<mj-alert id="plain" severity="error">Severity colours</mj-alert>'
        '<div id="probe" style="background: var(--mj-color-danger-surface); '
        'color: var(--mj-color-danger)"></div>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    result = frame.evaluate("""() => {
        const read = (id) => {
            const root = document.getElementById(id).shadowRoot;
            const container = getComputedStyle(root.querySelector('.container'));
            return { bg: container.backgroundColor, stripe: container.borderInlineStartColor,
                     icon: getComputedStyle(root.querySelector('.icon')).color };
        };
        const probe = getComputedStyle(document.getElementById('probe'));
        return { custom: read('custom'), plain: read('plain'),
                 dangerSurface: probe.backgroundColor, danger: probe.color };
    }""")

    assert result["custom"]["bg"] == "rgb(1, 2, 3)", result
    assert result["custom"]["stripe"] == "rgb(4, 5, 6)", result
    assert result["custom"]["icon"] == "rgb(7, 8, 9)", result
    assert result["plain"]["bg"] == result["dangerSurface"], result
    assert result["plain"]["icon"] == result["danger"], result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_heading_is_text_not_markup(page, base_url):
    """
        A heading that contains markup (correctly attribute-escaped by the
        server) is shown as text and never parsed into elements.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-alert heading="&lt;img src=&quot;data:,x&quot; '
        'onerror=&quot;top.__alertHits=1&quot;&gt;">Body</mj-alert>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)
    frame.wait_for_timeout(200)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        const slot = el.shadowRoot.querySelector("slot[name='title']");
        return {
            images: el.shadowRoot.querySelectorAll("img").length,
            text: slot.textContent,
            hits: top.__alertHits === undefined ? null : top.__alertHits,
        };
    }""")

    assert result["images"] == 0
    assert result["text"].startswith("<img")
    assert result["hits"] is None
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_removing_open_reopens(page, base_url):
    """
        Removing open="false" shows the alert and emits mj-alert-open (not
        mj-alert-close); an alert without a heading or actions hides those
        wrappers; the banner variant is a named region.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-alert variant="banner" open="false">Maintenance tonight</mj-alert>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        const events = [];
        el.addEventListener("mj-alert-open", () => events.push("open"));
        el.addEventListener("mj-alert-close", () => events.push("close"));
        el.removeAttribute("open");
        const region = el.shadowRoot.querySelector(".region");
        return {
            events: events,
            display: getComputedStyle(el).display,
            titleHidden: el.shadowRoot.querySelector(".title").hidden,
            actionsHidden: el.shadowRoot.querySelector(".actions").hidden,
            role: region.getAttribute("role"),
            name: region.getAttribute("aria-label"),
        };
    }""")

    assert result["events"] == ["open"]
    assert result["display"] == "block"
    assert result["titleHidden"] is True
    assert result["actionsHidden"] is True
    assert result["role"] == "region"
    assert result["name"] == "Info"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_alert_dismiss_moves_focus(page, base_url):
    """
        Dismissing a focused alert moves focus to the next focusable element
        instead of dropping it to the document body.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-alert dismissible severity="warning">Heads up</mj-alert>'
        '<button id="next">Next</button>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-alert", html=html)

    focused = frame.evaluate("""() => {
        const el = document.querySelector("mj-alert");
        const dismiss = el.shadowRoot.querySelector(".dismiss");
        dismiss.focus();
        dismiss.click();
        return document.activeElement ? document.activeElement.id : null;
    }""")

    assert focused == "next"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_open_in_markup_auto_dismisses(page, base_url):
    """
        A toast that has open and auto-dismiss in its markup starts its
        timer without errors and dismisses itself with reason "auto".

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    html = '<mj-toast open auto-dismiss="1000" severity="info">Saved</mj-toast>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    frame.evaluate("""() => {
        window.__toastReason = null;
        document.querySelector("mj-toast").addEventListener("mj-toast-dismiss", (event) => {
            window.__toastReason = event.detail.reason;
        });
    }""")
    frame.wait_for_function("() => window.__toastReason !== null", timeout=4000)

    reason = frame.evaluate("() => window.__toastReason")
    assert reason == "auto"
    assert errors == []
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_hiding_cancels_auto_dismiss(page, base_url):
    """
        Removing open before the timeout cancels the auto-dismiss: no
        mj-toast-dismiss fires and the element is not removed.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-toast open auto-dismiss="1000">Temporary</mj-toast>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    frame.evaluate("""() => {
        window.__toastDismissed = false;
        const el = document.querySelector("mj-toast");
        el.addEventListener("mj-toast-dismiss", () => { window.__toastDismissed = true; });
        el.open = false;
    }""")
    page.wait_for_timeout(1400)

    result = frame.evaluate("""() => ({
        dismissed: window.__toastDismissed,
        connected: document.querySelector("mj-toast") !== null,
    })""")
    assert result == {"dismissed": False, "connected": True}
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toast_action_event_and_standalone_overlay(page, base_url):
    """
        Activating a slotted action emits mj-toast-action with its value and
        dismisses the toast; a toast outside mj-toast-region is a fixed
        overlay; the heading is rendered as text.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-toast open heading="&lt;b&gt;Deleted&lt;/b&gt;">One item removed'
        '<button slot="actions" value="undo">Undo</button></mj-toast>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-toast", html=html)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-toast");
        const events = [];
        el.addEventListener("mj-toast-action", (event) => events.push("action:" + event.detail.action));
        el.addEventListener("mj-toast-dismiss", (event) => events.push("dismiss:" + event.detail.reason));
        const position = getComputedStyle(el).position;
        const bold = el.shadowRoot.querySelectorAll("b").length;
        el.querySelector("button").click();
        return { events: events, position: position, bold: bold };
    }""")

    assert result["events"] == ["action:undo", "dismiss:user"]
    assert result["position"] == "fixed"
    assert result["bold"] == 0
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_default_bar_fills_container(page, base_url):
    """
        A bar without a variant attribute is a block that spans its
        container, and show-value renders the percentage.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<div style="width: 400px"><mj-progress value="65" label="Upload" show-value></mj-progress></div>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-progress");
        return {
            width: Math.round(el.shadowRoot.querySelector(".track").getBoundingClientRect().width),
            value: el.shadowRoot.querySelector(".value-default").textContent,
        };
    }""")

    assert result["width"] == 400
    assert result["value"] == "65%"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_label_is_escaped(page, base_url):
    """
        A label containing quotes and markup stays one aria-label value and
        is not parsed into elements.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-progress value="10" '
        'label="a&quot;&gt;&lt;img src=&quot;data:,x&quot; onerror=&quot;top.__progressHits=1&quot;&gt;">'
        "</mj-progress>"
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)
    frame.wait_for_timeout(200)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-progress");
        const bar = el.shadowRoot.querySelector("[role='progressbar']");
        return {
            images: el.shadowRoot.querySelectorAll("img").length,
            name: bar.getAttribute("aria-label"),
            hits: top.__progressHits === undefined ? null : top.__progressHits,
        };
    }""")

    assert result["images"] == 0
    assert result["name"].startswith('a"><img')
    assert result["hits"] is None
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_progress_variant_switch_and_indeterminate_reset(page, base_url):
    """
        Changing variant after render rebuilds the shape; entering
        indeterminate clears the inline width and the stale aria-valuetext.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-progress value="40" label="Files" value-text="4 of 10 files"></mj-progress>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-progress", html=html)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-progress");
        const fill = el.shadowRoot.querySelector(".fill");
        const bar = el.shadowRoot.querySelector("[role='progressbar']");
        const before = { width: fill.style.width, text: bar.getAttribute("aria-valuetext") };
        el.setAttribute("indeterminate", "");
        const indeterminate = { width: fill.style.width, text: bar.getAttribute("aria-valuetext") };
        el.removeAttribute("indeterminate");
        el.setAttribute("variant", "ring");
        return {
            before: before,
            indeterminate: indeterminate,
            ring: el.shadowRoot.querySelector("svg.ring-svg") !== null,
        };
    }""")

    assert result["before"] == {"width": "40%", "text": "4 of 10 files"}
    assert result["indeterminate"] == {"width": "", "text": None}
    assert result["ring"] is True
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_count_has_text_alternative(page, base_url):
    """
        A count badge exposes the count (and its label) as visually hidden
        text, offers getAriaLabel(), and leaves the standard hidden property
        working.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge count="7" label="unread messages"><button>Inbox</button></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-badge");
        el.hidden = true;
        const hiddenWorks = el.hasAttribute("hidden") && el.hidden === true;
        el.hidden = false;
        return {
            text: el.shadowRoot.querySelector(".sr-text").textContent,
            helper: el.getAriaLabel("Inbox"),
            hiddenWorks: hiddenWorks,
            indicatorHidden: el.indicatorHidden,
        };
    }""")

    assert result["text"] == "7 unread messages"
    assert result["helper"] == "Inbox, 7 unread messages"
    assert result["hiddenWorks"] is True
    assert result["indicatorHidden"] is False
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_badge_color_override_is_cleared(page, base_url):
    """
        Removing color, or switching from status to count, removes the inline
        background override so the stylesheet colour applies again.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-badge variant="status" status="online" color="gold"><span>U</span></mj-badge>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-badge", html=html)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-badge");
        const indicator = el.shadowRoot.querySelector(".indicator");
        const withColor = indicator.style.getPropertyValue("--mj-badge-bg");
        el.removeAttribute("color");
        const statusColor = indicator.style.getPropertyValue("--mj-badge-bg");
        el.setAttribute("variant", "count");
        el.setAttribute("count", "2");
        return { withColor: withColor, statusColor: statusColor, countColor: indicator.style.getPropertyValue("--mj-badge-bg") };
    }""")

    assert result["withColor"] == "gold"
    assert result["statusColor"] == "var(--mj-color-success)"
    assert result["countColor"] == ""
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
def test_mj_chip_click_method_toggles_selectable_chip(page, base_url):
    """
        click() on the host toggles a selectable chip as a user click would
        (it used to dispatch a click at the host only, which did nothing);
        static and disabled chips ignore it.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-chip id="pick" mode="selectable" value="a">Pick</mj-chip>'
        '<mj-chip id="plain" value="b">Plain</mj-chip>'
        '<mj-chip id="off" mode="selectable" value="c" disabled>Off</mj-chip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    result = frame.evaluate("""() => {
        const seen = [];
        for (const id of ['pick', 'plain', 'off']) {
            const chip = document.getElementById(id);
            chip.addEventListener('mj-chip-change', (event) => seen.push(id + ':' + event.detail.selected));
            chip.click();
        }
        return { seen: seen, pick: document.getElementById('pick').selected,
                 off: document.getElementById('off').selected };
    }""")

    assert result["seen"] == ["pick:true"], result
    assert result["pick"] is True, result
    assert result["off"] is False, result
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_disabled_ignores_keyboard(page, base_url):
    """
        A disabled selectable chip is not a tab stop and Space/Enter do not
        toggle it.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = '<mj-chip mode="selectable" disabled value="f">Filter</mj-chip>'
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-chip");
        const chip = el.shadowRoot.querySelector(".chip");
        let selects = 0;
        el.addEventListener("mj-chip-select", () => { selects = selects + 1; });
        for (const key of [" ", "Enter"]) {
            chip.dispatchEvent(new KeyboardEvent("keydown", { key: key, bubbles: true, composed: true, cancelable: true }));
        }
        return { selects: selects, selected: el.selected, tabindex: chip.getAttribute("tabindex") };
    }""")

    assert result == {"selects": 0, "selected": False, "tabindex": "-1"}
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_chip_remove_key_fires_once_and_moves_focus(page, base_url):
    """
        Backspace on a remove button asks for removal once even when vetoed;
        after an accepted removal focus moves to the next chip. The remove
        button's name follows label text changes.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-chip id="a" mode="removable">TypeScript</mj-chip>'
        '<mj-chip id="b" mode="removable">Rust</mj-chip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-chip", html=html)

    frame.evaluate("""() => {
        const chip = document.getElementById("a");
        chip.textContent = "JavaScript";
    }""")
    frame.wait_for_timeout(50)

    result = frame.evaluate("""() => {
        const chip = document.getElementById("a");
        const remove = chip.shadowRoot.querySelector(".remove");
        const name = remove.getAttribute("aria-label");
        let requests = 0;
        const veto = (event) => { requests = requests + 1; event.preventDefault(); };
        chip.addEventListener("mj-chip-remove", veto);
        remove.focus();
        remove.dispatchEvent(new KeyboardEvent("keydown", { key: "Backspace", bubbles: true, composed: true, cancelable: true }));
        chip.removeEventListener("mj-chip-remove", veto);
        remove.dispatchEvent(new KeyboardEvent("keydown", { key: "Delete", bubbles: true, composed: true, cancelable: true }));
        return {
            name: name,
            requests: requests,
            removed: document.getElementById("a") === null,
            focused: document.activeElement ? document.activeElement.id : null,
        };
    }""")

    assert result == {"name": "Remove JavaScript", "requests": 1, "removed": True, "focused": "b"}
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_show_fires_once_without_recursion(page, base_url):
    """
        Showing the tooltip emits exactly one mj-tooltip-show and raises no
        error (the open attribute used to re-enter _show until the stack
        overflowed); hiding emits exactly one mj-tooltip-hide.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    html = (
        '<mj-tooltip content="Save the file" show-delay="0">'
        '<button slot="trigger">Save</button></mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    frame.evaluate("""() => {
        window.__tooltipEvents = [];
        const el = document.querySelector("mj-tooltip");
        el.addEventListener("mj-tooltip-show", () => window.__tooltipEvents.push("show"));
        el.addEventListener("mj-tooltip-hide", () => window.__tooltipEvents.push("hide"));
        el.querySelector("button").dispatchEvent(new FocusEvent("focusin", { bubbles: true }));
    }""")
    frame.wait_for_function("() => window.__tooltipEvents.length > 0", timeout=3000)
    frame.wait_for_timeout(100)
    frame.evaluate("() => { document.querySelector('mj-tooltip').open = false; }")

    events = frame.evaluate("() => window.__tooltipEvents")
    assert events == ["show", "hide"]
    assert errors == []
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_description_reaches_trigger(page, base_url):
    """
        The trigger's aria-describedby resolves to a light-DOM node in the
        same tree that holds the tooltip text.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Delete permanently">'
        '<button slot="trigger" aria-label="Delete">X</button></mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    text = frame.evaluate("""() => {
        const trigger = document.querySelector("mj-tooltip button");
        const ids = (trigger.getAttribute("aria-describedby") || "").split(" ");
        const node = document.getElementById(ids[ids.length - 1]);
        return node ? node.textContent : null;
    }""")

    assert text == "Delete permanently"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_content_shown_despite_whitespace(page, base_url):
    """
        Whitespace around the slotted trigger is not tooltip content: the
        popup shows the `content` text (it used to be slot fallback content,
        which the whitespace text node suppressed, leaving an empty popup),
        and slotted rich content still replaces it.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip id="plain" content="Copy to clipboard" open>\n'
        '  <button slot="trigger" type="button">Copy</button>\n'
        '</mj-tooltip>\n'
        '<mj-tooltip id="rich" content="Unused text" open>\n'
        '  <button slot="trigger" type="button">Help</button>\n'
        '  <strong>Rich</strong> content\n'
        '</mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)
    frame.wait_for_function(
        "() => document.getElementById('plain').shadowRoot.querySelector('.popup').hidden === false"
    )

    result = frame.evaluate("""() => {
        const read = (id) => {
            const root = document.getElementById(id).shadowRoot;
            const text = root.querySelector('.content-text');
            return { shown: text.checkVisibility(), text: text.textContent,
                     popupWidth: root.querySelector('.popup').getBoundingClientRect().width };
        };
        return { plain: read('plain'), rich: read('rich') };
    }""")

    assert result["plain"]["shown"] is True, result
    assert result["plain"]["text"] == "Copy to clipboard", result
    assert result["plain"]["popupWidth"] > 40, result
    assert result["rich"]["shown"] is False, result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_disabled_keeps_trigger_clickable(page, base_url):
    """
        A disabled tooltip does not block clicks on its trigger.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-tooltip content="Hint" disabled>'
        '<button slot="trigger" onclick="window.__tooltipClicked = true">Go</button></mj-tooltip>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    frame.locator("mj-tooltip button").click(timeout=3000)
    clicked = frame.evaluate("() => window.__tooltipClicked === true")
    assert clicked is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_escape_anywhere_and_right_placement(page, base_url):
    """
        placement="right" puts the popup to the right of the trigger, and
        Escape pressed while focus is elsewhere dismisses a hover-opened
        tooltip.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<div style="padding: 80px 200px">'
        '<mj-tooltip content="Right hint" placement="right" show-delay="0">'
        '<button slot="trigger">Hover</button></mj-tooltip></div>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    frame.evaluate("""() => {
        document.querySelector("mj-tooltip button").dispatchEvent(new PointerEvent("pointerenter"));
    }""")
    frame.wait_for_function("""() => {
        const popup = document.querySelector("mj-tooltip").shadowRoot.querySelector(".popup");
        return popup.hidden === false;
    }""", timeout=3000)

    result = frame.evaluate("""() => {
        const el = document.querySelector("mj-tooltip");
        const popup = el.shadowRoot.querySelector(".popup");
        const trigger = el.querySelector("button");
        const toRight = popup.getBoundingClientRect().left >= trigger.getBoundingClientRect().right;
        document.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        return { toRight: toRight, hiddenAfterEscape: popup.hidden };
    }""")

    assert result == {"toRight": True, "hiddenAfterEscape": True}
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tooltip_escape_in_dialog_closes_only_the_tooltip(page, base_url):
    """
        Inside an open mj-dialog, the first Escape dismisses the open tooltip
        and leaves the dialog open; the next Escape closes the dialog.

        :param page: The Playwright page object.
        :param base_url: The site base URL.
    """

    html = (
        '<mj-dialog id="dlg" label="Settings">'
        '<mj-tooltip id="tip" content="Hint" show-delay="0"><button slot="trigger">Hover</button></mj-tooltip>'
        '</mj-dialog>'
    )
    frame = _inject_html(page=page, base_url=base_url, tag="mj-tooltip", html=html)

    result = frame.evaluate("""async () => {
        const wait = (ms) => new Promise(r => setTimeout(r, ms));
        const dialog = document.getElementById("dlg");
        const tip = document.getElementById("tip");
        const trigger = tip.querySelector("button");
        const escape = () => trigger.dispatchEvent(new KeyboardEvent("keydown",
            { key: "Escape", bubbles: true, composed: true, cancelable: true }));
        dialog.setAttribute("open", "");
        await wait(300);
        trigger.focus();
        tip.setAttribute("open", "");
        await wait(200);
        const popup = tip.shadowRoot.querySelector(".popup");
        const shown = popup.hidden === false;
        escape();
        await wait(200);
        const first = { tooltipHidden: popup.hidden, dialogOpen: dialog.hasAttribute("open") };
        escape();
        await wait(200);
        return { shown: shown, first: first, dialogOpenAfterSecond: dialog.hasAttribute("open") };
    }""")

    assert result == {
        "shown": True,
        "first": {"tooltipHidden": True, "dialogOpen": True},
        "dialogOpenAfterSecond": False,
    }
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
