# Mention Input Spec

- **Tag:** `<mj-mention-input>`
- **Class / file:** `MentionInput` / `mentioninput.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** At-mention input, Tag input with mention triggers
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-mention-input>` is a rich text entry field that detects trigger characters (`@` for user mentions, `#` for topics or tags) and opens a `<mj-combobox>`-style suggestion popup for completion. Resolved mentions are rendered as styled, removable inline tokens within the text. The component emits both the raw text value and a structured array of resolved mention tokens, making it easy to parse and store mention metadata.

## 2. When to use / when not to use
Use wherever users need to mention other users or reference entities within free text (comments, chat, task descriptions, emails). Do not use for free-form hashtag entry without structured resolution — use `<mj-token-input>`. Do not use as a full rich-text editor; the only formatting it applies is mention tokens.

## 3. Anatomy
- **editable region** — a `contenteditable="true"` `<div>` with `role="textbox" aria-multiline="true"`.
- **placeholder** — CSS `::before` pseudo-element shown when the editable region is empty.
- **mention token** — `<span role="img" aria-label="@{displayName}">` inside the editable region; not editable; deletable with Backspace.
- **suggestion popup** — `<mj-combobox>` popup anchored below the trigger character position; opens on trigger detection.
- **suggestion items** — avatar + display name + optional subtitle per suggestion.
- **label** — visually associated `<label>` element (external or via `label` attribute).
- **character counter** — optional counter below the field showing remaining characters.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Single-line | `multiline="false"` | `Enter` submits instead of inserting a newline |
| Multi-line | `multiline="true"` (default) | `Shift+Enter` inserts newline; `Enter` fires `mj-submit` |
| Read-only | `readonly` | Tokens visible but not editable; no trigger detection |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `placeholder` | string | `""` | Yes | Placeholder text when empty |
| `multiline` | boolean | `true` | Yes | Allow newlines in the editable region |
| `max-length` | number | `0` | Yes | Maximum character count (0 = unlimited) |
| `triggers` | string | `"@#"` | Yes | Characters that open the suggestion popup |
| `min-trigger-length` | number | `1` | Yes | Minimum characters typed after trigger before suggestions appear |
| `disabled` | boolean | `false` | Yes | Disables the input |
| `readonly` | boolean | `false` | Yes | Makes the content non-editable |
| `required` | boolean | `false` | Yes | Marks the field as required for form validation |
| `name` | string | `""` | Yes | Form field name |
| `label` | string | `""` | Yes | Visible label text rendered above the field |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `value` | string | The raw text content (mention tokens represented as `@displayName` in plain text) |
| `mentions` | `MentionToken[]` | Array of resolved tokens: `{ trigger, id, displayName, type }` |
| `mentionSource` | `MentionDataSource` | Provides `suggest(trigger, query): Promise<Suggestion[]>` |
| `selectionRange` | `{ start: number, end: number }` | Current selection offsets in the plain-text value |

## 7. Slots
| Slot | Description |
|------|-------------|
| `suggestion-item` | Custom template for a suggestion list row; receives `suggestion` via context |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string, mentions: MentionToken[] }` | Yes | No | Fires on every keystroke or token change |
| `mj-change` | `{ value: string, mentions: MentionToken[] }` | Yes | No | Fires when focus leaves and value has changed |
| `mj-submit` | `{ value: string, mentions: MentionToken[] }` | Yes | Yes | Fires on Enter (single-line) or Shift+Enter in multi-line |
| `mj-mention-trigger` | `{ trigger: string, query: string }` | Yes | No | Fires when a trigger character is detected |
| `mj-mention-select` | `{ trigger: string, suggestion: Suggestion }` | Yes | No | Fires when a suggestion is chosen |
| `mj-mention-cancel` | `{ trigger: string }` | Yes | No | Fires when the suggestion popup is dismissed without selection |

## 9. CSS parts & custom properties
**Parts:** `root`, `label`, `editable`, `token`, `token-remove`, `suggestion-popup`, `suggestion-item`, `counter`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-mention-min-height` | `var(--mj-size-control-md)` | Minimum height of the editable region |
| `--mj-mention-max-height` | `200px` | Maximum height before scrolling (multi-line) |
| `--mj-mention-token-bg` | `var(--mj-color-accent-subtle)` | Background of a resolved mention token |
| `--mj-mention-token-color` | `var(--mj-color-accent)` | Text color of a resolved mention token |
| `--mj-mention-token-radius` | `var(--mj-radius-sm)` | Border radius of mention tokens |
| `--mj-mention-border` | `var(--mj-border-control)` | Border of the editable region |
| `--mj-mention-focus-ring` | `var(--mj-focus-ring)` | Focus ring on the editable region |

## 10. States
- **default** — editable; no trigger active.
- **focused** — editable region has focus; focus ring visible.
- **trigger-active** — suggestion popup open; suggestions loading or displayed.
- **disabled** — `aria-disabled="true"`; no editing; dimmed.
- **readonly** — `aria-readonly="true"`; tokens visible; no editing.
- **invalid** — `aria-invalid="true"`; red border; error message via `aria-describedby`.
- **max-length-reached** — character counter turns red; additional input blocked.

## 11. Behavior & interactions
On every keystroke, the component scans backward from the cursor position to detect a trigger character not preceded by whitespace or another token. If found and the query length meets `min-trigger-length`, `mentionSource.suggest(trigger, query)` is called (debounced 200 ms). Results populate the suggestion popup below the trigger character's position, anchored by the overlay engine. Keyboard navigation in the popup is managed by the overlay combobox; selecting a suggestion inserts a token span and removes the trigger+query text. Pressing Esc or navigating away without selecting closes the popup and fires `mj-mention-cancel`. Clicking a token removes it (same as Backspace when cursor is immediately after). Pasting plain text is accepted; pasting HTML is sanitized to plain text only.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| Typing `@` or `#` | Detects trigger; opens suggestion popup after `min-trigger-length` chars |
| `ArrowDown` (trigger active) | Moves focus into the suggestion popup |
| `ArrowUp` / `ArrowDown` in popup | Navigate suggestions (roving tabindex in popup) |
| `Enter` in popup | Selects highlighted suggestion; inserts token |
| `Escape` | Closes suggestion popup; returns focus to editable |
| `Backspace` after token | Removes the immediately preceding token |
| `Enter` (single-line mode) | Fires `mj-submit` |
| `Shift+Enter` (multi-line mode) | Inserts a newline; does not submit |
| `Enter` (multi-line mode) | Fires `mj-submit` |
| `Tab` | Moves focus out of the field; closes popup |

## 13. Accessibility
The editable region has `role="textbox"`, `aria-multiline`, `aria-placeholder`, `aria-required`, `aria-invalid`, `aria-disabled`, `aria-readonly`, and `aria-describedby` for error messages. The suggestion popup has `role="listbox"` (or delegates to `<mj-combobox>` internals) with `aria-label="Suggestions"`. When the popup opens, a polite live region announces "Suggestions available. Use arrow key to navigate." Each token has `role="img"` with `aria-label` of the form "@Alice" or "#react". The character counter has `aria-live="polite"` and updates as the user types. When the maximum length is reached, a polite announcement is made.

## 14. Form participation
Form-associated via `ElementInternals`. The plain-text `value` (with mention tokens as `@displayName`) is submitted under `name`. Constraint validation: `required` with empty value reports "Please fill in this field." `max-length` exceeded reports "The value must be N characters or fewer."

## 15. Internationalization & RTL
`placeholder` is localizable. Suggestion popup directions, trigger detection, and token insertion all work in RTL. The `dir` attribute on the editable region matches the document direction. Suggestion avatars and text are LTR regardless of document direction.

## 16. Progressive enhancement / SSR
Server renders a plain `<textarea>` with the `value` pre-filled. Without JS the user can edit text but no mention detection or token rendering occurs. On upgrade the component replaces the `<textarea>` with the `contenteditable` region, parses existing mention syntax from the value, and renders tokens for recognized mention IDs.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Overlay/positioning engine, Focus utilities, Form-association helper, Live-region/announcement service, Localization/formatting hook.
- **Components:** `<mj-combobox>` (suggestion popup pattern), `<mj-avatar>` (suggestion item display).

## 18. Edge cases & error handling
- Trigger immediately followed by a space: not treated as a mention trigger; popup does not open.
- `mentionSource` not set: trigger characters are typed literally; no popup.
- Suggestion fetch returns zero results: popup shows "No matches" message; does not close automatically.
- Token deleted by external `value` property set: tokens are re-parsed from the new value; orphaned DOM nodes removed.
- Content pasted with existing `@token` syntax: parsed and rendered as tokens if IDs are resolvable.
- Very fast typing after trigger: debounce suppresses intermediate fetches; only the last query fetches.

## 19. Acceptance criteria
- [ ] `@` and `#` (and other configured triggers) open the suggestion popup after `min-trigger-length` chars.
- [ ] Arrow key moves into popup; Enter selects; inserts token; fires `mj-mention-select`.
- [ ] Escape closes popup without selecting; fires `mj-mention-cancel`; focus returns to editable.
- [ ] Backspace immediately after a token removes the token and fires `mj-input`.
- [ ] `value` property returns plain text; `mentions` returns structured token array.
- [ ] Form-associated: value in `FormData` under `name`.
- [ ] `required` validation fails on empty; `max-length` validation enforced.
- [ ] Axe scan reports zero violations.
- [ ] RTL: token and popup render correctly.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should the component support custom trigger characters beyond `@` and `#` with separate data sources per trigger?
- Should mention tokens support hover cards (`<mj-popover>`) showing user details?
