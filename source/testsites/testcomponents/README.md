# testcomponents

A webworks test website whose sole purpose is to exercise and document the
`automojo-webworks` `mj-*` web component library. It requires **no
authentication**.

## What it provides

- A **browse-by-group** landing page (`/`) listing all 139 components across
  11 groups.
- A dedicated **Charts** landing page (`/charts`) gathering every chart
  component. A toggle in the header switches between the Components and
  Charts landing pages from any page.
- A per-group **index page** (`/components/<group>`) served by a dedicated
  `RestBlueprint`.
- An interactive **test/documentation page** for every component
  (`/components/<group>/<tag>`) with:
  - a description of what the component is and what it is used for,
  - how-to-use guidance and attribute/event tables,
  - the example source code,
  - a **live, editable playground** — edit the HTML and press *Run* to render
    the real component in an isolated preview iframe.

## Layout

```
testcomponents/
  app.py                     ASGI application entry point
  rendering.py               server-side HTML rendering
  catalog/                   component documentation catalog
    componentdoc.py          the ComponentDoc record
    groups.py                the 11 component groups
    <group>.py               per-group ComponentDoc lists
  endpoints/
    handlers.py              landing page + /static asset serving
    blueprints/              one RestBlueprint per component group
  tests/                     Playwright test suite
```

The `mj-*` library and design tokens are served from the
`automojo.webworks` static directory under the `/static` mount.

## Running the site

```sh
source .venv/bin/activate
PYTHONPATH=source/testsites:source/packages \
  python -m testcomponents.app
```

Then open <http://127.0.0.1:8000/>.

## Tests

See `tests/README.md`. The suite is Playwright-based:

```sh
cd source/testsites/testcomponents/tests
pytest -n 8
```
