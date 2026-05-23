# Label Spec

- **Tag:** `<mj-label>`
- **Class / file:** `MjLabel` / `mjlabel.js`
- **Category:** Text & data-entry controls — form-structure primitives
- **Primary or Variant:** Primary
- **Synonyms covered:** Label, Field label, Form label
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-label>` renders a visible, accessible label associated with a form control.
It wraps a native `<label>` element so that clicking the label text moves focus to
(and activates) the paired control. It additionally renders optional required/
optional indicators and a slot for inline help-icon triggers, keeping that
decoration semantically outside the bare label text.

## 2. When to use / when not to use
**Use** for every visible text label that identifies a form control — text fields,
selects, checkboxes, radio buttons, textareas, and custom `<mj-*>` inputs.
**Do not use** as a section heading or for purely decorative text; use `<h*>` or
`<mj-fieldset>` legend for group-level labels. Do not use the `placeholder`
attribute of an input as a substitute for a label.

## 3. Anatomy
- **Shadow `<label>`** — the native label element providing click-to-focus and
  the accessible name association via `for`/`htmlFor`.
- **Default slot** — the visible label text content.
- **Indicator span** — a `<span aria-hidden="true">` that renders the required
  asterisk or the "(optional)" text; placed after the label text in the visual
  layout.
- **Suffix slot** — intended for an inline help-icon button (e.g., a popover
  trigger); rendered after the indicator, outside the `<label>` click target.

## 4. Variants & modes
| Variant | Attribute | Description |
|---------|-----------|-------------|
| Default | _(none)_ | Horizontal label above the control |
| Inline | `layout="inline"` | Label and control are laid out side-by-side |
| Hidden | `visually-hidden` | Label text is visually hidden but remains in the accessibility tree |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `for` | string | `""` | Yes | ID of the associated control; forwarded to inner `<label for>` |
| `required` | boolean | `false` | Yes | Shows a required indicator (asterisk) after the label text |
| `optional` | boolean | `false` | Yes | Shows an "(optional)" badge after the label text |
| `disabled` | boolean | `false` | Yes | Renders label text at reduced opacity to match a disabled control |
| `layout` | `"stacked"` \| `"inline"` | `"stacked"` | Yes | Controls label/control layout direction |
| `visually-hidden` | boolean | `false` | Yes | Applies a visually-hidden utility class so the label is not displayed but remains in the accessibility tree |
| `required-label` | string | `"*"` | Yes | Override text for the required indicator |
| `optional-label` | string | `"(optional)"` | Yes | Override text for the optional indicator |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `control` | `HTMLElement \| null` | The associated form control resolved from the `for` attribute; `null` if not found |
| `htmlFor` | `string` | Mirrors the `for` attribute as a property; consistent with `HTMLLabelElement.htmlFor` |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | The visible label text |
| `suffix` | Content rendered after the required/optional indicator and outside the `<label>` click target (e.g., a help-icon popover trigger) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-click` | `{ control: HTMLElement \| null }` | Yes | No | Fires after the inner `<label>` click activates the associated control; useful for callers that need to react to label clicks |

## 9. CSS parts & custom properties
| Part / Property | Description |
|-----------------|-------------|
| `::part(label)` | The inner `<label>` element |
| `::part(indicator)` | The required/optional indicator `<span>` |
| `::part(suffix)` | The suffix slot container |
| `--mj-label-color` | Label text color (default: `var(--mj-color-text-primary)`) |
| `--mj-label-disabled-color` | Label text color when disabled (default: `var(--mj-color-text-disabled)`) |
| `--mj-label-font-size` | Font size (default: `var(--mj-font-size-sm)`) |
| `--mj-label-font-weight` | Font weight (default: `var(--mj-font-weight-medium)`) |
| `--mj-label-required-color` | Required indicator color (default: `var(--mj-color-text-error)`) |
| `--mj-label-gap` | Gap between label text, indicator, and suffix (default: `var(--mj-space-1)`) |

## 10. States
- **default** — normal label text color, no indicator unless `required` or
  `optional` is set.
- **disabled** — label rendered at `--mj-label-disabled-color` opacity.
- **required** — asterisk (or `required-label` text) displayed in
  `--mj-label-required-color`; `aria-hidden="true"` on the indicator span.
- **optional** — `(optional)` badge (or `optional-label` text) displayed in
  secondary color; `aria-hidden="true"` on the badge span.
- **visually-hidden** — label text hidden via CSS clip/position technique;
  remains in the accessibility tree.

## 11. Behavior & interactions
- On render, the component queries the document for the element whose `id` equals
  the `for` attribute value and caches it in `control`. If the control is a
  `<mj-*>` element, the component additionally forwards `for` to the shadow-root
  native input inside that component so the native `<label>` association is valid.
- If `for` is not set, the component attempts to associate with the first
  form-associated sibling or descendant (implicit label association), mirroring
  native `<label>` behavior.
- Clicking the label moves focus to the associated control via the inner `<label>`
  click delegation.
- When `required` and `optional` are both `false`, neither indicator is rendered
  and the indicator `<span>` is removed from the DOM to avoid stale aria-hidden
  nodes.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Label itself is not focusable; focus passes through to controls |
| _Any key on associated control_ | Label text activates the control when clicked (pointer-driven; no specific keyboard mapping on the label itself) |

## 13. Accessibility
- The inner `<label>` element provides the accessible name association via the
  `for`/`id` binding; the component validates that the `for` target exists and
  logs a console warning if not.
- Required and optional indicators carry `aria-hidden="true"`; the label text
  should include a screen-reader-only "(required)" or "(optional)" string only
  when the indicator symbol alone is ambiguous — this is the responsibility of
  the consuming layout, not the label component itself.
- When `visually-hidden` is set, the component uses the `.sr-only` clip technique
  (`clip: rect(0,0,0,0); position: absolute; width: 1px; height: 1px`) so text is
  exposed to assistive technology while being invisible to sighted users.
- The `suffix` slot content is outside the `<label>` element so interactive content
  (a help-icon button) does not become part of the label click target or the
  control's accessible name.

## 14. Form participation
Not form-associated. `<mj-label>` contributes no value to `FormData`. Its role is
purely associative and visual.

## 15. Internationalization & RTL
- `required-label` and `optional-label` are overridable per-locale via attributes
  or the shared localization hook.
- In RTL layouts the indicator and suffix slot appear on the left side of the label
  text (logical inline-end position).
- Label text is passed through as-is; no transformation is applied.

## 16. Progressive enhancement / SSR
Server renders as a native `<label for="…">…</label>`. On upgrade the component
wraps the server-rendered label and moves its content into the shadow `<label>`,
preserving the `for` association. Without scripting the native `<label>` association
and click behavior are fully functional.

## 17. Dependencies
- `web-component-development-plan.md` §6: Registry + base element helper,
  Design-token stylesheet.
- Peer form-structure primitives: `<mj-help-text>`, `<mj-error-message>`.
- Typically composed inside `<mj-form>` and `<mj-fieldset>`.

## 18. Edge cases & error handling
- `for` pointing to a non-existent ID: logs a console warning in development;
  the label still renders and may be associated implicitly.
- Both `required` and `optional` set simultaneously: `required` takes precedence;
  `optional` is ignored; console warning in development.
- Empty default slot: label renders with no text content; the associated control
  loses its accessible name — a console error is logged.
- Very long label text: wraps to multiple lines; indicator remains on the last
  line of text in logical inline-end position.
- `<mj-label>` used inside a `<mj-fieldset>`: the fieldset legend provides the
  group name; individual labels still provide field-level names.

## 19. Acceptance criteria
- [ ] Clicking label text moves focus to the associated control identified by `for`.
- [ ] Required indicator is visible with `required`; indicator span has
      `aria-hidden="true"`.
- [ ] Optional badge is visible with `optional`; indicator span has
      `aria-hidden="true"`.
- [ ] `visually-hidden` hides the label text visually while keeping it accessible.
- [ ] `disabled` reduces label text opacity to match disabled control styling.
- [ ] In RTL mode, indicator appears on the logical inline-end side.
- [ ] No-JS: native `<label for>` association is intact.
- [ ] Axe-core reports zero violations; no orphaned label warnings.

## 20. Open questions
- Should `<mj-label>` also accept a `for-slot` mechanism to associate with a
  specific named slot inside a `<mj-*>` host element rather than an `id`?
- Should the suffix slot be replaced by a dedicated `<mj-help-text>` icon-trigger
  pattern, or kept flexible for any interactive content?
