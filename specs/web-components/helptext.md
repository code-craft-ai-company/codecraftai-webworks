# Help Text Spec

- **Tag:** `<mj-help-text>`
- **Class / file:** `MjHelpText` / `mjhelptext.js`
- **Category:** Text & data-entry controls — form-structure primitives
- **Primary or Variant:** Primary
- **Synonyms covered:** Help text, Helper text, Hint text, Field description
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-help-text>` provides supplementary guidance or contextual instructions for a
form control. It renders a short description that is linked to the control via
`aria-describedby`, so assistive technologies announce the help text after the
control label and value. It is distinct from validation errors (`<mj-error-message>`)
and from the label (`<mj-label>`); all three can be present simultaneously.

## 2. When to use / when not to use
**Use** when a control needs a short clarifying note — format hints, constraints,
acceptable values, or context that cannot fit in the label. Examples: "Must be at
least 8 characters", "Enter the full country name", "yyyy-mm-dd".
**Do not use** for error messages — use `<mj-error-message>` instead.
**Do not use** for critical information that is also conveyed nowhere else; help
text may not be read by all users. **Do not use** as a replacement for a label.

## 3. Anatomy
- **Shadow `<p>` (or `<span>`)** — the text container; rendered as `<p>` when
  block-level layout is expected, `<span>` when inline-level (controlled by
  `display` attribute).
- **Icon slot** — optional leading icon (informational icon glyph) before the text.
- **Default slot** — the help text content (plain text or inline markup).

## 4. Variants & modes
| Variant | Attribute | Description |
|---------|-----------|-------------|
| Default | _(none)_ | Plain text description, block display |
| Inline | `display="inline"` | Inline `<span>` rather than block `<p>`; used when help text appears to the right of a control |
| Icon-prefixed | `icon` slot populated | Renders a leading icon before the text |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `for` | string | `""` | Yes | ID of the control this help text describes; the component sets `aria-describedby` on that control pointing to this element's `id` |
| `id` | string | _(auto-generated)_ | Yes | Must be stable; used as the `aria-describedby` target on the associated control |
| `display` | `"block"` \| `"inline"` | `"block"` | Yes | Whether the text container is a block `<p>` or inline `<span>` |
| `disabled` | boolean | `false` | Yes | Reduces opacity to match a disabled control's help text |
| `hidden` | boolean | `false` | Yes | Hides the help text visually and removes its contribution to `aria-describedby` |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `control` | `HTMLElement \| null` | The form control resolved from the `for` attribute; `null` if unresolvable |

## 7. Slots
| Slot | Description |
|------|-------------|
| `icon` | Optional leading icon element (e.g., `<mj-icon name="info">`) |
| _(default)_ | The help text content — plain text, inline `<code>`, `<strong>`, etc. |

## 8. Events
`<mj-help-text>` does not emit events; it is a passive display element.

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No events |

## 9. CSS parts & custom properties
| Part / Property | Description |
|-----------------|-------------|
| `::part(container)` | The inner `<p>` or `<span>` element |
| `::part(icon)` | The icon slot wrapper |
| `--mj-help-text-color` | Text color (default: `var(--mj-color-text-secondary)`) |
| `--mj-help-text-disabled-color` | Text color when disabled (default: `var(--mj-color-text-disabled)`) |
| `--mj-help-text-font-size` | Font size (default: `var(--mj-font-size-xs)`) |
| `--mj-help-text-gap` | Gap between icon and text (default: `var(--mj-space-1)`) |
| `--mj-help-text-margin-top` | Top margin relative to the control (default: `var(--mj-space-1)`) |

## 10. States
- **default** — secondary-color text rendered below (or beside) the associated
  control.
- **disabled** — text opacity reduced to `--mj-help-text-disabled-color`; the text
  remains in the accessibility tree so screen readers still announce it.
- **hidden** — element has `display: none`; the component also removes the element's
  `id` from the associated control's `aria-describedby` so the hidden text is not
  announced.

## 11. Behavior & interactions
- On `connectedCallback` and whenever `for` changes, the component:
  1. Resolves the target control by `document.getElementById(for)`.
  2. Appends this element's `id` to the control's `aria-describedby` list
     (space-separated; does not overwrite existing values).
  3. Stores a cleanup reference to remove the `id` from `aria-describedby` on
     `disconnectedCallback` or when `hidden` is set.
- If `for` is not set, the component does not auto-associate; it is the author's
  responsibility to ensure the relationship is expressed via `aria-describedby` on
  the control.
- When `hidden` toggles from `false` to `true`, the `id` is removed from the
  target control's `aria-describedby`; toggling back re-adds it.
- The component is entirely passive — no interactive behavior.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| — | `<mj-help-text>` is not focusable; no keyboard interaction |

## 13. Accessibility
- The element's `id` is the anchor for `aria-describedby` on the associated
  control; this id must be stable across re-renders and not change unless the `for`
  target changes.
- When `hidden`, the `id` is removed from the control's `aria-describedby`; setting
  `aria-hidden` on the element is insufficient because `aria-describedby` still
  resolves hidden elements in some user-agent implementations.
- The help text container has no explicit ARIA role — it is a static text element.
  Do not add `role="status"` or `role="alert"` here; those belong on live-region
  elements. For live feedback tied to a control, see `<mj-error-message>`.
- Icon in the `icon` slot must have `aria-hidden="true"` (decorative); if the icon
  conveys meaning not present in the text, that meaning must be expressed in the
  text itself.

## 14. Form participation
Not form-associated. Contributes no value to `FormData`. Purely presentational and
descriptive.

## 15. Internationalization & RTL
- Help text content is provided by the author and may be in any language.
- In RTL layouts the icon and text follow logical inline direction (icon on the
  right, text on the left), achieved via `flex-direction: row-reverse` or CSS
  logical properties.
- No locale-specific formatting is applied.

## 16. Progressive enhancement / SSR
Server renders as `<p id="…" class="mj-help-text">…</p>`. The associated control
has `aria-describedby="…"` set in server markup. On upgrade, the component wraps
the existing element and re-asserts the `aria-describedby` relationship. Without
scripting the `aria-describedby` in server markup is sufficient; no JavaScript
behavior is required for the help text to function.

## 17. Dependencies
- `web-component-development-plan.md` §6: Registry + base element helper,
  Design-token stylesheet.
- Peer form-structure primitives: `<mj-label>`, `<mj-error-message>`.
- Optional: `<mj-icon>` in the `icon` slot.

## 18. Edge cases & error handling
- Missing `for` attribute: help text renders normally but no auto-association is
  made; a console warning is logged in development builds.
- Target control not found in the document: a console warning is logged; the
  component retries on `MutationObserver` notifications in case the control is
  added asynchronously.
- Duplicate `id` on the help text element (author error): browser behavior; a
  console warning is logged.
- Very long help text: wraps naturally within its container; no truncation applied
  (truncation could hide critical information).
- `hidden` and `disabled` simultaneously: `hidden` wins; element is not rendered or
  announced.

## 19. Acceptance criteria
- [ ] Control's `aria-describedby` contains this element's `id` after connection.
- [ ] Setting `hidden` removes this element's `id` from the control's
      `aria-describedby`.
- [ ] Screen reader announces help text after the control's label and value when
      the control receives focus.
- [ ] `disabled` renders help text at reduced opacity; text remains in accessibility
      tree.
- [ ] RTL: icon appears on the logical inline-end side of the text.
- [ ] No-JS: `aria-describedby` in server markup correctly associates help text
      without scripting.
- [ ] Axe-core reports zero violations.
- [ ] Disconnecting the element from the DOM removes its `id` from the associated
      control's `aria-describedby`.

## 20. Open questions
- Should `<mj-help-text>` support a `live` attribute to emit help text as a
  `role="status"` polite live region for dynamically updated hints (e.g., a
  password-strength hint that changes as the user types)?
- Should auto-association without `for` be supported via closest-sibling or
  parent-form-control heuristic, or remain explicit-only?
