/*
 * mjavatar.js
 *
 * <mj-avatar> -- user/entity avatar with photo → initials → icon fallback chain,
 * optional presence indicator, multiple sizes, and deterministic background color
 * derived from the name.
 *
 * Structure: `.frame` is the sizing box. Inside it `.container` (role="img",
 * named after the person) clips the photo and the fallback, and the presence
 * dot is its SIBLING -- a child of a role="img" element is presentational,
 * so the dot has to sit outside it for its text alternative to be reachable
 * (and outside the clipping circle to be fully visible).
 *
 * Sizing and colour are resolved in CSS so the documented custom properties
 * keep working from the host:
 *   --mj-avatar-size    overrides the `size` attribute
 *   --mj-avatar-bg      overrides the name-derived background
 *   --mj-avatar-color-1 ... --mj-avatar-color-8   the name-hash palette
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";

/*
 * Default name-hash palette. Every entry has a contrast ratio of at least
 * 4.5:1 against the white initials (--mj-avatar-fg default). The same values
 * are the fallbacks of --mj-avatar-color-N in the stylesheet below; they are
 * never used as bare colours. They are fixed rather than theme tokens on
 * purpose: identity colours must not change with the theme, and the theme's
 * status colours turn light in the dark palette, which would fail the
 * contrast with white initials. `resolvedColor` reports these defaults.
 */
const AVATAR_COLORS = [
  "#2563eb", "#7c3aed", "#be185d", "#b91c1c",
  "#b45309", "#047857", "#0e7490", "#4f46e5"
];

const PRESENCE_STATES = ["online", "away", "busy", "offline"];

/* Keys of the presence names and the nameless-avatar label, resolved through t() at use time. */
const PRESENCE_LABEL_KEYS = {
  online: "mj.avatar.presence.online",
  away: "mj.avatar.presence.away",
  busy: "mj.avatar.presence.busy",
  offline: "mj.avatar.presence.offline"
};

const UNKNOWN_USER_LABEL_KEY = "mj.avatar.unknownUser";

function buildPaletteRules() {
  const rules = []
  for (let index = 0; index < AVATAR_COLORS.length; index = index + 1) {
    const slot = index + 1
    rules.push(
      `.container[data-palette="${slot}"] { --_hash-bg: var(--mj-avatar-color-${slot}, ${AVATAR_COLORS[index]}); }`
    )
  }
  const css = rules.join("\n")
  return css
}

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
  --_size: 2.25rem;
}
:host([size="xs"]) { --_size: 1.25rem; }
:host([size="sm"]) { --_size: 1.75rem; }
:host([size="md"]) { --_size: 2.25rem; }
:host([size="lg"]) { --_size: 3rem; }
:host([size="xl"]) { --_size: 4rem; }

.frame {
  --_resolved-size: var(--mj-avatar-size, var(--_size));
  position: relative;
  display: inline-flex;
  inline-size: var(--_resolved-size);
  block-size: var(--_resolved-size);
  flex-shrink: 0;
}

.container {
  --_hash-bg: var(--mj-avatar-color-1, ${AVATAR_COLORS[0]});
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  inline-size: 100%;
  block-size: 100%;
  border-radius: 50%;
  background: var(--_explicit-bg, var(--mj-avatar-bg, var(--_hash-bg)));
  border: var(--mj-avatar-border-width, 0px) solid var(--mj-avatar-border-color, var(--mj-border));
  overflow: hidden;
}
:host([shape="square"]) .container {
  border-radius: var(--mj-radius-md);
}
${buildPaletteRules()}

.img {
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
  display: none;
}
.img.visible { display: block; }

::slotted(img),
::slotted(picture) {
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
  display: block;
}
slot.custom-image { display: none; }
.container.has-custom slot.custom-image { display: contents; }
.container.has-custom .img,
.container.has-custom .initials,
.container.has-custom .icon { display: none; }

.initials {
  font-size: var(--mj-avatar-font-size, calc(var(--_resolved-size) * 0.4));
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-avatar-fg, #ffffff);
  line-height: 1;
  user-select: none;
  display: none;
}
.initials.visible { display: block; }

.icon {
  color: var(--mj-avatar-fg, #ffffff);
  inline-size: 60%;
  block-size: 60%;
  display: none;
}
.icon.visible { display: flex; align-items: center; justify-content: center; }
.icon ::slotted(*) { inline-size: 100%; block-size: 100%; }

.presence {
  position: absolute;
  inset-block-end: 0;
  inset-inline-end: 0;
  box-sizing: border-box;
  inline-size: var(--mj-avatar-presence-size, calc(var(--_resolved-size) * 0.28));
  block-size: var(--mj-avatar-presence-size, calc(var(--_resolved-size) * 0.28));
  border-radius: 50%;
  border: var(--mj-avatar-presence-border, 2px solid var(--mj-surface));
  background: var(--mj-avatar-presence-offline, var(--mj-text-muted));
  display: none;
}
.presence.visible { display: block; }
.presence[data-state="online"] { background: var(--mj-avatar-presence-online, var(--mj-color-success)); }
.presence[data-state="away"] { background: var(--mj-avatar-presence-away, var(--mj-color-warning)); }
.presence[data-state="busy"] { background: var(--mj-avatar-presence-busy, var(--mj-color-danger)); }
`;

export class MjAvatar extends MjElement {
  static tagName = "mj-avatar";
  static styles = STYLES;
  static watched = ["src", "name", "initials", "size", "shape", "presence", "color", "crossorigin"];

  constructor() {
    super()
    this._imgEl = null
    this._initialsEl = null
    this._iconEl = null
    this._presenceEl = null
    this._containerEl = null
    this._customSlot = null

    /* The src / crossorigin pair last handed to the inner <img>. */
    this._appliedSrc = null
    this._appliedCrossorigin = null

    /* True once the inner <img> has fired `load` for the applied src. */
    this._imageShown = false

    /* The last invalid `color` value that was reported, so it is logged once. */
    this._warnedColor = null
  }

  render() {
    const markup = `
      <div class="frame" part="frame">
        <div class="container" part="container" role="img">
          <img class="img" part="img" alt="" />
          <slot class="custom-image"></slot>
          <span class="initials" part="initials" aria-hidden="true"></span>
          <span class="icon" part="icon" aria-hidden="true">
            <slot name="icon">
              <svg viewBox="0 0 24 24" fill="currentColor" width="100%" height="100%" aria-hidden="true">
                <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
              </svg>
            </slot>
          </span>
        </div>
        <div class="presence" part="presence" role="img"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._containerEl = this.$(".container")
    this._imgEl = this.$(".img")
    this._initialsEl = this.$(".initials")
    this._iconEl = this.$(".icon")
    this._presenceEl = this.$(".presence")
    this._customSlot = this.$("slot.custom-image")

    this._appliedSrc = null
    this._appliedCrossorigin = null
    this._imageShown = false

    this.listen(this._imgEl, "load", this._onImgLoad.bind(this))
    this.listen(this._imgEl, "error", this._onImgError.bind(this))
    this.listen(this._customSlot, "slotchange", () => { this._syncCustomImage() })

    this._syncCustomImage()
    this._sync()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._containerEl === null || this._containerEl === undefined) {
      return
    }
    this._sync()
    return
  }

  /*
   * Bring the shadow DOM in line with the attributes. Every step is
   * idempotent; in particular the image is only (re)loaded when `src` or
   * `crossorigin` differ from what the inner <img> already has, so a presence
   * or size update never restarts the photo download.
   */
  _sync() {
    this._applyColor()
    this._loadImage()
    this._applyFallback()
    this._applyPresence()
    this._applyAriaLabel()
    return
  }

  /* A slotted <img>/<picture> replaces the src-driven photo and the fallback. */
  _syncCustomImage() {
    const assigned = this._customSlot.assignedElements({ flatten: true })
    const hasCustom = assigned.length > 0
    this._containerEl.classList.toggle("has-custom", hasCustom)

    if (hasCustom === true && this.hasAttribute("src") === true) {
      console.warn("<mj-avatar>: both `src` and a slotted image are set; the slotted image is used.")
    }
    return
  }

  _loadImage() {
    const src = this.getAttribute("src") || ""
    const crossorigin = this.getAttribute("crossorigin")

    const unchanged = src === (this._appliedSrc || "") && crossorigin === this._appliedCrossorigin
    if (unchanged === true) {
      return
    }

    this._appliedSrc = src
    this._appliedCrossorigin = crossorigin

    /* The fallback shows until the new photo has loaded. */
    this._imageShown = false
    this._imgEl.classList.remove("visible")

    if (crossorigin !== null) {
      this._imgEl.setAttribute("crossorigin", crossorigin)
    } else {
      this._imgEl.removeAttribute("crossorigin")
    }

    if (src.length === 0) {
      this._imgEl.removeAttribute("src")
    } else {
      this._imgEl.setAttribute("src", src)
    }
    return
  }

  _onImgLoad() {
    this._imageShown = true
    this._imgEl.classList.add("visible")
    this._applyFallback()
    this.emit("mj-avatar-image-load", { src: this._imgEl.src })
    return
  }

  _onImgError() {
    this._imageShown = false
    this._imgEl.classList.remove("visible")
    this._applyFallback()
    this.emit("mj-avatar-image-error", { src: this.getAttribute("src") || "" })
    return
  }

  /*
   * Show initials (or the icon when there is no name) whenever no photo is
   * on screen: no src, still loading, or failed.
   */
  _applyFallback() {
    const computed = this.computedInitials
    this._initialsEl.textContent = computed

    const showFallback = this._imageShown === false
    const showInitials = showFallback === true && computed.length > 0
    const showIcon = showFallback === true && computed.length === 0

    this._initialsEl.classList.toggle("visible", showInitials)
    this._iconEl.classList.toggle("visible", showIcon)
    return
  }

  /*
   * Background colour. The name hash selects one of the palette custom
   * properties through `data-palette`; an explicit, valid `color` attribute
   * is written to a private variable that wins over both the palette and
   * the host-level --mj-avatar-bg.
   */
  _applyColor() {
    const paletteIndex = this._paletteIndex()
    this._containerEl.setAttribute("data-palette", String(paletteIndex + 1))

    const explicit = this._explicitColor()
    if (explicit.length > 0) {
      this._containerEl.style.setProperty("--_explicit-bg", explicit)
    } else {
      this._containerEl.style.removeProperty("--_explicit-bg")
    }
    return
  }

  /* The `color` attribute when it is a colour the browser accepts, else "". */
  _explicitColor() {
    const explicit = (this.getAttribute("color") || "").trim()
    let color = ""

    if (explicit.length > 0) {
      const supported = typeof CSS !== "undefined" && typeof CSS.supports === "function"
        ? CSS.supports("color", explicit)
        : true
      if (supported === true) {
        color = explicit
      } else if (this._warnedColor !== explicit) {
        console.warn(`<mj-avatar>: color "${explicit}" is not a valid CSS color; using the name-derived color.`)
        this._warnedColor = explicit
      }
    }

    return color
  }

  _paletteIndex() {
    const name = this.getAttribute("name") || this.getAttribute("initials") || ""
    let index = 0

    if (name.length > 0) {
      let hash = 0
      for (let i = 0; i < name.length; i = i + 1) {
        hash = (hash * 31 + name.charCodeAt(i)) >>> 0
      }
      index = hash % AVATAR_COLORS.length
    }

    return index
  }

  _resolveColor() {
    const explicit = this._explicitColor()
    const color = explicit.length > 0 ? explicit : AVATAR_COLORS[this._paletteIndex()]
    return color
  }

  _applyPresence() {
    const presence = this.getAttribute("presence") || ""
    if (presence.length === 0) {
      this._presenceEl.classList.remove("visible")
      this._presenceEl.removeAttribute("aria-label")
      this._presenceEl.removeAttribute("data-state")
      return
    }

    const state = PRESENCE_STATES.indexOf(presence) >= 0 ? presence : "offline"
    this._presenceEl.setAttribute("data-state", state)
    this._presenceEl.setAttribute("aria-label", this._presenceLabel(presence))
    this._presenceEl.classList.add("visible")
    return
  }

  _presenceLabel(presence) {
    let label = presence
    if (Object.prototype.hasOwnProperty.call(PRESENCE_LABEL_KEYS, presence) === true) {
      label = t(PRESENCE_LABEL_KEYS[presence])
    }
    return label
  }

  _applyAriaLabel() {
    const name = this.getAttribute("name") || ""
    const label = name.length > 0 ? name : t(UNKNOWN_USER_LABEL_KEY)
    this._containerEl.setAttribute("aria-label", label)
    return
  }

  /* ----- scriptable API ----- */

  get computedInitials() {
    const explicit = this.getAttribute("initials") || ""
    if (explicit.length > 0) {
      const capped = [...explicit].slice(0, 2).join("")
      return capped
    }
    const name = (this.getAttribute("name") || "").trim()
    if (name.length === 0) {
      return ""
    }
    const parts = name.split(/\s+/)
    if (parts.length === 1) {
      const firstChar = [...parts[0]][0] || ""
      return firstChar.toUpperCase()
    }
    const first = [...parts[0]][0] || ""
    const last = [...parts[parts.length - 1]][0] || ""
    const initials = (first + last).toUpperCase()
    return initials
  }

  get imageLoaded() {
    const value = this._imgEl !== null && this._imgEl.complete === true && this._imgEl.naturalWidth > 0
    return value
  }

  /*
   * The explicit `color` attribute, or the default palette entry the name
   * hashes to. A host that overrides --mj-avatar-bg or --mj-avatar-color-N
   * changes what is painted without changing this value.
   */
  get resolvedColor() {
    const color = this._resolveColor()
    return color
  }
}
