# Copy Button Spec

- **Tag:** `<mj-copy-button>`
- **Class / file:** `MjCopyButton` / `mjcopybutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Copy button, Copy-to-clipboard button
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-copy-button>` copies a text value to the system clipboard using the async
Clipboard API. It provides transient visual and accessible confirmation that the copy
succeeded, and graceful feedback when it fails. This removes repeated boilerplate for
one of the most common utility actions in developer-facing and productivity UIs.

## 2. When to use / when not to use

Use alongside code blocks, API keys, shareable URLs, email addresses, or any
read-only text the user is likely to want copied. Do not use for binary data or
files — those belong to `<mj-share-button>` or a download link. Do not use as a
substitute for a proper form input when the user should be able to edit the value.

## 3. Anatomy

- **Host element** — the custom element.
- **button (part)** — inner `<button>`; the focusable, clickable target.
- **icon-copy (part)** — icon shown in the idle state (`slot="icon-copy"`).
- **icon-success (part)** — icon shown during the success confirmation window
  (`slot="icon-success"`).
- **icon-error (part)** — icon shown during the error state (`slot="icon-error"`).
- **label (part)** — default slot for visible button label (optional).

## 4. Variants & modes

| Mode                  | Attribute             | Description |
|-----------------------|-----------------------|-------------|
| Icon only             | `icon-only`           | Shows only the copy icon; `label` provides accessible name |
| Icon + label          | (default)             | Icon and label both visible |
| Source reference      | `for` attribute       | Copies text content of an element identified by id |
| Inline value          | `value` attribute     | Copies the literal string in `value` |

## 5. Attributes

| Attribute        | Type                               | Default           | Reflects | Description |
|------------------|------------------------------------|-------------------|----------|-------------|
| `value`          | string                             | —                 | Yes      | Text to copy; takes precedence over `for` |
| `for`            | string (id)                        | —                 | Yes      | Id of a source element whose `textContent` or `value` is copied |
| `variant`        | `primary\|secondary\|tertiary`     | `tertiary`        | Yes      | Visual emphasis |
| `size`           | `sm\|md\|lg`                       | `md`              | Yes      | Token-mapped dimensions |
| `disabled`       | boolean                            | `false`           | Yes      | Disables interaction; `aria-disabled="true"` |
| `icon-only`      | boolean                            | `false`           | Yes      | Hides label visually; requires `label` |
| `label`          | string                             | `"Copy"`          | Yes      | Accessible name; visible when not `icon-only` |
| `success-label`  | string                             | `"Copied!"`       | Yes      | Label shown and announced during success window |
| `error-label`    | string                             | `"Copy failed"`   | Yes      | Label shown and announced on failure |
| `timeout`        | number (ms)                        | `2000`            | Yes      | Duration of the success/error confirmation window |

## 6. Properties

| Property  | Type                            | Description |
|-----------|---------------------------------|-------------|
| `status`  | `'idle'\|'success'\|'error'`    | Current confirmation state (read-only) |
| `sourceEl`| `HTMLElement \| null`           | Resolved source element from `for` attribute (read-only) |

## 7. Slots

| Slot           | Description |
|----------------|-------------|
| (default)      | Visible button label (used when not `icon-only`) |
| `icon-copy`    | Icon in idle state (defaults to an internal clipboard icon) |
| `icon-success` | Icon in success state (defaults to an internal checkmark icon) |
| `icon-error`   | Icon in error state (defaults to an internal warning icon) |

## 8. Events

| Event          | `detail`                                    | Bubbles | Cancelable | Description |
|----------------|---------------------------------------------|---------|------------|-------------|
| `mj-copy`      | `{ value: string }`                         | Yes     | No         | Fires when the copy operation succeeds |
| `mj-copy-error`| `{ error: Error }`                          | Yes     | No         | Fires when the copy operation fails |

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<button>`
- `::part(icon-copy)` — idle icon wrapper
- `::part(icon-success)` — success icon wrapper
- `::part(icon-error)` — error icon wrapper
- `::part(label)` — label text wrapper

**Custom properties**
| Property | Description |
|---|---|
| `--mj-copy-button-bg` | Background in idle state |
| `--mj-copy-button-bg-success` | Background during success window |
| `--mj-copy-button-bg-error` | Background during error state |
| `--mj-copy-button-color` | Color in idle state |
| `--mj-copy-button-color-success` | Color during success window |
| `--mj-copy-button-color-error` | Color during error state |
| `--mj-copy-button-border-radius` | Corner radius |
| `--mj-copy-button-height` | Height (size token) |
| `--mj-copy-button-focus-ring-color` | Focus ring color |
| `--mj-copy-button-transition` | Color/icon transition duration |

## 10. States

| State    | Visual effect | ARIA effect |
|----------|---------------|-------------|
| idle     | Resting colors; copy icon | — |
| success  | Success token colors; checkmark icon; auto-reverts after `timeout` ms | Live region announces `success-label` |
| error    | Error token colors; warning icon; auto-reverts after `timeout` ms | Live region announces `error-label` |
| disabled | Reduced opacity; no pointer events | `aria-disabled="true"` |
| hover    | Tinted overlay | — |
| focus-visible | 2 px focus ring | — |
| active   | Pressed tint | — |

## 11. Behavior & interactions

- On activation the component calls `navigator.clipboard.writeText(value)`.
- The text to copy is resolved in priority order: `value` attribute → `textContent`
  (or `.value` if an input) of the element identified by `for` → empty string (which
  is a no-op copy; a console warning is emitted).
- On success: `status` becomes `"success"`; the success icon and `success-label` are
  shown; the live-region service announces `success-label` politely; `mj-copy` fires.
  After `timeout` milliseconds the button automatically returns to `"idle"`.
- On failure: `status` becomes `"error"`; the error icon and `error-label` are
  shown; the live region announces `error-label` assertively; `mj-copy-error` fires.
  After `timeout` ms the button returns to `"idle"`.
- If the Clipboard API is unavailable (no `navigator.clipboard` or permission
  denied), the error path is taken immediately.
- A second activation while the success/error window is active resets the timer
  and attempts a new copy.
- `prefers-reduced-motion`: icon/color transitions are suppressed.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Space`     | Activates the copy action |
| `Enter`     | Activates the copy action |
| `Tab`       | Moves focus to next focusable element |
| `Shift+Tab` | Moves focus to previous focusable element |

## 13. Accessibility

- The inner `<button>` carries the native button role.
- `aria-label` reflects the current state label: `label` when idle, `success-label`
  when succeeded, `error-label` when failed; this gives screen readers a consistent
  name that changes to announce the outcome.
- Success and error outcomes are additionally announced via the shared live-region
  service so users with focus elsewhere are also notified.
- When `icon-only` is set, the visible label is hidden and `aria-label` carries the
  full accessible name.
- The success/error icons are `aria-hidden="true"` — state is communicated by label
  and live region.
- Minimum target size: 44 × 44 CSS px.

## 14. Form participation

N/A. `<mj-copy-button>` is not a form-associated element.

## 15. Internationalization & RTL

- `label`, `success-label`, and `error-label` are localizable via the shared
  localization hook; default values are English and must be overridden for other
  locales.
- RTL layout: icon and label order mirrors via CSS logical properties.
- No locale-aware formatting required for copy content.

## 16. Progressive enhancement / SSR

Server renders `<mj-copy-button value="abc123" label="Copy key">Copy key</mj-copy-button>`.
Before upgrade, the element renders as inline text with no interactive behavior.
When scripting is unavailable, the copy affordance is absent; the source value should
also be displayed as selectable text so users can copy it manually. On upgrade, the
inner `<button>` is rendered and the Clipboard API is wired.

## 17. Dependencies

- **Registry + base element helper** (§6)
- **Design-token stylesheet** (§6)
- **Live-region service** (§6) — success and error announcements
- **Localization hook** (§6) — `label`, `success-label`, `error-label` strings

## 18. Edge cases & error handling

- Neither `value` nor `for` is set: console warning; copy is a no-op; no event fired.
- `for` references a non-existent element: console warning; falls back to `value`
  if set, otherwise no-op.
- `for` references a non-input element: uses `textContent`.
- `for` references an `<input>` or `<textarea>`: uses `.value`.
- Clipboard API permission denied by the browser: error path taken; `mj-copy-error`
  fired with the `NotAllowedError`.
- `timeout` set to `0`: success/error state reverts synchronously after the next
  micro-task tick.

## 19. Acceptance criteria

- [ ] Clicking copies the `value` attribute text to the clipboard.
- [ ] Clicking copies the text content of the `for`-referenced element when `value` is absent.
- [ ] Success state shown with success icon and `success-label`; reverts to idle after `timeout` ms.
- [ ] Error state shown with error icon and `error-label` when Clipboard API fails.
- [ ] `mj-copy` fires on success with `{ value }` detail.
- [ ] `mj-copy-error` fires on failure with `{ error }` detail.
- [ ] Live region announces `success-label` politely on success.
- [ ] Live region announces `error-label` assertively on failure.
- [ ] `disabled` blocks activation and sets `aria-disabled="true"`.
- [ ] `icon-only` with `label` sets `aria-label`; without `label` emits console warning.
- [ ] Icons in all three states are `aria-hidden="true"`.
- [ ] Keyboard: Space and Enter activate; Tab navigates naturally.
- [ ] Minimum target size 44 × 44 CSS px.
- [ ] axe scan zero violations in idle, success, and error states.
- [ ] Light, dark, high-contrast, RTL rendering verified.

## 20. Open questions

- Should the success/error window auto-revert timer be cancellable via an attribute
  (`auto-reset="false"`) for cases where the consumer wants to control the reset?
- Should a `fallback` attribute or property provide a legacy `execCommand` path for
  environments that lack the async Clipboard API (e.g. in-iframe contexts)?
- Confirm default icon assets: should the component ship internal SVG defaults or
  require consumer-provided `icon-copy` / `icon-success` / `icon-error` slots?
