"""
    test_playground.py

    Parametrized Playwright tests that exercise every component through
    its live playground. For all 139 components these verify that:

      - the mj-* library loads inside the isolated preview iframe and
        registers the component's custom element,
      - the playground preview renders the element,
      - the element upgrades (gains a shadow root and renders content),
      - editing the source and pressing Run re-renders the preview,
      - pressing Reset restores the original example.

    The preview is an isolated <iframe>, so modal components (which make
    their host document inert) cannot disable the playground controls,
    and example <script> blocks execute to populate data-driven widgets.

    This is the broad functional sweep that touches every component; the
    per-group test_func_*.py modules add deeper interaction tests.
"""

import pytest
from playwright.sync_api import expect

from conftest import all_components


_PARAMS = [
    pytest.param(group, tag, title, id=f"{group}/{tag}")
    for group, tag, title in all_components()
]


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


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_component_is_registered(page, base_url, group, tag, title):
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


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_playground_renders_component(page, base_url, group, tag, title):
    """
        The playground preview renders the component and it upgrades to a
        live custom element with a populated shadow root.

        :param group: The component group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    frame = _open_component(page, base_url, group, tag)

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

    return


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_playground_run_and_reset(page, base_url, group, tag, title):
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
