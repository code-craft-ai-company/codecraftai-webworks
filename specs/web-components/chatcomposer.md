# Chat Composer Spec

- **Tag:** `<mj-chat-composer>`
- **Class / file:** `ChatComposer` / `chatcomposer.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Message composer, Chat input, Message input bar
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-chat-composer>` is the message-entry component for chat interfaces. It composes a `<mj-mention-input>` for text entry with `@`/`#` mention support, an attachment picker button linked to `<mj-file-picker>`, a row of attachment previews for queued files, an emoji trigger, and a send button. It manages the send-on-Enter vs. newline-on-Shift+Enter convention and exposes a loading state during message delivery.

## 2. When to use / when not to use
Use as the primary input in a chat or messaging interface. Do not use in place of a comment form — use `<mj-comments>` + `<mj-mention-input>`. Do not use for a simple text field — use `<mj-text-field>` or `<mj-textarea>`.

## 3. Anatomy
- **composer root** — `<div role="form" aria-label="Message composer">`.
- **reply preview** — collapsible strip showing the message being replied to, with a cancel button.
- **mention input** — `<mj-mention-input multiline="true">` as the main text entry.
- **attachment bar** — horizontal list of queued attachment thumbnails or file chips, each with a remove button.
- **toolbar row** — below or beside the input; contains: attach button, emoji button, and a send button.
- **attach button** — `<mj-button>` that triggers a hidden `<input type="file">`.
- **emoji button** — `<mj-button>` that opens an `<mj-emoji-picker>` popover.
- **send button** — `<mj-button variant="primary">` that submits the message.
- **character counter** — optional `<span aria-live="polite">` when `max-length` is set.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default | (none) | Mention input + attach + emoji + send |
| Compact | `compact` | Single-line appearance; toolbar icons tighter |
| No attachments | `allow-attachments="false"` | Attach button hidden |
| No emoji | `allow-emoji="false"` | Emoji button hidden |
| Send on Enter | `send-key="enter"` (default) | Enter sends; Shift+Enter inserts newline |
| Send on Ctrl+Enter | `send-key="ctrl+enter"` | Ctrl+Enter sends; plain Enter inserts newline |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `placeholder` | string | `"Type a message…"` | Yes | Placeholder text in the mention input |
| `max-length` | number | `0` | Yes | Maximum character count; 0 = unlimited |
| `send-key` | `"enter"\|"ctrl+enter"` | `"enter"` | Yes | Keyboard shortcut to send |
| `allow-attachments` | boolean | `true` | Yes | Shows/hides the attach button |
| `allow-emoji` | boolean | `true` | Yes | Shows/hides the emoji picker button |
| `disabled` | boolean | `false` | Yes | Disables all controls |
| `loading` | boolean | `false` | Yes | Shows send button spinner; disables input while sending |
| `accept` | string | `""` | Yes | File types accepted by the attachment picker |
| `max-attachment-size` | number | `0` | Yes | Per-file size limit in bytes for attachments |
| `label` | string | `"Message composer"` | Yes | Accessible name for the form region |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `value` | string | Plain-text content of the mention input |
| `mentions` | `MentionToken[]` | Structured mention tokens from the mention input |
| `attachments` | `FileEntry[]` | Currently queued file attachments |
| `replyTo` | `{ messageId: string, preview: string } \| null` | Sets the reply preview strip; null hides it |
| `mentionSource` | `MentionDataSource` | Passed through to `<mj-mention-input>` |
| `clear` | `() => void` | Clears the input, mentions, and attachments |

## 7. Slots
| Slot | Description |
|------|-------------|
| `toolbar-start` | Additional controls before the attach button |
| `toolbar-end` | Additional controls after the emoji button but before send |
| `reply-preview` | Custom reply preview strip content (receives `replyTo` via context) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-send` | `{ value: string, mentions: MentionToken[], attachments: FileEntry[], replyTo: string \| null }` | Yes | Yes | Fires when the user sends a message; cancelable to prevent clear |
| `mj-attachment-add` | `{ files: FileEntry[] }` | Yes | No | Fires when files are added via the attach button |
| `mj-attachment-remove` | `{ fileId: string }` | Yes | No | Fires when an attachment is removed |
| `mj-reply-cancel` | `{}` | Yes | No | Fires when the reply preview is dismissed |
| `mj-input` | `{ value: string, mentions: MentionToken[] }` | Yes | No | Fires on every text or mention change (debounced 100 ms for typing indicators) |

## 9. CSS parts & custom properties
**Parts:** `root`, `reply-preview`, `reply-cancel`, `input`, `attachment-bar`, `attachment-item`, `attachment-remove`, `toolbar`, `attach-button`, `emoji-button`, `send-button`, `counter`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-composer-bg` | `var(--mj-color-surface-2)` | Background of the composer root |
| `--mj-composer-border` | `var(--mj-border-control)` | Border around the composer |
| `--mj-composer-radius` | `var(--mj-radius-lg)` | Border radius |
| `--mj-composer-min-height` | `var(--mj-size-control-md)` | Min height of the text area |
| `--mj-composer-max-height` | `200px` | Max height before scrolling |
| `--mj-composer-toolbar-gap` | `var(--mj-space-1)` | Gap between toolbar icons |
| `--mj-composer-attachment-size` | `56px` | Size of attachment preview thumbnails |

## 10. States
- **default** — empty input; send button disabled.
- **has-content** — non-empty text or at least one attachment; send button enabled.
- **loading** — `loading` attribute set; send button shows spinner; input disabled.
- **replying** — `replyTo` is set; reply preview strip visible above input.
- **has-attachments** — attachment bar visible with queued files.
- **disabled** — all controls disabled; visually dimmed.
- **max-length-reached** — counter red; additional typing blocked; send button remains enabled.

## 11. Behavior & interactions
On `send-key` trigger (Enter or Ctrl+Enter) with non-empty content, `mj-send` fires. If not cancelled, `clear()` is called automatically. If `mj-send` is cancelled by the consumer (e.g., to retry failed send), the content is preserved. Attachment files pass through `<mj-file-picker>` validation (type, size). Emoji insertion from `<mj-emoji-picker>` inserts the emoji character at the current cursor position in the mention input. The mention input auto-grows vertically up to `--mj-composer-max-height`. The send button is `aria-disabled="true"` (not `disabled`) when content is empty so it remains focusable with a tooltip explanation.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` (send-key="enter") | Sends the message; fires `mj-send` |
| `Shift+Enter` (send-key="enter") | Inserts a newline |
| `Ctrl+Enter` (send-key="ctrl+enter") | Sends the message |
| `Enter` (send-key="ctrl+enter") | Inserts a newline |
| `Escape` | Clears reply preview if replying; otherwise no action |
| `Tab` | Moves focus to the next control (attach → emoji → send) |
| `Shift+Tab` | Moves focus to previous control |
| `Delete` / `Backspace` on attachment | Removes the focused attachment |

## 13. Accessibility
Root carries `role="form"` with `aria-label`. The mention input is the primary interactive element; it has its own ARIA attributes. The send button has `aria-label="Send message"` (localizable). When disabled (empty content), `aria-disabled="true"` and `title="Type a message to send"`. The attachment bar is `<ul aria-label="Attachments">` with each item as `<li>`. Each attachment remove button is `aria-label="Remove attachment {filename}"`. The reply preview has `role="note"` with `aria-label="Replying to: {preview text}"`. The loading state sets `aria-busy="true"` on the form and `aria-label="Sending…"` on the send button.

## 14. Form participation
Not form-associated in the traditional sense (no ElementInternals value submission). The component manages its own message lifecycle via events. If wrapped in a `<form>`, the consumer should handle `mj-send` and prevent default form submission.

## 15. Internationalization & RTL
`placeholder`, `label`, send button label, attach button label, emoji button label, and error messages are all overridable. In RTL, the toolbar icon order is visually mirrored; the attach button appears on the inline-end and the send button on the inline-start.

## 16. Progressive enhancement / SSR
Server renders a `<form>` with a `<textarea>` and a submit button. Without JS, the user can type and submit. On upgrade the component replaces the textarea with `<mj-mention-input>`, adds the attachment and emoji controls, and intercepts the form submit with `mj-send`.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Overlay/positioning engine, Focus utilities, Live-region/announcement service, Localization/formatting hook.
- **Components:** `<mj-mention-input>`, `<mj-file-picker>`, `<mj-emoji-picker>`, `<mj-button>`, `<mj-progress>` (send spinner), `<mj-image>` (attachment thumbnail), `<mj-chip>` (non-image attachment preview), `<mj-tooltip>` (disabled send button explanation).

## 18. Edge cases & error handling
- Empty text + no attachments: send is blocked; send button `aria-disabled="true"`.
- `max-length` exceeded: additional typing blocked; partial paste allowed up to the limit.
- Attachment validation failure: rejected file shown as a red chip with error icon; valid files proceed.
- `loading` set to `true` externally while user types: input disabled; queued keystrokes discarded.
- Reply preview set to a very long preview text: clamped to 1 line with `text-overflow: ellipsis`.
- Emoji picker not available (`<mj-emoji-picker>` not registered): emoji button hidden gracefully.

## 19. Acceptance criteria
- [ ] `mj-send` fires with `value`, `mentions`, `attachments`, `replyTo` on correct key combo.
- [ ] `clear()` is called automatically after uncancelled `mj-send`.
- [ ] Send button `aria-disabled` when content empty; enabled when content present.
- [ ] Attachments render in the attachment bar; removal fires `mj-attachment-remove`.
- [ ] Reply preview shown when `replyTo` set; Escape clears it.
- [ ] `loading` disables input and shows spinner on send button.
- [ ] `max-length` blocks excess input; counter turns red.
- [ ] Axe scan reports zero violations.
- [ ] RTL toolbar icon order mirrors correctly.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should a "typing indicator" signal be emitted automatically on the debounced `mj-input` event for real-time presence, or left entirely to the consumer?
- Should voice-message recording be a planned extension slot for a future phase?
