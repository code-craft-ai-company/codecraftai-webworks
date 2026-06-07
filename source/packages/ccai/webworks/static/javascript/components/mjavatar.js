/*
 * mjavatar.js
 *
 * <mj-avatar> -- user/entity avatar with photo → initials → icon fallback chain,
 * optional presence indicator, multiple sizes, and deterministic background color
 * derived from the name.
 */

import { MjElement } from "../core/mjelement.js";

const SIZE_MAP = {
  xs: "1.25rem",
  sm: "1.75rem",
  md: "2.25rem",
  lg: "3rem",
  xl: "4rem"
};

const AVATAR_COLORS = [
  "#2563eb", "#7c3aed", "#db2777", "#dc2626",
  "#d97706", "#059669", "#0891b2", "#4f46e5"
];

const PRESENCE_COLORS = {
  online: "#15803d",
  away: "#b45309",
  busy: "#b91c1c",
  offline: "#6b7280"
};

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}

.container {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-avatar-size, 2.25rem);
  height: var(--mj-avatar-size, 2.25rem);
  border-radius: var(--_radius, 50%);
  background: var(--mj-avatar-bg, #2563eb);
  border: var(--mj-avatar-border-width, 0px) solid var(--mj-avatar-border-color, var(--mj-border));
  overflow: hidden;
  flex-shrink: 0;
}

.img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: none;
}
.img.visible { display: block; }

.initials {
  font-size: var(--mj-avatar-font-size, calc(var(--mj-avatar-size, 2.25rem) * 0.4));
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-avatar-fg, #ffffff);
  line-height: 1;
  user-select: none;
  display: none;
}
.initials.visible { display: block; }

.icon {
  color: var(--mj-avatar-fg, #ffffff);
  width: 60%;
  height: 60%;
  display: none;
}
.icon.visible { display: flex; align-items: center; justify-content: center; }

.presence {
  position: absolute;
  bottom: 0;
  inset-inline-end: 0;
  width: var(--mj-avatar-presence-size, calc(var(--mj-avatar-size, 2.25rem) * 0.28));
  height: var(--mj-avatar-presence-size, calc(var(--mj-avatar-size, 2.25rem) * 0.28));
  border-radius: 50%;
  border: var(--mj-avatar-presence-border, 2px solid var(--mj-surface));
  display: none;
}
.presence.visible { display: block; }
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
  }

  render() {
    const markup = `
      <div class="container" part="container" role="img">
        <img class="img" part="img" alt="" />
        <span class="initials" part="initials" aria-hidden="true"></span>
        <span class="icon" part="icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="currentColor" width="100%" height="100%" aria-hidden="true">
            <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
          </svg>
        </span>
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

    this.listen(this._imgEl, "load", this._onImgLoad.bind(this))
    this.listen(this._imgEl, "error", this._onImgError.bind(this))

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

  _sync() {
    this._applySize()
    this._applyShape()
    this._loadImage()
    this._applyPresence()
    this._applyAriaLabel()
    return
  }

  _applySize() {
    const size = this.getAttribute("size") || "md"
    const sizeValue = SIZE_MAP[size] || SIZE_MAP.md
    this._containerEl.style.setProperty("--mj-avatar-size", sizeValue)
    return
  }

  _applyShape() {
    const shape = this.getAttribute("shape") || "circle"
    const radius = shape === "square" ? "var(--mj-radius-md)" : "50%"
    this._containerEl.style.setProperty("--_radius", radius)
    return
  }

  _loadImage() {
    const src = this.getAttribute("src") || ""
    if (src.length === 0) {
      this._showFallback()
      return
    }

    const crossorigin = this.getAttribute("crossorigin")
    if (crossorigin !== null) {
      this._imgEl.setAttribute("crossorigin", crossorigin)
    }
    this._imgEl.setAttribute("src", src)
    return
  }

  _onImgLoad() {
    this._imgEl.classList.add("visible")
    this._initialsEl.classList.remove("visible")
    this._iconEl.classList.remove("visible")
    this.emit("mj-avatar-image-load", { src: this._imgEl.src })
    return
  }

  _onImgError() {
    this._imgEl.classList.remove("visible")
    this._showFallback()
    this.emit("mj-avatar-image-error", { src: this.getAttribute("src") || "" })
    return
  }

  _showFallback() {
    const computed = this.computedInitials
    const color = this._resolveColor()
    this._containerEl.style.background = color

    if (computed.length > 0) {
      this._initialsEl.textContent = computed
      this._initialsEl.classList.add("visible")
      this._iconEl.classList.remove("visible")
    } else {
      this._initialsEl.classList.remove("visible")
      this._iconEl.classList.add("visible")
    }
    return
  }

  _resolveColor() {
    const explicit = this.getAttribute("color") || ""
    if (explicit.length > 0) {
      return explicit
    }
    const name = this.getAttribute("name") || this.getAttribute("initials") || ""
    if (name.length === 0) {
      return AVATAR_COLORS[0]
    }
    let hash = 0
    for (let i = 0; i < name.length; i = i + 1) {
      hash = (hash * 31 + name.charCodeAt(i)) >>> 0
    }
    const index = hash % AVATAR_COLORS.length
    const color = AVATAR_COLORS[index]
    return color
  }

  _applyPresence() {
    const presence = this.getAttribute("presence") || ""
    if (presence.length === 0) {
      this._presenceEl.classList.remove("visible")
      return
    }
    const color = PRESENCE_COLORS[presence] || PRESENCE_COLORS.offline
    this._presenceEl.style.background = color
    this._presenceEl.setAttribute("aria-label", this._presenceLabel(presence))
    this._presenceEl.classList.add("visible")
    return
  }

  _presenceLabel(presence) {
    const labels = { online: "Online", away: "Away", busy: "Busy", offline: "Offline" }
    const label = labels[presence] || presence
    return label
  }

  _applyAriaLabel() {
    const name = this.getAttribute("name") || ""
    const label = name.length > 0 ? name : "Unknown user"
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
    const name = this.getAttribute("name") || ""
    if (name.length === 0) {
      return ""
    }
    const parts = name.trim().split(/\s+/)
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

  get resolvedColor() {
    const color = this._resolveColor()
    return color
  }
}
