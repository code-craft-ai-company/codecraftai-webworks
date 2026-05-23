# Inline Editable Text Spec

- **Tag:** `<mj-inline-edit>`
- **Class / file:** `InlineEdit` / `inlineedit.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Inline editable text, Contenteditable region, Click-to-edit
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-inline-edit>` lets users click or press Enter on a piece of displayed text
to edit it in place. While editing, an input or textarea replaces the text with
explicit commit (Enter/button) and cancel (Escape/button) actions. The component
emits `mj-change` only on explicit commit — not on every keystroke — making it
safe for immediate server round-trips. It is designed for titles, labels, and table
cells where context switching to a separate form would be disruptive.

## 2. When to use / when not to use
**Use** for single values that need quick in-context editing: page titles,
task names, editable table cells, dashboard labels. **Do not use** for multi-field
forms — use a proper form instead. **Do not use** when all fields on a page are
editable simultaneously — prefer `<mj-text-field>` inside a form.

## 3. Anatomy
- **Display mode** — the default rendered state.
  - **Display text** (`part="display-text"`) — the visible, styled text content.
  - **Edit trigger** (`part="edit-trigger"`) — the pencil/edit icon button that activates editing.
- **Edit mode** — shown while editing.
  - **Input** (`part="input"`) — `<input type="text">` for single-line or `<textarea>` for multi-line mode.
  - **Commit button** (`part="commit-button"`) — confirms the change.
  - **Cancel button** (`part="cancel-button"`) — reverts to the previous value.
- **Error message** (`part="error"`) — shown below the input in edit mode when invalid.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Single-line | — (default) | Uses `<input type="text">` |
| Multi-line | `multiline` | Uses `<textarea>`; Enter inserts newline; Ctrl+Enter commits |
| Edit-on-click | `trigger="click"` (default) | Click on display text activates edit |
| Edit-on-button | `trigger="button"` | Only the pencil button activates edit; display text is not clickable |
| Compact | `compact` | No separate commit/cancel buttons; Enter commits, Escape cancels |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for form submission |
| `value` | string | `""` | yes | The current committed text value |
| `placeholder` | string | `""` | yes | Placeholder inside the input when editing |
| `label` | string | `""` | yes | Accessible label for the input (screen-reader only; the display text also serves as context) |
| `trigger` | `"click"\|"button"` | `"click"` | yes | What gesture activates edit mode |
| `multiline` | boolean | `false` | yes | Use textarea instead of input |
| `compact` | boolean | `false` | yes | Omit explicit commit/cancel buttons |
| `required` | boolean | `false` | yes | Value must be non-empty on commit |
| `maxlength` | number | — | yes | Maximum character count |
| `minlength` | number | — | yes | Minimum character count |
| `pattern` | string | — | yes | Regex pattern validated on commit |
| `disabled` | boolean | `false` | yes | Prevents entering edit mode |
| `readonly` | boolean | `false` | yes | Display-only; edit trigger hidden |
| `error-message` | string | `""` | yes | Override validation message shown on failed commit |
| `edit-label` | string | `"Edit"` | yes | Accessible label for the edit trigger button |
| `commit-label` | string | `"Save"` | yes | Accessible label for the commit button |
| `cancel-label` | string | `"Cancel"` | yes | Accessible label for the cancel button |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `editing` | boolean | Read-only; true when in edit mode |
| `pendingValue` | string | Read-only; the current value being typed (before commit) |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `display` | Custom display rendering; when provided, replaces the default `part="display-text"` span |
| `edit-icon` | Custom icon for the edit trigger button |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-edit-start` | `{ value: string }` | yes | yes | Fires when edit mode is entered; cancel to prevent |
| `mj-edit-cancel` | `{ value: string }` | yes | no | Fires when edit is cancelled; `value` is the unchanged committed value |
| `mj-change` | `{ value: string, previousValue: string }` | yes | yes | Fires on commit if value changed; cancel to prevent the commit |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when a commit attempt fails validation |

## 9. CSS parts & custom properties
**Parts:** `display-text`, `edit-trigger`, `input`, `commit-button`, `cancel-button`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-inline-edit-color` | `--mj-color-text-default` | Display text color |
| `--mj-inline-edit-font` | inherited | Display text font (inherits from parent) |
| `--mj-inline-edit-trigger-color` | `--mj-color-icon-subtle` | Edit trigger icon color |
| `--mj-inline-edit-input-bg` | `--mj-color-surface-input` | Input background in edit mode |
| `--mj-inline-edit-input-border-color` | `--mj-color-border-focus` | Input border in edit mode |
| `--mj-inline-edit-input-border-radius` | `--mj-radius-sm` | Input corner radius |
| `--mj-inline-edit-error-color` | `--mj-color-text-error` | Error message color |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Display (rest) | Styled text; edit trigger visible on hover/focus | Edit trigger `aria-label="Edit {value}"` |
| Edit mode | Input replaces text; commit/cancel buttons visible | Focus moves to input; `aria-label` on input |
| Invalid (commit attempted) | Error border on input; error message shown | `aria-invalid="true"` on input |
| Disabled | Display text dimmed; edit trigger hidden | `aria-disabled="true"` on host |
| Readonly | Display text; no edit trigger | — |

## 11. Behavior & interactions
- **Activating edit mode**: clicking the display text (when `trigger="click"`) or the edit trigger button enters edit mode. `mj-edit-start` fires (cancelable). If not cancelled, focus moves to the input which is pre-filled with the current `value`.
- **Committing**: pressing Enter (single-line) or Ctrl+Enter (multiline) or clicking the commit button runs constraint validation. If valid, `mj-change` fires with the new and previous values; if not cancelled, `value` is updated, edit mode exits, and focus returns to the edit trigger.
- **Cancelling**: pressing Escape or clicking the cancel button discards the pending edit, fires `mj-edit-cancel`, exits edit mode, and returns focus to the edit trigger.
- **Blur without commit**: if the input loses focus to anywhere outside the edit region (input, commit button, cancel button), the edit is automatically cancelled (safe default); this is configurable via a future `blur-commits` attribute.
- **Compact mode**: no visible commit/cancel buttons; Enter commits and Escape cancels; the input has `aria-describedby` pointing to a hint about the keyboard shortcuts.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` (display or trigger focused) | Activate edit mode |
| `Enter` (input focused, single-line) | Commit the edit |
| `Ctrl+Enter` (textarea focused, multiline) | Commit the edit |
| `Enter` (textarea, multiline, no modifier) | Insert newline |
| `Escape` (edit mode) | Cancel the edit; restore previous value; return focus to trigger |
| `Tab` (in edit mode, compact) | Move focus to commit button (if not compact), then cancel button |
| `Space` (on edit trigger button) | Activate edit mode |

## 13. Accessibility
- The display text region is not interactive when `trigger="click"` is the only
  method; screen readers are directed to use the edit trigger button which has
  `aria-label="Edit {value}"` (localizable with the value interpolated).
- When edit mode is active, focus moves to the input. The input has `aria-label`
  from the `label` attribute and `aria-describedby` pointing to the error (when
  present) and the compact-mode keyboard hint.
- `aria-invalid="true"` on the input when a commit attempt fails validation.
- Commit and cancel buttons are real `<button>` elements with `aria-label`.
- On cancel or commit, focus is explicitly returned to the edit trigger button.
- The component does not use `contenteditable` for the edit region — it uses
  a native `<input>` or `<textarea>` for reliable form semantics and screen-reader support.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Contributes `name`/committed `value` pair to `FormData`.
- Does NOT submit the pending (uncommitted) value — only the last committed value.
- Supports `required`, `minlength`, `maxlength`, `pattern` constraint validation
  checked at commit time with localizable messages.
- Form reset reverts `value` to the `value` attribute (or `""`) and exits edit
  mode if currently active.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `edit-label`, `commit-label`, `cancel-label`, error messages, and compact
  keyboard hint text are all localizable via the shared localization hook.
- The interpolated value in `aria-label="Edit {value}"` must be escaped to
  prevent injection.
- In RTL, the edit trigger icon appears on the inline-start (left) of the text;
  commit/cancel button order is reversed.

## 16. Progressive enhancement / SSR
- Server renders the display text as a plain `<span>` and an edit-trigger link
  pointing to a full edit page; without script the user is taken to the full form.
- On upgrade, the component replaces the link with the inline edit mechanism
  without removing the display text content.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Localization hook** (§6).

## 18. Edge cases & error handling
- `mj-edit-start` cancelled by host: edit mode is not entered; focus stays on the trigger.
- `mj-change` cancelled by host: the value update is reverted; edit mode remains open so the user can correct the value.
- Empty commit with `required`: validation fires; focus stays on the input with `aria-invalid`.
- `value` changed programmatically while in edit mode: the display value is updated but `pendingValue` is not overwritten (the user's in-progress edit is preserved).
- `disabled` set while in edit mode: edit mode is exited immediately; pending changes are discarded; `mj-edit-cancel` fires.
- Very long values in the display text: truncated with CSS `text-overflow: ellipsis`; full value is accessible in the `title` attribute and to screen readers.

## 19. Acceptance criteria
- [ ] Clicking display text (trigger="click") activates edit mode; focus moves to input.
- [ ] Edit trigger button activates edit mode via click, Enter, and Space.
- [ ] Enter commits single-line; Ctrl+Enter commits multiline; Escape cancels.
- [ ] `mj-change` fires only on successful commit; `mj-edit-cancel` fires on cancel.
- [ ] `mj-change` cancelable: cancellation keeps edit mode open.
- [ ] `required`, `minlength`, `maxlength`, `pattern` validation blocks commit; `aria-invalid` set.
- [ ] Focus returns to edit trigger after commit or cancel.
- [ ] Blur outside the edit region cancels the edit.
- [ ] Form submit includes last committed value; form reset exits edit mode and reverts value.
- [ ] `aria-label` on edit trigger includes the current value.
- [ ] axe audit passes in display and edit modes.

## 20. Open questions
- Should `blur-commits` be a supported attribute for the common pattern of "clicking away saves the edit"?
- Should multi-line mode support auto-grow height during editing?
- Should the component emit `mj-change` when the value is committed unchanged (value === previousValue)?
