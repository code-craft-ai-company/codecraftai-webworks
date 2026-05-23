# Toast Region Spec

- **Tag:** `<mj-toast-region>`
- **Class / file:** `MjToastRegion` / `mjtoastregion.js`
- **Category:** Feedback & status components / Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Toast region, Snackbar container, Notification toaster
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-toast-region>` is the singleton placement and queuing manager for transient notification toasts. It controls the fixed-position region where `<mj-toast>` items appear, enforces a configurable display limit, sequences queued toasts, manages auto-dismiss timing (paused on hover/focus), and provides the live region through which screen readers are informed of notifications.

## 2. When to use / when not to use

Place one `<mj-toast-region>` per application viewport, typically as a direct child of `<body>`. All programmatic and declarative toasts are routed through it. Use toasts for non-blocking feedback that does not require user action (success confirmations, non-critical errors). Never use toasts as the only delivery channel for critical information requiring a response — use `<mj-dialog alertdialog>` for that. Do not stack more than three visible toasts simultaneously.

## 3. Anatomy

- **Region container** — the fixed-position list element acting as the `aria-live` region.
- **Toast stack** — ordered list of currently visible `<mj-toast>` items.
- **Queue** — internal FIFO of pending toasts waiting to be displayed.
- **`<mj-toast>` items** — individual toast elements rendered inside the region.

## 4. Variants & modes

| Placement | `placement` value | Notes |
|-----------|-----------------|-------|
| Bottom-end (default) | `bottom-end` | Standard lower-right (lower-left in RTL) |
| Bottom-start | `bottom-start` | Lower-left (lower-right in RTL) |
| Bottom-center | `bottom-center` | Centered bottom; common for mobile |
| Top-end | `top-end` | Upper-right |
| Top-start | `top-start` | Upper-left |
| Top-center | `top-center` | Centered top |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `placement` | `top-start` \| `top-center` \| `top-end` \| `bottom-start` \| `bottom-center` \| `bottom-end` | `bottom-end` | Yes | Viewport placement of the toast stack |
| `max-visible` | number | `3` | Yes | Maximum number of simultaneously visible toasts |
| `gap` | string | `var(--mj-space-3)` | Yes | Spacing between visible toasts |
| `offset-x` | string | `var(--mj-space-4)` | Yes | Horizontal offset from viewport edge |
| `offset-y` | string | `var(--mj-space-4)` | Yes | Vertical offset from viewport edge |
| `polite` | boolean | `false` | Yes | When true, forces `aria-live="polite"` for all toasts; default is per-toast severity |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `queue` | `ToastDescriptor[]` | Read-only; pending toasts not yet displayed |
| `visible` | `MjToast[]` | Read-only; currently displayed toast elements |
| `count` | `number` | Total of queued + visible toasts |

## 7. Slots

| Slot | Description |
|------|-------------|
| (none) | Toast items are programmatically created via `add()` or by dispatching `mj-toast-request` on the region |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-toast-add` | `{ id: string, descriptor: ToastDescriptor }` | Yes | No | Fired when a toast is added to the queue or display |
| `mj-toast-show` | `{ id: string }` | Yes | No | Fired when a toast becomes visible |
| `mj-toast-dismiss` | `{ id: string, reason: 'auto' \| 'user' \| 'api' }` | Yes | No | Fired when a toast is dismissed |
| `mj-toast-queue-empty` | `{}` | Yes | No | Fired when the queue and visible list both become empty |

## 9. CSS parts & custom properties

**Parts:**
- `::part(region)` — the outermost `<ol>` list container
- `::part(toast)` — individual toast items (delegated to `<mj-toast>`)

**Custom properties:**
- `--mj-toast-region-z-index` — z-index (default: `var(--mj-z-toast)`)
- `--mj-toast-region-gap` — overrides `gap` attribute
- `--mj-toast-region-offset-x` — overrides `offset-x` attribute
- `--mj-toast-region-offset-y` — overrides `offset-y` attribute
- `--mj-toast-max-width` — maximum width of individual toast items (default: `24rem`)

## 10. States

- **Empty:** No visible or queued toasts; region is present but visually empty.
- **Active:** One or more toasts visible; region is visible in the viewport corner.
- **Queue saturated:** Queue holds items beyond `max-visible`; oldest items are displayed first.
- **Hover/focus paused:** Any visible toast is hovered or focused; all auto-dismiss timers pause.
- **Reduced motion:** Slide/fade-in animations disabled; toasts appear instantly.

## 11. Behavior & interactions

**Adding a toast:** Callers invoke `toastRegion.add(descriptor)` or dispatch a `mj-toast-request` CustomEvent on the region (or anywhere in the document if the region is listening). A `ToastDescriptor` contains `{ message, severity, duration, actions, id? }`. If `visible.length < max-visible`, a `<mj-toast>` is created and appended immediately. Otherwise it is pushed to the queue.

**Auto-dismiss:** Each visible toast starts a countdown (`duration` ms, default 5000ms for `info`, 8000ms for `error`). When the countdown reaches zero, the toast exits with a dismiss animation and `mj-toast-dismiss` fires with `reason: 'auto'`. The next queued toast is then promoted.

**Pause on hover/focus:** When any pointer enters or any focusable element inside the region receives focus, all running countdowns are suspended. They resume when the pointer leaves and focus exits the region.

**User dismiss:** A close button on each `<mj-toast>` triggers immediate dismiss with `reason: 'user'`.

**Severity-based live politeness:** `error` and `warning` toasts use `aria-live="assertive"` (interrupt AT); `info` and `success` toasts use `aria-live="polite"` (queue announcement). The `polite` attribute on the region forces all toasts to polite.

**Queue promotion:** After a toast dismisses, the region checks the queue and promotes the first item if `visible.length < max-visible`.

**Layout:** Toasts stack with newer items appearing closer to the viewport edge (i.e., toasts push upward from the bottom corner). Each item's enter/exit animation is a vertical slide + fade.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Moves focus into the toast region; focuses the first interactive element of the first toast |
| `Shift+Tab` | Moves focus backward through toast actions |
| `Escape` (when focus inside toast region) | Dismisses the focused toast |
| `Enter` / `Space` on toast action | Activates the toast's action button |
| `Enter` / `Space` on close button | Dismisses the toast |

## 13. Accessibility

- **Role:** The region container is an `<ol>` element with `aria-live` and `aria-label="Notifications"` (overridable via `region-label` attribute). Each `<mj-toast>` is an `<li>` within it.
- **`aria-live`:** The region uses either `"assertive"` or `"polite"` depending on severity (see §11). The live attribute is set on the region container, not individual items, to ensure AT picks up content additions.
- **`aria-atomic="false"`:** New toast text is announced without repeating the entire list.
- **`aria-relevant="additions"`:** Only additions are announced; removal animations are not re-announced.
- **Focus:** The toast region is reachable by Tab; focus does not auto-move to it on toast arrival. Keyboard users can Tab into the region to read and dismiss toasts.
- **Non-blocking:** The region is `role="region"` with a distinctive label; keyboard users skip it using the bypass/skip-link mechanism.
- **Timer awareness:** Countdown timers are paused on focus (§11) so keyboard users have time to read and act.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- `placement="bottom-end"` resolves to bottom-right in LTR and bottom-left in RTL.
- `region-label` attribute (default `"Notifications"`) is the localized accessible name for the live region.
- Individual toast messages are always supplied by the caller and are their responsibility to localize.

## 16. Progressive enhancement / SSR

The region renders as an empty `<ol>` landmark server-side. Without JS, no toasts appear (toasts are inherently dynamic). The region is inert until the component upgrades and `add()` is called.

## 17. Dependencies

- **Section 6:** Design-token stylesheet, Live-region service.
- **`<mj-toast>`** — the individual toast item component rendered inside the region.

## 18. Edge cases & error handling

- **Multiple `<mj-toast-region>` elements:** A warning is logged if more than one is registered; the first registered is treated as authoritative. Subsequent regions operate independently.
- **`max-visible=0`:** Disables display; all toasts are queued indefinitely (effectively a buffer). Warning logged.
- **Toast with `duration=0`:** Toast is persistent until explicitly dismissed by the user or API.
- **Region removed from DOM while toasts are active:** `disconnectedCallback` clears all timers; toasts are removed; no memory leak.
- **Very long toast message:** Toast wraps to multiple lines; region respects `--mj-toast-max-width`; close button remains accessible.
- **Rapid burst of toasts:** Queue absorbs all; they are promoted one at a time as visible slots open.

## 19. Acceptance criteria

- [ ] Only `max-visible` toasts are shown simultaneously; extras queue.
- [ ] Queued toasts promote when a visible toast dismisses.
- [ ] Auto-dismiss timers pause when pointer enters or focus enters any toast; resume on leave/blur.
- [ ] `aria-live="assertive"` for error/warning; `aria-live="polite"` for info/success.
- [ ] `mj-toast-show` fires when a toast becomes visible; `mj-toast-dismiss` fires with correct reason.
- [ ] `mj-toast-queue-empty` fires when all toasts are cleared.
- [ ] Keyboard focus reaches toast actions via Tab; Esc dismisses focused toast.
- [ ] `placement` correctly positions the region in all six positions.
- [ ] RTL swaps start/end placements.
- [ ] Region remains accessible with `role="region"` and labeled `aria-label`.
- [ ] Reduced-motion: no slide/fade animations.
- [ ] axe-core reports zero violations with visible toasts.

## 20. Open questions

- Should `<mj-toast-region>` listen for a global `mj-toast-request` event on `window` so any script anywhere can trigger a toast without needing a direct reference to the region element?
- Should a maximum queue depth be configurable to prevent memory growth from burst notifications?
- Should toasts support rich HTML content (via a `content` slot) or message-string only?
