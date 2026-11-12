"""
    .. module:: testcomponents.tests.test_pages
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Every component test page is complete.

    Tests asserting that every component sandbox page is complete: it documents
    the component (description, how-to, reference tables), shows the example
    code, and provides the sandbox (gallery, editors, preview, inspector).

    Three checks run once per catalogued component (143 cases each): the
    documentation and reference, the Examples / Play tabs, and the sandbox
    (example code, panels, and the controls within the viewport on load). The cases are
    defined as individual module-level tests named
    ``<check>__<group>_<tag>`` so a broken page is reported by component. The
    page-level behaviour of the sandbox itself (gallery switching, controls,
    events, slots, errors, theme and direction) is tested in
    :mod:`testcomponents.tests.test_playground`.
"""

from testcomponents.catalog import BY_TAG
from testcomponents.harness.browsers import expect
from testcomponents.harness.catalogs import all_components
from testcomponents.harness.catalogs import identifier_for
from testcomponents.harness.generation import define_page_tests


# One case per component: (identifier, (group, tag, title)).
_CASES = [
    (identifier_for(group, tag), (group, tag, title))
    for group, tag, title in all_components()
]


def _check_component_page_has_documentation(page, base_url, group, tag, title):
    """
        Each component page shows its title, description, and how-to text;
        the description is shown in full (no height cap that clips it); and
        the reference tables and attribute controls match the doc.

        :param group: The component's group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")

    heading = page.get_by_test_id("component-heading")
    expect(heading).to_be_visible()
    expect(heading).to_contain_text(title)

    expect(page.get_by_test_id("component-summary")).to_be_visible()

    description = page.get_by_test_id("component-description")
    expect(description).to_be_visible()
    assert len(description.inner_text().strip()) > 0

    clipped = description.evaluate("element => element.scrollHeight > element.clientHeight + 1")
    assert clipped is False, "The description of {} is clipped.".format(tag)

    howto = page.get_by_test_id("component-howto")
    expect(howto).to_be_visible()
    assert len(howto.inner_text().strip()) > 0

    # A reference table for every documented field that has rows, and one
    # control per documented attribute.
    doc = BY_TAG[tag]
    tables = [
        ("attributes-table", len(doc.attributes)),
        ("properties-table", len(doc.properties)),
        ("methods-table", len(doc.methods)),
        ("events-table", len(doc.events)),
        ("slots-table", len(doc.slots)),
        ("parts-table", len(doc.parts)),
        ("css-properties-table", len(doc.css_properties)),
    ]
    for testid, rows in tables:
        table = page.get_by_test_id(testid)
        if rows == 0:
            expect(table).to_have_count(0)
        else:
            expect(table.locator("tbody tr")).to_have_count(rows)

    controls = page.get_by_test_id("controls-list").locator(".control-row")
    expect(controls).to_have_count(len(doc.attributes))

    return


def _check_component_page_has_demo_tabs(page, base_url, group, tag, title):
    """
        Each component page has the Examples / Play tabbed demo section
        with the Play tab selected by default; the Examples tab lists every
        gallery example and builds its own preview of the selected one.

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

    # Switching to the Examples tab reveals the gallery and its preview.
    example_tab.click()
    expect(example_tab).to_have_attribute("aria-selected", "true")
    expect(page.get_by_test_id("panel-example")).to_be_visible()
    example_frame = page.get_by_test_id("example-frame")
    expect(example_frame).to_be_visible()

    doc = BY_TAG[tag]
    cards = page.get_by_test_id("example-cards").locator("[data-example-card]")
    expect(cards).to_have_count(len(doc.gallery))

    # The preview document is built on demand for the selected example; that
    # the library runs in it is covered by the playground sweep (same builder).
    srcdoc = example_frame.get_attribute("srcdoc")
    assert srcdoc is not None, "The Examples tab built no preview for {}.".format(tag)
    assert "<" + tag in srcdoc, "The Examples preview of {} lacks the example.".format(tag)

    return


def _check_component_page_has_playground(page, base_url, group, tag, title):
    """
        Each component page provides the sandbox: the gallery, HTML / CSS /
        JS editors (the HTML one holding the example), Run / Reset / open /
        copy, the preview with its width, theme and direction switches, and
        the inspector. The demo controls (tabs, Run, Reset) and the top of
        the preview are within the viewport on load, so the sandbox can be
        operated without scrolling.

        :param group: The component's group key.
        :param tag: The component tag.
        :param title: The component title.
    """

    page.goto(base_url + f"/components/{group}/{tag}")

    editor = page.get_by_test_id("playground-editor")
    expect(editor).to_be_visible()
    example_text = editor.input_value()
    assert tag in example_text, "The HTML pane of {} does not hold the example.".format(tag)

    for testid in [
        "playground-style-editor", "playground-script-editor",
        "playground-run", "playground-reset", "playground-open", "playground-copy",
        "playground-preview", "example-gallery", "preview-widths", "preview-themes",
        "preview-dirs", "preview-resize-handle", "inspector", "controls-panel",
    ]:
        expect(page.get_by_test_id(testid)).to_be_visible()

    viewport = page.viewport_size
    height = viewport["height"]

    # Tabs and Run/Reset must be fully within the viewport.
    for testid in ["tab-example", "tab-play", "playground-run", "playground-reset"]:
        box = page.get_by_test_id(testid).bounding_box()
        assert box is not None, testid
        assert box["y"] >= 0, testid
        assert box["y"] + box["height"] <= height + 1, testid

    # The preview starts on screen; the editors follow it (the preview grows
    # with its content, so they may be below the fold).
    box = page.get_by_test_id("playground-preview").bounding_box()
    assert box is not None
    assert 0 <= box["y"] < height

    return


define_page_tests(globals(), "test_component_page_has_documentation",
                  _check_component_page_has_documentation, _CASES)
define_page_tests(globals(), "test_component_page_has_demo_tabs",
                  _check_component_page_has_demo_tabs, _CASES)
define_page_tests(globals(), "test_component_page_has_playground",
                  _check_component_page_has_playground, _CASES)


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
