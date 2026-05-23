# Dialog Spec

- **Tag:** `<mj-dialog>`
- **Class / file:** `MjDialog` / `mjdialog.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Modal dialog, Non-modal dialog, Alert dialog, Confirmation dialog, Prompt dialog
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-dialog>` is a modal or non-modal dialog built on the native `<dialog>` element. It provides a structured surface for focused user interactions — confirmations, alerts, form-based prompts, and general content — with full focus trapping (modal), backdrop management via `<mj-overlay>`, and proper ARIA semantics distinguishing `dialog` from `alertdialog` variants.

## 2. When to use / when not to use

Use when an interaction requires a dedicated, interruptive response before the user continues (confirmation, destructive action, data collection). Use `alertdialog` variant for urgent alerts requiring an immediate decision. Do not use for transient status messages (use `<mj-toast-region>`), non-blocking hints (use `<mj-popover>`), or navigation panels (use `<mj-drawer>`). Prefer inline content for non-critical secondary information.

## 3. Anatomy

- **Native `<dialog>` root** — provides top-layer promotion and native Esc handling.
- **`<mj-overlay>` backdrop** — dimming layer injected behind the dialog when `modal`.
- **Header** — optional title slot and close button.
- **Body** — scrollable main content area.
- **Footer** — optional action buttons (confirm, cancel, etc.).
- **Close button** — icon button in the header; labeled "Close dialog".

## 4. Variants & modes

| Variant | `variant` value | Role | Notes |
|---------|----------------|------|-------|
| Modal dialog | `dialog` (default) | `dialog` | Focus trapped; background inert; backdrop shown |
| Non-modal dialog | `dialog` + `modal="false"` | `dialog` | No focus trap; no backdrop; Esc still closes |
| Alert dialog | `alertdialog` | `alertdialog` | Focus moves to primary action; background inert |
| Confirmation dialog | `confirmation` | `alertdialog` | Resolves boolean; Confirm/Cancel buttons required |
| Prompt dialog | `prompt` | `alertdialog` | Contains an input; resolves with the entered value |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Opens the dialog; maps to native `<dialog open>` |
| `variant` | `dialog` \| `alertdialog` \| `confirmation` \| `prompt` | `dialog` | Yes | Selects ARIA role and behavior mode |
| `modal` | boolean | `true` | Yes | When true, traps focus and shows backdrop |
| `label` | string | `""` | Yes | `aria-label` override; falls back to heading slot text |
| `label-id` | string | `""` | Yes | ID of an external element to use as `aria-labelledby` |
| `description-id` | string | `""` | Yes | ID of an element for `aria-describedby` |
| `close-on-backdrop` | boolean | `true` | Yes | Whether clicking the backdrop closes the dialog |
| `no-close-button` | boolean | `false` | Yes | Hides the built-in header close button |
| `return-focus-id` | string | `""` | Yes | ID of element to restore focus to; auto-detected if absent |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `returnFocusEl` | `HTMLElement \| null` | Element to receive focus on close; set programmatically or auto-detected |
| `promptValue` | `string` | Current value of the prompt input (prompt variant only) |
| `nativeDialog` | `HTMLDialogElement` | Reference to the internal `<dialog>` element |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Main body content |
| `header` | Custom header content; replaces the built-in title + close button |
| `title` | Dialog heading text; used for `aria-labelledby` |
| `footer` | Action buttons and supplemental controls |
| `close-icon` | Custom icon for the close button |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-dialog-open` | `{ variant }` | Yes | No | Fired after the dialog opens and focus moves inside |
| `mj-dialog-close` | `{ variant, reason: 'close-button' \| 'backdrop' \| 'escape' \| 'api' }` | Yes | No | Fired after the dialog closes and focus is restored |
| `mj-dialog-confirm` | `{ value: string \| boolean }` | Yes | No | Fired when the confirm action is taken (confirmation/prompt variants) |
| `mj-dialog-cancel` | `{}` | Yes | No | Fired when the cancel/dismiss action is taken |
| `mj-dialog-before-close` | `{ reason }` | Yes | Yes | Fired before closing; canceling prevents close |

## 9. CSS parts & custom properties

**Parts:**
- `::part(dialog)` — the native `<dialog>` element
- `::part(header)` — the header bar
- `::part(title)` — the title element
- `::part(close-button)` — the header close icon button
- `::part(body)` — the scrollable content area
- `::part(footer)` — the footer action area
- `::part(overlay)` — the backdrop overlay

**Custom properties:**
- `--mj-dialog-width` — max-width of the dialog (default: `32rem`)
- `--mj-dialog-padding` — body padding (default: `var(--mj-space-6)`)
- `--mj-dialog-radius` — border radius (default: `var(--mj-radius-lg)`)
- `--mj-dialog-shadow` — box shadow (default: `var(--mj-elevation-4)`)
- `--mj-dialog-z-index` — z-index layer (default: `var(--mj-z-dialog)`)
- `--mj-dialog-bg` — background color (default: `var(--mj-color-surface)`)

## 10. States

- **Closed (default):** `open` attribute absent; `<dialog>` is `hidden`; not in top layer.
- **Open / focused:** `open` present; focus inside dialog; backdrop visible when modal.
- **Alert/Confirmation:** focus lands on primary action button on open.
- **Prompt active:** focus lands on the prompt `<input>`.
- **Backdrop active:** `<mj-overlay>` visible; `inert` applied to siblings.
- **Reduced motion:** open/close animations suppressed via `prefers-reduced-motion`.

## 11. Behavior & interactions

**Opening:** `open` attribute set or `show()` / `showModal()` method called. The component calls `nativeDialog.showModal()` when `modal=true`, promoting it to the top layer. `<mj-overlay>` is rendered behind the dialog. All sibling DOM trees receive `inert` (or equivalent `aria-hidden`). Focus moves to the first focusable element inside the dialog (or the dialog element itself if none).

**Focus trap (modal):** A focus trap sentinel is installed at the start and end of the dialog's focusable content. Tab/Shift+Tab cycles within. The Section 6 focus-trap utility manages this.

**Closing:** Triggered by Esc, backdrop click (when `close-on-backdrop=true`), the close button, or programmatic `close()`. The `mj-dialog-before-close` event fires; if not canceled, the dialog closes, `inert` is removed, focus returns to `returnFocusEl` (the element that triggered the open, or the element matching `return-focus-id`).

**Confirmation variant:** Renders Confirm and Cancel buttons in the footer. Confirm emits `mj-dialog-confirm` with `{ value: true }`. Cancel emits `mj-dialog-cancel`.

**Prompt variant:** Renders a labeled text input in the body and Confirm/Cancel in the footer. Confirm emits `mj-dialog-confirm` with `{ value: promptValue }`. Enter in the input triggers confirm.

**Scroll lock:** When modal, `overflow: hidden` is applied to `<body>` via a counter-based scroll-lock utility that supports multiple stacked modals.

**Animation:** Entry is a fade+scale-in; exit is a fade+scale-out. Durations read from `--mj-duration-enter` / `--mj-duration-exit` tokens.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Escape` | Closes the dialog (fires `mj-dialog-before-close` with `reason: 'escape'`) |
| `Tab` | Moves focus to the next focusable element within the dialog (wraps at end) |
| `Shift+Tab` | Moves focus to the previous focusable element within the dialog (wraps at start) |
| `Enter` | In prompt variant's input, triggers confirm action |
| `Space` or `Enter` on close button | Closes the dialog with `reason: 'close-button'` |

## 13. Accessibility

- **Roles:** `dialog` for standard and non-modal variants; `alertdialog` for alert, confirmation, and prompt variants.
- **Naming:** `aria-labelledby` points to the `title` slot element ID when present; falls back to `aria-label` from the `label` attribute.
- **Description:** `aria-describedby` wired to `description-id` attribute or auto-detected body paragraph.
- **`aria-modal="true"`** set on the native `<dialog>` when `modal=true`, reinforcing top-layer semantics for AT.
- **Inertness:** All content outside the dialog receives `inert` when modal, preventing AT from reaching background content.
- **Focus management:** On open, focus moves to the first focusable interactive element or the dialog root. On close, focus returns to the triggering element.
- **Alert variant initial focus:** Focus lands on the least-destructive action button (Cancel preferred over Confirm for destructive confirmations).
- **Screen reader announcements:** The dialog title is announced immediately on open via role semantics; no additional live region needed.
- **Forced colors:** Dialog border and shadow preserve in forced-color mode.

## 14. Form participation

The prompt variant hosts a text input internally but is not itself form-associated. The input's value is surfaced via `promptValue` property and the `mj-dialog-confirm` event detail. If the consuming application needs a proper form control inside the dialog, that form control is slotted as normal content.

## 15. Internationalization & RTL

- Built-in strings (close button label `"Close dialog"`, default Confirm/Cancel labels) are overridable via `close-label`, `confirm-label`, `cancel-label` attributes.
- RTL: the close button switches corners; footer button order reverses via `dir`-aware flex layout.
- Prompt input inherits document direction.

## 16. Progressive enhancement / SSR

Server renders a `<mj-dialog>` with slotted content. Without JS, the native `<dialog>` element is present but not modal; it can be wired with a basic CSS `:target` trick for minimal disclosure. On upgrade, the component takes over open/close lifecycle, adds the backdrop, and installs focus management.

## 17. Dependencies

- **Section 6:** Overlay/positioning engine (`<mj-overlay>`), Focus-trap utility, Live-region service, Design-token stylesheet.
- **`<mj-overlay>`** — backdrop rendering and scroll lock.
- **`<mj-button>`** — built-in close, Confirm, Cancel buttons.

## 18. Edge cases & error handling

- **Multiple open dialogs:** Each dialog stacks in the top layer; scroll lock uses a reference counter. Focus trap stacks correctly.
- **No focusable elements:** Focus falls back to the `<dialog>` element itself (`tabindex="-1"` set internally).
- **Long content:** Body scrolls internally; header and footer remain sticky.
- **`return-focus-id` target removed from DOM:** Falls back to `document.body`; a warning is logged.
- **Conflicting `open` + `modal` changes while open:** Changes are queued and applied synchronously on next open.
- **Nested dialogs:** Each trap is independently installed; Esc closes only the topmost.
- **Missing title slot:** `aria-label` from `label` attribute is used; if both absent, a console warning is emitted.

## 19. Acceptance criteria

- [ ] `showModal()` promotes dialog to top layer; `show()` opens non-modally.
- [ ] Tab and Shift+Tab cycle focus only within the open modal dialog.
- [ ] Esc closes the dialog; `mj-dialog-before-close` fires and is cancelable.
- [ ] Focus returns to the triggering element after close.
- [ ] `alertdialog` role is set for alert/confirmation/prompt variants.
- [ ] Background content is `inert` and unreachable by keyboard or AT when modal.
- [ ] `aria-modal="true"` present on modal dialogs.
- [ ] `aria-labelledby` resolves to the title slot element.
- [ ] Backdrop click closes dialog when `close-on-backdrop=true`; does not close when `false`.
- [ ] Prompt variant emits `mj-dialog-confirm` with the entered value on confirm.
- [ ] Confirmation variant emits `mj-dialog-confirm` with `true` on confirm, `mj-dialog-cancel` on cancel.
- [ ] Scroll lock applied to `<body>` when modal; released on close.
- [ ] Close button accessible name is "Close dialog".
- [ ] Forced-colors, dark-theme, RTL, and reduced-motion modes pass visual regression.
- [ ] axe-core reports zero violations in open state.

## 20. Open questions

- Should the prompt variant support multi-line (textarea) input via a `prompt-multiline` attribute?
- Do we expose a `::backdrop` custom property passthrough, or rely solely on `<mj-overlay>` for backdrop styling?
- Should stacking order between multiple open dialogs be managed by `<mj-dialog>` itself or by a shared overlay-manager singleton?
