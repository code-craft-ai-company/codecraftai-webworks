# Code Editor Spec

- **Tag:** `<mj-code-editor>`
- **Class / file:** `CodeEditor` / `codeeditor.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Code input, Syntax-highlighted editor
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-code-editor>` provides syntax-highlighted code authoring within the design
system. It wraps a pluggable syntax highlighting engine (injected via a property)
over a plain `<textarea>` fallback, adds line numbers, proper Tab key handling
that does not trap keyboard focus, and produces plain text as its form value.
It is intentionally lighter-weight than a full IDE widget — it targets config
files, scripts, queries, and template snippets.

## 2. When to use / when not to use
**Use** for user-authored code, configuration snippets, SQL queries, JSON input,
or any structured text where syntax highlighting aids readability. **Do not use**
for general plain text — prefer `<mj-textarea>`. **Do not use** for Markdown —
prefer `<mj-markdown-editor>`. **Do not use** as an embedded full IDE (no
in-component language server, no file-tree).

## 3. Anatomy
- **Container** (`part="container"`) — positions gutter and editor side by side.
- **Gutter** (`part="gutter"`) — line-number column (decorative; `aria-hidden`).
- **Native textarea** (`part="textarea"`) — the real `<textarea>` carrying the raw source; positioned over the highlight layer.
- **Highlight layer** (`part="highlight-layer"`) — `<pre><code>` block rendered by the syntax engine; `aria-hidden="true"`.
- **Cursor line highlight** (`part="cursor-line"`) — optional background stripe on the active line.
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Read-only | `readonly` | No textarea; highlight layer only; for display |
| Line numbers visible | `line-numbers` (default `true`) | Gutter shown |
| No line numbers | `line-numbers="false"` | Gutter hidden |
| Word wrap | `word-wrap` | Lines wrap; gutter adapts |
| Specific language | `language="python"` | Syntax engine tokenizes for that language |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for form submission |
| `value` | string | `""` | yes | Current source text |
| `language` | string | `"plaintext"` | yes | Language identifier passed to the syntax engine |
| `label` | string | `""` | yes | Visible label above the editor |
| `help-text` | string | `""` | yes | Hint text below the editor |
| `error-message` | string | `""` | yes | Override validation message |
| `placeholder` | string | `""` | yes | Placeholder shown when empty |
| `line-numbers` | boolean | `true` | yes | Show/hide the gutter |
| `word-wrap` | boolean | `false` | yes | Enable line wrapping |
| `tab-size` | number | `4` | yes | Visual tab width (CSS `tab-size`) and inserted spaces per Tab |
| `tab-inserts-spaces` | boolean | `true` | yes | Tab key inserts spaces; false inserts `\t` |
| `required` | boolean | `false` | yes | Field is required |
| `disabled` | boolean | `false` | yes | Disables the editor |
| `readonly` | boolean | `false` | yes | Read-only display mode |
| `maxlength` | number | — | yes | Maximum character count |
| `minlength` | number | — | yes | Minimum character count |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Font-size scale |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `highlighter` | `(code: string, language: string) => string` | Pluggable syntax engine; returns HTML token markup; defaults to identity (no highlighting) |
| `wordCount` | number | Read-only; line count of current value |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `toolbar` | Optional toolbar placed above the editor (e.g., language selector, copy button) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string, lineCount: number }` | yes | no | Fires on every keystroke (debounced 100 ms for highlight update) |
| `mj-change` | `{ value: string, lineCount: number }` | yes | no | Fires on blur when value has changed |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `container`, `gutter`, `textarea`, `highlight-layer`, `cursor-line`, `label`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-code-bg` | `--mj-color-surface-code` | Editor background |
| `--mj-code-border-color` | `--mj-color-border-default` | Border |
| `--mj-code-border-color-focus` | `--mj-color-border-focus` | Focus border |
| `--mj-code-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-code-font-family` | `--mj-font-mono` | Monospace font |
| `--mj-code-font-size` | `--mj-text-sm` | Code font size |
| `--mj-code-line-height` | `1.6` | Line height |
| `--mj-code-gutter-bg` | `--mj-color-surface-subtle` | Gutter background |
| `--mj-code-gutter-color` | `--mj-color-text-subtle` | Line number color |
| `--mj-code-cursor-line-bg` | `--mj-color-surface-hover` | Cursor line highlight |
| `--mj-code-min-height` | `200px` | Minimum editor height |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Highlight layer visible behind transparent textarea | `aria-multiline="true"` on textarea |
| Focus-visible | Focus ring on editor; cursor line highlighted | `aria-describedby` active |
| Readonly | Textarea hidden; highlight layer is the visible element | `aria-readonly="true"` |
| Disabled | All greyed; textarea pointer-events none | `aria-disabled="true"` |
| Invalid | Error border and message | `aria-invalid="true"` |

## 11. Behavior & interactions
- The textarea is transparent with a matching font/size/padding stack over the highlight `<pre>`. Scroll is synchronized between them using a shared scroll handler.
- On `input`, `value` is updated; after 100 ms debounce the `highlighter()` is called and the result is written to the highlight layer's innerHTML.
- Tab key behavior: when `tab-inserts-spaces` is `true`, pressing Tab inserts `tab-size` space characters at the caret via `setRangeText()`. When `false`, it inserts a `\t` character. Shift+Tab removes one level of indentation. Tab never moves focus out of the editor; to exit via keyboard the user presses Escape then Tab (the Escape key arms a "next Tab will exit" mode announced to screen readers).
- With a multi-line selection, Tab and Shift+Tab indent/unindent all selected lines.
- `readonly` hides the textarea and sets the highlight layer as the sole visible content; it is not focusable and does not participate in the tab order.
- Line numbers in the gutter are re-rendered on each `input` event.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Insert `tab-size` spaces (or `\t`); never moves focus |
| `Shift+Tab` | Remove one level of indentation from caret or selection |
| `Escape` | Arms "exit" mode; next Tab moves focus out of editor; announced to screen readers |
| `Tab` (after Escape) | Move focus to the next element in the page |
| `Ctrl/Cmd+A` | Select all code |
| `Ctrl/Cmd+Z` | Undo |
| `Ctrl/Cmd+Shift+Z` / `Ctrl/Cmd+Y` | Redo |
| `Ctrl/Cmd+/` | Toggle line comment (if language supports `//` or `#` comment prefix) |
| `Home` | Move caret to start of line (smart: before indent, then column 0) |
| `End` | Move caret to end of line |

## 13. Accessibility
- The native `<textarea>` carries `role="textbox"`, `aria-multiline="true"`,
  `aria-label` from the `label` attribute (or linked `<label>`), and
  `aria-describedby` referencing help and error IDs.
- The highlight layer and gutter are `aria-hidden="true"` — they are purely
  visual decoration.
- When "exit" mode is armed after Escape, a polite live-region announcement reads
  "Press Tab to move focus out of the code editor."
- `aria-invalid` and `aria-required` are set on the textarea as appropriate.
- Minimum contrast is maintained between syntax token colors and the editor
  background (WCAG AA 4.5:1 for normal text).

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Submits plain text (raw source code) as the `name`/`value` pair — never
  the highlighted HTML.
- Supports `required` (valueMissing), `minlength` (tooShort), `maxlength` (tooLong)
  with localizable messages.
- Form reset restores the `value` attribute content (or `""`) and re-renders
  the highlight layer; line count updates.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `label`, `help-text`, `error-message`, `placeholder`, and the Escape/Tab
  announcement are localizable via the shared localization hook.
- RTL support: the gutter moves to the right side; `dir="rtl"` is forwarded
  to the textarea. Note: most code is written left-to-right regardless of document
  direction; `dir="ltr"` is applied to the code container by default and overridable.

## 16. Progressive enhancement / SSR
- Server renders the code inside a `<textarea>` (and optionally a `<pre><code>`
  for the read-only case) so the raw source is visible and submittable without script.
- On upgrade, the component reads the textarea's value, applies the highlight
  engine, and renders the gutter.
- Without the `highlighter` property set, the component is functional as a plain
  monospace textarea with line numbers.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Live-region service** (§6) — Escape/Tab announcement.
- **Localization hook** (§6).
- **Pluggable syntax highlighter** — external library (e.g., Prism, highlight.js,
  Shiki); injected via the `highlighter` property; none bundled in-house.

## 18. Edge cases & error handling
- `highlighter` not set: component renders as a monospace plain-text textarea with line numbers; no highlighting.
- `highlighter` throws an exception: caught; the highlight layer is cleared and the textarea remains usable; error is logged to the console.
- Very large files (>5000 lines): the highlight update is debounced at 500 ms and the gutter is virtualized (only visible lines rendered).
- `word-wrap` enabled with line numbers: gutter shows the original line number for each source line, not each visual wrap line.
- `tab-inserts-spaces=false` and `tab-size`: the gutter CSS `tab-size` still uses `tab-size` for visual width of `\t` characters.
- Pasting mixed line endings (CRLF/LF): normalized to LF on input.

## 19. Acceptance criteria
- [ ] Tab inserts spaces (or `\t`) at caret; does not move focus.
- [ ] Escape arms exit mode; next Tab moves focus out; live region announcement fires.
- [ ] Shift+Tab removes one indentation level; works with multi-line selection.
- [ ] Line numbers update on each change and match the source line count.
- [ ] Scroll of textarea and highlight layer stays synchronized.
- [ ] `highlighter` function is called debounced; result appears in the highlight layer.
- [ ] `highlighter` errors are caught; textarea remains usable.
- [ ] `readonly` mode hides textarea; highlight layer displays the code.
- [ ] Form submit sends plain text value; form reset restores initial value.
- [ ] `aria-multiline`, `aria-label`, `aria-describedby`, `aria-invalid` correct.
- [ ] axe audit passes; highlight layer is aria-hidden.

## 20. Open questions
- Should `<mj-code-editor>` expose a line/column indicator in the status bar?
- Should find-and-replace (Ctrl+H) be in scope for this component?
- Should the `language` attribute accept an arbitrary string (passed to the highlighter) or be constrained to a known enum?
