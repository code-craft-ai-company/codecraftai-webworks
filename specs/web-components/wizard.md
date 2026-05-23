# Wizard Spec

- **Tag:** `<mj-wizard>`
- **Class / file:** `MjWizard` / `mjwizard.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Wizard, Multi-step form, Guided flow, Setup flow
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-wizard>` is a multi-step guided flow component that composes `<mj-nav-stepper>`
for progress indication with a managed content area and built-in navigation
buttons (Back, Next, Submit). It orchestrates step activation, validation gates,
focus management between steps, and lifecycle events for each step transition.

## 2. When to use / when not to use
**Use** when a task requires collecting or displaying information in a defined
sequence where each step must complete before the next. **Do not use** for simple
forms that fit on a single page. **Do not use** for optional navigation between
views — use `<mj-tabs>`. **Do not use** if the stepper indicator alone is enough
without managed content — use `<mj-nav-stepper>` directly.

## 3. Anatomy
- **Host element** — outer wrapper with `role="group"` and `aria-label`.
- **Step indicator** (`::part(stepper)`) — embedded `<mj-nav-stepper>` showing progress.
- **Content area** (`::part(content)`) — panel container; shows one `<mj-wizard-step>` at a time.
- **Active step panel** (`::part(panel)`) — the visible `<mj-wizard-step>`; receives focus on step change.
- **Navigation bar** (`::part(nav-bar)`) — footer bar containing Back, Next, and Submit buttons.
- **Back button** (`::part(back-btn)`) — previous-step trigger; hidden on step 0.
- **Next button** (`::part(next-btn)`) — next-step trigger; hidden on last step.
- **Submit button** (`::part(submit-btn)`) — form submission trigger; shown only on last step.
- **Step slot** — light-DOM slot into which `<mj-wizard-step>` elements are placed.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Linear | `linear` (default) | User cannot skip ahead; Next validates current step |
| Non-linear | _(no `linear`)_ | Steps reachable in any order; no validation gate |
| Stepper top | `stepper-position="top"` | Step indicator above content |
| Stepper side | `stepper-position="side"` | Step indicator to the left/start of content |
| Stepper hidden | `stepper-position="none"` | No visible step indicator |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `current` | number | `0` | Yes | Zero-based index of the active step |
| `linear` | boolean | `true` | Yes | Enforces sequential progression |
| `stepper-position` | string | `"top"` | Yes | Where to render the `<mj-nav-stepper>`: `top` \| `side` \| `none` |
| `label` | string | `"Wizard"` | Yes | `aria-label` for the `role="group"` host; announced on step transitions |
| `submit-label` | string | `"Submit"` | Yes | Label for the submit button on the last step |
| `next-label` | string | `"Next"` | Yes | Label for the Next button |
| `back-label` | string | `"Back"` | Yes | Label for the Back button |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `steps` | `Element[]` | Ordered array of `<mj-wizard-step>` elements |
| `currentStep` | `Element \| null` | Reference to the active `<mj-wizard-step>` |
| `isFirstStep` | boolean | Read-only; `true` when `current === 0` |
| `isLastStep` | boolean | Read-only; `true` when `current === steps.length - 1` |
| `valid` | boolean | Read-only; `true` when the current step's associated form is valid |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | `<mj-wizard-step>` elements defining each step's label and content |
| `actions` | Optional override slot for the navigation button bar; replaces built-in Back/Next/Submit |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-wizard-before-change` | `{ from: number, to: number, direction: "next" \| "back" \| "jump" }` | Yes | Yes | Fires before step changes; cancel to block |
| `mj-wizard-change` | `{ from: number, to: number, direction: string }` | Yes | No | Fires after the panel transitions to the new step |
| `mj-wizard-step-enter` | `{ index: number, step: Element }` | Yes | No | Fires when a step panel becomes active and focused |
| `mj-wizard-step-leave` | `{ index: number, step: Element }` | Yes | No | Fires when a step panel is about to be hidden |
| `mj-wizard-submit` | `{ formData: FormData \| null }` | Yes | Yes | Fires when the Submit button is activated on the last step; cancel to handle submission manually |
| `mj-wizard-complete` | `{}` | Yes | No | Fires after a successful submit (when not canceled) |

## 9. CSS parts & custom properties
**Parts**
- `::part(root)` — inner layout flex container
- `::part(stepper)` — the embedded `<mj-nav-stepper>`
- `::part(content)` — the panel content area
- `::part(panel)` — the active step panel wrapper
- `::part(nav-bar)` — the navigation button bar
- `::part(back-btn)` / `::part(next-btn)` / `::part(submit-btn)` — individual nav buttons

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-wizard-content-padding` | `var(--mj-spacing-6)` | Padding around the active step content |
| `--mj-wizard-nav-bar-padding` | `var(--mj-spacing-4) var(--mj-spacing-6)` | Padding of the navigation button bar |
| `--mj-wizard-nav-bar-border` | `1px solid var(--mj-color-border-muted)` | Top border of the nav bar |
| `--mj-wizard-stepper-width` | `200px` | Width of the side-positioned stepper |
| `--mj-wizard-min-height` | `320px` | Minimum height of the content area |
| `--mj-wizard-transition-duration` | `var(--mj-motion-duration-medium)` | Step-change cross-fade or slide duration |

## 10. States
- **default** — first step active; Back button hidden.
- **mid-flow** — steps 1..n-2 active; Back and Next visible.
- **last-step** — final step active; Next hidden; Submit visible.
- **loading** — Next/Submit disabled while async validation or submission runs;
  buttons show `aria-busy="true"` and loading spinner.
- **step-error** — current step has validation errors; Next is disabled; error
  summary shown within the step content.
- **completed** — `mj-wizard-complete` has fired; the wizard may show a
  completion state or redirect.

## 11. Behavior & interactions
- The wizard manages one `<mj-wizard-step>` as visible at a time; all others
  have the `hidden` attribute on their wrapper.
- On "Next": the wizard calls `checkValidity()` on any form inside the current
  step's content. If invalid, it calls `reportValidity()` and blocks progression.
  If valid (or `linear` is false), it increments `current`.
- On "Back": decrements `current`; no validation.
- After a step change, focus is moved to the heading or first focusable element
  within the newly active `<mj-wizard-step>` using the Section 6 focus utility.
- In `linear` mode, the embedded `<mj-nav-stepper>` uses `linear` mode; clicking
  upcoming steps is suppressed.
- The Submit button triggers `mj-wizard-submit` with any `FormData` aggregated
  from all steps' `<form>` elements. If not canceled, `mj-wizard-complete` fires.
- Step transition animation: a brief cross-fade or slide respects
  `prefers-reduced-motion` (no animation if reduced motion preferred).

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves through interactive content within the active step, then reaches nav buttons |
| `Enter` / `Space` | Activates Back, Next, or Submit buttons |
| `Escape` | No built-in action at the wizard level; individual step content may use Escape |
| Arrow keys | Not intercepted by the wizard itself; delegated to the embedded `<mj-nav-stepper>` |

## 13. Accessibility
- Host has `role="group"` and `aria-label` from the `label` attribute, grouping
  the stepper, content, and nav bar.
- On step change, focus moves to the new step's panel; the panel has
  `tabindex="-1"` to be programmatically focusable and has an accessible heading.
- The active step panel is announced as a live region change via a
  `role="status"` element that reads: "Step {n} of {total}: {stepTitle}".
- Navigation buttons have clear accessible names; Back and Next convey
  direction; Submit is labelled distinctly.
- When Next is disabled due to validation, the reason is communicated via an
  associated `aria-describedby` error summary.
- The embedded `<mj-nav-stepper>` handles its own ARIA per that spec.

## 14. Form participation
- The wizard is not itself a form-associated custom element.
- Each `<mj-wizard-step>` may contain one or more `<form>` or form controls;
  the wizard calls `checkValidity()` on them during Next-gate validation.
- The `mj-wizard-submit` event detail includes a `FormData` object aggregated
  from all step forms so the host page can submit a single request.

## 15. Internationalization & RTL
- Button labels (`next-label`, `back-label`, `submit-label`) are localizable via
  attributes or the localization hook keys: `mj.wizard.next`, `.back`, `.submit`.
- Step announcement template: `mj.wizard.stepAnnounce` with `{current}`,
  `{total}`, `{title}` interpolations.
- In RTL, the Back and Next buttons swap visual positions (Back on the right,
  Next on the left) to match reading direction.
- `stepper-position="side"` places the stepper on the inline-end in RTL.

## 16. Progressive enhancement / SSR
- Server renders steps as visible sections with headings and form fields;
  navigation buttons may be native `<button>` elements.
- Before upgrade: all step content is visible on the page (no hidden states);
  users can scroll through the full form.
- On upgrade: the wizard hides all but the first step, inserts the `<mj-nav-stepper>`,
  and activates the managed flow — a graceful enhancement from long-form to
  step-by-step.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet, focus
  utility, localization hook.
- `<mj-nav-stepper>` — embedded for step progress indication.
- `<mj-nav-step>` — created programmatically from `<mj-wizard-step>` labels.
- `<mj-button>` — used for Back, Next, and Submit controls.
- `<mj-wizard-step>` — companion element for individual step content panels.

## 18. Edge cases & error handling
- **Single step**: Back hidden; Next hidden; Submit shown immediately; stepper
  shows one step.
- **All steps invalid**: Submit is never reachable in linear mode; in non-linear
  mode, Submit fires with `formData` containing partial data; host logic decides.
- **`current` changed programmatically beyond `steps.length`**: clamped with a
  console warning.
- **Async validation on Next**: while awaiting, the Next button is disabled and
  shows a spinner; if the async call rejects, an error message is shown in the
  step and progression is blocked.
- **Step removed from DOM**: wizard re-indexes; if the removed step was current,
  previous step becomes active.
- **`stepper-position="none"` in linear mode**: no visual step indicator;
  the live-region announcement still fires to inform screen readers.

## 19. Acceptance criteria
- [ ] Shows one step at a time; all others have `hidden` attribute.
- [ ] Back hidden on first step; Submit shown on last step; Next otherwise.
- [ ] Next gate: invalid step form blocks progression; `reportValidity()` called.
- [ ] Focus moves to new step panel on change; step announced via live region.
- [ ] `mj-wizard-before-change` cancelable; canceling blocks transition.
- [ ] `mj-wizard-submit` fires on Submit; cancel prevents `mj-wizard-complete`.
- [ ] `<mj-nav-stepper>` embedded and reflects step state (current/complete/error).
- [ ] `stepper-position` controls stepper placement correctly.
- [ ] RTL: Back/Next swap positions; side stepper moves to inline-end.
- [ ] SSR: all step content visible before script; wizard upgrades gracefully.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should the wizard support a persistent summary/review panel on the final step
  that aggregates values from all prior steps?
- Should async step-level validation be configured on `<mj-wizard-step>` via a
  `validate` event or a property-bound function reference?
