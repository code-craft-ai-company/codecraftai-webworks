"""
    .. module:: testcomponents.tests.test_func_data

    Functional Playwright tests for the 'data' component group.

    Covers all ten data components:
      mj-table, mj-data-table, mj-tree-grid, mj-list, mj-virtual-list,
      mj-kanban, mj-calendar, mj-master-detail, mj-column-picker,
      mj-bulk-action-bar.

    Each test is independent and navigates to the component's playground
    page fresh.  The component renders inside a preview iframe and is
    populated AFTER the custom element is registered by calling the
    component's JS property setters via ``frame.evaluate``.

    IMPORTANT: The playground iframe uses ``<script type="module">`` to
    load the component library.  The inline example ``<script>`` runs
    synchronously during HTML parsing — BEFORE the module resolves and
    registers the custom element.  At that point the element is still a
    plain HTMLElement, so ``.columns = [...]`` creates an *own property*
    that shadows the class accessor after upgrade.  Tests therefore
    re-set all data properties after the element is upgraded to ensure
    the class setters run and ``afterRender`` internals are used.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open(page, base_url: str, tag: str):
    """
        Navigate to the playground for ``tag`` and return the preview frame
        after the custom element is registered and its shadow root exists.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param tag: The component tag name, e.g. ``'mj-table'``.

        :returns: The Frame object for the playground preview iframe.
    """

    page.goto(base_url + f"/components/data/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    # Wait for the custom element class to be registered
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    # Wait until the element in the DOM is fully upgraded (has a shadow root)
    frame.wait_for_function(
        """tag => {
            const el = document.querySelector(tag);
            return el !== null && el.shadowRoot !== null;
        }""",
        arg=tag,
        timeout=10000,
    )
    return frame


def _inject(frame, js: str):
    """
        Execute ``js`` in the frame and wait a short moment for any
        microtask-driven re-renders to settle.

        :param frame: The Playwright Frame.
        :param js: JavaScript expression to evaluate.

        :returns: The result of the evaluated JavaScript.
    """

    result = frame.evaluate(js)
    return result


# ===========================================================================
# mj-table
# ===========================================================================

_TABLE_SETUP = """() => {
    const el = document.querySelector('mj-table');
    // Delete own property set before upgrade so prototype setter is used
    delete el.columns;
    delete el.rows;
    el.columns = [
        { key: 'name',     label: 'Fruit'    },
        { key: 'color',    label: 'Color'    },
        { key: 'calories', label: 'Cal/100g' }
    ];
    el.rows = [
        { name: 'Apple',  color: 'Red',    calories: 52 },
        { name: 'Banana', color: 'Yellow', calories: 89 },
        { name: 'Mango',  color: 'Orange', calories: 60 }
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_table_renders_header_cells(page, base_url):
    """
        After data is pushed through the class setters the thead contains
        one ``<th>`` per column.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-table")
    _inject(frame, _TABLE_SETUP)
    frame.wait_for_function(
        "() => { const el = document.querySelector('mj-table'); "
        "return el.shadowRoot.querySelectorAll('thead th').length === 3; }",
        timeout=5000,
    )
    count = frame.evaluate(
        "() => document.querySelector('mj-table').shadowRoot"
        ".querySelectorAll('thead th').length"
    )
    assert count == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_table_renders_data_rows(page, base_url):
    """
        After the class setters run the tbody has one row per data record.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-table")
    _inject(frame, _TABLE_SETUP)
    frame.wait_for_function(
        "() => { const el = document.querySelector('mj-table'); "
        "return el.shadowRoot.querySelectorAll('tbody tr:not(.empty-row)').length === 3; }",
        timeout=5000,
    )
    row_count = frame.evaluate(
        "() => document.querySelector('mj-table').shadowRoot"
        ".querySelectorAll('tbody tr:not(.empty-row)').length"
    )
    assert row_count == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_table_cell_text_matches_data(page, base_url):
    """
        The first body cell of the first row contains the first fruit name.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-table")
    _inject(frame, _TABLE_SETUP)
    frame.wait_for_function(
        "() => { const el = document.querySelector('mj-table'); "
        "const rows = el.shadowRoot.querySelectorAll('tbody tr:not(.empty-row)'); "
        "return rows.length > 0 && rows[0].cells[0].textContent.trim().length > 0; }",
        timeout=5000,
    )
    first_cell = frame.evaluate(
        "() => { const el = document.querySelector('mj-table'); "
        "const rows = el.shadowRoot.querySelectorAll('tbody tr:not(.empty-row)'); "
        "return rows[0].cells[0].textContent.trim(); }"
    )
    assert first_cell == "Apple"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_table_programmatic_rows_update(page, base_url):
    """
        Setting new ``rows`` via the class setter replaces the rendered
        content.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-table")
    _inject(frame, _TABLE_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-table').shadowRoot"
        ".querySelectorAll('tbody tr:not(.empty-row)').length === 3",
        timeout=5000,
    )
    # Replace with two new rows
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-table');
            el.rows = [{ name: 'Cherry', color: 'Red', calories: 50 },
                       { name: 'Grape',  color: 'Purple', calories: 67 }];
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-table').shadowRoot"
        ".querySelectorAll('tbody tr:not(.empty-row)').length === 2",
        timeout=5000,
    )
    first_cell = frame.evaluate(
        "() => { const el = document.querySelector('mj-table'); "
        "return el.shadowRoot.querySelector('tbody tr:not(.empty-row) th').textContent.trim(); }"
    )
    assert first_cell == "Cherry"

    return


# ===========================================================================
# mj-data-table
# ===========================================================================

_DT_SETUP = """() => {
    const el = document.querySelector('mj-data-table');
    delete el.columns;
    delete el.rows;
    el.columns = [
        { key: 'id',   label: 'ID',   width: '60px'  },
        { key: 'name', label: 'Name', width: '160px' },
        { key: 'role', label: 'Role', width: '140px' }
    ];
    el.rows = [
        { id: 1, name: 'Alice',   role: 'Engineer'  },
        { id: 2, name: 'Bob',     role: 'Designer'  },
        { id: 3, name: 'Charlie', role: 'Manager'   },
        { id: 4, name: 'Diana',   role: 'QA'        }
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_renders_columns(page, base_url):
    """
        After data is injected, the header row shows one cell per column.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    _inject(frame, _DT_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-data-table').shadowRoot"
        ".querySelectorAll('.header-cell').length === 3",
        timeout=5000,
    )
    count = frame.evaluate(
        "() => document.querySelector('mj-data-table').shadowRoot"
        ".querySelectorAll('.header-cell').length"
    )
    assert count == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_renders_rows(page, base_url):
    """
        After data is injected the body renders at least one row element.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    _inject(frame, _DT_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-data-table').shadowRoot"
        ".querySelectorAll('.row').length >= 1",
        timeout=5000,
    )
    row_count = frame.evaluate(
        "() => document.querySelector('mj-data-table').shadowRoot"
        ".querySelectorAll('.row').length"
    )
    assert row_count >= 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_footer_shows_row_count(page, base_url):
    """
        The footer row-count label reflects the number of data rows supplied.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    _inject(frame, _DT_SETUP)
    frame.wait_for_function(
        "() => { const rc = document.querySelector('mj-data-table').shadowRoot"
        ".querySelector('.row-count'); return rc && rc.textContent.includes('4'); }",
        timeout=5000,
    )
    text = frame.evaluate(
        "() => document.querySelector('mj-data-table').shadowRoot"
        ".querySelector('.row-count').textContent.trim()"
    )
    assert "4" in text

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_sort_fires_event(page, base_url):
    """
        Clicking a sortable column header fires the ``mj-sort-change`` event
        with ``key`` and ``direction`` fields.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    # Make the element sortable and inject data
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-data-table');
            delete el.columns;
            delete el.rows;
            el.setAttribute('sortable', '');
            el.columns = [
                { key: 'id',   label: 'ID',   width: '60px',  sortable: true },
                { key: 'name', label: 'Name', width: '160px', sortable: true },
                { key: 'role', label: 'Role', width: '140px', sortable: true }
            ];
            el.rows = [
                { id: 1, name: 'Alice',   role: 'Engineer'  },
                { id: 2, name: 'Bob',     role: 'Designer'  }
            ];
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-data-table').shadowRoot"
        ".querySelector('.header-cell[data-sortable=\"true\"]') !== null",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__sortEvents = [];
            document.querySelector('mj-data-table').addEventListener(
                'mj-sort-change', e => window.__sortEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-data-table');
            const sortableHeader = el.shadowRoot.querySelector('.header-cell[data-sortable="true"]');
            if (sortableHeader) sortableHeader.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__sortEvents !== 'undefined' && window.__sortEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__sortEvents[0]")
    assert "key" in detail
    assert detail["direction"] in ("asc", "desc")

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_selection_fires_event(page, base_url):
    """
        Clicking a data cell when ``selection`` is ``single`` fires
        ``mj-selection-change`` with a ``selectedRows`` field.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-data-table');
            delete el.columns;
            delete el.rows;
            el.setAttribute('selection', 'single');
            el.columns = [{ key: 'name', label: 'Name', width: '160px' }];
            el.rows = [
                { name: 'Alice' },
                { name: 'Bob'   }
            ];
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-data-table').shadowRoot"
        ".querySelectorAll('.row').length >= 1",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__selEvents = [];
            document.querySelector('mj-data-table').addEventListener(
                'mj-selection-change', e => window.__selEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-data-table');
            const cell = el.shadowRoot.querySelector('.cell');
            if (cell) cell.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__selEvents !== 'undefined' && window.__selEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__selEvents[0]")
    assert "selectedRows" in detail

    return


# ===========================================================================
# mj-tree-grid
# ===========================================================================

_TG_SETUP = """() => {
    const el = document.querySelector('mj-tree-grid');
    delete el.columns;
    delete el.rows;
    el.columns = [
        { key: 'name', label: 'Name', width: '200px' },
        { key: 'size', label: 'Size', width: '100px' }
    ];
    el.rows = [
        { key: 'docs', data: { name: 'Documents', size: '-' }, children: [
            { key: 'cv',    data: { name: 'CV.pdf',     size: '120 KB' } },
            { key: 'cover', data: { name: 'Cover.docx', size: '45 KB'  } }
        ]},
        { key: 'imgs', data: { name: 'Images', size: '-' }, children: [
            { key: 'logo', data: { name: 'logo.png', size: '32 KB' } }
        ]}
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tree_grid_renders_header(page, base_url):
    """
        The tree grid shows at least two header cells (one per column).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-tree-grid")
    _inject(frame, _TG_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-grid').shadowRoot"
        ".querySelectorAll('.header-cell').length >= 2",
        timeout=5000,
    )
    count = frame.evaluate(
        "() => document.querySelector('mj-tree-grid').shadowRoot"
        ".querySelectorAll('.header-cell').length"
    )
    assert count >= 2

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tree_grid_renders_rows(page, base_url):
    """
        With ``expand-depth="1"`` the two top-level parents plus their
        children are visible (at least 4 rows).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-tree-grid")
    _inject(frame, _TG_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-grid').shadowRoot"
        ".querySelectorAll('.row').length >= 4",
        timeout=5000,
    )
    row_count = frame.evaluate(
        "() => document.querySelector('mj-tree-grid').shadowRoot"
        ".querySelectorAll('.row').length"
    )
    assert row_count >= 4

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tree_grid_has_expander_buttons(page, base_url):
    """
        Parent rows have expander buttons; leaf rows have hidden expanders.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-tree-grid")
    _inject(frame, _TG_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-grid').shadowRoot"
        ".querySelector('.expander-btn:not(.leaf)') !== null",
        timeout=5000,
    )
    has_expander = frame.evaluate(
        "() => document.querySelector('mj-tree-grid').shadowRoot"
        ".querySelector('.expander-btn:not(.leaf)') !== null"
    )
    assert has_expander is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tree_grid_collapse_fires_event(page, base_url):
    """
        Clicking the expander button on an expanded parent row fires the
        ``mj-row-collapse`` event.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-tree-grid")
    _inject(frame, _TG_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-grid').shadowRoot"
        ".querySelector('.expander-btn:not(.leaf)') !== null",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__collapseEvents = [];
            document.querySelector('mj-tree-grid').addEventListener(
                'mj-row-collapse', e => window.__collapseEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-tree-grid');
            const btn = el.shadowRoot.querySelector('.expander-btn:not(.leaf)');
            if (btn) btn.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__collapseEvents !== 'undefined' "
        "&& window.__collapseEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__collapseEvents[0]")
    assert "key" in detail

    return


# ===========================================================================
# mj-list
# ===========================================================================

_LIST_SETUP = """() => {
    const el = document.querySelector('mj-list');
    delete el.items;
    el.items = [
        { label: 'Design tokens',  href: '#tokens'   },
        { label: 'Components',     href: '#comps'    },
        { label: 'Patterns',       href: '#patterns' },
        { label: 'Accessibility',  href: '#a11y'     }
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_list_renders_items(page, base_url):
    """
        After items are set four ``<li>`` elements appear in the list.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-list")
    _inject(frame, _LIST_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-list').shadowRoot"
        ".querySelectorAll('li[part=item]').length === 4",
        timeout=5000,
    )
    count = frame.evaluate(
        "() => document.querySelector('mj-list').shadowRoot"
        ".querySelectorAll('li[part=item]').length"
    )
    assert count == 4

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_list_items_with_href_are_links(page, base_url):
    """
        Items with an ``href`` are rendered as ``<a>`` anchors.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-list")
    _inject(frame, _LIST_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-list').shadowRoot"
        ".querySelectorAll('li a').length === 4",
        timeout=5000,
    )
    link_count = frame.evaluate(
        "() => document.querySelector('mj-list').shadowRoot"
        ".querySelectorAll('li a').length"
    )
    assert link_count == 4

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_list_item_click_fires_event(page, base_url):
    """
        Clicking a button-type item (``action`` key) fires ``mj-item-click``
        with ``index`` and ``label`` fields without navigating the frame.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-list")
    # Use action items (rendered as buttons) to avoid iframe navigation
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-list');
            delete el.items;
            el.items = [
                { label: 'Option A', action: true },
                { label: 'Option B', action: true }
            ];
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-list').shadowRoot"
        ".querySelectorAll('li button').length >= 1",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__listEvents = [];
            document.querySelector('mj-list').addEventListener(
                'mj-item-click', e => window.__listEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-list');
            const btn = el.shadowRoot.querySelector('li button');
            if (btn) btn.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__listEvents !== 'undefined' && window.__listEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__listEvents[0]")
    assert detail["index"] == 0
    assert "label" in detail

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_list_description_type_renders_dl(page, base_url):
    """
        When ``type="description"`` is set programmatically the list
        renders ``<dt>`` terms.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-list")
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-list');
            el.setAttribute('type', 'description');
            delete el.items;
            el.items = [
                { label: 'Term A', description: 'Def A' },
                { label: 'Term B', description: 'Def B' }
            ];
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-list').shadowRoot"
        ".querySelectorAll('dt').length === 2",
        timeout=5000,
    )
    dt_count = frame.evaluate(
        "() => document.querySelector('mj-list').shadowRoot"
        ".querySelectorAll('dt').length"
    )
    assert dt_count == 2

    return


# ===========================================================================
# mj-virtual-list
# ===========================================================================

_VL_SETUP = """() => {
    const el = document.querySelector('mj-virtual-list');
    delete el.items;
    delete el.renderItem;
    el.renderItem = (item) => `<div style='padding:8px 12px'>${item.label}</div>`;
    const items = Array.from({ length: 40 }, (_, i) => ({ label: 'Item ' + (i + 1) }));
    el.items = items;
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_virtual_list_renders_items_window(page, base_url):
    """
        The virtual list renders at least one ``.vl-item`` in the DOM for
        a 40-item dataset.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-virtual-list")
    _inject(frame, _VL_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelectorAll('.vl-item').length >= 1",
        timeout=5000,
    )
    item_count = frame.evaluate(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelectorAll('.vl-item').length"
    )
    assert item_count >= 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_virtual_list_dom_count_less_than_total(page, base_url):
    """
        For a 40-item dataset the virtual window renders fewer than 40 DOM
        items to prove virtualisation is active.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-virtual-list")
    _inject(frame, _VL_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelectorAll('.vl-item').length >= 1",
        timeout=5000,
    )
    dom_count = frame.evaluate(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelectorAll('.vl-item').length"
    )
    assert dom_count < 40

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_virtual_list_item_content_renders(page, base_url):
    """
        The ``renderItem`` function is applied; the first visible item
        contains the expected text.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-virtual-list")
    _inject(frame, _VL_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelectorAll('.vl-item').length >= 1",
        timeout=5000,
    )
    first_text = frame.evaluate(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelector('.vl-item').textContent.trim()"
    )
    assert "Item" in first_text

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_virtual_list_load_more_button_present(page, base_url):
    """
        The example uses ``load-strategy="manual"``; a Load-more button
        should be present in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-virtual-list")
    frame.wait_for_function(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelector('.load-more-btn') !== null",
        timeout=5000,
    )
    btn_present = frame.evaluate(
        "() => document.querySelector('mj-virtual-list').shadowRoot"
        ".querySelector('.load-more-btn') !== null"
    )
    assert btn_present is True

    return


# ===========================================================================
# mj-kanban
# ===========================================================================

_KB_SETUP = """() => {
    const el = document.querySelector('mj-kanban');
    delete el.columns;
    el.columns = [
        { id: 'todo',  label: 'To Do',      cards: [
            { id: 'c1', title: 'Write tests'   },
            { id: 'c2', title: 'Update README'  }
        ]},
        { id: 'wip',   label: 'In Progress', wipLimit: 2, cards: [
            { id: 'c3', title: 'Refactor API'   }
        ]},
        { id: 'done',  label: 'Done',         cards: [
            { id: 'c4', title: 'Deploy v1.0'    }
        ]}
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_kanban_renders_columns(page, base_url):
    """
        After data is injected the board contains three column sections.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-kanban")
    _inject(frame, _KB_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-kanban').shadowRoot"
        ".querySelectorAll('.column').length === 3",
        timeout=5000,
    )
    col_count = frame.evaluate(
        "() => document.querySelector('mj-kanban').shadowRoot"
        ".querySelectorAll('.column').length"
    )
    assert col_count == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_kanban_renders_cards(page, base_url):
    """
        The board renders four cards spread across columns.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-kanban")
    _inject(frame, _KB_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-kanban').shadowRoot"
        ".querySelectorAll('.card').length === 4",
        timeout=5000,
    )
    card_count = frame.evaluate(
        "() => document.querySelector('mj-kanban').shadowRoot"
        ".querySelectorAll('.card').length"
    )
    assert card_count == 4

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_kanban_card_click_fires_event(page, base_url):
    """
        Clicking a card body fires ``mj-card-click`` with ``cardId`` and
        ``colId`` fields.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-kanban")
    _inject(frame, _KB_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-kanban').shadowRoot"
        ".querySelectorAll('.card').length >= 1",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__cardEvents = [];
            document.querySelector('mj-kanban').addEventListener(
                'mj-card-click', e => window.__cardEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-kanban');
            const card = el.shadowRoot.querySelector('.card');
            if (card) card.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__cardEvents !== 'undefined' && window.__cardEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__cardEvents[0]")
    assert "cardId" in detail
    assert "colId" in detail

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_kanban_column_titles_correct(page, base_url):
    """
        Column header titles match the labels supplied in the example.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-kanban")
    _inject(frame, _KB_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-kanban').shadowRoot"
        ".querySelectorAll('.col-title').length === 3",
        timeout=5000,
    )
    titles = frame.evaluate(
        "() => Array.from(document.querySelector('mj-kanban').shadowRoot"
        ".querySelectorAll('.col-title')).map(t => t.textContent.trim())"
    )
    assert "To Do" in titles
    assert "In Progress" in titles
    assert "Done" in titles

    return


# ===========================================================================
# mj-calendar
# ===========================================================================

_CAL_SETUP = """() => {
    const el = document.querySelector('mj-calendar');
    delete el.events;
    const today = new Date();
    const y = today.getFullYear();
    const m = today.getMonth();
    el.events = [
        { id: 'e1', title: 'Team standup',
          start: new Date(y, m, 3, 9, 0),  end: new Date(y, m, 3, 9, 30) },
        { id: 'e2', title: 'Design review',
          start: new Date(y, m, 10, 14, 0), end: new Date(y, m, 10, 15, 0),
          color: '#6366f1' },
        { id: 'e3', title: 'Release',
          start: new Date(y, m, 20, 11, 0), end: new Date(y, m, 20, 12, 0),
          color: '#22c55e' }
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_renders_month_grid(page, base_url):
    """
        In month view the calendar renders at least 28 day cells.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    frame.wait_for_function(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.day-cell').length >= 28",
        timeout=5000,
    )
    cell_count = frame.evaluate(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.day-cell').length"
    )
    assert cell_count >= 28

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_renders_event_chips(page, base_url):
    """
        After events are injected at least one event chip appears in the
        calendar grid.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    # Wait for grid to be ready first
    frame.wait_for_function(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.day-cell').length >= 28",
        timeout=5000,
    )
    _inject(frame, _CAL_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.event-chip').length >= 1",
        timeout=5000,
    )
    chip_count = frame.evaluate(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.event-chip').length"
    )
    assert chip_count >= 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_event_click_fires_event(page, base_url):
    """
        Clicking an event chip fires ``mj-event-click`` with an ``eventId``
        field.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    frame.wait_for_function(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.day-cell').length >= 28",
        timeout=5000,
    )
    _inject(frame, _CAL_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.event-chip').length >= 1",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__calEvents = [];
            document.querySelector('mj-calendar').addEventListener(
                'mj-event-click', e => window.__calEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-calendar');
            const chip = el.shadowRoot.querySelector('.event-chip');
            if (chip) chip.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__calEvents !== 'undefined' && window.__calEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__calEvents[0]")
    assert "eventId" in detail

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_date_select_fires_event(page, base_url):
    """
        Clicking a day cell fires ``mj-date-select`` with an ISO date string.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    frame.wait_for_function(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelectorAll('.day-cell').length >= 28",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__dateEvents = [];
            document.querySelector('mj-calendar').addEventListener(
                'mj-date-select', e => window.__dateEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-calendar');
            const cell = el.shadowRoot.querySelector(
                '.day-cell:not(.other-month):not([aria-disabled="true"])'
            );
            if (cell) cell.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__dateEvents !== 'undefined' && window.__dateEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__dateEvents[0]")
    assert "date" in detail
    assert len(detail["date"]) == 10

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_navigation_fires_period_change(page, base_url):
    """
        Clicking the Previous navigation button fires ``mj-period-change``
        with start, end, and view fields.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    frame.wait_for_function(
        "() => document.querySelector('mj-calendar').shadowRoot"
        ".querySelector('[part=\"prev-button\"]') !== null",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__periodEvents = [];
            document.querySelector('mj-calendar').addEventListener(
                'mj-period-change', e => window.__periodEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-calendar');
            const btn = el.shadowRoot.querySelector('[part="prev-button"]');
            if (btn) btn.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__periodEvents !== 'undefined' && window.__periodEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__periodEvents[0]")
    assert "start" in detail
    assert "end" in detail
    assert "view" in detail

    return


# ===========================================================================
# mj-master-detail
# ===========================================================================

_MD_SETUP = """() => {
    const el = document.querySelector('mj-master-detail');
    delete el.items;
    el.items = [
        { key: 'fr', label: 'France',  meta: 'Europe'   },
        { key: 'jp', label: 'Japan',   meta: 'Asia'     },
        { key: 'br', label: 'Brazil',  meta: 'Americas' }
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_master_detail_renders_items(page, base_url):
    """
        After items are injected three master list items are rendered.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-master-detail")
    _inject(frame, _MD_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-master-detail').shadowRoot"
        ".querySelectorAll('.master-item').length === 3",
        timeout=5000,
    )
    count = frame.evaluate(
        "() => document.querySelector('mj-master-detail').shadowRoot"
        ".querySelectorAll('.master-item').length"
    )
    assert count == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_master_detail_item_labels_rendered(page, base_url):
    """
        The label text of each injected item is visible in the master list.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-master-detail")
    _inject(frame, _MD_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-master-detail').shadowRoot"
        ".querySelectorAll('.item-label').length >= 3",
        timeout=5000,
    )
    labels = frame.evaluate(
        "() => Array.from(document.querySelector('mj-master-detail').shadowRoot"
        ".querySelectorAll('.item-label')).map(el => el.textContent.trim())"
    )
    assert "France" in labels
    assert "Japan" in labels
    assert "Brazil" in labels

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_master_detail_item_select_fires_event(page, base_url):
    """
        Clicking a master item fires ``mj-item-select`` with the correct key.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-master-detail")
    _inject(frame, _MD_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-master-detail').shadowRoot"
        ".querySelectorAll('.master-item').length >= 1",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__mdEvents = [];
            document.querySelector('mj-master-detail').addEventListener(
                'mj-item-select', e => window.__mdEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-master-detail');
            const item = el.shadowRoot.querySelector('.master-item');
            if (item) item.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__mdEvents !== 'undefined' && window.__mdEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__mdEvents[0]")
    assert "key" in detail
    assert detail["key"] == "fr"

    return


# ===========================================================================
# mj-column-picker
# ===========================================================================

_CP_SETUP = """() => {
    const cols = [
        { key: 'name',  label: 'Name',   visible: true,  locked: true  },
        { key: 'email', label: 'Email',  visible: true  },
        { key: 'role',  label: 'Role',   visible: true  },
        { key: 'dept',  label: 'Dept',   visible: false }
    ];
    const el = document.querySelector('mj-column-picker');
    delete el.columns;
    delete el.defaultColumns;
    el.columns = cols;
    el.defaultColumns = cols;
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_column_picker_trigger_button_visible(page, base_url):
    """
        The trigger button is rendered and labelled correctly.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-column-picker")
    frame.wait_for_function(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelector('.trigger-btn') !== null",
        timeout=5000,
    )
    label = frame.evaluate(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelector('.trigger-btn').getAttribute('aria-label')"
    )
    assert label == "Columns"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_column_picker_opens_panel(page, base_url):
    """
        Clicking the trigger button opens the panel (``aria-hidden`` becomes
        ``"false"``).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-column-picker")
    frame.wait_for_function(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelector('.trigger-btn') !== null",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-column-picker');
            el.shadowRoot.querySelector('.trigger-btn').click();
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelector('.panel').getAttribute('aria-hidden') === 'false'",
        timeout=5000,
    )
    panel_hidden = frame.evaluate(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelector('.panel').getAttribute('aria-hidden')"
    )
    assert panel_hidden == "false"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_column_picker_lists_columns(page, base_url):
    """
        When the panel is open the column list contains one row per column
        descriptor (four in the injected example).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-column-picker")
    _inject(frame, _CP_SETUP)
    # Open the panel
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-column-picker');
            el.setAttribute('open', '');
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelectorAll('.column-item').length === 4",
        timeout=5000,
    )
    count = frame.evaluate(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelectorAll('.column-item').length"
    )
    assert count == 4

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_column_picker_fires_open_event(page, base_url):
    """
        Opening the panel fires ``mj-picker-open``.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-column-picker")
    frame.wait_for_function(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelector('.trigger-btn') !== null",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__cpOpenEvents = [];
            document.querySelector('mj-column-picker').addEventListener(
                'mj-picker-open', () => window.__cpOpenEvents.push(true)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-column-picker');
            el.shadowRoot.querySelector('.trigger-btn').click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__cpOpenEvents !== 'undefined' && window.__cpOpenEvents.length > 0",
        timeout=5000,
    )
    fired = frame.evaluate("() => window.__cpOpenEvents.length > 0")
    assert fired is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_column_picker_visibility_change_immediate_mode(page, base_url):
    """
        Toggling an unlocked checkbox in ``apply-mode="immediate"`` fires
        ``mj-column-visibility-change`` with the expected fields.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-column-picker")
    _inject(frame, _CP_SETUP)
    # Open the panel
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-column-picker');
            el.setAttribute('open', '');
        }"""
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-column-picker').shadowRoot"
        ".querySelectorAll('.col-checkbox:not([disabled])').length >= 1",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__visEvents = [];
            document.querySelector('mj-column-picker').addEventListener(
                'mj-column-visibility-change',
                e => window.__visEvents.push(e.detail)
            );
        }"""
    )
    # Click the first unlocked checkbox
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-column-picker');
            const cb = el.shadowRoot.querySelector('.col-checkbox:not([disabled])');
            if (cb) cb.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__visEvents !== 'undefined' && window.__visEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__visEvents[0]")
    assert "key" in detail
    assert "visible" in detail
    assert "columns" in detail

    return


# ===========================================================================
# mj-bulk-action-bar
# ===========================================================================

_BAB_SETUP = """() => {
    const el = document.querySelector('mj-bulk-action-bar');
    delete el.actions;
    el.setAttribute('selected-count', '3');
    el.setAttribute('total-count', '20');
    el.setAttribute('visible', '');
    el.actions = [
        { key: 'export', label: 'Export', icon: '⬇' },
        { key: 'tag',    label: 'Tag',    icon: '\U0001f3f7' },
        { key: 'delete', label: 'Delete', icon: '\U0001f5d1', destructive: true }
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_bulk_action_bar_visible_when_selected(page, base_url):
    """
        After ``selected-count`` is set and ``visible`` is applied the bar
        is displayed as ``flex``.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-bulk-action-bar")
    _inject(frame, _BAB_SETUP)
    frame.wait_for_function(
        "() => { const el = document.querySelector('mj-bulk-action-bar'); "
        "const bar = el.shadowRoot.querySelector('.bar'); "
        "return bar && getComputedStyle(bar).display === 'flex'; }",
        timeout=5000,
    )
    bar_display = frame.evaluate(
        "() => { const el = document.querySelector('mj-bulk-action-bar'); "
        "const bar = el.shadowRoot.querySelector('.bar'); "
        "return getComputedStyle(bar).display; }"
    )
    assert bar_display == "flex"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_bulk_action_bar_count_label(page, base_url):
    """
        The count label reflects the ``selected-count`` attribute value.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-bulk-action-bar")
    _inject(frame, _BAB_SETUP)
    frame.wait_for_function(
        "() => { const el = document.querySelector('mj-bulk-action-bar'); "
        "const lbl = el.shadowRoot.querySelector('.count-label'); "
        "return lbl && lbl.textContent.includes('3'); }",
        timeout=5000,
    )
    label_text = frame.evaluate(
        "() => document.querySelector('mj-bulk-action-bar').shadowRoot"
        ".querySelector('.count-label').textContent.trim()"
    )
    assert "3" in label_text

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_bulk_action_bar_renders_action_buttons(page, base_url):
    """
        After the ``actions`` property is set three action buttons are
        rendered.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-bulk-action-bar")
    _inject(frame, _BAB_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-bulk-action-bar').shadowRoot"
        ".querySelectorAll('.action-btn').length === 3",
        timeout=5000,
    )
    btn_count = frame.evaluate(
        "() => document.querySelector('mj-bulk-action-bar').shadowRoot"
        ".querySelectorAll('.action-btn').length"
    )
    assert btn_count == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_bulk_action_bar_action_fires_event(page, base_url):
    """
        Clicking an action button fires ``mj-action`` with the correct
        ``actionKey``.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-bulk-action-bar")
    _inject(frame, _BAB_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-bulk-action-bar').shadowRoot"
        ".querySelectorAll('.action-btn').length >= 1",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__actionEvents = [];
            document.querySelector('mj-bulk-action-bar').addEventListener(
                'mj-action', e => window.__actionEvents.push(e.detail)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-bulk-action-bar');
            const btn = el.shadowRoot.querySelector('.action-btn');
            if (btn) btn.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__actionEvents !== 'undefined' && window.__actionEvents.length > 0",
        timeout=5000,
    )
    detail = frame.evaluate("() => window.__actionEvents[0]")
    assert "actionKey" in detail
    assert detail["actionKey"] == "export"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_bulk_action_bar_clear_fires_event(page, base_url):
    """
        Clicking the clear (×) button fires ``mj-clear-selection``.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-bulk-action-bar")
    _inject(frame, _BAB_SETUP)
    frame.wait_for_function(
        "() => document.querySelector('mj-bulk-action-bar').shadowRoot"
        ".querySelector('.clear-btn') !== null",
        timeout=5000,
    )
    frame.evaluate(
        """() => {
            window.__clearEvents = [];
            document.querySelector('mj-bulk-action-bar').addEventListener(
                'mj-clear-selection', () => window.__clearEvents.push(true)
            );
        }"""
    )
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-bulk-action-bar');
            const btn = el.shadowRoot.querySelector('.clear-btn');
            if (btn) btn.click();
        }"""
    )
    frame.wait_for_function(
        "() => typeof window.__clearEvents !== 'undefined' && window.__clearEvents.length > 0",
        timeout=5000,
    )
    fired = frame.evaluate("() => window.__clearEvents.length > 0")
    assert fired is True

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
