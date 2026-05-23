# Column Picker Spec

- **Tag:** `<mj-column-picker>`
- **Class / file:** `MjColumnPicker` / `mjcolumnpicker.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Column picker, Column visibility toggle, Show/hide columns
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-column-picker>` is a companion control for `<mj-data-table>` and
`<mj-tree-grid>` that lets users toggle column visibility and reorder columns
via a checkbox list in a dropdown panel. Changes are emitted as events so the
host grid can update its column definition without the picker having a direct
reference to the grid. It may also be used as a standalone column management
panel when placed in a toolbar.

## 2. When to use / when not to use
**Use** alongside `<mj-data-table>` or `<mj-tree-grid>` whenever users need
to show/hide or reorder columns dynamically. **Do not use** when the column set
is fixed and non-configurable. For filter-based column content management use
`<mj-data-table>`'s built-in filter controls.

## 3. Anatomy
- **Trigger button** — `<button>` with icon and label; opens the picker panel; `aria-haspopup="dialog"` or `"listbox"`.
- **Panel** — `<div role="dialog">` or popover anchored to the trigger; contains the column list.
- **Column list** — `<ul role="list">` of column items; each item has a checkbox, a drag handle, and a column label.
- **Checkbox** — native `<input type="checkbox">` (or `role="checkbox"`) controlling column visibility.
- **Drag handle** — for reordering columns in the panel; same keyboard grab/move/drop pattern as `<mj-data-table>` column reorder.
- **Reset button** — restores columns to the default configuration.
- **Apply button** (optional) — in "apply on close" mode, commits changes only when pressed.

## 4. Variants & modes
| Variant | `apply-mode` value | Behavior |
|---------|--------------------|----------|
| Immediate | `immediate` (default) | Each checkbox toggle fires `mj-column-visibility-change` instantly. |
| Deferred | `deferred` | Changes accumulate; `mj-columns-apply` fires only when the Apply button is pressed. |

Trigger appearance via `variant`: `icon-button` (default, columns icon only) | `button` (icon + "Columns" label).

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `apply-mode` | `immediate\|deferred` | `immediate` | yes | When column changes are emitted. |
| `variant` | `icon-button\|button` | `icon-button` | yes | Trigger button appearance. |
| `label` | string | `"Columns"` | yes | Accessible label for the trigger button and panel. |
| `open` | boolean | false | yes | Controls panel open/close state. |
| `disabled` | boolean | false | yes | Disables the trigger button. |
| `reorderable` | boolean | true | yes | Enables drag-to-reorder within the panel. |
| `min-visible` | number | `1` | yes | Minimum number of columns that must remain visible; prevents hiding the last column. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `columns` | `PickerColumn[]` | `{ key: string, label: string, visible: boolean, locked?: boolean, order: number }` — current column configuration including visibility and order. |
| `defaultColumns` | `PickerColumn[]` | The original column configuration; used by the Reset button. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `trigger` | Custom trigger element; replaces the default icon button. |
| `panel-header` | Content at the top of the picker panel (above the column list). |
| `panel-footer` | Content at the bottom of the panel (below the Reset button). |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-column-visibility-change` | `{ key: string, visible: boolean, columns: PickerColumn[] }` | true | false | A column's visibility was toggled (immediate mode). |
| `mj-column-reorder` | `{ key: string, from: number, to: number, columns: PickerColumn[] }` | true | false | A column was moved to a new order position within the panel. |
| `mj-columns-apply` | `{ columns: PickerColumn[] }` | true | false | User pressed Apply in deferred mode; full column state emitted. |
| `mj-columns-reset` | `{ columns: PickerColumn[] }` | true | false | User pressed Reset; columns reverted to `defaultColumns`. |
| `mj-picker-open` | `{}` | true | false | Panel opened. |
| `mj-picker-close` | `{}` | true | false | Panel closed. |

## 9. CSS parts & custom properties
**Parts:** `trigger-button`, `panel`, `panel-header`, `column-list`, `column-item`,
`column-checkbox`, `column-label`, `column-drag-handle`, `reset-button`,
`apply-button`, `panel-footer`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-cp-panel-width` | `240px` | Width of the dropdown panel. |
| `--mj-cp-panel-max-height` | `360px` | Max height before panel scrolls. |
| `--mj-cp-item-height` | `36px` | Height of each column item row. |
| `--mj-cp-drag-handle-color` | `token(--mj-color-text-subtle)` | Drag handle icon color. |
| `--mj-cp-checked-color` | `token(--mj-color-primary)` | Checkbox accent color. |

## 10. States
- **closed** — trigger button visible; panel hidden.
- **open** — panel visible; focus moved to first interactive element in panel.
- **column-visible** — checkbox checked; eye icon shown.
- **column-hidden** — checkbox unchecked; column label dimmed.
- **column-locked** — `locked` column: checkbox disabled (`aria-disabled="true"`); always visible; no drag handle.
- **dragging** — column item being reordered; `aria-grabbed="true"` on drag handle.
- **pending** (deferred mode) — changes made but not yet applied; Apply button enabled.
- **disabled** — trigger button `disabled`; `aria-disabled="true"`.

## 11. Behavior & interactions
**Panel positioning:** The panel is anchored below the trigger button using the
shared overlay/positioning engine (flip to top if insufficient space below). It is
light-dismissed on click outside or `Escape`. Focus is moved to the first checkbox
in the panel on open and restored to the trigger on close.

**Column visibility toggle:** Each `<input type="checkbox">` controls one column.
In `immediate` mode, the `change` event on the checkbox immediately fires
`mj-column-visibility-change`. In `deferred` mode, the checkbox state is tracked
internally and emitted only on Apply. The component enforces `min-visible`: if
toggling a checkbox would hide all visible columns and `min-visible=1`, the
checkbox is blocked and an error tooltip explains why.

**Reorder within the panel:** Drag handle operates identically to column reorder
in `<mj-data-table>`: pointer drag or keyboard grab (`Space`) + `ArrowUp`/`Down`
+ `Enter`/`Escape`. `mj-column-reorder` fires immediately in both apply modes
(column order changes are always immediate to keep the panel in sync with visual
feedback).

**Reset:** Pressing the Reset button restores `columns` to `defaultColumns`
(reverting visibility and order). `mj-columns-reset` fires. In deferred mode this
also clears pending changes.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` / `Space` on trigger | Open/close panel. |
| `Escape` | Close panel; restore focus to trigger. |
| `Tab` / `Shift+Tab` | Move focus through checkboxes, drag handles, Reset, Apply. |
| `Space` on checkbox | Toggle column visibility. |
| `Space` on drag handle | Grab column item for keyboard reorder. |
| `ArrowUp / Down` (grabbed item) | Move column item up/down in the list. |
| `Enter` (grabbed item) | Confirm reorder position; fire `mj-column-reorder`. |
| `Escape` (grabbed item) | Cancel reorder; return item to original position. |
| `Enter` on Apply button | Commit deferred changes; fire `mj-columns-apply`; close panel. |
| `Enter` on Reset button | Reset to default; fire `mj-columns-reset`. |

## 13. Accessibility
- Trigger button: `aria-haspopup="dialog"`, `aria-expanded` reflects open state, `aria-label` from `label` attribute.
- Panel: `role="dialog"`, `aria-label="{label} picker"`, `aria-modal="true"`.
- Column list: `role="list"`.
- Column items: `role="listitem"`.
- Checkboxes: native `<input type="checkbox">`; `aria-label="{column label}"`.
- Locked columns: checkbox `disabled` + `aria-describedby` pointing to a tooltip explaining it is always visible.
- Drag handle: `role="button"`, `aria-label="Reorder {column label}"`, `aria-grabbed`.
- Live region: announces "Column {label} hidden" / "shown" on each toggle; "Columns reordered" after drag.
- Focus trap: focus remains within the panel while open; Tab does not leave the dialog.
- `min-visible` enforcement: when blocking a hide, an `aria-live="assertive"` announcement says "At least one column must remain visible."

## 14. Form participation
N/A — the picker is a configuration control, not a form field. The host grid's
column state is managed externally by reacting to emitted events.

## 15. Internationalization & RTL
- In RTL, the panel anchors to the right edge of the trigger; drag handle on the right side of each item.
- All strings (`label`, Reset/Apply button labels, live region strings) are overridable via attributes.
- Column labels are caller-supplied and must be pre-translated.

## 16. Progressive enhancement / SSR
Without JS the trigger button is rendered as a `<details>/<summary>` disclosure
revealing the column list with native checkboxes. On upgrade the component replaces
the disclosure with the positioned panel and attaches the drag-reorder logic.

## 17. Dependencies
- Overlay/positioning engine (§6) — panel anchoring, flip, light-dismiss.
- Focus utilities — focus trap within the dialog panel (§6).
- Live-region/announcement service (§6).
- Design-token stylesheet (§6).
- Base element helper (§6).
- `<mj-button>` for trigger, Reset, and Apply buttons.

## 18. Edge cases & error handling
- **All columns hidden attempt** — blocked when `min-visible` would be violated; live region explains.
- **`columns` property updated externally while panel is open** — panel re-renders column list; pending deferred changes reset.
- **Zero columns** — trigger button disabled with `aria-disabled`; panel not openable.
- **Single column** — checkbox for that column disabled (always the only visible column).
- **Very long column labels** — truncated with ellipsis; full label in `title` and `aria-label`.
- **Panel overflow** — panel scrolls vertically within `--mj-cp-panel-max-height`.

## 19. Acceptance criteria
- [ ] Trigger button opens/closes panel; `aria-expanded` reflects state; `aria-haspopup="dialog"`.
- [ ] Panel: `role="dialog"`, `aria-modal="true"`, focus moved in on open, restored to trigger on close.
- [ ] Each column item has a native checkbox; toggle fires `mj-column-visibility-change` in immediate mode.
- [ ] Deferred mode: changes held until Apply pressed; `mj-columns-apply` fires with full state.
- [ ] `min-visible` blocks hiding the last visible column; live region announces reason.
- [ ] Locked columns: checkbox disabled; no drag handle.
- [ ] Reorder within panel: drag (pointer) and keyboard (Space+Arrows+Enter/Esc); `mj-column-reorder` fires.
- [ ] Reset button: restores `defaultColumns`; fires `mj-columns-reset`.
- [ ] Light-dismiss: click outside panel or `Escape` closes; focus restored.
- [ ] axe audit passes with zero violations in both open and closed states.
- [ ] RTL: panel anchors to right; drag handle on correct side.

## 20. Open questions
- Should column grouping (pinned-left / center / pinned-right) be visually separated within the picker list?
- Should the picker support a search/filter input for tables with many columns (e.g., 30+)?
