# Chat Message Spec

- **Tag:** `<mj-chat-message>`
- **Class / file:** `ChatMessage` / `chatmessage.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Chat bubble, Message bubble
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-chat-message>` renders a single message in a chat thread, including the author avatar, display name, timestamp, message body (text with mention tokens, attachments, and embedded media), delivery/read status indicators, and an emoji reaction bar. It supports both outgoing and incoming visual styles. New messages are announced politely to screen readers. It is designed to be used inside a `<div role="feed">` (typically managed by a chat list component).

## 2. When to use / when not to use
Use as the item component within a chat message list. Do not use for comment threads — use `<mj-comments>`. Do not use for a plain list of notifications — use `<mj-activity-feed>`.

## 3. Anatomy
- **article root** — `<article aria-labelledby="{id}-header">` to satisfy the `feed` item pattern.
- **avatar** — `<mj-avatar>` of the author; hidden for consecutive messages from the same author.
- **header** — `<header id="{id}-header">` with author name `<strong>` and `<time>` timestamp.
- **body** — rendered message content: plain text, mention tokens, rich text (Markdown HTML output), or media.
- **attachments** — list of `<mj-image>`, `<mj-media-player>`, or file chip `<mj-chip>` elements.
- **reply preview** — quoted excerpt if the message is a reply to another message.
- **reaction bar** — `<mj-chip>` list of emoji + count; current user's reactions shown as selected.
- **status indicator** — delivery/read status icon + text at the trailing edge of the message.
- **action menu trigger** — `<mj-button>` revealed on hover/focus that opens a context action menu.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Incoming | `variant="incoming"` (default) | Avatar and name on inline-start; bubble left-aligned |
| Outgoing | `variant="outgoing"` | Avatar omitted or on inline-end; bubble right-aligned; status indicator visible |
| System | `variant="system"` | Centered; no avatar; lighter style; used for system messages |
| Consecutive | `consecutive` | Avatar and name hidden; reduced top padding |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `variant` | `"incoming"\|"outgoing"\|"system"` | `"incoming"` | Yes | Visual and semantic variant |
| `consecutive` | boolean | `false` | Yes | Hides avatar/name for consecutive same-author messages |
| `author-name` | string | `""` | Yes | Display name of the message author |
| `author-id` | string | `""` | Yes | ID of the author; used for avatar lookup |
| `author-avatar` | string | `""` | Yes | URL of the author's avatar image |
| `timestamp` | string | `""` | Yes | ISO-8601 timestamp string |
| `status` | `"sent"\|"delivered"\|"read"\|"failed"` | `"sent"` | Yes | Delivery status (outgoing only) |
| `message-id` | string | `""` | Yes | Unique message ID; used for reply references |
| `allow-reactions` | boolean | `true` | Yes | Shows the reaction bar |
| `allow-actions` | boolean | `true` | Yes | Shows the action menu trigger |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `bodyHtml` | string | Sanitized HTML string for the message body (output of a Markdown renderer) |
| `attachments` | `AttachmentEntry[]` | `{ id, name, mimeType, url, size, thumbnailUrl? }` |
| `reactions` | `Reaction[]` | `{ emoji, count, userIds: string[] }` |
| `replyTo` | `{ messageId: string, authorName: string, preview: string } \| null` | Source message for the quoted reply preview |
| `currentUserId` | string | The ID of the logged-in user; controls which reactions are shown as "active" |

## 7. Slots
| Slot | Description |
|------|-------------|
| `body` | Custom message body; replaces built-in text/HTML rendering |
| `actions` | Additional items in the action menu |
| `attachment-{mimeType}` | Custom renderer for a specific attachment MIME type |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-message-react` | `{ messageId: string, emoji: string, active: boolean }` | Yes | No | Fires when a reaction is toggled |
| `mj-message-action` | `{ messageId: string, action: string }` | Yes | No | Fires when an action menu item is activated |
| `mj-message-reply` | `{ messageId: string }` | Yes | No | Fires when "Reply" action is chosen |
| `mj-message-link-click` | `{ href: string, messageId: string }` | Yes | Yes | Fires when a link in the message body is clicked; cancelable |

## 9. CSS parts & custom properties
**Parts:** `root`, `avatar`, `header`, `author-name`, `timestamp`, `body`, `reply-preview`, `bubble`, `attachments`, `reaction-bar`, `status`, `actions-trigger`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-msg-bubble-bg-incoming` | `var(--mj-color-surface-3)` | Bubble background for incoming messages |
| `--mj-msg-bubble-bg-outgoing` | `var(--mj-color-accent)` | Bubble background for outgoing messages |
| `--mj-msg-bubble-color-outgoing` | `var(--mj-color-on-accent)` | Text color inside outgoing bubble |
| `--mj-msg-bubble-radius` | `var(--mj-radius-lg)` | Bubble border radius |
| `--mj-msg-avatar-size` | `var(--mj-size-avatar-sm)` | Author avatar size |
| `--mj-msg-max-width` | `70%` | Maximum width of the message bubble |
| `--mj-msg-timestamp-color` | `var(--mj-color-text-secondary)` | Timestamp text color |
| `--mj-msg-status-color-read` | `var(--mj-color-accent)` | Color of the "read" status icon |

## 10. States
- **default** — rendered in the feed; actions trigger hidden.
- **hover / focus-within** — actions trigger button becomes visible; bubble may gain subtle shadow.
- **status-sent** — single checkmark icon; `aria-label="Sent"` on status element.
- **status-delivered** — double checkmark; `aria-label="Delivered"`.
- **status-read** — double checkmark in accent color; `aria-label="Read"`.
- **status-failed** — red exclamation icon; `aria-label="Failed to send"`; retry action in menu.
- **consecutive** — avatar and author name hidden; reduced vertical gap.
- **reaction-active** — a reaction chip is visually pressed for the current user.

## 11. Behavior & interactions
The action menu trigger is visually hidden until the message gains hover or focus-within. Activating it opens an `<mj-context-menu>` with options such as "Reply", "Copy text", "Edit" (own messages), "Delete" (own messages), "Forward". Reactions: clicking a chip calls `mj-message-react`; the consumer updates `reactions` optimistically and rolls back on server failure. Links in `bodyHtml` fire `mj-message-link-click` (cancelable) before default navigation, allowing the consumer to intercept internal links. Timestamps use `Intl.RelativeTimeFormat`; hovering or focusing the `<time>` element shows the absolute formatted date via `<mj-tooltip>`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Enters the message article; focuses links and buttons inside |
| `Tab` to actions trigger | Focuses the action menu trigger button |
| `Enter` / `Space` on trigger | Opens the action context menu |
| `Escape` | Closes the action context menu |
| `Enter` / `Space` on reaction chip | Toggles the reaction |
| `Tab` out of article | Moves to the next message article in the feed |

## 13. Accessibility
Each message is `<article aria-labelledby="{id}-header">` to fit the `role="feed"` pattern. The header contains the author name and timestamp that form the accessible label. Status indicators use `aria-label` describing the status text (never icon-only without a text alternative). Consecutive messages that hide the author name still carry `aria-label` on the article with the author name for screen readers. New messages arriving in real time are announced via the parent feed's live region ("New message from Alice"), not by the individual article, to avoid spurious re-reads. Reaction chips use `aria-pressed` for the current user's state. The action trigger has `aria-label="Message actions"` and `aria-haspopup="menu"`.

## 14. Form participation
N/A — display-only component.

## 15. Internationalization & RTL
`author-name` and all user-facing strings (status labels, action labels) are localizable. Timestamps use `Intl.DateTimeFormat` for the absolute form and `Intl.RelativeTimeFormat` for relative. In RTL, outgoing messages appear on the inline-start side and incoming on the inline-end (i.e., the alignment convention flips so the user's own messages are still visually distinguished as "right" in the user's reading direction).

## 16. Progressive enhancement / SSR
Server renders a plain `<article>` with author, timestamp, and body as static text. Without JS, reactions and action menus are not interactive. On upgrade, the component attaches reaction toggle handlers, the action menu, and live timestamp refresh.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Overlay/positioning engine, Live-region/announcement service, Localization/formatting hook.
- **Components:** `<mj-avatar>`, `<mj-chip>` (reactions, file attachments), `<mj-image>`, `<mj-media-player>`, `<mj-context-menu>`, `<mj-button>`, `<mj-tooltip>`.

## 18. Edge cases & error handling
- `bodyHtml` contains malicious markup: sanitized by the component using an allowlist before injection into the DOM.
- Very long single word with no break opportunity: `overflow-wrap: break-word` applied to the bubble.
- `status="failed"` with no retry handler: "Retry" action fires `mj-message-action` with `action="retry"`; consumer must implement.
- Message body is empty (attachment only): body element not rendered; bubble still has correct min-height.
- `author-avatar` URL 404s: `<mj-avatar>` falls back to initials.
- `timestamp` is in the future (clock skew): relative format shows the absolute date as a fallback.

## 19. Acceptance criteria
- [ ] `<article aria-labelledby>` structure present; label includes author name and timestamp.
- [ ] Status indicators have text alternatives (`aria-label`); not icon-only.
- [ ] Reaction chips toggle `aria-pressed`; `mj-message-react` fires with correct `active` boolean.
- [ ] Action menu trigger appears on hover/focus; opens context menu; Escape closes.
- [ ] `bodyHtml` is sanitized before DOM injection.
- [ ] Consecutive messages hide avatar/name in DOM and compensate with article `aria-label`.
- [ ] RTL: outgoing message alignment mirrors correctly.
- [ ] Axe scan reports zero violations.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should the component support inline image lightbox preview (opening `<mj-lightbox>` on image click) natively?
- Should message editing be handled within this component (inline edit mode) or delegated entirely to the parent chat list?
