# mj-* Web Component Library

A framework-agnostic library of 139 native Custom Elements served as static
assets by `codecraftai-webworks`. No build step is required.

## Usage

```html
<!-- Design tokens: link once at the document level. -->
<link rel="stylesheet" href="/static/styles/tokens.css">

<!-- All components, registered automatically. -->
<script type="module" src="/static/javascript/index.js"></script>

<mj-button variant="primary">Save</mj-button>
```

Individual components remain independently importable for tree-shaking:

```js
import { MjButton } from "/static/javascript/components/mjbutton.js";
import { define } from "/static/javascript/core/registry.js";
define(MjButton);
```

## Layout

```
static/
  styles/
    tokens.css      design tokens (light/dark/high-contrast)
    base.css        shared base styles (also for light-DOM use)
  javascript/
    index.js        barrel: imports + registers every component
    core/           shared foundation (see below)
    components/     139 component modules (mj<name>.js)
  gallery.html      live demo of components, docking, anchoring, theming
```

## Foundation (`core/`)

| Module | Provides |
|--------|----------|
| `mjelement.js` | `MjElement` base class; shadow DOM, attr/prop reflection, lifecycle, `emit`, dock/anchor participation, inherited context menu. `nextId()`. |
| `registry.js` | `define` / `defineAll` / `whenDefined` — idempotent registration. |
| `basestyles.js` | Shared base stylesheet adopted into every shadow root. |
| `anchoring.js` | `layoutDock` — the edge-consumption docking engine. |
| `contextmenu.js` | `openContextMenu` / `closeContextMenu` — accessible popup menu used by the base class. |
| `overlay.js` | `position` / `autoPosition` — anchored-overlay positioning with flip/shift. |
| `focustrap.js` | `trapFocus`, `getFocusable`, `RovingTabindex`. |
| `forminternals.js` | `FormControlMixin` — form-associated value controls via `ElementInternals`. |
| `announcer.js` | `announce` — shared live-region service. |
| `intl.js` | `t`, `setLocale`, locale-aware number/date/currency formatting. |
| `collection.js` | `DataSource`, `VirtualWindow` — data + virtualization utilities. |

## Cross-cutting capabilities

- **Themeable** — every component styles exclusively from `--mj-*` design
  tokens. Switching `data-theme="light|dark"` on any ancestor re-themes the
  subtree; tokens inherit through shadow boundaries.
- **Docking** — components carry a `dock` attribute (`top`/`bottom`/`start`/
  `end`/`fill`); place them inside `<mj-dock-layout>` and they consume edges in
  order, with `fill` taking the remainder.
- **Anchoring** — components carry an `anchor` attribute (`top-start`,
  `center`, `bottom-end`, `stretch`, …) to pin themselves inside any
  positioned container; offset via `--mj-anchor-inset`.
- **Accessible & scriptable** — WAI-ARIA APG patterns, full keyboard support,
  focus management, and live-region announcements; state is exposed as
  getter/setter properties and components emit namespaced `mj-*` events.
- **Context menu** — every component inherits a popup context menu from the
  base class. Configure it with the `contextMenu` property /
  `setContextMenu(items)` method, or declaratively via the `context-menu`
  attribute (a JSON array). It opens on right-click or Shift+F10 / the
  ContextMenu key; choosing an item emits `mj-context-select`:

  ```js
  el.setContextMenu([
    { label: "Duplicate", value: "duplicate" },
    { separator: true },
    { label: "Delete", value: "delete" }
  ]);
  el.addEventListener("mj-context-select", (e) => console.log(e.detail.value));
  ```

  ```html
  <mj-button context-menu='[{"label":"Inspect","value":"inspect"}]'>Go</mj-button>
  ```

## Specifications

Per-component specs: `specs/web-components/`. Strategy, universal
requirements, and phasing: `web-component-development-plan.md`.
