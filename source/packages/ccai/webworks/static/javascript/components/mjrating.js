/*
 * mjrating.js
 *
 * <mj-rating> -- star (or custom icon) rating input using the radiogroup
 * ARIA pattern with hover preview, half-step support, and form participation.
 *
 * Value model: `this._rating` (a number, 0 = no rating) is the single source
 * of truth. The `value` attribute is the default value: it is applied when
 * first seen and when it changes, and a form reset returns to it. The
 * current rating is not written back into the attribute, so the default
 * survives user changes.
 *
 * Structure: one star per unit. Each star stacks an empty glyph, a filled
 * glyph clipped to the filled fraction, and the radio hit zones on top (one
 * per star, or a leading and a trailing half with `half-steps`).
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.label {
  display: block;
  margin-bottom: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}
.label:empty { display: none; }
.label[data-required]::after {
  content: " *";
  color: var(--mj-color-danger);
}

.group {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-rating-icon-gap, var(--mj-space-1));
  flex-wrap: wrap;
}

.star {
  position: relative;
  display: inline-block;
  font-size: var(--mj-rating-icon-size, 1.5rem);
  line-height: 1;
  transition: transform var(--mj-motion-fast) var(--mj-motion-ease);
}
:host([size="sm"]) .star { font-size: var(--mj-rating-icon-size, 1.25rem); }
:host([size="lg"]) .star { font-size: var(--mj-rating-icon-size, 2rem); }

.icon-empty {
  display: block;
  color: var(--mj-rating-icon-color-empty, var(--mj-border-strong));
}

/* The filled glyph lies over the empty one, clipped to the filled share. */
.icon-fill {
  position: absolute;
  inset-block-start: 0;
  inset-inline-start: 0;
  inline-size: var(--mj-rating-fill, 0%);
  overflow: hidden;
  white-space: nowrap;
  color: var(--mj-rating-icon-color-filled, var(--mj-color-warning));
  transition: color var(--mj-motion-fast) var(--mj-motion-ease);
}
.group[data-preview] .icon-fill {
  color: var(--mj-rating-icon-color-hover, var(--mj-rating-icon-color-filled, var(--mj-color-warning)));
}
.star[data-hover] { transform: scale(1.15); }
@media (prefers-reduced-motion: reduce) {
  .star, .icon-fill { transition: none; }
  .star[data-hover] { transform: none; }
}

/* Radio hit zones: the whole star, or its two halves. */
.item {
  position: absolute;
  inset-block: 0;
  inset-inline-start: 0;
  inline-size: 100%;
  cursor: pointer;
  outline: none;
  border-radius: var(--mj-radius-sm);
}
.item[data-half="leading"] { inline-size: 50%; }
.item[data-half="trailing"] { inset-inline-start: 50%; inline-size: 50%; }
.item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([readonly]) .item { cursor: default; pointer-events: none; }
:host([disabled]) .item, .group[data-disabled] .item { cursor: not-allowed; pointer-events: none; }
:host([disabled]) .star, .group[data-disabled] .star { opacity: 0.4; }

.value-label {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  margin-inline-start: var(--mj-space-2);
}
.value-label[hidden] { display: none; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }
`;

const DEFAULT_MAX = 5;
const MAXIMUM_MAX = 10;

/*
 * The icons the `icon` attribute can name: the empty and the filled glyph
 * (different shapes, so the rating does not depend on colour alone), the
 * key of the item label ("3 stars out of 5") and the key of the read-only
 * value format ("{value} out of {max} stars").
 */
const ICONS = {
  star:    { empty: "☆", filled: "★", itemLabelKey: "mj.rating.starItem", ratedFormatKey: "mj.rating.starRated" },
  heart:   { empty: "♡", filled: "♥", itemLabelKey: "mj.rating.heartItem", ratedFormatKey: "mj.rating.heartRated" },
  circle:  { empty: "○", filled: "●", itemLabelKey: "mj.rating.pointItem", ratedFormatKey: "mj.rating.pointRated" },
  diamond: { empty: "◇", filled: "◆", itemLabelKey: "mj.rating.diamondItem", ratedFormatKey: "mj.rating.diamondRated" }
};

/*
 * The accessible name the page gave the host: `aria-labelledby`, then
 * `aria-label`, then an associated <label for> / wrapping <label>, then an
 * <mj-label for>. The shadow control cannot see any of these across the
 * shadow boundary, so the component copies the text onto it.
 */
function resolveHostLabel(host, internals) {
  let name = ""
  const root = host.getRootNode()

  const labelledBy = host.getAttribute("aria-labelledby") || ""
  if (labelledBy.trim().length > 0 && typeof root.getElementById === "function") {
    const parts = []
    const ids = labelledBy.trim().split(/\s+/)
    for (let index = 0; index < ids.length; index = index + 1) {
      const labelNode = root.getElementById(ids[index])
      if (labelNode !== null) {
        parts.push(labelNode.textContent.trim())
      }
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0) {
    name = (host.getAttribute("aria-label") || "").trim()
  }

  if (name.length === 0 && internals !== null && internals !== undefined && internals.labels !== undefined) {
    const parts = []
    for (let index = 0; index < internals.labels.length; index = index + 1) {
      parts.push(internals.labels[index].textContent.trim())
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0 && host.id.length > 0 && typeof root.querySelector === "function") {
    const mjLabel = root.querySelector(`mj-label[for="${CSS.escape(host.id)}"]`)
    if (mjLabel !== null) {
      name = mjLabel.textContent.trim()
    }
  }

  return name
}

export class MjRating extends FormControlMixin(MjElement) {
  static tagName = "mj-rating";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "value", "max",
    "required", "disabled", "readonly", "half-steps",
    "show-value-label", "icon", "icon-color", "size", "value-label-format",
    "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* The committed rating; 0 means none. */
    this._rating = 0

    /* The rating previewed under the pointer; 0 when not hovering. */
    this._hoverValue = 0

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the group or a submit failed. */
    this._showErrors = false

    /* The `max` value a "capped" console message was last logged for. */
    this._reportedMax = null

    this._groupId = nextId("mjrt-group")
    this._labelId = nextId("mjrt-label")
    this._helpId = nextId("mjrt-help")
    this._errorId = nextId("mjrt-error")
  }

  render() {
    const markup = html`
      <label class="label" part="label" id="${this._labelId}"></label>
      <div class="group" part="group" role="radiogroup" id="${this._groupId}"></div>
      <span class="value-label" part="value-label" hidden></span>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._labelEl = this.$(".label")
    this._groupEl = this.$(".group")
    this._valueLabelEl = this.$(".value-label")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")

    /*
     * The shadow DOM is new: rebuild it from the stored rating. Publishing
     * the value here is what makes an initial rating part of the form data
     * before the user touches the control.
     */
    this._hoverValue = 0
    this._publishFormValue()
    this._buildItems()
    this._syncAll()

    this.listen(this._groupEl, "click", this._onGroupClick.bind(this))
    this.listen(this._groupEl, "keydown", this._onGroupKeydown.bind(this))
    this.listen(this._groupEl, "pointerover", this._onGroupPointerover.bind(this))
    this.listen(this._groupEl, "pointerleave", this._onGroupPointerleave.bind(this))
    this.listen(this.shadowRoot, "focusout", this._onFocusout.bind(this))
    this.listen(this._labelEl, "click", this._onLabelClick.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    return
  }

  onConnected() {
    /* Labels outside the shadow root can only be resolved once connected. */
    this._syncAccessibleName()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._applyValueAttribute(newValue)
    }
    if (name === "max") {
      /* A smaller maximum caps the stored rating. */
      this._rating = Math.min(this._rating, this._getMax())
      this._publishFormValue()
    }

    if (this._groupEl === undefined || this._groupEl === null) {
      return
    }

    if (name === "max" || name === "half-steps" || name === "icon") {
      this._buildItems()
    }
    this._syncAll()
    return
  }

  /* ----- state helpers ----- */

  _getMax() {
    let max = parseInt(this.getAttribute("max") || String(DEFAULT_MAX), 10)
    if (Number.isNaN(max) === true || max <= 0) {
      max = DEFAULT_MAX
    }
    if (max > MAXIMUM_MAX) {
      if (this._reportedMax !== max) {
        this._reportedMax = max
        console.warn(`[mj-rating] max capped at ${MAXIMUM_MAX}`)
      }
      max = MAXIMUM_MAX
    }
    return max
  }

  _getStep() {
    const step = this.hasAttribute("half-steps") === true ? 0.5 : 1
    return step
  }

  _getIcon() {
    const name = (this.getAttribute("icon") || "star").toLowerCase()
    const icon = Object.prototype.hasOwnProperty.call(ICONS, name) === true ? ICONS[name] : ICONS.star
    return icon
  }

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _isInteractive() {
    const interactive = this._isDisabled() === false && this.hasAttribute("readonly") === false
    return interactive
  }

  /* Parse a rating; anything unusable is 0, and the result is 0..max. */
  _toRating(value) {
    let rating = 0
    if (value !== null && value !== undefined) {
      const parsed = typeof value === "number" ? value : parseFloat(String(value))
      if (Number.isFinite(parsed) === true) {
        rating = Math.min(this._getMax(), Math.max(0, parsed))
      }
    }
    return rating
  }

  _getItems() {
    let items = []
    if (this._groupEl !== undefined && this._groupEl !== null) {
      items = Array.from(this._groupEl.querySelectorAll(".item"))
    }
    return items
  }

  _itemValue(item) {
    const value = parseFloat(item.getAttribute("data-value") || "0")
    return value
  }

  /* ----- rendering ----- */

  _buildItems() {
    this._groupEl.textContent = ""

    const max = this._getMax()
    const halfSteps = this.hasAttribute("half-steps")
    const icon = this._getIcon()

    for (let position = 1; position <= max; position = position + 1) {
      const star = document.createElement("span")
      star.className = "star"
      star.setAttribute("part", "star")
      star.setAttribute("data-position", String(position))

      const empty = document.createElement("span")
      empty.className = "icon-empty"
      empty.setAttribute("part", "icon-empty")
      empty.setAttribute("aria-hidden", "true")
      empty.textContent = icon.empty

      const fill = document.createElement("span")
      fill.className = "icon-fill"
      fill.setAttribute("part", "icon-filled")
      fill.setAttribute("aria-hidden", "true")
      fill.textContent = icon.filled

      star.appendChild(empty)
      star.appendChild(fill)

      if (halfSteps === true) {
        star.appendChild(this._createItem(position - 0.5, "leading"))
        star.appendChild(this._createItem(position, "trailing"))
      } else {
        star.appendChild(this._createItem(position, null))
      }
      this._groupEl.appendChild(star)
    }
    return
  }

  _createItem(value, half) {
    const item = document.createElement("span")
    item.className = "item"
    item.setAttribute("part", "item")
    item.setAttribute("role", "radio")
    item.setAttribute("aria-checked", "false")
    item.setAttribute("data-value", String(value))
    item.setAttribute("aria-label", this._itemLabel(value))
    if (half !== null) {
      item.setAttribute("data-half", half)
    }
    item.tabIndex = -1
    return item
  }

  _itemLabel(value) {
    const max = this._getMax()
    const icon = this._getIcon()
    const label = t(icon.itemLabelKey, { count: value, max: max })
    return label
  }

  _formatValueLabel(fallbackFormat) {
    const format = this.getAttribute("value-label-format") || fallbackFormat
    const text = format.split("{value}").join(String(this._rating)).split("{max}").join(String(this._getMax()))
    return text
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const showValueLabel = this.hasAttribute("show-value-label")

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._helpEl.textContent = helpText

    this._groupEl.toggleAttribute("data-disabled", disabled === true)
    this._groupEl.setAttribute("aria-required", required === true ? "true" : "false")
    this._groupEl.setAttribute("aria-disabled", disabled === true ? "true" : "false")
    if (readonly === true) {
      this._groupEl.setAttribute("aria-readonly", "true")
    } else {
      this._groupEl.removeAttribute("aria-readonly")
    }

    this._syncIconColor()

    this._valueLabelEl.hidden = showValueLabel === false
    this._valueLabelEl.textContent = showValueLabel === true ? this._formatValueLabel(t("mj.rating.valueLabel")) : ""

    this._syncAccessibleName()
    this._renderRating()

    /* required / error-message feed validity. */
    this._refreshValidity()
    this._renderValidity(false)
    return
  }

  /*
   * `icon-color` names a colour token ("danger" -> --mj-color-danger), a
   * custom property ("--brand") or any CSS colour. It is applied through
   * the --mj-rating-icon-color-filled custom property, so a stylesheet or
   * ::part() rule can still override it.
   */
  _syncIconColor() {
    const iconColor = (this.getAttribute("icon-color") || "").trim()
    let color = ""

    if (iconColor.indexOf("--") === 0) {
      color = `var(${iconColor})`
    } else if (/^[a-z][a-z0-9-]*$/i.test(iconColor) === true && CSS.supports("color", iconColor) === false) {
      color = `var(--mj-color-${iconColor})`
    } else if (iconColor.length > 0 && CSS.supports("color", iconColor) === true) {
      color = iconColor
    }

    if (color.length > 0) {
      this._groupEl.style.setProperty("--mj-rating-icon-color-filled", color)
    } else {
      this._groupEl.style.removeProperty("--mj-rating-icon-color-filled")
    }
    return
  }

  /*
   * Name the radiogroup: the visible label, or the name given to the host
   * from outside, or "Rating". A read-only rating has no focusable radios,
   * so its group name also states the value.
   */
  _syncAccessibleName() {
    if (this._groupEl === undefined || this._groupEl === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    let name = label
    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      name = hostLabel
    }

    if (this.hasAttribute("readonly") === true) {
      /* Only {count} is filled here; {value} and {max} are left for the value format. */
      const ratedFormat = t(this._getIcon().ratedFormatKey, { count: this._getMax() })
      const rated = this._formatValueLabel(ratedFormat)
      this._groupEl.removeAttribute("aria-labelledby")
      this._groupEl.setAttribute("aria-label", name.length > 0 ? `${name}: ${rated}` : t("mj.rating.rated", { rating: rated }))
    } else if (name.length > 0 && name === label) {
      this._groupEl.removeAttribute("aria-label")
      this._groupEl.setAttribute("aria-labelledby", this._labelId)
    } else {
      this._groupEl.removeAttribute("aria-labelledby")
      this._groupEl.setAttribute("aria-label", name.length > 0 ? name : t("mj.rating.groupLabel"))
    }
    return
  }

  _updateDescribedBy() {
    const ids = []
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId)
    }
    if (this._errorEl.hasAttribute("data-visible") === true) {
      ids.push(this._errorId)
    }
    if (ids.length > 0) {
      this._groupEl.setAttribute("aria-describedby", ids.join(" "))
    } else {
      this._groupEl.removeAttribute("aria-describedby")
    }
    return
  }

  /*
   * Draw the stars. The fill follows the hover preview while the pointer is
   * over the group and the committed rating otherwise; `aria-checked` and
   * the tab stop always follow the committed rating only.
   */
  _renderRating() {
    const previewing = this._hoverValue > 0
    const shown = previewing === true ? this._hoverValue : this._rating
    const stars = this._groupEl.querySelectorAll(".star")

    this._groupEl.toggleAttribute("data-preview", previewing === true)

    for (let index = 0; index < stars.length; index = index + 1) {
      const star = stars[index]
      const position = index + 1
      const share = Math.min(1, Math.max(0, shown - (position - 1)))
      star.querySelector(".icon-fill").style.setProperty("--mj-rating-fill", `${share * 100}%`)
      star.toggleAttribute("data-hover", previewing === true && Math.ceil(this._hoverValue) === position)
    }

    /*
     * One radio is always the tab stop: the checked one, else the nearest
     * one below a value that matches no radio, else the first.
     */
    const items = this._getItems()
    const interactive = this._isInteractive()
    let tabStop = items.length > 0 ? items[0] : null

    for (let index = 0; index < items.length; index = index + 1) {
      const item = items[index]
      const value = this._itemValue(item)
      item.setAttribute("aria-checked", value === this._rating ? "true" : "false")
      item.tabIndex = -1
      if (value <= this._rating) {
        tabStop = item
      }
    }
    if (tabStop !== null && interactive === true) {
      tabStop.tabIndex = 0
    }
    return
  }

  /* ----- value ----- */

  /*
   * Apply the `value` attribute. The attribute is delivered once before the
   * first render and again after it (see MjElement), so the text already
   * applied is remembered and a repeat delivery does not overwrite what the
   * user or a script has chosen since.
   */
  _applyValueAttribute(attributeValue) {
    if (attributeValue === this._appliedValueAttribute) {
      return
    }
    this._appliedValueAttribute = attributeValue
    this._applyValue(attributeValue)
    return
  }

  /* The single entry point for every programmatic value change. */
  _applyValue(next) {
    this._rating = this._toRating(next)
    this._publishFormValue()

    if (this._groupEl !== undefined && this._groupEl !== null) {
      this._syncAll()
    }
    return
  }

  _publishFormValue() {
    this._setFormValue(String(this._rating))
    return
  }

  /*
   * A change made by the user. The rating is updated first, so a listener
   * reading `value` sees the new rating, then `mj-change` is emitted; if a
   * listener cancels it the previous rating is restored. Nothing happens,
   * and nothing is emitted, when the rating would not change. Returns true
   * when the rating changed.
   */
  _commitUserRating(next) {
    const previous = this._rating
    const rating = this._toRating(next)
    let changed = false

    if (rating === previous || this._isInteractive() === false) {
      return changed
    }

    this._rating = rating
    this._publishFormValue()
    this._syncAll()

    const notCanceled = this.emit("mj-change", { value: rating, previousValue: previous }, { cancelable: true })
    if (notCanceled === false) {
      this._rating = previous
      this._publishFormValue()
      this._syncAll()
    } else {
      changed = true
    }
    return changed
  }

  _focusTabStop() {
    const items = this._getItems()
    for (let index = 0; index < items.length; index = index + 1) {
      if (items[index].tabIndex === 0) {
        items[index].focus()
      }
    }
    return
  }

  /* ----- events ----- */

  _eventItem(event) {
    const item = event.target !== null && typeof event.target.closest === "function"
      ? event.target.closest(".item")
      : null
    return item
  }

  _onGroupClick(event) {
    const item = this._eventItem(event)
    if (item === null || this._isInteractive() === false) {
      return
    }

    const value = this._itemValue(item)
    const required = this.hasAttribute("required")

    /* Clicking the current rating again clears it, unless one is required. */
    const next = value === this._rating && required === false ? 0 : value
    this._commitUserRating(next)
    this._focusTabStop()
    return
  }

  _onGroupKeydown(event) {
    const item = this._eventItem(event)
    if (item === null || this._isInteractive() === false) {
      return
    }

    const key = event.key
    const step = this._getStep()
    const max = this._getMax()
    const required = this.hasAttribute("required")
    const minimum = required === true ? step : 0
    let target = null

    /* Under dir="rtl" the higher ratings are visually to the left. */
    const rtl = getComputedStyle(this._groupEl).direction === "rtl"
    const increaseKey = rtl === true ? "ArrowLeft" : "ArrowRight"
    const decreaseKey = rtl === true ? "ArrowRight" : "ArrowLeft"

    if (key === increaseKey || key === "ArrowUp") {
      target = Math.min(max, Math.floor(this._rating / step) * step + step)
    } else if (key === decreaseKey || key === "ArrowDown") {
      target = Math.max(minimum, Math.ceil(this._rating / step) * step - step)
    } else if (key === "Home") {
      target = step
    } else if (key === "End") {
      target = max
    } else if (key === "Delete" || key === "Backspace") {
      target = required === true ? this._rating : 0
    } else if (key === " " || key === "Enter") {
      /* Select the focused radio; never toggles a rating off. */
      target = this._itemValue(item)
    }

    if (target === null) {
      return
    }

    event.preventDefault()
    this._commitUserRating(target)

    /* Focus follows the selection, as in any radio group. */
    this._focusTabStop()
    return
  }

  _onGroupPointerover(event) {
    const item = this._eventItem(event)
    if (item === null || this._isInteractive() === false || event.pointerType === "touch") {
      return
    }

    const value = this._itemValue(item)
    if (value !== this._hoverValue) {
      this._hoverValue = value
      this._renderRating()
      this.emit("mj-hover", { hoverValue: value })
    }
    return
  }

  _onGroupPointerleave(event) {
    if (this._hoverValue !== 0) {
      this._hoverValue = 0
      this._renderRating()
    }
    return
  }

  /* Focus left the group: validate what was (or was not) chosen. */
  _onFocusout(event) {
    const next = event.relatedTarget
    const staysInside = next !== null && next !== undefined && this.shadowRoot.contains(next) === true
    if (staysInside === true) {
      return
    }

    this._showErrors = true
    this._refreshValidity()
    this._renderValidity(true)
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
    return
  }

  /* The visible label behaves like a <label for>: it focuses the group. */
  _onLabelClick(event) {
    if (this._isDisabled() === false) {
      this.focus()
    }
    return
  }

  /*
   * Activating an associated <label> clicks the host; move focus into the
   * group as a native control would.
   */
  _onHostClick(event) {
    const path = event.composedPath()
    if (path.length > 0 && path[0] === this && this._isDisabled() === false) {
      this.focus()
    }
    return
  }

  /* ----- validation ----- */

  /*
   * Show or hide the inline error from the current validity. `error-message`
   * replaces the built-in text but never makes a valid control look invalid.
   * `announce` is true when the user (leaving the group) or a submit attempt
   * triggered the check; only then is `mj-invalid` emitted.
   */
  _renderValidity(announce) {
    const message = this.validationMessage
    const invalid = message.length > 0 && this._showErrors === true

    if (invalid === true) {
      const override = this.getAttribute("error-message") || ""
      const displayMessage = override.length > 0 ? override : message
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      this._groupEl.setAttribute("aria-invalid", "true")
      this._updateDescribedBy()
      if (announce === true) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      this._groupEl.setAttribute("aria-invalid", "false")
      this._updateDescribedBy()
    }
    return
  }

  /*
   * `required` means a non-zero rating. The form value is "0" rather than
   * the empty string, so the mixin's generic check would never fire.
   */
  _refreshValidity() {
    if (this._internals === null || this._internals === undefined) {
      return
    }

    if (this.hasAttribute("required") === true && this._rating === 0) {
      const message = this.getAttribute("required-message") || t("mj.rating.required")
      const anchor = this._validationAnchor()
      if (anchor !== null && anchor !== undefined) {
        this._internals.setValidity({ valueMissing: true }, message, anchor)
      } else {
        this._internals.setValidity({ valueMissing: true }, message)
      }
    } else {
      this._internals.setValidity({})
    }
    return
  }

  _validationAnchor() {
    const anchor = this._groupEl !== undefined && this._groupEl !== null ? this._groupEl : null
    return anchor
  }

  onFormReset(initial) {
    this._showErrors = false
    this._hoverValue = 0
    this._applyValue(initial)
    return
  }

  onFormRestore(state) {
    const restored = typeof state === "string" ? state : "0"
    this._applyValue(restored)
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    if (this._groupEl !== undefined && this._groupEl !== null) {
      this._syncAll()
    }
    return
  }

  /* ----- public API ----- */

  get valueAsNumber() {
    return this._rating
  }

  set valueAsNumber(next) {
    this._applyValue(next)
    return
  }

  get value() {
    return String(this._rating)
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  checkValidity() {
    this._refreshValidity()
    const valid = super.checkValidity()
    return valid
  }

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  focus(options) {
    const items = this._getItems()
    let target = null
    for (let index = 0; index < items.length; index = index + 1) {
      if (items[index].tabIndex === 0) {
        target = items[index]
      }
    }
    if (target !== null) {
      target.focus(options)
    }
    return
  }
}
