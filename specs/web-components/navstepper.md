# Nav Stepper Spec

- **Tag:** `<mj-nav-stepper>`
- **Class / file:** `MjNavStepper` / `mjnavstepper.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Stepper (navigation), Step navigation, Progress stepper, Step indicator
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-nav-stepper>` is an ordered step-indicator navigation component that shows
a user's position within a multi-step process. Each step has a distinct state
(upcoming, current, complete, error) and can optionally be a navigable link to
re-enter a completed step. It is distinct from the numeric `<mj-number-field>`
spinner and serves as the structural backbone for `<mj-wizard>`.

## 2. When to use / when not to use
**Use** when a workflow has a defined, ordered sequence of discrete steps and
the user needs orientation about progress. **Use `<mj-wizard>`** when you also
need the content panels and navigation buttons managed by the component.
**Do not use** for simple progress indication — use `<mj-progress>`. **Do not
use** when steps are not sequential — use `<mj-tabs>`.

## 3. Anatomy
- **Host element** — wrapper; not a landmark on its own.
- **Step list** (`::part(list)`) — `<ol>` of steps in order.
- **Step item** (`::part(step)`) — each `<li>` containing the step indicator and label.
- **Step indicator** (`::part(indicator)`) — circle/number badge showing step number or status icon.
- **Step label** (`::part(label)`) — text label for the step; may include a sub-label.
- **Connector** (`::part(connector)`) — line between steps; decorative, `aria-hidden`.
- **Step link** (`::part(link)`) — optional `<a>` or `<button>` wrapping the indicator; present for navigable completed steps.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Horizontal | `orientation="horizontal"` | Steps laid out in a row with horizontal connectors |
| Vertical | `orientation="vertical"` | Steps stacked with vertical connectors; labels beside indicators |
| Linear | `linear` | Only the current and completed steps are navigable; future steps are not |
| Non-linear | _(no `linear`)_ | Any step can be activated regardless of completion order |
| Compact | `compact` | Indicator-only (no labels); labels appear in tooltips |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `current` | number | `0` | Yes | Zero-based index of the current active step |
| `orientation` | string | `"horizontal"` | Yes | Layout: `horizontal` \| `vertical` |
| `linear` | boolean | `true` | Yes | When true, restricts navigation to current and completed steps |
| `compact` | boolean | `false` | Yes | Shows indicators only; labels in tooltips |
| `label` | string | `"Progress"` | Yes | Accessible label for the stepper; becomes the `aria-label` of the `<ol>` wrapper or an associated heading |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `steps` | `Element[]` | Ordered array of all `<mj-nav-step>` child elements |
| `currentStep` | `Element \| null` | Reference to the currently active `<mj-nav-step>` element |
| `completedCount` | number | Read-only count of steps with `status="complete"` |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | `<mj-nav-step>` elements in order; defines the step sequence |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-nav-stepper-change` | `{ index: number, previousIndex: number, step: Element }` | Yes | Yes | Fires when the user activates a step; cancel to block navigation |
| `mj-nav-stepper-complete` | `{ completedCount: number, total: number }` | Yes | No | Fires when all steps reach `status="complete"` |

## 9. CSS parts & custom properties
**Parts**
- `::part(list)` — the `<ol>` step list
- `::part(step)` — each `<li>` step item
- `::part(indicator)` — step number/icon circle
- `::part(label)` — step title text
- `::part(sublabel)` — step subtitle/description text
- `::part(connector)` — line between steps
- `::part(link)` — navigable step anchor or button

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-nav-stepper-indicator-size` | `32px` | Diameter of the step indicator circle |
| `--mj-nav-stepper-indicator-bg-upcoming` | `var(--mj-color-surface-muted)` | Indicator fill for upcoming steps |
| `--mj-nav-stepper-indicator-bg-current` | `var(--mj-color-primary)` | Indicator fill for the current step |
| `--mj-nav-stepper-indicator-bg-complete` | `var(--mj-color-success)` | Indicator fill for completed steps |
| `--mj-nav-stepper-indicator-bg-error` | `var(--mj-color-error)` | Indicator fill for error steps |
| `--mj-nav-stepper-connector-color` | `var(--mj-color-border-muted)` | Connector line color (incomplete) |
| `--mj-nav-stepper-connector-color-complete` | `var(--mj-color-success)` | Connector color when the preceding step is complete |
| `--mj-nav-stepper-connector-width` | `2px` | Connector line thickness |
| `--mj-nav-stepper-font-size` | `var(--mj-font-size-sm)` | Label font size |

## 10. States
- **upcoming** — step not yet reached; indicator shows step number; not navigable in linear mode.
- **current** — active step; `aria-current="step"`; indicator highlighted.
- **complete** — step finished; indicator shows checkmark icon; navigable in both modes.
- **error** — step has an issue; indicator shows error icon; navigable for correction.
- **disabled** — step cannot be navigated to regardless of mode; `aria-disabled="true"`.
- **focus-visible** — navigable step link/button shows focus ring.
- **hover** — navigable steps show hover token on indicator and label.

## 11. Behavior & interactions
- The `current` attribute controls which step is active; it is reflected back
  when the user navigates by clicking a step link.
- In `linear` mode, clicking an upcoming step is suppressed (the link is
  `aria-disabled="true"` with no `href`/`onclick` delegation).
- In non-linear mode, all steps are navigable via their link/button.
- When `compact` is true, each step indicator has an associated `<mj-tooltip>`
  showing the label text.
- Connector lines are purely decorative (`aria-hidden`); they convey the fill
  level (complete vs. incomplete) via CSS that reads from the step item's state
  attribute.
- When `current` changes programmatically, focus does not automatically move to
  the new step — the host wizard or page logic manages focus.
- Step state transitions: `upcoming → current → complete` (or `→ error`). State
  is set via the `status` attribute on `<mj-nav-step>`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus through navigable step links/buttons in DOM order |
| `Enter` | Activates the focused step link or button; fires `mj-nav-stepper-change` |
| `Space` | Activates the focused button (non-link step trigger) |
| `Shift+Tab` | Reverse focus through navigable steps |

## 13. Accessibility
- The `<ol>` conveys step order semantically.
- The current step has `aria-current="step"` on its link or `<li>`.
- Completed and error steps have their status conveyed via `aria-label` on the
  indicator: e.g., "Step 2: Account details – completed".
- Upcoming/disabled steps in linear mode have `aria-disabled="true"` on their
  trigger and are not interactive; they remain in the DOM but are skipped by
  keyboard focus.
- Connectors are `aria-hidden="true"` and convey no information independently.
- An accessible label for the whole stepper is provided by the `label` attribute
  applied to an associated heading or the `<ol aria-label>`.
- Status icons (check, error) are `aria-hidden="true"`; status is conveyed
  through the accessible name, not the icon alone.

## 14. Form participation
N/A — `<mj-nav-stepper>` is a navigation/progress component, not a form control.

## 15. Internationalization & RTL
- `label` attribute is localizable; key `mj.navStepper.label`.
- Step accessible-name template: `mj.navStepper.stepLabel` with interpolation
  for `{number}`, `{title}`, and `{status}`.
- Status string keys: `mj.navStepper.status.upcoming`, `.current`, `.complete`,
  `.error`.
- In RTL, steps order visually from right to left in horizontal orientation;
  connectors reverse direction; indicators and labels swap inline positions.
- Vertical orientation is unaffected by RTL.

## 16. Progressive enhancement / SSR
- Server renders:
  ```html
  <mj-nav-stepper current="1">
    <mj-nav-step status="complete">Account</mj-nav-step>
    <mj-nav-step status="current">Details</mj-nav-step>
    <mj-nav-step status="upcoming">Review</mj-nav-step>
  </mj-nav-stepper>
  ```
- Before upgrade: steps are visible text items in an ordered list; no
  interaction or ARIA semantics.
- On upgrade: indicators, connectors, ARIA roles, `aria-current`, and keyboard
  interaction are applied without changing the underlying text content.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet,
  localization hook.
- `<mj-nav-step>` — companion element for individual step entries.
- `<mj-tooltip>` — used in `compact` mode for label tooltips.

## 18. Edge cases & error handling
- **`current` out of range**: clamped to `[0, steps.length - 1]`; console
  warning emitted.
- **Zero steps**: empty `<ol>` renders; console warning emitted.
- **All steps complete**: `mj-nav-stepper-complete` fires once; subsequent state
  changes do not re-fire.
- **Steps added/removed dynamically**: `MutationObserver` on the default slot
  re-indexes steps; `current` index is revalidated.
- **Error step in linear mode**: the error step is navigable (so the user can
  correct it) even if steps after it are upcoming.
- **Duplicate `status` attributes**: the component defers to the `current`
  attribute index as the canonical source; `status` on individual steps is
  advisory and may be overridden.

## 19. Acceptance criteria
- [ ] Renders `<ol>` with `<li>` items in correct order.
- [ ] `current` attribute highlights the active step with `aria-current="step"`.
- [ ] `status="complete"` shows checkmark; `status="error"` shows error icon.
- [ ] Linear mode: upcoming steps have `aria-disabled="true"`; not keyboard-reachable.
- [ ] Non-linear mode: all steps navigable; `mj-nav-stepper-change` fires on click.
- [ ] `compact` mode: labels in tooltips; indicators only visible.
- [ ] Horizontal and vertical orientations render correctly with connectors.
- [ ] RTL: horizontal order reverses; connectors direction correct.
- [ ] SSR: ordered list with text steps visible before script loads.
- [ ] `mj-nav-stepper-complete` fires when all steps reach `status="complete"`.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `<mj-nav-stepper>` support a `sub-steps` concept (steps within steps)
  or should that only be handled by `<mj-wizard>` via nested steppers?
- Should the error state prevent progression to the next step (enforced by the
  stepper) or is that always the wizard's responsibility?
