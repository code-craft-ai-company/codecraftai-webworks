# testcomponents

A webworks test website whose sole purpose is to exercise and document the
`codecraftai-webworks` `mj-*` web component library. Every page is a sandbox
for playing with a control: its visual presentation, slotting, behaviour and
the different ways to use it. It requires **no authentication**.

## What it provides

- A **browse-by-group** landing page (`/`) listing every component, grouped,
  with a client-side filter (tag, name, summary; `?q=` keeps it in the URL).
- A **Charts** landing page (`/charts`) gathering every chart component, the
  chart parts and the chart-type library, with the same filter. A toggle in
  the header switches between the two landing pages from any page.
- A per-group **index page** (`/components/<group>`) served by a dedicated
  `RestBlueprint`.
- A **sandbox page** for every component (`/components/<group>/<tag>`), every
  `<mj-chart>` type (`/chart-type/<type>`) and every chart part
  (`/chart-part/<tag>`: `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-data-table`), each with:
  - the full description, how-to guidance and reference tables (attributes
    with kind / values / default, properties, methods, events with their
    detail, slots, CSS parts, CSS custom properties -- only those with rows),
  - a **gallery** of named examples (`?example=<key>` deep-links one),
  - editable **HTML, CSS and JS** panes with Run, Reset, open in a new tab
    and Copy; the JS runs as a module after every element is upgraded,
  - a **preview** that sizes itself to its content, with width presets
    (320 / 768 / 1024 / full), a drag handle, and theme (light / dark / OS)
    and direction (LTR / RTL) switches applied live,
  - an **inspector**: Controls generated from the documented attributes
    (set live on the first instance, HTML pane kept in sync), a Slots panel
    that switches slot content off and on, an Events log of every `mj-*`
    event (and `change` / `input`), and an Errors panel for uncaught errors
    and unhandled rejections,
  - on chart pages, sample-data presets (empty, single point, negative
    values, 1,000 points),
  - previous / next links within the group.

The counts on the pages (components, groups, chart types, chart parts) are
derived from the catalogs by `rendering.site_counts()`; at the time of
writing the catalog holds 143 components in 11 groups, 139 chart types and
3 chart parts.

## Layout

```
testcomponents/
  app.py                     ASGI application entry point
  rendering.py               server-side HTML rendering of every page
  assets/                    page chrome inlined into every page
    site.css, site.js        styles, theme toggle, tabs, landing filter
    sandbox.js               the sandbox controller (no mj-* dependency)
    preview.js               bootstrap inlined into each preview document
  catalog/                   component documentation catalog
    componentdoc.py          the ComponentDoc record (+ table normalizers)
    attributedoc.py          AttributeDoc: typed attribute -> control
    componentexample.py      ComponentExample: one gallery example
    groups.py                the 11 component groups
    <group>.py               per-group ComponentDoc lists
  charttypes/                <mj-chart> type catalog
    charttypedoc.py          the ChartTypeDoc record
    chartparts.py            ComponentDocs of the chart parts
    _0N_*.py                 per-family ChartTypeDoc lists
  endpoints/
    handlers.py              landing pages, chart pages, /static serving
    blueprints/              one RestBlueprint per component group
  tests/                     Playwright test suite
```

The `mj-*` library and design tokens are served from the `ccai.webworks`
static directory under the `/static` mount, with `ETag` / `Last-Modified`
validators: the browser revalidates every file and an unchanged one costs a
304. The page chrome never loads the library; only the preview documents do.

## Writing docs and examples

The data model (fields, attribute kinds, example keys, heights, how a
script waits for upgrade, sample slot content) is described in the
docstrings of `catalog/componentdoc.py`, `catalog/attributedoc.py`,
`catalog/componentexample.py` and `charttypes/charttypedoc.py`. Every new
field is optional, so a doc with only `example`, `attributes` and `events`
keeps working. A malformed field raises `SemanticError` when the catalog is
imported; check a module with:

```sh
PYTHONPATH=source/testsites:source/packages \
  python -c "import testcomponents.catalog, testcomponents.charttypes"
```

## Running the site

```sh
source .venv/bin/activate
PYTHONPATH=source/testsites:source/packages \
  python -m testcomponents.app
```

Then open <http://127.0.0.1:8000/>.

## Tests

See `tests/README.md`. The suite drives the site through Playwright and runs
under the `testbase` runner (from the repository root):

```sh
testbase testing run --root ./source/testsites/testcomponents \
    --includes=testcomponents.tests --output=./.output/testcomponents-tests
```

Without Playwright and its Chromium browser every test is skipped with a
reason naming the missing piece.
