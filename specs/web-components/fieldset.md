# Fieldset Spec

- **Tag:** `<mj-fieldset>`
- **Class / file:** `MjFieldset` / `mjfieldset.js`
- **Category:** Text & data-entry controls — form-structure primitives
- **Primary or Variant:** Primary
- **Synonyms covered:** Fieldset, Fieldset with Legend
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-fieldset>` groups semantically related form controls under a common label
(legend). It maps directly to the native `<fieldset>/<legend>` pattern, ensuring
screen readers announce the group name for every contained control, and provides a
styled, themeable container that can be collapsed, disabled, or marked invalid as a
unit.

## 2. When to use / when not to use
**Use** to group controls that share a common purpose — a radio group, an address
block, a card-payment section. **Use** `<mj-fieldset>` as the container for
`<mj-radio-group>` and `<mj-checkbox-group>` which require group labelling.
**Do not use** for purely visual layout grouping with no semantic relationship;
use a layout primitive (`<mj-stack>`, `<mj-panel>`) instead. Do not nest fieldsets
more than two levels deep without a strong semantic justification.

## 3. Anatomy
- **Shadow `<fieldset>`** — the actual fieldset element that supplies the
  `group` role and disabled propagation to browsers that support it.
- **`<legend>` inside the shadow fieldset** — slotted via the `legend` slot; renders
  the group label text and optional required/optional badge.
- **Default slot** — all child controls, labels, help text, and error messages.
- **Footer slot** — optional helper text or aggregate error spanning the whole group.

## 4. Variants & modes
| Variant | Attribute | Description |
|---------|-----------|-------------|
| Default | _(none)_ | Bordered container with visible legend |
| Borderless | `variant="borderless"` | No border; legend remains; used inside cards or panels |
| Collapsible | `collapsible` | Legend acts as a disclosure button; content region expands/collapses |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `legend` | string | `""` | Yes | Text content of the legend; alternative to the `legend` slot |
| `disabled` | boolean | `false` | Yes | Maps to `<fieldset disabled>`; propagates disabled to all contained form controls |
| `required` | boolean | `false` | Yes | Marks the group as required; displays a required indicator beside the legend |
| `optional` | boolean | `false` | Yes | Displays an "(optional)" label beside the legend when the group is not required |
| `invalid` | boolean | `false` | Yes | Applies invalid styling to the group border and legend; does not set `aria-invalid` on the fieldset itself (errors live on controls) |
| `collapsible` | boolean | `false` | Yes | Enables the collapsible variant |
| `open` | boolean | `true` | Yes | When `collapsible`, controls whether the content region is visible |
| `variant` | `"default"` \| `"borderless"` | `"default"` | Yes | Visual style variant |
| `name` | string | `""` | Yes | Forwarded to the inner `<fieldset>` for form association grouping; informational only |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `controls` | `HTMLFormControlsCollection` | All form-associated controls directly inside this fieldset |

## 7. Slots
| Slot | Description |
|------|-------------|
| `legend` | The legend label content; overrides the `legend` attribute when both are present |
| _(default)_ | All form controls and structural primitives (`<mj-label>`, `<mj-help-text>`, etc.) |
| `footer` | Aggregate help text or group-level error message |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-toggle` | `{ open: boolean }` | Yes | Yes | Fires when the collapsible fieldset is expanded or collapsed; canceling prevents the state change |

## 9. CSS parts & custom properties
| Part / Property | Description |
|-----------------|-------------|
| `::part(fieldset)` | The inner `<fieldset>` element |
| `::part(legend)` | The inner `<legend>` element |
| `::part(content)` | The wrapper `<div>` that contains the default slot |
| `::part(footer)` | The footer slot container |
| `--mj-fieldset-border-color` | Border color (default: `var(--mj-color-border-default)`) |
| `--mj-fieldset-border-radius` | Corner radius (default: `var(--mj-radius-md)`) |
| `--mj-fieldset-gap` | Gap between slotted controls (default: `var(--mj-space-4)`) |
| `--mj-fieldset-legend-color` | Legend text color (default: `var(--mj-color-text-secondary)`) |
| `--mj-fieldset-legend-size` | Legend font-size (default: `var(--mj-font-size-sm)`) |
| `--mj-fieldset-invalid-border-color` | Border color in invalid state (default: `var(--mj-color-border-error)`) |

## 10. States
- **default** — visible border, legend displayed, all controls enabled.
- **disabled** — `[disabled]` on the inner `<fieldset>` propagates to all child
  controls; legend and border rendered at reduced opacity.
- **invalid** — group border switches to `--mj-fieldset-invalid-border-color`; does
  not suppress individual control errors.
- **collapsible / open** — legend renders a disclosure icon (rotated on expand);
  content region is visible.
- **collapsible / closed** — content region is hidden (`display:none`); the legend
  disclosure icon points to the collapsed direction; `aria-expanded="false"` on the
  legend button.
- **focus-visible** — when the legend button (in collapsible mode) has keyboard
  focus, a visible focus ring is applied using `--mj-focus-ring`.

## 11. Behavior & interactions
- The `disabled` attribute on `<mj-fieldset>` must set `disabled` on the inner
  `<fieldset>` so that browsers natively propagate disabled state to contained
  inputs; `<mj-*>` controls observe the fieldset's disabled state via
  `ElementInternals` or by reacting to the attribute on the shadow host.
- When `collapsible` is true, clicking or activating the legend button toggles
  `open`. The content region uses a CSS `grid-template-rows` transition from `0fr`
  to `1fr` (respecting `prefers-reduced-motion`).
- Setting `invalid` on the fieldset does not replace errors on individual controls;
  it is supplementary styling for the group border.
- When `required` and `optional` are both absent, no indicator is shown (caller
  chooses whether all fields are implicitly required in context).

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Moves focus through controls in DOM order; the legend button (collapsible) is in the tab order |
| `Enter` / `Space` | Toggles the collapsible fieldset open/closed when the legend button has focus |

## 13. Accessibility
- The inner `<fieldset>` supplies the implicit `group` role; all contained controls
  are associated with the `<legend>` text by the browser automatically.
- The `legend` slot/attribute text must be non-empty; a missing legend is flagged as
  a console warning in development builds.
- In collapsible mode, the `<legend>` wraps a `<button>` with `aria-expanded` and
  `aria-controls` pointing to the content `<div>`.
- The required indicator (asterisk or similar) inside the legend has
  `aria-hidden="true"`; the `<legend>` text itself should include "(required)" or
  equivalent via a visually-hidden span when a screen-reader-friendly string is
  needed.
- Group-level invalid state is not placed on the `<fieldset>` as `aria-invalid`
  (not a valid combination); individual controls carry their own `aria-invalid`.

## 14. Form participation
`<mj-fieldset>` is not itself form-associated. It does not contribute a value to
`FormData`. It facilitates grouping only; the contained `<mj-*>` controls participate
individually.

## 15. Internationalization & RTL
- The required badge text ("required" / "*") and optional badge text ("optional")
  are overridable via `required-label` and `optional-label` attributes and the
  shared localization hook.
- In RTL layouts the disclosure icon (collapsible mode) mirrors horizontally.
- Legend text may be provided in any language; no transformation is applied.

## 16. Progressive enhancement / SSR
Server renders as `<fieldset><legend>…</legend>…</fieldset>`. On upgrade, the
component wraps the light-DOM `<fieldset>` or mirrors its attributes onto the
shadow `<fieldset>`. Without scripting, the native fieldset/legend grouping remains
fully functional including disabled propagation.

## 17. Dependencies
- `web-component-development-plan.md` §6: Registry + base element helper,
  Design-token stylesheet, Focus utilities.
- `<mj-form>` as the typical parent context.
- `<mj-label>`, `<mj-help-text>`, `<mj-error-message>` as peer primitives slotted
  inside.

## 18. Edge cases & error handling
- Empty default slot: renders the bordered container with legend only; no error.
- Both `legend` attribute and `legend` slot provided: slot content takes precedence;
  console warning in development builds.
- `collapsible` with `open="false"` on initial render: content is hidden immediately
  without a transition (no flash of visible content).
- Dynamically toggling `disabled` after render: the component re-sets `disabled` on
  the inner `<fieldset>` and all slotted `<mj-*>` controls observe the change via
  their own `attributeChangedCallback`.
- Very long legend text: truncates with an ellipsis at one line; full text remains
  accessible as the element text content.

## 19. Acceptance criteria
- [ ] All controls inside a disabled `<mj-fieldset>` are non-interactive and
      `aria-disabled` or `disabled` is set on each.
- [ ] Screen reader announces group name (from legend) before each child control
      in the group.
- [ ] Collapsible fieldset: `Enter`/`Space` on the legend button toggles `open`;
      `aria-expanded` updates; content region is hidden/shown.
- [ ] `mj-toggle` fires with `{ open: boolean }` on every state change; canceling
      the event prevents the change.
- [ ] `invalid` attribute applies error border; individual control errors remain
      visible and independent.
- [ ] RTL: disclosure icon mirrors; legend text is right-aligned.
- [ ] No-JS: native `<fieldset>/<legend>` grouping is intact; disabled propagation
      works via the browser.
- [ ] Axe-core reports zero violations.

## 20. Open questions
- Should `<mj-fieldset>` support a `size` attribute to control the legend font
  size (e.g., heading level visual style) for use as a section header?
- Should the collapsible state be persisted to `localStorage` using a `storage-key`
  attribute, or is that deferred to a separate pattern?
