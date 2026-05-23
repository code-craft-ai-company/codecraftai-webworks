# Toast Spec

- **Tag:** `<mj-toast>`
- **Class / file:** `MjToast` / `mjtoast.js`
- **Category:** Feedback & status components
- **Primary or Variant:** Primary
- **Synonyms covered:** Snackbar, Notification, Toast notification
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-toast>` is a transient, non-modal notification that appears at the edge of
the viewport, informs the user of a status or action outcome, and optionally
auto-dismisses after a configurable timeout. It is managed by an accompanying
`<mj-toast-region>` that handles queueing, stacking, positioning, and live-region
semantics. Individual toasts are never the only channel for critical information.

## 2. When to use / when not to use

**Use** for brief, non-blocking confirmations of user-initiated actions
(e.g., "File saved", "Link copied") and low-priority background events
(e.g., "New message received").

**Do not use** for errors that require user action — use `<mj-alert>` or
`<mj-dialog>` instead. Do not use for content that users need to read at their
own pace; transient messages must not replace persistent feedback. Never use as
the sole channel for security-critical status.

## 3. Anatomy

- **Root container** (`part="container"`) — the outer positioned element; carries
  the ARIA live-region role.
- **Icon** (`part="icon"`) — optional severity icon; `aria-hidden` by default.
- **Content region** (`part="content"`) — wraps title and body.
  - **Title** (`part="title"`) — optional short heading from `<slot name="title">`.
  - **Body** (`part="body"`) — default slot for the notification message.
- **Action slot** (`part="actions"`) — `<slot name="actions">` for one optional
  inline action button (e.g., "Undo").
- **Dismiss button** (`part="dismiss"`) — close button; always present for
  keyboard/AT users even when `auto-dismiss` is set.
- **Progress bar** (`part="progress"`) — optional animated countdown bar showing
  remaining auto-dismiss time; hidden when `auto-dismiss` is not set.

## 4. Variants & modes

| Variant | `severity` value | Live-region politeness | Icon |
|---------|-----------------|------------------------|------|
| Informational | `info` (default) | polite | Info circle |
| Success | `success` | polite | Check circle |
| Warning | `warning` | polite | Warning triangle |
| Error | `error` | assertive | Error circle |

Auto-dismiss behavior:

| Mode | `auto-dismiss` | Description |
|------|---------------|-------------|
| Auto-dismiss | `> 0` (ms) | Toast dismisses after the timeout; timer pauses on hover or focus |
| Persistent | `0` or omitted | Toast remains until the user explicitly dismisses it |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `severity` | `"info"\|"success"\|"warning"\|"error"` | `"info"` | Yes | Severity level; drives icon, color tokens, and live-region politeness |
| `auto-dismiss` | number (ms) | `0` | Yes | Duration before auto-dismiss; `0` disables auto-dismiss |
| `heading` | string | `""` | Yes | Short title text; convenience alternative to the `title` slot |
| `no-icon` | boolean | `false` | Yes | Suppresses the default severity icon |
| `open` | boolean | `false` | Yes | Reflects the displayed state; set to `true` to show, `false` to hide/dismiss |
| `placement` | `"top-start"\|"top"\|"top-end"\|"bottom-start"\|"bottom"\|"bottom-end"` | `"bottom-end"` | Yes | Preferred viewport edge; overridden by the containing `<mj-toast-region>` when present |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `open` | `boolean` | Programmatic show/dismiss; mirrors the `open` attribute |
| `remainingTime` | `number` | Read-only; milliseconds remaining until auto-dismiss; `Infinity` when persistent |
| `pauseTimer` | `() => void` | Pauses the auto-dismiss countdown without dismissing the toast |
| `resumeTimer` | `() => void` | Resumes a paused countdown |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | Notification message body — plain text or rich inline HTML |
| `title` | Optional short heading rendered above the body |
| `icon` | Custom icon replacing the default severity icon |
| `actions` | One inline action button (e.g., `<mj-button variant="tertiary">Undo</mj-button>`) |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-toast-open` | `{ severity }` | Yes | No | Fired when the toast becomes visible |
| `mj-toast-dismiss` | `{ severity, reason: "auto"\|"user"\|"api" }` | Yes | Yes | Fired before the toast is removed; canceling keeps it open |
| `mj-toast-action` | `{ severity, action: string }` | Yes | No | Fired when an action button in the `actions` slot is activated; `action` is the button's `value` attribute |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)` — root element
- `::part(icon)` — icon wrapper
- `::part(title)` — heading wrapper
- `::part(content)` — body wrapper
- `::part(actions)` — action slot wrapper
- `::part(dismiss)` — dismiss button
- `::part(progress)` — auto-dismiss countdown bar

**Custom properties**
| Property | Description |
|----------|-------------|
| `--mj-toast-bg` | Background color |
| `--mj-toast-border-color` | Border color |
| `--mj-toast-color` | Foreground text color |
| `--mj-toast-icon-color` | Icon fill |
| `--mj-toast-border-radius` | Corner radius |
| `--mj-toast-padding-block` | Block-axis padding |
| `--mj-toast-padding-inline` | Inline-axis padding |
| `--mj-toast-shadow` | Box shadow / elevation |
| `--mj-toast-min-width` | Minimum width |
| `--mj-toast-max-width` | Maximum width |
| `--mj-toast-progress-color` | Countdown bar fill color |
| `--mj-toast-animation-duration` | Enter/exit animation duration |

## 10. States

- **closed** — `open=false`; element is `display:none` or not yet appended.
- **entering** — CSS animation plays as the toast slides/fades into view.
- **open** — `open=true`; visible and announced to AT.
- **paused** — auto-dismiss timer is paused (pointer hover or keyboard focus
  inside the toast); `[data-paused]` attribute set on the host.
- **exiting** — CSS exit animation plays before the element is removed.
- **focus-visible** — dismiss or action button shows focus ring.

## 11. Behavior & interactions

**Showing a toast.** The host page creates an `<mj-toast>` element and appends
it to an `<mj-toast-region>` (or to `document.body` as a fallback). The
`<mj-toast-region>` manages viewport positioning, stacking order, and the
announcement queue.

**Live region.** `<mj-toast-region>` owns a single off-screen ARIA live region
(`aria-live="polite"` for non-error; `aria-live="assertive"` for error). When a
toast opens, its text content is injected into the live region so assistive
technologies announce it without moving focus.

**Auto-dismiss timer.** When `auto-dismiss > 0`, a `setTimeout` starts after the
toast enters the open state. The timer is cleared and restarted on
`pointerenter`/`pointerleave` and paused on `focusin`/`focusout` within the
toast. On `transitionend` of the exit animation, the element is removed from the
DOM and `mj-toast-dismiss` fires with `reason="auto"`.

**Queueing.** `<mj-toast-region>` maintains a FIFO queue. When
`max-visible` is reached, incoming toasts are queued; the oldest visible toast
is not forcibly dismissed — new ones enter as older ones exit naturally.

**Reduced motion.** When `prefers-reduced-motion: reduce` matches, enter/exit
animations are replaced with an instant opacity change (no translate).

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the dismiss button, then action buttons in slot order, then out of the toast |
| `Shift+Tab` | Reverse focus order within the toast |
| `Enter` / `Space` | Activate the focused dismiss or action button |
| `Escape` | Dismiss the toast when focus is anywhere inside it |

## 13. Accessibility

- **Roles:** Individual toasts carry no ARIA role of their own; announcement is
  via the `<mj-toast-region>` live region. The dismiss button and action buttons
  use native `<button>` semantics.
- **Live region:** `<mj-toast-region>` exposes `aria-live="polite"` (non-error)
  or `aria-live="assertive"` (error) with `aria-atomic="true"`. The region is
  always in the DOM; toast text is injected on open.
- **Dismiss button:** always rendered; labeled `"Dismiss"` (localizable) even
  when only an icon is visible.
- **Focus:** toasts do not receive focus on open; they are reachable via `Tab`
  for users who want to interact with actions or dismiss manually.
- **Color:** severity is conveyed by icon and text, not color alone; 4.5:1
  text contrast; 3:1 UI component contrast.
- **Target size:** dismiss button minimum 24 × 24 CSS px; 44 × 44 px touch target.
- **Reduced motion:** animations respect `prefers-reduced-motion`.

## 14. Form participation

N/A — `<mj-toast>` is a display-only component.

## 15. Internationalization & RTL

- Dismiss button label defaults to `"Dismiss"` and is overridable via the
  `dismiss-label` attribute or the shared localization hook.
- Severity prefixes used in the live-region announcement ("Error:", "Success:",
  etc.) are overridable via the localization hook.
- Placement sides swap in RTL contexts (`top-end` becomes visual top-left);
  `inline-start`/`inline-end` logical properties are used throughout.
- The countdown progress bar direction respects `dir`.

## 16. Progressive enhancement / SSR

`<mj-toast>` is primarily a scripted component; meaningful SSR fallback is
limited. Server-rendered markup should include the toast content inside a
`<div role="status">` so the message is visible without JS. On upgrade, the
element adopts the content and applies interactive behavior. For pre-rendered
notifications that are always visible (not transient), prefer `<mj-alert>`.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle and attribute reflection.
- **Design-token stylesheet** (§6) — severity color tokens, elevation, motion.
- **Live-region/announcement service** (§6) — used by `<mj-toast-region>` to
  inject announcements into the managed live region.
- **Overlay/positioning engine** (§6) — viewport-edge placement and stacking
  when used without `<mj-toast-region>`.
- **`<mj-button>`** (§5.3) — dismiss button and action slot buttons.
- **`<mj-toast-region>`** — companion element (same file or a sibling module)
  that manages queueing, positioning, and the live-region container.

## 18. Edge cases & error handling

- **No `<mj-toast-region>`:** toast falls back to a fixed-position overlay at
  the `placement` position; the component creates its own minimal live region.
- **Very long message text:** wraps within `--mj-toast-max-width`; does not
  truncate; height grows.
- **Rapid creation:** `<mj-toast-region>` queues excess toasts; does not drop
  them silently.
- **Action button text overflow:** action text truncates with ellipsis; full
  text available via `title` attribute.
- **`auto-dismiss` set to very small values (< 1000 ms):** clamped to 1000 ms
  minimum to ensure the user can read the message; a console warning is emitted.
- **Timer during CPU throttling:** the countdown uses `performance.now()` deltas
  rather than assuming `setInterval` fires on time; remaining time is corrected
  on each tick.

## 19. Acceptance criteria

- [ ] Toast renders with correct severity icon, color tokens, and text.
- [ ] `auto-dismiss` timer starts on open, pauses on hover/focus, resumes on leave/blur.
- [ ] `mj-toast-dismiss` fires with correct `reason`; canceling it prevents removal.
- [ ] `mj-toast-action` fires when an action button is activated.
- [ ] `<mj-toast-region>` announces toast text via the correct live-region politeness.
- [ ] Error-severity toasts use `aria-live="assertive"`; all others use `"polite"`.
- [ ] Dismiss button is always present and keyboard-operable.
- [ ] `Escape` key dismisses the toast when focus is inside it.
- [ ] Enter/exit animations respect `prefers-reduced-motion`.
- [ ] RTL placement sides are mirrored correctly.
- [ ] Queueing: toasts beyond `max-visible` wait and appear as others dismiss.
- [ ] No hard-coded colors; all values resolve from design tokens.
- [ ] Passes automated axe accessibility checks with no violations.

## 20. Open questions

- Should `<mj-toast-region>` be a separate spec file, or fully specified within
  this document?
- What is the default `max-visible` count for the toast region (2? 3?)?
- Should the countdown progress bar be opt-in (default hidden) or opt-out
  (default shown when `auto-dismiss` is set)?
- Is a "persistent history" drawer (Notification center) triggered from the
  toast region in scope for P0 or deferred to P2?
