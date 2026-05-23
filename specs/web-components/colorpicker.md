# Color Picker Spec

- **Tag:** `<mj-color-picker>`
- **Class / file:** `MjColorPicker` / `mjcolorpicker.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Color chooser, Color selector
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-color-picker>` enhances `<input type="color">` with a rich chooser surface that includes a saturation/brightness gradient canvas, a hue slider, an optional alpha slider, hex/rgb/hsl text inputs, a swatch palette, and an optional eyedropper. It maintains a single color value and exposes it in multiple formats via properties.

## 2. When to use / when not to use
**Use** when the user needs to select a precise color for branding, theming, design, or configuration purposes. **Use the swatch-only variant** when choice is limited to a predefined palette. **Do not use** for categorical choices that happen to have colors — use `<mj-select>` or `<mj-radio-group>`. **Do not use** when the color will never be user-customized — hard-code the token value.

## 3. Anatomy
- **Trigger** (`part="trigger"`) — colored swatch button that opens the picker popup.
- **Popup** (`part="popup"`) — positioned overlay containing the full picker surface.
- **Gradient canvas** (`part="canvas"`) — 2D saturation/brightness color field.
- **Canvas thumb** (`part="canvas-thumb"`) — draggable cursor on the gradient canvas.
- **Hue slider** (`part="hue-slider"`) — horizontal rainbow track (`role="slider"`).
- **Hue thumb** (`part="hue-thumb"`) — draggable handle on the hue slider.
- **Alpha slider** (`part="alpha-slider"`) — optional transparency track (`role="slider"`).
- **Alpha thumb** (`part="alpha-thumb"`) — draggable handle on the alpha slider.
- **Format inputs** (`part="format-inputs"`) — hex, RGB, or HSL text fields.
- **Format switcher** (`part="format-switcher"`) — cycles between input formats.
- **Swatch grid** (`part="swatch-grid"`) — predefined color palette.
- **Swatch** (`part="swatch"`) — individual color swatch button.
- **Eyedropper button** (`part="eyedropper"`) — invokes the EyeDropper API.
- **Preview** (`part="preview"`) — side-by-side current vs. new color preview.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Full picker | (default) | Canvas + sliders + inputs + swatches |
| Swatch-only | `swatches-only` (boolean) | Only swatch palette shown; no canvas/sliders |
| No alpha | `no-alpha` (boolean) | Alpha slider hidden; values always fully opaque |
| Inline | `inline` (boolean) | Picker surface rendered inline; no popup trigger |
| Hex input only | `format="hex"` | Only hex text field shown in format inputs |
| RGB input | `format="rgb"` | RGB numeric fields |
| HSL input | `format="hsl"` | HSL numeric fields |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name |
| `value` | string | `"#000000"` | Yes | Current color as a CSS color string (hex by default) |
| `format` | `"hex"` \| `"rgb"` \| `"hsl"` | `"hex"` | Yes | Format of the `value` attribute and primary text input |
| `swatches` | string | `""` | Yes | JSON array of CSS color strings for the swatch palette |
| `swatches-only` | boolean | `false` | Yes | Restricts the picker to the swatch palette |
| `no-alpha` | boolean | `false` | Yes | Hides the alpha slider; forces full opacity |
| `inline` | boolean | `false` | Yes | Renders picker inline instead of in a popup |
| `disabled` | boolean | `false` | Yes | Disables the control |
| `readonly` | boolean | `false` | Yes | Value cannot be changed; submitted as-is |
| `required` | boolean | `false` | Yes | Field required (value must not be empty) |
| `open` | boolean | `false` | Yes | Opens/closes the popup programmatically |
| `eyedropper` | boolean | `false` | Yes | Shows eyedropper button (only if EyeDropper API available) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `color` | `{ h: number, s: number, l: number, a: number }` | Current color as HSL + alpha object |
| `hexValue` | `string` | Current color as `#rrggbb` or `#rrggbbaa` |
| `rgbValue` | `string` | Current color as `rgb(r, g, b)` or `rgba(r, g, b, a)` |
| `hslValue` | `string` | Current color as `hsl(h, s%, l%)` or `hsla(...)` |
| `swatchList` | `string[]` | Parsed array of swatch color strings |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| `swatches` | Custom swatch elements (alternative to the `swatches` attribute) |
| `trigger` | Custom trigger element instead of the default color swatch button |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, color: HSLAObject }` | Yes | No | Fired when the committed color changes (on mouse-up, Enter, or swatch click) |
| `mj-input` | `{ value: string, color: HSLAObject }` | Yes | No | Fired continuously while dragging sliders or canvas |
| `mj-open` | `{}` | Yes | Yes | Fired before popup opens |
| `mj-close` | `{}` | Yes | No | Fired after popup closes |

## 9. CSS parts & custom properties
**Parts:** `trigger`, `popup`, `canvas`, `canvas-thumb`, `hue-slider`, `hue-thumb`, `alpha-slider`, `alpha-thumb`, `format-inputs`, `format-switcher`, `swatch-grid`, `swatch`, `eyedropper`, `preview`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-color-picker-popup-width` | `16rem` | Width of the picker popup |
| `--mj-color-picker-canvas-height` | `10rem` | Height of the gradient canvas |
| `--mj-color-picker-swatch-size` | `1.5rem` | Width and height of each swatch |
| `--mj-color-picker-swatch-gap` | `--mj-space-1` | Gap between swatches |
| `--mj-color-picker-slider-height` | `0.75rem` | Height of hue/alpha slider tracks |
| `--mj-color-picker-thumb-size` | `1rem` | Diameter of all slider/canvas thumbs |
| `--mj-color-picker-border-radius` | `--mj-radius-md` | Popup and canvas corner radius |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default (closed) | Trigger shows current color | — |
| Open | Popup visible; canvas and sliders active | `aria-expanded="true"` on trigger |
| Dragging canvas | Thumb moves; `mj-input` fires continuously | `aria-valuenow` on canvas slider |
| Dragging hue | Hue changes | `aria-valuenow` on hue slider |
| Dragging alpha | Alpha changes | `aria-valuenow` on alpha slider |
| Focused swatch | Swatch has focus ring | `aria-selected="true"` if it matches current value |
| Eyedropper active | Browser overlay active | — |
| Disabled | Trigger muted; no pointer events | `aria-disabled="true"` |
| Invalid | Error border on trigger | `aria-invalid="true"` |

## 11. Behavior & interactions
- The gradient canvas is a 2D drag surface. The X axis represents saturation (0–100%); the Y axis represents brightness (0–100% inverted). Dragging fires `mj-input`; releasing fires `mj-change`.
- The hue slider adjusts the hue component (0–360°). The alpha slider adjusts opacity (0–1).
- Text input fields accept and parse hex, rgb(), or hsl() strings; on Enter or blur the value is committed via `mj-change`.
- Swatches are a grid of `<button>` elements. Clicking a swatch immediately commits the color.
- The eyedropper button invokes `window.EyeDropper`; if the API is unavailable the button is hidden regardless of the `eyedropper` attribute.
- Popup is closed by clicking outside (light-dismiss), pressing Escape, or activating the trigger again.
- Canvas and slider thumb positions are recalculated when the popup opens to reflect the current value.

## 12. Keyboard interaction
| Key | Focus on | Action |
|-----|----------|--------|
| `Enter` / `Space` | Trigger | Open / close popup |
| `Escape` | Popup open | Close popup; revert to value before open |
| `ArrowRight` / `ArrowLeft` | Hue slider | Increase / decrease hue by 1° |
| `ArrowRight` / `ArrowLeft` | Alpha slider | Increase / decrease alpha by 1% |
| `ArrowRight` / `ArrowUp` | Canvas thumb | Increase saturation / brightness by 1% |
| `ArrowLeft` / `ArrowDown` | Canvas thumb | Decrease saturation / brightness by 1% |
| `Tab` | Popup | Cycle: canvas → hue slider → alpha slider → hex input → format switcher → swatches → eyedropper |
| `Enter` | Swatch | Apply swatch color |
| `Enter` / `Space` | Eyedropper | Launch eyedropper |
| `ArrowRight` / `ArrowLeft` / `ArrowDown` / `ArrowUp` | Swatch grid | Move focus within grid |

## 13. Accessibility
- Trigger `<button>` has `aria-label` describing the current color (e.g., "Color picker, current color: #ff0000") and `aria-haspopup="dialog"`.
- Gradient canvas is a `role="slider"` region with two virtual sliders (saturation and brightness) exposed via `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext`.
- Hue slider: `role="slider"`, `aria-label="Hue"`, `aria-valuenow` (0–360), `aria-valuetext` (e.g., "120 degrees").
- Alpha slider: `role="slider"`, `aria-label="Opacity"`, `aria-valuenow` (0–100), `aria-valuetext` (e.g., "80%").
- Swatch grid: `role="grid"` or `role="listbox"` with each swatch as `role="gridcell"` or `role="option"`; `aria-selected="true"` on the matching swatch; `aria-label` is the CSS color string or author-supplied name.
- Format inputs: standard `<input type="text">` with visible `<label>`.
- Color changes are announced via a polite live region: "Color updated: #ff0000".
- Minimum target size for all interactive elements: 44 × 44 px on touch; 24 × 24 px on desktop per WCAG 2.2 2.5.8.

## 14. Form participation
- Form-associated via `ElementInternals`; contributes `name=value` where `value` is in the format specified by the `format` attribute.
- `required`: `validity.valueMissing` if `value` is empty (no color selected).
- On form reset, reverts to the initial `value` attribute.

## 15. Internationalization & RTL
- In RTL, the popup layout mirrors horizontally; slider thumbs start from the right.
- `aria-valuetext` for hue uses "degrees" — this string should be overridable via a localization hook.
- Opacity percentage label localizable via the `l10n` hook.
- Swatch `aria-label` values are author-supplied; no built-in English names for colors.

## 16. Progressive enhancement / SSR
- Server renders `<input type="color" name="..." value="...">` inside `<mj-color-picker>`.
- Before upgrade, the native color input is functional (browser-native UI).
- On upgrade, the native input is hidden and kept in sync for form submission.
- Without scripting, the native `<input type="color">` renders and is functional.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities, form-association helper, live-region service.
- EyeDropper API (platform, optional; gracefully omitted when unavailable).

## 18. Edge cases & error handling
- Invalid hex string in text input: field shows error styling; previous valid value retained; `mj-change` not fired.
- Alpha slider shown with `no-alpha` set: alpha slider is hidden; alpha component of any input color is stripped to 1.
- No swatches provided and `swatches-only` set: picker shows an empty palette; a console warning is logged.
- `value` attribute contains an unparseable CSS color: component falls back to `#000000`; console warning logged.
- Popup taller than viewport: canvas height is reduced; minimum canvas height is `4rem`.
- EyeDropper API unavailable: button hidden silently (no error logged).

## 19. Acceptance criteria
- [ ] Dragging the canvas thumb fires `mj-input`; releasing fires `mj-change` with updated color.
- [ ] Hue and alpha sliders update color in real time; `aria-valuenow` matches current value.
- [ ] Hex text input accepts valid hex strings and commits on Enter/blur.
- [ ] Clicking a swatch commits that color and closes popup (non-inline mode).
- [ ] Eyedropper button hidden when `EyeDropper` API is unavailable.
- [ ] Form submission includes `name=value` in the configured format.
- [ ] Trigger accessible name reflects the current color.
- [ ] Keyboard navigation covers all interactive elements within the popup via Tab.
- [ ] axe-core reports zero violations in open, swatch-only, and disabled states.
- [ ] RTL layout mirrors picker surface correctly.

## 20. Open questions
- Should `mj-change` fire when the popup is closed (commit on close) or immediately on each interaction within the popup?
- Should the component support named swatch labels (author-supplied) rendered as tooltips on swatch hover/focus?
- Should a "recent colors" section be built-in (stored in `localStorage`), or is that deferred to an author-supplied swatch list?
