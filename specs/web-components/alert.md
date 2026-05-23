# Alert Spec

- **Tag:** `<mj-alert>`
- **Class / file:** `MjAlert` / `mjalert.js`
- **Category:** Feedback & status components
- **Primary or Variant:** Primary
- **Synonyms covered:** Banner, Inline message, Callout, Status message, Error message, Warning message, Success message, Info message
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-alert>` is a contextual feedback message that communicates status or
outcome to the user. It covers the full severity range (info, success, warning,
error) and three placement patterns: **banner** (full-width, at the top of the
page or region), **inline** (within the flow of content), and **callout** (an
emphasized block within body copy). The component replaces ad-hoc colored `<div>`
solutions while ensuring severity is never conveyed by color alone.

## 2. When to use / when not to use

**Use** when you need to inform the user of an outcome, system state, or
contextual guidance that is directly relevant to their current task.

**Banner** — system-wide events, form-submission results, page-level errors.
**Inline** — field-adjacent or section-specific feedback.
**Callout** — editorial emphasis of important contextual information.

**Do not use** for transient notifications that should auto-dismiss — use
`<mj-toast>` instead. Do not use for interactive confirmations that require a
decision — use `<mj-dialog>` instead. Do not use in place of form validation
error messages — use the form Error primitive (§5.2).

## 3. Anatomy

- **Root container** (`part="container"`) — the outer element carrying the ARIA
  role and severity styling.
- **Icon** (`part="icon"`) — a severity-matched icon (info, check-circle,
  warning-triangle, error-circle); rendered inside a `<slot name="icon">` so
  hosts can override it; defaults are decorative (`aria-hidden`).
- **Content region** (`part="content"`) — wraps title and body.
  - **Title** (`part="title"`) — optional heading rendered from `<slot name="title">`.
  - **Body** (`part="body"`) — default slot for message text or rich content.
- **Action slot** (`part="actions"`) — `<slot name="actions">` for one or two
  inline action buttons (e.g. "Retry", "Dismiss action").
- **Dismiss button** (`part="dismiss"`) — an icon button rendered when
  `dismissible` is set; carries an accessible label.

## 4. Variants & modes

| Variant | `variant` value | Description |
|---------|-----------------|-------------|
| Inline  | `inline` (default) | Flows within the document; width determined by container |
| Banner  | `banner` | Full-width strip; typically placed at the top of a page region |
| Callout | `callout` | Block-level emphasis with stronger visual weight and a left accent border |

| Severity | `severity` value | Icon | Live-region role |
|----------|-----------------|------|-----------------|
| Informational | `info` (default) | Info circle | `status` (polite) |
| Success | `success` | Check circle | `status` (polite) |
| Warning | `warning` | Warning triangle | `status` (polite) |
| Error | `error` | Error circle | `alert` (assertive) |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `severity` | `"info"\|"success"\|"warning"\|"error"` | `"info"` | Yes | Controls color tokens, default icon, ARIA role, and live-region politeness |
| `variant` | `"inline"\|"banner"\|"callout"` | `"inline"` | Yes | Controls placement and visual treatment |
| `dismissible` | boolean | `false` | Yes | Renders a dismiss button; alert is removed from the DOM on dismiss |
| `heading` | string | `""` | Yes | Convenience attribute to set the title without using the `title` slot |
| `icon` | string | `""` | Yes | Token/name of the icon to use; overrides the default severity icon; empty string restores the default |
| `no-icon` | boolean | `false` | Yes | Suppresses the icon entirely |
| `open` | boolean | `true` | Yes | Controls visibility; setting to `false` hides the alert without removing it |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `severity` | `string` | Mirrors the `severity` attribute; settable by script |
| `open` | `boolean` | Programmatic show/hide without DOM removal; reflects to the `open` attribute |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | Message body — plain text or rich HTML (paragraphs, lists) |
| `title` | Optional alert heading rendered above the body |
| `icon` | Replaces the auto-selected severity icon with custom content |
| `actions` | Inline action button(s) placed after the body; use `<mj-button>` elements |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-alert-dismiss` | `{ severity, variant }` | Yes | Yes | Fired when the dismiss button is activated; canceling prevents DOM removal |
| `mj-alert-open` | `{ severity, variant }` | Yes | No | Fired when `open` transitions from `false` to `true` |
| `mj-alert-close` | `{ severity, variant }` | Yes | No | Fired when `open` transitions from `true` to `false` |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)` — root element
- `::part(icon)` — icon wrapper
- `::part(title)` — heading wrapper
- `::part(content)` — body content wrapper
- `::part(actions)` — action slot wrapper
- `::part(dismiss)` — dismiss button

**Custom properties**
| Property | Description |
|----------|-------------|
| `--mj-alert-bg` | Background color (defaults to severity token) |
| `--mj-alert-border-color` | Border/accent color (defaults to severity token) |
| `--mj-alert-color` | Foreground text color |
| `--mj-alert-icon-color` | Icon fill color |
| `--mj-alert-border-radius` | Corner radius |
| `--mj-alert-padding-block` | Block-axis padding |
| `--mj-alert-padding-inline` | Inline-axis padding |
| `--mj-alert-gap` | Gap between icon, content, and actions |
| `--mj-alert-callout-accent-width` | Width of the callout left-border accent |

## 10. States

- **default** — `open=true`; renders with the resolved severity tokens.
- **hidden** — `open=false`; `display:none` applied; no layout space taken.
- **dismissible** — dismiss button is visible and focusable.
- **no-icon** — icon wrapper is hidden; content shifts to fill the space.
- **focused-dismiss** — dismiss button shows focus ring per `focus-visible`.

## 11. Behavior & interactions

On render, the component sets `role="alert"` (error severity) or `role="status"`
(all other severities) on its container. Because the ARIA live region must be in
the DOM before content is injected, the shadow root is constructed synchronously
in the constructor and the live-region role is set before first paint.

When `dismissible` is set, activating the dismiss button fires
`mj-alert-dismiss`. If the event is not canceled, the element calls
`this.setAttribute('open', 'false')` and then removes itself from the DOM
after the CSS transition completes (listening for `transitionend`). If no
transition is defined, removal happens synchronously.

When `open` changes from `false` to `true` the alert re-injects the content
into the live region to trigger a re-announcement. A short `setTimeout(0)`
guards against the announcement being suppressed when the element was
just added to the DOM.

For the `banner` variant the component sets `role="region"` on its outer wrapper
and derives an accessible name from the `heading` attribute or `title` slot.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Moves focus to the dismiss button (if present) or to action buttons in slot order |
| `Enter` / `Space` | Activates the focused dismiss or action button |
| `Escape` | Activates dismiss when the dismiss button is focused (convenience shortcut) |

## 13. Accessibility

- **Roles:** `role="alert"` for `severity="error"` (assertive live region);
  `role="status"` for `info`, `success`, `warning` (polite live region).
  The `banner` variant wraps an additional `role="region"` landmark with an
  `aria-label` derived from the title.
- **States/properties:** `aria-live` is implicit in the role; no separate
  attribute needed. `aria-atomic="true"` ensures the full message is read when
  content changes.
- **Icon:** default severity icons are `aria-hidden="true"`; hosts that replace
  them via the `icon` slot must handle their own labelling.
- **Dismiss button:** has a visible label or `aria-label="Dismiss"` (localizable).
- **Color:** severity is communicated by icon + text label prefix (e.g. "Error:")
  in addition to color; meets 4.5:1 text contrast and 3:1 UI component contrast.
- **Target size:** dismiss button meets the 24 × 24 CSS px minimum; 44 × 44 px
  recommended touch target via padding.

## 14. Form participation

N/A — `<mj-alert>` is a display-only component.

## 15. Internationalization & RTL

- The dismiss button label defaults to `"Dismiss"` and is overridable via the
  `dismiss-label` attribute or the localization hook.
- Severity labels prepended for screen readers ("Error:", "Warning:", etc.) are
  overridable via the localization hook.
- In RTL contexts, icon and dismiss button swap sides; the callout accent border
  moves from `inline-start` to `inline-start` (already handled by logical
  properties throughout).
- All spacing uses logical CSS properties (`padding-inline`, `margin-block`).

## 16. Progressive enhancement / SSR

Server renders the alert as a styled `<div role="alert">` or `<div role="status">`
with inline class-based severity tokens. Before the script loads the content is
visible and readable. On upgrade, the custom element adopts the rendered content
into its shadow root slots, preserving text without layout shift.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle management and
  attribute/property reflection.
- **Design-token stylesheet** (§6) — severity color tokens.
- **Live-region/announcement service** (§6) — optional; used when imperatively
  updating alert content after initial render.
- **`<mj-button>`** (§5.3) — recommended element type for the `actions` slot and
  the dismiss button.

## 18. Edge cases & error handling

- **Empty content:** if both the default slot and `heading` are empty, the alert
  renders but logs a console warning; it is still accessible via its role.
- **Long text:** content wraps; no max-height truncation by default; hosts may
  apply `--mj-alert-max-height` and `overflow-y: auto` via `::part(content)`.
- **Conflicting attributes:** if `no-icon` and a custom `icon` are both set,
  `no-icon` wins.
- **Rapid open/close toggling:** transitions are debounced; if a new toggle
  arrives before `transitionend`, the in-progress transition is cancelled and the
  final state applied immediately.
- **Multiple alerts in a live region:** each `<mj-alert>` manages its own shadow
  live region; stacking multiple alerts on a page is supported without conflict.

## 19. Acceptance criteria

- [ ] Renders all four severity values with correct icon, color tokens, and ARIA role.
- [ ] Banner variant has `role="region"` with an accessible name.
- [ ] Callout variant renders the left accent border and elevated visual weight.
- [ ] `dismissible` renders a dismiss button that removes the alert on activation.
- [ ] `mj-alert-dismiss` is cancelable and prevents removal when canceled.
- [ ] `open=false` hides the alert; `open=true` restores it and re-announces.
- [ ] Screen reader announces error alerts assertively and other severities politely.
- [ ] Icon is `aria-hidden`; dismiss button has a localizable accessible name.
- [ ] All keyboard interactions work as specified.
- [ ] Passes automated axe accessibility checks with no violations.
- [ ] Renders usefully without JavaScript (SSR fallback).
- [ ] Callout accent border swaps to `inline-start` in RTL.
- [ ] Respects `prefers-color-scheme` and forced-colors.
- [ ] No hard-coded colors; all values resolve from design tokens.

## 20. Open questions

- Should the `banner` variant automatically insert itself into the page's top
  landmark, or remain in document flow at its authored position?
- Should a stacking/queuing strategy be defined at the Alert level for multiple
  simultaneous banners, or delegated entirely to the host page?
- Is a `compact` size variant needed where the icon and title share one line?
