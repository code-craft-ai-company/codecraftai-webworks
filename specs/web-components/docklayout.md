# Dock Layout Spec

- **Tag:** `<mj-dock-layout>`
- **Class / file:** `MjDockLayout` / `mjdocklayout.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Dock panel, Docking container, Edge-docking layout, App-shell layout host
- **Phase:** P2
- **Status:** Implemented (this spec documents the shipped behavior of `mjdocklayout.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-dock-layout>` is a container that arranges its children by their `dock`
attribute. In DOM order, each child with `dock="top"`, `bottom`, `start` or `end`
takes a band along that edge of the space that is still free; children with
`dock="fill"` share the rectangle that is left. The geometry depends on order, so it
is computed in script by the docking engine in `core/anchoring.js` (`layoutDock`)
rather than by CSS. It is the host for the `dock` attribute every MjElement carries,
and it is also a positioning context for anchored children. App shells, inspector
panels and toolbar-plus-content regions are built from it. It is presentational: it
has no role, handles no keys and has no strings.

## 2. When to use / when not to use

Use it for a region with fixed bands (toolbar, status bar, side panels) around a
content area that takes the rest of the space, for nested regions (a dock layout
docked as `fill` or as a band of an outer one), and for responsive re-docking by
changing a child's `dock` at run time. Do not use it for a one-dimensional run of
items — use `<mj-stack>`; for a 2-D grid of items — use `<mj-grid>`; for regions the
user resizes — use `<mj-split-pane>` (which can itself be docked). It does not grow
to fit its content: it fills its container on both axes and clips overflow, so do
not use it where the page should scroll as a whole. Put scrolling content in a
`fill` `<mj-scroll-area>`.

## 3. Anatomy

- **Host element** — `display: block`, `position: relative` (the positioning context
  for docked and anchored children), `inline-size: 100%`, `block-size: 100%`,
  `overflow: hidden`, background `--mj-bg`. `box-sizing: border-box` comes from the
  shared base stylesheet.
- **Shadow tree** — a single default `<slot>`. There is no wrapper element and no
  `::part`.
- **Children** (light DOM), by role:
  - **Bands** — `dock="top"`, `bottom`, `start` or `end`.
  - **Fill** — `dock="fill"`.
  - **Undocked** — no `dock` attribute, or a value that is not one of the five
    edges; left in normal flow.
  - **Anchored** — undocked mj-* components with the common `anchor` attribute.
  - **`<slot>` children** — when the layout sits in another component's shadow root,
    a `<slot>` child stands for the elements assigned to it (flattened), so the
    layout docks content slotted into that component.

## 4. Variants & modes

There are no visual variants. The behavioral dimensions are:

| Mode                 | Attribute                                   | Description |
|----------------------|---------------------------------------------|-------------|
| No gap (default)     | (no `gap`)                                  | Bands touch each other and the fill area |
| Gap preset           | `gap="xs\|sm\|md\|lg\|xl"`                  | Space after every band and between fill children, from the spacing tokens |
| Nested as a band     | `dock="top\|bottom"` / `dock="start\|end"` on the layout | The layout resets `block-size` (top/bottom) or `inline-size` (start/end) to `auto`; the author gives it a size on that axis |
| Nested as fill       | `dock="fill"` on the layout                 | The outer layout sizes it on both axes |
| Right-to-left        | `dir="rtl"` or an inherited RTL direction   | `start` and `end` swap sides |

## 5. Attributes

| Attribute | Type                      | Default | Reflects | Description |
|-----------|---------------------------|---------|----------|-------------|
| `gap`     | `xs\|sm\|md\|lg\|xl`      | —       | No       | Space between bands and between fill children. `xs` → `--mj-space-1`, `sm` → `--mj-space-2`, `md` → `--mj-space-4`, `lg` → `--mj-space-5`, `xl` → `--mj-space-6`. Any other value (including `none` or a length such as `12px`) gives 0. `--mj-dock-gap` overrides every preset. A change schedules a layout pass. There is no `gap` property |

**Attributes read on the children**

| Attribute | On             | Description |
|-----------|----------------|-------------|
| `dock`    | any child element (mj-* or plain) | `top`, `bottom`, `start`, `end` or `fill`, matched exactly (case-sensitive). Any other value, including `left` / `right`, leaves the child undocked. A change on any child is observed and schedules a pass |
| `hidden`  | any child element | Observed on every child. A hidden (`display: none`) child consumes no space |

Common MjElement attributes (`anchor`, `theme`, `hidden`, `context-menu`) behave as
on every component. `dock` on the layout itself is covered in §4; `disabled` has no
meaning for the layout and does not block pointer input to its content (see §18).

## 6. Properties

No component-specific properties.

**Methods**

| Method            | Description |
|-------------------|-------------|
| `requestLayout()` | Schedules a layout pass on the next animation frame. Calls are coalesced: while a frame is pending, further calls do nothing. Ignored while the layout is not connected. Use it after changes the layout cannot observe (§11) |

## 7. Slots

| Slot      | Description |
|-----------|-------------|
| (default) | The children: bands, fill children, undocked and anchored children, and `<slot>` children whose assigned elements are laid out in their place |

## 8. Events

| Event       | `detail`                         | Bubbles | Composed | Cancelable | Description |
|-------------|----------------------------------|---------|----------|------------|-------------|
| `mj-layout` | `{ container: MjDockLayout }` (the layout element) | No | Yes | No | Fires at the end of every scheduled pass that laid the children out, at most once per animation frame. A pass that finds the layout not rendered (0 × 0) changes nothing and fires nothing |

Because the event does not bubble, listen on the layout element itself. The layout
does not touch its children's own events.

## 9. CSS parts & custom properties

**Parts**

None. The shadow tree holds only the default slot.

**Custom properties**

| Property | Description |
|---|---|
| `--mj-dock-gap` | Gap between bands and between fill children. When set it wins over the `gap` attribute. Fallback: `0` without `gap`; `--mj-space-1` / `--mj-space-2` / `--mj-space-4` / `--mj-space-5` / `--mj-space-6` for `gap="xs"` / `sm` / `md` / `lg` / `xl`. It inherits, so it also reaches nested layouts |

Other styling hooks:
- The host background is the global `--mj-bg` token.
- The CSS `gap`, `row-gap` and `column-gap` properties set on the element from the
  page override the `:host` rules. `row-gap` follows `top` / `bottom` bands;
  `column-gap` follows `start` / `end` bands and separates fill children.
- Padding on the layout insets every band and the fill area.
- Anchored children use the base-stylesheet tokens `--mj-anchor-inset` (default 0)
  and `--mj-layer-docked` (their `z-index`).

## 10. States

| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| default | Bands and fill children placed; overflow clipped | — |
| empty (no docked children) | A blank block in `--mj-bg`; undocked children in normal flow | — |
| collapsed (a definite size on one axis only) | Docked children clipped; one console warning (§11) | — |
| not rendered (0 × 0, e.g. inside `display: none`) | A pass changes nothing and `mj-layout` does not fire; the first size change after it is shown runs a pass | — |
| hidden | `display: none` (base rule) | Removed from the accessibility tree |

## 11. Behavior & interactions

**Layout pass** (`layoutDock` in `core/anchoring.js`)

1. Measure the layout's padding box (`clientWidth` / `clientHeight`, refined with the
   computed size to keep fractions). When both are 0 nothing is touched.
2. The free rectangle starts at the padding edges, so padding insets the layout.
   `start` / `end` resolve against the layout's computed `direction`.
3. The dock children are the element children in DOM order, with each `<slot>` child
   replaced by its flattened assigned elements. A child is docked when its `dock`
   value is one of the five edges.
4. Children docked by this layout in the previous pass that are no longer docked are
   released (see "Inline styles" below).
5. Each docked child, in DOM order:
   - `display: none` — consumes nothing.
   - `fill` — deferred until all bands are placed.
   - a band — gets `position: absolute`, `box-sizing: border-box`, its offsets from
     the current free rectangle, and its **cross size**: the width of a `top` /
     `bottom` band, the height of a `start` / `end` band, set to the free extent minus
     the child's margins. The size along the consumed axis is the author's (`height`
     for top/bottom, `width` for start/end, inline or from a stylesheet) or the
     content size. The child's border box is then measured and the free edge moves by
     that size plus its margins plus the gap (`row-gap` for top/bottom, `column-gap`
     for start/end).
6. Fill children share the remaining rectangle side by side along the inline axis, in
   equal slices of `(free width − column-gap × (n − 1)) / n`, starting at the start
   side. Each gets the full remaining height. A child's margins are subtracted from
   its own slice and height. Fill children are placed after all bands wherever they
   appear in DOM order.
7. The resulting container size and child boxes are recorded, so the resize observer
   can tell the engine's own writes from real changes.

Lengths are written in pixels rounded to 1/100 px. Free extents never go below 0.

**Consequences of DOM order.** A `top` band declared before a `start` band spans the
full width and the start band sits below it; declared after it, the start band is
full-height and the top band spans only the remaining width.

**Inline styles.** The engine writes inline `position`, `box-sizing`, `top` or
`bottom`, `inset-inline-start` or `inset-inline-end`, and `width` and/or `height`.
The first time it writes a property it saves the author's inline value (and
priority). When a child changes edge, the properties the new edge does not write are
restored. When a child stops being docked (its `dock` removed or invalid, or it is
removed from the layout) every saved property is restored. A child moved into
another dock layout is released by the old one before the new one claims it.

**When a pass runs.** A pass is scheduled by:
- connecting the layout;
- a size change of the layout or of any dock child (`ResizeObserver`), but only when
  the layout's padding box, or a docked child's border box or visibility, differs
  from what the last pass left;
- children added or removed (`MutationObserver` on the layout);
- a `dir` attribute change on the layout itself;
- a `dock` or `hidden` attribute change on any dock child, mj-* or plain (an mj-*
  child also reports its `dock` changes, connection and removal through MjElement's
  `registerDockChild` / `unregisterDockChild`, which find the layout as described
  in §17);
- `slotchange` from a `<slot>` child;
- a `gap` attribute change;
- a locale change (MjElement renders the layout again, which reconnects it);
- `requestLayout()`.

Requests are coalesced into one pass on the next animation frame. When the layout
leaves the document its pending frame is cancelled and all observers are
disconnected. Its children keep the inline styles of the last pass until the layout
runs again.

**Not observed** (call `requestLayout()`): a change of the CSS `gap`, `row-gap`,
`column-gap` or `--mj-dock-gap`, of the layout's padding, of a child's margins, a
`direction` change that comes from an ancestor or from CSS, and a `dir` change on a
child. None of these changes a size the observers watch.

**Undocked children** stay in normal flow at the start of the padding box. Docked
children are absolutely positioned, so they paint above them.

**Anchored children.** The base stylesheet positions an mj-* component with
`anchor` absolutely with `z-index: var(--mj-layer-docked)`, so it is placed against
the layout's padding box (not the free rectangle) and above the bands. Plain
elements with `anchor` are not positioned; the rule exists only on mj-* hosts.

**Collapsed warning.** After a pass, when the layout has a direct child with a
`dock` attribute and exactly one of its client width and height is 0, it logs once
per instance:
`[mj-dock-layout] The layout has no {height|width}, so its docked children are
clipped. Give it a {height|width}, or place it in a container that has one.`

## 12. Keyboard interaction

N/A. The layout handles no keys and is not focusable; focus moves through the
children in DOM order. The inherited context-menu keys apply only when a context
menu is configured.

## 13. Accessibility

- No role and no ARIA. The shadow tree is just a slot, so the children appear
  directly in the accessibility tree.
- Landmarks are the children's job: use `header` / `nav` / `main` / `aside` /
  `footer` elements, or components that provide them (`<mj-toolbar label>`,
  `<mj-side-nav>`, `<mj-status-bar>`, a labelled `<mj-scroll-area>`).
- Reading order and focus order follow DOM order, and DOM order also decides which
  band claims space first. Visual order can therefore differ from reading order (a
  full-width status bar must be declared before the side panels, so it is also read
  before them). Authors choose an order that serves both (WCAG 1.3.2, 2.4.3).
- Bands keep their size when the layout shrinks and the fill area can shrink to 0.
  The layout does not adapt by itself; for reflow (WCAG 1.4.10) the author hides
  bands or re-docks them at narrow widths.
- Overflow is clipped. Content that may not fit must sit in a scroll container that
  keyboard users can reach, usually a `fill` `<mj-scroll-area>`.
- A `hidden` child (or one with `display: none` from a stylesheet) is removed from
  the accessibility tree as well as from the layout.

## 14. Form participation

N/A. `<mj-dock-layout>` is not form-associated and contributes no value.

## 15. Internationalization & RTL

- No localizable strings and no `t()` keys. The collapsed warning is a developer
  console message in English.
- `start` and `end` follow the layout's computed `direction`: in RTL `start` is the
  right edge. Inline padding and child margins are mapped the same way.
- When a child's direction differs from the layout's (a `dir="ltr"` panel in an RTL
  layout), the engine writes the opposite logical inset so the child still docks on
  the layout's start or end side.
- Fill children are laid out from the start side (right to left in RTL).
- A `dir` change on the layout triggers a pass; a direction change inherited from an
  ancestor does not (call `requestLayout()`).
- A locale change renders the layout again, which runs one pass and fires one
  `mj-layout`.

## 16. Progressive enhancement / SSR

Server renders the layout and its children with their `dock` attributes. Before
upgrade `mj-dock-layout` is an unknown inline element: the children render in normal
flow in DOM order, nothing is clipped, and the content is readable. On upgrade the
host styles apply at once, but the children stay in normal flow until the first pass
on the next animation frame. A page that wants to avoid that frame can style
`mj-dock-layout:not(:defined)`. The engine's inline styles are written only on the
client; server markup should not contain them.

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `onConnected`,
  `onAttributeChanged`, `listen`, `onTeardown`, `emit`); MjElement calls
  `registerDockChild` / `unregisterDockChild` for docked mj-* children. They find the
  layout the way `getDockChildren` sees the child: the child's parent when that is
  an `mj-dock-layout`, otherwise the layout whose `<slot>` child the child is
  (transitively) assigned to; the slot of the layout's own shadow root is never the
  match
- **Docking engine** — `core/anchoring.js`: `getDockChildren`, `layoutDock`,
  `isDockLayoutStale`
- **Design-token stylesheet** (§6) — `--mj-bg`, `--mj-space-*`; base-stylesheet rules
  for `:host([dock])`, `:host([dock="fill"])` and `:host([anchor])`
- **Platform** — `ResizeObserver` (used when available; without it size changes are
  not observed), `MutationObserver`, `requestAnimationFrame`
- Consumers: components that reset their host size per dock edge so they can be
  bands (`<mj-split-pane>`, `<mj-master-detail>`, `<mj-file-browser>`,
  `<mj-diagram>`, `<mj-dock-layout>` itself); the catalog examples also dock
  `<mj-toolbar>`, `<mj-status-bar>`, `<mj-side-nav>`, `<mj-app-bar>` and
  `<mj-scroll-area>`

## 18. Edge cases & error handling

- No definite size: `block-size: 100%` of a parent without a definite height
  resolves to the in-flow content height. Docked children are absolutely positioned
  and contribute none, so the layout is 0 high, the children are clipped and the
  collapsed warning is logged.
- A layout nested as a `top` / `bottom` (or `start` / `end`) band has `block-size`
  (or `inline-size`) `auto`; without an author size on that axis it collapses the
  same way.
- Unrecognized `dock` values (`left`, `right`, `Top`, `center`) leave the child
  undocked, in normal flow.
- More bands than fit: free extents stop at 0, later bands get a cross size of 0, and
  the overflow is clipped.
- No `fill` child: the remaining rectangle shows the layout background.
- A hidden child consumes no space; the inline styles of the last pass stay on it
  while it is hidden.
- `!important` rules in a stylesheet on a property the engine writes (for example
  `width` on a `top` band) beat the engine's inline value and break the layout.
  Non-important stylesheet values on those properties are overridden while docked.
- `box-sizing: border-box` is forced on docked children, so an author `height` on a
  band includes its padding and border.
- `dock` and `anchor` on the same child: the engine's inline offsets and the anchor
  insets both apply; the result is not defined.
- `--mj-dock-gap` set on an outer layout is inherited by nested layouts.
- `gap` with a length value (`gap="12px"`) is ignored; use the CSS `gap` property or
  `--mj-dock-gap`.
- `disabled` on the layout: ignored. The layout overrides the base control rule
  with `:host([disabled]) { pointer-events: auto; cursor: auto }`, so its content
  keeps receiving pointer input; disable the controls inside instead.
- A pass scheduled while the layout is not rendered (0 × 0) does nothing and emits
  no `mj-layout`.
- The collapsed warning checks only direct children with any `dock` attribute (not
  slot-assigned children, and not only valid values), and it is logged at most once
  per instance.

## 19. Acceptance criteria

- [ ] A `top` band is absolutely positioned at the top of the padding box, spans the free width, and keeps its author height.
- [ ] `bottom`, `start` and `end` bands consume their edges in DOM order; a later band starts where the earlier ones ended.
- [ ] `fill` children share the remaining rectangle in equal slices along the inline axis, separated by `column-gap`.
- [ ] Child margins and layout padding are honored.
- [ ] `gap="xs|sm|md|lg|xl"` maps to the documented tokens; other values give 0; `--mj-dock-gap` overrides all of them.
- [ ] In RTL, `start` docks on the right and `end` on the left; a child with a different `dir` still docks on the layout's side.
- [ ] Changing a child's `dock`, setting `hidden`, adding or removing a child, and resizing the layout or a docked child each produce one pass.
- [ ] Undocking or removing a child restores the inline values the author had.
- [ ] Several requests in one frame produce one pass and one `mj-layout`.
- [ ] A requested pass on a layout inside `display: none` emits no `mj-layout`.
- [ ] `registerDockChild` on a docked child (direct or slot-assigned) schedules a pass on its layout.
- [ ] `disabled` on the layout does not stop pointer input to its children.
- [ ] `mj-layout` has `detail.container === layout`, does not bubble, is composed and is not cancelable.
- [ ] `requestLayout()` while disconnected does nothing; disconnecting cancels a pending pass.
- [ ] A layout with width but no height logs the collapsed warning once.
- [ ] Children of a `<slot>` child are laid out in its place.
- [ ] Undocked children stay in flow; anchored mj-* children are pinned to the layout's padding box above the bands.
- [ ] axe scan zero violations for the catalog app-shell example.
- [ ] Light, dark, high-contrast and RTL rendering verified.

## 20. Open questions

- Should the layout observe direction changes from ancestors and CSS gap / padding /
  margin changes, or keep relying on `requestLayout()`?
- Should consumption order be separable from DOM order (for example a priority
  attribute), so reading and focus order need not follow the docking order?
- Should docked children be released (inline styles restored) when the layout
  leaves the document?
- Should the collapsed warning cover slot-assigned children and valid `dock` values
  only, and be re-armed after the size is fixed?
- Should the gap presets accept `none` explicitly and reflect through a `gap`
  property?
- The plan does not list a dock layout by name; P2 was assigned with Split pane,
  Scroll area and AppShell, which it hosts. Confirm the phase.
