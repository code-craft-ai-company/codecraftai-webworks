# Tour Spec

- **Tag:** `<mj-tour>`
- **Class / file:** `MjTour` / `mjtour.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Tour, Onboarding tour, Onboarding coach mark, Product walkthrough, Feature spotlight
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-tour>` sequences a series of anchored `<mj-popover>` coach-mark steps across page elements to guide users through a feature or onboarding flow. Each step spotlights a target element, displays a title and body, and offers Next, Back, and Skip/Done controls. Tours are fully dismissible, resumable, and keyboard-navigable.

## 2. When to use / when not to use

Use for first-time user onboarding, feature introductions, and contextual walkthroughs of complex interfaces. Use when the sequence of steps is linear and tied to specific UI elements. Do not use for reference documentation (use inline help or a Drawer). Do not auto-start tours on every visit — respect a `dismissed` / `completed` flag in storage. Never make tour steps the sole explanation of a feature; the UI must be self-explanatory without the tour.

## 3. Anatomy

- **Step popover** — an `<mj-popover>` anchored to the current step's `target` element.
- **Spotlight overlay** — a full-viewport `<mj-overlay>` with a cutout (CSS `clip-path` or `outline`/box-shadow technique) highlighting the target element.
- **Coach-mark card** — the popover content area with title, body, step counter, and navigation buttons.
- **Step counter** — "Step N of M" progress display.
- **Progress dots** — optional row of dots indicating step position.
- **Navigation buttons** — Back, Next/Done, Skip controls.
- **Close (Skip) button** — in the popover header; dismisses the entire tour.

## 4. Variants & modes

| Variant | `variant` value | Notes |
|---------|----------------|-------|
| Anchored (default) | `anchored` | Each step anchored to a specific target element with spotlight |
| Floating | `floating` | Step popover centered in the viewport (no anchor, no spotlight); used for non-element-specific steps |
| Modal | `modal` | Step shown inside a full `<mj-dialog>` instead of a popover |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `active` | boolean | `false` | Yes | Starts or resumes the tour |
| `current-step` | number | `0` | Yes | Zero-based index of the current step |
| `variant` | `anchored` \| `floating` \| `modal` | `anchored` | Yes | Layout strategy for step display |
| `show-progress-dots` | boolean | `true` | Yes | Shows the dot row progress indicator |
| `show-counter` | boolean | `true` | Yes | Shows the "Step N of M" text counter |
| `spotlight` | boolean | `true` | Yes | Enables the spotlight cutout overlay |
| `spotlight-padding` | number | `8` | Yes | Padding in px around the spotlighted element |
| `storage-key` | string | `""` | Yes | `localStorage` key to persist dismissed/completed state; empty = no persistence |
| `skip-label` | string | `"Skip tour"` | Yes | Label for the skip/dismiss button |
| `done-label` | string | `"Done"` | Yes | Label for the finish button on the last step |
| `next-label` | string | `"Next"` | Yes | Label for the Next button |
| `back-label` | string | `"Back"` | Yes | Label for the Back button |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `steps` | `TourStep[]` | Array of step descriptors; `TourStep` has `{ targetId, title, body, placement?, variant?, beforeShow?, afterHide? }` |
| `totalSteps` | `number` | Count of steps in the tour |
| `isComplete` | `boolean` | `true` when the last step has been confirmed |
| `isDismissed` | `boolean` | `true` when the tour was skipped before completion |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | `<mj-tour-step>` child elements declaring the step set declaratively |
| `step-title` | Custom title for the current step (override) |
| `step-body` | Custom body content for the current step |
| `navigation` | Custom navigation button area replacing built-in Back/Next/Skip |
| `progress` | Custom progress indicator area |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-tour-start` | `{ totalSteps: number }` | Yes | No | Fired when the tour begins |
| `mj-tour-step` | `{ step: number, totalSteps: number, stepDef: TourStep }` | Yes | Yes | Fired before showing each step; cancelable to prevent advance |
| `mj-tour-next` | `{ step: number, totalSteps: number }` | Yes | No | Fired when the user advances to the next step |
| `mj-tour-back` | `{ step: number, totalSteps: number }` | Yes | No | Fired when the user goes back to the previous step |
| `mj-tour-skip` | `{ step: number }` | Yes | No | Fired when the user skips/dismisses the tour |
| `mj-tour-complete` | `{ totalSteps: number }` | Yes | No | Fired when the last step is confirmed |

## 9. CSS parts & custom properties

**Parts:**
- `::part(popover)` — the step popover container
- `::part(card)` — the coach-mark card inner content area
- `::part(title)` — step title element
- `::part(body)` — step body content
- `::part(counter)` — the "Step N of M" text
- `::part(dots)` — the progress dot container
- `::part(dot)` — individual progress dot
- `::part(back-button)` — the Back navigation button
- `::part(next-button)` — the Next/Done button
- `::part(skip-button)` — the Skip button
- `::part(spotlight)` — the spotlight overlay element

**Custom properties:**
- `--mj-tour-card-width` — coach-mark card width (default: `20rem`)
- `--mj-tour-card-padding` — card padding (default: `var(--mj-space-5)`)
- `--mj-tour-card-radius` — card radius (default: `var(--mj-radius-lg)`)
- `--mj-tour-card-shadow` — card shadow (default: `var(--mj-elevation-4)`)
- `--mj-tour-card-bg` — card background (default: `var(--mj-color-surface)`)
- `--mj-tour-spotlight-color` — spotlight overlay color (default: `var(--mj-color-black-alpha-50)`)
- `--mj-tour-dot-size` — progress dot size (default: `8px`)
- `--mj-tour-dot-active-color` — active dot color (default: `var(--mj-color-primary)`)
- `--mj-tour-z-index` — z-index (default: `var(--mj-z-tour)`)

## 10. States

- **Inactive:** `active=false`; no popover or overlay visible.
- **Active — step shown:** Current step's popover visible; spotlight covers the target; navigation buttons present.
- **Active — first step:** Back button hidden or disabled.
- **Active — last step:** Next button label changes to "Done".
- **Dismissed:** Tour has been skipped; `isDismissed=true`; state optionally persisted.
- **Complete:** All steps confirmed; `isComplete=true`; state optionally persisted.
- **Target not found:** Step target element is missing from the DOM; step skips automatically or shows a floating fallback.
- **Reduced motion:** Popover appears without animation; spotlight appears instantly.

## 11. Behavior & interactions

**Starting:** Setting `active=true` or calling `start()` checks `storage-key` for a persisted dismissed/completed state. If not dismissed and not complete, the tour begins at `current-step`. `mj-tour-start` fires.

**Step display:** For each step, the component:
1. Calls `step.beforeShow?.()` if defined.
2. Scrolls the `target` element into view (`scrollIntoView({ block: 'center', behavior: 'smooth' })`).
3. Positions `<mj-popover>` anchored to the target with the step's `placement` (defaulting to `bottom-start`).
4. Renders the spotlight overlay with a CSS `box-shadow` / `outline` cutout around the target, sized with `spotlight-padding`.
5. Moves focus to the Next button inside the popover card.
6. Fires `mj-tour-step`; if canceled, the step is aborted and the tour pauses.

**Navigation:** "Next" advances `current-step` by 1 and fires `mj-tour-next`. On the last step, activating "Done" fires `mj-tour-complete` and deactivates the tour. "Back" decrements `current-step` and fires `mj-tour-back`. "Skip" fires `mj-tour-skip`, sets `isDismissed=true`, deactivates the tour, and persists the state if `storage-key` is set.

**Spotlight:** Implemented via a full-viewport `<div>` with `box-shadow: 0 0 0 9999px var(--mj-tour-spotlight-color)` and `border-radius` matching the target. The overlay's `clip-path` or an inner transparent window exposes the target element. The spotlight element is updated on `ResizeObserver` and `scroll` events to track the target.

**Focus management:** Focus moves to the first focusable element of the step popover card on each step. The spotlight overlay itself is `aria-hidden` and not in the focus order. When the tour ends, focus returns to the element that had focus before the tour started.

**Persistence:** When `storage-key` is set, `isDismissed` and `isComplete` are written to `localStorage` on skip/complete. On `start()`, these are read to skip re-showing a completed or dismissed tour.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Cycles focus among Back, Next/Done, Skip buttons in the card |
| `Enter` or `Space` on Next | Advances to the next step |
| `Enter` or `Space` on Back | Returns to the previous step |
| `Enter` or `Space` on Skip | Dismisses the tour |
| `Escape` | Dismisses the tour (equivalent to Skip) |
| `ArrowRight` | Advances to the next step (when focus is within the tour card) |
| `ArrowLeft` | Returns to the previous step (when focus is within the tour card) |

## 13. Accessibility

- **Roles:** The step popover card has `role="dialog"` (via `<mj-popover>` or an explicit wrapper) with `aria-label` set to the step title. This makes each step a distinct modal-like region announced by AT.
- **`aria-modal`:** Spotlight overlay and popover together act like a modal; `aria-modal="true"` is set on the card dialog. Background content receives `inert` via the spotlight overlay layer.
- **Focus management:** Each step move focuses the Next button (the primary action). Users can Tab to Back and Skip. Focus is never lost between steps.
- **`aria-live` progress:** A `aria-live="polite"` region announces step changes: "Step 2 of 5: [step title]".
- **Skip control:** Always available and keyboard-reachable; labeled with `skip-label` attribute.
- **Spotlight overlay:** `aria-hidden="true"`; the visual cutout is purely decorative.
- **Target element:** The spotlighted element is not given `aria-describedby` pointing to the tour card — the card is self-contained. However, the target is scrolled into view and is interactable if the user needs to inspect it.
- **Scroll behavior:** `scrollIntoView` respects `prefers-reduced-motion` by using `behavior: 'instant'` when reduced motion is preferred.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Built-in button labels (`skip-label`, `done-label`, `next-label`, `back-label`) are attributes and fully overridable.
- Counter format: default `"Step {current} of {total}"`; overridable via `counter-format` attribute.
- RTL: The Back and Next button order swaps. Popover placement directions invert for `start`/`end`. Arrow-key navigation (ArrowLeft/ArrowRight) follows logical reading direction.

## 16. Progressive enhancement / SSR

`<mj-tour>` renders nothing visible server-side. Without JS, no tour is shown and the page is fully usable without it. On upgrade, the component registers event listeners and is ready to start when triggered. A declarative `<mj-tour-step>` sub-element API allows step definitions in server-rendered HTML.

## 17. Dependencies

- **Section 6:** Overlay/positioning engine, Focus utilities, Design-token stylesheet, Live-region service.
- **`<mj-popover>`** — step card display and anchor positioning.
- **`<mj-overlay>`** — spotlight backdrop layer.
- **`<mj-button>`** — navigation buttons.

## 18. Edge cases & error handling

- **Target element not in DOM when step shows:** The step skips to the next with a console warning; if all steps have missing targets, the tour exits gracefully.
- **Target scrolled out of view between steps:** `scrollIntoView` runs on each step transition.
- **Tour started on a page without matching targets:** All steps skip; `mj-tour-complete` fires immediately with a console warning.
- **`storage-key` collision across multiple tours:** Each tour must use a unique `storage-key`; no enforcement, but documented.
- **Tour re-started after completion:** If `storage-key` records completion, `start()` is a no-op. Call `reset()` to clear the persisted state and restart.
- **Viewport too small for card:** Card is constrained by `<mj-popover>` collision detection; may flip or shift to fit.
- **Step `beforeShow` returning a rejected Promise:** Tour pauses at that step; a warning is logged; resume is manual via `next()`.

## 19. Acceptance criteria

- [ ] Setting `active=true` starts the tour at `current-step=0`.
- [ ] Each step scrolls the target into view and anchors the popover to it.
- [ ] Spotlight overlay renders with a cutout around the target, sized by `spotlight-padding`.
- [ ] Focus moves to the Next button on each step transition.
- [ ] `mj-tour-step` fires before each step and is cancelable.
- [ ] Next button advances the step; Back button regresses it.
- [ ] Skip button and Escape both dismiss the tour and fire `mj-tour-skip`.
- [ ] On the last step, the Next button label changes to `done-label`; activating it fires `mj-tour-complete`.
- [ ] Dismissed/completed state persists to `localStorage` when `storage-key` is set.
- [ ] Tour does not restart if `localStorage` records dismissal or completion.
- [ ] Focus returns to the pre-tour element when the tour ends.
- [ ] Background content is `inert` while the tour is active.
- [ ] `aria-live` region announces the current step on each transition.
- [ ] Missing target elements are skipped gracefully.
- [ ] RTL: arrow key directions, button order, and placement flip correctly.
- [ ] Reduced-motion: no scroll animation and no popover transition animation.
- [ ] axe-core reports zero violations at each step.

## 20. Open questions

- Should `<mj-tour>` support branching step sequences (conditional next step based on user state), or is linear-only acceptable for v1?
- Should the spotlight support rectangular cutouts only, or also circular cutouts for icon-only targets?
- Should `reset()` be a public method or should resetting be handled entirely by clearing the `storage-key` value externally?
