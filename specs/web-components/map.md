# Map Spec

- **Tag:** `<mj-map>`
- **Class / file:** `MjMap` / `mjmap.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Interactive map
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-map>` embeds an interactive geographic map by wrapping a pluggable provider
adapter (e.g. Leaflet, Mapbox GL, Google Maps). The component owns the accessible
surface — keyboard pan/zoom, accessible marker management, focus management, a
non-map list fallback — while delegating tile rendering and geographic projection
to the adapter. No map engine is bundled in-house.

## 2. When to use / when not to use

**Use** for interactive geographic maps that display locations, routes, or spatial
data alongside accessible alternatives.

**Do not use** for static decorative maps (use a plain `<mj-image>` with
descriptive alt text), for diagrammatic floor plans or network topologies (use
`<mj-diagram>`), or when a simple list of addresses is sufficient.

## 3. Anatomy

- **Container** (`::part(container)`) — outermost element; holds the map target
  and all overlay controls.
- **Map target** (`::part(map-target)`) — the `<div>` passed to the provider
  adapter for map tile rendering.
- **Controls bar** (`::part(controls)`) — overlaid panel with zoom in/out buttons
  and optional additional controls.
- **Zoom in button** (`::part(zoom-in)`) — increments zoom by one level.
- **Zoom out button** (`::part(zoom-out)`) — decrements zoom by one level.
- **Marker list** (`::part(marker-list)`) — visually hidden (or `show-list`-
  visible) `<ul>` of locations as accessible text links that move the map view.
- **Popup** (`::part(popup)`) — anchored info panel shown when a marker is
  selected; built on the overlay engine.
- **Loading** (`::part(loading)`) — spinner or skeleton shown while the adapter
  initializes.
- **Error** (`::part(error)`) — shown when the adapter or tile provider fails.

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Default | — | Interactive map with markers; keyboard pan/zoom |
| Static | `interactive="false"` | Map tiles shown; panning/zooming disabled; still keyboard-navigable markers |
| List visible | `show-list` (boolean) | Marker list rendered visibly below the map as a non-map fallback |
| Satellite | `map-type="satellite"` | Satellite imagery tiles (adapter must support it) |
| Terrain | `map-type="terrain"` | Terrain tile style |
| Road | `map-type="road"` (default) | Standard road map tiles |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `lat` | `number` | `0` | Yes | Initial center latitude |
| `lng` | `number` | `0` | Yes | Initial center longitude |
| `zoom` | `number` | `10` | Yes | Initial zoom level (provider-normalized 0–22) |
| `min-zoom` | `number` | `1` | Yes | Minimum permitted zoom level |
| `max-zoom` | `number` | `20` | Yes | Maximum permitted zoom level |
| `map-type` | `"road"\|"satellite"\|"terrain"` | `"road"` | Yes | Tile style passed to the adapter |
| `interactive` | `boolean` | `true` | Yes | Enables pointer pan/zoom |
| `show-list` | `boolean` | `false` | Yes | Render the marker list visibly |
| `label` | `string` | `""` | Yes | Accessible label for the map region landmark |
| `loading` | `boolean` | `false` | Yes | Shows the loading state |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `adapter` | `MapAdapter` | Pluggable provider; must implement `{ init(target, options): void, destroy(): void, panTo(lat, lng): void, setZoom(level): void, addMarker(marker): MapMarkerHandle, removeMarker(handle): void }` |
| `adapterOptions` | `object` | Provider-specific config passed verbatim to `adapter.init()` |
| `markers` | `MapMarker[]` | Array of `{ id: string, lat: number, lng: number, label: string, description?: string, href?: string }` objects |
| `center` | `{ lat: number, lng: number }` | Read/write; current map center; setting it calls `adapter.panTo()` |
| `currentZoom` | `number` | Read-only; zoom level as reported by the adapter |
| `selectedMarkerId` | `string \| null` | Currently selected marker id; setting it opens the popup for that marker |

## 7. Slots

| Slot | Description |
|------|-------------|
| `popup` | Custom popup content for the selected marker; receives `marker` data via a `detail` property |
| `empty` | Content shown when `markers` array is empty |
| `controls` | Additional control buttons appended to the controls bar |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-map-ready` | `{}` | Yes | No | Fired after the adapter has initialized and the map is interactive |
| `mj-map-move` | `{ lat: number, lng: number, zoom: number }` | Yes | No | Fired after the map pans or zooms (debounced 200ms) |
| `mj-map-marker-select` | `{ marker: MapMarker }` | Yes | No | Fired when a marker is selected (click, Enter, or marker-list link) |
| `mj-map-marker-deselect` | `{}` | Yes | No | Fired when the popup is dismissed |
| `mj-map-zoom-change` | `{ zoom: number }` | Yes | No | Fired after zoom level changes |
| `mj-map-error` | `{ message: string }` | Yes | No | Fired when adapter or tile loading fails |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)`, `::part(map-target)`, `::part(controls)`
- `::part(zoom-in)`, `::part(zoom-out)`, `::part(marker-list)`, `::part(popup)`
- `::part(loading)`, `::part(error)`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-map-height` | `400px` | Default map container height |
| `--mj-map-radius` | `var(--mj-radius-md)` | Corner radius of the container |
| `--mj-map-controls-bg` | `var(--mj-color-surface-1)` | Controls bar background |
| `--mj-map-controls-radius` | `var(--mj-radius-sm)` | Controls bar corner radius |
| `--mj-map-controls-shadow` | `var(--mj-elevation-2)` | Controls bar shadow |
| `--mj-map-popup-bg` | `var(--mj-color-surface-1)` | Popup background |
| `--mj-map-popup-width` | `16rem` | Popup width |
| `--mj-map-focus-ring` | `var(--mj-focus-ring)` | Focus ring style on the map target |

## 10. States

- **loading** — adapter initializing; spinner shown; map target hidden; `aria-busy="true"`.
- **ready** — adapter initialized; map tiles loading or loaded.
- **error** — adapter failed; error state shown; `mj-map-error` fired.
- **marker-selected** — a marker is active; popup is open; marker icon shows
  selected state (shape or label, not color alone).
- **panning** — user is dragging the map; cursor changes to `grabbing`.
- **focused** — the map target has keyboard focus; focus ring visible.

## 11. Behavior & interactions

On `connectedCallback` the component creates the map target div, calls
`adapter.init(target, { lat, lng, zoom, mapType, ...adapterOptions })`, and
attaches a `ResizeObserver` on the container to call the adapter's resize handler.

When the `markers` property is set (or updated), the component reconciles the
displayed markers by calling `adapter.addMarker()` / `adapter.removeMarker()` for
the diff. The marker list (`<ul>`) is rebuilt from the current `markers` array.
Each list item is a link (`<a>` with `href="#"` or the marker's `href`) that, when
activated, calls `adapter.panTo()` and opens the popup.

Keyboard pan: when the map target has focus and an arrow key is pressed, the
component calls `adapter.panTo()` with a step offset proportional to the current
zoom level. `+`/`-` keys adjust zoom.

Popup: when a marker is selected, the popup is shown via the overlay/positioning
engine anchored to the marker's pixel coordinates on the map target. Esc closes
the popup. When a `popup` slot is provided, it is rendered inside the overlay;
otherwise a default title+description layout is used.

Scroll lock: when the map container is focused, scroll-wheel events are captured
by the adapter for zoom. When the map loses focus, scroll-wheel reverts to page
scroll to avoid scroll trapping.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus into the map; first stop is the map target itself |
| `↑` / `↓` / `←` / `→` | Pan the map in the corresponding direction |
| `+` / `=` | Zoom in one level |
| `-` | Zoom out one level |
| `Tab` (within map) | Move focus to the next marker in the marker list (if `show-list` or via invisible marker list) |
| `Enter` / `Space` | Activate focused marker; open popup |
| `Escape` | Close open popup; return focus to the map target |
| `Tab` (within popup) | Navigate interactive elements in the popup |
| `Escape` (in popup) | Close popup; return focus to the marker |

## 13. Accessibility

- The map container is a `<section>` with `role="application"` and `aria-label`
  set to the `label` attribute (required; warns if empty).
- The map target (`<div>`) has `tabindex="0"` and `aria-label="Map"` (localized).
- The marker list is always in the DOM as an accessible fallback; it is visually
  hidden by default (`clip-path: inset(100%)`). Each marker list item is an `<a>`
  element with the marker's `label` as link text and `description` in an
  `aria-describedby` span.
- Markers on the map canvas are represented via the adapter's marker mechanism;
  accessible names come from the `label` field of each `MapMarker` object. The
  adapter contract requires that custom marker elements carry `aria-label` or are
  connected to their list counterpart via `aria-describedby`.
- The popup has `role="dialog"` with `aria-label` equal to the selected marker's
  label; focus moves into the popup on open and returns to the marker's list item
  on close.
- Zoom controls are `<button>` elements with `aria-label="Zoom in"` /
  `"Zoom out"` and `aria-disabled` when at min/max zoom.
- Map state (e.g. "Zoomed to level 12") is announced via a live region on zoom
  change (debounced to avoid excessive announcements).
- Color is never the sole differentiator for marker types; marker shapes or icons
  differentiate categories.

## 14. Form participation

N/A — `<mj-map>` is a display/interaction component with no form value.

## 15. Internationalization & RTL

- The `label` attribute and all UI strings (zoom button labels, live region
  messages, error/empty messages) are overridable via the localization hook (§3.8).
- Geographic coordinate display (lat/lng in popups) uses `Intl.NumberFormat` with
  appropriate fraction digits.
- In RTL documents the controls bar positions to the end edge; the pan direction
  of arrow keys remains geographically consistent (left arrow = west, always).
- Adapter tile labels (place names) follow the tile provider's locale configuration;
  the `locale` adapter option is passed from the document `lang` attribute.

## 16. Progressive enhancement / SSR

The server renders the marker list as a visible `<ul>` inside `<mj-map>`. Without
scripting the list of locations is immediately usable. On upgrade the component
promotes the list into its shadow DOM structure, hides it (unless `show-list` is
set), and initializes the adapter. No re-rendering of the list is needed.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection.
- **Design-token stylesheet** (§6) — all visual values.
- **Overlay/positioning engine** (§6) — popup positioning anchored to marker coordinates.
- **Focus utilities** (§6) — popup focus trap and restore.
- **Live-region service** (§6) — zoom and pan announcements.
- **Localization hook** (§6) — all user-facing strings.
- **Pluggable map provider adapter** — supplied by the host application; not bundled.

## 18. Edge cases & error handling

- `adapter` not set: renders the marker list only; logs a console error.
- Tile provider unavailable (network): adapter reports an error; `mj-map-error`
  fired; error state shown; marker list remains functional.
- `markers` is an empty array: empty slot shown; map still pans/zooms.
- Marker coordinates outside the adapter's supported bounds: adapter handles the
  clamp; the component passes coordinates verbatim.
- `zoom` clamped to `[min-zoom, max-zoom]`: silently clamped; `mj-map-zoom-change`
  fires with the clamped value.
- Map container resized to zero: `ResizeObserver` skips adapter resize call; resumes
  on next non-zero observation.
- Popup open when markers array is updated and the selected marker is removed:
  popup is closed; `mj-map-marker-deselect` fires.

## 19. Acceptance criteria

- [ ] Adapter `init()` is called with `lat`/`lng`/`zoom` on `connectedCallback`.
- [ ] `markers` property change adds/removes markers via the adapter diff.
- [ ] Marker list is in the DOM and accessible regardless of `show-list`.
- [ ] Clicking/activating a marker opens the popup with the marker's label.
- [ ] Arrow keys pan the map; `+`/`-` keys change zoom.
- [ ] Popup receives focus on open; Esc closes it and restores focus.
- [ ] Zoom buttons have correct `aria-disabled` at min/max zoom.
- [ ] Zoom change is announced via live region (debounced).
- [ ] No-adapter fallback renders marker list with a console error.
- [ ] `show-list` renders the marker list visibly.
- [ ] RTL layout positions controls on the end edge without JS changes.
- [ ] Tile error fires `mj-map-error` and shows the error state.
- [ ] Automated accessibility checks pass with no violations.

## 20. Open questions

- Should `<mj-map>` expose a `bounds` property (NE/SW corner) so hosts can
  constrain the viewport to a region?
- Should clustered markers be a first-class concept in the `MapMarker` model, or
  entirely delegated to the adapter?
- Should the popup slot receive marker data via a named event rather than a
  DOM property so it works in framework-rendered slots?
