# Chart Title Spec

- **Tag:** `<mj-chart-title>`
- **Class / file:** `MjChartTitle` / `charts/mjcharttitle.js`
- **Category:** Media & visualization (§5.9) — chart part of `<mj-chart>`
- **Primary or Variant:** Primary (a companion part of `<mj-chart>`)
- **Synonyms covered:** Chart title, Chart subtitle, Chart heading
- **Phase:** P3 (ships with `<mj-chart>`; Phase 1 of `chart-components-plan.md` §7)
- **Status:** Implemented (this spec documents the shipped behavior of `mjcharttitle.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-chart-title>` shows the title, and an optional subtitle, of a chart. It is
one of the coordinated part elements of the chart library
(`chart-components-plan.md` §3.3): it binds to an `<mj-chart>` controller — by
the controller's id in its `chart` attribute, or as a descendant of the chart —
and redraws each time the chart delivers a new model, so the title and subtitle
can come from the chart data (`meta.title`, `meta.subtitle`). Because it is a
separate element it can sit anywhere in the page (a card header, a dock-layout
edge) and still follow its chart. The bound chart uses the title text as its
accessible name when the chart has no name of its own. The title draws nothing
of the chart itself.

## 2. When to use / when not to use

Use for the visible title of an `<mj-chart>`, in particular when the title
should come from the data, should be placed apart from the drawing, or should
also name the chart for assistive technology. Set `level` when the title belongs
in the page's heading outline.

Do not use:
- for a page or section heading that is not tied to a chart — use a native
  heading;
- to give a chart an accessible name without visible text — set `label` (or
  `aria-label`) on `<mj-chart>`;
- for a longer text alternative — use `description` on `<mj-chart>` (or
  `meta.description` in the data);
- with the project-management charts (`<mj-burndown-chart>`, ...), which render
  their own titles.

## 3. Anatomy

- **Host element** — `display: block`; no surface of its own.
- **title (part)** — `<div class="title">`. Holds the default slot and a plain
  text span; carries `role="heading"` and `aria-level` when `level` is valid.
  - **default slot** — shows the element's own content when the content is the
    title source; hidden otherwise.
  - **text span** (`[data-title-text]`, not a part) — shows the title as plain
    text when it comes from `text` or `meta.title`; hidden otherwise.
- **subtitle (part)** — `<div class="subtitle">` with the subtitle as plain
  text; carries `hidden` when there is no subtitle.

Exactly one of the slot and the text span is visible at a time.

## 4. Variants & modes

There are no visual variants. The behavioral dimensions are:

| Mode | Selected by | Description |
|------|-------------|-------------|
| Attribute text | `text` present | `text` is shown as plain text; own content is hidden; `meta.title` is ignored |
| Own content | no `text`; content with non-blank text or any rendering element (an icon, an `<img alt>`) | The content is shown through the slot, markup included; its text alternative is the title text |
| Data title | no `text`, no content (only whitespace, comments, `script` / `style` / `template` or `hidden` elements) | `meta.title` of the bound chart's data, as plain text |
| Heading | `level="1"` ... `level="6"` | The `title` part is exposed as a heading of that level |
| Plain text (default) | no or invalid `level` | No heading semantics |
| Nested | placed inside `<mj-chart>` | Binds to that chart; the chart's styles place it above the drawing |
| Bound by id | `chart="<id>"` | Binds to that chart from anywhere in the page |
| Standalone | no chart resolves | Only `text`, own content and `subtitle` apply; no data fallback |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `chart` | string (element id) | — | No | Id of the `<mj-chart>` to bind to (trimmed). Looked up in the title's own root (document or shadow root), then in the document; an element that is not an `<mj-chart>` is ignored. Without it, or when it does not resolve, the nearest `<mj-chart>` ancestor is used (crossing shadow roots). Changing it rebinds |
| `text` | string | — | No | Title text, shown as plain text. Wins over the content and `meta.title` whenever the attribute is present, even when empty (an empty `text` shows no title) |
| `subtitle` | string | — | No | Subtitle text. Absent: `meta.subtitle` of the bound chart. Present but empty: no subtitle (no fallback to `meta.subtitle`) |
| `level` | integer `1`–`6` | — | No | Heading level of the `title` part. Parsed with `Number()`; a value that is not an integer from 1 to 6 (absent, empty, `0`, `7`, `2.5`, `h2`) removes the heading role |

None of these attributes has a property; nothing is reflected. Common MjElement
attributes (`dock`, `anchor`, `theme`, `hidden`, `context-menu`) behave as on
every component. `disabled` has no component-specific effect.

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `chartLabel` | `string` (read-only) | The title text currently shown, from whichever source won: the `text` value as written, the text alternative of the content (§11), or `String(meta.title)`; `""` when there is none (for example content that is only a decorative icon). The bound chart reads it for its accessible name |
| `controller` | `MjChart \| null` (read-only) | The chart the title is bound to (ChartPart mixin) |

**Methods**

| Method | Description |
|--------|-------------|
| `applyModel(model, context)` | Called by the controller with its model and render context (both `null` while the chart has nothing to show); caches them and redraws. Controller-facing; page code does not call it |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | Title content, shown as written (text, rich markup, an icon, an image) when `text` is absent and the content holds non-blank text or any rendering element. Its text alternative (§11) is the title text the chart uses for its name. Edits are observed (child list, character data, subtree, and the `alt`, `aria-label`, `aria-hidden` and `hidden` attributes of descendants) and redraw the title |

## 8. Events

N/A — `<mj-chart-title>` dispatches no events.

Related interactions:
- It listens on `document` for `mj-chart-connect` (dispatched by `<mj-chart>`,
  bubbling and composed, when the chart connects or its `id` changes) and
  resolves its controller again.
- When its title text changes while bound, it calls the controller's
  `refreshLabel()`, which recomputes the chart's `aria-label` and the caption of
  the chart's own hidden data table and, when the name changed, delivers the
  model to the bound parts again, so a `<mj-chart-data-table>` whose caption is
  the chart's name follows at once. No event is involved.

## 9. CSS parts & custom properties

**Parts**
- `::part(title)` — title line (the heading element when `level` is set)
- `::part(subtitle)` — subtitle line

**Custom properties**

| Property | Default | Description |
|---|---|---|
| `--mj-chart-title-font-size` | `var(--mj-font-size-lg, 1.125rem)` | Title font size |
| `--mj-chart-title-color` | `var(--mj-text, #14181f)` | Title color |

Shared tokens read directly (no component-specific property): title weight
`--mj-font-weight-bold` (fallback `700`); subtitle size `--mj-font-size-sm`
(`0.875rem`), color `--mj-text-muted` (`#5f6673`) and top margin `--mj-space-1`
(`0.25rem`). Restyle the subtitle through `::part(subtitle)`.

## 10. States

| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| titled | Title text shown in the `title` part | Heading role and level when `level` is valid |
| no title | `title` part empty (no text, no height) | With a valid `level` an empty heading is still exposed |
| subtitle | Subtitle line shown | Plain text, outside the heading |
| no subtitle | `subtitle` part carries `hidden` | — |
| unbound | Only `text`, content and `subtitle` are used | — |

The title is not focusable and has no hover, focus, active, selected, disabled,
loading or invalid state.

## 11. Behavior & interactions

- **Title source**, in order: the `text` attribute when present (even empty);
  else the element's own content when it has any (non-blank text, or an element
  other than `script` / `style` / `template` without `hidden`), shown through the
  slot; else `meta.title` of the bound chart's model, converted with `String()`;
  else empty.
- **Text alternative of the content** (the title text, `chartLabel`): text nodes
  as written; an element with a non-blank `aria-label` gives that label; an
  `<img>` / `<area>` gives its `alt`; an `<svg>` gives its `<title>` child's text;
  a `<br>` gives a space; `hidden`, `aria-hidden="true"`, `script`, `style` and
  `template` content gives nothing; other elements give the alternative of their
  children. Runs of whitespace are collapsed and the result is trimmed. Content
  that is only a decorative (`aria-hidden`) icon is shown but gives `""`, so the
  chart takes its name from its next source (`meta.title`, then "`<type>`
  chart").
- **Subtitle source**: the `subtitle` attribute when present; else
  `meta.subtitle` (`String()`); an empty result hides the subtitle part.
- **Redraws** happen after the first render, on every observed attribute change
  (`chart`, `text`, `subtitle`, `level` and the MjElement core attributes), on
  every mutation of the element's content (including `alt`, `aria-label`,
  `aria-hidden` and `hidden` changes on descendants), and on every model the controller
  delivers (each chart render, including resize re-renders, data changes and
  series toggles).
- **Binding** (ChartPart mixin): on connect the title resolves its controller
  (§5 `chart`), registers with it (`registerPart`) and receives the chart's
  current model if it has one. An `<mj-chart>` that is not upgraded yet, or that
  enters the page or gets its id later, announces itself with `mj-chart-connect`
  and the title binds then, so insertion order does not matter. On disconnect
  the title unregisters.
- **Chart name**: the chart's accessible name is, in order, an `aria-label` the
  page wrote, the chart's `label`, the chart's `title` attribute, the
  `chartLabel` of its bound title parts (registration order, first non-blank),
  `meta.title`, then "`<type>` chart". With `aria-labelledby` on the chart, the
  chart writes no `aria-label`. So the title names the chart only when the chart
  has none of the first three. Whenever the shown title text changes, the title
  calls `controller.refreshLabel()`; registering and unregistering a part also
  makes the chart recompute its name. A changed name is delivered to the
  chart's parts at once (no re-render).
- **Chart without data**: when the chart's data fails to load or parse, or the
  chart is removed from the page, the controller delivers `null`; the title then
  drops `meta.title` / `meta.subtitle` and keeps `text`, content and `subtitle`.
  A removed chart keeps the title registered and fills it again when re-inserted.
- **Layout when nested**: `<mj-chart>` styles its slotted title with
  `order: -1; flex: 0 0 auto`, so it is drawn above the drawing whatever its
  source position and does not shrink. Elsewhere it is an ordinary block that can
  be docked or anchored (MjElement).

## 12. Keyboard interaction

N/A — the title contains no focusable element and handles no keys.

## 13. Accessibility

- With a valid `level`, the `title` part has `role="heading"` and `aria-level`;
  the heading's content is the slotted content or the text span. The subtitle is
  outside the heading.
- Without `level` the title is plain text, not a heading.
- The bound chart copies the title text into its own `aria-label` (it does not
  use `aria-labelledby`). When the title is nested in the chart (a `figure`), a
  screen reader can hear the text once as the figure name and again as content.
- Title changes are not announced; there is no live region.
- Contrast depends on the theme tokens (`--mj-text` for the title,
  `--mj-text-muted` for the subtitle).

## 14. Form participation

N/A. `<mj-chart-title>` is not form-associated.

## 15. Internationalization & RTL

- The component has no built-in strings and uses no `t()` keys; all text comes
  from the author or the chart data.
- A locale change (`setLocale` / `registerStrings`) re-renders the element
  (MjElement default `onLocaleChanged` → `renderAgain()`), which also rebinds it;
  the text is unaffected.
- The title and subtitle are blocks with no `text-align` of their own, so they
  follow the inherited direction; `lang` / `dir` on slotted content are kept.

## 16. Progressive enhancement / SSR

Server renders `<mj-chart-title level="2" subtitle="Thousands of euros">Quarterly
revenue</mj-chart-title>`. Before upgrade the content shows as inline text, with
no subtitle and no heading semantics. On upgrade the element becomes a block, the
subtitle appears and the heading role is applied. A title or subtitle taken from
`meta` needs script (it comes from the chart data). A page that needs a heading
without script can put a native `<hN>` in the content and leave `level` unset
(setting both nests a heading inside a heading).

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `afterRender`,
  `onAttributeChanged`, `onTeardown`, docking / anchoring, theming)
- **ChartPart mixin** — `charts/core/chartpart.js` (controller resolution,
  registration, model delivery, `controller`, `applyModel`, `drawPart`,
  `onPartConnected`) and `charts/core/chartregistry.js` (`resolveController`,
  `mj-chart-connect`)
- **`<mj-chart>`** — `charts/mjchart.js`: `registerPart`, `unregisterPart`,
  `refreshLabel`; reads `chartLabel`. See [chart.md](chart.md): the controller
  draws no visible title of its own and delegates it to this element (its `title`
  attribute only feeds the accessible name).
- **Design-token stylesheet** (§6)
- Registered by `charts/index.js` (`defineAll`), which the library's main
  `index.js` imports.

## 18. Edge cases & error handling

- `text=""`: no title is shown, own content is hidden and `meta.title` is
  ignored; the chart skips the blank text when choosing its name.
- Content without text (only an icon element, an `<img alt>`): it counts as
  content and is shown through the slot; `meta.title` is not shown. The image's
  `alt` (or the icon's `aria-label` / SVG `<title>`) is the title text; a purely
  decorative icon gives `""` and the chart names itself from `meta.title`.
- Text inside `hidden` or `aria-hidden="true"` descendants does not count toward
  `chartLabel`. Text hidden only with CSS still counts.
- Whitespace-only `text`: rendered as whitespace; the chart ignores it for its
  name.
- `level` parsing: `" 3 "` and `"3.0"` are accepted as 3; any other non-integer
  or out-of-range value means no heading.
- `level` set while there is no title text: an empty heading is exposed.
- `chart` id that does not resolve, or names an element that is not an
  `<mj-chart>`: the nearest ancestor chart is used, else the title is unbound.
- Several titles bound to one chart: all are shown; the chart takes its name from
  the first registered one with non-blank text.
- A non-string `meta.title` / `meta.subtitle` is converted with `String()`.
- A failure while the controller delivers a model (`applyModel`) is caught by
  the controller (console warning) and does not stop the chart or its other
  parts.

## 19. Acceptance criteria

- [ ] With `text`, the title shows the attribute value as plain text and hides the content.
- [ ] Without `text`, non-blank content is shown through the slot with its markup.
- [ ] Content that is only an `<img alt>` or an icon is shown; the `alt` (or `aria-label`) names the chart, a decorative icon leaves the name to `meta.title`.
- [ ] A bound `<mj-chart-data-table>` whose caption is the chart name follows a title change without a chart re-render.
- [ ] Without `text` and content, the title shows `meta.title` of the bound chart.
- [ ] `subtitle` is shown when non-empty; absent `subtitle` falls back to `meta.subtitle`; `subtitle=""` shows none.
- [ ] `level` 1–6 sets `role="heading"` and `aria-level` on the `title` part; other values remove them.
- [ ] Editing the content, or changing `text` / `subtitle` / `level`, updates the title without a reload.
- [ ] Binding works nested, by `chart` id, and when the chart is inserted or given its id after the title.
- [ ] Changing `chart` rebinds; the previous chart's meta-derived title is dropped.
- [ ] The bound chart's `aria-label` follows the title text when the chart has no `aria-label`, `label` or `title` attribute.
- [ ] Removing the title makes the chart recompute its name.
- [ ] When the chart's data fails or the chart is removed, meta-derived text disappears and attribute/content text remains.
- [ ] Nested in `<mj-chart>`, the title is drawn above the drawing regardless of source order.
- [ ] `chartLabel` returns the text currently shown.
- [ ] axe scan zero violations with and without `level`.
- [ ] Light, dark, high-contrast and RTL rendering verified.

## 20. Open questions

- Should `text=""` fall back to the content / `meta.title` instead of suppressing
  the title?
- Should the chart reference the title with `aria-labelledby` instead of copying
  its text into `aria-label`, to avoid the double reading when nested?
- Should the subtitle feed the chart's description when the chart has none?
- Should an empty title drop the heading role?
- Should the subtitle accept rich content (a named slot)?
- Should `text`, `subtitle` and `level` get reflecting properties?
