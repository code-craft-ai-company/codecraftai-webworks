# Sort Control Spec

- **Tag:** `<mj-sort-control>`
- **Class / file:** `MjSortControl` / `mjsortcontrol.js`
- **Category:** Tables, lists & structured data (§5.8)
- **Primary or Variant:** Primary
- **Synonyms covered:** Sort control, Sort toggle, Sortable header button, Sort indicator
- **Phase:** P1
- **Status:** Implemented (this spec documents the shipped behavior of `mjsortcontrol.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-sort-control>` is a button that shows and changes the sort direction of one
named field. Each activation steps the direction through a cycle (by default
`none` → `asc` → `desc` → `none`) and emits `mj-sort-change` so the host (a data
table, list view, card grid, ...) can re-sort its data. It is one of the DataTable
companion controls of plan §5.8 ("Sort control exposes current sort"), but it is
independently placeable: it works wherever it is put, not only inside a table
header. It does not sort anything itself.

## 2. When to use / when not to use

Use for a sortable column header or a "sort by" button above a list, card grid or
search results, where the user toggles the direction of one field at a time.
Several controls that sort the same dataset share a `group` so only one of them is
active. Do not use it to pick the sort field from a list of fields — use
`<mj-select>` / `<mj-segmented-control>` (or the `sort-control` part of
`<mj-filter-panel>`). `<mj-data-table>` and `<mj-tree-grid>` render their own
sortable headers and do not need it. Do not use it as a generic on/off toggle —
use `<mj-toggle-button>`.

## 3. Anatomy

- **Host element** — `display: inline-flex`; no surface of its own.
- **button (part)** — the inner native `<button type="button">`; the only focusable
  target. It carries `aria-label` and `aria-pressed`.
- **label (part)** — wrapper around the default slot holding the visible field label.
- **indicator (part)** — decorative icon after the label: a double arrow for `none`,
  an up triangle for `asc`, a down triangle for `desc`. The icons are inline SVGs
  with `aria-hidden="true"` and are not slottable.

## 4. Variants & modes

There are no visual variants. The behavioral dimensions are:

| Mode                 | Attribute                     | Description |
|----------------------|-------------------------------|-------------|
| Three-state (default)| (no `cycle`)                  | `none` → `asc` → `desc` → `none` |
| Custom cycle         | `cycle="asc-desc"`, `cycle="desc-asc-none"`, ... | Directions and their order; two-state cycles never return to `none` |
| Grouped (single sort)| `group="<name>"`              | Activating one control resets the other members of the group to `none` |
| Standalone           | (no `group`)                  | Each control keeps its own direction |

## 5. Attributes

| Attribute     | Type                         | Default  | Reflects | Description |
|---------------|------------------------------|----------|----------|-------------|
| `field`       | string                       | `""`     | Yes      | Field the control sorts; sent as `detail.field`. Also the fallback accessible label |
| `direction`   | `none\|asc\|desc`            | `none`   | Yes      | Current direction. Set to `none` on first render when absent. Any other value reads as `none` |
| `cycle`       | dash-separated directions    | `none-asc-desc` | No | Steps and their order, e.g. `asc-desc`, `desc-asc-none`. Tokens are trimmed and lower-cased; unknown and repeated tokens are dropped; fewer than two usable tokens falls back to the default |
| `group`       | string                       | —        | No       | Controls with the same `group` in the same document or shadow root form a single-sort set |
| `label`       | string                       | —        | No       | Field label used in the accessible name. Defaults to the trimmed text content, then to `field` |
| `label-none`  | string template              | —        | No       | Accessible-name template while `direction="none"`; `{label}` is replaced by the field label |
| `label-asc`   | string template              | —        | No       | Accessible-name template while `direction="asc"` |
| `label-desc`  | string template              | —        | No       | Accessible-name template while `direction="desc"` |
| `disabled`    | boolean                      | `false`  | Yes      | Blocks activation and disables the inner button |

Common MjElement attributes (`dock`, `anchor`, `theme`, `hidden`, `context-menu`)
behave as on every component.

## 6. Properties

| Property    | Type                        | Description |
|-------------|-----------------------------|-------------|
| `field`     | `string`                    | Reflects `field`; the setter stores `String(value)` |
| `direction` | `'none'\|'asc'\|'desc'`     | Reflects `direction`; reading an unknown value returns `'none'`; setting an unknown value stores `'none'`. Setting it does not emit an event |
| `disabled`  | `boolean`                   | Reflects `disabled`; only `true` sets the attribute, any other value removes it |

**Methods**

| Method    | Description |
|-----------|-------------|
| `reset()` | Sets `direction` to `none` without emitting `mj-sort-change`. For hosts that sort under their own control and need the UI to match without an echo event |

## 7. Slots

| Slot      | Description |
|-----------|-------------|
| (default) | Visible field label. Its text is also the default field label of the accessible name; a `slotchange` rebuilds the name |

## 8. Events

| Event            | `detail`                                                           | Bubbles | Composed | Cancelable | Description |
|------------------|--------------------------------------------------------------------|---------|----------|------------|-------------|
| `mj-sort-change` | `{ field: string, direction: 'none'\|'asc'\|'desc', previousDirection: 'none'\|'asc'\|'desc' }` | Yes | Yes | No | Fires after each user activation, once `direction` (and the group reset) has been applied |

Group members reset by another control's activation, `reset()`, and setting
`direction` by attribute or property do not emit an event.

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<button>`
- `::part(label)` — label wrapper around the default slot
- `::part(indicator)` — direction icon wrapper

**Custom properties**
| Property | Description |
|---|---|
| `--mj-sort-control-color` | Text color (default `--mj-text`) |
| `--mj-sort-control-color-active` | Text color while sorted (default `--mj-accent`) |
| `--mj-sort-control-bg` | Background (default transparent) |
| `--mj-sort-control-bg-hover` | Hover background (default `--mj-bg-muted`) |
| `--mj-sort-control-bg-active` | Background while sorted (default `--mj-bg-muted`) |
| `--mj-sort-control-border-color` | Border color (default transparent) |
| `--mj-sort-control-border-radius` | Corner radius (default `--mj-radius-sm`) |
| `--mj-sort-control-height` | Minimum height (default `--mj-control-height-sm`) |
| `--mj-sort-control-font-weight` | Label weight (default `--mj-font-weight-medium`) |
| `--mj-sort-control-icon-size` | Indicator size (default `0.875rem`) |
| `--mj-sort-control-indicator-color` | Indicator color (default `currentColor`) |
| `--mj-sort-control-focus-ring-color` | Focus ring color (default `--mj-focus-ring`) |

## 10. States

| State          | Visual effect | ARIA effect |
|----------------|---------------|-------------|
| none           | Resting colors; double-arrow indicator at 45 % opacity | `aria-pressed="false"` |
| asc            | Active background and color; up-triangle indicator | `aria-pressed="true"` |
| desc           | Active background and color; down-triangle indicator | `aria-pressed="true"` |
| hover          | `--mj-sort-control-bg-hover` background | — |
| focus-visible  | Focus ring on the inner button | — |
| disabled       | 55 % opacity; `pointer-events: none` on the host | Inner button gets the native `disabled` attribute |

## 11. Behavior & interactions

- Activation (click, or Enter / Space through the native button) does nothing while
  `disabled` is set. Otherwise it computes the next direction, sets `direction`,
  resets the group siblings when the new direction is not `none`, then emits
  `mj-sort-change`.
- Next direction: the step after the current one in the cycle, wrapping around.
  When the current direction is not part of the cycle, the next direction is the
  first step of the cycle — or the second step when the first is `none`, so
  activation always moves to a sorted state.
- Group reset: every other `mj-sort-control[group]` with the same `group` value in
  the control's root node (`getRootNode()`: the document or the enclosing shadow
  root) whose direction is not `none` is set to `none`, silently. Controls in other
  roots are not affected.
- Every attribute change, and every `slotchange` of the default slot, re-syncs the
  indicator icon, `aria-label`, `aria-pressed` and the inner button's `disabled`.
- The component keeps no sort state beyond the `direction` attribute; the host owns
  the data and the actual sorting.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Enter`     | Activates: steps to the next direction (native button behavior) |
| `Space`     | Activates: steps to the next direction (native button behavior) |
| `Tab`       | Moves focus to the next focusable element |
| `Shift+Tab` | Moves focus to the previous focusable element |

There is no custom key handling; a disabled control is not focusable.

## 13. Accessibility

- Role: native `<button>`. `aria-pressed` is `"true"` while sorted (`asc` / `desc`)
  and `"false"` for `none`.
- `aria-label` names the field, the current state and what the next activation does.
  The field label is `label`, else the trimmed text content, else `field`. The
  default (English) names are, for current → next direction:
  - none → asc: "Sort by {label}, not sorted. Activate to sort ascending."
  - none → desc: "Sort by {label}, not sorted. Activate to sort descending."
  - asc → desc: "Sort by {label}, sorted ascending. Activate to sort descending."
  - asc → none: "Sort by {label}, sorted ascending. Activate to clear sort."
  - desc → asc: "Sort by {label}, sorted descending. Activate to sort ascending."
  - desc → none: "Sort by {label}, sorted descending. Activate to clear sort."
- The default names begin with the visible label, satisfying WCAG 2.5.3 (Label in
  Name). An author template from `label-*` replaces the default for that direction
  and should keep the visible label in it.
- The name is updated on every direction change, so a screen reader re-reads the new
  state on the focused button. The component does not use a live region.
- The indicator SVGs are `aria-hidden="true"`; state is conveyed by `aria-pressed`
  and the name.
- When the control sits in a table header, the host should still set `aria-sort` on
  the header cell; the control does not do this.

## 14. Form participation

N/A. `<mj-sort-control>` is not form-associated.

## 15. Internationalization & RTL

- The six default accessible-name templates are read through `t()` from
  `core/intl.js` at sync time (keys `mj.sortControl.labelNoneToAsc`,
  `mj.sortControl.labelNoneToDesc`, `mj.sortControl.labelAscToDesc`,
  `mj.sortControl.labelAscToNone`, `mj.sortControl.labelDescToAsc`,
  `mj.sortControl.labelDescToNone`), so `setLocale()` / `registerStrings()` apply
  on the next sync.
- `label-none`, `label-asc` and `label-desc` override the default template for their
  direction and win over the string table.
- The visible label comes from the default slot and is not managed by the component.
- Layout uses inline flex with a gap, so the indicator follows the label in the
  inline direction and mirrors in RTL. The arrow glyphs point up/down and are not
  mirrored.

## 16. Progressive enhancement / SSR

Server renders `<mj-sort-control field="name" direction="asc">Name</mj-sort-control>`.
Before upgrade the label text shows as inline content with no indicator and no
interaction. On upgrade the shadow button, indicator and accessible name appear, and
the server-rendered `direction` is kept. A host that sorts on the server should
render the matching `direction` so the indicator is correct on first paint.

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `afterRender`,
  `onAttributeChanged`, `listen`, `emit`, docking / anchoring)
- **Design-token stylesheet** (§6)
- **Localization hook** (§6) — `t()` for the default accessible-name templates
- Consumers: hosts that sort lists or tables; `<mj-filter-panel>` exposes a
  `sort-control` part for the same purpose

## 18. Edge cases & error handling

- Unknown `direction` value: the property reads `none`, the none icon and
  `aria-pressed="false"` are shown; the attribute value itself is left as written
  (so the `:host([direction="none"])` dimming does not apply until the next change).
- `cycle` with fewer than two usable tokens (empty, `"asc"`, `"foo-bar"`, `"asc-asc"`):
  the default three-state cycle is used.
- Current direction not in `cycle` (e.g. `direction="none"` with `cycle="asc-desc"`):
  activation moves to the first sorted state of the cycle.
- No label, no text content and no `field`: the `{label}` token is replaced by an
  empty string.
- `group` set but empty: treated as no group.
- Group members inside a different shadow root than the activated control are not
  reset.
- Activating to `none` (clearing the sort) does not touch the group siblings.
- `mj-sort-change` is not cancelable: `direction` has already changed when the event
  fires. A host that rejects a sort sets `direction` back or calls `reset()`.

## 19. Acceptance criteria

- [ ] Without `direction`, the control renders with `direction="none"` reflected.
- [ ] Activation steps `none` → `asc` → `desc` → `none` by default.
- [ ] `cycle="asc-desc"` alternates `asc` / `desc`; `cycle="desc-asc-none"` starts with `desc`.
- [ ] Invalid or too-short `cycle` values fall back to the default cycle.
- [ ] `mj-sort-change` fires once per activation with `field`, `direction`, `previousDirection`; it bubbles and is composed.
- [ ] `direction` set by attribute/property, `reset()`, and group resets emit no event.
- [ ] Activating one member of a `group` resets the other members in the same root to `none`.
- [ ] `aria-pressed` is `true` for `asc` / `desc` and `false` for `none`.
- [ ] `aria-label` matches the default template for each current → next pair, using `label`, text content or `field`.
- [ ] `label-none` / `label-asc` / `label-desc` replace the default name, with `{label}` substituted.
- [ ] Changing the slotted text updates the accessible name.
- [ ] `disabled` blocks activation and disables the inner button.
- [ ] Enter and Space activate; no other keys are handled.
- [ ] Indicator icon matches the direction and is `aria-hidden`.
- [ ] axe scan zero violations in each direction and when disabled.
- [ ] Light, dark, high-contrast and RTL rendering verified.

## 20. Open questions

- Should an unknown `direction` value be normalized on the attribute (as the property
  setter does), so the `none` styling applies?
- Should activation emit a cancelable request event before changing `direction`, as
  `<mj-disclosure-button>` does with `mj-change`?
- Should group resets reach controls in other shadow roots of the same host (for
  example, header cells rendered by a table into its own shadow tree)?
- Should the control optionally set `aria-sort` on an enclosing `columnheader`?
- Should multi-column sort (sort priority badges, Shift+activation) be supported, or
  left to `<mj-data-table>`?
