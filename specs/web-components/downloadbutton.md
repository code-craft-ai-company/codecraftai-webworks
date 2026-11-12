# Download Button Spec

- **Tag:** `<mj-download-button>`
- **Class / file:** `MjDownloadButton` / `mjdownloadbutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Download button
- **Phase:** P1
- **Status:** Implemented (this spec documents the shipped behavior of `mjdownloadbutton.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-download-button>` is a button-styled control that downloads a file. It renders
a real `<a download>` in its shadow root, so the browser performs the transfer, the
URL shows in the browser's download UI, modifier-clicks behave as on a link, and
`filename` supplies the suggested file name. Each click first emits the cancelable
`mj-download-start`; a listener that calls `preventDefault()` replaces the plain
download with its own flow (signed URL, generated file, progress) and can show
`loading` meanwhile. It satisfies the "Download wraps an anchor with `download`"
requirement of plan §5.3. The component itself never fetches anything.

## 2. When to use / when not to use

Use for an action that saves a file: an export, an attachment, a report, a
generated blob. Use it when the file URL is known up front, or when a listener
builds the file on demand and the button needs a busy state while it does.
Do not use it to navigate to a page or open a document in a tab — use `<mj-link>`
(which has its own `download` attribute for inline text links) or `<mj-button>`
for in-page actions; this component always sets `download` on its anchor. Do not
use it to share a URL — use `<mj-share-button>`; to copy text — use
`<mj-copy-button>`; to pick files for upload — use `<mj-upload-button>`.

`sharebutton.md` (§2) points downloads to this component; it no longer lists
"Download button" as a synonym.

## 3. Anatomy

- **Host element** — `display: inline-block` (`block` when the `block` attribute is
  set); no surface of its own.
- **button (part)** — the inner `<a class="btn">`, styled as a button. It always
  carries `download` and, when the URL is usable, `href`; without a usable URL it
  carries `role="link"` and `tabindex="0"` instead, so it stays a focusable link. It
  is the only focusable target and carries the ARIA attributes.
- **spinner (part)** — a ring before the content, `aria-hidden="true"`, shown only
  while `loading` is set.
- **Default slot** — inside the anchor: the visible text and an optional inline icon.

## 4. Variants & modes

| Mode / variant        | Attribute              | Description |
|-----------------------|------------------------|-------------|
| Default (outlined)    | (no `variant`)         | `--mj-surface` background with a `--mj-border-strong` border. Any value other than the three below renders this way |
| Primary               | `variant="primary"`    | Accent background and border, `--mj-text-on-accent` text |
| Tertiary              | `variant="tertiary"`   | Transparent background and border |
| Link                  | `variant="link"`       | Transparent, accent-colored underlined text, no padding, `min-height: 0` |
| Sizes                 | `size="sm"` / `size="lg"` | Smaller / larger min-height, padding and font size. Any other value (including `md`) is the medium size |
| Icon-only             | `icon-only`            | Zero padding and a 1:1 aspect ratio. The author supplies `label` |
| Block                 | `block`                | Host is `display: block`; the anchor is full width |
| Plain download        | (no listener cancels)  | The browser follows the anchor and downloads the file |
| Intercepted download  | listener calls `preventDefault()` on `mj-download-start` | The browser does nothing; the listener runs its own flow |

## 5. Attributes

| Attribute   | Type                                | Default | Reflects | Description |
|-------------|-------------------------------------|---------|----------|-------------|
| `href`      | URL string                          | —       | Yes      | URL of the file. Passed through the URL safety check (§11); a rejected value leaves the anchor without `href` and logs one console warning. Without a usable `href` the anchor is still a focusable link that only fires `mj-download-start` (§11) |
| `filename`  | string                              | —       | Yes      | Suggested file name, copied to the anchor's `download`. When absent or empty the anchor carries `download=""` and the browser picks the name |
| `variant`   | `primary\|tertiary\|link`           | —       | No       | Visual emphasis (§4). CSS only |
| `size`      | `sm\|lg`                            | —       | No       | Control size (§4). CSS only |
| `target`    | string                              | —       | No       | Copied to the anchor's `target` when non-empty |
| `rel`       | string                              | —       | No       | Copied to the anchor's `rel` when non-empty. When absent or empty and `target` is exactly `_blank`, the anchor gets `rel="noopener noreferrer"` |
| `label`     | string                              | —       | No       | Accessible name: copied to the anchor's `aria-label` when non-empty |
| `loading`   | boolean                             | `false` | Yes      | Busy: spinner shown, clicks swallowed, `aria-disabled` and `aria-busy` set; stays in the tab order |
| `disabled`  | boolean                             | `false` | Yes      | Clicks swallowed, `aria-disabled` set, removed from the tab order (`tabindex="-1"`); removing it restores the previous tab stop |
| `icon-only` | boolean                             | `false` | No       | Square button for an icon-only label. CSS only |
| `block`     | boolean                             | `false` | No       | Full-width layout. CSS only |

Common MjElement attributes (`dock`, `anchor`, `theme`, `hidden`, `context-menu`)
behave as on every component.

## 6. Properties

| Property   | Type      | Description |
|------------|-----------|-------------|
| `href`     | `string`  | Reflects `href`; reads `""` when absent. The setter stores `String(value)` (so `null` becomes `"null"`) |
| `filename` | `string`  | Reflects `filename`; reads `""` when absent. The setter stores `String(value)` |
| `loading`  | `boolean` | Reflects `loading`; a truthy value sets the attribute, a falsy value removes it |
| `disabled` | `boolean` | Reflects `disabled`; a truthy value sets the attribute, a falsy value removes it |

`target`, `rel`, `label`, `variant`, `size`, `icon-only` and `block` have no
properties; set them as attributes.

**Methods**

| Method    | Description |
|-----------|-------------|
| `focus(options)` | Focuses the inner anchor in every state (also without `href`, while `disabled`, and when a container's roving `tabindex="-1"` takes it out of the tab order). A host that carries its own `tabindex` is focused itself |
| `click()` | Clicks the inner anchor, so the full click flow runs: `mj-download-start` first, then the browser download unless a listener cancelled it. Does nothing (and emits nothing) while `disabled` or `loading`. Before the first render it does nothing. `HTMLElement.click()` would only dispatch a click at the host, which never reaches the anchor |

## 7. Slots

| Slot      | Description |
|-----------|-------------|
| (default) | Button content: text and an optional inline icon. It sits inside the anchor, so it must not contain interactive content (links, buttons, inputs) |

## 8. Events

| Event               | `detail`                               | Bubbles | Composed | Cancelable | Description |
|---------------------|----------------------------------------|---------|----------|------------|-------------|
| `mj-download-start` | `{ href: string, filename: string }`   | Yes     | Yes      | Yes        | Fires on each `click` of the inner anchor while neither `disabled` nor `loading` is set, before the browser follows the link. `preventDefault()` cancels the browser download |

- `detail.href` is the URL after the safety check — the same value the anchor
  carries — and `""` when `href` is absent or rejected. `detail.filename` is the
  `filename` attribute, `""` when absent.
- The event is emitted from the `click` listener only. A middle-click (`auxclick`),
  the browser's "Save link as" context-menu entry, or dragging the link out do not
  emit it and are not blocked by a cancelling listener.
- A click while `disabled` or `loading` emits nothing; its default action is
  prevented.
- The native `click` event of the anchor is composed and reaches listeners on the
  host as well (retargeted to the host).

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<a>` styled as the button
- `::part(spinner)` — busy spinner

**Custom properties**

| Property | Description |
|---|---|
| `--mj-download-button-height` | Minimum height of the medium size (default `--mj-control-height-md`). `size="sm"` / `size="lg"` use `--mj-control-height-sm` / `--mj-control-height-lg` instead, and `variant="link"` uses `0` |
| `--mj-download-button-font-weight` | Font weight (default `--mj-font-weight-medium`) |
| `--mj-download-button-color` | Text color (default `--mj-text`); not used by `primary` (`--mj-text-on-accent`) or `link` (`--mj-accent`) |
| `--mj-download-button-bg` | Background (default `--mj-surface`); not used by `primary`, `tertiary` or `link` |
| `--mj-download-button-border-color` | Border color (default `--mj-border-strong`); not used by `primary`, `tertiary` or `link` |
| `--mj-download-button-border-radius` | Corner radius (default `--mj-radius-md`) |
| `--mj-download-button-focus-ring-color` | Focus ring color (default `--mj-focus-ring`) |

The hover background (`--mj-bg-muted`; `--mj-accent-hover` for `primary`) and the
variant colors use library tokens directly and have no component property. The
spinner size is `1em` and its color `currentColor`.

## 10. States

| State         | Visual effect | ARIA effect |
|---------------|---------------|-------------|
| default       | Variant colors | Native link (`href` present); no `tabindex` unless a container set one |
| hover         | `--mj-bg-muted` background (`--mj-accent-hover` for `primary`; `link` stays transparent) | — |
| focus-visible | Focus ring on the anchor (`--mj-focus-ring-width`, `--mj-focus-ring-offset`) | — |
| loading       | Spinner shown; 55 % opacity; `pointer-events: none` on the anchor | `aria-disabled="true"`, `aria-busy="true"`; stays in the tab order |
| disabled      | 55 % opacity; `pointer-events: none` on the anchor | `aria-disabled="true"`, `tabindex="-1"`; no `aria-busy` even when `loading` is also set |
| no usable URL | Looks like the default state | Anchor without `href`, with `role="link"` and `tabindex="0"` (or a container's value): focusable, announced as a link; Enter and click fire `mj-download-start` only |

There is no pressed (`:active`) style.

## 11. Behavior & interactions

- **Anchor sync.** On first render and on every change of an observed attribute
  (the component's own and the common MjElement ones) the anchor's attributes are
  re-synced from the host attributes: `href` (after the safety check) or
  `role="link"`, `download`, `target`, `rel`, `aria-label`, `aria-disabled`,
  `aria-busy` and `tabindex`. `variant`, `size`, `icon-only` and `block` only drive
  CSS.
- **Tab stop.** The component writes the anchor's `tabindex` only when its state
  needs one: `-1` while `disabled`, `0` while there is no usable `href`. A
  `tabindex` found on the anchor that the component did not write was set by a
  managing container (the roving tab stop of `<mj-toolbar>`); it is remembered and
  kept on every re-sync. `disabled` overrides it with `-1`; removing `disabled`
  puts the container's value back. A re-render (reconnect after a removal, locale
  change) starts from a fresh anchor and forgets the container's value, so a button
  moved out of a toolbar does not keep its roving `tabindex`; the container sets it
  again when it re-collects its items. Without a container value, an anchor with `href` carries
  no `tabindex`.
- **URL safety.** `href` goes through `safeUrl()` from `core/html.js`, which keeps
  scheme-less (relative) URLs and the schemes `http:`, `https:`, `mailto:`, `tel:`,
  `sms:` and `blob:`, plus `data:image/(png|gif|jpeg|jpg|webp|avif|bmp)`. In
  addition the component accepts every other `data:` URL (any MIME type), because
  the anchor always carries `download` and the browser saves rather than opens it.
  Control characters and spaces are ignored when the scheme is checked. Any other
  scheme (for example `javascript:`) yields no `href` on the anchor and a
  `console.warn`. Only the last rejected value is remembered, so the warning is
  not repeated while `href` keeps the same rejected value, but alternating between
  two rejected values warns each time.
- **Activation.** A `click` on the anchor (pointer, Enter, or `click()`) is
  swallowed (`preventDefault()`, no event) while `disabled` or `loading` is set.
  An anchor without `href` has no native Enter activation; the component maps a
  plain Enter (no Alt/Ctrl/Meta) on it to a click, so the flow is the same as with
  an `href`.
  Otherwise `mj-download-start` is emitted; if a listener cancelled it the click's
  default action is prevented, otherwise the browser follows the anchor as a
  download (without `href` nothing happens). Modifier-clicks (Ctrl/Cmd/Shift) also emit the event and, if it is not
  cancelled, get the browser's usual modifier behavior.
- **Custom flow.** The component performs no network request, progress reporting,
  abort or error handling. The intended pattern is: cancel `mj-download-start`,
  set `loading = true`, produce the file (fetch, generate, sign), save it (for
  example through a temporary `<a download>` with a blob URL), then set
  `loading = false`. While `loading` is set further clicks are swallowed, so the
  flow cannot be started twice.
- **Cross-origin URLs.** The `download` attribute (and so `filename`) is honored by
  browsers only for same-origin, `blob:` and `data:` URLs; for a cross-origin URL
  the browser may navigate instead, in `target` if set. The server's
  `Content-Disposition` header decides in that case.
- A locale change renders the component again (MjElement default); it has no
  strings of its own, so nothing visible changes.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Enter`     | Activates the anchor (native link behavior; mapped by the component when there is no `href`): `mj-download-start`, then the download unless cancelled |
| `Space`     | No action from the component (native link behavior; the page may scroll) |
| `Tab`       | Moves focus to the next focusable element |
| `Shift+Tab` | Moves focus to the previous focusable element |

The only custom key handling is Enter on an anchor without `href` (mapped to a
click, as a native link does with one). A `disabled` button is not in the tab order;
a `loading` button is, and Enter on it does nothing. Without a usable `href` the
anchor is still in the tab order (`tabindex="0"`) and Enter fires
`mj-download-start`. `element.focus()` focuses the inner anchor in every state —
also while `disabled`, since `tabindex="-1"` does not prevent programmatic focus.
Inside `<mj-toolbar>` the toolbar's roving `tabindex` decides the tab stop.

## 13. Accessibility

- Role: the native anchor with `href` is exposed as a **link**, not a button, which
  matches the plan's "Download wraps an anchor" requirement and the browser's
  link affordances. Screen readers announce "link". Without a usable `href` the
  anchor carries `role="link"`, so the role does not change when a page sets the
  URL later.
- Name: the slotted content, or `label` (as `aria-label`) when set. `icon-only`
  buttons need `label`; the component does not supply a default name.
- `disabled` and `loading` both set `aria-disabled="true"`; `loading` (without
  `disabled`) adds `aria-busy="true"` and stays focusable so the busy state can be
  discovered; `disabled` sets `tabindex="-1"`.
- The spinner is `aria-hidden="true"`. The component does not announce the start
  or end of a download and uses no live region; a custom flow that takes time
  should announce its own outcome.
- The suggested `filename` is not exposed to assistive technology; include it in
  the visible text or `label` when it matters.
- Target size: `min-width: var(--mj-target-min)` always applies; the medium
  min-height is `--mj-control-height-md`. `variant="link"` has `min-height: 0` and
  no padding.

## 14. Form participation

N/A. `<mj-download-button>` is not form-associated and contributes no value.

## 15. Internationalization & RTL

- The component has no strings of its own and reads no `t()` keys. The visible
  text comes from the default slot and the accessible name override from `label`;
  both are author-provided. The console warning for a rejected `href` is English
  and not localized.
- Layout is inline flex with a gap; the spinner precedes the content in the inline
  direction and so mirrors in RTL. The spinner's open segment uses
  `border-inline-end-color` and mirrors as well.
- Under `prefers-reduced-motion: reduce` the background transition and the spinner
  rotation are turned off (the spinner shows as a static ring).

## 16. Progressive enhancement / SSR

Server renders
`<mj-download-button href="/files/report.csv" filename="report.csv">Download report</mj-download-button>`.
Before upgrade only the text shows, as inline content with no link and no
download. On upgrade the shadow anchor, styling and ARIA appear and the
server-rendered attributes are applied. A light-DOM `<a>` cannot be used as a
fallback inside the element, because slotted content ends up inside the shadow
anchor. Pages that must work without JavaScript render a plain `<a download>`
instead.

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `afterRender`,
  `onAttributeChanged`, `listen`, `emit`, `focus()`, docking / anchoring)
- **Safe HTML/URL helpers** — `safeUrl()` from `core/html.js`
- **Design-token stylesheet** (§6)
- Consumers: `<mj-toolbar>` treats `mj-download-button` as a toolbar item and
  manages the tab stop on its inner anchor; the component keeps that value (§11)
- Related: `<mj-button>` (same variant/size vocabulary), `<mj-link>` (`download` on a
  text link), `<mj-upload-button>`, `<mj-share-button>`, `<mj-copy-button>`

## 18. Edge cases & error handling

- `href` absent, empty or rejected: the anchor has no `href` but `role="link"` and
  `tabindex="0"`; a click or Enter emits `mj-download-start` with `href: ""` and
  then nothing happens unless a listener runs its own flow from that event (the
  listener-driven download, reachable from the keyboard).
- `javascript:` (or any other disallowed scheme, including obfuscated forms with
  embedded spaces or control characters): dropped, with one warning for as long as
  the value stays the same.
- Any `data:` URL is allowed, including types such as `data:text/html`; the anchor
  saves it because of `download`. A listener that cancels the event and navigates
  to `detail.href` itself takes on that risk.
- `filename` with path separators or reserved characters: passed to the browser
  unchanged; the browser sanitizes it.
- `target="_blank"` with no `rel` gets `rel="noopener noreferrer"`; the comparison
  is exact (`_BLANK` does not get the default). An author `rel` wins even if it
  omits `noopener`.
- `disabled` and `loading` together: treated as disabled for ARIA (no
  `aria-busy`) and focus (`tabindex="-1"`); clicks are swallowed.
- Inside `<mj-toolbar>`: the toolbar sets the anchor's `tabIndex` for its roving tab
  stop; attribute changes of the button (for example toggling `loading` or `label`)
  keep that value, so the toolbar keeps exactly one tab stop. A container value
  equal to the one the component would write itself (`0` without `href`) cannot be
  told apart and is treated as the component's own.
- `mj-download-start` cancelled by one listener while another listener expects the
  plain download: the cancel wins; the component does not coordinate listeners.
- Clicks during `loading` are swallowed silently; no event tells the page a click
  was ignored.

## 19. Acceptance criteria

- [ ] The shadow anchor always carries `download`; it equals `filename`, or is empty without it.
- [ ] Relative, `http:`, `https:`, `mailto:`, `tel:`, `sms:`, `blob:` and `data:` URLs reach the anchor's `href`.
- [ ] `javascript:` and other disallowed schemes leave the anchor without `href` and log a warning that is not repeated for the same value.
- [ ] A click emits `mj-download-start` with `{ href, filename }`; it bubbles, is composed and is cancelable.
- [ ] Cancelling `mj-download-start` prevents the browser download.
- [ ] While `disabled` or `loading`, clicks emit nothing and do not download.
- [ ] `click()` runs the same flow as a user click.
- [ ] `target` and `rel` are forwarded; `target="_blank"` without `rel` yields `rel="noopener noreferrer"`.
- [ ] `label` becomes the anchor's `aria-label`.
- [ ] `loading` shows the spinner, sets `aria-busy` and `aria-disabled`, and keeps the anchor focusable.
- [ ] `disabled` sets `aria-disabled` and `tabindex="-1"`; removing it restores a container's tab stop.
- [ ] Without a usable `href` the anchor has `role="link"`, is focusable, and Enter emits `mj-download-start`.
- [ ] A `tabindex` set on the anchor by `<mj-toolbar>` survives attribute changes of the button.
- [ ] `href`, `filename`, `loading` and `disabled` properties reflect their attributes.
- [ ] Enter activates (with or without `href`); Space and other keys are not handled by the component.
- [ ] `variant`, `size`, `icon-only` and `block` render as described in §4.
- [ ] axe scan zero violations in the default, loading, disabled and icon-only (with `label`) states.
- [ ] Light, dark, high-contrast, reduced-motion and RTL rendering verified.

## 20. Open questions

- Should Space activate the button, as on `<mj-button>`, given that it is styled
  and labelled as a button but exposed as a link?
- Should `auxclick` (middle-click) also emit `mj-download-start`, or should a
  listener-driven download remove `href` so the browser cannot bypass the event?
- Should the component offer an opt-in fetch flow (progress, abort, error state)
  instead of leaving it entirely to listeners?
- Should any `data:` URL be accepted, or only types that are inert when opened, as
  `safeUrl()` and `safeLinkUrl()` do?
- Should `variant="secondary"` be an explicit value, as on `<mj-button>`? Today it
  renders as the default because no rule matches it; the catalog examples use the
  default.
- Should the component announce completion or failure of a custom flow through the
  live-region announcer, or expose a status attribute for it?
