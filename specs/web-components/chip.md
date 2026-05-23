# Chip Spec

- **Tag:** `<mj-chip>`
- **Class / file:** `MjChip` / `mjchip.js`
- **Category:** Feedback & status components
- **Primary or Variant:** Primary
- **Synonyms covered:** Pill, Tag
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-chip>` is a compact, pill-shaped element that represents an attribute,
filter, category, or selected item. It covers three interaction modes: **static**
(display-only label), **removable** (label plus a labeled delete control), and
**selectable** (toggleable on/off state, analogous to a checkbox). All three
share one element to guarantee consistent sizing, theming, and accessibility
across contexts such as filter bars, tag lists, and token inputs.

## 2. When to use / when not to use

**Use `static`** to display read-only metadata labels, categories, or taxonomy
tags where no interaction is needed.

**Use `removable`** in tag inputs, applied filter bars, and token lists where
the user can delete individual items.

**Use `selectable`** in filter sets or option groups where the user toggles
items on/off — similar to a checkbox but rendered as a pill.

**Do not use** chips for primary navigation — use tabs, links, or segmented
controls. Do not use `selectable` chips as a substitute for radio buttons when
only one item may be selected — prefer a radio group or segmented control.
Do not place complex interactive content (inputs, menus) inside a chip.

## 3. Anatomy

- **Root element** (`part="chip"`) — the pill container; its ARIA role depends
  on the `mode` attribute.
- **Leading icon** (`part="leading-icon"`) — `<slot name="leading-icon">` for an
  optional icon or avatar before the label text.
- **Label** (`part="label"`) — `<slot>` (default) for the chip's visible text.
- **Remove button** (`part="remove"`) — an icon button rendered only in
  `removable` mode; carries an accessible name that includes the chip label.
- **Selection indicator** (`part="check"`) — a checkmark icon shown inside the
  chip when `selectable` mode is `selected`; `aria-hidden`.

## 4. Variants & modes

| Mode | `mode` value | Root role | Description |
|------|-------------|-----------|-------------|
| Static | `static` (default) | none (inline text) | Display-only; not focusable; no keyboard interaction |
| Removable | `removable` | `listitem` (when in a list) | Has a separate remove button; chip label itself is not interactive |
| Selectable | `selectable` | `checkbox` | The whole chip is a toggle; `aria-checked` reflects selected state |

| Size | `size` value | Description |
|------|-------------|-------------|
| Small | `sm` | Compact; used in dense lists or inline with body text |
| Medium | `md` (default) | Standard filter/tag size |
| Large | `lg` | Prominent option selectors |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `mode` | `"static"\|"removable"\|"selectable"` | `"static"` | Yes | Interaction mode; determines role, focusability, and rendered controls |
| `selected` | boolean | `false` | Yes | Selectable mode only; reflects the current toggle state; maps to `aria-checked` |
| `disabled` | boolean | `false` | Yes | Prevents interaction; applies `aria-disabled` and visual muted state |
| `value` | string | `""` | Yes | Machine-readable value associated with this chip; used when chips participate in a group or form |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | Yes | Size variant |
| `remove-label` | string | `""` | Yes | Accessible label for the remove button; defaults to `"Remove <label text>"` computed from the chip's text content |
| `color` | string | `""` | Yes | Token name or CSS color for the chip background; empty uses the default surface token |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `selected` | `boolean` | Programmatic read/write for selectable mode; mirrors `selected` attribute |
| `labelText` | `string` | Read-only; the resolved text content of the default slot; used to build the remove button's `aria-label` |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | The chip label text; may include simple inline markup |
| `leading-icon` | Optional icon, avatar, or image before the label |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-chip-remove` | `{ value, labelText }` | Yes | Yes | Fired when the remove button is activated; canceling prevents the chip from being removed from the DOM |
| `mj-chip-select` | `{ value, selected }` | Yes | Yes | Fired when a selectable chip is toggled; canceling prevents the `selected` state from changing |
| `mj-chip-change` | `{ value, selected }` | Yes | No | Alias / convenience event fired after `mj-chip-select` resolves (non-cancelable); mirrors native `change` semantics |

## 9. CSS parts & custom properties

**Parts**
- `::part(chip)` — root pill element
- `::part(leading-icon)` — leading icon wrapper
- `::part(label)` — label text wrapper
- `::part(check)` — selection checkmark icon (selectable mode)
- `::part(remove)` — remove button (removable mode)

**Custom properties**
| Property | Description |
|----------|-------------|
| `--mj-chip-bg` | Chip background color |
| `--mj-chip-color` | Chip label text color |
| `--mj-chip-border-color` | Chip border/outline color |
| `--mj-chip-border-width` | Chip border thickness |
| `--mj-chip-border-radius` | Corner radius (defaults to `9999px` pill shape) |
| `--mj-chip-padding-block` | Block-axis padding |
| `--mj-chip-padding-inline` | Inline-axis padding |
| `--mj-chip-gap` | Gap between leading icon, label, and remove button |
| `--mj-chip-selected-bg` | Background when selected |
| `--mj-chip-selected-color` | Text color when selected |
| `--mj-chip-disabled-opacity` | Opacity when disabled |
| `--mj-chip-focus-ring-color` | Focus ring color for selectable and remove button |
| `--mj-chip-remove-size` | Width/height of the remove button |

## 10. States

- **default** — visible, not selected, not disabled.
- **hover** — pointer hovers over a selectable chip or the remove button;
  background shifts to the hover token.
- **focus-visible** — selectable chip or remove button is keyboard-focused;
  focus ring is shown.
- **selected** — `selectable` mode with `selected=true`; `aria-checked="true"`;
  checkmark icon visible; uses `--mj-chip-selected-*` tokens.
- **disabled** — `disabled=true`; pointer events suppressed; `aria-disabled="true"`;
  reduced opacity via `--mj-chip-disabled-opacity`.
- **active** — pointer pressed; slight scale reduction or background shift.

## 11. Behavior & interactions

**Static mode.** The chip is a styled `<span>` with no ARIA role and no tab stop.
It conveys information visually and through its text content; no pointer or
keyboard interaction occurs on the chip itself.

**Removable mode.** The chip label area is non-interactive. The remove button
(`part="remove"`) is a real `<button>` with an accessible name built from
`remove-label` or computed as `"Remove ${labelText}"`. Activating the button
fires `mj-chip-remove`. If not canceled, the element removes itself from the DOM.
The remove button receives focus after the chip is removed only if there is an
adjacent chip or a designated return target (set via `return-focus` attribute
pointing to an element id).

**Selectable mode.** The entire chip is a focusable element with `role="checkbox"`
and `aria-checked`. Activating it (click, `Enter`, or `Space`) fires
`mj-chip-select`. If not canceled, `selected` toggles and `mj-chip-change` fires.
When chips are grouped inside a `<mj-chip-group>` (a future companion element),
the group manages roving tabindex for arrow-key navigation between chips.

**Disabled behavior.** Disabled chips do not respond to pointer or keyboard
events. The remove button within a disabled removable chip is also disabled.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Moves focus to a selectable chip or to the remove button of a removable chip |
| `Enter` / `Space` | Toggles a selectable chip; activates the focused remove button |
| `Backspace` / `Delete` | Removes the chip when a removable chip or its remove button is focused (convenience shortcut in token-input contexts) |
| `Escape` | No effect on isolated chips; a chip group may use this to deselect all |

## 13. Accessibility

- **Roles:**
  - `static` — no ARIA role; conveyed as text.
  - `removable` — the chip container has no role; the remove button uses native
    `<button>` semantics.
  - `selectable` — `role="checkbox"` on the chip element; `aria-checked`
    reflects `selected` state.
- **Accessible name:** the chip's text content (default slot) is its name in all
  modes. For selectable chips, `aria-label` may be provided if the visible label
  is insufficient.
- **Remove button label:** must always include the chip's label so screen readers
  announce "Remove [label]" rather than a bare "Remove" or "×".
- **Disabled:** `aria-disabled="true"` is used (not the HTML `disabled` attribute)
  so the chip remains in the focus order and is discoverable by AT; pointer
  events are blocked via CSS `pointer-events: none`.
- **Color:** chip color variants (if used for category coding) must not be the
  sole distinguishing feature; label text always present.
- **Groups:** when multiple selectable chips represent a logical group, they
  should be wrapped in a `<fieldset>` with a `<legend>` or in a labelled
  `<div role="group">`.

## 14. Form participation

`<mj-chip>` is not form-associated by default. In token-input and filter-bar
contexts, the values of selected/remaining chips are managed by the parent
component (`<mj-token-input>`, `<mj-filter-panel>`) which handles form
association. If a standalone selectable chip is used within a form, the host
must include a hidden `<input>` to carry the value, or implement a
form-associated wrapper.

## 15. Internationalization & RTL

- The remove button label template defaults to `"Remove {label}"` and is
  overridable via the `remove-label` attribute or the localization hook.
- In RTL contexts, leading icon and remove button swap sides automatically via
  logical CSS (`padding-inline-start`, `padding-inline-end`, flex `row-reverse`
  is NOT used — instead, logical flex gap and margin are applied).
- All spacing uses logical CSS properties.

## 16. Progressive enhancement / SSR

Server renders as:
```html
<!-- static -->
<span class="mj-chip">Label</span>

<!-- removable -->
<span class="mj-chip mj-chip--removable">
  Label
  <button type="button" aria-label="Remove Label">×</button>
</span>

<!-- selectable -->
<button type="button" class="mj-chip mj-chip--selectable" role="checkbox" aria-checked="false">
  Label
</button>
```
Before JS loads, static and removable chips render correctly. Selectable chips
render as buttons (functional but without toggle state management). On upgrade,
the custom element adopts the markup and enables reactive state tracking.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle and attribute reflection.
- **Design-token stylesheet** (§6) — color, spacing, radius, motion tokens.
- **`<mj-icon>`** (§5.3 / future icon primitive) — remove button icon and
  checkmark; falls back to Unicode `×` and `✓` if not available.

## 18. Edge cases & error handling

- **Empty label slot:** chip renders but emits a console warning; the remove
  button's computed label falls back to just `"Remove"`, which is insufficient
  for AT — hosts must provide a label.
- **`selected` set on a non-selectable chip:** attribute is ignored; console
  warning emitted.
- **`remove-label` attribute is empty string:** the component falls back to the
  computed `"Remove ${labelText}"` pattern.
- **Rapid removal of many chips:** each removal is processed independently; no
  batch animation or focus management beyond moving focus to the next sibling
  chip when possible.
- **Very long label text:** chip grows in width; text does not truncate by
  default; hosts may apply `max-width` and `text-overflow: ellipsis` via
  `::part(label)`.

## 19. Acceptance criteria

- [ ] Static mode renders as a non-interactive styled pill; not in the tab order.
- [ ] Removable mode renders a remove button with a label that includes the chip text.
- [ ] Selectable mode renders with `role="checkbox"` and correct `aria-checked`.
- [ ] Toggling a selectable chip fires `mj-chip-select` (cancelable) then `mj-chip-change`.
- [ ] Canceling `mj-chip-select` prevents the `selected` state from changing.
- [ ] Activating the remove button fires `mj-chip-remove` (cancelable); canceling prevents DOM removal.
- [ ] Disabled chips are non-interactive and carry `aria-disabled="true"`.
- [ ] `Backspace`/`Delete` removes a focused removable chip.
- [ ] `Enter`/`Space` toggles a focused selectable chip.
- [ ] Remove button label includes chip's label text.
- [ ] RTL layout renders icon and remove button on the correct sides.
- [ ] No hard-coded colors; all values resolve from design tokens.
- [ ] Passes automated axe accessibility checks with no violations.

## 20. Open questions

- Should `<mj-chip-group>` be specified in this file as a companion element
  (managing arrow-key navigation and group-level selection) or in a separate spec?
- Should selectable chips support an indeterminate state (for hierarchical
  filter groups) analogous to indeterminate checkboxes?
- Is a `truncate` attribute needed to limit chip width to a fixed max with
  ellipsis and a tooltip showing the full label?
