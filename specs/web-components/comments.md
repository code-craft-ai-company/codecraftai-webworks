# Comments Spec

- **Tag:** `<mj-comments>`
- **Class / file:** `Comments` / `comments.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Threaded comments, Comment thread, Discussion thread
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-comments>` renders a threaded comment section supporting nested replies, inline editing, deletion with confirmation, emoji reactions, relative timestamps, and `@`/`#` mention input. It is built on the `feed` ARIA pattern and delegates mention detection to `<mj-mention-input>`. Comments can be loaded incrementally and updated in real time.

## 2. When to use / when not to use
Use for structured conversational threads anchored to a piece of content (document comments, ticket discussions, review feedback). Do not use for a real-time chat interface — use `<mj-chat-composer>` and `<mj-chat-message>`. Do not use for a flat event log — use `<mj-activity-feed>`.

## 3. Anatomy
- **feed root** — `<div role="feed" aria-label="Comments">`.
- **comment count heading** — `<h2>` or `<h3>` with the count: "N comments".
- **top-level comment** — `<article>` with `aria-labelledby` pointing to the author + timestamp header.
- **comment header** — `<mj-avatar>`, author name `<strong>`, relative `<time>`, and action menu button.
- **comment body** — rendered HTML from Markdown or plain text (sanitized).
- **comment actions** — reply button, reaction button, edit button (if `currentUserId` matches author), delete button.
- **reaction bar** — `<mj-chip>` list of emoji + count; click to toggle own reaction.
- **reply thread** — nested `<div role="group" aria-label="Replies to {author}">` containing child `<article>` elements; collapsed by default beyond `max-visible-replies`.
- **reply composer** — inline `<mj-mention-input>` shown on reply activation; submit and cancel buttons.
- **top-level composer** — `<mj-mention-input>` at the top or bottom of the feed for new root comments.
- **load-more replies** — "Show N more replies" button per thread.
- **load-older comments** — "Load earlier comments" button or infinite-scroll sentinel.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default | (none) | Composer at bottom; threads collapsed |
| Composer at top | `composer-position="top"` | Composer rendered above the comment list |
| Flat | `max-depth="1"` | No nested replies; all replies shown as top-level |
| Read-only | `readonly` | No composer, reply, edit, or delete; reactions may be allowed |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `current-user-id` | string | `""` | Yes | ID of the authenticated user; gates edit/delete controls |
| `readonly` | boolean | `false` | Yes | Hides all write actions |
| `max-depth` | number | `3` | Yes | Maximum nesting depth for replies |
| `max-visible-replies` | number | `3` | Yes | Replies shown before "Show N more" |
| `allow-reactions` | boolean | `true` | Yes | Enables the emoji reaction bar |
| `composer-position` | `"top"\|"bottom"` | `"bottom"` | Yes | Position of the top-level composer |
| `empty-message` | string | `"Be the first to comment."` | Yes | Empty state message |
| `label` | string | `"Comments"` | Yes | `aria-label` on the feed root |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `comments` | `Comment[]` | Current comment tree: `{ id, authorId, authorName, authorAvatar, body, createdAt, updatedAt?, reactions?, replies? }` |
| `dataSource` | `CommentDataSource \| null` | Provides `fetch()`, `post()`, `edit()`, `delete()`, `react()` methods |
| `mentionSource` | `DataSourceAdapter \| null` | Passed through to `<mj-mention-input>` for `@` suggestions |
| `addComment` | `(comment: Comment) => void` | Prepends or appends a new comment in real-time |

## 7. Slots
| Slot | Description |
|------|-------------|
| `composer-header` | Content above the top-level composer (e.g., sort/filter controls) |
| `comment-actions-{userId}` | Extra actions for comments by a specific user |
| `empty` | Replaces the built-in empty state |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-comment-post` | `{ body: string, parentId: string \| null, mentions: Mention[] }` | Yes | No | Fires when a new comment is submitted |
| `mj-comment-edit` | `{ commentId: string, body: string }` | Yes | No | Fires when an edit is submitted |
| `mj-comment-delete` | `{ commentId: string }` | Yes | No | Fires after delete confirmation |
| `mj-comment-react` | `{ commentId: string, emoji: string, active: boolean }` | Yes | No | Fires when a reaction is toggled |
| `mj-load-older` | `{ cursor: string \| null }` | Yes | No | Fires when more comments are requested |
| `mj-load-replies` | `{ commentId: string, cursor: string \| null }` | Yes | No | Fires when more replies are expanded |

## 9. CSS parts & custom properties
**Parts:** `root`, `count-heading`, `comment`, `comment-header`, `comment-body`, `comment-actions`, `reaction-bar`, `reply-thread`, `reply-composer`, `top-composer`, `load-more-replies`, `load-older`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-comments-gap` | `var(--mj-space-5)` | Gap between top-level comments |
| `--mj-comments-reply-indent` | `var(--mj-space-8)` | Indent for each reply nesting level |
| `--mj-comments-avatar-size` | `var(--mj-size-avatar-sm)` | Avatar size |
| `--mj-comments-thread-line` | `2px solid var(--mj-color-border)` | Vertical line connecting replies |
| `--mj-comments-bg` | `transparent` | Background of the comments region |
| `--mj-comments-composer-bg` | `var(--mj-color-surface-2)` | Background of the composer area |

## 10. States
- **default** — comments loaded; composer visible.
- **loading** — initial load; skeleton placeholders.
- **empty** — no comments; empty state with composer.
- **submitting** — composer submit button loading; `<mj-mention-input>` disabled.
- **editing** — a comment body replaced with an `<mj-mention-input>` pre-filled with the existing text.
- **deleting** — delete confirmation dialog open.
- **readonly** — no edit/delete/reply/composer rendered.
- **reply-expanded** — a thread's collapsed replies are shown.

## 11. Behavior & interactions
Clicking "Reply" on a comment opens an inline `<mj-mention-input>` below the comment body within the same `<article>`. Submitting it emits `mj-comment-post` with `parentId` set; `dataSource.post()` is called if a data source is configured. Editing replaces the comment body with a pre-filled `<mj-mention-input>`; Esc cancels and restores the original text. Deleting shows an `<mj-dialog>` confirmation before emitting `mj-comment-delete`. Reactions: clicking a reaction chip toggles the current user's reaction; the count updates optimistically. If the server call fails, the optimistic update is rolled back and an error toast shown. Timestamps refresh every 60 seconds via `Intl.RelativeTimeFormat`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Navigate through comments and controls |
| `Page Down` / `Page Up` | Move between top-level comment articles (APG Feed) |
| `Enter` on "Reply" button | Opens inline reply composer |
| `Enter` in composer | Submits if `<mj-mention-input>` has no open suggestion popup |
| `Escape` in edit/reply composer | Cancels and restores the prior state |
| `Enter` / `Space` on reaction chip | Toggles the reaction |
| `Enter` / `Space` on delete button | Opens confirmation dialog |

## 13. Accessibility
Feed root carries `role="feed"` with `aria-label`. Each comment is `<article>` with `aria-labelledby` its author + timestamp header. Nested reply threads use `role="group"` with `aria-label="Replies to {authorName}"`. `aria-busy="true"` on the feed root during initial load and during reply expansion. Reaction chips carry `aria-pressed` and `aria-label="React with {emoji}, {count} reactions"`. The delete confirmation uses `<mj-dialog role="alertdialog">`. Edit and delete buttons are only rendered for `current-user-id`-matching comments, reducing noise for other users. Inline composers inherit accessibility from `<mj-mention-input>`.

## 14. Form participation
N/A — the component manages its own submission cycle. Not form-associated.

## 15. Internationalization & RTL
All user-facing strings (empty message, button labels, confirmation text, count heading, timestamps) are overridable. Relative timestamps use `Intl.RelativeTimeFormat`. Comment count heading uses `Intl.PluralRules` for "1 comment" vs. "N comments". In RTL, avatars and thread indent are on the inline-end side.

## 16. Progressive enhancement / SSR
Server renders a `<section>` with static `<article>` elements for each comment. Without JS, comments are readable. The composer degrades to a visible `<textarea>` + `<button type="submit">` inside a `<form>`. On upgrade the component replaces the form with `<mj-mention-input>` and hooks up the event-based submission.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Live-region/announcement service, Data-source adapter interface, Localization/formatting hook.
- **Components:** `<mj-mention-input>`, `<mj-avatar>`, `<mj-button>`, `<mj-chip>`, `<mj-dialog>`, `<mj-skeleton-loader>`, `<mj-empty-state>`, `<mj-alert>`, `<mj-toast>`.

## 18. Edge cases & error handling
- `max-depth` reached: "Reply" button replaced with a "Reply to root thread" link pointing to the top-level ancestor.
- Deleted comment with existing replies: body replaced with "[Comment deleted]" in italics; replies remain.
- Very long comment body: `<mj-disclosure>` "Show more / Show less" wraps body beyond 10 lines.
- Network failure on post: composer re-enabled; error message shown inline.
- Concurrent edit (another user edits while this user is editing): on submit, a conflict toast prompts the user to view the updated version.

## 19. Acceptance criteria
- [ ] `role="feed"` with `aria-label` on root; each comment is `<article>` with `aria-labelledby`.
- [ ] Page Down / Page Up navigate between top-level articles.
- [ ] Replying opens inline `<mj-mention-input>`; Esc cancels without data loss.
- [ ] Editing pre-fills mention input; Esc restores original; submit emits `mj-comment-edit`.
- [ ] Delete emits `mj-comment-delete` only after alertdialog confirmation.
- [ ] Reaction optimistic update rolls back on server error.
- [ ] `current-user-id` gates edit/delete buttons correctly.
- [ ] Axe scan reports zero violations.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should the component support rich-text (Markdown) rendering of comment bodies, or plain text only by default?
- Should reactions be a configurable emoji set (e.g., GitHub-style) or a free emoji picker?
