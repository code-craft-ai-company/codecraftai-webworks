"""
    test_pages.py

    Parametrized Playwright tests asserting that every component test page
    is complete: it documents the component (description, how-to), shows
    example code, and provides the interactive playground.

    These run once per catalogued component (139 cases).
"""

import pytest
from playwright.sync_api import expect

from conftest import all_components


_COMPONENTS = all_components()

# Build readable test ids: "group/tag".
_PARAMS = [
    pytest.param(group, tag, title, id=f"{group}/{tag}")
    for group, tag, title in _COMPONENTS
]


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_component_page_has_documentation(page, base_url, group, tag, title):
    """
        Each component page shows its title, description, and how-to text.

        :param group: The component's group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")

    heading = page.get_by_test_id("component-heading")
    expect(heading).to_be_visible()
    expect(heading).to_contain_text(title)

    description = page.get_by_test_id("component-description")
    expect(description).to_be_visible()
    assert len(description.inner_text().strip()) > 0

    howto = page.get_by_test_id("component-howto")
    expect(howto).to_be_visible()
    assert len(howto.inner_text().strip()) > 0

    return


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_component_page_has_example_code(page, base_url, group, tag, title):
    """
        Each component page carries the example code in the Play tab's
        editable HTML editor.

        :param group: The component's group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")

    editor = page.get_by_test_id("playground-editor")
    expect(editor).to_be_visible()

    example_text = editor.input_value()
    assert tag in example_text

    return


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_component_page_has_demo_tabs(page, base_url, group, tag, title):
    """
        Each component page has the Example / Play tabbed demo section
        with the Play tab selected by default.

        :param group: The component's group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")

    example_tab = page.get_by_test_id("tab-example")
    play_tab = page.get_by_test_id("tab-play")
    expect(example_tab).to_be_visible()
    expect(play_tab).to_be_visible()

    # Play is selected by default so the sandbox controls are usable.
    expect(play_tab).to_have_attribute("aria-selected", "true")
    expect(example_tab).to_have_attribute("aria-selected", "false")
    expect(page.get_by_test_id("panel-play")).to_be_visible()

    # Switching to the Example tab reveals the read-only scenario.
    example_tab.click()
    expect(example_tab).to_have_attribute("aria-selected", "true")
    expect(page.get_by_test_id("panel-example")).to_be_visible()
    expect(page.get_by_test_id("example-frame")).to_be_visible()

    return


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_component_page_has_playground(page, base_url, group, tag, title):
    """
        Each component page provides the editable Play sandbox with an
        HTML editor, a Style editor, run/reset controls, and a preview.

        :param group: The component's group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")

    editor = page.get_by_test_id("playground-editor")
    expect(editor).to_be_visible()
    assert len(editor.input_value().strip()) > 0

    expect(page.get_by_test_id("playground-style-editor")).to_be_visible()
    expect(page.get_by_test_id("playground-run")).to_be_visible()
    expect(page.get_by_test_id("playground-reset")).to_be_visible()
    expect(page.get_by_test_id("playground-preview")).to_be_visible()

    return


@pytest.mark.parametrize("group, tag, title", _PARAMS)
def test_playground_controls_visible_without_scroll(page, base_url, group, tag, title):
    """
        The demo controls (tabs, Run, Reset) and the component preview are
        within the viewport on load, so no scrolling is needed to operate
        the sandbox -- including while the suite runs.

        :param group: The component's group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")

    viewport = page.viewport_size
    height = viewport["height"]

    # Tabs and Run/Reset must be fully within the viewport.
    for testid in ["tab-example", "tab-play", "playground-run", "playground-reset"]:
        box = page.get_by_test_id(testid).bounding_box()
        assert box is not None, testid
        assert box["y"] >= 0, testid
        assert box["y"] + box["height"] <= height + 1, testid

    # The preview and the top of the HTML editor must also be on screen.
    for testid in ["playground-preview", "playground-editor"]:
        box = page.get_by_test_id(testid).bounding_box()
        assert box is not None, testid
        assert 0 <= box["y"] < height, testid

    return
