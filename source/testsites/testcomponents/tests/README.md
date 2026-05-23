# testcomponents Playwright test suite

Playwright tests covering the testcomponents site and the functionality of
every one of the 139 `mj-*` web components.

## Requirements

```sh
source .venv/bin/activate
pip install pytest-playwright pytest-xdist
playwright install chromium
```

## Running

```sh
cd source/testsites/testcomponents/tests
pytest -n 8            # parallel
pytest -m functional   # only the deep per-component interaction tests
```

`conftest.py` starts the testcomponents site in a subprocess on a free port
for the test session; no manual server start is needed.

## Controlling test pace

Playwright's `slow_mo` launch option pauses between every UI action. The
suite wires it to environment variables so the **whole suite** can be slowed
down for visual observation without editing any test:

| Variable | Effect |
|----------|--------|
| `MJ_TEST_SLOWMO` | Milliseconds to pause between every action (click, type, …). `0` / unset = full speed. |
| `MJ_TEST_HEADED` | Truthy (`1`/`true`/`yes`) runs the browser visible instead of headless. |

```sh
# Watch the components being tested, slowed down
MJ_TEST_HEADED=1 MJ_TEST_SLOWMO=400 pytest test_func_buttons.py

# Slow but headless (e.g. for video capture / debugging)
MJ_TEST_SLOWMO=250 pytest
```

Equivalent one-off CLI flags also work: `pytest --headed --slowmo 400`.

## Test modules

| Module | Scope |
|--------|-------|
| `test_site.py` | Browse page, group index pages, navigation, theme toggle, static assets, 404 handling. |
| `test_pages.py` | Parametrized over all 139 components: each page documents the component and provides the playground. |
| `test_playground.py` | Parametrized over all 139 components: the component registers, renders in the preview iframe, upgrades (shadow root), and the Run/Reset controls work. |
| `test_func_<group>.py` | Per-group deep functional tests — real interactions (clicks, typing, keyboard, ARIA state, emitted `mj-*` events) for every component. |

The preview is an isolated `<iframe>`, so modal components (which inert their
host document) cannot disable the test harness, and example `<script>` blocks
execute to populate data-driven components.
