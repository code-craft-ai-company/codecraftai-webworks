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

from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open(page, base_url: str, tag: str):
    """
        Navigate to the playground for ``tag`` and return the preview frame
        after the custom element is registered, its shadow root exists and
        the example's script has finished (``mjSandbox.ready``), so data a
        test injects is not overwritten by the example script afterwards.

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
    frame.wait_for_function(
        "() => window.mjSandbox !== undefined && window.mjSandbox.ready === true",
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_table_footer_slot_inside_tfoot(page, base_url):
    """
        Slotted footer content renders inside ``<tfoot>`` below the body, and
        a ``caption`` change after the first render updates the caption.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-table")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-table');
            const footer = document.createElement('div');
            footer.slot = 'footer';
            footer.textContent = 'Total';
            el.appendChild(footer);
            el.setAttribute('caption', 'Renamed');
            await wait(50);
            const sr = el.shadowRoot;
            const slot = sr.querySelector('slot[name="footer"]');
            const below = footer.getBoundingClientRect().top >= sr.querySelector('tbody').getBoundingClientRect().bottom - 1;
            return { inTfoot: slot.closest('tfoot') !== null, below: below,
                     caption: sr.querySelector('caption').textContent.trim() };
        }"""
    )
    assert result["inTfoot"] is True
    assert result["below"] is True
    assert result["caption"] == "Renamed"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_table_stack_toggle_reports_no_resize_observer_error(page, base_url):
    """
        responsive="stack" switching between cards and the table while the
        box is resized raises no "ResizeObserver loop" window error.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    page.goto(base_url + "/components/data/mj-table?example=responsive")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function("() => window.mjSandbox !== undefined && window.mjSandbox.ready === true", timeout=15000)

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const errors = [];
            const onError = (event) => errors.push(String(event.message));
            window.addEventListener("error", onError);
            const box = document.getElementById("box-stack");
            const wrapper = box.querySelector("mj-table").shadowRoot.querySelector(".scroll-wrapper");
            const stacked = [];
            for (const width of ["300px", "640px", "350px", "640px"]) {
                box.style.inlineSize = width;
                await wait(250);
                stacked.push(wrapper.hasAttribute("data-stacked"));
            }
            window.removeEventListener("error", onError);
            return { errors: errors, stacked: stacked };
        }"""
    )

    assert result["stacked"] == [True, False, True, False], result
    assert result["errors"] == [], result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_empty_placeholder_removed_when_rows_arrive(page, base_url):
    """
        Assigning ``columns`` before ``rows`` (the documented order) leaves no
        stale "No results" placeholder once the rows are rendered.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            document.body.innerHTML = '<mj-data-table id="fresh"></mj-data-table>';
            await wait(100);
            const el = document.getElementById('fresh');
            el.columns = [{ key: 'name', label: 'Name' }];
            await wait(50);
            const emptyBefore = el.shadowRoot.querySelectorAll('.empty-state').length;
            el.rows = [{ name: 'Alice' }, { name: 'Bob' }];
            await wait(50);
            return {
                emptyBefore: emptyBefore,
                emptyAfter: el.shadowRoot.querySelectorAll('.empty-state').length,
                rows: el.shadowRoot.querySelectorAll('.row').length
            };
        }"""
    )
    assert result["emptyBefore"] == 1
    assert result["emptyAfter"] == 0
    assert result["rows"] == 2

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_keyboard_sort_select_and_edit(page, base_url):
    """
        Enter on a sortable header sorts (numbers numerically, missing values
        last), Space on a cell selects its row, and F2 / Enter edit a cell and
        write the value to the row object even after sorting.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-data-table');
            delete el.columns;
            delete el.rows;
            el.setAttribute('sortable', '');
            el.setAttribute('selection', 'single');
            const rows = [
                { name: 'b', qty: 10 }, { name: 'a', qty: null }, { name: 'c', qty: 9 }
            ];
            el.columns = [{ key: 'name', label: 'Name' }, { key: 'qty', label: 'Qty' }];
            el.rows = rows;
            await wait(50);
            const sr = el.shadowRoot;
            const keydown = (k) => sr.activeElement.dispatchEvent(new KeyboardEvent('keydown',
                { key: k, bubbles: true, composed: true, cancelable: true }));
            el.focus();
            keydown('ArrowRight');
            keydown('Enter');
            await wait(50);
            const sorted = Array.from(sr.querySelectorAll('.row'))
                .sort((a, b) => a.offsetTop - b.offsetTop)
                .map(r => r.children[1].textContent);
            keydown('ArrowDown');
            keydown('ArrowLeft');
            keydown(' ');
            await wait(20);
            const selected = Array.from(el.selectedRows).length;
            keydown('F2');
            const input = sr.querySelector('.cell.editing input');
            input.value = 'edited';
            input.dispatchEvent(new KeyboardEvent('keydown',
                { key: 'Enter', bubbles: true, composed: true, cancelable: true }));
            await wait(20);
            return { sorted: sorted, selected: selected, edited: rows[2].name,
                     tabStops: sr.querySelectorAll('[tabindex="0"]').length };
        }"""
    )
    assert result["sorted"] == ["9", "10", ""]
    assert result["selected"] == 1
    assert result["edited"] == "edited"
    assert result["tabStops"] == 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_column_and_global_filter(page, base_url):
    """
        With ``filterable`` each column gets a filter input that narrows the
        rows and fires ``mj-filter-change``; ``globalFilter`` matches values,
        never property names.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-data-table")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-data-table');
            delete el.columns;
            delete el.rows;
            el.setAttribute('filterable', '');
            el.columns = [{ key: 'name', label: 'Name' }, { key: 'role', label: 'Role' }];
            el.rows = [
                { name: 'Alice', role: 'Engineer' },
                { name: 'Bob', role: 'Designer' },
                { name: 'Carol', role: 'Engineer' }
            ];
            await wait(50);
            const events = [];
            el.addEventListener('mj-filter-change', e => events.push(e.detail));
            const input = el.shadowRoot.querySelectorAll('.filter-input')[1];
            input.value = 'engin';
            input.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
            await wait(450);
            const columnFiltered = el.rowCount;
            el.filterState = {};
            el.globalFilter = 'role';
            await wait(20);
            const byPropertyName = el.rowCount;
            el.globalFilter = 'bob';
            await wait(20);
            return { columnFiltered: columnFiltered, events: events.length,
                     byPropertyName: byPropertyName, byValue: el.rowCount };
        }"""
    )
    assert result["columnFiltered"] == 2
    assert result["events"] == 1
    assert result["byPropertyName"] == 0
    assert result["byValue"] == 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_data_table_auto_height_grids_report_no_resize_observer_error(page, base_url):
    """
        Two grids without a height of their own (toolbar, footer and empty
        slots, one loading) load without a "ResizeObserver loop" error: the
        row render that resizes the observed body runs on the next frame.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    page.goto(base_url + "/components/data/mj-data-table?example=slots-and-states")
    page.wait_for_selector("[data-testid=playground-preview]")
    ready = """() => {
        const frame = document.getElementById("pg-frame");
        const sandbox = window.mjSandboxPage;
        return frame !== null && sandbox !== undefined && frame.getAttribute("data-ready-run") === String(sandbox.state.run);
    }"""
    page.wait_for_function(ready, timeout=15000)

    messages = []
    for _ in range(3):
        page.evaluate(
            """() => {
                const css = document.getElementById("pg-style");
                css.value = css.value.replace(/#books \\{ height: 280px; \\}/, "").replace(/height: 170px;/, "");
                window.mjSandboxPage.run();
            }"""
        )
        page.wait_for_function(ready, timeout=15000)
        page.wait_for_timeout(800)
        messages.extend(page.evaluate("() => window.mjSandboxPage.state.errors.map((error) => error.message)"))

    style = page.evaluate("() => document.getElementById('pg-style').value")
    assert "280px" not in style and "170px" not in style, style
    assert [message for message in messages if "ResizeObserver" in message] == [], messages

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_tree_grid_keyboard_navigation(page, base_url):
    """
        Rows are a roving tab stop: ArrowRight expands then moves to the first
        child, ArrowLeft moves back to the parent, Space selects the focused
        row, and expanders are not tab stops.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-tree-grid")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-tree-grid');
            delete el.columns;
            delete el.rows;
            el.setAttribute('selection', 'single');
            el.setAttribute('expand-depth', '0');
            el.columns = [{ key: 'name', label: 'Name' }];
            el.rows = [
                { key: 1, data: { name: 'Parent' }, children: [{ key: 2, data: { name: 'Child' } }] },
                { key: 3, data: { name: 'Other' } }
            ];
            await wait(50);
            const sr = el.shadowRoot;
            const keydown = (k) => sr.activeElement.dispatchEvent(new KeyboardEvent('keydown',
                { key: k, bubbles: true, composed: true, cancelable: true }));
            el.focus();
            keydown('ArrowRight');
            await wait(20);
            keydown('ArrowRight');
            const onChild = sr.activeElement.getAttribute('data-key');
            keydown(' ');
            await wait(20);
            const selected = Array.from(sr.querySelectorAll('.row[aria-selected="true"]'))
                .map(r => r.getAttribute('data-key'));
            keydown('ArrowLeft');
            return { onChild: onChild, selected: selected,
                     onParent: sr.activeElement.getAttribute('data-key'),
                     expanderTabIndex: sr.querySelector('.expander-btn').tabIndex };
        }"""
    )
    assert result["onChild"] == "2"
    assert result["selected"] == ["2"]
    assert result["onParent"] == "1"
    assert result["expanderTabIndex"] == -1

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_list_unsafe_href_and_ordered_markers(page, base_url):
    """
        A ``javascript:`` item href is neutralised, and an ordered list shows
        decimal markers without an explicit ``marker``.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-list")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            document.body.innerHTML = '<mj-list id="o" type="ordered"></mj-list>';
            await wait(100);
            const el = document.getElementById('o');
            el.items = [{ label: 'Safe', href: '#ok' }, { label: 'Bad', href: 'javascript:alert(1)' }];
            await wait(20);
            const ol = el.shadowRoot.querySelector('ol');
            const links = el.shadowRoot.querySelectorAll('a');
            return { hrefs: Array.from(links).map(a => a.getAttribute('href')),
                     listStyle: getComputedStyle(ol).listStyleType };
        }"""
    )
    assert result["hrefs"] == ["#ok", "#"]
    assert result["listStyle"] == "decimal"

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_virtual_list_items_keyboard_and_single_click_event(page, base_url):
    """
        The "No items" placeholder is gone once items exist, a click after
        scrolling emits exactly one ``mj-item-click``, and PageDown / Enter
        move focus between items and activate them.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-virtual-list")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-virtual-list');
            delete el.items;
            el.items = Array.from({ length: 60 }, (_, i) => ({ label: 'Item ' + i }));
            await wait(50);
            const sr = el.shadowRoot;
            const container = sr.querySelector('.scroll-container');
            const clicks = [];
            el.addEventListener('mj-item-click', e => clicks.push(e.detail.index));
            container.scrollTop = 600; await wait(60);
            container.scrollTop = 0; await wait(60);
            sr.querySelector('.vl-item[data-index="1"]').click();
            const clicksAfterScroll = clicks.length;
            el.focus();
            const keydown = (k) => sr.activeElement.dispatchEvent(new KeyboardEvent('keydown',
                { key: k, bubbles: true, composed: true, cancelable: true }));
            keydown('PageDown');
            keydown('PageDown');
            keydown('Enter');
            return { empty: sr.querySelectorAll('.empty-region').length,
                     clicksAfterScroll: clicksAfterScroll, clicks: clicks };
        }"""
    )
    assert result["empty"] == 0
    assert result["clicksAfterScroll"] == 1
    assert result["clicks"] == [1, 3]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_virtual_list_completeness_follows_total_and_end_of_list(page, base_url):
    """
        A host-loaded list that holds `total` items is complete: no Load more
        button, no mj-load-more, the aria-setsize of its articles is its size
        and the end region shows. Without `total` or `end-of-list` the list
        cannot know it is complete: it keeps offering more and its size is
        unknown (-1). The size is announced on the articles, never on the
        feed element (aria-setsize is not allowed on a feed).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-virtual-list")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            document.body.innerHTML =
                '<mj-virtual-list id="open-list" style="height:200px"></mj-virtual-list>' +
                '<mj-virtual-list id="total-list" total="3" style="height:200px"></mj-virtual-list>' +
                '<mj-virtual-list id="ended-list" end-of-list style="height:200px"></mj-virtual-list>';
            const loads = [];
            const items = [{ label: "one" }, { label: "two" }, { label: "three" }];
            for (const id of ["open-list", "total-list", "ended-list"]) {
                const list = document.getElementById(id);
                list.addEventListener("mj-load-more", () => loads.push(id));
                list.items = items.slice();
            }
            await wait(400);
            const state = (id) => {
                const root = document.getElementById(id).shadowRoot;
                const button = root.querySelector("[part='load-more-button']");
                return {
                    button: button !== null && getComputedStyle(button).display !== "none",
                    setsize: root.querySelector("[role='feed'] [role='article']").getAttribute("aria-setsize"),
                    feedSetsize: root.querySelector("[role='feed']").getAttribute("aria-setsize"),
                    end: root.querySelector("[part='end-state']").hidden === false
                };
            };
            return { open: state("open-list"), total: state("total-list"), ended: state("ended-list"), loads: loads };
        }"""
    )

    assert result["total"] == {"button": False, "setsize": "3", "feedSetsize": None, "end": True}, result
    assert result["ended"] == {"button": False, "setsize": "3", "feedSetsize": None, "end": True}, result
    assert result["open"]["button"] is True, result
    assert result["open"]["setsize"] == "-1", result
    assert result["open"]["feedSetsize"] is None, result
    assert "total-list" not in result["loads"] and "ended-list" not in result["loads"], result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_virtual_list_feed_owns_only_articles(page, base_url):
    """
        The role="feed" element of mj-virtual-list owns only its item
        articles (axe aria-required-children): the Load more button, the
        loading / error / end regions and the empty state are outside it.
        An empty list has no feed role (an empty feed is invalid), and the
        Load more text keeps 4.5:1 contrast in the dark theme.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-virtual-list")
    result = frame.evaluate(
        """async () => {
            """ + _A11Y_CONTRAST_JS + """
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            document.body.innerHTML =
                '<mj-virtual-list id="items-list" style="height:200px"></mj-virtual-list>' +
                '<mj-virtual-list id="error-list" error style="height:200px"></mj-virtual-list>' +
                '<mj-virtual-list id="empty-list" end-of-list style="height:200px"></mj-virtual-list>';
            await customElements.whenDefined("mj-virtual-list");
            document.getElementById("items-list").items = Array.from({ length: 30 }, (_, i) => ({ label: "Item " + i }));
            document.getElementById("error-list").items = [{ label: "one" }];
            await wait(300);
            const describe = (id) => {
                const root = document.getElementById(id).shadowRoot;
                const feed = root.querySelector("[role='feed']");
                return {
                    feed: feed !== null,
                    ownedRoles: feed === null ? [] : Array.from(new Set(Array.from(feed.children).map((child) => child.getAttribute("role")))),
                    foreignInside: feed === null ? 0 : feed.querySelectorAll(
                        "button, [role='alert'], [aria-live], .empty-region, .loading-region, .end-region, slot").length,
                    feedSetsize: feed === null ? null : feed.getAttribute("aria-setsize"),
                    button: root.querySelector("[part='load-more-button']") !== null,
                    alert: root.querySelector("[role='alert']") !== null,
                    empty: root.querySelector("[part='empty-state']") !== null
                };
            };
            const items = describe("items-list");
            const error = describe("error-list");
            const empty = describe("empty-list");
            document.documentElement.setAttribute("data-theme", "dark");
            await wait(100);
            const button = document.getElementById("items-list").shadowRoot.querySelector("[part='load-more-button']");
            const darkContrast = textContrast(button);
            document.documentElement.setAttribute("data-theme", "light");
            const lightContrast = textContrast(button);
            return { items: items, error: error, empty: empty, darkContrast: darkContrast, lightContrast: lightContrast };
        }"""
    )

    for key in ("items", "error"):
        state = result[key]
        assert state["feed"] is True, result
        assert state["ownedRoles"] == ["article"], result
        assert state["foreignInside"] == 0, result
        assert state["feedSetsize"] is None, result
        assert state["button"] is True, result
    assert result["error"]["alert"] is True, result
    assert result["empty"]["feed"] is False, result
    assert result["empty"]["empty"] is True, result
    assert result["darkContrast"] >= 4.5, result
    assert result["lightContrast"] >= 4.5, result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_kanban_keyboard_move_and_drop_position(page, base_url):
    """
        Enter on a card handle starts move mode, ArrowRight / Enter move the
        card to the next column (focus stays on its handle), and the WIP badge
        reports "at limit" rather than "exceeded" when count equals the limit.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-kanban")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-kanban');
            delete el.columns;
            el.setAttribute('wip-limits', '');
            el.columns = [
                { id: 'a', label: 'A', cards: [{ id: 'c1', title: 'One' }] },
                { id: 'b', label: 'B', wipLimit: 2, cards: [{ id: 'c2', title: 'Two' }] }
            ];
            await wait(50);
            const sr = el.shadowRoot;
            const moves = [];
            el.addEventListener('mj-card-move', e => moves.push(e.detail));
            const handle = sr.querySelector('.card[data-card-id="c1"] .card-handle');
            handle.focus();
            const keydown = (k) => sr.activeElement.dispatchEvent(new KeyboardEvent('keydown',
                { key: k, bubbles: true, composed: true, cancelable: true }));
            keydown('Enter');
            keydown('ArrowRight');
            keydown('Enter');
            await wait(20);
            const active = sr.activeElement;
            return { moves: moves, columnB: el.columns[1].cards.map(c => c.id),
                     focusCard: active.closest('.card').getAttribute('data-card-id'),
                     focusIsHandle: active.classList.contains('card-handle'),
                     badge: sr.querySelector('.wip-badge').className };
        }"""
    )
    assert len(result["moves"]) == 1
    assert result["moves"][0]["toColId"] == "b"
    assert result["columnB"] == ["c1", "c2"]
    assert result["focusCard"] == "c1"
    assert result["focusIsHandle"] is True
    assert result["badge"] == "wip-badge at-limit"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_kanban_empty_column_slot_is_not_inside_a_list(page, base_url):
    """
        A column body is a role="list" owning only list items while it holds
        cards. An empty column shows its empty-[id] slot in a body without
        the list role (a list may own only list items, axe
        aria-required-children); once a card arrives the body is a list
        again and the slot is gone.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-kanban")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            document.body.innerHTML = '<mj-kanban id="kb" label="Board">' +
                '<span slot="empty-review">Nothing waiting for review</span></mj-kanban>';
            await customElements.whenDefined("mj-kanban");
            const board = document.getElementById("kb");
            board.columns = [
                { id: "todo", label: "To Do", cards: [{ id: "c1", title: "Write tests" }, { id: "c2", title: "Docs" }] },
                { id: "review", label: "Review", cards: [] }
            ];
            await wait(100);
            const describe = () => {
                const bodies = Array.from(board.shadowRoot.querySelectorAll(".column-body"));
                return bodies.map((body) => ({
                    column: body.getAttribute("data-col-id"),
                    role: body.getAttribute("role"),
                    label: body.getAttribute("aria-label"),
                    childRoles: Array.from(new Set(Array.from(body.children)
                        .filter((child) => child.getAttribute("aria-hidden") !== "true")
                        .map((child) => child.getAttribute("role") || child.localName))),
                    slotted: Array.from(body.querySelectorAll("slot")).map((slot) => slot.assignedElements().length)
                }));
            };
            const before = describe();
            board.columns = [
                board.columns[0],
                { id: "review", label: "Review", cards: [{ id: "c3", title: "Check copy" }] }
            ];
            await wait(100);
            return { before: before, after: describe() };
        }"""
    )

    todo, review = result["before"]
    assert todo == {"column": "todo", "role": "list", "label": "To Do", "childRoles": ["listitem"], "slotted": []}, result
    assert review["role"] is None and review["label"] is None, result
    assert review["childRoles"] == ["slot"] and review["slotted"] == [1], result
    review_after = result["after"][1]
    assert review_after == {"column": "review", "role": "list", "label": "Review", "childRoles": ["listitem"], "slotted": []}, result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_local_dates_and_arrow_navigation(page, base_url):
    """
        ``value="2025-06-01"`` opens June 2025 (a local day, not UTC); arrow
        keys travel more than one cell, cross into the next month, and Enter
        selects the focused local date.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-calendar');
            el.setAttribute('value', '2025-06-01');
            await wait(50);
            const sr = el.shadowRoot;
            const label = sr.querySelector('.period-label').textContent;
            const dates = [];
            el.addEventListener('mj-date-select', e => dates.push(e.detail.date));
            sr.querySelector('.day-cell[data-date="2025-06-15"]').click();
            const cell = sr.querySelector('.day-cell[data-date="2025-06-28"]');
            cell.focus();
            const keydown = (k) => sr.activeElement.dispatchEvent(new KeyboardEvent('keydown',
                { key: k, bubbles: true, composed: true, cancelable: true }));
            keydown('ArrowRight');
            keydown('ArrowRight');
            keydown('ArrowRight');
            keydown('Enter');
            await wait(20);
            return { label: label, dates: dates,
                     shown: sr.querySelector('.period-label').textContent };
        }"""
    )
    assert "2025" in result["label"]
    assert "June" in result["label"] or "Jun" in result["label"]
    assert result["dates"] == ["2025-06-15", "2025-07-01"]
    assert "July" in result["shown"] or "Jul" in result["shown"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_form_submits_selected_day(page, base_url):
    """
        A named mj-calendar is form-associated: a required calendar is
        invalid until a day is selected, it submits the selected local day
        (not the displayed ``value``), and a form reset clears the selection.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            document.body.innerHTML = '<form id="f"><mj-calendar id="c" name="day" ' +
                'value="2025-06-01" required></mj-calendar></form>';
            await wait(200);
            const form = document.getElementById('f');
            const el = document.getElementById('c');
            const validBefore = el.checkValidity();
            el.shadowRoot.querySelector('.day-cell[data-date="2025-06-15"]').click();
            const submitted = new FormData(form).get('day');
            const validAfter = el.checkValidity();
            form.reset();
            return { validBefore: validBefore, submitted: submitted, validAfter: validAfter,
                     value: el.value, afterReset: new FormData(form).get('day'),
                     selectedAfterReset: el.selectedDate };
        }"""
    )
    assert result == {
        "validBefore": False, "submitted": "2025-06-15", "validAfter": True,
        "value": "2025-06-01", "afterReset": None, "selectedAfterReset": None,
    }

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_cancelled_event_create_keeps_selection(page, base_url):
    """
        mj-event-create comes first when a day is activated, and cancelling
        it keeps the previous selection (no mj-date-select). A readonly
        calendar selects without mj-event-create.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const calendar = document.querySelector("mj-calendar");
            const log = [];
            let veto = true;
            calendar.addEventListener("mj-event-create", (event) => {
                log.push("create " + event.detail.date);
                if (veto === true) { event.preventDefault(); }
            });
            calendar.addEventListener("mj-date-select", (event) => log.push("select " + event.detail.date));
            const cells = calendar.shadowRoot.querySelectorAll('.day-cell:not(.other-month):not([aria-disabled="true"])');
            const first = cells[0];
            const second = cells[1];
            const before = calendar.selectedDate;
            first.click();
            const vetoed = { selected: calendar.selectedDate, marked: calendar.shadowRoot.querySelectorAll(".day-cell[aria-selected]").length };
            veto = false;
            first.click();
            const accepted = { selected: calendar.selectedDate, marked: first.getAttribute("aria-selected") };
            veto = true;
            calendar.setAttribute("readonly", "");
            await wait(20);
            const secondKey = second.getAttribute("data-date");
            calendar.shadowRoot.querySelector('.day-cell[data-date="' + secondKey + '"]').click();
            return { before: before, vetoed: vetoed, accepted: accepted, readonlySelected: calendar.selectedDate,
                     firstKey: first.getAttribute("data-date"), secondKey: secondKey, log: log };
        }"""
    )

    first_key = result["firstKey"]
    second_key = result["secondKey"]
    assert result["vetoed"] == {"selected": result["before"], "marked": 0}, result
    assert result["accepted"] == {"selected": first_key, "marked": "true"}, result
    assert result["readonlySelected"] == second_key, result
    assert result["log"] == ["create " + first_key, "create " + first_key, "select " + first_key,
                             "select " + second_key], result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_calendar_event_chip_text_keeps_contrast_for_any_color(page, base_url):
    """
        An event's `color` is the chip's start stripe and a light tint
        behind the text, which stays --mj-text: every chip keeps 4.5:1 text
        contrast (axe color-contrast) in the light and the dark theme,
        whatever the colour, including the chart series colours the catalog
        uses and black, white and yellow.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-calendar")
    result = frame.evaluate(
        """async () => {
            """ + _A11Y_CONTRAST_JS + """
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            document.body.innerHTML = '<mj-calendar id="cal" value="2026-11-11"></mj-calendar>';
            await customElements.whenDefined("mj-calendar");
            const colors = [undefined, "#000000", "#ffffff", "#ffeb3b"];
            for (let series = 1; series <= 8; series = series + 1) {
                colors.push("var(--mj-chart-series-" + series + ")");
            }
            const calendar = document.getElementById("cal");
            calendar.events = colors.map((color, index) => ({
                id: "e" + index, title: "Event " + index,
                start: "2026-11-" + String(index + 2).padStart(2, "0"), color: color
            }));
            await wait(150);
            const measure = () => Array.from(calendar.shadowRoot.querySelectorAll(".event-chip")).map((chip) => textContrast(chip));
            document.documentElement.setAttribute("data-theme", "light");
            await wait(50);
            const light = measure();
            const blackChip = calendar.shadowRoot.querySelector(".event-chip[data-event-index='1']");
            const stripe = getComputedStyle(blackChip).borderInlineStartColor;
            document.documentElement.setAttribute("data-theme", "dark");
            await wait(50);
            const dark = measure();
            document.documentElement.setAttribute("data-theme", "light");
            return { count: colors.length, light: light, dark: dark, stripe: stripe };
        }"""
    )

    assert len(result["light"]) == result["count"], result
    assert len(result["dark"]) == result["count"], result
    assert min(result["light"]) >= 4.5, result
    assert min(result["dark"]) >= 4.5, result
    assert result["stripe"] == "rgb(0, 0, 0)", result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_master_detail_single_load_and_pinned_layout(page, base_url):
    """
        One click loads the detail once (numeric keys stay highlighted), and a
        pinned ``layout="side-by-side"`` neither recurses nor is rewritten.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-master-detail")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const el = document.querySelector('mj-master-detail');
            delete el.items;
            const calls = [];
            el.detailDataSource = (key) => { calls.push(key); return Promise.resolve({ key: key }); };
            el.items = [{ key: 1, label: 'One' }, { key: 2, label: 'Two' }];
            await wait(50);
            const sr = el.shadowRoot;
            sr.querySelector('.master-item[data-key="2"]').click();
            await wait(50);
            el.setAttribute('layout', 'side-by-side');
            await wait(50);
            return { calls: calls,
                     selected: Array.from(sr.querySelectorAll('.master-item[aria-selected="true"]'))
                         .map(i => i.getAttribute('data-key')),
                     layout: el.getAttribute('layout'), resolved: el.resolvedLayout,
                     tabStops: sr.querySelectorAll('.master-item[tabindex="0"]').length };
        }"""
    )
    assert result["calls"] == [2]
    assert result["selected"] == ["2"]
    assert result["layout"] == "side-by-side"
    assert result["resolved"] == "side-by-side"
    assert result["tabStops"] == 1

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_column_picker_keyboard_reorder_keeps_focus(page, base_url):
    """
        A grabbed handle moved with ArrowUp keeps focus, skips locked columns,
        and the drop fires ``mj-column-reorder``; Reset without
        ``defaultColumns`` restores the first assignment.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-column-picker")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            document.body.innerHTML = '<mj-column-picker id="fresh"></mj-column-picker>';
            await wait(100);
            const el = document.getElementById('fresh');
            el.columns = [
                { key: 'name', label: 'Name', locked: true },
                { key: 'email', label: 'Email' },
                { key: 'role', label: 'Role' }
            ];
            el.setAttribute('open', '');
            await wait(50);
            const sr = el.shadowRoot;
            const events = [];
            el.addEventListener('mj-column-reorder', e => events.push(e.detail));
            const handle = sr.querySelector('.column-item[data-col-key="role"] .drag-handle');
            handle.focus();
            handle.click();
            handle.dispatchEvent(new KeyboardEvent('keydown',
                { key: 'ArrowUp', bubbles: true, composed: true, cancelable: true }));
            sr.activeElement.dispatchEvent(new KeyboardEvent('keydown',
                { key: 'ArrowUp', bubbles: true, composed: true, cancelable: true }));
            const focusKept = sr.activeElement === handle;
            handle.click();
            const order = el.columns.map(c => c.key);
            sr.querySelector('[part="reset-button"]').click();
            return { focusKept: focusKept, order: order, events: events.length,
                     reset: el.columns.map(c => c.key) };
        }"""
    )
    assert result["focusKept"] is True
    assert result["order"] == ["name", "role", "email"]
    assert result["events"] == 1
    assert result["reset"] == ["name", "email", "role"]

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_bulk_action_bar_shows_when_count_rises(page, base_url):
    """
        The bar hides when ``selected-count`` drops to zero and shows itself
        again when it rises; a ``disabled`` attribute present at parse time
        disables the select-all checkbox and the clear button.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open(page, base_url, "mj-bulk-action-bar")
    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            document.body.innerHTML =
                '<mj-bulk-action-bar id="b" disabled total-count="5"></mj-bulk-action-bar>';
            await wait(100);
            const el = document.getElementById('b');
            const sr = el.shadowRoot;
            const disabled = [sr.querySelector('.select-all-cb').disabled,
                              sr.querySelector('.clear-btn').disabled];
            el.selectedCount = 2; await wait(20);
            const shown = el.hasAttribute('visible');
            el.selectedCount = 0; await wait(20);
            const hidden = el.hasAttribute('visible') === false;
            el.selectedCount = 1; await wait(20);
            return { disabled: disabled, shown: shown, hidden: hidden,
                     shownAgain: el.hasAttribute('visible') };
        }"""
    )
    assert result["disabled"] == [True, True]
    assert result["shown"] is True
    assert result["hidden"] is True
    assert result["shownAgain"] is True

    return


# ===========================================================================
# mj-row-selector
# ===========================================================================

def _set_row_selector_markup(frame, markup: str):
    """
        Replace the preview body of the mj-row-selector page with ``markup``
        and wait until every mj-row-selector in it has rendered.

        :param frame: The preview Frame.
        :param markup: The HTML to put in the preview body.
    """

    frame.evaluate("(markup) => { document.body.innerHTML = markup; }", markup)
    frame.wait_for_function(
        """() => Array.from(document.querySelectorAll('mj-row-selector'))
            .every((el) => el.shadowRoot !== null && el.shadowRoot.querySelector('input') !== null)""",
        timeout=5000,
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_row_selector_activation_from_indeterminate_selects(page, base_url):
    """
        Activating an indeterminate selector clears the mixed state and
        selects it, also when selected was set together with indeterminate
        (the native toggle alone would unselect it); activating again
        unselects.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    frame = _open(page, base_url, "mj-row-selector")
    _set_row_selector_markup(
        frame,
        '<mj-row-selector id="both" mode="all" selected indeterminate label="Select all"></mj-row-selector>'
        '<mj-row-selector id="mixed" mode="all" indeterminate label="Select all rows"></mj-row-selector>',
    )
    frame.evaluate(
        """() => {
            window.__rsDetails = [];
            for (const el of document.querySelectorAll('mj-row-selector')) {
                el.addEventListener('mj-row-select-change', (event) => { window.__rsDetails.push([el.id, event.detail.selected]); });
            }
        }"""
    )

    frame.locator("#both input").click()
    frame.locator("#mixed input").click()
    first = frame.evaluate(
        """() => ['both', 'mixed'].map((id) => {
            const el = document.getElementById(id);
            return [el.selected, el.indeterminate, el.shadowRoot.querySelector('input').checked];
        })"""
    )
    assert first == [[True, False, True], [True, False, True]]

    frame.locator("#both input").click()
    state = frame.evaluate("() => [document.getElementById('both').selected, window.__rsDetails]")
    assert state == [False, [["both", True], ["mixed", True], ["both", False]]]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_row_selector_disabled_click_does_not_reach_row(page, base_url):
    """
        A click on a disabled selector (its checkbox or its label text) is
        neither taken by the selector nor passed through to the table row
        underneath, and the host keeps the pointer.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    frame = _open(page, base_url, "mj-row-selector")
    _set_row_selector_markup(
        frame,
        '<table><tbody><tr id="rs-row">'
        '<td style="padding:16px"><mj-row-selector id="rs-dis" value="7" disabled>Row seven</mj-row-selector></td>'
        "<td>Order 7</td></tr></tbody></table>",
    )
    frame.evaluate(
        """() => {
            window.__rowClicks = 0;
            document.getElementById('rs-row').addEventListener('click', () => { window.__rowClicks = window.__rowClicks + 1; });
        }"""
    )

    frame.locator("#rs-dis input").click(force=True)
    frame.locator("#rs-dis .label").click(force=True)
    state = frame.evaluate(
        """() => {
            const el = document.getElementById('rs-dis');
            return { rowClicks: window.__rowClicks, selected: el.selected, pointer: getComputedStyle(el).pointerEvents };
        }"""
    )
    assert state == {"rowClicks": 0, "selected": False, "pointer": "auto"}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_row_selector_reports_only_its_own_event(page, base_url):
    """
        Toggling the selector reaches host listeners as one
        mj-row-select-change; the inner checkbox's composed native ``input``
        event stays inside the shadow root.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    frame = _open(page, base_url, "mj-row-selector")
    _set_row_selector_markup(
        frame,
        '<mj-row-selector id="rs-events" value="3">Row three</mj-row-selector>',
    )
    frame.evaluate(
        """() => {
            window.__hostEvents = [];
            const el = document.getElementById('rs-events');
            for (const name of ['input', 'mj-row-select-change']) {
                el.addEventListener(name, () => { window.__hostEvents.push(name); });
            }
        }"""
    )

    frame.locator("#rs-events input").click()
    events = frame.evaluate("() => window.__hostEvents")
    assert events == ["mj-row-select-change"], "Host listeners saw: {}".format(events)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_row_selector_icon_only_slot_gets_generated_name(page, base_url):
    """
        Slotted content without text (an aria-hidden icon) is shown but does
        not name the checkbox, so the generated name is used; slotted text
        names it through the wrapping label; label wins over both.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    icon = '<svg aria-hidden="true" width="16" height="16"><circle cx="8" cy="8" r="6"></circle></svg>'
    frame = _open(page, base_url, "mj-row-selector")
    _set_row_selector_markup(
        frame,
        '<mj-row-selector id="icon">' + icon + "</mj-row-selector>"
        '<mj-row-selector id="icon-all" mode="all">' + icon + "</mj-row-selector>"
        '<mj-row-selector id="text">' + icon + "Invoice 1042</mj-row-selector>"
        '<mj-row-selector id="labelled" label="Select invoice 7">' + icon + "</mj-row-selector>",
    )

    names = frame.evaluate(
        """() => ['icon', 'icon-all', 'text', 'labelled'].map((id) => {
            const root = document.getElementById(id).shadowRoot;
            return [root.querySelector('input').getAttribute('aria-label'), root.querySelector('.label').hidden];
        })"""
    )
    assert names == [
        ["Select row", False],
        ["Select all", False],
        [None, False],
        ["Select invoice 7", False],
    ]

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
