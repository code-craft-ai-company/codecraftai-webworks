# Markdown Editor Spec

- **Tag:** `<mj-markdown-editor>`
- **Class / file:** `MarkdownEditor` / `markdowneditor.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Markdown authoring field
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-markdown-editor>` is a text authoring component where the source format is
Markdown and the output value is raw Markdown text. It provides an accessible
toolbar that inserts Markdown syntax, an edit/preview split view that renders a
sanitized HTML preview, and a character/word counter. It is distinct from
`<mj-rich-text-editor>` because the internal representation and submitted value
are Markdown, not HTML.

## 2. When to use / when not to use
**Use** when the storage format is Markdown and authors are comfortable with
lightweight markup syntax (GitHub comments, documentation, README authoring).
**Do not use** when authors need WYSIWYG HTML output — prefer
`<mj-rich-text-editor>`. **Do not use** for code editing with syntax highlighting
— prefer `<mj-code-editor>`.

## 3. Anatomy
- **Header** (`part="header"`) — contains the toolbar and the edit/preview tab controls.
- **Mode tabs** (`part="mode-tabs"`) — Edit / Split / Preview tab strip.
- **Toolbar** (`part="toolbar"`) — `role="toolbar"` strip of Markdown syntax buttons; visible in Edit and Split modes.
- **Edit pane** (`part="edit-pane"`) — contains the `<textarea>` for Markdown source input.
- **Native textarea** (`part="textarea"`) — the underlying `<textarea>` receiving raw Markdown.
- **Preview pane** (`part="preview-pane"`) — sanitized HTML rendering of the Markdown source.
- **Divider** (`part="divider"`) — resizable gutter between panes in Split mode.
- **Status bar** (`part="status-bar"`) — word/character count.
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Mode | `view` value | Behavior |
|------|-------------|----------|
| Edit | `"edit"` | Only the textarea is visible |
| Split | `"split"` | Textarea and preview side by side |
| Preview | `"preview"` | Only the rendered HTML preview is visible |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for form submission |
| `value` | string | `""` | yes | Current Markdown content |
| `placeholder` | string | `""` | yes | Placeholder inside the textarea |
| `label` | string | `""` | yes | Visible label above the editor |
| `help-text` | string | `""` | yes | Hint text below the editor |
| `error-message` | string | `""` | yes | Override validation message |
| `view` | `"edit"\|"split"\|"preview"` | `"edit"` | yes | Active view mode |
| `required` | boolean | `false` | yes | Field is required |
| `disabled` | boolean | `false` | yes | Disables editing and toolbar |
| `readonly` | boolean | `false` | yes | Read-only; forces `view="preview"` |
| `maxlength` | number | — | yes | Maximum character count |
| `minlength` | number | — | yes | Minimum character count |
| `count-words` | boolean | `false` | yes | Shows word count in the status bar |
| `allowed-html-tags` | string | `""` | yes | Space-separated extra tags allowed in the HTML preview |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `previewHtml` | string | Read-only; the sanitized HTML string rendered in the preview pane |
| `wordCount` | number | Read-only; current word count of the Markdown source |
| `renderer` | `(markdown: string) => string` | Pluggable Markdown-to-HTML renderer; defaults to a built-in CommonMark renderer |
| `sanitizer` | `(html: string) => string` | Pluggable HTML sanitizer for preview output; defaults to built-in allowlist |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `toolbar-start` | Extra buttons prepended to the toolbar |
| `toolbar-end` | Extra buttons appended to the toolbar |
| `preview-empty` | Content shown in the preview pane when the Markdown value is empty |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string, wordCount: number }` | yes | no | Fires on every textarea keystroke (debounced 150 ms for preview update) |
| `mj-change` | `{ value: string, wordCount: number }` | yes | no | Fires on blur when value has changed |
| `mj-view-change` | `{ view: string }` | yes | no | Fires when the Edit/Split/Preview tab is changed |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `header`, `mode-tabs`, `toolbar`, `edit-pane`, `textarea`, `preview-pane`, `divider`, `status-bar`, `label`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-mde-bg` | `--mj-color-surface-input` | Edit pane background |
| `--mj-mde-preview-bg` | `--mj-color-surface-default` | Preview pane background |
| `--mj-mde-border-color` | `--mj-color-border-default` | Outer border |
| `--mj-mde-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-mde-toolbar-bg` | `--mj-color-surface-subtle` | Toolbar background |
| `--mj-mde-font-size` | `--mj-text-md` | Textarea font size |
| `--mj-mde-font-family` | `--mj-font-mono` | Textarea monospace font |
| `--mj-mde-preview-font-family` | `--mj-font-body` | Preview rendered font |
| `--mj-mde-min-height` | `300px` | Minimum total editor height |
| `--mj-mde-divider-color` | `--mj-color-border-subtle` | Split-mode divider color |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Edit mode | Textarea fills the content area; toolbar visible | `aria-selected="true"` on Edit tab |
| Split mode | Two equal panes; divider between them | `aria-selected="true"` on Split tab |
| Preview mode | Preview pane fills content area; toolbar hidden | `aria-selected="true"` on Preview tab |
| Readonly | `view="preview"` forced; tabs hidden | `aria-readonly="true"` on textarea |
| Disabled | All controls greyed; tabs and toolbar disabled | `aria-disabled="true"` |
| Invalid | Error border; message shown | `aria-invalid="true"` on textarea |

## 11. Behavior & interactions
- The Edit/Split/Preview tabs are rendered as a `role="tablist"` with three `role="tab"` buttons. Changing the tab updates `view`.
- The toolbar inserts Markdown syntax at the current caret position using `textarea.setRangeText()`. Selected text is wrapped (e.g., `**selected**` for bold).
- The preview pane is updated after a 200 ms debounce on each textarea `input` event, using `renderer()` to convert Markdown to HTML, then `sanitizer()`.
- In Split mode the divider is keyboard-resizable (Arrow Left/Right).
- `readonly` forces `view="preview"` and hides tabs; `disabled` disables all interaction including tab changes.
- `maxlength` is enforced on the Markdown character count (not rendered HTML length).

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` (from textarea) | Move focus to the mode tabs; then toolbar; then out |
| Arrow Left / Right (on mode tabs) | Switch between Edit / Split / Preview tabs |
| Arrow keys (in toolbar) | Roving tabindex within toolbar groups |
| `Enter` / `Space` (on toolbar button) | Insert corresponding Markdown syntax |
| `Ctrl/Cmd+B` | Wrap selection in `**bold**` |
| `Ctrl/Cmd+I` | Wrap selection in `_italic_` |
| `Ctrl/Cmd+K` | Insert `[text](url)` link template |
| `Ctrl/Cmd+Shift+P` | Toggle between Edit and Preview mode |
| Arrow Left / Right (on divider, Split mode) | Resize panes by 10% |

## 13. Accessibility
- The native `<textarea>` carries `role="textbox"`, `aria-multiline="true"`,
  `aria-label` from `label`, and `aria-describedby` pointing to help and error.
- Mode tabs use `role="tablist"` / `role="tab"` / `role="tabpanel"` pattern.
- Toolbar uses `role="toolbar"` with `aria-label="Markdown formatting"` (localizable).
- All toolbar buttons have `aria-label` for each format action (localizable).
- Preview pane has `role="region"` with `aria-label="Preview"` (localizable) and
  `aria-live="polite"` so updates are announced.
- The split-mode divider has `role="separator"` with `aria-valuenow` expressing
  the split ratio.
- `aria-invalid` and `aria-required` are set on the textarea as appropriate.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Submits raw Markdown text as the `name`/`value` pair — never the rendered HTML.
- Supports `required` (valueMissing), `minlength` (tooShort), `maxlength` (tooLong)
  with localizable messages.
- Form reset restores Markdown value to the `value` attribute (or `""`) and
  reverts `view` to its initial attribute value.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- All toolbar button labels, mode-tab labels, placeholder, and validation messages
  are localizable via the shared localization hook.
- In RTL the toolbar button order may be reversed; the Split mode divider starts
  at 50% regardless of direction.
- The preview pane inherits `dir` from the document for correct rendered content
  direction.

## 16. Progressive enhancement / SSR
- Server renders the Markdown content inside a `<textarea>` so the raw text is
  accessible and submittable without script.
- On upgrade, the component reads the textarea's value as the initial `value`.
- Without script the preview rendering is unavailable; the raw Markdown textarea
  remains functional.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Focus utilities** (§6) — roving tabindex in toolbar and tab list.
- **Live-region service** (§6) — preview update announcements.
- **Localization hook** (§6).
- **Pluggable CommonMark renderer** — external; injected via `renderer` property.

## 18. Edge cases & error handling
- `renderer` property not set: uses the built-in minimal CommonMark renderer (headings, paragraphs, bold, italic, links, lists, code blocks).
- Very large Markdown (>100 KB): renderer runs in a Web Worker if available; a loading indicator is shown in the preview.
- `allowed-html-tags` with disallowed tags (e.g., `<script>`): silently ignored; the sanitizer's security allowlist always takes precedence.
- `view` attribute changed at runtime while in Split mode: divider state is preserved.
- Pasting rich HTML into the textarea: only plain text is accepted by the textarea; HTML is stripped by the browser-native paste handler.

## 19. Acceptance criteria
- [ ] Edit / Split / Preview modes switch correctly via tabs and keyboard shortcuts.
- [ ] Toolbar buttons insert correct Markdown syntax at caret; wrap selected text.
- [ ] Preview pane renders debounced updates of the Markdown value.
- [ ] `renderer` and `sanitizer` can be replaced programmatically.
- [ ] `mj-input` debounced; `mj-change` fires on blur; `mj-view-change` on tab change.
- [ ] `required`, `minlength`, `maxlength` constraints validated correctly.
- [ ] Form submits raw Markdown; form reset restores initial Markdown value.
- [ ] Toolbar roving tabindex and mode-tab arrow navigation work correctly.
- [ ] Preview pane announces updates via `aria-live="polite"`.
- [ ] Split divider resizable by drag and by keyboard arrows.
- [ ] axe audit passes in all three view modes.

## 20. Open questions
- Should the built-in renderer support GitHub Flavored Markdown extensions (tables, task lists, strikethrough)?
- Should a `mention-trigger` attribute enable `@`-mention tokens in the textarea?
- Should Split mode support vertical (top/bottom) split in addition to horizontal?
