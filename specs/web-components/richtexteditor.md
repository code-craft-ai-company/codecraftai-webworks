# Rich Text Editor Spec

- **Tag:** `<mj-rich-text-editor>`
- **Class / file:** `RichTextEditor` / `richtexteditor.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** WYSIWYG editor, Formatted text editor
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-rich-text-editor>` provides formatted-text authoring with an accessible
toolbar and produces sanitized semantic HTML as its output value. It is intended
for content that requires emphasis, headings, links, and lists without exposing
raw HTML to authors. The component wraps a `contenteditable` region — not an
`<iframe>` — and delegates sanitization on every change.

## 2. When to use / when not to use
**Use** when authors need inline formatting (bold, italic, lists, links, headings)
and the output will be rendered as HTML. **Do not use** when authors write markdown
— prefer `<mj-markdown-editor>`. **Do not use** when raw HTML editing is
needed — that is an advanced scenario outside this component's scope. **Do not
use** for plain text — prefer `<mj-textarea>`.

## 3. Anatomy
- **Toolbar** (`part="toolbar"`) — horizontal `role="toolbar"` strip of format buttons.
- **Toolbar group** (`part="toolbar-group"`) — logical `role="group"` cluster within the toolbar.
- **Toolbar button** (`part="toolbar-button"`) — individual format action `<button>` with `aria-pressed`.
- **Editing region** (`part="editor"`) — the `contenteditable="true"` `<div>` with `role="textbox" aria-multiline="true"`.
- **Placeholder** (`part="placeholder"`) — absolutely positioned hint shown when editor is empty.
- **Status bar** (`part="status-bar"`) — optional word/character count below the editor.
- **Error message** (`part="error"`).
- **Label** (`part="label"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Full toolbar | — | All format groups shown |
| Minimal toolbar | `toolbar="minimal"` | Bold, italic, link, lists only |
| Custom toolbar | `toolbar="custom"` + `toolbar-config` property | Host specifies which groups and buttons appear |
| Read-only | `readonly` | `contenteditable="false"`; toolbar hidden |
| Focused (inline) | `inline` | No visible border at rest; border appears on focus |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for form submission |
| `value` | string | `""` | yes | Current HTML value (sanitized) |
| `placeholder` | string | `""` | yes | Placeholder shown when editor is empty |
| `label` | string | `""` | yes | Visible label above the editor |
| `help-text` | string | `""` | yes | Hint text below the editor |
| `error-message` | string | `""` | yes | Override validation message |
| `toolbar` | `"full"\|"minimal"\|"custom"` | `"full"` | yes | Toolbar configuration preset |
| `inline` | boolean | `false` | yes | Inline (borderless at rest) mode |
| `required` | boolean | `false` | yes | Field is required (non-empty HTML) |
| `disabled` | boolean | `false` | yes | Disables editing and toolbar |
| `readonly` | boolean | `false` | yes | Read-only display |
| `max-length` | number | — | yes | Maximum plain-text character count |
| `allowed-tags` | string | `""` | yes | Space-separated list of allowed HTML tags; overrides default allowlist |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `htmlValue` | string | The sanitized HTML content (same as `value`; explicit alias) |
| `textContent` | string | Plain-text extraction of the current content (read-only) |
| `toolbarConfig` | `Array<ToolbarGroup>` | Object model for `toolbar="custom"` configuration |
| `sanitizer` | `(html: string) => string` | Pluggable sanitizer function; defaults to built-in allowlist |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `toolbar-start` | Extra buttons prepended to the toolbar |
| `toolbar-end` | Extra buttons appended to the toolbar |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ html: string, text: string }` | yes | no | Fires on every content change (debounced 150 ms) |
| `mj-change` | `{ html: string, text: string }` | yes | no | Fires on blur when content has changed |
| `mj-format` | `{ command: string, value?: string, active: boolean }` | yes | no | Fires when a toolbar format is applied or toggled |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `toolbar`, `toolbar-group`, `toolbar-button`, `editor`, `placeholder`, `status-bar`, `label`, `error`, `help`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-rte-bg` | `--mj-color-surface-input` | Editor region background |
| `--mj-rte-border-color` | `--mj-color-border-default` | Border at rest |
| `--mj-rte-border-color-focus` | `--mj-color-border-focus` | Border when focused |
| `--mj-rte-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-rte-toolbar-bg` | `--mj-color-surface-subtle` | Toolbar background |
| `--mj-rte-toolbar-button-bg-active` | `--mj-color-surface-pressed` | Active format button background |
| `--mj-rte-min-height` | `200px` | Minimum editor height |
| `--mj-rte-font-size` | `--mj-text-md` | Editor content font size |
| `--mj-rte-font-family` | `--mj-font-body` | Editor content font family |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Neutral border; placeholder visible if empty | `aria-multiline="true"` on editor |
| Focus-visible | Focus ring on editor or toolbar button | `aria-describedby` references help/error |
| Format active | Toolbar button shows `aria-pressed="true"` | Screen reader announces toggle state |
| Invalid | Error border; message shown | `aria-invalid="true"` on editor |
| Disabled | Toolbar and editor greyed; `contenteditable="false"` | `aria-disabled="true"` |
| Readonly | `contenteditable="false"`; toolbar hidden | `aria-readonly="true"` |

## 11. Behavior & interactions
- The editing region uses `contenteditable="true"`. Format commands (bold, italic, etc.) are executed via `document.execCommand` where available, falling back to `Selection`/`Range` APIs for environments where `execCommand` is deprecated.
- After each change, the HTML is sanitized through `sanitizer()` and the result is stored as `value` in `ElementInternals`. The default sanitizer permits a fixed allowlist: `b`, `i`, `u`, `s`, `em`, `strong`, `a`, `ul`, `ol`, `li`, `h1`–`h4`, `blockquote`, `pre`, `code`, `br`, `p`.
- Paste events are intercepted; plain text and rich-paste HTML are both sanitized before insertion.
- The toolbar uses a roving tabindex within each group (`role="group"`); Tab moves between groups.
- Keyboard shortcuts (Ctrl/Cmd+B, +I, +U, +K for link) apply formats without using the toolbar.
- The placeholder is a non-focusable overlay hidden when `textContent.length > 0`.
- `max-length` is enforced on input by comparing `textContent.length`; excess input is prevented with a warning announcement.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` (from editor) | Move focus to toolbar; then out of component |
| `Shift+Tab` (from toolbar) | Return focus to editor |
| Arrow keys (in toolbar) | Navigate between toolbar buttons (roving tabindex within group) |
| `Enter` / `Space` (on toolbar button) | Apply format |
| `Ctrl/Cmd+B` | Toggle bold |
| `Ctrl/Cmd+I` | Toggle italic |
| `Ctrl/Cmd+U` | Toggle underline |
| `Ctrl/Cmd+K` | Open link dialog |
| `Ctrl/Cmd+Z` | Undo |
| `Ctrl/Cmd+Shift+Z` / `Ctrl/Cmd+Y` | Redo |
| `Escape` (link dialog) | Cancel link entry |

## 13. Accessibility
- The `contenteditable` region has `role="textbox"`, `aria-multiline="true"`,
  `aria-label` from `label`, and `aria-describedby` pointing to help and error.
- `aria-invalid="true"` is set on the editing region when invalid.
- Each toolbar button uses `aria-pressed` to reflect active format state.
- The toolbar has `role="toolbar"` with `aria-label="Formatting"` (localizable).
- Toolbar groups have `role="group"` with descriptive `aria-label`.
- All toolbar buttons have `aria-label` for each action (localizable).
- Link dialog is a modal with `role="dialog"`, focus trapped while open.
- Screen reader users can navigate the produced HTML as rich content.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Submits sanitized HTML as the `name`/`value` pair in `FormData`.
- `required` validation: `valueMissing` when `textContent.trim().length === 0`.
- `max-length` validation: `tooLong` when `textContent.length > max-length`.
- Custom validity messages are localizable.
- Form reset restores `value` to the `value` attribute content (or `""`) and
  re-renders the editing region; validation state is cleared.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- All toolbar button labels, link-dialog labels, placeholder, and validation
  messages are localizable via the shared localization hook.
- `dir` attribute on the editing region inherits from the document; the component
  respects `dir="rtl"` for right-to-left text entry.
- Toolbar button order may be reversed in RTL mode via CSS.

## 16. Progressive enhancement / SSR
- Server renders the sanitized HTML inside the component; without script it is
  displayed as read-only formatted content.
- On upgrade, the component reads the slot/light-DOM HTML content as the initial
  `value` and populates the editing region.
- If scripting is unavailable, a fallback `<textarea>` inside `<noscript>` allows
  plain-text submission.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Focus utilities** (§6) — roving tabindex in the toolbar.
- **Overlay/positioning engine** (§6) — link-dialog anchoring.
- **Live-region service** (§6) — max-length warnings and format announcements.
- **Localization hook** (§6).

## 18. Edge cases & error handling
- Pasting very large HTML (>500 KB): sanitization is run off the main thread if
  Workers are available; a loading spinner is shown in the editor during processing.
- `allowed-tags` set to an empty string: falls back to the default allowlist with
  a console warning.
- `execCommand` fully unavailable: the component degrades to plain-text entry with
  the toolbar hidden; a console warning is emitted.
- `value` set programmatically with unsanitized HTML: the setter always runs
  `sanitizer()` before applying.
- Undo/redo history is scoped to the editing region session and cleared on form reset.

## 19. Acceptance criteria
- [ ] Bold, italic, underline, strikethrough, link, heading, blockquote, code, ordered list, unordered list toolbar buttons apply correct formatting.
- [ ] `aria-pressed` state on toolbar buttons reflects active format at cursor.
- [ ] Toolbar roving tabindex navigates correctly with arrow keys.
- [ ] Paste of external HTML is sanitized; disallowed tags are stripped.
- [ ] `value` property always returns sanitized HTML.
- [ ] `mj-input` fires debounced; `mj-change` fires on blur with change.
- [ ] `required` validation fires when `textContent` is empty.
- [ ] Form submit includes sanitized HTML; form reset restores initial value.
- [ ] Link dialog is keyboard-operable and closes on Escape.
- [ ] All keyboard shortcuts (B, I, U, K, Z) work without the toolbar.
- [ ] axe audit passes in default and disabled states.

## 20. Open questions
- Should the component integrate an external sanitizer library (DOMPurify) or remain on the built-in allowlist?
- Should undo/redo history persist across blur/focus cycles or reset on blur?
- Should a `toolbar-config` JSON attribute be supported for purely declarative custom toolbar setup?
