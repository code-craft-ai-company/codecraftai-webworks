# Share Button Spec

- **Tag:** `<mj-share-button>`
- **Class / file:** `MjShareButton` / `mjsharebutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Share button, Download button (as a related concept — see §2),
  Upload button (relationship noted — see §2)
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-share-button>` invokes the platform Web Share API to share a URL, title, and
optional text with the user's chosen native share target (contacts, apps, clipboard).
When the Web Share API is unavailable or when the consumer opts in to a richer
experience, it falls back to a menu of explicit share targets (copy link, email,
social channels configured by the consumer). It consolidates the "Share" action
pattern for the entire library.

## 2. When to use / when not to use

Use for sharing a URL or piece of content to external destinations. For downloading
a file: use a plain `<a download href="…">` wrapped as `<mj-button>` — a download
anchor, not this component (the catalog notes the Download button is conceptually
related but is satisfied by `<mj-button>` wrapping a real anchor with the `download`
attribute). For uploading: use `<mj-file-picker>` — the Upload button concept in the
catalog is the trigger for that component, not this one. Do not use `<mj-share-button>`
for in-app clipboard operations — use `<mj-copy-button>`.

## 3. Anatomy

- **Host element** — the custom element; no visual surface beyond the button.
- **button (part)** — inner `<button>`; the focusable trigger.
- **icon (part)** — share icon slot (defaults to internal share icon).
- **label (part)** — default slot for visible label text.
- **fallback-menu (part)** — `<mj-menu>` rendered when Web Share API is unavailable
  or `force-menu` is set; contains configured share target items.
- **menu-item (part)** — individual share target items inside the fallback menu.

## 4. Variants & modes

| Mode                    | Condition | Description |
|-------------------------|-----------|-------------|
| Native share sheet      | `navigator.share` available and `force-menu` is false | Invokes OS share sheet directly |
| Fallback menu           | `navigator.share` unavailable or `force-menu="true"` | Opens an `<mj-menu>` of configured targets |
| Icon only               | `icon-only` attribute | Hides label; `label` attribute provides accessible name |
| Icon + label            | default | Icon and label both visible |

## 5. Attributes

| Attribute      | Type                               | Default         | Reflects | Description |
|----------------|------------------------------------|-----------------|----------|-------------|
| `share-url`    | string (URL)                       | `location.href` | Yes      | URL to share |
| `share-title`  | string                             | `document.title`| Yes      | Title for the share payload |
| `share-text`   | string                             | —               | Yes      | Optional body text for the share payload |
| `share-files`  | string (JSON array of URLs)        | —               | Yes      | Optional files; requires browser support for file sharing |
| `force-menu`   | boolean                            | `false`         | Yes      | Always show the fallback menu, even if Web Share API is available |
| `variant`      | `primary\|secondary\|tertiary`     | `secondary`     | Yes      | Visual emphasis |
| `size`         | `sm\|md\|lg`                       | `md`            | Yes      | Token-mapped dimensions |
| `disabled`     | boolean                            | `false`         | Yes      | Disables interaction; `aria-disabled="true"` |
| `loading`      | boolean                            | `false`         | Yes      | Shows spinner; `aria-busy="true"` |
| `icon-only`    | boolean                            | `false`         | Yes      | Hides label visually; requires `label` |
| `label`        | string                             | `"Share"`       | Yes      | Accessible name and visible label |
| `menu-label`   | string                             | `"Share via"`   | Yes      | Accessible name for the fallback menu |

## 6. Properties

| Property       | Type                                    | Description |
|----------------|-----------------------------------------|-------------|
| `shareData`    | `ShareData` object                      | Programmatic override for the full share payload; takes precedence over individual `share-*` attributes |
| `shareTargets` | `Array<{ label: string, href?: string, handler?: Function }>` | Configures fallback menu items programmatically |
| `canShare`     | `boolean` (read-only)                   | `true` when `navigator.share` is available and `force-menu` is false |

## 7. Slots

| Slot             | Description |
|------------------|-------------|
| (default)        | Visible button label |
| `icon`           | Share icon (defaults to internal share icon SVG) |
| `menu-item`      | Additional `<mj-menu-item>` entries appended to the fallback menu |

## 8. Events

| Event              | `detail`                                 | Bubbles | Cancelable | Description |
|--------------------|------------------------------------------|---------|------------|-------------|
| `mj-share`         | `{ method: 'native'\|'menu', data: ShareData }` | Yes | No | Fired after the native share sheet is invoked |
| `mj-share-select`  | `{ target: string, data: ShareData }`    | Yes     | No         | Fired when user selects a fallback menu target |
| `mj-share-error`   | `{ error: Error }`                       | Yes     | No         | Fired when the share operation fails |
| `mj-menu-open`     | `{}`                                     | Yes     | No         | Fallback menu opened |
| `mj-menu-close`    | `{}`                                     | Yes     | No         | Fallback menu closed |

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<button>`
- `::part(icon)` — icon wrapper
- `::part(label)` — label text wrapper
- `::part(fallback-menu)` — the fallback `<mj-menu>` element
- `::part(menu-item)` — individual menu items
- `::part(spinner)` — loading spinner

**Custom properties**
| Property | Description |
|---|---|
| `--mj-share-button-bg` | Background color |
| `--mj-share-button-color` | Icon/label color |
| `--mj-share-button-border-color` | Border color |
| `--mj-share-button-border-radius` | Corner radius |
| `--mj-share-button-height` | Height (size token) |
| `--mj-share-button-focus-ring-color` | Focus ring color |
| `--mj-share-button-menu-width` | Min-width of the fallback menu |

## 10. States

| State         | Visual effect | ARIA effect |
|---------------|---------------|-------------|
| default       | Resting colors | — |
| hover         | Tinted overlay | — |
| focus-visible | 2 px focus ring | — |
| active        | Pressed tint | — |
| loading       | Spinner replaces icon | `aria-busy="true"` |
| menu-open     | Button appears active; menu visible | `aria-expanded="true"`, `aria-haspopup="menu"` |
| disabled      | Reduced opacity; no pointer events | `aria-disabled="true"` |

## 11. Behavior & interactions

- On activation, if `canShare` is true, `navigator.share(shareData)` is called.
  `loading` is set to true during the async operation and cleared on resolve/reject.
  On success `mj-share` fires; on failure `mj-share-error` fires.
- If `canShare` is false (or `force-menu` is set), clicking opens the fallback
  `<mj-menu>` anchored below the button (positioning via the overlay engine).
  The menu contains default targets (Copy link) plus any configured `shareTargets`
  and any slotted `<mj-menu-item>` elements.
- Default fallback menu targets (configurable):
  1. Copy link — invokes `navigator.clipboard.writeText(share-url)` then closes menu.
  2. Email — opens `mailto:?subject=…&body=…` link.
  3. Any additional consumer-configured targets.
- The fallback menu follows the APG Menu pattern: opened by the button, dismissible
  with Escape or click outside, focus returns to the trigger on close.
- `share-files` is only used when `navigator.canShare({ files })` returns true;
  otherwise files are silently dropped and the URL-only payload is used.

## 12. Keyboard interaction

| Key              | Action |
|------------------|--------|
| `Space` / `Enter`| Activates share (native sheet or opens fallback menu) |
| `Tab`            | Moves focus to the button from the tab sequence; in menu open state: moves to menu |
| `Shift+Tab`      | Moves focus backward |
| `Escape`         | Closes the fallback menu (if open); focus returns to button |
| `Arrow Down`     | Fallback menu open: moves focus to first menu item |
| `Arrow Up`       | Fallback menu open: moves focus to last menu item |

## 13. Accessibility

- Inner `<button>` carries the native button role.
- When the fallback menu is used: `aria-haspopup="menu"` and `aria-expanded`
  (true/false) are set on the button.
- The fallback menu has `role="menu"` with an accessible name from `menu-label`.
- Each menu item has `role="menuitem"`.
- When `icon-only` is set, `aria-label` is set from `label`; absence triggers a
  console warning.
- The share icon is `aria-hidden="true"`.
- `aria-busy="true"` is set during the native share sheet async invocation.
- Minimum target size: 44 × 44 CSS px.

## 14. Form participation

N/A. `<mj-share-button>` is not a form-associated element.

## 15. Internationalization & RTL

- `label`, `menu-label`, and default fallback target labels ("Copy link", "Email")
  are localizable via the shared localization hook.
- RTL: icon and label order mirrors; fallback menu opens from the correct inline end.
- `share-title` and `share-text` are consumer-supplied strings; no locale
  transformation is applied by the component.

## 16. Progressive enhancement / SSR

Server renders `<mj-share-button share-url="https://…" label="Share">Share</mj-share-button>`.
Before upgrade, no share behavior exists. The surrounding page should provide an
alternative (e.g. the URL is displayed as selectable text, or a copy-link anchor is
present). On upgrade, the Web Share API or fallback menu is wired.

## 17. Dependencies

- **Registry + base element helper** (§6)
- **Design-token stylesheet** (§6)
- **Overlay/positioning engine** (§6) — fallback menu positioning
- **Live-region service** (§6) — share success/error announcements
- **Localization hook** (§6) — all user-facing strings
- `<mj-menu>` / `<mj-menu-item>` (§5.1, P1) — fallback share target menu
- `<mj-spinner>` (Progress, P0) — loading state
- `<mj-copy-button>` internals — "Copy link" target reuses the clipboard write logic

## 18. Edge cases & error handling

- User dismisses the native share sheet (AbortError): treated as cancellation, not
  an error; `mj-share-error` is not fired; `loading` is cleared silently.
- `navigator.share` throws for non-AbortError reasons: `mj-share-error` is fired.
- `share-files` provided but `navigator.canShare({ files })` returns false: files are
  dropped; share proceeds with URL only; a console info message is emitted.
- `share-url` is not a valid URL: `navigator.share` will throw; error path taken.
- Fallback menu with no targets: the menu renders with only the "Copy link" default.
- Both `disabled` and `loading` simultaneously: `disabled` takes precedence.

## 19. Acceptance criteria

- [ ] When `navigator.share` is available and `force-menu` is false, clicking invokes the native share sheet.
- [ ] `mj-share` fires on successful native share with correct method and data.
- [ ] `mj-share-error` fires on failure (non-abort); user-dismissed abort is silent.
- [ ] `loading` is true during native share async call; clears on resolve or reject.
- [ ] When `navigator.share` is unavailable or `force-menu` is true, the fallback menu opens.
- [ ] Fallback menu contains "Copy link" target by default.
- [ ] Fallback menu "Copy link" writes `share-url` to clipboard and closes menu.
- [ ] `mj-share-select` fires when a fallback target is selected.
- [ ] `aria-haspopup="menu"` and `aria-expanded` are set in fallback-menu mode.
- [ ] Fallback menu closes on Escape; focus returns to button.
- [ ] `disabled` blocks activation and sets `aria-disabled="true"`.
- [ ] `icon-only` with `label` sets `aria-label`; without `label` emits warning.
- [ ] RTL: fallback menu opens from correct inline side.
- [ ] Minimum target size 44 × 44 CSS px.
- [ ] axe scan zero violations in idle and menu-open states.
- [ ] Light, dark, high-contrast, RTL rendering verified.

## 20. Open questions

- Should default fallback targets (Copy link, Email) be a configurable default list
  via an attribute (JSON array) or only via the `shareTargets` property / slotted
  `<mj-menu-item>` elements?
- Should `<mj-share-button>` detect `navigator.share` availability at registration
  time (static) or at click time (dynamic, allowing polyfills to load later)?
- Confirm whether file sharing (`share-files`) is in scope for P1 or deferred to P2
  given its limited browser support at spec time.
