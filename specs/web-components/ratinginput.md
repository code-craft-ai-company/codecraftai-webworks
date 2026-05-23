# Rating Input Spec

- **Tag:** `<mj-rating>`
- **Class / file:** `RatingInput` / `ratinginput.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Star rating, Rating widget
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-rating>` is a star (or custom icon) rating input where the user selects a
whole or half-step score. It implements the radio-group ARIA pattern so each
selectable step is a focusable radio-button semantics item. A read-only variant
displays a rating without allowing changes — useful for review displays. The
component is form-associated and submits the numeric rating value.

## 2. When to use / when not to use
**Use** for subjective quality ratings on a fixed scale: product reviews, feedback
surveys, content quality scores. **Use** `readonly` for displaying an aggregate
rating score. **Do not use** for selections from a discrete named list — prefer
radio groups or `<mj-segmented-control>`. **Do not use** for numeric precision
beyond half-steps — prefer `<mj-slider>`.

## 3. Anatomy
- **Rating group** (`part="group"`) — `role="radiogroup"` container.
- **Rating item** (`part="item"`) — individual star/icon; each is a focusable `<span role="radio">`.
- **Icon filled** (`part="icon-filled"`) — the filled icon layer (star, heart, etc.).
- **Icon empty** (`part="icon-empty"`) — the empty icon layer.
- **Icon half** (`part="icon-half"`) — the half-filled icon layer (when `half-steps` enabled).
- **Value label** (`part="value-label"`) — optional text like "4 out of 5 stars".
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Whole steps | — (default) | Integer values 1–`max` |
| Half steps | `half-steps` | Values in 0.5 increments |
| Read-only | `readonly` | Displays rating; no interaction; used for display |
| With label | `show-value-label` | Text label shown beside the stars |
| Custom icon | `icon` attribute | Uses a named icon from the design system icon set |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name submitted with form data |
| `value` | string | `"0"` | yes | Current rating value (numeric string) |
| `max` | number | `5` | yes | Maximum rating (number of stars) |
| `label` | string | `""` | yes | Visible label above the rating |
| `help-text` | string | `""` | yes | Hint text |
| `error-message` | string | `""` | yes | Override validation message |
| `required` | boolean | `false` | yes | A non-zero rating must be selected |
| `disabled` | boolean | `false` | yes | Disables all interaction |
| `readonly` | boolean | `false` | yes | Display-only; no focusable items |
| `half-steps` | boolean | `false` | yes | Allow half-step (0.5 increment) selection |
| `show-value-label` | boolean | `false` | yes | Show numeric label like "4 out of 5" |
| `icon` | string | `"star"` | yes | Icon name from the design system icon set |
| `icon-color` | string | `""` | yes | CSS color token name for the filled icon; overrides default gold |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Icon size scale |
| `value-label-format` | string | `"{value} out of {max}"` | yes | Format string for the value label; `{value}` and `{max}` are interpolated |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `valueAsNumber` | number | The current rating as a JavaScript number |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `icon-filled` | Custom SVG/element used for the filled state of each rating item |
| `icon-empty` | Custom SVG/element used for the empty state |
| `icon-half` | Custom SVG/element used for the half-filled state |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: number, previousValue: number }` | yes | yes | Fires when the rating is changed; cancel to prevent |
| `mj-hover` | `{ hoverValue: number }` | yes | no | Fires when the pointer hovers over a rating position (preview) |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `group`, `item`, `icon-filled`, `icon-empty`, `icon-half`, `value-label`, `label`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-rating-icon-size` | size-scale token | Icon width/height |
| `--mj-rating-icon-gap` | `--mj-space-1` | Gap between icon items |
| `--mj-rating-icon-color-filled` | `--mj-color-rating-filled` | Filled star color |
| `--mj-rating-icon-color-empty` | `--mj-color-rating-empty` | Empty star color |
| `--mj-rating-icon-color-hover` | `--mj-color-rating-hover` | Preview hover color |
| `--mj-rating-icon-color-disabled` | `--mj-color-icon-disabled` | Disabled state color |
| `--mj-rating-focus-ring` | `--mj-shadow-focus-ring` | Focus ring on active item |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| No rating (value=0) | All icons empty | `aria-checked="false"` on all items; `aria-required` if required |
| Rated | Items up to value filled | `aria-checked="true"` on selected item |
| Hover preview | Items up to hover position filled in hover color | `aria-checked` unchanged during hover |
| Focus-visible | Focus ring on the currently focused rating item | Roving tabindex; `aria-checked` reflects committed value |
| Disabled | Icons dimmed; no pointer events | `aria-disabled="true"` on group |
| Readonly | Icons show value; no focus or hover | `aria-readonly="true"` on group; items not in tab order |
| Invalid | Error border and message | `aria-invalid="true"` on group |

## 11. Behavior & interactions
- The component renders `max` items (or `max × 2` for half-steps; each star has
  a left half and a right half clickable zone).
- Hovering over an item previews the rating by temporarily filling items up to
  that position. Moving the pointer away restores the committed value. `mj-hover`
  fires during hover.
- Clicking an item commits the rating, fires `mj-change` (cancelable). If not
  cancelled, `value` is updated and `ElementInternals` value is set.
- Clicking the already-selected item clears the rating to 0 (allows deselection),
  unless `required` is set.
- Roving tabindex: only the currently selected item (or the first item if none
  selected) is in the tab order. Arrow keys move focus and selection simultaneously.
- In `readonly` mode, no items are focusable and no events fire.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Move focus to the rating group (single tab stop) |
| `Arrow Right` / `Arrow Up` | Increase rating by 1 step (or 0.5 with `half-steps`) |
| `Arrow Left` / `Arrow Down` | Decrease rating by 1 step (or 0.5 with `half-steps`) |
| `Home` | Set rating to minimum (1 or 0.5 with `half-steps`) |
| `End` | Set rating to `max` |
| `Delete` / `Backspace` | Clear rating to 0 (if not `required`) |
| `Enter` / `Space` | No-op (rating already committed on arrow key change) |

## 13. Accessibility
- The group container has `role="radiogroup"` with `aria-label` from the `label`
  attribute or a linked `<label>`.
- Each rating item has `role="radio"`, `aria-label` of the form `"{n} star"`
  (or `"{n} stars"`, `"{n}.5 stars"` for half-steps — all localizable), and
  `aria-checked="true"` only for the currently selected item.
- `aria-required="true"` on the group when `required`.
- `aria-invalid="true"` on the group when validation fails.
- `aria-describedby` on the group references help and error IDs.
- `aria-disabled="true"` on the group when `disabled`.
- In `readonly`, the group has `aria-readonly="true"` and `tabindex="-1"` on all
  items; a single `aria-label` on the group conveys the displayed value
  (e.g., "Rated 4 out of 5 stars").
- Hover preview does not change `aria-checked` — only committed changes are
  reflected in ARIA state.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Submits the numeric string value (e.g., `"4"` or `"3.5"`) under `name`.
- `required` validation: `valueMissing` when `value` is `"0"`.
- Custom validity message: "Please select a rating." (localizable).
- Form reset restores `value` to the `value` attribute (or `"0"` if absent) and
  clears validation state.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `aria-label` strings for each item (`"{n} star"`, `"{n} stars"`) use the
  shared localization hook with plural support.
- `value-label-format` string is localizable.
- In RTL, stars render right-to-left; the first star is on the right.
  Arrow Right decreases the rating (toward the start direction) — consistent
  with the radio-group convention where Right/Up increase value.
  This may need per-locale UX validation.

## 16. Progressive enhancement / SSR
- Server renders the committed rating as a read-only display (e.g., `<span>4
  out of 5 stars</span>`) with `aria-label`.
- On upgrade the component reads the `value` attribute and renders the interactive
  star icons.
- Without script, no interactive rating is possible; the server markup conveys
  the current value accessibly.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Focus utilities** (§6) — roving tabindex.
- **Localization hook** (§6) — item labels, value-label format.

## 18. Edge cases & error handling
- `max=0` or negative: console error; component renders nothing; form value is `"0"`.
- `value` greater than `max` set via attribute: clamped to `max` at upgrade.
- `half-steps` and `value` set to a non-0.5-aligned number (e.g., `"2.3"`):
  rounded to nearest 0.5 with a console warning.
- Clicking the selected item with `required`: click has no effect; the rating
  stays at the current value.
- `readonly` and `required` both set: no interaction; validation still applies
  on form submit.
- Very large `max` values (>10): icons overflow; the component clamps `max` to 10
  and emits a console warning.

## 19. Acceptance criteria
- [ ] `max=5` renders 5 star icons; clicking star 3 sets value to 3 and fills stars 1–3.
- [ ] `half-steps`: hovering over the left half of star 3 previews 2.5; clicking commits 2.5.
- [ ] Arrow Right increases rating by step; Arrow Left decreases; Home sets to min; End sets to max.
- [ ] Delete/Backspace clears to 0 when not `required`.
- [ ] Hover preview fills icons but does not change `aria-checked`.
- [ ] `aria-checked="true"` only on the selected item; `role="radiogroup"` on group.
- [ ] `mj-change` cancelable; cancellation restores previous value.
- [ ] `required` + value=0: `reportValidity` sets `aria-invalid` and shows error.
- [ ] Form submit sends numeric string; form reset restores initial value.
- [ ] `readonly` mode: no focus, no hover, `aria-readonly="true"`, correct `aria-label` on group.
- [ ] axe audit passes in interactive and read-only modes.

## 20. Open questions
- Should the `mj-hover` event carry both the `hoverValue` and the `committedValue` so hosts can show a preview label without losing the current label?
- Should clearing to 0 require a double-click on the active item (to prevent accidental deselection)?
- Should `icon` accept a slot-provided SVG rather than only a named icon identifier?
