# Row Selector Spec

- **Tag:** `<mj-row-selector>`
- **Class / file:** `MjRowSelector` / `mjrowselector.js`
- **Category:** Tables, lists & structured data (§5.8)
- **Primary or Variant:** Primary
- **Synonyms covered:** Row selector, Row checkbox, Select-all checkbox, Selection checkbox column
- **Phase:** P1
- **Status:** Implemented (this spec documents the shipped behavior of `mjrowselector.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-row-selector>` is a checkbox that selects one row of a table, list or tree grid
(`mode="row"`, the default) or acts as the select-all checkbox in the header
(`mode="all"`). Both modes support an indeterminate (mixed) state. Each user toggle
emits `mj-row-select-change` with the new state, the row `value` and whether Shift
was held, so the host can update its selection model and select ranges. The
control stops its own clicks, so a click on it does not also trigger the row it sits
in. It is form-associated: a selected control submits its `value`. It is one of the
DataTable companion controls of plan §5.8 ("Row selector supports row + select-all
with indeterminate state"). It keeps only its own checked state; the selection model
and the select-all state belong to the host.

## 2. When to use / when not to use

Use it for the checkbox column of a plain `<table>`, of an `<mj-table>` (from a column
`render` function), of a list or card list, and for the matching select-all control in
the header. Do not use it inside `<mj-data-table>`, which has its own row selection
and `selectAll()`. Do not use it for ordinary form options — use
`<mj-checkbox-group>`. For actions on the current selection, pair it with
`<mj-bulk-action-bar>`.

## 3. Anatomy

- **Host element** — `display: inline-flex`, items centered, gap `--mj-space-2`.
- **wrap (part)** — a `<label>` around everything. The whole wrap is the click target
  (checkbox, label text, count, padding); it has the minimum target height, the hover
  background, and stops click propagation.
- **checkbox (part)** — the native `<input type="checkbox">`; the only focusable
  element. It carries `aria-label` when the name is explicit or generated (§13).
- **label (part)** — `<span>` around the default slot. Hidden when nothing visible
  is slotted.
- **count (part)** — `<span>` that shows `(count)` in `mode="all"` when `count` is
  non-empty; hidden otherwise.

## 4. Variants & modes

There are no visual variants. The behavioral dimensions are:

| Mode               | Attribute                           | Description |
|--------------------|-------------------------------------|-------------|
| Row (default)      | (no `mode`), `mode="row"`, or any value other than `all` | Selects one row; `count` is ignored; generated name "Select row" |
| Select all         | `mode="all"`                        | Header control; shows `count`; generated name "Select all" / "Select all ({count})" |
| Indeterminate      | `indeterminate`                     | Mixed state, in either mode; any user activation clears it and selects the control |

`mode="all"` does not change activation and does not touch other selectors: the
host sets the rows when it receives the event.

## 5. Attributes

| Attribute       | Type            | Default | Reflects | Description |
|-----------------|-----------------|---------|----------|-------------|
| `mode`          | `row\|all`      | `row`   | Yes      | Any value other than `all` reads as `row`. Not written when absent |
| `selected`      | boolean         | `false` | Yes      | Checked state. Its presence at first render is the state a form reset restores |
| `indeterminate` | boolean         | `false` | Yes      | Mixed state, in either mode. Removed by any user activation, which also selects the control |
| `value`         | string          | `""`    | Yes      | Row identifier. Sent as `detail.value`; submitted as the form value (`on` when empty) |
| `name`          | string          | `""`    | Yes      | Form field name the value is submitted under |
| `label`         | string          | —       | No       | Accessible name of the checkbox. When non-empty it wins over the slotted text. An empty value counts as absent |
| `count`         | string          | —       | No       | In `mode="all"` only: shown verbatim in parentheses after the label and used in the generated name. Empty counts as absent |
| `disabled`      | boolean         | `false` | Yes      | Disables the inner checkbox and dims the control. The host keeps the pointer, so clicks on it are still stopped and never reach the row |

Common MjElement attributes (`dock`, `anchor`, `theme`, `hidden`, `context-menu`)
behave as on every component.

## 6. Properties

| Property        | Type             | Description |
|-----------------|------------------|-------------|
| `mode`          | `'row'\|'all'`   | Reflects `mode`. Reading an unknown value returns `'row'`; setting anything other than `'row'` or `'all'` is ignored |
| `selected`      | `boolean`        | Reflects `selected`. Only `true` sets the attribute, any other value removes it. Setting it does not emit an event |
| `indeterminate` | `boolean`        | Reflects `indeterminate`. Only `true` sets the attribute. Setting it does not emit an event |
| `disabled`      | `boolean`        | Reflects `disabled`. Only `true` sets the attribute (stricter than the MjElement default, which coerces with `Boolean()`) |
| `value`         | `string`         | Reflects `value`; `""` when absent; the setter stores `String(value)` |
| `name`          | `string`         | Reflects `name`; `""` when absent; the setter stores `String(value)` |

`label` and `count` have no properties. `form`, `validity`, `willValidate`,
`checkValidity()` and `reportValidity()` are not exposed.

**Methods**

No component-specific methods. The inherited `focus()` moves focus to the inner
checkbox (and does nothing while it is disabled).

## 7. Slots

| Slot      | Description |
|-----------|-------------|
| (default) | Visible label next to the checkbox. Any element, or any text that is not only whitespace, is shown in the `label` part. It names the checkbox (through the wrapping `<label>`, unless `label` is set) only when it has text: non-blank text, or an element that is not `aria-hidden="true"` / `hidden` with text, an `aria-label` or (an `img`) an `alt`. Content without text, such as an icon alone, is shown but the generated name is used (§13). A `slotchange` re-syncs |

## 8. Events

| Event                  | `detail` | Bubbles | Composed | Cancelable | Description |
|------------------------|----------|---------|----------|------------|-------------|
| `mj-row-select-change` | `{ selected: boolean, indeterminate: false, mode: 'row'\|'all', value: string, shiftKey: boolean }` | Yes | Yes | No | Fires after each user toggle of the checkbox, once `selected` and `indeterminate` have been updated |

- `indeterminate` in the detail is always `false`.
- `value` is the `value` attribute, `""` when absent (the form value is `on` in that
  case).
- `shiftKey` tells whether Shift was held for the click that caused the change, so
  the host can select a range.
- Setting `selected` / `indeterminate` by attribute or property, a form reset, a
  fieldset disable and a state restore do not emit an event.
- Click events from inside the control are stopped at the wrap: listeners on the
  host, the row and the document do not receive them. The inner `change` event is
  not composed and stays in the shadow root. The native `input` event of the
  checkbox is composed; the component stops it inside the shadow root, so host
  listeners receive only `mj-row-select-change`.

## 9. CSS parts & custom properties

**Parts**
- `::part(wrap)` — the `<label>` around checkbox, label and count
- `::part(checkbox)` — the native checkbox
- `::part(label)` — container of the slotted label (hidden when empty)
- `::part(count)` — the `(count)` text in `mode="all"`

**Custom properties**
| Property | Description |
|---|---|
| `--mj-row-selector-color` | Text color of the host (default `--mj-text`) |
| `--mj-row-selector-height` | Minimum height of the wrap (default `--mj-target-min`) |
| `--mj-row-selector-padding` | Padding of the wrap (default `--mj-space-1`) |
| `--mj-row-selector-border-radius` | Corner radius of the wrap (default `--mj-radius-sm`) |
| `--mj-row-selector-bg-hover` | Wrap background on hover (default `--mj-bg-muted`) |
| `--mj-row-selector-size` | Checkbox width and height (default `1rem`) |
| `--mj-row-selector-accent` | Checkbox `accent-color` (default `--mj-accent`) |
| `--mj-row-selector-focus-ring-color` | Focus ring color (default `--mj-focus-ring`); width and offset come from `--mj-focus-ring-width` / `--mj-focus-ring-offset` |
| `--mj-row-selector-label-font-size` | Label font size (default `inherit`) |
| `--mj-row-selector-count-color` | Count color (default `--mj-text-muted`) |

The gap (`--mj-space-2`), the label line height (1.2) and the disabled opacity
(0.55) have no component token.

## 10. States

| State                 | Visual effect | ARIA effect |
|-----------------------|---------------|-------------|
| unselected            | Empty checkbox | Not checked (native) |
| selected              | Checked checkbox | Checked (native) |
| indeterminate         | Native mixed glyph, also when `selected` is set | Mixed (native) |
| hover                 | `--mj-row-selector-bg-hover` on the wrap | — |
| focus-visible         | Focus ring on the checkbox | — |
| disabled (attribute)  | 55 % opacity; `cursor: not-allowed`; no hover background. The host keeps the pointer (`pointer-events: auto` overrides the base control rule) | Inner checkbox gets the native `disabled` attribute |
| disabled by fieldset  | Same as disabled (the host matches `:disabled`) | Inner checkbox gets the native `disabled` attribute |
| with count            | `(count)` after the label in the count color | Part of the name only when the name comes from the wrapping `<label>` |

## 11. Behavior & interactions

- Activation: a click anywhere on the wrap, or Space on the focused checkbox,
  toggles the native checkbox. On its `change` the component reads the new checked
  state, removes `indeterminate` if present, sets or removes `selected`, re-syncs,
  then emits `mj-row-select-change`.
- From the indeterminate state activation always selects: the browser toggles the
  checked state and clears the mixed flag, and the component then forces
  `selected` (so a control with both `selected` and `indeterminate` set stays
  selected rather than being unselected). Activating again unselects.
- Shift tracking: the wrap's click listener records `shiftKey` from a click whose
  target is not the checkbox, and ORs in the `shiftKey` of the click that reaches the
  checkbox (direct, or forwarded by the `<label>`, which may carry no modifiers). The
  next `change` consumes the value and resets it to `false`.
- Every click inside the control is stopped at the wrap, so it does not reach the
  row and cannot trigger row navigation or row selection there. This holds while
  the control is disabled too: the host keeps the pointer, and a click on the label
  text or padding is stopped at the wrap (the browser dispatches no click for the
  disabled checkbox itself).
- Calling `click()` on the host does not toggle the control: the host has no
  activation behavior and the event never reaches the inner label.
- Every watched attribute change and every `slotchange` re-syncs: checked and
  indeterminate state, inner `disabled` (from the attribute or a disabled fieldset),
  `aria-label`, count text and visibility, label visibility, and the form value.
- A locale change renders the control again (MjElement default); the state lives in
  attributes and is kept, and focus returns to the checkbox if it was inside.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Space`     | Toggles the checkbox (native behavior) and emits `mj-row-select-change` |
| `Tab`       | Moves focus to the next focusable element |
| `Shift+Tab` | Moves focus to the previous focusable element |

There is no custom key handling. Enter does nothing. A disabled control is not
focusable. For Shift+Space, `shiftKey` is whatever the browser puts on the click it
synthesizes for keyboard activation.

## 13. Accessibility

- Role: native checkbox. `selected` maps to checked, `indeterminate` to mixed.
- Accessible name, in order:
  1. `label`, when non-empty — set as `aria-label` on the checkbox;
  2. slotted content that has text (§7) — no `aria-label`; the wrapping `<label>`
     names the checkbox with the slotted text plus `(count)` when shown;
  3. generated (English defaults): `mode="row"` → "Select row"; `mode="all"` with a
     `count` → "Select all ({count})"; `mode="all"` without → "Select all".
- The generated row name is the same on every row. Hosts should set `label` to name
  the row (for example "Select invoice 1042") and should not use raw row ids.
- When `label` and visible slotted text are both present, `label` replaces the
  visible text in the name; it should contain that text (WCAG 2.5.3).
- Target size: the whole wrap is clickable and at least `--mj-target-min` (2.75rem)
  high. Without a label it is 1.5rem wide at the defaults (1rem box plus padding),
  which is 24 CSS px at a 16px root (WCAG 2.5.8).
- Focus ring on the checkbox through `:focus-visible`.
- The component has no live region and does not touch the row. The host sets row
  state such as `aria-selected` and announces selection counts (for example with
  `<mj-bulk-action-bar>`).
- A select-all control in a header cell usually has no visible text; give it `label`.

## 14. Form participation

- `static formAssociated = true`; `ElementInternals` is attached when
  `attachInternals` exists. Without it the control works but contributes nothing to
  a form.
- Value: while `selected`, the `value` attribute, or `on` when it is empty; while
  unselected, nothing (`setFormValue(null)`). It is submitted under the host's
  `name`, so several selectors sharing a name read back with `FormData.getAll()`.
  `indeterminate` does not affect the value.
- Disabled: a `disabled` attribute or a disabled ancestor `<fieldset>` disables the
  inner checkbox (`formDisabledCallback`); a disabled form-associated element is not
  submitted.
- Reset (`formResetCallback`): removes `indeterminate` and restores `selected` to its
  presence at first render. This default is a snapshot: later changes to the
  `selected` attribute do not change it, and there is no `defaultSelected` property.
  No event.
- Restore (`formStateRestoreCallback`): selected when the restored state is not
  null, else unselected. No event.
- Validation: none. There is no `required`, no `setValidity()` call, and the control
  is always valid. It does not use the shared `FormControlMixin`
  (`core/forminternals.js`).

## 15. Internationalization & RTL

- The generated names are read through `t()` from `core/intl.js` at sync time (keys
  `mj.rowSelector.selectRow` "Select row", `core.selectAll` "Select all",
  `mj.rowSelector.selectAllCount` "Select all ({count})"), so `setLocale()` /
  `registerStrings()` apply; the control is rendered again on a locale change.
- `{count}` is the raw `count` attribute string. It is not formatted as a number and
  no plural form is chosen.
- `label` overrides the generated name; the host localizes it.
- The visible count is the `count` string inside literal ASCII parentheses; the
  parentheses are not localizable. The host formats the content (for example
  "3 of 12").
- Layout is inline flex, so the checkbox sits at the inline start and the label and
  count follow; it mirrors in RTL.

## 16. Progressive enhancement / SSR

Server renders `<mj-row-selector value="42" label="Select order 42" selected></mj-row-selector>`.
Before upgrade only slotted text shows; there is no checkbox and no form value. On
upgrade the checkbox appears with the server-rendered `selected` / `indeterminate`
state, and the authored `selected` becomes the form-reset default. Without script
nothing can be selected; a page that needs a no-JS path renders a native
`<input type="checkbox" name="..." value="...">` instead.

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `afterRender`,
  `onAttributeChanged`, `listen`, `emit`, `$`, `focus()` delegation, re-render on
  locale change)
- **Localization hook** (§6) — `t()` for the generated names
- **Design-token stylesheet** (§6)
- **Platform** — `ElementInternals` (form association, implemented in the component,
  not through the shared form-association helper)
- Consumers: hosts that build selection columns (plain tables, `<mj-table>` column
  `render`, lists); `<mj-data-table>` lists `mj-row-selector` among the in-cell
  controls whose click must not toggle row selection

## 18. Edge cases & error handling

- Unknown `mode` value: behaves as `row`; the attribute is left as written.
- `count` in `mode="row"`: ignored (not shown, not in the name).
- Whitespace-only slotted text: not a label; the label part is hidden and the
  generated name is used.
- A slotted element with no text (an icon only, or content that is
  `aria-hidden="true"`): shown in the label part, but the checkbox gets the generated
  name ("Select row" / "Select all").
- `selected` and `indeterminate` both set: shows mixed, form value submitted;
  activation clears the mixed state and keeps the control selected.
- `value` absent: `detail.value` is `""` and the form value is `on`.
- `value = null` stores the string `"null"`.
- `mj-row-select-change` is not cancelable: the state has already changed. A host
  that rejects the change sets `selected` back.
- Disabled (attribute or fieldset): the control stays a pointer target, so a click
  on it does not land on the cell or row underneath; it is stopped at the wrap.
- A `click` listener on the host never fires for clicks on the control.
- Range selection: the component only reports `shiftKey`; the host keeps the anchor
  row and applies the range.

## 19. Acceptance criteria

- [ ] Without `mode`, the control behaves as `row`; `mode="all"` shows `(count)` when `count` is non-empty.
- [ ] Click on the checkbox, the label text or the wrap padding toggles it; Space toggles it; Enter does not.
- [ ] Each user toggle fires one `mj-row-select-change` with `selected`, `indeterminate: false`, `mode`, `value`, `shiftKey`; it bubbles, is composed and is not cancelable.
- [ ] A Shift-click reports `shiftKey: true`; the next plain click reports `false`.
- [ ] Activation removes `indeterminate` and selects, with or without `selected` set.
- [ ] Setting `selected` / `indeterminate` / `value` by attribute or property updates the checkbox and emits no event.
- [ ] Clicks inside the control do not reach the host's ancestors.
- [ ] Accessible name follows `label` → slotted text → generated name, with the documented English defaults; an icon-only slot gets the generated name.
- [ ] Generated names follow `setLocale()` / `registerStrings()`.
- [ ] Inside a form, a selected control with `name` submits `value` (or `on`); an unselected or disabled one submits nothing.
- [ ] Form reset restores the authored `selected` and clears `indeterminate` without an event.
- [ ] A disabled `<fieldset>` disables the inner checkbox.
- [ ] `disabled` dims the control and disables the inner checkbox; a click on a disabled control does not reach the row.
- [ ] Each documented custom property changes its target style.
- [ ] axe scan zero violations unselected, selected, indeterminate, disabled and in `mode="all"`.
- [ ] Light, dark, high-contrast and RTL rendering verified.

## 20. Open questions

- Should the control adopt `FormControlMixin` (plan §6) and expose `form` /
  `validity` / `checkValidity()` and a `required` constraint? Today it has no
  validation, as §14 and the source header state.
- Should `count` be formatted with `Intl` and plural rules, and the parentheses be
  part of a string template?
- Should `click()` on the host toggle the control, as on a native checkbox?
- Should Shift+Space range selection be handled explicitly rather than relying on the
  browser's synthesized click?
