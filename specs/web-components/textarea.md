# Textarea Spec

- **Tag:** `<mj-textarea>`
- **Class / file:** `Textarea` / `textarea.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Multi-line text input
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-textarea>` enhances the native `<textarea>` element with design-system
styling, optional auto-grow (height expands as the user types), configurable
min/max row counts, and an integrated character/word counter — while remaining a
form-associated custom element. It is the go-to component for multi-line free-text
entry such as comments, descriptions, and messages.

## 2. When to use / when not to use
**Use** for any multi-line text entry: comments, bios, message bodies, addresses,
code snippets without syntax highlighting. **Do not use** when single-line entry
suffices — prefer `<mj-text-field>`. **Do not use** when formatting controls are
required — prefer `<mj-rich-text-editor>`. **Do not use** when markdown syntax is
preferred — prefer `<mj-markdown-editor>`.

## 3. Anatomy
- **Wrapper** (`part="wrapper"`) — block container that positions the textarea and resize handle.
- **Native textarea** (`part="textarea"`) — the real `<textarea>` element.
- **Label** (`part="label"`).
- **Help text** (`part="help"`).
- **Error message** (`part="error"`).
- **Counter** (`part="counter"`) — character or word count shown at the trailing end below the field.
- **Resize handle** (`part="resize-handle"`) — visible drag target; hidden when `auto-grow` is set.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Fixed size | — | User can resize via the handle (within min/max) |
| Auto-grow | `auto-grow` | Height expands with content; no resize handle |
| Min/max rows | `min-rows` / `max-rows` | Height clamped between row bounds |
| Character counter | `maxlength` set | Shows current/max character count |
| Word counter | `count-words` | Shows word count instead of character count |
| No resize | `no-resize` | Disables the resize handle without auto-grow |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for form submission |
| `value` | string | `""` | yes | Current text value |
| `placeholder` | string | `""` | yes | Placeholder text |
| `label` | string | `""` | yes | Visible label above the field |
| `help-text` | string | `""` | yes | Hint text below the field |
| `error-message` | string | `""` | yes | Override validation message |
| `rows` | number | `3` | yes | Initial visible row count |
| `min-rows` | number | `2` | yes | Minimum rows when auto-grow is active |
| `max-rows` | number | — | yes | Maximum rows before scrolling begins |
| `auto-grow` | boolean | `false` | yes | Enables auto-height expansion |
| `no-resize` | boolean | `false` | yes | Disables the user resize handle |
| `maxlength` | number | — | yes | Maximum character count |
| `minlength` | number | — | yes | Minimum character count |
| `count-words` | boolean | `false` | yes | Shows word count in counter instead of character count |
| `required` | boolean | `false` | yes | Field is required |
| `disabled` | boolean | `false` | yes | Disables the field |
| `readonly` | boolean | `false` | yes | Makes the field read-only |
| `spellcheck` | boolean | `true` | yes | Forwarded to native textarea |
| `autocomplete` | string | `"on"` | yes | Forwarded to native textarea |
| `wrap` | `"soft"\|"hard"` | `"soft"` | yes | Forwarded to native textarea |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Font-size scale |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `wordCount` | number | Read-only; current word count computed from value |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `footer` | Optional content rendered below the textarea but above the help/error row (e.g., formatting tips) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string, charCount: number, wordCount: number }` | yes | no | Fires on every keystroke |
| `mj-change` | `{ value: string, charCount: number, wordCount: number }` | yes | no | Fires on blur when value has changed |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `wrapper`, `textarea`, `label`, `help`, `error`, `counter`, `resize-handle`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-textarea-bg` | `--mj-color-surface-input` | Textarea background |
| `--mj-textarea-border-color` | `--mj-color-border-default` | Border at rest |
| `--mj-textarea-border-color-focus` | `--mj-color-border-focus` | Border when focused |
| `--mj-textarea-border-color-error` | `--mj-color-border-error` | Border when invalid |
| `--mj-textarea-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-textarea-font-size` | `--mj-text-md` | Font size inside the field |
| `--mj-textarea-min-height` | derived from `min-rows` | Minimum height |
| `--mj-textarea-max-height` | derived from `max-rows` | Maximum height before scroll |
| `--mj-textarea-resize-color` | `--mj-color-border-subtle` | Resize handle color |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Neutral border; resize handle visible | — |
| Focus-visible | Focus ring | `aria-describedby` references help/error |
| Auto-grow active | Height grows with content; handle hidden | — |
| Near limit | Counter changes to warning color when ≥ 90% of `maxlength` | Live region announces "N characters remaining" |
| At limit | Further typing blocked; counter shows 0 remaining | `aria-invalid="true"` if `maxlength` exceeded |
| Invalid | Error border and message | `aria-invalid="true"` |
| Disabled | Reduced opacity; resize disabled | `aria-disabled="true"` |
| Readonly | No border highlight; resize disabled | `aria-readonly="true"` |

## 11. Behavior & interactions
- Auto-grow: on each `input` event the textarea height is recalculated by
  temporarily setting height to `"auto"` to read `scrollHeight`, then setting the
  height to the clamped value in `[min-rows × lineHeight, max-rows × lineHeight]`.
  This is batched in a `requestAnimationFrame` to avoid layout thrash.
- The character counter updates on every `input` event and is rendered in a
  `role="status"` live region (polite). When the count reaches 90% of `maxlength`,
  the polite announcement becomes assertive.
- Word count is computed by splitting on `/\S+/g` and counting matches.
- The user resize handle is a native CSS `resize` on the `<textarea>` constrained
  by `min-height` and `max-height` derived from `min-rows`/`max-rows`.
- Validation runs on blur; `reportValidity()` runs immediately.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Move focus into the field; Exit the field (native Tab behavior — does NOT insert a tab character) |
| `Shift+Tab` | Move focus backwards |
| `Enter` | Insert newline (native behavior) |
| `Ctrl+A` / `Cmd+A` | Select all text (native) |
| `Ctrl+Z` / `Cmd+Z` | Undo (native) |

## 13. Accessibility
- The native `<textarea>` receives `aria-label` from the `label` attribute or
  is linked to a visible `<label>` element by id.
- `aria-describedby` references help-text and error IDs when present.
- `aria-invalid="true"` on the native textarea when invalid.
- `aria-required="true"` mirrors the `required` attribute.
- The character/word counter uses `role="status"` for polite announcements;
  near-limit announcements use `aria-live="assertive"`.
- The resize handle is draggable but also keyboard accessible: when focused it
  accepts Arrow Up/Down to change height by one row increment.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Contributes `name`/`value` (multi-line text) to `FormData`.
- Supports `required` (valueMissing), `minlength` (tooShort), `maxlength`
  (tooLong) constraint validation with localizable messages.
- Form reset restores value to the `value` attribute (or `""`) and clears
  validation state; auto-grow height resets to `min-rows`.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `label`, `help-text`, `error-message`, `placeholder` are all overridable via
  the localization hook.
- Counter format string `"{current}/{max}"` is localizable; word count format
  `"{count} words"` is localizable.
- In RTL, the counter aligns to the inline-start end; the resize handle may need
  to be placed at the inline-start corner (bottom-left in RTL) via CSS.

## 16. Progressive enhancement / SSR
- Server renders `<textarea name rows>` with a visible `<label>`; the field is
  fully functional without script.
- On upgrade the component wraps the existing textarea without clearing its
  value; `auto-grow` height is applied after measuring the initial content.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Live-region service** (§6) — counter announcements.
- **Localization hook** (§6).

## 18. Edge cases & error handling
- `auto-grow` and explicit `rows` together: `rows` sets the initial height;
  auto-grow overrides it as the user types.
- `max-rows` without `auto-grow`: `max-rows` still caps the user-drag resize.
- `count-words` and `maxlength` together: the character counter is shown for
  `maxlength` enforcement; the word count is displayed separately below it.
- Pasting large content (>100 KB): the auto-grow calculation and word count are
  throttled to avoid janking the main thread.
- `wrap="hard"` with `maxlength`: the character count includes inserted newlines.
- `readonly` with `no-resize`: both take effect; no interaction affordance shown.

## 19. Acceptance criteria
- [ ] Default textarea renders with correct `rows`, label, help, and error regions.
- [ ] `auto-grow` expands height on input, clamped to `min-rows`/`max-rows`.
- [ ] Character counter updates on each keystroke and matches `maxlength` enforcement.
- [ ] Word counter updates on each keystroke when `count-words` is set.
- [ ] Near-limit counter changes to warning color and fires assertive live-region announcement.
- [ ] Resize handle is draggable and keyboard-operable with Arrow Up/Down.
- [ ] `aria-invalid`, `aria-required`, `aria-describedby` correct in all states.
- [ ] Form submit includes correct name/multi-line value.
- [ ] Form reset restores original value and auto-grow height.
- [ ] No layout shift on upgrade from server-rendered markup.
- [ ] axe audit passes with zero violations.

## 20. Open questions
- Should `count-words` coexist with `maxlength` (character limit) in a dual-counter display?
- Should `auto-grow` support a `max-height` CSS override in addition to `max-rows`?
- Should Tab inside the textarea insert a tab character when combined with a modifier key (e.g., Ctrl+Tab)?
