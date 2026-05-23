# Avatar Spec

- **Tag:** `<mj-avatar>`
- **Class / file:** `MjAvatar` / `mjavatar.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** User avatar, Entity avatar
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-avatar>` displays a visual identity for a user or entity using a priority
chain: photo image → initials derived from the `name` attribute → a generic
person icon. An optional `<mj-badge>` presence indicator can be layered onto the
corner of the avatar. The component is sized by a `size` attribute and themed
entirely via design tokens.

## 2. When to use / when not to use

**Use** for representing a person or entity in lists, comments, profile headers,
and navigation items.

**Do not use** for general images (use `<mj-image>` instead), for brand logos
(use `<mj-image>` with `alt` set to the brand name), or when the only content
needed is an icon without the identity metaphor (use a standalone icon element).

## 3. Anatomy

- **Container** (`::part(container)`) — circular or rounded-square frame that
  clips content and holds the fallback background color.
- **Img** (`::part(img)`) — native `<img>` shown when `src` resolves successfully.
- **Initials** (`::part(initials)`) — `<span>` with computed initials text,
  shown when image is absent or fails.
- **Icon** (`::part(icon)`) — generic person SVG icon, shown when neither image
  nor name/initials are available.
- **Presence** (`::part(presence)`) — small colored dot badge anchored to the
  bottom-end corner; powered internally by `<mj-badge variant="dot">`.
- **Image slot** — allows a host to supply a custom `<img>` or `<picture>` element.

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Photo | `src` present and loads | Shows image; hides initials and icon |
| Initials | `src` absent/failed, `name` present | Derives initials; shows colored background |
| Icon | Neither `src` nor `name` | Renders generic person icon |
| Circular | `shape="circle"` (default) | `border-radius: 50%` |
| Rounded square | `shape="square"` | `border-radius: var(--mj-radius-md)` |
| XS–XL sizes | `size="xs"\|"sm"\|"md"\|"lg"\|"xl"` | Maps to token-defined dimensions |
| With presence | `presence="online"\|"away"\|"busy"\|"offline"` | Shows presence dot |
| Stacked group | Parent `<mj-avatar-group>` | Overlapping row (handled by parent) |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | `string` | `""` | Yes | URL of the avatar photo |
| `name` | `string` | `""` | Yes | Full name used for initials derivation and accessible label |
| `initials` | `string` | `""` | Yes | Override computed initials (max 2 characters rendered) |
| `size` | `"xs"\|"sm"\|"md"\|"lg"\|"xl"` | `"md"` | Yes | Avatar diameter via design tokens |
| `shape` | `"circle"\|"square"` | `"circle"` | Yes | Corner radius treatment |
| `presence` | `"online"\|"away"\|"busy"\|"offline"\|""` | `""` | Yes | Presence state; empty hides the indicator |
| `color` | `string` | `""` | Yes | Explicit background color for initials/icon state (CSS color or token); if empty, derived from `name` hash |
| `crossorigin` | `"anonymous"\|"use-credentials"` | `""` | Yes | Forwarded to the inner `<img>` |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `computedInitials` | `string` | Read-only; the 1–2 character string actually rendered |
| `imageLoaded` | `boolean` | `true` when the `<img>` has completed loading without error |
| `resolvedColor` | `string` | The background color in use (either `color` attribute or hash-derived) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Custom `<img>` or `<picture>` element used instead of the `src`-driven image |
| `icon` | Custom icon SVG/element to replace the generic person fallback |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-avatar-image-load` | `{ src: string }` | Yes | No | Fired when the photo image loads successfully |
| `mj-avatar-image-error` | `{ src: string }` | Yes | No | Fired when the photo fails; component falls back to initials/icon |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)` — outer circular/square frame
- `::part(img)` — photo `<img>`
- `::part(initials)` — initials text span
- `::part(icon)` — fallback icon wrapper
- `::part(presence)` — presence indicator dot

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-avatar-size` | (set by `size` token) | Explicit override for diameter |
| `--mj-avatar-font-size` | `calc(var(--mj-avatar-size) * 0.4)` | Initials font size |
| `--mj-avatar-border-width` | `0px` | Optional ring border width |
| `--mj-avatar-border-color` | `var(--mj-color-border)` | Ring border color |
| `--mj-avatar-bg` | (derived from name hash or `color` attr) | Background color for initials/icon state |
| `--mj-avatar-fg` | `var(--mj-color-text-on-filled)` | Text/icon color over background |
| `--mj-avatar-presence-size` | `calc(var(--mj-avatar-size) * 0.28)` | Presence dot diameter |
| `--mj-avatar-presence-border` | `2px solid var(--mj-color-surface-1)` | Ring that separates dot from avatar |

## 10. States

- **loading** — `src` is set but not yet resolved; shows initials/icon placeholder in the interim.
- **image-loaded** — photo displayed; initials/icon hidden.
- **image-error** — photo failed; falls back permanently to initials or icon for this `src` value.
- **initials** — no image available; background color + text shown.
- **icon** — neither image nor name available; generic icon shown.
- **presence-online** — green dot visible; text alternative "Online".
- **presence-away** — yellow dot; text alternative "Away".
- **presence-busy** — red dot; text alternative "Busy".
- **presence-offline** — grey dot; text alternative "Offline".

## 11. Behavior & interactions

When `src` is set, the component creates an off-DOM `Image` object to test
loading. On success, it shows the `<img>` inside shadow DOM. On failure it
silently falls back without throwing.

Initials are derived by splitting `name` on whitespace, taking the first
character of the first and last words, and uppercasing them. A `name` of a single
word yields one character. If `initials` is explicitly set it overrides this
derivation (capped at two characters for display).

The background color for the initials/icon state is deterministically derived by
hashing `name` (or `initials`) into one of a palette of token-defined accessible
colors so the same name always renders the same color. The `color` attribute
overrides this entirely.

The presence dot is positioned absolutely at `bottom: 0; inset-inline-end: 0` and
carries a white ring border so it floats cleanly over any background.

The avatar is not interactive by default. When placed inside an `<a>` or a
`<button>` by the host, the interactive element provides the required keyboard and
ARIA behavior.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| None | Avatar is a display component; no keyboard behavior unless wrapped in an interactive element by the host |

## 13. Accessibility

- The component renders with `role="img"` and `aria-label` set to the `name`
  attribute value (e.g. "Ada Lovelace"). When `name` is empty and only an icon
  is shown, `aria-label` is set to the localized string "Unknown user".
- The presence dot renders with `aria-label` set to the localized presence string
  (e.g. "Online") and `role="img"` so screen readers announce it separately.
- The inner `<img>` carries `alt=""` (decorative) because the outer `role="img"` +
  `aria-label` provides the accessible description for the entire component.
- Background color for initials is chosen from a pre-validated set that meets
  WCAG 4.5:1 contrast against `--mj-avatar-fg`.
- Presence state is never conveyed by color alone: the `aria-label` of the dot
  always provides the text equivalent.

## 14. Form participation

N/A — `<mj-avatar>` is a display component with no form value.

## 15. Internationalization & RTL

- Initials derivation applies Unicode-aware character handling; works with CJK
  names (single character extracted from a CJK name).
- `aria-label` strings ("Unknown user", presence labels) are overridable via the
  localization hook (§3.8).
- In RTL layouts the presence dot moves to the bottom-start corner via logical
  `inset-inline-end` property; no JS changes required.

## 16. Progressive enhancement / SSR

The server may render `<mj-avatar name="Ada Lovelace"><img src="..." alt=""></mj-avatar>`.
Before the script loads the slotted `<img>` is displayed as a raw image element.
On upgrade the component moves to its shadow-DOM rendering; if the slotted image
is reused, no additional network request is made.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection.
- **Design-token stylesheet** (§6) — avatar palette and size tokens.
- **`<mj-badge>`** — presence dot (Badge `variant="dot"` + `status` attribute).

## 18. Edge cases & error handling

- `name` is a single emoji character: initials renders the emoji; background color
  hash operates on the code-point string.
- Both `src` and a slotted `<img>` are provided: slotted `<img>` takes priority;
  `src` is ignored with a console warning.
- `initials` exceeds two characters: only the first two are shown; the full value
  is preserved in the attribute for aria-label fallback.
- `color` attribute is an invalid CSS color: component falls back to hash-derived
  color and logs a warning.
- `size` token not defined in the current theme: component falls back to `2rem`.

## 19. Acceptance criteria

- [ ] Photo renders when `src` resolves; falls back to initials on error.
- [ ] Initials are derived correctly from multi-word names and single-word names.
- [ ] `initials` attribute overrides computed initials (max 2 chars rendered).
- [ ] Color is deterministically derived from `name`; `color` attribute overrides it.
- [ ] All five `size` values map to distinct token-driven dimensions.
- [ ] `shape="square"` applies rounded-square border-radius.
- [ ] Presence dot renders correct color and `aria-label` for each state.
- [ ] `role="img"` and `aria-label` are present; screen reader announces correctly.
- [ ] Presence is not conveyed by color alone (aria-label present on dot).
- [ ] Initials background colors meet 4.5:1 contrast against foreground token.
- [ ] Server-rendered slotted `<img>` is preserved on upgrade.
- [ ] Automated accessibility checks pass with no violations.

## 20. Open questions

- Should `<mj-avatar-group>` (stacked row of avatars with overflow "+N" pill) be
  a separate spec or a section 4 variant of this component?
- Should the initials color palette be a closed token set or configurable via a
  CSS custom property list?
