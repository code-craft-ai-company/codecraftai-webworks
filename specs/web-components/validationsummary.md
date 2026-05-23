# Validation Summary Spec

- **Tag:** `<mj-validation-summary>`
- **Class / file:** `MjValidationSummary` / `mjvalidationsummary.js`
- **Category:** Text & data-entry controls — form-structure primitives
- **Primary or Variant:** Primary
- **Synonyms covered:** Validation summary, Error summary, Form error list
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-validation-summary>` aggregates all field-level validation errors from a
`<mj-form>` into a single, prominent, keyboard-reachable list at the top (or
bottom) of the form. Each error item is a link that moves focus directly to the
invalid control. The summary is hidden until the form is submitted with errors, and
receives programmatic focus on submission failure so keyboard and screen-reader
users are immediately aware of the problem scope before correcting individual fields.

## 2. When to use / when not to use
**Use** in any `<mj-form>` that has three or more fields, or in any form where
errors may appear outside the viewport. For single-field forms or inline-only
validation, the individual `<mj-error-message>` elements are sufficient.
**Do not use** for non-form contexts. **Do not use** to display application-level
alerts (use `<mj-alert>` instead).

## 3. Anatomy
- **Heading** — a visually styled, semantically correct heading (level determined
  by `heading-level` attribute) summarizing the error count, e.g., "3 errors
  prevented this form from being submitted".
- **Error list (`<ul>`)** — an unordered list of error items; one item per invalid
  control.
- **Error list item (`<li>`)** — contains an `<a href="#control-id">` link for each
  error; the link text is the field label plus the error message.
- **Leading icon slot** — optional icon placed before the heading (e.g., error-circle).

## 4. Variants & modes
| Variant | Attribute | Description |
|---------|-----------|-------------|
| Default | _(none)_ | Hidden until errors are present; displayed above the form fields |
| Always-render | `always-render` | Element occupies space when empty to avoid layout shift |
| Manual | `manual` | Errors are populated by the author via the `errors` property rather than auto-discovered from a `<mj-form>` |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `for` | string | `""` | Yes | ID of the associated `<mj-form>`; the summary listens for `mj-invalid` on that form |
| `visible` | boolean | `false` | Yes | Controls display; set automatically by the form on submission failure |
| `heading-level` | `"2"` \| `"3"` \| `"4"` \| `"5"` \| `"6"` | `"2"` | Yes | The HTML heading level for the summary title |
| `heading-text` | string | `"{count} error(s) prevented this form from being submitted"` | Yes | Overridable heading template; `{count}` is replaced with the error count |
| `always-render` | boolean | `false` | Yes | Keeps the element in layout even when there are no errors |
| `manual` | boolean | `false` | Yes | Disables auto-population from the associated form; caller populates via `errors` property |
| `focus-on-show` | boolean | `true` | Yes | Whether the summary container receives focus when it becomes visible |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `errors` | `Array<{ controlId: string, label: string, message: string }>` | The current list of errors. Setting this property replaces the displayed list and updates `visible` accordingly. Read by the form on submission; set manually in `manual` mode. |
| `count` | `number` | Read-only count of current errors; `0` when no errors |

## 7. Slots
| Slot | Description |
|------|-------------|
| `icon` | Leading icon before the heading; must be `aria-hidden="true"` |
| `heading` | Replaces the default generated heading when full control over heading markup is needed |
| _(default)_ | Not used; error list is generated from the `errors` property |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-show` | `{ errors: Array<{ controlId: string, label: string, message: string }>, count: number }` | Yes | No | Fires when the summary becomes visible with one or more errors |
| `mj-hide` | `{}` | Yes | No | Fires when the summary is cleared and hidden |
| `mj-error-click` | `{ controlId: string, label: string, message: string }` | Yes | No | Fires when the user clicks an error link; focus has already moved to the target control |

## 9. CSS parts & custom properties
| Part / Property | Description |
|-----------------|-------------|
| `::part(container)` | The outermost summary `<div>` |
| `::part(heading)` | The heading element (`<h2>`–`<h6>`) |
| `::part(list)` | The `<ul>` error list |
| `::part(item)` | Each `<li>` error item |
| `::part(link)` | Each `<a>` link inside an item |
| `::part(icon)` | The icon slot wrapper |
| `--mj-summary-bg` | Background color (default: `var(--mj-color-surface-error-subtle)`) |
| `--mj-summary-border-color` | Border color (default: `var(--mj-color-border-error)`) |
| `--mj-summary-border-radius` | Corner radius (default: `var(--mj-radius-md)`) |
| `--mj-summary-padding` | Inner padding (default: `var(--mj-space-4)`) |
| `--mj-summary-heading-color` | Heading text color (default: `var(--mj-color-text-error)`) |
| `--mj-summary-link-color` | Error link color (default: `var(--mj-color-text-link)`) |
| `--mj-summary-gap` | Gap between heading and list (default: `var(--mj-space-2)`) |

## 10. States
- **hidden** (default) — `[visible]` absent; `display: none` (or `visibility:
  hidden` with `always-render`); not in the tab order.
- **visible** — error list populated, container displayed, focus received
  (`focus-on-show` default `true`); announced as an alert on first appearance.
- **empty-visible** — edge case where `visible` is set but `errors` is empty; the
  component auto-hides and logs a console warning.
- **always-render / hidden** — occupies layout space; `aria-hidden="true"`;
  not announced.

## 11. Behavior & interactions
- When `for` is set, the component attaches a listener for `mj-invalid` on the
  referenced `<mj-form>`. On receiving the event it:
  1. Maps the event's `controls` array to `errors` entries by reading each
     control's associated `<mj-label>` text and `<mj-error-message>` text.
  2. Generates the error list DOM inside the shadow root.
  3. Sets `visible = true`.
  4. If `focus-on-show` is `true`, calls `focus()` on the summary container
     (which has `tabindex="-1"`).
- When `<mj-form>` fires `mj-submit` (valid submission), the summary clears its
  list and sets `visible = false`.
- Clicking an error link scrolls and focuses the target control. The link's
  `href="#control-id"` handles scroll; `focus()` is called programmatically to
  ensure reliable cross-browser focus.
- In `manual` mode, the host sets the `errors` property directly and manages
  `visible` independently.
- The heading text template substitutes `{count}` with the error count at render
  time. Singular/plural is the author's responsibility in `heading-text`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus from the summary container (or heading) to the first error link |
| `Tab` (through list) | Moves focus through each error link in order |
| `Enter` / `Space` (on link) | Follows the link: scrolls to and focuses the invalid control |
| `Shift+Tab` | Moves focus backwards through error links, then to the summary container |

## 13. Accessibility
- The summary container has `tabindex="-1"` so it can receive programmatic focus
  on show without being in the natural tab order when hidden.
- On first becoming visible the container is announced via `role="alert"` on the
  inner wrapper, alerting screen readers to the presence of form errors.
- Each error link has an accessible name formed as "fieldLabel: errorMessage"
  to give full context when the link is read in isolation (e.g., from a links list).
- The heading text must include the error count verbatim (not only in the list
  length) so the count is announced when focus arrives at the heading.
- The icon slot content must have `aria-hidden="true"` as the error status is
  conveyed in text.
- The list is a native `<ul>` inside the shadow DOM; list semantics are preserved.

## 14. Form participation
Not form-associated. Contributes no value to `FormData`. Acts as an observer and
display component driven by `<mj-form>` events.

## 15. Internationalization & RTL
- `heading-text` is fully overridable; the `{count}` token allows for locale-aware
  phrasing. Plural rules must be handled in the supplied string.
- Error link text is assembled from the associated control's label text (from
  `<mj-label>`) and error message (from `<mj-error-message>`); both are
  author-provided in the appropriate locale.
- In RTL layouts, icon and heading follow logical inline direction; the error list
  is right-aligned.

## 16. Progressive enhancement / SSR
Server renders the summary as a `<div role="alert" hidden>` with a pre-populated
error list when the form has been submitted with server-side validation errors.
`visible` is set by server markup absence of `hidden`. On upgrade the component
maps server-rendered list items to its internal `errors` array. Without scripting,
the server-rendered list is visible and the links work as anchor navigation to the
invalid fields.

## 17. Dependencies
- `web-component-development-plan.md` §6: Registry + base element helper,
  Live-region/announcement service, Focus utilities, Design-token stylesheet.
- `<mj-form>` — drives the summary via the `mj-invalid` event.
- `<mj-label>` — provides field label text for error link copy.
- `<mj-error-message>` — provides field error message text.
- Optional: `<mj-icon>` in the `icon` slot.

## 18. Edge cases & error handling
- `for` target form not found: logs a console warning; the summary remains in
  manual mode until the form appears (retried via `MutationObserver`).
- Error link target control not in the DOM at click time: link click is intercepted;
  a console warning is logged; no navigation occurs (avoids a broken `href`).
- All errors are corrected and the form is re-submitted successfully: the summary
  hides and its `errors` array is cleared.
- Very long list of errors (50+): the list renders without virtualization at this
  scale; pagination is not applied.
- `heading-text` does not contain `{count}`: the heading renders verbatim without
  a count; no error is thrown.
- Summary receives focus while an animated transition is in progress: focus is
  deferred until the transition completes (`transitionend` event).

## 19. Acceptance criteria
- [ ] Submitting a form with invalid controls causes the summary to appear with
      one error link per invalid control.
- [ ] Each error link text reads "fieldLabel: errorMessage".
- [ ] Clicking an error link scrolls to and focuses the corresponding invalid
      control.
- [ ] The summary container receives focus when it becomes visible (`focus-on-show`
      default `true`).
- [ ] A screen reader announces the summary heading and error count immediately on
      appearance.
- [ ] Submitting a valid form (after correcting errors) hides the summary.
- [ ] `manual` mode: setting `errors` property populates and shows the summary.
- [ ] RTL: list items are right-aligned; icon follows logical inline direction.
- [ ] No-JS: server-rendered error list is visible and anchor links navigate
      to invalid fields.
- [ ] Axe-core reports zero violations.

## 20. Open questions
- Should the summary support grouping errors by `<mj-fieldset>` (e.g., "Address
  section: 2 errors") in addition to flat per-field listing?
- Should `focus-on-show` default to `false` in some form layouts where the summary
  is always visible (e.g., a sticky summary panel), to avoid unexpected focus jumps?
