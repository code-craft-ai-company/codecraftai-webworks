# testcomponents functional site suite

Browser tests covering the testcomponents site and the functionality of
every one of the 139 `mj-*` web components. The suite runs under the
`testbase` runner; the tree is a testbase root marked by
`source/testsites/testcomponents/__testroot__.py`.

## Requirements

```sh
source .venv/bin/activate
pip install playwright
playwright install chromium
```

Playwright is optional for the repository as a whole: without the package or
its Chromium browser every test in this suite is skipped with a reason naming
the missing piece, and nothing errors.

## Running

From the repository root:

```sh
testbase testing run --root ./source/testsites/testcomponents \
    --includes=testcomponents.tests --output=./.output/testcomponents-tests

# only the deep per-component interaction tests
testbase testing run --root ./source/testsites/testcomponents \
    --includes=testcomponents.tests --include-marker-exp='+categories~=functional' \
    --output=./.output/testcomponents-tests

# one module, or one test
testbase testing run --root ./source/testsites/testcomponents \
    --includes=testcomponents.tests.test_func_buttons --output=./.output/testcomponents-tests
testbase testing run --root ./source/testsites/testcomponents \
    --includes='testcomponents.tests.test_site#test_theme_toggle_switches_theme' \
    --output=./.output/testcomponents-tests
```

`testcomponents.tests/__init__.py` originates the run-wide resources: the
browser (`browser_session`) and the testcomponents site, started in a
subprocess on a free port (`base_url`). Each test attaches its own fresh
`page` with `@testbase.attach.parameter(create_page, identifier="page")`.
The factories live in `testcomponents.harness`; no manual server start is
needed.

## Controlling test pace

Playwright's `slow_mo` launch option pauses between every UI action. The
suite wires it to environment variables so the **whole suite** can be slowed
down for visual observation without editing any test:

| Variable | Effect |
|----------|--------|
| `MJ_TEST_SLOWMO` | Milliseconds to pause between every action (click, type, …). `0` / unset = full speed. |
| `MJ_TEST_HEADED` | Truthy (`1`/`true`/`yes`/`on`) runs the browser visible instead of headless. |

```sh
# Watch the components being tested, slowed down
MJ_TEST_HEADED=1 MJ_TEST_SLOWMO=400 testbase testing run --root ./source/testsites/testcomponents \
    --includes=testcomponents.tests.test_func_buttons --output=./.output/testcomponents-tests

# Slow but headless (e.g. for video capture / debugging)
MJ_TEST_SLOWMO=250 testbase testing run --root ./source/testsites/testcomponents \
    --includes=testcomponents.tests --output=./.output/testcomponents-tests
```

## Test modules

| Module | Scope |
|--------|-------|
| `test_site.py` | Browse page, group index pages, navigation, theme toggle, static assets, 404 handling. |
| `test_pages.py` | One test per catalogued component and check (`<check>__<group>_<tag>`): each page documents the component and provides the playground. |
| `test_playground.py` | One test per catalogued component and check: the component registers, renders in the preview iframe, upgrades (shadow root), and the Run/Reset controls work. |
| `test_chart_library.py` | The `<mj-chart>` library: one test per chart type page, plus a render check over a representative sample. |
| `test_context_menu.py` | The context menu every component inherits from `MjElement`. |
| `test_func_<group>.py`, `test_dyn_charts_<group>.py` | Per-group deep functional tests (category `functional`) — real interactions (clicks, typing, keyboard, ARIA state, emitted `mj-*` events) for every component. |

Sweeps over a catalog are defined as individual module-level tests by
`testcomponents.harness.generation.define_page_tests`, so a broken component
is reported by name. Small literal tables use `testbase.parametrize`, which
runs every case and reports each failing case with its arguments.

The preview is an isolated `<iframe>`, so modal components (which inert their
host document) cannot disable the test harness, and example `<script>` blocks
execute to populate data-driven components.
